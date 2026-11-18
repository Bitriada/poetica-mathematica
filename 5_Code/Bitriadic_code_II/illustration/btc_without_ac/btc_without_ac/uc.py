"""Ultra-Complex numbers: UC = C[tau]/(tau^2).

Implements the algebra of Ch. IV, Def. 4.2.1.1 of the monograph
"Poetica Mathematica" (K. I. Kovlekov):

    UC = { a + bi + tau*c + tau*d*i | a, b, c, d in R },   i^2 = -1,
          tau^2 = 0,   i*tau = tau*i.

This is the classical algebra of "dual complex numbers" (Study numbers);
the monograph calls them Ultra-Complex (UC) numbers.  Every element has
a unique value/trace decomposition (Def. 4.2.1.3):

    z = val(z) + tau * tr(z),   val(z) = a + bi,  tr(z) = c + di,

and the product is the Leibniz rule (Claim 4.2.1.3):

    z1 * z2 = val1*val2 + tau*(val1*tr2 + val2*tr1).

The vectorised `UC` class stores `value` and `trace` as (arrays of)
complex numbers, so Monte-Carlo work on the Fare-Riemann sphere is fast.
`ExactUC` performs the same arithmetic on exact Fractions and is used by
the test-suite for proofs-by-random-evaluation of the algebra axioms.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Union

import numpy as np

__all__ = ["UC", "ExactUC", "TAU", "I_UNIT"]


Number = Union[int, float, complex, np.number, np.ndarray]


class UC:
    """Element(s) of UC = C[tau]/(tau^2), possibly whole arrays of them.

    Parameters
    ----------
    value, trace : complex scalar or array (broadcastable)
        The element is  z = value + tau * trace.
    """

    __slots__ = ("value", "trace")

    def __init__(self, value=0, trace=0):
        self.value = np.asarray(value, dtype=np.complex128)
        self.trace = np.asarray(trace, dtype=np.complex128)

    # ------------------------------------------------------------------
    # constructors / conversions
    # ------------------------------------------------------------------
    @classmethod
    def from_real4(cls, a, b, c, d):
        """Build from real coordinates: z = a + bi + tau*c + tau*d*i."""
        a, b, c, d = (np.asarray(x, dtype=np.float64) for x in (a, b, c, d))
        return cls(a + 1j * b, c + 1j * d)

    def to_real4(self):
        """Return real coordinates as an array with last axis of length 4."""
        v, t = self.value, self.trace
        return np.stack(
            [np.broadcast_to(v.real, t.real.shape),
             np.broadcast_to(v.imag, t.real.shape),
             np.broadcast_to(t.real, t.real.shape),
             np.broadcast_to(t.imag, t.real.shape)],
            axis=-1,
        )

    # ------------------------------------------------------------------
    # basic accessors (monograph Def. 4.2.1.3)
    # ------------------------------------------------------------------
    def val(self):
        """val(z) = a + bi  -- the value (classically observable part)."""
        return self.value

    def tr(self):
        """tr(z) = c + di  -- the trace (ghost layer)."""
        return self.trace

    def norm_fr(self):
        """Fare-Riemann norm  ||z||_FR = sqrt(a^2+b^2+c^2+d^2)  (Def. 4.2.4.1)."""
        return np.sqrt(np.abs(self.value) ** 2 + np.abs(self.trace) ** 2)

    def is_invertible(self):
        """True where val(z) != 0 (Claim 4.2.1.2: value part must be non-zero)."""
        return np.all(self.value != 0)

    # ------------------------------------------------------------------
    # arithmetic
    # ------------------------------------------------------------------
    @staticmethod
    def multiply(z1: "UC", z2: "UC") -> "UC":
        """Leibniz product rule of Claim 4.2.1.3.

        (v1 + tau t1)(v2 + tau t2) = v1 v2 + tau (v1 t2 + v2 t1).
        """
        v1, t1 = z1.value, z1.trace
        v2, t2 = z2.value, z2.trace
        return UC(v1 * v2, v1 * t2 + v2 * t1)

    def __add__(self, other):
        other = _coerce(other)
        return UC(self.value + other.value, self.trace + other.trace)

    __radd__ = __add__

    def __neg__(self):
        return UC(-self.value, -self.trace)

    def __sub__(self, other):
        other = _coerce(other)
        return UC(self.value - other.value, self.trace - other.trace)

    def __rsub__(self, other):
        other = _coerce(other)
        return other + (-self)

    def __mul__(self, other):
        if isinstance(other, UC):
            return UC.multiply(self, other)
        return UC(self.value * other, self.trace * other)

    __rmul__ = __mul__

    def inverse(self):
        """Inverse of Claim 4.2.1.2:

            (v + tau t)^-1 = 1/v - tau * t / v^2      (v != 0).

        Raises ZeroDivisionError for pure-trace elements, which are zero
        divisors (every x with val(x)=0 satisfies x^2 = 0).
        """
        v, t = self.value, self.trace
        if np.any(v == 0):
            raise ZeroDivisionError(
                "pure-trace element (value == 0): zero divisor, not invertible"
            )
        return UC(1.0 / v, -t / v ** 2)

    def __truediv__(self, other):
        if isinstance(other, UC):
            return self * other.inverse()
        return UC(self.value / other, self.trace / other)

    def __pow__(self, n: int):
        if not isinstance(n, int):
            return NotImplemented
        result = UC(1.0, 0.0)
        base = self
        if n < 0:
            base = self.inverse()
            n = -n
        for _ in range(n):
            result = UC.multiply(result, base)
        return result

    # ------------------------------------------------------------------
    # Fare Principle one-way operation (section 6.6.5)
    # ------------------------------------------------------------------
    def pay_trace(self) -> "UC":
        """Discard the trace layer:  z = val + tau*tr  ->  val.

        The Fare Principle (sec. 6.6.5): trace can be paid (discarded) but
        never created from nothing; this map is idempotent and many-to-one.
        """
        return UC(self.value, np.zeros_like(self.value))

    # ------------------------------------------------------------------
    # comparison / display
    # ------------------------------------------------------------------
    def __eq__(self, other):
        """Exact elementwise equality (array-friendly: returns bool)."""
        if not isinstance(other, UC):
            return NotImplemented
        return bool(np.array_equal(self.value, other.value)
                    and np.array_equal(self.trace, other.trace))

    def __getitem__(self, idx):
        """Mask/integer indexing for point subsets (vectorized use)."""
        return UC(self.value[idx], self.trace[idx])

    def __len__(self):
        return len(self.value)

    def close_to(self, other, atol=1e-10):
        other = _coerce(other)
        return (
            np.allclose(self.value, other.value, atol=atol, rtol=0.0)
            and np.allclose(self.trace, other.trace, atol=atol, rtol=0.0)
        )

    def max_abs(self):
        return float(np.max(np.abs(self.to_real4())))

    def __repr__(self):
        def fmt(x):
            s = np.asarray(x)
            return np.array2string(s, precision=4, separator=",")
        return f"UC(value={fmt(self.value)}, trace={fmt(self.trace)})"


def _coerce(x) -> UC:
    if isinstance(x, UC):
        return x
    return UC(x, 0)


#: the nilpotent generator tau (null-transit operator, sec. 4.2.2)
TAU = UC(0.0, 1.0)
#: the imaginary unit i as a UC element
I_UNIT = UC(1j, 0.0)


# ----------------------------------------------------------------------
# Exact (rational) arithmetic variant -- used by the test-suite to verify
# the algebra laws with zero floating-point doubt.
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class ExactUC:
    """z = a + b i + tau c + tau d i  with all coordinates exact Fractions."""

    a: Fraction = Fraction(0)
    b: Fraction = Fraction(0)
    c: Fraction = Fraction(0)
    d: Fraction = Fraction(0)

    # -- helpers -------------------------------------------------------
    def _cmul(u, v):
        """(u0,u1)*(v0,v1) as Gaussian rationals."""
        return (u[0] * v[0] - u[1] * v[1], u[0] * v[1] + u[1] * v[0])

    def _cadd(u, v):
        return (u[0] + v[0], u[1] + v[1])

    @property
    def _val(self):
        return (self.a, self.b)

    @property
    def _tr(self):
        return (self.c, self.d)

    # -- operations ----------------------------------------------------
    def __add__(self, o: "ExactUC") -> "ExactUC":
        return ExactUC(self.a + o.a, self.b + o.b, self.c + o.c, self.d + o.d)

    def __neg__(self):
        return ExactUC(-self.a, -self.b, -self.c, -self.d)

    def __sub__(self, o: "ExactUC"):
        return self + (-o)

    def __mul__(self, o: "ExactUC") -> "ExactUC":
        """Leibniz rule on exact rationals: v = v1 v2, t = v1 t2 + v2 t1."""
        v = ExactUC._cmul(self._val, o._val)
        t1 = ExactUC._cmul(self._val, o._tr)
        t2 = ExactUC._cmul(o._val, self._tr)
        t = ExactUC._cadd(t1, t2)
        return ExactUC(v[0], v[1], t[0], t[1])

    def norm_sq(self) -> Fraction:
        """||z||_FR^2 = a^2+b^2+c^2+d^2 exactly."""
        return self.a ** 2 + self.b ** 2 + self.c ** 2 + self.d ** 2

    def is_pure_trace(self) -> bool:
        return self.a == 0 and self.b == 0

    def inverse(self) -> "ExactUC":
        """Exact inverse  1/v - tau t / v^2  (valid iff val != 0)."""
        if self.is_pure_trace():
            raise ZeroDivisionError("pure-trace element: zero divisor")
        va, vb = self.a, self.b
        den = va ** 2 + vb ** 2
        # 1/v = conj(v)/|v|^2
        inv_a, inv_b = va / den, -vb / den
        # -t / v^2:  v^2 = (va^2-vb^2) + (2 va vb) i;  dividing by w means
        # multiplying by conj(w)/|w|^2 with |w|^2 = den^2
        w = ExactUC._cmul((va, vb), (va, vb))
        # t / v^2 = t * conj(v^2) / den^2
        conj_w = (w[0], -w[1])
        t = ExactUC._cmul((self.c, self.d), conj_w)
        ta, tb = t[0] / den ** 2, t[1] / den ** 2
        return ExactUC(inv_a, inv_b, -ta, -tb)

    def to_float_uc(self) -> UC:
        return UC(
            complex(float(self.a), float(self.b)),
            complex(float(self.c), float(self.d)),
        )
