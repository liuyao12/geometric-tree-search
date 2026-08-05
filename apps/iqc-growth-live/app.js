import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const $ = (id) => document.getElementById(id);
const viewport = $("viewport");
const scenarioSelect = $("scenarioSelect");
const confinementSelect = $("confinementSelect");
const policySelect = $("policySelect");
const playButton = $("playButton");
const playIcon = $("playIcon");
const playLabel = $("playLabel");
const stepButton = $("stepButton");
const resetButton = $("resetButton");
const speedInput = $("speedInput");
const speedOutput = $("speedOutput");
const backtrackInput = $("backtrackInput");
const backtrackOutput = $("backtrackOutput");
const markingToggle = $("markingToggle");
const bondToggle = $("bondToggle");
const frontierToggle = $("frontierToggle");
const rotateToggle = $("rotateToggle");
const runStateDot = $("runStateDot");
const runStateText = $("runStateText");
const eventKind = $("eventKind");
const eventCounter = $("eventCounter");
const phaseReadout = $("phaseReadout");
const rollbackFlash = $("rollbackFlash");
const rollbackCount = $("rollbackCount");
const captionAction = $("captionAction");
const timeline = $("timeline");
const timelineLabel = $("timelineLabel");
const atomMetric = $("atomMetric");
const atomDelta = $("atomDelta");
const frontierMetric = $("frontierMetric");
const oracleMetric = $("oracleMetric");
const oracleDelta = $("oracleDelta");
const reuseMetric = $("reuseMetric");
const reuseDelta = $("reuseDelta");
const decisionBadge = $("decisionBadge");
const decisionTitle = $("decisionTitle");
const decisionCopy = $("decisionCopy");
const actionValue = $("actionValue");
const domainValue = $("domainValue");
const energyValue = $("energyValue");
const resolverValue = $("resolverValue");
const stackDepth = $("stackDepth");
const searchStack = $("searchStack");
const markCount = $("markCount");
const markingTable = $("markingTable");

const COLORS = {
  blue: 0x55c8ff,
  green: 0xf0c96a,
  mint: 0x65e1bc,
  violet: 0xb594ff,
  red: 0xff6d71,
  ink: 0xdce9e5,
  line: 0x45635c,
};

const scene = new THREE.Scene();
scene.background = null;
scene.fog = new THREE.FogExp2(0x061011, 0.025);

