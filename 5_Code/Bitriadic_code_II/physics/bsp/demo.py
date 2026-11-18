"""End-to-end demo: the professional's workflow with YOUR OWN data.

1. Generates a synthetic "measured" interface dataset for the
   monograph case -- sampled from the EXACT Neumann solution with 3%
   realistic noise.  (Synthetic on purpose: this demonstrates the
   bring-your-own-data workflow; replace data/example_measurements.csv
   with your real experiment for actual validation.)
2. Runs the full BSP validation with the user data attached and
   writes results/water_ice_with_data/.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bsp.cases_io import load_case, case_to_params
from bsp.neumann import NeumannOnePhase


def make_synthetic_measurements(path="data/example_measurements.csv"):
    rng = np.random.default_rng(42)
    cfg = load_case("cases/water_ice_monograph.toml")
    p = case_to_params(cfg)
    alpha = p.k_grown / (p.rho * p.cp_grown)
    neu = NeumannOnePhase.freezing(p.T_s, p.T_m, alpha, p.k_grown,
                                   p.rho, p.L, p.cp_grown)
    # 20 "measurement" times between 200 s and 1800 s
    t = np.linspace(200.0, 1800.0, 20)
    s_true = neu.front(t)
    s_meas = s_true * (1.0 + rng.normal(0.0, 0.03, len(t)))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write("# SYNTHETIC demonstration data: exact Neumann front "
                 "positions + 3% Gaussian noise (seed 42).\n"
                 "# Replace this file with your real measurements:\n"
                 "#   columns: t_s (time in seconds), s_m (front "
                 "position in meters)\n")
        fh.write("t_s,s_m\n")
        for ti, si in zip(t, s_meas):
            fh.write(f"{ti:.1f},{si:.6f}\n")
    print(f"synthetic measurements written: {path} ({len(t)} points)")
    return path


if __name__ == "__main__":
    data = make_synthetic_measurements()
    from bsp.cli import main
    code = main(["run", "cases/water_ice_monograph.toml",
                 "--out", "results/water_ice_with_data",
                 "--user-data", data])
    sys.exit(code)
