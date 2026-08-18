import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const viewport = document.getElementById("viewport");
const substituteButton = document.getElementById("substitute-button");
const backButton = document.getElementById("back-button");
const generationValue = document.getElementById("generation-value");
const tileValue = document.getElementById("tile-value");
const orientationPlot = document.getElementById("orientation-plot");
const orientationValue = document.getElementById("orientation-value");
const orientationCurrent = document.getElementById("orientation-current");

const SQRT3 = Math.sqrt(3);
const INITIAL_GENERATION = 0;
const MAX_GENERATION = 5;
const FIXED_CHILD_SEQUENCE = [5, 5, 3, 5, 5];
const FACE_CENTER = new THREE.Vector3(SQRT3 / 2, 0.5, 0.5);
const FACE_INDICES = [
  0, 2, 1,
  3, 4, 5,
  0, 1, 4, 0, 4, 3,
  1, 2, 5, 1, 5, 4,
  2, 0, 3, 2, 3, 5
];
const EDGE_INDICES = [
  0, 1, 1, 2, 2, 0,
  3, 4, 4, 5, 5, 3,
  0, 3, 1, 4, 2, 5
];
const CANONICAL_VERTICES = [
  new THREE.Vector3(0, 0, 0),
  new THREE.Vector3(SQRT3, 0, 0),
  new THREE.Vector3(0, 1, 0),
  new THREE.Vector3(0, 0, 1),
  new THREE.Vector3(SQRT3, 0, 1),
  new THREE.Vector3(0, 1, 1)
];

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xedf1ef);
scene.add(new THREE.HemisphereLight(0xffffff, 0xaab8b1, 1.35));
const keyLight = new THREE.DirectionalLight(0xffffff, 1.1);
keyLight.position.set(5, 8, 7);
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0xc7d9ff, 0.45);
fillLight.position.set(-6, -2, 4);
scene.add(fillLight);

const camera = new THREE.PerspectiveCamera(34, 1, 0.002, 320);
camera.up.set(0, 0, 1);

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
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
controls.dampingFactor = 0.055;
controls.minDistance = 0.025;
controls.maxDistance = 420;

const root = new THREE.Group();
root.position.set(0.38, -0.08, 0);
scene.add(root);

const content = new THREE.Group();
content.position.copy(FACE_CENTER).multiplyScalar(-1);
root.add(content);

controls.target.copy(root.position);
camera.position.copy(root.position).add(
  new THREE.Vector3(3.55, 2.45, 4.2).multiplyScalar(2 ** INITIAL_GENERATION)
);
controls.update();
const lockedAzimuth = controls.getAzimuthalAngle();
controls.minAzimuthAngle = lockedAzimuth;
controls.maxAzimuthAngle = lockedAzimuth;
controls.minPolarAngle = 0.24;
controls.maxPolarAngle = 1.34;

const parentOutline = makeParentOutline();
content.add(parentOutline);

const daughterTransforms = makeDaughterTransforms();
let generation = INITIAL_GENERATION;
let subdivisionWords = [new THREE.Matrix4()];
let fixedPath = new THREE.Matrix4();
for (let depth = 0; depth < INITIAL_GENERATION; depth += 1) {
  subdivisionWords = substitute(subdivisionWords);
  fixedPath.multiply(daughterTransforms[FIXED_CHILD_SEQUENCE[depth]]);
}
const initialNormalization = fixedPath.clone().invert();
let currentExpandedTransforms = subdivisionWords.map((word) => initialNormalization.clone().multiply(word));
let currentVisual = makeVisual(currentExpandedTransforms);
content.add(currentVisual.group);
tileValue.textContent = subdivisionWords.length.toLocaleString();

const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
let transition = null;

function matrixFromColumns(origin, xColumn, yColumn, zColumn) {
  return new THREE.Matrix4().set(
    xColumn.x, yColumn.x, zColumn.x, origin.x,
    xColumn.y, yColumn.y, zColumn.y, origin.y,
    xColumn.z, yColumn.z, zColumn.z, origin.z,
    0, 0, 0, 1
  );
}

