"""Registry-focused tests: the sign loss (CTS Test 3), IEEE 754 edge
cases, moveset enforcement.  Standalone: python tests/test_registry.py"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rtfa import FareAudit, registry                    # noqa: E402
from rtfa.engine import execute                         # noqa: E402


# ---------------------------------------------------------------------------
# Test 3: the sign loss (Z:-1 -> N64)
# ---------------------------------------------------------------------------

def test_3_sign_loss():
    audit = FareAudit(run_id="t3")
    r = audit.transition("Z64:-1", "N64", "cast")
    assert r.tgt_display == "18446744073709551615", r.tgt_display
    assert r.fare.sign_lost is True
    assert r.fare.domain_violation is True
    assert r.fare.level_collision is True
    assert r.fare.exactness == "T"
    # PDD demo 3 variant (-5) flags the same way
    r5 = audit.transition("Z64:-5", "N64", "cast")
    assert r5.tgt_display == "18446744073709551611"
    assert r5.fare.sign_lost and r5.fare.domain_violation \
        and r5.fare.level_collision


# ---------------------------------------------------------------------------
# IEEE 754 edge cases (CTS section 8: NaN, Inf, -0.0, subnormals)
# ---------------------------------------------------------------------------

def test_overflow_to_infinity():
    audit = FareAudit(run_id="t-edge")
    r = audit.transition("F64:1.7976931348623157e308", "F64", "mul(2)")
    assert r.tgt_display == "+inf"
    assert r.fare.overflow and r.fare.exactness == "A"


def test_underflow_to_zero():
    audit = FareAudit(run_id="t-edge")
    r = audit.transition("F64:5e-324", "F64", "div(2)")
    assert r.tgt_display == "0.0"
    assert r.fare.underflow and r.fare.exactness == "A"


def test_negative_zero_abs():
    audit = FareAudit(run_id="t-edge")
    r = audit.transition("F64:-0.0", "F64", "abs")
    assert r.tgt_display == "0.0"
    assert r.fare.sign_lost and r.fare.magnitude_collapsed


def test_subnormal_representation():
    # a value that lands on a subnormal is flagged U (precision lost)
    audit = FareAudit(run_id="t-edge")
    r = audit.transition("F64:1e-320", "F64", "mul(1)")
    assert r.fare.underflow is True or r.fare.exactness == "R"


# ---------------------------------------------------------------------------
# Moveset enforcement (algebraic incapacity)
# ---------------------------------------------------------------------------

def test_movesets_declared():
    for rid in ("BIN", "N64", "Z64", "Q", "F64", "D128", "C128", "ADDR"):
        node = registry.get(rid)
        assert node.moveset, rid
        assert node.incapacity, rid
    assert "sqrt" not in registry.get("Z64").moveset
    assert "sqrt" in registry.get("F64").moveset
    assert registry.get("F64").overflow_mode == "to_infinity"


def test_sqrt_into_Q_is_domain_violation():
    # Q cannot resolve the irrational root (registry incapacity)
    audit = FareAudit(run_id="t-moveset")
    r = audit.transition("Q:2", "Q", "sqrt")
    assert r.blocked is True
    assert r.fare.domain_violation is True


def test_fare_ladder_table():
    for rung, info in registry.FARE_LADDER.items():
        assert info["mbp_layer"] == rung + 1
    assert registry.FARE_LADDER[1]["name"] == "Cipher"
    assert registry.FARE_LADDER[2]["name"] == "Address"


def test_projection_path_dependence():
    audit = FareAudit(run_id="t-path")
    direct = audit.transition("Q:1/10", "D128", "cast")
    assert direct.fare.exactness == "E" and direct.tgt_display == "0.1"
    info = audit.projection("Q:1/10", ["F64", "D128"])
    assert info["final_display"] == \
        "0.1000000000000000055511151231257827"
    assert info["delta"] is not None


if __name__ == "__main__":
    import inspect
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"[PASS] {name}")
            except AssertionError as exc:
                failures += 1
                print(f"[FAIL] {name}: {exc}")
    sys.exit(1 if failures else 0)
