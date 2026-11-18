"""Classical Neumann analytical solutions for the Stefan problem.

These are the exact reference solutions every BSP run is validated
against (the professional brings data; the physics brings truth).

One-phase freezing (solid [0, s(t)], liquid at T_m beyond):
    T(x, t) = T_s + (T_m - T_s) erf(x / (2 sqrt(a_s t))) / erf(lam)
    s(t)    = 2 lam sqrt(a_s t)
    lam solves   lam * exp(lam^2) * erf(lam) = Ste / sqrt(pi),
    Ste = c_p (T_m - T_s) / L        (latent-heat number)

One-phase melting (liquid [0, s(t)], solid at T_m beyond): the exact
mirror problem -- the SAME transcendental equation with the liquid
superheat in the Stefan number:
    lam * exp(lam^2) * erf(lam) = Ste / sqrt(pi),
    Ste = c_p (T_s - T_m) / L
(The erfc form belongs to the two-phase problem only, where the
superheated liquid extends to infinity.)

Two-phase freezing (solid [0, s], liquid (s, ...] possibly superheated
or subcooled, different properties per phase):
    T_s(x,t) = T_s + (T_m-T_s) erf(x/(2 sqrt(a_s t)))/erf(lam)
    T_l(x,t) = T_0 - (T_0-T_m) erfc(x/(2 sqrt(a_l t)))/erfc(mu),
    mu = lam sqrt(a_s / a_l),   s(t) = 2 lam sqrt(a_s t)
    lam = Ste_s e^{-lam^2}/(sqrt(pi) erf(lam))
          + Ste_l sqrt(a_l/a_s) e^{-mu^2}/(sqrt(pi) erfc(mu))
    Ste_s = c_ps (T_m - T_s)/L,  Ste_l = c_pl (T_0 - T_m)/L
    (Ste_l > 0 superheated liquid slows freezing; < 0 subcooled
    accelerates; = 0 reduces exactly to the one-phase equation).

DERIVATION CHECK (why the BSP paper's equation is wrong).  From the
Stefan condition rho L s'(t) = k_s dT/dx|_{s-} (one-phase):
    k_s (T_m-T_s) e^{-lam^2} / (sqrt(pi a_s t) erf(lam)) = rho L lam sqrt(a_s/t)
  => e^{-lam^2} / erf(lam) = lam * rho L a_s sqrt(pi) / (k_s (T_m-T_s))
                          = lam * sqrt(pi) * L c_p / (T_m - T_s)
  => lam e^{lam^2} erf(lam) = c_p (T_m-T_s) / (L sqrt(pi)) = Ste/sqrt(pi).
The BSP paper (sec. 12.1 / B.3) prints  e^{-lam^2}/erf(lam) =
L sqrt(pi)/(c_p (T_m-T_s))  -- the lambda factor on the right-hand side
is MISSING (their equation is the correct one evaluated at lam = 1).
For their water/ice case the correct root is lam ~= 0.2455, not the
lam ~= 0.15 they report; `monograph.py` quantifies this.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import erf, erfc

__all__ = ["NeumannOnePhase", "solve_lambda_one_phase",
           "solve_lambda_two_phase", "NeumannTwoPhase", "solve_lambda_melt"]


# ----------------------------------------------------------------------
# root finders
# ----------------------------------------------------------------------
def _brent(f, lo, hi, tol=1e-14, maxiter=200):
    """Bisection with bracket guarantee (robust, no scipy dependency)."""
    flo, fhi = f(lo), f(hi)
    if flo == 0.0:
        return lo
    if fhi == 0.0:
        return hi
    if flo * fhi > 0:
        raise ValueError(f"root not bracketed: f({lo})={flo}, f({hi})={fhi}")
    for _ in range(maxiter):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if fm == 0.0 or (hi - lo) < tol:
            return mid
        if flo * fm < 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


def solve_lambda_one_phase(ste: float) -> float:
    """lambda for one-phase freezing: lam e^{lam^2} erf(lam) = Ste/sqrt(pi)."""
    if ste <= 0:
        raise ValueError("Ste must be positive (T_m - T_s > 0 for freezing)")
    target = ste / np.sqrt(np.pi)
    return _brent(lambda lam: lam * np.exp(lam ** 2) * erf(lam) - target,
                  1e-12, 10.0)


def solve_lambda_melt(ste: float) -> float:
    """lambda for one-phase melting: the mirror of freezing, so the
    same erf equation with Ste = c_p (T_s - T_m)/L."""
    return solve_lambda_one_phase(ste)


def solve_lambda_two_phase(ste_s: float, ste_l: float, ar: float = 1.0) -> float:
    """lambda for two-phase freezing.

    lam = Ste_s e^{-lam^2}/(sqrt(pi) erf(lam))
        + Ste_l sqrt(a_l/a_s) e^{-mu^2}/(sqrt(pi) erfc(mu)),
    mu = lam sqrt(a_s/a_l),  ar = a_l/a_s (diffusivity ratio).

    ste_s > 0 required; ste_l any sign (superheat/subcooling).
    """
    if ste_s <= 0:
        raise ValueError("Ste_s must be positive for freezing")
    sq = np.sqrt(ar)

    def F(lam):
        mu = lam / sq
        return (ste_s * np.exp(-lam ** 2) / (np.sqrt(np.pi) * erf(lam))
                + ste_l * sq * np.exp(-mu ** 2) / (np.sqrt(np.pi) * erfc(mu))
                - lam)

    return _brent(F, 1e-9, 10.0)


# ----------------------------------------------------------------------
# analytical solution objects
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class NeumannOnePhase:
    """Exact one-phase Stefan solution (freezing or melting)."""

    mode: str            # "freezing" | "melting"
    T_s: float           # boundary temperature at x = 0
    T_m: float           # melting point
    lam: float           # Neumann constant
    alpha: float         # thermal diffusivity of the GROWN phase
    k: float             # conductivity of the grown phase
    rho: float
    L: float
    c_p: float

    @classmethod
    def freezing(cls, T_s, T_m, alpha, k, rho, L, c_p):
        ste = c_p * (T_m - T_s) / L
        lam = solve_lambda_one_phase(ste)
        return cls("freezing", T_s, T_m, lam, alpha, k, rho, L, c_p)

    @classmethod
    def melting(cls, T_s, T_m, alpha, k, rho, L, c_p):
        ste = c_p * (T_s - T_m) / L
        lam = solve_lambda_melt(ste)
        return cls("melting", T_s, T_m, lam, alpha, k, rho, L, c_p)

    # ------------------------------------------------------------------
    def ste(self) -> float:
        if self.mode == "freezing":
            return self.c_p * (self.T_m - self.T_s) / self.L
        return self.c_p * (self.T_s - self.T_m) / self.L

    def front(self, t):
        """s(t) = 2 lambda sqrt(alpha t)."""
        t = np.asarray(t, float)
        return 2.0 * self.lam * np.sqrt(self.alpha * np.maximum(t, 0.0))

    def front_velocity(self, t):
        """ds/dt = lambda sqrt(alpha / t) (singular at t = 0)."""
        t = max(float(t), 1e-300)
        return self.lam * np.sqrt(self.alpha / t)

    def profile(self, x, t):
        """Temperature field; x array-like, t > 0 scalar."""
        x = np.asarray(x, float)
        s = float(self.front(t))
        out = np.full_like(x, self.T_m, dtype=float)
        if s <= 0:
            return out
        inside = x <= s
        xi = x[inside] / (2.0 * np.sqrt(self.alpha * t))
        if self.mode == "freezing":
            out[inside] = self.T_s + (self.T_m - self.T_s) * erf(xi) / erf(self.lam)
        else:
            out[inside] = self.T_s - (self.T_s - self.T_m) * erf(xi) / erf(self.lam)
        return out

    def stefan_residual(self, t: float) -> float:
        """Self-consistency: rho L s'(t) - k dT/dx|_{s-} (must be ~0)."""
        s = float(self.front(t))
        grad = ((self.T_m - self.T_s) * np.exp(-(self.lam ** 2))
                / (np.sqrt(np.pi * self.alpha * t) * erf(self.lam)))
        if self.mode == "melting":
            grad = -grad
        return self.rho * self.L * self.front_velocity(t) - self.k * grad


