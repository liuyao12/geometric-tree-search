import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { parseStructureText, validateStructure } from "./structure-io.js";
import { randomNomadStructure } from "./structure-database.js";
import { PERIODIC_ELEMENTS } from "./periodic-table.js";
import {
  executeIceMolecularAnchorGrowth,
  validateIceMolecularPortArtifact,
} from "./ice-molecular-anchor-growth.js";
import { discoverIrregularCover } from "./irregular-cover.js?v=20260824-1";
import { generateAmorphousMixture } from "./amorphous-glass.js?v=20260824-1";
import { powderStructureFactor, summarizeStructureFactor } from "./structure-observables.js?v=20260824-1";
import { compositionBalanceDelta, learnCompositionTarget } from "./composition-balance.js?v=20260824-1";
import {
  discoverFiniteMolecularComponents,
  discoverMolecularConnectionTopology,
} from "./molecular-components.js?v=20260824-2";
import {
  aggregateMarkingReadout,
  coloredConnectionChirality,
} from "./marking-representation-readout.js?v=20260824-1";
import {
  coloredAngularViolations,
  coloredCoordinationDeficit,
  coloredGeometricStrain,
  coordinationEnvelopeFor,
  exclusionForPair,
  learnColoredAngularEnvelopes,
  learnColoredCoordinationEnvelopes,
  learnColoredDistanceEnvelopes,
} from "./colored-distance-envelopes.js?v=20260824-5";

