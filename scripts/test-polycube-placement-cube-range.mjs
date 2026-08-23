#!/usr/bin/env node

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  initialPlacementCubeBranches,
  placementCubeOrdinals,
  placementCubeBootstrapBranch,
  retrySamePlacementCubeLeaf,
  shouldRetryPlacementCubeProcess,
  splitPlacementCubeBranch
} from "./screen-polycube-placement-cube-range.mjs";

assert.deepEqual(placementCubeOrdinals(10, 4, 1), [1, 5, 9]);
assert.deepEqual(
  splitPlacementCubeBranch({ parts: 4, index: 1 }, 10, 8),
  [{ parts: 8, index: 1 }, { parts: 8, index: 5 }]
);
assert.deepEqual(
  splitPlacementCubeBranch({ parts: 8, index: 1 }, 10, 8),
  []
);
assert.deepEqual(
  splitPlacementCubeBranch({ parts: 4, index: 7 }, 10, 8),
  [],
  "a singleton leaf must not be relabeled as a geometric refinement"
);
assert.deepEqual(
  initialPlacementCubeBranches(10, 4, 8, [1, 3]),
  [
    { parts: 4, index: 0 },
    { parts: 8, index: 1 },
    { parts: 8, index: 5 },
    { parts: 4, index: 2 },
    { parts: 8, index: 3 },
    { parts: 8, index: 7 }
  ],
  "known-hard coarse cubes should be replaced by a disjoint one-level refinement"
);
assert.deepEqual(placementCubeBootstrapBranch(4, [0, 2, 3]), { parts: 4, index: 1 });
assert.throws(
  () => placementCubeBootstrapBranch(2, [0, 1]),
  /must leave at least one coarse bootstrap branch/
);
assert.equal(shouldRetryPlacementCubeProcess({
  timedOut: true,
  reportExists: false,
  cacheExists: true,
  cacheMetadataExists: true,
  retries: 0,
  maximumRetries: 1
}), true);
assert.equal(shouldRetryPlacementCubeProcess({
  timedOut: true,
  reportExists: false,
  cacheExists: true,
  cacheMetadataExists: true,
  retries: 1,
  maximumRetries: 1
}), false);
assert.deepEqual(
  retrySamePlacementCubeLeaf({ parts: 64, index: 35 }, 1, 2),
  { parts: 64, index: 35, sameLeafRetry: 1 }
);
assert.deepEqual(
  retrySamePlacementCubeLeaf({ parts: 64, index: 35, sameLeafRetry: 1 }, 1, 2),
  { parts: 64, index: 35, sameLeafRetry: 2 }
);
assert.equal(
  retrySamePlacementCubeLeaf({ parts: 64, index: 35, sameLeafRetry: 2 }, 1, 2),
  null
);
assert.equal(retrySamePlacementCubeLeaf({ parts: 32, index: 3 }, 2, 2), null);
assert.equal(shouldRetryPlacementCubeProcess({
  timedOut: true,
  reportExists: false,
  cacheExists: true,
  cacheMetadataExists: false,
  retries: 0,
  maximumRetries: 1
}), false);

