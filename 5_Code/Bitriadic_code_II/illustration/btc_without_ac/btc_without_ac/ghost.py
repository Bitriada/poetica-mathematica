"""The ghost disc D^2_tau and intrinsic-volume accounting (sec. 6.6.15).

The ghost disc is the trace-layer unit disc

    D^2_tau = { tau s : s in C, |s| <= 1 }  subset UC,

with the Proposition "Ghost Properties" of sec. 6.6.15:
  (i)   nilpotence:   x^2 = 0 for all x in D^2_tau;
  (ii)  invisibility: pi_R(x) = pi_C(x) = 0 for all x in D^2_tau;
  (iii) measure:      D^2_tau has area pi in the (c, d)-plane;
  (iv)  dimension:    V_int(D^2_tau) = 2 (basis {tau, tau i}).

Intrinsic volume is V_int(S) = dim_R span_R{ Z : Z in S }
(sec. 6.6.15, "Intrinsic Volume: Formal Definition").  For sampled
finite point sets we compute it as the rank of the stacked coordinate
matrix, which is exact for Zariski-generic samples.

The monograph's accounting (sec. 6.6.15):

    V_int(S^3_FR) = 4
    V_int(S^1_R)  = 1   (image of pi_R: the interval [−1, 1])
    V_int(D^2_C)  = 2   (image of pi_C: the unit disc)
    V_int(D^2_tau)= 2   (image of pi_tau: the ghost disc)
    1 + 2 + 2 = 5 > 4      -- projections "overlap" in the coordinate a
    visible (pi_R + pi_C) = 3, ghost = 2, total = 3 + 2 − 1 = 4.

The −1 is the real axis a, counted twice by pi_R and pi_C (span of the
pi_R image is contained in the span of the pi_C image).  We verify all
of these ranks numerically.
"""

from __future__ import annotations

import numpy as np

from .uc import UC

__all__ = [
    "ghost_disc_samples",
    "verify_nilpotence",
    "verify_invisibility",
    "ghost_area_montecarlo",
    "intrinsic_volume",
    "volume_accounting",
]


def ghost_disc_samples(n: int, rng: np.random.Generator) -> UC:
    """n points uniformly (by area) on the ghost disc {tau s : |s| <= 1}."""
    r = np.sqrt(rng.uniform(0.0, 1.0, n))
    ang = rng.uniform(0.0, 2.0 * np.pi, n)
    return UC(np.zeros(n), r * np.exp(1j * ang))


# ----------------------------------------------------------------------
# Ghost Properties (i)-(iv)
# ----------------------------------------------------------------------
def verify_nilpotence(x: UC) -> float:
    """(i)  max |x^2| over ghost-disc samples.  Exact zero: the product of
    two pure-trace elements is tau^2 * s s' = 0 (Leibniz rule, value 0)."""
    sq = x * x
    return float(np.max(np.abs(sq.to_real4())))


def verify_invisibility(x: UC) -> dict:
    """(ii)  pi_R(x) = 0 and pi_C(x) = 0 for all ghost-disc points
    (the value coordinates vanish identically)."""
    return {
        "max_abs_pi_real": float(np.max(np.abs(x.val().real))),
        "max_abs_pi_complex": float(np.max(np.abs(x.val()))),
    }


def ghost_area_montecarlo(n: int = 2_000_000,
                          rng: np.random.Generator | None = None) -> tuple[float, float]:
    """(iii)  Monte-Carlo estimate of the ghost disc's area in the (c, d)
    plane: the unit disc, area pi.  Hit-or-miss on the square [−1, 1]^2."""
    rng = rng or np.random.default_rng(11)
    xy = rng.uniform(-1.0, 1.0, (n, 2))
    inside = (xy ** 2).sum(axis=1) <= 1.0
    area = 4.0 * inside.mean()
    se = 4.0 * np.sqrt(inside.mean() * (1 - inside.mean()) / n)
    return float(area), float(se)


# ----------------------------------------------------------------------
# intrinsic volume V_int = dim of the linear span (sec. 6.6.15)
# ----------------------------------------------------------------------
def intrinsic_volume(coords: np.ndarray) -> int:
    """dim_R span of the given points (rank of the coordinate matrix)."""
    coords = np.atleast_2d(np.asarray(coords, dtype=float))
    return int(np.linalg.matrix_rank(coords, tol=1e-9))


def volume_accounting(n: int = 20_000,
                      rng: np.random.Generator | None = None) -> dict:
    """Verify the full intrinsic-volume bookkeeping of sec. 6.6.15.

    Ranks are computed from generic samples, hence exact: a.s. the rank
    equals the dimension of the span of the (infinite) set.
    """
    rng = rng or np.random.default_rng(23)
    from .sphere import sample_sphere

    z = sample_sphere(n, rng)
    x = z.to_real4()                     # columns (a, b, c, d)

    v_int_sphere = intrinsic_volume(x)                       # 4
    v_int_pi_real = intrinsic_volume(x[:, 0:1])              # 1
    v_int_pi_complex = intrinsic_volume(x[:, 0:2])           # 2
    v_int_pi_tau = intrinsic_volume(x[:, 2:4])               # 2
    v_int_visible = v_int_pi_real + v_int_pi_complex         # 3 (1 + 2)
    v_int_ghost = v_int_pi_tau                               # 2
    overlap = v_int_pi_real                                  # span(a) ⊂ span(a, b)
    total = v_int_visible + v_int_ghost - overlap            # 3 + 2 − 1 = 4

    return {
        "V_int(S^3_FR)": v_int_sphere,
        "V_int(pi_R S^3_FR)": v_int_pi_real,
        "V_int(pi_C S^3_FR)": v_int_pi_complex,
        "V_int(pi_tau S^3_FR)": v_int_pi_tau,
        "sum_of_projections": v_int_pi_real + v_int_pi_complex + v_int_pi_tau,
        "sum_exceeds_by": (v_int_pi_real + v_int_pi_complex + v_int_pi_tau)
                          - v_int_sphere,
        "visible": v_int_visible,
        "ghost": v_int_ghost,
        "overlap_correction": overlap,
        "visible_plus_ghost_minus_overlap": total,
        "accounting_consistent": total == v_int_sphere == 4,
    }
