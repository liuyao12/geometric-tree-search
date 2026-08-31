import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import {
  createTilingStream,
  GCTS_CATALOG_MIN_PERIODIC_MOTIF_TILES,
  isGctsFigureVisibleInCatalog,
  preprocessTilingSystem,
  tileSpecs
} from "../apps/3d-lattice-tiler/engine.js";
import {
  classifyLatticeCandidateScreen,
  LATTICE_POLYHEDRON_CENSUS_POOL,
  LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES,
  LATTICE_POLYHEDRON_PERIODIC_REJECTS,
  LATTICE_POLYHEDRON_SCREENING,
  LATTICE_POLYHEDRON_SHELL_REJECTS,
  LATTICE_POLYHEDRON_SIZE11_CONTROLS,
  LATTICE_POLYHEDRON_SIZE11_SCREENING,
  LATTICE_POLYHEDRON_SIZE12_CONTROLS,
  LATTICE_POLYHEDRON_SIZE12_SCREENING,
  LATTICE_POLYHEDRON_SIZE13_CONTROLS,
  LATTICE_POLYHEDRON_SIZE13_SCREENING,
  LATTICE_POLYHEDRON_SURVIVORS
} from "../assets/lattice-polyhedron-survivors.js";
import { A2_LAYERED_SIZE7_CANDIDATES } from "../assets/a2-layered-size7-candidates.js";
import { A2_LAYERED_SIZE8_CANDIDATES } from "../assets/a2-layered-size8-candidates.js";
import { A2_LAYERED_SIZE9_CANDIDATES } from "../assets/a2-layered-size9-candidates.js";
import { A2_SLICED_SIZE7_CANDIDATES } from "../assets/a2-sliced-size7-candidates.js";
import { A2_SLICED_SIZE8_CANDIDATES } from "../assets/a2-sliced-size8-candidates.js";
import { A2_SLICED_SIZE9_CANDIDATES } from "../assets/a2-sliced-size9-candidates.js";
import {
  polycubeCoronaBoundaryKey,
  searchPolycubeCorona,
  verifyPolycubeCoronaPatch
} from "../assets/polycube-corona-search.js";

const fingerprintDigest = values => createHash("sha256")
  .update(values.slice().sort().join("\n"))
  .digest("hex");

