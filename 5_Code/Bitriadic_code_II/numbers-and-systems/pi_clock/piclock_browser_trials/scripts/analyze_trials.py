#!/usr/bin/env python3
"""analyze_trials.py -- the T1-T15 + A-F measurement battery over the
exported trial logs (results/runs/*).  Pure log analysis: every number
here is derivable from ticks.csv / events.jsonl / session.json.
Writes results/measurements.json and prints a digest.

Exactness discipline: telescope is re-checked from the integer columns
as exact Python ints (the run-time BigInt check lives in session.json);
the gap identity (a) is exact at run time (witnessed), double-checked
here at 1e-15 relative; (b) is a double-precision identity by nature.
"""
import csv, json, math, sys
from pathlib import Path

ROOT = Path("/home/z/my-project/download/piclock-browser/results")
RUNS = ROOT / "runs"
PI = math.pi

def load_nested(run):
    """columns -> dict of lists (ints/floats/strings kept per type)"""
    path = RUNS / run / "ticks.csv"
    with open(path, newline="") as f:
        rd = csv.reader(f)
        head = next(rd)
        rows = list(rd)
    cols = {}
    INTS = {"B", "I", "m", "n", "order", "contains_pi", "sigma",
            "alpha", "beta", "gamma", "telescope_ok"}
    STRS = {"outer_sheet"}
    for j, name in enumerate(head):
        if name in INTS: cols[name] = [int(r[j]) for r in rows]
        elif name in STRS: cols[name] = [r[j] for r in rows]
        else: cols[name] = [float(r[j]) for r in rows]
    return cols

def load_legacy(run):
    path = RUNS / run / "ticks.csv"
    with open(path, newline="") as f:
        rd = csv.reader(f)
        head = next(rd)
        rows = list(rd)
    cols = {}
    for j, name in enumerate(head):
        if name in {"tick", "I", "order", "orderSize", "sigma", "angle",
                    "spheres", "wraps", "Ireg", "telescope_ok", "sheetB"}:
            try: cols[name] = [int(r[j]) for r in rows]
            except ValueError: cols[name] = [r[j] for r in rows]
        elif name in {"alpha", "beta", "gamma", "sphere_B", "sheetI",
                      "region", "sheetF"}:
            cols[name] = [r[j] for r in rows]
        else: cols[name] = [float(r[j]) for r in rows]
    return cols

def load_events(run):
    ev = []
    with open(RUNS / run / "events.jsonl") as f:
        for line in f:
            line = line.strip()
            if line: ev.append(json.loads(line))
    return ev

def session(run):
    return json.load(open(RUNS / run / "session.json"))

def mean(xs): return sum(xs) / len(xs)
def stdev(xs):
    if len(xs) < 2: return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

def linfit(xs, ys):
    """least squares y = a + b x; returns a, b, b_stderr, r2"""
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    b = sxy / sxx
    a = my - b * mx
    ssres = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    sst = syy if syy > 0 else 1e-300
    r2 = 1 - ssres / sst
    if n > 2:
        se = math.sqrt(ssres / (n - 2) / sxx)
    else: se = float("nan")
    return a, b, se, r2

def first_below(series, ticks, thr):
    for v, t in zip(series, ticks):
        if v < thr: return t
    return None

M = {}   # the measurements document
nested = {r: load_nested(r) for r in ["R-A", "R-B", "R-C", "R-F", "CTRL-R4"]}
legacy = {r: load_legacy(r) for r in ["R-D", "R-E"]}
events = {r: load_events(r) for r in
          ["R-A", "R-B", "R-C", "R-F", "CTRL-R4", "R-D", "R-E"]}

# ---------------------------------------------------------------- T1
M["T1"] = {}
for r in ["R-A", "R-B", "R-C", "R-F", "CTRL-R4"]:
    c = nested[r]
    B, cp = c["B"], c["contains_pi"]
    hits = [b for b, v in zip(B, cp) if v == 1]
    steady = [i for i, b in enumerate(B) if b >= 1000]
    pi_dU = [PI - c["U_final"][i] for i in steady]
    L_dpi = [c["L_final"][i] - PI for i in steady]
    M["T1"][r] = {
        "ticks": len(B), "contains_count": len(hits), "contains_ticks": hits,
        "straddle_fraction": len(hits) / len(B),
        "steady_pi_minus_U_final": {"min": min(pi_dU), "max": max(pi_dU),
                                    "mean": mean(pi_dU)},
        "steady_L_final_minus_pi": {"min": min(L_dpi), "max": max(L_dpi),
                                    "mean": mean(L_dpi)},
        "steady_contains_count": sum(1 for i in steady if cp[i] == 1),
    }

