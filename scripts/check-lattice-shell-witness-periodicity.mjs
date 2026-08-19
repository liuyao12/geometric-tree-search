#!/usr/bin/env node

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
const witnessFile = args.get("witness-file");
if (!witnessFile) throw new Error("--witness-file=<complete-shell report> is required");
const outputFile = args.get("output-file") ?? null;
const candidatesFile = args.get("candidates-file") ?? null;
const timeMs = Math.max(100, Math.floor(Number(args.get("time-ms")) || 120000));
const certificateTimeMs = Math.max(
  100,
  Math.floor(Number(args.get("certificate-time-ms")) || Math.min(timeMs, 60000))
);
const vectorLimit = Math.max(3, Math.floor(Number(args.get("vector-limit")) || 96));
const requestedId = args.get("id") ?? null;

const witnessReport = JSON.parse(await readFile(witnessFile, "utf8"));
const row = (witnessReport.rows ?? [])
  .filter(entry => Array.isArray(entry.bestShellWitness) && (!requestedId || entry.candidate === requestedId))
  .sort((left, right) =>
    (right.bestShellDepth ?? 0) - (left.bestShellDepth ?? 0)
    || right.bestShellWitness.length - left.bestShellWitness.length
  )[0];
if (!row) throw new Error(`The supplied report contains no serialized shell witness${requestedId ? ` for ${requestedId}` : ""}`);
const candidatesDocument = candidatesFile
  ? JSON.parse(await readFile(candidatesFile, "utf8"))
  : null;
const candidatePool = candidatesDocument
  ? (candidatesDocument.survivors ?? candidatesDocument.candidates ?? candidatesDocument)
  : LATTICE_POLYHEDRON_PRE_SHELL_CANDIDATES;
if (!Array.isArray(candidatePool)) throw new Error("Candidate input must be an array or contain a survivors/candidates array");
const candidate = candidatePool.find(entry => entry.id === row.candidate);
if (!candidate) throw new Error(`Unknown lattice candidate ${row.candidate}`);

const config = {
  mode_key: "cube",
  custom_system: {
    name: `Periodic quotient check ${candidate.id}`,
    figure_refs: [],
    polycubes: [],
    polyhedra: [{ name: `Candidate ${candidate.id}`, vertices: candidate.vertices }],
    polycube_lattice: "z3"
  },
  criterion: "count",
  target_val: row.bestShellWitness.length,
  tiling_strategy: "free_range",
  move_order: "global",
  exhaustive: true,
  agent_exhaustive: true,
  forced_move_layer_lag_cap: 0,
  generic_connected_patch_enumeration: true,
  generic_failure_memo: false,
  generic_periodic_certificate: true,
  generic_periodic_certificate_method: "internal_only",
  generic_periodic_certificate_time_limit_ms: certificateTimeMs,
  generic_periodic_vector_limit: vectorLimit,
  initial_patch: { placements: row.bestShellWitness },
  include_mirrors: false,
  template_preflight: false,
  placement_details: false,
  snapshot_every: 0,
  node_limit: Number.POSITIVE_INFINITY,
  time_limit_ms: timeMs,
  ui_yield_interval_ms: 1000000
};

const started = performance.now();
let final = null;
let check = null;
for await (const message of createTilingStream(config, tileSpecs, { stop: false })) {
  if (message.type === "translational_check") check = message;
  if (message.type === "finished") final = message;
}
if (!final) throw new Error("The periodicity check did not emit a terminal result");

const report = {
  schemaVersion: 1,
  kind: "lattice_shell_witness_periodicity_check",
  generatedAt: new Date().toISOString(),
  candidate: candidate.id,
  sourceWitness: {
    file: witnessFile,
    shellDepth: row.bestShellDepth,
    tiles: row.bestShellWitness.length,
    hash: row.bestShellWitnessHash ?? null
  },
  configuration: { timeMs, certificateTimeMs, vectorLimit, method: "internal_only" },
  result: {
    resultKind: final.result_kind,
    certifiedPeriodic: final.tiling_evidence?.kind === "translational_certificate",
    certificateCompleted: final.search_stats?.generic_periodic_certificate_completed ?? false,
    certificateTimedOut: final.search_stats?.generic_periodic_certificate_timed_out ?? false,
    basesTested: final.search_stats?.generic_periodic_internal_motif_bases_tested ?? 0,
    vectorsConsidered: final.search_stats?.generic_periodic_internal_motif_vector_count ?? 0,
    topTranslations: final.search_stats?.generic_periodic_internal_motif_top_translations ?? [],
    elapsedMs: Math.round(performance.now() - started),
    evidence: final.tiling_evidence ?? null,
    check: check
      ? {
          certified: check.certified,
          checkCompleted: check.check_completed,
          patchSize: check.patch_size,
          patchFingerprint: check.patch_fingerprint ?? null
        }
      : null
  },
  interpretation: "A certificate proves a periodic tiling. A completed negative check excludes this supplied finite patch as the tested quotient source, not every possible periodic motif for the tile."
};
const serialized = `${JSON.stringify(report, null, 2)}\n`;
if (outputFile) await writeFile(outputFile, serialized);
else process.stdout.write(serialized);