const growthWorkerSource = await readFile(
  new URL("../apps/3d-lattice-tiler/growth-benchmark-worker.js", import.meta.url),
  "utf8"
);
const growthAppSource = await readFile(
  new URL("../apps/3d-lattice-tiler/app.js", import.meta.url),
  "utf8"
);
const tilerStyleSource = await readFile(
  new URL("../apps/3d-lattice-tiler/style.css", import.meta.url),
  "utf8"
);
const canonicalTilerHtml = await readFile(
  new URL("../3d-lattice-tiler/index.html", import.meta.url),
  "utf8"
);
const sourceTilerHtml = await readFile(
  new URL("../apps/3d-lattice-tiler/index.html", import.meta.url),
  "utf8"
);
const appModuleVersion = html => html.match(/<script type="module" src="\.\/app\.js\?v=([^"]+)"/)?.[1];
const styleVersion = html => html.match(/<link rel="stylesheet" href="\.\/style\.css\?v=([^"]+)"/)?.[1];
assert.equal(
  appModuleVersion(canonicalTilerHtml),
  appModuleVersion(sourceTilerHtml),
  "the root GitHub Pages wrapper must load the same cache-busted app module as the source page"
);
assert.equal(
  styleVersion(canonicalTilerHtml),
  styleVersion(sourceTilerHtml),
  "the root GitHub Pages wrapper must load the same cache-busted stylesheet as the source page"
);
const preparedCube = preprocessTilingSystem({ mode_key: "cube", polycube_lattice: "z3" }, tileSpecs);
assert.equal(preparedCube.summary.point_group_order, 24);
assert.equal(preparedCube.summary.orientation_count, 1);
assert.equal(preparedCube.summary.tiles[0].stabilizer_order, 24);
assert.ok(preparedCube.summary.tiles.every(tile =>
  tile.orientation_count * tile.stabilizer_order === tile.point_group_order
), "orientation representatives must be the point-group cosets of the tile stabilizer");
assert.match(growthWorkerSource, /preprocessTilingSystem\(run\.config, tileSpecs\)/);
assert.match(growthWorkerSource, /type: "mode-ready"/);
assert.match(growthWorkerSource, /type !== "go"/);
assert.match(growthWorkerSource, /periodic_patch_unbounded: false/);
assert.match(growthWorkerSource, /periodic_stop_at_growth_goal: mode\.id === "translational"/);
assert.match(growthWorkerSource, /translationalPatchGoal/);
assert.match(growthAppSource, /translational_growth_goal_without_certificate/);
assert.match(growthAppSource, /readyModes\.size === GROWTH_MODES\.length/);
assert.match(growthAppSource, /performance\.timeOrigin \+ performance\.now\(\) \+ 100/);
assert.match(growthAppSource, /Preprocessing \(excluded\)/);
assert.match(
  growthAppSource,
  /function scheduleFullUpdate\(snapshot\) \{[\s\S]*?resetLiveFaceStacks\(snapshot\);[\s\S]*?resetLiveFrontierPoints\(snapshot\);[\s\S]*?pendingFullUpdate = snapshot;/,
  "a throttled full render must synchronize the live face model before later deltas"
);
assert.match(
  growthAppSource,
  /if \(pendingFullUpdate\) \{[\s\S]*?faces: liveFaces\(\),[\s\S]*?frontier_points: \[\.\.\.liveFrontierPoints\.values\(\)\]/,
  "backtracking deltas must update any full snapshot waiting to render"
);
assert.match(
  tilerStyleSource,
  /grid-template-rows: auto auto auto auto minmax\(190px, 1fr\);[\s\S]*?overflow-y: auto;/,
  "short desktop viewports must be able to scroll to a nonzero-height tile catalogue"
);
assert.match(growthWorkerSource, /id: "proof"[\s\S]*?proof: true/, "the research worker must retain the headless proof policy");
assert.match(
  growthWorkerSource,
  /id: "proof_nogood"[\s\S]*?proof: true,[\s\S]*?nogood: true/,
  "the research worker must retain the complementary exact-nogood proof policy"
);
assert.match(
  growthWorkerSource,
  /forced_move_layer_lag_cap: mode\.proof \|\| exactLearningShell \? 0 : baseConfig\.forced_move_layer_lag_cap/,
  "proof and exact learning shell lanes must disable generational pruning"
);
assert.match(
  growthWorkerSource,
  /\["free_range", "gcts", "rl", "gcts_rl"\]\.includes\(mode\.id\)/,
  "Free-range, GCTS, RL, and GCTS+RL must use the same exact shell state space"
);
assert.match(
  growthWorkerSource,
  /terminalCleanupRemoval[\s\S]*?message\.action === "remove"[\s\S]*?termination_reason/,
  "an inconclusive resource-limit unwind must not draw a false drop to zero"
);
assert.match(
  growthWorkerSource,
  /type === "extend-time"[\s\S]*?stopToken\.additional_time_ms/,
  "active benchmark workers must accept clock extensions without restarting"
);
assert.match(
  growthWorkerSource,
  /time_limit_ms: null,[\s\S]*?awaitClockBudget[\s\S]*?stopToken\.resume_clock/,
  "the benchmark clock cap must pause a live generator instead of unwinding its search stack"
);
assert.match(
  growthAppSource,
  /message\.type === "mode-paused"[\s\S]*?Continue to add clock time/,
  "paused lanes must remain visibly resumable"
);
assert.match(
  growthAppSource,
  /function extendGrowthBenchmark\(\)[\s\S]*?type: "extend-time"[\s\S]*?additionalTimeMs/,
  "Continue must add clock time to every active lane"
);
assert.doesNotMatch(sourceTilerHtml, /id="continueButton"/, "Run, Pause, and Continue must be one button");
assert.match(
  growthAppSource,
  /if \(!growthRunning\) startGrowthBenchmark\(\);[\s\S]*?else if \(growthPaused\) extendGrowthBenchmark\(\);[\s\S]*?else pauseGrowthBenchmark\(\);/,
  "the unified control must cycle through Run, Pause, and Continue"
);
assert.match(
  growthWorkerSource,
  /type === "pause"[\s\S]*?stopToken\.manual_pause = true/,
  "Pause must preserve each live worker at a safe generator checkpoint"
);
assert.match(
  growthAppSource,
  /function stopActiveRunAfterSelectionChange\(\)[\s\S]*?stopGrowthBenchmark[\s\S]*?growthSeries\.clear\(\)[\s\S]*?setRunButton\(\)/,
  "selecting another tile must discard the old benchmark and restore Run"
);
assert.match(growthWorkerSource, /generic_failure_memo: !!mode\.proof \|\| exactLearningShell/, "proof and exact learning shell lanes must memoize exact failures");
assert.match(
  growthWorkerSource,
  /generic_connected_patch_enumeration: !!mode\.proof && !shellSearch/,
  "the proof lane must enumerate every legal exposed-face extension"
);
assert.match(
  growthWorkerSource,
  /generic_failure_memo_symmetry: shellSearch \? "rigid" : "fixed"/,
  "count proofs must retain fixed-frame memoization while shell proofs use rooted rigid keys"
);
assert.match(
  growthWorkerSource,
  /generic_geometric_nogood: \["gcts", "gcts_rl"\]\.includes\(mode\.id\)[\s\S]*?\|\| \(!!mode\.nogood && !shellSearch\)/,
  "GCTS shell lanes must retain exact translated failure markings"
);
assert.match(growthWorkerSource, /generic_geometric_nogood_max_clauses: 20000/);
assert.match(growthWorkerSource, /generic_geometric_nogood_index: true/);
assert.match(
  growthWorkerSource,
  /generic_geometric_nogood_activation_failure_states: mode\.nogood \? 25 : 0/,
  "the complementary web lane must delay nogood application until 25 failed states"
);
assert.match(
  growthWorkerSource,
  /seeded_tie_breaks: !!mode\.proof/,
  "the proof comparison lane must use replayable seeded tie diversification"
);
assert.match(
  growthWorkerSource,
  /generic_periodic_certificate_check_distinct_patches: !!mode\.proof && !shellSearch/,
  "the proof comparison lane must check distinct branch patches at the same size"
);
assert.match(
  growthWorkerSource,
  /generic_periodic_certificate_checkpoint_sampling_policy: mode\.proof \? "hybrid" : "prefix"/,
  "the proof comparison lane must retain early patches and sample later branches"
);
assert.match(
  growthWorkerSource,
  /generic_periodic_certificate: !!mode\.proof && !shellSearch/,
  "the proof lane must test a reached target patch for an exact translational quotient"
);
assert.match(growthWorkerSource, /exhaustive: !!mode\.proof/, "only the proof comparison lane may claim exhaustive search");
assert.match(growthWorkerSource, /certificateKind: final\?\.tiling_evidence\?\.kind/, "proof certificates must reach the UI");
assert.match(growthWorkerSource, /id: "proof_crystal"[\s\S]*?moveOrder: "crystal"[\s\S]*?proof: true/, "the crystal lane must retain exact proof-search semantics");
assert.match(growthWorkerSource, /id: "proof_crystal"[\s\S]*?label: "Proof search · crystal rank"/, "the hidden research policy must retain its diagnostic label");
const publicGrowthModesSource = growthAppSource.match(/const GROWTH_MODES = \[([\s\S]*?)\n\];/)?.[1] ?? "";
assert.deepEqual(
  [...publicGrowthModesSource.matchAll(/id: "([^"]+)"/g)].map(match => match[1]),
  ["free_range", "gcts", "rl", "gcts_rl", "translational", "isohedral"],
  "the public chart must compare exactly the six solver lanes"
);
assert.deepEqual(
  [...publicGrowthModesSource.matchAll(/label: "([^"]+)"/g)].map(match => match[1]),
  ["Free-range", "GCTS", "RL", "GCTS + RL", "Translational", "Isohedral"]
);
assert.match(growthWorkerSource, /id: "free_range"[\s\S]*?label: "Free-range"/);
assert.match(growthWorkerSource, /id: "gcts"[\s\S]*?label: "GCTS"[\s\S]*?strategy: "free_range"/);
assert.match(growthWorkerSource, /id: "rl"[\s\S]*?moveOrder: "rl"/);
assert.match(growthWorkerSource, /id: "gcts_rl"[\s\S]*?moveOrder: "rl"/);
assert.match(growthWorkerSource, /id: "translational"[\s\S]*?moveOrder: "periodic"/);
assert.match(
  growthWorkerSource,
  /agent_policy: \["rl", "gcts_rl"\]\.includes\(mode\.id\) \? "cold_linucb" : null/,
  "only RL lanes may retain a cold next-placement model"
);
assert.match(growthWorkerSource, /agent_ucb_alpha: \["rl", "gcts_rl"\][\s\S]*?\? 0 : null/);
assert.match(growthWorkerSource, /learned_layer_macro: false/, "RL comparisons must place one tile per action");
assert.match(growthAppSource, /All six lanes finished\./);
assert.match(growthAppSource, /positive-control low-copy CEGAR run rejects/);
assert.match(growthAppSource, /Radius four is still unexhausted/);
assert.match(growthAppSource, /Pairwise next-ring coverability promotes/);
assert.match(growthAppSource, /Lazy GCTS independently replays/);
assert.match(growthWorkerSource, /message\.type === "placement_delta" && !terminalCleanupRemoval && tiles !== lastHistoryTileCount/);
assert.match(growthWorkerSource, /type: "sample-batch"/);
assert.doesNotMatch(growthWorkerSource, /tiles > best/);
assert.match(growthWorkerSource, /const exactNoTiling = final\?\.result_kind === "no_tiling"/);
assert.match(growthWorkerSource, /if \(exactNoTiling\) \{[\s\S]*?tiles: 0, terminal: true/);
assert.match(growthAppSource, /certified that no tiling is possible/);
assert.match(growthAppSource, /result\?\.criterion === "shell"[\s\S]*?completed shell \$\{shell\}[\s\S]*?max shell \$\{maxShell\}/);
assert.match(growthAppSource, /GCTS[^\n]*inconclusive|\["gcts", "gcts_rl"\][\s\S]*?searchIncomplete/);
assert.doesNotMatch(sourceTilerHtml, /name="criterion" value="layer"/);
assert.match(sourceTilerHtml, /Order-independent face-adjacency shell; exhaustive failure can prove non-tiling/);
assert.match(sourceTilerHtml, /id="growthHistoryBack"[\s\S]*?id="growthHistoryForward"/);
assert.match(growthAppSource, /function stepGrowthHistory\(direction\)/);
assert.match(
  growthAppSource,
  /const faceGroup = new THREE\.Group\(\);[\s\S]*?const edgeGroup = new THREE\.Group\(\);[\s\S]*?const frontierPointGroup = new THREE\.Group\(\);/,
  "the main renderer must retain persistent scene groups across snapshots"
);
assert.match(growthAppSource, /reconcileRenderBatches\(\s*faceGroup,/);
assert.match(growthAppSource, /reconcileRenderBatches\(\s*edgeGroup,/);
assert.match(
  growthAppSource,
  /function updateScene\(snapshot, options = \{\}\) \{[\s\S]*?preserveView = true/,
  "ordinary scene updates must preserve the camera unless the caller explicitly requests an initial fit"
);
assert.doesNotMatch(
  growthAppSource,
  /(?:faceGroup|edgeGroup|frontierPointGroup)\s*=\s*next/,
  "snapshot rendering must reconcile the existing scene rather than replace its groups"
);
const showGrowthSnapshotSource = growthAppSource.match(
  /function showGrowthSnapshot\(modeId, pointIndex = null\) \{[\s\S]*?\n\}/
)?.[0] ?? "";
assert.match(showGrowthSnapshotSource, /updateScene\(snapshot, \{ preserveView: true \}\)/);
assert.doesNotMatch(
  showGrowthSnapshotSource,
  /rootCentered\s*=\s*false|preserveView:\s*false/,
  "growth-history navigation must preserve the current camera orientation"
);
assert.doesNotMatch(
  growthAppSource,
  /function activateGrowthMode\(/,
  "the growth panel must not own a lane-switching helper"
);
assert.match(
  growthAppSource,
  /function handleGrowthPlotClick\(event\) \{[\s\S]*?const modeId = selectedGrowthMode\(\);[\s\S]*?clickedModeId !== modeId[\s\S]*?showGrowthSnapshot\(modeId, pointIndex\);/,
  "growth markers must only inspect history for the lane selected in the controls"
);
assert.doesNotMatch(
  growthAppSource.match(/function handleGrowthPlotClick\(event\) \{[\s\S]*?\n\}/)?.[0] ?? "",
  /(?:strategyRadios|strategySelect|setRadioValue|\.checked\s*=|dispatchEvent)/,
  "growth-curve clicks must never mutate the selected solver lane"
);
assert.match(
  growthAppSource,
  /mode: inspectable \? "lines\+markers" : "lines"/,
  "only the lane selected outside the growth panel may expose clickable markers"
);
assert.match(
  growthAppSource,
  /legend: \{[\s\S]*?itemclick: false,[\s\S]*?itemdoubleclick: false/,
  "the Plotly legend must not switch or hide growth lanes"
);
assert.match(
  growthAppSource,
  /plotly_legendclick[\s\S]*?plotly_legenddoubleclick[\s\S]*?growthPlotLegendBound = true/,
  "the chart must explicitly cancel both Plotly legend interaction events"
);
assert.doesNotMatch(sourceTilerHtml, /Learning Free-range/);
assert.match(sourceTilerHtml, /<b>GCTS<\/b>/);
assert.match(growthAppSource, /finite-patch witnesses, not space-tiling certificates/, "the catalog must not overstate a large GCTS patch");
assert.match(
  growthAppSource,
  /periodic_exact_through\s*\n?\s*\?\?\s*figure\.census_candidate\.screening\.periodic_hnf_max_motif_tiles/,
  "fresh survivor cards must fall back across the new and legacy exact-period fields"
);
assert.match(growthAppSource, /prioritizes independent repeated same-orientation translations/, "the catalog must explain the current crystal-rank policy");
assert.match(growthAppSource, /all four old 10_45026 witnesses repeated 57 of 60 placements along one direction/, "the catalog must disclose the misleading collinear target witnesses");
assert.match(growthAppSource, /recovered the known three-tile quotient of control 10_24775/, "the internal-period screen must expose its positive control");
assert.match(growthAppSource, /certified an embedded \$\{motifSize\}-tile translational quotient/, "the UI must distinguish an embedded motif from the entire target patch");
assert.match(
  growthAppSource,
  /this excludes those particular patches as translational fundamental domains, not other possible motifs/,
  "the catalog must state the narrow scope of a negative target-patch quotient check"
);
assert.match(growthAppSource, /Certified periodic control/, "the mined six-tile quotient must be visible as a periodic control");
assert.match(growthAppSource, /GCTS non-tiler controls/, "the exact non-tiler certificates must remain available as controls");
assert.match(
  growthAppSource,
  /hybrid branch screen saw/,
  "the catalog must expose the stronger distinct-branch checkpoint evidence"
);
assert.match(
  growthAppSource,
  /proper-rigid-motion patch fingerprints/,
  "the catalog must distinguish state-path check counts from globally distinct geometry"
);
assert.match(
  growthAppSource,
  /fixed-versus-rigid failure-memo replay produced identical search outcomes/,
  "the catalog must expose the measured reason for retaining fixed-root memo keys"
);
assert.match(
  growthAppSource,
  /complementary translation-equivariant nogood policy/,
  "the catalog must expose the complementary nogood screen"
);
assert.match(
  growthAppSource,
  /delayed until 25 failed states have been learned/,
  "the catalog must disclose the benchmarked nogood activation delay"
);
assert.match(
  growthAppSource,
  /On five unseen seeds/,
  "the catalog must expose the holdout generalization screen"
);
assert.match(
  growthAppSource,
  /remain complementary rather than universally superior/,
  "the catalog must not overstate delayed nogood generalization"
);
assert.match(
  growthAppSource,
  /that target patch is not a translational quotient/,
  "the completed proof-lane summary must retain the target-patch quotient result"
);

assert.equal(LATTICE_POLYHEDRON_CENSUS_POOL.length, 16, "the rescreener and catalog must share the full source pool");
assert.equal(
  LATTICE_POLYHEDRON_CENSUS_POOL.filter(candidate => candidate.screening.status === "exact_rejection").length,
  16,
  "every original candidate must now retain an exact rejection certificate"
);
assert.equal(LATTICE_POLYHEDRON_SCREENING.source_pool_size, LATTICE_POLYHEDRON_CENSUS_POOL.length);
const archivedScreening = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-rescreen-2026-08-17.json", import.meta.url),
  "utf8"
));
const archivedDiversifiedScreening = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-diversified-gcts-screen-2026-08-18.json", import.meta.url),
  "utf8"
));
const archivedProofScreening = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-gcts-checkpoint-screen-2026-08-18.json", import.meta.url),
  "utf8"
));
const archivedPrefixScreening = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-distinct-checkpoint-screen-2026-08-18.json", import.meta.url),
  "utf8"
));
const archivedDistinctScreening = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-hybrid-checkpoint-screen-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedFixedFrameOverlap = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-global-checkpoint-overlap-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedGlobalOverlap = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-rigid-checkpoint-overlap-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedFailureMemoAb = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-failure-memo-ab-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedNogoodPortfolio = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-nogood-proof-portfolio-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedDelayedNogood = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-delayed-nogood-screen-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedHoldout = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-holdout-screen-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedStagnationNogoodAb = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-stagnation-nogood-ab-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedBudgetOrder = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-budget-order-screen-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedInternalPeriod = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-internal-period-screen-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedGlobalExtension = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-global-extension-screen-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedCompleteShell = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-extendable-shell-screen-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedShellContinuation = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-10_45033-shell-continuation-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedCandidatePeriodic = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-10_45033-periodic-certificate-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedSize11FirstStage = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size11-first-stage-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedSize11ShellThree = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size11-shell3-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedSize11Periodic = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size11-periodic-summary-2026-08-19.json", import.meta.url),
  "utf8"
));
const archivedSize12FirstStage = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size12-full-isometry-first-stage-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize12ShellTwo = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size12-full-isometry-shell2-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize12Periodic = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size12-full-isometry-easy-lanes-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize12ShellThree = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size12-full-isometry-shell3-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize12ShellFour = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size12-full-isometry-shell4-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize12ShellSix = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size12-full-isometry-shell6-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize12Periodic204255 = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size12-12_204255-shell6-periodicity-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize12Periodic405129 = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size12-12_405129-shell6-periodicity-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize12Periodic235174 = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size12-12_235174-periodic-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize12CandidateShellThreePortfolio = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size12-12_235174-shell3-portfolio-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize12CandidateShellFourExtensions = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size12-12_235174-shell4-extension-portfolio-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize12CandidatePeriodicityPortfolio = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size12-12_235174-shell3-periodicity-portfolio-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedPolycubeDeepScreen = JSON.parse(await readFile(
  new URL("../data/polycube-volume9-deep-screen-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedPolycubeContinuationNogoods = JSON.parse(await readFile(
  new URL("../data/polycube-volume9-continuation-nogoods-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedPolycubePeriodicThrough13 = JSON.parse(await readFile(
  new URL("../data/polycube-volume9-periodic-through13-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedPolycubeCopy14Multisolver = JSON.parse(await readFile(
  new URL("../data/polycube-volume9-copy14-multisolver-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedPolycubeZ3Cegar = JSON.parse(await readFile(
  new URL("../data/polycube-volume9-z3-cegar-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedPolycubeCoronaForcing = JSON.parse(await readFile(
  new URL("../data/polycube-volume9-corona-forcing-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedPolycubeContactDisjunction = JSON.parse(await readFile(
  new URL("../data/polycube-volume9-contact-disjunction-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedPolycubeContactPropagation = JSON.parse(await readFile(
  new URL("../data/polycube-volume9-contact-propagation-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedPolycubeConditionalContactTransitions = JSON.parse(await readFile(
  new URL("../data/polycube-volume9-conditional-contact-transitions-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedPolycubeCoronaBoundaryStates = JSON.parse(await readFile(
  new URL("../data/polycube-volume9-corona-boundary-states-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedVolume10CoronaThrough2 = JSON.parse(await readFile(
  new URL("../data/polycube-volume10-corona-through2-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedVolume10GctsFunnelThrough9 = JSON.parse(await readFile(
  new URL("../data/polycube-volume10-gcts-funnel-through9-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedVolume10PeriodicCopy10 = JSON.parse(await readFile(
  new URL("../data/polycube-volume10-periodic-copy10-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedVolume10PeriodicCopy11 = JSON.parse(await readFile(
  new URL("../data/polycube-volume10-periodic-copy11-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedVolume10PeriodicCopy12 = JSON.parse(await readFile(
  new URL("../data/polycube-volume10-periodic-copy12-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedVolume10PeriodicCopy13 = JSON.parse(await readFile(
  new URL("../data/polycube-volume10-periodic-copy13-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedVolume10Seed7Coronas = JSON.parse(await readFile(
  new URL("../data/polycube-volume10-gcts-seed7-radius4-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedVolume10Radius4Continuations = JSON.parse(await readFile(
  new URL("../data/polycube-volume10-gcts-continuation-radius4-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP10055695Z3Cegar = JSON.parse(await readFile(
  new URL("../data/polycube-p10-055695-z3-cegar-radius4-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP10055695LazyCellCegar = JSON.parse(await readFile(
  new URL("../data/polycube-p10-055695-lazy-cell-cegar-2026-08-22.json", import.meta.url),
  "utf8"
));
const archivedP10054782LazyCellCegar = JSON.parse(await readFile(
  new URL("../data/polycube-p10-054782-lazy-cell-cegar-2026-08-22.json", import.meta.url),
  "utf8"
));
const archivedP10054782PlacementCubeCegar = JSON.parse(await readFile(
  new URL("../data/polycube-p10-054782-placement-cube-cegar-screen-2026-08-23.json", import.meta.url),
  "utf8"
));
const archivedP10054782Propagation = JSON.parse(await readFile(
  new URL("../data/polycube-p10-054782-propagate-values-nested-screen-2026-08-24.json", import.meta.url),
  "utf8"
));
const archivedP10052588Radius3Witness = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-radius3-witness-audit-2026-08-22.json", import.meta.url),
  "utf8"
));
const archivedP10052588Radius3WitnessRaw = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-radius3-witness-cegar-raw-2026-08-22.json", import.meta.url),
  "utf8"
));
const archivedP10052588StagedCellFeedback = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-staged-cell-feedback-2026-08-22.json", import.meta.url),
  "utf8"
));
const archivedP10052588Copy4748Frontier = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-copy47-48-frontier-2026-08-22.json", import.meta.url),
  "utf8"
));
const archivedP10052588Exact47CubeCover = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-exact47-placement-cube-cover-2026-08-22.json", import.meta.url),
  "utf8"
));
const archivedP10052588Exact4849CubeCover = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-exact48-49-placement-cube-cover-2026-08-22.json", import.meta.url),
  "utf8"
));
const archivedP10052588Exact50CubeCover = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-exact50-placement-cube-cover-2026-08-22.json", import.meta.url),
  "utf8"
));
const archivedP10052588Exact51AdaptiveCube = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-exact51-adaptive-placement-cube-2026-08-23.json", import.meta.url),
  "utf8"
));
const archivedP10052588Exact5253AdaptiveCube = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-exact52-53-adaptive-placement-cube-2026-08-23.json", import.meta.url),
  "utf8"
));
const archivedP10052588Exact5455AdaptiveCube = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-exact54-55-adaptive-placement-cube-2026-08-23.json", import.meta.url),
  "utf8"
));
const archivedP10052588Exact5660AdaptiveCube = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-exact56-60-adaptive-placement-cube-2026-08-23.json", import.meta.url),
  "utf8"
));
const archivedP10052588Exact6162PrerefinedCube = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-exact61-62-prerefined-placement-cube-2026-08-23.json", import.meta.url),
  "utf8"
));
const archivedP10052588Exact6367PrerefinedCube = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-exact63-67-prerefined-placement-cube-v2-2026-08-23.json", import.meta.url),
  "utf8"
));
const archivedP10052588AtLeast68Tail = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-at-least68-placement-cube-tail-2026-08-23.json", import.meta.url),
  "utf8"
));
const archivedP10052588CompleteExhaustion = JSON.parse(await readFile(
  new URL("../data/polycube-p10-052588-complete-radius3-exhaustion-2026-08-23.json", import.meta.url),
  "utf8"
));
const archivedPartialNextLayerLookahead = JSON.parse(await readFile(
  new URL("../data/polycube-corona-partial-next-layer-lookahead-ab-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedPlacementOrderDiversity = JSON.parse(await readFile(
  new URL("../data/polycube-corona-placement-order-diversity-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9HighCopyCegar = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-high-copy-cegar-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9StagedCoverability = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-staged-coverability-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9HigherOrderCoverability = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-higher-order-coverability-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9QuadrupleCoverability = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-quadruple-coverability-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9BatchedTripleCoverability = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-batched-triple-coverability-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9LazyHigherCoverability = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-lazy-higher-coverability-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9HybridHigherCoverability = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-hybrid-higher-coverability-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9RankedHybridCoverability = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-ranked-hybrid-coverability-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9FormulaCacheProfile = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-formula-cache-profile-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9CachedRankedExtension = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-cached-ranked-extension-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9BatchedSolverState = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-batched-solver-state-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9InteractiveZ3Cegar = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-interactive-z3-cegar-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9RankedPairWindow = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-ranked-pair-window-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9ReplaceablePairWindow = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-replaceable-pair-window-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9PairRecurrence = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-pair-recurrence-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9HistoricalCover = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-historical-cover-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9HistoricalCore = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-historical-core-2026-08-21.json", import.meta.url),
  "utf8"
));
const archivedP9AdaptivePairWindow = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-adaptive-pair-window-2026-08-22.json", import.meta.url),
  "utf8"
));
const archivedP9SoftPairQuota = JSON.parse(await readFile(
  new URL("../data/polycube-p9-42947-soft-pair-quota-2026-08-22.json", import.meta.url),
  "utf8"
));
const correctedConvexPeriodicRescreen = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-corrected-convex-periodic-rescreen-2026-08-20.json", import.meta.url),
  "utf8"
));
const correctedConvexNonTilers = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-corrected-convex-shell2-nontilers-2026-08-20.json", import.meta.url),
  "utf8"
));
const corrected16113NonTiler = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-10_16113-corrected-shell2-nontiler-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize13FirstStage = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size13-full-isometry-first-stage-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize13Periodic = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size13-full-isometry-easy-lanes-2026-08-20.json", import.meta.url),
  "utf8"
));
const archivedSize13ShellTwo = JSON.parse(await readFile(
  new URL("../data/lattice-polyhedron-size13-full-isometry-shell2-2026-08-20.json", import.meta.url),
  "utf8"
));
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.complete_shell_screen,
  {
    maximum_target_shell: 7,
    seeds: archivedCompleteShell.configuration.seeds,
    time_limit_ms: archivedCompleteShell.configuration.timeMs,
    configured_node_limit: archivedCompleteShell.configuration.nodeLimit,
    cascade: archivedCompleteShell.configuration.cascade,
    shell_definition: archivedCompleteShell.configuration.shellDefinition,
    global_zero_face_pruning: false,
    zero_face_rule: "a fixed exposed face with no legal face-mate is permanently unfillable",
    rejected_candidates: ["10_16113", "10_45026", "9_11683"],
    surviving_candidate: null,
    periodic_candidate: "10_45033",
    robust_completed_shell: 4,
    maximum_completed_shell: 7,
    shell_five_hits: 1,
    shell_five_trials: 3,
    shell_five_witness_tiles: 464,
    shell_six_hits: 2,
    shell_six_trials: 3,
    shell_six_witness_tiles: 764,
    shell_seven_hits: 1,
    shell_seven_trials: 3,
    shell_seven_witness_tiles: 1174,
    report: "data/lattice-polyhedron-extendable-shell-screen-2026-08-19.json",
    continuation_report: "data/lattice-polyhedron-10_45033-shell-continuation-2026-08-19.json",
    periodic_certificate_report: "data/lattice-polyhedron-10_45033-periodic-certificate-2026-08-19.json",
    corrected_convex_shell_report: "data/lattice-polyhedron-10_16113-corrected-shell1-2026-08-20.json",
    corrected_convex_shell_two_report: "data/lattice-polyhedron-10_16113-corrected-shell2-nontiler-2026-08-20.json"
  },
  "catalog complete-shell evidence must match the archived exact screen"
);
assert.deepEqual(
  {
    screen_date: LATTICE_POLYHEDRON_SCREENING.gcts_proof.screen_date,
    lane: LATTICE_POLYHEDRON_SCREENING.gcts_proof.lane,
    target_tiles: LATTICE_POLYHEDRON_SCREENING.gcts_proof.target_tiles,
    configured_node_limit: LATTICE_POLYHEDRON_SCREENING.gcts_proof.configured_node_limit,
    time_limit_ms: LATTICE_POLYHEDRON_SCREENING.gcts_proof.time_limit_seconds * 1000,
    seeds: LATTICE_POLYHEDRON_SCREENING.gcts_proof.seeds,
    seeded_tie_breaks: LATTICE_POLYHEDRON_SCREENING.gcts_proof.seeded_tie_breaks,
    generation_band: LATTICE_POLYHEDRON_SCREENING.gcts_proof.generation_band,
    exact_failure_memo: LATTICE_POLYHEDRON_SCREENING.gcts_proof.exact_failure_memo,
    translation_equivariant_nogoods: LATTICE_POLYHEDRON_SCREENING.gcts_proof.translation_equivariant_nogoods,
    mirrors: LATTICE_POLYHEDRON_SCREENING.gcts_proof.mirrors
  },
  {
    screen_date: archivedDiversifiedScreening.screen_date,
    lane: archivedDiversifiedScreening.baseline_protocol.lane,
    target_tiles: archivedDiversifiedScreening.baseline_protocol.target_tiles,
    configured_node_limit: archivedDiversifiedScreening.baseline_protocol.configured_node_limit,
    time_limit_ms: archivedDiversifiedScreening.baseline_protocol.time_limit_ms,
    seeds: archivedDiversifiedScreening.baseline_protocol.seeds,
    seeded_tie_breaks: archivedDiversifiedScreening.baseline_protocol.seeded_tie_breaks,
    generation_band: archivedDiversifiedScreening.baseline_protocol.generation_band,
    exact_failure_memo: archivedDiversifiedScreening.baseline_protocol.exact_failure_memo,
    translation_equivariant_nogoods: archivedDiversifiedScreening.baseline_protocol.translation_equivariant_nogoods,
    mirrors: archivedDiversifiedScreening.baseline_protocol.mirrors
  },
  "runtime proof-search limits must match the archived executed protocol"
);
assert.deepEqual(
  LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES.map(candidate => ({
    id: candidate.id,
    robust_largest_patch: candidate.gcts_proof_screening.robust_largest_patch,
    median_largest_patch: candidate.gcts_proof_screening.median_largest_patch,
    best_largest_patch: candidate.gcts_proof_screening.best_largest_patch,
    target_hits: candidate.gcts_proof_screening.target_hits,
    trials: candidate.gcts_proof_screening.trials
  })),
  archivedDiversifiedScreening.baseline_candidates
    .filter(candidate => LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES.some(survivor => survivor.id === candidate.id))
    .map(candidate => ({
    id: candidate.id,
    robust_largest_patch: candidate.robust_largest_patch,
    median_largest_patch: candidate.median_largest_patch,
    best_largest_patch: candidate.best_largest_patch,
    target_hits: candidate.trials.filter(trial => trial.termination_reason === "target_reached").length,
    trials: candidate.trials.length
  })),
  "catalog GCTS evidence must match the archived fixed-node runs"
);
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.checkpoint_quotient_check,
  {
    minimum_patch_tiles: archivedProofScreening.protocol.minimum_checkpoint_tiles,
    maximum_patch_tiles: archivedProofScreening.protocol.maximum_checkpoint_tiles,
    candidates_screened: archivedProofScreening.summary.candidates_screened,
    completed_checks: archivedProofScreening.summary.checkpoint_checks_completed,
    certificates_found: archivedProofScreening.summary.exact_periodic_rejections,
    rejected_candidate: archivedProofScreening.exact_periodic_rejection.id,
    certificate_method: archivedProofScreening.protocol.certificate_method,
    report: "data/lattice-polyhedron-gcts-checkpoint-screen-2026-08-18.json"
  },
  "runtime target-patch quotient evidence must match the archived exact checks"
);
assert.deepEqual(archivedProofScreening.summary.rejected_candidates, ["10_26470"]);
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.distinct_patch_checkpoint_screen,
  {
    paths_screened: archivedDistinctScreening.summary.paths_screened,
    sampling_policy: archivedDistinctScreening.protocol.sampling_policy,
    sampling_prefix: archivedDistinctScreening.protocol.sampling_prefix,
    sampling_stride: archivedDistinctScreening.protocol.sampling_stride,
    maximum_checks_per_size_per_path:
      archivedDistinctScreening.protocol.maximum_checks_per_size_per_path,
    eligible_distinct_path_states: archivedDistinctScreening.summary.eligible_distinct_path_states,
    completed_checks: archivedDistinctScreening.summary.checkpoint_checks_completed,
    checks_timed_out: archivedDistinctScreening.summary.checkpoint_checks_timed_out,
    certificates_found: archivedDistinctScreening.summary.exact_periodic_certificates_found,
    sampling_skips: archivedDistinctScreening.summary.sampling_skips,
    duplicate_states_skipped: archivedDistinctScreening.summary.duplicate_states_skipped,
    per_size_cap_skips: archivedDistinctScreening.summary.per_size_cap_skips,
    fingerprint_equivalence: "orientation_preserving_cubic_rigid_motion",
    globally_distinct_candidate_states:
      archivedGlobalOverlap.summary.globally_distinct_candidate_states,
    repeated_state_path_pairs: archivedGlobalOverlap.summary.repeated_state_path_pairs,
    global_uniqueness_rate: archivedGlobalOverlap.summary.global_uniqueness_rate,
    report: "data/lattice-polyhedron-hybrid-checkpoint-screen-2026-08-19.json",
    overlap_report: "data/lattice-polyhedron-rigid-checkpoint-overlap-2026-08-19.json",
    prior_fixed_frame_overlap_report: "data/lattice-polyhedron-global-checkpoint-overlap-2026-08-19.json",
    prior_prefix_report: "data/lattice-polyhedron-distinct-checkpoint-screen-2026-08-18.json"
  },
  "runtime distinct-patch evidence must match the archived executed screen"
);
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.failure_memo_ab,
  {
    paths_screened: archivedFailureMemoAb.summary.paths,
    fixed_and_rigid_outcomes_identical:
      archivedFailureMemoAb.summary.identical_bounded_search_outcomes,
    additional_rigid_memo_hits: archivedFailureMemoAb.summary.additional_rigid_memo_hits,
    observed_fixed_elapsed_ms: archivedFailureMemoAb.summary.fixed_elapsed_ms,
    observed_rigid_elapsed_ms: archivedFailureMemoAb.summary.rigid_elapsed_ms,
    observed_elapsed_ratio: archivedFailureMemoAb.summary.observed_elapsed_ratio,
    production_default: archivedFailureMemoAb.summary.production_default,
    report: "data/lattice-polyhedron-failure-memo-ab-2026-08-19.json"
  },
  "runtime failure-memo policy must match the controlled archived A/B"
);
assert.equal(archivedFailureMemoAb.benchmark_schema_version, 14);
assert.equal(archivedFailureMemoAb.paths.length, 12);
assert.ok(archivedFailureMemoAb.paths.every(path =>
  path.additional_rigid_hits === 0
  && path.fixed_memo_hits === path.rigid_memo_hits
  && path.observed_elapsed_ratio > 1
));
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.complementary_nogood_screen,
  {
    paths_screened: archivedNogoodPortfolio.summary.paths_per_policy,
    improved_paths: archivedNogoodPortfolio.summary.improved_nogood_paths,
    equal_paths: archivedNogoodPortfolio.summary.equal_nogood_paths,
    worsened_paths: archivedNogoodPortfolio.summary.worsened_nogood_paths,
    target_hits: archivedNogoodPortfolio.summary.nogood_target_hits,
    learned_clauses: archivedNogoodPortfolio.summary.total_nogood_clauses,
    exact_prunes: archivedNogoodPortfolio.summary.total_nogood_prunes,
    checkpoint_checks_completed: archivedNogoodPortfolio.summary.nogood_checkpoint_checks_completed,
    checkpoint_checks_timed_out: archivedNogoodPortfolio.summary.nogood_checkpoint_checks_timed_out,
    periodic_certificates_found: archivedNogoodPortfolio.summary.nogood_periodic_certificates_found,
    new_rigid_motion_fingerprints: archivedNogoodPortfolio.summary.new_nogood_fingerprints,
    combined_rigid_motion_fingerprints: archivedNogoodPortfolio.summary.combined_distinct_fingerprints,
    policy_decision: archivedNogoodPortfolio.summary.policy_decision,
    report: "data/lattice-polyhedron-nogood-proof-portfolio-2026-08-19.json"
  },
  "the runtime complementary proof policy must match its archived A/B and exact screen"
);
assert.equal(archivedNogoodPortfolio.benchmark_schema_version, 14);
assert.equal(archivedNogoodPortfolio.proof_paths.length, 12);
assert.equal(archivedNogoodPortfolio.summary.nogood_checkpoint_state_path_checks, 1109);
assert.equal(archivedNogoodPortfolio.summary.nogood_checkpoint_checks_completed, 1109);
assert.equal(archivedNogoodPortfolio.summary.nogood_checkpoint_checks_timed_out, 0);
assert.equal(archivedNogoodPortfolio.summary.nogood_periodic_certificates_found, 0);
assert.equal(archivedNogoodPortfolio.summary.new_nogood_fingerprints, 823);
assert.equal(archivedNogoodPortfolio.summary.combined_distinct_fingerprints, 1874);
assert.equal(archivedNogoodPortfolio.summary.policy_decision, "complementary_proof_lane");
assert.ok(archivedNogoodPortfolio.proof_paths.every(path =>
  path.checks_attempted === path.fingerprints.length
  && path.checks_completed === path.checks_attempted
  && path.checks_timed_out === 0
  && !path.certificate_found
  && new Set(path.fingerprints).size === path.fingerprints.length
  && path.fingerprint_digest_sha256 === fingerprintDigest(path.fingerprints)
));
assert.deepEqual(
  archivedNogoodPortfolio.proof_paths
    .filter(path => path.target_check_completed)
    .map(path => ({ id: path.id, seed: path.seed, largest_patch: path.largest_patch })),
  [{ id: "10_45033", seed: 1, largest_patch: 40 }],
  "the complementary policy must retain its checked 40-tile 10_45033 witness"
);
for (const coverage of archivedNogoodPortfolio.candidate_coverage) {
  const priorCandidate = archivedGlobalOverlap.candidates.find(candidate => candidate.id === coverage.id);
  const prior = new Set(priorCandidate.paths.flatMap(path => path.fingerprints));
  const currentPaths = archivedNogoodPortfolio.proof_paths.filter(path => path.id === coverage.id);
  const current = new Set(currentPaths.flatMap(path => path.fingerprints));
  const combined = new Set([...prior, ...current]);
  assert.equal(coverage.prior_distinct_fingerprints, prior.size);
  assert.equal(coverage.nogood_distinct_fingerprints, current.size);
  assert.equal(coverage.shared_fingerprints, [...current].filter(value => prior.has(value)).length);
  assert.equal(coverage.new_fingerprints, [...current].filter(value => !prior.has(value)).length);
  assert.equal(coverage.combined_distinct_fingerprints, combined.size);
  assert.equal(coverage.combined_digest_sha256, fingerprintDigest([...combined]));
}
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.delayed_nogood_screen,
  {
    paths_screened: archivedDelayedNogood.summary.paths_per_policy,
    activation_failure_states: 25,
    improved_over_immediate_paths: archivedDelayedNogood.summary.delayed_25_better_than_immediate,
    equal_to_immediate_paths: archivedDelayedNogood.summary.delayed_25_equal_to_immediate,
    worsened_from_immediate_paths: archivedDelayedNogood.summary.delayed_25_worse_than_immediate,
    target_hits: archivedDelayedNogood.summary.delayed_25_target_hits,
    learned_clauses: archivedDelayedNogood.summary.delayed_25_nogood_clauses,
    exact_prunes: archivedDelayedNogood.summary.delayed_25_nogood_prunes,
    checkpoint_checks_completed: archivedDelayedNogood.summary.delayed_checkpoint_checks_completed,
    checkpoint_checks_timed_out: archivedDelayedNogood.summary.delayed_checkpoint_checks_timed_out,
    periodic_certificates_found: archivedDelayedNogood.summary.delayed_periodic_certificates_found,
    new_rigid_motion_fingerprints: archivedDelayedNogood.summary.new_delayed_fingerprints,
    combined_rigid_motion_fingerprints: archivedDelayedNogood.summary.three_policy_fingerprints,
    policy_decision: archivedDelayedNogood.summary.policy_decision,
    report: "data/lattice-polyhedron-delayed-nogood-screen-2026-08-19.json"
  },
  "the runtime delayed proof policy must match its archived activation sweep and exact screen"
);
assert.equal(archivedDelayedNogood.benchmark_schema_version, 15);
assert.equal(archivedDelayedNogood.proof_paths.length, 12);
assert.deepEqual(
  archivedDelayedNogood.threshold_summary.find(summary => summary.activation_failure_states === 25),
  {
    activation_failure_states: 25,
    better_than_immediate: 2,
    equal_to_immediate: 10,
    worse_than_immediate: 0,
    better_than_baseline: 6,
    equal_to_baseline: 1,
    worse_than_baseline: 5,
    target_hits: 2
  }
);
assert.equal(archivedDelayedNogood.summary.delayed_checkpoint_checks_completed, 1116);
assert.equal(archivedDelayedNogood.summary.delayed_checkpoint_checks_timed_out, 0);
assert.equal(archivedDelayedNogood.summary.delayed_periodic_certificates_found, 0);
assert.equal(archivedDelayedNogood.summary.new_delayed_fingerprints, 199);
assert.equal(archivedDelayedNogood.summary.three_policy_fingerprints, 2073);
assert.equal(archivedDelayedNogood.summary.policy_decision, "replace_immediate_nogood_lane_with_delayed_25");
assert.ok(archivedDelayedNogood.proof_paths.every(path =>
  path.checks_attempted === path.fingerprints.length
  && path.checks_completed === path.checks_attempted
  && path.checks_timed_out === 0
  && !path.certificate_found
  && new Set(path.fingerprints).size === path.fingerprints.length
  && path.fingerprint_digest_sha256 === fingerprintDigest(path.fingerprints)
));
assert.deepEqual(
  archivedDelayedNogood.proof_paths
    .filter(path => path.target_check_completed)
    .map(path => ({ id: path.id, seed: path.seed, largest_patch: path.largest_patch })),
  [
    { id: "10_45033", seed: 1, largest_patch: 40 },
    { id: "10_45033", seed: 2, largest_patch: 40 }
  ],
  "the delayed policy must retain both checked 40-tile 10_45033 witnesses"
);
for (const coverage of archivedDelayedNogood.candidate_coverage) {
  const baselineCandidate = archivedGlobalOverlap.candidates.find(candidate => candidate.id === coverage.id);
  const baselineSet = new Set(baselineCandidate.paths.flatMap(path => path.fingerprints));
  const immediateSet = new Set(
    archivedNogoodPortfolio.proof_paths
      .filter(path => path.id === coverage.id)
      .flatMap(path => path.fingerprints)
  );
  const delayedSet = new Set(
    archivedDelayedNogood.proof_paths
      .filter(path => path.id === coverage.id)
      .flatMap(path => path.fingerprints)
  );
  const priorTwoPolicy = new Set([...baselineSet, ...immediateSet]);
  const threePolicy = new Set([...priorTwoPolicy, ...delayedSet]);
  assert.equal(coverage.baseline_distinct_fingerprints, baselineSet.size);
  assert.equal(coverage.immediate_distinct_fingerprints, immediateSet.size);
  assert.equal(coverage.delayed_distinct_fingerprints, delayedSet.size);
  assert.equal(coverage.prior_two_policy_fingerprints, priorTwoPolicy.size);
  assert.equal(coverage.new_delayed_fingerprints, [...delayedSet].filter(value => !priorTwoPolicy.has(value)).length);
  assert.equal(coverage.three_policy_fingerprints, threePolicy.size);
  assert.equal(coverage.three_policy_digest_sha256, fingerprintDigest([...threePolicy]));
}
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.holdout_screen,
  {
    seeds: archivedHoldout.summary.holdout_seeds,
    paths_per_policy: archivedHoldout.summary.paths_per_policy,
    total_policy_paths: archivedHoldout.summary.total_policy_paths,
    delayed_better_than_immediate:
      archivedHoldout.generalization.holdout_seeds_4_through_8.delayed_better_than_immediate,
    delayed_equal_to_immediate:
      archivedHoldout.generalization.holdout_seeds_4_through_8.delayed_equal_to_immediate,
    delayed_worse_than_immediate:
      archivedHoldout.generalization.holdout_seeds_4_through_8.delayed_worse_than_immediate,
    baseline_target_hits: archivedHoldout.generalization.holdout_seeds_4_through_8.baseline_target_hits,
    immediate_target_hits: archivedHoldout.generalization.holdout_seeds_4_through_8.immediate_target_hits,
    delayed_target_hits: archivedHoldout.generalization.holdout_seeds_4_through_8.delayed_target_hits,
    checkpoint_checks_completed: archivedHoldout.summary.exact_checks_completed,
    checkpoint_checks_timed_out: archivedHoldout.summary.exact_checks_timed_out,
    periodic_certificates_found: archivedHoldout.summary.periodic_certificates_found,
    new_rigid_motion_fingerprints: archivedHoldout.summary.new_holdout_fingerprints,
    expanded_rigid_motion_fingerprints: archivedHoldout.summary.expanded_eight_seed_fingerprints,
    policy_decision: archivedHoldout.summary.policy_decision,
    report: "data/lattice-polyhedron-holdout-screen-2026-08-19.json"
  },
  "the runtime holdout evidence must match the archived five-seed exact screen"
);
assert.equal(archivedHoldout.benchmark_schema_version, 15);
assert.equal(archivedHoldout.search_paths.length, 20);
assert.equal(archivedHoldout.proof_paths.length, 60);
assert.equal(archivedHoldout.summary.exact_checks_completed, 5540);
assert.equal(archivedHoldout.summary.exact_checks_timed_out, 0);
assert.equal(archivedHoldout.summary.periodic_certificates_found, 0);
assert.equal(archivedHoldout.summary.completed_target_patch_checks, 4);
assert.equal(archivedHoldout.summary.distinct_target_witnesses, 2);
assert.equal(archivedHoldout.summary.new_holdout_fingerprints, 2758);
assert.equal(archivedHoldout.summary.expanded_eight_seed_fingerprints, 4831);
assert.equal(
  archivedHoldout.summary.policy_decision,
  "retain_delayed_25_as_complementary_holdout_supported_lane"
);
assert.deepEqual(
  archivedHoldout.generalization.holdout_seeds_4_through_8,
  {
    delayed_better_than_immediate: 5,
    delayed_equal_to_immediate: 14,
    delayed_worse_than_immediate: 1,
    delayed_better_than_baseline: 6,
    delayed_equal_to_baseline: 3,
    delayed_worse_than_baseline: 11,
    baseline_target_hits: 1,
    immediate_target_hits: 1,
    delayed_target_hits: 2
  }
);
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.stagnation_nogood_ab,
  {
    training_thresholds: archivedStagnationNogoodAb.protocol.training_stagnation_failure_thresholds,
    selected_holdout_threshold: archivedStagnationNogoodAb.protocol.selected_holdout_threshold,
    training_paths_per_policy: archivedStagnationNogoodAb.summary.training_paths_per_policy,
    holdout_paths: archivedStagnationNogoodAb.summary.holdout_paths,
    training_10_better_than_fixed_delayed_25:
      archivedStagnationNogoodAb.training_summary[0].better_than_fixed_delayed_25,
    training_10_equal_to_fixed_delayed_25:
      archivedStagnationNogoodAb.training_summary[0].equal_to_fixed_delayed_25,
    training_10_worse_than_fixed_delayed_25:
      archivedStagnationNogoodAb.training_summary[0].worse_than_fixed_delayed_25,
    training_10_target_hits: archivedStagnationNogoodAb.training_summary[0].target_hits,
    holdout_10_better_than_fixed_delayed_25:
      archivedStagnationNogoodAb.holdout_summary.better_than_fixed_delayed_25,
    holdout_10_equal_to_fixed_delayed_25:
      archivedStagnationNogoodAb.holdout_summary.equal_to_fixed_delayed_25,
    holdout_10_worse_than_fixed_delayed_25:
      archivedStagnationNogoodAb.holdout_summary.worse_than_fixed_delayed_25,
    holdout_10_target_hits: archivedStagnationNogoodAb.holdout_summary.target_hits,
    fixed_delayed_25_holdout_target_hits:
      archivedStagnationNogoodAb.holdout_summary.fixed_delayed_25_target_hits,
    policy_decision: archivedStagnationNogoodAb.summary.policy_decision,
    report: "data/lattice-polyhedron-stagnation-nogood-ab-2026-08-19.json"
  },
  "the runtime policy decision must include the archived stagnation-gate rejection"
);
assert.equal(archivedStagnationNogoodAb.benchmark_schema_version, 16);
assert.equal(archivedStagnationNogoodAb.summary.policy_decision, "reject_stagnation_gate_retain_fixed_delayed_25");
assert.deepEqual(archivedStagnationNogoodAb.summary.combined_stagnation_10, {
  better_than_fixed_delayed_25: 0,
  equal_to_fixed_delayed_25: 27,
  worse_than_fixed_delayed_25: 5,
  target_hits: 3,
  fixed_delayed_25_target_hits: 4
});
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.budget_order_screen,
  {
    target_tiles: archivedBudgetOrder.protocol.target_tiles,
    training_seeds: archivedBudgetOrder.protocol.training_seeds,
    holdout_seeds: archivedBudgetOrder.protocol.holdout_seeds,
    baseline_node_limits: archivedBudgetOrder.protocol.baseline_node_limits,
    balanced_1000_target_hits: archivedBudgetOrder.budget_scaling.summary.balanced_1000.target_hits,
    balanced_2000_target_hits: archivedBudgetOrder.budget_scaling.summary.balanced_2000.target_hits,
    balanced_2000_exact_target_checks: archivedBudgetOrder.budget_scaling.summary.exact_target_checks_completed,
    frontier_order_decision: archivedBudgetOrder.frontier_order_screen.policy_decision,
    crystal_better_than_balanced: archivedBudgetOrder.move_order_screen.combined_comparison.better,
    crystal_equal_to_balanced: archivedBudgetOrder.move_order_screen.combined_comparison.equal,
    crystal_worse_than_balanced: archivedBudgetOrder.move_order_screen.combined_comparison.worse,
    balanced_target_hits: archivedBudgetOrder.move_order_screen.combined_comparison.baseline_target_hits,
    crystal_target_hits: archivedBudgetOrder.move_order_screen.combined_comparison.challenger_target_hits,
    exact_target_checks_completed: archivedBudgetOrder.move_order_screen.exact_target_checks_completed,
    exact_target_checks_timed_out: archivedBudgetOrder.move_order_screen.exact_target_checks_timed_out,
    periodic_certificates_found: archivedBudgetOrder.move_order_screen.periodic_certificates_found,
    distinct_candidate_target_witnesses: archivedBudgetOrder.move_order_screen.distinct_candidate_target_witnesses,
    policy_decision: archivedBudgetOrder.move_order_screen.policy_decision,
    report: "data/lattice-polyhedron-budget-order-screen-2026-08-19.json"
  },
  "the runtime crystal-lane decision must match the archived budget and order screen"
);
assert.deepEqual(archivedBudgetOrder.benchmark_schema_versions, [16, 17]);
assert.deepEqual(archivedBudgetOrder.move_order_screen.training_comparison, {
  better: 8,
  equal: 0,
  worse: 4,
  baseline_target_hits: 1,
  challenger_target_hits: 3
});
assert.deepEqual(archivedBudgetOrder.move_order_screen.holdout_comparison, {
  better: 13,
  equal: 0,
  worse: 7,
  baseline_target_hits: 0,
  challenger_target_hits: 4
});
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.internal_period_screen,
  {
    target_tiles: archivedInternalPeriod.protocol.target_tiles,
    seeds: archivedInternalPeriod.protocol.seeds,
    breadth_time_limit_ms: archivedInternalPeriod.protocol.time_limit_ms,
    configured_node_limit: archivedInternalPeriod.protocol.node_limit,
    internal_period_vector_limit: archivedInternalPeriod.protocol.internal_period_vector_limit,
    breadth_paths: archivedInternalPeriod.repeated_translation_rank_screen.paths,
    geometric_rank_3_paths:
      archivedInternalPeriod.repeated_translation_rank_screen.geometric_rank_3_paths,
    repeated_translation_rank_3_paths:
      archivedInternalPeriod.repeated_translation_rank_screen.repeated_translation_rank_3_paths,
    breadth_target_hits: archivedInternalPeriod.repeated_translation_rank_screen.target_hits,
    focused_candidate: archivedInternalPeriod.focused_target_protocol.id,
    focused_seed: archivedInternalPeriod.focused_target_protocol.seed,
    focused_search_time_limit_ms: archivedInternalPeriod.focused_target_protocol.search_time_limit_ms,
    focused_target_checks_completed: archivedInternalPeriod.exact_target_check.check_completed ? 1 : 0,
    focused_candidate_bases_tested: archivedInternalPeriod.exact_target_check.candidate_bases_tested,
    focused_periodic_certificates_found:
      archivedInternalPeriod.exact_target_check.whole_patch_or_internal_certificate_found ? 1 : 0,
    legacy_target_witnesses_checked:
      archivedInternalPeriod.legacy_crystal_target_checks.checked_witnesses,
    highly_collinear_10_45026_witnesses:
      archivedInternalPeriod.legacy_crystal_target_checks.highly_collinear_10_45026_witnesses,
    positive_control: archivedInternalPeriod.positive_control.id,
    positive_control_motif_tiles: archivedInternalPeriod.positive_control.certificate_patch_size,
    policy_decision: "replace_affine_rank_gate_with_repeated_translation_rank",
    report: "data/lattice-polyhedron-internal-period-screen-2026-08-19.json"
  }
);
assert.equal(archivedInternalPeriod.exact_target_check.candidate_bases_tested, 9139);
assert.equal(archivedInternalPeriod.exact_target_check.maximum_translation_support, 5);
assert.equal(archivedInternalPeriod.exact_target_check.whole_patch_or_internal_certificate_found, false);
assert.equal(archivedInternalPeriod.positive_control.certificate_patch_size, 3);
assert.equal(archivedInternalPeriod.positive_control.whole_patch_or_internal_certificate_found, true);
assert.equal(archivedGlobalExtension.schemaVersion, 19);
assert.equal(archivedGlobalExtension.configuration.connectedPatchEnumeration, true);
assert.equal(archivedGlobalExtension.configuration.unbandedMoveOrder, "global");
assert.equal(archivedGlobalExtension.rows.length, 12);
assert.ok(archivedGlobalExtension.rows.every(row =>
  row.connectedPatchEnumeration
  && row.largestPatch === 60
  && row.visitedNodes === 60
  && row.backtracks === 0
  && row.witnessGrowthAxisRank === 3
  && row.witnessPeriodicTranslationRank === 3
  && row.genericPeriodicCertificateChecksCompleted === 1
  && row.genericPeriodicCertificateChecksTimedOut === 0
  && !row.genericPeriodicCertificateFound
));
assert.deepEqual(
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.global_extension_screen,
  {
    target_tiles: archivedGlobalExtension.configuration.target,
    seeds: archivedGlobalExtension.configuration.seeds,
    configured_node_limit: archivedGlobalExtension.configuration.nodeLimit,
    trials: archivedGlobalExtension.rows.length,
    target_hits: archivedGlobalExtension.rows.filter(row => row.largestPatch === 60).length,
    distinct_witnesses: new Set(archivedGlobalExtension.rows.map(row => row.witnessHash)).size,
    geometric_rank_3_witnesses:
      archivedGlobalExtension.rows.filter(row => row.witnessGrowthAxisRank === 3).length,
    repeated_translation_rank_3_witnesses:
      archivedGlobalExtension.rows.filter(row => row.witnessPeriodicTranslationRank === 3).length,
    exact_target_checks_completed: archivedGlobalExtension.rows.reduce(
      (sum, row) => sum + row.genericPeriodicCertificateChecksCompleted,
      0
    ),
    exact_target_checks_timed_out: archivedGlobalExtension.rows.reduce(
      (sum, row) => sum + row.genericPeriodicCertificateChecksTimedOut,
      0
    ),
    internal_period_bases_tested: archivedGlobalExtension.rows.reduce(
      (sum, row) => sum + row.genericPeriodicInternalMotifBasesTested,
      0
    ),
    periodic_certificates_found:
      archivedGlobalExtension.rows.filter(row => row.genericPeriodicCertificateFound).length,
    search_correction: "global_face_extensions_and_applied_placement_node_accounting",
    supersedes_vertex_mrv_depth_comparisons: true,
    report: "data/lattice-polyhedron-global-extension-screen-2026-08-19.json"
  }
);
assert.ok(archivedBudgetOrder.budget_scaling.summary.all_paths_non_decreasing);
assert.equal(archivedBudgetOrder.frontier_order_screen.policy_decision, "retain_mrv");
assert.equal(archivedBudgetOrder.move_order_screen.exact_target_checks_completed, 8);
assert.equal(archivedBudgetOrder.move_order_screen.exact_target_checks_timed_out, 0);
assert.equal(archivedBudgetOrder.move_order_screen.periodic_certificates_found, 0);
assert.equal(archivedBudgetOrder.move_order_screen.distinct_candidate_target_witnesses, 6);
assert.ok(archivedBudgetOrder.move_order_screen.exact_target_proofs.every(path =>
  path.target_check_completed && !path.target_check_timed_out && !path.target_certificate_found
));
for (const path of archivedDelayedNogood.paths) {
  for (const outcome of [path.baseline, path.immediate, ...Object.values(path.delayed)]) {
    assert.ok(outcome.max_live_tiles >= outcome.largest_patch);
    assert.equal(outcome.uncaptured_max_live_tiles, outcome.max_live_tiles - outcome.largest_patch);
  }
}
for (const path of archivedHoldout.search_paths) {
  for (const outcome of [path.baseline, path.immediate, path.delayed_25]) {
    assert.ok(outcome.max_live_tiles >= outcome.largest_patch);
    assert.equal(outcome.uncaptured_max_live_tiles, outcome.max_live_tiles - outcome.largest_patch);
    assert.equal(outcome.growth_milestones.at(-1).patch_size, outcome.largest_patch);
    assert.equal(outcome.growth_milestones.at(-1).witness_hash, outcome.witness_hash);
  }
}
assert.ok(archivedHoldout.proof_paths.every(path =>
  path.checks_attempted === path.fingerprints.length
  && path.checks_completed === path.checks_attempted
  && path.checks_timed_out === 0
  && !path.certificate_found
  && new Set(path.fingerprints).size === path.fingerprints.length
  && path.fingerprint_digest_sha256 === fingerprintDigest(path.fingerprints)
));
for (const coverage of archivedHoldout.candidate_coverage) {
  const priorBaselineCandidate = archivedGlobalOverlap.candidates.find(candidate => candidate.id === coverage.id);
  const priorSet = new Set([
    ...priorBaselineCandidate.paths.flatMap(path => path.fingerprints),
    ...archivedNogoodPortfolio.proof_paths
      .filter(path => path.id === coverage.id)
      .flatMap(path => path.fingerprints),
    ...archivedDelayedNogood.proof_paths
      .filter(path => path.id === coverage.id)
      .flatMap(path => path.fingerprints)
  ]);
  const holdoutByPolicy = Object.fromEntries(["baseline", "immediate", "delayed"].map(policy => [
    policy,
    new Set(archivedHoldout.proof_paths
      .filter(path => path.id === coverage.id && path.policy === policy)
      .flatMap(path => path.fingerprints))
  ]));
  const holdoutUnion = new Set(Object.values(holdoutByPolicy).flatMap(set => [...set]));
  const expanded = new Set([...priorSet, ...holdoutUnion]);
  assert.equal(coverage.prior_three_policy_fingerprints, priorSet.size);
  assert.equal(coverage.holdout_baseline_fingerprints, holdoutByPolicy.baseline.size);
  assert.equal(coverage.holdout_immediate_fingerprints, holdoutByPolicy.immediate.size);
  assert.equal(coverage.holdout_delayed_fingerprints, holdoutByPolicy.delayed.size);
  assert.equal(coverage.holdout_union_fingerprints, holdoutUnion.size);
  assert.equal(coverage.new_holdout_fingerprints, [...holdoutUnion].filter(value => !priorSet.has(value)).length);
  assert.equal(coverage.expanded_eight_seed_fingerprints, expanded.size);
  assert.equal(coverage.expanded_digest_sha256, fingerprintDigest([...expanded]));
}
assert.equal(archivedDistinctScreening.paths.length, 12);
assert.ok(
  archivedDistinctScreening.paths.every(path =>
    path.checks_attempted === path.checks_completed
    && path.checks_timed_out === 0
    && !path.certificate_found
    && path.eligible_states === path.checks_attempted
      + path.sampling_skips
      + path.per_size_cap_skips
      + path.total_cap_skips
      + path.time_budget_skips
  ),
  "every archived distinct-patch check must be complete and internally accounted"
);
assert.deepEqual(
  archivedDistinctScreening.paths.map(path => ({ id: path.id, seed: path.seed, witness_hash: path.witness_hash })),
  archivedPrefixScreening.paths.map(path => ({ id: path.id, seed: path.seed, witness_hash: path.witness_hash })),
  "the prefix and hybrid policies must replay exactly the same GCTS paths"
);
assert.equal(
  archivedDistinctScreening.policy_comparison.prefix_checks_completed
    + archivedDistinctScreening.policy_comparison.spread_diagnostic_checks_completed
    - archivedDistinctScreening.policy_comparison.shared_first_patch_checks,
  archivedDistinctScreening.summary.checkpoint_checks_completed,
  "the hybrid evidence must be the exact union of prefix and later-branch samples"
);
assert.equal(archivedGlobalOverlap.source_benchmark_schema_version, 13);
assert.equal(archivedGlobalOverlap.prior_outcome_report, LATTICE_POLYHEDRON_SCREENING.gcts_proof.distinct_patch_checkpoint_screen.report);
assert.equal(
  archivedGlobalOverlap.prior_fingerprint_report,
  LATTICE_POLYHEDRON_SCREENING.gcts_proof.distinct_patch_checkpoint_screen.prior_fixed_frame_overlap_report
);
assert.equal(archivedGlobalOverlap.fingerprint.equivalence, "orientation-preserving cubic rigid motion");
assert.equal(archivedGlobalOverlap.summary.paths, archivedDistinctScreening.summary.paths_screened);
assert.equal(archivedGlobalOverlap.summary.state_path_pairs, archivedDistinctScreening.summary.checkpoint_checks_completed);
assert.equal(archivedGlobalOverlap.summary.exact_checks_completed, archivedGlobalOverlap.summary.state_path_pairs);
assert.equal(archivedGlobalOverlap.summary.exact_checks_timed_out, 0);
assert.equal(archivedGlobalOverlap.summary.exact_periodic_certificates_found, 0);
assert.deepEqual(
  archivedGlobalOverlap.candidates.flatMap(candidate => candidate.paths.map(path => ({
    id: candidate.id,
    seed: path.seed,
    witness_hash: path.witness_hash
  }))),
  archivedDistinctScreening.paths.map(path => ({ id: path.id, seed: path.seed, witness_hash: path.witness_hash })),
  "global fingerprint accounting must replay the same archived GCTS paths"
);
const globalCandidateFingerprints = [];
for (const overlapCandidate of archivedGlobalOverlap.candidates) {
  const union = new Set();
  const pathSets = new Map();
  const membership = new Map();
  let statePathPairs = 0;
  for (const path of overlapCandidate.paths) {
    assert.equal(path.fingerprints.length, path.checks_attempted);
    assert.equal(path.checks_completed + path.checks_timed_out, path.checks_attempted);
    assert.ok(path.fingerprints.every(value => /^[0-9a-f]{32}$/.test(value)));
    assert.equal(new Set(path.fingerprints).size, path.fingerprints.length);
    assert.equal(path.fingerprint_digest_sha256, fingerprintDigest(path.fingerprints));
    pathSets.set(path.seed, new Set(path.fingerprints));
    statePathPairs += path.fingerprints.length;
    path.fingerprints.forEach(fingerprint => {
      union.add(fingerprint);
      if (!membership.has(fingerprint)) membership.set(fingerprint, new Set());
      membership.get(fingerprint).add(path.seed);
    });
  }
  assert.equal(overlapCandidate.state_path_pairs, statePathPairs);
  assert.equal(overlapCandidate.globally_distinct_fingerprints, union.size);
  assert.equal(overlapCandidate.repeated_state_path_pairs, statePathPairs - union.size);
  assert.equal(overlapCandidate.union_digest_sha256, fingerprintDigest([...union]));
  const membershipHistogram = {};
  for (const seeds of membership.values()) {
    membershipHistogram[seeds.size] = (membershipHistogram[seeds.size] ?? 0) + 1;
  }
  assert.deepEqual(overlapCandidate.path_membership_histogram, membershipHistogram);
  for (const pair of overlapCandidate.pairwise_intersections) {
    const [leftSeed, rightSeed] = pair.seeds;
    const left = pathSets.get(leftSeed);
    const right = pathSets.get(rightSeed);
    const shared = [...left].filter(fingerprint => right.has(fingerprint)).length;
    const pairUnion = left.size + right.size - shared;
    assert.equal(pair.shared_fingerprints, shared);
    assert.equal(pair.union_fingerprints, pairUnion);
    assert.equal(pair.jaccard, pairUnion ? shared / pairUnion : 0);
  }
  for (const fingerprint of union) globalCandidateFingerprints.push(`${overlapCandidate.id}:${fingerprint}`);
}
assert.equal(
  archivedGlobalOverlap.summary.globally_distinct_candidate_states,
  archivedGlobalOverlap.candidates.reduce((sum, candidate) => sum + candidate.globally_distinct_fingerprints, 0)
);
assert.equal(
  archivedGlobalOverlap.summary.repeated_state_path_pairs,
  archivedGlobalOverlap.summary.state_path_pairs
    - archivedGlobalOverlap.summary.globally_distinct_candidate_states
);
assert.equal(
  archivedGlobalOverlap.summary.globally_distinct_digest_sha256,
  fingerprintDigest(globalCandidateFingerprints)
);
assert.equal(
  archivedFixedFrameOverlap.summary.globally_distinct_candidate_states
    - archivedGlobalOverlap.summary.globally_distinct_candidate_states,
  2,
  "proper rigid-motion canonicalization must identify the two rotated fixed-frame duplicates"
);
assert.ok(
  archivedGlobalOverlap.candidates.every(candidate => {
    const fixedFrame = archivedFixedFrameOverlap.candidates.find(item => item.id === candidate.id);
    return candidate.globally_distinct_fingerprints <= fixedFrame.globally_distinct_fingerprints;
  }),
  "a stronger equivalence relation must never increase a candidate's distinct-state count"
);
assert.ok(
  archivedProofScreening.paths
    .filter(path => path.id !== "10_26470")
    .every(path => path.checks_completed === 39 && !path.certificate_found)
  ,
  "all surviving focused paths must complete every size checkpoint without a certificate"
);
assert.ok(
  archivedProofScreening.paths.every(
    path => path.checks_timed_out === 0
  ),
  "the checkpoint screen must not hide an incomplete certificate check"
);
for (const candidate of LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES) {
  const witness = archivedProofScreening.paths.find(item => item.id === candidate.id);
  assert.ok(witness, `${candidate.id} must retain its focused 40-tile witness`);
  assert.equal(candidate.gcts_proof_screening.focused_witness_hash, witness.witness_hash);
  assert.equal(candidate.gcts_proof_screening.checkpoint_quotient_checks, 39);
  assert.equal(candidate.gcts_proof_screening.checkpoint_quotient_certificates, 0);
  const distinctSummary = archivedDistinctScreening.candidate_summary.find(item => item.id === candidate.id);
  assert.ok(distinctSummary, `${candidate.id} must retain its distinct-branch screen summary`);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_paths, distinctSummary.paths);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_eligible_states, distinctSummary.eligible_states);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_checks, distinctSummary.checks_completed);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_max_size, distinctSummary.maximum_patch);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_certificates, distinctSummary.certificates_found);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_timeouts, distinctSummary.checks_timed_out);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_sampling_skips, distinctSummary.sampling_skips);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_duplicate_skips, distinctSummary.duplicate_states_skipped);
  assert.equal(candidate.gcts_proof_screening.distinct_checkpoint_cap_skips, distinctSummary.per_size_cap_skips);
  const overlapSummary = archivedGlobalOverlap.candidates.find(item => item.id === candidate.id);
  assert.ok(overlapSummary, `${candidate.id} must retain its global checkpoint coverage summary`);
  assert.equal(candidate.gcts_proof_screening.global_checkpoint_states, overlapSummary.globally_distinct_fingerprints);
  assert.equal(candidate.gcts_proof_screening.repeated_checkpoint_path_pairs, overlapSummary.repeated_state_path_pairs);
  const nogoodSummary = archivedDelayedNogood.candidate_summary.find(item => item.id === candidate.id);
  const nogoodCoverage = archivedDelayedNogood.candidate_coverage.find(item => item.id === candidate.id);
  assert.ok(nogoodSummary && nogoodCoverage, `${candidate.id} must retain its delayed nogood evidence`);
  assert.equal(candidate.gcts_proof_screening.nogood_robust_largest_patch, nogoodSummary.delayed_25_robust_largest_patch);
  assert.equal(candidate.gcts_proof_screening.nogood_median_largest_patch, nogoodSummary.delayed_25_median_largest_patch);
  assert.equal(candidate.gcts_proof_screening.nogood_best_largest_patch, nogoodSummary.delayed_25_best_largest_patch);
  assert.equal(candidate.gcts_proof_screening.nogood_target_hits, nogoodSummary.delayed_25_target_hits);
  assert.equal(candidate.gcts_proof_screening.portfolio_robust_largest_patch, nogoodSummary.baseline_delayed_portfolio_robust_largest_patch);
  assert.equal(candidate.gcts_proof_screening.portfolio_median_largest_patch, nogoodSummary.baseline_delayed_portfolio_median_largest_patch);
  assert.equal(candidate.gcts_proof_screening.portfolio_best_largest_patch, nogoodSummary.baseline_delayed_portfolio_best_largest_patch);
  assert.equal(candidate.gcts_proof_screening.portfolio_target_hits, nogoodSummary.baseline_delayed_portfolio_target_hits);
  assert.equal(candidate.gcts_proof_screening.nogood_checkpoint_checks, nogoodCoverage.delayed_state_path_checks);
  assert.equal(candidate.gcts_proof_screening.nogood_checkpoint_distinct, nogoodCoverage.delayed_distinct_fingerprints);
  assert.equal(candidate.gcts_proof_screening.nogood_new_checkpoint_states, nogoodCoverage.new_delayed_fingerprints);
  assert.equal(candidate.gcts_proof_screening.combined_checkpoint_states, nogoodCoverage.three_policy_fingerprints);
  const holdoutSummary = archivedHoldout.candidate_summary.find(item => item.id === candidate.id);
  const holdoutCoverage = archivedHoldout.candidate_coverage.find(item => item.id === candidate.id);
  assert.ok(holdoutSummary && holdoutCoverage, `${candidate.id} must retain its holdout evidence`);
  assert.equal(candidate.gcts_proof_screening.holdout_trials, archivedHoldout.summary.holdout_seeds.length);
  assert.equal(
    candidate.gcts_proof_screening.holdout_nogood_robust_largest_patch,
    holdoutSummary.holdout_delayed_robust_largest_patch
  );
  assert.equal(
    candidate.gcts_proof_screening.holdout_nogood_median_largest_patch,
    holdoutSummary.holdout_delayed_median_largest_patch
  );
  assert.equal(
    candidate.gcts_proof_screening.holdout_nogood_best_largest_patch,
    holdoutSummary.holdout_delayed_best_largest_patch
  );
  assert.equal(
    candidate.gcts_proof_screening.holdout_nogood_target_hits,
    holdoutSummary.holdout_delayed_target_hits
  );
  assert.equal(candidate.gcts_proof_screening.holdout_checkpoint_checks, holdoutCoverage.holdout_checks_completed);
  assert.equal(candidate.gcts_proof_screening.holdout_new_checkpoint_states, holdoutCoverage.new_holdout_fingerprints);
  assert.equal(candidate.gcts_proof_screening.expanded_checkpoint_states, holdoutCoverage.expanded_eight_seed_fingerprints);
  const crystalSummary = archivedBudgetOrder.move_order_screen.candidate_summary.find(item => item.id === candidate.id);
  assert.ok(crystalSummary, `${candidate.id} must retain its balanced-versus-crystal evidence`);
  assert.equal(candidate.gcts_proof_screening.crystal_trials, crystalSummary.paths);
  assert.equal(candidate.gcts_proof_screening.crystal_better_than_balanced, crystalSummary.crystal_better);
  assert.equal(candidate.gcts_proof_screening.crystal_equal_to_balanced, crystalSummary.crystal_equal);
  assert.equal(candidate.gcts_proof_screening.crystal_worse_than_balanced, crystalSummary.crystal_worse);
  assert.equal(candidate.gcts_proof_screening.crystal_robust_largest_patch, crystalSummary.crystal_robust_largest_patch);
  assert.equal(candidate.gcts_proof_screening.crystal_median_largest_patch, crystalSummary.crystal_median_largest_patch);
  assert.equal(candidate.gcts_proof_screening.crystal_best_largest_patch, crystalSummary.crystal_best_largest_patch);
  assert.equal(candidate.gcts_proof_screening.crystal_target_hits, crystalSummary.crystal_target_hits);
  assert.equal(
    candidate.gcts_proof_screening.crystal_distinct_target_witnesses,
    crystalSummary.crystal_distinct_target_witnesses
  );
  const internalSummary = archivedInternalPeriod.repeated_translation_rank_screen.candidate_summary
    .find(item => item.id === candidate.id);
  assert.ok(internalSummary, `${candidate.id} must retain its internal-period evidence`);
  assert.equal(candidate.gcts_proof_screening.internal_period_trials, internalSummary.paths);
  assert.equal(
    candidate.gcts_proof_screening.internal_period_robust_largest_patch,
    internalSummary.robust_largest_patch
  );
  assert.equal(
    candidate.gcts_proof_screening.internal_period_median_largest_patch,
    internalSummary.median_largest_patch
  );
  assert.equal(
    candidate.gcts_proof_screening.internal_period_best_largest_patch,
    internalSummary.best_largest_patch
  );
  assert.equal(
    candidate.gcts_proof_screening.internal_period_geometric_rank_3_paths,
    internalSummary.geometric_rank_3_paths
  );
  assert.equal(
    candidate.gcts_proof_screening.internal_period_repeated_translation_rank_3_paths,
    internalSummary.repeated_translation_rank_3_paths
  );
  assert.equal(candidate.gcts_proof_screening.internal_period_target_hits, internalSummary.target_hits);
  const globalRows = archivedGlobalExtension.rows.filter(row => row.case === candidate.id);
  assert.equal(candidate.gcts_proof_screening.global_extension_trials, globalRows.length);
  assert.equal(
    candidate.gcts_proof_screening.global_extension_target_hits,
    globalRows.filter(row => row.largestPatch === 60).length
  );
  assert.equal(
    candidate.gcts_proof_screening.global_extension_distinct_witnesses,
    new Set(globalRows.map(row => row.witnessHash)).size
  );
  assert.equal(
    candidate.gcts_proof_screening.global_extension_minimum_isotropy,
    Math.min(...globalRows.map(row => row.witnessGrowthIsotropy))
  );
  assert.equal(
    candidate.gcts_proof_screening.global_extension_max_candidates,
    Math.max(...globalRows.map(row => row.connectedPatchMaxCandidates))
  );
  assert.equal(
    candidate.gcts_proof_screening.global_extension_exact_target_checks,
    globalRows.reduce((sum, row) => sum + row.genericPeriodicCertificateChecksCompleted, 0)
  );
  assert.equal(
    candidate.gcts_proof_screening.global_extension_internal_period_bases_tested,
    globalRows.reduce((sum, row) => sum + row.genericPeriodicInternalMotifBasesTested, 0)
  );
  assert.equal(candidate.gcts_proof_screening.global_extension_periodic_certificates, 0);
}
assert.deepEqual(
  LATTICE_POLYHEDRON_CENSUS_POOL
    .filter(candidate => candidate.screening.status === "exact_rejection")
    .filter(candidate => !["finite_extendable_shell_obstruction", "finite_shell_obstruction"].includes(candidate.screening.certificate))
    .filter(candidate => candidate.id !== "10_45033")
    .filter(candidate => candidate.id !== archivedProofScreening.exact_periodic_rejection.id)
    .map(candidate => ({
      id: candidate.id,
      certificate: candidate.screening.certificate,
      motif_tiles: candidate.screening.motif_tiles,
      period_vectors: candidate.screening.period_vectors
    })),
  archivedScreening.exact_rejections,
  "the original runtime rejection certificates must match the archived exact rescreen"
);
const checkpointRejection = LATTICE_POLYHEDRON_CENSUS_POOL.find(
  candidate => candidate.id === archivedProofScreening.exact_periodic_rejection.id
);
assert.deepEqual(
  {
    certificate: checkpointRejection?.screening.certificate,
    motif_tiles: checkpointRejection?.screening.motif_tiles,
    period_vectors: checkpointRejection?.screening.period_vectors
  },
  {
    certificate: "translational",
    motif_tiles: archivedProofScreening.exact_periodic_rejection.patch_tiles,
    period_vectors: archivedProofScreening.exact_periodic_rejection.period_vectors
  },
  "the newly rejected candidate must retain its exact checkpoint certificate"
);
assert.equal(archivedProofScreening.exact_periodic_rejection.motif.length, 8);
assert.equal(archivedProofScreening.exact_periodic_rejection.proof.boundary_face_count, 30);
assert.equal(archivedProofScreening.exact_periodic_rejection.proof.boundary_pairing.length, 15);
assert.equal(archivedProofScreening.exact_periodic_rejection.proof.motif_volume, 16);
assert.equal(archivedProofScreening.exact_periodic_rejection.proof.lattice_determinant, 16);
assert.deepEqual(
  LATTICE_POLYHEDRON_CENSUS_POOL
    .filter(candidate => ["10_16113", "10_45026", "10_45033", "9_11683"].includes(candidate.id))
    .map(candidate => candidate.id),
  archivedProofScreening.summary.inconclusive_survivors,
  "the public survivors must match the checkpoint-screen result"
);
assert.equal(
  classifyLatticeCandidateScreen({ translational: { provenImpossible: true }, isohedral: null }),
  "reject_certified_non_tiler",
  "a local impossibility certificate must never survive periodic screening"
);
assert.equal(
  classifyLatticeCandidateScreen({ translational: null, isohedral: null, shell: { provenImpossible: true } }),
  "reject_certified_non_tiler",
  "an exhaustive complete-shell obstruction must reject a candidate"
);
assert.equal(
  classifyLatticeCandidateScreen({ translational: { certified: false, incomplete: true }, isohedral: null }),
  "inconclusive",
  "a bounded search limit must remain inconclusive"
);