# ---------------------------------------------------------------- T2
M["T2"] = {}
for r in ["R-A", "R-B", "R-C"]:
    c = nested[r]
    bad_i, bad_f = [], []
    for i, B in enumerate(c["B"]):
        if not (c["L_i"][i] <= PI <= c["U_i"][i]): bad_i.append(B)
        if c["n"][i] >= 3 and not (c["L_f"][i] <= PI <= c["U_f"][i]):
            bad_f.append(B)
    M["T2"][r] = {
        "ticks": len(c["B"]),
        "leibniz_contains_pi": len(c["B"]) - len(bad_i),
        "leibniz_counterexamples": bad_i[:10],
        "apeirogon_contains_pi": len(c["B"]) - len(bad_f),
        "apeirogon_counterexamples": bad_f[:10],
    }

# ---------------------------------------------------------------- T3
M["T3"] = {}
for r, c in nested.items():
    fails = sum(1 for i in range(len(c["B"]))
                if c["alpha"][i] + c["beta"][i] + c["gamma"][i] != 0
                or c["telescope_ok"][i] != 1)
    M["T3"][r] = {"ticks": len(c["B"]), "telescope_failures": fails}
for r, c in legacy.items():
    fails = sum(1 for i in range(len(c["tick"]))
                if c["telescope_ok"][i] != 1)
    # exact re-check from the rational strings (alpha+beta+gamma)
    from fractions import Fraction
    ex = 0
    for i in range(len(c["tick"])):
        if (Fraction(c["alpha"][i]) + Fraction(c["beta"][i])
                + Fraction(c["gamma"][i])) != 0: ex += 1
    M["T3"][r] = {"ticks": len(c["tick"]),
                  "telescope_failures": fails, "exact_rational_failures": ex}
M["T3"]["telescope_fail_events_all_runs"] = sum(
    1 for evs in events.values() for e in evs
    if e["kind"] == "TELESCOPE_FAIL")

# ---------------------------------------------------------------- T4
M["T4"] = {}
for r in ["R-A", "R-B", "R-C"]:
    c = nested[r]
    dev_a, dev_b, dev_op, dev_free, floor = 0.0, 0.0, 0.0, 0.0, 0.0
    for i in range(len(c["B"])):
        gap = c["U_i"][i] - c["L_i"][i]
        law = 4 / (4 * c["m"][i] + 3)
        dev_a = max(dev_a, abs(gap - law) / law)
        I, LF = c["I"][i], c["L_F"][i]
        if I > 3:
            # the work-order expression cancels pi - L_F ~ 3pi/I;
            # its measurement floor is ulp(pi) * I / (3pi)
            dev_b = max(dev_b, abs((PI - LF) * I / (3 * PI) - 1))
            floor = max(floor, 2.220446049250313e-16 * PI * I / (3 * PI))
            # floor-free: L_F * I / (pi (I-3)) == 1 with no cancellation
            dev_free = max(dev_free,
                abs(LF * I / (PI * (I - 3)) - 1))
            dev_op = max(dev_op, abs((PI - 2 * c["F"][i] / I) * I / (3 * PI) - 1))
    M["T4"][r] = {
        "max_rel_gap_identity_deviation_double": dev_a,
        "max_rel_deviation_exact_layer_L_F": dev_b,
        "cancellation_floor_of_test_expression": floor,
        "max_rel_deviation_floor_free": dev_free,
        "max_rel_deviation_operational_F": dev_op,
        "runtime_exact_gap_identity_failures":
            session(r)["exactness"]["gap_identity_failures"],
    }
for r in ["R-D", "R-E"]:
    c = legacy[r]
    target = 2 * PI if r == "R-D" else PI
    const = 4 * PI if r == "R-D" else 3 * PI
    dev_formula, dev_op, dev_free = 0.0, 0.0, 0.0
    pre = 2 if r == "R-D" else 3
    for i in range(len(c["tick"])):
        I = c["I"][i]
        if I > pre:
            dev_formula = max(dev_formula,
                abs((target - c["ratio"][i]) * I / const - 1))
            dev_op = max(dev_op,
                abs((target - 2 * c["F"][i] / I) * I / const - 1))
            dev_free = max(dev_free,
                abs(c["ratio"][i] * I / (target * (I - pre)) - 1))
    M["T4"][r] = {
        "max_rel_deviation_ratio_formula": dev_formula,
        "max_rel_deviation_floor_free": dev_free,
        "max_rel_deviation_operational_F": dev_op,
    }

# ---------------------------------------------------------------- T5
M["T5"] = {}
for r in ["R-A", "R-B", "R-C"]:
    c = nested[r]
    B, bal = c["B"], c["balance_ratio"]
    warn = [b for b, v in zip(B, bal) if v > 10]
    # rising-edge audit from the series itself
    rising, unjustified = 0, 0
    for i in range(len(B)):
        if bal[i] > 10 and (i == 0 or bal[i - 1] <= 10): rising += 1
        elif bal[i] > 10 and i > 0 and bal[i - 1] > 10: unjustified += 1
    steady = [v for b, v in zip(B, bal) if b >= 1000]
    evs = [e for e in events[r] if e["kind"] == "BALANCE_WARNING"]
    rising_set = {B[i] for i in range(len(B))
                  if bal[i] > 10 and (i == 0 or bal[i - 1] <= 10)}
    M["T5"][r] = {
        "warning_ticks": [e["tick"] for e in evs],
        "first_warning_tick": evs[0]["tick"] if evs else None,
        "warning_events": len(evs), "rising_edges_in_series": rising,
        "mid_warning_ticks_without_edge": unjustified,
        "events_match_rising_edges": {e["tick"] for e in evs} == rising_set,
        "warn_tick_count_in_series": len(warn),
        "steady_balance_mean": mean(steady),
        "steady_balance_stdev": stdev(steady),
        "steady_balance_min": min(steady), "steady_balance_max": max(steady),
        "three_pi_over_2": 3 * PI / 2,
        "mean_minus_3pi2": mean(steady) - 3 * PI / 2,
    }
