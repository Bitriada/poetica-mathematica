"""Report generation: markdown report + summary.json + CSV outputs
for one validated case."""

from __future__ import annotations

import json
import os

import numpy as np

from . import figures as F
from .checks import summarize
from .enthalpy import run_enthalpy
from .neumann import NeumannOnePhase
from .solver import run_bsp

__all__ = ["validate_case", "write_outputs"]


def _neumann_for(p):
    alpha = p.k_grown / (p.rho * p.cp_grown)
    if p.mode == "melting":
        return NeumannOnePhase.melting(p.T_s, p.T_m, alpha, p.k_grown,
                                       p.rho, p.L, p.cp_grown)
    return NeumannOnePhase.freezing(p.T_s, p.T_m, alpha, p.k_grown,
                                    p.rho, p.L, p.cp_grown)


def validate_case(p, cfg=None, do_enthalpy=True, do_convergence=True,
                  convergence_levels=4, user_data=None, out_dir=None,
                  make_figures=True, verbose=True):
    """Run the full validation pipeline for one case; returns a dict
    with everything the report needs."""
    from .checks import convergence_study, run_checks

    neu = _neumann_for(p)
    res = run_bsp(p)
    # the enthalpy benchmark is cheap: run it REFINED (dx/4) so the
    # agreement check measures BSP's error against a well-converged
    # reference rather than the sum of two opposite O(dx) biases
    enth = run_enthalpy(p, dx=p.dx / 4.0) if do_enthalpy else None
    conv = None
    if do_convergence:
        if verbose:
            print("convergence study:")
        conv = convergence_study(p, levels=convergence_levels,
                                 with_enthalpy=do_enthalpy, verbose=verbose)
    checks = run_checks(p, res, neu, enth=enth, user_data=user_data,
                        conv=conv)
    return {"params": p, "cfg": cfg or {}, "result": res, "neumann": neu,
            "enthalpy": enth, "convergence": conv, "checks": checks,
            "user_data": user_data, "out_dir": out_dir,
            "make_figures": make_figures}


def _fmt_row(cols, vals):
    return "| " + " | ".join(str(v) for v in vals) + " |"


