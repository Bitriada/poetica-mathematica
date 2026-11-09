"""rtfa.cli -- the command line interface (CTS module 6).

    fare-audit run     --src "Q:1/10" --tgt F64 --op cast
    fare-audit run     --src "Q:1/10" --tgt F64 --op cast \
                      --mode reflection --return-to Q
    fare-audit run     --src "Z:3" --path "Z64 -> Q -> F64" --op "div(2)" \
                      --mode projection
    fare-audit demo    --out out/          # the full claimed-output suite
    fare-audit verify  --ledger out/ledger.jsonl

Run with ``python -m rtfa ...``.  ``demo`` exits non-zero if any golden
check of the acceptance suite fails.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, registry
from .api import FareAudit
from .ledger import verify as verify_ledger
from .report import (audit_table_csv, blocked_report, compaction_report,
                     generate_all, irreversibility_report,
                     saturation_report)

F64_MAX = 1.7976931348623157e308


# ---------------------------------------------------------------------------
# printing helpers
# ---------------------------------------------------------------------------

def _rule(char="="):
    print(char * 78)


def _title(text):
    print()
    _rule()
    print(text)
    _rule()


def _show(result, prefix="  "):
    src = result.src_spec or f"{result.src_id}:{result.src_display}"
    print(f"{prefix}[{src}] "
          f"--{result.op}"
          + (f"({result.arg_display})" if result.arg_display else "")
          + f"--> [{result.tgt_id}]  =  {result.tgt_display}")
    print(f"{prefix}  fare: {result.fare.codes()}   "
          f"exact: {result.exact_display}   "
          f"abs err: {result.error.abs_decimal}"
          + (f"   ulp: {result.error.ulp}"
             + ("" if result.error.ulp_bound_ok is None else
                f"  (bound 1/2 {'ok' if result.error.ulp_bound_ok else 'EXCEEDED'})")
             if result.error.ulp != "-" else ""))
    for note in result.notes:
        print(f"{prefix}  note: {note}")
    if result.saturation:
        print(f"{prefix}  SATURATION: {result.saturation}")


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

def cmd_run(args) -> int:
    audit = FareAudit(run_id=args.run_id)
    if args.mode == "projection":
        path = [p.strip() for p in args.path.split("->")]
        info = audit.projection(args.src, path, args.op)
        for leg in info["legs"]:
            _show(leg)
        print(f"\n  path delta: {info['delta']}")
    elif args.mode == "reflection":
        info = audit.reflection(args.src, args.tgt, args.return_to,
                                args.op)
        for leg in info["legs"]:
            _show(leg)
        print(f"\n  round trip exact: {info['equal']}")
    else:
        result = audit.transition(args.src, args.tgt, args.op,
                                  rounding=args.round)
        _show(result)
    if args.ledger:
        n = audit.ledger.export(args.ledger)
        print(f"\n  ledger: {n} entries -> {args.ledger}")
    if args.out:
        n = audit_table_csv(audit.ledger, args.out)
        print(f"  audit table: {n} rows -> {args.out}")
    return 0


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------

def cmd_verify(args) -> int:
    issues, stats = verify_ledger(args.ledger)
    if issues:
        for issue in issues:
            print(f"  {issue}")
        print(f"\nLEDGER VERIFICATION FAILED: {args.ledger}")
        return 1
    print(f"  OK: {stats['entries']} entries, chain intact, "
          f"head sha256:{stats['head_hash'][:16]}...")
    return 0


# ---------------------------------------------------------------------------
# demo -- the full claimed-output suite (PDD section 10 / CTS section 7)
# ---------------------------------------------------------------------------

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, cond, detail: str = "") -> bool:
    ok = bool(cond)
    CHECKS.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    if not ok and detail:
        print(f"         got: {detail}")
    return ok


def cmd_demo(args) -> int:
    global CHECKS
    CHECKS = []
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    _title("FARE-AUDIT DEMO SUITE -- the claimed outputs, one by one")
    print("  Paradigm: Algebraic Observation (read-only).  The tool never")
    print("  heals, fixes, or coerces the math; it observes transitions")
    print("  and records the Fare (MBP Central Inversion).")
    print("\n" + registry.print_registry())

    audit = FareAudit(run_id="fare-audit-demo-01")

    # -- 1. the Q -> F64 loss (Test 1 / PDD demo 1) --------------------
    _title("1. THE Q -> F64 LOSS  (CTS Test 1, PDD demo 1)  --  "
           "Q:1/10 --cast--> F64")
    r = audit.transition("Q:1/10", "F64", "cast")
    _show(r)
    check("exactness is R (rounded)", r.fare.exactness == "R",
          r.fare.exactness)
    check("target is the nearest binary64 "
          "0.10000000000000000555...",
          r.tgt_display == "0.10000000000000000555...", r.tgt_display)
    check("absolute error is 5.551e-18 (golden 5.55e-18)",
          r.error.abs_decimal == "5.551e-18", r.error.abs_decimal)
    check("ULP distance is 2/5 (the golden 0.5 is the round-to-nearest "
          "bound, and it holds)",
          r.error.ulp == "2/5" and r.error.ulp_bound_ok is True,
          f"ulp={r.error.ulp} bound_ok={r.error.ulp_bound_ok}")
    print("  exact source      : 1/10")
    print("  exact target bits : 3602879701896397/36028797018963968")

    # -- 2. the division bend (Test 2 / PDD demo 2) ---------------------
    _title("2. THE DIVISION BEND  (CTS Test 2, PDD demo 2)  --  "
           "Z64:3 --div(2)--> Z64")
    r = audit.transition("Z64:3", "Z64", "div(2)")
    _show(r)
    check("environment bent: target repr is Q", r.tgt_id == "Q", r.tgt_id)
    check("result is Q:3/2", r.tgt_display == "3/2", r.tgt_display)
    check("overflow flag set (division overflow forced the bend)",
          r.fare.overflow is True)
    check("the value itself is exact in Q (exactness E)",
          r.fare.exactness == "E", r.fare.exactness)

    # -- 3. the sign loss (Test 3 / PDD demo 3) --------------------------
    _title("3. THE SIGN LOSS  (CTS Test 3, PDD demo 3)  --  "
           "Z64:-1 --cast--> N64   (and the PDD variant -5)")
    r = audit.transition("Z64:-1", "N64", "cast")
    _show(r)
    check("bit pattern re-read: 18446744073709551615",
          r.tgt_display == "18446744073709551615", r.tgt_display)
    check("sign lost (S)", r.fare.sign_lost is True)
    check("domain violation (D / PDD's V)", r.fare.domain_violation is True)
    check("level collision (X: signed cipher re-read as unsigned)",
          r.fare.level_collision is True)
    check("exactness T (the signed reading was truncated away)",
          r.fare.exactness == "T", r.fare.exactness)
    r5 = audit.transition("Z64:-5", "N64", "cast")
    _show(r5)
    check("PDD variant Z64:-5 -> N64 flags S,D,X",
          r5.fare.sign_lost and r5.fare.domain_violation
          and r5.fare.level_collision)

    # -- 4. the phase obfuscation (Test 4 / PDD demo 4) ------------------
    _title("4. THE PHASE OBFUSCATION  (CTS Test 4, PDD demo 4)  --  "
           "Q:-4 --sqrt--> F64")
    r = audit.transition("Q:-4", "F64", "sqrt")
    _show(r)
    check("routed through C128 (dimensional lift)",
          r.routed_via == "C128", str(r.routed_via))
    check("result is 2.0[[i]] -- the [[b]] marker applied",
          r.tgt_display == "2.0[[i]]", r.tgt_display)
    check("phase obfuscated (P)", r.fare.phase_obfuscated is True)
    check("exactness A (the true value 2i is not representable in F64)",
          r.fare.exactness == "A", r.fare.exactness)
    print("  G6GF 3.4 companion: sqrt(Q:4) returns marked as well:")
    r4 = audit.transition("Q:4", "F64", "sqrt")
    _show(r4)
    check("sqrt(Q:4) -> F64 renders [[2.0]] (G6GF: sqrt(4) = [[2]])",
          r4.tgt_display == "[[2.0]]", r4.tgt_display)

    # -- 5. the reflection audit (PDD section 5 mode 2) ------------------
    _title("5. REFLECTION AUDIT  --  Q:1/10 -> F64 -> Q   (irreversibility)")
    info = audit.reflection("Q:1/10", "F64", "Q")
    for leg in info["legs"]:
        _show(leg)
    check("round trip returns 3602879701896397/36028797018963968, "
          "not 1/10 (PDD section 5 golden)",
          info["returned_display"] ==
          "3602879701896397/36028797018963968",
          info["returned_display"])
    check("round trip is NOT exact (irreversible)",
          info["equal"] is False)
    print(f"  delta: {info['delta']}")
    print("  (note: the first leg annihilates into ledger entry 1 -- "
          "the same fare cannot be paid twice; tau^2 = 0)")

    # -- 6. the projection audit (PDD section 5 mode 3) ------------------
    _title("6. PROJECTION AUDIT  --  Q:1/10 -> F64 -> D128   "
           "(path dependence)")
    direct = audit.transition("Q:1/10", "D128", "cast")
    _show(direct)
    check("direct Q:1/10 -> D128 is exact (decimal holds tenths)",
          direct.fare.exactness == "E" and direct.tgt_display == "0.1",
          direct.tgt_display)
    info = audit.projection("Q:1/10", ["F64", "D128"])
    for leg in info["legs"]:
        _show(leg)
    check("path Q->F64->D128 ends at 0.1000000000000000055511151231257827 "
          "(path dependence)",
          info["final_display"] ==
          "0.1000000000000000055511151231257827",
          info["final_display"])
    check("the two paths disagree (cumulative fare is real)",
          info["final_display"] != direct.tgt_display)
    print(f"  path delta vs 1/10: {info['delta']}")

    # -- 7. the apeirogon, CTS golden 5 -----------------------------------
    _title("7. THE APEIROGON  (CTS golden 5)  --  F64:2.0 --sqrt--> F64, "
           "five times")
    seq = audit.sequence("F64:2.0", ["sqrt"] * 5, "F64",
                         label="cts-golden-5")
    for leg in seq["legs"]:
        _show(leg)
    check("saturation event fires on the 3rd sqrt (drift limit 3)",
          seq["halted_at"] == 3, str(seq["halted_at"]))
    check("the halting record carries A + saturation_event",
          seq["legs"][-1].fare.exactness == "A"
          and seq["legs"][-1].fare.saturation_event)
    check("message: 'Apeirogon limit reached. F environment cannot "
          "simulate the continuous curve. Requires C environment.'",
          seq["legs"][-1].saturation ==
          "Apeirogon limit reached. F environment cannot simulate the "
          "continuous curve. Requires C environment.")

    # -- 8. the apeirogon, PDD demo 5 (the 100-step loop) -----------------
    _title("8. THE APEIROGON  (PDD demo 5)  --  loop sqrt ; x^2, "
           "100 iterations")
    ops = []
    for _ in range(100):
        ops += ["sqrt", "pow(2)"]
    seq = audit.sequence("F64:2.0", ops, "F64", label="pdd-demo-5")
    for leg in seq["legs"]:
        _show(leg)
    check("the audit halts at step 5 (3rd sqrt), long before step 100 "
          "or any overflow",
          seq["halted_at"] == 5 and seq["skipped"] == 195,
          f"halted_at={seq['halted_at']} skipped={seq['skipped']}")

    # -- 9. MBP layer collision (PDD section 8) ---------------------------
    _title("9. MBP LEVEL COLLISION  (PDD section 8)  --  "
           "L2_Multiply(3,4) with L1 binary-string operands")
    r = audit.transition("BIN:0b11", "Z64", "mul(BIN:0b100)")
    _show(r)
    check("blocked: the audit prevents the cross-layer leak",
          r.blocked is True)
    check("flags D (domain violation) and X (level collision)",
          r.fare.domain_violation and r.fare.level_collision)
    check("no fare was ledgered for the blocked attempt",
          all(a["ledger_index"] is None for a in audit.blocked))

    # -- 10. the address read (CTS section 5) ------------------------------
    _title("10. THE ADDRESS READ  (CTS section 5)  --  "
           "ADDR:0x7f3a1c --deref--> Z64  without a cast")
    r = audit.transition("ADDR:0x7f3a1c", "Z64", "deref")
    _show(r)
    check("blocked with X (an F2 address may not be read as an F1 "
          "cipher without a cast)",
          r.blocked and r.fare.level_collision)
    r = audit.transition("ADDR:0x7f3a1c", "Z64", "cast")
    _show(r)
    check("the explicit cast is legal and exact",
          not r.blocked and r.fare.exactness == "E")

    # -- 11. overflow / underflow / |b| on -0.0 ----------------------------
    _title("11. IEEE 754 EDGE CASES  --  overflow, underflow, |b| on -0.0")
    r = audit.transition(f"F64:{F64_MAX!r}", "F64", "mul(2)")
    _show(r)
    check("F64_max * 2 -> +inf with O (overflow)",
          r.tgt_display == "+inf" and r.fare.overflow
          and r.fare.exactness == "A")
    r = audit.transition("F64:5e-324", "F64", "div(2)")
    _show(r)
    check("min subnormal / 2 -> 0.0 with U (underflow)",
          r.tgt_display == "0.0" and r.fare.underflow)
    r = audit.transition("F64:-0.0", "F64", "abs")
    _show(r)
    check("|b| on -0.0 flattens the sign bit (S) and collapses the "
          "magnitude (M)",
          r.fare.sign_lost and r.fare.magnitude_collapsed)

    # -- 12. nilpotence (Test 5) -------------------------------------------
    _title("12. THE NILPOTENT LEDGER  (CTS Test 5)  --  the same "
           "transition, three times")
    np_audit = FareAudit(run_id="nilpotence-test")
    for _ in range(3):
        np_audit.transition("Q:1/10", "F64", "cast")
    st = np_audit.ledger.stats()
    print(f"  3 executions of Q:1/10 -> F64 in run 'nilpotence-test':")
    print(f"    ledger entries : {st['entries']}")
    print(f"    annihilation   : counter "
          f"{np_audit.ledger.entries[0]['annihilation_counter']} "
          "on the single entry")
    n_lines = np_audit.ledger.export(out / "nilpotence_ledger.jsonl")
    check("the ledger holds exactly 1 entry",
          st["entries"] == 1, str(st["entries"]))
    check("its annihilation_counter is 2",
          np_audit.ledger.entries[0]["annihilation_counter"] == 2)
    check("the JSONL file has exactly 1 line", n_lines == 1)
    print("  also, inside the main run, the reflection/projection first "
          "legs annihilated:")
    print(f"    annihilated attempts so far: {len(audit.annihilated)}: "
          + ", ".join(f"step {a['step']} -> entry "
                      f"{a['ledger_index'] + 1}" for a in audit.annihilated))

    # -- 13. hash chain integrity (Test 6) ---------------------------------
    _title("13. HASH CHAIN INTEGRITY  (CTS Test 6)  --  tamper with "
           "line 3")
    tamper = FareAudit(run_id="tamper-test")
    tamper.transition("Q:1/3", "F64", "cast")
    tamper.transition("Q:1/7", "F64", "cast")
    tamper.transition("Z64:3", "Z64", "div(2)")
    tamper.transition("Q:2/7", "F64", "cast")
    tamper.transition("Q:-4", "F64", "sqrt")
    tamper.ledger.export(out / "tamper_ledger.jsonl")
    issues, _ = verify_ledger(out / "tamper_ledger.jsonl")
    check("the pristine 5-conversion chain verifies clean",
          issues == [], "; ".join(issues))
    lines = (out / "tamper_ledger.jsonl").read_text().splitlines()
    import json as _json
    entry3 = _json.loads(lines[2])
    entry3["record_payload"]["target_val_computed"] = "0.999999 HACKED"
    lines[2] = _json.dumps(entry3, sort_keys=True)
    (out / "tampered_ledger.jsonl").write_text("\n".join(lines) + "\n")
    issues, _ = verify_ledger(out / "tampered_ledger.jsonl")
    print(f"  tampered line 3 -> verification says: {issues}")
    check("verify fails with 'Hash Mismatch at index 3'",
          any(i.startswith("Hash Mismatch at index 3") for i in issues),
          "; ".join(issues))

    # -- 14. export everything ---------------------------------------------
    _title("14. REPORTS AND LEDGER EXPORT")
    texts = generate_all(audit, out)
    n_entries = audit.ledger.export(out / "ledger.jsonl")
    st = audit.ledger.stats()
    print(f"  main ledger        : {n_entries} entries, "
          f"{st['annihilations']} annihilated attempts "
          f"-> {out / 'ledger.jsonl'}")
    print(f"  audit table        : {texts['rows']} rows "
          f"-> {out / 'audit_table.csv'}")
    for name in ("irreversibility_report.txt", "saturation_report.txt",
                 "blocked_report.txt", "compaction_report.txt"):
        print(f"  {name:<26}-> {out / name}")
    issues, vstats = verify_ledger(out / "ledger.jsonl")
    check("the exported main ledger verifies clean",
          issues == [], "; ".join(issues))
    print(f"  verify: OK, {vstats['entries']} entries, head "
          f"sha256:{vstats['head_hash'][:16]}...")

    print()
    print(texts["irreversibility_report.txt"])
    print(texts["saturation_report.txt"])
    print(texts["blocked_report.txt"])
    print(texts["compaction_report.txt"])

    # -- verdict ------------------------------------------------------------
    _title("DEMO SUITE VERDICT")
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    for name, ok, detail in CHECKS:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print()
    _rule()
    if passed == len(CHECKS):
        print(f"ALL {len(CHECKS)} GOLDEN CHECKS PASSED -- the project's "
              "claimed outputs are reproduced.")
        _rule()
        return 0
    print(f"{len(CHECKS) - passed} of {len(CHECKS)} checks FAILED")
    _rule()
    return 1


# ---------------------------------------------------------------------------
# argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fare-audit",
        description="Representation Transition / Fare Audit (RTFA) v1.0")
    p.add_argument("--version", action="version",
                   version=f"fare-audit {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="audit one transition")
    run.add_argument("--src", required=True,
                     help='source value spec, e.g. "Q:1/10"')
    run.add_argument("--tgt", default="F64", help="target representation")
    run.add_argument("--op", default="cast",
                     help='operation, e.g. cast | sqrt | div(2) | mul(...)')
    run.add_argument("--mode", default="prime",
                     choices=["prime", "reflection", "projection"])
    run.add_argument("--return-to", default="Q",
                     help="final representation for --mode reflection")
    run.add_argument("--path", default=None,
                     help='"A -> B -> C" for --mode projection')
    run.add_argument("--round", default="nearest_even")
    run.add_argument("--run-id", default="cli-run")
    run.add_argument("--ledger", default=None, help="ledger JSONL output")
    run.add_argument("--out", default=None, help="audit table CSV output")
    run.set_defaults(func=cmd_run)

    demo = sub.add_parser("demo",
                          help="run the full demo suite (all claimed "
                               "outputs)")
    demo.add_argument("--out", default="out")
    demo.set_defaults(func=cmd_demo)

    ver = sub.add_parser("verify", help="verify a ledger's hash chain")
    ver.add_argument("--ledger", required=True)
    ver.set_defaults(func=cmd_verify)
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
