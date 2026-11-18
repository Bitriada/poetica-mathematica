"""fare-octal unit tests: everything exact, standard library only."""

import random
from fractions import Fraction
from math import gcd, prod

import pytest

from fareoctal import (FORTRESS_NOTE, N_BITS, PRIMES, FareElement,
                       FareOctal, UNIT, ZERO, bit_address, count_table,
                       digit_address, functional_equation_identities,
                       index_rule_product, lattice_sums, linear_to_tensor,
                       spectral_involution, tau, tensor_to_linear,
                       zeta_element)
from fareoctal.core import sieve_primes
from fareoctal.lattice import (H_EXPONENTS, L_TABLE, M_TABLES, h_exponent,
                               m_value)
from fareoctal.verify import run_checks, write_report


# -- V1 counting ----------------------------------------------------------
def test_counting_first_states_match_monograph():
    expected = [(0, ()), (1, (0,)), (2, (1,)), (3, (0, 1)), (4, (2,)),
                (5, (0, 2)), (6, (1, 2)), (7, (0, 1, 2)), (8, (3,)),
                (9, (0, 3)), (10, (1, 3)), (11, (0, 1, 3)), (12, (2, 3)),
                (13, (0, 2, 3)), (14, (1, 2, 3)), (15, (0, 1, 2, 3))]
    for c, s, _ in count_table(16):
        assert s.active_linear() == expected[c][1]


def test_carry_displays():
    assert FareOctal.from_int(0).display() == "[0 0 0 0 0 0 0 0 0]"
    assert FareOctal.from_int(1).display() == "[0 0 0 0 0 0 0 0 1]"
    assert FareOctal.from_int(7).display() == "[0 0 0 0 0 0 0 0 7]"
    assert FareOctal.from_int(8).display() == "[0 0 0 0 0 0 0 1 0]"
    assert FareOctal.from_int(9).display() == "[0 0 0 0 0 0 0 1 1]"
    assert FareOctal.from_int(64).display() == "[0 0 0 0 0 0 1 0 0]"
    assert FareOctal.from_int(2 ** 27 - 1).display() == \
        "[7 7 7 7 7 7 7 7 7]"


# -- addressing -----------------------------------------------------------
def test_prime_ladder():
    assert PRIMES == tuple(sieve_primes(27))
    assert PRIMES[0] == 2 and PRIMES[26] == 103


def test_tensor_roundtrip_and_printed_examples():
    printed = {0: (1, 1, 1), 1: (1, 2, 1), 3: (2, 1, 1), 9: (1, 1, 2),
               13: (2, 2, 2), 26: (3, 3, 3)}
    for L, cell in printed.items():
        assert linear_to_tensor(L) == cell
    for L in range(N_BITS):
        assert tensor_to_linear(*linear_to_tensor(L)) == L


