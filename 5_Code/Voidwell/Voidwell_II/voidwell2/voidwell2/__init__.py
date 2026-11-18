"""voidwell2 -- Nilpotent Voidwell Cryptography.

A hash-and-key construction: from a secret seed, a 43-step walk
through a three-layer number system (fare-octal base, UC-Quaternion
wells, SHA-256 binding), published as a single hash H.  The key is
the seed alone; the wells sit at public pi-skeleton constants
(positions 3, 14, 15; digits 3, 1, 4).

Design facts that carry the security accounting:

  * full-width nullifiers: N_j = SHA256(ser(D') || full conjugated
    matrix) -- preimage domain 2^4123, one well saturates a
    256-bit seed;
  * H-only publication: the challenge carries H + public params,
    nothing per-well -- no dictionaries, no preimage targets, no
    early abort; the gate enforces the surface;
  * security = min(seed bits, 256): flagship (32-byte seed, 2^256)
    and compact (16-byte seed, 2^128); the sole assumption is
    SHA-256 preimage resistance.
"""
__version__ = "2.0.0"
