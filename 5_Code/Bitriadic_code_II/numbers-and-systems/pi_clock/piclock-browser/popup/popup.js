/* popup.js -- the toolbar mini-panel.  Same protocol as the widget:
 * a 'piclock' runtime port; renders snapshots, sends controls. */

(function () {
  "use strict";
  const PI = Math.PI;
  const PI_STR = "3.14159265358979323846";

  const $ = (id) => document.getElementById(id);
  const port = chrome.runtime.connect({ name: "piclock" });
  port.onMessage.addListener(onMessage);
  port.onDisconnect.addListener(() => location.reload());
  port.postMessage({ cmd: "hello" });

  function onMessage(msg) {
    if (msg.type !== "snapshot") return;
    const s = msg.snap;
    const str = s.ratio.toFixed(11);
    let lock = 0;
    while (lock < str.length && str[lock] === PI_STR[lock]) lock++;
    $("bigPi").innerHTML =
      `<span class="lock">${str.slice(0, lock)}</span>` +
      `<span class="free">${str.slice(lock)}</span>`;
    $("lawLine").textContent =
      `error ${s.error >= 0 ? "+" : ""}${s.error.toExponential(2)}` +
      `  = \u22123\u03c0/I  \u00b7  telescope ${s.telescope ? "\u2713" : "\u2717"}`;
    $("vI").textContent = Number(s.I).toLocaleString("en-US");
    $("vN").textContent = `${s.n} \u00b7 ${s.orderSize.toLocaleString("en-US")}`;
    $("vErr").textContent = s.error.toExponential(3);
    $("vSig").textContent =
      `${s.sigma > 0 ? "+1" : "\u22121"} \u00b7 wraps ${s.wraps}`;
    $("btnPlay").textContent = msg.running ? "pause" : "play";
    $("btnSpeed").textContent = "\u00D7" + msg.tps;
  }

  function send(action, extra = {}) {
    port.postMessage({ cmd: "control", action, ...extra });
  }
  $("btnPlay").addEventListener("click", () =>
    send($("btnPlay").textContent === "pause" ? "pause" : "play"));
  $("btnSpeed").addEventListener("click", () => {
    const speeds = [1, 4, 16, 64, 256];
    const cur = speeds.indexOf(parseInt(
      $("btnSpeed").textContent.slice(1), 10));
    send("speed", { tps: speeds[(cur + 1) % speeds.length] });
  });
  $("btnStep").addEventListener("click", () => send("step", { n: 1 }));
  $("btnReset").addEventListener("click", () => send("reset"));
  $("openDemo").addEventListener("click", (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: chrome.runtime.getURL("demo/index.html") });
  });
})();
