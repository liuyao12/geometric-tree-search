import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  CANONICAL_CHILDREN,
  FACE_DIRECTIONS,
  createGrowthState,
  exposedMarks,
  growOne,
  shrinkOne
} from "./chair-gcts.js?v=20260923-chair44";
import { VARIANTS, ROTATIONS, IDENTITY, COLORS, worldMarks, chairLeaves, childSupertile, parentContainingChild } from "./chair44.js?v=20260923-chair44";

import { DIRECTION_NODES, DIRECTION_EDGES, directionKey } from "./orientation-graph.js?v=20260923-eight-directions";

const viewport = document.getElementById("viewport");
const sceneShell = document.querySelector(".scene-shell");
const inflateButton = document.getElementById("inflate-button");
const applyOneButton = document.getElementById("apply-one-button");
const searchStatus = document.getElementById("search-status");
const backButton = document.getElementById("back-button");
const runButton = document.getElementById("run-button");
const generationValue = document.getElementById("generation-value");
const tileValue = document.getElementById("tile-value");
const generationLabel = document.getElementById("generation-label");
const tileLabel = document.getElementById("tile-label");
const hierarchyPlot = document.getElementById("hierarchy-plot");
const orientationPlot = document.getElementById("orientation-plot");
const orientationPanel = document.querySelector(".orientation-panel");
const orientationMatrix = document.getElementById("orientation-matrix");
const matrixValues = document.getElementById("matrix-values");
const chairColorFilter = document.getElementById("chair-color-filter");
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

