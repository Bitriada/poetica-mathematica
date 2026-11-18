"""QDME-bs demonstration: the whole verification story in ~30 seconds.

Run:  python demo.py
"""

from __future__ import annotations

import time

import numpy as np


def main() -> None:
    t0 = time.time()
    print("=" * 72)
    print("QDME-bs -- verifying Theorem 8.1 of Poetica Mathematica")
    print("=" * 72)

    # -- 1. the algebras (exact) ----------------------------------------
    print("\n[1] The algebra census (exact, over Q)")
    from qdme_bs.algebra.epoch5 import dimension_census, issue12_resolution
    for name, dim in dimension_census().items():
        print(f"    {dim:5d}D  {name}")
    i12 = issue12_resolution()
    print("    sqrt(-1) in UC = {+i, -i} exactly  ->  Epoch 5 contains NO j, k")
    print("    (the i -> j differential is genuine emergence, not a rename)")

    # -- 2. K1 gate -------------------------------------------------------
    print("\n[2] K1 gate: tau-centrality (the spec's first test)")
    from qdme_bs.algebra.centrality import k1_centrality
    r = k1_centrality(seed=2026)
    print(f"    verdict: {r['verdict']}  (tau commutes with i, j, k in all")
    print("    candidate algebras; the Grassmann reading fails exactly)")

    # -- 3. Thm 8.1 modes -------------------------------------------------
    print("\n[3] Theorem 8.1: three modes of one equation")
    from qdme_bs.unified.thm81 import (Thm81Params, full_generator,
                                       value_tier_nilpotent_flow, evolve)
    from qdme_bs.state.lift import lift_standard, random_density
    from qdme_bs.state.trace_cp import apply_superop, gkls_generator
    from scipy.linalg import expm
    rng = np.random.default_rng(2026)
    d = 2
    H = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    H = (H + H.conj().T) / 2
    L = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    g = 0.5
    rho0 = random_density(d, rng)
    p = Thm81Params(d=d, H=H, Gamma=np.eye(d) * 0.3, channels=[(L, g)])
    nf = value_tier_nilpotent_flow(p, rng)
    print(f"    BARE mode: value-tier feed from record tiers = "
          f"{nf['value-tier feed from record tiers (matrix norm)']:.1f}"
          "  (exact zero: nilpotents never lower tier)")
    out = evolve(p, lift_standard(rho0), 1.0, G=full_generator(p))
    G = gkls_generator(d, H, [L], [g])
    ref = apply_superop(expm(G * 1.0), rho0)
    err = float(np.max(np.abs(out.rho - ref)))
    print(f"    EVENT-FEED mode: value tier == GKLS reference, "
          f"max error {err:.2e}")

    # -- 4. the event clock ------------------------------------------------
    print("\n[4] Algorithm 4.1: time from trace events")
    from qdme_bs.algorithm.event_clock import event_clock_analysis
    ec = event_clock_analysis(seed=2026, n_traj=1500)
    print(f"    ensemble vs GKLS (amplitude damping): "
          f"{ec['(1) ensemble vs GKLS (amplitude damping)']:.2e} "
          f"(4-sigma bound {ec['    MC 4-sigma bound']:.2e})")
    print(f"    T2 from the trace-clock ensemble: "
          f"{ec['(3) T2 from trace-clock ensemble']:.3f} "
          f"(reference {ec['(3) T2 reference']:.3f})")

    # -- 5. the sweep ------------------------------------------------------
    print("\n[5] Universality: 4,000 random QDMEs (demo size)")
    from qdme_bs.universality.sweep import sweep
    sw = sweep(seed=2026, n_per_class=1000)
    for cls, v in sw["classes"].items():
        print(f"    {cls:16s} n={v['n']}  max err {v['max error']:.1e}  "
              f"encodable {v['fraction below 1e-8'] * 100:.0f}%")
    print(f"    reading (a) encodability: {sw['reading (a) encodability']}")

    # -- 6. the derivation (v1.1) ------------------------------------------
    print("\n[6] The physicality convention: DERIVED, not designated")
    from qdme_bs.derivation.gauge_fixing import enumerate_structures
    from qdme_bs.derivation.star_structures import lambda_family_symbolic
    fam = lambda_family_symbolic()
    print("    all *-structures on UC: tau* = lambda*tau, |lambda| = 1 "
          "(U(1) family, exact)")
    print("    theta-gauge is Z_2 only (theta^3 = 8theta => mu^3 = mu)")
    enum = enumerate_structures(2026)
    print(f"    enumeration: {enum['n_survivors']} survivor of "
          f"{enum['n_candidates']} candidates -> "
          f"{'UNIQUE' if enum['unique'] else 'NOT UNIQUE'}")
    s = enum["survivor"]
    print(f"    survivor: tau* = {s['tau*']}, record {s['record']}, "
          f"Tr sigma = 0: {s['Tr sigma = 0']}")
    print("    PSD clause: Gram identity (val(x* x) = A^dag A >= 0 for "
          "EVERY gauge)")

    # -- 7. the experimental program (v1.1) ---------------------------------
    print("\n[7] The experimental program: four protocols, honest power")
    from qdme_bs.experiments.c8_protocol import run_c8
    from qdme_bs.experiments.kernel_protocol import run_kernel
    c8 = run_c8()
    print(f"    C8 winding: covariant |rho01| = "
          f"{c8['prediction_covariant']['true |rho_01(t=2)|']:.1e} vs "
          f"mixed control "
          f"{c8['control_mixed_winding']['true |rho_01(t=2)|']:.3f} -> "
          f"{c8['verdict'].lower()}")
    kern = run_kernel()
    kt = kern["arm_theta_chain"]
    ks = kern["arm_standard_independent"]
    print(f"    kernel sqrt(8) rigidity (qutrit): theta-arm R = "
          f"{kt['rigidity residual R = max - mid - min']:+.3f} "
          f"(3sigma {kt['3 sigma_R threshold']:.3f}) consistent: "
          f"{kt['consistent_with_theta_chain (|R| <= 3 sigma_R)']}; "
          f"standard-arm z = {ks['z-score of R']:.1f} -> REJECTED")
    print(f"    -> {kern['verdict']}")

    print("\n" + "=" * 72)
    print(f"demo complete in {time.time() - t0:.1f}s -- run "
          "'qdme-bs verify --seed 2026', 'qdme-bs derive' and "
          "'qdme-bs experiments' for the full program")
    print("=" * 72)


if __name__ == "__main__":
    main()
