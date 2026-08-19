import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  CANONICAL_CHILDREN,
  FACE_DIRECTIONS,
  createGrowthState,
  exposedMarks,
  growOne,
  shrinkOne
} from "./chair-gcts.js";

const viewport = document.getElementById("viewport");
const sceneShell = document.querySelector(".scene-shell");
const inflateButton = document.getElementById("inflate-button");
const backButton = document.getElementById("back-button");
const runButton = document.getElementById("run-button");
const generationValue = document.getElementById("generation-value");
const tileValue = document.getElementById("tile-value");
const generationLabel = document.getElementById("generation-label");
const tileLabel = document.getElementById("tile-label");
const hierarchyPlot = document.getElementById("hierarchy-plot");
const chairColorFilter = document.getElementById("chair-color-filter");
const tileSelect = document.getElementById("tile-select");
const chairModeSelect = document.getElementById("chair-mode-select");
const panelKicker = document.getElementById("panel-kicker");
const hierarchyTitle = document.getElementById("hierarchy-title");
const panelCount = document.getElementById("panel-count");
const panelCountLabel = document.getElementById("panel-count-label");
const panelDescription = document.getElementById("panel-description");
const scaleLeft = document.getElementById("scale-left");
const scaleRight = document.getElementById("scale-right");
const frontierValue = document.getElementById("frontier-value");
const backtrackValue = document.getElementById("backtrack-value");
const sceneInstruction = document.getElementById("scene-instruction");

tileSelect.addEventListener("change", () => {
  window.location.href = tileSelect.value;
});

const MAX_GENERATION = 4;
const ORIENTATION_COLORS = [
  0x4776a8, 0x7a68a6, 0x3d8e84, 0x5aa36f,
  0xd66f57, 0xca6f94, 0xdfb65b, 0xb9944e
];
const CUBE_FACES = [
  [0, 2, 3, 1], [4, 5, 7, 6],
  [0, 1, 5, 4], [2, 6, 7, 3],
  [0, 4, 6, 2], [1, 3, 7, 5]
];
const FACE_NEIGHBORS = FACE_DIRECTIONS;
const CUBE_CORNERS = [
  [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],
  [0, 0, 1], [1, 0, 1], [0, 1, 1], [1, 1, 1]
];

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xedf1ef);

const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 500);
camera.position.set(7.2, 5.6, 8.4);

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
} catch (error) {
  viewport.textContent = "This three-dimensional view needs WebGL.";
  viewport.classList.add("webgl-fallback");
  throw error;
}
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
viewport.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 1.4;
controls.maxDistance = 180;
controls.target.set(0, 0, 0);
controls.update();

const root = new THREE.Group();
scene.add(root);

function add(left, right) {
  return [left[0] + right[0], left[1] + right[1], left[2] + right[2]];
}

function transformedChild(origin4, missing, parentMissing, childSize, parentSize) {
  const factor = childSize / 2;
  const childOrigin = origin4.map((coordinate) => coordinate * factor);
  const childMissing = [...missing];
  for (let axis = 0; axis < 3; axis += 1) {
    if (parentMissing[axis] === 0) {
      childOrigin[axis] = parentSize - childSize - childOrigin[axis];
      childMissing[axis] = 1 - childMissing[axis];
    }
  }
  return [childOrigin, childMissing];
}

function chairLeaves(level, origin = [0, 0, 0], missingCorner = [1, 1, 1], path = []) {
  if (level === 0) return [{ origin, missingCorner, path }];
  const parentSize = 2 ** (level + 1);
  const childSize = parentSize / 2;
  const leaves = [];
  CANONICAL_CHILDREN.forEach(([canonicalOrigin, canonicalMissing], childIndex) => {
    const [relativeOrigin, childMissing] = transformedChild(
      canonicalOrigin,
      canonicalMissing,
      missingCorner,
      childSize,
      parentSize
    );
    leaves.push(...chairLeaves(
      level - 1,
      add(origin, relativeOrigin),
      childMissing,
      [...path, childIndex]
    ));
  });
  return leaves;
}

