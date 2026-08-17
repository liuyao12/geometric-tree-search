import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { parseStructureText, validateStructure } from "./structure-io.js";
import { randomNomadStructure } from "./structure-database.js";
import { PERIODIC_ELEMENTS } from "./periodic-table.js";

const $ = (id) => document.getElementById(id);
const viewport = $("viewport");
const scenarioSelect = $("scenarioSelect");
const structureFileInput = $("structureFileInput");
const importStatus = $("importStatus");
const loadFixtureButton = $("loadFixtureButton");
const selectedElementsContainer = $("selectedElements");
const selectedElementCount = $("selectedElementCount");
const elementPresetButtons = [...document.querySelectorAll("[data-element-preset]")];
const periodicTableButton = $("periodicTableButton");
const periodicCompactGrid = $("periodicCompactGrid");
const periodicTablePanel = $("periodicTablePanel");
const periodicTableGrid = $("periodicTableGrid");
const periodicClearButton = $("periodicClearButton");
const periodicCloseButton = $("periodicCloseButton");
const randomMaterialButton = $("randomMaterialButton");
const databaseStatus = $("databaseStatus");
const databaseSourceLink = $("databaseSourceLink");
const confinementSelect = $("confinementSelect");
const policySelect = $("policySelect");
const stageOptionsPanel = $("stageOptionsPanel");
const stageOptionsEyebrow = $("stageOptionsEyebrow");
const stageOptionsTitle = $("stageOptionsTitle");
const stageOptionsState = $("stageOptionsState");
const clusterGeometryOptions = $("clusterGeometryOptions");
const geometryModeSelect = $("geometryModeSelect");
const geometryModeHint = $("geometryModeHint");
const geometryModeNote = $("geometryModeNote");
const poseAtlasTotal = $("poseAtlasTotal");
const poseAtlas = $("poseAtlas");
const markingTrainingOptions = $("markingTrainingOptions");
const growthSearchOptions = $("growthSearchOptions");
const markingChannelsSelect = $("markingChannelsSelect");
const markingChannelsHint = $("markingChannelsHint");
const markingReachSelect = $("markingReachSelect");
const markingReachHint = $("markingReachHint");
const markingRepresentationSelect = $("markingRepresentationSelect");
const markingRepresentationHint = $("markingRepresentationHint");
const restartMarkingButton = $("restartMarkingButton");
const saveMarkingButton = $("saveMarkingButton");
const markingConfigNote = $("markingConfigNote");
const markingLibrarySelect = $("markingLibrarySelect");
const markingLibraryCount = $("markingLibraryCount");
const trainVariantButton = $("trainVariantButton");
const primitiveGrowthButton = $("primitiveGrowthButton");
const hierarchicalGrowthButton = $("hierarchicalGrowthButton");
const growthModeNote = $("growthModeNote");
const pipelineButton = $("pipelineButton");
const playButton = $("playButton");
const playIcon = $("playIcon");
const playLabel = $("playLabel");
const stepButton = $("stepButton");
const resetButton = $("resetButton");
const speedInput = $("speedInput");
const speedOutput = $("speedOutput");
const growthDurationSelect = $("growthDurationSelect");
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
const clusterGallery = $("clusterGallery");
const viewportHint = $("viewportHint");
const unitCellBadge = $("unitCellBadge");
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
const rdfEyebrow = $("rdfEyebrow");
const rdfTitle = $("rdfTitle");
const rdfStatus = $("rdfStatus");
const rdfLegend = $("rdfLegend");
const coordChart = $("coordChart");
const coordEyebrow = $("coordEyebrow");
const coordTitle = $("coordTitle");
const coordStatus = $("coordStatus");
const coordLegend = $("coordLegend");
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
const orderClassValue = $("orderClassValue");
const structureNameValue = $("structureNameValue");
const symmetryValue = $("symmetryValue");
const confidenceValue = $("confidenceValue");
const auditNote = $("auditNote");
const recursiveStatus = $("recursiveStatus");
const hierarchyL1 = $("hierarchyL1");
const hierarchyL2 = $("hierarchyL2");
const hierarchyL3 = $("hierarchyL3");
const recursiveCurve = $("recursiveCurve");
const recursiveMark = $("recursiveMark");
const recursiveAction = $("recursiveAction");
const recursiveSpeed = $("recursiveSpeed");
const recursiveGate = $("recursiveGate");
const recursiveNote = $("recursiveNote");
const externalAudit = $("externalAudit");
const externalAuditName = $("externalAuditName");
const externalAuditHierarchy = $("externalAuditHierarchy");
const externalAuditPrecision = $("externalAuditPrecision");
const externalAuditRecall = $("externalAuditRecall");
const externalAuditReduction = $("externalAuditReduction");
const connectionAudit = $("connectionAudit");
const connectionAuditTransfer = $("connectionAuditTransfer");
const connectionAuditStates = $("connectionAuditStates");
const connectionConsensus = $("connectionConsensus");
const connectionSecondOrder = $("connectionSecondOrder");
const connectionFrontier = $("connectionFrontier");
const pipelineSteps = [...document.querySelectorAll("[data-pipeline-stage]")];
const VISIBLE_PIPELINE_STAGES = [0, 1, 3, 4];
const visiblePipelineOrdinal = (stage) => Math.max(0, VISIBLE_PIPELINE_STAGES.indexOf(stage)) + 1;
const nextVisiblePipelineStage = (stage) => VISIBLE_PIPELINE_STAGES[Math.min(
  VISIBLE_PIPELINE_STAGES.length - 1,
  Math.max(0, VISIBLE_PIPELINE_STAGES.indexOf(stage)) + 1,
)];

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
const DEFAULT_REFERENCE_COUNT = 216;
const ANALYSIS_WINDOW_COUNT = 256;
const FRONTIER_PREVIEW = 28;
const MAX_RULES_PER_PAIR = 28;
const MERGE_TOLERANCE = .24;
const COLLISION_TOLERANCE = .46;
const COMMUTING_SITE_TOLERANCE = 1e-4;
const SPATIAL_CELL = .52;
const RDF_BINS = 38;
const RDF_MAX_RADIUS = 4.2;
const COORDINATION_CUTOFF = 1.32;
const ELEMENTS = {
  H: { color: 0xf2f2f2, css: "#f2f2f2", radius: .31 },
  Li: { color: 0xcc80ff, css: "#cc80ff", radius: 1.28 },
  B: { color: 0xffb5b5, css: "#ffb5b5", radius: .84 },
  C: { color: 0x909090, css: "#909090", radius: .76 },
  N: { color: 0x3050f8, css: "#3050f8", radius: .71 },
  O: { color: 0xff0d0d, css: "#ff0d0d", radius: .66 },
  F: { color: 0x90e050, css: "#90e050", radius: .57 },
  Na: { color: 0x8f8fff, css: "#8f8fff", radius: 1.66 },
  Mg: { color: 0x8aff00, css: "#8aff00", radius: 1.41 },
  P: { color: 0xff8000, css: "#ff8000", radius: 1.07 },
  S: { color: 0xffff30, css: "#ffff30", radius: 1.05 },
  Cl: { color: 0x59d65c, css: "#59d65c", radius: 1.02 },
  K: { color: 0x8f40d4, css: "#8f40d4", radius: 2.03 },
  Ca: { color: 0x3dff00, css: "#3dff00", radius: 1.76 },
  Mn: { color: 0x9c7ac7, css: "#9c7ac7", radius: 1.39 },
  Ni: { color: 0x63d16e, css: "#63d16e", radius: 1.24 },
  Co: { color: 0xf090a0, css: "#f090a0", radius: 1.26 },
  Ti: { color: 0xb8c2cc, css: "#b8c2cc", radius: 1.60 },
  Cu: { color: 0xd98545, css: "#d98545", radius: 1.32 },
  Zr: { color: 0x79d3d6, css: "#79d3d6", radius: 1.75 },
  Al: { color: 0xb8c0c8, css: "#b8c0c8", radius: 1.21 },
  Fe: { color: 0xd45d42, css: "#d45d42", radius: 1.24 },
  Zn: { color: 0x7d80b0, css: "#7d80b0", radius: 1.22 },
  Ga: { color: 0xc28f8f, css: "#c28f8f", radius: 1.22 },
  Ge: { color: 0x668f8f, css: "#668f8f", radius: 1.20 },
  Si: { color: 0xe7b883, css: "#e7b883", radius: 1.11 },
};
const MATERIALS = {
  iceIh: { name: "ice Ih", elements: ["H", "O"], spacingA: .9572, cell: "hexagonal ice · proton-ordered fixture", order: "crystal", symmetry: "P6₃/mmc oxygen network", audit: "molecular cover + hydrogen-bond graph", molecularCover: "water", motifShellCutoff: 3.12, descriptorCutoff: 3.25, overlapDistanceCutoff: 3.35, icePolytype: "Ih", note: "The learner must discover H₂O molecules, then use overlapping water-dimer and oxygen-ring connection clusters to traverse the crystal." },
  iceIc: { name: "ice Ic", elements: ["H", "O"], spacingA: .9572, cell: "cubic ice · proton-ordered fixture", order: "crystal", symmetry: "Fd-3m oxygen network", audit: "molecular cover + hydrogen-bond graph", molecularCover: "water", motifShellCutoff: 3.12, descriptorCutoff: 3.25, overlapDistanceCutoff: 3.35, icePolytype: "Ic", note: "A cubic-ice control with the same H₂O motif but a different cluster-of-clusters connection grammar." },
  graphene: { name: "graphene monolayer", elements: ["C"], spacingA: 1.42, cell: "single hexagonal sheet", order: "crystal", symmetry: "p6/mmm layer group", audit: "2D translations + diffraction", intrinsicDimension: 2, planarLayers: [{ angle: 0, zA: 0, species: ["C", "C"] }], note: "A one-component intrinsic-2D positive control learned after arbitrary embedding in 3D." },
  hbn: { name: "aligned hBN bilayer", elements: ["B", "N"], spacingA: 1.44, cell: "aligned hexagonal sheets · 3.33 Å separation", order: "crystal", symmetry: "commensurate bilayer", audit: "2D translations + finite registry", intrinsicDimension: 2, planarLayers: [{ angle: 0, zA: -1.665, species: ["B", "N"] }, { angle: 0, zA: 1.665, species: ["B", "N"] }], note: "A commensurate bilayer whose finite interlayer registry can be represented by a bounded local marking." },
  competition: { name: "NaCl rocksalt", elements: ["Na", "Cl"], spacingA: 2.82, cell: "Fm3̅m · a = 5.640 Å", order: "crystal", symmetry: "Fm-3m · #225", audit: "space group", note: "A periodic positive control: translation is the cheap ceiling, while the learner must recover it blindly." },
  random: { name: "Cu₆₄Zr₃₆ metallic glass", elements: ["Cu", "Zr"], spacingA: 2.72, cell: "amorphous · quenched surrogate", order: "amorphous", symmetry: "no stable long-range group", audit: "local motifs + S(q)", note: "No unique continuation is implied. The target is an ensemble whose multiscale statistics match held-out large MD." },
  iqc: { name: "Al–Cu–Fe IQC approximant", elements: ["Al", "Cu", "Fe"], spacingA: 2.55, cell: "icosahedral approximant", order: "quasicrystal", symmetry: "icosahedral point symmetry", audit: "superspace + diffraction", note: "An ordinary 3D space group is insufficient; inflation, reciprocal-module, and phason statistics are required." },
  moire: { name: "30° twisted hBN bilayer", elements: ["B", "N"], spacingA: 1.44, cell: "two hexagonal sheets · 3.33 Å separation", order: "quasicrystal", symmetry: "12-fold quasiperiodic order", audit: "2D diffraction + absence of common translations", intrinsicDimension: 2, planarLayers: [{ angle: 0, zA: -1.665, species: ["B", "N"] }, { angle: Math.PI / 6, zA: 1.665, species: ["B", "N"] }], note: "Each sheet is periodic, while their 30° union has no common translation lattice." },
  bc8: { name: "silicon BC8-like network", elements: ["Si"], spacingA: 2.35, cell: "BC8 target · a = 6.636 Å", order: "crystal", symmetry: "Ia-3 · #206", audit: "space group", note: "A nontrivial crystalline control for topology, coordination, and species-preserving symmetry recovery." },
};
const RECURSIVE_BENCHMARKS = {
  iceIh: { hierarchy: [1, 6, 17], curve: [216, 1728, 13824], mark: "H₂O + dimer + ring ports", action: "known-window cover certified", speed: "37 placements / 216 atoms", gate: "pass · headless cover", status: "pass", note: "One H₂O isometry class covers every atom. Water-only search reaches just 1.39%; 115 overlapping dimer bridges and 38 oxygen-ring void boundaries restore 100% reconstruction with zero backtracking." },
  iceIc: { hierarchy: [1, 4, 12], curve: [192, 1536, 12288], mark: "H₂O + dimer + ring ports", action: "known-window cover certified", speed: "32 placements / 192 atoms", gate: "pass · headless cover", status: "pass", note: "The same molecular dictionary transfers to a distinct cubic connection grammar: 98 dimer bridges and 23 ring boundaries recover all 192 sites with zero backtracking." },
  graphene: { hierarchy: [1, 4, 16], curve: [373, 1495, 5983, 23935, 95743, 382975, 1531903], mark: "one C₂ sheet pose", action: "6 area rewrites → 1.53m", speed: "≈4× area per action", gate: "pass · 2D synthetic", status: "pass", note: "The generic planar atlas learns one C₂ motif pose and exactly predicts an unseen 1,495-atom disk." },
  hbn: { hierarchy: [2, 8, 32], curve: [746, 2990, 11960, 47840, 191360, 765440, 3061760], mark: "finite registry + pose fallback", action: "6 area rewrites → 3.06m", speed: "≈4× area per action", gate: "pass · 2D synthetic", status: "pass", note: "The registry vocabulary remains bounded for the aligned bilayer and the generic planar atlas preserves both learned sheet poses." },
  competition: { hierarchy: [7, 27, 164], curve: [216, 1728, 13824, 110592, 884736, 7077888], mark: "translation quotient", action: "5 rewrites → 7.08m", speed: "8× per action", gate: "pass · cell-free", status: "pass", note: "From 216 colored positions, the hierarchy discovers three composable translations without using the supplied cell. The recursive quotient reaches 7,077,888 implicit atoms in five actions." },
  random: { hierarchy: ["local", "—", "—"], curve: [507], mark: "no recurrent macro", action: "ensemble only", speed: "no claim", gate: "negative control", status: "limit", note: "The hierarchy correctly declines deterministic continuation. Four independently seeded amorphous controls produced zero deterministic false positives." },
  iqc: { hierarchy: [73, 17, 5], curve: [2064, 1122, 324, 78, 26, 12, 8, 4], mark: "bounded ports + exact derivations", action: "6 train levels · heldout L1 stops", speed: "1,248 / 1,248 primitive transfer", gate: "red · stationary transfer", status: "limit", note: "History-free re-clustering completely covers 2,064 grown atoms and reaches six positive train-compression levels. On three sealed held-out patches, frozen supports cover every atom and 256 of 259 first-level types replay; three absent types stop recursive transfer. The deterministic beam retains more exact derivations but still finds no stationary three-level production, so generic exponential IQC growth remains red.", external: { name: "experimental Sc–Zn IQC", hierarchy: "13 → 38 → 98", precision: "75.5% P / 55.0% R", recall: "85.4% P / 32.1% R", reduction: "57× → 185×" }, connection: { transfer: "1,248 / 1,248 atoms · 256 / 259 L1 types", states: "78 support types · 1,122 occurrences · 6 positive train levels", consensusLabel: "persistent wave / marking operating points", consensus: [["wave 1", 100.0, 3.27], ["wave 2", 34.18, 1.14], ["mark 1", 100.0, 0.07], ["mark 2", 0.0, 0.0]], secondOrderLabel: "position and species fidelity by unseen wave", secondOrder: [["wave 1", "position", 100.0, 3.27, 66.52, 2.18], ["wave 2", "position", 34.18, 1.14, 14.29, 0.47], ["mark", "normalized", 100.0, 0.07, 100.0, 0.07]], frontier: { waves: [324, 78, 26, 12, 8, 4], exact: "alternative-consistent train path", recall: "heldout primitive atoms 100% · recursive types 98.8%", full: "three missing frozen L1 types stop promotion without refit" }, macro: { stages: [["support types", 78], ["L1 quotient", 73], ["L2 quotient", 17]], safe: "heldout primitive cover · 1,248/1,248 atoms", rejected: "recursive transfer · 3/259 L1 types absent", crystal: "learned NaCl stationary control · 4,194,304 represented sites", iterated: "beam evidence · 324→78→26→12→8→4", similarity: "deep train compression passes · stationary heldout growth fails" } } },
  moire: { hierarchy: [2, 8, 32], curve: [746, 2990, 11960, 47840, 191360, 765440, 3061760], mark: "two sheet poses · Δθ = 30°", action: "6 radius doublings → 3.06m", speed: "≈4× area per action", gate: "pass · 2D synthetic", status: "pass", note: "The audited 2D atlas learns one B–N cluster isometry class in two sheet poses from 746 atoms. It exactly predicts an unseen 2,990-atom disk, preserves the 30° pose marking, and finds no common nonzero translation." },
  bc8: { hierarchy: ["pending", "pending", "pending"], curve: [], mark: "not benchmarked", action: "not benchmarked", speed: "—", gate: "real-data gate", status: "control", note: "This topology is visualized, but its audited parametric recursive benchmark remains pending." },
  imported: { hierarchy: ["live", "live", "live"], curve: [], mark: "discover from input", action: "not assumed", speed: "measure after fit", gate: "real-data gate", status: "control", note: "Imported materials are not assigned a recursive family in advance. The hierarchy must discover recurrent supports and pass a held-out continuation gate." },
};
RECURSIVE_BENCHMARKS.iqc.connection.macro.ceiling = "oracle reachability ceiling · greedy 21 maps 44.0% → pooled support vocabulary 94.2% → colored 1,000-support vocabulary 6,634/6,634 (100%) · complete representation, autonomous selection pending";
RECURSIVE_BENCHMARKS.iqc.connection.macro.selection = "autonomous first-wave marking · vote-only 3,416/8,172 (41.8%) → learned action marks 3,631/8,172 (44.4%) · +215 correct / −215 false · pair identity 3,554 · pair reliability 3,492 · geometric pair 3,446 · continuous cluster 3,540 · individual action mark remains best";
// The re-clustered hierarchy records type/occurrence retention, not emitted
// atom counts. Keep the atom curve to its one measured input cloud instead of
// presenting shrinking evidence counts as recursive material growth.
Object.assign(RECURSIVE_BENCHMARKS.iqc, {
  hierarchy: ["141 recurrent L1", "16 wave 1", "8 wave 2"],
  curve: [226, 318, 374],
  mark: "frozen recurrent macro ports",
  action: "2 autonomous macro waves",
  speed: "148 emitted · 136 correct",
  gate: "red · 91.9% P / 21.0% R",
  note: "Five raw, disjoint IQC windows learn a train-only strict-majority recurrent macro grammar. From a sixth 226-atom seed, frozen overlap and boundary ports autonomously place 16 then 8 whole clusters-of-clusters and emit 148 atoms; 136 match the sealed outer shell. This is genuine target-blind continuation, but the search stalls after two waves, precision is 91.9%, recall is 21.0%, and no stationary or exponential rule is present.",
});
Object.assign(RECURSIVE_BENCHMARKS.iqc.connection, {
  transfer: "sealed target-blind recurrent-macro execution · red",
  states: "raw/selected L1 types · 322/141 · seed macro poses 2",
});
Object.assign(RECURSIVE_BENCHMARKS.iqc.connection.frontier, {
  waves: [16, 8, 0],
  exact: "136 / 148 emitted atoms match",
  recall: "precision 91.9% · shell recall 21.0%",
  full: "train/evaluation raw IDs disjoint · target opened after execution",
});
Object.assign(RECURSIVE_BENCHMARKS.iqc.connection.macro, {
  stages: [["recurrent L1 types", 141], ["wave-1 placements", 16], ["wave-2 placements", 8]],
  safe: "whole-macro SE(3) placements · exact collision certificates",
  rejected: "12 wrong atoms · frontier exhausted",
  iterated: "self-fed placements · 16→8→0",
  similarity: "no stationary key · no finite-state cycle · no amplification",
});
const CLUSTER_COLORS = [0x55c8ff, 0xb594ff, 0x65e1bc, 0xf0c96a, 0xff7f88, 0x7ee1e8];
const clusterColor = (index) => CLUSTER_COLORS[index % CLUSTER_COLORS.length];
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
const unitCellGroup = new THREE.Group();
world.add(confinementGroup, unitCellGroup, bondGroup, atomGroup, clusterGroup, frontierGroup, decisionGroup);
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
const markingMaterials = new Map();
const candidateMaterial = new THREE.MeshBasicMaterial({ color: COLORS.violet, wireframe: true, transparent: true, opacity: 0.92 });
const rejectedMaterial = new THREE.MeshBasicMaterial({ color: COLORS.red, wireframe: true, transparent: true, opacity: 0.92 });

let pipelineStage = 0;
let pipelineAuto = false;
let stageElapsed = 0;
let playing = false;
let atoms = [];
let referenceAtoms = [];
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
let currentCandidates = [];
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
let learnedCover = null;
let detectedUnitCell = null;
let trainedMarking = null;
let sectionModel = null;
let overlapGrammar = null;
let placedClusters = [];
let frontierCandidates = [];
let frontierCandidateKeys = new Set();
let rejectedCandidateKeys = new Set();
let reconstructionCertified = false;
let reconstructionMarkingFallbacks = 0;
let atomSpatialIndex = new Map();
let trainingProgress = 0;
let markingSelection = null;
let liveOrderCache = { key: "", result: null };
let orderPrototypeLibrary = null;
let growthDeadline = 0;
let growthStartAtomCount = 0;
let growthStopReason = "";
let slowFrameSeconds = 0;
let importedStructure = null;
let selectedDatabaseElements = ["Na", "Cl"];
let markingDraft = { channels: 0, reach: 2, representation: "sites" };
let markingLibrary = [];
let activeMarkingId = null;
let hierarchyEnabled = true;
let nextMarkingId = 1;
let geometryMode = "auto";
let orientationAtlas = [];

function renderPeriodicSelection() {
  selectedElementsContainer.replaceChildren();
  selectedElementCount.textContent = String(selectedDatabaseElements.length);
  if (!selectedDatabaseElements.length) {
    const empty = document.createElement("span");
    empty.className = "selected-empty";
    empty.textContent = "Choose elements from the table";
    selectedElementsContainer.append(empty);
  }
  selectedDatabaseElements.forEach((symbol) => {
    const phase = PERIODIC_ELEMENTS.find((element) => element.symbol === symbol)?.phase || "solid";
    const atomStyle = elementRecord(symbol);
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = `selected-chip phase-${phase}`;
    chip.setAttribute("aria-label", `Remove ${symbol}`);
    chip.title = `${symbol} atom color ${atomStyle.css} · ${phase}`;
    const swatch = document.createElement("i");
    swatch.className = "atom-color-swatch";
    swatch.style.setProperty("--atom-color", atomStyle.css);
    swatch.setAttribute("aria-hidden", "true");
    const label = document.createElement("span");
    label.className = "selected-chip-symbol";
    label.textContent = symbol;
    const removeMark = document.createElement("span");
    removeMark.className = "selected-chip-remove";
    removeMark.setAttribute("aria-hidden", "true");
    removeMark.textContent = "×";
    chip.append(swatch, label, removeMark);
    chip.addEventListener("click", () => {
      selectedDatabaseElements = selectedDatabaseElements.filter((value) => value !== symbol);
      renderPeriodicSelection();
    });
    selectedElementsContainer.append(chip);
  });
  randomMaterialButton.disabled = selectedDatabaseElements.length === 0;
  periodicTableGrid.querySelectorAll("[data-element]").forEach((button) => {
    button.classList.toggle("selected", selectedDatabaseElements.includes(button.dataset.element));
    button.setAttribute("aria-pressed", String(selectedDatabaseElements.includes(button.dataset.element)));
  });
  periodicCompactGrid.querySelectorAll("[data-element]").forEach((cell) => {
    cell.classList.toggle("selected", selectedDatabaseElements.includes(cell.dataset.element));
  });
}

