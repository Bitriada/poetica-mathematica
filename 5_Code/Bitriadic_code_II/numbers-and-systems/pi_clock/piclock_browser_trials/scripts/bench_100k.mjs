/* bench_100k.mjs -- pre-trial timing probe: can we run 100k ticks of
 * each engine in reasonable time?  Measures the snapshot cost
 * (S_hi_exact.toString on huge BigInts) separately from raw ticks. */
import { readFileSync } from "node:fs";

const base = "/home/z/my-project/download/piclock-browser/";
globalThis.globalThis = globalThis;
for (const f of ["core/rational.js", "core/piclock.js", "core/nestedbif.js"])
  eval(readFileSync(base + f, "utf8"));

function bench(name, ticks, fn) {
  const t0 = performance.now();
  const extra = fn();
  const ms = performance.now() - t0;
  console.log(`${name}: ${ticks} ticks in ${(ms / 1000).toFixed(2)}s ` +
    `(${Math.round(ticks / (ms / 1000)).toLocaleString("en-US")} t/s) ${extra || ""}`);
}

// raw engine ticks (snapshot included -- that IS the engine API).
// Small ring: the trials RUNNER streams tick() returns; holding 100k
// snapshots with 20k-digit S_exact strings is what OOMs.
const clk = new PiLock.NestedBifClock({ logCap: 64 });
bench("nested-bif first 10k", 10000, () => {
  for (let k = 0; k < 10000; k++) clk.tick();
  return `den digits: ${clk.den.toString().length}, ring drops: ${clk.logDropped}`;
});
bench("nested-bif to 100k", 90000, () => {
  for (let k = 0; k < 90000; k++) clk.tick();
  return `den digits: ${clk.den.toString().length}, m=${clk.m}, n=${clk.n}, order=${clk.order}`;
});

// snapshot at depth: how expensive is one S_exact string pair now?
{
  const t = performance.now();
  for (let k = 0; k < 100; k++) clk.tick();
  console.log(`per-tick at B~100k: ${((performance.now() - t) / 100).toFixed(2)}ms`);
}

// legacy 100k
const leg = new PiLock.PiClock({});
bench("legacy 100k", 100000, () => {
  for (let k = 0; k < 100000; k++) leg.tick();
  return `I=${leg.I}, order=${leg.n}, F=${leg.F.toExponential(3)}, wraps=${leg.wraps}`;
});

// serialize cost at depth (for R-F design)
const t1 = performance.now();
const json = JSON.stringify(clk.toJSON ? clk.toJSON() : "no-toJSON");
console.log(`toJSON at B=100k: ${(performance.now() - t1).toFixed(0)}ms, ` +
  `${(json.length / 1e6).toFixed(1)}MB (exists: ${clk.toJSON !== undefined})`);
