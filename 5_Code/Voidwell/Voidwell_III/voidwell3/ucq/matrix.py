"""matrix.py -- n x n matrices over F_p, exact.

Operations: product (@), inverse (Gauss-Jordan; raises SingularMatrix),
adjugate_inverse (n in {2,3,4}: one modular exponentiation instead of
one per pivot -- the D6 speed work of the V3 investigation), trace,
equality, canonical serialization.

Voidwell-3 change vs Voidwell-2: `adjugate_inverse` computes
det M by cofactor expansion and the adjugate directly, then
M^{-1} = adj(M) * det(M)^{-1} mod p.  For the 4x4 well matrices this
replaces up to four pow() calls per candidate with exactly one, and
the well loop caches the inverse so the accepted candidate's
conjugation reuses it (the V2 profile showed 113 pow calls and a
fresh inverse inside every rejected conjugation).
"""
from __future__ import annotations

from ucq.field import P


class SingularMatrix(ValueError):
    """Raised when a matrix over F_p is not invertible."""


def _det2(m, p):
    return (m[0][0] * m[1][1] - m[0][1] * m[1][0]) % p


def _det3(m, p):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])) % p


class FpMatrix:
    __slots__ = ("n", "p", "rows")

    def __init__(self, rows, p: int = P):
        self.p = int(p)
        self.n = len(rows)
        self.rows = tuple(tuple(int(x) % self.p for x in r)
                          for r in rows)
        if any(len(r) != self.n for r in self.rows):
            raise ValueError("square matrix required")

    # -- constructors ---------------------------------------------------
    @classmethod
    def identity(cls, n: int, p: int = P) -> "FpMatrix":
        return cls([[1 if i == j else 0 for j in range(n)]
                    for i in range(n)], p)

    @classmethod
    def from_stream(cls, n: int, p: int, words) -> "FpMatrix":
        """Entries filled row-major from an iterator of integers
        (already reduced or reducible mod p)."""
        return cls([[next(words) % p for _ in range(n)] for _ in range(n)],
                   p)

    @classmethod
    def diagonal(cls, diag, p: int = P) -> "FpMatrix":
        return cls([[d if i == j else 0 for j, d in
                     enumerate(diag)] for i, d in enumerate(diag)], p)

    # -- arithmetic -------------------------------------------------------
    def __matmul__(self, other: "FpMatrix") -> "FpMatrix":
        if not isinstance(other, FpMatrix) or other.p != self.p \
                or other.n != self.n:
            raise ValueError("dimension/field mismatch")
        p, A, B = self.p, self.rows, other.rows
        return FpMatrix(
            [[sum(A[i][k] * B[k][j] for k in range(self.n)) % p
              for j in range(self.n)] for i in range(self.n)], p)

    def __add__(self, other: "FpMatrix") -> "FpMatrix":
        if not isinstance(other, FpMatrix) or other.p != self.p \
                or other.n != self.n:
            raise ValueError("dimension/field mismatch")
        p = self.p
        return FpMatrix([[(a + b) % p for a, b in zip(ra, rb)]
                         for ra, rb in zip(self.rows, other.rows)], p)

    def __sub__(self, other: "FpMatrix") -> "FpMatrix":
        if not isinstance(other, FpMatrix) or other.p != self.p \
                or other.n != self.n:
            raise ValueError("dimension/field mismatch")
        p = self.p
        return FpMatrix([[(a - b) % p for a, b in zip(ra, rb)]
                         for ra, rb in zip(self.rows, other.rows)], p)

    def __neg__(self) -> "FpMatrix":
        p = self.p
        return FpMatrix([[-a % p for a in r] for r in self.rows], p)

    def __eq__(self, other):
        return (isinstance(other, FpMatrix) and self.p == other.p
                and self.rows == other.rows)

    def __hash__(self):
        return hash((self.p, self.rows))

    def inverse(self) -> "FpMatrix":
        """Gauss-Jordan on [M | I]; exact; raises SingularMatrix."""
        n, p = self.n, self.p
        aug = [list(self.rows[i]) + [1 if i == j else 0
                                     for j in range(n)]
               for i in range(n)]
        for col in range(n):
            piv = next((r for r in range(col, n) if aug[r][col] % p),
                       None)
            if piv is None:
                raise SingularMatrix("singular over F_p")
            aug[col], aug[piv] = aug[piv], aug[col]
            inv = pow(aug[col][col], -1, p)
            aug[col] = [x * inv % p for x in aug[col]]
            for r in range(n):
                if r != col and aug[r][col]:
                    f = aug[r][col]
                    aug[r] = [(x - f * y) % p
                              for x, y in zip(aug[r], aug[col])]
        return FpMatrix([row[n:] for row in aug], p)

    def adjugate_inverse(self) -> "FpMatrix":
        """M^{-1} = adj(M) * det(M)^{-1} mod p, for n in {2,3,4}.
        Exactly one pow() call.  Raises SingularMatrix when det = 0.

        The adjugate is the transpose of the cofactor matrix; for the
        small n used here, cofactor expansion is faster than
        Gauss-Jordan in pure Python and the single pow replaces the
        per-pivot inversions.
        """
        n, p, m = self.n, self.p, self.rows
        if n == 1:
            d = m[0][0] % p
            if not d:
                raise SingularMatrix("singular over F_p")
            return FpMatrix([[pow(d, -1, p)]], p)
        if n == 2:
            det = _det2(m, p)
            if not det:
                raise SingularMatrix("singular over F_p")
            di = pow(det, -1, p)
            return FpMatrix([[m[1][1] * di % p, -m[0][1] * di % p],
                             [-m[1][0] * di % p, m[0][0] * di % p]], p)
        if n == 3:
            det = _det3(m, p)
            if not det:
                raise SingularMatrix("singular over F_p")
            di = pow(det, -1, p)
            def cf(i, j):
                rows = [m[r] for r in range(3) if r != i]
                cols = 3 - 1
                sub = [[rows[0][c] for c in range(3) if c != j],
                       [rows[1][c] for c in range(3) if c != j]]
                return _det2(sub, p)
            adj = [[cf(j, i) * (-1) ** (i + j) for j in range(3)]
                   for i in range(3)]  # note: transpose inside
            return FpMatrix([[adj[i][j] * di % p for j in range(3)]
                             for i in range(3)], p)
        if n == 4:
            # 4x4 via the Laplace expansion on 3x3 minors
            def minor3(skip_row, skip_col):
                sub = [[m[r][c] for c in range(4) if c != skip_col]
                       for r in range(4) if r != skip_row]
                return _det3(sub, p)
            det = 0
            for j in range(4):
                det += (-1) ** j * m[0][j] * minor3(0, j)
            det %= p
            if not det:
                raise SingularMatrix("singular over F_p")
            di = pow(det, -1, p)
            adj = [[((-1) ** (i + j)) * minor3(j, i) % p
                    for j in range(4)] for i in range(4)]
            return FpMatrix([[adj[i][j] * di % p for j in range(4)]
                             for i in range(4)], p)
        raise NotImplementedError(
            f"adjugate_inverse supports n <= 4 (got {n}); "
            "use inverse()")

    def trace(self) -> int:
        return sum(self.rows[i][i] for i in range(self.n)) % self.p

    def row(self, i: int) -> tuple:
        return self.rows[i % self.n]

    # -- serialization ------------------------------------------
    def serialize(self) -> bytes:
        """Canonical: b'\\x01' + n (2 bytes BE) + p bit-length (2 bytes)
        + entries row-major, fixed width, big-endian."""
        w = (self.p.bit_length() + 7) // 8
        out = bytearray(b"\x01"
                        + self.n.to_bytes(2, "big")
                        + self.p.bit_length().to_bytes(2, "big"))
        for row in self.rows:
            for x in row:
                out += x.to_bytes(w, "big")
        return bytes(out)

    @classmethod
    def deserialize(cls, blob: bytes, p: int) -> "FpMatrix":
        if blob[0] != 1:
            raise ValueError("unknown matrix serialization version")
        n = int.from_bytes(blob[1:3], "big")
        pbits = int.from_bytes(blob[3:5], "big")
        if pbits != p.bit_length():
            raise ValueError("field bit-length mismatch")
        w = (pbits + 7) // 8
        need = 5 + n * n * w
        if len(blob) < need:
            raise ValueError("truncated matrix serialization")
        vals = [int.from_bytes(blob[5 + i * w: 5 + (i + 1) * w], "big")
                for i in range(n * n)]
        rows = [vals[i * n:(i + 1) * n] for i in range(n)]
        return cls(rows, p)

    def __repr__(self):
        return f"FpMatrix({self.rows})"


__all__ = ["FpMatrix", "SingularMatrix"]
