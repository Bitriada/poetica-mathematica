#!/usr/bin/env python3
"""make_trial_figures.py -- the ANALYSIS.md figures, from the trial
logs only (runs/*/ticks.csv + measurements.json).  English labels;
matplotlib per the charts skill (constrained_layout, no top/right
spines, legends outside, low-saturation palette, conclusion titles).
Output: results/figures/fig1..fig4 PNGs @200dpi."""
import csv, json, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

ROOT = Path("/home/z/my-project/download/piclock-browser/results")
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
PI = math.pi

plt.rcParams.update({
    "font.sans-serif": ["DejaVu Sans"], "axes.unicode_minus": False,
    "figure.facecolor": "#FFFFFF", "axes.facecolor": "#FFFFFF",
    "axes.edgecolor": "#E5E7EB", "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": False, "xtick.major.size": 0, "ytick.major.size": 0,
    "xtick.labelsize": 9, "ytick.labelsize": 9,
    "axes.labelsize": 10, "axes.titlesize": 13,
    "axes.titleweight": "bold", "axes.titlepad": 12,
    "legend.frameon": False, "legend.fontsize": 9,
    "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight",
    "savefig.facecolor": "#FFFFFF", "savefig.pad_inches": 0.3,
})
# colorblind-safe palette (skill)
C = {"B": "#0077BB", "i": "#33BBEE", "f": "#EE7733", "F": "#CC3311",
     "law": "#111827", "warn": "#CC3311", "ok": "#009988",
     "ctrl": "#EE3377", "gray": "#9CA3AF"}
G300, G700 = "#D1D5DB", "#374151"

def load(run):
    with open(ROOT / "runs" / run / "ticks.csv", newline="") as f:
        rd = csv.reader(f)
        head = next(rd)
        rows = list(rd)
    out = {}
    for j, name in enumerate(head):
        try: out[name] = [float(r[j]) for r in rows]
        except ValueError: out[name] = [r[j] for r in rows]
    out["_B"] = [int(v) for v in out["B"]]
    return out

M = json.load(open(ROOT / "measurements.json"))
rc = load("R-C")
ctrl = load("CTRL-R4")

# ---------------------------------------------------------------- fig 1
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.2),
                             constrained_layout=True)
step = 40
sel = slice(0, len(rc["B"]), step)
for key, lbl in [("gap_B", "Gap_B (ordinal)"), ("gap_i", "Gap_i (Leibniz)"),
                 ("gap_f", "Gap_f (apeirogon)"), ("gap_F", "Gap_F (Farey law)")]:
    a1.loglog(rc["B"][sel], rc[key][sel], lw=1.6, color=C[key[4]],
              label=lbl)
a1.loglog(rc["B"][sel], [3 * PI / b for b in rc["B"][sel]],
          lw=1.2, ls="--", color=C["law"], label="3π/I (the law)")
a1.loglog(rc["B"][sel], [2 / b for b in rc["B"][sel]],
          lw=1.0, ls=":", color=C["gray"], label="2/B")
fits = M["T10"]["fits"]
a1.text(0.03, 0.05,
        "fitted slopes vs tick (R-C, 10³–10⁵):\n" +
        f"  B: {fits['gap_B']['slope']:.4f}   i: {fits['gap_i']['slope']:.4f}\n" +
        f"  f: {fits['gap_f']['slope']:.4f}   F: {fits['gap_F']['slope']:.4f}",
        transform=a1.transAxes, fontsize=8.5, color=G700, va="bottom",
        bbox=dict(fc="#F8FAFC", ec="#E5E7EB", lw=0.6, pad=4))
a1.set_xlabel("tick B"); a1.set_ylabel("gap")
a1.set_title("(a) all four gaps decay as 1/I — the balancer's rate lock")
a1.legend(loc="lower left", bbox_to_anchor=(0, 1.02), ncol=2,
          handlelength=1.6, columnspacing=1.2)
a1.yaxis.grid(True, alpha=0.08, color=G300)

sel2 = [i for i in range(0, len(rc["B"]), step) if rc["n"][i] > 3]
a2.loglog([rc["n"][i] for i in sel2], [rc["gap_f"][i] for i in sel2],
          lw=0, marker="o", ms=1.4, color=C["f"],
          label="Gap_f at apeirogon order n")
nn = [rc["n"][i] for i in sel2]
a2.loglog(nn, [PI ** 3 / (2 * n * n) for n in nn], lw=1.4, ls="--",
          color=C["law"], label="π³/(2n²)")