const camera = new THREE.PerspectiveCamera(46, 1, 0.1, 100);
camera.position.set(12.5, 9.5, 13.5);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
viewport.prepend(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.38;
controls.minDistance = 5;
controls.maxDistance = 34;

scene.add(new THREE.HemisphereLight(0xb9fff0, 0x091011, 1.25));
const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
keyLight.position.set(8, 13, 9);
scene.add(keyLight);
const rimLight = new THREE.PointLight(0x55c8ff, 24, 28, 2);
rimLight.position.set(-8, 4, -7);
scene.add(rimLight);

const world = new THREE.Group();
const confinementGroup = new THREE.Group();
const atomGroup = new THREE.Group();
const bondGroup = new THREE.Group();
const frontierGroup = new THREE.Group();
const decisionGroup = new THREE.Group();
const rollbackGroup = new THREE.Group();
world.add(confinementGroup, bondGroup, atomGroup, frontierGroup, decisionGroup, rollbackGroup);
scene.add(world);

const sphereGeometry = new THREE.SphereGeometry(0.22, 16, 12);
const candidateGeometry = new THREE.SphereGeometry(0.27, 14, 10);
const rollbackGeometry = new THREE.SphereGeometry(0.26, 13, 9);
const blueMaterial = new THREE.MeshStandardMaterial({ color: COLORS.blue, roughness: 0.28, metalness: 0.18, emissive: 0x0b526d, emissiveIntensity: 0.32 });
const greenMaterial = new THREE.MeshStandardMaterial({ color: COLORS.green, roughness: 0.34, metalness: 0.12, emissive: 0x59450c, emissiveIntensity: 0.27 });
const candidateMaterial = new THREE.MeshBasicMaterial({ color: COLORS.violet, wireframe: true, transparent: true, opacity: 0.9 });
const rejectedMaterial = new THREE.MeshBasicMaterial({ color: COLORS.red, wireframe: true, transparent: true, opacity: 0.92 });

const TAU = Math.PI * 2;
const PHI = (1 + Math.sqrt(5)) / 2;
const PATCH_DISTANCE = 1.12;
const TEMPERATURE = 0.09;
const INSERTION_PENALTY = 0.35;
const MAX_ATOMS = 260;
const MAX_HISTORY = 54;

const tetraDirections = [
  new THREE.Vector3(1, 1, 1),
  new THREE.Vector3(1, -1, -1),
  new THREE.Vector3(-1, 1, -1),
  new THREE.Vector3(-1, -1, 1),
].map((v) => v.normalize());

const icoDirections = [
  [0, 1, PHI], [0, -1, PHI], [0, 1, -PHI], [0, -1, -PHI],
  [1, PHI, 0], [-1, PHI, 0], [1, -PHI, 0], [-1, -PHI, 0],
  [PHI, 0, 1], [PHI, 0, -1], [-PHI, 0, 1], [-PHI, 0, -1],
].map((v) => new THREE.Vector3(...v).normalize());

let atoms = [];
let seedCount = 0;
let playing = false;
let eventIndex = 0;
let oracleCalls = 0;
let grammarDecisions = 0;
let acceptedDecisions = 0;
let rejectedDecisions = 0;
let eventHistory = [];
let stackHistory = [];
let markingCache = new Map();
let actionCache = new Map();
let rollbackParticles = [];
let currentCandidate = null;
let conflictStreak = 0;
let lastFrame = performance.now();
let eventAccumulator = 0;
let flashUntil = 0;
let nextAtomId = 1;
let rngState = 0x8f23ab17;

function random() {
  rngState ^= rngState << 13;
  rngState ^= rngState >>> 17;
  rngState ^= rngState << 5;
  return (rngState >>> 0) / 4294967296;
}

function randomUnit() {
  const z = random() * 2 - 1;
  const angle = random() * TAU;
  const radius = Math.sqrt(Math.max(0, 1 - z * z));
  return new THREE.Vector3(radius * Math.cos(angle), z, radius * Math.sin(angle));
}

function addAtom(position, species, seed = false, family = "growth", parent = null) {
  atoms.push({
    id: nextAtomId++,
    p: position.clone(),
    species,
    seed,
    family,
    parent,
    depth: parent ? parent.depth + 1 : 0,
    attempts: 0,
  });
}

function dodecahedronSeed(center, count = 20, family = "IQC") {
  const raw = [];
  for (const x of [-1, 1]) for (const y of [-1, 1]) for (const z of [-1, 1]) raw.push([x, y, z]);
  for (const a of [-1, 1]) for (const b of [-1, 1]) {
    raw.push([0, a / PHI, b * PHI], [a / PHI, b * PHI, 0], [a * PHI, 0, b / PHI]);
  }
  raw.slice(0, count).forEach((v) => addAtom(new THREE.Vector3(...v).multiplyScalar(0.87).add(center), "G", true, family));
}

function bc8Seed(center, count = 20, family = "BC8") {
  const queue = [{ p: center.clone(), depth: 0, parent: null }];
  const positions = [];
  while (queue.length && positions.length < count) {
    const item = queue.shift();
    if (positions.some((p) => p.distanceTo(item.p) < 0.62)) continue;
    positions.push(item.p);
    if (item.depth < 3) {
      const parity = item.depth % 2 ? -1 : 1;
      tetraDirections.forEach((direction) => queue.push({
        p: item.p.clone().addScaledVector(direction, PATCH_DISTANCE * parity),
        depth: item.depth + 1,
      }));
    }
  }
  positions.forEach((p) => addAtom(p, "B", true, family));
}

function randomSeed(center, count = 20, radius = 1.8, family = "glass") {
  let guard = 0;
  while (count > 0 && guard++ < 4000) {
    const p = randomUnit().multiplyScalar(radius * Math.cbrt(random())).add(center);
    if (atoms.some((atom) => atom.p.distanceTo(p) < 0.68)) continue;
    addAtom(p, random() < 0.57 ? "B" : "G", true, family);
    count--;
  }
}

function resetSimulation() {
  playing = false;
  eventIndex = 0;
  oracleCalls = 0;
  grammarDecisions = 0;
  acceptedDecisions = 0;
  rejectedDecisions = 0;
  eventHistory = [];
  stackHistory = [];
  markingCache = new Map();
  actionCache = new Map();
  rollbackParticles = [];
  currentCandidate = null;
  conflictStreak = 0;
  nextAtomId = 1;
  rngState = 0x8f23ab17 ^ scenarioSelect.selectedIndex * 0x91e10da5 ^ confinementSelect.selectedIndex * 0x734a9d;
  atoms = [];

  if (scenarioSelect.value === "competition") {
    bc8Seed(new THREE.Vector3(-4.2, 0, 0), 16, "BC8");
    dodecahedronSeed(new THREE.Vector3(0, 0, 0), 18, "IQC");
    randomSeed(new THREE.Vector3(4.2, 0, 0), 16, 1.55, "glass");
  } else if (scenarioSelect.value === "random") {
    randomSeed(new THREE.Vector3(), 36, 3.2, "fluid");
  } else if (scenarioSelect.value === "iqc") {
    dodecahedronSeed(new THREE.Vector3(), 20, "IQC");
  } else {
    bc8Seed(new THREE.Vector3(), 20, "BC8");
  }
  seedCount = atoms.length;
  buildConfinement();
  rebuildWorld();
  setDecisionWaiting();
  updateUI();
  setPlaying(false);
}

function clearGroup(group) {
  while (group.children.length) {
    const child = group.children.pop();
    if (![sphereGeometry, candidateGeometry, rollbackGeometry].includes(child.geometry)) child.geometry?.dispose?.();
    if (Array.isArray(child.material)) child.material.forEach((material) => material.dispose?.());
    else if (![blueMaterial, greenMaterial, candidateMaterial, rejectedMaterial].includes(child.material)) child.material?.dispose?.();
  }
}

function buildConfinement() {
  clearGroup(confinementGroup);
  const material = new THREE.LineBasicMaterial({ color: COLORS.line, transparent: true, opacity: 0.42 });
  const shape = confinementSelect.value;
  if (shape === "box") {
    confinementGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(16, 11, 11)), material));
  } else if (shape === "sphere") {
    confinementGroup.add(new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.SphereGeometry(6.4, 18, 12)), material));
  } else if (shape === "cylinder") {
    confinementGroup.add(new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.CylinderGeometry(5.3, 5.3, 14, 20, 4, true)), material));
    confinementGroup.rotation.z = Math.PI / 2;
  } else {
    const points = [];
    for (let ring = 0; ring <= 14; ring++) {
      const x = -7 + ring;
      const radius = 1.8 + 0.48 * Math.abs(x);
      for (let segment = 0; segment < 20; segment++) {
        const a = segment / 20 * TAU;
        const b = (segment + 1) / 20 * TAU;
        points.push(new THREE.Vector3(x, Math.cos(a) * radius, Math.sin(a) * radius));
        points.push(new THREE.Vector3(x, Math.cos(b) * radius, Math.sin(b) * radius));
      }
    }
    for (let segment = 0; segment < 12; segment++) {
      const a = segment / 12 * TAU;
      for (let ring = 0; ring < 14; ring++) {
        const x1 = -7 + ring;
        const x2 = x1 + 1;
        const r1 = 1.8 + 0.48 * Math.abs(x1);
        const r2 = 1.8 + 0.48 * Math.abs(x2);
        points.push(new THREE.Vector3(x1, Math.cos(a) * r1, Math.sin(a) * r1));
        points.push(new THREE.Vector3(x2, Math.cos(a) * r2, Math.sin(a) * r2));
      }
    }
    confinementGroup.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(points), material));
  }
}