const candidates = tileSpecs.figureCatalog.filter(figure => figure.census_candidate);
assert.equal(candidates.length, 56 + A2_LAYERED_SIZE7_CANDIDATES.length + A2_LAYERED_SIZE8_CANDIDATES.length + A2_LAYERED_SIZE9_CANDIDATES.length + A2_SLICED_SIZE7_CANDIDATES.length + A2_SLICED_SIZE8_CANDIDATES.length + A2_SLICED_SIZE9_CANDIDATES.length,
  "the lattice controls, free-polycube representatives, and focused A2 survivors must remain in the catalog");
assert.ok(!candidates.some(figure => figure.census_candidate.id === "10_26470"));
const survivors = candidates.filter(figure => figure.census_candidate.screening.status === "inconclusive");
const shellControls = candidates.filter(figure =>
  ["finite_extendable_shell_obstruction", "finite_shell_obstruction", "finite_corona_obstruction", "complete_radius3_obstruction"].includes(figure.census_candidate.screening.certificate)
);
const periodicControls = candidates.filter(figure =>
  ["translational", "isohedral_periodic_quotient"].includes(figure.census_candidate.screening.certificate)
);
const unresolvedA2Candidates = [...A2_SLICED_SIZE9_CANDIDATES, ...A2_SLICED_SIZE8_CANDIDATES, ...A2_SLICED_SIZE7_CANDIDATES, ...A2_LAYERED_SIZE9_CANDIDATES, ...A2_LAYERED_SIZE8_CANDIDATES, ...A2_LAYERED_SIZE7_CANDIDATES].filter(
  candidate => candidate.screening.status === "inconclusive"
);
assert.equal(survivors.length, 11 + unresolvedA2Candidates.length);
assert.deepEqual(
  survivors.map(figure => figure.census_candidate.id).sort(),
  [
    "p10-054782", "p10-055695", "p10-290795", "p10-346304",
    "p9-02127", "p9-08203", "p9-08219", "p9-20656",
    "p9-24025", "p9-42947", "p9-48258",
    ...unresolvedA2Candidates.map(candidate => candidate.id)
  ]
    .sort()
);
const a2Periodic = A2_LAYERED_SIZE7_CANDIDATES.find(candidate => candidate.id === "a2lp_7_00694");
assert.equal(a2Periodic?.screening.status, "periodic");
assert.equal(a2Periodic?.screening.certificate, "translational");
assert.equal(a2Periodic?.screening.motif_tiles, 8);
assert.equal(a2Periodic?.screening.periodic_eight_copy_replay_verified, true);
assert.deepEqual(a2Periodic?.screening.periodic_eight_copy_certificate?.period_vectors,
  [[2, 0, 0], [0, 2, 0], [0, 0, 7]]);
