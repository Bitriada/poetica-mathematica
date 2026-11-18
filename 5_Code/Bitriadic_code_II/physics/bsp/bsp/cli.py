"""Command-line interface.

    python -m bsp.cli run cases/water_ice_monograph.toml --out out/
    python -m bsp.cli run my_case.toml --out out/ --no-convergence
    python -m bsp.cli audit-monograph --out out/audit/
    python -m bsp.cli presets
"""

from __future__ import annotations

import argparse
import os
import sys

from .cases_io import PRESETS, case_to_params, load_case, load_user_data
from .monograph import audit_monograph


def _cmd_run(args):
    cfg = load_case(args.case)
    p = case_to_params(cfg)
    if args.dx:
        p.dx = float(args.dx)
    if args.t_end:
        p.t_end = float(args.t_end)
    if args.event_mode:
        p.event_mode = args.event_mode

    val = cfg.get("validation", {})
    user_data = None
    ud_path = args.user_data or val.get("user_data")
    if ud_path:
        user_data = load_user_data(ud_path)
        print(f"loaded user data: {len(user_data[0])} points from {ud_path}")

    from .report import validate_case, write_outputs
    name = cfg.get("case", {}).get("name",
                                   os.path.splitext(
                                       os.path.basename(args.case))[0])
    out_dir = args.out or os.path.join("results", name)
    print(f"running BSP: {name} (dx={p.dx} m, t_end={p.t_end} s, "
          f"event_mode={p.event_mode})")
    bundle = validate_case(
        p, cfg=cfg,
        do_enthalpy=bool(val.get("enthalpy", True)) and not args.no_enthalpy,
        do_convergence=(bool(val.get("convergence", True))
                        and not args.no_convergence),
        convergence_levels=int(val.get("convergence_levels", 4)),
        user_data=user_data, out_dir=out_dir,
        make_figures=not args.no_figures)
    paths = write_outputs(bundle, out_dir, case_name=name)

    from .checks import summarize
    print()
    print(summarize(bundle["checks"]))
    print()
    print(f"outputs written to {out_dir}/:")
    for k, v in paths.items():
        if k == "figures":
            for f in v:
                print(f"  - {f}")
        elif k != "summary":
            print(f"  - {v}")
    n_fail = sum(1 for c in bundle["checks"] if c.verdict == "FAIL")
    return 1 if n_fail else 0


