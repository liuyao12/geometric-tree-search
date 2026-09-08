import { embedding } from "../../assets/cyclotomic-five.js";
import { tileStates } from "../../assets/penrose-mixed-markings.js?v=20260907-frontier";

import { arrowStates } from "../../assets/penrose-arrows.js?v=20260907-extent";

import { inspectionPoints, inspectionText, formatCyclotomic } from "./point-inspection.js?v=20260907-contacts";

import { extendBar } from "../../assets/penrose-extensions.js?v=20260907-extent";

import { activityText } from "./search-status.js?v=20260907-activity";

const $ = id => document.getElementById(id);
const canvas = $("tilingCanvas");
const tileKinds = ["thick", "thin", "kite", "dart", "p5", "p3", "p2", "diamond", "boat", "star"];
const selectedKinds = () => tileKinds.filter(kind => $("tile_" + kind).checked);
const tileColors = { thick: "#8ab8a7", thin: "#e2c779", kite: "#82b4c9", dart: "#be99c6", p5: "#d9a4ac", p3: "#d6b4d3", p2: "#b5b3d9", diamond: "#e5c28e", boat: "#a9c6a2", star: "#e1ab83" };
const colors = ["#b45338", "#ba8219", "#197a69", "#426fa3", "#88569b"];
let worker = null, snapshot = null, busy = false, running = false, failed = false;
let coronaTarget = 3;
let generation = 0, lastTick = 0, radius = 5, zoom = 1, pan = { x: 0, y: 0 }, showMarking = false;
const drawn = new Map();
let candidateContacts = null, contactKey = null, pendingContactKey = null;
let pointer = null, inspectKey = null, inspectPoints = [], drag;
function currentContactKey() { return snapshot ? snapshot.tiles.map(t=>t.id).join(";") + "/" + $("extent").value : null; }
function requestContacts() {
  if (!snapshot || !worker || busy || running || !showMarking || $("pointDensity").value === "none") return;
  const key=currentContactKey();if(key===contactKey || pendingContactKey) return;
  pendingContactKey=key;worker.postMessage({type:"inspect",key,extent:Number($("extent").value)});
}
function hideInspection() { $("pointTooltip").hidden = true; }
function inspect(ctx, screen) {
  const key = snapshot.tiles.map(t => t.id).join(";") + JSON.stringify(snapshot.orientations) + "/" + $("extent").value + "/" + $("pointDensity").value + "/" + showMarking + "/" + (contactKey || "");
  if (key !== inspectKey) { inspectKey = key; inspectPoints = inspectionPoints({ ...snapshot, extent: Number($("extent").value) }, { contacts: showMarking && $("pointDensity").value !== "none" && contactKey === currentContactKey() ? candidateContacts : null, integersOnly: $("pointDensity").value === "integers" }); }
  let nearest = null, distance = 12;
  for (const point of inspectPoints) {
    if (!point.vertex && (!showMarking || $("pointDensity").value === "none")) continue;
    const p = screen(point.position);
    // Small vertex dots make the exact support discoverable in either view.
    ctx.fillStyle = point.vertex ? "#34483f" : point.conflict ? "#b73e2b" : point.candidateContacts ? "#426fa3" : "#643920";
    ctx.beginPath(); ctx.arc(p.x, p.y, point.vertex ? 2.1 : point.candidateContacts ? 1.8 : 1.5, 0, 2 * Math.PI); ctx.fill();
    if (pointer && !drag) {
      const d = Math.hypot(pointer.x - p.x, pointer.y - p.y);
      if (d < distance) { distance = d; nearest = point; }
    }
  }
  if (!nearest) { hideInspection(); return; }
  const p = screen(nearest.position);
  ctx.strokeStyle = "#19695b"; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(p.x, p.y, 6, 0, 2 * Math.PI); ctx.stroke();
  const text = inspectionText(nearest, snapshot.useMarkings);
  for (const [key, value] of Object.entries(text)) $("point_" + key).textContent = value;
  $("pointTooltip").hidden = false;
}
function visual(tile) {
  const key = tile.id + "/" + $("extent").value;
  if (!drawn.has(key)) drawn.set(key, {
    points: tile.exactPoints.map(p => embedding(p)),
    arrows: (!snapshot?.mixed && tile.arrowStart !== undefined ? [arrowStates(tile).find(s => s.start === tile.arrowStart)] : tile.bars ? [{start: 0, arrows: []}] : arrowStates(tile)).map(s => ({ start: s.start, arrows: s.arrows.map(a => ({ type: a.type, from: embedding(a.from), to: embedding(a.to) })) })),
    states: tileStates(tile).map(s => ({ start: s.start, bars: s.bars.map(b => { const e = extendBar(b, Number($("extent").value)); return { family: b.family, from: embedding(b.from), to: embedding(b.to), extFrom: embedding(e.from), extTo: embedding(e.to) }; }) }))
  });
  return drawn.get(key);
}
function paint() {
  const ctx = canvas.getContext("2d"), width = canvas.clientWidth, height = canvas.clientHeight, dpr = devicePixelRatio || 1;
  canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr); ctx.scale(dpr, dpr);
  if (!snapshot) { hideInspection(); return; }
  for (const tile of snapshot.tiles) for (const p of visual(tile).points) radius = Math.max(radius, Math.abs(p.x) + 1, Math.abs(p.y) + 1);
  if (showMarking) for (const tile of snapshot.tiles) for (const state of visual(tile).states) for (const bar of state.bars) {
    for (const p of [bar.extFrom, bar.extTo]) radius = Math.max(radius, Math.abs(p.x) + .5, Math.abs(p.y) + .5);
  }
  const scale = Math.min(width, height) / (2 * radius) * zoom;
  const screen = p => ({ x: width / 2 + p.x * scale + pan.x, y: height / 2 + p.y * scale + pan.y });
  const polygon = (tile, fill, stroke, lineWidth = 1) => {
    ctx.beginPath(); visual(tile).points.forEach((p, i) => { const q = screen(p); i ? ctx.lineTo(q.x, q.y) : ctx.moveTo(q.x, q.y); });
    ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); ctx.strokeStyle = stroke; ctx.lineWidth = lineWidth; ctx.stroke();
  };
  const orientations = new Map(snapshot.orientations);
  for (const tile of snapshot.tiles) {
    polygon(tile, tileColors[tile.kind], "#fbfbf5");
    if (showMarking) {
      const view = visual(tile), state = view.states.find(s => s.start === orientations.get(tile.id)) || view.states[0];
      ctx.lineWidth = Number($("stripeWidth").value);
      for (const bar of state.bars) {
        const highlighted = bar.family < Number($("markingDirections").value);
        ctx.strokeStyle = highlighted ? ($("directionColors").checked ? colors[bar.family] : "#643920") : "#8e938b";
        const a = screen(bar.from), b = screen(bar.to); ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      }
    } else {
      if (tile.bars && (snapshot.mixed || tile.arrowStart === undefined)) {
        const state = tileStates(tile)[0];
        for (const bar of state.bars) for (const end of bar.ends) {
          const p = screen(embedding(end.point)); ctx.fillStyle = colors[bar.family];
          ctx.beginPath(); ctx.arc(p.x, p.y, 2.5, 0, 2 * Math.PI); ctx.fill();
        }
      }
      const states = visual(tile).arrows, state = states.find(s => s.start === orientations.get(tile.id)) || states[0];
      ctx.strokeStyle = "#34483f"; ctx.lineWidth = 1.4;
      for (const arrow of state.arrows) {
        const a = screen(arrow.from), b = screen(arrow.to), dx = b.x - a.x, dy = b.y - a.y;
        const length = Math.hypot(dx, dy), ux = dx / length, uy = dy / length;
        const size = Math.min(4, length * .13);
        for (let n = 0; n < arrow.type; n++) {
          const offset = (n - (arrow.type - 1) / 2) * size * 1.3;
          const x = (a.x + b.x) / 2 + ux * offset, y = (a.y + b.y) / 2 + uy * offset;
          ctx.beginPath(); ctx.moveTo(x - ux * size - uy * size * .65, y - uy * size + ux * size * .65);
          ctx.lineTo(x, y); ctx.lineTo(x - ux * size + uy * size * .65, y - uy * size - ux * size * .65); ctx.stroke();
        }
      }
    }
  }
  if (showMarking && Number($("extent").value)) {
    ctx.setLineDash([3, 4]); ctx.globalAlpha = .42; ctx.lineWidth = Number($("stripeWidth").value);
    for (const tile of snapshot.tiles) {
      const view = visual(tile), state = view.states.find(s => s.start === orientations.get(tile.id)) || view.states[0];
      for (const bar of state.bars) {
        ctx.strokeStyle = $("directionColors").checked ? colors[bar.family] : "#643920";
        for (const [from, to] of [[bar.extFrom, bar.from], [bar.to, bar.extTo]]) {
          const a = screen(from), b = screen(to); ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
    }
    ctx.setLineDash([]); ctx.globalAlpha = 1;
  }
  const event = snapshot.event;
  if (event?.tile && ["try", "reject", "remove"].includes(event.type)) polygon(event.tile, event.type === "try" ? "#9c82b55c" : "#e8806244", event.type === "try" ? "#725488" : "#b73e2b", 2);
  inspect(ctx, screen);
}
function syncSettings() {
  const enabled = $("useMarkings").checked;
  const selected = selectedKinds(), classic = selected.length > 0 && selected.every(k => k === "thick" || k === "thin");
  $("tileHint").textContent = selected.length === 0 ? "Choose at least one tile."
    : selected.some(k => ["p5", "p3", "p2", "diamond", "boat", "star"].includes(k)) && selected.some(k => ["thick", "thin", "kite", "dart"].includes(k))
    ? "Allowed tiles, not required tiles. Shared construction scale: P1 edges cannot join P2/P3 by a whole edge."
    : "Selected tiles are allowed, not required. Mixed sets are an experiment in local compatibility.";
  $("pointDensity").disabled = !showMarking;
  $("extentValue").textContent = $("extent").value + "×";
  $("markingDirections").disabled = !showMarking;
  $("showMarking").textContent = showMarking ? (classic ? "Show edge arrows" : "Show edge decorations") : "Show Ammann bars";
  $("showMarking").setAttribute("aria-pressed", String(showMarking));
  $("directionColors").disabled = !showMarking; $("stripeWidth").disabled = !showMarking;
  $("matchingPrunesLabel").textContent = enabled ? "Ammann prunes" : "edge prunes";
  $("modeLabel").textContent = enabled ? "Ammann matching · no explicit edge check" : classic ? "Explicit Penrose edge-arrow matching" : "Explicit edge-decoration matching";
  $("markingHint").textContent = enabled
    ? `All five directions enforced · extent ${$("extent").value}× per stripe end. Overlapping extensions must agree; no edge-arrow predicate is called.`
    : classic ? "Single/double arrows must agree in type and direction on shared edges. Ammann bars are not checked."
    : "Colored edge ports must agree in position and direction on shared edges. Extended bars are not checked.";
}
function render() {
  syncSettings();
  if (snapshot?.done) running = false;
  $("startTiling").textContent = failed ? "Retry" : snapshot?.done ? "Start again" : running ? "Pause" : snapshot?.stats.proposals ? "Continue" : "Run";
  $("stepTiling").disabled = busy || failed || !snapshot || snapshot.done;
  if (!failed) {
    const corona = snapshot?.minimumFrontierGeneration ?? 0;
    const activity = activityText(snapshot?.activity, key => {
      const [coeff, denominator] = key.split("/");
      return formatCyclotomic({ coeff: coeff.split(",").map(Number), denominator: Number(denominator) });
    });
    $("statusMessage").textContent = !snapshot ? "initializing"
      : snapshot.done ? `${snapshot.status} · corona ${corona}`
      : running ? (activity === "ready" ? "tiling" : activity)
      : snapshot.pausedCorona != null ? `${activity === "ready" ? "" : activity + " · "}pausing at corona ${snapshot.pausedCorona}`
      : snapshot.stats.proposals ? `${activity === "ready" ? "" : activity + " · "}paused at corona ${corona}` : "ready";
  }
  if (snapshot) {
    $("eventLabel").textContent = snapshot.event?.message || "Seed ready";
    for (const [key, value] of Object.entries({ placed: snapshot.tiles.length, peak: snapshot.stats.peak, proposals: snapshot.stats.proposals, backtracks: snapshot.stats.backtracks, markingPrunes: snapshot.useMarkings ? snapshot.stats.markingPrunes : snapshot.stats.edgePrunes })) $(key).textContent = value.toLocaleString();
    $("computeTime").textContent = `${(snapshot.computeMs / 1000).toFixed(2)} s`;
    $("graphDetail").textContent = snapshot.graph ? `${snapshot.graph.points} unfinished points · ${snapshot.graph.candidates} candidates · ${snapshot.graph.incidences} incidences · ${snapshot.stats.forcedMoves} forced placements · ${snapshot.stats.branches} branches` : "";
    $("pruneDetail").textContent = `Prunes: ${snapshot.stats.edgePrunes} edge matches · ${snapshot.stats.capacityPrunes} capacity · ${snapshot.stats.geometryPrunes} overlap · ${snapshot.stats.topologyPrunes} boundary`;
  }
  paint(); requestContacts();
}
function error(message) {
  failed = true; running = false; busy = false; worker?.terminate(); worker = null;
  $("statusMessage").textContent = message; render();
}
function advance(events) {
  if (!worker || busy || failed || snapshot?.done) return;
  busy = true; $("stepTiling").disabled = true;
  worker.postMessage({ type: "advance", events, targetCorona: coronaTarget });
}
function reset(autostart = false) {
  running = false; coronaTarget = 3; generation++; const current = generation;
  worker?.terminate(); worker = null; busy = false; failed = false; snapshot = null;
  radius = 5; zoom = 1; pan = { x: 0, y: 0 }; drawn.clear();
  candidateContacts = null; contactKey = null; pendingContactKey = null;
  pointer = null; inspectKey = null; inspectPoints = []; hideInspection();
  for (const key of ["placed", "peak", "proposals", "backtracks", "markingPrunes"]) $(key).textContent = "0";
  $("graphDetail").textContent = ""; $("computeTime").textContent = "0.00 s"; $("eventLabel").textContent = "Seed ready"; $("pruneDetail").textContent = "No proposals yet";
  const options = { tileKinds: selectedKinds(), useMarkings: $("useMarkings").checked, extent: Number($("extent").value), targetCount: null, nodeLimit: 100000, seed: 17 };
  if (!options.tileKinds.length) { error("Choose at least one tile"); return; }
  $("statusMessage").textContent = "ready";
  running = autostart; busy = true;
  try { worker = new Worker(new URL("./growth-worker.js?v=20260907-contacts", import.meta.url), { type: "module" }); }
  catch (cause) { error(`Cannot start the search worker: ${cause.message}`); return; }
  worker.onmessage = ({ data }) => {
    if (current !== generation) return;
    if (data.type === "inspection") {
      pendingContactKey=null;
      if (data.key === currentContactKey()) { contactKey=data.key; candidateContacts=data.contacts || null; inspectKey=null; }
      render(); if (data.error) $("eventLabel").textContent = `Candidate contacts unavailable: ${data.error}`; return;
    }
    busy = false;
    if (data.error) { error(data.error); return; }
    snapshot = data;
    if (contactKey !== currentContactKey()) { candidateContacts=null; contactKey=null; }
    if (data.pausedCorona !== null && data.pausedCorona !== undefined) {
      running = false; coronaTarget = data.pausedCorona + 2;
    }
    render();
  };
  worker.onerror = event => { if (current === generation) error(`Search worker failed: ${event.message}`); };
  worker.postMessage({ type: "init", options }); render();
}
$("startTiling").addEventListener("click", () => { if (failed || snapshot?.done) return reset(true); running = !running; render(); });
$("stepTiling").addEventListener("click", () => { running = false; advance(1); render(); });
$("resetTiling").addEventListener("click", () => reset());
$("useMarkings").addEventListener("change", () => reset());
$("showMarking").addEventListener("click", () => { showMarking = !showMarking; render(); });
$("extent").addEventListener("input", () => {
  drawn.clear(); inspectKey = null;
  if ($("useMarkings").checked) reset(); else render();
});
$("pointDensity").addEventListener("change", () => { inspectKey = null; render(); });
$("markingDirections").addEventListener("change", render);
for (const id of ["directionColors", "stripeWidth"]) $(id).addEventListener("input", render);
$("fitView").addEventListener("click", () => { radius = 5; zoom = 1; pan = { x: 0, y: 0 }; render(); });
canvas.addEventListener("wheel", event => { event.preventDefault(); zoom = Math.max(.4, Math.min(5, zoom * Math.exp(-event.deltaY * .001))); paint(); }, { passive: false });
canvas.addEventListener("pointerdown", e => { drag = { x: e.clientX - pan.x, y: e.clientY - pan.y }; canvas.setPointerCapture(e.pointerId); hideInspection(); });
canvas.addEventListener("pointermove", e => {
  const rect = canvas.getBoundingClientRect(); pointer = { x: e.clientX - rect.left, y: e.clientY - rect.top };
  if (drag) pan = { x: e.clientX - drag.x, y: e.clientY - drag.y };
  paint();
});
canvas.addEventListener("pointerleave", () => { pointer = null; hideInspection(); paint(); });
for (const name of ["pointerup", "pointercancel", "lostpointercapture"]) canvas.addEventListener(name, () => { drag = null; });
window.addEventListener("resize", paint);
window.addEventListener("pagehide", () => { running = false; worker?.terminate(); worker = null; });
window.addEventListener("pageshow", event => { if (event.persisted) reset(); });
function tick(time) {
  if (running && time - lastTick >= 50) { lastTick = time; advance(200); }
  requestAnimationFrame(tick);
}
reset(); requestAnimationFrame(tick);

for (const kind of tileKinds) $("tile_" + kind).addEventListener("change", () => { $("tileSet").value = "custom"; reset(); });
$("tileSet").addEventListener("change", () => {
  const sets = { P3: ["thick", "thin"], P2: ["kite", "dart"], P1: ["p5", "p3", "p2", "diamond", "boat", "star"], all: tileKinds };
  if (!sets[$("tileSet").value]) return;
  for (const kind of tileKinds) $("tile_" + kind).checked = sets[$("tileSet").value].includes(kind);
  reset();
});
