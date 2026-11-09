"""Acceptance tests 1, 2, 4 (engine) and 5, 6 (ledger) -- CTS section 7 /
Developer Handoff section 6.  Also runnable standalone:
python tests/test_engine.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rtfa import FareAudit                                    # noqa: E402
from rtfa.api import value_spec                               # noqa: E402


# ---------------------------------------------------------------------------
# Test 1: the float rounding loss  (Q:1/10 -> F64)
# ---------------------------------------------------------------------------

def test_1_float_rounding_loss():
    audit = FareAudit(run_id="t1")
    r = audit.transition("Q:1/10", "F64", "cast")
    assert r.fare.exactness == "R", r.fare.exactness
    assert r.tgt_display == "0.10000000000000000555...", r.tgt_display
    assert r.error.abs_decimal == "5.551e-18", r.error.abs_decimal
    # exact absolute error: 1/180143985094819840
    assert r.error.abs_exact == "1/180143985094819840", r.error.abs_exact
    # ULP distance: exactly 2/5 of one binary64 ulp at 0.1; the golden
    # "0.5" is the round-to-nearest-even bound, which holds.
    assert r.error.ulp == "2/5", r.error.ulp
    assert r.error.ulp_bound_ok is True
    # the exact bits stored
    assert r.exact_display == "1/10"
    assert value_spec("F64", r.target_native) == \
        "F64:0x1.999999999999ap-4"


def test_1b_reflection_irreversibility():
    audit = FareAudit(run_id="t1b")
    info = audit.reflection("Q:1/10", "F64", "Q")
    assert info["equal"] is False
    assert info["returned_display"] == "3602879701896397/36028797018963968"


# ---------------------------------------------------------------------------
# Test 2: the integer division overflow (Z:3 / 2 bends to Q)
# ---------------------------------------------------------------------------

def test_2_division_bend():
    audit = FareAudit(run_id="t2")
    r = audit.transition("Z64:3", "Z64", "div(2)")
    assert r.tgt_id == "Q", r.tgt_id
    assert r.tgt_display == "3/2", r.tgt_display
    assert r.fare.overflow is True
    assert r.fare.exactness == "E"          # exact once the bend is paid
    assert any("bent to Q" in n for n in r.notes)


# ---------------------------------------------------------------------------
# Test 4: the phase obfuscation (Q:-4 -> sqrt -> F64)
# ---------------------------------------------------------------------------

def test_4_phase_obfuscation():
    audit = FareAudit(run_id="t4")
    r = audit.transition("Q:-4", "F64", "sqrt")
    assert r.routed_via == "C128"
    assert r.tgt_display == "2.0[[i]]", r.tgt_display
    assert r.fare.phase_obfuscated is True
    assert r.fare.exactness == "A"
    assert r.exact_display == "2 (magnitude)"


def test_4b_g6gf_sqrt4_marked():
    audit = FareAudit(run_id="t4b")
    r = audit.transition("Q:4", "F64", "sqrt")
    assert r.tgt_display == "[[2.0]]", r.tgt_display
    assert r.fare.phase_obfuscated is True


# ---------------------------------------------------------------------------
# Test 5: the nilpotent deduplication (same transition three times)
# ---------------------------------------------------------------------------

def test_5_nilpotent_dedup(tmp_path=None):
    audit = FareAudit(run_id="uuid-0001")
    for _ in range(3):
        audit.transition("Q:1/10", "F64", "cast")
    assert len(audit.ledger.entries) == 1
    assert audit.ledger.entries[0]["annihilation_counter"] == 2
    if tmp_path is not None:
        n = audit.ledger.export(tmp_path / "ledger.jsonl")
        assert n == 1


# ---------------------------------------------------------------------------
# Test 6: hash chain integrity (tamper with line 3)
# ---------------------------------------------------------------------------

def _tamper_corpus(path):
    audit = FareAudit(run_id="uuid-123")
    audit.transition("Q:1/3", "F64", "cast")
    audit.transition("Q:1/7", "F64", "cast")
    audit.transition("Z64:3", "Z64", "div(2)")
    audit.transition("Q:2/7", "F64", "cast")
    audit.transition("Q:-4", "F64", "sqrt")
    assert audit.ledger.export(path) == 5


def test_6_hash_chain(tmp_path):
    from rtfa.ledger import verify
    import json
    path = tmp_path / "ledger.jsonl"
    _tamper_corpus(path)
    issues, stats = verify(path)
    assert issues == [], issues
    assert stats["entries"] == 5
    # tamper with line 3
    lines = path.read_text().splitlines()
    entry = json.loads(lines[2])
    entry["record_payload"]["target_val_computed"] = "0.999999 HACKED"
    lines[2] = json.dumps(entry, sort_keys=True)
    path.write_text("\n".join(lines) + "\n")
    issues, _ = verify(path)
    assert any(i.startswith("Hash Mismatch at index 3") for i in issues), \
        issues


def test_6b_transition_key_tamper(tmp_path):
    from rtfa.ledger import verify
    import json
    path = tmp_path / "ledger.jsonl"
    _tamper_corpus(path)
    lines = path.read_text().splitlines()
    entry = json.loads(lines[1])
    entry["transition_key"] = "f" * 64
    lines[1] = json.dumps(entry, sort_keys=True)
    path.write_text("\n".join(lines) + "\n")
    issues, _ = verify(path)
    assert any("Transition-key mismatch" in i for i in issues), issues


# ---------------------------------------------------------------------------
# Extras: the Apeirogon (CTS golden 5) and the PDD demo-5 loop
# ---------------------------------------------------------------------------

def test_apeirogon_cts_golden():
    audit = FareAudit(run_id="t-apeiron")
    seq = audit.sequence("F64:2.0", ["sqrt"] * 5, "F64")
    assert seq["halted_at"] == 3, seq["halted_at"]
    last = seq["legs"][-1]
    assert last.fare.exactness == "A"
    assert last.fare.saturation_event is True
    assert last.saturation.startswith("Apeirogon limit reached.")


def test_apeirogon_loop_100():
    audit = FareAudit(run_id="t-loop")
    ops = []
    for _ in range(100):
        ops += ["sqrt", "pow(2)"]
    seq = audit.sequence("F64:2.0", ops, "F64")
    assert seq["halted_at"] == 5, seq["halted_at"]
    assert seq["skipped"] == 195


# ---------------------------------------------------------------------------
# Extras: registry / MBP layer behaviour (PDD section 8)
# ---------------------------------------------------------------------------

def test_mbp_level_collision():
    audit = FareAudit(run_id="t-mbp")
    r = audit.transition("BIN:0b11", "Z64", "mul(BIN:0b100)")
    assert r.blocked is True
    assert r.fare.domain_violation is True
    assert r.fare.level_collision is True
    assert len(audit.ledger.entries) == 0     # no fare for a blocked move


def test_address_read_needs_cast():
    audit = FareAudit(run_id="t-addr")
    r = audit.transition("ADDR:0x7f3a1c", "Z64", "deref")
    assert r.blocked is True and r.fare.level_collision is True
    r = audit.transition("ADDR:0x7f3a1c", "Z64", "cast")
    assert not r.blocked and r.fare.exactness == "E"


def test_natural_subtraction_below_zero():
    audit = FareAudit(run_id="t-nat")
    r = audit.transition("N64:2", "N64", "sub(5)")
    assert r.blocked is True
    assert r.fare.domain_violation is True


if __name__ == "__main__":
    import inspect
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            params = inspect.signature(fn).parameters
            try:
                if any(p.default is inspect.Parameter.empty
                       and p.name != "self" for p in params.values()):
                    import tempfile
                    with tempfile.TemporaryDirectory() as td:
                        fn(Path(td))
                else:
                    fn()
                print(f"[PASS] {name}")
            except AssertionError as exc:
                failures += 1
                print(f"[FAIL] {name}: {exc}")
    sys.exit(1 if failures else 0)
