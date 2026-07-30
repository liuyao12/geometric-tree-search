import { MAX_VALUE, PENROSE_CATALOG, deriveP2Model, exactToPoint, makePenroseModelSet, makeSelectedTileSearch, makeUniversalVertexAtlas, pointTotals } from "../../assets/penrose-model-set.js";
import { benchmarkGCTSPruning, learnPenroseGCTS, markingForTile } from "../../assets/penrose-gcts-marking.js";

const $ = id => document.getElementById(id);
const canvas = $("canvas");
const ctx = canvas.getContext("2d");
const windowCanvas = $("windowCanvas");
const windowCtx = windowCanvas.getContext("2d");
let model;
let atlas;
let trace = [];
let cursor = 0;
let active = [];
let trial = null;
let rollback = null;
let running = true;
let nodes = 0;
let backtracks = 0;
let lastFrame = 0;
let camera = { x: 0, y: 0, zoom: 1 };
let dragging = false;
let dragStart = null;
let learnedMarking = null;
let activeFamily = "P3";
let selectionDirty = false;
let searchSolved = false;
let searchStopped = false;
const selectedCatalog = new Set(["p3-thick", "p3-thin"]);

function resize(target, context) {
  const ratio = devicePixelRatio || 1;
  const width = target.clientWidth || target.width;
  const height = target.clientHeight || target.height;
  if (target.width !== Math.round(width * ratio) || target.height !== Math.round(height * ratio)) {
    target.width = Math.round(width * ratio);
    target.height = Math.round(height * ratio);
  }
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  return { width, height };
}

function transformScreenPoint(point, width, height) {
  const scale = Math.min(width, height) / (model.radius * 2.18) * camera.zoom;
  return {
    x: width / 2 + point.x * scale + camera.x,
    y: height / 2 + point.y * scale + camera.y
  };
}

function transform(exact, width, height) {
  return transformScreenPoint(exactToPoint(exact), width, height);
}

function drawTile(tile, width, height, fill, stroke, lineWidth = 1) {
  ctx.beginPath();
  tile.exactPoints.forEach((point, index) => {
    const p = transform(point, width, height);
    index ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y);
  });
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.strokeStyle = stroke;
  ctx.lineWidth = lineWidth;
  ctx.stroke();
}

function catalogEntryFor(tile, index = 0) {
  if (tile.presentation === "P2" || tile.presentation === "P3") {
    return PENROSE_CATALOG.find(entry =>
      entry.id === `${tile.presentation.toLowerCase()}-${tile.kind}` &&
      selectedCatalog.has(entry.id)
    ) || null;
  }
  const choices = PENROSE_CATALOG.filter(entry => selectedCatalog.has(entry.id) && entry.accepts.includes(tile.kind));
  return choices.length ? choices[index % choices.length] : null;
}

