#!/usr/bin/env node

import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const reportPath = process.argv[2]
  ?? "data/lattice-polyhedron-complete-shell-screen-2026-08-19.json";
const report = JSON.parse(await readFile(reportPath, "utf8"));

assert.equal(report.schemaVersion, 1);
assert.equal(report.kind, "lattice_polyhedron_complete_shell_screen");
assert.equal(report.configuration?.cascade, true);
assert.equal(report.configuration?.targetShellDepth, 5);
assert.equal(report.configuration?.model, "face-to-face lattice tiling");
assert.deepEqual(report.configuration?.seeds, [1, 2, 3]);

const expectedCandidates = ["10_16113", "10_45026", "10_45033", "9_11683"];
assert.deepEqual(report.candidates.map(entry => entry.candidate), expectedCandidates);
assert.equal(new Set(report.rows.map(row =>
  `${row.candidate}:${row.seed}:${row.targetShellDepth}`
)).size, report.rows.length, "candidate/seed/target receipts must be unique");

for (const row of report.rows) {
  assert.equal(row.targetShellDepth >= 1, true);
  assert.equal(row.searchIncomplete, row.resultKind === "search_incomplete");
  if (row.success) {
    assert.equal(row.resultKind, "patch_found");
    assert.equal(row.certified, false);
    assert.equal(row.certificateKind, "finite_complete_shell");
    assert.equal(row.bestShellDepth >= row.targetShellDepth, true);
    assert.equal(row.bestShellPatchTiles > 1, true);
    assert.ok(row.bestShellWitnessHash);
  }
  if (row.resultKind === "no_tiling") {
    assert.equal(row.success, false);
    assert.equal(row.certified, true);
    assert.equal(row.canTile, false);
    assert.equal(row.certificateKind, "finite_shell_obstruction");
    assert.equal(row.searchIncomplete, false);
    assert.equal(row.terminationReason, "exhausted");
  }
}

const rowsFor = id => report.rows.filter(row => row.candidate === id);
const firstObstructionDepth = id => Math.min(...rowsFor(id)
  .filter(row => row.resultKind === "no_tiling")
  .map(row => row.targetShellDepth));
assert.equal(firstObstructionDepth("10_16113"), 2);
assert.equal(firstObstructionDepth("10_45026"), 1);
assert.equal(firstObstructionDepth("9_11683"), 1);

const survivorRows = rowsFor("10_45033");
assert.equal(survivorRows.some(row => row.resultKind === "no_tiling"), false);
for (const depth of [1, 2, 3, 4]) {
  const rows = survivorRows.filter(row => row.targetShellDepth === depth);
  assert.equal(rows.length, 3);
  assert.equal(rows.every(row => row.success), true, `shell ${depth} must succeed in every seed`);
}
const depthFiveRows = survivorRows.filter(row => row.targetShellDepth === 5);
assert.equal(depthFiveRows.length, 3);
assert.equal(depthFiveRows.filter(row => row.success).length, 2);
assert.equal(depthFiveRows.filter(row => row.searchIncomplete).length, 1);
assert.equal(depthFiveRows.filter(row => row.success).every(row =>
  row.bestShellPatchTiles === 464
), true);

for (const candidate of expectedCandidates) {
  for (const seed of report.configuration.seeds) {
    const targets = rowsFor(candidate)
      .filter(row => row.seed === seed)
      .map(row => row.targetShellDepth);
    assert.deepEqual(targets, Array.from({ length: targets.length }, (_, index) => index + 1));
  }
}

const summary = {
  rejected: {
    "10_16113": { obstructionShell: 2, completedShell: 1 },
    "10_45026": { obstructionShell: 1, completedShell: 0 },
    "9_11683": { obstructionShell: 1, completedShell: 0 }
  },
  survivor: {
    id: "10_45033",
    robustCompletedShell: 4,
    maximumCompletedShell: 5,
    shellFiveHits: 2,
    shellFiveTrials: 3,
    shellFiveWitnessTiles: 464
  },
  totals: report.totals
};
process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
