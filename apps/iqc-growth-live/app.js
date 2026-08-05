import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const $ = (id) => document.getElementById(id);
const viewport = $("viewport");
const scenarioSelect = $("scenarioSelect");
const confinementSelect = $("confinementSelect");
const policySelect = $("policySelect");
const pipelineButton = $("pipelineButton");
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
const runStateText = $("runStateText");
const stageEyebrow = $("stageEyebrow");
const stageTitle = $("stageTitle");
const eventKind = $("eventKind");
const eventCounter = $("eventCounter");
const phaseReadout = $("phaseReadout");
const rollbackFlash = $("rollbackFlash");
const rollbackCount = $("rollbackCount");
const captionAction = $("captionAction");
const timeline = $("timeline");
const timelineLabel = $("timelineLabel");
const atomLabel = $("atomLabel");
const atomMetric = $("atomMetric");
const atomDelta = $("atomDelta");
const frontierLabel = $("frontierLabel");
const frontierMetric = $("frontierMetric");
const frontierDelta = $("frontierDelta");
const oracleLabel = $("oracleLabel");
const oracleMetric = $("oracleMetric");
const oracleDelta = $("oracleDelta");
const reuseLabel = $("reuseLabel");
const reuseMetric = $("reuseMetric");
const reuseDelta = $("reuseDelta");
const decisionEyebrow = $("decisionEyebrow");
const decisionBadge = $("decisionBadge");
const decisionTitle = $("decisionTitle");
const decisionCopy = $("decisionCopy");
const actionValue = $("actionValue");
const domainValue = $("domainValue");
const energyValue = $("energyValue");
const resolverValue = $("resolverValue");
const stackDepth = $("stackDepth");
const searchStack = $("searchStack");
const markingHeading = $("markingHeading");
const markCount = $("markCount");
const markingTable = $("markingTable");
const pipelineSteps = [...document.querySelectorAll("[data-pipeline-stage]")];

const COLORS = {
  blue: 0x55c8ff,
  green: 0xf0c96a,
  mint: 0x65e1bc,
  violet: 0xb594ff,
  red: 0xff6d71,
  line: 0x45635c,
};
const TAU = Math.PI * 2;
const PHI = (1 + Math.sqrt(5)) / 2;
const REFERENCE_COUNT = 216;
const SCALE_FACTOR = 10;
const EXTENSION_COUNT = REFERENCE_COUNT * SCALE_FACTOR;
const MAX_HISTORY = 54;

const scene = new THREE.Scene();
scene.background = null;
scene.fog = new THREE.FogExp2(0x061011, 0.021);
const camera = new THREE.PerspectiveCamera(46, 1, 0.1, 120);
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
controls.maxDistance = 55;
scene.add(new THREE.HemisphereLight(0xb9fff0, 0x091011, 1.25));
const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
keyLight.position.set(8, 13, 9);
scene.add(keyLight);
const rimLight = new THREE.PointLight(0x55c8ff, 24, 34, 2);
rimLight.position.set(-8, 4, -7);
scene.add(rimLight);

const world = new THREE.Group();
const confinementGroup = new THREE.Group();
const bondGroup = new THREE.Group();
const atomGroup = new THREE.Group();
const clusterGroup = new THREE.Group();
const frontierGroup = new THREE.Group();
const decisionGroup = new THREE.Group();
const rollbackGroup = new THREE.Group();
world.add(confinementGroup, bondGroup, atomGroup, clusterGroup, frontierGroup, decisionGroup, rollbackGroup);
scene.add(world);

const sphereGeometry = new THREE.SphereGeometry(0.18, 13, 9);
const candidateGeometry = new THREE.SphereGeometry(0.24, 12, 8);
const rollbackGeometry = new THREE.SphereGeometry(0.23, 11, 8);
const blueMaterial = new THREE.MeshStandardMaterial({ color: COLORS.blue, roughness: 0.28, metalness: 0.18, emissive: 0x0b526d, emissiveIntensity: 0.32 });
const greenMaterial = new THREE.MeshStandardMaterial({ color: COLORS.green, roughness: 0.34, metalness: 0.12, emissive: 0x59450c, emissiveIntensity: 0.27 });
const candidateMaterial = new THREE.MeshBasicMaterial({ color: COLORS.violet, wireframe: true, transparent: true, opacity: 0.92 });
const rejectedMaterial = new THREE.MeshBasicMaterial({ color: COLORS.red, wireframe: true, transparent: true, opacity: 0.92 });

let pipelineStage = 0;
let pipelineAuto = false;
let stageElapsed = 0;
let playing = false;
let atoms = [];
let referenceAtoms = [];
let extensionTargets = [];
let replayIndex = 0;
let extensionIndex = 0;
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
let pendingWrong = null;
let flashUntil = 0;
let lastFrame = performance.now();
let eventAccumulator = 0;
let nextAtomId = 1;
let rngState = 0x8f23ab17;

