"""The guided tour: the trinumeral, demonstrably.

    trinumeral demo    (or: python demo.py)
"""

from __future__ import annotations

import time
from fractions import Fraction


def main() -> int:
    t0 = time.time()
    from trinumeral import (Regime, SpinTally, SpinorialTally, Trinumeral,
                            canonical)

    line = "=" * 74
    print(line)
    print("The Trinumeral -- one value, three bases, an exact trace")
    print("Poetica Mathematica Ch. VIII sec. 8.4 (Heterobase counting)")
    print(line)

    # -- 1. the monograph's worked example, exactly --------------------------
    print("\n[1] omega/0 applied to v = 1/10 (the sec. 8.4.8 worked "
          "example):")
    T = Trinumeral.omega_0(Fraction(1, 10))
    a, b, g = T.fresh_discrepancies()
    print(T.show())
    print(f"    telescope alpha + beta + gamma = {a + b + g}   "
          f"(the heterobase triangle closes)")
    print(f"    tau-cycle coefficient = {float(T.cycle_coefficient()):.3g}"
          f"   (the monograph: 'on the order of 10^-19')")

    # -- 2. invariant points and the gates ------------------------------------
    print("\n[2] The gates and the invariant points:")
    print(f"    0/a projections of T: bin | int {T.project_0a('int')} | "
          f"float {T.project_0a('float')}  -- the trace and ghost disc "
          f"are lost")
    print(f"    omega/0(5) is traceless (all three bases agree): "
          f"{Trinumeral.omega_0(5).is_traceless()}")
    half = Trinumeral.omega_0(Fraction(3, 2))
    print(f"    omega/0(3/2) is traceless: {half.is_traceless()} -- the "
          f"integer sheet cannot hold one half: "
          f"beta = {half.fresh_discrepancies()[1]}")

    # -- 3. conversions and the 2^53 witness ------------------------------------
    print("\n[3] Conversions record what each base loses:")
    u = Trinumeral.omega_0(2 ** 53 + 1)
    v1 = u.int2float()
    print(f"    int2float on i = 2^53 + 1: f rounds to {v1.f:.0f}; the "
          f"e2 record is exactly -1, the ledger (initial +1) cancels "
          f"to 0, the state stays off by "
          f"{v1.fresh_discrepancies()[1]}")
    fb = T.float2bin()
    print(f"    float2bin on 0.1's double (55-bit expansion, p = 53): "
          f"record -1/2^55, e3 ledger now {fb.tau.coefficient(2)} "
          f"(the LEDGER cancels linearly; the STATE discrepancy is "
          f"recomputable anytime)")

    # -- 4. the annihilation ladder -----------------------------------------------
    print("\n[4] The annihilation ladder (trigger x response), default "
          "Level 1:")
    base = Trinumeral.omega_0(5)          # traceless slate
    base.engine.record(2, Fraction(1, 4))
    base.engine.record(2, Fraction(1, 4))
    print(f"    same conversion twice:  trace e3 = "
          f"{base.tau.coefficient(2)}, ghost = {base.ghost}   "
          f"(pair annihilation: 2|alpha| conserved)")
    print("    (saturation, reset, sign-sensitive, threshold and all "
          "5x6 trigger x response combinations are exercised in the "
          "trials battery, V6)")

    # -- 5. arithmetic species --------------------------------------------------------
    print("\n[5] Arithmetic: the bifurcation point of sec. 8.4.8:")
    S = Trinumeral.omega_0(2) + Trinumeral.omega_0(3)
    print(f"    carry:  2 + 3 = (B, {S.i}, {S.f}) with no trace: "
          f"{S.tau.is_zero()}  (the monograph's example)")
    X = (Trinumeral.omega_0(2, adder="xor")
         + Trinumeral.omega_0(3, adder="xor"))
    print(f"    xor:    2 xor 3 = {canonical(X.B)}, i = {X.i}; the "
          f"discarded carry sits on the trace: tau = {X.tau}")
    I = (Trinumeral.omega_0(Fraction(1, 10), adder="ieee")
         + Trinumeral.omega_0(Fraction(2, 10), adder="ieee"))
    print(f"    ieee:   0.1 + 0.2 = {I.f!r}; the rounding feeds tau "
          f"(traceless: {I.is_traceless()})")

    # -- 6. spin tallies -------------------------------------------------------------------
    print("\n[6] Spin tallies and the angle bridge (sec. 8.4.10):")
    s = SpinTally(0, 300) + SpinTally(0, 100)
    print(f"    (0, 300) + (0, 100) = {s!r}   (component-wise would "
          f"give the invalid (0, 400))")
    print(f"    theta = -1 deg  ->  {SpinTally.from_angle(-1)!r}   "
          f"(the negative-angle remark)")

    # -- 7. the double cover -----------------------------------------------------------------
    print("\n[7] The spinorial double cover (sec. 8.4.12 / 8.4.18):")
    spin = SpinorialTally(SpinTally(0, 0))
    r360 = spin.rotate(360)
    r720 = spin.rotate(360).rotate(360)
    print(f"    360 deg: sigma = {r360.sigma:+d}, crossing trace "
          f"{r360.tau}")
    print(f"    720 deg: sigma = {r720.sigma:+d}, trace {r720.tau}, "
          f"ghost {r720.ghost}   <- the coherent spinor regime: "
          f"pair annihilation, pure state")
    berry = spin.rotate(360).rotate(-360)
    print(f"    +360 then -360: sigma = {berry.sigma:+d} but trace "
          f"{berry.tau} != 0   <- the Berry phase regime: the path is "
          f"remembered")
    print(f"    a single 720 deg jump: sigma = "
          f"{spin.rotate(720).sigma:+d}  (sigma flips per boundary "
          f"crossed)")

    print("\n" + line)
    print(f"demo complete in {time.time() - t0:.1f}s -- run "
          f"'trinumeral trials' for the V1-V10 proof-by-trial dossier")
    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
