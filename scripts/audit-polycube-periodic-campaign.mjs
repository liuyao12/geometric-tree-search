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
if (!positional.length) throw new Error("Pass one final per-candidate audit.json path per candidate");
const integerArg = name => {
  const value = Number(args.get(name));
  if (!Number.isInteger(value) || value < 0) throw new Error(`--${name} must be a nonnegative integer`);
  return value;
};
const expectedCopies = integerArg("expected-copies");
const expectedStart = integerArg("expected-start");
const expectedEnd = integerArg("expected-end");
const expectedCandidates = String(args.get("expected-candidates") ?? "")
  .split(",")
  .map(value => value.trim())
  .filter(Boolean)
  .sort();
if (!expectedCandidates.length) throw new Error("--expected-candidates=id1,id2,... is required");

const candidates = positional.map(argument => {
  const labelSeparator = argument.indexOf("=");
  const declaredId = labelSeparator > 0 ? argument.slice(0, labelSeparator) : null;
  const path = labelSeparator > 0 ? argument.slice(labelSeparator + 1) : argument;
  const audit = JSON.parse(readFileSync(path, "utf8"));
  if (audit.schema !== "gcts.polycube_periodic_hnf_shard_audit.v1") {
    throw new Error(`${path} is not a final HNF shard audit`);
  }
  if (!audit.coverage_gap_free || audit.periodic_certificate !== false) {
    throw new Error(`${path} does not certify gap-free negative HNF coverage`);
  }
  if (audit.copies !== expectedCopies) {
    throw new Error(`${path} has copy count ${audit.copies}, expected ${expectedCopies}`);
  }
  if (audit.expected_range?.[0] !== expectedStart || audit.expected_range?.[1] !== expectedEnd) {
    throw new Error(`${path} covers ${JSON.stringify(audit.expected_range)}, expected [${expectedStart},${expectedEnd}]`);
  }
  if (audit.totals?.hnf_bases_exhausted !== expectedEnd - expectedStart) {
    throw new Error(`${path} has an inconsistent exhausted HNF total`);
  }
  return {
    id: declaredId ?? audit.candidate_id,
    source_candidate_id: audit.candidate_id,
    key: audit.candidate_key,
    audit: path,
    shards: audit.totals.shards,
    hnf_bases_exhausted: audit.totals.hnf_bases_exhausted,
    exact_cover_nodes: audit.totals.exact_cover_nodes,
    milliseconds: audit.totals.milliseconds
  };
}).sort((left, right) => left.id.localeCompare(right.id));

const actualCandidates = candidates.map(candidate => candidate.id);
if (new Set(actualCandidates).size !== actualCandidates.length) {
  throw new Error("Campaign contains a duplicate candidate audit");
}
if (JSON.stringify(actualCandidates) !== JSON.stringify(expectedCandidates)) {
  throw new Error(`Campaign candidates ${actualCandidates.join(",")} do not match expected ${expectedCandidates.join(",")}`);
}

process.stdout.write(`${JSON.stringify({
  schema: "gcts.polycube_periodic_hnf_campaign_audit.v1",
  copies: expectedCopies,
  expected_range_per_candidate: [expectedStart, expectedEnd],
  candidates,
  coverage_gap_free: true,
  periodic_certificates: 0,
  totals: {
    candidates: candidates.length,
    shards: candidates.reduce((sum, candidate) => sum + candidate.shards, 0),
    hnf_bases_exhausted: candidates.reduce((sum, candidate) => sum + candidate.hnf_bases_exhausted, 0),
    exact_cover_nodes: candidates.reduce((sum, candidate) => sum + candidate.exact_cover_nodes, 0),
    milliseconds: candidates.reduce((sum, candidate) => sum + candidate.milliseconds, 0)
  }
}, null, 2)}\n`);
