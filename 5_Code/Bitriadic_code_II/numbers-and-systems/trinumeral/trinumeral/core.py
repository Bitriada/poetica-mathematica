"""The Trinumeral: one value in three bases, with an exact trace.

MONOGRAPH SOURCE: Poetica Mathematica, Ch. VIII sec. 8.4 ("Heterobase
counting system: Trinumeral, spin-tallies"), secs. 8.4.1-8.4.8.

    "A trinumeral T is a meta-number: a container that holds one value
     in three distinct representations simultaneously.  We write
     T = (B, i, f, tau) where B is a binary representation, i is an
     integer, f is a complex floating-point number, and tau is a
     heterobase trace.  The trace records the discrepancies incurred
     when the same abstract value is forced into three different
     representational bases."

EXACTNESS.  Every discrepancy is a fractions.Fraction.  The float sheet
uses Python floats (IEEE 754 doubles) but is always read back through
float.as_integer_ratio(), so the algebra never rounds: the trace
records, exactly, what the representations themselves lose.

THE THREE EDGES (sec. 8.4.2), with signs as defined there:

    alpha = canonical(B) - i          (e1: binary -> integer)
    beta  = i - exact(f)              (e2: integer -> float)
    gamma = exact(f) - canonical(B_fb) (e3: float -> binary)

where B_fb is "the binary representation obtained by converting Re(f)
back to binary".  READING RESOLVED (correction C1 in the trials): if
B_fb is the exact re-encoding of the double, then gamma is IDENTICALLY
ZERO -- every IEEE double is a dyadic rational with a finite binary
expansion, so the return edge is always exact and the triangle never
closes.  The monograph's own worked example (sec. 8.4.8, T3 = 0.1,
gamma ~ 1e-17) matches the OTHER reading, sanctioned by sec. 8.4.2's
practice note ("the binary B_fb may be approximated by the existing
B"): B_fb = the STORED truncated B.  Default fb_mode="stored" (closes
the triangle: alpha + beta + gamma = 0 exactly); fb_mode="exact"
implements the formal definition (gamma == 0 always, demonstrated).

THE TELESCOPE THEOREM (established here, tested exactly): with
fb_mode="stored", the fresh construction discrepancies satisfy
alpha + beta + gamma = 0 identically -- the heterobase triangle closes;
the three translation costs cancel around the cycle B -> i -> f -> B.

CORRECTION C2 (sec. 8.4.8 signs): the arithmetic section prescribes
adding Delta_bi = i_sum - canonical(B_sum) etc., which are the NEGATIVES
of the sec. 8.4.2 edge conventions alpha = canonical(B) - i.  This
implementation records the fresh discrepancies with the consistent
8.4.2 signs (either choice telescopes; the printed one flips every
edge).

THE ANNIHILATION LADDER is two-dimensional (sec. 8.4.3a's own remark):
a TRIGGER ladder (what counts as a repeat: exact / within eps / any /
count-k / always) and a RESPONSE ladder (what invariant is preserved:
none / pair-cancel / saturation / reset / sign-sensitive / threshold-k).
CORRECTION C3: sec. 8.4.3 Level 1 transfers |alpha| to the ghost while
sec. 8.4.3a Level 1 transfers 2|alpha| and "conserves total magnitude";
the conserving 8.4.3a version is implemented (ghost += |trace_before| +
|alpha|, which equals 2|alpha| in the canonical pair case).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from .grassmann import (E1, E2, E3, TOP, ZERO, GrassmannElement,
                        generator, scalar)
from .ladder import LadderEngine

__all__ = ["Trinumeral", "Regime", "canonical", "encode_binary",
           "exact", "DEFAULT_P"]


DEFAULT_P = 53          # fractional bits; matches the IEEE 754 mantissa


# -- binary string <-> exact rational ----------------------------------------
def exact(f: float) -> Fraction:
    """The exact rational value of an IEEE 754 double."""
    return Fraction(*f.as_integer_ratio())


def encode_binary(v: Fraction, p: int = DEFAULT_P) -> str:
    """The finite binary representation of v: exact integer part plus
    the first p fractional bits, truncated toward zero (sec. 8.4.1:
    "typically truncated after a fixed number of bits ... The default
    precision can be p = 53 bits")."""
    v = Fraction(v)
    sign = "-" if v < 0 else ""
    m = abs(v)
    int_part = math.floor(m)
    frac = m - int_part
    int_bits = bin(int_part)[2:] if int_part else "0"
    frac_bits = []
    for _ in range(p):
        frac *= 2
        bit = 1 if frac >= 1 else 0
        frac_bits.append(str(bit))
        frac -= bit
    return f"{sign}{int_bits}.{''.join(frac_bits)}"


def canonical(B: str) -> Fraction:
    """The exact rational value of a finite binary string (sec. 8.4.2:
    "canonical(B) is the rational number represented by that finite
    truncation")."""
    B = B.strip()
    sign = -1 if B.startswith("-") else 1
    B = B.lstrip("+-")
    if "." in B:
        int_bits, frac_bits = B.split(".", 1)
    else:
        int_bits, frac_bits = B, ""
    n = int(int_bits, 2) if int_bits else 0
    q = Fraction(n)
    for j, bit in enumerate(frac_bits, start=1):
        if bit == "1":
            q += Fraction(1, 2 ** j)
    return sign * q


@dataclass(frozen=True)
class Regime:
    """The 2D annihilation parameter space (sec. 8.4.3a's closing
    remark: trigger ladder x response ladder).

    trigger: 0 none | 1 exact consecutive repeat (default) |
             2 within eps | 3 any repeat | 4 count k_trig | 5 always
    response: 0 add normally | 1 exact pair annihilation (default) |
             2 saturation | 3 reset, partial transfer | 4 sign-sensitive |
             5 threshold k_resp identical repeats
    """
    trigger: int = 1
    response: int = 1
    eps: Fraction = Fraction(1, 10 ** 6)
    k_trig: int = 2
    k_resp: int = 2


EDGE_NAMES = ("bin->int", "int->float", "float->bin")


class Trinumeral:
    """T = (B, i, f, tau) plus the ghost disc and the memory regime.

    The trace tau, the ghost disc and the annihilation ladder state
    live in a shared LadderEngine (ladder.py) -- the same engine the
    spinorial tally uses for its crossing edges."""

    def __init__(self, B, i, f, tau=None, ghost=Fraction(0), p=DEFAULT_P,
                 fb_mode="stored", adder="carry", mod_bits=64,
                 regime=None, edge_memory=None, name=None):
        self.B = B
        self.i = int(i)
        self.f = float(f)
        self.p = p
        self.fb_mode = fb_mode
        self.adder = adder
        self.mod_bits = mod_bits
        self.regime = regime or Regime()
        self.engine = LadderEngine(self.regime,
                                   tau=tau if tau is not None else ZERO,
                                   ghost=ghost, edge_memory=edge_memory)
        self.name = name

    # -- trace / ghost views (delegated) --------------------------------------
    @property
    def tau(self) -> GrassmannElement:
        return self.engine.tau

    @tau.setter
    def tau(self, value: GrassmannElement):
        self.engine.tau = value

    @property
    def ghost(self) -> Fraction:
        return self.engine.ghost

    @ghost.setter
    def ghost(self, value):
        self.engine.ghost = Fraction(value)

    @property
    def edge_memory(self):
        return self.engine.edge_memory

    # -- construction: the omega/0 gate (sec. 8.4.6) --------------------------
    @classmethod
    def omega_0(cls, v, p=DEFAULT_P, fb_mode="stored", regime=None,
                adder="carry", mod_bits=64, name=None) -> "Trinumeral":
        """omega/0 applied to a pure value v (sec. 8.4.6):
        constructs (B_v, i_v, f_v, tau_initial)."""
        v = Fraction(v)
        T = cls(B=encode_binary(v, p), i=int(v), f=float(v), p=p,
                fb_mode=fb_mode, regime=regime, adder=adder,
                mod_bits=mod_bits, name=name)
        a, b, g = T.fresh_discrepancies()
        T.tau = a * E1 + b * E2 + g * E3
        return T

    # -- projections: the 0/a gates (sec. 8.4.6) --------------------------------
    def project_0a(self, which):
        """0/a gate: collapse to a single representation.  'The trace
        is lost in this projection.  The heterobase information is
        invisible to any single-base observer.'"""
        if which == "bin":
            return self.B
        if which == "int":
            return self.i
        if which == "float":
            return self.f
        raise ValueError("which must be 'bin', 'int' or 'float'")

    # -- the three edges (sec. 8.4.2) ----------------------------------------------
    def fresh_discrepancies(self):
        """(alpha, beta, gamma) of the CURRENT state, exactly."""
        alpha = canonical(self.B) - self.i
        beta = self.i - exact(self.f)
        if self.fb_mode == "exact":
            B_fb = encode_binary(exact(self.f), max(self.p, 1074))
            gamma = exact(self.f) - canonical(B_fb)
        else:                                   # "stored" (default)
            gamma = exact(self.f) - canonical(self.B)
        return alpha, beta, gamma

    # -- tau-cycle (sec. 8.4.5) ------------------------------------------------------
    def tau_cycle(self) -> GrassmannElement:
        """(alpha e1) ^ (beta e2) ^ (gamma e3) = alpha*beta*gamma *
        (e1^e2^e3) -- the heterobase cycle invariant, from the ACTIVE
        grade-1 trace coefficients."""
        a = self.tau.coefficient(0)
        b = self.tau.coefficient(1)
        g = self.tau.coefficient(2)
        return (a * E1) * (b * E2) * (g * E3)

    def cycle_coefficient(self) -> Fraction:
        return self.tau_cycle().coefficient(0, 1, 2)

    # -- annihilation engine (secs. 8.4.3 / 8.4.3a), shared ------------------
    def _record_edge(self, edge: int, alpha: Fraction) -> Fraction:
        """Record a conversion discrepancy on an edge; the (trigger,
        response) regime applies (see ladder.py)."""
        return self.engine.record(edge, alpha)

    # -- conversion operations (sec. 8.4.8) -----------------------------------------
    def bin2int(self) -> "Trinumeral":
        """i' = the integer content of B (truncation toward zero);
        records (i' - i) on e1."""
        out = self._copy()
        i_new = int(canonical(self.B))    # int() truncates toward zero
        out._record_edge(0, i_new - self.i)
        out.i = i_new
        return out

    def int2float(self) -> "Trinumeral":
        """f' = i as a float; records (exact(f') - i) on e2.  For
        |i| > 2^53 the float ROUNDS and the edge records it exactly."""
        out = self._copy()
        f_new = float(self.i)
        out._record_edge(1, exact(f_new) - self.i)
        out.f = f_new
        return out

    def float2bin(self) -> "Trinumeral":
        """B' = binary of Re(f) truncated to p bits; records
        (canonical(B') - Re(f)) on e3.  Non-zero whenever f's binary
        expansion needs more than p fractional bits."""
        out = self._copy()
        B_new = encode_binary(exact(self.f), self.p)
        out._record_edge(2, canonical(B_new) - exact(self.f))
        out.B = B_new
        return out

    # -- arithmetic (sec. 8.4.8) -----------------------------------------------------
    def _binary_sum(self, other):
        """The B component of T1 + T2 under the chosen addition
        species (sec. 8.4.8's bifurcation point)."""
        c1, c2 = canonical(self.B), canonical(other.B)
        if self.adder == "carry":            # default: standard integer
            return encode_binary(c1 + c2, self.p)
        if self.adder == "xor":              # GF(2): parity sheet
            if c1.denominator != 1 or c2.denominator != 1:
                raise ValueError("xor adder requires integer-valued "
                                 "binary sheets")
            n1, n2 = int(c1), int(c2)
            width = max(n1.bit_length(), n2.bit_length(), 1)
            x = (n1 ^ n2) & ((1 << width) - 1)
            return encode_binary(Fraction(x), self.p)
        if self.adder == "ieee":             # continuous sheet
            f_sum = self.f + other.f         # actual IEEE rounding
            return encode_binary(exact(f_sum), self.p)
        if self.adder == "mod":              # cyclic tally
            m = 1 << self.mod_bits
            s = int(c1 + c2)
            return encode_binary(Fraction(s % m), self.p)
        raise ValueError(f"unknown adder species {self.adder!r}")

    def __add__(self, other: "Trinumeral") -> "Trinumeral":
        out = self._copy()
        out.B = self._binary_sum(other)
        out.i = self.i + other.i
        out.f = self.f + other.f
        out.tau = self.tau + other.tau          # linear, sec. 8.4.8
        out.ghost = self.ghost + other.ghost
        # merge the per-edge conversion memories (T1's entries win; the
        # monograph does not specify -- documented design choice)
        merged = {k: dict(v) for k, v in other.engine.edge_memory.items()}
        merged.update({k: dict(v)
                       for k, v in self.engine.edge_memory.items()})
        out.engine.edge_memory = merged
        # fresh discrepancies of the new state, recorded with the
        # CONSISTENT 8.4.2 signs (correction C2: the monograph's
        # printed Deltas are their negatives)
        a, b, g = out.fresh_discrepancies()
        out._record_edge(0, a)
        out._record_edge(1, b)
        out._record_edge(2, g)
        return out

    # -- structure ---------------------------------------------------------------------
    def activation(self):
        """The 8-pattern activation state (sec. 8.4.7): which edges
        carry non-zero active trace."""
        return self.tau.activation(3)

    def is_traceless(self) -> bool:
        """An invariant point of the membrane (sec. 8.4.17): all three
        representations agree exactly."""
        a, b, g = self.fresh_discrepancies()
        return a == 0 and b == 0 and g == 0 and self.tau.is_zero()

    def is_nihilum(self) -> bool:
        """The Nihilum (sec. 8.4.17): value 0, trace 0, ghost 0."""
        return (self.i == 0 and canonical(self.B) == 0
                and exact(self.f) == 0 and self.tau.is_zero()
                and self.ghost == 0)

    def _copy(self) -> "Trinumeral":
        return Trinumeral(B=self.B, i=self.i, f=self.f, tau=self.tau,
                          ghost=self.ghost, p=self.p,
                          fb_mode=self.fb_mode, adder=self.adder,
                          mod_bits=self.mod_bits, regime=self.regime,
                          edge_memory={k: dict(v) for k, v in
                                       self.edge_memory.items()},
                          name=self.name)

    # -- display --------------------------------------------------------------------------
    def show(self) -> str:
        a, b, g = self.fresh_discrepancies()
        act = self.activation()
        cyc = self.cycle_coefficient()
        sign = "+" if cyc > 0 else ("-" if cyc < 0 else "0")
        lines = [
            f"Trinumeral{f' {self.name}' if self.name else ''}:",
            f"  B      = {self.B[:40]}{'...' if len(self.B) > 40 else ''}"
            f"   (p = {self.p} fractional bits)",
            f"  i      = {self.i}",
            f"  f      = {self.f!r}  =  {exact(self.f)}",
            f"  alpha  = {a}   ({float(a):+.17g})",
            f"  beta   = {b}   ({float(b):+.17g})",
            f"  gamma  = {g}   ({float(g):+.3g})",
            f"  tau    = {self.tau!r}",
            f"  cycle  = {cyc} * (e1^e2^e3)   [sign: {sign}]",
            f"  ghost  = {self.ghost}   activation {act}",
            f"  regime = trigger {self.regime.trigger}, "
            f"response {self.regime.response}"
            f" ({EDGE_NAMES[0]} | {EDGE_NAMES[1]} | {EDGE_NAMES[2]})",
        ]
        return "\n".join(lines)

    def __repr__(self):
        a, b, g = self.fresh_discrepancies()
        return (f"Trinumeral(B={self.B[:12]}.., i={self.i}, "
                f"f={self.f!r}, tau={self.tau!r}, ghost={self.ghost})")