const slicedSizeNineLeads = A2_SLICED_SIZE9_CANDIDATES.filter(
  candidate => candidate.screening.status === "inconclusive"
);
assert.deepEqual(slicedSizeNineLeads.map(candidate => candidate.id), [
  "a2sa_9_11364", "a2sa_9_13833", "a2sa_9_15635"
]);
assert.deepEqual(
  slicedSizeNineLeads.map(candidate => [
    candidate.screening.periodic_ten_copy_exact_negative_orbits,
    candidate.screening.periodic_ten_copy_node_capped_orbits,
    candidate.screening.periodic_ten_copy_hnfs_exactly_excluded
  ]),
  [[38, 47, 181], [37, 48, 175], [38, 47, 181]]
);
assert.ok(slicedSizeNineLeads.every(candidate =>
  candidate.screening.periodic_eight_copy_complete
  && candidate.screening.periodic_solver_unknowns === 0
  && candidate.screening.corona_completed_verified
  && candidate.screening.radius_two_outer_exhausted === false
  && candidate.screening.substitution_direct_scalar_integer_scales_excluded_from === 2
  && candidate.screening.substitution_direct_scalar_all_scale_models_exhausted.join(",") === "proper,reflected"
  && candidate.screening.substitution_two_copy_census_candidates_exhausted === 356
  && candidate.screening.substitution_two_copy_metatile_scalar_scales_excluded.join(",") === "2,3"
  && candidate.screening.substitution_three_copy_metatile_scalar_scales_excluded.join(",") === "2,3"
  && candidate.screening.substitution_three_copy_models_exhausted.join(",") === "proper,reflected"
  && candidate.screening.substitution_four_copy_metatile_proper_scalar_scales_excluded.join(",") === "2"
  && candidate.screening.substitution_four_copy_metatile_types_exhausted > 3000
));
assert.equal(
  slicedSizeNineLeads.find(candidate => candidate.id === "a2sa_9_11364")
    ?.screening.substitution_four_copy_reflected_types_exhausted,
  195075
);
assert.equal(
  slicedSizeNineLeads.find(candidate => candidate.id === "a2sa_9_13833")
    ?.screening.substitution_four_copy_reflected_types_exhausted,
  406896
);
assert.equal(
  slicedSizeNineLeads.find(candidate => candidate.id === "a2sa_9_15635")
    ?.screening.substitution_four_copy_reflected_types_exhausted,
  233190
);
assert.equal(
  survivors.filter(figure => figure.census_candidate.screening.census_stage === "volume9_fresh_bounded_2026_08_25").length,
  6,
  "the fresh census must add six new free representatives beside the existing deep p9-42947 control"
);
const volumeNineSurvivor = survivors.find(figure => figure.census_candidate.id === "p9-42947");
assert.ok(volumeNineSurvivor
  && volumeNineSurvivor.census_candidate.kind === "polycube_census"
  && volumeNineSurvivor.census_candidate.volume === 9
  && volumeNineSurvivor.census_candidate.screening.periodic_hnf_max_motif_tiles === 14
  && volumeNineSurvivor.census_candidate.screening.corona_completed_radius === 4
  && volumeNineSurvivor.census_candidate.mirror_equivalent_id === "p9-42969"
);
assert.ok(survivors.filter(figure => figure.census_candidate.volume === 10).every(figure =>
  figure.census_candidate.kind === "polycube_census"
  && figure.census_candidate.screening.periodic_hnf_max_motif_tiles === 13
  && figure.census_candidate.screening.periodic_hnf_candidates_exhausted === 248682
  && figure.census_candidate.screening.periodic_hnf_report
    === "data/polycube-volume10-periodic-copy13-2026-08-21.json"
  && figure.census_candidate.screening.corona_completed_verified === true
  && figure.census_candidate.screening.corona_next_search_exhausted === false
));
assert.ok(survivors.filter(figure => ["p10-054782", "p10-055695"].includes(figure.census_candidate.id))
  .every(figure => figure.census_candidate.screening.corona_report
    === "data/polycube-volume10-gcts-continuation-radius4-2026-08-21.json"));
assert.deepEqual(
  Object.fromEntries(survivors.filter(figure => figure.census_candidate.volume === 10).map(figure => [
    figure.census_candidate.id,
    [
      figure.census_candidate.screening.corona_completed_radius,
      figure.census_candidate.screening.corona_next_radius
    ]
  ])),
  {
    "p10-054782": [3, 4],
    "p10-055695": [3, 4],
    "p10-290795": [2, 3],
    "p10-346304": [2, 3]
  }
);
assert.equal(shellControls.length, 9);
assert.equal(periodicControls.length, 49);
const visiblePeriodicControls = periodicControls.filter(isGctsFigureVisibleInCatalog);
assert.equal(GCTS_CATALOG_MIN_PERIODIC_MOTIF_TILES, 5);
assert.deepEqual(
  visiblePeriodicControls.map(figure => figure.census_candidate.id).sort(),
  ["10_45033", "11_151715", "12_204255", "12_405129", "13_0635270", "a2lp_7_00694", "a2sa_8_00240", "a2sa_8_00888", "a2sa_8_01059", "a2sa_8_02946", "a2sa_8_02965", "a2sa_8_02979", "a2sa_8_03138", "a2sa_9_01109", "a2sa_9_03727", "a2sa_9_14433", "a2sa_9_15089", "a2sa_9_16327", "p9-43172"],
  "the public catalogue should retain only periodic controls with a large certified motif"
);
assert.ok(periodicControls
  .filter(figure => !isGctsFigureVisibleInCatalog(figure))
  .every(figure => figure.census_candidate.screening.motif_tiles < GCTS_CATALOG_MIN_PERIODIC_MOTIF_TILES));
const periodicPolycube = periodicControls.find(figure => figure.census_candidate.id === "p9-43172");
assert.ok(periodicPolycube, "the resolved free-polycube class must remain as a periodic regression control");
assert.equal(periodicPolycube.census_candidate.mirror_equivalent_id, "p9-43188");
assert.equal(periodicPolycube.census_candidate.screening.motif_tiles, 8);
assert.equal(periodicPolycube.census_candidate.screening.quotient_determinant, 72);
assert.equal(archivedPolycubeDeepScreen.updated_census_counts.certified_periodic, 48262);
assert.equal(archivedPolycubeDeepScreen.updated_census_counts.bounded_inconclusive, 49);
assert.deepEqual(archivedPolycubeDeepScreen.mirror_equivalence_classes, [
  ["p9-42947", "p9-42969"],
  ["p9-43172", "p9-43188"]
]);
assert.equal(archivedPolycubeDeepScreen.periodic_control.independent_verification.verified, true);
assert.equal(archivedVolume10CoronaThrough2.final.complete_radius_2_patches, 6038);
assert.equal(archivedVolume10CoronaThrough2.final.certified_non_tilers, 4);
assert.deepEqual(archivedVolume10CoronaThrough2.final.bounded_unresolved_ids, ["p10-075714", "p10-324131"]);
assert.equal(archivedVolume10GctsFunnelThrough9.corrected_radius_2_census.complete_patches, 6040);
assert.equal(archivedVolume10GctsFunnelThrough9.corrected_radius_2_census.timeouts, 0);
assert.ok(archivedVolume10GctsFunnelThrough9.corrected_radius_2_census.formerly_unresolved_replays.every(
  replay => replay.patch_independently_verified
));
assert.equal(
  archivedVolume10GctsFunnelThrough9.exact_periodic_funnel.hnf_bases_per_surviving_class.cumulative_1_through_9,
  89435
);
assert.equal(archivedVolume10GctsFunnelThrough9.exact_periodic_funnel.copy_9_final_pool.timeouts, 0);
assert.equal(archivedVolume10GctsFunnelThrough9.final.free_class_candidates, 5);
assert.equal(archivedVolume10PeriodicCopy10.final.new_periodic_certificates, 0);
assert.equal(archivedVolume10PeriodicCopy10.final.final_timeouts, 0);
assert.equal(archivedVolume10PeriodicCopy10.final.unique_copy_10_hnf_bases_exhausted, 141050);
assert.equal(archivedVolume10PeriodicCopy10.final.hnf_bases_per_surviving_class_through_10, 117645);
assert.equal(archivedVolume10PeriodicCopy11.final.new_periodic_certificates, 0);
assert.equal(archivedVolume10PeriodicCopy11.final.final_timeouts, 0);
assert.equal(archivedVolume10PeriodicCopy11.final.unique_copy_11_hnf_bases_exhausted, 144305);
assert.equal(archivedVolume10PeriodicCopy11.final.hnf_bases_per_surviving_class_through_11, 146506);
assert.equal(archivedVolume10PeriodicCopy12.final.new_periodic_certificates, 0);
assert.equal(archivedVolume10PeriodicCopy12.final.final_timeouts, 0);
assert.equal(archivedVolume10PeriodicCopy12.final.unique_copy_12_hnf_bases_exhausted, 312325);
assert.equal(archivedVolume10PeriodicCopy12.final.hnf_bases_per_surviving_class_through_12, 208971);
assert.equal(archivedVolume10PeriodicCopy12.final.exact_cover_nodes_across_proof_runs, 167543751);
assert.ok(archivedVolume10PeriodicCopy12.candidates.every(candidate =>
  candidate.hnf_bases_exhausted === 62465
  && candidate.periodic_certificate === false
  && candidate.final_stopped_by === null
));
const archivedCopy12ShardedCandidate = archivedVolume10PeriodicCopy12.candidates
  .find(candidate => candidate.id === "p10-290795");
assert.ok(archivedCopy12ShardedCandidate?.shard_audit.coverage_gap_free);
assert.deepEqual(archivedCopy12ShardedCandidate.shard_audit.expected_range, [7452, 62465]);
assert.equal(archivedCopy12ShardedCandidate.shard_audit.hnf_bases_exhausted, 55013);
assert.equal(archivedCopy12ShardedCandidate.shard_audit.shards.length, 16);
assert.equal(
  archivedCopy12ShardedCandidate.shard_audit.shards.reduce((cursor, shard) => {
    assert.equal(shard.hnf_start_index, cursor, "copy-12 HNF shards must be gap- and overlap-free");
    assert.equal(shard.hnf_bases_exhausted, shard.hnf_end_index_exclusive - shard.hnf_start_index);
    return shard.hnf_end_index_exclusive;
  }, 7452),
  62465
);
assert.equal(archivedVolume10PeriodicCopy13.final.new_periodic_certificates, 0);
assert.equal(archivedVolume10PeriodicCopy13.final.final_timeouts, 0);
assert.equal(archivedVolume10PeriodicCopy13.final.unique_copy_13_hnf_bases_exhausted, 198555);
assert.equal(archivedVolume10PeriodicCopy13.final.hnf_bases_per_surviving_class_through_13, 248682);
assert.equal(archivedVolume10PeriodicCopy13.final.exact_cover_nodes_across_proof_runs, 128053880);
assert.equal(archivedVolume10PeriodicCopy13.campaign_audit.shards, 60);
assert.ok(archivedVolume10PeriodicCopy13.campaign_audit.coverage_gap_free);
assert.ok(archivedVolume10PeriodicCopy13.candidates.every(candidate =>
  candidate.hnf_bases_exhausted === 39711
  && candidate.periodic_certificate === false
  && candidate.final_stopped_by === null
));
const archivedCopy13AlgebraicCandidate = archivedVolume10PeriodicCopy13.candidates
  .find(candidate => candidate.id === "p10-290795");
assert.equal(archivedCopy13AlgebraicCandidate.algebraic_suffix.gf2_span_rejections, 15862);
assert.equal(archivedCopy13AlgebraicCandidate.algebraic_suffix.exact_cover_nodes, 0);
assert.equal(archivedVolume10Seed7Coronas.final.new_verified_radius_3_patches, 2);
assert.equal(archivedVolume10Seed7Coronas.final.radius_3_timeouts, 3);
assert.equal(archivedVolume10Seed7Coronas.final.radius_3_certified_non_tilers, 0);
assert.equal(archivedVolume10Seed7Coronas.final.radius_4_timeouts, 2);
assert.deepEqual(
  archivedVolume10Seed7Coronas.candidates
    .filter(candidate => candidate.radius_3.success)
    .map(candidate => [candidate.id, candidate.radius_3.witness_placements]),
  [["p10-054782", 45], ["p10-055695", 47]]
);
assert.ok(archivedVolume10Seed7Coronas.candidates
  .filter(candidate => candidate.radius_3.success)
  .every(candidate => candidate.radius_3.verified));
