"""schedule.py -- the well schedule: canonical form and digest.

A schedule is [(m_1, n_1), ..., (m_k, n_k)]: well positions m_j
(steps 1..L, strictly increasing) and digits n_j (0..n_digits-1).

Canonical serialization (schedule_digest): version byte, k, then the
pairs big-endian.  The digest is PUBLIC (in the challenge); by SHA-256
preimage resistance it commits the schedule without revealing it.
"""
from __future__ import annotations

import hashlib

from ucq.lift import Profile


def validate(pro: Profile, schedule: list[tuple[int, int]], L: int
             ) -> list[tuple[int, int]]:
    """Structural validation: positions strictly increasing in 1..L,
    digits in range, k consistent."""
    sched = [(int(m), int(n)) for m, n in schedule]
    if len({m for m, _ in sched}) != len(sched):
        raise ValueError("well positions must be distinct")
    prev = 0
    for m, n in sched:
        if not 1 <= m <= L:
            raise ValueError(f"well position {m} outside 1..{L}")
        if m <= prev:
            raise ValueError("well positions must be strictly "
                             "increasing")
        pro.check_digit(n)
        prev = m
    return sched


def serialize(schedule: list[tuple[int, int]]) -> bytes:
    out = bytearray(b"\x01")
    out.append(len(schedule))
    for m, n in schedule:
        out += m.to_bytes(2, "big")
        out.append(n)
    return bytes(out)


def digest(schedule: list[tuple[int, int]]) -> str:
    return hashlib.sha256(serialize(schedule)).hexdigest()


def parse(obj) -> list[tuple[int, int]]:
    """From JSON (list of 2-lists) with light validation."""
    if not isinstance(obj, list):
        raise ValueError("schedule must be a list")
    out = []
    for pair in obj:
        if (not isinstance(pair, list) or len(pair) != 2
                or not all(isinstance(x, int) for x in pair)):
            raise ValueError("schedule entries must be [m, n] ints")
        out.append((pair[0], pair[1]))
    return out


__all__ = ["validate", "serialize", "digest", "parse"]
