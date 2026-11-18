"""npcs CLI: trials, demo, keygen, commit, verify, info."""

from __future__ import annotations

import argparse
import os
import sys
import time


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="npcs",
        description="Nilpotent Path-Commitment Scheme (Fare-Octal + "
                    "UC-Q), operational")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("trials", help="run the T1-T10 proof-by-trial "
                                  "battery -> results/NPCS_TRIALS.md")
    sub.add_parser("demo", help="the guided tour (~10 s)")
    sub.add_parser("info", help="package info")

    k = sub.add_parser("keygen", help="generate a path key and print "
                                      "its commitment")
    k.add_argument("--length", type=int, default=64)
    k.add_argument("--seed", type=int, default=None)

    c = sub.add_parser("commit", help="commit to a path given as a "
                                      "comma-separated list of ints")
    c.add_argument("path")

    v = sub.add_parser("verify", help="verify a path against a "
                                      "commitment hex string")
    v.add_argument("path")
    v.add_argument("commitment", help="H:H_val:H_tr:L, hex, colon-"
                                      "separated")

    args = p.parse_args(argv)

    if args.cmd == "info":
        from npcs import __version__
        print(f"npcs {__version__} -- nilpotent path commitments, "
              f"exact integer arithmetic, zero deps")
        print("UC-Q (16D, tau^2 = 0) x Fare-Octal 27-bit chunks; "
              "bi-sheet commitments H = SHA-256(H_val || H_tr)")
        return 0

    if args.cmd == "demo":
        from npcs.demo import main as demo_main
        return demo_main()

    if args.cmd == "trials":
        from npcs.trials import run_trials, write_report
        print("[npcs] T1-T10 proof by trial ...")
        t0 = time.time()
        results = run_trials()
        os.makedirs("results", exist_ok=True)
        path = write_report(results, os.path.join("results",
                                                  "NPCS_TRIALS.md"))
        for k, v in results.items():
            print(f"    {k.split('_')[0]}: {v['verdict']}")
        print(f"[npcs] report: {path} ({time.time() - t0:.1f}s)")
        return 0

    if args.cmd == "keygen":
        import random
        from npcs import commit, generate_path
        rng = random.Random(args.seed) if args.seed is not None else None
        path = generate_path(args.length, rng)
        c = commit(path)
        print(f"path (secret!):   {','.join(str(x) for x in path)}")
        print(f"commitment:       {c.H.hex()}:{c.H_val.hex()}:"
              f"{c.H_tr.hex()}:{c.L}")
        return 0

    if args.cmd == "commit":
        from npcs import commit
        path = [int(x) for x in args.path.split(",")]
        c = commit(path)
        print(f"{c.H.hex()}:{c.H_val.hex()}:{c.H_tr.hex()}:{c.L}")
        return 0

    if args.cmd == "verify":
        from npcs import verify
        path = [int(x) for x in args.path.split(",")]
        h, h_val, h_tr, L = args.commitment.split(":")
        from npcs import Commitment
        c = Commitment(H=bytes.fromhex(h), H_val=bytes.fromhex(h_val),
                       H_tr=bytes.fromhex(h_tr), L=int(L))
        print("VALID" if verify(path, c) else "INVALID")
        return 0 if verify(path, c) else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
