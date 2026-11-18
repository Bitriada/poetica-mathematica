"""fare-octal CLI: verify, demo, info, address."""

from __future__ import annotations

import argparse
import os
import sys
import time


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="fare-octal",
        description="Fare-Octal counting system (Poetica Mathematica "
                    "Appendix A), operational")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("demo", help="the guided tour (~1 s)")
    sub.add_parser("info", help="package info")

    a = sub.add_parser("address", help="show the address of one state")
    a.add_argument("spec", help="'count:N' (linear count), 'value:N' "
                                "(squarefree value) or 'bits:N,N,..'")

    v = sub.add_parser("verify",
                       help="run the V1-V7 proof-by-trial checks and "
                            "write VERIFICATION.md")
    v.add_argument("--out", default="results")

    args = p.parse_args(argv)

    if args.cmd == "info":
        from fareoctal import __version__
        print(f"fare-octal {__version__} -- pure Python, zero deps")
        print("27 bits / 9 octal digits / 2^27 states; three readings:")
        print("  count (linear), value (squarefree Fare), h-weight (117 "
              "lattice H tensor)")
        return 0

    if args.cmd == "demo":
        from fareoctal.tour import main as tour_main
        return tour_main()

    if args.cmd == "verify":
        from fareoctal.verify import run_checks, write_report
        print("[fare-octal] V1-V7 proof by trial ...")
        t0 = time.time()
        results = run_checks()
        os.makedirs(args.out, exist_ok=True)
        path = write_report(results, os.path.join(args.out,
                                                  "VERIFICATION.md"))
        for k, v in results.items():
            print(f"    {k.split('_')[0]}: {v['verdict']}")
        print(f"[fare-octal] report: {path} ({time.time() - t0:.1f}s)")
        return 0

    # -- address -----------------------------------------------------------
    from fareoctal import (FareOctal, bit_address, digit_address,
                           linear_to_tensor)
    kind, _, val = args.spec.partition(":")
    try:
        if kind == "count":
            s = FareOctal.from_int(int(val))
        elif kind == "value":
            s = FareOctal.from_value(int(val))
        elif kind == "bits":
            s = FareOctal({int(x) for x in val.split(",") if x != ""})
        else:
            p.error("spec must be count:..., value:... or bits:...")
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(f"display   {s.display()}")
    print(f"count     {s.to_int()}")
    print(f"value     {s.value()}  (squarefree Fare reading)")
    print(f"tau labels (prime)  {s.active_prime_labels()}")
    print(f"tau labels (linear) {s.active_linear()}")
    print(f"h-weight  2^{s.h_exponent()}  (H-tensor embedding)")
    for b in s.active_linear():
        a = bit_address(b)
        print(f"    bit {b:2d}: cell (i={a['cell'][0]}, j={a['cell'][1]}, "
              f"k={a['cell'][2]})  digit D{a['digit']} pos {a['digit_bit']}"
              f"  prime {a['prime']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
