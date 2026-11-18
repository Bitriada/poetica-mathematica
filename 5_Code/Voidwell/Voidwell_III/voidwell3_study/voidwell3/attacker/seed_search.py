"""seed_search.py -- the honest enumeration against a published
challenge.

Two modes:

  random (default): replay N random seeds at FULL path cost against
    the published H and report the rate, the coverage fraction, and
    the expected work -- the same accounting the README states.
    There is no early abort: with nothing per-well published, every
    wrong seed costs a complete replay (the surface audit and the
    gate enforce that this stays true).

  --exhaustive: walk the ENTIRE seed space in order (refused above
    2^20 seeds).  For the study-toy variant (2^16) this converges in
    about a minute -- that is the lesson of the study case: the key
    space IS the seed space, and when the seed space is small, the
    construction concedes it honestly, at full replay cost per
    candidate, with no shortcut anywhere.

The profile (toy vs full model) is read from the challenge's own
public parameters.
"""
from __future__ import annotations

import json
import secrets
import sys
import time

from ucq.lift import FULL, TOY
from voidwell3 import wells as wells_mod
from voidwell3.encoder import run_path

TRIALS = 2048
EXHAUSTIVE_LIMIT_BITS = 20


def _profile_for(params: dict):
    if (params.get("digits") == TOY.n_digits
            and params.get("bits_per_digit") == TOY.bits_per_digit):
        return TOY
    return FULL


def _report(seed_bits: int, trials: int, hits: int, rate: float,
            exhaustive: bool) -> None:
    print(f"  trials: {trials:,}, hits: {hits}")
    if not exhaustive:
        cov_bits = trials.bit_length() - 1 if trials else 0
        print(f"  coverage: 2^{cov_bits} of 2^{seed_bits} "
              f"(a 2^-{seed_bits - cov_bits} fraction)")
    print(f"  rate: {rate:.1f} full replays/s")
    expected = 2 ** (seed_bits - 1)
    years = expected / rate / (365.25 * 86400)
    print(f"  expected work: 2^{seed_bits - 1} replays = "
          f"{years:.2e} years at this rate")
    if seed_bits <= 24:
        print(f"  (the claim is min({seed_bits}, 256): the key "
              "space is small enough to exhaust -- the study "
              "case's lesson)")
    else:
        print(f"  (the claim is min({seed_bits}, 256); the search "
              "does not warm up)")


def main(challenge_path: str, trials: int | None = None,
         exhaustive: bool = False) -> int:
    with open(challenge_path) as f:
        ch = json.load(f)
    params = ch["params"]
    seed_bits = params["seed_bits"]
    seed_bytes = seed_bits // 8
    H = ch["H"]
    data = bytes.fromhex(ch["data"])
    L = params["L"]
    e = params["e"]
    wells = wells_mod.parse(params["wells"])
    pro = _profile_for(params)
    model = "toy (F_257)" if pro is TOY else "full (256-bit F_p)"
    print(f"seed search against {challenge_path}")
    print(f"  model: {model}; target H: {H[:16]}...")

    t0 = time.perf_counter()
    hits = 0
    done = 0
    if exhaustive:
        if seed_bits > EXHAUSTIVE_LIMIT_BITS:
            print(f"  refused: --exhaustive is capped at "
                  f"2^{EXHAUSTIVE_LIMIT_BITS} seeds "
                  f"(this challenge is 2^{seed_bits})")
            return 1
        space = 1 << seed_bits
        print(f"  exhaustive: all {space:,} seeds in order "
              f"({seed_bytes}-byte)")
        found = None
        for i in range(space):
            r = run_path(pro, data, i.to_bytes(seed_bytes, "big"),
                         wells, L, e)
            if r.H == H:
                hits += 1
                found = i.to_bytes(seed_bytes, "big")
                print(f"  HIT after {i + 1:,} replays: "
                      f"seed = {found.hex()}")
                done = i + 1
                break
            if (i + 1) % 8192 == 0:
                dt = time.perf_counter() - t0
                print(f"    ... {i + 1:,} replays "
                      f"({(i + 1) / dt:.0f}/s)")
        if found is None:
            done = space
            print("  no hit: the seed is not in the space "
                  "(challenge malformed?)")
        dt = time.perf_counter() - t0
        _report(seed_bits, done, hits, done / dt, True)
        if hits:
            print("  the gate will now PASS this seed -- write it "
                  "to a key file and try it")
        return 0 if hits else 1

    n = trials if trials is not None else TRIALS
    print(f"  random: {n:,} seeds against the published H")
    for _ in range(n):
        seed = secrets.token_bytes(seed_bytes)
        r = run_path(pro, data, seed, wells, L, e)
        if r.H == H:
            hits += 1
            print("  HIT:", seed.hex())
    dt = time.perf_counter() - t0
    _report(seed_bits, n, hits, n / dt, False)
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opts = [a for a in sys.argv[1:] if a.startswith("--")]
    trials = None
    for o in opts:
        if o.startswith("--trials="):
            trials = int(o.split("=", 1)[1])
    raise SystemExit(main(args[0] if args else None,
                          trials=trials,
                          exhaustive="--exhaustive" in opts))