function orientationIndex(missingCorner) {
  return missingCorner[0] + 2 * missingCorner[1] + 4 * missingCorner[2];
}

const chairOrientationKeys = [...new Set(
  CANONICAL_CHILDREN.map(([, missingCorner]) => orientationIndex(missingCorner))
)];
let selectedChairOrientation = null;

function updateChairColorButtons() {
  chairColorFilter.querySelectorAll("button").forEach((button) => {
    const key = Number(button.dataset.orientation);
    const active = key === selectedChairOrientation;
    button.setAttribute("aria-pressed", String(active));
    button.classList.toggle("is-muted", selectedChairOrientation !== null && !active);
  });
}

for (const key of chairOrientationKeys) {
  const button = document.createElement("button");
  const bits = [key & 1, (key >> 1) & 1, (key >> 2) & 1].join("");
  button.type = "button";
  button.dataset.orientation = String(key);
  button.style.setProperty("--swatch", `#${ORIENTATION_COLORS[key].toString(16).padStart(6, "0")}`);
  button.setAttribute("aria-label", `Highlight chairs missing corner ${bits}`);
  button.setAttribute("aria-pressed", "false");
  button.title = `Missing corner ${bits}`;
  button.addEventListener("click", () => {
    selectedChairOrientation = selectedChairOrientation === key ? null : key;
    updateChairColorButtons();
    refreshChairHighlight(currentVisual);
    if (transition) {
      refreshChairHighlight(transition.from);
      refreshChairHighlight(transition.to);
    }
  });
  chairColorFilter.appendChild(button);
}

function leafCells(leaf) {
  const cells = [];
  for (let x = 0; x < 2; x += 1) {
    for (let y = 0; y < 2; y += 1) {
      for (let z = 0; z < 2; z += 1) {
        if (x === leaf.missingCorner[0] && y === leaf.missingCorner[1] && z === leaf.missingCorner[2]) continue;
        cells.push([leaf.origin[0] + x, leaf.origin[1] + y, leaf.origin[2] + z]);
      }
    }
  }
  return cells;
}

