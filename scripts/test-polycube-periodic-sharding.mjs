import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import { canonicalPolycubeKey } from "../assets/polycube-enumerator.js";

const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === "p9-42947");
assert.ok(candidate, "the periodic-sharding smoke test needs the unresolved p9 control");
const candidateKey = canonicalPolycubeKey(candidate.voxels);

const pipeline = new URL("./screen-3d-aperiodic-polycubes.mjs", import.meta.url);
const common = [
  pipeline.pathname,
  `--key=${candidateKey}`,
  "--periodic-min-tiles=3",
  "--periodic-max-tiles=3",
  "--box-screen=false",
  "--general-periodic=false",
  "--isohedral-screen=false",
  "--stop-after=periodic",
  "--report-chirality=false"
];

const emptyRange = spawnSync(process.execPath, [
  ...common,
  "--periodic-hnf-start-index=1200",
  "--periodic-hnf-end-index=1200"
], { encoding: "utf8" });
assert.equal(emptyRange.status, 0, emptyRange.stderr);
const records = emptyRange.stdout.trim().split(/\r?\n/).map(line => JSON.parse(line));
const start = records.find(record => record.type === "screen_start");
const result = records.find(record => record.type === "candidate")?.periodic_fast;
assert.equal(start.periodic_hnf_start_index, 1200);
assert.equal(start.periodic_hnf_end_index, 1200);
assert.equal(result.hnf_range_start, 1200);
assert.equal(result.hnf_range_end_exclusive, 1200);
assert.equal(result.hnf_range_total, 0);
assert.equal(result.hnf_range_exhausted, true);
assert.deepEqual(result.hnf_exhausted_by_copies, {});

const invalidMultiCopyRange = spawnSync(process.execPath, [
  pipeline.pathname,
  `--key=${candidateKey}`,
  "--periodic-min-tiles=2",
  "--periodic-max-tiles=3",
  "--periodic-hnf-start-index=1"
], { encoding: "utf8" });
assert.notEqual(invalidMultiCopyRange.status, 0);
assert.match(invalidMultiCopyRange.stderr, /explicit periodic HNF ranges require equal/);

const invalidResumeRange = spawnSync(process.execPath, [
  ...common,
  "--resume-active-hnf=true",
  "--periodic-hnf-start-index=1"
], { encoding: "utf8" });
assert.notEqual(invalidResumeRange.status, 0);
assert.match(invalidResumeRange.stderr, /cannot be combined with an explicit periodic HNF range/);

console.log("Polycube periodic-sharding regression passed", {
  start: result.hnf_range_start,
  end: result.hnf_range_end_exclusive
});