function insideConfinement(p, margin = 0.25) {
  const x = p.x / (8 - margin);
  const y = p.y / (5.5 - margin);
  const z = p.z / (5.5 - margin);
  if (confinementSelect.value === "box") return Math.max(Math.abs(x), Math.abs(y), Math.abs(z)) <= 1;
  if (confinementSelect.value === "sphere") return (p.x / 6.4) ** 2 + (p.y / 6.4) ** 2 + (p.z / 6.4) ** 2 <= 1;
  if (confinementSelect.value === "cylinder") return Math.abs(p.x) <= 7 && (p.y / 5.3) ** 2 + (p.z / 5.3) ** 2 <= 1;
  return Math.abs(p.x) <= 7 && Math.hypot(p.y, p.z) <= 1.8 + 0.48 * Math.abs(p.x);
}

function boundaryClearance(p) {
  if (!insideConfinement(p)) return -1;
  if (confinementSelect.value === "box") return Math.min(8 - Math.abs(p.x), 5.5 - Math.abs(p.y), 5.5 - Math.abs(p.z));
  if (confinementSelect.value === "sphere") return 6.4 - p.length();
  if (confinementSelect.value === "cylinder") return Math.min(7 - Math.abs(p.x), 5.3 - Math.hypot(p.y, p.z));
  return Math.min(7 - Math.abs(p.x), 1.8 + 0.48 * Math.abs(p.x) - Math.hypot(p.y, p.z));
}