const ICE_MOLECULAR_PORT_ARTIFACT = await fetch(new URL(
  "./ice-molecular-port-artifact.json?v=20260824-1", import.meta.url)).then((response) => {
  if (!response.ok) throw new Error(`Cannot load frozen ice port artifact: ${response.status}`);
  return response.json();
});
validateIceMolecularPortArtifact(ICE_MOLECULAR_PORT_ARTIFACT);

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
const translationSupport = $("translationSupport");
const rotationSupport = $("rotationSupport");
const channelRankSupport = $("channelRankSupport");
const molecularHypothesisState = $("molecularHypothesisState");
const molecularHypothesisEvidence = $("molecularHypothesisEvidence");
const molecularHypothesisRoute = $("molecularHypothesisRoute");
const poseAtlasTotal = $("poseAtlasTotal");
const poseAtlas = $("poseAtlas");
const markingTrainingOptions = $("markingTrainingOptions");
const inheritedGeometryMode = $("inheritedGeometryMode");
const inheritedPoseCount = $("inheritedPoseCount");
const inheritedChannelCount = $("inheritedChannelCount");
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
const markingSearchModeSelect = $("markingSearchModeSelect");
const geometryPreferenceSelect = $("geometryPreferenceSelect");
const strainWeightSelect = $("strainWeightSelect");
const strainWeightHint = $("strainWeightHint");
const compositionPreferenceSelect = $("compositionPreferenceSelect");
const surfacePreferenceSelect = $("surfacePreferenceSelect");
const growthSchedulingSelect = $("growthSchedulingSelect");
const growthSchedulingHint = $("growthSchedulingHint");
const trainVariantButton = $("trainVariantButton");
const primitiveGrowthButton = $("primitiveGrowthButton");
const hierarchicalGrowthButton = $("hierarchicalGrowthButton");
const growthModeNote = $("growthModeNote");
const policyComparison = $("policyComparison");
const policyComparisonState = $("policyComparisonState");
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
const downloadReceiptButton = $("downloadReceiptButton");
const copyReceiptButton = $("copyReceiptButton");
const receiptStatus = $("receiptStatus");
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
const rdfPairSelect = $("rdfPairSelect");
const structureObservableSelect = $("structureObservableSelect");
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
const strainValue = $("strainValue");
const compositionValue = $("compositionValue");
const surfaceValue = $("surfaceValue");
const resolverValue = $("resolverValue");
const constraintLedger = $("constraintLedger");
const stackDepth = $("stackDepth");
const searchStack = $("searchStack");
const markingHeading = $("markingHeading");
const markCount = $("markCount");
const markingTable = $("markingTable");
const growthCertificateSection = $("growthCertificateSection");
const growthCertificateState = $("growthCertificateState");
const certificateReplay = $("certificateReplay");
const certificateContinuation = $("certificateContinuation");
const certificateHierarchy = $("certificateHierarchy");
const certificateBoundary = $("certificateBoundary");
const growthCertificateNote = $("growthCertificateNote");
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
const DEFAULT_GEOMETRIC_STRAIN_WEIGHT = .16;
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
  iceIh: { name: "ice Ih", elements: ["H", "O"], spacingA: .9572, cell: "hexagonal ice · proton-ordered fixture", periodicWindow: true, order: "crystal", symmetry: "P6₃/mmc oxygen network", audit: "molecular cover + hydrogen-bond graph", motifShellCutoff: 3.12, descriptorCutoff: 3.25, overlapDistanceCutoff: 3.35, icePolytype: "Ih", note: "The learner must discover H₂O molecules, then use overlapping water-dimer and oxygen-ring connection clusters to traverse the crystal." },
  iceIc: { name: "ice Ic", elements: ["H", "O"], spacingA: .9572, cell: "cubic ice · proton-ordered fixture", periodicWindow: true, order: "crystal", symmetry: "Fd-3m oxygen network", audit: "molecular cover + hydrogen-bond graph", motifShellCutoff: 3.12, descriptorCutoff: 3.25, overlapDistanceCutoff: 3.35, icePolytype: "Ic", note: "A cubic-ice control with the same H₂O motif but a different cluster-of-clusters connection grammar." },
  dryIce: { name: "dry ice CO₂-I", elements: ["C", "O"], spacingA: 1.168, cell: "cubic molecular solid · Pa-3 · a = 5.578 Å", periodicWindow: true, referenceCellA: 16.734, order: "crystal", symmetry: "Pa-3 · #205", audit: "generic molecular + connection + void cover", motifShellCutoff: 4.2, descriptorCutoff: 4.6, overlapDistanceCutoff: 4.8, molecularFixture: "dry-ice-pa3", note: "A non-water molecular-crystal control: the learner must discover linear CO₂ components and intermolecular connection/void topology without receiving the CO₂ formula or Pa-3 label." },
  graphene: { name: "graphene monolayer", elements: ["C"], spacingA: 1.42, cell: "single hexagonal sheet", order: "crystal", symmetry: "p6/mmm layer group", audit: "2D translations + diffraction", intrinsicDimension: 2, planarLayers: [{ angle: 0, zA: 0, species: ["C", "C"] }], note: "A one-component intrinsic-2D positive control learned after arbitrary embedding in 3D." },
  hbn: { name: "aligned hBN bilayer", elements: ["B", "N"], spacingA: 1.44, cell: "aligned hexagonal sheets · 3.33 Å separation", order: "crystal", symmetry: "commensurate bilayer", audit: "2D translations + finite registry", intrinsicDimension: 2, planarLayers: [{ angle: 0, zA: -1.665, species: ["B", "N"] }, { angle: 0, zA: 1.665, species: ["B", "N"] }], note: "A commensurate bilayer whose finite interlayer registry can be represented by a bounded local marking." },
  competition: { name: "NaCl rocksalt", elements: ["Na", "Cl"], spacingA: 2.82, cell: "Fm3̅m · a = 5.640 Å", periodicWindow: true, order: "crystal", symmetry: "Fm-3m · #225", audit: "space group", note: "A periodic positive control: translation is the cheap ceiling, while the learner must recover it blindly." },
  random: { name: "Cu₆₄Zr₃₆ metallic glass", elements: ["Cu", "Zr"], spacingA: 2.72, cell: "periodic amorphous hard-core cell", periodicWindow: true, order: "amorphous", symmetry: "no stable long-range group", audit: "partial RDF + local motifs + S(q)", note: "No unique continuation is implied. The target is an ensemble; the deterministic browser fixture is a continuous random hard-core packing, not a perturbed lattice or an MD trajectory." },
  iqc: { name: "Al–Cu–Fe IQC approximant", elements: ["Al", "Cu", "Fe"], spacingA: 2.55, cell: "icosahedral approximant", periodicWindow: false, order: "quasicrystal", symmetry: "icosahedral point symmetry", audit: "superspace + diffraction", note: "An ordinary 3D space group is insufficient; inflation, reciprocal-module, and phason statistics are required." },
  moire: { name: "30° twisted hBN bilayer", elements: ["B", "N"], spacingA: 1.44, cell: "two hexagonal sheets · 3.33 Å separation", order: "quasicrystal", symmetry: "12-fold quasiperiodic order", audit: "2D diffraction + absence of common translations", intrinsicDimension: 2, planarLayers: [{ angle: 0, zA: -1.665, species: ["B", "N"] }, { angle: Math.PI / 6, zA: 1.665, species: ["B", "N"] }], note: "Each sheet is periodic, while their 30° union has no common translation lattice." },
  bc8: { name: "silicon BC8-like network", elements: ["Si"], spacingA: 2.35, cell: "BC8 target · a = 6.636 Å", periodicWindow: true, order: "crystal", symmetry: "Ia-3 · #206", audit: "space group", note: "A nontrivial crystalline control for topology, coordination, and species-preserving symmetry recovery." },
};
const RECURSIVE_BENCHMARKS = {
  iceIh: { hierarchy: [1, 8, "pose domains"], curve: [27, 43, 51], mark: "unanimous orientation domains", action: "2 exact blind O frontiers", speed: "16 → 8 exact · then fixed", gate: "pass anchor · molecular growth open", status: "limit", note: "The physically corrected fixture obeys the Bernal–Fowler ice rules: every H₂O donates twice and every O–O connection carries exactly one proton. The known periodic window has one H₂O class, 3 decorated bridge classes, and 33 decorated O₆ ring-boundary classes; together their occurrences cover 216/216 atoms. The sealed gate learns 8 proper-SE(3) ports on a disjoint 201-atom window. Factoring mutually exclusive H₂O poses emits 16/16 and then 8/8 correct unseen oxygen anchors before a safe fixed point. Proton orientations remain unresolved, so full-molecule, stationary, and exponential ice growth stay red." },
  iceIc: { hierarchy: [1, 8, "pose domains"], curve: [15, 27], mark: "Ih ports → Ic alternatives", action: "1 exact cross-polytype frontier", speed: "12 exact · then safe fixed point", gate: "progress · cross-polytype blind transfer", status: "limit", note: "The Ih-fitted 8-port grammar transfers to a disjoint cubic-ice seed without refitting or target access. Its first unseen oxygen frontier is 12/12 exact and the whole-molecule path reaches 100% oxygen recall, but premature proton choices lower precision. Domain unanimity rejects unsupported depth-2 anchors rather than emitting false sites. This isolates the remaining task as a bounded proton-orientation connection marking, not a new lattice backend." },
  dryIce: { hierarchy: ["molecule", "pair", "void"], curve: [3, 324], mark: "generic molecular ports", action: "94 replay decisions", speed: "324 / 324 · fixed point", gate: "exact known-window control", status: "limit", note: "A saved Pa-3 CO₂-I window exercises the generic, non-water molecular front end. Starting from one 3-atom CO₂ component, 94 deterministic covering decisions produce 95 rigid placements at causal depth 14 and replay all 324/324 known colored sites with zero missing, duplicate, or extraneous atoms. The frozen observed frontier then exhausts with zero outside-window emissions. This is an exact target-aware known-window replay—not autonomous continuation, stationarity, an exponential rule, or a physical growth rate." },
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
RECURSIVE_BENCHMARKS.iqc.connection.macro.selection = "fourth-block GCTS · consumed: 3/1,102 exact nine-action parents → 21/512 exact paths · fresh disjoint: 0/1,087 exact parents, 197/512 exact terminal blocks, best 11/12 · 535 s runtime green · parent supply red";
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
let coordinationCapacityPrunes = 0;
let angularEnvelopePrunes = 0;
let acceptedGeometricStrain = 0;
let rejectedGeometricStrain = 0;
let acceptedCompositionDelta = 0;
let rejectedCompositionDelta = 0;
let acceptedSurfaceDeficit = 0;
let rejectedSurfaceDeficit = 0;
let constraintNeighborhoodEvaluations = 0;
let constraintNeighborhoodSiteTotal = 0;
let maximumConstraintNeighborhoodSites = 0;
let lastPolicyComparison = null;
let atomSpatialIndex = new Map();
let trainingProgress = 0;
let markingSelection = null;
let liveOrderCache = { key: "", result: null };
let orderPrototypeLibrary = null;
let growthDeadline = 0;
let growthStartAtomCount = 0;
let growthStopReason = "";
let slowFrameSeconds = 0;
let iceAnchorTrace = null;
let iceAnchorWaveIndex = 0;
let importedStructure = null;
let selectedDatabaseElements = ["Na", "Cl"];
let markingDraft = { channels: 0, reach: 2, representation: "sites" };
let markingLibrary = [];
let activeMarkingId = null;
let markingSearchMode = "single";
let hierarchyEnabled = true;
let geometryPreference = "strain";
let geometricStrainWeight = DEFAULT_GEOMETRIC_STRAIN_WEIGHT;
let compositionPreference = "soft";
let surfacePreference = "soft";
let growthScheduling = "commuting";
let nextMarkingId = 1;
let geometryMode = "auto";
let orientationAtlas = [];
let selectedGalleryCluster = 0;
let rdfPairSelection = "all";
let structureObservableSelection = "rdf";
let coloredDistanceEnvelopes = null;
let coloredCoordinationEnvelopes = null;
let coloredAngularEnvelopes = null;
let compositionTarget = null;

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
  if (pipelineStage < 4) return {
    order: "not classified", structure: "classification begins after growth", symmetry: "withheld", confidence: 0,
    note: "The supplied configuration is used to learn geometry, not to preassign a phase. RDF, coordination, S(q), translation closure, and prototype labels are evaluated only after Material Growth begins.",
  };
  const source = classificationSample();
  if (source.length < 32) return {
    order: "insufficient sample", structure: "—", symmetry: "—", confidence: 0,
    note: `Waiting for at least 32 live atoms; ${source.length} are currently available.`,
  };
  const key = `${scenarioSelect.value}:${pipelineStage}:${Math.floor(source.length / 16)}:${Math.floor(atoms.length / 96)}`;
  if (liveOrderCache.key === key && liveOrderCache.result) return liveOrderCache.result;
  const stats = calculateStructuralStats(source, referenceSpacing);
  const matches = getOrderPrototypeLibrary().map((prototype) => {
    const rdfError = normalizedDistributionDistance(prototype.stats.rdf, stats.rdf);
    const coordinationError = normalizedDistributionDistance(prototype.stats.coordination, stats.coordination);
    const structureFactorError = normalizedDistributionDistance(
      ensureStructureFactor(prototype.stats).values, ensureStructureFactor(stats).values);
    return { ...prototype, evidenceMatch: Math.max(0, Math.min(1,
      1 - .30 * rdfError - .58 * coordinationError - .20 * structureFactorError)) };
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
  const result = {
    order, structure, symmetry, confidence,
    note: `Live reconstructed core: best RDF + coordination + geometric powder S(q) match across ${matches.length} prototypes${detectedUnitCell ? `; translation closure ${Math.round(translationClosure * 100)}%` : ""}. Unit-scattering S(q) is posthoc evidence—not experimental intensity or a growth input. ${best.material.audit} remains the required independent confirmation; prototype labels and space groups are not growth inputs.`,
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

function intrinsicPlaneNormal(source) {
  if (source.length < 3) return null;
  const centroid = source.reduce((sum, atom) => sum.add(atom.p), new THREE.Vector3())
    .multiplyScalar(1 / source.length);
  const first = source.reduce((best, atom) => {
    const vector = atom.p.clone().sub(centroid);
    return vector.lengthSq() > best.lengthSq() ? vector : best;
  }, new THREE.Vector3());
  if (first.lengthSq() < 1e-12) return null;
  const axis = first.clone().normalize();
  const second = source.reduce((best, atom) => {
    const vector = atom.p.clone().sub(centroid);
    const perpendicular = vector.clone().sub(axis.clone().multiplyScalar(vector.dot(axis)));
    return perpendicular.lengthSq() > best.lengthSq() ? perpendicular : best;
  }, new THREE.Vector3());
  if (second.lengthSq() < 1e-12) return null;
  return new THREE.Vector3().crossVectors(axis, second.normalize()).normalize();
}

function calculateStructuralStats(source, spacing, periodic = false,
  intrinsicDimension = currentMaterial().intrinsicDimension === 2 ? 2 : 3, requestedMaximumRadius = null) {
  const rdf = new Array(RDF_BINS).fill(0);
  const rdfCountsByPair = new Map();
  const pairDistances = [];
  const coordination = new Array(13).fill(0);
  if (!source.length) return { rdf, rdfByPair: {}, dimension: intrinsicDimension,
    maximumRadius: requestedMaximumRadius || RDF_MAX_RADIUS, edgeCorrection: periodic ? "periodic minimum image" : "finite-window translation",
    pairDistances, coordination, meanCoordination: 0, count: 0, neighborCounts: [], neighborLists: [] };

  const neighbors = new Array(source.length).fill(0);
  const neighborLists = Array.from({ length: source.length }, () => []);
  const minimum = new THREE.Vector3(Infinity, Infinity, Infinity);
  const maximum = new THREE.Vector3(-Infinity, -Infinity, -Infinity);
  source.forEach((atom) => {
    minimum.min(atom.p);
    maximum.max(atom.p);
  });

  const paddedSize = maximum.clone().sub(minimum).divideScalar(spacing).addScalar(1);
  const activeAxes = [0, 1, 2].sort((first, second) => paddedSize.getComponent(second) - paddedSize.getComponent(first))
    .slice(0, intrinsicDimension);
  const planeNormal = intrinsicDimension === 2 ? intrinsicPlaneNormal(source) : null;
  const cell = periodic ? currentCell() : null;
  const normalizedCellLengths = cell?.map((vector) => vector.length() / referenceSpacingA) || [];
  const naturalMaximumRadius = periodic && normalizedCellLengths.length
    ? Math.min(RDF_MAX_RADIUS, Math.min(...normalizedCellLengths) * .48)
    : Math.min(RDF_MAX_RADIUS, Math.min(...activeAxes.map((axis) => paddedSize.getComponent(axis))) * .45);
  const maximumRadius = Math.max(.5, requestedMaximumRadius || naturalMaximumRadius);
  const pairCounts = source.reduce((counts, atom) => {
    counts.set(atom.species, (counts.get(atom.species) || 0) + 1);
    return counts;
  }, new Map());

  for (let first = 0; first < source.length; first++) {
    for (let second = first + 1; second < source.length; second++) {
      // S(q) is the powder average of the actual finite observation.  Keep its
      // direct pair distance separate from the RDF's periodic minimum-image or
      // finite-window edge correction.
      const directVector = source[second].p.clone().sub(source[first].p).divideScalar(spacing);
      const scatteringDistance = planeNormal
        ? Math.sqrt(Math.max(0, directVector.lengthSq() - directVector.dot(planeNormal) ** 2))
        : directVector.length();
      pairDistances.push(scatteringDistance);
      const vector = periodic
        ? periodicDisplacement(source[first], source[second]).divideScalar(referenceSpacingA)
        : source[second].p.clone().sub(source[first].p).divideScalar(spacing);
      const normalizedDistance = vector.length();
      if (normalizedDistance < maximumRadius) {
        const bin = Math.min(RDF_BINS - 1, Math.floor(normalizedDistance / maximumRadius * RDF_BINS));
        const overlapFraction = periodic ? 1 : activeAxes.reduce((fraction, axis) =>
          fraction * Math.max(1e-6, 1 - Math.abs(vector.getComponent(axis)) / paddedSize.getComponent(axis)), 1);
        const weight = 1 / overlapFraction;
        rdf[bin] += weight;
        const pair = [source[first].species, source[second].species].sort().join("|");
        if (!rdfCountsByPair.has(pair)) rdfCountsByPair.set(pair, new Array(RDF_BINS).fill(0));
        rdfCountsByPair.get(pair)[bin] += weight;
      }
      if (normalizedDistance <= COORDINATION_CUTOFF) {
        neighbors[first]++;
        neighbors[second]++;
        neighborLists[first].push(second);
        neighborLists[second].push(first);
      }
    }
  }

  let measure = activeAxes.reduce((product, axis) => product * paddedSize.getComponent(axis), 1);
  if (periodic && cell && intrinsicDimension === 3) {
    measure = Math.abs(cell[0].dot(new THREE.Vector3().crossVectors(cell[1], cell[2]))) / (referenceSpacingA ** 3);
  } else if (periodic && cell && intrinsicDimension === 2) {
    measure = Math.max(...[[0, 1], [0, 2], [1, 2]].map(([first, second]) =>
      new THREE.Vector3().crossVectors(cell[first], cell[second]).length())) / (referenceSpacingA ** 2);
  }
  measure = Math.max(1, measure);
  const shellMeasure = (inner, outer) => intrinsicDimension === 2
    ? Math.PI * (outer ** 2 - inner ** 2)
    : 4 / 3 * Math.PI * (outer ** 3 - inner ** 3);
  for (let bin = 0; bin < RDF_BINS; bin++) {
    const inner = bin / RDF_BINS * maximumRadius;
    const outer = (bin + 1) / RDF_BINS * maximumRadius;
    const shell = shellMeasure(inner, outer);
    const idealPairs = source.length * (source.length - 1) / (2 * measure) * shell;
    rdf[bin] = idealPairs > 0 ? rdf[bin] / idealPairs : 0;
  }
  const rdfByPair = Object.fromEntries([...rdfCountsByPair].map(([pair, counts]) => {
    const [first, second] = pair.split("|");
    const combinations = first === second
      ? pairCounts.get(first) * (pairCounts.get(first) - 1) / 2
      : pairCounts.get(first) * pairCounts.get(second);
    return [pair, counts.map((value, bin) => {
      const inner = bin / RDF_BINS * maximumRadius;
      const outer = (bin + 1) / RDF_BINS * maximumRadius;
      const idealPairs = combinations / measure * shellMeasure(inner, outer);
      return idealPairs > 0 ? value / idealPairs : 0;
    })];
  }));

  neighbors.forEach((value) => coordination[Math.min(12, value)]++);
  for (let index = 0; index < coordination.length; index++) coordination[index] /= source.length;
  const meanCoordination = neighbors.reduce((sum, value) => sum + value, 0) / source.length;
  return { rdf, rdfByPair, dimension: intrinsicDimension, maximumRadius,
    edgeCorrection: periodic ? "periodic minimum image" : "finite-window translation",
    pairDistances, coordination, meanCoordination, count: source.length, neighborCounts: neighbors, neighborLists };
}

function ensureStructureFactor(stats) {
  if (!stats.structureFactor) {
    stats.structureFactor = powderStructureFactor(stats.pairDistances || [], stats.count, stats.dimension);
    stats.structureFactor.summary = summarizeStructureFactor(stats.structureFactor);
  }
  return stats.structureFactor;
}

function currentLiveStructure() {
  const source = pipelineStage === 4
    ? (atoms.length > ANALYSIS_WINDOW_COUNT ? [...atoms].sort((first, second) => first.p.lengthSq() - second.p.lengthSq()).slice(0, ANALYSIS_WINDOW_COUNT) : atoms)
    : [];
  const key = `${pipelineStage}:${atoms.length}:${replayIndex}`;
  if (key !== lastLiveStatsKey) {
    const livePeriodic = currentPbc().some(Boolean)
      && atoms.every((atom) => Number.isInteger(atom.referenceIndex));
    liveStructuralStats = calculateStructuralStats(source, referenceSpacing, livePeriodic,
      currentMaterial().intrinsicDimension === 2 ? 2 : 3, referenceStructuralStats?.maximumRadius || RDF_MAX_RADIUS);
    lastLiveStatsKey = key;
  }
  return { source, stats: liveStructuralStats || calculateStructuralStats([], referenceSpacing, false,
    currentMaterial().intrinsicDimension === 2 ? 2 : 3, referenceStructuralStats?.maximumRadius || RDF_MAX_RADIUS) };
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

function rdfPairLabel(key) {
  if (key === "all") return "all element pairs";
  return key.split("|").join("–");
}

function syncRdfPairOptions() {
  const keys = ["all", ...Object.keys(referenceStructuralStats?.rdfByPair || {}).sort()];
  const fingerprint = keys.join(",");
  if (rdfPairSelect.dataset.keys !== fingerprint) {
    rdfPairSelect.replaceChildren(...keys.map((key) => {
      const option = document.createElement("option");
      option.value = key;
      option.textContent = rdfPairLabel(key);
      return option;
    }));
    rdfPairSelect.dataset.keys = fingerprint;
  }
  if (!keys.includes(rdfPairSelection)) rdfPairSelection = "all";
  rdfPairSelect.value = rdfPairSelection;
}

function selectedRdf(stats) {
  return rdfPairSelection === "all" ? stats.rdf : stats.rdfByPair?.[rdfPairSelection] || new Array(RDF_BINS).fill(0);
}

function rdfTailSummary(values) {
  const tail = values.slice(Math.floor(values.length * .62));
  const mean = tail.reduce((sum, value) => sum + value, 0) / Math.max(1, tail.length);
  const rmsFromUnity = Math.sqrt(tail.reduce((sum, value) => sum + (value - 1) ** 2, 0) / Math.max(1, tail.length));
  return { mean, rmsFromUnity };
}

function renderTrainingStats() {
  const point = currentTrainingPoint();
  const visibleCurve = sectionModel.curve.slice(0, trainingProgress);
  const totalSamples = markingSampleCount();
  rdfPairSelect.hidden = true;
  structureObservableSelect.hidden = true;
  rdfEyebrow.textContent = "GCTS training curve";
  rdfTitle.textContent = "section mismatch";
  rdfStatus.textContent = `${point.samples}/${totalSamples} ${sectionModel.sampleKind}s · ${point.fitSamples} fit / ${point.holdoutSamples} holdout`;
  coordEyebrow.textContent = "learned section atlas";
  coordTitle.textContent = "connection-port strength";
  coordStatus.textContent = `support R = ${sectionModel.support.toFixed(1)}a · rank ${sectionModel.channels}`;
  coordClearButton.hidden = true;
  rdfChart.setAttribute("aria-label", "Training and held-out mismatch of local GCTS marking sections");
  coordChart.setAttribute("aria-label", "Directional connection-port strength of each learned cluster marking section");

  rdfChart.replaceChildren();
  drawChartFrame(rdfChart, "samples", "loss");
  [0, .25, .5, .75, 1].map((fraction) => Math.round(totalSamples * fraction)).forEach((tick) => {
    const x = 29 + tick / totalSamples * 323;
    rdfChart.append(svgNode("text", { x, y: 108, class: "chart-label", "text-anchor": "middle" }, String(tick)));
  });
  const maximum = Math.max(.001, sectionModel.initialPoint.trainLoss, sectionModel.initialPoint.validationLoss);
  const curvePath = (field) => visibleCurve.map((entry, index) => {
    const x = 29 + entry.samples / totalSamples * 323;
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
  const amplitudes = markingPrototypeTypes().map((_, cluster) => Math.sqrt(currentSectionCoefficients(cluster).reduce((sum, value) => sum + value ** 2, 0)));
  const maximumAmplitude = Math.max(.01, ...amplitudes);
  const barStep = 323 / amplitudes.length;
  amplitudes.forEach((amplitude, index) => {
    const height = amplitude / maximumAmplitude * 84;
    const key = `m_${markingPrototypeName(index)}`;
    const color = `#${markingColor(key).getHexString()}`;
    coordChart.append(svgNode("rect", {
      x: 29 + index * barStep + 2,
      y: 96 - height,
      width: Math.max(2, barStep - 4),
      height,
      fill: color,
      opacity: markingSelection && markingSelection !== key ? .18 : .72,
    }));
    const label = learnedCover?.molecular ? ["H₂O", "bridge", "O₆ gap"][index] || `C${index + 1}` : `C${index + 1}`;
    coordChart.append(svgNode("text", { x: 29 + (index + .5) * barStep, y: 108, class: "chart-label", "text-anchor": "middle" }, label));
  });
  setChartLegend(coordLegend, [["known-key", "type color = compatible connection port"], ["live-key", "red lobe = absent / failed port"]]);
}

function renderStructureStats() {
  if (!referenceStructuralStats) return;
  if (pipelineStage === 3) {
    renderTrainingStats();
    return;
  }
  structureObservableSelect.hidden = false;
  structureObservableSelect.value = structureObservableSelection;
  rdfPairSelect.hidden = structureObservableSelection !== "rdf";
  syncRdfPairOptions();
  const dimension = referenceStructuralStats.dimension;
  coordEyebrow.textContent = "first-shell coordination";
  coordTitle.innerHTML = "P(z), r<sub>c</sub> = 1.32a";
  coordChart.setAttribute("aria-label", "Coordination number distribution for known positions and live reconstruction");
  const liveWindowLabel = pipelineStage === 4 && atoms.length > ANALYSIS_WINDOW_COUNT ? "live central analysis window" : "live reconstruction";
  setChartLegend(rdfLegend, [["known-key", "known positions"], ["live-key", liveWindowLabel]]);
  setChartLegend(coordLegend, [["known-key", "known positions"], ["live-key", liveWindowLabel], ["", "click z to show all current shells"]]);
  const { stats: live } = currentLiveStructure();
  const selected = selectedCoordinationDetail();
  coordStatus.textContent = coordinationSelection === null
    ? `mean z ${referenceStructuralStats.meanCoordination.toFixed(1)} · ${live.count ? live.meanCoordination.toFixed(1) : "—"}`
    : `${coordinationSelection === 12 ? "z≥12" : `z=${coordinationSelection}`} · ${selected?.matchCount || 0} centers · ${selected?.edges.length || 0} links`;
  coordClearButton.hidden = coordinationSelection === null;

  rdfChart.replaceChildren();
  if (structureObservableSelection === "sq") {
    const knownSq = ensureStructureFactor(referenceStructuralStats);
    const liveSq = ensureStructureFactor(live);
    rdfEyebrow.textContent = `${dimension}D finite-observation powder average`;
    rdfTitle.textContent = "geometric S(q) · unit scattering weights";
    rdfChart.setAttribute("aria-label", "Geometric powder structure factor for known positions and live reconstruction");
    const summary = knownSq.summary;
    const liveSummary = live.count > 1 ? liveSq.summary : null;
    rdfStatus.textContent = `peak qa ${summary.peakQ.toFixed(1)} · S ${summary.peakHeight.toFixed(1)}${liveSummary ? ` → ${liveSummary.peakHeight.toFixed(1)}` : ""}`;
    rdfStatus.title = "Debye-style finite-window powder average with unit atom weights. It omits X-ray form factors, neutron scattering lengths, occupancies, thermal motion, and instrument response.";
    drawChartFrame(rdfChart, "q a", "S");
    const maximum = Math.max(1, ...knownSq.values, ...liveSq.values) * 1.08;
    const unityY = 96 - Math.min(1, 1 / maximum) * 84;
    rdfChart.append(svgNode("line", { x1: 29, y1: unityY, x2: 352, y2: unityY, class: "chart-guide" }));
    [5, 10, 15, 20].filter((tick) => tick >= knownSq.qMin && tick <= knownSq.qMax).forEach((tick) => {
      const x = 29 + (tick - knownSq.qMin) / (knownSq.qMax - knownSq.qMin) * 323;
      rdfChart.append(svgNode("text", { x, y: 108, class: "chart-label", "text-anchor": "middle" }, String(tick)));
    });
    rdfChart.append(svgNode("path", { id: "sqKnownPath", d: linePath(knownSq.values, maximum), class: "chart-known" }));
    if (live.count > 1) rdfChart.append(svgNode("path", { id: "sqLivePath", d: linePath(liveSq.values, maximum), class: "chart-live" }));
    setChartLegend(rdfLegend, [["known-key", "known · unit weights"], ["live-key", `${liveWindowLabel} · geometry only`]]);
  } else {
    const knownRdf = selectedRdf(referenceStructuralStats);
    const liveRdf = selectedRdf(live);
    const knownTail = rdfTailSummary(knownRdf);
    const liveTail = live.count > 1 ? rdfTailSummary(liveRdf) : null;
    rdfEyebrow.textContent = referenceStructuralStats.edgeCorrection === "periodic minimum image"
      ? `${dimension}D periodic-cell RDF` : `${dimension}D edge-corrected finite-window RDF`;
    rdfTitle.textContent = `g${dimension}D(${rdfPairSelection === "all" ? "all" : rdfPairLabel(rdfPairSelection)}; r / a)`;
    rdfChart.setAttribute("aria-label", "Radial distribution function for known positions and live reconstruction");
    rdfStatus.textContent = `tail ⟨g⟩ ${knownTail.mean.toFixed(2)}${liveTail ? ` → ${liveTail.mean.toFixed(2)}` : ""} · RMS₁ ${knownTail.rmsFromUnity.toFixed(2)}`;
    rdfStatus.title = currentMaterial().order === "amorphous"
      ? "An amorphous RDF has short-range peaks but should approach g(r)=1 at long range; it is not flat at every radius."
      : `Known ${referenceCount()} atoms; ${liveWindowLabel} ${live.count}.`;
    drawChartFrame(rdfChart, "r / a", "g");
    const rdfMaximum = Math.max(1, ...knownRdf, ...liveRdf) * 1.08;
    const unityY = 96 - Math.min(1, 1 / rdfMaximum) * 84;
    rdfChart.append(svgNode("line", { x1: 29, y1: unityY, x2: 352, y2: unityY, class: "chart-guide" }));
    const maximumRadius = referenceStructuralStats.maximumRadius;
    Array.from({ length: Math.floor(maximumRadius) }, (_, index) => index + 1).forEach((tick) => {
      const x = 29 + tick / maximumRadius * 323;
      rdfChart.append(svgNode("text", { x, y: 108, class: "chart-label", "text-anchor": "middle" }, String(tick)));
    });
    rdfChart.append(svgNode("path", { id: "rdfKnownPath", d: linePath(knownRdf, rdfMaximum), class: "chart-known" }));
    if (live.count > 1) rdfChart.append(svgNode("path", { id: "rdfLivePath", d: linePath(liveRdf, rdfMaximum), class: "chart-live" }));
  }

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
  // The tetrahedral oxygen graph is 4-regular. Orient deterministic Euler
  // circuits so every oxygen has two incoming and two outgoing edges, then put
  // one proton on each outgoing edge. This enforces the Bernal--Fowler rule
  // exactly; choosing two neighbors independently can create zero or two
  // protons on one O--O connection and is not a valid ice configuration.
  const edgeMap = new Map();
  neighbors.forEach((shell, index) => shell.forEach(({ other }) => {
    const pair = index < other ? [index, other] : [other, index];
    edgeMap.set(`${pair[0]}:${pair[1]}`, pair);
  }));
  const graphEdges = [...edgeMap.values()].sort((first, second) => first[0] - second[0] || first[1] - second[1]);
  const adjacency = Array.from({ length: oxygen.length }, () => []);
  graphEdges.forEach(([first, second], edge) => {
    adjacency[first].push({ other: second, edge });
    adjacency[second].push({ other: first, edge });
  });
  if (adjacency.some((shell) => shell.length !== 4)) throw new Error("ice oxygen graph is not tetrahedral");
  const unused = new Set(graphEdges.map((_, edge) => edge));
  const oriented = [];
  while (unused.size) {
    const startEdge = Math.min(...unused);
    const stack = [graphEdges[startEdge][0]];
    const circuit = [];
    while (stack.length) {
      const current = stack[stack.length - 1];
      const options = adjacency[current].filter(({ edge }) => unused.has(edge))
        .sort((first, second) => first.other - second.other || first.edge - second.edge);
      if (options.length) {
        unused.delete(options[0].edge);
        stack.push(options[0].other);
      } else circuit.push(stack.pop());
    }
    const path = circuit.reverse();
    for (let index = 0; index + 1 < path.length; index++) oriented.push([path[index], path[index + 1]]);
  }
  const outgoing = Array.from({ length: oxygen.length }, () => []);
  oriented.forEach(([donor, acceptor]) => outgoing[donor].push(acceptor));
  if (outgoing.some((shell) => shell.length !== 2)) throw new Error("balanced ice orientation must donate twice per oxygen");
  const records = oxygen.map((atom, index) => ({ pA: atom.pA.clone(), species: "O", family: `ice-${polytype}`, molecule: index, q: atom.address.slice(0, 3) }));
  oxygen.forEach((atom, index) => {
    const byNeighbor = new Map(neighbors[index].map((neighbor) => [neighbor.other, neighbor]));
    outgoing[index].slice().sort((first, second) => first - second).forEach((other) => {
      const neighbor = byNeighbor.get(other);
      records.push({ pA: atom.pA.clone().add(neighbor.vector.clone().setLength(.9572)), species: "H", family: `ice-${polytype}`, molecule: index, q: atom.address.slice(0, 3) });
    });
  });
  const center = records.reduce((sum, atom) => sum.add(atom.pA), new THREE.Vector3()).multiplyScalar(1 / records.length);
  const scale = .92 / .9572;
  return records.map((atom, sourceIndex) => ({ ...atom, p: atom.pA.clone().sub(center).multiplyScalar(scale), sourceIndex }))
    .sort((first, second) => first.p.lengthSq() - second.p.lengthSq() || first.species.localeCompare(second.species));
}

function makeDryIceReferenceConfiguration() {
  // Low-pressure CO2-I: carbon atoms occupy an fcc array and the linear
  // molecules follow the four body-diagonal orientations of Pa-3. The saved
  // 80 K lattice constant is 5.578 A; the intramolecular C--O distance uses
  // the 1.168 A diffraction value reported for phase I under compression.
  const latticeA = 5.578;
  const bondA = 1.168;
  const repeats = 3;
  const lengthA = latticeA * repeats;
  const basis = [
    { fractional: [0, 0, 0], axis: [1, 1, 1] },
    { fractional: [0, .5, .5], axis: [1, -1, -1] },
    { fractional: [.5, 0, .5], axis: [-1, 1, -1] },
    { fractional: [.5, .5, 0], axis: [-1, -1, 1] },
  ];
  const wrap = (value) => ((value % lengthA) + lengthA) % lengthA;
  const records = [];
  for (let ix = 0; ix < repeats; ix++) for (let iy = 0; iy < repeats; iy++) for (let iz = 0; iz < repeats; iz++) {
    basis.forEach(({ fractional, axis }, basisIndex) => {
      const carbon = new THREE.Vector3(
        (ix + fractional[0]) * latticeA,
        (iy + fractional[1]) * latticeA,
        (iz + fractional[2]) * latticeA,
      );
      const direction = new THREE.Vector3(...axis).normalize().multiplyScalar(bondA);
      const molecule = records.length / 3;
      records.push({ pA: carbon, species: "C", family: "dry-ice-pa3", molecule, q: [ix, iy, iz, basisIndex] });
      [-1, 1].forEach((sign) => {
        const oxygen = carbon.clone().addScaledVector(direction, sign);
        oxygen.set(wrap(oxygen.x), wrap(oxygen.y), wrap(oxygen.z));
        records.push({ pA: oxygen, species: "O", family: "dry-ice-pa3", molecule, q: [ix, iy, iz, basisIndex] });
      });
    });
  }
  const center = new THREE.Vector3(lengthA / 2, lengthA / 2, lengthA / 2);
  const scale = .92 / bondA;
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

function makeMetallicGlassReference() {
  const material = MATERIALS.random;
  const packing = generateAmorphousMixture({
    count: DEFAULT_REFERENCE_COUNT,
    copperFraction: .64,
    targetNearestAngstrom: material.spacingA,
  });
  const scale = .92 / material.spacingA;
  return packing.positions.map((position, sourceIndex) => {
    const pA = new THREE.Vector3(...position);
    return {
      pA,
      p: pA.clone().multiplyScalar(scale),
      species: packing.species[sourceIndex],
      family: "glass",
      sourceIndex,
      glassCellLengthA: packing.cellLengthAngstrom,
      glassAudit: packing.audit,
    };
  }).sort((first, second) => first.p.lengthSq() - second.p.lengthSq()
    || first.species.localeCompare(second.species));
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
  if (MATERIALS[scenario]?.molecularFixture === "dry-ice-pa3") return makeDryIceReferenceConfiguration();
  if (MATERIALS[scenario]?.intrinsicDimension === 2) return makePlanarReferenceConfiguration(scenario);
  if (scenario === "random") return makeMetallicGlassReference();
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
  if (scenarioSelect.value === "random" && referenceAtoms[0]?.glassCellLengthA) {
    const length = referenceAtoms[0].glassCellLengthA;
    return [new THREE.Vector3(length, 0, 0), new THREE.Vector3(0, length, 0), new THREE.Vector3(0, 0, length)];
  }
  if (currentMaterial().icePolytype) {
    const definition = iceDefinition(currentMaterial().icePolytype);
    return definition.primitive.map((vector, axis) => vector.clone().multiplyScalar(definition.repeats[axis]));
  }
  if (currentMaterial().referenceCellA) {
    const length = currentMaterial().referenceCellA;
    return [new THREE.Vector3(length, 0, 0), new THREE.Vector3(0, length, 0), new THREE.Vector3(0, 0, length)];
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
  if (scenarioSelect.value === "imported" && importedStructure) return importedStructure.pbc;
  return currentMaterial().periodicWindow ? [true, true, true] : [false, false, false];
}

function getOrderPrototypeLibrary() {
  if (orderPrototypeLibrary) return orderPrototypeLibrary;
  orderPrototypeLibrary = Object.entries(MATERIALS).map(([id, material]) => {
    const source = makeReferenceConfiguration(id);
    const spacing = medianNearestSpacing(source);
    return { id, material, stats: calculateStructuralStats(source, spacing, false, material.intrinsicDimension === 2 ? 2 : 3) };
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
  if (pipelineStage !== 4 || !detectedUnitCell || iceAnchorTrace) return;
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
  const vectors = centeredPeriodicSupport(referenceAtoms, placement.support);
  return directionalPoseDescriptor(placement.support.map((index, site) => ({
    species: referenceAtoms[index].species,
    vector: vectors[site],
    r: vectors[site].length() / referenceSpacingA,
  })));
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
    const poseByCenter = new Map();
    const poseByOccurrence = new Map();
    placements.forEach((placement, occurrenceIndex) => {
      const descriptor = supportOrientationDescriptor(placement);
      let pose = representatives.findIndex((candidate) => orientationDistance(candidate, descriptor) <= .16);
      if (pose < 0) { pose = representatives.length; representatives.push(descriptor); populations.push(0); }
      populations[pose]++;
      poseByCenter.set(placement.center, pose);
      poseByOccurrence.set(placement.coverIndex ?? occurrenceIndex, pose);
    });
    return { cluster: clusterIndex, element: cluster.element, occurrences: placements.length,
      orientations: representatives.length, populations: populations.slice().sort((first, second) => second - first),
      poseByCenter, poseByOccurrence };
  });
  return learnedClusters.clusters.map((cluster, clusterIndex) => {
    const occurrences = learnedClusters.labels.map((label, index) => label === clusterIndex ? index : -1)
      .filter((index) => index >= 0);
    const representatives = [];
    const populations = [];
    const poseByCenter = new Map();
    occurrences.forEach((index) => {
      const descriptor = orientationDescriptor(learnedClusters.environments[index]);
      let pose = representatives.findIndex((candidate) => orientationDistance(candidate, descriptor) <= .16);
      if (pose < 0) {
        pose = representatives.length;
        representatives.push(descriptor);
        populations.push(0);
      }
      populations[pose]++;
      poseByCenter.set(index, pose);
    });
    return {
      cluster: clusterIndex,
      element: cluster.element,
      occurrences: occurrences.length,
      orientations: representatives.length,
      populations: populations.slice().sort((first, second) => second - first),
      poseByCenter,
    };
  });
}

function poseAtlasEntryStatus(entry) {
  const sampledFraction = entry.orientations / Math.max(1, entry.occurrences);
  const everyPoseRepeated = entry.populations.length > 0
    && entry.populations.every((population) => population >= 2);
  if (entry.occurrences >= 12 && sampledFraction >= .8) return "sampled continuum";
  if (everyPoseRepeated) return "finite required set";
  return "unresolved support";
}

function rotationGroupLabel() {
  return currentMaterial().intrinsicDimension === 2 ? "SO(2)" : "SO(3)";
}

function poseSupportLabel(total, freeTypes, unresolvedTypes) {
  if (!freeTypes && !unresolvedTypes) return `${total} finite pose orbit${total === 1 ? "" : "s"}`;
  return [
    `${total} observed`,
    freeTypes ? `${freeTypes} equivariant ${rotationGroupLabel()}` : "",
    unresolvedTypes ? `${unresolvedTypes} unresolved` : "",
  ].filter(Boolean).join(" · ");
}

function resolvedGeometryMode() {
  if (geometryMode !== "auto") return geometryMode;
  if (detectedUnitCell) return "lattice";
  if (currentMaterial().periodicWindow && currentPbc().some(Boolean) && currentMaterial().order !== "amorphous") return "lattice";
  if (currentMaterial().intrinsicDimension === 2) {
    const angles = new Set((currentMaterial().planarLayers || []).map((layer) => Math.round((layer.angle || 0) * 1e6)));
    return angles.size > 1 ? "module" : "lattice";
  }
  return "offlattice";
}

function resolvedGeometryLabel() {
  return { lattice: "lattice", module: "finite-rank module", offlattice: "metric point set" }[resolvedGeometryMode()];
}

function automaticMarkingChannels() {
  return Math.max(3, ...orientationAtlas.map((entry) => recommendedChannelsForCluster(entry.cluster, entry.orientations)));
}

function clusterPortRank(cluster) {
  if (!overlapGrammar) return 1;
  return Math.max(1, new Set(observedPortRules(cluster).map(portRoleKey)).size);
}

function observedPortRules(cluster) {
  const rules = overlapGrammar?.rules.filter((rule) => rule.from === cluster) || [];
  if (!overlapGrammar?.molecular) return rules;
  const observed = [];
  overlapGrammar.reconstructionByOccurrence.forEach((rows) => rows.forEach((rule) => {
    if (rule.from === cluster) observed.push(rule);
  }));
  return [...rules, ...observed];
}

function portRoleKey(rule) {
  const separation = Math.round(rule.translation?.length?.() || 0);
  const rotation = Math.round((rule.rotationAngle || 0) / (Math.PI / 6));
  return `${rule.to}:${Math.round((rule.meanShared || 0) * 2)}:${separation}:${rotation}`;
}

function numericMatrixRank(matrix, tolerance = 1e-8) {
  if (!matrix.length || !matrix[0]?.length) return 0;
  const work = matrix.map((row) => row.slice());
  let rank = 0;
  for (let column = 0; column < work[0].length && rank < work.length; column++) {
    let pivot = rank;
    for (let row = rank + 1; row < work.length; row++) {
      if (Math.abs(work[row][column]) > Math.abs(work[pivot][column])) pivot = row;
    }
    if (Math.abs(work[pivot][column]) <= tolerance) continue;
    [work[rank], work[pivot]] = [work[pivot], work[rank]];
    const divisor = work[rank][column];
    for (let entry = column; entry < work[rank].length; entry++) work[rank][entry] /= divisor;
    for (let row = 0; row < work.length; row++) {
      if (row === rank || Math.abs(work[row][column]) <= tolerance) continue;
      const factor = work[row][column];
      for (let entry = column; entry < work[row].length; entry++) work[row][entry] -= factor * work[rank][entry];
    }
    rank++;
  }
  return rank;
}

function clusterPosePortRank(cluster) {
  const atlas = orientationAtlas.find((entry) => entry.cluster === cluster);
  const rules = observedPortRules(cluster);
  if (!atlas?.orientations || !rules.length) return 1;
  const roles = [...new Set(rules.map(portRoleKey))].sort();
  const roleIndex = new Map(roles.map((role, index) => [role, index]));
  const matrix = Array.from({ length: atlas.orientations }, () => new Array(roles.length).fill(0));
  rules.forEach((rule) => {
    const sources = rule.examples?.map((example) => example[0])
      || [Number.isInteger(rule.occurrenceFrom) ? rule.occurrenceFrom : rule.representativePair?.[0]];
    sources.forEach((source) => {
      const pose = overlapGrammar?.coverBased
        ? atlas.poseByOccurrence?.get(source)
        : atlas.poseByCenter?.get(source);
      if (pose !== undefined) matrix[pose][roleIndex.get(portRoleKey(rule))]++;
    });
  });
  return Math.max(1, numericMatrixRank(matrix));
}

function recommendedChannelsForCluster(cluster) {
  // Two scalar fields retain compatibility and failure evidence. The remaining
  // fields span only the observed coupling between proper pose orbits and
  // outgoing connection roles, rather than one-hot encoding raw rotations.
  return Math.min(12, Math.max(3, 2 + clusterPosePortRank(cluster)));
}

function centeredPeriodicSupport(source, support) {
  if (!support.length) return [];
  const anchor = source[support[0]];
  const vectors = support.map((atomIndex) => periodicDisplacement(anchor, source[atomIndex]));
  const centroid = vectors.reduce((sum, vector) => sum.add(vector), new THREE.Vector3())
    .multiplyScalar(1 / vectors.length);
  return vectors.map((vector) => vector.clone().sub(centroid));
}

function unwrappedRingSupport(source, waters, ring) {
  if (!ring.length) return [];
  const vectors = [new THREE.Vector3()];
  for (let index = 1; index < ring.length; index++) {
    const previous = source[waters[ring[index - 1]].center];
    const current = source[waters[ring[index]].center];
    vectors.push(vectors[index - 1].clone().add(periodicDisplacement(previous, current)));
  }
  const centroid = vectors.reduce((sum, vector) => sum.add(vector), new THREE.Vector3())
    .multiplyScalar(1 / vectors.length);
  return vectors.map((vector) => vector.clone().sub(centroid));
}

function coloredPeriodicSupportSignature(source, support) {
  // This is the same colored complete-metric invariant used by the headless
  // ice audit.  It is independent of translation, atom order, and any proper
  // or improper rigid isometry; raw atom IDs and the global cell frame never
  // enter the class label.
  const species = support.map((atomIndex) => source[atomIndex].species).sort();
  const pairs = [];
  support.forEach((first, firstIndex) => support.slice(firstIndex + 1).forEach((second) => {
    const colors = [source[first].species, source[second].species].sort().join("");
    pairs.push(`${colors}:${periodicDisplacement(source[first], source[second]).length().toFixed(2)}`);
  }));
  return `${species.join("")}|${pairs.sort().join("|")}`;
}

function molecularIsometryGallery(source, families, familyTypes) {
  const gallery = [];
  families.forEach((placements, familyType) => {
    const classes = new Map();
    placements.forEach((placement) => {
      const signature = coloredPeriodicSupportSignature(source, placement.support);
      const members = classes.get(signature) || [];
      members.push(placement);
      classes.set(signature, members);
    });
    [...classes.entries()].sort(([first], [second]) => first.localeCompare(second))
      .forEach(([signature, members], classIndex) => {
        const representative = members[0];
        const family = familyTypes[familyType];
        const customSupport = familyType === 2
          ? representative.ring.map((waterIndex) => families[0][waterIndex].center)
          : representative.support;
        const customVectors = familyType === 2
          ? unwrappedRingSupport(source, families[0], representative.ring)
          : centeredPeriodicSupport(source, customSupport);
        gallery.push({
          ...family,
          familyType,
          classIndex,
          classCount: classes.size,
          classSignature: signature,
          classPlacementIndices: members.map((placement) => placement.coverIndex),
          medoid: representative.center,
          count: members.length,
          customSupport,
          customVectors,
          label: `${family.shortLabel} · I${classIndex + 1}`,
        });
      });
  });
  return gallery;
}

function molecularComponentHypothesis(source) {
  return discoverFiniteMolecularComponents({
    species: source.map((atom) => atom.species),
    distance: (first, second) => periodicDisplacement(source[first], source[second]).length(),
  });
}

function discoveredWaterComponents(discovery) {
  if (!discovery.accepted || discovery.types.length !== 1) return null;
  const formula = discovery.types[0].formula;
  const waterFormula = formula.length === 2
    && formula[0][0] === "H" && formula[0][1] === 2
    && formula[1][0] === "O" && formula[1][1] === 1;
  if (!waterFormula || discovery.components.some((component) => component.length !== 3)) return null;
  return discovery;
}

function molecularDiscoverySummary(discovery, route) {
  return {
    accepted: discovery.accepted,
    reason: discovery.reason,
    route,
    covalentEdges: discovery.covalentEdges,
    components: discovery.componentCount,
    largestComponent: discovery.largestComponent,
    componentTypes: discovery.typeCount,
    formulas: discovery.types.map((type) => ({ formula: type.formula, occurrences: type.occurrences.length })),
    unsupportedElements: discovery.unsupported,
    materialLabelUsed: discovery.materialLabelUsed,
    expectedFormulaUsed: discovery.expectedFormulaUsed,
  };
}

function buildWaterClusterCover(source, molecularDiscovery) {
  const oxygen = source.map((atom, index) => atom.species === "O" ? index : -1).filter((index) => index >= 0);
  const waters = [];
  const owner = new Map();
  molecularDiscovery.components.forEach((component) => {
    const oxygenIndex = component.find((index) => source[index].species === "O");
    const bonded = component.filter((index) => source[index].species === "H")
      .sort((first, second) => first - second);
    if (!Number.isInteger(oxygenIndex) || bonded.length !== 2) return;
    const waterIndex = waters.length;
    const support = [oxygenIndex, ...bonded];
    waters.push({ center: oxygenIndex, support, type: 0, residual: false, kind: "H₂O molecule", family: "molecule" });
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
    type: 1, residual: false, kind: "H₂O···H₂O bridge", waterPair: [first, second], family: "bridge",
  }));

  const adjacency = Array.from({ length: waters.length }, () => new Set());
  bridges.forEach(({ waterPair: [first, second] }) => { adjacency[first].add(second); adjacency[second].add(first); });
  const ringPaths = new Map();
  adjacency.forEach((_, start) => {
    const stack = [[start, [start]]];
    while (stack.length) {
      const [current, path] = stack.pop();
      if (path.length === 6) {
        if (adjacency[current].has(start)) {
          const key = path.slice().sort((a, b) => a - b).join(":");
          if (!ringPaths.has(key)) ringPaths.set(key, path.slice());
        }
        continue;
      }
      adjacency[current].forEach((neighbor) => {
        if (neighbor <= start || path.includes(neighbor)) return;
        stack.push([neighbor, [...path, neighbor]]);
      });
    }
  });
  const gaps = [...ringPaths.values()].map((ring) => ({
    center: waters[ring[0]].center,
    support: [...new Set(ring.flatMap((waterIndex) => waters[waterIndex].support))],
    type: 2, residual: false, gap: true, kind: "oxygen-ring gap boundary", family: "gap",
    ring: ring.slice(),
  }));
  const placements = [...waters, ...bridges, ...gaps];
  placements.forEach((placement, coverIndex) => { placement.coverIndex = coverIndex; });
  const coveredAtoms = new Set(waters.flatMap((placement) => placement.support));
  const waterSupport = waters[0]?.support || [];
  const bridgeSupport = bridges[0]?.support || [];
  const ringSupport = gaps[0]?.ring?.map((waterIndex) => waters[waterIndex].center) || [];
  const types = [
    { type: 0, familyType: 0, medoid: waters[0]?.center || 0, element: "H₂O", shortLabel: "H₂O", label: "H₂O molecule", geometry: "bent molecular face",
      count: waters.length, visualKind: "molecule", customSupport: waterSupport,
      customVectors: centeredPeriodicSupport(source, waterSupport) },
    { type: 1, familyType: 1, medoid: bridges[0]?.center || 0, element: "2 H₂O", shortLabel: "bridge", label: "hydrogen-bond bridge", geometry: "connection polyhedron",
      count: bridges.length, visualKind: "bridge", customSupport: bridgeSupport,
      customVectors: centeredPeriodicSupport(source, bridgeSupport) },
    { type: 2, familyType: 2, medoid: gaps[0]?.center || 0, element: "O₆ void", shortLabel: "O₆ gap", label: "six-water ring void", geometry: "void-boundary polyhedron",
      count: gaps.length, visualKind: "ring", gap: true,
      customSupport: ringSupport,
      customVectors: unwrappedRingSupport(source, waters, gaps[0]?.ring || []) },
  ].filter((type) => type.customSupport.length);
  const galleryTypes = molecularIsometryGallery(source, [waters, bridges, gaps], types);
  const incidence = source.map((_, atomIndex) => placements.map((placement, placementIndex) => placement.support.includes(atomIndex) ? placementIndex : -1).filter((index) => index >= 0));
  return { placements, residualTypes: [], types, galleryTypes, incidence, covered: coveredAtoms.size,
    complete: coveredAtoms.size === source.length, periodic: true,
    molecularDiscovery: molecularDiscoverySummary(molecularDiscovery, "molecular connection / void cover"),
    molecular: { water: true, molecules: waters.length, connections: bridges.length, voids: gaps.length,
      moleculeClasses: galleryTypes.filter((type) => type.familyType === 0).length,
      connectionClasses: galleryTypes.filter((type) => type.familyType === 1).length,
      voidClasses: galleryTypes.filter((type) => type.familyType === 2).length,
      waters: waters.length, bridges: bridges.length, gaps: gaps.length,
      waterClasses: galleryTypes.filter((type) => type.familyType === 0).length,
      bridgeClasses: galleryTypes.filter((type) => type.familyType === 1).length,
      gapClasses: galleryTypes.filter((type) => type.familyType === 2).length } };
}

function molecularFormulaLabel(source, support) {
  const counts = new Map();
  support.forEach((index) => counts.set(source[index].species, (counts.get(source[index].species) || 0) + 1));
  return [...counts.entries()].sort(([first], [second]) => first.localeCompare(second))
    .map(([element, count]) => `${element}${count === 1 ? "" : count}`).join("");
}

function molecularComponentAnchor(source, support) {
  const populations = new Map();
  support.forEach((index) => populations.set(source[index].species, (populations.get(source[index].species) || 0) + 1));
  return support.map((index) => ({
    index,
    key: [
      String(populations.get(source[index].species)).padStart(3, "0"),
      source[index].species,
      ...support.filter((other) => other !== index).map((other) =>
        `${source[other].species}:${periodicDisplacement(source[index], source[other]).length().toFixed(3)}`).sort(),
    ].join("|"),
  })).sort((first, second) => first.key.localeCompare(second.key) || first.index - second.index)[0].index;
}

function genericMolecularDisplayEdges(source, support, discovery, connectedComponents = null) {
  const local = new Map(support.map((atomIndex, index) => [atomIndex, index]));
  const edges = discovery.edges.filter(([first, second]) => local.has(first) && local.has(second))
    .map(([first, second]) => [local.get(first), local.get(second), "bond"]);
  if (connectedComponents?.length === 2) {
    let contact = null;
    discovery.components[connectedComponents[0]].forEach((first) => discovery.components[connectedComponents[1]].forEach((second) => {
      const separation = periodicDisplacement(source[first], source[second]).length();
      if (!contact || separation < contact.separation) contact = { first, second, separation };
    }));
    if (contact) edges.push([local.get(contact.first), local.get(contact.second), "hydrogen"]);
  }
  return edges;
}

function unwrappedMolecularCycle(source, discovery, cycle) {
  const anchors = cycle.map((component) => molecularComponentAnchor(source, discovery.components[component]));
  if (!anchors.length) return [];
  const vectors = [new THREE.Vector3()];
  for (let index = 1; index < anchors.length; index++) {
    vectors.push(vectors[index - 1].clone().add(periodicDisplacement(source[anchors[index - 1]], source[anchors[index]])));
  }
  const centroid = vectors.reduce((sum, vector) => sum.add(vector), new THREE.Vector3()).multiplyScalar(1 / vectors.length);
  return vectors.map((vector) => vector.clone().sub(centroid));
}

function buildGenericMolecularClusterCover(source, molecularDiscovery) {
  const topology = discoverMolecularConnectionTopology({
    discovery: molecularDiscovery,
    species: source.map((atom) => atom.species),
    distance: (first, second) => periodicDisplacement(source[first], source[second]).length(),
  });
  if (!topology.componentGraphConnected) return null;
  const moleculeTypes = molecularDiscovery.types.length;
  const connectionOffset = moleculeTypes;
  const voidOffset = moleculeTypes + topology.connectionTypeCount;
  const moleculePlacements = molecularDiscovery.components.map((support, component) => {
    const type = molecularDiscovery.types.find((candidate) => candidate.occurrences.some((members) => members.join(":") === support.join(":"))).type;
    return { center: molecularComponentAnchor(source, support), support: support.slice(), type,
      residual: false, kind: "finite molecular component", component, family: "molecule" };
  });
  const connectionPlacements = topology.connections.map((connection) => ({
    center: molecularComponentAnchor(source, molecularDiscovery.components[connection.components[0]]),
    support: connection.members.slice(), type: connectionOffset + connection.type,
    residual: false, kind: "molecule-pair connection", components: connection.components.slice(), family: "bridge",
  }));
  const voidPlacements = topology.voids.map((boundary) => ({
    center: molecularComponentAnchor(source, molecularDiscovery.components[boundary.components[0]]),
    support: boundary.members.slice(), type: voidOffset + boundary.type,
    residual: false, gap: true, kind: "molecular void boundary", components: boundary.components.slice(), family: "gap",
  }));
  const placements = [...moleculePlacements, ...connectionPlacements, ...voidPlacements];
  placements.forEach((placement, coverIndex) => { placement.coverIndex = coverIndex; });
  const types = [];
  for (let type = 0; type < voidOffset + topology.voidTypeCount; type++) {
    const members = placements.filter((placement) => placement.type === type);
    const representative = members[0];
    if (!representative) continue;
    const molecule = type < connectionOffset;
    const connection = type >= connectionOffset && type < voidOffset;
    const visualSupport = representative.gap
      ? representative.components.map((component) => molecularComponentAnchor(source, molecularDiscovery.components[component]))
      : representative.support;
    const formula = molecule ? molecularFormulaLabel(source, representative.support)
      : connection ? representative.components.map((component) => molecularFormulaLabel(source, molecularDiscovery.components[component])).join(" + ")
        : `${representative.components.length}-molecule void`;
    types.push({
      type,
      medoid: representative.center,
      element: formula,
      shortLabel: molecule ? formula : connection ? "connection" : "void",
      label: `${molecule ? formula : connection ? "molecular connection" : "molecular void"} · I${(molecule ? type : connection ? type - connectionOffset : type - voidOffset) + 1}`,
      geometry: molecule ? "finite molecular polyhedron" : connection ? "molecule-pair connection polyhedron" : "void-boundary polygon",
      count: members.length,
      visualKind: molecule ? "molecule" : connection ? "bridge" : "ring",
      gap: !molecule && !connection,
      customSupport: visualSupport,
      customVectors: representative.gap
        ? unwrappedMolecularCycle(source, molecularDiscovery, representative.components)
        : centeredPeriodicSupport(source, visualSupport),
      displayEdges: molecule || connection
        ? genericMolecularDisplayEdges(source, representative.support, molecularDiscovery, representative.components)
        : null,
      classSignature: molecule ? molecularDiscovery.types[type].signature
        : connection ? topology.connections.find((record) => record.type === type - connectionOffset).signature
          : topology.voids.find((record) => record.type === type - voidOffset).signature,
      classPlacementIndices: members.map((placement) => placement.coverIndex),
      classIndex: molecule ? type : connection ? type - connectionOffset : type - voidOffset,
      classCount: molecule ? moleculeTypes : connection ? topology.connectionTypeCount : topology.voidTypeCount,
    });
  }
  const coveredAtoms = new Set(moleculePlacements.flatMap((placement) => placement.support));
  const incidence = source.map((_, atomIndex) => placements.map((placement, placementIndex) =>
    placement.support.includes(atomIndex) ? placementIndex : -1).filter((index) => index >= 0));
  return {
    placements, residualTypes: [], types, galleryTypes: types, incidence,
    covered: coveredAtoms.size, complete: coveredAtoms.size === source.length,
    periodic: currentPbc().some(Boolean),
    molecularDiscovery: molecularDiscoverySummary(molecularDiscovery, "generic molecular connection / void cover"),
    molecular: {
      water: false,
      molecules: moleculePlacements.length,
      connections: connectionPlacements.length,
      voids: voidPlacements.length,
      moleculeClasses: moleculeTypes,
      connectionClasses: topology.connectionTypeCount,
      voidClasses: topology.voidTypeCount,
      componentGraphConnected: topology.componentGraphConnected,
      expectedRingSizeUsed: topology.expectedRingSizeUsed,
    },
  };
}

function buildIrregularClusterCover(source, molecularDiscovery) {
  const result = discoverIrregularCover({
    species: source.map((atom) => atom.species),
    distance: (first, second) => periodicDisplacement(source[first], source[second]).length(),
    orientedVolume: (first, second, third, fourth) => periodicDisplacement(source[first], source[second])
      .dot(new THREE.Vector3().crossVectors(
        periodicDisplacement(source[first], source[third]),
        periodicDisplacement(source[first], source[fourth]),
      )),
    referenceSpacing: referenceSpacingA,
    shellRadius: motifShellCutoff(),
  });
  const types = result.types.map((type) => ({
    type: type.type,
    medoid: type.anchor,
    element: type.formula,
    label: type.residual ? `gap G${type.type + 1}` : `C${type.type + 1}`,
    geometry: type.geometry,
    count: type.occurrenceCount,
    candidateCount: type.observedCandidateCount,
    residual: type.residual,
    gap: type.residual,
    visualKind: type.residual ? "irregular-gap" : "irregular",
    customSupport: type.support.slice(),
    customVectors: centeredPeriodicSupport(source, type.support),
    classSignature: type.signature,
    chirality: type.chirality,
    seedKinds: type.kinds,
  }));
  const placements = result.placements.map((placement, coverIndex) => ({ ...placement, coverIndex }));
  const coveredAtoms = new Set(placements.flatMap((placement) => placement.support));
  const incidence = source.map((_, atomIndex) => placements
    .map((placement, placementIndex) => placement.support.includes(atomIndex) ? placementIndex : -1)
    .filter((placementIndex) => placementIndex >= 0));
  return {
    placements,
    residualTypes: types.filter((type) => type.residual),
    types,
    galleryTypes: types,
    incidence,
    covered: coveredAtoms.size,
    complete: result.complete && coveredAtoms.size === source.length,
    periodic: currentPbc().some(Boolean),
    occurrenceBased: true,
    molecularDiscovery: molecularDiscoverySummary(molecularDiscovery, "irregular support fallback"),
    irregular: {
      recurringCoordinationClasses: result.recurringCoordinationClasses,
      recurringCenterFreeClasses: result.recurringCenterFreeClasses,
      selectedCenterFreeOccurrences: result.selectedCenterFreeOccurrences,
      residualAtoms: result.residualAtoms,
      replayConnectorCount: result.replayConnectorCount,
      disconnectedReplayComponents: result.disconnectedReplayComponents,
      replaySeedPlacementIndex: result.replaySeedPlacementIndex,
      minimumOccurrences: result.minimumOccurrences,
      metricToleranceFraction: result.metricToleranceFraction,
    },
  };
}

// Discover exact recurring colored metric supports. Atom-centred coordination
// polyhedra are only one candidate family; centre-free bond-lens supports can
// enter the same cover, and any uncovered connected region becomes an explicit
// residual cluster rather than disappearing from the model.
function buildExhaustiveClusterCover(source) {
  const molecularDiscovery = molecularComponentHypothesis(source);
  const waterDiscovery = discoveredWaterComponents(molecularDiscovery);
  if (waterDiscovery) return buildWaterClusterCover(source, waterDiscovery);
  if (molecularDiscovery.accepted) {
    const molecularCover = buildGenericMolecularClusterCover(source, molecularDiscovery);
    if (molecularCover) return molecularCover;
  }
  return buildIrregularClusterCover(source, molecularDiscovery);
}

function clusterGalleryTypes() {
  if (!learnedClusters || !learnedCover) return [];
  if (learnedCover.galleryTypes) return learnedCover.galleryTypes;
  if (learnedCover.types) return learnedCover.types;
  return [
    ...learnedClusters.clusters.map((cluster, type) => ({ ...cluster, type, residual: false })),
    ...learnedCover.residualTypes.map((cluster, offset) => ({ ...cluster, type: learnedClusters.clusters.length + offset })),
  ];
}

function galleryPoseCount(cluster) {
  const placements = cluster.classPlacementIndices
    ? cluster.classPlacementIndices.map((index) => learnedCover.placements[index]).filter(Boolean)
    : learnedCover.placements.filter((placement) => placement.type === cluster.type);
  const representatives = [];
  placements.forEach((placement) => {
    const descriptor = supportOrientationDescriptor(placement);
    if (!representatives.some((candidate) => orientationDistance(candidate, descriptor) <= .16)) representatives.push(descriptor);
  });
  return representatives.length;
}

function clusterGalleryFamily(cluster) {
  if (cluster.residual) return "residual";
  if (cluster.visualKind === "molecule") return "molecule";
  if (cluster.visualKind === "bridge") return "bridge";
  if (cluster.visualKind === "ring" || cluster.gap) return "gap";
  return "support";
}

function clusterCoverRole(cluster) {
  return {
    molecule: "molecular atom cover",
    bridge: "connection polyhedron",
    gap: "void / gap boundary",
    residual: "explicit residual terminal",
    support: "recurring colored support",
  }[clusterGalleryFamily(cluster)];
}

function molecularCoverIcon(family) {
  if (family === "molecule") return `<svg viewBox="0 0 54 34" aria-hidden="true">
    <path d="M27 18 10 7M27 18 44 7"/><circle cx="27" cy="18" r="5"/><circle cx="10" cy="7" r="3"/><circle cx="44" cy="7" r="3"/>
  </svg>`;
  if (family === "bridge") return `<svg viewBox="0 0 54 34" aria-hidden="true">
    <path d="m7 8 13-5 1 14-14-9Zm26 9 1-14 13 5-14 9ZM7 8l26 9M20 3l14 0M21 17l26-9"/><path class="dash" d="M20 3 33 17"/>
  </svg>`;
  return `<svg viewBox="0 0 54 34" aria-hidden="true">
    <path d="m13 17 7-12h14l7 12-7 12H20L13 17Z"/><circle cx="13" cy="17" r="2"/><circle cx="20" cy="5" r="2"/><circle cx="34" cy="5" r="2"/><circle cx="41" cy="17" r="2"/><circle cx="34" cy="29" r="2"/><circle cx="20" cy="29" r="2"/>
  </svg>`;
}

function buildMolecularCoverLedger(types) {
  if (!learnedCover.molecular) return null;
  const molecular = learnedCover.molecular;
  const ledger = document.createElement("div");
  ledger.className = "cluster-cover-ledger";
  ledger.setAttribute("aria-label", "Molecular ice cover accounting");
  const layers = [
    { family: "molecule", eyebrow: "atomic cover", title: molecular.water ? `${molecular.waters} H₂O` : `${molecular.molecules} molecules`,
      detail: `${learnedCover.covered} / ${referenceCount()} atoms · ${molecular.moleculeClasses} isometry class${molecular.moleculeClasses === 1 ? "" : "es"}` },
    { family: "bridge", eyebrow: "connection cover", title: `${molecular.connections} connections`,
      detail: `${molecular.connectionClasses} metric-isometry classes · attachment geometry` },
    { family: "gap", eyebrow: "void-boundary cover", title: `${molecular.voids} ${molecular.water ? "O₆ boundaries" : "void boundaries"}`,
      detail: `${molecular.voidClasses} ${molecular.water ? "decorated" : "graph-derived"} classes · empty-region geometry` },
  ];
  layers.forEach((layer) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.clusterLedgerFilter = layer.family;
    button.setAttribute("aria-label", `Show ${layer.eyebrow}: ${layer.title}`);
    button.innerHTML = `${molecularCoverIcon(layer.family)}<span><small>${layer.eyebrow}</small><strong>${layer.title}</strong><em>${layer.detail}</em></span>`;
    button.addEventListener("click", () => {
      const filter = clusterGallery.querySelector(`[data-cluster-family-filter="${layer.family}"]`);
      filter?.click();
    });
    ledger.append(button);
  });
  const explanation = document.createElement("p");
  explanation.textContent = `${molecular.water ? "H₂O" : "Finite molecules"} close the atom cover; connection and void clusters encode intermolecular geometry without inventing radial spokes.`;
  ledger.append(explanation);
  return ledger;
}

function clusterPlacementIndices(cluster) {
  if (cluster.classPlacementIndices?.length) return cluster.classPlacementIndices.slice();
  return learnedCover.placements.map((placement, index) => placement.type === cluster.type ? index : -1)
    .filter((index) => index >= 0);
}

function updateClusterGalleryInspector(galleryIndex) {
  const types = clusterGalleryTypes();
  const cluster = types[galleryIndex];
  const inspector = clusterGallery.querySelector(".cluster-gallery-inspector");
  if (!cluster || !inspector) return;
  selectedGalleryCluster = galleryIndex;
  clusterGallery.querySelectorAll(".cluster-card").forEach((card) => {
    const active = Number(card.dataset.clusterIndex) === galleryIndex;
    card.classList.toggle("active", active);
    card.setAttribute("aria-pressed", String(active));
  });
  const placementIndices = clusterPlacementIndices(cluster);
  const coveredAtoms = new Set(placementIndices.flatMap((index) => learnedCover.placements[index]?.support || []));
  const sharedAtoms = [...coveredAtoms].filter((atomIndex) => learnedCover.incidence[atomIndex]?.length > 1).length;
  const supportSites = cluster.customSupport?.length
    || learnedCover.placements[placementIndices[0]]?.support.length || 1;
  const poseCount = galleryPoseCount(cluster);
  const familyIndex = cluster.familyType ?? galleryIndex;
  const ports = cluster.residual ? 0 : clusterPortRank(familyIndex);
  const channels = cluster.residual ? 0 : recommendedChannelsForCluster(familyIndex);
  const chirality = cluster.chirality || "unresolved / achiral";
  const coverKind = cluster.residual ? "literal terminal · never promoted" : "recurrent candidate · eligible for ports";
  const displayTopology = clusterDisplayTopology(cluster, clusterGallerySites(cluster));
  const surfaceLabel = cluster.visualKind === "ring"
    ? `${displayTopology.faces.length} boundary polygon${displayTopology.faces.length === 1 ? "" : "s"}`
    : `${displayTopology.faces.length} explicit face${displayTopology.faces.length === 1 ? "" : "s"}`;
  inspector.innerHTML = `
    <div><small>selected class</small><strong>${cluster.label || `C${galleryIndex + 1}`}</strong><span>${cluster.geometry || "colored support polyhedron"} · ${surfaceLabel} · ${displayTopology.edges.length} topology edges</span></div>
    <div><small>complete-cover evidence</small><strong>${coveredAtoms.size.toLocaleString()} / ${referenceCount().toLocaleString()} atoms</strong><span>${placementIndices.length} occurrence${placementIndices.length === 1 ? "" : "s"} · ${supportSites} sites / occurrence · ${sharedAtoms} overlap-shared atoms</span></div>
    <div><small>proper-pose support</small><strong>${poseCount || "unresolved"} orbit${poseCount === 1 ? "" : "s"} · χ ${chirality}</strong><span>translation and atom order removed; mirrors remain distinct when resolved</span></div>
    <div><small>connection capacity</small><strong>${ports} port role${ports === 1 ? "" : "s"} → ${channels} channel${channels === 1 ? "" : "s"}</strong><span>${coverKind}</span></div>`;
}

function buildMolecularGalleryToolbar(types) {
  const toolbar = document.createElement("div");
  toolbar.className = "cluster-gallery-toolbar";
  const controls = document.createElement("div");
  controls.className = "cluster-family-filters";
  controls.setAttribute("role", "group");
  controls.setAttribute("aria-label", "Filter molecular cluster isometry classes");
  const status = document.createElement("p");
  const filters = learnedCover.molecular ? [
    ["all", "All exact classes"], ["molecule", learnedCover.molecular.water ? "H₂O molecules" : "Molecules"],
    ["bridge", "Bridge polyhedra"], ["gap", "Gap boundaries"],
  ] : [
    ["all", "All cover classes"], ["support", "Recurring supports"],
    ["residual", "Gap / residual terminals"],
  ];
  filters.forEach(([family, label], index) => {
    const count = family === "all" ? types.length
      : types.filter((cluster) => clusterGalleryFamily(cluster) === family).length;
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.clusterFamilyFilter = family;
    button.classList.toggle("active", index === 0);
    button.setAttribute("aria-pressed", String(index === 0));
    button.innerHTML = `<span>${label}</span><b>${count}</b>`;
    button.addEventListener("click", () => {
      controls.querySelectorAll("button").forEach((candidate) => {
        const active = candidate === button;
        candidate.classList.toggle("active", active);
        candidate.setAttribute("aria-pressed", String(active));
      });
      let visible = 0;
      clusterGallery.querySelectorAll(".cluster-card").forEach((card) => {
        const show = family === "all" || card.dataset.clusterFamily === family;
        card.hidden = !show;
        visible += Number(show);
      });
      status.textContent = `Showing ${visible} / ${types.length} colored complete-metric isometry classes · no classes merged`;
      const selected = clusterGallery.querySelector(".cluster-card.active:not([hidden])")
        || clusterGallery.querySelector(".cluster-card:not([hidden])");
      if (selected) updateClusterGalleryInspector(Number(selected.dataset.clusterIndex));
    });
    controls.append(button);
  });
  status.textContent = `Showing ${types.length} / ${types.length} colored complete-metric isometry classes · no classes merged`;
  const inspector = document.createElement("div");
  inspector.className = "cluster-gallery-inspector";
  inspector.setAttribute("aria-live", "polite");
  const ledger = buildMolecularCoverLedger(types);
  toolbar.append(controls, status);
  if (ledger) toolbar.append(ledger);
  toolbar.append(inspector);
  return toolbar;
}

function rebuildClusterGallery() {
  clusterGallery.replaceChildren();
  const types = clusterGalleryTypes();
  clusterGallery.append(buildMolecularGalleryToolbar(types));
  types.forEach((cluster, galleryIndex) => {
    const card = document.createElement("article");
    card.className = `cluster-card${cluster.residual ? " residual" : ""}${cluster.gap ? " gap" : ""}`;
    card.dataset.clusterIndex = String(galleryIndex);
    card.dataset.clusterFamily = clusterGalleryFamily(cluster);
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-pressed", "false");
    if (cluster.classSignature) card.dataset.isometrySignature = cluster.classSignature;
    const canvas = document.createElement("canvas");
    canvas.width = 280;
    canvas.height = 224;
    canvas.dataset.cluster = String(galleryIndex);
    const label = document.createElement("div");
    label.className = "cluster-card-label";
    const placements = cluster.classPlacementIndices?.length
      ?? learnedCover.placements.filter((placement) => placement.type === cluster.type).length;
    const familyIndex = cluster.familyType ?? galleryIndex;
    const poses = learnedCover.molecular ? galleryPoseCount(cluster)
      : orientationAtlas.find((entry) => entry.cluster === galleryIndex)?.orientations || 0;
    const channels = cluster.residual ? 0 : recommendedChannelsForCluster(familyIndex);
    const name = cluster.label || (cluster.residual ? "gap" : `C${cluster.type + 1}`);
    const ports = cluster.residual ? 0 : clusterPortRank(familyIndex);
    const coupledRank = cluster.residual ? 0 : clusterPosePortRank(familyIndex);
    const learnedDegrees = cluster.residual
      ? "explicit residual"
      : `${poses || "—"} required pose${poses === 1 ? "" : "s"} × ${ports} port role${ports === 1 ? "" : "s"} · rank ${coupledRank} → ${channels}ch`;
    const classStatus = Number.isInteger(cluster.classIndex)
      ? `isometry ${cluster.classIndex + 1}/${cluster.classCount} · ` : "";
    const supportSites = cluster.customSupport?.length
      || learnedCover.placements.find((placement) => placement.type === cluster.type)?.support.length || 1;
    const chirality = cluster.chirality ? ` · χ ${cluster.chirality}` : "";
    label.innerHTML = `<b>${name}</b><em>${cluster.geometry || "colored support polyhedron"}</em><span>${classStatus}${cluster.element || cluster.species} · ${placements} placement${placements === 1 ? "" : "s"} · ${learnedDegrees}</span><small>${supportSites} colored site${supportSites === 1 ? "" : "s"} · ${clusterCoverRole(cluster)}${chirality}</small>`;
    card.append(canvas, label);
    card.addEventListener("click", () => updateClusterGalleryInspector(galleryIndex));
    card.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      updateClusterGalleryInspector(galleryIndex);
    });
    clusterGallery.append(card);
  });
  updateClusterGalleryInspector(Math.min(selectedGalleryCluster, Math.max(0, types.length - 1)));
}

function convexHullTriangles(sites) {
  if (sites.length === 3) return [[0, 1, 2]];
  if (sites.length < 4) return [];
  const faces = [];
  const seen = new Set();
  const tolerance = 1e-7;
  for (let first = 0; first < sites.length - 2; first++) {
    for (let second = first + 1; second < sites.length - 1; second++) {
      for (let third = second + 1; third < sites.length; third++) {
        const normal = new THREE.Vector3().crossVectors(
          sites[second].vector.clone().sub(sites[first].vector),
          sites[third].vector.clone().sub(sites[first].vector),
        );
        if (normal.lengthSq() <= tolerance) continue;
        let positive = false;
        let negative = false;
        sites.forEach((site, index) => {
          if (index === first || index === second || index === third) return;
          const side = normal.dot(site.vector.clone().sub(sites[first].vector));
          if (side > tolerance) positive = true;
          if (side < -tolerance) negative = true;
        });
        if (positive && negative) continue;
        const face = positive ? [first, third, second] : [first, second, third];
        const key = face.slice().sort((a, b) => a - b).join(":");
        if (!seen.has(key)) { seen.add(key); faces.push(face); }
      }
    }
  }
  return faces;
}

function waterBridgePolyhedron(sites) {
  // buildWaterClusterCover stores each bridge as O,H,H,O,H,H.  Preserve the
  // two molecular faces and connect their corresponding vertices as a
  // triangular prism.  A generic hull is the wrong representation here:
  // water dimers are close to coplanar, so every coplanar triple can look like
  // a hull face and produces the misleading spoke/fan drawing.
  if (sites.length !== 6 || sites[0].atom.species !== "O" || sites[3].atom.species !== "O") return null;
  const firstHydrogens = [1, 2];
  const secondHydrogens = [4, 5];
  if (![...firstHydrogens, ...secondHydrogens].every((index) => sites[index].atom.species === "H")) return null;
  const direct = sites[1].vector.distanceTo(sites[4].vector) + sites[2].vector.distanceTo(sites[5].vector);
  const crossed = sites[1].vector.distanceTo(sites[5].vector) + sites[2].vector.distanceTo(sites[4].vector);
  const paired = direct <= crossed ? secondHydrogens : secondHydrogens.slice().reverse();
  const faces = [
    [0, 1, 2], [3, paired[1], paired[0]],
    [0, 3, paired[0], 1], [0, 2, paired[1], 3], [1, paired[0], paired[1], 2],
  ];
  const edges = new Map();
  faces.forEach((face) => face.forEach((first, index) => {
    const second = face[(index + 1) % face.length];
    const key = first < second ? `${first}:${second}` : `${second}:${first}`;
    if (!edges.has(key)) edges.set(key, [first, second, "outline"]);
  }));
  [[0, 1], [0, 2], [3, 4], [3, 5]].forEach(([first, second]) => {
    edges.set(`bond:${first}:${second}`, [first, second, "bond"]);
  });
  const hydrogenBond = [
    [1, 3], [2, 3], [4, 0], [5, 0],
  ].map(([first, second]) => ({ first, second, distance: sites[first].vector.distanceTo(sites[second].vector) }))
    .sort((first, second) => first.distance - second.distance)[0];
  if (hydrogenBond) edges.set("hydrogen-bond", [hydrogenBond.first, hydrogenBond.second, "hydrogen"]);
  return { faces, edges: [...edges.values()] };
}

function clusterDisplayTopology(cluster, sites) {
  if (cluster.visualKind === "molecule" && !cluster.displayEdges) {
    return { faces: [[0, 1, 2]], edges: [[0, 1, "bond"], [0, 2, "bond"], [1, 2, "outline"]] };
  }
  if (cluster.visualKind === "ring") {
    const edges = sites.map((_, index) => [index, (index + 1) % sites.length, "ring"]);
    return { faces: [sites.map((_, index) => index)], edges };
  }
  if (cluster.visualKind === "bridge") {
    const bridge = waterBridgePolyhedron(sites);
    if (bridge) return bridge;
  }
  const faces = convexHullTriangles(sites);
  const edges = new Map();
  faces.forEach((face) => face.forEach((first, index) => {
    const second = face[(index + 1) % face.length];
    const key = first < second ? `${first}:${second}` : `${second}:${first}`;
    if (!edges.has(key)) edges.set(key, [first, second, "outline"]);
  }));
  (cluster.displayEdges || []).forEach(([first, second, kind]) => {
    edges.set(`${kind}:${Math.min(first, second)}:${Math.max(first, second)}`, [first, second, kind]);
  });
  return { faces, edges: [...edges.values()] };
}

function clusterGallerySites(cluster) {
  const center = referenceAtoms[cluster.medoid];
  if (!cluster.customSupport) {
    const sites = [{ vector: new THREE.Vector3(), atom: center }];
    if (!cluster.residual) learnedClusters.environments[cluster.medoid].shell
      .filter((neighbor) => neighbor.r <= motifShellCutoff())
      .forEach((neighbor) => sites.push(neighbor));
    return sites;
  }
  const sites = cluster.customSupport.map((atomIndex, index) => ({
    vector: cluster.customVectors?.[index]?.clone() || periodicDisplacement(center, referenceAtoms[atomIndex]),
    atom: referenceAtoms[atomIndex],
  }));
  if (!cluster.customVectors?.length) {
    const centroid = sites.reduce((sum, site) => sum.add(site.vector), new THREE.Vector3())
      .multiplyScalar(1 / sites.length);
    sites.forEach((site) => site.vector.sub(centroid));
  }
  return sites;
}

function drawClusterGallery(now) {
  if (pipelineStage !== 1 || clusterGallery.hidden) return;
  const scaleToScene = referenceSpacing / referenceSpacingA;
  clusterGallery.querySelectorAll("canvas[data-cluster]").forEach((canvas, galleryIndex) => {
    const cluster = clusterGalleryTypes()[Number(canvas.dataset.cluster)];
    if (!cluster) return;
    const context = canvas.getContext("2d");
    context.clearRect(0, 0, canvas.width, canvas.height);
    const sites = clusterGallerySites(cluster);
    const angleY = now * (.00018 + galleryIndex * .000011) + galleryIndex * .83;
    const angleX = now * (.00009 + galleryIndex * .000007) + .35;
    const quaternion = new THREE.Quaternion().setFromEuler(new THREE.Euler(angleX, angleY, angleY * .23));
    const projected = sites.map((site, index) => {
      const point = site.vector.clone().multiplyScalar(scaleToScene).applyQuaternion(quaternion);
      const perspective = 1 / (1 + Math.max(-.7, point.z) * .11);
      return { index, atom: site.atom, x: canvas.width / 2 + point.x * 48 * perspective, y: canvas.height / 2 + point.y * 48 * perspective, z: point.z, perspective };
    });
    const projectedByIndex = new Map(projected.map((point) => [point.index, point]));
    const topology = clusterDisplayTopology(cluster, sites);
    const surface = cluster.residual || cluster.gap ? [255, 193, 105] : [101, 225, 188];
    topology.faces.map((face) => ({ face, depth: face.reduce((sum, index) => sum + projectedByIndex.get(index).z, 0) / face.length }))
      .sort((first, second) => first.depth - second.depth).forEach(({ face }, faceIndex) => {
        const points = face.map((index) => projectedByIndex.get(index));
        if (points.some((point) => !point)) return;
        context.beginPath(); context.moveTo(points[0].x, points[0].y);
        points.slice(1).forEach((point) => context.lineTo(point.x, point.y));
        context.closePath();
        context.fillStyle = `rgba(${surface.join(",")},${cluster.gap ? .13 : .075 + (faceIndex % 3) * .018})`;
        context.fill();
      });
    topology.edges.forEach(([first, second, kind]) => {
      const start = projectedByIndex.get(first), finish = projectedByIndex.get(second);
      if (!start || !finish) return;
      context.save();
      context.beginPath(); context.moveTo(start.x, start.y); context.lineTo(finish.x, finish.y);
      context.lineWidth = kind === "bond" ? 2.4 : kind === "hydrogen" ? 1.2 : 1.5;
      context.strokeStyle = kind === "hydrogen" ? "rgba(147,190,255,.7)" : kind === "outline"
        ? `rgba(${surface.join(",")},.25)` : `rgba(${surface.join(",")},.62)`;
      if (kind === "hydrogen") context.setLineDash([3, 4]);
      context.stroke(); context.restore();
    });
    projected.sort((first, second) => first.z - second.z).forEach((point) => {
      const record = elementRecord(point.atom.species);
      const radius = 7.4 * point.perspective * Math.min(1.12, record.radius / 1.3);
      context.beginPath(); context.arc(point.x, point.y, radius, 0, TAU);
      context.fillStyle = record.css; context.shadowColor = record.css; context.shadowBlur = 6; context.fill(); context.shadowBlur = 0;
      context.strokeStyle = "rgba(255,255,255,.42)"; context.stroke();
    });
  });
}

function learnOverlapMarking(source) {
  if (learnedCover?.occurrenceBased) return learnCoverOverlapMarking(source);
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

function learnCoverOverlapMarking(source) {
  const placements = learnedCover.placements;
  const supportSets = placements.map((placement) => new Set(placement.support));
  const edges = [];
  for (let first = 0; first < placements.length; first++) {
    for (let second = first + 1; second < placements.length; second++) {
      const sharedIndices = [...supportSets[first]].filter((index) => supportSets[second].has(index));
      if (!sharedIndices.length) continue;
      edges.push({
        first,
        second,
        shared: sharedIndices.length,
        sharedIndices,
        distance: periodicDisplacement(source[placements[first].center], source[placements[second].center]).length() / referenceSpacingA,
        firstCluster: placements[first].type + 1,
        secondCluster: placements[second].type + 1,
      });
    }
  }
  edges.sort((first, second) => second.shared - first.shared || first.distance - second.distance
    || first.first - second.first || first.second - second.second);
  const incident = Array.from({ length: placements.length }, () => []);
  edges.forEach((edge) => {
    incident[edge.first].push(edge.second);
    incident[edge.second].push(edge.first);
  });
  const states = new Map();
  const sourceDomains = placements.map((placement, occurrence) => {
    const counts = new Map();
    incident[occurrence].forEach((other) => {
      const type = placements[other].type + 1;
      counts.set(type, (counts.get(type) || 0) + 1);
    });
    const roles = [...counts.entries()].sort((a, b) => a[0] - b[0])
      .map(([type, count]) => `C${type}×${count}`).join("+") || "isolated";
    return `C${placement.type + 1}|s${placement.support.length}|${roles}`;
  });
  const samples = sourceDomains.map((domain, index) => {
    const shared = edges.filter((edge) => edge.first === index || edge.second === index)
      .reduce((sum, edge) => sum + edge.shared, 0);
    const score = -.8 + .08 * shared;
    const state = states.get(domain) || { count: 0, min: Infinity, max: -Infinity, sum: 0 };
    state.count++;
    state.min = Math.min(state.min, score);
    state.max = Math.max(state.max, score);
    state.sum += score;
    states.set(domain, state);
    return { domain, score };
  });
  const runningStates = new Map();
  let reusable = 0;
  let overlaps = 0;
  const curve = samples.map((sample, index) => {
    const count = (runningStates.get(sample.domain) || 0) + 1;
    runningStates.set(sample.domain, count);
    if (count === 2) reusable++;
    overlaps += edges.filter((edge) => Math.max(edge.first, edge.second) === index).length;
    return { samples: index + 1, discovered: runningStates.size, reusable, overlaps };
  });
  const ambiguous = [...states.values()].filter((state) => state.count < 2 || state.max - state.min > .12).length;
  return { states, sourceDomains, samples, curve, edges, ambiguous, covered: placements.length, occurrenceBased: true };
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

function supportOccurrenceFrame(source, placement) {
  const anchor = source[placement.center];
  const vectors = placement.support.filter((index) => index !== placement.center)
    .map((index) => {
      const vector = periodicDisplacement(anchor, source[index]);
      const fingerprint = [
        source[index].species,
        Math.round(vector.length() / referenceSpacingA * 1000),
        ...placement.support.filter((other) => other !== index).map((other) =>
          `${source[other].species}:${Math.round(periodicDisplacement(source[index], source[other]).length() / referenceSpacingA * 1000)}`)
          .sort(),
      ].join("|");
      return { index, vector, fingerprint };
    })
    .filter((entry) => entry.vector.lengthSq() > 1e-10)
    .sort((first, second) => first.fingerprint.localeCompare(second.fingerprint)
      || first.index - second.index);
  if (!vectors.length) return new THREE.Quaternion();
  const x = vectors[0].vector.clone().normalize();
  let transverse = null;
  let transverseNorm = -Infinity;
  vectors.slice(1).forEach((entry) => {
    const norm = new THREE.Vector3().crossVectors(x, entry.vector).lengthSq();
    if (norm > transverseNorm) { transverseNorm = norm; transverse = entry.vector; }
  });
  if (!transverse || transverseNorm < 1e-8) transverse = Math.abs(x.x) < .8
    ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0);
  const z = new THREE.Vector3().crossVectors(x, transverse).normalize();
  const y = new THREE.Vector3().crossVectors(z, x).normalize();
  return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z)).normalize();
}

function makeCoverOccurrence(source, placement, index) {
  const rotation = supportOccurrenceFrame(source, placement);
  const inverse = rotation.clone().invert();
  const scale = referenceSpacing / referenceSpacingA;
  const sites = placement.support.map((atomIndex) => ({
    local: periodicDisplacement(source[placement.center], source[atomIndex]).multiplyScalar(scale).applyQuaternion(inverse),
    species: source[atomIndex].species,
    center: atomIndex === placement.center,
    referenceIndex: atomIndex,
  }));
  return {
    index,
    type: placement.type,
    position: source[placement.center].p.clone(),
    rotation,
    sites,
    placement,
  };
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
  const templates = (learnedCover.types || clusterGalleryTypes()).map((cluster) => ({
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
      const molecule = occurrences.find((occurrence) => occurrence.placement.family === "molecule"
        && occurrence.placement.support.includes(missing));
      if (!molecule) break;
      const anchors = [...coveredAtoms].map((atomIndex) => ({ atomIndex,
        distance: periodicDisplacement(source[molecule.placement.center], source[atomIndex]).length() }))
        .sort((first, second) => first.distance - second.distance).slice(0, 2).map((entry) => entry.atomIndex);
      if (anchors.length < 2) break;
      const connector = { center: molecule.placement.center,
        support: [...new Set([...anchors, ...molecule.placement.support])],
        type: learnedCover.types.length, residual: true, gap: true,
        kind: "learned residual gap connector", family: "gap" };
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
  return { molecular: true, coverBased: true, occurrences, templates, rules: [], byFrom: new Map(),
    reconstructionByOccurrence, replaySeedIndex, replayReachable: coveredAtoms.size,
    reconstructionEdges, observations: reconstructionEdges, recurring: 0, heldoutSupported: 0 };
}

function learnIrregularOverlapGrammar(source) {
  const occurrences = learnedCover.placements.map((placement, index) => makeCoverOccurrence(source, placement, index));
  const templates = learnedCover.types.map((cluster) => {
    const occurrence = occurrences.find((candidate) => candidate.type === cluster.type);
    return {
      type: cluster.type,
      medoid: cluster.medoid,
      sites: occurrence?.sites || [],
      radius: Math.max(0, ...(occurrence?.sites || []).map((site) => site.local.length())),
    };
  });
  const buckets = new Map();
  const addObservation = (firstIndex, secondIndex, edge, heldout) => {
    const first = occurrences[firstIndex];
    const second = occurrences[secondIndex];
    if (!first || !second || first.placement.residual || second.placement.residual) return;
    const inverse = first.rotation.clone().invert();
    const translation = periodicDisplacement(source[first.placement.center], source[second.placement.center])
      .multiplyScalar(referenceSpacing / referenceSpacingA).applyQuaternion(inverse);
    const rotation = inverse.multiply(second.rotation).normalize();
    const pairKey = `${first.type}>${second.type}`;
    const rules = buckets.get(pairKey) || [];
    let rule = rules.find((candidate) => candidate.translation.distanceTo(translation) < .16
      && quaternionDistance(candidate.rotation, rotation) < .24);
    if (!rule) {
      rule = {
        from: first.type,
        to: second.type,
        translation: translation.clone(),
        rotation: rotation.clone(),
        representativeTranslation: translation.clone(),
        representativeRotation: rotation.clone(),
        representativeShared: edge.shared,
        representativePair: [firstIndex, secondIndex],
        count: 0,
        fitCount: 0,
        holdoutCount: 0,
        sharedTotal: 0,
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
  const strongEdges = trainedMarking.edges.filter((edge) => edge.shared >= 2
    && edge.distance <= overlapDistanceCutoff());
  strongEdges.forEach((edge, index) => {
    const heldout = index % 5 === 0;
    addObservation(edge.first, edge.second, edge, heldout);
    addObservation(edge.second, edge.first, edge, heldout);
  });
  const rules = [];
  [...buckets.entries()].forEach(([pairKey, pairRules]) => {
    pairRules.sort((first, second) => second.count - first.count || second.sharedTotal - first.sharedTotal)
      .slice(0, MAX_RULES_PER_PAIR).forEach((rule) => {
        rule.translation.copy(rule.representativeTranslation);
        rule.rotation.copy(rule.representativeRotation);
        rule.id = rules.length;
        rule.pairKey = pairKey;
        rule.meanShared = rule.sharedTotal / Math.max(1, rule.count);
        rule.rotationAngle = 2 * Math.acos(Math.min(1, Math.abs(rule.rotation.w)));
        rule.sites = occurrences[rule.representativePair[1]].sites;
        rules.push(rule);
      });
  });
  const byFrom = new Map();
  rules.forEach((rule) => {
    const list = byFrom.get(rule.from) || [];
    list.push(rule);
    byFrom.set(rule.from, list);
  });
  const reconstructionByOccurrence = new Map();
  const addReconstructionEdge = (firstIndex, secondIndex, edge) => {
    const first = occurrences[firstIndex];
    const second = occurrences[secondIndex];
    if (!first || !second) return;
    const inverse = first.rotation.clone().invert();
    const exactRule = {
      id: `I${firstIndex}-${secondIndex}`,
      from: first.type,
      to: second.type,
      occurrenceFrom: firstIndex,
      occurrenceTo: secondIndex,
      reconstructionOnly: true,
      translation: periodicDisplacement(source[first.placement.center], source[second.placement.center])
        .multiplyScalar(referenceSpacing / referenceSpacingA).applyQuaternion(inverse),
      rotation: inverse.multiply(second.rotation).normalize(),
      count: 1,
      meanShared: edge.shared,
      sites: second.sites,
    };
    const adjacency = reconstructionByOccurrence.get(firstIndex) || [];
    adjacency.push(exactRule);
    reconstructionByOccurrence.set(firstIndex, adjacency);
  };
  strongEdges.forEach((edge) => {
    addReconstructionEdge(edge.first, edge.second, edge);
    addReconstructionEdge(edge.second, edge.first, edge);
  });
  const replaySeedIndex = rules.slice().sort((first, second) => second.count - first.count)[0]?.representativePair[0]
    ?? learnedCover.irregular?.replaySeedPlacementIndex ?? 0;
  const reachableOccurrences = new Set(occurrences[replaySeedIndex] ? [replaySeedIndex] : []);
  const replayQueue = [...reachableOccurrences];
  while (replayQueue.length) {
    const current = replayQueue.shift();
    (reconstructionByOccurrence.get(current) || []).forEach((rule) => {
      if (reachableOccurrences.has(rule.occurrenceTo)) return;
      reachableOccurrences.add(rule.occurrenceTo);
      replayQueue.push(rule.occurrenceTo);
    });
  }
  return {
    coverBased: true,
    occurrences,
    templates,
    rules,
    byFrom,
    reconstructionByOccurrence,
    replaySeedIndex,
    replayReachable: reachableOccurrences.size,
    reconstructionEdges: strongEdges.length * 2,
    observations: strongEdges.length * 2,
    recurring: rules.filter((rule) => rule.count >= 2).length,
    heldoutSupported: rules.filter((rule) => rule.holdoutCount > 0).length,
  };
}

function learnOverlapGrammar(source) {
  if (learnedCover?.molecular) return learnMolecularOverlapGrammar(source);
  if (learnedCover?.occurrenceBased) return learnIrregularOverlapGrammar(source);
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
  sites: { label: "site-resolved section", short: "site resolved", exponent: 4, overlapWeight: .58,
    readout: "minimum-weighted colored-site compatibility" },
  halo: { label: "local radial / angular halo", short: "local halo", exponent: 5, overlapWeight: .64,
    readout: "port and support-halo mean" },
  "chiral-halo": { label: "chiral local halo", short: "chiral halo", exponent: 5.5, overlapWeight: .66,
    readout: "halo plus learned mirror-odd colored-connection pseudoscalar" },
  ports: { label: "connection-port vector", short: "port vector", exponent: 6, overlapWeight: .70,
    readout: "bidirectional endpoint-port agreement" },
  whole: { label: "whole-cluster action", short: "whole action", exponent: 2, overlapWeight: .38,
    readout: "mean-dominant whole-template support" },
};
const MARKING_LIBRARY_STORAGE = "gcts-marking-library-v3";
const MARKING_VOCABULARY_SCHEMA = 3;

function restoreMarkingLibrary() {
  try {
    const stored = JSON.parse(localStorage.getItem(MARKING_LIBRARY_STORAGE) || "null");
    if (!stored || !Array.isArray(stored.markings)) return;
    markingLibrary = stored.markings.filter((marking) => marking?.id && marking?.config
      && typeof marking.vocabularyKey === "string"
      && Array.isArray(marking.coefficients) && MARKING_REPRESENTATIONS[marking.config.representation])
      .map((marking) => ({ ...marking, config: {
        ...marking.config, geometryMode: marking.config.geometryMode || "auto",
      } }));
    activeMarkingId = stored.activeMarkingId || null;
    markingSearchMode = stored.searchMode === "portfolio" ? "portfolio" : "single";
    nextMarkingId = Math.max(1, ...markingLibrary.map((marking) => Number(marking.id.split("-").at(-1)) + 1 || 1));
  } catch (_) {
    markingLibrary = [];
    activeMarkingId = null;
  }
}

function persistMarkingLibrary() {
  try {
    localStorage.setItem(MARKING_LIBRARY_STORAGE, JSON.stringify({
      markings: markingLibrary, activeMarkingId, searchMode: markingSearchMode,
    }));
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
    geometryMode,
  };
}

const receiptRound = (value, digits = 8) => Number(Number(value).toFixed(digits));

async function receiptSha256(text) {
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join("");
}

async function structureDigest(source, coordinateSpace) {
  const records = source.map((atom) => {
    const point = coordinateSpace === "angstrom" && atom.pA ? atom.pA : atom.p;
    return [atom.species, ...point.toArray().map((value) => receiptRound(value))];
  }).sort((first, second) => JSON.stringify(first).localeCompare(JSON.stringify(second)));
  return receiptSha256(JSON.stringify(records));
}

function receiptComposition(source) {
  const counts = new Map();
  source.forEach((atom) => counts.set(atom.species, (counts.get(atom.species) || 0) + 1));
  return Object.fromEntries([...counts.entries()].sort(([first], [second]) => first.localeCompare(second)));
}

function receiptClusterRecord(cluster, index) {
  const familyIndex = cluster.familyType ?? index;
  const placements = cluster.classPlacementIndices?.length
    ?? learnedCover.placements.filter((placement) => placement.type === cluster.type).length;
  const supportSites = cluster.customSupport?.length
    || learnedCover.placements.find((placement) => placement.type === cluster.type)?.support.length || 1;
  return {
    id: Number.isInteger(cluster.classIndex) ? `${clusterGalleryFamily(cluster)}:${cluster.classIndex + 1}` : `C${index + 1}`,
    label: cluster.label || `C${index + 1}`,
    family: clusterGalleryFamily(cluster),
    coverRole: clusterCoverRole(cluster),
    coloredSupportSites: supportSites,
    occurrences: placements,
    observedProperPoseOrbits: galleryPoseCount(cluster),
    portRoles: cluster.residual ? 0 : clusterPortRank(familyIndex),
    posePortRank: cluster.residual ? 0 : clusterPosePortRank(familyIndex),
    recommendedChannels: cluster.residual ? 0 : recommendedChannelsForCluster(familyIndex),
    chirality: cluster.chirality ?? null,
    isometryClass: Number.isInteger(cluster.classIndex) ? cluster.classIndex + 1 : null,
    familyClassCount: cluster.classCount ?? null,
  };
}

function receiptGrowthClaims(scenarioId, benchmark, trace) {
  const symbolicRecursiveSystems = new Set(["competition", "graphene", "hbn", "moire"]);
  const symbolicRecursiveScaling = benchmark.status === "pass" && symbolicRecursiveSystems.has(scenarioId);
  const stationaryProductionSystems = new Set(["competition"]);
  return {
    structuralContinuationOnly: true,
    physicalPotentialUsed: false,
    physicalElapsedTimeModeled: false,
    growthRateClaimed: false,
    targetCoordinatesIncluded: false,
    stationaryProductionCertified: benchmark.status === "pass" && stationaryProductionSystems.has(scenarioId),
    symbolicRecursiveScalingClaimed: symbolicRecursiveScaling,
    genericExponentialGctsClaimed: false,
    finiteFixedPointContinuation: Boolean(trace?.fixedPoint),
    iceProtonOrientationsResolved: trace ? false : null,
  };
}

async function buildExperimentReceipt() {
  const material = currentMaterial();
  const markingConfig = currentMarkingConfig();
  const activeMarking = selectedMarking();
  const benchmark = RECURSIVE_BENCHMARKS[scenarioSelect.value] || RECURSIVE_BENCHMARKS.imported;
  const cell = currentCell();
  const coverVisible = pipelineStage >= 1;
  const markingVisible = pipelineStage >= 3;
  const searchVisible = pipelineStage >= 4;
  const referenceSq = ensureStructureFactor(referenceStructuralStats);
  const receipt = {
    schema: "gcts-materials-growth-receipt-v1",
    generatedAt: new Date().toISOString(),
    application: {
      name: "Materials Growth Lab",
      buildId: "20260824-31",
      pipelineStages: ["sample configuration", "cluster identification", "GCTS learning", "material growth"],
    },
    input: {
      sourceKind: scenarioSelect.value === "imported"
        ? (importedStructure?.metadata?.entryId ? "public-database structure" : "locally parsed structure")
        : "deterministic curated fixture",
      scenarioId: scenarioSelect.value,
      materialName: material.name,
      elements: [...material.elements],
      composition: receiptComposition(referenceAtoms),
      atomCount: referenceAtoms.length,
      structureSha256: await structureDigest(referenceAtoms, "angstrom"),
      coordinatesEmbedded: false,
      coordinateDigestSpace: "Cartesian Å; order-independent serialization",
      periodicBoundary: currentPbc(),
      cellAngstrom: cell?.map((vector) => vector.toArray().map((value) => receiptRound(value))) || null,
      sourceReference: scenarioSelect.value === "imported" ? {
        name: importedStructure?.metadata?.name || importedStructure?.filename || null,
        entryId: importedStructure?.metadata?.entryId || null,
        materialId: importedStructure?.metadata?.materialId || null,
        format: importedStructure?.format || null,
      } : { fixture: scenarioSelect.value,
        generatorAudit: scenarioSelect.value === "random" ? referenceAtoms[0]?.glassAudit || null : null },
    },
    pipeline: {
      internalStage: pipelineStage,
      visibleStage: visiblePipelineOrdinal(pipelineStage),
      stageName: ["sample configuration", "cluster identification", "rigid encoding", "GCTS learning", "material growth"][pipelineStage],
    },
    geometry: {
      requestedMode: geometryMode,
      resolvedMode: resolvedGeometryMode(),
      resolvedLabel: resolvedGeometryLabel(),
      nearestNeighborAngstrom: receiptRound(referenceSpacingA),
      periodicAxes: currentPbc(),
      inferredUnitCell: Boolean(detectedUnitCell),
      rotationGroup: rotationGroupLabel(),
      poseAtlas: orientationAtlas.map((entry) => ({
        cluster: entry.cluster,
        observedProperPoseOrbits: entry.orientations,
        populations: [...entry.populations],
        support: entry.support,
      })),
      coloredDistanceEnvelopes: {
        role: "hard geometric exclusion learned from supplied positions; not a pair potential",
        config: coloredDistanceEnvelopes.config,
        fallbackExclusionAngstrom: receiptRound(coloredDistanceEnvelopes.fallbackExclusion * referenceSpacingA / referenceSpacing),
        pairs: coloredDistanceEnvelopes.records.map((record) => ({
          species: record.species,
          minimumObservedAngstrom: receiptRound(record.minimumObserved * referenceSpacingA / referenceSpacing),
          lowerContactAngstrom: receiptRound(record.lowerContact * referenceSpacingA / referenceSpacing),
          typicalContactAngstrom: receiptRound(record.typicalContact * referenceSpacingA / referenceSpacing),
          upperContactAngstrom: receiptRound(record.upperContact * referenceSpacingA / referenceSpacing),
          strainScaleAngstrom: receiptRound(record.contactScale * referenceSpacingA / referenceSpacing),
          hardExclusionAngstrom: receiptRound(record.exclusion * referenceSpacingA / referenceSpacing),
          nearestObservations: record.nearestObservations,
        })),
      },
      coloredCoordinationEnvelopes: {
        role: "causal upper saturation limits; incomplete frontier shells may remain below the bound",
        config: coloredCoordinationEnvelopes.config,
        pairs: coloredCoordinationEnvelopes.records.map((record) => ({
          centerSpecies: record.centerSpecies,
          neighborSpecies: record.neighborSpecies,
          contactCutoffAngstrom: receiptRound(record.contactCutoff * referenceSpacingA / referenceSpacing),
          medianObserved: record.medianObserved,
          upperObserved: record.upperObserved,
          maximumObserved: record.maximumObserved,
          centerObservations: record.centerObservations,
        })),
      },
      coloredAngularEnvelopes: {
        role: "causal three-body admissibility bands over already present contact neighbors; not an angular potential",
        config: coloredAngularEnvelopes.config,
        triplets: coloredAngularEnvelopes.records.map((record) => ({
          centerSpecies: record.centerSpecies,
          neighborSpecies: record.neighborSpecies,
          allowedBandsDegrees: record.bands.map((band) => [receiptRound(band.minimum), receiptRound(band.maximum)]),
          observedMedianDegrees: receiptRound(record.medianObservedDegrees),
          angleObservations: record.angleObservations,
          centerObservations: record.centerObservations,
        })),
      },
      compositionReservoir: {
        role: "observed multicomponent fractions used only for optional soft frontier balancing; not charge or chemical potential",
        reducedRatio: compositionTarget.reducedRatio,
        fractions: compositionTarget.fractions,
        observations: compositionTarget.observations,
      },
    },
    structuralEvidence: {
      role: "posthoc validation only; never a growth feature or branch score",
      selectedView: structureObservableSelection,
      rdf: {
        dimension: referenceStructuralStats.dimension,
        pair: rdfPairSelection,
        maximumRadiusInNearestNeighborUnits: receiptRound(referenceStructuralStats.maximumRadius),
        correction: referenceStructuralStats.edgeCorrection,
      },
      geometricPowderStructureFactor: {
        dimension: referenceSq.dimension,
        qMinTimesNearestNeighbor: referenceSq.qMin,
        qMaxTimesNearestNeighbor: referenceSq.qMax,
        bins: referenceSq.values.length,
        peakQTimesNearestNeighbor: receiptRound(referenceSq.summary.peakQ),
        peakHeight: receiptRound(referenceSq.summary.peakHeight),
        highQMean: receiptRound(referenceSq.summary.highQMean),
        unitScatteringWeights: true,
        xrayFormFactorsUsed: false,
        neutronScatteringLengthsUsed: false,
        experimentalIntensityClaimed: false,
      },
    },
    cover: coverVisible ? {
      status: learnedCover.complete ? "complete" : "incomplete",
      periodic: learnedCover.periodic,
      coveredAtoms: learnedCover.covered,
      inputAtoms: referenceAtoms.length,
      placements: learnedCover.placements.length,
      isometryTypes: clusterGalleryTypes().length,
      residualTypes: learnedCover.residualTypes?.length || 0,
      molecularFamilies: learnedCover.molecular || null,
      molecularDiscovery: learnedCover.molecularDiscovery || null,
      irregularMining: learnedCover.irregular || null,
      classes: clusterGalleryTypes().map(receiptClusterRecord),
    } : { status: "stage not entered" },
    marking: {
      status: markingVisible ? "trained" : "configured; stage not entered",
      config: markingConfig,
      searchMode: markingSearchMode,
      compatibleLibraryEntries: compatibleMarkings().map((marking) => ({ id: marking.id, name: marking.name })),
      active: markingVisible && activeMarking ? {
        id: activeMarking.id,
        name: activeMarking.name,
        vocabularyKey: activeMarking.vocabularyKey,
        config: activeMarking.config,
        representationReadout: MARKING_REPRESENTATIONS[activeMarking.config.representation]?.readout || null,
        representationState: activeMarking.representationState || null,
        coefficients: activeMarking.coefficients.map((row) => row.map((value) => receiptRound(value))),
      } : null,
      learned: markingVisible ? {
        prototypes: sectionModel.prototypeCount,
        channels: sectionModel.channels,
        reach: sectionModel.reach,
        representation: sectionModel.representation,
        representationReadout: MARKING_REPRESENTATIONS[sectionModel.representation]?.readout || null,
        learnedChiralPortClasses: Object.keys(sectionModel.representationState?.chiralPreferences || {}).length,
        fitSamples: sectionModel.fitCount ?? sectionModel.curve.length,
        holdoutSamples: sectionModel.holdoutCount ?? 0,
      } : null,
    },
    search: searchVisible ? {
      policy: policySelect.value,
      hierarchyEnabled: Boolean(hierarchyEnabled && !iceAnchorTrace),
      markingLibraryMode: markingSearchMode,
      scheduling: {
        mode: growthScheduling,
        candidateAction: "one frozen whole colored-cluster template placement",
        underlyingSearch: "dependency-ordered tree search",
        displayedUpdate: growthScheduling === "commuting"
          ? "maximal pairwise-compatible antichain; every accepted placement is valid in every permutation"
          : "one best-first branch decision",
        candidateGeometryChangedByScheduling: false,
      },
      explicitSites: atoms.length,
      explicitSitesSha256: await structureDigest(atoms, "scene"),
      coordinateDigestSpace: "scene coordinates; order-independent serialization; coordinates not embedded",
      placedClusters: placedClusters.length,
      acceptedDecisions,
      rejectedDecisions,
      coordinationCapacityPrunes,
      angularEnvelopePrunes,
      geometricStrainRanking: {
        role: "target-blind soft ordering of the unchanged exact candidate set; not energy or admissibility",
        mode: geometryPreference,
        enabled: geometryPreference === "strain",
        configuredWeight: geometricStrainWeight,
        effectiveWeight: activeGeometricStrainWeight(),
        acceptedMean: receiptRound(acceptedGeometricStrain / Math.max(1, acceptedDecisions)),
        rejectedMean: receiptRound(rejectedGeometricStrain / Math.max(1, rejectedDecisions)),
      },
      compositionBalanceRanking: {
        role: "target-blind soft ordering toward the observed multicomponent reservoir; never a hard surface constraint",
        mode: compositionPreference,
        effectiveWeight: activeCompositionBalanceWeight(),
        targetReducedRatio: compositionTarget.reducedRatio,
        acceptedMeanScaledDelta: receiptRound(acceptedCompositionDelta / Math.max(1, acceptedDecisions)),
        rejectedMeanScaledDelta: receiptRound(rejectedCompositionDelta / Math.max(1, rejectedDecisions)),
      },
      surfaceCompletionRanking: {
        role: "target-blind soft ordering that favors healing sample-derived coordination deficits; not bond or surface energy",
        mode: surfacePreference,
        effectiveWeight: activeSurfaceCompletionWeight(),
        target: "ordered species coordination medians learned from the supplied configuration",
        acceptedMeanScaledDelta: receiptRound(acceptedSurfaceDeficit / Math.max(1, acceptedDecisions)),
        rejectedMeanScaledDelta: receiptRound(rejectedSurfaceDeficit / Math.max(1, rejectedDecisions)),
      },
      localConstraintWork: {
        role: "exact finite-reach neighborhood evaluation via the live spatial index; not an approximation or sampled cutoff",
        maximumReachAngstrom: receiptRound(coloredCoordinationEnvelopes.maximumCutoff * referenceSpacingA / referenceSpacing),
        evaluations: constraintNeighborhoodEvaluations,
        meanProjectedSites: receiptRound(constraintNeighborhoodSiteTotal / Math.max(1, constraintNeighborhoodEvaluations)),
        maximumProjectedSites: maximumConstraintNeighborhoodSites,
        currentFullSites: atoms.length,
      },
      grammarDecisions,
      localOracleCalls: oracleCalls,
      liveCertificate: liveGrowthCertificate(),
      finiteIceAnchorTrace: iceAnchorTrace ? {
        artifactDigest: ICE_MOLECULAR_PORT_ARTIFACT.artifactDigest,
        caseId: iceAnchorTrace.caseId,
        seedAnchors: iceAnchorTrace.seedAnchors,
        waves: iceAnchorTrace.waves.map((wave) => ({
          wave: wave.wave,
          candidateAnchors: wave.candidateAnchors,
          acceptedAnchors: wave.acceptedAnchors,
          retainedOrientationHypotheses: wave.retainedOrientationHypotheses,
          rejectedNonunanimousAnchors: wave.rejectedNonunanimousAnchors,
        })),
        emittedAnchorCount: iceAnchorTrace.emittedAnchors.length,
        unresolvedOrientationDomains: iceAnchorTrace.unresolvedOrientationHypotheses,
        targetUsed: iceAnchorTrace.targetUsed,
        fixedPoint: iceAnchorTrace.fixedPoint,
        exactBackendCountParity: iceAnchorTrace.exactBackendCountParity,
      } : null,
    } : { status: "stage not entered" },
    evidenceBoundary: {
      benchmarkStatus: benchmark.status,
      benchmarkGate: benchmark.gate,
      ...receiptGrowthClaims(scenarioSelect.value, benchmark, iceAnchorTrace),
      note: benchmark.note,
    },
  };
  const experimentState = JSON.parse(JSON.stringify(receipt));
  delete experimentState.generatedAt;
  receipt.experimentStateSha256 = await receiptSha256(JSON.stringify(experimentState));
  receipt.receiptSha256 = await receiptSha256(JSON.stringify(receipt));
  return receipt;
}

async function serializedExperimentReceipt() {
  return `${JSON.stringify(await buildExperimentReceipt(), null, 2)}\n`;
}

async function withReceiptStatus(button, action) {
  const original = button.textContent;
  button.disabled = true;
  receiptStatus.textContent = "Building stage-aware receipt…";
  try {
    await action();
  } catch (error) {
    receiptStatus.textContent = `Receipt failed: ${error.message}`;
    console.error(error);
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

function markingMaterialKey() {
  return scenarioSelect.value === "imported"
    ? `imported:${importedStructure?.metadata?.entryId || importedStructure?.metadata?.name || referenceCount()}`
    : scenarioSelect.value;
}

function integerGcd(first, second) {
  let a = Math.abs(first);
  let b = Math.abs(second);
  while (b) [a, b] = [b, a % b];
  return a || 1;
}

function reducedCompositionKey() {
  const counts = new Map();
  referenceAtoms.forEach((atom) => counts.set(atom.species, (counts.get(atom.species) || 0) + 1));
  const divisor = [...counts.values()].reduce(integerGcd, 0) || 1;
  return [...counts.entries()].sort(([first], [second]) => first.localeCompare(second))
    .map(([species, count]) => `${species}${count / divisor}`).join(":");
}

function prototypeGeometryKey(prototype, index) {
  if (learnedCover?.occurrenceBased || learnedCover?.molecular) {
    const sites = prototype.customSupport.map((atomIndex) => referenceAtoms[atomIndex].species);
    const distances = [];
    for (let first = 0; first < prototype.customVectors.length; first++) {
      for (let second = first + 1; second < prototype.customVectors.length; second++) {
        const pair = [sites[first], sites[second]].sort().join("-");
        distances.push(`${pair}:${Math.round(prototype.customVectors[first]
          .distanceTo(prototype.customVectors[second]) / referenceSpacing * 100)}`);
      }
    }
    return `${sites.sort().join("")}|${distances.sort().join(",")}`;
  }
  const environment = learnedClusters.environments[prototype.medoid];
  return environment.features.map((value) => Math.round(value * 100)).join(",");
}

function markingVocabularyKey() {
  return JSON.stringify({
    schema: MARKING_VOCABULARY_SCHEMA,
    geometry: resolvedGeometryMode(),
    dimension: currentMaterial().intrinsicDimension || 3,
    composition: reducedCompositionKey(),
    prototypes: markingPrototypeTypes().map((prototype, index) => {
      const atlas = orientationAtlas.find((entry) => entry.cluster === index);
      return [
        prototype.element || prototype.species || "residual",
        prototype.gap ? "gap" : prototype.residual ? "residual" : "cluster",
        prototypeGeometryKey(prototype, index),
        atlas?.orientations || 0,
        atlas ? poseAtlasEntryStatus(atlas) : "unresolved support",
        clusterPortRank(index), clusterPosePortRank(index),
      ];
    }),
  });
}

function ruleColoredSiteGeometry(rule) {
  const sites = rule.sites || overlapGrammar.templates[rule.to]?.sites || [];
  return sites.map((site) => {
    const invariantNeighbors = sites.filter((other) => other !== site).map((other) =>
      `${other.species}:${Math.round(site.local.distanceTo(other.local) * 1000)}`).sort();
    const token = `${site.species}|${Math.round(site.local.length() * 1000)}|${invariantNeighbors.join(",")}`;
    return {
      token,
      local: site.local,
      parentVector: site.local.clone().applyQuaternion(rule.rotation).add(rule.translation),
    };
  });
}

function ruleColoredChirality(rule) {
  const sites = ruleColoredSiteGeometry(rule).map((site) => ({
    token: site.token,
    vector: site.parentVector.toArray(),
  }));
  return coloredConnectionChirality(rule.translation.toArray(), sites);
}

function learnRepresentationState() {
  const accumulators = new Map();
  (overlapGrammar?.rules || []).forEach((rule) => {
    const key = `${rule.from}>${rule.to}`;
    const state = accumulators.get(key) || { weightedSum: 0, observations: 0 };
    const observations = Math.max(1, rule.count || 1);
    state.weightedSum += ruleColoredChirality(rule) * observations;
    state.observations += observations;
    accumulators.set(key, state);
  });
  return {
    chiralPreferences: Object.fromEntries([...accumulators.entries()].map(([key, state]) => [key, {
      mean: state.weightedSum / state.observations,
      observations: state.observations,
    }])),
  };
}

function learnSectionModel(source, config = currentMarkingConfig()) {
  if (learnedCover?.occurrenceBased || learnedCover?.molecular) return learnMolecularSectionModel(source, config);
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
    fitCount: fitIndices.length, holdoutCount: holdoutIndices.length,
    prototypeCount: clusterCount, sampleLabels: learnedClusters.labels.slice(),
    representationState: learnRepresentationState(),
    sampleKind: "atom-centred environment" };
}

function learnMolecularSectionModel(source, config) {
  const axes = BALANCE_DIRECTIONS;
  const representation = MARKING_REPRESENTATIONS[config.representation] || MARKING_REPRESENTATIONS.sites;
  const reachScale = { 1: .72, 2: 1, 3: 1.35 }[config.reach] || 1;
  const support = descriptorCutoff() * reachScale;
  const exponent = representation.exponent;
  const overlapWeight = representation.overlapWeight;
  const channelGain = 1 + Math.log2(Math.max(1, config.channels)) * .065;
  const samples = overlapGrammar.occurrences;
  const prototypeCount = (learnedCover.types || clusterGalleryTypes()).length;
  const sampleLabels = samples.map((occurrence) => occurrence.type);
  const incident = Array.from({ length: samples.length }, () => []);
  overlapGrammar.reconstructionByOccurrence.forEach((rules, parent) => rules.forEach((rule) => {
    const child = rule.occurrenceTo;
    if (!Number.isInteger(child) || !samples[child]) return;
    const forward = rule.translation.clone().normalize();
    const reverse = rule.translation.clone().negate().normalize().applyQuaternion(rule.rotation.clone().invert());
    incident[parent].push({ direction: forward, shared: rule.meanShared || 0 });
    incident[child].push({ direction: reverse, shared: rule.meanShared || 0 });
  }));
  const targets = samples.map((_, index) => {
    const values = new Array(axes.length).fill(-.18 / channelGain);
    incident[index].forEach((port) => {
      let bestAxis = 0;
      let bestDot = -Infinity;
      axes.forEach((axis, axisIndex) => {
        const dot = port.direction.dot(axis);
        if (dot > bestDot) { bestDot = dot; bestAxis = axisIndex; }
      });
      values[bestAxis] = Math.max(values[bestAxis], Math.min(.36,
        (.10 + port.shared * .035) * channelGain));
    });
    return values;
  });
  const initial = Array.from({ length: prototypeCount }, (_, cluster) =>
    axes.map((_, axis) => (siteHash(cluster, axis, 29, 6) - .5) * .34 / Math.sqrt(channelGain)));
  const coefficients = initial.map((values) => values.slice());
  const fitIndices = samples.map((_, index) => index).filter((index) => index % 5 !== 0);
  const holdoutIndices = samples.map((_, index) => index).filter((index) => index % 5 === 0);
  const lossFor = (indices, values = coefficients) => indices.reduce((sum, index) => {
    const coefficientsForType = values[sampleLabels[index]];
    return sum + targets[index].reduce((error, target, axis) =>
      error + (coefficientsForType[axis] - target) ** 2, 0) / axes.length;
  }, 0) / Math.max(1, indices.length);
  let trainLoss = lossFor(fitIndices);
  let validationLoss = lossFor(holdoutIndices);
  const initialPoint = {
    samples: 0, fitSamples: 0, holdoutSamples: 0, overlaps: 0,
    trainLoss, validationLoss, coefficients: initial.map((values) => values.slice()),
  };
  let fitSamples = 0;
  let holdoutSamples = 0;
  let overlaps = 0;
  const curve = samples.map((_, index) => {
    const cluster = sampleLabels[index];
    if (index % 5 === 0) holdoutSamples++;
    else {
      fitSamples++;
      const step = .14 / (1 + Math.log2(Math.max(1, config.channels)) * .12);
      coefficients[cluster] = coefficients[cluster].map((value, axis) =>
        value + step * (targets[index][axis] - value));
    }
    overlaps += incident[index].length;
    trainLoss = lossFor(fitIndices);
    validationLoss = lossFor(holdoutIndices);
    return {
      samples: index + 1, fitSamples, holdoutSamples, overlaps,
      trainLoss, validationLoss,
      coefficients: coefficients.map((values) => values.slice()),
    };
  });
  return {
    axes, targets, initial, initialPoint, curve, support,
    channels: config.channels, channelMode: config.channelMode || "manual",
    reach: config.reach, representation: config.representation,
    overlapWeight, exponent, channelGain,
    fitCount: fitIndices.length, holdoutCount: holdoutIndices.length,
    prototypeCount, sampleLabels,
    representationState: learnRepresentationState(),
    sampleKind: learnedCover.molecular ? "molecular cover occurrence" : "irregular support occurrence",
  };
}

function markingSampleCount() {
  return sectionModel?.curve.length || referenceCount();
}

function markingPrototypeTypes() {
  return learnedCover?.occurrenceBased || learnedCover?.molecular ? learnedCover.types : learnedClusters.clusters;
}

function markingPrototypeName(index) {
  const prototype = markingPrototypeTypes()[index];
  return learnedCover?.occurrenceBased || learnedCover?.molecular
    ? prototype?.label || `C${index + 1}` : `C${index + 1}`;
}

function currentSectionPoint() {
  return trainingProgress > 0
    ? sectionModel.curve[Math.min(trainingProgress, sectionModel.curve.length) - 1]
    : sectionModel.initialPoint;
}

function currentSectionCoefficients(cluster) {
  return currentSectionPoint().coefficients[cluster];
}

function selectedMarking() {
  return compatibleMarkings().find((marking) => marking.id === activeMarkingId) || null;
}

function searchSectionCoefficients() {
  const marking = selectedMarking();
  return marking?.coefficients?.length === sectionModel.prototypeCount
    ? marking.coefficients : sectionModel.curve.at(-1).coefficients;
}

function markingAcceptanceThreshold(marking = selectedMarking()) {
  const representation = marking?.config.representation || sectionModel?.representation || "sites";
  const base = { sites: -.24, ports: -.14, whole: -.30 }[representation] ?? -.24;
  const channels = marking?.config.channels || sectionModel?.channels || 1;
  return base - Math.min(.06, Math.log2(Math.max(1, channels)) * .012);
}

function ruleMarkingDecision(rule) {
  const active = selectedMarking();
  const library = markingSearchMode === "portfolio" ? compatibleMarkings() : active ? [active] : [];
  const rows = library.map((marking) => ({
    id: marking.id,
    name: marking.name,
    score: ruleMarkingScore(rule, marking.coefficients,
      marking.config.representation, marking.representationState),
    threshold: markingAcceptanceThreshold(marking),
  }));
  if (!rows.length) {
    const score = ruleMarkingScore(rule, searchSectionCoefficients(),
      sectionModel.representation, sectionModel.representationState);
    rows.push({ id: "current", name: "current marking", score,
      threshold: markingAcceptanceThreshold() });
  }
  const strongest = rows.slice().sort((first, second) => second.score - first.score
    || first.id.localeCompare(second.id))[0];
  return { rows, score: strongest.score, source: strongest.id,
    accepted: rows.some((row) => row.score > row.threshold) };
}

function sectionLossForCluster(cluster) {
  const coefficients = currentSectionCoefficients(cluster);
  const indices = sectionModel.sampleLabels.map((label, index) => label === cluster ? index : -1).filter((index) => index >= 0);
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
  markingCache = new Map(overlapGrammar.rules.map((rule) => {
    const score = ruleMarkingDecision(rule).score;
    return [`r${rule.id}:C${rule.from + 1}>C${rule.to + 1}`, {
      count: rule.count, min: score - finalPoint.validationLoss, max: score + finalPoint.validationLoss, sum: score * rule.count,
    }];
  }));
}

function sectionValue(cluster, localDirection,
  coefficients = pipelineStage === 4 ? searchSectionCoefficients() : currentSectionPoint().coefficients,
  exponent = sectionModel.exponent) {
  return sectionModel.axes.reduce((sum, axis, index) =>
    sum + coefficients[cluster][index] * Math.max(0, localDirection.dot(axis)) ** exponent, 0);
}

function ruleMarkingScore(rule,
  coefficients = pipelineStage === 4 ? searchSectionCoefficients() : currentSectionPoint().coefficients,
  representationName = sectionModel.representation,
  representationState = sectionModel.representationState) {
  const representation = MARKING_REPRESENTATIONS[representationName] || MARKING_REPRESENTATIONS.sites;
  const forward = rule.translation.clone().normalize();
  const reverse = rule.translation.clone().negate().normalize().applyQuaternion(rule.rotation.clone().invert());
  const first = sectionValue(rule.from, forward, coefficients, representation.exponent);
  const second = sectionValue(rule.to, reverse, coefficients, representation.exponent);
  const inverseRotation = rule.rotation.clone().invert();
  const siteValues = ruleColoredSiteGeometry(rule).flatMap((site) => {
    if (site.parentVector.lengthSq() <= 1e-10) return [];
    const parentValue = sectionValue(rule.from, site.parentVector.clone().normalize(), coefficients, representation.exponent);
    const childToParent = site.parentVector.clone().negate().applyQuaternion(inverseRotation).normalize();
    const childValue = sectionValue(rule.to, childToParent, coefficients, representation.exponent);
    return [.5 * (parentValue + childValue) - Math.abs(parentValue - childValue)];
  });
  const chirality = ruleColoredChirality(rule);
  const preference = representationState?.chiralPreferences?.[`${rule.from}>${rule.to}`];
  const chiralityAffinity = preference?.observations
    ? 1 - Math.min(2, Math.abs(chirality - preference.mean)) : 0;
  return aggregateMarkingReadout({
    representation: representationName,
    forward: first,
    reverse: second,
    siteValues,
    chiralityAffinity,
  });
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

function learnReferenceDistanceEnvelopes(source) {
  const context = scenePeriodicContext();
  return learnColoredDistanceEnvelopes(source.map((atom) => atom.species),
    (first, second) => scenePeriodicDisplacement(source[first].p, source[second].p, context).length(), {
      fallbackExclusion: COLLISION_TOLERANCE,
    });
}

function learnReferenceCoordinationEnvelopes(source) {
  const context = scenePeriodicContext();
  return learnColoredCoordinationEnvelopes(source.map((atom) => atom.species),
    (first, second) => scenePeriodicDisplacement(source[first].p, source[second].p, context).length(),
    coloredDistanceEnvelopes);
}

function learnReferenceAngularEnvelopes(source) {
  const context = scenePeriodicContext();
  return learnColoredAngularEnvelopes(source.map((atom) => atom.species),
    (first, second) => scenePeriodicDisplacement(source[first].p, source[second].p, context),
    coloredCoordinationEnvelopes);
}

function coloredPairExclusion(firstSpecies, secondSpecies) {
  return exclusionForPair(coloredDistanceEnvelopes, firstSpecies, secondSpecies);
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
    const marking = ruleMarkingDecision(rule);
    frontierCandidates.push({ key, parentId: placement.id, rule, type: rule.to, position, rotation,
      occurrenceIndex: rule.reconstructionOnly ? rule.occurrenceTo : null,
      markingScore: marking.score, markingAccepted: marking.accepted,
      markingSource: marking.source, markingScores: marking.rows,
      priority: (policySelect.value === "marked" ? marking.score : 0) + Math.log1p(rule.count) * .09 + rule.meanShared * .035 + random() * .025 });
    frontierCandidateKeys.add(key);
  });
}

function dynamicCandidatePriority(candidate) {
  const parent = placedClusters.find((placement) => placement.id === candidate.parentId);
  return candidate.priority - candidate.position.length() * .055
    - sectorCounts[frontierSector(candidate.position)] * .11
    - (parent?.depth || 0) * .008;
}

function activeGeometricStrainWeight() {
  return geometryPreference === "strain" ? geometricStrainWeight : 0;
}

function activeCompositionBalanceWeight() {
  return compositionPreference === "strong" ? .70 : compositionPreference === "soft" ? .35 : 0;
}

function activeSurfaceCompletionWeight() {
  return surfacePreference === "strong" ? .36 : surfacePreference === "soft" ? .18 : 0;
}

function capturePolicyComparison(entries) {
  const admissible = entries.filter((entry) => entry.evaluation.accepted);
  const policies = [
    { id: "grammar", label: "mark + recurrence", score: (entry) => entry.baseScore },
    { id: "elastic", label: "elastic 0.16", score: (entry) => entry.baseScore - .16 * entry.evaluation.geometricStrain.total },
    { id: "composition", label: "composition 0.35", score: (entry) => entry.baseScore - .35 * entry.evaluation.compositionBalance.scaledDelta },
    { id: "surface", label: "surface 0.18", score: (entry) => entry.baseScore - .18 * entry.evaluation.surfaceCompletion.scaledDelta },
    { id: "active", label: "active combined", score: (entry) => entry.score },
  ].map((policy) => {
    const ranked = admissible.map((entry) => ({ entry, score: policy.score(entry) }))
      .sort((first, second) => second.score - first.score || first.entry.candidate.key.localeCompare(second.entry.candidate.key));
    const winner = ranked[0];
    return {
      id: policy.id,
      label: policy.label,
      action: winner ? `C${winner.entry.candidate.rule.from + 1}→C${winner.entry.candidate.rule.to + 1} · R${winner.entry.candidate.rule.id}` : "no admitted action",
      candidateKey: winner?.entry.candidate.key || null,
      score: winner?.score ?? null,
    };
  });
  lastPolicyComparison = {
    frontier: entries.length,
    admissible: admissible.length,
    referenceGuided: !reconstructionCertified,
    uniqueTopActions: new Set(policies.map((policy) => policy.candidateKey).filter(Boolean)).size,
    policies,
  };
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
    if (distance >= coloredPairExclusion(first.species, second.species)) continue;
    if (first.species === second.species && distance <= COMMUTING_SITE_TOLERANCE) continue;
    return false;
  }
  return true;
}

function uniqueFreshSites(freshSites) {
  const unique = [];
  freshSites.forEach((site) => {
    if (!unique.some((other) => other.species === site.species
      && other.p.distanceTo(site.p) <= COMMUTING_SITE_TOLERANCE)) unique.push(site);
  });
  return unique;
}

function constraintProjectionForFreshSites(rawFreshSites) {
  const freshSites = uniqueFreshSites(rawFreshSites);
  if (!freshSites.length || !coloredCoordinationEnvelopes) return {
    freshSites, projected: [], affectedIndices: [], affectedExistingIndices: [], freshIndices: [], existingCount: 0,
  };
  const reach = coloredCoordinationEnvelopes.maximumCutoff;
  const affectedExisting = new Set();
  freshSites.forEach((site) => nearbyAtoms(site.p, reach).forEach((atom) => {
    const envelope = coordinationEnvelopeFor(coloredCoordinationEnvelopes, atom.species, site.species);
    if (envelope && atom.p.distanceTo(site.p) <= envelope.contactCutoff) affectedExisting.add(atom);
  }));
  const centers = [...affectedExisting, ...freshSites];
  const localExisting = new Set(affectedExisting);
  centers.forEach((center) => nearbyAtoms(center.p, reach).forEach((atom) => {
    if (atom === center) return;
    const envelope = coordinationEnvelopeFor(coloredCoordinationEnvelopes, center.species, atom.species);
    if (envelope && center.p.distanceTo(atom.p) <= envelope.contactCutoff) localExisting.add(atom);
  }));
  const existing = [...localExisting];
  const projected = [...existing, ...freshSites];
  const existingIndex = new Map(existing.map((atom, index) => [atom, index]));
  const affectedExistingIndices = [...affectedExisting].map((atom) => existingIndex.get(atom));
  const freshIndices = freshSites.map((_, index) => existing.length + index);
  const affectedIndices = affectedExistingIndices.concat(freshIndices);
  constraintNeighborhoodEvaluations++;
  constraintNeighborhoodSiteTotal += projected.length;
  maximumConstraintNeighborhoodSites = Math.max(maximumConstraintNeighborhoodSites, projected.length);
  return { freshSites, projected, affectedIndices, affectedExistingIndices, freshIndices, existingCount: existing.length };
}

function coordinationOverflowsForFreshSites(rawFreshSites, projection = constraintProjectionForFreshSites(rawFreshSites)) {
  const { projected, affectedIndices } = projection;
  if (!affectedIndices.length) return [];
  const overflows = [];
  affectedIndices.forEach((centerIndex) => {
    const center = projected[centerIndex];
    coloredCoordinationEnvelopes.records.filter((record) => record.centerSpecies === center.species)
      .forEach((envelope) => {
        const count = projected.reduce((total, neighbor, neighborIndex) => {
          if (neighborIndex === centerIndex || neighbor.species !== envelope.neighborSpecies) return total;
          return total + (center.p.distanceTo(neighbor.p) <= envelope.contactCutoff ? 1 : 0);
        }, 0);
        if (count > envelope.maximumObserved) overflows.push({
          centerSpecies: center.species,
          neighborSpecies: envelope.neighborSpecies,
          count,
          maximum: envelope.maximumObserved,
        });
      });
  });
  return overflows;
}

function angularViolationsForFreshSites(rawFreshSites, projection = constraintProjectionForFreshSites(rawFreshSites)) {
  const { projected, affectedIndices } = projection;
  if (!affectedIndices.length || !coloredAngularEnvelopes) return [];
  return coloredAngularViolations(projected.map((site) => site.species),
    (first, second) => projected[second].p.clone().sub(projected[first].p),
    coloredCoordinationEnvelopes, coloredAngularEnvelopes, affectedIndices);
}

function geometricStrainForFreshSites(rawFreshSites, projection = constraintProjectionForFreshSites(rawFreshSites)) {
  const { projected, affectedIndices } = projection;
  if (!affectedIndices.length || !coloredAngularEnvelopes) return {
    total: 0, distance: 0, angle: 0, contactTerms: 0, angleTerms: 0,
  };
  return coloredGeometricStrain(projected.map((site) => site.species),
    (first, second) => projected[second].p.clone().sub(projected[first].p),
    coloredDistanceEnvelopes, coloredCoordinationEnvelopes, coloredAngularEnvelopes, affectedIndices);
}

function surfaceCompletionForFreshSites(rawFreshSites,
  projection = constraintProjectionForFreshSites(rawFreshSites)) {
  const { projected, affectedExistingIndices, freshIndices, existingCount } = projection;
  if (!freshIndices.length) return {
    beforeExisting: 0, afterExisting: 0, newSiteDeficit: 0,
    healedExisting: 0, scaledDelta: 0, terms: 0,
  };
  const existing = projected.slice(0, existingCount);
  const before = coloredCoordinationDeficit(existing.map((site) => site.species),
    (first, second) => existing[first].p.distanceTo(existing[second].p),
    coloredCoordinationEnvelopes, affectedExistingIndices);
  const afterExisting = coloredCoordinationDeficit(projected.map((site) => site.species),
    (first, second) => projected[first].p.distanceTo(projected[second].p),
    coloredCoordinationEnvelopes, affectedExistingIndices);
  const newSites = coloredCoordinationDeficit(projected.map((site) => site.species),
    (first, second) => projected[first].p.distanceTo(projected[second].p),
    coloredCoordinationEnvelopes, freshIndices);
  const healedExisting = before.mean - afterExisting.mean;
  return {
    beforeExisting: before.mean,
    afterExisting: afterExisting.mean,
    newSiteDeficit: newSites.mean,
    healedExisting,
    scaledDelta: .60 * newSites.mean - .40 * healedExisting,
    terms: afterExisting.terms + newSites.terms,
  };
}

function compositionBalanceForFreshSites(rawFreshSites) {
  const freshSites = uniqueFreshSites(rawFreshSites);
  if (!compositionTarget || !freshSites.length) return {
    before: 0, after: 0, delta: 0, scaledDelta: 0, maximumFractionError: 0,
    projectedFractions: {}, added: 0,
  };
  return compositionBalanceDelta(atoms.map((atom) => atom.species),
    freshSites.map((site) => site.species), compositionTarget);
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
  const markingRejected = policySelect.value === "marked" && !candidate.markingAccepted;
  return evaluation.conflicts > 0 || evaluation.boundaryFailures > 0
    || evaluation.coordinationOverflows?.length > 0 || evaluation.angularViolations?.length > 0
    || evaluation.fresh.length === 0 || markingRejected;
}

function commutingFrontierBatch() {
  const audit = reconstructionCertified
    ? { matched: referenceCount(), missing: 0, duplicateAtoms: 0, extraneousAtoms: 0 }
    : referenceCoverageAudit();
  // Candidate enumeration is frozen before this ranking. Geometric strain is
  // a target-blind preference among those exact actions, never an admission
  // rule and never a source of new coordinates.
  const evaluated = frontierCandidates.map((candidate) => {
    const evaluation = evaluateCandidate(candidate);
    const baseScore = dynamicCandidatePriority(candidate) + 2.5 * candidateReferenceGain(candidate, audit);
    return {
      candidate,
      evaluation,
      sites: evaluation.sites,
      baseScore,
      score: baseScore
        - activeGeometricStrainWeight() * evaluation.geometricStrain.total
        - activeCompositionBalanceWeight() * evaluation.compositionBalance.scaledDelta
        - activeSurfaceCompletionWeight() * evaluation.surfaceCompletion.scaledDelta,
    };
  });
  capturePolicyComparison(evaluated);
  const ranked = evaluated.sort((first, second) => second.score - first.score || first.candidate.key.localeCompare(second.candidate.key));
  if (overlapGrammar.molecular && !reconstructionCertified) {
    const ordered = ranked.slice().sort((first, second) => first.candidate.rule.replayOrder - second.candidate.rule.replayOrder);
    for (const entry of ordered) {
      if (entry.evaluation.accepted || rejectionIsOrderInvariant(entry.candidate, entry.evaluation)) {
        return [entry];
      }
    }
    return [];
  }
  if (growthScheduling === "serial") {
    const selected = ranked.find((entry) => entry.evaluation.accepted
      || rejectionIsOrderInvariant(entry.candidate, entry.evaluation));
    return selected ? [selected] : [];
  }
  const acceptedBatch = [];
  const rejectedBatch = [];
  for (const entry of ranked) {
    const { candidate, evaluation } = entry;
    if (evaluation.accepted) {
      if (!acceptedBatch.every((other) => sitesCanCommute(entry.sites, other.sites))) continue;
      const trial = [...acceptedBatch, entry];
      const trialFresh = uniqueFreshSites(trial.flatMap((trialEntry) => trialEntry.evaluation.fresh));
      const trialProjection = constraintProjectionForFreshSites(trialFresh);
      if (coordinationOverflowsForFreshSites(trialFresh, trialProjection).length
        || angularViolationsForFreshSites(trialFresh, trialProjection).length) continue;
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
    const neighborhood = nearbyAtoms(site.p, coloredDistanceEnvelopes?.maximumExclusion || COLLISION_TOLERANCE)
      .sort((first, second) => first.p.distanceToSquared(site.p) - second.p.distanceToSquared(site.p));
    const same = neighborhood.find((atom) => atom.species === site.species && atom.p.distanceTo(site.p) <= MERGE_TOLERANCE);
    if (same) merged.push({ site, atom: same });
    else if (neighborhood.some((atom) => atom.p.distanceTo(site.p) < coloredPairExclusion(site.species, atom.species))) conflicts++;
    else if (!insideGrowthDomain(site.p)) boundaryFailures++;
    else fresh.push(site);
  });
  const markingAccepted = policySelect.value !== "marked" || candidate.markingAccepted;
  const knownFailures = reconstructing ? canonical.failures : 0;
  const markingFallback = reconstructing && knownFailures === 0 && !markingAccepted;
  const constraintProjection = constraintProjectionForFreshSites(fresh);
  const coordinationOverflows = reconstructing ? [] : coordinationOverflowsForFreshSites(fresh, constraintProjection);
  const angularViolations = reconstructing ? [] : angularViolationsForFreshSites(fresh, constraintProjection);
  const geometricStrain = geometricStrainForFreshSites(fresh, constraintProjection);
  const surfaceCompletion = surfaceCompletionForFreshSites(fresh, constraintProjection);
  const compositionBalance = compositionBalanceForFreshSites(fresh);
  const accepted = conflicts === 0 && boundaryFailures === 0 && merged.length >= 2
    && fresh.length > 0 && knownFailures === 0 && coordinationOverflows.length === 0
    && angularViolations.length === 0 && (markingAccepted || markingFallback);
  return { accepted, sites, merged, fresh, conflicts, boundaryFailures, knownFailures, markingFallback,
    coordinationOverflows, angularViolations, geometricStrain, surfaceCompletion, compositionBalance,
    duplicateSites: canonical.duplicateSites,
    freshReferenceIndices: fresh.map((site) => site.referenceIndex).filter(Number.isInteger),
    reason: conflicts ? `${conflicts} hard-core/species conflicts` : boundaryFailures ? "outside confinement" : knownFailures ? `${knownFailures} sites outside known configuration` : coordinationOverflows.length ? `${coordinationOverflows.length} colored coordination capacities exceeded` : angularViolations.length ? `${angularViolations.length} colored angular envelopes violated` : merged.length < 2 ? "insufficient shared support" : fresh.length === 0 ? "duplicate covering" : !candidate.markingAccepted ? "marking mismatch" : "compatible overlap" };
}

function referenceCoverageCount() {
  return referenceCoverageAudit().matched;
}

function iceAnchorScenePoint(point) {
  const config = ICE_MOLECULAR_PORT_ARTIFACT.cases[scenarioSelect.value];
  const scale = .92 / currentMaterial().spacingA;
  return new THREE.Vector3(...point).sub(new THREE.Vector3(...config.boundaryCenter)).multiplyScalar(scale);
}

function initializeIceAnchorSearch() {
  iceAnchorTrace = executeIceMolecularAnchorGrowth(
    ICE_MOLECULAR_PORT_ARTIFACT, scenarioSelect.value);
  if (!iceAnchorTrace.exactBackendCountParity || iceAnchorTrace.targetUsed) {
    throw new Error("Frozen browser ice continuation diverged from its sealed backend certificate");
  }
  iceAnchorWaveIndex = 0;
  atoms = [];
  placedClusters = [];
  frontierCandidates = [];
  reconstructionCertified = true;
  iceAnchorTrace.seedSites.forEach(([species, point], index) => {
    const atom = addAtom(iceAnchorScenePoint(point), species, "ice-anchor", null, true);
    atom.anchorDomain = true;
    atom.clusterIds = [index + 1];
    indexAtom(atom);
  });
  growthStartAtomCount = atoms.length;
  replayIndex = 0;
  stackHistory = [{ type: "accept", depth: 0,
    action: `${iceAnchorTrace.seedAnchors} observed O anchors`, family: "sealed disjoint seed" }];
}

function initializeOffLatticeSearch() {
  atoms = [];
  placedClusters = [];
  frontierCandidates = [];
  frontierCandidateKeys = new Set();
  rejectedCandidateKeys = new Set();
  reconstructionCertified = false;
  reconstructionMarkingFallbacks = 0;
  coordinationCapacityPrunes = 0;
  angularEnvelopePrunes = 0;
  acceptedGeometricStrain = 0;
  rejectedGeometricStrain = 0;
  acceptedCompositionDelta = 0;
  rejectedCompositionDelta = 0;
  acceptedSurfaceDeficit = 0;
  rejectedSurfaceDeficit = 0;
  constraintNeighborhoodEvaluations = 0;
  constraintNeighborhoodSiteTotal = 0;
  maximumConstraintNeighborhoodSites = 0;
  lastPolicyComparison = null;
  atomSpatialIndex = new Map();
  const seedIndex = overlapGrammar.replaySeedIndex;
  const seedOccurrence = overlapGrammar.occurrences[seedIndex];
  const seedType = overlapGrammar.coverBased || overlapGrammar.molecular
    ? seedOccurrence.type : learnedClusters.labels[seedIndex];
  const seed = { id: 1, type: seedType, position: seedOccurrence.position.clone(), rotation: seedOccurrence.rotation.clone(), occurrenceIndex: seedIndex, parentId: null, ruleId: null, depth: 0, atomIds: [] };
  const inverseSeedFrame = seed.rotation.clone().invert();
  const seedSites = overlapGrammar.coverBased || overlapGrammar.molecular
    ? seedOccurrence.sites : [{ local: new THREE.Vector3(), species: referenceAtoms[seedIndex].species, center: true }];
  if (!overlapGrammar.coverBased && !overlapGrammar.molecular) learnedClusters.environments[seedIndex].shell.filter((neighbor) => neighbor.r <= motifShellCutoff()).forEach((neighbor) => seedSites.push({
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
  if (learnedCover?.occurrenceBased || learnedCover?.molecular) {
    markingPrototypeTypes().forEach((cluster, clusterIndex) => {
      const center = centers[clusterIndex];
      cluster.customVectors.forEach((vector, siteIndex) => reps.push({
        p: center.clone().add(vector),
        species: referenceAtoms[cluster.customSupport[siteIndex]].species,
        family: `C${clusterIndex + 1}`,
        symbolCenter: siteIndex === 0,
      }));
    });
    return reps;
  }
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
  const occurrenceBased = learnedCover?.occurrenceBased || learnedCover?.molecular;
  const count = occurrenceBased ? markingPrototypeTypes().length : learnedClusters?.clusters.length || 1;
  const spacing = occurrenceBased ? 5.2 : 3.15;
  return Array.from({ length: count }, (_, index) => new THREE.Vector3((index - (count - 1) / 2) * spacing, 0, 0));
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
  markingPrototypeTypes().forEach((_, cluster) => {
    const selectedKey = `m_${markingPrototypeName(cluster)}`;
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
    // Every occurrence-based support is already rendered as an independent
    // rotating polyhedral card. The legacy overlay below is atom-centred and
    // would turn molecular or irregular supports back into radial spokes.
    if (learnedCover?.occurrenceBased || learnedCover?.molecular) return;
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
    if (learnedCover?.occurrenceBased || learnedCover?.molecular) return;
    symbolCenters().forEach((center, index) => {
      const cluster = learnedClusters.clusters[index];
      const geometry = cluster.coordination <= 6 ? new THREE.OctahedronGeometry(1.22)
        : cluster.coordination >= 11 ? new THREE.IcosahedronGeometry(1.3, 0)
          : new THREE.SphereGeometry(1.25, 8, 5);
      addClusterEnvelope(geometry, center, clusterColor(index));
    });
  } else if (pipelineStage === 3 && sectionModel) {
    if (learnedCover?.occurrenceBased || learnedCover?.molecular) {
      buildSectionHalos();
      return;
    }
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
  const domain = { auto: "auto", lattice: "lattice", module: "module", offlattice: "SE(3)" }[config.geometryMode || "auto"];
  return `M${String(id).padStart(2, "0")} · ${domain} · ${channels} · R${config.reach} · ${representation}`;
}

function compatibleMarkings() {
  const key = markingMaterialKey();
  const vocabularyKey = markingVocabularyKey();
  return markingLibrary.filter((marking) => marking.materialKey === key
    && (marking.config.geometryMode || "auto") === geometryMode
    && marking.vocabularyKey === vocabularyKey
    && marking.coefficients.length === markingPrototypeTypes().length);
}

function freezeCurrentMarking() {
  if (!sectionModel) return null;
  const config = { channels: sectionModel.channels, channelMode: sectionModel.channelMode,
    reach: sectionModel.reach, representation: sectionModel.representation, geometryMode };
  const materialKey = markingMaterialKey();
  const vocabularyKey = markingVocabularyKey();
  let marking = markingLibrary.find((candidate) => candidate.materialKey === materialKey
    && candidate.vocabularyKey === vocabularyKey
    && candidate.config.channels === config.channels
    && (candidate.config.channelMode || "manual") === config.channelMode
    && candidate.config.reach === config.reach
    && (candidate.config.geometryMode || "auto") === config.geometryMode
    && candidate.config.representation === config.representation);
  if (!marking) {
    const serial = nextMarkingId++;
    marking = {
      id: `marking-${serial}`,
      name: markingName(config, serial),
      materialKey,
      materialName: currentMaterial().name,
      vocabularyKey,
      vocabularySummary: `${markingPrototypeTypes().length} cover types · ${resolvedGeometryLabel()} · ${reducedCompositionKey()}`,
      config,
      coefficients: sectionModel.curve.at(-1).coefficients.map((values) => [...values]),
      representationState: JSON.parse(JSON.stringify(sectionModel.representationState)),
      validationLoss: sectionModel.curve.at(-1).validationLoss,
      samples: markingSampleCount(),
    };
    markingLibrary.push(marking);
  } else {
    marking.coefficients = sectionModel.curve.at(-1).coefficients.map((values) => [...values]);
    marking.representationState = JSON.parse(JSON.stringify(sectionModel.representationState));
    marking.validationLoss = sectionModel.curve.at(-1).validationLoss;
    marking.samples = markingSampleCount();
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
  markingLibraryCount.textContent = `${compatible.length} compatible · ${markingLibrary.length} saved`;
}

function renderPoseAtlas() {
  poseAtlas.replaceChildren();
  const total = orientationAtlas.reduce((sum, entry) => sum + entry.orientations, 0);
  const freeTypes = orientationAtlas.filter((entry) => poseAtlasEntryStatus(entry) === "sampled continuum").length;
  const unresolvedTypes = orientationAtlas.filter((entry) => poseAtlasEntryStatus(entry) === "unresolved support").length;
  const supportSummary = freeTypes || unresolvedTypes
    ? `${total} observed poses${freeTypes ? ` · ${freeTypes} equivariant ${rotationGroupLabel()}` : ""}${unresolvedTypes ? ` · ${unresolvedTypes} unresolved` : ""}`
    : `${total} required poses`;
  poseAtlasTotal.textContent = `${supportSummary} · auto ${automaticMarkingChannels()}ch`;
  orientationAtlas.slice(0, 10).forEach((entry) => {
    const row = document.createElement("div");
    row.className = "pose-atlas-row";
    row.style.setProperty("--pose-color", `#${CLUSTER_COLORS[entry.cluster % CLUSTER_COLORS.length].toString(16).padStart(6, "0")}`);
    const code = document.createElement("code"); code.textContent = `C${entry.cluster + 1}`;
    const detail = document.createElement("span");
    const portRank = clusterPortRank(entry.cluster);
    const coupledRank = clusterPosePortRank(entry.cluster);
    const channels = recommendedChannelsForCluster(entry.cluster);
    detail.textContent = `${entry.element} · ${entry.occurrences} occurrences · ${portRank} port role${portRank === 1 ? "" : "s"} · coupled rank ${coupledRank}`;
    const count = document.createElement("b");
    const support = poseAtlasEntryStatus(entry);
    count.textContent = support === "finite required set"
      ? `${entry.orientations} required pose${entry.orientations === 1 ? "" : "s"} → ${channels}ch`
      : support === "sampled continuum"
        ? `${entry.orientations} sampled · equivariant ${rotationGroupLabel()} → ${channels}ch`
        : `${entry.orientations} observed · unresolved → ${channels}ch reserve`;
    row.append(code, detail, count);
    poseAtlas.appendChild(row);
  });
}

function renderMolecularHypothesis() {
  const audit = learnedCover?.molecularDiscovery;
  const panel = molecularHypothesisState.closest(".molecular-hypothesis-audit");
  panel.classList.remove("accepted", "rejected", "unavailable");
  if (!audit) {
    panel.classList.add("unavailable");
    molecularHypothesisState.textContent = "not evaluated";
    molecularHypothesisEvidence.textContent = "species + metric geometry only";
    molecularHypothesisRoute.textContent = "unknown";
    return;
  }
  const labels = audit.formulas.map((entry) => `${entry.occurrences}×${entry.formula.map(([element, count]) => `${element}${count === 1 ? "" : count}`).join("")}`);
  if (audit.accepted) {
    panel.classList.add("accepted");
    molecularHypothesisState.textContent = `${audit.components} recurrent finite component${audit.components === 1 ? "" : "s"}${labels.length ? ` · ${labels.join(" + ")}` : ""}`;
    molecularHypothesisEvidence.textContent = `${audit.covalentEdges} covalent edges · largest component ${audit.largestComponent} atoms · material/formula labels 0`;
    molecularHypothesisRoute.textContent = audit.route.includes("molecular") ? "molecular cover" : "irregular fallback";
    return;
  }
  const unavailable = audit.reason === "unsupported chemistry metadata";
  panel.classList.add(unavailable ? "unavailable" : "rejected");
  molecularHypothesisState.textContent = unavailable
    ? `not evaluated · missing ${audit.unsupportedElements.join(" / ") || "chemistry metadata"}`
    : `rejected · ${audit.reason}`;
  molecularHypothesisEvidence.textContent = unavailable
    ? "no element-specific rule was invented; geometry falls back safely"
    : `${audit.covalentEdges} candidate bonds · ${audit.components} component${audit.components === 1 ? "" : "s"} · largest ${audit.largestComponent} atoms`;
  molecularHypothesisRoute.textContent = "irregular cover";
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
    const periodicFixture = Boolean(currentMaterial().periodicWindow && currentCell() && currentPbc().some(Boolean));
    const resolvedMode = resolvedGeometryMode();
    geometryModeHint.textContent = geometryMode === "auto"
      ? resolvedMode === "lattice" ? latticeDetected ? "translation closure found" : periodicFixture ? "periodic cell supplied" : "intrinsic planar lattice"
        : resolvedMode === "module" ? "multiple incommensurate generators" : "no lattice closure"
      : geometryMode === "lattice" ? "periodic translation group"
      : geometryMode === "module" ? "finite-rank aperiodic support" : "unrestricted metric support";
    geometryModeNote.textContent = geometryMode === "auto"
      ? `${resolvedMode === "lattice" ? latticeDetected ? "A translation basis was inferred" : periodicFixture ? "The supplied periodic cell defines the translation quotient" : "A two-dimensional translation support was inferred" : resolvedMode === "module" ? "A finite-rank non-periodic support is the active hypothesis" : "No stable translation basis was inferred; the observed point set is retained without periodic wrapping"}; the pose classes still come only from the supplied positions.`
      : geometryMode === "lattice"
        ? "Periodic wrapping is applied before clustering; orientations are still quotiented by each cluster's proper symmetry."
        : geometryMode === "module"
          ? "No unit cell or periodic wrapping is assumed. Connections are learned from a discrete, finitely generated aperiodic pose/translation atlas—the natural hypothesis for model sets and quasicrystals."
          : `No discrete translation group is assumed. Candidate sites may come from an observed point set or a generator; ${rotationGroupLabel()} poses and connections are learned from local geometry.`;
    translationSupport.textContent = resolvedMode === "lattice"
      ? currentMaterial().intrinsicDimension === 2 ? "2 periodic generators" : "3 periodic generators"
      : resolvedMode === "module" ? "finite-rank module" : "metric point set";
    const totalPoses = orientationAtlas.reduce((sum, entry) => sum + entry.orientations, 0);
    const freeTypes = orientationAtlas.filter((entry) => poseAtlasEntryStatus(entry) === "sampled continuum").length;
    const unresolvedTypes = orientationAtlas.filter((entry) => poseAtlasEntryStatus(entry) === "unresolved support").length;
    rotationSupport.textContent = poseSupportLabel(totalPoses, freeTypes, unresolvedTypes);
    channelRankSupport.textContent = `${automaticMarkingChannels()} auto channel${automaticMarkingChannels() === 1 ? "" : "s"}`;
    renderMolecularHypothesis();
    renderPoseAtlas();
    stageOptionsState.textContent = resolvedMode === "module" ? "aperiodic module"
      : resolvedMode === "offlattice" ? `metric-set ${rotationGroupLabel()}` : "lattice candidate";
    return;
  }
  const resolvedChannels = sectionModel?.channels || currentMarkingConfig().channels;
  const inheritedDomain = resolvedGeometryLabel();
  const inheritedPoses = orientationAtlas.reduce((sum, entry) => sum + entry.orientations, 0);
  const inheritedFreeTypes = orientationAtlas.filter((entry) => poseAtlasEntryStatus(entry) === "sampled continuum").length;
  const inheritedUnresolvedTypes = orientationAtlas.filter((entry) => poseAtlasEntryStatus(entry) === "unresolved support").length;
  inheritedGeometryMode.textContent = inheritedDomain;
  inheritedPoseCount.textContent = poseSupportLabel(inheritedPoses, inheritedFreeTypes, inheritedUnresolvedTypes);
  inheritedChannelCount.textContent = `auto ${automaticMarkingChannels()}ch`;
  markingChannelsHint.textContent = markingDraft.channels
    ? `${markingDraft.channels} coupled field${markingDraft.channels === 1 ? "" : "s"}`
    : `auto → ${resolvedChannels} from pose/port rank`;
  markingReachHint.textContent = `${markingDraft.reach} shell${markingDraft.reach === 1 ? "" : "s"}`;
  markingRepresentationHint.textContent = MARKING_REPRESENTATIONS[markingDraft.representation].short;
  markingChannelsSelect.value = String(markingDraft.channels);
  markingReachSelect.value = String(markingDraft.reach);
  markingRepresentationSelect.value = markingDraft.representation;
  if (training) {
    const complete = trainingProgress >= markingSampleCount();
    const config = currentMarkingConfig();
    const existing = compatibleMarkings().some((marking) => marking.config.channels === config.channels
      && (marking.config.channelMode || "manual") === config.channelMode
      && marking.config.reach === config.reach && marking.config.representation === config.representation);
    stageOptionsState.textContent = complete ? existing ? "saved" : "fit complete" : `${trainingProgress}/${markingSampleCount()}`;
    saveMarkingButton.disabled = !complete;
    saveMarkingButton.textContent = existing ? "Update library copy" : "Freeze to library";
    markingConfigNote.textContent = `${resolvedChannels} channels${markingDraft.channels ? " (manual override)" : " (derived from the frozen pose × port incidence rank)"} · support R=${sectionModel?.support.toFixed(2) || "—"}a · ${MARKING_REPRESENTATIONS[markingDraft.representation].label}: ${MARKING_REPRESENTATIONS[markingDraft.representation].readout}. Clustering freezes the finite or sampled proper-rotation support before this fit; symmetry-equivalent rotations share channels.`;
  } else {
    renderMarkingLibrary();
    markingSearchModeSelect.value = markingSearchMode;
    const active = selectedMarking();
    const finiteIceAnchorMode = Boolean(iceAnchorTrace);
    geometryPreferenceSelect.value = geometryPreference;
    strainWeightSelect.value = String(geometricStrainWeight);
    compositionPreferenceSelect.value = compositionPreference;
    surfacePreferenceSelect.value = surfacePreference;
    growthSchedulingSelect.value = growthScheduling;
    geometryPreferenceSelect.disabled = finiteIceAnchorMode;
    strainWeightSelect.disabled = finiteIceAnchorMode || geometryPreference !== "strain";
    compositionPreferenceSelect.disabled = finiteIceAnchorMode;
    surfacePreferenceSelect.disabled = finiteIceAnchorMode;
    growthSchedulingSelect.disabled = finiteIceAnchorMode;
    growthSchedulingHint.textContent = growthScheduling === "commuting"
      ? "maximal commuting set" : "one branch decision";
    strainWeightHint.textContent = geometryPreference === "strain"
      ? `${geometricStrainWeight.toFixed(2)} soft` : "disabled";
    stageOptionsState.textContent = `${policySelect.value === "marked" && active ? active.name.split(" · ")[0] : "baseline"} · ${geometryPreference === "strain" ? `strain ${geometricStrainWeight.toFixed(2)}` : "no strain"}`;
    primitiveGrowthButton.classList.toggle("active", finiteIceAnchorMode || !hierarchyEnabled);
    primitiveGrowthButton.setAttribute("aria-pressed", String(finiteIceAnchorMode || !hierarchyEnabled));
    hierarchicalGrowthButton.classList.toggle("active", !finiteIceAnchorMode && hierarchyEnabled);
    hierarchicalGrowthButton.setAttribute("aria-pressed", String(!finiteIceAnchorMode && hierarchyEnabled));
    hierarchicalGrowthButton.disabled = finiteIceAnchorMode;
    primitiveGrowthButton.disabled = finiteIceAnchorMode;
    const markingUse = markingSearchMode === "portfolio"
      ? `The ${compatibleMarkings().length || 1}-mark compatible library scores each unchanged action; any trained mark may admit it.`
      : "The selected vocabulary-compatible marking ranks and prunes the unchanged candidate placements.";
    const strainUse = geometryPreference === "strain"
      ? ` A frozen sample-derived contact/angle strain adds a ${geometricStrainWeight.toFixed(2)} soft ordering term over that same candidate set.`
      : " Geometric strain is reported but contributes zero ranking weight for this ablation.";
    const ratio = Object.entries(compositionTarget.reducedRatio).map(([symbol, count]) => `${symbol}${count === 1 ? "" : count}`).join("");
    const compositionUse = compositionPreference === "none"
      ? " Composition drift is reported but contributes zero ranking weight."
      : ` A ${compositionPreference === "strong" ? "strong" : "balanced"} soft reservoir term favors the observed ${ratio} ratio without constraining an incomplete surface.`;
    const surfaceUse = surfacePreference === "none"
      ? " Coordination deficit is reported but contributes zero ranking weight."
      : ` A ${surfacePreference === "strong" ? "strong" : "balanced"} soft surface-completion term favors actions that heal observed coordination deficits without requiring a complete frontier shell.`;
    growthModeNote.textContent = finiteIceAnchorMode
      ? "This sealed ice gate executes primitive H₂O connection ports with mutually exclusive orientation domains. Clusters² is disabled because no stationary promoted ice production has been certified."
      : hierarchyEnabled
      ? `Accepted clusters expose frozen ports and may promote into clusters². ${growthScheduling === "commuting" ? "Each displayed update is a permutation-certified antichain over the underlying tree." : "Each displayed update executes one best-first tree branch."} ${markingUse}${strainUse}${compositionUse}${surfaceUse}`
      : `Primitive-only mode permits the seed frontier but prevents accepted clusters from spawning another recursive frontier. ${growthScheduling === "commuting" ? "Compatible placements may still be displayed as one permutation-certified antichain." : "Placements are executed one best-first branch at a time."} ${markingUse}${strainUse}${compositionUse}${surfaceUse}`;
  }
}

function resetCounters() {
  eventIndex = 0;
  oracleCalls = 0;
  grammarDecisions = 0;
  acceptedDecisions = 0;
  rejectedDecisions = 0;
  coordinationCapacityPrunes = 0;
  angularEnvelopePrunes = 0;
  acceptedGeometricStrain = 0;
  rejectedGeometricStrain = 0;
  acceptedCompositionDelta = 0;
  rejectedCompositionDelta = 0;
  acceptedSurfaceDeficit = 0;
  rejectedSurfaceDeficit = 0;
  constraintNeighborhoodEvaluations = 0;
  constraintNeighborhoodSiteTotal = 0;
  maximumConstraintNeighborhoodSites = 0;
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
  iceAnchorTrace = null;
  iceAnchorWaveIndex = 0;
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
  coloredDistanceEnvelopes = learnReferenceDistanceEnvelopes(referenceAtoms);
  coloredCoordinationEnvelopes = learnReferenceCoordinationEnvelopes(referenceAtoms);
  coloredAngularEnvelopes = learnReferenceAngularEnvelopes(referenceAtoms);
  compositionTarget = learnCompositionTarget(referenceAtoms.map((atom) => atom.species));
  referenceStructuralStats = calculateStructuralStats(referenceAtoms, referenceSpacing, currentPbc().some(Boolean),
    currentMaterial().intrinsicDimension === 2 ? 2 : 3);
  learnedClusters = learnLocalEnvironmentClusters(referenceAtoms);
  learnedCover = buildExhaustiveClusterCover(referenceAtoms);
  detectedUnitCell = geometryMode === "module" || geometryMode === "offlattice" ? null : inferTranslationCell(referenceAtoms);
  trainedMarking = learnOverlapMarking(referenceAtoms);
  overlapGrammar = learnOverlapGrammar(referenceAtoms);
  orientationAtlas = learnOrientationAtlas();
  const currentVocabularyKey = markingVocabularyKey();
  const compatibleActive = markingLibrary.find((marking) => marking.id === activeMarkingId
    && marking.materialKey === markingMaterialKey()
    && marking.vocabularyKey === currentVocabularyKey
    && marking.coefficients.length === markingPrototypeTypes().length);
  const growthMarking = compatibleActive || (pipelineStage === 4 ? compatibleMarkings().at(-1) : null);
  if (pipelineStage === 4 && growthMarking) {
    activeMarkingId = growthMarking.id;
    markingDraft = { ...growthMarking.config,
      channels: growthMarking.config.channelMode === "auto" ? 0 : growthMarking.config.channels };
  }
  sectionModel = learnSectionModel(referenceAtoms, currentMarkingConfig());
  if (pipelineStage !== 3) trainingProgress = markingSampleCount();
  if (pipelineStage === 4) {
    const compatible = compatibleMarkings();
    if (!compatible.length) freezeCurrentMarking();
  }
  if (pipelineStage >= 3 && policySelect.value === "marked") seedTrainedMarking();
  if (pipelineStage === 0 || pipelineStage === 1) atoms = referenceAtoms.map((atom) => cloneAtom(atom));
  else if (pipelineStage === 2) atoms = makeRepresentatives().map((atom) => cloneAtom(atom));
  else if (pipelineStage === 3) atoms = makeRepresentatives().map((atom) => cloneAtom(atom));
  else if (learnedCover.molecular?.water && currentMaterial().icePolytype) initializeIceAnchorSearch();
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
  const clusterCount = markingPrototypeTypes().length;
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
      values: [`${descriptorCutoff().toFixed(2)}a cutoff`, `${orientationAtlas.reduce((sum, entry) => sum + entry.orientations, 0)} pose classes`, `${learnedCover.placements.length} placements`, learnedCover.molecular ? `${learnedCover.molecular.molecules} molecules · ${learnedCover.molecular.connections} connections · ${learnedCover.molecular.voids} voids` : `${learnedCover.residualTypes.length} residual types`],
    },
    {
      eyebrow: "encoding · clusters of clusters", title: "Promote repeated overlaps into finite connection states", phase: `${overlapGrammar.rules.length} rules`,
      caption: `${overlapGrammar.observations.toLocaleString()} directed overlaps are registered in SE(3). Compressed recurrent rules drive continuation; frozen one-off residual edges preserve exact known-window replay.`, badge: "encode",
      decision: "Higher-order cluster states learned", copy: "A recurring parent/source connection is now a reusable cluster-of-clusters symbol. Its finite state transports across arbitrary rotations; separation is normalized before reuse at the next recursive scale.",
      values: [`${clusterCount} local types`, `${overlapGrammar.rules.length} connection states`, `${overlapGrammar.recurring} recurring`, `${overlapGrammar.heldoutSupported} held-out supported`],
    },
    {
      eyebrow: "training · recursive connection sections", title: "Freeze a bounded marking across hierarchy levels", phase: `loss ${trainingPoint.validationLoss.toFixed(3)}`,
      caption: `${trainingPoint.samples}/${markingSampleCount()} ${sectionModel.sampleKind}s processed · ${trainingPoint.overlaps.toLocaleString()} support overlaps · held-out mismatch ${trainingPoint.validationLoss.toFixed(3)}.`, badge: "train",
      decision: "Recursive marking training", copy: "Each local cluster begins with random directional ports. Observed higher-order connections shape the section; the resulting parent/source marking is frozen, rescaled, and evaluated on the next unseen cluster level.",
      values: [`fit ${sectionModel.channels}-channel m_C(x)`, `ball R=${sectionModel.support.toFixed(1)}a`, trainingPoint.validationLoss.toFixed(4), MARKING_REPRESENTATIONS[sectionModel.representation].label],
    },
    {
      eyebrow: "search · off-lattice recursive covering", title: "Let overlapping higher-order parents vote, then branch", phase: "seed cluster",
      caption: growthScheduling === "commuting"
        ? "Translated, rotated, and inflated parents continue past the known boundary. Each visual update is one maximal commuting frontier set: every displayed placement is valid in every permutation, while dependent residuals remain explicit tree branches."
        : "Translated, rotated, and inflated parents continue past the known boundary. Each visual update executes one best-first branch decision; the exact candidate geometry and dependency-ordered tree are unchanged.", badge: "search",
      decision: "Recursive consensus frontier initialized", copy: growthScheduling === "commuting"
        ? "The same frozen connection marking proposes the next scale. A frontier antichain is displayed together only after pairwise species and hard-core checks, plus a unique-new-support check for every accepted placement."
        : "The same frozen connection marking proposes the next scale. One best-first candidate is executed per update so branch order can be inspected directly.",
      values: ["parent + φ(source−parent)", policySelect.value === "marked" ? selectedMarking()?.name || "active marking" : policySelect.value === "direct" ? "exact local oracle" : "unmarked action", hierarchyEnabled ? "clusters² promotion" : "primitive clusters", "branch residual"],
    },
  ];
  if (learnedCover.molecular) {
    const water = learnedCover.molecular.water;
    narratives[1].eyebrow = "learning · molecular and gap cover";
    narratives[1].decision = "Molecular overlap cover computed";
    narratives[1].copy = water
      ? "Species-resolved bond geometry discovers one H₂O motif. Shared hydrogen-bond bridges and empty oxygen-ring boundaries are promoted to connection clusters, then the periodic window is audited atom by atom."
      : "Valence-bounded species geometry discovers recurrent finite molecules. A nearest-component graph supplies molecule-pair connections; locally shortest chordless cycles become explicit void boundaries without an expected formula or ring size.";
    narratives[1].caption = `${learnedCover.molecular.molecules} molecular placements cover every observed atom; ${learnedCover.molecular.connections} connection polyhedra and ${learnedCover.molecular.voids} void-boundary polygons fill the intermolecular grammar. The scrollable gallery shows all ${clusterGalleryTypes().length} colored metric-isometry classes as independent rotating scenes, with physical and connection edges—not radial coordination spokes.`;
    narratives[1].values = [
      `${learnedCover.molecular.moleculeClasses} molecule class${learnedCover.molecular.moleculeClasses === 1 ? "" : "es"}`,
      `${learnedCover.molecular.connectionClasses} connection classes`,
      `${learnedCover.molecular.voidClasses} void classes`,
      `${learnedCover.placements.length} occurrences`,
    ];
    narratives[2].title = "Register molecular bridges and gap-boundary ports";
    narratives[2].phase = `${overlapGrammar.reconstructionEdges} replay ports`;
    narratives[2].caption = `${overlapGrammar.reconstructionEdges} dependency-ordered molecular overlap ports connect a strict replay tree reaching ${overlapGrammar.replayReachable}/${referenceCount()} known sites.`;
    narratives[2].values = [
      `${learnedCover.molecular.moleculeClasses} molecule classes`,
      `${learnedCover.molecular.connectionClasses} connection classes`,
      `${learnedCover.molecular.voidClasses} void classes`,
      `${overlapGrammar.reconstructionEdges} replay ports`,
    ];
    if (water) {
      narratives[4].title = "Grow shared oxygen anchors; retain proton poses symbolically";
      narratives[4].phase = "sealed disjoint seed";
      narratives[4].decision = "Frozen molecular-port frontier initialized";
      narratives[4].copy = `A positions-and-species-only Ih training window learned ${ICE_MOLECULAR_PORT_ARTIFACT.ports.length} proper-SE(3) connection ports. The browser recomputes a disjoint ${scenarioSelect.value === "iceIc" ? "cubic-ice transfer" : "hexagonal-ice"} anchor frontier without target coordinates.`;
      narratives[4].caption = "Only oxygen anchors shared by mutually exclusive H₂O orientation hypotheses are displayed. Proton alternatives remain symbolic and parent-domain unanimity fails closed when the next connection is unsupported.";
      narratives[4].values = [
        `${ICE_MOLECULAR_PORT_ARTIFACT.ports.length} frozen ports`,
        `${iceAnchorTrace?.seedAnchors || 0} seed O anchors`,
        "target calls 0",
        "stationary claim false",
      ];
    }
  } else if (learnedCover.irregular) {
    narratives[1].eyebrow = "learning · exact irregular support cover";
    narratives[1].title = "Mine recurring colored point sets, then cover every atom";
    narratives[1].decision = "Center-free recurring-support cover computed";
    narratives[1].copy = "Atomic coordination shells and center-free bond-lens supports are candidate generators only. Translation- and proper-rotation-invariant colored metric plus chirality signatures define the actual support classes; connected uncovered regions become explicit gap terminals.";
    narratives[1].caption = `${learnedCover.covered}/${referenceCount()} atoms are represented by ${learnedCover.placements.length} support occurrences at ${(learnedCover.irregular.metricToleranceFraction * 100).toFixed(1)}% of the nearest-neighbour scale. The miner found ${learnedCover.irregular.recurringCoordinationClasses} recurring coordination classes and ${learnedCover.irregular.recurringCenterFreeClasses} recurring center-free candidates; ${learnedCover.irregular.selectedCenterFreeOccurrences} center-free occurrences were needed by the deterministic greedy complete cover and ${learnedCover.irregular.residualAtoms} atoms remain in explicit gap clusters.${learnedCover.irregular.disconnectedReplayComponents ? ` ${learnedCover.irregular.disconnectedReplayComponents} spatially separate cover components remain separate rather than receiving a nonlocal connector.` : ""}`;
    narratives[1].values = [
      `${learnedCover.irregular.recurringCoordinationClasses} coordination classes`,
      `${learnedCover.irregular.recurringCenterFreeClasses} center-free candidates`,
      `${learnedCover.irregular.selectedCenterFreeOccurrences} selected center-free`,
      `${learnedCover.residualTypes.length} gap classes · ${learnedCover.irregular.replayConnectorCount} local connectors`,
    ];
    narratives[2].title = "Register rigid ports between the exact support occurrences";
    narratives[2].phase = `${overlapGrammar.rules.length} frozen rules`;
    narratives[2].copy = "Every port maps one complete colored support to another by a proper rigid transform. Residual gaps participate in exact known-window replay but are not promoted into recurrent continuation rules.";
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
  strainValue.textContent = pipelineStage === 4
    ? geometryPreference === "strain" ? `enabled · weight ${geometricStrainWeight.toFixed(2)}` : "diagnostic only · weight 0"
    : "not ranked";
  compositionValue.textContent = pipelineStage === 4
    ? compositionPreference === "none" ? "diagnostic only · weight 0"
      : `${compositionPreference} reservoir · weight ${activeCompositionBalanceWeight().toFixed(2)}`
    : "not ranked";
  surfaceValue.textContent = pipelineStage === 4
    ? surfacePreference === "none" ? "diagnostic only · weight 0"
      : `${surfacePreference} completion · weight ${activeSurfaceCompletionWeight().toFixed(2)}`
    : "not ranked";
  renderConstraintLedger(null);
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
    boundaryFailures: evaluation.boundaryFailures,
    knownFailures: evaluation.knownFailures,
    coordinationOverflows: evaluation.coordinationOverflows?.length || 0,
    angularViolations: evaluation.angularViolations?.length || 0,
    markingAccepted: candidate.markingAccepted,
    freshSites: evaluation.fresh.length,
    geometricStrain: evaluation.geometricStrain,
    compositionBalance: evaluation.compositionBalance,
    surfaceCompletion: evaluation.surfaceCompletion,
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
    occurrenceIndex: overlapGrammar.coverBased || overlapGrammar.molecular ? candidate.occurrenceIndex : Number.isInteger(centerReferenceIndex)
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
      if (snapshotEvaluation.coordinationOverflows?.length) coordinationCapacityPrunes++;
      if (snapshotEvaluation.angularViolations?.length) angularEnvelopePrunes++;
      rejectedGeometricStrain += snapshotEvaluation.geometricStrain.total;
      rejectedCompositionDelta += snapshotEvaluation.compositionBalance.scaledDelta;
      rejectedSurfaceDeficit += snapshotEvaluation.surfaceCompletion.scaledDelta;
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
    acceptedGeometricStrain += evaluation.geometricStrain.total;
    acceptedCompositionDelta += evaluation.compositionBalance.scaledDelta;
    acceptedSurfaceDeficit += evaluation.surfaceCompletion.scaledDelta;
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
    : `${acceptedInBatch} ${growthScheduling === "commuting" ? "order-independent placements shown together" : "best-first branch placement"} (${freshInBatch} new atoms) · ${replayIndex}/${referenceCount()} known sites recovered`
      + `${reconstructionMarkingFallbacks ? ` · ${reconstructionMarkingFallbacks} marking false negatives bypassed by the replay certificate` : ""}`
      + `${rejectedInBatch ? ` · ${rejectedInBatch} invariant prunes flash red` : ""}.`;
  if (lastDecision) updateDecision(lastDecision);
  rebuildWorld();
  updateUI();
}

function performIceAnchorEvent() {
  const wave = iceAnchorTrace?.waves[iceAnchorWaveIndex];
  if (!wave) {
    growthStopReason = "Certified molecular anchor trace exhausted at its safe fixed point.";
    setPlaying(false);
    pipelineAuto = false;
    updatePipelineButtons();
    return;
  }
  // The material-growth viewport is atom-only for molecular ice. Candidate
  // identities and orientation domains remain in the textual/search trace;
  // accepted anchors appear directly as O atoms rather than halo glyphs.
  currentCandidates = [];
  iceAnchorWaveIndex++;
  eventIndex += wave.candidateAnchors;
  if (!wave.acceptedAnchors) {
    captionAction.textContent = `Safe fixed point after ${iceAnchorTrace.emittedAnchors.length} target-blind oxygen anchors. No parent orientation domain unanimously supports another site; unresolved proton poses are retained as alternatives, not drawn as simultaneous H atoms.`;
    decisionBadge.className = "badge neutral";
    decisionBadge.textContent = "fixed point";
    decisionTitle.textContent = "Unsupported molecular continuation stops safely";
    decisionCopy.textContent = "The frozen eight-port grammar has no unanimous next anchor. This finite certificate is not a stationary or exponential ice-growth rule.";
    actionValue.textContent = `wave ${wave.wave} · 0 accepted`;
    domainValue.textContent = `${wave.rejectedNonunanimousAnchors} non-unanimous anchors pruned`;
    energyValue.textContent = "target calls 0";
    strainValue.textContent = "not used by frozen ice trace";
    compositionValue.textContent = "not used by frozen ice trace";
    surfaceValue.textContent = "not used by frozen ice trace";
    resolverValue.textContent = "orientation-domain unanimity";
    appendHistory("reject", { type: "reject", depth: wave.wave,
      action: "safe fixed point", family: "no unanimous parent domain" });
    growthStopReason = "Frozen molecular-port grammar reached its certified finite fixed point.";
    setPlaying(false);
    pipelineAuto = false;
    updatePipelineButtons();
    rebuildWorld();
    updateUI();
    captionAction.textContent = `Safe fixed point after ${iceAnchorTrace.emittedAnchors.length} target-blind oxygen anchors. No parent orientation domain unanimously supports another site; unresolved proton poses are retained as alternatives, not drawn as simultaneous H atoms.`;
    return;
  }
  wave.emittedAnchors.forEach(([species, point]) => {
    const atom = addAtom(iceAnchorScenePoint(point), species, "ice-anchor", nearestParent(iceAnchorScenePoint(point)));
    atom.anchorDomain = true;
    indexAtom(atom);
  });
  acceptedDecisions += wave.acceptedAnchors;
  grammarDecisions += wave.acceptedAnchors;
  appendHistory("reuse", { type: "accept", depth: wave.wave,
    action: `${wave.acceptedAnchors} O anchors`,
    family: `${wave.retainedOrientationHypotheses} mutually exclusive H₂O poses retained` });
  captionAction.textContent = `Wave ${wave.wave}: ${wave.acceptedAnchors}/${wave.candidateAnchors} anchor candidates survive frozen proper-SE(3) ports and parent-domain unanimity. ${wave.retainedOrientationHypotheses} mutually exclusive H₂O orientation hypotheses remain symbolic; only their shared O atoms are displayed.`;
  updateDecision({ eventType: "reuse", accepted: true,
    state: { action: `${wave.acceptedAnchors} O-anchor placements`,
      domain: `8 frozen molecular ports · wave ${wave.wave}` },
    resolver: "orientation-domain unanimity", interval: [1, 1] });
  rebuildWorld();
  updateUI();
}

function advanceMarkingTraining(batchSize = 12) {
  trainingProgress = Math.min(markingSampleCount(), trainingProgress + batchSize);
  eventIndex = trainingProgress;
  buildClusterOverlay();
  rebuildWorld();
  updateUI();
}

function performEvent() {
  if (pipelineStage === 3) {
    if (trainingProgress < markingSampleCount()) advanceMarkingTraining();
    else enterPipelineStage(4, { play: pipelineAuto });
    return;
  }
  if (pipelineStage < 4) {
    enterPipelineStage(nextVisiblePipelineStage(pipelineStage), { play: pipelineAuto });
    return;
  }
  if (iceAnchorTrace) {
    performIceAnchorEvent();
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
    markingPrototypeTypes().forEach((_, cluster) => {
      const key = `m_${markingPrototypeName(cluster)}`;
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
      markingPrototypeTypes().forEach((_, cluster) => {
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
  const strain = event.state.geometricStrain;
  strainValue.textContent = strain
    ? `${strain.total.toFixed(3)} · r ${strain.distance.toFixed(3)} · θ ${strain.angle.toFixed(3)}`
    : "not evaluated";
  const balance = event.state.compositionBalance;
  compositionValue.textContent = balance
    ? `${balance.before.toFixed(3)} → ${balance.after.toFixed(3)} · Δ${balance.delta >= 0 ? "+" : ""}${balance.delta.toFixed(3)}`
    : "not evaluated";
  const surface = event.state.surfaceCompletion;
  surfaceValue.textContent = surface
    ? `new ${surface.newSiteDeficit.toFixed(3)} · healed ${surface.healedExisting.toFixed(3)} · Δ${surface.scaledDelta >= 0 ? "+" : ""}${surface.scaledDelta.toFixed(3)}`
    : "not evaluated";
  resolverValue.textContent = event.resolver;
  renderConstraintLedger(Number.isFinite(event.state.n15) ? event.state : null,
    Number.isFinite(event.state.n15) ? "configured" : "specialized");
  eventKind.textContent = reuse ? "MARK REUSE" : event.accepted ? "ACCEPT" : "REJECT";
}

function renderConstraintLedger(state, mode = "configured") {
  const ranked = (enabled) => enabled ? "ranked" : "diagnostic";
  const signed = (value) => `${value >= 0 ? "+" : ""}${value.toFixed(3)}`;
  const terms = state ? [
    { name: "species / hard core", status: state.clearance ? "fail" : "pass",
      value: state.clearance ? `${state.clearance} conflict${state.clearance === 1 ? "" : "s"}` : "pass",
      detail: "colored minimum-distance exclusion" },
    { name: "shared support", status: state.n15 >= 2 ? "pass" : "fail",
      value: `${state.n15} shared / ${state.freshSites} new`, detail: "whole-cluster overlap witness" },
    { name: "novel colored sites", status: state.freshSites > 0 ? "pass" : "fail",
      value: state.freshSites > 0 ? `${state.freshSites} emitted` : "duplicate covering",
      detail: "a tree action must extend the represented union" },
    { name: "public boundary", status: state.boundaryFailures || state.knownFailures ? "fail" : "pass",
      value: state.boundaryFailures ? `${state.boundaryFailures} outside domain`
        : state.knownFailures ? `${state.knownFailures} outside known window` : "pass",
      detail: "confinement or sealed replay domain" },
    { name: "coordination capacity", status: state.coordinationOverflows ? "fail" : "pass",
      value: state.coordinationOverflows ? `${state.coordinationOverflows} overflow${state.coordinationOverflows === 1 ? "" : "s"}` : "pass",
      detail: "species-resolved first-shell envelope" },
    { name: "angular envelope", status: state.angularViolations ? "fail" : "pass",
      value: state.angularViolations ? `${state.angularViolations} violation${state.angularViolations === 1 ? "" : "s"}` : "pass",
      detail: "colored bond-angle support" },
    { name: "elastic proxy", status: ranked(activeGeometricStrainWeight() > 0),
      value: state.geometricStrain ? state.geometricStrain.total.toFixed(3) : "not evaluated",
      detail: activeGeometricStrainWeight() > 0 ? `rank weight ${activeGeometricStrainWeight().toFixed(2)}` : "diagnostic · cannot authorize geometry" },
    { name: "composition reservoir", status: ranked(activeCompositionBalanceWeight() > 0),
      value: state.compositionBalance ? signed(state.compositionBalance.scaledDelta) : "not evaluated",
      detail: activeCompositionBalanceWeight() > 0 ? `rank weight ${activeCompositionBalanceWeight().toFixed(2)}` : "diagnostic · cannot authorize geometry" },
    { name: "surface completion", status: ranked(activeSurfaceCompletionWeight() > 0),
      value: state.surfaceCompletion ? signed(state.surfaceCompletion.scaledDelta) : "not evaluated",
      detail: activeSurfaceCompletionWeight() > 0 ? `rank weight ${activeSurfaceCompletionWeight().toFixed(2)}` : "diagnostic · cannot authorize geometry" },
    { name: "GCTS marking", status: policySelect.value === "marked" ? state.markingAccepted ? "pass" : "fail" : "diagnostic",
      value: policySelect.value === "marked" ? state.markingAccepted ? "compatible" : "mismatch" : "not gating",
      detail: "bounded transported connection section" },
  ] : mode === "specialized" ? [
    { name: "species / hard core", status: "pass", value: "backend-certified", detail: "frozen exact trace" },
    { name: "shared support", status: "pass", value: "frozen ports", detail: "proper-SE(3) molecular attachments" },
    { name: "novel colored sites", status: "pass", value: "exact anchors", detail: "one-to-one emitted-site certificate" },
    { name: "public boundary", status: "pass", value: "sealed", detail: "target calls 0 before scoring" },
    { name: "coordination capacity", status: "diagnostic", value: "not used", detail: "specialized frozen trace" },
    { name: "angular envelope", status: "diagnostic", value: "not used", detail: "specialized frozen trace" },
    { name: "elastic proxy", status: "diagnostic", value: "not used", detail: "cannot authorize this trace" },
    { name: "composition reservoir", status: "diagnostic", value: "not used", detail: "cannot authorize this trace" },
    { name: "surface completion", status: "diagnostic", value: "not used", detail: "cannot authorize this trace" },
    { name: "GCTS marking", status: "pass", value: "domain unanimity", detail: "all surviving H₂O poses agree" },
  ] : [
    { name: "species / hard core", status: "diagnostic", value: "armed", detail: "admission gate" },
    { name: "shared support", status: "diagnostic", value: "armed", detail: "admission gate" },
    { name: "novel colored sites", status: "diagnostic", value: "armed", detail: "admission gate" },
    { name: "public boundary", status: "diagnostic", value: "armed", detail: "admission gate" },
    { name: "coordination capacity", status: "diagnostic", value: "armed", detail: "admission gate" },
    { name: "angular envelope", status: "diagnostic", value: "armed", detail: "admission gate" },
    { name: "elastic proxy", status: ranked(activeGeometricStrainWeight() > 0),
      value: activeGeometricStrainWeight() > 0 ? "ranked" : "diagnostic", detail: `weight ${activeGeometricStrainWeight().toFixed(2)}` },
    { name: "composition reservoir", status: ranked(activeCompositionBalanceWeight() > 0),
      value: activeCompositionBalanceWeight() > 0 ? "ranked" : "diagnostic", detail: `weight ${activeCompositionBalanceWeight().toFixed(2)}` },
    { name: "surface completion", status: ranked(activeSurfaceCompletionWeight() > 0),
      value: activeSurfaceCompletionWeight() > 0 ? "ranked" : "diagnostic", detail: `weight ${activeSurfaceCompletionWeight().toFixed(2)}` },
    { name: "GCTS marking", status: policySelect.value === "marked" ? "ranked" : "diagnostic",
      value: policySelect.value === "marked" ? "active" : "not gating", detail: "bounded local section" },
  ];
  constraintLedger.replaceChildren(...terms.map((term) => {
    const row = document.createElement("article"); row.className = `constraint-term ${term.status}`;
    const label = document.createElement("small"); label.textContent = term.name;
    const value = document.createElement("strong"); value.textContent = term.value;
    const detail = document.createElement("span"); detail.textContent = term.detail;
    row.append(label, value, detail);
    return row;
  }));
}

function renderPolicyComparison() {
  policyComparison.replaceChildren();
  if (pipelineStage !== 4) {
    policyComparisonState.textContent = "available during growth";
    return;
  }
  if (iceAnchorTrace) {
    policyComparisonState.textContent = "specialized frozen trace";
    const row = document.createElement("article"); row.className = "active";
    const label = document.createElement("small"); label.textContent = "orientation domains";
    const action = document.createElement("strong"); action.textContent = "unanimous proper-SE(3) ports";
    const score = document.createElement("em"); score.textContent = "generic ranks unused";
    row.append(label, action, score); policyComparison.append(row);
    return;
  }
  if (!lastPolicyComparison) {
    policyComparisonState.textContent = "advance one update";
    const row = document.createElement("article");
    const label = document.createElement("small"); label.textContent = "pending";
    const action = document.createElement("strong"); action.textContent = `${frontierCandidates.length} frozen candidates await evaluation`;
    const score = document.createElement("em"); score.textContent = "same geometry";
    row.append(label, action, score); policyComparison.append(row);
    return;
  }
  const snapshot = lastPolicyComparison;
  policyComparisonState.textContent = `${snapshot.frontier} candidates · ${snapshot.admissible} admitted · ${snapshot.uniqueTopActions} winner${snapshot.uniqueTopActions === 1 ? "" : "s"}`
    + `${snapshot.referenceGuided ? " · target-aware replay" : " · target-blind frontier"}`;
  snapshot.policies.forEach((policy) => {
    const row = document.createElement("article"); row.classList.toggle("active", policy.id === "active");
    const label = document.createElement("small"); label.textContent = policy.label;
    const action = document.createElement("strong"); action.textContent = policy.action;
    const score = document.createElement("em"); score.textContent = policy.score === null ? "—" : policy.score.toFixed(3);
    row.append(label, action, score); policyComparison.append(row);
  });
}

function liveGrowthCertificate() {
  if (pipelineStage < 4) return null;
  const benchmark = RECURSIVE_BENCHMARKS[scenarioSelect.value] || RECURSIVE_BENCHMARKS.imported;
  if (iceAnchorTrace) {
    const processed = iceAnchorTrace.waves.slice(0, iceAnchorWaveIndex);
    const accepted = processed.reduce((sum, wave) => sum + wave.acceptedAnchors, 0);
    const nonemptyWaves = processed.filter((wave) => wave.acceptedAnchors > 0).length;
    const fixedPointReached = iceAnchorTrace.fixedPoint && iceAnchorWaveIndex >= iceAnchorTrace.waves.length;
    return {
      mode: "sealed molecular-anchor continuation",
      state: fixedPointReached ? "finite fixed point" : "target-blind execution",
      knownWindow: { status: "pass", title: `${iceAnchorTrace.seedAnchors} observed O anchors`,
        detail: "Seed only; the complete H₂O / bridge / O₆ cover was certified in cluster identification." },
      continuation: { status: iceAnchorTrace.exactBackendCountParity ? "pass" : "open",
        title: `${accepted} exact emitted O anchors`,
        detail: `${processed.reduce((sum, wave) => sum + wave.candidateAnchors, 0)} frozen candidates processed · target calls 0` },
      hierarchy: { status: nonemptyWaves >= 2 ? "progress" : "open",
        title: `${nonemptyWaves} nonempty self-fed wave${nonemptyWaves === 1 ? "" : "s"}`,
        detail: fixedPointReached ? "Grammar exhausted safely; no supported successor remains." : "Execution has not yet reached its certified endpoint." },
      claimBoundary: { status: "open", title: "O scaffold finite · proton / stationary open",
        detail: "Mutually exclusive H₂O orientations stay symbolic; no clusters² or exponential ice claim." },
      metrics: { seedSites: iceAnchorTrace.seedAnchors, emittedSites: accepted, processedWaves: processed.length,
        nonemptySelfFedWaves: nonemptyWaves, fixedPointReached, targetCalls: 0, exactBackendCountParity: iceAnchorTrace.exactBackendCountParity },
      benchmarkGate: benchmark.gate,
    };
  }
  const audit = referenceCoverageAudit();
  const generatedSites = atoms.filter((atom) => !Number.isInteger(atom.referenceIndex)).length;
  const maximumDepth = Math.max(0, ...placedClusters.map((placement) => placement.depth || 0));
  const fixedPointReached = reconstructionCertified && frontierCandidates.length === 0 && placedClusters.length > 0;
  const stationaryBenchmark = scenarioSelect.value === "competition" && benchmark.status === "pass";
  return {
    mode: "off-lattice covering search",
    state: fixedPointReached ? "finite fixed point" : reconstructionCertified ? "unseen continuation" : "known-window replay",
    knownWindow: { status: reconstructionCertified ? "pass" : "progress",
      title: `${audit.matched} / ${referenceCount()} known sites`,
      detail: `${audit.missing} missing · ${audit.duplicateAtoms} duplicates · ${audit.extraneousAtoms} extraneous during replay` },
    continuation: { status: generatedSites ? "progress" : "open", title: `${generatedSites} target-blind structural sites`,
      detail: generatedSites ? "Outside the supplied window; geometrically certified but not labeled physically correct." : "No outside-window site has been committed yet." },
    hierarchy: { status: maximumDepth >= 2 ? "progress" : "open",
      title: `${placedClusters.length} placements · causal depth ${maximumDepth}`,
      detail: hierarchyEnabled ? "Accepted clusters may expose frozen ports and self-feed." : "Primitive-only mode deliberately prevents recursive self-feed." },
    claimBoundary: { status: stationaryBenchmark ? "progress" : "open",
      title: stationaryBenchmark ? "Live finite trace · stationary benchmark separate" : "Finite structural continuation only",
      detail: stationaryBenchmark
        ? "NaCl recurrence is independently certified, but this viewport trace is not itself a physical-time trajectory."
        : "No potential, elapsed physical time, growth rate, or stationary/exponential rule is inferred from this animation." },
    metrics: { knownMatchedSites: audit.matched, knownInputSites: referenceCount(), exactKnownWindowReplay: reconstructionCertified,
      generatedStructuralSites: generatedSites, placedClusters: placedClusters.length, maximumCausalDepth: maximumDepth,
      fixedPointReached, targetCoordinatesUsed: false, physicalPotentialUsed: false },
    benchmarkGate: benchmark.gate,
  };
}

function updateGrowthCertificate() {
  const certificate = liveGrowthCertificate();
  growthCertificateSection.hidden = !certificate;
  if (!certificate) return;
  growthCertificateState.textContent = certificate.state;
  const fill = (element, record) => {
    element.className = record.status;
    element.querySelector("strong").textContent = record.title;
    element.querySelector("span").textContent = record.detail;
  };
  fill(certificateReplay, certificate.knownWindow);
  fill(certificateContinuation, certificate.continuation);
  fill(certificateHierarchy, certificate.hierarchy);
  fill(certificateBoundary, certificate.claimBoundary);
  growthCertificateNote.textContent = `${certificate.mode} · benchmark gate: ${certificate.benchmarkGate}`;
}

function updateUI() {
  updateRecursiveBenchmark();
  updateGrowthCertificate();
  renderPolicyComparison();
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
    const gapTypes = learnedCover.molecular ? learnedCover.molecular.voidClasses : learnedCover.residualTypes.length;
    reuseLabel.textContent = "GAP TYPES"; reuseMetric.textContent = String(gapTypes); reuseDelta.textContent = learnedCover.molecular
      ? `${learnedCover.molecular.voids} ${learnedCover.molecular.water ? "oxygen-ring" : "molecular void"} boundaries`
      : learnedCover.residualTypes.length ? "promoted to explicit clusters" : "none after overlap cover";
  } else if (pipelineStage === 2) {
    const occurrenceBased = learnedCover.occurrenceBased || learnedCover.molecular;
    atomLabel.textContent = "SYMBOLS"; atomMetric.textContent = String(occurrenceBased ? learnedCover.types.length : learnedClusters.clusters.length); atomDelta.textContent = learnedCover.molecular ? "molecule · bridge · ring boundary" : occurrenceBased ? "exact support and gap types" : "one per learned medoid";
    frontierLabel.textContent = "SE(3) RULES"; frontierMetric.textContent = String(overlapGrammar.rules.length); frontierDelta.textContent = "arbitrary quaternion + translation";
    oracleLabel.textContent = "PAIR OBSERVATIONS"; oracleMetric.textContent = overlapGrammar.observations.toLocaleString(); oracleDelta.textContent = `${overlapGrammar.recurring} rules recur`;
    const replayDenominator = overlapGrammar.coverBased ? overlapGrammar.occurrences.length : referenceCount();
    reuseLabel.textContent = "REPLAY GRAPH"; reuseMetric.textContent = `${overlapGrammar.replayReachable}/${replayDenominator}`; reuseDelta.textContent = `${overlapGrammar.reconstructionEdges.toLocaleString()} frozen observed edges · ${overlapGrammar.coverBased ? "occurrences" : "atoms"} · removed after certificate`;
  } else if (pipelineStage === 3) {
    const point = currentTrainingPoint();
    stageEyebrow.textContent = "training · recursive sections on cluster connections";
    stageTitle.textContent = trainingProgress < markingSampleCount() ? "Connection markings emerge on higher-order cluster states" : "Recursive GCTS marking frozen for transfer";
    decisionTitle.textContent = trainingProgress < markingSampleCount() ? "Fitting parent/source overlap consistency" : "Marked connections ready to rescale";
    decisionCopy.textContent = trainingProgress < markingSampleCount()
      ? "The local prototypes stay fixed while their connection sections morph. Type-colored lobes mark recurring parent/source overlaps; red lobes mark absent or failed connections. Their frames rotate with each placement; no physical potential is used."
      : "The learned connection sections now travel with higher-order cluster types and normalize their separation by recursive scale. Search rejects or branches when transported markings disagree.";
    phaseReadout.textContent = `loss ${point.validationLoss.toFixed(3)}`;
    captionAction.textContent = `${point.samples}/${markingSampleCount()} ${sectionModel.sampleKind}s · ${point.overlaps.toLocaleString()} support overlaps · fit ${point.trainLoss.toFixed(3)} · holdout ${point.validationLoss.toFixed(3)}.`;
    atomLabel.textContent = "SECTION SAMPLES"; atomMetric.textContent = `${point.samples}/${markingSampleCount()}`; atomDelta.textContent = `${point.fitSamples} fit · ${point.holdoutSamples} held out`;
    frontierLabel.textContent = "SUPPORT OVERLAPS"; frontierMetric.textContent = point.overlaps.toLocaleString(); frontierDelta.textContent = "section agreement constraints";
    oracleLabel.textContent = "FIT MISMATCH"; oracleMetric.textContent = point.trainLoss.toFixed(3); oracleDelta.textContent = "overlap + connection ports";
    reuseLabel.textContent = "HOLDOUT MISMATCH"; reuseMetric.textContent = point.validationLoss.toFixed(3); reuseDelta.textContent = "unseen local sections";
    actionValue.textContent = "fit m_C(x)";
    domainValue.textContent = `ball R=${sectionModel.support.toFixed(1)}a`;
    energyValue.textContent = point.validationLoss.toFixed(4);
    resolverValue.textContent = `${sectionModel.channels}ch · ${MARKING_REPRESENTATIONS[sectionModel.representation].short}`;
  } else {
    if (iceAnchorTrace) {
      const nextWave = iceAnchorTrace.waves[iceAnchorWaveIndex];
      const emitted = atoms.length - iceAnchorTrace.seedAnchors;
      stageEyebrow.textContent = "search · sealed molecular-port continuation";
      stageTitle.textContent = "Grow shared oxygen anchors; retain proton poses symbolically";
      phaseReadout.textContent = nextWave
        ? `wave ${nextWave.wave} · ${nextWave.candidateAnchors} candidates`
        : iceAnchorTrace.fixedPoint ? "safe finite fixed point" : "trace exhausted";
      atomLabel.textContent = "OXYGEN ANCHORS";
      atomMetric.textContent = atoms.length.toLocaleString();
      atomDelta.textContent = `${iceAnchorTrace.seedAnchors} observed seed · ${emitted} emitted`;
      frontierLabel.textContent = "NEXT ANCHOR WAVE";
      frontierMetric.textContent = nextWave ? String(nextWave.candidateAnchors) : "0";
      frontierDelta.textContent = "same frozen candidate set before scoring";
      oracleLabel.textContent = "TARGET CALLS";
      oracleMetric.textContent = "0";
      oracleDelta.textContent = "grammar + execution remain target-blind";
      reuseLabel.textContent = "CERTIFICATE";
      reuseMetric.textContent = iceAnchorTrace.exactBackendCountParity ? "EXACT" : "RED";
      reuseDelta.textContent = growthStopReason || "finite anchor continuation · no stationary claim";
      updateOrderAudit();
      renderStack();
      renderMarkings();
      renderStructureStats();
      renderLegend();
      syncStageOptions();
      return;
    }
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
  if (pipelineStage === 4 && iceAnchorTrace) {
    legendHeading.textContent = "Sealed molecular continuation";
    const oxygen = document.createElement("span");
    const oxygenSwatch = document.createElement("i");
    oxygenSwatch.className = "element-swatch";
    oxygenSwatch.style.setProperty("--swatch", ELEMENTS.O.css);
    oxygen.append(oxygenSwatch, document.createTextNode("O · emitted shared anchor atom"));
    const hydrogen = document.createElement("span");
    const hydrogenSwatch = document.createElement("i");
    hydrogenSwatch.className = "cluster-swatch";
    hydrogenSwatch.style.setProperty("--swatch", "#7f9e96");
    hydrogen.append(hydrogenSwatch, document.createTextNode("H · mutually exclusive pose hypotheses (not materialized)"));
    speciesLegend.append(oxygen, hydrogen);
  } else if (pipelineStage === 3 && sectionModel) {
    legendHeading.textContent = "Local marking sections";
    markingPrototypeTypes().forEach((cluster, index) => {
      const key = `m_${markingPrototypeName(index)}`;
      const row = document.createElement("span");
      const swatch = document.createElement("i");
      swatch.className = "cluster-swatch";
      swatch.style.setProperty("--swatch", `#${markingColor(key).getHexString()}`);
      row.append(swatch, document.createTextNode(`${key}(x) · ${cluster.label || `C${index + 1}`} · learned from ${cluster.count}`));
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
      const count = cluster.classPlacementIndices?.length
        ?? learnedCover.placements.filter((placement) => placement.type === cluster.type).length;
      row.append(swatch, document.createTextNode(`${cluster.residual ? "gap" : "C"}${index + 1} · ${cluster.element || cluster.species} · ${count} placements`));
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
    const state = document.createElement("em"); state.textContent = entry.type === "reject" ? "prune" : "keep";
    row.classList.toggle("reject", entry.type === "reject");
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
  markingHeading.textContent = pipelineStage === 0 ? "colored geometric envelopes" : pipelineStage < 2 ? "learned vocabulary" : pipelineStage === 2 ? "rigid overlap rules" : pipelineStage === 3 ? "local section bundle" : "active section marking";
  markingTable.replaceChildren();
  if (pipelineStage === 0) {
    const records = coloredDistanceEnvelopes?.records || [];
    const coordinationRecords = coloredCoordinationEnvelopes?.records || [];
    const angularRecords = coloredAngularEnvelopes?.records || [];
    markCount.textContent = `${records.length} pairs · ${coordinationRecords.length} capacities · ${angularRecords.length} angles · 1 reservoir`;
    const p = document.createElement("p");
    p.textContent = "Pair contacts, ordered coordination caps, and three-body angle bands are learned from positions; no motif labels or potential are supplied.";
    markingTable.appendChild(p);
    const reservoir = document.createElement("div"); reservoir.className = "mark-row composition-reservoir-row";
    reservoir.title = "Observed global fractions are an optional soft frontier preference, never a hard surface constraint";
    const reservoirCode = document.createElement("code"); reservoirCode.textContent = "ratio";
    const reservoirRatio = document.createElement("span"); reservoirRatio.textContent = Object.entries(compositionTarget.reducedRatio)
      .map(([symbol, count]) => `${symbol}:${count}`).join(" · ");
    const reservoirCount = document.createElement("b"); reservoirCount.textContent = `N=${compositionTarget.observations}`;
    reservoir.append(reservoirCode, reservoirRatio, reservoirCount); markingTable.appendChild(reservoir);
    const toAngstrom = referenceSpacingA / referenceSpacing;
    records.forEach((record) => {
      const row = document.createElement("div"); row.className = "mark-row distance-envelope-row";
      row.title = `${record.nearestObservations} nearest-by-species observations · exclusion remains below every supplied contact`;
      const code = document.createElement("code"); code.textContent = record.species.join("–");
      const span = document.createElement("span"); span.textContent = `contact ≥ ${(record.minimumObserved * toAngstrom).toFixed(2)} Å`;
      const b = document.createElement("b"); b.textContent = `hard < ${(record.exclusion * toAngstrom).toFixed(2)} Å`;
      row.append(code, span, b); markingTable.appendChild(row);
    });
    coordinationRecords.forEach((record) => {
      const row = document.createElement("div"); row.className = "mark-row coordination-envelope-row";
      row.title = `${record.centerObservations} observed ${record.centerSpecies} centers · upper bound preserves the maximum supplied coordination`;
      const code = document.createElement("code"); code.textContent = `${record.centerSpecies}→${record.neighborSpecies}`;
      const span = document.createElement("span"); span.textContent = `contact ≤ ${(record.contactCutoff * toAngstrom).toFixed(2)} Å`;
      const b = document.createElement("b"); b.textContent = `z ≤ ${record.maximumObserved}`;
      row.append(code, span, b); markingTable.appendChild(row);
    });
    angularRecords.forEach((record) => {
      const row = document.createElement("div"); row.className = "mark-row angular-envelope-row";
      row.title = `${record.angleObservations} observed angles around ${record.centerObservations} centers · separated modes remain separated`;
      const code = document.createElement("code"); code.textContent = `${record.neighborSpecies[0]}–${record.centerSpecies}–${record.neighborSpecies[1]}`;
      const span = document.createElement("span"); span.textContent = record.bands
        .map((band) => `${band.minimum.toFixed(0)}–${band.maximum.toFixed(0)}°`).join(" ∪ ");
      const b = document.createElement("b"); b.textContent = `×${record.angleObservations}`;
      row.append(code, span, b); markingTable.appendChild(row);
    });
    return;
  }
  const learned = learnedCover.molecular || learnedCover.occurrenceBased ? clusterGalleryTypes().map((cluster) => [
    `${cluster.label} · ${cluster.element}`,
    cluster.gap ? "explicit gap terminal" : cluster.geometry || "species + distances",
    `×${cluster.classPlacementIndices?.length
      ?? learnedCover.placements.filter((placement) => placement.type === cluster.type).length}`,
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
  const sectionEntries = markingPrototypeTypes().map((cluster, index) => {
    const count = sectionModel.sampleLabels.slice(0, trainingProgress).filter((label) => label === index).length;
    const total = sectionModel.sampleLabels.filter((label) => label === index).length;
    return [`m_${markingPrototypeName(index)}`, `loss ${sectionLossForCluster(index).toFixed(3)}`, `${count}/${total}`];
  });
  const activeEntries = [...cache.entries()].sort((a, b) => b[1].count - a[1].count).slice(0, 5).map(([key, value]) => [key, `${value.min.toFixed(2)}…${value.max.toFixed(2)}`, `×${value.count}`]);
  const entries = pipelineStage < 2 ? learned : pipelineStage === 2 ? rigidRules : pipelineStage === 3 ? sectionEntries : activeEntries;
  markCount.textContent = pipelineStage < 2 ? `${learned.length} learned` : pipelineStage === 2 ? `${overlapGrammar.rules.length} SE(3) rules` : pipelineStage === 3 ? `${sectionEntries.length} sections · rank ${sectionModel.channels}` : `${cache.size} active`;
  if (!entries.length) {
    const p = document.createElement("p");
    p.textContent = pipelineStage === 3 && trainingProgress === 0
      ? `Press Play or Step to process ${sectionModel.sampleKind} training samples.`
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
downloadReceiptButton.addEventListener("click", () => withReceiptStatus(downloadReceiptButton, async () => {
  const receipt = await serializedExperimentReceipt();
  const blob = new Blob([receipt], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `gcts-${scenarioSelect.value}-stage-${visiblePipelineOrdinal(pipelineStage)}-receipt.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
  receiptStatus.textContent = "Receipt downloaded · coordinates excluded; SHA-256 digests included.";
}));
copyReceiptButton.addEventListener("click", () => withReceiptStatus(copyReceiptButton, async () => {
  if (!navigator.clipboard?.writeText) throw new Error("clipboard API unavailable");
  await navigator.clipboard.writeText(await serializedExperimentReceipt());
  receiptStatus.textContent = "Receipt JSON copied · coordinates excluded; SHA-256 digests included.";
}));
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
  if (trainingProgress < markingSampleCount()) return;
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
    markingSearchMode = "single";
    markingDraft = { ...marking.config,
      channels: marking.config.channelMode === "auto" ? 0 : marking.config.channels };
    policySelect.value = "marked";
    persistMarkingLibrary();
  }
  if (pipelineStage === 4) enterPipelineStage(4);
});
markingSearchModeSelect.addEventListener("change", () => {
  markingSearchMode = markingSearchModeSelect.value === "portfolio" ? "portfolio" : "single";
  persistMarkingLibrary();
  if (pipelineStage === 4) enterPipelineStage(4);
});
geometryPreferenceSelect.addEventListener("change", () => {
  geometryPreference = geometryPreferenceSelect.value === "none" ? "none" : "strain";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
strainWeightSelect.addEventListener("change", () => {
  const value = Number(strainWeightSelect.value);
  geometricStrainWeight = [.08, .16, .32].includes(value) ? value : DEFAULT_GEOMETRIC_STRAIN_WEIGHT;
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
compositionPreferenceSelect.addEventListener("change", () => {
  const value = compositionPreferenceSelect.value;
  compositionPreference = value === "none" || value === "strong" ? value : "soft";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
surfacePreferenceSelect.addEventListener("change", () => {
  const value = surfacePreferenceSelect.value;
  surfacePreference = value === "none" || value === "strong" ? value : "soft";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
growthSchedulingSelect.addEventListener("change", () => {
  growthScheduling = growthSchedulingSelect.value === "serial" ? "serial" : "commuting";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
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
rdfPairSelect.addEventListener("change", () => {
  rdfPairSelection = rdfPairSelect.value;
  renderStructureStats();
});
structureObservableSelect.addEventListener("change", () => {
  structureObservableSelection = structureObservableSelect.value === "sq" ? "sq" : "rdf";
  renderStructureStats();
});
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