function setPeriodicTableOpen(open) {
  periodicTablePanel.hidden = !open;
  periodicTableButton.setAttribute("aria-expanded", String(open));
  periodicTableButton.setAttribute("aria-label", open ? "Collapse periodic table" : "Expand periodic table");
}

function buildPeriodicTable() {
  PERIODIC_ELEMENTS.forEach((element) => {
    const compactCell = document.createElement("span");
    compactCell.className = `periodic-compact-cell phase-${element.phase}`;
    compactCell.dataset.element = element.symbol;
    compactCell.style.gridColumn = element.column;
    compactCell.style.gridRow = element.row;
    periodicCompactGrid.append(compactCell);

    const button = document.createElement("button");
    button.type = "button";
    button.className = `periodic-element phase-${element.phase}`;
    button.dataset.element = element.symbol;
    button.style.gridColumn = element.column;
    button.style.gridRow = element.row;
    button.setAttribute("aria-label", `${element.symbol}, atomic number ${element.atomicNumber}, ${element.phase}`);
    button.innerHTML = `<small>${element.atomicNumber}</small>${element.symbol}`;
    button.addEventListener("click", () => {
      if (selectedDatabaseElements.includes(element.symbol)) {
        selectedDatabaseElements = selectedDatabaseElements.filter((value) => value !== element.symbol);
      } else if (selectedDatabaseElements.length < 8) {
        selectedDatabaseElements.push(element.symbol);
      } else {
        databaseStatus.className = "import-status invalid";
        databaseStatus.textContent = "Choose at most eight elements for one database query.";
      }
      renderPeriodicSelection();
    });
    periodicTableGrid.append(button);
  });
  renderPeriodicSelection();
}

function referenceCount() {
  return referenceAtoms.length || importedStructure?.atoms.length || DEFAULT_REFERENCE_COUNT;
}

function currentMaterial() {
  return scenarioSelect.value === "imported" && importedStructure ? importedStructure.material : MATERIALS[scenarioSelect.value];
}

function updateRecursiveBenchmark() {
  const benchmark = RECURSIVE_BENCHMARKS[scenarioSelect.value] || RECURSIVE_BENCHMARKS.imported;
  [hierarchyL1.textContent, hierarchyL2.textContent, hierarchyL3.textContent] = benchmark.hierarchy.map(String);
  recursiveMark.textContent = benchmark.mark;
  recursiveAction.textContent = benchmark.action;
  recursiveSpeed.textContent = benchmark.speed;
  recursiveGate.textContent = benchmark.gate;
  recursiveStatus.className = `recursive-status ${benchmark.status}`;
  recursiveStatus.textContent = benchmark.status === "limit" ? "open limit" : benchmark.status;
  recursiveNote.textContent = benchmark.note;
  externalAudit.hidden = !benchmark.external;
  if (benchmark.external) {
    externalAuditName.textContent = benchmark.external.name;
    externalAuditHierarchy.textContent = benchmark.external.hierarchy;
    externalAuditPrecision.textContent = benchmark.external.precision;
    externalAuditRecall.textContent = benchmark.external.recall;
    externalAuditReduction.textContent = benchmark.external.reduction;
  }
  connectionAudit.hidden = !benchmark.connection;
  connectionConsensus.replaceChildren();
  connectionSecondOrder.replaceChildren();
  connectionFrontier.replaceChildren();
  if (benchmark.connection) {
    connectionAuditTransfer.textContent = benchmark.connection.transfer;
    connectionAuditStates.textContent = benchmark.connection.states;
    benchmark.connection.consensus.forEach(([votes, precision, coverage]) => {
      const row = document.createElement("div");
      row.className = "consensus-row";
      row.innerHTML = `<b>${typeof votes === "number" ? `≥${votes} votes` : votes}</b><span><i style="--value:${precision}%"></i></span><em>P ${precision}% · R ${coverage}%</em>`;
      connectionConsensus.appendChild(row);
    });
    const heading = document.createElement("p");
    heading.className = "consensus-label";
    heading.textContent = benchmark.connection.secondOrderLabel || "second-order colored section · GCTS P/R versus votes P/R";
    connectionSecondOrder.appendChild(heading);
    benchmark.connection.secondOrder.forEach(([budget, policy, precision, coverage, votePrecision, voteCoverage]) => {
      const row = document.createElement("div");
      row.className = "consensus-row second-order-row";
      row.title = `${policy} section · vote-only P ${votePrecision}% / R ${voteCoverage}%`;
      row.innerHTML = `<b>${budget}</b><span><i style="--value:${precision}%"></i></span><em>GCTS ${precision}/${coverage}<small>vote ${votePrecision}/${voteCoverage}</small></em>`;
      connectionSecondOrder.appendChild(row);
    });
    const frontier = benchmark.connection.frontier;
    const frontierHeading = document.createElement("p");
    frontierHeading.className = "consensus-label";
    frontierHeading.textContent = "third-order maximum-score plateaus · regenerated actions";
    const waveStrip = document.createElement("div");
    waveStrip.className = "wave-strip";
    frontier.waves.forEach((size, index) => {
      const wave = document.createElement("span");
      wave.textContent = `${index + 1}:${size}`;
      wave.style.setProperty("--wave", `${Math.max(4, Math.sqrt(size) * 3)}px`);
      waveStrip.appendChild(wave);
    });
    const summary = document.createElement("p");
    summary.className = "frontier-summary";
    summary.innerHTML = `<strong>${frontier.exact}</strong><span>${frontier.recall}</span><small>${frontier.full}</small>`;
    connectionFrontier.append(frontierHeading, waveStrip, summary);
    if (benchmark.connection.macro) {
      const macro = benchmark.connection.macro;
      const macroHeading = document.createElement("p");
      macroHeading.className = "consensus-label macro-label";
      macroHeading.textContent = "oriented level-3 neighborhood marking · ablation";
      const macroFlow = document.createElement("div");
      macroFlow.className = "macro-audit-flow";
      macro.stages.forEach(([label, count], index) => {
        const stage = document.createElement("span");
        stage.innerHTML = `<small>${label}</small><b>${count.toLocaleString()}</b>`;
        macroFlow.appendChild(stage);
        if (index < macro.stages.length - 1) {
          const arrow = document.createElement("i");
          arrow.textContent = "→";
          macroFlow.appendChild(arrow);
        }
      });
      const verdict = document.createElement("p");
      verdict.className = "macro-verdict";
      verdict.innerHTML = `<span>${macro.safe}</span><strong>${macro.rejected}</strong>${macro.crystal ? `<small>${macro.crystal}</small>` : ""}${macro.iterated ? `<small>${macro.iterated}</small>` : ""}${macro.similarity ? `<small>${macro.similarity}</small>` : ""}${macro.ceiling ? `<small>${macro.ceiling}</small>` : ""}${macro.selection ? `<small>${macro.selection}</small>` : ""}`;
      connectionFrontier.append(macroHeading, macroFlow, verdict);
    }
  }
  recursiveCurve.replaceChildren();
  const progress = pipelineStage === 4
    ? Math.max(0, Math.min(1, atoms.length / Math.max(referenceCount(), 1) - 1))
    : 0;
  const activeLevel = benchmark.curve.length ? Math.floor(progress * (benchmark.curve.length - 1)) : -1;
  const maximumLog = Math.max(1, ...benchmark.curve.map((count) => Math.log10(Math.max(1, count))));
  benchmark.curve.forEach((count, index) => {
    const bar = document.createElement("div");
    bar.classList.toggle("active", index <= activeLevel);
    bar.style.setProperty("--bar-height", `${7 + Math.log10(Math.max(1, count)) / maximumLog * 27}px`);
    bar.title = `action ${index}: ${count.toLocaleString()} atoms represented`;
    const label = document.createElement("span");
    label.textContent = count >= 1e6 ? `${(count / 1e6).toFixed(1)}m` : count >= 1e3 ? `${Math.round(count / 1e3)}k` : String(count);
    bar.appendChild(label);
    recursiveCurve.appendChild(bar);
  });
  recursiveCurve.hidden = benchmark.curve.length === 0;
}

function importSummary(structure, validation) {
  const composition = Object.entries(validation.elementCounts).map(([element, count]) => `${element}${count}`).join(" · ");
  const periodicity = structure.pbc.map((value) => value ? "P" : "–").join("");
  const warnings = validation.warnings.length ? ` · ${validation.warnings.length} warning${validation.warnings.length === 1 ? "" : "s"}` : "";
  return `${structure.format} · ${validation.atomCount} atoms · ${composition} · PBC ${periodicity} · dₙₙ ${validation.medianNearestDistance.toFixed(3)} Å${warnings}`;
}

async function importStructureFile(file) {
  importStatus.className = "import-status";
  importStatus.textContent = `Reading ${file.name} locally…`;
  if (file.size > 8 * 1024 * 1024) throw new Error("File exceeds the 8 MB browser import limit");
  return activateImportedStructure(parseStructureText(await file.text(), file.name), file.name);
}

function activateImportedStructure(parsed, filename, statusElement = importStatus) {
  const validation = validateStructure(parsed, { maximumAtoms: 1200 });
  if (!validation.valid) throw new Error(validation.errors.join("; "));
  const elements = Object.keys(validation.elementCounts);
  importedStructure = {
    ...parsed, validation, filename,
    material: {
      name: parsed.name || filename,
      elements,
      spacingA: validation.medianNearestDistance,
      cell: parsed.cell ? `${parsed.format} cell · V=${validation.cellVolume.toFixed(2)} Å³` : `${parsed.format} · non-periodic`,
      order: "unclassified input",
      symmetry: parsed.metadata?.spaceGroupNumber
        ? `${parsed.metadata.spaceGroup || "space group"} · #${parsed.metadata.spaceGroupNumber}`
        : parsed.metadata?.spaceGroup || "not supplied",
      audit: "emergent structure audit",
      note: `Imported from ${filename}; no structure class, space group, or cluster vocabulary is supplied to growth.`,
    },
  };
  elements.forEach(elementRecord);
  const option = scenarioSelect.querySelector('option[value="imported"]');
  option.disabled = false;
  option.textContent = `Imported · ${importedStructure.material.name}`;
  scenarioSelect.value = "imported";
  statusElement.className = "import-status valid";
  statusElement.textContent = importSummary(parsed, validation);
  statusElement.title = validation.warnings.join("\n");
  orderPrototypeLibrary = null;
  enterPipelineStage(0);
  return importedStructure;
}

function growthDurationSeconds() {
  return Number(growthDurationSelect.value) || 60;
}

function growthTimeRemaining() {
  return growthDeadline ? Math.max(0, Math.ceil((growthDeadline - performance.now()) / 1000)) : 0;
}

function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}:${String(remainder).padStart(2, "0")}`;
}

function classificationSample() {
  const source = pipelineStage < 4 ? referenceAtoms : atoms;
  if (source.length <= ANALYSIS_WINDOW_COUNT) return source;
  // Preserve a physically contiguous observation window. Sampling uniformly by
  // insertion order would tear apart neighbor shells as the frontier grows.
  return [...source].sort((first, second) => first.p.lengthSq() - second.p.lengthSq()).slice(0, ANALYSIS_WINDOW_COUNT);
}

function normalizedDistributionDistance(first, second) {
  const scale = Math.max(1e-9, first.reduce((sum, value) => sum + Math.abs(value), 0));
  return first.reduce((sum, value, index) => sum + Math.abs(value - (second[index] || 0)), 0) / scale;
}

function translationClosureScore(source, basis) {
  if (!basis || source.length < 8) return 0;
  const sample = source.slice(0, Math.min(240, source.length));
  let matches = 0;
  sample.forEach((atom) => basis.forEach((vector) => {
    const forward = atom.p.clone().add(vector);
    const backward = atom.p.clone().sub(vector);
    if (source.some((candidate) => candidate.species === atom.species
      && Math.min(candidate.p.distanceTo(forward), candidate.p.distanceTo(backward)) < referenceSpacing * .15)) matches++;
  }));
  return matches / (sample.length * basis.length);
}

function inferLiveOrder() {
  const source = classificationSample();
  if (pipelineStage === 4 && source.length < 32) return {
    order: "insufficient sample", structure: "—", symmetry: "—", confidence: 0,
    note: `Waiting for at least 32 live atoms; ${source.length} are currently available.`,
  };
  const key = `${scenarioSelect.value}:${pipelineStage}:${Math.floor(source.length / 16)}:${Math.floor(atoms.length / 96)}`;
  if (liveOrderCache.key === key && liveOrderCache.result) return liveOrderCache.result;
  const stats = calculateStructuralStats(source, referenceSpacing);
  const matches = getOrderPrototypeLibrary().map((prototype) => {
    const rdfError = normalizedDistributionDistance(prototype.stats.rdf, stats.rdf);
    const coordinationError = normalizedDistributionDistance(prototype.stats.coordination, stats.coordination);
    return { ...prototype, evidenceMatch: Math.max(0, Math.min(1, 1 - .38 * rdfError - .72 * coordinationError)) };
  }).sort((first, second) => second.evidenceMatch - first.evidenceMatch);
  const best = matches[0];
  const bestCrystal = matches.find((match) => match.material.order === "crystal");
  const evidenceMatch = best.evidenceMatch;
  const translationClosure = pipelineStage === 4 && detectedUnitCell
    ? translationClosureScore(source, detectedUnitCell.basis) : 0;
  const sampleStrength = Math.max(0, Math.min(1, (source.length - 24) / 144));
  let confidence = evidenceMatch * (.48 + .52 * sampleStrength);
  const accepted = confidence >= .58;
  let order = "undetermined";
  let structure = `closest: ${best.material.name}`;
  let symmetry = "not assigned";
  if (translationClosure >= .24 && bestCrystal) {
    order = "crystal";
    structure = bestCrystal.material.name;
    symmetry = bestCrystal.material.symmetry;
    confidence = Math.max(confidence, Math.min(.98, .58 + .42 * translationClosure));
  } else if (accepted && best.material.order === "crystal") {
    order = "crystal";
    structure = best.material.name;
    symmetry = best.material.symmetry;
  } else if (accepted && best.material.order === "quasicrystal") {
    order = confidence >= .74 ? (best.id === "moire" ? "2D quasiperiodic bilayer" : "icosahedral quasicrystal") : "quasicrystal candidate";
    structure = best.material.name;
    symmetry = best.material.symmetry;
  } else if (accepted && best.material.order === "amorphous") {
    order = "amorphous solid";
    structure = best.material.name;
    symmetry = "no global space group";
  }
  const mode = pipelineStage < 4 ? "reference configuration" : "live reconstructed core";
  const result = {
    order, structure, symmetry, confidence,
    note: `${mode}: best RDF + coordination match across ${matches.length} prototypes${detectedUnitCell ? `; translation closure ${Math.round(translationClosure * 100)}%` : ""}. ${best.material.audit} remains the required independent confirmation; prototype labels and space groups are not growth inputs.`,
  };
  liveOrderCache = { key, result };
  return result;
}

function updateOrderAudit() {
  const inference = inferLiveOrder();
  orderClassValue.textContent = inference.order;
  structureNameValue.textContent = inference.structure;
  symmetryValue.textContent = inference.symmetry;
  confidenceValue.textContent = `${Math.round(inference.confidence * 100)}%`;
  auditNote.textContent = inference.note;
}

function getElementMaterial(symbol, dim = false) {
  const cache = dim ? dimElementMaterials : elementMaterials;
  if (!cache.has(symbol)) {
    const data = elementRecord(symbol);
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

function elementRecord(symbol) {
  if (ELEMENTS[symbol]) return ELEMENTS[symbol];
  let hash = 0;
  for (const character of symbol) hash = Math.imul(hash ^ character.charCodeAt(0), 0x45d9f3b);
  const color = new THREE.Color().setHSL(((hash >>> 0) % 360) / 360, .58, .62).getHex();
  ELEMENTS[symbol] = { color, css: `#${color.toString(16).padStart(6, "0")}`, radius: 1.35 };
  return ELEMENTS[symbol];
}

function markingColor(domain) {
  let hash = 2166136261;
  for (const character of domain) hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
  return new THREE.Color().setHSL(((hash >>> 0) % 360) / 360, .64, .62);
}

function getMarkingMaterial(domain, dim = false) {
  const key = `${domain}:${dim ? "dim" : "bright"}`;
  if (!markingMaterials.has(key)) {
    const color = markingColor(domain);
    markingMaterials.set(key, new THREE.MeshStandardMaterial({
      color,
      roughness: .3,
      metalness: .08,
      emissive: color,
      emissiveIntensity: dim ? .02 : .18,
      transparent: dim,
      opacity: dim ? .12 : 1,
      depthWrite: !dim,
    }));
  }
  return markingMaterials.get(key);
}

