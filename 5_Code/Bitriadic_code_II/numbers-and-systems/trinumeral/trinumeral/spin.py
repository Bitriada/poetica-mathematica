"""Spin tallies and the two-sheet (spinorial) extension.

MONOGRAPH SOURCE: Ch. VIII secs. 8.4.9-8.4.12 and 8.4.18.

    sec. 8.4.9:  "A spin tally is a data structure for recording cyclic
    quantities: S = (t, r) where t is an integer called the tally
    (number of complete rotations), and r is a remainder in
    [-360, 360].  The total rotation encoded by S is theta = t*360 + r."

    sec. 8.4.10: the angle bridge -- convert to total angles, add,
    convert back with floor division ("floor division rounds toward
    -infinity ... This convention preserves the invariant that the
    remainder is always in [0, 360) for SpinNatural").

    sec. 8.4.12: the spinorial tally S_spin = (S, sigma), sigma =
    +-1, "The sign flips whenever the total angle crosses a multiple
    of 360 ... If floor(theta_old/360) != floor(theta_new/360), then
    sigma -> -sigma ... After a 360 rotation, sigma has flipped once.
    After a 720 rotation, sigma has flipped twice and returns to its
    original value.  This is the double cover of the rotation group."

    sec. 8.4.18: the annihilation ladder as a two-sheet navigation
    protocol -- Level 1: "A 720 rotation (two consecutive sign flips
    with the same discrepancy) returns the system to its original
    sheet with zero trace.  This is the coherent spinor regime."
    Level 4: "A 720 rotation in one direction annihilates, but a 360
    clockwise followed by 360 counterclockwise leaves a trace.  This
    is the Berry phase regime - the system remembers the path taken,
    not just the endpoint."

DESIGN CHOICES, documented (full rationale in trials):

* sigma flips PER BOUNDARY CROSSED, not once per rotation event: a
  single 720-degree jump crosses two boundaries and returns sigma to
  +1, as sec. 8.4.18 requires ("a 720 rotation ... returns the system
  to its original sheet"); sec. 8.4.12's printed rule (flip once if
  the floors differ) agrees only for single-boundary steps (correction
  C5 in the trials).

* the crossing trace lives in the SAME exterior algebra as the
  trinumeral trace, on two dedicated edges: e1 (generator 0) records
  POSITIVE-direction crossings, e2 (generator 1) records NEGATIVE-
  direction crossings -- this is what makes sec. 8.4.18's Berry-phase
  regime exact: same-direction repeats land on one edge and can pair-
  annihilate; opposite directions land on different edges and cannot
  cancel.  The crossing discrepancy is the signed net boundary count.

* all angles are exact Fractions (degrees); floor is exact.
"""

from __future__ import annotations

import math
from fractions import Fraction

from .core import Regime
from .grassmann import E1, E2, ZERO, GrassmannElement
from .ladder import LadderEngine

__all__ = ["SpinTally", "SpinorialTally", "FULL_TURN"]

FULL_TURN = Fraction(360)