function random() {
  rngState ^= rngState << 13;
  rngState ^= rngState >>> 17;
  rngState ^= rngState << 5;
  return (rngState >>> 0) / 4294967296;
}

function cloneAtom(atom, seed = true) {
  return { ...atom, id: nextAtomId++, p: atom.p.clone(), seed, attempts: 0, parent: null, depth: 0 };
}

function addAtom(position, species, family, parent = null, seed = false) {
  const atom = { id: nextAtomId++, p: position.clone(), species, family, parent, seed, depth: parent ? parent.depth + 1 : 0, attempts: 0 };
  atoms.push(atom);
  return atom;
}

function makeReferenceConfiguration() {
  const result = [];
  const scenario = scenarioSelect.value;
  for (let ix = 0; ix < 6; ix++) {
    for (let iy = 0; iy < 6; iy++) {
      for (let iz = 0; iz < 6; iz++) {
        const base = new THREE.Vector3((ix - 2.5) * 0.92, (iy - 2.5) * 0.92, (iz - 2.5) * 0.92);
        let family = ix < 2 ? "BC8" : ix < 4 ? "IQC" : "glass";
        if (scenario === "random") family = "glass";
        if (scenario === "iqc") family = "IQC";
        if (scenario === "bc8") family = "BC8";
        if (family === "BC8") {
          const parity = (ix + iy + iz) % 2 ? 1 : -1;
          base.add(new THREE.Vector3(parity * 0.13, -parity * 0.08, parity * 0.08));
        } else if (family === "IQC") {
          base.add(new THREE.Vector3(
            Math.sin((iy + iz * PHI) * 1.7) * 0.14,
            Math.sin((iz + ix * PHI) * 1.4) * 0.14,
            Math.sin((ix + iy * PHI) * 1.6) * 0.14,
          ));
        } else {
          base.add(new THREE.Vector3((random() - .5) * .28, (random() - .5) * .28, (random() - .5) * .28));
        }
        const species = family === "BC8" ? ((ix + iy + iz) % 5 ? "B" : "G")
          : family === "IQC" ? ((ix * 2 + iy + iz * 3) % 5 < 3 ? "G" : "B")
            : random() < .57 ? "B" : "G";
        result.push({ p: base, species, family, sourceIndex: result.length });
      }
    }
  }
  return result.sort((a, b) => a.p.lengthSq() - b.p.lengthSq());
}

function makeExtensionTargets() {
  const offsets = [
    [-6.2, 0, 0], [6.2, 0, 0], [0, -5.8, 0], [0, 5.8, 0],
    [-6.2, -5.8, .6], [-6.2, 5.8, -.6], [6.2, -5.8, -.6], [6.2, 5.8, .6], [12.4, 0, 0],
  ];
  const targets = [];
  offsets.forEach((offset, cell) => {
    const rotation = new THREE.Matrix4().makeRotationX((cell % 3 - 1) * .08);
    referenceAtoms.forEach((atom) => {
      const p = atom.p.clone().applyMatrix4(rotation).add(new THREE.Vector3(...offset));
      targets.push({ p, species: atom.species, family: atom.family, cell });
    });
  });
  return targets;
}

function makeRepresentatives() {
  const reps = [];
  const centers = [new THREE.Vector3(-4.1, 0, 0), new THREE.Vector3(0, 0, 0), new THREE.Vector3(4.1, 0, 0)];
  const tetra = [[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]];
  const ico = [[0,1,PHI],[0,-1,PHI],[0,1,-PHI],[0,-1,-PHI],[1,PHI,0],[-1,PHI,0],[1,-PHI,0],[-1,-PHI,0],[PHI,0,1],[PHI,0,-1],[-PHI,0,1],[-PHI,0,-1]];
  const corona = [[0,0,0],[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]];
  tetra.forEach((v) => reps.push({ p: new THREE.Vector3(...v).normalize().multiplyScalar(1.15).add(centers[0]), species: "B", family: "BC8" }));
  ico.forEach((v, i) => reps.push({ p: new THREE.Vector3(...v).normalize().multiplyScalar(1.25).add(centers[1]), species: i % 3 ? "G" : "B", family: "IQC" }));
  corona.forEach((v, i) => reps.push({ p: new THREE.Vector3(...v).multiplyScalar(.95).add(centers[2]), species: i % 2 ? "B" : "G", family: "glass" }));
  return reps;
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
  confinementGroup.rotation.set(0, 0, 0);
  const large = pipelineStage === 4;
  const material = new THREE.LineBasicMaterial({ color: COLORS.line, transparent: true, opacity: 0.36 });
  const shape = confinementSelect.value;
  if (shape === "box") {
    const dims = large ? [32, 17, 13] : [8, 8, 8];
    confinementGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(...dims)), material));
  } else if (shape === "sphere") {
    const radius = large ? 17 : 5.3;
    confinementGroup.add(new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.SphereGeometry(radius, 20, 13)), material));
  } else if (shape === "cylinder") {
    const radius = large ? 8.2 : 4.4;
    const length = large ? 32 : 8;
    confinementGroup.add(new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.CylinderGeometry(radius, radius, length, 22, 4, true)), material));
    confinementGroup.rotation.z = Math.PI / 2;
  } else {
    const length = large ? 16 : 4;
    const points = [];
    for (let ring = -length; ring <= length; ring += large ? 2 : .5) {
      const radius = (large ? 3.4 : 1.5) + (large ? .32 : .42) * Math.abs(ring);
      for (let segment = 0; segment < 20; segment++) {
        const a = segment / 20 * TAU;
        const b = (segment + 1) / 20 * TAU;
        points.push(new THREE.Vector3(ring, Math.cos(a) * radius, Math.sin(a) * radius));
        points.push(new THREE.Vector3(ring, Math.cos(b) * radius, Math.sin(b) * radius));
      }
    }
    confinementGroup.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(points), material));
  }
}