# warning/clear alternation (T5 + T15 material)
for r in ["R-A", "R-B", "R-C"]:
    seq = [(e["kind"], e["tick"]) for e in events[r]
           if e["kind"] in ("BALANCE_WARNING", "BALANCE_CLEAR")]
    ok_alt = all(seq[i][0] != seq[i + 1][0] for i in range(len(seq) - 1))
    M["T5"][r]["warning_clear_alternating"] = ok_alt

# ---------------------------------------------------------------- T6
M["T6"] = {}
for r in ["R-A", "R-B", "R-C"]:
    c = nested[r]
    of = [e["tick"] for e in events[r] if e["kind"] == "OUTER_FLIP"]
    sf = [e["tick"] for e in events[r] if e["kind"] == "SPIN_FLIP"]
    of_iv = [b - a for a, b in zip(of, of[1:])] if len(of) > 1 else []
    sf_iv = [b - a for a, b in zip(sf, sf[1:])] if len(sf) > 1 else []
    B2sig = dict(zip(c["B"], c["sigma"]))
    sig_at_flip = [B2sig.get(t) for t in of]
    mod3 = [t % 3 for t in of]
    # sheet lock: is the outer sheet constant after the last flip?
    if of:
        last_flip = of[-1]
        sheets_after = {c["outer_sheet"][i]
                        for i in range(len(c["B"]))
                        if c["B"][i] > last_flip}
    else:
        last_flip, sheets_after = None, set()
    M["T6"][r] = {
        "outer_flips": len(of), "spin_flips": len(sf),
        "outer_intervals": of_iv,
        "outer_interval_stats": {"min": min(of_iv) if of_iv else None,
            "max": max(of_iv) if of_iv else None,
            "mean": mean(of_iv) if of_iv else None},
        "spin_interval_stats": {"min": min(sf_iv) if sf_iv else None,
            "max": max(sf_iv) if sf_iv else None,
            "mean": mean(sf_iv) if sf_iv else None},
        "sigma_at_outer_flips": {str(s): sig_at_flip.count(s)
                                 for s in (1, -1)},
        "outer_flip_tick_mod3": {str(k): mod3.count(k)
                                 for k in (0, 1, 2)},
        "sheet_locked_after_last_flip":
            len(sheets_after) == 1,
        "locked_sheet": list(sheets_after)[0] if len(sheets_after) == 1
            else None,
        "flip_frequency_ratio_spin_over_outer":
            (len(sf) / len(of)) if of else None,
    }

# ---------------------------------------------------------------- T7
c = nested["R-C"]
last_dec = [i for i, b in enumerate(c["B"]) if b >= 10000]
wid_I = [(c["U_final"][i] - c["L_final"][i]) * c["I"][i]
         for i in last_dec]
piU_I = [(PI - c["U_final"][i]) * c["I"][i] for i in last_dec]
Lpi_I = [(c["L_final"][i] - PI) * c["I"][i] for i in last_dec]
# log-log slope of the final width vs I (law region)
lx = [math.log10(c["I"][i]) for i in last_dec]
ly = [math.log10(c["U_final"][i] - c["L_final"][i]) for i in last_dec]
a, b, se, r2 = linfit(lx, ly)
M["T7"] = {
    "width_times_I_last_decade": {"mean": mean(wid_I),
        "stdev": stdev(wid_I), "min": min(wid_I), "max": max(wid_I)},
    "pi_minus_U_final_times_I_last_decade": {"mean": mean(piU_I),
        "stdev": stdev(piU_I), "min": min(piU_I), "max": max(piU_I)},
    "L_final_minus_pi_times_I_last_decade": {"mean": mean(Lpi_I),
        "stdev": stdev(Lpi_I), "min": min(Lpi_I), "max": max(Lpi_I)},
    "loglog_slope_width_vs_I": {"slope": b, "stderr": se, "r2": r2,
                                "fit_from": 10000, "fit_to": 100000},
    "three_pi": 3 * PI,
}

# ---------------------------------------------------------------- T8
c = nested["R-A"]
B, LF, UF = c["B"], c["L_final"], c["U_final"]
pi_est = [4.0]   # init from S_1 (sec. 4.3)
for i in range(len(B) - 1):
    pi_est.append((LF[i] + UF[i]) / 2)
