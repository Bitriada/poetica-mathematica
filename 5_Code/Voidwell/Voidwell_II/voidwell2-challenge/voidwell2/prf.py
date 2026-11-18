"""prf.py -- seed derivation: everything secret comes from one seed.

Voidwell-2 (design study, DR3): the KEY IS THE SEED ALONE.  There is
no schedule secret -- the wells sit at PUBLIC pi-skeleton constants
(wells.py) -- so the PRF derives exactly three kinds of material:

    prf_digivector(seed, domain)  -> initial state D_0 and the
                                     checkpoints C_1..C_3
    prf_matrix(profile, seed, j, ctr) -> the j-th well matrix
    prf_well_matrix(...)          -> rejection-sampled until (a)
                                     invertible and (b) its
                                     conjugation of the ARRIVING state
                                     nullifies the well's public digit
                                     (the nullification is EMERGENT --
                                     the gate's structural audit is a
                                     real filter, not a tautology)

Domain-separated SHA-256 (the seed-length prefix byte makes
16-byte compact and 32-byte flagship seeds flow through the same
derivation).  Determinism: pure hashlib, no process state.
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


def prf_digivector(pro: Profile, seed: bytes, domain: bytes) -> int:
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
    `digit`.  Returns (matrix, ctr)."""
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


__all__ = ["prf_digivector", "prf_matrix", "prf_well_matrix"]