function drawCatalogBadge(tile, entry, width, height) {
  if (!entry || entry.family !== "P1" || camera.zoom < .72) return;
  const p = transform(tile.centerExact, width, height);
  ctx.beginPath();
  ctx.arc(p.x, p.y, 5.6, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(248,247,242,.88)";
  ctx.fill();
  ctx.fillStyle = entry.color;
  ctx.font = "800 7px ui-sans-serif,system-ui";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(entry.short, p.x, p.y + .2);
}

function drawAtlas(width, height) {
  if (!$("atlasToggle").checked || !atlas?.points) return;
  ctx.save();
  for (const site of atlas.points) {
    const p = transform(site.exact, width, height);
    if (p.x < -3 || p.y < -3 || p.x > width + 3 || p.y > height + 3) continue;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 1.15, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(35,73,65,.17)";
    ctx.fill();
  }
  ctx.restore();
}

function drawPoints(width, height) {
  if (!$("pointsToggle").checked) return;
  const totals = pointTotals(active);
  const visible = new Map();
  active.forEach(tile => tile.vertices.forEach((id, index) => {
    if (!visible.has(id)) visible.set(id, tile.exactPoints[index]);
  }));
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  visible.forEach((point, id) => {
    const value = totals.get(id) || 0;
    const p = transform(point, width, height);
    const radius = value === MAX_VALUE ? 5.5 : 4;
    ctx.beginPath();
    ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = value === MAX_VALUE ? "#126f68" : "rgba(248,247,242,.92)";
    ctx.fill();
    ctx.strokeStyle = value === MAX_VALUE ? "#fff" : "#6e7772";
    ctx.lineWidth = 1;
    ctx.stroke();
    if (camera.zoom > .76) {
      ctx.fillStyle = value === MAX_VALUE ? "#fff" : "#43504b";
      ctx.font = "700 7px ui-monospace,monospace";
      ctx.fillText(String(value), p.x, p.y + .3);
    }
  });
}

function drawLearnedMarking(width, height) {
  if (!learnedMarking || model.presentation !== "P3" || !$("markingToggle").checked) return;
  ctx.save();
  if ($("barsToggle").checked) {
    ctx.setLineDash([4, 3]);
    ctx.lineWidth = 1.35;
    for (const tile of active) {
      const marking = markingForTile(tile, learnedMarking);
      for (const bar of marking.bars) {
        const from = transform(bar.from, width, height), to = transform(bar.to, width, height);
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);
        ctx.strokeStyle = `${bar.color}bb`;
        ctx.stroke();
      }
    }
    ctx.setLineDash([]);
  }
  for (const tile of active) {
    const marking = markingForTile(tile, learnedMarking);
    for (const edge of marking.edges) {
      const port = transform(edge.port, width, height);
      ctx.beginPath();
      ctx.arc(port.x, port.y, 2.2, 0, Math.PI * 2);
      ctx.fillStyle = edge.color;
      ctx.fill();
      ctx.strokeStyle = "rgba(255,255,255,.9)";
      ctx.lineWidth = .7;
      ctx.stroke();
    }
  }
  ctx.restore();
}

function drawWindow() {
  const { width, height } = resize(windowCanvas, windowCtx);
  windowCtx.clearRect(0, 0, width, height);
  const center = { x: width / 2, y: height / 2 };
  const radius = Math.min(width, height) * .37;
  windowCtx.beginPath();
  for (let i = 0; i < 10; i++) {
    const angle = -Math.PI / 2 + i * Math.PI / 5;
    const r = radius * (i % 2 ? .82 : 1);
    const x = center.x + Math.cos(angle) * r;
    const y = center.y + Math.sin(angle) * r;
    i ? windowCtx.lineTo(x, y) : windowCtx.moveTo(x, y);
  }
  windowCtx.closePath();
  windowCtx.fillStyle = "rgba(94,182,167,.15)";
  windowCtx.fill();
  windowCtx.strokeStyle = "#126f68";
  windowCtx.stroke();
  const phase = Number($("phaseInput").value) / 100;
  for (let i = 0; i < 78; i++) {
    const angle = i * 2.399963 + phase * 8;
    const r = radius * .92 * Math.sqrt((i + .5) / 78);
    windowCtx.beginPath();
    windowCtx.arc(center.x + Math.cos(angle) * r, center.y + Math.sin(angle) * r, 1.25, 0, Math.PI * 2);
    windowCtx.fillStyle = i < active.length / 3 ? "#126f68" : "rgba(52,67,61,.28)";
    windowCtx.fill();
  }
}

function draw() {
  const { width, height } = resize(canvas, ctx);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#e8e6dd";
  ctx.fillRect(0, 0, width, height);
  drawAtlas(width, height);
  active.forEach((tile, index) => {
    const entry = catalogEntryFor(tile, index);
    const fallback = tile.kind === "thick" ? "#5eb6a7" :
      tile.kind === "thin" ? "#d7ab42" :
      tile.kind === "kite" ? "#4c8fbd" : "#8b7eab";
    drawTile(tile, width, height, entry ? `${entry.color}dd` : `${fallback}66`, "rgba(248,247,242,.93)", 1);
    drawCatalogBadge(tile, entry, width, height);
  });
  if (trial) drawTile(trial, width, height, "rgba(139,126,171,.62)", "#655681", 2.4);
  if (rollback) drawTile(rollback, width, height, "rgba(238,118,93,.58)", "#bc4936", 3);
  drawLearnedMarking(width, height);
  drawPoints(width, height);
  drawWindow();
}