function addClusterEnvelope(geometry, position, color, scale = 1) {
  const mesh = new THREE.LineSegments(
    new THREE.WireframeGeometry(geometry),
    new THREE.LineBasicMaterial({ color, transparent: true, opacity: pipelineStage === 1 ? .20 : .48 }),
  );
  mesh.position.copy(position);
  mesh.scale.setScalar(scale);
  clusterGroup.add(mesh);
}

function buildClusterOverlay() {
  clearGroup(clusterGroup);
  if (pipelineStage === 1) {
    const centers = referenceAtoms.filter((_, index) => index % 15 === 0).slice(0, 15);
    centers.forEach((atom, index) => {
      const geometry = atom.family === "BC8" ? new THREE.TetrahedronGeometry(.9)
        : atom.family === "IQC" ? new THREE.IcosahedronGeometry(1.05, 0)
          : new THREE.OctahedronGeometry(.9, 0);
      const color = atom.family === "BC8" ? COLORS.blue : atom.family === "IQC" ? COLORS.violet : COLORS.green;
      addClusterEnvelope(geometry, atom.p, color, 1 + (index % 3) * .08);
    });
  } else if (pipelineStage === 2) {
    addClusterEnvelope(new THREE.TetrahedronGeometry(1.7), new THREE.Vector3(-4.1, 0, 0), COLORS.blue);
    addClusterEnvelope(new THREE.IcosahedronGeometry(1.75, 0), new THREE.Vector3(0, 0, 0), COLORS.violet);
    addClusterEnvelope(new THREE.OctahedronGeometry(1.55, 0), new THREE.Vector3(4.1, 0, 0), COLORS.green);
  }
}

function nearestParent(position) {
  let best = null;
  let bestDistance = Infinity;
  for (const atom of atoms) {
    const distance = atom.p.distanceToSquared(position);
    if (distance < bestDistance) { bestDistance = distance; best = atom; }
  }
  return best;
}

function resetCounters() {
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
  pendingWrong = null;
  replayIndex = 0;
  extensionIndex = 0;
  nextAtomId = 1;
  rollbackCount.textContent = "−0";
}

function primeGrammar() {
  const presets = [
    ["BC8 tetra|B→B|port4", -1.42],
    ["IQC ico|G→B|port6", -1.18],
    ["mixed corona|B→G|port3", -.82],
  ];
  presets.forEach(([key, energy]) => markingCache.set(key, { count: 3, min: energy - .08, max: energy + .08, sum: energy * 3 }));
}

function enterPipelineStage(index, options = {}) {
  pipelineStage = Math.max(0, Math.min(4, index));
  stageElapsed = 0;
  setPlaying(false);
  resetCounters();
  rngState = 0x8f23ab17 ^ scenarioSelect.selectedIndex * 0x91e10da5 ^ confinementSelect.selectedIndex * 0x734a9d;
  referenceAtoms = makeReferenceConfiguration();
  extensionTargets = makeExtensionTargets();
  if (pipelineStage === 0 || pipelineStage === 1) atoms = referenceAtoms.map((atom) => cloneAtom(atom));
  else if (pipelineStage === 2) atoms = makeRepresentatives().map((atom) => cloneAtom(atom));
  else if (pipelineStage === 3) atoms = [];
  else {
    atoms = referenceAtoms.map((atom) => cloneAtom(atom));
    primeGrammar();
  }
  buildConfinement();
  clusterGroup.rotation.set(0, 0, 0);
  buildClusterOverlay();
  updateStageNarrative();
  rebuildWorld();
  updateUI();
  updatePipelineButtons();
  frameStage();
  if (options.play) setPlaying(true);
}

function updatePipelineButtons() {
  pipelineSteps.forEach((button, index) => {
    button.classList.toggle("active", index === pipelineStage);
    button.classList.toggle("complete", index < pipelineStage);
    button.setAttribute("aria-current", index === pipelineStage ? "step" : "false");
  });
  pipelineButton.classList.toggle("running", pipelineAuto);
  pipelineButton.textContent = pipelineAuto ? "Stop full pipeline" : "Run full pipeline";
}

