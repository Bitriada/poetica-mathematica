#!/usr/bin/env node
/* Cross-check the Nested-Bif pi-clock engine (core/nestedbif.js)
 * against the authoritative Python reference
 * (assets/nested_bif_reference.json), plus engine invariants.
 *
 * Exact fields (BigInt/integers): B, I, m, n, order, orderSize,
 * sigma, phaseAngle, alpha, beta, gamma, telescope, ledger, ghost,
 * containsPi, bindsL, bindsU, fraction, history events.
 * Double fields (trig/pi_est chains may differ by ulps between V8
 * and CPython libm): compared with relative tolerance 1e-12.
 *
 *   node scripts/nested_bif_harness.mjs
 */

import { readFileSync } from "node:fs";

const ROOT = "/home/z/my-project/download/piclock-browser";

globalThis.globalThis = globalThis;
(0, eval)(readFileSync(`${ROOT}/core/rational.js`, "utf8"));
(0, eval)(readFileSync(`${ROOT}/core/piclock.js`, "utf8"));
(0, eval)(readFileSync(`${ROOT}/core/nestedbif.js`, "utf8"));

const { NestedBifClock, Rat } = globalThis.PiLock;
const ref = JSON.parse(
  readFileSync(`${ROOT}/assets/nested_bif_reference.json`, "utf8"));

let pass = 0, fail = 0;
function check(name, ok, detail = "") {
  if (ok) pass++;
  else { fail++; console.log(`  FAIL  ${name}  ${detail}`); }
}

const EXACT_INT = ["B", "I", "m", "n", "order", "orderSize", "sigma",
  "phaseAngle", "alpha", "beta", "gamma", "flipsOuter", "flipsSpin",
  "rolls", "wraps", "lastWrapN"];
const EXACT_LIST = ["ledger", "fraction"];
const EXACT_STR = ["sheetOuter", "bindsL", "bindsU"];
const DOUBLES = ["piEst", "F", "Fexact", "L_B", "U_B", "L_i", "U_i",
  "L_f", "U_f",
  "L_F", "U_F", "L_outer", "U_outer", "L_final", "U_final",
  "gapB", "gapI", "gapF", "gapFF", "balance"];
const TOL = 1e-12;

function closeEnough(a, b) {
  if (typeof a !== "number" || typeof b !== "number") return a === b;
  if (!Number.isFinite(a) || !Number.isFinite(b)) return a === b;
  if (a === b) return true;
  const s = Math.max(Math.abs(a), Math.abs(b));
  return Math.abs(a - b) <= TOL * s;
}

// -- 1. tick-for-tick cross-check vs Python --------------------------
console.log("[1] tick-for-tick vs Python reference (400 ticks)");
{
  const clk = new NestedBifClock({});
  let mismatches = 0;
  for (let k = 0; k < ref.ticks.length; k++) {
    const s = clk.tick();
    const e = ref.ticks[k];
    for (const f of EXACT_INT)
      if (s[f] !== e[f]) { mismatches++;
        if (mismatches < 6) console.log(`    tick ${k + 1} ${f}: ${s[f]} != ${e[f]}`); }
    for (const f of EXACT_LIST)
      if (JSON.stringify(s[f]) !== JSON.stringify(e[f])) { mismatches++;
        if (mismatches < 6) console.log(`    tick ${k + 1} ${f}: ${s[f]} != ${e[f]}`); }
    for (const f of EXACT_STR)
      if (s[f] !== e[f]) { mismatches++;
        if (mismatches < 6) console.log(`    tick ${k + 1} ${f}: ${s[f]} != ${e[f]}`); }
    for (const f of DOUBLES)
      if (!closeEnough(s[f], e[f])) { mismatches++;
        if (mismatches < 6) console.log(`    tick ${k + 1} ${f}: ${s[f]} != ${e[f]}`); }
    if (s.telescope !== e.telescope || s.containsPi !== e.containsPi
        || s.warn !== e.warn) { mismatches++;
      if (mismatches < 6) console.log(`    tick ${k + 1} bool divergence`); }
  }
  check("400 ticks match Python (all fields)", mismatches === 0,
    `${mismatches} field mismatches`);
}

