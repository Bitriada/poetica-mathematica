"""Case input: config files (TOML/JSON), material presets, user data.

A "case" is everything needed to run one BSP validation:

    [case]      name, mode (freezing|melting), T_m, T_s, T_0,
                length, dx, t_end, temp_unit (C|K)
    [material]  preset = "water_ice_monograph" | ...  OR explicit
                rho, L, k_grown, cp_grown, k_bulk, cp_bulk
    [run]       event_mode (integral|explicit), substep_safety,
                max_events
    [validation]
                neumann = true, enthalpy = true,
                convergence = true, convergence_levels = 4,
                user_data = "path/to/measurements.csv"
                (columns: t_s, s_m -- header optional)

Presets are typical handbook values for well-known phase-change
materials.  For critical work ALWAYS override with your own measured
properties -- the tool is designed for exactly that.
"""

from __future__ import annotations

import csv
import json
import os

import numpy as np

try:                                    # Python 3.11+
    import tomllib
except ImportError:                     # pragma: no cover
    tomllib = None

from .solver import BSPParams

__all__ = ["PRESETS", "load_case", "case_to_params", "load_user_data"]

#: typical handbook values (verify against your own source before
#: critical use).  Solid/liquid conductivity split where meaningful.
PRESETS = {
    # the BSP paper's own numbers (sec. 12.2 / appendix B.1):
    # water density/specific heat with ice conductivity; NOTE the
    # paper's alpha = 1.15e-6 is inconsistent with these (audit A3) --
    # this preset uses the self-consistent alpha = k/(rho cp).
    "water_ice_monograph": dict(
        rho=1000.0, L=334000.0, k_grown=2.2, cp_grown=4186.0,
        k_bulk=0.6, cp_bulk=4186.0,
        note="paper's mixed water/ice values; alpha inconsistent"),
    # physically consistent ice (grown) / water (bulk)
    "water_ice": dict(
        rho=917.0, L=333600.0, k_grown=2.22, cp_grown=2050.0,
        k_bulk=0.56, cp_bulk=4186.0,
        note="consistent ice/water properties"),
    "aluminum": dict(
        rho=2700.0, L=397000.0, k_grown=237.0, cp_grown=900.0,
        k_bulk=237.0, cp_bulk=900.0, note="handbook values"),
    "copper": dict(
        rho=8960.0, L=205000.0, k_grown=398.0, cp_grown=385.0,
        k_bulk=398.0, cp_bulk=385.0, note="handbook values"),
    "tin": dict(
        rho=7310.0, L=59500.0, k_grown=67.0, cp_grown=228.0,
        k_bulk=67.0, cp_bulk=228.0, note="handbook values"),
    "paraffin_wax": dict(
        rho=900.0, L=180000.0, k_grown=0.21, cp_grown=2500.0,
        k_bulk=0.21, cp_bulk=2500.0,
        note="typical PCM paraffin; verify your grade"),
}


def load_case(path: str) -> dict:
    """Load a case config (TOML or JSON) into a plain dict."""
    with open(path, "rb") as fh:
        raw = fh.read()
    if path.lower().endswith(".toml"):
        if tomllib is None:
            raise RuntimeError("TOML support requires Python 3.11+")
        cfg = tomllib.loads(raw.decode("utf-8"))
    else:
        cfg = json.loads(raw.decode("utf-8"))
    return cfg


def case_to_params(cfg: dict) -> BSPParams:
    """Build BSPParams from a case config dict."""
    case = dict(cfg.get("case", {}))
    mat = dict(cfg.get("material", {}))
    run = dict(cfg.get("run", {}))

    preset = mat.pop("preset", None)
    if preset is not None:
        if preset not in PRESETS:
            raise KeyError(f"unknown preset {preset!r}; "
                           f"available: {sorted(PRESETS)}")
        props = {k: v for k, v in PRESETS[preset].items() if k != "note"}
        props.update(mat)          # explicit values override the preset
        mat = props

    required_mat = ("rho", "L", "k_grown", "cp_grown")
    missing = [k for k in required_mat if k not in mat]
    if missing:
        raise KeyError(f"material section missing {missing}; give a "
                       f"preset or the explicit properties")

    p = BSPParams(
        mode=case.get("mode", "freezing"),
        T_m=float(case.get("T_m", 0.0)),
        T_s=float(case["T_s"]),
        T_0=float(case.get("T_0", case.get("T_m", 0.0))),
        length=float(case.get("length", 0.05)),
        dx=float(case.get("dx", 0.001)),
        t_end=float(case.get("t_end", 2000.0)),
        temp_unit=case.get("temp_unit", "C"),
        T_offset=0.0 if case.get("temp_unit", "C") == "K" else 273.15,
        rho=float(mat["rho"]),
        L=float(mat["L"]),
        k_grown=float(mat["k_grown"]),
        cp_grown=float(mat["cp_grown"]),
        k_bulk=float(mat.get("k_bulk", mat["k_grown"])),
        cp_bulk=float(mat.get("cp_bulk", mat["cp_grown"])),
        event_mode=run.get("event_mode", "integral"),
        substep_safety=float(run.get("substep_safety", 0.45)),
        max_events=int(run.get("max_events", 20000)),
    )
    if p.temp_unit == "K" and (p.T_m < 1.0):
        raise ValueError("temp_unit = 'K' but T_m < 1 K -- did you mean "
                         "temp_unit = 'C' or Kelvin temperatures?")
    return p


def load_user_data(path: str):
    """Load measured interface positions: CSV with columns t_s, s_m
    (any column order; header optional; 'time'/'t' and 's'/'front'
    aliases accepted).  Returns (t, s) arrays."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    rows = []
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = None
        for i, row in enumerate(reader):
            if not row:
                continue
            if header is None and any(
                    c.strip().lower() in ("t_s", "t", "time", "time_s",
                                          "s_m", "s", "front", "s_m_m",
                                          "position")
                    for c in row):
                header = [c.strip().lower() for c in row]
                continue
            try:
                rows.append([float(c) for c in row[:2]])
            except ValueError:
                continue
    if not rows:
        raise ValueError(f"no numeric rows found in {path}")
    data = list(zip(*rows))
    t = list(data[0])
    s = list(data[1])
    if header:
        low = [h for h in header]
        # order by header names if available
        t_idx = next((i for i, h in enumerate(low)
                      if h in ("t_s", "t", "time", "time_s")), None)
        s_idx = next((i for i, h in enumerate(low)
                      if h in ("s_m", "s", "front", "position", "s_m_m")),
                     None)
        if t_idx is not None and s_idx is not None:
            with open(path, newline="") as fh:
                rows2 = []
                for row in csv.reader(fh):
                    try:
                        rows2.append([float(row[t_idx]), float(row[s_idx])])
                    except (ValueError, IndexError):
                        continue
            t = [r[0] for r in rows2]
            s = [r[1] for r in rows2]
    return np.asarray(t, dtype=float), np.asarray(s, dtype=float)
