import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { POLYCUBE_GCTS_CANDIDATES } from "../assets/polycube-census-candidates.js";
import { canonicalPolycubeKey } from "../assets/polycube-enumerator.js";
import { polycubePeriodicHnfBasisCount } from "../assets/polycube-periodic-tiler.js";

const candidate = POLYCUBE_GCTS_CANDIDATES.find(entry => entry.id === "p9-42947");
assert.ok(candidate, "the periodic-sharding smoke test needs the unresolved p9 control");
const candidateKey = canonicalPolycubeKey(candidate.voxels);
assert.equal(polycubePeriodicHnfBasisCount(27), 1210);
assert.equal(polycubePeriodicHnfBasisCount(130), 39711);

const pipeline = new URL("./screen-3d-aperiodic-polycubes.mjs", import.meta.url);
const auditor = new URL("./audit-polycube-periodic-shards.mjs", import.meta.url);
const shardRunner = new URL("./run-polycube-periodic-shards.mjs", import.meta.url);
const campaignAuditor = new URL("./audit-polycube-periodic-campaign.mjs", import.meta.url);
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

const temporaryDirectory = mkdtempSync(join(tmpdir(), "gcts-hnf-shards-"));
const resumeInput = join(temporaryDirectory, "resume-input.ndjson");
writeFileSync(resumeInput, emptyRange.stdout);
const hashedInputRun = spawnSync(process.execPath, [
  pipeline.pathname,
  `--input-report=${resumeInput}`,
  "--periodic-min-tiles=3",
  "--periodic-max-tiles=3",
  "--periodic-hnf-start-index=1200",
  "--periodic-hnf-end-index=1200",
  "--box-screen=false",
  "--general-periodic=false",
  "--isohedral-screen=false",
  "--stop-after=periodic",
  "--report-chirality=false"
], { encoding: "utf8" });
assert.equal(hashedInputRun.status, 0, hashedInputRun.stderr);
const hashedInputStart = hashedInputRun.stdout.trim().split(/\r?\n/)
  .map(line => JSON.parse(line)).find(record => record.type === "screen_start");
assert.deepEqual(hashedInputStart.input_report_sha256, [{
  path: resumeInput,
  sha256: createHash("sha256").update(emptyRange.stdout).digest("hex")
}]);
const shardReport = (startIndex, endIndex) => [
  {
    type: "screen_start",
    periodic_min_tiles: 12,
    periodic_max_tiles: 12,
    periodic_hnf_start_index: startIndex,
    periodic_hnf_end_index: endIndex
  },
  {
    type: "candidate",
    id: "test-candidate",
    key: candidateKey,
    classification: "unresolved",
    periodic_fast: {
      certified: false,
      stopped_by: null,
      hnf_visited: endIndex - startIndex,
      hnf_range_start: startIndex,
      hnf_range_end_exclusive: endIndex,
      hnf_range_total: endIndex - startIndex,
      hnf_range_exhausted: true,
      nodes: endIndex - startIndex,
      milliseconds: 1
    }
  },
  { type: "screen_summary" }
].map(record => JSON.stringify(record)).join("\n") + "\n";
const shardA = join(temporaryDirectory, "a.ndjson");
const shardB = join(temporaryDirectory, "b.ndjson");
writeFileSync(shardA, shardReport(4, 7));
writeFileSync(shardB, shardReport(7, 9));
const audited = spawnSync(process.execPath, [
  auditor.pathname,
  "--expected-start=4",
  "--expected-end=9",
  shardA,
  shardB
], { encoding: "utf8" });
assert.equal(audited.status, 0, audited.stderr);
const audit = JSON.parse(audited.stdout);
assert.equal(audit.coverage_gap_free, true);
assert.equal(audit.totals.hnf_bases_exhausted, 5);
const rejectedGap = spawnSync(process.execPath, [
  auditor.pathname,
  "--expected-start=4",
  "--expected-end=10",
  shardA,
  shardB
], { encoding: "utf8" });
assert.notEqual(rejectedGap.status, 0);
assert.match(rejectedGap.stderr, /coverage ends at 9, expected 10/);

const orchestratedDirectory = join(temporaryDirectory, "orchestrated");
const orchestrated = spawnSync(process.execPath, [
  shardRunner.pathname,
  `--key=${candidateKey}`,
  "--id=p9-42947-test",
  "--copies=3",
  "--hnf-start-index=1200",
  "--hnf-end-index=1205",
  "--shards=2",
  "--concurrency=2",
  "--periodic-time-ms=10000",
  `--output-dir=${orchestratedDirectory}`
], { encoding: "utf8" });
assert.equal(orchestrated.status, 0, orchestrated.stderr);
const orchestratedRecords = orchestrated.stdout.trim().split(/\r?\n/).map(line => JSON.parse(line));
assert.equal(orchestratedRecords.at(-1).type, "shard_run_complete");
assert.equal(orchestratedRecords.at(-1).totals.hnf_bases_exhausted, 5);
const orchestratedAudit = JSON.parse(readFileSync(join(orchestratedDirectory, "audit.json"), "utf8"));
assert.deepEqual(orchestratedAudit.expected_range, [1200, 1205]);
assert.equal(orchestratedAudit.totals.shards, 2);
assert.equal(orchestratedAudit.candidate_id, "p9-42947-test");
const campaignAudit = spawnSync(process.execPath, [
  campaignAuditor.pathname,
  "--expected-copies=3",
  "--expected-start=1200",
  "--expected-end=1205",
  "--expected-candidates=p9-42947-test",
  join(orchestratedDirectory, "audit.json")
], { encoding: "utf8" });
assert.equal(campaignAudit.status, 0, campaignAudit.stderr);
const campaign = JSON.parse(campaignAudit.stdout);
assert.equal(campaign.coverage_gap_free, true);
assert.equal(campaign.totals.candidates, 1);
assert.equal(campaign.totals.hnf_bases_exhausted, 5);
const rejectedCandidateSet = spawnSync(process.execPath, [
  campaignAuditor.pathname,
  "--expected-copies=3",
  "--expected-start=1200",
  "--expected-end=1205",
  "--expected-candidates=wrong-candidate",
  join(orchestratedDirectory, "audit.json")
], { encoding: "utf8" });
assert.notEqual(rejectedCandidateSet.status, 0);
assert.match(rejectedCandidateSet.stderr, /do not match expected/);
const resumed = spawnSync(process.execPath, [
  shardRunner.pathname,
  `--key=${candidateKey}`,
  "--id=p9-42947-test",
  "--copies=3",
  "--hnf-start-index=1200",
  "--hnf-end-index=1205",
  "--shards=2",
  "--concurrency=2",
  `--output-dir=${orchestratedDirectory}`
], { encoding: "utf8" });
assert.equal(resumed.status, 0, resumed.stderr);
assert.equal(JSON.parse(resumed.stdout.split(/\r?\n/)[0]).reused, 2);
const invalidBackend = spawnSync(process.execPath, [
  shardRunner.pathname,
  `--key=${candidateKey}`,
  "--copies=3",
  "--exact-cover-backend=guess"
], { encoding: "utf8" });
assert.notEqual(invalidBackend.status, 0);
assert.match(invalidBackend.stderr, /exact-cover-backend must be scan or dlx/);
rmSync(temporaryDirectory, { recursive: true, force: true });

console.log("Polycube periodic-sharding regression passed", {
  start: result.hnf_range_start,
  end: result.hnf_range_end_exclusive,
  copy13Bases: polycubePeriodicHnfBasisCount(130)
});