function aroundAxis(point, axis, angle) {
  const moveTo = new THREE.Matrix4().makeTranslation(-point.x, -point.y, -point.z);
  const rotate = new THREE.Matrix4().makeRotationAxis(axis.clone().normalize(), angle);
  const moveBack = new THREE.Matrix4().makeTranslation(point.x, point.y, point.z);
  return moveBack.multiply(rotate).multiply(moveTo);
}

function makeBaseFour() {
  return [
    matrixFromColumns(
      new THREE.Vector3(SQRT3 / 2, 0, 0),
      new THREE.Vector3(0.5, 0, 0),
      new THREE.Vector3(0, 0.5, 0),
      new THREE.Vector3(0, 0, 0.5)
    ),
    matrixFromColumns(
      new THREE.Vector3(SQRT3 / 2, 0, 0.5),
      new THREE.Vector3(-0.5, 0, 0),
      new THREE.Vector3(0, 0.5, 0),
      new THREE.Vector3(0, 0, -0.5)
    ),
    matrixFromColumns(
      new THREE.Vector3(0, 0.5, 0.5),
      new THREE.Vector3(0.5, 0, 0),
      new THREE.Vector3(0, -0.5, 0),
      new THREE.Vector3(0, 0, -0.5)
    ),
    matrixFromColumns(
      new THREE.Vector3(0, 0.5, 0),
      new THREE.Vector3(0.5, 0, 0),
      new THREE.Vector3(0, 0.5, 0),
      new THREE.Vector3(0, 0, 0.5)
    )
  ];
}

function makeDaughterTransforms() {
  const quarterTurn = aroundAxis(
    new THREE.Vector3(0, 0.25, 0.25),
    new THREE.Vector3(1, 0, 0),
    Math.PI / 2
  );
  const thirdTurn = aroundAxis(
    new THREE.Vector3(SQRT3 / 6, 0.5, 0),
    new THREE.Vector3(0, 0, 1),
    (2 * Math.PI) / 3
  );
  const lift = new THREE.Matrix4().makeTranslation(0, 0, 0.5);

  const slabA = makeBaseFour().map((matrix, index) => {
    if (index === 1 || index === 2) return quarterTurn.clone().multiply(matrix);
    return matrix;
  });
  const slabB = makeBaseFour().map((matrix, index) => {
    const lifted = lift.clone().multiply(matrix);
    if (index === 2 || index === 3) return thirdTurn.clone().multiply(lifted);
    return lifted;
  });
  return [...slabA, ...slabB];
}

function substitute(transforms) {
  const next = [];
  for (const parent of transforms) {
    for (const child of daughterTransforms) {
      next.push(parent.clone().multiply(child));
    }
  }
  return next;
}

function canonicalQuaternion(matrix) {
  const position = new THREE.Vector3();
  const quaternion = new THREE.Quaternion();
  const scale = new THREE.Vector3();
  matrix.decompose(position, quaternion, scale);
  quaternion.normalize();
  const shouldFlip = quaternion.w < -1e-10
    || (Math.abs(quaternion.w) <= 1e-10 && (
      quaternion.x < -1e-10
      || (Math.abs(quaternion.x) <= 1e-10 && quaternion.y < -1e-10)
      || (Math.abs(quaternion.x) <= 1e-10 && Math.abs(quaternion.y) <= 1e-10 && quaternion.z < 0)
    ));
  if (shouldFlip) quaternion.set(-quaternion.x, -quaternion.y, -quaternion.z, -quaternion.w);
  return quaternion;
}

function distinctOrientations(transforms) {
  const orientations = new Map();
  for (const matrix of transforms) {
    const quaternion = canonicalQuaternion(matrix);
    const key = orientationKey(quaternion);
    if (!orientations.has(key)) orientations.set(key, quaternion);
  }
  return [...orientations.values()];
}

function orientationKey(quaternion) {
  return [quaternion.x, quaternion.y, quaternion.z, quaternion.w]
    .map((value) => value.toFixed(5))
    .join(",");
}

