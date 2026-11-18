"""trinumeral unit tests: exact, standard library only (pytest runner)."""

import math
import random
from fractions import Fraction

import pytest

from trinumeral import (E1, E2, E3, Regime, SpinTally, SpinorialTally,
                        TOP, Trinumeral, ZERO, canonical, encode_binary,
                        exact, run_trials, write_report)
from trinumeral.ladder import LadderEngine


def _rng():
    return random.Random(20261115)


# -- V1 exterior algebra -----------------------------------------------------
def test_generators_nilpotent_and_anticommuting():
    assert E1 * E1 == E2 * E2 == E3 * E3 == ZERO
    assert E1 * E2 == -(E2 * E1)
    assert E2 * E3 == -(E3 * E2)
    assert E3 * E1 == -(E1 * E3)
    assert TOP * TOP == ZERO                 # (e1e2e3)^2 = 0, sec. 8.4.5
    assert (E1 * E2) * E3 == TOP


def test_associativity_and_basis():
    rng = _rng()

    def rnd():
        return sum((rng.randint(-3, 3)
                    * E for E in (E1, E2, E3)), ZERO)

    for _ in range(200):
        x, y, z = rnd(), rnd(), rnd()
        assert (x * y) * z == x * (y * z)
    basis = [ZERO, E1, E2, E3, E1 * E2, E1 * E3, E2 * E3, TOP]
    assert len(basis) == 8                   # the 2^3 activation patterns


# -- V2 construction ---------------------------------------------------------
def test_worked_example_0p1_exact():
    T = Trinumeral.omega_0(Fraction(1, 10))
    a, b, g = T.fresh_discrepancies()
    assert a == Fraction(900719925474099, 2 ** 53)
    assert b == Fraction(-3602879701896397, 2 ** 55)
    assert g == Fraction(1, 2 ** 55)         # the "~1e-17" residue
    assert a + b + g == 0                    # the telescope theorem


def test_telescope_theorem_property():
    rng = _rng()
    for _ in range(300):
        v = Fraction(rng.randint(-10 ** 6, 10 ** 6),
                     rng.randint(1, 10 ** 6))
        x, y, z = Trinumeral.omega_0(v).fresh_discrepancies()
        assert x + y + z == 0


def test_binary_roundtrip_and_truncation():
    assert canonical("101.1") == Fraction(11, 2)
    assert canonical("-0.1") == Fraction(-1, 2)
    assert canonical(encode_binary(Fraction(5), 8)) == 5
    # truncation toward zero: |canonical| <= |v|, error < 2^-p
    for _ in range(100):
        v = Fraction(_rng().randint(-10 ** 6, 10 ** 6),
                     _rng().randint(1, 10 ** 6))
        c = canonical(encode_binary(v, 12))
        assert abs(c) <= abs(v)
        assert abs(v - c) < Fraction(1, 2 ** 12)
        assert (c > 0) == (v > 0) or v == 0


def test_projections_and_nihilum():
    T = Trinumeral.omega_0(Fraction(1, 10))
    assert T.project_0a("bin") == T.B
    assert T.project_0a("int") == 0
    assert T.project_0a("float") == 0.1
    N = Trinumeral.omega_0(0)
    assert N.is_nihilum() and N.is_traceless()


# -- V3 tau-cycle --------------------------------------------------------------
def test_tau_cycle():
    T = Trinumeral.omega_0(Fraction(1, 10))
    c = T.cycle_coefficient()
    assert c < 0                              # contraction parity
    assert abs(float(c)) < 1e-18              # "order of 1e-19"
    assert T.tau_cycle() * T.tau_cycle() == ZERO
    for v in (5, Fraction(1, 2), Fraction(3, 2)):
        assert Trinumeral.omega_0(v).cycle_coefficient() == 0


