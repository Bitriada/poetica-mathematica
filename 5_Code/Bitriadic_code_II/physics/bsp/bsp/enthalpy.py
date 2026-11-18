"""Independent enthalpy-method reference solver (the industry standard).

This is the benchmark every BSP run is compared against.  It is
deliberately INDEPENDENT of the BSP machinery: a fixed-grid apparent-
heat-capacity enthalpy scheme on its own uniform grid with its own
time step, as used in thermal engineering (the apparent-capacity
approach of commercial phase-change codes).

Formulation (phase properties by TEMPERATURE, not by "grown/bulk"):
    H(T): sensible + latent, solid = reference state
        T < T_m:   H = rho cp_s (T - T_m)              (solid, H < 0)
        T = T_m:   H in [0, rho L]                      (mushy band)
        T > T_m:   H = rho L + rho cp_l (T - T_m)       (liquid)
    conduction:  dH/dt = d/dx ( k_s/l dT/dx ),  face conductivities by
    harmonic average of the adjacent node phases
    interface position: linear interpolation of H through rho L / 2
    (the mid-mushy isotherm ~ T_m), which converges to the sharp
    interface with grid refinement (sub-cell resolution).

Discretization: explicit FTCS on enthalpy with per-step inversion of
the piecewise-linear H(T).  Time step: a fraction of the stability
limit.  First order in time, second in space -- the same order as the
BSP FTCS core, so the comparison is apples-to-apples.  Boundary
conditions mirror the BSP setup: Dirichlet T_s at x = 0, initial
temperature held at x = L.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["EnthalpyResult", "run_enthalpy"]


@dataclass
class EnthalpyResult:
    t_grid: np.ndarray            # saved times
    s_grid: np.ndarray            # front positions (H-interpolated)
    T_profiles: list = field(default_factory=list)   # saved fields
    T_profile_times: list = field(default_factory=list)
    H_final: np.ndarray = None
    T_final: np.ndarray = None
    n_steps: int = 0
    dt: float = 0.0

    def front_at(self, t):
        """Front position interpolated to the given times."""
        return np.interp(t, self.t_grid, self.s_grid)


def _T_of_H(H, rho, L, cp_s, cp_l, T_m):
    """Invert the piecewise-linear enthalpy relation (vectorized)."""
    T = np.empty_like(H)
    solid = H <= 0.0
    mushy = (H > 0.0) & (H < rho * L)
    liquid = H >= rho * L
    T[solid] = T_m + H[solid] / (rho * cp_s)
    T[mushy] = T_m
    T[liquid] = T_m + (H[liquid] - rho * L) / (rho * cp_l)
    return T


def run_enthalpy(p, n_save: int = 400, dx: float = None) -> EnthalpyResult:
    """Run the enthalpy reference for the same case as a BSPParams p.

    `dx` optionally overrides the grid spacing: the enthalpy scheme is
    cheap and vectorized, so running it REFINED (e.g. dx/4) gives a
    well-converged benchmark.  Note the nodal-enthalpy front estimator
    carries its own O(dx) lag (the latent of a node represents its
    whole control volume), so at MATCHED dx the enthalpy and BSP front
    differ by up to ~one cell in opposite directions -- both converge,
    with first order.
    """
    freezing = p.mode == "freezing"
    # phase properties (by temperature side, not grown/bulk)
    if freezing:
        cp_s, k_s = p.cp_grown, p.k_grown
        cp_l, k_l = p.cp_bulk, p.k_bulk
    else:
        cp_s, k_s = p.cp_bulk, p.k_bulk
        cp_l, k_l = p.cp_grown, p.k_grown
    rho, L, T_m = p.rho, p.L, p.T_m

    dx_eff = float(dx) if dx is not None else p.dx
    N = int(round(p.length / dx_eff))
    x = np.arange(N + 1) * dx_eff

    def H_of_T(T):
        """Enthalpy from temperature (vectorized, exact piecewise)."""
        return (rho * cp_s * np.minimum(T - T_m, 0.0)
                + rho * cp_l * np.maximum(T - T_m, 0.0)
                + rho * L * (T > T_m))

    # initial state: the BULK PHASE everywhere -- the phase is part of
    # the initial condition and cannot be inferred from T alone when
    # T_0 == T_m (H(T_m) is ambiguous by exactly one latent jump)
    if freezing:
        H_bulk = rho * L + rho * cp_l * (p.T_0 - T_m)   # liquid initial
    else:
        H_bulk = rho * cp_s * (p.T_0 - T_m)             # solid initial
    H = np.full(N + 1, H_bulk)
    H[0] = H_of_T(np.array([p.T_s]))[0]     # Dirichlet boundary

    dt = 0.4 * dx_eff ** 2 / (2.0 * max(k_s / (rho * cp_s), k_l / (rho * cp_l)))
    n_total = int(np.ceil(p.t_end / dt))
    save_every = max(1, n_total // n_save)

    res = EnthalpyResult(t_grid=[], s_grid=[], dt=dt)
    mid = 0.5 * rho * L

    def front_position(Hf):
        """Mid-front: linear interpolation of H through rho L / 2."""
        i = np.nonzero((Hf[:-1] - mid) * (Hf[1:] - mid) <= 0)[0]
        if len(i) == 0:
            return 0.0 if Hf[N] > mid else float(p.length)
        i = i[0]
        if Hf[i + 1] == Hf[i]:
            return x[i]
        return x[i] + dx_eff * (mid - Hf[i]) / (Hf[i + 1] - Hf[i])

    t, step = 0.0, 0
    while t < p.t_end - 1e-12:
        T = _T_of_H(H, rho, L, cp_s, cp_l, T_m)
        # face conductivities: harmonic mean of adjacent node phases
        solid = H <= mid
        kn = np.where(solid, k_s, k_l)
        kf = 2.0 * kn[:-1] * kn[1:] / (kn[:-1] + kn[1:])   # faces i+1/2
        Hn = H.copy()
        Hn[1:N] = H[1:N] + dt * (kf[1:N] * (T[2:N + 1] - T[1:N])
                                 - kf[0:N - 1] * (T[1:N] - T[0:N - 1])) / dx_eff ** 2
        Hn[0] = H_of_T(np.array([p.T_s]))[0]
        Hn[N] = H_bulk                            # far Dirichlet = bulk
        H = Hn
        t += dt
        step += 1
        if step % save_every == 0 or t >= p.t_end - 1e-12:
            res.t_grid.append(t)
            res.s_grid.append(front_position(H))
            if len(res.T_profiles) < 40:
                res.T_profiles.append(_T_of_H(H, rho, L, cp_s, cp_l, T_m).copy())
                res.T_profile_times.append(t)

    res.t_grid = np.array(res.t_grid)
    res.s_grid = np.array(res.s_grid)
    res.H_final = H
    res.T_final = _T_of_H(H, rho, L, cp_s, cp_l, T_m)
    res.n_steps = step
    return res
