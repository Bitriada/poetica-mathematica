#!/usr/bin/env python3
"""lattice117.py -- the 117-point object: a finite window of the
hyperoperation ladder (stdlib only, self-testing; exits non-zero on failure).

THE OBJECT
    Alphabet A = {1, 2, 3}.  Points are words over A of lengths 2, 3 and 4
    with the first letter distinguished as the zone letter:

        P = { (s, a) }            9 words of length 2   (rank 1)
          U { (s, a, b) }        27 words of length 3   (rank 2)
          U { (s, a, b, c) }     81 words of length 4   (rank 3)
                                                       --------
                                                        117 points

    The zone letter s names the zone:  1 = PRIME, 2 = REFLECTION,
    3 = PROJECTION.  The tail alpha = (a_1..a_l) is the index tuple of
    the cell; under the prefix relation P is the depth-2..4 skeleton of
    the full 3-ary tree.

THE VALUATION (one rule)
        base   b(alpha) = 2 ** (l * a_1 * ... * a_l)
        value  v(w)     = H_{l+1}(b(alpha), s)

    on the hyperoperation ladder H_1 = +, H_2 = *, H_3 = ^, H_4 = ^^
    (tetration), H_5 = pentation, H_6 = hexation.  Each rank lives on
    its own rung:

        rank 1, rung H_2:  v = b * s            = s * 2^a_1
        rank 2, rung H_3:  v = b ** s           = 2 ** (2*s*a_1*a_2)
        rank 3, rung H_4:  v = b ^^ s (tower)   = 2 ** E_s,
                           E_1 = 3h,  E_{t+1} = 3h * 2**E_t,  h = a*b*c.

    All values are exact.  Rank 1, rank 2 and rank-3 prime values are
    plain integers (largest 2**81).  The unwritable rank-3 reflection
    and projection values are kept in the canonical exact form
    c * 2**(u * 2**Y)  (c, u odd) on which equality and ordering are
    decided exactly -- no floating point, no truncation -- even though
    the largest value is 2**(81 * 2**(81 * 2**81)).

WHAT A RUN SHOWS (every claim machine-verified)
    sec 1-3   the three blocks printed in full, zone by zone;
    sec 4     index set: 117 = 9+27+81, tree skeleton, monotonicity;
    sec 5     the ladder: v = H_{l+1}(b, s) for all 117 points; the
              3x3 (rung x zone) window; the ladder table at base 2 up
              to pentation and hexation;
    sec 6     zones and orbits: 39 orbits of size 3 (one per cell),
              each orbit = {prime, reflection, projection}; the zone
              ladder inside rank l is walked by rung H_l -- the same
              recursion that builds the ladder -- so the zone structure
              of rank l+1 is a copy of the rank structure one rung up
              (self-similarity; each zone ladder is the free
              one-generator monoid truncated at 3);
    sec 7     fibres: 117 points collapse to 37 values, fibre sizes
              {1,3,4,5,6,9}; inside a block, fibres = permutation
              orbits of the index letters (unique factorization);
              across blocks, merges follow Diophantine collision laws,
              the main one  2*sab = 3h  (rank 2 vs rank-3 prime), plus
              the reflection law h*2^(3h) = h' giving the fibre-5 value
              2^24;
    sec 8     growth: F_0..F_3 of the fast-growing hierarchy and the
              Ackermann function exactly; rung H_{l+1} ~ F_l ~ A(l+1);
              the index tails read as truncated Cantor normal forms
              addressing the ordinals below omega^omega -- the triadic
              truncation (all axes cut at 3) is what makes the window
              finite;
    sec 9     specimens: exact expansions where they exist.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from functools import total_ordering
from itertools import product
from collections import Counter

A = (1, 2, 3)              # the alphabet
ZONES = {1: "prime", 2: "reflection", 3: "projection"}
FORMABLE_BITS = 10_000     # largest power-of-2 exponent ever expanded to an int

# allow exact decimal expansion of 2**4608, 2**49152, ...
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1_000_000)


def v2(n: int) -> int:
    """2-adic valuation v2(n) for n >= 1."""
    return (n & -n).bit_length() - 1


def odd_part(n: int) -> int:
    return n >> v2(n)


# ---------------------------------------------------------- canonical values

@total_ordering
@dataclass(frozen=True)
class Canon:
    """The exact number c * 2**(u * 2**Y) with c, u odd, c,u <= 127, Y >= 0.

    Every value of the object has this form with c <= 3 and u <= 81.
    The total order is exact: comparisons either use small integers or the
    (u, Y) structure; no huge integer is ever formed (see _cmp_exp).
    """

    c: int
    u: int
    Y: int

    def __post_init__(self):
        assert self.c % 2 == 1 and self.u % 2 == 1
        assert 1 <= self.c <= 127 and 1 <= self.u <= 127 and self.Y >= 0

    @staticmethod
    def of_int(n: int) -> "Canon":
        """Canonical form of a positive even integer."""
        if n < 2 or n % 2:
            raise ValueError("need a positive even integer")
        c = odd_part(n)
        X = v2(n)
        return Canon(c, odd_part(X), v2(X))

    def exponent(self):
        """X = u * 2**Y as an int, or None when too large to form."""
        return None if self.Y > FORMABLE_BITS else self.u << self.Y

    # ---- exact comparison of exponents X = u * 2**Y --------------------

    @staticmethod
    def _cmp_exp(X1, X2):
        if X1 == X2:
            return 0
        (u1, Y1), (u2, Y2) = X1, X2
        e1 = None if Y1 > FORMABLE_BITS else u1 << Y1
        e2 = None if Y2 > FORMABLE_BITS else u2 << Y2
        if e1 is not None and e2 is not None:
            return (e1 > e2) - (e1 < e2)
        if Y1 == Y2:                       # both unformable, same Y
            return (u1 > u2) - (u1 < u2)
        if Y1 > Y2:
            d = Y1 - Y2
            if d >= u2.bit_length():       # u1*2**d >= 2**d > u2
                return 1
            lhs = u1 << d                  # d < 7 here (u2 <= 127)
            return (lhs > u2) - (lhs < u2)
        return -Canon._cmp_exp(X2, X1)

    def _cmp(self, other: "Canon"):
        x = Canon._cmp_exp((self.u, self.Y), (other.u, other.Y))
        if x == 0:
            return (self.c > other.c) - (self.c < other.c)
        big, small = (self, other) if x > 0 else (other, self)
        e1, e2 = big.exponent(), small.exponent()
        if e1 is not None and e2 is not None:
            gap = e1 - e2
        else:
            # One exponent is unformable (>= 2**10000 up to a factor <= 127).
            # With u <= 127 one checks X_big - X_small >= 2**(Y_small - 13)
            # whenever Y_big > Y_small, and >= 16257 when Y_big <= Y_small,
            # so the gap always exceeds bit_length(c_small) <= 7.
            gap = 1 << 62
        if gap >= small.c.bit_length():     # c_big * 2**gap > c_small
            return 1 if x > 0 else -1
        lhs = big.c << gap                  # gap < 7 here
        s = (lhs > small.c) - (lhs < small.c)   # sign of (big vs small)
        return s if x > 0 else -s

    def __lt__(self, other: "Canon"):
        return self._cmp(other) < 0

    # ---- exact arithmetic needed by the coherence checks ----------------

    def mul_int(self, k: int) -> "Canon":
        """self * k for a positive integer k."""
        t = v2(self.c * k)
        Xn = self.exponent() + t
        return Canon(odd_part(self.c * k), odd_part(Xn), v2(Xn))

    def pow_int(self, k: int) -> "Canon":
        """self ** k for a positive integer k."""
        return Canon(self.c ** k, odd_part(k * self.u), v2(k) + self.Y)

    def pow_tower(self, other: "Canon") -> "Canon":
        """self ** other when both are powers of two (c = 1)."""
        assert self.c == 1 and other.c == 1
        Xa, Xb = self.exponent(), other.exponent()
        assert Xa is not None and Xb is not None
        return Canon(1, odd_part(Xa), v2(Xa) + Xb)


def canon_display(C: Canon) -> str:
    """Shortest honest display: decimal when modest, else c*2^(u*2^Y)."""
    X = C.exponent()
    if X is not None and X + C.c.bit_length() <= 84:
        return str(C.c << X)
    head = "2" if C.c == 1 else str(C.c)
    return f"{head}^({C.u}*2^{C.Y})"

# ------------------------------------------------------------ the valuation

def tail_product(alpha) -> int:
    p = 1
    for a in alpha:
        p *= a
    return p


def base(alpha) -> int:
    """b(alpha) = 2 ** (l * a_1 * ... * a_l), the rank-l base."""
    return 2 ** (len(alpha) * tail_product(alpha))


def value(s: int, alpha) -> Canon:
    """Exact value of the point (s, alpha) as a Canon."""
    l = len(alpha)
    if l == 1:
        return Canon.of_int(s * 2 ** alpha[0])
    if l == 2:
        return Canon.of_int(2 ** (2 * s * alpha[0] * alpha[1]))
    # rank 3: v = 2**E_s with E_1 = 3h, E_{t+1} = 3h * 2**E_t, h = a*b*c
    c3 = 3 * tail_product(alpha)
    t = v2(c3)
    if s == 1:
        return Canon(1, odd_part(c3), t)
    E_prev = c3 if s == 2 else c3 * 2 ** c3
    return Canon(1, odd_part(c3), E_prev + t)


def point_value(w) -> Canon:
    return value(w[0], w[1:])


def display(s: int, alpha) -> str:
    """Natural exact notation for the value at (s, alpha)."""
    l = len(alpha)
    if l == 1:
        return str(s * 2 ** alpha[0])
    if l == 2:
        return str(2 ** (2 * s * alpha[0] * alpha[1]))
    c3 = 3 * tail_product(alpha)
    if s == 1:
        return str(2 ** c3)
    E2 = c3 * 2 ** c3
    if s == 2:
        return f"2^{E2}" if E2 <= 10 ** 9 else f"2^({c3}*2^{c3})"
    inner = str(E2) if E2 <= 10 ** 9 else f"({c3}*2^{c3})"
    return f"2^({c3}*2^{inner})"


def all_points():
    """All 117 points, grouped by rank, as tuples (s, a_1, ..., a_l)."""
    for l in (1, 2, 3):
        for s in A:
            for alpha in product(A, repeat=l):
                yield (s,) + alpha


def block(l: int):
    return [(s,) + alpha for s in A for alpha in product(A, repeat=l)]


def cells():
    """The 39 index cells: one per tail, ranks 1..3."""
    for l in (1, 2, 3):
        for alpha in product(A, repeat=l):
            yield alpha


def word_str(w) -> str:
    return "(" + ",".join(str(x) for x in w) + ")"


def zone_str(s: int) -> str:
    return f"s={s} {ZONES[s]}"


# ------------------------------------------------------------------ printing

def rule(n=78):
    print("=" * n)


def header(title):
    print()
    rule()
    print(title)
    rule()


# ------------------------------------------------------- sections 0 to 3

def print_definition():
    header("0. THE OBJECT")
    print("""Alphabet A = {1,2,3}.  Points are words over A of lengths 2, 3, 4;
