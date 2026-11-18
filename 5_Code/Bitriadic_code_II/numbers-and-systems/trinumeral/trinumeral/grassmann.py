"""The graded exterior algebra L(V) of the heterobase trace, exactly.

MONOGRAPH SOURCE: Poetica Mathematica, Ch. VIII sec. 8.4.2 ("The Trace
as a Graded Algebra"):

    "The trace tau lives in a graded exterior algebra on three
     generators:  tau in Lambda(V) where V = span(e1, e2, e3).
     The three generators correspond to the three conversion edges:
     e1 for the binary-to-integer discrepancy, e2 for the
     integer-to-float discrepancy, e3 for the float-to-binary
     discrepancy.  Each generator is nilpotent: e1^2 = e2^2 = e3^2 = 0.
     The generators anticommute: e1 e2 = -e2 e1, e2 e3 = -e3 e2,
     e3 e1 = -e1 e3."

and sec. 8.4.7 ("The 117-Point Lattice"):

    "The three binary edges produce 2^3 = 8 possible activation
     patterns."

Those 8 patterns are exactly the 8 basis monomials of L(V) on three
generators -- Pascal's row (1, 3, 3, 1) by grade -- which is how the
activation state space is implemented here: an element is a mapping
from index-set (the active-edge set) to an exact rational coefficient,
and its grade counts active edges.

Everything is exact: coefficients are fractions.Fraction; there are no
floats in the algebra layer.
"""

from __future__ import annotations

from fractions import Fraction

__all__ = ["GrassmannElement", "E1", "E2", "E3", "TOP", "ZERO",
           "scalar", "generator", "wedge", "grade", "parse_monomial"]


class GrassmannElement:
    """An element of the exterior algebra: monomial -> coefficient.

    A monomial is a frozenset of generator indices (0 = e1, 1 = e2,
    2 = e3, ...); e.g. frozenset({0, 2}) is e1 ^ e3.  Immutable in
    spirit; operations return new elements.  Coefficients are exact
    Fractions.
    """

    __slots__ = ("terms",)

    def __init__(self, terms=None):
        # terms: dict[frozenset[int], Fraction]; zeros dropped
        clean = {}
        for k, v in (terms or {}).items():
            v = Fraction(v)
            if v != 0:
                clean[frozenset(k)] = v
        object.__setattr__(self, "terms", clean)

    # -- constructors --------------------------------------------------------
    @staticmethod
    def scalar(x) -> "GrassmannElement":
        return GrassmannElement({frozenset(): Fraction(x)})

    @staticmethod
    def generator(index: int) -> "GrassmannElement":
        return GrassmannElement({frozenset((index,)): Fraction(1)})

    # -- vector space ---------------------------------------------------------
    def __add__(self, other):
        out = dict(self.terms)
        for k, v in other.terms.items():
            out[k] = out.get(k, Fraction(0)) + v
        return GrassmannElement(out)

    def __neg__(self):
        return GrassmannElement({k: -v for k, v in self.terms.items()})

    def __sub__(self, other):
        return self + (-other)

    def __eq__(self, other):
        return isinstance(other, GrassmannElement) \
            and self.terms == other.terms

    def __hash__(self):
        return hash(tuple(sorted((tuple(sorted(k)), v)
                                 for k, v in self.terms.items())))

    # -- the wedge product ------------------------------------------------------
    def __mul__(self, other: "GrassmannElement") -> "GrassmannElement":
        """The exterior (wedge) product.  Nilpotence (e ^ e = 0) and
        anticommutation (e1 ^ e2 = -e2 ^ e1) are structural: a shared
        index annihilates the monomial; merging sorted index lists
        contributes the parity of the shuffle."""
        out = {}
        for ka, va in self.terms.items():
            for kb, vb in other.terms.items():
                if ka & kb:                       # nilpotence: e ^ e = 0
                    continue
                key = frozenset(ka | kb)
                sign = _shuffle_sign(sorted(ka), sorted(kb))
                out[key] = out.get(key, Fraction(0)) \
                    + va * vb * sign
        return GrassmannElement(out)

    wedge = __mul__

    def __rmul__(self, k):
        """Scalar multiple: Fraction * element."""
        return GrassmannElement({m: k * v for m, v in self.terms.items()})

    # -- accessors -----------------------------------------------------------------
    def coefficient(self, *indices) -> Fraction:
        """The coefficient of the monomial on exactly these generators."""
        return self.terms.get(frozenset(indices), Fraction(0))

    def is_zero(self) -> bool:
        return not self.terms

    def grade(self):
        """The set of grades present (a scalar has grade 0, e1 grade 1,
        e1^e2^e3 grade 3 ...)."""
        return {len(k) for k in self.terms}

    def activation(self, n_gens=3):
        """The activation pattern (sec. 8.4.7): which edges carry a
        nonzero GRADE-1 coefficient -- a tuple of 3 booleans, one of
        the 2^3 = 8 lattice patterns."""
        return tuple(self.coefficient(j) != 0 for j in range(n_gens))

    # -- display -----------------------------------------------------------------------
    def __repr__(self):
        if not self.terms:
            return "0"
        parts = []
        for k in sorted(self.terms, key=lambda s: (len(s), sorted(s))):
            v = self.terms[k]
            if not k:                                  # scalar monomial
                parts.append(str(v))
                continue
            label = "^".join(f"e{g + 1}" for g in sorted(k))
            if v == 1:
                parts.append(label)
            elif v == -1:
                parts.append("-" + label)
            else:
                parts.append(f"{v}*{label}")
        return " + ".join(parts).replace(" + -", " - ")


def _shuffle_sign(a, b):
    """Parity sign for merging two sorted index lists (antisymmetric
    exterior structure): (-1)^(number of pairs (x in a, y in b), x > y)."""
    inversions = sum(1 for x in a for y in b if x > y)
    return -1 if inversions % 2 else 1


def parse_monomial(name: str) -> GrassmannElement:
    """'e1' -> generator 0; 'e2^e3' -> e2^e3; '1' -> scalar 1."""
    if name == "1":
        return GrassmannElement.scalar(1)
    el = GrassmannElement()
    for tok in name.split("^"):
        idx = int(tok[1:]) - 1
        el = el * GrassmannElement.generator(idx)
    return el


ZERO = GrassmannElement()
E1 = GrassmannElement.generator(0)
E2 = GrassmannElement.generator(1)
E3 = GrassmannElement.generator(2)
TOP = E1 * E2 * E3          # e1 ^ e2 ^ e3, the tau-cycle carrier


def scalar(x) -> GrassmannElement:
    return GrassmannElement.scalar(x)


def generator(index: int) -> GrassmannElement:
    return GrassmannElement.generator(index)


def wedge(*elements):
    acc = GrassmannElement.scalar(1)
    for e in elements:
        acc = acc * e
    return acc


def grade(element: GrassmannElement):
    return element.grade()
