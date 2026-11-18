"""Reassembly: the homeomorphisms phi_k, trace payment, virtual spheres.

From sec. 6.6.15 ("Homeomorphism Construction", "Complete Reassembly
Algorithm") and sec. 6.6.8 (Hopf fiber perspective):

* Base version (sec. 6.6.15).  For Z = v + tau s in D_k with
  v = |v| e^{i theta}, the angle expansion

      theta' = 3 (theta − k * 2pi/3)      (wedge -> full turn)

  defines phi_k(Z) = |v| e^{i theta'} + tau s.  The map D_k -> S^3_FR
  is a *continuous bijection*: every target angle theta' in [0, 2pi)
  has the unique preimage theta = theta'/3 + k*2pi/3 in the wedge, and
  (|v|, s) pass through unchanged.

* Fiber version (sec. 6.6.8).  Each Hopf fiber circle splits into three
  120-degree arcs, S^1 = A0 |_| A1 |_| A2, giving a second partition of
  the sphere by the *trace* angle; stretching the arc to the full
  circle ("pays the trace to stretch") is phi_fiber_k.

* Complete reassembly (sec. 6.6.15): given Z with input domain k_in and
  target sphere_k, "apply the homeomorphism phi_k ∘ phi^{-1}_{k_input}
  (expand angle then compress)".  NOTE -- the two orders differ:
  the literal composition phi_target ∘ phi^{-1}_{k_in} is the identity
  on angles (3 * (theta/3 + k_in 2pi/3) − target 2pi/3 = theta +
  (k_in − target) 2pi ≡ theta), while the glossed order "expand then
  compress", phi^{-1}_target ∘ phi_{k_in}, is the triadic rotation
  R^{target − k_in}.  We implement the glossed order (the one that
  actually moves points into the target sphere) and verify BOTH
  identities numerically.

Honest caveat (documented in the verification report): phi_k is a
continuous bijection but NOT a homeomorphism in the strict sense -- D_k
(the half-open wedge) is non-compact and the inverse is discontinuous
across the seam fiber theta' = 0, exactly like the classical map
[0, 1) -> S^1, t |-> e^{2 pi i t}.  And phi_k scales measure by 3
(piece volume 1/3 -> image volume 1): it is not measure-preserving as a
map of measure spaces; the pushforward of the *conditional* (normalized)
measure on D_k is the uniform measure on S^3_FR.  The "multiplication"
1 -> 3 is therefore label bookkeeping, which is precisely the
monograph's spectator-relative reading.
"""

from __future__ import annotations

import numpy as np

from .sphere import triadic_rotation
from .triadic import assign_domain
from .uc import UC

__all__ = [
    "phi_base", "phi_base_inv", "phi_fiber", "phi_fiber_inv",
    "pay_trace", "reassemble", "virtual_spheres",
    "verify_phi_roundtrip", "verify_phi_image_is_full_sphere",
    "verify_reassembly_composition", "verify_angle_stretch_measure",
    "verify_pay_trace_one_way",
]

_TWO_PI = 2.0 * np.pi


def _masked(z: UC, mask: np.ndarray) -> UC:
    """Subset selection on a (possibly scalar) UC point set."""
    if z.val().ndim == 0:
        return z
    return UC(z.val()[mask], z.tr()[mask])


# ----------------------------------------------------------------------
# base construction (sec. 6.6.15)
# ----------------------------------------------------------------------
def phi_base(z: UC, k: int) -> UC:
    """phi_k(Z) = |v| e^{i 3(theta − k 2pi/3)} + tau s  for Z in D_k.

    Triples the value angle: maps the 120-degree wedge onto the full
    circle.  Precondition: points must lie in D_k (boundary rays are
    measure zero).
    """
    v = z.val()
    r = np.abs(v)
    theta = np.mod(np.angle(v), _TWO_PI)
    theta_new = 3.0 * (theta - k * _TWO_PI / 3.0)
    return UC(r * np.exp(1j * theta_new), z.tr())


def phi_base_inv(z: UC, k: int) -> UC:
    """Inverse image construction: theta -> theta/3 + k*2pi/3.

    Maps the full sphere back into the wedge D_k; defined for all Z.
    """
    v = z.val()
    r = np.abs(v)
    theta = np.mod(np.angle(v), _TWO_PI)
    theta_pre = theta / 3.0 + k * _TWO_PI / 3.0
    return UC(r * np.exp(1j * theta_pre), z.tr())


