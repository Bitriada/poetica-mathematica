"""seed_search.py -- the attacker's best weapon, shipped by the
designer: seed enumeration at full replay cost.

Against a Voidwell-2 challenge there is nothing else to attack:

  * no schedule digest is published -- there is nothing to
    preimage (the wells are public constants);
  * no nullifiers are published -- no dictionary has anything to
    match (and the nullifiers' preimage domain is 2^4123, so the
    dictionary could not be built either);
  * no early abort exists -- the only check is the final H
    comparison, so every seed trial costs one FULL replay.

This tool runs exactly that attack and prices it honestly:

    python3 attacker/seed_search.py --challenge contests/flagship/challenge.json \
        --budget 4096

It draws random seeds of the challenge's variant width, replays each
in full, and reports the rate and the extrapolation to the expected
work (2^127 trials for compact, 2^255 for flagship).  Run it against
your own challenges; the numbers it prints are the numbers the spec
claims.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ucq.lift import FULL  # noqa: E402
from voidwell2.encoder import run_path  # noqa: E402
from voidwell2 import wells as wells_mod  # noqa: E402

YEAR = 365.25 * 86400


def main() -> int:
    ap = argparse.ArgumentParser(
        description="seed enumeration against a Voidwell-2 challenge")
    ap.add_argument("--challenge", required=True)
    ap.add_argument("--budget", type=int, default=4096,
                    help="number of full-replay trials (default 4096)")
    args = ap.parse_args()

    with open(args.challenge) as f:
        ch = json.load(f)
    variant = ch["params"]["variant"]
    seed_bits = ch["params"]["seed_bits"]
    seed_bytes = 32 if variant == "flagship" else 16
    data = bytes.fromhex(ch["data"])
    L = ch["params"]["L"]
    wells = wells_mod.parse(ch["params"]["wells"])
    H_target = ch["H"]

    print(f"challenge: {args.challenge}")
    print(f"variant {variant} ({seed_bits}-bit seed), L={L}, "
          f"wells {wells} (public), H={H_target[:16]}...")
    print(f"attack: seed enumeration, FULL replay per trial "
          f"(no preimage, no dictionary, no early abort exists)")
    print()

    t0 = time.perf_counter()
    hits = 0
    for i in range(args.budget):
        seed = secrets.token_bytes(seed_bytes)
        H, *_ = run_path(FULL, data, seed, wells, L)
        if H == H_target:
            hits += 1
            print(f"  HIT at trial {i + 1}: seed {seed.hex()}")
    dt = time.perf_counter() - t0
    rate = args.budget / dt

    exp_bits = seed_bits - 1          # expected trials = 2^(n-1)
    yrs = 2.0 ** exp_bits / rate / YEAR
    print(f"trials: {args.budget} in {dt:.2f}s "
          f"({rate:.1f} full replays/s), hits: {hits}")
    print(f"expected work: 2^{exp_bits} full replays "
          f"= {2.0 ** exp_bits:.2e} trials")
    print(f"at the measured rate: {yrs:.2e} years")
    print()
    print("the honest summary: this is the best known attack; the "
          "claim is min(seed bits, 256) and the assumption is "
          "SHA-256 preimage resistance")
    return 0


if __name__ == "__main__":
    sys.exit(main())
