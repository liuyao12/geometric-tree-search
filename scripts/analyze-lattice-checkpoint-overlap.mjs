#!/usr/bin/env node

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";

const args = new Map(process.argv.slice(2).map(argument => {
  const separator = argument.indexOf("=");
  return separator < 0
    ? [argument.replace(/^--/, ""), "true"]
    : [argument.slice(2, separator), argument.slice(separator + 1)];
}));
const inputFile = args.get("input");
const outputFile = args.get("output");
assert.ok(inputFile, "--input=<benchmark-report.json> is required");

const report = JSON.parse(await readFile(inputFile, "utf8"));
const rows = report.rows.filter(row => row.lane === "free_range_unbanded");
assert.ok(rows.length, "the benchmark report has no free_range_unbanded rows");

const digest = values => createHash("sha256").update(values.slice().sort().join("\n")).digest("hex");
const intersection = (left, right) => new Set([...left].filter(value => right.has(value)));
const candidateIds = [...new Set(rows.map(row => row.case))];
const candidates = candidateIds.map(id => {
  const candidateRows = rows.filter(row => row.case === id).sort((a, b) => a.seed - b.seed);
  const pathSets = new Map();
  const paths = candidateRows.map(row => {
    const fingerprints = row.genericPeriodicCertificateCheckFingerprints ?? [];
    assert.equal(
      fingerprints.length,
      row.genericPeriodicCertificateChecksAttempted,
      `${id} seed ${row.seed}: fingerprint count must equal exact checks attempted`
    );
    assert.equal(
      row.genericPeriodicCertificateChecksCompleted + row.genericPeriodicCertificateChecksTimedOut,
      row.genericPeriodicCertificateChecksAttempted,
      `${id} seed ${row.seed}: every exact check must complete or time out explicitly`
    );
    assert.ok(
      fingerprints.every(value => /^[0-9a-f]{32}$/.test(value)),
      `${id} seed ${row.seed}: every checkpoint must have a 128-bit lowercase-hex fingerprint`
    );
    const unique = new Set(fingerprints);
    assert.equal(
      unique.size,
      fingerprints.length,
      `${id} seed ${row.seed}: a path must not check the same geometric patch twice`
    );
    pathSets.set(row.seed, unique);
    return {
      seed: row.seed,
      witness_hash: row.witnessHash,
      checks_attempted: row.genericPeriodicCertificateChecksAttempted,
      checks_completed: row.genericPeriodicCertificateChecksCompleted,
      checks_timed_out: row.genericPeriodicCertificateChecksTimedOut,
      certificate_found: row.genericPeriodicCertificateFound,
      fingerprint_digest_sha256: digest(fingerprints),
      fingerprints
    };
  });
  const membership = new Map();
  for (const [seed, fingerprints] of pathSets) {
    for (const fingerprint of fingerprints) {
      if (!membership.has(fingerprint)) membership.set(fingerprint, new Set());
      membership.get(fingerprint).add(seed);
    }
  }
  const membershipHistogram = {};
  for (const seeds of membership.values()) {
    membershipHistogram[seeds.size] = (membershipHistogram[seeds.size] ?? 0) + 1;
  }
  const pairwiseIntersections = [];
  for (let leftIndex = 0; leftIndex < paths.length; leftIndex++) {
    for (let rightIndex = leftIndex + 1; rightIndex < paths.length; rightIndex++) {
      const left = paths[leftIndex];
      const right = paths[rightIndex];
      const shared = intersection(pathSets.get(left.seed), pathSets.get(right.seed)).size;
      const union = pathSets.get(left.seed).size + pathSets.get(right.seed).size - shared;
      pairwiseIntersections.push({
        seeds: [left.seed, right.seed],
        shared_fingerprints: shared,
        union_fingerprints: union,
        jaccard: union ? shared / union : 0
      });
    }
  }
  const statePathPairs = paths.reduce((sum, path) => sum + path.checks_attempted, 0);
  const unionFingerprints = [...membership.keys()].sort();
  return {
    id,
    path_count: paths.length,
    state_path_pairs: statePathPairs,
    globally_distinct_fingerprints: unionFingerprints.length,
    repeated_state_path_pairs: statePathPairs - unionFingerprints.length,
    union_digest_sha256: digest(unionFingerprints),
    path_membership_histogram: Object.fromEntries(
      Object.entries(membershipHistogram).sort(([left], [right]) => Number(left) - Number(right))
    ),
    pairwise_intersections: pairwiseIntersections,
    paths
  };
});

const result = {
  schema_version: 1,
  screen_date: args.get("screen-date") ?? new Date().toISOString().slice(0, 10),
  engine_commit: args.get("engine-commit") ?? null,
  source_benchmark_schema_version: report.schemaVersion,
  fingerprint: {
    canonical_state: "sorted placed-tile geometry in the fixed seeded-run root frame",
    algorithm: "FNV-1a-128",
    encoding: "32 lowercase hexadecimal characters",
    interpretation: "collision-resistant accounting key, not a formal injective identifier"
  },
  protocol: report.configuration,
  candidates,
  summary: {
    candidates: candidates.length,
    paths: candidates.reduce((sum, candidate) => sum + candidate.path_count, 0),
    state_path_pairs: candidates.reduce((sum, candidate) => sum + candidate.state_path_pairs, 0),
    globally_distinct_candidate_states: candidates.reduce(
      (sum, candidate) => sum + candidate.globally_distinct_fingerprints,
      0
    ),
    repeated_state_path_pairs: candidates.reduce(
      (sum, candidate) => sum + candidate.repeated_state_path_pairs,
      0
    ),
    globally_distinct_digest_sha256: digest(candidates.flatMap(candidate => [...new Set(
      candidate.paths.flatMap(path => path.fingerprints)
    )].map(fingerprint => `${candidate.id}:${fingerprint}`)))
  }
};

const serialized = `${JSON.stringify(result, null, 2)}\n`;
if (outputFile) await writeFile(outputFile, serialized);
else process.stdout.write(serialized);