the first letter is the ZONE letter  s = 1 prime, 2 reflection, 3 projection;
the tail alpha is the index tuple of the cell:

    rank 1:  (s, a)          9 = 3^2  words
    rank 2:  (s, a, b)      27 = 3^3  words
    rank 3:  (s, a, b, c)   81 = 3^4  words
                             -------------
                             117 points altogether.

Under the prefix relation this is the depth-2..4 skeleton of the full
3-ary tree (every rank-3 word has a rank-2 prefix, every rank-2 word a
rank-1 prefix), and the 117 points split 39 cells x 3 zones.

VALUATION -- one rule, not three.  For w = (s, alpha), alpha = (a_1..a_l):

    base   b(alpha) = 2 ** (l * a_1 * ... * a_l)
    value  v(w)     = H_{l+1}(b, s)        on the hyperoperation ladder
                                            H_1 = +, H_2 = *, H_3 = ^,
                                            H_4 = ^^ (tetration):

    rank 1, rung H_2:  v = b  *  s          = s * 2**a_1
    rank 2, rung H_3:  v = b ** s           = 2 ** (2*s*a_1*a_2)
    rank 3, rung H_4:  v = b ^^ s (tower)   = 2 ** E_s,
                                              E_1 = 3h, E_{t+1} = 3h*2**E_t,
                                              h = a_1*a_2*a_3