const MAX_GENERATION = 4;
const RETAINED_CHILD_INDICES = [0, 1, 2, 3, 5, 6, 7];
const CORNER_COLORS = [
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

const orientationScene = new THREE.Scene();
const orientationCamera = new THREE.PerspectiveCamera(34, 1, 0.1, 20);
orientationCamera.up.set(0, 0, 1);
orientationCamera.position.set(2.25, 1.65, 2.15);
const orientationRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
orientationRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
orientationRenderer.setClearColor(0x000000, 0);
orientationRenderer.outputColorSpace = THREE.SRGBColorSpace;
orientationPlot.appendChild(orientationRenderer.domElement);

const orientationControls = new OrbitControls(orientationCamera, orientationRenderer.domElement);
orientationControls.enableDamping = true;
orientationControls.dampingFactor = 0.065;
orientationControls.enablePan = false;
orientationControls.minDistance = 2.2;
orientationControls.maxDistance = 5;

function makeOrientationCircle() {
  const points = Array.from({ length: 128 }, (_, index) => {
    const angle = (index / 128) * Math.PI * 2;
    return new THREE.Vector3(Math.cos(angle), Math.sin(angle), 0);
  });
  const circle = new THREE.LineLoop(
    new THREE.BufferGeometry().setFromPoints(points),
    new THREE.LineBasicMaterial({
      color: 0x17201e,
      transparent: true,
      opacity: 0.52,
      depthWrite: false,
      depthTest: false
    })
  );
  circle.renderOrder = 3;
  orientationScene.add(circle);
  return circle;
}

const orientationBoundary = makeOrientationCircle();
const orientationBoundaryView = new THREE.Vector3();

function updateOrientationBoundary() {
  orientationBoundaryView.copy(orientationCamera.position).sub(orientationControls.target);
  const cameraDistance = orientationBoundaryView.length();
  const planeOffset = 1 / cameraDistance;
  orientationBoundary.position.copy(orientationControls.target).addScaledVector(
    orientationBoundaryView,
    1 / (cameraDistance * cameraDistance)
  );
  orientationBoundary.quaternion.copy(orientationCamera.quaternion);
  orientationBoundary.scale.setScalar(Math.sqrt(1 - planeOffset * planeOffset));
}

const CHAIR_ROTATIONS = new Map();
for (const [id, rows] of ROTATIONS.entries()) {
  const key = directionKey(VARIANTS[id].missingCorner);
  const matrix = new THREE.Matrix4().set(...rows[0], 0, ...rows[1], 0, ...rows[2], 0, 0, 0, 0, 1);
  const quaternion = new THREE.Quaternion().setFromRotationMatrix(matrix).normalize();
  const angle = 2 * Math.acos(Math.min(1, Math.abs(quaternion.w)));
  if (!CHAIR_ROTATIONS.has(key) || angle < CHAIR_ROTATIONS.get(key).angle) {
    CHAIR_ROTATIONS.set(key, { rows, angle });
  }
}

function directionBallPoint(key) {
  return new THREE.Vector3(...DIRECTION_NODES[key].vector).normalize().multiplyScalar(0.86);
}

const directionEdges = new THREE.LineSegments(
  new THREE.BufferGeometry().setFromPoints(DIRECTION_EDGES.flatMap(pair => pair.map(directionBallPoint))),
  new THREE.LineBasicMaterial({ color: 0x54756d, transparent: true, opacity: 0.45, depthWrite: false })
);
directionEdges.renderOrder = 1;
orientationScene.add(directionEdges);

const orientationPointGeometry = new THREE.BufferGeometry();
const orientationPointMaterial = new THREE.ShaderMaterial({
  transparent: true,
  depthWrite: false,
  depthTest: true,
  uniforms: { pixelRatio: { value: Math.min(window.devicePixelRatio, 2) } },
  vertexShader: `
    attribute vec3 color;
    attribute float pointSize;
    varying vec3 pointColor;
    uniform float pixelRatio;
    void main() {
      pointColor = color;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      gl_PointSize = pointSize * pixelRatio;
    }
  `,
  fragmentShader: `
    varying vec3 pointColor;
    void main() {
      vec2 centered = gl_PointCoord - vec2(0.5);
      if (dot(centered, centered) > 0.25) discard;
      gl_FragColor = vec4(pointColor, 1.0);
    }
  `
});
const orientationPoints = new THREE.Points(orientationPointGeometry, orientationPointMaterial);
orientationPoints.renderOrder = 3;
orientationScene.add(orientationPoints);

const orientationSelectionMarker = new THREE.Points(
  new THREE.BufferGeometry().setFromPoints([new THREE.Vector3()]),
  new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    depthTest: false,
    uniforms: {
      pixelRatio: { value: Math.min(window.devicePixelRatio, 2) },
      dotSize: { value: 18 },
      haloSize: { value: 26 }
    },
    vertexShader: `
      uniform float pixelRatio;
      uniform float haloSize;
      void main() {
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = haloSize * pixelRatio;
      }
    `,
    fragmentShader: `
      uniform float dotSize;
      uniform float haloSize;
      void main() {
        float radius = length(gl_PointCoord - vec2(0.5));
        float innerRadius = dotSize / (2.0 * haloSize);
        float feather = 1.25 / haloSize;
        float outer = 1.0 - smoothstep(0.5 - feather, 0.5, radius);
        float inner = smoothstep(innerRadius, innerRadius + feather, radius);
        float alpha = outer * inner * 0.82;
        if (alpha < 0.01) discard;
        gl_FragColor = vec4(0.09, 0.125, 0.118, alpha);
      }
    `
  })
);
orientationSelectionMarker.visible = false;
orientationSelectionMarker.renderOrder = 4;
orientationScene.add(orientationSelectionMarker);
let orientationPointKeys = [];
const orientationPointSizes = new Map();