function proposalDirection(parent) {
  const library = parent.family === "BC8" || scenarioSelect.value === "bc8" ? tetraDirections : icoDirections;
  const direction = library[Math.floor(random() * library.length)].clone();
  const twist = new THREE.Quaternion().setFromAxisAngle(randomUnit(), (random() - 0.5) * 0.22);
  return direction.applyQuaternion(twist).normalize();
}

function childSpecies(parent) {
  if (scenarioSelect.value === "bc8") return "B";
  if (parent.family === "BC8" && random() < 0.72) return "B";
  if (parent.family === "IQC" && random() < 0.64) return "G";
  return random() < 0.57 ? "B" : "G";
}

function shiftedLJ(distance) {
  if (distance >= 2.5) return 0;
  const inv6 = 1 / distance ** 6;
  const cut6 = 1 / 2.5 ** 6;
  return 4 * (inv6 * inv6 - inv6 - cut6 * cut6 + cut6);
}

function evaluateExact(parent, candidate, distances) {
  let energy = 0;
  distances.forEach((distance, index) => {
    if (distance >= 2.5) return;
    const radial = shiftedLJ(Math.max(0.5, distance));
    if (radial > 0) energy += radial;
    else {
      const sameSpecies = atoms[index].species === candidate.species;
      const parentBond = atoms[index].id === parent.id;
      const modulation = parentBond ? (sameSpecies ? 1 : 1.15) : (sameSpecies ? 0.34 : 0.42);
      energy += radial * modulation;
    }
  });
  return energy + INSERTION_PENALTY;
}

function finiteState(parent, candidate, distances) {
  const n15 = distances.filter((distance) => distance < 1.5).length;
  const n25 = distances.filter((distance) => distance < 2.5).length;
  const minimum = Math.min(...distances);
  const clearance = boundaryClearance(candidate.p);
  const action = `${parent.species}→${candidate.species}`;
  const domain = `${action}|n${Math.min(4, n15)}/${Math.min(7, n25)}|r${Math.max(0, Math.min(15, Math.floor((minimum - .75) / .05)))}|b${Math.max(0, Math.min(7, Math.floor(clearance / .8)))}`;
  return { action, domain, n15, n25, minimum, clearance };
}

function cacheObservation(cache, key, energy) {
  const state = cache.get(key) || { count: 0, min: Infinity, max: -Infinity, sum: 0 };
  state.count++;
  state.min = Math.min(state.min, energy);
  state.max = Math.max(state.max, energy);
  state.sum += energy;
  cache.set(key, state);
  return state;
}

function resolvedByGrammar(cache, key, threshold) {
  const state = cache.get(key);
  if (!state || state.count < 2) return null;
  const low = state.min - 0.12;
  const high = state.max + 0.12;
  if (high < threshold) return { accepted: true, state, low, high };
  if (low > threshold) return { accepted: false, state, low, high };
  return null;
}

function chooseParent() {
  const candidates = atoms.filter((atom) => atom.attempts < 8);
  const source = candidates.length ? candidates : atoms;
  const recentBias = random() < 0.58 && source.length > 12;
  if (recentBias) return source[Math.max(0, source.length - 1 - Math.floor(random() * Math.min(14, source.length)))];
  return source[Math.floor(random() * source.length)];
}

