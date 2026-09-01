import { executeIceMolecularAnchorGrowth } from "./ice-molecular-anchor-growth.js?v=20260901-419";
import { buildPeriodicIceIhBoundarySeries } from "./ice-periodic-boundary-audit.mjs?v=20260901-419";
import { A2_LAYERED_SIZE8_CANDIDATES } from "../../assets/a2-layered-size8-candidates.js?v=20260827-2";
import { A2_SLICED_SIZE7_CANDIDATES } from "../../assets/a2-sliced-size7-candidates.js?v=20260828-320";
import { buildHierarchyPhysicsTransport, HIERARCHY_TRANSPORT_STAGES }
  from "./hierarchy-physics-transport.mjs?v=20260901-419";
import { buildHierarchyPhysicsInvestigation }
  from "./hierarchy-physics-investigation.mjs?v=20260901-419";
import { buildHierarchyPhysicsProtocolPacket, hierarchyPhysicsProtocolShareUrl,
  hierarchyPhysicsProtocolSelectionFromSearch, hierarchyPhysicsProtocolPacketFilename }
  from "./hierarchy-physics-protocol-packet.mjs?v=20260901-419";
import { hierarchyPhysicsProtocolLaunchAuditFromPacket }
  from "./hierarchy-physics-execution-binding.mjs?v=20260901-419";

const byId = (id) => document.getElementById(id);
const A2_SLICED_SCALE3_OBSTRUCTIONS = A2_SLICED_SIZE7_CANDIDATES.filter((candidate) =>
  candidate.screening.three_copy_metatile_scale3_reflected_status
    === "no_three_copy_metatile_scalar3_substitution");
const A2_SLICED_SCALE3_PARENT_COUNT = A2_SLICED_SCALE3_OBSTRUCTIONS.reduce((sum, candidate) =>
  sum + candidate.screening.three_copy_metatile_scale3_reflected_parent_types, 0);
const A2_SLICED_SCALE4_OBSTRUCTIONS = A2_SLICED_SIZE7_CANDIDATES.filter((candidate) =>
  candidate.screening.three_copy_metatile_scale4_reflected_status
    === "no_three_copy_metatile_scalar4_substitution");
const A2_SLICED_SCALE4_PARENT_COUNT = A2_SLICED_SCALE4_OBSTRUCTIONS.reduce((sum, candidate) =>
  sum + candidate.screening.three_copy_metatile_scale4_reflected_parent_types, 0);
const A2_SLICED_FOUR_COPY_SCALE2_OBSTRUCTIONS = A2_SLICED_SIZE7_CANDIDATES.filter((candidate) =>
  candidate.screening.four_copy_metatile_scale2_reflected_status
    === "no_four_copy_metatile_scalar2_substitution");
const A2_SLICED_FOUR_COPY_SCALE2_PARENT_COUNT = A2_SLICED_FOUR_COPY_SCALE2_OBSTRUCTIONS
  .reduce((sum, candidate) => sum + candidate.screening.four_copy_metatile_scale2_reflected_parent_types, 0);
const a2SlicedShortIds = (candidates) => candidates.map((candidate) => candidate.id.split("_").at(-1));

const atlas = byId("evidenceAtlas");
const atlasButton = byId("evidenceAtlasButton");
const ribbonButton = byId("evidenceRibbonButton");
const closeButton = byId("evidenceAtlasClose");
const methodLink = byId("atlasMethodLink");
const hierarchyPhysicsTransportSelect = byId("hierarchyPhysicsTransportSelect");
const hierarchyPhysicsTransportSummary = byId("hierarchyPhysicsTransportSummary");
const hierarchyPhysicsTransportMatrix = byId("hierarchyPhysicsTransportMatrix");
const hierarchyPhysicsTransportDetail = byId("hierarchyPhysicsTransportDetail");
const hierarchyPhysicsTransportBoundary = byId("hierarchyPhysicsTransportBoundary");
const hierarchyPhysicsInvestigationState = byId("hierarchyPhysicsInvestigationState");
const hierarchyPhysicsInvestigationScales = byId("hierarchyPhysicsInvestigationScales");
const hierarchyPhysicsInvestigationQuestion = byId("hierarchyPhysicsInvestigationQuestion");
const hierarchyPhysicsInvestigationFlow = byId("hierarchyPhysicsInvestigationFlow");
const hierarchyPhysicsInvestigationGate = byId("hierarchyPhysicsInvestigationGate");
const hierarchyPhysicsInvestigationRoute = byId("hierarchyPhysicsInvestigationRoute");
const hierarchyPhysicsProtocolDigest = byId("hierarchyPhysicsProtocolDigest");
const hierarchyPhysicsProtocolStatus = byId("hierarchyPhysicsProtocolStatus");
const hierarchyPhysicsProtocolCopyLink = byId("hierarchyPhysicsProtocolCopyLink");
const hierarchyPhysicsProtocolCopyJson = byId("hierarchyPhysicsProtocolCopyJson");
const hierarchyPhysicsProtocolDownload = byId("hierarchyPhysicsProtocolDownload");
const hierarchyPhysicsProtocolConformanceRoute = byId("hierarchyPhysicsProtocolConformanceRoute");
let selectedHierarchyPhysicsChannel = "colored-geometry";
let selectedHierarchyPhysicsStage = "macro";
let activeHierarchyPhysicsInvestigation = null;
let activeHierarchyPhysicsProtocolPacket = null;
let hierarchyPhysicsProtocolRenderVersion = 0;
let sharedHierarchyPhysicsSelection = null;
let sharedHierarchyPhysicsLoadError = null;
try { sharedHierarchyPhysicsSelection = hierarchyPhysicsProtocolSelectionFromSearch(window.location.search); }
catch (error) { sharedHierarchyPhysicsLoadError = error; }

const ICE_PORT_ARTIFACT = await fetch(new URL(
  "./ice-molecular-port-artifact.json?v=20260824-1", import.meta.url)).then((response) => {
  if (!response.ok) throw new Error(`Cannot load frozen ice evidence: ${response.status}`);
  return response.json();
});
const ICE_ORIENTATION_MARKING_AUDIT = await fetch(new URL(
  "./ice-orientation-marking-artifact.json?v=20260901-419", import.meta.url)).then((response) => {
  if (!response.ok) throw new Error(`Cannot load frozen ice orientation-marking audit: ${response.status}`);
  return response.json();
});
const ICE_TRACES = Object.fromEntries(["iceIh", "iceIc"].map((caseId) =>
  [caseId, executeIceMolecularAnchorGrowth(ICE_PORT_ARTIFACT, caseId)]));
const ICE_PERIODIC_BOUNDARY_SERIES = buildPeriodicIceIhBoundarySeries();
const acceptedPerWave = (caseId) => ICE_TRACES[caseId].waves.map((wave) => wave.acceptedAnchors);