function makeChairGeometry(leaf) {
  const cells = leafCells(leaf);
  const occupied = new Set(cells.map((cell) => cell.join(",")));
  const positions = [];
  for (const cell of cells) {
    const corners = CUBE_CORNERS.map(([x, y, z]) => [cell[0] + x, cell[1] + y, cell[2] + z]);
    CUBE_FACES.forEach((face, faceIndex) => {
      const neighbor = add(cell, FACE_NEIGHBORS[faceIndex]);
      if (occupied.has(neighbor.join(","))) return;
      for (const index of [face[0], face[1], face[2], face[0], face[2], face[3]]) {
        positions.push(...corners[index]);
      }
    });
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.computeVertexNormals();
  return geometry;
}

function makeParentOutline(size) {
  const half = size / 2;
  const surface = makeChairGeometry({ origin: [0, 0, 0], missingCorner: [1, 1, 1] });
  surface.scale(half, half, half);
  const geometry = new THREE.EdgesGeometry(surface, 1);
  surface.dispose();
  const material = new THREE.LineDashedMaterial({
    color: 0x1d6b62,
    transparent: true,
    opacity: 0.52,
    depthTest: false,
    dashSize: size * 0.018,
    gapSize: size * 0.012
  });
  const outline = new THREE.LineSegments(geometry, material);
  outline.computeLineDistances();
  outline.renderOrder = 3;
  return { outline, geometry, material };
}

function makeVisual(level) {
  const leaves = chairLeaves(level);
  const size = 2 ** (level + 1);
  const group = new THREE.Group();
  const materials = [];
  const geometries = [];
  const chairs = [];
  const orientationBuckets = new Map();
  const faceOpacity = Math.max(0.035, 0.2 / (2 ** level));
  const edgeOpacity = Math.max(0.11, 0.58 / (2 ** level));

  for (const leaf of leaves) {
    const orientation = orientationIndex(leaf.missingCorner);
    const geometry = makeChairGeometry(leaf);
    const edgeGeometry = new THREE.EdgesGeometry(geometry, 1);
    if (!orientationBuckets.has(orientation)) {
      orientationBuckets.set(orientation, { facePositions: [], edgePositions: [] });
    }
    const bucket = orientationBuckets.get(orientation);
    bucket.facePositions.push(...geometry.getAttribute("position").array);
    bucket.edgePositions.push(...edgeGeometry.getAttribute("position").array);
    geometry.dispose();
    edgeGeometry.dispose();
  }

  for (const [orientation, bucket] of orientationBuckets) {
    const color = new THREE.Color(ORIENTATION_COLORS[orientation]);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(bucket.facePositions, 3));
    geometry.computeVertexNormals();
    const faceMaterial = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: faceOpacity,
      depthWrite: false,
      depthTest: true,
      side: THREE.DoubleSide
    });
    faceMaterial.userData.baseOpacity = faceOpacity;
    const mesh = new THREE.Mesh(geometry, faceMaterial);
    mesh.renderOrder = 1;
    group.add(mesh);

    const edgeGeometry = new THREE.BufferGeometry();
    edgeGeometry.setAttribute("position", new THREE.Float32BufferAttribute(bucket.edgePositions, 3));
    const edgeMaterial = new THREE.LineBasicMaterial({
      color: color.clone().multiplyScalar(0.68),
      transparent: true,
      opacity: edgeOpacity,
      depthWrite: false,
      depthTest: true
    });
    edgeMaterial.userData.baseOpacity = edgeOpacity;
    const edges = new THREE.LineSegments(edgeGeometry, edgeMaterial);
    edges.renderOrder = 2;
    group.add(edges);
    geometries.push(geometry, edgeGeometry);
    materials.push(faceMaterial, edgeMaterial);
    chairs.push({ orientation, faceMaterial, edgeMaterial });
  }
  const parent = makeParentOutline(size);
  group.position.set(-size / 2, -size / 2, -size / 2);
  group.add(parent.outline);
  materials.push(parent.material);
  geometries.push(parent.geometry);

  return {
    group,
    level,
    leaves,
    chairs,
    materials,
    geometries
  };
}

const SOCKET_COLORS = [0xe25543, 0xf0a51f, 0x18a98b, 0x477dcc, 0x9a66c7, 0xd66f94];

