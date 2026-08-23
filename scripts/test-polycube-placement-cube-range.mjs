#!/usr/bin/env node

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  placementCubeOrdinals,
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
  [{ parts: 8, index: 7 }],
  "empty refinement children must be omitted"
);

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
} finally {
  rmSync(directory, { recursive: true, force: true });
}

process.stdout.write("polycube placement-cube range regressions passed\n");