function orientationCounts(leaves) {
  const counts = new Map();
  for (const leaf of leaves) {
    const key = directionKey(leaf.missingCorner ?? VARIANTS[leaf.variantId].missingCorner);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return counts;
}

function updateSelectedOrientation(key) {
  if (
    mode === "inflation"
    && selectedChairOrientation !== key
    && !orientationPointSizes.has(key)
  ) return;
  selectedChairOrientation = selectedChairOrientation === key ? null : key;
  updateChairColorButtons();
  refreshChairHighlight(currentVisual);
  if (transition) {
    refreshChairHighlight(transition.from);
    refreshChairHighlight(transition.to);
  }
  const rotation = selectedChairOrientation === null ? null : CHAIR_ROTATIONS.get(selectedChairOrientation);
  orientationSelectionMarker.visible = Boolean(rotation);
  orientationMatrix.hidden = !rotation;
  orientationPanel.classList.toggle("has-selection", Boolean(rotation));
  if (rotation) {
    const dotSize = orientationPointSizes.get(selectedChairOrientation) ?? 18;
    orientationSelectionMarker.material.uniforms.dotSize.value = dotSize;
    orientationSelectionMarker.material.uniforms.haloSize.value = dotSize + 8;
    orientationSelectionMarker.geometry.setFromPoints([directionBallPoint(selectedChairOrientation)]);
    matrixValues.textContent = '\\(\\begin{pmatrix}' + rotation.rows.map(row => row.join('&')).join('\\\\') + '\\end{pmatrix}\\)';
    window.MathJax?.typesetPromise?.([matrixValues]);
  }
}

function updateOrientationBall() {
  if (!currentInflationState) return;
  const counts = orientationCounts(mode === "search" ? growthState.placements : currentInflationState.leaves);
  const largest = Math.max(...counts.values());
  orientationPointKeys = DIRECTION_NODES.map(node => node.id);
  const positions = [];
  const colors = [];
  const sizes = [];
  orientationPointSizes.clear();
  for (const key of orientationPointKeys) {
    const point = directionBallPoint(key);
    positions.push(point.x, point.y, point.z);
    const color = new THREE.Color(CORNER_COLORS[key]);
    if (!counts.has(key)) color.lerp(new THREE.Color(0xedf1ef), 0.78);
    colors.push(color.r, color.g, color.b);
    const pointSize = counts.has(key) ? 8 + 10 * Math.sqrt(counts.get(key) / largest) : 7;
    sizes.push(pointSize);
    orientationPointSizes.set(key, pointSize);
  }
  orientationPointGeometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  orientationPointGeometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  orientationPointGeometry.setAttribute("pointSize", new THREE.Float32BufferAttribute(sizes, 1));
  orientationPointGeometry.computeBoundingSphere();
  chairColorFilter.querySelectorAll("button").forEach((button) => {
    button.classList.toggle("is-absent", !counts.has(Number(button.dataset.orientation)));
  });
  panelCount.textContent = String(counts.size);
  if (selectedChairOrientation !== null) {
    const dotSize = orientationPointSizes.get(selectedChairOrientation) ?? 18;
    orientationSelectionMarker.material.uniforms.dotSize.value = dotSize;
    orientationSelectionMarker.material.uniforms.haloSize.value = dotSize + 8;
  }
}

const orientationRaycaster = new THREE.Raycaster();
orientationRaycaster.params.Points.threshold = 0.12;
const orientationPointer = new THREE.Vector2();

orientationPlot.addEventListener("click", (event) => {
  const rect = orientationPlot.getBoundingClientRect();
  orientationPointer.set(
    ((event.clientX - rect.left) / rect.width) * 2 - 1,
    -((event.clientY - rect.top) / rect.height) * 2 + 1
  );
  orientationRaycaster.setFromCamera(orientationPointer, orientationCamera);
  const hit = orientationRaycaster.intersectObject(orientationPoints, false)[0];
  if (hit) updateSelectedOrientation(orientationPointKeys[hit.index]);
});

orientationPlot.addEventListener("keydown", (event) => {
  if (!["ArrowLeft", "ArrowRight", "Escape"].includes(event.key)) return;
  event.preventDefault();
  if (event.key === "Escape") {
    if (selectedChairOrientation !== null) updateSelectedOrientation(selectedChairOrientation);
    return;
  }
  const currentIndex = orientationPointKeys.indexOf(selectedChairOrientation);
  const direction = event.key === "ArrowRight" ? 1 : -1;
  const nextIndex = currentIndex < 0
    ? (direction > 0 ? 0 : orientationPointKeys.length - 1)
    : (currentIndex + direction + orientationPointKeys.length) % orientationPointKeys.length;
  if (selectedChairOrientation !== null) updateSelectedOrientation(selectedChairOrientation);
  updateSelectedOrientation(orientationPointKeys[nextIndex]);
});

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

function randomRetainedChildIndex() {
  return RETAINED_CHILD_INDICES[
    Math.floor(Math.random() * RETAINED_CHILD_INDICES.length)
  ];
}

function initialInflationState() {
  return {
    generation: 0,
    rotation: IDENTITY,
    origin: [0, 0, 0],
    missingCorner: [1, 1, 1],
    size: 2,
    leaves: chairLeaves(0),
    retainedChildIndex: null
  };
}

function expandInflationState(current, retainedChildIndex) {
  const parent = parentContainingChild(current, retainedChildIndex);
  const leaves = [];
  for (let childIndex = 0; childIndex < CANONICAL_CHILDREN.length; childIndex += 1) {
    if (childIndex === retainedChildIndex) {
      leaves.push(...current.leaves.map((leaf) => ({ ...leaf, path: [...leaf.path, childIndex] })));
      continue;
    }
    const child = childSupertile(parent, childIndex);
    leaves.push(...chairLeaves(
      current.generation,
      child.origin,
      child.rotation,
      [childIndex]
    ));
  }
  return {
    ...parent,
    generation: current.generation + 1,
    leaves,
    retainedChildIndex
  };
}

function orientationIndex(missingCorner) {
  return missingCorner[0] + 2 * missingCorner[1] + 4 * missingCorner[2];
}

const chairOrientationKeys = DIRECTION_NODES.map(node => node.id);
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
  const bits = DIRECTION_NODES[key].corner.join("");
  button.type = "button";
  button.dataset.orientation = String(key);
  button.style.setProperty("--swatch", `#${CORNER_COLORS[key].toString(16).padStart(6, "0")}`);
  button.setAttribute("aria-label", `Highlight missing-corner direction ${bits}`);
  button.setAttribute("aria-pressed", "false");
  button.title = `Corner ${bits} · three marked rotations`;
  button.addEventListener("click", () => {
    updateSelectedOrientation(key);
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

function makeParentOutline(size, missingCorner, origin) {
  const half = size / 2;
  const surface = makeChairGeometry({ origin: [0, 0, 0], missingCorner });
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
  outline.position.set(...origin);
  outline.computeLineDistances();
  outline.renderOrder = 3;
  return { outline, geometry, material };
}

function makeVisual(state) {
  const { leaves, size } = state;
  const level = state.generation;
  const group = new THREE.Group();
  const materials = [];
  const geometries = [];
  const chairs = [];
  const orientationBuckets = new Map();
  const faceOpacity = 0.18;
  const edgeOpacity = 0.48;

  for (const leaf of leaves) {
    const orientation = directionKey(leaf.missingCorner);
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
    const color = new THREE.Color(0xf0f1e9);
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
      color: 0x394845,
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
  addArrowVisual(group, leaves.flatMap(worldMarks), materials, geometries);
  const parent = makeParentOutline(size, state.missingCorner, state.origin);
  // Keep the original chair fixed in world space; new copies grow around it.
  group.position.set(-1, -1, -1);
  group.add(parent.outline);
  materials.push(parent.material);
  geometries.push(parent.geometry);

  return {
    group,
    level,
    state,
    size,
    leaves,
    chairs,
    materials,
    geometries
  };
}

function channelColor(color) { return COLORS[color]; }

function addArrowVisual(group, marks, materials, geometries) {
  const buckets = new Map(Object.keys(COLORS).map(color => [color, []]));
  const triangles = [
    [[-.065,-.36],[.065,-.36],[.065,.12]],
    [[-.065,-.36],[.065,.12],[-.065,.12]],
    [[-.17,.10],[.17,.10],[0,.42]]
  ];
  for (const mark of marks) {
    const normal = new THREE.Vector3(...mark.direction);
    const forward = new THREE.Vector3(...mark.arrow).normalize();
    const side = forward.clone().cross(normal);
    const center = new THREE.Vector3(...mark.cell).addScalar(.5).addScaledVector(normal,.509);
    for (const triangle of triangles) for (const [x,y] of triangle) {
      const p = center.clone().addScaledVector(side,x).addScaledVector(forward,y);
      buckets.get(mark.color).push(p.x,p.y,p.z);
    }
  }
  const arrows = new THREE.Group();
  arrows.name = 'chair44-arrows';
  arrows.visible = document.getElementById('show-markings').checked;
  for (const [color,positions] of buckets) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions,3));
    const material = new THREE.MeshBasicMaterial({color:COLORS[color],side:THREE.FrontSide,transparent:true,opacity:1,depthWrite:false});
    material.userData.baseOpacity = 1;
    const mesh = new THREE.Mesh(geometry,material); mesh.renderOrder = 4;
    // Rear arrows remain visible through the body, with lower contrast so
    // front and back markings can still be distinguished while orbiting.
    const backMaterial = material.clone();
    backMaterial.side = THREE.BackSide;
    backMaterial.opacity = 0.42;
    backMaterial.userData.baseOpacity = 0.42;
    const backMesh = new THREE.Mesh(geometry, backMaterial);
    backMesh.renderOrder = 3;
    arrows.add(backMesh, mesh);
    materials.push(backMaterial, material);
    geometries.push(geometry);
  }
  group.add(arrows);
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
    const orientation = directionKey(variant.missingCorner);
    const color = new THREE.Color(0xf0f1e9);
    const geometry = makeChairGeometry(leaf);
    const faceMaterial = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.18,
      depthWrite: false,
      depthTest: true,
      side: THREE.DoubleSide
    });
    faceMaterial.userData.baseOpacity = 0.18;
    const mesh = new THREE.Mesh(geometry, faceMaterial);
    mesh.renderOrder = 1;
    group.add(mesh);

    const edgeGeometry = new THREE.EdgesGeometry(geometry, 1);
    const edgeMaterial = new THREE.LineBasicMaterial({
      color: 0x394845,
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

  addArrowVisual(group, state.placements.flatMap(worldMarks), materials, geometries);

  const minima = [0, 1, 2].map(axis => Math.min(...allCells.map(cell => cell[axis])));
  const maxima = [0, 1, 2].map(axis => Math.max(...allCells.map(cell => cell[axis])) + 1);
  const size = Math.max(...maxima.map((maximum, axis) => maximum - minima[axis]));
  // Use the same fixed seed frame as inflation, never the patch centroid.
  group.position.set(-1, -1, -1);

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
    tileLabel.textContent = "prototile";
    tileValue.textContent = "1";
    frontierValue.textContent = String(exposedMarks(growthState).length);
    backtrackValue.textContent = String(growthState.solverBacktracks);
    searchStatus.textContent = growthState.status === 'consistent finite patch'
      ? 'Finite patch verified. Apply one to continue.'
      : growthState.status === 'exhausted' ? 'Local search exhausted.'
      : growthState.status.includes('budget') ? 'Backtracking; apply one to continue.'
      : `${growthState.forcedPlacements} forced · ${growthState.branchDecisions} choices`;
  } else {
    generationLabel.textContent = "inflations";
    generationValue.textContent = String(generation);
    tileLabel.textContent = "chairs";
    tileValue.textContent = currentInflationState.leaves.length.toLocaleString();
  }
}