const runner = fileURLToPath(new URL("./screen-polycube-placement-cube-range.mjs", import.meta.url));
const python = process.env.PYTHON ?? "python3";
const directory = mkdtempSync(join(tmpdir(), "polycube-cube-range-test-"));
try {
  const summaryPath = join(directory, "summary.json");
  const commonArguments = [
    runner,
    "--id=p9-42947",
    "--layer=1",
    "--min-count=1",
    "--max-count=1",
    "--anchor-cell=1,1,1",
    "--initial-parts=2",
    "--max-parts=4",
    "--timeout-ms=10000",
    "--process-grace-ms=20000",
    "--random-seed=10",
    `--python=${python}`,
    `--output-dir=${directory}`,
    `--report-output=${summaryPath}`
  ];
  const first = spawnSync(process.execPath, commonArguments, {
    encoding: "utf8",
    timeout: 60_000,
    maxBuffer: 8 * 1024 * 1024
  });
  assert.equal(first.status, 0, first.stderr);
  const firstSummary = JSON.parse(readFileSync(summaryPath, "utf8"));
  assert.equal(firstSummary.classification, "placement_cube_range_exhausted");
  assert.equal(firstSummary.launched_branches, 2);
  assert.equal(firstSummary.resumed_branches, 0);
  assert.equal(firstSummary.maximum_same_leaf_retries, 0);
  assert.equal(firstSummary.same_leaf_retries, 0);
  assert.equal(firstSummary.counts[0].anchor_placement_candidates, 12);
  assert.equal(firstSummary.counts[0].exhausted_branch_reports.length, 2);
  assert.ok(firstSummary.counts[0].certificate);
  assert.match(firstSummary.run_configuration_sha256, /^[0-9a-f]{64}$/);

  const resumed = spawnSync(process.execPath, commonArguments, {
    encoding: "utf8",
    timeout: 30_000,
    maxBuffer: 8 * 1024 * 1024
  });
  assert.equal(resumed.status, 0, resumed.stderr);
  const resumedSummary = JSON.parse(readFileSync(summaryPath, "utf8"));
  assert.equal(resumedSummary.classification, "placement_cube_range_exhausted");
  assert.equal(resumedSummary.launched_branches, 0);
  assert.equal(resumedSummary.resumed_branches, 2);
  assert.match(resumed.stdout, /"resumed":true/);

  const mismatched = spawnSync(process.execPath, commonArguments.map(argument =>
    argument === "--random-seed=10" ? "--random-seed=11" : argument
  ), {
    encoding: "utf8",
    timeout: 30_000,
    maxBuffer: 8 * 1024 * 1024
  });
  assert.notEqual(mismatched.status, 0);
  assert.match(mismatched.stderr, /different placement-cube run configuration/);
  const retryPolicyMismatch = spawnSync(process.execPath, [...commonArguments, "--same-leaf-retries=1"], {
    encoding: "utf8",
    timeout: 30_000,
    maxBuffer: 8 * 1024 * 1024
  });
  assert.notEqual(retryPolicyMismatch.status, 0);
  assert.match(retryPolicyMismatch.stderr, /different placement-cube run configuration/);

  const refinedDirectory = join(directory, "pre-refined");
  const refinedSummaryPath = join(refinedDirectory, "summary.json");
  const refinedArguments = commonArguments.map(argument => {
    if (argument.startsWith("--output-dir=")) return `--output-dir=${refinedDirectory}`;
    if (argument.startsWith("--report-output=")) return `--report-output=${refinedSummaryPath}`;
    return argument;
  });
  refinedArguments.push("--pre-refine-indices=0");
  const refined = spawnSync(process.execPath, refinedArguments, {
    encoding: "utf8",
    timeout: 60_000,
    maxBuffer: 8 * 1024 * 1024
  });
  assert.equal(refined.status, 0, refined.stderr);
  const refinedSummary = JSON.parse(readFileSync(refinedSummaryPath, "utf8"));
  assert.equal(refinedSummary.classification, "placement_cube_range_exhausted");
  assert.equal(refinedSummary.launched_branches, 3);
  assert.deepEqual(refinedSummary.pre_refine_indices, [0]);
  assert.equal(refinedSummary.counts[0].exhausted_branch_reports.length, 3);
  const refinedCertificate = JSON.parse(readFileSync(refinedSummary.counts[0].certificate, "utf8"));
  assert.deepEqual(
    refinedCertificate.leaves.map(leaf => [leaf.parts, leaf.index]),
    [[2, 1], [4, 0], [4, 2]]
  );
  assert.equal(refinedCertificate.covered_anchor_placement_candidates, 12);

  const refinedResume = spawnSync(process.execPath, refinedArguments, {
    encoding: "utf8",
    timeout: 30_000,
    maxBuffer: 8 * 1024 * 1024
  });
  assert.equal(refinedResume.status, 0, refinedResume.stderr);
  const refinedResumeSummary = JSON.parse(readFileSync(refinedSummaryPath, "utf8"));
  assert.equal(refinedResumeSummary.launched_branches, 0);
  assert.equal(refinedResumeSummary.resumed_branches, 3);

  const refinedConfigurationMismatch = spawnSync(
    process.execPath,
    refinedArguments.filter(argument => argument !== "--pre-refine-indices=0"),
    { encoding: "utf8", timeout: 30_000, maxBuffer: 8 * 1024 * 1024 }
  );
  assert.notEqual(refinedConfigurationMismatch.status, 0);
  assert.match(refinedConfigurationMismatch.stderr, /different placement-cube run configuration/);
} finally {
  rmSync(directory, { recursive: true, force: true });
}

process.stdout.write("polycube placement-cube range regressions passed\n");
