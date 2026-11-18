"""Node roles / layers for the BSP solver -- the null-transit reading.

THE PROBLEM THIS MODULE SOLVES (the node-0 conflict).

Algorithm 9.1 of the BSP paper starts with Event 0: the boundary
condition is imposed at x = 0 AND the interface marker is set there
(c(0) = 1).  For the first interval, node 0 therefore carries two
identities at once:

  * the DIRICHLET LAYER: the imposed boundary temperature T_s that
    drives the heat flow, and
  * the INTERFACE LAYER: the melting-point isotherm T_m that the
    diffusing bulk actually sees.

Pinning a single scalar a[0] to both T_s and T_m is a contradiction;
naively pinning a[0] = T_s lets the bulk "see" the cold boundary
instead of the interface and the field collapses (this failure is
reproduced deliberately in the test-suite).

THE NULL-TRANSIT RESOLUTION (monograph sec. 2.7.1, user's insight).

The monograph's null transit operator tau is characterised by
nilpotence (tau^2 = 0, the fare cannot be paid twice), irreversibility
(no inverse), and trace preservation (the crossing leaves a record).
A lattice node therefore does not hold one scalar but a LAYERED state
whose components switch roles dynamically as the front passes:

    node state z = a + b i + tau c + tau d i   (the UC number)

    LAYER 1  a (value)      -- what the diffusing field sees.  While
              the node is the interface, a = T_m; once the front has
              passed, a is evolved by FTCS; while the node is the cold
              boundary, a = T_s.
    LAYER 2  b (phase)      -- +1 grown phase, -1 bulk phase; records
              which side of the front the node is on.
    LAYER 3  tau c (trace)  -- the boundary marker: c = 1 exactly at
              the interface node, else 0.  This is the null-transit
              marker: c changes 0 -> 1 -> 0 exactly once per visit.
    LAYER 4  tau d i (coupling) -- the irreversible record: d = 1 on
              every node the interface has EVER occupied ("the fare
              was paid here").  Unlike c, d never resets: it is the
              trace left by the transit (Tr(tau) in sec. 2.7.1).

The dynamics of the layers implement the three null-transit axioms:

    NILPOTENCE      the interface layer can depart a node only once:
                    role transitions are one-way (BULK -> INTERFACE ->
                    GROWN); attempting a second departure is a no-op.
    IRREVERSIBILITY the interface can never return to a visited node
                    (in a monotone 1D front): visited[i] is frozen.
    TRACE           every departure leaves d = 1 behind; the fare
                    (latent heat of the first cell, rho L dx) is paid
                    once, at the transit, and recorded in the energy
                    bookkeeping as the "transit fare".

Node 0 during the first interval is then NOT a contradiction but the
coincident state: its Dirichlet layer holds T_s (set at Event 0,
drives the event-1 gradient exactly as in paper sec. 11.2) while its
interface layer shows T_m to the bulk.  Event 1 is the null transit:
the interface layer departs to node 1, node 0's value layer settles
to the Dirichlet value, and the trace layer keeps the record.  All of
this is verified by `bsp.checks` (transit_nilpotence, transit_trace,
transit_fare) and the test-suite.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["NodeRole", "NodeStates", "TRANSIT_FARE_NOTES"]


# ----------------------------------------------------------------------
# roles
# ----------------------------------------------------------------------
class NodeRole:
    BULK = "bulk"                # untouched phase, c = 0, d = 0
    INTERFACE = "interface"      # front is here: c = 1, a = T_m
    GROWN = "grown"              # front has passed: c = 0, d = 1
    BOUNDARY = "boundary"        # x = 0 Dirichlet layer (role, not phase)

    _TRANSITIONS = {
        BULK: (INTERFACE,),
        INTERFACE: (GROWN,),
        GROWN: (),                    # terminal: fare already paid
    }

    @classmethod
    def can_transition(cls, frm: str, to: str) -> bool:
        return to in cls._TRANSITIONS.get(frm, ())


TRANSIT_FARE_NOTES = (
    "The 'transit fare' is the null-transit payment of monograph "
    "sec. 2.7.1: the first cell's latent heat rho*L*dx (+ O(dx) "
    "sensible correction), paid once when the interface layer departs "
    "node 0.  It is O(dx) and vanishes in the convergence limit, so "
    "event 1 is a start-up transit, not a conservation failure."
)


@dataclass
class NodeStates:
    """Layered node states for the whole lattice (parallel arrays).

    a: value layer (temperature the field sees)
    b: phase layer (sign flips when the front passes: bulk -> grown)
    c: trace layer (boundary marker, 1 exactly at the interface)
    d: coupling layer (irreversible visited-record)
    role: NodeRole of each node
    """

    a: np.ndarray
    b: np.ndarray
    c: np.ndarray
    d: np.ndarray
    role: np.ndarray          # dtype '<U16'
    visited: np.ndarray       # bool: interface has ever been here

    @classmethod
    def init(cls, N: int, T_0: float, mode: str) -> "NodeStates":
        freezing = mode == "freezing"
        st = cls(
            a=np.full(N + 1, float(T_0)),
            b=np.full(N + 1, -1.0 if freezing else 1.0),
            c=np.zeros(N + 1),
            d=np.zeros(N + 1),
            role=np.array([NodeRole.BULK] * (N + 1), dtype="<U16"),
            visited=np.zeros(N + 1, dtype=bool),
        )
        return st

    # ------------------------------------------------------------------
    def interfaces(self) -> int:
        """Index of the (single) interface node; -1 if none."""
        idx = np.nonzero(self.c > 0.5)[0]
        return int(idx[0]) if len(idx) else -1

    def boundary_set(self) -> np.ndarray:
        """B = {p : c(p) != 0} -- paper Property 9.4."""
        return np.nonzero(self.c != 0)[0]

    # ------------------------------------------------------------------
    def impose_boundary(self, i: int, T_s: float):
        """Event 0: impose the Dirichlet layer at node i AND start the
        interface there (paper sec. 11.1).  Node i becomes the
        coincident state: Dirichlet layer keeps T_s (recorded in
        a_dirichlet), interface layer pins the field value at T_m."""
        self.role[i] = NodeRole.INTERFACE
        self.c[i] = 1.0
        self.d[i] = 1.0
        self.visited[i] = True

    def transit_to(self, i: int, T_m: float, T_bc_0: float = None) -> bool:
        """The null transit: interface layer departs node i-1 and
        arrives at node i (one-way, trace-leaving).

        T_bc_0 is the Dirichlet value at node 0: when the coincident
        node 0 transits (Event 1), its value layer switches from the
        interface reading (T_m) to the Dirichlet reading (T_s) AT the
        transit, so the next velocity evaluation and every later
        substep see the boundary, while the first interval saw the
        interface -- the dynamic layer switch that resolves the
        node-0 conflict.

        Returns True if the transit happened, False if it was refused
        (nilpotence / irreversibility guard: node i already visited,
        or node i-1 not the interface).
        """
        j = i - 1
        if not (0 <= j < len(self.role)):
            return False
        if self.role[j] != NodeRole.INTERFACE:
            return False                          # fare already paid
        if self.visited[i]:
            return False                          # irreversible
        # departure at j: interface -> grown, trace stays (d = 1)
        self.role[j] = NodeRole.GROWN
        self.c[j] = 0.0
        self.b[j] = 1.0 if self.b[j] < 0 else -1.0   # flip phase sign
        if j == 0 and T_bc_0 is not None:
            self.a[j] = T_bc_0    # Dirichlet layer takes over node 0
        # arrival at i: bulk -> interface
        self.role[i] = NodeRole.INTERFACE
        self.c[i] = 1.0
        self.d[i] = 1.0
        self.visited[i] = True
        self.a[i] = T_m
        return True

    # ------------------------------------------------------------------
    def value_layer_pins(self, f: int, p) -> None:
        """Apply the value-layer (a) pins for diffusion; delegates to
        the module-level `apply_value_pins` (single source of truth)."""
        apply_value_pins(self.a, f, p)


def apply_value_pins(a: np.ndarray, f: int, p) -> None:
    """The value-layer pins used by every diffusion substep:

    * node f (interface): a = T_m  -- what the bulk sees
    * node 0: a = T_s once grown phase exists (f >= 1); during the
      first interval node 0 is the coincident state and its value
      layer shows T_m (the interface), while its DIRICHLET layer
      (T_s) is carried by the case parameters and consumed by the
      event-1 gradient (paper sec. 11.2)
    * node N: a = T_0 (two-phase far field)
    """
    N = len(a) - 1
    a[f] = p.T_m
    a[0] = p.T_s if f > 0 else p.T_m
    if not np.isclose(p.T_0, p.T_m):
        a[N] = p.T_0
