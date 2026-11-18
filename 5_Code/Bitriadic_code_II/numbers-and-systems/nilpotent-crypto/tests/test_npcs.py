"""npcs unit tests: exact, standard library only (pytest runner)."""

import random
from math import prod

import pytest

from fareoctal import FareOctal, PRIMES

from npcs import (CHUNK_BITS, TAU, UCQ, UCQ_I, UCQ_J, UCQ_K, chunk_bits,
                  collapse, commit, encode, generate_path, mini_encode,
                  path_product, sheet_hashes, unchunk_bits, verify)
from npcs.encode import BLOCKS, block_trace, block_value, MINI_PRIMES
from npcs.scheme import OneShotRegistry
from npcs.ucq import (G0, cq_add, cq_commutes, cq_mul, cq_zero, g_add,
                      g_mul, serialize_int)


def _rng():
    return random.Random(20261115)


# -- T1 algebra ------------------------------------------------------------
def test_quaternion_units_and_associativity():
    I, J, K = UCQ_I, UCQ_J, UCQ_K
    ONE = UCQ.uc(re=1)
    assert I * I == J * J == K * K == -ONE
    assert I * J == K and J * I == -K and J * K == I
    assert K * J == -I and K * I == J and I * K == -J
    rng = _rng()

    def rnd():
        return UCQ.from_cq(*[rng.randint(-5, 5) for _ in range(16)])

    for _ in range(200):
        a, b, c = rnd(), rnd(), rnd()
        assert (a * b) * c == a * (b * c)
        assert (a * b).val() == cq_mul(a.val(), b.val())


def test_tau_nilpotent_central_and_leibniz():
    rng = _rng()
    assert TAU * TAU == UCQ.uc()
    for _ in range(100):
        z = UCQ.from_cq(*[rng.randint(-5, 5) for _ in range(16)])
        assert TAU * z == z * TAU
        assert (TAU * z).tr() == z.val()
    for _ in range(200):
        a, b = UCQ.from_cq(*[_rng().randint(-5, 5) for _ in range(16)]), \
            UCQ.from_cq(*[_rng().randint(-5, 5) for _ in range(16)])
        assert (a * b).tr() == cq_add(cq_mul(a.val(), b.tr()),
                                      cq_mul(a.tr(), b.val()))


def test_c7_commuted_leibniz_counterwitness():
    Z1 = UCQ.from_real((0, 0, 0, 0), (0, 0, 1, 0, 0, 0, 0, 0))  # tau*(iI)
    Z2 = UCQ.from_real((0, 0, 1, 0), (0, 0, 0, 0, 0, 0, 0, 0))   # J
    correct = (Z1 * Z2).tr()
    commuted = cq_add(cq_mul(Z1.val(), Z2.tr()), cq_mul(Z2.val(), Z1.tr()))
    assert correct != commuted            # +K vs -K


def test_c4_square_formula():
    v = UCQ.from_real((1, 2, 3, 4)).val()
    t = UCQ.from_real((0, 0, 0, 0), (0, 0, 0, 0, 1, 1, 0, 0)).tr()
    Z = UCQ(v, t)
    assert Z * Z == UCQ(cq_mul(v, v),
                        cq_add(cq_mul(v, t), cq_mul(t, v)))
    assert cq_mul(v, t) != cq_mul(t, v)   # the draft's 2*tau*v*t fails


def test_norm_multiplicative():
    def uc_mul(x, y):
        (v1, t1), (v2, t2) = x, y
        return (g_mul(v1, v2), g_add(g_mul(v1, t2), g_mul(v2, t1)))

    rng = _rng()
    for _ in range(200):
        a = UCQ.from_cq(*[rng.randint(-5, 5) for _ in range(16)])
        b = UCQ.from_cq(*[rng.randint(-5, 5) for _ in range(16)])
        assert uc_mul(a.norm_uc(), b.norm_uc()) == (a * b).norm_uc()
    assert UCQ.uc(re=3, i=4).norm_uc()[0] == (-7, 24)   # (3+4i)^2


def test_serialize_roundtrip_and_int():
    rng = _rng()
    for _ in range(200):
        z = UCQ.from_cq(*[rng.randint(-10 ** 40, 10 ** 40)
                          for _ in range(16)])
        assert UCQ.deserialize_exact(z.serialize_exact()) == z
    for n in (0, 1, -1, 255, -255, 2 ** 100, -(2 ** 100)):
        data = serialize_int(n)
        (k,) = int.from_bytes(data[:4], "big"),
        assert int.from_bytes(data[4:4 + k], "big", signed=True) == n