def write_outputs(bundle, out_dir: str, case_name: str = "case"):
    """Write events.csv, summary.json, report.md, figures."""
    os.makedirs(out_dir, exist_ok=True)
    p = bundle["params"]
    res = bundle["result"]
    neu = bundle["neumann"]
    enth = bundle["enthalpy"]
    conv = bundle["convergence"]
    checks = bundle["checks"]

    # ---- events.csv ---------------------------------------------------
    csv_path = os.path.join(out_dir, "events.csv")
    cols = res.EVENT_COLUMNS
    with open(csv_path, "w") as fh:
        fh.write(",".join(cols) + ",transit_type\n")
        tab = res.event_table()
        for i in range(len(res.t_events)):
            row = ",".join(f"{v:.6g}" if isinstance(v, (int, float,
                                                        np.floating))
                           else str(v) for v in tab[i])
            fh.write(row + "," + res.transit_types[i] + "\n")

    # ---- figures ------------------------------------------------------
    fig_paths = []
    if bundle.get("make_figures", True):
        fig_paths.append(F.plot_validation(
            os.path.join(out_dir, "fig_validation.png"),
            res, neu, enth=enth, conv=conv,
            user_data=bundle.get("user_data"),
            title=f"BSP validation -- {case_name}"))
        fig_paths.append(F.plot_profiles(
            os.path.join(out_dir, "fig_profiles.png"), res, neu,
            title=f"BSP final field -- {case_name}"))
        fig_paths.append(F.plot_clock(
            os.path.join(out_dir, "fig_clock.png"), res,
            title=f"trace-driven clock -- {case_name}"))

    # ---- summary.json -------------------------------------------------
    summary = {
        "case": case_name,
        "params": {k: v for k, v in p.__dict__.items()},
        "lambda_neumann": neu.lam,
        "Ste": neu.ste(),
        "n_events": len(res.t_events),
        "termination": res.termination,
        "t_end_reached": max(res.t_events) if res.t_events else 0.0,
        "s_end": res.s_events[-1] if res.s_events else 0.0,
        "substeps": res.n_substeps,
        "checks": [{"name": c.name, "claim": c.claim,
                    "verdict": c.verdict, "value": c.value,
                    "tolerance": c.tol, "detail": c.detail}
                   for c in checks],
        "n_pass": sum(1 for c in checks if c.verdict == "PASS"),
        "n_graded": sum(1 for c in checks
                        if c.verdict in ("PASS", "MARGINAL", "FAIL")),
    }
    if conv:
        summary["convergence"] = [
            {"dx_mm": c["dx"] * 1e3, "mean_err": c["err"],
             "max_err": c["max_err"], "n_events": c["n_events"],
             **({"enthalpy_err": c["enthalpy_err"]}
                if "enthalpy_err" in c else {})}
            for c in conv]
        dxs = np.array([c["dx"] for c in conv])
        errs = np.array([c["err"] for c in conv])
        summary["convergence_order"] = float(
            np.polyfit(np.log(dxs), np.log(errs), 1)[0])
    with open(os.path.join(out_dir, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2, default=float)

    # ---- report.md ------------------------------------------------------
    md = []
    md.append(f"# BSP validation report -- {case_name}\n")
    md.append("Generated by `bsp` -- the Bitriada Stefan Projection "
              "validation workbench. Every claim of the BSP paper that "
              "this case can test has been checked; the verdicts and "
              "numbers are below.\n")

    md.append("## Case\n")
    md.append(f"- mode: **{p.mode}**, T_m = {p.T_m} {p.temp_unit}, "
              f"T_s = {p.T_s}, T_0 = {p.T_0}")
    md.append(f"- domain: L = {p.length} m, dx = {p.dx} m "
              f"({int(round(p.length / p.dx))} cells), "
              f"t_end = {p.t_end} s")
    md.append(f"- material: rho = {p.rho} kg/m3, L = {p.L} J/kg, "
              f"k_grown = {p.k_grown}, cp_grown = {p.cp_grown}, "
              f"k_bulk = {p.k_bulk}, cp_bulk = {p.cp_bulk}")
    md.append(f"- Neumann constant: lambda = {neu.lam:.4f} "
              f"(Ste = {neu.ste():.4f})")
    md.append(f"- run: {len(res.t_events)} events, "
              f"{res.n_substeps} diffusion substeps, "
              f"termination: {res.termination}\n")

    md.append("## Soundness checks\n")
    md.append("| verdict | check | claim tested | measured | tolerance |")
    md.append("|---|---|---|---|---|")
    for c in checks:
        md.append(_fmt_row(None, [f"**{c.verdict}**", f"`{c.name}`",
                                  c.claim, c.value, c.tol or "--"]))
    md.append("")
    for c in checks:
        if c.detail:
            md.append(f"- **{c.name}**: {c.detail}")
    md.append("")

    if conv:
        md.append("## Grid convergence (Theorem 12.1)\n")
        md.append("| dx [mm] | events | mean err vs Neumann | "
                  "max err | enthalpy diff (matched dx) |")
        md.append("|---|---|---|---|---|")
        for c in conv:
            ent = (f"{c['enthalpy_err']:.3%}"
                   if "enthalpy_err" in c else "--")
            md.append(_fmt_row(None, [f"{c['dx']*1e3:.4f}",
                                      c["n_events"], f"{c['err']:.3%}",
                                      f"{c['max_err']:.3%}", ent]))
        dxs = np.array([c["dx"] for c in conv])
        errs = np.array([c["err"] for c in conv])
        order = float(np.polyfit(np.log(dxs), np.log(errs), 1)[0])
        md.append(f"\nFitted order of accuracy: **{order:.2f}** "
                  "(node-pinned front tracking is expected to be "
                  "~1st order).\n")

    md.append("## Event log (first 15)\n")
    md.append("| n | t [s] | dt [s] | s [m] | v_eff [m/s] | "
              "fare [J/m2] | dS [J/m2K] | transit |")
    md.append("|---|---|---|---|---|---|---|---|")
    tab = res.event_table()
    for i in range(min(15, len(res.t_events))):
        md.append(_fmt_row(None, [
            int(tab[i, 0]), f"{tab[i,1]:.2f}", f"{tab[i,3]:.2f}",
            f"{tab[i,7]:.4f}", f"{tab[i,5]:.3e}", f"{tab[i,9]:.1f}",
            f"{tab[i,10]:.3e}", res.transit_types[i]]))
    md.append("\n(full log in `events.csv`)\n")

    if fig_paths:
        md.append("## Figures\n")
        for fp in fig_paths:
            md.append(f"![{os.path.basename(fp)}]({os.path.basename(fp)})\n")

    with open(os.path.join(out_dir, "report.md"), "w") as fh:
        fh.write("\n".join(md))

    return {"events_csv": csv_path,
            "summary_json": os.path.join(out_dir, "summary.json"),
            "report_md": os.path.join(out_dir, "report.md"),
            "figures": fig_paths, "summary": summary}
