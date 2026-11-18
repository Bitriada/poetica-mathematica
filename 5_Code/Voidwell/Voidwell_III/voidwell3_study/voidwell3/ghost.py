"""ghost.py -- the ghost-disc accumulator (D5): a Merkle tree over
the walk's states.

MONOGRAPH SOURCE (Ch. IV sec. 4.2.4.4, the ghost disc D^2_tau): the
nilpotent trace membrane between the temporal spheres -- "the memory
that the journey was made, but a memory that vanishes when the
journey is repeated" (tau^2 = 0).  The MBP's Tax Monkey stores the
ledger in exactly this spirit: self-similar at every scale, with
logarithmic overhead.

VOIDWELL-3 REALIZATION.  Voidwell-2 chained every state linearly:
    h = SHA256(h || ser(D_i))     for i = 0..L
so verifying ANY intermediate state required the whole replay.
Voidwell-3 keeps every state leaf and folds them into a binary
Merkle accumulator:

    root = fold(SHA256(ser(D_0)), ..., SHA256(ser(D_L)))

The root enters H (so the full state sequence stays committed at
full strength), and the key holder can now OPEN any single state
with a log-size authentication path -- a partial proof the
construction could not give before.  The paths are the ghost disc's
"directions preserved": each path is the trace of one state's
position in the whole journey.

The tree is canonical: pairs are hashed left-then-right; an odd
final leaf is promoted unmixed (the length is folded into the root
assembly by the encoder, so promotion leaks nothing).
"""
from __future__ import annotations

import hashlib

from ucq.matrix import FpMatrix  # noqa: F401  (docs context only)

GHOST_VERSION = 1


def _sha(a: bytes, b: bytes) -> bytes:
    return hashlib.sha256(a + b).digest()


def leaf(pro, state: int) -> bytes:
    """The leaf hash of a walk state (domain-separated)."""
    from voidwell3.encoder import ser_state  # local: avoid cycle
    return hashlib.sha256(b"V3G" + ser_state(pro, state)).digest()


def build(leaves: list[bytes]) -> list[list[bytes]]:
    """The full Merkle tree, levels bottom-up: tree[0] = leaves,
    tree[-1] = [root].  Returns None-safe structure for empty input."""
    if not leaves:
        raise ValueError("no leaves")
    tree = [list(leaves)]
    while len(tree[-1]) > 1:
        cur = tree[-1]
        nxt = []
        for i in range(0, len(cur) - 1, 2):
            nxt.append(_sha(cur[i], cur[i + 1]))
        if len(cur) % 2:
            nxt.append(cur[-1])
        tree.append(nxt)
    return tree


def root(tree: list[list[bytes]]) -> bytes:
    return tree[-1][0]


def open_path(tree: list[list[bytes]], index: int) -> list[bytes]:
    """The sibling path for leaf `index`: each entry is the sibling
    hash at that level (the verifier knows the direction from the
    running index)."""
    if not 0 <= index < len(tree[0]):
        raise ValueError("index outside the leaves")
    path = []
    idx = index
    for level in tree[:-1]:
        if idx % 2 == 0:
            sib = idx + 1
        else:
            sib = idx - 1
        if sib < len(level):
            path.append(level[sib])
        else:
            path.append(None)     # odd-leaf promotion: no sibling
        idx //= 2
    return path


def verify_path(path: list[bytes], index: int,
                leaf_hash: bytes, root_hash: bytes) -> bool:
    """Recompute the root from a leaf, its index, and the sibling
    path.  None entries are the promoted-odd-leaf levels."""
    h = leaf_hash
    idx = index
    for sib in path:
        if sib is None:
            pass                  # promoted: hash unchanged
        elif idx % 2 == 0:
            h = _sha(h, sib)
        else:
            h = _sha(sib, h)
        idx //= 2
    return h == root_hash


def tamper_check(tree: list[list[bytes]]) -> bool:
    """Self-audit: every internal node equals the hash of its pair
    (or is a promoted leaf).  True iff the tree is internally
    consistent."""
    for li in range(len(tree) - 1):
        cur, nxt = tree[li], tree[li + 1]
        for i, node in enumerate(nxt):
            if 2 * i + 1 < len(cur):
                if _sha(cur[2 * i], cur[2 * i + 1]) != node:
                    return False
            else:
                if cur[2 * i] != node:
                    return False
    return True


__all__ = ["GHOST_VERSION", "leaf", "build", "root", "open_path",
           "verify_path", "tamper_check"]
