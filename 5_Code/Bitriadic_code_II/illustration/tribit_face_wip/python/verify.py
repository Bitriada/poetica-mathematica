"""verify.py -- the verification suite for Tribit Face.

Every structural claim the toy displays is checked here numerically,
each with its monograph source.  The suite also emits selftest.json:
golden vectors that the HTML's JavaScript math core must reproduce
(cross-checked by verify_js.py / the in-browser badge).

Run:  python3 verify.py        (from the python/ directory)
Exit code 0 iff all checks pass.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

from tribit import (UC, TAU, O_matrix, O_matrix_lifted, apply_O_matrix,
                    random_tribit)
import sphere as S
import fare as F

SEED = 42
RNG = random.Random(SEED)
TOL = 1e-9

CHECKS = []       # (id, name, source, ok, detail)
VECTORS = []      # {"op": ..., "in": [...], "out": [...]}


def check(cid: str, name: str, source: str, ok: bool, detail: str = ""):
    CHECKS.append({"id": cid, "name": name, "source": source,
                   "pass": bool(ok), "detail": detail})


def vec(op: str, inp, out, note=""):
    VECTORS.append({"op": op, "in": inp, "out": out, "note": note})


def cz(c: complex):
    """complex -> [re, im]; None stays None (infinity)."""
    if c is None:
        return None
    return [c.real, c.imag]


# ==========================================================================
# 1. UC as a commutative ring with the nilpotent trace
# ==========================================================================

def check_uc():
    xs = [random_tribit(RNG) for _ in range(6)]
    ok = all((x * y).almost(y * x) for x in xs for y in xs)
    check("UC-1", "multiplication commutative", "Ch. IV, UC axioms", ok)

    ok = all(((x * y) * w).almost(x * (y * w))
             for x, y, w in zip(xs, xs[1:], xs[2:]))
    check("UC-2", "multiplication associative", "Ch. IV, UC axioms", ok)

    ok = all((x * (y + w)).almost(x * y + x * w)
             for x, y, w in zip(xs, xs[1:], xs[2:]))
    check("UC-3", "distributivity", "Ch. IV, UC axioms", ok)

    t = TAU()
    check("UC-4", "tau^2 = 0 (trace cannot be duplicated)",
          "Def. 4.2.1", (t * t).almost(UC()))

    i_unit = UC(0.0, 1.0, 0.0, 0.0)
    check("UC-5", "i*tau = tau*i", "Def. 4.2.1",
          (i_unit * t).almost(t * i_unit))

    # Leibniz trace rule: tr(x*y) = val(x) tr(y) + val(y) tr(x)
    ok = True
    for x, y in zip(xs, xs[1:]):
        lhs = (x * y).tr
        rhs = x.val * y.tr + y.val * x.tr
        ok = ok and abs(lhs - rhs) < TOL
    check("UC-6", "Leibniz trace rule = the Fare Principle",
          "Sec. 4.1 (Algebroid definition)", ok)

    z1 = UC(1, 0, 1, 0)          # 1 + tau
    z2 = UC(2, 0, 3, 0)          # 2 + 3 tau
    check("UC-7", "dual arithmetic spot check (1+tau)(2+3tau) = 2+5tau",
          "UC = C[tau]/(tau^2)", (z1 * z2).almost(UC(2, 0, 5, 0)))


# ==========================================================================
# 2. The C8 rotation group
# ==========================================================================

def check_rotations():
    ok = True
    for j in range(8):
        for k in range(8):
            z = random_tribit(RNG)
            lhs = z.rotate(j).rotate(k)
            rhs = z.rotate((j + k) % 8)
            ok = ok and lhs.almost(rhs)
    check("C8-1", "O_j . O_k = O_(j+k mod 8): cyclic group law",
          "Claim 4.2.3.4", ok)

    z = random_tribit(RNG)
    ok = all(z.rotate(0).almost(z) and z.rotate(k).rotate(8 - k).almost(z)
             for k in range(8))
    check("C8-2", "O_0 = id and O_k^-1 = O_(8-k)", "Claim 4.2.3.4", ok)

    ok = all(z.rotate(k).val == z.val or abs(z.rotate(k).val - z.val) < TOL
             for k in range(8))
    check("C8-3", "value plane strictly unchanged by every O_k",
          "Def. 4.2.3.3 / Sec. 4.5.2a", ok)

    t1 = z.rotate(1).tr
    expect = z.tr * complex(math.cos(math.pi / 4), math.sin(math.pi / 4))
    check("C8-4", "O_1 rotates the trace by pi/4", "Def. 4.2.3.3",
          abs(t1 - expect) < TOL)

    ok = all(apply_O_matrix(k, z).almost(z.rotate(k)) for k in range(8))
    check("C8-5", "UC-scale 4x4 matrix matches O_k (value block = identity)",
          "Def. 4.2.3.3 (cf. Prop. 4.2.3.5 tension, README)", ok)

    # the lifted (TFA-scale) matrix rotates value and trace together
    def apply_lifted(k, z0):
        m = O_matrix_lifted(k)
        x = [z0.a, z0.b, z0.c, z0.d]
        y = [sum(m[i][j] * x[j] for j in range(4)) for i in range(4)]
        return UC(*y)
    rot = complex(math.cos(math.pi / 4), math.sin(math.pi / 4))
    ok = (abs(apply_lifted(1, z).val - z.val * rot) < TOL
          and abs(apply_lifted(1, z).tr - z.tr * rot) < TOL)
    check("C8-6", "Prop. 4.2.3.5 two-block matrix = simultaneous value+trace "
          "rotation (the TFA-lifted grammar)", "Prop. 4.2.3.5 + Remark 4.2.3.3a",
          ok,
          "the monograph's matrix disagrees with its own Def. 4.2.3.3 at "
          "UC scale; both readings are implemented and labelled")


# ==========================================================================
# 3. The null-transit gates
# ==========================================================================

def check_gates():
    z = random_tribit(RNG)
    a = z.atlas()
    check("G-1", "atlas 0/a kills the trace, preserves the value",
          "Sec. 4.5.2a", a.tr == 0 and abs(a.val - z.val) < TOL)

    o = z.overdrive()
    check("G-2", "overdrive w/0 lifts the value into the trace (v -> v + tau v)",
          "Sec. 4.5.2a", abs(o.tr - z.val) < TOL and abs(o.val - z.val) < TOL)

    check("G-3", "one-way switch: 0/a (w/0 (v)) = v",
          "Sec. 4.5.2a", z.overdrive().atlas().almost(z.atlas()))

    zs = UC(0.3, -0.5, 0.7, 0.2)   # has a genuine trace
    check("G-4", "the reverse composition loses the trace: w/0 (0/a (z)) != z",
          "Sec. 4.5.2a", not zs.atlas().overdrive().almost(zs))

    check("G-5", "memory depth one: overdrive is idempotent",
          "Sec. 4.5.2a (tau^2 = 0)", z.overdrive().overdrive().almost(o))


# ==========================================================================
# 4. The Fare-Riemann sphere
# ==========================================================================

def check_sphere():
    z = random_tribit(RNG)
    check("S-1", "normalisation lands on S3_FR", "Def. 4.2.4.1",
          abs(z.normalized().norm_fr() - 1.0) < TOL)

    # value-fibers
    v = complex(0.3, 0.2)
    pts = [S.value_fiber_point(v, k * math.pi / 12) for k in range(24)]
    ok = (all(abs(p.val - v) < TOL for p in pts)
          and all(abs(abs(p.tr) - S.value_fiber_radius(v)) < TOL for p in pts)
          and all(abs(p.norm_fr() - 1.0) < TOL for p in pts))
    check("S-2", "value-fiber over v: fixed value, radius sqrt(1-|v|^2), "
          "on the sphere", "Sec. 4.2.4 explicit fibration", ok)

    zs = UC(0.3, 0.2, 0.4, -0.5).normalized()
    orbit = [zs.rotate(k) for k in range(8)]
    ok = (all(abs(p.val - zs.val) < TOL for p in orbit)
          and all(abs(abs(p.tr) - abs(zs.tr)) < TOL for p in orbit))
    check("S-3", "the O_k orbit of a tribit lies on its value-fiber "
          "(rotations navigate the fiber)", "Sec. 4.5.2a", ok)

    # classical Hopf map
    q = complex(0.8, -0.6)
    ok = all(S.hopf_map(S.hopf_fiber_point(q, k * math.pi / 6)) is not None
             and abs(S.hopf_map(S.hopf_fiber_point(q, k * math.pi / 6)) - q) < TOL
             for k in range(12))
    check("S-4", "h(z) = tr/val is constant q on the classical Hopf fiber "
          "{(u, q u)}", "classical S3 -> S2 fibration", ok)

    ok = all(S.hopf_map(S.nadir_point(k * math.pi / 6)) is None
             for k in range(12))
    check("S-5", "fiber at infinity = pure trace (the nadir circle)",
          "Sec. 4.2.4 Prop. 4.2.4.3", ok)

    ok = all(abs(S.hopf_map(S.pure_value_point(k * math.pi / 6))) < TOL
             for k in range(12))
    check("S-6", "fiber over 0 = the pure value circle", "Sec. 4.2.4", ok)

    # the honest tension: same value, different Hopf base
    z1 = S.value_fiber_point(complex(0.5, 0), 0.0)
    z2 = S.value_fiber_point(complex(0.5, 0), math.pi / 2)
    check("S-7", "value-fibers and Hopf fibers are genuinely different "
          "fibrations (same value, different h)", "README honest limits",
          abs(S.hopf_map(z1) - S.hopf_map(z2)) > 0.1,
          "Sec. 4.2.4 calls the value map a Hopf fibration while its "
          "explicit fibers fix the value; both are shown, distinct")

    # nadir
    n = S.nadir_point(1.234)
    check("S-8", "nadir circle: pure transit states (val = 0, |tr| = 1)",
          "Def. 4.2.4.4", abs(n.val) < TOL and abs(abs(n.tr) - 1.0) < TOL)

    # intrinsic metric and the balance torus
    ok = all(p.norm_tau() <= math.sqrt(2.0) + TOL
             for p in (random_tribit(RNG).normalized() for _ in range(500)))
    check("S-9", "intrinsic norm ||z||_tau <= sqrt(2) on the sphere",
          "Def. 4.2.4.6 / Prop. 4.2.4.7", ok)

    b = S.balance_point(0.7, 2.1)
    check("S-10", "the balance torus attains the intrinsic radius sqrt(2)",
          "Prop. 4.2.4.7", abs(b.norm_tau() - math.sqrt(2.0)) < TOL
          and abs(b.norm_fr() - 1.0) < TOL)

    check("S-11", "balance condition |val| = |tr| = 1/sqrt(2): the Clifford "
          "torus (our identification)", "AGS balance, s = 1/2",
          abs(abs(b.val) - 1 / math.sqrt(2)) < TOL
          and abs(abs(b.tr) - 1 / math.sqrt(2)) < TOL)

    ok = True
    for _ in range(200):
        p = random_tribit(RNG).normalized()
        if abs(abs(p.val) - abs(p.tr)) > 1e-3:      # off the balance torus
            ok = ok and p.norm_tau() < math.sqrt(2.0) - 1e-6
    check("S-12", "off-balance points are strictly below the intrinsic "
          "radius (Cauchy-Schwarz equality case)", "our verification", ok)

    # stereographic round trip
    ok = True
    for _ in range(50):
        p = random_tribit(RNG).normalized()
        if p.a > 0.98:
            continue                                # near the pole
        back = S.inv_stereographic(S.stereographic(p))
        ok = ok and back.almost(p, 1e-9)
    check("S-13", "stereographic projection round-trips (away from the pole)",
          "display layer", ok)


# ==========================================================================
# 5. The Fare Algebra
# ==========================================================================

def check_fare():
    check("F-1", "tau_p^2 = 0 for the first primes", "Def. 4.1.1.1",
          F.tau_p_times_tau_p_zero())

    check("F-2", "tau_2 * tau_3 = tau_6 (coprime product)",
          "Def. 4.1.1.1", F.tau(2) * F.tau(3) == F.tau(6))

    check("F-3", "tau_2 * tau_6 = 0 (shared prime dies)",
          "Def. 4.1.1.1", F.tau(2) * F.tau(6) == F.FareElem())

    primes = F.first_primes(5)
    ok = True
    for _ in range(50):
        m = RNG.choice([2, 3, 5, 6, 7, 10, 15, 30])
        n = RNG.choice([2, 3, 5, 6, 7, 10, 15, 30])
        prod = F.tau(m) * F.tau(n)
        if math.gcd(m, n) == 1:
            ok = ok and prod == F.tau(m * n)
        else:
            ok = ok and prod == F.FareElem()
    check("F-4", "coprimality product rule on random pairs",
          "Def. 4.1.1.1", ok)

    ok = all(F.collapse_is_linear(F.random_fare(RNG, primes),
                                  F.random_fare(RNG, primes))
             for _ in range(30))
    check("F-5", "collapse phi_UC : F -> UC is a linear surjection "
          "(addition preserved)", "Sec. 4.5.2a", ok)

    prod = F.tau(2) * F.tau(3)            # tau_6
    lhs = prod.collapse()                 # tau
    rhs = F.tau(2).collapse() * F.tau(3).collapse()   # tau * tau = 0
    check("F-5b", "collapse is NOT multiplicative: phi(tau_2 tau_3) = tau "
          "but phi(tau_2) phi(tau_3) = 0 -- presence, not arithmetic",
          "our verification of Sec. 4.1.5 / 4.5.2a",
          lhs == TAU() and rhs == UC(),
          "the monograph calls phi_UC a linear surjection; a ring "
          "homomorphism reading would be false")

    z = F.tau(2, 0.5 + 0.5j) + F.tau(15, 1 - 2j)
    check("F-6", "spectral involution is the identity at s = 1/2",
          "Claim 4.1.1.7 / Remark 4.2.4.1a",
          z.involution(0.5) == z)

    ok = True
    for _ in range(10):
        s = complex(RNG.uniform(0.1, 0.9), RNG.uniform(-1, 1))
        ok = ok and z.involution(s).involution(1 - s) == z
    check("F-7", "iota_s . iota_(1-s) = id (zeta functional equation "
          "symmetry)", "Claim 4.1.1.5", ok)

    ok = all(F.functional_equation_holds(complex(RNG.uniform(0.2, 0.8),
                                                 RNG.uniform(-1, 1)))
             for _ in range(10))
    check("F-8", "Z(s) = iota_s(Z(1-s)) on the truncated algebra",
          "Claim 4.1.1.6", ok)

    # square-free lattice on the nadir circle
    pts = S.squarefree_lattice_points(max_n=210)
    angs = {n: S.squarefree_label_angle(n) for n, _ in pts}
    ok = True
    for m in angs:
        for n in angs:
            if math.gcd(m, n) == 1 and m * n in angs:
                lhs = (angs[m] + angs[n]) % S.TAU
                d = (angs[m * n] - lhs + S.TAU / 2) % S.TAU - S.TAU / 2
                ok = ok and abs(d) < 1e-9
    check("F-9", "coprime multiplication is angle addition on the nadir "
          "circle (tau_m tau_n = tau_mn)", "Sec. 4.1.5", ok)

    vals = sorted(angs.values())
    sep = min((b - a) for a, b in zip(vals, vals[1:]))
    check("F-10", f"square-free labels are injective under the logarithmic "
          f"height (min separation {sep:.4f} rad)",
          "our instantiation of Sec. 4.1.5", sep > 1e-6)

    ok = all(p.val == 0 and abs(p.norm_fr() - 1.0) < TOL
             for _, p in pts)
    check("F-11", "all lattice points lie on the nadir circle of S3_FR",
          "Sec. 4.1.5 (placement is our instantiation)", ok)


# ==========================================================================
# 6. Golden vectors for the JavaScript cross-check
# ==========================================================================

def build_vectors():
    r = random.Random(2026)   # separate stream, stable across runs
    x, y = random_tribit(r), random_tribit(r)
    vec("add", [x.to_json(), y.to_json()], (x + y).to_json())
    vec("mul", [x.to_json(), y.to_json()], (x * y).to_json(),
        "Leibniz rule: value multiplies, trace cross-adds")
    for k in range(8):
        vec("rotate", [x.to_json(), k], x.rotate(k).to_json())
    vec("atlas", [x.to_json()], x.atlas().to_json(), "gate 0/a")
    vec("overdrive", [x.to_json()], x.overdrive().to_json(), "gate w/0")
    vec("normTau", [x.to_json()], x.norm_tau())
    vec("normFr", [x.to_json()], x.norm_fr())

    z = random_tribit(r).normalized()
    vec("normalize", [x.to_json()], x.normalized().to_json())
    vec("hopf", [z.to_json()], cz(S.hopf_map(z)))
    vec("hopfNadir", [S.nadir_point(1.0).to_json()], cz(S.hopf_map(
        S.nadir_point(1.0))), "infinity encoded as null")
    q = complex(0.8, -0.6)
    vec("hopfFiberPoint", [cz(q), 1.1], S.hopf_fiber_point(q, 1.1).to_json())
    v = complex(0.3, 0.2)
    vec("valueFiberPoint", [cz(v), 2.0],
        S.value_fiber_point(v, 2.0).to_json())
    vec("balancePoint", [0.7, 2.1], S.balance_point(0.7, 2.1).to_json())
    vec("nadirPoint", [2.5], S.nadir_point(2.5).to_json())
    vec("pureValuePoint", [1.3], S.pure_value_point(1.3).to_json())
    p = S.balance_point(0.4, 1.7)
    vec("stereographic", [p.to_json()], list(S.stereographic(p)))
    X = S.stereographic(p)
    vec("invStereographic", [list(X)], S.inv_stereographic(X).to_json())

    for n in [1, 2, 3, 6, 30, 210]:
        vec("labelAngle", [n], S.squarefree_label_angle(n))
    vec("fareMul", [2, 3], 6, "tau_2 tau_3 = tau_6")
    vec("fareMul", [6, 10], 0, "shared prime dies")
    vec("fareMul", [1, 30], 30, "tau_1 is the unit")
    # involution factor n^(1-2s) at s = 0.3 + 0.2i for n = 6
    s = complex(0.3, 0.2)
    vec("involutionFactor", [6, cz(s)],
        cz(complex(6) ** (1.0 - 2.0 * s)))
    # collapse of a small fare element: coeffs {1: v, 6: t}
    v0, t0 = 0.7 - 0.2j, 0.4 + 0.9j
    fe = F.FareElem({1: v0, 6: t0})
    vec("collapse", [cz(v0), 6, cz(t0)], fe.collapse().to_json(),
        "tau_1 -> value, tau_n (n>1) -> trace")


# ==========================================================================
# main
# ==========================================================================

def main() -> int:
    check_uc()
    check_rotations()
    check_gates()
    check_sphere()
    check_fare()
    build_vectors()

    passed = sum(1 for c in CHECKS if c["pass"])
    width = max(len(c["id"]) for c in CHECKS)
    for c in CHECKS:
        mark = "PASS" if c["pass"] else "FAIL"
        line = f"[{mark}] {c['id']:<{width}}  {c['name']}"
        if not c["pass"] and c["detail"]:
            line += f"   -- {c['detail']}"
        print(line)
    print(f"\n{passed}/{len(CHECKS)} checks passed, "
          f"{len(VECTORS)} golden vectors emitted")

    out = {
        "project": "Tribit Face",
        "generated": "2026-11-18",
        "seed": SEED,
        "tolerance": 1e-9,
        "checks": CHECKS,
        "vectors": VECTORS,
    }
    dest = Path(__file__).parent / "selftest.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"selftest.json written to {dest}")

    if passed != len(CHECKS):
        print("FAILURES PRESENT", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
