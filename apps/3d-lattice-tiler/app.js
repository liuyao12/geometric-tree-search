import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  GCTS_CATALOG_MIN_PERIODIC_MOTIF_TILES,
  isGctsFigureVisibleInCatalog,
  tileSpecs
} from "./engine.js?v=20260827-a2-size7-v226";

const $ = (id) => document.getElementById(id);

const selectedTilesEl = $("selectedTiles");
const candidateResearchPanel = $("candidateResearchPanel");
const candidateResearchTitle = $("candidateResearchTitle");
const candidateResearchDetail = $("candidateResearchDetail");
const candidateSearchButton = $("candidateSearchButton");
const statusEl = $("status");
const maxTilesInput = $("maxTilesInput");
const layerInput = $("layerInput");
const shellInput = $("shellInput");
const regionField = $("regionField");
const regionSizeFields = $("regionSizeFields");
const regionWidthInput = $("regionWidthInput");
const regionDepthInput = $("regionDepthInput");
const regionHeightInput = $("regionHeightInput");
const snapshotSelect = $("snapshotSelect");
const strategySelect = $("strategySelect");
const strategyRadios = [...document.querySelectorAll('input[name="tilingStrategy"]')];
const strategyDescription = $("strategyDescription");
const faceOrderSelect = $("faceOrderSelect");
const moveOrderSelect = $("moveOrderSelect");
const branchCapInput = $("branchCapInput");
const nodeCapInput = $("nodeCapInput");
const candidateCapInput = $("candidateCapInput");
const timeCapInput = $("timeCapInput");
const mirrorCheckbox = $("mirrorCheckbox");
const exhaustiveCheckbox = $("exhaustiveCheckbox");
const internalCheckbox = $("internalCheckbox");
const edgesCheckbox = $("edgesCheckbox");
const autoFitCheckbox = $("autoFitCheckbox");
const polycubeLatticeSelect = $("polycubeLatticeSelect");
const periodicTileCountSelect = $("periodicTileCountSelect");
const runButton = $("runButton");
const fitButton = $("fitButton");
const maxTileField = $("maxTileField");
const layerField = $("layerField");
const shellField = $("shellField");
const tileList = $("tileList");
const systemTileList = $("systemTileList");
const customPolycubeCheckbox = $("customPolycubeCheckbox");
const customNameInput = $("customNameInput");
const customShapeMatch = $("customShapeMatch");
const customPolyhedronCheckbox = $("customPolyhedronCheckbox");
const customPolyhedronInput = $("customPolyhedronInput");
const customPolyhedronStatus = $("customPolyhedronStatus");
const polycubeBuilder = $("polycubeBuilder");
const clearBuilderButton = $("clearBuilderButton");
const customBuilderButton = $("customBuilderButton");
const customBuilderDialog = $("customBuilderDialog");
const closeBuilderButton = $("closeBuilderButton");
const treePanel = $("treePanel");
const viewport = $("viewport");
const elapsedTime = $("elapsedTime");
const growthChart = $("growthChart");
const growthViewState = $("growthViewState");
const growthHistoryBack = $("growthHistoryBack");
const growthHistoryForward = $("growthHistoryForward");
const growthBenchmarkStatus = $("growthBenchmarkStatus");

const metricTiles = $("metricTiles");
const metricFrontier = $("metricFrontier");
const metricLayer = $("metricLayer");
const metricLayerDetail = $("metricLayerDetail");
const metricVisited = $("metricVisited");
const metricVisitedDetail = $("metricVisitedDetail");
const metricNodes = $("metricNodes");
const metricGrowth = $("metricGrowth");
const metricGrowthDetail = $("metricGrowthDetail");

const prettyNameMap = new Map([
  ["J15", "Johnson solid J15"],
  ["Gyro", "Gyro polyhedron"],
  ["FriaufPoly", "Friauf polyhedron"],
  ["EscherSolid", "Escher Solid"]
]);

const prettyName = (name) => prettyNameMap.get(name) ?? name;

const SOLVER_MESSAGE_FRAME_BUDGET_MS = 10;
const SOLVER_MESSAGE_COMPACT_THRESHOLD = 600;
const FULL_UPDATE_INTERVAL_MS = 260;
const LIVE_UPDATE_FAST_INTERVAL_MS = 70;
const LIVE_UPDATE_MEDIUM_INTERVAL_MS = 130;
const LIVE_UPDATE_SLOW_INTERVAL_MS = 260;
const TREE_RENDER_INTERVAL_MS = 180;
const RUNNING_EDGE_FACE_LIMIT = 3500;
const MAX_RENDERED_TREE_ROWS = 900;
const MAX_STORED_TREE_SNAPSHOTS = 18;
const MAX_PENDING_TREE_SNAPSHOTS = 24;
const CHECKPOINT_VERSION = 2;
const CHECKPOINT_DB_NAME = "3d-lattice-tiler-checkpoints";
const CHECKPOINT_STORE_NAME = "checkpoints";
const CHECKPOINT_KEY = "latest";
const CHECKPOINT_SAVE_INTERVAL_MS = 1800;

function fallbackRenderer(label) {
  const canvas = document.createElement("canvas");
  canvas.className = "renderer-fallback";
  canvas.setAttribute("aria-label", label);
  return {
    domElement: canvas,
    setClearColor() {},
    setPixelRatio() {},
    setSize(width, height) {
      canvas.width = width;
      canvas.height = height;
    },
    render() {}
  };
}

function createRendererOrFallback(options, label) {
  try {
    return new THREE.WebGLRenderer(options);
  } catch (error) {
    console.warn(`${label} WebGL renderer failed`, error);
    return fallbackRenderer(label);
  }
}
const gcdInt = (a, b) => {
  a = Math.abs(Math.round(a));
  b = Math.abs(Math.round(b));
  while (b) [a, b] = [b, a % b];
  return a || 1;
};
const formatSolidAngleValue = (item) => {
  if (item?.display_symbolic) return item.display_symbolic;
  if (item?.symbolic) return item.symbolic;
  const weight = Number(item?.weight);
  const maxValue = Number(item?.max_value) || 1;
  const value = Number.isFinite(Number(item?.value)) ? Number(item.value) : weight / maxValue;
  if (!Number.isFinite(weight) || !Number.isFinite(value)) return "";
  if (Math.abs(weight - Math.round(weight)) < 1e-9 && Math.abs(maxValue - Math.round(maxValue)) < 1e-9) {
    const divisor = gcdInt(weight, maxValue);
    const numerator = Math.round(weight) / divisor;
    const denominator = Math.round(maxValue) / divisor;
    return denominator === 1 ? String(numerator) : `${numerator}/${denominator}`;
  }
  return `≈${value.toPrecision(12).replace(/0+$/u, "").replace(/\.$/u, "")}`;
};
const solidAngleListLabel = (solidAngles = []) => {
  const counts = new Map();
  for (const item of solidAngles) {
    const label = formatSolidAngleValue(item);
    if (!label) continue;
    counts.set(label, (counts.get(label) ?? 0) + 1);
  }
  const values = [...counts.entries()].map(([label, count]) => count > 1 ? `${label} (${count})` : label);
  return values.length ? values.join(", ") : "No sampled solid-angle values";
};

const escapeHtml = (value) => String(value)
  .replace(/&/gu, "&amp;")
  .replace(/</gu, "&lt;")
  .replace(/>/gu, "&gt;")
  .replace(/"/gu, "&quot;");
const solidAngleListHtml = (solidAngles = []) => {
  const counts = new Map();
  for (const item of solidAngles) {
    const label = formatSolidAngleValue(item);
    if (!label) continue;
    counts.set(label, (counts.get(label) ?? 0) + 1);
  }
  const values = [...counts.entries()].map(([label, count]) => {
    const safeLabel = escapeHtml(label);
    return count > 1 ? `${safeLabel} <strong>(${count})</strong>` : safeLabel;
  });
  return values.length ? values.join(", ") : "No sampled solid-angle values";
};
const solidAngleTitle = (solidAngles = []) => solidAngleListLabel(solidAngles);
const polycubeLatticeLabel = (lattice) => {
  const normalized = tileSpecs.normalizePolycubeLattice?.(lattice) ?? lattice;
  if (normalized === "fcc") return "FCC lattice";
  if (normalized === "half") return "(1/2)Z³ lattice";
  return "Z³ lattice";
};
const clone = (value) => (typeof structuredClone === "function" ? structuredClone(value) : JSON.parse(JSON.stringify(value)));
const figureCatalog = tileSpecs.figureCatalog ?? [];
const figureById = new Map();
for (const figure of figureCatalog) {
  figureById.set(figure.id, figure);
  for (const alias of figure.aliases ?? []) figureById.set(alias, figure);
}
const defaultFigureId = figureById.has("cube::0") ? "cube::0" : figureCatalog[0]?.id;
const figureSourceLabel = (figure) => {
  const names = figure?.system_names ?? (figure?.system_name ? [figure.system_name] : []);
  if (names.length <= 1) return names[0] ?? "";
  return `Used in ${names.length} systems`;
};
const figureSourceTitle = (figure) => {
  const names = figure?.system_names ?? (figure?.system_name ? [figure.system_name] : []);
  return names.join(", ");
};

if ("scrollRestoration" in history) history.scrollRestoration = "manual";
window.scrollTo({ top: 0, left: 0 });

let running = false;
let paused = false;
let isFinished = false;
let runSeq = 0;
let pausedConfigKey = null;
let startedAt = 0;
let solverWorker = null;
let solverWorkerActive = false;
const growthWorkers = new Map();
let growthSequence = 0;
let growthRunning = false;
let growthPaused = false;
const growthPausedModes = new Set();
const growthSeries = new Map();
let growthInspection = { modeId: "free_range", pointIndex: null };
let growthPlotClickBound = false;
let growthPlotLegendBound = false;
let growthPlotBackgroundBound = false;
let growthPointerWasNearPoint = false;
let growthPlotRevision = 0;
let growthUiRefreshTimer = null;
let growthUiRefreshShowCurrent = false;
let workerDisplayPaused = false;
let solverMessageQueue = [];
let solverMessageQueueIndex = 0;
let solverMessageFlushQueued = false;
let pendingFullUpdate = null;
let fullUpdateRenderQueued = false;
let fullUpdateTimer = null;
let applyingFullUpdate = false;
let lastFullUpdateRenderedAt = 0;
let pendingLiveSnapshot = null;
let liveUpdateRenderQueued = false;
let liveUpdateTimer = null;
let lastLiveUpdateRenderedAt = 0;

let lastSnapshot = null;
let lastSearchStats = null;
let prototileInfo = null;
let currentOpacities = {};
let rootCentered = false;
let liveFaceStacks = new Map();
let liveFrontierPoints = new Map();

const treeMap = new Map();
const pendingSnapshots = new Map();
const treeSnapshotOrder = [];
const expandedNodes = new Set();
const manuallyExpanded = new Set();
let selectedNodeId = null;
let treeRenderQueued = false;
let treeRenderTimer = null;
let lastTreeRenderAt = 0;
let needsRender = true;
let renderWidth = 0;
let renderHeight = 0;
let selectedFigureIds = ["cube::0"];
let builderNeedsRender = true;
let builderWidth = 0;
let builderHeight = 0;
let builderVoxels = new Set(["0,0,0"]);
let builderHoverKey = null;
let customNameEdited = false;
let lastAutoCustomName = customNameInput.value;
let lastBuilderSignature = null;
let listedPolycubeShapeMap = null;
const figureThumbnailCache = new Map();
const figureTileCache = new Map();
let checkpointDbPromise = null;
let checkpointSaveTimer = null;
let checkpointIdleQueued = false;
let checkpointSaving = false;
let checkpointSaveQueued = false;
let pendingCheckpointSnapshot = null;
let pendingCheckpointReason = "snapshot";
let lastCheckpointSaveAt = 0;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xedf1ef);

const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 4000);
camera.position.set(20, 20, 20);

const renderer = createRendererOrFallback({ antialias: true, powerPreference: "default" }, "Main viewport");
renderer.setClearColor(0xedf1ef, 1);
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
viewport.appendChild(renderer.domElement);
renderer.domElement.addEventListener("wheel", (event) => event.preventDefault(), { passive: false });
renderer.domElement.addEventListener("webglcontextlost", (event) => {
  event.preventDefault();
  setStatus("WebGL context lost; waiting for Chrome to recover...");
});
renderer.domElement.addEventListener("webglcontextrestored", () => {
  setStatus(running ? "Running..." : "Ready");
  requestRender();
});

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 0.4;
controls.maxDistance = 1e6;
controls.addEventListener("change", requestRender);

scene.add(new THREE.HemisphereLight(0xffffff, 0xcfd9d4, 0.78));
scene.add(new THREE.AmbientLight(0xffffff, 0.72));
const keyLight = new THREE.DirectionalLight(0xffffff, 0.95);
keyLight.position.set(12, 18, 14);
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0xffffff, 0.46);
fillLight.position.set(-14, -6, 12);
scene.add(fillLight);
const rimLight = new THREE.DirectionalLight(0xffffff, 0.32);
rimLight.position.set(-10, 14, -16);
scene.add(rimLight);

const faceGroup = new THREE.Group();
const edgeGroup = new THREE.Group();
const frontierPointGroup = new THREE.Group();
scene.add(faceGroup, edgeGroup, frontierPointGroup);

let thumbnailRenderer = null;
function getThumbnailRenderer() {
  if (thumbnailRenderer) return thumbnailRenderer;
  thumbnailRenderer = createRendererOrFallback({
    antialias: true,
    preserveDrawingBuffer: true,
    powerPreference: "low-power"
  }, "Tile thumbnail");
  thumbnailRenderer.setPixelRatio(1);
  thumbnailRenderer.setClearColor(0xedf1ef, 1);
  thumbnailRenderer.setSize(180, 135, false);
  return thumbnailRenderer;
}

const builderScene = new THREE.Scene();
builderScene.background = new THREE.Color(0xedf1ef);
const builderCamera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
builderCamera.position.set(5, 5, 5);
let builderRenderer = null;
let builderControls = null;
function ensureBuilderRenderer() {
  if (builderRenderer && builderControls) return true;
  try {
    builderRenderer = createRendererOrFallback({ antialias: true, powerPreference: "default" }, "Custom polycube builder");
    builderRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    builderRenderer.setClearColor(0xedf1ef, 1);
    polycubeBuilder.appendChild(builderRenderer.domElement);
    builderControls = new OrbitControls(builderCamera, builderRenderer.domElement);
    builderControls.enableDamping = true;
    builderControls.dampingFactor = 0.08;
    builderControls.addEventListener("change", requestBuilderRender);
    builderRenderer.domElement.addEventListener("pointermove", handleBuilderPointerMove);
    builderRenderer.domElement.addEventListener("pointerleave", () => {
      builderHoverKey = null;
      renderBuilderVoxels();
    });
    builderRenderer.domElement.addEventListener("pointerdown", handleBuilderPointerDown);
    builderRenderer.domElement.addEventListener("contextmenu", (event) => event.preventDefault());
    return true;
  } catch (error) {
    console.warn("Custom polycube builder renderer failed", error);
    builderRenderer = null;
    builderControls = null;
    return false;
  }
}
builderScene.add(new THREE.HemisphereLight(0xffffff, 0xcfd9d4, 0.82));
builderScene.add(new THREE.AmbientLight(0xffffff, 0.78));
const builderLight = new THREE.DirectionalLight(0xffffff, 1.0);
builderLight.position.set(5, 8, 6);
builderScene.add(builderLight);
const builderFillLight = new THREE.DirectionalLight(0xffffff, 0.44);
builderFillLight.position.set(-6, 4, -5);
builderScene.add(builderFillLight);
const builderGrid = new THREE.GridHelper(8, 8, 0xb9c8c2, 0xd7e0dc);
builderGrid.position.y = -0.5;
builderScene.add(builderGrid);
let builderGroup = new THREE.Group();
builderScene.add(builderGroup);
const builderRaycaster = new THREE.Raycaster();
const builderPointer = new THREE.Vector2();
const builderCubeGeometry = new THREE.BoxGeometry(0.92, 0.92, 0.92);
const builderBlockMaterial = new THREE.MeshPhongMaterial({ color: 0x178273, flatShading: true });
const builderGhostMaterial = new THREE.MeshPhongMaterial({
  color: 0x315f9f,
  opacity: 0.35,
  transparent: true,
  flatShading: true
});
const builderEdgeMaterial = new THREE.LineBasicMaterial({ color: 0x111827, opacity: 0.55, transparent: true });
const builderEdgeGeometry = new THREE.EdgesGeometry(builderCubeGeometry);

function requestRender() {
  needsRender = true;
}

function requestBuilderRender() {
  builderNeedsRender = true;
}

function setStatus(text) {
  statusEl.textContent = text;
}

function queuedSolverMessageCount() {
  return Math.max(0, solverMessageQueue.length - solverMessageQueueIndex);
}

function setWorkerDisplayPaused(nextPaused) {
  if (workerDisplayPaused === nextPaused) return;
  workerDisplayPaused = nextPaused;
  if (!solverWorker || !solverWorkerActive) return;
  solverWorker.postMessage({
    type: nextPaused ? "pause" : "resume",
    seq: runSeq,
    reason: "display"
  });
}

function syncWorkerDisplayBackpressure() {
  // Rendering is a lossy observer of solver progress. Never pause the search
  // merely because the display is rebuilding geometry or draining telemetry.
  if (workerDisplayPaused) setWorkerDisplayPaused(false);
}

function compactSolverMessageQueue() {
  if (queuedSolverMessageCount() < SOLVER_MESSAGE_COMPACT_THRESHOLD) return;
  const tail = solverMessageQueue.slice(solverMessageQueueIndex);
  let latestFullUpdateIndex = -1;
  const latestWorkingStatusIndexById = new Map();
  tail.forEach((message, index) => {
    if (message?.type === "full_update") latestFullUpdateIndex = index;
    if (message?.type === "node_status" && message.status === "working") {
      latestWorkingStatusIndexById.set(message.id, index);
    }
  });
  solverMessageQueue = tail.filter((message, index) => {
    if (message?.type === "full_update") return index === latestFullUpdateIndex;
    if (message?.type === "placement_delta" && latestFullUpdateIndex >= 0) {
      return index > latestFullUpdateIndex;
    }
    if (message?.type === "node_status" && message.status === "working") {
      return latestWorkingStatusIndexById.get(message.id) === index;
    }
    return true;
  });
  solverMessageQueueIndex = 0;
}

function enqueueSolverMessage(message) {
  enqueueSolverMessages([message]);
}

function enqueueSolverMessages(messages) {
  for (const message of messages ?? []) {
    if (message) solverMessageQueue.push(message);
  }
  if (!messages?.length) return;
  compactSolverMessageQueue();
  syncWorkerDisplayBackpressure();
  scheduleSolverMessageFlush();
}

function scheduleSolverMessageFlush() {
  if (solverMessageFlushQueued) return;
  solverMessageFlushQueued = true;
  requestAnimationFrame(flushSolverMessages);
}

function flushSolverMessages() {
  solverMessageFlushQueued = false;
  const started = performance.now();
  while (solverMessageQueueIndex < solverMessageQueue.length) {
    if (solverMessageQueue[solverMessageQueueIndex]?.type === "placement_delta") {
      const deltas = [];
      while (
        solverMessageQueueIndex < solverMessageQueue.length
        && solverMessageQueue[solverMessageQueueIndex]?.type === "placement_delta"
      ) {
        deltas.push(solverMessageQueue[solverMessageQueueIndex]);
        solverMessageQueueIndex += 1;
      }
      for (let index = 0; index < deltas.length; index++) {
        applyPlacementDelta(deltas[index], { deferDisplay: index < deltas.length - 1 });
      }
    } else {
      handleMessage(solverMessageQueue[solverMessageQueueIndex]);
      solverMessageQueueIndex += 1;
    }
    if (performance.now() - started >= SOLVER_MESSAGE_FRAME_BUDGET_MS) break;
  }
  if (solverMessageQueueIndex >= solverMessageQueue.length) {
    solverMessageQueue = [];
    solverMessageQueueIndex = 0;
  } else {
    if (solverMessageQueueIndex > 200) {
      solverMessageQueue = solverMessageQueue.slice(solverMessageQueueIndex);
      solverMessageQueueIndex = 0;
    }
    scheduleSolverMessageFlush();
  }
  syncWorkerDisplayBackpressure();
}

function criterion() {
  return document.querySelector('input[name="criterion"]:checked').value;
}

function updateCriterionUI() {
  const selected = criterion();
  const byCount = selected === "count";
  maxTileField.classList.toggle("is-active", byCount);
  layerField?.classList.toggle("is-active", selected === "layer");
  shellField.classList.toggle("is-active", selected === "shell");
  regionField.classList.toggle("is-active", selected === "region");
  regionSizeFields.classList.toggle("is-hidden", selected !== "region");
}

const STRATEGY_DESCRIPTIONS = {
  free_range: "Prioritizes forced moves, then explores sensible legal placements with backtracking.",
  learning_free_range: "Starts with an empty marking and records exact local frontier failures; translated recurrences are pruned by geometric overlap.",
  rl_free_range: "Starts with zero linear weights and learns one-tile next-placement returns from anonymous lattice geometry during this run.",
  gcts_rl: "Combines the same one-tile cold linear learner with exact GCTS failure markings; RL orders but never removes legal branches.",
  translational: "Tests increasingly large patches for three exact translation vectors and stops only on a certificate or search limit.",
  isohedral: "Bounded positive-certificate search: it accepts only an exact periodic quotient preserved by symmetries taking the root to every tile class; failure is inconclusive."
};

function checkedRadioValue(radios, fallback) {
  return radios.find(radio => radio.checked)?.value ?? fallback;
}

function setRadioValue(radios, value, fallback) {
  const selected = radios.find(radio => radio.value === value)
    ?? radios.find(radio => radio.value === fallback);
  if (selected) selected.checked = true;
  return selected?.value ?? fallback;
}

function updateStrategyUI() {
  const strategy = checkedRadioValue(strategyRadios, "free_range");
  strategySelect.value = strategy;
  strategyDescription.textContent = STRATEGY_DESCRIPTIONS[strategy] ?? STRATEGY_DESCRIPTIONS.translational;
  periodicTileCountSelect.disabled = strategy !== "translational";
}

function initFigureSelection() {
  const params = new URLSearchParams(window.location.search);
  const requested = params.get("figure");
  const requestedFromTile = params.get("tile");
  const requestedFigure = requested && figureById.has(requested)
    ? requested
    : `${requestedFromTile}::0`;
  const initialFigure = figureById.get(requestedFigure) ?? figureById.get(defaultFigureId);
  selectedFigureIds = [initialFigure?.id].filter(Boolean);
}

function applySearchParams() {
  const params = new URLSearchParams(window.location.search);
  const setSelectParam = (control, name) => {
    const value = params.get(name);
    if (!value || !control) return;
    if ([...control.options].some(option => option.value === value)) control.value = value;
  };
  const setPositiveNumberParam = (control, name) => {
    const value = Number(params.get(name));
    if (Number.isFinite(value) && value > 0) control.value = String(value);
  };
  const criterionParam = params.get("criterion");
  if (["count", "shell", "region"].includes(criterionParam)) {
    document.querySelector(`input[name="criterion"][value="${criterionParam}"]`).checked = true;
  }
  setPositiveNumberParam(maxTilesInput, "target");
  setPositiveNumberParam(maxTilesInput, "target_val");
  setPositiveNumberParam(layerInput, "layer");
  setPositiveNumberParam(shellInput, "shell");
  setSelectParam(faceOrderSelect, "face_order");
  setSelectParam(strategySelect, "tiling_strategy");
  setSelectParam(moveOrderSelect, "move_order");
  setSelectParam(polycubeLatticeSelect, "polycube_lattice");
  setSelectParam(periodicTileCountSelect, "periodic_tile_count");
  setPositiveNumberParam(branchCapInput, "branch_cap");
  setPositiveNumberParam(candidateCapInput, "candidate_cap");
  setPositiveNumberParam(nodeCapInput, "node_limit");
  setPositiveNumberParam(timeCapInput, "time_limit");
  setPositiveNumberParam(regionWidthInput, "region_width");
  setPositiveNumberParam(regionDepthInput, "region_depth");
  setPositiveNumberParam(regionHeightInput, "region_height");
  setRadioValue(strategyRadios, strategySelect.value, "translational");
}

function selectedFigures() {
  return [...new Map(selectedFigureIds.map(id => figureById.get(id)).filter(Boolean).map(figure => [figure.id, figure])).values()];
}

function rootFigure() {
  return selectedFigures()[0] ?? null;
}

function figuresShareFace(a, b) {
  if (!a || !b) return false;
  if (a.compatible_ids?.includes(b.id)) return true;
  if (b.compatible_ids?.includes(a.id)) return true;
  return false;
}

function isFigureCompatibleWithSelection(figure) {
  const selected = selectedFigures();
  if (!selected.length) return true;
  if (selected.some(item => item.id === figure.id)) return true;
  return selected.every(item => figuresShareFace(item, figure));
}

function updateMirrorAvailability() {
  const isChiral = selectedFigures().some(figure =>
    figure.is_chiral || figure.census_candidate?.screening?.requires_mirrors
  );
  const reflectionsForbidden = selectedFigures().some(figure => figure.aperiodic_tile?.reflections_forbidden);
  mirrorCheckbox.disabled = !isChiral || reflectionsForbidden;
  mirrorCheckbox.parentElement.style.opacity = isChiral && !reflectionsForbidden ? "1" : "0.45";
  if (!isChiral || reflectionsForbidden) mirrorCheckbox.checked = false;
}

function applyModeDefaults() {
  const figure = rootFigure();
  const defaults = tileSpecs.metadata[figure?.mode_key]?.default_viz ?? {};
  internalCheckbox.checked = !!defaults.internal;
  updateMirrorAvailability();
}

function createTileMeshGroup(tile, colorIndex = 0) {
  const group = new THREE.Group();
  const positions = [];
  const edgePositions = [];
  const scale = tileSpecs.SCALE;

  for (const face of tile.faces ?? []) {
    if (face.length < 3) continue;
    for (let i = 1; i < face.length - 1; i += 1) {
      pushVertex(positions, tile.verts[face[0]], scale);
      pushVertex(positions, tile.verts[face[i]], scale);
      pushVertex(positions, tile.verts[face[i + 1]], scale);
    }
    for (let i = 0; i < face.length; i += 1) {
      pushVertex(edgePositions, tile.verts[face[i]], scale);
      pushVertex(edgePositions, tile.verts[face[(i + 1) % face.length]], scale);
    }
  }

  if (positions.length) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geometry.computeVertexNormals();
    group.add(new THREE.Mesh(geometry, new THREE.MeshPhongMaterial({
      color: new THREE.Color(tileSpecs.COLOR_PALETTE[colorIndex % tileSpecs.COLOR_PALETTE.length]),
      side: THREE.DoubleSide,
      flatShading: true,
      polygonOffset: true,
      polygonOffsetFactor: 1,
      polygonOffsetUnits: 1
    })));
  }
  if (edgePositions.length) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(edgePositions, 3));
    group.add(new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({ color: 0x111827 })));
  }
  return group;
}

function tileForFigure(figure) {
  if (!figure) return null;
  if (figureTileCache.has(figure.id)) return figureTileCache.get(figure.id);
  const built = tileSpecs.TILING_REGISTRY[figure?.mode_key]?.build() ?? [];
  const tile = built[figure?.tile_index] ?? null;
  figureTileCache.set(figure.id, tile);
  return tile;
}