function updateActionButtons() {
  const busy = Boolean(transition);
  chairModeSelect.disabled = busy;
  inflateButton.disabled = busy || generation === MAX_GENERATION;
  applyOneButton.disabled = busy || (growthState.complete && growthState.status !== 'consistent finite patch');
  backButton.disabled = busy || (mode === 'search' ? growthState.history.length === 0 : generation === 0);
  backButton.querySelector('span').textContent = 'Undo';
  runButton.disabled = !autoRun && (busy || growthState.complete);
  runButton.querySelector('span').textContent = autoRun ? 'Pause' : 'Run';
  runButton.querySelector('b').textContent = autoRun ? 'Ⅱ' : '▶';
}

const inflationStates = [initialInflationState()];
let generation = 0;
let currentInflationState = inflationStates[generation];
let mode = "inflation";
let growthState = createGrowthState(2);
let autoRun = false;
let runTimer = null;
let currentVisual = makeVisual(currentInflationState);
root.add(currentVisual.group);
camera.position.copy(cameraDestinationForVisual(currentVisual));
let transition = null;
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
viewport.dataset.retainedChildren = "";
viewport.dataset.tile = "Chair44";
viewport.dataset.markings = "24";

function updateModePanel() {
  const searching = mode === "search";
  sceneShell.classList.toggle("is-search", searching);
  orientationPlot.hidden = false;
  hierarchyPlot.hidden = true;
  orientationMatrix.hidden = selectedChairOrientation === null;
  if (searching) {
    panelKicker.textContent = "corner-direction graph";
    hierarchyTitle.textContent = "Rotations";
    panelCount.textContent = String(orientationCounts(growthState.placements).size);
    panelCountLabel.textContent = "of 8 present";
    scaleLeft.textContent = "8 directions";
    scaleRight.textContent = "quarter turns";
    panelDescription.textContent = "Eight missing-corner directions, connected by quarter turns. Each node groups three marked rotations. Dot size shows tile count; pale nodes are absent. No reflections.";
    sceneInstruction.textContent = "Drag to orbit · blue meets blue · red meets green";
    hierarchyPlot.setAttribute("aria-label", "Colors of exposed Chair44 arrows in the local search");
  } else {
    panelKicker.textContent = "corner-direction graph";
    hierarchyTitle.textContent = 'Rotations';
    panelCount.textContent = String(orientationCounts(currentInflationState.leaves).size);
    panelCountLabel.textContent = "of 8 present";
    scaleLeft.textContent = "8 directions";
    scaleRight.textContent = "quarter turns";
    panelDescription.textContent = "Eight missing-corner directions, connected by quarter turns. Each node groups three marked rotations. Dot size shows tile count; pale nodes are absent. No reflections.";
    sceneInstruction.textContent = "Drag to orbit · markings rotate with each chair";
    orientationPlot.setAttribute("aria-label", "Rotatable eight-node graph of missing-corner directions connected by proper quarter turns");
  }
  updateReadout();
  updateActionButtons();
  drawHierarchyPlot();
  updateOrientationBall();
}

