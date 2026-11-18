"""voidwell3 -- the Perspective Walk (Nilpotent Voidwell
Cryptography, version 3).

A hash-and-key construction in the Voidwell family: from a secret
seed, an L-step walk through fare-octal states, punctuated by FOUR
wells -- one per perspectival algebra (UC1 point, UC2 line, UC3
disc, UC4 field) -- placed and directed by the first four primes,
committed by full-width nullifiers, accumulated in a ghost-disc
Merkle tree, and contracted through the sixteen-cell zeta-array.
Published as a single hash H.  The key is the seed alone.

WHAT IS NEW IN V3 (each mapped to its module):

  * the Perspective Walk (D1): four wells, four kinds of complex
    direction, four exact algebraic laws and the loop closure
    i1^2 + i2^2 + i3^2 + 1 = 0 (perspectives.py);
  * the Primes Spine (D2): wells at positions 2, 3, 5, 7 nullifying
    digits 2, 3, 5, 7, with the spectral involution exponent
    e = 1 - 2s as a public parameter (wells.py; e = 0 is the
    monograph's critical fixed point s = 1/2);
  * the zeta-array assembly (D3) and the quaternion disentangling
    map (D4): sixteen named cells, axes (quaternion component,
    perspective), re-indexed by the quaternion multiplication table
    before contraction (zeta.py);
  * the ghost-disc accumulator (D5): a Merkle tree over every walk
    state, with logarithmic-size state proofs (ghost.py);
  * the packed XOF PRF and cached adjugate inverses (D6): the
    engineering layer (prf.py, ucq/matrix.py);
  * the state-dependent mixer (D7): no fixed data schedule can
    avoid digits anymore (encoder.py base_step).

WHAT IS UNCHANGED, ON PURPOSE (the honest-security discipline):

  * security = min(seed bits, 256); the sole assumption is SHA-256
    preimage resistance; the key space IS the seed space;
  * full-width nullifiers (2^4123 preimage domain in the full
    model; one well saturates a 256-bit seed, and there are four);
  * H-only publication enforced by the gate (the audit's teeth);
  * the same-code-path small model, exhaustively enumerable, and
    the shipped attacker package.
"""
__version__ = "3.0.0"