const SYSTEMS = {
  nacl: {
    short: "NaCl", kind: "periodic crystal", name: "NaCl rocksalt",
    summary: "The positive control for true stationary recursion. Positions and species are sufficient to recover three translations, a radix-two cell rule, eight child offsets, and a frozen directed-port certificate.",
    values: [2, 16, 128, 1024, 8192, 65536, 524288, 4194304], verifiedThrough: 7,
    metrics: [["learned scale", "2.000×"], ["child cells", "8"], ["strong witnesses", "1,478 / 750 / 86"], ["symbolic actions", "7 → 4.19m"]],
    verdict: ["proved", "Stationary colored production · exact scale and population substitution"],
    evidence: [
      ["Discovery", "3 recurrent generators", "No cell, axes, or space group supplied."],
      ["Frozen replay", "216 → 1,728 → 13,824", "Separate colored configurations replay exactly."],
      ["Port certificate", "8 children · 24 directed ports", "Two atom-disjoint macro occurrences; MDL saving 30."],
    ],
  },
  ice: {
    short: "H₂O ice", kind: "molecular crystal", name: "Ice Ih → Ice Ic",
    summary: "Ice is covered molecularly rather than by atom-centred coordination spokes. A bent H₂O motif, hydrogen-bond bridge polyhedra, and O₆ ring-boundary gap clusters cover the periodic configuration; a sealed eight-port grammar then transfers exact unseen oxygen anchors and audits every retained proton-orientation domain against the finite ice-rule graph.",
    values: [27, 27 + acceptedPerWave("iceIh")[0], 27 + acceptedPerWave("iceIh")[0] + acceptedPerWave("iceIh")[1]], verifiedThrough: 2,
    metrics: [["Ih isometry classes", "1 + 3 + 33"], ["Ic isometry classes", "1 + 2 + 39"],
      ["blind O frontiers", `Ih ${acceptedPerWave("iceIh").join(" → ")} · VI 4 → 3 → 1`],
      ["Ih ice-rule edges", `${ICE_TRACES.iceIh.orientationAudit.constrainedEdgesSatisfied} / ${ICE_TRACES.iceIh.orientationAudit.constrainedEdgesTotal}`],
      ["Ih H₂O poses", `${ICE_TRACES.iceIh.orientationAudit.resolvedAnchors} fixed · ${ICE_TRACES.iceIh.orientationAudit.ambiguousAnchors} symbolic`],
      ["Ih finite assignments", BigInt(ICE_TRACES.iceIh.orientationAudit.stateCountExact).toLocaleString()],
      ["open-boundary log Ω/N", ICE_TRACES.iceIh.orientationAudit.boundarySensitivity.finiteLogStatesPerMolecule.toFixed(3)]],
    verdict: ["progress", "Complete molecular cover and finite anchor transfer pass · proton and stationary growth remain open"],
    evidence: [
      ["Complete molecular cover", "Ih 216 / 216 · Ic 192 / 192", "H₂O molecules cover the atoms; bridge and O₆ ring-boundary clusters encode the interstitial connection geometry."],
      ["Frozen port fit", `${ICE_PORT_ARTIFACT.provenance.trainingMolecules} H₂O · ${ICE_PORT_ARTIFACT.ports.length} ports`, `${ICE_PORT_ARTIFACT.provenance.trainingAtoms} positions/species only; proper SE(3); target used = ${ICE_PORT_ARTIFACT.provenance.targetUsed}.`],
      ["Sealed finite execution", `Ih ${acceptedPerWave("iceIh").join(" → ")} · Ic ${acceptedPerWave("iceIc").join(" → ")}`, "Every accepted unseen oxygen anchor is exact; unsupported depth is rejected at a finite fixed point."],
      ["Finite proton constraint audit", `${ICE_TRACES.iceIh.orientationAudit.constrainedEdgesSatisfied} / ${ICE_TRACES.iceIh.orientationAudit.constrainedEdgesTotal} Ih edges · ${ICE_TRACES.iceIc.orientationAudit.constrainedEdgesSatisfied} / ${ICE_TRACES.iceIc.orientationAudit.constrainedEdgesTotal} Ic edges`, `Exactly one geometrically donated proton is possible on every observed O–O edge. The audit fixes ${ICE_TRACES.iceIh.orientationAudit.resolvedAnchors} / ${ICE_TRACES.iceIh.orientationAudit.anchors} Ih molecular poses; ${ICE_TRACES.iceIh.orientationAudit.ambiguousAnchors} remain symbolic because the finite boundary does not select a unique proton microstate.`],
      ["Exact finite state space", `${BigInt(ICE_TRACES.iceIh.orientationAudit.stateCountExact).toLocaleString()} Ih · ${BigInt(ICE_TRACES.iceIc.orientationAudit.stateCountExact).toLocaleString()} Ic`, `Exact factor elimination counts complete ice-rule assignments and pose marginals without treating the 4,096-state explicit preview cap as a count. log Ω is geometric finite-boundary degeneracy, not thermodynamic entropy.`],
      ["Open-boundary sensitivity", `log Ω/N ${ICE_TRACES.iceIh.orientationAudit.boundarySensitivity.finiteLogStatesPerMolecule.toFixed(3)} · Pauling ln(3/2) ${ICE_TRACES.iceIh.orientationAudit.boundarySensitivity.paulingReferenceLogStatesPerMolecule.toFixed(3)}`, `${ICE_TRACES.iceIh.orientationAudit.boundarySensitivity.boundaryLocalMarginalAmbiguity.ambiguousAnchors} / ${ICE_TRACES.iceIh.orientationAudit.boundarySensitivity.boundaryLocalMarginalAmbiguity.anchors} boundary domains remain ambiguous with mean local Hgeom ${ICE_TRACES.iceIh.orientationAudit.boundarySensitivity.boundaryLocalMarginalAmbiguity.meanEntropyNats.toFixed(3)} nats, versus ${ICE_TRACES.iceIh.orientationAudit.boundarySensitivity.interiorLocalMarginalAmbiguity.meanEntropyNats.toFixed(3)} for four-connected interior domains. These correlated uniform-assignment marginals are a boundary diagnostic, not an additive entropy decomposition or Boltzmann ensemble.`],
      ["Exact periodic closure series", ICE_PERIODIC_BOUNDARY_SERIES.map((audit) => `${audit.moleculeCount} H₂O: Ω ${BigInt(audit.exactAssignmentCount).toLocaleString()}`).join(" · "), `The browser rebuilds four declared Ice-Ih oxygen supercells from lattice geometry, verifies every oxygen has four periodic bonds, and exactly counts two-donor assignments with one proton per bond. The largest tractable interactive cell has ${ICE_PERIODIC_BOUNDARY_SERIES.at(-1).moleculeCount} molecules, no parallel-image bond pairs, and log Ω/N ${ICE_PERIODIC_BOUNDARY_SERIES.at(-1).logAssignmentsPerMolecule.toFixed(5)}. This is a finite-size closure comparison, not a bulk extrapolation or energy-weighted ensemble.`],
      ["Periodic proton-flux sectors", `${ICE_PERIODIC_BOUNDARY_SERIES.at(-1).fluxSectorCount} sectors · ${BigInt(ICE_PERIODIC_BOUNDARY_SERIES.at(-1).zeroFluxStateCount).toLocaleString()} / ${BigInt(ICE_PERIODIC_BOUNDARY_SERIES.at(-1).exactAssignmentCount).toLocaleString()} zero winding`, `All ${BigInt(ICE_PERIODIC_BOUNDARY_SERIES.at(-1).exactAssignmentCount).toLocaleString()} states are explicitly enumerated after the independent exact factor count, partitioned by net oriented periodic-image crossings, and checked under F↔−F inversion. Flux-sector multiplicity is a topology diagnostic under uniform combinatorial weighting—not polarization, dipole moment, energy, thermodynamic entropy, or a proton-growth trajectory.`],
      ["Uniform state-space information", `H(F) ${ICE_PERIODIC_BOUNDARY_SERIES.at(-1).fluxSectorEntropyNats.toFixed(3)} nats · exp H ${ICE_PERIODIC_BOUNDARY_SERIES.at(-1).effectiveFluxSectorCount.toFixed(1)} sectors`, `The exact microstate partition obeys ln Ω = H(F) + H(state|F). In the 2×2×1 cell, the flux label accounts for ${(100 * ICE_PERIODIC_BOUNDARY_SERIES.at(-1).fluxLabelInformationFraction).toFixed(2)}% of ln Ω and ${ICE_PERIODIC_BOUNDARY_SERIES.at(-1).conditionalMicrostateEntropyGivenFluxNats.toFixed(3)} nats remain inside sectors. These are Shannon information identities for equally counted geometric assignments, not Boltzmann weights, measured residual entropy, or a bulk-limit result.`],
      ["Disjoint pose-marking transfer", `${ICE_ORIENTATION_MARKING_AUDIT.arms.learned.exact} / ${ICE_ORIENTATION_MARKING_AUDIT.heldout.candidateDomains} exact · p=${ICE_ORIENTATION_MARKING_AUDIT.arms.shuffled.empiricalP}`, `The frozen local marking beats unmarked ${ICE_ORIENTATION_MARKING_AUDIT.arms.unmarked.exact} / ${ICE_ORIENTATION_MARKING_AUDIT.heldout.candidateDomains}, but ties the best of ${ICE_ORIENTATION_MARKING_AUDIT.arms.shuffled.count} label-shuffled refits. The true pose is present in only ${ICE_ORIENTATION_MARKING_AUDIT.heldout.exactSupplyDomains} / ${ICE_ORIENTATION_MARKING_AUDIT.heldout.targetMatchedDomains} exact-anchor domains; the marking gate remains red.`],
      ["Orientation-physics handoff", "global assignment request · fail closed", "The live growth card can export every retained H₂O geometry and binary ice-rule constraint at one declared thermodynamic/boundary state. A response must score complete global assignments, bind the immutable request, cover the declared state space, and separate one winner after uncertainty. Local pose energies cannot activate the marking."],
      ["Resolved claim boundary", "O anchors green · proton poses red", "Whole-H₂O continuation, clusters², stationary recurrence, and exponential ice growth are not claimed."],
      ["Disordered Ice VI transfer", "8 / 8 O anchors · 0 false", "A two-parent connection consensus selected on three training microstates transfers across a disjoint realization. All eight D₂O orientations stay symbolic; forced molecules make three site errors."],
    ],
    actions: [
      ["Inspect Ice Ih cover", "iceIh", 1],
      ["Inspect ordered Ice VIII cover", "iceVIII", 1],
      ["Inspect disordered Ice VI ambiguity", "iceVI", 1],
      ["Verify Ice VI growth is withheld", "iceVI", 4],
      ["Sample Ice VI and inspect D₂O clusters", "iceVI", 1, "resolve-ice-vi"],
      ["Replay Ice Ih anchor trace", "iceIh", 4],
      ["Replay Ih → Ic transfer", "iceIc", 4],
    ],
  },
  iqc: {
    short: "Ideal IQC", kind: "icosahedral quasicrystal", name: "Ideal icosahedral QC",
    summary: "The generic port/cover graph performs exact self-fed continuation and promotes larger recurrent supports. What it has not found is one exact chemistry–chirality–port production that repeats across three consecutive scales.",
    values: [507, 4923, 13847, 31521, 66935], verifiedThrough: 4,
    metrics: [["exact actions", "3+"], ["largest audited cloud", "66,935"], ["train hierarchy", "73→17→6→3→2→1"], ["stationary witnesses", "0"]],
    verdict: ["open", "Finite exact growth passes · generic stationary/exponential rule remains open"],
    evidence: [
      ["Generic VM", "31,521 exact sites", "One relational evaluator; no material-family dispatch."],
      ["Continuous section", "4 / 4 + 4 / 4 fresh", "Continuous port-state invariants rank both self-fed colored actions first."],
      ["Parallel section preflight", "57 / 216 · 48 / 216 pure bands", "No whole-action threshold reaches 95% group-heldout precision; the fresh antichain target stays sealed."],
      ["Carried obligations", "1 + 1 pure actions retained", "Future port-consensus features reach perfect precision only at one action per stage; the 18-action coverage gate stays red."],
      ["Explicit incidences", "8 / 9 connected paths · 0 / 16 exact", "Role vocabulary transfers at 97.4% mass, but connection closure alone selects structurally legal false branches."],
      ["Candidate section", "25 / 26 exact · 4 / 9 nuclei", "Adding the colored nearest-neighbor metric graph raises precision-qualified throughput, but four boundary families remain uncovered."],
      ["Geometry selection", "nested 41 / 65 · rank-two 16 / 18", "The reach/bin grid transfers on eight generic nuclei; the symmetry-centred nucleus remains an explicit red control."],
      ["Orbit-channel confirmation", "18 / 18 development → 0 / 2 reserved", "The frozen band-multiplicity selector fails on a disjoint preregistered nucleus; pose channels survive, orbit size as value does not."],
      ["Score-stack controls", "disagreement 18 / 20 · linear 0 / 20", "Cross-fitted scalar mixtures fail; the next marking must retain the joint incidence graph."],
      ["Joint incidence graph", "25,977 relational types · 15 / 20", "Role–shell and role–edge vocabulary transfers at 97.7%; independent edge weights still lose topology."],
      ["Message passing", "1 round 14 / 20 · 2 rounds 14 / 20", "Exact message colors fragment into 80k / 162k node types; a learned finite quotient is required."],
      ["Learned message readout", "16 / 20 integrated · p=.375", "A grouped ridge-logistic head wins two inner folds but reduces outer exact transfer; candidate geometry is unchanged and confirmation stays sealed."],
      ["Individual port paths", "9 / 9 exact paths exist · 5 / 9 selected", "Removing a double-counted child score exposes real joint-marking value, but four boundary environments remain unresolved."],
      ["Third-frontier value", "4 / 9 selected", "A 512-path target-free lookahead is worse than the corrected two-step mark; frontier supply is not the missing value."],
      ["Finite relational quotient", "362 states · wide ranks 3 / 1", "Canonical node/edge messages improve ordering but select no wide action; grouped-shuffle p=.96875."],
      ["Obligation automaton", "8 / 9 nuclei · 27 / 28 sites", "Weakest-link sequence scoring beats 31 grouped shuffles (p=.03125), but 47/102 states have one-group support and one nucleus fails."],
      ["Fresh automaton confirmation", "exact rank 5 · top 2 / 3", "A disjoint one-shot nucleus falsifies deployment; only 6.25–18.75% of transition states are recognized."],
      ["Disjoint obligation corpus", "20 nuclei · 303 branches", "Site yield beats all 31 shuffled controls (41 > 40; p=.03125), but exact top-action choice is 7 / 8 and fails its null (p=.125)."],
      ["Site-resolved development", "8 / 8 exact · 45 sites", "A k=7 weighted local section with mean whole-action aggregation beats all 31 complete grouped shuffles for both exact actions and site yield (p=.03125 each)."],
      ["Fresh site-section confirmation", "0 / 3 exact · 2 / 9 sites", "The preregistered maximin nucleus falsifies transfer: wave one has no exact action in the frozen portfolio; waves two and three each supply one, but the frozen marking selects neither."],
      ["Consumed supply diagnosis", "0 / 157 → 1 / 166", "No portfolio width can repair the old tree. Changing reach from 8→8→8 to 12→4→8 restores one exact terminal with fewer checks (356 vs 392), but old fusion/scalar ranks are 107/114."],
      ["Stage-local rollout development", "19 / 19 exact · 59 sites", "A bounded temporal connection section beats the connection-only order and every one of 31 grouped-label refits (max 18 exact / 58 sites; p=.03125 each)."],
      ["Rollout confirmation falsification", "marked 6 / 9 · baseline 6 / 9", "On a preregistered disjoint nucleus the mark replaces a 3/3 exact first baseline block with a 2/3 block. Zero marked blocks are exact, so transfer and sustained growth remain red."],
      ["Marking-library tree", "exact baseline head preserved", "Connection and rollout markings rank one immutable eight-action frontier. The portfolio retains both heads instead of letting the unconfirmed rollout value erase the exact connection action; a consumed three-block beam still has zero exact terminals."],
      ["Prefix channel portfolio", "raw exact path · autonomous 0", "A bounded 12→8→16 port reach contains a target-guided exact three-block path; the first missing correct port was rank 14/740. The frozen channel-diverse 8→16→32 marking retains two exact first blocks but zero exact second blocks, so transferable value remains red."],
      ["Fresh bounded clusters² supply", "410 exact · 47 / 168 prefixes", "A preregistered disjoint nucleus freezes 6,099 target-blind nine-action lineages before one target open. All eight parents supply exact continuations; geometry memoization saves 9,033 advances and meets the 1,200-second compute gate. Winner selection and stationary recursion remain open."],
      ["Clusters²", "6 positive quotient levels", "History-free re-clustering improves proof depth."],
      ["Frontier states", "336 / 368 sites", "Four heterogeneous multi-child rules are real, but no closed state matrix repeats across transitions."],
      ["Strict audit", "0 common three-level keys", "Topology, chemistry, chirality, ports, pose, and populations stay exact."],
    ],
  },
  cdyb: {
    short: "Cd–Yb", kind: "published real-material model", name: "Cd₅.₇Yb icosahedral QC",
    summary: "A published cut-and-project model supplies positions and species only; its hidden higher-dimensional coordinates never enter the learner. Local connection marking gives exact finite growth, while promoted vocabularies still fail to seed a stationary exterior rule on a disjoint nucleus.",
    values: [59, 237], verifiedThrough: 1,
    xLabels: ["sealed seed", "finite continuation"],
    curveEyebrow: "published-model finite continuation",
    curveTitle: "explicit sites before a conservative fixed point",
    curveNote: "finite target-blind growth · not a stationary projection",
    metrics: [["causal nuclei", "295 / 295 exact"], ["held-out hierarchy", "4 re-encoding levels"], ["site calibration", "207 / 211 nested"], ["obligation closure", "16 parents · 146 / 146"], ["spatial reserve", "81 / 81 · 11 parents"], ["stationary witnesses", "0"]],
    closureFunnel: {
      title: "Cd–Yb · whole-child value from development to spatial reserve",
      summary: "Select a stage to follow the representation change, exact parent promotion, and the present candidate-supply boundary.",
      steps: [
        ["isolated-site arm", 9, "A strict scalar cutoff commits 9 of 74 first-wave development obligations (8 correct) but closes no child. Fragment precision alone is not a growth action."],
        ["development children", 16, "A threshold fit above every negative whole child in the other four windows commits 16 complete, port-witnessed supports."],
        ["development sites", 146, "Those complete obligations emit 146 / 146 correct sites and self-feed in two of five development windows."],
        ["development parents", 16, "Every exact RHS re-verifies frozen ports and independently fits its promoted prototype in proper SE(3)."],
        ["reserved sites", 81, "Without refit, one consumed spatially disjoint reserve executes 4→4→3 sections and emits 81 / 81 correct sites. The other reserve supplies zero candidates."],
        ["reserved parents", 11, "Eleven children and parents close across three waves. Because these structural windows were previously observed by re-encoding audits, this is spatial transfer—not fresh confirmation."],
      ],
    },
    supplyAudit: {
      title: "Cd–Yb · the abstraction layer that loses candidate supply",
      summary: "Both R7 nuclei contain frozen recurring supports and hundreds of exact primitive-port continuations. Only one nucleus contains a support type promoted into a retained macro anchor.",
      reserves: [
        {
          label: "reserve A · anchor-starved", state: "open",
          steps: [
            ["seed atoms", 64, "The public R7 nucleus contains 64 colored sites."],
            ["recognized supports", 32, "Thirty-two exact occurrences span 17 frozen support types; primitive recognition is not the failure."],
            ["macro anchors", 0, "None of those 17 support types appears as a child in the 181 retained macro alternatives, so the proper-SE(3) frame loop has zero hypotheses."],
            ["whole candidates", 0, "With no retained child anchor, neither one-half nor one-third coverage can instantiate a macro pose."],
            ["promoted parents", 0, "No complete child or parent can be certified. The executor correctly stops rather than inventing an attachment."],
          ],
          primitive: { exact: 204, total: 345, sites: 292 },
          verdict: "Promotion lost locally useful roles: the frozen primitive port graph still supplies 204 exact actions, but 141 alternatives are inexact and no validated primitive ranker is installed.",
        },
        {
          label: "reserve B · executable", state: "progress",
          steps: [
            ["seed atoms", 64, "The second public R7 nucleus also begins from 64 colored sites."],
            ["recognized supports", 12, "Twelve exact occurrences span 10 frozen support types."],
            ["macro anchors", 4, "Four occurrences, from four support types, participate in retained macro alternatives and generate 25 proper-frame hypotheses."],
            ["whole candidates", 12, "Twelve complete-section candidates survive frozen ports, boundary, and collision checks."],
            ["promoted parents", 11, "The frozen marking commits 4→4→3 sections: 81/81 emitted sites are correct and 11 exact parents promote."],
          ],
          primitive: { exact: 134, total: 348, sites: 261 },
          verdict: "Where a retained macro anchor exists, the whole-child value transfers exactly. The remaining bottleneck is recurrent anchor coverage, not a looser child-fraction gate.",
        },
      ],
      coverage: "1/3 rejected · one wrong action + 10 wrong sites · 1/2 retained",
    },
    verdict: ["progress", "Real-material finite continuation passes · hierarchical transfer and stationarity remain open"],
    evidence: [
      ["Complete train cover", "2,385 / 2,385 atoms", "Five disjoint R14 windows learn 80 first-level types and explicit residual-complete representations from positions and species only."],
      ["Causal section", "178 / 178 + 117 / 117", "Bounded connection witnesses beat 31 ownership shuffles."],
      ["Deep hierarchy", "80→36→22→15→8→6→4→2→1", "Every later retained type is witnessed in at least two raw windows."],
      ["Frozen held-out hierarchy", "53/92→20/26→8/8→2/2", "Four exact re-encoding levels preserve IDs and ports; absent symbols stay dormant and residual atoms complete every representation."],
      ["Seed-only hierarchy", "276 primitive · 0 complete L1", "A disjoint 478-atom nucleus contains no complete promoted seed macro, so the exact hierarchy correctly refuses to start."],
      ["Partial promoted frontier", "82 candidates · 6 exact", "Finite one-child completions expose real policy headroom, but the train-only marking does not beat 31 within-parent shuffled refits."],
      ["Preregistered confirmation", "7 waves · 247 / 2,217 shell atoms", "The target-blind hierarchy self-feeds across four levels, yet the common first frontier contains no fully exact macro and both registered ranking gates remain red."],
      ["Site-resolved section", "207 / 211 · P 98.10%", "A deterministic four-window refit threshold is nonempty across all five outer folds (minimum P 95.92%) and beats shuffled retained-site yield, but it was devised on this corpus; future untouched confirmation remains sealed."],
      ["Group-sealed obligation execution", "146 / 146 sites · 16 parents", "A whole-child threshold fit outside each execution window closes 16 port-certified children and parents, self-feeding in two of five development windows. Geometry vocabulary is shared, so untouched transfer remains open."],
      ["Consumed spatial transfer", "81 / 81 sites · 11 parents", "The frozen final policy executes 4→4→3 sections in one reserved R14 window with no refit; the other has zero candidates. Exact value transfers where supply exists, but coverage and fresh confirmation remain open."],
      ["Candidate-supply diagnosis", "0 anchor types · 204 / 345 exact primitive", "The empty reserve recognizes 32 support occurrences but none belongs to a retained macro child type. Lowering child coverage is unsafe and cannot create a frame; exact primitive supply survives below promotion."],
      ["Stationary audit", "0 three-scale keys", "Finite growth and nine-level compression are not renamed sustained or exponential quasicrystal growth."],
    ],
    actions: [
      ["Open published Cd–Yb input", "cdyb", 0],
      ["Watch the irregular cover settle", "cdyb", 1],
      ["Inspect per-cluster GCTS sections", "cdyb", 3],
      ["Run the live finite frontier", "cdyb", 4],
    ],
  },
  glass: {
    short: "Glass", kind: "amorphous negative control", name: "Cu–Zr metallic glass",
    summary: "A complete finite cover is always possible, but a deterministic stationary production should not be hallucinated. The amorphous control is therefore successful when compression and recursive transfer are rejected.",
    values: [216], verifiedThrough: 0,
    metrics: [["complete representation", "yes + residuals"], ["stationary macros", "0"], ["deterministic continuation", "rejected"], ["correct target", "ensemble statistics"]],
    verdict: ["control", "Negative control passes by refusing a false exponential grammar"],
    evidence: [
      ["Local structure", "motifs are allowed", "Short-range order is not confused with global determinism."],
      ["Recursion", "stationarity rejected", "No copied patch is promoted forever from one observation."],
      ["Evaluation", "RDF + S(q) + motif statistics", "A glass target is an ensemble, not one privileged continuation."],
    ],
  },
  a2: {
    short: "A₂ exact", kind: "exact layer-essential geometry tests", name: "A₂ layer-essential lattice functions",
    summary: `Two independent finite catalogs test whether exact weighted periodic screens, replayed coronas, and bounded GCTS obstruction clauses can narrow difficult geometric families without overclaiming non-tiling or aperiodicity. Four size-eight layered candidates remain exact through seven copies; eight size-seven sliced candidates have complete radius-two patches and bounded three-copy obstructions at scales three and four, while ${a2SlicedShortIds(A2_SLICED_FOUR_COPY_SCALE2_OBSTRUCTIONS).join(" · ") || "no candidate"} also has a complete four-copy scale-two obstruction.`,
    values: [4940, 411, 6, 4], verifiedThrough: 3,
    xLabels: ["census", "after 1-copy", "after 2-copy", "after 4-copy"],
    curveEyebrow: "exact survivor funnel",
    curveTitle: "layer-essential size-eight screening",
    curveObserved: "independently replayed exact screens",
    curveProjected: "larger periodic domains remain open",
    curveNote: "4,940 → 411 → 6 → 4 · zero solver unknowns",
    metrics: [["layered size-8 census", "4,940 → 4"], ["sliced size-7 census", "1,112 → 8 focused"], ["size-7 radius-2 patches", "8 / 8 complete"], ["3-copy scale-3 / 4", `${A2_SLICED_SCALE3_OBSTRUCTIONS.length}/${A2_SLICED_SCALE4_OBSTRUCTIONS.length} obstructed`], ["4-copy scale-2", `${A2_SLICED_FOUR_COPY_SCALE2_OBSTRUCTIONS.length} obstructed · ${A2_SLICED_SIZE7_CANDIDATES.length - A2_SLICED_FOUR_COPY_SCALE2_OBSTRUCTIONS.length} open`]],
    verdict: ["open", "Finite periodic and corona evidence is exact · every global classification remains unresolved"],
    evidence: [
      ["Periodic funnel", "4,529 + 405 + 2 certified", "Exact weighted quotients remove 4,936 of 4,940 shapes before the surviving frontier. Each survivor then exhausts all 1,995 seven-copy HNF bases with zero solver unknowns; two use 32 complete meet-in-the-middle fallbacks apiece."],
      ["Root corona", "24 / 29 / 30 / 27 copies", "Each of the four exact-through-seven survivors has an independently replayed complete first corona."],
      ["GCTS marking", "16 / 72 / 72 / 62 clauses", "Sound obstruction clauses prune first-corona families, but none of the four outer first-corona spaces is exhausted."],
      ["Substitution screen", "2…8 · 49 anisotropic pairs", "Direct scalar and layer-anisotropic rules are excluded, together with connected two- and three-copy metatile alphabets at scales 2 and 3."],
      ["Sliced size-seven frontier", "8 complete radius-two patches", "The focused consecutive-layer candidates contain 190–252 copies in their exact radius-two patches. Uniform radius-three GCTS runs retain 759 sound failure clauses and 731 first-corona clauses, but every search stops at a declared round or solver limit."],
      ["Cluster substitution obstructions", `17 bounded grammars · ${(A2_SLICED_SCALE3_PARENT_COUNT + A2_SLICED_SCALE4_PARENT_COUNT + A2_SLICED_FOUR_COPY_SCALE2_PARENT_COUNT).toLocaleString()} parent tests`, `Complete proper/reflected three-copy searches certify no substitution at scale three and four for all eight focused candidates. A separate four-copy scale-two search exhausts ${A2_SLICED_FOUR_COPY_SCALE2_PARENT_COUNT.toLocaleString()} parents for ${a2SlicedShortIds(A2_SLICED_FOUR_COPY_SCALE2_OBSTRUCTIONS).join(" · ")}; the other seven four-copy screens remain explicitly unrun or unresolved. These results rule out seventeen bounded cluster grammars, not every substitution or global tiling.`],
      ["Claim boundary", "4 unresolved", "Larger periodic domains, complete second-corona searches, and general substitutions remain open. Exact-through-seven is not a proof of non-tiling or aperiodicity."],
    ],
  },
};