class SpinTally:
    """S = (t, r): complete rotations plus remainder; theta = 360t + r.

    variant "natural": r in [0, 360)  (the sec. 8.4.9 SpinNatural)
    variant "integer": r in [-360, 360]                    (SpinInteger)
    variant "float":   r in [-360, 360], rational          (SpinFloat)
    """

    def __init__(self, t: int, r, variant: str = "natural", name=None):
        if variant not in ("natural", "integer", "float"):
            raise ValueError("variant must be natural | integer | float")
        self.t = int(t)
        self.r = Fraction(r)
        self.variant = variant
        self.name = name
        self._check()

    def _check(self):
        if self.variant == "natural":
            ok = 0 <= self.r < FULL_TURN
        else:
            ok = -FULL_TURN <= self.r <= FULL_TURN
        if not ok:
            raise ValueError(f"remainder {self.r} outside the "
                             f"{self.variant} range")

    # -- the angle bridge (sec. 8.4.10) ------------------------------------
    @property
    def angle(self) -> Fraction:
        return FULL_TURN * self.t + self.r

    @classmethod
    def from_angle(cls, theta, variant: str = "natural") -> "SpinTally":
        """Convert a total angle back: t = floor(theta/360),
        r = theta - 360t -- the floor convention of sec. 8.4.10."""
        theta = Fraction(theta)
        t = math.floor(theta / FULL_TURN)
        r = theta - FULL_TURN * t
        return cls(t, r, variant)

    def __add__(self, other: "SpinTally") -> "SpinTally":
        if self.variant != other.variant:
            raise ValueError("angle bridge requires a common variant")
        return SpinTally.from_angle(self.angle + other.angle, self.variant)

    # -- the three tally types as three bases (sec. 8.4.11) --------------------
    def in_variants(self):
        """The same angle in all three tally types -- the spin-domain
        heterobase view (sec. 8.4.11: 'the three representations are
        the three tally types applied to the same angle')."""
        theta = self.angle
        out = {}
        for variant in ("natural", "integer", "float"):
            t = math.floor(theta / FULL_TURN)
            r = theta - FULL_TURN * t
            if variant == "integer" and r > FULL_TURN / 2:
                # the Integer tally prefers the signed remainder
                t, r = t + 1, r - FULL_TURN
            out[variant] = SpinTally(t, r, variant)
        return out

    def shift_to(self, other: "SpinTally") -> Fraction:
        """The signed re-encoding shift between two tallies of the SAME
        angle in different variants: how many whole turns the encoding
        moved.  The spin-domain translation cost."""
        if self.angle != other.angle:
            raise ValueError("shift defined only for equal angles")
        return Fraction(other.t - self.t)

    # -- plumbing -----------------------------------------------------------------
    def is_origin(self) -> bool:
        return self.t == 0 and self.r == 0

    def __eq__(self, other):
        return isinstance(other, SpinTally) and self.t == other.t \
            and self.r == other.r and self.variant == other.variant

    def __repr__(self):
        return (f"SpinTally{self.variant.title()}"
                f"({self.t}, {self.r}) [theta={float(self.angle):g}deg]")


class SpinorialTally:
    """S_spin = (S, sigma): the two-sheet spin tally (sec. 8.4.12).

    sigma in {+1, -1} records the sheet; it flips PER 360-degree
    boundary crossed.  The crossing trace accumulates in the exterior
    algebra: edge e1 for positive-direction crossings, edge e2 for
    negative-direction crossings (the chiral/Berry structure of
    sec. 8.4.18 Level 4).  The annihilation regime is the trinumeral's
    (trigger, response) pair -- default Level 1, the coherent spinor
    regime: two identical crossings pair-annihilate, so a 720-degree
    rotation returns the system to its original sheet with zero trace.
    """

    def __init__(self, tally: SpinTally, sigma: int = 1,
                 tau: GrassmannElement = None, ghost=Fraction(0),
                 regime: Regime = None, edge_memory=None, name=None):
        self.tally = tally
        self.sigma = int(sigma)          # +-1
        self.regime = regime or Regime()
        self.engine = LadderEngine(self.regime,
                                   tau=tau if tau is not None else ZERO,
                                   ghost=ghost, edge_memory=edge_memory)
        self.name = name
        if self.sigma not in (1, -1):
            raise ValueError("sigma must be +1 or -1")

    # -- trace / ghost views (delegated) -------------------------------------
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

    # -- the monograph's floor-quotient crossing rule (sec. 8.4.12) ---------------
    def rotate(self, delta_theta) -> "SpinorialTally":
        """Rotate by delta_theta (degrees, exact): update the tally via
        the angle bridge, flip sigma per boundary crossed, record the
        crossing charge on its direction edge with annihilation."""
        out = self._copy()
        d = Fraction(delta_theta)
        theta_old = self.tally.angle
        theta_new = theta_old + d
        crossings = (math.floor(theta_new / FULL_TURN)
                     - math.floor(theta_old / FULL_TURN))
        if crossings % 2 != 0:               # flip per boundary, by parity
            out.sigma = -out.sigma
        if crossings > 0:
            out.engine.record(0, Fraction(crossings))       # e+ edge
        elif crossings < 0:
            out.engine.record(1, Fraction(crossings))       # e- edge
        out.tally = SpinTally.from_angle(theta_new, self.tally.variant)
        return out

    # -- structure ---------------------------------------------------------------
    def is_pure(self) -> bool:
        """A pure state: zero crossing trace (the sheet is coherent)."""
        return self.tau.is_zero()

    def _copy(self) -> "SpinorialTally":
        return SpinorialTally(tally=self.tally, sigma=self.sigma,
                              tau=self.tau, ghost=self.ghost,
                              regime=self.regime,
                              edge_memory={k: dict(v) for k, v in
                                           self.engine.edge_memory.items()},
                              name=self.name)

    def __repr__(self):
        return (f"SpinorialTally(sigma={self.sigma:+d}, "
                f"{self.tally!r}, tau={self.tau!r}, "
                f"ghost={self.ghost})")
