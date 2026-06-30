#!/usr/bin/env node

import { createWriteStream, mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { performance } from "node:perf_hooks";

process.stdout.on("error", error => {
  if (error.code === "EPIPE") process.exit(0);
  throw error;
});
process.on("uncaughtException", error => {
  if (error.code === "EPIPE") process.exit(0);
  throw error;
});

const timers = new Map();
const originalConsole = {
  time: console.time.bind(console),
  timeEnd: console.timeEnd.bind(console)
};

function installQuietConsole(verbose) {
  console.time = (label = "default") => {
    if (verbose) timers.set(label, performance.now());
  };
  console.timeEnd = (label = "default") => {
    if (!verbose) return;
    const start = timers.get(label);
    timers.delete(label);
    if (start == null) return originalConsole.timeEnd(label);
    process.stderr.write(`${label}: ${(performance.now() - start).toFixed(3)}ms\n`);
  };
}

function usage() {
  return `Usage:
  node scripts/run-tiler-cli.mjs [options]

Examples:
  node scripts/run-tiler-cli.mjs --figure letter_o::0 --output runs/letter-o-summary.json --trace runs/letter-o-trace.ndjson
  node scripts/run-tiler-cli.mjs --list-figures

Options:
  --figure, --figures <id[,id]>   Figure id/name to use. Repeatable. Default: cube::0.
  --list-figures                  Print available figure ids and exit.
  --criterion <count|layer>       Goal type. Default: count.
  --target <n>                    Target tile count or layer. Default: 80.
  --snapshot-every <n>            Engine snapshot cadence. Default: 10.
  --move-order <name>             coverage, repeat, periodic, crystal, isohedral, symmetric, layer, or balanced. Default: coverage.
  --face-order <name>             Frontier-point order: coverage, constrained, or pocket. Default: coverage.
  --branch-cap <n>                Branch cap; 0 means uncapped. Default: 0.
  --node-limit <n>                Node cap; 0 means uncapped. Default: 0.
  --candidate-cap <n>             Candidate cap; 0 means uncapped. Default: 0.
  --time-limit-ms <n>             Engine time cap; 0 means uncapped. Default: 0.
  --polycube-lattice <z3|d3>      Polycube sampling lattice. D3 adds face-center samples. Default: z3.
  --isohedral-check [n]           Fast single-tile isohedral-style smoke check to corona/layer n. Default: 6.
  --wall-time-ms <n>              Runner wall-clock cap; writes a best-effort summary.
  --include-mirrors               Include mirror tiles.
  --exhaustive                    Continue after the first success.
  --trace <path>                  Write compact NDJSON event trace.
  --branch-details                Include move translations/scores in branch traces.
  --placement-details             Include placement translations in snapshots.
  --output <path>                 Write JSON summary. Default: stdout.
  --full-snapshots                Include face geometry in trace snapshots.
  --sample-limit <n>              Max curve samples in the summary. Default: 2000.
  --verbose                       Show engine timing logs on stderr.
`;
}

function readArgs(argv) {
  const opts = {
    figures: [],
    criterion: "count",
    target: 80,
    snapshotEvery: 10,
    moveOrder: "coverage",
    faceOrder: "coverage",
    branchCap: 0,
    nodeLimit: 0,
    candidateCap: 0,
    timeLimitMs: 0,
    polycubeLattice: "z3",
    isohedralCheck: null,
    wallTimeMs: 0,
    includeMirrors: false,
    exhaustive: false,
    fullSnapshots: false,
    branchDetails: false,
    placementDetails: false,
    sampleLimit: 2000,
    output: null,
    trace: null,
    verbose: false,
    listFigures: false
  };

  const next = (i, name) => {
    if (i + 1 >= argv.length) throw new Error(`${name} needs a value`);
    return argv[i + 1];
  };

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") {
      process.stdout.write(usage());
      process.exit(0);
    } else if (arg === "--list-figures") {
      opts.listFigures = true;
    } else if (arg === "--figure") {
      opts.figures.push(next(i, arg));
      i += 1;
    } else if (arg === "--figures") {
      opts.figures.push(...next(i, arg).split(",").map(s => s.trim()).filter(Boolean));
      i += 1;
    } else if (arg === "--criterion") {
      opts.criterion = next(i, arg);
      i += 1;
    } else if (arg === "--target") {
      opts.target = Number(next(i, arg));
      i += 1;
    } else if (arg === "--snapshot-every") {
      opts.snapshotEvery = Number(next(i, arg));
      i += 1;
    } else if (arg === "--move-order") {
      opts.moveOrder = next(i, arg);
      i += 1;
    } else if (arg === "--face-order") {
      opts.faceOrder = next(i, arg);
      i += 1;
    } else if (arg === "--branch-cap") {
      opts.branchCap = Number(next(i, arg));
      i += 1;
    } else if (arg === "--node-limit") {
      opts.nodeLimit = Number(next(i, arg));
      i += 1;
    } else if (arg === "--candidate-cap") {
      opts.candidateCap = Number(next(i, arg));
      i += 1;
    } else if (arg === "--time-limit-ms") {
      opts.timeLimitMs = Number(next(i, arg));
      i += 1;
    } else if (arg === "--polycube-lattice") {
      const lattice = next(i, arg).toLowerCase();
      if (!["z3", "d3"].includes(lattice)) throw new Error(`${arg} must be z3 or d3`);
      opts.polycubeLattice = lattice;
      i += 1;
    } else if (arg === "--isohedral-check") {
      const maybeValue = argv[i + 1];
      if (maybeValue && !maybeValue.startsWith("--")) {
        opts.isohedralCheck = Number(maybeValue);
        i += 1;
      } else {
        opts.isohedralCheck = 6;
      }
    } else if (arg === "--wall-time-ms") {
      opts.wallTimeMs = Number(next(i, arg));
      i += 1;
    } else if (arg === "--include-mirrors") {
      opts.includeMirrors = true;
    } else if (arg === "--exhaustive") {
      opts.exhaustive = true;
    } else if (arg === "--trace") {
      opts.trace = next(i, arg);
      i += 1;
    } else if (arg === "--branch-details") {
      opts.branchDetails = true;
    } else if (arg === "--placement-details") {
      opts.placementDetails = true;
    } else if (arg === "--output") {
      opts.output = next(i, arg);
      i += 1;
    } else if (arg === "--full-snapshots") {
      opts.fullSnapshots = true;
    } else if (arg === "--sample-limit") {
      opts.sampleLimit = Number(next(i, arg));
      i += 1;
    } else if (arg === "--verbose") {
      opts.verbose = true;
    } else {
      throw new Error(`Unknown option: ${arg}\n\n${usage()}`);
    }
  }
  return opts;
}

