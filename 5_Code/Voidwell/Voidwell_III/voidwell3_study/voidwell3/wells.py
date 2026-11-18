"""wells.py -- the PUBLIC well schedule of Voidwell-3: the prime
skeleton (the Primes Spine, D2 of the V3 investigation).

Voidwell-2 placed its wells at pi's opening digits.  Voidwell-3
places them at the first four primes, and lets the same primes
direct them:

    positions 2, 3, 5, 7     digit targets 2, 3, 5, 7

Four wells for four perspectives (perspectives.py): well j sits at
the j-th prime and nullifies the j-th prime's octal digit.  The
schedule is public, fixed, and nothing-up-my-sleeve -- the primes
are the monograph's own subject matter (the Fare Algebra is
prime-indexed), and the skeleton carries the identity of the
construction.

THE INVOLUTION EXPONENT e (the spectral involution, made a public
parameter).  The monograph's Fare Algebra defines the spectral
involution iota_s(tau_n) = n^(1-2s) tau_n, whose zeta element Z(s)
is FIXED exactly when s = 1/2 (Theorem 4.1.1.7 -- verified
numerically in the V3 investigation: the deviation scan vanishes at
s = 1/2 and nowhere else).  Voidwell-3 publishes the integer
exponent

    e = 1 - 2s   (mod p-1)

and scales the j-th well's prime into its derivation domains as
n_j^e mod p.  At the critical value s = 1/2 the exponent is e = 0
and every scaling n_j^0 = 1 is trivial -- the involution is the
identity, the monograph's fixed point, visible as a parameter of
the artifact.  The default challenge uses e = 1 (s = 0).
"""
from __future__ import annotations

import hashlib

from ucq.lift import Profile

#: the prime skeleton: the j-th well at position p_j, nullifying
#: digit p_j -- the first four primes place AND direct
PRIMES = [2, 3, 5, 7]
WELLS_FULL = list(zip(PRIMES, PRIMES))     # [(2,2),(3,3),(5,5),(7,7)]

#: the small model runs the SAME constants (its 8 one-bit digits
#: accommodate the prime digit targets 2,3,5,7)
WELLS_TOY = list(zip(PRIMES, PRIMES))

L_FULL = 43
L_TOY = 10
K = 4

#: default public exponent (s = 0); e = 0 is the critical setting
DEFAULT_E = 1


def wells_for(pro: Profile, L: int, k: int | None = None) \
        -> list[tuple[int, int]]:
    """The public well list for a profile/path length.  k trims the
    list (the small-model harness varies k); k = 0 is the empty
    schedule (the collapse demonstration)."""
    base = WELLS_FULL if pro.size == 4 else WELLS_TOY
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


def prime_scaling(pro: Profile, j: int, e: int) -> int:
    """n_j^e mod p -- the spectral involution's scale on the j-th
    prime, entering the checkpoint and well-matrix derivation
    domains.  At e = 0 every scaling is 1 (the fixed point)."""
    if not 1 <= j <= len(PRIMES):
        raise ValueError(f"well index {j} outside 1..{len(PRIMES)}")
    if not 0 <= e < pro.p - 1:
        raise ValueError(f"exponent e={e} outside 0..p-2")
    return pow(PRIMES[j - 1], e, pro.p)


def serialize(wells: list[tuple[int, int]], e: int) -> bytes:
    out = bytearray(b"\x03")
    out.append(len(wells))
    for m, n in wells:
        out += m.to_bytes(2, "big")
        out.append(n)
    out += e.to_bytes(2, "big")
    return bytes(out)


def digest(wells: list[tuple[int, int]], e: int) -> str:
    return hashlib.sha256(serialize(wells, e)).hexdigest()


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


__all__ = ["PRIMES", "WELLS_FULL", "WELLS_TOY", "L_FULL", "L_TOY",
           "K", "DEFAULT_E", "wells_for", "validate", "prime_scaling",
           "serialize", "digest", "parse"]
