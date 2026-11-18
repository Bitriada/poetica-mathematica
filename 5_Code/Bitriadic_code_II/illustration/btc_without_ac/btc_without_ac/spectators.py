"""Mathematical spectators: projections, apparent counts, spectator shift.

The monograph (secs. 6.6.1, 6.6.15; Ch. VII sec. 6.3a.7) models an
observer algebraically as a pair (pi_S, M_S): a projection onto a
visible subspace plus a measure there.  The case-study spectators:

    Spectator    Projection      Visible subspace   Sees
    Unfathoming  pi_R            R (1D)             magnitude only, [−1, 1]
    Forward      pi_C            C (2D)             value plane D^2, angle
    Backward     pi_C chiral     C (2D)             mirrored disc (memory)
    Deep         pi_C + pi_tau   C + C_tau (4D)     value AND trace

The *apparent count* N_S of a decomposition X = |_|_k X_k is the number
of domains the spectator can distinguish (sec. 6.6.15):

    Unfathoming: N = 1   (angle information lost in [−1, 1])
    Forward:     N = 3   (wedges separated by angle)
    Deep:        N = 3   (angle + trace)

We compute N_S from data rather than hard-coding it: two domains are
*distinguishable* by spectator S iff their images under pi_S have
essentially disjoint supports (occupied-bin Jaccard overlap below a
threshold; the boundary rays and the origin are measure-zero
ambiguities).  For the Unfathoming spectator the three images are
intervals with large overlaps ([−1/2, 1], [−1, 0], (−1/2, 1/2)), so
nothing is distinguished and N = 1; for Forward/Backward/Deep the wedge
sectors are disjoint up to measure zero, so N = 3.  Apparent counts are
then the connected components of the "indistinguishable" relation.

The spectator *shift* operator Sigma (sec. 6.6.6 / 6.6.15) maps one
spectator to another; the apparent number of spheres changes 1 -> 3 and
back 3 -> 1.  It is reversible: nothing about the underlying structure
changes, only the distinguishing power -- the monograph's central point
that the "multiplication" is observer-relative bookkeeping.

Sec. 6.6.1 also writes four spectator *functionals* on point sets
{z_n}: Spec_empty, Spec_+, Spec_-, Spec_x.  Only Spec_empty and the
i-multiplication are literally well defined inside the commutative UC
algebra; the monograph writes the other two with quaternionic units
j, k acting on a "UC-quaternionic configuration", and flags the whole
pass as loose ("would look something like that").  We implement them
under documented UC readings (trace-plane angle for j, combined
phase+trace angle for k = i*j) and label them INTERPRETIVE in the
verification report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from .triadic import assign_domain
from .uc import UC

__all__ = [
    "pi_real", "pi_complex", "pi_complex_chiral", "pi_tau",
    "Spectator", "SPECTATORS", "CASE_STUDY_SPECTATORS",
    "spec_unfathoming", "spec_forward", "spec_backward", "spec_meta",
    "pairwise_overlap", "distinguishability", "apparent_count",
    "spectator_shift", "SHIFT_TABLE_MONOGRAPH",
]


# ----------------------------------------------------------------------
# projections (sec. 6.6.15, "The Three Projections")
# ----------------------------------------------------------------------
def pi_real(z: UC) -> np.ndarray:
    """pi_R(a + bi + tau c + tau d i) = a.  Visible space: the real line."""
    v = z.val()
    return np.stack([np.broadcast_to(v.real, z.trace.real.shape)], axis=-1)


def pi_complex(z: UC) -> np.ndarray:
    """pi_C(...) = a + bi.  Visible space: the value plane (unit disc)."""
    v = z.val()
    return np.stack([v.real, v.imag], axis=-1)


def pi_complex_chiral(z: UC) -> np.ndarray:
    """Backward spectator: the chiral dual of pi_C (conjugate value plane).

    The monograph (sec. 6.6.1) calls the Backward spectator the chiral
    dual of the Forward one; mirroring the disc by complex conjugation
    is the canonical orientation-reversing reading.
    """
    v = np.conj(z.val())
    return np.stack([v.real, v.imag], axis=-1)


def pi_tau(z: UC) -> np.ndarray:
    """pi_tau(...) = tau (c + di).  Visible space: the trace (ghost) plane."""
    t = z.tr()
    return np.stack([t.real, t.imag], axis=-1)


# ----------------------------------------------------------------------
# spectator registry
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Spectator:
    key: str
    name: str
    term: str                 # algebraic term, Ch. VII Def. 6.3a.6
    stabilizer: str           # C8 stabilizer, Ch. VII Prop. 6.3a.2
    sees: str                 # "what it sees", Ch. VII table
    projection: Optional[Callable[[UC], np.ndarray]]
    visible_dim: Optional[int]
    bins: tuple = (48,)       # histogram bins per axis for the overlap test
    limits: tuple = ((-1.0, 1.0),)
    note: str = ""


#: the six spectator positions of Ch. VII sec. 6.3a.7 (registry data;
#: projections are defined for the four used in the case study).
SPECTATORS = {
    "unfathoming": Spectator(
        "unfathoming", "Unfathoming Spectator", "1", "C8 (full group)",
        "pure count / magnitude; projection pi_R sees only [−1, 1]",
        pi_real, 1, bins=(64,), limits=((-1.0, 1.0),),
        note="sees only magnitude; angle information is lost (sec. 6.6.15)"),
    "forward": Spectator(
        "forward", "Forward Spectator", "a + |b|(+i)", "C2 (positive winding)",
        "trajectory / phase; projection pi_C sees the value disc D^2",
        pi_complex, 2, bins=(40, 40), limits=((-1.0, 1.0), (-1.0, 1.0)),
        note="distinguishes the three wedges by angle"),
    "backward": Spectator(
        "backward", "Backward Spectator", "a + |b|(−i)", "C2 (negative winding)",
        "memory / regression; the chiral dual of the Forward view",
        pi_complex_chiral, 2, bins=(40, 40), limits=((-1.0, 1.0), (-1.0, 1.0)),
        note="same distinguishing power as Forward, mirrored"),
    "deep": Spectator(
        "deep", "Deep Spectator", "a", "C4 (quarter group)",
        "value and trace together; projection pi_C + pi_tau, full UC (4D)",
        None, 4,
        note="sees at least everything Forward sees: pi_Deep factors "
             "through pi_C, so distinguishability is at least Forward's "
             "(monograph table: 'Yes (by angle + trace)')"),
    "meta": Spectator(
        "meta", "Meta Spectator", "tau", "mixed",
        "intrinsic vs extrinsic distinction; detects projection artefacts",
        None, None,
        note="no projection in the rigorous table of sec. 6.6.15; "
             "apparent count not defined there"),
    "facilitator": Spectator(
        "facilitator", "Facilitator", "tau i", "trivial",
        "all components simultaneously; second-order observer",
        None, None,
        note="no projection in sec. 6.6.15; 'must split' (Ch. VII) -- "
             "out of scope for the sphere decomposition"),
}

#: spectators with a computable apparent count in sec. 6.6.15
CASE_STUDY_SPECTATORS = ("unfathoming", "forward", "backward", "deep")


# ----------------------------------------------------------------------
# spectator functionals of sec. 6.6.1 (INTERPRETIVE, see module docstring)
# ----------------------------------------------------------------------
def spec_unfathoming(z: UC) -> float:
    """Spec_empty(z) = (1/N) sum ||z_n||.  Magnitude only."""
    return float(np.mean(z.norm_fr()))


def spec_forward(z: UC) -> float:
    """Spec_+(z) = (1/N) sum arg(i * z_n) * ||z_n||.  Phase view.

    i * z has value i*val(z) (UC is commutative), so this is the mean
    value-plane angle shifted by +pi/2, magnitude-weighted.
    """
    ang = np.angle(1j * z.val())
    return float(np.mean(ang * z.norm_fr()))


def spec_backward(z: UC) -> float:
    """Spec_-(z) = (1/N) sum arg(j * z_n) * ||z_n||.  Entropy view.

    INTERPRETIVE: the monograph multiplies by the quaternionic unit j,
    which does not act inside commutative UC.  Adopted reading: j maps
    the trace coordinates (c, d) into the value slot, i.e. the angle of
    the trace plane -- the "entropic orientation".
    """
    ang = np.angle(z.tr())
    return float(np.mean(ang * z.norm_fr()))


def spec_meta(z: UC) -> float:
    """Spec_x(z) = (1/N) sum arg(k * z_n) * ||z_n||.  Cross view.

    INTERPRETIVE: k = i*j combines phase and entropy; adopted reading:
    the wrapped sum of value angle (+pi/2 shift) and trace angle.
    """
    ang = np.mod(np.angle(1j * z.val()) + np.angle(z.tr()) + np.pi, 2 * np.pi) - np.pi
    return float(np.mean(ang * z.norm_fr()))


# ----------------------------------------------------------------------
# distinguishability and apparent counts (sec. 6.6.15)
# ----------------------------------------------------------------------
_OVERLAP_THRESHOLD = 0.15  # calibrated: Unfathoming pairs score ~0.3-0.4,
                           # wedge sectors score < 0.10 (see tests/demo)


def pairwise_overlap(spectator: Spectator, z: UC, labels=None) -> np.ndarray:
    """3x3 matrix of occupied-bin Jaccard overlaps of pi_S(D_k), pi_S(D_l).

    For the Deep spectator the matrix is Forward's (its projection
    factors through pi_C; seeing more can only add distinguishing power,
    and the monograph table lists N_Deep = N_Forward = 3).
    """
    if spectator.key == "deep":
        spectator = SPECTATORS["forward"]
    if spectator.projection is None:
        raise ValueError(f"spectator {spectator.key!r} has no projection")
    if labels is None:
        labels, _ = assign_domain(z)

    coords = spectator.projection(z)
    dim = coords.shape[-1]
    bins = spectator.bins[:dim]
    limits = spectator.limits[:dim]

    occ = []
    for k in range(3):
        m = labels == k
        h, _ = np.histogramdd(coords[m], bins=bins, range=limits)
        occ.append(h > 0)
    out = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            inter = np.logical_and(occ[i], occ[j]).sum()
            union = np.logical_or(occ[i], occ[j]).sum()
            out[i, j] = inter / union if union else 0.0
    return out


def distinguishability(spectator: Spectator, z: UC, labels=None,
                       threshold: float = _OVERLAP_THRESHOLD) -> np.ndarray:
    """Boolean 3x3: domains (i, j) distinguishable by this spectator."""
    return pairwise_overlap(spectator, z, labels) < threshold


def apparent_count(spectator: Spectator, z: UC, labels=None,
                   threshold: float = _OVERLAP_THRESHOLD) -> int:
    """N_S(S^3_FR): number of domains the spectator can tell apart.

    Domains merge when their pi_S images overlap above threshold;
    N_S is the number of connected components of the merge graph.
    """
    dis = distinguishability(spectator, z, labels, threshold)
    merged = np.ones(3, dtype=bool)
    for i in range(3):
        for j in range(i + 1, 3):
            if not dis[i, j]:
                merged[i] = merged[j] = True  # same class; track via union-find
    # union-find over "not distinguishable" edges
    parent = list(range(3))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(3):
        for j in range(i + 1, 3):
            if not dis[i, j]:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    return len({find(i) for i in range(3)})


# ----------------------------------------------------------------------
# spectator shift (secs. 6.6.6, 6.6.15)
# ----------------------------------------------------------------------
def spectator_shift(s_from: str, s_to: str, z: UC, labels=None) -> tuple[int, int]:
    """Sigma: (S_from, S_to) -> (N_from, N_to).

    The shift operator changes the apparent sphere count.  It is
    reversible in the monograph's sense: Sigma^-1 returns the count,
    because the underlying structure never changed.
    """
    n_from = apparent_count(SPECTATORS[s_from], z, labels)
    n_to = apparent_count(SPECTATORS[s_to], z, labels)
    return n_from, n_to


#: the shift table as printed in sec. 6.6.6 of the monograph (narrative
#: variant; note Deep is listed there with N = 1, while the corrected
#: table of sec. 6.6.15 has N_Deep = 3 -- the report documents this).
SHIFT_TABLE_MONOGRAPH = [
    ("Unfathoming", "Deep", "1 -> 1 (trace revealed)"),
    ("Deep", "Forward", "1 -> 3 (triadic split)"),
    ("Forward", "Unfathoming", "3 -> 1 (collapse to value)"),
]
