import { executeIceMolecularAnchorGrowth } from "./ice-molecular-anchor-growth.js";

const byId = (id) => document.getElementById(id);

const atlas = byId("evidenceAtlas");
const atlasButton = byId("evidenceAtlasButton");
const ribbonButton = byId("evidenceRibbonButton");
const closeButton = byId("evidenceAtlasClose");
const methodLink = byId("atlasMethodLink");

const ICE_PORT_ARTIFACT = await fetch(new URL(
  "./ice-molecular-port-artifact.json?v=20260824-1", import.meta.url)).then((response) => {
  if (!response.ok) throw new Error(`Cannot load frozen ice evidence: ${response.status}`);
  return response.json();
});
const ICE_TRACES = Object.fromEntries(["iceIh", "iceIc"].map((caseId) =>
  [caseId, executeIceMolecularAnchorGrowth(ICE_PORT_ARTIFACT, caseId)]));
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
    summary: "Ice is covered molecularly rather than by atom-centred coordination spokes. A bent H₂O motif, hydrogen-bond bridge polyhedra, and O₆ ring-boundary gap clusters cover the periodic configuration; a sealed eight-port grammar then transfers exact unseen oxygen anchors until a conservative fixed point.",
    values: [27, 27 + acceptedPerWave("iceIh")[0], 27 + acceptedPerWave("iceIh")[0] + acceptedPerWave("iceIh")[1]], verifiedThrough: 2,
    metrics: [["Ih isometry classes", "1 + 3 + 33"], ["Ic isometry classes", "1 + 2 + 39"], ["Ice VI conformers / ports", "5 / 84"], ["blind O frontiers", `Ih ${acceptedPerWave("iceIh").join(" → ")} · VI 4 → 3 → 1`]],
    verdict: ["progress", "Complete molecular cover and finite anchor transfer pass · proton and stationary growth remain open"],
    evidence: [
      ["Complete molecular cover", "Ih 216 / 216 · Ic 192 / 192", "H₂O molecules cover the atoms; bridge and O₆ ring-boundary clusters encode the interstitial connection geometry."],
      ["Frozen port fit", `${ICE_PORT_ARTIFACT.provenance.trainingMolecules} H₂O · ${ICE_PORT_ARTIFACT.ports.length} ports`, `${ICE_PORT_ARTIFACT.provenance.trainingAtoms} positions/species only; proper SE(3); target used = ${ICE_PORT_ARTIFACT.provenance.targetUsed}.`],
      ["Sealed finite execution", `Ih ${acceptedPerWave("iceIh").join(" → ")} · Ic ${acceptedPerWave("iceIc").join(" → ")}`, "Every accepted unseen oxygen anchor is exact; unsupported depth is rejected at a finite fixed point."],
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
    metrics: [["causal nuclei", "2 disjoint"], ["local growth", "295 / 295 exact"], ["train hierarchy", "9 positive levels"], ["stationary witnesses", "0"]],
    verdict: ["progress", "Real-material finite continuation passes · hierarchical transfer and stationarity remain open"],
    evidence: [
      ["Causal section", "178 / 178 + 117 / 117", "Bounded connection witnesses beat 31 ownership shuffles."],
      ["Deep hierarchy", "80→36→22→15→8→6→4→2→1", "Every later retained type is witnessed in at least two raw windows."],
      ["Sealed nucleus", "82 partial candidates · 6 exact", "One-child completion exposes policy headroom without target leakage."],
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
};

const MATRIX = [
  ["NaCl crystal", ["pass", "100% colored cover"], ["pass", "2 exact unseen levels"], ["pass", "8-child cell macro"], ["pass", "4.19m / 7 actions"]],
  ["H₂O ice", ["pass", "Ih 216 · Ic 192"], ["pass", "16→8 · 12 exact O"], ["open", "no promoted ice rule"], ["open", "finite fixed point"]],
  ["Ideal IQC", ["pass", "2,064 / 2,064"], ["pass", "31,521 exact sites"], ["progress", "6 train levels"], ["open", "no 3-scale key"]],
  ["Cd₅.₇Yb IQC", ["pass", "2,385 / 2,385"], ["pass", "295 / 295 local"], ["progress", "9 train · 4 replay"], ["open", "no stationary key"]],
  ["Cu–Zr glass", ["control", "cover + residuals"], ["control", "not uniquely defined"], ["control", "recursion rejected"], ["control", "negative passes"]],
];

const MATRIX_DETAILS = {
  "NaCl crystal": "The learner receives neither the unit cell nor Fm-3m. A positions-only discovery proposes the radix and offsets; the independently learned proper-port graph must witness the same eight-child production at three scales before the stationary gate turns green.",
  "H₂O ice": "The periodic ice configurations are not reduced to atom-centred shells. One bent H₂O class covers each molecule; decorated hydrogen-bond bridges and O₆ ring boundaries encode connections and fill the periodically extended cover. Eight proper-SE(3) ports learned on 201 Ih atoms emit exact disjoint oxygen frontiers, but mutually exclusive proton orientations are still symbolic, so clusters² and stationary growth remain red.",
  "Ideal IQC": "Exact continuation is real and self-fed, but different promoted productions appear at successive levels. Deep compression is not renamed exponential growth: the strict stationary audit requires the same exact semantic production and learned scale twice in succession.",
  "Cd₅.₇Yb IQC": "The real-material model is the hardest transfer case. Bounded local marking succeeds for finite primitive growth, but exact promoted clusters are sparse and nucleus-dependent. Dormant types remain frozen rather than being refit on held-out atoms.",
  "Cu–Zr glass": "The negative control protects the benchmark from a trivial answer. Residual clusters guarantee representation, but no stable macro production, unique exterior continuation, or million-site symbolic claim is admitted.",
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
    status: "open", label: "thermodynamics + kinetics", title: "Leap-frogging dynamics is the approximation boundary",
    physical: "Temperature, pressure, chemical potentials, free-energy differences, diffusion barriers, nucleation rates, phonons, and time-dependent disorder.",
    geometric: "Structural evidence, connection successes/failures, dimensionless contact/angle strain, composition drift, and optional supplied formal-charge drift are retained. Fixed-topology snapshot pairs may additionally expose local best-affine F, Green–Lagrange invariants, D²min, and neighbor exchange while one selected frame alone supplies the cluster grammar and growth seed.",
    growth: "Tree search jumps directly between geometrically certified states. Soft geometry may order legal branches; proposal checks and backtracks measure computational work, not elapsed physical time.",
    boundary: "The portal predicts structurally admissible continuation, not a growth rate or thermodynamic phase diagram. Snapshot order is not time, correlated frames are not claimed independent, and no velocity, force, or integration step is used. MD/DFT or experimental labels must calibrate kinetic claims separately.",
    systems: [
      ["NaCl", "Exact structural recurrence", "Symbolic scale leap", "No physical growth time"],
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
  ["open", "Proton-resolved ice growth", "The current section carries competing H₂O pose domains symbolically. It does not yet choose all proton orientations or certify a promoted stationary ice production."],
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
  ["open", "Generic QC stationarity", "No exact chemistry–chirality–directed-port production recurs across three consecutive QC levels."],
  ["progress", "IQC option-preserving beam", "A width-four target-free beam keeps the branch with the largest compatible next frontier. Frozen before wave 20, it adds 120/120 exact held-forward sites; all 24 waves are 572/572 exact. Spatial confirmation and stationarity remain open."],
  ["open", "Generic million-site QC growth", "Specialized/address ceilings cross one million; the family-blind cluster-of-clusters executor does not yet."],
  ["open", "Pure-port crystal closure", "NaCl's port graph certifies the learned cell rule, but the radix/offset proposal still comes from a positions-only grid learner."],
  ["open", "Explicit output cost", "Symbolic derivations compress actions; emitting every atom remains linear and is not claimed to replace molecular dynamics time integration."],
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
  svg.innerHTML = `<g class="chart-grid">${grid}</g><polygon class="growth-area" points="${area}"/><polyline class="growth-line" points="${points}"/>${dots}<g class="x-labels">${values.map((_value, index) => `<text x="${x(index)}" y="${height - 24}" text-anchor="middle">a${index}</text>`).join("")}</g>`;
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
  byId("atlasCurveTitle").textContent = `${system.short} · growth by learned action`;
  byId("systemEvidenceCards").innerHTML = system.evidence.map(([label, value, note]) => `<article><small>${label}</small><strong>${value}</strong><p>${note}</p></article>`).join("");
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
document.querySelectorAll("[data-ledger-filter]").forEach((button) => button.addEventListener("click", () => renderLedger(button.dataset.ledgerFilter)));
methodLink.addEventListener("click", closeAtlas);
document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !atlas.hidden) closeAtlas(); });

renderMatrix();
renderSystems();
renderAnatomy("cover");
renderPhysics("bonding");
renderTimeline();
renderLedger();
