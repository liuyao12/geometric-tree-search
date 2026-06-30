#!/usr/bin/env node
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { performance } from "node:perf_hooks";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const usage = () => `Usage:
  node scripts/benchmark-tiler-policies.mjs [options]

Options:
  --figures <id[,id]>             Figure ids/names. Default: cube::0.
  --policies <name[,name]>        Move orders to compare. Default: coverage,isohedral,crystal,balanced.
  --criterion <count|layer>       Goal type. Default: count.
  --target <n>                    Target tile count or layer. Default: 40.
  --polycube-lattice <z3|d3>      Polycube sampling lattice. Default: z3.
  --time-limit-ms <n>             Per-run engine time cap. Default: 5000.
  --node-limit <n>                Per-run node cap; 0 means uncapped. Default: 0.
  --candidate-cap <n>             Candidate cap; 0 means uncapped. Default: 0.
  --output <path>                 Write JSON summary. Default: stdout.
`;

const splitList = (value) => String(value).split(",").map(s => s.trim()).filter(Boolean);
const finitePositive = (value) => Number.isFinite(value) && value > 0 ? value : null;

function readArgs(argv) {
  const opts = {
    figures: ["cube::0"],
    policies: ["coverage", "isohedral", "crystal", "balanced"],
    criterion: "count",
    target: 40,
    polycubeLattice: "z3",
    timeLimitMs: 5000,
    nodeLimit: 0,
    candidateCap: 0,
    output: null
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
    } else if (arg === "--figures" || arg === "--figure") {
      opts.figures = splitList(next(i, arg));
      i += 1;
    } else if (arg === "--policies") {
      opts.policies = splitList(next(i, arg));
      i += 1;
    } else if (arg === "--criterion") {
      opts.criterion = next(i, arg);
      i += 1;
    } else if (arg === "--target") {
      opts.target = Number(next(i, arg));
      i += 1;
    } else if (arg === "--polycube-lattice") {
      const lattice = next(i, arg).toLowerCase();
      if (!["z3", "d3"].includes(lattice)) throw new Error(`${arg} must be z3 or d3`);
      opts.polycubeLattice = lattice;
      i += 1;
    } else if (arg === "--time-limit-ms") {
      opts.timeLimitMs = Number(next(i, arg));
      i += 1;
    } else if (arg === "--node-limit") {
      opts.nodeLimit = Number(next(i, arg));
      i += 1;
    } else if (arg === "--candidate-cap") {
      opts.candidateCap = Number(next(i, arg));
      i += 1;
    } else if (arg === "--output") {
      opts.output = next(i, arg);
      i += 1;
    } else {
      throw new Error(`Unknown option: ${arg}\n\n${usage()}`);
    }
  }
  return opts;
}

function figureAliases(figure) {
  return [figure.id, figure.name, figure.mode_key, `${figure.mode_key}::${figure.tile_index}`]
    .filter(Boolean)
    .map(value => String(value).toLowerCase());
}

function resolveFigures(requested) {
  const byKey = new Map();
  for (const figure of tileSpecs.figureCatalog ?? []) {
    for (const alias of figureAliases(figure)) byKey.set(alias, figure);
  }
  return requested.map(id => {
    const figure = byKey.get(String(id).toLowerCase());
    if (!figure) throw new Error(`Unknown figure: ${id}`);
    return figure;
  });
}

function makeConfig(figures, opts, policy) {
  return {
    mode_key: figures[0]?.mode_key ?? "cube",
    custom_system: {
      name: figures.map(figure => figure.name).join(" + ") || "Policy benchmark system",
      figure_refs: figures.map(figure => figure.id),
      polycubes: [],
      polycube_lattice: opts.polycubeLattice
    },
    polycube_lattice: opts.polycubeLattice,
    criterion: opts.criterion,
    target_val: opts.target,
    exhaustive: false,
    include_mirrors: false,
    snapshot_every: 25,
    move_order: policy,
    face_order: "coverage",
    branch_details: false,
    placement_details: false,
    branch_cap: null,
    node_limit: finitePositive(opts.nodeLimit),
    candidate_cap: finitePositive(opts.candidateCap),
    time_limit_ms: finitePositive(opts.timeLimitMs),
    ui_yield_interval_ms: 24
  };
}

async function runPolicy(figures, opts, policy) {
  const started = performance.now();
  const stopToken = { stop: false };
  const config = makeConfig(figures, opts, policy);
  let final = null;
  let latestSnapshot = null;
  let messages = 0;
  let maxTileCount = 0;
  let maxLayer = 0;
  for await (const message of createTilingStream(config, tileSpecs, stopToken)) {
    messages += 1;
    if (message.type === "full_update" || message.type === "node_snapshot") {
      const snap = message.snapshot ?? message;
      latestSnapshot = snap;
      maxTileCount = Math.max(maxTileCount, snap.tile_count ?? 0);
      maxLayer = Math.max(maxLayer, snap.frontier_stats?.min_gen ?? 0);
    }
    if (message.type === "finished") {
      final = message;
      break;
    }
  }
  return {
    policy,
    elapsed_ms: Math.round(performance.now() - started),
    messages,
    success: !!final?.success,
    best_effort: !!final?.best_effort,
    final_tile_count: final?.tile_count ?? latestSnapshot?.tile_count ?? 0,
    max_tile_count: maxTileCount,
    max_layer: maxLayer,
    final_search_stats: final?.search_stats ?? null,
    latest_frontier_stats: latestSnapshot?.frontier_stats ?? null
  };
}

async function main() {
  const opts = readArgs(process.argv.slice(2));
  if (!["count", "layer"].includes(opts.criterion)) throw new Error("--criterion must be count or layer");
  const allowedPolicies = new Set(["coverage", "repeat", "periodic", "crystal", "isohedral", "symmetric", "layer", "balanced"]);
  for (const policy of opts.policies) if (!allowedPolicies.has(policy)) throw new Error(`Unknown policy/move order: ${policy}`);
  const figures = resolveFigures(opts.figures);
  const results = [];
  for (const policy of opts.policies) results.push(await runPolicy(figures, opts, policy));
  const summary = {
    generated_at: new Date().toISOString(),
    config: opts,
    figures: figures.map(figure => ({ id: figure.id, name: figure.name, category: figure.category ?? [] })),
    results
  };
  const json = JSON.stringify(summary, null, 2);
  if (opts.output) {
    mkdirSync(dirname(resolve(opts.output)), { recursive: true });
    writeFileSync(opts.output, `${json}\n`);
  } else {
    process.stdout.write(`${json}\n`);
  }
}

main().catch(error => {
  console.error(error?.stack || String(error));
  process.exit(1);
});
