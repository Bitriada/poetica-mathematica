"""harness.py -- the small model, exhaustively enumerated.

PARAMETERS: F_257, 2x2 matrices, an 8-bit digivector (eight one-bit
digits -- a byte), L = 10, wells at the SAME prime constants as the
flagship (positions/digits 2, 3, 5, 7), seed space 2^16 (two-byte
seeds 0x0000..0xffff), k = 0..4.  The same run_path code path as
the full model -- the demonstration's central claim.

Why F_257 and not Voidwell-2's F_7: the V3 investigation measured
that conjugation orbits in F_7 are tiny (63-119 distinct conjugated
matrices per well), so the V2 toy's effective binding saturated near
2^21 and its final state collapsed to ONE bit.  GL(2, 257) has room
for real orbits, and V3's bijection walk cannot collapse the final
state at all -- the miniature now demonstrates what it claims.

Three measurements (the V2 methodology, kept):

  1. exhaustive enumeration -- all 65,536 seeds, their H values, and
     the density quotient |seeds| / |seeds hitting the reference H|.
     At k = 0 the quotient collapses toward the state space (the
     wells are what bind the checkpoints); at k >= 1 the nullifiers
     bind and the quotient saturates at the seed space -- for the
     RIGHT reason: the key space IS the seed space.
  2. the final-state distribution -- the bijection walk's exact
     uniformity: D_L takes all 256 values (chi-square reported).
  3. the toy dictionary -- what a wider surface would give the
     attacker HERE: a nullifier -> seed table built from all seeds,
     and the time to invert a published nullifier.  In the full
     model the same table would need 2^4123 preimages per well.
"""
from __future__ import annotations

import math
import sys
import time

from ucq.lift import TOY
from voidwell3 import wells as wells_mod
from voidwell3.encoder import run_path

DATA = bytes.fromhex("00112233")
L = wells_mod.L_TOY


def all_seeds():
    for i in range(1 << 16):
        yield i.to_bytes(2, "big")


def chi2_survival(stat: float, df: int) -> float:
    a, x = df / 2, stat / 2
    if x <= 0:
        return 1.0
    # series for the lower incomplete gamma (x < a+1)
    if x < a + 1:
        ap, s, d = a, 1.0 / a, 1.0 / a
        for _ in range(1000):
            ap += 1
            d *= x / ap
            s += d
            if abs(d) < abs(s) * 1e-14:
                break
        p = s * math.exp(-x + a * math.log(x) - math.lgamma(a))
        return 1.0 - p
    # continued fraction for the upper (x >= a+1)
    tiny = 1e-300
    b, c, d, h = x + 1 - a, 1.0 / tiny, 1.0 / (x + 1 - a), \
        1.0 / (x + 1 - a)
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        if abs(c) < tiny:
            c = tiny
        c = b + an / c
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1) < 1e-14:
            break
    return math.exp(-x + a * math.log(x) -
                    math.lgamma(a)) * h


def main(verbose: bool = True) -> int:
    wells4 = wells_mod.wells_for(TOY, L, 4)
    ok = True

    # -- 1. exhaustive enumeration: the collapse-to-saturation scan
    #       (k = 0 collapses toward the state space; k >= 1 the
    #       nullifiers bind and the quotient saturates at the seed
    #       space; the k = 4 pass also collects the D_L histogram
    #       and the toy dictionary, so the whole battery is three
    #       passes over the 2^16 seeds)
    ref_seed = b"\x34\x21"
    ref = run_path(TOY, DATA, ref_seed, wells4, L)
    ref_H = {k: run_path(TOY, DATA, ref_seed,
                         wells_mod.wells_for(TOY, L, k), L).H
             for k in (0, 1, 4)}
    for k in (0, 1, 4):
        wells = wells_mod.wells_for(TOY, L, k)
        t0 = time.perf_counter()
        Hs = {}
        hist = [0] * 256
        table = {}
        for i, seed in enumerate(all_seeds()):
            r = run_path(TOY, DATA, seed, wells, L)
            Hs[r.H] = Hs.get(r.H, 0) + 1
            if k == 4:
                hist[r.D_L] += 1
                for n in r.nullifiers:
                    table[n] = i
        dt = time.perf_counter() - t0
        distinct = len(Hs)
        quotient = (1 << 16) // max(1, Hs.get(ref_H[k], 0))
        if verbose:
            print(f"k={k}: distinct H = {distinct:6d} of 65536; "
                  f"density quotient = {quotient:5d} "
                  f"({dt:5.1f}s)")
        if k == 0 and distinct > (1 << 9):
            ok = False
            print("  UNEXPECTED: k=0 should collapse toward the "
                  "state space (256), got", distinct)
        if k == 1 and distinct < (1 << 15):
            ok = False
            print("  UNEXPECTED: k=1 should bind beyond the state "
                  "space, got", distinct)
        if k == 4 and distinct != (1 << 16):
            ok = False
            print("  UNEXPECTED: k=4 should saturate the seed space "
                  "exactly, got", distinct)

        # -- 2. the final-state distribution (the bijection walk) --
        if k == 4:
            exp = (1 << 16) / 256
            stat = sum((x - exp) ** 2 / exp for x in hist)
            p = chi2_survival(stat, 255)
            seen = sum(1 for x in hist if x)
            if verbose:
                print(f"D_L values: {seen}/256; chi2 = {stat:.1f} "
                      f"(df 255, p = {p:.3f})")
            if seen != 256 or p < 0.001:
                ok = False
                print("  UNEXPECTED: the bijection walk must be "
                      "uniform")

            # -- 3. the toy dictionary ------------------------------
            hits = sum(1 for n in ref.nullifiers if n in table)
            need = len(ref.nullifiers)
            if verbose:
                print(f"dictionary: {len(table)} nullifier entries; "
                      f"inverting the reference's published "
                      f"nullifiers matched {hits}/{need} -- a wider "
                      "surface concedes the seed (hence H-only)")
            if hits != need:
                ok = False

    if verbose:
        print("TOY:", "OK" if ok else "REVIEW")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
