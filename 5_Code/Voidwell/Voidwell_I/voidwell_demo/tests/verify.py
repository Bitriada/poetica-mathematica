"""verify.py -- the voidwell verification battery (spec D11 items
1-3 plus the monograph-law trials).

  V8   fare-octal digit operations: exact over 10^5 random states,
       all n; plus equivalence of the encoder's int fast path with the
       FareOctal reference class.
  V9   lift/project round-trip: all 2^3 small-model states and 10^5
       sampled full-model digivectors.
  V10  nullification: for 10^3 random (state, M, digit) with M
       invertible, trace_digit(conjugate(lift(D), M), d) is read back
       exactly; the PRF's rejection-sampled matrices nullify their
       target digit every time; and conjugation is order-sensitive
       (M1 M2 != M2 M1 give different wells).
  V11  UC-polynomial laws (sec. 8.5): the convolution rule and fare
       linearity, on random polynomials AND on real encoding paths.
  V12  multinumeral structure (App. A): trace dimension 36; off-
       diagonal commensurability always free; annihilation is an
       intra-base (diagonal) event.
"""
from __future__ import annotations

import random
import sys

sys.path.insert(0, ".")

from fareoctal.core import FareOctal, ZERO, tau, N_DIGITS
from ucq import conjugate, multinumeral, ucpoly
from ucq.conjugate import conjugation_nullifies, trace_digit
from ucq.lift import FULL, SMALL, lift, project
from ucq.matrix import FpMatrix, SingularMatrix
from voidwell.encoder import base_step, digit_set, encode, run_path
from voidwell.prf import prf_matrix, prf_schedule, prf_well_matrix

rng = random.Random(20261116)
RESULTS = []


def verdict(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" +
          (f"  [{detail}]" if detail else ""))


# ---------------------------------------------------------------- V8
def v8():
    fails = 0
    for _ in range(100_000):
        st = FareOctal.from_int(rng.getrandbits(27))
        n = rng.randrange(9)
        v = rng.randrange(8)
        if st.digit_zero(n).to_int() != \
                FareOctal.from_int(st.to_int() & ~(7 << (3 * n))).to_int():
            fails += 1
        d0 = st.digit_zero(n)
        if d0.digit_value(n) != 0 or any(
                d0.digit_value(m) != st.digit_value(m) for m in range(9)
                if m != n):
            fails += 1
        ds = st.digit_set(n, v)
        if ds.digit_value(n) != v or any(
                ds.digit_value(m) != st.digit_value(m) for m in range(9)
                if m != n):
            fails += 1
        if st.digit_vector() != tuple(st.digit_value(m)
                                      for m in range(N_DIGITS)):
            fails += 1
        if FareOctal.from_int(st.to_int()).to_int() != st.to_int():
            fails += 1
    verdict("V8a fare-octal digit ops exact (1e5 states)", fails == 0,
            f"{fails} failures")

    # int fast path == FareOctal reference
    fails = 0
    for _ in range(100_000):
        st = FareOctal.from_int(rng.getrandbits(27))
        b = rng.randrange(256)
        s2, fare = base_step(FULL, st.to_int(), b)
        # reference: the same transition through the FareOctal class
        op = b % 3
        if op == 0:
            g = (b >> 2) % 27
            ref = st * tau(g)
            if ref._bits is None:            # annihilated -> fallback
                ref = st.digit_set((b >> 3) % 9, (b >> 6) & 7)
                ref_fare = 1
            else:
                ref_fare = 0
        elif op == 1:
            ref = st.digit_zero((b >> 2) % 9)
            ref_fare = 1
        else:
            ref = st.digit_set((b >> 2) % 9, (b >> 5) & 7)
            ref_fare = 1
        if s2 != ref.to_int() or fare != ref_fare:
            fails += 1
    verdict("V8b encoder fast path == FareOctal class (1e5)", 
            fails == 0, f"{fails} failures")


