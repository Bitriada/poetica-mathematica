"""trinumeral -- the heterobase counting system, operational.

Poetica Mathematica Ch. VIII sec. 8.4: one value held in three
representational bases simultaneously -- binary (deep), integer
(forward), float (backward) -- with an exact graded trace of the
translation costs, an annihilation ladder of memory regimes, a ghost
disc, spin tallies, and the two-sheet spinorial double cover.

    from fractions import Fraction
    from trinumeral import Trinumeral

    T = Trinumeral.omega_0(Fraction(1, 10))    # the omega/0 gate
    T.show()                                    # B, i, f, alpha beta gamma
    T.tau, T.tau_cycle(), T.ghost               # the heterobase trace
    T.project_0a("int")                         # the 0/a gate (loses tau)

Every discrepancy is an exact Fraction; the float sheet is read back
through float.as_integer_ratio(), so nothing rounds in the algebra.
The monograph's sec. 8.4.8 worked example reproduces exactly, and
seven monograph inconsistencies are corrected with exact witnesses
(trinumeral.trials -> results/TRINUMERAL_TRIALS.md).
"""

from .grassmann import (E1, E2, E3, GrassmannElement, TOP, ZERO, scalar,
                        wedge)
from .core import (DEFAULT_P, Regime, Trinumeral, canonical,
                   encode_binary, exact)
from .ladder import LadderEngine
from .spin import SpinTally, SpinorialTally
from .trials import run_trials, write_report

__version__ = "1.0.0"

__all__ = [
    "E1", "E2", "E3", "TOP", "ZERO", "GrassmannElement", "scalar",
    "wedge", "DEFAULT_P", "Regime", "Trinumeral", "canonical",
    "encode_binary", "exact", "LadderEngine", "SpinTally",
    "SpinorialTally", "run_trials", "write_report", "__version__",
]