function orientationColorFromQuaternion(quaternion) {
  const canonical = canonicalizeQuaternion(quaternion.clone().normalize());
  const azimuth = Math.atan2(canonical.y, canonical.x) / (Math.PI * 2) + 0.5;
  const hue = (azimuth + canonical.z * 0.16 + (1 - canonical.w) * 0.08 + 1) % 1;
  return new THREE.Color().setHSL(hue, 0.52, 0.52);
}

function orientationColor(matrix) {
  return orientationColorFromQuaternion(canonicalQuaternion(matrix));
}

const orientationOrbitCache = new Map();

function orientationOrbit(depth) {
  if (orientationOrbitCache.has(depth)) return orientationOrbitCache.get(depth);
  const generators = distinctOrientations(daughterTransforms);
  let current = new Map([["0.00000,0.00000,0.00000,1.00000", new THREE.Quaternion()]]);
  for (let level = 0; level < depth; level += 1) {
    const next = new Map();
    for (const parent of current.values()) {
      for (const generator of generators) {
        const quaternion = parent.clone().multiply(generator).normalize();
        const canonical = canonicalizeQuaternion(quaternion);
        const key = orientationKey(canonical);
        if (!next.has(key)) next.set(key, canonical);
      }
    }
    current = next;
  }
  const result = [...current.values()];
  orientationOrbitCache.set(depth, result);
  return result;
}

function canonicalizeQuaternion(quaternion) {
  const shouldFlip = quaternion.w < -1e-10
    || (Math.abs(quaternion.w) <= 1e-10 && (
      quaternion.x < -1e-10
      || (Math.abs(quaternion.x) <= 1e-10 && quaternion.y < -1e-10)
      || (Math.abs(quaternion.x) <= 1e-10 && Math.abs(quaternion.y) <= 1e-10 && quaternion.z < 0)
    ));
  if (shouldFlip) quaternion.set(-quaternion.x, -quaternion.y, -quaternion.z, -quaternion.w);
  return quaternion;
}

function axisAnglePoint(quaternion) {
  const w = THREE.MathUtils.clamp(quaternion.w, -1, 1);
  const angle = 2 * Math.acos(w);
  const sine = Math.sqrt(Math.max(0, 1 - w * w));
  if (angle < 1e-8 || sine < 1e-8) return new THREE.Vector3();
  return new THREE.Vector3(quaternion.x / sine, quaternion.y / sine, quaternion.z / sine)
    .multiplyScalar(angle / Math.PI);
}

function projectOrientationPoint(point) {
  const yaw = 0.68;
  const pitch = -0.42;
  const x1 = Math.cos(yaw) * point.x + Math.sin(yaw) * point.z;
  const z1 = -Math.sin(yaw) * point.x + Math.cos(yaw) * point.z;
  const y2 = Math.cos(pitch) * point.y - Math.sin(pitch) * z1;
  const z2 = Math.sin(pitch) * point.y + Math.cos(pitch) * z1;
  return { x: x1, y: y2, depth: z2 };
}