def test_bit_address_chain():
    for L in range(N_BITS):
        a = bit_address(L)
        assert a["cell"] == linear_to_tensor(L)
        assert a["digit"] == L // 3 and a["digit_bit"] == L % 3
        assert a["prime"] == PRIMES[L]
    for n in range(9):
        assert digit_address(n) == (n // 3 + 1, n % 3 + 1)


# -- readings --------------------------------------------------------------
def test_three_readings():
    s = FareOctal({1, 2})                     # primes 3, 5
    assert s.display() == "[0 0 0 0 0 0 0 0 6]"
    assert s.to_int() == 6
    assert s.value() == 15
    assert s.h_exponent() == 3 * (1 * 2 * 1 + 1 * 3 * 1)
    assert s.h_weight() == 2 ** 15


def test_from_value_roundtrip_random():
    rng = random.Random(42)
    for _ in range(300):
        bits = frozenset(b for b in range(N_BITS) if rng.random() < 0.3)
        s = FareOctal(bits)
        assert FareOctal.from_value(s.value()) == s
        assert FareOctal.from_int(s.to_int()) == s


def test_from_value_rejects_non_squarefree_and_out_of_window():
    with pytest.raises(ValueError):
        FareOctal.from_value(4)          # 2^2
    with pytest.raises(ValueError):
        FareOctal.from_value(107)        # prime beyond the window
    with pytest.raises(ValueError):
        FareOctal.from_value(2 * 107)    # 107 outside the window
    assert FareOctal.from_value(1) is UNIT
    assert FareOctal.from_value(0) is ZERO


# -- the Fare product -------------------------------------------------------
def test_product_rules_exact():
    t = lambda n: FareOctal.from_value(n)
    assert t(2) * t(2) is ZERO                    # nilpotency
    assert t(2) * t(3) == t(6)                    # coprime merge
    assert t(2) * t(5) == t(10)
    assert t(6) * t(10) is ZERO                   # gcd 2 > 1
    assert t(15) * t(77) == t(1155)               # 3*5 and 7*11
    assert UNIT * t(6) == t(6)                    # tau_1 = 1
    assert UNIT * UNIT == UNIT                    # 1*1 = 1
    assert ZERO * t(6) is ZERO
    for b in range(N_BITS):
        assert tau(b) * tau(b) is ZERO            # tau_b^2 = 0


def test_product_is_associative_and_commutative():
    rng = random.Random(2026)
    for _ in range(500):
        A = FareOctal({b for b in range(N_BITS) if rng.random() < 0.15})
        B = FareOctal({b for b in range(N_BITS) if rng.random() < 0.15})
        C = FareOctal({b for b in range(N_BITS) if rng.random() < 0.15})
        assert (A * B) * C == A * (B * C)
        assert A * B == B * A


def test_literal_index_rule_divergences():
    # App. A sec. 4.1 read literally on the 0..26 indices:
    assert index_rule_product(5, 7) == 35          # no bit 35: not closed
    assert index_rule_product(1, 1) is None        # nilpotency
    assert index_rule_product(1, 2) == 2           # gcd(1,2)=1
    # (tau_1 tau_1) tau_2 = 0  but  tau_1 (tau_1 tau_2) = tau_2
    lhs = None if index_rule_product(1, 1) is None else \
        index_rule_product(index_rule_product(1, 1), 2)
    assert lhs is None
    assert index_rule_product(1, index_rule_product(1, 2)) == 2


def test_f2_sec_4_2_post_state_matches_no_reading():
    # value reading of tau_3 * tau_5 = tau_15: bits {1,2}
    assert FareOctal.from_value(15).display() == "[0 0 0 0 0 0 0 0 6]"
    # linear-index reading of "tau_15": bit 15 -> D5 = 4th token
    assert FareOctal({15}).display() == "[0 0 0 1 0 0 0 0 0]"
    # the monograph's printed string is bit 9 (prime 29)
    assert FareOctal({9}).display() == "[0 0 0 0 0 1 0 0 0]"
    assert bit_address(9)["prime"] == 29


# -- window algebra ----------------------------------------------------------
def test_fareelement_7_2_completed():
    A = FareElement.from_states(tau(0), tau(1))    # tau_2 + tau_3
    B = FareElement.from_states(tau(0), tau(2))    # tau_2 + tau_5
    P = A * B
    assert P.values() == {10: 1, 6: 1, 15: 1}
    assert len(P.coeffs) == 3


def test_fareelement_matches_fare_algebra_prop():
    rng = random.Random(7)
    checked = 0
    while checked < 200:
        m, n = rng.randrange(1, 10 ** 6), rng.randrange(1, 10 ** 6)
        try:
            SM, SN = FareOctal.from_value(m), FareOctal.from_value(n)
        except ValueError:
            continue
        P = SM * SN
        if gcd(m, n) == 1:
            assert P is not ZERO and P.value() == m * n
        else:
            assert P is ZERO
        checked += 1


def test_spectral_involution_and_zeta():
    # pairing with INTEGER exponents 1-2s: iota_s . iota_{1-s} = id
    for s in (0, 1, 2):
        Z = zeta_element(Fraction(s), 4)
        back = spectral_involution(spectral_involution(Z, Fraction(s)),
                                   Fraction(1 - s))
        assert back == Z
    assert spectral_involution(zeta_element(Fraction(1, 2), 4),
                               Fraction(1, 2)) == \
        zeta_element(Fraction(1, 2), 4)               # critical line: id
    res = functional_equation_identities(r=4)
    assert all(v for v in res.values())


# -- lattice ------------------------------------------------------------------
def test_lattice_tables_exact():
    assert L_TABLE == ((2, 4, 8), (4, 8, 16), (6, 12, 24))
    assert m_value(1, 1, 1) == 4 and m_value(1, 3, 3) == 262144
    assert m_value(2, 2, 2) == 65536
    assert m_value(2, 3, 3) == 68719476736            # "6,87E+10"
    assert m_value(3, 3, 3) == 2 ** 54                 # "1,8E+16"
    assert M_TABLES[3][0][0] == 64
    assert h_exponent(1, 1, 1) == 3 and h_exponent(3, 3, 3) == 81
    assert max(e for row in H_EXPONENTS[3] for e in row) == 81


def test_lattice_sums_and_storage():
    s = lattice_sums()
    assert s["levels"] == {"L": 9, "M": 27, "H": 81}
    assert s["total_points"] == 117 and s["per_axis_sum"] == 39
    # the 27 bits are the 27 H cells; the 9 digits are the (k,i) rows
    cells = {bit_address(L)["cell"] for L in range(27)}
    assert cells == {(i, j, k) for k in (1, 2, 3) for i in (1, 2, 3)
                     for j in (1, 2, 3)}
    assert FORTRESS_NOTE["points"] == 81


# -- census --------------------------------------------------------------------
def test_maximal_state():
    m = FareOctal(frozenset(range(N_BITS)))
    assert m.display() == "[7 7 7 7 7 7 7 7 7]"
    assert m.value() == prod(PRIMES)                  # primorial of 27 primes
    assert m.h_exponent() == 3 * 6 * 6 * 6 == 648
    assert m.h_weight() == 2 ** 648


# -- the full dossier ------------------------------------------------------------
def test_verify_all_checks():
    results = run_checks()
    for k, v in results.items():
        assert v["verdict"].startswith("PASS"), (k, v)


def test_write_report(tmp_path):
    results = run_checks()
    p = write_report(results, str(tmp_path / "VERIFICATION.md"))
    text = open(p, encoding="utf-8").read()
    assert "F1" in text and "F5" in text
    assert "117" in text and "2^27" in text
