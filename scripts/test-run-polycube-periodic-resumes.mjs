#!/usr/bin/env node

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const temporaryDirectory = mkdtempSync(join(tmpdir(), "gcts-periodic-resumes-"));
try {
  const node = process.execPath;
  const screen = new URL("./screen-3d-aperiodic-polycubes.mjs", import.meta.url).pathname;
  const runner = new URL("./run-polycube-periodic-resumes.mjs", import.meta.url).pathname;
  const key = "0,0,0;0,0,1;0,0,5;0,0,6;0,1,1;0,1,2;0,1,3;0,1,4;0,1,5";
  const sourcePath = join(temporaryDirectory, "p9-20656-copy12-source.ndjson");
  const common = [
    "--size=9",
    "--max-candidates=1",
    "--periodic-screen=true",
    "--periodic-min-tiles=12",
    "--periodic-max-tiles=12",
    "--periodic-budget-clock=cpu",
    "--periodic-exact-cover-backend=dlx",
    "--periodic-linear-prefilter=false",
    "--periodic-time-ms=1000",
    "--box-screen=false",
    "--general-periodic=false",
    "--isohedral-screen=false",
    "--stop-after=periodic",
    "--nodes=50000000"
  ];
  const sourceRun = spawnSync(node, [
    screen,
    `--key=${key}`,
    "--candidate-id=p9-20656",
    ...common,
    `--output-file=${sourcePath}`
  ], { encoding: "utf8", timeout: 30000 });
  assert.equal(sourceRun.status, 0, sourceRun.stderr);
  const sourceRecords = readFileSync(sourcePath, "utf8").split(/\r?\n/u).filter(Boolean).map(JSON.parse);
  const sourceCandidate = sourceRecords.find(record => record.type === "candidate");
  assert.equal(sourceCandidate.periodic_fast.stopped_by, "time_limit");
  assert.ok(Number.isFinite(sourceCandidate.periodic_fast.active_hnf_index));

  const prefix = join(temporaryDirectory, "p9-20656-copy12");
  const run = spawnSync(node, [
    runner,
    `--output-prefix=${prefix}`,
    "--max-slices=2",
    `--resume-report=${sourcePath}`,
    ...common
  ], { encoding: "utf8", timeout: 30000 });
  assert.equal(run.status, 0, run.stderr);
  const events = run.stdout.trim().split(/\r?\n/u).map(line => JSON.parse(line));
  assert.ok(events.length >= 1 && events.length <= 2);
  const firstPath = `${prefix}-resume0.ndjson`;
  const firstRecords = readFileSync(firstPath, "utf8").split(/\r?\n/u).filter(Boolean).map(JSON.parse);
  const firstStart = firstRecords.find(record => record.type === "screen_start");
  const firstCandidate = firstRecords.find(record => record.type === "candidate");
  assert.equal(firstStart.input_report_sha256[0].sha256,
    createHash("sha256").update(readFileSync(sourcePath, "utf8")).digest("hex"));
  assert.equal(firstCandidate.periodic_fast.hnf_skipped,
    sourceCandidate.periodic_fast.active_hnf_index);
  if (events.length === 2) {
    const secondPath = `${prefix}-resume1.ndjson`;
    const secondRecords = readFileSync(secondPath, "utf8").split(/\r?\n/u).filter(Boolean).map(JSON.parse);
    const secondStart = secondRecords.find(record => record.type === "screen_start");
    assert.equal(secondStart.input_report_sha256[0].sha256,
      createHash("sha256").update(readFileSync(firstPath, "utf8")).digest("hex"));
  }
  console.log("Periodic resume-driver regression passed", {
    slices: events.length,
    first_hnf: firstCandidate.periodic_fast.hnf_skipped
  });
} finally {
  rmSync(temporaryDirectory, { recursive: true, force: true });
}
