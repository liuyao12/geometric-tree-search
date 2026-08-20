#!/usr/bin/env node

import { readFile, writeFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";
import { createTilingStream, tileSpecs } from "../apps/3d-lattice-tiler/engine.js";
import { LATTICE_POLYHEDRON_GCTS_EXAMPLES } from "../assets/lattice-polyhedron-survivors.js";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const candidatesFile = args.get("candidates-file");
const candidateId = args.get("id");
if (!candidateId) {
  throw new Error("Usage: --id=SIZE_INDEX [--candidates-file=report.json] [--output-file=receipt.json]");
}
const numberArg = (name, fallback) => {
  const value = Number(args.get(name));
  return Number.isFinite(value) ? value : fallback;
};
const document = candidatesFile ? JSON.parse(await readFile(candidatesFile, "utf8")) : null;
const pool = document
  ? document.survivors ?? document.candidates ?? document.rows ?? document
  : LATTICE_POLYHEDRON_GCTS_EXAMPLES;
if (!Array.isArray(pool)) throw new Error("Candidate input must be an array or contain candidates/survivors/rows");
const candidate = pool.find(entry => (entry.id ?? entry.candidate) === candidateId);
if (!candidate?.vertices) throw new Error(`Candidate ${candidateId} with vertices was not found`);

const includeMirrors = args.get("include-mirrors") === "true";
const maximumMotifTiles = Math.max(1, Math.floor(numberArg("periodic-max", 8)));
const timeLimitMs = Math.max(50, Math.floor(numberArg("time-ms", 30000)));
const nodeLimit = Math.max(1, Math.floor(numberArg("node-limit", 500000)));
const config = {
  mode_key: "cube",
  custom_system: {
    name: `Periodic screen ${candidateId}`,
    figure_refs: [],
    polycubes: [],
    polyhedra: [{ name: `Candidate ${candidateId}`, vertices: candidate.vertices }],
    polycube_lattice: "z3"
  },
  criterion: "count",
  target_val: Math.max(24, maximumMotifTiles),
  tiling_strategy: "translational",
  include_mirrors: includeMirrors,
  periodic_patch_max_tiles: maximumMotifTiles,
  template_preflight: true,
  snapshot_every: 0,
  placement_details: true,
  branch_cap: null,
  candidate_cap: null,
  node_limit: nodeLimit,
  time_limit_ms: timeLimitMs,
  ui_yield_interval_ms: 1000000
};

const started = performance.now();
const checks = [];
let final = null;
for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
  if (message.type === "translational_check") {
    checks.push({
      patchSize: message.patch_size,
      certified: !!message.certified,
      periodicTemplate: message.periodic_template ?? null,
      rejection: message.search_stats?.periodic_certificate_last_rejection ?? null,
      neighborhoodRejection: message.search_stats?.periodic_neighborhood_last_rejection ?? null
    });
  }
  if (message.type === "finished") final = message;
}
if (!final) throw new Error("Periodic screen emitted no terminal result");

const receipt = {
  schemaVersion: 1,
  kind: "lattice_polyhedron_periodic_certificate_screen",
  generatedAt: new Date().toISOString(),
  source: candidatesFile ?? "assets/lattice-polyhedron-survivors.js",
  candidate: { id: candidateId, vertices: candidate.vertices },
  configuration: {
    orientationGroup: includeMirrors ? "full cubic isometries" : "proper cubic lattice orientations",
    maximumMotifTiles,
    timeLimitMs,
    nodeLimit,
    overlapValidation: "complete neighboring-cell convex separating-axis audit"
  },
  checks,
  result: {
    resultKind: final.result_kind,
    success: !!final.success,
    canTile: final.can_tile ?? null,
    searchIncomplete: !!final.search_incomplete,
    evidence: final.tiling_evidence ?? null,
    elapsedMs: Math.round(performance.now() - started),
    visitedNodes: final.search_stats?.visited_nodes ?? 0,
    periodicMotifNodes: final.search_stats?.periodic_motif_nodes ?? 0,
    periodicMotifStates: final.search_stats?.periodic_motif_states ?? 0
  }
};

const serialized = `${JSON.stringify(receipt, null, 2)}\n`;
const outputFile = args.get("output-file");
if (outputFile) await writeFile(outputFile, serialized);
process.stdout.write(serialized);