drift = [(PI - pi_est[i]) * B[i] for i in range(len(B))]
first_exc = next((B[i] for i, d in enumerate(drift) if d > 1), None)
first_nocov = next((B[i] for i in range(len(B))
                    if c["U_B"][i] < PI), None)
b_contains = [B[i] for i in range(len(B))
              if c["L_B"][i] <= PI <= c["U_B"][i]]
M["T8"] = {
    "first_tick_drift_exceeds_1": first_exc,
    "drift_at_that_tick": next((drift[i] for i in range(len(B))
        if B[i] == first_exc), None) if first_exc else None,
    "first_tick_U_B_below_pi": first_nocov,
    "final_pi_est_minus_pi": pi_est[-1] - PI,
    "final_drift_times_B": drift[-1],
    "B_band_contains_pi_ticks": b_contains,
    "B_band_contains_pi_count": len(b_contains),
}

# ---------------------------------------------------------------- T9
c = nested["R-A"]
M["T9"] = {"window": []}
for i in range(len(c["B"])):
    if 5 <= c["B"][i] <= 15:
        I = c["I"][i]
        ideal_n = math.floor(math.sqrt(PI * PI * I / 6))
        M["T9"]["window"].append({
            "B": c["B"][i], "n": c["n"][i], "ideal_n": ideal_n,
            "gap_f": c["gap_f"][i], "gap_i": c["gap_i"][i],
            "gap_B": c["gap_B"][i], "balance": c["balance_ratio"][i],
            "warn": c["balance_ratio"][i] > 10,
        })
n_changes = []
prev = None
for i in range(len(c["B"])):
    if prev is not None and c["n"][i] != prev:
        n_changes.append(c["B"][i])
    prev = c["n"][i]
warns = [e["tick"] for e in events["R-A"]
         if e["kind"] == "BALANCE_WARNING"]
M["T9"]["n_at_tick_8"] = next((c["n"][i] for i in range(len(c["B"]))
    if c["B"][i] == 8), None)
M["T9"]["n_changes_R-A"] = n_changes
M["T9"]["warning_ticks_R-A"] = warns
# ticks since last n-step for each warning
M["T9"]["warnings_since_last_n_step"] = [
    {"tick": w, "last_n_step": max([x for x in n_changes if x <= w],
                                   default=None),
     "gap": w - max([x for x in n_changes if x <= w], default=0)}
    for w in warns]
c10 = nested["R-B"]
n_changes10 = []
prev = None
for i in range(len(c10["B"])):
    if prev is not None and c10["n"][i] != prev:
        n_changes10.append(c10["B"][i])
    prev = c10["n"][i]
warns10 = [e["tick"] for e in events["R-B"]
           if e["kind"] == "BALANCE_WARNING"]
M["T9"]["R-B_warning_vs_n_step"] = [
    {"tick": w, "gap_since_last_n_step":
        w - max([x for x in n_changes10 if x <= w], default=0)}
    for w in warns10]
M["T9"]["R-B_n_steps"] = len(n_changes10)

# ---------------------------------------------------------------- T10
c = nested["R-C"]
sel = [i for i, b in enumerate(c["B"]) if 1000 <= b <= 100000]
lx = [math.log10(c["B"][i]) for i in sel]
fits = {}
for name, col in [("gap_B", "gap_B"), ("gap_i", "gap_i"),
                  ("gap_f", "gap_f"), ("gap_F", "gap_F")]:
    ly = [math.log10(c[col][i]) for i in sel]
    a, b, se, r2 = linfit(lx, ly)
    fits[name] = {"slope": b, "stderr": se, "r2": r2}
# gap_f vs its own index n (the -2 law)
sel2 = [i for i in sel if c["n"][i] > 3]
lxn = [math.log10(c["n"][i]) for i in sel2]
lyn = [math.log10(c["gap_f"][i]) for i in sel2]
a, b, se, r2 = linfit(lxn, lyn)
fits["gap_f_vs_n"] = {"slope": b, "stderr": se, "r2": r2}
M["T10"] = {"fit_range_ticks": [1000, 100000], "fits": fits,
            "theory": {"gap_B_vs_tick": -1, "gap_i_vs_tick": -1,
                       "gap_f_vs_tick": -1,
                       "gap_F_vs_tick": -1, "gap_f_vs_n": -2,
                        "note": "hypothesis stated -2 for gap_f/gap_F vs tick; the balancer sets n ~ sqrt(I), so vs tick it is -1"}}

# ---------------------------------------------------------------- T11
c = nested["R-A"]
M["T11"] = {
    "sigma_ticks_1_to_12": [c["sigma"][i] for i in range(12)],
    "first_10_spin_flips": [
        {"tick": e["tick"], "to": e["payload"]["to"]}
        for e in events["R-A"] if e["kind"] == "SPIN_FLIP"][:10],
}
sf = [e["tick"] for e in events["R-A"] if e["kind"] == "SPIN_FLIP"]
iv = [b - a for a, b in zip(sf, sf[1:])]
M["T11"]["all_spin_intervals_3"] = all(v == 3 for v in iv)
M["T11"]["spin_interval_min_max"] = [min(iv), max(iv)] if iv else None

