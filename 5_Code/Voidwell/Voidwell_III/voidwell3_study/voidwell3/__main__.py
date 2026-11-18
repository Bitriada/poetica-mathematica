"""__main__.py -- the Voidwell-3 command line.

    python3 -m voidwell3 params              # the public constants
    python3 -m voidwell3 encode <seed.hex>   # one encoding, verbose
    python3 -m voidwell3 seal <dir> [variant]
    python3 -m voidwell3 gate <challenge> <key>
    python3 -m voidwell3 demo                # the guided tour
    python3 -m voidwell3 toy                 # the small model
    python3 -m voidwell3 attack <challenge>  # the shipped attacker
    python3 -m voidwell3 verify              # the W-battery
"""
from __future__ import annotations

import json
import secrets
import sys

from ucq.lift import FULL, TOY
from voidwell3 import gate as gate_mod
from voidwell3 import perspectives as persp
from voidwell3 import wells as wells_mod
from voidwell3.encoder import (VARIANTS, run_path, ser_state, sha)

DATA = bytes.fromhex("00112233")          # the demo data block


def cmd_params() -> None:
    print("Voidwell-3 -- the Perspective Walk")
    print("profiles:")
    for name, pro in (("full", FULL), ("toy", TOY)):
        print(f"  {name}: {pro.n_digits} digits x "
              f"{pro.bits_per_digit} bits = {pro.n_bits} bits, "
              f"{pro.size}x{pro.size} over F_p "
              f"({pro.p.bit_length()}-bit)")
    print("wells (the prime skeleton):",
          wells_mod.WELLS_FULL)
    print("involution exponent e = 1 - 2s (default "
          f"{wells_mod.DEFAULT_E}; e = 0 is the critical s = 1/2)")
    print("perspectives:")
    for line in persp.audit(FULL):
        print("  ", line)
    print("variants:", {v: d["claim"] for v, d in VARIANTS.items()})


def cmd_encode(seed_hex: str) -> None:
    seed = bytes.fromhex(seed_hex)
    wells = wells_mod.wells_for(FULL, wells_mod.L_FULL)
    res = run_path(FULL, DATA, seed, wells, wells_mod.L_FULL)
    print("H          :", res.H)
    print("ghost root :", res.ghost_root)
    print("D_0 / D_L  :", f"{res.D_0:09o} / {res.D_L:09o}")
    for w in res.wells_detail:
        print(f"well {w['j']} (pos {w['position']}, digit "
              f"{w['digit']}): ctr={w['ctr']}  D'="
              f"{w['D_prime']:09o}  N={w['nullifier'][:16]}...")
    print("zeta cells :", len(res.zeta_cells),
          "| disentangled:", len(res.disentangled))
    print("fares      :", sum(res.fares), "over", len(res.fares),
          "steps")


def cmd_seal(out_dir: str, variant: str = "flagship") -> None:
    import os
    if variant not in VARIANTS:
        raise SystemExit(f"unknown variant {variant}")
    nb = VARIANTS[variant]["seed_bytes"]
    seed = secrets.token_bytes(nb)
    wells = wells_mod.wells_for(FULL, wells_mod.L_FULL)
    res = run_path(FULL, DATA, seed, wells, wells_mod.L_FULL)
    os.makedirs(out_dir, exist_ok=True)
    chal = {
        "version": 3,
        "params": {
            "construction": "perspective-walk",
            "variant": variant,
            "seed_bits": VARIANTS[variant]["seed_bits"],
            "lift_version": 1,
            "digits": FULL.n_digits,
            "bits_per_digit": FULL.bits_per_digit,
            "L": wells_mod.L_FULL,
            "k": len(wells),
            "e": wells_mod.DEFAULT_E,
            "wells": [list(w) for w in wells],
        },
        "data": DATA.hex(),
        "data_commitment": sha(DATA),
        "nullifier_count": len(wells),
        "H": res.H,
    }
    key = {"version": 3, "variant": variant,
           "seed": seed.hex()}
    cpath = os.path.join(out_dir, "challenge.json")
    kpath = os.path.join(out_dir, "challenge_KEY.json")
    with open(cpath, "w") as f:
        json.dump(chal, f, indent=1)
        f.write("\n")
    # the key is written next to the challenge; move it somewhere
    # private before publishing the directory
    with open(kpath, "w") as f:
        json.dump(key, f, indent=1)
        f.write("\n")
    print(f"sealed {variant} challenge -> {cpath}")
    print(f"key (KEEP PRIVATE)         -> {kpath}")
    rc = gate_mod.gate(cpath, kpath, FULL)
    raise SystemExit(rc)


def cmd_gate(challenge: str, key: str) -> None:
    # the profile comes from the challenge's own public parameters
    # (the toy cases are 8 one-bit digits; the full model 9 octal)
    with open(challenge) as f:
        ch = json.load(f)
    pro = gate_mod.profile_for_params(ch.get("params", {}))
    raise SystemExit(gate_mod.gate(challenge, key, pro))


def cmd_demo() -> None:
    seed = secrets.token_bytes(32)
    wells = wells_mod.wells_for(FULL, wells_mod.L_FULL)
    res = run_path(FULL, DATA, seed, wells, wells_mod.L_FULL)
    print("== Voidwell-3 demo (one fresh flagship encoding) ==")
    print("the walk:", len(res.values) - 1, "steps;",
          len(wells), "wells at the primes",
          [w[0] for w in wells])
    for w in res.wells_detail:
        print(f"  well {w['j']}: perspective UC{w['j']}, digit "
              f"{w['digit']} nullified (ctr={w['ctr']}), trace law "
              f"holds ({w['trace_actual']})")
    i = 17
    path = res.open_state(FULL, i)
    print(f"ghost-disc proof for state {i}: {len(path)} hashes "
          f"(log-size); verifies:",
          res.verify_state(FULL, i))
    print("zeta-array: 16 cells, disentangled by the quaternion "
          "table, contracted into H")
    print("H:", res.H)
    # the fare ledger law (tau^2 = 0)
    from ucq import ucpoly
    P = ucpoly.path_polynomial(res.values[1:], res.fares)
    print("fare ledger: fare(path) =", P.fare(),
          "== sum of step fares = ", sum(res.fares))


def cmd_toy() -> None:
    from voidwell3.small_model import harness
    raise SystemExit(harness.main())


def cmd_attack(challenge: str) -> None:
    from voidwell3.attacker import seed_search, surface_audit
    rc1 = surface_audit.main(challenge)
    rc2 = seed_search.main(challenge)
    raise SystemExit(rc1 or rc2)


def cmd_verify() -> None:
    from tests import verify
    raise SystemExit(verify.main())


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    cmd = argv[1]
    if cmd == "params":
        cmd_params()
    elif cmd == "encode":
        cmd_encode(argv[2] if len(argv) > 2 else "00" * 32)
    elif cmd == "seal":
        cmd_seal(argv[2] if len(argv) > 2
                 else "contests/flagship",
                 argv[3] if len(argv) > 3 else "flagship")
    elif cmd == "gate":
        cmd_gate(argv[2], argv[3])
    elif cmd == "demo":
        cmd_demo()
    elif cmd == "toy":
        cmd_toy()
    elif cmd == "attack":
        cmd_attack(argv[2])
    elif cmd == "verify":
        cmd_verify()
    else:
        print(__doc__)
        raise SystemExit(2)


if __name__ == "__main__":
    main(sys.argv)