function drawOrientationBall(transforms) {
  if (!orientationPlot) return;
  const currentOrientations = distinctOrientations(transforms);
  const sampleDepth = generation + 2;
  const orientations = orientationOrbit(sampleDepth);
  orientationValue.textContent = orientations.length.toLocaleString();
  orientationCurrent.textContent = `${currentOrientations.length.toLocaleString()} ${currentOrientations.length === 1 ? "occurs" : "occur"} in the current patch.`;
  orientationPlot.setAttribute(
    "aria-label",
    `Axis-angle ball sampling ${orientations.length.toLocaleString()} tile ${orientations.length === 1 ? "orientation" : "orientations"} through word depth ${sampleDepth}`
  );

  const size = Math.max(120, Math.round(orientationPlot.clientWidth || 220));
  const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
  orientationPlot.width = Math.round(size * pixelRatio);
  orientationPlot.height = Math.round(size * pixelRatio);
  const context = orientationPlot.getContext("2d");
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  context.clearRect(0, 0, size, size);

  const center = size / 2;
  const radius = size * 0.43;
  context.strokeStyle = "rgba(23, 32, 30, 0.20)";
  context.lineWidth = 1;
  context.beginPath();
  context.arc(center, center, radius, 0, Math.PI * 2);
  context.stroke();

  context.strokeStyle = "rgba(23, 32, 30, 0.09)";
  context.beginPath();
  context.ellipse(center, center, radius, radius * 0.31, 0, 0, Math.PI * 2);
  context.moveTo(center, center - radius);
  context.bezierCurveTo(center + radius * 0.38, center - radius * 0.5, center + radius * 0.38, center + radius * 0.5, center, center + radius);
  context.moveTo(center, center - radius);
  context.bezierCurveTo(center - radius * 0.38, center - radius * 0.5, center - radius * 0.38, center + radius * 0.5, center, center + radius);
  context.stroke();

  const points = orientations
    .map((quaternion) => ({
      ...projectOrientationPoint(axisAnglePoint(quaternion)),
      color: orientationColorFromQuaternion(quaternion)
    }))
    .sort((a, b) => a.depth - b.depth);
  const pointRadius = points.length > 1500 ? 0.72 : points.length > 250 ? 1 : points.length > 40 ? 1.35 : 1.8;
  for (const point of points) {
    const alpha = 0.28 + 0.48 * ((point.depth + 1) / 2);
    const red = Math.round(point.color.r * 255);
    const green = Math.round(point.color.g * 255);
    const blue = Math.round(point.color.b * 255);
    context.fillStyle = `rgba(${red}, ${green}, ${blue}, ${alpha.toFixed(3)})`;
    context.beginPath();
    context.arc(center + point.x * radius, center - point.y * radius, pointRadius, 0, Math.PI * 2);
    context.fill();
  }

  context.fillStyle = "rgba(23, 32, 30, 0.72)";
  context.beginPath();
  context.arc(center, center, 1.8, 0, Math.PI * 2);
  context.fill();
}

function makeTransparentMaterial({ line = false, opacity } = {}) {
  if (line) {
    const material = new THREE.LineBasicMaterial({
      color: 0x17201e,
      transparent: true,
      depthWrite: false,
      depthTest: true,
      opacity
    });
    material.userData.baseOpacity = opacity;
    return material;
  }
  const material = new THREE.MeshPhongMaterial({
    color: 0xffffff,
    vertexColors: true,
    transparent: true,
    depthWrite: false,
    depthTest: true,
    opacity,
    side: THREE.DoubleSide,
    flatShading: true,
    shininess: 18,
    specular: 0x53605c,
    polygonOffset: true,
    polygonOffsetFactor: 1,
    polygonOffsetUnits: 1
  });
  material.userData.baseOpacity = opacity;
  return material;
}

function makeVisual(transforms) {
  const facePositions = [];
  const faceColors = [];
  const edgePositions = [];
  const edgeColors = [];
  const transformed = CANONICAL_VERTICES.map(() => new THREE.Vector3());

  for (const matrix of transforms) {
    const color = orientationColor(matrix);
    for (let i = 0; i < CANONICAL_VERTICES.length; i += 1) {
      transformed[i].copy(CANONICAL_VERTICES[i]).applyMatrix4(matrix);
    }
    for (const index of FACE_INDICES) {
      const point = transformed[index];
      facePositions.push(point.x, point.y, point.z);
      faceColors.push(color.r, color.g, color.b);
    }
    for (const index of EDGE_INDICES) {
      const point = transformed[index];
      edgePositions.push(point.x, point.y, point.z);
      edgeColors.push(color.r, color.g, color.b);
    }
  }

  const faceOpacity = Math.max(0.006, 0.09 / Math.pow(transforms.length, 0.28));
  const edgeOpacity = Math.max(0.01, 0.16 / Math.pow(transforms.length, 0.25));
  const faceGeometry = new THREE.BufferGeometry();
  faceGeometry.setAttribute("position", new THREE.Float32BufferAttribute(facePositions, 3));
  faceGeometry.setAttribute("color", new THREE.Float32BufferAttribute(faceColors, 3));
  faceGeometry.computeVertexNormals();
  const faceMaterial = makeTransparentMaterial({ opacity: faceOpacity });
  const mesh = new THREE.Mesh(faceGeometry, faceMaterial);
  mesh.renderOrder = 1;

  const edgeGeometry = new THREE.BufferGeometry();
  edgeGeometry.setAttribute("position", new THREE.Float32BufferAttribute(edgePositions, 3));
  edgeGeometry.setAttribute("color", new THREE.Float32BufferAttribute(edgeColors, 3));
  const edgeMaterial = makeTransparentMaterial({ line: true, opacity: edgeOpacity });
  const edges = new THREE.LineSegments(edgeGeometry, edgeMaterial);
  edges.renderOrder = 2;

  const group = new THREE.Group();
  group.add(mesh, edges);
  return { group, materials: [faceMaterial, edgeMaterial], geometries: [faceGeometry, edgeGeometry] };
}

