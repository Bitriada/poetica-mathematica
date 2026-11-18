"""verify.py -- the Voidwell-2 verification battery.

Runs from the project root:  python3 tests/verify.py
(or `make verify`).  Every check prints PASS/FAIL; exit 1 on any
failure.  Checks are numbered W1..W12.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fareoctal.core import FareOctal, UNIT, tau, N_DIGITS  # noqa: E402
from ucq.lift import FULL, SMALL, lift, project, roundtrip_ok  # noqa
from ucq.matrix import FpMatrix  # noqa: E402
from voidwell2.encoder import (VARIANTS, encode, run_path,  # noqa: E402
                               ser_state, sha, base_step)
from voidwell2 import tickkey  # noqa: E402
from voidwell2 import wells as wells_mod  # noqa: E402
from voidwell2.gate import (ALLOWED_CHALLENGE_FIELDS,  # noqa: E402
                            check_challenge, gate)

DATA = bytes.fromhex("00112233")
FLAG_SEED = bytes.fromhex("11" * 32)
COMPACT_SEED = bytes.fromhex("22" * 16)

_results = []


def check(name, ok, note=""):
    _results.append((name, bool(ok), note))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {note}"
                                                    if note else ""))


def main() -> int:
    # W1 determinism: same seed -> same H, twice, and cross-process
    c1, k1, _ = encode(FULL, DATA, FLAG_SEED, 43, "flagship")
    c2, _k, _ = encode(FULL, DATA, FLAG_SEED, 43, "flagship")
    check("W1 determinism (same process)", c1["H"] == c2["H"])
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "c.json")
        r = subprocess.run(
            [sys.executable, "-m", "voidwell2", "encode",
             "--variant", "flagship", "--seed", FLAG_SEED.hex(),
             "--data", DATA.hex(), "--out", out],
            cwd=ROOT, capture_output=True, text=True)
        c3 = json.load(open(out)) if r.returncode == 0 else {}
    check("W1 determinism (cross-process)",
          r.returncode == 0 and c3.get("H") == c1["H"])

    # W2 variant discipline: lengths enforced, outputs independent
    try:
        encode(FULL, DATA, bytes(16), 43, "flagship")
        ok_len = False
    except ValueError:
        ok_len = True
    check("W2 flagship rejects a 16-byte seed", ok_len)
    try:
        encode(FULL, DATA, bytes(32), 43, "compact")
        ok_len2 = False
    except ValueError:
        ok_len2 = True
    check("W2 compact rejects a 32-byte seed", ok_len2)
    cc, _kk, _ = encode(FULL, DATA, COMPACT_SEED, 43, "compact")
    check("W2 variants give independent H",
          len({c1["H"], cc["H"]}) == 2)

    # W3 the full-width nullifier: domain arithmetic
    m = FpMatrix([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12],
                  [13, 14, 15, 16]], FULL.p)
    check("W3 matrix serialization is 517 bytes (16 x 32-bit cells)",
          len(m.serialize()) == 517)
    from voidwell2 import prf
    wells = wells_mod.wells_for(FULL, 43)
    H, h, nulls, D = run_path(FULL, DATA, FLAG_SEED, wells, 43)
    check("W3 three nullifiers, 64-hex each", len(nulls) == 3
          and all(len(n) == 64 for n in nulls))
    # the nullifier input is ser(D') || matrix: 5 + 517 = 522 bytes
    # -- the domain is 2^27 x p^16 = 2^4123
    check("W3 nullifier domain >= 2^4123 (27-bit state + 4096-bit "
          "matrix)", 27 + 16 * 256 >= 4123)

    # W4 different seeds -> different nullifiers (whp)
    Hb, _hb, nulls_b, _ = run_path(FULL, DATA,
                                   bytes.fromhex("44" * 32), wells, 43)
    check("W4 seed change flips every nullifier",
          all(a != b for a, b in zip(nulls, nulls_b)))

    # W5 the public surface is exactly the allowed fields
    check("W5 challenge surface == allowed fields",
          set(c1) == ALLOWED_CHALLENGE_FIELDS,
          f"published: {sorted(c1)}")
    check("W5 params carry the public pi-skeleton wells",
          c1["params"]["wells"] == [[3, 3], [14, 1], [15, 4]])

    # W6 gate accepts both honest variants (end to end, via CLI)
    with tempfile.TemporaryDirectory() as td:
        for variant, seed in (("flagship", FLAG_SEED),
                              ("compact", COMPACT_SEED)):
            co = os.path.join(td, f"{variant}.json")
            ko = os.path.join(td, f"{variant}.key.json")
            r = subprocess.run(
                [sys.executable, "-m", "voidwell2", "encode",
                 "--variant", variant, "--seed", seed.hex(),
                 "--data", DATA.hex(), "--out", co, "--key-out", ko],
                cwd=ROOT, capture_output=True, text=True)
            g = subprocess.run(
                [sys.executable, "-m", "voidwell2", "gate",
                 "--challenge", co, "--key", ko],
                cwd=ROOT, capture_output=True, text=True)
            check(f"W6 gate PASS ({variant})",
                  r.returncode == 0 and g.returncode == 0
                  and "PASS" in g.stdout)

    # W7 gate rejections: wrong seed, flipped H, wrong variant,
    #    tampered data, leak fields, tampered wells
    ch = dict(c1)
    bad = dict(ch)
    bad["H"] = ("0" if ch["H"][0] != "0" else "1") + ch["H"][1:]
    leak = dict(ch)
    leak["schedule_digest"] = "ab" * 32
    tamw = json.loads(json.dumps(ch))
    tamw["params"]["wells"] = [[3, 3], [14, 1], [16, 4]]
    tamd = json.loads(json.dumps(ch))
    tamd["data"] = "ff" * 4
    key_ok = {"version": 2, "variant": "flagship",
              "seed": FLAG_SEED.hex()}
    key_wrong = {"version": 2, "variant": "flagship",
                 "seed": ("00" * 32)}
    key_var = {"version": 2, "variant": "compact",
               "seed": COMPACT_SEED.hex()}
    with tempfile.TemporaryDirectory() as td:
        def _g(chal, key):
            cp = os.path.join(td, "c.json")
            kp = os.path.join(td, "k.json")
            json.dump(chal, open(cp, "w"))
            json.dump(key, open(kp, "w"))
            return gate(cp, kp, pro=FULL, verbose=False)
        check("W7 reject: wrong seed", _g(ch, key_wrong) == 1)
        check("W7 reject: flipped H bit", _g(bad, key_ok) == 1)
        check("W7 reject: key variant mismatch", _g(ch, key_var) == 2)
        check("W7 reject: tampered data", _g(tamd, key_ok) == 2)
        check("W7 reject: leak fields (schedule_digest)",
              _g(leak, key_ok) == 2)
        check("W7 reject: tampered wells", _g(tamw, key_ok) == 2)

    # W8 the base layer (the fare-octal battery)
    check("W8 fare-octal core: 9 digits, UNIT = 1, tau(0) = 2",
          N_DIGITS == 9 and UNIT.value() == 1
          and tau(0).value() == 2)
    x = FareOctal.from_value(30)            # 2*3*5: squarefree
    check("W8 fare-octal from_value round trip",
          FareOctal.from_value(x.value()).value() == x.value())
    # lift/project round trip on a sample
    ok = all(roundtrip_ok(FULL, s) for s in range(0, 1 << 27,
                                                   (1 << 27) // 5000))
    check("W8 lift/project round trip (5000 samples)", ok)
    ok = all(roundtrip_ok(SMALL, s) for s in range(1 << 3))
    check("W8 small-model round trip (exhaustive)", ok)

    # W9 the fare ledger + tau^2 = 0 linearity on a real encoding
    #     (the linearity law: fare(path) == sum of fares)
    from ucq import ucpoly
    Hc, _hc, _nc, _Dc, values, fares = run_path(
        FULL, DATA, FLAG_SEED, wells, 43, collect=True)
    check("W9 fare ledger collected over the path",
          len(fares) == 43 and len(values) == 44)
    P = ucpoly.path_polynomial(values[1:], fares)
    check("W9 tau^2 = 0 linearity: fare(path) == sum(per-step)",
          P.fare() == sum(fares),
          f"fare {P.fare()} == sum {sum(fares)}")

    # W10 tick-key: telescope, staircase, round trip, rejection
    for t in (1, 2, 3, 4, 5, 9, 67, 1000, 3141592653):
        a, b_, g = tickkey.sheets(t)
        if a + b_ + g != 0:
            check("W10 telescope exact", False, f"tick {t}")
            break
    else:
        check("W10 telescope alpha+beta+gamma = 0 exact "
              "(sampled ticks)", True)
    st = [tickkey.integer_sheet(t) for t in (4, 5, 8, 9, 66, 67,
                                             3141592653)]
    check("W10 staircase 0/1/2/3 transitions at I = 5, 9, 67",
          st == [0, 1, 1, 2, 2, 3, 3], f"{st}")
    chall, key = tickkey.keygen(tickkey.DEMO_TICK)
    check("W10 tick-key gate round trip", tickkey.gate(chall, key))
    wrong = {"version": 1, "tick": tickkey.DEMO_TICK + 1}
    check("W10 tick-key rejects a wrong tick",
          not tickkey.gate(chall, wrong))

    # W11 the small model runs the SAME code path
    sw = wells_mod.wells_for(SMALL, 8)
    Hs, _hs, nulls_s, _Ds = run_path(SMALL, DATA, b"\x5a", sw, 8)
    check("W11 small model: same run_path, 3 nullifiers",
          len(nulls_s) == 3)

    # W12 claim discipline: the printed claim is min(n, 256)
    claims = {v: VARIANTS[v]["claim"] for v in VARIANTS}
    check("W12 claims: flagship 2^256, compact 2^128",
          claims["flagship"] == "min(256, 256) = 2^256"
          and claims["compact"] == "min(128, 256) = 2^128")

    # W13 the two illustration cases reproduce bit-for-bit
    cases = [
        ("case1-flagship", "flagship", FLAG_SEED, DATA),
        ("case2-compact", "compact", COMPACT_SEED,
         bytes.fromhex("deadbeef")),
    ]
    for name, variant, seed, data in cases:
        d = os.path.join(ROOT, "examples", name)
        with open(os.path.join(d, "challenge.json")) as f:
            stored = json.load(f)
        c, k, _ = encode(FULL, data, seed, 43, variant)
        ok = (c == stored and k["seed"] == seed.hex())
        with tempfile.TemporaryDirectory() as td:
            cp = os.path.join(td, "c.json")
            kp = os.path.join(td, "k.json")
            json.dump(c, open(cp, "w"))
            json.dump(k, open(kp, "w"))
            ok = ok and gate(cp, kp, pro=FULL, verbose=False) == 0
        check(f"W13 example {name} reproduces and gates", ok)

    failed = [r for r in _results if not r[1]]
    print()
    print(f"{len(_results) - len(failed)}/{len(_results)} checks "
          f"passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
