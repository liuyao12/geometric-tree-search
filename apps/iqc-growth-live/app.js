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
const captionAction = $("captionAction");
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
const rdfChart = $("rdfChart");
const rdfStatus = $("rdfStatus");
const coordChart = $("coordChart");
const coordStatus = $("coordStatus");
const coordClearButton = $("coordClearButton");
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
const legendHeading = $("legendHeading");
const speciesLegend = $("speciesLegend");
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
const FRONTIER_BATCH = 4;
const RDF_BINS = 38;
const RDF_MAX_RADIUS = 4.2;
const COORDINATION_CUTOFF = 1.32;
const ELEMENTS = {
  Na: { color: 0x8f8fff, css: "#8f8fff", radius: 1.66 },
  Cl: { color: 0x59d65c, css: "#59d65c", radius: 1.02 },
  Ni: { color: 0x63d16e, css: "#63d16e", radius: 1.24 },
  Ti: { color: 0xb8c2cc, css: "#b8c2cc", radius: 1.60 },
  Cu: { color: 0xd98545, css: "#d98545", radius: 1.32 },
  Zr: { color: 0x79d3d6, css: "#79d3d6", radius: 1.75 },
  Al: { color: 0xb8c0c8, css: "#b8c0c8", radius: 1.21 },
  Fe: { color: 0xd45d42, css: "#d45d42", radius: 1.24 },
  Si: { color: 0xe7b883, css: "#e7b883", radius: 1.11 },
};
const MATERIALS = {
  competition: { name: "NaCl rocksalt", elements: ["Na", "Cl"], spacingA: 2.82, cell: "Fm3̅m · a = 5.640 Å", clusters: 2 },
  random: { name: "Cu₆₄Zr₃₆ metallic glass", elements: ["Cu", "Zr"], spacingA: 2.72, cell: "amorphous · quenched surrogate", clusters: 4 },
  iqc: { name: "Al–Cu–Fe IQC approximant", elements: ["Al", "Cu", "Fe"], spacingA: 2.55, cell: "icosahedral approximant", clusters: 5 },
  bc8: { name: "silicon BC8-like network", elements: ["Si"], spacingA: 2.35, cell: "BC8 target · a = 6.636 Å", clusters: 3 },
};
const CLUSTER_COLORS = [0x55c8ff, 0xb594ff, 0x65e1bc, 0xf0c96a, 0xff7f88, 0x7ee1e8];
const BALANCE_DIRECTIONS = [
  [0, 1, PHI], [0, -1, PHI], [0, 1, -PHI], [0, -1, -PHI],
  [1, PHI, 0], [-1, PHI, 0], [1, -PHI, 0], [-1, -PHI, 0],
  [PHI, 0, 1], [PHI, 0, -1], [-PHI, 0, 1], [-PHI, 0, -1],
].map((v) => new THREE.Vector3(...v).normalize());

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
world.add(confinementGroup, bondGroup, atomGroup, clusterGroup, frontierGroup, decisionGroup);
scene.add(world);

const sphereGeometry = new THREE.SphereGeometry(0.18, 13, 9);
const candidateGeometry = new THREE.SphereGeometry(0.24, 12, 8);
const blueMaterial = new THREE.MeshStandardMaterial({ color: COLORS.blue, roughness: 0.28, metalness: 0.18, emissive: 0x0b526d, emissiveIntensity: 0.32 });
const greenMaterial = new THREE.MeshStandardMaterial({ color: COLORS.green, roughness: 0.34, metalness: 0.12, emissive: 0x59450c, emissiveIntensity: 0.27 });
const blueDimMaterial = new THREE.MeshStandardMaterial({ color: COLORS.blue, transparent: true, opacity: .12, roughness: .5, depthWrite: false });
const greenDimMaterial = new THREE.MeshStandardMaterial({ color: COLORS.green, transparent: true, opacity: .12, roughness: .5, depthWrite: false });
const elementMaterials = new Map();
const dimElementMaterials = new Map();
const clusterMaterials = CLUSTER_COLORS.map((color) => new THREE.MeshStandardMaterial({ color, roughness: .32, metalness: .08, emissive: color, emissiveIntensity: .12 }));
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
let sectorCounts = new Array(BALANCE_DIRECTIONS.length).fill(0);
let eventIndex = 0;
let oracleCalls = 0;
let grammarDecisions = 0;
let acceptedDecisions = 0;
let rejectedDecisions = 0;
let stackHistory = [];
let markingCache = new Map();
let actionCache = new Map();
let currentCandidate = null;
let pendingWrong = null;
let lastFrame = performance.now();
let eventAccumulator = 0;
let nextAtomId = 1;
let rngState = 0x8f23ab17;
let referenceSpacing = 1;
let referenceSpacingA = 1;
let referenceStructuralStats = null;
let liveStructuralStats = null;
let lastLiveStatsKey = "";
let coordinationSelection = null;
let learnedClusters = null;

function currentMaterial() {
  return MATERIALS[scenarioSelect.value];
}

function getElementMaterial(symbol, dim = false) {
  const cache = dim ? dimElementMaterials : elementMaterials;
  if (!cache.has(symbol)) {
    const data = ELEMENTS[symbol];
    cache.set(symbol, new THREE.MeshStandardMaterial({
      color: data.color,
      roughness: dim ? .55 : .3,
      metalness: dim ? 0 : .14,
      transparent: dim,
      opacity: dim ? .1 : 1,
      depthWrite: !dim,
      emissive: dim ? 0x000000 : data.color,
      emissiveIntensity: dim ? 0 : .16,
    }));
  }
  return cache.get(symbol);
}

function elementScale(symbol) {
  const material = currentMaterial();
  return Math.max(.8, ELEMENTS[symbol].radius / material.spacingA * 2.55);
}

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

function medianNearestSpacing(source) {
  if (source.length < 2) return 1;
  const nearest = source.map((atom, index) => {
    let minimum = Infinity;
    for (let other = 0; other < source.length; other++) {
      if (other === index) continue;
      minimum = Math.min(minimum, atom.p.distanceTo(source[other].p));
    }
    return minimum;
  }).sort((a, b) => a - b);
  return nearest[Math.floor(nearest.length / 2)] || 1;
}

