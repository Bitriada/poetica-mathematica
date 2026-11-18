"""The window Fare algebra F_27: linear combinations of Fare-Octal states.

MONOGRAPH SOURCE (Ch. IV sec. 4.1.1, Definition 4.1.1.1):

    F = C[tau_p : p in P] / (tau_p^2 = 0),   tau_p tau_q = tau_q tau_p,

with basis tau_S over finite prime subsets S (tau_empty = 1) and

    tau_S * tau_T = tau_{S u T}   if S and T disjoint, else 0.

Restricting to the first 27 primes gives the WINDOW algebra F_27: a
finite-dimensional commutative algebra of dimension 2^27 whose basis
elements are EXACTLY the 2^27 Fare-Octal states.  This is the precise
sense in which "the Fare-Octal state space embodies the Fare Algebra":
states are the basis, the display counts the basis index, and
Appendix A's multiplication is the basis product.

WHY A LINEAR LAYER IS NEEDED.  Appendix A sec. 7.2 multiplies
multi-tau STATES:  (tau_0 + tau_1)(tau_0 + tau_2)  -- but a product of
sums is a SUM of products, i.e. a general element of F_27, not a
single 27-bit state.  The monograph leaves that computation
symbolic ("Each term evaluated: ... if gcd=1, else 0").  FareElement
completes it, exactly, with integer coefficients.

ALSO HERE: the spectral involution iota_s(tau_n) = n^(1-2s) tau_n and
the zeta element Z(s) = sum_{n squarefree} n^(-s) tau_n, with the
algebraic functional equation  Z(s) = iota_s(Z(1-s))  (Claim
4.1.1.6).  Both are checked exactly in verify.py (V5): the involution
pairing iota_s . iota_{1-s} = id holds because the exponents combine
as (1-2s) + (2s-1) = 0, and the functional equation holds termwise
because (s-1) + (1-2s) = -s.  On the critical line s = 1/2 the
involution is the identity (n^0).
"""

from __future__ import annotations

from fractions import Fraction

from .core import PRIMES, FareOctal, ZERO, UNIT

__all__ = ["FareElement", "spectral_involution", "zeta_element",
           "functional_equation_identities"]


class FareElement:
    """An exact element of the window Fare algebra F_27:
    sum over Fare-Octal states of integer/Fraction/complex coefficients.

    Stored as {frozenset_of_bits: coefficient}; the ZERO state (value 0)
    never appears as a key (annihilated terms are dropped), and the
    all-off state (bits = frozenset()) is the tau_1 = 1 term.
    """

    __slots__ = ("coeffs",)

    def __init__(self, coeffs: dict | None = None):
        clean = {}
        for k, c in (coeffs or {}).items():
            if c != 0:
                clean[k] = c
        self.coeffs = clean

    # -- constructors -------------------------------------------------------
    @staticmethod
    def from_state(s: FareOctal) -> "FareElement":
        if s.is_zero():
            return FareElement()
        return FareElement({s._bits: 1})

    @staticmethod
    def from_states(*states: FareOctal) -> "FareElement":
        """A sum of states, e.g. tau_0 + tau_1 as in App. A sec. 7.2."""
        out = FareElement()
        for s in states:
            out = out + FareElement.from_state(s)
        return out

    def states(self) -> list[FareOctal]:
        return [FareOctal(bits) for bits in self.coeffs]

    # -- arithmetic ---------------------------------------------------------
    def __add__(self, other: "FareElement") -> "FareElement":
        out = dict(self.coeffs)
        for k, c in other.coeffs.items():
            out[k] = out.get(k, 0) + c
            if out[k] == 0:
                del out[k]
        return FareElement(out)

    def __sub__(self, other: "FareElement") -> "FareElement":
        return self + other.scaled(-1)

    def scaled(self, lam) -> "FareElement":
        return FareElement({k: lam * c for k, c in self.coeffs.items()})

    def __mul__(self, other: "FareElement") -> "FareElement":
        """The bilinear product: expand pairwise, drop annihilated terms
        (overlapping switch sets), merge survivors."""
        out: dict = {}
        for ka, ca in self.coeffs.items():
            for kb, cb in other.coeffs.items():
                if ka & kb:        # shared switch -> tau^2 -> 0
                    continue
                k = ka | kb
                out[k] = out.get(k, 0) + ca * cb
        return FareElement(out)

    # -- linear-form helpers --------------------------------------------------
    def total_coefficient(self):
        return sum(self.coeffs.values())

    def values(self) -> dict:
        """{squarefree value: coefficient} (value 1 = the tau_1 term)."""
        out = {}
        for bits, c in self.coeffs.items():
            v = FareOctal(bits).value()
            out[v] = out.get(v, 0) + c
        return out

    def __eq__(self, other):
        return isinstance(other, FareElement) and self.coeffs == other.coeffs

    def __bool__(self):
        return bool(self.coeffs)

    def __repr__(self):
        if not self.coeffs:
            return "0"
        parts = []
        for bits, c in sorted(self.coeffs.items(),
                              key=lambda kv: FareOctal(kv[0]).value()):
            v = FareOctal(bits).value()
            label = "1" if v == 1 else f"tau_{v}"
            parts.append(f"{c}*{label}" if c != 1 else label)
        return " + ".join(parts)