# -- V4 invariant points (C7) ----------------------------------------------------
def test_invariant_points_are_exact_integers():
    assert Trinumeral.omega_0(5).is_traceless()
    assert Trinumeral.omega_0(2 ** 53).is_traceless()
    assert not Trinumeral.omega_0(2 ** 53 + 1).is_traceless()
    assert not Trinumeral.omega_0(Fraction(3, 2)).is_traceless()   # C7
    assert not Trinumeral.omega_0(Fraction(1, 2)).is_traceless()   # C7
    for k in (0, 1, 7, -3, 2 ** 53, 2 ** 53 + 2, 2 ** 54 - 2):
        assert Trinumeral.omega_0(k).is_traceless() == (float(k) == k)


# -- V5 conversions ---------------------------------------------------------------
def test_conversions():
    u = Trinumeral.omega_0(2 ** 53 + 1)
    v = u.int2float()
    assert v.f == float(2 ** 53)              # the double rounds
    # ledger: construction beta = +1, conversion records -1 -> cancels
    # linearly (no annihilation); STATE stays incoherent by exactly 1
    assert v.tau.coefficient(1) == 0
    assert v.fresh_discrepancies()[1] == 1
    t = Trinumeral.omega_0(Fraction(1, 10))
    fb = t.float2bin()
    assert fb.tau.coefficient(2) == 0         # ledger: +1/2^55 then -1/2^55
    assert fb.fresh_discrepancies()[2] == Fraction(1, 2 ** 55)  # state
    fb55 = Trinumeral.omega_0(Fraction(1, 10), p=55).float2bin()
    assert fb55.tau.coefficient(2) == Fraction(1, 2 ** 55)  # record was 0
    bi = Trinumeral.omega_0(Fraction(7, 3)).bin2int()
    assert bi.i == 2


# -- V6 the ladder -------------------------------------------------------------------
def test_response_matrix():
    for resp, (trace, ghost) in {
            0: (Fraction(2), Fraction(0)),
            1: (Fraction(0), Fraction(2)),
            2: (Fraction(1), Fraction(1)),
            3: (Fraction(0), Fraction(2)),
            4: (Fraction(0), Fraction(2)),
            5: (Fraction(0), Fraction(2))}.items():
        eng = LadderEngine(Regime(trigger=5, response=resp))
        eng.record(2, 1)
        eng.record(2, 1)
        assert eng.tau.coefficient(2) == trace, f"R{resp}"
        assert eng.ghost == ghost, f"R{resp}"


def test_trigger_levels():
    def run(trig, seq, **kw):
        eng = LadderEngine(Regime(trigger=trig, response=3, **kw))
        for a in seq:
            eng.record(2, Fraction(a))
        return eng

    assert run(0, [1, 1]).tau.coefficient(2) == 2        # never
    assert run(1, [1, 2]).tau.coefficient(2) == 3        # exact only
    assert run(1, [1, 1]).tau.coefficient(2) == 0
    eng = run(2, [1, 1 + Fraction(1, 10 ** 7)])
    assert eng.tau.coefficient(2) == 0                   # within eps
    assert run(2, [1, 2]).tau.coefficient(2) == 3        # outside
    assert run(3, [1, 5]).tau.coefficient(2) == 0        # any repeat
    assert run(4, [1, 1, 1], k_trig=3).tau.coefficient(2) == 0
    eng = run(5, [1])                                    # always
    assert eng.tau.coefficient(2) == 0 and eng.ghost == 1


def test_pair_annihilation_conserves_and_spends():
    eng = LadderEngine(Regime())                        # default (1, 1)
    assert eng.record(2, Fraction(1, 4)) == 0
    assert eng.record(2, Fraction(1, 4)) == Fraction(1, 2)   # 2|alpha|
    assert eng.tau.coefficient(2) == 0 and eng.ghost == Fraction(1, 2)
    assert eng.record(2, Fraction(1, 4)) == 0           # spent: no effect
    assert eng.ghost == Fraction(1, 2)


def test_chiral_response_r4():
    eng = LadderEngine(Regime(trigger=5, response=4))
    eng.record(2, 1)
    eng.record(2, 1)                        # same sign: cancel
    assert eng.tau.coefficient(2) == 0 and eng.ghost == 2
    eng2 = LadderEngine(Regime(trigger=5, response=4))
    eng2.record(2, 1)
    eng2.record(2, -1)                      # opposite: add normally
    assert eng2.tau.coefficient(2) == 0 and eng2.ghost == 0


