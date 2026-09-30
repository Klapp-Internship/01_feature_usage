// Erstellt die anonymisierten README-Screenshots.
// Voraussetzung: App läuft unter http://localhost:8501, Node >= 22, Edge oder Chrome installiert.
//   node docs/make_screenshots.mjs
// Öffnet ein sichtbares Browserfenster, klickt durch die Tabs, führt vor jedem
// Screenshot docs/anonymize.js aus und speichert die Bilder nach docs/.
import { spawn } from "node:child_process";
import { readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const DOCS = dirname(fileURLToPath(import.meta.url));
const URL = process.env.APP_URL || "http://localhost:8501/feature_usage";
const PORT = 9333;
const BROWSER = process.env.BROWSER_EXE ||
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const ANON = readFileSync(join(DOCS, "anonymize.js"), "utf8");
const WIDTH = 1440, SCALE = 1.5;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = spawn(BROWSER, [
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "shots-"))}`,
  "--no-first-run", "--new-window", `--window-size=${WIDTH},1000`, URL,
], { stdio: "ignore" });

let targets = [];
for (let i = 0; i < 40 && !targets.some((t) => t.type === "page"); i++) {
  await sleep(500);
  targets = await fetch(`http://127.0.0.1:${PORT}/json`).then((r) => r.json()).catch(() => []);
}
const page = targets.find((t) => t.type === "page" && t.url.includes("localhost"))
  ?? targets.find((t) => t.type === "page");
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));

let seq = 0;
const pending = new Map();
ws.addEventListener("message", (e) => {
  const msg = JSON.parse(e.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
});
const send = (method, params = {}) => new Promise((resolve, reject) => {
  const id = ++seq;
  pending.set(id, (m) => (m.error ? reject(new Error(m.error.message)) : resolve(m.result)));
  ws.send(JSON.stringify({ id, method, params }));
});
const js = async (expression) =>
  (await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true })).result.value;
const waitFor = async (expression, timeout = 20000) => {
  for (const t0 = Date.now(); Date.now() - t0 < timeout; await sleep(300)) if (await js(expression)) return;
  throw new Error(`Timeout: ${expression}`);
};
const click = async (x, y) => {
  for (const type of ["mousePressed", "mouseReleased"])
    await send("Input.dispatchMouseEvent", { type, x, y, button: "left", clickCount: 1 });
};
const openTab = (name) => js(`[...document.querySelectorAll('[role=tab]')]
  .find(b => b.innerText.includes(${JSON.stringify(name)})).click()`);
const viewport = (height) => send("Emulation.setDeviceMetricsOverride",
  { width: WIDTH, height, deviceScaleFactor: SCALE, mobile: false });

async function shot(file, height) {
  await viewport(height);
  await sleep(2500); // Plotly/Grid neu zeichnen lassen
  console.log(file, await js(ANON));
  await sleep(600);
  const { data } = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(DOCS, file), Buffer.from(data, "base64"));
}

await send("Page.enable");
await send("Runtime.enable");
await viewport(1000);
await waitFor(`!!document.querySelector('[data-testid="stDataFrame"] canvas')`);
await sleep(2000);

// 1) Gesamtübersicht
await shot("overview.png", 1000);

// 2) Feature-Analyse
await openTab("Feature-Analyse");
await waitFor(`[...document.querySelectorAll('.js-plotly-plot')].some(p => p.offsetParent)`);
await shot("feature_view.png", 1150);

// 3) Schule im Detail: Demo-Schule über die Suche in der Übersicht auswählen
await viewport(1000);
await openTab("Gesamtübersicht");
await sleep(1000);
await js(`(() => {
  const input = document.querySelector('input[aria-label="Suchfeld"]');
  input.focus(); input.select();
})()`);
await send("Input.insertText", { text: process.env.DEMO_SCHOOL || "Musterschule" });
await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Enter", code: "Enter", windowsVirtualKeyCode: 13 });
await sleep(2500);
const cell = await js(`(() => {
  const c = [...document.querySelectorAll('[data-testid="stDataFrame"] canvas')]
    .find(c => c.getBoundingClientRect().height < 60).getBoundingClientRect();
  return { x: c.left + 22, y: c.bottom + 17 };
})()`);
await click(cell.x, cell.y);
await sleep(2000);
await openTab("Schule im Detail");
await waitFor(`[...document.querySelectorAll('.js-plotly-plot')].some(p => p.offsetParent)`);
await shot("detailed_view.png", 2250);

// 4) Übrige Features
await openTab("Übrige Features");
await sleep(2000);
await shot("other_features.png", 1000);

ws.close();
browser.kill();
console.log("fertig");