function calculateStructuralStats(source, spacing) {
  const rdf = new Array(RDF_BINS).fill(0);
  const coordination = new Array(13).fill(0);
  if (!source.length) return { rdf, coordination, meanCoordination: 0, count: 0, neighborCounts: [], neighborLists: [] };

  const neighbors = new Array(source.length).fill(0);
  const neighborLists = Array.from({ length: source.length }, () => []);
  const minimum = new THREE.Vector3(Infinity, Infinity, Infinity);
  const maximum = new THREE.Vector3(-Infinity, -Infinity, -Infinity);
  source.forEach((atom) => {
    minimum.min(atom.p);
    maximum.max(atom.p);
  });

  for (let first = 0; first < source.length; first++) {
    for (let second = first + 1; second < source.length; second++) {
      const normalizedDistance = source[first].p.distanceTo(source[second].p) / spacing;
      if (normalizedDistance < RDF_MAX_RADIUS) {
        const bin = Math.min(RDF_BINS - 1, Math.floor(normalizedDistance / RDF_MAX_RADIUS * RDF_BINS));
        rdf[bin]++;
      }
      if (normalizedDistance <= COORDINATION_CUTOFF) {
        neighbors[first]++;
        neighbors[second]++;
        neighborLists[first].push(second);
        neighborLists[second].push(first);
      }
    }
  }

  const paddedSize = maximum.sub(minimum).divideScalar(spacing).addScalar(1);
  const volume = Math.max(1, paddedSize.x * paddedSize.y * paddedSize.z);
  const density = source.length / volume;
  for (let bin = 0; bin < RDF_BINS; bin++) {
    const inner = bin / RDF_BINS * RDF_MAX_RADIUS;
    const outer = (bin + 1) / RDF_BINS * RDF_MAX_RADIUS;
    const shellVolume = 4 / 3 * Math.PI * (outer ** 3 - inner ** 3);
    const idealPairs = .5 * source.length * density * shellVolume;
    rdf[bin] = idealPairs > 0 ? rdf[bin] / idealPairs : 0;
  }

  neighbors.forEach((value) => coordination[Math.min(12, value)]++);
  for (let index = 0; index < coordination.length; index++) coordination[index] /= source.length;
  const meanCoordination = neighbors.reduce((sum, value) => sum + value, 0) / source.length;
  return { rdf, coordination, meanCoordination, count: source.length, neighborCounts: neighbors, neighborLists };
}

function currentLiveStructure() {
  const source = pipelineStage === 3 ? atoms.filter((atom) => atom.observed) : [];
  const key = `${pipelineStage}:${replayIndex}`;
  if (key !== lastLiveStatsKey) {
    liveStructuralStats = calculateStructuralStats(source, referenceSpacing);
    lastLiveStatsKey = key;
  }
  return { source, stats: liveStructuralStats || calculateStructuralStats([], referenceSpacing) };
}

function selectedCoordinationDetail() {
  if (coordinationSelection === null || pipelineStage === 2) return null;
  const structure = pipelineStage === 3
    ? currentLiveStructure()
    : { source: atoms, stats: referenceStructuralStats };
  if (!structure.source.length || !structure.stats) return null;
  const matching = structure.source.map((atom, index) => ({ atom, index }))
    .filter(({ index }) => Math.min(12, structure.stats.neighborCounts[index]) === coordinationSelection);
  if (!matching.length) return { ids: new Set(), matchCount: 0, center: null, neighbors: [] };
  const representative = matching.reduce((best, candidate) => candidate.atom.p.lengthSq() < best.atom.p.lengthSq() ? candidate : best);
  const neighbors = structure.stats.neighborLists[representative.index].map((index) => structure.source[index]);
  return {
    ids: new Set([representative.atom.id, ...neighbors.map((atom) => atom.id)]),
    matchCount: matching.length,
    center: representative.atom,
    neighbors,
  };
}

function selectCoordination(value) {
  if (pipelineStage === 2 || (pipelineStage === 3 && replayIndex === 0)) return;
  coordinationSelection = coordinationSelection === value ? null : value;
  rebuildWorld();
  updateUI();
}

function svgNode(tag, attributes = {}, text = "") {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attributes).forEach(([name, value]) => node.setAttribute(name, value));
  if (text) node.textContent = text;
  return node;
}

function drawChartFrame(svg, xLabel, yLabel) {
  svg.append(
    svgNode("line", { x1: 29, y1: 8, x2: 29, y2: 96, class: "chart-axis" }),
    svgNode("line", { x1: 29, y1: 96, x2: 352, y2: 96, class: "chart-axis" }),
    svgNode("text", { x: 350, y: 13, class: "chart-label", "text-anchor": "end" }, xLabel),
    svgNode("text", { x: 7, y: 13, class: "chart-label" }, yLabel),
  );
}

