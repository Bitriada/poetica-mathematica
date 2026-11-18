"""The classical side: Banach-Tarski's F2 machinery, and where AC enters.

Sec. 6.6.2 of the monograph describes the classical proof:

  Theorem (Banach-Tarski, 1924).  A solid ball in R^3 decomposes into
  finitely many disjoint subsets reassembled (by rotations and
  translations only) into two balls identical to the first.  The proof
  uses the free group F2 on two generators, a paradoxical decomposition
  of F2, and the Axiom of Choice.  "AC is invoked to assert that such a
  selection [one representative per orbit] exists, without providing a
  method."

This module makes every word of that description computable:

1. `paradoxical_decomposition` -- the 4-piece paradoxical decomposition
   of F2 = <a, b> itself.  With S(x) = reduced words starting with x:

       F2 = {e} |_| S(a) |_| S(a^-1) |_| S(b) |_| S(b^-1),
       F2 = S(a) |_| a S(a^-1),      F2 = S(b) |_| b S(b^-1),

   so the four pieces S(a), S(a^-1), S(b), S(b^-1) assemble TWO copies
   of F2 under the group action.  This part is fully constructive and
   choice-free (verified on truncated balls B_L).

2. `free_rotation_generators` -- the standard rotation pair with
   cos(angle) = 3/5 about perpendicular axes (Swierczkowski 1958),
   which generates a free subgroup of SO(3); we spot-check freeness on
   all reduced words up to a given length (finite evidence).

3. `orbit_transfer` -- transferring the decomposition to the orbit of a
   single point x0 on S^2: constructive for ONE explicitly chosen orbit
   (no choice needed), two copies of the orbit come out.

4. `foelner_ratio` -- why AC (or non-measurability) is unavoidable on
   the full sphere: by Tarski's theorem a group is non-amenable iff it
   admits a paradoxical decomposition.  We compute the Folner boundary
   ratios: for F2, |dB_L|/|B_L| -> 2 (stays bounded away from 0 -- non-
   amenable, no measurable fundamental domain, pieces must be
   non-measurable); for Z it -> 0 (amenable -- Z admits NO paradoxical
   decomposition); finite groups such as C3 are amenable trivially
   (boundary vanishes once the ball fills the group).  This is the
   sharp quantitative reason the monograph's C3 decomposition cannot be
   a classical volume-doubling: finite symmetry groups are amenable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "reduce_word", "multiply_words", "ball_words", "ball_size",
    "word_to_str", "paradoxical_decomposition",
    "free_rotation_generators", "check_freeness",
    "orbit_transfer", "foelner_ratio", "where_ac_enters",
    "COMPARISON_TABLE",
]

# word alphabet: 0 = a, 1 = b, 2 = a^-1, 3 = b^-1  (as integer tuples)
_LETTERS = "abAB"
_CANCEL = {(0, 2), (2, 0), (1, 3), (3, 1)}


def reduce_word(w: tuple[int, ...]) -> tuple[int, ...]:
    """Free reduction: cancel aa^-1, a^-1a, bb^-1, b^-1b pairs."""
    stack: list[int] = []
    for g in w:
        if stack and (stack[-1], g) in _CANCEL:
            stack.pop()
        else:
            stack.append(g)
    return tuple(stack)


def multiply_words(w1: tuple[int, ...], w2: tuple[int, ...]) -> tuple[int, ...]:
    return reduce_word(w1 + w2)


def word_to_str(w: tuple[int, ...]) -> str:
    return "".join(_LETTERS[g] for g in w) or "e"


def ball_size(L: int) -> int:
    """|B_L| = 1 + sum_{k<=L} 4*3^(k-1) = 2*3^L - 1 (reduced words)."""
    return 2 * 3 ** L - 1


def ball_words(L: int) -> list[tuple[int, ...]]:
    """All reduced words of length <= L (BFS enumeration)."""
    out = [()]
    frontier = [()]
    for _ in range(L):
        nxt = []
        for w in frontier:
            last = w[-1] if w else None
            for g in range(4):
                if last is not None and (last, g) in _CANCEL:
                    continue
                nxt.append(w + (g,))
        out.extend(nxt)
        frontier = nxt
    return out


# ----------------------------------------------------------------------
# 1. the paradoxical decomposition of F2 (constructive, choice-free)
# ----------------------------------------------------------------------
@dataclass
class ParadoxReport:
    L: int
    words: int
    partition_ok: bool
    copy1_cover: bool
    copy2_cover: bool
    copies_disjoint_pieces: bool
    pieces: dict
    copy1: set
    copy2: set


def paradoxical_decomposition(L: int = 7) -> ParadoxReport:
    """Verify the 4-piece paradoxical decomposition of F2 on B_L.

    pieces S(a), S(a^-1), S(b), S(b^-1) partition B_L \\ {e};
    copy1 = S(a) + a.S(a^-1) and copy2 = S(b) + b.S(b^-1) each cover
    B_{L-1}; the two copies use disjoint pieces.  Group translations
    are the 'isometries'; no choice is made anywhere.
    """
    words = ball_words(L)
    word_set = set(words)
    pieces = {g: set() for g in range(4)}  # by first letter
    for w in words:
        if w:
            pieces[w[0]].add(w)
        # e is handled separately (it is the image of a.a^-1 and b.b^-1)

    partition_ok = (
        sum(len(pieces[g]) for g in range(4)) == len(words) - 1
        and all(w in word_set for p in pieces.values() for w in p)
    )

    A, B, a_inv, b_inv = 0, 1, 2, 3          # first-letter piece keys
    a, b = (0,), (1,)                        # generator words
    copy1 = pieces[A] | {multiply_words(a, w) for w in pieces[a_inv]}
    copy2 = pieces[B] | {multiply_words(b, w) for w in pieces[b_inv]}

    sub_ball = set(ball_words(L - 1))
    copy1_cover = sub_ball <= copy1
    copy2_cover = sub_ball <= copy2
    disjoint_pieces = not (pieces[A] | pieces[a_inv]) & (pieces[B] | pieces[b_inv])

    return ParadoxReport(
        L=L,
        words=len(words),
        partition_ok=partition_ok,
        copy1_cover=copy1_cover,
        copy2_cover=copy2_cover,
        copies_disjoint_pieces=disjoint_pieces,
        pieces={word_to_str((g,)): len(pieces[g]) for g in range(4)},
        copy1=copy1,
        copy2=copy2,
    )


# ----------------------------------------------------------------------
# 2. the free rotation pair (Swierczkowski 1958; cos = 3/5)
# ----------------------------------------------------------------------
def free_rotation_generators() -> tuple[np.ndarray, np.ndarray]:
    """(A, B): rotations by arccos(3/5) about the z- and x-axes.

    The subgroup of SO(3) they generate is free on {A, B} (classical
    result used in every constructive account of Banach-Tarski; the
    3-4-5 Pythagorean angle makes the entries exact rationals).
    """
    c, s = 3.0 / 5.0, 4.0 / 5.0
    A = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    B = np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])
    return A, B


def check_freeness(L: int = 5) -> dict:
    """Finite evidence: no non-empty reduced word of length <= L acts as
    the identity (and orbit points of a generic x0 stay distinct)."""
    mats = free_rotation_generators()
    A, B = mats
    gens = {0: A, 1: B, 2: A.T, 3: B.T}   # rotations: inverse = transpose
    x0 = np.array([0.3127, -0.7415, 0.5943])
    x0 /= np.linalg.norm(x0)
    min_dev = np.inf
    orbit = set()
    for w in ball_words(L):
        if not w:
            continue
        M = np.eye(3)
        for g in w:
            M = M @ gens[g]
        dev = float(np.max(np.abs(M - np.eye(3))))
        min_dev = min(min_dev, dev)
        y = M @ x0
        orbit.add((round(y[0], 9), round(y[1], 9), round(y[2], 9)))
    n_words = ball_size(L) - 1
    return {
        "max_length": L,
        "words_checked": n_words,
        "min_identity_deviation": min_dev,
        "distinct_orbit_points": len(orbit),
        "no_word_is_identity": min_dev > 1e-9,
        "orbit_injective": len(orbit) == n_words,
    }


# ----------------------------------------------------------------------
# 3. transfer to one explicitly chosen orbit (still choice-free)
# ----------------------------------------------------------------------
def orbit_transfer(L: int = 5) -> dict:
    """The paradoxical decomposition transferred to the orbit of x0.

    Choosing x0 explicitly (we take a fixed generic point) makes the
    transfer constructive: the orbit F2.x0 is countable, pieces
    S(g).x0 are disjoint, and the two reassembled copies equal the
    orbit.  The Axiom of Choice is only needed to do this for ALL
    (uncountably many) orbits at once.
    """
    mats = free_rotation_generators()
    A, B = mats
    gens = {0: A, 1: B, 2: A.T, 3: B.T}
    x0 = np.array([0.3127, -0.7415, 0.5943])
    x0 /= np.linalg.norm(x0)

    def act(w, x):
        M = np.eye(3)
        for g in w:
            M = M @ gens[g]
        return M @ x

    words = [w for w in ball_words(L) if w]
    pieces = {g: [] for g in range(4)}
    for w in words:
        pieces[w[0]].append(act(w, x0))

    def key(y):
        return (round(y[0], 9), round(y[1], 9), round(y[2], 9))

    orbit = {key(act(w, x0)) for w in words}
    p_keys = {g: {key(y) for y in ys} for g, ys in pieces.items()}
    disjoint = (
        not (p_keys[0] & p_keys[2]) and not (p_keys[0] & p_keys[1])
        and not (p_keys[0] & p_keys[3]) and not (p_keys[2] & p_keys[1])
        and not (p_keys[2] & p_keys[3]) and not (p_keys[1] & p_keys[3])
    )
    # reassembled copies: a.S(A).x0 and b.S(B).x0
    copy1 = {key(act((0,) + w, x0)) for w in words if w[0] == 2}
    copy2 = {key(act((1,) + w, x0)) for w in words if w[0] == 3}
    return {
        "max_length": L,
        "orbit_size": len(orbit),
        "pieces_disjoint": disjoint,
        "pieces_cover_orbit": sum(len(s) for s in p_keys.values()) == len(orbit),
        "copy1_size": len(copy1),
        "copy2_size": len(copy2),
        "truncated_note": "copies cover the orbit up to length effects "
                          "(translations move length +1 words outward)",
    }


# ----------------------------------------------------------------------
# 4. amenability: the sharp reason AC cannot be avoided classically
# ----------------------------------------------------------------------
def foelner_ratio(L_max: int = 8) -> dict:
    """Boundary ratios |dB_L| / |B_L|: F2 stays ~2, Z decays to 0.

    Tarski's theorem: non-amenable <=> paradoxical decomposition.  A
    Folner sequence (boundary ratio -> 0) exists exactly for amenable
    groups.  F2 has none -- its boundary ratio converges to 2 -- hence
    any paradoxical pieces for an F2-action must be non-measurable and
    the orbit representatives cannot be chosen measurably: this is
    where the Axiom of Choice enters the classical proof.  Finite
    groups (C3) are amenable: the boundary vanishes once B_L = G.
    """
    f2 = []
    for L in range(1, L_max + 1):
        size = ball_size(L)
        boundary = ball_size(L + 1) - ball_size(L)
        f2.append((L, boundary / size))
    zz = [(L, 2 / (2 * L + 1)) for L in range(1, 10 * L_max + 1)]
    return {
        "F2_ratios": f2,
        "F2_limit": 2.0,
        "Z_ratios": zz,
        "Z_limit": 0.0,
        "C3_note": "finite groups are amenable (boundary of G itself is "
                   "empty), so C3 admits no paradoxical decomposition -- "
                   "the UC 'multiplication' cannot be classical volume "
                   "doubling, consistent with the monograph's "
                   "spectator-relative reading (sec. 6.6.7).",
    }


def where_ac_enters() -> str:
    """Explanatory text for the report (sec. 6.6.2, 6.6.7)."""
    return (
        "The F2-level decomposition is constructive and choice-free, and it "
        "transfers constructively to any SINGLE explicitly chosen orbit. "
        "AC enters exactly one place: the sphere is the disjoint union of "
        "uncountably many F2-orbits, and the proof must pick one "
        "representative from each orbit to copy the 4-piece pattern onto "
        "the whole sphere. By non-amenability (Folner ratio -> 2) there is "
        "no measurable way to make those selections, so AC is invoked to "
        "assert a transversal exists 'without providing a method' -- the "
        "monograph's phrasing. The UC decomposition of sec. 6.6 needs no "
        "such step: the domains are given by an explicit O(1) angle test."
    )


# ----------------------------------------------------------------------
# the monograph's comparison table (sec. 6.6.9)
# ----------------------------------------------------------------------
COMPARISON_TABLE = [
    ("Property", "Classical BT", "UC Decomposition"),
    ("Number of pieces", "~5 (4 + identity)", "3"),
    ("Requires AC", "Yes (orbit transversal)", "No (explicit angle test)"),
    ("Pieces measurable", "No", "Yes (volume 1/3 each)"),
    ("Volume preserved", "No (paradox: doubling)", "Yes (extrinsic)"),
    ("Structure preserved", "N/A", "Redistributed (trace layer)"),
    ("Spectator-dependent", "No", "Yes (apparent count 1 <-> 3)"),
    ("Symmetry group", "F2 (free, non-amenable)", "C3 (finite, amenable)"),
]
