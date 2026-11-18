"""prf.py -- seed derivation: everything secret comes from one seed.

Domain-separated SHA-256 (spec D4):

    prf_digivector(seed, domain, data) -> initial/checkpoint state
    prf_matrix(profile, seed, domain, j, ctr, state, digit)
        -> the j-th well matrix, rejection-sampled until (a) invertible
           and (b) its conjugation of `state` nullifies `digit`
           (resolution R2: the nullification is EMERGENT, so the gate's
           structural audit is a real filter: a wrong matrix fails it
           with probability 1 - 2^-bits_per_digit)
    prf_schedule(seed, L, k) -> sorted distinct well positions (1..L)
           and digits (0..n_digits-1)

Determinism: pure hashlib, no process state -- same (seed, domain, j)
gives the same output across runs and processes (D4 acceptance).
"""
from __future__ import annotations

import hashlib

from ucq.conjugate import conjugation_nullifies
from ucq.lift import Profile
from ucq.matrix import FpMatrix, SingularMatrix

_WELL_DOMAIN_MAX_TRIES = 10_000


def _prf_bytes(seed: bytes, domain: bytes, *indices: int) -> bytes:
    h = hashlib.sha256()
    h.update(len(seed).to_bytes(1, "big"))
    h.update(seed)
    h.update(domain)
    for i in indices:
        h.update(i.to_bytes(4, "big"))
    return h.digest()


def prf_digivector(pro: Profile, seed: bytes, domain: bytes,
                   data: bytes = b"") -> int:
    """A state in 0..2^n_bits-1 from the PRF."""
    raw = _prf_bytes(seed, domain, 0) + _prf_bytes(seed, domain, 1, 0)
    n = int.from_bytes(raw, "big")
    return n % (1 << pro.n_bits)


def _matrix_words(seed: bytes, domain: bytes, j: int, ctr: int, r: int):
    """Infinite stream of PRF words for entry r of matrix (j, ctr)."""
    while True:
        yield int.from_bytes(
            _prf_bytes(seed, domain, j, ctr, r), "big")
        r += 1


def prf_matrix(pro: Profile, seed: bytes, j: int, ctr: int) -> FpMatrix:
    """A PRF matrix (invertibility NOT yet checked)."""
    words = []
    for r in range(pro.size * pro.size):
        it = _matrix_words(seed, b"M", j, ctr, r)
        words.append(next(it))
    rows = [words[r * pro.size:(r + 1) * pro.size]
            for r in range(pro.size)]
    return FpMatrix(rows, pro.p)


def prf_well_matrix(pro: Profile, seed: bytes, j: int, state: int,
                    digit: int) -> tuple[FpMatrix, int]:
    """The j-th well matrix: rejection-sample PRF counters until the
    matrix is invertible AND its conjugation of `state` nullifies
    `digit`.  Returns (matrix, ctr) -- ctr is part of the derivation,
    the gate replays identically."""
    for ctr in range(_WELL_DOMAIN_MAX_TRIES):
        M = prf_matrix(pro, seed, j, ctr)
        try:
            if conjugation_nullifies(pro, state, M, digit):
                return M, ctr
        except SingularMatrix:
            continue
    raise RuntimeError(
        f"well {j}: no nullifying matrix in "
        f"{_WELL_DOMAIN_MAX_TRIES} tries (probability < 2^-130)")


def prf_schedule(pro: Profile, seed: bytes, L: int, k: int,
                 rng_domain: bytes = b"S") -> list[tuple[int, int]]:
    """k distinct well positions in 1..L and digits in 0..n_digits-1,
    sorted by position.  Draw without replacement by PRF stream."""
    positions: list[int] = []
    digits: list[int] = []
    pool = list(range(1, L + 1))
    ctr = 0
    while len(positions) < k:
        raw = _prf_bytes(seed, rng_domain, ctr)
        n = int.from_bytes(raw, "big")
        ctr += 1
        idx = n % len(pool)
        positions.append(pool.pop(idx))
        digits.append((n >> 16) % pro.n_digits)
    order = sorted(range(k), key=lambda t: positions[t])
    sched = [(positions[t], digits[t]) for t in order]
    return sched


__all__ = ["prf_digivector", "prf_matrix", "prf_well_matrix",
           "prf_schedule"]