const MATRIX = [
  ["NaCl crystal", ["pass", "100% colored cover"], ["pass", "2 exact unseen levels"], ["pass", "8-child cell macro"], ["pass", "4.19m / 7 actions"]],
  ["H₂O ice", ["pass", "Ih 216 · Ic 192"], ["pass", "16→8 · 12 exact O"], ["open", "no promoted ice rule"], ["open", "finite fixed point"]],
  ["Ideal IQC", ["pass", "2,064 / 2,064"], ["pass", "31,521 exact sites"], ["progress", "6 train levels"], ["open", "no 3-scale key"]],
  ["Cd₅.₇Yb IQC", ["pass", "2,385 / 2,385"], ["pass", "295 / 295 local"], ["progress", "9 train · 4 replay"], ["open", "no stationary key"]],
  ["Cu–Zr glass", ["control", "cover + residuals"], ["control", "not uniquely defined"], ["control", "recursion rejected"], ["control", "negative passes"]],
  ["A₂ geometry test", ["pass", "4,940 exact census"], ["pass", "4 root coronas"], ["progress", "exact through 6"], ["open", "4 unresolved"]],
];

const MATRIX_DETAILS = {
  "NaCl crystal": "The learner receives neither the unit cell nor Fm-3m. A positions-only discovery proposes the radix and offsets; the independently learned proper-port graph must witness the same eight-child production at three scales before the stationary gate turns green.",
  "H₂O ice": "The periodic ice configurations are not reduced to atom-centred shells. One bent H₂O class covers each molecule; decorated hydrogen-bond bridges and O₆ ring boundaries encode connections and fill the periodically extended cover. Eight proper-SE(3) ports learned on 201 Ih atoms emit exact disjoint oxygen frontiers, but mutually exclusive proton orientations are still symbolic, so clusters² and stationary growth remain red.",
  "Ideal IQC": "Exact continuation is real and self-fed, but different promoted productions appear at successive levels. Deep compression is not renamed exponential growth: the strict stationary audit requires the same exact semantic production and learned scale twice in succession.",
  "Cd₅.₇Yb IQC": "The real-material model is the hardest transfer case. Bounded local marking succeeds for finite primitive growth, but exact promoted clusters are sparse and nucleus-dependent. Dormant types remain frozen rather than being refit on held-out atoms.",
  "Cu–Zr glass": "The negative control protects the benchmark from a trivial answer. Residual clusters guarantee representation, but no stable macro production, unique exterior continuation, or million-site symbolic claim is admitted.",
  "A₂ geometry test": `This is not an atomic material claim. It isolates exact geometric screening and GCTS marking on two layer-essential lattice-function families: weighted periodic quotients narrow the 4,940-shape layered census to four exact-through-seven survivors, while eight focused consecutive-layer size-seven supports have complete radius-two patches and ${A2_SLICED_SCALE3_OBSTRUCTIONS.length} bounded scale-three cluster obstructions. Local obstruction clauses are never renamed non-tiling, aperiodicity, or material growth.`,
};

const ANATOMY = {
  cover: ["Complete, irregular cluster cover", "Frequent colored point-set isometries are found without requiring an atom at the centre or a fixed-radius sphere. A deterministic cover records overlaps, while every uncovered connected component becomes an explicit residual cluster. Coverage is therefore exact and compression remains falsifiable.", ["species + xyz only", "proper rotations", "gaps stay explicit"]],
  ports: ["Finite connection vocabulary", "Each witnessed neighboring or overlapping placement is expressed in the parent cluster frame and quotiented by the proper symmetry groups of both clusters. Reflections, unlike-species coincidences, and sub-minimum-distance collisions are rejected.", ["SE(3), never O(3)", "overlap chemistry", "boundary slots"]],
  mark: ["A local section over connections", "The marking is not an energy surface. It is a bounded function of already present incident ports and local compatibility evidence. It ranks the same frozen exact actions seen by every baseline and shuffled control.", ["incoming order ≤ 2", "no target atoms", "identical candidates"]],
  search: ["Tree search with parallel visible moves", "Under the hood, every placement is a branch decision with rejection and rollback accounting. On screen, candidates that commute—different frontier sides with no conflicts—are committed as one antichain, so update order does not create a fake physical sequence.", ["whole clusters", "pairwise compatibility", "proposal work counted"]],
  promote: ["Clusters become atoms of the next grammar", "Accepted or re-clustered unions are canonicalized as new proper-SE(3) prototypes. Their internal ports become edges and exposed ports become the next frontier. Stationarity is claimed only if one exact production recurs across three levels with equal learned scales and population substitutions.", ["history-free option", "positive MDL", "strict recurrence gate"]],
};

const PHYSICS_MAP = {
  bonding: {
    status: "proved", label: "bonding + coordination", title: "Bonding topology becomes a colored metric cover",
    physical: "Element identity, optionally supplied formal oxidation state, bond-length neighborhoods, coordination, bond angles, molecular membership, bulk composition, and recurring local polyhedra already present in the supplied configuration.",
    geometric: "Complete colored supports are augmented by species-pair exclusions, ordered coordination caps, separated three-body angle bands, an arbitrary-component composition reservoir, and—only when completely supplied—a formal-charge reservoir. Supports may be irregular, centre-free, and overlapping.",
    growth: "Hard geometry rejects collisions, oversaturation, and forbidden observed-angle gaps. Optional soft strain, composition, and formal-charge bookkeeping rank the same frozen actions without changing their coordinates.",
    boundary: "The soft scores are not energies or chemical potentials. Formal oxidation states may be preserved as input labels; no charge density, electrostatic energy, inferred oxidation state, bond order, electronic free energy, force, temperature, or reaction barrier is evaluated.",
    systems: [
      ["NaCl", "1:1 octahedral coordination", "Na–Cl exclusions · z≤6 · 90°∪180° · 1:1 reservoir", "Coulomb energy and phonons omitted"],
      ["H₂O ice", "Bent H₂O + tetrahedral O network", "O→H≤2 · H→O≤1 · bent/tetrahedral bands · H₂O reservoir", "Proton energetics unresolved"],
      ["Ideal IQC", "Recurring decorated local environments", "Irregular supports + colored many-body envelopes + finite ports", "Model interaction omitted"],
      ["Cd–Yb", "Published decorated atomic packing", "Positions/species-only envelopes and Cd:Yb reservoir", "No cut/project labels or metallic potential"],
      ["Cu–Zr glass", "Broad short-range distributions", "Wide learned bands + residuals; no forced recurrence", "No unique continuation claimed"],
    ],
  },
  orientation: {
    status: "progress", label: "orientation + chirality", title: "Directional chemistry becomes a finite proper-pose vocabulary",
    physical: "Molecular orientation, directional hydrogen bonds, coordination-polyhedron pose, and chiral local arrangements.",
    geometric: "Every occurrence is registered by a proper SE(3) pose and quotiented only by the cluster's learned proper symmetry. Reflections remain distinct when chirality is present.",
    growth: "Incoming and outgoing port incidences constrain which orientation alternatives can attach. The marking may rank alternatives but cannot alter their frozen geometry.",
    boundary: "Ice oxygen anchors transfer exactly, but competing H₂O proton orientations remain symbolic. Rotational kinetics and orientational entropy are not yet modeled.",
    systems: [
      ["NaCl", "One octahedral orientation orbit", "24 proper symmetries collapse equivalent ports", "Null orientation control"],
      ["H₂O ice", "Two-donor / two-acceptor pose domains", "8 Ih-fitted ports + parent-domain unanimity", "Full proton assignment open"],
      ["Ideal IQC", "Many off-lattice proper poses", "Pose × port incidence channels", "Transferable winner still incomplete"],
      ["Cd–Yb", "Decorated shell orientation", "Proper-SE(3) local connection section", "Stationary pose rule absent"],
      ["Cu–Zr glass", "Broad local pose distribution", "No forced global orientation grammar", "Correct negative behavior"],
    ],
  },
  order: {
    status: "progress", label: "long-range order", title: "Lattice, module, or metric order is inferred—not prescribed",
    physical: "Periodic translation order, aperiodic long-range coherence, chemical sublattice order, two-dimensional layers, and the absence of a unique amorphous continuation.",
    geometric: "Auto mode tests a translation lattice, a finite-rank module, or an unrestricted metric point set. Local ports remain proper-SE(3) objects in every mode. Reciprocal-space inspection decomposes the finite Debye sum into unit number density, selected chemistry-token sublattices, constant-Z low-q proxy, or composition-centered Z contrast.",
    growth: "Repeated productions may be promoted across scales. Exponential representation requires the same exact production and learned scale over three consecutive levels. All reciprocal-space channels remain posthoc evidence and never rank a branch.",
    boundary: "Deep compression alone is not stationarity. The ideal and Cd–Yb quasicrystals still have zero certified three-scale stationary productions. Constant Z is not a q-dependent atomic form factor; no neutron length, occupancy-weighted amplitude, anomalous term, Debye–Waller damping, or instrument response is used.",
    systems: [
      ["NaCl", "Periodic translation group", "Learned radix-2, 8-child rule", "Stationary gate green"],
      ["H₂O ice", "Periodic oxygen network", "Finite molecular-port continuation", "Promoted ice recurrence open"],
      ["Ideal IQC", "Aperiodic coherent order", "Off-lattice ports + six train levels", "No common three-scale key"],
      ["Cd–Yb", "Published icosahedral QC model", "Nine positive compression levels", "Held-out exterior stationarity open"],
      ["Cu–Zr glass", "No deterministic long-range order", "Stationary recursion rejected", "Negative gate green"],
    ],
  },
  defects: {
    status: "proved", label: "voids + defects", title: "Missing space remains an explicit geometric object",
    physical: "Voids, interstitial boundaries, vacancies, incomplete crop boundaries, layer separation, local incompatibilities, current-state contact/angle mismatch, and localized coherent/non-affine deformation between supplied snapshots.",
    geometric: "Uncovered connected components become residual clusters; failed overlap tests become rejection evidence. Every current site can be compared with frozen colored contact-length, separated angle-mode, and ordered coordination envelopes without atom identity across time. For paired fixed-topology structures, a Falk–Langer affine map additionally separates Green–Lagrange shear/dilation from √D²min residual motion and kNN exchange.",
    growth: "The search cannot silently drop uncovered atoms or accept a partial child as complete. The current-state mismatch map and paired deformation microscope are posthoc: they color sample-relative compatibility, surface shortfall, coherent shear, dilation, residual motion, or neighbor exchange without changing a branch.",
    boundary: "A residual guarantees complete representation, not stability; coordination shortfall can simply be a free surface. Current geometric mismatch is not frustration energy, stress, or a defect label. Local F and D²min are kinematic snapshot differences—not modulus, elastic or defect energy, plasticity identity, kinetics, or time. Rank-deficient cages withhold 3D strain.",
    systems: [
      ["NaCl", "Crop and cover boundaries", "Exact residual terminals", "No defect thermodynamics"],
      ["H₂O ice", "O₆ interstitial ring regions", "33 Ih / 39 Ic gap-boundary classes", "No vacancy relaxation"],
      ["Ideal IQC", "Irregular uncovered components", "Gap clusters retained at every hierarchy", "Compression remains falsifiable"],
      ["Cd–Yb", "Dormant held-out symbols", "Exact residual-complete re-encoding", "Novel types fail closed"],
      ["Cu–Zr glass", "Nonrecurring local environments", "Residuals preserve every atom", "No fake grammar"],
    ],
  },
  kinetics: {
    status: "progress", label: "thermodynamics + kinetics", title: "Equilibrium habit, kinetic habit, spatial supply, rate control, and exact events stay distinct",
    physical: "The portal distinguishes interfacial free energy γ(n̂), bulk parent-to-nucleus driving-force density Δg, steady normal interface velocity v(n̂) at one declared driving condition, spatially resolved net incorporation flux J(x,n̂) over one frozen interface, and candidate-resolved transition-state barriers/prefactors. Exact local handoffs bind each response to one structure, interface/frame, method, settings digest, boundary condition, and uncertainty contract. When J and v additionally share one coupling-state digest, a periodic site density converts J to a supply-equivalent velocity and resolves only nonoverlapping three-sigma rate-control regimes. A separate work-bound nucleation handoff may accept independently calculated site density, Zeldovich factor, and critical-nucleus attachment frequency; only then does it expose a conditional steady-state homogeneous rate density. A schedule-bound handoff may accept a committor-validated species-labelled critical configuration; a separate proper-SE(3) frozen-grammar cover, port, collision, and boundary gate can explicitly stage that representative as a local GCTS seed. Reversible finite event histories may audit local grand-canonical balance, observed rate cycles, competing finite pathways, and a finite ΔΩ(N) profile.",
    geometric: "Validated γ(n̂) builds an equilibrium Wulff envelope and may regularize finite-nucleus support mismatch. A separately validated positive Δg, bound to that exact γ response and thermodynamic state, supplies a conditional homothetic capillarity-work profile with a critical Wulff scale and barrier—but the barrier alone never becomes a rate. When explicitly enabled, the action bridge freezes the pre-candidate Wulff center and ranks the identical frontier by ΔΔG = Δ[Cγs^(d−1) − ΔgV₀s^d]; unsupported orientations abstain and no coordinates or hard gates change. Independently supplied ρsite, Z, and f⁺ may evaluate J=ρsite Z f⁺ exp(−ΔG*/kBT) plus a selectable finite Poisson observation window. A declared seed can then freeze homogeneous event times and normalized 2D/3D positions; those points contain no atomistic nucleus or crystallographic pose. Independently validated v(n̂) builds a kinetic-Wulff envelope. A validated J(x,n̂) quadrature resolves nonuniform substrate supply, depletion, or shadowing and may rank the same exact frontier by compact spatial/normal flux contrast. The diagnostic bridge plots log10[J/(ρsite v)] patch by patch but adds no third score. Candidate-specific barriers remain attached to exact action IDs rather than being inferred from any envelope or field.",
    growth: "Tree search still leap-frogs between hard-certified structural states. Equilibrium-shape, orientation-speed, local-supply, or exact event-rate evidence can order one immutable candidate catalog only after explicit validation; proposal checks and backtracks remain computational work. Seeded CNT event points remain outside the atomic growth state until a separate atomistic nucleus-construction handoff exists, while a GCTS leap receives physical time only from a complete finite HTST action catalog with declared temperature and prefactors.",
    boundary: "One finite orientation set is not a complete equilibrium or kinetic habit; one steady velocity field does not transfer across driving state; and one flux map must be recalculated as its frozen interface or transport boundary changes. Morphology supplies none of γ, Δg, v, or J; γ does not supply v or Δg; geometric visibility is not diffusion. Conditional capillarity omits heterogeneous wetting, elastic/strain energy, diffuse interfaces, curvature corrections, atom counts, and nonclassical pathways. The optional CNT rate still assumes one steady homogeneous reaction coordinate and supplied kinetic factors; its Poisson window is not an observed induction time, depletion model, spatial correlation, or GCTS clock. Comparing J/ρsite with v does not justify adding inverse resistances or inferring an effective rate. These priors are not attachment probabilities, complete moving-boundary solutions, or universal phase diagrams.",
    systems: [
      ["NaCl", "Exact structural recurrence", "Symbolic scale leap + optional external habit evidence", "No universal growth time"],
      ["H₂O ice", "Ice-rule-compatible scaffold", "Exact finite O-anchor leap", "No proton barrier or entropy"],
      ["Ideal IQC", "Geometric finite continuation", "Target-blind tree execution", "No formation free energy"],
      ["Cd–Yb", "Real-model structural continuation", "Causal local mark", "No metallic kinetics"],
      ["Cu–Zr glass", "Ensemble structural statistics", "RDF / S(q) / motif evaluation", "No unique trajectory"],
    ],
  },
};

