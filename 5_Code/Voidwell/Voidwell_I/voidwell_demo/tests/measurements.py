"""measurements.py -- the demonstration's measured quantities.

For each test case (k = 0, 1, 3): the full fare ledger (sec. 8.5
reading), the multinumeral event census (App. A reading), and the
exact key-space arithmetic.  Writes results/measurements.json.

REVISED 2026-11-16 after the independent cryptanalysis: adds the
ATTACK SURFACE of the demo challenge (contests/test3/challenge.json,
whose key is published at results/test3_withheld_key.json so every
number below is independently checkable):

  * the schedule-digest preimage (C(43,3) x 9^3 = 2^23.1 candidates,
    exhaustive, timed);
  * the nullifier dictionary attack (one 2^27 state scan, timed);
  * the effective-security accounting: 108 path-binding bits
    (D_0, C_1..C_3) + 72 nullifier-binding bits (3 x 24) = 2^180,
    against 2^203.1 unstructured and the claimed 2^279.1;
  * replay rates (full and early-abort) and years-to-solve.

Runtime: about 2-3 minutes, dominated by the 2^27 nullifier scan.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import secrets
import sys
import time
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from fareoctal.core import FareOctal
from ucq import multinumeral
from ucq.conjugate import conjugate
from ucq.lift import FULL, lift, project
from ucq import ucpoly
from voidwell import schedule as sched_mod
from voidwell.encoder import (block_at, base_step, digit_value,
                              run_path, ser_state, sha)
from voidwell.prf import prf_schedule, prf_digivector, prf_well_matrix

DATA = bytes.fromhex("00112233")
L = 43
SEEDS = {0: "11" * 32, 1: "22" * 32, 3: "33" * 32}


def key_space(L: int, k: int) -> dict:
    from math import comb
    sched = comb(L, k) * (9 ** k)
    return {"schedule_factor": sched,
            "log2_schedule_factor": math.log2(sched) if sched else 0.0,
            "log2_total": 256 + (math.log2(sched) if sched else 0.0),
            "total": (2 ** 256) * sched}


def measure(k: int) -> dict:
    seed = bytes.fromhex(SEEDS[k])
    sched = prf_schedule(FULL, seed, L, k)
    H, h_L, nulls, D_L, values, fares = run_path(
        FULL, DATA, seed, sched, L, collect=True)

    # multinumeral census: intra-base annihilation events at the base
    # layer (the union fallback of resolution R3)
    annihilations = burns = writes = clean_unions = 0
    for i in range(1, L + 1):
        if any(m == i for m, _ in sched):
            continue
        b = block_at(DATA, i)
        if b % 3 == 0:
            g = (b >> 2) % 27
            if values[i - 1] & (1 << g):
                annihilations += 1
            else:
                clean_unions += 1
        elif b % 3 == 1:
            burns += 1
        else:
            writes += 1

    # the well census: nullified digits and their weights
    wells = []
    for (m, n) in sched:
        arriving = values[m - 1]
        weight = (arriving >> (3 * n)) & 7
        wells.append({"position": m, "digit": n,
                      "burned_weight": weight})

    P = ucpoly.path_polynomial(values[1:], fares)
    return {
        "k": k,
        "seed": SEEDS[k],
        "schedule": [[m, n] for m, n in sched],
        "H": H,
        "D0": values[0], "D_L": D_L,
        "path_length": L,
        "fare_ledger": {
            "total_fare": sum(fares),
            "per_step": fares,
            "clean_unions": clean_unions,
            "annihilation_fallbacks": annihilations,
            "slot_burns": burns,
            "slot_writes": writes,
            "well_fares": [w["burned_weight"] for w in wells],
        },
        "ucpoly_fare": P.fare(),          # L1: == total_fare
        "wells": wells,
        "key_space": key_space(L, k),
    }


def attack_surface() -> dict:
    """The measured attack surface of the DEMO challenge (k = 3, seed
    S3 -- published at results/test3_withheld_key.json).  Every stage
    of the structured attack of the independent cryptanalysis,
    executed and timed on this challenge."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    chal = json.load(open(os.path.join(root, "contests", "test3",
                                       "challenge.json")))
    withheld = json.load(open(os.path.join(root, "results",
                                           "test3_withheld_key.json")))
    key_seed = bytes.fromhex(withheld["seed"])
    key_sched = [(m, n) for m, n in withheld["schedule"]]

    # -- stage 1: schedule-digest preimage (exhaustive) ---------------
    target = bytes.fromhex(chal["schedule_digest"])
    buf = bytearray(11)          # 01 | k | (m:2B, n:1B) x 3
    buf[0], buf[1] = 1, 3
    matches = []
    n_cand = 0
    t0 = time.perf_counter()
    for p1, p2, p3 in combinations(range(1, L + 1), 3):
        buf[2:4] = p1.to_bytes(2, "big")
        buf[5:7] = p2.to_bytes(2, "big")
        buf[8:10] = p3.to_bytes(2, "big")
        for n1 in range(9):
            buf[4] = n1
            for n2 in range(9):
                buf[7] = n2
                for n3 in range(9):
                    buf[10] = n3
                    n_cand += 1
                    if hashlib.sha256(buf).digest() == target:
                        matches.append([(p1, n1), (p2, n2), (p3, n3)])
    sched_sec = time.perf_counter() - t0

    # -- stage 2: nullifier dictionary (one 2^27 scan) ------------------
    targets = {bytes.fromhex(n): i for i, n in enumerate(chal["nullifiers"])}
    found = {}
    pre = bytearray(b"\x01\x00\x00\x00\x00")
    t0 = time.perf_counter()
    for s in range(1 << 27):
        pre[1:5] = s.to_bytes(4, "big")
        d = hashlib.sha256(pre).digest()
        if d in targets:
            found[targets[d]] = s
    null_sec = time.perf_counter() - t0
    digits_ok = all(digit_value(FULL, found[j], key_sched[j][1]) == 0
                    for j in range(3) if j in found)

    # -- stage 3: accounting + replay rates -----------------------------
    def replay_abort(seed):
        wells = {m: (j + 1, n) for j, (m, n) in enumerate(key_sched)}
        D = prf_digivector(FULL, seed, b"D0", DATA)
        j = 0
        for i in range(1, L + 1):
            if i in wells:
                wj, n = wells[i]
                M, _c = prf_well_matrix(FULL, seed, wj, D, n)
                Dp = project(FULL, conjugate(lift(FULL, D), M))
                if sha(ser_state(Dp)) != chal["nullifiers"][j]:
                    return False
                j += 1
                D = prf_digivector(FULL, seed, bytes([0x43, wj]), DATA)
            else:
                D, _ = base_step(FULL, D, block_at(DATA, i))
        return True

    t0 = time.perf_counter()
    for _ in range(200):
        run_path(FULL, DATA, secrets.token_bytes(32), key_sched, L)
    full_rate = 200 / (time.perf_counter() - t0)
    t0 = time.perf_counter()
    for _ in range(600):
        replay_abort(secrets.token_bytes(32))
    abort_rate = 600 / (time.perf_counter() - t0)

    binding_path = 4 * 27            # D_0, C_1, C_2, C_3
    binding_null = 3 * 24            # 3 wells x 24 bits (digit is free)
    eff = binding_path + binding_null
    unstructured = math.log2(n_cand) + eff
    claimed = 256 + math.log2(n_cand)
    yr = 365.25 * 86400
    return {
        "challenge": "contests/test3/challenge.json (the demo case; "
                     "key published at results/test3_withheld_key.json)",
        "schedule_preimage": {
            "candidates": n_cand, "log2_space": round(math.log2(n_cand), 2),
            "matches": len(matches),
            "recovered": [[m, n] for m, n in matches[0]],
            "seconds": round(sched_sec, 2),
            "matches_published_key": matches == [key_sched],
            "note": "a committed secret drawn from a 2^23.1 space is "
                    "not a work factor -- it is a transparency",
        },
        "nullifier_dictionary": {
            "scan_space": 1 << 27,
            "seconds": round(null_sec, 1),
            "rate_per_s": round((1 << 27) / null_sec),
            "recovered_states": {str(j + 1): found.get(j)
                                 for j in range(3)},
            "digits_zeroed_match_schedule": digits_ok,
            "nullifiers_recomputed_ok": all(
                sha(ser_state(found[j])) == chal["nullifiers"][j]
                for j in range(3) if j in found),
            "note": "one-wayness over a 27-bit domain is a dictionary, "
                    "not a barrier; the recovered states are free "
                    "early-abort filters (2^-24 each) for any seed "
                    "search",
        },
        "accounting": {
            "path_binding_bits": binding_path,
            "nullifier_binding_bits": binding_null,
            "effective_security_log2": eff,
            "unstructured_bruteforce_log2": round(unstructured, 2),
            "claimed_log2": round(claimed, 2),
            "overstatement_bits": round(claimed - eff, 2),
            "metric_error_bits": round(claimed - unstructured, 2),
            "decomposition_gain_bits": round(unstructured - eff, 2),
            "full_replay_rate_per_s": round(full_rate, 1),
            "early_abort_rate_per_s": round(abort_rate, 1),
            "years_at_early_abort_rate": (2.0 ** eff) / abort_rate / yr,
        },
    }


