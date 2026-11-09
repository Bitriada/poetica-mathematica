"""rtfa -- Representation Transition / Fare Audit (fare-audit) v1.0.

A read-only instrument that observes transitions between computational
representations (N, Z, Q, F64, D128, C128, ...) and records the exact
"Fare" each transition pays (PDD/CTS v1.0).  Theoretical basis: the
Monkey Business Pipeline (MBP), the Generative Construction of 6
Geometric Freedoms (G6GF), the Fare Principle, and the Generative
Integer Fractal (GIF).

    from rtfa import FareAudit, Fraction, Decimal

    audit = FareAudit(run_id="demo-1")
    record = audit.transition(source="Q:1/10", target="F64",
                              operation="cast")
    print(record.fare.exactness)        # -> "R"

CLI:  python -m rtfa run | demo | verify
"""

from fractions import Fraction              # re-exported (CTS section 6.2)
from decimal import Decimal                 # re-exported (CTS section 6.2)

from .api import FareAudit
from .ledger import FareLedger, verify
from . import registry

__version__ = "1.0.0"

__all__ = ["FareAudit", "FareLedger", "verify", "registry",
           "Fraction", "Decimal", "__version__"]