# ---------------------------------------------------------------- T13
M["T13"] = {}
ca, cb = nested["R-F"], nested["R-B"]
int_diffs, dbl_bad = [], []
for col in ca:
    if col == "outer_sheet": continue
    for i in range(len(ca["B"])):
        va, vb = ca[col][i], cb[col][i]
        if col in {"B", "I", "m", "n", "order", "contains_pi", "sigma",
                   "alpha", "beta", "gamma", "telescope_ok"}:
            if va != vb: int_diffs.append((col, ca["B"][i], va, vb))
        else:
            dv = abs(va - vb) / max(1e-300, abs(vb))
            if dv > 1e-12: dbl_bad.append((col, ca["B"][i], va, vb, dv))
sheet_diffs = sum(1 for x, y in zip(ca["outer_sheet"], cb["outer_sheet"])
                  if x != y)
ea = [(e["kind"], e["tick"]) for e in events["R-F"]]
eb = [(e["kind"], e["tick"]) for e in events["R-B"]]
M["T13"] = {
    "integer_or_bool_mismatches": len(int_diffs),
    "double_mismatches_gt_1e-12": len(dbl_bad),
    "worst_double_rel_dev": max((d[4] for d in dbl_bad), default=0.0),
    "sheet_mismatches": sheet_diffs,
    "event_sequences_identical": ea == eb,
    "event_counts": {"R-F": len(ea), "R-B": len(eb)},
}

# ---------------------------------------------------------------- T15
M["T15"] = {}
for r in ["R-A", "R-B", "R-C", "R-F", "CTRL-R4"]:
    evs = events[r]
    pairs = [(e["kind"], e["tick"]) for e in evs]
    dups = len(pairs) - len(set(pairs))
    c = nested[r]
    order_changes = sum(1 for i in range(1, len(c["B"]))
                        if c["order"][i] != c["order"][i - 1])
    rolls = sum(1 for e in evs if e["kind"] == "ORDER_ROLLOVER")
    # warning edge audit against the series
    bal = c["balance_ratio"]; B = c["B"]
    rising = {B[i] for i in range(len(B))
              if bal[i] > 10 and (i == 0 or bal[i - 1] <= 10)}
    warn_events = {e["tick"] for e in evs
                   if e["kind"] == "BALANCE_WARNING"}
    M["T15"][r] = {
        "duplicate_kind_tick_pairs": dups,
        "order_changes_in_csv": order_changes,
        "ORDER_ROLLOVER_events": rolls,
        "rollover_match": order_changes == rolls,
        "warning_events_match_rising_edges": warn_events == rising,
        "PRECISION_FOLD_events": sum(1 for e in evs
                                     if e["kind"] == "PRECISION_FOLD"),
    }
for r in ["R-D", "R-E"]:
    c = legacy[r]
    order_changes = sum(1 for i in range(1, len(c["tick"]))
                        if c["order"][i] != c["order"][i - 1])
    rolls = sum(1 for e in events[r] if e["kind"] == "ORDER_ROLLOVER")
    pairs = [(e["kind"], e["tick"]) for e in events[r]]
    M["T15"][r] = {
        "duplicate_kind_tick_pairs": len(pairs) - len(set(pairs)),
        "order_changes_in_csv": order_changes,
        "ORDER_ROLLOVER_events": rolls, "rollover_match":
            order_changes == rolls,
        "PRECISION_FOLD_events": sum(1 for e in events[r]
                                     if e["kind"] == "PRECISION_FOLD"),
    }

# ---------------------------------------------------------------- A
c = nested["R-C"]
M["A"] = {"thresholds": {}}
for name, col in [("B", "gap_B"), ("i", "gap_i"), ("f", "gap_f"),
                  ("F", "gap_F")]:
    M["A"]["thresholds"][name] = {
        "t_1e-3": first_below(c[col], c["B"], 1e-3),
        "t_1e-4": first_below(c[col], c["B"], 1e-4),
        "t_1e-5": first_below(c[col], c["B"], 1e-5),
    }
M["A"]["final_width_thresholds"] = {
    "t_1e-3": first_below([u - l for u, l in
        zip(c["U_final"], c["L_final"])], c["B"], 1e-3),
    "t_1e-4": first_below([u - l for u, l in
        zip(c["U_final"], c["L_final"])], c["B"], 1e-4),
    "t_1e-5": first_below([u - l for u, l in
        zip(c["U_final"], c["L_final"])], c["B"], 1e-5),
}
# binding layer (largest gap) at each threshold tick
for thr, key in [(1e-3, "t_1e-3"), (1e-4, "t_1e-4"), (1e-5, "t_1e-5")]:
    t = M["A"]["thresholds"]["F"][key]
    if t is None:
        M["A"][f"binding_at_{key}"] = {
            "tick": None,
            "note": "no layer reaches this threshold within 100,000 ticks"}
        continue
    i = c["B"].index(t)
    gaps = {"B": c["gap_B"][i], "i": c["gap_i"][i],
            "f": c["gap_f"][i], "F": c["gap_F"][i]}
    M["A"][f"binding_at_{key}"] = {
        "tick": t, "gaps": gaps,
        "largest": max(gaps, key=gaps.get),
        "note": "the final width is governed by the widest lower gap + the U side; Farey gap_F equals the law 3pi/I exactly"}
