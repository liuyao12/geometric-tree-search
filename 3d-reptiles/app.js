import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { exactDyadicSO3 } from "./dyadic-so3.js";

const viewport = document.getElementById("viewport");
const substituteButton = document.getElementById("substitute-button");
const backButton = document.getElementById("back-button");
const generationValue = document.getElementById("generation-value");
const tileValue = document.getElementById("tile-value");
const orientationPlot = document.getElementById("orientation-plot");
const orientationValue = document.getElementById("orientation-value");
const orientationCurrent = document.getElementById("orientation-current");
const visualEffectSelect = document.getElementById("visual-effect-select");
const effectDescription = document.getElementById("effect-description");
const tileSelect = document.getElementById("tile-select");
const orientationPanel = document.querySelector(".orientation-panel");
const orientationMatrix = document.getElementById("orientation-matrix");
const matrixFactor = document.getElementById("matrix-factor");
const matrixValues = document.getElementById("matrix-values");

tileSelect.addEventListener("change", () => {
  window.location.href = tileSelect.value;
});

const SQRT3 = Math.sqrt(3);
const INITIAL_GENERATION = 1;
const MAX_GENERATION = 5;
const FIXED_CHILD_SEQUENCE = [5, 5, 3, 5, 5];
const TURNING_CHILD_INDICES = new Set([1, 2, 6, 7]);
const TURN_GENERATION_COLORS = [
  0xb8bfbc,
  0xf2553d,
  0xf2a51f,
  0x18a98b,
  0x3478df,
  0xa94fd1
];
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

const orientationShellGeometry = new THREE.SphereGeometry(1, 28, 18);
const orientationShell = new THREE.Mesh(
  orientationShellGeometry,
  new THREE.MeshBasicMaterial({ color: 0xf8fbf9, transparent: true, opacity: 0.11, depthWrite: false, side: THREE.DoubleSide })
);
orientationScene.add(orientationShell);

function makeOrientationDiameter(axis, color) {
  const geometry = new THREE.BufferGeometry().setFromPoints([
    axis.clone().multiplyScalar(-1),
    axis.clone()
  ]);
  const line = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.34, depthWrite: false }));
  orientationScene.add(line);
  const endpointGeometry = new THREE.BufferGeometry().setFromPoints([
    axis.clone().multiplyScalar(-1),
    axis.clone()
  ]);
  const endpoints = new THREE.Points(endpointGeometry, new THREE.PointsMaterial({ color, size: 0.055, sizeAttenuation: true, depthWrite: false }));
  orientationScene.add(endpoints);
}

makeOrientationDiameter(new THREE.Vector3(1, 0, 0), 0xd16f59);
makeOrientationDiameter(new THREE.Vector3(0, 1, 0), 0x4f81ad);
makeOrientationDiameter(new THREE.Vector3(0, 0, 1), 0x4f9179);

function makeOrientationCircle(color, opacity) {
  const points = [];
  for (let index = 0; index < 128; index += 1) {
    const angle = (index / 128) * Math.PI * 2;
    points.push(new THREE.Vector3(Math.cos(angle), Math.sin(angle), 0));
  }
  const circle = new THREE.LineLoop(
    new THREE.BufferGeometry().setFromPoints(points),
    new THREE.LineBasicMaterial({ color, transparent: true, opacity, depthWrite: false, depthTest: false })
  );
  circle.renderOrder = 2;
  orientationScene.add(circle);
  return circle;
}

const xyGreatCircle = makeOrientationCircle(0x4f9179, 0.28);
const xzGreatCircle = makeOrientationCircle(0x4f81ad, 0.28);
xzGreatCircle.rotation.x = Math.PI / 2;
const yzGreatCircle = makeOrientationCircle(0xd16f59, 0.28);
yzGreatCircle.rotation.y = Math.PI / 2;
const orientationBoundary = makeOrientationCircle(0x17201e, 0.52);
orientationBoundary.renderOrder = 3;

const orientationGraphGroup = new THREE.Group();
orientationScene.add(orientationGraphGroup);

