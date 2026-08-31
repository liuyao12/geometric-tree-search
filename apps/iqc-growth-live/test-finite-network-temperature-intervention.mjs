import assert from "node:assert/strict";
import { buildFiniteNetworkTemperatureIntervention }
  from "./finite-network-temperature-intervention.mjs";

const KB = 8.617333262145e-5;
const T0 = 600;
function network(nodeIds, records) {
  const nodes = nodeIds.map((id) => ({ stateId: id,
    stateSha256: id.repeat(64).slice(0, 64), shortHash: id.repeat(10).slice(0, 10) }));
  const hash = Object.fromEntries(nodes.map((node) => [node.stateId, node.stateSha256]));
  return { nodes, hash, directedEdges: records.map(([from, to, barrier, prefactor, character], index) => ({
    key: `edge-${index}`, fromStateSha256: hash[from], toStateSha256: hash[to],
    barrierElectronVolt: barrier, barrierUncertaintyElectronVolt: .01,
    attemptFrequencyPerSecond: prefactor, attemptFrequencyUncertaintyLog10: .1,
    logRatePerSecond: Math.log(prefactor) - barrier / (KB * T0),
    logRateUncertainty: Math.hypot(.01 / (KB * T0), .1 * Math.LN10),
    temperatureKelvin: T0, methodSettingsSha256: "m".repeat(64),
    prefactorSettingsSha256: "p".repeat(64), eventDirection: "attach",
    initialAtomCount: 10, finalAtomCount: 11,
    temperatureApplicability: { scope: "bounded-constant-htst", minimumKelvin: 400,
      maximumKelvin: 900, externallyAuthorized: true,
      barrierAndPrefactorAssumedConstant: true },
    geometricPathObservable: { geometricCharacter: character },
  })) };
}

const chain = network(["a", "b", "t"], [
  ["a", "b", .4, 1e12, "contact-forming"],
  ["b", "t", .7, 2e13, "displacive"],
]);
const original = JSON.stringify(chain);
const chainAudit = buildFiniteNetworkTemperatureIntervention(chain, {
  sourceStateSha256: chain.hash.a, targetStateSha256: chain.hash.t,
  temperatureKelvin: 800, sampleCount: 9,
});
assert.equal(chainAudit.available, true);
const k1 = 1e12 * Math.exp(-.4 / (KB * 800));
const k2 = 2e13 * Math.exp(-.7 / (KB * 800));
const k10 = 1e12 * Math.exp(-.4 / (KB * T0));
const k20 = 2e13 * Math.exp(-.7 / (KB * T0));
assert.ok(Math.abs(chainAudit.selectedResponse.exactConditionalPassageTimeRatio
  - (1 / k1 + 1 / k2) / (1 / k10 + 1 / k20)) < 1e-10);
assert.ok(Math.abs(chainAudit.selectedResponse.targetHittingProbability - 1) < 1e-12);
assert.equal(chainAudit.commonAuthorizedMinimumKelvin, 400);
assert.equal(chainAudit.commonAuthorizedMaximumKelvin, 900);
assert.equal(chainAudit.dominantTemperatureControlEdge.geometricCharacter != null, true);
assert.equal(chainAudit.networkMutated, false);
assert.equal(chainAudit.unauthorizedExtrapolationPerformed, false);
assert.equal(JSON.stringify(chain), original);

const branch = network(["a", "t", "f"], [
  ["a", "t", .3, 1e12, "contact-forming"],
  ["a", "f", .8, 1e14, "contact-breaking"],
]);
const branchAudit = buildFiniteNetworkTemperatureIntervention(branch, {
  sourceStateSha256: branch.hash.a, targetStateSha256: branch.hash.t,
  temperatureKelvin: 800,
});
const targetRate = 1e12 * Math.exp(-.3 / (KB * 800));
const failureRate = 1e14 * Math.exp(-.8 / (KB * 800));
assert.ok(Math.abs(branchAudit.selectedResponse.targetHittingProbability
  - targetRate / (targetRate + failureRate)) < 1e-12);
assert.ok(Math.abs(branchAudit.selectedResponse.exactConditionalPassageTimeRatio
  - ((1 / (targetRate + failureRate))
    / (1 / (Math.exp(branch.directedEdges[0].logRatePerSecond)
      + Math.exp(branch.directedEdges[1].logRatePerSecond))))) < 1e-10);

const unauthorized = structuredClone(branch);
unauthorized.directedEdges[0].temperatureApplicability = { scope: "single-temperature",
  minimumKelvin: null, maximumKelvin: null, externallyAuthorized: false,
  barrierAndPrefactorAssumedConstant: false };
assert.equal(buildFiniteNetworkTemperatureIntervention(unauthorized, {
  sourceStateSha256: unauthorized.hash.a, targetStateSha256: unauthorized.hash.t,
  temperatureKelvin: 800,
}).available, false);
assert.equal(buildFiniteNetworkTemperatureIntervention(branch, {
  sourceStateSha256: branch.hash.a, targetStateSha256: branch.hash.t,
  temperatureKelvin: 950,
}).available, false);

console.log("finite-network temperature intervention: ok");