# -- V7 arithmetic ---------------------------------------------------------------------
def test_arithmetic_species():
    S = Trinumeral.omega_0(2) + Trinumeral.omega_0(3)
    assert (S.i, S.f, S.is_traceless()) == (5, 5.0, True)   # monograph
    X = (Trinumeral.omega_0(2, adder="xor")
         + Trinumeral.omega_0(3, adder="xor"))
    assert canonical(X.B) == 1 and X.tau.coefficient(0) == -4
    I = (Trinumeral.omega_0(Fraction(1, 10), adder="ieee")
         + Trinumeral.omega_0(Fraction(2, 10), adder="ieee"))
    assert I.f == 0.1 + 0.2 and not I.is_traceless()
    M = (Trinumeral.omega_0(2 ** 64 - 1, adder="mod", mod_bits=64)
         + Trinumeral.omega_0(2, adder="mod", mod_bits=64))
    assert canonical(M.B) == 1


def test_addition_merges_traces_and_ghosts():
    A = Trinumeral.omega_0(Fraction(1, 10))
    B = Trinumeral.omega_0(Fraction(1, 10))
    S = A + B
    assert S.ghost == A.ghost + B.ghost
    assert not S.tau.is_zero()


# -- V8 spin tallies ---------------------------------------------------------------------
def test_angle_bridge_and_negative_remark():
    assert SpinTally(0, 300) + SpinTally(0, 100) == SpinTally(1, 40)
    assert SpinTally.from_angle(-1) == SpinTally(-1, 359)
    rng = _rng()
    for _ in range(300):
        a = SpinTally(rng.randint(-5, 5), Fraction(rng.randint(0, 359)))
        b = SpinTally(rng.randint(-5, 5), Fraction(rng.randint(0, 359)))
        c = a + b
        assert 0 <= c.r < 360
        assert c.angle == a.angle + b.angle


def test_three_tally_types_one_angle():
    theta = Fraction(700, 3)
    variants = SpinTally.from_angle(theta).in_variants()
    for v, t in variants.items():
        assert t.angle == theta               # all three decode identically
    assert variants["natural"].shift_to(variants["natural"]) == 0
    for t in variants.values():               # shifts are whole turns
        assert variants["natural"].shift_to(t).denominator == 1


# -- V9 double cover -----------------------------------------------------------------------
def test_double_cover_and_berry():
    s = SpinorialTally(SpinTally(0, 0))
    r360 = s.rotate(360)
    r720 = s.rotate(360).rotate(360)
    assert r360.sigma == -1 and not r360.tau.is_zero()
    assert r720.sigma == +1 and r720.tau.is_zero()
    assert r720.ghost == 2                       # coherent spinor regime
    assert s.rotate(720).sigma == +1             # C5: flip per boundary
    berry = s.rotate(360).rotate(-360)
    assert berry.sigma == +1
    assert berry.tau.coefficient(0) == 1         # e+ holds the CW charge
    assert berry.tau.coefficient(1) == -1        # e- holds the CCW one
    assert not berry.tau.is_zero()               # Berry: path remembered
    quad = s.rotate(180).rotate(180).rotate(180).rotate(180)
    assert quad.sigma == +1


# -- V10 the battery ---------------------------------------------------------------------------
def test_trials_all_pass():
    results = run_trials()
    for k, v in results.items():
        assert v["verdict"].startswith(("EST-CONFIRMED", "CORRECTED",
                                        "BY-TRIAL", "OPEN")), (k, v)


def test_report_written(tmp_path):
    p = write_report(run_trials(), str(tmp_path / "T.md"))
    text = open(p, encoding="utf-8").read()
    for needle in ("C1", "C7", "Telescope", "coherent spinor",
                   "8.4.10", "1e-17"):
        assert needle in text, needle
