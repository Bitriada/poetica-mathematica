"""gate.py -- verification (design study, section 6).

Exit codes: PASS=0, FAIL=1, MALFORMED=2.

Checks, in order:
  1. Schema: both JSONs parse, versions match, the variant's seed
     width matches the key, the data commitment matches, and the
     challenge's parameters equal the spec constants (L = 43, the
     public pi-skeleton wells).
  2. SURFACE ENFORCEMENT: a challenge that publishes a schedule
     digest or a nullifier list is rejected as malformed --
     Voidwell-2 challenges publish H and parameters, nothing else.
     The gate is the audit's teeth.
  3. Replay: recompute the path from the seed -- the same run_path
     code path as the encoder (bit-identical by construction).
  4. Structural audit at each well: digit n_j of the conjugated,
     projected digivector is 0 (inside run_path; a wrong matrix
     fails it with probability 1 - 2^-bits_per_digit).
  5. Binding: H compared in constant time (hmac.compare_digest).
     Nothing is published per-well, so the H comparison IS the
     binding, and the attacker has no partial check to filter
     with -- every failing trial costs a full replay.
"""
from __future__ import annotations

import hmac
import json

from ucq.lift import Profile
from voidwell2 import wells as wells_mod
from voidwell2.encoder import (VARIANTS, EncodingError, run_path, sha)

PASS, FAIL, MALFORMED = 0, 1, 2

#: fields a V2 challenge may carry (the entire public surface)
ALLOWED_CHALLENGE_FIELDS = {
    "version", "params", "H", "data", "data_commitment",
    "nullifier_count",
}
#: per-well leak fields: publishing these is a spec violation
#: (the challenge must carry H and public parameters only)
FORBIDDEN_CHALLENGE_FIELDS = {"schedule_digest", "nullifiers",
                              "schedule"}


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


def check_challenge(ch: dict, pro: Profile) -> int:
    """Schema + surface checks; returns (L, variant) or raises."""
    if ch.get("version") != 2:
        raise Malformed("version must be 2 (Voidwell-2)")
    params = ch.get("params")
    if not isinstance(params, dict):
        raise Malformed("challenge.params missing")
    if params.get("lift_version") != 1:
        raise Malformed("unknown lift version")
    variant = params.get("variant")
    if variant not in VARIANTS:
        raise Malformed(f"unknown variant {variant!r}")
    if params.get("seed_bits") != VARIANTS[variant]["seed_bits"]:
        raise Malformed("seed_bits does not match the variant")
    if params.get("digits") != pro.n_digits or \
            params.get("bits_per_digit") != pro.bits_per_digit:
        raise Malformed("challenge parameters do not match the "
                        "profile")
    k = params.get("k")
    if not isinstance(k, int) or k < 0:
        raise Malformed("k must be a non-negative int")
    if ch.get("nullifier_count") != k:
        raise Malformed("nullifier_count does not match k")
    data_hex = ch.get("data")
    if not isinstance(data_hex, str):
        raise Malformed("challenge.data missing")
    data = bytes.fromhex(data_hex)
    if sha(data) != ch.get("data_commitment"):
        raise Malformed("data commitment mismatch")
    L = params.get("L")
    if not isinstance(L, int):
        raise Malformed("params.L missing")
    wells = wells_mod.parse(params.get("wells"))
    wells_mod.validate(pro, wells, L)
    if len(wells) != k:
        raise Malformed("wells length does not match k")
    # the wells must equal the spec's public constants (no schedule
    # freedom exists in V2 -- a challenge with different wells is a
    # different, unstudied construction)
    if wells != wells_mod.wells_for(pro, L, k):
        raise Malformed("wells do not match the public pi-skeleton "
                        "constants of the spec")
    if not isinstance(ch.get("H"), str) or len(ch["H"]) != 64:
        raise Malformed("challenge.H must be a 64-hex digest")
    # -- surface enforcement (DR2) --
    extra = set(ch) - ALLOWED_CHALLENGE_FIELDS
    if extra & FORBIDDEN_CHALLENGE_FIELDS:
        raise Malformed("V2 challenges must not publish per-well "
                        f"values (found: {sorted(extra)})")
    if extra:
        raise Malformed(f"unknown challenge fields: {sorted(extra)}")
    return L, variant


def gate(challenge_path: str, key_path: str, pro: Profile,
         verbose: bool = True) -> int:
    try:
        ch = _load(challenge_path)
        key = _load(key_path)
        L, variant = check_challenge(ch, pro)
    except Malformed as e:
        if verbose:
            print(f"MALFORMED: {e}")
        return MALFORMED
    except ValueError as e:
        if verbose:
            print(f"MALFORMED: {e}")
        return MALFORMED

    try:
        if key.get("version") != 2:
            raise Malformed("key version must be 2")
        if key.get("variant") != variant:
            raise Malformed("key variant does not match the challenge")
        seed_hex = key.get("seed")
        if not isinstance(seed_hex, str):
            raise Malformed("key.seed missing")
        seed = bytes.fromhex(seed_hex)
        n_bytes = VARIANTS[variant]["seed_bytes"]
        if len(seed) != n_bytes:
            raise Malformed(f"variant {variant} requires a "
                            f"{n_bytes}-byte seed (got {len(seed)})")
    except Malformed as e:
        if verbose:
            print(f"MALFORMED: {e}")
        return MALFORMED
    except ValueError as e:
        if verbose:
            print(f"MALFORMED: {e}")
        return MALFORMED

    # replay + structural audit + binding
    wells = wells_mod.parse(ch["params"]["wells"])
    data = bytes.fromhex(ch["data"])
    try:
        H, _h, nulls, _D = run_path(pro, data, seed, wells, L)
    except EncodingError as e:
        if verbose:
            print(f"FAIL: {e}")
        return FAIL
    if len(nulls) != ch["params"]["k"]:
        if verbose:
            print("FAIL: nullifier count")
        return FAIL
    if not hmac.compare_digest(H, ch["H"]):
        if verbose:
            print("FAIL: binding")
        return FAIL
    if verbose:
        print("PASS")
    return PASS


__all__ = ["gate", "check_challenge", "PASS", "FAIL", "MALFORMED",
           "Malformed", "ALLOWED_CHALLENGE_FIELDS",
           "FORBIDDEN_CHALLENGE_FIELDS"]