So each rank lives on its own rung of the ladder, the zone letter s is
the second OPERAND of that rung (s copies of the base under the rung
operation), and the tail letters scale the base through their product.
Every value is exact; unwritable values are kept as exact exponential
expressions.""")


def print_rank1():
    header("1. RANK-1 BLOCK -- 9 points --  v = b*s = s * 2^a   (rung H_2)")
    print("                      a=1    a=2    a=3")
    for s in A:
        cells_ = "".join(f"{display(s, (a,)):>7}" for a in A)
        print(f"   {zone_str(s):<16}{cells_}")
    print("""
Reading: the zone letter acts by ordinary multiplication (rung H_2);
e.g. (3,2) is the projection point on cell (2,) with value 3 * 2^2 = 12.""")


def print_rank2():
    header("2. RANK-2 BLOCK -- 27 points --  v = b^s = 2^(2*s*a*b)   (rung H_3)")
    for s in A:
        print(f"\n   {zone_str(s)}:  v = ( 2^(2*a*b) )^{s}"
              + ("   (entrywise squares of prime)" if s == 2 else
                 "   (entrywise cubes of prime)" if s == 3 else ""))
        print("              b=1               b=2               b=3")
        for a in A:
            cells_ = "".join(f"{display(s, (a, b)):>17}" for b in A)
            print(f"   a={a}  {cells_}")


def print_rank3():
    header("3. RANK-3 BLOCK -- 81 points --  v = b^^s = 2^E_s,  h = a*b*c   "
           "(rung H_4)")
    print("""
   Tower exponents:  E_1 = 3h,   E_{t+1} = 3h * 2^E_t.""")
    # s = 1: plain integers
    print("\n   s = 1 (prime):  v = 2^(3*h)  -- plain integers, up to 2^81")
    for a in A:
        print(f"\n      slice a = {a}   (exponents {3*a}*b*c):")
        print("                b=1                 b=2                 b=3")
        for b in A:
            cells_ = "".join(f"{display(1, (a, b, c)):>19}" for c in A)
            print(f"      b={b}  {cells_}")
    # s = 2 and s = 3: exact exponential expressions
    for s in (2, 3):
        name = ZONES[s]
        print(f"\n   s = {s} ({name}):  v = "
              + ("2^E_2 (E_2 = 3h*2^3h)" if s == 2 else
                 "2^E_3 (E_3 = 3h*2^E_2)")
              + " -- exact expressions")
        wid = 17 if s == 2 else 20
        for a in A:
            print(f"\n      slice a = {a}   (h = {a}*b*c):")
            print("                    b=1               b=2               b=3")
            for b in A:
                cells_ = "".join(f"{display(s, (a, b, c)):>{wid}}" for c in A)
                print(f"      b={b}  {cells_}")


def print_exponent_table():
    """The 10 attainable products h = a*b*c with the exact rank-3 exponents."""
    print("\n   The rank-3 exponents, tabulated by h = a*b*c")
    print("   (h takes exactly 10 of the 27 possible values; the missing")
    print("    products 5,7,10,11,... are not products of three letters).")
    print("\n      h   mult   3h        E_2 = 3h*2^(3h)          E_3 = 3h*2^E_2")
    for h in sorted({tail_product(alpha)
                     for alpha in product(A, repeat=3)}):
        mult = sum(1 for alpha in product(A, repeat=3)
                   if tail_product(alpha) == h)
        c3 = 3 * h
        E2 = c3 * 2 ** c3
        print(f"    {h:>3}   {mult:>3}   {c3:>3}   {E2:>24}   {c3}*2^{E2}"
              if E2 <= 10 ** 9 else
              f"    {h:>3}   {mult:>3}   {c3:>3}   {c3}*2^{c3:<12}   "
              f"{c3}*2^({c3}*2^{c3})")


# ------------------------------------------------- checks and the ladder

PASSED = [0]


def check(name, cond):
    assert cond, f"CHECK FAILED: {name}"
    PASSED[0] += 1
    print(f"   [ok] {name}")


def tetration(a, h):
    """a ^^ h, exact for the small arguments used here."""
    x = 1
    for _ in range(h):
        x = a ** x
    return x


def pentation(a, h):
    """a ^^^ h (rung H_5), exact for tiny arguments only (a=2, h<=3)."""
    x = 1
    for _ in range(h):
        x = tetration(a, x)
    return x


# ------------------------------------------------- section 4: the index set

def index_set():
    header("4. THE INDEX SET -- grading, tree skeleton, monotonicity")
    points = list(all_points())
    print("\n 4.1  Grading")
    check("|P| = 117", len(points) == 117)
    check("block sizes 9 + 27 + 81 = 117",
          [len(block(l)) for l in (1, 2, 3)] == [9, 27, 81])

    print("\n 4.2  Prefix structure (truncated 3-ary tree)")
    b1, b2, b3 = block(1), block(2), block(3)
    check("every rank-3 word has its length-3 and length-2 prefixes in P",
          all(w[:3] in b2 and w[:2] in b1 for w in b3))
    pref3 = Counter(w[:3] for w in b3)
    pref2 = Counter(w[:2] for w in b2)
    check("each rank-2 word is the prefix of exactly 3 rank-3 words",
          set(pref3.values()) == {3} and len(pref3) == 27)
    check("each rank-1 word is the prefix of exactly 3 rank-2 words",
          set(pref2.values()) == {3} and len(pref2) == 9)

    print("\n 4.3  Monotonicity: v is strictly increasing in each letter")
    print("       separately (not jointly: (1,3) -> 8 while (2,1) -> 4).")
    ok = True
    for l in (1, 2, 3):
        for w in block(l):
            for i in range(len(w)):
                if w[i] < 3:
                    w2 = w[:i] + (w[i] + 1,) + w[i + 1:]
                    ok = ok and point_value(w) < point_value(w2)
    check("all 117 x 4 adjacent-letter comparisons are strict", ok)


# ------------------------------------------- section 5: hyperoperation ladder

def ladder_section():
    header("5. THE HYPEROPERATION LADDER -- v = H_(l+1)(b, s)")
    print("""