# asymptotic constants gap*I over the last decade
sel = [i for i, b in enumerate(c["B"]) if b >= 10000]
M["A"]["asymptotic_gap_times_I"] = {
    name: {"mean": mean([c[col][i] * c["I"][i] for i in sel]),
           "stdev": stdev([c[col][i] * c["I"][i] for i in sel])}
    for name, col in [("B", "gap_B"), ("i", "gap_i"), ("f", "gap_f"),
                      ("F", "gap_F")]}
M["A"]["laws"] = {
    "gap_B": "2/B (exact by construction)", "gap_i": "4/(4m+3)",
    "gap_f": "pi^3/(2n^2) with n^2 ~ pi^2 I/6 -> 3pi/I",
    "gap_F": "3pi/I (exact law)",
    "final_width": "max lower + U side; measured c in T7"}

# ---------------------------------------------------------------- B
M["B"] = {}
c = nested["R-B"]
first_nocov = next((c["B"][i] for i in range(len(c["B"]))
                    if c["U_B"][i] < PI), None)
M["B"]["R-B_first_U_B_below_pi"] = first_nocov
sel = [i for i, b in enumerate(c["B"]) if b >= 1000]
M["B"]["R-B_steady"] = {
    "pi_minus_U_final_times_I": mean(
        [(PI - c["U_final"][i]) * c["I"][i] for i in sel]),
    "width_times_I": mean(
        [(c["U_final"][i] - c["L_final"][i]) * c["I"][i] for i in sel]),
    "contains_rate": sum(1 for i in sel if c["contains_pi"][i]) / len(sel),
}
# the control
cc = nested["CTRL-R4"]
selc = [i for i, b in enumerate(cc["B"]) if b >= 1000]
M["B"]["CTRL-R4"] = {
    "fix": "pi_est := outer-bracket midpoint after each tick (runner-side)",
    "contains_count": session("CTRL-R4")["contains_pi"]["count"],
    "contains_ticks": session("CTRL-R4")["contains_pi"]["ticks"],
    "steady_contains_rate": sum(1 for i in selc
        if cc["contains_pi"][i]) / len(selc),
    "steady_pi_minus_U_final_times_I": mean(
        [(PI - cc["U_final"][i]) * cc["I"][i] for i in selc]),
    "steady_width_times_I": mean(
        [(cc["U_final"][i] - cc["L_final"][i]) * cc["I"][i] for i in selc]),
    "first_U_B_below_pi": next((cc["B"][i] for i in range(len(cc["B"]))
        if cc["U_B"][i] < PI), None),
    "final_contains": cc["contains_pi"][-1],
}
# fixed-point analysis of the control (from the log itself)
# the control's steady state, from the log itself
selc_all = [i for i in range(len(cc["B"])) if cc["B"][i] >= 1000]
inverted = sum(1 for i in selc_all
               if cc["L_final"][i] > cc["U_final"][i])
U_is_pi = sum(1 for i in selc_all
              if cc["U_final"][i] == PI)
M["B"]["CTRL-R4_steady"] = {
    "inverted_ticks_L_gt_U": inverted,
    "ticks_with_U_final_equal_pi_bitwise": U_is_pi,
    "steady_ticks": len(selc_all),
    "L_final_minus_pi_times_I": mean(
        [(cc["L_final"][i] - PI) * cc["I"][i] for i in selc_all]),
    "width_times_I": mean(
        [(cc["U_final"][i] - cc["L_final"][i]) * cc["I"][i] for i in selc_all]),
    "interpretation": "the fix overshoots: the B band rides ABOVE pi; "
      "L_final = L_B > pi while U_final = min(U_outer, pi) = pi, so the "
      "intersection is EMPTY (width negative). The failure moves from "
      "'below the membrane' to 'inverted against the membrane'.",
}
# main run fixed point: pi_est and the B band
selm = [i for i in range(len(c["B"])) if c["B"][i] >= 1000]
pi_est_main = [(c["L_final"][i] + c["U_final"][i]) / 2 for i in selm]
M["B"]["R-B_fixed_point"] = {
    "steady_pi_minus_pi_est_times_I": mean(
        [(PI - pi_est_main[i]) * c["I"][i] for i in range(len(selm))]),
    "final_equals_B_band_ticks": sum(
        1 for i in selm
        if c["L_final"][i] == c["L_B"][i]
        and c["U_final"][i] == c["U_B"][i]),
    "steady_ticks": len(selm),
    "note": "when both sides bind on the B band, mid(final) = pi_est and "
      "pi_est self-replicates; the bracket is the B band riding below pi",
}