function updateMetrics() {
  const totals = pointTotals(active);
  const saturated = [...totals.values()].filter(value => value === MAX_VALUE).length;
  $("atlasMetric").textContent = (atlas?.points.length || 0).toLocaleString();
  $("placedMetric").textContent = active.length.toLocaleString();
  $("nodesMetric").textContent = nodes.toLocaleString();
  $("backtrackMetric").textContent = backtracks.toLocaleString();
  $("saturatedMetric").textContent = saturated.toLocaleString();
  const progress = trace.length ? cursor / trace.length * 100 : 0;
  $("timelineFill").style.width = `${progress}%`;
  $("timelineHead").style.left = `${progress}%`;
}

function applyEvent() {
  if (!trace.length) return;
  if (cursor >= trace.length) {
    running = false;
    $("runButton").textContent = "Replay selected set";
    $("runState").textContent = "complete";
    $("runState").parentElement.classList.add("paused");
    $("eventLabel").textContent = searchSolved
      ? "selected catalog completed the exact-cover patch"
      : searchStopped ? "node limit reached before completion" : "selected catalog exhausted · no completion";
    $("status").textContent = searchSolved
      ? `Completed ${active.length} selected tiles with ${backtracks} visible rollbacks.`
      : `No completion for this selected catalog in the current exact patch; ${backtracks} branches rolled back.`;
    return;
  }
  const event = trace[cursor++];
  const eventEntry = catalogEntryFor(event.tile, active.length);
  nodes++;
  trial = null;
  rollback = null;
  if (event.type === "try" || event.type === "reject" || event.type === "witness") trial = event.tile;
  if (event.type === "add") {
    active.push(event.tile);
    if (event.speculative) trial = event.tile;
  }
  if (event.type === "remove") {
    active = active.filter(tile => tile.id !== event.tile.id);
    rollback = event.tile;
    backtracks++;
  }
  const compiledLabel = eventEntry ? ` · ${eventEntry.family} ${eventEntry.name}` : " · no selected proposal";
  $("eventLabel").textContent = `${event.message}${compiledLabel}`;
  $("status").textContent = `Node ${nodes}: ${event.type.toUpperCase()} · exact ${event.tile.kind} tile${compiledLabel}`;
  updateMetrics();
  if (model) draw();
}

function rebuild(autostart = true) {
  const target = Number($("targetInput").value);
  const phaseCode = Number($("phaseInput").value) * 10;
  const radius = Math.max(10, Math.ceil(target / 30) + 7);
  const fixedSeed = makeUniversalVertexAtlas({ radius, phaseCode, samples: 1 });
  const p3Model = fixedSeed.base;
  const p2Model = deriveP2Model(p3Model);
  const search = makeSelectedTileSearch({
    p3Model,
    p2Model,
    selectedIds: selectedCatalog,
    preferredFamily: activeFamily,
    targetCount: target
  });
  model = search.model;
  trace = search.trace;
  searchSolved = search.success;
  searchStopped = search.stopped;
  atlas = {
    points: model.vertices.map(vertex => ({ exact: vertex.exact })),
    presentation: model.presentation
  };
  active = [];
  cursor = 0;
  nodes = 0;
  backtracks = 0;
  trial = null;
  rollback = null;
  const canRun = trace.length > 0;
  running = autostart && canRun;
  selectionDirty = false;
  $("runButton").textContent = running ? "Pause trace" : "Run selected set";
  $("runState").textContent = running ? "running" : canRun ? "ready" : "empty catalog";
  $("runState").parentElement.classList.toggle("paused", !running);
  $("presentationLabel").textContent = model.presentation === "P2+P3"
    ? "LIVE SEARCH / MIXED P2+P3 EXACT ATOMS"
    : model.presentation === "P2"
      ? "LIVE SEARCH / EXACT P2 KITES + DARTS"
      : "LIVE SEARCH / EXACT P3 RHOMBS";
  $("eventLabel").textContent = `${model.presentation} exact candidates compiled · ${search.universeAtoms} common atoms`;
  $("status").textContent = canRun
    ? `${selectedCatalog.size} selected prototiles compile to ${model.tiles.length.toLocaleString()} exact placements; ${atlas.points.length.toLocaleString()} reachable support points.`
    : "No implemented prototile is selected. Choose tiles, then run.";
  updateMetrics();
  draw();
}

