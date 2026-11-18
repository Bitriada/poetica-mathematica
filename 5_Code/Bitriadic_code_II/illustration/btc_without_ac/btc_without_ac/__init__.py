"""btc_without_ac: a computational model of "Banach-Tarski without the
Axiom of Choice" -- the case study of sec. 6.6 of the monograph
*Poetica Mathematica: Cogitatio ex Nihilo et Speculum Scientiae*
(K. I. Kovlekov, CC BY 4.0).

The package implements, verifies and visualizes:

* the Ultra-Complex algebra UC = C[tau]/(tau^2) (Ch. IV, sec. 4.2);
* the Fare-Riemann sphere S^3_FR, its Hopf-type value fibration,
  nadir plane and C3/C8 symmetry (secs. 4.2.4, 4.4.3);
* the constructive triadic decomposition S^3_FR = D0 |_| D1 |_| D2,
  the explicit O(1), choice-free assignment (secs. 6.6.3, 6.6.17);
* the spectator framework: projections, apparent sphere counts
  N_S = 1 (Unfathoming) / 3 (Forward, Backward, Deep) and the
  reversible spectator shift 1 <-> 3 (secs. 6.6.1, 6.6.15, Ch. VII);
* the ghost disc D^2_tau and the intrinsic-volume accounting
  3 + 2 - 1 = 4 (sec. 6.6.15);
* the reassembly homeomorphisms phi_k, trace payment (Fare Principle)
  and the three provenance-labeled virtual spheres (secs. 6.6.5-6.6.8,
  6.6.15);
* the classical contrast: the constructive 4-piece paradoxical
  decomposition of the free group F2, the free rotation pair, orbit
  transfer, and the amenability boundary (Folner ratios) that marks
  exactly where the Axiom of Choice becomes indispensable (sec. 6.6.2).

Run `python demo.py` for the full narrated demonstration (figures +
verification report), or `pytest` for the test-suite.
"""

from .uc import UC, ExactUC, TAU, I_UNIT
from . import sphere, triadic, spectators, ghost, reassembly, classical, report

__version__ = "1.0.0"

__all__ = [
    "UC", "ExactUC", "TAU", "I_UNIT",
    "sphere", "triadic", "spectators", "ghost", "reassembly",
    "classical", "report",
]