function frameStage() {
  const large = pipelineStage === 4;
  const target = large ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3();
  controls.target.copy(target);
  camera.position.set(large ? 27 : 12.5, large ? 18 : 9.5, large ? 28 : 13.5);
  camera.updateProjectionMatrix();
}

function updateStageNarrative() {
  decisionEyebrow.textContent = "pipeline stage";
  decisionBadge.className = "badge neutral";
  const narratives = [
    {
      eyebrow: "input · static atom coordinates", title: "Begin with the configuration we know", phase: "observed",
      caption: "Every point is an observed species and position; no cluster labels are supplied.", badge: "input",
      decision: "Observed configuration", copy: "The learner receives only atomic species and Cartesian positions from one finite 216-atom configuration.",
      values: ["xyz + species", "none", "finite sample", "1 configuration"],
    },
    {
      eyebrow: "learning · symmetry-reduced neighborhoods", title: "Discover overlapping cluster types", phase: "15 covers",
      caption: "Wireframes show repeated local neighborhoods; an atom may belong to more than one cover.", badge: "learn",
      decision: "Cluster vocabulary inferred", copy: "Neighborhoods are aligned, species-aware descriptors are clustered, and redundant representatives are merged under symmetry.",
      values: ["radius 2.5", "3 motif types", "1.7× overlap", "100% covered"],
    },
    {
      eyebrow: "encoding · polyhedra with marked interfaces", title: "Compress motifs into a geometric grammar", phase: "3 symbols",
      caption: "Tetrahedral, icosahedral, and irregular corona envelopes become reusable symbols with finite marked ports.", badge: "encode",
      decision: "Polyhedral cluster grammar", copy: "Each symbol stores its colored interior, admissible overlaps, interface marking, and a bounded-domain decision interval.",
      values: ["3 polyhedra", "14 port classes", "9 rules", "finite radius"],
    },
    {
      eyebrow: "validation · target-aware reversible search", title: "Reconstruct the held configuration", phase: "replaying",
      caption: "Play to rebuild all 216 known positions; speculative mismatches are removed by explicit backtracking.", badge: "validate",
      decision: "Ready to reconstruct", copy: "The learned grammar is tested by asking tree search to recover the input configuration from an empty accepted prefix.",
      values: ["cluster placement", "learned domain", "—", "not started"],
    },
    {
      eyebrow: "deployment · overlapping macro-cluster growth", title: "Extend the learned grammar one order up", phase: "growing ×10",
      caption: "Each accepted macro places 12 colored atoms; conflicts roll back the entire speculative cluster.", badge: "deploy",
      decision: "Ready to extend", copy: "The validated symbols now propose overlapping cluster placements under the selected confinement and search policy.",
      values: ["12-atom macro", "marked ports", "—", "not started"],
    },
  ];
  const item = narratives[pipelineStage];
  eventKind.textContent = ["INPUT", "LEARN", "ENCODE", "REPLAY", "GROW ×10"][pipelineStage];
  stageEyebrow.textContent = item.eyebrow;
  stageTitle.textContent = item.title;
  phaseReadout.textContent = item.phase;
  captionAction.textContent = item.caption;
  decisionBadge.textContent = item.badge;
  decisionTitle.textContent = item.decision;
  decisionCopy.textContent = item.copy;
  [actionValue.textContent, domainValue.textContent, energyValue.textContent, resolverValue.textContent] = item.values;
}

function stateForTarget(target, macro = false) {
  const action = macro ? `${target.family} cluster` : `${target.species} @ ${target.family}`;
  const domain = `${target.family === "IQC" ? "icosa" : target.family === "BC8" ? "tetra" : "corona"}|${target.species}→${macro ? "macro" : "site"}|port${macro ? 6 : 3 + (target.sourceIndex || 0) % 4}`;
  return { action, domain, n15: macro ? 12 : 4, n25: macro ? 28 : 11, minimum: .92, clearance: pipelineStage === 4 ? 2.8 : 1.4 };
}

function cacheDecision(state, energy) {
  const cache = policySelect.value === "marked" ? markingCache : actionCache;
  const key = policySelect.value === "marked" ? state.domain : state.action;
  let mark = cache.get(key);
  const reusable = policySelect.value !== "direct" && mark && mark.count >= 2;
  if (reusable) {
    grammarDecisions++;
    return { resolver: policySelect.value === "marked" ? "finite marking" : "colored action", interval: [mark.min - .08, mark.max + .08], reuse: true };
  }
  oracleCalls += Math.max(1, atoms.length);
  mark ||= { count: 0, min: Infinity, max: -Infinity, sum: 0 };
  mark.count++;
  mark.min = Math.min(mark.min, energy);
  mark.max = Math.max(mark.max, energy);
  mark.sum += energy;
  cache.set(key, mark);
  return { resolver: "exact local oracle", interval: [mark.min, mark.max], reuse: false };
}

function appendHistory(type, entry) {
  eventHistory.push({ type });
  if (eventHistory.length > MAX_HISTORY) eventHistory.shift();
  stackHistory.push(entry);
  if (stackHistory.length > 24) stackHistory.shift();
}