// -- 2. the history events match -------------------------------------
console.log("[2] phase history (flips + warnings) vs Python");
{
  const clk = new NestedBifClock({});
  for (let k = 0; k < ref.ticks.length; k++) clk.tick();
  const ev = clk.history.filter(
    (e) => e.type !== "WARN_BALANCE" && e.type !== "WARN_CLEAR");
  const refEv = ref.history.filter(
    (e) => e.type !== "WARN_BALANCE" && e.type !== "WARN_CLEAR");
  check("event count (flips + rolls + folds)", ev.length === refEv.length,
    `${ev.length} != ${refEv.length}`);
  // every ORDER_ROLL lands on the right order/size/phi
  const rolls = ev.filter((e) => e.type === "ORDER_ROLL");
  const refRolls = refEv.filter((e) => e.type === "ORDER_ROLL");
  check("ORDER_ROLL events identical (order/size/phi/tick)",
    rolls.length === refRolls.length && rolls.every((r, k) =>
      r.tick === refRolls[k].tick && r.order === refRolls[k].order
      && r.orderSize === refRolls[k].orderSize
      && r.phi === refRolls[k].phi),
    `${rolls.length} rolls vs ${refRolls.length}`);
  let ok = ev.length === refEv.length;
  for (let k = 0; k < Math.min(ev.length, refEv.length); k++) {
    const a = ev[k], b = refEv[k];
    if (a.type !== b.type || a.tick !== b.tick || a.to !== b.to
        || a.from !== b.from) ok = false;
    if (a.type === "OUTER_FLIP"
        && JSON.stringify(a.annihilated) !== JSON.stringify(b.annihilated))
      ok = false;
  }
  check("flip events identical (type/tick/from/to/annihilated)", ok);
  const warns = clk.history.filter((e) => e.type === "WARN_BALANCE");
  const refWarns = ref.history.filter((e) => e.type === "WARN_BALANCE");
  check("warn rising-edge events identical",
    warns.length === refWarns.length
    && warns.every((w, k) => w.tick === refWarns[k].tick),
    `${JSON.stringify(warns.map((w) => w.tick))} vs ${JSON.stringify(refWarns.map((w) => w.tick))}`);
}

// -- 3. engine invariants --------------------------------------------
console.log("[3] engine invariants");
{
  const clk = new NestedBifClock({});
  for (let k = 0; k < 2000; k++) clk.tick();
  // R1: I is transfinite, equals B; order consistent with |F_order|
  check("I === B (transfinite, no reset)", clk.I === clk.B);
  check("order rollover: |F_order| >= I",
    clk.orderSize >= Number(clk.I),
    `order=${clk.order} size=${clk.orderSize} I=${clk.I}`);
  const prevSize = clk.sieve.fareySize(clk.order - 1);
  check("order minimal: |F_{order-1}| < I", prevSize < Number(clk.I));
  // telescope at every state
  check("telescope alpha+beta+gamma = 0",
    clk.alpha + clk.beta + clk.gamma === 0n);
  check("alpha = B - m, beta = m - n, gamma = n - B",
    clk.alpha === clk.B - clk.m && clk.beta === clk.m - clk.n
    && clk.gamma === clk.n - clk.B);
  // sigma cadence: flips every 3rd tick (120 deg per tick)
  const sigmaFlips = clk.history.filter((e) => e.type === "SPIN_FLIP");
  const cadence = sigmaFlips.every(
    (e, k) => e.tick === 3 * (k + 1));
  check("spin flips at ticks 3, 6, 9, ... (120 deg/tick)", cadence,
    `first: ${sigmaFlips.slice(0, 3).map((e) => e.tick)}`);
  check("sigma = (-1)^(angle/360 parity)",
    clk.sigma === (Math.floor(clk.phaseAngle / 360) % 2 === 0 ? 1 : -1));
  // exact Leibniz: S_hi - S_lo = 4/(4m+3) exactly, and values vs Fraction
  const mN = Number(clk.m);
  check("exact gap identity S_hi - S_lo = 4/(4m+3)",
    (clk.numHi - clk.numLo) * BigInt(4 * mN + 3) === 4n * clk.den);
  const S_hi = new Rat(clk.numHi, clk.den);
  const S_lo = new Rat(clk.numLo, clk.den);
  const refHi = Rat.parse(ref.deep_final.S_hi);
  const refLo = Rat.parse(ref.deep_final.S_lo);
  check("deep S_hi value == Python Fraction",
    S_hi.mul(refHi).eq(new Rat(1n)) === false
      ? S_hi.n * refHi.d === refHi.n * S_hi.d : true,
    "");
  check("deep S_lo value == Python Fraction",
    S_lo.n * refLo.d === refLo.n * S_lo.d);
  // balancer targets
  const I = Number(clk.I);
  const tm = Math.floor(I / (3 * Math.PI));
  const tn = Math.max(3, Math.floor(Math.sqrt(Math.PI * Math.PI * I / 6)));
  check("balancer: m == floor(I/(3pi))", Number(clk.m) === tm,
    `${clk.m} != ${tm}`);
  check("balancer: n == max(3, floor(sqrt(pi^2 I/6)))",
    Number(clk.n) === tn, `${clk.n} != ${tn}`);
  // the exact Farey law, live: L_F = 2F/I = pi(1 - 3/I)
  const s = clk.tick();
  const lawErr = Math.abs(s.L_F - Math.PI * (s.I - 3) / s.I);
  check("Farey value-bif law L_F = pi(1-3/I)", lawErr < 1e-12,
    `err=${lawErr}`);
  check("U_F = pi (the membrane)", s.U_F === Math.PI);
  // log ring
  check("tick log ring bounded by logCap",
    clk.tickLog.length <= clk.logCap && clk.tickLog.length > 0);
}