const TIMELINE = [
  ["01", "Complete covers", "Atom-centred shells were replaced by irregular repeated supports, exact overlap covers, and explicit residual gap clusters.", "proved"],
  ["02", "Oriented ports", "Connection identity became a finite double orbit of proper cluster symmetries with colored overlap witnesses.", "proved"],
  ["03", "Causal frontier", "Held-out atoms were removed from branch choice; targets are opened only after frozen candidate traces exist.", "proved"],
  ["04", "Parallel growth", "Compatible whole-cluster moves became antichains over an underlying tree search, preserving order independence.", "proved"],
  ["05", "Clusters of clusters", "Sparse port graphs and exact MDL mining promoted recurring connected unions into higher-level prototypes.", "proved"],
  ["06", "Crystal stationarity", "NaCl produced an independently witnessed eight-child rule at three scales and crossed the symbolic million-site gate.", "proved"],
  ["07", "Quasicrystal continuation", "Ideal IQC and published Cd–Yb systems achieved exact, self-fed finite growth with causal local markings.", "progress"],
  ["08", "History-free hierarchy", "Re-clustering generated deeper IQC and nine-level Cd–Yb compression without encoding action order as geometry.", "progress"],
  ["09", "Site-resolved completion", "Partial macro sites now remain explicit obligations; no child or parent exists until its full colored support and ports verify.", "proved"],
  ["10", "Vector frontier substitutions", "Global one-owner matching learns and executes A→AB, B→A with spectral growth φ; the real IQC still has no closed recurrent matrix.", "progress"],
  ["11", "Continuous port-state section", "Adding invariant parent/source connection statistics makes both fresh self-fed actions rank first: 4 / 4 plus 4 / 4 exact colored sites.", "proved"],
  ["12", "Whole-action calibration", "Absolute pure thresholds select 50 and 24 training sites but transfer no actions; a 15-feature band section also fails the 95% group-heldout precision preflight.", "open"],
  ["13", "Carried obligations", "One-step successor-port summaries isolate one pure seed and one pure self-fed action, but fail the predeclared two-actions-per-nucleus aggregate coverage gate.", "progress"],
  ["14", "Explicit port incidence", "Bounded backtracking finds two-action connected paths on 8 / 9 held-out nuclei, but all 16 selected actions are false; role closure is necessary, not sufficient.", "progress"],
  ["15", "Candidate-level section", "Adding the colored nearest-neighbor metric graph to individual pose–port descriptors yields 25 / 26 exact compatible placements across four of nine nuclei.", "progress"],
  ["15b", "Nested geometry selection", "The same action graph tests one/two/three-shell coarse/fine sections. Nested thresholds drift to 41 / 65; fixed top-two ranking is 16 / 18 and fails only the symmetry-centred nucleus.", "progress"],
  ["15c", "Orbit-channel falsification", "A symmetry-normalized channel view plus a target-free orbit-size selector is 18 / 18 in development, then 0 / 2 on its committed disjoint confirmation. Orbit multiplicity is rejected as value.", "open"],
  ["15d", "Scalar-stack rejection", "With the consumed target now development-only, disagreement scoring reaches 18 / 20 and a fully nested 15-feature linear stack reaches 0 / 20. Joint incidence geometry is the remaining target.", "open"],
  ["15e", "Joint incidence graph", "Explicit role–shell and role–metric-edge types transfer at 97.7%, but marginal edge scoring reaches only 15 / 20. Finite subgraph topology is the next section.", "progress"],
  ["15f", "Message-color fragmentation", "One and two bounded graph-message rounds each reach 14 / 20; 80k / 162k exact node colors show why the next operation must be a learned quotient.", "open"],
  ["15g", "Learned readout rejection", "A group-sealed scalar head over bounded messages is admitted in two folds but lowers the outer result to 16 / 20 exact paths; learned equivariant updates remain open.", "open"],
  ["16", "Individual port paths", "Every nucleus contains exact two-step root→child paths in a fixed target-free supply. Correcting score composition raises heldout selection from 0 / 9 to 5 / 9.", "progress"],
  ["17", "Third-frontier control", "A fixed 512-path shortlist contains exact alternatives in every nucleus, but outgoing-frontier valuation falls to 4 / 9 and is rejected.", "progress"],
  ["17b", "Simultaneous port cover", "Exhaustive SAT/UNSAT/UNKNOWN search catches conflicting marginal controls, but all 120 real IQC branches satisfy the coarse role cover. Exact finite port-instance incidence is now the open representation.", "progress"],
  ["17c", "Exact port instances", "Preserving ordered parent→source incidence makes forward continuation reject 26 / 61 false branches while retaining 57 / 59 exact. One supplied nucleus loses exact supply, so boundary-conditioned backoff remains open.", "progress"],
  ["17d", "Boundary backoff falsification", "A six-feature, group-heldout scalar backoff restores 59 / 59 exact branches and all 9 nuclei while still rejecting 8 false branches. Every one of 31 within-nucleus label shuffles ties it (p = 1), so it remains a descriptive defer rule—not a learned marking.", "open"],
  ["17e", "Complete branch graph", "The unordered colored metric graph distinguishes all 28 forward-UNSAT branches locally, but 119 / 120 graphs are unique. Nearest-graph and recurrent-edge sections each recover 0 / 2 exact nuclei; identifiability is not transferable value.", "open"],
  ["17f", "External recurrent value", "A closed-ball-disjoint 29-nucleus corpus improves wide fallback recovery to 1 / 2, but the second exact branch ranks tenth, supply stays 8 / 9, and all 31 grouped label shuffles tie (p = 1). The nine scalar branch features are rejected as the missing quotient.", "open"],
  ["17g", "Geometry-complete macro quotient", "Seventeen wide-disjoint nuclei freeze 168 three-action occurrences with exact colored proper-SE(3) nodes and 158 port derivations. The selected quotient reaches 7 / 9 supplied development nuclei at 63.6% precision (p = .4375), then selects 0 / 2 exact and two false branches on the unchanged wide set. Triangle geometry is rejected; a shared port-incidence graph is next.", "open"],
  ["17h", "Shared port-incidence graph", "The 168 development and 120 unchanged wide branches now use one ID-free colored node / directed-port / endpoint-incidence schema. A strict recurrent quotient is 4 / 9 at 100% development precision, but recognizes only 1 / 28 wide fallback candidates and neither exact branch; it correctly selects nothing. Exact schema alignment is proved, transferable graph similarity remains open.", "progress"],
  ["17i", "Continuous port-graph metric", "A group-balanced 92-feature graph metric separates action shape, port roles, pose, environment, and endpoint incidence. Train selection keeps only pose+incidence and reaches 6 / 9 at 100% precision, but grouped shuffles reach 7 (p = .46875). Wide exact branches rank fifth and second; no action clears threshold. The metric is rejected as value.", "open"],
  ["17j", "Finite relational message quotient", "Three canonical action nodes and three incidence edges produce 216 bounded measurements and 362 recurrent train states. The selected node-message rule is 4 / 9 at 100% development precision but indistinguishable from grouped shuffles (p = .96875). Wide exact ranks improve to third and first, yet neither clears the frozen threshold. Ranking structure improved; commitment remains disabled.", "open"],
  ["17k", "Port-obligation automaton", "Sixteen-step target-free trajectories are compressed to 102 identity-free discharge/production states. A weakest-four-state score selects 8 / 9 supplied nuclei and 27 / 28 available colored sites; every one of 31 grouped-label shuffles reaches at most seven (p = .03125). Forty-seven states have support in only one training group, the form is exploratory, and one nucleus still fails, so it is a confirmation candidate—not a deployed search rule.", "progress"],
  ["17l", "Obligation confirmation falsification", "A maximin nucleus at (-110,-70,-70) is 87.18 units from every consumed rollout domain. Thirteen candidates and all sixteen-step trajectories freeze before one target open. Two exact branches exist, but the first ranks fifth; top-one is 2 / 3 correct. State coverage is only 6.25–18.75%, so the automaton is rejected for deployment and the nucleus becomes consumed development evidence.", "open"],
  ["17m", "Obligation backoff falsification", "A target-free receipt companion reproduces the consumed 13-branch trajectory set. Exact→role-shape→aggregate backoff raises known-exact state coverage from 12.5% to 75%, but p=.1875 and its rank worsens from 5 to 8. Coverage is not value.", "open"],
  ["17n", "Soft role/temporal obligation value", "Identity-free role ownership and ordered time bins both beat shuffled controls in group-heldout AUC and log-loss (p=.03125), yet top-action selection remains p=.50. On the consumed target-free trajectories the known exact branch ranks 13 and 8. The features remain diagnostic, not deployed.", "open"],
  ["17o", "Disjoint obligation transfer corpus", "Twenty preregistered, mutually disjoint rollout domains freeze 303 target-free branches before any target exists. Full grouped refit selects 41 correct sites, above every shuffle (p=.03125), but only 7 / 8 exact-bearing nuclei; a shuffle reaches eight (p=.125). Site-section signal is green, whole-action GCTS remains red.", "progress"],
  ["17p", "Clusters² future option", "Four frozen markings value each parent by its complete child tree. A channel-diverse 4 × top-8 portfolio retains the consumed exact parent→child path that greedy choices lose; marginal-preserving controls give p=.50, so supply improves while causal selection stays open.", "progress"],
  ["17q", "Held-out child-option graph", "Across ten consumed development nuclei, each six-action parent owns an immutable graph of up to eight future actions. Leave-one-nucleus-out order-1/order-2 port heads plus local option channels retain an exact parent in 8 / 9 supplied nuclei; both marginal nulls give p=.03125. The strongest order-2 head is also 8 / 9, so the portfolio is reproducibly non-random but has not yet added causal retention or labeled a third-block child.", "progress"],
  ["17r", "Executable third-block split", "Forty retained parents generate 5,091 target-free terminals at the expanded radius before one consumed target open. Exact parents survive in eight nuclei; the bounded top-8 tree has 90 exact paths across six, but the four-channel portfolio keeps only six paths across three. Two failures occur at the reach cutoff and three at portfolio pruning.", "open"],
  ["17s", "Terminal geometry value rejected", "A nested group-heldout ridge sees 5,091 frozen terminal score/triangle/radius/cross-distance records and the same four-per-parent budget. It retains exact paths in 2 / 6 supplied nuclei versus 3 / 6 for the incumbent (retention p=.4375; rank p=.21875), so terminal geometry is not promoted as a marking.", "open"],
  ["17t", "Consumed reach boundary", "A target-guided diagnostic follows only correct prefixes for the four exact parents hidden in nuclei 1 and 2. The unchanged frozen frontier contains an exact three-action path for all four, with minimum bottleneck rank 12 and rank sums 21 or 23; top-8 contains none. This locates the failure at reach, but cannot authorize a target-tuned top-12 policy.", "progress"],
  ["17u", "Compute-matched channel reach", "The budget remains eight: three scalar leaders plus one from each of five frozen pose/port channels. It restores all four hidden exact parents, then preserves every prior supply nucleus: 15 / 15 exact parents and 8 / 8 eligible nuclei versus 11 / 15 and 6 / 8 for scalar top-8; exact paths rise 90 → 472. The selector was designed on consumed failures, so production remains unchanged pending fresh confirmation.", "progress"],
  ["17v", "Fresh bounded clusters² supply", "A whole-child joint mark plus base fallback expands 47 rather than 168 prefixes on a preregistered disjoint nucleus. The receipt freezes 6,099 nine-action lineages before one target open; 410 are exact across all eight parents. Geometry memoization saves 9,033 advances and the run passes its 1,200-second gate.", "proved"],
  ["17w", "Commuting first-frontier closure", "A target-free subset dynamic program admits a three-action parent only when every action order reaches the same colored state. Across four development nuclei, an incidence marking retains an exact closure under every group holdout; on the consumed audit it selects two exact parents in the fixed top-eight batch.", "proved"],
  ["17x", "Conditional child value rejected", "Conditioned on those closure parents, a 3,994-candidate / 95-positive child marking supplies all 14 exact parent branches under four-nucleus holdout. On the fifth consumed geometry, however, the two exact continuations rank 132nd and 133rd. Six coarse feature ablations remain outside top 16. An explicit six-node parent→child incidence graph is directionally better: its order-2 value supplies 12 / 14 development branches and moves the fifth-geometry ranks to 69 and 71; order 3 supplies 9 / 14 and ranks 78 and 80. Neither survives top 16, so explicit connection correspondence is necessary but not yet a transferable child policy.", "open"],
  ["18", "Open frontier", "Learn a transferable winner among the 410 supplied exact alternatives, commit a conflict-free antichain without target truth, and promote it into a recurring oriented production with a strict three-scale stationarity audit.", "open"],
  ["19", "Molecular ice cover", "Atom-centred spokes are replaced by one bent H₂O motif plus decorated bridge and O₆ gap-boundary isometry classes, covering 216 / 216 Ih and 192 / 192 Ic atoms.", "proved"],
  ["20", "Blind ice anchor transfer", "Eight Ih-fitted proper-SE(3) ports emit exact 16 → 8 → 0 Ih and 12 → 0 Ic oxygen-anchor frontiers. Proton orientations and stationary promotion remain explicit red gates.", "progress"],
  ["21", "Layer-essential A₂ frontier", "A 4,940-shape size-eight census leaves four candidates exact through every periodic quotient up to seven copies. Replayed root coronas and 16 / 72 / 72 / 62 sound GCTS clauses sharpen the frontier without confusing bounded evidence with non-tiling or aperiodicity.", "progress"],
  ["22", "Experiment-facing powder validation", "A frozen structure/contrast request accepts independent pdCIF-style q, 2θ, or d profiles only after growth, preserves uncertainty and resolution metadata, and reports Rwp plus residuals without feeding clustering, marking, admission, or search. The built-in instrument response remains an explicit synthetic demonstrator, not evidence.", "proved"],
  ["23", "Public RRUFF profile bridge", "A digest-pinned CC-BY-4.0 RRUFF/JARVIS subset supplies fifteen measured powder profiles without upload. Exact chemistry filters candidates, the scientist chooses a replicate or polymorph, and only an additional curated phase correspondence permits a same-material claim; chemistry-only comparisons remain explicit experimental references.", "proved"],
  ["24", "q-dependent X-ray amplitudes", "Measured powder XRD now compares against a finite Debye intensity with physical inverse-ångström q and source-pinned neutral-atom Cromer–Mann f₀(q), not constant Z. Unsupported chemistry fails closed; ionic, anomalous, texture, absorption, diffuse, and undeclared instrument effects remain explicit omissions.", "proved"],
];