# ---------------------------------------------------------------- V9
def v9():
    fails = sum(0 if project(SMALL, lift(SMALL, s)) == s else 1
                for s in range(1 << SMALL.n_bits))
    verdict("V9a lift round-trip, small model (all 8 states)",
            fails == 0)
    fails = 0
    for _ in range(100_000):
        s = rng.getrandbits(27)
        if project(FULL, lift(FULL, s)) != s:
            fails += 1
    verdict("V9b lift round-trip, full model (1e5 samples)",
            fails == 0, f"{fails} failures")
    # structure: every bit lands in its documented cell
    Q = lift(FULL, 1 << 26)
    ok = Q.rows[10 // 4][10 % 4] == 2    # bit 26 -> cell 10, shift 1
    verdict("V9c packing table honored (bit 26 -> cell 10 shift 1)", ok)


# ---------------------------------------------------------------- V10
def v10():
    fails = noninv = 0
    for _ in range(1000):
        s = rng.getrandbits(27)
        d = rng.randrange(9)
        while True:
            M = FpMatrix([[rng.randrange(FULL.p) for _ in range(4)]
                          for _ in range(4)], FULL.p)
            try:
                Minv = M.inverse()
                break
            except SingularMatrix:
                noninv += 1
        Qp = conjugate.conjugate(lift(FULL, s), M)
        if trace_digit(FULL, Qp, d) != \
                (project(FULL, Qp) >> (3 * d)) & 7:
            fails += 1
        # conjugation sanity: M Q M^-1 with M = I is Q
    I4 = FpMatrix.identity(4, FULL.p)
    s = rng.getrandbits(27)
    verdict("V10a trace_digit reads the conjugated state exactly",
            fails == 0, f"{fails} failures; {noninv} resamples")
    verdict("V10b identity conjugation is the identity",
            conjugate.conjugate(lift(FULL, s), I4) == lift(FULL, s))

    # order sensitivity: M1 M2 vs M2 M1 give different wells
    def rand_gl():
        while True:
            M = FpMatrix([[rng.randrange(FULL.p) for _ in range(4)]
                          for _ in range(4)], FULL.p)
            try:
                M.inverse()
                return M
            except SingularMatrix:
                continue
    diff = same = 0
    for _ in range(200):
        s = rng.getrandbits(27)
        A, B = rand_gl(), rand_gl()
        w1 = project(FULL, conjugate.conjugate(
            conjugate.conjugate(lift(FULL, s), A), B))
        w2 = project(FULL, conjugate.conjugate(
            conjugate.conjugate(lift(FULL, s), B), A))
        if w1 == w2:
            same += 1
        else:
            diff += 1
    verdict("V10c well order matters (A-then-B != B-then-A)",
            diff > same * 19, f"{diff}/200 differ")

    # the PRF's rejection-sampled matrices nullify EVERY time
    fails = 0
    seed = bytes(range(32))
    for j in range(20):
        s = rng.getrandbits(27)
        d = rng.randrange(9)
        M, _ = prf_well_matrix(FULL, seed, j, s, d)
        if not conjugation_nullifies(FULL, s, M, d):
            fails += 1
    verdict("V10d PRF well matrices nullify their digit (20 draws)",
            fails == 0, f"{fails} failures")


# ---------------------------------------------------------------- V11
def v11():
    fails = 0
    for _ in range(500):
        F = ucpoly.UCPolynomial(
            [ucpoly.UC(rng.randrange(-9, 10), rng.randrange(-9, 10))
             for _ in range(rng.randrange(1, 6))])
        G = ucpoly.UCPolynomial(
            [ucpoly.UC(rng.randrange(-9, 10), rng.randrange(-9, 10))
             for _ in range(rng.randrange(1, 6))])
        FG = F * G
        # L2: the convolution rule reproduces the product's betas
        # (the product trims trailing zero coefficients; pad to compare)
        conv = ucpoly.convolution_fares(F, G)
        direct = [abs(c.beta) for c in FG.coeffs]
        direct += [0] * (len(conv) - len(direct))
        if direct != conv:
            fails += 1
        # L1 (structure): the product stays tau-linear -- every
        # coefficient is a single UC pair (by construction) and the
        # fare is the sum of the per-coefficient weights
        if FG.fare() != sum(conv):
            fails += 1
    verdict("V11a convolution rule + tau-linearity (500 random pairs)",
            fails == 0, f"{fails} failures")

    # L1 on real encodings: fare(path) == sum of per-step fares
    fails = 0
    for k in (0, 1, 3):
        seed = bytes([k]) * 32
        sched = prf_schedule(FULL, seed, 43, k)
        H, h, nulls, D, values, fares = run_path(
            FULL, bytes.fromhex("00112233"), seed, sched, 43,
            collect=True)
        P = ucpoly.path_polynomial(values[1:], fares)
        if P.fare() != sum(fares):
            fails += 1
    verdict("V11b fare linearity on real encodings (k=0,1,3)",
            fails == 0, f"{fails} failures")


# ---------------------------------------------------------------- V12
def v12():
    ok = multinumeral.trace_dimension(9) == 36
    verdict("V12a trace dimension n(n-1)/2 = 36 for 9 bases", ok)
    fails = 0
    for _ in range(1000):
        a, b = rng.getrandbits(27), rng.getrandbits(27)
        cm = multinumeral.commensurability(FULL, a, b)
        if any(not cm[i][j] for i in range(9) for j in range(9)
               if i != j):
            fails += 1          # off-diagonal must always be free
        # annihilation iff some diagonal cell blocks
        ann = multinumeral.annihilates(FULL, a, b)
        diag_blocked = any(not cm[i][i] for i in range(9))
        if ann != diag_blocked:
            fails += 1
    verdict("V12b off-diagonal free; annihilation is intra-base "
            "(1e3 pairs)", fails == 0, f"{fails} failures")


def main() -> int:
    print("voidwell verification battery")
    print("=" * 60)
    v8(); v9(); v10(); v11(); v12()
    bad = [r for r in RESULTS if not r[1]]
    print("=" * 60)
    print(f"{len(RESULTS) - len(bad)}/{len(RESULTS)} PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