function finitePositive(value) {
  return Number.isFinite(value) && value > 0 ? value : null;
}

function ensureParent(path) {
  mkdirSync(dirname(resolve(path)), { recursive: true });
}

function compactSnapshot(message, includeFaces = false) {
  const base = {
    type: message.type,
    node_id: message.node_id ?? null,
    tile_count: message.tile_count ?? 0,
    tile_counts: message.tile_counts ?? [],
    frontier_stats: message.frontier_stats ?? null,
    search_stats: message.search_stats ?? null,
    face_count: message.faces?.length ?? 0,
    placements: message.placements
  };
  if (includeFaces) base.faces = message.faces ?? [];
  return base;
}

function compactEvent(message, includeFaces = false) {
  if (message.type === "full_update") return compactSnapshot(message, includeFaces);
  if (message.type === "node_snapshot") {
    return {
      type: "node_snapshot",
      node_id: message.node_id,
      snapshot: compactSnapshot(message.snapshot, includeFaces)
    };
  }
  if (message.type === "branch_set") {
    return {
      type: "branch_set",
      parent: message.parent ?? null,
      branch_count: message.branches?.length ?? 0,
      branches: (message.branches ?? []).map(branch => ({
        id: branch.id,
        text: branch.text ?? "",
        is_forced: !!branch.is_forced,
        frontier_stats: branch.frontier_stats ?? null,
        prototile_idx: branch.prototile_idx,
        translation: branch.translation,
        coverage: branch.coverage,
        same_root_orientation: branch.same_root_orientation,
        periodic_continuation: branch.periodic_continuation,
        pair_periodic_continuation: branch.pair_periodic_continuation,
        vector_repeat: branch.vector_repeat,
        parallelogram_completion: branch.parallelogram_completion,
        periodic_cell: branch.periodic_cell,
        target_face_pocket: branch.target_face_pocket,
        symmetry: branch.symmetry,
        score: branch.score,
        preview_frontier_stats: branch.preview_frontier_stats
      }))
    };
  }
  return message;
}

