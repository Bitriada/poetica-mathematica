"""The UC-Q algebra, exactly: nilpotent-cryptography groundwork.

MONOGRAPH SOURCES.

* Ch. VI sec. 6.2.8 ("The UC-Quaternion Algebra"): UCQ = H (x)_R UC is
  16-dimensional over R; each quaternion coefficient lives in the
  commutative ring UC = R[i, tau] / (i^2 + 1, tau^2), with i commuting
  with tau and with the quaternion units i, j, k (UC coefficients are
  central); the quaternion conjugate gives Q*Qbar = a^2+b^2+c^2+d^2, a
  UC-valued quadratic form whose value part carries the split signature
  of the reduced norm of H (x) C.
* Ch. VI sec. 6.2.8a ("Trace Accumulation in UCQ Products"):
  Proposition 2.8a.1, the UC product rule
      (v1 + tau*t1)(v2 + tau*t2) = v1*v2 + tau*(v1*t2 + v2*t1),
  "a Leibniz-like structure: the trace of a product is the weighted sum
  of individual traces, with values serving as weights"; Corollary
  2.8a.4, the four-direction trace accumulation; "the value component
  carries the result of the computation; the trace component carries
  the history of how that result was obtained.  No external logging
  mechanism is required - the algebra is self-auditing."
* Ch. IX / Book II ("The Nilpotent Cryptography Conjecture"): the
  conjecture that hash functions built on this arithmetic are one-way
  because annihilated traces cannot be reconstructed -- "Verification
  or refutation awaits the construction of a working TriPU or a formal
  proof of the one-way property."

REPRESENTATION (all arithmetic exact; integers only, no floats).

A complex quaternion ("CQ") is a quaternion
    w + x*I + y*J + z*K,   w, x, y, z Gaussian integers (pairs of ints),
with the complex unit central (Ch. VI: "i commuting with ... i, j, k").
A UCQ element is a pair (V, D) of CQs representing

    Z = V + tau*D        ("value sheet" V, "trace sheet" D)

so that the product rule becomes
    (V1, D1) * (V2, D2) = (V1*V2, V1*D2 + D1*V2)
and tau * Z = (0, V).  The 16 real degrees of freedom are the 8 Gaussian
components of V plus the 8 of D.

TWO CORRECTIONS TO THE NPCS DRAFT, proven by exact witness in trials:

(Corr-1) The draft's sec. 1.1 states tr(Z1 Z2) = val(Z1) tr(Z2) +
    val(Z2) tr(Z1).  The commuted second term is wrong in the
    non-commutative setting: the correct law is
        tr(Z1 Z2) = V1 D2 + D1 V2,
    which differs from V1 D2 + V2 D1 whenever D1 and V2 do not commute
    (exact witness: T1).

(Corr-2) The draft's sec. 7.3 states (v + tau*t)^2 = v^2 + 2*tau*v*t.
    The correct square is v^2 + tau*(v t + t v), and v t != t v in
    general (exact witness: T1).

Also corrected here: UCQ is a real ALGEBRA -- it has additive inverses
(Z + (-Z) = 0).  The monograph's "no operation for subtraction" claim
belongs to the Fortress COUNTING architecture (the carry/fold ledger),
not to UCQ; see trials T9 for the honest restatement.
"""

from __future__ import annotations

import struct

__all__ = ["g_add", "g_sub", "g_neg", "g_mul", "g_sq", "G0",
           "cq_zero", "cq_add", "cq_sub", "cq_neg", "cq_mul", "cq_conj",
           "cq_commutes", "UCQ", "TAU", "UCQ_I", "UCQ_J", "UCQ_K",
           "ucq_product", "serialize_int"]

# -- Gaussian integers (exact complex numbers: (re, im) int pairs) ----------
G0 = (0, 0)


def g_add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def g_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def g_neg(a):
    return (-a[0], -a[1])


def g_mul(a, b):
    return (a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0])


def g_sq(a):
    return g_mul(a, a)


# -- complex quaternions: 4 Gaussian components (w, x, y, z) ----------------
# The complex unit is CENTRAL; only the quaternion units anticommute.
def cq_zero():
    return (G0, G0, G0, G0)


def cq_add(p, q):
    return tuple(g_add(a, b) for a, b in zip(p, q))


