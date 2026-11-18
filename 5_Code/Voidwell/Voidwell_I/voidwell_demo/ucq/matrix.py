"""matrix.py -- n x n matrices over F_p, exact.

Operations: product (@), inverse (Gauss-Jordan; raises SingularMatrix),
trace, equality, canonical serialization (version byte, n, entry
width from p).  GL membership is `inverse()` succeeding.
"""
from __future__ import annotations

from ucq.field import P


class SingularMatrix(ValueError):
    """Raised when a matrix over F_p is not invertible."""


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

    # -- arithmetic -------------------------------------------------------
    def __matmul__(self, other: "FpMatrix") -> "FpMatrix":
        if not isinstance(other, FpMatrix) or other.p != self.p \
                or other.n != self.n:
            raise ValueError("dimension/field mismatch")
        p, A, B = self.p, self.rows, other.rows
        return FpMatrix(
            [[sum(A[i][k] * B[k][j] for k in range(self.n)) % p
              for j in range(self.n)] for i in range(self.n)], p)

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

    def trace(self) -> int:
        return sum(self.rows[i][i] for i in range(self.n)) % self.p

    # -- equality / serialization ------------------------------------------
    def __eq__(self, other):
        return (isinstance(other, FpMatrix) and self.p == other.p
                and self.rows == other.rows)

    def __hash__(self):
        return hash((self.p, self.rows))

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
        """Inverse of serialize; the field p is supplied by the caller
        (it is context, not payload) and its bit-length is checked."""
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
