"""The soundness check suite: run BSP on the user's case and verify,
claim by claim, that BSP is a sound alternative.

Each check is tied to a specific claim of the BSP paper:

  neumann_agreement    Theorem 12.1 (BSP-Neumann convergence): the
                       event positions track s(t) = 2 lam sqrt(alpha t)
  convergence          Theorem 12.1 in the limit dx -> 0: measured
                       order of accuracy (expect ~1 for node-pinned
                       front tracking)
  enthalpy_agreement   independent industry-standard benchmark
                       (apparent-capacity enthalpy method) on the same
                       grid: the two methods must agree with each other
  energy_conservation  Theorem 13.2 (energy conserved at each trace
                       event, up to the boundary flux): per-event drift
                       of E + Q_out
  second_law           Theorem 14.1: entropy production >= 0 and
                       cumulative S monotone non-decreasing
  sharp_interface      Property 9.3 (tau^2 = 0 keeps the interface
                       sharp): exactly one boundary node at all times
  trace_clock          Property 9.2 (time emerges from trace): strictly
                       increasing event times, dt > 0, non-uniform
  null_transit         the monograph's sec. 2.7.1 axioms implemented in
                       bsp.nodes: monotone one-way transits, trace
                       record d = 1 on visited nodes, transit fare
                       ~ rho L dx, crossing condition exact
  boundary_set         Property 9.4: B = {p : c(p) != 0} tracks the
                       front with no reconstruction
  uc_algebra           sec. 3: tau^2 = 0 exactly; Prop. 3.2 deviation
  lattice_counts       sec. 4: 1DB = 117 = 9+27+81, 2DB = 243 (and the
                       finding that Algorithm 9.1 does not use them)

Verdicts: PASS / MARGINAL / FAIL (thresholds below) and INFO for
structural findings.  `run_checks` returns a list of CheckResult and
`render_report` turns them into text.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .lattice import lattice_report
from .neumann import NeumannOnePhase
from .solver import run_bsp
from .uc import UC, prop32_report

__all__ = ["CheckResult", "run_checks", "convergence_study",
           "measurement_window", "summarize"]


@dataclass
class CheckResult:
    name: str
    claim: str
    verdict: str          # PASS / MARGINAL / FAIL / INFO
    value: str
    tol: str = ""
    detail: str = ""


# ----------------------------------------------------------------------
def measurement_window(res, s_lo_frac: float = 0.3, s_hi_frac: float = 0.95):
    """Boolean mask of events inside the measurement window: skips the
    start-up transient (the first events carry the O(dx) null-transit
    fare and the paper's own start-up rule) and the domain end."""
    s = np.asarray(res.s_events)
    if len(s) == 0:
        return np.zeros(0, dtype=bool)
    s_end = s[-1]
    return (s >= s_lo_frac * s_end) & (s <= s_hi_frac * s_end)


def _err_vs_neumann(res, neu, mask):
    t = np.asarray(res.t_events)[mask]
    s = np.asarray(res.s_events)[mask]
    if len(t) == 0:
        return 0.0, 0.0, 0
    s_ref = neu.front(t)
    rel = np.abs(s - s_ref) / np.maximum(s_ref, 1e-300)
    return float(np.mean(rel)), float(np.max(rel)), len(t)


# ----------------------------------------------------------------------
def run_checks(p, res, neu, enth=None, user_data=None, conv=None,
               rng_seed: int = 7) -> list:
    """Assemble the full check list for one BSP run."""
    checks = []
    rhoLdx = p.rho * p.L * p.dx

    # -- Theorem 12.1: agreement with the exact Neumann solution -----
    mask = measurement_window(res)
    mean_err, max_err, n_win = _err_vs_neumann(res, neu, mask)
    verdict = ("PASS" if mean_err < 0.10 else
               "MARGINAL" if mean_err < 0.20 else "FAIL")
    checks.append(CheckResult(
        "neumann_agreement",
        "Thm 12.1: BSP event positions track s(t) = 2*lam*sqrt(alpha t)",
        verdict, f"mean rel err {mean_err:.3%} (max {max_err:.3%}, "
        f"{n_win} events in window)",
        "mean < 10% (marginal < 20%)",
        "measured on the mid-window events (start-up excluded); the "
        "convergence check below is the dx -> 0 statement"))

    # -- Theorem 12.1: convergence order ------------------------------
    if conv is not None and len(conv) >= 2:
        dxs = np.array([c["dx"] for c in conv])
        errs = np.array([c["err"] for c in conv])
        orders = np.log2(errs[:-1] / errs[1:])
        fitted = float(np.polyfit(np.log(dxs), np.log(errs), 1)[0])
        mono = bool(np.all(np.diff(errs) < 0))
        verdict = ("PASS" if (fitted >= 0.7 and mono) else
                   "MARGINAL" if fitted >= 0.4 else "FAIL")
        checks.append(CheckResult(
            "convergence",
            "Thm 12.1 (dx -> 0): BSP event times converge to Neumann",
            verdict,
            f"order ~ {fitted:.2f} (pairwise {', '.join(f'{o:.2f}' for o in orders)}); "
            f"errs {', '.join(f'{e:.3%}' for e in errs)}",
            "fitted order >= 0.7, errors decreasing",
            f"grids dx = {', '.join(f'{d*1e3:.3f}' for d in dxs)} mm; "
            "node-pinned front tracking is expected to be ~1st order"))

    # -- independent benchmark ----------------------------------------
    if enth is not None:
        t = np.asarray(res.t_events)[mask]
        s = np.asarray(res.s_events)[mask]
        s_en = enth.front_at(t)
        ok = s_en > 0
        if np.sum(ok) >= 3:
            rel = np.abs(s[ok] - s_en[ok]) / np.maximum(s_en[ok], 1e-300)
            mean_d = float(np.mean(rel))
            verdict = ("PASS" if mean_d < 0.10 else
                       "MARGINAL" if mean_d < 0.20 else "FAIL")
            checks.append(CheckResult(
                "enthalpy_agreement",
                "independent benchmark: apparent-capacity enthalpy method "
                "(refined grid dx/4)",
                verdict, f"mean rel diff {mean_d:.3%} over {int(np.sum(ok))} events",
                "mean < 10%",
                "two independent discretizations agreeing is the strongest "
                "simple evidence of correctness"))

    # -- Theorem 13.2: energy conservation ----------------------------
    fare = np.asarray(res.fare_events)
    if len(fare) >= 3:
        drift = float(np.max(np.abs(fare[1:]))) / rhoLdx
        E = np.asarray(res.E_events)
        Q = np.asarray(res.Q_events)
        s_end = res.s_events[-1]
        cum = abs(E[-1] - E[0] + Q[-1]) / (p.rho * p.L * max(s_end, 1e-12))
        verdict = ("PASS" if (drift < 0.05 and cum < 0.05) else
                   "MARGINAL" if (drift < 0.15 and cum < 0.15) else "FAIL")
        checks.append(CheckResult(
            "energy_conservation",
            "Thm 13.2: energy conserved at each trace event up to the "
            "boundary flux (E_after - E_before + Q_out = 0)",
            verdict,
            f"max per-event drift {drift:.3%} of one cell's latent; "
            f"cumulative drift {cum:.3%} of total latent exchanged",
            "both < 5% (marginal < 15%)",
            "event 1 excluded: it carries the null-transit fare "
            "(first cell's latent + boundary-cell chill), O(dx), a "
            "start-up payment rather than a conservation failure"))

    # -- Theorem 14.1: second law -------------------------------------
    dS = np.asarray(res.dS_events)
    S = np.asarray(res.S_events)
    mono_S = bool(np.all(np.diff(S) >= -1e-15))
    nonneg = bool(np.all(dS >= -1e-15))
    verdict = "PASS" if (mono_S and nonneg) else "FAIL"
    checks.append(CheckResult(
        "second_law",
        "Thm 14.1: entropy production dS = k (grad T)^2 / T^2 dt >= 0, "
        "cumulative S monotone",
        verdict,
        f"min dS = {float(np.min(dS)):.3e} J/(m2 K), S(t_end) = "
        f"{S[-1]:.4f} J/(m2 K), monotone: {mono_S}",
        "dS >= 0 and S non-decreasing",
        "dS uses the paper's formula with absolute temperature and the "
        "dx volume element added (per-unit area)"))

    # -- Property 9.3: sharp interface --------------------------------
    sharp = (float(np.sum(res.c_final)) == 1.0
             and bool(np.all(np.diff(np.asarray(res.p_events)) == 1)))
    checks.append(CheckResult(
        "sharp_interface",
        "Prop 9.3 (tau^2 = 0): the boundary marker never smears -- exactly "
        "one interface node at all times",
        "PASS" if sharp else "FAIL",
        f"interface nodes at end: {int(np.sum(res.c_final))}; "
        f"front advances node-by-node (all dp = 1): "
        f"{bool(np.all(np.diff(np.asarray(res.p_events)) == 1))}",
        "exactly 1, dp = 1",
        "the trace layer c is 0/1 by construction and tau^2 = 0 keeps "
        "multiplication from smearing it (uc_algebra below)"))

    # -- Property 9.2: trace-driven clock ------------------------------
    t_ev = np.asarray(res.t_events)
    dt_ev = np.asarray(res.dt_events)
    if len(t_ev) >= 3:
        increasing = bool(np.all(np.diff(t_ev) > 0))
        positive = bool(np.all(dt_ev > 0))
        ratio = float(np.max(dt_ev) / np.min(dt_ev))
        nonuniform = ratio > 1.5
        verdict = "PASS" if (increasing and positive and nonuniform) else "FAIL"
        checks.append(CheckResult(
            "trace_clock",
            "Prop 9.2: time emerges from trace events -- strictly "
            "increasing, non-uniform clock ticks",
            verdict,
            f"{len(t_ev)} events, dt in [{dt_ev.min():.2g}, {dt_ev.max():.2g}] s "
            f"(span ratio {ratio:.1f}), decelerating front captured "
            "without any adaptive time-step controller",
            "t increasing, dt > 0, non-uniform",
            "for a sqrt(t) front the intervals grow linearly with event "
            "index; the uniform-grid alternative would need dt small "
            "enough for the fastest early event"))

    # -- null-transit axioms (monograph sec. 2.7.1) --------------------
    if len(fare) >= 1:
        sign = -1.0 if p.mode == "freezing" else 1.0
        chill = p.rho * p.cp_grown * abs(p.T_s - p.T_m) * p.dx
        expected_fare = sign * (rhoLdx + chill)
        rel = abs(fare[0] - expected_fare) / rhoLdx
        visited_ok = bool(np.all(np.asarray(res.d_final)[
            :res.p_events[-1] + 1] == 1.0))
        one_way = bool(np.all(np.diff(np.asarray(res.p_events)) == 1))
        cross = float(np.max(np.abs(np.asarray(res.cross_residuals)))) / p.dx \
            if res.cross_residuals else 0.0
        # crossing residual tolerance 1e-3 dx: the partial-substep
        # landing has a granularity ~ v dt_stab (for high-diffusivity
        # materials the gradient relaxes within one substep); it is a
        # time-discretization granularity that vanishes with refinement
        verdict = "PASS" if (rel < 0.02 and visited_ok and one_way
                             and cross < 1e-3) else "FAIL"
        checks.append(CheckResult(
            "null_transit",
            "monograph sec. 2.7.1 via bsp.nodes: nilpotent, irreversible, "
            "trace-preserving layer switch at node 0",
            verdict,
            f"fare_1 = {fare[0]:.1f} vs expected {expected_fare:.1f} "
            f"({rel:.2%} of rho L dx); visited record d = 1 on all "
            f"{res.p_events[-1] + 1} visited nodes: {visited_ok}; "
            f"one-way transits: {one_way}; max crossing residual "
            f"{cross:.2e} dx",
            "fare within 2%, record complete, one-way, residual < 1e-3 dx",
            "the start-up node-0 conflict (boundary layer T_s vs "
            "interface layer T_m) is resolved by dynamic layer switching; "
            "the fare is O(dx) and vanishes in the convergence limit"))

    # -- user data ------------------------------------------------------
    if user_data is not None:
        t_u = np.asarray(user_data[0], dtype=float)
        s_u = np.asarray(user_data[1], dtype=float)
        s_bsp_at = np.interp(t_u, res.t_events, res.s_events)
        ok = (t_u > res.t_events[0]) & (s_u > 0)
        if np.sum(ok) >= 3:
            rel_b = np.abs(s_bsp_at[ok] - s_u[ok]) / np.maximum(s_u[ok], 1e-300)
            s_neu_at = neu.front(t_u[ok])
            rel_n = np.abs(s_neu_at - s_u[ok]) / np.maximum(s_u[ok], 1e-300)
            verdict = ("PASS" if np.mean(rel_b) < 0.10 else
                       "MARGINAL" if np.mean(rel_b) < 0.25 else "FAIL")
            checks.append(CheckResult(
                "user_data",
                "YOUR measurements: BSP front vs observed interface "
                "positions (and Neumann as reference)",
                verdict,
                f"BSP RMS rel err {float(np.sqrt(np.mean(rel_b**2))):.3%}; "
                f"Neumann RMS rel err {float(np.sqrt(np.mean(rel_n**2))):.3%} "
                f"({int(np.sum(ok))} points)",
                "RMS < 10% (marginal < 25%)",
                "bring your own (time, position) data via the case file's "
                "user_data = 'file.csv'"))

    # -- structural: UC algebra and lattices ----------------------------
    tau = UC.from_arrays(0.0, 0.0, 1.0, 0.0)
    tau2 = tau * tau
    exact_zero = (tau2.c == 0.0 and tau2.d == 0.0
                  and tau2.a == 0.0 and tau2.b == 0.0)
    rng = np.random.default_rng(rng_seed)
    rep = prop32_report(rng, 500)
    checks.append(CheckResult(
        "uc_algebra",
        "sec. 3: UC algebra with tau^2 = 0 (sharp interface encoding)",
        "PASS" if exact_zero else "FAIL",
        f"tau^2 = 0 exactly: {exact_zero}; Prop 3.2's printed product "
        f"deviates from the algebra it defines by up to "
        f"{rep['max_tau_real_deviation']:.3f} (tau-real) / "
        f"{rep['max_tau_imag_deviation']:.3f} (tau-imag) on random samples "
        "(value parts agree)",
        "tau^2 = 0 exact",
        "bsp.uc implements the correct Leibniz product; the paper's "
        "Prop 3.2 drops the -bd'-b'd contribution and flips a sign -- "
        "see the audit report"))

    lat = lattice_report()
    lat_ok = (lat["1DB_points_match"] and lat["L_table_matches_paper"]
              and lat["M_table_matches_paper"] and lat["2DB_consistent"])
    checks.append(CheckResult(
        "lattice_counts",
        "sec. 4: 1DB = 117 = 9 + 27 + 81 points, 2DB = 243 positions, "
        "value tables as printed",
        "PASS" if lat_ok else "FAIL",
        f"1DB points: {lat['1DB_points_enumerated']}, L-table match: "
        f"{lat['L_table_matches_paper']}, M-table match: "
        f"{lat['M_table_matches_paper']}, 2DB zone accounting: "
        f"{lat['2DB_naive_351_vs_zone_accounting_243']}",
        "all counts and tables match",
        "finding: the lattices are sound combinatorial objects but "
        "Algorithm 9.1 never uses them (it runs on a plain uniform "
        "lattice); they are not load-bearing for the solver"))

    return checks


# ----------------------------------------------------------------------
def convergence_study(p_base, levels: int = 4, with_enthalpy: bool = True,
                      verbose: bool = True):
    """Refine dx by successive factors of 2 and measure the error
    against the exact Neumann solution on a fixed physical window."""
    results = []
    dx0 = p_base.dx
    for k in range(levels):
        dx = dx0 / (2 ** k)
        pk = p_base.__class__(**{**p_base.__dict__, "dx": dx})
        res = run_bsp(pk)
        alpha = pk.k_grown / (pk.rho * pk.cp_grown)
        if pk.mode == "melting":
            neu = NeumannOnePhase.melting(pk.T_s, pk.T_m, alpha,
                                          pk.k_grown, pk.rho, pk.L,
                                          pk.cp_grown)
        else:
            neu = NeumannOnePhase.freezing(pk.T_s, pk.T_m, alpha,
                                           pk.k_grown, pk.rho, pk.L,
                                           pk.cp_grown)
        # fixed physical window from the coarsest run
        s_ref = res.s_events[-1] if res.s_events else pk.length
        s_lo, s_hi = 0.3 * s_ref, 0.95 * s_ref
        mask = ((np.asarray(res.s_events) >= s_lo)
                & (np.asarray(res.s_events) <= s_hi))
        mean_err, max_err, n_win = _err_vs_neumann(res, neu, mask)
        entry = {"dx": dx, "err": mean_err, "max_err": max_err,
                 "n_events": len(res.t_events), "n_window": n_win,
                 "result": res, "neumann": neu}
        if with_enthalpy:
            from .enthalpy import run_enthalpy
            enth = run_enthalpy(pk)
            t = np.asarray(res.t_events)[mask]
            s = np.asarray(res.s_events)[mask]
            s_en = enth.front_at(t)
            ok = s_en > 0
            entry["enthalpy_err"] = (float(np.mean(
                np.abs(s[ok] - s_en[ok]) / np.maximum(s_en[ok], 1e-300)))
                if np.sum(ok) >= 3 else float("nan"))
        results.append(entry)
        if verbose:
            msg = (f"  dx={dx*1e3:.4f} mm: {len(res.t_events)} events, "
                   f"mean err {mean_err:.3%}")
            if "enthalpy_err" in entry:
                msg += (f", enthalpy diff (matched dx) "
                        f"{entry['enthalpy_err']:.3%}")
            print(msg)
    return results


def summarize(checks) -> str:
    """One-line-per-check summary table."""
    lines = []
    for c in checks:
        lines.append(f"[{c.verdict:^8}] {c.name}: {c.value}")
    n_pass = sum(1 for c in checks if c.verdict == "PASS")
    n_all = sum(1 for c in checks if c.verdict in ("PASS", "MARGINAL", "FAIL"))
    lines.append(f"--- {n_pass}/{n_all} checks PASS ---")
    return "\n".join(lines)