function figureAliases(figure) {
  return [
    figure.id,
    figure.name,
    figure.name?.toLowerCase(),
    figure.name?.replace(/\s+/g, "").toLowerCase(),
    ...(figure.aliases ?? [])
  ].filter(Boolean);
}

function resolveFigures(tileSpecs, requested) {
  const byKey = new Map();
  for (const figure of tileSpecs.figureCatalog ?? []) {
    for (const alias of figureAliases(figure)) byKey.set(String(alias).toLowerCase(), figure);
  }
  const ids = requested.length ? requested : ["cube::0"];
  return ids.map(id => {
    const figure = byKey.get(String(id).toLowerCase());
    if (!figure) throw new Error(`Unknown figure: ${id}. Use --list-figures.`);
    return figure;
  });
}

function makeConfig(figures, opts) {
  return {
    mode_key: figures[0]?.mode_key ?? "cube",
    custom_system: {
      name: figures.map(figure => figure.name).join(" + ") || "Headless system",
      figure_refs: figures.map(figure => figure.id),
      polycubes: [],
      polycube_lattice: opts.polycubeLattice
    },
    polycube_lattice: opts.polycubeLattice,
    isohedral_check: opts.isohedralCheck,
    criterion: opts.criterion,
    target_val: opts.target,
    exhaustive: opts.exhaustive,
    include_mirrors: opts.includeMirrors,
    snapshot_every: Number.isFinite(opts.snapshotEvery) ? opts.snapshotEvery : 10,
    move_order: opts.moveOrder,
    face_order: opts.faceOrder,
    branch_details: opts.branchDetails,
    placement_details: opts.placementDetails,
    branch_cap: finitePositive(opts.branchCap),
    node_limit: finitePositive(opts.nodeLimit),
    candidate_cap: finitePositive(opts.candidateCap),
    time_limit_ms: finitePositive(opts.timeLimitMs),
    ui_yield_interval_ms: 24
  };
}

function figureSummary(tileSpecs, figure) {
  const tile = tileSpecs.TILING_REGISTRY?.[figure.mode_key]?.build?.()?.[figure.tile_index];
  return {
    id: figure.id,
    name: figure.name,
    category: figure.category ?? [],
    face_count: tile?.faces?.length ?? null
  };
}

function pushSample(samples, sample, limit) {
  if (samples.length < limit) {
    samples.push(sample);
    return;
  }
  const stride = Math.ceil((samples.length + 1) / limit);
  if (samples.length % stride === 0) samples[Math.floor(samples.length / stride) % limit] = sample;
}