function channelColor(channel) {
  let hash = 2166136261;
  for (let index = 0; index < channel.length; index += 1) {
    hash ^= channel.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return SOCKET_COLORS[Math.abs(hash) % SOCKET_COLORS.length];
}

function makeSearchVisual(state) {
  const group = new THREE.Group();
  const materials = [];
  const geometries = [];
  const chairs = [];
  const allCells = [];

  for (const placement of state.placements) {
    const variant = state.catalog.variants[placement.variantId];
    const leaf = { origin: placement.origin, missingCorner: variant.missingCorner };
    const orientation = orientationIndex(variant.missingCorner);
    const color = new THREE.Color(ORIENTATION_COLORS[orientation]);
    const geometry = makeChairGeometry(leaf);
    const faceMaterial = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.15,
      depthWrite: false,
      depthTest: true,
      side: THREE.DoubleSide
    });
    faceMaterial.userData.baseOpacity = 0.15;
    const mesh = new THREE.Mesh(geometry, faceMaterial);
    mesh.renderOrder = 1;
    group.add(mesh);

    const edgeGeometry = new THREE.EdgesGeometry(geometry, 1);
    const edgeMaterial = new THREE.LineBasicMaterial({
      color: color.clone().multiplyScalar(0.72),
      transparent: true,
      opacity: 0.62,
      depthWrite: false,
      depthTest: true
    });
    edgeMaterial.userData.baseOpacity = 0.62;
    const edges = new THREE.LineSegments(edgeGeometry, edgeMaterial);
    edges.renderOrder = 2;
    group.add(edges);
    materials.push(faceMaterial, edgeMaterial);
    geometries.push(geometry, edgeGeometry);
    chairs.push({ orientation, faceMaterial, edgeMaterial });
    variant.cells.forEach(cell => allCells.push(add(placement.origin, cell)));
  }

  const outward = new THREE.Vector3(0, 0, 1);
  for (const mark of exposedMarks(state)) {
    const direction = new THREE.Vector3(...mark.direction);
    const geometry = mark.polarity > 0
      ? new THREE.CircleGeometry(0.145, 16)
      : new THREE.RingGeometry(0.075, 0.155, 16);
    const material = new THREE.MeshBasicMaterial({
      color: channelColor(mark.channel),
      transparent: true,
      opacity: 0.9,
      depthWrite: false,
      depthTest: false,
      side: THREE.DoubleSide
    });
    material.userData.baseOpacity = 0.9;
    const socket = new THREE.Mesh(geometry, material);
    socket.position.set(
      mark.cell[0] + 0.5 + mark.direction[0] * 0.506,
      mark.cell[1] + 0.5 + mark.direction[1] * 0.506,
      mark.cell[2] + 0.5 + mark.direction[2] * 0.506
    );
    socket.quaternion.setFromUnitVectors(outward, direction);
    socket.renderOrder = 5;
    group.add(socket);
    geometries.push(geometry);
    materials.push(material);
  }

  const minima = [0, 1, 2].map(axis => Math.min(...allCells.map(cell => cell[axis])));
  const maxima = [0, 1, 2].map(axis => Math.max(...allCells.map(cell => cell[axis])) + 1);
  const center = minima.map((minimum, axis) => (minimum + maxima[axis]) / 2);
  const size = Math.max(...maxima.map((maximum, axis) => maximum - minima[axis]));
  group.position.set(-center[0], -center[1], -center[2]);

  return { group, level: 0, leaves: state.placements, chairs, materials, geometries, size };
}

function setVisualOpacity(visual, amount) {
  for (const material of visual.materials) {
    material.userData.transitionAmount = amount;
    material.opacity = (material.userData.baseOpacity ?? 0.52)
      * (material.userData.highlightFactor ?? 1)
      * amount;
  }
}

function refreshChairHighlight(visual) {
  if (!visual) return;
  for (const chair of visual.chairs) {
    const highlighted = selectedChairOrientation === null || chair.orientation === selectedChairOrientation;
    chair.faceMaterial.userData.highlightFactor = highlighted ? 1 : 0.08;
    chair.edgeMaterial.userData.highlightFactor = highlighted ? 1 : 0.12;
  }
  for (const material of visual.materials) {
    material.opacity = (material.userData.baseOpacity ?? 0.52)
      * (material.userData.highlightFactor ?? 1)
      * (material.userData.transitionAmount ?? 1);
  }
}

function disposeVisual(visual) {
  root.remove(visual.group);
  visual.geometries.forEach((geometry) => geometry.dispose());
  visual.materials.forEach((material) => material.dispose());
}

function updateReadout() {
  if (mode === "search") {
    generationLabel.textContent = "placed";
    generationValue.textContent = String(growthState.placements.length);
    tileLabel.textContent = "catalogue";
    tileValue.textContent = String(growthState.catalog.variants.length);
    frontierValue.textContent = String(exposedMarks(growthState).length);
    backtrackValue.textContent = String(growthState.solverBacktracks);
  } else {
    generationLabel.textContent = "inflations";
    generationValue.textContent = String(generation);
    tileLabel.textContent = "chairs";
    tileValue.textContent = (8 ** generation).toLocaleString();
  }
}