function fitCameraToObject(cameraToFit, controlsToFit, object, padding = 1.8) {
  const box = new THREE.Box3().setFromObject(object);
  if (box.isEmpty()) return;
  const center = new THREE.Vector3();
  const size = new THREE.Vector3();
  box.getCenter(center);
  box.getSize(size);
  const radius = Math.max(1, size.length() * 0.5);
  const distance = radius / Math.sin(THREE.MathUtils.degToRad(cameraToFit.fov) / 2) * padding;
  const offset = new THREE.Vector3(1.3, 1.05, 1.15).normalize().multiplyScalar(distance);
  controlsToFit.target.copy(center);
  cameraToFit.position.copy(center).add(offset);
  cameraToFit.near = Math.max(0.01, radius / 100);
  cameraToFit.far = Math.max(1000, radius * 80);
  cameraToFit.updateProjectionMatrix();
  controlsToFit.update();
}


function placeholderThumbnail(label = "tile") {
  const safe = encodeURIComponent(label);
  return `data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 180 135'%3E%3Crect width='180' height='135' fill='%23edf1ef'/%3E%3Cpath d='M52 38h76v59H52z' fill='none' stroke='%2393a4a0' stroke-width='5'/%3E%3Ctext x='90' y='72' text-anchor='middle' dominant-baseline='middle' font-family='sans-serif' font-size='16' fill='%2364766f'%3E${safe}%3C/text%3E%3C/svg%3E`;
}

function tileThumbnail(tile, cacheKey, colorIndex = 0) {
  if (figureThumbnailCache.has(cacheKey)) return figureThumbnailCache.get(cacheKey);
  if (!tile) return placeholderThumbnail();
  let group = null;
  try {
    const sceneForThumb = new THREE.Scene();
    sceneForThumb.background = new THREE.Color(0xedf1ef);
    const cameraForThumb = new THREE.PerspectiveCamera(45, 4 / 3, 0.1, 1000);
    group = createTileMeshGroup(tile, colorIndex);
    sceneForThumb.add(group);
    sceneForThumb.add(new THREE.AmbientLight(0xffffff, 0.76));
    const light = new THREE.DirectionalLight(0xffffff, 0.76);
    light.position.set(4, 6, 5);
    sceneForThumb.add(light);
    const box = new THREE.Box3().setFromObject(group);
    const center = new THREE.Vector3();
    const size = new THREE.Vector3();
    box.getCenter(center);
    box.getSize(size);
    const radius = Math.max(0.8, size.length() * 0.5);
    cameraForThumb.position.copy(center).add(new THREE.Vector3(1.35, 1.05, 1.15).normalize().multiplyScalar(radius * 4.2));
    cameraForThumb.lookAt(center);
    cameraForThumb.near = 0.01;
    cameraForThumb.far = Math.max(100, radius * 50);
    cameraForThumb.updateProjectionMatrix();
    const rendererForThumb = getThumbnailRenderer();
    rendererForThumb.render(sceneForThumb, cameraForThumb);
    const url = rendererForThumb.domElement.toDataURL("image/png");
    figureThumbnailCache.set(cacheKey, url);
    return url;
  } catch (error) {
    console.warn("Tile catalog thumbnail failed", error);
    const fallback = placeholderThumbnail(tile?.name ?? "tile");
    figureThumbnailCache.set(cacheKey, fallback);
    return fallback;
  } finally {
    if (group) disposeObjectTree(group);
  }
}

function figureThumbnail(figure) {
  const colorIndex = Math.max(0, figureCatalog.findIndex(item => item.id === figure.id));
  return tileThumbnail(tileForFigure(figure), `figure:${figure.id}`, colorIndex);
}

function tileFaceCount(tile) {
  return tile?.faces?.length ?? 0;
}

function figureHasCategory(figure, category) {
  return (figure.category ?? []).includes(category);
}

function polycubeCubeCount(figure) {
  if (!figureHasCategory(figure, "Polycubes")) return Infinity;
  const tile = tileForFigure(figure);
  const count = (tile?.occupancy_points ?? []).filter(point => point.weight === 48).length;
  return count || Infinity;
}

const catalogGroupDefinitions = [
  { id: "aperiodic", title: "Known aperiodic monotile", test: figure => figureHasCategory(figure, "Aperiodic Monotiles") },
  { id: "a2-layered", title: "A₂ layered solids · x+y+z=c", test: figure => figureHasCategory(figure, "A2 Layered Solids") },
  { id: "unresolved-polycubes", title: "Unresolved polycube candidates", test: figure => figureHasCategory(figure, "Unresolved Polycube Candidates") },
  { id: "unresolved", title: "Unresolved lattice candidates", test: figure => figureHasCategory(figure, "Unresolved Lattice Candidates") },
  {
    id: "periodic-controls",
    title: `Large-domain periodic controls (≥${GCTS_CATALOG_MIN_PERIODIC_MOTIF_TILES} tiles)`,
    test: figure => figureHasCategory(figure, "GCTS Periodic Controls")
  },
  { id: "non-tiler-controls", title: "GCTS non-tiler controls", test: figure => figureHasCategory(figure, "GCTS Non-Tiler Controls") },
  { id: "face-obstruction-controls", title: "Face-to-face obstruction controls", test: figure => figureHasCategory(figure, "Face-to-face Obstruction Controls") },
  { id: "polycubes", title: "Polycubes", test: figure => figureHasCategory(figure, "Polycubes") },
  { id: "fedorov", title: "Fedorov solids", test: figure => figureHasCategory(figure, "Fedorov Solids") },
  { id: "space", title: "Space-fillers", test: figure => figureHasCategory(figure, "Space Fillers") },
  { id: "platonic", title: "Platonic solids", test: figure => figureHasCategory(figure, "Platonic Solids") },
  { id: "sphere", title: "Sphere packings", test: figure => figureHasCategory(figure, "Sphere Packings") },
  { id: "other", title: "Other", test: () => true }
];

function catalogGroupForFigure(figure) {
  return catalogGroupDefinitions.find(group => group.test(figure)) ?? catalogGroupDefinitions.at(-1);
}

function sortCatalogFigures(groupId, figures) {
  return figures.slice().sort((a, b) => {
    if (groupId === "unresolved") {
      return (a.census_candidate?.survivor_priority ?? Infinity) - (b.census_candidate?.survivor_priority ?? Infinity);
    }
    if (groupId === "periodic-controls") {
      const motifDelta = (b.census_candidate?.screening?.motif_tiles ?? 0)
        - (a.census_candidate?.screening?.motif_tiles ?? 0);
      if (motifDelta !== 0) return motifDelta;
      const polycubeDelta = Number(b.census_candidate?.kind === "polycube_census")
        - Number(a.census_candidate?.kind === "polycube_census");
      if (polycubeDelta !== 0) return polycubeDelta;
    }
    if (groupId === "polycubes") {
      const cubeDelta = polycubeCubeCount(a) - polycubeCubeCount(b);
      if (cubeDelta !== 0) return cubeDelta;
    }
    return prettyName(a.name).localeCompare(prettyName(b.name));
  });
}

function groupedCatalogFigures() {
  const groups = new Map(catalogGroupDefinitions.map(group => [group.id, []]));
  for (const figure of figureCatalog) {
    if (!isGctsFigureVisibleInCatalog(figure)) continue;
    groups.get(catalogGroupForFigure(figure).id).push(figure);
  }
  return catalogGroupDefinitions
    .map(group => ({ ...group, figures: sortCatalogFigures(group.id, groups.get(group.id) ?? []) }))
    .filter(group => group.figures.length);
}

function customPolycubeDisplayName() {
  return customNameInput.value.trim() || "Custom polycube";
}

function selectedPolycubeLattice() {
  return tileSpecs.normalizePolycubeLattice?.(polycubeLatticeSelect.value) ?? "z3";
}

function customPolycubeTile() {
  return tileSpecs.buildPolycubeTile(customPolycubeDisplayName(), [...builderVoxels].map(keyToVoxel), { polycube_lattice: selectedPolycubeLattice() });
}

function customPolycubeThumbnail(tile) {
  const signature = [...builderVoxels].sort().join("|") || "empty";
  return tileThumbnail(tile, `custom:${signature}`, selectedFigureIds.length);
}

function customPolyhedronDefinition({ updateStatus = true } = {}) {
  if (!customPolyhedronCheckbox.checked) return null;
  try {
    const definition = JSON.parse(customPolyhedronInput.value);
    if (!definition || Array.isArray(definition) || typeof definition !== "object") {
      throw new Error("Expected one JSON object");
    }
    const name = String(definition.name || "Custom lattice polyhedron");
    const tile = tileSpecs.buildLatticePolyhedronTile(name, definition.vertices, definition.faces);
    if (updateStatus) {
      customPolyhedronStatus.textContent = `${tile.verts.length} vertices · ${tile.faces.length} faces · valid 3D lattice polyhedron`;
      customPolyhedronStatus.classList.remove("is-error");
    }
    return {
      config: { name, vertices: definition.vertices, faces: definition.faces },
      tile
    };
  } catch (error) {
    if (updateStatus) {
      customPolyhedronStatus.textContent = error?.message ?? String(error);
      customPolyhedronStatus.classList.add("is-error");
    }
    return null;
  }
}

function selectedSystemItems() {
  const items = selectedFigures().map((figure, index) => ({
    id: figure.id,
    name: prettyName(figure.name),
    title: `${figureSourceTitle(figure)}: ${prettyName(figure.name)}`,
    thumbnail: figureThumbnail(figure),
    faceCount: tileFaceCount(tileForFigure(figure)),
    solidAngles: figure.solid_angles ?? tileSpecs.solidAngleValues?.(tileForFigure(figure)) ?? [],
    latticeLabel: figure.category?.includes("Polycubes") ? polycubeLatticeLabel(selectedPolycubeLattice()) : "",
    tileIndex: index,
    remove: () => {
      selectedFigureIds = selectedFigureIds.filter(id => id !== figure.id);
      handleFigureSelectionChanged();
    }
  }));
  if (customPolycubeCheckbox.checked) {
    const name = customPolycubeDisplayName();
    const tile = customPolycubeTile();
    items.push({
      id: "__custom_polycube__",
      name: `custom: ${name}`,
      title: `${name}: ${builderVoxels.size} cube${builderVoxels.size === 1 ? "" : "s"}`,
      thumbnail: customPolycubeThumbnail(tile),
      faceCount: tileFaceCount(tile),
      solidAngles: tileSpecs.solidAngleValues?.(tile) ?? [],
      latticeLabel: polycubeLatticeLabel(tile.polycube_lattice),
      tileIndex: items.length,
      remove: () => {
        customPolycubeCheckbox.checked = false;
        handleCustomPolycubeChanged();
      }
    });
  }
  const customPolyhedron = customPolyhedronDefinition();
  if (customPolyhedron) {
    const { config, tile } = customPolyhedron;
    items.push({
      id: "__custom_polyhedron__",
      name: `custom: ${config.name}`,
      title: `${config.name}: ${tile.verts.length} vertices, ${tile.faces.length} faces`,
      thumbnail: tileThumbnail(tile, `custom-polyhedron:${customPolyhedronInput.value}`, items.length),
      faceCount: tileFaceCount(tile),
      solidAngles: tileSpecs.solidAngleValues?.(tile) ?? [],
      latticeLabel: "integer lattice",
      tileIndex: items.length,
      remove: () => {
        customPolyhedronCheckbox.checked = false;
        handleCustomPolycubeChanged();
      }
    });
  }
  return items;
}

function tileCountForSelectedItem(item, snapshot = lastSnapshot) {
  if (item.tileIndex == null) return 0;
  return snapshot?.tile_counts?.find(entry => entry.type_idx === item.tileIndex)?.count ?? 0;
}

function renderSelectedTiles() {
  selectedTilesEl.replaceChildren();
  const items = selectedSystemItems();
  if (!items.length) {
    const empty = document.createElement("span");
    empty.className = "selected-empty";
    empty.textContent = "Choose a tile";
    selectedTilesEl.appendChild(empty);
    return;
  }
  items.forEach((item, index) => {
    const row = document.createElement("div");
    row.className = "selected-tile-row";
    row.classList.toggle("is-root", index === 0);

    if (item.thumbnail) {
      const image = document.createElement("img");
      image.className = "selected-tile-thumb";
      image.alt = item.name;
      image.src = item.thumbnail;
      row.append(image);
    }

    const main = document.createElement("div");
    main.className = "selected-tile-main";

    const label = document.createElement("span");
    label.className = "selected-tile-name";
    label.textContent = item.name;
    label.title = `${item.title}${item.latticeLabel ? `\n${item.latticeLabel}` : ""}\n${solidAngleTitle(item.solidAngles)}`;

    const faces = document.createElement("span");
    faces.className = "selected-tile-faces";
    faces.textContent = item.latticeLabel ? `${item.faceCount} faces · ${item.latticeLabel}` : `${item.faceCount} faces`;
    faces.title = `Faces on this tile${item.latticeLabel ? `\n${item.latticeLabel}` : ""}\n${solidAngleTitle(item.solidAngles)}`;
    main.append(label, faces);

    const count = document.createElement("span");
    count.className = "selected-tile-count";
    count.textContent = tileCountForSelectedItem(item);
    count.title = "Copies in the displayed tiling";

    const opacity = document.createElement("input");
    opacity.className = "selected-tile-opacity";
    opacity.type = "range";
    opacity.min = "0";
    opacity.max = "1";
    opacity.step = "0.05";
    opacity.value = currentOpacities[item.tileIndex] ?? 1;
    opacity.title = `Opacity for ${item.name}`;
    opacity.addEventListener("input", () => {
      currentOpacities[item.tileIndex] = +opacity.value;
      if (lastSnapshot) updateScene(lastSnapshot, { preserveView: true });
      requestRender();
    });

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "selected-tile-remove";
    remove.textContent = "x";
    remove.title = `Remove ${item.name}`;
    remove.addEventListener("click", item.remove);
    row.append(main, opacity, count, remove);
    selectedTilesEl.appendChild(row);
  });
}

function getCustomPolycubeConfig() {
  if (!customPolycubeCheckbox.checked) return [];
  return [{
    name: customNameInput.value.trim() || "Custom polycube",
    voxels: [...builderVoxels].map(key => key.split(",").map(Number))
  }];
}

function customSystemConfig() {
  const polycubes = getCustomPolycubeConfig();
  const customPolyhedron = customPolyhedronDefinition({ updateStatus: false });
  return {
    name: selectedFigures().map(figure => figure.name).join(" + ") || "Figure system",
    figure_refs: selectedFigureIds,
    polycubes,
    polyhedra: customPolyhedron ? [customPolyhedron.config] : [],
    polycube_lattice: selectedPolycubeLattice()
  };
}

function requestIdleWork(callback) {
  if (typeof window.requestIdleCallback === "function") {
    window.requestIdleCallback(callback, { timeout: 2500 });
    return;
  }
  window.setTimeout(callback, 0);
}

function openCheckpointDb() {
  if (!("indexedDB" in window)) return Promise.resolve(null);
  if (checkpointDbPromise) return checkpointDbPromise;
  checkpointDbPromise = new Promise((resolve) => {
    const request = indexedDB.open(CHECKPOINT_DB_NAME, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(CHECKPOINT_STORE_NAME)) db.createObjectStore(CHECKPOINT_STORE_NAME);
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => {
      console.warn("Could not open tiler checkpoint store", request.error);
      resolve(null);
    };
  });
  return checkpointDbPromise;
}

async function writeCheckpointRecord(record) {
  const db = await openCheckpointDb();
  if (!db) return;
  await new Promise((resolve, reject) => {
    const tx = db.transaction(CHECKPOINT_STORE_NAME, "readwrite");
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error);
    tx.objectStore(CHECKPOINT_STORE_NAME).put(record, CHECKPOINT_KEY);
  });
}

async function readCheckpointRecord() {
  const db = await openCheckpointDb();
  if (!db) return null;
  return await new Promise((resolve) => {
    const tx = db.transaction(CHECKPOINT_STORE_NAME, "readonly");
    const request = tx.objectStore(CHECKPOINT_STORE_NAME).get(CHECKPOINT_KEY);
    request.onsuccess = () => resolve(request.result ?? null);
    request.onerror = () => {
      console.warn("Could not read tiler checkpoint", request.error);
      resolve(null);
    };
  });
}

function checkpointUiState() {
  return {
    selectedFigureIds: [...selectedFigureIds],
    builderVoxels: [...builderVoxels],
    customName: customNameInput.value,
    customNameEdited,
    customPolyhedronJson: customPolyhedronInput.value,
    controls: {
      criterion: criterion(),
      maxTiles: maxTilesInput.value,
      layer: layerInput.value,
      shell: shellInput.value,
      regionWidth: regionWidthInput.value,
      regionDepth: regionDepthInput.value,
      regionHeight: regionHeightInput.value,
      snapshotEvery: snapshotSelect.value,
      faceOrder: faceOrderSelect.value,
      tilingStrategy: strategySelect.value,
      moveOrder: moveOrderSelect.value,
      polycubeLattice: selectedPolycubeLattice(),
      periodicTileCount: periodicTileCountSelect.value,
      branchCap: branchCapInput.value,
      nodeCap: nodeCapInput.value,
      candidateCap: candidateCapInput.value,
      timeCap: timeCapInput.value,
      mirror: mirrorCheckbox.checked,
      exhaustive: exhaustiveCheckbox.checked,
      internal: internalCheckbox.checked,
      edges: edgesCheckbox.checked,
      autoFit: autoFitCheckbox.checked,
      customPolycube: customPolycubeCheckbox.checked,
      customPolyhedron: customPolyhedronCheckbox.checked
    }
  };
}

function snapshotForCheckpoint(snapshot) {
  const keepInternal = internalCheckbox.checked;
  return {
    type: "full_update",
    tile_count: snapshot.tile_count ?? 0,
    tile_counts: snapshot.tile_counts ?? [],
    faces: (snapshot.faces ?? []).filter(face => keepInternal || !face.internal),
    frontier_points: snapshot.frontier_points ?? [],
    frontier_stats: snapshot.frontier_stats ?? null,
    search_stats: snapshot.search_stats ?? null,
    visual_only: !keepInternal
  };
}

function buildCheckpoint(snapshot, reason) {
  return {
    version: CHECKPOINT_VERSION,
    savedAt: Date.now(),
    reason,
    elapsedMs: startedAt ? Math.max(0, performance.now() - startedAt) : 0,
    config: pausedConfigKey ? JSON.parse(pausedConfigKey) : JSON.parse(configKey()),
    ui: checkpointUiState(),
    currentOpacities: { ...currentOpacities },
    prototileInfo: clone(prototileInfo),
    snapshot: snapshotForCheckpoint(snapshot)
  };
}

function queueCheckpointSave(snapshot, options = {}) {
  if (!snapshot || !prototileInfo) return;
  pendingCheckpointSnapshot = snapshot;
  pendingCheckpointReason = options.reason ?? pendingCheckpointReason ?? "snapshot";

  if (options.immediate) {
    if (checkpointSaveTimer) {
      clearTimeout(checkpointSaveTimer);
      checkpointSaveTimer = null;
    }
    checkpointIdleQueued = false;
    void saveCheckpointNow();
    return;
  }

  if (checkpointSaveTimer || checkpointIdleQueued) return;
  const elapsed = performance.now() - lastCheckpointSaveAt;
  const delay = Math.max(0, CHECKPOINT_SAVE_INTERVAL_MS - elapsed);
  checkpointSaveTimer = setTimeout(() => {
    checkpointSaveTimer = null;
    checkpointIdleQueued = true;
    requestIdleWork(() => {
      checkpointIdleQueued = false;
      void saveCheckpointNow();
    });
  }, delay);
}

function cancelPendingCheckpointSave() {
  if (checkpointSaveTimer) {
    clearTimeout(checkpointSaveTimer);
    checkpointSaveTimer = null;
  }
  checkpointIdleQueued = false;
  pendingCheckpointSnapshot = null;
  pendingCheckpointReason = "snapshot";
}

async function saveCheckpointNow() {
  if (checkpointSaving) {
    checkpointSaveQueued = true;
    return;
  }
  const snapshot = pendingCheckpointSnapshot ?? lastSnapshot;
  if (!snapshot || !prototileInfo) return;
  const reason = pendingCheckpointReason || "snapshot";
  pendingCheckpointSnapshot = null;
  checkpointSaving = true;
  try {
    await writeCheckpointRecord(buildCheckpoint(snapshot, reason));
    lastCheckpointSaveAt = performance.now();
  } catch (error) {
    console.warn("Could not save tiler checkpoint", error);
  } finally {
    checkpointSaving = false;
    if (checkpointSaveQueued || pendingCheckpointSnapshot) {
      checkpointSaveQueued = false;
      queueCheckpointSave(pendingCheckpointSnapshot ?? lastSnapshot, { reason: pendingCheckpointReason || "snapshot" });
    }
  }
}

function applyCheckpointUiState(ui = {}) {
  const controls = ui.controls ?? {};
  const validFigureIds = (ui.selectedFigureIds ?? []).filter(id => figureById.has(id));
  if (validFigureIds.length) selectedFigureIds = validFigureIds;
  if (Array.isArray(ui.builderVoxels) && ui.builderVoxels.length) {
    builderVoxels = new Set(ui.builderVoxels.filter(key => /^-?\d+,-?\d+,-?\d+$/u.test(key)));
  }
  if (!builderVoxels.size) builderVoxels = new Set(["0,0,0"]);

  const savedCriterion = ["count", "shell", "region"].includes(controls.criterion) ? controls.criterion : "count";
  const criterionRadio = document.querySelector(`input[name="criterion"][value="${savedCriterion}"]`);
  if (criterionRadio) criterionRadio.checked = true;
  if (controls.maxTiles != null) maxTilesInput.value = controls.maxTiles;
  if (controls.layer != null) layerInput.value = controls.layer;
  if (controls.shell != null) shellInput.value = controls.shell;
  if (controls.regionWidth != null) regionWidthInput.value = controls.regionWidth;
  if (controls.regionDepth != null) regionDepthInput.value = controls.regionDepth;
  if (controls.regionHeight != null) regionHeightInput.value = controls.regionHeight;
  if (controls.snapshotEvery != null) snapshotSelect.value = controls.snapshotEvery;
  if (controls.faceOrder != null) faceOrderSelect.value = controls.faceOrder;
  if (controls.tilingStrategy != null) {
    const savedStrategy = controls.tilingStrategy === "freestyle" ? "free_range" : controls.tilingStrategy;
    strategySelect.value = setRadioValue(strategyRadios, savedStrategy, "free_range");
  }
  if (controls.moveOrder != null) moveOrderSelect.value = controls.moveOrder;
  if (controls.polycubeLattice != null) {
    const lattice = tileSpecs.normalizePolycubeLattice?.(controls.polycubeLattice) ?? "z3";
    polycubeLatticeSelect.value = lattice;
  }
  if (controls.periodicTileCount != null) periodicTileCountSelect.value = String(controls.periodicTileCount);
  if (controls.branchCap != null) branchCapInput.value = controls.branchCap;
  if (controls.nodeCap != null) nodeCapInput.value = controls.nodeCap;
  if (controls.candidateCap != null) candidateCapInput.value = controls.candidateCap;
  if (controls.timeCap != null) timeCapInput.value = controls.timeCap;
  mirrorCheckbox.checked = !!controls.mirror;
  exhaustiveCheckbox.checked = !!controls.exhaustive;
  internalCheckbox.checked = !!controls.internal;
  edgesCheckbox.checked = controls.edges !== false;
  autoFitCheckbox.checked = controls.autoFit !== false;
  customPolycubeCheckbox.checked = !!controls.customPolycube;
  if (ui.customPolyhedronJson != null) customPolyhedronInput.value = ui.customPolyhedronJson;
  customPolyhedronCheckbox.checked = !!controls.customPolyhedron;
  if (ui.customName != null) customNameInput.value = ui.customName;
  customNameEdited = !!ui.customNameEdited;

  updateCriterionUI();
  updateStrategyUI();
  renderBuilderVoxels(false);
  refreshFigureSelectionUI();
}

function shouldSkipCheckpointRestore() {
  const params = new URLSearchParams(window.location.search);
  return params.has("figure") || params.has("tile");
}

async function restoreLatestCheckpoint() {
  if (shouldSkipCheckpointRestore()) return;
  const checkpoint = await readCheckpointRecord();
  if (!checkpoint || checkpoint.version !== CHECKPOINT_VERSION || !checkpoint.snapshot || !checkpoint.prototileInfo) return;
  if (running || paused || lastSnapshot) return;

  applyCheckpointUiState(checkpoint.ui);
  currentOpacities = { ...(checkpoint.currentOpacities ?? {}) };
  prototileInfo = checkpoint.prototileInfo;
  startedAt = performance.now() - Math.max(0, checkpoint.elapsedMs ?? 0);
  isFinished = true;
  initTileControls(prototileInfo);
  updateScene(checkpoint.snapshot, { preserveView: false });
  setStatus(`Restored: ${checkpoint.snapshot.tile_count ?? 0} tiles`);
  setRunButton();
}

function hasRunnableSelection() {
  return selectedFigures().length > 0
    || customPolycubeCheckbox.checked
    || !!customPolyhedronDefinition({ updateStatus: false });
}

function stopActiveRunAfterSelectionChange() {
  if (growthRunning || growthWorkers.size) stopGrowthBenchmark("Selection changed; benchmark discarded.");
  growthPaused = false;
  growthPausedModes.clear();
  growthSeries.clear();
  growthInspection = { modeId: selectedGrowthMode(), pointIndex: null };
  if (running || paused || solverWorkerActive) {
    runSeq += 1;
    stopSolverWorker();
    running = false;
    paused = false;
    pausedConfigKey = null;
  }
  isFinished = false;
  resetRunView();
  renderGrowthChart();
  setStatus(hasRunnableSelection() ? "Ready" : "Choose a figure or enable a custom lattice tile.");
  setRunButton();
}

function handleFigureSelectionChanged() {
  applyModeDefaults();
  stopActiveRunAfterSelectionChange();
  refreshFigureSelectionUI();
}

function handleCustomPolycubeChanged() {
  stopActiveRunAfterSelectionChange();
  refreshFigureSelectionUI();
}

function selectedCensusCandidate() {
  return rootFigure()?.census_candidate ?? null;
}

function selectedLayeredLattice() {
  return rootFigure()?.layered_lattice ?? null;
}

function censusCandidatePeriodicLane(candidate) {
  const certificate = candidate?.screening?.certificate;
  if (certificate === "translational") return "translational";
  if (certificate === "isohedral_periodic_quotient") return "isohedral";
  return null;
}

function applyCandidateSearchPreset({ invalidate = true } = {}) {
  const knownAperiodic = rootFigure()?.aperiodic_tile ?? null;
  const candidate = selectedCensusCandidate();
  const layeredLattice = selectedLayeredLattice();
  if (!candidate && !knownAperiodic && !layeredLattice) return;
  const periodicLane = censusCandidatePeriodicLane(candidate);
  const periodicCandidate = !!periodicLane;
  document.querySelector(`input[name="criterion"][value="${candidate || layeredLattice ? "shell" : "count"}"]`).checked = true;
  maxTilesInput.value = knownAperiodic
    ? "80"
    : layeredLattice
      ? "120"
    : periodicCandidate
      ? String(Math.max(24, candidate.screening?.motif_tiles ?? 1))
      : "120";
  if (candidate || layeredLattice) shellInput.value = "2";
  strategySelect.value = setRadioValue(
    strategyRadios,
    candidate || layeredLattice ? "gcts_rl" : "free_range",
    candidate || layeredLattice ? "gcts_rl" : "free_range"
  );
  faceOrderSelect.value = "mrv";
  moveOrderSelect.value = "balanced";
  snapshotSelect.value = "0";
  timeCapInput.value = knownAperiodic ? "10" : layeredLattice ? "30" : "60";
  nodeCapInput.value = "0";
  candidateCapInput.value = "0";
  branchCapInput.value = "0";
  exhaustiveCheckbox.checked = true;
  mirrorCheckbox.checked = !!candidate?.screening?.requires_mirrors;
  updateCriterionUI();
  updateStrategyUI();
  if (invalidate) invalidatePausedRunIfNeeded();
}

