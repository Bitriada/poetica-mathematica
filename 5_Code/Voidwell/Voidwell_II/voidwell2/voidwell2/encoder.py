"""encoder.py -- the Voidwell-2 encoder (design study, section 6).

`run_path` is the single deterministic code path shared by the
encoder, the gate, the small-model harness and the attacker
package -- the full model and the small model call the same
function with their Profile.

TWO DESIGN FACTS CARRY THE SECURITY ACCOUNTING:

  1. FULL-WIDTH NULLIFIERS.  Each well commits the whole
     conversion:
         N_j = SHA256(ser(D') || serialize(M Q M^-1))
     -- a 27 + 4096-bit preimage domain (2^4123).  The nullifier
     records the FULL conjugated matrix, not its 27-bit shadow;
     each well binds at least 256 bits (hash-capped), so ONE well
     already saturates a 256-bit seed, and there are three.

  2. H-ONLY PUBLICATION.  The challenge publishes H and the public
     parameters -- nothing per-well, no schedule, no intermediate
     values.  With nothing to match against, every wrong seed
     costs a FULL replay: no dictionaries, no preimage targets,
     no early abort (the gate enforces the surface; see gate.py).

PIPELINE:

  D_0 = prf_digivector(seed, "D0")
  h   = SHA256(IV || ser(D_0))
  for i in 1..L:
      if i is well position m_j (PUBLIC):
          Q  = lift(D);  Q' = M_j Q M_j^{-1}
          D' = project(Q')            (digit n_j of D' is 0 -- emergent)
          N_j = SHA256(ser(D') || Q'.serialize())     <-- fact 1
          D  = C_j                    (checkpoint restart)
      else:
          D  = base_step(D, block_i)  (fare-octal transition, R3)
      h = SHA256(h || ser(D))
  H = SHA256(h || ser(N_1..N_k) || ser(D_L) || wells_digest)

The key is the seed ALONE: D_0, C_1..C_3 and M_1..M_3 are all
PRF(seed); the wells are public constants (wells.py).  The fare
ledger (sec. 8.5) is returned for the UC-polynomial laws.
"""
from __future__ import annotations

import hashlib

from ucq.conjugate import conjugate
from ucq.lift import Profile, lift, project
from ucq.matrix import SingularMatrix
from voidwell2 import prf, wells as wells_mod

IV = b"voidwell-v2"          # public domain-separation IV
SER_VERSION = 2

#: the two variants (design study Table 3): same construction, the
#: seed width is the only difference; security = min(seed bits, 256)
VARIANTS = {
    "flagship": {"seed_bytes": 32, "seed_bits": 256,
                 "claim": "min(256, 256) = 2^256"},
    "compact": {"seed_bytes": 16, "seed_bits": 128,
                "claim": "min(128, 256) = 2^128"},
}


class EncodingError(RuntimeError):
    pass


# -- serialization --------------------------------------------------------
def ser_state(state: int) -> bytes:
    """Canonical digivector serialization: version + 4-byte BE int."""
    return bytes([SER_VERSION]) + state.to_bytes(4, "big")


def ser_nullifiers(nullifiers: list[str]) -> bytes:
    out = bytearray(bytes([SER_VERSION, len(nullifiers)]))
    for n in nullifiers:
        out += bytes.fromhex(n)
    return bytes(out)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# -- the base transition (R3) ----------------------------------------------
def base_step(pro: Profile, state: int, block: int) -> tuple[int, int]:
    """One fare-octal transition; returns (state', fare)."""
    n_switches = pro.n_bits
    op = block % 3
    if op == 0:                                   # union-or-annihilate
        g = (block >> 2) % n_switches
        if state & (1 << g):
            n = (block >> 3) % pro.n_digits
            v = (block >> 6) & pro.digit_max
            return digit_set(pro, state, n, v), 1
        return state | (1 << g), 0
    if op == 1:                                   # burn a slot
        n = (block >> 2) % pro.n_digits
        shift = pro.bits_per_digit * n
        mask = pro.digit_max << shift
        return state & ~mask, 1
    # op == 2: write a slot
    n = (block >> 2) % pro.n_digits
    v = (block >> 5) & pro.digit_max
    return digit_set(pro, state, n, v), 1


def digit_set(pro: Profile, state: int, n: int, v: int) -> int:
    shift = pro.bits_per_digit * n
    mask = pro.digit_max << shift
    return (state & ~mask) | (v << shift)


def digit_value(pro: Profile, state: int, n: int) -> int:
    return (state >> (pro.bits_per_digit * n)) & pro.digit_max