function cameraDestinationForVisual(visual) {
  const direction = camera.position.clone().sub(controls.target).normalize();
  const sphere = new THREE.Box3().setFromObject(visual.group).getBoundingSphere(new THREE.Sphere());
  const vertical = THREE.MathUtils.degToRad(camera.fov);
  const horizontal = 2 * Math.atan(Math.tan(vertical / 2) * camera.aspect);
  const distance = sphere.radius / Math.sin(Math.min(vertical, horizontal) / 2) * 1.20;
  controls.target.copy(sphere.center);
  return sphere.center.clone().addScaledVector(direction, distance);
}

function cameraDestinationForGrowth(visual) {
  // Keep the viewing direction and orbit target fixed. Only dolly backward
  // when a corner of the growing patch would leave the padded view frustum.
  const backward = camera.position.clone().sub(controls.target).normalize();
  const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
  const up = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
  const tangentY = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2) * 0.85;
  const tangentX = tangentY * camera.aspect;
  const bounds = new THREE.Box3().setFromObject(visual.group);
  let distance = camera.position.distanceTo(controls.target);
  for (const x of [bounds.min.x, bounds.max.x]) {
    for (const y of [bounds.min.y, bounds.max.y]) {
      for (const z of [bounds.min.z, bounds.max.z]) {
        const point = new THREE.Vector3(x, y, z).sub(controls.target);
        distance = Math.max(distance, point.dot(backward) + Math.max(
          Math.abs(point.dot(right)) / tangentX,
          Math.abs(point.dot(up)) / tangentY,
          camera.near * 2
        ));
      }
    }
  }
  return controls.target.clone().addScaledVector(backward, distance);
}