function elementScale(symbol) {
  const material = currentMaterial();
  return Math.max(.8, elementRecord(symbol).radius / material.spacingA * 2.55);
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

function calculateStructuralStats(source, spacing, periodic = false) {
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
      const normalizedDistance = periodic
        ? periodicDisplacement(source[first], source[second]).length() / referenceSpacingA
        : source[first].p.distanceTo(source[second].p) / spacing;
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
  const cell = periodic ? currentCell() : null;
  const periodicVolume = cell ? Math.abs(cell[0].dot(new THREE.Vector3().crossVectors(cell[1], cell[2]))) / (referenceSpacingA ** 3) : 0;
  const volume = Math.max(1, periodicVolume || paddedSize.x * paddedSize.y * paddedSize.z);
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
  const source = pipelineStage === 4
    ? (atoms.length > ANALYSIS_WINDOW_COUNT ? [...atoms].sort((first, second) => first.p.lengthSq() - second.p.lengthSq()).slice(0, ANALYSIS_WINDOW_COUNT) : atoms)
    : [];
  const key = `${pipelineStage}:${atoms.length}:${replayIndex}`;
  if (key !== lastLiveStatsKey) {
    liveStructuralStats = calculateStructuralStats(source, referenceSpacing);
    lastLiveStatsKey = key;
  }
  return { source, stats: liveStructuralStats || calculateStructuralStats([], referenceSpacing) };
}

function selectedCoordinationDetail() {
  if (coordinationSelection === null || pipelineStage === 2) return null;
  const structure = pipelineStage === 4
    ? currentLiveStructure()
    : { source: atoms, stats: referenceStructuralStats };
  if (!structure.source.length || !structure.stats) return null;
  const matching = structure.source.map((atom, index) => ({ atom, index }))
    .filter(({ index }) => Math.min(12, structure.stats.neighborCounts[index]) === coordinationSelection);
  if (!matching.length) return { ids: new Set(), centerIds: new Set(), neighborIds: new Set(), matchCount: 0, centers: [], neighbors: [], edges: [] };
  const centers = matching.map(({ atom }) => atom);
  const centerIds = new Set(centers.map((atom) => atom.id));
  const neighbors = [];
  const neighborIds = new Set();
  const edges = [];
  const edgeKeys = new Set();
  matching.forEach(({ atom: center, index }) => {
    structure.stats.neighborLists[index].forEach((neighborIndex) => {
      const neighbor = structure.source[neighborIndex];
      if (!neighborIds.has(neighbor.id)) neighbors.push(neighbor);
      neighborIds.add(neighbor.id);
      const key = center.id < neighbor.id ? `${center.id}:${neighbor.id}` : `${neighbor.id}:${center.id}`;
      if (!edgeKeys.has(key)) {
        edgeKeys.add(key);
        edges.push([center, neighbor]);
      }
    });
  });
  return {
    ids: new Set([...centerIds, ...neighborIds]),
    centerIds,
    neighborIds,
    matchCount: matching.length,
    centers,
    neighbors,
    edges,
  };
}

function selectCoordination(value) {
  if (pipelineStage === 2 || (pipelineStage === 4 && replayIndex === 0)) return;
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

function setChartLegend(container, entries) {
  container.replaceChildren();
  entries.forEach(([className, label]) => {
    const span = document.createElement("span");
    span.className = className;
    span.textContent = label;
    container.appendChild(span);
  });
}

function renderTrainingStats() {
  const point = currentTrainingPoint();
  const visibleCurve = sectionModel.curve.slice(0, trainingProgress);
  rdfEyebrow.textContent = "GCTS training curve";
  rdfTitle.textContent = "section mismatch";
  rdfStatus.textContent = `${point.samples}/${referenceCount()} samples · ${point.fitSamples} fit / ${point.holdoutSamples} holdout`;
  coordEyebrow.textContent = "learned section atlas";
  coordTitle.textContent = "connection-port strength";
  coordStatus.textContent = `support R = ${sectionModel.support.toFixed(1)}a · rank ${sectionModel.channels}`;
  coordClearButton.hidden = true;
  rdfChart.setAttribute("aria-label", "Training and held-out mismatch of local GCTS marking sections");
  coordChart.setAttribute("aria-label", "Directional connection-port strength of each learned cluster marking section");

  rdfChart.replaceChildren();
  drawChartFrame(rdfChart, "samples", "loss");
  [0, .25, .5, .75, 1].map((fraction) => Math.round(referenceCount() * fraction)).forEach((tick) => {
    const x = 29 + tick / referenceCount() * 323;
    rdfChart.append(svgNode("text", { x, y: 108, class: "chart-label", "text-anchor": "middle" }, String(tick)));
  });
  const maximum = Math.max(.001, sectionModel.initialPoint.trainLoss, sectionModel.initialPoint.validationLoss);
  const curvePath = (field) => visibleCurve.map((entry, index) => {
    const x = 29 + entry.samples / referenceCount() * 323;
    const y = 96 - Math.min(1, entry[field] / maximum) * 84;
    return `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(" ");
  if (visibleCurve.length) {
    rdfChart.append(svgNode("path", { d: curvePath("trainLoss"), class: "chart-known" }));
    rdfChart.append(svgNode("path", { d: curvePath("validationLoss"), class: "chart-live" }));
  }
  setChartLegend(rdfLegend, [["known-key", "overlap + port fit"], ["live-key", "held-out mismatch"]]);

  coordChart.replaceChildren();
  drawChartFrame(coordChart, "cluster section", "norm");
  const amplitudes = learnedClusters.clusters.map((_, cluster) => Math.sqrt(currentSectionCoefficients(cluster).reduce((sum, value) => sum + value ** 2, 0)));
  const maximumAmplitude = Math.max(.01, ...amplitudes);
  const barStep = 323 / amplitudes.length;
  amplitudes.forEach((amplitude, index) => {
    const height = amplitude / maximumAmplitude * 84;
    const key = `m_C${index + 1}`;
    const color = `#${markingColor(key).getHexString()}`;
    coordChart.append(svgNode("rect", {
      x: 29 + index * barStep + 2,
      y: 96 - height,
      width: Math.max(2, barStep - 4),
      height,
      fill: color,
      opacity: markingSelection && markingSelection !== key ? .18 : .72,
    }));
    coordChart.append(svgNode("text", { x: 29 + (index + .5) * barStep, y: 108, class: "chart-label", "text-anchor": "middle" }, `C${index + 1}`));
  });
  setChartLegend(coordLegend, [["known-key", "type color = compatible connection port"], ["live-key", "red lobe = absent / failed port"]]);
}

function renderStructureStats() {
  if (!referenceStructuralStats) return;
  if (pipelineStage === 3) {
    renderTrainingStats();
    return;
  }
  rdfEyebrow.textContent = "finite-window RDF";
  rdfTitle.textContent = "g(r / a)";
  coordEyebrow.textContent = "first-shell coordination";
  coordTitle.innerHTML = "P(z), r<sub>c</sub> = 1.32a";
  rdfChart.setAttribute("aria-label", "Radial distribution function for known positions and live reconstruction");
  coordChart.setAttribute("aria-label", "Coordination number distribution for known positions and live reconstruction");
  const liveWindowLabel = pipelineStage === 4 && atoms.length > ANALYSIS_WINDOW_COUNT ? "live central analysis window" : "live reconstruction";
  setChartLegend(rdfLegend, [["known-key", "known positions"], ["live-key", liveWindowLabel]]);
  setChartLegend(coordLegend, [["known-key", "known positions"], ["live-key", liveWindowLabel], ["", "click z to show all current shells"]]);
  const { stats: live } = currentLiveStructure();
  rdfStatus.textContent = `known ${referenceCount()} · ${liveWindowLabel} ${live.count}`;
  const selected = selectedCoordinationDetail();
  coordStatus.textContent = coordinationSelection === null
    ? `mean z ${referenceStructuralStats.meanCoordination.toFixed(1)} · ${live.count ? live.meanCoordination.toFixed(1) : "—"}`
    : `${coordinationSelection === 12 ? "z≥12" : `z=${coordinationSelection}`} · ${selected?.matchCount || 0} centers · ${selected?.edges.length || 0} links`;
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
      "aria-label": `${index === 12 ? "12 or more" : index} neighbors; show all matching shells`,
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

function motifShellCutoff() {
  return currentMaterial().motifShellCutoff || 1.38;
}

function descriptorCutoff() {
  return currentMaterial().descriptorCutoff || 1.9;
}

function overlapDistanceCutoff() {
  return currentMaterial().overlapDistanceCutoff || 2.35;
}

function cartesianFromFractional(fractional, cell) {
  return new THREE.Vector3()
    .addScaledVector(cell[0], fractional[0])
    .addScaledVector(cell[1], fractional[1])
    .addScaledVector(cell[2], fractional[2]);
}

function iceDefinition(polytype) {
  if (polytype === "Ic") {
    const a = 6.36;
    return {
      primitive: [new THREE.Vector3(a, 0, 0), new THREE.Vector3(0, a, 0), new THREE.Vector3(0, 0, a)],
      repeats: [2, 2, 2],
      basis: [[0,0,0], [0,.5,.5], [.5,0,.5], [.5,.5,0], [.25,.25,.25], [.25,.75,.75], [.75,.25,.75], [.75,.75,.25]],
    };
  }
  const a = 4.518, c = 7.357, u = 3 / 8;
  return {
    primitive: [new THREE.Vector3(a, 0, 0), new THREE.Vector3(-a / 2, Math.sqrt(3) * a / 2, 0), new THREE.Vector3(0, 0, c)],
    repeats: [3, 3, 2],
    basis: [[0,0,0], [2/3,1/3,.5], [0,0,u], [2/3,1/3,.5+u]],
  };
}

function makeIceReferenceConfiguration(polytype) {
  const definition = iceDefinition(polytype);
  const cell = definition.primitive.map((vector, axis) => vector.clone().multiplyScalar(definition.repeats[axis]));
  const oxygen = [];
  for (let i = 0; i < definition.repeats[0]; i++) for (let j = 0; j < definition.repeats[1]; j++) for (let k = 0; k < definition.repeats[2]; k++) {
    definition.basis.forEach((basis, basisIndex) => {
      const fractional = [(i + basis[0]) / definition.repeats[0], (j + basis[1]) / definition.repeats[1], (k + basis[2]) / definition.repeats[2]];
      oxygen.push({ pA: cartesianFromFractional(fractional, cell), fractional, address: [i, j, k, basisIndex] });
    });
  }
  const minimumImage = (first, second) => {
    const fractional = second.fractional.map((value, axis) => {
      const delta = value - first.fractional[axis];
      return delta - Math.round(delta);
    });
    return cartesianFromFractional(fractional, cell);
  };
  const neighbors = oxygen.map((atom, index) => oxygen.map((candidate, other) => other === index ? null : {
    other, vector: minimumImage(atom, candidate),
  }).filter(Boolean).sort((first, second) => first.vector.lengthSq() - second.vector.lengthSq()).slice(0, 4));
  const records = oxygen.map((atom, index) => ({ pA: atom.pA.clone(), species: "O", family: `ice-${polytype}`, molecule: index, q: atom.address.slice(0, 3) }));
  oxygen.forEach((atom, index) => {
    const ordered = neighbors[index].slice().sort((first, second) => first.vector.z - second.vector.z || first.vector.y - second.vector.y || first.vector.x - second.vector.x);
    const offset = (atom.address[0] + 2 * atom.address[1] + atom.address[2] + atom.address[3]) % 4;
    [ordered[offset], ordered[(offset + 1) % 4]].forEach((neighbor) => {
      records.push({ pA: atom.pA.clone().add(neighbor.vector.clone().setLength(.9572)), species: "H", family: `ice-${polytype}`, molecule: index, q: atom.address.slice(0, 3) });
    });
  });
  const center = records.reduce((sum, atom) => sum.add(atom.pA), new THREE.Vector3()).multiplyScalar(1 / records.length);
  const scale = .92 / .9572;
  return records.map((atom, sourceIndex) => ({ ...atom, p: atom.pA.clone().sub(center).multiplyScalar(scale), sourceIndex }))
    .sort((first, second) => first.p.lengthSq() - second.p.lengthSq() || first.species.localeCompare(second.species));
}

function makeSyntheticReferenceSite(qx, qy, qz, sourceIndex = 0, scenario = scenarioSelect.value) {
  const material = MATERIALS[scenario];
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

function makeReferenceConfiguration(scenario = scenarioSelect.value) {
  if (scenario === "imported" && importedStructure) {
    const center = importedStructure.atoms.reduce((sum, atom) => sum.add(new THREE.Vector3(...atom.position)), new THREE.Vector3())
      .multiplyScalar(1 / importedStructure.atoms.length);
    const sceneScale = .92 / importedStructure.validation.medianNearestDistance;
    return importedStructure.atoms.map((atom, sourceIndex) => {
      const pA = new THREE.Vector3(...atom.position);
      return {
        pA, p: pA.clone().sub(center).multiplyScalar(sceneScale), species: atom.species,
        family: "imported", sourceIndex, occupancy: atom.occupancy ?? 1,
      };
    }).sort((first, second) => first.p.lengthSq() - second.p.lengthSq());
  }
  if (MATERIALS[scenario]?.icePolytype) return makeIceReferenceConfiguration(MATERIALS[scenario].icePolytype);
  if (MATERIALS[scenario]?.intrinsicDimension === 2) return makePlanarReferenceConfiguration(scenario);
  const result = [];
  for (let ix = 0; ix < 6; ix++) for (let iy = 0; iy < 6; iy++) for (let iz = 0; iz < 6; iz++) {
    result.push(makeSyntheticReferenceSite(ix - 2.5, iy - 2.5, iz - 2.5, result.length, scenario));
  }
  return result.sort((a, b) => a.p.lengthSq() - b.p.lengthSq());
}

function makePlanarReferenceConfiguration(scenario = "moire") {
  const result = [];
  const material = MATERIALS[scenario];
  const bondScene = .92;
  const lattice = Math.sqrt(3) * bondScene;
  const a1 = new THREE.Vector2(lattice, 0);
  const a2 = new THREE.Vector2(.5 * lattice, .5 * Math.sqrt(3) * lattice);
  const basis = new THREE.Vector2().addVectors(a1, a2).multiplyScalar(1 / 3);
  const layers = material.planarLayers || [{ angle: 0, zA: -1.665, species: ["B", "N"] }, { angle: Math.PI / 6, zA: 1.665, species: ["B", "N"] }];
  layers.forEach(({ angle, zA, species: layerSpecies }, layer) => {
    const z = zA / material.spacingA * bondScene;
    const cosine = Math.cos(angle);
    const sine = Math.sin(angle);
    for (let i = -12; i <= 12; i++) for (let j = -12; j <= 12; j++) {
      const origin = new THREE.Vector2(i * a1.x + j * a2.x, i * a1.y + j * a2.y);
      [[new THREE.Vector2(), layerSpecies[0]], [basis, layerSpecies[1]]].forEach(([offset, species], basisIndex) => {
        const raw = origin.clone().add(offset);
        const p = new THREE.Vector3(cosine * raw.x - sine * raw.y,
          sine * raw.x + cosine * raw.y, z);
        const pA = p.clone().multiplyScalar(material.spacingA / bondScene);
        result.push({ p, pA, species, family: scenario, layer,
          sourceIndex: result.length, q: [i, j, layer + basisIndex * .25] });
      });
    }
  });
  return result.sort((first, second) => first.p.x ** 2 + first.p.y ** 2 - second.p.x ** 2 - second.p.y ** 2
    || first.layer - second.layer || first.species.localeCompare(second.species)).slice(0, DEFAULT_REFERENCE_COUNT);
}

function currentCell() {
  if (currentMaterial().intrinsicDimension === 2) return null;
  if (currentMaterial().icePolytype) {
    const definition = iceDefinition(currentMaterial().icePolytype);
    return definition.primitive.map((vector, axis) => vector.clone().multiplyScalar(definition.repeats[axis]));
  }
  if (scenarioSelect.value === "imported" && importedStructure?.cell) {
    return importedStructure.cell.map((vector) => new THREE.Vector3(...vector));
  }
  const length = 6 * currentMaterial().spacingA;
  return [new THREE.Vector3(length, 0, 0), new THREE.Vector3(0, length, 0), new THREE.Vector3(0, 0, length)];
}

function currentPbc() {
  if (geometryMode === "module" || geometryMode === "offlattice") return [false, false, false];
  if (geometryMode === "lattice") return currentCell() ? [true, true, true] : [false, false, false];
  if (currentMaterial().intrinsicDimension === 2) return [false, false, false];
  return scenarioSelect.value === "imported" && importedStructure ? importedStructure.pbc : [true, true, true];
}

function getOrderPrototypeLibrary() {
  if (orderPrototypeLibrary) return orderPrototypeLibrary;
  orderPrototypeLibrary = Object.entries(MATERIALS).map(([id, material]) => {
    const source = makeReferenceConfiguration(id);
    const spacing = medianNearestSpacing(source);
    return { id, material, stats: calculateStructuralStats(source, spacing) };
  });
  return orderPrototypeLibrary;
}

function periodicDisplacement(first, second) {
  const material = currentMaterial();
  const scale = material.spacingA / .92;
  const firstPosition = first.pA || first.p.clone().multiplyScalar(scale);
  const secondPosition = second.pA || second.p.clone().multiplyScalar(scale);
  const delta = secondPosition.clone().sub(firstPosition);
  const cell = currentCell();
  const pbc = currentPbc();
  if (cell && pbc.some(Boolean)) {
    const cellMatrix = new THREE.Matrix3().set(
      cell[0].x, cell[1].x, cell[2].x,
      cell[0].y, cell[1].y, cell[2].y,
      cell[0].z, cell[1].z, cell[2].z,
    );
    const fractional = delta.clone().applyMatrix3(cellMatrix.clone().invert());
    ["x", "y", "z"].forEach((axis, index) => { if (pbc[index]) fractional[axis] -= Math.round(fractional[axis]); });
    return fractional.applyMatrix3(cellMatrix);
  }
  return delta;
}

function inferTranslationCell(source) {
  if (scenarioSelect.value === "imported" && importedStructure?.cell && currentPbc().every(Boolean)) {
    const scale = referenceSpacing / referenceSpacingA;
    return { basis: currentCell().map((vector) => vector.multiplyScalar(scale)), source: "reported periodic cell" };
  }
  const sample = source.slice(0, Math.min(72, source.length));
  const candidates = new Map();
  for (let first = 0; first < sample.length; first++) for (let second = first + 1; second < sample.length; second++) {
    if (sample[first].species !== sample[second].species) continue;
    let vector = sample[second].p.clone().sub(sample[first].p);
    const length = vector.length();
    if (length < referenceSpacing * 1.05 || length > referenceSpacing * 3.2) continue;
    const components = [vector.x, vector.y, vector.z];
    const leading = components.find((value) => Math.abs(value) > .05);
    if (leading < 0) vector.multiplyScalar(-1);
    const key = [vector.x, vector.y, vector.z].map((value) => Math.round(value / (referenceSpacing * .04))).join(":");
    if (!candidates.has(key)) candidates.set(key, vector);
  }
  const scored = [...candidates.values()].map((vector) => {
    let supported = 0;
    sample.forEach((atom) => {
      const target = atom.p.clone().add(vector);
      if (source.some((candidate) => candidate.species === atom.species && candidate.p.distanceTo(target) < referenceSpacing * .12)) supported++;
    });
    return { vector, support: supported / sample.length };
  }).filter((candidate) => candidate.support >= .42)
    .sort((first, second) => first.vector.lengthSq() - second.vector.lengthSq() || second.support - first.support)
    .slice(0, 24);
  let best = null;
  for (let i = 0; i < scored.length; i++) for (let j = i + 1; j < scored.length; j++) for (let k = j + 1; k < scored.length; k++) {
    const volume = Math.abs(scored[i].vector.dot(new THREE.Vector3().crossVectors(scored[j].vector, scored[k].vector)));
    if (volume < referenceSpacing ** 3 * .35) continue;
    const score = volume / (scored[i].support * scored[j].support * scored[k].support);
    if (!best || score < best.score) best = { score, basis: [scored[i].vector.clone(), scored[j].vector.clone(), scored[k].vector.clone()] };
  }
  return best ? { basis: best.basis, source: "translation consensus" } : null;
}

function buildDetectedUnitCell() {
  clearGroup(unitCellGroup);
  unitCellBadge.hidden = true;
  if (pipelineStage !== 4 || !detectedUnitCell) return;
  const inference = inferLiveOrder();
  if (inference.order.includes("quasicrystal") || inference.order === "amorphous solid") return;
  const [a, b, c] = detectedUnitCell.basis;
  const centroid = atoms.slice(0, Math.min(atoms.length, 500)).reduce((sum, atom) => sum.add(atom.p), new THREE.Vector3())
    .multiplyScalar(1 / Math.max(1, Math.min(atoms.length, 500)));
  const origin = centroid.clone().addScaledVector(a, -.5).addScaledVector(b, -.5).addScaledVector(c, -.5);
  const vertices = [0, 1, 2, 3, 4, 5, 6, 7].map((mask) => origin.clone()
    .addScaledVector(a, mask & 1 ? 1 : 0)
    .addScaledVector(b, mask & 2 ? 1 : 0)
    .addScaledVector(c, mask & 4 ? 1 : 0));
  const points = [];
  [[0,1],[0,2],[0,4],[1,3],[1,5],[2,3],[2,6],[3,7],[4,5],[4,6],[5,7],[6,7]].forEach(([first, second]) => points.push(vertices[first], vertices[second]));
  unitCellGroup.add(new THREE.LineSegments(
    new THREE.BufferGeometry().setFromPoints(points),
    new THREE.LineBasicMaterial({ color: COLORS.mint, transparent: true, opacity: .88, depthTest: false }),
  ));
  unitCellBadge.hidden = false;
  const classified = inference.order === "crystal";
  unitCellBadge.textContent = classified ? "unit cell detected" : "unit cell candidate";
  unitCellBadge.title = `${classified ? inference.symmetry : "awaiting live crystal classification"} · ${detectedUnitCell.source}`;
}

function localEnvironmentDescriptor(source, centerIndex) {
  const material = currentMaterial();
  const descriptorRadius = descriptorCutoff();
  const shellRadius = motifShellCutoff();
  const center = source[centerIndex];
  const neighbors = source.map((atom, index) => {
    if (index === centerIndex) return null;
    const vector = periodicDisplacement(center, atom);
    return { atom, vector, r: vector.length() / referenceSpacingA };
  }).filter((item) => item && item.r < descriptorRadius).sort((a, b) => a.r - b.r);

  const features = material.elements.map((element) => center.species === element ? 2 : 0);
  const radialCenters = descriptorRadius > 2.2 ? [.82, 1.02, 1.22, 1.48, 1.82, 2.35, 2.88] : [.82, 1.02, 1.22, 1.48, 1.75];
  material.elements.forEach((element) => radialCenters.forEach((radialCenter) => {
    const value = neighbors.reduce((sum, neighbor) => {
      if (neighbor.atom.species !== element) return sum;
      const cutoff = .5 * (Math.cos(Math.PI * neighbor.r / descriptorRadius) + 1);
      return sum + Math.exp(-(((neighbor.r - radialCenter) / .13) ** 2)) * cutoff;
    }, 0);
    features.push(value);
  }));

  const angular = new Array(6).fill(0);
  const firstShell = neighbors.filter((neighbor) => neighbor.r <= shellRadius).slice(0, 20);
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
  return { features, coordination: firstShell.length, shell: neighbors.slice(0, 20) };
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
  const maximumK = Math.min(10, source.length);
  const minimumK = 2;
  const complexityFloor = Math.min(maximumK, currentMaterial().elements.length + 2);
  const seedMedoids = [vectors.reduce((best, vector, index) => {
    const norm = squaredDescriptorDistance(vector, new Array(dimensions).fill(0));
    return norm < best.norm ? { index, norm } : best;
  }, { index: 0, norm: Infinity }).index];
  while (seedMedoids.length < maximumK) {
    let candidate = 0;
    let farthest = -Infinity;
    vectors.forEach((vector, index) => {
      const distance = Math.min(...seedMedoids.map((medoid) => squaredDescriptorDistance(vector, vectors[medoid])));
      if (distance > farthest) { farthest = distance; candidate = index; }
    });
    seedMedoids.push(candidate);
  }
  const selectionCurve = [];
  for (let candidateK = minimumK; candidateK <= maximumK; candidateK++) {
    const medoidSubset = seedMedoids.slice(0, candidateK);
    const cost = vectors.reduce((sum, vector) => sum + Math.min(...medoidSubset.map((medoid) => squaredDescriptorDistance(vector, vectors[medoid]))), 0) / vectors.length;
    selectionCurve.push({ k: candidateK, cost });
  }
  let k = maximumK;
  for (let index = 0; index < selectionCurve.length - 1; index++) {
    const current = selectionCurve[index];
    const next = selectionCurve[index + 1];
    if (current.cost < 1e-8 || (current.k >= complexityFloor && (current.cost - next.cost) / Math.max(1e-8, current.cost) < .04)) {
      k = current.k;
      break;
    }
  }
  const medoids = seedMedoids.slice(0, k);

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
  return { labels: labels.map((label) => remap.get(label)), clusters, environments, descriptorLength: dimensions, selectionCurve, selectedK: k };
}

function directionalPoseDescriptor(shell) {
  const values = [];
  currentMaterial().elements.forEach((element) => BALANCE_DIRECTIONS.forEach((axis) => {
    const value = shell.reduce((sum, neighbor) => {
      const species = neighbor.atom?.species || neighbor.species;
      if (species !== element || neighbor.vector.lengthSq() < 1e-12) return sum;
      const direction = neighbor.vector.clone().normalize();
      const radial = Math.exp(-(((neighbor.r - 1) / .42) ** 2));
      return sum + radial * Math.max(0, direction.dot(axis)) ** 6;
    }, 0);
    values.push(value);
  }));
  const norm = Math.sqrt(values.reduce((sum, value) => sum + value * value, 0)) || 1;
  return values.map((value) => value / norm);
}

function orientationDescriptor(environment) {
  return directionalPoseDescriptor(environment.shell.filter((neighbor) => neighbor.r <= motifShellCutoff()));
}

function supportOrientationDescriptor(placement) {
  const center = referenceAtoms[placement.center];
  return directionalPoseDescriptor(placement.support.filter((index) => index !== placement.center).map((index) => {
    const vector = periodicDisplacement(center, referenceAtoms[index]);
    return { species: referenceAtoms[index].species, vector, r: vector.length() / referenceSpacingA };
  }));
}

function orientationDistance(first, second) {
  return Math.sqrt(first.reduce((sum, value, index) => sum + (value - second[index]) ** 2, 0));
}

function learnOrientationAtlas() {
  if (!learnedClusters) return [];
  if (learnedCover?.types) return learnedCover.types.map((cluster, clusterIndex) => {
    const placements = learnedCover.placements.filter((placement) => placement.type === cluster.type);
    const representatives = [];
    const populations = [];
    placements.forEach((placement) => {
      const descriptor = supportOrientationDescriptor(placement);
      let pose = representatives.findIndex((candidate) => orientationDistance(candidate, descriptor) <= .16);
      if (pose < 0) { pose = representatives.length; representatives.push(descriptor); populations.push(0); }
      populations[pose]++;
    });
    return { cluster: clusterIndex, element: cluster.element, occurrences: placements.length,
      orientations: representatives.length, populations: populations.sort((first, second) => second - first) };
  });
  return learnedClusters.clusters.map((cluster, clusterIndex) => {
    const occurrences = learnedClusters.labels.map((label, index) => label === clusterIndex ? index : -1)
      .filter((index) => index >= 0);
    const representatives = [];
    const populations = [];
    occurrences.forEach((index) => {
      const descriptor = orientationDescriptor(learnedClusters.environments[index]);
      let pose = representatives.findIndex((candidate) => orientationDistance(candidate, descriptor) <= .16);
      if (pose < 0) {
        pose = representatives.length;
        representatives.push(descriptor);
        populations.push(0);
      }
      populations[pose]++;
    });
    return {
      cluster: clusterIndex,
      element: cluster.element,
      occurrences: occurrences.length,
      orientations: representatives.length,
      populations: populations.sort((first, second) => second - first),
    };
  });
}

function automaticMarkingChannels() {
  return Math.max(3, ...orientationAtlas.map((entry) => recommendedChannelsForCluster(entry.cluster, entry.orientations)));
}

function clusterPortRank(cluster) {
  if (!overlapGrammar) return 1;
  return Math.max(1, new Set(overlapGrammar.rules
    .filter((rule) => rule.from === cluster)
    .map((rule) => `${rule.to}:${Math.round((rule.meanShared || 0) * 2)}`)).size);
}

function recommendedChannelsForCluster(cluster, poses) {
  const portRank = clusterPortRank(cluster);
  // The fields form a symmetry-aware local basis; they are not one-hot pose
  // labels. Pose and port orbit complexity therefore enter logarithmically.
  return Math.min(12, Math.max(3, 2
    + Math.ceil(Math.log2(Math.max(1, poses) + 1))
    + Math.min(3, Math.ceil(Math.log2(portRank + 1)))));
}

function buildWaterClusterCover(source) {
  const oxygen = source.map((atom, index) => atom.species === "O" ? index : -1).filter((index) => index >= 0);
  const hydrogen = source.map((atom, index) => atom.species === "H" ? index : -1).filter((index) => index >= 0);
  const waters = [];
  const owner = new Map();
  oxygen.forEach((oxygenIndex) => {
    const bonded = hydrogen.map((index) => ({ index, distance: periodicDisplacement(source[oxygenIndex], source[index]).length() }))
      .filter((entry) => entry.distance < 1.16).sort((first, second) => first.distance - second.distance).slice(0, 2).map((entry) => entry.index);
    if (bonded.length !== 2) return;
    const waterIndex = waters.length;
    const support = [oxygenIndex, ...bonded];
    waters.push({ center: oxygenIndex, support, type: 0, residual: false, kind: "H₂O molecule" });
    support.forEach((atomIndex) => owner.set(atomIndex, waterIndex));
  });

  const bridgePairs = new Set();
  waters.forEach((water, waterIndex) => water.support.slice(1).forEach((proton) => {
    const acceptor = oxygen.filter((index) => index !== water.center).map((index) => ({
      index, distance: periodicDisplacement(source[proton], source[index]).length(),
    })).sort((first, second) => first.distance - second.distance)[0];
    if (!acceptor || acceptor.distance > 2.25) return;
    const other = owner.get(acceptor.index);
    if (!Number.isInteger(other) || other === waterIndex) return;
    bridgePairs.add([Math.min(waterIndex, other), Math.max(waterIndex, other)].join(":"));
  }));
  const bridges = [...bridgePairs].map((key) => key.split(":").map(Number)).map(([first, second]) => ({
    center: waters[first].center,
    support: [...new Set([...waters[first].support, ...waters[second].support])],
    type: 1, residual: false, kind: "H₂O···H₂O bridge", waterPair: [first, second],
  }));

  const adjacency = Array.from({ length: waters.length }, () => new Set());
  bridges.forEach(({ waterPair: [first, second] }) => { adjacency[first].add(second); adjacency[second].add(first); });
  const ringKeys = new Set();
  adjacency.forEach((_, start) => {
    const stack = [[start, [start]]];
    while (stack.length) {
      const [current, path] = stack.pop();
      if (path.length === 6) {
        if (adjacency[current].has(start)) ringKeys.add(path.slice().sort((a, b) => a - b).join(":"));
        continue;
      }
      adjacency[current].forEach((neighbor) => {
        if (neighbor <= start || path.includes(neighbor)) return;
        stack.push([neighbor, [...path, neighbor]]);
      });
    }
  });
  const gaps = [...ringKeys].map((key) => key.split(":").map(Number)).map((ring) => ({
    center: waters[ring[0]].center,
    support: [...new Set(ring.flatMap((waterIndex) => waters[waterIndex].support))],
    type: 2, residual: false, gap: true, kind: "oxygen-ring gap boundary",
  }));
  const placements = [...waters, ...bridges, ...gaps];
  const coveredAtoms = new Set(waters.flatMap((placement) => placement.support));
  const types = [
    { type: 0, medoid: waters[0]?.center || 0, element: "H₂O", label: "molecule", customSupport: waters[0]?.support || [] },
    { type: 1, medoid: bridges[0]?.center || 0, element: "O–H···O", label: "connection", customSupport: bridges[0]?.support || [] },
    { type: 2, medoid: gaps[0]?.center || 0, element: "O₆ void", label: "gap boundary", gap: true, customSupport: gaps[0]?.support || [] },
  ].filter((type) => type.customSupport.length);
  const incidence = source.map((_, atomIndex) => placements.map((placement, placementIndex) => placement.support.includes(atomIndex) ? placementIndex : -1).filter((index) => index >= 0));
  return { placements, residualTypes: [], types, incidence, covered: coveredAtoms.size,
    complete: coveredAtoms.size === source.length, periodic: true,
    molecular: { waters: waters.length, bridges: bridges.length, gaps: gaps.length } };
}

// Turn environment labels into an explicit overlapping cover.  Candidate
// placements are atom-centred first shells on the periodic quotient.  Greedy
// set cover chooses recurring placements; any atom left behind is promoted to
// a residual cluster placement instead of disappearing from the model.
function buildExhaustiveClusterCover(source) {
  if (currentMaterial().molecularCover === "water") return buildWaterClusterCover(source);
  const shellRadius = motifShellCutoff();
  const supports = source.map((_, center) => [
    center,
    ...learnedClusters.environments[center].shell
      .filter((neighbor) => neighbor.r <= shellRadius)
      .map((neighbor) => source.indexOf(neighbor.atom)),
  ].filter((index, position, values) => index >= 0 && values.indexOf(index) === position));
  const occurrences = supports.map((support, center) => ({
    center, support, type: learnedClusters.labels[center], residual: false,
  })).sort((first, second) => second.support.length - first.support.length || first.center - second.center);
  const uncovered = new Set(source.map((_, index) => index));
  const placements = [];
  while (uncovered.size) {
    let best = null;
    let gain = 0;
    occurrences.forEach((occurrence) => {
      const candidateGain = occurrence.support.reduce((sum, index) => sum + Number(uncovered.has(index)), 0);
      if (candidateGain > gain) { best = occurrence; gain = candidateGain; }
    });
    if (!best || !gain) break;
    placements.push(best);
    best.support.forEach((index) => uncovered.delete(index));
  }
  const residualTypes = [];
  [...uncovered].forEach((atomIndex) => {
    const species = source[atomIndex].species;
    let type = residualTypes.findIndex((candidate) => candidate.species === species);
    if (type < 0) {
      type = residualTypes.length;
      residualTypes.push({ species, count: 0, medoid: atomIndex, coordination: 0, spread: 0, residual: true });
    }
    residualTypes[type].count++;
    placements.push({ center: atomIndex, support: [atomIndex], type: learnedClusters.clusters.length + type, residual: true });
    uncovered.delete(atomIndex);
  });
  const coveredAtoms = new Set(placements.flatMap((placement) => placement.support));
  const incidence = source.map((_, atomIndex) => placements
    .map((placement, placementIndex) => placement.support.includes(atomIndex) ? placementIndex : -1)
    .filter((placementIndex) => placementIndex >= 0));
  return {
    placements, residualTypes, incidence,
    covered: coveredAtoms.size,
    complete: coveredAtoms.size === source.length,
    periodic: currentPbc().some(Boolean),
  };
}

function clusterGalleryTypes() {
  if (!learnedClusters || !learnedCover) return [];
  if (learnedCover.types) return learnedCover.types;
  return [
    ...learnedClusters.clusters.map((cluster, type) => ({ ...cluster, type, residual: false })),
    ...learnedCover.residualTypes.map((cluster, offset) => ({ ...cluster, type: learnedClusters.clusters.length + offset })),
  ];
}

function rebuildClusterGallery() {
  clusterGallery.replaceChildren();
  clusterGalleryTypes().forEach((cluster, galleryIndex) => {
    const card = document.createElement("article");
    card.className = `cluster-card${cluster.residual ? " residual" : ""}`;
    const canvas = document.createElement("canvas");
    canvas.width = 280;
    canvas.height = 224;
    canvas.dataset.cluster = String(galleryIndex);
    const label = document.createElement("div");
    label.className = "cluster-card-label";
    const placements = learnedCover.placements.filter((placement) => placement.type === cluster.type).length;
    const poses = orientationAtlas.find((entry) => entry.cluster === galleryIndex)?.orientations || 0;
    const name = cluster.label || (cluster.residual ? "gap" : `C${cluster.type + 1}`);
    label.innerHTML = `<b>${name}</b><span>${cluster.element || cluster.species} · ${placements} placement${placements === 1 ? "" : "s"} · ${poses || "—"} pose${poses === 1 ? "" : "s"}</span>`;
    card.append(canvas, label);
    clusterGallery.append(card);
  });
}

function drawClusterGallery(now) {
  if (pipelineStage !== 1 || clusterGallery.hidden) return;
  const scaleToScene = referenceSpacing / referenceSpacingA;
  clusterGallery.querySelectorAll("canvas[data-cluster]").forEach((canvas, galleryIndex) => {
    const cluster = clusterGalleryTypes()[Number(canvas.dataset.cluster)];
    if (!cluster) return;
    const context = canvas.getContext("2d");
    context.clearRect(0, 0, canvas.width, canvas.height);
    const center = referenceAtoms[cluster.medoid];
    let sites = [{ vector: new THREE.Vector3(), atom: center }];
    if (cluster.customSupport) sites = cluster.customSupport.map((atomIndex) => ({
      vector: periodicDisplacement(center, referenceAtoms[atomIndex]), atom: referenceAtoms[atomIndex],
    }));
    else if (!cluster.residual) learnedClusters.environments[cluster.medoid].shell
      .filter((neighbor) => neighbor.r <= motifShellCutoff())
      .forEach((neighbor) => sites.push(neighbor));
    const angleY = now * (.00018 + galleryIndex * .000011) + galleryIndex * .83;
    const angleX = now * (.00009 + galleryIndex * .000007) + .35;
    const quaternion = new THREE.Quaternion().setFromEuler(new THREE.Euler(angleX, angleY, angleY * .23));
    const projected = sites.map((site, index) => {
      const point = site.vector.clone().multiplyScalar(scaleToScene).applyQuaternion(quaternion);
      const perspective = 1 / (1 + Math.max(-.7, point.z) * .11);
      return { index, atom: site.atom, x: canvas.width / 2 + point.x * 48 * perspective, y: canvas.height / 2 + point.y * 48 * perspective, z: point.z, perspective };
    }).sort((first, second) => first.z - second.z);
    const projectedCenter = projected.find((point) => point.index === 0);
    context.lineWidth = 1.5;
    projected.filter((point) => point.index !== 0).forEach((point) => {
      context.beginPath(); context.moveTo(projectedCenter.x, projectedCenter.y); context.lineTo(point.x, point.y);
      context.strokeStyle = cluster.residual || cluster.gap ? "rgba(255,193,105,.42)" : "rgba(101,225,188,.32)"; context.stroke();
    });
    projected.forEach((point) => {
      const record = elementRecord(point.atom.species);
      const radius = (point.index ? 6.5 : 8.5) * point.perspective * Math.min(1.12, record.radius / 1.3);
      context.beginPath(); context.arc(point.x, point.y, radius, 0, TAU);
      context.fillStyle = record.css; context.shadowColor = record.css; context.shadowBlur = point.index ? 5 : 10; context.fill(); context.shadowBlur = 0;
      context.strokeStyle = point.index ? "rgba(255,255,255,.24)" : "rgba(255,255,255,.72)"; context.stroke();
    });
  });
}

function learnOverlapMarking(source) {
  const shellRadius = motifShellCutoff();
  const shells = source.map((center, centerIndex) => {
    const neighbors = [];
    source.forEach((atom, atomIndex) => {
      if (atomIndex === centerIndex) return;
      const normalizedDistance = periodicDisplacement(center, atom).length() / referenceSpacingA;
      if (normalizedDistance <= shellRadius) neighbors.push({ index: atomIndex, distance: normalizedDistance });
    });
    return neighbors;
  });
  const shellSets = shells.map((neighbors, index) => new Set([index, ...neighbors.map((neighbor) => neighbor.index)]));
  const states = new Map();
  const sourceDomains = new Array(source.length);
  const samples = new Array(source.length);
  shells.forEach((neighbors, centerIndex) => {
    const counts = new Map();
    neighbors.forEach(({ index }) => {
      const cluster = learnedClusters.labels[index] + 1;
      counts.set(cluster, (counts.get(cluster) || 0) + 1);
    });
    const shellCode = [...counts.entries()].sort((a, b) => a[0] - b[0]).map(([cluster, count]) => `C${cluster}×${count}`).join("+") || "isolated";
    const ownCluster = learnedClusters.labels[centerIndex] + 1;
    const domain = `C${ownCluster}|z${neighbors.length}|${shellCode}`;
    const meanDistance = neighbors.reduce((sum, neighbor) => sum + neighbor.distance, 0) / Math.max(1, neighbors.length);
    const score = -1.35 + .24 * meanDistance;
    const state = states.get(domain) || { count: 0, min: Infinity, max: -Infinity, sum: 0 };
    state.count++;
    state.min = Math.min(state.min, score);
    state.max = Math.max(state.max, score);
    state.sum += score;
    states.set(domain, state);
    sourceDomains[centerIndex] = domain;
    samples[centerIndex] = { domain, score };
  });

  const edges = [];
  for (let first = 0; first < source.length; first++) {
    for (let second = first + 1; second < source.length; second++) {
      const distance = periodicDisplacement(source[first], source[second]).length() / referenceSpacingA;
      if (distance > 2.76) continue;
      const sharedIndices = [];
      shellSets[first].forEach((index) => { if (shellSets[second].has(index)) sharedIndices.push(index); });
      if (!sharedIndices.length) continue;
      edges.push({
        first, second, shared: sharedIndices.length, sharedIndices, distance,
        firstCluster: learnedClusters.labels[first] + 1,
        secondCluster: learnedClusters.labels[second] + 1,
      });
    }
  }
  edges.sort((first, second) => second.shared - first.shared || first.distance - second.distance);
  const runningStates = new Map();
  let reusable = 0;
  const curve = samples.map((sample, index) => {
    const count = (runningStates.get(sample.domain) || 0) + 1;
    runningStates.set(sample.domain, count);
    if (count === 2) reusable++;
    return { samples: index + 1, discovered: runningStates.size, reusable };
  });
  const overlapsAdded = new Array(source.length).fill(0);
  edges.forEach((edge) => overlapsAdded[Math.max(edge.first, edge.second)]++);
  let overlapTotal = 0;
  curve.forEach((point, index) => {
    overlapTotal += overlapsAdded[index];
    point.overlaps = overlapTotal;
  });
  const ambiguous = [...states.values()].filter((state) => state.count < 2 || state.max - state.min > .12).length;
  return { states, sourceDomains, samples, curve, edges, ambiguous, covered: sourceDomains.filter(Boolean).length };
}

function occurrenceFrame(source, centerIndex) {
  const shell = learnedClusters.environments[centerIndex].shell.filter((neighbor) => neighbor.r <= motifShellCutoff());
  if (!shell.length) return new THREE.Quaternion();
  const x = shell[0].vector.clone().normalize();
  let transverse = null;
  let transverseNorm = -Infinity;
  shell.slice(1).forEach((neighbor) => {
    const norm = new THREE.Vector3().crossVectors(x, neighbor.vector).lengthSq();
    if (norm > transverseNorm) { transverseNorm = norm; transverse = neighbor.vector; }
  });
  if (!transverse || transverseNorm < 1e-8) {
    transverse = Math.abs(x.x) < .8 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0);
  }
  const z = new THREE.Vector3().crossVectors(x, transverse).normalize();
  const y = new THREE.Vector3().crossVectors(z, x).normalize();
  const matrix = new THREE.Matrix4().makeBasis(x, y, z);
  return new THREE.Quaternion().setFromRotationMatrix(matrix).normalize();
}

function quaternionDistance(first, second) {
  return 2 * Math.acos(Math.min(1, Math.abs(first.dot(second))));
}

function learnMolecularOverlapGrammar(source) {
  const placements = learnedCover.placements;
  const makeOccurrence = (placement, index) => {
    const position = source[placement.center].p.clone();
    const sites = placement.support.map((atomIndex) => ({
      local: periodicDisplacement(source[placement.center], source[atomIndex]).multiplyScalar(referenceSpacing / referenceSpacingA),
      species: source[atomIndex].species,
      center: atomIndex === placement.center,
      referenceIndex: atomIndex,
    }));
    return { index, type: placement.type, position, rotation: new THREE.Quaternion(), sites, placement };
  };
  const occurrences = placements.map(makeOccurrence);
  const templates = clusterGalleryTypes().map((cluster) => ({
    type: cluster.type, medoid: cluster.medoid,
    sites: occurrences.find((occurrence) => occurrence.type === cluster.type)?.sites || [],
    radius: 3.4,
  }));
  const reconstructionByOccurrence = new Map();
  let reconstructionEdges = 0;
  const addReplayRule = (first, second) => {
    const shared = occurrences[first].placement.support.filter((atomIndex) => occurrences[second].placement.support.includes(atomIndex)).length;
    const rule = {
      id: `M${first}-${second}`, from: occurrences[first].type, to: occurrences[second].type,
      occurrenceFrom: first, occurrenceTo: second, reconstructionOnly: true,
      translation: periodicDisplacement(source[occurrences[first].placement.center], source[occurrences[second].placement.center])
        .multiplyScalar(referenceSpacing / referenceSpacingA),
      rotation: new THREE.Quaternion(), count: 1, meanShared: shared,
      sites: occurrences[second].sites, replayOrder: reconstructionEdges,
    };
    const adjacency = reconstructionByOccurrence.get(first) || [];
    adjacency.push(rule);
    reconstructionByOccurrence.set(first, adjacency);
    reconstructionEdges++;
  };
  const replaySeedIndex = 0;
  const reachableOccurrences = new Set([replaySeedIndex]);
  const coveredAtoms = new Set(occurrences[replaySeedIndex].placement.support);
  while (coveredAtoms.size < source.length) {
    const candidates = occurrences.map((occurrence, index) => ({
      index, shared: occurrence.placement.support.filter((atomIndex) => coveredAtoms.has(atomIndex)).length,
      fresh: occurrence.placement.support.filter((atomIndex) => !coveredAtoms.has(atomIndex)).length,
    })).filter((entry) => !reachableOccurrences.has(entry.index) && entry.shared >= 2 && entry.fresh > 0)
      .sort((first, second) => second.shared - first.shared || second.fresh - first.fresh || first.index - second.index);
    if (!candidates.length) {
      const missing = source.findIndex((_, atomIndex) => !coveredAtoms.has(atomIndex));
      const water = occurrences.find((occurrence) => occurrence.type === 0 && occurrence.placement.support.includes(missing));
      if (!water) break;
      const anchors = [...coveredAtoms].map((atomIndex) => ({ atomIndex,
        distance: periodicDisplacement(source[water.placement.center], source[atomIndex]).length() }))
        .sort((first, second) => first.distance - second.distance).slice(0, 2).map((entry) => entry.atomIndex);
      if (anchors.length < 2) break;
      const connector = { center: water.placement.center,
        support: [...new Set([...anchors, ...water.placement.support])],
        type: 2, residual: false, gap: true, kind: "learned residual gap connector" };
      occurrences.push(makeOccurrence(connector, occurrences.length));
      continue;
    }
    const next = candidates[0].index;
    const parent = [...reachableOccurrences].filter((index) => occurrences[index].placement.support.some((atomIndex) => occurrences[next].placement.support.includes(atomIndex)))
      .sort((first, second) => occurrences[second].placement.support.filter((atomIndex) => occurrences[next].placement.support.includes(atomIndex)).length
        - occurrences[first].placement.support.filter((atomIndex) => occurrences[next].placement.support.includes(atomIndex)).length)[0];
    addReplayRule(parent, next);
    reachableOccurrences.add(next);
    occurrences[next].placement.support.forEach((atomIndex) => coveredAtoms.add(atomIndex));
  }
  return { molecular: true, occurrences, templates, rules: [], byFrom: new Map(),
    reconstructionByOccurrence, replaySeedIndex, replayReachable: coveredAtoms.size,
    reconstructionEdges, observations: reconstructionEdges, recurring: 0, heldoutSupported: 0 };
}

function learnOverlapGrammar(source) {
  if (currentMaterial().molecularCover === "water") return learnMolecularOverlapGrammar(source);
  const scenePerAngstrom = referenceSpacing / referenceSpacingA;
  const occurrences = source.map((atom, index) => ({
    index,
    type: learnedClusters.labels[index],
    position: atom.p.clone(),
    rotation: occurrenceFrame(source, index),
  }));
  const templates = learnedClusters.clusters.map((cluster, type) => {
    const medoid = cluster.medoid;
    const inverseFrame = occurrences[medoid].rotation.clone().invert();
    const sites = [{ local: new THREE.Vector3(), species: source[medoid].species, center: true }];
    learnedClusters.environments[medoid].shell
      .filter((neighbor) => neighbor.r <= motifShellCutoff())
      .forEach((neighbor) => sites.push({
        local: neighbor.vector.clone().multiplyScalar(scenePerAngstrom).applyQuaternion(inverseFrame),
        species: neighbor.atom.species,
        center: false,
      }));
    return { type, medoid, sites, radius: Math.max(...sites.map((site) => site.local.length()), 0) };
  });

  const buckets = new Map();
  const addObservation = (firstIndex, secondIndex, edge, heldout) => {
    const first = occurrences[firstIndex];
    const second = occurrences[secondIndex];
    const inverse = first.rotation.clone().invert();
    const translation = periodicDisplacement(source[firstIndex], source[secondIndex])
      .multiplyScalar(scenePerAngstrom)
      .applyQuaternion(inverse);
    const rotation = inverse.multiply(second.rotation).normalize();
    const pairKey = `${first.type}>${second.type}`;
    const rules = buckets.get(pairKey) || [];
    let rule = rules.find((candidate) =>
      candidate.translation.distanceTo(translation) < .16
      && quaternionDistance(candidate.rotation, rotation) < .24);
    if (!rule) {
      rule = {
        from: first.type, to: second.type,
        translation: translation.clone(), rotation: rotation.clone(),
        representativeTranslation: translation.clone(), representativeRotation: rotation.clone(), representativeShared: edge.shared,
        representativePair: [firstIndex, secondIndex],
        count: 0, fitCount: 0, holdoutCount: 0, sharedTotal: 0,
        examples: [],
      };
      rules.push(rule);
      buckets.set(pairKey, rules);
    }
    const weight = 1 / (rule.count + 1);
    rule.translation.lerp(translation, weight);
    if (rule.rotation.dot(rotation) < 0) rotation.set(-rotation.x, -rotation.y, -rotation.z, -rotation.w);
    rule.rotation.slerp(rotation, weight).normalize();
    rule.count++;
    if (edge.shared > rule.representativeShared) {
      rule.representativeTranslation.copy(translation);
      rule.representativeRotation.copy(rotation);
      rule.representativeShared = edge.shared;
      rule.representativePair = [firstIndex, secondIndex];
    }
    if (heldout) rule.holdoutCount++; else rule.fitCount++;
    rule.sharedTotal += edge.shared;
    if (rule.examples.length < 6) rule.examples.push([firstIndex, secondIndex]);
  };

  const strongEdges = trainedMarking.edges.filter((edge) => edge.shared >= 2 && edge.distance <= overlapDistanceCutoff());
  strongEdges.forEach((edge, index) => {
    const heldout = index % 5 === 0;
    addObservation(edge.first, edge.second, edge, heldout);
    addObservation(edge.second, edge.first, edge, heldout);
  });
  const rules = [];
  [...buckets.entries()].forEach(([pairKey, pairRules]) => {
    pairRules
      .sort((first, second) => second.count - first.count || second.sharedTotal - first.sharedTotal)
      .slice(0, MAX_RULES_PER_PAIR)
      .forEach((rule) => {
        rule.translation.copy(rule.representativeTranslation);
        rule.rotation.copy(rule.representativeRotation);
        rule.id = rules.length;
        rule.pairKey = pairKey;
        rule.meanShared = rule.sharedTotal / Math.max(1, rule.count);
        rule.rotationAngle = 2 * Math.acos(Math.min(1, Math.abs(rule.rotation.w)));
        const targetIndex = rule.representativePair[1];
        const targetFrameInverse = occurrences[targetIndex].rotation.clone().invert();
        rule.sites = [{ local: new THREE.Vector3(), species: source[targetIndex].species, center: true }];
        learnedClusters.environments[targetIndex].shell.filter((neighbor) => neighbor.r <= motifShellCutoff()).forEach((neighbor) => rule.sites.push({
          local: neighbor.vector.clone().multiplyScalar(scenePerAngstrom).applyQuaternion(targetFrameInverse),
          species: neighbor.atom.species, center: false,
        }));
        rules.push(rule);
      });
  });
  const byFrom = new Map();
  rules.forEach((rule) => {
    const list = byFrom.get(rule.from) || [];
    list.push(rule);
    byFrom.set(rule.from, list);
  });
  const recurring = rules.filter((rule) => rule.count >= 2).length;
  const heldoutSupported = rules.filter((rule) => rule.holdoutCount > 0).length;
  // Preserve the observed occurrence graph separately from the compressed
  // continuation grammar. These exact one-off edges certify that the frozen
  // vocabulary can replay its training window; they are never available after
  // reconstruction completes.
  const reconstructionByOccurrence = new Map();
  const addReconstructionEdge = (firstIndex, secondIndex, edge) => {
    const first = occurrences[firstIndex];
    const second = occurrences[secondIndex];
    const inverse = first.rotation.clone().invert();
    const targetFrameInverse = second.rotation.clone().invert();
    const exactRule = {
      id: `O${firstIndex}-${secondIndex}`,
      from: first.type,
      to: second.type,
      occurrenceFrom: firstIndex,
      occurrenceTo: secondIndex,
      reconstructionOnly: true,
      translation: periodicDisplacement(source[firstIndex], source[secondIndex])
        .multiplyScalar(scenePerAngstrom).applyQuaternion(inverse),
      rotation: inverse.multiply(second.rotation).normalize(),
      count: 1,
      meanShared: edge.shared,
      sites: [{ local: new THREE.Vector3(), species: source[secondIndex].species, center: true }],
    };
    learnedClusters.environments[secondIndex].shell.filter((neighbor) => neighbor.r <= motifShellCutoff()).forEach((neighbor) => exactRule.sites.push({
      local: neighbor.vector.clone().multiplyScalar(scenePerAngstrom).applyQuaternion(targetFrameInverse),
      species: neighbor.atom.species,
      center: false,
    }));
    const adjacency = reconstructionByOccurrence.get(firstIndex) || [];
    adjacency.push(exactRule);
    reconstructionByOccurrence.set(firstIndex, adjacency);
  };
  strongEdges.forEach((edge) => {
    addReconstructionEdge(edge.first, edge.second, edge);
    addReconstructionEdge(edge.second, edge.first, edge);
  });
  const replaySeedIndex = rules.slice().sort((first, second) => second.count - first.count)[0]?.representativePair[0]
    ?? learnedClusters.clusters[0].medoid;
  const reachableOccurrences = new Set([replaySeedIndex]);
  const replayQueue = [replaySeedIndex];
  while (replayQueue.length) {
    const current = replayQueue.shift();
    (reconstructionByOccurrence.get(current) || []).forEach((rule) => {
      if (reachableOccurrences.has(rule.occurrenceTo)) return;
      reachableOccurrences.add(rule.occurrenceTo);
      replayQueue.push(rule.occurrenceTo);
    });
  }
  return { occurrences, templates, rules, byFrom, reconstructionByOccurrence,
    replaySeedIndex, replayReachable: reachableOccurrences.size,
    reconstructionEdges: strongEdges.length * 2,
    observations: strongEdges.length * 2, recurring, heldoutSupported };
}

const MARKING_REPRESENTATIONS = {
  sites: { label: "site-resolved section", short: "site resolved", exponent: 4, overlapWeight: .58 },
  ports: { label: "connection-port vector", short: "port vector", exponent: 6, overlapWeight: .70 },
  whole: { label: "whole-cluster action", short: "whole action", exponent: 2, overlapWeight: .38 },
};
const MARKING_LIBRARY_STORAGE = "gcts-marking-library-v1";

function restoreMarkingLibrary() {
  try {
    const stored = JSON.parse(localStorage.getItem(MARKING_LIBRARY_STORAGE) || "null");
    if (!stored || !Array.isArray(stored.markings)) return;
    markingLibrary = stored.markings.filter((marking) => marking?.id && marking?.config
      && Array.isArray(marking.coefficients) && MARKING_REPRESENTATIONS[marking.config.representation]);
    activeMarkingId = stored.activeMarkingId || null;
    nextMarkingId = Math.max(1, ...markingLibrary.map((marking) => Number(marking.id.split("-").at(-1)) + 1 || 1));
  } catch (_) {
    markingLibrary = [];
    activeMarkingId = null;
  }
}

function persistMarkingLibrary() {
  try {
    localStorage.setItem(MARKING_LIBRARY_STORAGE, JSON.stringify({ markings: markingLibrary, activeMarkingId }));
  } catch (_) {
    // The live lab remains fully functional when storage is unavailable.
  }
}

function currentMarkingConfig() {
  const requestedChannels = Number(markingDraft.channels);
  return {
    channels: requestedChannels || automaticMarkingChannels(),
    channelMode: requestedChannels ? "manual" : "auto",
    reach: Number(markingDraft.reach),
    representation: markingDraft.representation,
  };
}

function markingMaterialKey() {
  return scenarioSelect.value === "imported"
    ? `imported:${importedStructure?.metadata?.entryId || importedStructure?.metadata?.name || referenceCount()}`
    : scenarioSelect.value;
}

function learnSectionModel(source, config = currentMarkingConfig()) {
  const axes = BALANCE_DIRECTIONS;
  const representation = MARKING_REPRESENTATIONS[config.representation] || MARKING_REPRESENTATIONS.sites;
  const reachScale = { 1: .72, 2: 1, 3: 1.35 }[config.reach] || 1;
  const support = descriptorCutoff() * reachScale;
  const exponent = representation.exponent;
  const overlapWeight = representation.overlapWeight;
  const channelGain = 1 + Math.log2(Math.max(1, config.channels)) * .065;
  const incidentEdges = Array.from({ length: source.length }, () => []);
  trainedMarking.edges.forEach((edge) => {
    incidentEdges[edge.first].push(edge);
    if (edge.second !== edge.first) incidentEdges[edge.second].push(edge);
  });
  const basisAt = (centerIndex, atomIndex) => {
    const vector = periodicDisplacement(source[centerIndex], source[atomIndex]);
    const distance = vector.length() / referenceSpacingA;
    if (distance >= support || distance < 1e-6) return { features: new Array(axes.length).fill(0) };
    const frame = overlapGrammar.molecular ? occurrenceFrame(source, centerIndex) : overlapGrammar.occurrences[centerIndex].rotation;
    const direction = vector.normalize().applyQuaternion(frame.clone().invert());
    const radial = .5 * (1 + Math.cos(Math.PI * distance / support));
    return { features: axes.map((axis) => radial * Math.max(0, direction.dot(axis)) ** exponent) };
  };
  const fieldAt = (coefficients, basis) => basis.features.reduce((sum, feature, axis) => sum + feature * coefficients[axis], 0);
  const targets = source.map((center, centerIndex) => {
    const values = new Array(axes.length).fill(-.18 / channelGain);
    incidentEdges[centerIndex].forEach((edge) => {
      const otherIndex = edge.first === centerIndex ? edge.second : edge.first;
      const vector = periodicDisplacement(center, source[otherIndex]);
      if (vector.length() < 1e-6 || edge.shared < 2) return;
      const frame = overlapGrammar.molecular ? occurrenceFrame(source, centerIndex) : overlapGrammar.occurrences[centerIndex].rotation;
      const direction = vector.normalize().applyQuaternion(frame.clone().invert());
      let bestAxis = 0;
      let bestDot = -Infinity;
      axes.forEach((axis, axisIndex) => {
        const dot = direction.dot(axis);
        if (dot > bestDot) { bestDot = dot; bestAxis = axisIndex; }
      });
      values[bestAxis] = Math.max(values[bestAxis], Math.min(.36, (.10 + edge.shared * .035) * channelGain));
    });
    return values;
  });
  const clusterCount = learnedClusters.clusters.length;
  const initial = Array.from({ length: clusterCount }, (_, cluster) =>
    axes.map((_, axis) => (siteHash(cluster, axis, 17, 4) - .5) * .34 / Math.sqrt(channelGain)));
  const coefficients = initial.map((values) => [...values]);
  const fitIndices = source.map((_, index) => index).filter((index) => index % 5 !== 0);
  const holdoutIndices = source.map((_, index) => index).filter((index) => index % 5 === 0);
  const fitSet = new Set(fitIndices);
  const holdoutSet = new Set(holdoutIndices);
  const portLossFor = (indices, values = coefficients) => indices.reduce((sum, index) => {
    const cluster = learnedClusters.labels[index];
    return sum + targets[index].reduce((error, target, axis) => error + (values[cluster][axis] - target) ** 2, 0) / axes.length;
  }, 0) / Math.max(1, indices.length);
  const overlapLossFor = (membership, values = coefficients) => {
    let loss = 0;
    let count = 0;
    trainedMarking.edges.forEach((edge) => {
      if (!membership.has(edge.first) || !membership.has(edge.second)) return;
      const firstCoefficients = values[learnedClusters.labels[edge.first]];
      const secondCoefficients = values[learnedClusters.labels[edge.second]];
      edge.sharedIndices.forEach((atomIndex) => {
        const firstValue = fieldAt(firstCoefficients, basisAt(edge.first, atomIndex));
        const secondValue = fieldAt(secondCoefficients, basisAt(edge.second, atomIndex));
        loss += (firstValue - secondValue) ** 2;
        count++;
      });
    });
    return loss / Math.max(1, count);
  };
  const totalLossFor = (indices, membership, values = coefficients) =>
    (1 - overlapWeight) * portLossFor(indices, values) + overlapWeight * overlapLossFor(membership, values);
  const initialPoint = {
    samples: 0,
    fitSamples: 0,
    holdoutSamples: 0,
    trainLoss: totalLossFor(fitIndices, fitSet),
    validationLoss: totalLossFor(holdoutIndices, holdoutSet),
    coefficients: initial.map((values) => [...values]),
  };
  let fitSamples = 0;
  let holdoutSamples = 0;
  let trainLoss = initialPoint.trainLoss;
  let validationLoss = initialPoint.validationLoss;
  const curve = source.map((_, index) => {
    const cluster = learnedClusters.labels[index];
    if (index % 5 === 0) holdoutSamples++;
    else {
      fitSamples++;
      const channelStep = .14 / (1 + Math.log2(Math.max(1, config.channels)) * .12);
      coefficients[cluster] = coefficients[cluster].map((value, axis) => value + channelStep * (targets[index][axis] - value));
      const incident = incidentEdges[index].filter((edge) => Math.max(edge.first, edge.second) <= index);
      const gradient = new Array(axes.length).fill(0);
      let constraints = 0;
      incident.forEach((edge) => {
        const firstCluster = learnedClusters.labels[edge.first];
        const secondCluster = learnedClusters.labels[edge.second];
        edge.sharedIndices.forEach((atomIndex) => {
          const firstBasis = basisAt(edge.first, atomIndex);
          const secondBasis = basisAt(edge.second, atomIndex);
          const difference = fieldAt(coefficients[firstCluster], firstBasis) - fieldAt(coefficients[secondCluster], secondBasis);
          axes.forEach((__, axis) => {
            if (firstCluster === cluster) gradient[axis] += difference * firstBasis.features[axis];
            if (secondCluster === cluster) gradient[axis] -= difference * secondBasis.features[axis];
          });
          constraints++;
        });
      });
      if (constraints) coefficients[cluster] = coefficients[cluster].map((value, axis) => value - .04 * gradient[axis] / constraints);
    }
    const portLoss = targets[index].reduce((error, target, axis) =>
      error + (coefficients[cluster][axis] - target) ** 2, 0) / axes.length;
    let overlapLoss = 0;
    let overlapConstraints = 0;
    incidentEdges[index].forEach((edge) => {
      const firstCoefficients = coefficients[learnedClusters.labels[edge.first]];
      const secondCoefficients = coefficients[learnedClusters.labels[edge.second]];
      edge.sharedIndices.forEach((atomIndex) => {
        const difference = fieldAt(firstCoefficients, basisAt(edge.first, atomIndex))
          - fieldAt(secondCoefficients, basisAt(edge.second, atomIndex));
        overlapLoss += difference ** 2;
        overlapConstraints++;
      });
    });
    const sampleLoss = (1 - overlapWeight) * portLoss + overlapWeight * overlapLoss / Math.max(1, overlapConstraints);
    if (index % 5 === 0) validationLoss = .92 * validationLoss + .08 * sampleLoss;
    else trainLoss = .92 * trainLoss + .08 * sampleLoss;
    return {
      samples: index + 1,
      fitSamples,
      holdoutSamples,
      trainLoss,
      validationLoss,
      coefficients: coefficients.map((values) => [...values]),
    };
  });
  return { axes, targets, initial, initialPoint, curve, support, channels: config.channels,
    channelMode: config.channelMode || "manual", reach: config.reach,
    representation: config.representation, overlapWeight, exponent, channelGain,
    fitCount: fitIndices.length, holdoutCount: holdoutIndices.length };
}

function currentSectionPoint() {
  return trainingProgress > 0 ? sectionModel.curve[trainingProgress - 1] : sectionModel.initialPoint;
}

function currentSectionCoefficients(cluster) {
  return currentSectionPoint().coefficients[cluster];
}

function selectedMarking() {
  return markingLibrary.find((marking) => marking.id === activeMarkingId) || null;
}

function searchSectionCoefficients() {
  const marking = selectedMarking();
  return marking?.coefficients?.length === learnedClusters.clusters.length
    ? marking.coefficients : sectionModel.curve.at(-1).coefficients;
}

function markingAcceptanceThreshold() {
  const marking = selectedMarking();
  const representation = marking?.config.representation || sectionModel?.representation || "sites";
  const base = { sites: -.24, ports: -.14, whole: -.30 }[representation] ?? -.24;
  const channels = marking?.config.channels || sectionModel?.channels || 1;
  return base - Math.min(.06, Math.log2(Math.max(1, channels)) * .012);
}

function sectionLossForCluster(cluster) {
  const coefficients = currentSectionCoefficients(cluster);
  const indices = learnedClusters.labels.map((label, index) => label === cluster ? index : -1).filter((index) => index >= 0);
  return indices.reduce((sum, index) => sum + sectionModel.targets[index].reduce((error, target, axis) => error + (coefficients[axis] - target) ** 2, 0) / sectionModel.axes.length, 0) / Math.max(1, indices.length);
}

function visibleTrainingStates(limit = trainingProgress) {
  const states = new Map();
  trainedMarking.samples.slice(0, limit).forEach(({ domain, score }) => {
    const state = states.get(domain) || { count: 0, min: Infinity, max: -Infinity, sum: 0 };
    state.count++;
    state.min = Math.min(state.min, score);
    state.max = Math.max(state.max, score);
    state.sum += score;
    states.set(domain, state);
  });
  return states;
}

function currentTrainingPoint() {
  const overlapPoint = trainingProgress > 0
    ? trainedMarking.curve[Math.min(trainingProgress, trainedMarking.curve.length) - 1]
    : { samples: 0, discovered: 0, reusable: 0, overlaps: 0 };
  return { ...overlapPoint, ...currentSectionPoint() };
}

function seedTrainedMarking() {
  const finalPoint = sectionModel.curve.at(-1);
  const coefficients = searchSectionCoefficients();
  markingCache = new Map(overlapGrammar.rules.map((rule) => {
    const score = ruleMarkingScore(rule, coefficients);
    return [`r${rule.id}:C${rule.from + 1}>C${rule.to + 1}`, {
      count: rule.count, min: score - finalPoint.validationLoss, max: score + finalPoint.validationLoss, sum: score * rule.count,
    }];
  }));
}

function sectionValue(cluster, localDirection, coefficients = pipelineStage === 4 ? searchSectionCoefficients() : currentSectionPoint().coefficients) {
  return sectionModel.axes.reduce((sum, axis, index) =>
    sum + coefficients[cluster][index] * Math.max(0, localDirection.dot(axis)) ** sectionModel.exponent, 0);
}

function ruleMarkingScore(rule, coefficients = pipelineStage === 4 ? searchSectionCoefficients() : currentSectionPoint().coefficients) {
  const forward = rule.translation.clone().normalize();
  const reverse = rule.translation.clone().negate().normalize().applyQuaternion(rule.rotation.clone().invert());
  const first = sectionValue(rule.from, forward, coefficients);
  const second = sectionValue(rule.to, reverse, coefficients);
  return .5 * (first + second) - Math.abs(first - second) - Math.max(0, -.08 - first) - Math.max(0, -.08 - second);
}

function spatialKey(position) {
  return `${Math.floor(position.x / SPATIAL_CELL)},${Math.floor(position.y / SPATIAL_CELL)},${Math.floor(position.z / SPATIAL_CELL)}`;
}

function indexAtom(atom) {
  const key = spatialKey(atom.p);
  const bucket = atomSpatialIndex.get(key) || [];
  bucket.push(atom);
  atomSpatialIndex.set(key, bucket);
}

function rebuildSpatialIndex() {
  atomSpatialIndex = new Map();
  atoms.forEach(indexAtom);
}

function nearbyAtoms(position, radius = COLLISION_TOLERANCE) {
  const result = [];
  const reach = Math.ceil(radius / SPATIAL_CELL);
  const base = [Math.floor(position.x / SPATIAL_CELL), Math.floor(position.y / SPATIAL_CELL), Math.floor(position.z / SPATIAL_CELL)];
  for (let dx = -reach; dx <= reach; dx++) for (let dy = -reach; dy <= reach; dy++) for (let dz = -reach; dz <= reach; dz++) {
    const bucket = atomSpatialIndex.get(`${base[0] + dx},${base[1] + dy},${base[2] + dz}`);
    if (bucket) bucket.forEach((atom) => { if (atom.p.distanceToSquared(position) <= radius * radius) result.push(atom); });
  }
  return result;
}

function scenePeriodicContext() {
  const scale = referenceSpacing / referenceSpacingA;
  const cell = currentCell()?.map((vector) => vector.clone().multiplyScalar(scale));
  const pbc = currentPbc();
  if (!cell || !pbc.some(Boolean)) return { matrix: null, inverse: null, pbc };
  const matrix = new THREE.Matrix3().set(
    cell[0].x, cell[1].x, cell[2].x,
    cell[0].y, cell[1].y, cell[2].y,
    cell[0].z, cell[1].z, cell[2].z,
  );
  return { matrix, inverse: matrix.clone().invert(), pbc };
}

function scenePeriodicDisplacement(first, second, context = scenePeriodicContext()) {
  const delta = second.clone().sub(first);
  if (!context.matrix) return delta;
  const fractional = delta.applyMatrix3(context.inverse);
  ["x", "y", "z"].forEach((axis, index) => {
    if (context.pbc[index]) fractional[axis] -= Math.round(fractional[axis]);
  });
  return fractional.applyMatrix3(context.matrix);
}

function referenceIndexForSite(site, context = scenePeriodicContext()) {
  let bestIndex = -1;
  let bestDistance2 = MERGE_TOLERANCE ** 2;
  referenceAtoms.forEach((reference, index) => {
    if (reference.species !== site.species) return;
    const distance2 = scenePeriodicDisplacement(reference.p, site.p, context).lengthSq();
    if (distance2 <= bestDistance2) { bestIndex = index; bestDistance2 = distance2; }
  });
  return bestIndex;
}

function referenceCoverageAudit() {
  const context = scenePeriodicContext();
  const counts = new Array(referenceAtoms.length).fill(0);
  let extraneousAtoms = 0;
  atoms.forEach((atom) => {
    const index = Number.isInteger(atom.referenceIndex)
      ? atom.referenceIndex : referenceIndexForSite(atom, context);
    if (index < 0) extraneousAtoms++;
    else counts[index]++;
  });
  const matchedMask = counts.map((count) => count > 0);
  return {
    matchedMask,
    counts,
    matched: matchedMask.filter(Boolean).length,
    missing: matchedMask.filter((value) => !value).length,
    extraneousAtoms,
    duplicateAtoms: counts.reduce((sum, count) => sum + Math.max(0, count - 1), 0),
    context,
  };
}

function candidateReferenceGain(candidate, audit) {
  if (reconstructionCertified || audit.missing === 0) return 0;
  const gained = new Set();
  candidateSites(candidate).forEach((site) => {
    referenceAtoms.forEach((reference, index) => {
      if (audit.matchedMask[index] || reference.species !== site.species) return;
      if (scenePeriodicDisplacement(reference.p, site.p, audit.context).lengthSq() <= MERGE_TOLERANCE ** 2) gained.add(index);
    });
  });
  return gained.size;
}

function canonicalKnownSites(sites, context = scenePeriodicContext()) {
  const byReference = new Map();
  let failures = 0;
  sites.forEach((site) => {
    const referenceIndex = referenceIndexForSite(site, context);
    if (referenceIndex < 0) { failures++; return; }
    if (byReference.has(referenceIndex)) return;
    const reference = referenceAtoms[referenceIndex];
    byReference.set(referenceIndex, {
      ...site,
      p: reference.p.clone(),
      species: reference.species,
      referenceIndex,
    });
  });
  return { sites: [...byReference.values()], failures, duplicateSites: sites.length - failures - byReference.size };
}

function insideGrowthDomain(position) {
  const shape = confinementSelect.value;
  if (shape === "box") return Math.max(Math.abs(position.x), Math.abs(position.y), Math.abs(position.z)) <= 8.35;
  if (shape === "sphere") return position.length() <= 8.8;
  if (shape === "cylinder") return Math.abs(position.x) <= 8.35 && Math.hypot(position.y, position.z) <= 7.8;
  return Math.abs(position.x) <= 8.35 && Math.hypot(position.y, position.z) <= 2.25 + .58 * Math.abs(position.x);
}

function frontierSector(position) {
  const direction = position.clone().normalize();
  let best = 0;
  let bestDot = -Infinity;
  BALANCE_DIRECTIONS.forEach((axis, index) => {
    const dot = direction.dot(axis);
    if (dot > bestDot) { best = index; bestDot = dot; }
  });
  return best;
}

function candidateKey(type, position, rotation) {
  const q = rotation.clone();
  if (q.w < 0) q.set(-q.x, -q.y, -q.z, -q.w);
  return [type, Math.round(position.x / .12), Math.round(position.y / .12), Math.round(position.z / .12),
    Math.round(q.x / .08), Math.round(q.y / .08), Math.round(q.z / .08), Math.round(q.w / .08)].join(":");
}

function enqueueRulesFromPlacement(placement) {
  const continuationRules = hierarchyEnabled || placement.depth === 0
    ? overlapGrammar.byFrom.get(placement.type) || [] : [];
  const replayRules = !reconstructionCertified && Number.isInteger(placement.occurrenceIndex)
    ? overlapGrammar.reconstructionByOccurrence.get(placement.occurrenceIndex) || [] : [];
  const rules = [...replayRules, ...continuationRules];
  rules.forEach((rule) => {
    const rotation = placement.rotation.clone().multiply(rule.rotation).normalize();
    const position = placement.position.clone().add(rule.translation.clone().applyQuaternion(placement.rotation));
    const key = `${candidateKey(rule.to, position, rotation)}${rule.reconstructionOnly ? `:O${rule.occurrenceTo}` : ""}`;
    if (rejectedCandidateKeys.has(key) || frontierCandidateKeys.has(key)) return;
    if (placedClusters.some((candidate) => candidate.type === rule.to
      && candidate.position.distanceTo(position) < .2
      && quaternionDistance(candidate.rotation, rotation) < .24
      && (!rule.reconstructionOnly || candidate.occurrenceIndex === rule.occurrenceTo))) return;
    const markingScore = ruleMarkingScore(rule);
    frontierCandidates.push({ key, parentId: placement.id, rule, type: rule.to, position, rotation,
      occurrenceIndex: rule.reconstructionOnly ? rule.occurrenceTo : null, markingScore,
      priority: (policySelect.value === "marked" ? markingScore : 0) + Math.log1p(rule.count) * .09 + rule.meanShared * .035 + random() * .025 });
    frontierCandidateKeys.add(key);
  });
}

function dynamicCandidatePriority(candidate) {
  const parent = placedClusters.find((placement) => placement.id === candidate.parentId);
  return candidate.priority - candidate.position.length() * .055
    - sectorCounts[frontierSector(candidate.position)] * .11
    - (parent?.depth || 0) * .008;
}

function candidateSites(candidate) {
  return (candidate.rule.sites || overlapGrammar.templates[candidate.type].sites).map((site) => ({
    species: site.species, center: site.center,
    p: site.local.clone().applyQuaternion(candidate.rotation).add(candidate.position),
  }));
}

function sitesCanCommute(firstSites, secondSites) {
  for (const first of firstSites) for (const second of secondSites) {
    const distance = first.p.distanceTo(second.p);
    if (distance > COLLISION_TOLERANCE) continue;
    if (first.species === second.species && distance <= COMMUTING_SITE_TOLERANCE) continue;
    return false;
  }
  return true;
}

function batchRetainsNovelSites(entries) {
  if (!reconstructionCertified && replayIndex < referenceCount()) {
    const owners = new Map();
    entries.forEach((entry) => entry.evaluation.freshReferenceIndices.forEach((referenceIndex) =>
      owners.set(referenceIndex, (owners.get(referenceIndex) || 0) + 1)));
    return entries.every((entry) => entry.evaluation.freshReferenceIndices.some((referenceIndex) =>
      owners.get(referenceIndex) === 1));
  }
  return entries.every((entry, index) => entry.evaluation.fresh.some((site) => !entries.some((other, otherIndex) =>
    otherIndex !== index && other.sites.some((otherSite) => otherSite.species === site.species
      && otherSite.p.distanceTo(site.p) <= COMMUTING_SITE_TOLERANCE))));
}

function rejectionIsOrderInvariant(candidate, evaluation) {
  const markingRejected = policySelect.value === "marked" && candidate.markingScore <= markingAcceptanceThreshold();
  return evaluation.conflicts > 0 || evaluation.boundaryFailures > 0
    || evaluation.fresh.length === 0 || markingRejected;
}

function commutingFrontierBatch() {
  const audit = referenceCoverageAudit();
  const ranked = frontierCandidates.map((candidate) => ({
    candidate,
    score: dynamicCandidatePriority(candidate) + 2.5 * candidateReferenceGain(candidate, audit),
  })).sort((first, second) => second.score - first.score).map((entry) => entry.candidate);
  if (overlapGrammar.molecular && !reconstructionCertified) {
    const ordered = ranked.slice().sort((first, second) => first.rule.replayOrder - second.rule.replayOrder);
    for (const candidate of ordered) {
      const evaluation = evaluateCandidate(candidate);
      if (evaluation.accepted || rejectionIsOrderInvariant(candidate, evaluation)) {
        return [{ candidate, evaluation, sites: evaluation.sites }];
      }
    }
    return [];
  }
  const acceptedBatch = [];
  const rejectedBatch = [];
  for (const candidate of ranked) {
    const evaluation = evaluateCandidate(candidate);
    const entry = { candidate, evaluation, sites: evaluation.sites };
    if (evaluation.accepted) {
      if (!acceptedBatch.every((other) => sitesCanCommute(entry.sites, other.sites))) continue;
      const trial = [...acceptedBatch, entry];
      if (!batchRetainsNovelSites(trial)) continue;
      acceptedBatch.push(entry);
      continue;
    }
    // "Insufficient shared support" can become valid after another placement,
    // so it is deferred rather than flashed red. The failures retained here
    // remain failures after any permutation of the accepted batch.
    if (!rejectionIsOrderInvariant(candidate, evaluation)) continue;
    if (![...acceptedBatch, ...rejectedBatch].every((other) => sitesCanCommute(entry.sites, other.sites))) continue;
    rejectedBatch.push(entry);
  }
  return [...acceptedBatch, ...rejectedBatch];
}

function refineCandidateTranslation(candidate) {
  const corrections = [];
  candidateSites(candidate).forEach((site) => {
    const match = nearbyAtoms(site.p, .34).filter((atom) => atom.species === site.species)
      .sort((first, second) => first.p.distanceToSquared(site.p) - second.p.distanceToSquared(site.p))[0];
    if (match) corrections.push(match.p.clone().sub(site.p));
  });
  if (corrections.length < 2) return;
  const correction = corrections.reduce((sum, value) => sum.add(value), new THREE.Vector3()).multiplyScalar(1 / corrections.length);
  if (correction.length() <= .18) candidate.position.add(correction);
}

function evaluateCandidate(candidate) {
  refineCandidateTranslation(candidate);
  const rawSites = candidateSites(candidate);
  const reconstructing = !reconstructionCertified && replayIndex < referenceCount();
  const canonical = reconstructing ? canonicalKnownSites(rawSites) : { sites: rawSites, failures: 0, duplicateSites: 0 };
  const sites = canonical.sites;
  const audit = reconstructing ? referenceCoverageAudit() : null;
  const merged = [];
  const fresh = [];
  let conflicts = 0;
  let boundaryFailures = 0;
  sites.forEach((site) => {
    if (reconstructing) {
      if (audit.matchedMask[site.referenceIndex]) {
        const atom = atoms.find((candidateAtom) => candidateAtom.referenceIndex === site.referenceIndex)
          || nearbyAtoms(site.p, MERGE_TOLERANCE).find((candidateAtom) => candidateAtom.species === site.species);
        if (atom) merged.push({ site, atom });
      } else fresh.push(site);
      return;
    }
    const neighborhood = nearbyAtoms(site.p, COLLISION_TOLERANCE)
      .sort((first, second) => first.p.distanceToSquared(site.p) - second.p.distanceToSquared(site.p));
    const same = neighborhood.find((atom) => atom.species === site.species && atom.p.distanceTo(site.p) <= MERGE_TOLERANCE);
    if (same) merged.push({ site, atom: same });
    else if (neighborhood.length) conflicts++;
    else if (!insideGrowthDomain(site.p)) boundaryFailures++;
    else fresh.push(site);
  });
  const markingAccepted = policySelect.value !== "marked" || candidate.markingScore > markingAcceptanceThreshold();
  const knownFailures = reconstructing ? canonical.failures : 0;
  const markingFallback = reconstructing && knownFailures === 0 && !markingAccepted;
  const accepted = conflicts === 0 && boundaryFailures === 0 && merged.length >= 2
    && fresh.length > 0 && knownFailures === 0 && (markingAccepted || markingFallback);
  return { accepted, sites, merged, fresh, conflicts, boundaryFailures, knownFailures, markingFallback,
    duplicateSites: canonical.duplicateSites,
    freshReferenceIndices: fresh.map((site) => site.referenceIndex).filter(Number.isInteger),
    reason: conflicts ? `${conflicts} hard-core/species conflicts` : boundaryFailures ? "outside confinement" : knownFailures ? `${knownFailures} sites outside known configuration` : merged.length < 2 ? "insufficient shared support" : fresh.length === 0 ? "duplicate covering" : candidate.markingScore <= markingAcceptanceThreshold() ? "marking mismatch" : "compatible overlap" };
}

function referenceCoverageCount() {
  return referenceCoverageAudit().matched;
}

function initializeOffLatticeSearch() {
  atoms = [];
  placedClusters = [];
  frontierCandidates = [];
  frontierCandidateKeys = new Set();
  rejectedCandidateKeys = new Set();
  reconstructionCertified = false;
  reconstructionMarkingFallbacks = 0;
  atomSpatialIndex = new Map();
  const seedIndex = overlapGrammar.replaySeedIndex;
  const seedType = overlapGrammar.molecular ? overlapGrammar.occurrences[seedIndex].type : learnedClusters.labels[seedIndex];
  const seedOccurrence = overlapGrammar.occurrences[seedIndex];
  const seed = { id: 1, type: seedType, position: seedOccurrence.position.clone(), rotation: seedOccurrence.rotation.clone(), occurrenceIndex: seedIndex, parentId: null, ruleId: null, depth: 0, atomIds: [] };
  const inverseSeedFrame = seed.rotation.clone().invert();
  const seedSites = overlapGrammar.molecular ? seedOccurrence.sites : [{ local: new THREE.Vector3(), species: referenceAtoms[seedIndex].species, center: true }];
  if (!overlapGrammar.molecular) learnedClusters.environments[seedIndex].shell.filter((neighbor) => neighbor.r <= motifShellCutoff()).forEach((neighbor) => seedSites.push({
    local: neighbor.vector.clone().multiplyScalar(referenceSpacing / referenceSpacingA).applyQuaternion(inverseSeedFrame),
    species: neighbor.atom.species, center: false,
  }));
  const canonicalSeed = canonicalKnownSites(seedSites.map((site) => ({
    ...site, p: site.local.clone().applyQuaternion(seed.rotation).add(seed.position),
  })));
  canonicalSeed.sites.forEach((site) => {
    const atom = addAtom(site.p, site.species, `C${seedType + 1}`, null, true);
    atom.referenceIndex = site.referenceIndex;
    atom.clusterIds = [seed.id];
    seed.atomIds.push(atom.id);
    indexAtom(atom);
  });
  placedClusters.push(seed);
  enqueueRulesFromPlacement(seed);
  replayIndex = referenceCoverageCount();
  const initialAudit = referenceCoverageAudit();
  reconstructionCertified = replayIndex === referenceCount() && atoms.length === referenceCount()
    && initialAudit.extraneousAtoms === 0 && initialAudit.duplicateAtoms === 0;
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
      .filter((neighbor) => neighbor.r <= motifShellCutoff())
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
    else if (![blueMaterial, greenMaterial, blueDimMaterial, greenDimMaterial, candidateMaterial, rejectedMaterial, ...elementMaterials.values(), ...dimElementMaterials.values(), ...clusterMaterials, ...markingMaterials.values()].includes(child.material)) child.material?.dispose?.();
  }
}

function buildConfinement() {
  clearGroup(confinementGroup);
  confinementGroup.rotation.set(0, 0, 0);
  const large = pipelineStage === 4;
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

function buildSectionHalos() {
  const centers = symbolCenters();
  const up = new THREE.Vector3(0, 1, 0);
  learnedClusters.clusters.forEach((_, cluster) => {
    const selectedKey = `m_C${cluster + 1}`;
    const dim = markingSelection && markingSelection !== selectedKey;
    const coefficients = currentSectionCoefficients(cluster);
    coefficients.forEach((coefficient, axisIndex) => {
      const compatible = coefficient >= 0;
      const strength = Math.min(1, Math.abs(coefficient) / .28);
      Array.from({ length: Math.min(4, sectionModel.channels) }, (_, level) => level).forEach((level) => {
        const direction = sectionModel.axes[axisIndex];
        const material = new THREE.MeshBasicMaterial({
          color: compatible ? markingColor(selectedKey) : COLORS.red,
          wireframe: true,
          transparent: true,
          opacity: dim ? .02 : (.08 + strength * .22) * (1 / (1 + level * .48)),
          depthWrite: false,
        });
        const mesh = new THREE.Mesh(new THREE.SphereGeometry(1, 8, 5), material);
        const reachOffset = .72 + sectionModel.reach * .08;
        mesh.position.copy(centers[cluster]).addScaledVector(direction, reachOffset + strength * .32 + level * .10);
        mesh.quaternion.setFromUnitVectors(up, direction);
        const transverse = .10 + strength * .15 + level * .038;
        const longitudinal = .20 + strength * .28 + level * .07;
        mesh.scale.set(transverse, longitudinal, transverse);
        if (markingSelection === selectedKey) mesh.scale.multiplyScalar(1.08);
        clusterGroup.add(mesh);
      });
    });
  });
}

function buildClusterOverlay() {
  clearGroup(clusterGroup);
  if (pipelineStage === 1 && learnedClusters) {
    learnedClusters.clusters.forEach((cluster, index) => {
      const atom = referenceAtoms[cluster.medoid];
      const geometry = cluster.coordination <= 6 ? new THREE.OctahedronGeometry(1.0)
        : cluster.coordination >= 11 ? new THREE.IcosahedronGeometry(1.12, 0)
          : new THREE.SphereGeometry(1.05, 8, 5);
      addClusterEnvelope(geometry, atom.p, clusterColor(index), 1 + Math.min(.22, cluster.spread * .035));
      const shellLines = [];
      referenceAtoms.forEach((neighbor) => {
        const distance = atom.p.distanceTo(neighbor.p) / referenceSpacing;
        if (neighbor !== atom && distance <= motifShellCutoff()) shellLines.push(atom.p, neighbor.p);
      });
      if (shellLines.length) clusterGroup.add(new THREE.LineSegments(
        new THREE.BufferGeometry().setFromPoints(shellLines),
        new THREE.LineBasicMaterial({ color: clusterColor(index), transparent: true, opacity: .72 }),
      ));
    });
  } else if (pipelineStage === 2) {
    symbolCenters().forEach((center, index) => {
      const cluster = learnedClusters.clusters[index];
      const geometry = cluster.coordination <= 6 ? new THREE.OctahedronGeometry(1.22)
        : cluster.coordination >= 11 ? new THREE.IcosahedronGeometry(1.3, 0)
          : new THREE.SphereGeometry(1.25, 8, 5);
      addClusterEnvelope(geometry, center, clusterColor(index));
    });
  } else if (pipelineStage === 3 && sectionModel) {
    symbolCenters().forEach((center, index) => {
      const cluster = learnedClusters.clusters[index];
      const geometry = cluster.coordination <= 6 ? new THREE.OctahedronGeometry(1.22)
        : cluster.coordination >= 11 ? new THREE.IcosahedronGeometry(1.3, 0)
          : new THREE.SphereGeometry(1.25, 8, 5);
      addClusterEnvelope(geometry, center, clusterColor(index));
    });
    buildSectionHalos();
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

function markingName(config, id) {
  const representation = MARKING_REPRESENTATIONS[config.representation]?.short || config.representation;
  const channels = config.channelMode === "auto" ? `auto→${config.channels}ch` : `${config.channels}ch`;
  return `M${String(id).padStart(2, "0")} · ${channels} · R${config.reach} · ${representation}`;
}

function compatibleMarkings() {
  const key = markingMaterialKey();
  return markingLibrary.filter((marking) => marking.materialKey === key);
}

function freezeCurrentMarking() {
  if (!sectionModel) return null;
  const config = { channels: sectionModel.channels, channelMode: sectionModel.channelMode,
    reach: sectionModel.reach, representation: sectionModel.representation };
  const materialKey = markingMaterialKey();
  let marking = markingLibrary.find((candidate) => candidate.materialKey === materialKey
    && candidate.config.channels === config.channels
    && (candidate.config.channelMode || "manual") === config.channelMode
    && candidate.config.reach === config.reach
    && candidate.config.representation === config.representation);
  if (!marking) {
    const serial = nextMarkingId++;
    marking = {
      id: `marking-${serial}`,
      name: markingName(config, serial),
      materialKey,
      materialName: currentMaterial().name,
      config,
      coefficients: sectionModel.curve.at(-1).coefficients.map((values) => [...values]),
      validationLoss: sectionModel.curve.at(-1).validationLoss,
      samples: referenceCount(),
    };
    markingLibrary.push(marking);
  } else {
    marking.coefficients = sectionModel.curve.at(-1).coefficients.map((values) => [...values]);
    marking.validationLoss = sectionModel.curve.at(-1).validationLoss;
    marking.samples = referenceCount();
  }
  activeMarkingId = marking.id;
  policySelect.value = "marked";
  persistMarkingLibrary();
  syncStageOptions();
  return marking;
}

function restartMarkingTraining() {
  if (pipelineStage !== 3) return;
  setPlaying(false);
  trainingProgress = 0;
  eventIndex = 0;
  markingSelection = null;
  sectionModel = learnSectionModel(referenceAtoms, currentMarkingConfig());
  markingCache.clear();
  buildClusterOverlay();
  rebuildWorld();
  updateUI();
  syncStageOptions();
}

function renderMarkingLibrary() {
  const compatible = compatibleMarkings();
  markingLibrarySelect.replaceChildren();
  const baseline = document.createElement("option");
  baseline.value = "action";
  baseline.textContent = "No marking · colored-action baseline";
  markingLibrarySelect.appendChild(baseline);
  const oracle = document.createElement("option");
  oracle.value = "direct";
  oracle.textContent = "Exact local oracle · diagnostic ceiling";
  markingLibrarySelect.appendChild(oracle);
  compatible.forEach((marking) => {
    const option = document.createElement("option");
    option.value = marking.id;
    option.textContent = `${marking.name} · loss ${marking.validationLoss.toFixed(3)}`;
    markingLibrarySelect.appendChild(option);
  });
  const wanted = policySelect.value === "marked" ? activeMarkingId : policySelect.value;
  markingLibrarySelect.value = [...markingLibrarySelect.options].some((option) => option.value === wanted)
    ? wanted : compatible.at(-1)?.id || "action";
  markingLibraryCount.textContent = `${compatible.length} saved`;
}

function renderPoseAtlas() {
  poseAtlas.replaceChildren();
  const total = orientationAtlas.reduce((sum, entry) => sum + entry.orientations, 0);
  poseAtlasTotal.textContent = `${total} poses · auto ${automaticMarkingChannels()}ch`;
  orientationAtlas.slice(0, 10).forEach((entry) => {
    const row = document.createElement("div");
    row.className = "pose-atlas-row";
    row.style.setProperty("--pose-color", `#${CLUSTER_COLORS[entry.cluster % CLUSTER_COLORS.length].toString(16).padStart(6, "0")}`);
    const code = document.createElement("code"); code.textContent = `C${entry.cluster + 1}`;
    const detail = document.createElement("span");
    const portRank = clusterPortRank(entry.cluster);
    const channels = recommendedChannelsForCluster(entry.cluster, entry.orientations);
    detail.textContent = `${entry.element} · ${entry.occurrences} occurrences · ${portRank} outgoing port role${portRank === 1 ? "" : "s"}`;
    const count = document.createElement("b");
    count.textContent = `${entry.orientations} pose${entry.orientations === 1 ? "" : "s"} → ${channels}ch`;
    row.append(code, detail, count);
    poseAtlas.appendChild(row);
  });
}

function syncStageOptions() {
  const visible = pipelineStage === 1 || pipelineStage === 3 || pipelineStage === 4;
  stageOptionsPanel.hidden = !visible;
  if (!visible) return;
  const clustering = pipelineStage === 1;
  const training = pipelineStage === 3;
  clusterGeometryOptions.hidden = !clustering;
  markingTrainingOptions.hidden = !training;
  growthSearchOptions.hidden = clustering || training;
  stageOptionsEyebrow.textContent = clustering ? "02 · geometric hypothesis" : training ? "03 · marking experiment" : "04 · search experiment";
  stageOptionsTitle.textContent = clustering ? "Learn the pose atlas" : training ? "Train a connection marking" : "Choose the search grammar";
  if (clustering) {
    geometryModeSelect.value = geometryMode;
    const latticeDetected = Boolean(detectedUnitCell);
    const periodicSupport = currentPbc().some(Boolean);
    geometryModeHint.textContent = geometryMode === "auto"
      ? latticeDetected ? "translation closure found" : periodicSupport ? "periodic window; basis unresolved" : "no lattice closure"
      : geometryMode === "lattice" ? "periodic constraint"
        : geometryMode === "module" ? "finite-rank aperiodic hypothesis" : "continuous placement hypothesis";
    geometryModeNote.textContent = geometryMode === "auto"
      ? `${latticeDetected ? "A translation basis was inferred" : periodicSupport ? "The input declares a periodic quotient, but the finite sample did not yield a stable basis" : "No stable translation basis was inferred"}; the pose classes still come only from the supplied positions.`
      : geometryMode === "lattice"
        ? "Periodic wrapping is applied before clustering; orientations are still quotiented by each cluster's proper symmetry."
        : geometryMode === "module"
          ? "No unit cell or periodic wrapping is assumed. Connections are learned from a discrete, finitely generated aperiodic pose/translation atlas—the natural hypothesis for model sets and quasicrystals."
          : "No discrete translation support is assumed. Every observed proper-SE(3) pose and connection must be learned from local geometry.";
    renderPoseAtlas();
    stageOptionsState.textContent = geometryMode === "module" ? "aperiodic module"
      : geometryMode === "offlattice" ? "free SE(3)"
        : latticeDetected ? "lattice candidate" : periodicSupport ? "periodic quotient" : "off-lattice";
    return;
  }
  const resolvedChannels = sectionModel?.channels || currentMarkingConfig().channels;
  markingChannelsHint.textContent = markingDraft.channels
    ? `${markingDraft.channels} coupled field${markingDraft.channels === 1 ? "" : "s"}`
    : `auto → ${resolvedChannels} from pose/port rank`;
  markingReachHint.textContent = `${markingDraft.reach} shell${markingDraft.reach === 1 ? "" : "s"}`;
  markingRepresentationHint.textContent = MARKING_REPRESENTATIONS[markingDraft.representation].short;
  markingChannelsSelect.value = String(markingDraft.channels);
  markingReachSelect.value = String(markingDraft.reach);
  markingRepresentationSelect.value = markingDraft.representation;
  if (training) {
    const complete = trainingProgress >= referenceCount();
    const config = currentMarkingConfig();
    const existing = compatibleMarkings().some((marking) => marking.config.channels === config.channels
      && (marking.config.channelMode || "manual") === config.channelMode
      && marking.config.reach === config.reach && marking.config.representation === config.representation);
    stageOptionsState.textContent = complete ? existing ? "saved" : "fit complete" : `${trainingProgress}/${referenceCount()}`;
    saveMarkingButton.disabled = !complete;
    saveMarkingButton.textContent = existing ? "Update library copy" : "Freeze to library";
    markingConfigNote.textContent = `${resolvedChannels} channels${markingDraft.channels ? " (manual)" : " (auto from pose/port rank)"} · support R=${sectionModel?.support.toFixed(2) || "—"}a · ${MARKING_REPRESENTATIONS[markingDraft.representation].label}. Channels transform with the learned pose atlas; they do not enumerate raw frame rotations.`;
  } else {
    renderMarkingLibrary();
    const active = selectedMarking();
    stageOptionsState.textContent = policySelect.value === "marked" && active ? active.name.split(" · ")[0] : "baseline";
    primitiveGrowthButton.classList.toggle("active", !hierarchyEnabled);
    primitiveGrowthButton.setAttribute("aria-pressed", String(!hierarchyEnabled));
    hierarchicalGrowthButton.classList.toggle("active", hierarchyEnabled);
    hierarchicalGrowthButton.setAttribute("aria-pressed", String(hierarchyEnabled));
    growthModeNote.textContent = hierarchyEnabled
      ? "Accepted clusters expose frozen ports and may promote into clusters². The selected marking ranks and prunes those exact candidate placements."
      : "Primitive-only mode permits the seed frontier but prevents accepted clusters from spawning another recursive frontier.";
  }
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
  currentCandidates = [];
  placedClusters = [];
  frontierCandidates = [];
  frontierCandidateKeys = new Set();
  rejectedCandidateKeys = new Set();
  atomSpatialIndex = new Map();
  replayIndex = 0;
  extensionIndex = 0;
  sectorCounts = new Array(BALANCE_DIRECTIONS.length).fill(0);
  nextAtomId = 1;
  liveStructuralStats = null;
  lastLiveStatsKey = "";
  coordinationSelection = null;
  trainingProgress = 0;
  markingSelection = null;
  liveOrderCache = { key: "", result: null };
  growthDeadline = 0;
  growthStartAtomCount = 0;
  growthStopReason = "";
  slowFrameSeconds = 0;
}

function enterPipelineStage(index, options = {}) {
  pipelineStage = Math.max(0, Math.min(4, index));
  stageElapsed = 0;
  setPlaying(false);
  resetCounters();
  rngState = 0x8f23ab17 ^ scenarioSelect.selectedIndex * 0x91e10da5 ^ confinementSelect.selectedIndex * 0x734a9d;
  referenceAtoms = makeReferenceConfiguration();
  referenceSpacing = scenarioSelect.value === "imported" ? .92 : medianNearestSpacing(referenceAtoms);
  referenceSpacingA = scenarioSelect.value === "imported"
    ? importedStructure.validation.medianNearestDistance
    : referenceSpacing / .92 * currentMaterial().spacingA;
  referenceStructuralStats = calculateStructuralStats(referenceAtoms, referenceSpacing, currentPbc().some(Boolean));
  learnedClusters = learnLocalEnvironmentClusters(referenceAtoms);
  learnedCover = buildExhaustiveClusterCover(referenceAtoms);
  detectedUnitCell = geometryMode === "module" || geometryMode === "offlattice" ? null : inferTranslationCell(referenceAtoms);
  trainedMarking = learnOverlapMarking(referenceAtoms);
  overlapGrammar = learnOverlapGrammar(referenceAtoms);
  orientationAtlas = learnOrientationAtlas();
  const compatibleActive = markingLibrary.find((marking) => marking.id === activeMarkingId
    && marking.materialKey === markingMaterialKey());
  const growthMarking = compatibleActive || (pipelineStage === 4 ? compatibleMarkings().at(-1) : null);
  if (pipelineStage === 4 && growthMarking) {
    activeMarkingId = growthMarking.id;
    markingDraft = { ...growthMarking.config,
      channels: growthMarking.config.channelMode === "auto" ? 0 : growthMarking.config.channels };
  }
  sectionModel = learnSectionModel(referenceAtoms, currentMarkingConfig());
  if (pipelineStage !== 3) trainingProgress = referenceCount();
  if (pipelineStage === 4) {
    const compatible = compatibleMarkings();
    if (!compatible.length) freezeCurrentMarking();
  }
  if (pipelineStage >= 3 && policySelect.value === "marked") seedTrainedMarking();
  if (pipelineStage === 0 || pipelineStage === 1) atoms = referenceAtoms.map((atom) => cloneAtom(atom));
  else if (pipelineStage === 2) atoms = makeRepresentatives().map((atom) => cloneAtom(atom));
  else if (pipelineStage === 3) atoms = makeRepresentatives().map((atom) => cloneAtom(atom));
  else initializeOffLatticeSearch();
  if (pipelineStage < 4) rebuildSpatialIndex();
  buildConfinement();
  clusterGroup.rotation.set(0, 0, 0);
  clusterGallery.hidden = pipelineStage !== 1;
  viewport.classList.toggle("cluster-gallery-mode", pipelineStage === 1);
  viewportHint.textContent = pipelineStage === 1 ? "independent SE(3) views · scroll for all types" : "drag to orbit · wheel to zoom";
  if (pipelineStage === 1) rebuildClusterGallery();
  buildClusterOverlay();
  updateStageNarrative();
  rebuildWorld();
  updateUI();
  updatePipelineButtons();
  syncStageOptions();
  frameStage();
  if (options.play) setPlaying(true);
}

function updatePipelineButtons() {
  pipelineSteps.forEach((button) => {
    const stage = Number(button.dataset.pipelineStage);
    button.classList.toggle("active", stage === pipelineStage);
    button.classList.toggle("complete", stage < pipelineStage);
    button.setAttribute("aria-current", stage === pipelineStage ? "step" : "false");
  });
  pipelineButton.classList.toggle("running", pipelineAuto);
  pipelineButton.textContent = pipelineAuto ? "Stop full pipeline" : "Run full pipeline";
}

function frameStage() {
  const large = pipelineStage === 4;
  const prototypes = pipelineStage === 2 || pipelineStage === 3;
  const target = new THREE.Vector3();
  controls.target.copy(target);
  camera.position.set(large ? 18 : prototypes ? 8 : 12.5, large ? 13 : prototypes ? 5.8 : 9.5, large ? 19 : prototypes ? 9 : 13.5);
  camera.updateProjectionMatrix();
}

function updateStageNarrative() {
  decisionEyebrow.textContent = "pipeline stage";
  decisionBadge.className = "badge neutral";
  const material = currentMaterial();
  const clusterCount = learnedClusters?.clusters.length || 0;
  const trainingPoint = trainedMarking ? currentTrainingPoint() : { samples: 0, discovered: 0, reusable: 0, overlaps: 0 };
  const narratives = [
    {
      eyebrow: "input · static atom coordinates", title: "Begin with the configuration we know", phase: "observed",
      caption: `${material.name}: element identities and Cartesian positions are supplied in ångströms; no environment labels are given.`, badge: "input",
      decision: material.name, copy: `The learner receives ${referenceCount()} element-labelled positions. ${material.cell}; measured median nearest-neighbor distance ${referenceSpacingA.toFixed(2)} Å.`,
      values: [material.elements.join(" / "), material.cell, `${referenceSpacingA.toFixed(2)} Å`, "1 configuration"],
    },
    {
      eyebrow: "learning · radial + angular environments", title: "Cluster the environments actually present", phase: `${clusterGalleryTypes().length} cover types`,
      caption: `${learnedCover.covered}/${referenceCount()} atoms are covered by ${learnedCover.placements.length} overlapping placements on the ${currentPbc().some(Boolean) ? "periodic quotient" : "finite non-periodic window"}. ${orientationAtlas.reduce((sum, entry) => sum + entry.orientations, 0)} symmetry-inequivalent cluster poses cover all observed occurrences.`, badge: "learn",
      decision: "Cluster cover and pose atlas computed", copy: "Element-resolved radial and angular descriptors define approximate isometry classes. Their centered colored point sets are compared in the laboratory frame, automatically quotienting each cluster's proper self-symmetries; uncovered components remain explicit residual types.",
      values: [`${descriptorCutoff().toFixed(2)}a cutoff`, `${orientationAtlas.reduce((sum, entry) => sum + entry.orientations, 0)} pose classes`, `${learnedCover.placements.length} placements`, learnedCover.molecular ? `${learnedCover.molecular.waters} H₂O · ${learnedCover.molecular.bridges} bridges · ${learnedCover.molecular.gaps} gaps` : `${learnedCover.residualTypes.length} residual types`],
    },
    {
      eyebrow: "encoding · clusters of clusters", title: "Promote repeated overlaps into finite connection states", phase: `${overlapGrammar.rules.length} rules`,
      caption: `${overlapGrammar.observations.toLocaleString()} directed overlaps are registered in SE(3). Compressed recurrent rules drive continuation; frozen one-off residual edges preserve exact known-window replay.`, badge: "encode",
      decision: "Higher-order cluster states learned", copy: "A recurring parent/source connection is now a reusable cluster-of-clusters symbol. Its finite state transports across arbitrary rotations; separation is normalized before reuse at the next recursive scale.",
      values: [`${clusterCount} local types`, `${overlapGrammar.rules.length} connection states`, `${overlapGrammar.recurring} recurring`, `${overlapGrammar.heldoutSupported} held-out supported`],
    },
    {
      eyebrow: "training · recursive connection sections", title: "Freeze a bounded marking across hierarchy levels", phase: `loss ${trainingPoint.validationLoss.toFixed(3)}`,
      caption: `${trainingPoint.samples}/${referenceCount()} centers processed · ${trainingPoint.overlaps.toLocaleString()} support overlaps · held-out mismatch ${trainingPoint.validationLoss.toFixed(3)}.`, badge: "train",
      decision: "Recursive marking training", copy: "Each local cluster begins with random directional ports. Observed higher-order connections shape the section; the resulting parent/source marking is frozen, rescaled, and evaluated on the next unseen cluster level.",
      values: [`fit ${sectionModel.channels}-channel m_C(x)`, `ball R=${sectionModel.support.toFixed(1)}a`, trainingPoint.validationLoss.toFixed(4), MARKING_REPRESENTATIONS[sectionModel.representation].label],
    },
    {
      eyebrow: "search · off-lattice recursive covering", title: "Let overlapping higher-order parents vote, then branch", phase: "seed cluster",
      caption: "Translated, rotated, and inflated parents continue past the known boundary. Each visual update is one maximal commuting frontier set: every displayed placement is valid in every permutation, while dependent residuals remain explicit tree branches.", badge: "search",
      decision: "Recursive consensus frontier initialized", copy: "The same frozen connection marking proposes the next scale. A frontier antichain is displayed together only after pairwise species and hard-core checks, plus a unique-new-support check for every accepted placement.",
      values: ["parent + φ(source−parent)", policySelect.value === "marked" ? selectedMarking()?.name || "active marking" : policySelect.value === "direct" ? "exact local oracle" : "unmarked action", hierarchyEnabled ? "clusters² promotion" : "primitive clusters", "branch residual"],
    },
  ];
  if (learnedCover.molecular) {
    narratives[1].eyebrow = "learning · molecular and gap cover";
    narratives[1].decision = "Molecular overlap cover computed";
    narratives[1].copy = "Species-resolved bond geometry discovers one H₂O motif. Shared hydrogen-bond bridges and empty oxygen-ring boundaries are promoted to connection clusters, then the periodic window is audited atom by atom.";
    narratives[2].title = "Register molecular bridges and gap-boundary ports";
    narratives[2].phase = `${overlapGrammar.reconstructionEdges} replay ports`;
    narratives[2].caption = `${overlapGrammar.reconstructionEdges} dependency-ordered molecular overlap ports connect a strict replay tree reaching ${overlapGrammar.replayReachable}/${referenceCount()} known sites.`;
    narratives[2].values = ["1 H₂O class", `${learnedCover.molecular.bridges} bridges`, `${learnedCover.molecular.gaps} ring gaps`, `${overlapGrammar.reconstructionEdges} replay ports`];
    narratives[4].caption = "The molecular search remains a strict tree under the hood. Dependency-ordered water, bridge, and gap placements reconstruct the known periodic window before any reusable continuation rule may act.";
    narratives[4].values = ["H₂O → bridge → gap", "shared atom support", "frozen replay ports", "branch residual"];
  }
  const item = narratives[pipelineStage];
  eventKind.textContent = ["INPUT", "LEARN", "ENCODE", "TRAIN", "SEARCH"][pipelineStage];
  stageEyebrow.textContent = item.eyebrow;
  stageTitle.textContent = item.title;
  phaseReadout.textContent = item.phase;
  captionAction.textContent = item.caption;
  decisionBadge.textContent = item.badge;
  decisionTitle.textContent = item.decision;
  decisionCopy.textContent = item.copy;
  [actionValue.textContent, domainValue.textContent, energyValue.textContent, resolverValue.textContent] = item.values;
}

function stateForCandidate(candidate, evaluation) {
  const rule = candidate.rule;
  return {
    action: `C${rule.from + 1} → C${rule.to + 1} · R${rule.id}`,
    domain: `r${rule.id}:C${rule.from + 1}>C${rule.to + 1}`,
    n15: evaluation.merged.length,
    n25: evaluation.sites.length,
    minimum: candidate.markingScore,
    clearance: evaluation.conflicts,
  };
}

function cacheDecision(state, energy) {
  const cache = policySelect.value === "marked" ? markingCache : actionCache;
  const key = policySelect.value === "marked" ? state.domain : state.action;
  let mark = cache.get(key);
  const reusable = policySelect.value !== "direct" && mark && mark.count >= 2;
  if (reusable) {
    grammarDecisions++;
    return { resolver: policySelect.value === "marked" ? "section overlap" : "colored action", interval: [mark.min - .08, mark.max + .08], reuse: true };
  }
  oracleCalls++;
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

function materializeCandidate(candidate, evaluation) {
  const parent = placedClusters.find((placement) => placement.id === candidate.parentId);
  const centerReferenceIndex = evaluation.sites.find((site) => site.center)?.referenceIndex;
  const placement = {
    id: placedClusters.length + 1, type: candidate.type,
    position: candidate.position.clone(), rotation: candidate.rotation.clone(),
    occurrenceIndex: overlapGrammar.molecular ? candidate.occurrenceIndex : Number.isInteger(centerReferenceIndex)
      && learnedClusters.labels[centerReferenceIndex] === candidate.type
      ? centerReferenceIndex : candidate.occurrenceIndex,
    parentId: candidate.parentId, ruleId: candidate.rule.id,
    depth: (parent?.depth || 0) + 1, atomIds: [],
  };
  evaluation.merged.forEach(({ atom }) => {
    atom.clusterIds ||= [];
    if (!atom.clusterIds.includes(placement.id)) atom.clusterIds.push(placement.id);
    placement.atomIds.push(atom.id);
  });
  evaluation.fresh.forEach((site) => {
    const atom = addAtom(site.p, site.species, `C${candidate.type + 1}`, nearestParent(site.p));
    if (Number.isInteger(site.referenceIndex)) atom.referenceIndex = site.referenceIndex;
    atom.clusterIds = [placement.id];
    placement.atomIds.push(atom.id);
    indexAtom(atom);
  });
  placedClusters.push(placement);
  sectorCounts[frontierSector(placement.position)]++;
  enqueueRulesFromPlacement(placement);
  candidate.rule.used = (candidate.rule.used || 0) + 1;
  extensionIndex++;
  if (evaluation.markingFallback) reconstructionMarkingFallbacks++;
  replayIndex = referenceCoverageCount();
  if (!reconstructionCertified && replayIndex === referenceCount()) {
    const audit = referenceCoverageAudit();
    reconstructionCertified = atoms.length === referenceCount()
      && audit.extraneousAtoms === 0 && audit.duplicateAtoms === 0;
    if (reconstructionCertified) {
      frontierCandidates = frontierCandidates.filter((frontier) => !frontier.rule.reconstructionOnly);
      frontierCandidateKeys = new Set(frontierCandidates.map((frontier) => frontier.key));
    }
  }
  return placement;
}

function performOffLatticeEvent() {
  const batch = commutingFrontierBatch();
  if (!batch.length) {
    pauseGrowth("Frontier exhausted: no learned overlap rule remains geometrically admissible.");
    return;
  }
  const selectedKeys = new Set(batch.map(({ candidate }) => candidate.key));
  frontierCandidates = frontierCandidates.filter((candidate) => !selectedKeys.has(candidate.key));
  batch.filter(({ evaluation }) => !evaluation.accepted).forEach(({ candidate }) => rejectedCandidateKeys.add(candidate.key));
  currentCandidates = batch.map(({ candidate, evaluation }) => ({
    p: candidate.position.clone(), accepted: evaluation.accepted,
    rotation: candidate.rotation.clone(), type: candidate.type,
  }));
  let acceptedInBatch = 0;
  let rejectedInBatch = 0;
  let freshInBatch = 0;
  let lastDecision = null;
  batch.forEach(({ candidate, evaluation: snapshotEvaluation }) => {
    let evaluation = snapshotEvaluation;
    let state = stateForCandidate(candidate, evaluation);
    if (!snapshotEvaluation.accepted) {
      rejectedDecisions++;
      rejectedInBatch++;
      appendHistory("reject", { type: "reject", depth: placedClusters.find((placement) => placement.id === candidate.parentId)?.depth || 0,
        action: state.action, family: evaluation.reason });
      lastDecision = { eventType: "reject", accepted: false, state, resolver: "geometric + section prune",
        energy: candidate.markingScore, interval: [candidate.markingScore, candidate.markingScore] };
      return;
    }
    // Re-evaluate against earlier members of this same batch. The batch builder
    // guarantees that this remains admissible in every permutation; this pass
    // converts any coincident same-species fresh sites into shared sites.
    evaluation = evaluateCandidate(candidate);
    state = stateForCandidate(candidate, evaluation);
    if (!evaluation.accepted) throw new Error("Commuting frontier batch lost permutation invariance");
    const decision = cacheDecision(state, candidate.markingScore);
    const placement = materializeCandidate(candidate, evaluation);
    acceptedDecisions++;
    acceptedInBatch++;
    freshInBatch += evaluation.fresh.length;
    appendHistory(decision.reuse ? "reuse" : "accept", { type: "accept", depth: placement.depth, action: state.action,
      family: `${evaluation.merged.length} shared · ${evaluation.fresh.length} new` });
    lastDecision = { eventType: decision.reuse ? "reuse" : "accept", accepted: true, state,
      resolver: decision.resolver, energy: candidate.markingScore, interval: decision.interval };
  });
  selectedKeys.forEach((key) => frontierCandidateKeys.delete(key));
  eventIndex += batch.length;
  captionAction.textContent = reconstructionCertified
    ? `Known-window certificate passed: ${referenceCount()}/${referenceCount()} species-labelled sites recovered one-to-one, with no duplicate or extraneous quotient sites. The observed one-off replay edges are now removed; continuation uses only the compressed learned grammar.`
    : `${acceptedInBatch} order-independent placements shown together (${freshInBatch} new atoms) · ${replayIndex}/${referenceCount()} known sites recovered`
      + `${reconstructionMarkingFallbacks ? ` · ${reconstructionMarkingFallbacks} marking false negatives bypassed by the replay certificate` : ""}`
      + `${rejectedInBatch ? ` · ${rejectedInBatch} invariant prunes flash red` : ""}.`;
  if (lastDecision) updateDecision(lastDecision);
  rebuildWorld();
  updateUI();
}

function advanceMarkingTraining(batchSize = 12) {
  trainingProgress = Math.min(referenceCount(), trainingProgress + batchSize);
  eventIndex = trainingProgress;
  buildClusterOverlay();
  rebuildWorld();
  updateUI();
}

function performEvent() {
  if (pipelineStage === 3) {
    if (trainingProgress < referenceCount()) advanceMarkingTraining();
    else enterPipelineStage(4, { play: pipelineAuto });
    return;
  }
  if (pipelineStage < 4) {
    enterPipelineStage(nextVisiblePipelineStage(pipelineStage), { play: pipelineAuto });
    return;
  }
  performOffLatticeEvent();
}

function rebuildWorld() {
  clearGroup(atomGroup);
  clearGroup(unitCellGroup);
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
      addInstances(atoms.filter((atom) => atom.species === symbol && selectedCoordination.neighborIds.has(atom.id) && !selectedCoordination.centerIds.has(atom.id)), getElementMaterial(symbol), (atom) => elementScale(atom.species) * 1.08);
      addInstances(atoms.filter((atom) => atom.species === symbol && selectedCoordination.centerIds.has(atom.id)), getElementMaterial(symbol), (atom) => elementScale(atom.species) * 1.3);
    });
  } else if (pipelineStage === 1 && learnedClusters) {
    learnedClusters.clusters.forEach((_, cluster) => {
      addInstances(atoms.filter((atom, index) => learnedClusters.labels[index] === cluster), clusterMaterials[cluster], (atom) => elementScale(atom.species));
    });
  } else if (pipelineStage === 3 && trainedMarking) {
    learnedClusters.clusters.forEach((_, cluster) => {
      const key = `m_C${cluster + 1}`;
      const selectedOut = markingSelection && markingSelection !== key;
      addInstances(atoms.filter((atom) => atom.family === `C${cluster + 1}`), getMarkingMaterial(key, selectedOut), (atom) => elementScale(atom.species) * (selectedOut ? .76 : atom.symbolCenter ? 1.16 : 1));
    });
  } else {
    currentMaterial().elements.forEach((symbol) => {
      addInstances(atoms.filter((atom) => atom.species === symbol), getElementMaterial(symbol), (atom) => elementScale(atom.species));
    });
  }

  if (bondToggle.checked) {
    const points = [];
    if (selectedCoordination?.centers.length) {
      selectedCoordination.edges.forEach(([center, neighbor]) => points.push(center.p, neighbor.p));
    } else if (pipelineStage === 3 && trainedMarking) {
      learnedClusters.clusters.forEach((_, cluster) => {
        const family = `C${cluster + 1}`;
        const center = atoms.find((atom) => atom.family === family && atom.symbolCenter);
        if (center) atoms.filter((atom) => atom.family === family && !atom.symbolCenter).forEach((atom) => points.push(center.p, atom.p));
      });
    } else atoms.forEach((atom) => {
      if (atom.parent) points.push(atom.parent.p, atom.p);
    });
    if (!selectedCoordination && pipelineStage < 4 && pipelineStage !== 3 && atoms.length <= 250) {
      for (let i = 0; i < atoms.length; i++) {
        for (let j = i + 1; j < atoms.length; j++) {
          const distance = atoms[i].p.distanceToSquared(atoms[j].p);
          if (distance > .55 && distance < 1.08) points.push(atoms[i].p, atoms[j].p);
        }
      }
    }
    if (points.length) bondGroup.add(new THREE.LineSegments(
      new THREE.BufferGeometry().setFromPoints(points),
      new THREE.LineBasicMaterial({
        color: selectedCoordination || pipelineStage === 3 ? COLORS.violet : 0x87afa5,
        transparent: true,
        opacity: selectedCoordination ? .9 : pipelineStage === 3 ? .38 : .2,
        depthTest: pipelineStage !== 3,
      }),
    ));
  }

  if (frontierToggle.checked && pipelineStage >= 4) {
    const targets = [...frontierCandidates].sort((first, second) => second.priority - first.priority).slice(0, FRONTIER_PREVIEW);
    if (targets.length) frontierGroup.add(new THREE.Points(
      new THREE.BufferGeometry().setFromPoints(targets.map((target) => target.position)),
      new THREE.PointsMaterial({ color: COLORS.mint, size: .085, transparent: true, opacity: .62, sizeAttenuation: true }),
    ));
    frontierMetric.textContent = String(targets.length);
  }

  currentCandidates.forEach((candidate) => {
    const mesh = new THREE.Mesh(candidateGeometry, candidate.accepted ? candidateMaterial : rejectedMaterial);
    mesh.position.copy(candidate.p);
    if (candidate.rotation) mesh.quaternion.copy(candidate.rotation);
    decisionGroup.add(mesh);
    if (markingToggle.checked) {
      const geometry = new THREE.IcosahedronGeometry(1.15, 0);
      const domain = new THREE.LineSegments(
        new THREE.WireframeGeometry(geometry),
        new THREE.LineBasicMaterial({ color: COLORS.violet, transparent: true, opacity: .18 }),
      );
      domain.position.copy(candidate.p);
      if (candidate.rotation) domain.quaternion.copy(candidate.rotation);
      decisionGroup.add(domain);
    }
  });
  if (selectedCoordination?.centers.length) {
    const centerMarkers = new THREE.InstancedMesh(candidateGeometry, candidateMaterial, selectedCoordination.centers.length);
    selectedCoordination.centers.forEach((center, index) => {
      dummy.position.copy(center.p);
      dummy.scale.setScalar(1.3);
      dummy.updateMatrix();
      centerMarkers.setMatrixAt(index, dummy.matrix);
    });
    centerMarkers.instanceMatrix.needsUpdate = true;
    decisionGroup.add(centerMarkers);
  }
  buildDetectedUnitCell();
}

function updateDecision(event) {
  decisionEyebrow.textContent = "current tree decision";
  const reuse = event.eventType === "reuse";
  decisionBadge.className = `badge ${reuse ? "reuse" : event.accepted ? "accept" : "reject"}`;
  decisionBadge.textContent = reuse ? "reused" : event.accepted ? "accepted" : "rejected";
  decisionTitle.textContent = `${event.state.action} ${event.accepted ? "survives" : "fails"}`;
  decisionCopy.textContent = reuse
    ? "The transformed local sections agree on their shared support, so the learned marking resolves this placement without another exact local evaluation."
    : !event.accepted
      ? "This rigid placement violates shared-support, confinement, species, hard-core, or transported-section constraints, so the branch is pruned while the remaining frontier stays live."
    : event.resolver === "speculative branch"
      ? "The placement is provisionally attached to the search stack while its exposed interfaces are checked."
      : "The local oracle evaluates the proposed placement and records its result under the bounded geometric section.";
  actionValue.textContent = event.state.action;
  domainValue.textContent = event.state.domain;
  energyValue.textContent = event.interval ? `[${event.interval[0].toFixed(2)}, ${event.interval[1].toFixed(2)}]` : "geometric prune";
  resolverValue.textContent = event.resolver;
  eventKind.textContent = reuse ? "MARK REUSE" : event.accepted ? "ACCEPT" : "REJECT";
}

function updateUI() {
  updateRecursiveBenchmark();
  eventCounter.textContent = String(eventIndex).padStart(4, "0");
  const material = currentMaterial();
  if (pipelineStage === 0) {
    atomLabel.textContent = "ATOMS"; atomMetric.textContent = String(referenceCount()); atomDelta.textContent = `${material.name} · xyz in Å`;
    frontierLabel.textContent = "ELEMENTS"; frontierMetric.textContent = String(material.elements.length); frontierDelta.textContent = material.elements.join(" / ");
    oracleLabel.textContent = "LABELS GIVEN"; oracleMetric.textContent = "0"; oracleDelta.textContent = "clusters must be inferred";
    reuseLabel.textContent = "GROWTH MODE"; reuseMetric.textContent = "OPEN"; reuseDelta.textContent = "restartable 1–2 minute bursts";
  } else if (pipelineStage === 1) {
    atomLabel.textContent = "PLACEMENTS"; atomMetric.textContent = String(learnedCover.placements.length); atomDelta.textContent = `overlapping ${currentPbc().some(Boolean) ? "periodic" : "open"} cover`;
    frontierLabel.textContent = "ISOMETRY TYPES"; frontierMetric.textContent = String(clusterGalleryTypes().length); frontierDelta.textContent = "one rotating scene per type";
    oracleLabel.textContent = "COVERAGE"; oracleMetric.textContent = `${Math.round(learnedCover.covered / referenceCount() * 100)}%`; oracleDelta.textContent = `${learnedCover.covered} / ${referenceCount()} atoms · ${learnedCover.complete ? "complete" : "incomplete"}`;
    const gapTypes = learnedCover.molecular?.gaps ? 1 : learnedCover.residualTypes.length;
    reuseLabel.textContent = "GAP TYPES"; reuseMetric.textContent = String(gapTypes); reuseDelta.textContent = learnedCover.molecular?.gaps ? `${learnedCover.molecular.gaps} oxygen-ring boundaries` : learnedCover.residualTypes.length ? "promoted to explicit clusters" : "none after overlap cover";
  } else if (pipelineStage === 2) {
    atomLabel.textContent = "SYMBOLS"; atomMetric.textContent = String(learnedClusters.clusters.length); atomDelta.textContent = "one per learned medoid";
    frontierLabel.textContent = "SE(3) RULES"; frontierMetric.textContent = String(overlapGrammar.rules.length); frontierDelta.textContent = "arbitrary quaternion + translation";
    oracleLabel.textContent = "PAIR OBSERVATIONS"; oracleMetric.textContent = overlapGrammar.observations.toLocaleString(); oracleDelta.textContent = `${overlapGrammar.recurring} rules recur`;
    reuseLabel.textContent = "REPLAY GRAPH"; reuseMetric.textContent = `${overlapGrammar.replayReachable}/${referenceCount()}`; reuseDelta.textContent = `${overlapGrammar.reconstructionEdges.toLocaleString()} frozen observed edges · removed after certificate`;
  } else if (pipelineStage === 3) {
    const point = currentTrainingPoint();
    stageEyebrow.textContent = "training · recursive sections on cluster connections";
    stageTitle.textContent = trainingProgress < referenceCount() ? "Connection markings emerge on higher-order cluster states" : "Recursive GCTS marking frozen for transfer";
    decisionTitle.textContent = trainingProgress < referenceCount() ? "Fitting parent/source overlap consistency" : "Marked connections ready to rescale";
    decisionCopy.textContent = trainingProgress < referenceCount()
      ? "The local prototypes stay fixed while their connection sections morph. Type-colored lobes mark recurring parent/source overlaps; red lobes mark absent or failed connections. Their frames rotate with each placement; no physical potential is used."
      : "The learned connection sections now travel with higher-order cluster types and normalize their separation by recursive scale. Search rejects or branches when transported markings disagree.";
    phaseReadout.textContent = `loss ${point.validationLoss.toFixed(3)}`;
    captionAction.textContent = `${point.samples}/${referenceCount()} centers · ${point.overlaps.toLocaleString()} support overlaps · fit ${point.trainLoss.toFixed(3)} · holdout ${point.validationLoss.toFixed(3)}.`;
    atomLabel.textContent = "SECTION SAMPLES"; atomMetric.textContent = `${point.samples}/${referenceCount()}`; atomDelta.textContent = `${point.fitSamples} fit · ${point.holdoutSamples} held out`;
    frontierLabel.textContent = "SUPPORT OVERLAPS"; frontierMetric.textContent = point.overlaps.toLocaleString(); frontierDelta.textContent = "section agreement constraints";
    oracleLabel.textContent = "FIT MISMATCH"; oracleMetric.textContent = point.trainLoss.toFixed(3); oracleDelta.textContent = "overlap + connection ports";
    reuseLabel.textContent = "HOLDOUT MISMATCH"; reuseMetric.textContent = point.validationLoss.toFixed(3); reuseDelta.textContent = "unseen local sections";
    actionValue.textContent = "fit m_C(x)";
    domainValue.textContent = `ball R=${sectionModel.support.toFixed(1)}a`;
    energyValue.textContent = point.validationLoss.toFixed(4);
    resolverValue.textContent = `${sectionModel.channels}ch · ${MARKING_REPRESENTATIONS[sectionModel.representation].short}`;
  } else {
    stageEyebrow.textContent = "search · recursive off-lattice covering";
    stageTitle.textContent = hierarchyEnabled
      ? "Transport parents, merge overlap votes, promote clusters²"
      : "Search one primitive-cluster frontier without promotion";
    phaseReadout.textContent = playing && growthDeadline
      ? `${placedClusters.length.toLocaleString()} clusters · ${formatDuration(growthTimeRemaining())} left`
      : `${atoms.length.toLocaleString()} atoms · ${placedClusters.length.toLocaleString()} clusters`;
    atomLabel.textContent = "EXPLICIT ATOMS";
    atomMetric.textContent = atoms.length.toLocaleString();
    atomDelta.textContent = `${replayIndex}/${referenceCount()} unique known sites · ${placedClusters.length} rigid placements`;
    frontierLabel.textContent = "SE(3) FRONTIER";
    frontierMetric.textContent = frontierCandidates.length.toLocaleString();
    frontierDelta.textContent = "untried learned attachments";
    oracleLabel.textContent = "LOCAL ORACLE";
    oracleMetric.textContent = oracleCalls > 9999 ? `${(oracleCalls / 1000).toFixed(1)}k` : String(oracleCalls);
    oracleDelta.textContent = `${acceptedDecisions + rejectedDecisions} tree decisions`;
    reuseLabel.textContent = "GCTS REUSE";
    const resolved = Math.max(1, acceptedDecisions + rejectedDecisions);
    reuseMetric.textContent = `${Math.round(grammarDecisions / resolved * 100)}%`;
    reuseDelta.textContent = growthStopReason || `${Math.max(0, atoms.length - growthStartAtomCount).toLocaleString()} atoms added this burst`;
  }
  updateOrderAudit();
  renderStack();
  renderMarkings();
  renderStructureStats();
  renderLegend();
  syncStageOptions();
}

function renderLegend() {
  speciesLegend.replaceChildren();
  if (pipelineStage === 3 && sectionModel) {
    legendHeading.textContent = "Local marking sections";
    learnedClusters.clusters.forEach((cluster, index) => {
      const key = `m_C${index + 1}`;
      const row = document.createElement("span");
      const swatch = document.createElement("i");
      swatch.className = "cluster-swatch";
      swatch.style.setProperty("--swatch", `#${markingColor(key).getHexString()}`);
      row.append(swatch, document.createTextNode(`${key}(x) · C${index + 1} prototype · learned from ${cluster.count}`));
      speciesLegend.appendChild(row);
    });
    const failed = document.createElement("span");
    const failedSwatch = document.createElement("i");
    failedSwatch.className = "cluster-swatch";
    failedSwatch.style.setProperty("--swatch", "#ff6d71");
    failed.append(failedSwatch, document.createTextNode("red lobe · absent / failed connection"));
    speciesLegend.appendChild(failed);
  } else if (pipelineStage === 1 && learnedClusters) {
    legendHeading.textContent = "Cover isometry types";
    clusterGalleryTypes().forEach((cluster, index) => {
      const row = document.createElement("span");
      const swatch = document.createElement("i");
      swatch.className = "cluster-swatch";
      swatch.style.setProperty("--swatch", cluster.residual ? "#ff6d71" : `#${CLUSTER_COLORS[index % CLUSTER_COLORS.length].toString(16).padStart(6, "0")}`);
      row.append(swatch, document.createTextNode(`${cluster.residual ? "gap" : "C"}${index + 1} · ${cluster.element || cluster.species} · ${cluster.count}`));
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
  if (pipelineStage === 3 && trainedMarking) {
    const visibleEdges = trainedMarking.edges.filter((edge) => edge.first < trainingProgress && edge.second < trainingProgress);
    stackDepth.textContent = `${visibleEdges.length.toLocaleString()} observations`;
    searchStack.replaceChildren();
    visibleEdges.slice(0, 6).forEach((edge) => {
      const row = document.createElement("li");
      const shared = document.createElement("b"); shared.textContent = `×${edge.shared}`;
      const action = document.createElement("span"); action.textContent = `C${edge.firstCluster} ↔ C${edge.secondCluster}`;
      const state = document.createElement("em"); state.textContent = `${edge.distance.toFixed(2)}a`;
      row.append(shared, action, state);
      searchStack.appendChild(row);
    });
    if (!visibleEdges.length) {
      const row = document.createElement("li"); row.className = "empty-row"; row.textContent = "Overlap observations appear as samples are processed."; searchStack.appendChild(row);
    }
    return;
  }
  const rows = stackHistory.slice(-6).reverse();
  stackDepth.textContent = pipelineStage < 4 ? `stage ${visiblePipelineOrdinal(pipelineStage)}/4` : `depth ${Math.max(0, ...atoms.map((atom) => atom.depth))}`;
  searchStack.replaceChildren();
  if (!rows.length) {
    const row = document.createElement("li");
    row.className = "empty-row";
    row.textContent = pipelineStage < 4 ? "Tree search begins after marking training." : "Accepted branches appear here.";
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

function selectMarkingDomain(domain) {
  markingSelection = markingSelection === domain ? null : domain;
  buildClusterOverlay();
  rebuildWorld();
  updateUI();
}

function renderMarkings() {
  markingHeading.textContent = pipelineStage < 2 ? "learned vocabulary" : pipelineStage === 2 ? "rigid overlap rules" : pipelineStage === 3 ? "local section bundle" : "active section marking";
  markingTable.replaceChildren();
  if (pipelineStage === 0) {
    markCount.textContent = "not learned";
    const p = document.createElement("p"); p.textContent = "No motif or cluster labels are supplied."; markingTable.appendChild(p); return;
  }
  const learned = learnedCover.molecular ? clusterGalleryTypes().map((cluster) => [
    `${cluster.label} · ${cluster.element}`,
    cluster.gap ? "empty-region boundary" : "species + distances",
    `×${learnedCover.placements.filter((placement) => placement.type === cluster.type).length}`,
  ]) : learnedClusters.clusters.map((cluster, index) => [
    `C${index + 1} · ${cluster.element} medoid`,
    `z${cluster.coordination} · σ${cluster.spread.toFixed(1)}`,
    `×${cluster.count}`,
  ]);
  const rigidRules = overlapGrammar.rules.slice(0, 10).map((rule) => [
    `R${rule.id} · C${rule.from + 1}→C${rule.to + 1}`,
    `θ${THREE.MathUtils.radToDeg(rule.rotationAngle).toFixed(0)}° · |t|${rule.translation.length().toFixed(2)}a`,
    `×${rule.count}`,
  ]);
  const cache = policySelect.value === "marked" ? markingCache : actionCache;
  const sectionEntries = learnedClusters.clusters.map((cluster, index) => {
    const count = learnedClusters.labels.slice(0, trainingProgress).filter((label) => label === index).length;
    return [`m_C${index + 1}`, `loss ${sectionLossForCluster(index).toFixed(3)}`, `${count}/${cluster.count}`];
  });
  const activeEntries = [...cache.entries()].sort((a, b) => b[1].count - a[1].count).slice(0, 5).map(([key, value]) => [key, `${value.min.toFixed(2)}…${value.max.toFixed(2)}`, `×${value.count}`]);
  const entries = pipelineStage < 2 ? learned : pipelineStage === 2 ? rigidRules : pipelineStage === 3 ? sectionEntries : activeEntries;
  markCount.textContent = pipelineStage < 2 ? `${learned.length} learned` : pipelineStage === 2 ? `${overlapGrammar.rules.length} SE(3) rules` : pipelineStage === 3 ? `${sectionEntries.length} sections · rank ${sectionModel.channels}` : `${cache.size} active`;
  if (!entries.length) {
    const p = document.createElement("p");
    p.textContent = pipelineStage === 3 && trainingProgress === 0
      ? "Press Play or Step to process atom-centered training samples."
      : policySelect.value === "marked" ? "No reusable local section was learned." : "This policy does not preload GCTS markings.";
    markingTable.appendChild(p); return;
  }
  entries.forEach(([key, interval, count]) => {
    const row = document.createElement("div"); row.className = "mark-row";
    if (pipelineStage === 3) {
      row.tabIndex = 0;
      row.setAttribute("role", "button");
      row.setAttribute("aria-label", `${key}; isolate its connection level sets`);
      row.setAttribute("aria-pressed", markingSelection === key ? "true" : "false");
      row.style.borderLeftColor = `#${markingColor(key).getHexString()}`;
      row.addEventListener("click", () => selectMarkingDomain(key));
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectMarkingDomain(key); }
      });
    }
    const code = document.createElement("code"); code.textContent = key; code.title = key;
    const span = document.createElement("span"); span.textContent = interval;
    const b = document.createElement("b"); b.textContent = count;
    row.append(code, span, b); markingTable.appendChild(row);
  });
}


function setPlaying(value) {
  playing = value;
  if (playing && pipelineStage === 4) {
    growthDeadline = performance.now() + growthDurationSeconds() * 1000;
    growthStartAtomCount = atoms.length;
    growthStopReason = "";
    slowFrameSeconds = 0;
  } else if (!playing) growthDeadline = 0;
  playIcon.textContent = playing ? "Ⅱ" : "▶";
  playLabel.textContent = playing ? "Pause" : pipelineStage === 4 ? `Grow ${growthDurationSeconds() / 60} min` : "Play";
  playButton.setAttribute("aria-label", playing ? "Pause pipeline" : pipelineStage === 4 ? `Grow explicit atoms for ${growthDurationSeconds() / 60} minute${growthDurationSeconds() === 60 ? "" : "s"}` : "Play pipeline");
  document.querySelector(".run-state").classList.toggle("running", playing);
  runStateText.textContent = playing ? `Stage ${visiblePipelineOrdinal(pipelineStage)} running` : `Stage ${visiblePipelineOrdinal(pipelineStage)} paused`;
}

function pauseGrowth(reason) {
  const added = Math.max(0, atoms.length - growthStartAtomCount);
  growthStopReason = reason;
  setPlaying(false);
  pipelineAuto = false;
  updatePipelineButtons();
  captionAction.textContent = `${reason} ${added.toLocaleString()} explicit atoms were added in this burst; click Grow again to continue from the same frontier.`;
  updateUI();
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
playButton.addEventListener("click", () => {
  if (playing && pipelineStage === 4) pauseGrowth("Paused by user.");
  else setPlaying(!playing);
  updateUI();
});
stepButton.addEventListener("click", () => { setPlaying(false); performEvent(); });
resetButton.addEventListener("click", () => enterPipelineStage(pipelineStage));
scenarioSelect.addEventListener("change", () => enterPipelineStage(0));
periodicTableButton.addEventListener("click", () => setPeriodicTableOpen(periodicTablePanel.hidden));
periodicCloseButton.addEventListener("click", () => setPeriodicTableOpen(false));
periodicClearButton.addEventListener("click", () => {
  selectedDatabaseElements = [];
  renderPeriodicSelection();
});
elementPresetButtons.forEach((button) => button.addEventListener("click", () => {
  selectedDatabaseElements = button.dataset.elementPreset.split(",");
  renderPeriodicSelection();
}));
randomMaterialButton.addEventListener("click", async () => {
  randomMaterialButton.disabled = true;
  databaseStatus.className = "import-status";
  const requestedElements = [...selectedDatabaseElements];
  databaseStatus.textContent = `Searching NOMAD for exactly ${requestedElements.join(" + ")}…`;
  try {
    const { structure, total, selectedOffset } = await randomNomadStructure(requestedElements);
    const repetitions = structure.metadata.repetitions || [1, 1, 1];
    const primitiveCount = structure.metadata.primitiveAtomCount || structure.atoms.length;
    activateImportedStructure(structure, `NOMAD entry ${structure.metadata.entryId}`, databaseStatus);
    databaseStatus.textContent = `${importSummary(structure, importedStructure.validation)} · ${primitiveCount} atoms expanded ${repetitions.join("×")} · random ${selectedOffset + 1}/${total.toLocaleString()}`;
    databaseSourceLink.href = structure.metadata.sourceUrl;
    databaseSourceLink.textContent = `Open NOMAD entry ${structure.metadata.entryId.slice(0, 10)}… ↗`;
  } catch (error) {
    databaseStatus.className = "import-status invalid";
    databaseStatus.textContent = `Database query failed: ${error.message}`;
  } finally {
    randomMaterialButton.disabled = selectedDatabaseElements.length === 0;
  }
});
structureFileInput.addEventListener("change", async () => {
  const [file] = structureFileInput.files;
  if (!file) return;
  try {
    await importStructureFile(file);
  } catch (error) {
    importStatus.className = "import-status invalid";
    importStatus.textContent = `Import failed: ${error.message}`;
  } finally {
    structureFileInput.value = "";
  }
});
loadFixtureButton.addEventListener("click", async () => {
  try {
    importStatus.className = "import-status";
    importStatus.textContent = "Loading the bundled extXYZ fixture…";
    const response = await fetch("./fixtures/nacl-64.extxyz");
    if (!response.ok) throw new Error(`fixture request returned ${response.status}`);
    activateImportedStructure(parseStructureText(await response.text(), "nacl-64.extxyz"), "bundled fixture · nacl-64.extxyz");
  } catch (error) {
    importStatus.className = "import-status invalid";
    importStatus.textContent = `Fixture failed: ${error.message}`;
  }
});
confinementSelect.addEventListener("change", () => enterPipelineStage(pipelineStage));
geometryModeSelect.addEventListener("change", () => {
  geometryMode = geometryModeSelect.value;
  enterPipelineStage(1);
});
markingChannelsSelect.addEventListener("change", () => {
  markingDraft.channels = Number(markingChannelsSelect.value);
  restartMarkingTraining();
});
markingReachSelect.addEventListener("change", () => {
  markingDraft.reach = Number(markingReachSelect.value);
  restartMarkingTraining();
});
markingRepresentationSelect.addEventListener("change", () => {
  markingDraft.representation = markingRepresentationSelect.value;
  restartMarkingTraining();
});
restartMarkingButton.addEventListener("click", restartMarkingTraining);
saveMarkingButton.addEventListener("click", () => {
  if (trainingProgress < referenceCount()) return;
  freezeCurrentMarking();
  updateUI();
});
markingLibrarySelect.addEventListener("change", () => {
  const value = markingLibrarySelect.value;
  if (value === "action" || value === "direct") {
    policySelect.value = value;
  } else {
    const marking = markingLibrary.find((candidate) => candidate.id === value);
    if (!marking) return;
    activeMarkingId = marking.id;
    markingDraft = { ...marking.config,
      channels: marking.config.channelMode === "auto" ? 0 : marking.config.channels };
    policySelect.value = "marked";
    persistMarkingLibrary();
  }
  if (pipelineStage === 4) enterPipelineStage(4);
});
trainVariantButton.addEventListener("click", () => {
  const marking = selectedMarking();
  if (marking) markingDraft = { ...marking.config,
    channels: marking.config.channelMode === "auto" ? 0 : marking.config.channels };
  enterPipelineStage(3);
});
primitiveGrowthButton.addEventListener("click", () => {
  if (!hierarchyEnabled) return;
  hierarchyEnabled = false;
  if (pipelineStage === 4) enterPipelineStage(4);
});
hierarchicalGrowthButton.addEventListener("click", () => {
  if (hierarchyEnabled) return;
  hierarchyEnabled = true;
  if (pipelineStage === 4) enterPipelineStage(4);
});
policySelect.addEventListener("change", () => {
  if (pipelineStage === 4) enterPipelineStage(4);
  else {
    markingCache.clear(); actionCache.clear(); grammarDecisions = 0;
    if (policySelect.value === "marked" && pipelineStage >= 3 && trainedMarking) seedTrainedMarking();
    updateUI();
  }
});
speedInput.addEventListener("input", () => { speedOutput.textContent = speedInput.value; });
growthDurationSelect.addEventListener("change", () => { if (!playing) setPlaying(false); updateUI(); });
[markingToggle, bondToggle, frontierToggle].forEach((input) => input.addEventListener("change", rebuildWorld));
rotateToggle.addEventListener("change", () => { controls.autoRotate = rotateToggle.checked; });
coordClearButton.addEventListener("click", () => selectCoordination(coordinationSelection));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !periodicTablePanel.hidden) setPeriodicTableOpen(false);
});
document.addEventListener("pointerdown", (event) => {
  if (periodicTablePanel.hidden) return;
  if (periodicTablePanel.contains(event.target) || periodicTableButton.contains(event.target)) return;
  setPeriodicTableOpen(false);
});

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
  const rawDelta = (now - lastFrame) / 1000;
  const delta = Math.min(.1, rawDelta);
  lastFrame = now;
  controls.autoRotate = rotateToggle.checked;
  controls.update();
  if (playing) {
    if (pipelineStage === 3) {
      eventAccumulator += delta * Number(speedInput.value);
      while (eventAccumulator >= 1) {
        eventAccumulator--;
        performEvent();
        if (pipelineStage !== 3 || !playing) break;
      }
    } else if (pipelineStage < 4) {
      stageElapsed += delta;
      if (stageElapsed >= 1.8) enterPipelineStage(nextVisiblePipelineStage(pipelineStage), { play: true });
    } else {
      if (growthDeadline && now >= growthDeadline) {
        pauseGrowth("Timed growth complete.");
      } else {
        slowFrameSeconds = rawDelta > .13 ? slowFrameSeconds + rawDelta : Math.max(0, slowFrameSeconds - rawDelta * .5);
        if (atoms.length > 1000 && slowFrameSeconds > 4) pauseGrowth("Paused to protect browser responsiveness.");
      }
      if (!playing) {
        renderer.render(scene, camera);
        return;
      }
      eventAccumulator += delta * Number(speedInput.value);
      while (eventAccumulator >= 1) {
        eventAccumulator--;
        performEvent();
        if (!playing) break;
      }
    }
  } else eventAccumulator = 0;
  if (currentCandidates.length) decisionGroup.children.forEach((child, index) => {
    if (index % (markingToggle.checked ? 2 : 1) !== 0) return;
    child.rotation.y += delta * 1.8;
    child.rotation.x += delta * .7;
  });
  clusterGroup.rotation.y += pipelineStage === 2 ? delta * .08 : 0;
  drawClusterGallery(now);
  renderer.render(scene, camera);
}

restoreMarkingLibrary();
buildPeriodicTable();
enterPipelineStage(0);
resize();
requestAnimationFrame(animate);
