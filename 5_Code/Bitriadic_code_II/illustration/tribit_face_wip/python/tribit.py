"""tribit.py -- the Ultra-Complex algebra UC and the Tribit machine.

Implements the structures of Poetica Mathematica, Chapter IV:

  * the tribit z = a + b*i + tau*c + tau*d*i  with  i^2 = -1,
    tau^2 = 0, i*tau = tau*i                    (Sec. 4.2.1)
  * the eight rotations O_k, k = 0..7, rotating the trace plane by
    k*pi/4 while leaving the value plane fixed; a cyclic group C8
    with explicit 4x4 matrices                    (Sec. 4.2.3)
  * the null-transit gates: atlas 0/a (kills the trace, classical
    readout) and overdrive w/0 (lifts the value into the trace) --
    a one-way switch                               (Sec. 4.5.2a)
  * the three projections pi_val, pi_geom, pi_info of Tribit Space
    T = R^4                                        (Def. 4.2.3.2)

UC is the coordinate algebra of the geometric axis; the Fare-Riemann
sphere (sphere.py) is its geometric realisation.
"""

from __future__ import annotations

import math
from cmath import isclose as _cisclose  # noqa: F401  (kept for callers)

TOL = 1e-9


class UC:
    """An element of UC = C[tau]/(tau^2), stored as (a, b, c, d).

    value  v = a + b*i      the classical content of a computation
    trace  t = c + d*i      the nilpotent fare: history that cannot
                            be duplicated, because tau^2 = 0
    """

    __slots__ = ("a", "b", "c", "d")

    def __init__(self, a=0.0, b=0.0, c=0.0, d=0.0):
        self.a, self.b, self.c, self.d = (
            float(a), float(b), float(c), float(d))

    # ---------- constructors ----------

    @classmethod
    def from_value(cls, v: complex) -> "UC":
        """A pure value, no trace (a point of the value plane)."""
        return cls(v.real, v.imag, 0.0, 0.0)

    # ---------- projections (Def. 4.2.3.2) ----------

    @property
    def val(self) -> complex:
        """pi_val: the value projection (a, b)."""
        return complex(self.a, self.b)

    @property
    def tr(self) -> complex:
        """The trace projection (c, d) as a complex number."""
        return complex(self.c, self.d)

    def pi_geom(self) -> float:
        """pi_geom: the real fare axis (c)."""
        return self.c

    def pi_info(self) -> float:
        """pi_info: the informatic fare axis (d)."""
        return self.d

    # ---------- norms ----------

    def norm_fr(self) -> float:
        """Fare-Riemann norm ||z||_FR = sqrt(|val|^2 + |tr|^2)."""
        return math.sqrt(self.a ** 2 + self.b ** 2 + self.c ** 2 + self.d ** 2)

    def norm_tau(self) -> float:
        """Intrinsic metric ||z||_tau = |val| + |tr|  (Def. 4.2.4.6)."""
        return abs(self.val) + abs(self.tr)

    def on_sphere(self, tol=1e-9) -> bool:
        return abs(self.norm_fr() - 1.0) <= tol

    def normalized(self) -> "UC":
        """Radial projection onto the Fare-Riemann sphere S3_FR."""
        n = self.norm_fr()
        if n == 0:
            raise ValueError("the null origin has no direction to project")
        return UC(self.a / n, self.b / n, self.c / n, self.d / n)

    # ---------- ring operations ----------

    def __add__(self, o: "UC") -> "UC":
        return UC(self.a + o.a, self.b + o.b, self.c + o.c, self.d + o.d)

    def __sub__(self, o: "UC") -> "UC":
        return UC(self.a - o.a, self.b - o.b, self.c - o.c, self.d - o.d)

    def __mul__(self, o: "UC") -> "UC":
        """(v + tau t)(v' + tau t') = v v' + tau (v t' + v' t).

        The Leibniz rule IS the Fare Principle: the trace of a product
        is the weighted sum of the individual traces.  All trace-trace
        products vanish because tau^2 = 0.
        """
        v, t = self.val, self.tr
        w, s = o.val, o.tr
        p, q = v * w, v * s + w * t
        return UC(p.real, p.imag, q.real, q.imag)

    def __eq__(self, o) -> bool:
        if not isinstance(o, UC):
            return NotImplemented
        return (abs(self.a - o.a) < TOL and abs(self.b - o.b) < TOL
                and abs(self.c - o.c) < TOL and abs(self.d - o.d) < TOL)

    def almost(self, o: "UC", tol=TOL) -> bool:
        return (abs(self.a - o.a) < tol and abs(self.b - o.b) < tol
                and abs(self.c - o.c) < tol and abs(self.d - o.d) < tol)

    # ---------- the C8 rotation group (Def. 4.2.3.3) ----------

    def rotate(self, k: int) -> "UC":
        """O_k: rotate the trace plane by k*pi/4, value untouched.

        O_k(a,b,c,d) = (a, b,
                        c cos(k pi/4) - d sin(k pi/4),
                        c sin(k pi/4) + d cos(k pi/4))
        """
        k %= 8
        ang = k * math.pi / 4.0
        cs, sn = math.cos(ang), math.sin(ang)
        return UC(self.a, self.b,
                  self.c * cs - self.d * sn,
                  self.c * sn + self.d * cs)

    __call__ = rotate  # z(k) == O_k(z)

    # ---------- the null-transit gates (Sec. 4.5.2a) ----------

    def atlas(self) -> "UC":
        """Gate 0/a: kill the trace, project to the value plane.

        The exit back to a classical readout.  Discards the fare.
        """
        return UC(self.a, self.b, 0.0, 0.0)

    def overdrive(self) -> "UC":
        """Gate w/0: lift the value into the trace: z -> val + tau*val.

        Memory has depth exactly one (tau^2 = 0): the lift cannot
        accumulate, so overdrive is idempotent -- the model of "you
        can remember, but only once".
        """
        return UC(self.a, self.b, self.a, self.b)

    # ---------- display ----------

    def __repr__(self) -> str:
        def f(x):
            return f"{x:.4f}".rstrip("0").rstrip(".") if abs(x) > 1e-12 else "0"
        return (f"UC({f(self.a)} {f(self.b):+}i "
                f"+ tau({f(self.c)} {f(self.d):+}i))")

    def to_json(self) -> list:
        return [self.a, self.b, self.c, self.d]