a2.text(0.03, 0.05,
        f"fitted slope vs n: {fits['gap_f_vs_n']['slope']:.4f} ± {fits['gap_f_vs_n']['stderr']:.4f}",
        transform=a2.transAxes, fontsize=8.5, color=G700, va="bottom",
        bbox=dict(fc="#F8FAFC", ec="#E5E7EB", lw=0.6, pad=4))
a2.set_xlabel("apeirogon order n"); a2.set_ylabel("gap_f")
a2.set_title("(b) against its own order n, the apeirogon decays as 1/n²")
a2.legend(loc="lower left", bbox_to_anchor=(0, 1.02),
          handlelength=1.6)
a2.yaxis.grid(True, alpha=0.08, color=G300)
fig.suptitle("Fig. 1 — Gap-rate laws: −1 in the tick, −2 in the scheme's own index",
             fontsize=15, fontweight="bold")
fig.savefig(FIG / "fig1_gap_laws.png")
plt.close(fig)
print("fig1 done")

# ---------------------------------------------------------------- fig 2
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.2),
                             constrained_layout=True)
sel = slice(0, len(rc["B"]), 20)
a1.semilogx(rc["B"][sel], rc["balance_ratio"][sel], lw=1.1,
            color=C["B"], label="balance = max/min (outer three)")
a1.axhline(3 * PI / 2, ls="--", lw=1.2, color=C["law"],
           label="3π/2 = 4.712")
a1.axhline(10, ls=":", lw=1.2, color=C["warn"], label="threshold 10")
a1.scatter([8], [rc["balance_ratio"][7]], s=46, zorder=5,
           color=C["warn"], marker="v")
a1.annotate("the only warning ever: tick 8", xy=(8, rc["balance_ratio"][7]),
            xytext=(30, 10.6), fontsize=9, color=C["warn"],
            arrowprops=dict(arrowstyle="->", color=C["warn"], lw=0.9))
a1.set_xlabel("tick B"); a1.set_ylabel("balance ratio")
a1.set_title("(a) balance converges onto 3π/2 from above (R-C, 10⁵ ticks)")
a1.legend(loc="lower left", bbox_to_anchor=(0, 1.02), ncol=3,
          handlelength=1.5, columnspacing=1.1)
a1.yaxis.grid(True, alpha=0.08, color=G300)

ra = load("R-A")
n30 = list(range(1, 31))
bal30 = [ra["balance_ratio"][b - 1] for b in n30]
a2.plot(n30, bal30, lw=1.6, color=C["B"], marker="o", ms=3.5,
        label="balance")
a2.axhline(10, ls=":", lw=1.2, color=C["warn"], label="threshold 10")
nsteps = [b for b in n30 if b > 1 and ra["n"][b - 1] != ra["n"][b - 2]]
for s in nsteps:
    a2.axvline(s, lw=0.9, color=C["f"], alpha=0.55)
a2.text(nsteps[0] + 0.3, 1.05, "apeirogon n-step", fontsize=8.5,
        color=C["f"], rotation=90, va="bottom")
a2.fill_between([7.5, 9.5], 0, 14, color="#FEF3C7", alpha=0.7, zorder=0)
a2.annotate("warn @ 8\n(n=3 pinned)", xy=(8, 10.39),
            xytext=(13.5, 11.3), fontsize=9, color=C["warn"],
            arrowprops=dict(arrowstyle="->", color=C["warn"], lw=0.9))
a2.set_xlim(0.5, 30.5); a2.set_ylim(0, 13)
a2.set_xlabel("tick B"); a2.set_ylabel("balance ratio")
a2.set_title("(b) the tick-8 warning: n quantization vs the 3π/I target")
a2.legend(loc="lower left", bbox_to_anchor=(0, 1.02), ncol=2,
          handlelength=1.5)
a2.yaxis.grid(True, alpha=0.08, color=G300)
fig.suptitle("Fig. 2 — One warning in 10⁵ ticks, fully explained by the apeirogon staircase",
             fontsize=15, fontweight="bold")
fig.savefig(FIG / "fig2_balance.png")
plt.close(fig)
print("fig2 done")

# ---------------------------------------------------------------- fig 3
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.4),
                             constrained_layout=True)
