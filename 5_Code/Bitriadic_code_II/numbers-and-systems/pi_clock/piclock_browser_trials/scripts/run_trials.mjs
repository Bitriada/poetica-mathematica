/* run_trials.mjs -- the single-owner trial loop for the nested-bif
 * pi-clock battery (NESTEDBIF_TRIALS).
 *
 * Each run streams three logs into results/runs/<RUN>/:
 *   ticks.csv   -- every tick, the 30-column schema of the work order
 *                  (nested-bif runs) or the documented legacy schema
 *   events.jsonl-- on-change events, kinds OUTER_FLIP | SPIN_FLIP |
 *                  BALANCE_WARNING | BALANCE_CLEAR (documented extra)
 *                  | ORDER_ROLLOVER | PRECISION_FOLD | TELESCOPE_FAIL
 *   session.json-- config, counters, gap stats, exactness witnesses
 *
 * Exactness: the telescope identity and the Leibniz gap identity are
 * verified per tick by cross-multiplied BigInts taken from the LIVE
 * engine registers (never floating point); the first violating tick
 * would be captured as an exact witness.  The CSV carries the display
 * doubles; the analyzer re-checks what it can from the log.
 *
 * Runs: R-A R-B R-C (nested-bif half 1k/10k/100k), R-D (legacy FULL
 * 100k -- the 2pi lock lives in the legacy Farey layer; the nested-bif
 * engine is half-region only, documented reading), R-E (legacy half
 * 10k), R-F (nested-bif 10k with kill/restore at 5,000), CTRL-R4
 * (nested-bif 10k with the one-line R4 fix applied RUNNER-SIDE:
 * after each tick, pi_est := outer-bracket midpoint; core untouched).
 *
 * Usage: node run_trials.mjs R-A|R-B|R-C|R-D|R-E|R-F|CTRL-R4|all
 */
import { readFileSync, mkdirSync, writeFileSync, createWriteStream }
  from "node:fs";
import { join } from "node:path";

const ROOT = "/home/z/my-project/download/piclock-browser/";
const OUT = join(ROOT, "results", "runs");
globalThis.globalThis = globalThis;
for (const f of ["core/rational.js", "core/piclock.js", "core/nestedbif.js"])
  eval(readFileSync(join(ROOT, f), "utf8"));

const PI = Math.PI;

// epoch machinery must be gone (run validity rule)
if (PiLock.EPOCH_TICKS !== undefined || PiLock.FOLD_TICKS !== undefined)
  throw new Error("run invalid: epoch constants present");
if (PiLock.PRECISION_BOUND !== 2 ** 52)
  throw new Error("run invalid: precision boundary missing");

const RUNS = {
  "R-A": { engine: "nested", ticks: 1000 },
  "R-B": { engine: "nested", ticks: 10000 },
  "R-C": { engine: "nested", ticks: 10000 * 10 },   // 100k
  "R-D": { engine: "legacy", ticks: 10000 * 10, region: "full" },
  "R-E": { engine: "legacy", ticks: 10000, region: "half" },
  "R-F": { engine: "nested", ticks: 10000, killAt: 5000 },
  "CTRL-R4": { engine: "nested", ticks: 10000, ctrlR4: true },
};

const NB_COLS = ["B", "I", "m", "n", "order", "L_B", "U_B", "L_i", "U_i",
  "L_f", "U_f", "L_F", "U_F", "L_outer", "U_outer", "L_final", "U_final",
  "contains_pi", "gap_B", "gap_i", "gap_f", "gap_F", "balance_ratio",
  "outer_sheet", "sigma", "alpha", "beta", "gamma", "telescope_ok",
  "F", "F_exact"];

const LEG_COLS = ["tick", "I", "order", "orderSize", "F", "F_exact",
  "ratio", "error", "sigma", "angle", "alpha", "beta", "gamma",
  "telescope_ok", "sphere_B", "spheres", "wraps", "Ireg", "sheetB",
  "sheetI", "sheetF", "region"];

function fmt(x) {
  if (typeof x === "number") return String(x);       // round-trip repr
  return String(x);
}

/** accumulate streaming stats */
function stats() {
  return { n: 0, min: Infinity, max: -Infinity, sum: 0,
    add(v) { this.n++; if (v < this.min) this.min = v;
      if (v > this.max) this.max = v; this.sum += v; },
    done() { return { count: this.n, min: this.min, max: this.max,
      mean: this.sum / this.n }; } };
}

