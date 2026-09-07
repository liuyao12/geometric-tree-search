import { embedding } from "../../assets/cyclotomic-five.js";
import { ammannStates } from "../../assets/penrose-ammann.js?v=20260907-settings";

const $ = id => document.getElementById(id);
const canvas = $("tilingCanvas");
const colors = ["#b45338", "#ba8219", "#197a69", "#426fa3", "#88569b"];
let worker = null, snapshot = null, busy = false, running = false, failed = false;
let generation = 0, lastTick = 0, radius = 5, zoom = 1, pan = { x: 0, y: 0 }, showMarking = true;
const drawn = new Map();
function visual(tile) {
  if (!drawn.has(tile.id)) drawn.set(tile.id, {
    points: tile.exactPoints.map(p => embedding(p)),
    states: ammannStates(tile).map(s => ({ start: s.start, bars: s.bars.map(b => ({ family: b.family, from: embedding(b.from), to: embedding(b.to) })) }))
  });
  return drawn.get(tile.id);
}
function paint() {
  const ctx = canvas.getContext("2d"), width = canvas.clientWidth, height = canvas.clientHeight, dpr = devicePixelRatio || 1;
  canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr); ctx.scale(dpr, dpr);
  if (!snapshot) return;
  for (const tile of snapshot.tiles) for (const p of visual(tile).points) radius = Math.max(radius, Math.abs(p.x) + 1, Math.abs(p.y) + 1);
  const scale = Math.min(width, height) / (2 * radius) * zoom;
  const screen = p => ({ x: width / 2 + p.x * scale + pan.x, y: height / 2 + p.y * scale + pan.y });
  const polygon = (tile, fill, stroke, lineWidth = 1) => {
    ctx.beginPath(); visual(tile).points.forEach((p, i) => { const q = screen(p); i ? ctx.lineTo(q.x, q.y) : ctx.moveTo(q.x, q.y); });
    ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); ctx.strokeStyle = stroke; ctx.lineWidth = lineWidth; ctx.stroke();
  };
  const orientations = new Map(snapshot.orientations);
  for (const tile of snapshot.tiles) {
    polygon(tile, tile.kind === "thick" ? "#8ab8a7" : "#e2c779", "#fbfbf5");
    if (showMarking) {
      const view = visual(tile), state = view.states.find(s => s.start === orientations.get(tile.id)) || view.states[0];
      ctx.lineWidth = Number($("stripeWidth").value);
      for (const bar of state.bars) {
        const enforced = !snapshot.useMarkings || bar.family < snapshot.markingDirections;
        ctx.strokeStyle = enforced ? ($("directionColors").checked ? colors[bar.family] : "#643920") : "#8e938b";
        const a = screen(bar.from), b = screen(bar.to); ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      }
    }
  }
  const event = snapshot.event;
  if (event?.tile && ["try", "reject", "remove"].includes(event.type)) polygon(event.tile, event.type === "try" ? "#9c82b55c" : "#e8806244", event.type === "try" ? "#725488" : "#b73e2b", 2);
}
function syncSettings() {
  const enabled = $("useMarkings").checked, count = Number($("markingDirections").value);
  $("markingDirections").disabled = !enabled;
  $("showMarking").textContent = showMarking ? "Hide marking" : "Show marking";
  $("showMarking").setAttribute("aria-pressed", String(showMarking));
  $("directionColors").disabled = !showMarking; $("stripeWidth").disabled = !showMarking;
  $("modeLabel").textContent = enabled ? `Tiling with marking · ${count} direction${count === 1 ? "" : "s"}` : "Tiling without marking";
  $("markingHint").textContent = !enabled
    ? "Marking is not enforced. Visible stripes may fail to line up."
    : count === 5 ? "All five directions enforced. Each rhomb keeps its complete fixed Ammann template."
    : `Weaker experiment: only families 1–${count} are enforced. Other stripes stay on the tiles in gray; this is not the full Ammann rule.`;
}
function render() {
  syncSettings();
  if (snapshot?.done) running = false;
  $("startTiling").textContent = failed ? "Retry" : snapshot?.done ? "Start again" : running ? "Pause" : snapshot && snapshot.stats.proposals ? "Resume tiling" : "Start tiling";
  $("stepTiling").disabled = busy || failed || !snapshot || snapshot.done;
  $("runState").textContent = failed ? "error" : !snapshot ? "initializing" : snapshot.done ? snapshot.status : running ? "searching" : snapshot.stats.proposals ? "paused" : "ready";
  if (snapshot) {
    $("eventLabel").textContent = snapshot.event?.message || "Seed ready";
    for (const [key, value] of Object.entries({ placed: snapshot.tiles.length, peak: snapshot.stats.peak, proposals: snapshot.stats.proposals, backtracks: snapshot.stats.backtracks, markingPrunes: snapshot.stats.markingPrunes })) $(key).textContent = value.toLocaleString();
    $("computeTime").textContent = `${(snapshot.computeMs / 1000).toFixed(2)} s`;
    $("pruneDetail").textContent = `Other prunes: ${snapshot.stats.capacityPrunes} capacity · ${snapshot.stats.geometryPrunes} overlap · ${snapshot.stats.topologyPrunes} boundary`;
    if (snapshot.done) $("statusMessage").textContent = `${snapshot.status}: ${snapshot.tiles.length} tiles after ${snapshot.stats.proposals.toLocaleString()} proposals. Change the marking checkbox and start again to compare from the same seed.`;
  }
  paint();
}
function error(message) {
  failed = true; running = false; busy = false; worker?.terminate(); worker = null;
  $("statusMessage").textContent = message; render();
}
function advance(events) {
  if (!worker || busy || failed || snapshot?.done) return;
  busy = true; $("stepTiling").disabled = true;
  worker.postMessage({ type: "advance", events });
}
function reset(autostart = false) {
  running = false; generation++; const current = generation;
  worker?.terminate(); worker = null; busy = false; failed = false; snapshot = null;
  radius = 5; zoom = 1; pan = { x: 0, y: 0 }; drawn.clear();
  for (const key of ["placed", "peak", "proposals", "backtracks", "markingPrunes"]) $(key).textContent = "0";
  $("computeTime").textContent = "0.00 s"; $("eventLabel").textContent = "One thick-rhomb seed"; $("pruneDetail").textContent = "No proposals yet";
  const options = { useMarkings: $("useMarkings").checked, markingDirections: Number($("markingDirections").value), targetCount: Number($("targetCount").value), nodeLimit: Number($("nodeLimit").value), seed: Number($("shuffleSeed").value) };
  if ($("shuffleSeed").value.trim() === "" || !Number.isSafeInteger(options.seed)) { error("Enter an integer shuffle seed, then retry."); return; }
  $("statusMessage").textContent = "Ready from the seed. Changing marking rules restarts the search; display settings do not.";
  running = autostart; busy = true;
  try { worker = new Worker(new URL("./growth-worker.js?v=20260907-settings", import.meta.url), { type: "module" }); }
  catch (cause) { error(`Cannot start the search worker: ${cause.message}`); return; }
  worker.onmessage = ({ data }) => {
    if (current !== generation) return;
    busy = false;
    if (data.error) { error(data.error); return; }
    snapshot = data; render();
  };
  worker.onerror = event => { if (current === generation) error(`Search worker failed: ${event.message}`); };
  worker.postMessage({ type: "init", options }); render();
}
$("startTiling").addEventListener("click", () => { if (failed || snapshot?.done) return reset(true); running = !running; render(); });
$("stepTiling").addEventListener("click", () => { running = false; advance(1); render(); });
$("resetTiling").addEventListener("click", () => reset());
for (const id of ["useMarkings", "markingDirections", "targetCount", "nodeLimit", "shuffleSeed"]) $(id).addEventListener("change", () => reset());
$("showMarking").addEventListener("click", () => { showMarking = !showMarking; render(); });
for (const id of ["directionColors", "stripeWidth"]) $(id).addEventListener("input", render);
$("fitView").addEventListener("click", () => { radius = 5; zoom = 1; pan = { x: 0, y: 0 }; render(); });
canvas.addEventListener("wheel", event => { event.preventDefault(); zoom = Math.max(.4, Math.min(5, zoom * Math.exp(-event.deltaY * .001))); paint(); }, { passive: false });
let drag;
canvas.addEventListener("pointerdown", e => { drag = { x: e.clientX - pan.x, y: e.clientY - pan.y }; canvas.setPointerCapture(e.pointerId); });
canvas.addEventListener("pointermove", e => { if (drag) { pan = { x: e.clientX - drag.x, y: e.clientY - drag.y }; paint(); } });
for (const name of ["pointerup", "pointercancel", "lostpointercapture"]) canvas.addEventListener(name, () => { drag = null; });
window.addEventListener("resize", paint);
window.addEventListener("pagehide", () => { running = false; worker?.terminate(); worker = null; });
window.addEventListener("pageshow", event => { if (event.persisted) reset(); });
function tick(time) {
  if (running && time - lastTick >= 50) { lastTick = time; advance(Number($("playbackSpeed").value)); }
  requestAnimationFrame(tick);
}
reset(); requestAnimationFrame(tick);
