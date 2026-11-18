"""harness.py -- the 9-bit small model, exhaustively enumerated (D8),
with the structured attack as the honest baseline (revision 2).

PARAMETERS (spec D8): F_7, 2x2 matrices, 3-bit digivector (3 one-bit
digits), L = 8, seed space 2^8 (seeds 0x00..0xff), k = 0..3.  The
same run_path code path as the full model -- only the Profile differs
(SMALL vs FULL), which is the demonstration's central claim.

REVISION 2 (2026-11-16), after the independent cryptanalysis of the
issued challenge.  The original harness reported "attack cost" as
|K| / |{keys sharing the reference H}|.  That quotient is the INVERSE
DENSITY of keys per hash value, not the work of any adversary: at
k >= 1 the binding constraints (path plus nullifiers) far exceed
log2|K|, so essentially every H is hit by at most one key and the
quotient trivially equals |K|.  The original conclusion ("cost equals
key space at every k >= 1") was an artifact of counting.  This
revision keeps the enumeration for transparency, relabels the
quotient as the density artifact it is, and MEASURES the structured
attack instead:

  1. schedule preimage -- enumerate all C(8,k) x n_digits^k candidate
     schedules and match the published schedule digest;
  2. nullifier preimage -- scan the whole state space (2^3 states)
     and match the published nullifiers;
  3. seed replay -- replay all 256 seeds with the recovered schedule
     (worst case; early abort at the first nullifier mismatch).

Worst-case work counting: |schedules| + |states| + |seeds| -- a SUM,
where the refuted claim multiplied: |schedules| x |seeds|.

  k   key space     density artifact   structured (worst)   speedup
  1   6,144         6,144              288                  21.3x
  2   64,512        64,512             516                  125.0x
  3   387,072       387,072            1,776                217.9x

Slopes (k >= 1): density 2.989 bits/well (the artifact -- identical
to the key-space slope by construction); structured 1.31 bits/well
(the honest scaling of the best known attack).  The gap widens with
k and saturates near the seed-space size, because the attack pays
|schedules| + |seeds| while the claim priced |schedules| x |seeds|.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from itertools import combinations

from ucq.lift import SMALL
from voidwell import schedule as sched_mod
from voidwell.encoder import run_path, ser_state, sha

DATA = bytes.fromhex("00112233")
L = 8
SEEDS = [bytes([s]) for s in range(256)]


def all_schedules(k: int):
    """Every schedule: C(L,k) position sets x n_digits^k digit draws."""
    if k == 0:
        yield []
        return

    def digits_rec(i, cur):
        if i == k:
            yield list(cur)
            return
        for d in range(SMALL.n_digits):
            cur.append(d)
            yield from digits_rec(i + 1, cur)
            cur.pop()

    for positions in combinations(range(1, L + 1), k):
        for digits in digits_rec(0, []):
            yield list(zip(positions, digits))


def enumerate_k(k: int):
    keys = 0
    by_H: dict[str, int] = {}
    ref_H = None
    for seed in SEEDS:
        for sched in all_schedules(k):
            H, _h, _nulls, _D = run_path(SMALL, DATA, seed, sched, L)
            keys += 1
            by_H[H] = by_H.get(H, 0) + 1
            if ref_H is None:
                ref_H = H
    ref_collisions = by_H.get(ref_H, 0)
    return keys, by_H, ref_H, ref_collisions


def structured_attack(k: int, ref_H: str, ref_sched_digest: str,
                      ref_nullifiers: list[str]):
    """The best known attack, executed against the reference challenge
    with worst-case work counting.  Returns (worst, breakdown, found).
    """
    # 1. schedule preimage (worst case: the full enumeration)
    n_sched = 0
    recovered = None
    for s in all_schedules(k):
        n_sched += 1
        if sched_mod.digest(s) == ref_sched_digest:
            recovered = s
    # 2. nullifier preimage: one scan of the state space
    n_states = (1 << SMALL.n_bits) if k else 0
    for s in range(n_states):
        if sha(ser_state(s)) in ref_nullifiers:
            pass                      # recovered; counted, not stored
    # 3. seed replay with the recovered schedule (worst case: all)
    passing = [sd.hex() for sd in SEEDS
               if run_path(SMALL, DATA, sd, recovered, L)[0] == ref_H]
    worst = n_sched + n_states + len(SEEDS)
    return worst, {"schedule_preimage": n_sched,
                   "nullifier_scan": n_states,
                   "seed_replay": len(SEEDS)}, passing


def fit_slope(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = my - slope * mx
    ss_res = sum((y - (slope * x + intercept)) ** 2
                 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    return slope, intercept, r2


def main() -> int:
    rows = []
    print("small model: F_7, 2x2, 3-bit digivector, L=8, "
          "256 seeds, exhaustive (harness rev. 2)")
    print()
    print(f"{'k':>2} {'key space':>10} {'distinct H':>11} "
          f"{'keys/H mean':>12} {'density*':>10} "
          f"{'structured':>11} {'speedup':>8}")
    for k in range(4):
        t0 = time.time()
        keys, by_H, ref_H, coll = enumerate_k(k)
        # the reference challenge, as the gate would publish it
        ref_sched = next(all_schedules(k))
        _H, _h, ref_nulls, _D = run_path(
            SMALL, DATA, SEEDS[0], ref_sched, L)
        assert _H == ref_H
        worst, ops, passing = structured_attack(
            k, ref_H, sched_mod.digest(ref_sched), ref_nulls)
        distinct = len(by_H)
        mean = keys / distinct
        density = keys / coll if coll else float(keys)
        rows.append({
            "k": k, "key_space": keys, "distinct_H": distinct,
            "keys_per_H_mean": mean, "keys_per_H_max": max(by_H.values()),
            "reference_H": ref_H, "reference_collisions": coll,
            "density_artifact": density,
            "log2_density": math.log2(density),
            "log2_space": math.log2(keys),
            "structured_attack_worst_case": worst,
            "structured_attack_ops": ops,
            "log2_structured": math.log2(worst),
            "structured_speedup_vs_key_space": keys / worst,
            "structured_attack_found_passing_key": bool(passing),
            "seconds": round(time.time() - t0, 1),
        })
        r = rows[-1]
        print(f"{k:>2} {keys:>10,} {distinct:>11,} "
              f"{mean:>12.2f} 2^{math.log2(density):>7.2f} "
              f"{worst:>11,} {keys / worst:>7.1f}x"
              f"   [{r['seconds']}s]")

    rows1 = [r for r in rows if r["k"] >= 1]
    slope_d, _i, r2_d = fit_slope([r["k"] for r in rows1],
                                  [r["log2_density"] for r in rows1])
    slope_s, _i, r2_s = fit_slope([r["k"] for r in rows1],
                                  [r["log2_structured"] for r in rows1])
    slope_k, _i, r2_k = fit_slope([r["k"] for r in rows1],
                                  [r["log2_space"] for r in rows1])
    print()
    print(f"slope log2(density artifact) vs k, k>=1 : {slope_d:.3f} "
          f"bits/well (r^2 = {r2_d:.4f})  [== key-space slope "
          f"{slope_k:.3f}: an artifact of counting]")
    print(f"slope log2(structured attack) vs k, k>=1: {slope_s:.3f} "
          f"bits/well (r^2 = {r2_s:.4f})  [the honest baseline]")
    print()
    print("READING (rev. 2): the original harness mistook inverse key")
    print("density for attack cost -- at k >= 1 every reference H is")
    print("hit by exactly one key, so the quotient trivially equals")
    print("|K|.  The structured attack (schedule preimage + nullifier")
    print("dictionary + seed replay) is a SUM, not a product: 288 /")
    print("516 / 1,776 operations at k = 1 / 2 / 3, speedups 21x /")
    print("125x / 218x that grow with k.  The k = 0 baseline stays")
    print("endpoint-decomposable (36 keys share the reference H, cost")
    print("2^2.83 against a space of 2^8).")

    out = {
        "model": "F_7 2x2 3-bit L=8 256-seed exhaustive",
        "revision": 2,
        "note": ("rev. 2 after the independent cryptanalysis: the "
                 "'attack_cost_measured' field of revision 1 was the "
                 "inverse key density (|K| / keys-per-reference-H), "
                 "not the work of any adversary; it is retained as "
                 "density_artifact for transparency, and the "
                 "structured attack is the measured baseline"),
        "rows": rows,
        "slopes": {
            "density_k_ge_1": slope_d, "density_r2": r2_d,
            "key_space_k_ge_1": slope_k, "key_space_r2": r2_k,
            "structured_k_ge_1": slope_s, "structured_r2": r2_s,
        },
    }
    here = os.path.dirname(os.path.abspath(__file__))
    res = os.path.join(here, "..", "..", "results")
    os.makedirs(res, exist_ok=True)
    with open(os.path.join(res, "small_model.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"\nwrote results/small_model.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
