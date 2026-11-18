"""Figures for the BSP validation report.

All figures use the Agg backend with fonts registered per the
environment rules (Noto Sans SC for CJK safety alongside DejaVu).
Legends sit outside the axes; constrained_layout everywhere.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.font_manager as fm
for _f in ("/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
    if os.path.exists(_f):
        fm.fontManager.addfont(_f)

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["Noto Sans SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

__all__ = ["plot_validation", "plot_profiles", "plot_clock"]


def plot_validation(out_path, res, neu, enth=None, conv=None,
                    user_data=None, title="BSP validation"):
    """The main figure: front position vs time against all references."""
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4),
                             constrained_layout=True)
    t_ev = np.asarray(res.t_events)
    s_ev = np.asarray(res.s_events)

    ax = axes[0]
    tt = np.linspace(1e-6, max(t_ev[-1] * 1.05, 1.0), 500)
    ax.plot(tt, neu.front(tt), "-", color="#888", lw=1.5,
            label="Neumann (exact)")
    if enth is not None:
        ax.plot(enth.t_grid, enth.s_grid, "--", color="#c0662a", lw=1.5,
                label="enthalpy benchmark")
    ax.plot(t_ev, s_ev, "o", ms=4.5, color="#1a5fb4",
            label="BSP events", zorder=5)
    if user_data is not None:
        t_u, s_u = user_data
        ax.plot(t_u, s_u, "x", ms=6, mew=1.6, color="#b30000",
                label="your data", zorder=6)
    ax.set_xlabel("time t  [s]")
    ax.set_ylabel("front position s  [m]")
    ax.set_title("front trajectory")
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.0), fontsize=8,
              framealpha=0.9)
    ax.grid(alpha=0.3)

    ax = axes[1]
    s_ref = neu.front(t_ev)
    rel = (s_ev - s_ref) / np.maximum(s_ref, 1e-300)
    ax.plot(t_ev, 100.0 * rel, "o-", ms=3.5, lw=1.0, color="#1a5fb4",
            label="BSP vs Neumann")
    if enth is not None:
        s_en = enth.front_at(t_ev)
        ok = s_en > 0
        ax.plot(t_ev[ok], 100.0 * (s_ev[ok] - s_en[ok]) / s_en[ok], "s--",
                ms=3.0, lw=1.0, color="#c0662a",
                label="BSP vs enthalpy")
    ax.axhline(0.0, color="#888", lw=1.0)
    ax.axhspan(-5, 5, color="green", alpha=0.08,
               label="±5% band")
    ax.set_xlabel("time t  [s]")
    ax.set_ylabel("relative deviation  [%]")
    ax.set_title("deviation from exact solution")
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.0), fontsize=8,
              framealpha=0.9)
    ax.grid(alpha=0.3)

    if conv is not None and len(conv) >= 2:
        # inset: convergence
        ins = ax.inset_axes([0.58, 0.14, 0.38, 0.34])
        dxs = np.array([c["dx"] for c in conv])
        errs = np.array([c["err"] for c in conv])
        ins.loglog(dxs * 1e3, errs, "o-", color="#1a5fb4", ms=4)
        ref = errs[0] * (dxs / dxs[0])
        ins.loglog(dxs * 1e3, ref, ":", color="#888",
                   label="1st order")
        ins.set_xlabel("dx [mm]", fontsize=7)
        ins.set_ylabel("mean err", fontsize=7)
        ins.tick_params(labelsize=7)
        ins.legend(fontsize=7)
        ins.set_title("grid convergence", fontsize=7)

    fig.suptitle(title, fontsize=11)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_profiles(out_path, res, neu, dx_for_plot=None, title="BSP field"):
    """Final temperature profile vs the exact Neumann profile, plus the
    trace/coupling layers (the UC state) beneath."""
    p = res.params
    N = len(res.a_final) - 1
    x = np.arange(N + 1) * p.dx
    t_end = res.t_events[-1] if res.t_events else p.t_end
    s_neu = float(neu.front(t_end))

    fig, axes = plt.subplots(2, 1, figsize=(7.5, 6.4),
                             sharex=True, constrained_layout=True,
                             height_ratios=[2.2, 1.0])
    ax = axes[0]
    xf = np.linspace(0, p.length, 800)
    ax.plot(xf, neu.profile(xf, t_end), "-", color="#888", lw=1.5,
            label=f"Neumann at t={t_end:.0f} s")
    ax.plot(x, res.a_final, "o", ms=2.6, color="#1a5fb4",
            label="BSP value layer a")
    ax.axvline(s_neu, color="#888", ls=":", lw=1.2,
               label=f"Neumann front {s_neu*1e3:.1f} mm")
    ax.axvline(res.s_events[-1], color="#1a5fb4", ls="--", lw=1.2,
               label=f"BSP front {res.s_events[-1]*1e3:.1f} mm")
    ax.axhline(p.T_m, color="k", lw=0.7, alpha=0.5)
    ax.set_ylabel("temperature  [C]")
    ax.set_title(title)
    ax.legend(fontsize=8, loc="center right")
    ax.grid(alpha=0.3)

    ax = axes[1]
    ax.step(x, res.c_final, where="mid", color="#26a269", lw=1.6,
            label="trace layer c (boundary marker)")
    ax.step(x, res.d_final, where="mid", color="#c0662a", lw=1.4,
            linestyle="--", label="coupling layer d (visited record)")
    ax.set_xlabel("x  [m]")
    ax.set_ylabel("layer value")
    ax.set_ylim(-0.15, 1.35)
    ax.legend(fontsize=8, loc="center right")
    ax.grid(alpha=0.3)

    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_clock(out_path, res, title="Trace-driven clock"):
    """The BSP clock: event intervals dt_n (non-uniform by construction)
    and the SP-manifold trajectory."""
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2),
                             constrained_layout=True)
    t_ev = np.asarray(res.t_events)
    dt_ev = np.asarray(res.dt_events)
    n_ev = np.arange(1, len(t_ev) + 1)

    ax = axes[0]
    ax.plot(n_ev, dt_ev, "o-", ms=4, color="#1a5fb4")
    ax.set_xlabel("event index n")
    ax.set_ylabel("clock tick dt_n  [s]")
    ax.set_title("time between trace events")
    ax.grid(alpha=0.3)

    ax = axes[1]
    X = np.array(res.X_events)
    ax.plot(X[:, 0], X[:, 1], "-", lw=1.2, color="#1a5fb4",
            label="1DB-SP: (X, Y) temperature / phase complexity")
    ax2 = ax.twinx()
    ax2.plot(X[:, 0], X[:, 2], "--", lw=1.2, color="#c0662a",
             label="2DB-SP: (X, U) energy")
    ax2.set_ylabel("U (normalized energy)", color="#c0662a")
    ax.set_xlabel("X (mean value-layer temperature)")
    ax.set_ylabel("Y (phase complexity)")
    ax.set_title("SP-manifold trajectory (paper Def. 6.1, adopted)")
    l1, lab1 = ax.get_legend_handles_labels()
    l2, lab2 = ax2.get_legend_handles_labels()
    ax.legend(l1 + l2, lab1 + lab2, fontsize=8, loc="upper left",
              bbox_to_anchor=(0.0, 1.0))
    ax.grid(alpha=0.3)

    fig.suptitle(title, fontsize=11)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path
