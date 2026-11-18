/* background.js -- the MV3 service worker: the single owner of the
 * pi-clock machine.
 *
 * Architecture (Path 2, WebExtensions):
 *   - this worker owns the PiClock (exact BigInt machine, core/piclock.js
 *     loaded via importScripts);
 *   - a setInterval drives live ticks while the worker is alive; the
 *     machine state persists to chrome.storage.local and every wake
 *     (onStartup / onConnect / onAlarm) CATCHES UP deterministically
 *     from the stored wall-clock timestamp -- the clock keeps running
 *     across service-worker restarts and tab closes, with no drift
 *     (the machine is pure: state -> tick());
 *   - a chrome.alarms keepalive (30 s) bounds each catch-up batch;
 *   - widgets in tabs and the toolbar popup connect on a runtime port
 *     ('piclock') and receive (B, I, F, error, ...) snapshots at 10 fps;
 *     control messages (play / pause / step / speed / reset) flow back.
 */

importScripts("core/rational.js", "core/piclock.js");

const STORE_KEY = "piclock.state.v1";
const BROADCAST_MS = 100;          // 10 fps to the widgets
const PERSIST_MS = 1000;
const MAX_CATCHUP = 200000;        // ticks per wake (deterministic)
const SPEEDS = [1, 4, 16, 64, 256];

const S = {
  clock: null,          // PiLock.PiClock
  tracker: null,        // FractionTracker (display-side Farey walk)
  sieve: null,          // TotientSieve (asset-loaded)
  running: false,
  tps: 4,               // ticks per second
  lastWall: 0,
  fracAcc: 0,           // fractional tick accumulator
  ports: new Set(),
  lastPersist: 0,
  timer: null,
};

// ---------------------------------------------------------------- sieve
async function loadSieve() {
  try {
    const url = chrome.runtime.getURL("assets/totients.bin");
    const buf = await (await fetch(url)).arrayBuffer();
    return new PiLock.TotientSieve(new Uint32Array(buf));
  } catch (e) {
    return new PiLock.TotientSieve(4096);   // computed fallback
  }
}

// ---------------------------------------------------------------- state
async function persist(force = false) {
  const now = Date.now();
  if (!force && now - S.lastPersist < PERSIST_MS) return;
  S.lastPersist = now;
  S.lastWall = now;
  await chrome.storage.local.set({
    [STORE_KEY]: {
      machine: S.clock.toJSON(),
      running: S.running,
      tps: S.tps,
      lastWall: S.lastWall,
    },
  });
}

async function restore() {
  const got = await chrome.storage.local.get(STORE_KEY);
  const saved = got[STORE_KEY];
  if (saved && saved.machine) {
    S.clock = PiLock.PiClock.fromJSON(saved.machine, S.sieve);
    S.running = !!saved.running;
    S.tps = saved.tps || 4;
    S.lastWall = saved.lastWall || Date.now();
    // deterministic catch-up: the machine is pure, so the elapsed
    // wall time converts exactly into ticks
    if (S.running) {
      const due = Math.floor((Date.now() - S.lastWall) / 1000 * S.tps);
      for (let k = 0; k < Math.min(due, MAX_CATCHUP); k++) S.clock.tick();
    }
  } else {
    S.clock = new PiLock.PiClock({ region: "half", value: "1/10",
                                   sieve: S.sieve });
    S.running = true;
    S.tps = 4;
  }
  S.tracker = new PiLock.FractionTracker(S.sieve);
  S.lastWall = Date.now();
  S.fracAcc = 0;
}

// ---------------------------------------------------------------- loop
function broadcast() {
  if (S.ports.size === 0) return;
  const snap = PiLock.serializeSnapshot(S.clock.snapshot());
  snap.fraction = S.tracker.sync(S.clock.n, S.clock.I)
    .map(String);
  const msg = { type: "snapshot", snap, running: S.running, tps: S.tps,
                speeds: SPEEDS };
  for (const p of S.ports) {
    try { p.postMessage(msg); } catch (e) { S.ports.delete(p); }
  }
}

function startLoop() {
  if (S.timer) clearInterval(S.timer);
  S.timer = setInterval(async () => {
    const now = Date.now();
    const dt = (now - S.lastWall) / 1000;
    S.lastWall = now;
    if (S.running && dt >= 0) {
      S.fracAcc += dt * S.tps;
      const due = Math.floor(S.fracAcc);
      S.fracAcc -= due;
      const capped = Math.min(due, MAX_CATCHUP);
      for (let k = 0; k < capped; k++) S.clock.tick();
      if (due > capped) S.fracAcc = 0;      // refuse runaway
    }
    await persist();
    broadcast();
  }, BROADCAST_MS);
}

// ---------------------------------------------------------------- ports
chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== "piclock") return;
  S.ports.add(port);
  port.onMessage.addListener(async (m) => {
    if (m.cmd === "control") {
      if (m.action === "play") S.running = true;
      else if (m.action === "pause") { S.running = false; }
      else if (m.action === "speed") {
        S.tps = SPEEDS.includes(m.tps) ? m.tps : 4;
      } else if (m.action === "step") {
        const n = Math.max(1, Math.min(m.n || 1, 10000));
        for (let k = 0; k < n; k++) S.clock.tick();
      } else if (m.action === "reset") {
        S.clock = new PiLock.PiClock({ region: "half",
          value: m.value || "1/10", sieve: S.sieve });
        S.tracker = new PiLock.FractionTracker(S.sieve);
        S.running = true;
      }
      S.lastWall = Date.now(); S.fracAcc = 0;
      await persist(true);
      broadcast();
    } else if (m.cmd === "hello") {
      broadcast();
    }
  });
  port.onDisconnect.addListener(() => S.ports.delete(port));
});

// ---------------------------------------------------------------- wake
chrome.alarms.create("piclock-keepalive", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener(async (a) => {
  if (a.name === "piclock-keepalive") {
    // wake the worker: the interval loop resumes and the deterministic
    // catch-up in restore()/persist timing keeps the clock advancing
  }
});

chrome.runtime.onStartup.addListener(() => { /* handled in main() */ });
chrome.runtime.onInstalled.addListener(() => { /* handled in main() */ });

// ---------------------------------------------------------------- main
(async function main() {
  S.sieve = await loadSieve();
  await restore();
  startLoop();
  broadcast();
})();
