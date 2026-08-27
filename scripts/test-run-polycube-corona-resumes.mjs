#!/usr/bin/env node

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const temporaryDirectory = mkdtempSync(join(tmpdir(), "gcts-corona-resumes-"));
try {
  const prefix = join(temporaryDirectory, "p9-20656-layer7");
  const runner = new URL("./run-polycube-corona-resumes.mjs", import.meta.url);
  const key = "0,0,0;0,0,1;0,0,5;0,0,6;0,1,1;0,1,2;0,1,3;0,1,4;0,1,5";
  const run = spawnSync(process.execPath, [
    runner.pathname,
    `--output-prefix=${prefix}`,
    "--max-slices=2",
    `--key=${key}`,
    "--candidate-id=p9-20656",
    "--size=9",
    "--max-candidates=1",
    "--periodic-screen=false",
    "--box-screen=false",
    "--general-periodic=false",
    "--isohedral-screen=false",
    "--stop-after=all",
    "--obstruction-layer=7",
    "--obstruction-time-ms=1000",
    "--obstruction-budget-clock=cpu",
    "--obstruction-nogoods=true",
    "--obstruction-conflict-backjumping=true",
    "--obstruction-symmetry-nogoods=false",
    "--obstruction-nogood-limit=50000",
    "--obstruction-seed=0",
    "--obstruction-return-corona=false",
    "--nodes=50000000"
  ], { encoding: "utf8", timeout: 30000 });
  assert.equal(run.status, 0, run.stderr);
  const events = run.stdout.trim().split(/\r?\n/u).map(line => JSON.parse(line));
  assert.equal(events.length, 2);
  assert.equal(events[0].terminal, null);
  assert.equal(events[1].terminal, null);
  assert.ok(events.every(event => event.resume_path_length > 0));
  const sourcePath = `${prefix}-resume0.ndjson`;
  const tailPath = `${prefix}-resume1.ndjson`;
  const sourceText = readFileSync(sourcePath, "utf8");
  const tailRecords = readFileSync(tailPath, "utf8").split(/\r?\n/u).filter(Boolean).map(JSON.parse);
  const tailStart = tailRecords.find(record => record.type === "screen_start");
  const tailCandidate = tailRecords.find(record => record.type === "candidate");
  assert.equal(tailStart.obstruction_resume_report_sha256,
    createHash("sha256").update(sourceText).digest("hex"));
  assert.ok(tailCandidate.obstruction.resumed_from_path.length > 0);
  console.log("Corona resume-driver regression passed", {
    slices: events.length,
    source_hash: tailStart.obstruction_resume_report_sha256
  });
} finally {
  rmSync(temporaryDirectory, { recursive: true, force: true });
}