function performEvent() {
  if (!atoms.length) return;
  if (atoms.length >= MAX_ATOMS) {
    setPlaying(false);
    captionAction.textContent = "Growth ceiling reached. Reset to run another search.";
    return;
  }
  eventIndex++;
  const parent = chooseParent();
  parent.attempts++;
  const direction = proposalDirection(parent);
  const candidate = {
    p: parent.p.clone().addScaledVector(direction, PATCH_DISTANCE + (random() - .5) * .08),
    species: childSpecies(parent),
    family: parent.family,
    parent,
  };
  const distances = atoms.map((atom) => atom.p.distanceTo(candidate.p));
  const state = finiteState(parent, candidate, distances);
  const threshold = -TEMPERATURE * Math.log(Math.max(1e-8, random()));
  const overlap = state.minimum < 0.76;
  const outside = state.clearance < 0;
  let energy = Infinity;
  let accepted = false;
  let resolver = "geometry";
  let eventType = "reject";
  let interval = null;

  if (!overlap && !outside) {
    const cache = policySelect.value === "marked" ? markingCache : actionCache;
    const key = policySelect.value === "marked" ? state.domain : state.action;
    const reusable = policySelect.value === "direct" ? null : resolvedByGrammar(cache, key, threshold);
    if (reusable) {
      accepted = reusable.accepted;
      interval = [reusable.low, reusable.high];
      energy = reusable.state.sum / reusable.state.count;
      resolver = policySelect.value === "marked" ? "finite marking" : "colored action";
      grammarDecisions++;
      eventType = "reuse";
    } else {
      energy = evaluateExact(parent, candidate, distances);
      oracleCalls += atoms.length;
      accepted = energy <= threshold;
      resolver = "exact local oracle";
      const observed = cacheObservation(cache, key, energy);
      interval = [observed.min, observed.max];
      eventType = accepted ? "accept" : "reject";
    }
  }

  if (overlap) {
    resolver = "hard-core geometry";
    energy = 99;
  } else if (outside) {
    resolver = "confinement";
    energy = 99;
  }

  currentCandidate = { ...candidate, accepted, rejected: !accepted, state, resolver };
  if (accepted) {
    addAtom(candidate.p, candidate.species, false, candidate.family, parent);
    acceptedDecisions++;
    conflictStreak = 0;
    const added = atoms.at(-1);
    stackHistory.push({ type: "accept", id: added.id, depth: added.depth, action: state.action, family: added.family });
    captionAction.textContent = `${state.action} accepted at depth ${added.depth}; ${resolver}.`;
  } else {
    rejectedDecisions++;
    conflictStreak++;
    stackHistory.push({ type: "reject", id: parent.id, depth: parent.depth + 1, action: state.action, family: parent.family });
    captionAction.textContent = `${state.action} rejected: ${overlap ? "hard-core overlap" : outside ? "outside confinement" : "energy interval missed the Metropolis threshold"}.`;
  }

  const conflictPressure = Number(backtrackInput.value) / 100;
  const shouldBacktrack = !accepted && atoms.length > seedCount + 3 && (conflictStreak >= 3 || random() < conflictPressure * 0.18);
  let removed = [];
  if (shouldBacktrack) {
    const count = Math.min(atoms.length - seedCount, 1 + Math.floor(random() * (1 + conflictPressure * 5)));
    removed = atoms.splice(atoms.length - count, count);
    removed.forEach((atom) => rollbackParticles.push({ p: atom.p.clone(), species: atom.species, expires: performance.now() + 650 }));
    stackHistory.push({ type: "backtrack", id: removed[0]?.id || 0, depth: removed[0]?.depth || 0, action: `−${removed.length} atoms`, family: removed[0]?.family || "branch" });
    conflictStreak = 0;
    flashUntil = performance.now() + 520;
    rollbackCount.textContent = `−${removed.length}`;
    eventType = "backtrack";
    captionAction.textContent = `Conflict closed the branch; rolled back ${removed.length} speculative atom${removed.length === 1 ? "" : "s"}.`;
  }

  eventHistory.push({ type: eventType, accepted, state, resolver, energy, interval, removed: removed.length });
  if (eventHistory.length > MAX_HISTORY) eventHistory.shift();
  if (stackHistory.length > 24) stackHistory.shift();
  rebuildWorld();
  updateDecision({ eventType, accepted, state, resolver, energy, interval, threshold, overlap, outside, removed: removed.length });
  updateUI();
}