const CLAIMS = [
  ["proved", "Complete representation", "Every observed atom belongs to a repeated support or an explicit residual cluster; gaps are never silently dropped."],
  ["proved", "Proper rigid-motion invariance", "Permutation and arbitrary proper-SE(3) transforms preserve the scientific grammar; mirror images remain distinct when chiral."],
  ["proved", "Crystal exponential representation", "The learned NaCl recurrence represents 4,194,304 colored sites after seven symbolic actions."],
  ["proved", "Multi-state exponential control", "A positions-only grammar learns A→AB and B→A, predicts a sealed 48-site fourth wave exactly, and represents 1,178,508 sites at vector action 24."],
  ["proved", "Causal GCTS advantage", "On sealed IQC frontiers, learned connection sections beat matched baselines and 31 shuffled controls with identical candidate sets."],
  ["proved", "Exact finite QC continuation", "Multiple ideal and published quasicrystal nuclei grow self-fed with exact colored-site certificates."],
  ["proved", "Negative amorphous control", "The generic hierarchy rejects stationary recursion rather than memorizing and repeating a glass crop."],
  ["proved", "Molecular ice cover", "Ice Ih and Ic are covered by repeated bent H₂O motifs plus explicit bridge and O₆ gap-boundary clusters; the 216- and 192-atom periodic windows are represented completely without radial coordination spokes."],
  ["progress", "Finite ice anchor transfer", "Eight Ih-fitted proper-SE(3) ports emit 16 then 8 exact unseen Ih oxygen anchors and 12 exact Ic anchors before a conservative fixed point."],
  ["open", "Proton-resolved ice growth", "The current section carries competing H₂O pose domains symbolically. A global free-energy request is now executable, but no external response is bundled; no proton assignment or promoted stationary ice production is claimed."],
  ["open", "Conditional classical nucleation work", "Validated γ(n̂) unlocks an exact specimen-, response-, phase-, and temperature-bound Δg request. A returned positive driving-force density produces a conditional Wulff-scale barrier profile, but no physical response is bundled and no atom count or heterogeneous correction is inferred."],
  ["open", "Conditional capillarity action ranking", "After both γ(n̂) and Δg validate, an opt-in target-free regularizer can rank unchanged actions by their frozen-center Wulff-scale work increment. It never changes candidate geometry or admission, and it is not an atomistic pathway, attachment probability, nucleation rate, or clock."],
  ["open", "Conditional classical nucleation rate", "A validated capillarity work object can issue a separate exact-state request for ρsite, Z, and f⁺. Only a conforming response exposes J=ρsite Z f⁺ exp(−ΔG*/kBT) and a selectable finite Poisson window; no kinetics are bundled, no GCTS action receives time, and heterogeneous/nonclassical mechanisms remain open."],
  ["open", "Seeded conditional nucleation schedule", "A validated rate can freeze exponential event times and uniform normalized positions in one declared finite observation box. Seed, uniforms, hashes, cap truncation, and coordinates are auditable, but the points contain no atoms or poses and never become GCTS nuclei without a separate construction handoff."],
  ["conditional", "Atomistic critical-nucleus geometry → GCTS seed", "A frozen event schedule can request one independently committor-validated species-labelled critical configuration. A conforming response supplies atom count, membership, and coordinates; seeded proper rotations produce a magnified preview. An explicit frozen-grammar gate then requires colored proper-SE(3) cluster cover, connected admitted ports, residual terminals, and live collision/boundary checks before local seed staging. This remains one representative, not an ensemble or heterogeneous-site model, and it does not infer either physical clock."],
  ["progress", "Deep QC compression", "Ideal IQC reaches six positive quotient levels; Cd–Yb reaches nine on five disjoint training windows."],
  ["progress", "Frozen hierarchy transfer", "IQC primitive cover transfers completely and Cd–Yb promoted vocabularies re-encode four held-out levels, with dormant symbols explicit."],
  ["progress", "Site-resolved marking", "A 1,245-site train corpus gives site AUC 0.8864 and action AUC 1.0, both significant against 31 shuffles."],
  ["proved", "Continuous IQC section", "A 50,065-example post-commit port-state section transfers for two fresh self-fed waves, emitting 8 / 8 exact colored sites."],
  ["open", "Parallel IQC action marking", "Whole-action band labels are 57 / 216 and 48 / 216 positive, but no group-heldout threshold reaches 95% precision; local scores alone cannot yet admit an exact antichain."],
  ["progress", "Port-obligation lookahead", "One-step future-frontier features find one zero-error action per stage, but retain 1 / 18 required actions; explicit incidence-level search is still needed."],
  ["progress", "Explicit incidence search", "A 504-action, target-free two-level graph carries semantic port roles and backtracks stranded branches. It finds 8 / 9 connected paths, but all 16 selected actions are false; 97.4% role transfer shows the missing signal is joint local section geometry, not vocabulary coverage."],
  ["progress", "Candidate pose–port section", "Across 44,602 collision-free candidates, the colored metric-graph section admits 25 / 26 exact placements. They cover only four of nine nuclei, so the reserved target stays sealed."],
  ["open", "Orbit-channel confirmation", "One-vote-per-family scoring prevents symmetry-orbit cardinality from inflating evidence and reaches 18 / 18 development placements, but the preregistered selector is 0 / 2 on a disjoint reserved nucleus."],
  ["open", "Joint incidence geometry", "Post-confirmation controls reject both orbit-disagreement selection (18 / 20) and nested scalar score stacking (0 / 20); candidate generation is fixed, so the next mark must retain relational incidence structure."],
  ["progress", "Relational marking vocabulary", "The local section now carries 25,977 explicit role–geometry relations with 97.7% heldout weight coverage. Its 15 / 20 result shows message passing or canonical subgraphs—not more marginal weights—are required."],
  ["open", "Finite message quotient", "Distance/role quotients keep exact hashes at 14 / 20. An additive 457-node / 976-graph incidence vocabulary reaches 15 / 20; a ≥3-nucleus recurrent codebook falls to 11 / 20. Compression alone is not the missing value."],
  ["open", "Learned message value", "A class-balanced grouped ridge head selects depth one in every fold and replaces the incumbent twice, but the sealed aggregate falls to 16 / 20 exact terminals with p=.375 against 31 within-nucleus shuffles."],
  ["progress", "Expanded IQC development", "Eight preregistered disjoint nuclei add 16 held-out actions. The frozen quotient reaches 30 / 36 overall; a whole-state conditional/backoff table reaches 29 / 36. The next confirmation remains sealed."],
  ["progress", "Pose-aware antichain search", "Proper-rotation-invariant port-axis channels preserve chirality and learn 4,414–9,580 finite orientation tokens. The best arm and a nested unordered two-action search both remain at 30 / 36, although every nucleus contains exact compatible pairs in its 16-action shortlist."],
  ["progress", "Successor-state value", "Each shortlisted action is executed hypothetically and scored by the frozen port frontier it creates. The target-free one-step value improves 30 / 36 to 31 / 36. Pooling up to four child successors remains 31 / 36, isolating path-conditioned obligations as the next target."],
  ["progress", "Directed obligation value", "Keeping each root→child port obligation separate raises expanded IQC selection to 33 / 36 and 16 / 18 exact nuclei. Widening the exact tree from 4 to 16 children supplies rank-13 paths but remains 33 / 36, so confirmation stays sealed."],
  ["progress", "Connection-vocabulary audit", "Pooling exact raw connection states from 17 nuclei is counterproductive: boundary-fragmented cluster IDs supply correct roots in 14 / 18 and exact paths in only 7 / 18. A shared recurrent cluster quotient must precede port learning."],
  ["progress", "Exact two-step path supply", "One hundred twenty-eight target-free descriptor classes per nucleus contain exact root→child connections in all nine nuclei. Correct score composition selects 5 / 9; four failures now isolate the missing path-value section."],
  ["proved", "Fresh bounded three-block supply", "A preregistered disjoint IQC nucleus freezes 6,099 target-blind nine-action lineages; one later target open verifies 410 exact lineages across all eight parents while 47 scheduled prefixes replace 168 eager prefixes."],
  ["progress", "Third-frontier negative control", "Executing 512 target-free paths per nucleus and marking their outgoing port sections selects only 4 / 9. A larger immediate frontier is again rejected as the search value."],
  ["progress", "Simultaneous consistency search", "Complete successor enumeration and exhaustive compatible-set search are now distinct from scalar ranking. All 59 exact and 61 false wide-IQC branches satisfy the semantic-role cover, proving that exact port instances—not more role weights—are required."],
  ["progress", "Finite port-instance contradiction", "Occurrence-level forward continuation raises retained branch precision from 49.2% to 62.0% and rejects 26 false branches. Two exact branches also fail, so the certificate is diagnostic rather than an autonomous rollback rule."],
  ["open", "Boundary backoff causality", "Port-length conditioning restores exact supply and retains 8 false rejections, but shuffled labels reproduce the entire grouped selection result. The next mark must distinguish joint endpoint geometry within one boundary regime."],
  ["open", "Branch-graph transfer", "Complete simultaneous action geometry removes every within-nucleus exact/false collision, yet only two exact rows recur across nuclei and two bounded grouped sections both select 0 / 2 recoverable exact branches. A recurrent cluster-of-clusters quotient must precede value learning."],
  ["open", "External recurrent-value transfer", "After removing the only overlapping training nucleus, a 338-branch / 29-nucleus scalar value selects 19 / 20 training nuclei but only 1 / 2 recoverable wide fallbacks. It ties every grouped shuffle and leaves exact supply at 8 / 9, so it is not deployed."],
  ["open", "Geometry-complete clusters² transfer", "A compact frozen fixture retains 168 three-action macro occurrences, 72 exact labels, and 158 symmetry-quotiented port derivations without raw occurrence IDs. Its geometry-only quotient fails grouped shuffles and external wide transfer, so it is not deployed; the next marking must align exact port incidence across training and wide candidates."],
  ["progress", "Common clusters² port schema", "Every development and wide branch is now replayed into the same proper-SE(3)-canonical graph with three colored actions, witnessed incoming ports, and endpoint-incidence edges. The exact recurrent vocabulary is too sparse—1 / 28 wide candidates recognized—so graph-metric learning, not another schema retrofit, is the next gate."],
  ["open", "Continuous port-graph value", "A train-selected pose+incidence metric improves strict development coverage from 4 / 9 to 6 / 9 without false selections, but is reproduced by grouped shuffles and admits no unchanged-wide branch. Exact alternatives at ranks 5 and 2 show useful ordering signal without a validated commit rule."],
  ["open", "Finite relational message value", "A train-fitted, group-balanced quotient compresses 216 canonical node/edge measurements into 362 recurrent states. It improves wide exact ranks to 3 and 1 but selects neither, while 31 full grouped-label refits give p=.96875. The quotient remains a diagnostic library entry, not a search policy."],
  ["progress", "Sequential obligation value", "A finite 102-state automaton scores each branch by its four weakest recognized port-obligation states. It raises group-heldout selection from 7 / 9 to 8 / 9 and retains 27 / 28 available sites with p=.03125 against 31 shuffles. Forty-seven states have one-group support; the result is exploratory and one supplied nucleus remains wrong, so no autonomous commit is claimed."],
  ["open", "Fresh obligation transfer", "The frozen automaton receives a one-shot disjoint test with 152 complete terminals and a 13-branch portfolio. Two exact branches are supplied, but first-exact rank is 5 and top-one is 2 / 3 correct. Low state coverage, not candidate supply, blocks deployment."],
  ["open", "Obligation backoff transfer", "Hierarchical exact/role-shape/aggregate matching raises consumed known-exact state coverage sixfold but worsens its rank and fails grouped shuffles; it is not a marking policy."],
  ["progress", "Soft obligation coordinates", "Role-conditioned and time-binned metrics carry significant group-heldout ranking information, but neither beats the top-action shuffle null or transfers useful ordering to the consumed disjoint nucleus."],
  ["progress", "Disjoint obligation site signal", "A 20-nucleus, 303-branch preregistered corpus validates correct-site yield against 31 grouped shuffles (41 versus maximum 40; p=.03125). Exact whole-branch selection remains red at 7 / 8 with p=.125, so the score is not deployed."],
  ["progress", "Clusters² option-preserving tree", "The exact consumed six-action lineage is retained by a target-free four-parent, multi-marking child portfolio: ports rank its parent first and the base top-eight child set contains the exact continuation. Fifteen of 31 score-marginal shuffles also retain it, so the result proves bounded rollback supply—not a learned commit rule."],
  ["proved", "Site-resolved development gate", "Scoring the three colored sites separately, then aggregating without splitting the certified action, reaches 8 / 8 exact supplied nuclei and 45 correct sites; both exceed all 31 grouped shuffles at p=.03125."],
  ["open", "Fresh site-section transfer", "On the published maximin nucleus the frozen three-wave portfolio supplies exact actions in only waves two and three, selects none, and recovers 2 / 9 sites. The target was opened once after all rankings, so the development mark is falsified rather than retuned."],
  ["progress", "Consumed proposal repair", "Full-tree scoring proves the old first wave has zero exact terminals. A 12→4→8 schedule restores one exact terminal with 9% fewer proposal checks, but existing terminal heads rank it 107/114; proposal supply is repaired while transferable value remains open."],
  ["progress", "Stage-local rollout value", "Twenty disjoint development nuclei validate a 16-step temporal connection section: 19/19 supplied exact terminals and 59 colored sites, above 31 fully refitted shuffles at p=.03125 for both metrics."],
  ["open", "Rollout-value spatial transfer", "A preregistered disjoint confirmation recovers 6/9 sites in both arms, but the learned mark turns the baseline's exact 3/3 first block into 2/3 and has zero exact blocks. Deployment, sustained continuation, and exponential growth remain red."],
  ["progress", "Nearest recurrent branch value", "A geometry-only 30-nucleus corpus freezes 354 depth-three terminal branches. Group-heldout k=9 nearest-recurrent value improves exact selection from 17 / 21 to 20 / 21 supplied nuclei and moves the consumed diagnostic exact branch from rank 10 to rank 1. A fresh autonomous confirmation remains unopened."],
  ["progress", "Frontier-state grammar", "Five recurring types cover 336 / 368 IQC sites; four rules are heterogeneous, but no closed state matrix recurs across transitions."],
  ["open", "Nested calibration", "The strongest Cd–Yb site threshold is 97.73% precise when fixed, but fully nested selection is 94.48%; a fresh target stays sealed."],
  ["progress", "Child-obligation closure", "On five Cd–Yb development windows, a whole-child threshold fit outside each execution window emits 146/146 correct sites, closes and promotes 16 exact parents, and self-feeds in two windows. The geometry vocabulary is shared across folds, so this is finite development execution rather than untouched transfer or stationary growth."],
  ["progress", "Consumed Cd–Yb spatial transfer", "One of two spatially disjoint reserved windows executes 4→4→3 frozen whole-child sections with 81/81 correct sites and 11 promoted parents; the other supplies zero candidates. The policy is not refit, but both structural windows were previously used by re-encoding audits, so fresh confirmation remains open."],
  ["progress", "Cd–Yb abstraction-boundary diagnosis", "The empty reserve has 32 exact support occurrences but zero retained macro-anchor types. Its primitive port graph still contains 204/345 exact actions; one-third child coverage is rejected by held-development errors. Promotion coverage—not local geometry or marking threshold—is the next gate."],
  ["open", "Generic QC stationarity", "No exact chemistry–chirality–directed-port production recurs across three consecutive QC levels."],
  ["progress", "IQC option-preserving beam", "A width-four target-free beam keeps the branch with the largest compatible next frontier. Frozen before wave 20, it adds 120/120 exact held-forward sites; all 24 waves are 572/572 exact. Spatial confirmation and stationarity remain open."],
  ["progress", "A₂ sliced radius-three frontier", "Eight size-seven consecutive-layer candidates have complete exact radius-two patches (190–252 copies). Uniform radius-three runs retain 759 failure and 731 first-corona clauses, then stop at declared round or solver limits; every global classification remains unresolved."],
  ["proved", "Seventeen bounded A₂ cluster obstructions", `${A2_SLICED_SCALE3_PARENT_COUNT.toLocaleString()} scale-three and ${A2_SLICED_SCALE4_PARENT_COUNT.toLocaleString()} scale-four reflected three-copy parent types are exhausted across all eight leads; ${A2_SLICED_FOUR_COPY_SCALE2_PARENT_COUNT.toLocaleString()} four-copy scale-two parents are additionally exhausted for ${a2SlicedShortIds(A2_SLICED_FOUR_COPY_SCALE2_OBSTRUCTIONS).join(" · ")}. Each certificate excludes one finite grammar only; none proves non-tiling or aperiodicity.`],
  ["open", "Generic million-site QC growth", "Specialized/address ceilings cross one million; the family-blind cluster-of-clusters executor does not yet."],
  ["open", "Pure-port crystal closure", "NaCl's port graph certifies the learned cell rule, but the radix/offset proposal still comes from a positions-only grid learner."],
  ["open", "Explicit output cost", "Symbolic derivations compress actions; emitting every atom remains linear and is not claimed to replace molecular dynamics time integration."],
  ["progress", "Exact A₂ layer-essential screening", "From 4,940 size-eight layer-essential shapes, exact weighted quotient replay leaves four candidates unresolved through seven copies with zero solver unknowns. Their first coronas are independently replayed, and 16 / 72 / 72 / 62 sound GCTS clauses prune local families."],
  ["open", "A₂ global classification", "The four survivors remain unresolved. Larger periodic domains, complete outer-corona searches, and general substitution grammars are open; bounded scalar, anisotropic, and small-metatile exclusions prove neither non-tiling nor aperiodicity."],
];