// -- 4. deep run vs Python (2000 ticks, sparse) -----------------------
console.log("[4] deep run vs Python (I = 2000)");
{
  const clk = new NestedBifClock({});
  for (let k = 0; k < 2000; k++) clk.tick();
  const d = ref.deep_final;
  check("deep: I, m, n, order",
    Number(clk.I) === d.I && Number(clk.m) === d.m
    && Number(clk.n) === d.n && clk.order === d.order,
    `I=${clk.I}/${d.I} m=${clk.m}/${d.m} n=${clk.n}/${d.n}`);
  check("deep: ledger + ghost exact",
    JSON.stringify(clk.ledger.map(Number)) === JSON.stringify(d.ledger)
    && Number(clk.ghost) === d.ghost,
    `${clk.ledger.map(Number)} vs ${d.ledger}; ghost ${clk.ghost}/${d.ghost}`);
  check("deep: flip counters",
    clk.flipsOuter === d.flipsOuter && clk.flipsSpin === d.flipsSpin,
    `${clk.flipsOuter}/${d.flipsOuter} ${clk.flipsSpin}/${d.flipsSpin}`);
  check("deep: pi_est and F within tolerance",
    closeEnough(clk.piEst, d.piEst) && closeEnough(clk.F, d.F),
    `${clk.piEst} vs ${d.piEst}`);
  // sparse snapshots
  const last = clk.tickLog[clk.tickLog.length - 1];
  const refLast = ref.sparse[ref.sparse.length - 1];
  check("deep: final snapshot fields match",
    last.B === refLast.B && last.alpha === refLast.alpha
    && last.telescope === refLast.telescope
    && closeEnough(last.balance, refLast.balance));
}

// -- 5. exact Leibniz vs fractions.Fraction at sample m --------------
console.log("[5] exact Leibniz sums (shared-denominator, no big-gcd)");
{
  const clk = new NestedBifClock({});
  // S_1 = 4, S_2 = 8/3 at m = 0 (initial state)
  check("initial S_hi = 4 (S_1)",
    new Rat(clk.numHi, clk.den).eq(new Rat(4n)));
  check("initial S_lo = 8/3 (S_2)",
    new Rat(clk.numLo, clk.den).eq(new Rat(8n, 3n)));
  // advance to m = 10 and verify against exact recomputation
  clk._advanceLeibniz(10n);
  const ten = { hi: new Rat(clk.numHi, clk.den),
                lo: new Rat(clk.numLo, clk.den) };
  let hi = new Rat(4n), lo = new Rat(8n, 3n), mm = 0n;
  while (mm < 10n) {
    hi = lo.add(new Rat(4n, 4n * mm + 5n));
    lo = hi.sub(new Rat(4n, 4n * mm + 7n));
    mm += 1n;
  }
  check("S_hi(10) == exact Rat recomputation", ten.hi.eq(hi),
    `${ten.hi} != ${hi}`);
  check("S_lo(10) == exact Rat recomputation", ten.lo.eq(lo));
  // doubles are sane (S_lo < pi < S_hi, gap ~ 4/(4m+3))
  const dh = clk.S_hi_value, dl = clk.S_lo_value;
  check("Leibniz straddles pi at m=10",
    dl < Math.PI && Math.PI < dh);
  check("Leibniz double gap ~= 4/(4m+3)",
    Math.abs((dh - dl) - 4 / 43) < 1e-12);
}

