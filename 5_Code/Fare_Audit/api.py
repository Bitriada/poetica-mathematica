"""rtfa.api -- the Audit Orchestrator (PDD section 3; CTS section 6.2).

``FareAudit`` is the object the CTS Python API specifies:

    from rtfa import FareAudit, Fraction, Decimal

    audit = FareAudit(run_id="demo-1")
    record = audit.transition(source="Q:1/10", target="F64",
                              operation="cast", rounding="nearest_even")
    print(record.fare.exactness)          # -> "R"
    audit.ledger.export("ledger.jsonl")

It builds the three audit modes of PDD section 5 (the GIF zones):

* Prime audit (one-way):        immediate loss of exactness;
* Reflection audit (round trip): irreversibility;
* Projection audit (multi-hop):  path dependence, cumulative fare;

enforces the GIF triadic rule through the engine's drift score and the
ledger's nilpotence, and records every attempt for the reports.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

from .engine import StepResult, execute
from .ledger import FareLedger
from .values import EVal, Rational, exact_equals_target, fmt_fraction


def value_spec(rep_id: str, native) -> str:
    """Re-serialize a computed value as a parseable source spec, so a
    multi-hop path can feed its own output forward without new error
    (floats round-trip through their exact hex form)."""
    if isinstance(native, float):
        return f"{rep_id}:{native.hex()}"
    if isinstance(native, Decimal):
        return f"{rep_id}:{native}"
    if isinstance(native, Fraction):
        return f"{rep_id}:{fmt_fraction(native)}"
    if isinstance(native, complex):
        return f"{rep_id}:{native.real!r}+{native.imag!r}j"
    return f"{rep_id}:{native}"


class FareAudit:
    """One audit run: engine + nilpotent ledger + attempt log."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.ledger = FareLedger(run_id)
        self.attempts: list[dict] = []
        self.reflections: list[dict] = []
        self.projections: list[dict] = []
        self._step = 0

    # ------------------------------------------------------------------ core

    def _record(self, result: StepResult, status: str, ledger_index,
                total_steps=None) -> dict:
        self._step += 1
        attempt = {"step": self._step, "run_id": self.run_id,
                   "result": result, "status": status,
                   "ledger_index": ledger_index}
        if total_steps is not None:
            attempt["total_steps"] = total_steps
        self.attempts.append(attempt)
        return attempt

    def transition(self, source: str, target: str, operation: str = "cast",
                   rounding: str = "nearest_even",
                   mode: str = "prime") -> StepResult:
        """One audited transition (prime audit when mode='prime')."""
        if rounding != "nearest_even":
            raise ValueError("v1 implements round-to-nearest-even only "
                             f"(requested {rounding!r})")
        result, _ = execute(source, operation, target, mode=mode, drift=0)
        if result.blocked:
            self._record(result, "blocked", None)
        else:
            status, idx = self.ledger.append(result.payload())
            self._record(result, status, idx)
        return result

    # ------------------------------------------------- reflection (round trip)

    def reflection(self, source: str, via: str, return_to: str,
                   operation: str = "cast") -> dict:
        """PDD section 5, mode 2: source -> via -> return_to; checks
        irreversibility of the round trip."""
        leg1 = self.transition(source, via, operation, mode="reflection")
        if leg1.blocked or leg1.target_native is None:
            info = {"source_spec": source,
                    "source_repr": source.split(":")[0], "via": via,
                    "return_to": return_to, "equal": False,
                    "returned_display": "BLOCKED", "delta": None}
            self.reflections.append(info)
            return info
        src2 = value_spec(leg1.tgt_id, leg1.target_native)
        leg2 = self.transition(src2, return_to, operation,
                               mode="reflection")
        from .values import parse_value
        _, src_exact = parse_value(source)
        returned = leg2.exact if leg2.exact is not None else None
        equal = (returned is not None
                 and exact_equals_target(src_exact, _native_of(returned)))
        delta = None
        if not equal and isinstance(returned, Rational) \
                and isinstance(src_exact, Rational):
            delta = fmt_fraction(returned.frac - src_exact.frac)
        info = {"source_spec": source,
                "source_repr": source.split(":")[0], "via": via,
                "return_to": return_to,
                "equal": equal,
                "returned_display": leg2.exact_display
                if leg2.exact is not None else "-",
                "delta": delta,
                "legs": (leg1, leg2)}
        self.reflections.append(info)
        return info

    # ------------------------------------------------- projection (multi-hop)

    def projection(self, source: str, path: list[str],
                   operation: str = "cast") -> dict:
        """PDD section 5, mode 3: multi-hop path; checks path dependence
        and the cumulative fare (final value vs the original source)."""
        legs = []
        cur = source
        halted = None
        for hop in path:
            res, drift = execute(cur, operation, hop, mode="projection",
                                 drift=0)
            if res.blocked:
                self._record(res, "blocked", None)
                legs.append(res)
                halted = "blocked"
                break
            status, idx = self.ledger.append(res.payload())
            self._record(res, status, idx)
            legs.append(res)
            if res.saturation:
                halted = "saturation"
                break
            if res.target_native is None:
                halted = "no value"
                break
            cur = value_spec(res.tgt_id, res.target_native)
        from .values import parse_value
        _, src_exact = parse_value(source)
        final = legs[-1]
        final_exact = final.exact
        delta = None
        if isinstance(final_exact, Rational) and isinstance(src_exact, Rational):
            delta = fmt_fraction(final_exact.frac - src_exact.frac)
        info = {"source": source, "path": path,
                "final_repr": final.tgt_id,
                "final_display": final.tgt_display,
                "delta": delta, "legs": legs, "halted": halted}
        self.projections.append(info)
        return info

    # ------------------------------------------------- sequences (the loop)

    def sequence(self, source: str, ops: list[str], target: str,
                 label: str = "") -> dict:
        """Run a chain of operations (the Apeirogon demos).  The drift
        score accumulates across the chain; a saturation event halts it."""
        legs: list[StepResult] = []
        cur = source
        drift = 0
        halted_at = None
        for i, op in enumerate(ops, start=1):
            res, drift = execute(cur, op, target, mode="projection",
                                 drift=drift)
            if res.blocked:
                attempt = self._record(res, "blocked", None,
                                       total_steps=len(ops))
                attempt["seq_step"] = i
                legs.append(res)
                halted_at = i
                break
            status, idx = self.ledger.append(res.payload())
            attempt = self._record(res, status, idx, total_steps=len(ops))
            attempt["seq_step"] = i
            legs.append(res)
            if res.saturation:
                halted_at = i
                break
            if res.target_native is None:
                halted_at = i
                break
            cur = value_spec(res.tgt_id, res.target_native)
        return {"label": label, "source": source, "ops": ops,
                "target": target, "legs": legs, "halted_at": halted_at,
                "skipped": len(ops) - halted_at if halted_at else 0,
                "final_drift": drift}

    # ------------------------------------------------- convenience

    @property
    def blocked(self) -> list[dict]:
        return [a for a in self.attempts if a["result"].blocked]

    @property
    def annihilated(self) -> list[dict]:
        return [a for a in self.attempts if a["status"] == "annihilated"]


def _native_of(exact: EVal):
    """Best native rendering of an exact value (for comparisons)."""
    from .values import exact_to_float
    if isinstance(exact, Rational):
        return exact.frac
    return exact_to_float(exact)
