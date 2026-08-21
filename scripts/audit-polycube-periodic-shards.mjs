#!/usr/bin/env node

import { readFileSync } from "node:fs";

const args = new Map();
const positional = [];
for (const argument of process.argv.slice(2)) {
  if (!argument.startsWith("--")) {
    positional.push(argument);
    continue;
  }
  const separator = argument.indexOf("=");
  args.set(
    argument.slice(2, separator < 0 ? undefined : separator),
    separator < 0 ? "true" : argument.slice(separator + 1)
  );
}
const reports = [
  ...positional,
  ...String(args.get("reports") ?? "").split(",").map(value => value.trim()).filter(Boolean)
];
if (!reports.length) throw new Error("Pass periodic shard reports as paths or --reports=a,b");

const integerArg = name => {
  const value = Number(args.get(name));
  if (!Number.isInteger(value) || value < 0) throw new Error(`--${name} must be a nonnegative integer`);
  return value;
};
const expectedStart = integerArg("expected-start");
const expectedEnd = integerArg("expected-end");
if (expectedEnd < expectedStart) throw new Error("--expected-end must be at least --expected-start");

const shards = reports.map(report => {
  const records = readFileSync(report, "utf8").split(/\r?\n/).filter(Boolean).map(line => JSON.parse(line));
  const starts = records.filter(record => record.type === "screen_start");
  const candidates = records.filter(record => record.type === "candidate");
  const summaries = records.filter(record => record.type === "screen_summary");
  if (starts.length !== 1 || candidates.length !== 1 || summaries.length !== 1) {
    throw new Error(`${report} must contain exactly one start, candidate, and summary record`);
  }
  const start = starts[0];
  const candidate = candidates[0];
  const result = candidate.periodic_fast;
  if (!result) throw new Error(`${report} has no periodic_fast result`);
  if (start.periodic_min_tiles !== start.periodic_max_tiles) {
    throw new Error(`${report} is not a single-copy-count HNF shard`);
  }
  if (result.certified || candidate.classification === "periodic") {
    throw new Error(`${report} found a periodic certificate; remove the candidate and verify the witness`);
  }
  if (result.stopped_by != null || result.hnf_range_exhausted !== true) {
    throw new Error(`${report} did not exhaust its requested HNF range`);
  }
  const rangeStart = result.hnf_range_start;
  const rangeEnd = result.hnf_range_end_exclusive;
  if (!Number.isInteger(rangeStart) || !Number.isInteger(rangeEnd) || rangeEnd < rangeStart) {
    throw new Error(`${report} has invalid HNF range metadata`);
  }
  if (start.periodic_hnf_start_index !== rangeStart
    || start.periodic_hnf_end_index !== rangeEnd) {
    throw new Error(`${report} start and result HNF ranges disagree`);
  }
  if (result.hnf_range_total !== rangeEnd - rangeStart
    || result.hnf_visited !== rangeEnd - rangeStart) {
    throw new Error(`${report} HNF visit count does not equal its exhausted interval`);
  }
  return {
    report,
    candidate_id: candidate.id,
    candidate_key: candidate.key,
    copies: start.periodic_min_tiles,
    hnf_start_index: rangeStart,
    hnf_end_index_exclusive: rangeEnd,
    hnf_bases_exhausted: rangeEnd - rangeStart,
    exact_cover_nodes: result.nodes ?? 0,
    milliseconds: result.milliseconds ?? candidate.milliseconds ?? 0
  };
}).sort((left, right) => left.hnf_start_index - right.hnf_start_index);

const identities = new Set(shards.map(shard => `${shard.candidate_id}\n${shard.candidate_key}\n${shard.copies}`));
if (identities.size !== 1) throw new Error("Shard reports do not describe the same candidate and copy count");
let cursor = expectedStart;
for (const shard of shards) {
  if (shard.hnf_start_index !== cursor) {
    const relation = shard.hnf_start_index < cursor ? "overlap" : "gap";
    throw new Error(`HNF ${relation}: expected next index ${cursor}, got ${shard.hnf_start_index}`);
  }
  cursor = shard.hnf_end_index_exclusive;
}
if (cursor !== expectedEnd) throw new Error(`HNF coverage ends at ${cursor}, expected ${expectedEnd}`);

process.stdout.write(`${JSON.stringify({
  schema: "gcts.polycube_periodic_hnf_shard_audit.v1",
  candidate_id: shards[0].candidate_id,
  candidate_key: shards[0].candidate_key,
  copies: shards[0].copies,
  expected_range: [expectedStart, expectedEnd],
  coverage_gap_free: true,
  periodic_certificate: false,
  shards,
  totals: {
    shards: shards.length,
    hnf_bases_exhausted: expectedEnd - expectedStart,
    exact_cover_nodes: shards.reduce((sum, shard) => sum + shard.exact_cover_nodes, 0),
    milliseconds: shards.reduce((sum, shard) => sum + shard.milliseconds, 0)
  }
}, null, 2)}\n`);
