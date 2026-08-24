#!/usr/bin/env node

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import { enumeratePolycubeCoronaPlacements } from "../assets/polycube-corona-search.js";
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
const cegarRunner = fileURLToPath(new URL("./screen-polycube-placement-cube-cegar.mjs", import.meta.url));
const python = process.env.PYTHON ?? "python3";
const directory = mkdtempSync(join(tmpdir(), "polycube-cube-range-test-"));
try {
  const summaryPath = join(directory, "summary.json");
  const sharedCacheDirectory = join(directory, "shared-cache");
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
    `--formula-cache-dir=${sharedCacheDirectory}`,
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
  assert.equal(
    JSON.parse(readFileSync(firstSummary.run_configuration, "utf8")).formula_cache_directory,
    sharedCacheDirectory
  );
  assert.equal(
    JSON.parse(readFileSync(firstSummary.counts[0].exhausted_branch_reports[0], "utf8")).formula_cache,
    join(sharedCacheDirectory, "exact-1-base.smt2")
  );

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

  const requiredPlacementPath = join(directory, "required-placement.json");
  const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === "p9-42947");
  writeFileSync(requiredPlacementPath, `${JSON.stringify({
    placement_keys: [enumeratePolycubeCoronaPlacements(candidate.voxels, 1)[0].key]
  })}\n`);
  const requiredDirectory = join(directory, "required-placement-range");
  const requiredSummaryPath = join(requiredDirectory, "summary.json");
  const requiredArguments = commonArguments.map(argument => {
    if (argument.startsWith("--output-dir=")) return `--output-dir=${requiredDirectory}`;
    if (argument.startsWith("--report-output=")) return `--report-output=${requiredSummaryPath}`;
    return argument;
  });
  requiredArguments.push(`--required-placement-report=${requiredPlacementPath}`);
  const required = spawnSync(process.execPath, requiredArguments, {
    encoding: "utf8",
    timeout: 60_000,
    maxBuffer: 8 * 1024 * 1024
  });
  assert.equal(required.status, 0, required.stderr);
  const requiredSummary = JSON.parse(readFileSync(requiredSummaryPath, "utf8"));
  assert.equal(requiredSummary.classification, "placement_cube_range_exhausted");
  assert.equal(
    JSON.parse(readFileSync(requiredSummary.run_configuration, "utf8")).required_placement_report,
    requiredPlacementPath
  );
  assert.equal(
    JSON.parse(readFileSync(requiredSummary.counts[0].exhausted_branch_reports[0], "utf8")).required_placements,
    1
  );

  const refinedConfigurationMismatch = spawnSync(
    process.execPath,
    refinedArguments.filter(argument => argument !== "--pre-refine-indices=0"),
    { encoding: "utf8", timeout: 30_000, maxBuffer: 8 * 1024 * 1024 }
  );
  assert.notEqual(refinedConfigurationMismatch.status, 0);
  assert.match(refinedConfigurationMismatch.stderr, /different placement-cube run configuration/);

  const cegarDirectory = join(directory, "cegar");
  const cegarSummaryPath = join(cegarDirectory, "summary.json");
  const cegarArguments = commonArguments.slice(1).map(argument => {
    if (argument.startsWith("--output-dir=")) return `--output-dir=${cegarDirectory}`;
    if (argument.startsWith("--report-output=")) return `--report-output=${cegarSummaryPath}`;
    return argument;
  });
  const cegar = spawnSync(process.execPath, [cegarRunner, ...cegarArguments, "--cegar-rounds=2"], {
    encoding: "utf8",
    timeout: 60_000,
    maxBuffer: 8 * 1024 * 1024
  });
  assert.equal(cegar.status, 0, cegar.stderr);
  const cegarSummary = JSON.parse(readFileSync(cegarSummaryPath, "utf8"));
  assert.equal(cegarSummary.classification, "placement_cube_range_exhausted");
  assert.equal(cegarSummary.formula_cache_scope, "next-ring-universe");
  assert.equal(cegarSummary.exact_availability, false);
  assert.equal(cegarSummary.propagate_values, true);
  assert.equal(cegarSummary.rounds.length, 1);
  assert.equal(cegarSummary.initial_clause_constraints, 0);
  assert.equal(cegarSummary.final_clause_constraints, 0);
  assert.match(cegarSummary.final_clause_report_sha256, /^[0-9a-f]{64}$/);

  const tailDirectory = join(directory, "tail");
  const tailSummaryPath = join(tailDirectory, "summary.json");
  const tailArguments = commonArguments.map(argument => {
    if (argument === "--min-count=1") return "--min-count=999";
    if (argument === "--max-count=1") return "--max-count=999";
    if (argument.startsWith("--output-dir=")) return `--output-dir=${tailDirectory}`;
    if (argument.startsWith("--report-output=")) return `--report-output=${tailSummaryPath}`;
    return argument;
  });
  tailArguments.push("--open-ended-maximum=true");
  const tail = spawnSync(process.execPath, tailArguments, {
    encoding: "utf8",
    timeout: 60_000,
    maxBuffer: 8 * 1024 * 1024
  });
  assert.equal(tail.status, 0, tail.stderr);
  const tailSummary = JSON.parse(readFileSync(tailSummaryPath, "utf8"));
  assert.equal(tailSummary.classification, "placement_cube_tail_exhausted");
  assert.equal(tailSummary.open_ended_maximum, true);
  assert.equal(tailSummary.counts[0].placement_count, 999);
  assert.equal(tailSummary.counts[0].maximum_placement_count, null);
  const tailCertificate = JSON.parse(readFileSync(tailSummary.counts[0].certificate, "utf8"));
  assert.equal(tailCertificate.min_placements, 999);
  assert.equal(tailCertificate.max_placements, null);
  assert.equal(tailCertificate.covered_anchor_placement_candidates, 12);
} finally {
  rmSync(directory, { recursive: true, force: true });
}

process.stdout.write("polycube placement-cube range regressions passed\n");
