"""field.py -- the prime fields for the UCQ layer of Voidwell-3.

FULL model: the secp256k1 field prime p = 2^256 - 2^32 - 977 (a
well-known, independently verifiable 256-bit prime, unchanged from
Voidwell-2 for continuity).

TOY model: F_257.  The Voidwell-2 small model used F_7, and the V3
pre-design investigation measured why that understates the
construction: conjugation orbits in F_7 are tiny (63-119 distinct
conjugated matrices per well), so the toy's effective binding
saturated near 2^21.  F_257 keeps the toy exhaustively enumerable
(2-byte seeds) while giving GL(2, 257) enough room that orbits no
longer collapse -- the miniature becomes a faithful model.
"""
from __future__ import annotations

P = 2**256 - 2**32 - 977
PRIME_BITS = 256
P_HEX = f"{P:064x}"

P_TOY = 257          # the small-model prime: 2^8 + 1, Fermat


def is_probable_prime(n: int) -> bool:
    """Deterministic Miller-Rabin for n < 3.3e24 (more than enough to
    re-verify both primes)."""
    if n < 2:
        return False
    for sp in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % sp == 0:
            return n == sp
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


assert is_probable_prime(P), "the full-model prime must be prime"
assert is_probable_prime(P_TOY), "the toy prime must be prime"

__all__ = ["P", "PRIME_BITS", "P_HEX", "P_TOY", "is_probable_prime"]