async function main() {
  const opts = readArgs(process.argv.slice(2));
  installQuietConsole(opts.verbose);
  const { createTilingStream, tileSpecs } = await import("../apps/3d-lattice-tiler/engine.js");

  if (opts.listFigures) {
    for (const figure of tileSpecs.figureCatalog ?? []) {
      process.stdout.write(`${figure.id}\t${figure.name}\t${(figure.category ?? []).join(", ")}\n`);
    }
    return;
  }

  if (opts.isohedralCheck != null) {
    if (opts.figures.length > 1) throw new Error("--isohedral-check currently expects a single figure/tile");
    if (!Number.isFinite(opts.isohedralCheck) || opts.isohedralCheck <= 0) throw new Error("--isohedral-check target must be positive");
    opts.criterion = "layer";
    opts.target = opts.isohedralCheck;
    opts.moveOrder = "isohedral";
    if (!opts.branchCap) opts.branchCap = 1;
    if (!opts.candidateCap) opts.candidateCap = 200;
  }

  if (!["count", "layer"].includes(opts.criterion)) throw new Error("--criterion must be count or layer");
  if (!["coverage", "repeat", "periodic", "crystal", "isohedral", "symmetric", "layer", "balanced"].includes(opts.moveOrder)) {
    throw new Error("--move-order must be coverage, repeat, periodic, crystal, isohedral, symmetric, layer, or balanced");
  }
  if (!["coverage", "constrained", "pocket"].includes(opts.faceOrder)) {
    throw new Error("--face-order must be coverage, constrained, or pocket");
  }
  if (!Number.isFinite(opts.target) || opts.target <= 0) throw new Error("--target must be positive");

  const figures = resolveFigures(tileSpecs, opts.figures);
  const config = makeConfig(figures, opts);
  if (opts.trace) ensureParent(opts.trace);
  const traceStream = opts.trace ? createWriteStream(opts.trace) : null;

  const startedAt = performance.now();
  const counters = {
    messages: 0,
    branch_sets: 0,
    branches_created: 0,
    node_snapshots: 0,
    full_updates: 0,
    statuses: {},
    max_tile_count_seen: 0,
    max_frontier_faces_seen: 0,
    max_depth_seen: 0,
    max_progress_total_paths_seen: 0
  };
  const curve = [];
  let finalMessage = null;
  let latestSnapshot = null;
  let bestSnapshot = null;

  const writeTrace = (record) => {
    if (!traceStream) return;
    traceStream.write(`${JSON.stringify(record)}\n`);
  };

  writeTrace({
    type: "run_start",
    at: new Date().toISOString(),
    figures: figures.map(({ id, name }) => ({ id, name })),
    config
  });

  const stopToken = { stop: false };
  let wallTimeExpired = false;
  const wallTimeLimitMs = finitePositive(opts.wallTimeMs);
  const wallTimer = wallTimeLimitMs
    ? setTimeout(() => {
      wallTimeExpired = true;
      stopToken.stop = true;
    }, wallTimeLimitMs)
    : null;
  wallTimer?.unref?.();

  const stream = createTilingStream(config, tileSpecs, stopToken);
  for await (const message of stream) {
    counters.messages += 1;
    writeTrace(compactEvent(message, opts.fullSnapshots));

    if (message.type === "branch_set") {
      counters.branch_sets += 1;
      counters.branches_created += message.branches?.length ?? 0;
    } else if (message.type === "node_status") {
      counters.statuses[message.status] = (counters.statuses[message.status] ?? 0) + 1;
    } else if (message.type === "node_snapshot") {
      counters.node_snapshots += 1;
    } else if (message.type === "full_update") {
      counters.full_updates += 1;
      latestSnapshot = compactSnapshot(message, opts.fullSnapshots);
      if (!bestSnapshot || latestSnapshot.tile_count >= bestSnapshot.tile_count) bestSnapshot = latestSnapshot;
      counters.max_tile_count_seen = Math.max(counters.max_tile_count_seen, latestSnapshot.tile_count);
      counters.max_frontier_faces_seen = Math.max(counters.max_frontier_faces_seen, latestSnapshot.frontier_stats?.total_faces ?? 0);
      counters.max_depth_seen = Math.max(counters.max_depth_seen, latestSnapshot.search_stats?.progress_depth ?? 0);
      counters.max_progress_total_paths_seen = Math.max(counters.max_progress_total_paths_seen, latestSnapshot.search_stats?.progress_total_paths ?? 0);
      pushSample(curve, {
        t_ms: Math.round(performance.now() - startedAt),
        tile_count: latestSnapshot.tile_count,
        frontier_faces: latestSnapshot.frontier_stats?.total_faces ?? 0,
        lowest_layer: latestSnapshot.frontier_stats?.min_gen ?? 0,
        lowest_layer_faces: latestSnapshot.frontier_stats?.count ?? 0,
        forced_on_path: latestSnapshot.search_stats?.forced_on_path ?? 0,
        backtracks: latestSnapshot.search_stats?.backtracks ?? 0,
        progress_percent: latestSnapshot.search_stats?.visited_percent ?? 0,
        progress_paths: latestSnapshot.search_stats?.progress_total_paths ?? 0
      }, opts.sampleLimit);
    } else if (message.type === "finished") {
      finalMessage = message;
    }
  }
  if (wallTimer) clearTimeout(wallTimer);

  if (traceStream) {
    writeTrace({ type: "run_end", at: new Date().toISOString(), final: finalMessage });
    await new Promise(resolve => traceStream.end(resolve));
  }

  const elapsedMs = Math.round(performance.now() - startedAt);
  const summary = {
    version: 1,
    generated_at: new Date().toISOString(),
    elapsed_ms: elapsedMs,
    figures: figures.map(figure => figureSummary(tileSpecs, figure)),
    config,
    wall_time_limit_ms: wallTimeLimitMs,
    wall_time_expired: wallTimeExpired,
    final: finalMessage,
    counters,
    latest_snapshot: latestSnapshot,
    best_snapshot: bestSnapshot,
    curve,
    trace: opts.trace ?? null
  };

  const json = `${JSON.stringify(summary, null, 2)}\n`;
  if (opts.output) {
    ensureParent(opts.output);
    writeFileSync(opts.output, json);
  } else {
    process.stdout.write(json);
  }
}

main().catch(error => {
  process.stderr.write(`${error.stack ?? error.message}\n`);
  process.exitCode = 1;
});