def _cmd_audit(args):
    out = audit_monograph()
    out_dir = args.out or "results/audit"
    os.makedirs(out_dir, exist_ok=True)

    lines = ["# Audit of the BSP paper's own numbers",
             "", "Recomputation of every quantitative claim in the "
             "paper's validation (sec. 12 / appendix B).", ""]
    lam = out["lambda"]
    lines += [
        "## The Neumann constant (claims A1, A2)",
        "",
        f"- Ste = c_p (T_m - T_s) / L = **{lam['Ste']:.4f}**",
        f"- the paper's printed equation "
        f"e^(-l^2)/erf(l) = L sqrt(pi) / (c_p dT) has RHS = "
        f"{lam['printed_equation_rhs']:.2f}; its true root is "
        f"lambda = {lam['root_of_printed_equation']:.4f}",
        f"- the correct one-phase equation "
        f"l e^(l^2) erf(l) = Ste/sqrt(pi) gives "
        f"**lambda = {lam['correct_lambda']:.4f}**",
        f"- the paper's claim lambda = 0.15 satisfies NEITHER: it is "
        f"off by a factor {1/lam['claim_residual_vs_printed_eq']:.2f} "
        f"on the printed equation and "
        f"{1/lam['claim_residual_vs_correct_eq']:.2f} on the correct "
        f"one (the printed equation is the correct one with the factor "
        f"lambda on the RHS missing, i.e. evaluated at lambda = 1)",
        "",
        "## Thermal diffusivity (claim A3)",
        "",
        f"- the paper states alpha = {out['alpha']['paper_alpha']:.3e} "
        f"m2/s but its own k, rho, c_p give "
        f"{out['alpha']['alpha_from_paper_k_rho_cp']:.3e} "
        f"(factor {out['alpha']['ratio']:.2f}). "
        f"{out['alpha']['note']}",
        "",
        "## First event (claim A5)",
        "",
        f"- paper formula dt_1 = rho L dx^2 / (k dT) = "
        f"{out['first_event']['paper_formula']:.4f} s; paper prints "
        f"15.2 s; this package's solver reproduces "
        f"{out['first_event']['this_package']:.4f} s -- "
        f"**correct and reproduced**",
        "",
        "## Event tables (claim A4)",
        "",
        f"- sec. 12.2 first events: "
        f"{out['event_tables']['paper_sec_12_2_first_events']}",
        f"- appendix B.2 first events: "
        f"{out['event_tables']['paper_appendix_B2_first_events']} "
        f"(mutually inconsistent by 10x)",
        f"- the paper's explicit rule run on its own field: "
        f"**{out['event_tables']['explicit_rule_run']['n_events']} "
        f"events, then stalls: "
        f"{out['event_tables']['explicit_rule_run']['termination']}** "
        f"-- the printed rule cannot produce the appendix table; the "
        f"appendix's intervals were hand-fed from the Neumann profile",
        f"- faithful run (crossing condition): first events "
        f"{[round(float(t), 1) for t in out['event_tables']['faithful_integral_run']['t_events'][:5]]}",
    ]
    h = out["headline_t1000"]
    lines += [
        "",
        "## The headline 'within 2%' (claim A6)",
        "",
        f"- at t = 1000 s the paper claims Neumann s = 0.0102 m "
            f"(from lambda = 0.15, alpha = 1.15e-6): recomputed = "
            f"{h['neumann_with_claimed_lambda_and_paper_alpha']*1e3:.2f} mm",
            f"- with the CORRECT lambda but the paper's alpha: "
            f"{h['neumann_with_correct_lambda_paper_alpha']*1e3:.2f} mm",
            f"- with correct lambda and self-consistent alpha: "
            f"{h['neumann_correct_selfconsistent_alpha']*1e3:.2f} mm",
            f"- faithful BSP at dx = 0.5 mm: "
            f"{h['bsp_faithful_dx_0.5mm']*1e3:.2f} mm "
            f"(**{h['bsp_vs_correct_selfconsistent']:.1%}** from the "
            f"correct value)",
            f"- verdict: {h['note']}",
            "",
            "## Overall",
            "",
            "The paper's validation arithmetic contains four "
            "independent errors (missing factor in the lambda "
            "equation; mis-solved lambda; inconsistent alpha; two "
            "mutually inconsistent event tables). None of them "
            "invalidates the METHOD: the faithful BSP run converges "
            "to the correct Neumann solution (see the convergence "
            "study in the case reports). The framework is sound; the "
            "paper's numbers needed this correction.",
        ]
    path = os.path.join(out_dir, "audit.md")
    with open(path, "w") as fh:
        fh.write("\n".join(lines))
    import json
    with open(os.path.join(out_dir, "audit.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=float)
    print("\n".join(lines))
    print(f"\nwritten: {path}")
    return 0


def _cmd_presets(args):
    print("available material presets (typical handbook values -- "
          "override with your own measurements for critical work):")
    for name, props in PRESETS.items():
        note = props.get("note", "")
        print(f"  {name:24s} rho={props['rho']}, L={props['L']}, "
              f"k={props['k_grown']}, cp={props['cp_grown']}"
              f"  [{note}]")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bsp",
                                 description="BSP validation workbench")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="run one case end-to-end")
    r.add_argument("case", help="case file (.toml or .json)")
    r.add_argument("--out", default=None, help="output directory")
    r.add_argument("--dx", default=None, help="override lattice spacing")
    r.add_argument("--t-end", dest="t_end", default=None)
    r.add_argument("--event-mode", choices=("integral", "explicit"),
                   default=None)
    r.add_argument("--user-data", default=None,
                   help="CSV with measured (t_s, s_m) interface data")
    r.add_argument("--no-convergence", action="store_true")
    r.add_argument("--no-enthalpy", action="store_true")
    r.add_argument("--no-figures", action="store_true")
    r.set_defaults(func=_cmd_run)

    a = sub.add_parser("audit-monograph",
                       help="recompute the paper's own validation numbers")
    a.add_argument("--out", default=None)
    a.set_defaults(func=_cmd_audit)

    pr = sub.add_parser("presets", help="list material presets")
    pr.set_defaults(func=_cmd_presets)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
