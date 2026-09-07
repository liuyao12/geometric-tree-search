import { embedding } from "../../assets/cyclotomic-five.js";
import { ammannStates } from "../../assets/penrose-ammann.js";

const $ = id => document.getElementById(id);
const lanes = ["plain", "marked"].map((id, i) => ({ id, useMarkings: Boolean(i), canvas: $(`${id}Canvas`), worker: null, busy: false, snapshot: null }));
let running = false, generation = 0, lastTick = 0, radius = 5, zoom = 1, pan = { x: 0, y: 0 };
const drawn = new Map();
function visual(tile) {
  if (!drawn.has(tile.id)) drawn.set(tile.id, { points: tile.exactPoints.map(p => embedding(p)),
    states: ammannStates(tile).map(s => ({ start: s.start, bars: s.bars.map(b => [embedding(b.from), embedding(b.to)]) })) });
  return drawn.get(tile.id);
}
function paint(lane) {
  const c = lane.canvas, ctx = c.getContext("2d"), width = c.clientWidth, height = c.clientHeight, dpr = devicePixelRatio || 1;
  c.width = Math.round(width * dpr); c.height = Math.round(height * dpr); ctx.scale(dpr, dpr);
  if (!lane.snapshot) return;
  const scale = Math.min(width, height) / (2 * radius) * zoom;
  const screen = p => ({ x: width / 2 + p.x * scale + pan.x, y: height / 2 + p.y * scale + pan.y });
  const polygon = (tile, fill, stroke, lineWidth = 1) => {
    ctx.beginPath(); visual(tile).points.forEach((p, i) => { const q = screen(p); i ? ctx.lineTo(q.x, q.y) : ctx.moveTo(q.x, q.y); });
    ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); ctx.strokeStyle = stroke; ctx.lineWidth = lineWidth; ctx.stroke();
  };
  const orientations = new Map(lane.snapshot.orientations);
  for (const tile of lane.snapshot.tiles) {
    polygon(tile, tile.kind === "thick" ? "#8ab8a7" : "#e2c779", "#fbfbf5");
    if ($("showStripes").checked) {
      const view = visual(tile), state = view.states.find(s => s.start === orientations.get(tile.id)) || view.states[0];
      ctx.strokeStyle = "#643920"; ctx.lineWidth = 1.4;
      for (const [a, b] of state.bars) { const p = screen(a), q = screen(b); ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke(); }
    }
  }
  const event = lane.snapshot.event;
  if (event?.tile && ["try", "reject", "remove"].includes(event.type)) polygon(event.tile, event.type === "try" ? "#9c82b55c" : "#e8806244", event.type === "try" ? "#725488" : "#b73e2b", 2);
}
function render() {
  for (const lane of lanes) for (const tile of lane.snapshot?.tiles || []) for (const p of visual(tile).points) radius = Math.max(radius, Math.abs(p.x) + 1, Math.abs(p.y) + 1);
  for (const lane of lanes) {
    const s = lane.snapshot; if (!s) continue;
    $(`${lane.id}Status`).textContent = s.done ? s.status : running ? "searching" : "paused";
    $(`${lane.id}Event`).textContent = s.event?.message || "Seed ready";
    for (const [key, value] of Object.entries({ placed: s.tiles.length, proposals: s.stats.proposals, backtracks: s.stats.backtracks, peak: s.stats.peak })) $(`${lane.id}-${key}`).textContent = value.toLocaleString();
    $(`${lane.id}Prunes`).textContent = `Pruned: ${s.stats.capacityPrunes} capacity · ${s.stats.geometryPrunes} overlap · ${s.stats.topologyPrunes} boundary · ${s.stats.markingPrunes} marking`;
    paint(lane);
  }
  const allDone = lanes.every(lane => lane.snapshot?.done);
  if (allDone) running = false;
  $("compareRun").textContent = allDone ? "Run again" : running ? "Pause" : "Run both";
  if (allDone) $("comparisonSummary").textContent = lanes.map(l => `${l.useMarkings ? "With markings" : "Without markings"}: ${l.snapshot.status}, ${l.snapshot.tiles.length} tiles, ${l.snapshot.stats.proposals.toLocaleString()} proposals`).join(". ") + ". A finite patch is not a proof of infinite tiling.";
}
function advance(events) {
  for (const lane of lanes) if (lane.worker && !lane.busy && !lane.snapshot?.done) { lane.busy = true; lane.worker.postMessage({ type: "advance", events }); }
}
function reset(autostart = false) {
  const targetCount = Number($("compareTarget").value), nodeLimit = Number($("compareBudget").value), seed = Number($("compareSeed").value);
  if (!Number.isSafeInteger(seed)) { $("comparisonSummary").textContent = "Enter an integer shuffle seed."; return; }
  running = autostart; generation++; const current = generation; radius = 5; zoom = 1; pan = { x: 0, y: 0 }; drawn.clear();
  $("comparisonSummary").textContent = "Both searches use the same seed rhomb, candidate ordering, geometry checks, target, and proposal budget. Only marking enforcement differs.";
  for (const lane of lanes) {
    lane.worker?.terminate(); lane.snapshot = null; lane.busy = true;
    lane.worker = new Worker(new URL("./growth-worker.js?v=20260907-comparison", import.meta.url), { type: "module" });
    lane.worker.onmessage = ({ data }) => {
      if (current !== generation) return;
      lane.busy = false;
      if (data.error) { running = false; $(`${lane.id}Status`).textContent = "error"; $("comparisonSummary").textContent = data.error; return; }
      lane.snapshot = data; render();
    };
    lane.worker.onerror = event => { if (current !== generation) return; running = false; lane.busy = false; $(`${lane.id}Status`).textContent = "error"; $("comparisonSummary").textContent = `Search worker failed: ${event.message}`; };
    lane.worker.postMessage({ type: "init", options: { useMarkings: lane.useMarkings, targetCount, nodeLimit, seed } });
  }
  $("compareRun").textContent = running ? "Pause" : "Run both";
}
$("compareRun").addEventListener("click", () => { if (lanes.every(l => l.snapshot?.done)) return reset(true); running = !running; render(); });
$("compareStep").addEventListener("click", () => { running = false; advance(1); render(); });
$("compareReset").addEventListener("click", () => reset());
for (const id of ["compareTarget", "compareBudget", "compareSeed"]) $(id).addEventListener("change", () => reset());
$("showStripes").addEventListener("change", render);
for (const lane of lanes) {
  lane.canvas.addEventListener("wheel", event => { event.preventDefault(); zoom = Math.max(.4, Math.min(5, zoom * Math.exp(-event.deltaY * .001))); render(); }, { passive: false });
  let drag;
  lane.canvas.addEventListener("pointerdown", e => { drag = { x: e.clientX - pan.x, y: e.clientY - pan.y }; lane.canvas.setPointerCapture(e.pointerId); });
  lane.canvas.addEventListener("pointermove", e => { if (drag) { pan = { x: e.clientX - drag.x, y: e.clientY - drag.y }; render(); } });
  for (const name of ["pointerup", "pointercancel", "lostpointercapture"]) lane.canvas.addEventListener(name, () => { drag = null; });
}
window.addEventListener("resize", render);
window.addEventListener("pagehide", () => lanes.forEach(l => l.worker?.terminate()));
function tick(time) {
  if (running && time - lastTick >= 50) { lastTick = time; advance(Number($("compareSpeed").value)); }
  requestAnimationFrame(tick);
}
reset(); requestAnimationFrame(tick);
