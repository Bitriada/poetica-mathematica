"""tickkey.py -- the tick-key toy: the family's floor piece (design
study, section 5.3).

The key is a MOMENT IN THE PI-CLOCK'S LIFE: a tick number I*.  The
gate publishes

    H = SHA256("tickkey-v1" || ser(I*) || ser(alpha) || ser(beta)
               || ser(gamma))

where (alpha, beta, gamma) are the pi-clock's three sheets at tick I*
-- the exact discrepancies between the binary, integer and float
bases reading v_I = pi(I-3)/I (the H-trials' live projection,
`LiveHeterobase`, substrate-verified):

    n = PI*(I-3),  d = PI*I            (PI = the 340-digit rational)
    q = (n * 2^53) // d                the 53-bit binary sheet
    B = q / 2^53                       the binary base's reading
    i = n // d                         the integer sheet (the staircase)
    ef = float(n/d), exactly           the double sheet (correctly
                                       rounded, read back exactly)
    alpha = B - i,  beta = i - ef,  gamma = ef - B

The sheets are CLOSED-FORM at any tick, so the honest holder's keygen
is O(1): pick a tick, read the clock's face, hash it.  The attacker
must climb the tick space hashing as they go -- expected work ~I*/2.
The security is log2(I*), exactly, and NOTHING above this toy (the
wells, the conjugations, the fares) adds a single bit to that floor:
they add structure, auditability and narrative.  This exists to keep
that accounting legible.

Precision: the vendored 340-digit pi (pi_const.json, Machin <->
mpmath <-> published prefixes) supports exact sheets for any tick
I < 2^1000 (the constant's own verified envelope; per-tick cost is
O(1) big-rational work).
"""
from __future__ import annotations

import hashlib
import json
import os

from fractions import Fraction

VERSION = 1
VERSION_BYTES = b"tickkey-v1"
SHEET_BITS = 53
_HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_HERE, "pi_const.json")) as _f:
    _c = json.load(_f)
PI = Fraction(int(_c["decimal"].replace(".", "")),
               10 ** _c["digits"])
PI_DIGITS = _c["digits"]
#: the constant's verified envelope (gen_pi_const.py): exact sheets
#: for any tick below this bound
MAX_TICK = 1 << 1000


class TickKeyError(ValueError):
    pass


def sheets(tick: int) -> tuple[Fraction, Fraction, Fraction]:
    """The three sheets at `tick` -- exact, closed-form."""
    if not isinstance(tick, int) or tick < 1:
        raise TickKeyError("tick must be a positive integer")
    if tick >= MAX_TICK:
        raise TickKeyError(f"tick exceeds the constant's exactness "
                           f"envelope (2^1000)")
    if tick <= 3:
        return Fraction(0), Fraction(0), Fraction(0)
    n = PI.numerator * (tick - 3)
    d = PI.denominator * tick
    q = (n << SHEET_BITS) // d
    B = Fraction(q, 1 << SHEET_BITS)
    i = n // d
    ef = Fraction(float(Fraction(n, d)))    # correctly rounded, exact
    return B - i, i - ef, ef - B


def integer_sheet(tick: int) -> int:
    """The staircase register i_I = trunc(pi(I-3)/I) at `tick`."""
    if tick <= 3:
        return 0
    return (PI.numerator * (tick - 3)) // (PI.denominator * tick)


def ser_int(x: int, width: int = 16) -> bytes:
    return x.to_bytes(width, "big", signed=True)


def serialize(tick: int, sh: tuple[Fraction, Fraction, Fraction]) -> bytes:
    out = bytearray(VERSION_BYTES)
    out += ser_int(tick)
    for f in sh:
        out += ser_int(f.numerator)
        out += ser_int(f.denominator)
    return bytes(out)


def H_for_tick(tick: int) -> str:
    return hashlib.sha256(serialize(tick, sheets(tick))).hexdigest()


def keygen(tick: int) -> tuple[dict, dict]:
    """(challenge, key) at a given tick."""
    if not 1 <= tick < MAX_TICK:
        raise TickKeyError("tick outside 1..2^1000")
    challenge = {
        "version": VERSION,
        "params": {
            "sheet_bits": SHEET_BITS,
            "pi_digits": PI_DIGITS,
            "max_tick_log2": 1000,
        },
        "H": H_for_tick(tick),
    }
    key = {"version": VERSION, "tick": tick}
    return challenge, key


def gate(challenge: dict, key: dict) -> bool:
    """True iff the key's tick produces the challenge's H."""
    if challenge.get("version") != VERSION or \
            key.get("version") != VERSION:
        return False
    tick = key.get("tick")
    if not isinstance(tick, int) or not 1 <= tick < MAX_TICK:
        return False
    import hmac as _hmac
    return _hmac.compare_digest(H_for_tick(tick),
                                challenge.get("H", ""))


#: the published demonstration tick: pi's first ten digits as an
#: integer -- security log2(3141592653) = 31.55 bits (a toy)
DEMO_TICK = 3141592653


def demo() -> dict:
    """The published demo round trip; returns a small record."""
    challenge, key = keygen(DEMO_TICK)
    ok = gate(challenge, key)
    alpha, beta, gamma = sheets(DEMO_TICK)
    return {
        "tick": DEMO_TICK,
        "H": challenge["H"],
        "gate": "PASS" if ok else "FAIL",
        "security_log2": DEMO_TICK.bit_length() - 1,
        "telescope_exact": alpha + beta + gamma == 0,
        "integer_sheet": integer_sheet(DEMO_TICK),
    }


__all__ = ["VERSION", "SHEET_BITS", "PI", "PI_DIGITS", "MAX_TICK",
           "TickKeyError", "sheets", "integer_sheet", "serialize",
           "H_for_tick", "keygen", "gate", "DEMO_TICK", "demo"]