const orientationPointGeometry = new THREE.BufferGeometry();
const orientationPointMaterial = new THREE.ShaderMaterial({
  transparent: true,
  depthWrite: false,
  depthTest: true,
  uniforms: {
    pixelRatio: { value: Math.min(window.devicePixelRatio, 2) }
  },
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
      pixelRatio: { value: Math.min(window.devicePixelRatio, 2) }
    },
    vertexShader: `
      uniform float pixelRatio;
      void main() {
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = 28.0 * pixelRatio;
      }
    `,
    fragmentShader: `
      void main() {
        float radius = length(gl_PointCoord - vec2(0.5));
        float outer = 1.0 - smoothstep(0.44, 0.5, radius);
        float inner = smoothstep(0.33, 0.38, radius);
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
let orientationPointBaseColors = [];
let selectedOrientationKey = null;
let orientationRepresentatives = new Map();
let orientationGenerationEdges = [];

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 0.025;
controls.maxDistance = 420;
const orbitDriftAxis = new THREE.Vector3();
const orbitDriftQuaternion = new THREE.Quaternion();
const orbitPreviousOffset = new THREE.Vector3();
const orbitCurrentOffset = new THREE.Vector3();
const ORBIT_DRIFT_SPEED = 0.085;
let orbitDrag = null;
let orbitDriftActive = false;

renderer.domElement.addEventListener("pointerdown", (event) => {
  if (event.pointerType === "mouse" && event.button !== 0) return;
  orbitDrag = {
    pointerId: event.pointerId,
    lastX: event.clientX,
    lastY: event.clientY,
    distance: 0,
    axis: null,
    lastOffset: camera.position.clone().sub(controls.target).normalize()
  };
});

renderer.domElement.addEventListener("pointermove", (event) => {
  if (!orbitDrag || event.pointerId !== orbitDrag.pointerId) return;
  orbitDrag.distance += Math.hypot(event.clientX - orbitDrag.lastX, event.clientY - orbitDrag.lastY);
  orbitDrag.lastX = event.clientX;
  orbitDrag.lastY = event.clientY;
  orbitCurrentOffset.copy(camera.position).sub(controls.target).normalize();
  orbitDriftQuaternion.setFromUnitVectors(orbitDrag.lastOffset, orbitCurrentOffset);
  const sineHalfAngle = Math.hypot(
    orbitDriftQuaternion.x,
    orbitDriftQuaternion.y,
    orbitDriftQuaternion.z
  );
  if (sineHalfAngle > 1e-5) {
    orbitDrag.axis = new THREE.Vector3(
      orbitDriftQuaternion.x,
      orbitDriftQuaternion.y,
      orbitDriftQuaternion.z
    ).divideScalar(sineHalfAngle);
  }
  orbitDrag.lastOffset.copy(orbitCurrentOffset);
});

renderer.domElement.addEventListener("pointerup", (event) => {
  if (!orbitDrag || event.pointerId !== orbitDrag.pointerId) return;
  if (orbitDrag.distance > 4 && orbitDrag.axis) {
    orbitDriftAxis.copy(orbitDrag.axis);
    orbitDriftActive = true;
  }
  orbitDrag = null;
});

renderer.domElement.addEventListener("pointercancel", (event) => {
  if (orbitDrag?.pointerId === event.pointerId) orbitDrag = null;
});

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

const parentOutline = makeParentOutline();
content.add(parentOutline);

const daughterTransforms = makeDaughterTransforms();
let mutedOrientationKeys = new Set();
let visualEffect = visualEffectSelect.value;
let generation = INITIAL_GENERATION;
let subdivisionWords = [new THREE.Matrix4()];
let currentTurnGenerations = [null];
let fixedPath = new THREE.Matrix4();
for (let depth = 0; depth < INITIAL_GENERATION; depth += 1) {
  subdivisionWords = substitute(subdivisionWords);
  currentTurnGenerations = substituteTurnGenerations(currentTurnGenerations, depth + 1);
  fixedPath.multiply(daughterTransforms[FIXED_CHILD_SEQUENCE[depth]]);
}
const initialNormalization = fixedPath.clone().invert();
let currentExpandedTransforms = subdivisionWords.map((word) => initialNormalization.clone().multiply(word));
updateMutedOrientationKeys(currentExpandedTransforms);
let currentVisual = makeVisual(currentExpandedTransforms, currentTurnGenerations);
content.add(currentVisual.group);
generationValue.textContent = String(generation);
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

function substituteTurnGenerations(parentGenerations, nextGeneration) {
  const children = [];
  for (const parentGeneration of parentGenerations) {
    for (let childIndex = 0; childIndex < daughterTransforms.length; childIndex += 1) {
      children.push(
        parentGeneration ?? (TURNING_CHILD_INDICES.has(childIndex) ? nextGeneration : null)
      );
    }
  }
  return children;
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

function updateMutedOrientationKeys(transforms) {
  const counts = new Map();
  for (const matrix of transforms) {
    const key = orientationKey(canonicalQuaternion(matrix));
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const maximum = Math.max(...counts.values());
  mutedOrientationKeys = new Set(
    [...counts]
      .filter(([, count]) => count === maximum && (maximum > 1 || transforms.length === 1))
      .map(([key]) => key)
  );
}

function firstTurnGenerationByOrientation(transforms, turnGenerations) {
  const generations = new Map();
  transforms.forEach((matrix, index) => {
    const key = orientationKey(canonicalQuaternion(matrix));
    const generationIntroduced = turnGenerations[index];
    if (!generations.has(key)) generations.set(key, generationIntroduced);
    else if (generationIntroduced !== null) {
      const existing = generations.get(key);
      if (existing === null || generationIntroduced < existing) generations.set(key, generationIntroduced);
    }
  });
  return generations;
}

function turnGenerationColor(generationIntroduced) {
  return new THREE.Color(TURN_GENERATION_COLORS[generationIntroduced] ?? 0xd943a4);
}

function orientationKey(quaternion) {
  return [quaternion.x, quaternion.y, quaternion.z, quaternion.w]
    .map((value) => {
      const rounded = Number(value.toFixed(5));
      return (Object.is(rounded, -0) ? 0 : rounded).toFixed(5);
    })
    .join(",");
}

function orientationColorFromQuaternion(quaternion) {
  const canonical = canonicalizeQuaternion(quaternion.clone().normalize());
  const azimuth = Math.atan2(canonical.y, canonical.x) / (Math.PI * 2) + 0.5;
  const hue = (azimuth + canonical.z * 0.16 + (1 - canonical.w) * 0.08 + 1) % 1;
  return new THREE.Color().setHSL(hue, 0.84, 0.55);
}

function orientationColor(matrix) {
  return orientationColorFromQuaternion(canonicalQuaternion(matrix));
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

function buildOrientationGenerationEdges(targetGeneration) {
  if (targetGeneration === 0) return [];
  const normalization = fixedPath.clone().invert();
  const leafKeys = new Set(orientationPointKeys);
  const resolvedLeafKeys = new Map();
  const leafOrientations = [...orientationRepresentatives].map(([key, matrix]) => [
    key,
    canonicalQuaternion(matrix)
  ]);
  const resolveLeafKey = (quaternion) => {
    const roundedKey = orientationKey(quaternion);
    if (leafKeys.has(roundedKey)) return roundedKey;
    if (resolvedLeafKeys.has(roundedKey)) return resolvedLeafKeys.get(roundedKey);
    let bestKey = null;
    let bestDot = -1;
    for (const [key, candidate] of leafOrientations) {
      const dot = Math.abs(quaternion.dot(candidate));
      if (dot > bestDot) {
        bestDot = dot;
        bestKey = key;
      }
    }
    const resolved = bestDot > 1 - 1e-9 ? bestKey : null;
    resolvedLeafKeys.set(roundedKey, resolved);
    return resolved;
  };
  const fixedPrefixes = [new THREE.Matrix4()];
  for (let depth = 0; depth < targetGeneration; depth += 1) {
    fixedPrefixes.push(
      fixedPrefixes[depth].clone().multiply(daughterTransforms[FIXED_CHILD_SEQUENCE[depth]])
    );
  }
  const identityQuaternion = canonicalQuaternion(
    normalization.clone().multiply(fixedPrefixes[targetGeneration])
  );
  const identityKey = resolveLeafKey(identityQuaternion);
  const componentParents = new Map([...leafKeys].map((key) => [key, key]));
  const findComponent = (key) => {
    let root = key;
    while (componentParents.get(root) !== root) root = componentParents.get(root);
    while (componentParents.get(key) !== key) {
      const parent = componentParents.get(key);
      componentParents.set(key, root);
      key = parent;
    }
    return root;
  };
  const joinComponents = (first, second) => {
    const firstRoot = findComponent(first);
    const secondRoot = findComponent(second);
    if (firstRoot === secondRoot) return false;
    componentParents.set(secondRoot, firstRoot);
    return true;
  };
  const edges = [];
  let suffixWords = [new THREE.Matrix4()];

  // Work from the innermost retained tile outward. At each expansion the
  // distinguished child is already present; seven congruent copies of the
  // entire suffix cluster are placed around it.
  for (let depth = targetGeneration - 1; depth >= 0; depth -= 1) {
    const prefix = fixedPrefixes[depth];
    const retainedChild = daughterTransforms[FIXED_CHILD_SEQUENCE[depth]];
    for (const suffix of suffixWords) {
      const sourceWord = prefix.clone().multiply(retainedChild).multiply(suffix);
      const sourceQuaternion = canonicalQuaternion(normalization.clone().multiply(sourceWord));
      const sourceKey = resolveLeafKey(sourceQuaternion);
      for (let childIndex = 0; childIndex < daughterTransforms.length; childIndex += 1) {
        if (childIndex === FIXED_CHILD_SEQUENCE[depth]) continue;
        const targetWord = prefix.clone().multiply(daughterTransforms[childIndex]).multiply(suffix);
        const targetQuaternion = canonicalQuaternion(normalization.clone().multiply(targetWord));
        const targetKey = resolveLeafKey(targetQuaternion);
        if (targetKey === null || sourceKey === null || targetKey === sourceKey || !joinComponents(sourceKey, targetKey)) continue;
        edges.push({
          sourceKey,
          targetKey,
          sourceQuaternion,
          targetQuaternion,
          generation: targetGeneration - depth
        });
      }
    }
    suffixWords = substitute(suffixWords);
  }
  const identityComponent = findComponent(identityKey);
  const unlinkedKeys = [...leafKeys].filter((key) => findComponent(key) !== identityComponent);
  orientationPlot.dataset.unlinkedOrientations = String(unlinkedKeys.length);
  return edges;
}

function appendOrientationSegment(target, sourceQuaternion, targetQuaternion) {
  const source = axisAnglePoint(canonicalizeQuaternion(sourceQuaternion.clone()));
  const destination = axisAnglePoint(canonicalizeQuaternion(targetQuaternion.clone()));
  target.push(source.x, source.y, source.z, destination.x, destination.y, destination.z);
}

function clearOrientationGraph() {
  while (orientationGraphGroup.children.length) {
    const child = orientationGraphGroup.children[0];
    orientationGraphGroup.remove(child);
    child.geometry.dispose();
    child.material.dispose();
  }
}

function drawOrientationGenerationGraph() {
  clearOrientationGraph();
  orientationGenerationEdges = buildOrientationGenerationEdges(generation);
  orientationPlot.dataset.generationEdges = String(orientationGenerationEdges.length);
  let segmentCount = 0;
  for (const highlighted of [false, true]) {
    const positions = [];
    for (const edge of orientationGenerationEdges) {
      const incident = selectedOrientationKey !== null
        && (edge.sourceKey === selectedOrientationKey || edge.targetKey === selectedOrientationKey);
      if (incident !== highlighted) continue;
      appendOrientationSegment(positions, edge.sourceQuaternion, edge.targetQuaternion);
    }
    if (!positions.length) continue;
    segmentCount += positions.length / 6;
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    const material = new THREE.LineBasicMaterial({
      color: 0x17201e,
      transparent: true,
      opacity: highlighted ? 1 : selectedOrientationKey === null ? 0.58 : 0.1,
      depthWrite: false,
      depthTest: false
    });
    const lines = new THREE.LineSegments(geometry, material);
    lines.renderOrder = highlighted ? 3 : 2;
    orientationGraphGroup.add(lines);
  }
  orientationPlot.dataset.generationSegments = String(segmentCount);
}

function drawOrientationBall(transforms, turnGenerations = currentTurnGenerations) {
  if (!orientationPlot) return;
  orientationRepresentatives = new Map();
  for (const matrix of transforms) {
    const key = orientationKey(canonicalQuaternion(matrix));
    if (!orientationRepresentatives.has(key)) orientationRepresentatives.set(key, matrix);
  }
  const orientations = distinctOrientations(transforms);
  orientationValue.textContent = orientations.length.toLocaleString();
  orientationCurrent.textContent = `${orientations.length.toLocaleString()} ${orientations.length === 1 ? "occurs" : "occur"} in the current patch.`;
  orientationPlot.setAttribute(
    "aria-label",
    `Rotatable solid axis-angle ball containing ${orientations.length.toLocaleString()} current tile ${orientations.length === 1 ? "orientation" : "orientations"}. Click a dot or use the left and right arrow keys to inspect its exact matrix.`
  );
  const positions = [];
  const colors = [];
  const pointSizes = [];
  const orientationTurnGenerations = firstTurnGenerationByOrientation(transforms, turnGenerations);
  const orientationCounts = new Map();
  for (const matrix of transforms) {
    const key = orientationKey(canonicalQuaternion(matrix));
    orientationCounts.set(key, (orientationCounts.get(key) ?? 0) + 1);
  }
  const maximumOrientationCount = Math.max(...orientationCounts.values());
  const maximumPointSize = 16;
  orientationPointKeys = [];
  orientationPointBaseColors = [];
  for (const quaternion of orientations) {
    const point = axisAnglePoint(quaternion);
    const key = orientationKey(quaternion);
    const color = visualEffect === "turn-generation"
      ? turnGenerationColor(orientationTurnGenerations.get(key))
      : mutedOrientationKeys.has(key)
        ? new THREE.Color(0xb8bfbc)
        : orientationColorFromQuaternion(quaternion);
    orientationPointKeys.push(key);
    orientationPointBaseColors.push(color);
    positions.push(point.x, point.y, point.z);
    colors.push(color.r, color.g, color.b);
    pointSizes.push(Math.max(
      2.5,
      maximumPointSize * Math.sqrt(orientationCounts.get(key) / maximumOrientationCount)
    ));
  }
  orientationPointGeometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  orientationPointGeometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  orientationPointGeometry.setAttribute("pointSize", new THREE.Float32BufferAttribute(pointSizes, 1));
  orientationPointGeometry.computeBoundingSphere();
  const selectedIndex = orientationPointKeys.indexOf(selectedOrientationKey);
  orientationSelectionMarker.visible = selectedIndex >= 0;
  if (selectedIndex >= 0) {
    orientationSelectionMarker.position.fromArray(positions, selectedIndex * 3);
    orientationCurrent.textContent = "One orientation is highlighted in the tiling. Click it again to clear.";
  } else if (selectedOrientationKey !== null) {
    selectedOrientationKey = null;
    refreshVisualColors(currentVisual);
  }
  refreshOrientationPointColors();
  updateSelectedOrientationMatrix();
  drawOrientationGenerationGraph();
}

function physicalRotationRows(matrix) {
  const position = new THREE.Vector3();
  const quaternion = new THREE.Quaternion();
  const scale = new THREE.Vector3();
  matrix.decompose(position, quaternion, scale);
  const elements = new THREE.Matrix4().makeRotationFromQuaternion(quaternion.normalize()).elements;
  return [
    [elements[0], elements[4], elements[8]],
    [elements[1], elements[5], elements[9]],
    [elements[2], elements[6], elements[10]]
  ];
}

function updateSelectedOrientationMatrix() {
  const representative = orientationRepresentatives.get(selectedOrientationKey);
  const exact = representative ? exactDyadicSO3(physicalRotationRows(representative)) : null;
  const visible = Boolean(exact);
  orientationMatrix.hidden = !visible;
  orientationPanel.classList.toggle("has-selection", visible);
  if (!visible) return;

  matrixFactor.textContent = exact.denominator === 1 ? "" : `1/${exact.denominator}`;
  matrixValues.replaceChildren(...exact.numerators.flatMap(row => row.map(value => {
    const cell = document.createElement("span");
    cell.textContent = String(value);
    return cell;
  })));
  const factorLabel = exact.denominator === 1 ? "" : `one over ${exact.denominator} times `;
  orientationMatrix.setAttribute(
    "aria-label",
    `Selected element of SO q over the dyadic integers: ${factorLabel}${exact.numerators.map(row => row.join(", ")).join("; ")}`
  );
}

function refreshOrientationPointColors() {
  const colors = orientationPointGeometry.getAttribute("color");
  if (!colors) return;
  for (let index = 0; index < orientationPointKeys.length; index += 1) {
    const color = orientationPointBaseColors[index];
    colors.setXYZ(index, color.r, color.g, color.b);
  }
  colors.needsUpdate = true;
}

function displayedTileColor(matrix, turnGeneration) {
  const color = orientationColor(matrix);
  const key = orientationKey(canonicalQuaternion(matrix));
  if (visualEffect === "turn-generation") {
    if (selectedOrientationKey !== null && key !== selectedOrientationKey) return new THREE.Color(0xb8bfbc);
    if (turnGeneration === null) {
      return new THREE.Color(selectedOrientationKey === key ? 0x8f9895 : 0xb8bfbc);
    }
    const generationColor = turnGenerationColor(turnGeneration);
    return selectedOrientationKey === key ? generationColor.offsetHSL(0, 0.08, 0.08) : generationColor;
  }
  if (mutedOrientationKeys.has(key)) {
    return new THREE.Color(selectedOrientationKey === key ? 0x8f9895 : 0xb8bfbc);
  }
  if (selectedOrientationKey === null) return color;
  if (key === selectedOrientationKey) return color.offsetHSL(0, 0.1, 0.08);
  return new THREE.Color(0xb8bfbc);
}

function makeTransparentMaterial({ line = false, opacity } = {}) {
  if (line) {
    const material = new THREE.LineBasicMaterial({
      color: 0xffffff,
      vertexColors: true,
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

function makeVisual(transforms, turnGenerations) {
  const facePositions = [];
  const faceColors = [];
  const edgePositions = [];
  const edgeColors = [];
  const transformed = CANONICAL_VERTICES.map(() => new THREE.Vector3());

  transforms.forEach((matrix, transformIndex) => {
    const color = displayedTileColor(matrix, turnGenerations[transformIndex]);
    for (let i = 0; i < CANONICAL_VERTICES.length; i += 1) {
      transformed[i].copy(CANONICAL_VERTICES[i]).applyMatrix4(matrix);
    }
    for (const index of FACE_INDICES) {
      const point = transformed[index];
      facePositions.push(point.x, point.y, point.z);
      faceColors.push(color.r, color.g, color.b, 1);
    }
    for (const index of EDGE_INDICES) {
      const point = transformed[index];
      edgePositions.push(point.x, point.y, point.z);
      edgeColors.push(color.r, color.g, color.b, 1);
    }
  });

  const faceOpacity = Math.max(0.006, 0.09 / Math.pow(transforms.length, 0.28));
  const edgeOpacity = Math.max(0.01, 0.16 / Math.pow(transforms.length, 0.25));
  const faceGeometry = new THREE.BufferGeometry();
  faceGeometry.setAttribute("position", new THREE.Float32BufferAttribute(facePositions, 3));
  faceGeometry.setAttribute("color", new THREE.Float32BufferAttribute(faceColors, 4));
  faceGeometry.computeVertexNormals();
  const faceMaterial = makeTransparentMaterial({ opacity: faceOpacity });
  const mesh = new THREE.Mesh(faceGeometry, faceMaterial);
  mesh.renderOrder = 1;

  const edgeGeometry = new THREE.BufferGeometry();
  edgeGeometry.setAttribute("position", new THREE.Float32BufferAttribute(edgePositions, 3));
  edgeGeometry.setAttribute("color", new THREE.Float32BufferAttribute(edgeColors, 4));
  const edgeMaterial = makeTransparentMaterial({ line: true, opacity: edgeOpacity });
  const edges = new THREE.LineSegments(edgeGeometry, edgeMaterial);
  edges.renderOrder = 2;

  const group = new THREE.Group();
  group.add(mesh, edges);
  return { group, transforms, turnGenerations, materials: [faceMaterial, edgeMaterial], geometries: [faceGeometry, edgeGeometry] };
}

function refreshVisualColors(visual) {
  if (!visual) return;
  const faceColors = visual.geometries[0].getAttribute("color");
  const edgeColors = visual.geometries[1].getAttribute("color");
  let faceOffset = 0;
  let edgeOffset = 0;
  visual.transforms.forEach((matrix, transformIndex) => {
    const color = displayedTileColor(matrix, visual.turnGenerations[transformIndex]);
    const matches = selectedOrientationKey !== null
      && orientationKey(canonicalQuaternion(matrix)) === selectedOrientationKey;
    const faceAlpha = selectedOrientationKey === null
      ? 1
      : matches ? 1 : Math.max(0.004, visual.materials[0].userData.baseOpacity * 0.35);
    const edgeAlpha = selectedOrientationKey === null
      ? 1
      : matches ? 1 : Math.max(0.008, visual.materials[1].userData.baseOpacity * 0.28);
    for (let index = 0; index < FACE_INDICES.length; index += 1) {
      faceColors.setXYZW(faceOffset++, color.r, color.g, color.b, faceAlpha);
    }
    for (let index = 0; index < EDGE_INDICES.length; index += 1) {
      edgeColors.setXYZW(edgeOffset++, color.r, color.g, color.b, edgeAlpha);
    }
  });
  faceColors.needsUpdate = true;
  edgeColors.needsUpdate = true;
  refreshVisualEmphasis(visual);
}

function refreshVisualEmphasis(visual) {
  if (!visual) return;
  for (const material of visual.materials) {
    const targetOpacity = selectedOrientationKey === null ? material.userData.baseOpacity : 1;
    material.opacity = targetOpacity * (material.userData.transitionAmount ?? 1);
  }
}

function selectOrientation(key) {
  selectedOrientationKey = selectedOrientationKey === key ? null : key;
  refreshOrientationPointColors();
  refreshVisualColors(currentVisual);
  if (transition) {
    refreshVisualColors(transition.from);
    refreshVisualColors(transition.to);
  }
  const selectedIndex = orientationPointKeys.indexOf(selectedOrientationKey);
  orientationSelectionMarker.visible = selectedIndex >= 0;
  if (selectedIndex >= 0) {
    orientationSelectionMarker.position.fromBufferAttribute(
      orientationPointGeometry.getAttribute("position"),
      selectedIndex
    );
  }
  orientationCurrent.textContent = selectedOrientationKey === null
    ? `${orientationPointKeys.length.toLocaleString()} ${orientationPointKeys.length === 1 ? "occurs" : "occur"} in the current patch.`
    : "One orientation is highlighted in the tiling; its generation edges are emphasized. Click it again to clear.";
  updateSelectedOrientationMatrix();
  drawOrientationGenerationGraph();
}

const orientationRaycaster = new THREE.Raycaster();
orientationRaycaster.params.Points.threshold = 0.1;
let orientationPointerStart = null;
orientationRenderer.domElement.addEventListener("pointerdown", (event) => {
  orientationPointerStart = { x: event.clientX, y: event.clientY };
});
orientationRenderer.domElement.addEventListener("pointerup", (event) => {
  if (!orientationPointerStart) return;
  const distance = Math.hypot(event.clientX - orientationPointerStart.x, event.clientY - orientationPointerStart.y);
  orientationPointerStart = null;
  if (distance > 5) return;
  const rect = orientationRenderer.domElement.getBoundingClientRect();
  const pointer = new THREE.Vector2(
    ((event.clientX - rect.left) / rect.width) * 2 - 1,
    -((event.clientY - rect.top) / rect.height) * 2 + 1
  );
  orientationRaycaster.setFromCamera(pointer, orientationCamera);
  const hit = orientationRaycaster.intersectObject(orientationPoints, false)[0];
  if (hit && Number.isInteger(hit.index)) selectOrientation(orientationPointKeys[hit.index]);
  else if (selectedOrientationKey !== null) selectOrientation(null);
});
orientationPlot.addEventListener("keydown", (event) => {
  if (!["ArrowRight", "ArrowLeft", "Home", "Escape"].includes(event.key)) return;
  event.preventDefault();
  if (event.key === "Escape") {
    if (selectedOrientationKey !== null) selectOrientation(null);
    return;
  }
  let selectedIndex = orientationPointKeys.indexOf(selectedOrientationKey);
  if (event.key === "Home") selectedIndex = 0;
  else if (event.key === "ArrowRight") selectedIndex = (selectedIndex + 1 + orientationPointKeys.length) % orientationPointKeys.length;
  else selectedIndex = (selectedIndex - 1 + orientationPointKeys.length) % orientationPointKeys.length;
  selectOrientation(orientationPointKeys[selectedIndex]);
});

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
    material.userData.transitionAmount = amount;
  }
  refreshVisualEmphasis(visual);
}

function stateAtGeneration(targetGeneration) {
  let words = [new THREE.Matrix4()];
  let turnGenerations = [null];
  const path = new THREE.Matrix4();
  const depthLimit = targetGeneration;
  for (let depth = 0; depth < depthLimit; depth += 1) {
    words = substitute(words);
    turnGenerations = substituteTurnGenerations(turnGenerations, depth + 1);
    path.multiply(daughterTransforms[FIXED_CHILD_SEQUENCE[depth]]);
  }
  const normalization = path.clone().invert();
  return {
    words,
    path,
    transforms: words.map((word) => normalization.clone().multiply(word)),
    turnGenerations
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
  currentTurnGenerations = nextState.turnGenerations;
  updateMutedOrientationKeys(expandedTransforms);
  const nextVisual = makeVisual(expandedTransforms, currentTurnGenerations);
  setVisualOpacity(nextVisual, 0);
  content.add(nextVisual.group);

  generation = targetGeneration;
  subdivisionWords = nextState.words;
  fixedPath = nextState.path;
  generationValue.textContent = String(generation);
  tileValue.textContent = subdivisionWords.length.toLocaleString();
  drawOrientationBall(expandedTransforms, currentTurnGenerations);
  refreshVisualColors(nextVisual);

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
visualEffectSelect.addEventListener("change", () => {
  visualEffect = visualEffectSelect.value;
  effectDescription.textContent = visualEffect === "turn-generation"
    ? "Grey means not yet turned; color records the first turning expansion."
    : "Dominant classes are grey; the proliferating orbit is colored.";
  refreshVisualColors(currentVisual);
  if (transition) {
    refreshVisualColors(transition.from);
    refreshVisualColors(transition.to);
  }
  drawOrientationBall(currentExpandedTransforms, currentTurnGenerations);
});
updateActionButtons();

function resize() {
  const width = Math.max(1, viewport.clientWidth);
  const height = Math.max(1, viewport.clientHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

function resizeOrientationBall() {
  const size = Math.max(1, Math.round(orientationPlot.clientWidth));
  orientationRenderer.setSize(size, size, false);
  orientationCamera.aspect = 1;
  orientationCamera.updateProjectionMatrix();
}

const resizeObserver = new ResizeObserver(resize);
resizeObserver.observe(viewport);
const orientationResizeObserver = new ResizeObserver(resizeOrientationBall);
orientationResizeObserver.observe(orientationPlot);
resize();
resizeOrientationBall();
drawOrientationBall(currentExpandedTransforms, currentTurnGenerations);

let previousAnimationTime = null;

function animate(time) {
  const elapsedSeconds = previousAnimationTime === null
    ? 0
    : Math.min(0.05, (time - previousAnimationTime) / 1000);
  previousAnimationTime = time;
  controls.update();
  if (orbitDriftActive && orbitDrag === null && transition === null && elapsedSeconds > 0) {
    orbitPreviousOffset.copy(camera.position).sub(controls.target);
    orbitDriftQuaternion.setFromAxisAngle(orbitDriftAxis, ORBIT_DRIFT_SPEED * elapsedSeconds);
    orbitPreviousOffset.applyQuaternion(orbitDriftQuaternion);
    camera.position.copy(controls.target).add(orbitPreviousOffset);
    camera.lookAt(controls.target);
  }
  orientationControls.update();
  orientationBoundary.quaternion.copy(orientationCamera.quaternion);
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
  orientationRenderer.render(orientationScene, orientationCamera);
  requestAnimationFrame(animate);
}

requestAnimationFrame(animate);
