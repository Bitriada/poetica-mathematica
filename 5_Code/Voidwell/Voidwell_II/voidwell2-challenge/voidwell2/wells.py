"""wells.py -- the PUBLIC well schedule: the pi-skeleton (design
study, idea A as built).

Voidwell-2 has no schedule secret.  The wells sit at pi's own opening
digits, fixed constants of the spec:

    full model (L = 43):   positions 3, 14, 15   digits 3, 1, 4
                            (pi = 3.1415... -- the first six digits
                             place and direct the three wells)
    small model (L = 8):   positions 1, 3, 4     digits 0, 1, 2
                            (pi = 3.14, digits folded into 0..2)

Why public is not just safe but REQUIRED (design study section
4.2): once the challenge publishes nothing per-well, an attacker's
search is over seeds; secret positions would buy exactly 0 bits.
Public constants have nothing to preimage, are
nothing-up-my-sleeve by construction, and make the challenge's
public surface minimal.

The digest() of the well list is folded into H purely as domain
separation (it is a public constant; committing it reveals nothing).
"""
from __future__ import annotations

import hashlib

from ucq.lift import Profile

#: full model: pi's 3.1415 as (position, digit) pairs -- the three
#: algebras sit at steps 3, 14 and 15 and nullify octal digits 3, 1, 4
WELLS_FULL = [(3, 3), (14, 1), (15, 4)]

#: small model: pi's 3.14 folded into L = 8 and digits 0..2
WELLS_SMALL = [(1, 0), (3, 1), (4, 2)]

#: spec-fixed parameters (the user decision: "Fixed 43")
L_FULL = 43
K_FULL = 3


def wells_for(pro: Profile, L: int, k: int | None = None) \
        -> list[tuple[int, int]]:
    """The public well list for a profile/path length.  k trims the
    list to its first k wells (used by the small-model harness to
    vary k); k = 0 gives the empty schedule."""
    if pro.size == 4:
        base = WELLS_FULL
    else:
        base = WELLS_SMALL
    wells = [w for w in base if w[0] <= L]
    if k is None:
        k = len(wells)
    if k > len(wells):
        raise ValueError(f"k={k} exceeds the {len(wells)} skeleton "
                         f"wells inside L={L}")
    return wells[:k]


def validate(pro: Profile, wells: list[tuple[int, int]], L: int
             ) -> list[tuple[int, int]]:
    """Structural validation: positions strictly increasing in 1..L,
    digits in range."""
    out = [(int(m), int(n)) for m, n in wells]
    if len({m for m, _ in out}) != len(out):
        raise ValueError("well positions must be distinct")
    prev = 0
    for m, n in out:
        if not 1 <= m <= L:
            raise ValueError(f"well position {m} outside 1..{L}")
        if m <= prev:
            raise ValueError("well positions must be strictly "
                             "increasing")
        pro.check_digit(n)
        prev = m
    return out


def serialize(wells: list[tuple[int, int]]) -> bytes:
    out = bytearray(b"\x02")
    out.append(len(wells))
    for m, n in wells:
        out += m.to_bytes(2, "big")
        out.append(n)
    return bytes(out)


def digest(wells: list[tuple[int, int]]) -> str:
    return hashlib.sha256(serialize(wells)).hexdigest()


def parse(obj) -> list[tuple[int, int]]:
    """From JSON (list of 2-lists) with light validation."""
    if not isinstance(obj, list):
        raise ValueError("wells must be a list")
    out = []
    for pair in obj:
        if (not isinstance(pair, list) or len(pair) != 2
                or not all(isinstance(x, int) for x in pair)):
            raise ValueError("wells entries must be [m, n] ints")
        out.append((pair[0], pair[1]))
    return out


__all__ = ["WELLS_FULL", "WELLS_SMALL", "L_FULL", "K_FULL", "wells_for",
           "validate", "serialize", "digest", "parse"]
