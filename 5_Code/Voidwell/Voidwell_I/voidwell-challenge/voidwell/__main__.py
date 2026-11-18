"""__main__.py -- the voidwell command line interface (spec D5-D7).

  python -m voidwell encode  --data <hex> --seed <hex> --wells <k>
                              --length 43 --out challenge.json
                              --key-out key.json
  python -m voidwell gate    --challenge challenge.json --key key.json
  python -m voidwell params

Exit codes for `gate`: 0 PASS, 1 FAIL, 2 malformed.
"""
from __future__ import annotations

import argparse
import json
import sys

from ucq.field import P, P_HEX
from ucq.lift import FULL, LIFT_VERSION
from voidwell.encoder import encode
from voidwell.gate import gate


def cmd_encode(args) -> int:
    data = bytes.fromhex(args.data)
    seed = bytes.fromhex(args.seed)
    challenge, key, detail = encode(FULL, data, seed, args.wells,
                                    args.length)
    with open(args.out, "w") as f:
        json.dump(challenge, f, indent=1)
        f.write("\n")
    if args.key_out:
        with open(args.key_out, "w") as f:
            json.dump(key, f, indent=1)
            f.write("\n")
    print(f"H = {challenge['H']}")
    print(f"schedule_digest = {challenge['schedule_digest']}")
    print(f"wrote {args.out}"
          + (f" and {args.key_out}" if args.key_out else ""))
    return 0


def cmd_gate(args) -> int:
    return gate(args.challenge, args.key, pro=FULL)


def cmd_params(_args) -> int:
    print("Parameter table (the demo's hard-coded parameters, "
          "matching rules.md):")
    print()
    print(f"  Field            F_p, p = 2^256 - 2^32 - 977")
    print(f"                   p = {P_HEX}")
    print(f"  Digivector       27 bits, 9 octal digits (fare-octal)")
    print(f"  UCQ              4x4 matrix over F_p (16 dof, sec. 6.2.8b)")
    print(f"  Well operator    GL(4, F_p) conjugation, PRF-derived")
    print(f"                   (rejection-sampled to nullify digit n_j)")
    print(f"  Checkpoints      k x 27 bits, PRF-derived")
    print(f"  Path length      L = 43")
    print(f"  Hash             SHA-256, iterated over the full path")
    print(f"  Lift version     {LIFT_VERSION}")
    print(f"  Key space        2^256 x C(43,k) x 9^k  (spec formula)")
    print(f"                   k=0: 2^256   k=1: 2^264.6   "
          f"k=3: 2^279.1   k=6: 2^297.6")
    print(f"                   (spec D9's '2^278'/'2^300' are roundings;")
    print(f"                    exact: C(43,3)*9^3 = 2^23.10, "
          f"C(43,6)*9^6 = 2^41.57)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="voidwell")
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("encode", help="produce challenge + key")
    e.add_argument("--data", required=True, help="message hex")
    e.add_argument("--seed", required=True, help="seed hex (<=255 bytes)")
    e.add_argument("--wells", type=int, required=True)
    e.add_argument("--length", type=int, default=43)
    e.add_argument("--out", default="challenge.json")
    e.add_argument("--key-out", default=None)
    e.set_defaults(func=cmd_encode)

    g = sub.add_parser("gate", help="verify a key against a challenge")
    g.add_argument("--challenge", required=True)
    g.add_argument("--key", required=True)
    g.set_defaults(func=cmd_gate)

    p = sub.add_parser("params", help="print the parameter table")
    p.set_defaults(func=cmd_params)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
