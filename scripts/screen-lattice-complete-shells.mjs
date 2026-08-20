#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import { LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES } from "../assets/lattice-polyhedron-survivors.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const numberArg = (name, fallback) => {
  const value = Number(args.get(name));
  return Number.isFinite(value) ? value : fallback;
};
const targetShellDepth = Math.max(1, Math.floor(numberArg("target", 2)));
const cascade = args.get("cascade") === "true";
const timeMs = Math.max(50, Math.floor(numberArg("time-ms", 20000)));
const nodeLimit = Math.max(1, Math.floor(numberArg("node-limit", 10000)));
const outputFile = args.get("output-file") ?? null;
const includeWitness = args.get("include-witness") === "true";
const initialPatchFile = args.get("initial-patch-file") ?? null;
const failureMemo = args.get("failure-memo") !== "false";
const includeMirrors = args.get("include-mirrors") === "true";
const globalZeroFacePruning = args.get("global-zero-face-pruning") === "true";
const failureMemoSymmetry = args.get("memo-symmetry") === "fixed" ? "fixed" : "rigid";
const seededTieBreaks = args.get("seeded-tie-breaks") !== "false";
const seeds = [...new Set((args.get("seeds") ?? "1,2,3")
  .split(",")
  .map(value => Math.floor(Number(value)))
  .filter(value => Number.isFinite(value) && value > 0))];
if (!seeds.length) seeds.push(1);
const requestedIds = new Set((args.get("ids") ?? "").split(",").filter(Boolean));
const excludeCertifiedPeriodic = args.get("exclude-certified-periodic") === "true";
const candidatesFile = args.get("candidates-file") ?? null;
const candidatesDocument = candidatesFile
  ? JSON.parse(await readFile(candidatesFile, "utf8"))
  : null;
const candidatePool = candidatesDocument
  ? (candidatesDocument.survivors ?? candidatesDocument.candidates ?? candidatesDocument.rows ?? candidatesDocument)
  : LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES;
if (!Array.isArray(candidatePool)) throw new Error("Candidate input must be an array or contain a survivors/candidates array");
const candidates = candidatePool.filter(candidate =>
  (!requestedIds.size || requestedIds.has(candidate.id))
  && (!excludeCertifiedPeriodic || candidate.classification !== "reject_certified_periodic")
);
const initialPatchDocument = initialPatchFile
  ? JSON.parse(await readFile(initialPatchFile, "utf8"))
  : null;
const initialPatchRow = (initialPatchDocument?.rows ?? [])
  .filter(row => Array.isArray(row.bestShellWitness)
    && (!requestedIds.size || requestedIds.has(row.candidate)))
  .sort((left, right) =>
    (right.bestShellDepth ?? 0) - (left.bestShellDepth ?? 0)
    || (right.bestShellWitness?.length ?? 0) - (left.bestShellWitness?.length ?? 0)
  )[0] ?? null;
const initialPatch = Array.isArray(initialPatchDocument)
  ? initialPatchDocument
  : Array.isArray(initialPatchDocument?.placements)
    ? initialPatchDocument.placements
    : initialPatchRow?.bestShellWitness ?? null;

const patchHash = placements => createHash("sha256")
  .update((placements ?? []).map(placement => [
    placement.prototile_idx,
    placement.orientation_id ?? placement.orientation_signature,
    ...(placement.translation ?? [])
  ].join(":"))
    .sort()
    .join("||"))
  .digest("hex")
  .slice(0, 16);

const configFor = (candidate, seed, targetDepth) => ({
  mode_key: "cube",
  custom_system: {
    name: `Complete-shell screen ${candidate.id}`,
    figure_refs: [],
    polycubes: [],
    polyhedra: [{ name: `Candidate ${candidate.id}`, vertices: candidate.vertices }],
    polycube_lattice: "z3"
  },
  criterion: "shell",
  target_val: targetDepth,
  tiling_strategy: "free_range",
  move_order: "shell",
  face_order: "mrv",
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_complete_shell_enumeration: true,
  generic_global_zero_face_pruning: globalZeroFacePruning,
  generic_failure_memo: failureMemo,
  generic_failure_memo_symmetry: failureMemoSymmetry,
  generic_failure_memo_max_states: 200000,
  generic_geometric_nogood: false,
  include_mirrors: includeMirrors,
  template_preflight: false,
  snapshot_every: 1,
  placement_details: true,
  branch_cap: null,
  candidate_cap: null,
  node_limit: nodeLimit,
  time_limit_ms: timeMs,
  random_seed: seed,
  seeded_tie_breaks: seededTieBreaks,
  ...(initialPatch ? { initial_patch: { placements: initialPatch } } : {}),
  ui_yield_interval_ms: 1000000
});