# --------------------------------------------------------------------------
# Module-level helpers
# --------------------------------------------------------------------------

def O_matrix(k: int) -> list:
    """The 4x4 real matrix of O_k at UC scale, basis {1, i, tau, i*tau}.

    Definition 4.2.3.3: O_k(z) = val(z) + tau * e^{ik pi/4} * tr(z) --
    the trace block rotates, the value block is the identity:

        [1  0   0   0 ]
        [0  1   0   0 ]
        [0  0  cos -sin]
        [0  0  sin  cos]

    Note: Proposition 4.2.3.5 states a block-diagonal matrix with TWO
    identical rotation blocks (value rotating too).  That is the action
    of the grammar lifted to the full Transit-Fare Algebra, where the
    extended O_k rotate all graded components simultaneously (Remark
    4.2.3.3a); at the 1DB/UC scale the definition and the TriPU
    description (Sec. 4.5.2a) leave the value plane strictly unchanged.
    See O_matrix_lifted for the two-block form; verify.py checks both.
    """
    ang = (k % 8) * math.pi / 4.0
    cs, sn = math.cos(ang), math.sin(ang)
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, cs, -sn],
        [0.0, 0.0, sn, cs],
    ]


def O_matrix_lifted(k: int) -> list:
    """The two-identical-blocks matrix of Proposition 4.2.3.5.

    Simultaneous rotation of value and trace planes: the fractal lift
    of the same grammar to the TFA scale (Remark 4.2.3.3a).
    """
    ang = (k % 8) * math.pi / 4.0
    cs, sn = math.cos(ang), math.sin(ang)
    return [
        [cs, -sn, 0.0, 0.0],
        [sn, cs, 0.0, 0.0],
        [0.0, 0.0, cs, -sn],
        [0.0, 0.0, sn, cs],
    ]


def apply_O_matrix(k: int, z: UC) -> UC:
    m = O_matrix(k)
    x = [z.a, z.b, z.c, z.d]
    y = [sum(m[i][j] * x[j] for j in range(4)) for i in range(4)]
    return UC(*y)


def TAU() -> UC:
    """The bare nilpotent generator tau (pure trace, real axis)."""
    return UC(0.0, 0.0, 1.0, 0.0)


def random_tribit(rng) -> UC:
    """A random UC element with components in [-1, 1]."""
    return UC(rng.uniform(-1, 1), rng.uniform(-1, 1),
              rng.uniform(-1, 1), rng.uniform(-1, 1))