function makeParentOutline() {
  const points = [];
  for (const index of EDGE_INDICES) points.push(CANONICAL_VERTICES[index]);
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineDashedMaterial({ color: 0x1d6b62, opacity: 0.72, transparent: true, depthTest: false, dashSize: 0.035, gapSize: 0.025 });
  const line = new THREE.LineSegments(geometry, material);
  line.computeLineDistances();
  line.renderOrder = 3;
  return line;
}

function disposeVisual(visual) {
  content.remove(visual.group);
  for (const geometry of visual.geometries) geometry.dispose();
  for (const material of visual.materials) material.dispose();
}

function setVisualOpacity(visual, amount) {
  for (const material of visual.materials) {
    material.opacity = material.userData.baseOpacity * amount;
  }
}

function stateAtGeneration(targetGeneration) {
  let words = [new THREE.Matrix4()];
  const path = new THREE.Matrix4();
  const depthLimit = targetGeneration;
  for (let depth = 0; depth < depthLimit; depth += 1) {
    words = substitute(words);
    path.multiply(daughterTransforms[FIXED_CHILD_SEQUENCE[depth]]);
  }
  const normalization = path.clone().invert();
  return {
    words,
    path,
    transforms: words.map((word) => normalization.clone().multiply(word))
  };
}

function updateActionButtons() {
  const busy = Boolean(transition);
  backButton.disabled = busy || generation <= 0;
  substituteButton.disabled = busy || generation >= MAX_GENERATION;
  substituteButton.querySelector("span").textContent = generation >= MAX_GENERATION
    ? "Maximum expansion reached"
    : "Apply one more expansion";
}

function showGeneration(targetGeneration) {
  if (transition || targetGeneration < 0 || targetGeneration > MAX_GENERATION || targetGeneration === generation) return;
  const direction = targetGeneration > generation ? 1 : -1;
  const nextState = stateAtGeneration(targetGeneration);
  const expandedTransforms = nextState.transforms;
  currentExpandedTransforms = expandedTransforms;
  const nextVisual = makeVisual(expandedTransforms);
  setVisualOpacity(nextVisual, 0);
  content.add(nextVisual.group);

  generation = targetGeneration;
  subdivisionWords = nextState.words;
  fixedPath = nextState.path;
  generationValue.textContent = String(generation);
  tileValue.textContent = subdivisionWords.length.toLocaleString();
  drawOrientationBall(expandedTransforms);

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

substituteButton.addEventListener("click", () => showGeneration(generation + 1));
backButton.addEventListener("click", () => showGeneration(generation - 1));
updateActionButtons();

function resize() {
  const width = Math.max(1, viewport.clientWidth);
  const height = Math.max(1, viewport.clientHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

const resizeObserver = new ResizeObserver(resize);
resizeObserver.observe(viewport);
const orientationResizeObserver = new ResizeObserver(() => drawOrientationBall(currentExpandedTransforms));
orientationResizeObserver.observe(orientationPlot);
resize();
drawOrientationBall(currentExpandedTransforms);

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