assert.equal(
  archivedVolume10Radius4Continuations.final.saved_radius_3_witnesses_rejected_by_exact_radius_4_continuation,
  2
);
assert.equal(
  archivedVolume10Radius4Continuations.final.outer_radius_3_states_checked_for_radius_4_continuation,
  25
);
assert.equal(archivedVolume10Radius4Continuations.final.outer_radius_3_states_extended_to_radius_4, 0);
assert.equal(archivedVolume10Radius4Continuations.final.certified_non_tilers, 0);
assert.ok(archivedVolume10Radius4Continuations.candidates.every(candidate =>
  candidate.saved_witness_fixed_continuation.exhausted
  && candidate.saved_witness_fixed_continuation.nodes === 1
  && candidate.combined_radius_4_portfolio.search_exhausted === false
));
assert.equal(archivedP10055695Z3Cegar.lazy_obstruction_cegar.z3_sat_outer_states, 20);
assert.equal(archivedP10055695Z3Cegar.lazy_obstruction_cegar.exact_dead_outer_states, 20);
assert.equal(archivedP10055695Z3Cegar.lazy_obstruction_cegar.minimum_outer_placements_witnessed, 43);
assert.equal(archivedP10055695Z3Cegar.lazy_obstruction_cegar.continuation_nodes, 25);
assert.equal(archivedP10055695Z3Cegar.lazy_obstruction_cegar.learned_symmetry_closed_clauses, 40);
assert.equal(archivedP10055695Z3Cegar.staged_low_copy_cegar.initial_symmetry_closed_clauses, 40);
assert.equal(archivedP10055695Z3Cegar.staged_low_copy_cegar.z3_sat_outer_states, 20);
assert.equal(archivedP10055695Z3Cegar.staged_low_copy_cegar.exact_dead_outer_states, 20);
assert.equal(archivedP10055695Z3Cegar.staged_low_copy_cegar.minimum_outer_placements_witnessed, 41);
assert.equal(archivedP10055695Z3Cegar.staged_max_41_cegar.z3_sat_outer_states, 9);
assert.equal(archivedP10055695Z3Cegar.staged_max_41_cegar.z3_timeout_trials, 1);
assert.equal(archivedP10055695Z3Cegar.staged_max_41_cegar.exact_dead_outer_states, 9);
assert.equal(archivedP10055695Z3Cegar.combined_clause_distinct_outer_states, 49);
assert.equal(archivedP10055695Z3Cegar.combined_exact_dead_outer_states, 49);
assert.equal(archivedP10055695Z3Cegar.combined_continuation_nodes, 62);
assert.equal(archivedP10055695Z3Cegar.final_symmetry_closed_clauses, 98);
assert.equal(archivedP10055695Z3Cegar.eager_one_step_coverability_ablation.max_47.status, "timeout");
assert.equal(archivedP10055695Z3Cegar.eager_one_step_coverability_ablation.max_43_staged.status, "timeout");
assert.equal(archivedP10055695Z3Cegar.radius_3_space_exhausted, false);
assert.equal(archivedP10055695Z3Cegar.certified_non_tiler, false);
assert.equal(archivedP10055695LazyCellCegar.implementation_commit, "dd3839e");
assert.equal(archivedP10055695LazyCellCegar.lazy_cell_portfolio.z3_sat_outer_states, 22);
assert.equal(archivedP10055695LazyCellCegar.lazy_cell_portfolio.z3_timeout_trials, 17);
assert.equal(archivedP10055695LazyCellCegar.lazy_cell_portfolio.final_cell_coverability_constraints, 44);
assert.equal(archivedP10055695LazyCellCegar.incremental_dynamic_cell_ablation.z3_sat_outer_states, 4);
assert.equal(archivedP10055695LazyCellCegar.incremental_dynamic_cell_ablation.subsequent_sat_states_without_reconstruction, 3);
assert.equal(archivedP10055695LazyCellCegar.combined_with_prior_clause_cegar.clause_distinct_outer_states, 71);
assert.equal(archivedP10055695LazyCellCegar.verified_radius_4_witness_found, false);
assert.equal(archivedP10055695LazyCellCegar.certified_non_tiler, false);
assert.equal(archivedP10054782LazyCellCegar.implementation_commit, "dd3839e");
assert.equal(archivedP10054782LazyCellCegar.portfolio.z3_sat_outer_states, 22);
assert.equal(archivedP10054782LazyCellCegar.portfolio.z3_timeout_trials, 11);
assert.equal(archivedP10054782LazyCellCegar.portfolio.final_cell_coverability_constraints, 20);
assert.equal(archivedP10054782LazyCellCegar.portfolio.redundant_batched_sat_states, 2);
assert.equal(archivedP10054782LazyCellCegar.incremental_dynamic_cell_ablation.z3_sat_outer_states, 7);
assert.equal(archivedP10054782LazyCellCegar.incremental_dynamic_cell_ablation.subsequent_sat_states_without_reconstruction, 6);
assert.equal(archivedP10054782LazyCellCegar.incremental_dynamic_cell_ablation.minimum_outer_placements_witnessed, 41);
assert.equal(archivedP10054782LazyCellCegar.radius_3_space_exhausted, false);
assert.equal(archivedP10054782LazyCellCegar.certified_non_tiler, false);
assert.equal(archivedP10052588Radius3Witness.multi_obstruction_and_replay_commit, "c07c455");
assert.equal(archivedP10052588Radius3Witness.radius_2_to_3_cegar.z3_sat_outer_proposals, 120);
assert.equal(archivedP10052588Radius3Witness.radius_2_to_3_cegar.exact_dead_outer_proposals, 119);
assert.equal(archivedP10052588Radius3Witness.radius_2_to_3_cegar.verified_radius_3_witnesses, 1);
assert.equal(archivedP10052588Radius3Witness.independent_clause_replay.verified_clauses, 114);
assert.equal(archivedP10052588Radius3Witness.radius_3_witness.total_surrounding_placements, 39);
assert.equal(archivedP10052588Radius3Witness.fixed_witness_radius_4_continuation.immediate_dead_target_count, 12);
assert.equal(archivedP10052588Radius3Witness.radius_3_space_exhausted, false);
assert.equal(archivedP10052588Radius3Witness.certified_non_tiler, false);
assert.equal(archivedP10052588Radius3Witness.certified_aperiodic, false);
assert.equal(archivedP10052588Exact47CubeCover.classification, "placement_cube_cover_exhausted");
assert.equal(archivedP10052588Exact47CubeCover.anchor_placement_candidates, 58);
assert.equal(archivedP10052588Exact47CubeCover.covered_anchor_placement_candidates, 58);
assert.equal(archivedP10052588Exact47CubeCover.branch_leaves, 11);
assert.equal(archivedP10052588Exact47CubeCover.coverage_verification.leaf_overlaps, 0);
assert.equal(archivedP10052588Exact47CubeCover.coverage_verification.uncovered_anchor_placement_candidates, 0);
assert.equal(archivedP10052588Exact47CubeCover.new_verified_copy_bound, 47);
assert.equal(archivedP10052588Exact47CubeCover.copy_48_exhausted, false);
assert.equal(archivedP10052588Exact47CubeCover.certified_non_tiler, false);
assert.equal(archivedP10052588Exact47CubeCover.certified_aperiodic, false);
assert.equal(archivedP10052588Exact4849CubeCover.classification, "placement_cube_range_exhausted");
assert.deepEqual(archivedP10052588Exact4849CubeCover.placement_counts, [48, 49]);
assert.equal(archivedP10052588Exact4849CubeCover.covers.length, 2);
assert.ok(archivedP10052588Exact4849CubeCover.covers.every(cover =>
  cover.branch_leaves === 17
  && cover.covered_anchor_placement_candidates === 58
  && cover.leaf_overlaps === 0
  && cover.uncovered_anchor_placement_candidates === 0
));
assert.equal(archivedP10052588Exact4849CubeCover.new_verified_copy_bound, 49);
assert.equal(archivedP10052588Exact4849CubeCover.copy_50_exhausted, false);
assert.equal(archivedP10052588Exact4849CubeCover.certified_non_tiler, false);
assert.equal(archivedP10052588Exact4849CubeCover.certified_aperiodic, false);
assert.equal(archivedP10052588Exact50CubeCover.classification, "placement_cube_cover_exhausted");
assert.equal(archivedP10052588Exact50CubeCover.placement_count, 50);
assert.equal(archivedP10052588Exact50CubeCover.branch_leaves, 18);
assert.equal(archivedP10052588Exact50CubeCover.covered_anchor_placement_candidates, 58);
assert.equal(archivedP10052588Exact50CubeCover.coverage_verification.leaf_overlaps, 0);
assert.equal(archivedP10052588Exact50CubeCover.coverage_verification.uncovered_anchor_placement_candidates, 0);
assert.equal(archivedP10052588Exact50CubeCover.new_verified_copy_bound, 50);
assert.equal(archivedP10052588Exact50CubeCover.copy_51_exhausted, false);
assert.equal(archivedP10052588Exact50CubeCover.certified_non_tiler, false);
assert.equal(archivedP10052588Exact50CubeCover.certified_aperiodic, false);
assert.equal(archivedP10052588Exact51AdaptiveCube.classification, "placement_cube_cover_exhausted");
assert.equal(archivedP10052588Exact51AdaptiveCube.placement_count, 51);
assert.equal(archivedP10052588Exact51AdaptiveCube.branch_leaves, 17);
assert.equal(archivedP10052588Exact51AdaptiveCube.covered_anchor_placement_candidates, 58);
assert.equal(archivedP10052588Exact51AdaptiveCube.coverage_verification.leaf_overlaps, 0);
assert.equal(archivedP10052588Exact51AdaptiveCube.coverage_verification.uncovered_anchor_placement_candidates, 0);
assert.equal(archivedP10052588Exact51AdaptiveCube.resumability_verification.replay_solver_launches, 0);
assert.equal(archivedP10052588Exact51AdaptiveCube.resumability_verification.replay_resumed_branches, 18);
assert.equal(archivedP10052588Exact51AdaptiveCube.resumability_verification.changed_configuration_rejected, true);
assert.match(archivedP10052588Exact51AdaptiveCube.run_configuration_sha256, /^[0-9a-f]{64}$/);
assert.equal(archivedP10052588Exact51AdaptiveCube.new_verified_copy_bound, 51);
assert.equal(archivedP10052588Exact51AdaptiveCube.copy_52_exhausted, false);
assert.equal(archivedP10052588Exact51AdaptiveCube.certified_non_tiler, false);
assert.equal(archivedP10052588Exact51AdaptiveCube.certified_aperiodic, false);
assert.equal(archivedP10052588Exact5253AdaptiveCube.classification, "placement_cube_range_exhausted");
assert.deepEqual(archivedP10052588Exact5253AdaptiveCube.placement_counts, [52, 53]);
assert.equal(archivedP10052588Exact5253AdaptiveCube.covers.length, 2);
assert.equal(archivedP10052588Exact5253AdaptiveCube.covers.reduce((sum, cover) => sum + cover.branch_leaves, 0), 35);
assert.ok(archivedP10052588Exact5253AdaptiveCube.covers.every(cover =>
  cover.covered_anchor_placement_candidates === 58
  && cover.leaf_overlaps === 0
  && cover.uncovered_anchor_placement_candidates === 0
  && cover.replay_solver_launches === 0
));
assert.equal(archivedP10052588Exact5253AdaptiveCube.new_verified_copy_bound, 53);
assert.equal(archivedP10052588Exact5253AdaptiveCube.copy_54_exhausted, false);
assert.equal(archivedP10052588Exact5253AdaptiveCube.certified_non_tiler, false);
assert.equal(archivedP10052588Exact5253AdaptiveCube.certified_aperiodic, false);
assert.equal(archivedP10052588Exact5455AdaptiveCube.classification, "placement_cube_range_exhausted");
assert.deepEqual(archivedP10052588Exact5455AdaptiveCube.placement_counts, [54, 55]);
assert.equal(archivedP10052588Exact5455AdaptiveCube.covers.length, 2);
assert.equal(archivedP10052588Exact5455AdaptiveCube.covers.reduce((sum, cover) => sum + cover.branch_leaves, 0), 35);
assert.ok(archivedP10052588Exact5455AdaptiveCube.covers.every(cover =>
  cover.covered_anchor_placement_candidates === 58
  && cover.leaf_overlaps === 0
  && cover.uncovered_anchor_placement_candidates === 0
));
assert.equal(archivedP10052588Exact5455AdaptiveCube.resumability_verification.replay_solver_launches, 0);
assert.equal(archivedP10052588Exact5455AdaptiveCube.resumability_verification.replay_resumed_branches, 38);
assert.equal(archivedP10052588Exact5455AdaptiveCube.new_verified_copy_bound, 55);
assert.equal(archivedP10052588Exact5455AdaptiveCube.copy_56_exhausted, false);
assert.equal(archivedP10052588Exact5455AdaptiveCube.certified_non_tiler, false);
assert.equal(archivedP10052588Exact5455AdaptiveCube.certified_aperiodic, false);
assert.equal(archivedP10052588Exact5660AdaptiveCube.classification, "placement_cube_ranges_exhausted");
assert.deepEqual(archivedP10052588Exact5660AdaptiveCube.placement_counts, [56, 57, 58, 59, 60]);
assert.equal(archivedP10052588Exact5660AdaptiveCube.covers.length, 5);
assert.equal(archivedP10052588Exact5660AdaptiveCube.covers.reduce((sum, cover) => sum + cover.branch_leaves, 0), 86);
assert.equal(archivedP10052588Exact5660AdaptiveCube.covers.reduce((sum, cover) => sum + cover.initial_solver_launches, 0), 92);
assert.ok(archivedP10052588Exact5660AdaptiveCube.covers.every(cover =>
  cover.covered_anchor_placement_candidates === 58
  && cover.leaf_overlaps === 0
  && cover.uncovered_anchor_placement_candidates === 0
));
assert.equal(archivedP10052588Exact5660AdaptiveCube.coverage_verification.independently_regenerated_certificates_byte_identical, true);
assert.equal(archivedP10052588Exact5660AdaptiveCube.resumability_verification.replay_solver_launches, 0);
assert.equal(archivedP10052588Exact5660AdaptiveCube.resumability_verification.replay_resumed_branches, 92);
assert.equal(archivedP10052588Exact5660AdaptiveCube.new_verified_copy_bound, 60);
assert.equal(archivedP10052588Exact5660AdaptiveCube.copy_61_exhausted, false);
assert.equal(archivedP10052588Exact5660AdaptiveCube.certified_non_tiler, false);
assert.equal(archivedP10052588Exact5660AdaptiveCube.certified_aperiodic, false);
assert.equal(archivedP10052588Exact6162PrerefinedCube.classification, "placement_cube_ranges_exhausted");
assert.deepEqual(archivedP10052588Exact6162PrerefinedCube.placement_counts, [61, 62]);
assert.equal(archivedP10052588Exact6162PrerefinedCube.covers.length, 2);
assert.equal(archivedP10052588Exact6162PrerefinedCube.covers.reduce((sum, cover) => sum + cover.branch_leaves, 0), 40);
assert.equal(archivedP10052588Exact6162PrerefinedCube.covers[0].focused_leaf.result, "unsat");
assert.deepEqual(archivedP10052588Exact6162PrerefinedCube.covers[1].pre_refine_indices, [0, 2, 3]);
assert.ok(archivedP10052588Exact6162PrerefinedCube.covers.every(cover =>
  cover.covered_anchor_placement_candidates === 58
  && cover.leaf_overlaps === 0
  && cover.uncovered_anchor_placement_candidates === 0
));
assert.equal(archivedP10052588Exact6162PrerefinedCube.coverage_verification.independently_regenerated_certificates_byte_identical, true);
assert.equal(archivedP10052588Exact6162PrerefinedCube.resumability_verification.runner_replay_solver_launches, 0);
assert.equal(archivedP10052588Exact6162PrerefinedCube.resumability_verification.runner_replay_resumed_reports, 45);
assert.equal(archivedP10052588Exact6162PrerefinedCube.algorithmic_observation.singleton_geometric_refinement_disallowed, true);
assert.equal(archivedP10052588Exact6162PrerefinedCube.new_verified_copy_bound, 62);
assert.equal(archivedP10052588Exact6162PrerefinedCube.copy_63_exhausted, false);
assert.equal(archivedP10052588Exact6162PrerefinedCube.certified_non_tiler, false);
assert.equal(archivedP10052588Exact6162PrerefinedCube.certified_aperiodic, false);
assert.equal(archivedP10052588Exact6367PrerefinedCube.classification, "placement_cube_ranges_exhausted");
assert.deepEqual(archivedP10052588Exact6367PrerefinedCube.placement_counts, [63, 64, 65, 66, 67]);
assert.deepEqual(archivedP10052588Exact6367PrerefinedCube.pre_refine_indices, [0, 2, 3]);
assert.equal(archivedP10052588Exact6367PrerefinedCube.covers.length, 5);
assert.equal(archivedP10052588Exact6367PrerefinedCube.covers.reduce((sum, cover) => sum + cover.branch_leaves, 0), 96);
assert.equal(archivedP10052588Exact6367PrerefinedCube.covers.reduce((sum, cover) => sum + cover.runner_attempted_reports, 0), 97);
assert.ok(archivedP10052588Exact6367PrerefinedCube.covers.every(cover =>
  cover.covered_anchor_placement_candidates === 58
  && cover.leaf_overlaps === 0
  && cover.uncovered_anchor_placement_candidates === 0
));
assert.equal(archivedP10052588Exact6367PrerefinedCube.covers[3].timed_out_parent.index, 3);
assert.equal(archivedP10052588Exact6367PrerefinedCube.same_leaf_retries_used, 0);
assert.equal(archivedP10052588Exact6367PrerefinedCube.coverage_verification.independently_regenerated_certificates_byte_identical, true);
assert.equal(archivedP10052588Exact6367PrerefinedCube.resumability_verification.replay_solver_launches, 0);
assert.equal(archivedP10052588Exact6367PrerefinedCube.resumability_verification.replay_resumed_reports, 97);
assert.equal(archivedP10052588Exact6367PrerefinedCube.new_verified_copy_bound, 67);
assert.equal(archivedP10052588Exact6367PrerefinedCube.copy_68_exhausted, false);
assert.equal(archivedP10052588Exact6367PrerefinedCube.certified_non_tiler, false);
assert.equal(archivedP10052588Exact6367PrerefinedCube.certified_aperiodic, false);
assert.equal(archivedP10052588AtLeast68Tail.classification, "placement_cube_tail_exhausted");
assert.equal(archivedP10052588AtLeast68Tail.minimum_placement_count, 68);
assert.equal(archivedP10052588AtLeast68Tail.maximum_placement_count, null);
assert.equal(archivedP10052588AtLeast68Tail.branch_leaves, 19);
assert.equal(archivedP10052588AtLeast68Tail.covered_anchor_placement_candidates, 58);
assert.equal(archivedP10052588AtLeast68Tail.uncovered_anchor_placement_candidates, 0);
assert.equal(archivedP10052588AtLeast68Tail.open_ended_tail_exhausted, true);
assert.equal(archivedP10052588CompleteExhaustion.conclusion.unrestricted_radius_3_space_exhausted, true);
assert.equal(archivedP10052588CompleteExhaustion.conclusion.certified_non_tiler, true);
assert.equal(archivedP10052588CompleteExhaustion.conclusion.certified_aperiodic, false);
assert.equal(archivedP10052588CompleteExhaustion.count_cover.exact_components.flatMap(component => component.counts).length, 21);
assert.equal(archivedP10052588StagedCellFeedback.implementation_commit, "7df66cc");
assert.equal(archivedP10052588StagedCellFeedback.matched_seed_175_ablation.all_at_once.sat_radius_3_states, 1);
assert.equal(archivedP10052588StagedCellFeedback.matched_seed_175_ablation.staged_four_at_a_time.sat_radius_3_states, 5);
assert.equal(archivedP10052588StagedCellFeedback.three_seed_staged_portfolio.distinct_radius_3_states, 19);
assert.equal(archivedP10052588StagedCellFeedback.three_seed_staged_portfolio.independently_replayed_clause_instances, 216);
assert.equal(archivedP10052588StagedCellFeedback.three_seed_staged_portfolio.clause_replay_failures, 0);
assert.equal(archivedP10052588StagedCellFeedback.joint_clause_and_cell_feedback_ablation.implementation_commit, "b4bbc33");
assert.equal(archivedP10052588StagedCellFeedback.joint_clause_and_cell_feedback_ablation.sat_radius_3_states, 4);
assert.equal(archivedP10052588StagedCellFeedback.joint_clause_and_cell_feedback_ablation.states_new_beyond_three_seed_cell_only_portfolio, 3);
assert.equal(archivedP10052588StagedCellFeedback.joint_clause_and_cell_feedback_ablation.combined_distinct_radius_3_states, 22);
assert.equal(archivedP10052588StagedCellFeedback.joint_clause_and_cell_feedback_ablation.independently_replayed_clauses, 57);
assert.equal(archivedP10052588StagedCellFeedback.joint_clause_and_cell_feedback_ablation.clause_replay_failures, 0);
assert.equal(archivedP10052588StagedCellFeedback.joint_clause_and_cell_feedback_ablation.production_policy_promoted, false);
assert.equal(archivedP10052588StagedCellFeedback.relaxed_copy_bound_seed_188.maximum_surrounding_placements, 42);
assert.equal(archivedP10052588StagedCellFeedback.relaxed_copy_bound_seed_188.sat_radius_3_states, 4);
assert.equal(archivedP10052588StagedCellFeedback.relaxed_copy_bound_seed_188.surrounding_placement_distribution["40"], 3);
assert.equal(archivedP10052588StagedCellFeedback.relaxed_copy_bound_seed_188.states_new_beyond_prior_twenty_two_state_portfolio, 4);
assert.equal(archivedP10052588StagedCellFeedback.relaxed_copy_bound_seed_188.combined_distinct_radius_3_states, 26);
assert.equal(archivedP10052588StagedCellFeedback.relaxed_copy_bound_seed_188.independently_replayed_clauses, 40);
assert.equal(archivedP10052588StagedCellFeedback.relaxed_copy_bound_seed_188.clause_replay_failures, 0);
assert.equal(archivedP10052588StagedCellFeedback.relaxed_copy_bound_seed_188.copy_bound_exhausted, false);
assert.equal(archivedP10052588StagedCellFeedback.same_process_timeout_escalation_seed_188.implementation_commit, "8301b3d");
assert.equal(archivedP10052588StagedCellFeedback.same_process_timeout_escalation_seed_188.matched_states_without_retry, 4);
assert.equal(archivedP10052588StagedCellFeedback.same_process_timeout_escalation_seed_188.states_with_retry, 6);
assert.equal(archivedP10052588StagedCellFeedback.same_process_timeout_escalation_seed_188.surrounding_placement_distribution["41"], 2);
assert.equal(archivedP10052588StagedCellFeedback.same_process_timeout_escalation_seed_188.combined_distinct_radius_3_states, 28);
assert.equal(archivedP10052588StagedCellFeedback.same_process_timeout_escalation_seed_188.independently_replayed_clauses, 60);
assert.equal(archivedP10052588StagedCellFeedback.same_process_timeout_escalation_seed_188.clause_replay_failures, 0);
assert.equal(archivedP10052588StagedCellFeedback.same_process_timeout_escalation_seed_188.copy_bound_exhausted, false);
assert.equal(archivedP10052588StagedCellFeedback.exact_partition_restart_seed_191.initial_applied_cells, 20);
assert.equal(archivedP10052588StagedCellFeedback.exact_partition_restart_seed_191.final_applied_cells, 32);
assert.equal(archivedP10052588StagedCellFeedback.exact_partition_restart_seed_191.combined_distinct_radius_3_states, 31);
assert.equal(archivedP10052588StagedCellFeedback.exact_partition_restart_seed_191.independently_replayed_clauses, 90);
assert.equal(archivedP10052588StagedCellFeedback.frontier_batch_backoff_seed_197.large_step_control.z3_status, "unknown");
assert.equal(archivedP10052588StagedCellFeedback.frontier_batch_backoff_seed_197.large_step_control.attempted_applied_cells, 36);
assert.equal(archivedP10052588StagedCellFeedback.frontier_batch_backoff_seed_197.small_step_run.final_applied_cells, 34);
assert.equal(archivedP10052588StagedCellFeedback.frontier_batch_backoff_seed_197.small_step_run.combined_distinct_radius_3_states, 33);
assert.equal(archivedP10052588StagedCellFeedback.frontier_batch_backoff_seed_197.small_step_run.independently_replayed_clauses, 97);
assert.equal(archivedP10052588StagedCellFeedback.frontier_batch_backoff_seed_197.adaptive_batching_supported, true);
assert.equal(archivedP10052588StagedCellFeedback.transactional_feedback_backoff.implementation_commit, "0a590e6");
assert.equal(archivedP10052588StagedCellFeedback.transactional_feedback_backoff.regression_control.rollback_exact, true);
assert.equal(archivedP10052588StagedCellFeedback.transactional_feedback_backoff.p10_052588_frontier.direct_large_step_seed_197.final_applied_cells, 36);
assert.equal(archivedP10052588StagedCellFeedback.transactional_feedback_backoff.p10_052588_frontier.automatic_backoff_seed_194.transactions_rolled_back, 2);
assert.deepEqual(
  archivedP10052588StagedCellFeedback.transactional_feedback_backoff.p10_052588_frontier.automatic_backoff_seed_194.attempts.map(attempt => [attempt.clauses, attempt.cells, attempt.status]),
  [[6, 4, "unknown"], [3, 2, "unknown"], [2, 1, "sat"]]
);
assert.equal(archivedP10052588StagedCellFeedback.transactional_feedback_backoff.p10_052588_frontier.combined_distinct_radius_3_states, 35);
assert.equal(archivedP10052588StagedCellFeedback.transactional_feedback_backoff.automatic_backoff_validated, true);
assert.equal(archivedP10052588StagedCellFeedback.retained_feedback_frontier.implementation_commit, "48f0c84");
assert.equal(archivedP10052588StagedCellFeedback.retained_feedback_frontier.seed_200_from_36_cells.final_applied_cells, 40);
assert.equal(archivedP10052588StagedCellFeedback.retained_feedback_frontier.seed_200_from_36_cells.independently_replayed_clauses, 107);
assert.equal(archivedP10052588StagedCellFeedback.retained_feedback_frontier.seed_203_from_40_cells.final_applied_cells, 41);
assert.equal(archivedP10052588StagedCellFeedback.retained_feedback_frontier.seed_203_from_40_cells.independently_replayed_clauses, 114);
assert.equal(archivedP10052588StagedCellFeedback.retained_feedback_frontier.seed_207_from_41_cells.status, "unknown");
assert.equal(archivedP10052588StagedCellFeedback.retained_feedback_frontier.combined_distinct_radius_3_states, 37);
assert.equal(archivedP10052588StagedCellFeedback.retained_feedback_frontier.maximum_verified_applied_cells, 41);
assert.equal(archivedP10052588StagedCellFeedback.retained_feedback_frontier.verified_radius_4_witness_found, false);
assert.equal(archivedP10052588StagedCellFeedback.partial_formula_cache_frontier.implementation_commit, "d8677e4");
assert.equal(archivedP10052588StagedCellFeedback.partial_formula_cache_frontier.matched_prefix_41_probe.applied_reports_byte_identical, true);
assert.equal(archivedP10052588StagedCellFeedback.partial_formula_cache_frontier.matched_prefix_41_probe.cache_miss_construction_milliseconds, 52672);
assert.equal(archivedP10052588StagedCellFeedback.partial_formula_cache_frontier.matched_prefix_41_probe.cache_hit_construction_milliseconds, 2648);
assert.equal(archivedP10052588StagedCellFeedback.partial_formula_cache_frontier.seed_208_from_41_cells.final_applied_cells, 42);
assert.equal(archivedP10052588StagedCellFeedback.partial_formula_cache_frontier.seed_208_from_41_cells.independently_replayed_clauses, 118);
assert.equal(archivedP10052588StagedCellFeedback.partial_formula_cache_frontier.seed_209_from_42_cells.status, "unknown");
assert.equal(archivedP10052588StagedCellFeedback.partial_formula_cache_frontier.seed_210_from_42_cells.final_applied_cells, 43);
assert.equal(archivedP10052588StagedCellFeedback.partial_formula_cache_frontier.seed_210_from_42_cells.independently_replayed_clauses, 127);
assert.equal(archivedP10052588StagedCellFeedback.partial_formula_cache_frontier.combined_distinct_radius_3_states, 39);
assert.equal(archivedP10052588StagedCellFeedback.partial_formula_cache_frontier.maximum_verified_applied_cells, 43);
assert.equal(archivedP10052588StagedCellFeedback.partial_formula_cache_frontier.verified_radius_4_witness_found, false);
assert.equal(archivedP10052588StagedCellFeedback.deep_cached_prefix_frontier.seed_211_from_43_cells.final_applied_cells, 44);
assert.equal(archivedP10052588StagedCellFeedback.deep_cached_prefix_frontier.seed_211_from_43_cells.independently_replayed_clauses, 132);
assert.equal(archivedP10052588StagedCellFeedback.deep_cached_prefix_frontier.seed_211_from_43_cells.novel_against_prior_saved_witnesses, true);
assert.equal(archivedP10052588StagedCellFeedback.deep_cached_prefix_frontier.seed_212_from_44_cells.outer_placements, 41);
assert.equal(archivedP10052588StagedCellFeedback.deep_cached_prefix_frontier.seed_212_from_44_cells.final_applied_cells, 45);
assert.equal(archivedP10052588StagedCellFeedback.deep_cached_prefix_frontier.seed_212_from_44_cells.independently_replayed_clauses, 138);
assert.equal(archivedP10052588StagedCellFeedback.deep_cached_prefix_frontier.seed_212_from_44_cells.novel_against_prior_saved_witnesses, true);
assert.equal(archivedP10052588StagedCellFeedback.deep_cached_prefix_frontier.combined_distinct_radius_3_states, 41);
assert.equal(archivedP10052588StagedCellFeedback.deep_cached_prefix_frontier.maximum_verified_applied_cells, 45);
assert.equal(archivedP10052588StagedCellFeedback.deep_cached_prefix_frontier.verified_radius_4_witness_found, false);
assert.equal(archivedP10052588StagedCellFeedback.prefix_45_seed_diversification.seed_213_cache_miss.final_applied_cells, 46);
assert.equal(archivedP10052588StagedCellFeedback.prefix_45_seed_diversification.seed_213_cache_miss.independently_replayed_clauses, 146);
assert.equal(archivedP10052588StagedCellFeedback.prefix_45_seed_diversification.seed_214_cache_hit.outer_placements, 40);
assert.equal(archivedP10052588StagedCellFeedback.prefix_45_seed_diversification.seed_214_cache_hit.final_applied_cells, 46);
assert.equal(archivedP10052588StagedCellFeedback.prefix_45_seed_diversification.seed_214_cache_hit.independently_replayed_clauses, 148);
assert.equal(archivedP10052588StagedCellFeedback.prefix_45_seed_diversification.applied_clause_reports_byte_identical, true);
assert.equal(archivedP10052588StagedCellFeedback.prefix_45_seed_diversification.applied_cell_reports_byte_identical, true);
assert.equal(archivedP10052588StagedCellFeedback.prefix_45_seed_diversification.combined_distinct_radius_3_states, 43);
assert.equal(archivedP10052588StagedCellFeedback.prefix_45_seed_diversification.maximum_verified_applied_cells, 46);
assert.equal(archivedP10052588StagedCellFeedback.prefix_45_seed_diversification.verified_radius_4_witness_found, false);
assert.equal(archivedP10052588StagedCellFeedback.retained_three_step_chain_from_46_cells.iterations.length, 3);
assert.deepEqual(
  archivedP10052588StagedCellFeedback.retained_three_step_chain_from_46_cells.iterations.map(row => [row.outer_placements, row.final_applied_cells, row.radius_4_continuation_nodes]),
  [[40, 47, 2], [41, 48, 2], [41, 49, 2]]
);
assert.equal(archivedP10052588StagedCellFeedback.retained_three_step_chain_from_46_cells.iterations[1].construction_milliseconds, 0);
assert.equal(archivedP10052588StagedCellFeedback.retained_three_step_chain_from_46_cells.iterations[2].construction_milliseconds, 0);
assert.equal(archivedP10052588StagedCellFeedback.retained_three_step_chain_from_46_cells.all_patches_independently_verified, true);
assert.equal(archivedP10052588StagedCellFeedback.retained_three_step_chain_from_46_cells.all_boundaries_mutually_distinct, true);
assert.equal(archivedP10052588StagedCellFeedback.retained_three_step_chain_from_46_cells.independently_replayed_clauses, 158);
assert.equal(archivedP10052588StagedCellFeedback.retained_three_step_chain_from_46_cells.combined_distinct_radius_3_states, 46);
assert.equal(archivedP10052588StagedCellFeedback.retained_three_step_chain_from_46_cells.final_applied_cells, 49);
assert.equal(archivedP10052588StagedCellFeedback.retained_three_step_chain_from_46_cells.verified_radius_4_witness_found, false);
assert.equal(archivedP10052588StagedCellFeedback.retained_five_step_chain_from_49_cells.iterations.length, 5);
assert.deepEqual(
  archivedP10052588StagedCellFeedback.retained_five_step_chain_from_49_cells.iterations.map(row => [row.outer_placements, row.final_applied_cells, row.radius_4_continuation_nodes]),
  [[42, 50, 2], [42, 51, 2], [41, 52, 2], [40, 53, 2], [42, 54, 2]]
);
assert.equal(archivedP10052588StagedCellFeedback.retained_five_step_chain_from_49_cells.iterations.slice(1).every(row => row.construction_milliseconds === 0), true);
assert.equal(archivedP10052588StagedCellFeedback.retained_five_step_chain_from_49_cells.all_patches_independently_verified, true);
assert.equal(archivedP10052588StagedCellFeedback.retained_five_step_chain_from_49_cells.all_boundaries_mutually_distinct, true);
assert.equal(archivedP10052588StagedCellFeedback.retained_five_step_chain_from_49_cells.independently_replayed_clauses, 171);
assert.equal(archivedP10052588StagedCellFeedback.retained_five_step_chain_from_49_cells.combined_distinct_radius_3_states, 51);
assert.equal(archivedP10052588StagedCellFeedback.retained_five_step_chain_from_49_cells.final_applied_cells, 54);
assert.equal(archivedP10052588StagedCellFeedback.retained_five_step_chain_from_49_cells.verified_radius_4_witness_found, false);
assert.equal(archivedP10052588StagedCellFeedback.bounded_exhaustion_at_57_cells.precertificate_chain_from_54_cells.new_distinct_radius_3_states, 2);
assert.equal(archivedP10052588StagedCellFeedback.bounded_exhaustion_at_57_cells.precertificate_chain_from_54_cells.independently_replayed_clauses, 176);
assert.equal(archivedP10052588StagedCellFeedback.bounded_exhaustion_at_57_cells.seed_226_cache_miss.z3_status, "unsat");
assert.equal(archivedP10052588StagedCellFeedback.bounded_exhaustion_at_57_cells.seed_227_cache_hit.z3_status, "unsat");
assert.equal(archivedP10052588StagedCellFeedback.bounded_exhaustion_at_57_cells.applied_clause_reports_byte_identical, true);
assert.equal(archivedP10052588StagedCellFeedback.bounded_exhaustion_at_57_cells.applied_cell_reports_byte_identical, true);
assert.equal(archivedP10052588StagedCellFeedback.bounded_exhaustion_at_57_cells.maximum_outer_placements, 42);
assert.equal(archivedP10052588StagedCellFeedback.bounded_exhaustion_at_57_cells.applied_clauses, 114);
assert.equal(archivedP10052588StagedCellFeedback.bounded_exhaustion_at_57_cells.applied_cells, 57);
assert.equal(archivedP10052588StagedCellFeedback.bounded_exhaustion_at_57_cells.radius_3_copy_bound_exhausted, true);
assert.equal(archivedP10052588StagedCellFeedback.bounded_exhaustion_at_57_cells.unrestricted_radius_3_space_exhausted, false);
assert.equal(archivedP10052588StagedCellFeedback.bounded_exhaustion_at_57_cells.certified_non_tiler, false);
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_44_copies.maximum_outer_placements, 44);
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_44_copies.seed_228_cache_miss.z3_status, "unknown");
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_44_copies.seed_229_cache_hit.z3_status, "unsat");
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_44_copies.seed_230_cache_hit.z3_status, "unknown");
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_44_copies.radius_3_copy_bound_exhausted, true);
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_44_copies.unrestricted_radius_3_space_exhausted, false);
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_46_copies.maximum_outer_placements, 46);
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_46_copies.seed_231_cache_miss.z3_status, "unsat");
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_46_copies.seed_232_cache_hit.z3_status, "unknown");
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_46_copies.seed_232_cache_hit.transaction_rolled_back, true);
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_46_copies.same_applied_reports_as_44_copy_certificate, true);
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_46_copies.radius_3_copy_bound_exhausted, true);
assert.equal(archivedP10052588StagedCellFeedback.widened_bounded_exhaustion_through_46_copies.unrestricted_radius_3_space_exhausted, false);
assert.equal(archivedP10052588StagedCellFeedback.radius_3_copy_bound_exhausted, true);
assert.equal(archivedP10052588StagedCellFeedback.certified_non_tiler, false);
assert.equal(archivedP10052588StagedCellFeedback.certified_aperiodic, false);
assert.equal(archivedP10052588Copy4748Frontier.timeout_runs, 5);
assert.equal(archivedP10052588Copy4748Frontier.runs.every(run => run.z3_status === "unknown"), true);
assert.equal(archivedP10052588Copy4748Frontier.runs.every(run => run.transaction_rolled_back), true);
assert.equal(archivedP10052588Copy4748Frontier.exact_cardinality_encoding_change.previous_constraints, 2);
assert.equal(archivedP10052588Copy4748Frontier.exact_cardinality_encoding_change.current_constraints, 1);
assert.equal(archivedP10052588Copy4748Frontier.exact_cardinality_encoding_change.matched_wall_clock_improvement_established, false);
assert.equal(archivedP10052588Copy4748Frontier.copy_47_exhausted, false);
assert.equal(archivedP10052588Copy4748Frontier.copy_48_exhausted, false);
assert.equal(archivedP10052588Copy4748Frontier.certified_non_tiler, false);
assert.equal(archivedP10052588Copy4748Frontier.certified_aperiodic, false);
for (const source of archivedP10052588Radius3Witness.raw_reports) {
  const bytes = await readFile(new URL(`../${source.path}`, import.meta.url));
  assert.equal(
    createHash("sha256").update(bytes).digest("hex"),
    source.sha256,
    `${source.path} must match its archived SHA-256`
  );
}
assert.equal(archivedPartialNextLayerLookahead.algorithm.default_enabled, false);
assert.equal(
  archivedPartialNextLayerLookahead["p10-055695_radius3_to_4"].baseline.continuation_checks,
  14
);
assert.equal(
  archivedPartialNextLayerLookahead["p10-055695_radius3_to_4"]
    .lookahead_from_40_placements.continuation_checks,
  0
);
assert.equal(
  archivedPartialNextLayerLookahead["p10-055695_radius3_to_4"]
    .fresh_ordering_validation.aggregate_nodes,
  4985856
);
assert.equal(
  archivedPartialNextLayerLookahead["p10-055695_radius3_to_4"]
    .fresh_ordering_validation.aggregate_next_layer_prunes,
  127
);
assert.equal(
  archivedPartialNextLayerLookahead["p9-42947_radius4_to_5"].baseline.continuation_checks,
  46
);
assert.equal(
  archivedPartialNextLayerLookahead["p9-42947_radius4_to_5"]
    .lookahead_from_60_placements.next_layer_prunes,
  282
);
assert.equal(archivedPartialNextLayerLookahead.result.outer_search_exhausted, false);
assert.equal(archivedPartialNextLayerLookahead.result.certified_non_tiler, false);
assert.equal(archivedPlacementOrderDiversity.algorithm.default_profile, "compact");
assert.equal(archivedPlacementOrderDiversity.p9_seeded_profile.seed_3_sampled_run.complete_proposals, 1);
assert.equal(archivedPlacementOrderDiversity.p9_seeded_profile.seed_11_run.complete_proposals, 0);
assert.equal(archivedPlacementOrderDiversity.p9_seeded_profile.seed_12_run.complete_proposals, 0);
const seededP9Boundary = archivedPlacementOrderDiversity.independently_replayed_p9_boundary_state;
assert.equal(seededP9Boundary.placements, 79);
assert.equal(seededP9Boundary.corona.length, 79);
assert.equal(
  verifyPolycubeCoronaPatch(
    volumeNineSurvivor.census_candidate.voxels,
    seededP9Boundary.corona,
    4
  ).verified,
  true
);
assert.equal(
  createHash("sha256")
    .update(polycubeCoronaBoundaryKey(
      volumeNineSurvivor.census_candidate.voxels,
      seededP9Boundary.corona,
      4
    ))
    .digest("hex"),
  seededP9Boundary.boundary_sha256
);
const seededP9ContinuationReplay = searchPolycubeCorona(
  volumeNineSurvivor.census_candidate.voxels,
  {
    layers: 5,
    fixedPlacements: seededP9Boundary.corona,
    nodeLimit: 100_000,
    timeLimitMs: 1000,
    nogoods: true
  }
);
assert.equal(seededP9ContinuationReplay.exhausted, true);
assert.equal(seededP9ContinuationReplay.nodes, 1);
assert.equal(seededP9ContinuationReplay.fixed_obstruction_nogood.fixed_placement_indices.length, 2);
assert.equal(archivedPlacementOrderDiversity.result.new_verified_radius_5_witness, false);
assert.equal(archivedPlacementOrderDiversity.result.outer_search_exhausted, false);
assert.equal(archivedP9HighCopyCegar.minimum_79_portfolio.z3_sat_outer_states, 10);
assert.equal(archivedP9HighCopyCegar.minimum_80_staged_portfolio.z3_sat_outer_states, 9);
assert.equal(archivedP9HighCopyCegar.minimum_81_staged_portfolio.z3_sat_outer_states, 5);
assert.equal(archivedP9HighCopyCegar.focused_79_to_81_lazy_cegar.z3_sat_outer_states, 12);
assert.equal(archivedP9HighCopyCegar.focused_79_to_81_lazy_cegar.z3_timeout_trials, 3);
assert.equal(archivedP9HighCopyCegar.combined_clause_distinct_outer_states, 36);
assert.equal(archivedP9HighCopyCegar.combined_exact_dead_outer_states, 36);
assert.equal(archivedP9HighCopyCegar.combined_continuation_nodes, 44);
assert.equal(archivedP9HighCopyCegar.final_symmetry_closed_clauses, 108);
assert.equal(archivedP9HighCopyCegar.eager_one_step_coverability_ablation.z3_timeout_trials, 5);
assert.equal(archivedP9HighCopyCegar.high_copy_space_exhausted, false);
assert.equal(archivedP9HighCopyCegar.certified_non_tiler, false);
assert.equal(archivedP9StagedCoverability.matched_15_cell_encoding_ab.edge_cnf.asserted_constraints, 200044);
assert.equal(archivedP9StagedCoverability.matched_15_cell_encoding_ab.grouped_pseudo_boolean.asserted_constraints, 5342);
assert.equal(archivedP9StagedCoverability.full_single_cell_coverability.next_ring_cells_constrained, 180);
assert.equal(archivedP9StagedCoverability.full_coverability_cegar_portfolio.z3_sat_outer_states, 19);
assert.equal(archivedP9StagedCoverability.full_coverability_cegar_portfolio.immediate_dead_target_obstructions, 0);
assert.equal(archivedP9StagedCoverability.full_coverability_cegar_portfolio.resolved_subtree_obstructions, 19);
assert.equal(archivedP9StagedCoverability.full_coverability_cegar_portfolio.continuation_nodes, 74);
assert.equal(archivedP9StagedCoverability.full_coverability_cegar_portfolio.maximum_single_continuation_nodes, 9);
assert.equal(archivedP9StagedCoverability.full_coverability_cegar_portfolio.final_symmetry_expanded_pair_constraints, 42);
assert.equal(archivedP9StagedCoverability.radius_five_witness_found, false);
assert.equal(archivedP9StagedCoverability.outer_search_exhausted, false);
assert.equal(archivedP9HigherOrderCoverability.combined_full_single_coverability_portfolio.z3_sat_outer_states, 41);
assert.equal(archivedP9HigherOrderCoverability.combined_full_single_coverability_portfolio.continuation_nodes, 208);
assert.equal(archivedP9HigherOrderCoverability.combined_full_single_coverability_portfolio.maximum_single_continuation_nodes, 13);
assert.equal(archivedP9HigherOrderCoverability.first_globally_pairwise_and_triplewise_coverable_state.pairwise_coverable, true);
assert.equal(archivedP9HigherOrderCoverability.first_globally_pairwise_and_triplewise_coverable_state.triplewise_coverable, true);
assert.equal(archivedP9HigherOrderCoverability.first_globally_pairwise_and_triplewise_coverable_state.first_incompatible_quadruple.diameter, 6);
assert.equal(archivedP9HigherOrderCoverability.first_globally_pairwise_and_triplewise_coverable_state.first_incompatible_quadruple.candidate_quadruples_blocked, 33);
assert.equal(archivedP9HigherOrderCoverability.radius_five_witness_found, false);
assert.equal(archivedP9HigherOrderCoverability.outer_search_exhausted, false);
assert.equal(archivedP9QuadrupleCoverability.implementation_commit, "240c519");
assert.equal(archivedP9QuadrupleCoverability.encoding.root_symmetry_orbit_constraints, 3);
assert.equal(archivedP9QuadrupleCoverability.cegar_portfolio.z3_sat_outer_states, 13);
assert.equal(archivedP9QuadrupleCoverability.cegar_portfolio.exact_dead_outer_states, 13);
assert.equal(archivedP9QuadrupleCoverability.cegar_portfolio.maximum_single_continuation_nodes, 28);
assert.equal(archivedP9QuadrupleCoverability.cegar_portfolio.final_pair_constraints, 699);
assert.equal(archivedP9QuadrupleCoverability.cegar_portfolio.final_triple_constraints, 18);
assert.equal(archivedP9QuadrupleCoverability.cegar_portfolio.final_quadruple_constraints, 3);
assert.equal(archivedP9QuadrupleCoverability.deepest_new_state.pairwise_coverable, true);
assert.equal(archivedP9QuadrupleCoverability.deepest_new_state.first_incompatible_triple.candidate_triples_blocked, 28);
assert.equal(archivedP9QuadrupleCoverability.outer_search_exhausted, false);
assert.equal(archivedP9BatchedTripleCoverability.implementation_commit, "648c495");
assert.equal(archivedP9BatchedTripleCoverability.portfolio.z3_sat_outer_states, 12);
assert.equal(archivedP9BatchedTripleCoverability.portfolio.z3_timeout_trials, 4);
assert.equal(archivedP9BatchedTripleCoverability.portfolio.triple_orbits_added, 30);
assert.equal(archivedP9BatchedTripleCoverability.portfolio.final_pair_constraints, 720);
assert.equal(archivedP9BatchedTripleCoverability.portfolio.final_triple_constraints, 108);
assert.equal(archivedP9BatchedTripleCoverability.portfolio.final_four_trial_timeouts, 3);
assert.equal(archivedP9BatchedTripleCoverability.outer_search_exhausted, false);
const p10055695Survivor = survivors.find(figure => figure.census_candidate.id === "p10-055695");
const p10054782Survivor = survivors.find(figure => figure.census_candidate.id === "p10-054782");
const p10052588Survivor = candidates.find(figure => figure.census_candidate.id === "p10-052588");
assert.equal(
  p10052588Survivor.census_candidate.screening.corona_report,
  "data/polycube-p10-052588-radius3-witness-audit-2026-08-22.json"
);
assert.equal(p10052588Survivor.census_candidate.screening.corona_completed_radius, 3);
assert.equal(p10052588Survivor.census_candidate.screening.corona_completed_witness_placements, 39);
assert.equal(p10052588Survivor.census_candidate.screening.corona_radius3_cegar_proposals, 120);
assert.equal(p10052588Survivor.census_candidate.screening.corona_radius3_cegar_replayed_clauses, 114);
assert.equal(p10052588Survivor.census_candidate.screening.corona_radius3_witness_radius4_dead_cells, 12);
assert.equal(
  p10052588Survivor.census_candidate.screening.corona_staged_cell_feedback_report,
  "data/polycube-p10-052588-staged-cell-feedback-2026-08-22.json"
);
assert.equal(p10052588Survivor.census_candidate.screening.corona_staged_cell_feedback_distinct_states, 19);
assert.equal(p10052588Survivor.census_candidate.screening.corona_staged_cell_feedback_replayed_clause_instances, 216);
assert.equal(p10052588Survivor.census_candidate.screening.corona_joint_feedback_new_states, 3);
assert.equal(p10052588Survivor.census_candidate.screening.corona_joint_feedback_combined_distinct_states, 22);
assert.equal(p10052588Survivor.census_candidate.screening.corona_joint_feedback_replayed_clauses, 57);
assert.equal(p10052588Survivor.census_candidate.screening.corona_joint_feedback_promoted, false);
assert.equal(p10052588Survivor.census_candidate.screening.corona_relaxed_copy_bound, 42);
assert.equal(p10052588Survivor.census_candidate.screening.corona_relaxed_copy_bound_40_copy_states, 3);
assert.equal(p10052588Survivor.census_candidate.screening.corona_relaxed_copy_bound_combined_distinct_states, 26);
assert.equal(p10052588Survivor.census_candidate.screening.corona_relaxed_copy_bound_replayed_clauses, 40);
assert.equal(p10052588Survivor.census_candidate.screening.corona_relaxed_copy_bound_exhausted, false);
assert.equal(p10052588Survivor.census_candidate.screening.corona_timeout_retry_implementation_commit, "8301b3d");
assert.equal(p10052588Survivor.census_candidate.screening.corona_timeout_retry_states, 6);
assert.equal(p10052588Survivor.census_candidate.screening.corona_timeout_retry_41_copy_states, 2);
assert.equal(p10052588Survivor.census_candidate.screening.corona_timeout_retry_combined_distinct_states, 28);
assert.equal(p10052588Survivor.census_candidate.screening.corona_timeout_retry_replayed_clauses, 60);
assert.equal(p10052588Survivor.census_candidate.screening.corona_timeout_retry_copy_bound_exhausted, false);
assert.equal(p10052588Survivor.census_candidate.screening.corona_partition_restart_applied_cells, 32);
assert.equal(p10052588Survivor.census_candidate.screening.corona_frontier_large_batch_status, "timeout");
assert.equal(p10052588Survivor.census_candidate.screening.corona_frontier_small_batch_cells, 34);
assert.equal(p10052588Survivor.census_candidate.screening.corona_frontier_combined_distinct_states, 33);
assert.equal(p10052588Survivor.census_candidate.screening.corona_frontier_adaptive_batching_supported, true);
assert.equal(p10052588Survivor.census_candidate.screening.corona_transactional_feedback_commit, "0a590e6");
assert.equal(p10052588Survivor.census_candidate.screening.corona_transactional_feedback_backoff_rollbacks, 2);
assert.equal(p10052588Survivor.census_candidate.screening.corona_transactional_feedback_maximum_applied_cells, 36);
assert.equal(p10052588Survivor.census_candidate.screening.corona_transactional_feedback_combined_distinct_states, 35);
assert.equal(p10052588Survivor.census_candidate.screening.corona_transactional_feedback_validated, true);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_feedback_commit, "48f0c84");
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_feedback_maximum_applied_cells, 41);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_feedback_combined_distinct_states, 37);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_feedback_seed200_replayed_clauses, 107);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_feedback_seed203_replayed_clauses, 114);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_feedback_replay_failures, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_feedback_seed207_minimum_batch_status, "unknown");
assert.equal(p10052588Survivor.census_candidate.screening.corona_partial_formula_cache_commit, "d8677e4");
assert.equal(p10052588Survivor.census_candidate.screening.corona_partial_formula_cache_combined_distinct_states, 39);
assert.equal(p10052588Survivor.census_candidate.screening.corona_partial_formula_cache_maximum_applied_cells, 43);
assert.equal(p10052588Survivor.census_candidate.screening.corona_partial_formula_cache_seed208_replayed_clauses, 118);
assert.equal(p10052588Survivor.census_candidate.screening.corona_partial_formula_cache_seed210_replayed_clauses, 127);
assert.equal(p10052588Survivor.census_candidate.screening.corona_partial_formula_cache_replay_failures, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_partial_formula_cache_seed209_status, "unknown");
assert.equal(p10052588Survivor.census_candidate.screening.corona_deep_cached_prefix_combined_distinct_states, 41);
assert.equal(p10052588Survivor.census_candidate.screening.corona_deep_cached_prefix_maximum_applied_cells, 45);
assert.equal(p10052588Survivor.census_candidate.screening.corona_deep_cached_prefix_seed211_placements, 42);
assert.equal(p10052588Survivor.census_candidate.screening.corona_deep_cached_prefix_seed212_placements, 41);
assert.equal(p10052588Survivor.census_candidate.screening.corona_deep_cached_prefix_seed211_replayed_clauses, 132);
assert.equal(p10052588Survivor.census_candidate.screening.corona_deep_cached_prefix_seed212_replayed_clauses, 138);
assert.equal(p10052588Survivor.census_candidate.screening.corona_deep_cached_prefix_replay_failures, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_prefix45_diversification_combined_distinct_states, 43);
assert.equal(p10052588Survivor.census_candidate.screening.corona_prefix45_diversification_minimum_placements, 40);
assert.equal(p10052588Survivor.census_candidate.screening.corona_prefix45_diversification_maximum_applied_cells, 46);
assert.equal(p10052588Survivor.census_candidate.screening.corona_prefix45_diversification_applied_reports_identical, true);
assert.equal(p10052588Survivor.census_candidate.screening.corona_prefix45_diversification_seed213_replayed_clauses, 146);
assert.equal(p10052588Survivor.census_candidate.screening.corona_prefix45_diversification_seed214_replayed_clauses, 148);
assert.equal(p10052588Survivor.census_candidate.screening.corona_prefix45_diversification_replay_failures, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_three_step_new_states, 3);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_three_step_combined_distinct_states, 46);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_three_step_maximum_applied_cells, 49);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_three_step_second_construction_ms, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_three_step_third_construction_ms, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_three_step_replayed_clauses, 158);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_three_step_replay_failures, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_five_step_new_states, 5);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_five_step_combined_distinct_states, 51);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_five_step_maximum_applied_cells, 54);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_five_step_reconstructions_avoided, 4);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_five_step_replayed_clauses, 171);
assert.equal(p10052588Survivor.census_candidate.screening.corona_retained_five_step_replay_failures, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_bounded_exhaustion_new_states, 2);
assert.equal(p10052588Survivor.census_candidate.screening.corona_bounded_exhaustion_combined_distinct_states, 53);
assert.equal(p10052588Survivor.census_candidate.screening.corona_bounded_exhaustion_certificate_cells, 57);
assert.equal(p10052588Survivor.census_candidate.screening.corona_bounded_exhaustion_applied_clauses, 114);
assert.equal(p10052588Survivor.census_candidate.screening.corona_bounded_exhaustion_base_maximum_placements, 42);
assert.equal(p10052588Survivor.census_candidate.screening.corona_bounded_exhaustion_base_independent_unsat_runs, 2);
assert.equal(p10052588Survivor.census_candidate.screening.corona_bounded_exhaustion_maximum_placements, 46);
assert.equal(p10052588Survivor.census_candidate.screening.corona_bounded_exhaustion_independent_unsat_runs, 1);
assert.equal(p10052588Survivor.census_candidate.screening.corona_widened_exhaustion_unsat_seed, 231);
assert.equal(p10052588Survivor.census_candidate.screening.corona_widened_exhaustion_unknown_runs, 1);
assert.equal(p10052588Survivor.census_candidate.screening.corona_bounded_exhaustion_replayed_clauses, 176);
assert.equal(p10052588Survivor.census_candidate.screening.corona_bounded_exhaustion_replay_failures, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_copy47_48_frontier_timeout_runs, 5);
assert.equal(p10052588Survivor.census_candidate.screening.corona_copy47_48_frontier_minimum_open_placements, 47);
assert.equal(p10052588Survivor.census_candidate.screening.corona_copy47_48_frontier_maximum_open_placements, 48);
assert.equal(p10052588Survivor.census_candidate.screening.corona_copy47_48_exact_count_constraints_before, 2);
assert.equal(p10052588Survivor.census_candidate.screening.corona_copy47_48_exact_count_constraints_after, 1);
assert.equal(p10052588Survivor.census_candidate.screening.corona_copy47_48_frontier_open, true);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact47_cube_anchor_candidates, 58);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact47_cube_branch_leaves, 11);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact47_cube_exhausted, true);
assert.deepEqual(p10052588Survivor.census_candidate.screening.corona_exact48_49_cube_counts, [48, 49]);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact48_49_cube_branch_leaves, 34);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact48_49_cube_exhausted, true);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact50_cube_branch_leaves, 18);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact50_cube_exhausted, true);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact51_adaptive_cube_branch_leaves, 17);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact51_adaptive_cube_resume_launches, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact51_adaptive_cube_resumed_branches, 18);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact51_adaptive_cube_exhausted, true);
assert.deepEqual(p10052588Survivor.census_candidate.screening.corona_exact52_53_adaptive_cube_counts, [52, 53]);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact52_53_adaptive_cube_branch_leaves, 35);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact52_53_adaptive_cube_resume_launches, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact52_53_adaptive_cube_resumed_branches, 38);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact52_53_adaptive_cube_exhausted, true);
assert.deepEqual(p10052588Survivor.census_candidate.screening.corona_exact54_55_adaptive_cube_counts, [54, 55]);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact54_55_adaptive_cube_branch_leaves, 35);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact54_55_adaptive_cube_resume_launches, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact54_55_adaptive_cube_resumed_branches, 38);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact54_55_adaptive_cube_exhausted, true);
assert.deepEqual(p10052588Survivor.census_candidate.screening.corona_exact56_60_adaptive_cube_counts, [56, 57, 58, 59, 60]);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact56_60_adaptive_cube_branch_leaves, 86);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact56_60_adaptive_cube_solver_launches, 92);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact56_60_adaptive_cube_resume_launches, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact56_60_adaptive_cube_resumed_branches, 92);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact56_60_adaptive_cube_exhausted, true);
assert.deepEqual(p10052588Survivor.census_candidate.screening.corona_exact61_62_prerefined_cube_counts, [61, 62]);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact61_62_prerefined_cube_branch_leaves, 40);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact61_62_prerefined_cube_runner_launches, 45);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact61_62_prerefined_cube_focused_launches, 1);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact61_62_prerefined_cube_replay_launches, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact61_62_prerefined_cube_resumed_reports, 45);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact61_62_prerefined_cube_exhausted, true);
assert.deepEqual(p10052588Survivor.census_candidate.screening.corona_exact63_67_prerefined_cube_counts, [63, 64, 65, 66, 67]);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact63_67_prerefined_cube_branch_leaves, 96);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact63_67_prerefined_cube_solver_launches, 97);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact63_67_prerefined_cube_replay_launches, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact63_67_prerefined_cube_resumed_reports, 97);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact63_67_prerefined_cube_same_leaf_retries, 0);
assert.equal(p10052588Survivor.census_candidate.screening.corona_exact63_67_prerefined_cube_exhausted, true);
assert.equal(p10052588Survivor.census_candidate.screening.status, "exact_rejection");
assert.equal(p10052588Survivor.census_candidate.screening.certificate, "complete_radius3_obstruction");
assert.equal(p10052588Survivor.census_candidate.screening.corona_at_least68_tail_exhausted, true);
assert.equal(p10052588Survivor.census_candidate.screening.corona_verified_copy_bound, null);
assert.equal(p10052588Survivor.census_candidate.screening.corona_minimum_open_placements, null);
assert.equal(p10052588Survivor.census_candidate.screening.corona_staged_cell_feedback_copy_bound_exhausted, true);
assert.equal(p10052588Survivor.census_candidate.screening.corona_radius3_space_exhausted, true);
assert.equal(p10052588Survivor.census_candidate.screening.corona_cegar_certified_non_tiler, true);
assert.deepEqual(
  verifyPolycubeCoronaPatch(
    p10052588Survivor.census_candidate.voxels,
    archivedP10052588Radius3WitnessRaw.radius_witness.corona,
    3
  ),
  {
    verified: true,
    placements: 39,
    occupied_cells: 400,
    target_cells: 189,
    method: "independent_corona_patch_occupancy"
  }
);
assert.equal(
  p10054782Survivor.census_candidate.screening.corona_cell_cegar_report,
  "data/polycube-p10-054782-lazy-cell-cegar-2026-08-22.json"
);
assert.equal(p10054782Survivor.census_candidate.screening.corona_cell_cegar_states_checked, 22);
assert.equal(p10054782Survivor.census_candidate.screening.corona_cell_cegar_final_constraints, 20);
assert.equal(p10054782Survivor.census_candidate.screening.corona_cell_cegar_minimum_placements, 41);
assert.equal(p10054782Survivor.census_candidate.screening.corona_cell_cegar_radius3_exhausted, false);
assert.equal(
  p10054782Survivor.census_candidate.screening.corona_placement_cube_cegar_report,
  "data/polycube-p10-054782-placement-cube-cegar-screen-2026-08-23.json"
);
assert.equal(p10054782Survivor.census_candidate.screening.corona_placement_cube_cegar_rounds, 2);
assert.equal(p10054782Survivor.census_candidate.screening.corona_placement_cube_cegar_final_clauses, 45);
assert.equal(p10054782Survivor.census_candidate.screening.corona_placement_cube_cegar_final_cells, 47);
assert.equal(p10054782Survivor.census_candidate.screening.corona_placement_cube_cegar_exact41_exhausted, false);
assert.equal(
  p10054782Survivor.census_candidate.screening.corona_propagate_values_nested_report,
  "data/polycube-p10-054782-propagate-values-nested-screen-2026-08-24.json"
);
assert.equal(p10054782Survivor.census_candidate.screening.corona_propagate_values_historical_singletons, 6);
assert.equal(p10054782Survivor.census_candidate.screening.corona_propagate_values_unsat_singletons, 5);
assert.equal(p10054782Survivor.census_candidate.screening.corona_propagate_values_new_proposals, 10);
assert.equal(p10054782Survivor.census_candidate.screening.corona_propagate_values_new_proposals_rejected, 10);
assert.equal(p10054782Survivor.census_candidate.screening.corona_propagate_values_continuation_nodes, 13);
assert.equal(p10054782Survivor.census_candidate.screening.corona_propagate_values_final_clauses, 236);
assert.equal(p10054782Survivor.census_candidate.screening.corona_propagate_values_replayed_clauses, 236);
assert.equal(p10054782Survivor.census_candidate.screening.corona_nested_partition_unsat_leaves, 35);
assert.equal(p10054782Survivor.census_candidate.screening.corona_nested_partition_open_leaves, 0);
assert.equal(p10054782Survivor.census_candidate.screening.corona_nested_partition_required_placements, 7);
assert.equal(p10054782Survivor.census_candidate.screening.corona_nested_partition_exact41_exhausted, true);
assert.equal(p10054782Survivor.census_candidate.screening.corona_exact41_radius4_survivors_exhausted, true);
assert.equal(p10054782Survivor.census_candidate.screening.corona_next_unresolved_minimum_placements, 42);
assert.equal(archivedP10054782Propagation.solver_improvement.historical_unsat_leaves, 5);
assert.equal(archivedP10054782Propagation.solver_improvement.historical_sat_proposals, 1);
assert.equal(archivedP10054782Propagation.exact_radius4_feedback.combined_replay.verified_clauses, 58);
assert.equal(archivedP10054782Propagation.exact_radius4_feedback.combined_replay.failed_clauses, 0);
assert.equal(archivedP10054782Propagation.nested_partition.exact_unsat_partition_leaves, 35);
assert.equal(archivedP10054782Propagation.nested_partition.open_partition_leaves, 0);
assert.equal(archivedP10054782Propagation.nested_partition.exact41_exhausted, true);
assert.equal(archivedP10054782Propagation.exact41_closure.new_radius3_proposals, 9);
assert.equal(archivedP10054782Propagation.exact41_closure.radius4_rejections, 9);
assert.equal(archivedP10054782Propagation.exact41_closure.continuation_nodes, 11);
assert.equal(archivedP10054782Propagation.exact41_closure.additional_exact_unsat_leaves, 17);
assert.equal(archivedP10054782Propagation.exact41_closure.total_exact_unsat_partition_leaves, 35);
assert.equal(archivedP10054782Propagation.exact41_closure.final_feedback_clauses, 236);
assert.equal(archivedP10054782Propagation.exact41_closure.final_replayed_clauses, 236);
assert.equal(archivedP10054782Propagation.exact41_closure.replay_failures, 0);
assert.equal(archivedP10054782Propagation.exact41_closure.final_clause_keys.length, 236);
assert.equal(archivedP10054782Propagation.exact41_closure.open_partition_leaves, 0);
assert.equal(archivedP10054782Propagation.exact41_closure.exact41_radius4_survivors_exhausted, true);
assert.equal(
  verifyPolycubeCoronaPatch(
    p10054782Survivor.census_candidate.voxels,
    archivedP10054782Propagation.new_radius3_proposal.corona,
    3
  ).verified,
  true
);
const archivedP10054782FollowupProposals = [
  ...archivedP10054782Propagation.exact41_closure.first_split.initial_proposals,
  ...archivedP10054782Propagation.exact41_closure.first_split.feedback_154_proposals,
  archivedP10054782Propagation.exact41_closure.second_split.proposal_index_1,
  archivedP10054782Propagation.exact41_closure.third_split.proposal
];
assert.equal(archivedP10054782FollowupProposals.length, 9);
for (const proposal of archivedP10054782FollowupProposals) {
  assert.equal(
    verifyPolycubeCoronaPatch(p10054782Survivor.census_candidate.voxels, proposal.corona, 3).verified,
    true,
    `${proposal.report} must independently verify as a radius-three patch`
  );
}
assert.equal(archivedP10054782PlacementCubeCegar.classification, "cegar_round_limit");
assert.equal(archivedP10054782PlacementCubeCegar.rounds.length, 2);
assert.equal(archivedP10054782PlacementCubeCegar.feedback.plain_clause_replay.verified_clauses, 45);
assert.match(archivedP10054782PlacementCubeCegar.warning, /neither a non-tiling nor an aperiodicity certificate/);
assert.match(
  growthAppSource,
  /Placement-cube CEGAR now continues SAT partition leaves automatically[\s\S]*?41-copy proposals in total[\s\S]*?Exact count 41 is therefore exhausted as a possible radius-four survivor[\s\S]*?the candidate is still inconclusive/,
  "the candidate panel must distinguish exact-41 radius-four exhaustion from a tiling classification"
);
assert.equal(
  p10055695Survivor.census_candidate.screening.corona_cegar_report,
  "data/polycube-p10-055695-z3-cegar-radius4-2026-08-21.json"
);
assert.equal(p10055695Survivor.census_candidate.screening.corona_cegar_radius3_states_checked, 49);
assert.equal(p10055695Survivor.census_candidate.screening.corona_cegar_minimum_radius3_placements, 41);
assert.equal(p10055695Survivor.census_candidate.screening.corona_cegar_continuation_nodes, 62);
assert.equal(p10055695Survivor.census_candidate.screening.corona_cegar_max41_timeout_runs, 1);
assert.equal(p10055695Survivor.census_candidate.screening.corona_cegar_radius3_exhausted, false);
assert.equal(
  p10055695Survivor.census_candidate.screening.corona_cell_cegar_report,
  "data/polycube-p10-055695-lazy-cell-cegar-2026-08-22.json"
);
assert.equal(p10055695Survivor.census_candidate.screening.corona_cell_cegar_states_checked, 22);
assert.equal(p10055695Survivor.census_candidate.screening.corona_cell_cegar_final_constraints, 44);
assert.equal(p10055695Survivor.census_candidate.screening.corona_cell_cegar_combined_states_checked, 71);
assert.match(growthAppSource, /Lazy next-ring cell promotion has now checked/);
assert.match(growthAppSource, /finite-corona evidence, not a non-tiling or aperiodicity certificate/);
assert.match(growthAppSource, /An unbounded-copy radius-two-to-three CEGAR chain proposed/);
assert.match(growthAppSource, /This upgrades the candidate's finite survival evidence, not its tiling or aperiodicity status/);
assert.equal(p10055695Survivor.census_candidate.screening.corona_partial_coverability_min_placements, 40);
assert.equal(p10055695Survivor.census_candidate.screening.corona_partial_coverability_prunes, 28);
assert.equal(p10055695Survivor.census_candidate.screening.corona_partial_coverability_validation_nodes, 4985856);
assert.equal(p10055695Survivor.census_candidate.screening.corona_placement_order_compact_complete_proposals, 14);
assert.equal(p10055695Survivor.census_candidate.screening.corona_placement_order_alternative_improved, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_partial_coverability_min_placements, 60);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_partial_coverability_prunes, 282);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_seeded_order_proposal_placements, 79);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_seeded_order_continuation_nodes, 1);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_high_copy_cegar_states_checked, 36);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_high_copy_cegar_continuation_nodes, 44);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_high_copy_cegar_space_exhausted, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_staged_coverability_states_checked, 19);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_staged_coverability_continuation_nodes, 74);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_staged_coverability_maximum_continuation_nodes, 9);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_staged_coverability_pair_constraints, 42);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_higher_order_states_checked, 41);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_higher_order_continuation_nodes, 208);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_higher_order_maximum_continuation_nodes, 13);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_higher_order_pair_constraints, 666);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_higher_order_first_quadruple_diameter, 6);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_quadruple_states_checked, 13);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_quadruple_maximum_continuation_nodes, 28);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_quadruple_pair_constraints, 699);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_quadruple_triple_constraints, 18);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_batched_triple_states_checked, 12);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_batched_triple_orbits_added, 30);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_batched_triple_final_triple_constraints, 108);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_batched_triple_final_four_timeouts, 3);
assert.equal(archivedP9LazyHigherCoverability.matched_ablation.encoded.sat_outer_states, 1);
assert.equal(archivedP9LazyHigherCoverability.matched_ablation.encoded.process_timeouts, 3);
assert.equal(archivedP9LazyHigherCoverability.matched_ablation.lazy_higher.sat_outer_states, 4);
assert.equal(archivedP9LazyHigherCoverability.matched_ablation.lazy_higher.process_timeouts, 0);
assert.equal(archivedP9LazyHigherCoverability.chained_extension.exact_tuple_rejections, 8);
assert.equal(archivedP9LazyHigherCoverability.chained_extension.final_constraints.triple, 141);
assert.equal(archivedP9LazyHigherCoverability.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_lazy_higher_extension_states, 8);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_lazy_higher_final_pair_constraints, 744);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_lazy_higher_final_triple_constraints, 141);
assert.equal(archivedP9HybridHigherCoverability.matched_seed_275_load_probe.one_encoded_orbit.z3_status, "sat");
assert.equal(archivedP9HybridHigherCoverability.matched_seed_275_load_probe.twelve_encoded_orbits.z3_status, "unknown");
assert.equal(archivedP9HybridHigherCoverability.fixed_first_orbit_chain.sat_outer_states, 11);
assert.equal(archivedP9HybridHigherCoverability.fixed_first_orbit_chain.triple_defect_states, 6);
assert.equal(archivedP9HybridHigherCoverability.recent_orbit_extension.sat_outer_states, 2);
assert.equal(archivedP9HybridHigherCoverability.recent_orbit_extension.final_constraints.triple, 174);
assert.equal(archivedP9HybridHigherCoverability.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_hybrid_higher_chain_sat_states, 13);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_hybrid_higher_pair_defect_states, 6);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_hybrid_higher_triple_defect_states, 7);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_hybrid_higher_final_triple_constraints, 174);
assert.equal(archivedP9RankedHybridCoverability.ranked_chain.sat_outer_states, 6);
assert.equal(archivedP9RankedHybridCoverability.ranked_chain.selection_transition.selected_score_after_learning, 110);
assert.equal(archivedP9RankedHybridCoverability.ranked_chain.final_constraints.triple, 207);
assert.equal(archivedP9RankedHybridCoverability.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_ranked_hybrid_states_checked, 6);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_ranked_hybrid_selected_score, 110);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_ranked_hybrid_final_triple_constraints, 207);
assert.equal(archivedP9FormulaCacheProfile.two_iteration_cegar_profile.cache_hit.pair_constraints_reused, 771);
assert.ok(archivedP9FormulaCacheProfile.two_iteration_cegar_profile.construction_runtime_reduction_fraction > 0.93);
assert.equal(archivedP9FormulaCacheProfile.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_formula_cache_pair_constraints, 771);
assert.ok(volumeNineSurvivor.census_candidate.screening.corona_formula_cache_total_reduction_fraction > 0.92);
assert.equal(archivedP9CachedRankedExtension.one_ranked_orbit_extension.sat_outer_states, 5);
assert.equal(archivedP9CachedRankedExtension.one_ranked_orbit_extension.triple_defect_states, 4);
assert.equal(archivedP9CachedRankedExtension.one_ranked_orbit_extension.final_constraints.triple, 264);
assert.equal(archivedP9CachedRankedExtension.two_ranked_orbit_probe.z3_status, "unknown");
assert.equal(archivedP9CachedRankedExtension.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cached_ranked_sat_states, 5);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cached_ranked_final_pair_constraints, 774);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cached_ranked_final_triple_constraints, 264);
assert.equal(archivedP9BatchedSolverState.positive_control.distinct_exact_models_returned, 3);
assert.equal(archivedP9BatchedSolverState.production_probe.witnesses_returned, 1);
assert.equal(archivedP9BatchedSolverState.production_probe.second_model_attempt.z3_status, "unknown");
assert.equal(archivedP9BatchedSolverState.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_batched_solver_returned_witnesses, 1);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_batched_solver_final_pair_constraints, 777);
assert.equal(archivedP9InteractiveZ3Cegar.production_chain.sat_outer_states, 9);
assert.equal(archivedP9InteractiveZ3Cegar.production_chain.unknown_timeout_trials, 0);
assert.equal(archivedP9InteractiveZ3Cegar.production_chain.production_pair_feedback.second_model_passed_pair_audit, true);
assert.equal(archivedP9InteractiveZ3Cegar.production_chain.final_constraints.triple, 336);
assert.equal(archivedP9InteractiveZ3Cegar.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_interactive_z3_sat_states, 9);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_interactive_z3_final_pair_constraints, 792);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_interactive_z3_final_triple_constraints, 336);
assert.equal(archivedP9RankedPairWindow.matched_seed_306.selected_window, 16);
assert.equal(archivedP9RankedPairWindow.matched_seed_306.rows[1].z3_status, "sat");
assert.equal(archivedP9RankedPairWindow.matched_seed_306.rows[3].z3_status, "unknown");
assert.equal(archivedP9RankedPairWindow.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_ranked_pair_window_orbits, 16);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_ranked_pair_window_constraints, 48);
assert.equal(archivedP9ReplaceablePairWindow.portfolio_totals.exact_sat_states, 9);
assert.equal(archivedP9ReplaceablePairWindow.cached_extension.window_sweep[1].pair_orbits, 64);
assert.equal(archivedP9ReplaceablePairWindow.cached_extension.window_sweep[2].z3_status, "unknown");
assert.equal(archivedP9ReplaceablePairWindow.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_replaceable_pair_sat_states, 9);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_replaceable_pair_final_constraints, 855);
assert.equal(archivedP9PairRecurrence.replay_contract.current_contract_eligible_states, 114);
assert.equal(archivedP9PairRecurrence.historical_higher_order_audit.tuple_gate_survivor_states, 0);
assert.equal(archivedP9PairRecurrence.matched_seed_321_window_16.selected_production_policy, "max-blocked-combinations");
assert.equal(archivedP9PairRecurrence.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_pair_recurrence_pair_complete_states, 26);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_pair_recurrence_tuple_survivors, 0);
assert.equal(archivedP9HistoricalCover.selection_rule.historical_defect_sets_covered, 51);
assert.equal(archivedP9HistoricalCover.matched_seeds_322_to_324.historical_cover.total_incompatible_target_pairs, 22);
assert.equal(archivedP9HistoricalCover.pair_complete_state_found, false);
assert.equal(archivedP9HistoricalCover.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_historical_cover_sets_covered, 51);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_historical_cover_pair_complete_states, 0);
assert.equal(archivedP9HistoricalCore.historical_state_model.distinct_singleton_orbits, 25);
assert.equal(archivedP9HistoricalCore.selection_rule.singleton_orbits_retained, 25);
assert.equal(archivedP9HistoricalCore.matched_seeds_325_to_327.historical_core.total_check_milliseconds, 106280);
assert.equal(archivedP9HistoricalCore.matched_seeds_325_to_327.historical_cover.total_incompatible_target_pairs, 11);
assert.equal(archivedP9HistoricalCore.pair_complete_state_found, false);
assert.equal(archivedP9HistoricalCore.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_historical_core_singleton_orbits, 25);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_historical_core_pair_complete_states, 0);
assert.equal(archivedP9AdaptivePairWindow.matched_seed_328_three_model_chain.complete_recent_defect_response.total_check_milliseconds, 114050);
assert.equal(archivedP9AdaptivePairWindow.matched_seed_328_three_model_chain.ordinary_historical_cover_control.total_incompatible_target_pairs, 21);
assert.equal(archivedP9AdaptivePairWindow.historical_cover_64_orbit_probe.historical_defect_sets_covered, 91);
assert.equal(archivedP9AdaptivePairWindow.pair_complete_state_found, false);
assert.equal(archivedP9AdaptivePairWindow.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_adaptive_pair_total_defects, 20);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_adaptive_pair_complete_states, 0);
assert.equal(archivedP9SoftPairQuota.matched_seeds_330_to_332.soft_72_of_96_constraints.total_check_milliseconds, 83163);
assert.equal(archivedP9SoftPairQuota.matched_seeds_330_to_332.hard_96_constraint_control.total_incompatible_target_pairs, 19);
assert.equal(archivedP9SoftPairQuota.symmetry_orbit_quota_ablation.quota_24.z3_status, "unknown");
assert.equal(archivedP9SoftPairQuota.selected_production_policy, "hard historical-cover");
assert.equal(archivedP9SoftPairQuota.certified_aperiodic, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_soft_pair_quota_total_defects, 19);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_soft_pair_complete_states, 0);
assert.match(growthAppSource, /grouped pseudo-Boolean encoding compresses/);
assert.match(growthAppSource, /every next-ring cell is individually coverable/);
assert.match(growthAppSource, /passes every pair and every triple/);
assert.match(growthAppSource, /observed obstruction order to four/);
assert.match(growthAppSource, /exact proposal solver now encodes that quadruple/);
assert.match(growthAppSource, /deepest survives/);
assert.match(growthAppSource, /Complete per-state triple batching/);
assert.match(growthAppSource, /monolithic proposal formula/);
assert.match(growthAppSource, /matched lazy-higher ablation/);
assert.match(growthAppSource, /next target is hybrid proposal steering/);
assert.match(growthAppSource, /Hybrid-higher screening encodes just/);
assert.match(growthAppSource, /Persistent impact ranking then follows/);
assert.match(growthAppSource, /not evidence of non-tiling or aperiodicity/);
assert.match(growthAppSource, /Validated formula caching now reuses/);
assert.match(growthAppSource, /search-throughput improvement only/);
assert.match(growthAppSource, /cached one-orbit ranked extension returns/);
assert.match(growthAppSource, /no radius-five GCTS continuation starts/);
assert.match(growthAppSource, /Exact retained-state batching can request/);
assert.match(growthAppSource, /accept each audited obstruction interactively/);
assert.match(growthAppSource, /Bidirectional retained CEGAR now does that/);
assert.match(growthAppSource, /applied before the next check/);
assert.match(growthAppSource, /Pair-level impact ranking now keeps the full/);
assert.match(growthAppSource, /without relaxing the exact gate/);
assert.match(growthAppSource, /Ranked pair steering is now genuinely replaceable/);
assert.match(growthAppSource, /not a non-tiling or aperiodicity certificate/);
assert.match(growthAppSource, /deduplicated replay independently verifies/);
assert.match(
  growthAppSource,
  /Staging exact dead-cell feedback[\s\S]*?complementary diversity lane[\s\S]*?Relaxing the cap to[\s\S]*?Same-process timeout escalation[\s\S]*?Transactional feedback now automates[\s\S]*?proves neither non-tiling nor aperiodicity/,
  "the catalogue must expose staged cell feedback without overstating the bounded screen"
);
assert.match(growthAppSource, /Impact-only remains the production lane/);
assert.match(growthAppSource, /Joint historical coverage preserves all/);
assert.match(growthAppSource, /complementary diversity lane/);
assert.match(growthAppSource, /A stricter historical-core lane identifies/);
assert.match(growthAppSource, /retained only as a proposal-diversity lane/);
assert.match(growthAppSource, /Retained CEGAR can now reserve a bounded prefix/);
assert.match(growthAppSource, /Ordinary historical-cover remains the production lane/);
assert.match(growthAppSource, /Soft global pair steering now supports/);
assert.match(growthAppSource, /Hard historical-cover remains production/);
assert.match(
  growthAppSource,
  /optional exact partial-patch rule now waits until[\s\S]*?next-ring cell has no compatible placement/,
  "the catalogue must explain the exact partial next-layer filter without implying exhaustion"
);
assert.match(
  growthAppSource,
  /seeded-first exact row ordering reaches a distinct[\s\S]*?diversity lane rather than the default/,
  "the catalogue must describe the distinct seeded boundary without promoting it to a witness"
);
assert.match(
  growthAppSource,
  /Minimum-copy CEGAR supplies[\s\S]*?high-copy space remains unexhausted/,
  "the catalogue must scope the high-copy CEGAR portfolio as incomplete"
);
assert.deepEqual(
  archivedVolume10GctsFunnelThrough9.final_free_class_candidates.map(candidate => candidate.id).sort(),
  ["p10-052588", "p10-054782", "p10-055695", "p10-290795", "p10-346304"]
);
assert.ok(archivedVolume10GctsFunnelThrough9.final_free_class_candidates.every(candidate =>
  candidate.radius_2.patch_independently_verified
  && candidate.radius_3.complete_patch_found === false
  && candidate.radius_3.search_exhausted === false
));
assert.equal(archivedPolycubeContinuationNogoods.summary.carried_nogood_clauses, 6573);
assert.equal(archivedPolycubeContinuationNogoods.summary.total_explained_obstructions, 54);
assert.equal(archivedPolycubeContinuationNogoods.summary.radius_5_witness_found, false);
assert.equal(archivedPolycubeContinuationNogoods.summary.outer_search_exhausted, false);
assert.equal(archivedPolycubePeriodicThrough13.cumulative.hnf_quotients_for_copies_1_through_13, 169511);
assert.equal(archivedPolycubePeriodicThrough13.cumulative.exact_cover_nodes, 13121513);
assert.equal(archivedPolycubePeriodicThrough13.cumulative.certificate_found, false);
assert.equal(archivedPolycubeCopy14Multisolver.periodic_copy_14.hnf_bases_exhausted, 51870);
assert.equal(archivedPolycubeCopy14Multisolver.periodic_copy_14.exact_cover_nodes, 21267747);
assert.equal(archivedPolycubeCopy14Multisolver.periodic_copy_14.coverage_gap_free, true);
assert.equal(archivedPolycubeCopy14Multisolver.periodic_copy_14.periodic_certificate, false);
assert.equal(archivedPolycubeCopy14Multisolver.periodic_cumulative.hnf_bases_exhausted, 221381);
assert.equal(archivedPolycubeCopy14Multisolver.periodic_cumulative.exact_cover_nodes, 34389260);
assert.equal(archivedPolycubeCopy14Multisolver.corona_backend_cross_check.python_z3_radius_5.incidence_counts_agree, true);
assert.ok(archivedPolycubeCopy14Multisolver.corona_backend_cross_check.radius_4_positive_controls.every(
  control => control.independently_verified
));
assert.equal(archivedPolycubeCopy14Multisolver.radius_5_search.z3_portfolio.witness_found, false);
assert.equal(archivedPolycubeCopy14Multisolver.radius_5_search.z3_portfolio.unsat_proved, false);
assert.equal(archivedPolycubeCopy14Multisolver.radius_5_search.javascript_restart_portfolio.search_exhausted, false);
assert.equal(archivedPolycubeZ3Cegar.positive_control.exact_dead_outer_states, 17);
assert.equal(archivedPolycubeZ3Cegar.positive_control.verified_inner_witness_found, true);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.combined_exact_dead_outer_states, 284);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.combined_symmetry_closed_clauses, 807);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.one_step_coverability.exact_dead_outer_states, 4);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.one_step_coverability.immediate_dead_target_obstructions, 0);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.one_step_coverability.resolved_subtree_obstructions, 4);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.pair_coverability.initial_symmetry_closed_pair_constraints, 72);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.pair_coverability.pair_filtered_exact_dead_outer_states, 2);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.pair_coverability.final_symmetry_closed_pair_constraints, 114);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.pair_coverability.pair_114_exhausted, false);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.economical_outer_patches.minimum_outer_placements_witnessed, 62);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.economical_outer_patches.max_62_exhausted, false);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.radius_4_space_exhausted, false);
assert.equal(archivedPolycubeZ3Cegar.radius_4_to_5.certified_non_tiler, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.periodic_hnf_candidates_exhausted, 221381);
assert.equal(
  volumeNineSurvivor.census_candidate.screening.periodic_hnf_report,
  "data/polycube-volume9-copy14-multisolver-2026-08-21.json"
);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_z3_radius4_fast_verified, true);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_z3_radius5_runs, 6);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_z3_radius5_witness, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_z3_radius5_unsat, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cegar_radius4_states_checked, 284);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cegar_symmetry_closed_clauses, 807);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cegar_minimum_radius4_placements, 62);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cegar_lookahead_resolved_subtree_obstructions, 4);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cegar_pair_final_constraints, 114);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cegar_pair_lazy_subset_replays_verified, 2);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cegar_pair_lazy_minimum_clause_size, 4);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cegar_pair_witness_cnf_states_checked, 2);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cegar_pair_witness_cnf_max62_states_checked, 1);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cegar_radius4_exhausted, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_cegar_certified_non_tiler, false);
assert.equal(
  volumeNineSurvivor.census_candidate.screening.corona_nogood_portfolio_report,
  "data/polycube-volume9-continuation-nogoods-2026-08-20.json"
);
assert.deepEqual(archivedPolycubeCoronaForcing.totals, {
  tested: 9,
  forced: 0,
  replaceable: 9,
  incomplete: 0
});
assert.ok(archivedPolycubeCoronaForcing.probes.every(probe => probe.alternative_verified));
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_forcing_individually_forced, 0);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_forcing_replaceable, 9);
assert.equal(
  volumeNineSurvivor.census_candidate.screening.corona_forcing_report,
  "data/polycube-volume9-corona-forcing-2026-08-20.json"
);
assert.equal(archivedPolycubeContactDisjunction.catalog.contact_types, 69);
assert.equal(archivedPolycubeContactDisjunction.algorithm.corona_constraints_at_proof, 92);
assert.equal(archivedPolycubeContactDisjunction.forced_disjunction.minimum_nontrivial_size, 6);
assert.equal(archivedPolycubeContactDisjunction.forced_disjunction.forbidden_placements, 36);
assert.equal(archivedPolycubeContactDisjunction.replay.all_exhausted, true);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_contact_minimum_nontrivial_disjunction, 6);
assert.equal(
  volumeNineSurvivor.census_candidate.screening.corona_contact_disjunction_report,
  "data/polycube-volume9-contact-disjunction-2026-08-20.json"
);
assert.equal(archivedPolycubeContactPropagation.active_to_active_placements, 9);
assert.deepEqual(archivedPolycubeContactPropagation.reciprocal_cycles.map(cycle => cycle.types), [
  [3, 44],
  [29]
]);
assert.ok(archivedPolycubeContactPropagation.cycle_extension_trials.every(trial => trial.success));
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_contact_reciprocal_cycles, 2);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_contact_cycle_completed_radius, 4);
assert.equal(
  volumeNineSurvivor.census_candidate.screening.corona_contact_propagation_report,
  "data/polycube-volume9-contact-propagation-2026-08-20.json"
);
assert.equal(archivedPolycubeConditionalContactTransitions.reciprocal_incoming_orbits, 12);
assert.equal(archivedPolycubeConditionalContactTransitions.inactive_incoming_orbits, 9);
assert.equal(archivedPolycubeConditionalContactTransitions.active_incoming_orbits, 3);
assert.equal(archivedPolycubeConditionalContactTransitions.possible_transition_edges, 134);
assert.equal(archivedPolycubeConditionalContactTransitions.seed_replays_agree, true);
assert.equal(archivedPolycubeConditionalContactTransitions.all_incoming_orbits_extendable, true);
assert.equal(
  archivedPolycubeConditionalContactTransitions.all_inactive_incoming_orbits_require_an_outgoing_active_contact,
  true
);
assert.equal(archivedPolycubeConditionalContactTransitions.inactive_rules_only_require_any_possible_state, true);
assert.equal(archivedPolycubeConditionalContactTransitions.all_active_incoming_orbits_can_terminate, true);
assert.deepEqual(archivedPolycubeConditionalContactTransitions.terminating_active_incoming_orbits, [1, 6, 11]);
assert.equal(
  volumeNineSurvivor.census_candidate.screening.corona_contact_conditional_report,
  "data/polycube-volume9-conditional-contact-transitions-2026-08-20.json"
);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_contact_reciprocal_incoming_orbits, 12);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_contact_conditional_transition_edges, 134);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_contact_radius_one_forces_unbounded_chain, false);
assert.equal(archivedPolycubeCoronaBoundaryStates.portfolio.canonical_boundary_states, 2522);
assert.equal(archivedPolycubeCoronaBoundaryStates.portfolio.obstructed_boundary_states, 1922);
assert.equal(archivedPolycubeCoronaBoundaryStates.portfolio.extendable_boundary_states, 600);
assert.equal(archivedPolycubeCoronaBoundaryStates.portfolio.incomplete_boundary_states, 0);
assert.equal(archivedPolycubeCoronaBoundaryStates.portfolio.repeated_state_outcomes_agree, true);
assert.ok(archivedPolycubeCoronaBoundaryStates.portfolio.trials.every(trial =>
  trial.extendable + trial.obstructed === trial.sampled
));
assert.equal(archivedPolycubeCoronaBoundaryStates.learned_portfolio.explained_obstructions, 2070);
assert.equal(archivedPolycubeCoronaBoundaryStates.learned_portfolio.final_nogood_clauses, 2089);
assert.equal(archivedPolycubeCoronaBoundaryStates.learned_portfolio.nogood_prunes, 41824);
assert.deepEqual(
  archivedPolycubeCoronaBoundaryStates.deeper_boundary_samples.radius2_to_radius3_unlearned,
  {
    seeds: [0, 1, 2, 3],
    sampled_states_per_seed: 100,
    sampled_states: 400,
    extendable_states: 0,
    obstructed_states: 400,
    incomplete_states: 0,
    maximum_continuation_nodes: 6,
    warning: "The traversal prefixes are strongly order-biased; a known radius-three witness proves that extendable radius-two states exist."
  }
);
assert.equal(
  archivedPolycubeCoronaBoundaryStates.deeper_boundary_samples.radius2_to_radius3_learned.extendable_states,
  462
);
assert.equal(
  archivedPolycubeCoronaBoundaryStates.deeper_boundary_samples.radius3_to_radius4_learned.nogood_prunes,
  10100253
);
assert.equal(archivedPolycubeCoronaBoundaryStates.deep_proposal_ablation.radius3_to_radius4.direct_proposal.success, true);
assert.equal(archivedPolycubeCoronaBoundaryStates.deep_proposal_ablation.radius3_to_radius4.direct_proposal.verified, true);
assert.equal(archivedPolycubeCoronaBoundaryStates.deep_proposal_ablation.radius3_to_radius4.direct_proposal.nodes, 4786);
assert.equal(
  archivedPolycubeCoronaBoundaryStates.deep_proposal_ablation.radius4_to_radius5_equal_wall_budget.direct_proposal_then_outer.success,
  false
);
assert.equal(
  archivedPolycubeCoronaBoundaryStates.deep_proposal_ablation.adaptive_250ms_profile.radius3_to_radius4.verified,
  true
);
assert.ok(
  archivedPolycubeCoronaBoundaryStates.deep_proposal_ablation.adaptive_250ms_profile.radius4_to_radius5_equal_wall_budget.node_coverage_ratio
  > 0.98
);
assert.equal(archivedPolycubeCoronaBoundaryStates.symmetry_nogood_ablation.symmetry_closed.symmetry_clauses, 1820);
assert.equal(
  volumeNineSurvivor.census_candidate.screening.corona_boundary_state_report,
  "data/polycube-volume9-corona-boundary-states-2026-08-20.json"
);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_boundary_sampled_states, 2522);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_boundary_obstructed_states, 1922);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_boundary_extendable_states, 600);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_boundary_radius2_learned_survivors, 462);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_boundary_radius3_stress_prunes, 10100253);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_deep_proposal_radius4_nodes, 4786);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_deep_proposal_radius4_verified, true);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_deep_proposal_radius5_improved_equal_budget, false);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_adaptive_proposal_milliseconds, 250);
assert.ok(volumeNineSurvivor.census_candidate.screening.corona_adaptive_proposal_radius5_coverage_ratio > 0.98);
assert.equal(volumeNineSurvivor.census_candidate.screening.corona_symmetry_nogood_closure_improved, false);
assert.equal(LATTICE_POLYHEDRON_SHELL_REJECTS.length, 3);
assert.equal(LATTICE_POLYHEDRON_SURVIVORS.length, 0);
assert.equal(LATTICE_POLYHEDRON_PERIODIC_REJECTS.length, 1);
assert.equal(LATTICE_POLYHEDRON_SIZE11_CONTROLS.length, 8);
assert.equal(LATTICE_POLYHEDRON_SIZE11_SCREENING.source_pool_size, 156464);
assert.deepEqual(archivedSize11FirstStage.counts, {
  localEdgeObstruction: 156400,
  extendableShellObstruction: 56,
  shellOneWitness: 8,
  incomplete: 0,
  other: 0
});
assert.equal(archivedSize11ShellThree.totals.certifiedNonTilerTrials, 6);
assert.equal(archivedSize11Periodic.rows.length, 6);
assert.ok(archivedSize11Periodic.rows.every(row => row.translational?.certified));
assert.equal(LATTICE_POLYHEDRON_SIZE12_CONTROLS.length, 27);
assert.equal(LATTICE_POLYHEDRON_SIZE12_SCREENING.source_pool_size, 503443);
assert.equal(LATTICE_POLYHEDRON_SIZE13_CONTROLS.length, 3);
assert.equal(LATTICE_POLYHEDRON_SIZE13_SCREENING.source_pool_size, 1502640);
assert.equal(archivedSize13FirstStage.configuration.completeConfiguredSize, true);
assert.equal(archivedSize13FirstStage.screenedCandidates, 1502640);
assert.deepEqual(archivedSize13FirstStage.counts, {
  localEdgeObstruction: 1502508,
  extendableShellObstruction: 39,
  shellOneWitness: 93,
  incomplete: 0,
  other: 0
});
assert.equal(archivedSize13Periodic.rows.length, 93);
assert.equal(archivedSize13Periodic.rows.filter(row => row.classification === "reject_certified_periodic").length, 88);
assert.equal(archivedSize13Periodic.rows.filter(row => row.classification === "reject_certified_isohedral").length, 2);
assert.deepEqual(
  archivedSize13Periodic.rows.filter(row => row.classification === "inconclusive").map(row => row.id).sort(),
  ["13_0492735", "13_1072824", "13_1429971"]
);
assert.equal(archivedSize13ShellTwo.totals.certifiedNonTilerTrials, 9);
assert.equal(archivedSize13ShellTwo.totals.incompleteTrials, 0);
assert.ok(archivedSize13ShellTwo.rows.every(row =>
  row.resultKind === "no_tiling"
  && row.canTile === false
  && row.certificateKind === "finite_shell_obstruction"
));
assert.equal(LATTICE_POLYHEDRON_SIZE12_SCREENING.certified_periodic_tilers, 63);
assert.equal(LATTICE_POLYHEDRON_SIZE12_SCREENING.shell_two_non_tilers, 2);
assert.equal(LATTICE_POLYHEDRON_SIZE12_SCREENING.shell_three_non_tilers, 0);
assert.equal(LATTICE_POLYHEDRON_SIZE12_SCREENING.shell_four_non_tilers, 0);
assert.equal(LATTICE_POLYHEDRON_SIZE12_SCREENING.unresolved_after_shell_four, 0);
assert.equal(LATTICE_POLYHEDRON_SIZE12_SCREENING.unresolved_candidate, null);
assert.deepEqual(archivedSize12FirstStage.counts, {
  localEdgeObstruction: 503353,
  extendableShellObstruction: 25,
  shellOneWitness: 65,
  incomplete: 0,
  other: 0
});
assert.equal(archivedSize12ShellTwo.totals.certifiedNonTilerTrials, 3);
assert.equal(archivedSize12ShellTwo.totals.targetHits, 8);
assert.equal(archivedSize12ShellThree.totals.certifiedNonTilerTrials, 3);
assert.equal(archivedSize12ShellThree.totals.targetHits, 5);
assert.equal(archivedSize12ShellFour.totals.certifiedNonTilerTrials, 2);
assert.equal(archivedSize12ShellFour.totals.targetHits, 2);
assert.equal(archivedSize12ShellFour.totals.incompleteTrials, 1);
assert.deepEqual(
  archivedSize12ShellFour.rows.filter(row => row.certified && row.canTile === false).map(row => row.candidate).sort(),
  ["12_124794", "12_424326"]
);
assert.equal(archivedSize12ShellSix.totals.targetHits, 2);
for (const periodicReport of [archivedSize12Periodic204255, archivedSize12Periodic405129]) {
  assert.equal(periodicReport.result.certifiedPeriodic, true);
  assert.equal(periodicReport.result.certificateCompleted, true);
  assert.equal(periodicReport.result.evidence?.can_tile, true);
}
assert.equal(archivedSize12Periodic204255.result.evidence.patch_size, 8);
assert.equal(archivedSize12Periodic405129.result.evidence.patch_size, 24);
assert.equal(archivedSize12Periodic235174.result.resultKind, "certified_tiling");
assert.equal(archivedSize12Periodic235174.result.canTile, true);
assert.equal(archivedSize12Periodic235174.result.evidence.patch_size, 2);
assert.equal(archivedSize12Periodic235174.configuration.orientationGroup, "proper cubic lattice orientations");
assert.deepEqual(correctedConvexPeriodicRescreen.totals, {
  candidates: 9,
  certifiedPeriodic: 9,
  properOrientationCertificates: 3,
  fullIsometryCertificates: 6,
  maximumMotifTiles: 2
});
assert.ok(correctedConvexPeriodicRescreen.rows.every(row =>
  row.result.resultKind === "certified_tiling"
  && row.result.canTile === true
  && row.result.evidence?.periodic_template?.proof?.overlap_validation === "complete_lattice_translation_neighborhood"
));
assert.equal(correctedConvexNonTilers.totals.certifiedNonTilerTrials, 4);
assert.deepEqual(
  correctedConvexNonTilers.rows.map(row => row.candidate).sort(),
  ["10_45026", "12_121693", "12_158688", "9_11683"]
);
assert.equal(corrected16113NonTiler.configuration.failureMemo, false);
assert.equal(corrected16113NonTiler.configuration.globalZeroFacePruning, false);
assert.equal(corrected16113NonTiler.configuration.globalFrontierGraph, true);
assert.equal(corrected16113NonTiler.totals.certifiedNonTilerTrials, 3);
assert.equal(corrected16113NonTiler.totals.incompleteTrials, 0);
assert.ok(corrected16113NonTiler.rows.every(row =>
  row.resultKind === "no_tiling"
  && row.canTile === false
  && row.certificateKind === "finite_shell_obstruction"
  && row.visitedNodes === 50
  && row.shellFaceMatchAttempts < 20000
));
assert.equal(archivedSize12CandidateShellThreePortfolio.totals.targetHits, 20);
assert.equal(archivedSize12CandidateShellThreePortfolio.candidates[0].distinctBestWitnesses, 20);
assert.equal(archivedSize12CandidateShellFourExtensions.rows.length, 20);
assert.ok(archivedSize12CandidateShellFourExtensions.rows.every(row =>
  row.resultKind === "patch_extension_impossible"
  && row.canTile === null
  && row.initialPatchSourceSeed === row.seed
  && row.initialPatchSelection === "candidate_and_seed"
));
assert.deepEqual(archivedSize12CandidatePeriodicityPortfolio.totals, {
  witnesses: 20,
  completed: 20,
  timedOut: 0,
  certifiedPeriodic: 0,
  distinctWitnesses: 20,
  basesTested: 303583
});
assert.equal(archivedSize12Periodic.rows.length, 65);
assert.equal(archivedSize12Periodic.rows.filter(row => row.translational?.certified).length, 54);
assert.equal(archivedSize12Periodic.rows.filter(row => row.classification === "inconclusive").length, 11);
assert.equal(archivedSize12Periodic.rows.find(row => row.id === "12_235174")?.classification, "inconclusive");
assert.equal(archivedShellContinuation.checkpoints.at(-1).shellDepth, 7);
assert.equal(archivedCandidatePeriodic.certificate.motif.length, 6);

