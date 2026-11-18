"""npcs -- the Nilpotent Path-Commitment Scheme, operational.

A bi-sheet credential built on Fare-Octal states (fareoctal, vendored)
and the UC-Q algebra of Poetica Mathematica Ch. VI sec. 6.2.8:
nilpotent cryptography made demonstrable, proof by trial.

    from npcs import generate_path, commit, verify

    path = generate_path(64)                 # secret: 27-bit chunks
    c = commit(path)                         # (H, H_val, H_tr, L)
    verify(path, c)                          # True
    verify(path[:-1] + [path[-1] ^ 1], c)    # False (one flipped bit)

All arithmetic is exact (integers only).  The draft spec's float64
serialization flaw and five other slips are corrected and demonstrated
with exact witnesses -- see npcs.trials and results/NPCS_TRIALS.md.
"""

from .ucq import (G0, TAU, UCQ, UCQ_I, UCQ_J, UCQ_K, cq_add, cq_conj,
                  cq_mul, cq_zero, g_mul, serialize_int, ucq_product)
from .encode import (BLOCKS, CHUNK_BITS, block_trace, block_value,
                     chunk_bits, encode, mini_encode, unchunk_bits)
from .scheme import (Commitment, OneShotRegistry, collapse, commit,
                     generate_path, path_product, sheet_hashes, verify)

__version__ = "1.0.0"

__all__ = [
    "G0", "TAU", "UCQ", "UCQ_I", "UCQ_J", "UCQ_K", "cq_add", "cq_conj",
    "cq_mul", "cq_zero", "g_mul", "serialize_int", "ucq_product",
    "BLOCKS", "CHUNK_BITS", "block_trace", "block_value", "chunk_bits",
    "encode", "mini_encode", "unchunk_bits", "Commitment",
    "OneShotRegistry", "collapse", "commit", "generate_path",
    "path_product", "sheet_hashes", "verify", "__version__",
]