function updateActionButtons() {
  const busy = Boolean(transition);
  if (mode === "search") {
    const complete = growthState.placements.length >= growthState.catalog.targetCount;
    backButton.disabled = busy || growthState.placements.length === 1;
    inflateButton.disabled = busy || complete;
    inflateButton.querySelector("span").textContent = complete ? "Patch complete" : "Place next chair";
    backButton.querySelector("span").textContent = "Remove last";
    runButton.disabled = complete && !autoRun;
    runButton.querySelector("span").textContent = autoRun ? "Pause" : "Run";
    runButton.querySelector("b").textContent = autoRun ? "Ⅱ" : "▶";
  } else {
    backButton.disabled = busy || generation === 0;
    inflateButton.disabled = busy || generation === MAX_GENERATION;
    inflateButton.querySelector("span").textContent = generation === MAX_GENERATION
      ? "Maximum inflation reached"
      : "Apply one more inflation";
    backButton.querySelector("span").textContent = "Go back";
  }
}

let generation = 0;
let mode = "search";
let growthState = createGrowthState(2);
let autoRun = false;
let currentVisual = makeSearchVisual(growthState);
root.add(currentVisual.group);
let transition = null;
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
sceneShell.classList.add("is-search");

function updateModePanel() {
  const searching = mode === "search";
  sceneShell.classList.toggle("is-search", searching);
  if (searching) {
    panelKicker.textContent = "GCTS marking";
    hierarchyTitle.textContent = "depth 2";
    panelCount.textContent = String(growthState.catalog.variants.length);
    panelCountLabel.textContent = "tile states";
    scaleLeft.textContent = "seed";
    scaleRight.textContent = "matched frontier";
    panelDescription.textContent = "The search aligns complementary face sockets, checks every new contact, and rejects overlaps. No enclosing superchair is given to it.";
    sceneInstruction.textContent = "Drag to orbit · colored tabs are exposed local sockets";
    hierarchyPlot.setAttribute("aria-label", "Live diagram of exposed local matching sockets in the chair search");
  } else {
    panelKicker.textContent = "inflation rule";
    hierarchyTitle.textContent = "× 2";
    panelCount.textContent = "8";
    panelCountLabel.textContent = "children";
    scaleLeft.textContent = "parent";
    scaleRight.textContent = "child addresses";
    panelDescription.textContent = "Choose one of the seven colors to highlight every chair with that missing-corner orientation. The central child prevents the rule from being merely seven octants.";
    sceneInstruction.textContent = "Drag to orbit · scroll through transparent walls";
    hierarchyPlot.setAttribute("aria-label", "Axonometric diagram of the eight child chairs and their missing-corner orientations");
  }
  updateReadout();
  updateActionButtons();
  drawHierarchyPlot();
}

function cameraDestinationForSize(size) {
  const offset = camera.position.clone().sub(controls.target).normalize();
  return controls.target.clone().add(offset.multiplyScalar(8 + size * 2.05));
}

function swapVisual(nextVisual, duration, cameraDestination) {
  setVisualOpacity(nextVisual, 0);
  root.add(nextVisual.group);
  if (prefersReducedMotion) {
    disposeVisual(currentVisual);
    currentVisual = nextVisual;
    setVisualOpacity(nextVisual, 1);
    camera.position.copy(cameraDestination);
    updateActionButtons();
    if (autoRun) window.setTimeout(runNextSearchStep, 60);
    return;
  }
  transition = {
    from: currentVisual,
    to: nextVisual,
    start: performance.now(),
    duration,
    cameraStart: camera.position.clone(),
    cameraDestination
  };
  updateActionButtons();
}

function showGeneration(targetGeneration) {
  if (transition || targetGeneration < 0 || targetGeneration > MAX_GENERATION || targetGeneration === generation) return;
  const direction = targetGeneration > generation ? 1 : -1;
  const nextVisual = makeVisual(targetGeneration);
  refreshChairHighlight(nextVisual);
  generation = targetGeneration;
  updateReadout();

  const cameraOffset = camera.position.clone().sub(controls.target);
  const cameraDestination = controls.target.clone().add(cameraOffset.multiplyScalar(direction > 0 ? 2 : 0.5));
  swapVisual(nextVisual, 720, cameraDestination);
}

