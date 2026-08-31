import assert from "node:assert/strict";
import { buildCatalogConditionalChronology, chronologyFingerprint }
  from "./catalog-conditional-chronology.mjs";

const event = (index, before, wait, atomsBefore, atomsAfter) => ({ index, status: "accepted",
  label: `event ${index}`, before: { atoms: atomsBefore }, after: { atoms: atomsAfter },
  actionBarrierCheckpoint: { kineticCompetition: { committed: true, mode: "seeded-kmc",
    clockBeforeSeconds: before, clockAfterSeconds: before + wait, waitingTimeSeconds: wait,
    eventCountBefore: index - 1, eventCountAfter: index, selectedCandidateId: `candidate-${index}`,
    selectedEventDirection: "attach", temperatureKelvin: 800, selectedProbabilityWithinFrozenCatalog: .4,
    selectedLog10RatePerSecond: 3, log10TotalRatePerSecond: 3.4, candidateCount: 12,
    catalogScope: "requested-hard-admitted-actions-only" } } });
const chronology = buildCatalogConditionalChronology([
  event(1, 0, .002, 100, 106),
  { index: 2, status: "accepted", before: { atoms: 106 }, after: { atoms: 110 } },
  event(3, .002, .008, 110, 118),
], { totalLeapEvents: 3 });
assert.equal(chronology.clockedEvents, 2);
assert.equal(chronology.unclockedAcceptedLeaps, 1);
assert.equal(chronology.elapsedSeconds, .01);
assert.equal(chronology.structuralAtomAdvance, 14);
assert.equal(chronology.unconditionalMaterialTimeClaimed, false);
assert.equal(chronology.bulkGrowthRateClaimed, false);
assert.equal(chronology.targetUsed, false);
assert.equal(chronologyFingerprint({ b: 2, a: 1 }), chronologyFingerprint({ a: 1, b: 2 }));
assert.throws(() => buildCatalogConditionalChronology([
  event(1, 0, .002, 100, 106), event(2, .004, .001, 106, 108),
]), /continuous conditional clock/);
console.log("catalog-conditional chronology tests passed");