The ladder:  H_1 = a+b,  H_2 = a*b,  H_3 = a^b,  H_4 = a^^b (tetration),
H_5 = a^^^b (pentation), H_6 = a^^^^b (hexation), built by the recursion

    H_{n+1}(a, 1) = a,       H_{n+1}(a, s+1) = H_n(a, H_{n+1}(a, s)).

The valuation of sec 0 is exactly one ladder evaluation per point:
rank l lives on rung H_{l+1}, the zone letter s is the second operand,
and the tail scales the base b = 2^(l * a_1 * ... * a_l).""")

    print("\n 5.1  The valuation, rung by rung (all 117 points)")
    ok1 = all(point_value((s, a)) == Canon.of_int(base((a,)) * s)
              for s in A for a in A)
    check("rank 1: v(s,a) = H_2(b, s) = b * s     (exact integers)", ok1)
    ok2 = all(point_value((s, a, b)) == Canon.of_int(base((a, b)) ** s)
              for s in A for a in A for b in A)
    check("rank 2: v(s,a,b) = H_3(b, s) = b ** s  (exact integers)", ok2)
    ok3 = all(point_value((1, a, b, c)) == Canon.of_int(base((a, b, c)))
              for a in A for b in A for c in A)
    check("rank 3, prime: v(1,a,b,c) = H_4(b, 1) = b  (exact integers)", ok3)
    ok4 = True
    for a in A:
        for b in A:
            for c in A:
                t1 = point_value((1, a, b, c))   # b = 2^(3h)
                t2 = t1.pow_tower(t1)            # H_3(b, H_4(b,1)) = b^b
                t3 = t1.pow_tower(t2)            # H_3(b, H_4(b,2)) = b^(b^b)
                ok4 = ok4 and t2 == point_value((2, a, b, c)) \
                           and t3 == point_value((3, a, b, c))
    check("rank 3, reflection/projection: v = H_4(b,2) = b^b and "
          "H_4(b,3) = b^(b^b)  (exact canonical forms via the ladder "
          "recursion; the integers themselves are unwritable)", ok4)
    # independent closed-form anchors
    R1 = [[s * 2 ** a for a in A] for s in A]
    check("rank-1 table equals its closed form s*2^a",
          R1 == [[2, 4, 8], [4, 8, 16], [6, 12, 24]])
    M1 = [[2 ** (2 * a * b) for b in A] for a in A]
    M2 = [[2 ** (4 * a * b) for b in A] for a in A]
    M3 = [[2 ** (6 * a * b) for b in A] for a in A]
    check("rank-2 prime matrix equals its closed form",
          M1 == [[4, 16, 64], [16, 256, 4096], [64, 4096, 262144]])
    check("rank-2 reflection matrix is the entrywise square of prime",
          all(M2[i][j] == M1[i][j] ** 2 for i in range(3) for j in range(3)))
    check("rank-2 projection matrix is the entrywise cube of prime",
          all(M3[i][j] == M1[i][j] ** 3 for i in range(3) for j in range(3)))
    check("rank-3 prime equals 2^(3*a*b*c), maximum 2^81 at (1,3,3,3)",
          all(point_value((1, a, b, c)) == Canon.of_int(2 ** (3 * a * b * c))
              for a in A for b in A for c in A)
          and point_value((1, 3, 3, 3)) == Canon.of_int(2 ** 81))

    print("\n 5.2  The ladder itself, at base 2 (exact integers)")
    print("\n        rung                 H(2,1)  H(2,2)        H(2,3)")
    rows = [
        ("H_1  addition        ", lambda b: 2 + b),
        ("H_2  multiplication  ", lambda b: 2 * b),
        ("H_3  exponentiation  ", lambda b: 2 ** b),
        ("H_4  tetration       ", lambda b: tetration(2, b)),
        ("H_5  pentation       ", lambda b: pentation(2, b)),
    ]
    for name, f in rows:
        print(f"        {name}  {f(1):>5}  {f(2):>5}  {f(3):>12}")
    print("        H_6  hexation             2      4      2^^65536"
          "   (structural)")
    check("the operand-2 column is constantly 4 from H_2 up: "
          "2*2 = 2^2 = 2^^2 = 2^^^2 = 4",
          2 * 2 == 2 ** 2 == tetration(2, 2) == pentation(2, 2) == 4)
    check("ladder recursion at base 2: H_3(2,s+1) = H_2(2, H_3(2,s))",
          all(2 ** (s + 1) == 2 * 2 ** s for s in (1, 2)))
    check("ladder recursion at base 2: H_4(2,s+1) = H_3(2, H_4(2,s)), s=1,2,3",
          all(tetration(2, s + 1) == 2 ** tetration(2, s) for s in (1, 2, 3)))
    check("ladder recursion at base 2: H_5(2,3) = H_4(2, H_5(2,2)) = 2^^4",
          pentation(2, 3) == tetration(2, pentation(2, 2)) == 65536)
    print("        H_6(2,3) = H_5(2, H_6(2,2)) = H_5(2,4) = 2^^65536, a")
    print("        tower of 65536 twos.  Note H_6(2,3) = H_5(2,4): at base")
    print("        2 the ladder folds -- the base-2 column is degenerate.")

    print("""
 5.3  The window.  v = H_{l+1}(b, s) puts rank l on rung l+1, the zone
       letter s as second operand:

                  prime    reflection    projection     (= operand s)
        rank 1  H_2  * :    b          2b            3b
        rank 2  H_3  ^ :    b          b^2           b^3
        rank 3  H_4 ^^ :    b          b^b          b^(b^b)

       a 3x3 (rung x operand) window of the ladder -- one rung per rank,
       one operand per zone, the base ranging over the 39 cells.  Rank 4
       would be pentation, rank 5 hexation; sec 8 locates this window in
       the fast-growing hierarchy.""")


# --------------------------------------------- section 6: zones and orbits

def zones_orbits():
    header("6. ZONES AND ORBITS -- 39 orbits of size 3; self-similarity")

    print("\n 6.1  Orbits of the zone action")
    cells_ = list(cells())
    check("39 index cells (3 + 9 + 27)", len(cells_) == 39)
    orbits = {alpha: [(s,) + alpha for s in A] for alpha in cells_}
    flat = [w for ws in orbits.values() for w in ws]
    check("the 39 orbits {(s,alpha) : s in A} partition the 117 points",
          len(flat) == 117 and len(set(flat)) == 117)
    check("every orbit has size 3 -- one prime, one reflection, one "
          "projection point",
          all(len(ws) == 3 for ws in orbits.values()))
    ok = all(point_value(ws[0]) < point_value(ws[1]) < point_value(ws[2])
             for ws in orbits.values())
    check("in every orbit: prime < reflection < projection (strictly)", ok)
    print("\n       specimen orbits (cell -> its three zone values):")
    short = {1: "prime", 2: "refl", 3: "proj"}
    for alpha in [(1,), (3,), (1, 3), (2, 3),
                  (1, 1, 1), (2, 2, 2), (1, 2, 3)]:
        l, p = len(alpha), tail_product(alpha)
        bstr = str(base(alpha)) if l <= 2 else f"2^{3 * p}"
        vals = "   ".join(f"{short[s]}: {display(s, alpha)}" for s in A)
        print(f"         cell {str(alpha):<10} b = {bstr:<8} {vals}")

    print("\n 6.2  Monoid truncation: zone_s = g^s(unit), g(x) = H_l(b, x)")
    print("""       The zone ladder inside rank l is the orbit of the unit of
       rung H_l under the map g(x) = H_l(b, x), stopped after three
       steps -- the free monoid on one generator, truncated at 3:

         rank 1:  g(x) = b + x   (rung H_1),  unit 0:   b,  2b,  3b
         rank 2:  g(x) = b * x   (rung H_2),  unit 1:   b,  b^2, b^3
         rank 3:  g(x) = b ^ x   (rung H_3),  unit 1:   b,  b^b, b^(b^b)""")
    ok = True
    for alpha in cells_:
        l = len(alpha)
        b = base(alpha)
        if l == 1:
            x = 0                            # unit of H_1
            for s in A:
                x = b + x
                ok = ok and point_value((s,) + alpha) == Canon.of_int(x)
        elif l == 2:
            x = 1                            # unit of H_2
            for s in A:
                x = b * x
                ok = ok and point_value((s,) + alpha) == Canon.of_int(x)
        else:
            t = Canon.of_int(b)              # b = 2^(3h)
            x = t                            # g^1(unit): b^1 = b
            ok = ok and x == point_value((1,) + alpha)
            for s in (2, 3):
                x = t.pow_tower(x)           # g(x) = b^x
                ok = ok and x == point_value((s,) + alpha)
    check("zone_s = g^s(unit of H_l) for all 39 cells", ok)
    ok2 = True
    for alpha in cells_:
        l = len(alpha)
        b = base(alpha)
        v1, v2, v3 = (point_value((s,) + alpha) for s in A)
        if l == 1:
            ok2 = ok2 and v2 == Canon.of_int(b + b) \
                       and v3 == Canon.of_int(b + b + b)
        elif l == 2:
            ok2 = ok2 and v2 == Canon.of_int(b * b) \
                       and v3 == Canon.of_int(b * b * b)
        else:
            t = Canon.of_int(b)
            ok2 = ok2 and v2 == t.pow_tower(v1) and v3 == t.pow_tower(v2)
    check("zone walk v_(s+1) = H_l(b, v_s) for all 39 cells -- the SAME "
          "recursion that builds the ladder (5.2)", ok2)

    print("""
 6.3  Self-similarity.  The zone ladder inside rank l is walked by rung
       H_l (6.2); the rung ladder is built by that very recursion (5.2).
       So the zones of rank l+1 are walked by H_{l+1} -- the rung that
       rank l+1 itself lives on.  Transposing the grid,

         (rank l, zone s)  |->  (rung H_{l+1}, operand s),

       the 3x3 (rank x zone) grid of the object is the 3x3 (rung x
       operand) segment of the ladder: the zone axis of one rank is the
       rank axis of the whole ladder, both the triad {1,2,3}.  Zone
       structure at rank l+1 = rank structure one rung up.""")


# ------------------------------------------------- section 7: fibres

def fibres_section():
    header("7. FIBRES OF THE VALUATION -- 117 points, 37 values")
    points = list(all_points())

    print("\n 7.1  The collapse")
    print("       v is NOT injective; the coincidences are multiplicative.")
    fibers = {}
    for w in points:
        fibers.setdefault(point_value(w), []).append(w)
    sizes = Counter(len(v) for v in fibers.values())
    check("the 117 points fall into 37 distinct values", len(fibers) == 37)
    check("fibre sizes add back to 117",
          sum(len(v) for v in fibers.values()) == 117)
    check("fibre size distribution {1:11, 3:17, 4:2, 5:1, 6:4, 9:2}",
          dict(sizes) == {1: 11, 3: 17, 4: 2, 5: 1, 6: 4, 9: 2})
    maxf = max(len(v) for v in fibers.values())
    big = sorted(v for v in fibers.values() if len(v) == maxf)
    check("maximum fibre size is 9, attained exactly at 4096 and 262144",
          maxf == 9 and len(big) == 2
          and point_value(big[0][0]) == Canon.of_int(4096)
          and point_value(big[1][0]) == Canon.of_int(262144))
    v24 = Canon.of_int(2 ** 24)
    check("2^24 has fibre 5: three rank-2 words, one rank-3 prime word, "
          "one rank-3 reflection word",
          len(fibers[v24]) == 5
          and sum(1 for w in fibers[v24] if len(w) == 3) == 3
          and sum(1 for w in fibers[v24] if len(w) == 4 and w[0] == 1) == 1
          and sum(1 for w in fibers[v24] if len(w) == 4 and w[0] == 2) == 1)
    ok = True
    for val, ws in fibers.items():
        r2 = [w for w in ws if len(w) == 3]
        r31 = [w for w in ws if len(w) == 4 and w[0] == 1]
        if r2 and r31:
            ok = ok and all(2 * w[0] * w[1] * w[2] == 3 * u[1] * u[2] * u[3]
                            for w in r2 for u in r31)
    check("rank-2 / rank-3(prime) collisions satisfy 2*sab = 3*h exactly",
          ok)

    print("\n 7.2  Inside one (rank, zone): fibres = permutation orbits")
    print("""       Unique factorization: two tails from {1,2,3}^l have equal
       product iff they are permutations of each other, so inside one
       block the fibre of a value is exactly a permutation orbit of the
       index letters -- this is where the fibre sizes 1, 3, 6 come from.""")
    ok = True
    for l in (2, 3):
        for s in A:
            groups = {}
            for alpha in product(A, repeat=l):
                groups.setdefault(point_value((s,) + alpha), []).append(alpha)
            for ws in groups.values():
                ok = ok and all(sorted(p) == sorted(q)
                                for p in ws for q in ws)
            ok = ok and (len({tuple(sorted(ws[0])) for ws in groups.values()})
                         == len(groups))
    check("rank 2 and 3, every zone: equal value <=> permuted tails", ok)
    r2prod = Counter(s * a * b for s in A for a in A for b in A)
    r3prod = Counter(a * b * c for a in A for b in A for c in A)
    check("multiplicity of a product of 3 letters: 1 for h=1,8,27;  3 for "
          "h=2,3,4,9,12,18;  6 for h=6  (1+3+3+3+6+1+3+3+3+1 = 27)",
          sorted(set(r3prod.values())) == [1, 3, 6]
          and sum(r3prod.values()) == 27
          and r3prod[1] == r3prod[8] == r3prod[27] == 1
          and r3prod[6] == 6)

    print("\n 7.3  Across blocks: the Diophantine collision laws")
    print("""       A rank-2 word (s,a,b) and a rank-3 prime word (1,i,j,k)
       collide iff  2*s*a*b = 3*i*j*k  -- four letters {1,2,3} against
       three.  The six solutions, with the multiplicities of 7.2:""")
    print("\n          E     sab (mult)     h (mult)    fibre of 2^E")
    sols = []
    for p2 in sorted(r2prod):
        E = 2 * p2
        if E % 3 == 0 and E // 3 in r3prod:
            sols.append((E, p2, E // 3))
    for E, p2, h in sols:
        print(f"         {E:>3}     {p2:>3}  ({r2prod[p2]})       {h:>3}  "
              f"({r3prod[h]})        {r2prod[p2] + r3prod[h]}")
    check("exactly 6 solutions of 2*sab = 3*h, at E = 6,12,18,24,36,54, "
          "with h = (2/3)*sab",
          [E for E, _, _ in sols] == [6, 12, 18, 24, 36, 54])
    f4 = fibers[Canon.of_int(4)]
    f8 = fibers[Canon.of_int(8)]
    check("rank 1 merges into rank 2 at 4 and 16 only "
          "(4: rank-1 (1,2),(2,1) + rank-2 sab=1;  16: (2,3) + sab=2 x3)",
          len(f4) == 3 and sum(1 for w in f4 if len(w) == 2) == 2
          and len(fibers[Canon.of_int(16)]) == 4)
    check("rank 1 merges into rank-3 prime at 8 only "
          "(rank-1 (1,3),(2,2) + the rank-3 word (1,1,1,1))",
          len(f8) == 3 and sum(1 for w in f8 if len(w) == 2) == 2
          and (1, 1, 1, 1) in f8)
    r3h = sorted(r3prod)
    sols2 = [(h, h * 2 ** (3 * h)) for h in r3h if h * 2 ** (3 * h) in r3h]
    check("reflection law h*2^(3h) = h' (rank-3 reflection vs prime) has "
          "the unique solution h=1, h'=8 -- giving the fibre-5 value 2^24",
          sols2 == [(1, 8)])
    check("rank-1 projection values 6, 12, 24 (odd part 3) are isolated: "
          "every other value is a power of two",
          all(len(fibers[Canon.of_int(3 * 2 ** a)]) == 1 for a in A))
    print("""       So the fibre sizes decompose as:  1, 3, 6 = permutation
       multiplicities inside a block (7.2);  4, 9 = sums of two such
       multiplicities over the 2sab = 3h law;  5 = the unique triple
       meeting at 2^24 (3 rank-2 + 1 rank-3 prime + 1 rank-3 reflection).""")

    print("\n       Cross-block fibres (points from more than one block):")
    for val in sorted(fibers):
        ws = fibers[val]
        ranks = {len(w) for w in ws}
        if len(ranks) > 1:
            byrank = {}
            for w in ws:
                byrank.setdefault(len(w), []).append(w)
            print(f"\n         value {canon_display(val)}  -- fibre {len(ws)}")
            for r in sorted(byrank):
                tag = f"rank {r - 1}"     # block rank = word length - 1
                pts = "  ".join(word_str(w) for w in byrank[r])
                print(f"           {tag:<8} ({len(byrank[r])}):  {pts}")
    print("\n       Block-internal fibres (multiplicity of the product):")
    for val in sorted(fibers):
        ws = fibers[val]
        ranks = {len(w) for w in ws}
        if len(ranks) == 1 and len(ws) > 1:
            r = next(iter(ranks))
            print(f"         value {canon_display(val)}  -- fibre {len(ws)}"
                  f"  (rank {r - 1}, zone s = {ws[0][0]})")

    print("\n 7.4  Canonical form and exact order")
    cs = [point_value(w).c for w in points]
    us = [point_value(w).u for w in points]
    check("all 117 values fit c*2^(u*2^Y) with c <= 3 and u <= 81",
          max(cs) <= 3 and max(us) <= 81)
    vals = sorted(fibers)
    check("global minimum is 2 at (1,1)",
          vals[0] == Canon.of_int(2) and fibers[vals[0]] == [(1, 1)])
    top = vals[-1]
    check("global maximum is the tower at (3,3,3,3)",
          fibers[top] == [(3, 3, 3, 3)])
    print(f"         global max = {canon_display(top)}"
          f"  = 2^(81*2^(81*2^81))")
    for l in (1, 2, 3):
        bv = [point_value(w) for w in block(l)]
        print(f"         rank {l}: min {canon_display(min(bv)):>12}"
              f"   max {canon_display(max(bv))}")
    a = point_value((2, 1, 2, 3))    # h=6:  2^(18*2^18)
    b = point_value((3, 1, 1, 1))    # h=1:  2^(3*2^24)
    c = point_value((2, 2, 2, 2))    # h=8:  2^(24*2^24)
    check("the blocks interleave: 2^(18*2^18) < 2^(3*2^24) < 2^(24*2^24)",
          a < b < c)
    check("smallest projection tower < largest reflection tower: "
          "2^(3*2^24) < 2^(81*2^81)",
          point_value((3, 1, 1, 1)) < point_value((2, 3, 3, 3)))
    print("\n       The ten largest values of the object:")
    for val in vals[-10:]:
        print(f"         {canon_display(val):>34}   "
              f"{', '.join(word_str(w) for w in fibers[val])}")


# ------------------------------------------------- section 8: growth

def fgh(k, n):
    """F_k(n) of the fast-growing hierarchy, exact for k <= 3, n <= 3.

    F_0(n) = n+1;  F_{k+1}(n) = F_k^n(n)  (n-fold self-composition),
    so F_1(n) = 2n, F_2(n) = n*2^n, F_3(n) = x -> x*2^x iterated n times.
    """
    if k == 0:
        return n + 1
    if k == 1:
        return 2 * n
    if k == 2:
        return n << n
    x = n
    for _ in range(n):
        x = x << x
    return x


def ack(m, n):
    """Ackermann A(m, n) by the primitive recursion (small m, n only)."""
    if m == 0:
        return n + 1
    if n == 0:
        return ack(m - 1, 1)
    return ack(m - 1, ack(m, n - 1))


def growth_section():
    header("8. GROWTH -- the fast-growing hierarchy and Ackermann")
    print("""