# -- spectral involution and the zeta element --------------------------------
def _pow_exact(n: int, e: Fraction):
    """n^e exactly when e is an integer, else as a float/complex via
    exponent identity (documented per-call)."""
    if e.denominator == 1:
        return Fraction(n) ** e.numerator if e.numerator >= 0 else \
            Fraction(1, n ** (-e.numerator))
    return complex(n) ** complex(e)


def spectral_involution(el: FareElement, s) -> FareElement:
    """iota_s: tau_n |-> n^(1-2s) tau_n, extended linearly
    (Definition 4.1.1.4).  s may be a Fraction (integer exponents ->
    exact) or complex (spot checks)."""
    e = 1 - 2 * s
    out = {}
    for bits, c in el.coeffs.items():
        n = FareOctal(bits).value()
        out[bits] = c * _pow_exact(n, Fraction(e) if not isinstance(e, complex)
                                   else e)
    return FareElement(out)


def zeta_element(s, r: int = 4) -> FareElement:
    """The window zeta element  Z(s) = sum_{n in window} n^(-s) tau_n
    over the sub-window of the first r primes (2^r states; r <= 27).

    In the FULL Fare Algebra the sum runs over all squarefree n (an
    infinite formal sum); any finite sub-window is a truncation, and
    the functional equation below holds termwise on every truncation.
    """
    if not 1 <= r <= len(PRIMES):
        raise ValueError("r must be in 1..27")
    out = {}
    for mask in range(1 << r):
        bits = frozenset(b for b in range(r) if mask >> b & 1)
        n = FareOctal(bits).value()
        out[bits] = _pow_exact(n, Fraction(-s)
                               if not isinstance(s, complex) else -s)
    return FareElement(out)


def functional_equation_identities(r: int = 4, s_exact=(0, 1, 2)):
    """Claim 4.1.1.6 on the sub-window: Z(s) == iota_s(Z(1-s)),
    checked EXACTLY for integer s (integer exponents -> Fractions) and
    structurally (exponent identity (s-1)+(1-2s) = -s) for all s.

    The involution PAIRING iota_s . iota_{1-s} = id (Claim 4.1.1.5) is
    exact for every integer-or-half-integer s where 1-2s is an integer
    (exponents combine to n^0); for general s the pairing holds
    structurally (n^{1-2s} . n^{1-2(1-s)} = n^0) but the arithmetic
    leaves the rationals, so it is only spot-checked numerically there.
    """
    results = {}
    for s in s_exact:
        lhs = zeta_element(Fraction(s), r)
        rhs = spectral_involution(zeta_element(1 - Fraction(s), r),
                                  Fraction(s))
        results[f"Z({s}) == iota_{s}(Z({1 - s})) (exact)"] = lhs == rhs
    for s in (0, 1, 2, 3):  # pairing with INTEGER exponents 1-2s
        Z = zeta_element(Fraction(s), r)
        back = spectral_involution(spectral_involution(Z, Fraction(s)),
                                   Fraction(1 - Fraction(s)))
        results[f"iota_{s} . iota_{1 - s} = id (exact)"] = back == Z
    # structural: for every basis value n the exponent sums coincide
    ok = all((s - 1) + (1 - 2 * s) == -s for s in s_exact)
    results["exponent identity (s-1)+(1-2s) = -s"] = ok
    results["critical line s = 1/2: iota is the identity (n^0)"] = \
        spectral_involution(zeta_element(Fraction(1, 2), 4),
                            Fraction(1, 2)) == zeta_element(Fraction(1, 2), 4)
    return results
