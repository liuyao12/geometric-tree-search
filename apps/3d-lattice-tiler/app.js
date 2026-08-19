import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { tileSpecs } from "./engine.js?v=20260818-face-key-v57";
import {
  normalizeProposalProgram,
  proposalTileKey
} from "./proposal-learner.js?v=20260817-generation-band-v31";

const $ = (id) => document.getElementById(id);

const selectedTilesEl = $("selectedTiles");
const candidateResearchPanel = $("candidateResearchPanel");
const candidateResearchTitle = $("candidateResearchTitle");
const candidateResearchDetail = $("candidateResearchDetail");
const candidateSearchButton = $("candidateSearchButton");
const statusEl = $("status");
const maxTilesInput = $("maxTilesInput");
const layerInput = $("layerInput");
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
const growthSeries = new Map();
let growthInspection = { modeId: "free_range", pointIndex: null };
let growthPlotClickBound = false;
let growthPlotBackgroundBound = false;
let growthPointerWasNearPoint = false;
let growthPlotRevision = 0;
const PROPOSAL_CACHE_STORAGE_KEY = "gcts-3d-learned-proposals-v2";
const readProposalCache = () => {
  try {
    const parsed = JSON.parse(localStorage.getItem(PROPOSAL_CACHE_STORAGE_KEY) ?? "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
};
const cachedProposalForConfig = config => {
  const raw = readProposalCache()[proposalTileKey(config)];
  return raw ? normalizeProposalProgram(raw) : null;
};
const rememberLearnedProposal = (config, rawProgram) => {
  if (!rawProgram) return null;
  const program = normalizeProposalProgram(rawProgram);
  const key = proposalTileKey(config);
  const cache = readProposalCache();
  const current = cache[key] ? normalizeProposalProgram(cache[key]) : null;
  if (
    current
    && current.patch.length > program.patch.length
    && current.generation >= program.generation
  ) return current;
  cache[key] = program;
  try {
    localStorage.setItem(PROPOSAL_CACHE_STORAGE_KEY, JSON.stringify(cache));
  } catch {
    return current;
  }
  return program;
};
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

let faceGroup = new THREE.Group();
let edgeGroup = new THREE.Group();
let frontierPointGroup = new THREE.Group();
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
  layerField.classList.toggle("is-active", selected === "layer");
  regionField.classList.toggle("is-active", selected === "region");
  regionSizeFields.classList.toggle("is-hidden", selected !== "region");
}

const STRATEGY_DESCRIPTIONS = {
  free_range: "Prioritizes forced moves, then explores sensible legal placements with backtracking.",
  learning_free_range: "Runs the same tree search, remembers its best legal patch, and replays that proposal on later runs.",
  translational: "Tests increasingly large patches for three exact translation vectors and stops only on a certificate or search limit.",
  isohedral: "Searches tile-transitive patches, then requires an exact periodic quotient preserved by symmetries taking the root to every tile class."
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
  if (criterionParam === "count" || criterionParam === "layer" || criterionParam === "region") {
    document.querySelector(`input[name="criterion"][value="${criterionParam}"]`).checked = true;
  }
  setPositiveNumberParam(maxTilesInput, "target");
  setPositiveNumberParam(maxTilesInput, "target_val");
  setPositiveNumberParam(layerInput, "layer");
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
  const isChiral = selectedFigures().some(figure => figure.is_chiral);
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
  { id: "unresolved", title: "5 unresolved lattice candidates", test: figure => figureHasCategory(figure, "Unresolved Lattice Candidates") },
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

  const savedCriterion = ["count", "layer", "region"].includes(controls.criterion) ? controls.criterion : "count";
  const criterionRadio = document.querySelector(`input[name="criterion"][value="${savedCriterion}"]`);
  if (criterionRadio) criterionRadio.checked = true;
  if (controls.maxTiles != null) maxTilesInput.value = controls.maxTiles;
  if (controls.layer != null) layerInput.value = controls.layer;
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
  if (running || paused || solverWorkerActive) {
    runSeq += 1;
    stopSolverWorker();
    running = false;
    paused = false;
    pausedConfigKey = null;
  }
  isFinished = false;
  resetRunView();
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

function applyCandidateSearchPreset({ invalidate = true } = {}) {
  const knownAperiodic = rootFigure()?.aperiodic_tile ?? null;
  if (!selectedCensusCandidate() && !knownAperiodic) return;
  document.querySelector('input[name="criterion"][value="count"]').checked = true;
  maxTilesInput.value = knownAperiodic ? "80" : "120";
  strategySelect.value = setRadioValue(strategyRadios, "free_range", "free_range");
  faceOrderSelect.value = "mrv";
  moveOrderSelect.value = "balanced";
  snapshotSelect.value = "0";
  timeCapInput.value = knownAperiodic ? "10" : "30";
  nodeCapInput.value = "0";
  candidateCapInput.value = "0";
  branchCapInput.value = "0";
  exhaustiveCheckbox.checked = true;
  mirrorCheckbox.checked = false;
  updateCriterionUI();
  updateStrategyUI();
  if (invalidate) invalidatePausedRunIfNeeded();
}

function updateCandidateResearchPanel() {
  const candidate = selectedCensusCandidate();
  const knownAperiodic = rootFigure()?.aperiodic_tile ?? null;
  candidateResearchPanel.classList.toggle("is-hidden", !candidate && !knownAperiodic);
  candidateSearchButton.classList.toggle("is-hidden", !!knownAperiodic);
  if (candidate) {
    const screening = candidate.last_screening;
    const limits = screening
      ? ` Translational motifs through ${screening.translational.maximum_requested_motif_tiles} tiles (${screening.translational.seconds_per_tile}s); isohedral growth horizon ${screening.isohedral.growth_horizon_tiles} tiles (${screening.isohedral.seconds_per_tile}s).`
      : "";
    candidateResearchTitle.textContent = `Research candidate ${candidate.id}`;
    candidateResearchDetail.textContent = `Survivor ${candidate.survivor_priority}/${candidate.survivor_count ?? 5} · ${candidate.lattice_points} lattice points · no exact translational or tile-transitive quotient certificate found within the recorded search limits.${limits}`;
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
        angles.textContent = `survivor ${figure.census_candidate.survivor_priority}/${figure.census_candidate.survivor_count ?? 5} · ${figure.census_candidate.lattice_points} points`;
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
  const forcedLayerLagCap = positiveSearchParam("generation_lag_cap", "forced_layer_lag_cap", "forced_move_layer_lag_cap") ?? 2;
  const selectedCriterion = criterion();
  const tilingStrategy = checkedRadioValue(strategyRadios, "free_range");
  const isLearningFreeRange = tilingStrategy === "learning_free_range";
  const isStructural = tilingStrategy === "translational" || tilingStrategy === "isohedral";
  const candidateIsohedralHorizon = root?.census_candidate?.last_screening
    ?.isohedral?.growth_horizon_tiles ?? null;
  return JSON.stringify({
    mode_key: root?.mode_key ?? "cube",
    custom_system: customSystem,
    polycube_lattice: selectedPolycubeLattice(),
    criterion: selectedCriterion,
    target_val: selectedCriterion === "count" ? +maxTilesInput.value : +layerInput.value,
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
    move_order: isLearningFreeRange ? "agent" : moveOrderSelect.value,
    greedy_no_backtrack: false,
    agent_exhaustive: true,
    template_preflight: isStructural,
    periodic_patch_unbounded: tilingStrategy === "translational",
    periodic_patch_max_tiles: tilingStrategy === "translational"
      ? null
      : Math.max(1, Number(periodicTileCountSelect.value) || 4),
    periodic_template_max_volume: 512,
    isohedral_search_horizon_tiles:
      positiveSearchParam("isohedral_search_horizon_tiles") ?? candidateIsohedralHorizon,
    forced_move_layer_lag_cap: forcedLayerLagCap,
    branch_cap: positiveOrNull(branchCapInput),
    node_limit: positiveOrNull(nodeCapInput),
    candidate_cap: positiveOrNull(candidateCapInput),
    time_limit_ms: seconds == null ? null : seconds * 1000,
    ui_yield_interval_ms: 24
  });
}

function setRunButton() {
  runButton.disabled = !hasRunnableSelection();
  runButton.textContent = growthRunning ? "Stop" : "Run";
  runButton.dataset.state = growthRunning ? "stop" : "run";
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

function disposeObjectGroup(group) {
  clearObjectGroup(group);
  group.parent?.remove(group);
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
  const layerPointCount = Number.isFinite(stats?.min_layer_point_count) ? stats.min_layer_point_count : frontierPoints;
  metricFrontier.textContent = frontierPoints;
  metricLayer.textContent = minLayer;
  metricLayerDetail.textContent = `active layer · ${layerPointCount} point${layerPointCount === 1 ? "" : "s"} · ${candidateCount} candidate${candidateCount === 1 ? "" : "s"}`;
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
  const { preserveView = false, rebuildFaces = true, syncLive = true } = options;
  lastSnapshot = snapshot;
  if (syncLive && snapshot?.faces) resetLiveFaceStacks(snapshot);
  if (syncLive && snapshot?.frontier_points) resetLiveFrontierPoints(snapshot);

  const faces = snapshot?.faces ?? [];
  const scale = prototileInfo?.scale ?? 2;
  const faceBatches = new Map();
  const edgeBatches = new Map();
  const showInternal = internalCheckbox.checked;
  const showEdges = edgesCheckbox.checked && (!running || faces.length <= RUNNING_EDGE_FACE_LIMIT);
  const nextFaceGroup = rebuildFaces ? new THREE.Group() : null;
  const nextEdgeGroup = new THREE.Group();
  const nextFrontierPointGroup = new THREE.Group();

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
    for (const batch of faceBatches.values()) {
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute("position", new THREE.Float32BufferAttribute(batch.positions, 3));
      geometry.computeVertexNormals();
      const material = new THREE.MeshPhongMaterial({
        color: new THREE.Color(batch.color),
        transparent: batch.alpha < 0.999,
        opacity: batch.alpha,
        side: THREE.DoubleSide,
        flatShading: true,
        polygonOffset: true,
        polygonOffsetFactor: 1,
        polygonOffsetUnits: 1,
        depthWrite: batch.alpha > 0.55
      });
      nextFaceGroup.add(new THREE.Mesh(geometry, material));
    }
  }

  for (const batch of edgeBatches.values()) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(batch.positions, 3));
    const material = new THREE.LineBasicMaterial({
      color: 0x111827,
      transparent: batch.alpha < 0.999,
      opacity: Math.min(0.72, Math.max(0.18, batch.alpha))
    });
    nextEdgeGroup.add(new THREE.LineSegments(geometry, material));
  }

  const pointPositions = [];
  for (const point of snapshot?.frontier_points ?? []) {
    if (!point?.pos?.length) continue;
    pointPositions.push([point.pos[0] / scale, point.pos[1] / scale, point.pos[2] / scale]);
  }
  if (pointPositions.length) {
    const lattice = selectedPolycubeLattice();
    const pointRadius = lattice === "half" ? 0.0425 : 0.06;
    const pointGeometry = new THREE.SphereGeometry(pointRadius, 8, 6);
    const pointMaterial = new THREE.MeshBasicMaterial({
      color: { z3: 0x178273, fcc: 0x315f9f, half: 0xd97706 }[lattice] ?? 0x178273,
      transparent: true,
      opacity: 0.9,
      depthTest: true,
      depthWrite: false
    });
    const pointMesh = new THREE.InstancedMesh(pointGeometry, pointMaterial, pointPositions.length);
    const pointMatrix = new THREE.Matrix4();
    pointPositions.forEach((position, index) => {
      pointMatrix.makeTranslation(position[0], position[1], position[2]);
      pointMesh.setMatrixAt(index, pointMatrix);
    });
    pointMesh.instanceMatrix.needsUpdate = true;
    nextFrontierPointGroup.add(pointMesh);
  }

  if (rebuildFaces) {
    const oldFaceGroup = faceGroup;
    faceGroup = nextFaceGroup;
    scene.add(faceGroup);
    disposeObjectGroup(oldFaceGroup);
  }
  const oldEdgeGroup = edgeGroup;
  edgeGroup = nextEdgeGroup;
  scene.add(edgeGroup);
  disposeObjectGroup(oldEdgeGroup);
  const oldFrontierPointGroup = frontierPointGroup;
  frontierPointGroup = nextFrontierPointGroup;
  scene.add(frontierPointGroup);
  disposeObjectGroup(oldFrontierPointGroup);

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
      : `No ${message.patch_size}-tile patch; checking the next size…`);
    return;
  }
  if (message.type === "full_update") {
    attachSnapshotToNode(message.node_id, message);
    if ((message.tile_count ?? 0) <= 1) {
      flushFullUpdateNow();
      updateScene(message);
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
    const prefix = message.result_kind === "certified_tiling"
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
  solverWorker = new Worker(new URL("./solver-worker.js?v=20260818-face-key-v57", import.meta.url), { type: "module" });
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
  { id: "free_range", strategy: "free_range", label: "Free-range · balanced", color: "#6f7c77", symbol: "square-open", dash: "dash" },
  { id: "no_brainer", strategy: "free_range", label: "Free-range · no-brainer", color: "#b86442", symbol: "cross-open", dash: "dot" },
  { id: "proof", strategy: "free_range", label: "Proof search · unbanded", color: "#252b29", symbol: "triangle-down-open", dash: "longdash" },
  { id: "learning", strategy: "learning_free_range", label: "Learning Free-range", color: "#178273", symbol: "diamond", dash: "solid" },
  { id: "translational", strategy: "translational", label: "Translational", color: "#315f9f", symbol: "circle-open", dash: "solid" },
  { id: "isohedral", strategy: "isohedral", label: "Isohedral", color: "#7656a5", symbol: "triangle-up-open", dash: "solid" }
];

function selectedGrowthMode() {
  const strategy = checkedRadioValue(strategyRadios, "free_range");
  if (strategy === "free_range") return moveOrderSelect.value === "no_brainer" ? "no_brainer" : "free_range";
  return GROWTH_MODES.find(mode => mode.strategy === strategy)?.id ?? "free_range";
}

function activateGrowthMode(modeId) {
  const mode = GROWTH_MODES.find(candidate => candidate.id === modeId);
  if (!mode) return;
  setRadioValue(strategyRadios, mode.strategy, "free_range");
  strategySelect.value = mode.strategy;
  if (mode.id === "free_range") moveOrderSelect.value = "balanced";
  if (mode.id === "no_brainer") moveOrderSelect.value = "no_brainer";
  if (mode.id === "proof") moveOrderSelect.value = "balanced";
  updateStrategyUI();
}

function showGrowthSnapshot(modeId, pointIndex = null) {
  const series = growthSeries.get(modeId);
  const inspectedPoint = Number.isInteger(pointIndex) ? series?.points?.[pointIndex] : null;
  const snapshot = inspectedPoint?.snapshot ?? (pointIndex == null ? series?.snapshot : null);
  growthInspection = {
    modeId,
    pointIndex: inspectedPoint?.snapshot ? pointIndex : null
  };
  const modeLabel = series?.mode?.label
    ?? GROWTH_MODES.find(mode => mode.id === modeId)?.label
    ?? modeId;
  if (growthInspection.pointIndex == null) {
    growthViewState.textContent = `Current · ${modeLabel}`;
  } else {
    growthViewState.textContent = `Sample · ${modeLabel} · ${inspectedPoint.tiles} tiles at ${(inspectedPoint.milliseconds / 1000).toFixed(2)}s`;
  }
  if (!snapshot) return;
  if (series.prototileInfo) initTileControls(series.prototileInfo);
  lastSnapshot = snapshot;
  rootCentered = false;
  updateScene(snapshot, { preserveView: false });
  const displayedPoint = growthInspection.pointIndex == null ? series.points?.at(-1) : inspectedPoint;
  const tiles = displayedPoint?.tiles ?? snapshot.tile_count ?? 0;
  const time = displayedPoint ? ` at ${(displayedPoint.milliseconds / 1000).toFixed(2)}s` : "";
  setStatus(`${modeLabel}: ${tiles} tiles${time}${growthInspection.pointIndex == null ? " · current" : " · historical sample"}`);
}

function showSelectedGrowthSnapshot() {
  const modeId = selectedGrowthMode();
  showGrowthSnapshot(modeId, null);
}

function handleGrowthPlotClick(event) {
  const selectedPoint = event?.points?.[0];
  if (!selectedPoint || !growthPointerWasNearPoint) {
    const modeId = growthInspection.modeId ?? selectedGrowthMode();
    activateGrowthMode(modeId);
    showGrowthSnapshot(modeId, null);
    renderGrowthChart();
    return;
  }
  const [modeId, pointIndex] = selectedPoint.customdata ?? [];
  if (!modeId || !Number.isInteger(pointIndex)) return;
  activateGrowthMode(modeId);
  showGrowthSnapshot(modeId, pointIndex);
  renderGrowthChart();
}

async function renderGrowthChart() {
  const plotly = window.Plotly;
  const revision = ++growthPlotRevision;
  const allPoints = [...growthSeries.values()].flatMap(series => series.points ?? []);
  if (!plotly?.react) {
    growthChart.replaceChildren();
    const fallback = document.createElement("div");
    fallback.className = "growth-empty";
    fallback.textContent = "Interactive chart unavailable.";
    growthChart.appendChild(fallback);
    return;
  }

  const activeMode = growthInspection.modeId ?? selectedGrowthMode();
  const traces = GROWTH_MODES.map(mode => {
    const series = growthSeries.get(mode.id);
    const points = series?.points ?? [];
    const selectedIndex = mode.id === activeMode ? growthInspection.pointIndex : null;
    return {
      type: "scatter",
      mode: "lines+markers",
      name: mode.label,
      x: points.map(point => point.milliseconds / 1000),
      y: points.map(point => point.tiles),
      customdata: points.map((_, index) => [mode.id, index]),
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
      hovertemplate: `<b>${mode.label}</b><br>%{y} tiles<br>%{x:.2f} seconds<extra></extra>`
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
    clickanywhere: true,
    dragmode: false,
    showlegend: hasPoints,
    legend: {
      orientation: "h",
      x: 0,
      xanchor: "left",
      y: 1.16,
      yanchor: "top",
      bgcolor: "rgba(255,255,255,0)",
      font: { size: 10 }
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
  if (!growthPlotBackgroundBound) {
    growthChart.addEventListener("click", event => {
      if (growthPointerWasNearPoint) return;
      queueMicrotask(() => {
        const modeId = growthInspection.modeId ?? selectedGrowthMode();
        activateGrowthMode(modeId);
        showGrowthSnapshot(modeId, null);
        renderGrowthChart();
      });
    }, true);
    growthChart.addEventListener("pointerdown", event => {
      const threshold = 13;
      growthPointerWasNearPoint = [...growthChart.querySelectorAll(".point")].some(point => {
        const bounds = point.getBoundingClientRect();
        const centerX = bounds.left + bounds.width / 2;
        const centerY = bounds.top + bounds.height / 2;
        return Math.hypot(event.clientX - centerX, event.clientY - centerY) <= threshold;
      });
    }, true);
    growthPlotBackgroundBound = true;
  }
}

function formatGrowthResult(result, target) {
  const stopReason = {
    node_limit: "node limit",
    time_limit: "time limit",
    generation_band_pruning: "generation-band pruning",
    configured_branch_pruning: "configured branch pruning"
  }[result?.stats?.termination_reason] ?? null;
  const stopSuffix = result?.searchIncomplete && stopReason ? ` · ${stopReason}` : "";
  const learningSuffix = result?.mode === "learning"
    ? result.reusedLearnedPatch
      ? ` (replayed ${result.stats?.proposal_patch_tiles_replayed ?? 0})`
      : result.learnedProgram?.patch?.length
        ? ` (learned ${result.learnedProgram.patch.length})`
        : ""
    : "";
  const targetPoint = result?.points?.find(point => point.tiles >= target);
  if (result?.resultKind === "known_aperiodic_construction") {
    return `${result.label} · known SCD construction to ${target} tiles ${formatElapsed(targetPoint?.milliseconds ?? result.milliseconds)}`;
  }
  if (
    result?.mode === "proof"
    && result?.certified
    && result?.canTile === false
    && result?.certificateKind === "finite_patch_obstruction"
  ) {
    const patchSize = result.certificateTargetTiles ?? target;
    return `${result.label} certified no connected ${patchSize}-tile patch ${formatElapsed(result.milliseconds)}`;
  }
  if (result?.mode === "isohedral" && result?.resultKind === "certified_tiling") {
    return `${result.label} certified ${result.certificatePatchSize ?? "finite"}-tile unit cell ${formatElapsed(result.milliseconds)}`;
  }
  if (result?.mode === "isohedral" && !result?.success) {
    const maxLive = result.stats?.max_live_tiles ?? result.tileCount ?? 0;
    const attempts = result.stats?.isohedral_certificate_attempts ?? 0;
    const reused = result.stats?.isohedral_certificate_duplicate_states_skipped ?? 0;
    const effort = `max ${maxLive} live · ${attempts} quotient check${attempts === 1 ? "" : "s"}${reused ? ` · ${reused} reused` : ""}`;
    return result.searchIncomplete
      ? `${result.label} inconclusive · ${effort}`
      : `${result.label} exhausted without a certificate · ${effort}`;
  }
  if (result?.mode === "translational" && !result?.success) {
    const checked = result.checkedPatchSize ?? 0;
    return result.searchIncomplete
      ? `${result.label} inconclusive · checked through ${checked}-tile patches`
      : `${result.label} exhausted through ${checked}-tile patches`;
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
  setRunButton();
  const target = Number(maxTilesInput.value) || 1;
  growthBenchmarkStatus.textContent = results.map(result => formatGrowthResult(result, target)).join(" · ");
  setStatus("All six modes finished.");
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
  setRunButton();
  growthBenchmarkStatus.textContent = status;
  setStatus(status);
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
  growthSeries.clear();
  growthInspection = { modeId: selectedGrowthMode(), pointIndex: null };
  for (const mode of GROWTH_MODES) {
    growthSeries.set(mode.id, { mode, points: [], snapshot: null, result: null, status: "starting" });
  }
  renderGrowthChart();
  growthSequence += 1;
  const sequence = growthSequence;
  const config = JSON.parse(configKey());
  config.criterion = "count";
  config.target_val = Math.max(2, Number(maxTilesInput.value) || 2);
  config.ui_yield_interval_ms = 250;
  const cachedLearningProgram = cachedProposalForConfig(config);
  growthRunning = true;
  setRunButton();
  setStatus("Running all six modes…");
  growthBenchmarkStatus.textContent = `Running six searches simultaneously to ${config.target_val} tiles…`;

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
    if (!growthWorkers.size) {
      finishGrowthBenchmark(GROWTH_MODES.map(mode => growthSeries.get(mode.id)?.result).filter(Boolean));
    } else {
      refreshStatus();
    }
  };

  for (const mode of GROWTH_MODES) {
    const worker = new Worker(new URL("./growth-benchmark-worker.js?v=20260818-face-key-v57", import.meta.url), { type: "module" });
    growthWorkers.set(mode.id, worker);
    worker.addEventListener("message", event => {
      const message = event.data ?? {};
      if (message.sequence !== sequence) return;
      const series = growthSeries.get(mode.id);
      if (!series) return;
      if (message.type === "series-start") {
        series.mode = message.mode;
        series.status = "running";
      } else if (message.type === "prototile-info") {
        series.prototileInfo = message.info;
      } else if (message.type === "mode-status") {
        series.status = message.text;
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
        if (mode.id === "learning" && message.result.learnedProgram) {
          const stored = rememberLearnedProposal(config, message.result.learnedProgram);
          if (stored) {
            series.learnedProgram = stored;
            series.status = message.result.reusedLearnedPatch
              ? `reused ${message.result.stats?.proposal_patch_tiles_replayed ?? 0}-tile patch; learned ${stored.patch.length}`
              : `learned ${stored.patch.length}-tile patch for next run`;
          }
        }
        if (!series.status || ["running", "starting"].includes(series.status)) {
          series.status = message.result.success ? "finished" : message.result.searchIncomplete ? "search limit" : "terminated";
        }
        if (!series.points.length) series.points = message.result.points ?? [];
        renderGrowthChart();
      } else if (message.type === "finished") {
        series.result = message.result;
        finishWorker(mode.id);
      } else if (message.type === "error") {
        series.status = `error: ${message.error}`;
        finishWorker(mode.id);
      }
      refreshStatus();
    });
    worker.addEventListener("error", error => {
      const series = growthSeries.get(mode.id);
      if (series) series.status = `error: ${error.message}`;
      finishWorker(mode.id);
    });
    worker.postMessage({
      type: "start",
      sequence,
      config: mode.id === "learning"
        ? { ...config, proposal_program: cachedLearningProgram }
        : config,
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

  [maxTilesInput, layerInput, regionWidthInput, regionDepthInput, regionHeightInput, snapshotSelect, strategySelect, ...strategyRadios, faceOrderSelect, moveOrderSelect, polycubeLatticeSelect, periodicTileCountSelect, branchCapInput, nodeCapInput, candidateCapInput, timeCapInput, exhaustiveCheckbox, mirrorCheckbox, customPolycubeCheckbox, customNameInput, customPolyhedronCheckbox, customPolyhedronInput].forEach((control) => {
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
    if (growthRunning) stopGrowthBenchmark();
    else startGrowthBenchmark();
  });

  candidateSearchButton.addEventListener("click", () => {
    applyCandidateSearchPreset();
    setStatus("Long-growth preset ready: six modes race to 120 tiles for up to 30 seconds.");
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