def block_at(data: bytes, i: int) -> int:
    return data[(i - 1) % len(data)] if data else 0


# -- the core ------------------------------------------------------------
def run_path(pro: Profile, data: bytes, seed: bytes,
             wells: list[tuple[int, int]], L: int,
             collect: bool = False):
    """Replay the full path.  Returns (H, h_L, nullifiers, D_L) and,
    with collect=True, the (values, fares) fare ledger for the
    UC-polynomial measurements."""
    wells_mod.validate(pro, wells, L)
    k = len(wells)
    well_at = {m: (j + 1, n) for j, (m, n) in enumerate(wells)}

    D = prf.prf_digivector(pro, seed, b"D0")
    Cs = {}
    for m, (j, n) in well_at.items():
        Cs[j] = prf.prf_digivector(pro, seed, bytes([0x43, j]))
    # (checkpoint domain "C<j>"; matrices are derived lazily at the
    #  well, after the arriving state is known -- R2)

    h = hashlib.sha256(IV + ser_state(D)).digest()
    nullifiers: list[str] = []
    values, fares = [D], []
    for i in range(1, L + 1):
        if i in well_at:
            j, n = well_at[i]
            try:
                M, _ctr = prf.prf_well_matrix(pro, seed, j, D, n)
            except SingularMatrix as e:                       # pragma
                raise EncodingError(f"well {j}: {e}")
            Qp = conjugate(lift(pro, D), M)
            Dp = project(pro, Qp)
            if digit_value(pro, Dp, n) != 0:                  # pragma
                raise EncodingError(
                    f"well {j}: nullification failed (derivation bug)")
            # the nullifier records the FULL conversion -- the
            # 27-bit projected state AND the whole 4096-bit
            # conjugated matrix (preimage domain 2^4123)
            nullifiers.append(sha(ser_state(Dp) + Qp.serialize()))
            fare = digit_value(pro, D, n)      # the burned slot's weight
            D = Cs[j]
            fares.append(fare)
        else:
            D, fare = base_step(pro, D, block_at(data, i))
            fares.append(fare)
        h = hashlib.sha256(h + ser_state(D)).digest()
        values.append(D)
    wells_digest = wells_mod.digest(wells)
    H = hashlib.sha256(
        h + ser_nullifiers(nullifiers)
        + ser_state(D) + bytes.fromhex(wells_digest)).digest()
    out = (H.hex(), h.hex(), nullifiers, D)
    return (out[0], out[1], out[2], out[3], values, fares) if collect \
        else out


# -- the encoder ----------------------------------------------------------
def encode(pro: Profile, data: bytes, seed: bytes, L: int,
           variant: str, wells: list[tuple[int, int]] | None = None):
    """Returns (challenge_dict, key_dict, detail).

    The key is the seed alone; the wells default to the public
    pi-skeleton constants for the profile (wells.py).
    """
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}")
    n_bytes = VARIANTS[variant]["seed_bytes"]
    if len(seed) != n_bytes:
        raise ValueError(f"variant {variant} requires a "
                         f"{n_bytes}-byte seed (got {len(seed)})")
    if wells is None:
        wells = wells_mod.wells_for(pro, L)
    else:
        wells = wells_mod.validate(pro, wells, L)
    H, h_L, nullifiers, D_L = run_path(pro, data, seed, wells, L)
    challenge = {
        "version": 2,
        "params": {
            "p": f"{pro.p:x}",
            "L": L,
            "k": len(wells),
            "hash": "sha256",
            "lift_version": 1,
            "digits": pro.n_digits,
            "bits_per_digit": pro.bits_per_digit,
            "variant": variant,
            "seed_bits": VARIANTS[variant]["seed_bits"],
            "wells": [[m, n] for m, n in wells],
        },
        "H": H,
        "data": data.hex(),
        "data_commitment": sha(data),
        "nullifier_count": len(nullifiers),
        # nothing else: no schedule digest (no secret schedule
        # exists), no nullifier list (they live only inside H).
        # The gate rejects any challenge that publishes more.
    }
    key = {"version": 2, "variant": variant, "seed": seed.hex()}
    detail = {"h_L": h_L, "nullifiers": nullifiers, "D_L": D_L}
    return challenge, key, detail


__all__ = ["IV", "SER_VERSION", "VARIANTS", "EncodingError",
           "ser_state", "ser_nullifiers", "sha", "base_step",
           "digit_set", "digit_value", "block_at", "run_path", "encode"]