function stopAutoRun() {
  autoRun = false;
  window.clearTimeout(runTimer);
  runTimer = null;
}

function scheduleSearchStep() {
  window.clearTimeout(runTimer);
  runTimer = null;
  if (!autoRun) return;
  if (growthState.complete) {
    stopAutoRun();
    updateActionButtons();
    return;
  }
  runTimer = window.setTimeout(() => {
    runTimer = null;
    runNextSearchStep();
  }, 70);
}

function swapVisual(nextVisual, duration, cameraDestination, crossFade = true) {
  // Repeatedly cross-fading transparent copies changes their combined opacity.
  // Local growth replaces geometry in one frame and only animates the camera.
  const previousVisual = currentVisual;
  setVisualOpacity(nextVisual, crossFade ? 0 : 1);
  root.add(nextVisual.group);
  if (prefersReducedMotion) {
    disposeVisual(currentVisual);
    currentVisual = nextVisual;
    setVisualOpacity(nextVisual, 1);
    camera.position.copy(cameraDestination);
    updateActionButtons();
    scheduleSearchStep();
    return;
  }
  if (!crossFade) {
    disposeVisual(previousVisual);
    currentVisual = nextVisual;
  }
  transition = {
    from: crossFade ? previousVisual : null,
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
  if (direction > 0) {
    while (inflationStates.length <= targetGeneration) {
      inflationStates.push(expandInflationState(
        inflationStates[inflationStates.length - 1],
        randomRetainedChildIndex()
      ));
    }
  } else {
    inflationStates.length = targetGeneration + 1;
  }
  currentInflationState = inflationStates[targetGeneration];
  const nextVisual = makeVisual(currentInflationState);
  refreshChairHighlight(nextVisual);
  generation = targetGeneration;
  viewport.dataset.retainedChildren = inflationStates
    .slice(1)
    .map((state) => String(state.retainedChildIndex + 1))
    .join(",");
  updateReadout();
  updateOrientationBall();

  const cameraDestination = cameraDestinationForVisual(nextVisual);
  swapVisual(nextVisual, 720, cameraDestination);
}

function showGrowthStep(direction) {
  if (transition || mode !== "search") return;
  const nextState = direction > 0 ? growOne(growthState) : shrinkOne(growthState);
  if (nextState === growthState) return;
  growthState = nextState;
  const nextVisual = makeSearchVisual(growthState);
  updateReadout();
  drawHierarchyPlot();
  updateOrientationBall();
  refreshChairHighlight(nextVisual);
  swapVisual(nextVisual, autoRun ? 190 : 420, cameraDestinationForGrowth(nextVisual), false);
}

function runNextSearchStep() {
  if (!autoRun || transition || mode !== "search") return;
  if (growthState.complete) {
    stopAutoRun();
    updateActionButtons();
    return;
  }
  showGrowthStep(1);
}

inflateButton.addEventListener("click", () => {
  if (transition) return;
  switchMode('inflation');
  showGeneration(generation + 1);
});
applyOneButton.addEventListener('click', () => {
  if (transition) return;
  switchMode('search');
  showGrowthStep(1);
});
backButton.addEventListener("click", () => {
  stopAutoRun();
  if (mode === "search") showGrowthStep(-1);
  else showGeneration(generation - 1);
});
runButton.addEventListener("click", () => {
  if (autoRun) stopAutoRun();
  else autoRun = true;
  updateActionButtons();
  if (autoRun) runNextSearchStep();
});
document.getElementById('show-markings').addEventListener('change', event => {
  for (const visual of [currentVisual, transition?.from, transition?.to]) {
    const arrows = visual?.group.getObjectByName('chair44-arrows');
    if (arrows) arrows.visible = event.target.checked;
  }
});
function switchMode(nextMode) {
  stopAutoRun();
  if (mode === nextMode) return;
  mode = nextMode;
  chairModeSelect.value = mode;
  disposeVisual(currentVisual);
  currentVisual = mode === "search" ? makeSearchVisual(growthState) : makeVisual(currentInflationState);
  root.add(currentVisual.group);
  refreshChairHighlight(currentVisual);
  camera.position.copy(mode === "search" ? cameraDestinationForGrowth(currentVisual) : cameraDestinationForVisual(currentVisual));
  updateModePanel();
}
chairModeSelect.addEventListener("change", () => switchMode(chairModeSelect.value));

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
      context.arc(x, y, 5.5, 0, Math.PI * 2);
      const color = new THREE.Color(channelColor(mark.color));
      context.fillStyle = `rgb(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)})`;
      if (mark.color !== "green") context.fill();
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
      const color = new THREE.Color(CORNER_COLORS[orientationIndex(missing)]);
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
  if (currentVisual && !transition) {
    camera.position.copy(mode === "search" ? cameraDestinationForGrowth(currentVisual) : cameraDestinationForVisual(currentVisual));
  }
}