// -- 6. log/history caps ----------------------------------------------
console.log("[6b] serialization round-trip (catch-up capability)");
{
  const a = new NestedBifClock({ threshold: 10 });
  for (let k = 0; k < 777; k++) a.tick();
  // kill -> persist -> restart
  const json = JSON.parse(JSON.stringify(a.toJSON()));
  const b = NestedBifClock.fromJSON(json);
  check("restore: registers",
    b.B === a.B && b.m === a.m && b.n === a.n && b.I === a.I
    && b.order === a.order && b.orderSize === a.orderSize
    && b.F === a.F && b.piEst === a.piEst && b.sigma === a.sigma
    && b.phaseAngle === a.phaseAngle && b.sheetOuter === a.sheetOuter);
  check("restore: exact Leibniz layer",
    b.den === a.den && b.numHi === a.numHi && b.numLo === a.numLo);
  check("restore: trinumeral + counters",
    b.alpha === a.alpha && b.beta === a.beta && b.gamma === a.gamma
    && b.ledger.every((x, e) => x === a.ledger[e]) && b.ghost === a.ghost
    && b.flipsOuter === a.flipsOuter && b.flipsSpin === a.flipsSpin
    && b.rolls === a.rolls && b.wraps === a.wraps
    && b.balanceWarns === a.balanceWarns);
  check("restore: history carried", b.history.length === a.history.length);
  check("restore: tracker position",
    b.tracker.order === a.tracker.order
    && b.tracker.position === a.tracker.position
    && b.tracker.walker.position === a.tracker.walker.position
    && b.tracker.walker.a === a.tracker.walker.a);
  // continuation identical, tick for tick
  let same = true, firstBad = -1;
  for (let k = 0; k < 123; k++) {
    const s1 = a.tick(), s2 = b.tick();
    for (const key of Object.keys(s1)) {
      if (typeof s1[key] === "number" ? s1[key] !== s2[key]
          : String(s1[key]) !== String(s2[key])) {
        same = false; firstBad = k; break;
      }
    }
    if (!same) break;
  }
  check("catch-up: 123 post-restart ticks identical", same,
    firstBad >= 0 ? `first diff at +${firstBad}` : "");
}

console.log("[6] logging (ring buffers, caps)");
{
  const clk = new NestedBifClock({ logCap: 100, maxHistory: 60 });
  for (let k = 0; k < 500; k++) clk.tick();
  check("tick log capped at 100", clk.tickLog.length === 100);
  check("logDropped counted", clk.logDropped === 400);
  check("history capped", clk.history.length <= 60);
  check("recentHistory returns newest",
    clk.recentHistory(3)[2].tick >= clk.recentHistory(3)[0].tick);
  // snapshots are JSON-able (the export path)
  const j = JSON.parse(JSON.stringify(clk.tickLog[0]));
  check("snapshot JSON round-trip", j.B === clk.tickLog[0].B
    && typeof j.S_hi_exact[0] === "string");
}

// -- 7b. the precision fold (2^52 boundary) ---------------------------
console.log("[7b] the precision fold (2^52, the numerical boundary)");
{
  const clk = new NestedBifClock({});
  for (let k = 0; k < 1000; k++) clk.tick();
  check("no fold below the bound in 1000 ticks",
    clk.wraps === 0 && clk.F <= 2 ** 52);
  check("F tracks the exact layer before any fold",
    Math.abs(clk.F - (Math.PI / 2) * (Number(clk.I) - 3))
      <= 1e-9 * Math.PI / 2 * Number(clk.I));
  // synthetic injection: force F past the boundary
  clk.F = 2 ** 52 + 100;
  const before = clk.wraps;
  const s = clk.tick();
  check("PRECISION_FOLD fires past 2^52",
    s.precisionFold === true && clk.wraps === before + 1,
    `wraps=${clk.wraps}`);
  check("F wrapped into [0, 2pi)", clk.F >= 0 && clk.F < 2 * Math.PI,
    `F=${clk.F}`);
  const expectN = Math.floor((2 ** 52 + 100 + Math.PI / 2) / (2 * Math.PI));
  check("wrap count n = floor(F/2pi)", clk.lastWrapN === expectN);
  const evt = clk.history.filter((e) => e.type === "PRECISION_FOLD").pop();
  check("PRECISION_FOLD event recorded",
    !!evt && evt.tick === s.B && evt.n === expectN && evt.wraps === clk.wraps);
  // the value bif reads the exact layer: L_F unaffected by the wrap
  const lawErr = Math.abs(s.L_F - Math.PI * (s.I - 3) / s.I);
  check("value bif unaffected (L_F from F_exact)", lawErr < 1e-12,
    `err=${lawErr}`);
  const s2 = clk.tick();
  check("no immediate refold", s2.precisionFold === false);
}

// -- 7. the tracking diagnosis (R4) ----------------------------------
console.log("[7] R4 dynamics (honest surfacing)");
{
  const clk = new NestedBifClock({});
  let contained = 0, detachedAt = -1;
  for (let k = 0; k < 400; k++) {
    const s = clk.tick();
    if (s.containsPi) contained++;
    else if (detachedAt < 0) detachedAt = s.B;
  }
  check("final bracket contains pi on the early ticks",
    contained > 0, `contained=${contained}`);
  check("final bracket detaches below pi (B-scheme tracking, R4)",
    detachedAt > 0 && detachedAt <= 10, `detached at tick ${detachedAt}`);
  check("outer bracket stays non-inverted (L_outer <= U_outer)",
    clk.tickLog.every((s) => s.L_outer <= s.U_outer));
  check("U_final <= pi always (the membrane bounds from above)",
    clk.tickLog.every((s) => s.U_final <= Math.PI + 1e-15));
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
