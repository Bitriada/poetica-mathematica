"""The annihilation ladder engine: one implementation, two users.

MONOGRAPH SOURCE: Ch. VIII secs. 8.4.3 (the trigger ladder: what counts
as a repeat) and 8.4.3a (the response ladder: what invariant is
preserved when annihilation fires), unified by 8.4.3a's closing remark:

    "The memory regime is determined by two independent choices.  The
     first choice is sensitivity: how loose does the match have to be
     for annihilation to fire?  The second choice is conservation: when
     annihilation fires, what invariant is preserved?  A complete
     specification of the memory regime requires both."

Trigger ladder (fires?):
    0  never                                  (perfect memory)
    1  exact consecutive repeat, trace != 0   (default)
    2  repeat within eps
    3  any second conversion on the edge
    4  after k_trig repetitions of the type
    5  always

Response ladder (what happens; t = trace before, alpha = incoming):
    0  add normally:  t + alpha               (2*alpha in the clean case)
    1  exact pair:    0, ghost += |t| + |alpha|   (= 2|alpha| when t =
       alpha; conserves total magnitude -- sec. 8.4.3a Level 1; note
       sec. 8.4.3 Level 1 prints |alpha|, the non-conserving variant:
       correction C3 in the trials)
    2  saturation:    t stays, ghost += |alpha|   (bounded memory cell)
    3  reset:         0, ghost += |alpha|     (prior magnitude LOST)
    4  sign-sensitive: same sign -> 0, ghost += |t| + |alpha|;
       opposite signs add normally            (chiral sheet)
    5  threshold:     after k_resp identical consecutive -> 0,
       ghost += |t| + |alpha|                 (= k|alpha| in the clean
       case; Level 1 is k = 2)

Sec. 8.4.3 Level 1 also says "After annihilation, subsequent identical
conversions have no effect" -- implemented as the spent flag under
trigger 1.
"""

from __future__ import annotations

from fractions import Fraction

from .grassmann import GrassmannElement

__all__ = ["LadderEngine"]


class LadderEngine:
    """Per-edge conversion memory + the (trigger, response) regime.
    Shared by the trinumeral edges and the spinorial crossing edges."""

    def __init__(self, regime, tau: GrassmannElement = None,
                 ghost=Fraction(0), edge_memory=None):
        self.regime = regime
        self.tau = tau if tau is not None else GrassmannElement()
        self.ghost = Fraction(ghost)
        self.edge_memory = edge_memory if edge_memory is not None else {}

    # -- the single entry point ------------------------------------------------
    def record(self, edge: int, alpha: Fraction) -> Fraction:
        """Record a conversion discrepancy on an edge; returns the
        ghost transfer made (0 if none)."""
        alpha = Fraction(alpha)
        mem = self.edge_memory.get(edge,
                                   {"last": None, "run_ident": 0,
                                    "run_any": 0, "spent": False})
        last = mem["last"]
        run_ident = (mem["run_ident"] + (1 if alpha == last else 0)
                     if last is not None else 1)
        run_any = mem["run_any"] + 1
        t = self.tau.coefficient(edge)
        r = self.regime

        # sec. 8.4.3 Level 1: subsequent identical conversions have no
        # effect (spent flag; trigger 1 only)
        if r.trigger == 1 and mem["spent"] and alpha == last:
            return Fraction(0)

        fire = self._fires(alpha, last, run_ident, run_any, t)
        transfer = Fraction(0)
        if not fire:
            new_t = t + alpha                    # linear accumulation
        else:
            new_t, transfer = self._respond(alpha, last, run_ident, t)
            self.ghost += transfer
            if r.trigger == 1 and alpha == last and new_t == 0:
                mem["spent"] = True

        terms = {k: v for k, v in self.tau.terms.items()
                 if len(k) != 1 or edge not in k}
        if new_t != 0:
            terms[frozenset((edge,))] = new_t
        self.tau = GrassmannElement(terms)
        mem.update(last=alpha, run_ident=run_ident, run_any=run_any,
                   spent=mem["spent"])
        self.edge_memory[edge] = mem
        return transfer

    # -- the two ladders ----------------------------------------------------------
    def _fires(self, alpha, last, run_ident, run_any, t) -> bool:
        r = self.regime
        if r.trigger == 0:
            return False
        if r.trigger == 1:
            return last is not None and alpha == last and t != 0
        if r.trigger == 2:
            return last is not None and abs(alpha - last) < r.eps
        if r.trigger == 3:
            return last is not None
        if r.trigger == 4:
            return run_any >= r.k_trig
        if r.trigger == 5:
            return True
        raise ValueError(f"unknown trigger level {r.trigger}")

    def _respond(self, alpha, last, run_ident, t):
        """Returns (new_trace_coefficient, ghost_transfer)."""
        r = self.regime
        if r.response == 0:
            return t + alpha, Fraction(0)
        if r.response == 1:
            if alpha == last:      # a true pair: cancel completely
                return Fraction(0), abs(t) + abs(alpha)
            return t + alpha, Fraction(0)
        if r.response == 2:        # saturation: bounded memory cell
            if t == 0:
                return alpha, Fraction(0)
            return t, abs(alpha)
        if r.response == 3:        # reset; prior magnitude lost
            return Fraction(0), abs(alpha)
        if r.response == 4:        # sign-sensitive (chiral sheet)
            if last is not None and alpha != 0 and last != 0 \
                    and (alpha > 0) == (last > 0):
                return Fraction(0), abs(t) + abs(alpha)
            return t + alpha, Fraction(0)
        if r.response == 5:        # threshold: k identical repeats
            if run_ident >= r.k_resp:
                return Fraction(0), abs(t) + abs(alpha)
            return t + alpha, Fraction(0)
        raise ValueError(f"unknown response level {r.response}")
