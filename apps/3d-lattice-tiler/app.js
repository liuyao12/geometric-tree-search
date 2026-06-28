import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { tileSpecs } from "./engine.js?v=20260627-frontier-graph";

const $ = (id) => document.getElementById(id);

const selectedTilesEl = $("selectedTiles");
const statusEl = $("status");
const maxTilesInput = $("maxTilesInput");
const layerInput = $("layerInput");
const snapshotSelect = $("snapshotSelect");
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
const polycubeD3Checkbox = $("polycubeD3Checkbox");
const runButton = $("runButton");
const fitButton = $("fitButton");
const maxTileField = $("maxTileField");
const layerField = $("layerField");
const tileList = $("tileList");
const systemTileList = $("systemTileList");
const customPolycubeCheckbox = $("customPolycubeCheckbox");
const customNameInput = $("customNameInput");
const customShapeMatch = $("customShapeMatch");
const polycubeBuilder = $("polycubeBuilder");
const clearBuilderButton = $("clearBuilderButton");
const customBuilderButton = $("customBuilderButton");
const customBuilderDialog = $("customBuilderDialog");
const closeBuilderButton = $("closeBuilderButton");
const treePanel = $("treePanel");
const viewport = $("viewport");
const elapsedTime = $("elapsedTime");

const metricTiles = $("metricTiles");
const metricFrontier = $("metricFrontier");
const metricLayer = $("metricLayer");
const metricLayerDetail = $("metricLayerDetail");
const metricVisited = $("metricVisited");
const metricVisitedDetail = $("metricVisitedDetail");
const metricNodes = $("metricNodes");

const prettyNameMap = new Map([
  ["J15", "Johnson solid J15"],
  ["Gyro", "Gyro polyhedron"],
  ["FriaufPoly", "Friauf polyhedron"],
  ["EscherSolid", "Escher Solid"]
]);

const prettyName = (name) => prettyNameMap.get(name) ?? name;

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
  return value.toFixed(5).replace(/0+$/u, "").replace(/\.$/u, "");
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
let pendingFullUpdate = null;
let fullUpdateRenderQueued = false;

let lastSnapshot = null;
let lastSearchStats = null;
let prototileInfo = null;
let currentOpacities = {};
let rootCentered = false;

const treeMap = new Map();
const pendingSnapshots = new Map();
const expandedNodes = new Set();
const manuallyExpanded = new Set();
let selectedNodeId = null;
let treeRenderQueued = false;
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
scene.add(faceGroup, edgeGroup);

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

function criterion() {
  return document.querySelector('input[name="criterion"]:checked').value;
}