function animate(time) {
  const speed = Number($("speedInput").value);
  const interval = 520 - speed * 4.75;
  if (running && time - lastFrame > interval) {
    applyEvent();
    lastFrame = time;
  }
  requestAnimationFrame(animate);
}

$("runButton").addEventListener("click", () => {
  if (selectionDirty || cursor >= trace.length) return rebuild(true);
  running = !running;
  $("runButton").textContent = running ? "Pause trace" : "Resume trace";
  $("runState").textContent = running ? "running" : "paused";
  $("runState").parentElement.classList.toggle("paused", !running);
});
$("stepButton").addEventListener("click", () => {
  if (selectionDirty) rebuild(false);
  running = false;
  applyEvent();
  $("runButton").textContent = "Resume trace";
  $("runState").textContent = "paused";
  $("runState").parentElement.classList.add("paused");
});
$("resetButton").addEventListener("click", () => rebuild(false));
$("targetInput").addEventListener("input", event => { $("targetOutput").textContent = `${event.target.value} tiles`; });
$("targetInput").addEventListener("change", stageSelection);
$("speedInput").addEventListener("input", event => { $("speedOutput").textContent = `${event.target.value}%`; });
$("phaseInput").addEventListener("input", event => { $("phaseOutput").textContent = (event.target.value / 100).toFixed(2); drawWindow(); });
$("phaseInput").addEventListener("change", stageSelection);
$("pointsToggle").addEventListener("change", draw);
$("atlasToggle").addEventListener("change", draw);
$("markingToggle").addEventListener("change", draw);
$("barsToggle").addEventListener("change", draw);
$("windowToggle").addEventListener("change", event => { $("windowInset").hidden = !event.target.checked; });
canvas.addEventListener("wheel", event => { event.preventDefault(); camera.zoom = Math.max(.45, Math.min(3.5, camera.zoom * Math.exp(-event.deltaY * .001))); draw(); }, { passive: false });
canvas.addEventListener("pointerdown", event => { dragging = true; dragStart = { x: event.clientX - camera.x, y: event.clientY - camera.y }; canvas.setPointerCapture(event.pointerId); });
canvas.addEventListener("pointermove", event => { if (!dragging) return; camera.x = event.clientX - dragStart.x; camera.y = event.clientY - dragStart.y; draw(); });
canvas.addEventListener("pointerup", () => { dragging = false; });
window.addEventListener("resize", draw);

function drawCatalogIcon(canvasElement, entry) {
  const context = canvasElement.getContext("2d");
  const ratio = devicePixelRatio || 1;
  const width = 68, height = 58;
  canvasElement.width = width * ratio;
  canvasElement.height = height * ratio;
  context.scale(ratio, ratio);
  context.beginPath();
  entry.points.forEach(([x, y], index) => {
    const px = width / 2 + x * 27;
    const py = height / 2 + y * 27;
    index ? context.lineTo(px, py) : context.moveTo(px, py);
  });
  context.closePath();
  context.fillStyle = `${entry.color}cc`;
  context.fill();
  context.strokeStyle = entry.color;
  context.lineWidth = 1.4;
  context.stroke();
}