function showGrowthStep(direction) {
  if (transition || mode !== "search") return;
  const nextState = direction > 0 ? growOne(growthState) : shrinkOne(growthState);
  if (nextState.placements.length === growthState.placements.length) return;
  growthState = nextState;
  const nextVisual = makeSearchVisual(growthState);
  updateReadout();
  drawHierarchyPlot();
  swapVisual(nextVisual, autoRun ? 190 : 420, cameraDestinationForSize(nextVisual.size));
}

function runNextSearchStep() {
  if (!autoRun || transition || mode !== "search") return;
  if (growthState.placements.length >= growthState.catalog.targetCount) {
    autoRun = false;
    updateActionButtons();
    return;
  }
  showGrowthStep(1);
}

inflateButton.addEventListener("click", () => {
  if (mode === "search") showGrowthStep(1);
  else showGeneration(generation + 1);
});
backButton.addEventListener("click", () => {
  autoRun = false;
  if (mode === "search") showGrowthStep(-1);
  else showGeneration(generation - 1);
});
runButton.addEventListener("click", () => {
  autoRun = !autoRun;
  updateActionButtons();
  if (autoRun) runNextSearchStep();
});
chairModeSelect.addEventListener("change", () => {
  autoRun = false;
  mode = chairModeSelect.value;
  disposeVisual(currentVisual);
  currentVisual = mode === "search" ? makeSearchVisual(growthState) : makeVisual(generation);
  root.add(currentVisual.group);
  camera.position.copy(cameraDestinationForSize(mode === "search" ? currentVisual.size : 2 ** (generation + 1)));
  updateModePanel();
});

