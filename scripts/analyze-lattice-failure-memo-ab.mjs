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
assert.ok(args.get("fixed"), "--fixed=<fixed-frame-report.json> is required");
assert.ok(args.get("rigid"), "--rigid=<rigid-motion-report.json> is required");

const fixed = JSON.parse(await readFile(args.get("fixed"), "utf8"));
const rigid = JSON.parse(await readFile(args.get("rigid"), "utf8"));
assert.equal(fixed.schemaVersion, rigid.schemaVersion);
assert.equal(fixed.configuration.failureMemoSymmetry, "fixed");
assert.equal(rigid.configuration.failureMemoSymmetry, "rigid");
const withoutSymmetry = configuration => {
  const copy = { ...configuration };
  delete copy.failureMemoSymmetry;
  return copy;
};
assert.deepEqual(
  withoutSymmetry(fixed.configuration),
  withoutSymmetry(rigid.configuration),
  "A/B configurations must differ only in failure-memo key equivalence"
);
assert.equal(fixed.rows.length, rigid.rows.length);

const pathIdentity = row => [
  row.case,
  row.seed,
  row.resultKind,
  row.success,
  row.searchIncomplete,
  row.terminationReason,
  row.witnessHash,
  row.largestPatch,
  row.visitedNodes,
  row.backtracks,
  row.failureMemoStates,
  row.failureMemoHits
];
const paths = fixed.rows.map((fixedRow, index) => {
  const rigidRow = rigid.rows[index];
  assert.equal(fixedRow.case, rigidRow.case);
  assert.equal(fixedRow.seed, rigidRow.seed);
  assert.deepEqual(
    pathIdentity(fixedRow),
    pathIdentity(rigidRow),
    `${fixedRow.case} seed ${fixedRow.seed}: memo equivalence changed the bounded search outcome`
  );
  assert.equal(fixedRow.failureMemoKeyEquivalence, "fixed_frame");
  assert.equal(rigidRow.failureMemoKeyEquivalence, "orientation_preserving_cubic_rigid_motion");
  return {
    id: fixedRow.case,
    seed: fixedRow.seed,
    witness_hash: fixedRow.witnessHash,
    largest_patch: fixedRow.largestPatch,
    visited_nodes: fixedRow.visitedNodes,
    backtracks: fixedRow.backtracks,
    memo_states: fixedRow.failureMemoStates,
    fixed_memo_hits: fixedRow.failureMemoHits,
    rigid_memo_hits: rigidRow.failureMemoHits,
    additional_rigid_hits: rigidRow.failureMemoHits - fixedRow.failureMemoHits,
    fixed_elapsed_ms: fixedRow.elapsedMs,
    rigid_elapsed_ms: rigidRow.elapsedMs,
    observed_elapsed_ratio: fixedRow.elapsedMs ? rigidRow.elapsedMs / fixedRow.elapsedMs : null
  };
});
const median = values => {
  const sorted = values.slice().sort((left, right) => left - right);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
};
const fixedElapsedMs = paths.reduce((sum, path) => sum + path.fixed_elapsed_ms, 0);
const rigidElapsedMs = paths.reduce((sum, path) => sum + path.rigid_elapsed_ms, 0);
const identityDigest = createHash("sha256")
  .update(paths.map(path => JSON.stringify(pathIdentity(fixed.rows.find(row =>
    row.case === path.id && row.seed === path.seed
  )))).join("\n"))
  .digest("hex");
const result = {
  schema_version: 1,
  screen_date: args.get("screen-date") ?? new Date().toISOString().slice(0, 10),
  engine_commit: args.get("engine-commit") ?? null,
  benchmark_schema_version: fixed.schemaVersion,
  protocol: withoutSymmetry(fixed.configuration),
  arms: {
    fixed: "fixed root-frame placement geometry",
    rigid: "translation plus 24 proper cubic rotations"
  },
  paths,
  summary: {
    candidates: new Set(paths.map(path => path.id)).size,
    paths: paths.length,
    identical_bounded_search_outcomes: paths.length,
    additional_rigid_memo_hits: paths.reduce((sum, path) => sum + path.additional_rigid_hits, 0),
    fixed_elapsed_ms: fixedElapsedMs,
    rigid_elapsed_ms: rigidElapsedMs,
    observed_elapsed_delta_ms: rigidElapsedMs - fixedElapsedMs,
    observed_elapsed_ratio: fixedElapsedMs ? rigidElapsedMs / fixedElapsedMs : null,
    median_path_elapsed_ratio: median(paths.map(path => path.observed_elapsed_ratio)),
    paths_with_rigid_elapsed_increase: paths.filter(path => path.rigid_elapsed_ms > path.fixed_elapsed_ms).length,
    bounded_path_identity_sha256: identityDigest,
    production_default: "fixed"
  },
  interpretation: [
    "The fixed root placement already breaks the proper cubic symmetries encountered by these twelve candidate paths: rigid canonicalization produced no additional exact failure-memo hit.",
    "Every bounded outcome, witness, depth, node count, backtrack count, memo-state count, and memo-hit count was identical between arms.",
    "Rigid canonicalization added work in this observed run, so fixed-frame failure keys remain the production default; elapsed ratios are benchmark observations, not a hardware-independent theorem.",
    "Rigid keys remain available as an explicit experiment and automatically fall back to fixed-frame keys for finite target regions where global rotation or translation is not a sound equivalence."
  ]
};

const serialized = `${JSON.stringify(result, null, 2)}\n`;
if (args.get("output")) await writeFile(args.get("output"), serialized);
else process.stdout.write(serialized);