sel = [i for i in range(0, len(rc["B"]), 40) if rc["B"][i] >= 100]
B = [rc["B"][i] for i in sel]
piU = [(PI - rc["U_final"][i]) * rc["I"][i] for i in sel]
Lpi = [(rc["L_final"][i] - PI) * rc["I"][i] for i in sel]
wid = [(rc["U_final"][i] - rc["L_final"][i]) * rc["I"][i] for i in sel]
a1.semilogx(B, piU, lw=1.4, color=C["B"], label="(π − U_final)·I")
a1.semilogx(B, Lpi, lw=1.4, color=C["f"], label="(L_final − π)·I")
a1.semilogx(B, wid, lw=1.4, color=C["ok"], label="(U_final − L_final)·I")
a1.axhline(2, ls="--", lw=1, color=C["ok"], alpha=0.6)
a1.text(1.1e2, 2.12, "width law 2/B → c = 2", fontsize=8.5, color=C["ok"])
a1.axhline(0, lw=0.8, color="#6B7280")
a1.set_xlabel("tick B"); a1.set_ylabel("quantity × I")
a1.set_title("(a) main runs: the final bracket IS the B band, below π")
a1.legend(loc="lower left", bbox_to_anchor=(0, 1.02), ncol=3,
          handlelength=1.5, columnspacing=1.1)
a1.yaxis.grid(True, alpha=0.08, color=G300)

selc = [i for i in range(0, len(ctrl["B"]), 4) if ctrl["B"][i] >= 10]
Bc = [ctrl["B"][i] for i in selc]
piUc = [(PI - ctrl["U_final"][i]) * ctrl["I"][i] for i in selc]
Lpic = [(ctrl["L_final"][i] - PI) * ctrl["I"][i] for i in selc]
widc = [(ctrl["U_final"][i] - ctrl["L_final"][i]) * ctrl["I"][i]
        for i in selc]
a2.semilogx(Bc, piUc, lw=1.4, color=C["B"], label="(π − U_final)·I = 0")
a2.semilogx(Bc, Lpic, lw=1.4, color=C["f"],
            label="(L_final − π)·I > 0 — bracket above π")
a2.semilogx(Bc, widc, lw=1.4, color=C["ctrl"],
            label="width·I < 0 — inverted")
a2.axhline(0, lw=0.8, color="#6B7280")
a2.set_xlabel("tick B"); a2.set_ylabel("quantity × I")
a2.set_title("(b) CTRL-R4 fix: the bracket inverts against the membrane")
a2.legend(loc="lower left", bbox_to_anchor=(0, 1.02), ncol=1,
          handlelength=1.5)
a2.yaxis.grid(True, alpha=0.08, color=G300)
fig.suptitle("Fig. 3 — The final-bracket anomaly (R4): below π by construction; the naive fix overshoots",
             fontsize=15, fontweight="bold")
fig.savefig(FIG / "fig3_bracket.png")
plt.close(fig)
print("fig3 done")

# ---------------------------------------------------------------- fig 4
fig, ax = plt.subplots(figsize=(13, 4.6), constrained_layout=True)
w = ra["_B"][:60]
sig = [ra["sigma"][b - 1] for b in w]
sheet = [1.0 if ra["outer_sheet"][b - 1] == "upper" else -1.0 for b in w]
ax.step(w, sig, where="post", lw=2.2, color=C["B"],
        label="σ — inner bif (spinorial), period 3")
ax.step(w, [2.6 * s for s in sheet], where="post", lw=2.2,
        color=C["f"], label="outer sheet (offset +2.6)")
ax.axvline(2, lw=1.2, ls=":", color=C["f"])
ax.annotate("the only OUTER_FLIP: tick 2, lower → upper,\nthen locked for 10⁵ ticks",
            xy=(2, 3.6), xytext=(9, 3.9), fontsize=9, color=C["f"],
            arrowprops=dict(arrowstyle="->", color=C["f"], lw=0.9))
for k in range(1, 4):
    ax.text(3 * k + 0.35, -1.28, f"flip @{3*k}", fontsize=7.5,
            color=C["B"], rotation=90, va="top")
ax.set_xlabel("tick B"); ax.set_ylabel("σ (outer sheet offset)")
ax.set_yticks([-1, 1, 1.6, 3.6])
ax.set_yticklabels(["−1", "+1", "lower", "upper"])
ax.set_xlim(0, 60); ax.set_ylim(-1.6, 4.4)
ax.set_title("Fig. 4 — The two bifs: a 3-tick spinorial cycle vs a one-shot outer phase (R-A, ticks 1–60)")
ax.legend(loc="lower left", bbox_to_anchor=(0, 1.02), ncol=2,
          handlelength=1.8)
ax.yaxis.grid(True, alpha=0.08, color=G300)
fig.savefig(FIG / "fig4_phase.png")
plt.close(fig)
print("fig4 done")

# verify non-blank
from PIL import Image
for f in sorted(FIG.glob("*.png")):
    im = Image.open(f).convert("L")
    h = im.histogram()
    print(f.name, im.size,
          "non-white:", round(1 - h[255] / sum(h), 3))