function drawHierarchyPlot() {
  const rect = hierarchyPlot.getBoundingClientRect();
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(1, Math.round(rect.width * ratio));
  const height = Math.max(1, Math.round(rect.height * ratio));
  if (hierarchyPlot.width !== width || hierarchyPlot.height !== height) {
    hierarchyPlot.width = width;
    hierarchyPlot.height = height;
  }
  const context = hierarchyPlot.getContext("2d");
  context.clearRect(0, 0, width, height);
  context.save();
  context.scale(ratio, ratio);
  const cssWidth = width / ratio;
  const cssHeight = height / ratio;
  if (mode === "search") {
    const marks = exposedMarks(growthState);
    const centerX = cssWidth / 2;
    const centerY = cssHeight / 2;
    const radius = Math.min(cssWidth, cssHeight) * 0.34;
    context.strokeStyle = "rgba(23, 32, 30, .22)";
    context.lineWidth = 1;
    context.beginPath();
    context.arc(centerX, centerY, radius, 0, Math.PI * 2);
    context.stroke();

    context.fillStyle = "rgba(29, 107, 98, .13)";
    context.strokeStyle = "rgba(29, 107, 98, .72)";
    context.beginPath();
    context.moveTo(centerX - radius * 0.33, centerY - radius * 0.33);
    context.lineTo(centerX + radius * 0.33, centerY - radius * 0.33);
    context.lineTo(centerX + radius * 0.33, centerY + radius * 0.05);
    context.lineTo(centerX + radius * 0.04, centerY + radius * 0.05);
    context.lineTo(centerX + radius * 0.04, centerY + radius * 0.34);
    context.lineTo(centerX - radius * 0.33, centerY + radius * 0.34);
    context.closePath();
    context.fill();
    context.stroke();

    const sampleCount = Math.min(28, marks.length);
    for (let index = 0; index < sampleCount; index += 1) {
      const mark = marks[Math.floor(index * marks.length / sampleCount)];
      const angle = (index / sampleCount) * Math.PI * 2 - Math.PI / 2;
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius;
      context.strokeStyle = "rgba(23, 32, 30, .12)";
      context.beginPath();
      context.moveTo(centerX + Math.cos(angle) * radius * 0.48, centerY + Math.sin(angle) * radius * 0.48);
      context.lineTo(x, y);
      context.stroke();
      context.beginPath();
      context.arc(x, y, mark.polarity > 0 ? 4.5 : 5.5, 0, Math.PI * 2);
      const color = new THREE.Color(channelColor(mark.channel));
      context.fillStyle = `rgb(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)})`;
      if (mark.polarity > 0) context.fill();
      else {
        context.lineWidth = 2;
        context.strokeStyle = context.fillStyle;
        context.stroke();
        context.lineWidth = 1;
      }
    }
    context.fillStyle = "#17201e";
    context.font = `400 ${Math.max(16, cssWidth * 0.12)}px Georgia, serif`;
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(String(growthState.placements.length), centerX, centerY + radius * 0.75);
    context.restore();
    return;
  }
  const project = ([x, y, z]) => [
    cssWidth * 0.5 + (x - y) * cssWidth * 0.105,
    cssHeight * 0.61 + (x + y) * cssHeight * 0.052 - z * cssHeight * 0.105
  ];

  context.strokeStyle = "rgba(23, 32, 30, .2)";
  context.lineWidth = 1;
  const outline = [[0, 0, 0], [4, 0, 0], [4, 4, 0], [0, 4, 0], [0, 0, 0], [0, 0, 4], [4, 0, 4]];
  context.beginPath();
  outline.forEach((point, index) => {
    const [x, y] = project(point);
    if (index === 0) context.moveTo(x, y); else context.lineTo(x, y);
  });
  context.stroke();

  CANONICAL_CHILDREN
    .map(([origin, missing], index) => ({ origin, missing, index }))
    .sort((a, b) => (a.origin[0] + a.origin[1] + a.origin[2]) - (b.origin[0] + b.origin[1] + b.origin[2]))
    .forEach(({ origin, missing, index }) => {
      const center = [origin[0] + 1, origin[1] + 1, origin[2] + 1];
      const [x, y] = project(center);
      const radius = Math.max(8, cssWidth * 0.055);
      context.beginPath();
      context.arc(x, y, radius, 0, Math.PI * 2);
      const color = new THREE.Color(ORIENTATION_COLORS[orientationIndex(missing)]);
      context.fillStyle = `rgba(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)}, .72)`;
      context.fill();
      context.strokeStyle = "rgba(23, 32, 30, .55)";
      context.stroke();
      context.fillStyle = "#17201e";
      context.font = `700 ${Math.max(8, cssWidth * 0.042)}px ui-sans-serif, system-ui, sans-serif`;
      context.textAlign = "center";
      context.textBaseline = "middle";
      context.fillText(String(index + 1), x, y + 0.5);
    });
  context.restore();
}

function resize() {
  const width = Math.max(1, viewport.clientWidth);
  const height = Math.max(1, viewport.clientHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

new ResizeObserver(resize).observe(viewport);
new ResizeObserver(drawHierarchyPlot).observe(hierarchyPlot);
resize();
drawHierarchyPlot();
updateModePanel();

function animate(time) {
  controls.update();
  if (transition) {
    const raw = Math.min(1, (time - transition.start) / transition.duration);
    const eased = raw * raw * (3 - 2 * raw);
    setVisualOpacity(transition.from, 1 - eased);
    setVisualOpacity(transition.to, eased);
    camera.position.lerpVectors(transition.cameraStart, transition.cameraDestination, eased);
    if (raw >= 1) {
      disposeVisual(transition.from);
      currentVisual = transition.to;
      transition = null;
      updateActionButtons();
      if (autoRun) window.setTimeout(runNextSearchStep, 70);
    }
  }
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

requestAnimationFrame(animate);
