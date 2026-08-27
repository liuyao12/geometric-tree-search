import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const script = new URL("./screen-3d-aperiodic-polycubes.mjs", import.meta.url);
const continuationScript = new URL("./screen-polycube-corona-continuations.mjs", import.meta.url);
const candidateKey = "0,0,0;0,0,1;0,0,2;0,1,1;0,2,0;1,0,0;1,1,0;1,2,0;1,3,0;2,2,0";
const common = [
  "--periodic-screen=false",
  "--box-screen=false",
  "--isohedral-screen=false",
  "--stop-after=all",
  "--obstruction-layer=2",
  "--obstruction-time-ms=5000",
  "--obstruction-budget-clock=cpu",
  "--obstruction-nogoods=true",
  "--obstruction-conflict-backjumping=true",
  "--obstruction-return-nogoods=true",
  "--obstruction-return-corona=true",
  "--nodes=500",
  "--report-chirality=false"
];
const run = args => {
  const result = spawnSync(process.execPath, [script.pathname, ...args], {
    encoding: "utf8",
    maxBuffer: 16 * 1024 * 1024
  });
  assert.equal(result.status, 0, result.stderr);
  return result.stdout;
};
const candidateRecord = output => output.split(/\r?\n/).filter(Boolean)
  .map(line => JSON.parse(line))
  .find(record => record.type === "candidate");

const temporaryDirectory = mkdtempSync(join(tmpdir(), "gcts-corona-persistence-"));
try {
  const trainingOutput = run([`--key=${candidateKey}`, "--obstruction-seed=0", ...common]);
  const training = candidateRecord(trainingOutput);
  assert.equal(training.obstruction.patch_verified, true);
  assert.ok(training.obstruction.corona.length > 0);
  assert.equal(training.obstruction.corona_verification.verified, true);
  assert.ok(training.obstruction.nogood_clause_keys.length > 0);

  const report = join(temporaryDirectory, "training.ndjson");
  writeFileSync(report, trainingOutput);
  const emptyResume = spawnSync(process.execPath, [
    script.pathname,
    `--input-report=${report}`,
    "--input-classification=unresolved",
    "--input-stopped-by=time_limit"
  ], { encoding: "utf8" });
  assert.notEqual(emptyResume.status, 0);
  assert.match(emptyResume.stderr, /No candidates matched/);
  const replayOutput = run([
    `--input-report=${report}`,
    `--obstruction-initial-nogood-report=${report}`,
    `--obstruction-preferred-corona-report=${report}`,
    "--input-classification=unresolved",
    "--obstruction-seed=1",
    ...common
  ]);
  const replay = candidateRecord(replayOutput);
  assert.equal(replay.obstruction.patch_verified, true);
  assert.ok(replay.obstruction.initial_nogood_clauses > 0);
  assert.ok(replay.obstruction.preferred_placements_requested > 0);
  assert.ok(replay.obstruction.preferred_placements_matched > 0);
  assert.ok(replay.obstruction.nogood_clause_keys.length >= replay.obstruction.initial_nogood_clauses);

  const ringKey = "0,0,0;0,1,0;0,2,0;1,0,0;1,2,0;2,0,0;2,1,0;2,2,0";
  const exactResumeCommon = [
    `--key=${ringKey}`,
    "--candidate-id=ring8",
    "--periodic-screen=false",
    "--box-screen=false",
    "--general-periodic=false",
    "--isohedral-screen=false",
    "--stop-after=all",
    "--obstruction-layer=3",
    "--obstruction-time-ms=60000",
    "--obstruction-budget-clock=cpu",
    "--obstruction-nogoods=true",
    "--obstruction-conflict-backjumping=true",
    "--obstruction-symmetry-nogoods=false",
    "--obstruction-nogood-limit=50000"
  ];
  const cutoffOutput = run([...exactResumeCommon, "--nodes=1000"]);
  const cutoff = candidateRecord(cutoffOutput);
  assert.equal(cutoff.obstruction.stopped_by, "node_limit");
  assert.ok(cutoff.obstruction.resume_path.length > 0);
  const cutoffReport = join(temporaryDirectory, "exact-cutoff.ndjson");
  writeFileSync(cutoffReport, cutoffOutput);
  const exactTailOutput = run([
    ...exactResumeCommon,
    "--nodes=500000",
    `--obstruction-resume-report=${cutoffReport}`
  ]);
  const exactTail = candidateRecord(exactTailOutput);
  assert.equal(exactTail.obstruction.patch_verified, true);
  assert.deepEqual(exactTail.obstruction.resumed_from_path, cutoff.obstruction.resume_path);
  const mismatchedResume = spawnSync(process.execPath, [
    script.pathname,
    ...exactResumeCommon,
    "--nodes=500000",
    "--obstruction-seed=1",
    `--obstruction-resume-report=${cutoffReport}`
  ], { encoding: "utf8" });
  assert.notEqual(mismatchedResume.status, 0);
  assert.match(mismatchedResume.stderr, /Corona resume settings differ from source: seed/);

  const cpuContinuation = spawnSync(process.execPath, [
    continuationScript.pathname,
    "--id=p10-052588",
    "--outer-layer=2",
    "--inner-layer=3",
    "--seeds=7",
    "--time-ms=1",
    "--inner-time-ms=1",
    "--budget-clock=cpu"
  ], { encoding: "utf8" });
  assert.equal(cpuContinuation.status, 0, cpuContinuation.stderr);
  const continuationRecords = cpuContinuation.stdout.trim().split(/\r?\n/).map(line => JSON.parse(line));
  assert.equal(continuationRecords[0].budget_clock, "cpu");
  assert.equal(continuationRecords.at(-1).type, "continuation_portfolio_summary");
  const fixedOnlyContinuation = spawnSync(process.execPath, [
    continuationScript.pathname,
    "--id=p10-052588",
    "--outer-layer=2",
    "--inner-layer=3",
    "--seeds=",
    "--time-ms=1",
    "--inner-time-ms=1"
  ], { encoding: "utf8" });
  assert.equal(fixedOnlyContinuation.status, 0, fixedOnlyContinuation.stderr);
  const fixedOnlyRecords = fixedOnlyContinuation.stdout.trim().split(/\r?\n/).map(line => JSON.parse(line));
  assert.deepEqual(fixedOnlyRecords[0].seeds, []);
  assert.deepEqual(fixedOnlyRecords.at(-1).trials, []);
  const invalidClock = spawnSync(process.execPath, [
    continuationScript.pathname,
    "--budget-clock=calendar"
  ], { encoding: "utf8" });
  assert.notEqual(invalidClock.status, 0);
  assert.match(invalidClock.stderr, /budget-clock must be wall or cpu/);
  console.log("Polycube corona persistence regression passed", {
    exported: training.obstruction.nogood_clause_keys.length,
    imported: replay.obstruction.initial_nogood_clauses,
    replayNodes: replay.obstruction.nodes
  });
} finally {
  rmSync(temporaryDirectory, { recursive: true, force: true });
}