const witnessDescriptor = placements => {
  if (!Array.isArray(placements) || !placements.length) return null;
  const rootTranslation = placements[0].translation ?? [0, 0, 0];
  return placements.map(placement => ({
    prototile_idx: placement.prototile_idx ?? 0,
    orientation_index: placement.orientation_index,
    orientation_id: placement.orientation_id ?? null,
    translation: (placement.translation ?? [0, 0, 0]).map((value, axis) =>
      value - rootTranslation[axis]
    )
  }));
};

async function runCandidate(candidate, seed, targetDepth) {
  const started = performance.now();
  let final = null;
  let bestShellDepth = 0;
  let bestShellPatchTiles = 1;
  let bestShellWitnessHash = null;
  let bestShellWitness = null;
  let maxLiveTiles = 1;
  let maxFrontierFaces = 0;
  let maxGlobalCandidates = 0;
  let minimumRootExposedFaces = Infinity;
  let maxShellReachableTiles = 0;
  let maxUnreachableExposedFaces = 0;
  const shellMilestones = [];
  for await (const message of createTilingStream(configFor(candidate, seed, targetDepth), tileSpecs, { stop: false })) {
    const snapshot = message.type === "node_snapshot" ? message.snapshot : message;
    const shellDepth = snapshot?.frontier_stats?.complete_shell_depth ?? 0;
    const tileCount = snapshot?.tile_count ?? snapshot?.placements?.length ?? 0;
    maxLiveTiles = Math.max(maxLiveTiles, tileCount, snapshot?.search_stats?.max_live_tiles ?? 0);
    maxFrontierFaces = Math.max(maxFrontierFaces, snapshot?.frontier_stats?.total_faces ?? 0);
    if (Number.isFinite(snapshot?.frontier_stats?.root_exposed_face_count)) {
      minimumRootExposedFaces = Math.min(
        minimumRootExposedFaces,
        snapshot.frontier_stats.root_exposed_face_count
      );
    }
    maxShellReachableTiles = Math.max(
      maxShellReachableTiles,
      snapshot?.frontier_stats?.shell_reachable_tiles ?? 0
    );
    maxUnreachableExposedFaces = Math.max(
      maxUnreachableExposedFaces,
      snapshot?.frontier_stats?.unreachable_exposed_face_count ?? 0
    );
    maxGlobalCandidates = Math.max(
      maxGlobalCandidates,
      snapshot?.search_stats?.generic_global_extension_max_candidates ?? 0
    );
    if (shellDepth > bestShellDepth) {
      bestShellDepth = shellDepth;
      bestShellPatchTiles = tileCount;
      bestShellWitnessHash = Array.isArray(snapshot?.placements) && snapshot.placements.length
        ? patchHash(snapshot.placements)
        : null;
      if (includeWitness && Array.isArray(snapshot?.placements) && snapshot.placements.length) {
        bestShellWitness = witnessDescriptor(snapshot.placements);
      }
      shellMilestones.push({
        shellDepth,
        tileCount,
        witnessHash: bestShellWitnessHash,
        visitedNodes: snapshot?.search_stats?.visited_nodes ?? 0,
        elapsedMs: Math.round(performance.now() - started)
      });
    }
    if (
      shellDepth === bestShellDepth
      && shellDepth > 0
      && !bestShellWitnessHash
      && Array.isArray(snapshot?.placements)
      && snapshot.placements.length
    ) {
      bestShellPatchTiles = snapshot.placements.length;
      bestShellWitnessHash = patchHash(snapshot.placements);
      if (includeWitness) bestShellWitness = witnessDescriptor(snapshot.placements);
      const milestone = shellMilestones.at(-1);
      if (milestone?.shellDepth === shellDepth) {
        milestone.tileCount = bestShellPatchTiles;
        milestone.witnessHash = bestShellWitnessHash;
      }
    }
    if (message.type === "finished") final = message;
  }
  const stats = final?.search_stats ?? {};
  maxLiveTiles = Math.max(maxLiveTiles, stats.max_live_tiles ?? 0);
  return {
    candidate: candidate.id,
    seed,
    targetShellDepth: targetDepth,
    resultKind: final?.result_kind ?? "missing_result",
    success: !!final?.success,
    canTile: final?.can_tile ?? null,
    certified: !!final?.tiling_evidence?.certified,
    certificateKind: final?.tiling_evidence?.kind ?? null,
    searchIncomplete: !!final?.search_incomplete,
    terminationReason: stats.termination_reason
      ?? (final?.success ? "target_reached" : final?.search_incomplete ? "bounded_incomplete" : "exhausted"),
    elapsedMs: Math.round(performance.now() - started),
    bestShellDepth,
    bestShellPatchTiles,
    bestShellWitnessHash,
    ...(includeWitness ? { bestShellWitness } : {}),
    maxLiveTiles,
    maxFrontierFaces,
    maxGlobalCandidates,
    minimumRootExposedFaces: Number.isFinite(minimumRootExposedFaces) ? minimumRootExposedFaces : null,
    maxShellReachableTiles,
    maxUnreachableExposedFaces,
    visitedNodes: stats.visited_nodes ?? 0,
    backtracks: stats.backtracks ?? 0,
    failedStates: stats.generic_failure_memo_states ?? 0,
    failureMemoHits: stats.generic_failure_memo_hits ?? 0,
    globalZeroFaceDeadEnds: stats.generic_global_zero_face_dead_ends ?? 0,
    initialPatchAppliedTiles: stats.initial_patch_applied_tiles ?? 0,
    initialPatchBaseShellDepth: stats.initial_patch_base_shell_depth ?? 0,
    shellMilestones
  };
}

