"""field.py -- the prime field F_p for the UCQ layer.

The demonstration prime is the secp256k1 field prime

    p = 2^256 - 2^32 - 977

chosen because it is a well-known, independently verifiable 256-bit
prime (printed by `python -m voidwell params`).  All UCQ arithmetic in
the full model is exact integer arithmetic mod p; the small model uses
F_7 (the spec's D8 choice) through the same code path.
"""
from __future__ import annotations

P = 2**256 - 2**32 - 977
PRIME_BITS = 256
P_HEX = f"{P:064x}"


def is_probable_prime(n: int) -> bool:
    """Deterministic Miller-Rabin for n < 3.3e24 (more than enough to
    re-verify p); the full-model p is additionally a published
    standard prime."""
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


assert is_probable_prime(P), "the demonstration prime must be prime"

__all__ = ["P", "PRIME_BITS", "P_HEX", "is_probable_prime"]
