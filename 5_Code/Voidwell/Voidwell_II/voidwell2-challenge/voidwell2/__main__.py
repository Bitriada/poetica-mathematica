"""__main__.py -- the voidwell2 command line interface.

  python -m voidwell2 keygen  --variant flagship|compact [--out key.json]
  python -m voidwell2 encode  --variant ... --data <hex> [--seed <hex>]
                              --out challenge.json [--key-out key.json]
  python -m voidwell2 gate    --challenge challenge.json --key key.json
  python -m voidwell2 params
  python -m voidwell2 tickkey keygen --tick N --out ... [--challenge-out]
  python -m voidwell2 tickkey gate --challenge ... --key ...
  python -m voidwell2 tickkey demo

Exit codes for `gate`: 0 PASS, 1 FAIL, 2 malformed.
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys

from ucq.field import P, P_HEX
from ucq.lift import FULL
from voidwell2 import tickkey
from voidwell2.encoder import VARIANTS, encode
from voidwell2.gate import gate
from voidwell2.wells import K_FULL, L_FULL, WELLS_FULL

DATA_DEFAULT = "00112233"


def _dump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)
        f.write("\n")


def cmd_keygen(args) -> int:
    n = VARIANTS[args.variant]["seed_bytes"]
    seed = secrets.token_bytes(n)
    key = {"version": 2, "variant": args.variant, "seed": seed.hex()}
    if args.out:
        _dump(key, args.out)
        print(f"wrote {args.out} ({args.variant}, {n}-byte seed)")
    else:
        print(seed.hex())
    return 0


def cmd_encode(args) -> int:
    data = bytes.fromhex(args.data)
    if args.seed is not None:
        seed = bytes.fromhex(args.seed)
    else:
        seed = secrets.token_bytes(
            VARIANTS[args.variant]["seed_bytes"])
    challenge, key, detail = encode(FULL, data, seed, L_FULL,
                                    args.variant)
    _dump(challenge, args.out)
    if args.key_out:
        _dump(key, args.key_out)
    print(f"variant   = {args.variant}")
    print(f"H         = {challenge['H']}")
    print(f"published = H + public params only "
          f"(no schedule digest, no nullifiers)")
    print(f"wrote {args.out}"
          + (f" and {args.key_out}" if args.key_out else ""))
    return 0


def cmd_gate(args) -> int:
    return gate(args.challenge, args.key, pro=FULL)


def cmd_params(_args) -> int:
    sec = {"flagship": "2^256", "compact": "2^128"}
    print("Voidwell-2 parameter table (the spec's hard-coded "
          "parameters):")
    print()
    print(f"  Field            F_p, p = 2^256 - 2^32 - 977")
    print(f"                   p = {P_HEX}")
    print(f"  Digivector       27 bits, 9 octal digits (fare-octal)")
    print(f"  UCQ              4x4 matrix over F_p (16 dof, sec. 6.2.8b)")
    print(f"  Well operator    GL(4, F_p) conjugation, PRF-derived,")
    print(f"                   rejection-sampled to nullify digit n_j")
    print(f"  Wells (PUBLIC)   the pi-skeleton: positions 3, 14, 15,")
    print(f"                   digits 3, 1, 4  (pi = 3.1415...)")
    print(f"                   -- {WELLS_FULL}")
    print(f"  Checkpoints      3 x 27 bits, PRF-derived")
    print(f"  Path length      L = {L_FULL}, k = {K_FULL} (fixed)")
    print(f"  Nullifier        SHA-256(ser(D') || full conjugated")
    print(f"                   matrix)  -- preimage domain 2^4123")
    print(f"  Publication      H + public parameters ONLY")
    print(f"  Lift version     1")
    for name, v in VARIANTS.items():
        print(f"  Variant {name:<9} key = {v['seed_bytes']} B seed, "
              f"security = {v['claim']}")
    print()
    print("  HONEST SECURITY STATEMENT: security = min(seed bits, 256);")
    print("  the assumption is SHA-256 preimage resistance; every")
    print("  other layer (fare-octal base, UCQ conjugation, fares,")
    print("  nullification) is integrity and narrative, audited as")
    print("  such.  The best attack is seed enumeration at FULL")
    print("  replay cost -- no dictionaries, no preimages, no early")
    print("  abort exist against a V2 challenge.")
    return 0


def _tickkey(args) -> int:
    sub = args.tk_cmd
    if sub == "keygen":
        challenge, key = tickkey.keygen(args.tick)
        _dump(key, args.out)
        _dump(challenge, args.challenge_out)
        print(f"tick = {args.tick}  "
              f"(security log2 = {args.tick.bit_length() - 1:.2f})")
        print(f"H    = {challenge['H']}")
        print(f"wrote {args.out} and {args.challenge_out}")
        return 0
    if sub == "gate":
        with open(args.challenge) as f:
            ch = json.load(f)
        with open(args.key) as f:
            key = json.load(f)
        ok = tickkey.gate(ch, key)
        print("PASS" if ok else "FAIL")
        return 0 if ok else 1
    if sub == "demo":
        rec = tickkey.demo()
        print(f"demo tick {rec['tick']} "
              f"(pi's first ten digits)")
        print(f"H = {rec['H']}")
        print(f"gate: {rec['gate']}")
        print(f"security = log2(tick) = "
              f"{rec['security_log2']} bits (a toy -- the floor)")
        print(f"telescope alpha+beta+gamma = 0 exact: "
              f"{rec['telescope_exact']}")
        print(f"integer sheet (staircase) at the demo tick: "
              f"{rec['integer_sheet']}")
        return 0
    return 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="voidwell2")
    sub = ap.add_subparsers(dest="cmd", required=True)

    kg = sub.add_parser("keygen", help="generate a random seed key")
    kg.add_argument("--variant", choices=sorted(VARIANTS),
                    required=True)
    kg.add_argument("--out", default=None)
    kg.set_defaults(func=cmd_keygen)

    e = sub.add_parser("encode", help="produce challenge + key")
    e.add_argument("--variant", choices=sorted(VARIANTS),
                   required=True)
    e.add_argument("--data", default=DATA_DEFAULT,
                   help=f"message hex (default {DATA_DEFAULT})")
    e.add_argument("--seed", default=None,
                   help="seed hex (default: random)")
    e.add_argument("--out", default="challenge.json")
    e.add_argument("--key-out", default=None)
    e.set_defaults(func=cmd_encode)

    g = sub.add_parser("gate", help="verify a key against a challenge")
    g.add_argument("--challenge", required=True)
    g.add_argument("--key", required=True)
    g.set_defaults(func=cmd_gate)

    p = sub.add_parser("params", help="print the parameter table")
    p.set_defaults(func=cmd_params)

    tk = sub.add_parser("tickkey", help="the pi-clock tick-key toy")
    tk_sub = tk.add_subparsers(dest="tk_cmd", required=True)
    tk_k = tk_sub.add_parser("keygen", help="encode a tick key")
    tk_k.add_argument("--tick", type=int, required=True)
    tk_k.add_argument("--out", default="tickkey.json")
    tk_k.add_argument("--challenge-out", default="tickkey_challenge.json")
    tk_g = tk_sub.add_parser("gate", help="verify a tick key")
    tk_g.add_argument("--challenge", required=True)
    tk_g.add_argument("--key", required=True)
    tk_d = tk_sub.add_parser("demo", help="the published demo tick")
    tk.set_defaults(func=_tickkey)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
