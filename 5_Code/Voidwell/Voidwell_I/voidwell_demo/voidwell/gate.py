"""gate.py -- verification with the three checks of spec D6.

Exit codes: PASS=0, FAIL=1, MALFORMED=2.

Checks, in order:
  1. Schema: both JSONs parse, versions match, k matches
     nullifier_count, data commitment matches the public data.
  2. Replay: recompute the path from (seed, schedule) -- the same
     run_path code path as the encoder (bit-identical by
     construction, not by re-implementation).
  3. Structural audit at each well: digit n_j of the conjugated,
     projected digivector is 0 (built into run_path; a wrong matrix
     fails here with probability 1 - 2^-bits_per_digit BEFORE any
     hash comparison).
  4. Nullifier recomputation + 5. binding: H compared in constant
     time (hmac.compare_digest).
"""
from __future__ import annotations

import hashlib
import hmac
import json

from ucq.lift import Profile
from voidwell import schedule as sched_mod
from voidwell.encoder import EncodingError, run_path, sha

PASS, FAIL, MALFORMED = 0, 1, 2


class Malformed(Exception):
    pass


def _load(path: str) -> dict:
    try:
        with open(path) as f:
            obj = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise Malformed(f"cannot parse {path}: {e}")
    if not isinstance(obj, dict):
        raise Malformed(f"{path}: top level must be an object")
    return obj


def gate(challenge_path: str, key_path: str, pro: Profile,
         verbose: bool = True) -> int:
    try:
        ch = _load(challenge_path)
        key = _load(key_path)
    except Malformed as e:
        if verbose:
            print(f"MALFORMED: {e}")
        return MALFORMED

    try:
        if ch.get("version") != 1 or key.get("version") != 1:
            raise Malformed("version must be 1")
        params = ch.get("params")
        if not isinstance(params, dict):
            raise Malformed("challenge.params missing")
        if params.get("lift_version") != 1:
            raise Malformed("unknown lift version")
        k = params.get("k")
        if not isinstance(k, int) or k < 0:
            raise Malformed("k must be a non-negative int")
        if ch.get("nullifier_count") != k:
            raise Malformed("nullifier_count does not match k")
        if params.get("digits") != pro.n_digits or \
                params.get("bits_per_digit") != pro.bits_per_digit:
            raise Malformed("challenge parameters do not match the "
                            "profile")
        data_hex = ch.get("data")
        if not isinstance(data_hex, str):
            raise Malformed("challenge.data missing")
        data = bytes.fromhex(data_hex)
        if sha(data) != ch.get("data_commitment"):
            raise Malformed("data commitment mismatch")
        seed_hex = key.get("seed")
        if not isinstance(seed_hex, str):
            raise Malformed("key.seed missing")
        seed = bytes.fromhex(seed_hex)
        if not 1 <= len(seed) <= 255:
            raise Malformed("key.seed must be 1..255 bytes")
        schedule = sched_mod.parse(key.get("schedule"))
        L = params.get("L")
        if not isinstance(L, int):
            raise Malformed("params.L missing")
        sched_mod.validate(pro, schedule, L)
        if len(schedule) != k:
            raise Malformed("schedule length does not match k")
        if sched_mod.digest(schedule) != ch.get("schedule_digest"):
            if verbose:
                print("FAIL: schedule digest mismatch")
            return FAIL
        H_target = ch.get("H")
        if not isinstance(H_target, str) or len(H_target) != 64:
            raise Malformed("challenge.H must be a 64-hex digest")
    except Malformed as e:
        if verbose:
            print(f"MALFORMED: {e}")
        return MALFORMED
    except ValueError as e:
        if verbose:
            print(f"MALFORMED: {e}")
        return MALFORMED

    # replay + structural audit + nullifier recomputation + binding
    try:
        H, _h, nulls, _D = run_path(pro, data, seed, schedule, L)
    except EncodingError as e:
        if verbose:
            print(f"FAIL: {e}")
        return FAIL
    if len(nulls) != k:
        if verbose:
            print("FAIL: nullifier count")
        return FAIL
    # check 4: nullifier recomputation against the published list
    published = ch.get("nullifiers")
    if isinstance(published, list) and len(published) == k:
        for got, want in zip(nulls, published):
            if not hmac.compare_digest(got, want):
                if verbose:
                    print("FAIL: nullifier recomputation")
                return FAIL
    if not hmac.compare_digest(H, H_target):
        if verbose:
            print("FAIL: binding")
        return FAIL
    if verbose:
        print("PASS")
    return PASS


__all__ = ["gate", "PASS", "FAIL", "MALFORMED", "Malformed"]
