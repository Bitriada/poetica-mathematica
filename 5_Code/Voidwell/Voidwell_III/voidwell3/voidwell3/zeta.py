"""zeta.py -- the zeta-array assembly (D3 + D4): the tensor-shaped
hash, disentangled by the quaternion multiplication table.

MONOGRAPH SOURCES.

* Ch. VI sec. 6.1.5-6.1.6 (the fracture of the zeta-string): the
  single critical line cannot hold the distinct spectral shadows; it
  fractures into "3 legitimate bitriadic strings + 1 fold string
  making it technically a 4x4 binary string array" -- the ZETA-ARRAY:
  sixteen distinct strands, "arranged naturally into a 4 x 4 matrix",
  each carrying a different configuration of phase, entropy, and
  trace.
* Ch. VI sec. 6.2 (UC-Quaternions): the 16-dimensional algebra that
  "supplies [the] disentangling map between quaternionic strands".

VOIDWELL-3 REALIZATION.  The final hash of Voidwell-2 was a single
SHA-256 over the chain.  Voidwell-3 assembles SIXTEEN named cells
first, then contracts:

    cell[a][b] = SHA256("V3Z" || a || b || N_b || row_a(Q'_b))
                  a in {0,1,2,3}  (quaternion component 1, i, j, k)
                  b in {0,1,2,3}  (perspective well 1..4)

-- a 4 x 4 array whose two axes are the quaternionic directions and
the perspectival wells; every cell is a real hash of real per-well
material (the full-width nullifier and one row of the conjugated
matrix), so each cell independently binds its well.

THE DISENTANGLING MAP (D4).  Before contraction the array is
re-indexed by the quaternion multiplication table itself: for the
product q_a * q_b the table gives a component mu_b(a) and a sign
S[a][b],

    mu_0 = (0,1,2,3)   mu_1 = (1,0,3,2)
    mu_2 = (2,3,0,1)   mu_3 = (3,2,1,0)

    disentangled[mu_b(a)][b] = SHA256(cell[a][b] || sign(a,b))

Each strand is re-hashed with its quaternion sign and moved to the
component its product lands on.  The map is a bijection (each mu_b
is a permutation), it is nothing-up-my-sleeve (it IS the quaternion
table), and the gate recomputes it exactly.

CONTRACTION.  H = SHA256("V3H" || ghost_root || ser(disentangled 16)
        || ser_state(D_L) || wells_digest || e).

The conjectural layer of the monograph (sixteen zeta-STRINGS, each
carrying a local 1/2 line; the null-transit reunification) is
logged for a future version; what ships here is the verified FORM:
a tensor of sixteen named commitments, disentangled by quaternion
arithmetic, contracted into one hash.
"""
from __future__ import annotations

import hashlib

ZETA_VERSION = 1

#: the quaternion components, in index order: 1, i, j, k
COMPONENTS = ["1", "i", "j", "k"]

#: mu_b(a): the component index of the product q_a * q_b, for each
#: fixed b.  Each row is a permutation of 0..3 (verified at import).
MU = {
    0: (0, 1, 2, 3),     # x*1
    1: (1, 0, 3, 2),     # x*i:  1->i, i->-1, j->-k, k->j
    2: (2, 3, 0, 1),     # x*j:  1->j, i->k, j->-1, k->-i
    3: (3, 2, 1, 0),     # x*k:  1->k, i->-j, j->i, k->-1
}

#: S[a][b]: the sign of the product q_a * q_b (True = negative).
#: Row a=0 (the identity) and column b=0 are all positive; the
#: 3x3 inner block is the quaternion sign table.
_SIGNS = {
    (0, 0): 1, (0, 1): 1, (0, 2): 1, (0, 3): 1,
    (1, 0): 1, (1, 1): -1, (1, 2): 1, (1, 3): -1,
    (2, 0): 1, (2, 1): -1, (2, 2): -1, (2, 3): 1,
    (3, 0): 1, (3, 1): 1, (3, 2): -1, (3, 3): -1,
}


def sign(a: int, b: int) -> int:
    return _SIGNS[(a, b)]


def _check_tables() -> None:
    """The disentangling map must be a bijection on the 16 cells."""
    for b, mu in MU.items():
        assert sorted(mu) == [0, 1, 2, 3], f"mu_{b} not a permutation"
    seen = set()
    for a in range(4):
        for b in range(4):
            seen.add((MU[b][a], b))
    assert len(seen) == 16, "disentangling is not a bijection"


_check_tables()


def cell(a: int, b: int, nullifier_hex: str, row: tuple) -> str:
    """One zeta-array cell: a hash of the quaternion component index
    a, the perspective b, the well's full-width nullifier, and row a
    of the conjugated matrix."""
    h = hashlib.sha256()
    h.update(b"V3Z")
    h.update(bytes([a, b]))
    h.update(bytes.fromhex(nullifier_hex))
    for x in row:
        h.update(int(x).to_bytes(32, "big"))
    return h.hexdigest()


def disentangle(cells: dict) -> list[str]:
    """The disentangling map: re-hash each cell with its quaternion
    sign and move it to the product's component.  `cells` maps
    (a, b) -> hex.  Returns the re-hashed cells in canonical
    (well b, component a') order.  Partial schedules (k < 4, the
    small model's collapse scan) entangle only their wells; an
    empty schedule entangles nothing.  The map is a bijection on
    the present cells (each mu_b is a permutation; asserted)."""
    if not cells:
        return []
    out = {}
    for (a, b), src in cells.items():
        dst = (MU[b][a], b)
        if dst in out:
            raise ValueError("disentangling collision "
                             "(table is not a bijection)")
        h = hashlib.sha256()
        h.update(bytes.fromhex(src))
        h.update(bytes([sign(a, b) & 0xFF]))
        out[dst] = h.hexdigest()
    wells_b = sorted({b for _, b in out})
    return [out[(a, b)] for b in wells_b for a in range(4)]


def serialize_cells(disentangled: list[str]) -> bytes:
    out = bytearray(b"\x03")
    out.append(len(disentangled))
    for c in disentangled:
        out += bytes.fromhex(c)
    return bytes(out)


__all__ = ["ZETA_VERSION", "COMPONENTS", "MU", "sign", "cell",
           "disentangle", "serialize_cells"]