# ----------------------------------------------------------------------
# fiber construction (sec. 6.6.8)
# ----------------------------------------------------------------------
def phi_fiber(z: UC, k: int) -> UC:
    """Stretch the trace arc A_k to the full fiber circle (sec. 6.6.8).

    phi_fiber_k keeps the value and the fiber radius, and triples the
    trace angle.  Precondition: trace angle in arc A_k (the trace angle
    of Z must satisfy k*2pi/3 <= arg(tr Z) < (k+1)*2pi/3).
    """
    t = z.tr()
    rho = np.abs(t)
    ang = np.mod(np.angle(t), _TWO_PI)
    ang_new = 3.0 * (ang - k * _TWO_PI / 3.0)
    return UC(z.val(), rho * np.exp(1j * ang_new))


def phi_fiber_inv(z: UC, k: int) -> UC:
    """Inverse of the fiber stretch (full circle -> arc A_k)."""
    t = z.tr()
    rho = np.abs(t)
    ang = np.mod(np.angle(t), _TWO_PI)
    ang_pre = ang / 3.0 + k * _TWO_PI / 3.0
    return UC(z.val(), rho * np.exp(1j * ang_pre))


# ----------------------------------------------------------------------
# Fare Principle: paying the trace (sec. 6.6.5)
# ----------------------------------------------------------------------
def pay_trace(z: UC) -> UC:
    """Z = val + tau*tr  ->  val:  discard the trace layer (one-way)."""
    return z.pay_trace()


def verify_pay_trace_one_way() -> dict:
    """The Fare Principle: pay_trace is idempotent and many-to-one.

    Trace can be paid, never created: after payment the map annihilates
    the whole ghost layer (all points with equal value merge).
    """
    ghost = UC(np.zeros(8), np.exp(1j * np.linspace(0, _TWO_PI, 8, endpoint=False)))
    images = pay_trace(ghost).to_real4()
    rng = np.random.default_rng(3)
    from .sphere import sample_sphere
    z = sample_sphere(1000, rng)
    once = pay_trace(z)
    twice = pay_trace(once)
    idempotent_err = float(np.max(np.abs(once.to_real4() - twice.to_real4())))
    return {
        "idempotent_error": idempotent_err,
        "ghost_layer_collapses_to_zero": bool(np.allclose(images, 0.0)),
        "V_int_after_payment": 2,   # only the value plane survives
    }


# ----------------------------------------------------------------------
# complete reassembly (sec. 6.6.15)
# ----------------------------------------------------------------------
def reassemble(z: UC, target_k: int) -> UC:
    """'Expand angle then compress' (the glossed order of sec. 6.6.15):

        phi^{-1}_{target} ∘ phi_{k_input}  =  R^{target − k_input}.

    Every point is moved into the target wedge; the three target images
    are three labeled copies of the full sphere.
    """
    k_in, pole = assign_domain(z)
    if np.any(pole):
        raise ValueError("pole points (val = 0) have no defined wedge")
    expanded = phi_base(z, 0)                    # expand (from D_{k_in})
    theta_exp = np.mod(np.angle(expanded.val()), _TWO_PI)
    r = np.abs(z.val())
    # compress into wedge target_k
    theta_out = theta_exp / 3.0 + target_k * _TWO_PI / 3.0
    return UC(r * np.exp(1j * theta_out), z.tr())


def virtual_spheres(z: UC):
    """The three virtual spheres of sec. 6.6.6 / 6.6.15.

    sphere_k = phi_k(D_k): each third-volume wedge, angle-tripled,
    covers the full sphere.  Returned as a list of (label, UC): every
    point carries the provenance label k.  As SETS the three images
    coincide with S^3_FR; they differ only by label -- the
    spectator-relative 'multiplication'.
    """
    k, _ = assign_domain(z)
    out = []
    for kk in range(3):
        out.append((kk, phi_base(_masked(z, k == kk), kk)))
    return out


