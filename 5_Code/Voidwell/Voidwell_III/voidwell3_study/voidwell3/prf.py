"""prf.py -- the seed-derived stream: scalars by SHA-256, matrices by
a packed XOF (the D6 speed work).

Voidwell-2 derived every matrix entry with its own SHA-256 call (16
per 4x4 candidate; the measured replay spent 472 PRF calls).  V3
packs a whole candidate matrix out of ONE SHAKE-256 stream:

    stream = SHAKE256(domain || seed || j || ctr || scale)
    entry  = next 32-byte chunk, reduced mod p

Deterministic, seed-derived, and one XOF call per candidate instead
of sixteen hashes.  The rejection loop keeps Voidwell-2's emergent
nullification (draw until the conjugation nullifies the target
digit, resolution R2) but now:

  * computes the candidate inverse ONCE (adjugate -- a single pow),
  * reuses it for the nullification test AND, on acceptance, hands
    it to the encoder so the kept conjugation is not recomputed,

which removes the double work the V2 profile exposed (the accepted
candidate's conjugation was rebuilt from scratch inside the walk).
"""
from __future__ import annotations

import hashlib

from ucq.conjugate import conjugate, trace_digit
from ucq.lift import Profile, lift
from ucq.matrix import FpMatrix, SingularMatrix

_WELL_DOMAIN_MAX_TRIES = 10_000
_ENTRY_BYTES = 32


def _prf_bytes(seed: bytes, domain: bytes, *indices: int) -> bytes:
    """Scalar derivations stay on SHA-256 (unchanged from V2)."""
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


def xof_matrix(pro: Profile, seed: bytes, domain: bytes, j: int,
               ctr: int, scale: int) -> FpMatrix:
    """A candidate matrix from ONE SHAKE-256 call: ceil(n^2 * 32 / 32)
    32-byte chunks, reduced mod p.  `scale` is the involution
    scaling n_j^e mod p (wells.py), folded into the stream so the
    public exponent parameterizes the derivation."""
    h = hashlib.shake_256()
    h.update(len(seed).to_bytes(1, "big"))
    h.update(seed)
    h.update(domain)
    h.update(j.to_bytes(4, "big"))
    h.update(ctr.to_bytes(4, "big"))
    h.update(scale.to_bytes(32, "big"))
    stream = h.digest(_ENTRY_BYTES * pro.size * pro.size)
    words = [int.from_bytes(
        stream[i * _ENTRY_BYTES:(i + 1) * _ENTRY_BYTES], "big") % pro.p
        for i in range(pro.size * pro.size)]
    rows = [words[r * pro.size:(r + 1) * pro.size]
            for r in range(pro.size)]
    return FpMatrix(rows, pro.p)


def prf_well_matrix(pro: Profile, seed: bytes, j: int, state: int,
                    digit: int, scale: int,
                    twist=None) -> tuple[FpMatrix, FpMatrix, int]:
    """The j-th well matrix: rejection-sample candidates until the
    conjugation (through the perspective twist) nullifies `digit`.

    Returns (M, Minv, ctr): the matrix, its inverse (reused by the
    encoder for the kept conjugation), and the rejection counter
    (the issuer-side effort, invisible in H).
    """
    Q = lift(pro, state)
    TQ = twist(Q) if twist is not None else Q
    for ctr in range(_WELL_DOMAIN_MAX_TRIES):
        M = xof_matrix(pro, seed, b"M", j, ctr, scale)
        try:
            Minv = M.adjugate_inverse()
        except SingularMatrix:
            continue
        if trace_digit(pro, conjugate(TQ, M, Minv), digit) == 0:
            return M, Minv, ctr
    raise RuntimeError(
        f"well {j}: no nullifying matrix in "
        f"{_WELL_DOMAIN_MAX_TRIES} tries (probability < 2^-130)")


__all__ = ["prf_digivector", "xof_matrix", "prf_well_matrix"]
