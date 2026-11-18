/* t12_injection.mjs -- T12: the precision fold, injection test.
 * Injects F just below the 2^52 boundary at a live tick, ticks once,
 * and captures the pre/post state.  No engine code is modified; the
 * register is set through its public field, exactly as a unit test
 * would.  Writes results/t12_injection.json. */
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const ROOT = "/home/z/my-project/download/piclock-browser/";
globalThis.globalThis = globalThis;
for (const f of ["core/rational.js", "core/piclock.js", "core/nestedbif.js"])
  eval(readFileSync(join(ROOT, f), "utf8"));

const PI = Math.PI;
const engine = new PiLock.NestedBifClock({});
for (let k = 0; k < 100; k++) engine.tick();   // a live state, I = 100

// pre-fold reference values (the exact layer and the value bif)
const Ipre = Number(engine.I);
const FexPre = (PI / 2) * (Ipre - 3);
const LFPre = 2 * FexPre / Ipre;

// inject F = 2^52 - 1 (eps = 1 < pi/2, so one increment crosses).
// A CONTROL TWIN runs the same tick without injection: the per-tick
// change of the law (I advances 100 -> 101) is thereby held constant,
// and any remaining difference is the fold's effect alone.
engine.F = 2 ** 52 - 1;
const twin = PiLock.NestedBifClock.fromJSON(JSON.parse(
  JSON.stringify(((() => { const t = new PiLock.NestedBifClock({});
    for (let k = 0; k < 100; k++) t.tick(); return t; })()).toJSON())));
const snapTwin = twin.tick();                   // same tick, no fold
const snap = engine.tick();                     // the fold fires inside

const Ipost = Number(engine.I);
const FexPost = snap.Fexact;
const LFPost = snap.L_F;
const foldEvents = engine.history
  .filter((e) => e.type === "PRECISION_FOLD")
  .map((e) => ({ tick: e.tick, wraps: e.wraps, n: e.n, F_after: e.F_after }));

const ratioDev = Math.abs(LFPost / snapTwin.L_F - 1);
const out = {
  trial: "T12 precision fold (injection, twin-controlled)",
  hypothesis: "the fold at 2^52 preserves the exact layer: F wraps, " +
    "F_exact and the value bif are bit-for-bit what the same tick " +
    "produces WITHOUT the fold",
  injected_state: {
    tick_B: snap.B, I: 100, F_injected: 2 ** 52 - 1,
    epsilon: 1, boundary: 2 ** 52,
    note: "F set through the public register at a live state (I = 100); " +
      "a twin engine runs the identical tick un-folded" },
  post_fold_state: {
    fold_fired: snap.precisionFold === true,
    twin_folded: snapTwin.precisionFold === false,
    wraps: engine.wraps, n_removed: engine.lastWrapN,
    F_wrapped: engine.F, F_in_unit_interval:
      engine.F >= 0 && engine.F < 2 * PI,
    F_exact_folded: FexPost, F_exact_twin: snapTwin.Fexact,
    F_exact_bitwise_identical: FexPost === snapTwin.Fexact,
    L_F_folded: LFPost, L_F_twin: snapTwin.L_F,
    L_F_bitwise_identical: LFPost === snapTwin.L_F,
    ratio_preservation_relative_deviation: ratioDev,
    law_check_deviation: Math.abs(
      LFPost / (PI * (Ipost - 3) / Ipost) - 1),
    ratio_preserved_to_1e_minus_12: ratioDev < 1e-12,
    events: foldEvents },
  verdict: (snap.precisionFold === true && snapTwin.precisionFold === false
    && FexPost === snapTwin.Fexact && LFPost === snapTwin.L_F
    && engine.F < 2 * PI && engine.lastWrapN ===
      Math.floor((2 ** 52 - 1 + PI / 2) / (2 * PI)))
    ? "EST-CONFIRMED"
    : "FAILED",
  expected_wrap_n: Math.floor((2 ** 52 - 1 + PI / 2) / (2 * PI)),
  note: "no live run reaches the boundary (I ~ 2.9e15 ticks); " +
    "this trial is injection-only by design. The naive pre/post " +
    "comparison FAILS by construction: the tick itself advances I, " +
    "so F_exact changes lawfully by (pi/2) per tick; the twin " +
    "isolates the fold's effect (recorded as a trial note, the " +
    "first run of this test measured the lawful 3.1e-4 per-tick " +
    "change and misread it as fold damage).",
};
writeFileSync(join(ROOT, "results", "t12_injection.json"),
  JSON.stringify(out, null, 1));
console.log(JSON.stringify(out, null, 1));
