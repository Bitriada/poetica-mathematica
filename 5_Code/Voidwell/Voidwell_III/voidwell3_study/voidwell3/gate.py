"""gate.py -- verification for Voidwell-3.

Exit codes: PASS=0, FAIL=1, MALFORMED=2.

The V3 gate keeps the V2 discipline and extends the audit suite --
"the audit's teeth" now check the challenge's PUBLIC mathematics
before any replay:

  1. Schema: JSONs parse, versions match, the variant's seed width
     matches the key, the data commitment matches, the parameters
     equal the spec constants (L, the prime skeleton wells, the
     involution exponent e).
  2. SURFACE ENFORCEMENT: a challenge that publishes per-well values
     is rejected as malformed (unchanged from V2).
  3. THE PERSPECTIVE AUDIT: the four public units satisfy their four
     laws (i1^2=i1, i2^2=-i2, i4^2=-1) and the loop closure
     i1^2+i2^2+i3^2+1 = 0 -- recomputed from the constants.
  4. THE QUATERNION AUDIT: the disentangling table's mu maps are
     permutations (the 16-cell map is a bijection).
  5. THE INVOLUTION AUDIT: e is a valid public exponent; the
     fixed-point fact is reported (e = 0 <=> s = 1/2, the critical
     line, where every prime scaling n_j^e is 1).
  6. Replay: recompute the path -- the same run_path code path as
     the encoder.  Inside the replay: emergent nullification per
     well (a wrong matrix fails with probability 1 - 2^-bpd), the
     per-well trace law tr(Q') = tr(Q) + tr(Q U_j^2) (fails with
     probability 1 - 1/p), the ghost root, the 16 zeta cells, and
     the disentangling.
  7. Binding: H compared in constant time.
"""
from __future__ import annotations

import hmac
import json

from ucq.lift import FULL, TOY, Profile
from voidwell3 import perspectives as persp
from voidwell3 import wells as wells_mod
from voidwell3 import zeta as zeta_mod
from voidwell3.encoder import (VARIANTS, EncodingError, run_path,
                               sha)

PASS, FAIL, MALFORMED = 0, 1, 2


def profile_for_params(params: dict) -> "Profile":
    """Pick the model profile from a challenge's public parameters:
    the toy is 8 one-bit digits, the full model 9 octal digits.
    Lets the gate CLI and the study cases run one command for any
    variant."""
    if not isinstance(params, dict):
        return FULL
    if (params.get("digits") == TOY.n_digits
            and params.get("bits_per_digit") == TOY.bits_per_digit):
        return TOY
    return FULL


#: fields a V3 challenge may carry (the entire public surface)
ALLOWED_CHALLENGE_FIELDS = {
    "version", "params", "H", "data", "data_commitment",
    "nullifier_count",
}
#: per-well leak fields: publishing these is a spec violation
FORBIDDEN_CHALLENGE_FIELDS = {"schedule_digest", "nullifiers",
                              "schedule", "wells_detail",
                              "ghost_root", "zeta_cells"}


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


def check_challenge(ch: dict, pro: Profile) -> tuple[int, int]:
    """Schema + surface + public-math audits; returns (L, e)."""
    if ch.get("version") != 3:
        raise Malformed("version must be 3 (Voidwell-3)")
    params = ch.get("params")
    if not isinstance(params, dict):
        raise Malformed("challenge.params missing")
    if params.get("lift_version") != 1:
        raise Malformed("unknown lift version")
    if params.get("construction") != "perspective-walk":
        raise Malformed("construction must be 'perspective-walk'")
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
    e = params.get("e")
    if not isinstance(e, int) or not 0 <= e < pro.p - 1:
        raise Malformed("params.e must be an int in 0..p-2 "
                        "(e = 1 - 2s; e = 0 is the critical value "
                        "s = 1/2)")
    wells = wells_mod.parse(params.get("wells"))
    wells_mod.validate(pro, wells, L)
    if len(wells) != k:
        raise Malformed("wells length does not match k")
    # the wells must equal the spec's public constants (the prime
    # skeleton; no schedule freedom exists in V3)
    if wells != wells_mod.wells_for(pro, L, k):
        raise Malformed("wells do not match the public prime "
                        "skeleton constants of the spec")
    if not isinstance(ch.get("H"), str) or len(ch["H"]) != 64:
        raise Malformed("challenge.H must be a 64-hex digest")
    # -- surface enforcement --
    extra = set(ch) - ALLOWED_CHALLENGE_FIELDS
    if extra & FORBIDDEN_CHALLENGE_FIELDS:
        raise Malformed("V3 challenges must not publish per-well "
                        f"values (found: {sorted(extra)})")
    if extra:
        raise Malformed(f"unknown challenge fields: {sorted(extra)}")
    # -- the public-math audits --
    try:
        persp.units(pro)     # the four laws + the closure
    except AssertionError as err:
        raise Malformed(f"perspective audit failed: {err}")
    for b, mu in zeta_mod.MU.items():
        if sorted(mu) != [0, 1, 2, 3]:
            raise Malformed(f"quaternion audit failed: mu_{b} "
                            "is not a permutation")
    # the involution fixed-point audit: at e = 0 every prime scaling
    # is 1 (the identity involution, s = 1/2); this is informational
    # -- it documents that the gate KNOWS the critical setting
    if e == 0 and k > 0:
        # legal, but noteworthy: the challenge sits ON the fixed
        # point (the scalings are all 1)
        pass
    return L, e


def gate(challenge_path: str, key_path: str, pro: Profile,
         verbose: bool = True) -> int:
    try:
        ch = _load(challenge_path)
        key = _load(key_path)
        L, e = check_challenge(ch, pro)
        params = ch["params"]
        variant = params["variant"]
    except Malformed as exc:
        if verbose:
            print(f"MALFORMED: {exc}")
        return MALFORMED
    except ValueError as exc:
        if verbose:
            print(f"MALFORMED: {exc}")
        return MALFORMED

    try:
        if key.get("version") != 3:
            raise Malformed("key version must be 3")
        if key.get("variant") != variant:
            raise Malformed("key variant does not match the "
                            "challenge")
        seed_hex = key.get("seed")
        if not isinstance(seed_hex, str):
            raise Malformed("key.seed missing")
        seed = bytes.fromhex(seed_hex)
        n_bytes = VARIANTS[variant]["seed_bytes"]
        if len(seed) != n_bytes:
            raise Malformed(f"variant {variant} requires a "
                            f"{n_bytes}-byte seed (got {len(seed)})")
    except Malformed as exc:
        if verbose:
            print(f"MALFORMED: {exc}")
        return MALFORMED
    except ValueError as exc:
        if verbose:
            print(f"MALFORMED: {exc}")
        return MALFORMED

    # replay + the in-path audits (nullification, trace law, ghost
    # root, zeta cells, disentangling) + binding
    wells = wells_mod.parse(params["wells"])
    data = bytes.fromhex(ch["data"])
    try:
        res = run_path(pro, data, seed, wells, L, e)
    except EncodingError as exc:
        if verbose:
            print(f"FAIL: {exc}")
        return FAIL
    if len(res.nullifiers) != params["k"]:
        if verbose:
            print("FAIL: nullifier count")
        return FAIL
    if not hmac.compare_digest(res.H, ch["H"]):
        if verbose:
            print("FAIL: binding")
        return FAIL
    if verbose:
        print("PASS")
    return PASS


__all__ = ["gate", "check_challenge", "PASS", "FAIL", "MALFORMED",
           "Malformed", "ALLOWED_CHALLENGE_FIELDS",
           "FORBIDDEN_CHALLENGE_FIELDS"]
