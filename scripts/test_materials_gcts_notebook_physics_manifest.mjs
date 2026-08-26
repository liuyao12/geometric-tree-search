import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const extract = (start, end) => {
  const match = source.match(new RegExp(`function ${start}\\([\\s\\S]*?\\n}\\n\\nfunction ${end}`));
  assert.ok(match, `${start} must remain extractable`);
  return Function(`"use strict"; return (${match[0].replace(new RegExp(`\\n\\nfunction ${end}$`), "")});`)();
};

const notebookPhysicsManifest = extract("notebookPhysicsManifest", "experimentNotebookSummary");
const notebookPhysicsComparison = extract("notebookPhysicsComparison", "notebookPhysicsLayerHistory");
const notebookPhysicsLayerHistory = extract("notebookPhysicsLayerHistory", "renderNotebookPhysicsEvolution");

const leap = {
  index: 4,
  status: "accepted",
  targetUsed: false,
  physicsTranslation: [
    { id: "steric", process: "Steric exclusion", status: "encoded", role: "hard constraint",
      encoding: "colored minimum-distance exclusion", evidence: "0 collisions", boundary: "not an energy" },
    { id: "relaxation", process: "Local relaxation", status: "open", role: "declared hypothesis",
      encoding: "disabled", evidence: "no displacement", boundary: "not MD" },
  ],
};
const previousLeap = structuredClone(leap);
previousLeap.index = 3;
previousLeap.physicsTranslation[0].evidence = "candidate frontier not yet evaluated";
const manifest = notebookPhysicsManifest([previousLeap, leap]);
assert.equal(manifest.schema, 2);
assert.equal(manifest.sourceLeapIndex, 4);
assert.equal(manifest.retainedLeapCount, 2);
assert.equal(manifest.history.length, 2);
assert.equal(manifest.historyAlignment, "discrete structural-leap index; not physical time");
assert.equal(manifest.coordinatesEmbedded, false);
assert.equal(manifest.targetUsed, false);
assert.equal(manifest.physicalTimeModeled, false);
assert.deepEqual(Object.keys(manifest.records[0]), ["id", "process", "status", "role", "encoding", "evidence", "boundary"]);
assert.equal(notebookPhysicsManifest([]), null);

const evolution = notebookPhysicsLayerHistory(manifest, "steric");
assert.equal(evolution.available, true);
assert.equal(evolution.snapshots.length, 2);
assert.equal(evolution.snapshots[0].responseChanged, false);
assert.equal(evolution.snapshots[1].configurationChanged, false);
assert.equal(evolution.snapshots[1].responseChanged, true);
assert.equal(evolution.changeCount, 1);
const legacyManifest = structuredClone(manifest); legacyManifest.schema = 1; delete legacyManifest.history;
assert.equal(notebookPhysicsLayerHistory(legacyManifest, "steric").available, false);

const first = { physicsManifest: manifest };
const secondManifest = structuredClone(manifest);
secondManifest.records[0].evidence = "2 rejected collisions";
secondManifest.records[1].encoding = "5% capped accommodation";
secondManifest.records[1].status = "encoded";
const comparison = notebookPhysicsComparison(first, { physicsManifest: secondManifest });
assert.equal(comparison.available, true);
assert.equal(comparison.records.length, 2);
assert.equal(comparison.configurationChanges, 1);
assert.equal(comparison.responseChanges, 1);
assert.equal(comparison.openCount, 1);
assert.equal(comparison.records.find((record) => record.id === "steric").configurationChanged, false);
assert.equal(comparison.records.find((record) => record.id === "steric").responseChanged, true);
assert.equal(comparison.records.find((record) => record.id === "relaxation").configurationChanged, true);

assert.equal(notebookPhysicsComparison({}, secondManifest).available, false);
const tainted = structuredClone(manifest); tainted.targetUsed = true;
assert.equal(notebookPhysicsComparison(first, { physicsManifest: tainted }).available, false);
const coordinateBearing = structuredClone(manifest); coordinateBearing.coordinatesEmbedded = true;
assert.equal(notebookPhysicsComparison(first, { physicsManifest: coordinateBearing }).available, false);
const earlierTargetTaint = structuredClone(previousLeap); earlierTargetTaint.targetUsed = true;
assert.equal(notebookPhysicsManifest([earlierTargetTaint, leap]).targetUsed, true);

console.log("notebook physics manifest: passed");