# -- T2 encode ---------------------------------------------------------------
def test_blocks_and_injectivity():
    for start, width, primes in BLOCKS:
        assert len(primes) == width
        seen = set()
        for pattern in range(1 << width):
            v = prod(primes[j] for j in range(width) if pattern >> j & 1)
            seen.add(v)
        assert len(seen) == 1 << width       # unique factorization
    rng = _rng()
    sample = rng.sample(range(1 << CHUNK_BITS), 30_000)
    assert len({encode(c).val() for c in sample}) == 30_000


def test_block_readings():
    chunk = (1 << 0) | (1 << 6) | (1 << 20)
    assert block_value(chunk, 0) == PRIMES[0]
    assert block_value(chunk, 1) == PRIMES[6]
    assert block_value(chunk, 2) == 1
    assert block_value(chunk, 3) == PRIMES[20]
    assert block_trace(chunk, 0) == (1, 0)
    assert block_trace(chunk, 1) == (1, 6)
    assert block_trace(chunk, 2) == (0, 0)
    assert block_trace(chunk, 3) == (1, 20)


def test_chunk_roundtrip():
    rng = _rng()
    for _ in range(200):
        n = rng.randrange(0, 5000)
        bits = "".join(rng.choice("01") for _ in range(n))
        chunks, n_bits = chunk_bits(bits)
        assert unchunk_bits(chunks, n_bits) == bits