# ---------------------------------------------------------------- C
c = nested["R-C"]
sel = [i for i, b in enumerate(c["B"]) if b >= 10000]
mI = [c["m"][i] / c["I"][i] for i in sel]
n2I = [c["n"][i] ** 2 / c["I"][i] for i in sel]
M["C"] = {
    "m_over_I_last_decade": {"mean": mean(mI), "stdev": stdev(mI),
        "min": min(mI), "max": max(mI)},
    "one_over_3pi": 1 / (3 * PI),
    "n2_over_I_last_decade": {"mean": mean(n2I), "stdev": stdev(n2I),
        "min": min(n2I), "max": max(n2I)},
    "pi2_over_6": PI * PI / 6,
    "m_rel_dev": abs(mean(mI) - 1 / (3 * PI)) / (1 / (3 * PI)),
    "n2_rel_dev": abs(mean(n2I) - PI * PI / 6) / (PI * PI / 6),
    "note": "n2/I is a staircase (integer n); mean vs pi^2/6 with quantization residual",
}
# legacy cross-check: gap law constants, computed against the right
# target from the ratio column (the engine's 'error' field is always
# pi-referenced, so the full-region lock is |ratio - 2pi| * I -> 4pi)
cl = legacy["R-D"]
sel = [i for i in range(len(cl["tick"])) if cl["I"][i] > 2]
M["C"]["R-D_full_region"] = {
    "target": 2 * PI,
    "gap_law_ratio_minus_2pi_times_I": {
        "mean": sum(abs(cl["ratio"][i] - 2 * PI) * cl["I"][i]
                    for i in sel) / len(sel),
        "min": min(abs(cl["ratio"][i] - 2 * PI) * cl["I"][i] for i in sel),
        "max": max(abs(cl["ratio"][i] - 2 * PI) * cl["I"][i] for i in sel),
        "count": len(sel)},
    "expected_constant": 4 * PI,
    "note": "the engine error field is pi-referenced in both regions; " +
            "the full-region lock is measured from the ratio column"}
ce = legacy["R-E"]
sel = [i for i in range(len(ce["tick"])) if ce["I"][i] > 3]
M["C"]["R-E_half_region"] = {
    "target": PI,
    "gap_law_ratio_minus_pi_times_I": {
        "mean": sum(abs(ce["ratio"][i] - PI) * ce["I"][i] for i in sel)
                / len(sel),
        "min": min(abs(ce["ratio"][i] - PI) * ce["I"][i] for i in sel),
        "max": max(abs(ce["ratio"][i] - PI) * ce["I"][i] for i in sel),
        "count": len(sel)},
    "expected_constant": 3 * PI,
}

# ---------------------------------------------------------------- D
c = nested["R-C"]
of = [e["tick"] for e in events["R-C"] if e["kind"] == "OUTER_FLIP"]
B2sig = dict(zip(c["B"], c["sigma"]))
sig_at = [B2sig.get(t) for t in of]
mod3 = [t % 3 for t in of]
M["D"] = {
    "outer_flips_R-C": len(of),
    "outer_flip_ticks_R-C": of,
    "outer_intervals_R-C": [b - a for a, b in zip(of, of[1:])],
    "sigma_at_outer_flips_R-C": {str(s): sig_at.count(s)
                                 for s in (1, -1)},
    "outer_flip_mod3_R-C": {str(k): mod3.count(k) for k in (0, 1, 2)},
    "spin_period": 3,
}

# ---------------------------------------------------------------- E
M["E"] = []
# E1: gap_f slope correction
M["E"].append({"finding": "T10 hypothesis correction",
    "detail": "gap_f and gap_F slopes vs TICK are -1, not -2; -2 holds for gap_f vs its own index n (the balancer sets n ~ sqrt(pi^2 I/6))",
    "witness": M["T10"]["fits"]})
# E2: control negative result
M["E"].append({"finding": "the naive R4 one-line fix does not restore containment",
    "detail": "anchoring pi_est to the outer midpoint still leaves U_final below pi in steady state: the B band half-width 1/B is narrower than the outer bracket's lower offset 3pi/(2I); fixed point U_B = L_outer + 2/I < pi",
    "witness": M["B"]["CTRL-R4"]})
# E2b: control inversion detail
M["E"].append({"finding": "the R4 control run inverts the final bracket",
    "detail": "with pi_est anchored to the outer midpoint, the B band overshoots ABOVE pi: L_final > pi = U_final in every steady tick (empty intersection, negative width ~ -2.7/I)",
    "witness": M["B"]["CTRL-R4_steady"]})
# E3: legacy sphere-mask saturation
c = legacy["R-D"]
FULL = (1 << 64) - 1
sat = next((c["tick"][i] for i in range(len(c["tick"]))
            if int(c["sphere_B"][i]) == FULL), None)
M["E"].append({"finding": "the legacy sphere mask saturates",
    "detail": f"B = 2^64 - 1 first at tick {sat} in R-D (order ~{c['order'][c['tick'].index(sat)] if sat else None}); every bit is set forever after, so the presence register carries no further information",
    "witness": {"first_all_ones_tick": sat}})