function stageSelection() {
  selectionDirty = true;
  running = false;
  active = [];
  trial = null;
  rollback = null;
  $("runButton").textContent = "Run selected set";
  $("runState").textContent = "selection staged";
  $("runState").parentElement.classList.add("paused");
  $("eventLabel").textContent = "catalog changed · press Run selected set";
  $("status").textContent = `${selectedCatalog.size} prototiles selected; no search has been run for this catalog yet.`;
  updateMetrics();
  if (model) draw();
}

function syncCatalog() {
  document.querySelectorAll(".catalog-tile").forEach(button => {
    button.setAttribute("aria-pressed", String(selectedCatalog.has(button.dataset.tile)));
  });
  const entries = PENROSE_CATALOG.filter(entry => selectedCatalog.has(entry.id));
  const families = [...new Set(entries.map(entry => entry.family))];
  const mode = families.length > 1 ? `${families.join("+")} exact-atom candidate mix` :
    entries.length === 2 ? `${families[0]} complete preset` :
    entries.length ? `${families[0]} partial selection` : "empty selection";
  $("catalogState").textContent = `${entries.length} selected · ${mode}`;
  const p2 = activeFamily === "P2";
  $("weightALabel").textContent = p2 ? "dart" : "thin rhomb";
  $("weightAValue").textContent = p2 ? "1 / 2 / 6" : "1 / 4";
  $("weightAIcon").className = p2 ? "dart" : "thin";
  $("weightBLabel").textContent = p2 ? "kite" : "thick rhomb";
  $("weightBValue").textContent = p2 ? "2 / 4" : "2 / 3";
  $("weightBIcon").className = p2 ? "kite" : "thick";
  $("legendALabel").textContent = p2 ? "kite" : "thick";
  $("legendAIcon").className = p2 ? "tile-kite" : "tile-thick";
  $("legendBLabel").textContent = p2 ? "dart" : "thin";
  $("legendBIcon").className = p2 ? "tile-dart" : "tile-thin";
  $("presentationLabel").textContent = p2
    ? "LIVE SEARCH / EXACT P2 KITES + DARTS"
    : "LIVE SEARCH / EXACT P3 RHOMBS";
  $("learnMarkingButton").textContent = p2 ? "Learn marking on underlying P3" : "Learn P3 marking";
  if (model) draw();
}

function buildCatalog() {
  const container = $("tileCatalog");
  PENROSE_CATALOG.forEach(entry => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "catalog-tile";
    button.dataset.tile = entry.id;
    button.style.setProperty("--tile-color", entry.color);
    button.setAttribute("aria-label", `${entry.family} ${entry.name}`);
    if (entry.family === "P1") {
      button.disabled = true;
      button.title = "P1 exact recomposition is cataloged but not implemented yet";
    }
    button.innerHTML = `<canvas aria-hidden="true"></canvas><div><span>${entry.family}</span><b>${entry.name}</b></div>`;
    button.addEventListener("click", () => {
      if (entry.family === "P1") return;
      selectedCatalog.has(entry.id) ? selectedCatalog.delete(entry.id) : selectedCatalog.add(entry.id);
      syncCatalog();
      stageSelection();
    });
    container.appendChild(button);
    drawCatalogIcon(button.querySelector("canvas"), entry);
  });
  document.querySelectorAll("[data-family]").forEach(button => button.addEventListener("click", () => {
    const family = button.dataset.family;
    if (family === "P1") return;
    if (family !== "implemented") activeFamily = family;
    selectedCatalog.clear();
    PENROSE_CATALOG
      .filter(entry => family === "implemented"
        ? entry.family === "P2" || entry.family === "P3"
        : entry.family === family)
      .forEach(entry => selectedCatalog.add(entry.id));
    syncCatalog();
    stageSelection();
  }));
  $("clearCatalog").addEventListener("click", () => {
    selectedCatalog.clear();
    syncCatalog();
    stageSelection();
  });
  syncCatalog();
}