function statusLabel(status) {
  return status === "pass" || status === "proved" ? "proved" : status === "progress" ? "measured" : status === "control" ? "control" : "open";
}

function openAtlas() {
  atlas.hidden = false;
  document.body.classList.add("atlas-open");
  atlasButton.setAttribute("aria-expanded", "true");
  closeButton.focus();
}

function closeAtlas() {
  atlas.hidden = true;
  document.body.classList.remove("atlas-open");
  atlasButton.setAttribute("aria-expanded", "false");
  atlasButton.focus();
}

function renderMatrix() {
  MATRIX.forEach(([name, ...cells]) => {
    const row = document.createElement("div");
    row.className = "matrix-row";
    row.setAttribute("role", "row");
    row.innerHTML = `<strong>${name}</strong>`;
    cells.forEach(([status, label]) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `matrix-cell ${status}`;
      button.innerHTML = `<i></i><span>${label}</span><small>${statusLabel(status)}</small>`;
      button.addEventListener("click", () => {
        document.querySelectorAll(".matrix-row.selected").forEach((item) => item.classList.remove("selected"));
        row.classList.add("selected");
        byId("matrixDetail").innerHTML = `<span>${name}</span><p>${MATRIX_DETAILS[name]}</p>`;
      });
      row.appendChild(button);
    });
    byId("benchmarkMatrix").appendChild(row);
  });
  byId("benchmarkMatrix").querySelector(".matrix-cell").click();
}

function drawGrowthChart(system) {
  const svg = byId("atlasGrowthChart");
  const width = 720, height = 300, left = 62, right = 28, top = 28, bottom = 54;
  const values = system.values;
  const maximum = Math.max(...values, 10);
  const maxLog = Math.ceil(Math.log10(maximum));
  const x = (index) => left + (width - left - right) * (values.length === 1 ? .5 : index / (values.length - 1));
  const y = (value) => top + (height - top - bottom) * (1 - Math.log10(Math.max(1, value)) / maxLog);
  const grid = Array.from({length: maxLog + 1}, (_, power) => {
    const value = 10 ** power;
    return `<g><line x1="${left}" y1="${y(value)}" x2="${width - right}" y2="${y(value)}"/><text x="${left - 10}" y="${y(value) + 3}" text-anchor="end">10${power === 0 ? "⁰" : `<tspan baseline-shift="super">${power}</tspan>`}</text></g>`;
  }).join("");
  const points = values.map((value, index) => `${x(index)},${y(value)}`).join(" ");
  const area = `${left},${height - bottom} ${points} ${x(values.length - 1)},${height - bottom}`;
  const dots = values.map((value, index) => `<g class="${index <= system.verifiedThrough ? "verified" : "projected"}"><circle cx="${x(index)}" cy="${y(value)}" r="5"/><text x="${x(index)}" y="${Math.max(14, y(value) - 12)}" text-anchor="middle">${value.toLocaleString()}</text></g>`).join("");
  const xLabels = system.xLabels || values.map((_value, index) => `a${index}`);
  svg.innerHTML = `<g class="chart-grid">${grid}</g><polygon class="growth-area" points="${area}"/><polyline class="growth-line" points="${points}"/>${dots}<g class="x-labels">${values.map((_value, index) => `<text x="${x(index)}" y="${height - 24}" text-anchor="middle">${xLabels[index]}</text>`).join("")}</g>`;
}

const A2_CATALOGS = Object.freeze({
  layered: {
    label: "Layered size 8", title: "Four size-eight candidates remain exact through seven copies",
    summary: "Select a layer-essential lattice function. The diagram is its exact A₂ cell support; the bars are sound outer-corona obstruction clauses.",
    footerLabel: "What one clause means",
    footer: "A specific placement subset in the first corona cannot be completed into a saturated second corona—even when every unselected helper placement remains available.",
    candidates: [...A2_LAYERED_SIZE8_CANDIDATES]
      .filter(candidate => candidate.screening.status === "inconclusive")
      .sort((left, right) => left.survivor_priority - right.survivor_priority),
  },
  sliced: {
    label: "Sliced size 7", title: "Eight consecutive-layer candidates now reach a complete radius-two patch",
    summary: "Each diagram is a proper affine-A₃ alcove complex projected without changing incidence. Radius-three bars separate retained failure clauses from first-corona clauses; no bar is a non-tiling proof.",
    footerLabel: "What radius three means",
    footer: "The fixed radius-two patch is extended by a uniform bounded GCTS search. Retained clauses are sound local obstructions, while a round or solver limit leaves the global extension question unresolved.",
    candidates: [...A2_SLICED_SIZE7_CANDIDATES]
      .filter(candidate => candidate.screening.status === "inconclusive")
      .sort((left, right) => left.survivor_priority - right.survivor_priority),
  },
});

let activeA2Catalog = "layered";

function convexHull(points) {
  const ordered = [...new Map(points.map((point) => [point.join(","), point])).values()]
    .sort((left, right) => left[0] - right[0] || left[1] - right[1]);
  if (ordered.length < 3) return ordered;
  const cross = (origin, first, second) => (first[0] - origin[0]) * (second[1] - origin[1])
    - (first[1] - origin[1]) * (second[0] - origin[0]);
  const half = (values) => {
    const result = [];
    values.forEach((point) => {
      while (result.length >= 2 && cross(result.at(-2), result.at(-1), point) <= 0) result.pop();
      result.push(point);
    });
    return result;
  };
  return [...half(ordered).slice(0, -1), ...half([...ordered].reverse()).slice(0, -1)];
}

function a2CandidateSvg(candidate) {
  if (candidate.alcoves) {
    const project = ([x, y, z]) => [(x - y) * 36 + z * 7, (x + y) * 18 - z * 34];
    const shapes = candidate.alcoves.map((alcove, index) => {
      const vertices = [alcove.base.slice()];
      alcove.order.forEach((axis) => {
        const next = vertices.at(-1).slice(); next[axis] += 1; vertices.push(next);
      });
      const points = convexHull(vertices.map(project));
      const layer = Math.min(3, Math.floor(index * 4 / Math.max(1, candidate.alcoves.length)));
      return { index, points, layer, depth: vertices.reduce((sum, point) => sum + point[2], 0) / vertices.length };
    }).sort((left, right) => left.depth - right.depth || left.index - right.index);
    const coordinates = shapes.flatMap((shape) => shape.points);
    const minX = Math.min(...coordinates.map(([x]) => x)) - 18;
    const maxX = Math.max(...coordinates.map(([x]) => x)) + 18;
    const minY = Math.min(...coordinates.map(([, y]) => y)) - 18;
    const maxY = Math.max(...coordinates.map(([, y]) => y)) + 18;
    const polygons = shapes.map((shape) => `<polygon class="a2-layer-${shape.layer}" points="${shape.points.map((point) => point.join(",")).join(" ")}"/><text x="${shape.points.reduce((sum, point) => sum + point[0], 0) / shape.points.length}" y="${shape.points.reduce((sum, point) => sum + point[1], 0) / shape.points.length + 2}">${shape.index + 1}</text>`).join("");
    return `<svg viewBox="${minX} ${minY} ${maxX - minX} ${maxY - minY}" role="img" aria-label="${candidate.name}, seven affine alcoves">${polygons}</svg>`;
  }
  const polygons = candidate.cells.map((cell) => {
    const centerX = (cell.q - cell.r) * 30 + cell.k * 7;
    const centerY = (cell.q + cell.r) * 17 - cell.k * 22;
    const points = cell.kind === "u"
      ? [[centerX, centerY - 14], [centerX - 14, centerY + 10], [centerX + 14, centerY + 10]]
      : [[centerX, centerY + 14], [centerX - 14, centerY - 10], [centerX + 14, centerY - 10]];
    return { cell, points };
  }).sort((left, right) => left.cell.k - right.cell.k || left.cell.r - right.cell.r || left.cell.q - right.cell.q);
  const coordinates = polygons.flatMap(({ points }) => points);
  const minX = Math.min(...coordinates.map(([x]) => x)) - 18;
  const maxX = Math.max(...coordinates.map(([x]) => x)) + 18;
  const minY = Math.min(...coordinates.map(([, y]) => y)) - 18;
  const maxY = Math.max(...coordinates.map(([, y]) => y)) + 18;
  const shapes = polygons.map(({ cell, points }) => `<polygon class="a2-layer-${Math.min(3, cell.k)}" points="${points.map((point) => point.join(",")).join(" ")}"/><circle cx="${points.reduce((sum, point) => sum + point[0], 0) / 3}" cy="${points.reduce((sum, point) => sum + point[1], 0) / 3}" r="1.8"/>`).join("");
  return `<svg viewBox="${minX} ${minY} ${maxX - minX} ${maxY - minY}" role="img" aria-label="${candidate.name}, eight exact triangular prisms">${shapes}</svg>`;
}

function a2ClauseCount(candidate) {
  return candidate.alcoves
    ? candidate.screening.radius_three_failure_clauses + candidate.screening.radius_three_first_corona_clauses
    : candidate.screening.corona2_gcts_sound_clauses;
}

