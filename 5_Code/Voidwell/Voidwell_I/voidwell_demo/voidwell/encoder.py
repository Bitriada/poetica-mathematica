"""encoder.py -- the three-layer encoder (spec D5) and its core.

`run_path` is the single deterministic code path shared by the
encoder, the gate, and the small-model harness (the spec's claim
"everything after it is the same code with larger parameters" is
literal: both models call run_path with their Profile).

PIPELINE (spec Part II, data flow):

  D_0 = prf_digivector(seed, "D0", data)
  h   = SHA256(IV || ser(D_0))
  for i in 1..L:
      if i is well position m_j:
          Q  = lift(D)                       # fare-octal -> UCQ
          Q' = M_j @ Q @ M_j^{-1}            # non-commutative mixing
          D' = project(Q')                   # UCQ -> fare-octal
          (M_j was rejection-sampled so that digit n_j of D' is 0)
          N_j = SHA256(ser(D'))              # the nullifier
          D  = C_j                           # checkpoint restart
      else:
          D  = base_step(D, block_i)         # fare-octal transition
      h = SHA256(h || ser(D))
  H = SHA256(h || ser(nullifiers) || ser(D_L) || schedule_digest)

BASE TRANSITION (resolution R3, version 1).  block_i = data byte
(i-1) mod len(data); b = block_i selects the operation:

    b % 3 == 0  UNION       D' = D * tau_g, g = (b >> 2) % n_switches;
                             if the product annihilates (shared active
                             switch), fall back to digit_set -- the
                             annihilation is the fare, the slot write
                             records it, the state survives
                             (App. A's Nihilum is never entered)
    b % 3 == 1  DIGIT_ZERO  burn slot n = (b >> 2) % n_digits (fare 1)
    b % 3 == 2  DIGIT_SET   write slot n = (b >> 2) % n_digits to
                             v = (b >> 5) & digit_max (fare 1)

FARE LEDGER (sec. 8.5).  Every step pays a fare (0 for a clean union,
1 for annihilation/burn/write, the nullified digit's weight at a
well).  run_path returns the (values, fares) pair so the UC-polynomial
laws L1/L2 can be verified on real encodings (ucpoly.py).
"""
from __future__ import annotations

import hashlib

from ucq.conjugate import conjugate
from ucq.lift import Profile, lift, project
from ucq.matrix import SingularMatrix
from voidwell import prf, schedule as sched_mod

IV = b"voidwell-v1"          # public domain-separation IV
SER_VERSION = 1


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
            # annihilation: the fare is paid, the slot write records it
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
             schedule: list[tuple[int, int]], L: int,
             collect: bool = False):
    """Replay the full path.  Returns (H, h_L, nullifiers, D_L) and,
    with collect=True, the (values, fares) fare ledger for the
    UC-polynomial measurements."""
    sched_mod.validate(pro, schedule, L)
    k = len(schedule)
    wells = {m: (j + 1, n) for j, (m, n) in enumerate(schedule)}

    D = prf.prf_digivector(pro, seed, b"D0", data)
    Cs = {}
    for m, (j, n) in wells.items():
        Cs[j] = prf.prf_digivector(pro, seed, bytes([0x43, j]), data)
    # (checkpoint domain "C<j>"; matrices are derived lazily at the
    #  well, after the arriving state is known -- R2)

    h = hashlib.sha256(IV + ser_state(D)).digest()
    nullifiers: list[str] = []
    values, fares = [D], []
    for i in range(1, L + 1):
        if i in wells:
            j, n = wells[i]
            try:
                M, _ctr = prf.prf_well_matrix(pro, seed, j, D, n)
            except SingularMatrix as e:                       # pragma
                raise EncodingError(f"well {j}: {e}")
            Dp = project(pro, conjugate(lift(pro, D), M))
            if digit_value(pro, Dp, n) != 0:                  # pragma
                raise EncodingError(
                    f"well {j}: nullification failed (derivation bug)")
            nullifiers.append(sha(ser_state(Dp)))
            fare = digit_value(pro, D, n)      # the burned slot's weight
            D = Cs[j]
            fares.append(fare)
        else:
            D, fare = base_step(pro, D, block_at(data, i))
            fares.append(fare)
        h = hashlib.sha256(h + ser_state(D)).digest()
        values.append(D)
    schedule_digest = sched_mod.digest(schedule)
    H = hashlib.sha256(
        h + ser_nullifiers(nullifiers)
        + ser_state(D) + bytes.fromhex(schedule_digest)).digest()
    out = (H.hex(), h.hex(), nullifiers, D)
    return (out[0], out[1], out[2], out[3], values, fares) if collect \
        else out


# -- the encoder (D5) ------------------------------------------------------
def encode(pro: Profile, data: bytes, seed: bytes, k: int, L: int,
           schedule: list[tuple[int, int]] | None = None):
    """Returns (challenge_dict, key_dict, detail).  The schedule is
    PRF-derived from the seed when not supplied (the honest case)."""
    if len(seed) > 255:
        raise ValueError("seed too long (max 255 bytes)")
    if schedule is None:
        schedule = prf.prf_schedule(pro, seed, L, k)
    else:
        schedule = sched_mod.validate(pro, schedule, L)
        if len(schedule) != k:
            raise ValueError("schedule length does not match k")
    H, h_L, nullifiers, D_L = run_path(pro, data, seed, schedule, L)
    challenge = {
        "version": 1,
        "params": {
            "p": f"{pro.p:x}",
            "L": L,
            "k": k,
            "hash": "sha256",
            "lift_version": 1,
            "digits": pro.n_digits,
            "bits_per_digit": pro.bits_per_digit,
        },
        "H": H,
        "schedule_digest": sched_mod.digest(schedule),
        "data": data.hex(),
        "data_commitment": sha(data),
        "nullifier_count": len(nullifiers),
        # the nullifiers are published (they are one-way digests of
        # secret post-conjugation states; H already commits them) so
        # the gate's nullifier recomputation is an explicit,
        # independently testable check (spec D6 check 4)
        "nullifiers": list(nullifiers),
    }
    key = {"version": 1, "seed": seed.hex(),
           "schedule": [[m, n] for m, n in schedule]}
    detail = {"h_L": h_L, "nullifiers": nullifiers, "D_L": D_L}
    return challenge, key, detail


__all__ = ["IV", "EncodingError", "ser_state", "ser_nullifiers",
           "sha", "base_step", "digit_set", "digit_value",
           "block_at", "run_path", "encode"]