const pauseForLearning = () => new Promise(resolve => setTimeout(resolve, 140));

async function learnMarking() {
  const button = $("learnMarkingButton");
  button.disabled = true;
  const wasRunning = running;
  running = false;
  $("markingResult").dataset.state = "learning";
  $("markingStatus").textContent = "Enumerating legal P3 half-edge contacts…";
  await pauseForLearning();
  const trainingModels = Array.from({ length: 7 }, (_, index) =>
    makePenroseModelSet({ radius: 11, phaseCode: [47, 181, 293, 419, 557, 673, 811][index] })
  );
  $("markingStatus").textContent = "Solving overlap equalities and the rank-five C₅ action…";
  await pauseForLearning();
  const fitModels = trainingModels.slice(0, 5);
  const heldOutModels = trainingModels.slice(5);
  learnedMarking = learnPenroseGCTS(fitModels);
  const comparison = benchmarkGCTSPruning(fitModels, heldOutModels);
  $("markingStatus").textContent = "Auditing vertex coronas and straight-line continuation…";
  await pauseForLearning();

  const strictBars = Math.round(learnedMarking.straightFraction * 100);
  $("rankMetric").textContent = String(learnedMarking.rank);
  $("starMetric").textContent = String(learnedMarking.vertexStars.length);
  $("barMetric").textContent = `${strictBars}%`;
  $("tensorMetric").textContent = `${learnedMarking.tensor.activeSlots}/${learnedMarking.tensor.denseSlots}`;
  const audit = learnedMarking.ammannAudit;
  $("ammannVerdict").dataset.state = audit.rediscovered ? "pass" : "fail";
  $("ammannVerdict").textContent = audit.rediscovered
    ? "Ammann audit passed · equivalent matching language and exact straight bars"
    : `Not yet Ammann-equivalent · ${audit.falseAccepts} empirically forbidden edge pairs survive · exact straightness fails`;
  const comparisonRows = [
    ["base", comparison.methods.capacity],
    ["rank", comparison.methods.rankFive],
    ["tensor", comparison.methods.compatibility]
  ];
  for (const [prefix, result] of comparisonRows) {
    $(`${prefix}Nodes`).textContent = result.examined.toLocaleString();
    $(`${prefix}Backtracks`).textContent = result.backtracks.toLocaleString();
    $(`${prefix}Prunes`).textContent = result.pruned.toLocaleString();
    $(`${prefix}False`).textContent = result.falsePrunes.toLocaleString();
  }
  $("comparisonContacts").textContent = `${comparison.contacts.toLocaleString()} exact contacts`;
  $("comparisonSummary").textContent =
    `Compatibility uses ${(comparison.methods.compatibility.relativeWork * 100).toFixed(1)}% of baseline node work ` +
    `(${comparison.methods.compatibility.speedup.toFixed(2)}× fewer examined proposals), with ` +
    `${comparison.methods.compatibility.falsePrunes} legal continuations lost.`;
  $("markingResult").dataset.state = "learned";
  $("markingToggle").disabled = false;
  $("barsToggle").disabled = false;
  $("markingStatus").textContent = learnedMarking.validationMismatches === 0
    ? `Learned ${learnedMarking.positiveContacts.toLocaleString()} legal contacts with zero gluing errors. θ uses ${learnedMarking.tensor.activeSlots} of ${learnedMarking.tensor.denseSlots} real-valued slots; support coordinates remain exact. The Ammann verdict stays negative until specificity and exact straightness both pass.`
    : `${learnedMarking.validationMismatches} held-out contacts violate the learned marking.`;
  $("eventLabel").textContent = "rank-five GCTS marking active · seven unmarked vertex stars retained";
  button.textContent = "Relearn P3 marking";
  button.disabled = false;
  running = wasRunning;
  draw();
}

buildCatalog();
$("learnMarkingButton").addEventListener("click", learnMarking);
rebuild(false);
requestAnimationFrame(animate);