function renderA2Candidate(candidateId) {
  const catalog = A2_CATALOGS[activeA2Catalog];
  const candidate = catalog.candidates.find((entry) => entry.id === candidateId) || catalog.candidates[0];
  const screen = candidate.screening;
  document.querySelectorAll("[data-a2-candidate]").forEach((button) => {
    const active = button.dataset.a2Candidate === candidate.id;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  const unitLabel = candidate.alcoves
    ? `${candidate.alcoves.length} affine alcoves · ${candidate.lattice_points} lattice vertices`
    : `${candidate.cells.length} exact A₂ prisms · ${candidate.lattice_points} lattice points`;
  byId("a2CandidateShape").innerHTML = `${a2CandidateSvg(candidate)}<span>${unitLabel}</span>`;
  byId("a2CandidateStory").innerHTML = candidate.alcoves ? `
    <header><span>${candidate.id}</span><strong>${screen.radius_three_status}</strong></header>
    <h4>${candidate.name}</h4>
    <div><span><small>exact radius-two patch</small><b>${screen.radius_two_patch_copies} copies</b></span><span><small>target / occupied sites</small><b>${screen.radius_two_target_points} / ${screen.radius_two_occupied_points}</b></span><span><small>periodic screen</small><b>through ${screen.periodic_exact_through} copies</b></span><span><small>failure clauses</small><b>${screen.radius_three_failure_clauses}</b></span><span><small>first-corona clauses</small><b>${screen.radius_three_first_corona_clauses}</b></span><span><small>radius-three stop</small><b>${screen.radius_three_stopped_by.replaceAll("_", " ")}</b></span><span><small>3-copy metatile scales</small><b>${screen.three_copy_metatile_substitution_scales_exhausted.join(" · ")}</b></span><span><small>scale-3 / 4 parents</small><b>${(screen.three_copy_metatile_scale3_reflected_parent_types || 0).toLocaleString()} / ${(screen.three_copy_metatile_scale4_reflected_parent_types || 0).toLocaleString()}</b></span><span><small>4-copy scale-2</small><b>${screen.four_copy_metatile_scale2_reflected_parent_types ? `${screen.four_copy_metatile_scale2_reflected_parent_types.toLocaleString()} parents` : "unresolved"}</b></span></div>
    <p>The consecutive-layer support has weight profile <b>${candidate.morphology.layer_weight_profile.join(" · ")}</b>. Its six-copy weighted periodic screen is complete with zero solver unknowns, and the displayed radius-two patch is exact. The uniform radius-three run retains ${screen.radius_three_failure_clauses} failure and ${screen.radius_three_first_corona_clauses} first-corona clauses before a declared ${screen.radius_three_stopped_by.replaceAll("_", " ")}. Direct scalar substitutions at scales ${screen.direct_scalar_substitution_scales_exhausted[0]}–${screen.direct_scalar_substitution_scales_exhausted.at(-1)} and three-copy metatile substitutions at scales ${screen.three_copy_metatile_substitution_scales_exhausted.join(" and ")} are excluded${screen.three_copy_metatile_scale3_reflected_parent_types ? ` after exhausting ${screen.three_copy_metatile_scale3_reflected_parent_types.toLocaleString()} scale-three and ${screen.three_copy_metatile_scale4_reflected_parent_types.toLocaleString()} scale-four reflected parent types` : ""}${screen.four_copy_metatile_scale2_reflected_parent_types ? `; a distinct four-copy scale-two census also exhausts ${screen.four_copy_metatile_scale2_reflected_parent_types.toLocaleString()} reflected parent types` : "; its four-copy scale-two screen remains unresolved"}. The candidate remains <b>unresolved</b>.</p>` : `
    <header><span>${candidate.id}</span><strong>${screen.status}</strong></header>
    <h4>${candidate.name}</h4>
    <div><span><small>root corona</small><b>${screen.corona_root_patch_copies} copies</b></span><span><small>periodic frontier</small><b>through ${screen.periodic_exact_through} copies</b></span><span><small>seven-copy HNF bases</small><b>${screen.periodic_hnf_bases_exhausted_by_copies["7"].toLocaleString()}</b></span><span><small>sound GCTS clauses</small><b>${screen.corona2_gcts_sound_clauses}</b></span><span><small>outer corona</small><b>${screen.corona2_gcts_stopped_by.replaceAll("_", " ")}</b></span><span><small>solver unknowns</small><b>${screen.periodic_solver_unknowns}</b></span></div>
    <p>This candidate survives every exact weighted periodic quotient through seven copies (${screen.periodic_seven_copy_exact_multicover_nodes.toLocaleString()} exact multicover nodes; ${screen.periodic_seven_copy_mitm_fallbacks} complete meet-in-the-middle fallbacks). Its first corona is independently replayed, while ${screen.corona2_gcts_sound_clauses} sound local clauses prune—but do not exhaust—the outer first-corona search. Direct scalar substitutions at scales ${screen.direct_scalar_substitution_scales_exhausted[0]}–${screen.direct_scalar_substitution_scales_exhausted.at(-1)}, ${screen.direct_layer_scale_pairs_exhausted} anisotropic scale pairs, and connected two- and three-copy metatile rules at scales 2 and 3 are excluded. Larger domains and more general grammars keep the classification <b>unresolved</b>.</p>`;
}

function renderA2Explorer() {
  const tabs = byId("a2CandidateTabs");
  const catalog = A2_CATALOGS[activeA2Catalog];
  document.querySelectorAll("[data-a2-catalog]").forEach((button) => {
    const active = button.dataset.a2Catalog === activeA2Catalog;
    button.classList.toggle("active", active); button.setAttribute("aria-selected", String(active));
  });
  byId("a2ExplorerTitle").textContent = catalog.title;
  byId("a2ExplorerSummary").textContent = catalog.summary;
  byId("a2ExplorerFooterLabel").textContent = catalog.footerLabel;
  byId("a2ExplorerFooterText").textContent = catalog.footer;
  const maximum = Math.max(...catalog.candidates.map(a2ClauseCount), 1);
  tabs.replaceChildren(...catalog.candidates.map((candidate) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.a2Candidate = candidate.id;
    button.setAttribute("role", "tab");
    button.innerHTML = `<span>${candidate.id.slice(-5)}</span><strong>${a2ClauseCount(candidate)}</strong><small>${candidate.alcoves ? "R3 clauses" : "sound clauses"}</small>`;
    button.addEventListener("click", () => renderA2Candidate(candidate.id));
    return button;
  }));
  byId("a2BlockerBars").replaceChildren(...catalog.candidates.map((candidate) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.a2Candidate = candidate.id;
    button.style.setProperty("--a2-blocker-ratio", `${a2ClauseCount(candidate) / maximum}`);
    button.innerHTML = `<span>${candidate.id.slice(-5)}</span><i></i><b>${a2ClauseCount(candidate)}</b>`;
    button.addEventListener("click", () => renderA2Candidate(candidate.id));
    return button;
  }));
  renderA2Candidate(catalog.candidates[0].id);
}

document.querySelectorAll("[data-a2-catalog]").forEach((button) => button.addEventListener("click", () => {
  activeA2Catalog = button.dataset.a2Catalog;
  renderA2Explorer();
}));

function renderSupplyAudit(audit) {
  byId("supplyAuditTitle").textContent = audit.title;
  byId("supplyAuditSummary").textContent = audit.summary;
  const renderReserve = (index) => {
    const reserve = audit.reserves[index];
    document.querySelectorAll("[data-supply-reserve]").forEach((button) => {
      const active = Number(button.dataset.supplyReserve) === index;
      button.classList.toggle("active", active);
      button.setAttribute("aria-selected", String(active));
    });
    const maximum = Math.max(...reserve.steps.map((step) => step[1]), 1);
    const detail = byId("supplyAuditDetail");
    const stageButtons = reserve.steps.map(([label, value, note], stage) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.supplyStage = String(stage);
      button.style.setProperty("--supply-ratio", String(Math.sqrt(value / maximum)));
      button.innerHTML = `<small>${String(stage + 1).padStart(2, "0")}</small><span>${label}</span><i></i><strong>${value.toLocaleString()}</strong>`;
      button.addEventListener("click", () => {
        stageButtons.forEach((item) => item.classList.toggle("active", item === button));
        detail.className = `supply-audit-detail ${value ? "supplied" : "starved"}`;
        detail.innerHTML = `<span>${label}</span><strong>${value.toLocaleString()}</strong><p>${note}</p>`;
      });
      return button;
    });
    byId("supplyAuditStages").replaceChildren(...stageButtons);
    const primitive = reserve.primitive;
    const exactRatio = primitive.total ? primitive.exact / primitive.total : 0;
    byId("supplyAuditFallback").innerHTML = `
      <header><span>lower-level port frontier</span><strong>${primitive.exact} exact / ${primitive.total} candidates</strong></header>
      <div class="supply-fallback-meter"><i style="--primitive-exact:${exactRatio}"></i></div>
      <dl><div><dt>exact primitive actions</dt><dd>${primitive.exact}</dd></div><div><dt>inexact alternatives</dt><dd>${primitive.total - primitive.exact}</dd></div><div><dt>exact site union</dt><dd>${primitive.sites}</dd></div></dl>
      <p>${reserve.verdict}</p><footer>${audit.coverage}</footer>`;
    stageButtons[0]?.click();
  };
  const tabs = audit.reserves.map((reserve, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.supplyReserve = String(index);
    button.setAttribute("role", "tab");
    button.innerHTML = `<span>${reserve.label}</span><strong>${reserve.steps[3][1] ? `${reserve.steps[3][1]} macro candidates` : "macro frontier empty"}</strong>`;
    button.addEventListener("click", () => renderReserve(index));
    return button;
  });
  byId("supplyAuditTabs").replaceChildren(...tabs);
  renderReserve(0);
}

function renderSystem(key) {
  const system = SYSTEMS[key];
  document.querySelectorAll("[data-system]").forEach((button) => button.classList.toggle("active", button.dataset.system === key));
  byId("atlasSystemKind").textContent = system.kind;
  byId("atlasSystemName").textContent = system.name;
  byId("atlasSystemSummary").textContent = system.summary;
  byId("atlasSystemMetrics").innerHTML = system.metrics.map(([term, value]) => `<div><dt>${term}</dt><dd>${value}</dd></div>`).join("");
  byId("atlasSystemVerdict").className = `system-verdict ${system.verdict[0]}`;
  byId("atlasSystemVerdict").innerHTML = `<span>${statusLabel(system.verdict[0])}</span><strong>${system.verdict[1]}</strong>`;
  byId("atlasCurveEyebrow").textContent = system.curveEyebrow || "represented or explicit sites";
  byId("atlasCurveTitle").textContent = system.curveTitle || `${system.short} · growth by learned action`;
  byId("atlasCurveObserved").textContent = system.curveObserved || "explicit / verified";
  byId("atlasCurveProjected").textContent = system.curveProjected || "symbolic representation";
  byId("atlasCurveNote").textContent = system.curveNote || "log scale · labels show exact counts";
  byId("systemEvidenceCards").innerHTML = system.evidence.map(([label, value, note]) => `<article><small>${label}</small><strong>${value}</strong><p>${note}</p></article>`).join("");
  const closure = byId("systemClosureFunnel");
  closure.hidden = !system.closureFunnel;
  if (system.closureFunnel) {
    const funnel = system.closureFunnel;
    const maximum = Math.max(...funnel.steps.map((step) => step[1]), 1);
    byId("closureFunnelTitle").textContent = funnel.title;
    byId("closureFunnelSummary").textContent = funnel.summary;
    const detail = byId("closureFunnelDetail");
    const buttons = funnel.steps.map(([label, value, note], index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.closureStep = String(index);
      button.setAttribute("role", "listitem");
      button.style.setProperty("--closure-ratio", String(Math.log1p(value) / Math.log1p(maximum)));
      button.innerHTML = `<small>${String(index + 1).padStart(2, "0")}</small><span>${label}</span><i></i><strong>${value.toLocaleString()}</strong>`;
      button.addEventListener("click", () => {
        buttons.forEach((item) => item.classList.toggle("active", item === button));
        detail.innerHTML = `<b>${label}</b><span>${note}</span>`;
      });
      return button;
    });
    byId("closureFunnelSteps").replaceChildren(...buttons);
    buttons[0]?.click();
  }
  const supply = byId("systemSupplyAudit");
  supply.hidden = !system.supplyAudit;
  if (system.supplyAudit) renderSupplyAudit(system.supplyAudit);
  const a2Explorer = byId("a2CoronaExplorer");
  a2Explorer.hidden = key !== "a2";
  if (key === "a2") renderA2Explorer();
  const actions = byId("atlasSystemActions");
  actions.hidden = !system.actions?.length;
  actions.replaceChildren(...(system.actions || []).map(([label, scenario, stage, preparation]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.dataset.atlasScenario = scenario;
    button.dataset.atlasStage = String(stage);
    button.addEventListener("click", () => launchWorkflow(scenario, stage, preparation));
    return button;
  }));
  drawGrowthChart(system);
}