# E4: F accumulation drift
M["E"].append({"finding": "the operational F drifts from F_exact by a random walk",
    "detail": "accumulated double rounding of F += pi/2 vs the closed formula (pi/2)(I-3)",
    "witness": {r: M["T4"].get(r, {}).get("max_rel_deviation_operational_F")
                for r in ["R-A", "R-B", "R-C", "R-D", "R-E"]}})
# E5: contains ticks identical across run lengths
M["E"].append({"finding": "the straddling ticks are the same four early ticks in every run",
    "detail": "R-A/R-B/R-C/R-F all report contains_count = 4; the ticks are the fixed early transient, never revisited",
    "witness": {r: M["T1"][r]["contains_ticks"] for r in
                ["R-A", "R-B", "R-C", "R-F"]}})
# E3b: the outer sheet is a one-shot
M["E"].append({"finding": "the outer phase flips exactly once (tick 2) and locks",
    "detail": "every run R-A/R-B/R-C reports a single OUTER_FLIP at tick 2 (lower -> upper); the sheet then stays 'upper' for 100,000 ticks -- the outer bif has no cadence to correlate with the 3-tick spinorial cadence",
    "witness": {"flips": M["T6"]["R-C"]["outer_flips"],
                "sigma_at_flip": M["T6"]["R-C"]["sigma_at_outer_flips"],
                "locked": M["T6"]["R-C"]["sheet_locked_after_last_flip"]}})
# E6: warnings cluster against n-steps
M["E"].append({"finding": "balance warnings cluster in the window before an n-step",
    "detail": "gap_f lags the 3pi/I target between apeirogon increments; warnings fire inside those windows",
    "witness": {"R-A": M["T9"]["warnings_since_last_n_step"],
                "R-B_gaps": M["T9"]["R-B_warning_vs_n_step"]}})

# ---------------------------------------------------------------- F
c = nested["R-C"]
sel = [i for i, b in enumerate(c["B"]) if b >= 10000]
corr = {}
for a_, b_ in [("gap_i", "gap_f"), ("gap_B", "gap_f"), ("gap_i", "gap_B")]:
    xs = [c[a_][i] for i in sel]; ys = [c[b_][i] for i in sel]
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs)
                    * sum((y - my) ** 2 for y in ys))
    corr[f"{a_}_vs_{b_}"] = num / den if den else None
M["F"] = {
    "gap_correlations_last_decade_R-C": corr,
    "law_rates_measured": M["A"]["asymptotic_gap_times_I"],
    "three_pi": 3 * PI,
}

json.dump(M, open(ROOT / "measurements.json", "w"), indent=1)
print("measurements.json written")
print("\n=== digest ===")
print("T1 contains:", {r: (M['T1'][r]['contains_count'],
      M['T1'][r]['contains_ticks']) for r in ['R-A','R-B','R-C','CTRL-R4']})
print("T2:", {r: (M['T2'][r]['leibniz_counterexamples'],
      M['T2'][r]['apeirogon_counterexamples']) for r in ['R-A','R-B','R-C']})
print("T3 failures:", {r: v['telescope_failures'] for r, v in M['T3'].items() if isinstance(v, dict)})
print("T4 max devs:", {r: M['T4'][r].get('max_rel_deviation_exact_layer_L_F',
      M['T4'][r].get('max_rel_deviation_ratio_formula')) for r in M['T4']})
print("T5 first warnings:", {r: M['T5'][r]['first_warning_tick'] for r in ['R-A','R-B','R-C']},
      "steady mean:", {r: round(M['T5'][r]['steady_balance_mean'], 3) for r in ['R-A','R-B','R-C']})
print("T6 outer flips:", {r: M['T6'][r]['outer_flips'] for r in ['R-A','R-B','R-C']},
      "sigma at flips R-C:", M['T6']['R-C']['sigma_at_outer_flips'],
      "mod3 R-C:", M['T6']['R-C']['outer_flip_tick_mod3'])
print("T7 width*I:", M['T7']['width_times_I_last_decade']['mean'],
      "slope:", M['T7']['loglog_slope_width_vs_I']['slope'])
print("T8 first drift>1:", M['T8']['first_tick_drift_exceeds_1'],
      "first U_B<pi:", M['T8']['first_tick_U_B_below_pi'])
print("T10 fits:", {k: round(v['slope'], 4) for k, v in M['T10']['fits'].items()})
print("T11 sigma 1-12:", M['T11']['sigma_ticks_1_to_12'],
      "all 3:", M['T11']['all_spin_intervals_3'])
print("T13:", M['T13'])
print("T15:", json.dumps(M['T15'], default=str)[:400])
print("A thresholds:", M['A']['thresholds'])
print("B ctrl:", M['B']['CTRL-R4']['steady_contains_rate'],
      M['B']['CTRL-R4']['steady_pi_minus_U_final_times_I'])
print("C:", M['C']['m_rel_dev'], M['C']['n2_rel_dev'],
      M['C']['n2_over_I_last_decade'])
print("D intervals:", M['D']['outer_intervals_R-C'][:20], "...")
print("F corr:", M['F']['gap_correlations_last_decade_R-C'])