@dataclass(frozen=True)
class NeumannTwoPhase:
    """Exact two-phase Stefan solution (freezing orientation)."""

    T_s: float           # boundary temperature (solid side, x = 0)
    T_m: float
    T_0: float           # initial liquid temperature
    lam: float
    alpha_s: float
    alpha_l: float
    k_s: float
    k_l: float
    rho: float
    L: float
    c_ps: float
    c_pl: float

    @classmethod
    def freezing(cls, T_s, T_m, T_0, alpha_s, alpha_l, k_s, k_l,
                 rho, L, c_ps, c_pl):
        ste_s = c_ps * (T_m - T_s) / L
        ste_l = c_pl * (T_0 - T_m) / L
        lam = solve_lambda_two_phase(ste_s, ste_l, ar=alpha_l / alpha_s)
        return cls(T_s, T_m, T_0, lam, alpha_s, alpha_l, k_s, k_l,
                   rho, L, c_ps, c_pl)

    @property
    def mu(self) -> float:
        return self.lam * np.sqrt(self.alpha_s / self.alpha_l)

    def front(self, t):
        t = np.asarray(t, float)
        return 2.0 * self.lam * np.sqrt(self.alpha_s * np.maximum(t, 0.0))

    def profile(self, x, t):
        x = np.asarray(x, float)
        s = float(self.front(t))
        out = np.where(x <= s, np.nan, np.nan)
        solid = x <= s
        liquid = x > s
        out[solid] = (self.T_s + (self.T_m - self.T_s)
                      * erf(x[solid] / (2 * np.sqrt(self.alpha_s * t)))
                      / erf(self.lam))
        out[liquid] = (self.T_0 - (self.T_0 - self.T_m)
                       * erfc(x[liquid] / (2 * np.sqrt(self.alpha_l * t)))
                       / erfc(self.mu))
        return out

    def stefan_residual(self, t: float) -> float:
        """rho L s'(t) - (k_s dT_s/dx - k_l dT_l/dx)|_{x=s} (must be ~0)."""
        g_s = ((self.T_m - self.T_s) * np.exp(-self.lam ** 2)
               / (np.sqrt(np.pi * self.alpha_s * t) * erf(self.lam)))
        g_l = (-(self.T_0 - self.T_m) * np.exp(-self.mu ** 2)
               / (np.sqrt(np.pi * self.alpha_l * t) * erfc(self.mu)))
        v = self.lam * np.sqrt(self.alpha_s / t)
        return self.rho * self.L * v - (self.k_s * g_s - self.k_l * g_l)
