"""bsp -- a validation workbench for the Bitriada Stefan Projection.

Run a Stefan moving-boundary problem (freezing / melting) with the
BSP algorithm (trace-driven, event-based time) on YOUR OWN data and
check it against the exact Neumann solution, an enthalpy-method
benchmark, and your measured interface positions.

    from bsp.solver import BSPParams, run_bsp
    p = BSPParams(dx=5e-4, t_end=3000.0, ...)
    result = run_bsp(p)

CLI:  python -m bsp.cli run cases/water_ice_monograph.toml --out out/
"""

__version__ = "1.0.0"