const rows = [];
for (const candidate of candidates) {
  for (const seed of seeds) {
    const targets = cascade
      ? Array.from({ length: targetShellDepth }, (_, index) => index + 1)
      : [targetShellDepth];
    for (const targetDepth of targets) {
      const row = await runCandidate(candidate, seed, targetDepth);
      rows.push(row);
      if (args.get("progress") !== "false") process.stderr.write(
        `${candidate.id} seed ${seed}: shell ${row.bestShellDepth}/${targetDepth}, ${row.maxLiveTiles} tiles, ${row.terminationReason}\n`
      );
      if (row.certified && row.canTile === false) break;
      if (row.searchIncomplete) break;
    }
  }
}

const byCandidate = candidates.map(candidate => {
  const trials = rows.filter(row => row.candidate === candidate.id);
  return {
    candidate: candidate.id,
    trials: trials.length,
    targetHits: trials.filter(row => row.success).length,
    deepestCompletedShell: Math.max(0, ...trials.filter(row => row.success).map(row => row.targetShellDepth)),
    firstCertifiedObstructionDepth: Math.min(
      Infinity,
      ...trials.filter(row => row.certified && row.canTile === false).map(row => row.targetShellDepth)
    ),
    certifiedNonTilerTrials: trials.filter(row => row.certified && row.canTile === false).length,
    minimumBestShellDepth: Math.min(...trials.map(row => row.bestShellDepth)),
    maximumBestShellDepth: Math.max(...trials.map(row => row.bestShellDepth)),
    minimumShellWitnessTiles: Math.min(...trials.map(row => row.bestShellPatchTiles)),
    maximumShellWitnessTiles: Math.max(...trials.map(row => row.bestShellPatchTiles)),
    distinctBestWitnesses: new Set(trials.map(row => row.bestShellWitnessHash).filter(Boolean)).size,
    totalVisitedNodes: trials.reduce((sum, row) => sum + row.visitedNodes, 0),
    totalBacktracks: trials.reduce((sum, row) => sum + row.backtracks, 0)
  };
});
const report = {
  schemaVersion: 1,
  kind: "lattice_polyhedron_complete_shell_screen",
  generatedAt: new Date().toISOString(),
  configuration: {
    targetShellDepth,
    includeMirrors,
    cascade,
    timeMs,
    nodeLimit,
    seeds,
    failureMemo,
    failureMemoSymmetry,
    seededTieBreaks,
    globalZeroFacePruning,
    includeWitness,
    initialPatch: initialPatch
      ? {
          tiles: initialPatch.length,
          candidate: initialPatchRow?.candidate ?? null,
          completedShellDepth: initialPatchRow?.bestShellDepth ?? null,
          witnessHash: initialPatchRow?.bestShellWitnessHash ?? null
        }
      : null,
    candidatesFile,
    excludeCertifiedPeriodic,
    orientationGroup: includeMirrors ? "full cubic isometries" : "proper cubic rotations",
    model: "face-to-face lattice tiling",
    shellDefinition: "minimum face-adjacency distance from the root among owners of exposed faces",
    deadFaceRule: "an exposed face below the requested shell depth with no currently legal face-mate is a failed shell obligation and is pruned"
  },
  rows,
  candidates: byCandidate,
  totals: {
    trials: rows.length,
    targetHits: rows.filter(row => row.success).length,
    certifiedNonTilerTrials: rows.filter(row => row.certified && row.canTile === false).length,
    incompleteTrials: rows.filter(row => row.searchIncomplete).length
  },
  interpretation: "Completing a finite shell while avoiding permanently unfillable exposed faces is necessary but not sufficient for an infinite face-to-face tiling. Exhaustion under these exact obligations is a non-tiling certificate; a time or node limit is inconclusive."
};
const serialized = `${JSON.stringify(report, null, 2)}\n`;
if (outputFile) await writeFile(outputFile, serialized);
else process.stdout.write(serialized);
