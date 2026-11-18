"""trinumeral CLI: demo, trials, show, spin, info."""

from __future__ import annotations

import argparse
import os
import sys
import time
from fractions import Fraction


def _parse_value(text: str):
    """'1/10' -> Fraction, '5' -> int, else float."""
    text = text.strip()
    if "/" in text:
        num, den = text.split("/")
        return Fraction(int(num), int(den))
    try:
        return int(text)
    except ValueError:
        return Fraction(text) if "." in text else float(text)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="trinumeral",
        description="The heterobase counting system of Poetica "
                    "Mathematica Ch. VIII sec. 8.4, operational")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("demo", help="the guided tour")
    sub.add_parser("trials", help="run the V1-V10 proof-by-trial "
                                  "battery -> results/TRINUMERAL_TRIALS.md")
    sub.add_parser("info", help="package info")

    s = sub.add_parser("show", help="construct a trinumeral from a value "
                                    "and show it")
    s.add_argument("value", help="e.g. 5, 1/10, -3/7")
    s.add_argument("--p", type=int, default=53, help="fractional bits")
    s.add_argument("--fb", choices=["stored", "exact"], default="stored")

    sp = sub.add_parser("spin", help="spinorial rotation demo")
    sp.add_argument("--angles", default="360,360",
                    help="comma-separated degrees, e.g. 360,360 or "
                         "720 or 360,-360")

    args = p.parse_args(argv)

    if args.cmd == "info":
        from trinumeral import __version__
        print(f"trinumeral {__version__} -- one value, three bases, "
              f"an exact trace")
        print("Ch. VIII sec. 8.4: binary (deep) | integer (forward) | "
              "float (backward); Lambda(V) trace; annihilation ladder; "
              "ghost disc; spinorial double cover")
        return 0

    if args.cmd == "demo":
        from trinumeral.demo import main as demo_main
        return demo_main()

    if args.cmd == "trials":
        from trinumeral.trials import run_trials, write_report
        print("[trinumeral] V1-V10 proof by trial ...")
        t0 = time.time()
        results = run_trials()
        os.makedirs("results", exist_ok=True)
        path = write_report(results, os.path.join(
            "results", "TRINUMERAL_TRIALS.md"))
        for k, v in results.items():
            print(f"    {k.split('_')[0]}: {v['verdict']}")
        print(f"[trinumeral] report: {path} ({time.time() - t0:.1f}s)")
        return 0

    if args.cmd == "show":
        from trinumeral import Trinumeral
        T = Trinumeral.omega_0(_parse_value(args.value), p=args.p,
                               fb_mode=args.fb)
        print(T.show())
        return 0

    if args.cmd == "spin":
        from trinumeral import SpinTally, SpinorialTally
        s = SpinorialTally(SpinTally(0, 0))
        print(f"start: {s!r}")
        for tok in args.angles.split(","):
            s = s.rotate(_parse_value(tok))
            print(f"rotate({tok}): sigma={s.sigma:+d}  tally={s.tally!r}"
                  f"  tau={s.tau}  ghost={s.ghost}  "
                  f"pure={s.is_pure()}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
