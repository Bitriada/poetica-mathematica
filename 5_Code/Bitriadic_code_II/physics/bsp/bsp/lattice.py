"""The Bitriada lattices of the BSP paper (sec. 4) -- with checks.

Structure (Def. 4.1): the 1DB lattice has 117 points in 3 zones x
3 levels:

    L (Low)     3 points/zone x 3 zones  =  9
    M (Medium)  9 points/zone x 3 zones  = 27
    H (High)   27 points/zone x 3 zones  = 81
                                 total   = 117

Zone values (Arithmetic Bitriada): L-level  N_L(z, i) = z * 2^i for
i = 1..3 (Prime 2,4,8 / Reflection 4,8,16 / Projection 6,12,24);
M-level  N_M(z, i, j) = 2^(2 i j z)  (the paper's M-meta table at
z = 1: 4,16,64 / 16,256,4096 / 64,4096,262144).

2DB (Def. 4.2): 243 positions = 81 x 3 (H-level projection with zone
accounting).

IMPORTANT AUDIT NOTE (used by the assessment report): Algorithm 9.1 of
the paper never touches the 1DB/2DB lattices -- it runs on a plain
uniform lattice x_i = i * dx.  The lattices are sound combinatorial
objects (this module verifies their counts and value tables), but they
are NOT load-bearing for the solver.  The solver's "trace" is the
operational descendant of the lattice trace idea: c(p) in {0, 1}.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["Lattice1DB", "Lattice2DB", "lattice_report", "ZONES", "LEVELS"]

ZONES = ("Prime", "Reflection", "Projection")   # z = 1, 2, 3
LEVELS = ("L", "M", "H")


@dataclass(frozen=True)
class Lattice1DB:
    """The 117-point Arithmetic Bitriada lattice (3 zones x 3 levels).

    level point-counts: L -> 3 per zone, M -> 9, H -> 27
    (the factor 3 in 9/27/81 = 3 x (3/9/27) is the zone structure).
    """

    @staticmethod
    def level_sizes() -> dict:
        return {"L": 9, "M": 27, "H": 81}

    @staticmethod
    def total() -> int:
        return 117

    @staticmethod
    def points() -> list[tuple]:
        """All 117 (level, zone, index) coordinates, index 1-based."""
        pts = []
        for lvl, per_zone in (("L", 3), ("M", 9), ("H", 27)):
            for z in (1, 2, 3):
                for i in range(1, per_zone + 1):
                    pts.append((lvl, z, i))
        return pts

    # -- value formulas ------------------------------------------------
    @staticmethod
    def value_L(z: int, i: int) -> int:
        """N_L(z, i) = z * 2^i  (L-level base values, i = 1..3)."""
        return z * 2 ** i

    @staticmethod
    def value_M(z: int, i: int, j: int) -> int:
        """N_M(z, i, j) = 2^(2 i j z)  (M-level, i, j = 1..3)."""
        return 2 ** (2 * i * j * z)

    @staticmethod
    def table_L() -> dict:
        """The paper's L-level table: zone -> [i=1, i=2, i=3]."""
        return {ZONES[z - 1]: [Lattice1DB.value_L(z, i) for i in (1, 2, 3)]
                for z in (1, 2, 3)}

    @staticmethod
    def table_M(z: int = 1) -> np.ndarray:
        """The paper's M-meta table for zone z (3x3 matrix)."""
        return np.array([[Lattice1DB.value_M(z, i, j) for j in (1, 2, 3)]
                         for i in (1, 2, 3)])


@dataclass(frozen=True)
class Lattice2DB:
    """The 243-position hyper-lattice (Def. 4.2).

    1DB has 117 points; the naive count would be 117 x 3 = 351, but
    with proper zone accounting the H-level projection carries
    81 x 3 = 243 positions.
    """

    @staticmethod
    def total() -> int:
        return 243

    @staticmethod
    def naive_count() -> int:
        return 117 * 3

    @staticmethod
    def h_level_count() -> int:
        return 81 * 3


def lattice_report() -> dict:
    """Verify every count and value table the paper states."""
    tL = Lattice1DB.table_L()
    expected_L = {"Prime": [2, 4, 8], "Reflection": [4, 8, 16],
                  "Projection": [6, 12, 24]}
    tM = Lattice1DB.table_M(1)
    expected_M = np.array([[4, 16, 64], [16, 256, 4096],
                           [64, 4096, 262144]])
    pts = Lattice1DB.points()
    return {
        "1DB_level_sizes": Lattice1DB.level_sizes(),
        "1DB_sum_9_27_81": sum(Lattice1DB.level_sizes().values()),
        "1DB_total_claim": Lattice1DB.total(),
        "1DB_points_enumerated": len(pts),
        "1DB_points_match": len(pts) == 117,
        "L_table_matches_paper": tL == expected_L,
        "M_table_matches_paper": bool(np.array_equal(tM, expected_M)),
        "2DB_total_claim": Lattice2DB.total(),
        "2DB_naive_351_vs_zone_accounting_243":
            (Lattice2DB.naive_count(), Lattice2DB.h_level_count()),
        "2DB_consistent": Lattice2DB.h_level_count() == 243,
        "used_by_algorithm_9_1": False,
    }