function updateCriterionUI() {
  const byCount = criterion() === "count";
  maxTileField.classList.toggle("is-active", byCount);
  layerField.classList.toggle("is-active", !byCount);
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
  mirrorCheckbox.disabled = !isChiral;
  mirrorCheckbox.parentElement.style.opacity = isChiral ? "1" : "0.45";
  if (!isChiral) mirrorCheckbox.checked = false;
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

function customPolycubeTile() {
  return tileSpecs.buildPolycubeTile(customPolycubeDisplayName(), [...builderVoxels].map(keyToVoxel));
}

function customPolycubeThumbnail(tile) {
  const signature = [...builderVoxels].sort().join("|") || "empty";
  return tileThumbnail(tile, `custom:${signature}`, selectedFigureIds.length);
}

function selectedSystemItems() {
  const items = selectedFigures().map((figure, index) => ({
    id: figure.id,
    name: prettyName(figure.name),
    title: `${figureSourceTitle(figure)}: ${prettyName(figure.name)}`,
    thumbnail: figureThumbnail(figure),
    faceCount: tileFaceCount(tileForFigure(figure)),
    solidAngles: figure.solid_angles ?? tileSpecs.solidAngleValues?.(tileForFigure(figure)) ?? [],
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
      tileIndex: items.length,
      remove: () => {
        customPolycubeCheckbox.checked = false;
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
    label.title = `${item.title}\n${solidAngleTitle(item.solidAngles)}`;

    const faces = document.createElement("span");
    faces.className = "selected-tile-faces";
    faces.textContent = `${item.faceCount} faces`;
    faces.title = `Faces on this tile\n${solidAngleTitle(item.solidAngles)}`;
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
  return {
    name: selectedFigures().map(figure => figure.name).join(" + ") || "Figure system",
    figure_refs: selectedFigureIds,
    polycubes,
    polycube_lattice: polycubeD3Checkbox?.checked ? "d3" : "z3"
  };
}

function hasRunnableSelection() {
  return selectedFigures().length > 0 || customPolycubeCheckbox.checked;
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
  setStatus(hasRunnableSelection() ? "Ready" : "Choose a figure or enable the custom polycube.");
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
      const compatible = isFigureCompatibleWithSelection(figure);
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
      angles.innerHTML = solidAngleListHtml(figure.solid_angles);
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
  const seconds = positiveOrNull(timeCapInput);
  return JSON.stringify({
    mode_key: root?.mode_key ?? "cube",
    custom_system: customSystem,
    criterion: criterion(),
    target_val: criterion() === "count" ? +maxTilesInput.value : +layerInput.value,
    exhaustive: exhaustiveCheckbox.checked,
    include_mirrors: mirrorCheckbox.checked,
    snapshot_every: Number.isFinite(snapshotEvery) ? snapshotEvery : 1,
    face_order: faceOrderSelect.value,
    move_order: moveOrderSelect.value,
    branch_cap: positiveOrNull(branchCapInput),
    node_limit: positiveOrNull(nodeCapInput),
    candidate_cap: positiveOrNull(candidateCapInput),
    time_limit_ms: seconds == null ? null : seconds * 1000,
    ui_yield_interval_ms: 24
  });
}

function setRunButton() {
  if (running) {
    runButton.disabled = false;
    runButton.textContent = "Pause";
    runButton.dataset.state = "pause";
    return;
  }
  if (paused && pausedConfigKey === configKey()) {
    runButton.disabled = false;
    runButton.textContent = "Continue";
    runButton.dataset.state = "continue";
    return;
  }
  runButton.disabled = !hasRunnableSelection();
  runButton.textContent = "Run";
  runButton.dataset.state = "run";
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
  metricFrontier.textContent = frontierPoints;
  metricLayer.textContent = candidateCount;
  metricLayerDetail.textContent = `candidate${candidateCount === 1 ? "" : "s"} for ${frontierPoints} frontier point${frontierPoints === 1 ? "" : "s"}`;
}

function updateSearchMetrics(stats = null) {
  if (stats) lastSearchStats = stats;
  const visitedPercent = stats?.visited_percent ?? 0;
  const progressDepth = stats?.progress_depth ?? stats?.max_depth ?? 0;
  const completedPaths = stats?.progress_completed_paths ?? stats?.visited_nodes ?? treeMap.size;
  const totalPaths = stats?.progress_total_paths ?? stats?.estimated_nodes_at_depth ?? null;
  const completedPathLabel = stats?.progress_completed_paths_label ?? completedPaths;
  const totalPathLabel = stats?.progress_total_paths_label ?? totalPaths;

  metricVisited.textContent = formatVisitedPercent(visitedPercent);
  metricVisitedDetail.textContent = `DFS estimate, depth ${progressDepth}`;
  metricNodes.textContent = totalPathLabel
    ? `${completedPathLabel}/${totalPathLabel} paths`
    : `${completedPaths} paths`;
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

function updateScene(snapshot, options = {}) {
  const { preserveView = false, rebuildFaces = true } = options;
  lastSnapshot = snapshot;

  const faces = snapshot?.faces ?? [];
  const scale = prototileInfo?.scale ?? 2;
  const faceBatches = new Map();
  const edgeBatches = new Map();
  const showInternal = internalCheckbox.checked;
  const showEdges = edgesCheckbox.checked;
  const nextFaceGroup = rebuildFaces ? new THREE.Group() : null;
  const nextEdgeGroup = new THREE.Group();

  for (const face of faces) {
    const alpha = visibleAlpha(face) * (face.internal && !showInternal ? 0.72 : 1);
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
    name.textContent = prettyName(tile.name);
    name.title = `${prettyName(tile.name)}\n${solidAngleTitle(tile.solid_angles)}`;

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
  }
  scheduleTreeRender();
  return node;
}

function attachSnapshotToNode(nodeId, snapshot) {
  if (nodeId == null || !snapshot) return;
  const frozen = clone(snapshot);
  const node = treeMap.get(nodeId);
  if (node) {
    node.snapshot = frozen;
    if (frozen.frontier_stats) node.frontierStats = frozen.frontier_stats;
    scheduleTreeRender();
  } else {
    pendingSnapshots.set(nodeId, frozen);
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
  treeMap.clear();
  pendingSnapshots.clear();
  expandedNodes.clear();
  manuallyExpanded.clear();
  selectedNodeId = null;
  treePanel.replaceChildren();
  metricNodes.textContent = "0 nodes";
}

function scheduleTreeRender() {
  if (treeRenderQueued) return;
  treeRenderQueued = true;
  requestAnimationFrame(() => {
    treeRenderQueued = false;
    renderTree();
  });
}

function renderTree() {
  treePanel.replaceChildren();

  const isGenericBranchLeaf = (node) =>
    node
    && !node.isForced
    && !node.children.length
    && !node.snapshot
    && !node.label
    && !node.statusText
    && !node.resultText;

  const renderBranchSummary = (count, depth) => {
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

  const renderNode = (nodeId, depth) => {
    const node = treeMap.get(nodeId);
    if (!node) return;

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
  if (message.type === "full_update") {
    attachSnapshotToNode(message.node_id, message);
    scheduleFullUpdate(message);
    return;
  }
  if (message.type === "finished") {
    isFinished = true;
    running = false;
    paused = false;
    solverWorkerActive = false;
    if (message.success !== false) revealSuccessPath();
    metricTiles.textContent = message.tile_count ?? metricTiles.textContent;
    if (message.search_stats) updateSearchMetrics(message.search_stats);
    const prefix = message.success === false ? (message.best_effort ? "Stopped: best" : "Stopped") : "Finished";
    setStatus(`${prefix}: ${message.tile_count} tiles`);
    setRunButton();
  }
}

function scheduleFullUpdate(snapshot) {
  pendingFullUpdate = snapshot;
  if (fullUpdateRenderQueued) return;
  fullUpdateRenderQueued = true;
  requestAnimationFrame(() => {
    fullUpdateRenderQueued = false;
    const latest = pendingFullUpdate;
    pendingFullUpdate = null;
    if (latest) updateScene(latest);
  });
}

function ensureSolverWorker() {
  if (solverWorker) return solverWorker;
  solverWorker = new Worker(new URL("./solver-worker.js?v=20260627-frontier-graph", import.meta.url), { type: "module" });
  solverWorker.addEventListener("message", (event) => {
    const { seq, type, message, error } = event.data ?? {};
    if (seq !== runSeq) return;

    if (type === "solver_message") {
      handleMessage(message);
      return;
    }

    if (type === "solver_error") {
      running = false;
      paused = false;
      solverWorkerActive = false;
      setStatus(`Error: ${error}`);
      setRunButton();
      return;
    }

    if (type === "solver_idle" && running && !isFinished) {
      running = false;
      paused = false;
      solverWorkerActive = false;
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
  pendingFullUpdate = null;
}

function resetRunView() {
  rootCentered = false;
  lastSnapshot = null;
  lastSearchStats = null;
  prototileInfo = null;
  currentOpacities = {};
  clearTree();
  clearObjectGroup(faceGroup);
  clearObjectGroup(edgeGroup);
  tileList.replaceChildren();
  updateRunMetrics(null);
  elapsedTime.textContent = "0.0s";
  requestRender();
}

function startNewRun() {
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
  startedAt = performance.now();
  pausedConfigKey = configKey();
  resetRunView();
  setRunButton();
  setStatus("Running...");

  const config = JSON.parse(pausedConfigKey);
  ensureSolverWorker().postMessage({ type: "start", seq: runSeq, config });
}

function continueRun() {
  if (!solverWorkerActive) return startNewRun();
  paused = false;
  running = true;
  setRunButton();
  setStatus("Running...");
  solverWorker?.postMessage({ type: "resume", seq: runSeq });
}

function pauseRun() {
  paused = true;
  running = false;
  solverWorker?.postMessage({ type: "pause", seq: runSeq });
  setRunButton();
  setStatus("Paused");
}

function bindControls() {
  document.querySelectorAll('input[name="criterion"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      updateCriterionUI();
      invalidatePausedRunIfNeeded();
    });
  });

  [maxTilesInput, layerInput, snapshotSelect, faceOrderSelect, moveOrderSelect, branchCapInput, nodeCapInput, candidateCapInput, timeCapInput, exhaustiveCheckbox, mirrorCheckbox, customPolycubeCheckbox, customNameInput].forEach((control) => {
    control.addEventListener("input", invalidatePausedRunIfNeeded);
    control.addEventListener("change", invalidatePausedRunIfNeeded);
  });

  customPolycubeCheckbox.addEventListener("change", handleCustomPolycubeChanged);

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
    if (running) return pauseRun();
    if (paused && pausedConfigKey === configKey() && solverWorkerActive) return continueRun();
    return startNewRun();
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
updateCriterionUI();
applyModeDefaults();
refreshFigureSelectionUI();
bindControls();
setRunButton();
animate();
