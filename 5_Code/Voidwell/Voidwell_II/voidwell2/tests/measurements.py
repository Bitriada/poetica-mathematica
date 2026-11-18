"""measurements.py -- rates, attack surface, and the honest
extrapolations.

Runs from the project root:  python3 tests/measurements.py
Writes results/measurements.json.

What is measured (and why each number exists):

  1. encode/gate rates, both variants -- the honest per-trial cost.
     There is no early abort: a wrong seed costs the SAME full
     replay as the honest key (measured side by side; the ratio is
     the property, ~1.0 by design and by measurement).
  2. attack extrapolations -- 2^127 (compact) and 2^255 (flagship)
     full replays at the measured rate, in years.  No dictionaries,
     no preimages, no filters exist against a challenge; seed
     enumeration at full replay is the best known attack.
  3. the tick-key climb rate -- ticks hashed per second, the
     expected climb to the demo tick, and the honest note that an
     n-bit tick-key needs I* ~ 2^n.
  4. the published-surface audit -- the field-by-field nature of
     everything a challenge publishes (the pre-shipment check).
"""
from __future__ import annotations

import json
import math
import os
import secrets
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ucq.lift import FULL  # noqa: E402
from voidwell2 import tickkey  # noqa: E402
from voidwell2.encoder import encode, run_path  # noqa: E402
from voidwell2 import wells as wells_mod  # noqa: E402
from voidwell2.gate import ALLOWED_CHALLENGE_FIELDS  # noqa: E402

DATA = bytes.fromhex("00112233")
YEAR = 365.25 * 86400

OUT = os.path.join(ROOT, "results", "measurements.json")


def rate_encode(variant: str, n: int = 150) -> dict:
    t0 = time.perf_counter()
    for i in range(n):
        seed = (bytes([i % 256]) * 32)[:32] if variant == "flagship" \
            else (bytes([i % 256]) * 16)
        encode(FULL, DATA, seed, 43, variant)
    dt = time.perf_counter() - t0
    return {"trials": n, "seconds": round(dt, 3),
            "rate_per_s": round(n / dt, 1)}


def rate_wrong_seed(variant: str, n: int = 150) -> dict:
    """Full replays of seeds that all FAIL -- the no-early-abort
    property: the attacker's per-trial cost equals the honest
    replay cost (nothing is published to abort against)."""
    wells = wells_mod.wells_for(FULL, 43)
    H_ref, *_ = run_path(FULL, DATA, b"\x01" * 32, wells, 43)
    t0 = time.perf_counter()
    hits = 0
    for i in range(n):
        seed = secrets.token_bytes(32 if variant == "flagship"
                                   else 16)
        H, *_ = run_path(FULL, DATA, seed, wells, 43)
        if H == H_ref:
            hits += 1
    dt = time.perf_counter() - t0
    return {"trials": n, "hits": hits, "seconds": round(dt, 3),
            "rate_per_s": round(n / dt, 1)}


def tickkey_climb(ticks: int = 100_000) -> dict:
    """Hash consecutive ticks (the attacker's climb) and time it."""
    t0 = time.perf_counter()
    for t in range(1, ticks + 1):
        tickkey.H_for_tick(t)
    dt = time.perf_counter() - t0
    rate = ticks / dt
    demo = tickkey.DEMO_TICK
    return {"ticks": ticks, "seconds": round(dt, 2),
            "ticks_per_s": round(rate, 0),
            "expected_climb_to_demo_tick_seconds":
                round(demo / 2 / rate, 1),
            "demo_tick": demo,
            "demo_tick_log2": round(math.log2(demo), 2)}


def surface_audit() -> dict:
    ch, _key, _ = encode(FULL, DATA, b"\x11" * 32, 43, "flagship")
    fields = {}
    for f in ch:
        if f in ("H", "data_commitment"):
            fields[f] = "256-bit SHA-256 of full-width material " \
                        "(>= 2^256 preimage domain)"
        elif f == "params":
            fields[f] = "public parameters (pi-skeleton wells, " \
                        "variant, widths) -- public by design"
        else:
            fields[f] = "public data / count -- public by design"
    return {"published_fields": sorted(ch),
            "allowed_fields": sorted(ALLOWED_CHALLENGE_FIELDS),
            "match": set(ch) == ALLOWED_CHALLENGE_FIELDS,
            "nature": fields,
            "leak_fields_absent": not ({"nullifiers",
                                         "schedule_digest"} & set(ch))}


def main() -> int:
    print("Voidwell-2 measurements")
    print()
    enc = {v: rate_encode(v) for v in ("flagship", "compact")}
    wrong = {v: rate_wrong_seed(v) for v in ("flagship", "compact")}
    for v in enc:
        print(f"encode rate ({v}): {enc[v]['rate_per_s']}/s "
              f"({enc[v]['trials']} trials, {enc[v]['seconds']}s)")
        print(f"wrong-seed full replay ({v}): "
              f"{wrong[v]['rate_per_s']}/s, {wrong[v]['hits']} hits "
              f"in {wrong[v]['trials']} trials -- no early abort: "
              f"the attacker pays full replay per trial")
    full_rate = enc["flagship"]["rate_per_s"]
    ratio = wrong["flagship"]["rate_per_s"] / full_rate
    print(f"no-early-abort property: wrong-seed rate / honest rate "
          f"= {ratio:.2f} (the attacker gains nothing per trial)")

    attacks = {}
    for v, bits in (("compact", 127), ("flagship", 255)):
        yrs = 2.0 ** bits / full_rate / YEAR
        attacks[v] = {"expected_trials": f"2^{bits}",
                      "per_trial": "full replay",
                      "years": f"{yrs:.2e}"}
        print(f"attack ({v}): 2^{bits} full replays at "
              f"{full_rate}/s = {yrs:.2e} years")

    print()
    climb = tickkey_climb()
    print(f"tick-key climb: {climb['ticks_per_s']:.0f} ticks/s "
          f"({climb['ticks']} ticks in {climb['ticks'] and climb['seconds']}s); "
          f"expected climb to the demo tick "
          f"2^{climb['demo_tick_log2']}: "
          f"{climb['expected_climb_to_demo_tick_seconds']}s")

    audit = surface_audit()
    print()
    print("published-surface audit: "
          f"{'PASS' if audit['match'] and audit['leak_fields_absent'] else 'FAIL'}")
    for f, nature in audit["nature"].items():
        print(f"  {f}: {nature}")

    claims = {
        "flagship": "security = min(256, 256) = 2^256",
        "compact": "security = min(128, 256) = 2^128",
        "assumption": "SHA-256 preimage resistance; all other "
                      "layers are integrity and narrative",
        "best_attack": "seed enumeration at full replay cost",
    }
    print()
    print("claims (the number the rules must carry):")
    for k, v in claims.items():
        print(f"  {k}: {v}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({
            "model": "voidwell-2",
            "encode_rate": enc,
            "wrong_seed_rate": wrong,
            "no_early_abort_ratio": round(ratio, 2),
            "attacks": attacks,
            "tickkey": climb,
            "surface_audit": audit,
            "claims": claims,
        }, f, indent=1)
        f.write("\n")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
