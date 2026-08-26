import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const source = readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const extract = (start, end) => {
  const match = source.match(new RegExp(`function ${start}\\([\\s\\S]*?\\n}\\n\\nfunction ${end}`));
  assert.ok(match, `${start} must remain extractable`);
  return Function(`"use strict"; return (${match[0].replace(new RegExp(`\\n\\nfunction ${end}$`), "")});`)();
};

const notebookPhysicsManifest = extract("notebookPhysicsManifest", "experimentNotebookSummary");
const notebookPhysicsComparison = extract("notebookPhysicsComparison", "renderNotebookPhysicsAudit");

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
const manifest = notebookPhysicsManifest([leap]);
assert.equal(manifest.schema, 1);
assert.equal(manifest.sourceLeapIndex, 4);
assert.equal(manifest.coordinatesEmbedded, false);
assert.equal(manifest.targetUsed, false);
assert.equal(manifest.physicalTimeModeled, false);
assert.deepEqual(Object.keys(manifest.records[0]), ["id", "process", "status", "role", "encoding", "evidence", "boundary"]);
assert.equal(notebookPhysicsManifest([]), null);

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

console.log("notebook physics manifest: passed");
