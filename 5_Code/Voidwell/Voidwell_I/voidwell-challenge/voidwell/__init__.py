"""voidwell -- the three-layer construction (spec Part II).

LAYER 1  BASE      fare-octal digivector transitions (commutative)
LAYER 2  WELLS     UCQ conjugation, nullifiers, checkpoint restart
LAYER 3  BINDING   iterated SHA-256 over the full path

Modules: prf, schedule, encoder, gate; CLI in __main__.
"""
from voidwell import prf, schedule, encoder, gate
from voidwell.encoder import encode, run_path, EncodingError
from voidwell.gate import gate, PASS, FAIL, MALFORMED

__all__ = ["prf", "schedule", "encoder", "gate", "encode", "run_path",
           "EncodingError", "PASS", "FAIL", "MALFORMED"]