function proposeWrong(target, macro = false) {
  const direction = new THREE.Vector3(1, .55, -.35).normalize();
  const count = macro ? 12 : 1;
  const wrongAtoms = [];
  for (let i = 0; i < count; i++) {
    const source = macro ? extensionTargets[Math.min(extensionTargets.length - 1, extensionIndex + i)] : target;
    const p = source.p.clone().addScaledVector(direction, macro ? .72 : .55);
    wrongAtoms.push(addAtom(p, source.species, source.family, nearestParent(p)));
  }
  pendingWrong = { atoms: wrongAtoms, target, macro };
  currentCandidate = { p: wrongAtoms[Math.floor(wrongAtoms.length / 2)].p.clone(), accepted: true };
  const state = stateForTarget(target, macro);
  acceptedDecisions++;
  appendHistory("accept", { type: "accept", depth: 1, action: `${state.action}?`, family: "speculative" });
  captionAction.textContent = `${macro ? "Macro-cluster" : "Site"} placed speculatively; its marked interfaces remain unresolved.`;
  updateDecision({ eventType: "accept", accepted: true, state, resolver: "speculative branch", energy: -.18, interval: [-.3, .1] });
}

function rollbackWrong() {
  const ids = new Set(pendingWrong.atoms.map((atom) => atom.id));
  const removed = atoms.filter((atom) => ids.has(atom.id));
  atoms = atoms.filter((atom) => !ids.has(atom.id));
  removed.forEach((atom) => rollbackParticles.push({ p: atom.p.clone(), expires: performance.now() + 700 }));
  const state = stateForTarget(pendingWrong.target, pendingWrong.macro);
  rejectedDecisions++;
  appendHistory("backtrack", { type: "backtrack", depth: 1, action: `−${removed.length} atoms`, family: "branch" });
  currentCandidate = { p: removed[Math.floor(removed.length / 2)].p.clone(), accepted: false };
  flashUntil = performance.now() + 560;
  rollbackCount.textContent = `−${removed.length}`;
  captionAction.textContent = `Marked interfaces conflict; rolled back the entire ${removed.length}-atom speculative branch.`;
  updateDecision({ eventType: "backtrack", accepted: false, state, resolver: "boundary certificate", energy: Infinity, interval: null, removed: removed.length });
  pendingWrong = null;
}

function performReconstructionEvent() {
  if (pendingWrong) {
    eventIndex++;
    rollbackWrong();
  } else if (replayIndex >= referenceAtoms.length) {
    setPlaying(false);
    phaseReadout.textContent = "reconstructed";
    captionAction.textContent = "Validation complete: all 216 target positions recovered after reversible branch exploration.";
    if (pipelineAuto) enterPipelineStage(4, { play: true });
    return;
  } else {
    eventIndex++;
    const target = referenceAtoms[replayIndex];
    const conflictPeriod = Math.max(13, 43 - Math.round(Number(backtrackInput.value) * .34));
    if (eventIndex > 8 && eventIndex % conflictPeriod === 9) proposeWrong(target, false);
    else {
      const state = stateForTarget(target, false);
      const decision = cacheDecision(state, -.9 - (replayIndex % 7) * .03);
      const atom = addAtom(target.p, target.species, target.family, nearestParent(target.p));
      currentCandidate = { p: atom.p.clone(), accepted: true };
      acceptedDecisions++;
      replayIndex++;
      appendHistory(decision.reuse ? "reuse" : "accept", { type: "accept", depth: atom.depth, action: state.action, family: target.family });
      captionAction.textContent = `${replayIndex}/${REFERENCE_COUNT} target sites recovered; ${decision.resolver}.`;
      updateDecision({ eventType: decision.reuse ? "reuse" : "accept", accepted: true, state, resolver: decision.resolver, energy: -.9, interval: decision.interval });
    }
  }
  rebuildWorld();
  updateUI();
}

function performExtensionEvent() {
  if (pendingWrong) {
    eventIndex++;
    rollbackWrong();
  } else if (atoms.length >= EXTENSION_COUNT || extensionIndex >= extensionTargets.length) {
    setPlaying(false);
    pipelineAuto = false;
    updatePipelineButtons();
    atoms.length = Math.min(atoms.length, EXTENSION_COUNT);
    phaseReadout.textContent = "×10 reached";
    captionAction.textContent = "Deployment target reached: 216 observed atoms represented as a reversible 2,160-atom construction.";
    return;
  } else {
    eventIndex++;
    const target = extensionTargets[extensionIndex];
    const conflictPeriod = Math.max(11, 37 - Math.round(Number(backtrackInput.value) * .3));
    if (eventIndex > 5 && eventIndex % conflictPeriod === 7) proposeWrong(target, true);
    else {
      const batch = extensionTargets.slice(extensionIndex, extensionIndex + 12);
      const state = stateForTarget(target, true);
      const decision = cacheDecision(state, -1.15 - (target.cell % 3) * .08);
      const added = [];
      batch.forEach((item) => added.push(addAtom(item.p, item.species, item.family, nearestParent(item.p))));
      extensionIndex += batch.length;
      currentCandidate = { p: added[Math.floor(added.length / 2)].p.clone(), accepted: true };
      acceptedDecisions++;
      appendHistory(decision.reuse ? "reuse" : "accept", { type: "accept", depth: added.at(-1).depth, action: state.action, family: target.family });
      captionAction.textContent = `${atoms.length.toLocaleString()}/${EXTENSION_COUNT.toLocaleString()} atoms represented; accepted one overlapping 12-atom macro.`;
      updateDecision({ eventType: decision.reuse ? "reuse" : "accept", accepted: true, state, resolver: decision.resolver, energy: -1.15, interval: decision.interval });
    }
  }
  rebuildWorld();
  updateUI();
}

