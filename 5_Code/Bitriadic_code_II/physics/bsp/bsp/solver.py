"""The BSP solver: Algorithm 9.1 (BSP Evolution with Trace-Driven Time),
implemented on the layered node states of `bsp.nodes` (null-transit
reading -- see that module's docstring for how the node-0 conflict is
resolved by dynamic layer switching).

    state per node: z_i = a_i + b_i i + tau c_i + tau d_i i
        a_i  value layer     temperature (field)
        b_i  phase layer     flips sign when the front passes
        c_i  trace layer     boundary marker: 1 exactly at the interface
        d_i  coupling layer  irreversible transit record (visited nodes)

    MAIN LOOP (paper sec. 9.1), integral mode (default):
      STEP 1  evolve the value layer by explicit FTCS substeps,
              accumulating the integrated front advance
              integral v dt (per-substep trapezoid)
      STEP 2  v_n at the interface node from the Stefan condition,
              re-evaluated on the evolving field after every substep
      STEP 3  the event fires when the advance reaches dx -- the
              crossing condition; the last substep is partial so the
              crossing lands exactly (residual reported per event)
      STEP 4  time has already advanced to the event
      STEP 5  fire the transit: c(f) -> 0, c(f+1) -> 1 (nilpotent,
              irreversible, trace-leaving -- see nodes.transit_to)
      STEP 6  boundary set B = {p : c(p) != 0} is exactly the front
      STEP 7  record the event (t_n, p_n, dtau_n) -- the clock tick
      STEP 8  update the entropy layer (2DB-SP: q0, q2 >= 0)

    EVENT RULES.  "integral" (default) is the only self-consistent
    realization of trace-driven time: right after an event the
    just-released interior node still sits at T_m, so the
    start-of-interval velocity is ZERO and the paper's explicit rule
    dt = dx / v(0) stalls after two events (the paper's own appendix
    tables were built from hand-fed Neumann gradients, not from
    Algorithm 9.1's STEP 1 field -- quantified in bsp.monograph).
    "explicit" is kept verbatim for reproduction of that behaviour.

Energy / entropy bookkeeping (paper secs. 13-14), per unit area.
The LIQUID holds the latent heat (solid = reference state), so
freezing RELEASES rho L dx per cell through the boundary:

  E(t)  = sum_{visited i} rho cp_grown (a_i - T_m) dx
          + sum_{liquid i} rho cp_bulk (a_i - T_m) dx
          + rho L dx * (N - f)          [latent of liquid cells]
  Q_out = integral k_g (a_1 - a_0)/dx dt   (heat leaving at x = 0)
  fare_n = E_n - E_{n-1} + (Q_n - Q_{n-1})     [1st law: dE = -Q_out]
        n = 1 : the null-transit fare, ~ -(rho L dx + chill of the
                 boundary cell); a start-up payment, O(dx), not a
                 conservation failure
        n >= 2: the conservation drift (must vanish with dx)
  dS    = sum over substeps k (dT/dx)^2 / T_abs^2 dx dt  >= 0

The 2DB-SP entropy layer (paper sec. 5.4): q0 = normalized energy,
q2 = cumulative entropy production, tau1 = last event's production,
tau2 = event count (history memory).  The paper defines roles, not
formulas; these readings are marked ADOPTED in the report.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .nodes import NodeRole, NodeStates, apply_value_pins

__all__ = ["BSPParams", "BSPResult", "run_bsp"]


@dataclass
class BSPParams:
    mode: str = "freezing"        # "freezing" | "melting"
    T_m: float = 0.0              # melting point [K or C, consistent]
    T_s: float = -10.0            # boundary temperature at x = 0
    T_0: float = 0.0              # initial temperature (bulk phase)
    length: float = 0.05          # domain length [m]
    dx: float = 0.001             # lattice spacing [m]
    t_end: float = 2000.0         # stop time [s]
    rho: float = 1000.0           # density [kg/m^3]
    L: float = 334000.0           # latent heat [J/kg]
    k_grown: float = 2.2          # conductivity of the growing phase
    cp_grown: float = 4186.0      # specific heat of the growing phase
    k_bulk: float = 2.2           # conductivity of the bulk phase
    cp_bulk: float = 4186.0       # specific heat of the bulk phase
    T_offset: float = 273.15      # Celsius -> Kelvin offset for entropy
    temp_unit: str = "C"          # "C" | "K" (offset used only in dS)
    event_mode: str = "integral"  # "integral" (crossing cond.) | "explicit"
    substep_safety: float = 0.45  # fraction of FTCS stability limit
    max_events: int = 20000

    # derived ----------------------------------------------------------
    def alpha_grown(self) -> float:
        return self.k_grown / (self.rho * self.cp_grown)

    def alpha_bulk(self) -> float:
        return self.k_bulk / (self.rho * self.cp_bulk)

    def one_phase(self) -> bool:
        return abs(self.T_0 - self.T_m) < 1e-12

    def Tabs(self, T):
        """Absolute temperature for the entropy formula."""
        off = self.T_offset if self.temp_unit == "C" else 0.0
        return np.maximum(T + off, 1.0)


@dataclass
class BSPResult:
    params: BSPParams
    t_events: list = field(default_factory=list)     # event times
    p_events: list = field(default_factory=list)     # node index moved TO
    dt_events: list = field(default_factory=list)    # interval lengths
    dtau_events: list = field(default_factory=list)  # trace increments (+1)
    transit_types: list = field(default_factory=list)  # "null" | "advance"
    v_events: list = field(default_factory=list)     # effective velocity
    grad_events: list = field(default_factory=list)  # implied mean gradient
    s_events: list = field(default_factory=list)     # front position (n*dx)
    E_events: list = field(default_factory=list)     # total energy at event
    fare_events: list = field(default_factory=list)  # transit fare / drift
    dS_events: list = field(default_factory=list)    # entropy per interval
    S_events: list = field(default_factory=list)     # cumulative entropy
    Q_events: list = field(default_factory=list)     # cumulative heat out
    X_events: list = field(default_factory=list)     # SP-manifold coords
    cross_residuals: list = field(default_factory=list)  # advance - dx
    a_final: np.ndarray = None                       # final value layer
    c_final: np.ndarray = None                       # final trace layer
    d_final: np.ndarray = None                       # final coupling layer
    role_final: np.ndarray = None                    # final node roles
    termination: str = ""
    n_substeps: int = 0

    # ------------------------------------------------------------------
    EVENT_COLUMNS = ("n", "t_s", "p", "dt_s", "dtau", "v_n_m_s", "grad_K_m",
                     "s_m", "E_J_m2", "fare_J_m2", "dS_J_m2K", "S_J_m2K",
                     "Q_out_J_m2")

    def event_table(self) -> np.ndarray:
        """Numeric event log; columns as in EVENT_COLUMNS (transit_types
        is a separate string list aligned with the rows)."""
        return np.column_stack([
            np.arange(1, len(self.t_events) + 1),
            self.t_events, self.p_events, self.dt_events,
            self.dtau_events, self.v_events, self.grad_events,
            self.s_events, self.E_events, self.fare_events,
            self.dS_events, self.S_events, self.Q_events,
        ])


# ----------------------------------------------------------------------
# field primitives
# ----------------------------------------------------------------------
def _velocity(a, f, p):
    """STEP 2: interface velocity from the Stefan condition.

    freezing:  v = (k_g g_in  - k_b g_out) / (rho L)
    melting:   v = (-k_g g_in + k_b g_out) / (rho L)

    f = 0 is the coincident state: the paper's sec. 11.2 start-up rule
    reads the DIRICHLET layer (T_s) against the initial profile, not
    the evolved field (whose value layer shows T_m at node 0).
    """
    freezing = p.mode == "freezing"
    if f == 0:
        # the initial-profile gradient across the first cell, SIGNED as
        # the field gradient (a[1] - a[0]) / dx would be -- positive for
        # freezing, negative for melting; the velocity formulas below
        # then give v > 0 for both modes
        g_in = (p.T_0 - p.T_s) / p.dx
        g_out = 0.0
    else:
        g_in = (a[f] - a[f - 1]) / p.dx
        g_out = (a[f + 1] - a[f]) / p.dx if f + 1 <= len(a) - 1 else 0.0
    if freezing:
        v = (p.k_grown * g_in - p.k_bulk * g_out) / (p.rho * p.L)
    else:
        v = (-p.k_grown * g_in + p.k_bulk * g_out) / (p.rho * p.L)
    return v, g_in


def _substep(a, f, p, dt, stats=None):
    """One explicit FTCS update (stable for dt <= dt_stab), with pins,
    flux and entropy accumulation.  Mutates `a` in place."""
    N = len(a) - 1
    alpha_g, alpha_b = p.alpha_grown(), p.alpha_bulk()
    k_g, k_b = p.k_grown, p.k_bulk
    new = a.copy()
    if f >= 2:                                       # grown-phase interior
        i0, i1 = 1, f                                # nodes i0..i1-1
        lap = (a[i0 - 1:i1 - 1] - 2 * a[i0:i1] + a[i0 + 1:i1 + 1]) / p.dx ** 2
        new[i0:i1] = a[i0:i1] + alpha_g * dt * lap
        if stats is not None:
            g = (a[i0 + 1:i1 + 1] - a[i0 - 1:i1 - 1]) / (2 * p.dx)
            stats["S"] += float(np.sum(
                k_g * g ** 2 / p.Tabs(a[i0:i1]) ** 2)) * dt * p.dx
    if f + 2 <= N:                                   # bulk-phase interior
        i0, i1 = f + 1, N
        if i1 > i0:
            lap = (a[i0 - 1:i1 - 1] - 2 * a[i0:i1] + a[i0 + 1:i1 + 1]) / p.dx ** 2
            new[i0:i1] = a[i0:i1] + alpha_b * dt * lap
            if stats is not None:
                g = (a[i0 + 1:i1 + 1] - a[i0 - 1:i1 - 1]) / (2 * p.dx)
                stats["S"] += float(np.sum(
                    k_b * g ** 2 / p.Tabs(a[i0:i1]) ** 2)) * dt * p.dx
    if stats is not None:
        q = k_g * (a[1] - a[0]) / p.dx               # flux out at x = 0
        stats["Q"] += q * dt
        stats["n_sub"] += 1
    apply_value_pins(new, f, p)
    a[:] = new


def _diffuse(a, f, p, dt_total, dt_stab, stats=None):
    """STEP 1 as a plain loop of stability-limited substeps (used by the
    explicit event mode and terminal intervals; no crossing logic)."""
    if dt_total <= 0:
        return
    n_sub = max(1, int(np.ceil(dt_total / dt_stab)))
    dt = dt_total / n_sub
    for _ in range(n_sub):
        _substep(a, f, p, dt, stats)


def _sweep_interval(a, f, p, dt_stab, stats, t_budget):
    """Single-pass crossing sweep (integral event mode).

    Evolves the field substep by substep (STEP 1), re-evaluating the
    Stefan velocity on the evolving field (STEP 2) and accumulating
    the integrated front advance with a per-substep trapezoid.  When
    the remaining advance fits within one stability substep, a PARTIAL
    substep lands exactly on the crossing (STEP 3); the residual is
    returned for the diagnostics.  Stops early at the time budget.

    Returns (elapsed, advance, crossed).
    """
    elapsed = 0.0
    advance = 0.0
    v_prev = max(_velocity(a, f, p)[0], 0.0)
    while elapsed < t_budget - 1e-12:
        rem_d = p.dx - advance
        if rem_d <= 1e-9 * p.dx:
            return elapsed, advance, True
        rem_t = t_budget - elapsed
        if v_prev > 1e-30 and rem_d / v_prev <= dt_stab:
            dt = min(rem_d / v_prev, rem_t)      # land on the crossing
        else:
            dt = min(dt_stab, rem_t)
        _substep(a, f, p, dt, stats)
        elapsed += dt
        v_now = max(_velocity(a, f, p)[0], 0.0)
        advance += 0.5 * (v_prev + v_now) * dt
        v_prev = v_now
    return elapsed, advance, advance >= p.dx - 1e-9 * p.dx


# ----------------------------------------------------------------------
# the solver
# ----------------------------------------------------------------------
def run_bsp(p: BSPParams) -> BSPResult:
    """Execute Algorithm 9.1 with trace-driven time."""
    freezing = p.mode == "freezing"
    if freezing and not (p.T_s < p.T_m):
        raise ValueError("freezing requires T_s < T_m")
    if not freezing and not (p.T_s > p.T_m):
        raise ValueError("melting requires T_s > p.T_m")

    N = int(round(p.length / p.dx))
    st = NodeStates.init(N, p.T_0, p.mode)

    # Event 0 (paper sec. 11.1): impose the boundary condition; node 0
    # enters the coincident state (Dirichlet layer T_s + interface layer)
    st.impose_boundary(0, p.T_s)
    # NOTE: the value layer at node 0 stays at T_m during the coincident
    # first interval (what the field sees); the Dirichlet value T_s lives
    # in the case parameter and is consumed by the event-1 gradient
    # (paper sec. 11.2) and by the transit layer switch below.
    f = 0
    t = 0.0
    rhoL = p.rho * p.L
    dt_stab = p.substep_safety * p.dx ** 2 / (2.0 * max(p.alpha_grown(),
                                                        p.alpha_bulk()))
    res = BSPResult(params=p)
    stats = {"Q": 0.0, "S": 0.0, "n_sub": 0}

    def total_energy(states: NodeStates, f_idx: int) -> float:
        """Stored energy (solid = reference state): sensible relative
        to T_m (visited nodes use the grown-phase cp) + LATENT OF THE
        LIQUID CELLS.  The front position claim is s = f_idx * dx, so
        freezing has f_idx frozen cells and N - f_idx liquid cells,
        while melting has f_idx melted (liquid) cells and N - f_idx
        solid -- the liquid is the VISITED side when melting.  Phase
        change therefore moves rho L dx per event through the boundary
        (1st law: dE = -Q_out)."""
        vis = states.visited
        cp = np.where(vis, p.cp_grown, p.cp_bulk)
        sens = float(np.sum(p.rho * cp * (states.a - p.T_m) * vis)) * p.dx
        liquid_cells = (N - f_idx) if freezing else f_idx
        return sens + rhoL * p.dx * liquid_cells

    E_prev = total_energy(st, 0)     # energy just after Event 0
    Q_prev = 0.0

    while True:
        if f + 1 > N - 1:
            res.termination = "front reached domain end"
            break

        v0, _ = _velocity(st.a, f, p)
        if p.event_mode == "integral":
            # a zero START velocity is legitimate here: right after an
            # event the just-released interior node still sits at T_m;
            # the field builds the gradient during the interval
            elapsed, advance, crossed = _sweep_interval(
                st.a, f, p, dt_stab, stats, p.t_end - t)
            t += elapsed
            if not crossed:
                res.termination = "t_end reached"
                break
            # residual of the FIRED event only (a terminal unfinished
            # sweep is not an event and must not pollute the log)
            res.cross_residuals.append(advance - p.dx)
            dt_event = elapsed
        else:
            # the paper's printed rule, kept verbatim: dt = dx / v(0)
            if v0 <= 0:
                res.termination = (f"non-positive interface velocity "
                                   f"at t={t:.1f}s")
                break
            dt_event = p.dx / v0
            if t + dt_event > p.t_end:
                _diffuse(st.a, f, p, p.t_end - t, dt_stab, stats)
                t = p.t_end
                res.termination = "t_end reached"
                break
            _diffuse(st.a, f, p, dt_event, dt_stab, stats)
            t += dt_event
            res.cross_residuals.append(0.0)

        # STEPs 5-6: fire the transit (nilpotent, irreversible,
        # trace-leaving); boundary set becomes exactly {f+1}
        if not st.transit_to(f + 1, p.T_m, T_bc_0=p.T_s):
            res.termination = f"transit refused at node {f + 1} (guard)"
            break
        f += 1

        # STEP 7: record the event
        E = total_energy(st, f)
        fare = E - E_prev + (stats["Q"] - Q_prev)
        E_prev, Q_prev = E, stats["Q"]
        prev_S = res.S_events[-1] if res.S_events else 0.0
        res.t_events.append(t)
        res.p_events.append(f)
        res.dt_events.append(dt_event)
        res.dtau_events.append(1)
        res.transit_types.append("null" if f == 1 else "advance")
        res.v_events.append(p.dx / dt_event)             # effective v
        res.grad_events.append(rhoL * (p.dx / dt_event) / p.k_grown)
        res.s_events.append(f * p.dx)
        res.E_events.append(E)
        res.fare_events.append(fare)
        res.dS_events.append(stats["S"] - prev_S)
        res.S_events.append(stats["S"])
        res.Q_events.append(stats["Q"])

        # STEP 8: 2DB-SP layer + SP-manifold coordinates (ADOPTED readings)
        X = float(np.mean(st.a[:f + 1]))
        Y = float(np.sqrt(np.mean(st.b ** 2 + st.c ** 2 + st.d ** 2)))
        U = E / (rhoL * p.length)          # normalized energy scalar
        V = float(np.hypot(res.S_events[-1], res.dS_events[-1] * 1e6))
        res.X_events.append((X, Y, U, V))

        if len(res.t_events) >= p.max_events:
            res.termination = "max_events reached"
            break

    res.a_final = st.a
    res.c_final = st.c
    res.d_final = st.d
    res.role_final = st.role
    res.n_substeps = stats["n_sub"]
    return res