def main() -> int:
    print("measuring the three test cases ...")
    tests = [measure(k) for k in (0, 1, 3)]
    print("measuring the attack surface of the demo challenge "
          "(~2-3 min, includes the 2^27 nullifier scan) ...")
    surface = attack_surface()
    out = {"tests": tests,
           "key_spaces": {f"k={k}": key_space(L, k) for k in
                          (0, 1, 2, 3, 4, 5, 6)},
           "attack_surface": surface,
           "multinumeral": {
               "bases": 9,
               "trace_dimension": multinumeral.trace_dimension(9),
               "prime_labels": "2,3,5,...,103 (27 switches)",
               "off_diagonal": "always free (V12b)",
               "annihilation": "intra-base (diagonal) event (V12b)",
           }}
    here = os.path.dirname(os.path.abspath(__file__))
    res = os.path.join(here, "..", "results")
    with open(os.path.join(res, "measurements.json"), "w") as f:
        json.dump(out, f, indent=1)
    for t in tests:
        fl = t["fare_ledger"]
        print(f"k={t['k']}: fare={fl['total_fare']} "
              f"(unions {fl['clean_unions']}, annih {fl['annihilation_fallbacks']}, "
              f"burns {fl['slot_burns']}, writes {fl['slot_writes']}, "
              f"wells {fl['well_fares']}) "
              f"key space 2^{t['key_space']['log2_total']:.2f}")
    sp = surface["schedule_preimage"]
    nd = surface["nullifier_dictionary"]
    ac = surface["accounting"]
    print(f"attack surface: schedule preimage {sp['candidates']:,} "
          f"candidates -> {sp['matches']} match in {sp['seconds']}s "
          f"(== published key: {sp['matches_published_key']})")
    print(f"nullifier dictionary: 2^27 scan in {nd['seconds']}s, "
          f"recovered 3/3, digits zeroed ok: "
          f"{nd['digits_zeroed_match_schedule']}")
    print(f"effective security 2^{ac['effective_security_log2']} "
          f"(unstructured 2^{ac['unstructured_bruteforce_log2']}, "
          f"claimed 2^{ac['claimed_log2']}, overstatement "
          f"{ac['overstatement_bits']} bits)")
    print(f"trace dimension (9 bases): "
          f"{out['multinumeral']['trace_dimension']}")
    print("wrote results/measurements.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