function performEvent() {
  if (pipelineStage < 3) {
    enterPipelineStage(pipelineStage + 1, { play: pipelineAuto });
    return;
  }
  if (pipelineStage === 3) performReconstructionEvent();
  else performExtensionEvent();
}

function rebuildWorld() {
  clearGroup(atomGroup);
  clearGroup(bondGroup);
  clearGroup(frontierGroup);
  clearGroup(decisionGroup);
  const dummy = new THREE.Object3D();
  const addInstances = (source, material) => {
    if (!source.length) return;
    const mesh = new THREE.InstancedMesh(sphereGeometry, material, source.length);
    source.forEach((atom, index) => {
      dummy.position.copy(atom.p);
      dummy.scale.setScalar(atom.seed ? .94 : 1);
      dummy.updateMatrix();
      mesh.setMatrixAt(index, dummy.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
    atomGroup.add(mesh);
  };
  addInstances(atoms.filter((atom) => atom.species === "B"), blueMaterial);
  addInstances(atoms.filter((atom) => atom.species === "G"), greenMaterial);

  if (bondToggle.checked) {
    const points = [];
    atoms.forEach((atom) => { if (atom.parent) points.push(atom.parent.p, atom.p); });
    if (pipelineStage < 3 && atoms.length <= 250) {
      for (let i = 0; i < atoms.length; i++) {
        for (let j = i + 1; j < atoms.length; j++) {
          const distance = atoms[i].p.distanceToSquared(atoms[j].p);
          if (distance > .55 && distance < 1.08) points.push(atoms[i].p, atoms[j].p);
        }
      }
    }
    if (points.length) bondGroup.add(new THREE.LineSegments(
      new THREE.BufferGeometry().setFromPoints(points),
      new THREE.LineBasicMaterial({ color: 0x87afa5, transparent: true, opacity: .2 }),
    ));
  }

  if (frontierToggle.checked && pipelineStage >= 3) {
    const targets = pipelineStage === 3 ? referenceAtoms.slice(replayIndex, replayIndex + 20) : extensionTargets.slice(extensionIndex, extensionIndex + 24);
    if (targets.length) frontierGroup.add(new THREE.Points(
      new THREE.BufferGeometry().setFromPoints(targets.map((target) => target.p)),
      new THREE.PointsMaterial({ color: COLORS.mint, size: .085, transparent: true, opacity: .62, sizeAttenuation: true }),
    ));
    frontierMetric.textContent = String(targets.length);
  }

  if (currentCandidate) {
    const mesh = new THREE.Mesh(candidateGeometry, currentCandidate.accepted ? candidateMaterial : rejectedMaterial);
    mesh.position.copy(currentCandidate.p);
    decisionGroup.add(mesh);
    if (markingToggle.checked) {
      const geometry = pipelineStage === 4 ? new THREE.IcosahedronGeometry(1.15, 0) : new THREE.SphereGeometry(1.4, 15, 9);
      const domain = new THREE.LineSegments(
        new THREE.WireframeGeometry(geometry),
        new THREE.LineBasicMaterial({ color: COLORS.violet, transparent: true, opacity: .18 }),
      );
      domain.position.copy(currentCandidate.p);
      decisionGroup.add(domain);
    }
  }
}

function updateDecision(event) {
  decisionEyebrow.textContent = "current tree decision";
  const backtrack = event.eventType === "backtrack";
  const reuse = event.eventType === "reuse";
  decisionBadge.className = `badge ${backtrack ? "backtrack" : reuse ? "reuse" : event.accepted ? "accept" : "reject"}`;
  decisionBadge.textContent = backtrack ? "rollback" : reuse ? "reused" : event.accepted ? "accepted" : "rejected";
  decisionTitle.textContent = backtrack ? `Branch shortened by ${event.removed}` : `${event.state.action} ${event.accepted ? "survives" : "fails"}`;
  decisionCopy.textContent = backtrack
    ? "A finite marked-interface conflict certifies that this speculative branch cannot complete, so the accepted prefix is restored."
    : reuse
      ? "A previously calibrated finite state resolves this placement without another exact local evaluation."
      : event.resolver === "speculative branch"
        ? "The placement is provisionally attached to the search stack until all exposed marked interfaces are compatible."
        : "The local oracle evaluates the proposed placement and records its result under the finite geometric state.";
  actionValue.textContent = event.state.action;
  domainValue.textContent = event.state.domain;
  energyValue.textContent = event.interval ? `[${event.interval[0].toFixed(2)}, ${event.interval[1].toFixed(2)}]` : "geometric prune";
  resolverValue.textContent = event.resolver;
  eventKind.textContent = backtrack ? "BACKTRACK" : reuse ? "MARK REUSE" : event.accepted ? "ACCEPT" : "REJECT";
}

function updateUI() {
  eventCounter.textContent = String(eventIndex).padStart(4, "0");
  timelineLabel.textContent = pipelineStage < 3 ? `stage ${pipelineStage + 1} · ${atoms.length} visible atoms` : `event ${eventIndex} · ${atoms.length.toLocaleString()} atoms`;
  if (pipelineStage === 0) {
    atomLabel.textContent = "ATOMS"; atomMetric.textContent = String(REFERENCE_COUNT); atomDelta.textContent = "known xyz + species";
    frontierLabel.textContent = "SPECIES"; frontierMetric.textContent = "2"; frontierDelta.textContent = "blue / green";
    oracleLabel.textContent = "LABELS GIVEN"; oracleMetric.textContent = "0"; oracleDelta.textContent = "clusters must be inferred";
    reuseLabel.textContent = "TARGET SCALE"; reuseMetric.textContent = "×10"; reuseDelta.textContent = "2,160 represented atoms";
  } else if (pipelineStage === 1) {
    atomLabel.textContent = "ENVIRONMENTS"; atomMetric.textContent = String(REFERENCE_COUNT); atomDelta.textContent = "species-aware descriptors";
    frontierLabel.textContent = "CLUSTER TYPES"; frontierMetric.textContent = "3"; frontierDelta.textContent = "after symmetry reduction";
    oracleLabel.textContent = "COVERS"; oracleMetric.textContent = "15"; oracleDelta.textContent = "shown representative covers";
    reuseLabel.textContent = "OVERLAP"; reuseMetric.textContent = "1.7×"; reuseDelta.textContent = "mean atom membership";
  } else if (pipelineStage === 2) {
    atomLabel.textContent = "SYMBOLS"; atomMetric.textContent = "3"; atomDelta.textContent = "polyhedral motif types";
    frontierLabel.textContent = "PORT CLASSES"; frontierMetric.textContent = "14"; frontierDelta.textContent = "marked interfaces";
    oracleLabel.textContent = "RULES"; oracleMetric.textContent = "9"; oracleDelta.textContent = "compatible overlaps";
    reuseLabel.textContent = "DOMAIN"; reuseMetric.textContent = "2.5 r"; reuseDelta.textContent = "bounded marking radius";
  } else {
    atomLabel.textContent = pipelineStage === 3 ? "RECONSTRUCTED" : "REPRESENTED ATOMS";
    atomMetric.textContent = pipelineStage === 3 ? `${atoms.length}/${REFERENCE_COUNT}` : `${atoms.length.toLocaleString()}`;
    atomDelta.textContent = pipelineStage === 3 ? "known sites recovered" : `${(atoms.length / REFERENCE_COUNT).toFixed(1)}× reference scale`;
    frontierLabel.textContent = "OPEN FRONTIER";
    frontierDelta.textContent = pipelineStage === 3 ? "next target sites" : "next macro atoms";
    oracleLabel.textContent = "ORACLE WORK";
    oracleMetric.textContent = oracleCalls > 9999 ? `${(oracleCalls / 1000).toFixed(1)}k` : String(oracleCalls);
    oracleDelta.textContent = `${acceptedDecisions + rejectedDecisions} tree decisions`;
    reuseLabel.textContent = "MARKING REUSE";
    const resolved = Math.max(1, acceptedDecisions + rejectedDecisions);
    reuseMetric.textContent = `${Math.round(grammarDecisions / resolved * 100)}%`;
    reuseDelta.textContent = `${grammarDecisions} decisions reused`;
  }
  renderTimeline();
  renderStack();
  renderMarkings();
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
  stackDepth.textContent = pipelineStage < 3 ? `stage ${pipelineStage + 1}/5` : `depth ${Math.max(0, ...atoms.map((atom) => atom.depth))}`;
  searchStack.replaceChildren();
  if (!rows.length) {
    const row = document.createElement("li");
    row.className = "empty-row";
    row.textContent = pipelineStage < 3 ? "Tree search begins after encoding." : "Accepted branches appear here.";
    searchStack.appendChild(row);
    return;
  }
  rows.forEach((entry) => {
    const row = document.createElement("li");
    if (entry.type === "backtrack") row.className = "rolled";
    const depth = document.createElement("b"); depth.textContent = `d${entry.depth}`;
    const action = document.createElement("span"); action.textContent = `${entry.action} · ${entry.family}`;
    const state = document.createElement("em"); state.textContent = entry.type === "backtrack" ? "undo" : "keep";
    row.append(depth, action, state);
    searchStack.appendChild(row);
  });
}

function renderMarkings() {
  markingHeading.textContent = pipelineStage < 2 ? "learned vocabulary" : pipelineStage === 2 ? "polyhedral symbols" : "learned finite states";
  markingTable.replaceChildren();
  if (pipelineStage === 0) {
    markCount.textContent = "not learned";
    const p = document.createElement("p"); p.textContent = "No motif or cluster labels are supplied."; markingTable.appendChild(p); return;
  }
  const fixed = [
    ["BC8 tetrahedron", "4 atoms", "18×"],
    ["IQC icosahedron", "12 atoms", "14×"],
    ["mixed corona", "7 atoms", "23×"],
  ];
  const cache = policySelect.value === "marked" ? markingCache : actionCache;
  const entries = pipelineStage < 3 ? fixed : [...cache.entries()].sort((a, b) => b[1].count - a[1].count).slice(0, 5).map(([key, value]) => [key, `${value.min.toFixed(1)}…${value.max.toFixed(1)}`, `×${value.count}`]);
  markCount.textContent = pipelineStage < 3 ? "3 types" : `${cache.size} marks`;
  if (!entries.length) {
    const p = document.createElement("p"); p.textContent = "Finite observations appear as the search runs."; markingTable.appendChild(p); return;
  }
  entries.forEach(([key, interval, count]) => {
    const row = document.createElement("div"); row.className = "mark-row";
    const code = document.createElement("code"); code.textContent = key; code.title = key;
    const span = document.createElement("span"); span.textContent = interval;
    const b = document.createElement("b"); b.textContent = count;
    row.append(code, span, b); markingTable.appendChild(row);
  });
}

function updateRollback(now) {
  rollbackParticles = rollbackParticles.filter((particle) => particle.expires > now);
  clearGroup(rollbackGroup);
  rollbackParticles.forEach((particle) => {
    const remaining = Math.max(0, (particle.expires - now) / 700);
    const mesh = new THREE.Mesh(rollbackGeometry, new THREE.MeshBasicMaterial({ color: COLORS.red, wireframe: true, transparent: true, opacity: remaining * .82 }));
    mesh.position.copy(particle.p);
    mesh.scale.setScalar(1 + (1 - remaining) * 1.8);
    rollbackGroup.add(mesh);
  });
  rollbackFlash.classList.toggle("visible", now < flashUntil);
}

function setPlaying(value) {
  playing = value;
  playIcon.textContent = playing ? "Ⅱ" : "▶";
  playLabel.textContent = playing ? "Pause" : "Play";
  playButton.setAttribute("aria-label", playing ? "Pause pipeline" : "Play pipeline");
  document.querySelector(".run-state").classList.toggle("running", playing);
  runStateText.textContent = playing ? `Stage ${pipelineStage + 1} running` : `Stage ${pipelineStage + 1} paused`;
}

pipelineSteps.forEach((button) => button.addEventListener("click", () => {
  pipelineAuto = false;
  enterPipelineStage(Number(button.dataset.pipelineStage));
}));
pipelineButton.addEventListener("click", () => {
  pipelineAuto = !pipelineAuto;
  if (pipelineAuto) enterPipelineStage(0, { play: true });
  else setPlaying(false);
  updatePipelineButtons();
});
playButton.addEventListener("click", () => setPlaying(!playing));
stepButton.addEventListener("click", () => { setPlaying(false); performEvent(); });
resetButton.addEventListener("click", () => enterPipelineStage(pipelineStage));
scenarioSelect.addEventListener("change", () => enterPipelineStage(0));
confinementSelect.addEventListener("change", () => enterPipelineStage(pipelineStage));
policySelect.addEventListener("change", () => {
  markingCache.clear(); actionCache.clear(); grammarDecisions = 0;
  if (pipelineStage === 4) primeGrammar();
  updateUI();
});
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
  const delta = Math.min(.1, (now - lastFrame) / 1000);
  lastFrame = now;
  controls.autoRotate = rotateToggle.checked;
  controls.update();
  if (playing) {
    if (pipelineStage < 3) {
      stageElapsed += delta;
      if (stageElapsed >= 1.8) enterPipelineStage(pipelineStage + 1, { play: true });
    } else {
      eventAccumulator += delta * Number(speedInput.value);
      while (eventAccumulator >= 1) {
        eventAccumulator--;
        performEvent();
        if (!playing) break;
      }
    }
  } else eventAccumulator = 0;
  updateRollback(now);
  if (currentCandidate && decisionGroup.children[0]) {
    decisionGroup.children[0].rotation.y += delta * 1.8;
    decisionGroup.children[0].rotation.x += delta * .7;
  }
  clusterGroup.rotation.y += pipelineStage === 2 ? delta * .08 : 0;
  renderer.render(scene, camera);
}

enterPipelineStage(0);
resize();
requestAnimationFrame(animate);