async function solve(config) {
  let final = null;
  let largestPatch = 0;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    largestPatch = Math.max(largestPatch, message.tile_count ?? message.placements?.length ?? 0);
    if (message.type === "finished") final = message;
  }
  assert.ok(final, "search must emit a terminal result");
  return { final, largestPatch };
}

const corrected16113Figure = candidates.find(figure => figure.census_candidate.id === "10_16113");
const corrected16113Proof = await solve({
  mode_key: corrected16113Figure.mode_key,
  custom_system: {
    name: "10_16113 exact shell-2 regression",
    figure_refs: [corrected16113Figure.id],
    polycubes: [],
    polycube_lattice: "z3"
  },
  criterion: "shell",
  target_val: 2,
  tiling_strategy: "free_range",
  move_order: "shell",
  face_order: "mrv",
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_complete_shell_enumeration: true,
  generic_global_frontier_graph: true,
  generic_global_zero_face_pruning: false,
  generic_failure_memo: false,
  include_mirrors: true,
  template_preflight: false,
  snapshot_every: 0,
  branch_cap: null,
  candidate_cap: null,
  node_limit: 10000,
  time_limit_ms: 5000,
  seeded_tie_breaks: false,
  ui_yield_interval_ms: 1000000
});
assert.notEqual(
  corrected16113Proof.final.can_tile,
  false,
  "a face-to-face shell obstruction for a general lattice polyhedron must not be promoted to unrestricted lattice non-tiling"
);
assert.ok(
  corrected16113Proof.final.search_stats.generic_shell_face_match_attempts < 20000,
  "translation-normalized face indexing should avoid scanning every oriented face anchor"
);

