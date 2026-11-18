"""harness.py -- the 9-bit small model, exhaustively enumerated.

PARAMETERS: F_7, 2x2 matrices, 3-bit digivector (3 one-bit
digits), L = 8, seed space 2^8 (seeds 0x00..0xff), k = 0..3.  The
same run_path code path as the full model -- only the Profile
differs, which is the demonstration's central claim.

The wells are public constants (as in the full model), so the key
space IS the seed space (2^8) and the only attack surface is H.
Three things are measured:

  1. exhaustive enumeration -- all 256 seeds, their H values, and
     the density quotient |seeds| / |seeds hitting the reference H|.
     At k = 0 the quotient is 2^3 (the checkpoint-less collapse: H
     commits only D_0 and its public path -- the wells are what
     bind the checkpoints).  At k >= 1 the full-width nullifiers
     bind ~2^22 >> 2^8 and the quotient saturates at 256 -- for
     the RIGHT reason: the quotient equals the seed space because
     the key space IS the seed space.  (A quotient equal to the
     key space is NOT by itself evidence of security; what matters
     is that every trial is a full replay -- see the note below.)

  2. seed enumeration (the honest baseline) -- replay seeds until
     the reference H appears: worst case 256 FULL replays, and
     with the minimal surface there is nothing to abort against.
     At k >= 1 attack work = key space exactly: enumeration, no
     shortcuts, no sum-vs-product story.

  3. the toy dictionary -- what a wider surface (published
     nullifiers) would give the attacker HERE: the full-width
     nullifier domain is 8 states x 7^4 matrices = 19,208 =
     2^14.2, an afternoon of hashing.  Demonstrated, then the
     honest split is printed: the toy cannot exhibit 256-bit
     preimage hardness; the full model's 2^4123 domain can.  The
     security claim of the full model rests on SHA-256, stated --
     never on the toy.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

from ucq.lift import SMALL
from voidwell2.encoder import run_path, ser_state, sha
from voidwell2 import wells as wells_mod

DATA = bytes.fromhex("00112233")
L = 8
SEEDS = [bytes([s]) for s in range(256)]
OUT = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))),
    "results", "small_model.json")


def wells_k(k: int) -> list[tuple[int, int]]:
    return wells_mod.wells_for(SMALL, L, k)


def enumerate_k(k: int):
    """All 256 seeds -> H; returns (H_counts, ref_H, hits).  The
    reference seed is 0x5a (mid-space) so the enumeration demo
    below pays a representative number of trials."""
    wells = wells_k(k)
    ref_seed = SEEDS[0x5a]
    ref_H = None
    counts = {}
    for s in SEEDS:
        H, _h, _n, _D = run_path(SMALL, DATA, s, wells, L)
        counts[H] = counts.get(H, 0) + 1
        if s == ref_seed:
            ref_H = H
    return counts, ref_H, counts[ref_H]


def seed_enumeration(k: int, ref_H: str) -> tuple[int, float]:
    """The honest baseline: replay seeds until the reference H
    appears (worst case); returns (trials_to_first, seconds)."""
    wells = wells_k(k)
    t0 = time.perf_counter()
    trials = 0
    for s in SEEDS:
        trials += 1
        H, _h, _n, _D = run_path(SMALL, DATA, s, wells, L)
        if H == ref_H:
            break
    return trials, time.perf_counter() - t0


def toy_dictionary(k: int = 3):
    """A wider surface, demonstrated: publish the k nullifiers
    of a small-model challenge and dictionary-attack them.

    The domain: every (state, matrix) pair the nullifier could hash
    -- 8 states x 7^4 = 19,208 entries for the 2x2/F_7 model
    (2^14.2).  In the FULL model the same domain is 2^27 x p^16 =
    2^4123: the demonstration is feasible HERE and only here.
    """
    from ucq.matrix import FpMatrix
    wells = wells_k(k)
    seed = SEEDS[0x5a]
    H, _h, nulls, _D = run_path(SMALL, DATA, seed, wells, L)

    t0 = time.perf_counter()
    table = {}
    for state in range(1 << SMALL.n_bits):
        for a in range(SMALL.p):
            for b in range(SMALL.p):
                for c in range(SMALL.p):
                    for d in range(SMALL.p):
                        Q = FpMatrix([[a, b], [c, d]], SMALL.p)
                        table[sha(ser_state(state)
                                  + Q.serialize())] = (state, Q)
    build_s = time.perf_counter() - t0

    recovered = []
    for n in nulls:
        recovered.append(table.get(n))
    return {
        "domain": len(table),
        "domain_log2": round(math.log2(len(table)), 1),
        "build_seconds": round(build_s, 1),
        "recovered": sum(1 for r in recovered if r is not None),
        "published": len(nulls),
        "full_model_domain_log2": 4123,
    }


def main() -> int:
    print("Voidwell-2 small model: F_7, 2x2, 3-bit state, "
          "L = 8, seeds 0x00..0xff, wells PUBLIC")
    print()
    rows = []
    for k in range(0, 4):
        counts, ref_H, hits = enumerate_k(k)
        quotient = len(SEEDS) / hits
        trials, secs = seed_enumeration(k, ref_H)
        rows.append({
            "k": k,
            "key_space": len(SEEDS),
            "seeds_hitting_ref_H": hits,
            "density_quotient": quotient,
            "density_quotient_is_artifact":
                "at k=0 it undercounts the collapse; at k>=1 it "
                "equals the seed space for the right reason (the "
                "key space IS the seed space)",
            "seed_enumeration_trials_to_ref_seed": trials,
            "seed_enumeration_expected": 128.5,
            "seed_enumeration_worst": 256,
            "seed_enumeration_seconds": round(secs, 3),
            "distinct_H": len(counts),
        })
        print(f"k={k}: key space {len(SEEDS)}, distinct H "
              f"{len(counts)}, seeds hitting ref H {hits} "
              f"(quotient {quotient:.1f}), seed enumeration found "
              f"the key after {trials} full replays in {secs:.3f}s "
              f"(expected 128.5, worst 256)")

    print()
    print("the toy dictionary (what a wider surface would give "
          "the attacker HERE):")
    toy = toy_dictionary()
    print(f"  full-width nullifier domain: {toy['domain']} = "
          f"2^{toy['domain_log2']}")
    print(f"  dictionary build: {toy['build_seconds']} s; "
          f"recovered {toy['recovered']}/{toy['published']} "
          f"published nullifiers")
    print(f"  the same domain in the FULL model: "
          f"2^{toy['full_model_domain_log2']} -- the toy cannot "
          f"exhibit 256-bit preimage hardness;")
    print("  the full model's claim rests on SHA-256, stated.")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"revision": 3, "model": "2x2/F_7, 3-bit, L=8",
                   "wells_public": True,
                   "rows": rows, "toy_dictionary": toy}, f, indent=1)
        f.write("\n")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