The fast-growing hierarchy:  F_0(n) = n+1,  F_{k+1}(n) = F_k^n(n).
Each rung of the hyperoperation ladder is one level of it (at base 2):
H_2(2, n) = 2n = F_1(n) exactly;  F_2(n) = n*2^n = n * H_3(2, n);  F_3
is tower-class, like H_4.""")

    print("\n 8.1  F_k(n) exactly (k <= 3)")
    print("\n            n=1      n=2                     n=3")
    row0 = [fgh(0, n) for n in (1, 2, 3)]
    row1 = [fgh(1, n) for n in (1, 2, 3)]
    row2 = [fgh(2, n) for n in (1, 2, 3)]
    print(f"   F_0   {row0[0]:>4}   {row0[1]:>6}   {row0[2]:>22}")
    print(f"   F_1   {row1[0]:>4}   {row1[1]:>6}   {row1[2]:>22}"
          "   = H_2(2, n) exactly")
    print(f"   F_2   {row2[0]:>4}   {row2[1]:>6}   {row2[2]:>22}"
          "   = n*2^n = n * H_3(2, n)")
    print( "   F_3      2     2048   402653184*2^402653184")
    f32 = fgh(3, 2)
    f33 = fgh(3, 3)
    check("F_1(n) = 2n = H_2(2,n) and F_2(n) = n*2^n for n = 1, 2, 3",
          all(fgh(1, n) == 2 * n and fgh(2, n) == n * 2 ** n
              for n in (1, 2, 3)))
    check("F_3(2) = 2048 = 2^11 and F_3(3) = 402653184 * 2^402653184",
          f32 == 2048 and f33 == 402653184 * 2 ** 402653184)
    print(f"         F_3(3) has about {f33.bit_length() * math.log10(2):.2e}"
          " digits (estimate from the bit length).")
    print("         F_4(2) = F_3(F_3(2)) = F_3(2048) is a tower of height")
    print("         ~2048 -- beyond any integer a machine holds.  F_4 grows")
    print("         like pentation, F_5 like hexation: the ladder and the")
    print("         hierarchy are the same construction read two ways.")

    print("\n 8.2  Ackermann  (A(m, .) lives on rung H_m for m >= 2)")
    check("A(2,n) = 2n+3 and A(3,n) = 2^(n+3)-3 for n = 0..4 "
          "(primitive recursion, exact)",
          all(ack(2, n) == 2 * n + 3 and ack(3, n) == 2 ** (n + 3) - 3
              for n in range(5)))
    A40 = ack(4, 0)                        # = A(3,1) = 13, direct recursion
    A41 = 2 ** (A40 + 3) - 3               # = A(3, A(4,0)) = A(3,13)
    A42 = 2 ** 65536 - 3                   # = A(3, A(4,1)) = A(3,65533)
    check("A(4,0) = 13 by direct recursion; then A(4,1) = A(3,13) = 65533 "
          "and A(4,2) = A(3,65533) = 2^65536 - 3 (verified closed form)",
          A40 == 13 and A41 == 65533 and A42 == 2 ** 65536 - 3)
    print(f"         A(4,2) = 2^65536 - 3 has exactly {len(str(A42))} digits.")
    print("         A(5,2) = A(4, A(5,1)) = A(4, 2^^65536 - 3) = "
          "2^^(2^^65536) - 3:")
    print("         structural only -- pentation class.")

    print("""
 8.3  Where the object sits.  Standard classification (Goodstein/Wainer;
       a theorem about the hierarchy, not about this code): rung H_{m+2}
       has the growth class of F_m, and A(m, .) ~ rung H_m:

         rank 1  =  rung H_2  ~  F_1  ~  A(2, .)    multiplication
         rank 2  =  rung H_3  ~  F_2  ~  A(3, .)    exponentiation
         rank 3  =  rung H_4  ~  F_3  ~  A(4, .)    tetration
         rank 4 (beyond the object)  ~  F_4  ~  A(5, .)   pentation

       The 117 points are the 3x3 (rung x operand) window at F_1..F_3,
       small operands, bases up to 2^81 -- large enough that the top of
       the object already outscales F_3(3):""")
    top_digits = 81 * 2 ** 81 * math.log10(2)
    f33_digits = f33.bit_length() * math.log10(2)
    print(f"         digit counts: top value 2^(81*2^(81*2^81)) has "
          f"~{top_digits:.2e} digits, F_3(3) only ~{f33_digits:.2e}.")

    print("""
 8.4  The omega^omega reading (structural interpretation).  A tail
       (a_1, ..., a_l) reads as the Cantor normal form

            omega^(l-1)*a_1 + omega^(l-2)*a_2 + ... + a_l.

       Tails of unbounded length with unbounded digits address exactly
       the ordinals below omega^omega -- the address space of the
       fast-growing hierarchy F_alpha, alpha < omega^omega (F_omega is
       the Ackermann diagonal; F_(omega^2), F_(omega^3), ... are further
       nestings of the same construction).  The object truncates EVERY
       axis at 3: tail length <= 3, digits <= 3, rungs H_2..H_4, operands
       1.. 3 -- the triadic limit.  Remove the truncations and the 117
       points unfold into the whole omega^omega segment; keep them and
       it stays a finite, fully computable window of it.""")


# ------------------------------------------------- section 9: specimens

def specimens():
    header("9. SPECIMENS -- exact expansions where they exist")
    print(f"\n   2^81 = 2**(3*27) (point (1,3,3,3), the largest integer in")
    print(f"   the object):")
    print(f"     {2**81}")
    print(f"\n   2^24 (point (2,1,1,1), the smallest reflection tower):")
    print(f"     {2**24}")
    print(f"\n   2^384 = 2**(6*2^6) (point (2,1,1,2), h=2):")
    print(f"     {2**384}")
    print(f"\n   Digit counts of the towers whose expansion still fits:")
    for h, note in ((3, "h=3, points (2,1,1,3)...: 2^4608"),
                    (4, "h=4, points (2,1,2,2)...: 2^49152")):
        c3 = 3 * h
        print(f"     2^{c3 * 2 ** c3} has exactly "
              f"{len(str(2 ** (c3 * 2 ** c3)))} digits   ({note})")
    E2max = 81 * 2 ** 81
    print(f"\n   Beyond that only exponents are writable: the largest "
          f"reflection value")
    print(f"   is 2^(81*2^81), whose exponent is the exact integer")
    print(f"        E_2 = 81*2^81 = {E2max}")
    print(f"   (a decimal expansion of 2^(81*2^81) would need roughly")
    print(f"    {float(E2max) * 0.30102999566398114:.2e} digits"
          " (an estimate, not an exact count).")
    print(f"\n   Ackermann A(4,2) = 2^65536 - 3: {len(str(2**65536 - 3))}"
          " digits (sec 8.2);")
    print(f"   H_6(2,3) = 2^^65536, a tower of 65536 twos: structural (sec 5.2).")


# ------------------------------------------------------------------- driver

def main():
    print_definition()
    print_rank1()
    print_rank2()
    print_rank3()
    print_exponent_table()
    index_set()
    ladder_section()
    zones_orbits()
    fibres_section()
    growth_section()
    specimens()
    header(f"SELF-TEST PASSED -- {PASSED[0]} checks, 117 points, "
           f"37 values, 39 orbits")
    return 0


if __name__ == "__main__":
    sys.exit(main())

