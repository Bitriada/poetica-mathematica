"""ucpoly.py -- UC-polynomials and the path's fare ledger (sec. 8.5).

MONOGRAPH SOURCE (Ch. VIII sec. 8.5, "UC-polynomials"):

* A UC-polynomial has coefficients in UC = R[i, tau]/(i^2+1, tau^2):
  F(x) = sum_i (alpha_i + tau*beta_i) x^i.  "The trace in each
  coefficient is the fare paid at the composition that produced that
  coefficient."
* The convolution rule (the section's central construction):
      (alpha + tau*beta)(alpha' + tau*beta')
          = alpha*alpha' + tau*(alpha*beta' + alpha'*beta)
  -- "a Leibniz-like structure"; by induction every product stays
  LINEAR in tau: "the fare is paid linearly, and the trace cannot
  compound" (tau^2 = 0).
* The fare of F: Fare(F) = sum_i |beta_i|, "the total trace-weight
  across all coefficients"; under multiplication the fare accumulates
  through the cross-convolution terms.

This module implements UC coefficients/polynomials over Z (exact) and
builds the PATH POLYNOMIAL of a voidwell encoding: coefficient i is
the i-th path state's display value (alpha_i) paired with the fare
its step paid (beta_i).  The demonstration's measurements then verify,
on real encodings, the two monograph laws:

  (L1) linearity: Fare(F) = sum of per-step fares exactly (tau^2 = 0
       means no cross-compounding), for any path;
  (L2) the convolution rule: Fare(F * G) equals the cross-convolution
       formula sum_{i+j=k} |alpha_i beta'_j + alpha'_j beta_i| per
       degree, checked against direct polynomial multiplication.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UC:
    """A UC coefficient: alpha + tau*beta (exact integers)."""
    alpha: int = 0
    beta: int = 0

    def __add__(self, o: "UC") -> "UC":
        return UC(self.alpha + o.alpha, self.beta + o.beta)

    def __mul__(self, o: "UC") -> "UC":
        # sec. 8.5: (a + tau b)(a' + tau b') = aa' + tau(ab' + a'b)
        return UC(self.alpha * o.alpha,
                  self.alpha * o.beta + o.alpha * self.beta)

    def fare(self) -> int:
        return abs(self.beta)


class UCPolynomial:
    """Coefficients low-degree first; trailing zeros trimmed."""
    __slots__ = ("coeffs",)

    def __init__(self, coeffs=None):
        c = list(coeffs or [])
        while c and c[-1] == UC(0, 0):
            c.pop()
        self.coeffs = tuple(c)

    def __add__(self, o: "UCPolynomial") -> "UCPolynomial":
        n = max(len(self.coeffs), len(o.coeffs))
        def at(c, i):
            return c.coeffs[i] if i < len(c.coeffs) else UC()
        return UCPolynomial([at(self, i) + at(o, i) for i in range(n)])

    def __mul__(self, o: "UCPolynomial") -> "UCPolynomial":
        if not self.coeffs or not o.coeffs:
            return UCPolynomial()
        out = [UC() for _ in range(len(self.coeffs) + len(o.coeffs) - 1)]
        for i, a in enumerate(self.coeffs):
            for j, b in enumerate(o.coeffs):
                out[i + j] = out[i + j] + a * b
        return UCPolynomial(out)

    def fare(self) -> int:
        """Fare(F) = sum_i |beta_i| (sec. 8.5)."""
        return sum(c.fare() for c in self.coeffs)

    def degree_fares(self) -> list[int]:
        """|beta_k| per degree k (for the convolution check L2)."""
        return [c.fare() for c in self.coeffs]

    def __eq__(self, o):
        return isinstance(o, UCPolynomial) and self.coeffs == o.coeffs

    def __repr__(self):
        return "UCPoly(" + ", ".join(
            f"({c.alpha}+t{c.beta})" for c in self.coeffs) + ")"


def convolution_fares(F: UCPolynomial, G: UCPolynomial) -> list[int]:
    """The sec. 8.5 fare formula for the product F*G, evaluated per
    degree from the cross-convolution:
        beta_k(F*G) = sum_{i+j=k} (alpha_i beta'_j + alpha'_j beta_i)
    (exact -- the formula the monograph states; L2 compares it to the
    direct product's beta coefficients.)"""
    out = [0] * (len(F.coeffs) + len(G.coeffs) - 1 if F.coeffs
                 and G.coeffs else 0)
    for i, a in enumerate(F.coeffs):
        for j, b in enumerate(G.coeffs):
            out[i + j] += a.alpha * b.beta + a.beta * b.alpha
    return [abs(x) for x in out]


def path_polynomial(values: list[int], fares: list[int]) -> UCPolynomial:
    """Coefficient i = (value of D_i) + tau*(fare paid at step i).
    The path's composition history as a UC-polynomial."""
    if len(values) != len(fares):
        raise ValueError("values and fares must align")
    return UCPolynomial([UC(v, f) for v, f in zip(values, fares)])


__all__ = ["UC", "UCPolynomial", "convolution_fares",
           "path_polynomial"]
