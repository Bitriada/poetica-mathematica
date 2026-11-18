"""The NPCS scheme: path keys, bi-sheet commitments, verification.

DRAFT SOURCE (NPCS sec. 2), with the corrections of trials T3/T9
(exact serialization; honest tamper-evidence).

* A PATH KEY is a sequence of 27-bit Fare-Octal chunks (the secret).
* The COMMITMENT is the UC-Q tensor product
      T(P) = encode(s_0) * encode(s_1) * ... * encode(s_L),
  hashed sheet by sheet (EXACT integer serialization, not the draft's
  lossy float64 -- trials T3):
      H_val = SHA-256(serialize(val(T)))
      H_tr  = SHA-256(serialize(tr(T)))
      H     = SHA-256(H_val || H_tr)
  The public commitment is (H, H_val, H_tr, L) with L = len(P) - 1.

* VERIFICATION (draft sec. 2.3): five checks -- length, recomputation,
  and the three hash equalities.  Under a random guess the three
  independent 256-bit hash checks accept with probability 2^-768.

* ONE-SHOT MODE (draft sec. 2.4): replay protection by verifier state
  (a Used-set).  Honest scope, per the draft and the monograph: tau^2
  = 0 is a WITHIN-computation annihilation property; ACROSS
  presentations, only the registry enforces one-shot.

KEY GENERATION (draft sec. 2.2 constraints, both kept):
  (1) no two consecutive chunks share the same trace sheet
      (tr(encode(s_j)) != tr(encode(s_{j+1})));
  (2) the path is not equal to its reverse and has no nontrivial
      cyclic self-rotation.
Trial T6 documents that constraint (1) is not load-bearing: nothing
annihilates on consecutive repetition (the tau^2 cross terms vanish in
EVERY product by design -- Proposition 2.8a.1), and the draft's own
sec. 7.3 concedes this.  The constraints are cheap and harmless.
"""

from __future__ import annotations

import hashlib
import random
import secrets
from dataclasses import dataclass

from .encode import CHUNK_BITS, encode
from .ucq import UCQ, ucq_product

__all__ = ["Commitment", "path_product", "generate_path", "commit",
           "verify", "OneShotRegistry", "sheet_hashes", "collapse"]


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def collapse(Z: UCQ) -> bytes:
    """collapse: UCQ -> 256 bits (draft sec. 1.5), on the EXACT
    serialization (the draft's float64 variant is lossy -- trials T3)."""
    return sha256(Z.serialize_exact())


def sheet_hashes(Z: UCQ):
    """(H_val, H_tr) for a UCQ element: two independent SHA-256
    commitments, one per sheet."""
    return sha256(Z.serialize_sheet("val")), sha256(Z.serialize_sheet("tr"))


def path_product(chunks) -> UCQ:
    """T(P) = encode(s_0) * ... * encode(s_L) in UCQ (order matters)."""
    return ucq_product([encode(c) for c in chunks])


@dataclass(frozen=True)
class Commitment:
    H: bytes
    H_val: bytes
    H_tr: bytes
    L: int          # draft notation: path (s_0..s_L), so len = L + 1

    def __repr__(self):
        return (f"Commitment(H={self.H.hex()[:16]}.., "
                f"H_val={self.H_val.hex()[:16]}.., "
                f"H_tr={self.H_tr.hex()[:16]}.., L={self.L})")


def commit(chunks) -> Commitment:
    """The public commitment to a path (draft sec. 2.2)."""
    if not chunks:
        raise ValueError("path must contain at least one chunk")
    T = path_product(chunks)
    h_val, h_tr = sheet_hashes(T)
    H = sha256(h_val + h_tr)
    return Commitment(H=H, H_val=h_val, H_tr=h_tr, L=len(chunks) - 1)


def _is_cyclic_self_rotation(path):
    n = len(path)
    doubled = path + path
    return any(doubled[r:r + n] == path for r in range(1, n))


def generate_path(length: int, rng: random.Random | None = None,
                  max_attempts: int = 10_000) -> list[int]:
    """A random path key satisfying the draft's sec. 2.2 constraints."""
    if length < 2:
        raise ValueError("path length must be at least 2")
    rng = rng or random.Random(secrets.randbits(128))
    for _ in range(max_attempts):
        path = [rng.getrandbits(CHUNK_BITS) for _ in range(length)]
        ok = all(encode(path[j]).tr() != encode(path[j + 1]).tr()
                 for j in range(length - 1))                 # constraint 1
        ok = ok and path != path[::-1]                       # constraint 2
        ok = ok and not _is_cyclic_self_rotation(path)
        if ok:
            return path
    raise RuntimeError("constraint satisfaction failed (should not happen)")


def verify(chunks, c: Commitment) -> bool:
    """The draft's five verification checks."""
    if len(chunks) != c.L + 1:                               # check 1
        return False
    T = path_product(chunks)                                 # check 2
    h_val, h_tr = sheet_hashes(T)
    return (h_val == c.H_val                                 # checks 3, 4
            and h_tr == c.H_tr
            and sha256(c.H_val + c.H_tr) == c.H)             # check 5


class OneShotRegistry:
    """Verifier-side replay guard (draft sec. 2.4): the one-shot
    property is enforced by this STATE, not by the algebra."""

    def __init__(self):
        self.used: set[bytes] = set()

    def present(self, chunks, c: Commitment) -> tuple[bool, str]:
        if not verify(chunks, c):
            return False, "invalid path (hash checks failed)"
        H = c.H
        if H in self.used:
            return False, "replay: commitment already presented"
        self.used.add(H)
        return True, "accepted (one-shot)"