# ----------------------------------------------------------------------
# verifications
# ----------------------------------------------------------------------
def verify_phi_roundtrip(z: UC, k: int) -> float:
    """max |phi_k^{-1}(phi_k(Z)) − Z| on points of D_k (should be ~1e-16)."""
    zk = _masked(z, assign_domain(z)[0] == k)
    img = phi_base(zk, k)
    back = phi_base_inv(img, k)
    return float(np.max(np.abs(back.to_real4() - zk.to_real4())))


def verify_phi_image_is_full_sphere(k: int, n: int = 100_000,
                                    rng: np.random.Generator | None = None,
                                    atol: float = 1e-9) -> dict:
    """Constructive proof-by-evaluation that phi_k(D_k) = S^3_FR.

    For uniformly drawn target points Y on the sphere, the constructed
    preimage X = phi_k^{-1}(Y) must (a) lie in D_k and (b) map back to
    Y exactly.  This verifies surjectivity and injectivity on samples.
    """
    from .sphere import sample_sphere

    rng = rng or np.random.default_rng(99)
    y = sample_sphere(n, rng)
    x = phi_base_inv(y, k)
    in_domain = assign_domain(x)[0] == k
    img = phi_base(x, k)
    roundtrip_err = float(np.max(np.abs(img.to_real4() - y.to_real4())))
    return {
        "k": k,
        "n": n,
        "preimages_in_domain_fraction": float(np.mean(in_domain)),
        "max_roundtrip_error": roundtrip_err,
        "surjective_on_samples": bool(np.all(in_domain) and roundtrip_err < atol),
    }


def verify_reassembly_composition(z: UC) -> dict:
    """Check the two readings of the sec. 6.6.15 reassembly composition.

    literal:  phi_t ∘ phi^{-1}_{k_in} = identity (well-formed when
              t == k_in: the intermediate point lies in the outer wedge);
    glossed:  phi^{-1}_t ∘ phi_{k_in} = R^{t − k_in} (per-point power).
    """
    from .sphere import OMEGA

    k_in, _ = assign_domain(z)
    lit_err = 0.0
    glo_err = 0.0
    for t in range(3):
        # literal: phi_t ∘ phi^{-1}_{k_in} on the points with k_in == t
        m = k_in == t
        if np.any(m):
            w = phi_base_inv(_masked(z, m), t)      # S^3 -> D_t
            lit = phi_base(w, t)                    # D_t -> S^3
            lit_err = max(lit_err, float(np.max(np.abs(
                lit.to_real4() - _masked(z, m).to_real4()))))
        # glossed: expand from k_in, then compress into t (per point)
        glo = reassemble(z, t)
        rhs = UC(OMEGA ** (t - k_in) * z.val(), z.tr())
        glo_err = max(glo_err, float(np.max(np.abs(
            glo.to_real4() - rhs.to_real4()))))
    return {
        "literal_order_identity_error": lit_err,
        "glossed_order_rotation_error": glo_err,
        "glossed_equals_triadic_rotation": glo_err < 1e-9,
    }


def verify_angle_stretch_measure(n: int = 400_000,
                                 rng: np.random.Generator | None = None) -> dict:
    """Distributional check: phi_k turns the uniform measure on D_k into
    the uniform measure on S^3_FR (conditional normalization), and the
    *measure scaling factor* of the bijection is exactly 3 (piece volume
    1/3 -> image volume 1).  The image angle histogram must be flat.
    """
    from .sphere import sample_sphere

    rng = rng or np.random.default_rng(5)
    z = sample_sphere(n, rng)
    k, _ = assign_domain(z)
    piece_fraction = float(np.mean(k == 0))
    img = phi_base(_masked(z, k == 0), 0)
    ang = np.mod(np.angle(img.val()), _TWO_PI)
    # chi-square-style flatness: 12 bins, compare to uniform 1/12
    hist, _ = np.histogram(ang, bins=12, range=(0.0, _TWO_PI))
    expected = len(ang) / 12.0
    chi2 = float(np.sum((hist - expected) ** 2 / expected))
    return {
        "piece_volume_D0": piece_fraction,
        "image_volume_as_labeled_copy": 1.0,
        "measure_scaling_factor": 1.0 / piece_fraction,
        "image_angle_chi2_12bins": chi2,
        "image_angle_uniform": bool(abs(piece_fraction - 1.0 / 3.0) < 0.005
                                    and chi2 < 200.0),
    }
