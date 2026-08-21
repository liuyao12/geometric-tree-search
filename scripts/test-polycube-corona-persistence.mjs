import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const script = new URL("./screen-3d-aperiodic-polycubes.mjs", import.meta.url);
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
  assert.ok(training.obstruction.nogood_clause_keys.length > 0);

  const report = join(temporaryDirectory, "training.ndjson");
  writeFileSync(report, trainingOutput);
  const replayOutput = run([
    `--input-report=${report}`,
    `--obstruction-initial-nogood-report=${report}`,
    "--input-classification=unresolved",
    "--obstruction-seed=1",
    ...common
  ]);
  const replay = candidateRecord(replayOutput);
  assert.equal(replay.obstruction.patch_verified, true);
  assert.ok(replay.obstruction.initial_nogood_clauses > 0);
  assert.ok(replay.obstruction.nogood_clause_keys.length >= replay.obstruction.initial_nogood_clauses);
  console.log("Polycube corona persistence regression passed", {
    exported: training.obstruction.nogood_clause_keys.length,
    imported: replay.obstruction.initial_nogood_clauses,
    replayNodes: replay.obstruction.nodes
  });
} finally {
  rmSync(temporaryDirectory, { recursive: true, force: true });
}