function runNested(id, cfg) {
  const dir = join(OUT, id);
  mkdirSync(dir, { recursive: true });
  const t0 = performance.now();
  // R-C uses the demo-default ring (8,192): log-ring pressure is part
  // of the run's purpose; other runs use the same default.
  let engine = new PiLock.NestedBifClock({ logCap: 8192 });
  const ticksCsv = createWriteStream(join(dir, "ticks.csv"));
  const eventsJsonl = createWriteStream(join(dir, "events.jsonl"));
  ticksCsv.write(NB_COLS.join(",") + "\n");

  const ev = stats();        // event counting by kind
  const counts = {};
  const gaps = { gap_B: stats(), gap_i: stats(), gap_f: stats(),
    gap_F: stats(), final_width: stats(), pi_minus_U: stats(),
    L_minus_pi: stats() };
  const balance = stats();
  const contains = [];
  let telescopeFails = 0, gapFails = 0, firstWitness = null;
  let histMark = 0;
  const note = (line) => eventsJsonl.write(JSON.stringify(line) + "\n");

  for (let t = 1; t <= cfg.ticks; t++) {
    // ---- R-F: kill the worker at killAt, restore from persisted state
    if (cfg.killAt && t === cfg.killAt + 1) {
      const persisted = JSON.parse(JSON.stringify(engine.toJSON()));
      engine = null;                                   // the worker dies
      engine = PiLock.NestedBifClock.fromJSON(persisted);
      histMark = engine.history.length; // serialized history already streamed
    }
    const s = engine.tick();
    // drain new events (kind mapping for the trial battery)
    for (const e of engine.history.slice(histMark)) {
      const kind = e.type === "WARN_BALANCE" ? "BALANCE_WARNING"
        : e.type === "WARN_CLEAR" ? "BALANCE_CLEAR"
        : e.type === "ORDER_ROLL" ? "ORDER_ROLLOVER" : e.type;
      const payload = { ...e }; delete payload.type; delete payload.tick;
      note({ kind, tick: e.tick, payload });
      counts[kind] = (counts[kind] || 0) + 1;
    }
    histMark = engine.history.length;
    // exact witnesses from the LIVE BigInt registers
    if (engine.alpha + engine.beta + engine.gamma !== 0n) {
      telescopeFails++;
      note({ kind: "TELESCOPE_FAIL", tick: s.B,
        payload: { alpha: String(engine.alpha),
          beta: String(engine.beta), gamma: String(engine.gamma) } });
      if (!firstWitness) firstWitness =
        { tick: s.B, kind: "TELESCOPE_FAIL",
          alpha: engine.alpha.toString(), beta: engine.beta.toString(),
          gamma: engine.gamma.toString() };
    }
    const mNum = Number(engine.m);
    if ((engine.numHi - engine.numLo) * BigInt(4 * mNum + 3)
        !== 4n * engine.den) {
      gapFails++;
      if (!firstWitness) firstWitness =
        { tick: s.B, kind: "GAP_IDENTITY_FAIL",
          numHi: engine.numHi.toString(), numLo: engine.numLo.toString(),
          den: engine.den.toString(), m: mNum };
    }
    // tick row
    const row = {
      B: s.B, I: s.I, m: s.m, n: s.n, order: s.order,
      L_B: s.L_B, U_B: s.U_B, L_i: s.L_i, U_i: s.U_i,
      L_f: s.L_f, U_f: s.U_f, L_F: s.L_F, U_F: s.U_F,
      L_outer: s.L_outer, U_outer: s.U_outer,
      L_final: s.L_final, U_final: s.U_final,
      contains_pi: s.containsPi ? 1 : 0,
      gap_B: s.gapB, gap_i: s.gapI, gap_f: s.gapF, gap_F: s.gapFF,
      balance_ratio: s.balance, outer_sheet: s.sheetOuter,
      sigma: s.sigma, alpha: s.alpha, beta: s.beta, gamma: s.gamma,
      telescope_ok: s.telescope ? 1 : 0,
      F: s.F, F_exact: s.Fexact,
    };
    ticksCsv.write(NB_COLS.map((c) => fmt(row[c])).join(",") + "\n");
    if (s.containsPi) contains.push(s.B);
    gaps.gap_B.add(s.gapB); gaps.gap_i.add(s.gapI);
    gaps.gap_f.add(s.gapF); gaps.gap_F.add(s.gapFF);
    gaps.final_width.add(s.U_final - s.L_final);
    gaps.pi_minus_U.add(PI - s.U_final);
    gaps.L_minus_pi.add(s.L_final - PI);
    balance.add(s.balance);
    // ---- CTRL-R4: the one-line fix, applied OUTSIDE the core
    if (cfg.ctrlR4) engine.piEst = (s.L_outer + s.U_outer) / 2;
    if (t % 10000 === 0) console.log(`  ${id}: tick ${t}`);
  }
  ticksCsv.end(); eventsJsonl.end();
  const wallMs = performance.now() - t0;
  const gapsDone = {};
  for (const k of Object.keys(gaps)) gapsDone[k] = gaps[k].done();
  const last = engine.tickLog[engine.tickLog.length - 1];
  const session = {
    run: id, engine: "nested-bif (core/nestedbif.js)", region: "half",
    ticks: cfg.ticks, wallMs: Math.round(wallMs),
    node: process.version,
    config: { threshold: engine.threshold, logCap: engine.logCap,
      maxHistory: engine.maxHistory },
    kill_restore: cfg.killAt
      ? { killed_at_tick: cfg.killAt, restored_from: "toJSON" } : null,
    control: cfg.ctrlR4
      ? "R4 one-line fix: after each tick, pi_est := outer-bracket midpoint (runner-side; core untouched)"
      : null,
    final: { B: last.B, I: last.I, m: last.m, n: last.n,
      order: last.order, orderSize: last.orderSize,
      L_final: last.L_final, U_final: last.U_final,
      sigma: last.sigma, sheetOuter: last.sheetOuter,
      alpha: last.alpha, beta: last.beta, gamma: last.gamma,
      ghost: last.ghost, F: last.F, F_exact: last.Fexact },
    event_counts: Object.assign(
      { OUTER_FLIP: 0, SPIN_FLIP: 0, BALANCE_WARNING: 0, BALANCE_CLEAR: 0,
        ORDER_ROLLOVER: 0, PRECISION_FOLD: 0, TELESCOPE_FAIL: 0 }, counts),
    gaps: gapsDone, balance: balance.done(),
    contains_pi: { count: contains.length, ticks: contains },
    exactness: { telescope_failures: telescopeFails,
      gap_identity_failures: gapFails, first_witness: firstWitness },
    log_ring: { cap: engine.logCap, dropped: engine.logDropped,
      dropped_events: engine.logDroppedEvents,
      events_held: engine.history.length },
  };
  writeFileSync(join(dir, "session.json"), JSON.stringify(session, null, 1));
  console.log(`  ${id}: done in ${(wallMs / 1000).toFixed(1)}s, ` +
    `contains_pi ${contains.length}, events ` +
    Object.values(counts).reduce((a, b) => a + b, 0) +
    `, telescope fails ${telescopeFails}, gap fails ${gapFails}`);
}

