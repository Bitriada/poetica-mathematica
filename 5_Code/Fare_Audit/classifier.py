"""rtfa.classifier -- the Fare Classifier (CTS module 3, section 4.2).

Compares the exact mathematical value with the value the target
representation actually produced, and emits the **Fare Vector** (CTS
section 2.2): one exclusive exactness code plus co-occurring error
flags.

Exactness codes (mutually exclusive):
    E  exact        the target holds the exact value
    R  rounded      value representable in principle, rounded to the
                    nearest available target value (1/10 -> F64)
    T  truncated    low digits / bits discarded (3.9 -> Z, sign-bit
                    re-reads, two's-complement wraps)
    A  approximated the exact value is not representable in the target
                    even in principle (irrationals into finite floats,
                    complexes into reals, over/underflow sentinels)

Error flags:  O overflow, U underflow, D domain violation (the PDD also
writes this flag as V, "precondition breach" -- same condition), S sign
lost, P phase obfuscated ([[b]]), M magnitude collapsed (|b|), X level
collision, saturation event (the Apeirogon).

All comparisons are exact (``Fraction``); decimal evaluations of
irrationals are used only to *measure* the error, never to classify it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from . import registry
from .values import (Cplx, EVal, Rational, Sqrt, exact_equals_target,
                     exact_is_negative, fmt_fraction, sqrt_decimal)

FLAG_ORDER = (("overflow", "O"), ("underflow", "U"),
              ("domain_violation", "D"), ("sign_lost", "S"),
              ("phase_obfuscated", "P"), ("magnitude_collapsed", "M"),
              ("level_collision", "X"), ("saturation_event", "SAT"))


@dataclass
class FareVector:
    """CTS section 2.2 schema.  exactness may also be '-' for blocked
    transitions (no value was computed; documented extension)."""
    exactness: str = "-"
    overflow: bool = False
    underflow: bool = False
    domain_violation: bool = False
    sign_lost: bool = False
    phase_obfuscated: bool = False
    magnitude_collapsed: bool = False
    level_collision: bool = False
    saturation_event: bool = False

    def codes(self) -> str:
        parts = [self.exactness] if self.exactness != "-" else []
        parts += [code for attr, code in FLAG_ORDER
                  if getattr(self, attr)]
        return ",".join(parts) if parts else "-"

    def to_dict(self) -> dict:
        d = {"exactness": self.exactness}
        for attr, _ in FLAG_ORDER:
            d[attr] = getattr(self, attr)
        return d


@dataclass
class ErrorMetrics:
    abs_exact: str = "-"          # exact Fraction, when both sides rational
    abs_decimal: str = "-"        # scientific decimal, for the audit table
    rel: str = "-"
    ulp: str = "-"                # |target - exact| / ulp(target)
    ulp_bound_ok: bool | None = None   # None when not applicable

    def to_dict(self) -> dict:
        return {"abs_exact": self.abs_exact, "abs": self.abs_decimal,
                "rel": self.rel, "ulp": self.ulp,
                "ulp_bound_ok": self.ulp_bound_ok}


def _fmt_sci(x) -> str:
    """Three-significant-digit scientific notation (5.551e-18).  Display
    only -- the exact value is always kept alongside."""
    try:
        f = float(x)
    except (TypeError, ValueError, OverflowError):
        return "-"
    if f == 0:
        return "0"
    return f"{f:.3e}"


def _metrics_rational(exact_frac: Fraction, target_native) -> ErrorMetrics:
    """Exact metrics when the exact value is rational: floats and Decimals
    convert to Fraction without loss, so the error itself is exact."""
    m = ErrorMetrics()
    tgt = Fraction(target_native)
    err = tgt - exact_frac
    m.abs_exact = fmt_fraction(err)
    m.abs_decimal = _fmt_sci(err)
    if exact_frac != 0:
        m.rel = _fmt_sci(err / abs(exact_frac))
    if isinstance(target_native, float) and math.isfinite(target_native) \
            and target_native != 0:
        ulp = Fraction(math.ulp(target_native))
        q = err / ulp
        m.ulp = fmt_fraction(q) if q.denominator <= 10 ** 9 \
            else _fmt_sci(q)
        m.ulp_bound_ok = abs(q) <= Fraction(1, 2)
    return m


def _metrics_irrational(exact: Sqrt, target_native) -> ErrorMetrics:
    """Metrics against a 60-digit evaluation of the exact irrational."""
    m = ErrorMetrics()
    root = sqrt_decimal(exact.rad)
    tgt = target_native if isinstance(target_native, Decimal) \
        else Decimal(target_native)
    err = tgt - root
    m.abs_decimal = _fmt_sci(err)
    m.rel = _fmt_sci(err / root)
    if isinstance(target_native, float) and target_native != 0:
        m.ulp = _fmt_sci(err / Decimal(math.ulp(target_native)))
        m.ulp_bound_ok = abs(err) <= Decimal(math.ulp(target_native)) / 2
    return m


def classify(res, src_val: EVal, exact: EVal, outcome, marker) -> None:
    """Fill res.fare and res.error in place (CTS section 4.2)."""
    fare: FareVector = res.fare
    fare.overflow = fare.overflow or outcome.overflow
    fare.underflow = fare.underflow or outcome.underflow
    native = res.target_native
    tgt_node = registry.get(res.tgt_id)

    # ---- sign lost (CTS 4.2) ------------------------------------------
    src_negative = exact_is_negative(src_val)
    if src_negative and native is not None:
        if outcome.wrapped:
            fare.sign_lost = True
        else:
            try:
                if Fraction(native) >= 0 and \
                        not exact_equals_target(exact, native):
                    fare.sign_lost = True
            except (TypeError, ValueError, OverflowError):
                pass
    # -0.0 flattened to 0.0 is also a sign loss
    if isinstance(native, float) and native == 0 and src_negative:
        fare.sign_lost = True

    # ---- magnitude collapsed (|b|, G6GF 3.4) ---------------------------
    if res.op == "abs" and src_negative:
        fare.magnitude_collapsed = True
        res.notes.append("|b| extracted the magnitude and dropped the sign "
                         "(G6GF 3.4: catching the complex imposters)")

    # ---- the sign bit of -0.0 under |b| (F64 incapacity) ---------------
    if getattr(res, "src_neg_zero", False) and res.op == "abs" \
            and isinstance(native, float) and native == 0:
        fare.sign_lost = True
        fare.magnitude_collapsed = True
        res.notes.append("the sign bit of -0.0 did not survive |b| "
                         "(F64 incapacity: sign of 0 not preserved)")

    # ---- level collision via shared bit pattern (CTS test 3) ----------
    if outcome.wrapped and src_negative and tgt_node.id == "N64":
        fare.level_collision = True
        res.notes.append("level collision: a signed cipher's bit pattern "
                         "re-read as an unsigned cipher (MBP 9.6: levels "
                         "must never share a representation)")

    if native is None:                            # blocked / no value
        fare.exactness = "-"
        return

    # ---- exactness (CTS 4.2, exclusive) --------------------------------
    if marker is not None:
        # A value returning from the complex plane into a real
        # environment: the rendered magnitude may itself be exact, but
        # the true value (with its phase) is not representable here.
        fare.exactness = "A"
        res.error = ErrorMetrics(abs_exact="0", abs_decimal="0", rel="0")
        res.notes.append("the phase lost on return from the complex plane "
                         "is the fare (P); it is not measurable as a "
                         "distance")
    elif exact_equals_target(exact, native):
        fare.exactness = "E"
    elif fare.overflow or fare.underflow:
        fare.exactness = "A"
    elif isinstance(exact, Sqrt):
        fare.exactness = "A"
        res.notes.append("irrational value forced into a finite "
                         "representation (approximated)")
    elif isinstance(exact, Cplx):
        fare.exactness = "A"
    elif outcome.truncated or outcome.wrapped:
        fare.exactness = "T"
    else:
        fare.exactness = "R"

    # ---- error metrics --------------------------------------------------
    if fare.exactness == "E":
        res.error = ErrorMetrics(abs_exact="0", abs_decimal="0", rel="0",
                                 ulp="0", ulp_bound_ok=True)
    elif marker is not None:
        pass                                   # already set above
    elif isinstance(exact, Rational):
        try:
            res.error = _metrics_rational(exact.frac, native)
        except (TypeError, ValueError, OverflowError):
            res.error = ErrorMetrics()
    elif isinstance(exact, Sqrt):
        try:
            res.error = _metrics_irrational(exact, native)
        except (TypeError, ValueError, OverflowError):
            res.error = ErrorMetrics()
    else:
        # A complex value hailing back to a real environment: what
        # rendered is the magnitude, and it may be exact; the lost phase
        # is the fare (P) and is not measurable as a distance.
        res.error = ErrorMetrics(abs_exact="0", abs_decimal="0", rel="0")
        res.notes.append("error metrics are measured against the rendered "
                         "magnitude; the lost phase is not measurable as "
                         "a distance")
