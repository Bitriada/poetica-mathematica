"""rtfa.engine -- the Transition Engine (CTS module 2, section 4.1).

Executes one audited transition at a time, exactly as the CTS
prescribes:

1. Precondition check -- does any environment in play own the operation
   (moveset), and does the Fare-Ladder rung structure allow it
   (level collision, CTS section 5)?
2. Execute exact math -- every operation is computed in exact arithmetic
   (rtfa.values: ``fractions.Fraction``, symbolic square roots, exact
   complex pairs).
3. Cast to the target -- IEEE 754 binary64 via Python floats (correctly
   rounded, round-to-nearest-even), decimal128 via a 34-digit context,
   integers with truncation / two's-complement wrap.
4. Generate the trace -- the exact result and the cast result are handed
   to the classifier (rtfa.classifier).

G6GF behaviours implemented here (papers: "Generative Construction of
6 Geometric Freedoms", "History of Math as a Sequence of Cognitive
Revolutions"):

* the division bend: 3/2 does not resolve in Z and the environment
  bends to Q (G6GF section 2, "the broken perfection");
* the dimensional lift: sqrt of a negative (or of a value whose source
  environment lacks the root vocabulary) routes through the complex
  plane; on return to a real environment the [[b]] obfuscation marker
  is applied (G6GF section 3.4; Fare Principle paper, section 5);
* the Apeirogon: nested irrational ^b / sqrt(b) inside the F environment
  accumulate a drift score; when it reaches 3 the engine raises a
  Goedelian Saturation Event and halts the path (G6GF section 4.6,
  CTS section 4.4).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from fractions import Fraction

from . import registry
from .classifier import FareVector, ErrorMetrics, classify
from .values import (Cplx, EVal, Rational, Sqrt, exact_equals_target,
                     exact_is_negative, exact_magnitude, exact_to_float,
                     fmt_decimal, fmt_exact, fmt_float, fmt_fraction,
                     parse_float_spec, parse_op, parse_value, sqrt_exact)

SATURATION_LIMIT = 3          # CTS 4.4 / handoff step 4: drift >= 3 fires
SATURATION_MESSAGE = (
    "Apeirogon limit reached. F environment cannot simulate the continuous "
    "curve. Requires C environment.")


# ---------------------------------------------------------------------------
# Result structures
# ---------------------------------------------------------------------------

@dataclass
class CastOutcome:
    native: object = None
    display: str = "-"
    overflow: bool = False
    underflow: bool = False
    wrapped: bool = False
    truncated: bool = False
    domain_violation: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class StepResult:
    """One audited transition -- the unit the ledger records."""
    mode: str                                    # prime|reflection|projection
    src_id: str
    src_display: str
    op: str
    arg_display: str | None
    tgt_id: str                                  # actual target (after bend)
    tgt_display: str
    exact: EVal | None
    exact_display: str
    src_spec: str = ""                           # raw input spec, as given
    target_native: object = None
    fare: FareVector = field(default_factory=FareVector)
    error: ErrorMetrics = field(default_factory=ErrorMetrics)
    notes: list[str] = field(default_factory=list)
    blocked: bool = False
    routed_via: str | None = None
    src_neg_zero: bool = False
    drift_after: int = 0
    saturation: str | None = None

    def payload(self) -> dict:
        """Canonical record payload (CTS section 2.3)."""
        return {
            "source_repr": self.src_id,
            "source_val_exact": self.src_display,
            "operation": self.op + (f"({self.arg_display})"
                                    if self.arg_display else ""),
            "target_repr": self.tgt_id,
            "target_val_computed": self.tgt_display,
            "exact_val": self.exact_display,
            "fare_vector": self.fare.to_dict(),
            "error_metrics": self.error.to_dict(),
            "mode": self.mode,
            "routed_via": self.routed_via,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Step 2: exact math
# ---------------------------------------------------------------------------

def _apply_op(src_val: EVal, op: str, arg: EVal | None) -> EVal:
    if op == "cast":
        return src_val
    if op == "abs":
        return exact_magnitude(src_val)
    if op == "sqrt":
        return sqrt_exact(src_val)
    if op in ("add", "sub", "mul", "div", "pow"):
        if arg is None:
            raise ValueError(f"{op} needs an argument, e.g. {op}(2)")
        if not isinstance(src_val, Rational) or not isinstance(arg, Rational):
            raise ValueError(f"{op} is only exact on rationals in v1")
        a, b = src_val.frac, arg.frac
        if op == "add":
            return Rational(a + b)
        if op == "sub":
            return Rational(a - b)
        if op == "mul":
            return Rational(a * b)
        if op == "div":
            if b == 0:
                raise ZeroDivisionError
            return Rational(a / b)
        if op == "pow":
            if b.denominator != 1:
                raise ValueError("non-integer exponent is out of scope in v1")
            return Rational(a ** b.numerator)
    raise ValueError(f"unknown operation {op!r}")


# ---------------------------------------------------------------------------
# Step 3: cast into the target representation
# ---------------------------------------------------------------------------

def _cast(node, exact: EVal, op: str):
    """Returns (outcome, bent_to_id, new_exact).  A bend replaces the
    target environment (Z/N division that does not resolve bends to Q);
    new_exact replaces the value when a complex hailing back to a real
    environment is reduced to its magnitude."""
    out = CastOutcome()
    env, rid = node.g6gf_env, node.id

    # ---- the division bend (G6GF section 2) --------------------------
    if env in ("N", "Z") and isinstance(exact, Rational) \
            and exact.frac.denominator != 1 and op == "div":
        out.notes.append(
            f"division did not resolve in {rid}; the environment bent to "
            "Q (G6GF section 2: the broken perfection)")
        out2, _, _ = _cast(registry.get("Q"), exact, op)
        out2.notes = out.notes + out2.notes
        return out2, "Q", None

    # ---- a complex value hailing back to a real environment -----------
    # The phase is destroyed on return; what renders is the magnitude
    # (G6GF 3.4: |b| catches the complex imposters).  The engine keeps
    # the original complex for the [[b]] marker decision.
    new_exact = None
    if env != "C" and isinstance(exact, Cplx):
        new_exact = exact_magnitude(exact)
        exact = new_exact
        out.notes.append("complex value hailed back to a real "
                         "environment: the phase is destroyed, the "
                         "magnitude renders (G6GF 3.4)")

    # ---- complex target ----------------------------------------------
    if env == "C":
        if isinstance(exact, Cplx):
            out.native = complex(exact_to_float(exact.re),
                                 exact_to_float(exact.im))
            if isinstance(exact.re, Rational) and isinstance(exact.im, Rational):
                out.display = fmt_exact(exact)
            else:
                out.display = (fmt_float(out.native.real)
                               + fmt_float(out.native.imag) + "i")
        else:
            out.native = complex(exact_to_float(exact), 0.0)
            out.display = fmt_float(out.native.real)
        return out, None, new_exact

    # ---- integer environments ----------------------------------------
    if env in ("N", "Z") or rid == "BIN":
        if not isinstance(exact, Rational):
            out.notes.append("an irrational cannot enter an integer "
                             "environment")
            out.domain_violation = True
            out.display = "BLOCKED"
            return out, None, new_exact
        fr = exact.frac
        if fr.denominator != 1:
            out.native = int(fr)                 # truncate toward zero
            out.truncated = True
        else:
            out.native = fr.numerator
        v = out.native
        if rid == "BIN":
            if not 0 <= v <= 255:
                out.domain_violation = True
                out.notes.append("value outside one 8-bit tape cell")
            out.display = bin(v)
            return out, None, new_exact
        if rid == "N64":
            if v < 0 and op != "cast":
                # N arithmetic below zero is a domain violation (PDD:
                # "subtraction < 0 throws Domain_Violation")
                out.domain_violation = True
                out.native = None
                out.display = "BLOCKED"
                out.notes.append("N cannot go below 0; the result of the "
                                 "operation leaves the environment")
                return out, None, new_exact
            if v < 0:
                out.native = v % (2 ** 64)       # bit pattern re-read
                out.wrapped = True
                out.domain_violation = True
                out.notes.append("negative re-read as an unsigned "
                                 "magnitude (Z64/N64 share the bit "
                                 "pattern)")
            elif v > registry.U64_MAX:
                out.native = v % (2 ** 64)
                out.wrapped = True
                out.overflow = True
            out.display = str(out.native)
            return out, None, new_exact
        if rid == "Z64":
            if not registry.I64_MIN <= v <= registry.I64_MAX:
                out.native = ((v + 2 ** 63) % 2 ** 64) - 2 ** 63
                out.wrapped = True
                out.overflow = True
                out.notes.append("wrapped modulo 2^64 (to_wrap)")
            out.display = str(out.native)
            return out, None, new_exact

    # ---- exact rational target ---------------------------------------
    if rid == "Q":
        if isinstance(exact, Rational):
            out.native = exact.frac
            out.display = fmt_fraction(exact.frac)
        else:
            out.notes.append("Q cannot render an irrational root exactly")
            out.display = fmt_exact(exact)
        return out, None, new_exact

    # ---- IEEE 754 binary64 -------------------------------------------
    if rid == "F64":
        f = exact_to_float(exact)
        if math.isinf(f):
            out.overflow = True
            out.notes.append("overflow to +inf (IEEE 754 to_infinity)")
        is_zero_src = isinstance(exact, Rational) and exact.frac == 0
        if f == 0 and not is_zero_src:
            out.underflow = True
            out.notes.append("underflow to zero (to_subnormal_then_zero)")
        elif f != 0 and abs(f) < 2.2250738585072014e-308:
            out.underflow = True
            out.notes.append("subnormal result (precision lost)")
        out.native = f
        out.display = fmt_float(f)
        return out, None, new_exact

    # ---- IEEE 754 decimal128 -----------------------------------------
    if rid == "D128":
        with localcontext() as ctx:
            ctx.prec = 80
            if isinstance(exact, Rational):
                d = (Decimal(exact.frac.numerator)
                     / Decimal(exact.frac.denominator))
            elif isinstance(exact, Sqrt):
                from .values import sqrt_decimal
                d = sqrt_decimal(exact.rad)
            else:
                d = None
            if d is None:
                out.notes.append("D128 received a complex value")
                return out, None, new_exact
            ctx.prec = registry.D128_DIGITS
            ctx.rounding = ROUND_HALF_EVEN
            q = ctx.plus(d)
        out.native = q
        out.display = fmt_decimal(q)
        if isinstance(exact, Rational) and Fraction(q) != exact.frac:
            out.notes.append("rounded to 34 significant decimal digits")
        return out, None, new_exact

    if rid == "ADDR":
        out.display = (hex(int(exact.frac))
                       if isinstance(exact, Rational) else fmt_exact(exact))
        return out, None, new_exact

    out.notes.append(f"no cast rule for {rid}")
    return out, None, None


# ---------------------------------------------------------------------------
# The transition
# ---------------------------------------------------------------------------

def execute(src_spec: str, op_spec: str, tgt_id: str, mode: str = "prime",
            drift: int = 0) -> tuple[StepResult, int]:
    """Run one audited transition.  Returns (result, drift_after)."""
    src_id, src_val = parse_value(src_spec)
    op, arg_spec = parse_op(op_spec)
    src_node = registry.get(src_id)
    tgt_node = registry.get(tgt_id)

    res = StepResult(mode=mode, src_id=src_id, src_display=fmt_exact(src_val),
                     op=op, arg_display=arg_spec, tgt_id=tgt_id,
                     tgt_display="-", exact=None, exact_display="-",
                     src_spec=src_spec)
    fare = res.fare

    # the sign bit of -0.0 is representational, not mathematical: it is
    # lost in the exact model, so it is detected on the raw spec
    if src_id == "F64":
        try:
            f0 = parse_float_spec(src_spec.split(":", 1)[1])
            res.src_neg_zero = (f0 == 0 and math.copysign(1.0, f0) < 0)
        except ValueError:
            pass

    # ---- step 1: preconditions (moveset + Fare-Ladder rungs) ---------
    home = registry.OP_HOME_RUNG.get(op)
    if home is None:
        raise ValueError(f"unknown operation {op!r}")
    if home > src_node.fare_rung:
        # The operand environment sits below the operation's rung: it
        # literally lacks the vocabulary (MBP 9.2, algebraic incapacity).
        res.blocked = True
        fare.domain_violation = True
        fare.level_collision = True
        note = registry.level_collision(op, src_node, tgt_node)
        res.notes.append(note or f"op '{op}' sits above the operand rung")
        res.tgt_display = "BLOCKED"
        return res, drift
    if home > tgt_node.fare_rung:
        # The target cannot receive the operation's result (CTS section 5:
        # an address read as a cipher without an explicit cast).
        res.blocked = True
        fare.level_collision = True
        if op not in tgt_node.moveset:
            fare.domain_violation = True
        res.notes.append(
            f"op '{op}' lives on rung F{home}; target {tgt_id} is rung "
            f"F{tgt_node.fare_rung} -- a downward crossing needs an "
            "explicit cast")
        res.tgt_display = "BLOCKED"
        return res, drift
    if op != "cast" and op not in src_node.moveset \
            and op not in tgt_node.moveset:
        res.blocked = True
        fare.domain_violation = True
        res.notes.append(f"'{op}' is in neither {src_id}'s nor {tgt_id}'s "
                         "moveset")
        res.tgt_display = "BLOCKED"
        return res, drift

    # ---- routing: the dimensional lift through the complex plane -----
    if op == "sqrt" and (op not in src_node.moveset
                         or exact_is_negative(src_val)):
        res.routed_via = "C128"
        res.notes.append("dimensional lift: sqrt routed through the "
                         "complex plane (C128); the fare is paid on return")

    # ---- step 2: exact math ------------------------------------------
    arg_val = None
    if arg_spec is not None:
        try:
            arg_val = Rational(Fraction(arg_spec))
        except (ValueError, ZeroDivisionError):
            _, arg_val = parse_value(arg_spec)
    try:
        exact = _apply_op(src_val, op, arg_val)
    except ZeroDivisionError:
        res.blocked = True
        fare.domain_violation = True
        res.notes.append("division by zero does not resolve below C")
        res.tgt_display = "BLOCKED"
        return res, drift
    except ValueError as exc:
        res.blocked = True
        fare.domain_violation = True
        res.notes.append(str(exc))
        res.tgt_display = "BLOCKED"
        return res, drift
    res.exact = exact
    res.exact_display = fmt_exact(exact)

    # ---- step 3: cast (with the division bend) -----------------------
    original_exact = exact                     # kept for the [[b]] marker
    outcome, bent_to, bent_exact = _cast(tgt_node, exact, op)
    if bent_to:
        res.tgt_id = bent_to
        tgt_node = registry.get(bent_to)
        fare.overflow = True                     # characteristic overflow
    if bent_exact is not None:
        exact = bent_exact
        res.exact = exact
        res.exact_display = fmt_exact(exact) + " (magnitude)"
    res.notes.extend(outcome.notes)
    res.target_native = outcome.native

    if outcome.native is None and outcome.domain_violation:
        # the cast itself refused: the value leaves the target's domain
        # (e.g. N arithmetic below zero, an irrational into an integer
        # environment) -- the transition never happens
        res.blocked = True
        res.tgt_display = "BLOCKED"
        fare.domain_violation = True
        classify(res, src_val, exact, outcome, None)
        return res, drift

    # ---- the [[b]] obfuscation marker on return from the complex plane
    marker = None
    if res.routed_via and tgt_node.g6gf_env != "C":
        fare.phase_obfuscated = True
        im_nonzero = (isinstance(original_exact, Cplx)
                      and not (isinstance(original_exact.im, Rational)
                               and original_exact.im.frac == 0))
        marker = "[[i]]" if im_nonzero else "wrap"
    if marker == "[[i]]":
        res.tgt_display = outcome.display + "[[i]]"
    elif marker == "wrap":
        res.tgt_display = f"[[{outcome.display}]]"
    else:
        res.tgt_display = outcome.display
    fare.overflow = fare.overflow or outcome.overflow
    fare.underflow = fare.underflow or outcome.underflow
    fare.domain_violation = fare.domain_violation or outcome.domain_violation

    # ---- the Apeirogon: drift score inside the F environment ---------
    if op in ("sqrt", "pow") and tgt_node.g6gf_env == "F" \
            and isinstance(exact, Sqrt):
        drift += 1
        res.drift_after = drift
        if drift >= SATURATION_LIMIT:
            fare.saturation_event = True
            res.saturation = SATURATION_MESSAGE
            res.notes.append(
                f"drift score {drift}: nested irrational operation inside "
                "the F environment (transfinite smoothing, G6GF 4.6)")
    else:
        res.drift_after = drift

    # ---- step 4: classify --------------------------------------------
    classify(res, src_val, exact, outcome, marker)
    return res, drift
