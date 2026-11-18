"""qdme_bs: verification project for Theorem 8.1 (Unified Quantum Master
Equation) of *Poetica Mathematica* (K. I. Kovlekov, CC BY 4.0).

Theorem 8.1 (monograph, Part VIII sec. 8.1 "Bitriada Quantum Dynamics"):

    d(rho_hat)/dt = -i[H, rho] - i*tau*[Gamma, rho] - i*theta*[K, rho]
                    + Lambda . E[rho]

with the specializations table

    H only                -> Schrodinger      (1DB)
    H, Gamma, tau^2 = 0   -> Lindblad         (2DB)
    H, Gamma, K, theta!=0 -> Non-Markovian    (3DB-4DB)
    all terms             -> Evolutionary     (5DB)

Register discipline (monograph sec. 3.5.6):

* (mat) -- conjectured identity as a formal object: falsifiable here.
* (res) -- structural resonance: characterised, not provable.
* (par) -- poetic parable: not tested.

Layering (spec sec. 4): verification -> universality -> specializations
-> unified -> state -> algebra.  The pinned sub-algebra reference
``btc_without_ac`` (UC = C[tau]/(tau^2), 4D) is vendored unmodified and
wrapped, never redefined: UC is 4D, UC-Q is 16D -- do not conflate.
"""

from __future__ import annotations

import sys
from pathlib import Path

__version__ = "1.1.0"

# ---------------------------------------------------------------------------
# Vendored, pinned btc_without_ac (the 4D UC sub-algebra reference).
# The copy under <project>/btc_without_ac is byte-identical to the source
# project; we only put its root on sys.path so ``import btc_without_ac``
# resolves to the vendored one deterministically.  Wrap, do not modify.
# ---------------------------------------------------------------------------
_VENDOR_ROOT = Path(__file__).resolve().parent.parent / "btc_without_ac"
if _VENDOR_ROOT.is_dir() and str(_VENDOR_ROOT) not in sys.path:
    sys.path.insert(0, str(_VENDOR_ROOT))