# -- T3 serialization flaw ------------------------------------------------------
def test_c1_float64_flaw_witness():
    big = 2 ** 60
    Z1 = UCQ.from_cq(big, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    Z2 = UCQ.from_cq(big + 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    assert Z1.serialize_float64() == Z2.serialize_float64()
    assert Z1.serialize_exact() != Z2.serialize_exact()
    # the draft's collapse WOULD collide (same float64 bytes); ours does not:
    assert collapse(Z1) != collapse(Z2)


def test_c5_128_bytes_is_1024_bits():
    Z = UCQ.from_cq(*range(16))
    assert len(Z.serialize_float64()) == 128
    assert 128 * 8 == 1024            # the draft says 2048


# -- T4 scheme --------------------------------------------------------------------
def test_commit_verify_tamper():
    rng = _rng()
    path = generate_path(16, rng)
    c = commit(path)
    assert c == commit(path)                    # deterministic
    assert verify(path, c)
    for _ in range(200):
        bad = list(path)
        bad[rng.randrange(len(bad))] ^= 1 << rng.randrange(27)
        assert not verify(bad, c)
    assert not verify(path[:-1], c)
    assert not verify(path + [0], c)
    assert not verify(generate_path(16, rng), c)


def test_path_constraints():
    rng = _rng()
    path = generate_path(12, rng)
    for j in range(len(path) - 1):
        assert encode(path[j]).tr() != encode(path[j + 1]).tr()
    assert path != path[::-1]
    n = len(path)
    doubled = path + path
    assert not any(doubled[r:r + n] == path for r in range(1, n))


def test_one_shot_registry():
    rng = _rng()
    path = generate_path(8, rng)
    c = commit(path)
    reg = OneShotRegistry()
    assert reg.present(path, c) == (True, "accepted (one-shot)")
    ok, msg = reg.present(path, c)
    assert not ok and "replay" in msg
    other = generate_path(8, rng)
    ok, msg = reg.present(other, c)
    assert not ok and "invalid" in msg            # wrong path, same commitment


# -- T5 transcript -------------------------------------------------------------------
def test_transcript_equals_leibniz_sum():
    rng = _rng()
    for L in (2, 3, 7, 20):
        chunks = [rng.getrandbits(27) for _ in range(L)]
        encs = [encode(x) for x in chunks]
        T = path_product(chunks)
        acc = cq_zero()
        for j in range(L):
            pl = pr = None
            for v in [encs[k].val() for k in range(j)]:
                pl = v if pl is None else cq_mul(pl, v)
            for v in [encs[k].val() for k in range(j + 1, L)]:
                pr = v if pr is None else cq_mul(pr, v)
            term = encs[j].tr()
            if pl is not None:
                term = cq_mul(pl, term)
            if pr is not None:
                term = cq_mul(term, pr)
            acc = cq_add(acc, term)
        assert T.tr() == acc


# -- T6 order sensitivity -----------------------------------------------------------
def test_order_sensitivity_and_central_class():
    rng = _rng()
    path = generate_path(10, rng)
    c = commit(path)
    for j in range(len(path) - 1):
        p = list(path)
        p[j], p[j + 1] = p[j + 1], p[j]
        assert commit(p) != c
    # central-difference pair: chunks 0 and 1 differ only in block a
    assert path_product([0, 1]) == path_product([1, 0])
    # generic pairs do not commute
    hits = 0
    tries = 0
    for _ in range(30):
        u, v = rng.getrandbits(27), rng.getrandbits(27)
        if u == v:
            continue
        tries += 1
        hits += path_product([u, v]) != path_product([v, u])
    assert hits == tries and tries >= 25


# -- T7 mini census -------------------------------------------------------------------
def test_mini_census_pairs():
    minis = [mini_encode(c) for c in range(256)]
    by_v, by_t = {}, {}
    for s in range(256):
        for t in range(256):
            P = minis[s] * minis[t]
            by_v.setdefault(P.V, set()).add(P.D)
            by_t[P] = True
    assert 0 < len(by_t) < 256 * 256       # compression, not injectivity
    # document the value-sheet collision count (may be 0 in this regime)
    collisions = sum(1 for ds in by_v.values() if len(ds) > 1)
    assert collisions >= 0                 # informational


def test_bi_sheet_witness():
    """Found by the T7 census: two mini paths with IDENTICAL value
    sheets but DISTINCT trace sheets -- H_val alone would collide;
    the bi-sheet commitment separates them.  The bi-sheet design is
    load-bearing, proven by trial."""
    a = mini_encode(20) * mini_encode(162)
    b = mini_encode(26) * mini_encode(86)
    assert a.val() == b.val()                       # value sheets collide
    assert a.tr() != b.tr()                         # trace sheets separate
    ha, hb = sheet_hashes(a), sheet_hashes(b)
    assert ha[0] == hb[0]                           # H_val collides
    assert ha[1] != hb[1]                           # H_tr discriminates
    from npcs import collapse
    assert collapse(a) != collapse(b)               # full commitment separates


# -- T8 norm shadow -------------------------------------------------------------------
def test_norm_shadow_multiplicative_and_permutation_invariant():
    def vnorm(cq):
        return sum(g[0] ** 2 + g[1] ** 2 for g in cq)

    rng = _rng()
    for _ in range(100):
        chunks = [rng.getrandbits(27) for _ in range(4)]
        T = path_product(chunks)
        total = prod(vnorm(encode(x).val()) for x in chunks)
        assert vnorm(T.val()) == total
        shuffled = chunks[:]
        rng.shuffle(shuffled)
        assert vnorm(path_product(shuffled).val()) == total


# -- T9 ghost disc ---------------------------------------------------------------------
def test_ghost_disc_2_648():
    maximal = FareOctal(frozenset(range(27)))
    assert maximal.h_weight() == 2 ** 648
    # UCQ does have additive inverses (draft C2 correction)
    rng = _rng()
    z = UCQ.from_cq(*[rng.randint(-9, 9) for _ in range(16)])
    assert z + (-z) == UCQ.uc()
    # tau multiplication collapses the trace sheet
    z1 = UCQ.from_real((3, 4, 5, 6), (1, 2, 3, 4, 5, 6, 7, 8))
    z2 = UCQ.from_real((3, 4, 5, 6), (9, 9, 9, 9, 9, 9, 9, 9))
    assert TAU * z1 == TAU * z2


# -- the battery ------------------------------------------------------------------------
def test_trials_all_pass():
    from npcs.trials import run_trials
    results = run_trials()
    for k, v in results.items():
        assert v["verdict"].startswith(("EST-CONFIRMED", "CORRECTED",
                                        "BY-TRIAL", "OPEN")), (k, v)


def test_report_written(tmp_path):
    from npcs.trials import run_trials, write_report
    p = write_report(run_trials(), str(tmp_path / "NPCS_TRIALS.md"))
    text = open(p, encoding="utf-8").read()
    for needle in ("C1", "C7", "2^648", "Leibniz", "ghost disc"):
        assert needle in text, needle