function resizeOrientationBall() {
  const width = Math.max(1, orientationPlot.clientWidth);
  const height = Math.max(1, orientationPlot.clientHeight);
  orientationRenderer.setSize(width, height, false);
  orientationCamera.aspect = width / height;
  orientationCamera.updateProjectionMatrix();
}

new ResizeObserver(resize).observe(viewport);
new ResizeObserver(drawHierarchyPlot).observe(hierarchyPlot);
new ResizeObserver(resizeOrientationBall).observe(orientationPlot);
resize();
resizeOrientationBall();
drawHierarchyPlot();
updateModePanel();

function animate(time) {
  controls.update();
  orientationControls.update();
  updateOrientationBoundary();
  if (transition) {
    const raw = Math.min(1, (time - transition.start) / transition.duration);
    const eased = raw * raw * (3 - 2 * raw);
    if (transition.from) {
      setVisualOpacity(transition.from, 1 - eased);
      setVisualOpacity(transition.to, eased);
    }
    camera.position.lerpVectors(transition.cameraStart, transition.cameraDestination, eased);
    if (raw >= 1) {
      if (transition.from) disposeVisual(transition.from);
      currentVisual = transition.to;
      transition = null;
      updateActionButtons();
      scheduleSearchStep();
    }
  }
  renderer.render(scene, camera);
  orientationRenderer.render(orientationScene, orientationCamera);
  requestAnimationFrame(animate);
}

requestAnimationFrame(animate);
