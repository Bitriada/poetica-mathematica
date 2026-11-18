"""fare.py -- the Fare Algebra F and its arithmetic (Def. 4.1.1.1).

F = C[tau_p : p prime] / (tau_p^2 = 0)

  * basis {tau_n} indexed by square-free positive integers, tau_1 = 1;
  * multiplication  tau_m * tau_n = tau_{mn}  if gcd(m, n) = 1,
    and 0 otherwise;
  * the collapse map  phi_UC : F -> UC  sends every tau_n with n > 1
    to the single tau, "forgetting which specific prime was recorded
    and retaining only the binary fact that a prime was present"
    (Sec. 4.1.5);
  * the spectral involution  iota_s(tau_n) = n^{1-2s} tau_n
    (Def. 4.1.1.4), the algebraic encoding of the zeta functional
    equation; iota_{1/2} = id is the balance condition that forces
    the Fare-Riemann sphere (Remark 4.2.4.1a);
  * the zeta element  Z(s) = sum_{n square-free} n^{-s} tau_n,
    truncated, satisfying  Z(s) = iota_s(Z(1-s))  (Claim 4.1.1.6).

This module implements a finite truncation: square-free n whose prime
factors lie in a chosen prime list, coefficients as dicts {n: complex}.
"""

from __future__ import annotations

import math
from cmath import exp as _cexp  # noqa: F401
from typing import Dict, List, Optional

from tribit import UC, TAU, TOL
from sphere import first_primes


class FareElem:
    """An element of the truncated Fare Algebra: sum coeff[n] * tau_n."""

    def __init__(self, coeffs: Optional[Dict[int, complex]] = None):
        self.coeffs: Dict[int, complex] = dict(coeffs or {})

    # ---------- algebra ----------

    def __add__(self, o: "FareElem") -> "FareElem":
        out = dict(self.coeffs)
        for n, c in o.coeffs.items():
            out[n] = out.get(n, 0j) + c
        return FareElem({n: c for n, c in out.items() if abs(c) > 1e-15})

    def __mul__(self, o: "FareElem") -> "FareElem":
        out: Dict[int, complex] = {}
        for m, cm in self.coeffs.items():
            for n, cn in o.coeffs.items():
                g = math.gcd(m, n)
                if g == 1:
                    k = m * n
                    out[k] = out.get(k, 0j) + cm * cn
                # gcd > 1: the product carries a repeated prime -> 0
        return FareElem({n: c for n, c in out.items() if abs(c) > 1e-15})

    def __eq__(self, o) -> bool:
        if not isinstance(o, FareElem):
            return NotImplemented
        keys = set(self.coeffs) | set(o.coeffs)
        return all(abs(self.coeffs.get(k, 0j) - o.coeffs.get(k, 0j)) < TOL
                   for k in keys)

    # ---------- structured maps ----------

    def collapse(self) -> UC:
        """phi_UC : F -> UC.

        tau_1 -> 1 (the value); every tau_n, n > 1, -> the single tau
        (the trace).  A ring homomorphism: the coprimality rule maps
        onto the Leibniz rule of UC.
        """
        val = 0j
        tr = 0j
        for n, c in self.coeffs.items():
            if n == 1:
                val += c
            else:
                tr += c
        return UC(val.real, val.imag, tr.real, tr.imag)

    def involution(self, s: complex) -> "FareElem":
        """iota_s(tau_n) = n^{1-2s} * tau_n  (Def. 4.1.1.4)."""
        out = {}
        for n, c in self.coeffs.items():
            out[n] = c * complex(n) ** (1.0 - 2.0 * s)
        return FareElem(out)

    # ---------- display ----------

    def __repr__(self) -> str:
        if not self.coeffs:
            return "0"
        parts = []
        for n in sorted(self.coeffs):
            c = self.coeffs[n]
            parts.append(f"({c:.4f})*tau_{n}")
        return " + ".join(parts)


def tau(n: int, coeff: complex = 1.0 + 0j) -> FareElem:
    """The basis element tau_n (n square-free, or 1 for the unit)."""
    return FareElem({n: complex(coeff)})


def zeta_element(s: complex, max_n: int = 210) -> FareElem:
    """Z(s) = sum_{n square-free <= max_n} n^{-s} * tau_n."""
    from sphere import is_squarefree
    coeffs = {}
    for n in range(1, max_n + 1):
        if is_squarefree(n):
            coeffs[n] = complex(n) ** (-complex(s))
    return FareElem(coeffs)


def functional_equation_holds(s: complex, max_n: int = 210,
                              tol: float = 1e-8) -> bool:
    """Check Z(s) = iota_s(Z(1-s)) on the truncation (Claim 4.1.1.6).

    On the finite algebra the identity is exact for every s (it is a
    termwise identity n^{s-1} * n^{1-2s} = n^{-s}); truncation only
    decides which terms exist.
    """
    lhs = zeta_element(s, max_n)
    rhs = zeta_element(1.0 - s, max_n).involution(s)
    return lhs == rhs or _close(lhs, rhs, tol)


def _close(x: FareElem, y: FareElem, tol: float) -> bool:
    keys = set(x.coeffs) | set(y.coeffs)
    return all(abs(x.coeffs.get(k, 0j) - y.coeffs.get(k, 0j)) < tol
               for k in keys)


def collapse_is_linear(x: FareElem, y: FareElem) -> bool:
    """phi_UC(x + y) = phi_UC(x) + phi_UC(y): a linear surjection.

    The monograph calls phi_UC a linear surjection (Sec. 4.5.2a), not
    a ring homomorphism -- and it cannot be one: phi(tau_2 * tau_3) =
    phi(tau_6) = tau, while phi(tau_2) * phi(tau_3) = tau * tau = 0.
    The collapse records the PRESENCE of primes, not their arithmetic.
    """
    return (x + y).collapse().almost(x.collapse() + y.collapse())


def random_fare(rng, primes: List[int]) -> FareElem:
    """A random Fare element over the given prime basis."""
    import itertools
    basis = [1]
    for r in range(1, 3):  # products of up to 2 distinct primes
        for combo in itertools.combinations(primes, r):
            basis.append(math.prod(combo))
    coeffs = {}
    for n in basis:
        if rng.random() < 0.4:
            coeffs[n] = complex(rng.uniform(-1, 1), rng.uniform(-1, 1))
    return FareElem(coeffs)


def tau_p_times_tau_p_zero() -> bool:
    """tau_p^2 = 0: the nilpotence that keeps the basis square-free."""
    for p in first_primes(6):
        if not (tau(p) * tau(p) == FareElem()):
            return False
    return True
