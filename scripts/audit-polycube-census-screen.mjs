#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

import { canonicalPolycubeKey } from "../assets/polycube-enumerator.js";

const args = new Map();
const reports = [];
for (const argument of process.argv.slice(2)) {
  if (!argument.startsWith("--")) {
    reports.push(argument);
    continue;
  }
  const separator = argument.indexOf("=");
  args.set(argument.slice(2, separator < 0 ? undefined : separator),
    separator < 0 ? "true" : argument.slice(separator + 1));
}
if (!reports.length) throw new Error("Pass one or more outer-census shard reports");
const expectedCandidates = Number(args.get("expected-candidates"));
if (!Number.isInteger(expectedCandidates) || expectedCandidates < 1) {
  throw new Error("--expected-candidates must be a positive integer");
}
const expectedHash = args.get("expected-key-sha256") ?? null;

const shards = reports.map(path => {
  const records = readFileSync(path, "utf8").split(/\r?\n/).filter(Boolean).map(JSON.parse);
  const starts = records.filter(record => record.type === "screen_start");
  const candidates = records.filter(record => record.type === "candidate");
  const summaries = records.filter(record => record.type === "screen_summary");
  if (starts.length !== 1 || summaries.length !== 1) {
    throw new Error(`${path} must contain exactly one start and one summary`);
  }
  const start = starts[0];
  const summary = summaries[0];
  if (candidates.length !== start.candidates || candidates.length !== summary.candidates) {
    throw new Error(`${path} candidate record count disagrees with its header or summary`);
  }
  if (!Number.isInteger(start.candidate_range_start)
    || !Number.isInteger(start.candidate_range_end_exclusive)
    || start.candidate_range_end_exclusive - start.candidate_range_start !== candidates.length) {
    throw new Error(`${path} has invalid outer candidate range metadata`);
  }
  if (summary.candidate_range_start !== start.candidate_range_start
    || summary.candidate_range_end_exclusive !== start.candidate_range_end_exclusive
    || summary.candidate_key_sha256 !== start.candidate_key_sha256) {
    throw new Error(`${path} header and summary metadata disagree`);
  }
  const hash = createHash("sha256");
  const counts = { periodic: 0, non_tiler: 0, isohedral_lead: 0, unresolved: 0 };
  for (let localIndex = 0; localIndex < candidates.length; localIndex += 1) {
    const candidate = candidates[localIndex];
    const expectedIndex = start.candidate_range_start + localIndex;
    if (candidate.global_index !== expectedIndex || candidate.index !== localIndex + 1) {
      throw new Error(`${path} has a missing, duplicate, or reordered candidate at ${expectedIndex}`);
    }
    const canonical = canonicalPolycubeKey(candidate.voxels, {
      includeReflections: start.equivalence === "rotations_and_reflections"
    });
    if (canonical !== candidate.key) throw new Error(`${candidate.id} has a noncanonical or corrupt key`);
    if (!(candidate.classification in counts)) throw new Error(`${candidate.id} has unknown classification`);
    counts[candidate.classification] += 1;
    if (candidate.classification === "periodic") {
      const independentlyVerified = candidate.easy_witness?.verified === true
        || candidate.periodic?.certificate_verified === true
        || candidate.isohedral?.certificate_verified === true;
      if (!independentlyVerified) throw new Error(`${candidate.id} has an unverified periodic classification`);
    }
    if (candidate.classification === "non_tiler"
      && (candidate.obstruction?.certified !== true || candidate.obstruction?.incomplete)) {
      throw new Error(`${candidate.id} has an incomplete non-tiler classification`);
    }
    hash.update(`${candidate.id}\0${candidate.key}\n`);
  }
  if (JSON.stringify(counts) !== JSON.stringify(summary.counts)) {
    throw new Error(`${path} classification counts do not replay`);
  }
  if (hash.digest("hex") !== start.candidate_key_sha256) {
    throw new Error(`${path} candidate hash does not replay`);
  }
  return { path, start, summary, candidates };
}).sort((left, right) => left.start.candidate_range_start - right.start.candidate_range_start);

const protocolFields = [
  "size", "source_candidates", "equivalence", "periodic_min_tiles", "periodic_max_tiles",
  "periodic_screen", "periodic_exact_cover_backend", "periodic_linear_prefilter",
  "periodic_budget_clock", "box_screen", "general_periodic", "isohedral_screen",
  "engine_budget_clock", "obstruction_layer", "obstruction_budget_clock", "stop_after"
];
for (const field of protocolFields) {
  if (new Set(shards.map(shard => JSON.stringify(shard.start[field]))).size !== 1) {
    throw new Error(`mixed shard protocol field: ${field}`);
  }
}

let cursor = 0;
const ids = new Set();
const aggregateHash = createHash("sha256");
const aggregateCounts = { periodic: 0, non_tiler: 0, isohedral_lead: 0, unresolved: 0 };
for (const shard of shards) {
  if (shard.start.candidate_range_start !== cursor) {
    throw new Error(`outer candidate range gap/overlap: expected ${cursor}, got ${shard.start.candidate_range_start}`);
  }
  for (const candidate of shard.candidates) {
    if (ids.has(candidate.id)) throw new Error(`duplicate candidate ID ${candidate.id}`);
    ids.add(candidate.id);
    aggregateHash.update(`${candidate.id}\0${candidate.key}\n`);
  }
  for (const key of Object.keys(aggregateCounts)) aggregateCounts[key] += shard.summary.counts[key];
  cursor = shard.start.candidate_range_end_exclusive;
}
if (cursor !== expectedCandidates || ids.size !== expectedCandidates) {
  throw new Error(`outer coverage ends at ${cursor} with ${ids.size} IDs; expected ${expectedCandidates}`);
}
const candidateKeySha256 = aggregateHash.digest("hex");
if (expectedHash && candidateKeySha256 !== expectedHash) {
  throw new Error(`aggregate key hash ${candidateKeySha256} does not match manifest ${expectedHash}`);
}

process.stdout.write(`${JSON.stringify({
  schema: "gcts.z3_polycube_screen_audit.v1",
  model: shards[0].start.equivalence,
  size: shards[0].start.size,
  candidates: expectedCandidates,
  candidate_key_sha256: candidateKeySha256,
  candidate_coverage_gap_free: true,
  duplicate_ids: 0,
  protocol_consistent: true,
  counts: aggregateCounts,
  shards: shards.map(shard => ({
    path: shard.path,
    range: [shard.start.candidate_range_start, shard.start.candidate_range_end_exclusive],
    candidate_key_sha256: shard.start.candidate_key_sha256
  })),
  warning: "Unresolved is a bounded-screen status, not evidence of aperiodicity."
}, null, 2)}\n`);