def cq_sub(p, q):
    return tuple(g_sub(a, b) for a, b in zip(p, q))


def cq_neg(p):
    return tuple(g_neg(a) for a in p)


def cq_mul(p, q):
    """Quaternion product with Gaussian (central-complex) coefficients.

    Multiplication table (rows: p's unit, cols: q's unit) -> (sign, unit):
    1*1=1, 1*i=i, ...  i*i=-1, i*j=k, i*k=-j, j*i=-k, j*j=-1, j*k=i,
    k*i=j, k*j=-i, k*k=-1  (i j k = -1, all units anticommute)."""
    table = (
        ((1, 0), (1, 1), (1, 2), (1, 3)),
        ((1, 1), (-1, 0), (1, 3), (-1, 2)),
        ((1, 2), (-1, 3), (-1, 0), (1, 1)),
        ((1, 3), (1, 2), (-1, 1), (-1, 0)),
    )
    acc = [G0, G0, G0, G0]
    for a in range(4):
        pa = p[a]
        for b in range(4):
            sign, unit = table[a][b]
            term = g_mul(pa, q[b])
            acc[unit] = g_add(acc[unit],
                              term if sign > 0 else g_neg(term))
    return tuple(acc)


def cq_conj(p):
    """Quaternion conjugate: negate quaternion units, keep coefficients."""
    return (p[0], g_neg(p[1]), g_neg(p[2]), g_neg(p[3]))


def cq_commutes(p, q) -> bool:
    return cq_mul(p, q) == cq_mul(q, p)