let candidateRun = null;
for (const periodicControl of periodicControls) {
  const certificateLane = periodicControl.census_candidate.screening.certificate === "isohedral_periodic_quotient"
    ? "isohedral"
    : "translational";
  candidateRun = await solve({
    mode_key: periodicControl.mode_key,
    custom_system: {
      name: "Candidate catalog smoke test",
      figure_refs: [periodicControl.id],
      polycubes: [],
      polycube_lattice: "z3"
    },
    polycube_lattice: "z3",
    criterion: "count",
    target_val: periodicControl.census_candidate.screening.motif_tiles,
    tiling_strategy: certificateLane,
    exhaustive: true,
    include_mirrors: !!periodicControl.census_candidate.screening.requires_mirrors,
    snapshot_every: 0,
    placement_details: true,
    face_order: "mrv",
    move_order: "balanced",
    known_periodic_template: periodicControl.census_candidate.screening.periodic_template,
    time_limit_ms: 2000,
    ui_yield_interval_ms: 100,
    template_preflight: true
  });
  assert.equal(candidateRun.final.success, true, `${periodicControl.census_candidate.id} must replay its verified quotient`);
  assert.equal(candidateRun.final.result_kind, "certified_tiling");
  assert.equal(candidateRun.final.tiling_evidence?.patch_size, periodicControl.census_candidate.screening.motif_tiles);
  assert.equal(candidateRun.final.can_tile, true);
  if (periodicControl.census_candidate.id === "a2lp_7_00694") {
    assert.equal(
      candidateRun.final.tiling_evidence?.periodic_template?.proof?.method,
      "exact_weighted_lattice_function_quotient"
    );
    assert.equal(candidateRun.final.tiling_evidence?.periodic_template?.quotient_classes, 28);
  }
  if (certificateLane === "isohedral") {
    assert.equal(candidateRun.final.tiling_evidence?.kind, "isohedral_certificate");
    assert.match(candidateRun.final.tiling_evidence?.certificate_kind ?? "", /isohedral_periodic_quotient/);
  }
}