function updateCandidateResearchPanel() {
  const candidate = selectedCensusCandidate();
  const knownAperiodic = rootFigure()?.aperiodic_tile ?? null;
  const layeredLattice = selectedLayeredLattice();
  candidateResearchPanel.classList.toggle("is-hidden", !candidate && !knownAperiodic && !layeredLattice);
  candidateSearchButton.classList.toggle("is-hidden", !!knownAperiodic);
  if (layeredLattice && !candidate) {
    candidateSearchButton.textContent = "Load layered shell-2 curriculum";
    candidateResearchTitle.textContent = `${rootFigure()?.name ?? "A₂ prism"} · layered lattice function`;
    candidateResearchDetail.textContent = `This non-polycube is an exact prism over an A₂ polygon. Its end faces lie on x+y+z=${layeredLattice.base_layer} and x+y+z=${layeredLattice.top_layer}; all solid-angle samples use the forty-eighth convention inherited from the planar A₂ angles. The solver restricts direct orientations to the six proper cubic rotations preserving the foliation x+y+z=c. Role: ${layeredLattice.role}. For the hat and turtle this is a structured search lead, not yet a proof that the unrestricted three-dimensional tile forces aperiodicity.`;
    return;
  }
  if (candidate) {
    const periodicLane = censusCandidatePeriodicLane(candidate);
    candidateSearchButton.textContent = "Load cold shell-2 curriculum";
    const screening = candidate.last_screening;
    const proof = candidate.gcts_proof_screening;
    const shell = candidate.shell_screening;
    const limits = screening?.translational && screening?.isohedral
      ? ` Translational motifs through ${screening.translational.maximum_requested_motif_tiles} tiles (${screening.translational.seconds_per_tile}s); isohedral growth horizon ${screening.isohedral.growth_horizon_tiles} tiles (${screening.isohedral.seconds_per_tile}s).`
      : "";
    const proofProtocol = screening?.gcts_proof;
    const proofEvidence = proof && proofProtocol ? (() => {
      const globalExtension = proofProtocol.global_extension_screen;
      if (globalExtension && proof.global_extension_trials) {
        const witnessLabel = proof.global_extension_distinct_witnesses === 1 ? "witness" : "witnesses";
        return ` Corrected branch-complete GCTS now enumerates every legal exposed-face extension and charges the node budget only for placements actually applied. All ${proof.global_extension_trials} runs reached ${globalExtension.target_tiles} tiles without backtracking, producing ${proof.global_extension_distinct_witnesses} distinct ${witnessLabel}; every witness had geometric and repeated-translation rank 3, with minimum span isotropy ${proof.global_extension_minimum_isotropy.toFixed(3)}. All ${proof.global_extension_exact_target_checks} exact target-patch checks completed, testing ${proof.global_extension_internal_period_bases_tested.toLocaleString()} candidate period bases without finding a whole-patch or embedded translational quotient. Across the four candidates this is ${globalExtension.target_hits}/${globalExtension.trials} target hits, ${globalExtension.distinct_witnesses} distinct witnesses, and ${globalExtension.internal_period_bases_tested.toLocaleString()} rejected bases with no timeout. These are strong finite-patch witnesses, not space-tiling or aperiodicity certificates. Earlier vertex-MRV depth and policy comparisons are retained as historical diagnostics but are superseded: they incorrectly treated a temporarily stranded vertex as a dead end and charged unvisited UI alternatives to the node budget.`;
      }
      const baselineRange = proof.robust_largest_patch === proof.best_largest_patch
        ? `${proof.best_largest_patch}`
        : `${proof.robust_largest_patch}–${proof.best_largest_patch}`;
      const baseline = proof.target_hits === proof.trials
        ? ` Diversified unbanded GCTS reached a connected ${proofProtocol.target_tiles}-tile patch in all ${proof.trials} seeds${proof.distinct_target_witnesses ? ` as ${proof.distinct_target_witnesses} distinct witnesses` : ""}.`
        : ` Diversified unbanded GCTS ranged from ${baselineRange} tiles across ${proof.trials} seeds at the configured ${proofProtocol.configured_node_limit}-node baseline.`;
      const focused = proof.focused_target_witness && proof.target_hits !== proof.trials
        ? ` A focused run (seed ${proof.focused_seed}) reached ${proofProtocol.target_tiles} tiles after ${proof.focused_visited_nodes} visited nodes.`
        : "";
      const quotient = proof.checkpoint_quotient_checks
        ? ` Exact boundary-quotient checks completed at all ${proof.checkpoint_quotient_checks} newly reached patch sizes from 2 through ${proofProtocol.target_tiles} and certified none; this excludes those particular patches as translational fundamental domains, not other possible motifs.`
        : "";
      const distinctBranches = proof.distinct_checkpoint_checks
        ? ` A separate ${proof.distinct_checkpoint_paths}-path hybrid branch screen saw ${proof.distinct_checkpoint_eligible_states} path-local distinct states through size ${proof.distinct_checkpoint_max_size} and completed exact checks on ${proof.distinct_checkpoint_checks}: the first four at each size plus later states 17, 33, and 49 when reached. Across seeds, those checks represent ${proof.global_checkpoint_states} proper-rigid-motion patch fingerprints; ${proof.repeated_checkpoint_path_pairs} checks repeated geometry reached by another seed. It found no certificate or timeout; ${proof.distinct_checkpoint_sampling_skips + proof.distinct_checkpoint_cap_skips} eligible states were not selected by that bounded schedule.`
        : "";
      const memoAb = proofProtocol.failure_memo_ab
        ? ` A controlled fixed-versus-rigid failure-memo replay produced identical search outcomes and no additional rigid memo hit on all ${proofProtocol.failure_memo_ab.paths_screened} paths, so the faster fixed-root key remains the proof lane default.`
        : "";
      const nogoodRange = proof.nogood_robust_largest_patch === proof.nogood_best_largest_patch
        ? `${proof.nogood_best_largest_patch}`
        : `${proof.nogood_robust_largest_patch}–${proof.nogood_best_largest_patch}`;
      const nogood = proof.nogood_checkpoint_checks
        ? ` A complementary translation-equivariant nogood policy, delayed until 25 failed states have been learned, ranged from ${nogoodRange} tiles across ${proof.trials} seeds${proof.nogood_target_hits ? ` and reached the ${proofProtocol.target_tiles}-tile target in ${proof.nogood_target_hits} seed${proof.nogood_target_hits === 1 ? "" : "s"}` : ""}. Its ${proof.nogood_checkpoint_checks} completed quotient checks add ${proof.nogood_new_checkpoint_states} rigid-motion patch geometries beyond the earlier baseline-plus-immediate-nogood screen, raising this candidate's three-policy checked union to ${proof.combined_checkpoint_states}; none certified periodicity.`
        : "";
      const holdoutRange = proof.holdout_nogood_robust_largest_patch === proof.holdout_nogood_best_largest_patch
        ? `${proof.holdout_nogood_best_largest_patch}`
        : `${proof.holdout_nogood_robust_largest_patch}–${proof.holdout_nogood_best_largest_patch}`;
      const holdout = proof.holdout_trials && proofProtocol.holdout_screen
        ? ` On five unseen seeds, the delayed policy ranged from ${holdoutRange} tiles${proof.holdout_nogood_target_hits ? ` and reached ${proofProtocol.target_tiles} tiles in ${proof.holdout_nogood_target_hits} seed${proof.holdout_nogood_target_hits === 1 ? "" : "s"}` : ""}. Across all three holdout policies, ${proof.holdout_checkpoint_checks} exact checks added ${proof.holdout_new_checkpoint_states} new geometries and expanded this candidate's eight-seed checked union to ${proof.expanded_checkpoint_states}. Globally, delayed nogoods beat immediate nogoods on ${proofProtocol.holdout_screen.delayed_better_than_immediate} holdout paths, tied ${proofProtocol.holdout_screen.delayed_equal_to_immediate}, and worsened ${proofProtocol.holdout_screen.delayed_worse_than_immediate}; they remain complementary rather than universally superior.`
        : "";
      const crystalRange = proof.crystal_robust_largest_patch === proof.crystal_best_largest_patch
        ? `${proof.crystal_best_largest_patch}`
        : `${proof.crystal_robust_largest_patch}–${proof.crystal_best_largest_patch}`;
      const crystal = proof.crystal_trials && proofProtocol.budget_order_screen
        ? ` In the original eight-seed 1,000-node order screen, crystal ordering ranged from ${crystalRange} tiles, beat balanced on ${proof.crystal_better_than_balanced} paths, tied ${proof.crystal_equal_to_balanced}, and lost ${proof.crystal_worse_than_balanced}.${proof.crystal_target_hits ? ` It reached ${proofProtocol.budget_order_screen.target_tiles} tiles ${proof.crystal_target_hits} time${proof.crystal_target_hits === 1 ? "" : "s"} as ${proof.crystal_distinct_target_witnesses} distinct checked witness${proof.crystal_distinct_target_witnesses === 1 ? "" : "es"}.` : ""} Across all candidates, the original policy beat balanced on ${proofProtocol.budget_order_screen.crystal_better_than_balanced} of 32 paths and raised 60-tile hits from ${proofProtocol.budget_order_screen.balanced_target_hits} to ${proofProtocol.budget_order_screen.crystal_target_hits}.`
        : "";
      const internalRange = proof.internal_period_robust_largest_patch === proof.internal_period_best_largest_patch
        ? `${proof.internal_period_best_largest_patch}`
        : `${proof.internal_period_robust_largest_patch}–${proof.internal_period_best_largest_patch}`;
      const internalPeriod = proof.internal_period_trials && proofProtocol.internal_period_screen
        ? ` The current crystal lane instead prioritizes independent repeated same-orientation translations: in a five-second breadth screen it ranged from ${internalRange} tiles and reached repeated-translation rank 3 on ${proof.internal_period_repeated_translation_rank_3_paths}/${proof.internal_period_trials} paths.${proof.internal_period_focused_target ? ` A focused 30-second run reached 60 tiles; its exact internal-motif check rejected all ${proof.internal_period_candidate_bases_tested} candidate period bases, with maximum observed translation support ${proof.internal_period_max_translation_support}.` : ""} Retrospective checks found no exact quotient inside any of the original seven 60-tile witnesses; all four old 10_45026 witnesses repeated 57 of 60 placements along one direction, so tile count alone had overstated their 3D evidence. The same internal checker recovered the known three-tile quotient of control 10_24775.`
        : "";
      return `${baseline}${focused} These are finite-patch witnesses, not space-tiling certificates.${quotient}${distinctBranches}${memoAb}${nogood}${holdout}${crystal}${internalPeriod}`;
    })() : "";
    if (periodicLane) {
      candidateResearchTitle.textContent = `Certified periodic control ${candidate.id}`;
      const source = candidate.screening.periodic_source
        ?? "an exact quotient was mined from the validated 1,174-tile shell-7 witness";
      const sizeLabel = candidate.kind === "polycube_census"
        ? `${candidate.volume} cubes`
        : `${candidate.lattice_points} lattice points`;
      candidateResearchDetail.textContent = `${sizeLabel} · ${source}; the motif has ${candidate.screening.motif_tiles} tiles and period vectors ${candidate.screening.period_vectors.map(vector => `(${vector.join(",")})`).join(", ")}.${candidate.mirror_equivalent_id ? ` Its omitted enantiomer ${candidate.mirror_equivalent_id} is tiling-equivalent by reflection of all space.` : ""} Use the preset to replay the certificate in the ${periodicLane === "isohedral" ? "Isohedral" : "Translational"} lane.`;
    } else if (["finite_extendable_shell_obstruction", "finite_shell_obstruction", "finite_corona_obstruction", "complete_radius3_obstruction"].includes(candidate.screening?.certificate)) {
      candidateResearchTitle.textContent = `Certified non-tiler control ${candidate.id}`;
      candidateResearchDetail.textContent = candidate.screening.certificate === "complete_radius3_obstruction"
        ? `${candidate.volume}-cube polycube · a hash-locked, machine-checked count chain exhausts every radius-three exact-cover proposal: all patches through 46 surrounding copies, every exact count from 47 through 67, and the open-ended tail from 68 upward. The ${candidate.screening.corona_complete_replayed_clauses} imported obstruction clauses were replayed by plain chronological radius-four GCTS with optional nogoods and conflict backjumping disabled; all ${candidate.screening.corona_complete_checked_next_ring_cells} cell obligations are necessary next-ring conditions. Therefore no radius-three patch extends to radius four, which certifies non-tiling in Z³ under proper rotations. Its omitted enantiomer ${candidate.mirror_equivalent_id} has the reflected obstruction. The web run visualizes this hard control; the archived count-chain verifier is the certificate.`
        : candidate.screening.certificate === "finite_corona_obstruction"
        ? `${candidate.volume}-cube polycube · an independently verified radius-${candidate.screening.corona_completed_radius} patch exists, but exact unpruned lattice-cover search exhausts every radius-${candidate.screening.corona_obstruction_radius} extension after ${candidate.screening.corona_obstruction_nodes.toLocaleString()} search nodes over ${candidate.screening.corona_obstruction_placements_considered.toLocaleString()} legal placements. Its omitted enantiomer ${candidate.mirror_equivalent_id} has the reflected obstruction.`
        : candidate.screening.certificate === "finite_shell_obstruction"
        ? `${candidate.lattice_points} lattice points · exhaustive unpruned face-to-face GCTS proves that no combinatorial shell ${candidate.screening.shell_depth} can surround the normalized root under full cubic isometries and integer translations. Shell ${shell?.deepest_completed_shell ?? 1} is attainable, making this a compact non-tiler regression control.`
        : `${candidate.lattice_points} lattice points · exhaustive face-obligation GCTS proves that every route toward combinatorial shell ${candidate.screening.shell_depth} encounters a permanently unfillable exposed face in the configured face-to-face proper-lattice model.${shell?.deepest_completed_shell ? ` Shell ${shell.deepest_completed_shell} is attainable, but no indefinitely extendable next shell exists.` : " The contradiction appears before the first complete shell."} Earlier connected-patch growth could still extend elsewhere, which is why this remains a useful regression control rather than an unresolved candidate.`;
    } else {
      candidateResearchTitle.textContent = `Research candidate ${candidate.id}`;
      candidateResearchDetail.textContent = candidate.kind === "a2_layered_polyprism_census"
        ? `${candidate.description} Exact weighted HNF search exhausts every periodic quotient through ${candidate.screening.periodic_exact_through} copies; at four copies that is all ${candidate.screening.periodic_determinant14_hnf_bases_exhausted} determinant-14 bases with no solver unknowns. An independently replayed root corona uses ${candidate.screening.corona_root_patch_copies} copies. Focused second-corona CEGAR rejects ${candidate.screening.corona2_first_states_rejected}/${candidate.screening.corona2_first_states_checked} distinct first-corona states, but the outer corona space is not exhausted. Larger periodic domains and other corona states remain open, so this is a bounded-unresolved non-polycube benchmark—not evidence of aperiodicity.`
        : candidate.kind === "polycube_census"
        ? candidate.screening.census_stage === "volume9_fresh_bounded_2026_08_25"
          ? `${candidate.volume}-cube ${candidate.mirror_equivalent_id ? `chiral polycube; its omitted enantiomer ${candidate.mirror_equivalent_id} is tiling-equivalent by reflection of all space` : "achiral polycube"}. A fresh, gap-audited proper-rotation census found no independently verified periodic quotient through ${candidate.screening.periodic_exact_through} copies. A longer exact run was requested through ${candidate.screening.periodic_requested_through}, but stopped partway through the ${candidate.screening.periodic_next_motif}-copy domain after ${candidate.screening.periodic_deep_hnf_visited.toLocaleString()} HNF bases and ${candidate.screening.periodic_deep_nodes.toLocaleString()} exact-cover nodes, so larger domains remain open. The bounded isohedral certifier found no certificate through its ${candidate.screening.isohedral_growth_horizon}-tile horizon; that negative result is inconclusive. An independently replayed radius-${candidate.screening.corona_completed_radius} corona exists (${candidate.screening.corona_completed_nodes.toLocaleString()} search nodes over ${candidate.screening.corona_placements_considered.toLocaleString()} placements). This is a bounded-unresolved GCTS benchmark, not evidence of aperiodicity.`
        : candidate.screening.census_stage?.startsWith("volume10_through")
          ? `${candidate.volume}-cube ${candidate.mirror_equivalent_id ? `chiral polycube; its omitted enantiomer ${candidate.mirror_equivalent_id} is the same tiling-existence problem under reflection of all space` : "achiral polycube"}. Exact HNF search exhausted all ${candidate.screening.periodic_hnf_candidates_exhausted.toLocaleString()} quotient bases through ${candidate.screening.periodic_hnf_max_motif_tiles} copies without a periodic certificate. Its radius-${candidate.screening.corona_completed_radius} patch is independently verified. Radius ${candidate.screening.corona_next_radius} remains unresolved across ${candidate.screening.corona_next_portfolio_runs} conflict-backjumping ${candidate.screening.corona_next_portfolio_runs === 1 ? "run" : "runs"} with ${candidate.screening.corona_next_time_limit_ms / 1000} aggregate CPU-seconds of configured budget and ${candidate.screening.corona_next_nodes.toLocaleString()} search nodes; that search was not exhausted.${candidate.screening.corona_continuation_states_checked ? ` Continuation-guided GCTS tested ${candidate.screening.corona_continuation_states_checked} complete radius-${candidate.screening.corona_completed_radius} ${candidate.screening.corona_continuation_states_checked === 1 ? "state" : "states"}; exact radius-${candidate.screening.corona_next_radius} continuation rejected ${candidate.screening.corona_continuation_states_rejected} as dead ends, then the outer search remained incomplete.` : ""} This is a focused GCTS stress candidate, not a tiling or aperiodicity claim.`
          : `${candidate.volume}-cube nonplanar polycube; its omitted enantiomer ${candidate.mirror_equivalent_id} is the same tiling-existence problem under reflection of all space. Exact HNF search exhausted all ${candidate.screening.periodic_hnf_candidates_exhausted.toLocaleString()} quotients through ${candidate.screening.periodic_hnf_max_motif_tiles} copies without a periodic certificate. An exact radius-${candidate.screening.corona_completed_radius} corona exists; radius ${candidate.screening.corona_next_radius} remained incomplete after ${candidate.screening.corona_next_nodes.toLocaleString()} nodes and ${candidate.screening.corona_next_time_limit_ms / 1000}s. Conflict-directed continuation GCTS learned ${candidate.screening.corona_nogood_clauses.toLocaleString()} exact placement nogoods across ${candidate.screening.corona_nogood_portfolio_trials} seeded orderings and pruned ${candidate.screening.corona_nogood_prunes.toLocaleString()} branches using only ${candidate.screening.corona_nogood_continuation_checks} full continuation checks. It found no radius-${candidate.screening.corona_next_radius} extension but did not exhaust the outer search. An exact first-corona forcing audit found all ${candidate.screening.corona_forcing_placements_tested} baseline neighbor placements replaceable, so no individual absolute placement is forced. At the coarser contact-type level, a counterexample-guided exact search found a minimum non-single-cell disjunction of ${candidate.screening.corona_contact_minimum_nontrivial_disjunction} types. Its reciprocal two-state and self-state cycles both survive through radius ${candidate.screening.corona_contact_cycle_completed_radius}. Conditioning on the reciprocal contacts gives ${candidate.screening.corona_contact_reciprocal_incoming_orbits} incoming placement orbits and a dense ${candidate.screening.corona_contact_conditional_transition_edges}-edge local graph: all ${candidate.screening.corona_contact_inactive_incoming_orbits} inactive orbits require another active contact, but the ${candidate.screening.corona_contact_terminating_active_incoming_orbits} active orbits can terminate without one. Whole-corona boundary states are sharper: ${candidate.screening.corona_boundary_obstructed_states.toLocaleString()} of ${candidate.screening.corona_boundary_sampled_states.toLocaleString()} distinct sampled radius-one exteriors (${(100 * candidate.screening.corona_boundary_obstructed_fraction).toFixed(1)}%) cannot extend to radius two, while ${candidate.screening.corona_boundary_extendable_states} survive. An on-demand learned run accumulated ${candidate.screening.corona_boundary_learned_clauses.toLocaleString()} clauses and ${candidate.screening.corona_boundary_nogood_prunes.toLocaleString()} prunes. At the next level it redirected a 1,000-state run to ${candidate.screening.corona_boundary_radius2_learned_survivors} radius-three survivors; at radius three it still made ${candidate.screening.corona_boundary_radius3_stress_prunes.toLocaleString()} prunes in ${candidate.screening.corona_boundary_radius3_stress_time_ms / 1000}s without reaching a survivor. A bounded direct-depth proposal beats that held-out ordering failure with a verified radius-four witness in ${candidate.screening.corona_deep_proposal_radius4_nodes.toLocaleString()} nodes and ${candidate.screening.corona_deep_proposal_radius4_milliseconds}ms. A ${candidate.screening.corona_adaptive_proposal_milliseconds}ms pilot retains that escape while preserving ${(100 * candidate.screening.corona_adaptive_proposal_radius5_coverage_ratio).toFixed(1)}% of equal-budget radius-five coverage; neither it nor exact symmetry closure improves the radius-five result, so both remain optional. An independent pseudo-Boolean Z3 backend matches the ${candidate.screening.corona_next_radius === 5 ? "6,781-placement" : "finite"} incidence model and finds a separately verified radius-four patch in ${candidate.screening.corona_z3_radius4_fast_milliseconds}ms; ${candidate.screening.corona_z3_radius5_runs} diversified radius-five runs totaling ${(candidate.screening.corona_z3_radius5_milliseconds / 1000).toFixed(1)}s remain undecided. A positive-control low-copy CEGAR run rejects ${candidate.screening.corona_cegar_positive_control_dead_states} dead radius-two patches before recovering a verified radius-three witness. Applied here, it exactly rejects all ${candidate.screening.corona_cegar_radius4_obstructed_states} proposed radius-four states, including ${candidate.screening.corona_cegar_economical_radius4_states_checked} economical states down to ${candidate.screening.corona_cegar_minimum_radius4_placements} copies, and retains ${candidate.screening.corona_cegar_symmetry_closed_clauses} sound symmetry-closed obstruction clauses. Eight earlier 62-copy attempts timed out before the factored encoding found and exactly rejected one; ${candidate.screening.corona_cegar_pair_witness_cnf_max61_timeout_runs} searches at 61 copies remain timeout-inconclusive. Radius four is still unexhausted. This is a concrete GCTS proposal-selection stress test, while tiling and aperiodicity remain unresolved.`
        : candidate.lattice_points === 12
        ? `${candidate.description} Complete shell ${shell?.deepest_completed_shell ?? 2} is recorded.${limits}`
        : `Sole shell-screen survivor · ${candidate.lattice_points} lattice points · complete shells 1–${shell?.robust_completed_shell ?? 4} were found in every seed; shell ${shell?.deepest_completed_shell ?? 5} was reached in ${shell?.shell_five_hits ?? 2}/${shell?.shell_five_trials ?? 3} trials with ${shell?.shell_five_witness_tiles ?? 464} tiles. No exact translational or tile-transitive quotient certificate has been found within the recorded limits.${limits}${proofEvidence}`;
      if (candidate.kind === "polycube_census" && candidate.screening.corona_cegar_pair_final_constraints) {
        candidateResearchDetail.textContent += ` Pairwise next-ring coverability promotes ${candidate.screening.corona_cegar_pair_filtered_states_checked} further proposals to ${candidate.screening.corona_cegar_pair_filtered_continuation_nodes}-node aggregate continuation proofs and learns ${candidate.screening.corona_cegar_pair_final_constraints} symmetry-closed cell-pair obligations; ${candidate.screening.corona_cegar_pair_final_timeout_runs} solves with the full pair set remain timeout-inconclusive. A factored witness-CNF encoding uses ${candidate.screening.corona_cegar_pair_witness_cnf_choice_variables.toLocaleString()} local choices and exposes ${candidate.screening.corona_cegar_pair_witness_cnf_states_checked} additional 63-copy proposals plus ${candidate.screening.corona_cegar_pair_witness_cnf_max62_states_checked} at 62 copies; exact GCTS rejects them in ${candidate.screening.corona_cegar_pair_witness_cnf_continuation_nodes + candidate.screening.corona_cegar_pair_witness_cnf_max62_continuation_nodes} aggregate nodes. A three-element root-stabilizer lex leader is exact but does not improve the unresolved 61-copy run. Lazy GCTS independently replays ${candidate.screening.corona_cegar_pair_lazy_subset_replays_verified}/${candidate.screening.corona_cegar_pair_lazy_states_checked} pair clauses, with a minimum ${candidate.screening.corona_cegar_pair_lazy_minimum_clause_size}-placement explanation blocking ${candidate.screening.corona_cegar_pair_lazy_candidate_pairs_blocked.toLocaleString()} compatible next-ring placement pairs in aggregate; the equal-node outer A/B run is neutral because it encounters only simpler immediate obstructions.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_cegar_radius3_states_checked) {
        candidateResearchDetail.textContent += ` A separate pseudo-Boolean CEGAR portfolio proposes ${candidate.screening.corona_cegar_radius3_states_checked} clause-distinct radius-three patches, down to ${candidate.screening.corona_cegar_minimum_radius3_placements} surrounding copies; exact continuation rejects every one at radius four in ${candidate.screening.corona_cegar_continuation_nodes} aggregate nodes and retains ${candidate.screening.corona_cegar_symmetry_closed_clauses} sound symmetry-closed obstruction clauses. Two eager one-step-coverability solves time out, so the lighter proposal model with lazy exact cuts is currently the better supplier. The radius-three state space remains unexhausted.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_cell_cegar_states_checked) {
        candidateResearchDetail.textContent += ` Lazy next-ring cell promotion has now checked ${candidate.screening.corona_cell_cegar_states_checked} exact proposals and promoted ${candidate.screening.corona_cell_cegar_orbits_promoted} symmetry-distinct dead-cell orbits, ending with ${candidate.screening.corona_cell_cegar_final_constraints} enforced cells and ${candidate.screening.corona_cell_cegar_final_clauses} sound placement clauses.${candidate.screening.corona_cell_cegar_minimum_placements ? ` The smallest proposal uses ${candidate.screening.corona_cell_cegar_minimum_placements} surrounding copies.` : ""} The recorded portfolio contains ${candidate.screening.corona_cell_cegar_combined_states_checked} clause-distinct radius-three states and ${candidate.screening.corona_cell_cegar_combined_continuation_nodes} continuation nodes; every failure is still immediate, so no radius-four subtree has survived. Incremental Z3 reused one formula for ${candidate.screening.corona_cell_cegar_incremental_states} SAT proposals, including ${candidate.screening.corona_cell_cegar_incremental_reused_states} strengthened checks without reconstruction; randomized restarts remain necessary after a solver timeout. This remains finite-corona evidence, not a non-tiling or aperiodicity certificate.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_placement_cube_cegar_rounds) {
        candidateResearchDetail.textContent += ` Placement-cube CEGAR now continues SAT partition leaves automatically. Its first ${candidate.screening.corona_placement_cube_cegar_rounds} exact-41 rounds reject ${candidate.screening.corona_placement_cube_cegar_proposals_rejected}/${candidate.screening.corona_placement_cube_cegar_proposals_checked} radius-three proposals at radius four, then grow the independently replayed feedback to ${candidate.screening.corona_placement_cube_cegar_final_clauses} clauses and ${candidate.screening.corona_placement_cube_cegar_final_cells} next-ring cells. Fixed-value propagation before PB bit-blasting then revisits ${candidate.screening.corona_propagate_values_historical_singletons} historical singleton leaves: ${candidate.screening.corona_propagate_values_unsat_singletons} become exact UNSAT and the sixth yields a new 41-copy proposal. Nested compatible-placement cubes and exact GCTS feedback ultimately test and reject ${candidate.screening.corona_propagate_values_new_proposals} 41-copy proposals in total, using ${candidate.screening.corona_propagate_values_continuation_nodes} continuation nodes. All ${candidate.screening.corona_propagate_values_replayed_clauses} obstruction clauses replay independently with no failure, and ${candidate.screening.corona_nested_partition_unsat_leaves} terminal partition leaves close with no open residue. Exact count 41 is therefore exhausted as a possible radius-four survivor in this model. Counts ${candidate.screening.corona_next_unresolved_minimum_placements} and above and the unbounded tail remain open, so the candidate is still inconclusive.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_radius3_cegar_proposals) {
        const radius3 = candidate.screening;
        candidateResearchDetail.textContent += ` An unbounded-copy radius-two-to-three CEGAR chain proposed ${radius3.corona_radius3_cegar_proposals} exact outer states. GCTS rejected ${radius3.corona_radius3_cegar_rejected_states} of them—${radius3.corona_radius3_cegar_immediate_obstructions} by an immediate dead cell and ${radius3.corona_radius3_cegar_subtree_obstructions} by a resolved subtree conflict—before extending the last proposal to an independently verified ${radius3.corona_completed_witness_placements}-copy radius-three corona. A separate replay exhausts all ${radius3.corona_radius3_cegar_replayed_clauses}/${radius3.corona_radius3_cegar_final_clauses} retained obstruction clauses. That recorded survivor itself has ${radius3.corona_radius3_witness_radius4_dead_cells} immediate radius-four dead cells, with a smallest ${radius3.corona_radius3_witness_radius4_minimum_clause}-copy conflict, so it does not reach radius four; other radius-three coronas remain unexhausted. This upgrades the candidate's finite survival evidence, not its tiling or aperiodicity status.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_staged_cell_feedback_report) {
        const stagedCells = candidate.screening;
        candidateResearchDetail.textContent += ` Staging exact dead-cell feedback ${stagedCells.corona_staged_cell_feedback_batch} constraints at a time improves the matched radius-three proposal funnel from ${stagedCells.corona_staged_cell_feedback_matched_all_at_once_states} state to ${stagedCells.corona_staged_cell_feedback_matched_staged_states} under the same seed and 30-second check cap. Across ${stagedCells.corona_staged_cell_feedback_portfolio_runs} staged seeds it supplies ${stagedCells.corona_staged_cell_feedback_distinct_states} distinct ${stagedCells.corona_staged_cell_feedback_minimum_placements}–${stagedCells.corona_staged_cell_feedback_maximum_placements}-copy states. Exact radius-four GCTS rejects all ${stagedCells.corona_staged_cell_feedback_radius4_rejections} immediately in ${stagedCells.corona_staged_cell_feedback_continuation_nodes} aggregate nodes, and independent replay verifies all ${stagedCells.corona_staged_cell_feedback_replayed_clause_instances} learned clause instances with ${stagedCells.corona_staged_cell_feedback_replay_failures} failures. A matched joint clause-and-cell schedule returns ${stagedCells.corona_joint_feedback_matched_states} states rather than ${stagedCells.corona_staged_cell_feedback_matched_staged_states}, so it is not the production policy; however, ${stagedCells.corona_joint_feedback_new_states} are new beyond the whole prior portfolio, raising the exact corpus to ${stagedCells.corona_joint_feedback_combined_distinct_states} distinct states. GCTS rejects all ${stagedCells.corona_joint_feedback_radius4_rejections} immediately, and replay verifies ${stagedCells.corona_joint_feedback_replayed_clauses} more clauses with ${stagedCells.corona_joint_feedback_replay_failures} failures, so joint staging remains a complementary diversity lane. Relaxing the cap to ${stagedCells.corona_relaxed_copy_bound} adds ${stagedCells.corona_relaxed_copy_bound_new_states} further states, including ${stagedCells.corona_relaxed_copy_bound_40_copy_states} with 40 surrounding copies, for ${stagedCells.corona_relaxed_copy_bound_combined_distinct_states} distinct states overall. Same-process timeout escalation then extends the matched run from ${stagedCells.corona_timeout_retry_matched_no_retry_states} to ${stagedCells.corona_timeout_retry_states} states without rebuilding the solver, adding ${stagedCells.corona_timeout_retry_41_copy_states} new 41-copy states and raising the exact corpus to ${stagedCells.corona_timeout_retry_combined_distinct_states}. Exact partition restarts add ${stagedCells.corona_partition_restart_new_states} states and advance to ${stagedCells.corona_partition_restart_applied_cells} applied cells. At that frontier a four-cell step toward ${stagedCells.corona_frontier_large_batch_cells} times out, while one-cell steps reach ${stagedCells.corona_frontier_small_batch_cells}, add ${stagedCells.corona_frontier_small_batch_new_states} more 42-copy states, and raise the exact corpus to ${stagedCells.corona_frontier_combined_distinct_states}. Transactional feedback now automates that recovery: on the matched hard seed it rolls back ${stagedCells.corona_transactional_feedback_backoff_rollbacks} timed-out increments before a one-cell step succeeds; on another seed the four-cell step solves directly and reaches ${stagedCells.corona_transactional_feedback_maximum_applied_cells} applied cells. These add ${stagedCells.corona_transactional_feedback_new_states} states for ${stagedCells.corona_transactional_feedback_combined_distinct_states} distinct states overall, with ${stagedCells.corona_transactional_feedback_direct_replayed_clauses} and ${stagedCells.corona_transactional_feedback_backoff_replayed_clauses} clauses independently replayed and ${stagedCells.corona_transactional_feedback_replay_failures} failures. Retained feedback then contributes ${stagedCells.corona_retained_feedback_new_states} more distinct states, advances the exact prefix to ${stagedCells.corona_retained_feedback_maximum_applied_cells} applied cells, and raises the corpus to ${stagedCells.corona_retained_feedback_combined_distinct_states}. GCTS rejects both new states immediately in ${stagedCells.corona_retained_feedback_continuation_nodes} nodes; independent replay verifies the ${stagedCells.corona_retained_feedback_seed200_replayed_clauses}- and ${stagedCells.corona_retained_feedback_seed203_replayed_clauses}-clause reports with ${stagedCells.corona_retained_feedback_replay_failures} failures. A fresh seed still times out on the minimum 2-clause/1-cell step at that frontier. The ≤${stagedCells.corona_relaxed_copy_bound}-copy proposal space is unexhausted, so this proves neither non-tiling nor aperiodicity.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_partial_formula_cache_commit) {
        const cache = candidate.screening;
        const cacheReduction = (100 * cache.corona_partial_formula_cache_construction_reduction_fraction).toFixed(1);
        candidateResearchDetail.textContent += ` Exact partial-formula caching keys the base solver formula to the applied cell prefix and cuts matched construction from ${(cache.corona_partial_formula_cache_miss_construction_ms / 1000).toFixed(1)} seconds to ${(cache.corona_partial_formula_cache_hit_construction_ms / 1000).toFixed(2)} seconds (${cacheReduction}%). Cache-backed seeds add ${cache.corona_partial_formula_cache_new_states} distinct 42-copy states, advance from 41 to ${cache.corona_partial_formula_cache_maximum_applied_cells} applied cells, and raise the exact corpus to ${cache.corona_partial_formula_cache_combined_distinct_states}. GCTS rejects both immediately in ${cache.corona_partial_formula_cache_continuation_nodes} nodes; independent replay verifies ${cache.corona_partial_formula_cache_seed208_replayed_clauses} and ${cache.corona_partial_formula_cache_seed210_replayed_clauses} clauses with ${cache.corona_partial_formula_cache_replay_failures} failures. The cache-miss control remains ${cache.corona_partial_formula_cache_seed209_status}; the ≤42-copy space is unexhausted, so neither non-tiling nor aperiodicity is established.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_deep_cached_prefix_combined_distinct_states) {
        const deepPrefix = candidate.screening;
        candidateResearchDetail.textContent += ` Retained one-cell restarts then add new ${deepPrefix.corona_deep_cached_prefix_seed211_placements}- and ${deepPrefix.corona_deep_cached_prefix_seed212_placements}-copy states, advance the exact prefix to ${deepPrefix.corona_deep_cached_prefix_maximum_applied_cells} applied cells, and raise the bounded corpus to ${deepPrefix.corona_deep_cached_prefix_combined_distinct_states} states. Exact GCTS rejects both at radius four in ${deepPrefix.corona_deep_cached_prefix_continuation_nodes} aggregate nodes, while independent replay verifies all ${deepPrefix.corona_deep_cached_prefix_seed211_replayed_clauses} and ${deepPrefix.corona_deep_cached_prefix_seed212_replayed_clauses} accumulated clauses with ${deepPrefix.corona_deep_cached_prefix_replay_failures} failures. The proposal space is still unexhausted.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_prefix45_diversification_combined_distinct_states) {
        const diversified = candidate.screening;
        const constructionReduction = (100 * diversified.corona_prefix45_diversification_construction_reduction_fraction).toFixed(1);
        candidateResearchDetail.textContent += ` Matched diversification at the 45-cell prefix adds distinct 41- and ${diversified.corona_prefix45_diversification_minimum_placements}-copy states and converges to byte-identical ${diversified.corona_prefix45_diversification_maximum_applied_cells}-cell applied reports. The cache hit cuts construction by ${constructionReduction}% and the bounded corpus reaches ${diversified.corona_prefix45_diversification_combined_distinct_states} states. GCTS rejects both new states immediately in ${diversified.corona_prefix45_diversification_continuation_nodes} aggregate nodes; independent replay verifies ${diversified.corona_prefix45_diversification_seed213_replayed_clauses} and ${diversified.corona_prefix45_diversification_seed214_replayed_clauses} clauses with ${diversified.corona_prefix45_diversification_replay_failures} failures. No radius-four survivor has been found and the search remains unexhausted.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_retained_three_step_combined_distinct_states) {
        const chain = candidate.screening;
        candidateResearchDetail.textContent += ` A retained three-step solver chain then advances the exact prefix from 46 to ${chain.corona_retained_three_step_maximum_applied_cells} cells without reconstructing either successful intermediate formula. Its ${chain.corona_retained_three_step_new_states} independently verified ${chain.corona_retained_three_step_minimum_placements}- or 41-copy states raise the bounded corpus to ${chain.corona_retained_three_step_combined_distinct_states}. GCTS rejects all three at radius four in ${chain.corona_retained_three_step_continuation_nodes} aggregate nodes, and replay verifies all ${chain.corona_retained_three_step_replayed_clauses} accumulated clauses with ${chain.corona_retained_three_step_replay_failures} failures. The ≤42-copy proposal space remains unexhausted.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_retained_five_step_combined_distinct_states) {
        const longChain = candidate.screening;
        candidateResearchDetail.textContent += ` A longer retained chain succeeds at five further one-cell increments, reaching ${longChain.corona_retained_five_step_maximum_applied_cells} applied cells while avoiding ${longChain.corona_retained_five_step_reconstructions_avoided} formula reconstructions. Its ${longChain.corona_retained_five_step_new_states} independently verified ${longChain.corona_retained_five_step_minimum_placements}–${longChain.corona_retained_five_step_maximum_placements}-copy states raise the bounded corpus to ${longChain.corona_retained_five_step_combined_distinct_states}. All five fail radius-four continuation immediately in ${longChain.corona_retained_five_step_continuation_nodes} aggregate nodes, and replay verifies all ${longChain.corona_retained_five_step_replayed_clauses} clauses with ${longChain.corona_retained_five_step_replay_failures} failures. Same-process retention is now the production frontier policy; the search remains unexhausted.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_bounded_exhaustion_independent_unsat_runs) {
        const bounded = candidate.screening;
        const constructionReduction = (100 * bounded.corona_bounded_exhaustion_construction_reduction_fraction).toFixed(1);
        const timeoutControlLabel = bounded.corona_widened_exhaustion_unknown_runs === 1 ? "control" : "controls";
        candidateResearchDetail.textContent += ` The final retained chain adds ${bounded.corona_bounded_exhaustion_new_states} more verified states and reaches ${bounded.corona_bounded_exhaustion_maximum_verified_cells} applied cells. At ${bounded.corona_bounded_exhaustion_certificate_cells} cells, ${bounded.corona_bounded_exhaustion_base_independent_unsat_runs} independent solver seeds first agree on exact UNSAT through ${bounded.corona_bounded_exhaustion_base_maximum_placements} copies for byte-identical ${bounded.corona_bounded_exhaustion_applied_clauses}-clause formulas; the cache hit cuts construction by ${constructionReduction}%. Raising the cap to ${bounded.corona_bounded_exhaustion_maximum_placements} gives another exact UNSAT on seed ${bounded.corona_widened_exhaustion_unsat_seed}, alongside ${bounded.corona_widened_exhaustion_unknown_runs} timeout/rollback ${timeoutControlLabel}. This exhausts the ≤${bounded.corona_bounded_exhaustion_maximum_placements}-copy radius-three proposal stratum as a source of radius-four survivors, after ${bounded.corona_bounded_exhaustion_combined_distinct_states} verified bounded states and ${bounded.corona_bounded_exhaustion_replayed_clauses} replayed obstruction clauses. It does not exhaust larger coronas and proves neither non-tiling nor aperiodicity.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_copy47_48_frontier_report) {
        const frontier = candidate.screening;
        candidateResearchDetail.textContent += ` The earlier ${frontier.corona_copy47_48_frontier_timeout_runs}-run audit isolated the then-open ${frontier.corona_copy47_48_frontier_minimum_open_placements}–${frontier.corona_copy47_48_frontier_maximum_open_placements}-copy band, but every exact solve timed out and rolled back. Exact-cardinality formulas replace ${frontier.corona_copy47_48_exact_count_constraints_before} opposing pseudo-Boolean bounds with ${frontier.corona_copy47_48_exact_count_constraints_after} equality, saving ${frontier.corona_copy47_48_exact_count_formula_bytes_saved.toLocaleString()} serialized bytes; that matched audit established no speedup or exhaustion.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_exact47_cube_exhausted) {
        const cubes = candidate.screening;
        candidateResearchDetail.textContent += ` Exhaustive placement-cube decomposition subsequently partitions all ${cubes.corona_exact47_cube_anchor_candidates} ways to cover anchor cell ${cubes.corona_exact47_cube_anchor_cell} into ${cubes.corona_exact47_cube_branch_leaves} disjoint UNSAT leaves with an identical base-formula digest, closing exact count 47.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_exact48_49_cube_exhausted) {
        const cubes = candidate.screening;
        candidateResearchDetail.textContent += ` Two further digest-checked covers use ${cubes.corona_exact48_49_cube_branch_leaves} total leaves to close exact counts ${cubes.corona_exact48_49_cube_counts.join(" and ")}.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_exact50_cube_exhausted) {
        const cubes = candidate.screening;
        candidateResearchDetail.textContent += ` An ${cubes.corona_exact50_cube_branch_leaves}-leaf cover then closes exact count 50.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_exact51_adaptive_cube_exhausted) {
        const cubes = candidate.screening;
        candidateResearchDetail.textContent += ` The resumable adaptive runner closes exact count 51 with ${cubes.corona_exact51_adaptive_cube_branch_leaves} verified leaves after ${cubes.corona_exact51_adaptive_cube_solver_launches} solver launches; replay reuses all ${cubes.corona_exact51_adaptive_cube_resumed_branches} branch reports with ${cubes.corona_exact51_adaptive_cube_resume_launches} new launches.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_exact52_53_adaptive_cube_exhausted) {
        const cubes = candidate.screening;
        candidateResearchDetail.textContent += ` The same runner closes exact counts ${cubes.corona_exact52_53_adaptive_cube_counts.join(" and ")} with ${cubes.corona_exact52_53_adaptive_cube_branch_leaves} verified leaves after ${cubes.corona_exact52_53_adaptive_cube_solver_launches} total launches; replay reuses all ${cubes.corona_exact52_53_adaptive_cube_resumed_branches} attempted reports with ${cubes.corona_exact52_53_adaptive_cube_resume_launches} new launches.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_exact54_55_adaptive_cube_exhausted) {
        const cubes = candidate.screening;
        candidateResearchDetail.textContent += ` A contiguous range run closes exact counts ${cubes.corona_exact54_55_adaptive_cube_counts.join(" and ")} with ${cubes.corona_exact54_55_adaptive_cube_branch_leaves} verified leaves after ${cubes.corona_exact54_55_adaptive_cube_solver_launches} total launches; it enters the second count only after certifying the first, and replay reuses all ${cubes.corona_exact54_55_adaptive_cube_resumed_branches} attempted reports with ${cubes.corona_exact54_55_adaptive_cube_resume_launches} new launches.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_exact56_60_adaptive_cube_exhausted) {
        const cubes = candidate.screening;
        candidateResearchDetail.textContent += ` Three more adaptive runs close every exact count from ${cubes.corona_exact56_60_adaptive_cube_counts.at(0)} through ${cubes.corona_exact56_60_adaptive_cube_counts.at(-1)} with ${cubes.corona_exact56_60_adaptive_cube_branch_leaves} verified leaves after ${cubes.corona_exact56_60_adaptive_cube_solver_launches} launches. Independent regeneration reproduces all five cover certificates byte for byte, and replay reuses all ${cubes.corona_exact56_60_adaptive_cube_resumed_branches} attempted reports with ${cubes.corona_exact56_60_adaptive_cube_resume_launches} new launches.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_exact61_62_prerefined_cube_exhausted) {
        const cubes = candidate.screening;
        candidateResearchDetail.textContent += ` Exact ${cubes.corona_exact61_62_prerefined_cube_counts[0]} initially leaves one singleton anchor unresolved at 60 seconds; a focused seed closes that same leaf, and an independent ${cubes.corona_exact61_62_prerefined_cube_branch_leaves / 2}-leaf union covers all 58 anchors. Exact ${cubes.corona_exact61_62_prerefined_cube_counts[1]} pre-refines recurrent hard cubes 0, 2, and 3 and closes with another ${cubes.corona_exact61_62_prerefined_cube_branch_leaves / 2}-leaf union. Across both counts the runner uses ${cubes.corona_exact61_62_prerefined_cube_runner_launches} attempts and the focused leaf adds ${cubes.corona_exact61_62_prerefined_cube_focused_launches} solve; replay reuses ${cubes.corona_exact61_62_prerefined_cube_resumed_reports} cached runner reports with ${cubes.corona_exact61_62_prerefined_cube_replay_launches} new launches.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_exact63_67_prerefined_cube_exhausted) {
        const cubes = candidate.screening;
        candidateResearchDetail.textContent += ` The corrected version-two runner closes every exact count from ${cubes.corona_exact63_67_prerefined_cube_counts.at(0)} through ${cubes.corona_exact63_67_prerefined_cube_counts.at(-1)} with ${cubes.corona_exact63_67_prerefined_cube_branch_leaves} verified leaves across ${cubes.corona_exact63_67_prerefined_cube_solver_launches} attempted reports. All five independently regenerated certificates are byte-identical; replay reuses all ${cubes.corona_exact63_67_prerefined_cube_resumed_reports} reports with ${cubes.corona_exact63_67_prerefined_cube_replay_launches} new launches. Exact 66 alone needs a true two-to-one-anchor refinement, and no configured singleton retry is used. Together with the earlier bounded certificates, this exhausts radius-three proposals through ${cubes.corona_verified_copy_bound} surrounding copies under the replayed necessary conditions. Copy ${cubes.corona_minimum_open_placements} and unrestricted radius three remain open, so this proves neither non-tiling nor aperiodicity.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_partial_coverability_report) {
        const partial = candidate.screening;
        const throughput = (100 * partial.corona_partial_coverability_nodes
          / partial.corona_partial_coverability_milliseconds
          / (partial.corona_partial_coverability_baseline_nodes
            / partial.corona_partial_coverability_baseline_milliseconds)).toFixed(1);
        candidateResearchDetail.textContent += ` An optional exact partial-patch rule now waits until ${partial.corona_partial_coverability_min_placements} surrounding copies, then rejects a branch as soon as any next-ring cell has no compatible placement. In the matched run it replaced ${partial.corona_partial_coverability_baseline_continuation_checks} doomed complete-patch continuation checks with ${partial.corona_partial_coverability_prunes} earlier prunes and performed ${partial.corona_partial_coverability_nodes.toLocaleString()} outer nodes (${throughput}% of baseline throughput).${candidate.id === "p9-42947" ? ` A longer run still reached only depth ${partial.corona_partial_coverability_long_maximum_depth}, so the maintenance cost does not yet buy a deeper state for this candidate.` : ` Two fresh orderings add ${partial.corona_partial_coverability_validation_nodes.toLocaleString()} nodes and ${partial.corona_partial_coverability_validation_prunes} exact early prunes without reaching a complete proposal; proposal supply is now the bottleneck.`} The finite outer search remains unexhausted.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_placement_order_report) {
        const ordering = candidate.screening;
        candidateResearchDetail.textContent += candidate.id === "p9-42947"
          ? ` A seeded-first exact row ordering reaches a distinct ${ordering.corona_seeded_order_proposal_placements}-copy radius-four boundary state after ${ordering.corona_seeded_order_validation_nodes.toLocaleString()} nodes across three restarts. Exact radius-five continuation rejects it in ${ordering.corona_seeded_order_continuation_nodes} node with a ${ordering.corona_seeded_order_obstruction_clause_size}-placement clause; the other two seeded restarts produce no complete proposal, so this remains a diversity lane rather than the default.`
          : ` A matched three-profile ordering ablation leaves compact-first search as the best observed supplier: it reaches ${ordering.corona_placement_order_compact_complete_proposals} complete proposals while expansive-first and seeded-first reach ${ordering.corona_placement_order_alternative_complete_proposals}. Alternative ordering remains an exact optional restart, not a claimed improvement.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_high_copy_cegar_report) {
        const highCopy = candidate.screening;
        candidateResearchDetail.textContent += ` Minimum-copy CEGAR supplies ${highCopy.corona_high_copy_cegar_states_checked} further clause-distinct radius-four states using ${highCopy.corona_high_copy_cegar_minimum_placements}–${highCopy.corona_high_copy_cegar_maximum_placements} surrounding copies. Exact radius-five continuation rejects all of them in ${highCopy.corona_high_copy_cegar_continuation_nodes} aggregate nodes and retains ${highCopy.corona_high_copy_cegar_symmetry_closed_clauses} symmetry-closed clauses. ${highCopy.corona_high_copy_cegar_lightweight_timeout_runs} lightweight and ${highCopy.corona_high_copy_cegar_eager_timeout_runs} one-step-coverable proposal runs time out, so the high-copy space remains unexhausted.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_staged_coverability_report) {
        const staged = candidate.screening;
        candidateResearchDetail.textContent += ` A grouped pseudo-Boolean encoding compresses ${staged.corona_staged_coverability_logical_conflict_edges.toLocaleString()} exact outer/lookahead conflict implications into ${staged.corona_staged_coverability_grouped_conflicts.toLocaleString()} groups and ${staged.corona_staged_coverability_asserted_constraints.toLocaleString()} total asserted constraints. It supplies ${staged.corona_staged_coverability_states_checked} radius-four states with ${staged.corona_staged_coverability_minimum_placements}–${staged.corona_staged_coverability_maximum_placements} copies in which every next-ring cell is individually coverable. Radius-five GCTS rejects all ${staged.corona_staged_coverability_resolved_subtree_states} through genuine resolved-subtree conflicts in ${staged.corona_staged_coverability_continuation_nodes} aggregate nodes (maximum ${staged.corona_staged_coverability_maximum_continuation_nodes}), while lazy learning grows to ${staged.corona_staged_coverability_pair_constraints} symmetry-expanded pair obligations. No radius-five witness is found and the outer search remains unexhausted.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_higher_order_coverability_report) {
        const higher = candidate.screening;
        candidateResearchDetail.textContent += ` Higher-order CEGAR extends this to ${higher.corona_higher_order_states_checked} exact full-single-coverability states with ${higher.corona_higher_order_minimum_placements}–${higher.corona_higher_order_maximum_placements} copies, rejected in ${higher.corona_higher_order_continuation_nodes} aggregate radius-five nodes (maximum ${higher.corona_higher_order_maximum_continuation_nodes}). Systematic and lazy learning reaches ${higher.corona_higher_order_pair_constraints} pair and ${higher.corona_higher_order_triple_constraints} triple obligations. A ${higher.corona_higher_order_pairwise_triplewise_state_placements}-copy state independently passes every pair and every triple on the full 180-cell next ring, yet GCTS rejects it in ${higher.corona_higher_order_pairwise_triplewise_state_continuation_nodes} nodes; its first audited local inconsistency is a diameter-${higher.corona_higher_order_first_quadruple_diameter} quadruple blocking ${higher.corona_higher_order_first_quadruple_candidate_combinations} placement combinations. This raises the observed obstruction order to four, but still proves neither non-tiling nor aperiodicity.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_quadruple_coverability_report) {
        const quadruple = candidate.screening;
        candidateResearchDetail.textContent += ` The exact proposal solver now encodes that quadruple's ${quadruple.corona_quadruple_constraints}-member symmetry orbit directly. It supplies ${quadruple.corona_quadruple_states_checked} further ${quadruple.corona_quadruple_minimum_placements}–${quadruple.corona_quadruple_maximum_placements}-copy states, all rejected by radius-five GCTS in ${quadruple.corona_quadruple_continuation_nodes} aggregate nodes; the deepest survives ${quadruple.corona_quadruple_maximum_continuation_nodes} nodes. These new states expose ${quadruple.corona_quadruple_pair_defect_states} still-missing pair cases and ${quadruple.corona_quadruple_triple_defect_states} pairwise-complete but triple-defective cases, growing the formula to ${quadruple.corona_quadruple_pair_constraints} pair and ${quadruple.corona_quadruple_triple_constraints} triple obligations. Thus excluding one order-four defect improves the benchmark but does not complete the lower-order screen or prove aperiodicity.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_batched_triple_report) {
        const batch = candidate.screening;
        candidateResearchDetail.textContent += ` Complete per-state triple batching then checks ${batch.corona_batched_triple_states_checked} more exact dead states. Its ${batch.corona_batched_triple_triple_defect_states} pairwise-complete proposals contribute ${batch.corona_batched_triple_orbits_added} triple orbits in six audits, growing the carried formula to ${batch.corona_batched_triple_final_pair_constraints} pair, ${batch.corona_batched_triple_final_triple_constraints} triple, and ${batch.corona_batched_triple_final_quadruple_constraints} quadruple obligations. At that strength ${batch.corona_batched_triple_final_four_timeouts} of the final four outer solves time out, shifting the bottleneck from repeated tuple discovery to the monolithic proposal formula; this remains inconclusive.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_lazy_higher_report) {
        const lazy = candidate.screening;
        candidateResearchDetail.textContent += ` A matched lazy-higher ablation keeps pair obligations in Z3 but audits triples and quadruples exactly after each proposal. From the identical saved formula and four seeds, proposal yield rises from ${lazy.corona_lazy_higher_encoded_sat_states}/${lazy.corona_lazy_higher_matched_trials} with ${lazy.corona_lazy_higher_encoded_timeouts} timeouts to ${lazy.corona_lazy_higher_sat_states}/${lazy.corona_lazy_higher_matched_trials} with none; every returned state has a sound tuple obstruction before GCTS. Eight chained restarts add ${lazy.corona_lazy_higher_extension_pair_defect_states} pair-defective and ${lazy.corona_lazy_higher_extension_triple_defect_states} pairwise-complete but triple-defective states, reaching ${lazy.corona_lazy_higher_final_pair_constraints} pair, ${lazy.corona_lazy_higher_final_triple_constraints} triple, and ${lazy.corona_lazy_higher_final_quadruple_constraints} quadruple obligations. No tuple-complete radius-four state or radius-five witness appears, so the next target is hybrid proposal steering, not an aperiodicity claim.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_hybrid_higher_report) {
        const hybrid = candidate.screening;
        candidateResearchDetail.textContent += ` Hybrid-higher screening encodes just ${hybrid.corona_hybrid_higher_encoded_triple_orbits} complete triple orbit and audits the rest lazily. It returns all four matched proposals without timeout and cuts their aggregate Z3 time by ${(100 * hybrid.corona_hybrid_higher_matched_runtime_reduction_fraction).toFixed(1)}% versus fully lazy screening; encoding ${hybrid.corona_hybrid_higher_large_subset_timeout_orbits} unranked orbits already times out. Across the chained fixed and recent-orbit lanes, ${hybrid.corona_hybrid_higher_chain_sat_states} exact proposals expose ${hybrid.corona_hybrid_higher_pair_defect_states} pair and ${hybrid.corona_hybrid_higher_triple_defect_states} triple defects, growing the formula to ${hybrid.corona_hybrid_higher_final_pair_constraints} pair, ${hybrid.corona_hybrid_higher_final_triple_constraints} triple, and ${hybrid.corona_hybrid_higher_final_quadruple_constraints} quadruple obligations.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_ranked_hybrid_report) {
        const ranked = candidate.screening;
        candidateResearchDetail.textContent += ` Persistent impact ranking then follows the triple orbit observed to block ${ranked.corona_ranked_hybrid_selected_score} candidate combinations. Six more exact proposals expose ${ranked.corona_ranked_hybrid_pair_defect_states} pair and ${ranked.corona_ranked_hybrid_triple_defect_states} triple defects, reaching ${ranked.corona_ranked_hybrid_final_pair_constraints} pair, ${ranked.corona_ranked_hybrid_final_triple_constraints} triple, and ${ranked.corona_ranked_hybrid_final_quadruple_constraints} quadruple obligations. The ranked orbit changes as intended, but no proposal clears the full triple audit and each solve still takes minutes. This remains an unresolved benchmark, not evidence of non-tiling or aperiodicity; retaining outer-solver state is now the main performance target.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_formula_cache_report) {
        const cache = candidate.screening;
        candidateResearchDetail.textContent += ` Validated formula caching now reuses the static exact-cover/lookahead formula and all ${cache.corona_formula_cache_pair_constraints} accumulated pair constraints across solver seeds while rebuilding higher-order steering and forbidden-state clauses. In a matched two-iteration driver profile, construction falls from ${(cache.corona_formula_cache_miss_construction_ms / 1000).toFixed(1)}s to ${(cache.corona_formula_cache_hit_construction_ms / 1000).toFixed(1)}s (${(100 * cache.corona_formula_cache_construction_reduction_fraction).toFixed(1)}%), reducing total one-second-probe wall time by ${(100 * cache.corona_formula_cache_total_reduction_fraction).toFixed(1)}%. This is a search-throughput improvement only; both timed checks are inconclusive.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_cached_ranked_extension_report) {
        const extension = candidate.screening;
        candidateResearchDetail.textContent += ` The cached one-orbit ranked extension returns ${extension.corona_cached_ranked_sat_states} exact proposals with ${extension.corona_cached_ranked_timeout_trials} timeout: ${extension.corona_cached_ranked_triple_defect_states} consecutive states clear every accumulated pair check before failing the full triple audit, while one exposes a new pair orbit. The screen now carries ${extension.corona_cached_ranked_final_pair_constraints} pair, ${extension.corona_cached_ranked_final_triple_constraints} triple, and ${extension.corona_cached_ranked_final_quadruple_constraints} quadruple obligations. A separate two-highest-impact-orbit solve also times out. No proposal clears the full triple audit, so no radius-five GCTS continuation starts and the candidate remains unresolved.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_batched_solver_state_report) {
        const batch = candidate.screening;
        candidateResearchDetail.textContent += ` Exact retained-state batching can request ${batch.corona_batched_solver_requested_witnesses} distinct Boolean models without rebuilding Z3. On the positive control it learns from one model and verifies the next through GCTS. On this candidate, seed 302 returns one proposal after ${(batch.corona_batched_solver_first_check_ms / 1000).toFixed(1)}s, exposes a new pair orbit, then spends ${(batch.corona_batched_solver_second_check_ms / 1000).toFixed(1)}s without a second model. The carried screen reaches ${batch.corona_batched_solver_final_pair_constraints} pair and ${batch.corona_batched_solver_final_triple_constraints} triple obligations. Blind batching is therefore not the answer here; the next solver should accept each audited obstruction interactively before continuing its retained search.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_interactive_z3_report) {
        const interactive = candidate.screening;
        candidateResearchDetail.textContent += ` Bidirectional retained CEGAR now does that: it asserts every audited state clause and new pair obligation inside the same Z3 process before requesting another model. Three sessions return ${interactive.corona_interactive_z3_sat_states}/${interactive.corona_interactive_z3_sat_states} exact proposals with no timeout—${interactive.corona_interactive_z3_pair_defect_states} pair-defective and ${interactive.corona_interactive_z3_triple_defect_states} pairwise-complete but triple-defective. In production, ${interactive.corona_interactive_z3_pair_feedback_applied} newly learned pair constraints are applied before the next check, whose model clears the enlarged pair audit and reaches the triple audit. The portfolio advances to ${interactive.corona_interactive_z3_final_pair_constraints} pair, ${interactive.corona_interactive_z3_final_triple_constraints} triple, and ${interactive.corona_interactive_z3_final_quadruple_constraints} quadruple obligations. No proposal clears the full triple audit, so the candidate remains unresolved.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_ranked_pair_window_report) {
        const rankedPairs = candidate.screening;
        candidateResearchDetail.textContent += ` Pair-level impact ranking now keeps the full ${rankedPairs.corona_interactive_z3_final_pair_constraints}-constraint audit but initially steers Z3 with only the strongest ${rankedPairs.corona_ranked_pair_window_orbits} symmetry orbits (${rankedPairs.corona_ranked_pair_window_constraints} constraints). In the matched seed, that window constructs in ${(rankedPairs.corona_ranked_pair_window_construction_ms / 1000).toFixed(1)}s and returns an exact proposal after ${(rankedPairs.corona_ranked_pair_window_check_ms / 1000).toFixed(1)}s; loading every pair takes ${(rankedPairs.corona_ranked_pair_full_construction_ms / 1000).toFixed(1)}s and then times out after ${(rankedPairs.corona_ranked_pair_full_check_ms / 1000).toFixed(1)}s. A retained follow-up returns ${rankedPairs.corona_ranked_pair_retained_sat_states} more pair-defective states while asserting ${rankedPairs.corona_ranked_pair_feedback_constraints} promoted constraints, then times out. This improves proposal throughput without relaxing the exact gate; it still supplies no radius-five witness or aperiodicity evidence.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_replaceable_pair_window_report) {
        const replacement = candidate.screening;
        candidateResearchDetail.textContent += ` Ranked pair steering is now genuinely replaceable: activation assumptions hold the live window fixed while compiled inactive formulas remain cached. A changed window can construct in ${(replacement.corona_replaceable_pair_fast_construction_ms / 1000).toFixed(1)}s and return an exact state in ${(replacement.corona_replaceable_pair_fast_check_ms / 1000).toFixed(1)}s. The expanded portfolio returns ${replacement.corona_replaceable_pair_sat_states} exact states and records ${replacement.corona_replaceable_pair_timeout_trials} timeouts; all ${replacement.corona_replaceable_pair_defect_states} returned states fail the complete pair audit. Windows of 32 and 64 orbits solve in ${(replacement.corona_replaceable_pair_window32_check_ms / 1000).toFixed(1)}s and ${(replacement.corona_replaceable_pair_window64_check_ms / 1000).toFixed(1)}s but remain pair-defective, while 128 orbits times out. The screen now carries ${replacement.corona_replaceable_pair_final_constraints} pair constraints and ${replacement.corona_replaceable_pair_final_clauses} verified state clauses. This is stronger screening and faster proposal generation, not a non-tiling or aperiodicity certificate.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_pair_recurrence_report) {
        const recurrence = candidate.screening;
        candidateResearchDetail.textContent += ` A deduplicated replay independently verifies ${recurrence.corona_pair_recurrence_verified_states} historical radius-four states; ${recurrence.corona_pair_recurrence_eligible_states} satisfy the current individual-coverability contract and expose ${recurrence.corona_pair_recurrence_orbits} recurrent pair orbits. Of these states, ${recurrence.corona_pair_recurrence_pair_defect_states} fail pair coverability and ${recurrence.corona_pair_recurrence_pair_complete_states} clear it; ${recurrence.corona_pair_recurrence_triple_defect_states} of the latter fail the bounded triple gate, and the final one fails a quadruple obstruction, leaving ${recurrence.corona_pair_recurrence_tuple_survivors} GCTS continuation targets. Recurrence is therefore recorded but not promoted blindly: in a matched 16-orbit probe, impact-only solves in ${(recurrence.corona_pair_recurrence_impact_check_ms / 1000).toFixed(1)}s with ${recurrence.corona_pair_recurrence_impact_defects} pair defects, versus ${(recurrence.corona_pair_recurrence_frequency_check_ms / 1000).toFixed(1)}s/${recurrence.corona_pair_recurrence_frequency_defects} for frequency-first and ${(recurrence.corona_pair_recurrence_weighted_check_ms / 1000).toFixed(1)}s/${recurrence.corona_pair_recurrence_weighted_defects} for frequency-weighted impact. Impact-only remains the production lane. These are bounded finite-patch screens, not a non-tiling or aperiodicity certificate.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_historical_cover_report) {
        const cover = candidate.screening;
        candidateResearchDetail.textContent += ` Joint historical coverage preserves all ${cover.corona_historical_cover_defect_sets} per-state defect sets instead of flattening them into marginal counts. Its greedy 16-orbit window intersects ${cover.corona_historical_cover_sets_covered} replayed failures, versus ${cover.corona_historical_impact_sets_covered} for impact-only. Across three matched seeds both lanes return three exact states; historical-cover uses ${(cover.corona_historical_cover_total_check_ms / 1000).toFixed(1)}s total and exposes ${cover.corona_historical_cover_total_pair_defects} pair defects, versus ${(cover.corona_historical_impact_total_check_ms / 1000).toFixed(1)}s and ${cover.corona_historical_impact_total_pair_defects}. This modest aggregate improvement earns it a complementary diversity lane, not a replacement for impact-only: neither produces a pair-complete state, so no new GCTS continuation begins.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_historical_core_report) {
        const core = candidate.screening;
        candidateResearchDetail.textContent += ` A stricter historical-core lane identifies ${core.corona_historical_core_singleton_states} failed states whose sole pair defect belongs to ${core.corona_historical_core_singleton_orbits} distinct orbits, and protects all of those orbits in a 32-orbit window before greedily covering the rest. It intersects ${core.corona_historical_core_sets_covered} historical failures, versus ${core.corona_historical_core_control_sets_covered} for ordinary historical-cover. Across matched seeds 325–327, however, the protected core needs ${(core.corona_historical_core_total_check_ms / 1000).toFixed(1)}s and leaves ${core.corona_historical_core_total_pair_defects} defects, versus ${(core.corona_historical_core_control_check_ms / 1000).toFixed(1)}s and ${core.corona_historical_core_control_pair_defects}; it finds ${core.corona_historical_core_new_pair_orbits} new pair orbit but no pair-complete state. Historical-core is therefore retained only as a proposal-diversity lane, not promoted to production, and supplies no radius-five or aperiodicity evidence.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_adaptive_pair_report) {
        const adaptive = candidate.screening;
        candidateResearchDetail.textContent += ` Retained CEGAR can now reserve a bounded prefix of the live pair window for the exact defect set from its preceding proposal, with each trial reporting whether that response is complete. A complete 32-orbit response initially reduces nine defects to four, but across three matched models it needs ${(adaptive.corona_adaptive_pair_total_check_ms / 1000).toFixed(1)}s and ${adaptive.corona_adaptive_pair_replacement_constraints} replacement constraints for ${adaptive.corona_adaptive_pair_total_defects} defects; ordinary historical-cover needs ${(adaptive.corona_adaptive_pair_control_check_ms / 1000).toFixed(1)}s and ${adaptive.corona_adaptive_pair_control_replacement_constraints} replacements for ${adaptive.corona_adaptive_pair_control_defects}. Both discover ${adaptive.corona_adaptive_pair_new_orbits} new pair orbits. Bounding the response to four orbits still times out on its next check. Even a 64-orbit window that intersects all ${adaptive.corona_historical_cover64_sets_covered} historical defect sets returns a fresh state with ${adaptive.corona_historical_cover64_pair_defects} pair defects, and its cache-identical replay times out. Ordinary historical-cover remains the production lane; no pair-complete state or radius-five GCTS start is obtained.`;
      }
      if (candidate.kind === "polycube_census" && candidate.screening.corona_soft_pair_quota_report) {
        const soft = candidate.screening;
        candidateResearchDetail.textContent += ` Soft global pair steering now supports both constraint quotas and complete root-symmetry-orbit quotas while retaining the exact lazy audit. Across matched seeds 330–332, asking Z3 to satisfy at least 72 of 96 ranked constraints takes ${(soft.corona_soft_pair_quota_total_check_ms / 1000).toFixed(1)}s and exposes ${soft.corona_soft_pair_quota_total_defects} full-audit defects; making all 96 hard takes ${(soft.corona_soft_pair_hard_total_check_ms / 1000).toFixed(1)}s with the same ${soft.corona_soft_pair_hard_total_defects} defects. A quota of 84 is also slower and exposes ${soft.corona_soft_pair_quota84_defects} defects. At the symmetry-correct orbit level, 24 of 32 times out, while 16 of 32 takes ${(soft.corona_soft_pair_orbit16_check_ms / 1000).toFixed(1)}s with ${soft.corona_soft_pair_orbit16_defects} defects, versus ${(soft.corona_soft_pair_hard_seed330_check_ms / 1000).toFixed(1)}s/${soft.corona_soft_pair_hard_seed330_defects} for the hard control. Hard historical-cover remains production; no quota state clears the pair gate or starts radius-five GCTS.`;
      }
    }
  } else if (knownAperiodic) {
    candidateResearchTitle.textContent = "Known weakly aperiodic monotile";
    candidateResearchDetail.textContent = "Integral 3–4–5 Schmitt–Conway–Danzer biprism. Free-range shows the published rotated-layer construction; mirror copies must remain disabled.";
  }
}

function renderSystemTileList() {
  systemTileList.replaceChildren();
  for (const group of groupedCatalogFigures()) {
    const section = document.createElement("section");
    section.className = "catalog-group";
    const heading = document.createElement("h3");
    heading.className = "catalog-group-title";
    heading.textContent = group.title;
    const grid = document.createElement("div");
    grid.className = "catalog-group-grid";

    for (const figure of group.figures) {
      const selected = selectedFigureIds.includes(figure.id);
      const compatible = !!figure.census_candidate || !!figure.aperiodic_tile || isFigureCompatibleWithSelection(figure);
      const row = document.createElement("button");
      row.type = "button";
      row.className = "figure-card";
      row.classList.toggle("is-root", figure.id === selectedFigureIds[0]);
      row.classList.toggle("is-selected", selected);
      row.classList.toggle("is-incompatible", !selected && !compatible);
      row.disabled = !selected && !compatible;
      row.setAttribute("aria-checked", String(selected));
      row.setAttribute("aria-disabled", String(!selected && !compatible));
      const angleTitle = solidAngleTitle(figure.solid_angles);
      row.title = !selected && !compatible
        ? `No compatible lattice face with the current selection.\n${angleTitle}`
        : angleTitle;
      row.addEventListener("click", () => {
        if (selected) {
          selectedFigureIds = selectedFigureIds.filter(id => id !== figure.id);
        } else if (figure.census_candidate || figure.aperiodic_tile) {
          selectedFigureIds = [figure.id];
          applyCandidateSearchPreset({ invalidate: false });
        } else if (compatible && !selectedFigureIds.includes(figure.id)) {
          selectedFigureIds.push(figure.id);
        }
        handleFigureSelectionChanged();
      });

      const image = document.createElement("img");
      image.alt = prettyName(figure.name);
      image.src = figureThumbnail(figure);
      const name = document.createElement("div");
      name.className = "figure-card-title";
      name.textContent = prettyName(figure.name);
      name.title = `${figureSourceTitle(figure)}: ${prettyName(figure.name)}\n${angleTitle}`;
      const angles = document.createElement("div");
      angles.className = "figure-card-angles";
      if (figure.census_candidate) {
        const certificate = figure.census_candidate.screening?.certificate;
        angles.textContent = ["translational", "isohedral_periodic_quotient"].includes(certificate)
          ? `${figure.census_candidate.screening.motif_tiles}-tile periodic quotient · ${figure.census_candidate.kind === "polycube_census" ? `${figure.census_candidate.volume} cubes` : `${figure.census_candidate.lattice_points} points`}`
          : certificate === "complete_radius3_obstruction"
            ? `complete radius 3→4 obstruction · ${figure.census_candidate.volume} cubes`
          : figure.census_candidate.kind === "polycube_census"
          ? `period > ${figure.census_candidate.screening.periodic_exact_through
            ?? figure.census_candidate.screening.periodic_hnf_max_motif_tiles} · corona radius ${figure.census_candidate.screening.corona_completed_radius} · ${figure.census_candidate.volume} cubes`
          : ["finite_extendable_shell_obstruction", "finite_shell_obstruction"].includes(certificate)
            ? `${certificate === "finite_shell_obstruction" ? "complete-shell" : "dead-face shell"} ${figure.census_candidate.screening.shell_depth} obstruction · ${figure.census_candidate.lattice_points} points`
            : `survivor ${figure.census_candidate.survivor_priority}/${figure.census_candidate.survivor_count ?? 1} · ${figure.census_candidate.lattice_points} points`;
        angles.classList.add("is-census-label");
      } else {
        angles.innerHTML = solidAngleListHtml(figure.solid_angles);
      }
      row.append(image, name, angles);
      grid.appendChild(row);
    }

    section.append(heading, grid);
    systemTileList.appendChild(section);
  }
}

function refreshFigureSelectionUI() {
  renderSelectedTiles();
  renderSystemTileList();
  updateMirrorAvailability();
  updateCandidateResearchPanel();
}

function keyToVoxel(key) {
  return key.split(",").map(Number);
}

function voxelKey(voxel) {
  return voxel.join(",");
}

const AXIS_PERMUTATIONS = [
  [0, 1, 2], [0, 2, 1], [1, 0, 2],
  [1, 2, 0], [2, 0, 1], [2, 1, 0]
];
const SIGN_CHOICES = [
  [1, 1, 1], [1, 1, -1], [1, -1, 1], [1, -1, -1],
  [-1, 1, 1], [-1, 1, -1], [-1, -1, 1], [-1, -1, -1]
];

function normalizeVoxelList(voxels) {
  if (!voxels.length) return [];
  const mins = [Infinity, Infinity, Infinity];
  for (const voxel of voxels) for (let i = 0; i < 3; i++) mins[i] = Math.min(mins[i], voxel[i]);
  return voxels
    .map(v => [v[0] - mins[0], v[1] - mins[1], v[2] - mins[2]])
    .sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
}

function canonicalVoxelSignature(voxels) {
  if (!voxels.length) return "";
  let best = null;
  for (const perm of AXIS_PERMUTATIONS) {
    for (const signs of SIGN_CHOICES) {
      const transformed = voxels.map(v => [
        v[perm[0]] * signs[0],
        v[perm[1]] * signs[1],
        v[perm[2]] * signs[2]
      ]);
      const signature = normalizeVoxelList(transformed).map(voxelKey).join("|");
      if (best == null || signature < best) best = signature;
    }
  }
  return best;
}

function polycubeVoxelsFromTile(tile) {
  const scale = tileSpecs.SCALE;
  const voxels = [];
  for (const point of tile?.occupancy_points ?? []) {
    if (point.weight !== 48) continue;
    const voxel = point.pos.map(coord => (coord - 1) / scale);
    if (voxel.every(Number.isInteger)) voxels.push(voxel);
  }
  return voxels;
}

function listedPolycubeShapes() {
  if (listedPolycubeShapeMap) return listedPolycubeShapeMap;
  listedPolycubeShapeMap = new Map();
  for (const figure of figureCatalog) {
    if (!(figure.category ?? []).includes("Polycubes")) continue;
    const signature = canonicalVoxelSignature(polycubeVoxelsFromTile(tileForFigure(figure)));
    if (!signature) continue;
    const names = listedPolycubeShapeMap.get(signature) ?? [];
    const name = prettyName(figure.name);
    if (!names.includes(name)) names.push(name);
    listedPolycubeShapeMap.set(signature, names);
  }
  return listedPolycubeShapeMap;
}

function refreshCustomPolycubeIdentity() {
  const signature = canonicalVoxelSignature([...builderVoxels].map(keyToVoxel));
  if (signature === lastBuilderSignature) return;
  lastBuilderSignature = signature;
  const names = listedPolycubeShapes().get(signature) ?? [];
  const matchName = names[0];
  if (matchName) {
    customShapeMatch.textContent = `Matches ${matchName}`;
    if (!customNameEdited) {
      customNameInput.value = matchName;
      lastAutoCustomName = matchName;
    }
  } else {
    const count = builderVoxels.size;
    customShapeMatch.textContent = `${count} cube${count === 1 ? "" : "s"}`;
    if (!customNameEdited) {
      customNameInput.value = "Custom polycube";
      lastAutoCustomName = customNameInput.value;
    }
  }
}

function clearBuilderGroup() {
  while (builderGroup.children.length) builderGroup.children.pop();
}

function renderBuilderVoxels(fit = false) {
  refreshCustomPolycubeIdentity();
  clearBuilderGroup();
  const sorted = [...builderVoxels].sort();
  for (const key of sorted) {
    const [x, y, z] = keyToVoxel(key);
    const block = new THREE.Mesh(builderCubeGeometry, builderBlockMaterial);
    block.position.set(x, y, z);
    block.userData = { block: true, key, voxel: [x, y, z] };
    const edges = new THREE.LineSegments(builderEdgeGeometry, builderEdgeMaterial);
    edges.position.copy(block.position);
    edges.userData = { edge: true };
    builderGroup.add(block, edges);
  }
  if (builderHoverKey && !builderVoxels.has(builderHoverKey)) {
    const [x, y, z] = keyToVoxel(builderHoverKey);
    const ghost = new THREE.Mesh(builderCubeGeometry, builderGhostMaterial);
    ghost.position.set(x, y, z);
    ghost.userData = { ghost: true };
    builderGroup.add(ghost);
  }
  if (fit && builderControls) fitCameraToObject(builderCamera, builderControls, builderGroup, 2.35);
  requestBuilderRender();
}

function builderBlockIntersections(event) {
  if (!builderRenderer) return [];
  const rect = builderRenderer.domElement.getBoundingClientRect();
  builderPointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  builderPointer.y = -(((event.clientY - rect.top) / rect.height) * 2 - 1);
  builderRaycaster.setFromCamera(builderPointer, builderCamera);
  return builderRaycaster.intersectObjects(builderGroup.children.filter(child => child.userData.block), false);
}

function addTargetFromHit(hit) {
  const base = hit.object.userData.voxel;
  const normal = hit.face.normal;
  return [
    base[0] + Math.round(normal.x),
    base[1] + Math.round(normal.y),
    base[2] + Math.round(normal.z)
  ];
}

function handleBuilderPointerMove(event) {
  const hit = builderBlockIntersections(event)[0];
  const nextHover = hit ? voxelKey(addTargetFromHit(hit)) : null;
  if (nextHover === builderHoverKey) return;
  builderHoverKey = nextHover;
  renderBuilderVoxels();
}

function handleBuilderPointerDown(event) {
  const hit = builderBlockIntersections(event)[0];
  if (!hit) return;
  event.preventDefault();
  if (event.button === 2 || event.shiftKey || event.altKey) {
    const key = hit.object.userData.key;
    if (builderVoxels.size > 1) {
      builderVoxels.delete(key);
      builderHoverKey = null;
      renderBuilderVoxels();
      handleCustomPolycubeChanged();
    }
    return;
  }

  const target = addTargetFromHit(hit);
  const key = voxelKey(target);
  if (!builderVoxels.has(key)) {
    builderVoxels.add(key);
    customPolycubeCheckbox.checked = true;
    builderHoverKey = null;
    renderBuilderVoxels();
    handleCustomPolycubeChanged();
  }
}

function configKey() {
  const snapshotEvery = Number(snapshotSelect.value);
  const customSystem = customSystemConfig();
  const root = rootFigure();
  const positiveOrNull = (control) => {
    const value = Number(control.value);
    return Number.isFinite(value) && value > 0 ? value : null;
  };
  const positiveSearchParam = (...names) => {
    const params = new URLSearchParams(window.location.search);
    for (const name of names) {
      if (!params.has(name)) continue;
      const value = Number(params.get(name));
      if (Number.isFinite(value) && value >= 0) return value;
    }
    return null;
  };
  const seconds = positiveOrNull(timeCapInput);
  const selectedCriterion = criterion();
  const tilingStrategy = checkedRadioValue(strategyRadios, "free_range");
  const completeGlobalSearch = tilingStrategy === "free_range"
    && moveOrderSelect.value === "global"
    && selectedCriterion === "count"
    && exhaustiveCheckbox.checked;
  const completeShellSearch = selectedCriterion === "shell"
    && ["free_range", "learning_free_range", "rl_free_range", "gcts_rl"].includes(tilingStrategy)
    && exhaustiveCheckbox.checked;
  const forcedLayerLagCap = completeGlobalSearch || completeShellSearch
    ? 0
    : positiveSearchParam("generation_lag_cap", "forced_layer_lag_cap", "forced_move_layer_lag_cap") ?? 2;
  const isGcts = tilingStrategy === "learning_free_range" || tilingStrategy === "gcts_rl";
  const isRl = tilingStrategy === "rl_free_range" || tilingStrategy === "gcts_rl";
  const isStructural = tilingStrategy === "translational" || tilingStrategy === "isohedral";
  const candidateIsohedralHorizon = root?.census_candidate?.last_screening
    ?.isohedral?.growth_horizon_tiles ?? null;
  return JSON.stringify({
    mode_key: root?.mode_key ?? "cube",
    custom_system: customSystem,
    polycube_lattice: selectedPolycubeLattice(),
    criterion: selectedCriterion,
    target_val: selectedCriterion === "count"
      ? +maxTilesInput.value
      : selectedCriterion === "shell"
        ? +shellInput.value
        : +layerInput.value,
    target_region: selectedCriterion === "region" ? (() => {
      const size = [
        Math.max(1, Number(regionWidthInput.value) || 1),
        Math.max(1, Number(regionDepthInput.value) || 1),
        Math.max(1, Number(regionHeightInput.value) || 1)
      ];
      return { type: "box", center: size.map(value => value / 2), size };
    })() : null,
    exhaustive: exhaustiveCheckbox.checked,
    include_mirrors: mirrorCheckbox.checked,
    snapshot_every: Number.isFinite(snapshotEvery) ? snapshotEvery : 1,
    face_order: faceOrderSelect.value,
    tiling_strategy: tilingStrategy,
    move_order: isRl
      ? "rl"
      : isGcts
        ? "balanced"
        : tilingStrategy === "translational"
          ? "periodic"
          : completeShellSearch
            ? "shell"
            : moveOrderSelect.value,
    complete_lattice_point_branching: isGcts || isRl || tilingStrategy === "translational"
      || (tilingStrategy === "free_range" && selectedCriterion !== "shell"),
    gcts_failure_marking: isGcts,
    gcts_marking_reach_multiplier: 1,
    gcts_marking_max_clauses: 20000,
    gcts_marking_max_context_tiles: 1000000,
    gcts_marking_activation_failures: 0,
    gcts_marking_symmetry: "fixed",
    gcts_marking_index: true,
    greedy_no_backtrack: false,
    agent_exhaustive: true,
    agent_policy: isRl ? "cold_linucb" : null,
    agent_ucb_alpha: isRl ? 0 : null,
    seeded_tie_breaks: isRl || tilingStrategy === "translational",
    random_seed: 1,
    learned_layer_macro: false,
    template_preflight: isStructural,
    periodic_patch_unbounded: false,
    periodic_stop_at_growth_goal: tilingStrategy === "translational",
    periodic_goal_preflight_time_ms: tilingStrategy === "translational" ? 1000 : null,
    periodic_motif_node_limit: tilingStrategy === "translational" ? 2500 : null,
    periodic_patch_max_tiles: tilingStrategy === "translational"
      ? selectedCriterion === "count"
        ? Math.max(1, +maxTilesInput.value)
        : selectedCriterion === "shell"
          ? Math.max(24, 24 * +shellInput.value)
          : Math.max(1, Number(periodicTileCountSelect.value) || 4)
      : Math.max(1, Number(periodicTileCountSelect.value) || 4),
    periodic_template_max_volume: 512,
    isohedral_search_horizon_tiles:
      positiveSearchParam("isohedral_search_horizon_tiles") ?? candidateIsohedralHorizon,
    forced_move_layer_lag_cap: forcedLayerLagCap,
    generic_connected_patch_enumeration: completeGlobalSearch,
    generic_complete_shell_enumeration: completeShellSearch,
    // Catalog annotations are display-only. Every interactive lane must derive
    // its behavior from the supplied lattice geometry in the current run.
    known_periodic_template: null,
    branch_cap: positiveOrNull(branchCapInput),
    node_limit: positiveOrNull(nodeCapInput),
    candidate_cap: positiveOrNull(candidateCapInput),
    time_limit_ms: seconds == null ? null : seconds * 1000,
    ui_yield_interval_ms: 24
  });
}

function setRunButton() {
  runButton.disabled = !hasRunnableSelection();
  const extensionSeconds = Math.max(1, Number(timeCapInput.value) || 60);
  runButton.textContent = !growthRunning
    ? "Run"
    : growthPaused
      ? `Continue +${extensionSeconds}s`
      : "Pause";
  runButton.dataset.state = !growthRunning ? "run" : growthPaused ? "continue" : "pause";
  if (runButton.disabled) runButton.textContent = "Choose a figure";
}

function invalidatePausedRunIfNeeded() {
  if (!paused) {
    setRunButton();
    return;
  }
  if (pausedConfigKey !== configKey()) {
    runSeq += 1;
    stopSolverWorker();
    paused = false;
    setStatus("Ready");
  }
  setRunButton();
}

function disposeObjectTree(object) {
  while (object.children?.length) disposeObjectTree(object.children.pop());
  object.geometry?.dispose?.();
  if (Array.isArray(object.material)) object.material.forEach((mat) => mat.dispose?.());
  else object.material?.dispose?.();
}

function clearObjectGroup(group) {
  while (group.children.length) disposeObjectTree(group.children.pop());
}

function resizeRenderer() {
  const bounds = viewport.getBoundingClientRect();
  const width = Math.max(1, Math.floor(bounds.width));
  const height = Math.max(1, Math.floor(bounds.height));
  if (width === renderWidth && height === renderHeight) return;
  renderWidth = width;
  renderHeight = height;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height, false);
  requestRender();
}

new ResizeObserver(resizeRenderer).observe(viewport);
resizeRenderer();

function resizeBuilderRenderer() {
  if (!ensureBuilderRenderer()) return;
  const bounds = polycubeBuilder.getBoundingClientRect();
  const width = Math.max(1, Math.floor(bounds.width));
  const height = Math.max(1, Math.floor(bounds.height));
  if (width === builderWidth && height === builderHeight) return;
  builderWidth = width;
  builderHeight = height;
  builderCamera.aspect = width / height;
  builderCamera.updateProjectionMatrix();
  builderRenderer.setSize(width, height, false);
  requestBuilderRender();
}

new ResizeObserver(resizeBuilderRenderer).observe(polycubeBuilder);

function openCustomBuilderDialog() {
  if (!customBuilderDialog.open) {
    if (typeof customBuilderDialog.showModal === "function") customBuilderDialog.showModal();
    else customBuilderDialog.setAttribute("open", "");
  }
  requestAnimationFrame(() => {
    ensureBuilderRenderer();
    resizeBuilderRenderer();
    requestBuilderRender();
  });
}

function closeCustomBuilderDialog() {
  if (customBuilderDialog.open && typeof customBuilderDialog.close === "function") customBuilderDialog.close();
  else customBuilderDialog.removeAttribute("open");
}

function batchFor(map, key, setup) {
  let batch = map.get(key);
  if (!batch) {
    batch = setup();
    map.set(key, batch);
  }
  return batch;
}

function geometryFromPositions(positions, { normals = false } = {}) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  if (normals) geometry.computeVertexNormals();
  return geometry;
}

function replaceObjectGeometry(object, geometry) {
  const previous = object.geometry;
  object.geometry = geometry;
  previous?.dispose?.();
}

function reconcileRenderBatches(group, batches, createObject, updateObject) {
  const existing = new Map(group.children.map(object => [object.userData.renderBatchKey, object]));
  for (const [key, batch] of batches) {
    let object = existing.get(key);
    if (object) {
      existing.delete(key);
      updateObject(object, batch);
    } else {
      object = createObject(batch);
      object.userData.renderBatchKey = key;
      group.add(object);
    }
  }
  for (const object of existing.values()) {
    group.remove(object);
    disposeObjectTree(object);
  }
}

function pushVertex(out, vertex, scale) {
  out.push(vertex[0] / scale, vertex[1] / scale, vertex[2] / scale);
}

function faceNormal(vertices) {
  if (!vertices || vertices.length < 3) return [0, 0, 0];
  const a = vertices[0];
  for (let i = 1; i < vertices.length - 1; i += 1) {
    const b = vertices[i];
    const c = vertices[i + 1];
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2];
    const vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
    const nx = uy * vz - uz * vy;
    const ny = uz * vx - ux * vz;
    const nz = ux * vy - uy * vx;
    const len = Math.hypot(nx, ny, nz);
    if (len > 1e-9) return [nx / len, ny / len, nz / len];
  }
  return [0, 0, 0];
}

function pushOffsetVertex(out, vertex, scale, offset) {
  out.push(vertex[0] / scale + offset[0], vertex[1] / scale + offset[1], vertex[2] / scale + offset[2]);
}

function visibleAlpha(face) {
  const typeIndex = face.type_idx ?? 0;
  return currentOpacities[typeIndex] ?? 1;
}

function formatVisitedPercent(value) {
  if (!Number.isFinite(value)) return "0%";
  const clamped = Math.max(0, Math.min(100, value));
  if (clamped >= 100) return "100%";
  if (clamped >= 10) return `${Math.floor(clamped)}%`;
  if (clamped > 0) return `${(Math.floor(clamped * 10) / 10).toFixed(1)}%`;
  return "0%";
}

function updateFrontierMetrics(stats = null) {
  const frontierPoints = stats?.point_count ?? stats?.frontier_points ?? stats?.count ?? 0;
  const candidateCount = Number.isFinite(stats?.candidate_count) ? stats.candidate_count : 0;
  const minLayer = Number.isFinite(stats?.min_layer) ? stats.min_layer : 0;
  const shellDepth = Number.isFinite(stats?.complete_shell_depth) ? stats.complete_shell_depth : 0;
  const layerPointCount = Number.isFinite(stats?.min_layer_point_count) ? stats.min_layer_point_count : frontierPoints;
  metricFrontier.textContent = frontierPoints;
  metricLayer.textContent = criterion() === "shell" ? shellDepth : minLayer;
  metricLayerDetail.textContent = criterion() === "shell"
    ? `complete shell · ${stats?.min_shell_face_count ?? 0} nearest exposed face${stats?.min_shell_face_count === 1 ? "" : "s"}`
    : `active layer · ${layerPointCount} point${layerPointCount === 1 ? "" : "s"} · ${candidateCount} candidate${candidateCount === 1 ? "" : "s"}`;
}

function updateSearchMetrics(stats = null) {
  if (stats) lastSearchStats = stats;
  const visitedPercent = stats?.visited_percent ?? 0;
  const progressDepth = stats?.progress_depth ?? stats?.max_depth ?? 0;
  const completedPaths = stats?.progress_completed_paths ?? stats?.visited_nodes ?? treeMap.size;
  const totalPaths = stats?.progress_total_paths ?? stats?.estimated_nodes_at_depth ?? null;
  const completedPathLabel = stats?.progress_completed_paths_label ?? completedPaths;
  const totalPathLabel = stats?.progress_total_paths_label ?? totalPaths;
  const visitedNodes = stats?.visited_nodes ?? treeMap.size;

  metricVisited.textContent = formatVisitedPercent(visitedPercent);
  metricVisitedDetail.textContent = `DFS estimate, depth ${progressDepth}`;
  metricNodes.textContent = totalPathLabel
    ? `${visitedNodes} nodes · ${completedPathLabel}/${totalPathLabel} paths`
    : `${visitedNodes} nodes`;
  const isotropy = Number(stats?.growth_isotropy);
  const spans = stats?.growth_spans ?? [0, 0, 0];
  metricGrowth.textContent = Number.isFinite(isotropy) ? `${Math.round(isotropy * 100)}%` : "—";
  metricGrowthDetail.textContent = `center spans ${spans.map(value => Number(value.toFixed?.(2) ?? value)).join(" × ")}`;
}

function refreshNodeMetricFallback() {
  if (lastSearchStats) updateSearchMetrics(lastSearchStats);
  else metricNodes.textContent = `${treeMap.size} nodes`;
}

function formatElapsed(ms) {
  const seconds = Math.max(0, ms / 1000);
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const minutes = Math.floor(seconds / 60);
  const remaining = Math.floor(seconds % 60);
  return `${minutes}m ${remaining.toString().padStart(2, "0")}s`;
}

function updateRunMetrics(snapshot = null) {
  metricTiles.textContent = snapshot?.tile_count ?? 0;
  updateFrontierMetrics(snapshot?.frontier_stats);
  updateSearchMetrics(snapshot?.search_stats);
  renderSelectedTiles();
}

function displayFaceKey(face, fallbackIndex = 0) {
  if (face?.key) return face.key;
  return `face:${fallbackIndex}:${(face?.v ?? []).map(vertex => vertex.join(",")).sort().join("|")}`;
}

function resetLiveFaceStacks(snapshot) {
  liveFaceStacks = new Map();
  (snapshot?.faces ?? []).forEach((face, index) => {
    const key = displayFaceKey(face, index);
    const storedFace = { ...face, key, v: (face.v ?? []).map(vertex => vertex.slice()) };
    if (!liveFaceStacks.has(key)) liveFaceStacks.set(key, []);
    liveFaceStacks.get(key).push(storedFace);
  });
}

function liveFaces() {
  const faces = [];
  for (const stack of liveFaceStacks.values()) {
    for (const face of stack) faces.push(face);
  }
  return faces;
}

function frontierPointKey(point) {
  return (point?.pos ?? point ?? []).join(",");
}

function resetLiveFrontierPoints(snapshot) {
  liveFrontierPoints = new Map();
  for (const point of snapshot?.frontier_points ?? []) {
    liveFrontierPoints.set(frontierPointKey(point), {
      ...point,
      pos: (point.pos ?? []).slice()
    });
  }
}

function liveFaceCount() {
  let count = 0;
  for (const stack of liveFaceStacks.values()) count += stack.length;
  return count;
}

function liveRenderInterval() {
  const count = liveFaceCount();
  if (count <= 1200) return LIVE_UPDATE_FAST_INTERVAL_MS;
  if (count <= 4800) return LIVE_UPDATE_MEDIUM_INTERVAL_MS;
  return LIVE_UPDATE_SLOW_INTERVAL_MS;
}

function scheduleLiveUpdateFromDelta(delta) {
  pendingLiveSnapshot = {
    type: "live_update",
    tile_count: delta.tile_count ?? lastSnapshot?.tile_count ?? 0,
    tile_counts: delta.tile_counts ?? lastSnapshot?.tile_counts ?? [],
    frontier_stats: delta.frontier_stats ?? lastSnapshot?.frontier_stats ?? null,
    search_stats: delta.search_stats ?? lastSnapshot?.search_stats ?? null,
    frontier_points: [...liveFrontierPoints.values()]
  };
  if (liveUpdateRenderQueued) return;
  liveUpdateRenderQueued = true;
  const elapsed = performance.now() - lastLiveUpdateRenderedAt;
  const delay = running ? Math.max(0, liveRenderInterval() - elapsed) : 0;
  liveUpdateTimer = setTimeout(() => {
    liveUpdateTimer = null;
    requestAnimationFrame(flushLiveUpdateNow);
  }, delay);
}

function flushLiveUpdateNow() {
  if (liveUpdateTimer) {
    clearTimeout(liveUpdateTimer);
    liveUpdateTimer = null;
  }
  liveUpdateRenderQueued = false;
  const latest = pendingLiveSnapshot;
  pendingLiveSnapshot = null;
  if (!latest) return;
  latest.faces = liveFaces();
  latest.frontier_points = [...liveFrontierPoints.values()];
  applyingFullUpdate = true;
  syncWorkerDisplayBackpressure();
  try {
    updateScene(latest, { preserveView: true, syncLive: false });
    lastLiveUpdateRenderedAt = performance.now();
    queueCheckpointSave(latest, { reason: "live" });
  } finally {
    applyingFullUpdate = false;
    syncWorkerDisplayBackpressure();
  }
}

function applyPlacementDelta(delta, { deferDisplay = false } = {}) {
  if (!delta) return;
  if (!liveFaceStacks.size && lastSnapshot?.faces?.length) resetLiveFaceStacks(lastSnapshot);
  if (!liveFrontierPoints.size && lastSnapshot?.frontier_points?.length) resetLiveFrontierPoints(lastSnapshot);

  const frontierKeys = delta.frontier_face_keys ?? [];
  const coveredKeys = delta.covered_face_keys ?? [];

  if (delta.action === "add") {
    for (const key of coveredKeys) {
      for (const face of liveFaceStacks.get(key) ?? []) face.internal = true;
    }
    for (const face of delta.faces ?? []) {
      const key = displayFaceKey(face);
      if (!liveFaceStacks.has(key)) liveFaceStacks.set(key, []);
      liveFaceStacks.get(key).push({ ...face, key, v: (face.v ?? []).map(vertex => vertex.slice()) });
    }
  } else if (delta.action === "remove") {
    for (const key of [...frontierKeys, ...coveredKeys]) {
      const stack = liveFaceStacks.get(key);
      if (!stack) continue;
      stack.pop();
      if (!stack.length) liveFaceStacks.delete(key);
    }
    for (const key of coveredKeys) {
      const stack = liveFaceStacks.get(key);
      if (stack?.length === 1) stack[0].internal = false;
    }
  }

  for (const point of delta.lattice_updates ?? []) {
    const key = frontierPointKey(point);
    if (point.frontier) liveFrontierPoints.set(key, { ...point, pos: point.pos.slice() });
    else liveFrontierPoints.delete(key);
  }

  // A full snapshot can be waiting for its throttled render while newer
  // placement deltas arrive. Keep that pending render at the current state;
  // otherwise the older snapshot would erase faces restored by backtracking.
  if (pendingFullUpdate) {
    pendingFullUpdate = {
      ...pendingFullUpdate,
      tile_count: delta.tile_count ?? pendingFullUpdate.tile_count,
      tile_counts: delta.tile_counts ?? pendingFullUpdate.tile_counts,
      faces: liveFaces(),
      frontier_points: [...liveFrontierPoints.values()],
      frontier_stats: delta.frontier_stats ?? pendingFullUpdate.frontier_stats,
      search_stats: delta.search_stats ?? pendingFullUpdate.search_stats
    };
  }

  if (!deferDisplay) {
    updateRunMetrics({
      tile_count: delta.tile_count,
      tile_counts: delta.tile_counts ?? lastSnapshot?.tile_counts,
      frontier_stats: delta.frontier_stats ?? lastSnapshot?.frontier_stats,
      search_stats: delta.search_stats ?? lastSearchStats
    });
    scheduleLiveUpdateFromDelta(delta);
  }
}

function updateScene(snapshot, options = {}) {
  const { preserveView = true, rebuildFaces = true, syncLive = true } = options;
  lastSnapshot = snapshot;
  if (syncLive && snapshot?.faces) resetLiveFaceStacks(snapshot);
  if (syncLive && snapshot?.frontier_points) resetLiveFrontierPoints(snapshot);

  const faces = snapshot?.faces ?? [];
  const scale = prototileInfo?.scale ?? 2;
  const faceBatches = new Map();
  const edgeBatches = new Map();
  const showInternal = internalCheckbox.checked;
  const showEdges = edgesCheckbox.checked && (!running || faces.length <= RUNNING_EDGE_FACE_LIMIT);

  for (const face of faces) {
    if (face.internal && !showInternal) continue;
    const alpha = visibleAlpha(face);
    if (alpha < 0.01) continue;
    const color = face.color ?? "#178273";
    const vertices = face.v ?? [];
    if (vertices.length < 3) continue;
    const normal = faceNormal(vertices);
    const offsetDistance = face.internal ? 0.012 : 0;
    const offset = normal.map(value => value * offsetDistance);

    if (rebuildFaces) {
      const faceKey = `${color}|${alpha.toFixed(3)}|${alpha > 0.55 ? 1 : 0}`;
      const faceBatch = batchFor(faceBatches, faceKey, () => ({ color, alpha, positions: [] }));
      for (let i = 1; i < vertices.length - 1; i += 1) {
        pushOffsetVertex(faceBatch.positions, vertices[0], scale, offset);
        pushOffsetVertex(faceBatch.positions, vertices[i], scale, offset);
        pushOffsetVertex(faceBatch.positions, vertices[i + 1], scale, offset);
      }
    }

    if (showEdges) {
      const edgeKey = alpha.toFixed(3);
      const edgeBatch = batchFor(edgeBatches, edgeKey, () => ({ alpha, positions: [] }));
      for (let i = 0; i < vertices.length; i += 1) {
        pushOffsetVertex(edgeBatch.positions, vertices[i], scale, offset);
        pushOffsetVertex(edgeBatch.positions, vertices[(i + 1) % vertices.length], scale, offset);
      }
    }
  }

  if (rebuildFaces) {
    reconcileRenderBatches(
      faceGroup,
      faceBatches,
      batch => new THREE.Mesh(
        geometryFromPositions(batch.positions, { normals: true }),
        new THREE.MeshPhongMaterial({
          color: new THREE.Color(batch.color),
          transparent: batch.alpha < 0.999,
          opacity: batch.alpha,
          side: THREE.DoubleSide,
          flatShading: true,
          polygonOffset: true,
          polygonOffsetFactor: 1,
          polygonOffsetUnits: 1,
          depthWrite: batch.alpha > 0.55
        })
      ),
      (object, batch) => replaceObjectGeometry(
        object,
        geometryFromPositions(batch.positions, { normals: true })
      )
    );
  }

  reconcileRenderBatches(
    edgeGroup,
    edgeBatches,
    batch => new THREE.LineSegments(
      geometryFromPositions(batch.positions),
      new THREE.LineBasicMaterial({
        color: 0x111827,
        transparent: batch.alpha < 0.999,
        opacity: Math.min(0.72, Math.max(0.18, batch.alpha))
      })
    ),
    (object, batch) => replaceObjectGeometry(object, geometryFromPositions(batch.positions))
  );

  const pointPositions = [];
  for (const point of snapshot?.frontier_points ?? []) {
    if (!point?.pos?.length) continue;
    pointPositions.push([point.pos[0] / scale, point.pos[1] / scale, point.pos[2] / scale]);
  }
  const lattice = selectedPolycubeLattice();
  const frontierBatchKey = `frontier:${lattice}`;
  const existingFrontierMesh = frontierPointGroup.children.find(
    object => object.userData.renderBatchKey === frontierBatchKey
  );
  for (const object of [...frontierPointGroup.children]) {
    if (object === existingFrontierMesh && pointPositions.length) continue;
    frontierPointGroup.remove(object);
    disposeObjectTree(object);
  }
  if (pointPositions.length) {
    const pointRadius = lattice === "half" ? 0.0425 : 0.06;
    const requiredCapacity = pointPositions.length;
    let pointMesh = existingFrontierMesh;
    if (!pointMesh || pointMesh.userData.instanceCapacity < requiredCapacity) {
      if (pointMesh) {
        frontierPointGroup.remove(pointMesh);
        disposeObjectTree(pointMesh);
      }
      const capacity = 2 ** Math.ceil(Math.log2(Math.max(1, requiredCapacity)));
      const pointGeometry = new THREE.SphereGeometry(pointRadius, 8, 6);
      const pointMaterial = new THREE.MeshBasicMaterial({
        color: { z3: 0x178273, fcc: 0x315f9f, half: 0xd97706 }[lattice] ?? 0x178273,
        transparent: true,
        opacity: 0.9,
        depthTest: true,
        depthWrite: false
      });
      pointMesh = new THREE.InstancedMesh(pointGeometry, pointMaterial, capacity);
      pointMesh.userData.renderBatchKey = frontierBatchKey;
      pointMesh.userData.instanceCapacity = capacity;
      frontierPointGroup.add(pointMesh);
    }
    pointMesh.count = pointPositions.length;
    const pointMatrix = new THREE.Matrix4();
    pointPositions.forEach((position, index) => {
      pointMatrix.makeTranslation(position[0], position[1], position[2]);
      pointMesh.setMatrixAt(index, pointMatrix);
    });
    pointMesh.instanceMatrix.needsUpdate = true;
  }

  updateRunMetrics(snapshot);
  if (!preserveView && autoFitCheckbox.checked && !rootCentered) centerOnSnapshot(snapshot, true);
  requestRender();
}

function centerOnSnapshot(snapshot, force = false) {
  if (!snapshot || (!force && rootCentered)) return;
  const scale = prototileInfo?.scale ?? 2;
  const box = new THREE.Box3();
  const point = new THREE.Vector3();
  for (const face of snapshot.faces ?? []) {
    for (const vertex of face.v ?? []) {
      point.set(vertex[0] / scale, vertex[1] / scale, vertex[2] / scale);
      box.expandByPoint(point);
    }
  }
  if (box.isEmpty()) return;

  const center = new THREE.Vector3();
  const size = new THREE.Vector3();
  box.getCenter(center);
  box.getSize(size);
  const radius = Math.max(2, size.length() * 0.5);
  const maxDim = Math.max(size.x, size.y, size.z, 1);
  const verticalFov = THREE.MathUtils.degToRad(camera.fov);
  const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * Math.max(camera.aspect, 0.25));
  const limitingFov = Math.min(verticalFov, horizontalFov);
  const fitHeightDistance = maxDim / (2 * Math.tan(verticalFov / 2));
  const fitWidthDistance = fitHeightDistance / Math.max(camera.aspect, 0.25);
  const sphereDistance = radius / Math.sin(Math.max(0.1, limitingFov / 2));
  const distance = Math.max(fitHeightDistance, fitWidthDistance, sphereDistance) * 2.3;
  const offset = new THREE.Vector3(1.3, 1.05, 1.15).normalize().multiplyScalar(distance);
  controls.target.copy(center);
  camera.position.copy(center).add(offset);
  camera.near = Math.max(0.05, radius / 200);
  camera.far = Math.max(4000, radius * 50);
  camera.updateProjectionMatrix();
  controls.update();
  rootCentered = true;
  requestRender();
}

function initTileControls(info) {
  prototileInfo = info;
  tileList.replaceChildren();

  const defaults = info.default_opacities ?? [];
  info.tiles.forEach((tile, index) => {
    if (currentOpacities[index] == null) currentOpacities[index] = defaults[index] ?? 1;

    const row = document.createElement("div");
    row.className = "tile-row";

    const swatch = document.createElement("span");
    swatch.className = "tile-swatch";
    swatch.style.background = tileSpecs.COLOR_PALETTE[index % tileSpecs.COLOR_PALETTE.length];

    const meta = document.createElement("div");
    meta.className = "tile-meta";

    const name = document.createElement("div");
    name.className = "tile-name";
    const latticeLabel = tile.is_polycube ? polycubeLatticeLabel(tile.polycube_lattice) : "";
    name.textContent = latticeLabel ? `${prettyName(tile.name)} · ${latticeLabel}` : prettyName(tile.name);
    name.title = `${prettyName(tile.name)}${latticeLabel ? `\n${latticeLabel}` : ""}\n${solidAngleTitle(tile.solid_angles)}`;

    const slider = document.createElement("input");
    slider.type = "range";
    slider.min = "0";
    slider.max = "1";
    slider.step = "0.05";
    slider.value = currentOpacities[index];
    slider.addEventListener("input", () => {
      currentOpacities[index] = +slider.value;
      if (lastSnapshot) updateScene(lastSnapshot, { preserveView: true });
      requestRender();
    });

    const angles = document.createElement("div");
    angles.className = "tile-angles";
    angles.innerHTML = solidAngleListHtml(tile.solid_angles);

    meta.append(name, angles, slider);
    row.append(swatch, meta);
    tileList.appendChild(row);
  });
  renderSelectedTiles();
}

function addNodeToTree(id, label, parentId = null, isForced = false, frontierStats = null) {
  let node = treeMap.get(id);
  if (node) {
    if (label?.trim()) node.label = label.trim();
    node.isForced = !!isForced;
    if (frontierStats) node.frontierStats = frontierStats;
  } else {
    node = {
      id,
      label: label?.trim() || "",
      parentId,
      isForced: !!isForced,
      children: [],
      status: "pending",
      statusText: "",
      resultText: "",
      colorId: null,
      snapshot: null,
      frontierStats
    };
    treeMap.set(id, node);
    if (parentId != null) {
      const parent = treeMap.get(parentId);
      if (parent && !parent.children.includes(id)) parent.children.push(id);
    }
    if (parentId == null) expandedNodes.add(id);
  }

  const pending = pendingSnapshots.get(id);
  if (pending) {
    node.snapshot = pending;
    if (pending.frontier_stats) node.frontierStats = pending.frontier_stats;
    pendingSnapshots.delete(id);
    rememberTreeSnapshotNode(id);
  }
  scheduleTreeRender();
  return node;
}

function rememberTreeSnapshotNode(nodeId) {
  if (nodeId == null) return;
  const existingIndex = treeSnapshotOrder.indexOf(nodeId);
  if (existingIndex >= 0) treeSnapshotOrder.splice(existingIndex, 1);
  treeSnapshotOrder.push(nodeId);
  trimStoredTreeSnapshots(nodeId);
}

function trimStoredTreeSnapshots(protectedNodeId = null) {
  let passes = 0;
  while (treeSnapshotOrder.length > MAX_STORED_TREE_SNAPSHOTS && passes < treeSnapshotOrder.length + 4) {
    const nodeId = treeSnapshotOrder.shift();
    const node = treeMap.get(nodeId);
    if (!node?.snapshot) continue;
    if (nodeId === selectedNodeId || nodeId === protectedNodeId) {
      treeSnapshotOrder.push(nodeId);
      passes += 1;
      continue;
    }
    node.snapshot = null;
  }
}

function rememberPendingSnapshot(nodeId, snapshot) {
  if (nodeId == null || !snapshot) return;
  if (!Array.isArray(snapshot.faces) || !snapshot.faces.length) return;
  pendingSnapshots.set(nodeId, snapshot);
  while (pendingSnapshots.size > MAX_PENDING_TREE_SNAPSHOTS) {
    const oldest = pendingSnapshots.keys().next().value;
    pendingSnapshots.delete(oldest);
  }
}

function attachSnapshotToNode(nodeId, snapshot) {
  if (nodeId == null || !snapshot) return;
  const hasGeometry = Array.isArray(snapshot.faces) && snapshot.faces.length;
  const node = treeMap.get(nodeId);
  if (node) {
    if (hasGeometry) node.snapshot = snapshot;
    if (snapshot.frontier_stats) node.frontierStats = snapshot.frontier_stats;
    if (hasGeometry) rememberTreeSnapshotNode(nodeId);
    scheduleTreeRender();
  } else {
    rememberPendingSnapshot(nodeId, snapshot);
  }
}

function selectTreeNode(nodeId) {
  const node = treeMap.get(nodeId);
  if (!node?.snapshot) return;
  selectedNodeId = nodeId;
  updateScene(node.snapshot, { preserveView: true });
  const stats = node.frontierStats ?? node.snapshot.frontier_stats;
  if (stats) updateFrontierMetrics(stats);
  updateSearchMetrics(node.snapshot.search_stats);
  renderTree();
}

function updateNodeStatus(id, status, text = "", colorId = null, frontierStats = null, frontierDual = null) {
  const node = treeMap.get(id);
  if (!node) return;
  node.status = status;
  const cleanText = text?.trim();
  if (cleanText) {
    if (status === "working") {
      node.statusText = cleanText;
      node.resultText = "";
    } else if (node.statusText || node.label) {
      node.resultText = cleanText;
    } else {
      node.statusText = cleanText;
    }
  }
  if (colorId != null) node.colorId = colorId;
  if (frontierStats) node.frontierStats = frontierStats;
  if (frontierDual) node.frontierDual = frontierDual;

  if (status === "fail" && !manuallyExpanded.has(id)) expandedNodes.delete(id);
  if (status === "working") {
    let currentId = node.parentId;
    while (currentId != null) {
      expandedNodes.add(currentId);
      currentId = treeMap.get(currentId)?.parentId;
    }
  }

  refreshNodeMetricFallback();
  if (frontierStats) updateFrontierMetrics(frontierStats);
  scheduleTreeRender();
}

function pathToTreeNode(nodeId) {
  const path = [];
  const seen = new Set();
  let currentId = nodeId;
  while (currentId != null && !seen.has(currentId)) {
    const node = treeMap.get(currentId);
    if (!node) break;
    path.unshift(currentId);
    seen.add(currentId);
    currentId = node.parentId;
  }
  return path;
}

function findSuccessPath() {
  let bestPath = [];
  for (const node of treeMap.values()) {
    if (node.status !== "success") continue;
    const path = pathToTreeNode(node.id);
    if (!path.length) continue;
    const allAncestorsSucceeded = path.every((id) => treeMap.get(id)?.status === "success");
    if (allAncestorsSucceeded && path.length > bestPath.length) bestPath = path;
  }
  return bestPath;
}

function revealSuccessPath() {
  const successPath = findSuccessPath();
  if (!successPath.length) return;

  expandedNodes.clear();
  manuallyExpanded.clear();
  for (const nodeId of successPath) {
    const node = treeMap.get(nodeId);
    if (node?.children.length) expandedNodes.add(nodeId);
  }
  renderTree();
}

function clearTree() {
  if (treeRenderTimer) {
    clearTimeout(treeRenderTimer);
    treeRenderTimer = null;
  }
  treeRenderQueued = false;
  treeMap.clear();
  pendingSnapshots.clear();
  treeSnapshotOrder.length = 0;
  expandedNodes.clear();
  manuallyExpanded.clear();
  selectedNodeId = null;
  treePanel.replaceChildren();
  metricNodes.textContent = "0 nodes";
}

function scheduleTreeRender() {
  if (treeRenderQueued) return;
  treeRenderQueued = true;
  const elapsed = performance.now() - lastTreeRenderAt;
  const delay = running ? Math.max(0, TREE_RENDER_INTERVAL_MS - elapsed) : 0;
  treeRenderTimer = setTimeout(() => {
    treeRenderTimer = null;
    requestAnimationFrame(() => {
      treeRenderQueued = false;
      renderTree();
    });
  }, delay);
}

function renderTree() {
  lastTreeRenderAt = performance.now();
  treePanel.replaceChildren();
  let renderedRows = 0;
  let treeRowsLimited = false;

  const isGenericBranchLeaf = (node) =>
    node
    && !node.isForced
    && !node.children.length
    && !node.snapshot
    && !node.label
    && !node.statusText
    && !node.resultText;

  const renderBranchSummary = (count, depth) => {
    if (renderedRows >= MAX_RENDERED_TREE_ROWS) {
      treeRowsLimited = true;
      return;
    }
    renderedRows += 1;
    const row = document.createElement("div");
    row.className = "tree-node tree-node-summary";
    row.style.paddingLeft = `${depth * 18}px`;

    const toggle = document.createElement("span");
    toggle.className = "tree-toggle";

    const content = document.createElement("span");
    content.className = "tree-button tree-button-summary";

    const statusDot = document.createElement("span");
    statusDot.className = "tree-status";

    const label = document.createElement("span");
    label.className = "tree-label";
    label.textContent = `${count} more branch${count === 1 ? "" : "es"}`;

    content.append(statusDot, label);
    row.append(toggle, content);
    treePanel.appendChild(row);
  };

  const renderTreeLimitSummary = () => {
    const row = document.createElement("div");
    row.className = "tree-node tree-node-summary";
    const toggle = document.createElement("span");
    toggle.className = "tree-toggle";
    const content = document.createElement("span");
    content.className = "tree-button tree-button-summary";
    const statusDot = document.createElement("span");
    statusDot.className = "tree-status";
    const label = document.createElement("span");
    label.className = "tree-label";
    const hiddenCount = Math.max(1, treeMap.size - renderedRows);
    label.textContent = `${hiddenCount} more node${hiddenCount === 1 ? "" : "s"}`;
    content.append(statusDot, label);
    row.append(toggle, content);
    treePanel.appendChild(row);
  };

  const renderNode = (nodeId, depth) => {
    const node = treeMap.get(nodeId);
    if (!node) return;
    if (renderedRows >= MAX_RENDERED_TREE_ROWS) {
      treeRowsLimited = true;
      return;
    }
    renderedRows += 1;

    const row = document.createElement("div");
    row.className = "tree-node";
    row.style.paddingLeft = `${depth * 18}px`;

    const toggle = document.createElement("span");
    toggle.className = "tree-toggle";
    if (node.children.length) {
      toggle.textContent = expandedNodes.has(nodeId) ? "-" : "+";
      toggle.addEventListener("click", () => {
        if (expandedNodes.has(nodeId)) {
          expandedNodes.delete(nodeId);
          manuallyExpanded.delete(nodeId);
        } else {
          expandedNodes.add(nodeId);
          manuallyExpanded.add(nodeId);
        }
        renderTree();
      });
    }

    const content = document.createElement("span");
    content.className = "tree-button";
    content.dataset.status = node.status;
    if (node.snapshot) content.classList.add("has-snapshot");
    if (selectedNodeId === nodeId) content.classList.add("is-selected");

    const statusDot = document.createElement("span");
    statusDot.className = "tree-status";
    if (node.colorId != null) statusDot.style.background = tileSpecs.COLOR_PALETTE[node.colorId % tileSpecs.COLOR_PALETTE.length];

    const label = document.createElement("span");
    label.className = "tree-label";
    label.textContent = node.statusText || node.label || (node.isForced ? "forced" : "branch");
    label.title = label.textContent;

    const result = document.createElement("span");
    result.className = "tree-result";
    if (node.resultText) result.textContent = node.resultText;

    const frontier = document.createElement("span");
    frontier.className = "tree-frontier";
    if (node.frontierStats) {
      const points = node.frontierStats.point_count ?? node.frontierStats.count ?? 0;
      const candidates = Number.isFinite(node.frontierStats.candidate_count) ? node.frontierStats.candidate_count : 0;
      frontier.textContent = `${points} pts / ${candidates} cand`;
      const associations = node.frontierDual?.association_count ?? node.frontierStats.association_count;
      frontier.title = Number.isFinite(associations)
        ? `Frontier-candidate graph: ${points} points, ${candidates} candidates, ${associations} associations`
        : `Frontier-candidate graph: ${points} points, ${candidates} candidates`;
    }

    content.append(statusDot, label);
    if (result.textContent) content.append(result);
    if (frontier.textContent) content.append(frontier);
    if (node.snapshot) {
      content.addEventListener("click", () => selectTreeNode(nodeId));
    }

    row.append(toggle, content);
    treePanel.appendChild(row);

    if (expandedNodes.has(nodeId)) {
      let pendingBranchCount = 0;
      const flushPendingBranches = () => {
        if (!pendingBranchCount) return;
        renderBranchSummary(pendingBranchCount, depth + 1);
        pendingBranchCount = 0;
      };
      for (const childId of node.children) {
        const child = treeMap.get(childId);
        if (isGenericBranchLeaf(child)) {
          pendingBranchCount += 1;
        } else {
          flushPendingBranches();
          renderNode(childId, depth + 1);
        }
      }
      flushPendingBranches();
    }
  };

  for (const node of treeMap.values()) {
    if (node.parentId == null) renderNode(node.id, 0);
  }

  if (treeRowsLimited) renderTreeLimitSummary();
}

function handleMessage(message) {
  if (message.type === "palette") return;
  if (message.type === "prototile_info") {
    initTileControls(message);
    if (message.default_internal != null) internalCheckbox.checked = !!message.default_internal;
    return;
  }
  if (message.type === "branch_set") {
    for (const branch of message.branches ?? []) {
      addNodeToTree(branch.id, branch.text || "", message.parent, branch.is_forced, branch.frontier_stats);
    }
    return;
  }
  if (message.type === "node_status") {
    updateNodeStatus(message.id, message.status, message.text || "", message.color_id, message.frontier_stats, message.frontier_dual);
    return;
  }
  if (message.type === "node_snapshot") {
    attachSnapshotToNode(message.node_id, message.snapshot);
    return;
  }
  if (message.type === "translational_check") {
    setStatus(message.certified
      ? `Certified ${message.patch_size}-tile translational patch`
      : message.growth_goal_reached
        ? message.check_completed
          ? message.growth_goal_criterion === "shell"
            ? `Reached shell ${message.growth_goal_target}; checked patch is not a quotient`
            : `Reached ${message.growth_goal_target}-tile goal; checked patch is not a quotient`
          : "Reached the growth goal; quotient check timed out"
        : `No ${message.patch_size}-tile patch; checking the next size…`);
    return;
  }
  if (message.type === "full_update") {
    attachSnapshotToNode(message.node_id, message);
    if ((message.tile_count ?? 0) <= 1) {
      flushFullUpdateNow();
      updateScene(message, { preserveView: false });
      lastFullUpdateRenderedAt = performance.now();
      queueCheckpointSave(message, { reason: "root" });
      return;
    }
    scheduleFullUpdate(message);
    return;
  }
  if (message.type === "placement_delta") {
    applyPlacementDelta(message);
    return;
  }
  if (message.type === "finished") {
    isFinished = true;
    running = false;
    paused = false;
    solverWorkerActive = false;
    setWorkerDisplayPaused(false);
    flushFullUpdateNow();
    if (message.success !== false) revealSuccessPath();
    metricTiles.textContent = message.tile_count ?? metricTiles.textContent;
    if (message.search_stats) updateSearchMetrics(message.search_stats);
    const translationalGoalInconclusive = message.search_stats?.termination_reason
      === "translational_growth_goal_without_certificate";
    const prefix = translationalGoalInconclusive
      ? "Translational inconclusive at goal"
      : message.result_kind === "certified_tiling"
      ? "Certified"
      : message.result_kind === "patch_found"
        ? "Patch found"
        : message.result_kind === "no_tiling"
          ? message.tiling_evidence?.kind === "local_edge_obstruction"
            ? "Cannot tile face-to-face"
            : "Cannot tile region"
          : message.search_incomplete
            ? "Search limit: best"
            : message.success === false
              ? (message.best_effort ? "No tiling found: best" : "No tiling found")
              : "Finished";
    const finishedTileCount = message.tile_count ?? 0;
    setStatus(`${prefix}: ${finishedTileCount} tile${finishedTileCount === 1 ? "" : "s"}`);
    if (lastSnapshot) queueCheckpointSave(lastSnapshot, { immediate: true, reason: "finished" });
    setRunButton();
  }
}

function scheduleFullUpdate(snapshot) {
  // Synchronize the model immediately even though expensive Three.js geometry
  // rebuilding remains throttled. Subsequent deltas must apply to this exact
  // snapshot, not to whichever frame happened to be rendered previously.
  resetLiveFaceStacks(snapshot);
  resetLiveFrontierPoints(snapshot);
  if (liveUpdateTimer) {
    clearTimeout(liveUpdateTimer);
    liveUpdateTimer = null;
  }
  liveUpdateRenderQueued = false;
  pendingLiveSnapshot = null;
  pendingFullUpdate = snapshot;
  if (fullUpdateRenderQueued) return;
  fullUpdateRenderQueued = true;
  const elapsed = performance.now() - lastFullUpdateRenderedAt;
  const delay = running ? Math.max(0, FULL_UPDATE_INTERVAL_MS - elapsed) : 0;
  fullUpdateTimer = setTimeout(() => {
    fullUpdateTimer = null;
    requestAnimationFrame(flushFullUpdateNow);
  }, delay);
}

function flushFullUpdateNow() {
  if (fullUpdateTimer) {
    clearTimeout(fullUpdateTimer);
    fullUpdateTimer = null;
  }
  if (liveUpdateTimer) {
    clearTimeout(liveUpdateTimer);
    liveUpdateTimer = null;
  }
  liveUpdateRenderQueued = false;
  pendingLiveSnapshot = null;
  fullUpdateRenderQueued = false;
  const latest = pendingFullUpdate;
  pendingFullUpdate = null;
  if (!latest) return;

  applyingFullUpdate = true;
  syncWorkerDisplayBackpressure();
  try {
    updateScene(latest);
    lastFullUpdateRenderedAt = performance.now();
    queueCheckpointSave(latest, { reason: "snapshot" });
  } finally {
    applyingFullUpdate = false;
    syncWorkerDisplayBackpressure();
  }
}

function ensureSolverWorker() {
  if (solverWorker) return solverWorker;
  solverWorker = new Worker(new URL("./solver-worker.js?v=20260827-a2-size7-v226", import.meta.url), { type: "module" });
  solverWorker.addEventListener("message", (event) => {
    const { seq, type, message, error } = event.data ?? {};
    if (seq !== runSeq) return;

    if (type === "solver_message") {
      enqueueSolverMessage(message);
      return;
    }
    if (type === "solver_messages") {
      enqueueSolverMessages(event.data?.messages);
      return;
    }

    if (type === "solver_error") {
      running = false;
      paused = false;
      solverWorkerActive = false;
      setWorkerDisplayPaused(false);
      setStatus(`Error: ${error}`);
      setRunButton();
      return;
    }

    if (type === "solver_idle" && running && !isFinished) {
      running = false;
      paused = false;
      solverWorkerActive = false;
      setWorkerDisplayPaused(false);
      setStatus("Stopped");
      setRunButton();
    }
  });
  solverWorker.addEventListener("error", (error) => {
    console.error(error);
    running = false;
    paused = false;
    solverWorkerActive = false;
    setStatus(`Error: ${error.message}`);
    setRunButton();
  });
  return solverWorker;
}

function stopSolverWorker() {
  solverWorker?.postMessage({ type: "stop" });
  solverWorkerActive = false;
  workerDisplayPaused = false;
  solverMessageQueue = [];
  solverMessageQueueIndex = 0;
  solverMessageFlushQueued = false;
  pendingFullUpdate = null;
  if (fullUpdateTimer) {
    clearTimeout(fullUpdateTimer);
    fullUpdateTimer = null;
  }
  fullUpdateRenderQueued = false;
  pendingLiveSnapshot = null;
  if (liveUpdateTimer) {
    clearTimeout(liveUpdateTimer);
    liveUpdateTimer = null;
  }
  liveUpdateRenderQueued = false;
}

function resetRunView() {
  cancelPendingCheckpointSave();
  rootCentered = false;
  lastSnapshot = null;
  lastSearchStats = null;
  prototileInfo = null;
  currentOpacities = {};
  liveFaceStacks = new Map();
  liveFrontierPoints = new Map();
  clearTree();
  clearObjectGroup(faceGroup);
  clearObjectGroup(edgeGroup);
  clearObjectGroup(frontierPointGroup);
  tileList.replaceChildren();
  updateRunMetrics(null);
  elapsedTime.textContent = "0.0s";
  requestRender();
}

function startNewRun(configOverride = null) {
  if (!hasRunnableSelection()) {
    setStatus("Choose a figure or enable the custom polycube.");
    setRunButton();
    return;
  }
  stopSolverWorker();
  runSeq += 1;
  paused = false;
  running = true;
  isFinished = false;
  solverWorkerActive = true;
  workerDisplayPaused = false;
  solverMessageQueue = [];
  solverMessageQueueIndex = 0;
  solverMessageFlushQueued = false;
  startedAt = performance.now();
  pausedConfigKey = configKey();
  resetRunView();
  setRunButton();
  setStatus("Running...");

  const config = configOverride ?? JSON.parse(pausedConfigKey);
  ensureSolverWorker().postMessage({ type: "start", seq: runSeq, config });
}

function continueRun() {
  if (!solverWorkerActive) return startNewRun();
  paused = false;
  running = true;
  setRunButton();
  setStatus("Running...");
  solverWorker?.postMessage({ type: "resume", seq: runSeq, reason: "ui" });
  syncWorkerDisplayBackpressure();
}

function pauseRun() {
  paused = true;
  running = false;
  solverWorker?.postMessage({ type: "pause", seq: runSeq, reason: "ui" });
  setRunButton();
  setStatus("Paused");
}

const GROWTH_MODES = [
  { id: "free_range", strategy: "free_range", label: "Free-range", color: "#6f7c77", symbol: "square-open", dash: "dash" },
  { id: "gcts", strategy: "learning_free_range", label: "GCTS", color: "#178273", symbol: "diamond", dash: "solid" },
  { id: "rl", strategy: "rl_free_range", label: "RL", color: "#c16a28", symbol: "cross", dash: "dot" },
  { id: "gcts_rl", strategy: "gcts_rl", label: "GCTS + RL", color: "#b33c67", symbol: "star", dash: "solid" },
  { id: "translational", strategy: "translational", label: "Translational", color: "#315f9f", symbol: "circle-open", dash: "solid" },
  { id: "isohedral", strategy: "isohedral", label: "Isohedral", color: "#7656a5", symbol: "triangle-up-open", dash: "solid" }
];

function selectedGrowthMode() {
  const strategy = checkedRadioValue(strategyRadios, "free_range");
  return GROWTH_MODES.find(mode => mode.strategy === strategy)?.id ?? "free_range";
}

function growthHistorySnapshotIndices(series) {
  return (series?.points ?? [])
    .map((point, index) => point?.historySnapshot || point?.historyDelta || point?.snapshot ? index : null)
    .filter(index => index !== null);
}

function createGrowthHistoryModel(snapshot) {
  const faceStacks = new Map();
  for (let index = 0; index < (snapshot?.faces ?? []).length; index += 1) {
    const face = snapshot.faces[index];
    const key = displayFaceKey(face, index);
    if (!faceStacks.has(key)) faceStacks.set(key, []);
    faceStacks.get(key).push({ ...face, key, v: (face.v ?? []).map(vertex => vertex.slice()) });
  }
  const frontierPoints = new Map((snapshot?.frontier_points ?? []).map(point => [
    frontierPointKey(point),
    { ...point, pos: point.pos?.slice() }
  ]));
  return {
    faceStacks,
    frontierPoints,
    tile_count: snapshot?.tile_count ?? 0,
    tile_counts: snapshot?.tile_counts ?? [],
    frontier_stats: snapshot?.frontier_stats ?? null,
    search_stats: snapshot?.search_stats ?? null
  };
}

function applyGrowthHistoryDelta(model, delta) {
  if (!model || !delta) return model;
  const frontierKeys = delta.frontier_face_keys ?? [];
  const coveredKeys = delta.covered_face_keys ?? [];
  if (delta.action === "add") {
    for (const key of coveredKeys) {
      for (const face of model.faceStacks.get(key) ?? []) face.internal = true;
    }
    for (const face of delta.faces ?? []) {
      const key = displayFaceKey(face);
      if (!model.faceStacks.has(key)) model.faceStacks.set(key, []);
      model.faceStacks.get(key).push({ ...face, key, v: (face.v ?? []).map(vertex => vertex.slice()) });
    }
  } else if (delta.action === "remove") {
    for (const key of [...frontierKeys, ...coveredKeys]) {
      const stack = model.faceStacks.get(key);
      if (!stack) continue;
      stack.pop();
      if (!stack.length) model.faceStacks.delete(key);
    }
    for (const key of coveredKeys) {
      const stack = model.faceStacks.get(key);
      if (stack?.length === 1) stack[0].internal = false;
    }
  }
  for (const point of delta.lattice_updates ?? []) {
    const key = frontierPointKey(point);
    if (point.frontier) model.frontierPoints.set(key, { ...point, pos: point.pos?.slice() });
    else model.frontierPoints.delete(key);
  }
  model.tile_count = delta.tile_count ?? model.tile_count;
  model.tile_counts = delta.tile_counts ?? model.tile_counts;
  model.frontier_stats = delta.frontier_stats ?? model.frontier_stats;
  model.search_stats = delta.search_stats ?? model.search_stats;
  return model;
}

function growthSnapshotFromModel(model) {
  if (!model) return null;
  return {
    type: "full_update",
    tile_count: model.tile_count,
    tile_counts: model.tile_counts,
    faces: [...model.faceStacks.values()].flat().map(face => ({
      ...face,
      v: (face.v ?? []).map(vertex => vertex.slice())
    })),
    frontier_points: [...model.frontierPoints.values()].map(point => ({
      ...point,
      pos: point.pos?.slice()
    })),
    frontier_stats: model.frontier_stats,
    search_stats: model.search_stats
  };
}

function growthSnapshotAt(series, pointIndex) {
  if (!Number.isInteger(pointIndex)) return series?.snapshot ?? null;
  let model = null;
  for (let index = 0; index <= pointIndex; index += 1) {
    const point = series?.points?.[index];
    if (point?.historySnapshot) model = createGrowthHistoryModel(point.historySnapshot);
    else if (point?.historyDelta) model = applyGrowthHistoryDelta(model, point.historyDelta);
    else if (point?.snapshot) model = createGrowthHistoryModel(point.snapshot);
  }
  return growthSnapshotFromModel(model);
}

function appendGrowthHistorySamples(series, samples) {
  for (const sample of samples ?? []) {
    const point = {
      ...sample.point,
      historySnapshot: sample.snapshot ?? null,
      historyDelta: sample.delta ?? null
    };
    series.points.push(point);
    if (sample.snapshot) series.historyModel = createGrowthHistoryModel(sample.snapshot);
    else if (sample.delta) series.historyModel = applyGrowthHistoryDelta(series.historyModel, sample.delta);
  }
  series.snapshot = growthSnapshotFromModel(series.historyModel) ?? series.snapshot;
}

function updateGrowthHistoryButtons() {
  const modeId = selectedGrowthMode();
  const indices = growthHistorySnapshotIndices(growthSeries.get(modeId));
  const pointIndex = growthInspection.modeId === modeId ? growthInspection.pointIndex : null;
  const position = pointIndex == null
    ? indices.length
    : indices.indexOf(pointIndex);
  growthHistoryBack.disabled = !indices.length || position <= 0;
  growthHistoryForward.disabled = pointIndex == null;
}

function stepGrowthHistory(direction) {
  const modeId = selectedGrowthMode();
  const indices = growthHistorySnapshotIndices(growthSeries.get(modeId));
  if (!indices.length) return;
  const pointIndex = growthInspection.modeId === modeId ? growthInspection.pointIndex : null;
  const position = pointIndex == null
    ? indices.length
    : indices.indexOf(pointIndex);
  if (direction < 0) {
    if (position <= 0) return;
    showGrowthSnapshot(modeId, indices[position - 1]);
  } else {
    if (pointIndex == null) return;
    const nextPosition = position + 1;
    showGrowthSnapshot(modeId, nextPosition < indices.length ? indices[nextPosition] : null);
  }
  renderGrowthChart();
}

function showGrowthSnapshot(modeId, pointIndex = null) {
  const series = growthSeries.get(modeId);
  const inspectedPoint = Number.isInteger(pointIndex) ? series?.points?.[pointIndex] : null;
  const snapshot = growthSnapshotAt(series, Number.isInteger(pointIndex) ? pointIndex : null);
  growthInspection = {
    modeId,
    pointIndex: inspectedPoint && snapshot ? pointIndex : null
  };
  const modeLabel = series?.mode?.label
    ?? GROWTH_MODES.find(mode => mode.id === modeId)?.label
    ?? modeId;
  if (growthInspection.pointIndex == null) {
    growthViewState.textContent = `Current · ${modeLabel}`;
  } else {
    growthViewState.textContent = `Sample · ${modeLabel} · ${inspectedPoint.tiles} tiles at ${(inspectedPoint.milliseconds / 1000).toFixed(2)}s`;
  }
  updateGrowthHistoryButtons();
  if (!snapshot) return;
  if (series.prototileInfo) initTileControls(series.prototileInfo);
  lastSnapshot = snapshot;
  updateScene(snapshot, { preserveView: true });
  const displayedPoint = growthInspection.pointIndex == null ? series.points?.at(-1) : inspectedPoint;
  const tiles = displayedPoint?.tiles ?? snapshot.tile_count ?? 0;
  const time = displayedPoint ? ` at ${(displayedPoint.milliseconds / 1000).toFixed(2)}s` : "";
  setStatus(`${modeLabel}: ${tiles} tiles${time}${growthInspection.pointIndex == null ? " · current" : " · historical sample"}`);
}

function showSelectedGrowthSnapshot() {
  const modeId = selectedGrowthMode();
  showGrowthSnapshot(modeId, null);
}

function scheduleGrowthUiRefresh({ showCurrent = false } = {}) {
  growthUiRefreshShowCurrent ||= showCurrent;
  if (growthUiRefreshTimer) return;
  growthUiRefreshTimer = setTimeout(() => {
    growthUiRefreshTimer = null;
    const shouldShowCurrent = growthUiRefreshShowCurrent;
    growthUiRefreshShowCurrent = false;
    if (shouldShowCurrent) showSelectedGrowthSnapshot();
    renderGrowthChart();
  }, 300);
}

function handleGrowthPlotClick(event) {
  const modeId = selectedGrowthMode();
  const selectedPoint = event?.points?.[0];
  if (!selectedPoint) return;
  const [clickedModeId, pointIndex] = selectedPoint.customdata ?? [];
  if (clickedModeId !== modeId || !Number.isInteger(pointIndex)) return;
  showGrowthSnapshot(modeId, pointIndex);
  renderGrowthChart();
}

function growthEventIsNearPoint(event) {
  if (event.target?.closest?.(".point")) return true;
  const threshold = 13;
  return [...growthChart.querySelectorAll(".point")].some(point => {
    const bounds = point.getBoundingClientRect();
    const centerX = bounds.left + bounds.width / 2;
    const centerY = bounds.top + bounds.height / 2;
    return Math.hypot(event.clientX - centerX, event.clientY - centerY) <= threshold;
  });
}

async function renderGrowthChart() {
  const plotly = window.Plotly;
  const revision = ++growthPlotRevision;
  const allPoints = [...growthSeries.values()].flatMap(series => series.points ?? []);
  updateGrowthHistoryButtons();
  if (!plotly?.react) {
    growthChart.replaceChildren();
    const fallback = document.createElement("div");
    fallback.className = "growth-empty";
    fallback.textContent = "Interactive chart unavailable.";
    growthChart.appendChild(fallback);
    return;
  }

  const activeMode = selectedGrowthMode();
  const traces = GROWTH_MODES.map(mode => {
    const series = growthSeries.get(mode.id);
    const points = series?.points ?? [];
    const inspectable = mode.id === activeMode;
    const selectedIndex = mode.id === activeMode ? growthInspection.pointIndex : null;
    return {
      type: "scatter",
      mode: inspectable ? "lines+markers" : "lines",
      name: mode.label,
      x: points.map(point => point.milliseconds / 1000),
      y: points.map(point => point.tiles),
      customdata: points.map((_, index) => inspectable ? [mode.id, index] : null),
      line: {
        color: mode.color,
        width: mode.id === activeMode ? 3.5 : 2.2,
        dash: mode.dash,
        shape: "hv"
      },
      marker: {
        color: mode.color,
        symbol: mode.symbol,
        size: points.map((_, index) => index === selectedIndex ? 13 : mode.id === activeMode ? 8 : 6),
        line: {
          color: points.map((_, index) => index === selectedIndex ? "#ffffff" : mode.color),
          width: points.map((_, index) => index === selectedIndex ? 3 : 1.5)
        }
      },
      opacity: mode.id === activeMode ? 1 : 0.28,
      hoverinfo: inspectable ? "all" : "skip",
      hovertemplate: inspectable
        ? `<b>${mode.label}</b><br>%{y} tiles<br>%{x:.2f} seconds<extra></extra>`
        : undefined
    };
  });

  const hasPoints = allPoints.length > 0;
  const layout = {
    autosize: true,
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(246,248,245,0.7)",
    margin: { l: 52, r: 18, t: 42, b: 42 },
    font: {
      family: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      color: "#62716b",
      size: 11
    },
    hovermode: "closest",
    clickmode: "event",
    clickanywhere: false,
    dragmode: false,
    showlegend: hasPoints,
    legend: {
      orientation: "h",
      x: 0,
      xanchor: "left",
      y: 1.16,
      yanchor: "top",
      bgcolor: "rgba(255,255,255,0)",
      font: { size: 10 },
      itemclick: false,
      itemdoubleclick: false
    },
    xaxis: {
      visible: hasPoints,
      title: { text: "Elapsed time (seconds)", standoff: 10, font: { size: 11 } },
      rangemode: "tozero",
      fixedrange: true,
      showline: false,
      zeroline: false,
      gridcolor: "rgba(98,113,107,0.13)",
      tickcolor: "rgba(98,113,107,0.25)",
      automargin: true
    },
    yaxis: {
      visible: hasPoints,
      title: { text: "Tiles", standoff: 8, font: { size: 11 } },
      rangemode: "tozero",
      fixedrange: true,
      showline: false,
      zeroline: false,
      gridcolor: "rgba(98,113,107,0.13)",
      tickcolor: "rgba(98,113,107,0.25)",
      automargin: true,
      dtick: hasPoints && Math.max(...allPoints.map(point => point.tiles)) <= 12 ? 2 : undefined
    },
    annotations: hasPoints ? [] : [{
      x: 0.5,
      y: 0.5,
      xref: "paper",
      yref: "paper",
      text: "Run the comparison to measure this tile system.",
      showarrow: false,
      font: { color: "#62716b", size: 12 }
    }],
    transition: { duration: 160, easing: "cubic-in-out" }
  };

  await plotly.react(growthChart, traces, layout, {
    responsive: true,
    displayModeBar: false,
    displaylogo: false,
    staticPlot: false
  });
  if (revision !== growthPlotRevision) return;
  if (!growthPlotClickBound && typeof growthChart.on === "function") {
    growthChart.on("plotly_click", handleGrowthPlotClick);
    growthPlotClickBound = true;
  }
  if (!growthPlotLegendBound && typeof growthChart.on === "function") {
    const keepGrowthLegendReadOnly = () => false;
    growthChart.on("plotly_legendclick", keepGrowthLegendReadOnly);
    growthChart.on("plotly_legenddoubleclick", keepGrowthLegendReadOnly);
    growthPlotLegendBound = true;
  }
  if (!growthPlotBackgroundBound) {
    growthChart.addEventListener("click", event => {
      growthPointerWasNearPoint = growthEventIsNearPoint(event);
      if (growthPointerWasNearPoint) return;
      queueMicrotask(() => {
        const modeId = selectedGrowthMode();
        showGrowthSnapshot(modeId, null);
        renderGrowthChart();
      });
    }, true);
    growthChart.addEventListener("pointerdown", event => {
      growthPointerWasNearPoint = growthEventIsNearPoint(event);
    }, true);
    growthPlotBackgroundBound = true;
  }
}

function formatMemoryBytes(bytes) {
  const value = Math.max(0, Number(bytes) || 0);
  if (value < 1024) return `${Math.round(value)} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KiB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MiB`;
}

function formatGrowthResult(result, target) {
  const proofMode = result?.mode?.startsWith("proof");
  const stopReason = {
    node_limit: "node limit",
    time_limit: "time limit",
    generation_band_pruning: "generation-band pruning",
    configured_branch_pruning: "configured branch pruning"
  }[result?.stats?.termination_reason] ?? null;
  const stopSuffix = result?.searchIncomplete && stopReason ? ` · ${stopReason}` : "";
  const learningMilliseconds =
    (result?.stats?.agent_score_time_ms ?? 0) + (result?.stats?.agent_training_time_ms ?? 0);
  const learnedBytes = result?.memory?.learnedPayloadBytes ?? 0;
  const certificateBytes = result?.memory?.certificatePayloadBytes ?? 0;
  const searchCacheEntries = result?.memory?.transientSearchCacheEntries ?? 0;
  const certificateMemory = certificateBytes
    ? ` · certificate ${formatMemoryBytes(certificateBytes)}`
    : "";
  const memorySuffix = ` · learned ${formatMemoryBytes(learnedBytes)}${certificateMemory} · search cache ${searchCacheEntries} states`;
  const gctsClauses = result?.memory?.markingClauses ?? 0;
  const gctsPrunes = (result?.stats?.marking_geometric_prunes ?? 0)
    + (result?.stats?.generic_geometric_nogood_prunes ?? 0);
  const learningSuffix = result?.mode === "gcts_rl"
    ? ` (RL ${result.stats?.agent_model_weight_count ?? result.stats?.agent_learned_tags ?? 0} weights; GCTS ${gctsClauses} failures, ${gctsPrunes} reuses; learner ${formatElapsed(learningMilliseconds)})`
    : result?.mode === "gcts"
    ? ` (learned ${gctsClauses}, reused ${gctsPrunes})`
    : result?.mode === "rl"
      ? ` (learned ${result.stats?.agent_model_weight_count ?? result.stats?.agent_learned_tags ?? 0} geometric weights; learner ${formatElapsed(learningMilliseconds)})`
    : "";
  const targetPoint = result?.points?.find(point => point.tiles >= target);
  if (result?.resultKind === "known_aperiodic_construction") {
    return `${result.label} · known SCD construction to ${target} tiles ${formatElapsed(targetPoint?.milliseconds ?? result.milliseconds)}`;
  }
  if (result?.criterion === "shell") {
    const shell = result.targetValue ?? target;
    if (result.resultKind === "no_tiling" && result.certified && result.canTile === false) {
      return `${result.label} certified that shell ${shell} is impossible, hence no tiling exists ${formatElapsed(result.milliseconds)}${memorySuffix}`;
    }
    if (result.success) {
      return `${result.label} completed shell ${shell} with ${result.tileCount} tiles ${formatElapsed(result.milliseconds)}${learningSuffix}${memorySuffix}`;
    }
    const maxShell = result.stats?.max_complete_shell_depth ?? 0;
    const maxLive = result.stats?.max_live_tiles ?? result.tileCount ?? 0;
    return `${result.label} inconclusive · max shell ${maxShell} · max ${maxLive} live${stopSuffix}${learningSuffix}${memorySuffix}`;
  }
  if (
    proofMode
    && result?.certified
    && result?.canTile === false
    && result?.certificateKind === "finite_shell_obstruction"
  ) {
    return `${result.label} certified shell ${result.certificateTargetShell ?? target} impossible ${formatElapsed(result.milliseconds)}`;
  }
  if (proofMode && result?.criterion === "shell" && result?.success) {
    return `${result.label} completed shell ${result.targetValue ?? target} with ${result.tileCount} tiles ${formatElapsed(result.milliseconds)}`;
  }
  if (proofMode && result?.criterion === "shell") {
    return `${result.label} inconclusive · max complete shell ${result.stats?.max_complete_shell_depth ?? 0} · max ${result.stats?.max_live_tiles ?? result.tileCount ?? 0} live${stopSuffix}`;
  }
  if (
    proofMode
    && result?.certified
    && result?.canTile === false
    && result?.certificateKind === "finite_patch_obstruction"
  ) {
    const patchSize = result.certificateTargetTiles ?? target;
    return `${result.label} certified no connected ${patchSize}-tile patch ${formatElapsed(result.milliseconds)}`;
  }
  if (
    proofMode
    && result?.certified
    && result?.canTile === true
    && result?.certificateSource === "gcts_growth_checkpoint"
  ) {
    return `${result.label} certified a ${result.certificatePatchSize}-tile checkpoint as a translational quotient ${formatElapsed(result.milliseconds)}`;
  }
  if (proofMode && targetPoint && result?.stats?.generic_periodic_certificate_attempted) {
    const patchSize = target;
    const completedChecks = result.stats.generic_periodic_certificate_checks_completed ?? 0;
    const checkpointSuffix = completedChecks > 1 ? ` · ${completedChecks} exact patch checkpoints` : "";
    if (result.stats.generic_periodic_certificate_target_found) {
      const motifSize = result.certificatePatchSize ?? patchSize;
      if (motifSize < patchSize) {
        return `${result.label} reached ${patchSize} tiles; certified an embedded ${motifSize}-tile translational quotient ${formatElapsed(result.milliseconds)}`;
      }
      return `${result.label} certified the ${patchSize}-tile target patch as a translational quotient ${formatElapsed(result.milliseconds)}`;
    }
    if (result.stats.generic_periodic_certificate_target_completed) {
      return `${result.label} reached ${patchSize} tiles; that target patch is not a translational quotient${checkpointSuffix} ${formatElapsed(result.milliseconds)}`;
    }
    return `${result.label} reached ${patchSize} tiles; target-patch quotient check timed out ${formatElapsed(result.milliseconds)}`;
  }
  if (result?.mode === "isohedral" && result?.resultKind === "certified_tiling") {
    return `${result.label} certified ${result.certificatePatchSize ?? "finite"}-tile unit cell ${formatElapsed(result.milliseconds)}`;
  }
  if (result?.mode === "isohedral" && !result?.success) {
    const maxLive = result.stats?.max_live_tiles ?? result.tileCount ?? 0;
    const attempts = result.stats?.isohedral_certificate_attempts ?? 0;
    const reused = result.stats?.isohedral_certificate_duplicate_states_skipped ?? 0;
    const effort = `max ${maxLive} live · ${attempts} quotient check${attempts === 1 ? "" : "s"}${reused ? ` · ${reused} reused` : ""}`;
    return `${result.label} inconclusive · ${effort}`;
  }
  if (result?.mode === "translational" && !result?.success) {
    if (result.stats?.termination_reason === "translational_growth_goal_without_certificate") {
      const reached = result.criterion === "shell"
        ? `shell ${result.targetValue}`
        : result.criterion === "count"
          ? `${result.targetValue}-tile goal`
          : `${result.criterion} ${result.targetValue}`;
      return `${result.label} reached ${reached}; inconclusive (no translational certificate through that patch)`;
    }
    const checked = result.checkedPatchSize ?? 0;
    return `${result.label} inconclusive · checked through ${checked}-tile patches`;
  }
  if (["gcts", "gcts_rl"].includes(result?.mode) && result?.resultKind === "no_tiling") {
    return `${result.label} certified that no tiling is possible ${formatElapsed(result.milliseconds)}`;
  }
  if (["gcts", "gcts_rl"].includes(result?.mode) && result?.searchIncomplete) {
    const maxLive = result.stats?.max_live_tiles ?? result.tileCount ?? 0;
    return `${result.label} inconclusive · max ${maxLive} live${stopSuffix}${learningSuffix}`;
  }
  if (!result?.success && result?.canTile == null) {
    const maxLive = result?.stats?.max_live_tiles ?? result?.tileCount ?? 0;
    return `${result?.label ?? "run"} inconclusive · max ${maxLive} live${stopSuffix}${learningSuffix}`;
  }
  if (targetPoint) {
    const witness = result?.mode === "translational" && result?.resultKind === "certified_tiling"
        ? ` certified ${result.certificatePatchSize ?? "finite"}-tile unit cell`
        : "";
    return `${result.label}${witness} ${formatElapsed(targetPoint.milliseconds)}${learningSuffix}`;
  }
  return `${result?.label ?? "run"} ${result?.tileCount ?? 0} tiles in ${formatElapsed(result?.milliseconds ?? 0)}${learningSuffix}${stopSuffix}`;
}

function finishGrowthBenchmark(results) {
  growthRunning = false;
  growthPaused = false;
  growthPausedModes.clear();
  setRunButton();
  const target = criterion() === "shell"
    ? Number(shellInput.value) || 1
    : criterion() === "count"
      ? Number(maxTilesInput.value) || 1
      : Number(layerInput.value) || 1;
  const preprocessing = results.map(result =>
    `${result.label} ${(result.preprocessingMilliseconds ?? 0).toFixed(1)}ms`
  ).join(" · ");
  const searches = results.map(result => formatGrowthResult(result, target)).join(" · ");
  growthBenchmarkStatus.textContent = `Preprocessing (excluded): ${preprocessing} · Search: ${searches}`;
  setStatus("All six lanes finished.");
  renderGrowthChart();
}

function stopGrowthBenchmark(status = "Comparison stopped.") {
  growthSequence += 1;
  for (const worker of growthWorkers.values()) {
    worker.postMessage({ type: "stop" });
    worker.terminate();
  }
  growthWorkers.clear();
  growthRunning = false;
  growthPaused = false;
  growthPausedModes.clear();
  setRunButton();
  growthBenchmarkStatus.textContent = status;
  setStatus(status);
}

function pauseGrowthBenchmark() {
  if (!growthRunning || growthPaused || !growthWorkers.size) return;
  growthPaused = true;
  growthPausedModes.clear();
  for (const worker of growthWorkers.values()) {
    worker.postMessage({ type: "pause", sequence: growthSequence });
  }
  setRunButton();
  setStatus("Pausing active lanes at their next safe search checkpoint…");
}

function extendGrowthBenchmark() {
  if (!growthRunning || !growthWorkers.size) return;
  const additionalSeconds = Math.max(1, Number(timeCapInput.value) || 60);
  const additionalTimeMs = additionalSeconds * 1000;
  for (const worker of growthWorkers.values()) {
    worker.postMessage({
      type: "extend-time",
      sequence: growthSequence,
      additionalTimeMs
    });
  }
  growthPaused = false;
  growthPausedModes.clear();
  setRunButton();
  setStatus(`Added ${additionalSeconds}s to ${growthWorkers.size} active lane${growthWorkers.size === 1 ? "" : "s"}.`);
  growthBenchmarkStatus.textContent = `${growthBenchmarkStatus.textContent} · +${additionalSeconds}s added to active lanes`;
}

function startGrowthBenchmark() {
  if (!hasRunnableSelection()) {
    growthBenchmarkStatus.textContent = "Choose a figure or enable a custom lattice tile first.";
    return;
  }
  if (running || paused) {
    stopSolverWorker();
    runSeq += 1;
    running = false;
    paused = false;
    setRunButton();
    setStatus("Stopped main run for a fair growth comparison.");
  }
  if (growthWorkers.size) stopGrowthBenchmark();
  resetRunView();
  growthPaused = false;
  growthPausedModes.clear();
  growthSeries.clear();
  growthInspection = { modeId: selectedGrowthMode(), pointIndex: null };
  for (const mode of GROWTH_MODES) {
    growthSeries.set(mode.id, { mode, points: [], snapshot: null, result: null, status: "starting" });
  }
  renderGrowthChart();
  growthSequence += 1;
  const sequence = growthSequence;
  const config = JSON.parse(configKey());
  config.ui_yield_interval_ms = 250;
  growthRunning = true;
  setRunButton();
  setStatus("Preprocessing tile orientations for all six lanes…");
  const targetLabel = config.criterion === "shell"
    ? `shell ${config.target_val}`
    : config.criterion === "count"
      ? `${config.target_val} tiles`
      : `${config.criterion} ${config.target_val}`;
  growthBenchmarkStatus.textContent = `Preprocessing six lanes before the shared start barrier…`;
  const readyModes = new Set();
  const preprocessingFingerprints = new Set();
  let benchmarkStarted = false;

  const refreshStatus = () => {
    const summaries = GROWTH_MODES.map(mode => {
      const series = growthSeries.get(mode.id);
      const latest = series?.points?.at(-1);
      if (series?.result) return formatGrowthResult(series.result, config.target_val);
      if (series?.status && !["running", "starting"].includes(series.status)) return `${mode.label}: ${series.status}`;
      return `${mode.label} ${latest?.tiles ?? 0}`;
    });
    growthBenchmarkStatus.textContent = summaries.join(" · ");
  };

  const finishWorker = (modeId) => {
    growthWorkers.get(modeId)?.terminate();
    growthWorkers.delete(modeId);
    growthPausedModes.delete(modeId);
    if (!growthWorkers.size) {
      finishGrowthBenchmark(GROWTH_MODES.map(mode => growthSeries.get(mode.id)?.result).filter(Boolean));
    } else {
      if (growthPausedModes.size === growthWorkers.size) growthPaused = true;
      setRunButton();
      refreshStatus();
    }
  };

  for (const mode of GROWTH_MODES) {
    const worker = new Worker(new URL("./growth-benchmark-worker.js?v=20260827-a2-size7-v226", import.meta.url), { type: "module" });
    growthWorkers.set(mode.id, worker);
    setRunButton();
    worker.addEventListener("message", event => {
      const message = event.data ?? {};
      if (message.sequence !== sequence) return;
      const series = growthSeries.get(mode.id);
      if (!series) return;
      if (message.type === "series-start") {
        series.mode = message.mode;
        series.status = "running";
      } else if (message.type === "mode-ready") {
        series.preprocessingMilliseconds = message.preprocessingMilliseconds;
        series.preprocessing = message.preprocessing;
        series.status = `ready · ${message.preprocessing?.orientation_count ?? 0} orientations · stabilizer computed · ${formatElapsed(message.preprocessingMilliseconds ?? 0)} prep`;
        readyModes.add(mode.id);
        if (message.preprocessing?.fingerprint) preprocessingFingerprints.add(message.preprocessing.fingerprint);
        if (readyModes.size === GROWTH_MODES.length && !benchmarkStarted) {
          if (preprocessingFingerprints.size !== 1) {
            stopGrowthBenchmark("Preprocessing mismatch: the lanes did not receive identical tile geometry.");
            return;
          }
          benchmarkStarted = true;
          const startEpochMs = performance.timeOrigin + performance.now() + 100;
          for (const [readyModeId, readyWorker] of growthWorkers) {
            const readySeries = growthSeries.get(readyModeId);
            if (readySeries) readySeries.status = "at start barrier";
            readyWorker.postMessage({ type: "go", sequence, startEpochMs });
          }
          setStatus(`All six lanes ready; search clock starts after preprocessing.`);
          growthBenchmarkStatus.textContent = `All six lanes ready; starting simultaneously to ${targetLabel}…`;
        }
      } else if (message.type === "prototile-info") {
        series.prototileInfo = message.info;
      } else if (message.type === "mode-status") {
        series.status = message.text;
      } else if (message.type === "mode-paused") {
        growthPausedModes.add(mode.id);
        series.status = `paused at ${formatElapsed(message.milliseconds ?? 0)} · ${message.tiles ?? 0} live · Continue to add clock time`;
        if (growthPausedModes.size === growthWorkers.size) {
          growthPaused = true;
          setRunButton();
        }
      } else if (message.type === "sample-batch") {
        appendGrowthHistorySamples(series, message.samples);
        scheduleGrowthUiRefresh({ showCurrent:
          selectedGrowthMode() === mode.id
          && growthInspection.modeId === mode.id
          && growthInspection.pointIndex == null
          && series.snapshot
        });
      } else if (message.type === "sample") {
        series.points.push({ ...message.point, snapshot: message.snapshot ?? null });
        if (message.snapshot) series.snapshot = message.snapshot;
        renderGrowthChart();
        if (
          selectedGrowthMode() === mode.id
          && growthInspection.modeId === mode.id
          && growthInspection.pointIndex == null
          && message.snapshot
        ) showSelectedGrowthSnapshot();
      } else if (message.type === "series-finished") {
        series.result = message.result;
        const gctsClauses = message.result.memory?.markingClauses ?? 0;
        const gctsPrunes = (message.result.stats?.marking_geometric_prunes ?? 0)
          + (message.result.stats?.generic_geometric_nogood_prunes ?? 0);
        if (mode.id === "gcts_rl") {
          series.status = `RL ${message.result.stats?.agent_model_weight_count ?? 0} weights; GCTS ${gctsClauses} failures / ${gctsPrunes} reuses; ${formatMemoryBytes(message.result.memory?.learnedPayloadBytes)} retained`;
        } else if (mode.id === "gcts") {
          series.status = `learned ${gctsClauses} geometric failures; reused ${gctsPrunes}; ${formatMemoryBytes(message.result.memory?.learnedPayloadBytes)} retained`;
        } else if (mode.id === "rl") {
          series.status = `${message.result.stats?.agent_model_weight_count ?? 0} anonymous geometric weights; ${formatMemoryBytes(message.result.memory?.learnedPayloadBytes)} retained`;
        }
        if (!series.status || ["running", "starting"].includes(series.status)) {
          series.status = message.result.success ? "finished" : message.result.searchIncomplete ? "search limit" : "terminated";
        }
        if (!series.points.length) series.points = message.result.points ?? [];
        renderGrowthChart();
      } else if (message.type === "finished") {
        series.result = message.result;
        const completesBenchmark = growthWorkers.size === 1;
        finishWorker(mode.id);
        if (completesBenchmark) return;
      } else if (message.type === "error") {
        series.status = `error: ${message.error}`;
        if (!benchmarkStarted) {
          stopGrowthBenchmark(`Preprocessing failed for ${mode.label}: ${message.error}`);
          return;
        }
        finishWorker(mode.id);
      }
      refreshStatus();
    });
    worker.addEventListener("error", error => {
      const series = growthSeries.get(mode.id);
      if (series) series.status = `error: ${error.message}`;
      if (!benchmarkStarted) {
        stopGrowthBenchmark(`Preprocessing failed for ${mode.label}: ${error.message}`);
        return;
      }
      finishWorker(mode.id);
    });
    worker.postMessage({
      type: "prepare",
      sequence,
      config,
      mode: mode.id
    });
  }
}

function bindControls() {
  document.querySelectorAll('input[name="criterion"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      updateCriterionUI();
      invalidatePausedRunIfNeeded();
    });
  });

  [maxTilesInput, layerInput, shellInput, regionWidthInput, regionDepthInput, regionHeightInput, snapshotSelect, strategySelect, ...strategyRadios, faceOrderSelect, moveOrderSelect, polycubeLatticeSelect, periodicTileCountSelect, branchCapInput, nodeCapInput, candidateCapInput, timeCapInput, exhaustiveCheckbox, mirrorCheckbox, customPolycubeCheckbox, customNameInput, customPolyhedronCheckbox, customPolyhedronInput].forEach((control) => {
    if (!control) return;
    control.addEventListener("input", invalidatePausedRunIfNeeded);
    control.addEventListener("change", invalidatePausedRunIfNeeded);
  });

  strategyRadios.forEach(radio => radio.addEventListener("change", () => {
    updateStrategyUI();
    showSelectedGrowthSnapshot();
    renderGrowthChart();
  }));
  polycubeLatticeSelect.addEventListener("change", () => {
    refreshFigureSelectionUI();
    if (lastSnapshot) updateScene(lastSnapshot, { preserveView: true, rebuildFaces: false });
  });

  customPolycubeCheckbox.addEventListener("change", handleCustomPolycubeChanged);
  customPolyhedronCheckbox.addEventListener("change", handleCustomPolycubeChanged);
  customPolyhedronInput.addEventListener("input", () => {
    customPolyhedronDefinition();
    if (customPolyhedronCheckbox.checked) handleCustomPolycubeChanged();
  });

  customNameInput.addEventListener("input", () => {
    if (customNameInput.value !== lastAutoCustomName) customNameEdited = true;
    refreshFigureSelectionUI();
  });

  internalCheckbox.addEventListener("change", () => {
    if (lastSnapshot) updateScene(lastSnapshot, { preserveView: true });
  });
  edgesCheckbox.addEventListener("change", () => {
    if (lastSnapshot) updateScene(lastSnapshot, { preserveView: true, rebuildFaces: false });
  });
  autoFitCheckbox.addEventListener("change", () => {
    if (autoFitCheckbox.checked && lastSnapshot) centerOnSnapshot(lastSnapshot, true);
  });

  fitButton.addEventListener("click", () => {
    if (lastSnapshot) centerOnSnapshot(lastSnapshot, true);
  });

  runButton.addEventListener("click", () => {
    if (!growthRunning) startGrowthBenchmark();
    else if (growthPaused) extendGrowthBenchmark();
    else pauseGrowthBenchmark();
  });
  growthHistoryBack.addEventListener("click", () => stepGrowthHistory(-1));
  growthHistoryForward.addEventListener("click", () => stepGrowthHistory(1));

  candidateSearchButton.addEventListener("click", () => {
    applyCandidateSearchPreset();
    setStatus("Long-growth preset ready: six lanes race to shell 2 for up to 60 seconds.");
    setRunButton();
  });

  customBuilderButton.addEventListener("click", openCustomBuilderDialog);
  closeBuilderButton.addEventListener("click", closeCustomBuilderDialog);
  customBuilderDialog.addEventListener("click", (event) => {
    if (event.target === customBuilderDialog) closeCustomBuilderDialog();
  });
  customBuilderDialog.addEventListener("close", () => {
    builderHoverKey = null;
    requestBuilderRender();
  });

  clearBuilderButton.addEventListener("click", () => {
    builderVoxels = new Set(["0,0,0"]);
    builderHoverKey = null;
    renderBuilderVoxels(true);
    invalidatePausedRunIfNeeded();
  });
}

function updateElapsed() {
  if (running || paused || isFinished) {
    const base = startedAt || performance.now();
    elapsedTime.textContent = formatElapsed(performance.now() - base);
  }
}

function animate() {
  window.requestAnimationFrame(animate);
  if (controls.update()) requestRender();
  if (builderControls?.update()) requestBuilderRender();
  updateElapsed();
  if (needsRender) {
    renderer.render(scene, camera);
    needsRender = false;
  }
  if (builderNeedsRender && builderRenderer) {
    builderRenderer.render(builderScene, builderCamera);
    builderNeedsRender = false;
  }
}

initFigureSelection();
applySearchParams();
{
  const startupParams = new URLSearchParams(window.location.search);
  const hasExplicitSearchSettings = ["criterion", "target", "target_val", "time_limit", "tiling_strategy"]
    .some(name => startupParams.has(name));
  if ((selectedCensusCandidate() || rootFigure()?.aperiodic_tile) && !hasExplicitSearchSettings) {
    applyCandidateSearchPreset({ invalidate: false });
  }
}
updateCriterionUI();
updateStrategyUI();
applyModeDefaults();
refreshFigureSelectionUI();
bindControls();
setRunButton();
renderGrowthChart();
animate();
void restoreLatestCheckpoint();
