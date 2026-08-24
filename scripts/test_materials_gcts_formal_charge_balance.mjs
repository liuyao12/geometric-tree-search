import assert from "node:assert/strict";
import {
  formalChargeBalanceDelta,
  learnFormalChargeTarget,
} from "../apps/iqc-growth-live/formal-charge-balance.js";
import { formalChargeFromChemistryToken } from "../apps/iqc-growth-live/structure-io.js";

const nacl = learnFormalChargeTarget(["Na^+1", "Cl^-1", "Na^+1", "Cl^-1"], formalChargeFromChemistryToken);
assert.equal(nacl.available, true);
assert.equal(nacl.coverage, 1);
assert.equal(nacl.meanFormalCharge, 0);
assert.equal(nacl.netFormalCharge, 0);

const heals = formalChargeBalanceDelta(["Na^+1", "Na^+1", "Cl^-1"], ["Cl^-1"], nacl, formalChargeFromChemistryToken);
assert.equal(heals.available, true);
assert.ok(heals.delta < 0, "adding Cl- should reduce Na-rich formal-charge drift");
assert.equal(heals.projectedNetFormalCharge, 0);

const worsens = formalChargeBalanceDelta(["Na^+1", "Na^+1", "Cl^-1"], ["Na^+1"], nacl, formalChargeFromChemistryToken);
assert.ok(worsens.delta > 0, "adding Na+ should increase Na-rich formal-charge drift");

const mixed = learnFormalChargeTarget([
  "occ[Fe^+2=0.5;Fe^+3=0.5]",
  "occ[O^-2=1]",
  "occ[O^-2=0.25;Vac=0.75]",
], formalChargeFromChemistryToken);
assert.equal(mixed.available, true);
assert.equal(mixed.netFormalCharge, 0);
assert.equal(mixed.meanFormalCharge, 0);

const incomplete = learnFormalChargeTarget(["Na^+1", "Cl"], formalChargeFromChemistryToken);
assert.equal(incomplete.available, false);
assert.equal(incomplete.coverage, .5);
const unavailable = formalChargeBalanceDelta(["Na^+1"], ["Cl^-1"], incomplete, formalChargeFromChemistryToken);
assert.equal(unavailable.available, false);
assert.equal(unavailable.scaledDelta, 0);
assert.match(unavailable.reason, /incomplete/);

console.log("formal oxidation-state reservoir balance: passed", {
  nacl: nacl.meanFormalCharge,
  heals: heals.scaledDelta,
  worsens: worsens.scaledDelta,
  mixed: mixed.netFormalCharge,
});