const exhaustiveWitness = await solve({
  mode_key: "cube",
  criterion: "count",
  target_val: 2,
  tiling_strategy: "free_range",
  exhaustive: true,
  template_preflight: false,
  time_limit_ms: 1000
});
assert.equal(exhaustiveWitness.final.success, true, "exhaustive mode must stop when it finds a witness");
assert.equal(exhaustiveWitness.final.result_kind, "patch_found");

const conwayFigure = tileSpecs.figureCatalog.find(figure => figure.mode_key === "scd_conway");
assert.ok(conwayFigure?.aperiodic_tile, "the Conway biprism must be visible as a known aperiodic monotile");
const conwayTile = tileSpecs.TILING_REGISTRY.scd_conway.build()[0];
assert.ok(conwayTile.verts.flat().every(Number.isInteger), "the catalog realization must have lattice vertices");
const conwayRun = await solve({
  mode_key: "scd_conway",
  custom_system: {
    name: "SCD layered construction",
    figure_refs: ["scd_conway::0"],
    polycubes: [],
    polycube_lattice: "z3"
  },
  criterion: "count",
  target_val: 24,
  tiling_strategy: "free_range",
  include_mirrors: false,
  snapshot_every: 1,
  placement_details: true
});
assert.equal(conwayRun.final.success, true);
assert.equal(conwayRun.final.can_tile, true);
assert.equal(conwayRun.final.result_kind, "known_aperiodic_construction");
assert.equal(conwayRun.largestPatch, 24);

console.log("3D census candidate regressions passed", {
  candidates: candidates.length,
  periodicControls: periodicControls.length,
  shellControls: shellControls.length,
  corrected16113ProofNodes: corrected16113Proof.final.search_stats.visited_nodes,
  firstPatch: candidateRun.largestPatch,
  visitedNodes: candidateRun.final.search_stats.visited_nodes,
  conwayPatch: conwayRun.largestPatch
});
