"""verify.py -- the Voidwell-3 W-battery: every claim of the build,
checked by code.  Run from the voidwell3 root:

    python3 -m voidwell3 verify

W1  the perspective laws + the loop closure (both profiles)
W2  lift/project round trips (toy exhaustive, full sampled)
W3  the bijection walk: every op bijective; D_L per-digit entropy
W4  the ghost-disc accumulator: open/verify, tamper detection
W5  the zeta-array: cells recomputable, the quaternion table exact
W6  the per-well trace law, with a negative control
W7  the involution exponent e: the fixed point at e = 0
W8  full-width nullifiers: distinct, preimage domain as stated
W9  the fare ledger: tau^2 = 0 linearity on real paths
W10 output statistics: H byte chi-square + avalanche
W11 variants: compact and flagship round trips
W12 the gate: honest PASS, wrong key FAIL, malformed MALFORMED
W13 speed: replay cost vs the V2 baseline
W14 determinism: same seed, same H; serialization stable
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import secrets
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from ucq import FULL, TOY, ucpoly  # noqa: E402
from ucq.lift import lift, project, roundtrip_ok  # noqa: E402
from ucq.matrix import FpMatrix  # noqa: E402
from voidwell3 import encoder, ghost as ghost_mod  # noqa: E402
from voidwell3 import perspectives as persp  # noqa: E402
from voidwell3 import wells as wells_mod  # noqa: E402
from voidwell3 import zeta as zeta_mod  # noqa: E402
from voidwell3.encoder import (base_step, digit_value,  # noqa: E402
                               run_path, sha, ser_state)
from voidwell3 import gate as gate_mod  # noqa: E402

DATA = bytes.fromhex("00112233")   # the demo data block

W = FULL
WELLS = wells_mod.wells_for(W, wells_mod.L_FULL)
TOY_WELLS = wells_mod.wells_for(TOY, wells_mod.L_TOY)

_results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    mark = "ok" if ok else "FAIL"
    line = f"[{mark}] {name}"
    if detail:
        line += f"  ({detail})"
    print(line)
    _results.append((name, bool(ok)))


def _chi2_survival(stat: float, df: int) -> float:
    a, x = df / 2, stat / 2
    if x <= 0:
        return 1.0
    if x < a + 1:
        ap, s, d = a, 1.0 / a, 1.0 / a
        for _ in range(2000):
            ap += 1
            d *= x / ap
            s += d
            if abs(d) < abs(s) * 1e-14:
                break
        p = s * math.exp(-x + a * math.log(x) - math.lgamma(a))
        return 1.0 - p
    tiny = 1e-300
    b, c, d, h = x + 1 - a, 1.0 / tiny, 1.0 / (x + 1 - a), \
        1.0 / (x + 1 - a)
    for i in range(1, 2000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        if abs(c) < tiny:
            c = tiny
        c = b + an / c
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1) < 1e-14:
            break
    return math.exp(-x + a * math.log(x) -
                    math.lgamma(a)) * h


def w1_perspectives() -> None:
    for name, pro in (("full", FULL), ("toy", TOY)):
        try:
            persp.units(pro)
            ok = True
        except AssertionError:
            ok = False
        check(f"W1 perspective laws + closure ({name})", ok)
    # the closure is exactly the monograph's: i1^2+i2^2+i3^2+1 = 0
    U = persp.units(FULL)
    I = FpMatrix.identity(4, FULL.p)
    zero = U[1] @ U[1] + U[2] @ U[2] + U[3] @ U[3] + I
    check("W1 closure identity i1^2+i2^2+i3^2+1 = 0",
          all(x == 0 for r in zero.rows for x in r))


def w2_lift() -> None:
    check("W2 lift/project round trip (toy, exhaustive)",
          all(roundtrip_ok(TOY, s) for s in range(256)))
    check("W2 lift/project round trip (full, 5000 samples)",
          all(roundtrip_ok(FULL, s) for s in range(
              0, 1 << 27, (1 << 27) // 5000)))


def w3_bijection_walk() -> None:
    # every op bijective on the toy, exhaustively per block
    blocks = [0x00, 0x11, 0x22, 0x33, 0x55, 0x77, 0x99, 0xFF]
    ok = True
    for b in blocks:
        seen = set()
        for s in range(256):
            s2, _ = base_step(TOY, s, b)
            seen.add(s2)
        ok = ok and len(seen) == 256
    check("W3 base ops bijective (toy, exhaustive, 8 blocks)", ok)
    # the walk cannot lose information: D_L is a relabeling of the
    # last checkpoint -> per-digit entropy must be full
    N = 800
    hist = [[0] * 8 for _ in range(9)]
    for _ in range(N):
        r = run_path(FULL, DATA, secrets.token_bytes(32),
                     WELLS, wells_mod.L_FULL)
        for d in range(9):
            hist[d][digit_value(FULL, r.D_L, d)] += 1
    ents = [-sum((c / N) * math.log2(c / N) for c in h if c)
            for h in hist]
    check("W3 D_L per-digit entropy ~ 3.0 (V2 measured 18.21/27)",
          all(e > 2.95 for e in ents),
          f"total {sum(ents):.2f} of 27 bits")


def w4_ghost() -> None:
    r = run_path(FULL, DATA, secrets.token_bytes(32), WELLS,
                 wells_mod.L_FULL)
    ok = all(r.verify_state(FULL, i)
             for i in (0, 1, 7, 17, 30, len(r.values) - 1))
    check("W4 ghost open/verify (6 positions)", ok)
    # tamper detection: flip one leaf, the path must fail
    tree = ghost_mod.build(
        [ghost_mod.leaf(FULL, s) for s in r.values])
    check("W4 ghost tree internally consistent",
          ghost_mod.tamper_check(tree))
    tree[0][5] = hashlib.sha256(b"lie").digest()
    check("W4 ghost tamper detection",
          not ghost_mod.tamper_check(tree))
    # the root is bound into H
    other = run_path(FULL, DATA, secrets.token_bytes(32), WELLS,
                     wells_mod.L_FULL)
    check("W4 ghost root differs across seeds",
          other.ghost_root != r.ghost_root)


def w5_zeta() -> None:
    # the quaternion ground truth: (component, sign) of q_a * q_b
    truth = {
        (0, 0): (0, 1), (0, 1): (1, 1), (0, 2): (2, 1),
        (0, 3): (3, 1),
        (1, 0): (1, 1), (1, 1): (0, -1), (1, 2): (3, 1),
        (1, 3): (2, -1),
        (2, 0): (2, 1), (2, 1): (3, -1), (2, 2): (0, -1),
        (2, 3): (1, 1),
        (3, 0): (3, 1), (3, 1): (2, 1), (3, 2): (1, -1),
        (3, 3): (0, -1),
    }
    ok = True
    for (a, b), (comp, sg) in truth.items():
        if zeta_mod.MU[b][a] != comp or zeta_mod.sign(a, b) != sg:
            ok = False
    check("W5 quaternion table exact (all 16 products)", ok)
    r = run_path(FULL, DATA, secrets.token_bytes(32), WELLS,
                 wells_mod.L_FULL)
    ok = (len(r.zeta_cells) == 16 and len(r.disentangled) == 16
          and len(set(r.disentangled)) == 16)
    # cells are recomputable from the recorded well material
    ok2 = True
    for wd in r.wells_detail:
        for a in range(4):
            if r.zeta_cells[(a, wd["j"] - 1)] != zeta_mod.cell(
                    a, wd["j"] - 1, wd["nullifier"],
                    wd["Qp"].row(a)):
                ok2 = False
    check("W5 zeta cells: 16, distinct, recomputable", ok and ok2)


def w6_trace_law() -> None:
    r = run_path(FULL, DATA, secrets.token_bytes(32), WELLS,
                 wells_mod.L_FULL)
    ok = all(w["trace_expected"] == w["trace_actual"]
             for w in r.wells_detail)
    check("W6 trace law tr(Q') = tr(Q) + tr(Q U_j^2) at all wells",
          ok)
    # negative control: perturb one entry of a conjugated matrix
    # and the law must fail
    wd = r.wells_detail[0]
    rows = [list(x) for x in wd["Qp"].rows]
    rows[0][0] = (rows[0][0] + 1) % FULL.p
    bad = FpMatrix(rows, FULL.p)
    check("W6 negative control (perturbed Q' fails the law)",
          bad.trace() != wd["trace_expected"])


def w7_involution() -> None:
    ok = all(wells_mod.prime_scaling(FULL, j, 0) == 1
             for j in (1, 2, 3, 4))
    check("W7 fixed point: e = 0 (s = 1/2) makes every prime "
          "scaling n_j^e = 1", ok)
    seed = secrets.token_bytes(32)
    r0 = run_path(FULL, DATA, seed, WELLS, wells_mod.L_FULL, e=0)
    r1 = run_path(FULL, DATA, seed, WELLS, wells_mod.L_FULL, e=1)
    check("W7 e is a live parameter (e=0 and e=1 give different H)",
          r0.H != r1.H and r0.ghost_root != r1.ghost_root)
    # the well schedule digest commits e
    check("W7 wells digest commits e",
          wells_mod.digest(WELLS, 0) != wells_mod.digest(WELLS, 1))


def w8_nullifiers() -> None:
    r = run_path(FULL, DATA, secrets.token_bytes(32), WELLS,
                 wells_mod.L_FULL)
    widths = set()
    for w in r.wells_detail:
        pre = ser_state(FULL, w["D_prime"]) + w["Qp"].serialize()
        widths.add(len(pre) * 8)
    # 27 state bits + 4096 matrix bits = 2^4123 entropy domain;
    # the canonical serialization adds version/width framing
    check("W8 full-width nullifiers (2^4123 preimage domain)",
          widths == {4184} and len(set(r.nullifiers)) == 4,
          f"preimage {sorted(widths)} bits incl. framing "
          f"(27 + 4096 + framing)")


def w9_ledger() -> None:
    for pro, wels, L, seed in (
            (FULL, WELLS, wells_mod.L_FULL, secrets.token_bytes(32)),
            (TOY, TOY_WELLS, wells_mod.L_TOY, b"\xab\xcd")):
        r = run_path(pro, DATA, seed, wels, L)
        P = ucpoly.path_polynomial(r.values[1:], r.fares)
        check(f"W9 tau^2 = 0 ledger linearity "
              f"({'full' if pro is FULL else 'toy'}): "
              f"fare(path) = sum of fares",
              P.fare() == sum(r.fares),
              f"{P.fare()} = {sum(r.fares)}")


def w10_statistics() -> None:
    N = 512
    buf = bytearray()
    for _ in range(N):
        r = run_path(FULL, DATA, secrets.token_bytes(32), WELLS,
                     wells_mod.L_FULL)
        buf += bytes.fromhex(r.H)
    counts = [0] * 256
    for b in buf:
        counts[b] += 1
    stat = sum((c - len(buf) / 256) ** 2 / (len(buf) / 256)
               for c in counts)
    p = _chi2_survival(stat, 255)
    check("W10 H byte chi-square vs uniform (512 seeds)",
          0.001 < p < 0.999, f"p = {p:.3f}")
    dists = []
    for _ in range(128):
        orig = secrets.token_bytes(32)
        fl = bytearray(orig)
        bit = secrets.randbelow(256)
        fl[bit // 8] ^= 1 << (bit % 8)
        h1 = run_path(FULL, DATA, orig, WELLS,
                      wells_mod.L_FULL).H
        h2 = run_path(FULL, DATA, bytes(fl), WELLS,
                      wells_mod.L_FULL).H
        dists.append(bin(int(h1, 16) ^ int(h2, 16)).count("1"))
    mean = sum(dists) / len(dists)
    check("W10 avalanche (128 one-bit seed flips)",
          abs(mean - 128) < 4, f"mean {mean:.1f} of 256")


def w11_variants() -> None:
    for variant, nb in (("compact", 16), ("flagship", 32)):
        seed = secrets.token_bytes(nb)
        r = run_path(FULL, DATA, seed, WELLS, wells_mod.L_FULL)
        chal = {
            "version": 3,
            "params": {
                "construction": "perspective-walk",
                "variant": variant,
                "seed_bits": nb * 8,
                "lift_version": 1,
                "digits": FULL.n_digits,
                "bits_per_digit": FULL.bits_per_digit,
                "L": wells_mod.L_FULL,
                "k": len(WELLS),
                "e": wells_mod.DEFAULT_E,
                "wells": [list(w) for w in WELLS],
            },
            "data": DATA.hex(),
            "data_commitment": sha(DATA),
            "nullifier_count": len(WELLS),
            "H": r.H,
        }
        key = {"version": 3, "variant": variant,
               "seed": seed.hex()}
        with tempfile.TemporaryDirectory() as td:
            cp = os.path.join(td, "c.json")
            kp = os.path.join(td, "k.json")
            with open(cp, "w") as f:
                json.dump(chal, f)
            with open(kp, "w") as f:
                json.dump(key, f)
            rc = gate_mod.gate(cp, kp, FULL, verbose=False)
        check(f"W11 {variant} encode + gate round trip", rc == 0)


def w12_gate() -> None:
    seed = secrets.token_bytes(32)
    r = run_path(FULL, DATA, seed, WELLS, wells_mod.L_FULL)
    base = {
        "version": 3,
        "params": {
            "construction": "perspective-walk",
            "variant": "flagship",
            "seed_bits": 256,
            "lift_version": 1,
            "digits": FULL.n_digits,
            "bits_per_digit": FULL.bits_per_digit,
            "L": wells_mod.L_FULL,
            "k": len(WELLS),
            "e": wells_mod.DEFAULT_E,
            "wells": [list(w) for w in WELLS],
        },
        "data": DATA.hex(),
        "data_commitment": sha(DATA),
        "nullifier_count": len(WELLS),
        "H": r.H,
    }
    good_key = {"version": 3, "variant": "flagship",
                "seed": seed.hex()}
    wrong_key = {"version": 3, "variant": "flagship",
                 "seed": secrets.token_bytes(32).hex()}

    def run(chal, key):
        with tempfile.TemporaryDirectory() as td:
            cp = os.path.join(td, "c.json")
            kp = os.path.join(td, "k.json")
            with open(cp, "w") as f:
                json.dump(chal, f)
            with open(kp, "w") as f:
                json.dump(key, f)
            return gate_mod.gate(cp, kp, FULL, verbose=False)

    check("W12 gate: honest key -> PASS",
          run(base, good_key) == gate_mod.PASS)
    check("W12 gate: wrong key -> FAIL",
          run(base, wrong_key) == gate_mod.FAIL)
    leak = dict(base)
    leak["nullifiers"] = r.nullifiers
    check("W12 gate: published nullifiers -> MALFORMED",
          run(leak, good_key) == gate_mod.MALFORMED)
    badwells = json.loads(json.dumps(base))
    badwells["params"]["wells"] = [[2, 2], [3, 3], [5, 5], [8, 7]]
    check("W12 gate: off-skeleton wells -> MALFORMED",
          run(badwells, good_key) == gate_mod.MALFORMED)
    bade = json.loads(json.dumps(base))
    bade["params"]["e"] = "1"
    check("W12 gate: non-integer e -> MALFORMED",
          run(bade, good_key) == gate_mod.MALFORMED)
    badh = dict(base)
    badh["H"] = "00" * 32
    check("W12 gate: wrong H -> FAIL",
          run(badh, good_key) == gate_mod.FAIL)


def w13_speed() -> None:
    # min of 3 batches (microbenchmark hygiene: the minimum is the
    # least load-contaminated estimate on a shared machine)
    best = None
    for _ in range(3):
        t0 = time.perf_counter()
        n = 40
        for _ in range(n):
            run_path(FULL, DATA, secrets.token_bytes(32), WELLS,
                     wells_mod.L_FULL)
        ms = (time.perf_counter() - t0) / n * 1000
        best = ms if best is None else min(best, ms)
    ms = best
    v2_ms, v2_wells = 6.77, 3        # the V3 investigation baseline
    per_well_v3 = ms / len(WELLS)
    per_well_v2 = v2_ms / v2_wells
    # the claim: one V3 perspective well (twist + conjugation +
    # trace law + 4 zeta cells) costs LESS than one V2 well
    check("W13 speed: a perspective well costs less than a V2 well",
          per_well_v3 < per_well_v2,
          f"{ms:.2f} ms/replay, {per_well_v3:.2f} ms/well vs "
          f"V2 {per_well_v2:.2f} ({per_well_v2 / per_well_v3:.2f}x "
          "denser per well)")


def w14_determinism() -> None:
    seed = secrets.token_bytes(32)
    r1 = run_path(FULL, DATA, seed, WELLS, wells_mod.L_FULL)
    r2 = run_path(FULL, DATA, seed, WELLS, wells_mod.L_FULL)
    check("W14 determinism: same seed -> same H",
          r1.H == r2.H and r1.ghost_root == r2.ghost_root)
    w = r1.wells_detail[0]
    q2 = FpMatrix.deserialize(w["Qp"].serialize(), FULL.p)
    check("W14 matrix serialization round trip", q2 == w["Qp"])


def main() -> int:
    print("Voidwell-3 W-battery")
    w1_perspectives()
    w2_lift()
    w3_bijection_walk()
    w4_ghost()
    w5_zeta()
    w6_trace_law()
    w7_involution()
    w8_nullifiers()
    w9_ledger()
    w10_statistics()
    w11_variants()
    w12_gate()
    w13_speed()
    w14_determinism()
    fails = [n for n, ok in _results if not ok]
    print(f"\n{len(_results) - len(fails)}/{len(_results)} passed")
    if fails:
        print("FAILED:", fails)
        return 1
    print("ALL GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
