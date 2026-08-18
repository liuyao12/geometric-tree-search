import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const viewport = document.getElementById("viewport");
const inflateButton = document.getElementById("inflate-button");
const backButton = document.getElementById("back-button");
const generationValue = document.getElementById("generation-value");
const tileValue = document.getElementById("tile-value");
const volumeValue = document.getElementById("volume-value");
const hierarchyPlot = document.getElementById("hierarchy-plot");
const tileSelect = document.getElementById("tile-select");

tileSelect.addEventListener("change", () => {
  window.location.href = tileSelect.value;
});

const MAX_GENERATION = 2;
const CANONICAL_CHILDREN = [
  [[0, 0, 0], [1, 1, 1]],
  [[0, 0, 2], [1, 1, 0]],
  [[0, 2, 0], [1, 0, 1]],
  [[0, 2, 2], [1, 0, 0]],
  [[1, 1, 1], [1, 1, 1]],
  [[2, 0, 0], [0, 1, 1]],
  [[2, 0, 2], [0, 1, 0]],
  [[2, 2, 0], [0, 0, 1]]
];
const ORIENTATION_COLORS = [
  0x4776a8, 0x7a68a6, 0x3d8e84, 0x5aa36f,
  0xd66f57, 0xca6f94, 0xdfb65b, 0xb9944e
];
const CUBE_FACES = [
  [0, 2, 3, 1], [4, 5, 7, 6],
  [0, 1, 5, 4], [2, 6, 7, 3],
  [0, 4, 6, 2], [1, 3, 7, 5]
];
const FACE_NEIGHBORS = [
  [0, 0, -1], [0, 0, 1],
  [0, -1, 0], [0, 1, 0],
  [-1, 0, 0], [1, 0, 0]
];
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
  const faceOpacity = Math.max(0.035, 0.2 / (2 ** level));
  const edgeOpacity = Math.max(0.11, 0.58 / (2 ** level));
  for (const leaf of leaves) {
    const color = new THREE.Color(ORIENTATION_COLORS[orientationIndex(leaf.missingCorner)]);
    const geometry = makeChairGeometry(leaf);
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

    const edgeGeometry = new THREE.EdgesGeometry(geometry, 1);
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
    materials,
    geometries
  };
}

function setVisualOpacity(visual, amount) {
  for (const material of visual.materials) {
    material.opacity = (material.userData.baseOpacity ?? 0.52) * amount;
  }
}

function disposeVisual(visual) {
  root.remove(visual.group);
  visual.geometries.forEach((geometry) => geometry.dispose());
  visual.materials.forEach((material) => material.dispose());
}

function updateReadout() {
  const chairs = 8 ** generation;
  generationValue.textContent = String(generation);
  tileValue.textContent = chairs.toLocaleString();
  volumeValue.textContent = (chairs * 7).toLocaleString();
}

function updateActionButtons() {
  const busy = Boolean(transition);
  backButton.disabled = busy || generation === 0;
  inflateButton.disabled = busy || generation === MAX_GENERATION;
  inflateButton.querySelector("span").textContent = generation === MAX_GENERATION
    ? "Maximum inflation reached"
    : "Apply one more inflation";
}

let generation = 0;
let currentVisual = makeVisual(generation);
root.add(currentVisual.group);
let transition = null;
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function showGeneration(targetGeneration) {
  if (transition || targetGeneration < 0 || targetGeneration > MAX_GENERATION || targetGeneration === generation) return;
  const direction = targetGeneration > generation ? 1 : -1;
  const nextVisual = makeVisual(targetGeneration);
  setVisualOpacity(nextVisual, 0);
  root.add(nextVisual.group);
  generation = targetGeneration;
  updateReadout();

  const cameraOffset = camera.position.clone().sub(controls.target);
  const cameraDestination = controls.target.clone().add(cameraOffset.multiplyScalar(direction > 0 ? 2 : 0.5));
  if (prefersReducedMotion) {
    disposeVisual(currentVisual);
    currentVisual = nextVisual;
    setVisualOpacity(nextVisual, 1);
    camera.position.copy(cameraDestination);
    updateActionButtons();
    return;
  }

  transition = {
    from: currentVisual,
    to: nextVisual,
    start: performance.now(),
    duration: 720,
    cameraStart: camera.position.clone(),
    cameraDestination
  };
  updateActionButtons();
}

inflateButton.addEventListener("click", () => showGeneration(generation + 1));
backButton.addEventListener("click", () => showGeneration(generation - 1));

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
updateReadout();
updateActionButtons();

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
    }
  }
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

requestAnimationFrame(animate);