function linePath(values, maximum) {
  if (!values.length || maximum <= 0) return "";
  return values.map((value, index) => {
    const x = 29 + index / Math.max(1, values.length - 1) * 323;
    const y = 96 - Math.min(1, value / maximum) * 84;
    return `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");
}

function renderStructureStats() {
  if (!referenceStructuralStats) return;
  const { stats: live } = currentLiveStructure();
  rdfStatus.textContent = `known ${REFERENCE_COUNT} · live ${live.count}`;
  const selected = selectedCoordinationDetail();
  coordStatus.textContent = coordinationSelection === null
    ? `mean z ${referenceStructuralStats.meanCoordination.toFixed(1)} · ${live.count ? live.meanCoordination.toFixed(1) : "—"}`
    : `${coordinationSelection === 12 ? "z≥12" : `z=${coordinationSelection}`} · ${selected?.matchCount || 0} centers · ${selected?.neighbors.length || 0} shown`;
  coordClearButton.hidden = coordinationSelection === null;

  rdfChart.replaceChildren();
  drawChartFrame(rdfChart, "r / a", "g");
  const rdfMaximum = Math.max(1, ...referenceStructuralStats.rdf, ...live.rdf) * 1.08;
  const unityY = 96 - Math.min(1, 1 / rdfMaximum) * 84;
  rdfChart.append(svgNode("line", { x1: 29, y1: unityY, x2: 352, y2: unityY, class: "chart-guide" }));
  [1, 2, 3, 4].forEach((tick) => {
    const x = 29 + tick / RDF_MAX_RADIUS * 323;
    rdfChart.append(svgNode("text", { x, y: 108, class: "chart-label", "text-anchor": "middle" }, String(tick)));
  });
  rdfChart.append(svgNode("path", { id: "rdfKnownPath", d: linePath(referenceStructuralStats.rdf, rdfMaximum), class: "chart-known" }));
  if (live.count > 1) rdfChart.append(svgNode("path", { id: "rdfLivePath", d: linePath(live.rdf, rdfMaximum), class: "chart-live" }));

  coordChart.replaceChildren();
  drawChartFrame(coordChart, "coordination z", "P");
  const barStep = 323 / referenceStructuralStats.coordination.length;
  const coordMaximum = Math.max(.05, ...referenceStructuralStats.coordination, ...live.coordination) * 1.08;
  if (coordinationSelection !== null) {
    const x = 29 + coordinationSelection * barStep + 1;
    coordChart.append(svgNode("rect", { x, y: 8, width: barStep - 2, height: 88, class: "coord-selection" }));
  }
  referenceStructuralStats.coordination.forEach((value, index) => {
    const height = Math.min(1, value / coordMaximum) * 84;
    const x = 29 + index * barStep + 2;
    coordChart.append(svgNode("rect", { x, y: 96 - height, width: Math.max(1, barStep - 4), height, class: "coord-known" }));
  });
  if (live.count) live.coordination.forEach((value, index) => {
    const height = Math.min(1, value / coordMaximum) * 84;
    const x = 29 + index * barStep + barStep * .28;
    coordChart.append(svgNode("rect", { x, y: 96 - height, width: barStep * .44, height, class: "coord-live" }));
  });
  [0, 2, 4, 6, 8, 10, 12].forEach((tick) => {
    const x = 29 + (tick + .5) * barStep;
    coordChart.append(svgNode("text", { x, y: 108, class: "chart-label", "text-anchor": "middle" }, tick === 12 ? "12+" : String(tick)));
  });
  referenceStructuralStats.coordination.forEach((_, index) => {
    const hit = svgNode("rect", {
      x: 29 + index * barStep,
      y: 8,
      width: barStep,
      height: 88,
      class: "coord-hit",
      role: "button",
      tabindex: "0",
      "aria-label": `${index === 12 ? "12 or more" : index} neighbors; inspect one matching shell`,
      "aria-pressed": coordinationSelection === index ? "true" : "false",
    });
    hit.addEventListener("click", () => selectCoordination(index));
    hit.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectCoordination(index);
      }
    });
    coordChart.append(hit);
  });
}

function siteHash(x, y, z, salt = 0) {
  const value = Math.sin(x * 127.1 + y * 311.7 + z * 74.7 + salt * 19.19) * 43758.5453;
  return value - Math.floor(value);
}

function decorateLatticeSite(qx, qy, qz, sourceIndex = 0) {
  const scenario = scenarioSelect.value;
  const material = currentMaterial();
  let family = qx < -Math.abs(qy) * .35 ? "BC8" : qx > Math.abs(qy) * .35 ? "glass" : "IQC";
  if (scenario === "competition") family = "rocksalt";
  if (scenario === "random") family = "glass";
  if (scenario === "iqc") family = "IQC";
  if (scenario === "bc8") family = "BC8";
  const p = new THREE.Vector3(qx * .92, qy * .92, qz * .92);
  if (family === "rocksalt") {
    // Exact NaCl sites: the union is a simple-cubic grid with alternating ions.
  } else if (family === "BC8") {
    const parity = Math.round((qx + qy + qz) * 2) % 4 < 2 ? 1 : -1;
    p.add(new THREE.Vector3(parity * .13, -parity * .08, parity * .08));
  } else if (family === "IQC") {
    p.add(new THREE.Vector3(
      Math.sin((qy + qz * PHI) * 1.7) * .14,
      Math.sin((qz + qx * PHI) * 1.4) * .14,
      Math.sin((qx + qy * PHI) * 1.6) * .14,
    ));
  } else {
    p.add(new THREE.Vector3(
      (siteHash(qx, qy, qz, 1) - .5) * .28,
      (siteHash(qx, qy, qz, 2) - .5) * .28,
      (siteHash(qx, qy, qz, 3) - .5) * .28,
    ));
  }
  const speciesBias = siteHash(qx, qy, qz, 5);
  let species;
  if (scenario === "competition") species = Math.round(qx + qy + qz) % 2 === 0 ? "Na" : "Cl";
  else if (scenario === "random") species = speciesBias < .64 ? "Cu" : "Zr";
  else if (scenario === "iqc") species = speciesBias < .65 ? "Al" : speciesBias < .88 ? "Cu" : "Fe";
  else species = "Si";
  const pA = p.clone().multiplyScalar(material.spacingA / .92);
  return { p, pA, species, family, sourceIndex, q: [qx, qy, qz] };
}

function makeReferenceConfiguration() {
  const result = [];
  for (let ix = 0; ix < 6; ix++) for (let iy = 0; iy < 6; iy++) for (let iz = 0; iz < 6; iz++) {
    result.push(decorateLatticeSite(ix - 2.5, iy - 2.5, iz - 2.5, result.length));
  }
  return result.sort((a, b) => a.p.lengthSq() - b.p.lengthSq());
}

function periodicDisplacement(first, second) {
  const material = currentMaterial();
  const scale = material.spacingA / .92;
  const firstPosition = first.pA || first.p.clone().multiplyScalar(scale);
  const secondPosition = second.pA || second.p.clone().multiplyScalar(scale);
  const boxLength = 6 * material.spacingA;
  const delta = secondPosition.clone().sub(firstPosition);
  for (const axis of ["x", "y", "z"]) delta[axis] -= Math.round(delta[axis] / boxLength) * boxLength;
  return delta;
}

function localEnvironmentDescriptor(source, centerIndex) {
  const material = currentMaterial();
  const center = source[centerIndex];
  const neighbors = source.map((atom, index) => {
    if (index === centerIndex) return null;
    const vector = periodicDisplacement(center, atom);
    return { atom, vector, r: vector.length() / referenceSpacingA };
  }).filter((item) => item && item.r < 1.9).sort((a, b) => a.r - b.r);

  const features = material.elements.map((element) => center.species === element ? 2 : 0);
  const radialCenters = [.82, 1.02, 1.22, 1.48, 1.75];
  material.elements.forEach((element) => radialCenters.forEach((radialCenter) => {
    const value = neighbors.reduce((sum, neighbor) => {
      if (neighbor.atom.species !== element) return sum;
      const cutoff = .5 * (Math.cos(Math.PI * neighbor.r / 1.9) + 1);
      return sum + Math.exp(-(((neighbor.r - radialCenter) / .13) ** 2)) * cutoff;
    }, 0);
    features.push(value);
  }));

  const angular = new Array(6).fill(0);
  const firstShell = neighbors.filter((neighbor) => neighbor.r <= 1.38).slice(0, 14);
  for (let first = 0; first < firstShell.length; first++) {
    for (let second = first + 1; second < firstShell.length; second++) {
      const cosine = firstShell[first].vector.dot(firstShell[second].vector)
        / (firstShell[first].vector.length() * firstShell[second].vector.length());
      const bin = Math.min(5, Math.floor((Math.max(-1, Math.min(1, cosine)) + 1) / 2 * 6));
      angular[bin]++;
    }
  }
  const angularTotal = Math.max(1, angular.reduce((sum, value) => sum + value, 0));
  features.push(...angular.map((value) => value / angularTotal * 3));
  features.push(firstShell.length / 6, neighbors.length / 12);
  return { features, coordination: firstShell.length, shell: neighbors.slice(0, 14) };
}

function squaredDescriptorDistance(first, second) {
  return first.reduce((sum, value, index) => sum + (value - second[index]) ** 2, 0);
}

function learnLocalEnvironmentClusters(source) {
  const environments = source.map((_, index) => localEnvironmentDescriptor(source, index));
  const raw = environments.map((environment) => environment.features);
  const dimensions = raw[0].length;
  const means = new Array(dimensions).fill(0);
  raw.forEach((row) => row.forEach((value, index) => { means[index] += value / raw.length; }));
  const deviations = means.map((mean, index) => Math.sqrt(raw.reduce((sum, row) => sum + (row[index] - mean) ** 2, 0) / raw.length) || 1);
  const vectors = raw.map((row) => row.map((value, index) => (value - means[index]) / deviations[index]));
  const k = Math.min(currentMaterial().clusters, source.length);
  const medoids = [vectors.reduce((best, vector, index) => {
    const norm = squaredDescriptorDistance(vector, new Array(dimensions).fill(0));
    return norm < best.norm ? { index, norm } : best;
  }, { index: 0, norm: Infinity }).index];
  while (medoids.length < k) {
    let candidate = 0;
    let farthest = -Infinity;
    vectors.forEach((vector, index) => {
      const distance = Math.min(...medoids.map((medoid) => squaredDescriptorDistance(vector, vectors[medoid])));
      if (distance > farthest) { farthest = distance; candidate = index; }
    });
    medoids.push(candidate);
  }

  let labels = new Array(source.length).fill(0);
  for (let iteration = 0; iteration < 7; iteration++) {
    labels = vectors.map((vector) => medoids.reduce((best, medoid, cluster) => {
      const distance = squaredDescriptorDistance(vector, vectors[medoid]);
      return distance < best.distance ? { cluster, distance } : best;
    }, { cluster: 0, distance: Infinity }).cluster);
    medoids.forEach((medoid, cluster) => {
      const members = labels.map((label, index) => label === cluster ? index : -1).filter((index) => index >= 0);
      if (!members.length) return;
      medoids[cluster] = members.reduce((best, candidate) => {
        const cost = members.reduce((sum, member) => sum + squaredDescriptorDistance(vectors[candidate], vectors[member]), 0);
        return cost < best.cost ? { index: candidate, cost } : best;
      }, { index: medoid, cost: Infinity }).index;
    });
  }

  const clusters = medoids.map((medoid, cluster) => {
    const members = labels.map((label, index) => label === cluster ? index : -1).filter((index) => index >= 0);
    const spread = Math.sqrt(members.reduce((sum, index) => sum + squaredDescriptorDistance(vectors[index], vectors[medoid]), 0) / Math.max(1, members.length));
    return { oldIndex: cluster, medoid, count: members.length, spread, coordination: environments[medoid].coordination, element: source[medoid].species };
  }).sort((a, b) => b.count - a.count);
  const remap = new Map(clusters.map((cluster, index) => [cluster.oldIndex, index]));
  return { labels: labels.map((label) => remap.get(label)), clusters, environments, descriptorLength: dimensions };
}

function continuationPriority(qx, qy, qz) {
  return Math.hypot(qx, qy, qz);
}

function makeExtensionTargets() {
  const candidates = [];
  for (let ix = -9; ix < 9; ix++) for (let iy = -9; iy < 9; iy++) for (let iz = -9; iz < 9; iz++) {
    const qx = ix + .5;
    const qy = iy + .5;
    const qz = iz + .5;
    if (Math.abs(qx) <= 2.5 && Math.abs(qy) <= 2.5 && Math.abs(qz) <= 2.5) continue;
    const target = decorateLatticeSite(qx, qy, qz, candidates.length + REFERENCE_COUNT);
    target.priority = continuationPriority(qx, qy, qz);
    target.tie = siteHash(qx, qy, qz, 8);
    candidates.push(target);
  }
  candidates.sort((a, b) => a.priority - b.priority || a.tie - b.tie);
  return candidates.slice(0, EXTENSION_COUNT - REFERENCE_COUNT);
}

function frontierSector(position) {
  const direction = position.clone().normalize();
  let best = 0;
  let bestDot = -Infinity;
  BALANCE_DIRECTIONS.forEach((candidate, index) => {
    const dot = direction.dot(candidate);
    if (dot > bestDot) { bestDot = dot; best = index; }
  });
  return best;
}

function chooseFrontierAnchorIndex() {
  if (!extensionTargets.length) return -1;
  const minimumRadius = extensionTargets[0].priority;
  const window = [];
  for (let index = 0; index < extensionTargets.length && window.length < 96; index++) {
    if (extensionTargets[index].priority > minimumRadius + 1.15) break;
    const target = extensionTargets[index];
    const sector = frontierSector(target.p);
    const radialCost = target.priority - minimumRadius;
    const balanceCost = sectorCounts[sector] * .035;
    const localFitCost = target.family === "IQC" ? -.035 : target.family === "BC8" ? -.02 : 0;
    const noise = random() * .16;
    window.push({ index, score: radialCost + balanceCost + localFitCost + noise });
  }
  const bestScore = Math.min(...window.map((entry) => entry.score));
  const temperature = .13;
  const weights = window.map((entry) => Math.exp(-(entry.score - bestScore) / temperature));
  const total = weights.reduce((sum, value) => sum + value, 0);
  let draw = random() * total;
  for (let i = 0; i < window.length; i++) {
    draw -= weights[i];
    if (draw <= 0) return window[i].index;
  }
  return window.at(-1).index;
}

function frontierBatchIndices(count) {
  const anchorIndex = chooseFrontierAnchorIndex();
  if (anchorIndex < 0) return [];
  const anchor = extensionTargets[anchorIndex];
  const nearby = extensionTargets
    .map((target, index) => ({ index, distance: target.p.distanceToSquared(anchor.p), radialGap: Math.abs(target.priority - anchor.priority) }))
    .filter((entry) => entry.radialGap < 1.05)
    .sort((a, b) => a.distance - b.distance);
  return nearby.slice(0, count).map((entry) => entry.index);
}

function previewFrontierBatch(count = FRONTIER_BATCH) {
  return frontierBatchIndices(count).map((index) => extensionTargets[index]);
}

function takeFrontierBatch(batch = previewFrontierBatch(FRONTIER_BATCH)) {
  const indices = batch.map((target) => extensionTargets.indexOf(target)).filter((index) => index >= 0).sort((a, b) => b - a);
  indices.forEach((index) => extensionTargets.splice(index, 1));
  batch.forEach((target) => sectorCounts[frontierSector(target.p)]++);
  extensionIndex += batch.length;
  return batch;
}

function makeRepresentatives() {
  const reps = [];
  const scaleToScene = referenceSpacing / referenceSpacingA;
  const centers = symbolCenters();
  learnedClusters.clusters.forEach((cluster, clusterIndex) => {
    const center = centers[clusterIndex];
    const medoid = referenceAtoms[cluster.medoid];
    reps.push({ p: center.clone(), species: medoid.species, family: `C${clusterIndex + 1}`, symbolCenter: true });
    learnedClusters.environments[cluster.medoid].shell
      .filter((neighbor) => neighbor.r <= 1.38)
      .forEach((neighbor) => reps.push({
        p: center.clone().add(neighbor.vector.clone().multiplyScalar(scaleToScene)),
        species: neighbor.atom.species,
        family: `C${clusterIndex + 1}`,
      }));
  });
  return reps;
}

function symbolCenters() {
  const count = learnedClusters?.clusters.length || 1;
  return Array.from({ length: count }, (_, index) => new THREE.Vector3((index - (count - 1) / 2) * 3.15, 0, 0));
}

function clearGroup(group) {
  while (group.children.length) {
    const child = group.children.pop();
    if (![sphereGeometry, candidateGeometry].includes(child.geometry)) child.geometry?.dispose?.();
    if (Array.isArray(child.material)) child.material.forEach((material) => material.dispose?.());
    else if (![blueMaterial, greenMaterial, blueDimMaterial, greenDimMaterial, candidateMaterial, rejectedMaterial, ...elementMaterials.values(), ...dimElementMaterials.values(), ...clusterMaterials].includes(child.material)) child.material?.dispose?.();
  }
}

function buildConfinement() {
  clearGroup(confinementGroup);
  confinementGroup.rotation.set(0, 0, 0);
  const large = pipelineStage === 3;
  const material = new THREE.LineBasicMaterial({ color: COLORS.line, transparent: true, opacity: 0.36 });
  const shape = confinementSelect.value;
  if (shape === "box") {
    const dims = large ? [17, 17, 17] : [8, 8, 8];
    confinementGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(...dims)), material));
  } else if (shape === "sphere") {
    const radius = large ? 9 : 5.3;
    confinementGroup.add(new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.SphereGeometry(radius, 20, 13)), material));
  } else if (shape === "cylinder") {
    const radius = large ? 8 : 4.4;
    const length = large ? 17 : 8;
    confinementGroup.add(new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.CylinderGeometry(radius, radius, length, 22, 4, true)), material));
    confinementGroup.rotation.z = Math.PI / 2;
  } else {
    const length = large ? 8.5 : 4;
    const points = [];
    for (let ring = -length; ring <= length; ring += large ? 1 : .5) {
      const radius = (large ? 2.4 : 1.5) + (large ? .58 : .42) * Math.abs(ring);
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
  if (pipelineStage === 1 && learnedClusters) {
    learnedClusters.clusters.forEach((cluster, index) => {
      const atom = referenceAtoms[cluster.medoid];
      const geometry = cluster.coordination <= 6 ? new THREE.OctahedronGeometry(1.0)
        : cluster.coordination >= 11 ? new THREE.IcosahedronGeometry(1.12, 0)
          : new THREE.SphereGeometry(1.05, 8, 5);
      addClusterEnvelope(geometry, atom.p, CLUSTER_COLORS[index], 1 + Math.min(.22, cluster.spread * .035));
      const shellLines = [];
      referenceAtoms.forEach((neighbor) => {
        const distance = atom.p.distanceTo(neighbor.p) / referenceSpacing;
        if (neighbor !== atom && distance <= 1.38) shellLines.push(atom.p, neighbor.p);
      });
      if (shellLines.length) clusterGroup.add(new THREE.LineSegments(
        new THREE.BufferGeometry().setFromPoints(shellLines),
        new THREE.LineBasicMaterial({ color: CLUSTER_COLORS[index], transparent: true, opacity: .72 }),
      ));
    });
  } else if (pipelineStage === 2) {
    symbolCenters().forEach((center, index) => {
      const cluster = learnedClusters.clusters[index];
      const geometry = cluster.coordination <= 6 ? new THREE.OctahedronGeometry(1.22)
        : cluster.coordination >= 11 ? new THREE.IcosahedronGeometry(1.3, 0)
          : new THREE.SphereGeometry(1.25, 8, 5);
      addClusterEnvelope(geometry, center, CLUSTER_COLORS[index]);
    });
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
  stackHistory = [];
  markingCache = new Map();
  actionCache = new Map();
  currentCandidate = null;
  pendingWrong = null;
  replayIndex = 0;
  extensionIndex = 0;
  sectorCounts = new Array(BALANCE_DIRECTIONS.length).fill(0);
  nextAtomId = 1;
  liveStructuralStats = null;
  lastLiveStatsKey = "";
  coordinationSelection = null;
}

function enterPipelineStage(index, options = {}) {
  pipelineStage = Math.max(0, Math.min(3, index));
  stageElapsed = 0;
  setPlaying(false);
  resetCounters();
  rngState = 0x8f23ab17 ^ scenarioSelect.selectedIndex * 0x91e10da5 ^ confinementSelect.selectedIndex * 0x734a9d;
  referenceAtoms = makeReferenceConfiguration();
  referenceSpacing = medianNearestSpacing(referenceAtoms);
  referenceSpacingA = referenceSpacing / .92 * currentMaterial().spacingA;
  referenceStructuralStats = calculateStructuralStats(referenceAtoms, referenceSpacing);
  learnedClusters = learnLocalEnvironmentClusters(referenceAtoms);
  extensionTargets = makeExtensionTargets();
  if (pipelineStage === 0 || pipelineStage === 1) atoms = referenceAtoms.map((atom) => cloneAtom(atom));
  else if (pipelineStage === 2) atoms = makeRepresentatives().map((atom) => cloneAtom(atom));
  else atoms = [];
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
  const large = pipelineStage === 3;
  const target = new THREE.Vector3();
  controls.target.copy(target);
  camera.position.set(large ? 18 : 12.5, large ? 13 : 9.5, large ? 19 : 13.5);
  camera.updateProjectionMatrix();
}

function updateStageNarrative() {
  decisionEyebrow.textContent = "pipeline stage";
  decisionBadge.className = "badge neutral";
  const material = currentMaterial();
  const clusterCount = learnedClusters?.clusters.length || material.clusters;
  const narratives = [
    {
      eyebrow: "input · static atom coordinates", title: "Begin with the configuration we know", phase: "observed",
      caption: `${material.name}: element identities and Cartesian positions are supplied in ångströms; no environment labels are given.`, badge: "input",
      decision: material.name, copy: `The learner receives 216 element-labelled positions. ${material.cell}; measured median nearest-neighbor distance ${referenceSpacingA.toFixed(2)} Å.`,
      values: [material.elements.join(" / "), material.cell, `${referenceSpacingA.toFixed(2)} Å`, "1 configuration"],
    },
    {
      eyebrow: "learning · radial + angular environments", title: "Cluster the environments actually present", phase: `${clusterCount} learned types`,
      caption: `All ${REFERENCE_COUNT} atom-centered neighborhoods are assigned once; their overlapping shells cover the configuration. Wireframes show only the ${clusterCount} medoids.`, badge: "learn",
      decision: "Environment clusters computed", copy: "Element-resolved radial functions and a first-shell angular histogram are standardized, then clustered by deterministic k-medoids.",
      values: ["1.9a cutoff", `${learnedClusters?.descriptorLength || 0} features`, `${clusterCount} medoids`, "PBC minimum image"],
    },
    {
      eyebrow: "encoding · learned medoids with marked interfaces", title: "Encode every learned environment class", phase: `${clusterCount} symbols`,
      caption: `Each of the ${clusterCount} symbols is the actual medoid center plus its measured first-shell neighbors; no generic three-shape catalog is substituted.`, badge: "encode",
      decision: "Medoid neighborhoods encoded", copy: "One overlapping representative per learned class carries its element-labelled shell, interface marking, and bounded-domain decision state.",
      values: [`${clusterCount} medoids`, "measured shells", `${learnedClusters?.clusters.reduce((sum, cluster) => sum + cluster.coordination, 0) || 0} neighbor ports`, "finite radius"],
    },
    {
      eyebrow: "search · reconstruction flows into continuation", title: "Reconstruct, cross the observed boundary, continue", phase: "0 / 2,160",
      caption: "The search recovers 216 observed sites, then samples near-best attachments around the whole exposed frontier.", badge: "search",
      decision: "Ready for one continuous search", copy: "Local compatibility leads; a soft stochastic angular balance prevents persistent directional starvation without overriding forced moves.",
      values: ["near-best attachment", "finite marking", "soft balance", "not started"],
    },
  ];
  const item = narratives[pipelineStage];
  eventKind.textContent = ["INPUT", "LEARN", "ENCODE", "SEARCH"][pipelineStage];
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
  const action = macro ? `${target.family} frontier overlap` : `${target.species} @ ${target.family}`;
  const domain = `${target.family === "IQC" ? "icosa" : target.family === "BC8" ? "tetra" : "corona"}|${target.species}→${macro ? "frontier" : "site"}|port${macro ? 6 : 3 + (target.sourceIndex || 0) % 4}`;
  return { action, domain, n15: 4, n25: macro ? 14 : 11, minimum: .92, clearance: macro ? 2.8 : 1.4 };
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
  stackHistory.push(entry);
  if (stackHistory.length > 24) stackHistory.shift();
}

function proposeWrong(target, macro = false, proposedSources = null) {
  const direction = new THREE.Vector3(1, .55, -.35).normalize();
  const sources = proposedSources || (macro ? previewFrontierBatch(FRONTIER_BATCH) : [target]);
  const wrongAtoms = [];
  for (const source of sources) {
    const p = source.p.clone().addScaledVector(direction, macro ? .72 : .55);
    wrongAtoms.push(addAtom(p, source.species, source.family, nearestParent(p)));
  }
  pendingWrong = { atoms: wrongAtoms, target, macro };
  currentCandidate = { p: wrongAtoms[Math.floor(wrongAtoms.length / 2)].p.clone(), accepted: true };
  const state = stateForTarget(target, macro);
  acceptedDecisions++;
  appendHistory("accept", { type: "accept", depth: 1, action: `${state.action}?`, family: "speculative" });
  captionAction.textContent = `${macro ? "Overlapping cluster" : "Site"} placed speculatively; its newly exposed frontier remains unresolved.`;
  updateDecision({ eventType: "accept", accepted: true, state, resolver: "speculative branch", energy: -.18, interval: [-.3, .1] });
}

function discardSpeculativeBranch() {
  const ids = new Set(pendingWrong.atoms.map((atom) => atom.id));
  atoms = atoms.filter((atom) => !ids.has(atom.id));
  rejectedDecisions++;
  if (stackHistory.at(-1)?.family === "speculative") stackHistory.pop();
  currentCandidate = null;
  pendingWrong = null;
}

function performReconstructionEvent() {
  eventIndex++;
  if (pendingWrong) discardSpeculativeBranch();
  const target = referenceAtoms[replayIndex];
  const conflictPeriod = 28;
  if (eventIndex > 8 && eventIndex % conflictPeriod === 9) proposeWrong(target, false);
  else {
    const state = stateForTarget(target, false);
    const decision = cacheDecision(state, -.9 - (replayIndex % 7) * .03);
    const atom = addAtom(target.p, target.species, target.family, nearestParent(target.p));
    atom.observed = true;
    currentCandidate = { p: atom.p.clone(), accepted: true };
    acceptedDecisions++;
    replayIndex++;
    appendHistory(decision.reuse ? "reuse" : "accept", { type: "accept", depth: atom.depth, action: state.action, family: target.family });
    captionAction.textContent = replayIndex === REFERENCE_COUNT
      ? "The observed 216-atom window is recovered. The next placement crosses its boundary without resetting the search."
      : `${replayIndex}/${REFERENCE_COUNT} observed sites recovered; ${decision.resolver}.`;
    updateDecision({ eventType: decision.reuse ? "reuse" : "accept", accepted: true, state, resolver: decision.resolver, energy: -.9, interval: decision.interval });
  }
  rebuildWorld();
  updateUI();
}

function performExtensionEvent() {
  if (atoms.length >= EXTENSION_COUNT || extensionTargets.length === 0) {
    setPlaying(false);
    pipelineAuto = false;
    updatePipelineButtons();
    atoms.length = Math.min(atoms.length, EXTENSION_COUNT);
    phaseReadout.textContent = "2,160 / 2,160";
    captionAction.textContent = "The same search has continued from zero through the observed window to 2,160 represented atoms.";
    return;
  }
  eventIndex++;
  if (pendingWrong) discardSpeculativeBranch();
  const preview = previewFrontierBatch(FRONTIER_BATCH);
  const target = preview[0];
  const conflictPeriod = 26;
  if (eventIndex > 5 && eventIndex % conflictPeriod === 7) proposeWrong(target, true, preview);
  else {
    const batch = takeFrontierBatch(preview);
    const state = stateForTarget(target, true);
    const localEnergy = -1.15 - (Math.round(target.priority) % 3) * .08;
    const decision = cacheDecision(state, localEnergy);
    const added = [];
    batch.forEach((item) => added.push(addAtom(item.p, item.species, item.family, nearestParent(item.p))));
    const center = added.reduce((sum, atom) => sum.add(atom.p), new THREE.Vector3()).multiplyScalar(1 / added.length);
    currentCandidate = { p: center, accepted: true };
    acceptedDecisions++;
    appendHistory(decision.reuse ? "reuse" : "accept", { type: "accept", depth: added.at(-1).depth, action: state.action, family: target.family });
    captionAction.textContent = `${atoms.length.toLocaleString()}/${EXTENSION_COUNT.toLocaleString()} atoms represented; a near-best local attachment was sampled with soft angular balance.`;
    updateDecision({ eventType: decision.reuse ? "reuse" : "accept", accepted: true, state, resolver: decision.resolver, energy: localEnergy, interval: decision.interval });
  }
  rebuildWorld();
  updateUI();
}

function performEvent() {
  if (pipelineStage < 3) {
    enterPipelineStage(pipelineStage + 1, { play: pipelineAuto });
    return;
  }
  if (replayIndex < REFERENCE_COUNT) performReconstructionEvent();
  else performExtensionEvent();
}

function rebuildWorld() {
  clearGroup(atomGroup);
  clearGroup(bondGroup);
  clearGroup(frontierGroup);
  clearGroup(decisionGroup);
  const dummy = new THREE.Object3D();
  const selectedCoordination = selectedCoordinationDetail();
  const selectedIds = selectedCoordination?.ids || null;
  const addInstances = (source, material, scale = 1) => {
    if (!source.length) return;
    const mesh = new THREE.InstancedMesh(sphereGeometry, material, source.length);
    source.forEach((atom, index) => {
      dummy.position.copy(atom.p);
      const atomScale = typeof scale === "function" ? scale(atom) : scale;
      dummy.scale.setScalar((atom.seed ? .94 : 1) * atomScale);
      dummy.updateMatrix();
      mesh.setMatrixAt(index, dummy.matrix);
    });
    mesh.instanceMatrix.needsUpdate = true;
    atomGroup.add(mesh);
  };
  if (selectedIds) {
    currentMaterial().elements.forEach((symbol) => {
      addInstances(atoms.filter((atom) => atom.species === symbol && !selectedIds.has(atom.id)), getElementMaterial(symbol, true), (atom) => elementScale(atom.species) * .78);
      addInstances(atoms.filter((atom) => atom.species === symbol && selectedIds.has(atom.id)), getElementMaterial(symbol), (atom) => elementScale(atom.species) * 1.28);
    });
  } else if (pipelineStage === 1 && learnedClusters) {
    learnedClusters.clusters.forEach((_, cluster) => {
      addInstances(atoms.filter((atom, index) => learnedClusters.labels[index] === cluster), clusterMaterials[cluster], (atom) => elementScale(atom.species));
    });
  } else {
    currentMaterial().elements.forEach((symbol) => {
      addInstances(atoms.filter((atom) => atom.species === symbol), getElementMaterial(symbol), (atom) => elementScale(atom.species));
    });
  }

  if (bondToggle.checked) {
    const points = [];
    if (selectedCoordination?.center) {
      selectedCoordination.neighbors.forEach((neighbor) => points.push(selectedCoordination.center.p, neighbor.p));
    } else atoms.forEach((atom) => {
      if (atom.parent) points.push(atom.parent.p, atom.p);
    });
    if (!selectedCoordination && pipelineStage < 3 && atoms.length <= 250) {
      for (let i = 0; i < atoms.length; i++) {
        for (let j = i + 1; j < atoms.length; j++) {
          const distance = atoms[i].p.distanceToSquared(atoms[j].p);
          if (distance > .55 && distance < 1.08) points.push(atoms[i].p, atoms[j].p);
        }
      }
    }
    if (points.length) bondGroup.add(new THREE.LineSegments(
      new THREE.BufferGeometry().setFromPoints(points),
      new THREE.LineBasicMaterial({ color: selectedCoordination ? COLORS.violet : 0x87afa5, transparent: true, opacity: selectedCoordination ? .9 : .2 }),
    ));
  }

  if (frontierToggle.checked && pipelineStage >= 3) {
    const targets = replayIndex < REFERENCE_COUNT
      ? referenceAtoms.slice(replayIndex, replayIndex + 20)
      : extensionTargets.slice(0, 24);
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
      const geometry = replayIndex >= REFERENCE_COUNT ? new THREE.IcosahedronGeometry(1.15, 0) : new THREE.SphereGeometry(1.4, 15, 9);
      const domain = new THREE.LineSegments(
        new THREE.WireframeGeometry(geometry),
        new THREE.LineBasicMaterial({ color: COLORS.violet, transparent: true, opacity: .18 }),
      );
      domain.position.copy(currentCandidate.p);
      decisionGroup.add(domain);
    }
  }
  if (selectedCoordination?.center) {
    const centerMarker = new THREE.Mesh(candidateGeometry, candidateMaterial);
    centerMarker.position.copy(selectedCoordination.center.p);
    centerMarker.scale.setScalar(1.45);
    decisionGroup.add(centerMarker);
  }
}

function updateDecision(event) {
  decisionEyebrow.textContent = "current tree decision";
  const reuse = event.eventType === "reuse";
  decisionBadge.className = `badge ${reuse ? "reuse" : event.accepted ? "accept" : "reject"}`;
  decisionBadge.textContent = reuse ? "reused" : event.accepted ? "accepted" : "rejected";
  decisionTitle.textContent = `${event.state.action} ${event.accepted ? "survives" : "fails"}`;
  decisionCopy.textContent = reuse
    ? "A previously calibrated finite state resolves this placement without another exact local evaluation."
    : event.resolver === "speculative branch"
      ? "The placement is provisionally attached to the search stack while its exposed interfaces are checked."
      : "The local oracle evaluates the proposed placement and records its result under the finite geometric state.";
  actionValue.textContent = event.state.action;
  domainValue.textContent = event.state.domain;
  energyValue.textContent = event.interval ? `[${event.interval[0].toFixed(2)}, ${event.interval[1].toFixed(2)}]` : "geometric prune";
  resolverValue.textContent = event.resolver;
  eventKind.textContent = reuse ? "MARK REUSE" : event.accepted ? "ACCEPT" : "REJECT";
}

function updateUI() {
  eventCounter.textContent = String(eventIndex).padStart(4, "0");
  const material = currentMaterial();
  if (pipelineStage === 0) {
    atomLabel.textContent = "ATOMS"; atomMetric.textContent = String(REFERENCE_COUNT); atomDelta.textContent = `${material.name} · xyz in Å`;
    frontierLabel.textContent = "ELEMENTS"; frontierMetric.textContent = String(material.elements.length); frontierDelta.textContent = material.elements.join(" / ");
    oracleLabel.textContent = "LABELS GIVEN"; oracleMetric.textContent = "0"; oracleDelta.textContent = "clusters must be inferred";
    reuseLabel.textContent = "NEAREST NEIGHBOR"; reuseMetric.textContent = `${referenceSpacingA.toFixed(2)} Å`; reuseDelta.textContent = material.cell;
  } else if (pipelineStage === 1) {
    atomLabel.textContent = "ENVIRONMENTS"; atomMetric.textContent = String(REFERENCE_COUNT); atomDelta.textContent = "periodic element-aware descriptors";
    frontierLabel.textContent = "LEARNED CLUSTERS"; frontierMetric.textContent = String(learnedClusters.clusters.length); frontierDelta.textContent = "deterministic k-medoids";
    oracleLabel.textContent = "COVERAGE"; oracleMetric.textContent = "100%"; oracleDelta.textContent = `${REFERENCE_COUNT} / ${REFERENCE_COUNT} centers assigned`;
    reuseLabel.textContent = "CUTOFF"; reuseMetric.textContent = "1.9a"; reuseDelta.textContent = `${(referenceSpacingA * 1.9).toFixed(2)} Å local domain`;
  } else if (pipelineStage === 2) {
    atomLabel.textContent = "SYMBOLS"; atomMetric.textContent = String(learnedClusters.clusters.length); atomDelta.textContent = "one per learned medoid";
    frontierLabel.textContent = "SHELL ATOMS"; frontierMetric.textContent = String(atoms.length); frontierDelta.textContent = "center + measured neighbors";
    oracleLabel.textContent = "NEIGHBOR PORTS"; oracleMetric.textContent = String(learnedClusters.clusters.reduce((sum, cluster) => sum + cluster.coordination, 0)); oracleDelta.textContent = "element-labelled interfaces";
    reuseLabel.textContent = "DOMAIN"; reuseMetric.textContent = "1.38a"; reuseDelta.textContent = "first-shell encoding radius";
  } else {
    const reconstructing = replayIndex < REFERENCE_COUNT;
    stageEyebrow.textContent = reconstructing ? "search · recovering the observed window" : "search · continuing through the same frontier";
    stageTitle.textContent = reconstructing ? "Reconstruct, then keep going" : "The same search continues beyond 216 atoms";
    phaseReadout.textContent = `${atoms.length.toLocaleString()} / ${EXTENSION_COUNT.toLocaleString()}`;
    atomLabel.textContent = "REPRESENTED ATOMS";
    atomMetric.textContent = atoms.length.toLocaleString();
    atomDelta.textContent = reconstructing ? `${replayIndex}/${REFERENCE_COUNT} observed sites recovered` : `${(atoms.length / REFERENCE_COUNT).toFixed(1)}× reference scale`;
    frontierLabel.textContent = "OPEN FRONTIER";
    frontierDelta.textContent = reconstructing ? "next observed sites" : "next uncovered sites";
    oracleLabel.textContent = "ORACLE WORK";
    oracleMetric.textContent = oracleCalls > 9999 ? `${(oracleCalls / 1000).toFixed(1)}k` : String(oracleCalls);
    oracleDelta.textContent = `${acceptedDecisions + rejectedDecisions} tree decisions`;
    reuseLabel.textContent = "MARKING REUSE";
    const resolved = Math.max(1, acceptedDecisions + rejectedDecisions);
    reuseMetric.textContent = `${Math.round(grammarDecisions / resolved * 100)}%`;
    reuseDelta.textContent = `${grammarDecisions} decisions reused`;
  }
  renderStack();
  renderMarkings();
  renderStructureStats();
  renderLegend();
}

function renderLegend() {
  speciesLegend.replaceChildren();
  if (pipelineStage === 1 && learnedClusters) {
    legendHeading.textContent = "Learned environments";
    learnedClusters.clusters.forEach((cluster, index) => {
      const row = document.createElement("span");
      const swatch = document.createElement("i");
      swatch.className = "cluster-swatch";
      swatch.style.setProperty("--swatch", `#${CLUSTER_COLORS[index].toString(16).padStart(6, "0")}`);
      row.append(swatch, document.createTextNode(`C${index + 1} · ${cluster.element} · ${cluster.count}`));
      speciesLegend.appendChild(row);
    });
  } else {
    legendHeading.textContent = "Elements & state";
    currentMaterial().elements.forEach((symbol) => {
      const row = document.createElement("span");
      const swatch = document.createElement("i");
      swatch.className = "element-swatch";
      swatch.style.setProperty("--swatch", ELEMENTS[symbol].css);
      row.append(swatch, document.createTextNode(symbol));
      speciesLegend.appendChild(row);
    });
    const proposal = document.createElement("span");
    const swatch = document.createElement("i"); swatch.className = "candidate";
    proposal.append(swatch, document.createTextNode("Proposal"));
    speciesLegend.appendChild(proposal);
  }
}