function runLegacy(id, cfg) {
  const dir = join(OUT, id);
  mkdirSync(dir, { recursive: true });
  const t0 = performance.now();
  const engine = new PiLock.PiClock({ region: cfg.region });
  const ticksCsv = createWriteStream(join(dir, "ticks.csv"));
  const eventsJsonl = createWriteStream(join(dir, "events.jsonl"));
  ticksCsv.write(LEG_COLS.join(",") + "\n");
  const counts = { ORDER_ROLLOVER: 0, SPIN_FLIP: 0, PRECISION_FOLD: 0,
    TELESCOPE_FAIL: 0 };
  const err = stats(), fDrift = stats(), ratioDev = stats();
  let telescopeFails = 0, firstWitness = null;
  let prevSigma = 1, prevOrder = 1, lastRatio = null;
  const gapLaw = stats();   // |error| * I  ->  3pi (half) or 4pi (full)
  const note = (line) => eventsJsonl.write(JSON.stringify(line) + "\n");
  const target = cfg.region === "full" ? 2 * PI : PI;
  for (let t = 1; t <= cfg.ticks; t++) {
    const s = engine.tick();
    if (s.telescope === false) { telescopeFails++;
      note({ kind: "TELESCOPE_FAIL", tick: s.tick,
        payload: { alpha: s.alpha.toString(), beta: s.beta.toString(),
          gamma: s.gamma.toString() } });
      if (!firstWitness) firstWitness = { tick: s.tick,
        kind: "TELESCOPE_FAIL" }; }
    if (s.sigma !== prevSigma) { counts.SPIN_FLIP++;
      note({ kind: "SPIN_FLIP", tick: s.tick,
        payload: { to: s.sigma } }); prevSigma = s.sigma; }
    if (s.n !== prevOrder) { counts.ORDER_ROLLOVER++;
      note({ kind: "ORDER_ROLLOVER", tick: s.tick,
        payload: { order: s.n, orderSize: s.orderSize } });
      prevOrder = s.n; }
    if (s.fold) { counts.PRECISION_FOLD++;
      note({ kind: "PRECISION_FOLD", tick: s.tick,
        payload: { wraps: s.wraps, n: s.lastWrapN, F_after: s.F } }); }
    const row = {
      tick: s.tick, I: s.I, order: s.n, orderSize: s.orderSize,
      F: s.F, F_exact: s.Fexact, ratio: s.ratio, error: s.error,
      sigma: s.sigma, angle: s.angle,
      alpha: s.alpha.toString(), beta: s.beta.toString(),
      gamma: s.gamma.toString(), telescope_ok: s.telescope ? 1 : 0,
      sphere_B: s.B.toString(), spheres: s.spheres, wraps: s.wraps,
      Ireg: s.Ireg, sheetB: s.sheetB, sheetI: s.sheetI.toString(),
      sheetF: s.sheetF, region: s.region,
    };
    ticksCsv.write(LEG_COLS.map((c) => fmt(row[c])).join(",") + "\n");
    err.add(Math.abs(s.error));
    fDrift.add(Math.abs(s.F - s.Fexact) / Math.max(1e-300, s.Fexact || 1));
    ratioDev.add(Math.abs(s.ratio - target));
    gapLaw.add(Math.abs(s.error) * Number(s.I));
    lastRatio = s.ratio;
    if (t % 20000 === 0) console.log(`  ${id}: tick ${t}`);
  }
  ticksCsv.end(); eventsJsonl.end();
  const wallMs = performance.now() - t0;
  writeFileSync(join(dir, "session.json"), JSON.stringify({
    run: id, engine: "legacy (core/piclock.js)", region: cfg.region,
    ticks: cfg.ticks, wallMs: Math.round(wallMs), node: process.version,
    schema_note: "legacy schema: the nested-bif columns do not exist " +
      "on the legacy machine; the Farey-layer lock is measured via " +
      "ratio/error. Events are derived per tick from state changes " +
      "(sigma, order, fold flag, telescope) -- the legacy machine has " +
      "no event stream of its own.",
    final: { I: engine.I.toString(), order: engine.n,
      orderSize: engine.orderSize, F: engine.F,
      F_exact: engine.Fexact, ratio: lastRatio,
      sigma: engine.sigma, spheres: engine.spheres,
      wraps: engine.wraps, B_mask_bits:
        engine.B.toString(2).split("").filter((c) => c === "1").length },
    event_counts: counts,
    farey_lock: { target, error: err.done(),
      gap_law_error_times_I: gapLaw.done(),
      expected_constant: cfg.region === "full" ? 4 * PI : 3 * PI },
    f_accumulation_drift_relative: fDrift.done(),
    ratio_gap_to_target: ratioDev.done(),
    contains_pi: { count: 0, ticks: [], note:
      "not applicable on the legacy machine (no final bracket); " +
      "the Farey layer approaches from below by the exact law" },
    exactness: { telescope_failures: telescopeFails,
      first_witness: firstWitness },
  }, null, 1));
  console.log(`  ${id}: done in ${(wallMs / 1000).toFixed(1)}s, order ` +
    `${engine.order}, wraps ${engine.wraps}, telescope fails ${telescopeFails}`);
}

const which = process.argv[2] || "all";
const list = which === "all" ? Object.keys(RUNS) : [which];
if (!list.every((r) => RUNS[r])) {
  console.error("unknown run:", which); process.exit(1);
}
console.log(`trial runs: ${list.join(" ")}; ` +
  `epoch constants absent (run validity verified at load)`);
for (const id of list) {
  const cfg = RUNS[id];
  if (cfg.engine === "nested") runNested(id, cfg);
  else runLegacy(id, cfg);
}
console.log("all requested runs complete");