function rebuildWorld() {
  clearGroup(atomGroup);
  clearGroup(bondGroup);
  clearGroup(frontierGroup);
  clearGroup(decisionGroup);

  const blueAtoms = atoms.filter((atom) => atom.species === "B");
  const greenAtoms = atoms.filter((atom) => atom.species === "G");
  const dummy = new THREE.Object3D();
  const addInstances = (source, material) => {
    if (!source.length) return;
    const mesh = new THREE.InstancedMesh(sphereGeometry, material, source.length);
    source.forEach((atom, index) => {
      const scale = atom.seed ? 1.06 : 0.93;
      dummy.position.copy(atom.p);
      dummy.scale.setScalar(scale);
      dummy.updateMatrix();
      mesh.setMatrixAt(index, dummy.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
    atomGroup.add(mesh);
  };
  addInstances(blueAtoms, blueMaterial);
  addInstances(greenAtoms, greenMaterial);

  if (bondToggle.checked) {
    const points = [];
    for (let i = 0; i < atoms.length; i++) {
      for (let j = i + 1; j < atoms.length; j++) {
        if (atoms[i].p.distanceToSquared(atoms[j].p) < 1.48 ** 2) points.push(atoms[i].p, atoms[j].p);
      }
    }
    if (points.length) {
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      bondGroup.add(new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({ color: 0x87afa5, transparent: true, opacity: 0.24 })));
    }
  }

  if (frontierToggle.checked && atoms.length) {
    const frontier = [];
    const source = atoms.slice(Math.max(0, atoms.length - 22));
    for (let i = 0; i < Math.min(36, source.length * 2); i++) {
      const parent = source[i % source.length];
      const p = parent.p.clone().addScaledVector(proposalDirection(parent), PATCH_DISTANCE);
      if (insideConfinement(p) && atoms.every((atom) => atom.p.distanceToSquared(p) > .72 ** 2)) frontier.push(p);
    }
    if (frontier.length) {
      const geometry = new THREE.BufferGeometry().setFromPoints(frontier);
      const material = new THREE.PointsMaterial({ color: COLORS.mint, size: 0.075, transparent: true, opacity: 0.55, sizeAttenuation: true });
      frontierGroup.add(new THREE.Points(geometry, material));
      frontierMetric.textContent = String(frontier.length);
    } else frontierMetric.textContent = "0";
  } else frontierMetric.textContent = "—";

  if (currentCandidate) {
    const mesh = new THREE.Mesh(candidateGeometry, currentCandidate.accepted ? candidateMaterial : rejectedMaterial);
    mesh.position.copy(currentCandidate.p);
    decisionGroup.add(mesh);
    if (markingToggle.checked) {
      const domain = new THREE.Mesh(
        new THREE.SphereGeometry(2.5, 18, 10),
        new THREE.MeshBasicMaterial({ color: COLORS.violet, wireframe: true, transparent: true, opacity: 0.09 }),
      );
      domain.position.copy(currentCandidate.p);
      decisionGroup.add(domain);
    }
  }
}

function updateRollback(now) {
  rollbackParticles = rollbackParticles.filter((particle) => particle.expires > now);
  clearGroup(rollbackGroup);
  rollbackParticles.forEach((particle) => {
    const remaining = Math.max(0, (particle.expires - now) / 650);
    const material = new THREE.MeshBasicMaterial({ color: COLORS.red, wireframe: true, transparent: true, opacity: remaining * .85 });
    const mesh = new THREE.Mesh(rollbackGeometry, material);
    mesh.position.copy(particle.p);
    mesh.scale.setScalar(1 + (1 - remaining) * 1.7);
    rollbackGroup.add(mesh);
  });
  rollbackFlash.classList.toggle("visible", now < flashUntil);
}

function updateDecision(event) {
  const isBacktrack = event.eventType === "backtrack";
  const isReuse = event.eventType === "reuse";
  decisionBadge.className = `badge ${isBacktrack ? "backtrack" : isReuse ? "reuse" : event.accepted ? "accept" : "reject"}`;
  decisionBadge.textContent = isBacktrack ? "rollback" : isReuse ? "reused" : event.accepted ? "accepted" : "rejected";
  decisionTitle.textContent = isBacktrack ? `Branch shortened by ${event.removed}` : `${event.state.action} insertion ${event.accepted ? "survives" : "fails"}`;
  if (isBacktrack) decisionCopy.textContent = "Repeated local conflicts exhausted this speculative branch. The accepted prefix remains and the search resumes from an earlier frontier.";
  else if (isReuse) decisionCopy.textContent = "The complete calibrated interval for this finite domain lies on one side of the stochastic acceptance threshold, so no exact energy evaluation is needed.";
  else if (event.overlap || event.outside) decisionCopy.textContent = event.overlap ? "The candidate violates the hard-core distance and is pruned geometrically." : "The candidate crosses the confinement boundary and is pruned before physics is evaluated.";
  else decisionCopy.textContent = "The browser oracle evaluates interactions with the current configuration, then records the result under this finite geometric state.";
  actionValue.textContent = event.state.action;
  domainValue.textContent = `n${event.state.n15}/${event.state.n25} · r${event.state.minimum.toFixed(2)} · b${event.state.clearance.toFixed(1)}`;
  energyValue.textContent = Number.isFinite(event.energy)
    ? event.interval ? `[${event.interval[0].toFixed(2)}, ${event.interval[1].toFixed(2)}]` : event.energy.toFixed(2)
    : "geometric prune";
  resolverValue.textContent = event.resolver;
  eventKind.textContent = isBacktrack ? "BACKTRACK" : isReuse ? "MARK REUSE" : event.accepted ? "ACCEPT" : "REJECT";
}

function setDecisionWaiting() {
  decisionBadge.className = "badge neutral";
  decisionBadge.textContent = "waiting";
  decisionTitle.textContent = "No proposal yet";
  decisionCopy.textContent = "Play or step once to expose a compatible patch on the finite boundary.";
  actionValue.textContent = "—";
  domainValue.textContent = "—";
  energyValue.textContent = "—";
  resolverValue.textContent = "—";
  eventKind.textContent = "SEED";
  captionAction.textContent = "Choose a policy, then play.";
}

function updateUI() {
  eventCounter.textContent = String(eventIndex).padStart(4, "0");
  atomMetric.textContent = String(atoms.length);
  atomDelta.textContent = `${atoms.length - seedCount >= 0 ? "+" : ""}${atoms.length - seedCount} after seed`;
  oracleMetric.textContent = oracleCalls > 9999 ? `${(oracleCalls / 1000).toFixed(1)}k` : String(oracleCalls);
  oracleDelta.textContent = `${acceptedDecisions + rejectedDecisions} resolved proposals`;
  const resolved = acceptedDecisions + rejectedDecisions;
  const reuse = resolved ? grammarDecisions / resolved : 0;
  reuseMetric.textContent = `${Math.round(reuse * 100)}%`;
  reuseDelta.textContent = `${grammarDecisions} decisions reused`;
  timelineLabel.textContent = `event ${eventIndex} · ${atoms.length} atoms`;
  phaseReadout.textContent = inferPhase();
  renderTimeline();
  renderStack();
  renderMarkings();
}

function inferPhase() {
  if (atoms.length < seedCount * .7) return "dissolving";
  const blue = atoms.filter((atom) => atom.species === "B").length / Math.max(1, atoms.length);
  let bonds = 0;
  for (let i = 0; i < atoms.length; i++) for (let j = i + 1; j < atoms.length; j++) if (atoms[i].p.distanceToSquared(atoms[j].p) < 1.45 ** 2) bonds++;
  const coordination = bonds * 2 / Math.max(1, atoms.length);
  if (scenarioSelect.value === "competition" && eventIndex < 40) return "competing";
  if (blue > .83 && coordination > 2.15) return "BC8-like";
  if (coordination > 2.55 && blue > .38 && blue < .76) return "IQC-like";
  if (coordination < 1.7) return "fluid / open";
  return "disordered solid";
}

function renderTimeline() {
  timeline.replaceChildren();
  eventHistory.forEach((event) => {
    const item = document.createElement("i");
    item.className = event.type;
    item.title = event.type;
    timeline.appendChild(item);
  });
}

function renderStack() {
  const rows = stackHistory.slice(-6).reverse();
  stackDepth.textContent = `depth ${Math.max(0, ...atoms.map((atom) => atom.depth))}`;
  searchStack.replaceChildren();
  if (!rows.length) {
    const row = document.createElement("li");
    row.className = "empty-row";
    row.textContent = "Accepted branches appear here.";
    searchStack.appendChild(row);
    return;
  }
  rows.forEach((entry) => {
    const row = document.createElement("li");
    if (entry.type === "backtrack") row.className = "rolled";
    const index = document.createElement("b");
    index.textContent = `d${entry.depth}`;
    const action = document.createElement("span");
    action.textContent = entry.type === "backtrack" ? entry.action : `${entry.action} · ${entry.family}`;
    const state = document.createElement("em");
    state.textContent = entry.type === "accept" ? "keep" : entry.type === "backtrack" ? "undo" : "try";
    row.append(index, action, state);
    searchStack.appendChild(row);
  });
}

function renderMarkings() {
  const source = policySelect.value === "marked" ? markingCache : actionCache;
  const entries = [...source.entries()].sort((a, b) => b[1].count - a[1].count).slice(0, 5);
  markCount.textContent = `${source.size} mark${source.size === 1 ? "" : "s"}`;
  markingTable.replaceChildren();
  if (!entries.length) {
    const empty = document.createElement("p");
    empty.textContent = "No repeated domain yet.";
    markingTable.appendChild(empty);
    return;
  }
  entries.forEach(([key, value]) => {
    const row = document.createElement("div");
    row.className = "mark-row";
    const code = document.createElement("code");
    code.textContent = key;
    code.title = key;
    const interval = document.createElement("span");
    interval.textContent = `${value.min.toFixed(1)}…${value.max.toFixed(1)}`;
    const count = document.createElement("b");
    count.textContent = `×${value.count}`;
    row.append(code, interval, count);
    markingTable.appendChild(row);
  });
}

function setPlaying(value) {
  playing = value;
  playIcon.textContent = playing ? "Ⅱ" : "▶";
  playLabel.textContent = playing ? "Pause" : "Play";
  playButton.setAttribute("aria-label", playing ? "Pause growth" : "Play growth");
  document.querySelector(".run-state").classList.toggle("running", playing);
  runStateText.textContent = playing ? "Search running" : eventIndex ? "Search paused" : "Paused at seed";
}

playButton.addEventListener("click", () => setPlaying(!playing));
stepButton.addEventListener("click", () => { setPlaying(false); performEvent(); });
resetButton.addEventListener("click", resetSimulation);
scenarioSelect.addEventListener("change", resetSimulation);
confinementSelect.addEventListener("change", resetSimulation);
policySelect.addEventListener("change", () => { markingCache.clear(); actionCache.clear(); grammarDecisions = 0; updateUI(); });
speedInput.addEventListener("input", () => { speedOutput.textContent = speedInput.value; });
backtrackInput.addEventListener("input", () => { backtrackOutput.textContent = `${backtrackInput.value}%`; });
[markingToggle, bondToggle, frontierToggle].forEach((input) => input.addEventListener("change", rebuildWorld));
rotateToggle.addEventListener("change", () => { controls.autoRotate = rotateToggle.checked; });

function resize() {
  const width = viewport.clientWidth;
  const height = viewport.clientHeight;
  if (!width || !height) return;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

new ResizeObserver(resize).observe(viewport);

function animate(now) {
  requestAnimationFrame(animate);
  const delta = Math.min(0.1, (now - lastFrame) / 1000);
  lastFrame = now;
  controls.autoRotate = rotateToggle.checked;
  controls.update();
  if (playing) {
    eventAccumulator += delta * Number(speedInput.value);
    while (eventAccumulator >= 1) {
      eventAccumulator--;
      performEvent();
      if (!playing) break;
    }
  } else eventAccumulator = 0;
  updateRollback(now);
  if (currentCandidate && decisionGroup.children[0]) {
    decisionGroup.children[0].rotation.y += delta * 1.8;
    decisionGroup.children[0].rotation.x += delta * .7;
  }
  renderer.render(scene, camera);
}

resetSimulation();
resize();
requestAnimationFrame(animate);