function launchWorkflow(scenario, stage, preparation = null) {
  const scenarioSelect = byId("scenarioSelect");
  const stageButton = document.querySelector(`[data-pipeline-stage="${stage}"]`);
  if (!scenarioSelect?.querySelector(`option[value="${scenario}"]`) || !stageButton) return;
  closeAtlas();
  if (window.gctsMaterialsWorkflow?.launch({ scenario, stage, preparation })) return;
  scenarioSelect.value = scenario;
  scenarioSelect.dispatchEvent(new Event("change", { bubbles: true }));
  if (preparation === "resolve-ice-vi" && !byId("iceViAverageButton")?.hidden) byId("iceViAverageButton").click();
  if (preparation === "resolve-ice-vi") byId("iceViMicrostateButton")?.click();
  stageButton.click();
  stageButton.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderSystems() {
  const tabs = byId("atlasSystemTabs");
  Object.entries(SYSTEMS).forEach(([key, system]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.system = key;
    button.innerHTML = `<span>${system.kind}</span><strong>${system.short}</strong>`;
    button.addEventListener("click", () => renderSystem(key));
    tabs.appendChild(button);
  });
  renderSystem("nacl");
}

window.addEventListener("gcts:open-evidence-system", (event) => {
  const key = event.detail?.system;
  if (!SYSTEMS[key]) return;
  atlasButton?.click();
  renderSystem(key);
});

function renderAnatomy(key) {
  const [title, copy, tags] = ANATOMY[key];
  document.querySelectorAll("[data-anatomy]").forEach((button) => button.classList.toggle("active", button.dataset.anatomy === key));
  byId("anatomyDetail").innerHTML = `<span>selected layer</span><h3>${title}</h3><p>${copy}</p><div>${tags.map((tag) => `<b>${tag}</b>`).join("")}</div>`;
}

function renderPhysics(key) {
  const layer = PHYSICS_MAP[key];
  document.querySelectorAll("[data-physics]").forEach((button) => {
    const active = button.dataset.physics === key;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  byId("physicsMapDetail").className = `physics-map-detail ${layer.status}`;
  byId("physicsMapDetail").innerHTML = `
    <header><span>${statusLabel(layer.status)}</span><h2>${layer.title}</h2></header>
    <div class="physics-flow">
      <article><small>physical content</small><p>${layer.physical}</p></article>
      <i>→</i><article><small>geometric encoding</small><p>${layer.geometric}</p></article>
      <i>→</i><article><small>effect on growth</small><p>${layer.growth}</p></article>
      <i>≠</i><article class="boundary"><small>explicit boundary</small><p>${layer.boundary}</p></article>
    </div>
    <div class="physics-system-table" role="table" aria-label="${layer.label} encoding by material system">
      <div class="physics-system-head" role="row"><span>system</span><span>physical structure</span><span>geometric surrogate</span><span>not claimed</span></div>
      ${layer.systems.map(([system, physical, geometry, boundary]) => `<div role="row"><strong>${system}</strong><span>${physical}</span><span>${geometry}</span><span>${boundary}</span></div>`).join("")}
    </div>`;
}

function renderHierarchyPhysicsTransport(receiptId = "iqc-reencoding") {
  const audit = buildHierarchyPhysicsTransport(receiptId);
  if (!hierarchyPhysicsTransportSelect.options.length) {
    audit.options.forEach((option) => hierarchyPhysicsTransportSelect.add(new Option(option.label, option.id)));
  }
  hierarchyPhysicsTransportSelect.value = audit.receiptId;
  hierarchyPhysicsTransportSummary.replaceChildren(...audit.stageSummaries.map((stage) => {
    const article = document.createElement("article");
    const small = document.createElement("small"); small.textContent = stage.label;
    const strong = document.createElement("strong"); strong.textContent = `${stage.causalCount} / ${stage.total}`;
    const span = document.createElement("span");
    span.textContent = `${stage.exactCount} exact · ${stage.counts.reevaluated} re-evaluated · ${stage.counts.representation} representation · ${stage.openCount} open`;
    article.append(small, strong, span);
    return article;
  }));
  const header = document.createElement("div"); header.className = "hierarchy-transport-head";
  header.setAttribute("role", "row");
  const channelHead = document.createElement("span"); channelHead.textContent = "physical channel";
  header.append(channelHead, ...HIERARCHY_TRANSPORT_STAGES.map((stage) => {
    const cell = document.createElement("span"); cell.textContent = stage.short; return cell;
  }));
  const rows = audit.rows.map((row) => {
    const button = document.createElement("button"); button.type = "button";
    button.className = row.id === selectedHierarchyPhysicsChannel ? "active" : "";
    button.dataset.hierarchyPhysicsChannel = row.id;
    button.setAttribute("role", "row");
    button.setAttribute("aria-pressed", String(row.id === selectedHierarchyPhysicsChannel));
    const label = document.createElement("strong"); label.textContent = row.label;
    button.append(label, ...row.stages.map((stage) => {
      const cell = document.createElement("span"); cell.className = stage.status;
      cell.textContent = stage.status === "exact" ? "exact" : stage.status === "reevaluated" ? "recheck"
        : stage.status === "representation" ? "accounted" : "open";
      cell.title = `${stage.label}: ${stage.statusLabel}`;
      return cell;
    }));
    button.addEventListener("click", () => {
      selectedHierarchyPhysicsChannel = row.id;
      renderHierarchyPhysicsTransport(audit.receiptId);
    });
    return button;
  });
  hierarchyPhysicsTransportMatrix.replaceChildren(header, ...rows);
  const selected = audit.rows.find((row) => row.id === selectedHierarchyPhysicsChannel) || audit.rows[0];
  if (selected.id !== selectedHierarchyPhysicsChannel) selectedHierarchyPhysicsChannel = selected.id;
  hierarchyPhysicsTransportDetail.replaceChildren();
  const detailHeader = document.createElement("header");
  const copy = document.createElement("span");
  const small = document.createElement("small"); small.textContent = selected.physical;
  const title = document.createElement("strong"); title.textContent = selected.label;
  copy.append(small, title);
  const frontier = document.createElement("b");
  frontier.textContent = selected.lastTransportedStage
    ? `causal through ${selected.lastTransportedStage.short}` : "no causal transport";
  detailHeader.append(copy, frontier);
  const evidence = document.createElement("div");
  const evidenceLabel = document.createElement("b"); evidenceLabel.textContent = "transport certificate";
  const evidenceCopy = document.createElement("p"); evidenceCopy.textContent = selected.evidence;
  evidence.append(evidenceLabel, evidenceCopy);
  const boundary = document.createElement("div");
  const boundaryLabel = document.createElement("b"); boundaryLabel.textContent = "claim boundary";
  const boundaryCopy = document.createElement("p"); boundaryCopy.textContent = selected.boundary;
  boundary.append(boundaryLabel, boundaryCopy);
  hierarchyPhysicsTransportDetail.append(detailHeader, evidence, boundary);
  renderHierarchyPhysicsInvestigation(audit.receiptId);
  hierarchyPhysicsTransportBoundary.textContent = `${audit.title} · ${audit.claimBoundary}`;
}

function renderHierarchyPhysicsInvestigation(receiptId) {
  const plan = buildHierarchyPhysicsInvestigation(receiptId,
    selectedHierarchyPhysicsChannel, selectedHierarchyPhysicsStage);
  activeHierarchyPhysicsInvestigation = plan;
  hierarchyPhysicsInvestigationState.className = plan.status;
  hierarchyPhysicsInvestigationState.textContent = `${plan.stageShort} · ${plan.statusLabel}`;
  hierarchyPhysicsInvestigationScales.replaceChildren(...HIERARCHY_TRANSPORT_STAGES.map((stage) => {
    const button = document.createElement("button"); button.type = "button";
    button.className = stage.id === plan.stageId ? "active" : "";
    button.setAttribute("aria-pressed", String(stage.id === plan.stageId));
    const transport = buildHierarchyPhysicsTransport(receiptId).rows
      .find((row) => row.id === plan.channelId).stages
      .find((candidate) => candidate.id === stage.id);
    const small = document.createElement("small"); small.textContent = stage.short;
    const strong = document.createElement("strong"); strong.textContent = transport.statusLabel;
    button.append(small, strong);
    button.addEventListener("click", () => {
      selectedHierarchyPhysicsStage = stage.id;
      renderHierarchyPhysicsInvestigation(receiptId);
    });
    return button;
  }));
  hierarchyPhysicsInvestigationQuestion.className = plan.status;
  hierarchyPhysicsInvestigationQuestion.innerHTML = `<small>${plan.channelLabel} · ${plan.stageLabel}</small><strong>${plan.question}</strong><p>${plan.nextAction}</p><b>${plan.operator}</b>`;
  const records = [
    ["01", "required evidence", plan.evidence],
    ["02", "geometric encoding", plan.encoding],
    ["03", "sealed validation", plan.validation],
    ["04", "execution hook", plan.execution],
  ];
  hierarchyPhysicsInvestigationFlow.replaceChildren(...records.flatMap(([index, label, copy], position) => {
    const article = document.createElement("article");
    const small = document.createElement("small"); small.textContent = index;
    const strong = document.createElement("strong"); strong.textContent = label;
    const paragraph = document.createElement("p"); paragraph.textContent = copy;
    article.append(small, strong, paragraph);
    if (position === records.length - 1) return [article];
    const arrow = document.createElement("i"); arrow.textContent = "→"; arrow.setAttribute("aria-hidden", "true");
    return [article, arrow];
  }));
  hierarchyPhysicsInvestigationGate.innerHTML = `<b>green gate</b>${plan.greenGate}`;
  hierarchyPhysicsInvestigationRoute.textContent = `${plan.route.label} →`;
  renderHierarchyPhysicsProtocolPacket(plan);
}

async function renderHierarchyPhysicsProtocolPacket(plan) {
  const version = ++hierarchyPhysicsProtocolRenderVersion;
  activeHierarchyPhysicsProtocolPacket = null;
  hierarchyPhysicsProtocolDigest.className = "pending";
  hierarchyPhysicsProtocolDigest.textContent = "computing SHA-256…";
  hierarchyPhysicsProtocolStatus.className = "pending";
  hierarchyPhysicsProtocolStatus.textContent = "Canonicalizing evidence, encoding, validation, hook, gate, and leakage invariants.";
  [hierarchyPhysicsProtocolCopyLink, hierarchyPhysicsProtocolCopyJson,
    hierarchyPhysicsProtocolDownload].forEach((button) => { button.disabled = true; });
  try {
    const packet = await buildHierarchyPhysicsProtocolPacket(plan.receiptId, plan.channelId, plan.stageId);
    if (version !== hierarchyPhysicsProtocolRenderVersion) return;
    activeHierarchyPhysicsProtocolPacket = packet;
    hierarchyPhysicsProtocolDigest.textContent = `${packet.sha256.slice(0, 16)}…`;
    const shared = sharedHierarchyPhysicsSelection;
    const sameSelection = shared && shared.receiptId === plan.receiptId
      && shared.channelId === plan.channelId && shared.stageId === plan.stageId;
    const verified = sameSelection && shared.expectedSha256 === packet.sha256;
    const mismatch = sameSelection && !verified;
    const malformedShare = sharedHierarchyPhysicsLoadError && !shared;
    hierarchyPhysicsProtocolDigest.className = verified ? "verified" : mismatch || malformedShare ? "mismatch" : "ready";
    hierarchyPhysicsProtocolStatus.className = verified ? "verified" : mismatch || malformedShare ? "mismatch" : "ready";
    hierarchyPhysicsProtocolStatus.textContent = malformedShare
      ? `Shared plan rejected: ${sharedHierarchyPhysicsLoadError.message}` : verified
      ? "Shared packet verified byte-for-byte · open the live conformance checklist to compare design with executed evidence."
      : mismatch ? "Shared packet SHA-256 mismatch · plan shown, but provenance is not verified."
        : "Deterministic design packet · coordinates and candidate actions absent · executionAuthorized = false.";
    if (sameSelection) {
      const launchAudit = hierarchyPhysicsProtocolLaunchAuditFromPacket(shared, packet);
      window.__gctsHierarchyPhysicsProtocolLaunchAudit = launchAudit;
      window.dispatchEvent(new CustomEvent("gcts:hierarchy-physics-protocol-audit",
        { detail: launchAudit }));
    }
    [hierarchyPhysicsProtocolCopyLink, hierarchyPhysicsProtocolCopyJson,
      hierarchyPhysicsProtocolDownload].forEach((button) => { button.disabled = false; });
  } catch (error) {
    if (version !== hierarchyPhysicsProtocolRenderVersion) return;
    hierarchyPhysicsProtocolDigest.className = "mismatch";
    hierarchyPhysicsProtocolDigest.textContent = "packet unavailable";
    hierarchyPhysicsProtocolStatus.className = "mismatch";
    hierarchyPhysicsProtocolStatus.textContent = error.message;
  }
}

function protocolPacketDownload(packet) {
  const blob = new Blob([packet.canonicalPacketJson], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a"); link.href = url;
  link.download = hierarchyPhysicsProtocolPacketFilename(packet);
  document.body.appendChild(link); link.click(); link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

async function copyProtocolText(text, success) {
  if (!navigator.clipboard?.writeText) throw new Error("Clipboard API unavailable.");
  await navigator.clipboard.writeText(text);
  hierarchyPhysicsProtocolStatus.className = "verified";
  hierarchyPhysicsProtocolStatus.textContent = success;
}

function routeToHierarchyPhysicsInvestigation() {
  const plan = activeHierarchyPhysicsInvestigation;
  if (!plan) return;
  launchWorkflow(plan.route.scenario, plan.route.stage);
  window.setTimeout(() => {
    const focus = byId(plan.route.focusId);
    focus?.scrollIntoView({ behavior: "smooth", block: "center" });
    if (focus?.matches("select,button,input")) focus.focus({ preventScroll: true });
  }, 180);
}

function renderTimeline() {
  byId("researchTimeline").innerHTML = TIMELINE.map(([index, title, copy, status]) => `<article class="${status}"><span>${index}</span><div><small>${status === "proved" ? "established" : status === "progress" ? "measured advance" : "current frontier"}</small><h3>${title}</h3><p>${copy}</p></div><i></i></article>`).join("");
}

function renderLedger(filter = "all") {
  document.querySelectorAll("[data-ledger-filter]").forEach((button) => button.classList.toggle("active", button.dataset.ledgerFilter === filter));
  byId("claimLedger").innerHTML = CLAIMS.filter(([status]) => filter === "all" || status === filter).map(([status, title, copy]) => `<article class="${status}"><span>${status}</span><h3>${title}</h3><p>${copy}</p></article>`).join("");
}

function selectTab(key) {
  document.querySelectorAll("[data-atlas-tab]").forEach((button) => button.classList.toggle("active", button.dataset.atlasTab === key));
  document.querySelectorAll("[data-atlas-panel]").forEach((panel) => {
    const active = panel.dataset.atlasPanel === key;
    panel.classList.toggle("active", active);
    panel.hidden = !active;
  });
}

atlasButton.addEventListener("click", openAtlas);
ribbonButton.addEventListener("click", openAtlas);
closeButton.addEventListener("click", closeAtlas);
atlas.addEventListener("click", (event) => { if (event.target === atlas) closeAtlas(); });
document.querySelectorAll("[data-atlas-tab]").forEach((button) => button.addEventListener("click", () => selectTab(button.dataset.atlasTab)));
document.querySelectorAll("[data-anatomy]").forEach((button) => button.addEventListener("click", () => renderAnatomy(button.dataset.anatomy)));
document.querySelectorAll("[data-physics]").forEach((button) => button.addEventListener("click", () => renderPhysics(button.dataset.physics)));
hierarchyPhysicsTransportSelect.addEventListener("change", () =>
  renderHierarchyPhysicsTransport(hierarchyPhysicsTransportSelect.value));
hierarchyPhysicsInvestigationRoute.addEventListener("click", routeToHierarchyPhysicsInvestigation);
hierarchyPhysicsProtocolCopyLink.addEventListener("click", () => {
  const packet = activeHierarchyPhysicsProtocolPacket;
  if (!packet) return;
  copyProtocolText(hierarchyPhysicsProtocolShareUrl(window.location.href, packet),
    "Verified plan link copied · reopening recomputes and checks the full SHA-256.")
    .catch((error) => { hierarchyPhysicsProtocolStatus.textContent = error.message; });
});
hierarchyPhysicsProtocolCopyJson.addEventListener("click", () => {
  const packet = activeHierarchyPhysicsProtocolPacket;
  if (!packet) return;
  copyProtocolText(packet.canonicalPacketJson,
    "Canonical protocol JSON copied · plan only · no coordinates or candidate actions embedded.")
    .catch((error) => { hierarchyPhysicsProtocolStatus.textContent = error.message; });
});
hierarchyPhysicsProtocolDownload.addEventListener("click", () => {
  if (activeHierarchyPhysicsProtocolPacket) protocolPacketDownload(activeHierarchyPhysicsProtocolPacket);
});
hierarchyPhysicsProtocolConformanceRoute.addEventListener("click", () => {
  closeAtlas();
  byId("receiptScaleBridgeConformance")?.scrollIntoView({ behavior: "smooth", block: "center" });
});
document.querySelectorAll("[data-ledger-filter]").forEach((button) => button.addEventListener("click", () => renderLedger(button.dataset.ledgerFilter)));
methodLink.addEventListener("click", closeAtlas);
document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !atlas.hidden) closeAtlas(); });

renderMatrix();
renderSystems();
renderAnatomy("cover");
renderPhysics("bonding");
if (sharedHierarchyPhysicsSelection) {
  selectedHierarchyPhysicsChannel = sharedHierarchyPhysicsSelection.channelId;
  selectedHierarchyPhysicsStage = sharedHierarchyPhysicsSelection.stageId;
  renderHierarchyPhysicsTransport(sharedHierarchyPhysicsSelection.receiptId);
  selectTab("physics");
  window.setTimeout(openAtlas, 0);
} else {
  renderHierarchyPhysicsTransport();
}
renderTimeline();
renderLedger();
