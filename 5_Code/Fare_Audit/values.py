"""rtfa.values -- the exact value model shared by engine and classifier.

(The CTS module list is registry/engine/classifier/ledger/report/cli;
this module is the exact-arithmetic core factored out of the engine so
that the classifier can use it without a circular import.)

Everything here is exact: rationals as ``fractions.Fraction``, irrational
square roots carried symbolically, complexes as exact component pairs.
Approximation happens only in ``sqrt_decimal`` (a 60-digit evaluation
used for *error metrics* against irrational values -- never for
classification decisions, which stay exact).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Union

from . import registry


# ---------------------------------------------------------------------------
# Value types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Rational:
    """An exact rational number."""
    frac: Fraction

    @property
    def is_rational(self) -> bool:
        return True


@dataclass(frozen=True)
class Sqrt:
    """The exact square root of a positive rational that is not a
    perfect square -- irrational, approximated on demand only."""
    rad: Fraction

    @property
    def is_rational(self) -> bool:
        return False


@dataclass(frozen=True)
class Cplx:
    """An exact complex number; components are Rational or Sqrt."""
    re: Union[Rational, Sqrt]
    im: Union[Rational, Sqrt]

    @property
    def is_rational(self) -> bool:
        return False


EVal = Union[Rational, Sqrt, Cplx]


# ---------------------------------------------------------------------------
# Exact algebra
# ---------------------------------------------------------------------------

def is_perfect_square(fr: Fraction) -> bool:
    p, q = fr.numerator, fr.denominator          # Fraction is reduced
    if p < 0:
        return False
    rp, rq = math.isqrt(p), math.isqrt(q)
    return rp * rp == p and rq * rq == q


def sqrt_exact(v: EVal) -> EVal:
    """Exact square root: rational, irrational, or exact complex."""
    if isinstance(v, Rational):
        if v.frac < 0:
            inner = sqrt_exact(Rational(-v.frac))
            return Cplx(re=Rational(Fraction(0)), im=inner)
        if is_perfect_square(v.frac):
            return Rational(Fraction(math.isqrt(v.frac.numerator),
                                     math.isqrt(v.frac.denominator)))
        return Sqrt(v.frac)
    if isinstance(v, Sqrt):
        # sqrt(sqrt(r)) is not rational for our operands; carry it as an
        # irrational whose radicand is the nested root.
        return Sqrt(Fraction(0)) if v.rad == 0 else Sqrt(v.rad)
    if isinstance(v, Cplx):
        raise ValueError("sqrt of an exact complex is out of scope in v1")
    raise TypeError(v)


def exact_to_float(v: EVal) -> float:
    if isinstance(v, Rational):
        try:
            return float(v.frac)                 # correctly rounded (RNE)
        except OverflowError:
            # a rational beyond the binary64 range overflows to +-inf,
            # exactly as IEEE 754 prescribes (to_infinity)
            return math.inf if v.frac > 0 else -math.inf
    if isinstance(v, Sqrt):
        return float(sqrt_decimal(v.rad))
    if isinstance(v, Cplx):
        return exact_to_float(v.re)
    raise TypeError(v)


def exact_magnitude(v: EVal) -> EVal:
    """|v| exactly -- the |b| operation (G6GF section 3.4)."""
    if isinstance(v, Rational):
        return Rational(abs(v.frac))
    if isinstance(v, Sqrt):
        return v
    if isinstance(v, Cplx):
        if isinstance(v.re, Sqrt) or isinstance(v.im, Sqrt):
            raise ValueError("magnitude of an irrational complex is not "
                             "exact in v1")
        m2 = v.re.frac ** 2 + v.im.frac ** 2
        if is_perfect_square(m2):
            return Rational(Fraction(math.isqrt(m2.numerator),
                                     math.isqrt(m2.denominator)))
        return Sqrt(m2)
    raise TypeError(v)


def exact_is_negative(v: EVal) -> bool:
    if isinstance(v, Rational):
        return v.frac < 0
    if isinstance(v, Sqrt):
        return False
    if isinstance(v, Cplx):
        return exact_to_float(v) < 0 and exact_to_float(v.im) == 0
    raise TypeError(v)


def exact_equals_target(v: EVal, target_native) -> bool:
    """Exact comparison of the mathematical value against the computed
    target.  Floats and Decimals convert to Fraction without loss, so
    the comparison itself never rounds."""
    if isinstance(v, Rational):
        try:
            return Fraction(target_native) == v.frac
        except (TypeError, ValueError, OverflowError):
            return False
    if isinstance(v, Sqrt):
        return False                              # irrational, never exact
    if isinstance(v, Cplx):
        try:
            c = complex(target_native)
            return (Fraction(c.real) == Fraction(exact_to_float(v.re))
                    and Fraction(c.imag) == Fraction(exact_to_float(v.im)))
        except (TypeError, ValueError, OverflowError):
            return False
    return False


def sqrt_decimal(fr: Fraction) -> Decimal:
    """60-digit decimal evaluation of sqrt(fr) -- error metrics only."""
    with localcontext() as ctx:
        ctx.prec = 60
        return (Decimal(fr.numerator) / Decimal(fr.denominator)).sqrt()


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def fmt_fraction(fr: Fraction) -> str:
    return str(fr.numerator) if fr.denominator == 1 \
        else f"{fr.numerator}/{fr.denominator}"


def fmt_float(f: float) -> str:
    """Honest binary64 display: the exact decimal expansion of the stored
    value, truncated with '...' when long (PDD section 9.1 golden style:
    0.10000000000000000555...)."""
    if math.isnan(f):
        return "nan"
    if math.isinf(f):
        return "+inf" if f > 0 else "-inf"
    if f == 0:
        return "-0.0" if math.copysign(1.0, f) < 0 else "0.0"
    s = str(Decimal(f))
    if "E" in s or "e" in s:
        return s
    if "." not in s:
        s += ".0"
    return s if len(s) <= 24 else s[:22] + "..."


def fmt_decimal(d: Decimal) -> str:
    s = str(d)
    if "." not in s and "E" not in s:
        s += ".0"
    return s


def fmt_exact(v: EVal) -> str:
    if isinstance(v, Rational):
        return fmt_fraction(v.frac)
    if isinstance(v, Sqrt):
        return f"sqrt({fmt_fraction(v.rad)})"
    re_s = fmt_exact(v.re)
    im_s = fmt_exact(v.im)
    if not im_s.startswith("-"):
        im_s = "+" + im_s
    return f"{re_s}{im_s}i"


# ---------------------------------------------------------------------------
# Parsing: "Q:1/10", "Z:-1", "F64:0.1", "BIN:0b11", "ADDR:0x7f3a1c", ...
# ---------------------------------------------------------------------------

def parse_value(spec: str) -> tuple[str, EVal]:
    rep_id, _, rest = spec.partition(":")
    rep_id, rest = rep_id.strip(), rest.strip()
    node = registry.get(rep_id)
    if not node.implemented:
        raise ValueError(f"{rep_id} is declared but not implemented (v2)")
    env = node.g6gf_env
    if rep_id == "BIN":
        return rep_id, Rational(Fraction(int(rest, 0)))
    if env in ("N", "Z"):
        return rep_id, Rational(Fraction(int(rest, 0)))
    if env == "Q":
        return rep_id, Rational(Fraction(rest))
    if rep_id == "F64":
        try:
            f = float(rest)
        except ValueError:
            f = float.fromhex(rest)               # exact round-trip form
        return rep_id, Rational(Fraction(f))
    if rep_id == "D128":
        return rep_id, Rational(Fraction(Decimal(rest)))
    if rep_id == "ADDR":
        return rep_id, Rational(Fraction(int(rest, 0)))
    if env == "C":
        c = complex(rest.replace(" ", ""))
        return rep_id, Cplx(re=Rational(Fraction(c.real)),
                            im=Rational(Fraction(c.imag)))
    raise ValueError(f"cannot parse value spec {spec!r}")


def parse_float_spec(rest: str) -> float:
    """The raw float of an F64 spec (preserves the sign of -0.0)."""
    try:
        return float(rest)
    except ValueError:
        return float.fromhex(rest)


def parse_op(op_spec: str) -> tuple[str, str | None]:
    """'div(2)' -> ('div', '2');   'sqrt' -> ('sqrt', None)."""
    op_spec = op_spec.strip()
    if "(" in op_spec:
        op, _, arg = op_spec.partition("(")
        return op.strip(), arg.strip(" )") or None
    return op_spec, None
