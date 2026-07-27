#!/usr/bin/env node

import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const args = new Set(process.argv.slice(2));
const strict = args.has("--strict");
const quick = args.has("--quick");
const requestedModes = process.argv
  .slice(2)
  .filter(arg => arg.startsWith("--mode="))
  .flatMap(arg => arg.slice("--mode=".length).split(","))
  .map(value => value.trim())
  .filter(Boolean);
const timeLimitMs = quick ? 1500 : 5000;
const nodeLimit = quick ? 10000 : 50000;

async function runAttempt(modeKey, strategy, options = {}) {
  const translational = strategy === "translational";
  const boundingBox = !!options.boundingBox;
  const balancedCount = !!options.balancedCount;
  const rootTile = boundingBox
    ? tileSpecs.TILING_REGISTRY[modeKey].build()[0]
    : null;
  const rootOrientation = rootTile?.unique_orientations?.[0];
  const boxSize = rootOrientation
    ? [0, 1, 2].map(axis => {
        const coordinates = rootOrientation.verts.map(vertex => vertex[axis]);
        return Math.max(...coordinates) - Math.min(...coordinates);
      })
    : null;
  const config = {
    mode_key: modeKey,
    criterion: boundingBox ? "region" : translational || balancedCount ? "count" : "layer",
    target_val: translational ? 20 : balancedCount ? 8 : 1,
    target_region: boundingBox ? {
      type: "box",
      center: boxSize.map(value => value / 2),
      size: boxSize
    } : undefined,
    tiling_strategy: strategy,
    include_mirrors: boundingBox,
    move_order: "balanced",
    face_order: "mrv",
    template_preflight: true,
    periodic_patch_max_tiles: 4,
    periodic_template_max_volume: 512,
    branch_cap: 32,
    candidate_cap: 10000,
    node_limit: nodeLimit,
    time_limit_ms: timeLimitMs,
    safety_max_tiles: 300,
    ui_yield_interval_ms: 1000
  };
  const started = performance.now();
  let finished = null;
  let latestSnapshot = null;
  for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
    if (message.type === "full_update") latestSnapshot = message;
    if (message.type === "finished") finished = message;
  }
  return {
    strategy,
    objective: boundingBox
      ? "bounding_box"
      : translational
        ? "periodic_patch"
        : balancedCount
          ? "balanced_count"
          : "layer",
    success: !!finished?.success,
    result_kind: finished?.result_kind ?? "missing_result",
    certified: !!finished?.tiling_evidence?.certified && finished?.can_tile === true,
    ruled_out: finished?.result_kind === "no_tiling" && finished?.can_tile === false,
    evidence: finished?.tiling_evidence?.kind ?? null,
    can_tile: finished?.can_tile ?? null,
    search_incomplete: !!finished?.search_incomplete,
    tiles: finished?.tile_count ?? latestSnapshot?.tile_count ?? 0,
    tile_counts: (latestSnapshot?.tile_counts ?? []).map(item => ({
      name: item.name,
      count: item.count
    })),
    growth_rank: finished?.search_stats?.growth_axis_rank ?? 0,
    growth_isotropy: finished?.search_stats?.growth_isotropy ?? 0,
    milliseconds: Math.round(performance.now() - started)
  };
}

const registryModeKeys = requestedModes.length
  ? requestedModes
  : Object.keys(tileSpecs.TILING_REGISTRY);
for (const modeKey of registryModeKeys) {
  if (!tileSpecs.TILING_REGISTRY[modeKey]) {
    throw new Error(`Unknown catalog mode: ${modeKey}`);
  }
}
const figureBelongsToSystem = (figure, modeKey) =>
  figure.mode_key === modeKey
  || (figure.aliases ?? []).some(alias => alias.startsWith(`${modeKey}::`));
const results = [];
for (const modeKey of registryModeKeys) {
  const attempts = [];
  attempts.push(await runAttempt(modeKey, "translational"));
  if (!attempts.some(attempt => attempt.certified || attempt.ruled_out)) {
    attempts.push(await runAttempt(modeKey, "freestyle", { boundingBox: true }));
  }
  if (!attempts.some(attempt => attempt.certified || attempt.ruled_out || attempt.success)) {
    attempts.push(await runAttempt(modeKey, "isohedral"));
  }
  if (!attempts.some(attempt => attempt.certified || attempt.ruled_out || attempt.success)) {
    attempts.push(await runAttempt(modeKey, "freestyle"));
  }
  if (!attempts.some(attempt => attempt.certified || attempt.ruled_out || attempt.success)) {
    attempts.push(await runAttempt(modeKey, "isohedral", { balancedCount: true }));
  }
  const accepted = attempts.find(attempt => attempt.certified)
    ?? attempts.find(attempt => attempt.ruled_out)
    ?? attempts.find(attempt => attempt.success && attempt.growth_rank === 3)
    ?? null;
  results.push({
    mode_key: modeKey,
    system: tileSpecs.TILING_REGISTRY[modeKey]?.name ?? modeKey,
    figures: tileSpecs.figureCatalog
      .filter(figure => figureBelongsToSystem(figure, modeKey))
      .map(figure => figure.name),
    status: accepted?.certified
      ? "certified"
      : accepted?.ruled_out
        ? "ruled_out"
      : accepted
        ? accepted.objective === "balanced_count" ? "balanced_patch" : "layer_patch"
        : "unresolved",
    selected_strategy: accepted?.strategy ?? null,
    attempts
  });
  process.stdout.write(`${JSON.stringify(results.at(-1))}\n`);
}

const coveredFigureIds = new Set();
for (const result of results) {
  if (result.status === "unresolved") continue;
  for (const figure of tileSpecs.figureCatalog) {
    if (figureBelongsToSystem(figure, result.mode_key)) coveredFigureIds.add(figure.id);
  }
}
const unresolved = results.filter(result => result.status === "unresolved");
const auditedFigures = tileSpecs.figureCatalog.filter(figure =>
  registryModeKeys.some(modeKey => figureBelongsToSystem(figure, modeKey))
);
const uncoveredFigures = auditedFigures
  .filter(figure => !coveredFigureIds.has(figure.id))
  .map(figure => ({ id: figure.id, name: figure.name, mode_key: figure.mode_key }));
const summary = {
  systems: results.length,
  figures: tileSpecs.figureCatalog.length,
  certified_systems: results.filter(result => result.status === "certified").length,
  ruled_out_systems: results.filter(result => result.status === "ruled_out").length,
  layer_patch_systems: results.filter(result => result.status === "layer_patch").length,
  balanced_patch_systems: results.filter(result => result.status === "balanced_patch").length,
  unresolved_systems: unresolved.map(result => result.mode_key),
  uncovered_figures: uncoveredFigures
};
process.stdout.write(`${JSON.stringify({ type: "catalog_summary", ...summary }, null, 2)}\n`);

if (strict && (unresolved.length || uncoveredFigures.length)) process.exitCode = 1;