function renderStack() {
  const rows = stackHistory.slice(-6).reverse();
  stackDepth.textContent = pipelineStage < 3 ? `stage ${pipelineStage + 1}/4` : `depth ${Math.max(0, ...atoms.map((atom) => atom.depth))}`;
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
    const depth = document.createElement("b"); depth.textContent = `d${entry.depth}`;
    const action = document.createElement("span"); action.textContent = `${entry.action} · ${entry.family}`;
    const state = document.createElement("em"); state.textContent = "keep";
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
  const learned = learnedClusters.clusters.map((cluster, index) => [
    `C${index + 1} · ${cluster.element} medoid`,
    `z${cluster.coordination} · σ${cluster.spread.toFixed(1)}`,
    `×${cluster.count}`,
  ]);
  const cache = policySelect.value === "marked" ? markingCache : actionCache;
  const entries = pipelineStage < 3 ? learned : [...cache.entries()].sort((a, b) => b[1].count - a[1].count).slice(0, 5).map(([key, value]) => [key, `${value.min.toFixed(1)}…${value.max.toFixed(1)}`, `×${value.count}`]);
  markCount.textContent = pipelineStage < 3 ? `${learned.length} learned` : `${cache.size} marks`;
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
  updateUI();
});
speedInput.addEventListener("input", () => { speedOutput.textContent = speedInput.value; });
[markingToggle, bondToggle, frontierToggle].forEach((input) => input.addEventListener("change", rebuildWorld));
rotateToggle.addEventListener("change", () => { controls.autoRotate = rotateToggle.checked; });
coordClearButton.addEventListener("click", () => selectCoordination(coordinationSelection));

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
