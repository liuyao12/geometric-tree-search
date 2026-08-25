import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  occupancyChemistryToken,
  occupancyDisplayLabel,
  displacement as structureDisplacement,
  formalChargeFromChemistryToken,
  isotropicPairDistanceUncertaintyA,
  parseStructureText,
  validateStructure,
} from "./structure-io.js?v=20260824-5";
import { randomNomadStructure } from "./structure-database.js?v=20260824-1";
import { PERIODIC_ELEMENTS } from "./periodic-table.js";
import {
  executeIceMolecularAnchorGrowth,
  validateIceMolecularPortArtifact,
} from "./ice-molecular-anchor-growth.js";
import {
  executeFrozenIceViAnchorTrace,
  validateIceViAnchorTraceArtifact,
} from "./ice-vi-anchor-trace.js?v=20260824-1";
import { discoverIrregularCover } from "./irregular-cover.js?v=20260824-1";
import { generateAmorphousMixture } from "./amorphous-glass.js?v=20260824-1";
import { powderStructureFactor, summarizeStructureFactor } from "./structure-observables.js?v=20260824-1";
import { compositionBalanceDelta, learnCompositionTarget } from "./composition-balance.js?v=20260824-1";
import { formalChargeBalanceDelta, learnFormalChargeTarget } from "./formal-charge-balance.js?v=20260824-1";
import {
  discoverFiniteMolecularComponents,
  discoverMolecularConnectionTopology,
} from "./molecular-components.js?v=20260824-3";
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
  learnColoredAngularEnvelopesEnsemble,
  learnColoredCoordinationEnvelopesEnsemble,
  learnColoredDistanceEnvelopesEnsemble,
} from "./colored-distance-envelopes.js?v=20260824-6";
import { learnLocalPairDistanceUncertaintyEnsemble } from "./ensemble-geometry-uncertainty.js?v=20260824-1";
import { classifyProperPoseOrbits, symmetryReducedMisorientation } from "./proper-pose-orbits.js?v=20260825-1";
import {
  centeredStructuralWindow,
  inferPointSetDimension,
  phaseComparisonRadius,
} from "./phase-evidence.js?v=20260824-1";
import {
  growthEnvironmentAudit,
  growthEnvironmentContains,
  growthEnvironmentSignedMargin,
  growthEnvironmentSpec,
} from "./growth-environments.js?v=20260825-3";
import { auditGeometricMicrostructure } from "./microstructure-audit.js?v=20260824-1";
import { CDYB_BROWSER_FIXTURE } from "./cdyb-browser-fixture.js?v=20260824-1";
import {
  generateIceViiiObservation,
  ICE_VIII_BROWSER_FIXTURE,
} from "./ice-viii-browser-fixture.js?v=20260824-1";
import {
  generateIceViAverageObservation,
  ICE_VI_BROWSER_FIXTURE,
  resolveIceViIceRuleMicrostate,
} from "./ice-vi-browser-fixture.js?v=20260824-2";

const ICE_MOLECULAR_PORT_ARTIFACT = await fetch(new URL(
  "./ice-molecular-port-artifact.json?v=20260824-1", import.meta.url)).then((response) => {
  if (!response.ok) throw new Error(`Cannot load frozen ice port artifact: ${response.status}`);
  return response.json();
});
validateIceMolecularPortArtifact(ICE_MOLECULAR_PORT_ARTIFACT);

const ICE_VI_ANCHOR_TRACE_ARTIFACT = await fetch(new URL(
  "./ice-vi-anchor-trace-artifact.json?v=20260824-1", import.meta.url)).then((response) => {
  if (!response.ok) throw new Error(`Cannot load frozen Ice VI anchor trace: ${response.status}`);
  return response.json();
});
validateIceViAnchorTraceArtifact(ICE_VI_ANCHOR_TRACE_ARTIFACT);

const $ = (id) => document.getElementById(id);
const viewport = $("viewport");
const scenarioSelect = $("scenarioSelect");
const iceViMicrostateControls = $("iceViMicrostateControls");
const iceViMicrostateButton = $("iceViMicrostateButton");
const iceViAverageButton = $("iceViAverageButton");
const iceViMicrostateState = $("iceViMicrostateState");
const iceViMicrostateStatus = $("iceViMicrostateStatus");
const ensembleControls = $("ensembleControls");
const ensembleFrameSelect = $("ensembleFrameSelect");
const ensembleFrameCount = $("ensembleFrameCount");
const ensembleEvidenceSelect = $("ensembleEvidenceSelect");
const ensembleStatus = $("ensembleStatus");
const measurementConditions = $("measurementConditions");
const measurementConditionChips = $("measurementConditionChips");
const publishedFixtureProvenance = $("publishedFixtureProvenance");
const publishedFixtureLicense = $("publishedFixtureLicense");
const publishedFixtureName = $("publishedFixtureName");
const publishedFixtureArticle = $("publishedFixtureArticle");
const publishedFixtureArchive = $("publishedFixtureArchive");
const structureFileInput = $("structureFileInput");
const importStatus = $("importStatus");
const loadFixtureButton = $("loadFixtureButton");
const loadEnsembleFixtureButton = $("loadEnsembleFixtureButton");
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
const confinementHint = $("confinementHint");
const confinementNote = $("confinementNote");
const policySelect = $("policySelect");
const stageOptionsPanel = $("stageOptionsPanel");
const stageOptionsEyebrow = $("stageOptionsEyebrow");
const stageOptionsTitle = $("stageOptionsTitle");
const stageOptionsState = $("stageOptionsState");
const clusterGeometryOptions = $("clusterGeometryOptions");
const geometryModeSelect = $("geometryModeSelect");
const clusterToleranceSelect = $("clusterToleranceSelect");
const clusterToleranceHint = $("clusterToleranceHint");
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
const growthProtocolSelect = $("growthProtocolSelect");
const growthProtocolHint = $("growthProtocolHint");
const growthProtocolSummary = $("growthProtocolSummary");
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
const chargePreferenceSelect = $("chargePreferenceSelect");
const chargePreferenceHint = $("chargePreferenceHint");
const surfacePreferenceSelect = $("surfacePreferenceSelect");
const frontMorphologySelect = $("frontMorphologySelect");
const frontMorphologyWeightSelect = $("frontMorphologyWeightSelect");
const frontMorphologyHint = $("frontMorphologyHint");
const frontMorphologyBadge = $("frontMorphologyBadge");
const frontMorphologyBadgeLabel = $("frontMorphologyBadgeLabel");
const epitaxyTemplateSelect = $("epitaxyTemplateSelect");
const epitaxyWeightSelect = $("epitaxyWeightSelect");
const epitaxyTemplateHint = $("epitaxyTemplateHint");
const epitaxyBadge = $("epitaxyBadge");
const epitaxyBadgeLabel = $("epitaxyBadgeLabel");
const externalDriveSelect = $("externalDriveSelect");
const externalDriveWeightSelect = $("externalDriveWeightSelect");
const externalDriveHint = $("externalDriveHint");
const externalDriveBadge = $("externalDriveBadge");
const externalDriveGlyph = $("externalDriveGlyph");
const externalDriveBadgeLabel = $("externalDriveBadgeLabel");
const affineLoadSelect = $("affineLoadSelect");
const affineLoadMagnitudeSelect = $("affineLoadMagnitudeSelect");
const affineLoadHint = $("affineLoadHint");
const affineLoadBadge = $("affineLoadBadge");
const affineLoadGlyph = $("affineLoadGlyph");
const affineLoadBadgeLabel = $("affineLoadBadgeLabel");
const robustnessPreferenceSelect = $("robustnessPreferenceSelect");
const robustnessWeightSelect = $("robustnessWeightSelect");
const robustnessHint = $("robustnessHint");
const microstructureCouplingSelect = $("microstructureCouplingSelect");
const microstructureCouplingWeightSelect = $("microstructureCouplingWeightSelect");
const microstructureCouplingHint = $("microstructureCouplingHint");
const loopClosurePreferenceSelect = $("loopClosurePreferenceSelect");
const loopClosureWeightSelect = $("loopClosureWeightSelect");
const loopClosureHint = $("loopClosureHint");
const loopClosureBadge = $("loopClosureBadge");
const loopClosureBadgeLabel = $("loopClosureBadgeLabel");
const arrivalPathSelect = $("arrivalPathSelect");
const arrivalPathWeightSelect = $("arrivalPathWeightSelect");
const arrivalPathHint = $("arrivalPathHint");
const arrivalPathBadge = $("arrivalPathBadge");
const arrivalPathBadgeLabel = $("arrivalPathBadgeLabel");
const explorationScaleSelect = $("explorationScaleSelect");
const explorationScaleHint = $("explorationScaleHint");
const resampleGrowthButton = $("resampleGrowthButton");
const explorationBadge = $("explorationBadge");
const explorationBadgeLabel = $("explorationBadgeLabel");
const growthNucleiSelect = $("growthNucleiSelect");
const growthNucleiHint = $("growthNucleiHint");
const nucleiBadge = $("nucleiBadge");
const nucleiBadgeLabel = $("nucleiBadgeLabel");
const nucleusInterfaceInspector = $("nucleusInterfaceInspector");
const nucleusInterfaceState = $("nucleusInterfaceState");
const nucleusPairButtons = $("nucleusPairButtons");
const nucleusPairDetail = $("nucleusPairDetail");
const growthSchedulingSelect = $("growthSchedulingSelect");
const growthSchedulingHint = $("growthSchedulingHint");
const trainVariantButton = $("trainVariantButton");
const primitiveGrowthButton = $("primitiveGrowthButton");
const hierarchicalGrowthButton = $("hierarchicalGrowthButton");
const growthModeNote = $("growthModeNote");
const policyComparison = $("policyComparison");
const policyComparisonState = $("policyComparisonState");
const policySensitivityState = $("policySensitivityState");
const policyHistoryElement = $("policyHistory");
const policyPreviewState = $("policyPreviewState");
const scalePassportState = $("scalePassportState");
const scalePassport = $("scalePassport");
const scalePassportDetail = $("scalePassportDetail");
const observationProvenanceState = $("observationProvenanceState");
const observationProvenance = $("observationProvenance");
const observationProvenanceDetail = $("observationProvenanceDetail");
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
const saveNotebookButton = $("saveNotebookButton");
const clearNotebookButton = $("clearNotebookButton");
const notebookState = $("notebookState");
const notebookEntries = $("notebookEntries");
const notebookComparison = $("notebookComparison");
const notebookInterventionAudit = $("notebookInterventionAudit");
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
const processTimeline = $("processTimeline");
const processTimelineEyebrow = $("processTimelineEyebrow");
const processTimelineTitle = $("processTimelineTitle");
const processTimelineState = $("processTimelineState");
const processTimelineInput = $("processTimelineInput");
const processTimelineNote = $("processTimelineNote");
const processEvidenceLedger = $("processEvidenceLedger");
const processEvidenceDetail = $("processEvidenceDetail");
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
const chargeValue = $("chargeValue");
const surfaceValue = $("surfaceValue");
const resolverValue = $("resolverValue");
const constraintLedger = $("constraintLedger");
const constraintDetail = $("constraintDetail");
const leapCertificateSection = $("leapCertificateSection");
const leapCertificateState = $("leapCertificateState");
const leapHistoryElement = $("leapHistory");
const leapFlow = $("leapFlow");
const leapPhysicsMatrix = $("leapPhysicsMatrix");
const leapPhysicsDetail = $("leapPhysicsDetail");
const leapClaimBoundary = $("leapClaimBoundary");
const growthMechanismSection = $("growthMechanismSection");
const growthMechanismState = $("growthMechanismState");
const growthMechanismProjection = $("growthMechanismProjection");
const growthMechanismCanvas = $("growthMechanismCanvas");
const growthMechanismLedger = $("growthMechanismLedger");
const growthMechanismBoundary = $("growthMechanismBoundary");
const growthUncertaintyState = $("growthUncertaintyState");
const growthUncertaintyBudget = $("growthUncertaintyBudget");
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
const costScalingSection = $("costScalingSection");
const costScalingState = $("costScalingState");
const mdHorizonSelect = $("mdHorizonSelect");
const mdScalingSelect = $("mdScalingSelect");
const costLiveWork = $("costLiveWork");
const costScalingTable = $("costScalingTable");
const costScalingBoundary = $("costScalingBoundary");
const legendHeading = $("legendHeading");
const speciesLegend = $("speciesLegend");
const orderClassValue = $("orderClassValue");
const structureNameValue = $("structureNameValue");
const symmetryValue = $("symmetryValue");
const confidenceValue = $("confidenceValue");
const phaseWindowValue = $("phaseWindowValue");
const phaseMarginValue = $("phaseMarginValue");
const phaseIndependentValue = $("phaseIndependentValue");
const phaseClosureValue = $("phaseClosureValue");
const phaseTrajectoryState = $("phaseTrajectoryState");
const phaseTrajectoryCanvas = $("phaseTrajectoryCanvas");
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
const PHASE_CLASSIFICATION_MINIMUM_ATOMS = 32;
const PHASE_CLASSIFICATION_THRESHOLD = .58;
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
  D: { color: 0xd9f4ff, css: "#d9f4ff", radius: .31 },
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
  Cd: { color: 0xffd98f, css: "#ffd98f", radius: 1.44 },
  Yb: { color: 0x00bf38, css: "#00bf38", radius: 1.87 },
};
const MATERIALS = {
  iceIh: { name: "ice Ih", elements: ["H", "O"], spacingA: .9572, cell: "hexagonal ice · proton-ordered fixture", periodicWindow: true, order: "crystal", symmetry: "P6₃/mmc oxygen network", audit: "molecular cover + hydrogen-bond graph", motifShellCutoff: 3.12, descriptorCutoff: 3.25, overlapDistanceCutoff: 3.35, icePolytype: "Ih", note: "The learner must discover H₂O molecules, then use overlapping water-dimer and oxygen-ring connection clusters to traverse the crystal." },
  iceIc: { name: "ice Ic", elements: ["H", "O"], spacingA: .9572, cell: "cubic ice · proton-ordered fixture", periodicWindow: true, order: "crystal", symmetry: "Fd-3m oxygen network", audit: "molecular cover + hydrogen-bond graph", motifShellCutoff: 3.12, descriptorCutoff: 3.25, overlapDistanceCutoff: 3.35, icePolytype: "Ic", note: "A cubic-ice control with the same H₂O motif but a different cluster-of-clusters connection grammar." },
  iceVIII: { name: "ice VIII · D₂O", elements: ["D", "O"], spacingA: .9732640323944047,
    cell: "tetragonal proton-ordered ice · COD 1566658 · 2×2×2 observation window",
    periodicWindow: true, order: "crystal", symmetry: "I4₁/amd · #141",
    audit: "published neutron geometry + molecular/connection/void cover",
    motifShellCutoff: 3.0, descriptorCutoff: 3.35, overlapDistanceCutoff: 3.55,
    molecularFixture: "ice-viii-cod-1566658",
    fixtureProvenance: {
      id: `COD-${ICE_VIII_BROWSER_FIXTURE.codId}`,
      name: "proton-ordered D₂O ice VIII",
      atomCount: 192,
      articleDoi: ICE_VIII_BROWSER_FIXTURE.doi,
      sourceUrl: `https://www.crystallography.net/cod/${ICE_VIII_BROWSER_FIXTURE.codId}.cif`,
      license: ICE_VIII_BROWSER_FIXTURE.license,
      sourceSha256: ICE_VIII_BROWSER_FIXTURE.cifSha256,
      normalizedAtomsSha256: ICE_VIII_BROWSER_FIXTURE.normalizedAtomsSha256,
      sourceRevision: ICE_VIII_BROWSER_FIXTURE.codRevision,
    },
    note: "A published neutron-diffraction control with explicit, fully occupied deuterium sites. D is retained as an isotope; the learner receives only D/O identities and Cartesian positions, not the D₂O formula or ice-VIII label." },
  iceVI: { name: "ice VI · disordered D₂O average", elements: ["D", "O"], spacingA: .97,
    cell: "tetragonal proton-disordered ice · COD 1567346 · 2×2×2 average structure",
    periodicWindow: true, order: "crystal", symmetry: "P4₂/nmc · #137",
    audit: "published half-occupied D sites + occupancy-aware irregular/gap cover",
    motifShellCutoff: 3.0, descriptorCutoff: 3.35, overlapDistanceCutoff: 3.55,
    molecularFixture: "ice-vi-cod-1567346-average", averageStructureSites: true,
    occupancyWeightedAtomCount: 240, growthWithheld: true,
    recordedMeasurementConditions: {
      temperature: { value: ICE_VI_BROWSER_FIXTURE.measurement.temperatureK, unit: "K", sourceTag: "_diffrn_ambient_temperature" },
      environment: { value: ICE_VI_BROWSER_FIXTURE.measurement.radiation, sourceTag: "_diffrn_radiation_probe" },
      provenance: "recorded diffraction conditions from COD 1567346",
    },
    crystallographicOccupancy: {
      representation: "80 fully occupied O sites plus 320 candidate D sites at occupancy 1/2; vacancy retained explicitly",
      mixedSites: 0, partialSites: 320, inferredEqualFractionSites: 0, totalVacancyFraction: 160,
      formalChargeCoverage: 0, formalChargeResolvedSites: 0, netSuppliedCellFormalCharge: 0,
    },
    fixtureProvenance: {
      id: `COD-${ICE_VI_BROWSER_FIXTURE.codId}`,
      name: "proton-disordered D₂O ice VI average structure",
      atomCount: 400,
      countLabel: "400 average sites · 240 occupancy-weighted atoms",
      articleDoi: ICE_VI_BROWSER_FIXTURE.doi,
      sourceUrl: `https://www.crystallography.net/cod/${ICE_VI_BROWSER_FIXTURE.codId}.cif`,
      license: ICE_VI_BROWSER_FIXTURE.license,
      sourceSha256: ICE_VI_BROWSER_FIXTURE.cifSha256,
      normalizedAtomsSha256: ICE_VI_BROWSER_FIXTURE.normalizedAtomsSha256,
      sourceRevision: ICE_VI_BROWSER_FIXTURE.codRevision,
    },
    note: "A published diffraction-average structure. Every half-occupied D/vacancy site remains an explicit occupational alternative. The positions do not specify a unique assignment of two deuteria to each oxygen, so molecular discovery must fail closed instead of inventing D₂O molecules." },
  dryIce: { name: "dry ice CO₂-I", elements: ["C", "O"], spacingA: 1.168, cell: "cubic molecular solid · Pa-3 · a = 5.578 Å", periodicWindow: true, referenceCellA: 16.734, order: "crystal", symmetry: "Pa-3 · #205", audit: "generic molecular + connection + void cover", motifShellCutoff: 4.2, descriptorCutoff: 4.6, overlapDistanceCutoff: 4.8, molecularFixture: "dry-ice-pa3", note: "A non-water molecular-crystal control: the learner must discover linear CO₂ components and intermolecular connection/void topology without receiving the CO₂ formula or Pa-3 label." },
  graphene: { name: "graphene monolayer", elements: ["C"], spacingA: 1.42, cell: "single hexagonal sheet", order: "crystal", symmetry: "p6/mmm layer group", audit: "2D translations + diffraction", intrinsicDimension: 2, planarLayers: [{ angle: 0, zA: 0, species: ["C", "C"] }], note: "A one-component intrinsic-2D positive control learned after arbitrary embedding in 3D." },
  hbn: { name: "aligned hBN bilayer", elements: ["B", "N"], spacingA: 1.44, cell: "aligned hexagonal sheets · 3.33 Å separation", order: "crystal", symmetry: "commensurate bilayer", audit: "2D translations + finite registry", intrinsicDimension: 2, planarLayers: [{ angle: 0, zA: -1.665, species: ["B", "N"] }, { angle: 0, zA: 1.665, species: ["B", "N"] }], note: "A commensurate bilayer whose finite interlayer registry can be represented by a bounded local marking." },
  competition: { name: "NaCl rocksalt", elements: ["Na", "Cl"], spacingA: 2.82, cell: "Fm3̅m · a = 5.640 Å", periodicWindow: true, order: "crystal", symmetry: "Fm-3m · #225", audit: "space group", note: "A periodic positive control: translation is the cheap ceiling, while the learner must recover it blindly." },
  random: { name: "Cu₆₄Zr₃₆ metallic glass", elements: ["Cu", "Zr"], spacingA: 2.72, cell: "periodic amorphous hard-core cell", periodicWindow: true, order: "amorphous", symmetry: "no stable long-range group", audit: "partial RDF + local motifs + S(q)", note: "No unique continuation is implied. The target is an ensemble; the deterministic browser fixture is a continuous random hard-core packing, not a perturbed lattice or an MD trajectory." },
  iqc: { name: "Al–Cu–Fe IQC approximant", elements: ["Al", "Cu", "Fe"], spacingA: 2.55, cell: "icosahedral approximant", periodicWindow: false, order: "quasicrystal", symmetry: "icosahedral point symmetry", audit: "superspace + diffraction", note: "An ordinary 3D space group is insufficient; inflation, reciprocal-module, and phason statistics are required." },
  cdyb: { name: "Cd₅.₇Yb icosahedral quasicrystal", elements: ["Cd", "Yb"], spacingA: 2.62788720764582,
    cell: "published aperiodic Cd–Yb model · off-centre R14 Å crop", periodicWindow: false,
    order: "quasicrystal", symmetry: "icosahedral noncrystallographic order", audit: "published model + sealed disjoint continuation",
    publishedFixture: "cdyb-offcenter-r14", fixtureProvenance: CDYB_BROWSER_FIXTURE,
    note: "A 506-atom physical Cd/Yb crop from the published CC-BY-4.0 model. The live learner receives only species and positions; six-dimensional coordinates, occupation domains, empty-centre markers, and the family label are withheld from clustering and growth." },
  moire: { name: "30° twisted hBN bilayer", elements: ["B", "N"], spacingA: 1.44, cell: "two hexagonal sheets · 3.33 Å separation", order: "quasicrystal", symmetry: "12-fold quasiperiodic order", audit: "2D diffraction + absence of common translations", intrinsicDimension: 2, planarLayers: [{ angle: 0, zA: -1.665, species: ["B", "N"] }, { angle: Math.PI / 6, zA: 1.665, species: ["B", "N"] }], note: "Each sheet is periodic, while their 30° union has no common translation lattice." },
  bc8: { name: "silicon BC8-like network", elements: ["Si"], spacingA: 2.35, cell: "BC8 target · a = 6.636 Å", periodicWindow: true, order: "crystal", symmetry: "Ia-3 · #206", audit: "space group", note: "A nontrivial crystalline control for topology, coordination, and species-preserving symmetry recovery." },
};
const RECURSIVE_BENCHMARKS = {
  iceIh: { hierarchy: [1, 8, "pose domains"], curve: [27, 43, 51], mark: "unanimous orientation domains", action: "2 exact blind O frontiers", speed: "16 → 8 exact · then fixed", gate: "pass anchor · molecular growth open", status: "limit", note: "The physically corrected fixture obeys the Bernal–Fowler ice rules: every H₂O donates twice and every O–O connection carries exactly one proton. The known periodic window has one H₂O class, 3 decorated bridge classes, and 33 decorated O₆ ring-boundary classes; together their occurrences cover 216/216 atoms. The sealed gate learns 8 proper-SE(3) ports on a disjoint 201-atom window. Factoring mutually exclusive H₂O poses emits 16/16 and then 8/8 correct unseen oxygen anchors before a safe fixed point. Proton orientations remain unresolved, so full-molecule, stationary, and exponential ice growth stay red." },
  iceIc: { hierarchy: [1, 8, "pose domains"], curve: [15, 27], mark: "Ih ports → Ic alternatives", action: "1 exact cross-polytype frontier", speed: "12 exact · then safe fixed point", gate: "progress · cross-polytype blind transfer", status: "limit", note: "The Ih-fitted 8-port grammar transfers to a disjoint cubic-ice seed without refitting or target access. Its first unseen oxygen frontier is 12/12 exact and the whole-molecule path reaches 100% oxygen recall, but premature proton choices lower precision. Domain unanimity rejects unsupported depth-2 anchors rather than emitting false sites. This isolates the remaining task as a bounded proton-orientation connection marking, not a new lattice backend." },
  iceVIII: { hierarchy: ["D₂O", "bridges", "voids"], curve: [192], mark: "published ordered-isotope geometry",
    action: "cover audit only", speed: "no autonomous claim", gate: "real-data molecular generalization", status: "control",
    note: "COD 1566658 supplies fully occupied O and D coordinates from neutron diffraction. The live path must rediscover D₂O molecules and the interpenetrating-network connection/void grammar from positions alone. This is a published known-window cover audit; no held-out ice-VIII continuation, stationary rule, or high-pressure kinetics is claimed." },
  iceVI: { hierarchy: ["O framework", "D/Vac alternatives", "gap terminals"], curve: [400, 23, 8], mark: "two-parent port consensus",
    action: "8 exact O anchors · D₂O poses retained", speed: "4 → 3 → 1 exact · then fixed", gate: "pass O framework · orientation red", status: "limit",
    note: "COD 1567346 supplies a proton-disordered average structure: 80 O positions and 320 candidate D positions at occupancy 1/2 in the 2×2×2 observation. The average remains unresolved and declines a unique D₂O partition. In a separate sealed audit, one realized microstate teaches five D₂O metric conformers and 84 proper-SE(3) ports. A 95.8%-precision training consensus then transfers to a spatially disjoint microstate and emits 4 → 3 → 1 exact unseen oxygen anchors with zero false anchors. Every new D₂O pose remains a mutually exclusive occupational hypothesis; forcing whole molecules makes three atomic errors. Oxygen-framework continuation passes, while occupational, stationary, and exponential growth remain red." },
  dryIce: { hierarchy: ["molecule", "pair", "void"], curve: [3, 324], mark: "generic molecular ports", action: "94 replay decisions", speed: "324 / 324 · fixed point", gate: "exact known-window control", status: "limit", note: "A saved Pa-3 CO₂-I window exercises the generic, non-water molecular front end. Starting from one 3-atom CO₂ component, 94 deterministic covering decisions produce 95 rigid placements at causal depth 14 and replay all 324/324 known colored sites with zero missing, duplicate, or extraneous atoms. The frozen observed frontier then exhausts with zero outside-window emissions. This is an exact target-aware known-window replay—not autonomous continuation, stationarity, an exponential rule, or a physical growth rate." },
  graphene: { hierarchy: [1, 4, 16], curve: [373, 1495, 5983, 23935, 95743, 382975, 1531903], mark: "one C₂ sheet pose", action: "6 area rewrites → 1.53m", speed: "≈4× area per action", gate: "pass · 2D synthetic", status: "pass", note: "The generic planar atlas learns one C₂ motif pose and exactly predicts an unseen 1,495-atom disk." },
  hbn: { hierarchy: [2, 8, 32], curve: [746, 2990, 11960, 47840, 191360, 765440, 3061760], mark: "finite registry + pose fallback", action: "6 area rewrites → 3.06m", speed: "≈4× area per action", gate: "pass · 2D synthetic", status: "pass", note: "The registry vocabulary remains bounded for the aligned bilayer and the generic planar atlas preserves both learned sheet poses." },
  competition: { hierarchy: [7, 27, 164], curve: [216, 1728, 13824, 110592, 884736, 7077888], mark: "translation quotient", action: "5 rewrites → 7.08m", speed: "8× per action", gate: "pass · cell-free", status: "pass", note: "From 216 colored positions, the hierarchy discovers three composable translations without using the supplied cell. The recursive quotient reaches 7,077,888 implicit atoms in five actions." },
  random: { hierarchy: ["local", "—", "—"], curve: [507], mark: "no recurrent macro", action: "ensemble only", speed: "no claim", gate: "negative control", status: "limit", note: "The hierarchy correctly declines deterministic continuation. Four independently seeded amorphous controls produced zero deterministic false positives." },
  iqc: { hierarchy: [73, 17, 5], curve: [2064, 1122, 324, 78, 26, 12, 8, 4], mark: "bounded ports + exact derivations", action: "6 train levels · heldout L1 stops", speed: "1,248 / 1,248 primitive transfer", gate: "red · stationary transfer", status: "limit", note: "History-free re-clustering completely covers 2,064 grown atoms and reaches six positive train-compression levels. On three sealed held-out patches, frozen supports cover every atom and 256 of 259 first-level types replay; three absent types stop recursive transfer. The deterministic beam retains more exact derivations but still finds no stationary three-level production, so generic exponential IQC growth remains red.", external: { name: "experimental Sc–Zn IQC", hierarchy: "13 → 38 → 98", precision: "75.5% P / 55.0% R", recall: "85.4% P / 32.1% R", reduction: "57× → 185×" }, connection: { transfer: "1,248 / 1,248 atoms · 256 / 259 L1 types", states: "78 support types · 1,122 occurrences · 6 positive train levels", consensusLabel: "persistent wave / marking operating points", consensus: [["wave 1", 100.0, 3.27], ["wave 2", 34.18, 1.14], ["mark 1", 100.0, 0.07], ["mark 2", 0.0, 0.0]], secondOrderLabel: "position and species fidelity by unseen wave", secondOrder: [["wave 1", "position", 100.0, 3.27, 66.52, 2.18], ["wave 2", "position", 34.18, 1.14, 14.29, 0.47], ["mark", "normalized", 100.0, 0.07, 100.0, 0.07]], frontier: { waves: [324, 78, 26, 12, 8, 4], exact: "alternative-consistent train path", recall: "heldout primitive atoms 100% · recursive types 98.8%", full: "three missing frozen L1 types stop promotion without refit" }, macro: { stages: [["support types", 78], ["L1 quotient", 73], ["L2 quotient", 17]], safe: "heldout primitive cover · 1,248/1,248 atoms", rejected: "recursive transfer · 3/259 L1 types absent", crystal: "learned NaCl stationary control · 4,194,304 represented sites", iterated: "beam evidence · 324→78→26→12→8→4", similarity: "deep train compression passes · stationary heldout growth fails" } } },
  cdyb: { hierarchy: [80, 36, 22], curve: [506, 1056, 1672], mark: "causal local connection consensus",
    action: "5 target-blind finite waves", speed: "177 / 179 emitted sites correct", gate: "finite autonomous pass · stationary red", status: "limit",
    note: "The browser input is the published 506-atom off-centre crop. Backend audits on disjoint windows learn nine positive compression levels and a causal local marking; two sealed nuclei grow 178/178 and 117/117 correct atoms, while the same unmarked searches emit 83 false atoms. Those finite runs reach fixed points and no production recurs across three scales, so sustained, stationary, and exponential Cd–Yb growth remain open." },
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
const externalDriveGroup = new THREE.Group();
const unitCellGroup = new THREE.Group();
const interfaceGroup = new THREE.Group();
world.add(confinementGroup, externalDriveGroup, unitCellGroup, bondGroup, atomGroup, clusterGroup, interfaceGroup, frontierGroup, decisionGroup);
scene.add(world);

const sphereGeometry = new THREE.SphereGeometry(0.18, 13, 9);
const occupancyRingGeometry = new THREE.TorusGeometry(0.235, 0.012, 5, 24);
const candidateGeometry = new THREE.SphereGeometry(0.24, 12, 8);
const blueMaterial = new THREE.MeshStandardMaterial({ color: COLORS.blue, roughness: 0.28, metalness: 0.18, emissive: 0x0b526d, emissiveIntensity: 0.32 });
const greenMaterial = new THREE.MeshStandardMaterial({ color: COLORS.green, roughness: 0.34, metalness: 0.12, emissive: 0x59450c, emissiveIntensity: 0.27 });
const blueDimMaterial = new THREE.MeshStandardMaterial({ color: COLORS.blue, transparent: true, opacity: .12, roughness: .5, depthWrite: false });
const greenDimMaterial = new THREE.MeshStandardMaterial({ color: COLORS.green, transparent: true, opacity: .12, roughness: .5, depthWrite: false });
const elementMaterials = new Map();
const dimElementMaterials = new Map();
const occupancyRingMaterials = new Map();
const thermalEnvelopeMaterial = new THREE.MeshBasicMaterial({
  color: 0x9d84ff, wireframe: true, transparent: true, opacity: .16, depthWrite: false,
});
const interfaceRingMaterial = new THREE.MeshBasicMaterial({ color: 0x7ee1e8,
  transparent: true, opacity: .9, depthWrite: false });
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
let acceptedUnloadedGeometricStrain = 0;
let rejectedUnloadedGeometricStrain = 0;
let acceptedCompositionDelta = 0;
let rejectedCompositionDelta = 0;
let acceptedFormalChargeDelta = 0;
let rejectedFormalChargeDelta = 0;
let acceptedSurfaceDeficit = 0;
let rejectedSurfaceDeficit = 0;
let acceptedExternalDriveAlignment = 0;
let rejectedExternalDriveAlignment = 0;
let acceptedRobustnessScore = 0;
let rejectedRobustnessScore = 0;
let acceptedMicrostructureCouplingScore = 0;
let rejectedMicrostructureCouplingScore = 0;
let acceptedLoopClosureScore = 0;
let rejectedLoopClosureScore = 0;
let acceptedIndependentLoopWitnesses = 0;
let rejectedIndependentLoopWitnesses = 0;
let acceptedArrivalPathScore = 0;
let rejectedArrivalPathScore = 0;
let acceptedBlockedPathSamples = 0;
let rejectedBlockedPathSamples = 0;
let arrivalPathSiteSamples = 0;
let arrivalPathNeighborhoodChecks = 0;
let acceptedExplorationOffset = 0;
let rejectedExplorationOffset = 0;
let acceptedFrontMorphologyScore = 0;
let rejectedFrontMorphologyScore = 0;
let frontMorphologyEvaluations = 0;
let frontMorphologyNeighborhoodChecks = 0;
let acceptedEpitaxyRegistryScore = 0;
let rejectedEpitaxyRegistryScore = 0;
let epitaxyRegistryEvaluations = 0;
let epitaxyRegistrySiteChecks = 0;
let constraintNeighborhoodEvaluations = 0;
let constraintNeighborhoodSiteTotal = 0;
let maximumConstraintNeighborhoodSites = 0;
let lastPolicyComparison = null;
let policyComparisonHistory = [];
let selectedPolicySnapshotIndex = -1;
let selectedPolicyPreviewId = "active";
let policySnapshotCount = 0;
let selectedScalePassportId = null;
let selectedScalePassportStage = -1;
let selectedObservationProvenanceId = null;
let experimentNotebookEntries = [];
let selectedNotebookEntryIds = [];
let atomSpatialIndex = new Map();
let trainingProgress = 0;
let clusterDiscoveryTrace = null;
let clusterDiscoveryProgress = 0;
let selectedProcessEvidenceIndex = 0;
let selectedConstraintName = "species / hard core";
let leapHistory = [];
let selectedLeapIndex = -1;
let leapEventCount = 0;
let selectedLeapPhysicsId = "steric";
let growthMechanismEvents = [];
let growthMechanismTotals = {};
let growthPoseAuditsByLeap = new Map();
const MAXIMUM_POSE_AUDITS_PER_LEAP = 64;
let growthMechanismProjectionKey = "xy";
let markingSelection = null;
let liveOrderCache = { key: "", result: null };
let liveOrderHistory = [];
let orderPrototypeLibrary = null;
let growthDeadline = 0;
let growthStartAtomCount = 0;
let growthStopReason = "";
let slowFrameSeconds = 0;
let iceAnchorTrace = null;
let iceAnchorWaveIndex = 0;
let importedStructure = null;
let importedFrameIndex = 0;
let ensembleEvidenceMode = "all";
let iceViMicrostate = null;
let iceViMicrostateSeed = 0;
let selectedDatabaseElements = ["Na", "Cl"];
let markingDraft = { channels: 0, reach: 2, representation: "sites" };
let markingLibrary = [];
let activeMarkingId = null;
let markingSearchMode = "single";
let hierarchyEnabled = true;
let mdHorizonSteps = 100000;
let mdWorkScaling = "local";
let geometryPreference = "strain";
let growthProtocolMode = "custom";
let geometricStrainWeight = DEFAULT_GEOMETRIC_STRAIN_WEIGHT;
let compositionPreference = "soft";
let chargePreference = "auto";
let surfacePreference = "soft";
let frontMorphologyMode = "none";
let frontMorphologyWeight = .24;
let epitaxyTemplateMode = "none";
let epitaxyWeight = .24;
let externalDriveMode = "none";
let externalDriveWeight = .24;
let affineLoadMode = "none";
let affineLoadMagnitude = .02;
let robustnessPreference = "none";
let robustnessWeight = .24;
let microstructureCouplingMode = "none";
let microstructureCouplingWeight = .24;
let loopClosurePreference = "none";
let loopClosureWeight = .24;
let arrivalPathMode = "none";
let arrivalPathWeight = .24;
let geometricExplorationScale = 0;
let growthPathSeed = 1;
let requestedGrowthNuclei = 1;
let initializedGrowthNuclei = 0;
let coalescenceEvents = 0;
let crossNucleusMergeContacts = 0;
let selectedNucleusPairKey = null;
let growthScheduling = "commuting";
let nextMarkingId = 1;
let geometryMode = "auto";
let clusterToleranceMode = "balanced";
let orientationAtlas = [];
let microstructureEvidence = null;
let microstructureProjection = "xy";
let selectedGalleryCluster = 0;
let rdfPairSelection = "all";
let structureObservableSelection = "rdf";
let coloredDistanceEnvelopes = null;
let coloredCoordinationEnvelopes = null;
let coloredAngularEnvelopes = null;
let ensemblePairDistanceUncertainty = null;
let compositionTarget = null;
let formalChargeTarget = null;

const GROWTH_PROTOCOL_DEFAULTS = Object.freeze({
  confinement: "box", geometryPreference: "strain", geometricStrainWeight: .16,
  compositionPreference: "soft", chargePreference: "auto", surfacePreference: "soft",
  frontMorphologyMode: "none", frontMorphologyWeight: .24,
  epitaxyTemplateMode: "none", epitaxyWeight: .24,
  externalDriveMode: "none", externalDriveWeight: .24,
  affineLoadMode: "none", affineLoadMagnitude: .02,
  robustnessPreference: "none", robustnessWeight: .24,
  microstructureCouplingMode: "none", microstructureCouplingWeight: .24,
  loopClosurePreference: "none", loopClosureWeight: .24,
  arrivalPathMode: "none", arrivalPathWeight: .24,
  geometricExplorationScale: 0, requestedGrowthNuclei: 1,
  growthScheduling: "commuting", hierarchyEnabled: true,
});

const GROWTH_PROTOCOLS = Object.freeze({
  bulk: {
    label: "bulk continuation", summary: "Neutral finite bulk boundary with learned strain, balanced composition, and surface-completion ordering.",
    settings: { confinement: "box", geometryPreference: "strain", geometricStrainWeight: .16,
      compositionPreference: "soft", chargePreference: "auto", surfacePreference: "soft",
      frontMorphologyMode: "none", epitaxyTemplateMode: "none", externalDriveMode: "none",
      affineLoadMode: "none", robustnessPreference: "none", microstructureCouplingMode: "none",
      loopClosurePreference: "none", arrivalPathMode: "none", geometricExplorationScale: 0,
      requestedGrowthNuclei: 1, growthScheduling: "commuting", hierarchyEnabled: true },
  },
  epitaxy: {
    label: "coherent thin-film epitaxy", summary: "Supported film with a coherent hexagonal registry, facet propagation, upward feed geometry, arrival clearance, and robustness ordering.",
    settings: { confinement: "substrate", geometryPreference: "strain", geometricStrainWeight: .16,
      compositionPreference: "soft", chargePreference: "auto", surfacePreference: "strong",
      frontMorphologyMode: "facet", frontMorphologyWeight: .24, epitaxyTemplateMode: "hex-coherent", epitaxyWeight: .24,
      externalDriveMode: "z-plus", externalDriveWeight: .24, affineLoadMode: "none",
      robustnessPreference: "margin", robustnessWeight: .24, microstructureCouplingMode: "none",
      loopClosurePreference: "none", arrivalPathMode: "declared-drive", arrivalPathWeight: .24,
      geometricExplorationScale: 0, requestedGrowthNuclei: 1, growthScheduling: "commuting", hierarchyEnabled: true },
  },
  "misfit-film": {
    label: "misfit thin film", summary: "The coherent-film protocol with a declared +5% hexagonal support mismatch; no elastic relaxation or dislocations are inserted.",
    settings: { confinement: "substrate", geometryPreference: "strain", geometricStrainWeight: .16,
      compositionPreference: "soft", chargePreference: "auto", surfacePreference: "strong",
      frontMorphologyMode: "facet", frontMorphologyWeight: .24, epitaxyTemplateMode: "hex-mismatch", epitaxyWeight: .24,
      externalDriveMode: "z-plus", externalDriveWeight: .24, affineLoadMode: "none",
      robustnessPreference: "margin", robustnessWeight: .24, microstructureCouplingMode: "none",
      loopClosurePreference: "consensus", loopClosureWeight: .12, arrivalPathMode: "declared-drive", arrivalPathWeight: .24,
      geometricExplorationScale: 0, requestedGrowthNuclei: 1, growthScheduling: "commuting", hierarchyEnabled: true },
  },
  directional: {
    label: "directional solidification", summary: "A +Z growth direction, coherent facet-front ordering, declared arrival accessibility, and narrow configurational alternatives.",
    settings: { confinement: "box", geometryPreference: "strain", geometricStrainWeight: .16,
      compositionPreference: "soft", chargePreference: "auto", surfacePreference: "soft",
      frontMorphologyMode: "facet", frontMorphologyWeight: .24, epitaxyTemplateMode: "none",
      externalDriveMode: "z-plus", externalDriveWeight: .48, affineLoadMode: "none",
      robustnessPreference: "margin", robustnessWeight: .12, microstructureCouplingMode: "none",
      loopClosurePreference: "none", arrivalPathMode: "declared-drive", arrivalPathWeight: .24,
      geometricExplorationScale: .05, requestedGrowthNuclei: 1, growthScheduling: "commuting", hierarchyEnabled: true },
  },
  dendritic: {
    label: "dendritic growth hypothesis", summary: "A finite nucleus with radial-outward drive, exposed-tip preference, radial arrival accessibility, and a broader path ensemble.",
    settings: { confinement: "sphere", geometryPreference: "strain", geometricStrainWeight: .08,
      compositionPreference: "soft", chargePreference: "auto", surfacePreference: "soft",
      frontMorphologyMode: "tip", frontMorphologyWeight: .48, epitaxyTemplateMode: "none",
      externalDriveMode: "radial-out", externalDriveWeight: .24, affineLoadMode: "none",
      robustnessPreference: "none", microstructureCouplingMode: "none", loopClosurePreference: "none",
      arrivalPathMode: "radial-outward", arrivalPathWeight: .24, geometricExplorationScale: .15,
      requestedGrowthNuclei: 1, growthScheduling: "commuting", hierarchyEnabled: true },
  },
  impingement: {
    label: "polycrystal impingement", summary: "Four dispersed observed nuclei, pose-interface following, multi-parent loop closure, and simultaneous compatible-front scheduling.",
    settings: { confinement: "box", geometryPreference: "strain", geometricStrainWeight: .16,
      compositionPreference: "soft", chargePreference: "auto", surfacePreference: "soft",
      frontMorphologyMode: "smooth", frontMorphologyWeight: .24, epitaxyTemplateMode: "none",
      externalDriveMode: "none", affineLoadMode: "none", robustnessPreference: "margin", robustnessWeight: .12,
      microstructureCouplingMode: "interface-follow", microstructureCouplingWeight: .24,
      loopClosurePreference: "consensus", loopClosureWeight: .24, arrivalPathMode: "none",
      geometricExplorationScale: .05, requestedGrowthNuclei: 4, growthScheduling: "commuting", hierarchyEnabled: true },
  },
  "pore-fill": {
    label: "constricted-pore filling", summary: "Hard hourglass confinement with concavity filling, coordination healing, and parent-normal arrival accessibility.",
    settings: { confinement: "hourglass", geometryPreference: "strain", geometricStrainWeight: .16,
      compositionPreference: "soft", chargePreference: "auto", surfacePreference: "strong",
      frontMorphologyMode: "smooth", frontMorphologyWeight: .48, epitaxyTemplateMode: "none",
      externalDriveMode: "none", affineLoadMode: "none", robustnessPreference: "margin", robustnessWeight: .24,
      microstructureCouplingMode: "gap-heal", microstructureCouplingWeight: .24,
      loopClosurePreference: "consensus", loopClosureWeight: .12,
      arrivalPathMode: "parent-outward", arrivalPathWeight: .24, geometricExplorationScale: 0,
      requestedGrowthNuclei: 1, growthScheduling: "commuting", hierarchyEnabled: true },
  },
});
const GROWTH_PROTOCOL_CONTROL_IDS = new Set([
  "geometryPreferenceSelect", "strainWeightSelect", "compositionPreferenceSelect", "chargePreferenceSelect",
  "surfacePreferenceSelect", "frontMorphologySelect", "frontMorphologyWeightSelect",
  "epitaxyTemplateSelect", "epitaxyWeightSelect", "externalDriveSelect", "externalDriveWeightSelect",
  "affineLoadSelect", "affineLoadMagnitudeSelect", "robustnessPreferenceSelect", "robustnessWeightSelect",
  "microstructureCouplingSelect", "microstructureCouplingWeightSelect", "loopClosurePreferenceSelect",
  "loopClosureWeightSelect", "arrivalPathSelect", "arrivalPathWeightSelect", "explorationScaleSelect",
  "growthNucleiSelect", "growthSchedulingSelect",
]);

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

function referenceEntityLabel(count = referenceCount()) {
  return `${count.toLocaleString()} ${currentMaterial()?.averageStructureSites ? "average sites" : "atoms"}`;
}

function currentImportedFrame() {
  return importedStructure?.frames?.[importedFrameIndex] || importedStructure;
}

function currentImportedFrameValidation() {
  const frame = currentImportedFrame();
  if (!frame) return importedStructure?.validation || null;
  if (frame === importedStructure) return importedStructure.validation;
  if (!frame.validation) {
    frame.validation = validateStructure({ atoms: frame.atoms, cell: frame.cell, pbc: frame.pbc }, {
      maximumAtoms: 1200,
      maximumFrames: 1,
    });
  }
  return frame.validation;
}

function activeImportedFrameValidation() {
  return scenarioSelect.value === "imported" ? currentImportedFrameValidation() : null;
}

function importedTrajectoryFrames() {
  return importedStructure?.frames?.length ? importedStructure.frames : importedStructure ? [importedStructure] : [];
}

function evidenceFrameCount() {
  return scenarioSelect.value === "imported" && ensembleEvidenceMode === "all"
    ? importedTrajectoryFrames().length || 1 : 1;
}

function activeMeasurementConditions() {
  if (scenarioSelect.value !== "imported") return currentMaterial()?.recordedMeasurementConditions || null;
  if (!importedStructure) return null;
  return currentImportedFrame()?.metadata?.measurementConditions
    || importedStructure.metadata?.measurementConditions || null;
}

function formatRecordedCondition(value) {
  if (!Number.isFinite(Number(value))) return null;
  return Number(Number(value).toPrecision(7)).toLocaleString(undefined, { maximumFractionDigits: 6 });
}

function renderMeasurementConditions() {
  const conditions = activeMeasurementConditions();
  const records = [
    conditions?.temperature ? {
      text: `T ${formatRecordedCondition(conditions.temperature.value)} ${conditions.temperature.unit || "K"}${conditions.temperature.deprecatedFallback ? " · legacy tag" : ""}`,
      title: conditions.temperature.sourceTag,
    } : null,
    conditions?.pressure ? {
      text: `P ${formatRecordedCondition(conditions.pressure.value)} ${conditions.pressure.unit || "kPa"}${conditions.pressure.deprecatedFallback ? " · legacy tag" : ""}`,
      title: conditions.pressure.sourceTag,
    } : null,
    conditions?.environment?.value ? {
      text: `environment ${conditions.environment.value}`,
      title: conditions.environment.sourceTag,
    } : null,
  ].filter(Boolean);
  measurementConditions.hidden = records.length === 0;
  measurementConditionChips.replaceChildren();
  records.forEach((record) => {
    const chip = document.createElement("span");
    chip.textContent = record.text;
    chip.title = record.title || "recorded condition";
    measurementConditionChips.append(chip);
  });
}

function renderPublishedFixtureProvenance() {
  const provenance = currentMaterial()?.fixtureProvenance;
  publishedFixtureProvenance.hidden = !provenance;
  if (!provenance) return;
  publishedFixtureLicense.textContent = provenance.license;
  const atomCount = provenance.atoms?.length || provenance.atomCount;
  publishedFixtureName.textContent = `${provenance.name}${provenance.countLabel ? ` · ${provenance.countLabel}` : atomCount ? ` · ${atomCount.toLocaleString()} physical atoms` : ""}`;
  publishedFixtureArticle.href = `https://doi.org/${provenance.articleDoi}`;
  publishedFixtureArticle.textContent = "article DOI";
  publishedFixtureArchive.href = provenance.sourceUrl || `https://doi.org/${provenance.archiveDoi}`;
  publishedFixtureArchive.textContent = provenance.sourceUrl ? "source CIF" : "immutable archive";
}

function syncImportedFrameMaterial() {
  if (!importedStructure?.material) return;
  const frame = currentImportedFrame();
  const validation = currentImportedFrameValidation();
  importedStructure.material.spacingA = validation.medianNearestDistance;
  importedStructure.material.cell = frame.cell
    ? `${importedStructure.format} frame ${importedFrameIndex + 1} cell · V=${validation.cellVolume.toFixed(2)} Å³`
    : `${importedStructure.format} frame ${importedFrameIndex + 1} · non-periodic`;
}

function renderEnsembleControls() {
  renderMeasurementConditions();
  renderPublishedFixtureProvenance();
  const frames = importedTrajectoryFrames();
  const visible = scenarioSelect.value === "imported" && frames.length > 1;
  ensembleControls.hidden = !visible;
  if (!visible) return;
  importedFrameIndex = Math.max(0, Math.min(importedFrameIndex, frames.length - 1));
  ensembleFrameSelect.replaceChildren();
  frames.forEach((frame, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    const label = frame.name || frame.comment || `frame ${index + 1}`;
    option.textContent = `Frame ${index + 1} · ${label.slice(0, 64)}`;
    ensembleFrameSelect.append(option);
  });
  ensembleFrameSelect.value = String(importedFrameIndex);
  ensembleEvidenceSelect.value = ensembleEvidenceMode;
  ensembleFrameCount.textContent = `${frames.length} snapshots`;
  const presentations = frames.length * (frames[0]?.atoms.length || 0);
  const empirical = ensemblePairDistanceUncertainty?.available
    && ensemblePairDistanceUncertainty.frameCount === frames.length
    ? ` · local pair σ₉₀ ${ensemblePairDistanceUncertainty.upperPairDistanceSigma.toFixed(4)} Å`
    : "";
  ensembleStatus.textContent = ensembleEvidenceMode === "all"
    ? `Pooling ${frames.length} fixed-topology frames · ${presentations.toLocaleString()} atom presentations${empirical}. Frame ${importedFrameIndex + 1} alone supplies the cluster cover, grammar, and growth seed.`
    : `Ablation: only frame ${importedFrameIndex + 1} supplies geometric envelopes, the cluster cover, grammar, and growth seed.`;
}

function currentMaterial() {
  if (scenarioSelect.value === "imported" && importedStructure) return importedStructure.material;
  const material = MATERIALS[scenarioSelect.value];
  if (scenarioSelect.value !== "iceVI" || !iceViMicrostate) return material;
  return {
    ...material,
    name: "ice VI · sampled D₂O microstate",
    cell: "tetragonal ice VI · one geometry-valid occupational realization",
    audit: "geometry-only ice-rule realization + molecular/connection/gap cover",
    averageStructureSites: false,
    occupancyWeightedAtomCount: null,
    growthWithheld: false,
    crystallographicOccupancy: {
      ...material.crystallographicOccupancy,
      representation: "one sampled 240-atom D₂O realization derived from the 400-site diffraction average",
      partialSites: 0,
      totalVacancyFraction: 0,
      realizationSeed: iceViMicrostate.audit.seed,
      realizationMethod: iceViMicrostate.audit.method,
    },
    fixtureProvenance: {
      ...material.fixtureProvenance,
      name: "proton-disordered D₂O ice VI · sampled ice-rule microstate",
      countLabel: "240 realized atoms · derived from 400 average sites",
    },
    note: "A deterministic Euler orientation of the measured four-connected oxygen graph selects one of each paired D/Vac alternatives. The realization obeys two D per oxygen and one D per O–O bond; it is a sampled microstate, not a refinement claim.",
  };
}

function renderIceViMicrostateControls() {
  const visible = scenarioSelect.value === "iceVI";
  iceViMicrostateControls.hidden = !visible;
  if (!visible) return;
  if (!iceViMicrostate) {
    iceViAverageButton.hidden = true;
    iceViMicrostateState.textContent = "diffraction average · unresolved";
    iceViMicrostateButton.textContent = "Sample one geometry-valid D₂O microstate";
    iceViMicrostateStatus.textContent = "Uses only the paired D/Vac positions and the four-connected oxygen network: one D per O–O bond and two covalent D per oxygen.";
    return;
  }
  const audit = iceViMicrostate.audit;
  iceViAverageButton.hidden = false;
  iceViMicrostateState.textContent = `sample ${audit.seed} · ${audit.realizedAtoms} atoms`;
  iceViMicrostateButton.textContent = "Sample a different ice-rule microstate";
  iceViMicrostateStatus.textContent = `${audit.oxygenAtoms} O · ${audit.selectedDeuteriumAtoms} D · ${audit.oxygenBonds} hydrogen bonds · ${audit.connectedOxygenNetworks} interpenetrating networks. Both ice rules pass; the reported cell supplies minimum images, while no energy or potential selects the state.`;
}

function currentRecursiveBenchmark() {
  const benchmark = RECURSIVE_BENCHMARKS[scenarioSelect.value] || RECURSIVE_BENCHMARKS.imported;
  if (scenarioSelect.value !== "iceVI" || !iceViMicrostate) return benchmark;
  return {
    hierarchy: ["5 D₂O conformers", "84 typed ports", "pose alternatives"],
    curve: [23, 4, 3, 1],
    mark: "two-parent O-anchor consensus",
    action: "8 exact O anchors · poses unresolved",
    speed: "4 → 3 → 1 exact · finite fixed point",
    gate: "O framework pass · occupational pose red",
    status: "limit",
    note: "The diffraction average remains unchanged in provenance. A geometry-only Euler orientation selects one reproducible 240-atom occupational microstate with two covalent D per oxygen and one D per O–O bond; molecular, bridge, and O₄ gap clusters are learned from that realization. Separately, a sealed positions-only audit learns five D₂O metric conformers and 84 proper-SE(3) ports. A training-selected two-parent consensus emits eight exact oxygen anchors across three self-fed waves on a disjoint microstate. All eight D₂O orientations remain mutually exclusive alternatives, and forced whole-molecule continuation produces three wrong sites. No kinetics, stationary rule, exponential growth, or experimental instantaneous configuration is claimed.",
  };
}

function updateRecursiveBenchmark() {
  const benchmark = currentRecursiveBenchmark();
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
    bar.title = `action ${index}: ${count.toLocaleString()} ${currentMaterial().averageStructureSites ? "average sites" : "atoms"} represented`;
    const label = document.createElement("span");
    label.textContent = count >= 1e6 ? `${(count / 1e6).toFixed(1)}m` : count >= 1e3 ? `${Math.round(count / 1e3)}k` : String(count);
    bar.appendChild(label);
    recursiveCurve.appendChild(bar);
  });
  recursiveCurve.hidden = benchmark.curve.length === 0;
}

function importSummary(structure, validation) {
  const composition = Object.entries(validation.elementCounts).map(([element, count]) =>
    `${element}${Number.isInteger(count) ? count : Number(count.toFixed(3))}`).join(" · ");
  const periodicity = structure.pbc.map((value) => value ? "P" : "–").join("");
  const warnings = validation.warnings.length ? ` · ${validation.warnings.length} warning${validation.warnings.length === 1 ? "" : "s"}` : "";
  const disorder = validation.mixedOccupancySites || validation.partialOccupancySites
    ? ` · ${validation.mixedOccupancySites} mixed / ${validation.partialOccupancySites} partial sites`
    : "";
  const thermal = validation.thermalDisplacementSites
    ? ` · U/B ${validation.thermalDisplacementSites} sites${validation.anisotropicDisplacementSites ? ` · ${validation.anisotropicDisplacementSites} anisotropic` : ""} · σ̃ ${validation.medianThermalSigmaA.toFixed(3)} Å`
    : "";
  const charge = validation.formalChargeCoverage > 0
    ? ` · formal q ${(validation.formalChargeCoverage * 100).toFixed(0)}% · cell ${validation.netFormalCharge >= 0 ? "+" : ""}${Number(validation.netFormalCharge.toFixed(4))}`
    : "";
  const trajectory = validation.trajectoryFrameCount > 1
    ? ` · ${validation.trajectoryFrameCount} fixed-topology frames${validation.trajectoryVariableCell ? " · variable cell" : ""}` : "";
  const recordedConditions = [
    validation.measurementTemperatureKelvin !== null ? `${formatRecordedCondition(validation.measurementTemperatureKelvin)} K` : null,
    validation.measurementPressureKilopascal !== null ? `${formatRecordedCondition(validation.measurementPressureKilopascal)} kPa` : null,
  ].filter(Boolean);
  const conditions = recordedConditions.length ? ` · measured ${recordedConditions.join(" · ")}` : "";
  return `${structure.format} · ${validation.atomCount} sites · ${composition}${disorder}${thermal}${charge}${trajectory}${conditions} · PBC ${periodicity} · dₙₙ ${validation.medianNearestDistance.toFixed(3)} Å${warnings}`;
}

async function importStructureFile(file) {
  importStatus.className = "import-status";
  importStatus.textContent = `Reading ${file.name} locally…`;
  if (file.size > 8 * 1024 * 1024) throw new Error("File exceeds the 8 MB browser import limit");
  return activateImportedStructure(parseStructureText(await file.text(), file.name), file.name);
}

function deterministicSnapshotEnsemble(structure) {
  const phases = [-1, 0, 1];
  const frames = phases.map((phase, frameIndex) => {
    const dilation = 1 + phase * .0015;
    const cell = structure.cell?.map((vector) => vector.map((value) => value * dilation)) || null;
    const atoms = structure.atoms.map((atom, atomIndex) => ({
      ...atom,
      occupancyAlternatives: atom.occupancyAlternatives?.map((entry) => ({ ...entry })),
      position: atom.position.map((value, axis) => value * dilation
        + .018 * Math.sin((atomIndex + 1) * (axis + 2) * 1.173 + frameIndex * 1.91)),
    }));
    return {
      name: `deterministic displaced snapshot ${frameIndex + 1}`,
      comment: `geometry-only NaCl ensemble demo · phase ${phase}`,
      atoms,
      cell,
      pbc: [...structure.pbc],
      metadata: { frameIndex, deterministicDemonstration: true },
    };
  });
  return {
    ...structure,
    name: "NaCl fixed-topology snapshot ensemble",
    atoms: frames[0].atoms,
    cell: frames[0].cell,
    pbc: frames[0].pbc,
    frames,
    metadata: { ...structure.metadata, frameCount: frames.length, deterministicDemonstration: true },
  };
}

function activateImportedStructure(parsed, filename, statusElement = importStatus) {
  const validation = validateStructure(parsed, { maximumAtoms: 1200 });
  if (!validation.valid) throw new Error(validation.errors.join("; "));
  importedFrameIndex = 0;
  ensembleEvidenceMode = "all";
  ensemblePairDistanceUncertainty = null;
  const actualElements = Object.keys(validation.elementCounts);
  const elements = [...new Set(parsed.atoms.map(occupancyChemistryToken))];
  importedStructure = {
    ...parsed, validation, filename,
    material: {
      name: parsed.name || filename,
      elements,
      actualElements,
      spacingA: validation.medianNearestDistance,
      cell: parsed.cell ? `${parsed.format} cell · V=${validation.cellVolume.toFixed(2)} Å³` : `${parsed.format} · non-periodic`,
      order: "unclassified input",
      symmetry: parsed.metadata?.spaceGroupNumber
        ? `${parsed.metadata.spaceGroup || "space group"} · #${parsed.metadata.spaceGroupNumber}`
        : parsed.metadata?.spaceGroup || "not supplied",
      audit: "emergent structure audit",
      note: `Imported from ${filename}; no structure class, space group, or cluster vocabulary is supplied to growth. Mixed and partial sites remain occupational alternatives rather than coincident atoms or a silently selected element. Supplied formal oxidation states remain chemistry channels; missing states are never guessed.`,
    },
  };
  syncImportedFrameMaterial();
  elements.forEach(elementRecord);
  const option = scenarioSelect.querySelector('option[value="imported"]');
  option.disabled = false;
  option.textContent = `Imported · ${importedStructure.material.name}`;
  scenarioSelect.value = "imported";
  renderEnsembleControls();
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
  // Preserve a translation-invariant, physically contiguous observation
  // window. Sampling by insertion order tears apart neighbor shells; sampling
  // around the global origin would make a coordinate frame part of the label.
  return centeredStructuralWindow(source, Math.min(ANALYSIS_WINDOW_COUNT, Math.max(1, source.length)));
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
  if (pipelineStage < 4 || currentMaterial().growthWithheld) return {
    order: "not classified", structure: currentMaterial().growthWithheld ? "occupational realization unresolved" : "classification begins after growth", symmetry: "withheld", confidence: 0,
    sampleAtoms: 0, liveAtoms: 0, minimumAtoms: PHASE_CLASSIFICATION_MINIMUM_ATOMS,
    historyKey: "withheld", posthocOnly: true, usedAsGrowthInput: false,
    independentPhaseDetermination: false, classificationThreshold: PHASE_CLASSIFICATION_THRESHOLD,
    note: currentMaterial().growthWithheld
      ? "The diffraction-average occupancy does not define one instantaneous material realization. Phase classification and growth remain withheld until a valid occupational microstate or ensemble representation is supplied."
      : "The supplied configuration is used to learn geometry, not to preassign a phase. RDF, coordination, S(q), translation closure, and prototype labels are evaluated only after Material Growth begins.",
  };
  const availableSource = classificationSample();
  if (availableSource.length < PHASE_CLASSIFICATION_MINIMUM_ATOMS) return {
    order: "insufficient sample", structure: "—", symmetry: "—", confidence: 0,
    sampleAtoms: availableSource.length, liveAtoms: atoms.length, minimumAtoms: PHASE_CLASSIFICATION_MINIMUM_ATOMS,
    historyKey: `insufficient:${availableSource.length}:${atoms.length}`, posthocOnly: true, usedAsGrowthInput: false,
    independentPhaseDetermination: false, classificationThreshold: PHASE_CLASSIFICATION_THRESHOLD,
    note: `Waiting for at least ${PHASE_CLASSIFICATION_MINIMUM_ATOMS} live atoms; ${availableSource.length} are currently available.`,
  };
  const library = getOrderPrototypeLibrary();
  const matchedAtomCount = Math.min(availableSource.length, ...library.map((prototype) => prototype.source.length));
  const source = centeredStructuralWindow(availableSource, matchedAtomCount);
  const dimensionAudit = inferPointSetDimension(source);
  const comparisonRadius = phaseComparisonRadius(source.length, dimensionAudit.dimension);
  const key = `${scenarioSelect.value}:${pipelineStage}:${Math.floor(source.length / 16)}:${Math.floor(atoms.length / 96)}:${dimensionAudit.dimension}:${comparisonRadius.toFixed(3)}`;
  if (liveOrderCache.key === key && liveOrderCache.result) return liveOrderCache.result;
  const stats = calculateStructuralStats(source, referenceSpacing, false, dimensionAudit.dimension, comparisonRadius);
  const matches = library.map((prototype) => {
    const prototypeStats = matchedPrototypeStats(prototype, source.length, comparisonRadius);
    const rdfError = normalizedDistributionDistance(prototypeStats.rdf, stats.rdf);
    const coordinationError = normalizedDistributionDistance(prototypeStats.coordination, stats.coordination);
    const structureFactorError = normalizedDistributionDistance(
      ensureStructureFactor(prototypeStats).values, ensureStructureFactor(stats).values);
    return {
      ...prototype, stats: prototypeStats, rdfError, coordinationError, structureFactorError,
      evidenceMatch: Math.max(0, Math.min(1,
        1 - .30 * rdfError - .58 * coordinationError - .20 * structureFactorError)),
    };
  }).sort((first, second) => second.evidenceMatch - first.evidenceMatch);
  const best = matches[0];
  const runnerUp = matches[1] || best;
  const independentMatches = matches.filter((match) => match.id !== scenarioSelect.value);
  const independentBest = independentMatches[0] || best;
  const independentRunnerUp = independentMatches[1] || independentBest;
  const independentPrototypeMargin = Math.max(0, independentBest.evidenceMatch - independentRunnerUp.evidenceMatch);
  const bestCrystal = matches.find((match) => match.material.order === "crystal");
  const runnerUpCrystal = matches.find((match) => match.material.order === "crystal" && match.id !== bestCrystal?.id) || bestCrystal;
  const evidenceMatch = best.evidenceMatch;
  const prototypeMargin = Math.max(0, best.evidenceMatch - runnerUp.evidenceMatch);
  const bestPrototypeResolved = best.evidenceMatch >= .45 && prototypeMargin >= .02;
  const crystalPrototypeMargin = Math.max(0, (bestCrystal?.evidenceMatch || 0) - (runnerUpCrystal?.evidenceMatch || 0));
  const crystalPrototypeResolved = Boolean(bestCrystal && bestCrystal.evidenceMatch >= .45 && crystalPrototypeMargin >= .02);
  const translationClosure = pipelineStage === 4 && detectedUnitCell
    ? translationClosureScore(source, detectedUnitCell.basis) : 0;
  const sampleStrength = Math.max(0, Math.min(1, (source.length - 24) / 144));
  let confidence = evidenceMatch * (.48 + .52 * sampleStrength);
  const accepted = confidence >= PHASE_CLASSIFICATION_THRESHOLD;
  let order = "undetermined";
  let structure = bestPrototypeResolved ? `closest: ${best.material.name}` : "prototype unresolved";
  let symmetry = "not assigned";
  if (translationClosure >= .24 && bestCrystal) {
    order = "crystal";
    structure = crystalPrototypeResolved ? bestCrystal.material.name : "periodic crystal · prototype unresolved";
    symmetry = crystalPrototypeResolved ? bestCrystal.material.symmetry : "translation group detected · point group unresolved";
    confidence = Math.max(confidence, Math.min(.98, .58 + .42 * translationClosure));
  } else if (accepted && bestPrototypeResolved && best.material.order === "crystal") {
    order = "crystal";
    structure = best.material.name;
    symmetry = best.material.symmetry;
  } else if (accepted && bestPrototypeResolved && best.material.order === "quasicrystal") {
    order = confidence >= .74 ? (best.id === "moire" ? "2D quasiperiodic bilayer" : "icosahedral quasicrystal") : "quasicrystal candidate";
    structure = best.material.name;
    symmetry = best.material.symmetry;
  } else if (accepted && bestPrototypeResolved && best.material.order === "amorphous") {
    order = "amorphous solid";
    structure = best.material.name;
    symmetry = "no global space group";
  }
  const result = {
    order, structure, symmetry, confidence,
    sampleAtoms: source.length,
    liveAtoms: atoms.length,
    availableAnalysisAtoms: availableSource.length,
    minimumAtoms: PHASE_CLASSIFICATION_MINIMUM_ATOMS,
    inferredDimension: dimensionAudit.dimension,
    planarityRatio: dimensionAudit.planarityRatio,
    localPlanarityRatio: dimensionAudit.localPlanarityRatio,
    dimensionInferenceBasis: dimensionAudit.basis,
    comparisonRadius,
    matchedPrototypeAtomCount: matchedAtomCount,
    bestPrototypeId: best.id,
    bestPrototypeName: best.material.name,
    bestPrototypeEvidenceMatch: best.evidenceMatch,
    runnerUpPrototypeId: runnerUp.id,
    runnerUpPrototypeName: runnerUp.material.name,
    runnerUpPrototypeEvidenceMatch: runnerUp.evidenceMatch,
    prototypeMargin,
    independentBestPrototypeId: independentBest.id,
    independentBestPrototypeName: independentBest.material.name,
    independentBestPrototypeOrder: independentBest.material.order,
    independentBestPrototypeEvidenceMatch: independentBest.evidenceMatch,
    independentRunnerUpPrototypeId: independentRunnerUp.id,
    independentPrototypeMargin,
    bestPrototypeResolved,
    crystalPrototypeMargin,
    crystalPrototypeResolved,
    rdfError: best.rdfError,
    coordinationError: best.coordinationError,
    structureFactorError: best.structureFactorError,
    translationClosure,
    prototypeLibrarySize: matches.length,
    selectedFixturePresentInPrototypeLibrary: matches.some((match) => match.id === scenarioSelect.value),
    historyKey: key,
    posthocOnly: true,
    usedAsGrowthInput: false,
    independentPhaseDetermination: false,
    classificationThreshold: PHASE_CLASSIFICATION_THRESHOLD,
    note: `Matched ${source.length}-atom, ${dimensionAudit.dimension}D windows at r≤${comparisonRadius.toFixed(2)}a; dimension basis: ${dimensionAudit.basis}. ${bestPrototypeResolved ? `Best RDF + coordination + geometric powder S(q) prototype is ${best.material.name} (${Math.round(best.evidenceMatch * 100)}%; ${Math.round(prototypeMargin * 100)}-point margin over ${runnerUp.material.name})` : `No RDF + coordination + geometric powder S(q) prototype separates from the runner-up (top score ${Math.round(best.evidenceMatch * 100)}%; margin ${Math.round(prototypeMargin * 100)} points)`}; leaving the selected fixture out gives ${independentBest.material.name} at ${Math.round(independentBest.evidenceMatch * 100)}%${detectedUnitCell ? `; translation closure ${Math.round(translationClosure * 100)}%` : ""}. Unit-scattering S(q) is posthoc evidence—not experimental intensity or a growth input. ${best.material.audit} remains the required independent confirmation; this diagnostic prototype comparison is not an independent phase determination.`,
  };
  liveOrderCache = { key, result };
  return result;
}

function phaseTrajectoryColor(order) {
  if (order === "crystal") return "#65e1bc";
  if (order.includes("quasicrystal") || order.includes("quasiperiodic")) return "#55c8ff";
  if (order === "amorphous solid") return "#e1aa61";
  return "#71857f";
}

function recordLiveOrder(inference) {
  if (pipelineStage !== 4 || currentMaterial().growthWithheld) return;
  const previous = liveOrderHistory[liveOrderHistory.length - 1];
  if (previous?.historyKey === inference.historyKey) return;
  liveOrderHistory.push({
    historyKey: inference.historyKey,
    acceptedDecisions,
    liveAtoms: atoms.length,
    sampleAtoms: inference.sampleAtoms,
    order: inference.order,
    confidence: inference.confidence,
    bestPrototypeId: inference.bestPrototypeId || null,
    bestPrototypeEvidenceMatch: inference.bestPrototypeEvidenceMatch ?? null,
    prototypeMargin: inference.prototypeMargin ?? null,
    independentBestPrototypeId: inference.independentBestPrototypeId || null,
    independentBestPrototypeEvidenceMatch: inference.independentBestPrototypeEvidenceMatch ?? null,
    translationClosure: inference.translationClosure ?? null,
  });
  if (liveOrderHistory.length > 96) {
    const first = liveOrderHistory[0];
    liveOrderHistory = [first, ...liveOrderHistory.slice(1).filter((_, index) => index % 2 === 1)];
  }
}

function drawPhaseTrajectory() {
  const context = phaseTrajectoryCanvas.getContext("2d");
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(220, phaseTrajectoryCanvas.clientWidth || 336);
  const height = Math.max(64, phaseTrajectoryCanvas.clientHeight || 70);
  phaseTrajectoryCanvas.width = Math.round(width * ratio);
  phaseTrajectoryCanvas.height = Math.round(height * ratio);
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, width, height);
  const points = liveOrderHistory;
  if (pipelineStage < 4 || currentMaterial().growthWithheld || !points.length) {
    context.fillStyle = "#647a73";
    context.font = "7px ui-monospace, SFMono-Regular, Menlo, monospace";
    context.textAlign = "center";
    const withheld = pipelineStage < 4 || currentMaterial().growthWithheld;
    context.fillText(currentMaterial().growthWithheld ? "classification withheld · occupational state unresolved"
      : pipelineStage < 4 ? "classification withheld until material growth" : "waiting for live atoms", width / 2, height / 2);
    phaseTrajectoryState.textContent = withheld ? "withheld" : "waiting";
    phaseTrajectoryCanvas.setAttribute("aria-label", withheld
      ? currentMaterial().growthWithheld ? "Phase confidence is withheld because the occupational state is unresolved"
        : "Phase confidence is withheld until material growth begins"
      : "Phase confidence trajectory is waiting for live atoms");
    return;
  }
  const margin = { left: 24, right: 5, top: 6, bottom: 14 };
  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;
  const atomMinimum = Math.min(...points.map((point) => point.liveAtoms));
  const atomMaximum = Math.max(...points.map((point) => point.liveAtoms));
  const x = (point, index) => margin.left + (atomMaximum === atomMinimum
    ? (points.length === 1 ? .5 : index / (points.length - 1))
    : (point.liveAtoms - atomMinimum) / (atomMaximum - atomMinimum)) * plotWidth;
  const y = (confidence) => margin.top + (1 - Math.max(0, Math.min(1, confidence))) * plotHeight;
  context.strokeStyle = "rgba(130,158,149,.18)";
  context.lineWidth = 1;
  [0, .5, 1].forEach((value) => {
    context.beginPath(); context.moveTo(margin.left, y(value)); context.lineTo(width - margin.right, y(value)); context.stroke();
  });
  context.setLineDash([3, 3]);
  context.strokeStyle = "rgba(181,148,255,.55)";
  context.beginPath(); context.moveTo(margin.left, y(PHASE_CLASSIFICATION_THRESHOLD)); context.lineTo(width - margin.right, y(PHASE_CLASSIFICATION_THRESHOLD)); context.stroke();
  context.setLineDash([]);
  for (let index = 1; index < points.length; index++) {
    context.strokeStyle = phaseTrajectoryColor(points[index].order);
    context.lineWidth = 1.5;
    context.beginPath(); context.moveTo(x(points[index - 1], index - 1), y(points[index - 1].confidence)); context.lineTo(x(points[index], index), y(points[index].confidence)); context.stroke();
  }
  points.forEach((point, index) => {
    context.fillStyle = phaseTrajectoryColor(point.order);
    context.beginPath(); context.arc(x(point, index), y(point.confidence), index === points.length - 1 ? 2.5 : 1.5, 0, TAU); context.fill();
  });
  context.fillStyle = "#71857f";
  context.font = "6px ui-monospace, SFMono-Regular, Menlo, monospace";
  context.textAlign = "right";
  context.fillText("100", margin.left - 3, y(1) + 2);
  context.fillText("0", margin.left - 3, y(0) + 2);
  context.textAlign = "left";
  context.fillText(`${atomMinimum} atoms`, margin.left, height - 3);
  context.textAlign = "right";
  context.fillText(`${atomMaximum} atoms`, width - margin.right, height - 3);
  const latest = points[points.length - 1];
  phaseTrajectoryState.textContent = `${points.length} reads · ${Math.round(latest.confidence * 100)}%`;
  phaseTrajectoryCanvas.setAttribute("aria-label", `Phase confidence trajectory with ${points.length} post-growth reads from ${atomMinimum} to ${atomMaximum} live atoms; latest classification ${latest.order} at ${Math.round(latest.confidence * 100)} percent confidence`);
}

function updateOrderAudit() {
  const inference = inferLiveOrder();
  recordLiveOrder(inference);
  orderClassValue.textContent = inference.order;
  structureNameValue.textContent = inference.structure;
  symmetryValue.textContent = inference.symmetry;
  confidenceValue.textContent = `${Math.round(inference.confidence * 100)}%`;
  phaseWindowValue.textContent = pipelineStage < 4 || currentMaterial().growthWithheld ? "withheld" : `${inference.sampleAtoms}/${ANALYSIS_WINDOW_COUNT}`;
  phaseMarginValue.textContent = inference.prototypeMargin === undefined ? "—" : `+${Math.round(inference.prototypeMargin * 100)} pt`;
  phaseIndependentValue.textContent = inference.independentBestPrototypeEvidenceMatch === undefined
    ? "—" : `${inference.independentBestPrototypeOrder} ${Math.round(inference.independentBestPrototypeEvidenceMatch * 100)}%`;
  phaseClosureValue.textContent = inference.translationClosure === undefined ? "—" : `${Math.round(inference.translationClosure * 100)}%`;
  auditNote.textContent = inference.note;
  drawPhaseTrajectory();
}

function getElementMaterial(symbol, dim = false) {
  const cache = dim ? dimElementMaterials : elementMaterials;
  if (!cache.has(symbol)) {
    const data = elementRecord(symbol);
    cache.set(symbol, new THREE.MeshStandardMaterial({
      color: data.color,
      roughness: dim ? .55 : .3,
      metalness: dim ? 0 : .14,
      transparent: dim || data.opacity < .999,
      opacity: dim ? .1 : data.opacity ?? 1,
      depthWrite: !dim && !(data.opacity < .999),
      emissive: dim ? 0x000000 : data.color,
      emissiveIntensity: dim ? 0 : .16,
    }));
  }
  return cache.get(symbol);
}

function occupationalAlternatives(symbol) {
  const source = importedStructure?.atoms?.find((atom) => occupancyChemistryToken(atom) === symbol);
  if (source) return {
    alternatives: source.occupancyAlternatives,
    total: source.occupancyTotal ?? source.occupancy ?? 1,
    label: occupancyDisplayLabel(source),
  };
  const match = String(symbol).match(/^occ\[(.*)]$/);
  if (!match) return null;
  const records = match[1].split(";").map((entry) => entry.split("="))
    .filter(([species]) => species !== "Vac")
    .map(([species, fraction]) => ({ species, fraction: Number(fraction) }));
  const total = records.reduce((sum, entry) => sum + entry.fraction, 0);
  return { alternatives: records, total, label: match[1].replaceAll(";", " / ").replaceAll("=", " ") };
}

function elementRecord(symbol) {
  if (ELEMENTS[symbol]) return ELEMENTS[symbol];
  const occupational = occupationalAlternatives(symbol);
  if (occupational?.alternatives.length) {
    const mixed = occupational.alternatives.reduce((color, entry) => {
      const component = new THREE.Color(elementRecord(entry.species).color);
      color.r += component.r * entry.fraction;
      color.g += component.g * entry.fraction;
      color.b += component.b * entry.fraction;
      return color;
    }, new THREE.Color(0, 0, 0));
    const vacancy = Math.max(0, 1 - occupational.total);
    mixed.r += .18 * vacancy; mixed.g += .22 * vacancy; mixed.b += .22 * vacancy;
    const radius = occupational.alternatives.reduce((sum, entry) => sum + elementRecord(entry.species).radius * entry.fraction, 0)
      / Math.max(occupational.total, 1e-8);
    const color = mixed.getHex();
    ELEMENTS[symbol] = {
      color, css: `#${color.toString(16).padStart(6, "0")}`, radius,
      opacity: .58 + .42 * occupational.total,
      occupancy: occupational,
    };
    return ELEMENTS[symbol];
  }
  let hash = 0;
  for (const character of symbol) hash = Math.imul(hash ^ character.charCodeAt(0), 0x45d9f3b);
  const color = new THREE.Color().setHSL(((hash >>> 0) % 360) / 360, .58, .62).getHex();
  ELEMENTS[symbol] = { color, css: `#${color.toString(16).padStart(6, "0")}`, radius: 1.35 };
  return ELEMENTS[symbol];
}

function occupancyRingDescriptor(atom) {
  const occupational = occupationalAlternatives(atom.species);
  if (!occupational || (occupational.alternatives.length < 2 && occupational.total >= .999999)) return null;
  const secondary = occupational.alternatives[1]?.species || "vacancy";
  const color = secondary === "vacancy" ? 0xb5cbc5 : elementRecord(secondary).color;
  return { key: `${secondary}:${occupational.total.toFixed(6)}`, color };
}

function occupancyRingMaterial(descriptor) {
  if (!occupancyRingMaterials.has(descriptor.key)) occupancyRingMaterials.set(descriptor.key,
    new THREE.MeshBasicMaterial({ color: descriptor.color, transparent: true, opacity: .88, depthWrite: false }));
  return occupancyRingMaterials.get(descriptor.key);
}

function materialElementLabels(material = currentMaterial()) {
  return material.elements.map((symbol) => occupationalAlternatives(symbol)?.label || symbol);
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
    const label = learnedCover?.molecular
      ? [learnedCover.molecular.waterLabel || "molecule", "bridge", "O₆ gap"][index] || `C${index + 1}`
      : `C${index + 1}`;
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
    rdfStatus.title = "Debye-style finite-window powder average of mean positions with unit atom weights. It omits X-ray form factors, neutron scattering lengths, occupancy-weighted scattering, Debye–Waller intensity damping, and instrument response.";
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
      : `Known ${referenceEntityLabel()}; ${liveWindowLabel} ${live.count}.`;
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

function makeIceViiiReferenceConfiguration() {
  const observation = generateIceViiiObservation();
  const center = new THREE.Vector3(
    observation.cell[0][0] / 2,
    observation.cell[1][1] / 2,
    observation.cell[2][2] / 2,
  );
  const scale = .92 / MATERIALS.iceVIII.spacingA;
  return observation.atoms.map((atom, sourceIndex) => {
    const pA = new THREE.Vector3(...atom.position);
    return {
      pA,
      p: pA.clone().sub(center).multiplyScalar(scale),
      species: atom.species,
      displaySpecies: atom.species,
      family: "published-ice-viii",
      sourceIndex,
      q: atom.q.slice(),
    };
  }).sort((first, second) => first.p.lengthSq() - second.p.lengthSq()
    || first.species.localeCompare(second.species) || first.sourceIndex - second.sourceIndex);
}

function makeIceViAverageReferenceConfiguration(observation = generateIceViAverageObservation()) {
  const center = new THREE.Vector3(
    observation.cell[0][0] / 2,
    observation.cell[1][1] / 2,
    observation.cell[2][2] / 2,
  );
  const scale = .92 / MATERIALS.iceVI.spacingA;
  return observation.atoms.map((atom, sourceIndex) => {
    const pA = new THREE.Vector3(...atom.position);
    const site = { species: atom.species, occupancy: atom.occupancy,
      occupancyAlternatives: atom.occupancyAlternatives.map((entry) => ({ ...entry })) };
    const resolved = Boolean(observation.audit);
    return {
      pA,
      p: pA.clone().sub(center).multiplyScalar(scale),
      species: resolved ? atom.species : occupancyChemistryToken(site),
      displaySpecies: atom.species,
      occupancyLabel: resolved ? null : occupancyDisplayLabel(site),
      occupancyAlternatives: site.occupancyAlternatives,
      occupancy: atom.occupancy,
      uIsoA2: atom.uIsoA2,
      thermalSigmaA: Math.sqrt(atom.uIsoA2),
      family: resolved ? "published-ice-vi-realization" : "published-ice-vi-average",
      sourceIndex,
      q: atom.q.slice(),
      occupationalRealizationSeed: resolved ? observation.audit.seed : null,
    };
  }).sort((first, second) => first.p.lengthSq() - second.p.lengthSq()
    || first.species.localeCompare(second.species) || first.sourceIndex - second.sourceIndex);
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

function makeImportedFrameReference(frame = currentImportedFrame(), sceneScale = null) {
  if (!frame?.atoms?.length) return [];
  const validation = frame === currentImportedFrame() ? currentImportedFrameValidation()
    : frame.validation || validateStructure({ atoms: frame.atoms, cell: frame.cell, pbc: frame.pbc }, { maximumAtoms: 1200, maximumFrames: 1 });
  if (!frame.validation && frame !== importedStructure) frame.validation = validation;
  if (!validation?.valid) throw new Error(validation?.errors?.join("; ") || "Imported frame is invalid");
  const center = frame.atoms.reduce((sum, atom) => sum.add(new THREE.Vector3(...atom.position)), new THREE.Vector3())
    .multiplyScalar(1 / frame.atoms.length);
  const scale = sceneScale ?? .92 / validation.medianNearestDistance;
  return frame.atoms.map((atom, sourceIndex) => {
      const pA = new THREE.Vector3(...atom.position);
      return {
        pA, p: pA.clone().sub(center).multiplyScalar(scale),
        species: occupancyChemistryToken(atom), displaySpecies: atom.species,
        occupancyLabel: occupancyDisplayLabel(atom),
        occupancyAlternatives: atom.occupancyAlternatives?.map((entry) => ({ ...entry })) || [{ species: atom.species, fraction: atom.occupancy ?? 1 }],
        occupancy: atom.occupancyTotal ?? atom.occupancy ?? 1,
        formalCharge: atom.formalCharge ?? null,
        uIsoA2: atom.uIsoA2 ?? null,
        thermalSigmaA: atom.thermalSigmaA ?? null,
        uAnisoCartesianA2: atom.uAnisoCartesianA2?.map((row) => row.slice()) || null,
        thermalSigmaAxesA: atom.thermalSigmaAxesA?.slice() || null,
        thermalAxesCartesian: atom.thermalAxesCartesian?.map((axis) => axis.slice()) || null,
        family: "imported", sourceIndex,
      };
    }).sort((first, second) => first.p.lengthSq() - second.p.lengthSq()
      || first.species.localeCompare(second.species) || first.sourceIndex - second.sourceIndex);
}

function makeReferenceConfiguration(scenario = scenarioSelect.value) {
  if (scenario === "imported" && importedStructure) return makeImportedFrameReference();
  if (MATERIALS[scenario]?.icePolytype) return makeIceReferenceConfiguration(MATERIALS[scenario].icePolytype);
  if (MATERIALS[scenario]?.molecularFixture === "ice-viii-cod-1566658") return makeIceViiiReferenceConfiguration();
  if (MATERIALS[scenario]?.molecularFixture === "ice-vi-cod-1567346-average") {
    return makeIceViAverageReferenceConfiguration(scenario === scenarioSelect.value && iceViMicrostate
      ? iceViMicrostate : generateIceViAverageObservation());
  }
  if (MATERIALS[scenario]?.molecularFixture === "dry-ice-pa3") return makeDryIceReferenceConfiguration();
  if (MATERIALS[scenario]?.publishedFixture === "cdyb-offcenter-r14") return makeCdYbReferenceConfiguration();
  if (MATERIALS[scenario]?.intrinsicDimension === 2) return makePlanarReferenceConfiguration(scenario);
  if (scenario === "random") return makeMetallicGlassReference();
  const result = [];
  for (let ix = 0; ix < 6; ix++) for (let iy = 0; iy < 6; iy++) for (let iz = 0; iz < 6; iz++) {
    result.push(makeSyntheticReferenceSite(ix - 2.5, iy - 2.5, iz - 2.5, result.length, scenario));
  }
  return result.sort((a, b) => a.p.lengthSq() - b.p.lengthSq());
}

function makeCdYbReferenceConfiguration() {
  const scale = .92 / MATERIALS.cdyb.spacingA;
  return CDYB_BROWSER_FIXTURE.atoms.map(([species, x, y, z], sourceIndex) => {
    const pA = new THREE.Vector3(x, y, z);
    return { pA, p: pA.clone().multiplyScalar(scale), species, family: "published-cdyb", sourceIndex };
  }).sort((first, second) => first.p.lengthSq() - second.p.lengthSq()
    || first.species.localeCompare(second.species) || first.sourceIndex - second.sourceIndex);
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
  if (currentMaterial().molecularFixture === "ice-viii-cod-1566658") {
    const [rx, ry, rz] = ICE_VIII_BROWSER_FIXTURE.repeats;
    const [a, b, c] = ICE_VIII_BROWSER_FIXTURE.cellAngstrom;
    return [new THREE.Vector3(rx * a, 0, 0), new THREE.Vector3(0, ry * b, 0), new THREE.Vector3(0, 0, rz * c)];
  }
  if (currentMaterial().molecularFixture === "ice-vi-cod-1567346-average") {
    const [rx, ry, rz] = ICE_VI_BROWSER_FIXTURE.repeats;
    const [a, b, c] = ICE_VI_BROWSER_FIXTURE.cellAngstrom;
    return [new THREE.Vector3(rx * a, 0, 0), new THREE.Vector3(0, ry * b, 0), new THREE.Vector3(0, 0, rz * c)];
  }
  if (currentMaterial().referenceCellA) {
    const length = currentMaterial().referenceCellA;
    return [new THREE.Vector3(length, 0, 0), new THREE.Vector3(0, length, 0), new THREE.Vector3(0, 0, length)];
  }
  const importedFrame = currentImportedFrame();
  if (scenarioSelect.value === "imported" && importedFrame?.cell) {
    return importedFrame.cell.map((vector) => new THREE.Vector3(...vector));
  }
  const length = 6 * currentMaterial().spacingA;
  return [new THREE.Vector3(length, 0, 0), new THREE.Vector3(0, length, 0), new THREE.Vector3(0, 0, length)];
}

function currentPbc() {
  if (geometryMode === "module" || geometryMode === "offlattice") return [false, false, false];
  if (geometryMode === "lattice") return currentCell() ? [true, true, true] : [false, false, false];
  if (currentMaterial().intrinsicDimension === 2) return [false, false, false];
  if (scenarioSelect.value === "imported" && importedStructure) return currentImportedFrame()?.pbc || [false, false, false];
  return currentMaterial().periodicWindow ? [true, true, true] : [false, false, false];
}

function getOrderPrototypeLibrary() {
  if (orderPrototypeLibrary) return orderPrototypeLibrary;
  orderPrototypeLibrary = Object.entries(MATERIALS).map(([id, material]) => {
    const source = makeReferenceConfiguration(id);
    const spacing = medianNearestSpacing(source);
    const dimensionAudit = inferPointSetDimension(source);
    return { id, material, source, spacing, dimensionAudit, statsByWindow: new Map() };
  });
  return orderPrototypeLibrary;
}

function matchedPrototypeStats(prototype, atomCount, comparisonRadius) {
  const count = Math.min(atomCount, prototype.source.length);
  const key = `${count}:${comparisonRadius.toFixed(4)}`;
  if (!prototype.statsByWindow.has(key)) {
    const source = centeredStructuralWindow(prototype.source, count);
    prototype.statsByWindow.set(key, calculateStructuralStats(source, prototype.spacing, false,
      prototype.dimensionAudit.dimension, comparisonRadius));
  }
  return prototype.statsByWindow.get(key);
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

function classifyPlacementPoseOrbits(placements) {
  return classifyProperPoseOrbits(placements.map((placement) => {
    const vectors = centeredPeriodicSupport(referenceAtoms, placement.support);
    return {
      species: placement.support.map((index) => referenceAtoms[index].species),
      positions: vectors.map((vector) => vector.toArray()),
    };
  }), {
    metricToleranceFraction: effectiveClusterMetricTolerance(),
    angularToleranceRadians: .12,
  });
}

function learnOrientationAtlas() {
  if (!learnedClusters) return [];
  if (learnedCover?.types) return learnedCover.types.map((cluster, clusterIndex) => {
    const placements = learnedCover.placements.filter((placement) => placement.type === cluster.type);
    const orbitModel = classifyPlacementPoseOrbits(placements);
    const poseByCenter = new Map();
    const poseByOccurrence = new Map();
    placements.forEach((placement, occurrenceIndex) => {
      const pose = orbitModel.assignments[occurrenceIndex];
      poseByCenter.set(placement.center, pose);
      poseByOccurrence.set(placement.coverIndex ?? occurrenceIndex, pose);
    });
    return { cluster: clusterIndex, element: cluster.element, occurrences: placements.length,
      orientations: orbitModel.orientations, populations: orbitModel.populations,
      support: orbitModel.support, frameKind: orbitModel.frameKind,
      properSymmetryGaugeCount: orbitModel.properSymmetryGaugeCount,
      globalTranslationInvariant: orbitModel.globalTranslationInvariant,
      commonProperRotationEquivariant: orbitModel.commonProperRotationEquivariant,
      improperRotationsQuotiented: orbitModel.improperRotationsQuotiented,
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

function learnMicrostructureEvidence() {
  const gallery = clusterGalleryTypes();
  const types = gallery.map((type, index) => ({
    id: index,
    residual: Boolean(type.residual),
    gap: Boolean(type.gap),
  }));
  const classByPlacement = new Map();
  const poseByPlacement = new Map();
  gallery.forEach((cluster, classIndex) => {
    const placementIndices = clusterPlacementIndices(cluster);
    const orbitModel = classifyPlacementPoseOrbits(placementIndices
      .map((index) => learnedCover.placements[index]).filter(Boolean));
    placementIndices.forEach((placementIndex, occurrenceIndex) => {
      classByPlacement.set(placementIndex, classIndex);
      poseByPlacement.set(placementIndex, orbitModel.assignments[occurrenceIndex] ?? null);
    });
  });
  return auditGeometricMicrostructure({
    atoms: referenceAtoms.map((atom, index) => ({
      chemistryToken: atom.species,
      coordination: learnedClusters.environments[index]?.coordination ?? 0,
    })),
    placements: learnedCover.placements.map((placement, placementIndex) => ({
      type: classByPlacement.get(placementIndex),
      support: placement.support.slice(),
      centerPosition: referenceAtoms[placement.center].p.toArray(),
      pose: poseByPlacement.get(placementIndex) ?? null,
    })),
    types,
    adjacencyReach: 2.5 * referenceSpacing,
  });
}

function poseAtlasEntryStatus(entry) {
  if (entry.support) return entry.support;
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

function clusterMetricTolerance() {
  return clusterToleranceMode === "strict" ? .01 : clusterToleranceMode === "thermal" ? .05 : .025;
}

function measuredPairUncertaintyAngstrom() {
  const sigma = activeImportedFrameValidation()?.medianThermalSigmaA || 0;
  const crystallographic = isotropicPairDistanceUncertaintyA(sigma);
  const ensemble = ensemblePairDistanceUncertainty?.upperPairDistanceSigma || 0;
  return Math.max(crystallographic, ensemble);
}

function measuredPairUncertaintySource() {
  const sigma = activeImportedFrameValidation()?.medianThermalSigmaA || 0;
  const crystallographic = isotropicPairDistanceUncertaintyA(sigma);
  const ensemble = ensemblePairDistanceUncertainty?.upperPairDistanceSigma || 0;
  if (ensemble > crystallographic && ensemble > 0) return "snapshot pair-distance σ90 floor";
  if (crystallographic > 0) return "measured Uiso/Biso floor";
  return "nominal tolerance";
}

function clusterMetricToleranceAngstrom() {
  return Math.max(referenceSpacingA * clusterMetricTolerance(), measuredPairUncertaintyAngstrom());
}

function effectiveClusterMetricTolerance() {
  return clusterMetricToleranceAngstrom() / Math.max(referenceSpacingA, 1e-9);
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
  const occupational = source.some((atom) => occupationalAlternatives(atom.species));
  const result = discoverFiniteMolecularComponents({
    species: source.map((atom) => atom.species),
    distance: (first, second) => periodicDisplacement(source[first], source[second]).length(),
    descriptorToleranceA: clusterMetricToleranceAngstrom(),
  });
  return occupational ? {
    ...result,
    accepted: false,
    reason: "occupationally disordered sites use the irregular colored-support route",
    occupationalAlternativesPreserved: true,
  } : result;
}

function isHydrogenIsotope(species) {
  return species === "H" || species === "D";
}

function discoveredWaterComponents(discovery) {
  if (!discovery.components.length || discovery.components.some((component) => component.length !== 3)
    || !discovery.types.length || discovery.unsupported?.length) return null;
  const formulas = discovery.types.map((type) => type.formula);
  const isotope = formulas[0].find(([species]) => isHydrogenIsotope(species))?.[0];
  const waterFormula = formulas.every((formula) => formula.length === 2
    && formula.some(([species, count]) => species === isotope && count === 2)
    && formula.some(([species, count]) => species === "O" && count === 1));
  if (!isotope || !waterFormula) return null;
  return {
    ...discovery,
    accepted: true,
    reason: discovery.accepted ? discovery.reason : "recurrent finite water topology with multiple metric conformers",
    waterIsotope: isotope,
    waterLabel: isotope === "D" ? "D₂O" : "H₂O",
    metricConformerTypes: discovery.types.length,
    metricConformerRecurrenceRequired: false,
  };
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
    occupationalAlternativesPreserved: Boolean(discovery.occupationalAlternativesPreserved),
    materialLabelUsed: discovery.materialLabelUsed,
    expectedFormulaUsed: discovery.expectedFormulaUsed,
  };
}

function buildWaterClusterCover(source, molecularDiscovery) {
  const hydrogenSpecies = molecularDiscovery.waterIsotope || "H";
  const waterLabel = molecularDiscovery.waterLabel || "H₂O";
  const oxygen = source.map((atom, index) => atom.species === "O" ? index : -1).filter((index) => index >= 0);
  const waters = [];
  const owner = new Map();
  molecularDiscovery.components.forEach((component) => {
    const oxygenIndex = component.find((index) => source[index].species === "O");
    const bonded = component.filter((index) => source[index].species === hydrogenSpecies)
      .sort((first, second) => first - second);
    if (!Number.isInteger(oxygenIndex) || bonded.length !== 2) return;
    const waterIndex = waters.length;
    const support = [oxygenIndex, ...bonded];
    waters.push({ center: oxygenIndex, support, type: 0, residual: false, kind: `${waterLabel} molecule`, family: "molecule" });
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
    type: 1, residual: false, kind: `${waterLabel}···${waterLabel} bridge`, waterPair: [first, second], family: "bridge",
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
    { type: 0, familyType: 0, medoid: waters[0]?.center || 0, element: waterLabel, shortLabel: waterLabel, label: `${waterLabel} molecule`, geometry: "bent molecular face",
      count: waters.length, visualKind: "molecule", customSupport: waterSupport,
      customVectors: centeredPeriodicSupport(source, waterSupport) },
    { type: 1, familyType: 1, medoid: bridges[0]?.center || 0, element: `2 ${waterLabel}`, shortLabel: "bridge", label: "hydrogen-bond bridge", geometry: "connection polyhedron",
      count: bridges.length, visualKind: "bridge", customSupport: bridgeSupport,
      customVectors: centeredPeriodicSupport(source, bridgeSupport) },
    { type: 2, familyType: 2, medoid: gaps[0]?.center || 0, element: "O₆ void", shortLabel: "O₆ gap", label: "six-water ring void", geometry: "void-boundary polyhedron",
      count: gaps.length, visualKind: "ring", gap: true,
      customSupport: ringSupport,
      customVectors: unwrappedRingSupport(source, waters, gaps[0]?.ring || []) },
  ].filter((type) => type.customSupport.length);
  const exactGalleryTypes = molecularIsometryGallery(source, [waters, bridges, gaps], types);
  const molecularConformers = exactGalleryTypes.filter((type) => type.familyType === 0);
  // A molecule is the recurring topological atom cover. Small measured bond
  // distortions remain finite conformer/pose subtypes for the port grammar;
  // they must not turn one H2O/D2O motif into a wall of separate "clusters".
  const moleculeGalleryType = {
    ...types[0],
    classIndex: 0,
    classCount: 1,
    classPlacementIndices: waters.map((water) => water.coverIndex),
    count: waters.length,
    observedMetricConformers: molecularConformers.length,
    geometry: `bent molecular face · ${molecularConformers.length} metric conformer${molecularConformers.length === 1 ? "" : "s"}`,
  };
  const galleryTypes = [moleculeGalleryType,
    ...exactGalleryTypes.filter((type) => type.familyType !== 0)];
  const incidence = source.map((_, atomIndex) => placements.map((placement, placementIndex) => placement.support.includes(atomIndex) ? placementIndex : -1).filter((index) => index >= 0));
  return { placements, residualTypes: [], types, galleryTypes, incidence, covered: coveredAtoms.size,
    complete: coveredAtoms.size === source.length, periodic: true,
    molecularDiscovery: molecularDiscoverySummary(molecularDiscovery, "molecular connection / void cover"),
    molecular: { water: true, waterLabel, hydrogenSpecies, molecules: waters.length, connections: bridges.length, voids: gaps.length,
      moleculeClasses: 1,
      metricConformerClasses: molecularConformers.length,
      connectionClasses: galleryTypes.filter((type) => type.familyType === 1).length,
      voidClasses: galleryTypes.filter((type) => type.familyType === 2).length,
      waters: waters.length, bridges: bridges.length, gaps: gaps.length,
      waterClasses: 1,
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
    descriptorToleranceA: clusterMetricToleranceAngstrom(),
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
    metricTolerance: effectiveClusterMetricTolerance(),
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

function canonicalCycleKey(cycle) {
  const orders = [];
  const reversed = cycle.slice().reverse();
  for (let offset = 0; offset < cycle.length; offset++) {
    orders.push([...cycle.slice(offset), ...cycle.slice(0, offset)].join(":"));
    orders.push([...reversed.slice(offset), ...reversed.slice(0, offset)].join(":"));
  }
  return orders.sort()[0];
}

function unwrappedAtomicCycle(source, cycle) {
  if (!cycle.length) return [];
  const vectors = [new THREE.Vector3()];
  for (let index = 1; index < cycle.length; index++) {
    vectors.push(vectors[index - 1].clone().add(periodicDisplacement(source[cycle[index - 1]], source[cycle[index]])));
  }
  const centroid = vectors.reduce((sum, vector) => sum.add(vector), new THREE.Vector3())
    .multiplyScalar(1 / vectors.length);
  return vectors.map((vector) => vector.clone().sub(centroid));
}

function decorateIceViOxygenVoidBoundaries(source, cover) {
  const oxygen = source.map((atom, index) => atom.species === "O" ? index : -1).filter((index) => index >= 0);
  if (oxygen.length < 4) return cover;
  const fourthNeighborDistances = oxygen.map((center) => oxygen.filter((index) => index !== center)
    .map((index) => periodicDisplacement(source[center], source[index]).length()).sort((first, second) => first - second)[3]);
  const finiteFourth = fourthNeighborDistances.filter(Number.isFinite).sort((first, second) => first - second);
  if (!finiteFourth.length) return cover;
  const cutoff = finiteFourth[Math.floor(finiteFourth.length / 2)] * 1.035;
  const adjacency = new Map(oxygen.map((center) => [center, new Set(oxygen.filter((index) => index !== center
    && periodicDisplacement(source[center], source[index]).length() <= cutoff))]));
  const minimumDegree = Math.min(...[...adjacency.values()].map((neighbors) => neighbors.size));
  if (minimumDegree < 2) return cover;
  const cycles = new Map();
  const maximumRingSize = 8;
  oxygen.forEach((start) => {
    const stack = [[start, [start]]];
    while (stack.length) {
      const [current, path] = stack.pop();
      if (path.length >= 4 && adjacency.get(current).has(start)) {
        const key = canonicalCycleKey(path);
        if (!cycles.has(key)) cycles.set(key, path.slice());
      }
      if (path.length === maximumRingSize) continue;
      adjacency.get(current).forEach((neighbor) => {
        if (neighbor === start || neighbor < start || path.includes(neighbor)) return;
        stack.push([neighbor, [...path, neighbor]]);
      });
    }
  });
  const chordless = [...cycles.values()].filter((cycle) => {
    for (let first = 0; first < cycle.length; first++) for (let second = first + 1; second < cycle.length; second++) {
      const adjacentInCycle = second === first + 1 || (first === 0 && second === cycle.length - 1);
      if (!adjacentInCycle && adjacency.get(cycle[first]).has(cycle[second])) return false;
    }
    return true;
  });
  if (!chordless.length) return cover;
  const minimumRingSize = Math.min(...chordless.map((cycle) => cycle.length));
  const shortestRings = chordless.filter((cycle) => cycle.length === minimumRingSize);
  const classes = new Map();
  shortestRings.forEach((cycle) => {
    const signature = coloredPeriodicSupportSignature(source, cycle);
    const members = classes.get(signature) || [];
    members.push(cycle);
    classes.set(signature, members);
  });
  const typeOffset = Math.max(-1, ...cover.types.map((type) => type.type)) + 1;
  const addedTypes = [];
  const addedPlacements = [];
  [...classes.entries()].sort(([first], [second]) => first.localeCompare(second))
    .forEach(([signature, members], classIndex) => {
      const type = typeOffset + classIndex;
      const placementIndices = [];
      // The full observed ring count remains in the audit, while only one
      // representative per exact isometry class enters the interactive
      // gallery. Duplicating all symmetry-related empty boundaries would add
      // quadratic drawing work without adding a new isometry class.
      members.slice(0, 1).forEach((cycle) => {
        const coverIndex = cover.placements.length + addedPlacements.length;
        placementIndices.push(coverIndex);
        addedPlacements.push({ center: cycle[0], support: cycle.slice(), type, residual: false, gap: true,
          kind: "oxygen-framework void boundary", family: "gap", ring: cycle.slice(), coverIndex });
      });
      const representative = members[0];
      addedTypes.push({
        type, medoid: representative[0], element: `O${minimumRingSize} void`, shortLabel: `O${minimumRingSize} gap`,
        label: `O${minimumRingSize} gap · I${classIndex + 1}`, geometry: "oxygen-framework void-boundary polygon",
        count: members.length, observedOccurrences: members.length, residual: false, gap: true, visualKind: "ring",
        customSupport: representative.slice(), customVectors: unwrappedAtomicCycle(source, representative),
        classSignature: signature, classPlacementIndices: placementIndices,
        classIndex, classCount: classes.size,
      });
    });
  cover.placements.push(...addedPlacements);
  cover.types.push(...addedTypes);
  if (cover.galleryTypes !== cover.types) cover.galleryTypes.push(...addedTypes);
  cover.incidence = source.map((_, atomIndex) => cover.placements.map((placement, placementIndex) =>
    placement.support.includes(atomIndex) ? placementIndex : -1).filter((placementIndex) => placementIndex >= 0));
  cover.voidBoundary = {
    source: "fully occupied oxygen-framework shortest chordless rings",
    neighborCutoffAngstrom: cutoff,
    oxygenCoordinationMinimum: minimumDegree,
    ringSize: minimumRingSize,
    occurrences: shortestRings.length,
    interactiveRepresentatives: addedPlacements.length,
    classes: addedTypes.length,
    hydrogenOccupancyUsed: false,
    expectedRingSizeUsed: false,
  };
  if (cover.molecular) {
    cover.molecular.voids = shortestRings.length;
    cover.molecular.voidClasses = addedTypes.length;
    cover.molecular.gaps = shortestRings.length;
    cover.molecular.gapClasses = addedTypes.length;
  }
  return cover;
}

// Discover exact recurring colored metric supports. Atom-centred coordination
// polyhedra are only one candidate family; centre-free bond-lens supports can
// enter the same cover, and any uncovered connected region becomes an explicit
// residual cluster rather than disappearing from the model.
function buildExhaustiveClusterCover(source) {
  const molecularDiscovery = molecularComponentHypothesis(source);
  const waterDiscovery = discoveredWaterComponents(molecularDiscovery);
  if (waterDiscovery) {
    const waterCover = buildWaterClusterCover(source, waterDiscovery);
    if (currentMaterial().molecularFixture === "ice-vi-cod-1567346-average") {
      // Ice VI's shortest oxygen-framework voids are O4 boundaries. Remove
      // the generic six-ring family before adding those graph-derived gaps;
      // retaining both families visually double-counts empty space.
      waterCover.placements = waterCover.placements.filter((placement) => placement.family !== "gap");
      waterCover.placements.forEach((placement, coverIndex) => { placement.coverIndex = coverIndex; });
      waterCover.types = waterCover.types.filter((type) => type.familyType !== 2);
      waterCover.galleryTypes = waterCover.galleryTypes.filter((type) => type.familyType !== 2);
      waterCover.incidence = source.map((_, atomIndex) => waterCover.placements
        .map((placement, placementIndex) => placement.support.includes(atomIndex) ? placementIndex : -1)
        .filter((placementIndex) => placementIndex >= 0));
      return decorateIceViOxygenVoidBoundaries(source, waterCover);
    }
    return waterCover;
  }
  if (molecularDiscovery.accepted) {
    const molecularCover = buildGenericMolecularClusterCover(source, molecularDiscovery);
    if (molecularCover) return molecularCover;
  }
  const irregular = buildIrregularClusterCover(source, molecularDiscovery);
  return currentMaterial().molecularFixture === "ice-vi-cod-1567346-average"
    ? decorateIceViOxygenVoidBoundaries(source, irregular) : irregular;
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

function galleryPoseModel(cluster) {
  const placements = cluster.classPlacementIndices
    ? cluster.classPlacementIndices.map((index) => learnedCover.placements[index]).filter(Boolean)
    : learnedCover.placements.filter((placement) => placement.type === cluster.type);
  return classifyPlacementPoseOrbits(placements);
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
  const oxygenRingLabel = learnedCover.voidBoundary?.ringSize
    ? `O${learnedCover.voidBoundary.ringSize} boundaries`
    : "O₆ boundaries";
  const ledger = document.createElement("div");
  ledger.className = "cluster-cover-ledger";
  ledger.setAttribute("aria-label", "Molecular ice cover accounting");
  const layers = [
    { family: "molecule", eyebrow: "atomic cover", title: molecular.water ? `${molecular.waters} ${molecular.waterLabel || "H₂O"}` : `${molecular.molecules} molecules`,
      detail: `${learnedCover.covered} / ${referenceCount()} atoms · ${molecular.moleculeClasses} isometry class${molecular.moleculeClasses === 1 ? "" : "es"}` },
    { family: "bridge", eyebrow: "connection cover", title: `${molecular.connections} connections`,
      detail: `${molecular.connectionClasses} metric-isometry classes · attachment geometry` },
    { family: "gap", eyebrow: "void-boundary cover", title: `${molecular.voids} ${molecular.water ? oxygenRingLabel : "void boundaries"}`,
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
  explanation.textContent = `${molecular.water ? molecular.waterLabel || "H₂O" : "Finite molecules"} close the atom cover; connection and void clusters encode intermolecular geometry without inventing radial spokes.`;
  ledger.append(explanation);
  return ledger;
}

const MICROSTRUCTURE_PROJECTIONS = {
  xy: { axes: [0, 1], labels: ["x", "y"] },
  xz: { axes: [0, 2], labels: ["x", "z"] },
  yz: { axes: [1, 2], labels: ["y", "z"] },
};

function drawMicrostructureProjection(canvas, projectionKey = microstructureProjection) {
  const projection = MICROSTRUCTURE_PROJECTIONS[projectionKey] || MICROSTRUCTURE_PROJECTIONS.xy;
  const context = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#051011";
  context.fillRect(0, 0, width, height);
  if (!microstructureEvidence?.siteRoles?.length) return;
  const points = microstructureEvidence.siteRoles.map((role) => ({
    role,
    position: referenceAtoms[role.index]?.p?.toArray(),
  })).filter((entry) => entry.position?.every(Number.isFinite));
  if (!points.length) return;
  const [horizontal, vertical] = projection.axes;
  const horizontalValues = points.map((entry) => entry.position[horizontal]);
  const verticalValues = points.map((entry) => entry.position[vertical]);
  const minimumHorizontal = Math.min(...horizontalValues), maximumHorizontal = Math.max(...horizontalValues);
  const minimumVertical = Math.min(...verticalValues), maximumVertical = Math.max(...verticalValues);
  const rangeHorizontal = Math.max(1e-9, maximumHorizontal - minimumHorizontal);
  const rangeVertical = Math.max(1e-9, maximumVertical - minimumVertical);
  const padding = 24;
  const scale = Math.min((width - 2 * padding) / rangeHorizontal, (height - 2 * padding) / rangeVertical);
  const occupiedWidth = rangeHorizontal * scale, occupiedHeight = rangeVertical * scale;
  const offsetX = (width - occupiedWidth) / 2, offsetY = (height - occupiedHeight) / 2;
  const screenPoint = (position) => ({
    x: offsetX + (position[horizontal] - minimumHorizontal) * scale,
    y: height - offsetY - (position[vertical] - minimumVertical) * scale,
  });
  context.strokeStyle = "rgba(151,194,183,.09)";
  context.lineWidth = 1;
  for (let division = 0; division <= 4; division++) {
    const x = padding + (width - 2 * padding) * division / 4;
    const y = padding + (height - 2 * padding) * division / 4;
    context.beginPath(); context.moveTo(x, padding); context.lineTo(x, height - padding); context.stroke();
    context.beginPath(); context.moveTo(padding, y); context.lineTo(width - padding, y); context.stroke();
  }
  context.font = "10px ui-monospace, monospace";
  context.fillStyle = "rgba(151,194,183,.55)";
  context.fillText(`${projection.labels[0]} →`, width - 48, height - 8);
  context.fillText(`${projection.labels[1]} ↑`, 8, 14);
  points.forEach(({ role, position }) => {
    const point = screenPoint(position);
    context.beginPath();
    context.arc(point.x, point.y, role.literalTerminal ? 3.1 : 2.15, 0, TAU);
    context.fillStyle = role.literalTerminal ? "rgba(255,109,113,.95)"
      : role.recurring ? "rgba(101,225,188,.76)" : "rgba(112,139,132,.42)";
    context.fill();
    if (role.gapBoundary) {
      context.beginPath(); context.arc(point.x, point.y, 4.2, 0, TAU);
      context.strokeStyle = "rgba(255,193,105,.72)"; context.lineWidth = 1; context.stroke();
    }
    if (role.poseInterface) {
      context.beginPath(); context.arc(point.x, point.y, 5.5, 0, TAU);
      context.strokeStyle = "rgba(85,200,255,.72)"; context.lineWidth = 1; context.stroke();
    }
    if (role.coordinationAnomaly) {
      context.beginPath(); context.arc(point.x, point.y, 7.2, 0, TAU);
      context.strokeStyle = "rgba(181,148,255,.9)"; context.lineWidth = 1.35; context.stroke();
    }
    if (role.occupationalAlternative) {
      context.save(); context.translate(point.x, point.y); context.rotate(Math.PI / 4);
      context.strokeStyle = role.explicitVacancy ? "rgba(220,232,228,.95)" : "rgba(181,148,255,.95)";
      context.lineWidth = 1.2; context.strokeRect(-3.2, -3.2, 6.4, 6.4); context.restore();
    }
  });
}

function buildMicrostructureProjection() {
  const panel = document.createElement("div");
  panel.className = "microstructure-map";
  const header = document.createElement("header");
  const copy = document.createElement("span");
  copy.innerHTML = "<small>spatial evidence projection</small><strong>same positions · diagnostic overlays only</strong>";
  const controls = document.createElement("div");
  controls.setAttribute("aria-label", "Microstructure projection plane");
  const canvas = document.createElement("canvas");
  canvas.width = 900;
  canvas.height = 220;
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", "Spatial projection of recurring clusters, gap boundaries, literal residuals, coordination anomalies, local pose interfaces, and occupational alternatives");
  Object.keys(MICROSTRUCTURE_PROJECTIONS).forEach((key) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = key.toUpperCase();
    button.setAttribute("aria-pressed", String(key === microstructureProjection));
    button.addEventListener("click", () => {
      microstructureProjection = key;
      controls.querySelectorAll("button").forEach((entry) => entry.setAttribute("aria-pressed", String(entry === button)));
      drawMicrostructureProjection(canvas, key);
    });
    controls.append(button);
  });
  header.append(copy, controls);
  const legend = document.createElement("div");
  legend.className = "microstructure-map-legend";
  [
    ["recurring", "mint"], ["gap boundary", "amber"], ["literal residual", "red"],
    ["pose interface", "blue"], ["coordination candidate", "violet"], ["occupancy / vacancy", "diamond"],
  ].forEach(([label, className]) => {
    const item = document.createElement("span");
    item.innerHTML = `<i class="${className}"></i>${label}`;
    legend.append(item);
  });
  panel.append(header, canvas, legend);
  drawMicrostructureProjection(canvas);
  return panel;
}

function buildMicrostructureLedger() {
  if (!microstructureEvidence) return null;
  const audit = microstructureEvidence;
  const ledger = document.createElement("details");
  ledger.className = "microstructure-ledger";
  ledger.setAttribute("aria-label", "Geometric microstructure evidence");
  const heading = document.createElement("summary");
  heading.className = "microstructure-heading";
  heading.innerHTML = `<span><small>heterogeneous geometry audit</small><strong>microstructure candidates · labels withheld</strong></span><em>${audit.coordinationAnomalyAtoms} coordination · ${audit.literalOnlyAtoms} literal-only · ${audit.crossPoseContacts} cross-pose contacts</em>`;
  const cards = [
    ["recurring material classes", audit.recurringTypes, `${audit.recurringCoveredAtoms} atoms covered by promotable supports`],
    ["gap / void boundaries", audit.gapBoundaryTypes, `${audit.gapBoundaryAtoms} boundary atoms · reusable constraint only`],
    ["literal residuals", audit.terminalTypes, `${audit.literalOnlyAtoms} atoms require non-generative terminals`],
    ["coordination anomalies", audit.coordinationAnomalyAtoms, "species-local median / MAD candidates"],
    ["local pose interfaces", audit.crossPoseContacts, `${audit.poseDomainComponents} spatial pose components · not grain labels`],
    ["occupational alternatives", audit.occupationalAlternativeSites, `${audit.explicitVacancySites} explicit vacancy-bearing sites`],
  ];
  const grid = document.createElement("div");
  grid.className = "microstructure-grid";
  cards.forEach(([label, value, detail]) => {
    const card = document.createElement("article");
    card.innerHTML = `<small>${label}</small><strong>${Number(value).toLocaleString()}</strong><span>${detail}</span>`;
    grid.append(card);
  });
  const boundary = document.createElement("p");
  boundary.textContent = "These are inspection candidates, not defect or grain-boundary assignments: molecular orientations, finite surfaces, strain, and crop truncation can produce the same local signals. Gap boundaries may recur as connection constraints but emit no atoms. No formation energy is inferred; literal residuals never become growth rules.";
  ledger.append(heading, buildMicrostructureProjection(), grid, boundary);
  return ledger;
}

const GROWTH_EVENT_PHENOTYPES = {
  bulk: { label: "bulk-like recurrence", color: "#65e1bc" },
  surface: { label: "undercoordination / surface", color: "#ffc169" },
  interface: { label: "pose-interface adjacent", color: "#55c8ff" },
  gap: { label: "gap / residual adjacent", color: "#b594ff" },
  occupancy: { label: "occupancy-alternative adjacent", color: "#d9d2ff" },
  topology: { label: "local topology rejection", color: "#ff7f88" },
  boundary: { label: "public-boundary rejection", color: "#f0c96a" },
  marking: { label: "connection-mark rejection", color: "#b594ff" },
  conflict: { label: "colored contact conflict", color: "#ff6d71" },
  redundant: { label: "redundant cover prune", color: "#71867f" },
  prune: { label: "other geometric prune", color: "#cf858c" },
};

function growthEventNeighborhood(candidate, evaluation) {
  const reach = Math.max(referenceSpacing * 1.15, (microstructureEvidence?.adjacencyReach || 0) * .46);
  const probes = evaluation.fresh?.length ? evaluation.fresh.map((site) => site.p) : [candidate.position];
  const counts = { recurring: 0, gap: 0, residual: 0, interface: 0, anomaly: 0, occupancy: 0, vacancy: 0 };
  microstructureEvidence?.siteRoles?.forEach((role) => {
    const point = referenceAtoms[role.index]?.p;
    if (!point || !probes.some((probe) => probe.distanceTo(point) <= reach)) return;
    if (role.recurring) counts.recurring++;
    if (role.gapBoundary) counts.gap++;
    if (role.literalTerminal) counts.residual++;
    if (role.poseInterface) counts.interface++;
    if (role.coordinationAnomaly) counts.anomaly++;
    if (role.occupationalAlternative) counts.occupancy++;
    if (role.explicitVacancy) counts.vacancy++;
  });
  return { reach, counts };
}

function classifyGrowthEvent(candidate, evaluation) {
  const neighborhood = growthEventNeighborhood(candidate, evaluation);
  const counts = neighborhood.counts;
  const reason = String(evaluation.reason || "").toLowerCase();
  let phenotype = "bulk";
  if (!evaluation.accepted && /duplicate|redundant|no novel/.test(reason)) phenotype = "redundant";
  else if (evaluation.boundaryFailures || evaluation.knownFailures || /boundary|outside/.test(reason)) phenotype = "boundary";
  else if (evaluation.conflicts || /conflict|hard.core|species/.test(reason)) phenotype = "conflict";
  else if (evaluation.coordinationOverflows?.length || evaluation.angularViolations?.length || /coordination|angular|topology/.test(reason)) phenotype = "topology";
  else if (candidate.markingAccepted === false || /marking|section/.test(reason)) phenotype = "marking";
  else if (!evaluation.accepted) phenotype = "prune";
  else if (counts.occupancy) phenotype = "occupancy";
  else if (counts.interface) phenotype = "interface";
  else if (counts.gap || counts.residual) phenotype = "gap";
  else if ((evaluation.surfaceCompletion?.scaledDelta || 0) > .08
    || (evaluation.surfaceCompletion?.newSiteDeficit || 0) > (evaluation.surfaceCompletion?.healedExisting || 0)) phenotype = "surface";
  const tags = Object.entries(counts).filter(([, count]) => count > 0).map(([label]) => label);
  if (evaluation.surfaceCompletion?.scaledDelta < -.08) tags.push("coordination healing");
  return { phenotype, tags, neighborhood, reason: evaluation.reason || "unspecified" };
}

function candidatePosePerturbationAudit(candidate) {
  const sceneToAngstrom = referenceSpacingA / Math.max(referenceSpacing, 1e-12);
  const measuredUncertainty = measuredPairUncertaintyAngstrom();
  const resolvedTolerance = clusterMetricToleranceAngstrom();
  const stressRadiusAngstrom = Math.max(measuredUncertainty, resolvedTolerance * .5, 1e-6);
  const stressRadiusScene = stressRadiusAngstrom / sceneToAngstrom;
  const candidateRadius = Math.max(stressRadiusScene,
    ...candidateSites(candidate).map((site) => site.p.distanceTo(candidate.position)));
  const rotationRadians = Math.min(Math.PI / 18, stressRadiusScene / candidateRadius);
  const axes = [new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, 0, 1)];
  const cloneAt = (position, rotation) => ({ ...candidate,
    position: position.clone(), rotation: rotation.clone().normalize(), markingAccepted: true });
  const diagnosticOptions = { refinePose: false, recordWork: false, targetAware: false, enforceMarking: false };
  const nominal = evaluateCandidate(cloneAt(candidate.position, candidate.rotation), diagnosticOptions);
  const trials = [];
  axes.forEach((axis) => [-1, 1].forEach((sign) => {
    const translated = candidate.position.clone().addScaledVector(axis, sign * stressRadiusScene);
    trials.push(evaluateCandidate(cloneAt(translated, candidate.rotation), diagnosticOptions));
    const delta = new THREE.Quaternion().setFromAxisAngle(axis, sign * rotationRadians);
    trials.push(evaluateCandidate(cloneAt(candidate.position,
      candidate.rotation.clone().premultiply(delta)), diagnosticOptions));
  }));
  const agreementCount = trials.filter((trial) => trial.accepted === nominal.accepted).length;
  const acceptedCount = trials.filter((trial) => trial.accepted).length;
  const failureModes = Object.fromEntries([...new Set(trials.filter((trial) => !trial.accepted)
    .map((trial) => trial.reason))].sort().map((reason) =>
    [reason, trials.filter((trial) => !trial.accepted && trial.reason === reason).length]));
  return {
    perturbationTrials: trials.length,
    perturbationAgreementCount: agreementCount,
    perturbationAgreementFraction: agreementCount / Math.max(1, trials.length),
    perturbationHardAcceptanceCount: acceptedCount,
    perturbationNominalHardGeometryAccepted: nominal.accepted,
    perturbationStressRadiusAngstrom: stressRadiusAngstrom,
    perturbationRotationDegrees: rotationRadians * 180 / Math.PI,
    perturbationFailureModes: failureModes,
    perturbationEnsembleExecutedForThisAction: true,
    perturbationAuditTargetUsed: false,
    candidateSelectionTargetUsed: !reconstructionCertified,
  };
}

function growthDecisionUncertainty(candidate, evaluation, nearbyRoleCounts, executePerturbation) {
  let minimumContactClearance = Infinity;
  const searchRadius = Math.max(coloredDistanceEnvelopes?.maximumExclusion || COLLISION_TOLERANCE,
    coloredCoordinationEnvelopes?.maximumCutoff || 0);
  evaluation.fresh.forEach((site) => nearbyAtoms(site.p, searchRadius).forEach((atom) => {
    const clearance = site.p.distanceTo(atom.p) - coloredPairExclusion(site.species, atom.species);
    minimumContactClearance = Math.min(minimumContactClearance, clearance);
  }));
  const maximumOverlapResidual = evaluation.merged.reduce((maximum, entry) =>
    Math.max(maximum, entry.site.p.distanceTo(entry.atom.p)), 0);
  const markingMargins = (candidate.markingScores || []).map((row) => row.score - row.threshold);
  const markingMargin = markingMargins.length ? Math.max(...markingMargins) : null;
  const activeMarking = selectedMarking();
  const markingHoldoutLoss = activeMarking?.validationLoss
    ?? sectionModel?.curve?.at(-1)?.validationLoss ?? null;
  const sceneToAngstrom = referenceSpacingA / Math.max(referenceSpacing, 1e-12);
  const measuredUncertainty = measuredPairUncertaintyAngstrom();
  const nominalTolerance = referenceSpacingA * clusterMetricTolerance();
  const perturbation = executePerturbation ? candidatePosePerturbationAudit(candidate) : {
    perturbationTrials: 0,
    perturbationAgreementCount: 0,
    perturbationAgreementFraction: null,
    perturbationHardAcceptanceCount: 0,
    perturbationNominalHardGeometryAccepted: null,
    perturbationStressRadiusAngstrom: null,
    perturbationRotationDegrees: null,
    perturbationFailureModes: {},
    perturbationEnsembleExecutedForThisAction: false,
    perturbationAuditTargetUsed: false,
    candidateSelectionTargetUsed: !reconstructionCertified,
    perturbationNotExecutedReason: "deterministic per-leap audit cap reached",
  };
  return {
    measuredPairDistanceSigmaAngstrom: measuredUncertainty,
    nominalMetricToleranceAngstrom: nominalTolerance,
    resolvedMetricToleranceAngstrom: clusterMetricToleranceAngstrom(),
    measurementFloorActive: measuredUncertainty > nominalTolerance + 1e-9,
    minimumContactClearanceAngstrom: Number.isFinite(minimumContactClearance)
      ? minimumContactClearance * sceneToAngstrom : null,
    maximumOverlapResidualAngstrom: maximumOverlapResidual * sceneToAngstrom,
    activeMarkingGate: policySelect.value === "marked",
    markingMargin,
    markingHoldoutLoss,
    nearbyOccupationalAlternativeSites: nearbyRoleCounts.occupancy,
    nearbyExplicitVacancySites: nearbyRoleCounts.vacancy,
    occupancyRealizationResolved: !currentMaterial().growthWithheld,
    ...perturbation,
    statisticalConfidenceClaimed: false,
  };
}

function prepareGrowthMechanismDiagnostic(candidate, evaluation) {
  const classified = classifyGrowthEvent(candidate, evaluation);
  const leapIndex = leapEventCount + 1;
  const poseAuditCount = growthPoseAuditsByLeap.get(leapIndex) || 0;
  const executePerturbation = poseAuditCount < MAXIMUM_POSE_AUDITS_PER_LEAP;
  if (executePerturbation) growthPoseAuditsByLeap.set(leapIndex, poseAuditCount + 1);
  const uncertainty = growthDecisionUncertainty(candidate, evaluation,
    classified.neighborhood.counts, executePerturbation);
  return { classified, leapIndex, uncertainty };
}

function recordGrowthMechanismEvent(candidate, evaluation, accepted, depth, frozenDiagnostic = null) {
  const { classified, leapIndex, uncertainty } = frozenDiagnostic
    || prepareGrowthMechanismDiagnostic(candidate, evaluation);
  growthMechanismEvents.push({
    index: eventIndex + growthMechanismEvents.length + 1,
    accepted,
    phenotype: classified.phenotype,
    tags: classified.tags,
    reason: classified.reason,
    leapIndex,
    position: candidate.position.toArray(),
    nearbyRoleCounts: classified.neighborhood.counts,
    neighborhoodReachAngstrom: classified.neighborhood.reach * referenceSpacingA / referenceSpacing,
    sharedSites: evaluation.merged.length,
    emittedSites: evaluation.fresh.length,
    depth,
    gateSignals: {
      coloredConflicts: evaluation.conflicts,
      boundaryFailures: evaluation.boundaryFailures,
      knownWindowFailures: evaluation.knownFailures,
      coordinationOverflows: evaluation.coordinationOverflows?.length || 0,
      angularViolations: evaluation.angularViolations?.length || 0,
      markingAccepted: candidate.markingAccepted,
    },
    uncertainty,
  });
  const totals = growthMechanismTotals[classified.phenotype] ||= { accepted: 0, rejected: 0, emittedSites: 0 };
  totals[accepted ? "accepted" : "rejected"]++;
  totals.emittedSites += accepted ? evaluation.fresh.length : 0;
  if (growthMechanismEvents.length > 96) {
    const olderLeap = growthMechanismEvents.findIndex((event) => event.leapIndex < leapIndex);
    const unaudited = growthMechanismEvents.findIndex((event) =>
      !event.uncertainty.perturbationEnsembleExecutedForThisAction);
    growthMechanismEvents.splice(olderLeap >= 0 ? olderLeap : unaudited >= 0 ? unaudited : 0, 1);
  }
}

function growthMechanismAudit() {
  const byPhenotype = Object.fromEntries(Object.entries(growthMechanismTotals)
    .map(([id, counts]) => [id, { ...counts }]));
  const eventsObserved = Object.values(byPhenotype).reduce((sum, counts) => sum + counts.accepted + counts.rejected, 0);
  return {
    role: "post-decision spatial correlation between frozen tree actions and input-derived local geometric roles",
    eventsStored: growthMechanismEvents.length,
    eventsObserved,
    maximumStoredEvents: 96,
    maximumPoseAuditsPerLeap: MAXIMUM_POSE_AUDITS_PER_LEAP,
    poseAuditsObserved: [...growthPoseAuditsByLeap.values()].reduce((sum, count) => sum + count, 0),
    byPhenotype,
    events: growthMechanismEvents.map(({ position, ...event }) => ({
      ...event,
      neighborhoodReachAngstrom: receiptRound(event.neighborhoodReachAngstrom),
      uncertainty: Object.fromEntries(Object.entries(event.uncertainty)
        .map(([key, value]) => [key, typeof value === "number" ? receiptRound(value) : value])),
    })),
    coordinatesEmbedded: false,
    usedForCandidateEnumeration: false,
    usedForAdmission: false,
    usedForBranchRanking: activeMicrostructureCouplingWeight() > 0,
    branchRankingMode: microstructureCouplingMode,
    branchRankingWeight: activeMicrostructureCouplingWeight(),
    perturbationAuditTargetUsed: false,
    statisticalConfidenceClaimed: false,
    defectLabelsAssigned: false,
    physicalMechanismAssigned: false,
    formationEnergyInferred: false,
    kineticsInferred: false,
  };
}

function drawGrowthMechanismMap() {
  const context = growthMechanismCanvas.getContext("2d");
  const width = growthMechanismCanvas.width, height = growthMechanismCanvas.height;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#051011"; context.fillRect(0, 0, width, height);
  const projection = MICROSTRUCTURE_PROJECTIONS[growthMechanismProjectionKey] || MICROSTRUCTURE_PROJECTIONS.xy;
  const basePoints = referenceAtoms.map((atom) => atom.p.toArray());
  const eventPoints = growthMechanismEvents.map((event) => event.position);
  const points = [...basePoints, ...eventPoints];
  if (!points.length) return;
  const [horizontal, vertical] = projection.axes;
  const minH = Math.min(...points.map((point) => point[horizontal]));
  const maxH = Math.max(...points.map((point) => point[horizontal]));
  const minV = Math.min(...points.map((point) => point[vertical]));
  const maxV = Math.max(...points.map((point) => point[vertical]));
  const rangeH = Math.max(1e-9, maxH - minH), rangeV = Math.max(1e-9, maxV - minV);
  const padding = 24, scale = Math.min((width - 2 * padding) / rangeH, (height - 2 * padding) / rangeV);
  const offsetX = (width - rangeH * scale) / 2, offsetY = (height - rangeV * scale) / 2;
  const screen = (point) => [offsetX + (point[horizontal] - minH) * scale,
    height - offsetY - (point[vertical] - minV) * scale];
  basePoints.forEach((point, index) => {
    const [x, y] = screen(point);
    const highlighted = microstructureRoleMatches(microstructureEvidence?.siteRoles?.[index] || {});
    context.fillStyle = highlighted ? "rgba(181,148,255,.72)" : "rgba(151,194,183,.13)";
    context.beginPath(); context.arc(x, y, highlighted ? 2.6 : 1.25, 0, TAU); context.fill();
    if (highlighted) {
      context.strokeStyle = "rgba(181,148,255,.34)"; context.lineWidth = 1;
      context.beginPath(); context.arc(x, y, 5.2, 0, TAU); context.stroke();
    }
  });
  growthMechanismEvents.forEach((event) => {
    const [x, y] = screen(event.position);
    const color = GROWTH_EVENT_PHENOTYPES[event.phenotype]?.color || "#b594ff";
    context.strokeStyle = color; context.fillStyle = color; context.lineWidth = 2;
    if (event.accepted) { context.beginPath(); context.arc(x, y, 4.4, 0, TAU); context.fill(); }
    else { context.beginPath(); context.moveTo(x - 4, y - 4); context.lineTo(x + 4, y + 4); context.moveTo(x + 4, y - 4); context.lineTo(x - 4, y + 4); context.stroke(); }
  });
  context.fillStyle = "rgba(151,194,183,.55)"; context.font = "10px ui-monospace, monospace";
  context.fillText(`${projection.labels[0]} →`, width - 48, height - 8); context.fillText(`${projection.labels[1]} ↑`, 8, 14);
}

function renderGrowthUncertaintyBudget() {
  growthUncertaintyBudget.replaceChildren();
  if (!growthMechanismEvents.length) {
    growthUncertaintyState.textContent = "awaiting a decision";
    const empty = document.createElement("p");
    empty.textContent = "The first evaluated frontier will expose measurement, tolerance, contact, overlap, marking, and occupancy conditioning.";
    growthUncertaintyBudget.appendChild(empty);
    return;
  }
  const latestLeap = Math.max(...growthMechanismEvents.map((event) => event.leapIndex));
  const events = growthMechanismEvents.filter((event) => event.leapIndex === latestLeap);
  const uncertainties = events.map((event) => event.uncertainty);
  const auditedEvents = events.filter((event) =>
    event.uncertainty.perturbationEnsembleExecutedForThisAction);
  const finite = (field) => uncertainties.map((entry) => entry[field]).filter(Number.isFinite);
  const minimum = (field) => { const values = finite(field); return values.length ? Math.min(...values) : null; };
  const maximum = (field) => { const values = finite(field); return values.length ? Math.max(...values) : null; };
  const first = uncertainties[0];
  const markingMargin = minimum("markingMargin");
  const holdoutLoss = maximum("markingHoldoutLoss");
  const occupancy = events.reduce((sum, event) => sum + event.uncertainty.nearbyOccupationalAlternativeSites, 0);
  const perturbationTrials = events.reduce((sum, event) => sum + event.uncertainty.perturbationTrials, 0);
  const perturbationAgreements = events.reduce((sum, event) => sum + event.uncertainty.perturbationAgreementCount, 0);
  const selectionTargetUsed = events.some((event) => event.uncertainty.candidateSelectionTargetUsed);
  const values = [
    ["measured pair σ", `${first.measuredPairDistanceSigmaAngstrom.toFixed(3)} Å`, first.measurementFloorActive ? "sets tolerance floor" : "below nominal ε"],
    ["resolved isometry ε", `${first.resolvedMetricToleranceAngstrom.toFixed(3)} Å`, `nominal ${first.nominalMetricToleranceAngstrom.toFixed(3)} Å`],
    ["minimum contact clearance", minimum("minimumContactClearanceAngstrom") === null ? "not sampled" : `${minimum("minimumContactClearanceAngstrom").toFixed(3)} Å`, "distance above learned exclusion"],
    ["maximum overlap residual", `${maximum("maximumOverlapResidualAngstrom").toFixed(3)} Å`, "coincident support mismatch"],
    ["active marking margin", first.activeMarkingGate && markingMargin !== null ? markingMargin.toFixed(3) : "not gating", holdoutLoss === null ? "holdout unavailable" : `holdout loss ${holdoutLoss.toFixed(3)}`],
    ["occupancy adjacency", occupancy.toLocaleString(), first.occupancyRealizationResolved ? "realization explicit" : "occupational state unresolved"],
    ["bounded pose ensemble", `${perturbationAgreements}/${perturbationTrials} agree`, `${auditedEvents.length}/${events.length} decisions · ${maximum("perturbationStressRadiusAngstrom").toFixed(3)} Å · ${maximum("perturbationRotationDegrees").toFixed(2)}°`],
    ["candidate provenance", selectionTargetUsed ? "known-window guided" : "target-blind", "perturbation audit itself target-blind"],
  ];
  values.forEach(([label, value, detail]) => {
    const tile = document.createElement("span");
    tile.innerHTML = `<small>${label}</small><strong>${value}</strong><em>${detail}</em>`;
    growthUncertaintyBudget.appendChild(tile);
  });
  const conditioning = [];
  if (first.measurementFloorActive) conditioning.push("measurement-floor conditioned");
  if (first.activeMarkingGate && markingMargin !== null && holdoutLoss !== null && markingMargin <= holdoutLoss) conditioning.push("marking margin ≤ holdout loss");
  if (occupancy) conditioning.push("occupancy-adjacent");
  if (perturbationAgreements < perturbationTrials) conditioning.push("pose-sensitive");
  growthUncertaintyState.textContent = `${auditedEvents.length}/${events.length} decisions pose-audited · ${conditioning.join(" · ") || "nominal geometry"} · ${perturbationAgreements}/${perturbationTrials} trials agree · confidence unclaimed`;
}

function renderGrowthMechanismAudit() {
  growthMechanismSection.hidden = pipelineStage !== 4;
  if (pipelineStage !== 4) return;
  const audit = growthMechanismAudit();
  const accepted = Object.values(audit.byPhenotype).reduce((sum, counts) => sum + counts.accepted, 0);
  const rejected = Object.values(audit.byPhenotype).reduce((sum, counts) => sum + counts.rejected, 0);
  growthMechanismState.textContent = audit.eventsObserved
    ? `${accepted} accepted · ${rejected} rejected · ${audit.eventsStored}/${audit.eventsObserved} mapped · ${microstructureCouplingLabel()}`
    : `no decisions yet · ${microstructureCouplingLabel()}`;
  drawGrowthMechanismMap();
  growthMechanismLedger.replaceChildren();
  Object.entries(GROWTH_EVENT_PHENOTYPES).forEach(([id, record]) => {
    const count = audit.byPhenotype[id];
    if (!count) return;
    const tile = document.createElement("span"); tile.style.setProperty("--phenotype", record.color);
    tile.innerHTML = `<small>${record.label}</small><strong>${count.accepted} / ${count.rejected}</strong><em>accepted / rejected · ${count.emittedSites} emitted</em>`;
    growthMechanismLedger.appendChild(tile);
  });
  if (!growthMechanismLedger.children.length) {
    const empty = document.createElement("p"); empty.textContent = "Advance one tree-search update to map its local geometric environment."; growthMechanismLedger.appendChild(empty);
  }
  renderGrowthUncertaintyBudget();
  growthMechanismBoundary.textContent = `Phenotypes and uncertainty budgets are assigned after the candidate geometry and decision are frozen. Up to ${MAXIMUM_POSE_AUDITS_PER_LEAP} deterministic pose audits replay hard geometry at the larger of measured pair uncertainty and half the resolved isometry tolerance; the capped set is retained in encounter order, target-blind, and never changes admission or rank. This is a bounded sensitivity audit, not a posterior probability, confidence interval, thermal ensemble, dynamics, or calibrated robustness certificate. ${activeMicrostructureCouplingWeight() > 0 ? `The declared ${microstructureCouplingLabel()} experiment uses only proximity to frozen input-derived roles as a soft rank term over unchanged actions.` : "Proximity to heterogeneous-geometry roles is diagnostic only."} ${activeFrontMorphologyWeight() > 0 ? `The ${frontMorphologyLabel()} experiment uses parent-local angular support as another soft ordering term.` : "Front morphology is diagnostic only."} ${activeEpitaxyWeight() > 0 ? `The declared ${epitaxyTemplateLabel()} contributes an interfacial registry score without substrate atoms.` : "No epitaxial template ranks the frontier."} No defect identity, mean curvature, adhesion, interface energy, physical mechanism, formation energy, mobility, or rate is inferred.`;
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
  const poseModel = galleryPoseModel(cluster);
  const poseCount = poseModel.orientations;
  const poseStatus = poseModel.support === "finite required set" ? "required finite orbit"
    : poseModel.support === "sampled continuum" || poseModel.support === "sampled axial continuum"
      ? poseModel.support : "observed · unresolved law";
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
    <div><small>complete-cover evidence</small><strong>${coveredAtoms.size.toLocaleString()} / ${referenceEntityLabel()}</strong><span>${placementIndices.length} occurrence${placementIndices.length === 1 ? "" : "s"} · ${supportSites} sites / occurrence · ${sharedAtoms} overlap-shared sites</span></div>
    <div><small>proper-pose support</small><strong>${poseCount || "unresolved"} orbit${poseCount === 1 ? "" : "s"} · ${poseModel.properSymmetryGaugeCount || 1} proper gauge${poseModel.properSymmetryGaugeCount === 1 ? "" : "s"} · χ ${chirality}</strong><span>${poseStatus} · intrinsic right-handed frames remove translation and atom order; mirrors remain distinct</span></div>
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
  const galleryAccounting = learnedCover.molecular?.metricConformerClasses > 1
    ? `${learnedCover.molecular.metricConformerClasses} molecular metric conformers retained beneath one topology class`
    : "no classes merged";
  const filters = learnedCover.molecular ? [
    ["all", "All cover classes"], ["molecule", learnedCover.molecular.water ? `${learnedCover.molecular.waterLabel || "H₂O"} molecules` : "Molecules"],
    ["bridge", "Bridge polyhedra"], ["gap", "Gap boundaries"],
  ] : [
    ["all", "All cover classes"], ["support", "Recurring supports"],
    ...(types.some((cluster) => cluster.gap && !cluster.residual) ? [["gap", "Void boundaries"]] : []),
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
      status.textContent = `Showing ${visible} / ${types.length} cover classes · ${galleryAccounting}`;
      const selected = clusterGallery.querySelector(".cluster-card.active:not([hidden])")
        || clusterGallery.querySelector(".cluster-card:not([hidden])");
      if (selected) {
        updateClusterGalleryInspector(Number(selected.dataset.clusterIndex));
        clusterGallery.scrollTo({
          top: Math.max(0, selected.offsetTop - 8), left: 0, behavior: "auto",
        });
      }
      if (pipelineStage === 3) updateClusterGalleryTrainingReadouts();
    });
    controls.append(button);
  });
  status.textContent = `Showing ${types.length} / ${types.length} cover classes · ${galleryAccounting}`;
  const inspector = document.createElement("div");
  inspector.className = "cluster-gallery-inspector";
  inspector.setAttribute("aria-live", "polite");
  const ledger = buildMolecularCoverLedger(types);
  toolbar.append(controls, status);
  // Ledger and inspector are peer grid rows, not overflowing children of a
  // fixed toolbar track. This keeps every 3D card below—not underneath—the
  // accounting controls at desktop and narrow widths.
  const rows = document.createDocumentFragment();
  rows.append(toolbar);
  if (ledger) rows.append(ledger);
  rows.append(inspector);
  return rows;
}

function rebuildClusterGallery() {
  clusterGallery.replaceChildren();
  clusterGallery.scrollTop = 0;
  clusterGallery.scrollLeft = 0;
  const types = clusterGalleryTypes();
  clusterGallery.append(buildMolecularGalleryToolbar(types));
  const microstructure = buildMicrostructureLedger();
  if (microstructure) clusterGallery.append(microstructure);
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
    const placements = cluster.observedOccurrences ?? cluster.classPlacementIndices?.length
      ?? learnedCover.placements.filter((placement) => placement.type === cluster.type).length;
    const familyIndex = cluster.familyType ?? galleryIndex;
    const galleryPose = learnedCover.molecular ? galleryPoseModel(cluster) : null;
    const poses = galleryPose?.orientations
      ?? (orientationAtlas.find((entry) => entry.cluster === galleryIndex)?.orientations || 0);
    const channels = cluster.residual ? 0 : recommendedChannelsForCluster(familyIndex);
    const name = cluster.label || (cluster.residual ? "gap" : `C${cluster.type + 1}`);
    const ports = cluster.residual ? 0 : clusterPortRank(familyIndex);
    const coupledRank = cluster.residual ? 0 : clusterPosePortRank(familyIndex);
    const posePhrase = galleryPose?.support === "finite required set" || !galleryPose
      ? `${poses || "—"} required pose${poses === 1 ? "" : "s"}`
      : galleryPose.support === "sampled continuum" || galleryPose.support === "sampled axial continuum"
        ? `${poses} sampled equivariant pose${poses === 1 ? "" : "s"}`
        : `${poses} observed pose${poses === 1 ? "" : "s"} · unresolved`;
    const learnedDegrees = cluster.residual
      ? "explicit residual"
      : `${posePhrase} × ${ports} port role${ports === 1 ? "" : "s"} · rank ${coupledRank} → ${channels}ch`;
    const classStatus = Number.isInteger(cluster.classIndex)
      ? `isometry ${cluster.classIndex + 1}/${cluster.classCount} · ` : "";
    const supportSites = cluster.customSupport?.length
      || learnedCover.placements.find((placement) => placement.type === cluster.type)?.support.length || 1;
    const chirality = cluster.chirality ? ` · χ ${cluster.chirality}` : "";
    label.innerHTML = `<b>${name}</b><em>${cluster.geometry || "colored support polyhedron"}</em><span>${classStatus}${cluster.element || cluster.species} · ${placements} placement${placements === 1 ? "" : "s"} · ${learnedDegrees}</span><small>${supportSites} colored site${supportSites === 1 ? "" : "s"} · ${clusterCoverRole(cluster)}${chirality}</small><small class="cluster-training-readout" data-cluster-training="${galleryIndex}"></small>`;
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
  updateClusterGalleryTrainingReadouts();
}

function updateClusterGalleryTrainingReadouts() {
  if (!sectionModel || clusterGallery.hidden) return;
  const visible = [...clusterGallery.querySelectorAll(".cluster-card")].filter((card) => !card.hidden).length;
  const status = clusterGallery.querySelector(".cluster-gallery-toolbar p");
  if (status) status.textContent = `GCTS fit ${trainingProgress}/${markingSampleCount()} · showing ${visible}/${clusterGalleryTypes().length} cluster marking scenes`;
  clusterGallery.querySelectorAll("[data-cluster-training]").forEach((readout) => {
    const galleryIndex = Number(readout.dataset.clusterTraining);
    const cluster = clusterGalleryTypes()[galleryIndex];
    if (!cluster || cluster.residual) {
      readout.textContent = "literal terminal · no marking is fitted";
      readout.classList.add("terminal");
      return;
    }
    const prototype = cluster.familyType ?? galleryIndex;
    const processed = sectionModel.sampleLabels.slice(0, trainingProgress)
      .filter((label) => label === prototype).length;
    const total = sectionModel.sampleLabels.filter((label) => label === prototype).length;
    const loss = sectionLossForCluster(prototype);
    readout.textContent = `${processed}/${total} local sections · loss ${loss.toFixed(3)} · ${sectionModel.channels}ch · reach ${sectionModel.reach}`;
    readout.classList.toggle("complete", trainingProgress >= markingSampleCount());
  });
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
  if (![...firstHydrogens, ...secondHydrogens].every((index) => isHydrogenIsotope(sites[index].atom.species))) return null;
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

function drawClusterCardMarking(context, canvas, cluster, galleryIndex, quaternion) {
  if (pipelineStage !== 3 || !sectionModel || cluster.residual) return;
  const prototype = cluster.familyType ?? galleryIndex;
  const coefficients = currentSectionCoefficients(prototype);
  if (!coefficients) return;
  const key = `m_${markingPrototypeName(prototype)}`;
  const positive = markingColor(key);
  const positiveRgb = `${Math.round(positive.r * 255)},${Math.round(positive.g * 255)},${Math.round(positive.b * 255)}`;
  const progress = trainingProgress / Math.max(1, markingSampleCount());
  coefficients.forEach((coefficient, axisIndex) => {
    const axis = sectionModel.axes[axisIndex]?.clone().applyQuaternion(quaternion);
    if (!axis) return;
    const planeLength = Math.hypot(axis.x, axis.y);
    if (planeLength < .08) return;
    const directionX = axis.x / planeLength, directionY = axis.y / planeLength;
    const strength = Math.min(1, Math.abs(coefficient) / .28);
    const centerX = canvas.width / 2 + directionX * (54 + strength * 22);
    const centerY = canvas.height / 2 + directionY * (54 + strength * 22);
    const angle = Math.atan2(directionY, directionX);
    const rgb = coefficient >= 0 ? positiveRgb : "255,109,113";
    for (let level = 2; level >= 0; level--) {
      const transverse = 8 + strength * 7 + level * 3.5;
      const longitudinal = 15 + strength * 13 + level * 5;
      context.save();
      context.translate(centerX, centerY); context.rotate(angle);
      context.beginPath(); context.ellipse(0, 0, longitudinal, transverse, 0, 0, TAU);
      context.strokeStyle = `rgba(${rgb},${(.18 + progress * .18) / (1 + level * .34)})`;
      context.lineWidth = level === 0 ? 1.55 : 1;
      if (coefficient < 0) context.setLineDash([3, 3]);
      context.stroke(); context.restore();
    }
    context.beginPath(); context.arc(centerX, centerY, 2.1 + strength * 1.3, 0, TAU);
    context.fillStyle = `rgba(${rgb},${.48 + progress * .34})`; context.fill();
  });
}

function drawClusterGallery(now) {
  if (pipelineStage !== 3 || clusterGallery.hidden) return;
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
    drawClusterCardMarking(context, canvas, cluster, Number(canvas.dataset.cluster), quaternion);
    topology.faces.map((face) => ({ face, depth: face.reduce((sum, index) => sum + projectedByIndex.get(index).z, 0) / face.length }))
      .sort((first, second) => first.depth - second.depth).forEach(({ face }, faceIndex) => {
        const points = face.map((index) => projectedByIndex.get(index));
        if (points.some((point) => !point)) return;
        context.beginPath(); context.moveTo(points[0].x, points[0].y);
        points.slice(1).forEach((point) => context.lineTo(point.x, point.y));
        context.closePath();
        const faceAlpha = cluster.gap ? .17 : cluster.visualKind === "molecule"
          ? .24 : cluster.visualKind === "bridge" ? .12 + (faceIndex % 3) * .018
            : .075 + (faceIndex % 3) * .018;
        context.fillStyle = `rgba(${surface.join(",")},${faceAlpha})`;
        context.fill();
      });
    topology.edges.forEach(([first, second, kind]) => {
      const start = projectedByIndex.get(first), finish = projectedByIndex.get(second);
      if (!start || !finish) return;
      context.save();
      context.beginPath(); context.moveTo(start.x, start.y); context.lineTo(finish.x, finish.y);
      context.lineWidth = kind === "bond" ? 2.4 : kind === "hydrogen" ? 1.2
        : cluster.visualKind === "molecule" ? 1.9 : 1.5;
      context.strokeStyle = kind === "hydrogen" ? "rgba(147,190,255,.7)" : kind === "outline"
        ? `rgba(${surface.join(",")},${cluster.visualKind === "molecule" ? .72 : .34})`
        : `rgba(${surface.join(",")},.62)`;
      if (kind === "hydrogen") context.setLineDash([3, 4]);
      if (kind === "outline" && cluster.visualKind === "molecule") context.setLineDash([2, 3]);
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
const EXPERIMENT_NOTEBOOK_STORAGE = "gcts-experiment-notebook-v1";
const MAX_EXPERIMENT_NOTEBOOK_ENTRIES = 8;
let notebookClearArmed = false;

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
    clusterToleranceMode,
    effectiveMetricToleranceFraction: effectiveClusterMetricTolerance(),
    effectiveMetricToleranceAngstrom: clusterMetricToleranceAngstrom(),
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
    const tensor = atom.uAnisoCartesianA2?.flat().map((value) => receiptRound(value)) || null;
    return [atom.species, receiptRound(atom.occupancy ?? 1), receiptRound(atom.uIsoA2 ?? 0), tensor,
      ...point.toArray().map((value) => receiptRound(value))];
  }).sort((first, second) => JSON.stringify(first).localeCompare(JSON.stringify(second)));
  return receiptSha256(JSON.stringify(records));
}

function atomOccupancyContributions(atom) {
  const occupational = occupationalAlternatives(atom.species);
  if (occupational) return occupational.alternatives;
  return [{ species: atom.displaySpecies || atom.species, fraction: atom.occupancy ?? 1 }];
}

function receiptComposition(source) {
  const counts = new Map();
  source.forEach((atom) => atomOccupancyContributions(atom).forEach((entry) =>
    counts.set(entry.species, (counts.get(entry.species) || 0) + entry.fraction)));
  return Object.fromEntries([...counts.entries()].sort(([first], [second]) => first.localeCompare(second))
    .map(([species, count]) => [species, receiptRound(count)]));
}

function receiptClusterRecord(cluster, index) {
  const familyIndex = cluster.familyType ?? index;
  const poseModel = galleryPoseModel(cluster);
  const placements = cluster.observedOccurrences ?? cluster.classPlacementIndices?.length
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
    interactiveRepresentativeOccurrences: cluster.classPlacementIndices?.length ?? placements,
    observedProperPoseOrbits: poseModel.orientations,
    properPoseSupport: poseModel.support,
    properSymmetryGaugeCount: poseModel.properSymmetryGaugeCount,
    frameKind: poseModel.frameKind,
    commonProperRotationEquivariant: poseModel.commonProperRotationEquivariant,
    improperRotationsQuotiented: poseModel.improperRotationsQuotiented,
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
    trajectoryIntegrated: false,
    kineticsInferredFromSnapshotOrder: false,
    growthRateClaimed: false,
    targetCoordinatesIncluded: false,
    stationaryProductionCertified: benchmark.status === "pass" && stationaryProductionSystems.has(scenarioId),
    symbolicRecursiveScalingClaimed: symbolicRecursiveScaling,
    genericExponentialGctsClaimed: false,
    finiteFixedPointContinuation: Boolean(trace?.fixedPoint),
    iceProtonOrientationsResolved: trace ? false : null,
  };
}

const COST_SCALING_FACTORS = [10, 1000, 100000];

function formatWorkUnits(value) {
  if (!Number.isFinite(value)) return "—";
  if (value < 1000) return Math.round(value).toLocaleString();
  if (value < 1e6) return `${(value / 1e3).toFixed(value < 1e4 ? 1 : 0)}k`;
  if (value < 1e9) return `${(value / 1e6).toFixed(value < 1e7 ? 1 : 0)}m`;
  if (value < 1e12) return `${(value / 1e9).toFixed(value < 1e10 ? 1 : 0)}b`;
  return value.toExponential(2).replace("e+", "e");
}

function certifiedRecursiveAmplification(benchmark) {
  const claims = receiptGrowthClaims(scenarioSelect.value, benchmark, iceAnchorTrace);
  if (!claims.symbolicRecursiveScalingClaimed || benchmark.curve.length < 2) return null;
  const ratios = benchmark.curve.slice(1).map((count, index) => count / benchmark.curve[index])
    .filter((ratio) => Number.isFinite(ratio) && ratio > 1);
  if (ratios.length !== benchmark.curve.length - 1) return null;
  return Math.exp(ratios.reduce((sum, ratio) => sum + Math.log(ratio), 0) / ratios.length);
}

function computationalCostAudit() {
  const benchmark = currentRecursiveBenchmark();
  const claims = receiptGrowthClaims(scenarioSelect.value, benchmark, iceAnchorTrace);
  const baseSites = Math.max(1, referenceCount());
  const amplification = certifiedRecursiveAmplification(benchmark);
  const scalingLabel = mdWorkScaling === "long-range" ? "O(N log2 N)" : "O(N)";
  const rows = COST_SCALING_FACTORS.map((factor) => {
    const targetSites = baseSites * factor;
    const interactionFactor = mdWorkScaling === "long-range" ? Math.log2(Math.max(2, targetSites)) : 1;
    const mdWork = targetSites * mdHorizonSteps * interactionFactor;
    return {
      sizeMultiplier: factor,
      targetSites,
      symbolicGctsActions: amplification ? Math.ceil(Math.log(factor) / Math.log(amplification)) : null,
      symbolicActionBasis: amplification ? "certified recursive benchmark representation" : "not certified for this material",
      explicitGctsMaterializationWrites: targetSites,
      mdInteractionStepUnits: mdWork.toExponential(6),
    };
  });
  return {
    role: "algorithmic work ledger; no physical trajectory or wall-clock equivalence",
    baseObservedSites: baseSites,
    liveBrowserWork: {
      stageEntered: pipelineStage >= 4,
      currentExplicitSites: atoms.length,
      grammarDecisions,
      acceptedDecisions,
      rejectedDecisions,
      exactLocalConstraintEvaluations: constraintNeighborhoodEvaluations,
      projectedNeighborhoodSites: constraintNeighborhoodSiteTotal,
      maximumProjectedNeighborhoodSites: maximumConstraintNeighborhoodSites,
      mdForceEvaluationsPerformed: 0,
    },
    assumptions: {
      mdHorizonSteps,
      mdInteractionScaling: mdWorkScaling,
      mdInteractionScalingLabel: scalingLabel,
      userSelectableNotInferred: true,
      forceFieldSpecified: false,
      hardwareSpecified: false,
    },
    recursiveRepresentation: {
      certified: claims.symbolicRecursiveScalingClaimed,
      stationaryProductionCertified: claims.stationaryProductionCertified,
      amplificationPerAction: amplification === null ? null : receiptRound(amplification),
      explicitOutputRemainsLinear: true,
    },
    rows,
    boundaries: {
      operationUnitsOnly: true,
      wallTimeCompared: false,
      speedupClaimed: false,
      mdReplacementClaimed: false,
      kineticsModeled: false,
      explicitMaterializationComplexity: "O(N)",
    },
  };
}

function renderComputationalCost() {
  const audit = computationalCostAudit();
  const recursive = audit.recursiveRepresentation;
  costScalingState.className = recursive.certified ? "pass" : "limit";
  costScalingState.textContent = recursive.certified
    ? `${recursive.amplificationPerAction.toFixed(2)}× certified representation`
    : "symbolic recursion not certified";
  const live = audit.liveBrowserWork;
  const tiles = [
    ["explicit sites", live.currentExplicitSites],
    ["tree decisions", live.grammarDecisions],
    ["local tests", live.exactLocalConstraintEvaluations],
    ["neighbor sites inspected", live.projectedNeighborhoodSites],
  ];
  costLiveWork.replaceChildren(...tiles.map(([label, value]) => {
    const tile = document.createElement("span");
    tile.innerHTML = `<small>${label}</small><strong>${formatWorkUnits(value)}</strong>`;
    return tile;
  }));
  costLiveWork.classList.toggle("inactive", !live.stageEntered);
  costScalingTable.replaceChildren();
  const headings = ["scale", "explicit solid", "symbolic GCTS", "emit/write", "MD work units"];
  headings.forEach((label) => {
    const cell = document.createElement("b");
    cell.className = "cost-table-head";
    cell.setAttribute("role", "columnheader");
    cell.textContent = label;
    costScalingTable.appendChild(cell);
  });
  audit.rows.forEach((row) => {
    const cells = [
      `${formatWorkUnits(row.sizeMultiplier)}×`,
      formatWorkUnits(row.targetSites),
      row.symbolicGctsActions === null ? "not certified" : `${row.symbolicGctsActions} actions`,
      formatWorkUnits(row.explicitGctsMaterializationWrites),
      formatWorkUnits(Number(row.mdInteractionStepUnits)),
    ];
    cells.forEach((value, index) => {
      const cell = document.createElement(index === 0 ? "strong" : "span");
      cell.setAttribute("role", "cell");
      cell.classList.toggle("uncertified", index === 2 && row.symbolicGctsActions === null);
      cell.textContent = value;
      costScalingTable.appendChild(cell);
    });
  });
  const livePrefix = live.stageEntered
    ? "Live counters are exact deterministic browser operations."
    : "Enter material growth to populate the live browser counters.";
  costScalingBoundary.textContent = `${livePrefix} MD = ${mdHorizonSteps.toExponential(0).replace("e+", "e")} assumed steps with ${audit.assumptions.mdInteractionScalingLabel} abstract interaction work. Explicit GCTS output still writes O(N) sites. No force field, wall time, kinetics, or speedup is claimed.`;
}

function receiptExternalGeometry() {
  const audit = growthEnvironmentAudit(confinementSelect.value);
  const scale = referenceSpacingA / Math.max(referenceSpacing, 1e-12);
  const source = audit.parametersSceneUnits;
  let parametersAngstrom;
  if (source.halfExtents) parametersAngstrom = { halfExtents: source.halfExtents.map((value) => receiptRound(value * scale)) };
  else if (Number.isFinite(source.radius) && Number.isFinite(source.halfLength)) parametersAngstrom = {
    halfLength: receiptRound(source.halfLength * scale), radius: receiptRound(source.radius * scale),
  };
  else if (Number.isFinite(source.radius)) parametersAngstrom = { radius: receiptRound(source.radius * scale) };
  else if (source.lateralHalfExtents) parametersAngstrom = {
    lateralHalfExtents: source.lateralHalfExtents.map((value) => receiptRound(value * scale)),
    lowerZ: receiptRound(source.lowerZ * scale), upperZ: receiptRound(source.upperZ * scale),
  };
  else parametersAngstrom = {
    halfLength: receiptRound(source.halfLength * scale),
    throatRadius: receiptRound(source.throatRadius * scale),
    radialSlope: source.radialSlope,
  };
  return { ...audit, parametersAngstrom, sceneUnitAngstrom: receiptRound(scale) };
}

function receiptMicrostructureAudit() {
  if (!microstructureEvidence) return null;
  const { adjacencyReach, coordinationBaselines, siteRoles, ...audit } = microstructureEvidence;
  return {
    ...audit,
    mappedSiteCount: siteRoles.length,
    poseInterfaceAtoms: siteRoles.filter((site) => site.poseInterface).length,
    adjacencyReachSceneUnits: receiptRound(adjacencyReach),
    adjacencyReachAngstrom: receiptRound(adjacencyReach * referenceSpacingA / referenceSpacing),
    coordinationBaselines: coordinationBaselines.map((entry) => ({
      ...entry,
      median: receiptRound(entry.median),
      mad: receiptRound(entry.mad),
      anomalyThreshold: receiptRound(entry.anomalyThreshold),
    })),
  };
}

function receiptEmergentClassification() {
  const inference = inferLiveOrder();
  return {
    status: currentMaterial().growthWithheld ? "withheld; occupational realization unresolved"
      : pipelineStage < 4 ? "withheld until material growth" : inference.order,
    stageGate: currentMaterial().growthWithheld ? "material growth unavailable for average occupancy" : "material growth only",
    minimumLiveAtoms: PHASE_CLASSIFICATION_MINIMUM_ATOMS,
    maximumContiguousAnalysisWindowAtoms: ANALYSIS_WINDOW_COUNT,
    decisionThreshold: PHASE_CLASSIFICATION_THRESHOLD,
    atomCountMatchedAcrossPrototypeWindows: true,
    comparisonRadiusMatchedAcrossPrototypeWindows: true,
    intrinsicDimensionInferredFromPositionCovariance: true,
    curatedIntrinsicDimensionUsed: false,
    absoluteOriginUsedForWindowSelection: false,
    posthocOnly: true,
    usedAsGrowthInput: false,
    usedForCandidateAdmission: false,
    usedForBranchRanking: false,
    independentPhaseDetermination: false,
    prototypeComparisonWeights: { rdf: .30, coordination: .58, geometricPowderStructureFactor: .20 },
    selectedFixturePresentInPrototypeLibrary: inference.selectedFixturePresentInPrototypeLibrary ?? null,
    current: {
      order: inference.order,
      structure: inference.structure,
      symmetry: inference.symmetry,
      confidence: receiptRound(inference.confidence),
      liveAtoms: inference.liveAtoms,
      analysisWindowAtoms: inference.sampleAtoms,
      availableAnalysisAtoms: inference.availableAnalysisAtoms ?? inference.sampleAtoms,
      inferredDimension: inference.inferredDimension || null,
      planarityRatio: inference.planarityRatio === undefined ? null : receiptRound(inference.planarityRatio),
      localPlanarityRatio: inference.localPlanarityRatio === undefined ? null : receiptRound(inference.localPlanarityRatio),
      dimensionInferenceBasis: inference.dimensionInferenceBasis || null,
      comparisonRadiusInNearestNeighborUnits: inference.comparisonRadius === undefined ? null : receiptRound(inference.comparisonRadius),
      matchedPrototypeAtomCount: inference.matchedPrototypeAtomCount || null,
      bestPrototypeId: inference.bestPrototypeId || null,
      bestPrototypeEvidenceMatch: inference.bestPrototypeEvidenceMatch === undefined ? null : receiptRound(inference.bestPrototypeEvidenceMatch),
      runnerUpPrototypeId: inference.runnerUpPrototypeId || null,
      runnerUpPrototypeEvidenceMatch: inference.runnerUpPrototypeEvidenceMatch === undefined ? null : receiptRound(inference.runnerUpPrototypeEvidenceMatch),
      prototypeMargin: inference.prototypeMargin === undefined ? null : receiptRound(inference.prototypeMargin),
      bestPrototypeResolved: inference.bestPrototypeResolved ?? false,
      crystalPrototypeMargin: inference.crystalPrototypeMargin === undefined ? null : receiptRound(inference.crystalPrototypeMargin),
      crystalPrototypeResolved: inference.crystalPrototypeResolved ?? false,
      leaveSelectedFixtureOut: {
        bestPrototypeId: inference.independentBestPrototypeId || null,
        bestPrototypeOrder: inference.independentBestPrototypeOrder || null,
        evidenceMatch: inference.independentBestPrototypeEvidenceMatch === undefined ? null : receiptRound(inference.independentBestPrototypeEvidenceMatch),
        runnerUpPrototypeId: inference.independentRunnerUpPrototypeId || null,
        prototypeMargin: inference.independentPrototypeMargin === undefined ? null : receiptRound(inference.independentPrototypeMargin),
        usedForDisplayedClassification: false,
      },
      rdfError: inference.rdfError === undefined ? null : receiptRound(inference.rdfError),
      coordinationError: inference.coordinationError === undefined ? null : receiptRound(inference.coordinationError),
      geometricPowderStructureFactorError: inference.structureFactorError === undefined ? null : receiptRound(inference.structureFactorError),
      translationClosure: inference.translationClosure === undefined ? null : receiptRound(inference.translationClosure),
      prototypeLibrarySize: inference.prototypeLibrarySize || null,
    },
    trajectory: liveOrderHistory.map((entry) => ({
      acceptedDecisions: entry.acceptedDecisions,
      liveAtoms: entry.liveAtoms,
      analysisWindowAtoms: entry.sampleAtoms,
      order: entry.order,
      confidence: receiptRound(entry.confidence),
      bestPrototypeId: entry.bestPrototypeId,
      bestPrototypeEvidenceMatch: entry.bestPrototypeEvidenceMatch === null ? null : receiptRound(entry.bestPrototypeEvidenceMatch),
      prototypeMargin: entry.prototypeMargin === null ? null : receiptRound(entry.prototypeMargin),
      independentBestPrototypeId: entry.independentBestPrototypeId,
      independentBestPrototypeEvidenceMatch: entry.independentBestPrototypeEvidenceMatch === null
        ? null : receiptRound(entry.independentBestPrototypeEvidenceMatch),
      translationClosure: entry.translationClosure === null ? null : receiptRound(entry.translationClosure),
    })),
    coordinatesEmbedded: false,
  };
}

async function buildExperimentReceipt() {
  const material = currentMaterial();
  const markingConfig = currentMarkingConfig();
  const activeMarking = selectedMarking();
  const benchmark = currentRecursiveBenchmark();
  const cell = currentCell();
  const coverVisible = pipelineStage >= 1;
  const markingVisible = pipelineStage >= 3;
  const searchVisible = pipelineStage >= 4;
  const referenceSq = ensureStructureFactor(referenceStructuralStats);
  const trajectoryFrames = scenarioSelect.value === "imported" ? importedTrajectoryFrames() : [];
  const recordedConditions = activeMeasurementConditions();
  const trajectoryFrameDigests = trajectoryFrames.length > 1
    ? await Promise.all(trajectoryFrames.map((frame) => structureDigest(makeImportedFrameReference(frame, 1), "angstrom")))
    : [];
  const receipt = {
    schema: "gcts-materials-growth-receipt-v1",
    generatedAt: new Date().toISOString(),
    application: {
      name: "Materials Growth Lab",
      buildId: "20260825-91",
      pipelineStages: ["sample configuration", "cluster identification", "GCTS learning", "material growth"],
    },
    input: {
      sourceKind: scenarioSelect.value === "imported"
        ? (importedStructure?.metadata?.entryId ? "public-database structure" : "locally parsed structure")
        : "deterministic curated fixture",
      scenarioId: scenarioSelect.value,
      materialName: material.name,
      elements: material.actualElements ? [...material.actualElements] : [...material.elements],
      siteChemistryChannels: [...material.elements],
      composition: receiptComposition(referenceAtoms),
      atomCount: referenceAtoms.length,
      externalGeometry: receiptExternalGeometry(),
      recordedMeasurementConditions: recordedConditions ? {
        provenance: recordedConditions.provenance || "recorded diffraction/cell-measurement conditions",
        temperatureKelvin: recordedConditions.temperature?.value ?? null,
        temperatureSourceTag: recordedConditions.temperature?.sourceTag ?? null,
        temperatureDeprecatedFallback: recordedConditions.temperature?.deprecatedFallback ?? null,
        pressureKilopascal: recordedConditions.pressure?.value ?? null,
        pressureSourceTag: recordedConditions.pressure?.sourceTag ?? null,
        pressureDeprecatedFallback: recordedConditions.pressure?.deprecatedFallback ?? null,
        environment: recordedConditions.environment?.value ?? null,
        environmentSourceTag: recordedConditions.environment?.sourceTag ?? null,
        usedAsSimulationControl: false,
        temperatureInferred: false,
        pressureInferred: false,
        synthesisConditionsClaimed: false,
        thermodynamicStateReconstructed: false,
      } : null,
      crystallographicOccupancy: scenarioSelect.value === "imported" ? {
        representation: "one geometric site with a finite element-fraction alternative set; vacancy retained explicitly",
        mixedSites: importedStructure?.validation?.mixedOccupancySites || 0,
        partialSites: importedStructure?.validation?.partialOccupancySites || 0,
        inferredEqualFractionSites: importedStructure?.validation?.inferredOccupancySites || 0,
        totalVacancyFraction: receiptRound(importedStructure?.validation?.vacancyFraction || 0),
        formalChargeCoverage: receiptRound(importedStructure?.validation?.formalChargeCoverage || 0),
        formalChargeResolvedSites: importedStructure?.validation?.chargeResolvedSites || 0,
        netSuppliedCellFormalCharge: receiptRound(importedStructure?.validation?.netFormalCharge || 0),
        occupationalChemistryTokens: [...new Set(referenceAtoms.map((atom) => atom.species))].sort(),
        alternativesCollapsedToPrimarySpecies: false,
      } : material.crystallographicOccupancy ? {
        ...material.crystallographicOccupancy,
        totalVacancyFraction: receiptRound(material.crystallographicOccupancy.totalVacancyFraction),
        occupationalChemistryTokens: [...new Set(referenceAtoms.map((atom) => atom.species))].sort(),
        alternativesCollapsedToPrimarySpecies: false,
        uniqueMolecularAssignmentClaimed: false,
        sourceAverageUniquelyDeterminesAssignment: false,
        occupationalAlternativeSelectionPerformed: Boolean(iceViMicrostate),
        sampledIceRuleMicrostate: iceViMicrostate ? {
          ...iceViMicrostate.audit,
          sourceAverageSites: generateIceViAverageObservation().atoms.length,
          sourceOccupancyWeightedAtoms: MATERIALS.iceVI.occupancyWeightedAtomCount,
          selectedBeforeClusterLearning: true,
          selectedByTargetOrGrowthScore: false,
          claimedAsExperimentalInstantaneousConfiguration: false,
        } : null,
      } : null,
      structureSha256: await structureDigest(referenceAtoms, "angstrom"),
      trajectoryEnsemble: trajectoryFrames.length > 1 ? {
        frameCount: trajectoryFrames.length,
        selectedFrameIndexZeroBased: importedFrameIndex,
        geometricEvidenceMode: ensembleEvidenceMode,
        geometricEvidenceFrameCount: coloredDistanceEnvelopes.frameCount,
        geometricEvidenceAtomPresentations: coloredDistanceEnvelopes.atomPresentations,
        fixedTopologyAndAtomOrderRequired: true,
        topologyConsistent: importedStructure.validation.trajectoryTopologyConsistent,
        variableCell: importedStructure.validation.trajectoryVariableCell,
        frameStructureSha256: trajectoryFrameDigests,
        ensembleSha256: await receiptSha256(JSON.stringify(trajectoryFrameDigests)),
        framesUsedForDistanceCoordinationAngleEnvelopes: coloredDistanceEnvelopes.frameCount,
        framesUsedForClusterCover: 1,
        framesUsedForPortGrammarAndMarking: 1,
        framesUsedForGrowthSeed: 1,
        crossFrameAtomPairsConstructed: false,
        temporalOrderingUsed: false,
        velocitiesUsed: false,
        forcesUsed: false,
        integrationTimeStepUsed: false,
        independentSampleCountClaimed: false,
      } : null,
      coordinatesEmbedded: false,
      coordinateDigestSpace: "Cartesian Å + occupancy token + isotropic U / optional Cartesian Uij in Å²; order-independent serialization",
      periodicBoundary: currentPbc(),
      cellAngstrom: cell?.map((vector) => vector.toArray().map((value) => receiptRound(value))) || null,
      sourceReference: scenarioSelect.value === "imported" ? {
        name: importedStructure?.metadata?.name || importedStructure?.filename || null,
        entryId: importedStructure?.metadata?.entryId || null,
        materialId: importedStructure?.metadata?.materialId || null,
        format: importedStructure?.format || null,
      } : { fixture: scenarioSelect.value,
        generatorAudit: scenarioSelect.value === "random" ? referenceAtoms[0]?.glassAudit || null : null,
        publishedModel: material.fixtureProvenance ? {
          fixtureId: material.fixtureProvenance.id,
          articleDoi: material.fixtureProvenance.articleDoi,
          archiveDoi: material.fixtureProvenance.archiveDoi || null,
          sourceUrl: material.fixtureProvenance.sourceUrl || null,
          license: material.fixtureProvenance.license,
          archiveSha256: material.fixtureProvenance.archiveSha256 || material.fixtureProvenance.sourceSha256 || null,
          normalizedAtomsSha256: material.fixtureProvenance.normalizedAtomsSha256 || null,
          generatorVersion: material.fixtureProvenance.generatorVersion || null,
          sourceRevision: material.fixtureProvenance.sourceRevision || null,
          crop: material.fixtureProvenance.crop || null,
          sourceSitesEmbedded: false,
          cutAndProjectCoordinatesEmbedded: false,
          phaseLabelUsedByLearner: false,
        } : null },
    },
    pipeline: {
      internalStage: pipelineStage,
      visibleStage: visiblePipelineOrdinal(pipelineStage),
      stageName: ["sample configuration", "cluster identification", "rigid encoding", "GCTS learning", "material growth"][pipelineStage],
      reversibleProcessTimeline: processTimelineRecord(),
    },
    computationalWork: computationalCostAudit(),
    geometry: {
      requestedMode: geometryMode,
      metricIsometryToleranceMode: clusterToleranceMode,
      nominalMetricIsometryToleranceFractionOfNearestNeighbor: clusterMetricTolerance(),
      metricIsometryToleranceFractionOfNearestNeighbor: receiptRound(effectiveClusterMetricTolerance()),
      metricIsometryToleranceAngstrom: receiptRound(clusterMetricToleranceAngstrom()),
      positionalUncertainty: {
        source: [activeImportedFrameValidation()?.thermalDisplacementSites ? "CIF/JSON isotropic or anisotropic U/B" : null,
          ensemblePairDistanceUncertainty?.available ? "fixed-topology snapshot pair distances" : null].filter(Boolean).join(" + ") || "not supplied",
        toleranceFloorSource: measuredPairUncertaintySource(),
        isotropicSites: activeImportedFrameValidation()?.thermalDisplacementSites || 0,
        anisotropicTensorSites: activeImportedFrameValidation()?.anisotropicDisplacementSites || 0,
        medianOneAxisSigmaAngstrom: receiptRound(activeImportedFrameValidation()?.medianThermalSigmaA || 0),
        maximumOneAxisSigmaAngstrom: receiptRound(activeImportedFrameValidation()?.maximumThermalSigmaA || 0),
        maximumPrincipalAxisSigmaAngstrom: receiptRound(activeImportedFrameValidation()?.maximumThermalAxisSigmaA || 0),
        pairDistanceOneSigmaFloorAngstrom: receiptRound(measuredPairUncertaintyAngstrom()),
        empiricalSnapshotPairDistances: ensemblePairDistanceUncertainty?.available ? {
          frameCount: ensemblePairDistanceUncertainty.frameCount,
          atomPresentations: ensemblePairDistanceUncertainty.atomPresentations,
          localPairCount: ensemblePairDistanceUncertainty.localPairCount,
          localCutoffAngstrom: receiptRound(ensemblePairDistanceUncertainty.localCutoff),
          medianPairDistanceSigmaAngstrom: receiptRound(ensemblePairDistanceUncertainty.medianPairDistanceSigma),
          upperQuantile: ensemblePairDistanceUncertainty.upperQuantile,
          upperPairDistanceSigmaAngstrom: receiptRound(ensemblePairDistanceUncertainty.upperPairDistanceSigma),
          maximumPairDistanceSigmaAngstrom: receiptRound(ensemblePairDistanceUncertainty.maximumPairDistanceSigma),
          crossFramePairsConstructed: false,
          temporalOrderingUsed: false,
          independentSampleCountClaimed: false,
        } : null,
        usedAsPotentialOrDynamics: false,
      },
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
        frameKind: entry.frameKind || "laboratory directional fallback",
        properSymmetryGaugeCount: entry.properSymmetryGaugeCount || null,
        globalTranslationInvariant: entry.globalTranslationInvariant ?? null,
        commonProperRotationEquivariant: entry.commonProperRotationEquivariant ?? null,
        improperRotationsQuotiented: entry.improperRotationsQuotiented ?? null,
      })),
      coloredDistanceEnvelopes: {
        role: "hard geometric exclusion learned from supplied positions; not a pair potential",
        frameCount: coloredDistanceEnvelopes.frameCount,
        atomPresentations: coloredDistanceEnvelopes.atomPresentations,
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
        frameCount: coloredCoordinationEnvelopes.frameCount,
        atomPresentations: coloredCoordinationEnvelopes.atomPresentations,
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
        frameCount: coloredAngularEnvelopes.frameCount,
        atomPresentations: coloredAngularEnvelopes.atomPresentations,
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
      formalChargeReservoir: {
        role: "optional supplied oxidation-state bookkeeping used only for soft ordering; not charge density, Coulomb energy, redox chemistry, electron transfer, dielectric screening, potential, or chemical potential",
        available: formalChargeTarget.available,
        source: formalChargeTarget.source,
        coverage: receiptRound(formalChargeTarget.coverage),
        resolvedObservations: formalChargeTarget.resolvedObservations,
        observations: formalChargeTarget.observations,
        netReferenceFormalCharge: receiptRound(formalChargeTarget.netFormalCharge),
        meanReferenceFormalChargePerSite: formalChargeTarget.meanFormalCharge === null ? null : receiptRound(formalChargeTarget.meanFormalCharge),
        oxidationStatesInferred: false,
      },
      multiscalePassport: {
        role: "live material- and stage-specific map from observed structural evidence to geometric encoding and explicit claim boundaries",
        coordinateDataEmbedded: false,
        structuralScalesEncoded: liveScalePassportRecords().filter((record) => ["reached", "active"].includes(record.status)).length,
        kineticsModeled: false,
        scales: liveScalePassportRecords().map((record) => ({
          id: record.id,
          label: record.label,
          status: record.status,
          scale: record.scale,
          evidence: record.evidence,
          geometricEncoding: record.encoding,
          searchRole: record.role,
          claimBoundary: record.boundary,
        })),
      },
      observationProvenanceChain: {
        role: "coordinate-free audit of how recorded conditions, structural samples, and uncertainty enter or do not enter geometry learning and growth",
        simulationControlChannelsFromRecordedConditions: 0,
        coordinatesEmbedded: false,
        records: observationProvenanceRecords(),
      },
    },
    structuralEvidence: {
      role: "posthoc validation only; never a growth feature or branch score",
      emergentClassification: receiptEmergentClassification(),
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
      emptyRegionBoundaries: learnedCover.voidBoundary || null,
      heterogeneousGeometryAudit: receiptMicrostructureAudit(),
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
      experimentProtocol: growthProtocolManifest(),
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
        affineLoadMode,
        affineLoadLabel: affineLoadModeLabel(),
        prescribedStrainMagnitude: affineLoadMode === "none" ? 0 : affineLoadMagnitude,
        deformationGradient: affineLoadTensor().map((row) => row.map((value) => receiptRound(value))),
        acceptedMean: receiptRound(acceptedGeometricStrain / Math.max(1, acceptedDecisions)),
        rejectedMean: receiptRound(rejectedGeometricStrain / Math.max(1, rejectedDecisions)),
        unloadedAcceptedMean: receiptRound(acceptedUnloadedGeometricStrain / Math.max(1, acceptedDecisions)),
        unloadedRejectedMean: receiptRound(rejectedUnloadedGeometricStrain / Math.max(1, rejectedDecisions)),
        candidateCoordinatesChanged: false,
        hardAdmissionChanged: false,
        modulusOrStressInferred: false,
      },
      compositionBalanceRanking: {
        role: "target-blind soft ordering toward the observed multicomponent reservoir; never a hard surface constraint",
        mode: compositionPreference,
        effectiveWeight: activeCompositionBalanceWeight(),
        targetReducedRatio: compositionTarget.reducedRatio,
        acceptedMeanScaledDelta: receiptRound(acceptedCompositionDelta / Math.max(1, acceptedDecisions)),
        rejectedMeanScaledDelta: receiptRound(rejectedCompositionDelta / Math.max(1, rejectedDecisions)),
      },
      formalChargeBalanceRanking: {
        role: "target-blind soft ordering toward the supplied mean formal charge per site; never a hard surface constraint or electrostatic energy",
        mode: chargePreference,
        available: formalChargeTarget.available,
        enabled: activeFormalChargeWeight() > 0,
        effectiveWeight: activeFormalChargeWeight(),
        referenceMeanFormalChargePerSite: formalChargeTarget.meanFormalCharge === null ? null : receiptRound(formalChargeTarget.meanFormalCharge),
        acceptedMeanScaledDelta: receiptRound(acceptedFormalChargeDelta / Math.max(1, acceptedDecisions)),
        rejectedMeanScaledDelta: receiptRound(rejectedFormalChargeDelta / Math.max(1, rejectedDecisions)),
      },
      surfaceCompletionRanking: {
        role: "target-blind soft ordering that favors healing sample-derived coordination deficits; not bond or surface energy",
        mode: surfacePreference,
        effectiveWeight: activeSurfaceCompletionWeight(),
        target: "ordered species coordination medians learned from the supplied configuration",
        acceptedMeanScaledDelta: receiptRound(acceptedSurfaceDeficit / Math.max(1, acceptedDecisions)),
        rejectedMeanScaledDelta: receiptRound(rejectedSurfaceDeficit / Math.max(1, rejectedDecisions)),
      },
      mesoscopicFrontMorphologyRanking: {
        role: "target-blind soft ordering of unchanged exact actions by parent-local angular support and backing-depth geometry",
        mode: frontMorphologyMode,
        label: frontMorphologyLabel(),
        enabled: activeFrontMorphologyWeight() > 0,
        effectiveWeight: activeFrontMorphologyWeight(),
        angularSectorCount: 8,
        neighborhoodReachNearestNeighborUnits: 2.4,
        acceptedMeanScore: receiptRound(acceptedFrontMorphologyScore / Math.max(1, acceptedDecisions)),
        rejectedMeanScore: receiptRound(rejectedFrontMorphologyScore / Math.max(1, rejectedDecisions)),
        evaluations: frontMorphologyEvaluations,
        neighborhoodChecks: frontMorphologyNeighborhoodChecks,
        localFrame: "parent proper-SE(3) tangent frame + parent-to-candidate normal",
        candidateSetChanged: false,
        candidateGeometryChanged: false,
        hardAdmissionChanged: false,
        heldoutTargetUsed: false,
        meanCurvatureInferred: false,
        surfaceEnergyInferred: false,
        capillaryPressureInferred: false,
        physicalTimeIntegrated: false,
      },
      epitaxialRegistryRanking: {
        role: "user-declared target-blind support-plane template ranks unchanged exact interfacial actions",
        mode: epitaxyTemplateMode,
        label: epitaxyTemplateLabel(),
        enabled: activeEpitaxyWeight() > 0,
        requiredEnvironment: "substrate",
        activeEnvironment: confinementSelect.value,
        effectiveWeight: activeEpitaxyWeight(),
        template: epitaxyTemplateSpec(),
        interactionReachNearestNeighborUnits: 3.5,
        acceptedMeanScore: receiptRound(acceptedEpitaxyRegistryScore / Math.max(1, acceptedDecisions)),
        rejectedMeanScore: receiptRound(rejectedEpitaxyRegistryScore / Math.max(1, rejectedDecisions)),
        evaluations: epitaxyRegistryEvaluations,
        freshSiteChecks: epitaxyRegistrySiteChecks,
        substrateAtomsPresent: false,
        candidateSetChanged: false,
        candidateGeometryChanged: false,
        hardAdmissionChanged: false,
        heldoutTargetUsed: false,
        adhesionEnergyInferred: false,
        interfaceEnergyInferred: false,
        epitaxialRelaxationModeled: false,
        dislocationNetworkInferred: false,
      },
      externalDrivingGeometry: {
        role: "user-declared target-blind soft ordering of unchanged exact candidate actions by parent-to-child direction",
        mode: externalDriveMode,
        label: externalDriveModeLabel(),
        enabled: activeExternalDriveWeight() > 0,
        effectiveWeight: activeExternalDriveWeight(),
        globalAxis: externalDriveMode === "z-plus" ? [0, 0, 1]
          : externalDriveMode === "z-minus" ? [0, 0, -1] : null,
        seedRelative: externalDriveMode === "radial-out" || externalDriveMode === "radial-in",
        acceptedMeanAlignment: receiptRound(acceptedExternalDriveAlignment / Math.max(1, acceptedDecisions)),
        rejectedMeanAlignment: receiptRound(rejectedExternalDriveAlignment / Math.max(1, rejectedDecisions)),
        candidateGeometryChanged: false,
        targetUsed: false,
        physicalFieldSolved: false,
      },
      constraintRobustnessRanking: {
        role: "target-blind soft ordering of unchanged exact actions by the smallest normalized geometric safety margin",
        mode: robustnessPreference,
        enabled: activeRobustnessWeight() > 0,
        effectiveWeight: activeRobustnessWeight(),
        acceptedMeanScore: receiptRound(acceptedRobustnessScore / Math.max(1, acceptedDecisions)),
        rejectedMeanScore: receiptRound(rejectedRobustnessScore / Math.max(1, rejectedDecisions)),
        candidateGeometryChanged: false,
        hardAdmissionChanged: false,
        targetUsed: false,
        temperatureModeled: false,
        probabilityInferred: false,
        freeEnergyInferred: false,
        perturbationEnsembleUsedForRanking: false,
      },
      microstructureCouplingRanking: {
        role: "user-declared soft coupling to frozen input-derived heterogeneous-geometry roles over unchanged exact actions",
        mode: microstructureCouplingMode,
        label: microstructureCouplingLabel(),
        enabled: activeMicrostructureCouplingWeight() > 0,
        effectiveWeight: activeMicrostructureCouplingWeight(),
        acceptedMeanScore: receiptRound(acceptedMicrostructureCouplingScore / Math.max(1, acceptedDecisions)),
        rejectedMeanScore: receiptRound(rejectedMicrostructureCouplingScore / Math.max(1, rejectedDecisions)),
        observedInputGeometryUsed: true,
        heldoutTargetUsed: false,
        defectLabelsUsed: false,
        candidateGeometryChanged: false,
        hardAdmissionChanged: false,
        formationEnergyInferred: false,
        mobilityInferred: false,
      },
      mesoscopicLoopClosureRanking: {
        role: "target-blind multi-parent consensus over complete transformed colored site sets from frozen proper-SE(3) connection rules",
        mode: loopClosurePreference,
        enabled: activeLoopClosureWeight() > 0,
        effectiveWeight: activeLoopClosureWeight(),
        acceptedMeanScore: receiptRound(acceptedLoopClosureScore / Math.max(1, acceptedDecisions)),
        rejectedMeanScore: receiptRound(rejectedLoopClosureScore / Math.max(1, rejectedDecisions)),
        acceptedMeanIndependentCompatiblePaths: receiptRound(acceptedIndependentLoopWitnesses / Math.max(1, acceptedDecisions)),
        rejectedMeanIndependentCompatiblePaths: receiptRound(rejectedIndependentLoopWitnesses / Math.max(1, rejectedDecisions)),
        generatingParentExcludedFromConsensus: true,
        frozenConnectionRulesOnly: true,
        candidateGeometryChanged: false,
        hardAdmissionChanged: false,
        heldoutTargetUsed: false,
        elasticEnergyInferred: false,
        modulusOrStressInferred: false,
      },
      geometricArrivalPathRanking: {
        role: "soft kinetic-accessibility proxy from swept hard-core clearance of emitted sites along a declared arrival direction",
        mode: arrivalPathMode,
        label: arrivalPathLabel(),
        enabled: activeArrivalPathWeight() > 0,
        declaredDirectionAvailable: arrivalPathMode !== "declared-drive" || externalDriveMode !== "none",
        effectiveWeight: activeArrivalPathWeight(),
        sampleCountPerSite: arrivalPathMode === "none" ? 0 : 9,
        sweepDistanceNearestNeighborUnits: 2,
        acceptedMeanScore: receiptRound(acceptedArrivalPathScore / Math.max(1, acceptedDecisions)),
        rejectedMeanScore: receiptRound(rejectedArrivalPathScore / Math.max(1, rejectedDecisions)),
        acceptedBlockedSiteSamples: acceptedBlockedPathSamples,
        rejectedBlockedSiteSamples: rejectedBlockedPathSamples,
        totalSiteSamples: arrivalPathSiteSamples,
        neighborhoodChecks: arrivalPathNeighborhoodChecks,
        emittedSitesOnly: true,
        intermediateBoundaryEnforced: false,
        candidateGeometryChanged: false,
        hardAdmissionChanged: false,
        heldoutTargetUsed: false,
        barrierOrRateInferred: false,
        physicalTimeIntegrated: false,
      },
      configurationalPathEnsemble: {
        role: "reproducible Gumbel ordering over the unchanged exact frontier after all declared geometric terms",
        dimensionlessExplorationScale: geometricExplorationScale,
        seed: growthPathSeed,
        mode: geometricExplorationScale > 0 ? "sampled exact branch ordering" : "greedy deterministic ordering",
        acceptedMeanOffset: receiptRound(acceptedExplorationOffset / Math.max(1, acceptedDecisions)),
        rejectedMeanOffset: receiptRound(rejectedExplorationOffset / Math.max(1, rejectedDecisions)),
        hashInputs: ["growthPathSeed", "eventIndex", "candidateKey"],
        candidateSetChanged: false,
        hardAdmissionChanged: false,
        exactCandidateGeometryChanged: false,
        physicalTemperatureKelvin: null,
        energyUnitsUsed: false,
        boltzmannDistributionClaimed: false,
        freeEnergyInferred: false,
        physicalTimeIntegrated: false,
      },
      multiNucleusGrowth: {
        role: "geometry-only co-growth from farthest-separated cluster occurrences already present in the supplied configuration",
        requestedNuclei: requestedGrowthNuclei,
        initializedNuclei: initializedGrowthNuclei,
        selection: "deterministic farthest-point traversal of observed cluster occurrence centers",
        orientations: "observed proper-SE(3) occurrence poses; no artificial grain rotation",
        coalescenceEvents,
        crossNucleusSharedSiteContacts: crossNucleusMergeContacts,
        pairwiseOrientationRelationships: growthNucleusPairs().map((pair) => ({
          nuclei: [pair.first.nucleusId, pair.second.nucleusId],
          clusterTypes: [pair.first.type, pair.second.type],
          comparableColoredMetricClass: pair.misorientation.comparable,
          properSymmetryReducedMisorientationDegrees: pair.misorientation.angleDegrees === null
            ? null : receiptRound(pair.misorientation.angleDegrees),
          properGaugePairsMinimized: pair.misorientation.properGaugePairs,
          improperRotationsQuotiented: false,
          seedCenterSeparationAngstrom: receiptRound(pair.centerSeparationAngstrom),
          sharedSpeciesLabeledSites: pair.sharedSites,
          sharedSiteFractionOfSmallerLineage: receiptRound(pair.sharedSiteFraction),
          targetUsed: false,
        })),
        interfaceVisualization: "cyan rings mark sites shared by lineages from different initialized nuclei",
        exactSpeciesAndCollisionGatesPreserved: true,
        targetUsedToSelectSeeds: false,
        nucleationRateInferred: false,
        grainIdentityInferred: false,
        interfacialEnergyInferred: false,
        physicalTimeIntegrated: false,
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
      structuralLeapCertificates: leapHistory.map((leap) => ({
        index: leap.index, status: leap.status, label: leap.label,
        before: leap.before, proposal: leap.proposal, tests: leap.tests, after: leap.after,
        targetUsed: leap.targetUsed, physicalTimeModeled: leap.physicalTimeModeled,
        dynamicsIntegrated: leap.dynamicsIntegrated, claimBoundary: leap.claimBoundary,
        physicsTranslation: leap.physicsTranslation,
      })),
      spatialGrowthEventAudit: growthMechanismAudit(),
      policySensitivity: {
        role: "counterfactual soft-physics rankings over one unchanged hard-admitted candidate set; previews never execute",
        maximumStoredFrontiers: 48,
        candidateCoordinatesEmbedded: false,
        snapshots: policyComparisonHistory.map((snapshot) => ({
          index: snapshot.index,
          frontierCandidates: snapshot.frontier,
          hardAdmittedCandidates: snapshot.admissible,
          candidateSetDigest: snapshot.candidateDigest,
          candidateSetTargetUsed: snapshot.candidateSetTargetUsed,
          rankingTargetUsed: snapshot.rankingTargetUsed,
          rankingMode: snapshot.referenceGuided ? "known-window reference-guided replay" : "target-blind frontier",
          distinctTopActions: snapshot.uniqueTopActions,
          policies: snapshot.policies.map((policy) => ({
            id: policy.id,
            label: policy.label,
            action: policy.action,
            selectedCandidateDigest: policy.candidateDigest,
            score: policy.score === null ? null : receiptRound(policy.score),
          })),
        })),
      },
      finiteIceAnchorTrace: iceAnchorTrace ? {
        artifactDigest: iceAnchorTrace.artifactDigest,
        caseId: iceAnchorTrace.caseId,
        moleculeLabel: iceAnchorTrace.moleculeLabel,
        conformerTypes: iceAnchorTrace.conformerTypes,
        frozenPorts: iceAnchorTrace.portCount,
        selectionRule: iceAnchorTrace.selectionRuleLabel,
        seedAnchors: iceAnchorTrace.seedAnchors,
        waves: iceAnchorTrace.waves.map((wave) => ({
          wave: wave.wave,
          candidateAnchors: wave.candidateAnchors,
          acceptedAnchors: wave.acceptedAnchors,
          retainedOrientationHypotheses: wave.retainedOrientationHypotheses,
          rejectedNonunanimousAnchors: wave.rejectedNonunanimousAnchors,
          rejectedCandidateAnchors: wave.rejectedCandidateAnchors,
          candidateDigest: wave.candidateDigest,
        })),
        emittedAnchorCount: iceAnchorTrace.emittedAnchors.length,
        unresolvedOrientationDomains: iceAnchorTrace.unresolvedOrientationHypotheses,
        targetUsed: iceAnchorTrace.targetUsed,
        fixedPoint: iceAnchorTrace.fixedPoint,
        exactBackendCountParity: iceAnchorTrace.exactBackendCountParity,
        provenance: iceAnchorTrace.provenance,
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

function notebookInterventionFactors(receipt) {
  const search = receipt.search?.explicitSites === undefined ? null : receipt.search;
  const activeMarking = receipt.marking?.active;
  const cost = receipt.computationalWork;
  const serialized = (value) => JSON.stringify(value);
  return {
    pipeline: { label: "pipeline extent", role: "execution", value: `${receipt.pipeline.stageName}:${receipt.pipeline.visibleStage}` },
    boundary: { label: "external boundary", role: "geometry", value: serialized({
      kind: receipt.input.externalGeometry?.kind,
      periodic: receipt.input.periodicBoundary,
      parametersAngstrom: receipt.input.externalGeometry?.parametersAngstrom,
    }) },
    clustering: { label: "cluster geometry", role: "geometry", value: serialized({
      requested: receipt.geometry.requestedMode,
      resolved: receipt.geometry.resolvedMode,
      toleranceMode: receipt.geometry.metricIsometryToleranceMode,
      toleranceAngstrom: receipt.geometry.metricIsometryToleranceAngstrom,
    }) },
    marking: { label: "GCTS marking", role: "learned representation", value: serialized({
      config: receipt.marking.config,
      searchMode: receipt.marking.searchMode,
      activeId: activeMarking?.id || null,
      vocabularyKey: activeMarking?.vocabularyKey || null,
    }) },
    ranking: { label: "frontier ranking", role: "search", value: search?.policy || "not entered" },
    protocol: { label: "growth protocol", role: "experiment", value: serialized(search?.experimentProtocol || null) },
    softPhysics: { label: "soft physics ordering", role: "search", value: serialized(search ? {
      strain: [search.geometricStrainRanking?.mode, search.geometricStrainRanking?.effectiveWeight,
        search.geometricStrainRanking?.affineLoadMode, search.geometricStrainRanking?.prescribedStrainMagnitude],
      composition: [search.compositionBalanceRanking?.mode, search.compositionBalanceRanking?.effectiveWeight],
      formalCharge: [search.formalChargeBalanceRanking?.mode, search.formalChargeBalanceRanking?.effectiveWeight],
      surface: [search.surfaceCompletionRanking?.mode, search.surfaceCompletionRanking?.effectiveWeight],
      frontMorphology: [search.mesoscopicFrontMorphologyRanking?.mode,
        search.mesoscopicFrontMorphologyRanking?.effectiveWeight],
      epitaxy: [search.epitaxialRegistryRanking?.mode, search.epitaxialRegistryRanking?.effectiveWeight],
      externalDrive: [search.externalDrivingGeometry?.mode, search.externalDrivingGeometry?.effectiveWeight],
      robustness: [search.constraintRobustnessRanking?.mode, search.constraintRobustnessRanking?.effectiveWeight],
      microstructure: [search.microstructureCouplingRanking?.mode, search.microstructureCouplingRanking?.effectiveWeight],
      loopClosure: [search.mesoscopicLoopClosureRanking?.mode, search.mesoscopicLoopClosureRanking?.effectiveWeight],
      arrivalPath: [search.geometricArrivalPathRanking?.mode, search.geometricArrivalPathRanking?.effectiveWeight],
      pathEnsemble: [search.configurationalPathEnsemble?.dimensionlessExplorationScale,
        search.configurationalPathEnsemble?.seed],
    } : null) },
    scheduling: { label: "tree scheduling", role: "search", value: serialized(search?.scheduling || null) },
    hierarchy: { label: "clusters² promotion", role: "search", value: String(search?.hierarchyEnabled ?? "not entered") },
    costModel: { label: "cost estimate assumptions", role: "analysis only", value: serialized(cost?.assumptions || null) },
  };
}

function experimentNotebookSummary(receipt) {
  const cover = receipt.cover?.inputAtoms ? receipt.cover : null;
  const search = receipt.search?.explicitSites === undefined ? null : receipt.search;
  const certificate = search?.liveCertificate || null;
  const classification = receipt.structuralEvidence?.emergentClassification;
  const activeMarking = receipt.marking?.active;
  const generatedSites = certificate?.metrics?.generatedStructuralSites
    ?? Math.max(0, (search?.explicitSites || 0) - receipt.input.atomCount);
  const causalDepth = certificate?.metrics?.maximumCausalDepth
    ?? certificate?.metrics?.nonemptyWaves ?? 0;
  const strongestClaim = receipt.evidenceBoundary.stationaryProductionCertified
    ? "stationary structural production certified"
    : certificate?.state || receipt.evidenceBoundary.benchmarkGate || "structural evidence only";
  return {
    id: receipt.receiptSha256.slice(0, 16),
    savedAt: receipt.generatedAt,
    receiptSha256: receipt.receiptSha256,
    experimentStateSha256: receipt.experimentStateSha256,
    material: receipt.input.materialName,
    scenarioId: receipt.input.scenarioId,
    inputStructureSha256: receipt.input.structureSha256,
    inputIdentity: `${receipt.input.scenarioId}:${receipt.input.structureSha256}`,
    elements: receipt.input.elements,
    inputAtoms: receipt.input.atomCount,
    stage: receipt.pipeline.stageName,
    stageOrdinal: receipt.pipeline.visibleStage,
    geometry: `${receipt.geometry.resolvedLabel} · ε ${receipt.geometry.metricIsometryToleranceAngstrom} Å`,
    rotationGroup: receipt.geometry.rotationGroup,
    structuralScalesEncoded: receipt.geometry.multiscalePassport.structuralScalesEncoded,
    cover: cover ? `${cover.isometryTypes} types · ${cover.placements} placements · ${cover.coveredAtoms}/${cover.inputAtoms} sites` : "not entered",
    coverComplete: cover?.status === "complete",
    marking: activeMarking ? activeMarking.name : receipt.marking.status,
    markingRepresentation: activeMarking?.representationReadout || receipt.marking.learned?.representationReadout || "not trained",
    hierarchy: search ? (search.hierarchyEnabled ? "clusters² enabled" : "primitive clusters") : "not entered",
    explicitSites: search?.explicitSites ?? 0,
    generatedSites,
    placedClusters: search?.placedClusters ?? 0,
    acceptedDecisions: search?.acceptedDecisions ?? 0,
    rejectedDecisions: search?.rejectedDecisions ?? 0,
    localConstraintEvaluations: search?.localConstraintWork?.evaluations ?? 0,
    projectedNeighborhoodSites: receipt.computationalWork?.liveBrowserWork?.projectedNeighborhoodSites ?? 0,
    causalDepth,
    classification: classification?.status || "withheld",
    classificationConfidence: classification?.current?.confidence ?? 0,
    strongestClaim,
    benchmarkGate: receipt.evidenceBoundary.benchmarkGate,
    physicalTimeModeled: receipt.evidenceBoundary.physicalElapsedTimeModeled,
    interventionFactors: notebookInterventionFactors(receipt),
    coordinatesEmbedded: false,
  };
}

function persistExperimentNotebook() {
  try {
    localStorage.setItem(EXPERIMENT_NOTEBOOK_STORAGE, JSON.stringify({
      schema: 1, entries: experimentNotebookEntries,
    }));
  } catch (_) {
    receiptStatus.textContent = "Notebook could not be persisted; receipt export remains available.";
  }
}

function restoreExperimentNotebook() {
  try {
    const stored = JSON.parse(localStorage.getItem(EXPERIMENT_NOTEBOOK_STORAGE) || "null");
    experimentNotebookEntries = Array.isArray(stored?.entries)
      ? stored.entries.filter((entry) => entry?.id && entry?.receiptSha256 && entry?.coordinatesEmbedded === false)
        .slice(-MAX_EXPERIMENT_NOTEBOOK_ENTRIES) : [];
  } catch (_) {
    experimentNotebookEntries = [];
  }
  selectedNotebookEntryIds = experimentNotebookEntries.slice(-2).map((entry) => entry.id);
}

function notebookComparisonValue(entry, key) {
  const values = {
    material: entry.material,
    input: `${entry.inputAtoms.toLocaleString()} atoms · ${entry.elements.join(" / ")}`,
    geometry: entry.geometry,
    cover: entry.cover,
    marking: `${entry.marking} · ${entry.markingRepresentation}`,
    search: `${entry.hierarchy} · ${entry.placedClusters} clusters · depth ${entry.causalDepth}`,
    output: `${entry.explicitSites.toLocaleString()} explicit · +${entry.generatedSites.toLocaleString()} structural sites`,
    decisions: `${entry.acceptedDecisions} accepted · ${entry.rejectedDecisions} rejected`,
    classification: `${entry.classification} · ${Math.round(entry.classificationConfidence * 100)}%`,
    claim: `${entry.strongestClaim} · ${entry.benchmarkGate}`,
  };
  return values[key];
}

function notebookInterventionComparison(first, second) {
  const firstFactors = first.interventionFactors || {};
  const secondFactors = second.interventionFactors || {};
  const factorKeys = [...new Set([...Object.keys(firstFactors), ...Object.keys(secondFactors)])].sort();
  const changedFactors = factorKeys.filter((key) => firstFactors[key]?.value !== secondFactors[key]?.value)
    .map((key) => ({ key, ...(secondFactors[key] || firstFactors[key]) }));
  const inputIdentityAvailable = Boolean(first.inputIdentity && second.inputIdentity);
  const sameInput = inputIdentityAvailable && first.inputIdentity === second.inputIdentity;
  let status = "descriptive";
  let title = "descriptive comparison only";
  let detail = "Input identity is unavailable in one legacy summary; save both states again for a controlled audit.";
  if (inputIdentityAvailable && !sameInput) {
    title = "different observed configurations";
    detail = "The input structure digests differ. Outcome deltas describe two materials or samples; they do not identify a causal effect.";
  } else if (sameInput && changedFactors.length === 1) {
    status = changedFactors[0].role === "analysis only" ? "analysis" : "controlled";
    title = changedFactors[0].role === "analysis only" ? "controlled analysis-only change" : "one-factor structural intervention";
    detail = `${changedFactors[0].label} is the only recorded factor that changed; the observed configuration digest is identical.`;
  } else if (sameInput && changedFactors.length === 0) {
    status = "replicate";
    title = "same recorded experiment state";
    detail = "No recorded intervention changed. Any outcome difference is replicate divergence or an unrecorded factor, not an attributed effect.";
  } else if (sameInput) {
    status = "confounded";
    title = `${changedFactors.length} factors changed together`;
    detail = "The input geometry is identical, but the outcome delta cannot be assigned to one intervention.";
  }
  const delta = (key) => Number(second[key] || 0) - Number(first[key] || 0);
  return {
    status, title, detail, sameInput, inputIdentityAvailable, changedFactors,
    firstInputDigest: first.inputStructureSha256 || null,
    secondInputDigest: second.inputStructureSha256 || null,
    causalAttributionAllowed: status === "controlled",
    outcomes: [
      { label: "structural sites", value: delta("generatedSites"), unit: "sites" },
      { label: "accepted branches", value: delta("acceptedDecisions"), unit: "branches" },
      { label: "rejected branches", value: delta("rejectedDecisions"), unit: "branches" },
      { label: "causal depth", value: delta("causalDepth"), unit: "levels" },
      { label: "classification", value: delta("classificationConfidence") * 100, unit: "points" },
      { label: "local tests", value: delta("localConstraintEvaluations"), unit: "tests" },
      { label: "neighbor inspections", value: delta("projectedNeighborhoodSites"), unit: "sites" },
    ],
  };
}

function signedNotebookDelta(value) {
  if (!Number.isFinite(value)) return "—";
  const rounded = Math.abs(value) < 10 && !Number.isInteger(value) ? Number(value.toFixed(2)) : Math.round(value);
  return `${rounded > 0 ? "+" : ""}${rounded.toLocaleString()}`;
}

function renderNotebookInterventionAudit(selected) {
  notebookInterventionAudit.replaceChildren();
  const header = document.createElement("header");
  const eyebrow = document.createElement("small"); eyebrow.textContent = "intervention audit";
  const title = document.createElement("strong");
  const detail = document.createElement("span");
  header.append(eyebrow, title, detail);
  notebookInterventionAudit.append(header);
  if (selected.length !== 2) {
    notebookInterventionAudit.className = "notebook-intervention-audit waiting";
    title.textContent = "select two runs";
    detail.textContent = "Input identity and changed assumptions are checked before any causal comparison.";
    return;
  }
  const audit = notebookInterventionComparison(selected[0], selected[1]);
  notebookInterventionAudit.className = `notebook-intervention-audit ${audit.status}`;
  title.textContent = audit.title;
  detail.textContent = audit.detail;
  const identity = document.createElement("div"); identity.className = "notebook-input-identity";
  identity.innerHTML = `<small>observed input</small><strong>${audit.sameInput ? "identical SHA-256" : "not identical"}</strong><span>${audit.firstInputDigest?.slice(0, 10) || "legacy"} → ${audit.secondInputDigest?.slice(0, 10) || "legacy"}</span>`;
  const factors = document.createElement("div"); factors.className = "notebook-factor-list";
  if (audit.changedFactors.length) audit.changedFactors.forEach((factor) => {
    const chip = document.createElement("span"); chip.textContent = `${factor.label} · ${factor.role}`; factors.appendChild(chip);
  });
  else {
    const chip = document.createElement("span"); chip.textContent = "no recorded factor change"; factors.appendChild(chip);
  }
  const outcomes = document.createElement("div"); outcomes.className = "notebook-outcome-deltas";
  audit.outcomes.forEach((outcome) => {
    const tile = document.createElement("span");
    tile.innerHTML = `<small>${outcome.label}</small><strong>${signedNotebookDelta(outcome.value)}</strong><em>${outcome.unit} · run 2 − run 1</em>`;
    outcomes.appendChild(tile);
  });
  const boundary = document.createElement("p");
  boundary.textContent = audit.causalAttributionAllowed
    ? "Causal interpretation is limited to this recorded one-factor intervention; hidden experimental confounders are not excluded."
    : "Outcome deltas remain visible, but the portal does not attribute them causally.";
  notebookInterventionAudit.append(identity, factors, outcomes, boundary);
}

function renderExperimentNotebook() {
  notebookState.textContent = `${experimentNotebookEntries.length}/${MAX_EXPERIMENT_NOTEBOOK_ENTRIES} saved runs`;
  clearNotebookButton.disabled = experimentNotebookEntries.length === 0;
  notebookEntries.replaceChildren(...experimentNotebookEntries.map((entry, index) => {
    const button = document.createElement("button"); button.type = "button";
    const selected = selectedNotebookEntryIds.includes(entry.id);
    button.classList.toggle("active", selected);
    button.setAttribute("aria-pressed", String(selected));
    button.title = `Receipt ${entry.receiptSha256}; coordinates excluded`;
    const number = document.createElement("small"); number.textContent = `run ${index + 1} · stage ${entry.stageOrdinal}`;
    const material = document.createElement("strong"); material.textContent = entry.material;
    const state = document.createElement("span"); state.textContent = `${entry.explicitSites.toLocaleString()} sites · ${entry.marking}`;
    const claim = document.createElement("em"); claim.textContent = entry.strongestClaim;
    button.append(number, material, state, claim);
    button.addEventListener("click", () => {
      if (selectedNotebookEntryIds.includes(entry.id)) selectedNotebookEntryIds = selectedNotebookEntryIds.filter((id) => id !== entry.id);
      else {
        if (selectedNotebookEntryIds.length >= 2) selectedNotebookEntryIds.shift();
        selectedNotebookEntryIds.push(entry.id);
      }
      renderExperimentNotebook();
    });
    return button;
  }));
  const selected = selectedNotebookEntryIds.map((id) => experimentNotebookEntries.find((entry) => entry.id === id)).filter(Boolean);
  notebookComparison.replaceChildren();
  renderNotebookInterventionAudit(selected);
  if (selected.length !== 2) {
    const note = document.createElement("p");
    note.textContent = selected.length ? "Select one more saved run to compare." : "Select two saved runs to compare.";
    notebookComparison.append(note); return;
  }
  const header = document.createElement("header");
  const empty = document.createElement("small"); empty.textContent = "field";
  const first = document.createElement("strong"); first.textContent = selected[0].material;
  const second = document.createElement("strong"); second.textContent = selected[1].material;
  header.append(empty, first, second); notebookComparison.append(header);
  [["material", "material"], ["input", "input"], ["geometry", "geometry"], ["cover", "cover"],
    ["marking", "marking"], ["search", "search"], ["output", "output"], ["decisions", "decisions"],
    ["classification", "classification"], ["claim boundary", "claim"]].forEach(([label, key]) => {
    const row = document.createElement("div");
    const name = document.createElement("small"); name.textContent = label;
    const firstValue = document.createElement("span"); firstValue.textContent = notebookComparisonValue(selected[0], key);
    const secondValue = document.createElement("span"); secondValue.textContent = notebookComparisonValue(selected[1], key);
    row.classList.toggle("same", firstValue.textContent === secondValue.textContent);
    row.append(name, firstValue, secondValue); notebookComparison.append(row);
  });
}

async function saveCurrentExperimentNotebookEntry() {
  if (experimentNotebookEntries.length >= MAX_EXPERIMENT_NOTEBOOK_ENTRIES) {
    receiptStatus.textContent = "Notebook is full. Download receipts or clear the notebook before saving another run."; return;
  }
  saveNotebookButton.disabled = true;
  receiptStatus.textContent = "Freezing coordinate-free run summary…";
  try {
    const receipt = await buildExperimentReceipt();
    const duplicate = experimentNotebookEntries.find((entry) => entry.experimentStateSha256 === receipt.experimentStateSha256);
    if (duplicate) {
      selectedNotebookEntryIds = [duplicate.id];
      receiptStatus.textContent = "This exact experiment state is already saved.";
    } else {
      const entry = experimentNotebookSummary(receipt);
      experimentNotebookEntries.push(entry);
      selectedNotebookEntryIds = [...selectedNotebookEntryIds.slice(-1), entry.id];
      persistExperimentNotebook();
      receiptStatus.textContent = `Run ${experimentNotebookEntries.length} saved · coordinate-free summary · receipt ${entry.receiptSha256.slice(0, 10)}…`;
    }
    renderExperimentNotebook();
  } catch (error) {
    receiptStatus.textContent = `Notebook save failed: ${error.message}`;
    console.error(error);
  } finally {
    saveNotebookButton.disabled = false;
  }
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
  referenceAtoms.forEach((atom) => atomOccupancyContributions(atom).forEach((entry) =>
    counts.set(entry.species, (counts.get(entry.species) || 0) + entry.fraction)));
  const values = [...counts.values()];
  const integral = values.every((value) => Math.abs(value - Math.round(value)) < 1e-8);
  const divisor = integral ? values.map(Math.round).reduce(integerGcd, 0) || 1 : Math.min(...values.filter((value) => value > 1e-10));
  return [...counts.entries()].sort(([first], [second]) => first.localeCompare(second))
    .map(([species, count]) => `${species}${receiptRound(count / divisor, 5)}`).join(":");
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
    metricToleranceMode: clusterToleranceMode,
    nominalMetricToleranceFraction: clusterMetricTolerance(),
    metricToleranceFraction: effectiveClusterMetricTolerance(),
    metricToleranceAngstrom: clusterMetricToleranceAngstrom(),
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
  // Molecular connection covers may expose many exact isometry classes while
  // retaining only a few human-facing family summaries.  Fit one coefficient
  // row for every executable occurrence type, not merely every summary card.
  const prototypeCount = Math.max(
    (learnedCover.types || clusterGalleryTypes()).length,
    ...samples.map((occurrence) => occurrence.type + 1),
  );
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

function periodicContextFromSceneCell(cell, pbc) {
  if (!cell || !pbc.some(Boolean)) return { matrix: null, inverse: null, pbc };
  const matrix = new THREE.Matrix3().set(
    cell[0].x, cell[1].x, cell[2].x,
    cell[0].y, cell[1].y, cell[2].y,
    cell[0].z, cell[1].z, cell[2].z,
  );
  return { matrix, inverse: matrix.clone().invert(), pbc };
}

function scenePeriodicContext() {
  const scale = referenceSpacing / referenceSpacingA;
  const cell = currentCell()?.map((vector) => vector.clone().multiplyScalar(scale));
  return periodicContextFromSceneCell(cell, currentPbc());
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

function importedFramePeriodicAxes(frame) {
  if (geometryMode === "module" || geometryMode === "offlattice") return [false, false, false];
  if (geometryMode === "lattice") return frame.cell ? [true, true, true] : [false, false, false];
  return frame.pbc || [false, false, false];
}

function referenceEvidenceFrames(source) {
  if (scenarioSelect.value !== "imported" || !importedStructure
    || ensembleEvidenceMode !== "all" || importedTrajectoryFrames().length <= 1) {
    return [{ source, context: scenePeriodicContext(), frameIndex: importedFrameIndex }];
  }
  const commonSceneScale = referenceSpacing / referenceSpacingA;
  const selected = currentImportedFrame();
  return importedTrajectoryFrames().map((frame, frameIndex) => {
    const frameSource = frame === selected ? source : makeImportedFrameReference(frame, commonSceneScale);
    const cell = frame.cell?.map((vector) => new THREE.Vector3(...vector).multiplyScalar(commonSceneScale)) || null;
    return {
      source: frameSource,
      context: periodicContextFromSceneCell(cell, importedFramePeriodicAxes(frame)),
      frameIndex,
    };
  });
}

function learnReferenceEnsemblePairUncertainty() {
  const frames = scenarioSelect.value === "imported" && ensembleEvidenceMode === "all"
    ? importedTrajectoryFrames() : [];
  if (frames.length < 2) return learnLocalPairDistanceUncertaintyEnsemble([], {
    localCutoff: descriptorCutoff() * referenceSpacingA,
  });
  const geometricFrames = frames.map((frame) => ({
    species: frame.atoms.map(occupancyChemistryToken),
    distance: (first, second) => Math.hypot(...structureDisplacement(
      frame.atoms[first].position,
      frame.atoms[second].position,
      frame.cell,
      importedFramePeriodicAxes(frame),
    )),
  }));
  return learnLocalPairDistanceUncertaintyEnsemble(geometricFrames, {
    referenceFrameIndex: importedFrameIndex,
    localCutoff: descriptorCutoff() * referenceSpacingA,
    upperQuantile: .9,
  });
}

function learnReferenceDistanceEnvelopes(source) {
  const frames = referenceEvidenceFrames(source).map(({ source: frameSource, context }) => ({
    species: frameSource.map((atom) => atom.species),
    distance: (first, second) => scenePeriodicDisplacement(frameSource[first].p, frameSource[second].p, context).length(),
  }));
  return learnColoredDistanceEnvelopesEnsemble(frames, {
      fallbackExclusion: COLLISION_TOLERANCE,
  });
}

function learnReferenceCoordinationEnvelopes(source) {
  const frames = referenceEvidenceFrames(source).map(({ source: frameSource, context }) => ({
    species: frameSource.map((atom) => atom.species),
    distance: (first, second) => scenePeriodicDisplacement(frameSource[first].p, frameSource[second].p, context).length(),
  }));
  return learnColoredCoordinationEnvelopesEnsemble(frames, coloredDistanceEnvelopes);
}

function learnReferenceAngularEnvelopes(source) {
  const frames = referenceEvidenceFrames(source).map(({ source: frameSource, context }) => ({
    species: frameSource.map((atom) => atom.species),
    displacement: (first, second) => scenePeriodicDisplacement(frameSource[first].p, frameSource[second].p, context),
  }));
  return learnColoredAngularEnvelopesEnsemble(frames, coloredCoordinationEnvelopes);
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
  return growthEnvironmentContains(confinementSelect.value, position);
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

function affineLoadModeLabel(mode = affineLoadMode) {
  return ({ none: "observed metric", "hydro-compress": "hydrostatic compression",
    "hydro-tension": "hydrostatic tension", "z-tension": "uniaxial Z tension",
    "xy-shear": "XY shear" })[mode] || "observed metric";
}

function affineLoadTensor() {
  const m = affineLoadMagnitude;
  if (affineLoadMode === "hydro-compress") return [[1 - m, 0, 0], [0, 1 - m, 0], [0, 0, 1 - m]];
  if (affineLoadMode === "hydro-tension") return [[1 + m, 0, 0], [0, 1 + m, 0], [0, 0, 1 + m]];
  if (affineLoadMode === "z-tension") return [[1, 0, 0], [0, 1, 0], [0, 0, 1 + m]];
  if (affineLoadMode === "xy-shear") return [[1, m, 0], [0, 1, 0], [0, 0, 1]];
  return [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
}

function applyAffineLoad(vector) {
  const tensor = affineLoadTensor();
  return new THREE.Vector3(
    tensor[0][0] * vector.x + tensor[0][1] * vector.y + tensor[0][2] * vector.z,
    tensor[1][0] * vector.x + tensor[1][1] * vector.y + tensor[1][2] * vector.z,
    tensor[2][0] * vector.x + tensor[2][1] * vector.y + tensor[2][2] * vector.z,
  );
}

function effectiveGeometricStrain(evaluation) {
  return affineLoadMode === "none" ? evaluation.geometricStrain : evaluation.affineLoadedGeometricStrain;
}

function activeCompositionBalanceWeight() {
  return compositionPreference === "strong" ? .70 : compositionPreference === "soft" ? .35 : 0;
}

function activeFormalChargeWeight() {
  if (!formalChargeTarget?.available || chargePreference === "none") return 0;
  return chargePreference === "strong" ? .50 : .25;
}

function activeSurfaceCompletionWeight() {
  return surfacePreference === "strong" ? .36 : surfacePreference === "soft" ? .18 : 0;
}

function activeFrontMorphologyWeight() {
  return frontMorphologyMode === "none" ? 0 : frontMorphologyWeight;
}

function frontMorphologyLabel(mode = frontMorphologyMode) {
  return ({ none: "neutral front", smooth: "concavity filling",
    facet: "facet propagation", tip: "tip selection" })[mode] || "neutral front";
}

function frontMorphologyForCandidate(candidate, { recordWork = true } = {}) {
  const parent = placedClusters.find((placement) => placement.id === candidate.parentId);
  const outward = candidate.position.clone().sub(parent?.position || new THREE.Vector3());
  if (outward.lengthSq() < 1e-12) outward.set(0, 0, 1);
  outward.normalize();
  let tangentX = new THREE.Vector3(1, 0, 0).applyQuaternion(parent?.rotation || new THREE.Quaternion());
  tangentX.addScaledVector(outward, -tangentX.dot(outward));
  if (tangentX.lengthSq() < 1e-8) {
    tangentX = new THREE.Vector3(0, 1, 0).applyQuaternion(parent?.rotation || new THREE.Quaternion());
    tangentX.addScaledVector(outward, -tangentX.dot(outward));
  }
  tangentX.normalize();
  const tangentY = outward.clone().cross(tangentX).normalize();
  const reach = 2.4 * referenceSpacing;
  const neighborhood = nearbyAtoms(candidate.position, reach)
    .map((atom) => ({ atom, offset: atom.p.clone().sub(candidate.position) }))
    .filter(({ offset }) => offset.lengthSq() > MERGE_TOLERANCE ** 2);
  const sectors = new Set();
  const backingDepths = [];
  neighborhood.forEach(({ offset }) => {
    const depth = -offset.dot(outward) / Math.max(referenceSpacing, 1e-12);
    if (depth > 0) backingDepths.push(depth);
    const x = offset.dot(tangentX); const y = offset.dot(tangentY);
    if (x * x + y * y <= .04 * referenceSpacing ** 2) return;
    const angle = (Math.atan2(y, x) + 2 * Math.PI) % (2 * Math.PI);
    sectors.add(Math.floor(angle / (2 * Math.PI) * 8) % 8);
  });
  const angularCoverage = sectors.size / 8;
  const backingFraction = backingDepths.length / Math.max(1, neighborhood.length);
  const meanDepth = backingDepths.reduce((sum, depth) => sum + depth, 0) / Math.max(1, backingDepths.length);
  const depthStd = Math.sqrt(backingDepths.reduce((sum, depth) => sum + (depth - meanDepth) ** 2, 0)
    / Math.max(1, backingDepths.length));
  const planeCoherence = Math.exp(-2 * depthStd);
  const smoothScore = 2 * angularCoverage - 1;
  const tipScore = 1 - 2 * angularCoverage;
  const facetScore = 2 * backingFraction * planeCoherence - 1;
  const score = frontMorphologyMode === "smooth" ? smoothScore
    : frontMorphologyMode === "tip" ? tipScore
      : frontMorphologyMode === "facet" ? facetScore : 0;
  if (recordWork) {
    frontMorphologyEvaluations++;
    frontMorphologyNeighborhoodChecks += neighborhood.length;
  }
  return {
    mode: frontMorphologyMode, label: frontMorphologyLabel(), score,
    angularSectors: sectors.size, angularSectorCount: 8, angularCoverage,
    occupiedSectors: [...sectors].sort((a, b) => a - b),
    backingAtoms: backingDepths.length, neighborhoodAtoms: neighborhood.length,
    backingFraction, meanBackingDepthNearestNeighborUnits: meanDepth,
    backingDepthStdNearestNeighborUnits: depthStd, planeCoherence,
    localFrame: "parent proper-SE(3) tangent frame + parent-to-candidate normal",
    normal: outward.toArray(), tangentX: tangentX.toArray(), tangentY: tangentY.toArray(),
    reachNearestNeighborUnits: 2.4,
    candidateGeometryChanged: false, hardAdmissionChanged: false,
    heldoutTargetUsed: false, meanCurvatureInferred: false,
    surfaceEnergyInferred: false, capillaryPressureInferred: false,
  };
}

function epitaxyTemplateSpec(mode = epitaxyTemplateMode) {
  return ({
    "square-coherent": { symmetry: "square", mismatch: 0, angleDegrees: 0 },
    "square-mismatch": { symmetry: "square", mismatch: .05, angleDegrees: 0 },
    "hex-coherent": { symmetry: "hexagonal", mismatch: 0, angleDegrees: 0 },
    "hex-mismatch": { symmetry: "hexagonal", mismatch: .05, angleDegrees: 0 },
    "hex-30": { symmetry: "hexagonal", mismatch: 0, angleDegrees: 30 },
  })[mode] || null;
}

function epitaxyTemplateLabel(mode = epitaxyTemplateMode) {
  const spec = epitaxyTemplateSpec(mode);
  if (!spec) return "inert support plane";
  const mismatch = spec.mismatch ? ` · +${Math.round(spec.mismatch * 100)}%` : " · coherent";
  const rotation = spec.angleDegrees ? ` · ${spec.angleDegrees}°` : "";
  return `${spec.symmetry} template${mismatch}${rotation}`;
}

function activeEpitaxyWeight() {
  return confinementSelect.value === "substrate" && epitaxyTemplateSpec() ? epitaxyWeight : 0;
}

function epitaxyLatticeCoordinate(position, spec = epitaxyTemplateSpec()) {
  if (!spec) return null;
  const spacing = referenceSpacing * (1 + spec.mismatch);
  const angle = -spec.angleDegrees * Math.PI / 180;
  const x = Math.cos(angle) * position.x - Math.sin(angle) * position.y;
  const y = Math.sin(angle) * position.x + Math.cos(angle) * position.y;
  let u; let v;
  if (spec.symmetry === "hexagonal") {
    v = 2 * y / (Math.sqrt(3) * spacing);
    u = x / spacing - .5 * v;
  } else {
    u = x / spacing;
    v = y / spacing;
  }
  const nearestU = Math.round(u); const nearestV = Math.round(v);
  const latticeX = spec.symmetry === "hexagonal"
    ? spacing * (nearestU + .5 * nearestV) : spacing * nearestU;
  const latticeY = spec.symmetry === "hexagonal"
    ? spacing * Math.sqrt(3) * .5 * nearestV : spacing * nearestV;
  const inverseAngle = -angle;
  const worldX = Math.cos(inverseAngle) * latticeX - Math.sin(inverseAngle) * latticeY;
  const worldY = Math.sin(inverseAngle) * latticeX + Math.cos(inverseAngle) * latticeY;
  return { u, v, nearestU, nearestV, nearestDistance: Math.hypot(position.x - worldX, position.y - worldY),
    nearestPoint: [worldX, worldY], spacing };
}

function epitaxyRegistryForFreshSites(fresh, { recordWork = true } = {}) {
  const template = epitaxyTemplateSpec();
  const enabled = activeEpitaxyWeight() > 0;
  const plane = growthEnvironmentSpec("substrate").parameters.lowerZ;
  const reach = 3.5 * referenceSpacing;
  const interfacial = enabled ? fresh.map((site) => {
    const height = site.p.z - plane;
    if (height < 0 || height > reach) return null;
    const coordinate = epitaxyLatticeCoordinate(site.p, template);
    const lateralScore = 2 * Math.exp(-8 * (coordinate.nearestDistance / coordinate.spacing) ** 2) - 1;
    const proximityWeight = Math.exp(-2 * height / reach);
    return { species: site.species, height, lateralScore, proximityWeight,
      nearestDistance: coordinate.nearestDistance, nearestPoint: coordinate.nearestPoint };
  }).filter(Boolean) : [];
  const weightTotal = interfacial.reduce((sum, site) => sum + site.proximityWeight, 0);
  const score = interfacial.reduce((sum, site) => sum + site.lateralScore * site.proximityWeight, 0)
    / Math.max(weightTotal, 1);
  if (recordWork && enabled) {
    epitaxyRegistryEvaluations++;
    epitaxyRegistrySiteChecks += fresh.length;
  }
  return {
    mode: epitaxyTemplateMode, label: epitaxyTemplateLabel(), enabled, score,
    templateSymmetry: template?.symmetry || null, mismatchFraction: template?.mismatch || 0,
    azimuthDegrees: template?.angleDegrees || 0, templateSpacingSceneUnits: template ? referenceSpacing * (1 + template.mismatch) : null,
    templateSpacingAngstrom: template ? referenceSpacingA * (1 + template.mismatch) : null,
    supportPlaneZSceneUnits: plane, interactionReachNearestNeighborUnits: 3.5,
    interfacialSites: interfacial.length, evaluatedFreshSites: enabled ? fresh.length : 0,
    meanNearestRegistryDistanceAngstrom: interfacial.length
      ? interfacial.reduce((sum, site) => sum + site.nearestDistance, 0) / interfacial.length * referenceSpacingA / referenceSpacing : null,
    siteRecords: interfacial.map((site) => ({ species: site.species,
      heightNearestNeighborUnits: site.height / referenceSpacing,
      registryScore: site.lateralScore,
      proximityWeight: site.proximityWeight })),
    templateDeclaredByUser: Boolean(template), substrateAtomsPresent: false, targetUsed: false,
    candidateSetChanged: false, candidateGeometryChanged: false, hardAdmissionChanged: false,
    adhesionEnergyInferred: false, interfaceEnergyInferred: false, epitaxialStrainRelaxationModeled: false,
  };
}

function activeExternalDriveWeight() {
  return externalDriveMode === "none" ? 0 : externalDriveWeight;
}

function activeRobustnessWeight() {
  return robustnessPreference === "margin" ? robustnessWeight : 0;
}

function activeMicrostructureCouplingWeight() {
  return microstructureCouplingMode === "none" ? 0 : microstructureCouplingWeight;
}

function microstructureCouplingLabel(mode = microstructureCouplingMode) {
  return ({ none: "neutral", "gap-heal": "gap healing", "interface-follow": "pose-interface following",
    "anomaly-avoid": "coordination-anomaly avoidance", "occupancy-follow": "occupational-front following" })[mode] || "neutral";
}

function microstructureRoleMatches(role, mode = microstructureCouplingMode) {
  if (mode === "gap-heal") return role.gapBoundary || role.literalTerminal;
  if (mode === "interface-follow") return role.poseInterface;
  if (mode === "anomaly-avoid") return role.coordinationAnomaly;
  if (mode === "occupancy-follow") return role.occupationalAlternative || role.explicitVacancy;
  return false;
}

function microstructureCouplingForCandidate(candidate, evaluation) {
  const neighborhood = growthEventNeighborhood(candidate, evaluation);
  const counts = neighborhood.counts;
  let rawSignal = 0;
  if (microstructureCouplingMode === "gap-heal") rawSignal = counts.gap + counts.residual;
  else if (microstructureCouplingMode === "interface-follow") rawSignal = counts.interface;
  else if (microstructureCouplingMode === "anomaly-avoid") rawSignal = -counts.anomaly;
  else if (microstructureCouplingMode === "occupancy-follow") rawSignal = counts.occupancy + counts.vacancy;
  return {
    mode: microstructureCouplingMode,
    label: microstructureCouplingLabel(),
    rawSignal,
    score: Math.sign(rawSignal) * Math.tanh(Math.abs(rawSignal) / 2),
    nearbyRoleCounts: { ...counts },
    reachAngstrom: neighborhood.reach * referenceSpacingA / Math.max(referenceSpacing, 1e-12),
    observedInputGeometryUsed: true,
    heldoutTargetUsed: false,
    defectLabelsUsed: false,
    candidateGeometryChanged: false,
    hardAdmissionChanged: false,
  };
}

function activeLoopClosureWeight() {
  return loopClosurePreference === "consensus" ? loopClosureWeight : 0;
}

function transformedRuleSites(rule, type, position, rotation) {
  return (rule.sites || overlapGrammar.templates[type].sites).map((site) => ({
    species: site.species,
    p: site.local.clone().applyQuaternion(rotation).add(position),
  }));
}

function coloredSiteSetResidual(first, second) {
  if (first.length !== second.length) return Infinity;
  const directed = (source, target) => source.reduce((maximum, site) => {
    const distances = target.filter((other) => other.species === site.species)
      .map((other) => site.p.distanceTo(other.p));
    return distances.length ? Math.max(maximum, Math.min(...distances)) : Infinity;
  }, 0);
  return Math.max(directed(first, second), directed(second, first));
}

function mesoscopicLoopClosureForCandidate(candidate) {
  const toleranceScene = clusterMetricToleranceAngstrom()
    * referenceSpacing / Math.max(referenceSpacingA, 1e-12);
  const positionWindow = Math.max(.36, 4 * toleranceScene);
  const coloredSiteWindow = Math.max(.18, 2 * toleranceScene);
  const candidateColoredSites = candidateSites(candidate);
  const paths = [];
  placedClusters.forEach((placement) => {
    const rules = hierarchyEnabled || placement.depth === 0
      ? overlapGrammar.byFrom.get(placement.type) || [] : [];
    rules.filter((rule) => rule.to === candidate.type).forEach((rule) => {
      const predictedRotation = placement.rotation.clone().multiply(rule.rotation).normalize();
      const predictedPosition = placement.position.clone()
        .add(rule.translation.clone().applyQuaternion(placement.rotation));
      const positionResidual = predictedPosition.distanceTo(candidate.position);
      if (positionResidual > positionWindow) return;
      const coloredSiteResidual = coloredSiteSetResidual(
        transformedRuleSites(rule, candidate.type, predictedPosition, predictedRotation), candidateColoredSites);
      paths.push({
        parentId: placement.id,
        ruleId: rule.id,
        positionResidual,
        coloredSiteResidual,
        compatible: coloredSiteResidual <= coloredSiteWindow,
      });
    });
  });
  const independent = paths.filter((path) => path.parentId !== candidate.parentId);
  const compatible = independent.filter((path) => path.compatible);
  const conflicting = independent.filter((path) => !path.compatible);
  const meanNormalizedResidual = compatible.length ? compatible.reduce((sum, path) => sum
    + path.coloredSiteResidual / Math.max(toleranceScene, 1e-9), 0) / compatible.length : 0;
  const supportCredit = Math.tanh(compatible.length / 2);
  const conflictPenalty = Math.tanh(conflicting.length / 2);
  const residualPenalty = compatible.length ? .35 * Math.tanh(meanNormalizedResidual / 2) : 0;
  return {
    score: Math.max(-1, Math.min(1, supportCredit - conflictPenalty - residualPenalty)),
    independentCompatiblePaths: compatible.length,
    independentConflictingPaths: conflicting.length,
    nearbyPredictedPaths: independent.length,
    meanNormalizedResidual,
    positionWindowSceneUnits: positionWindow,
    positionWindowAngstrom: positionWindow * referenceSpacingA / Math.max(referenceSpacing, 1e-12),
    coloredSiteWindowSceneUnits: coloredSiteWindow,
    coloredSiteWindowAngstrom: coloredSiteWindow * referenceSpacingA / Math.max(referenceSpacing, 1e-12),
    generatingParentExcludedFromConsensus: true,
    frozenConnectionRulesOnly: true,
    completeColoredSiteSetsCompared: true,
    rawQuaternionUsedForCompatibility: false,
    candidateGeometryChanged: false,
    hardAdmissionChanged: false,
    heldoutTargetUsed: false,
    modulusOrStressInferred: false,
  };
}

function activeArrivalPathWeight() {
  return arrivalPathMode === "none" ? 0 : arrivalPathWeight;
}

function deterministicPathUniform(candidateKey) {
  const serialized = `${growthPathSeed}|${eventIndex}|${candidateKey}`;
  let hash = 0x811c9dc5;
  for (let index = 0; index < serialized.length; index++) {
    hash ^= serialized.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return (hash + .5) / 0x100000000;
}

function geometricExplorationOffset(candidate) {
  if (geometricExplorationScale <= 0) return 0;
  const uniform = Math.max(1e-12, Math.min(1 - 1e-12, deterministicPathUniform(candidate.key)));
  return geometricExplorationScale * -Math.log(-Math.log(uniform));
}

function arrivalPathLabel(mode = arrivalPathMode) {
  return ({ none: "final pose only", "parent-outward": "parent-normal arrival",
    "radial-outward": "seed-radial arrival", "declared-drive": "declared-drive arrival" })[mode]
    || "final pose only";
}

function arrivalPathAxis(candidate) {
  const parent = placedClusters.find((placement) => placement.id === candidate.parentId);
  const seedOrigin = placedClusters[0]?.position || new THREE.Vector3();
  if (arrivalPathMode === "parent-outward") {
    return candidate.position.clone().sub(parent?.position || seedOrigin).normalize();
  }
  if (arrivalPathMode === "radial-outward") {
    return candidate.position.clone().sub(seedOrigin).normalize();
  }
  if (arrivalPathMode === "declared-drive") {
    const external = externalDriveForCandidate(candidate);
    return external.axis ? new THREE.Vector3(...external.axis).normalize() : new THREE.Vector3();
  }
  return new THREE.Vector3();
}

function geometricArrivalPathForCandidate(candidate, fresh) {
  const sampleCount = arrivalPathMode === "none" ? 0 : 9;
  const axis = arrivalPathAxis(candidate);
  const available = sampleCount > 0 && axis.lengthSq() > 1e-12;
  const sweepDistance = 2 * referenceSpacing;
  const toleranceScene = clusterMetricToleranceAngstrom()
    * referenceSpacing / Math.max(referenceSpacingA, 1e-12);
  let minimumClearance = Infinity;
  let blockedSiteSamples = 0;
  let neighborhoodChecks = 0;
  const blockedSites = new Set();
  if (available) fresh.forEach((site, siteIndex) => {
    for (let sample = 0; sample < sampleCount; sample++) {
      const fraction = sample / Math.max(1, sampleCount - 1);
      const point = site.p.clone().addScaledVector(axis, sweepDistance * (1 - fraction));
      const neighborhood = nearbyAtoms(point,
        coloredDistanceEnvelopes?.maximumExclusion || COLLISION_TOLERANCE);
      neighborhoodChecks += neighborhood.length;
      let sampleBlocked = false;
      neighborhood.forEach((atom) => {
        const clearance = point.distanceTo(atom.p) - coloredPairExclusion(site.species, atom.species);
        minimumClearance = Math.min(minimumClearance, clearance);
        if (clearance < 0) sampleBlocked = true;
      });
      if (sampleBlocked) { blockedSiteSamples++; blockedSites.add(siteIndex); }
    }
  });
  if (!Number.isFinite(minimumClearance)) minimumClearance = toleranceScene;
  return {
    mode: arrivalPathMode,
    label: arrivalPathLabel(),
    available,
    axis: available ? axis.toArray() : null,
    sampleCount,
    sweepDistanceSceneUnits: sweepDistance,
    sweepDistanceAngstrom: sweepDistance * referenceSpacingA / Math.max(referenceSpacing, 1e-12),
    siteSamples: fresh.length * sampleCount,
    neighborhoodChecks,
    blockedSiteSamples,
    blockedSites: blockedSites.size,
    minimumClearanceSceneUnits: minimumClearance,
    minimumClearanceAngstrom: minimumClearance * referenceSpacingA / Math.max(referenceSpacing, 1e-12),
    pathAccessible: available && blockedSiteSamples === 0,
    score: available ? Math.tanh(minimumClearance / Math.max(toleranceScene, 1e-9)) : 0,
    emittedSitesOnly: true,
    intermediateBoundaryEnforced: false,
    candidateGeometryChanged: false,
    hardAdmissionChanged: false,
    heldoutTargetUsed: false,
    knownWindowReplayGeometryUsed: !reconstructionCertified,
    barrierOrRateInferred: false,
    physicalTimeIntegrated: false,
  };
}

function externalDriveModeLabel(mode = externalDriveMode) {
  return ({ none: "isotropic", "z-plus": "axis +Z", "z-minus": "axis −Z",
    "radial-out": "radial outward", "radial-in": "radial inward" })[mode] || "isotropic";
}

function externalDriveForCandidate(candidate) {
  const parent = placedClusters.find((placement) => placement.id === candidate.parentId);
  const displacement = candidate.position.clone().sub(parent?.position || candidate.position);
  const seedOrigin = placedClusters[0]?.position || new THREE.Vector3();
  let axis = new THREE.Vector3();
  if (externalDriveMode === "z-plus") axis.set(0, 0, 1);
  else if (externalDriveMode === "z-minus") axis.set(0, 0, -1);
  else if (externalDriveMode === "radial-out" || externalDriveMode === "radial-in") {
    axis.copy((parent?.position || candidate.position).clone().sub(seedOrigin));
    if (axis.lengthSq() < 1e-12) axis.copy(candidate.position).sub(seedOrigin);
    if (axis.lengthSq() > 1e-12) axis.normalize();
    if (externalDriveMode === "radial-in") axis.multiplyScalar(-1);
  }
  const alignment = axis.lengthSq() > 0 && displacement.lengthSq() > 0
    ? displacement.clone().normalize().dot(axis) : 0;
  return {
    mode: externalDriveMode,
    label: externalDriveModeLabel(),
    alignment,
    signedStepSceneUnits: displacement.dot(axis),
    axis: axis.lengthSq() > 0 ? axis.toArray() : null,
    globalAxis: externalDriveMode === "z-plus" || externalDriveMode === "z-minus"
      ? axis.toArray() : null,
    seedRelative: externalDriveMode === "radial-out" || externalDriveMode === "radial-in",
    targetUsed: false,
    candidateGeometryChanged: false,
  };
}

function constraintRobustnessForCandidate(fresh, merged) {
  const scaleAngstrom = referenceSpacingA / Math.max(referenceSpacing, 1e-12);
  const toleranceScene = clusterMetricToleranceAngstrom() / Math.max(scaleAngstrom, 1e-12);
  const contactMargins = [];
  fresh.forEach((site) => nearbyAtoms(site.p,
    coloredDistanceEnvelopes?.maximumExclusion || COLLISION_TOLERANCE).forEach((atom) => {
    contactMargins.push(site.p.distanceTo(atom.p) - coloredPairExclusion(site.species, atom.species));
  }));
  const overlapMargins = merged.map(({ site, atom }) => MERGE_TOLERANCE - site.p.distanceTo(atom.p));
  const boundaryMargins = fresh.map((site) => growthEnvironmentSignedMargin(confinementSelect.value, site.p));
  const minimum = (values) => values.length ? Math.min(...values) : null;
  const componentsScene = {
    contactClearance: minimum(contactMargins),
    overlapHeadroom: minimum(overlapMargins),
    boundaryClearance: minimum(boundaryMargins),
  };
  const finite = Object.values(componentsScene).filter(Number.isFinite);
  const minimumMarginScene = finite.length ? Math.min(...finite) : 0;
  const normalizedMinimum = minimumMarginScene / Math.max(toleranceScene, 1e-9);
  return {
    score: Math.tanh(normalizedMinimum / 2),
    normalizedMinimum,
    minimumMarginScene,
    minimumMarginAngstrom: minimumMarginScene * scaleAngstrom,
    componentsScene,
    componentsAngstrom: Object.fromEntries(Object.entries(componentsScene)
      .map(([key, value]) => [key, Number.isFinite(value) ? value * scaleAngstrom : null])),
    toleranceAngstrom: clusterMetricToleranceAngstrom(),
    targetUsed: false,
    candidateGeometryChanged: false,
    hardAdmissionChanged: false,
    perturbationEnsembleUsedForRanking: false,
  };
}

function frozenFrontierDigest(entries) {
  const serialized = entries.map((entry) => entry.candidate.key).sort().join("|");
  let hash = 0x811c9dc5;
  for (let index = 0; index < serialized.length; index++) {
    hash ^= serialized.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash.toString(16).padStart(8, "0");
}

function capturePolicyComparison(entries) {
  const admissible = entries.filter((entry) => entry.evaluation.accepted);
  const policies = [
    { id: "grammar", label: "mark + recurrence", score: (entry) => entry.baseScore },
    { id: "elastic", label: "elastic 0.16", score: (entry) => entry.baseScore - .16 * entry.evaluation.geometricStrain.total },
    { id: "affine-load", label: `${affineLoadModeLabel()} metric`,
      score: (entry) => entry.baseScore - .16 * effectiveGeometricStrain(entry.evaluation).total },
    { id: "composition", label: "composition 0.35", score: (entry) => entry.baseScore - .35 * entry.evaluation.compositionBalance.scaledDelta },
    { id: "charge", label: "formal charge 0.25", score: (entry) => entry.baseScore - .25 * entry.evaluation.formalChargeBalance.scaledDelta },
    { id: "surface", label: "surface 0.18", score: (entry) => entry.baseScore - .18 * entry.evaluation.surfaceCompletion.scaledDelta },
    { id: "front-morphology", label: `${frontMorphologyLabel()} ${activeFrontMorphologyWeight().toFixed(2)}`,
      score: (entry) => entry.baseScore + activeFrontMorphologyWeight() * entry.evaluation.frontMorphology.score },
    { id: "epitaxy", label: `${epitaxyTemplateLabel()} ${activeEpitaxyWeight().toFixed(2)}`,
      score: (entry) => entry.baseScore + activeEpitaxyWeight() * entry.evaluation.epitaxyRegistry.score },
    { id: "drive", label: `${externalDriveModeLabel()} ${activeExternalDriveWeight().toFixed(2)}`,
      score: (entry) => entry.baseScore + activeExternalDriveWeight() * entry.evaluation.externalDrive.alignment },
    { id: "robustness", label: `constraint margin ${activeRobustnessWeight().toFixed(2)}`,
      score: (entry) => entry.baseScore + activeRobustnessWeight() * entry.evaluation.constraintRobustness.score },
    { id: "microstructure", label: `${microstructureCouplingLabel()} ${activeMicrostructureCouplingWeight().toFixed(2)}`,
      score: (entry) => entry.baseScore + activeMicrostructureCouplingWeight() * entry.evaluation.microstructureCoupling.score },
    { id: "loop-closure", label: `loop closure ${activeLoopClosureWeight().toFixed(2)}`,
      score: (entry) => entry.baseScore + activeLoopClosureWeight() * entry.evaluation.loopClosure.score },
    { id: "arrival-path", label: `${arrivalPathLabel()} ${activeArrivalPathWeight().toFixed(2)}`,
      score: (entry) => entry.baseScore + activeArrivalPathWeight() * entry.evaluation.arrivalPath.score },
    { id: "combined", label: "combined greedy", score: (entry) => entry.score },
    { id: "active", label: geometricExplorationScale > 0
      ? `sampled T* ${geometricExplorationScale.toFixed(2)}` : "active greedy",
      score: (entry) => entry.selectionScore },
  ].map((policy) => {
    const ranked = admissible.map((entry) => ({ entry, score: policy.score(entry) }))
      .sort((first, second) => second.score - first.score || first.entry.candidate.key.localeCompare(second.entry.candidate.key));
    const winner = ranked[0];
    return {
      id: policy.id,
      label: policy.label,
      action: winner ? `C${winner.entry.candidate.rule.from + 1}→C${winner.entry.candidate.rule.to + 1} · R${winner.entry.candidate.rule.id}` : "no admitted action",
      candidateKey: winner?.entry.candidate.key || null,
      candidateDigest: winner ? frozenFrontierDigest([winner.entry]) : null,
      score: winner?.score ?? null,
      preview: winner ? { p: winner.entry.candidate.position.clone(),
        rotation: winner.entry.candidate.rotation.clone(), type: winner.entry.candidate.type } : null,
    };
  });
  lastPolicyComparison = {
    index: ++policySnapshotCount,
    frontier: entries.length,
    admissible: admissible.length,
    candidateDigest: frozenFrontierDigest(entries),
    candidateSetTargetUsed: false,
    rankingTargetUsed: !reconstructionCertified,
    referenceGuided: !reconstructionCertified,
    uniqueTopActions: new Set(policies.map((policy) => policy.candidateKey).filter(Boolean)).size,
    policies,
  };
  policyComparisonHistory.push(lastPolicyComparison);
  if (policyComparisonHistory.length > 48) policyComparisonHistory.shift();
  selectedPolicySnapshotIndex = policyComparisonHistory.length - 1;
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

function constraintProjectionForFreshSites(rawFreshSites, { recordWork = true } = {}) {
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
  if (recordWork) {
    constraintNeighborhoodEvaluations++;
    constraintNeighborhoodSiteTotal += projected.length;
    maximumConstraintNeighborhoodSites = Math.max(maximumConstraintNeighborhoodSites, projected.length);
  }
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

function affineLoadedGeometricStrainForFreshSites(rawFreshSites,
  projection = constraintProjectionForFreshSites(rawFreshSites)) {
  if (affineLoadMode === "none") return geometricStrainForFreshSites(rawFreshSites, projection);
  const { projected, affectedIndices } = projection;
  if (!affectedIndices.length || !coloredAngularEnvelopes) return {
    total: 0, distance: 0, angle: 0, contactTerms: 0, angleTerms: 0,
  };
  return coloredGeometricStrain(projected.map((site) => site.species),
    (first, second) => applyAffineLoad(projected[second].p.clone().sub(projected[first].p)),
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

function formalChargeBalanceForFreshSites(rawFreshSites) {
  const freshSites = uniqueFreshSites(rawFreshSites);
  if (!formalChargeTarget || !freshSites.length) return {
    available: false, reason: "candidate adds no sites", before: 0, after: 0, delta: 0, scaledDelta: 0,
    currentNetFormalCharge: null, freshNetFormalCharge: null, projectedNetFormalCharge: null,
    projectedMeanFormalCharge: null, referenceMeanFormalCharge: formalChargeTarget?.meanFormalCharge ?? null, added: 0,
  };
  return formalChargeBalanceDelta(atoms.map((atom) => atom.species),
    freshSites.map((site) => site.species), formalChargeTarget, formalChargeFromChemistryToken);
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
    const score = baseScore
        - activeGeometricStrainWeight() * effectiveGeometricStrain(evaluation).total
        - activeCompositionBalanceWeight() * evaluation.compositionBalance.scaledDelta
        - activeFormalChargeWeight() * evaluation.formalChargeBalance.scaledDelta
        - activeSurfaceCompletionWeight() * evaluation.surfaceCompletion.scaledDelta
        + activeFrontMorphologyWeight() * evaluation.frontMorphology.score
        + activeEpitaxyWeight() * evaluation.epitaxyRegistry.score
        + activeExternalDriveWeight() * evaluation.externalDrive.alignment
        + activeRobustnessWeight() * evaluation.constraintRobustness.score
        + activeMicrostructureCouplingWeight() * evaluation.microstructureCoupling.score
        + activeLoopClosureWeight() * evaluation.loopClosure.score
        + activeArrivalPathWeight() * evaluation.arrivalPath.score;
    const explorationOffset = geometricExplorationOffset(candidate);
    candidate.explorationOffset = explorationOffset;
    return { candidate, evaluation, sites: evaluation.sites, baseScore, score,
      explorationOffset, selectionScore: score + explorationOffset };
  });
  capturePolicyComparison(evaluated);
  const ranked = evaluated.sort((first, second) => second.selectionScore - first.selectionScore
    || first.candidate.key.localeCompare(second.candidate.key));
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

function evaluateCandidate(candidate, {
  refinePose = true,
  recordWork = true,
  targetAware = true,
  enforceMarking = true,
} = {}) {
  if (refinePose) refineCandidateTranslation(candidate);
  const rawSites = candidateSites(candidate);
  const reconstructing = targetAware && !reconstructionCertified && replayIndex < referenceCount();
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
  const markingAccepted = !enforceMarking || policySelect.value !== "marked" || candidate.markingAccepted;
  const knownFailures = reconstructing ? canonical.failures : 0;
  const markingFallback = reconstructing && knownFailures === 0 && !markingAccepted;
  const constraintProjection = constraintProjectionForFreshSites(fresh, { recordWork });
  const coordinationOverflows = reconstructing ? [] : coordinationOverflowsForFreshSites(fresh, constraintProjection);
  const angularViolations = reconstructing ? [] : angularViolationsForFreshSites(fresh, constraintProjection);
  const geometricStrain = geometricStrainForFreshSites(fresh, constraintProjection);
  const affineLoadedGeometricStrain = affineLoadedGeometricStrainForFreshSites(fresh, constraintProjection);
  const surfaceCompletion = surfaceCompletionForFreshSites(fresh, constraintProjection);
  const frontMorphology = frontMorphologyForCandidate(candidate, { recordWork });
  const epitaxyRegistry = epitaxyRegistryForFreshSites(fresh, { recordWork });
  const compositionBalance = compositionBalanceForFreshSites(fresh);
  const formalChargeBalance = formalChargeBalanceForFreshSites(fresh);
  const externalDrive = externalDriveForCandidate(candidate);
  const constraintRobustness = constraintRobustnessForCandidate(fresh, merged);
  const microstructureCoupling = microstructureCouplingForCandidate(candidate, { fresh, merged });
  const loopClosure = mesoscopicLoopClosureForCandidate(candidate);
  const arrivalPath = geometricArrivalPathForCandidate(candidate, fresh);
  const accepted = conflicts === 0 && boundaryFailures === 0 && merged.length >= 2
    && fresh.length > 0 && knownFailures === 0 && coordinationOverflows.length === 0
    && angularViolations.length === 0 && (markingAccepted || markingFallback);
  return { accepted, sites, merged, fresh, conflicts, boundaryFailures, knownFailures, markingFallback,
    coordinationOverflows, angularViolations, geometricStrain, affineLoadedGeometricStrain,
    surfaceCompletion, frontMorphology, epitaxyRegistry, compositionBalance, formalChargeBalance,
    externalDrive, constraintRobustness, microstructureCoupling, loopClosure, arrivalPath,
    duplicateSites: canonical.duplicateSites,
    freshReferenceIndices: fresh.map((site) => site.referenceIndex).filter(Number.isInteger),
    reason: conflicts ? `${conflicts} hard-core/species conflicts` : boundaryFailures ? "outside confinement" : knownFailures ? `${knownFailures} sites outside known configuration` : coordinationOverflows.length ? `${coordinationOverflows.length} colored coordination capacities exceeded` : angularViolations.length ? `${angularViolations.length} colored angular envelopes violated` : merged.length < 2 ? "insufficient shared support" : fresh.length === 0 ? "duplicate covering" : !markingAccepted ? "marking mismatch" : "compatible overlap" };
}

function referenceCoverageCount() {
  return referenceCoverageAudit().matched;
}

function iceAnchorScenePoint(point) {
  const scale = .92 / currentMaterial().spacingA;
  return new THREE.Vector3(...point).sub(new THREE.Vector3(...iceAnchorTrace.boundaryCenter)).multiplyScalar(scale);
}

function initializeIceAnchorSearch() {
  iceAnchorTrace = scenarioSelect.value === "iceVI"
    ? executeFrozenIceViAnchorTrace(ICE_VI_ANCHOR_TRACE_ARTIFACT)
    : executeIceMolecularAnchorGrowth(ICE_MOLECULAR_PORT_ARTIFACT, scenarioSelect.value);
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

function growthSeedSites(occurrenceIndex) {
  const occurrence = overlapGrammar.occurrences[occurrenceIndex];
  if (overlapGrammar.coverBased || overlapGrammar.molecular) return occurrence.sites;
  const inverseFrame = occurrence.rotation.clone().invert();
  const sites = [{ local: new THREE.Vector3(), species: referenceAtoms[occurrenceIndex].species, center: true }];
  learnedClusters.environments[occurrenceIndex].shell
    .filter((neighbor) => neighbor.r <= motifShellCutoff())
    .forEach((neighbor) => sites.push({
      local: neighbor.vector.clone().multiplyScalar(referenceSpacing / referenceSpacingA).applyQuaternion(inverseFrame),
      species: neighbor.atom.species, center: false,
    }));
  return sites;
}

function growthSeedType(occurrenceIndex) {
  const occurrence = overlapGrammar.occurrences[occurrenceIndex];
  return overlapGrammar.coverBased || overlapGrammar.molecular
    ? occurrence.type : learnedClusters.labels[occurrenceIndex];
}

function observedGrowthSeedIndices() {
  const requested = Math.max(1, requestedGrowthNuclei);
  const replaySeed = overlapGrammar.replaySeedIndex;
  const eligible = overlapGrammar.occurrences.map((occurrence, index) => ({ occurrence, index }))
    .filter(({ occurrence, index }) => occurrence?.position && growthSeedSites(index).length >= 2)
    .sort((a, b) => a.index - b.index);
  const referenceSupports = new Map(eligible.map(({ occurrence, index }) => [index, new Set(canonicalKnownSites(
    growthSeedSites(index).map((site) => ({ ...site,
      p: site.local.clone().applyQuaternion(occurrence.rotation).add(occurrence.position) }))).sites
    .map((site) => site.referenceIndex))]));
  let first = replaySeed;
  let pool = eligible;
  if (requested > 1) {
    const byType = new Map();
    eligible.forEach((entry) => {
      const type = growthSeedType(entry.index);
      const group = byType.get(type) || [];
      group.push(entry); byType.set(type, group);
    });
    const recurring = [...byType.entries()].filter(([, group]) => group.length >= requested)
      .sort((a, b) => b[1].length - a[1].length || a[0] - b[0])[0];
    if (recurring) {
      pool = recurring[1];
      first = pool.slice().sort((a, b) =>
        a.occurrence.position.distanceToSquared(overlapGrammar.occurrences[replaySeed].position)
        - b.occurrence.position.distanceToSquared(overlapGrammar.occurrences[replaySeed].position)
        || a.index - b.index)[0].index;
    }
  }
  const selected = [first];
  while (selected.length < requested) {
    const occupied = new Set(selected.flatMap((index) => [...(referenceSupports.get(index) || [])]));
    const next = pool.filter(({ index }) => !selected.includes(index)
        && [...(referenceSupports.get(index) || [])].every((referenceIndex) => !occupied.has(referenceIndex)))
      .map(({ occurrence, index }) => ({ index, minimumSeparation: Math.min(...selected.map((chosen) =>
        occurrence.position.distanceTo(overlapGrammar.occurrences[chosen].position))) }))
      .sort((a, b) => b.minimumSeparation - a.minimumSeparation || a.index - b.index)[0];
    if (!next || next.minimumSeparation < referenceSpacing * 1.5) break;
    selected.push(next.index);
  }
  return selected;
}

function growthNucleusOccurrence(placement) {
  const sites = growthSeedSites(placement.occurrenceIndex);
  return {
    species: sites.map((site) => site.species),
    positions: sites.map((site) => site.local.clone().applyQuaternion(placement.rotation)
      .add(placement.position).toArray()),
  };
}

function growthNucleusPairs() {
  const nuclei = placedClusters.filter((placement) => placement.seedNucleus)
    .sort((a, b) => a.nucleusId - b.nucleusId);
  const pairs = [];
  for (let first = 0; first < nuclei.length; first++) for (let second = first + 1; second < nuclei.length; second++) {
    const a = nuclei[first]; const b = nuclei[second];
    const misorientation = symmetryReducedMisorientation(growthNucleusOccurrence(a), growthNucleusOccurrence(b), {
      metricToleranceFraction: effectiveClusterMetricTolerance(),
    });
    const atomsA = atoms.filter((atom) => atom.nucleusIds?.includes(a.nucleusId));
    const atomsB = atoms.filter((atom) => atom.nucleusIds?.includes(b.nucleusId));
    const shared = atoms.filter((atom) => atom.nucleusIds?.includes(a.nucleusId)
      && atom.nucleusIds.includes(b.nucleusId));
    pairs.push({ key: `${a.nucleusId}:${b.nucleusId}`, first: a, second: b, misorientation,
      centerSeparationAngstrom: a.position.distanceTo(b.position) * referenceSpacingA / referenceSpacing,
      sharedSites: shared.length, firstSites: atomsA.length, secondSites: atomsB.length,
      sharedSiteFraction: shared.length / Math.max(1, Math.min(atomsA.length, atomsB.length)),
      sameClusterType: a.type === b.type, targetUsed: false });
  }
  return pairs;
}

function renderNucleusInterfaceInspector() {
  const pairs = pipelineStage === 4 ? growthNucleusPairs() : [];
  nucleusInterfaceInspector.hidden = pairs.length === 0;
  if (!pairs.length) return;
  if (!pairs.some((pair) => pair.key === selectedNucleusPairKey)) selectedNucleusPairKey = pairs[0].key;
  const selected = pairs.find((pair) => pair.key === selectedNucleusPairKey) || pairs[0];
  nucleusInterfaceState.textContent = selected.sharedSites
    ? `${selected.sharedSites} registered sites` : "domains separated";
  nucleusPairButtons.replaceChildren();
  pairs.forEach((pair) => {
    const button = document.createElement("button"); button.type = "button";
    button.classList.toggle("active", pair.key === selected.key);
    button.setAttribute("aria-pressed", String(pair.key === selected.key));
    button.textContent = `N${pair.first.nucleusId} ↔ N${pair.second.nucleusId}`;
    button.addEventListener("click", () => {
      selectedNucleusPairKey = pair.key;
      renderNucleusInterfaceInspector();
      rebuildWorld();
    });
    nucleusPairButtons.append(button);
  });
  nucleusPairDetail.replaceChildren();
  const angle = selected.misorientation.comparable
    ? `${selected.misorientation.angleDegrees.toFixed(2)}°` : "not comparable";
  [
    ["proper misorientation", angle, selected.misorientation.comparable
      ? `${selected.misorientation.properGaugePairs} symmetry-gauge pairs minimized` : selected.misorientation.reason],
    ["seed separation", `${selected.centerSeparationAngstrom.toFixed(2)} Å`, "observed occurrence centers"],
    ["shared-site registry", `${selected.sharedSites} sites · ${(selected.sharedSiteFraction * 100).toFixed(1)}%`, `${selected.firstSites} / ${selected.secondSites} lineage sites`],
    ["claim boundary", "geometric interface", "no grain label or interfacial energy"],
  ].forEach(([label, value, detail]) => {
    const row = document.createElement("div"); const small = document.createElement("small");
    const strong = document.createElement("strong"); const span = document.createElement("span");
    small.textContent = label; strong.textContent = value; span.textContent = detail;
    row.append(small, strong, span); nucleusPairDetail.append(row);
  });
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
  acceptedUnloadedGeometricStrain = 0;
  rejectedUnloadedGeometricStrain = 0;
  acceptedCompositionDelta = 0;
  rejectedCompositionDelta = 0;
  acceptedFormalChargeDelta = 0;
  rejectedFormalChargeDelta = 0;
  acceptedSurfaceDeficit = 0;
  rejectedSurfaceDeficit = 0;
  acceptedExternalDriveAlignment = 0;
  rejectedExternalDriveAlignment = 0;
  acceptedRobustnessScore = 0;
  rejectedRobustnessScore = 0;
  acceptedMicrostructureCouplingScore = 0;
  rejectedMicrostructureCouplingScore = 0;
  acceptedLoopClosureScore = 0;
  rejectedLoopClosureScore = 0;
  acceptedIndependentLoopWitnesses = 0;
  rejectedIndependentLoopWitnesses = 0;
  acceptedArrivalPathScore = 0;
  rejectedArrivalPathScore = 0;
  acceptedBlockedPathSamples = 0;
  rejectedBlockedPathSamples = 0;
  arrivalPathSiteSamples = 0;
  arrivalPathNeighborhoodChecks = 0;
  acceptedExplorationOffset = 0;
  rejectedExplorationOffset = 0;
  acceptedFrontMorphologyScore = 0;
  rejectedFrontMorphologyScore = 0;
  frontMorphologyEvaluations = 0;
  frontMorphologyNeighborhoodChecks = 0;
  acceptedEpitaxyRegistryScore = 0;
  rejectedEpitaxyRegistryScore = 0;
  epitaxyRegistryEvaluations = 0;
  epitaxyRegistrySiteChecks = 0;
  initializedGrowthNuclei = 0;
  coalescenceEvents = 0;
  crossNucleusMergeContacts = 0;
  selectedNucleusPairKey = null;
  constraintNeighborhoodEvaluations = 0;
  constraintNeighborhoodSiteTotal = 0;
  maximumConstraintNeighborhoodSites = 0;
  lastPolicyComparison = null;
  policyComparisonHistory = [];
  selectedPolicySnapshotIndex = -1;
  selectedPolicyPreviewId = "active";
  policySnapshotCount = 0;
  atomSpatialIndex = new Map();
  const seedIndices = observedGrowthSeedIndices();
  seedIndices.forEach((seedIndex, nucleusIndex) => {
    const seedOccurrence = overlapGrammar.occurrences[seedIndex];
    const seedType = growthSeedType(seedIndex);
    const seed = { id: placedClusters.length + 1, nucleusId: nucleusIndex + 1, seedNucleus: true,
      type: seedType, position: seedOccurrence.position.clone(), rotation: seedOccurrence.rotation.clone(),
      occurrenceIndex: seedIndex, parentId: null, ruleId: null, depth: 0, atomIds: [] };
    const canonicalSeed = canonicalKnownSites(growthSeedSites(seedIndex).map((site) => ({
      ...site, p: site.local.clone().applyQuaternion(seed.rotation).add(seed.position),
    })));
    canonicalSeed.sites.forEach((site) => {
      const existing = nearbyAtoms(site.p, MERGE_TOLERANCE)
        .find((atom) => atom.species === site.species && atom.p.distanceTo(site.p) <= MERGE_TOLERANCE);
      const atom = existing || addAtom(site.p, site.species, `C${seedType + 1}`, null, true);
      atom.referenceIndex = site.referenceIndex;
      atom.clusterIds ||= [];
      if (!atom.clusterIds.includes(seed.id)) atom.clusterIds.push(seed.id);
      atom.nucleusIds ||= [];
      if (!atom.nucleusIds.includes(seed.nucleusId)) atom.nucleusIds.push(seed.nucleusId);
      seed.atomIds.push(atom.id);
      if (!existing) indexAtom(atom);
    });
    placedClusters.push(seed);
  });
  initializedGrowthNuclei = placedClusters.length;
  selectedNucleusPairKey = initializedGrowthNuclei > 1
    ? `${placedClusters[0].nucleusId}:${placedClusters[1].nucleusId}` : null;
  placedClusters.forEach(enqueueRulesFromPlacement);
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
  const renderScale = pipelineStage === 4 ? 1 : .55;
  const material = new THREE.LineBasicMaterial({ color: COLORS.line, transparent: true, opacity: 0.36 });
  const spec = growthEnvironmentSpec(confinementSelect.value);
  confinementHint.textContent = spec.shortLabel;
  confinementNote.textContent = spec.note;
  if (spec.shape === "orthorhombic box" || spec.shape === "orthorhombic slab") {
    const dims = spec.parameters.halfExtents.map((value) => value * 2 * renderScale);
    confinementGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(...dims)), material));
  } else if (spec.shape === "sphere") {
    const radius = spec.parameters.radius * renderScale;
    confinementGroup.add(new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.SphereGeometry(radius, 20, 13)), material));
  } else if (spec.shape === "x-axis cylinder") {
    const radius = spec.parameters.radius * renderScale;
    const length = spec.parameters.halfLength * 2 * renderScale;
    confinementGroup.add(new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.CylinderGeometry(radius, radius, length, 22, 4, true)), material));
    confinementGroup.rotation.z = Math.PI / 2;
  } else if (spec.shape === "bounded half-space above a plane") {
    const width = spec.parameters.lateralHalfExtents[0] * 2 * renderScale;
    const depth = spec.parameters.lateralHalfExtents[1] * 2 * renderScale;
    const height = (spec.parameters.upperZ - spec.parameters.lowerZ) * renderScale;
    const outline = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(width, depth, height)), material);
    outline.position.z = (spec.parameters.upperZ + spec.parameters.lowerZ) * .5 * renderScale;
    confinementGroup.add(outline);
    const grid = new THREE.GridHelper(width, 12, 0xffbe5c, 0x735f39);
    grid.rotation.x = Math.PI / 2;
    grid.position.z = spec.parameters.lowerZ * renderScale;
    grid.material.transparent = true;
    grid.material.opacity = .32;
    confinementGroup.add(grid);
    const template = epitaxyTemplateSpec();
    if (template) {
      const latticeSpacing = referenceSpacing * (1 + template.mismatch) * renderScale;
      const azimuth = template.angleDegrees * Math.PI / 180;
      const templatePoints = [];
      for (let first = -18; first <= 18; first++) {
        for (let second = -18; second <= 18; second++) {
          const localX = template.symmetry === "hexagonal"
            ? latticeSpacing * (first + .5 * second) : latticeSpacing * first;
          const localY = template.symmetry === "hexagonal"
            ? latticeSpacing * Math.sqrt(3) * .5 * second : latticeSpacing * second;
          const x = Math.cos(azimuth) * localX - Math.sin(azimuth) * localY;
          const y = Math.sin(azimuth) * localX + Math.cos(azimuth) * localY;
          if (Math.abs(x) <= width * .5 && Math.abs(y) <= depth * .5) {
            templatePoints.push(x, y, spec.parameters.lowerZ * renderScale + .025);
          }
        }
      }
      const templateGeometry = new THREE.BufferGeometry();
      templateGeometry.setAttribute("position", new THREE.Float32BufferAttribute(templatePoints, 3));
      confinementGroup.add(new THREE.Points(templateGeometry,
        new THREE.PointsMaterial({ color: 0xffb15c, size: .075, transparent: true, opacity: .82 })));
    }
  } else {
    const length = spec.parameters.halfLength * renderScale;
    const points = [];
    for (let ring = -length; ring <= length; ring += renderScale) {
      const radius = spec.parameters.throatRadius * renderScale + spec.parameters.radialSlope * Math.abs(ring);
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

function discoveryEdgeKey(first, second) {
  return first < second ? `${first}:${second}` : `${second}:${first}`;
}

function discoveryHash(first, second, salt = 0) {
  let value = Math.imul(first + 1, 0x45d9f3b) ^ Math.imul(second + 1, 0x119de1f3) ^ salt;
  value = Math.imul(value ^ value >>> 16, 0x45d9f3b);
  return (value ^ value >>> 16) >>> 0;
}

function minimumSpanningSupportEdges(support) {
  const members = [...new Set(support)].filter((index) => referenceAtoms[index]);
  if (members.length < 2) return [];
  const visited = new Set([members[0]]);
  const edges = [];
  while (visited.size < members.length) {
    let best = null;
    visited.forEach((first) => members.forEach((second) => {
      if (visited.has(second)) return;
      const length = periodicDisplacement(referenceAtoms[first], referenceAtoms[second]).length();
      const key = discoveryEdgeKey(first, second);
      if (!best || length < best.length - 1e-9 || (Math.abs(length - best.length) <= 1e-9 && key < best.key)) {
        best = { first, second, length, key };
      }
    }));
    if (!best) break;
    visited.add(best.second);
    edges.push(best);
  }
  return edges;
}

function placementDiscoveryEdges(placement) {
  const ring = placement.ring?.filter((index) => referenceAtoms[index]);
  if (ring?.length >= 3) return ring.map((first, index) => {
    const second = ring[(index + 1) % ring.length];
    return { first, second,
      length: periodicDisplacement(referenceAtoms[first], referenceAtoms[second]).length(),
      key: discoveryEdgeKey(first, second) };
  });
  return minimumSpanningSupportEdges(placement.support || []);
}

function buildClusterDiscoveryTrace() {
  const types = new Map(clusterGalleryTypes().map((cluster) => [cluster.type, cluster]));
  const finalByKey = new Map();
  const placements = learnedCover.placements.map((placement, placementIndex) => {
    const cluster = types.get(placement.type);
    const family = cluster ? clusterGalleryFamily(cluster) : placement.gap ? "gap" : "support";
    const edges = placementDiscoveryEdges(placement);
    edges.forEach((edge) => {
      const record = finalByKey.get(edge.key) || { ...edge, final: true, families: new Set(),
        types: new Set(), placementIndices: new Set() };
      record.families.add(family);
      record.types.add(placement.type);
      record.placementIndices.add(placementIndex);
      finalByKey.set(edge.key, record);
    });
    return { placementIndex, support: [...new Set(placement.support || [])], family,
      type: placement.type, edgeKeys: edges.map((edge) => edge.key) };
  });
  const finalEdges = [...finalByKey.values()];
  const maximumFinalLength = Math.max(referenceSpacingA * 1.05,
    ...finalEdges.map((edge) => edge.length));
  const candidates = [];
  for (let first = 0; first < referenceAtoms.length; first++) {
    for (let second = first + 1; second < referenceAtoms.length; second++) {
      const key = discoveryEdgeKey(first, second);
      if (finalByKey.has(key)) continue;
      const length = periodicDisplacement(referenceAtoms[first], referenceAtoms[second]).length();
      if (length <= maximumFinalLength * 1.08) candidates.push({ first, second, key, length, final: false,
        families: new Set(["candidate"]), types: new Set(), placementIndices: new Set() });
    }
  }
  candidates.sort((first, second) => first.length - second.length || first.key.localeCompare(second.key));
  const rejectedLimit = Math.min(900, Math.max(referenceAtoms.length * 2, finalEdges.length));
  const totalSteps = 36;
  const edges = [...finalEdges, ...candidates.slice(0, rejectedLimit)].map((edge) => {
    const birthStep = 1 + discoveryHash(edge.first, edge.second, 0x91e10da5) % 7;
    const decisionStep = edge.final
      ? 8 + discoveryHash(edge.first, edge.second, 0x734a9d) % 23
      : 5 + discoveryHash(edge.first, edge.second, 0x2c1b3c6d) % 19;
    return { ...edge, birthStep, decisionStep,
      family: edge.families.has("gap") ? "gap" : edge.families.has("bridge") ? "bridge"
        : edge.families.has("molecule") ? "molecule" : edge.families.has("residual") ? "residual" : "support" };
  });
  const edgeByKey = new Map(edges.filter((edge) => edge.final).map((edge) => [edge.key, edge]));
  placements.forEach((placement) => {
    placement.settleStep = placement.edgeKeys.length
      ? Math.max(...placement.edgeKeys.map((key) => edgeByKey.get(key)?.decisionStep || totalSteps - 1))
      : 10 + discoveryHash(placement.placementIndex, placement.type, 0x6d2b79f5) % 20;
  });
  return { totalSteps, edges, placements, finalEdges: finalEdges.length,
    rejectedEdges: Math.min(rejectedLimit, candidates.length), targetUsed: false };
}

function clusterDiscoveryState(progress = clusterDiscoveryProgress) {
  if (!clusterDiscoveryTrace) return { tentative: [], rejected: [], settled: [], coveredAtoms: new Set(),
    settledPlacements: 0, cumulativeRejected: 0 };
  const tentative = [], rejected = [], settled = [];
  let cumulativeRejected = 0;
  clusterDiscoveryTrace.edges.forEach((edge) => {
    if (progress < edge.birthStep) return;
    if (progress < edge.decisionStep) tentative.push(edge);
    else if (edge.final) settled.push(edge);
    else {
      cumulativeRejected++;
      if (progress < edge.decisionStep + 3) rejected.push(edge);
    }
  });
  const settledPlacements = clusterDiscoveryTrace.placements.filter((placement) => placement.settleStep <= progress);
  return { tentative, rejected, settled,
    coveredAtoms: new Set(settledPlacements.flatMap((placement) => placement.support)),
    settledPlacements: settledPlacements.length, cumulativeRejected };
}

function discoveryEdgePoints(edge) {
  const start = referenceAtoms[edge.first].p.clone();
  const scale = referenceSpacing / referenceSpacingA;
  const finish = start.clone().add(periodicDisplacement(
    referenceAtoms[edge.first], referenceAtoms[edge.second]).multiplyScalar(scale));
  return [start, finish];
}

function addDiscoveryLines(edges, color, opacity, depthTest = true) {
  if (!edges.length) return;
  clusterGroup.add(new THREE.LineSegments(
    new THREE.BufferGeometry().setFromPoints(edges.flatMap(discoveryEdgePoints)),
    new THREE.LineBasicMaterial({ color, transparent: true, opacity, depthTest }),
  ));
}

function buildClusterDiscoveryOverlay() {
  const state = clusterDiscoveryState();
  addDiscoveryLines(state.tentative, 0x84b8b2, .24);
  addDiscoveryLines(state.rejected, COLORS.red, .88, false);
  const colors = { molecule: 0x65e1bc, bridge: 0x55c8ff, gap: 0xffc169,
    residual: 0xff6d71, support: 0xb594ff };
  Object.entries(colors).forEach(([family, color]) =>
    addDiscoveryLines(state.settled.filter((edge) => edge.family === family), color, family === "gap" ? .72 : .58));
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
    buildClusterDiscoveryOverlay();
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
  const nominalTolerance = { strict: 1, balanced: 2.5, thermal: 5 }[config.clusterToleranceMode || "balanced"];
  const effectiveTolerance = 100 * (config.effectiveMetricToleranceFraction || nominalTolerance / 100);
  const tolerance = `ε${Math.abs(effectiveTolerance - nominalTolerance) > .05 ? `${nominalTolerance}→${effectiveTolerance.toFixed(1)}` : nominalTolerance}%`;
  return `M${String(id).padStart(2, "0")} · ${domain} · ${tolerance} · ${channels} · R${config.reach} · ${representation}`;
}

function compatibleMarkings() {
  const key = markingMaterialKey();
  const vocabularyKey = markingVocabularyKey();
  return markingLibrary.filter((marking) => marking.materialKey === key
    && (marking.config.geometryMode || "auto") === geometryMode
    && (marking.config.clusterToleranceMode || "balanced") === clusterToleranceMode
    && marking.vocabularyKey === vocabularyKey
    && marking.coefficients.length === markingPrototypeTypes().length);
}

function freezeCurrentMarking() {
  if (!sectionModel) return null;
  const config = { channels: sectionModel.channels, channelMode: sectionModel.channelMode,
    reach: sectionModel.reach, representation: sectionModel.representation, geometryMode, clusterToleranceMode,
    effectiveMetricToleranceFraction: effectiveClusterMetricTolerance(),
    effectiveMetricToleranceAngstrom: clusterMetricToleranceAngstrom() };
  const materialKey = markingMaterialKey();
  const vocabularyKey = markingVocabularyKey();
  let marking = markingLibrary.find((candidate) => candidate.materialKey === materialKey
    && candidate.vocabularyKey === vocabularyKey
    && candidate.config.channels === config.channels
    && (candidate.config.channelMode || "manual") === config.channelMode
    && candidate.config.reach === config.reach
    && (candidate.config.geometryMode || "auto") === config.geometryMode
    && (candidate.config.clusterToleranceMode || "balanced") === config.clusterToleranceMode
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
  const axialTypes = orientationAtlas.filter((entry) => poseAtlasEntryStatus(entry) === "sampled axial continuum").length;
  const unresolvedTypes = orientationAtlas.filter((entry) => poseAtlasEntryStatus(entry) === "unresolved support").length;
  const supportSummary = freeTypes || axialTypes || unresolvedTypes
    ? `${total} observed poses${freeTypes ? ` · ${freeTypes} equivariant ${rotationGroupLabel()}` : ""}${axialTypes ? ` · ${axialTypes} axial` : ""}${unresolvedTypes ? ` · ${unresolvedTypes} unresolved` : ""}`
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
    detail.textContent = `${entry.element} · ${entry.occurrences} occurrences · ${entry.properSymmetryGaugeCount || 1} proper gauge${entry.properSymmetryGaugeCount === 1 ? "" : "s"} · ${portRank} port role${portRank === 1 ? "" : "s"} · coupled rank ${coupledRank}`;
    const count = document.createElement("b");
    const support = poseAtlasEntryStatus(entry);
    count.textContent = support === "finite required set"
      ? `${entry.orientations} required pose${entry.orientations === 1 ? "" : "s"} → ${channels}ch`
      : support === "sampled continuum"
        ? `${entry.orientations} sampled · equivariant ${rotationGroupLabel()} → ${channels}ch`
        : support === "sampled axial continuum"
          ? `${entry.orientations} sampled axes · equivariant stabilizer → ${channels}ch`
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
  const occupational = audit.occupationalAlternativesPreserved;
  const unavailable = audit.reason === "unsupported chemistry metadata" || occupational;
  panel.classList.add(unavailable ? "unavailable" : "rejected");
  molecularHypothesisState.textContent = unavailable
    ? occupational ? "not evaluated · occupational alternatives have no single valence/radius"
      : `not evaluated · missing ${audit.unsupportedElements.join(" / ") || "chemistry metadata"}`
    : `rejected · ${audit.reason}`;
  molecularHypothesisEvidence.textContent = unavailable
    ? occupational ? "the complete occupancy vector is retained by the irregular support learner"
      : "no element-specific rule was invented; geometry falls back safely"
    : `${audit.covalentEdges} candidate bonds · ${audit.components} component${audit.components === 1 ? "" : "s"} · largest ${audit.largestComponent} atoms`;
  molecularHypothesisRoute.textContent = "irregular cover";
}

function currentGrowthProtocolSettings() {
  return {
    confinement: confinementSelect.value, geometryPreference, geometricStrainWeight,
    compositionPreference, chargePreference, surfacePreference,
    frontMorphologyMode, frontMorphologyWeight, epitaxyTemplateMode, epitaxyWeight,
    externalDriveMode, externalDriveWeight, affineLoadMode, affineLoadMagnitude,
    robustnessPreference, robustnessWeight, microstructureCouplingMode, microstructureCouplingWeight,
    loopClosurePreference, loopClosureWeight, arrivalPathMode, arrivalPathWeight,
    geometricExplorationScale, growthPathSeed, requestedGrowthNuclei, growthScheduling, hierarchyEnabled,
  };
}

function growthProtocolManifest() {
  const protocol = GROWTH_PROTOCOLS[growthProtocolMode];
  return {
    id: growthProtocolMode,
    label: protocol?.label || "custom experiment",
    summary: protocol?.summary || "Every search control remains independent and receipt-visible.",
    preset: Boolean(protocol),
    settings: currentGrowthProtocolSettings(),
    convenienceOnly: true,
    hiddenPhysicsAdded: false,
    candidateGeometryAuthorized: false,
  };
}

function renderGrowthProtocolSummary() {
  const manifest = growthProtocolManifest();
  growthProtocolSelect.value = growthProtocolMode;
  growthProtocolHint.textContent = manifest.preset ? "audited control bundle" : "custom settings";
  const span = document.createElement("span"); const title = document.createElement("b");
  const copy = document.createElement("small"); title.textContent = manifest.label; copy.textContent = manifest.summary;
  span.append(title, copy); growthProtocolSummary.replaceChildren(span);
}

function applyGrowthProtocol(mode) {
  const protocol = GROWTH_PROTOCOLS[mode];
  if (!protocol) {
    growthProtocolMode = "custom";
    renderGrowthProtocolSummary();
    return;
  }
  const settings = { ...GROWTH_PROTOCOL_DEFAULTS, ...protocol.settings };
  growthProtocolMode = mode;
  confinementSelect.value = settings.confinement;
  geometryPreference = settings.geometryPreference; geometricStrainWeight = settings.geometricStrainWeight;
  compositionPreference = settings.compositionPreference; chargePreference = settings.chargePreference;
  surfacePreference = settings.surfacePreference;
  frontMorphologyMode = settings.frontMorphologyMode; frontMorphologyWeight = settings.frontMorphologyWeight;
  epitaxyTemplateMode = settings.epitaxyTemplateMode; epitaxyWeight = settings.epitaxyWeight;
  externalDriveMode = settings.externalDriveMode; externalDriveWeight = settings.externalDriveWeight;
  affineLoadMode = settings.affineLoadMode; affineLoadMagnitude = settings.affineLoadMagnitude;
  robustnessPreference = settings.robustnessPreference; robustnessWeight = settings.robustnessWeight;
  microstructureCouplingMode = settings.microstructureCouplingMode;
  microstructureCouplingWeight = settings.microstructureCouplingWeight;
  loopClosurePreference = settings.loopClosurePreference; loopClosureWeight = settings.loopClosureWeight;
  arrivalPathMode = settings.arrivalPathMode; arrivalPathWeight = settings.arrivalPathWeight;
  geometricExplorationScale = settings.geometricExplorationScale; growthPathSeed = 1;
  requestedGrowthNuclei = settings.requestedGrowthNuclei; growthScheduling = settings.growthScheduling;
  hierarchyEnabled = settings.hierarchyEnabled;
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
}

function syncStageOptions() {
  const visible = pipelineStage === 1 || pipelineStage === 3 || pipelineStage === 4;
  externalDriveBadge.hidden = pipelineStage !== 4 || externalDriveMode === "none";
  externalDriveBadgeLabel.textContent = externalDriveModeLabel();
  externalDriveGlyph.textContent = ({ "z-plus": "↑", "z-minus": "↓",
    "radial-out": "↗", "radial-in": "↙" })[externalDriveMode] || "·";
  affineLoadBadge.hidden = pipelineStage !== 4 || affineLoadMode === "none";
  affineLoadBadge.classList.toggle("solo", externalDriveMode === "none");
  affineLoadBadgeLabel.textContent = `${Math.round(affineLoadMagnitude * 100)}% ${affineLoadModeLabel()}`;
  affineLoadGlyph.textContent = ({ "hydro-compress": "↘", "hydro-tension": "↗",
    "z-tension": "⇅", "xy-shear": "⇆" })[affineLoadMode] || "·";
  loopClosureBadge.hidden = pipelineStage !== 4 || loopClosurePreference === "none";
  loopClosureBadge.style.top = `${49 + 35 * Number(externalDriveMode !== "none")
    + 35 * Number(affineLoadMode !== "none")}px`;
  loopClosureBadgeLabel.textContent = `loop closure · w ${loopClosureWeight.toFixed(2)}`;
  arrivalPathBadge.hidden = pipelineStage !== 4 || arrivalPathMode === "none";
  arrivalPathBadge.style.top = `${49 + 35 * Number(externalDriveMode !== "none")
    + 35 * Number(affineLoadMode !== "none") + 35 * Number(loopClosurePreference !== "none")}px`;
  arrivalPathBadgeLabel.textContent = `${arrivalPathLabel()} · w ${arrivalPathWeight.toFixed(2)}`;
  explorationBadge.hidden = pipelineStage !== 4 || geometricExplorationScale <= 0;
  explorationBadge.style.top = `${49 + 35 * Number(externalDriveMode !== "none")
    + 35 * Number(affineLoadMode !== "none") + 35 * Number(loopClosurePreference !== "none")
    + 35 * Number(arrivalPathMode !== "none")}px`;
  explorationBadgeLabel.textContent = `T* ${geometricExplorationScale.toFixed(2)} · seed ${growthPathSeed}`;
  nucleiBadge.hidden = pipelineStage !== 4 || initializedGrowthNuclei <= 1;
  nucleiBadge.style.top = `${49 + 35 * Number(externalDriveMode !== "none")
    + 35 * Number(affineLoadMode !== "none") + 35 * Number(loopClosurePreference !== "none")
    + 35 * Number(arrivalPathMode !== "none") + 35 * Number(geometricExplorationScale > 0)}px`;
  nucleiBadgeLabel.textContent = `${initializedGrowthNuclei || requestedGrowthNuclei} nuclei · ${crossNucleusMergeContacts} interface contacts`;
  frontMorphologyBadge.hidden = pipelineStage !== 4 || frontMorphologyMode === "none";
  frontMorphologyBadge.style.top = `${49 + 35 * Number(externalDriveMode !== "none")
    + 35 * Number(affineLoadMode !== "none") + 35 * Number(loopClosurePreference !== "none")
    + 35 * Number(arrivalPathMode !== "none") + 35 * Number(geometricExplorationScale > 0)
    + 35 * Number(initializedGrowthNuclei > 1)}px`;
  frontMorphologyBadgeLabel.textContent = `${frontMorphologyLabel()} · w ${frontMorphologyWeight.toFixed(2)}`;
  epitaxyBadge.hidden = pipelineStage !== 4 || activeEpitaxyWeight() <= 0;
  epitaxyBadge.style.top = `${49 + 35 * Number(externalDriveMode !== "none")
    + 35 * Number(affineLoadMode !== "none") + 35 * Number(loopClosurePreference !== "none")
    + 35 * Number(arrivalPathMode !== "none") + 35 * Number(geometricExplorationScale > 0)
    + 35 * Number(initializedGrowthNuclei > 1) + 35 * Number(frontMorphologyMode !== "none")}px`;
  epitaxyBadgeLabel.textContent = `${epitaxyTemplateLabel()} · w ${epitaxyWeight.toFixed(2)}`;
  renderNucleusInterfaceInspector();
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
    clusterToleranceSelect.value = clusterToleranceMode;
    const thermalFloor = measuredPairUncertaintyAngstrom();
    clusterToleranceHint.textContent = thermalFloor > referenceSpacingA * clusterMetricTolerance()
      ? `${(effectiveClusterMetricTolerance() * 100).toFixed(1)}% effective · ${clusterMetricToleranceAngstrom().toFixed(3)} Å · ${measuredPairUncertaintySource()}`
      : `${(clusterMetricTolerance() * 100).toFixed(1)}% of nearest-neighbor scale · ${clusterMetricToleranceAngstrom().toFixed(3)} Å`;
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
    const freeTypes = orientationAtlas.filter((entry) => ["sampled continuum", "sampled axial continuum"].includes(poseAtlasEntryStatus(entry))).length;
    const unresolvedTypes = orientationAtlas.filter((entry) => poseAtlasEntryStatus(entry) === "unresolved support").length;
    rotationSupport.textContent = poseSupportLabel(totalPoses, freeTypes, unresolvedTypes);
    channelRankSupport.textContent = `${automaticMarkingChannels()} auto channel${automaticMarkingChannels() === 1 ? "" : "s"}`;
    renderMolecularHypothesis();
    renderPoseAtlas();
    const toleranceLabel = `ε ${(effectiveClusterMetricTolerance() * 100).toFixed(1)}%`;
    stageOptionsState.textContent = `${resolvedMode === "module" ? "aperiodic module"
      : resolvedMode === "offlattice" ? `metric-set ${rotationGroupLabel()}` : "lattice candidate"} · ${toleranceLabel}`;
    return;
  }
  const resolvedChannels = sectionModel?.channels || currentMarkingConfig().channels;
  const inheritedDomain = resolvedGeometryLabel();
  const inheritedPoses = orientationAtlas.reduce((sum, entry) => sum + entry.orientations, 0);
  const inheritedFreeTypes = orientationAtlas.filter((entry) => ["sampled continuum", "sampled axial continuum"].includes(poseAtlasEntryStatus(entry))).length;
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
    renderGrowthProtocolSummary();
    markingSearchModeSelect.value = markingSearchMode;
    const active = selectedMarking();
    const finiteIceAnchorMode = Boolean(iceAnchorTrace);
    geometryPreferenceSelect.value = geometryPreference;
    strainWeightSelect.value = String(geometricStrainWeight);
    compositionPreferenceSelect.value = compositionPreference;
    chargePreferenceSelect.value = chargePreference;
    surfacePreferenceSelect.value = surfacePreference;
    frontMorphologySelect.value = frontMorphologyMode;
    frontMorphologyWeightSelect.value = String(frontMorphologyWeight);
    epitaxyTemplateSelect.value = epitaxyTemplateMode;
    epitaxyWeightSelect.value = String(epitaxyWeight);
    externalDriveSelect.value = externalDriveMode;
    externalDriveWeightSelect.value = String(externalDriveWeight);
    affineLoadSelect.value = affineLoadMode;
    affineLoadMagnitudeSelect.value = String(affineLoadMagnitude);
    robustnessPreferenceSelect.value = robustnessPreference;
    robustnessWeightSelect.value = String(robustnessWeight);
    microstructureCouplingSelect.value = microstructureCouplingMode;
    microstructureCouplingWeightSelect.value = String(microstructureCouplingWeight);
    loopClosurePreferenceSelect.value = loopClosurePreference;
    loopClosureWeightSelect.value = String(loopClosureWeight);
    arrivalPathSelect.value = arrivalPathMode;
    arrivalPathWeightSelect.value = String(arrivalPathWeight);
    explorationScaleSelect.value = String(geometricExplorationScale);
    growthNucleiSelect.value = String(requestedGrowthNuclei);
    growthSchedulingSelect.value = growthScheduling;
    geometryPreferenceSelect.disabled = finiteIceAnchorMode;
    strainWeightSelect.disabled = finiteIceAnchorMode || geometryPreference !== "strain";
    compositionPreferenceSelect.disabled = finiteIceAnchorMode;
    chargePreferenceSelect.disabled = finiteIceAnchorMode || !formalChargeTarget?.available;
    surfacePreferenceSelect.disabled = finiteIceAnchorMode;
    frontMorphologySelect.disabled = finiteIceAnchorMode;
    frontMorphologyWeightSelect.disabled = finiteIceAnchorMode || frontMorphologyMode === "none";
    epitaxyTemplateSelect.disabled = finiteIceAnchorMode || confinementSelect.value !== "substrate";
    epitaxyWeightSelect.disabled = finiteIceAnchorMode || confinementSelect.value !== "substrate" || epitaxyTemplateMode === "none";
    externalDriveSelect.disabled = finiteIceAnchorMode;
    externalDriveWeightSelect.disabled = finiteIceAnchorMode || externalDriveMode === "none";
    affineLoadSelect.disabled = finiteIceAnchorMode;
    affineLoadMagnitudeSelect.disabled = finiteIceAnchorMode || affineLoadMode === "none";
    robustnessPreferenceSelect.disabled = finiteIceAnchorMode;
    robustnessWeightSelect.disabled = finiteIceAnchorMode || robustnessPreference === "none";
    microstructureCouplingSelect.disabled = finiteIceAnchorMode;
    microstructureCouplingWeightSelect.disabled = finiteIceAnchorMode || microstructureCouplingMode === "none";
    loopClosurePreferenceSelect.disabled = finiteIceAnchorMode;
    loopClosureWeightSelect.disabled = finiteIceAnchorMode || loopClosurePreference === "none";
    arrivalPathSelect.disabled = finiteIceAnchorMode;
    arrivalPathWeightSelect.disabled = finiteIceAnchorMode || arrivalPathMode === "none";
    explorationScaleSelect.disabled = finiteIceAnchorMode;
    growthNucleiSelect.disabled = finiteIceAnchorMode;
    resampleGrowthButton.disabled = finiteIceAnchorMode || geometricExplorationScale <= 0;
    resampleGrowthButton.textContent = `↻ Resample path · seed ${growthPathSeed}`;
    growthSchedulingSelect.disabled = finiteIceAnchorMode;
    growthSchedulingHint.textContent = growthScheduling === "commuting"
      ? "maximal commuting set" : "one branch decision";
    strainWeightHint.textContent = geometryPreference === "strain"
      ? `${geometricStrainWeight.toFixed(2)} soft` : "disabled";
    chargePreferenceHint.textContent = formalChargeTarget?.available
      ? `${formalChargeTarget.resolvedObservations}/${formalChargeTarget.observations} sites · q̄ ${formalChargeTarget.meanFormalCharge >= 0 ? "+" : ""}${formalChargeTarget.meanFormalCharge.toFixed(3)}`
      : `${formalChargeTarget?.resolvedObservations || 0}/${formalChargeTarget?.observations || referenceCount()} sites · unavailable`;
    externalDriveHint.textContent = externalDriveMode === "none"
      ? "isotropic · weight zero" : `${externalDriveModeLabel()} · weight ${externalDriveWeight.toFixed(2)}`;
    affineLoadHint.textContent = affineLoadMode === "none"
      ? "undeformed metric" : `${Math.round(affineLoadMagnitude * 100)}% ${affineLoadModeLabel()}`;
    robustnessHint.textContent = robustnessPreference === "margin"
      ? `minimum margin · weight ${robustnessWeight.toFixed(2)}` : "diagnostic · weight zero";
    microstructureCouplingHint.textContent = microstructureCouplingMode === "none"
      ? "neutral · weight zero" : `${microstructureCouplingLabel()} · weight ${microstructureCouplingWeight.toFixed(2)}`;
    loopClosureHint.textContent = loopClosurePreference === "consensus"
      ? `multi-parent consensus · weight ${loopClosureWeight.toFixed(2)}` : "local-only · weight zero";
    arrivalPathHint.textContent = arrivalPathMode === "none"
      ? "not ranked · final pose only"
      : arrivalPathMode === "declared-drive" && externalDriveMode === "none"
        ? "requires external driving geometry · score zero"
        : `${arrivalPathLabel()} · 9 samples × 2dₙₙ · weight ${arrivalPathWeight.toFixed(2)}`;
    explorationScaleHint.textContent = geometricExplorationScale > 0
      ? `dimensionless T* ${geometricExplorationScale.toFixed(2)} · seed ${growthPathSeed}` : "greedy · T* = 0";
    growthNucleiHint.textContent = finiteIceAnchorMode ? "sealed molecular seed"
      : `${initializedGrowthNuclei || requestedGrowthNuclei} observed seed${(initializedGrowthNuclei || requestedGrowthNuclei) === 1 ? "" : "s"} · ${crossNucleusMergeContacts} interface contacts`;
    frontMorphologyHint.textContent = frontMorphologyMode === "none"
      ? "neutral · diagnostic" : `${frontMorphologyLabel()} · weight ${frontMorphologyWeight.toFixed(2)}`;
    epitaxyTemplateHint.textContent = confinementSelect.value !== "substrate"
      ? "choose supported-film geometry"
      : epitaxyTemplateMode === "none" ? "inert excluded plane · registry off"
        : `${epitaxyTemplateLabel()} · weight ${epitaxyWeight.toFixed(2)}`;
    stageOptionsState.textContent = `${growthProtocolMode === "custom" ? "custom" : GROWTH_PROTOCOLS[growthProtocolMode].label} · ${policySelect.value === "marked" && active ? active.name.split(" · ")[0] : "baseline"} · ${geometryPreference === "strain" ? `strain ${geometricStrainWeight.toFixed(2)}` : "no strain"}`;
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
      ? ` A frozen sample-derived contact/angle strain adds a ${geometricStrainWeight.toFixed(2)} soft ordering term over that same candidate set${affineLoadMode === "none" ? "." : ` after the metric is transformed by the declared ${Math.round(affineLoadMagnitude * 100)}% ${affineLoadModeLabel()}; coordinates and hard gates stay unchanged.`}`
      : " Geometric strain is reported but contributes zero ranking weight for this ablation.";
    const ratio = Object.entries(compositionTarget.reducedRatio).map(([symbol, count]) => `${symbol}${count === 1 ? "" : count}`).join("");
    const compositionUse = compositionPreference === "none"
      ? " Composition drift is reported but contributes zero ranking weight."
      : ` A ${compositionPreference === "strong" ? "strong" : "balanced"} soft reservoir term favors the observed ${ratio} ratio without constraining an incomplete surface.`;
    const chargeUse = !formalChargeTarget?.available
      ? " No complete formal oxidation-state channel was supplied, so charge ranking fails closed at weight zero."
      : chargePreference === "none"
        ? " Formal-charge drift is reported but contributes zero ranking weight."
        : ` A ${chargePreference === "strong" ? "strong" : "balanced"} formal-charge-density term softly favors the supplied mean q̄=${formalChargeTarget.meanFormalCharge.toFixed(3)}; it is bookkeeping, not electrostatic energy.`;
    const surfaceUse = surfacePreference === "none"
      ? " Coordination deficit is reported but contributes zero ranking weight."
      : ` A ${surfacePreference === "strong" ? "strong" : "balanced"} soft surface-completion term favors actions that heal observed coordination deficits without requiring a complete frontier shell.`;
    const externalDriveUse = externalDriveMode === "none"
      ? " No external direction is preferred."
      : ` A user-declared ${externalDriveModeLabel()} direction adds a ${externalDriveWeight.toFixed(2)} soft alignment term to the same actions; it is boundary/loading geometry, not a solved force field.`;
    const robustnessUse = robustnessPreference === "margin"
      ? ` A ${robustnessWeight.toFixed(2)} soft robustness term prefers the largest minimum normalized contact, overlap, or boundary safety margin; it does not sample temperature or change hard admission.`
      : " Constraint margins are reported but contribute zero ranking weight.";
    const microstructureUse = microstructureCouplingMode === "none"
      ? " Heterogeneous-geometry correlations remain post-decision diagnostics."
      : ` A user-declared ${microstructureCouplingLabel()} hypothesis adds a ${microstructureCouplingWeight.toFixed(2)} soft term from frozen input-derived roles; no defect identity or formation energy is assumed.`;
    const loopClosureUse = loopClosurePreference === "consensus"
      ? ` A ${loopClosureWeight.toFixed(2)} mesoscopic term rewards independent frozen-rule paths that close onto the same proper-SE(3) pose and penalizes nearby incompatible paths.`
      : " Multi-parent loop closure is reported but contributes zero rank weight.";
    const arrivalPathUse = arrivalPathMode === "none"
      ? " Swept arrival clearance is disabled; only the final pose is tested."
      : ` A ${arrivalPathWeight.toFixed(2)} soft accessibility term sweeps emitted sites along a 9-point ${arrivalPathLabel()} path spanning 2dₙₙ; it is not a barrier or trajectory.`;
    const explorationUse = geometricExplorationScale > 0
      ? ` Reproducible Gumbel sampling at dimensionless T*=${geometricExplorationScale.toFixed(2)} and seed ${growthPathSeed} explores alternate exact branch orders; this is not Kelvin temperature or Boltzmann sampling.`
      : " Frontier selection is deterministic greedy ordering (T*=0).";
    const nucleiUse = requestedGrowthNuclei > 1
      ? ` ${initializedGrowthNuclei || requestedGrowthNuclei} far-separated observed cluster occurrences seed independent pose domains; ${crossNucleusMergeContacts} cross-nucleus shared-site contacts have emerged. No nucleation rate or grain identity is inferred.`
      : " Growth begins from one observed local cluster occurrence.";
    const morphologyUse = frontMorphologyMode === "none"
      ? " Mesoscopic angular support and backing depth are reported but have zero rank weight."
      : ` A ${frontMorphologyWeight.toFixed(2)} soft ${frontMorphologyLabel()} term ranks the same exact actions from their parent-local angular support and backing-depth profile; it is not surface energy or mean curvature.`;
    const epitaxyUse = activeEpitaxyWeight() <= 0
      ? confinementSelect.value === "substrate" ? " The support plane remains inert excluded geometry; epitaxial registry contributes zero rank weight." : " No support-plane template is active."
      : ` A declared ${epitaxyTemplateLabel()} ranks interfacial sites within 3.5dₙₙ of the support at weight ${epitaxyWeight.toFixed(2)}; it supplies no substrate atoms, adhesion, or interface energy.`;
    growthModeNote.textContent = finiteIceAnchorMode
      ? "This sealed ice gate executes primitive H₂O connection ports with mutually exclusive orientation domains. Clusters² is disabled because no stationary promoted ice production has been certified."
      : hierarchyEnabled
      ? `Accepted clusters expose frozen ports and may promote into clusters². ${growthScheduling === "commuting" ? "Each displayed update is a permutation-certified antichain over the underlying tree." : "Each displayed update executes one best-first branch."} ${markingUse}${strainUse}${compositionUse}${chargeUse}${surfaceUse}${externalDriveUse}${robustnessUse}${microstructureUse}${loopClosureUse}${arrivalPathUse}${explorationUse}${nucleiUse}${morphologyUse}${epitaxyUse}`
      : `Primitive-only mode permits the seed frontier but prevents accepted clusters from spawning another recursive frontier. ${growthScheduling === "commuting" ? "Compatible placements may still be displayed as one permutation-certified antichain." : "Placements are executed one best-first branch at a time."} ${markingUse}${strainUse}${compositionUse}${chargeUse}${surfaceUse}${externalDriveUse}${robustnessUse}${microstructureUse}${loopClosureUse}${arrivalPathUse}${explorationUse}${nucleiUse}${morphologyUse}${epitaxyUse}`;
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
  acceptedUnloadedGeometricStrain = 0;
  rejectedUnloadedGeometricStrain = 0;
  acceptedCompositionDelta = 0;
  rejectedCompositionDelta = 0;
  acceptedFormalChargeDelta = 0;
  rejectedFormalChargeDelta = 0;
  acceptedSurfaceDeficit = 0;
  rejectedSurfaceDeficit = 0;
  acceptedExternalDriveAlignment = 0;
  rejectedExternalDriveAlignment = 0;
  acceptedRobustnessScore = 0;
  rejectedRobustnessScore = 0;
  acceptedMicrostructureCouplingScore = 0;
  rejectedMicrostructureCouplingScore = 0;
  acceptedLoopClosureScore = 0;
  rejectedLoopClosureScore = 0;
  acceptedIndependentLoopWitnesses = 0;
  rejectedIndependentLoopWitnesses = 0;
  acceptedArrivalPathScore = 0;
  rejectedArrivalPathScore = 0;
  acceptedBlockedPathSamples = 0;
  rejectedBlockedPathSamples = 0;
  arrivalPathSiteSamples = 0;
  arrivalPathNeighborhoodChecks = 0;
  acceptedExplorationOffset = 0;
  rejectedExplorationOffset = 0;
  acceptedFrontMorphologyScore = 0;
  rejectedFrontMorphologyScore = 0;
  frontMorphologyEvaluations = 0;
  frontMorphologyNeighborhoodChecks = 0;
  acceptedEpitaxyRegistryScore = 0;
  rejectedEpitaxyRegistryScore = 0;
  epitaxyRegistryEvaluations = 0;
  epitaxyRegistrySiteChecks = 0;
  initializedGrowthNuclei = 0;
  coalescenceEvents = 0;
  crossNucleusMergeContacts = 0;
  selectedNucleusPairKey = null;
  constraintNeighborhoodEvaluations = 0;
  constraintNeighborhoodSiteTotal = 0;
  maximumConstraintNeighborhoodSites = 0;
  lastPolicyComparison = null;
  policyComparisonHistory = [];
  selectedPolicySnapshotIndex = -1;
  selectedPolicyPreviewId = "active";
  policySnapshotCount = 0;
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
  clusterDiscoveryTrace = null;
  clusterDiscoveryProgress = 0;
  leapHistory = [];
  selectedLeapIndex = -1;
  leapEventCount = 0;
  selectedLeapPhysicsId = "steric";
  growthMechanismEvents = [];
  growthMechanismTotals = {};
  growthPoseAuditsByLeap = new Map();
  growthMechanismProjectionKey = "xy";
  markingSelection = null;
  liveOrderCache = { key: "", result: null };
  liveOrderHistory = [];
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
  if (scenarioSelect.value === "imported") syncImportedFrameMaterial();
  rngState = 0x8f23ab17 ^ scenarioSelect.selectedIndex * 0x91e10da5 ^ confinementSelect.selectedIndex * 0x734a9d;
  referenceAtoms = makeReferenceConfiguration();
  referenceSpacing = scenarioSelect.value === "imported" ? .92 : medianNearestSpacing(referenceAtoms);
  referenceSpacingA = scenarioSelect.value === "imported"
    ? currentImportedFrameValidation().medianNearestDistance
    : referenceSpacing / .92 * currentMaterial().spacingA;
  ensemblePairDistanceUncertainty = learnReferenceEnsemblePairUncertainty();
  coloredDistanceEnvelopes = learnReferenceDistanceEnvelopes(referenceAtoms);
  coloredCoordinationEnvelopes = learnReferenceCoordinationEnvelopes(referenceAtoms);
  coloredAngularEnvelopes = learnReferenceAngularEnvelopes(referenceAtoms);
  compositionTarget = learnCompositionTarget(referenceAtoms.map((atom) => atom.species));
  formalChargeTarget = learnFormalChargeTarget(referenceAtoms.map((atom) => atom.species), formalChargeFromChemistryToken);
  referenceStructuralStats = calculateStructuralStats(referenceAtoms, referenceSpacing, currentPbc().some(Boolean),
    currentMaterial().intrinsicDimension === 2 ? 2 : 3);
  learnedClusters = learnLocalEnvironmentClusters(referenceAtoms);
  learnedCover = buildExhaustiveClusterCover(referenceAtoms);
  detectedUnitCell = geometryMode === "module" || geometryMode === "offlattice" ? null : inferTranslationCell(referenceAtoms);
  trainedMarking = learnOverlapMarking(referenceAtoms);
  overlapGrammar = learnOverlapGrammar(referenceAtoms);
  orientationAtlas = learnOrientationAtlas();
  microstructureEvidence = learnMicrostructureEvidence();
  clusterDiscoveryTrace = buildClusterDiscoveryTrace();
  clusterDiscoveryProgress = pipelineStage === 1
    ? Math.min(1, clusterDiscoveryTrace.totalSteps) : clusterDiscoveryTrace.totalSteps;
  if (pipelineStage === 1) eventIndex = clusterDiscoveryProgress;
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
  else if (currentMaterial().growthWithheld) atoms = referenceAtoms.map((atom) => cloneAtom(atom));
  else if (learnedCover.molecular?.water
    && (currentMaterial().icePolytype || scenarioSelect.value === "iceVI")) initializeIceAnchorSearch();
  else initializeOffLatticeSearch();
  if (pipelineStage < 4) rebuildSpatialIndex();
  buildConfinement();
  clusterGroup.rotation.set(0, 0, 0);
  clusterGallery.hidden = pipelineStage !== 3;
  viewport.classList.toggle("cluster-gallery-mode", pipelineStage === 3);
  viewportHint.textContent = pipelineStage === 3
    ? "one evolving marking scene per cluster · scroll for all types"
    : pipelineStage === 1 ? "full configuration · tentative → rejected → settled supports"
      : "drag to orbit · wheel to zoom";
  if (pipelineStage === 3) rebuildClusterGallery();
  buildClusterOverlay();
  updateStageNarrative();
  rebuildWorld();
  updateUI();
  updatePipelineButtons();
  syncStageOptions();
  renderEnsembleControls();
  renderIceViMicrostateControls();
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
  const externalGeometry = growthEnvironmentSpec(confinementSelect.value);
  const clusterCount = markingPrototypeTypes().length;
  const trainingPoint = trainedMarking ? currentTrainingPoint() : { samples: 0, discovered: 0, reusable: 0, overlaps: 0 };
  const narratives = [
    {
      eyebrow: "input · static atom coordinates", title: "Begin with the configuration we know", phase: "observed",
      caption: `${material.name}: element identities and Cartesian positions are supplied in ångströms; no phase or cluster labels are given.${material.averageStructureSites ? " Half-occupied sites are alternatives in an average structure, not simultaneous atoms." : ""}${evidenceFrameCount() > 1 ? ` ${evidenceFrameCount()} fixed-topology snapshots broaden the geometric envelopes without being concatenated.` : ""}`, badge: "input",
      decision: material.name, copy: `The learner receives ${referenceEntityLabel()} for the selected seed frame.${material.averageStructureSites ? ` Their total occupancy is ${material.occupancyWeightedAtomCount.toLocaleString()} atoms.` : ""} ${material.cell}; measured median nearest-neighbor distance ${referenceSpacingA.toFixed(2)} Å.${evidenceFrameCount() > 1 ? ` Contact, coordination, and angle statistics pool ${coloredDistanceEnvelopes.atomPresentations.toLocaleString()} atom presentations across ${coloredDistanceEnvelopes.frameCount} frames.` : ""}`,
      values: [materialElementLabels(material).join(" / "), material.cell, `${referenceSpacingA.toFixed(2)} Å`, `${evidenceFrameCount()} evidence frame${evidenceFrameCount() === 1 ? "" : "s"}`],
    },
    {
      eyebrow: "learning · full-scene support discovery", title: "Let candidate connections compete across the configuration", phase: "discovery 0 / 36",
      caption: `The complete ${currentPbc().some(Boolean) ? "periodic quotient" : "finite non-periodic window"} stays visible while local candidate connections appear, fail consistency tests, disappear, and settle into a complete overlapping cover. Final support classes are not shown as isolated cards until GCTS learning.`, badge: "learn",
      decision: "Testing a center-free support graph", copy: "Element-resolved distance and angle envelopes propose local edges. Proper-isometry recurrence, overlap consistency, and complete-cover accounting decide which connections survive; uncovered connected regions become explicit gap terminals.",
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
        ? `Translated, rotated, and inflated parents continue inside the ${externalGeometry.shortLabel}. Each visual update is one maximal commuting frontier set: every displayed placement is valid in every permutation, while dependent residuals remain explicit tree branches.`
        : `Translated, rotated, and inflated parents continue inside the ${externalGeometry.shortLabel}. Each visual update executes one best-first branch decision; the exact candidate geometry and dependency-ordered tree are unchanged.`, badge: "search",
      decision: "Recursive consensus frontier initialized", copy: growthScheduling === "commuting"
        ? `The same frozen connection marking proposes the next scale. A frontier antichain is displayed only after pairwise species, hard-core, unique-new-support, and ${externalGeometry.shortLabel} containment checks.`
        : `The same frozen connection marking proposes the next scale. One best-first candidate is executed per update inside the ${externalGeometry.shortLabel}, so branch order can be inspected directly.`,
      values: ["parent + φ(source−parent)", `${externalGeometry.shortLabel} · ${policySelect.value === "marked" ? selectedMarking()?.name || "active marking" : policySelect.value === "direct" ? "exact local oracle" : "unmarked action"}`, hierarchyEnabled ? "clusters² promotion" : "primitive clusters", "branch residual"],
    },
  ];
  if (learnedCover.molecular) {
    const water = learnedCover.molecular.water;
    narratives[1].eyebrow = "learning · molecular and gap cover";
    narratives[1].decision = "Molecular overlap cover computed";
    narratives[1].copy = water
      ? `Species-resolved bond geometry discovers one ${learnedCover.molecular.waterLabel || "H₂O"} motif. Shared hydrogen-bond bridges and empty oxygen-ring boundaries are promoted to connection clusters, then the periodic window is audited atom by atom.`
      : "Valence-bounded species geometry discovers recurrent finite molecules. A nearest-component graph supplies molecule-pair connections; locally shortest chordless cycles become explicit void boundaries without an expected formula or ring size.";
    const conformerAccounting = learnedCover.molecular.metricConformerClasses > 1
      ? ` The molecular card retains ${learnedCover.molecular.metricConformerClasses} measured metric conformers as pose subtypes beneath one topological atom-cover class.`
      : "";
    narratives[1].caption = `Across the full atomic scene, candidate species-resolved bonds and intermolecular connections are proposed, rejected, and replaced until ${learnedCover.molecular.molecules} molecular placements, ${learnedCover.molecular.connections} connection polyhedra, and ${learnedCover.molecular.voids} void-boundary polygons cover every observed atom. Surviving H₂O/D₂O edges are molecular bonds—not radial coordination spokes.${conformerAccounting}`;
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
    narratives[3].title = "Learn one connection section on each molecular, bridge, and gap class";
    narratives[3].copy = `Each learned cover class now receives its own rotating 3D card. Its atoms and support polyhedron remain fixed while random local connection contours morph toward the observed overlap marking; literal residual terminals remain visible but are not trained.`;
    if (water) {
      narratives[4].title = `Grow shared oxygen anchors; retain ${iceAnchorTrace?.orientationSpecies || "H"} poses symbolically`;
      narratives[4].phase = "sealed disjoint seed";
      narratives[4].decision = "Frozen molecular-port frontier initialized";
      narratives[4].copy = scenarioSelect.value === "iceVI"
        ? `One positions-and-species-only Ice VI microstate learned ${iceAnchorTrace?.conformerTypes || 5} D₂O conformers and ${iceAnchorTrace?.portCount || 84} proper-SE(3) connection ports. The browser replays the frozen trace on a spatially disjoint microstate nucleus; target coordinates were opened only after the trace was sealed.`
        : `A positions-and-species-only Ih training window learned ${ICE_MOLECULAR_PORT_ARTIFACT.ports.length} proper-SE(3) connection ports. The browser recomputes a disjoint ${scenarioSelect.value === "iceIc" ? "cubic-ice transfer" : "hexagonal-ice"} anchor frontier without target coordinates.`;
      narratives[4].caption = `Only oxygen anchors shared by mutually exclusive ${iceAnchorTrace?.moleculeLabel || "H₂O"} orientation hypotheses are displayed. ${iceAnchorTrace?.orientationSpecies || "H"} alternatives remain symbolic and ${iceAnchorTrace?.selectionRuleLabel || "parent-domain unanimity"} fails closed when the next connection is unsupported.`;
      narratives[4].values = [
        `${iceAnchorTrace?.portCount || ICE_MOLECULAR_PORT_ARTIFACT.ports.length} frozen ports`,
        `${iceAnchorTrace?.seedAnchors || 0} seed O anchors`,
        "target calls 0",
        "stationary claim false",
      ];
    }
  } else if (learnedCover.irregular) {
    narratives[1].eyebrow = "learning · exact irregular support cover";
    narratives[1].title = `Mine recurring colored point sets, then cover every ${material.averageStructureSites ? "average site" : "atom"}`;
    narratives[1].decision = "Center-free recurring-support cover computed";
    narratives[1].copy = `Atomic coordination shells and center-free bond-lens supports are candidate generators only. Translation- and proper-rotation-invariant colored metric plus chirality signatures define the actual support classes; connected uncovered regions become explicit gap terminals.${learnedCover.voidBoundary ? " Fully occupied oxygen-framework rings additionally define empty-region boundaries without selecting any D/vacancy alternative." : ""}`;
    narratives[1].caption = `The whole configuration remains visible while recurring coordination and center-free bond-lens candidates compete. Accepted edges settle into ${learnedCover.placements.length} support occurrences covering ${learnedCover.covered}/${referenceCount()} ${material.averageStructureSites ? "average sites" : "atoms"}; rejected edges flash red and disappear. ${learnedCover.irregular.residualAtoms} uncovered sites remain as explicit gap clusters.${learnedCover.voidBoundary ? ` ${learnedCover.voidBoundary.occurrences} shortest chordless O${learnedCover.voidBoundary.ringSize} boundaries encode empty regions.` : ""}`;
    narratives[1].values = [
      `${learnedCover.irregular.recurringCoordinationClasses} coordination classes`,
      `${learnedCover.irregular.recurringCenterFreeClasses} center-free candidates`,
      `${learnedCover.irregular.selectedCenterFreeOccurrences} selected center-free`,
      `${learnedCover.residualTypes.length + (learnedCover.voidBoundary?.classes || 0)} gap classes · ${learnedCover.irregular.replayConnectorCount} local connectors`,
    ];
    narratives[2].title = "Register rigid ports between the exact support occurrences";
    narratives[2].phase = `${overlapGrammar.rules.length} frozen rules`;
    narratives[2].copy = "Every port maps one complete colored support to another by a proper rigid transform. Residual gaps participate in exact known-window replay but are not promoted into recurrent continuation rules.";
    narratives[3].title = "Fit a separate evolving marking on every recurring support class";
    narratives[3].copy = "The GCTS gallery isolates each learned support in its own rotating 3D scene. Its atoms and polyhedron stay fixed while random connection level sets morph toward the bounded local section learned from overlap observations.";
  }
  if (material.growthWithheld) {
    narratives[4] = {
      eyebrow: "search · occupational state unresolved", title: "Withhold growth rather than materialize half-occupied atoms", phase: "no executable branch",
      caption: "The average oxygen framework, D/vacancy alternatives, and empty-region boundaries remain inspectable. A valid ice-rule microstate or an explicit occupancy-valued ensemble grammar is required before tree search.", badge: "withheld",
      decision: "No unique molecular seed state", copy: "The diffraction average does not select two deuteria around each oxygen. Treating all candidate D sites as simultaneous atoms would create a fictitious structure, so search and phase classification fail closed.",
      values: ["0 executable actions", "target calls 0", "D/vacancy alternatives preserved", "growth claim false"],
    };
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
  chargeValue.textContent = pipelineStage === 4
    ? !formalChargeTarget?.available ? "unavailable · no complete supplied channel"
      : chargePreference === "none" ? "diagnostic only · weight 0"
        : `${chargePreference} formal reservoir · weight ${activeFormalChargeWeight().toFixed(2)}`
    : "not ranked";
  surfaceValue.textContent = pipelineStage === 4
    ? surfacePreference === "none" ? "diagnostic only · weight 0"
      : `${surfacePreference} completion · weight ${activeSurfaceCompletionWeight().toFixed(2)}`
    : "not ranked";
  renderConstraintLedger(null);
}

function nucleusInterfaceForCandidate(candidate, evaluation) {
  const parent = placedClusters.find((placement) => placement.id === candidate.parentId);
  const parentNucleus = parent?.nucleusId || 1;
  const otherNuclei = new Set();
  let crossNucleusContacts = 0;
  evaluation.merged.forEach(({ atom }) => (atom.nucleusIds || []).forEach((nucleusId) => {
    if (nucleusId === parentNucleus) return;
    otherNuclei.add(nucleusId);
    crossNucleusContacts++;
  }));
  return { parentNucleus, otherNuclei: [...otherNuclei].sort((a, b) => a - b),
    crossNucleusContacts, coalescenceCandidate: otherNuclei.size > 0,
    seedSelectionTargetUsed: false, interfacialEnergyInferred: false };
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
    affineLoadedGeometricStrain: evaluation.affineLoadedGeometricStrain,
    compositionBalance: evaluation.compositionBalance,
    formalChargeBalance: evaluation.formalChargeBalance,
    surfaceCompletion: evaluation.surfaceCompletion,
    frontMorphology: evaluation.frontMorphology,
    epitaxyRegistry: evaluation.epitaxyRegistry,
    externalDrive: evaluation.externalDrive,
    constraintRobustness: evaluation.constraintRobustness,
    microstructureCoupling: evaluation.microstructureCoupling,
    loopClosure: evaluation.loopClosure,
    arrivalPath: evaluation.arrivalPath,
    nucleusInterface: nucleusInterfaceForCandidate(candidate, evaluation),
    geometricExploration: {
      dimensionlessScale: geometricExplorationScale,
      seed: growthPathSeed,
      offset: candidate.explorationOffset || 0,
    },
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
    nucleusId: parent?.nucleusId || 1,
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
    atom.nucleusIds ||= [];
    if (!atom.nucleusIds.includes(placement.nucleusId)) {
      atom.nucleusIds.push(placement.nucleusId);
      atom.interfaceContact = true;
      crossNucleusMergeContacts++;
    }
    placement.atomIds.push(atom.id);
  });
  const touchesOtherNucleus = evaluation.merged.some(({ atom }) => atom.nucleusIds?.some((id) => id !== placement.nucleusId));
  if (touchesOtherNucleus) coalescenceEvents++;
  evaluation.fresh.forEach((site) => {
    const atom = addAtom(site.p, site.species, `C${candidate.type + 1}`, nearestParent(site.p));
    if (Number.isInteger(site.referenceIndex)) atom.referenceIndex = site.referenceIndex;
    atom.clusterIds = [placement.id];
    atom.nucleusIds = [placement.nucleusId];
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
  const before = { atoms: atoms.length, clusters: placedClusters.length, frontier: frontierCandidates.length };
  const batch = commutingFrontierBatch();
  if (!batch.length) {
    recordStructuralLeap({ status: "fixed", label: "no geometrically admissible successor",
      before, proposal: { candidates: 0, sites: 0, shared: 0, fresh: 0 },
      tests: { summary: "finite frontier exhausted", detail: "Every frozen port is consumed, unsupported, conflicting, or outside the public domain." },
      after: { atoms: atoms.length, clusters: placedClusters.length, accepted: 0, rejected: 0,
        depth: Math.max(0, ...placedClusters.map((placement) => placement.depth || 0)) },
      claimBoundary: "This is a certified finite structural fixed point. It is not equilibrium, a stopping time, or evidence that a physical interface cannot advance by an unmodeled mechanism." });
    pauseGrowth("Frontier exhausted: no learned overlap rule remains geometrically admissible.");
    return;
  }
  const selectedKeys = new Set(batch.map(({ candidate }) => candidate.key));
  frontierCandidates = frontierCandidates.filter((candidate) => !selectedKeys.has(candidate.key));
  batch.filter(({ evaluation }) => !evaluation.accepted).forEach(({ candidate }) => rejectedCandidateKeys.add(candidate.key));
  currentCandidates = batch.map(({ candidate, evaluation }) => ({
    p: candidate.position.clone(), accepted: evaluation.accepted,
    rotation: candidate.rotation.clone(), type: candidate.type,
    arrivalAxis: evaluation.arrivalPath.axis,
    arrivalSweepDistance: evaluation.arrivalPath.sweepDistanceSceneUnits,
    frontMorphology: evaluation.frontMorphology,
  }));
  const mechanismDiagnostics = new Map(batch.map(({ candidate, evaluation }) =>
    [candidate, prepareGrowthMechanismDiagnostic(candidate, evaluation)]));
  let acceptedInBatch = 0;
  let rejectedInBatch = 0;
  let freshInBatch = 0;
  let sharedInBatch = 0;
  let proposedSitesInBatch = 0;
  let lastDecision = null;
  batch.forEach(({ candidate, evaluation: snapshotEvaluation }) => {
    let evaluation = snapshotEvaluation;
    let state = stateForCandidate(candidate, evaluation);
    if (!snapshotEvaluation.accepted) {
      proposedSitesInBatch += snapshotEvaluation.sites.length;
      sharedInBatch += snapshotEvaluation.merged.length;
      rejectedDecisions++;
      if (snapshotEvaluation.coordinationOverflows?.length) coordinationCapacityPrunes++;
      if (snapshotEvaluation.angularViolations?.length) angularEnvelopePrunes++;
      rejectedGeometricStrain += effectiveGeometricStrain(snapshotEvaluation).total;
      rejectedUnloadedGeometricStrain += snapshotEvaluation.geometricStrain.total;
      rejectedCompositionDelta += snapshotEvaluation.compositionBalance.scaledDelta;
      rejectedFormalChargeDelta += snapshotEvaluation.formalChargeBalance.scaledDelta;
      rejectedSurfaceDeficit += snapshotEvaluation.surfaceCompletion.scaledDelta;
      rejectedFrontMorphologyScore += snapshotEvaluation.frontMorphology.score;
      rejectedEpitaxyRegistryScore += snapshotEvaluation.epitaxyRegistry.score;
      rejectedExternalDriveAlignment += snapshotEvaluation.externalDrive.alignment;
      rejectedRobustnessScore += snapshotEvaluation.constraintRobustness.score;
      rejectedMicrostructureCouplingScore += snapshotEvaluation.microstructureCoupling.score;
      rejectedLoopClosureScore += snapshotEvaluation.loopClosure.score;
      rejectedIndependentLoopWitnesses += snapshotEvaluation.loopClosure.independentCompatiblePaths;
      rejectedArrivalPathScore += snapshotEvaluation.arrivalPath.score;
      rejectedBlockedPathSamples += snapshotEvaluation.arrivalPath.blockedSiteSamples;
      arrivalPathSiteSamples += snapshotEvaluation.arrivalPath.siteSamples;
      arrivalPathNeighborhoodChecks += snapshotEvaluation.arrivalPath.neighborhoodChecks;
      rejectedExplorationOffset += candidate.explorationOffset || 0;
      rejectedInBatch++;
      appendHistory("reject", { type: "reject", depth: placedClusters.find((placement) => placement.id === candidate.parentId)?.depth || 0,
        action: state.action, family: evaluation.reason });
      recordGrowthMechanismEvent(candidate, snapshotEvaluation, false,
        placedClusters.find((placement) => placement.id === candidate.parentId)?.depth || 0,
        mechanismDiagnostics.get(candidate));
      lastDecision = { eventType: "reject", accepted: false, state, resolver: "geometric + section prune",
        energy: candidate.markingScore, interval: [candidate.markingScore, candidate.markingScore] };
      return;
    }
    // Re-evaluate against earlier members of this same batch. The batch builder
    // guarantees that this remains admissible in every permutation; this pass
    // converts any coincident same-species fresh sites into shared sites.
    evaluation = evaluateCandidate(candidate);
    state = stateForCandidate(candidate, evaluation);
    proposedSitesInBatch += evaluation.sites.length;
    sharedInBatch += evaluation.merged.length;
    if (!evaluation.accepted) throw new Error("Commuting frontier batch lost permutation invariance");
    const decision = cacheDecision(state, candidate.markingScore);
    const parentDepth = placedClusters.find((placement) => placement.id === candidate.parentId)?.depth || 0;
    recordGrowthMechanismEvent(candidate, evaluation, true, parentDepth + 1,
      mechanismDiagnostics.get(candidate));
    const placement = materializeCandidate(candidate, evaluation);
    acceptedDecisions++;
    acceptedGeometricStrain += effectiveGeometricStrain(evaluation).total;
    acceptedUnloadedGeometricStrain += evaluation.geometricStrain.total;
    acceptedCompositionDelta += evaluation.compositionBalance.scaledDelta;
    acceptedFormalChargeDelta += evaluation.formalChargeBalance.scaledDelta;
    acceptedSurfaceDeficit += evaluation.surfaceCompletion.scaledDelta;
    acceptedFrontMorphologyScore += evaluation.frontMorphology.score;
    acceptedEpitaxyRegistryScore += evaluation.epitaxyRegistry.score;
    acceptedExternalDriveAlignment += evaluation.externalDrive.alignment;
    acceptedRobustnessScore += evaluation.constraintRobustness.score;
    acceptedMicrostructureCouplingScore += evaluation.microstructureCoupling.score;
    acceptedLoopClosureScore += evaluation.loopClosure.score;
    acceptedIndependentLoopWitnesses += evaluation.loopClosure.independentCompatiblePaths;
    acceptedArrivalPathScore += evaluation.arrivalPath.score;
    acceptedBlockedPathSamples += evaluation.arrivalPath.blockedSiteSamples;
    arrivalPathSiteSamples += evaluation.arrivalPath.siteSamples;
    arrivalPathNeighborhoodChecks += evaluation.arrivalPath.neighborhoodChecks;
    acceptedExplorationOffset += candidate.explorationOffset || 0;
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
  recordStructuralLeap({ status: acceptedInBatch ? "accepted" : "rejected",
    label: growthScheduling === "commuting"
      ? `${batch.length} pairwise-commuting whole-cluster actions` : `${batch.length} best-first whole-cluster action`,
    before,
    proposal: { candidates: batch.length, sites: proposedSitesInBatch, shared: sharedInBatch,
      fresh: freshInBatch + batch.filter(({ evaluation }) => !evaluation.accepted)
        .reduce((sum, { evaluation }) => sum + evaluation.fresh.length, 0) },
    tests: { summary: `${acceptedInBatch} passed · ${rejectedInBatch} pruned`,
      detail: "Species/hard-core, overlap, novelty, public boundary, coordination, angle, and active marking were evaluated before any commit." },
    after: { atoms: atoms.length, clusters: placedClusters.length, accepted: acceptedInBatch, rejected: rejectedInBatch,
      depth: Math.max(0, ...placedClusters.map((placement) => placement.depth || 0)) },
    claimBoundary: "The accepted antichain is valid in every placement order and jumps directly to a certified structural state. No force trajectory, relaxation path, transition probability, or physical elapsed time was computed." });
  rebuildWorld();
  updateUI();
}

function performIceAnchorEvent() {
  const wave = iceAnchorTrace?.waves[iceAnchorWaveIndex];
  const before = { atoms: atoms.length, clusters: acceptedDecisions,
    frontier: wave?.candidateAnchors || 0 };
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
    captionAction.textContent = `Safe fixed point after ${iceAnchorTrace.emittedAnchors.length} target-blind oxygen anchors. ${iceAnchorTrace.fixedPointReason} Unresolved ${iceAnchorTrace.orientationSpecies} poses are retained as alternatives, not drawn as simultaneous atoms.`;
    decisionBadge.className = "badge neutral";
    decisionBadge.textContent = "fixed point";
    decisionTitle.textContent = "Unsupported molecular continuation stops safely";
    decisionCopy.textContent = `The frozen ${iceAnchorTrace.portCount}-port grammar has no supported next anchor. This finite certificate is not a stationary or exponential ice-growth rule.`;
    actionValue.textContent = `wave ${wave.wave} · 0 accepted`;
    domainValue.textContent = `${wave.rejectedCandidateAnchors} unsupported or conflicting anchors pruned`;
    energyValue.textContent = "target calls 0";
    strainValue.textContent = "not used by frozen ice trace";
    compositionValue.textContent = "not used by frozen ice trace";
    chargeValue.textContent = "not used by frozen ice trace";
    surfaceValue.textContent = "not used by frozen ice trace";
    resolverValue.textContent = iceAnchorTrace.selectionRuleLabel;
    appendHistory("reject", { type: "reject", depth: wave.wave,
      action: "safe fixed point", family: "no unanimous parent domain" });
    recordStructuralLeap({ status: "fixed", label: `wave ${wave.wave} · molecular anchor frontier`,
      before, proposal: { candidates: wave.candidateAnchors, sites: wave.candidateAnchors, shared: 0, fresh: 0 },
      tests: { summary: `0 / ${wave.candidateAnchors} anchors admitted`,
        detail: `${wave.rejectedCandidateAnchors} unsupported or conflicting candidates fail ${iceAnchorTrace.selectionRuleLabel}.` },
      after: { atoms: atoms.length, clusters: acceptedDecisions, accepted: 0,
        rejected: wave.rejectedCandidateAnchors, depth: wave.wave },
      claimBoundary: `The frozen ${iceAnchorTrace.portCount}-port grammar reaches a finite structural fixed point. Unresolved ${iceAnchorTrace.orientationSpecies} motion, proton/deuteron barriers, entropy, and physical stopping time are not modeled.` });
    growthStopReason = "Frozen molecular-port grammar reached its certified finite fixed point.";
    setPlaying(false);
    pipelineAuto = false;
    updatePipelineButtons();
    rebuildWorld();
    updateUI();
    captionAction.textContent = `Safe fixed point after ${iceAnchorTrace.emittedAnchors.length} target-blind oxygen anchors. ${iceAnchorTrace.fixedPointReason} Unresolved ${iceAnchorTrace.orientationSpecies} poses are retained as alternatives, not drawn as simultaneous atoms.`;
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
    family: `${wave.retainedOrientationHypotheses} mutually exclusive ${iceAnchorTrace.moleculeLabel} poses retained` });
  captionAction.textContent = `Wave ${wave.wave}: ${wave.acceptedAnchors}/${wave.candidateAnchors} anchor candidates survive frozen proper-SE(3) ports and ${iceAnchorTrace.selectionRuleLabel}. ${wave.retainedOrientationHypotheses} mutually exclusive ${iceAnchorTrace.moleculeLabel} orientation hypotheses remain symbolic; only their shared O atoms are displayed.`;
  updateDecision({ eventType: "reuse", accepted: true,
    state: { action: `${wave.acceptedAnchors} O-anchor placements`,
      domain: `${iceAnchorTrace.portCount} frozen molecular ports · wave ${wave.wave}` },
    resolver: iceAnchorTrace.selectionRuleLabel, interval: [1, 1] });
  recordStructuralLeap({ status: "accepted", label: `wave ${wave.wave} · shared oxygen-anchor leap`,
    before, proposal: { candidates: wave.candidateAnchors, sites: wave.candidateAnchors,
      shared: wave.retainedOrientationHypotheses, fresh: wave.acceptedAnchors },
    tests: { summary: `${wave.acceptedAnchors} / ${wave.candidateAnchors} anchors admitted`,
      detail: `${iceAnchorTrace.portCount} frozen proper-SE(3) ports + ${iceAnchorTrace.selectionRuleLabel}; ${wave.retainedOrientationHypotheses} mutually exclusive ${iceAnchorTrace.moleculeLabel} poses retained.` },
    after: { atoms: atoms.length, clusters: acceptedDecisions, accepted: wave.acceptedAnchors,
      rejected: wave.rejectedCandidateAnchors, depth: wave.wave },
    claimBoundary: `The browser jumps to oxygen anchors shared by every surviving ${iceAnchorTrace.moleculeLabel} orientation domain. It does not integrate ${iceAnchorTrace.orientationSpecies} rearrangement, tunnelling, diffusion, relaxation, probability, or elapsed physical time.` });
  rebuildWorld();
  updateUI();
}

function advanceMarkingTraining(batchSize = 12) {
  trainingProgress = Math.min(markingSampleCount(), trainingProgress + batchSize);
  eventIndex = trainingProgress;
  updateClusterGalleryTrainingReadouts();
  buildClusterOverlay();
  rebuildWorld();
  updateUI();
}

function advanceClusterDiscovery(batchSize = 3) {
  if (!clusterDiscoveryTrace) return;
  clusterDiscoveryProgress = Math.min(
    clusterDiscoveryTrace.totalSteps, clusterDiscoveryProgress + batchSize);
  eventIndex = clusterDiscoveryProgress;
  buildClusterOverlay();
  rebuildWorld();
  updateUI();
}

function processTimelineRecord() {
  if (pipelineStage === 1 && clusterDiscoveryTrace) {
    const state = clusterDiscoveryState();
    const total = clusterDiscoveryTrace.totalSteps;
    return {
      stage: "cluster-identification",
      title: "Connection decisions",
      eyebrow: "process microscope · full 3D scene",
      progress: clusterDiscoveryProgress,
      total,
      state: `${clusterDiscoveryProgress} / ${total} · ${state.tentative.length} testing · ${state.rejected.length} removing · ${state.settled.length} settled`,
      note: clusterDiscoveryProgress >= total
        ? "The complete overlapping cluster-and-gap cover is frozen. Drag backward to audit how competing connections were removed."
        : "Drag to inspect tentative, rejected, and settled atom connections; Play resumes discovery from this exact decision step.",
      reversible: true,
      traceFrozen: true,
      targetUsed: false,
      evidence: processTimelineEvidenceRecord(),
    };
  }
  if (pipelineStage === 3 && sectionModel) {
    const point = currentTrainingPoint();
    const total = markingSampleCount();
    return {
      stage: "gcts-learning",
      title: "Local marking fit",
      eyebrow: "process microscope · one 3D scene per cluster",
      progress: trainingProgress,
      total,
      state: `${trainingProgress} / ${total} samples · holdout ${point.validationLoss.toFixed(3)}`,
      note: trainingProgress >= total
        ? "The local connection sections are fully fitted. Drag backward to compare their random initial halos with intermediate learned level sets."
        : "Drag to morph every cluster's local level sets through the fit; Play resumes from the selected sample count.",
      reversible: true,
      traceFrozen: true,
      targetUsed: false,
      evidence: processTimelineEvidenceRecord(),
    };
  }
  return null;
}

function processTimelineEvidenceRecord() {
  if (pipelineStage === 1 && clusterDiscoveryTrace) {
    const progress = clusterDiscoveryProgress;
    const current = clusterDiscoveryState(progress);
    const previous = clusterDiscoveryState(Math.max(0, progress - 1));
    const born = clusterDiscoveryTrace.edges.filter((edge) => edge.birthStep === progress);
    const accepted = clusterDiscoveryTrace.edges.filter((edge) => edge.final && edge.decisionStep === progress);
    const removed = clusterDiscoveryTrace.edges.filter((edge) => !edge.final && edge.decisionStep === progress);
    const placements = clusterDiscoveryTrace.placements.filter((placement) => placement.settleStep === progress);
    const newCoverage = [...current.coveredAtoms].filter((index) => !previous.coveredAtoms.has(index)).length;
    const acceptedFamilies = Object.entries(accepted.reduce((counts, edge) => {
      counts[edge.family] = (counts[edge.family] || 0) + 1;
      return counts;
    }, {})).sort((first, second) => second[1] - first[1] || first[0].localeCompare(second[0]));
    const representative = accepted[0] || removed[0] || born[0] || null;
    const pair = representative
      ? `${referenceAtoms[representative.first].species}–${referenceAtoms[representative.second].species} · ${(representative.length / Math.max(1e-9, referenceSpacing)).toFixed(2)}a`
      : "no edge transition at this step";
    return {
      mode: "deterministic audit replay of the learned cover",
      selectedStep: progress,
      targetUsed: false,
      coordinatesEmbedded: false,
      tiles: [
        { label: "new hypotheses", value: born.length, status: "testing",
          detail: `${born.length} distance-admissible pair connections enter the visual audit queue at this step.` },
        { label: "accepted / removed", value: `${accepted.length} / ${removed.length}`, status: removed.length ? "mixed" : "accepted",
          detail: `${accepted.length} edges belong to the final recurring cluster-and-gap cover; ${removed.length} short alternatives do not.` },
        { label: "cover gain", value: `+${newCoverage} sites`, status: newCoverage ? "accepted" : "neutral",
          detail: `${placements.length} complete support placement${placements.length === 1 ? "" : "s"} settle, newly certifying ${newCoverage} observed site${newCoverage === 1 ? "" : "s"}.` },
        { label: "representative", value: pair, status: representative?.final ? "accepted" : representative ? "rejected" : "neutral",
          detail: representative
            ? `${pair}. ${representative.final ? `Retained as ${representative.family}; accepted family counts are ${acceptedFamilies.map(([family, count]) => `${family} ${count}`).join(", ") || "none at this exact step"}.` : "Removed because it is absent from every selected recurring support or explicit gap class."}`
            : "No edge is born or decided at this exact audit step; neighboring steps still update complete support placements." },
      ],
      claimBoundary: "The learner computed the recurring isometry cover before this visualization. Step order is a deterministic audit replay, not molecular dynamics, an online clustering optimizer, or physical time.",
    };
  }
  if (pipelineStage === 3 && sectionModel) {
    const progress = trainingProgress;
    const point = currentSectionPoint();
    const previous = progress > 1 ? sectionModel.curve[progress - 2] : sectionModel.initialPoint;
    const sampleIndex = progress - 1;
    const cluster = sampleIndex >= 0 ? sectionModel.sampleLabels[sampleIndex] : null;
    const target = cluster === null ? [] : sectionModel.targets[sampleIndex] || [];
    const coefficientDelta = cluster === null ? 0 : Math.sqrt(point.coefficients[cluster].reduce((sum, value, axis) =>
      sum + (value - previous.coefficients[cluster][axis]) ** 2, 0));
    const fitSample = point.fitSamples > previous.fitSamples;
    const overlapGain = (point.overlaps || 0) - (previous.overlaps || 0);
    const lossDelta = point.validationLoss - previous.validationLoss;
    const positiveChannels = target.filter((value) => value > 0).length;
    return {
      mode: "deterministic sample-indexed section fit",
      selectedStep: progress,
      targetUsed: false,
      coordinatesEmbedded: false,
      tiles: [
        { label: "sample role", value: progress ? (fitSample ? "fit" : "held out") : "initial", status: fitSample ? "accepted" : "neutral",
          detail: progress ? `Sample ${progress} is a ${fitSample ? "fitting" : "held-out validation"} ${sectionModel.sampleKind}; held-out samples never update coefficients.` : "Deterministic random local-section coefficients before any occurrence is processed." },
        { label: "cluster section", value: cluster === null ? "unassigned" : markingPrototypeName(cluster), status: "testing",
          detail: cluster === null ? "No cluster occurrence has been processed yet." : `${markingPrototypeName(cluster)} receives this local connection observation; ${positiveChannels}/${sectionModel.channels} active channel directions carry compatible-port evidence.` },
        { label: "coefficient step", value: coefficientDelta.toFixed(4), status: coefficientDelta ? "accepted" : "neutral",
          detail: `Coordinate-free L2 change of the selected cluster's local section coefficients. Neighborhood reach is ${sectionModel.reach} and the representation is ${MARKING_REPRESENTATIONS[sectionModel.representation].short}.` },
        { label: "holdout change", value: `${lossDelta >= 0 ? "+" : ""}${lossDelta.toFixed(4)}`, status: lossDelta <= 0 ? "accepted" : "rejected",
          detail: `Held-out mismatch changes by ${lossDelta.toFixed(4)} at this sample; ${overlapGain >= 0 ? "+" : ""}${overlapGain} support-overlap constraints become visible.` },
      ],
      claimBoundary: "These are local connection-section fitting diagnostics. They are not forces, energies, potentials, relaxation steps, elapsed physical time, or target-guided growth scores.",
    };
  }
  return null;
}

function renderProcessEvidence() {
  const evidence = processTimelineEvidenceRecord();
  processEvidenceLedger.replaceChildren();
  processEvidenceDetail.textContent = "";
  if (!evidence) return;
  selectedProcessEvidenceIndex = Math.min(selectedProcessEvidenceIndex, evidence.tiles.length - 1);
  evidence.tiles.forEach((tile, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `${tile.status}${index === selectedProcessEvidenceIndex ? " active" : ""}`;
    button.setAttribute("aria-pressed", index === selectedProcessEvidenceIndex ? "true" : "false");
    const label = document.createElement("small"); label.textContent = tile.label;
    const value = document.createElement("strong"); value.textContent = tile.value;
    button.append(label, value);
    button.addEventListener("click", () => { selectedProcessEvidenceIndex = index; renderProcessEvidence(); });
    processEvidenceLedger.appendChild(button);
  });
  const selected = evidence.tiles[selectedProcessEvidenceIndex];
  processEvidenceDetail.textContent = `${selected.detail} Claim boundary: ${evidence.claimBoundary}`;
}

function updateProcessTimeline() {
  const record = processTimelineRecord();
  processTimeline.hidden = !record;
  if (!record) return;
  processTimelineEyebrow.textContent = record.eyebrow;
  processTimelineTitle.textContent = record.title;
  processTimelineState.textContent = record.state;
  processTimelineNote.textContent = record.note;
  processTimelineInput.max = String(Math.max(1, record.total));
  processTimelineInput.value = String(record.progress);
  processTimelineInput.setAttribute("aria-valuetext", record.state);
  processTimeline.style.setProperty("--process-progress", `${100 * record.progress / Math.max(1, record.total)}%`);
  renderProcessEvidence();
}

function scrubProcessTimeline(value) {
  const record = processTimelineRecord();
  if (!record) return;
  setPlaying(false);
  const progress = Math.max(0, Math.min(record.total, Math.round(Number(value) || 0)));
  selectedProcessEvidenceIndex = 0;
  if (pipelineStage === 1) clusterDiscoveryProgress = progress;
  else if (pipelineStage === 3) trainingProgress = progress;
  eventIndex = progress;
  buildClusterOverlay();
  if (pipelineStage === 3) updateClusterGalleryTrainingReadouts();
  rebuildWorld();
  updateUI();
}

function performEvent() {
  if (pipelineStage === 1) {
    if (clusterDiscoveryProgress < clusterDiscoveryTrace.totalSteps) advanceClusterDiscovery();
    else enterPipelineStage(nextVisiblePipelineStage(pipelineStage), { play: pipelineAuto });
    return;
  }
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
  clearGroup(externalDriveGroup);
  clearGroup(unitCellGroup);
  clearGroup(bondGroup);
  clearGroup(interfaceGroup);
  clearGroup(frontierGroup);
  clearGroup(decisionGroup);
  if (pipelineStage === 4 && externalDriveMode !== "none") {
    const origin = placedClusters[0]?.position?.clone() || new THREE.Vector3();
    const extent = Math.max(4.5, ...atoms.map((atom) => atom.p.distanceTo(origin))) * .9;
    const addArrow = (start, direction, length) => {
      const unit = direction.clone().normalize();
      const end = start.clone().addScaledVector(unit, length);
      externalDriveGroup.add(new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([start, end]),
        new THREE.LineBasicMaterial({ color: 0xf0c96a, transparent: true, opacity: .62 }),
      ));
      const head = new THREE.Mesh(new THREE.ConeGeometry(.18, .58, 10),
        new THREE.MeshBasicMaterial({ color: 0xf0c96a, transparent: true, opacity: .72 }));
      head.position.copy(end);
      head.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), unit);
      externalDriveGroup.add(head);
    };
    if (externalDriveMode === "z-plus" || externalDriveMode === "z-minus") {
      const direction = new THREE.Vector3(0, 0, externalDriveMode === "z-plus" ? 1 : -1);
      addArrow(origin.clone().addScaledVector(direction, -extent * .55), direction, extent * 1.1);
    } else {
      const inward = externalDriveMode === "radial-in";
      [new THREE.Vector3(1, 0, 0), new THREE.Vector3(-1, 0, 0), new THREE.Vector3(0, 1, 0),
        new THREE.Vector3(0, -1, 0), new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, 0, -1)]
        .forEach((axis) => addArrow(origin.clone().addScaledVector(axis, inward ? extent : extent * .22),
          axis.clone().multiplyScalar(inward ? -1 : 1), extent * .48));
    }
  }
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

  const selectedPair = growthNucleusPairs().find((pair) => pair.key === selectedNucleusPairKey);
  if (pipelineStage === 4 && selectedPair) {
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints([
      selectedPair.first.position, selectedPair.second.position,
    ]), new THREE.LineDashedMaterial({ color: 0x7ee1e8, dashSize: .22, gapSize: .13,
      transparent: true, opacity: .55 }));
    line.computeLineDistances();
    interfaceGroup.add(line);
  }
  const interfaceSites = atoms.filter((atom) => selectedPair
    ? atom.nucleusIds?.includes(selectedPair.first.nucleusId) && atom.nucleusIds.includes(selectedPair.second.nucleusId)
    : atom.interfaceContact || (atom.nucleusIds?.length || 0) > 1);
  if (pipelineStage === 4 && interfaceSites.length) {
    const rings = new THREE.InstancedMesh(occupancyRingGeometry, interfaceRingMaterial, interfaceSites.length);
    interfaceSites.forEach((atom, index) => {
      dummy.position.copy(atom.p);
      dummy.rotation.set(Math.PI / 2 * (index % 2), Math.PI / 3 * (index % 3), 0);
      dummy.scale.setScalar(elementScale(atom.species) * 1.32);
      dummy.updateMatrix();
      rings.setMatrixAt(index, dummy.matrix);
    });
    dummy.rotation.set(0, 0, 0);
    rings.instanceMatrix.needsUpdate = true;
    atomGroup.add(rings);
  }

  const occupationalGroups = new Map();
  atoms.forEach((atom) => {
    const descriptor = occupancyRingDescriptor(atom);
    if (!descriptor) return;
    const group = occupationalGroups.get(descriptor.key) || { descriptor, atoms: [] };
    group.atoms.push(atom);
    occupationalGroups.set(descriptor.key, group);
  });
  occupationalGroups.forEach(({ descriptor, atoms: sites }) => {
    const rings = new THREE.InstancedMesh(occupancyRingGeometry, occupancyRingMaterial(descriptor), sites.length);
    sites.forEach((atom, index) => {
      dummy.position.copy(atom.p);
      dummy.rotation.set(Math.PI / 2 * (index % 2), Math.PI / 4 * (index % 4), 0);
      dummy.scale.setScalar(elementScale(atom.species));
      dummy.updateMatrix();
      rings.setMatrixAt(index, dummy.matrix);
    });
    dummy.rotation.set(0, 0, 0);
    rings.instanceMatrix.needsUpdate = true;
    atomGroup.add(rings);
  });
  const thermalSites = atoms.filter((atom) => Number.isFinite(atom.thermalSigmaA) && atom.thermalSigmaA > 0);
  if (thermalSites.length) {
    const envelopes = new THREE.InstancedMesh(sphereGeometry, thermalEnvelopeMaterial, thermalSites.length);
    thermalSites.forEach((atom, index) => {
      dummy.position.copy(atom.p);
      const atomRadius = sphereGeometry.parameters.radius * elementScale(atom.species);
      const sigmaAxes = atom.thermalSigmaAxesA || [atom.thermalSigmaA, atom.thermalSigmaA, atom.thermalSigmaA];
      const axes = atom.thermalAxesCartesian || [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
      dummy.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(
        new THREE.Vector3(...axes[0]), new THREE.Vector3(...axes[1]), new THREE.Vector3(...axes[2])));
      const scaleAxes = sigmaAxes.map((sigma) => (atomRadius * 1.04
        + 2 * sigma * referenceSpacing / referenceSpacingA) / sphereGeometry.parameters.radius);
      dummy.scale.set(...scaleAxes);
      dummy.updateMatrix();
      envelopes.setMatrixAt(index, dummy.matrix);
    });
    dummy.rotation.set(0, 0, 0);
    envelopes.instanceMatrix.needsUpdate = true;
    atomGroup.add(envelopes);
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
    if (!selectedCoordination && pipelineStage < 4 && pipelineStage !== 3
        && pipelineStage !== 1 && atoms.length <= 250) {
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

  currentCandidates.forEach((candidate, candidateIndex) => {
    const mesh = new THREE.Mesh(candidateGeometry, candidate.accepted ? candidateMaterial : rejectedMaterial);
    mesh.position.copy(candidate.p);
    if (candidate.rotation) mesh.quaternion.copy(candidate.rotation);
    decisionGroup.add(mesh);
    if (candidateIndex < 12 && candidate.arrivalAxis && candidate.arrivalSweepDistance > 0) {
      const axis = new THREE.Vector3(...candidate.arrivalAxis).normalize();
      const start = candidate.p.clone().addScaledVector(axis, candidate.arrivalSweepDistance);
      const path = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([start, candidate.p]),
        new THREE.LineDashedMaterial({ color: 0xffc169, dashSize: .16, gapSize: .09,
          transparent: true, opacity: .72 }),
      );
      path.computeLineDistances();
      decisionGroup.add(path);
      const head = new THREE.Mesh(new THREE.ConeGeometry(.11, .32, 8),
        new THREE.MeshBasicMaterial({ color: 0xffc169, transparent: true, opacity: .78 }));
      head.position.copy(candidate.p);
      head.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), axis.clone().negate());
      decisionGroup.add(head);
    }
    if (candidateIndex < 12 && frontMorphologyMode !== "none" && candidate.frontMorphology) {
      const tangentX = new THREE.Vector3(...candidate.frontMorphology.tangentX);
      const tangentY = new THREE.Vector3(...candidate.frontMorphology.tangentY);
      const normal = new THREE.Vector3(...candidate.frontMorphology.normal);
      const sectorPoints = [];
      candidate.frontMorphology.occupiedSectors.forEach((sector) => {
        const angle = (sector + .5) / 8 * 2 * Math.PI;
        const radial = tangentX.clone().multiplyScalar(Math.cos(angle)).addScaledVector(tangentY, Math.sin(angle));
        sectorPoints.push(candidate.p.clone().addScaledVector(radial, .30), candidate.p.clone().addScaledVector(radial, .48));
      });
      if (sectorPoints.length) decisionGroup.add(new THREE.LineSegments(
        new THREE.BufferGeometry().setFromPoints(sectorPoints),
        new THREE.LineBasicMaterial({ color: 0x65e1bc, transparent: true, opacity: .82 }),
      ));
      decisionGroup.add(new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          candidate.p.clone().addScaledVector(normal, -.34), candidate.p.clone().addScaledVector(normal, .46),
        ]),
        new THREE.LineBasicMaterial({ color: 0x65e1bc, transparent: true, opacity: .44 }),
      ));
    }
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

function physicsTranslationRecords(leap = null) {
  const activeMarking = selectedMarking();
  const markingMode = policySelect.value === "marked"
    ? activeMarking ? `${activeMarking.name} · ${MARKING_REPRESENTATIONS[activeMarking.config.representation].short}` : "current learned section"
    : policySelect.value === "direct" ? "exact-local diagnostic ceiling" : "unmarked action baseline";
  const chemistryTerms = [activeCompositionBalanceWeight() > 0 ? `composition w=${activeCompositionBalanceWeight().toFixed(2)}` : null,
    activeFormalChargeWeight() > 0 ? `formal charge w=${activeFormalChargeWeight().toFixed(2)}` : null].filter(Boolean);
  const leapResult = leap
    ? `${leap.tests.summary}; ${leap.after.accepted} accepted and ${leap.after.rejected} rejected in the displayed leap.`
    : "Awaiting the first frozen frontier evaluation.";
  return [
    { id: "steric", process: "short-range repulsion / species contact", status: "hard", role: "hard admission gate",
      encoding: `${coloredDistanceEnvelopes?.records?.length || 0} colored pair envelopes with exact species coincidence and learned hard-exclusion radii`,
      evidence: leapResult,
      boundary: "This excludes geometrically impossible contacts; it is not a repulsive pair potential, force, pressure, or collision trajectory." },
    { id: "local", process: "local bonding geometry / valence saturation", status: "hard", role: "hard causal neighborhood gate",
      encoding: `${coloredCoordinationEnvelopes?.records?.length || 0} ordered coordination bounds + ${coloredAngularEnvelopes?.records?.length || 0} colored angular bands within the sample-derived reach`,
      evidence: `${coordinationCapacityPrunes} coordination and ${angularEnvelopePrunes} angular prunes have occurred in this run.`,
      boundary: "Coordination and angle envelopes constrain local topology but do not calculate bond order, bond energy, hybridization, or electronic structure." },
    { id: "connection", process: "cluster attachment preference", status: policySelect.value === "action" ? "open" : "learned", role: policySelect.value === "action" ? "ablated" : "learned local connection gate / rank",
      encoding: `${markingMode}; ${sectionModel?.channels || 0} channels, reach ${sectionModel?.reach || 0}, transported in cluster-local proper-SE(3) frames`,
      evidence: leap ? `${leap.proposal.shared} shared and ${leap.proposal.fresh} proposed fresh sites were checked through the frozen port grammar.` : "No attachment scored yet.",
      boundary: "A GCTS marking represents compatibility of overlapping cluster sections. It is not an interatomic potential or a calibrated attachment free energy." },
    { id: "chemistry", process: "multicomponent reservoir / charge bookkeeping", status: chemistryTerms.length ? "soft" : "open", role: chemistryTerms.length ? "target-blind soft ordering" : "available but disabled",
      encoding: chemistryTerms.join(" + ") || "no composition or supplied-formal-charge ranking term is active",
      evidence: chemistryTerms.length ? `Reference reduced ratio ${compositionTarget?.reducedRatio || "unavailable"}; formal-charge coverage ${Math.round((formalChargeTarget?.coverage || 0) * 100)}%.` : "Candidate geometry is unchanged; this counterfactual policy contribution is zero.",
      boundary: "These finite-reservoir summaries are not chemical potentials, oxidation-state inference, Coulomb energy, electron transfer, or redox thermodynamics." },
    { id: "surface", process: "interface completion / undercoordination", status: activeSurfaceCompletionWeight() > 0 ? "soft" : "open", role: activeSurfaceCompletionWeight() > 0 ? "target-blind soft ordering" : "disabled",
      encoding: activeSurfaceCompletionWeight() > 0 ? `sample-derived colored coordination deficit, w=${activeSurfaceCompletionWeight().toFixed(2)}` : "no surface-completion ranking term is active",
      evidence: leap ? `${leap.before.frontier} frontier candidates before the leap; ${leap.after.atoms - leap.before.atoms} explicit atoms added.` : "No interface update yet.",
      boundary: "This favors closing local coordination deficits but does not relax a surface, calculate surface energy, reconstruct an interface, or model solvent/feedstock transport." },
    { id: "front-morphology", process: "capillarity / front-shape selection", status: activeFrontMorphologyWeight() > 0 ? "soft" : "open", role: activeFrontMorphologyWeight() > 0 ? "mesoscopic geometric ordering" : "diagnostic",
      encoding: `${frontMorphologyLabel()}; eight parent-local angular support sectors plus the normalized depth spread of atoms backing each candidate within 2.4dₙₙ`,
      evidence: leap ? `Accepted mean front score ${receiptRound(acceptedFrontMorphologyScore / Math.max(1, acceptedDecisions), 4)}; rejected mean ${receiptRound(rejectedFrontMorphologyScore / Math.max(1, rejectedDecisions), 4)}; ${frontMorphologyNeighborhoodChecks.toLocaleString()} neighbor checks.` : "No front candidate evaluated yet.",
      boundary: "This distinguishes concavity filling, coherent backing, and exposed tips geometrically. It is not mean curvature, surface energy, capillary pressure, a Wulff construction, attachment kinetics, or physical time." },
    { id: "epitaxy", process: "substrate templating / epitaxial registry", status: activeEpitaxyWeight() > 0 ? "soft" : "open", role: activeEpitaxyWeight() > 0 ? "declared interfacial geometric ordering" : "disabled",
      encoding: activeEpitaxyWeight() > 0
        ? `${epitaxyTemplateLabel()}, w=${activeEpitaxyWeight().toFixed(2)}; fresh sites within 3.5dₙₙ are projected onto the nearest declared 2D template node with height-decaying weight`
        : confinementSelect.value === "substrate" ? "inert impenetrable support plane; no registry template" : "no support-plane geometry is active",
      evidence: leap ? `Accepted mean registry score ${receiptRound(acceptedEpitaxyRegistryScore / Math.max(1, acceptedDecisions), 4)}; rejected mean ${receiptRound(rejectedEpitaxyRegistryScore / Math.max(1, rejectedDecisions), 4)}; ${epitaxyRegistrySiteChecks.toLocaleString()} fresh-site checks.` : "No interfacial action evaluated yet.",
      boundary: "The template is a user-declared uncolored 2D point set. It supplies no substrate atoms or chemistry and is not adhesion, interface energy, wetting, elastic relaxation, a misfit-dislocation model, or a growth rate." },
    { id: "affine", process: "prescribed mechanical boundary deformation", status: affineLoadMode === "none" ? "open" : "soft", role: affineLoadMode === "none" ? "disabled" : "target-blind deformed-metric ordering",
      encoding: affineLoadMode === "none"
        ? "identity deformation gradient; observed contact/angle metric"
        : `${Math.round(affineLoadMagnitude * 100)}% ${affineLoadModeLabel()} with F=${JSON.stringify(affineLoadTensor())}; exact coordinates and hard gates unchanged`,
      evidence: leap ? `Loaded accepted mean ${receiptRound(acceptedGeometricStrain / Math.max(1, acceptedDecisions), 4)} versus unloaded ${receiptRound(acceptedUnloadedGeometricStrain / Math.max(1, acceptedDecisions), 4)}.` : "No loaded attachment scored yet.",
      boundary: "This is a prescribed deformation gradient, not inferred stress, pressure, modulus, force, elastic relaxation, plasticity, phonons, or mechanical equilibrium." },
    { id: "drive", process: "externally imposed directional loading / feed geometry", status: activeExternalDriveWeight() > 0 ? "soft" : "open", role: activeExternalDriveWeight() > 0 ? "target-blind soft ordering" : "disabled",
      encoding: activeExternalDriveWeight() > 0
        ? `${externalDriveModeLabel()} parent→child alignment, w=${activeExternalDriveWeight().toFixed(2)}, over the unchanged frozen frontier`
        : "isotropic search; no preferred attachment direction",
      evidence: leap ? `Accepted mean alignment ${receiptRound(acceptedExternalDriveAlignment / Math.max(1, acceptedDecisions), 4)}; rejected mean ${receiptRound(rejectedExternalDriveAlignment / Math.max(1, rejectedDecisions), 4)}.` : "No directional attachment scored yet.",
      boundary: "This is a declared geometric boundary/loading condition. It does not solve a force, electric field, flux transport, stress propagation, or orientation-dependent attachment rate." },
    { id: "robustness", process: "finite geometric uncertainty / attachment tolerance", status: activeRobustnessWeight() > 0 ? "soft" : "open", role: activeRobustnessWeight() > 0 ? "target-blind constraint-margin ordering" : "diagnostic",
      encoding: `minimum of colored-contact clearance, exact-overlap headroom, and public-boundary clearance, normalized by ε=${clusterMetricToleranceAngstrom().toFixed(3)} Å`,
      evidence: leap ? `Accepted mean bounded score ${receiptRound(acceptedRobustnessScore / Math.max(1, acceptedDecisions), 4)}; rejected mean ${receiptRound(rejectedRobustnessScore / Math.max(1, rejectedDecisions), 4)}.` : "No attachment margin scored yet.",
      boundary: "This deterministic safety margin is not a perturbation ensemble, thermal fluctuation, survival probability, free energy, barrier, or rate." },
    { id: "microstructure", process: "defect/interface-conditioned growth hypothesis", status: activeMicrostructureCouplingWeight() > 0 ? "soft" : "open", role: activeMicrostructureCouplingWeight() > 0 ? "input-derived geometric coupling" : "diagnostic",
      encoding: activeMicrostructureCouplingWeight() > 0
        ? `${microstructureCouplingLabel()}, w=${activeMicrostructureCouplingWeight().toFixed(2)}, from frozen gap/residual, pose-interface, coordination, or occupational roles`
        : "heterogeneous-geometry roles are mapped but do not rank branches",
      evidence: leap ? `Accepted mean coupling score ${receiptRound(acceptedMicrostructureCouplingScore / Math.max(1, acceptedDecisions), 4)}; rejected mean ${receiptRound(rejectedMicrostructureCouplingScore / Math.max(1, rejectedDecisions), 4)}.` : "No microstructure-conditioned action scored yet.",
      boundary: "These roles are geometric hypotheses, not automatic vacancies, dislocations, grains, formation energies, mobilities, or physical mechanisms." },
    { id: "multi-nucleus", process: "multiple nuclei / impingement", status: initializedGrowthNuclei > 1 ? "explicit" : "open", role: initializedGrowthNuclei > 1 ? "observed-pose co-growth" : "single local seed",
      encoding: `${initializedGrowthNuclei || requestedGrowthNuclei} farthest-separated observed cluster occurrence${(initializedGrowthNuclei || requestedGrowthNuclei) === 1 ? "" : "s"}; lineage IDs propagate through unchanged frozen ports`,
      evidence: `${coalescenceEvents} coalescence action${coalescenceEvents === 1 ? "" : "s"} and ${crossNucleusMergeContacts} shared-site interface contact${crossNucleusMergeContacts === 1 ? "" : "s"} in the live state.`,
      boundary: "Observed seeds expose geometric impingement, not a nucleation rate, grain identity, interfacial energy, texture distribution, coarsening law, or elapsed time." },
    { id: "loop-closure", process: "mesoscopic elastic compatibility / seam avoidance", status: activeLoopClosureWeight() > 0 ? "soft" : "open", role: activeLoopClosureWeight() > 0 ? "multi-parent proper-SE(3) consensus" : "diagnostic",
      encoding: "independent placed parents apply frozen connection rules; complete transformed colored site sets are compared so proper-symmetry gauges cannot create false seams",
      evidence: leap ? `Accepted mean ${receiptRound(acceptedIndependentLoopWitnesses / Math.max(1, acceptedDecisions), 4)} independent compatible paths; rejected mean ${receiptRound(rejectedIndependentLoopWitnesses / Math.max(1, rejectedDecisions), 4)}.` : "No mesoscopic loop tested yet.",
      boundary: "Loop closure detects geometric consistency, not elastic energy, modulus, stress, force balance, dislocation energy, or mechanical relaxation." },
    { id: "kinetics", process: "activation, diffusion, heat flow, and elapsed time", status: activeArrivalPathWeight() > 0 ? "soft" : "open", role: activeArrivalPathWeight() > 0 ? "geometric accessibility proxy" : "not modeled",
      encoding: activeArrivalPathWeight() > 0
        ? `${arrivalPathLabel()}; 9 swept-clearance samples over 2dₙₙ for emitted sites only, w=${activeArrivalPathWeight().toFixed(2)}`
        : "none; the accepted whole-cluster antichain jumps directly between certified structural states",
      evidence: leap ? `${arrivalPathSiteSamples.toLocaleString()} site-path samples and ${arrivalPathNeighborhoodChecks.toLocaleString()} existing-neighbor checks; ${leap.after.atoms - leap.before.atoms} explicit sites emitted.` : "The seed has no physical clock.",
      boundary: "Swept clearance is not a minimum-energy path. No barrier, rate, pathway probability, thermostat, phonon transport, diffusion, hydrodynamics, relaxation trajectory, or physical duration is inferred." },
    { id: "path-ensemble", process: "configurational pathway multiplicity", status: geometricExplorationScale > 0 ? "sampled" : "open", role: geometricExplorationScale > 0 ? "reproducible exact-branch exploration" : "deterministic greedy ordering",
      encoding: geometricExplorationScale > 0
        ? `FNV-keyed Gumbel offsets at dimensionless T*=${geometricExplorationScale.toFixed(2)}, seed ${growthPathSeed}; candidate geometry and every hard gate are unchanged`
        : "T*=0; the highest exact combined score is selected deterministically",
      evidence: leap ? `Accepted mean ordering offset ${receiptRound(acceptedExplorationOffset / Math.max(1, acceptedDecisions), 4)}; rejected mean ${receiptRound(rejectedExplorationOffset / Math.max(1, rejectedDecisions), 4)}.` : "No branch order has been sampled yet.",
      boundary: "T* is not Kelvin temperature. These offsets are not energy, Boltzmann weights, equilibrium probabilities, free energy, kinetics, or physical time." },
    { id: "long-range", process: "long-range elasticity, electrostatics, and electronic response", status: "open", role: "outside the bounded local grammar",
      encoding: `local constraint reach is at most ${coloredCoordinationEnvelopes ? (coloredCoordinationEnvelopes.maximumCutoff * referenceSpacingA / referenceSpacing).toFixed(2) : "—"} Å; ${[affineLoadMode === "none" ? null : `${affineLoadModeLabel()} metric`, activeExternalDriveWeight() > 0 ? `${externalDriveModeLabel()} drive` : null].filter(Boolean).join(" + ") || "no external condition"} is imposed geometrically, but nonlocal material response is unsolved`,
      evidence: "The portal reports this omission instead of silently folding it into a local score.",
      boundary: "Collective strain, defects, polarization, screening, magnetism, excited states, and nonlocal charge redistribution require external physics or new geometric state variables." },
  ];
}

function renderLeapPhysics(leap = null) {
  const records = leap?.physicsTranslation || physicsTranslationRecords(leap);
  leapPhysicsMatrix.replaceChildren();
  if (!records.some((record) => record.id === selectedLeapPhysicsId)) selectedLeapPhysicsId = records[0]?.id || "steric";
  records.forEach((record) => {
    const button = document.createElement("button"); button.type = "button";
    button.className = `${record.status}${record.id === selectedLeapPhysicsId ? " active" : ""}`;
    button.setAttribute("aria-pressed", String(record.id === selectedLeapPhysicsId));
    const small = document.createElement("small"); small.textContent = record.role;
    const strong = document.createElement("strong"); strong.textContent = record.process;
    const span = document.createElement("span"); span.textContent = record.status;
    button.append(small, strong, span);
    button.addEventListener("click", () => { selectedLeapPhysicsId = record.id; renderLeapPhysics(leap); });
    leapPhysicsMatrix.append(button);
  });
  const selected = records.find((record) => record.id === selectedLeapPhysicsId) || records[0];
  leapPhysicsDetail.replaceChildren();
  if (!selected) return;
  const header = document.createElement("header");
  const small = document.createElement("small"); small.textContent = `${selected.status} · ${selected.role}`;
  const strong = document.createElement("strong"); strong.textContent = selected.process;
  header.append(small, strong); leapPhysicsDetail.append(header);
  [["geometric encoding", selected.encoding], ["this leap", selected.evidence], ["claim boundary", selected.boundary]].forEach(([label, copy]) => {
    const row = document.createElement("div"); const key = document.createElement("b"); const value = document.createElement("p");
    key.textContent = label; value.textContent = copy; row.append(key, value); leapPhysicsDetail.append(row);
  });
}

function renderStructuralLeap(leap = null) {
  if (!leapCertificateSection) return;
  leapCertificateSection.hidden = pipelineStage !== 4;
  if (pipelineStage !== 4) return;
  const selected = leap || leapHistory[selectedLeapIndex] || null;
  leapHistoryElement.replaceChildren();
  leapHistory.slice(-8).forEach((entry, visibleIndex) => {
    const absoluteIndex = Math.max(0, leapHistory.length - 8) + visibleIndex;
    const button = document.createElement("button"); button.type = "button";
    button.className = entry.status;
    button.classList.toggle("active", absoluteIndex === selectedLeapIndex);
    button.setAttribute("aria-pressed", String(absoluteIndex === selectedLeapIndex));
    button.textContent = `${entry.index} · ${entry.status === "accepted" ? "+" : entry.status === "fixed" ? "■" : "×"}${entry.after.atoms - entry.before.atoms}`;
    button.title = `${entry.label} · ${entry.status}`;
    button.addEventListener("click", () => {
      selectedLeapIndex = absoluteIndex;
      renderStructuralLeap(leapHistory[selectedLeapIndex]);
    });
    leapHistoryElement.append(button);
  });
  leapFlow.replaceChildren();
  renderLeapPhysics(selected);
  if (!selected) {
    leapCertificateState.textContent = "seed state · no leap executed";
    [
      ["01 · before", `${atoms.length} explicit atoms`, `${placedClusters.length} placed clusters`],
      ["02 · proposal", "frontier not sampled", `${frontierCandidates.length} frozen candidates`],
      ["03 · certificate", "not evaluated", "geometry gates await one action"],
      ["04 · after", "unchanged seed", "physical time unresolved"],
    ].forEach(([label, value, detail]) => {
      const card = document.createElement("article");
      const small = document.createElement("small"); small.textContent = label;
      const strong = document.createElement("strong"); strong.textContent = value;
      const span = document.createElement("span"); span.textContent = detail;
      card.append(small, strong, span); leapFlow.append(card);
    });
    leapClaimBoundary.textContent = "No trajectory is integrated. The seed geometry defines a search state, not a time origin or nucleation probability.";
    return;
  }
  leapCertificateState.textContent = `${selected.status} · leap ${selected.index}`;
  [
    ["01 · before", `${selected.before.atoms} atoms · ${selected.before.clusters} clusters`, `${selected.before.frontier} frozen frontier candidates`],
    ["02 · proposed leap", selected.label, `${selected.proposal.candidates} candidates · ${selected.proposal.sites} colored sites · ${selected.proposal.shared} shared + ${selected.proposal.fresh} new`],
    ["03 · geometric certificate", selected.tests.summary, selected.tests.detail],
    ["04 · after", `${selected.after.atoms} atoms · ${selected.after.clusters} clusters`, `${selected.after.accepted} accepted · ${selected.after.rejected} rejected · causal depth ${selected.after.depth}`],
  ].forEach(([label, value, detail], index) => {
    const card = document.createElement("article");
    if (index === 2) card.className = selected.status;
    const small = document.createElement("small"); small.textContent = label;
    const strong = document.createElement("strong"); strong.textContent = value;
    const span = document.createElement("span"); span.textContent = detail;
    card.append(small, strong, span); leapFlow.append(card);
  });
  leapClaimBoundary.textContent = selected.claimBoundary;
}

function recordStructuralLeap(leap) {
  const frozen = { ...leap, index: ++leapEventCount, targetUsed: false,
    physicalTimeModeled: false, dynamicsIntegrated: false };
  frozen.physicsTranslation = physicsTranslationRecords(frozen);
  leapHistory.push(frozen);
  if (leapHistory.length > 24) leapHistory.shift();
  selectedLeapIndex = leapHistory.length - 1;
  renderStructuralLeap(frozen);
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
  const strain = affineLoadMode === "none"
    ? event.state.geometricStrain : event.state.affineLoadedGeometricStrain;
  strainValue.textContent = strain
    ? `${strain.total.toFixed(3)} · r ${strain.distance.toFixed(3)} · θ ${strain.angle.toFixed(3)}${affineLoadMode === "none" ? "" : ` · ${affineLoadModeLabel()}`}`
    : "not evaluated";
  const balance = event.state.compositionBalance;
  compositionValue.textContent = balance
    ? `${balance.before.toFixed(3)} → ${balance.after.toFixed(3)} · Δ${balance.delta >= 0 ? "+" : ""}${balance.delta.toFixed(3)}`
    : "not evaluated";
  const charge = event.state.formalChargeBalance;
  chargeValue.textContent = charge?.available
    ? `${charge.before.toFixed(3)} → ${charge.after.toFixed(3)} · Δ${charge.delta >= 0 ? "+" : ""}${charge.delta.toFixed(3)} · q ${charge.projectedNetFormalCharge >= 0 ? "+" : ""}${charge.projectedNetFormalCharge.toFixed(2)}`
    : charge?.reason || "not evaluated";
  const surface = event.state.surfaceCompletion;
  surfaceValue.textContent = surface
    ? `new ${surface.newSiteDeficit.toFixed(3)} · healed ${surface.healedExisting.toFixed(3)} · Δ${surface.scaledDelta >= 0 ? "+" : ""}${surface.scaledDelta.toFixed(3)}`
    : "not evaluated";
  resolverValue.textContent = event.resolver;
  renderConstraintLedger(Number.isFinite(event.state.n15) ? event.state : null,
    Number.isFinite(event.state.n15) ? "configured" : "specialized");
  eventKind.textContent = reuse ? "MARK REUSE" : event.accepted ? "ACCEPT" : "REJECT";
}

function geometryConstraintEvidence(name, term, state, mode) {
  const frameCount = coloredDistanceEnvelopes?.frameCount || 1;
  const presentations = coloredDistanceEnvelopes?.atomPresentations || referenceCount();
  const pairRecords = coloredDistanceEnvelopes?.records || [];
  const coordinationRecords = coloredCoordinationEnvelopes?.records || [];
  const angularRecords = coloredAngularEnvelopes?.records || [];
  const totalAngles = angularRecords.reduce((sum, record) => sum + (record.angleObservations || 0), 0);
  const totalBands = angularRecords.reduce((sum, record) => sum + (record.bands?.length || 0), 0);
  const ratio = compositionTarget?.reducedRatio
    ? Object.entries(compositionTarget.reducedRatio).map(([symbol, count]) => `${symbol}:${count}`).join(" · ") : "unavailable";
  const environment = growthEnvironmentSpec(confinementSelect.value);
  const generic = {
    observed: `${presentations.toLocaleString()} species-labelled position presentations · ${frameCount} within-frame observation${frameCount === 1 ? "" : "s"}`,
    encoding: term.detail,
    searchRole: term.status === "pass" || term.status === "fail" ? "hard admission gate"
      : term.status === "ranked" ? "soft ordering of the unchanged exact candidate set" : "diagnostic only",
    boundary: "Geometric evidence only; no force, free energy, rate, or elapsed physical time is inferred.",
  };
  const evidence = {
    "species / hard core": {
      observed: `${pairRecords.length} colored pair envelopes from ${presentations.toLocaleString()} atom presentations`,
      encoding: "Species-preserving coincidence plus pair-specific minimum-distance exclusions learned below every supplied contact.",
      searchRole: "Hard gate: an unlike species coincidence or sub-exclusion contact rejects the whole placement.",
      boundary: "A contact exclusion is not a pair potential, bond order, repulsive energy, or electronic-structure calculation.",
    },
    "shared support": {
      observed: `${learnedCover?.placements?.length || 0} cover occurrences · ${(overlapGrammar?.observations || 0).toLocaleString()} witnessed directed relations`,
      encoding: "Exact colored shared sites and a proper-SE(3) relative pose, quotiented by learned proper cluster symmetries.",
      searchRole: "Hard gate: a frozen attachment must reproduce its required overlap or admitted boundary witness.",
      boundary: "Witnessed adjacency establishes structural compatibility, not binding energy or reaction favorability.",
    },
    "novel colored sites": {
      observed: `${learnedCover?.covered || 0}/${referenceCount()} input sites represented · ${learnedCover?.residualTypes?.length || 0} explicit residual types`,
      encoding: "Species-labelled set difference of a whole rigid cluster; shared sites are counted once and gaps remain literal.",
      searchRole: "Hard gate: an action must add at least one new colored site without silently dropping part of a cluster.",
      boundary: "Novel geometry is a continuation proposal, not proof that the site is thermodynamically occupied.",
    },
    "public boundary": {
      observed: `${environment.shortLabel} selected before search · ${currentPbc().some(Boolean) ? "periodic input quotient" : "finite input window"}`,
      encoding: `${environment.shape} containment evaluated before branch ranking.`,
      searchRole: "Hard gate: every emitted site must lie inside the declared public growth domain.",
      boundary: "The domain is an experimental/geometric condition, not an inferred surface energy or equilibrium crystal habit.",
    },
    "coordination capacity": {
      observed: `${coordinationRecords.length} ordered species channels · ${coordinationRecords.reduce((sum, record) => sum + (record.centerObservations || 0), 0).toLocaleString()} center observations`,
      encoding: "For each centre→neighbour species channel, the first-shell cutoff and maximum observed occupancy are frozen.",
      searchRole: "Hard causal gate: a proposal cannot oversaturate an already present local coordination channel.",
      boundary: "Observed coordination capacity is not valence theory, bond energy, charge transfer, or a guarantee of stability.",
    },
    "angular envelope": {
      observed: `${totalAngles.toLocaleString()} colored three-body angles · ${totalBands} separated angular bands`,
      encoding: "Neighbour–centre–neighbour angle support is stored as a union of observed bands rather than one spherical shell.",
      searchRole: "Hard causal gate: new bonds cannot force already present contact neighbours into an unsupported angular gap.",
      boundary: "These bands are not an angular potential, torque, vibrational mode, or finite-temperature distribution.",
    },
    "elastic proxy": {
      observed: `${pairRecords.length} contact scales + ${totalBands} angular bands from the supplied geometry`,
      encoding: affineLoadMode === "none"
        ? "Dimensionless distance and angle residuals measure deformation away from observed local envelopes."
        : `${Math.round(affineLoadMagnitude * 100)}% ${affineLoadModeLabel()} applies F=${JSON.stringify(affineLoadTensor())} to local displacement vectors before the same residual is evaluated.`,
      searchRole: activeGeometricStrainWeight() > 0
        ? `Soft rank term with weight ${activeGeometricStrainWeight().toFixed(2)}; it cannot authorize a failed hard gate.` : "Diagnostic only; weight zero.",
      boundary: "This is not elastic energy: the deformation gradient is prescribed, while no modulus, stress tensor, pressure, relaxation, plasticity, phonon, or force is calculated.",
    },
    "composition reservoir": {
      observed: `${ratio} reduced ratio from ${compositionTarget?.observations || referenceCount()} supplied sites`,
      encoding: "The running composition-distance change of each candidate is measured against the observed multicomponent ratio.",
      searchRole: activeCompositionBalanceWeight() > 0
        ? `Soft rank term with weight ${activeCompositionBalanceWeight().toFixed(2)}.` : "Diagnostic only; weight zero.",
      boundary: "Composition balancing is not a chemical potential, phase reservoir, reaction network, or charge-neutrality model.",
    },
    "formal-charge reservoir": {
      observed: formalChargeTarget?.available
        ? `${Math.round(formalChargeTarget.coverage * 100)}% supplied oxidation-state coverage · q̄ ${formalChargeTarget.meanFormalCharge.toFixed(3)}`
        : `${Math.round((formalChargeTarget?.coverage || 0) * 100)}% coverage · incomplete channel`,
      encoding: formalChargeTarget?.available
        ? "Candidate bookkeeping tracks drift from the supplied mean formal charge per site." : "No surrogate is fitted when oxidation states are not completely supplied.",
      searchRole: activeFormalChargeWeight() > 0
        ? `Soft rank term with weight ${activeFormalChargeWeight().toFixed(2)}.` : "Unavailable or diagnostic only.",
      boundary: "Formal labels are not charge density, electrostatics, redox chemistry, electron transfer, or dielectric screening.",
    },
    "surface completion": {
      observed: `${coordinationRecords.length} learned bulk coordination channels define local deficit relative to the sample`,
      encoding: "A candidate receives credit for healing existing coordination deficits and cost for creating new exposed deficits.",
      searchRole: activeSurfaceCompletionWeight() > 0
        ? `Soft rank term with weight ${activeSurfaceCompletionWeight().toFixed(2)}.` : "Diagnostic only; weight zero.",
      boundary: "Coordination deficit is not surface free energy, reconstruction, adsorption, solvent chemistry, or Wulff construction.",
    },
    "front morphology": {
      observed: `${state?.frontMorphology?.neighborhoodAtoms ?? 0} placed atoms within 2.4dₙₙ · ${state?.frontMorphology?.angularSectors ?? 0}/8 occupied parent-local angular sectors`,
      encoding: state?.frontMorphology
        ? `angular coverage ${state.frontMorphology.angularCoverage.toFixed(3)} · backing fraction ${state.frontMorphology.backingFraction.toFixed(3)} · plane coherence ${state.frontMorphology.planeCoherence.toFixed(3)}`
        : "parent-local angular support and normalized backing-depth spread",
      searchRole: activeFrontMorphologyWeight() > 0
        ? `Soft ${frontMorphologyLabel()} rank term with weight ${activeFrontMorphologyWeight().toFixed(2)}.` : "Diagnostic only; weight zero.",
      boundary: "This is a finite-neighborhood shape descriptor, not mean curvature, surface energy, capillary pressure, Wulff faceting, or attachment kinetics.",
    },
    "epitaxial registry": {
      observed: state?.epitaxyRegistry?.enabled
        ? `${state.epitaxyRegistry.interfacialSites}/${state.epitaxyRegistry.evaluatedFreshSites} new sites within 3.5dₙₙ of the declared support template`
        : confinementSelect.value === "substrate" ? "impenetrable support plane; registry disabled" : "no supported-film environment",
      encoding: state?.epitaxyRegistry?.enabled
        ? `${state.epitaxyRegistry.templateSymmetry} lattice · ${(state.epitaxyRegistry.mismatchFraction * 100).toFixed(1)}% mismatch · ${state.epitaxyRegistry.azimuthDegrees.toFixed(1)}° azimuth · nearest-node distance weighted by height`
        : "No substrate sites or interactions are introduced.",
      searchRole: activeEpitaxyWeight() > 0
        ? `Soft interfacial rank term with weight ${activeEpitaxyWeight().toFixed(2)} over the unchanged exact frontier.` : "Disabled; hard support-plane exclusion only.",
      boundary: "This declared geometric registry is not substrate chemistry, adsorption, adhesion, interface free energy, wetting, elastic relaxation, a dislocation network, or kinetics.",
    },
    "external drive": {
      observed: `${externalDriveModeLabel()} declared by the user before growth; no target coordinates or outcomes are read`,
      encoding: externalDriveMode === "none"
        ? "The frozen frontier is isotropic with respect to an external axis."
        : "The normalized parent→child attachment direction is projected onto a declared global axis or the seed-relative radial direction.",
      searchRole: activeExternalDriveWeight() > 0
        ? `Soft rank term +${activeExternalDriveWeight().toFixed(2)} × alignment over the unchanged exact candidate set.` : "Diagnostic only; weight zero.",
      boundary: "A directional geometric bias is not force, stress, pressure, electric field, chemical-potential gradient, deposition flux, or a kinetic rate.",
    },
    "constraint robustness": {
      observed: `effective geometric tolerance ε=${clusterMetricToleranceAngstrom().toFixed(3)} Å from the selected clustering uncertainty rule`,
      encoding: "The smallest contact-exclusion clearance, overlap headroom, or public-domain clearance is normalized by ε and smoothly bounded.",
      searchRole: activeRobustnessWeight() > 0
        ? `Soft rank term with weight ${activeRobustnessWeight().toFixed(2)} over the unchanged exact frontier.` : "Diagnostic only; weight zero.",
      boundary: "Margin ordering does not sample a pose ensemble and is not temperature, probability, energy, or a physical stability certificate. The separate post-decision pose audit remains validation only.",
    },
    "microstructure coupling": {
      observed: `${microstructureEvidence?.gapBoundaryAtoms || 0} gap-boundary atoms · ${microstructureEvidence?.literalOnlyAtoms || 0} literal-only · ${microstructureEvidence?.crossPoseContacts || 0} cross-pose contacts · ${microstructureEvidence?.coordinationAnomalyAtoms || 0} coordination candidates`,
      encoding: `${microstructureCouplingLabel()} converts the count of nearby frozen input-derived roles into a bounded signed score.`,
      searchRole: activeMicrostructureCouplingWeight() > 0
        ? `Soft rank term with weight ${activeMicrostructureCouplingWeight().toFixed(2)} over unchanged exact actions.` : "Post-decision diagnostic only; weight zero.",
      boundary: "A spatial role is not a defect label. This experiment infers no formation energy, migration barrier, mobility, grain identity, or mechanism.",
    },
    "multi-nucleus interface": {
      observed: `${initializedGrowthNuclei || requestedGrowthNuclei} initialized observed pose domains · ${crossNucleusMergeContacts} shared-site contacts so far`,
      encoding: "Each placement inherits its seed lineage. A contact is recorded only when an exact accepted cluster shares a colored site with a different initialized lineage.",
      searchRole: state?.nucleusInterface?.coalescenceCandidate
        ? `Diagnostic interface event with ${state.nucleusInterface.crossNucleusContacts} cross-lineage shared-site contact${state.nucleusInterface.crossNucleusContacts === 1 ? "" : "s"}.`
        : "Diagnostic only; the candidate remains within one initialized lineage.",
      boundary: "Lineage contact is not a grain-boundary classification, interfacial energy, misorientation distribution, nucleation probability, coarsening law, or physical time.",
    },
    "mesoscopic loop closure": {
      observed: `${overlapGrammar?.rules?.length || 0} frozen recurring proper-SE(3) rules can independently predict a frontier pose from already placed parents`,
      encoding: "Nearby predictions for the same cluster type are compared as complete colored point sets; raw quaternion frames are never compared, and the generating parent is excluded from the independent-consensus count.",
      searchRole: activeLoopClosureWeight() > 0
        ? `Soft rank term with weight ${activeLoopClosureWeight().toFixed(2)} over unchanged exact candidates.` : "Diagnostic only; weight zero.",
      boundary: "This is a bounded graph loop-closure residual, not long-range elasticity, stress, energy, force balance, plastic relaxation, or a dislocation calculation.",
    },
    "arrival-path accessibility": {
      observed: `${arrivalPathMode === "none" ? 0 : 9} deterministic samples per emitted site over a 2dₙₙ declared approach`,
      encoding: "Only the emitted colored sites are swept backward from the final pose; at each sample their clearance above the learned pair exclusion is evaluated against already placed atoms.",
      searchRole: activeArrivalPathWeight() > 0
        ? `Soft rank term with weight ${activeArrivalPathWeight().toFixed(2)}; final-pose admission is unchanged.` : "Disabled; final pose only.",
      boundary: "This is one declared rigid arrival geometry, not a transition path, activation barrier, diffusion event, assembly mechanism, probability, rate, or elapsed time.",
    },
    "configurational path ensemble": {
      observed: `dimensionless T*=${geometricExplorationScale.toFixed(2)} · seed ${growthPathSeed} · event ${eventIndex}`,
      encoding: "A deterministic hash of seed, event index, and exact candidate key produces one reproducible Gumbel ordering offset. No coordinate, candidate, or hard certificate is changed.",
      searchRole: geometricExplorationScale > 0
        ? "Samples one alternative ordering of the unchanged admitted frontier." : "Greedy deterministic ordering; offset zero.",
      boundary: "The exploration scale has no Kelvin or energy units and does not imply Boltzmann sampling, thermodynamic probability, free energy, a transition rate, or elapsed time.",
    },
    "GCTS marking": {
      observed: `${trainingProgress}/${markingSampleCount()} ${sectionModel?.sampleKind || "connection"} samples · ${iceAnchorTrace?.portCount || overlapGrammar?.rules?.length || 0} frozen connection states`,
      encoding: mode === "specialized"
        ? `${iceAnchorTrace?.portCount || 0} frozen proper-SE(3) molecular ports + mutually exclusive ${iceAnchorTrace?.moleculeLabel || "H₂O"} orientation domains`
        : `${sectionModel?.channels || 0}-channel ${MARKING_REPRESENTATIONS[sectionModel?.representation]?.label || "local section"} over ${sectionModel?.reach || 0} neighbour shell${sectionModel?.reach === 1 ? "" : "s"}`,
      searchRole: mode === "specialized"
        ? "All surviving molecular pose domains must agree on an oxygen anchor before it is emitted."
        : policySelect.value === "marked" ? "Bounded transported context ranks or gates the same frozen exact actions." : "Fitted but not active in the selected search policy.",
      boundary: "The marking encodes connection success/failure. It is not a physical potential, and it cannot invent a candidate pose.",
    },
  }[name] || generic;
  return { ...evidence, status: term.status, current: `${term.value} · ${term.detail}`, mode };
}

function renderConstraintDetail(term, state, mode) {
  if (!constraintDetail || !term) return;
  const evidence = geometryConstraintEvidence(term.name, term, state, mode);
  constraintDetail.className = `constraint-detail ${term.status}`;
  constraintDetail.replaceChildren();
  const header = document.createElement("header");
  const eyebrow = document.createElement("small"); eyebrow.textContent = `selected surrogate · ${term.status}`;
  const title = document.createElement("strong"); title.textContent = term.name;
  const live = document.createElement("span"); live.textContent = evidence.current;
  header.append(eyebrow, title, live); constraintDetail.append(header);
  [
    ["observed evidence", evidence.observed],
    ["geometric encoding", evidence.encoding],
    ["role in search", evidence.searchRole],
    ["claim boundary", evidence.boundary],
  ].forEach(([label, copy]) => {
    const row = document.createElement("div");
    const key = document.createElement("b"); key.textContent = label;
    const value = document.createElement("p"); value.textContent = copy;
    row.append(key, value); constraintDetail.append(row);
  });
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
      value: state.geometricStrain ? (affineLoadMode === "none" ? state.geometricStrain : state.affineLoadedGeometricStrain).total.toFixed(3) : "not evaluated",
      detail: activeGeometricStrainWeight() > 0 ? `rank weight ${activeGeometricStrainWeight().toFixed(2)} · ${affineLoadModeLabel()}` : "diagnostic · cannot authorize geometry" },
    { name: "composition reservoir", status: ranked(activeCompositionBalanceWeight() > 0),
      value: state.compositionBalance ? signed(state.compositionBalance.scaledDelta) : "not evaluated",
      detail: activeCompositionBalanceWeight() > 0 ? `rank weight ${activeCompositionBalanceWeight().toFixed(2)}` : "diagnostic · cannot authorize geometry" },
    { name: "formal-charge reservoir", status: ranked(activeFormalChargeWeight() > 0),
      value: state.formalChargeBalance?.available ? signed(state.formalChargeBalance.scaledDelta) : state.formalChargeBalance?.reason || "unavailable",
      detail: activeFormalChargeWeight() > 0 ? `rank weight ${activeFormalChargeWeight().toFixed(2)} · supplied oxidation states` : "diagnostic · cannot authorize geometry" },
    { name: "surface completion", status: ranked(activeSurfaceCompletionWeight() > 0),
      value: state.surfaceCompletion ? signed(state.surfaceCompletion.scaledDelta) : "not evaluated",
      detail: activeSurfaceCompletionWeight() > 0 ? `rank weight ${activeSurfaceCompletionWeight().toFixed(2)}` : "diagnostic · cannot authorize geometry" },
    { name: "front morphology", status: ranked(activeFrontMorphologyWeight() > 0),
      value: state.frontMorphology ? `${signed(state.frontMorphology.score)} · ${state.frontMorphology.angularSectors}/8 sectors` : "not evaluated",
      detail: activeFrontMorphologyWeight() > 0 ? `${frontMorphologyLabel()} · rank weight ${activeFrontMorphologyWeight().toFixed(2)}` : "diagnostic · no capillarity claim" },
    { name: "epitaxial registry", status: ranked(activeEpitaxyWeight() > 0),
      value: state.epitaxyRegistry?.enabled ? `${signed(state.epitaxyRegistry.score)} · ${state.epitaxyRegistry.interfacialSites} interface sites` : "inactive",
      detail: activeEpitaxyWeight() > 0 ? `${epitaxyTemplateLabel()} · rank weight ${activeEpitaxyWeight().toFixed(2)}` : "requires supported-film template" },
    { name: "external drive", status: ranked(activeExternalDriveWeight() > 0),
      value: state.externalDrive ? signed(state.externalDrive.alignment) : "not evaluated",
      detail: activeExternalDriveWeight() > 0 ? `${externalDriveModeLabel()} · rank weight ${activeExternalDriveWeight().toFixed(2)}` : "isotropic · weight zero" },
    { name: "constraint robustness", status: ranked(activeRobustnessWeight() > 0),
      value: state.constraintRobustness ? `${state.constraintRobustness.score.toFixed(3)} · ${state.constraintRobustness.minimumMarginAngstrom.toFixed(3)} Å min` : "not evaluated",
      detail: activeRobustnessWeight() > 0 ? `rank weight ${activeRobustnessWeight().toFixed(2)} · deterministic margin` : "diagnostic · no ensemble" },
    { name: "microstructure coupling", status: ranked(activeMicrostructureCouplingWeight() > 0),
      value: state.microstructureCoupling ? `${signed(state.microstructureCoupling.score)} · ${state.microstructureCoupling.label}` : "not evaluated",
      detail: activeMicrostructureCouplingWeight() > 0 ? `rank weight ${activeMicrostructureCouplingWeight().toFixed(2)} · labels withheld` : "diagnostic · labels withheld" },
    { name: "multi-nucleus interface", status: state.nucleusInterface?.coalescenceCandidate ? "interface" : "diagnostic",
      value: state.nucleusInterface ? `${state.nucleusInterface.crossNucleusContacts} cross-lineage contacts · parent N${state.nucleusInterface.parentNucleus}` : "not evaluated",
      detail: `${initializedGrowthNuclei || requestedGrowthNuclei} observed nuclei · diagnostic only · no interfacial energy` },
    { name: "mesoscopic loop closure", status: ranked(activeLoopClosureWeight() > 0),
      value: state.loopClosure ? `${signed(state.loopClosure.score)} · ${state.loopClosure.independentCompatiblePaths} support / ${state.loopClosure.independentConflictingPaths} conflict` : "not evaluated",
      detail: activeLoopClosureWeight() > 0 ? `rank weight ${activeLoopClosureWeight().toFixed(2)} · generating parent excluded` : "diagnostic · local-only ordering" },
    { name: "arrival-path accessibility", status: ranked(activeArrivalPathWeight() > 0),
      value: state.arrivalPath ? `${signed(state.arrivalPath.score)} · ${state.arrivalPath.blockedSiteSamples}/${state.arrivalPath.siteSamples} blocked samples` : "not evaluated",
      detail: activeArrivalPathWeight() > 0 ? `rank weight ${activeArrivalPathWeight().toFixed(2)} · ${arrivalPathLabel()}` : "disabled · final pose only" },
    { name: "configurational path ensemble", status: geometricExplorationScale > 0 ? "sampled" : "diagnostic",
      value: state.geometricExploration ? `${signed(state.geometricExploration.offset)} · T* ${state.geometricExploration.dimensionlessScale.toFixed(2)} · seed ${state.geometricExploration.seed}` : "not evaluated",
      detail: geometricExplorationScale > 0 ? "reproducible branch-order offset · unchanged geometry and hard gates" : "greedy ordering · offset zero" },
    { name: "GCTS marking", status: policySelect.value === "marked" ? state.markingAccepted ? "pass" : "fail" : "diagnostic",
      value: policySelect.value === "marked" ? state.markingAccepted ? "compatible" : "mismatch" : "not gating",
      detail: "bounded transported connection section" },
  ] : mode === "withheld" ? [
    { name: "species / hard core", status: "diagnostic", value: "not executed", detail: "occupational state unresolved" },
    { name: "shared support", status: "diagnostic", value: "not executed", detail: "no molecular seed realization" },
    { name: "novel colored sites", status: "diagnostic", value: "not executed", detail: "average sites are not emitted atoms" },
    { name: "public boundary", status: "diagnostic", value: "not executed", detail: "target calls 0" },
    { name: "coordination capacity", status: "diagnostic", value: "inspection only", detail: "average-site geometry" },
    { name: "angular envelope", status: "diagnostic", value: "inspection only", detail: "average-site geometry" },
    { name: "elastic proxy", status: "diagnostic", value: "withheld", detail: "no branch ranking" },
    { name: "composition reservoir", status: "diagnostic", value: "withheld", detail: "occupancy ensemble required" },
    { name: "formal-charge reservoir", status: "diagnostic", value: "unavailable", detail: "no complete supplied oxidation-state channel" },
    { name: "surface completion", status: "diagnostic", value: "withheld", detail: "no branch ranking" },
    { name: "front morphology", status: "diagnostic", value: "withheld", detail: "no executable front" },
    { name: "epitaxial registry", status: "diagnostic", value: "withheld", detail: "no executable supported-film front" },
    { name: "external drive", status: "diagnostic", value: "withheld", detail: "occupational realization required" },
    { name: "GCTS marking", status: "diagnostic", value: "not executed", detail: "inspectable sections only" },
  ] : mode === "specialized" ? [
    { name: "species / hard core", status: "pass", value: "backend-certified", detail: "frozen exact trace" },
    { name: "shared support", status: "pass", value: "frozen ports", detail: "proper-SE(3) molecular attachments" },
    { name: "novel colored sites", status: "pass", value: "exact anchors", detail: "one-to-one emitted-site certificate" },
    { name: "public boundary", status: "pass", value: "sealed", detail: "target calls 0 before scoring" },
    { name: "coordination capacity", status: "diagnostic", value: "not used", detail: "specialized frozen trace" },
    { name: "angular envelope", status: "diagnostic", value: "not used", detail: "specialized frozen trace" },
    { name: "elastic proxy", status: "diagnostic", value: "not used", detail: "cannot authorize this trace" },
    { name: "composition reservoir", status: "diagnostic", value: "not used", detail: "cannot authorize this trace" },
    { name: "formal-charge reservoir", status: "diagnostic", value: "not used", detail: "cannot authorize this trace" },
    { name: "surface completion", status: "diagnostic", value: "not used", detail: "cannot authorize this trace" },
    { name: "front morphology", status: "diagnostic", value: "not used", detail: "specialized frozen trace" },
    { name: "epitaxial registry", status: "diagnostic", value: "not used", detail: "specialized frozen trace" },
    { name: "external drive", status: "diagnostic", value: "not used", detail: "cannot authorize this trace" },
    { name: "GCTS marking", status: "pass", value: "domain unanimity",
      detail: `all surviving ${iceAnchorTrace?.moleculeLabel || "H₂O"} poses agree` },
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
    { name: "formal-charge reservoir", status: ranked(activeFormalChargeWeight() > 0),
      value: activeFormalChargeWeight() > 0 ? "ranked" : formalChargeTarget?.available ? "diagnostic" : "unavailable",
      detail: formalChargeTarget?.available ? `weight ${activeFormalChargeWeight().toFixed(2)}` : "no complete supplied oxidation-state channel" },
    { name: "surface completion", status: ranked(activeSurfaceCompletionWeight() > 0),
      value: activeSurfaceCompletionWeight() > 0 ? "ranked" : "diagnostic", detail: `weight ${activeSurfaceCompletionWeight().toFixed(2)}` },
    { name: "front morphology", status: ranked(activeFrontMorphologyWeight() > 0),
      value: activeFrontMorphologyWeight() > 0 ? frontMorphologyLabel() : "diagnostic", detail: `weight ${activeFrontMorphologyWeight().toFixed(2)}` },
    { name: "epitaxial registry", status: ranked(activeEpitaxyWeight() > 0),
      value: activeEpitaxyWeight() > 0 ? epitaxyTemplateLabel() : "inactive", detail: `weight ${activeEpitaxyWeight().toFixed(2)}` },
    { name: "external drive", status: ranked(activeExternalDriveWeight() > 0),
      value: activeExternalDriveWeight() > 0 ? externalDriveModeLabel() : "isotropic",
      detail: activeExternalDriveWeight() > 0 ? `weight ${activeExternalDriveWeight().toFixed(2)}` : "weight zero" },
    { name: "GCTS marking", status: policySelect.value === "marked" ? "ranked" : "diagnostic",
      value: policySelect.value === "marked" ? "active" : "not gating", detail: "bounded local section" },
  ];
  if (!terms.some((term) => term.name === selectedConstraintName)) selectedConstraintName = terms[0].name;
  constraintLedger.replaceChildren(...terms.map((term) => {
    const row = document.createElement("button"); row.type = "button";
    row.className = `constraint-term ${term.status}`;
    row.classList.toggle("active", term.name === selectedConstraintName);
    row.setAttribute("aria-pressed", String(term.name === selectedConstraintName));
    row.title = `Inspect ${term.name}: evidence, geometric encoding, search role, and claim boundary`;
    const label = document.createElement("small"); label.textContent = term.name;
    const value = document.createElement("strong"); value.textContent = term.value;
    const detail = document.createElement("span"); detail.textContent = term.detail;
    row.append(label, value, detail);
    row.addEventListener("click", () => {
      selectedConstraintName = term.name;
      constraintLedger.querySelectorAll(".constraint-term").forEach((candidate) => {
        const active = candidate === row;
        candidate.classList.toggle("active", active);
        candidate.setAttribute("aria-pressed", String(active));
      });
      renderConstraintDetail(term, state, mode);
    });
    return row;
  }));
  renderConstraintDetail(terms.find((term) => term.name === selectedConstraintName), state, mode);
}

function previewPolicyWinner(policy, snapshot) {
  selectedPolicyPreviewId = policy.id;
  const frontierReadout = { value: frontierMetric.textContent, detail: frontierDelta.textContent };
  if (policy.preview) {
    currentCandidates = [{ p: policy.preview.p.clone(), rotation: policy.preview.rotation.clone(),
      type: policy.preview.type, accepted: true, preview: true }];
    rebuildWorld();
    frontierMetric.textContent = frontierReadout.value;
    frontierDelta.textContent = frontierReadout.detail;
    policyPreviewState.textContent = `${policy.label}: ${policy.action} · frontier ${snapshot.candidateDigest} · candidate set target-free`
      + `${snapshot.rankingTargetUsed ? " · replay score reference-guided" : " · ranking target-free"}`;
  } else {
    currentCandidates = [];
    rebuildWorld();
    frontierMetric.textContent = frontierReadout.value;
    frontierDelta.textContent = frontierReadout.detail;
    policyPreviewState.textContent = `${policy.label}: no hard-admitted action on frontier ${snapshot.candidateDigest}`;
  }
  renderPolicyComparison();
}

function renderPolicyComparison() {
  policyComparison.replaceChildren();
  policyHistoryElement.replaceChildren();
  if (pipelineStage !== 4) {
    policyComparisonState.textContent = "available during growth";
    policySensitivityState.textContent = "available during growth";
    policyPreviewState.textContent = "Select a policy row during material growth.";
    return;
  }
  if (iceAnchorTrace) {
    policyComparisonState.textContent = "specialized frozen trace";
    const row = document.createElement("article"); row.className = "active";
    const label = document.createElement("small"); label.textContent = "orientation domains";
    const action = document.createElement("strong"); action.textContent = "unanimous proper-SE(3) ports";
    const score = document.createElement("em"); score.textContent = "generic ranks unused";
    row.append(label, action, score); policyComparison.append(row);
    policySensitivityState.textContent = "generic policy comparison not applicable";
    policyPreviewState.textContent = `${iceAnchorTrace.selectionRuleLabel} is the only certified molecular-anchor policy in this trace.`;
    return;
  }
  if (!lastPolicyComparison) {
    policyComparisonState.textContent = "advance one update";
    const row = document.createElement("article");
    const label = document.createElement("small"); label.textContent = "pending";
    const action = document.createElement("strong"); action.textContent = `${frontierCandidates.length} frozen candidates await evaluation`;
    const score = document.createElement("em"); score.textContent = "same geometry";
    row.append(label, action, score); policyComparison.append(row);
    policySensitivityState.textContent = "no evaluated frontiers";
    policyPreviewState.textContent = "Select a policy row after the first frontier is frozen.";
    return;
  }
  const snapshot = policyComparisonHistory[selectedPolicySnapshotIndex] || lastPolicyComparison;
  policyComparisonState.textContent = `${snapshot.frontier} candidates · ${snapshot.admissible} admitted · ${snapshot.uniqueTopActions} winner${snapshot.uniqueTopActions === 1 ? "" : "s"}`
    + `${snapshot.referenceGuided ? " · target-aware replay" : " · target-blind frontier"}`;
  snapshot.policies.forEach((policy) => {
    const row = document.createElement("button"); row.type = "button";
    row.classList.toggle("active", policy.id === selectedPolicyPreviewId);
    row.setAttribute("aria-pressed", String(policy.id === selectedPolicyPreviewId));
    row.title = `Preview the ${policy.label} winner without executing it`;
    const label = document.createElement("small"); label.textContent = policy.label;
    const action = document.createElement("strong"); action.textContent = policy.action;
    const score = document.createElement("em"); score.textContent = policy.score === null ? "—" : policy.score.toFixed(3);
    row.append(label, action, score); policyComparison.append(row);
    row.addEventListener("click", () => previewPolicyWinner(policy, snapshot));
  });
  const sensitive = policyComparisonHistory.filter((entry) => entry.uniqueTopActions > 1).length;
  const meanWinners = policyComparisonHistory.reduce((sum, entry) => sum + entry.uniqueTopActions, 0)
    / Math.max(1, policyComparisonHistory.length);
  policySensitivityState.textContent = `${sensitive}/${policyComparisonHistory.length} frontiers disagree · mean ${meanWinners.toFixed(2)} winners`;
  policyComparisonHistory.slice(-12).forEach((entry, visibleIndex) => {
    const absoluteIndex = Math.max(0, policyComparisonHistory.length - 12) + visibleIndex;
    const button = document.createElement("button"); button.type = "button";
    button.classList.toggle("sensitive", entry.uniqueTopActions > 1);
    button.classList.toggle("active", absoluteIndex === selectedPolicySnapshotIndex);
    button.setAttribute("aria-pressed", String(absoluteIndex === selectedPolicySnapshotIndex));
    button.textContent = `${entry.index} · ${entry.uniqueTopActions}`;
    button.title = `Frontier ${entry.index}: ${entry.uniqueTopActions} distinct policy winners · candidate digest ${entry.candidateDigest}`;
    button.addEventListener("click", () => {
      selectedPolicySnapshotIndex = absoluteIndex;
      selectedPolicyPreviewId = "active";
      const activePolicy = entry.policies.find((policy) => policy.id === "active") || entry.policies.at(-1);
      previewPolicyWinner(activePolicy, entry);
    });
    policyHistoryElement.append(button);
  });
  const selectedPolicy = snapshot.policies.find((policy) => policy.id === selectedPolicyPreviewId) || snapshot.policies.at(-1);
  policyPreviewState.textContent = `${selectedPolicy.label}: ${selectedPolicy.action} · frontier ${snapshot.candidateDigest} · candidate set target-free`
    + `${snapshot.rankingTargetUsed ? " · replay score reference-guided" : " · ranking target-free"}`;
}

function liveGrowthCertificate() {
  if (pipelineStage < 4) return null;
  const benchmark = currentRecursiveBenchmark();
  if (currentMaterial().growthWithheld) return {
    mode: "occupational-disorder claim boundary",
    state: "growth withheld",
    knownWindow: { status: "pass", title: `${referenceCount()} average sites preserved`,
      detail: `${currentMaterial().occupancyWeightedAtomCount} occupancy-weighted atoms · no candidate site collapsed` },
    continuation: { status: "open", title: "No unique molecular seed state",
      detail: "The average diffraction structure does not choose two D sites around each oxygen." },
    hierarchy: { status: "open", title: "Resolve an ice-rule realization first",
      detail: "A sampled occupational microstate or an occupancy-valued ensemble grammar is required before growth." },
    claimBoundary: { status: "pass", title: "No fictitious average-atom growth",
      detail: "Play, branching, promotion, and phase classification remain disabled for this ambiguity control." },
    metrics: { averageSites: referenceCount(), occupancyWeightedAtoms: currentMaterial().occupancyWeightedAtomCount,
      targetCoordinatesUsed: false, uniqueMolecularAssignmentClaimed: false, growthExecuted: false },
    benchmarkGate: benchmark.gate,
  };
  if (iceAnchorTrace) {
    const processed = iceAnchorTrace.waves.slice(0, iceAnchorWaveIndex);
    const accepted = processed.reduce((sum, wave) => sum + wave.acceptedAnchors, 0);
    const nonemptyWaves = processed.filter((wave) => wave.acceptedAnchors > 0).length;
    const fixedPointReached = iceAnchorTrace.fixedPoint && iceAnchorWaveIndex >= iceAnchorTrace.waves.length;
    return {
      mode: "sealed molecular-anchor continuation",
      state: fixedPointReached ? "finite fixed point" : "target-blind execution",
      knownWindow: { status: "pass", title: `${iceAnchorTrace.seedAnchors} observed O anchors`,
        detail: `Seed only; the complete ${iceAnchorTrace.moleculeLabel} / bridge / ${iceAnchorTrace.gapLabel} cover was certified in cluster identification.` },
      continuation: { status: iceAnchorTrace.exactBackendCountParity ? "pass" : "open",
        title: `${accepted} exact emitted O anchors`,
        detail: `${processed.reduce((sum, wave) => sum + wave.candidateAnchors, 0)} frozen candidates processed · target calls 0` },
      hierarchy: { status: nonemptyWaves >= 2 ? "progress" : "open",
        title: `${nonemptyWaves} nonempty self-fed wave${nonemptyWaves === 1 ? "" : "s"}`,
        detail: fixedPointReached ? "Grammar exhausted safely; no supported successor remains." : "Execution has not yet reached its certified endpoint." },
      claimBoundary: { status: "open", title: `O scaffold finite · ${iceAnchorTrace.orientationSpecies} pose / stationary open`,
        detail: `Mutually exclusive ${iceAnchorTrace.moleculeLabel} orientations stay symbolic; no clusters² or exponential ice claim.` },
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

function clusterDiameterRangeAngstrom() {
  const sceneToAngstrom = referenceSpacingA / Math.max(referenceSpacing, 1e-12);
  const diameters = clusterGalleryTypes().map((cluster) => {
    const sites = clusterGallerySites(cluster);
    let diameter = 0;
    for (let first = 0; first < sites.length; first++) for (let second = first + 1; second < sites.length; second++) {
      diameter = Math.max(diameter, sites[first].vector.distanceTo(sites[second].vector));
    }
    return diameter * sceneToAngstrom;
  }).filter((diameter) => diameter > 0).sort((first, second) => first - second);
  if (!diameters.length) return { median: 0, maximum: 0 };
  return { median: diameters[Math.floor(diameters.length / 2)], maximum: diameters.at(-1) };
}

function observationProvenanceRecords() {
  const conditions = activeMeasurementConditions();
  const validation = activeImportedFrameValidation();
  const conditionSummary = [
    conditions?.temperature ? `T ${formatRecordedCondition(conditions.temperature.value)} ${conditions.temperature.unit || "K"}` : null,
    conditions?.pressure ? `P ${formatRecordedCondition(conditions.pressure.value)} ${conditions.pressure.unit || "kPa"}` : null,
    conditions?.environment?.value ? conditions.environment.value : null,
  ].filter(Boolean);
  const frames = evidenceFrameCount();
  const uncertainty = measuredPairUncertaintyAngstrom();
  const uncertaintySource = measuredPairUncertaintySource();
  const tolerance = clusterMetricToleranceAngstrom();
  const coverReady = pipelineStage >= 1;
  const growthReady = pipelineStage >= 4;
  const importedFrames = importedTrajectoryFrames();
  return [
    { id: "conditions", short: "conditions", status: conditionSummary.length ? "recorded" : "unavailable",
      value: conditionSummary.length ? conditionSummary.join(" · ") : "no temperature / pressure metadata",
      observed: conditionSummary.length ? `Recorded source metadata: ${conditionSummary.join(" · ")}.` : "No calibrated thermodynamic condition accompanies this geometry.",
      transform: "Preserved as provenance labels only; no geometric parameter is inferred from temperature or pressure.",
      use: "Displayed and serialized; never passed into clustering, marking, candidate enumeration, or ranking.",
      boundary: "Recorded measurement conditions describe how a structure was measured, not how it grew, equilibrated, or should evolve." },
    { id: "samples", short: "samples", status: frames > 1 ? "measured" : "single",
      value: frames > 1 ? `${frames} fixed-topology frames` : "1 structural frame",
      observed: scenarioSelect.value === "imported" && importedFrames.length > 1
        ? `${importedFrames.length} ordered structural snapshots with fixed species and atom ordering.`
        : `${referenceCount()} species-labelled Cartesian sites in one observation window.`,
      transform: frames > 1 ? `${ensembleEvidenceMode === "all" ? "All frames pool" : "Only the displayed frame supplies"} contact, coordination, angle, and local pair-distance observations.` : "One frame supplies the finite structural evidence.",
      use: `Growth starts from exactly one displayed frame${frames > 1 ? ` (${importedFrameIndex + 1}/${importedFrames.length})` : ""}; cross-frame atom pairs are never invented.`,
      boundary: "Snapshot order is not treated as a trajectory unless velocities, time steps, and calibrated temporal provenance are independently supplied; none are used here." },
    { id: "uncertainty", short: "uncertainty", status: uncertainty > 0 ? "measured" : "nominal",
      value: uncertainty > 0 ? `${uncertainty.toFixed(3)} Å pair σ floor` : "no measured σ floor",
      observed: uncertainty > 0
        ? `${uncertaintySource}; ${validation?.thermalDisplacementSites || 0} U/B sites and ${ensemblePairDistanceUncertainty?.localPairCount || 0} local snapshot-pair observations.`
        : "No U/B displacement parameters or repeated fixed-topology pair-distance spread is available.",
      transform: uncertainty > 0 ? "The larger measured pair-distance uncertainty becomes a lower bound on metric-isometry matching tolerance." : "The selected nominal tolerance remains unchanged.",
      use: "Broadens equivalence testing and colored distance envelopes; it does not displace atoms or sample a thermal configuration.",
      boundary: "A positional uncertainty ellipsoid is not a phonon mode, force covariance, temperature distribution, or dynamical ensemble." },
    { id: "tolerance", short: "tolerance", status: "active",
      value: `ε ${(effectiveClusterMetricTolerance() * 100).toFixed(2)}% · ${tolerance.toFixed(3)} Å`,
      observed: `${clusterToleranceMode} nominal mode: ${(clusterMetricTolerance() * 100).toFixed(1)}% of dₙₙ=${referenceSpacingA.toFixed(3)} Å; floor source ${uncertaintySource}.`,
      transform: `Effective ε=max(nominal ${ (referenceSpacingA * clusterMetricTolerance()).toFixed(3)} Å, measured ${uncertainty.toFixed(3)} Å).`,
      use: "Controls colored metric-isometry class matching and vocabulary compatibility; every experiment receipt records the resolved value.",
      boundary: "Tolerance is an observation/model-resolution parameter, not thermal energy, strain energy, or permission to move sites." },
    { id: "representation", short: "representation", status: coverReady ? "learned" : "pending",
      value: coverReady ? `${clusterGalleryTypes().length} cover types · ${orientationAtlas.reduce((sum, entry) => sum + entry.orientations, 0)} pose orbits` : "await cluster identification",
      observed: coverReady ? `${learnedCover.covered}/${referenceCount()} observed sites represented by ${learnedCover.placements.length} overlapping placements.` : "Only raw sites and chemistry tokens are currently available.",
      transform: coverReady ? "Resolved tolerance produces colored isometry classes, explicit gaps, proper-pose orbits, and frozen connection ports." : "No cluster label is supplied; the learner must form a complete cover first.",
      use: coverReady ? "The exact local vocabulary becomes the only geometry available to GCTS and tree search." : "Not used before identification.",
      boundary: "A stable representation does not prove energetic stability, uniqueness of motif decomposition, or transfer to an unseen growth front." },
    { id: "growth", short: "growth use", status: growthReady ? "active" : "pending",
      value: growthReady ? `${atoms.length} explicit sites · ${acceptedDecisions} accepted actions` : "not executed",
      observed: growthReady ? `${frontierCandidates.length} frozen frontier actions over the selected seed frame.` : "Growth waits for cluster and marking stages.",
      transform: "Only species, positions, structural uncertainty-derived envelopes, learned ports, and configured geometry surrogates enter the search.",
      use: growthReady ? "Whole exact cluster placements jump between certified structural states; the known target is not a branch feature." : "No branch has been ranked or committed.",
      boundary: "Temperature, pressure, environment, snapshot ordering, forces, velocities, rates, and physical time remain outside execution." },
  ];
}

function renderObservationProvenance() {
  const records = observationProvenanceRecords();
  if (!records.some((record) => record.id === selectedObservationProvenanceId)) {
    selectedObservationProvenanceId = records.find((record) => record.status === "measured")?.id || "tolerance";
  }
  const selected = records.find((record) => record.id === selectedObservationProvenanceId) || records[0];
  const measured = records.filter((record) => ["recorded", "measured"].includes(record.status)).length;
  observationProvenanceState.textContent = `${measured} measured channel${measured === 1 ? "" : "s"} · simulation controls 0`;
  observationProvenance.replaceChildren(...records.map((record, index) => {
    const button = document.createElement("button"); button.type = "button";
    button.className = record.status;
    button.classList.toggle("active", record.id === selected.id);
    button.setAttribute("aria-pressed", String(record.id === selected.id));
    const number = document.createElement("small"); number.textContent = String(index + 1).padStart(2, "0");
    const label = document.createElement("strong"); label.textContent = record.short;
    const status = document.createElement("span"); status.textContent = record.status;
    button.append(number, label, status);
    button.addEventListener("click", () => { selectedObservationProvenanceId = record.id; renderObservationProvenance(); });
    return button;
  }));
  observationProvenanceDetail.className = `observation-provenance-detail ${selected.status}`;
  observationProvenanceDetail.replaceChildren();
  const header = document.createElement("header");
  const block = document.createElement("div"); const eyebrow = document.createElement("small"); eyebrow.textContent = selected.status;
  const title = document.createElement("strong"); title.textContent = selected.short;
  const value = document.createElement("span"); value.textContent = selected.value;
  block.append(eyebrow, title); header.append(block, value); observationProvenanceDetail.append(header);
  [["observed", selected.observed], ["transformation", selected.transform], ["use in search", selected.use], ["claim boundary", selected.boundary]].forEach(([label, copy]) => {
    const row = document.createElement("div"); const key = document.createElement("b"); const body = document.createElement("p");
    key.textContent = label; body.textContent = copy; row.append(key, body); observationProvenanceDetail.append(row);
  });
}

function liveScalePassportRecords() {
  const clusterScale = clusterDiameterRangeAngstrom();
  const clusterTypes = clusterGalleryTypes();
  const markingConfig = currentMarkingConfig();
  const conditions = activeMeasurementConditions();
  const conditionLabels = [
    conditions?.temperature?.value === null || conditions?.temperature?.value === undefined
      ? null : `${conditions.temperature.value} K recorded`,
    conditions?.pressure?.value === null || conditions?.pressure?.value === undefined
      ? null : `${conditions.pressure.value} kPa recorded`,
    conditions?.environment?.value || null,
  ].filter(Boolean);
  const maximumDepth = Math.max(0, ...placedClusters.map((placement) => placement.depth || 0));
  const stageReached = (stage) => pipelineStage >= stage;
  return [
    {
      id: "contacts", label: "atoms + contacts", short: "atomic", status: "reached",
      scale: `${referenceSpacingA.toFixed(3)} Å nearest-neighbor scale`,
      evidence: `${referenceCount().toLocaleString()} colored sites · ${coloredDistanceEnvelopes.atomPresentations.toLocaleString()} atom presentations`,
      encoding: `${coloredDistanceEnvelopes.records.length} pair exclusions · ${coloredCoordinationEnvelopes.records.length} coordination caps · ${coloredAngularEnvelopes.records.length} angular channels`,
      role: "Hard collision, species, coordination, and observed-angle admission; dimensionless contact strain may softly rank legal actions.",
      boundary: "No bond order, electron density, force, phonon, elastic modulus, pair potential, or angular potential is inferred.",
    },
    {
      id: "clusters", label: "clusters + voids", short: "local motifs", status: stageReached(1) ? "reached" : "pending",
      scale: stageReached(1) ? `${clusterScale.median.toFixed(2)} Å median · ${clusterScale.maximum.toFixed(2)} Å maximum support` : "learned after complete-cover discovery",
      evidence: stageReached(1) ? `${clusterTypes.length} colored isometry classes · ${learnedCover.placements.length} placements · ${learnedCover.residualTypes?.length || 0} residual classes` : "No cluster label is supplied with the input.",
      encoding: "Overlapping irregular colored point sets, proper-pose orbits, molecular faces, connection polyhedra, and explicit gap terminals.",
      role: "Defines the indivisible geometry transported by the covering search; residuals close the observation but cannot silently become growth rules.",
      boundary: "Recurrence and exact cover do not establish energetic stability, defect formation energy, relaxation, or a unique physical motif decomposition.",
    },
    {
      id: "marking", label: "GCTS neighborhood", short: "connection halo", status: stageReached(3) ? "reached" : "pending",
      scale: stageReached(3) ? `${sectionModel.reach} cluster-hop reach · ${sectionModel.channels} channels` : `${markingConfig.reach} cluster-hop reach configured`,
      evidence: stageReached(3) ? `${sectionModel.fitCount ?? sectionModel.curve.length} fit sections · ${sectionModel.holdoutCount ?? 0} holdout sections` : "Channels are allocated only after cluster pose and port ranks are frozen.",
      encoding: stageReached(3) ? `${MARKING_REPRESENTATIONS[sectionModel.representation]?.label || sectionModel.representation}; bounded incoming compatibility and failure evidence` : `${MARKING_REPRESENTATIONS[markingConfig.representation]?.label || markingConfig.representation} requested`,
      role: "Ranks or admits already enumerated exact cluster attachments; it can select among alternatives but cannot move an atom or invent a pose.",
      boundary: "The marking is a connection-valued local section, not potential energy, free energy, probability, or elapsed-time dynamics.",
    },
    {
      id: "continuation", label: "frontier + hierarchy", short: "structural scale", status: stageReached(4) ? "active" : "pending",
      scale: stageReached(4) ? `${placedClusters.length.toLocaleString()} placed clusters · causal depth ${maximumDepth}` : "activated during material growth",
      evidence: stageReached(4) ? `${frontierCandidates.length.toLocaleString()} live SE(3) frontier actions · ${acceptedDecisions} accepted / ${rejectedDecisions} rejected decisions` : "Requires a frozen cluster, port, and marking vocabulary.",
      encoding: hierarchyEnabled ? "Dependency-ordered tree search with compatible antichain commits and optional clusters-of-clusters promotion." : "Primitive-cluster best-first covering search; recursive promotion disabled.",
      role: "Leap-frogs between fully certified structural states while preserving explicit colored overlaps, collisions, residuals, and branch work.",
      boundary: "A deep hierarchy or large represented count is not stationary growth; exponential claims require an exact recurring production across independently verified scales.",
    },
    {
      id: "kinetics", label: "thermodynamics + time", short: "open boundary", status: "open",
      scale: conditionLabels.length ? conditionLabels.join(" · ") : "no calibrated thermodynamic state supplied",
      evidence: conditionLabels.length ? `${conditionLabels.length} recorded condition channel${conditionLabels.length === 1 ? "" : "s"}; retained as provenance only` : "Positions, species, and optional structural snapshots contain no clock, force, or ensemble calibration.",
      encoding: "Only structural successes/failures and geometric surrogate scores are available. Recorded conditions never become hidden simulation controls.",
      role: "Defines the current approximation boundary and the data that MD, DFT, kinetic Monte Carlo, or experiment must supply for kinetic calibration.",
      boundary: "No temperature-dependent free energy, chemical potential, diffusion barrier, nucleation probability, growth rate, or physical elapsed time is claimed.",
    },
  ];
}

function renderScalePassport() {
  const records = liveScalePassportRecords();
  const defaults = ["contacts", "clusters", "clusters", "marking", "continuation"];
  if (selectedScalePassportStage !== pipelineStage || !records.some((record) => record.id === selectedScalePassportId)) {
    selectedScalePassportId = defaults[pipelineStage] || "contacts";
    selectedScalePassportStage = pipelineStage;
  }
  const selected = records.find((record) => record.id === selectedScalePassportId) || records[0];
  const encoded = records.filter((record) => ["reached", "active"].includes(record.status)).length;
  scalePassportState.textContent = `${encoded}/4 structural scales encoded · kinetics open`;
  scalePassport.replaceChildren(...records.map((record, index) => {
    const button = document.createElement("button"); button.type = "button";
    button.className = record.status;
    button.classList.toggle("active", record.id === selected.id);
    button.setAttribute("aria-pressed", String(record.id === selected.id));
    const number = document.createElement("small"); number.textContent = String(index + 1).padStart(2, "0");
    const label = document.createElement("strong"); label.textContent = record.short;
    const status = document.createElement("span"); status.textContent = record.status;
    button.append(number, label, status);
    button.addEventListener("click", () => { selectedScalePassportId = record.id; renderScalePassport(); });
    return button;
  }));
  scalePassportDetail.className = `scale-passport-detail ${selected.status}`;
  scalePassportDetail.replaceChildren();
  const header = document.createElement("header");
  const headerText = document.createElement("div");
  const eyebrow = document.createElement("small"); eyebrow.textContent = selected.status;
  const title = document.createElement("strong"); title.textContent = selected.label;
  const scale = document.createElement("span"); scale.textContent = selected.scale;
  headerText.append(eyebrow, title); header.append(headerText, scale); scalePassportDetail.append(header);
  [["observed evidence", selected.evidence], ["geometric encoding", selected.encoding],
    ["role in search", selected.role], ["claim boundary", selected.boundary]].forEach(([label, copy]) => {
    const row = document.createElement("div"); const key = document.createElement("b"); const value = document.createElement("p");
    key.textContent = label; value.textContent = copy; row.append(key, value); scalePassportDetail.append(row);
  });
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
  renderComputationalCost();
  renderObservationProvenance();
  renderScalePassport();
  renderPolicyComparison();
  renderStructuralLeap();
  renderGrowthMechanismAudit();
  updateProcessTimeline();
  eventCounter.textContent = String(eventIndex).padStart(4, "0");
  const material = currentMaterial();
  playButton.disabled = pipelineStage === 4 && Boolean(material.growthWithheld);
  stepButton.disabled = pipelineStage === 4 && Boolean(material.growthWithheld);
  if (pipelineStage === 0) {
    atomLabel.textContent = material.averageStructureSites ? "AVERAGE SITES" : "ATOMS"; atomMetric.textContent = String(referenceCount()); atomDelta.textContent = material.averageStructureSites ? `${material.occupancyWeightedAtomCount} occupancy-weighted atoms · xyz in Å` : `${material.name} · xyz in Å`;
    frontierLabel.textContent = "ELEMENTS"; frontierMetric.textContent = String(material.actualElements?.length || material.elements.length); frontierDelta.textContent = materialElementLabels(material).join(" / ");
    oracleLabel.textContent = "LABELS GIVEN"; oracleMetric.textContent = "0"; oracleDelta.textContent = "clusters must be inferred";
    reuseLabel.textContent = "GROWTH MODE"; reuseMetric.textContent = "OPEN"; reuseDelta.textContent = "restartable 1–2 minute bursts";
  } else if (pipelineStage === 1) {
    const discovery = clusterDiscoveryState();
    const finished = clusterDiscoveryProgress >= (clusterDiscoveryTrace?.totalSteps || 0);
    const covered = finished ? learnedCover.covered : discovery.coveredAtoms.size;
    stageEyebrow.textContent = "learning · full-scene support discovery";
    stageTitle.textContent = finished
      ? "The overlapping cluster-and-gap cover has settled"
      : "Test, remove, and replace connections across the full configuration";
    phaseReadout.textContent = finished
      ? `${clusterGalleryTypes().length} isometry classes settled`
      : `discovery ${clusterDiscoveryProgress}/${clusterDiscoveryTrace?.totalSteps || 0}`;
    decisionTitle.textContent = finished ? "Complete support graph accepted" : "Resolving competing local connections";
    decisionCopy.textContent = finished
      ? "Every observed atom belongs to at least one accepted molecular, irregular-support, or explicit gap cluster. Proper pose multiplicities and marking channels can now be learned from these occurrences."
      : "Muted teal edges are live hypotheses. Locally inconsistent or non-recurrent edges flash red before removal; family-colored edges have survived and now support one or more accepted cluster occurrences.";
    captionAction.textContent = finished
      ? `${discovery.settledPlacements}/${learnedCover.placements.length} placements settled · ${covered}/${referenceCount()} sites covered · ${discovery.cumulativeRejected} candidate edges rejected.`
      : `${discovery.tentative.length} tentative · ${discovery.rejected.length} being removed · ${discovery.settled.length} settled edges · ${discovery.settledPlacements} support placements currently certified.`;
    atomLabel.textContent = "CANDIDATE LINKS"; atomMetric.textContent = String(discovery.tentative.length); atomDelta.textContent = "live hypotheses over the full 3D scene";
    frontierLabel.textContent = "SETTLED SUPPORTS"; frontierMetric.textContent = String(discovery.settledPlacements); frontierDelta.textContent = `${discovery.settled.length} accepted connection edges`;
    oracleLabel.textContent = "CURRENT COVERAGE"; oracleMetric.textContent = `${Math.round(covered / Math.max(1, referenceCount()) * 100)}%`; oracleDelta.textContent = `${covered} / ${referenceCount()} ${material.averageStructureSites ? "average sites" : "atoms"} · target labels never used`;
    const gapTypes = learnedCover.molecular ? learnedCover.molecular.voidClasses : learnedCover.residualTypes.length + (learnedCover.voidBoundary?.classes || 0);
    reuseLabel.textContent = "REJECTED LINKS"; reuseMetric.textContent = String(discovery.cumulativeRejected); reuseDelta.textContent = finished
      ? `${gapTypes} explicit gap class${gapTypes === 1 ? "" : "es"} retained rather than hidden`
      : "failed recurrence / overlap consistency · removed";
    actionValue.textContent = finished ? `${learnedCover.placements.length} accepted placements` : `${discovery.tentative.length} edges under test`;
    domainValue.textContent = currentPbc().some(Boolean) ? "periodically extended full scene" : "finite full scene";
    energyValue.textContent = `${discovery.cumulativeRejected} removed`;
    resolverValue.textContent = finished ? `${clusterGalleryTypes().length} classes · complete cover` : "distance + angle + isometry + cover";
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
    if (material.growthWithheld) {
      renderConstraintLedger(null, "withheld");
      stageEyebrow.textContent = "search · occupational state unresolved";
      stageTitle.textContent = "Growth withheld until one ice-rule realization is supplied or sampled";
      phaseReadout.textContent = "average structure · no branch execution";
      captionAction.textContent = "The oxygen framework and D/vacancy alternatives remain visible, but no half-occupied site is treated as a simultaneous atom and no molecular assignment is invented.";
      atomLabel.textContent = "AVERAGE SITES";
      atomMetric.textContent = referenceCount().toLocaleString();
      atomDelta.textContent = `${material.occupancyWeightedAtomCount} occupancy-weighted atoms · unchanged input`;
      frontierLabel.textContent = "EXECUTABLE FRONTIER";
      frontierMetric.textContent = "0";
      frontierDelta.textContent = "unique D₂O realization unavailable";
      oracleLabel.textContent = "TARGET CALLS";
      oracleMetric.textContent = "0";
      oracleDelta.textContent = "growth not executed";
      reuseLabel.textContent = "CLAIM BOUNDARY";
      reuseMetric.textContent = "WITHHELD";
      reuseDelta.textContent = "occupancy ensemble required";
      updateOrderAudit();
      renderStack();
      renderMarkings();
      renderStructureStats();
      renderLegend();
      syncStageOptions();
      return;
    }
    if (iceAnchorTrace) {
      const nextWave = iceAnchorTrace.waves[iceAnchorWaveIndex];
      const emitted = atoms.length - iceAnchorTrace.seedAnchors;
      stageEyebrow.textContent = "search · sealed molecular-port continuation";
      stageTitle.textContent = `Grow shared oxygen anchors; retain ${iceAnchorTrace.orientationSpecies} poses symbolically`;
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
    hydrogen.append(hydrogenSwatch, document.createTextNode(`${iceAnchorTrace.orientationSpecies} · mutually exclusive pose hypotheses (not materialized)`));
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
    legendHeading.textContent = "Clustering decisions";
    [
      ["#84b8b2", "tentative · candidate connection under test"],
      ["#ff6d71", "rejected · flashes, then is removed"],
      ["#65e1bc", "settled · accepted molecular/support edge"],
      ["#ffc169", "settled gap · empty-region boundary"],
    ].forEach(([color, label]) => {
      const row = document.createElement("span");
      const swatch = document.createElement("i");
      swatch.className = "cluster-swatch";
      swatch.style.setProperty("--swatch", color);
      row.append(swatch, document.createTextNode(label));
      speciesLegend.appendChild(row);
    });
  } else {
    legendHeading.textContent = "Elements & state";
    currentMaterial().elements.forEach((symbol) => {
      const row = document.createElement("span");
      const swatch = document.createElement("i");
      swatch.className = "element-swatch";
      swatch.style.setProperty("--swatch", ELEMENTS[symbol].css);
      const occupational = occupationalAlternatives(symbol);
      if (occupational?.alternatives.length > 1) {
        const stops = occupational.alternatives.map((entry, index) => {
          const start = occupational.alternatives.slice(0, index).reduce((sum, item) => sum + item.fraction, 0) / occupational.total * 100;
          const end = (occupational.alternatives.slice(0, index + 1).reduce((sum, item) => sum + item.fraction, 0) / occupational.total) * 100;
          return `${elementRecord(entry.species).css} ${start}% ${end}%`;
        });
        swatch.style.background = `conic-gradient(${stops.join(",")})`;
      }
      row.append(swatch, document.createTextNode(occupational?.label || symbol));
      speciesLegend.appendChild(row);
    });
    const activeImportedValidation = activeImportedFrameValidation();
    if (activeImportedValidation?.thermalDisplacementSites) {
      const row = document.createElement("span");
      const swatch = document.createElement("i");
      swatch.className = "thermal-envelope-swatch";
      row.append(swatch, document.createTextNode(`2σ U/B displacement halo · ${activeImportedValidation.anisotropicDisplacementSites || 0} anisotropic · median σ ${activeImportedValidation.medianThermalSigmaA.toFixed(3)} Å`));
      speciesLegend.appendChild(row);
    }
    const proposal = document.createElement("span");
    const swatch = document.createElement("i"); swatch.className = "candidate";
    proposal.append(swatch, document.createTextNode("Proposal"));
    speciesLegend.appendChild(proposal);
    if (pipelineStage === 4 && initializedGrowthNuclei > 1) {
      const interfaceRow = document.createElement("span");
      const interfaceSwatch = document.createElement("i");
      interfaceSwatch.className = "cluster-swatch";
      interfaceSwatch.style.setProperty("--swatch", "#7ee1e8");
      interfaceRow.append(interfaceSwatch, document.createTextNode("cyan ring · exact cross-nucleus shared site"));
      speciesLegend.appendChild(interfaceRow);
    }
  }
}

function renderStack() {
  if (pipelineStage === 1 && clusterDiscoveryTrace) {
    const discovery = clusterDiscoveryState();
    stackDepth.textContent = `${clusterDiscoveryProgress}/${clusterDiscoveryTrace.totalSteps} discovery steps`;
    searchStack.replaceChildren();
    [
      ["?", `${discovery.tentative.length} candidate connections`, "test"],
      ["×", `${discovery.rejected.length} inconsistent connections`, "remove"],
      ["✓", `${discovery.settled.length} accepted support edges`, "keep"],
      ["C", `${discovery.settledPlacements} certified placements`, `${discovery.coveredAtoms.size} sites`],
    ].forEach(([symbol, actionText, stateText], index) => {
      const row = document.createElement("li");
      if (index === 1) row.className = "reject";
      const depth = document.createElement("b"); depth.textContent = symbol;
      const action = document.createElement("span"); action.textContent = actionText;
      const state = document.createElement("em"); state.textContent = stateText;
      row.append(depth, action, state); searchStack.appendChild(row);
    });
    return;
  }
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
    markCount.textContent = `${records.length} pairs · ${coordinationRecords.length} capacities · ${angularRecords.length} angles · ${coloredDistanceEnvelopes.frameCount} frame${coloredDistanceEnvelopes.frameCount === 1 ? "" : "s"}`;
    const p = document.createElement("p");
    p.textContent = coloredDistanceEnvelopes.frameCount > 1
      ? `Pair contacts, ordered coordination caps, and three-body angle bands pool ${coloredDistanceEnvelopes.atomPresentations.toLocaleString()} within-frame atom presentations. The selected frame alone supplies clusters and growth; no cross-frame pair, motif label, or potential is constructed.`
      : "Pair contacts, ordered coordination caps, and three-body angle bands are learned from positions; no motif labels or potential are supplied.";
    markingTable.appendChild(p);
    if (coloredDistanceEnvelopes.frameCount > 1) {
      const ensemble = document.createElement("div"); ensemble.className = "mark-row composition-reservoir-row";
      ensemble.title = "Raw snapshot presentations may be correlated; this is not an independent-sample or kinetic claim";
      const code = document.createElement("code"); code.textContent = "ensemble";
      const summary = document.createElement("span"); summary.textContent = `${coloredDistanceEnvelopes.frameCount} frames · σ₉₀ ${ensemblePairDistanceUncertainty?.upperPairDistanceSigma.toFixed(4) || "0.0000"} Å`;
      const count = document.createElement("b"); count.textContent = `${coloredDistanceEnvelopes.atomPresentations.toLocaleString()} sites`;
      ensemble.append(code, summary, count); markingTable.appendChild(ensemble);
    }
    const reservoir = document.createElement("div"); reservoir.className = "mark-row composition-reservoir-row";
    reservoir.title = "Observed global fractions are an optional soft frontier preference, never a hard surface constraint";
    const reservoirCode = document.createElement("code"); reservoirCode.textContent = "ratio";
    const reservoirRatio = document.createElement("span"); reservoirRatio.textContent = Object.entries(compositionTarget.reducedRatio)
      .map(([symbol, count]) => `${symbol}:${count}`).join(" · ");
    const reservoirCount = document.createElement("b"); reservoirCount.textContent = `N=${compositionTarget.observations}`;
    reservoir.append(reservoirCode, reservoirRatio, reservoirCount); markingTable.appendChild(reservoir);
    const chargeReservoir = document.createElement("div"); chargeReservoir.className = "mark-row composition-reservoir-row";
    chargeReservoir.title = "Formal oxidation states are used only when completely supplied; no electrostatic potential is inferred";
    const chargeCode = document.createElement("code"); chargeCode.textContent = "formal q";
    const chargeSummary = document.createElement("span"); chargeSummary.textContent = formalChargeTarget.available
      ? `q̄ ${formalChargeTarget.meanFormalCharge >= 0 ? "+" : ""}${formalChargeTarget.meanFormalCharge.toFixed(3)} · cell ${formalChargeTarget.netFormalCharge >= 0 ? "+" : ""}${formalChargeTarget.netFormalCharge.toFixed(3)}`
      : "unavailable · oxidation states not completely supplied";
    const chargeCoverage = document.createElement("b"); chargeCoverage.textContent = `${Math.round(formalChargeTarget.coverage * 100)}%`;
    chargeReservoir.append(chargeCode, chargeSummary, chargeCoverage); markingTable.appendChild(chargeReservoir);
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
    `×${cluster.observedOccurrences ?? cluster.classPlacementIndices?.length
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
  if (value && pipelineStage === 4 && currentMaterial().growthWithheld) value = false;
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
processTimelineInput.addEventListener("input", () => scrubProcessTimeline(processTimelineInput.value));
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
saveNotebookButton.addEventListener("click", () => {
  notebookClearArmed = false;
  clearNotebookButton.textContent = "Clear notebook";
  saveCurrentExperimentNotebookEntry();
});
clearNotebookButton.addEventListener("click", () => {
  if (!notebookClearArmed) {
    notebookClearArmed = true;
    clearNotebookButton.textContent = "Confirm clear";
    receiptStatus.textContent = "Click Confirm clear to remove all locally saved notebook summaries.";
    return;
  }
  experimentNotebookEntries = [];
  selectedNotebookEntryIds = [];
  notebookClearArmed = false;
  clearNotebookButton.textContent = "Clear notebook";
  try { localStorage.removeItem(EXPERIMENT_NOTEBOOK_STORAGE); } catch (_) { /* local state is already cleared */ }
  receiptStatus.textContent = "Experiment notebook cleared. Downloaded receipts are unaffected.";
  renderExperimentNotebook();
});
scenarioSelect.addEventListener("change", () => {
  renderEnsembleControls();
  renderIceViMicrostateControls();
  enterPipelineStage(0);
});
iceViMicrostateButton.addEventListener("click", () => {
  iceViMicrostateSeed++;
  iceViMicrostate = resolveIceViIceRuleMicrostate(iceViMicrostateSeed);
  orderPrototypeLibrary = null;
  renderIceViMicrostateControls();
  enterPipelineStage(0);
});
iceViAverageButton.addEventListener("click", () => {
  iceViMicrostate = null;
  orderPrototypeLibrary = null;
  renderIceViMicrostateControls();
  enterPipelineStage(0);
});
ensembleFrameSelect.addEventListener("change", () => {
  importedFrameIndex = Number(ensembleFrameSelect.value) || 0;
  syncImportedFrameMaterial();
  orderPrototypeLibrary = null;
  enterPipelineStage(0);
});
ensembleEvidenceSelect.addEventListener("change", () => {
  ensembleEvidenceMode = ensembleEvidenceSelect.value === "selected" ? "selected" : "all";
  enterPipelineStage(0);
});
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
loadEnsembleFixtureButton.addEventListener("click", async () => {
  try {
    importStatus.className = "import-status";
    importStatus.textContent = "Building a deterministic three-snapshot geometry ensemble…";
    const response = await fetch("./fixtures/nacl-64.extxyz");
    if (!response.ok) throw new Error(`fixture request returned ${response.status}`);
    const base = parseStructureText(await response.text(), "nacl-64.extxyz");
    activateImportedStructure(deterministicSnapshotEnsemble(base), "bundled deterministic NaCl snapshot ensemble");
  } catch (error) {
    importStatus.className = "import-status invalid";
    importStatus.textContent = `Ensemble fixture failed: ${error.message}`;
  }
});
confinementSelect.addEventListener("change", () => {
  growthProtocolMode = "custom";
  enterPipelineStage(pipelineStage);
});
growthProtocolSelect.addEventListener("change", () => applyGrowthProtocol(growthProtocolSelect.value));
growthSearchOptions.addEventListener("change", (event) => {
  if (event.target === growthProtocolSelect || !GROWTH_PROTOCOL_CONTROL_IDS.has(event.target.id)) return;
  growthProtocolMode = "custom";
  renderGrowthProtocolSummary();
});
geometryModeSelect.addEventListener("change", () => {
  geometryMode = geometryModeSelect.value;
  enterPipelineStage(1);
});
clusterToleranceSelect.addEventListener("change", () => {
  clusterToleranceMode = clusterToleranceSelect.value;
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
chargePreferenceSelect.addEventListener("change", () => {
  const value = chargePreferenceSelect.value;
  chargePreference = value === "none" || value === "strong" ? value : "auto";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
surfacePreferenceSelect.addEventListener("change", () => {
  const value = surfacePreferenceSelect.value;
  surfacePreference = value === "none" || value === "strong" ? value : "soft";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
frontMorphologySelect.addEventListener("change", () => {
  const value = frontMorphologySelect.value;
  frontMorphologyMode = ["smooth", "facet", "tip"].includes(value) ? value : "none";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
frontMorphologyWeightSelect.addEventListener("change", () => {
  const value = Number(frontMorphologyWeightSelect.value);
  frontMorphologyWeight = [.12, .24, .48].includes(value) ? value : .24;
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
epitaxyTemplateSelect.addEventListener("change", () => {
  const value = epitaxyTemplateSelect.value;
  epitaxyTemplateMode = ["square-coherent", "square-mismatch", "hex-coherent", "hex-mismatch", "hex-30"].includes(value)
    ? value : "none";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
epitaxyWeightSelect.addEventListener("change", () => {
  const value = Number(epitaxyWeightSelect.value);
  epitaxyWeight = [.12, .24, .48].includes(value) ? value : .24;
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
externalDriveSelect.addEventListener("change", () => {
  const value = externalDriveSelect.value;
  externalDriveMode = ["z-plus", "z-minus", "radial-out", "radial-in"].includes(value) ? value : "none";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
externalDriveWeightSelect.addEventListener("change", () => {
  const value = Number(externalDriveWeightSelect.value);
  externalDriveWeight = [.12, .24, .48].includes(value) ? value : .24;
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
affineLoadSelect.addEventListener("change", () => {
  const value = affineLoadSelect.value;
  affineLoadMode = ["hydro-compress", "hydro-tension", "z-tension", "xy-shear"].includes(value)
    ? value : "none";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
affineLoadMagnitudeSelect.addEventListener("change", () => {
  const value = Number(affineLoadMagnitudeSelect.value);
  affineLoadMagnitude = [.01, .02, .04].includes(value) ? value : .02;
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
robustnessPreferenceSelect.addEventListener("change", () => {
  robustnessPreference = robustnessPreferenceSelect.value === "margin" ? "margin" : "none";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
robustnessWeightSelect.addEventListener("change", () => {
  const value = Number(robustnessWeightSelect.value);
  robustnessWeight = [.12, .24, .48].includes(value) ? value : .24;
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
microstructureCouplingSelect.addEventListener("change", () => {
  const value = microstructureCouplingSelect.value;
  microstructureCouplingMode = ["gap-heal", "interface-follow", "anomaly-avoid", "occupancy-follow"].includes(value)
    ? value : "none";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
microstructureCouplingWeightSelect.addEventListener("change", () => {
  const value = Number(microstructureCouplingWeightSelect.value);
  microstructureCouplingWeight = [.12, .24, .48].includes(value) ? value : .24;
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
loopClosurePreferenceSelect.addEventListener("change", () => {
  loopClosurePreference = loopClosurePreferenceSelect.value === "consensus" ? "consensus" : "none";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
loopClosureWeightSelect.addEventListener("change", () => {
  const value = Number(loopClosureWeightSelect.value);
  loopClosureWeight = [.12, .24, .48].includes(value) ? value : .24;
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
arrivalPathSelect.addEventListener("change", () => {
  const value = arrivalPathSelect.value;
  arrivalPathMode = ["parent-outward", "radial-outward", "declared-drive"].includes(value)
    ? value : "none";
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
arrivalPathWeightSelect.addEventListener("change", () => {
  const value = Number(arrivalPathWeightSelect.value);
  arrivalPathWeight = [.12, .24, .48].includes(value) ? value : .24;
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
explorationScaleSelect.addEventListener("change", () => {
  const value = Number(explorationScaleSelect.value);
  geometricExplorationScale = [0, .05, .15, .35].includes(value) ? value : 0;
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
resampleGrowthButton.addEventListener("click", () => {
  if (geometricExplorationScale <= 0) return;
  growthPathSeed += 1;
  if (pipelineStage === 4) enterPipelineStage(4);
  else syncStageOptions();
});
growthNucleiSelect.addEventListener("change", () => {
  const value = Number(growthNucleiSelect.value);
  requestedGrowthNuclei = [1, 2, 4].includes(value) ? value : 1;
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
  growthProtocolMode = "custom";
  if (pipelineStage === 4) enterPipelineStage(4);
});
hierarchicalGrowthButton.addEventListener("click", () => {
  if (hierarchyEnabled) return;
  hierarchyEnabled = true;
  growthProtocolMode = "custom";
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
mdHorizonSelect.addEventListener("change", () => {
  const value = Number(mdHorizonSelect.value);
  mdHorizonSteps = [1000, 100000, 10000000].includes(value) ? value : 100000;
  renderComputationalCost();
});
mdScalingSelect.addEventListener("change", () => {
  mdWorkScaling = mdScalingSelect.value === "long-range" ? "long-range" : "local";
  renderComputationalCost();
});
[...growthMechanismProjection.querySelectorAll("[data-growth-projection]")].forEach((button) => button.addEventListener("click", () => {
  growthMechanismProjectionKey = button.dataset.growthProjection;
  growthMechanismProjection.querySelectorAll("[data-growth-projection]").forEach((candidate) =>
    candidate.setAttribute("aria-pressed", String(candidate === button)));
  drawGrowthMechanismMap();
}));
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
    if (pipelineStage === 1 || pipelineStage === 3) {
      eventAccumulator += delta * Number(speedInput.value);
      while (eventAccumulator >= 1) {
        eventAccumulator--;
        performEvent();
        if ((pipelineStage !== 1 && pipelineStage !== 3) || !playing) break;
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

function applyLaunchParameters() {
  const parameters = new URLSearchParams(window.location.search);
  const material = parameters.get("material");
  if (material && [...scenarioSelect.options].some((option) => option.value === material)) {
    scenarioSelect.value = material;
  }
  if (scenarioSelect.value === "iceVI" && parameters.has("microstate")) {
    const requested = Number.parseInt(parameters.get("microstate"), 10);
    iceViMicrostateSeed = Number.isInteger(requested) && requested > 0 ? requested : 1;
    iceViMicrostate = resolveIceViIceRuleMicrostate(iceViMicrostateSeed);
  }
  const requestedStage = Number.parseInt(parameters.get("stage"), 10);
  return Number.isInteger(requestedStage) ? Math.max(0, Math.min(4, requestedStage)) : 0;
}

restoreMarkingLibrary();
restoreExperimentNotebook();
renderExperimentNotebook();
buildPeriodicTable();
enterPipelineStage(applyLaunchParameters());
resize();
requestAnimationFrame(animate);
