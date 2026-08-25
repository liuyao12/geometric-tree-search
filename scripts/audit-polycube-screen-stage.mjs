#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

import { canonicalPolycubeKey } from "../assets/polycube-enumerator.js";

const args = new Map(process.argv.slice(2).filter(argument => argument.startsWith("--")).map(argument => {
  const separator = argument.indexOf("=");
  return [argument.slice(2, separator < 0 ? undefined : separator),
    separator < 0 ? "true" : argument.slice(separator + 1)];
}));
const inputs = String(args.get("inputs") ?? "").split(",").filter(Boolean);
const outputs = String(args.get("outputs") ?? args.get("output") ?? "").split(",").filter(Boolean);
const inputClassification = args.get("input-classification") ?? "unresolved";
if (!inputs.length || !outputs.length) {
  throw new Error("--inputs=a,b and --output=stage.ndjson (or --outputs=a,b) are required");
}

const parse = path => readFileSync(path, "utf8").split(/\r?\n/).filter(Boolean).map(JSON.parse);
const expected = new Map();
for (const input of inputs) {
  for (const candidate of parse(input).filter(record =>
    record.type === "candidate" && record.classification === inputClassification)) {
    if (expected.has(candidate.id)) throw new Error(`duplicate input candidate ${candidate.id}`);
    expected.set(candidate.id, candidate);
  }
}

const shards = outputs.map(output => {
  const records = parse(output);
  const starts = records.filter(record => record.type === "screen_start");
  const candidates = records.filter(record => record.type === "candidate");
  const summaries = records.filter(record => record.type === "screen_summary");
  if (starts.length !== 1 || summaries.length !== 1) throw new Error(`${output} needs one header and summary`);
  const start = starts[0];
  const summary = summaries[0];
  if (candidates.length !== start.candidates || candidates.length !== summary.candidates) {
    throw new Error(`${output} candidate count disagrees with its header or summary`);
  }
  const shardHash = createHash("sha256");
  for (const candidate of candidates) shardHash.update(`${candidate.id}\0${candidate.key}\n`);
  if (shardHash.digest("hex") !== start.candidate_key_sha256
    || start.candidate_key_sha256 !== summary.candidate_key_sha256) {
    throw new Error(`${output} candidate hash does not replay`);
  }
  return { output, start, summary, candidates };
});
const candidates = shards.flatMap(shard => shard.candidates);
if (candidates.length !== expected.size) {
  throw new Error(`stage has ${candidates.length} candidates; expected ${expected.size}`);
}
const start = shards[0].start;
const seen = new Set();
const hash = createHash("sha256");
const counts = { periodic: 0, non_tiler: 0, isohedral_lead: 0, unresolved: 0 };
for (const candidate of candidates) {
  const prior = expected.get(candidate.id);
  if (!prior || prior.key !== candidate.key || JSON.stringify(prior.voxels) !== JSON.stringify(candidate.voxels)) {
    throw new Error(`${candidate.id} is missing from or disagrees with the input stage`);
  }
  if (seen.has(candidate.id)) throw new Error(`duplicate output candidate ${candidate.id}`);
  seen.add(candidate.id);
  const canonical = canonicalPolycubeKey(candidate.voxels, {
    includeReflections: start.equivalence === "rotations_and_reflections"
  });
  if (canonical !== candidate.key) throw new Error(`${candidate.id} canonical key mismatch`);
  if (!(candidate.classification in counts)) throw new Error(`${candidate.id} unknown classification`);
  counts[candidate.classification] += 1;
  if (candidate.classification === "periodic" && !(
    candidate.easy_witness?.verified === true
      || candidate.periodic?.certificate_verified === true
      || candidate.isohedral?.certificate_verified === true
  )) throw new Error(`${candidate.id} periodic result lacks independent replay`);
  if (candidate.classification === "non_tiler"
    && (candidate.obstruction?.certified !== true || candidate.obstruction?.incomplete)) {
    throw new Error(`${candidate.id} non-tiler result is incomplete`);
  }
  hash.update(`${candidate.id}\0${candidate.key}\n`);
}
const candidateKeySha256 = hash.digest("hex");
for (const key of Object.keys(counts)) {
  const reported = shards.reduce((sum, shard) => sum + shard.summary.counts[key], 0);
  if (counts[key] !== reported) throw new Error(`aggregate ${key} count does not replay`);
}

process.stdout.write(`${JSON.stringify({
  schema: "gcts.z3_polycube_screen_stage_audit.v1",
  input_classification: inputClassification,
  candidates: candidates.length,
  candidate_key_sha256: candidateKeySha256,
  identities_match_input_exactly: true,
  duplicate_ids: 0,
  shards: outputs.length,
  counts,
  protocol: {
    periodic_min_tiles: start.periodic_min_tiles,
    periodic_max_tiles: start.periodic_max_tiles,
    periodic_exact_cover_backend: start.periodic_exact_cover_backend,
    periodic_budget_clock: start.periodic_budget_clock,
    stop_after: start.stop_after
  },
  warning: "Unresolved is a bounded-screen status, not evidence of aperiodicity."
}, null, 2)}\n`);