# -- UCQ: Z = V + tau*D ------------------------------------------------------
class UCQ:
    """An exact element of the UC-Q algebra, as two complex quaternions
    (V, D) with Z = V + tau*D.  Immutable, hashable."""

    __slots__ = ("V", "D")

    def __init__(self, V, D):
        object.__setattr__(self, "V", tuple(V))
        object.__setattr__(self, "D", tuple(D))

    # -- constructors --------------------------------------------------------
    @staticmethod
    def from_cq(*ints):
        """16 ints -> the 16 real parameters: V's four Gaussian
        components (re, im each), then D's four."""
        vals = list(ints) + [0] * (16 - len(ints))
        V = tuple((vals[2 * j], vals[2 * j + 1]) for j in range(4))
        D = tuple((vals[8 + 2 * j], vals[9 + 2 * j]) for j in range(4))
        return UCQ(V, D)

    @staticmethod
    def from_real(v, d=None):
        """The encode shape: V a REAL quaternion (4 ints), D a complex
        quaternion (4 Gaussian pairs or 8 ints)."""
        V = tuple((x, 0) for x in v)
        if d is None:
            d = (G0, G0, G0, G0)
        if len(d) == 8:
            d = tuple((d[2 * j], d[2 * j + 1]) for j in range(4))
        return UCQ(V, tuple(d))

    @staticmethod
    def uc(re=0, i=0, tau=0, tau_i=0):
        """A central UC number (scalar quaternion component)."""
        V = ((re, i), G0, G0, G0)
        D = ((tau, tau_i), G0, G0, G0)
        return UCQ(V, D)

    # -- sheets ---------------------------------------------------------------
    def val(self):
        return self.V

    def tr(self):
        return self.D

    # -- arithmetic ------------------------------------------------------------
    def __add__(self, other):
        return UCQ(cq_add(self.V, other.V), cq_add(self.D, other.D))

    def __neg__(self):
        return UCQ(cq_neg(self.V), cq_neg(self.D))

    def __sub__(self, other):
        return self + (-other)

    def __mul__(self, other: "UCQ") -> "UCQ":
        """(V1, D1)(V2, D2) = (V1 V2, V1 D2 + D1 V2) -- Prop. 2.8a.1."""
        if not isinstance(other, UCQ):
            return NotImplemented
        return UCQ(cq_mul(self.V, other.V),
                   cq_add(cq_mul(self.V, other.D), cq_mul(self.D, other.V)))

    def tau_mul(self) -> "UCQ":
        """tau * Z = (0, V): multiplication by tau collapses the trace
        sheet -- the algebraic information-annihilation operator."""
        return UCQ(cq_zero(), self.V)

    # -- conjugate and norm ------------------------------------------------------
    def conj(self) -> "UCQ":
        """Quaternion conjugate (units negated in both sheets)."""
        return UCQ(cq_conj(self.V), cq_conj(self.D))

    def norm_uc(self):
        """Q*Qbar = a^2 + b^2 + c^2 + d^2 as a UC number
        (value, trace) of Gaussian integers -- Ch. VI sec. 6.2.8.

        value = sum_j val_j^2   (split signature on the complex parts)
        trace = 2 * sum_j val_j * tr_j
        Multiplicative as UC numbers (reduced norm over the commutative
        ring UC) -- verified exactly in trials T1."""
        val = G0
        tr = G0
        for v, d in zip(self.V, self.D):
            val = g_add(val, g_sq(v))
            tr = g_add(tr, g_mul(v, d))
        return (val, (2 * tr[0], 2 * tr[1]))

    # -- serialization -------------------------------------------------------------
    def components(self):
        """The 16 real parameters: V (4 x (re, im)), D (4 x (re, im))."""
        out = []
        for g in self.V:
            out.extend(g)
        for g in self.D:
            out.extend(g)
        return out

    def serialize_exact(self) -> bytes:
        """Canonical EXACT serialization: 16 length-prefixed signed
        big-endian integers.  Injective on UCQ (no rounding)."""
        return b"".join(serialize_int(n) for n in self.components())

    @staticmethod
    def deserialize_exact(data: bytes) -> "UCQ":
        """Inverse of serialize_exact (round-trip exactness)."""
        ints, i = [], 0
        for _ in range(16):
            (n,) = struct.unpack_from(">I", data, i)
            i += 4
            ints.append(int.from_bytes(data[i:i + n], "big", signed=True))
            i += n
        return UCQ.from_cq(*ints)

    def serialize_sheet(self, sheet: str) -> bytes:
        """Exact serialization of ONE sheet ('val' or 'tr'): 8
        length-prefixed signed integers."""
        cq = self.V if sheet == "val" else self.D
        ints = []
        for g in cq:
            ints.extend(g)
        return b"".join(serialize_int(n) for n in ints)

    def serialize_float64(self) -> bytes:
        """The NPCS DRAFT's sec. 1.5 serialization: 16 IEEE 754
        double-precision coefficients, big-endian (128 bytes).

        WARNING (draft flaw, demonstrated in trials T3): products of
        Fare-Octal encodings produce integers far beyond 2^53; float64
        rounds them, so distinct elements can serialize identically.
        Kept only to demonstrate the flaw."""
        return struct.pack(">16d", *(float(n) for n in self.components()))

    # -- plumbing -------------------------------------------------------------------
    def __eq__(self, other):
        return isinstance(other, UCQ) and self.V == other.V \
            and self.D == other.D

    def __hash__(self):
        return hash((UCQ, self.V, self.D))

    def __repr__(self):
        sheets = []
        for name, cq in (("V", self.V), ("D", self.D)):
            parts = []
            for c, u in zip(cq, ("", "I", "J", "K")):
                if c == G0:
                    continue
                label = f"{c[0]}{c[1]:+d}i" if c[1] else f"{c[0]}"
                parts.append(label + u)
            sheets.append(f"{name}[" + " ".join(parts) + "]")
        return f"UCQ({sheets[0]}; {sheets[1]})"


def serialize_int(n: int) -> bytes:
    """Length-prefixed signed big-endian integer (exact, injective)."""
    n = int(n)
    length = max(1, (n.bit_length() + 8) // 8)
    body = n.to_bytes(length, "big", signed=True)
    return len(body).to_bytes(4, "big") + body


# -- named elements -------------------------------------------------------------
TAU = UCQ(((0, 0), G0, G0, G0), ((1, 0), G0, G0, G0))   # tau = 0 + tau*1
UCQ_I = UCQ(((0, 0), (1, 0), G0, G0), (G0, G0, G0, G0))  # quaternion i
UCQ_J = UCQ((G0, G0, (1, 0), G0), (G0, G0, G0, G0))      # quaternion j
UCQ_K = UCQ((G0, G0, G0, (1, 0)), (G0, G0, G0, G0))      # quaternion k


def ucq_product(elements):
    """Left-to-right product of a sequence of UCQ elements (the path
    commitment tensor product T(P) of the NPCS scheme)."""
    it = iter(elements)
    acc = next(it)
    for e in it:
        acc = acc * e
    return acc
