import assert from "node:assert/strict";
import { auditCriticalNucleusGrammarAdmission }
  from "./critical-nucleus-grammar-admission.mjs";

const sha = "a".repeat(64);
const local = [
  { species: "A", positionAngstrom: [0, 0, 0] },
  { species: "B", positionAngstrom: [2, 0, 0] },
  { species: "C", positionAngstrom: [0, 3, 0] },
  { species: "D", positionAngstrom: [0, 0, 4] },
];
const angle = .73; const cosine = Math.cos(angle); const sine = Math.sin(angle);
const rotate = ([x, y, z]) => [cosine * x - sine * y, sine * x + cosine * y, z];
const translation = [7, -4, 2];
const transformed = local.map((site, index) => ({
  siteId: `site-${index}`,
  species: site.species,
  positionAngstrom: rotate(site.positionAngstrom).map((value, axis) => value + translation[axis]),
  membershipProbability: .9,
  region: index ? "interface" : "core",
}));
const residual = { siteId: "residual-E", species: "E", positionAngstrom: [12, 9, -3],
  membershipProbability: .7, region: "interface" };
const geometry = {
  schema: "gcts-critical-nucleus-geometry-evidence-v1",
  requestSha256: "b".repeat(64), structureSha256: sha,
  sites: [...transformed, residual], targetUsed: false, gctsSeedChanged: false,
};
const grammar = {
  schema: "gcts-frozen-local-port-grammar-v1",
  structureSha256: sha,
  metricToleranceAngstrom: 1e-5,
  minimumSharedAtoms: 2,
  prototypes: [{ typeId: 4, occurrenceIndex: 19, sites: local,
    outgoingRuleCount: 3, incomingRuleCount: 2 }],
  admittedConnections: [{ fromType: 4, toType: 4 }],
  targetUsed: false,
};

const audit = auditCriticalNucleusGrammarAdmission(geometry, grammar,
  { minimumRecognizedFraction: .8 });
assert.equal(audit.seedAdmissible, true);
assert.equal(audit.selectedOccurrenceCount, 1);
assert.equal(audit.coveredAtomCount, 4);
assert.equal(audit.residualAtomCount, 1);
assert.equal(audit.completeRepresentationWithResidualTerminals, true);
assert.equal(audit.frontierPlacementCount, 1);
assert.equal(audit.connectedRecognizedCover, true);
assert.equal(audit.truncated, false);
assert.ok(audit.selectedOccurrences[0].rmsdAngstrom < 1e-10);
assert.equal(audit.selectedOccurrences[0].occurrenceIndex, 19);

const strict = auditCriticalNucleusGrammarAdmission(geometry, grammar,
  { minimumRecognizedFraction: .95 });
assert.equal(strict.seedAdmissible, false);
assert.equal(strict.recognizedAtomFraction, .8);

const permuted = { ...geometry, sites: [residual, transformed[2], transformed[0],
  transformed[3], transformed[1]] };
const permutationAudit = auditCriticalNucleusGrammarAdmission(permuted, grammar,
  { minimumRecognizedFraction: .8 });
assert.equal(permutationAudit.seedAdmissible, true);
assert.equal(permutationAudit.recognizedAtomFraction, audit.recognizedAtomFraction);

const reflected = { ...geometry, sites: geometry.sites.map(site => ({ ...site,
  positionAngstrom: [-site.positionAngstrom[0], site.positionAngstrom[1],
    site.positionAngstrom[2]] })) };
const reflectionAudit = auditCriticalNucleusGrammarAdmission(reflected, grammar,
  { minimumRecognizedFraction: .8 });
assert.equal(reflectionAudit.seedAdmissible, false);
assert.equal(reflectionAudit.enumeratedOccurrenceCount, 0);

const noFrontier = auditCriticalNucleusGrammarAdmission(geometry, { ...grammar,
  prototypes: [{ ...grammar.prototypes[0], outgoingRuleCount: 0 }] },
{ minimumRecognizedFraction: .8 });
assert.equal(noFrontier.seedAdmissible, false);
assert.equal(noFrontier.frontierPlacementCount, 0);

const collinear = auditCriticalNucleusGrammarAdmission(geometry, { ...grammar,
  prototypes: [{ typeId: 0, occurrenceIndex: 0, outgoingRuleCount: 1, incomingRuleCount: 1,
    sites: [{ species: "A", positionAngstrom: [0, 0, 0] },
      { species: "A", positionAngstrom: [1, 0, 0] },
      { species: "A", positionAngstrom: [2, 0, 0] }] }],
  admittedConnections: [] }, { minimumRecognizedFraction: 0 });
assert.equal(collinear.unorientablePrototypeCount, 1);
assert.equal(collinear.seedAdmissible, false);

assert.throws(() => auditCriticalNucleusGrammarAdmission({ ...geometry, targetUsed: true },
  grammar), /target-blind/);
assert.throws(() => auditCriticalNucleusGrammarAdmission(geometry,
  { ...grammar, targetUsed: true }), /target-blind/);
assert.throws(() => auditCriticalNucleusGrammarAdmission(geometry,
  { ...grammar, structureSha256: "c".repeat(64) }), /structure mismatch/);
const truncated = auditCriticalNucleusGrammarAdmission(geometry, { ...grammar,
  prototypes: [grammar.prototypes[0], { ...grammar.prototypes[0], typeId: 5 }],
  admittedConnections: [{ fromType: 4, toType: 4 }, { fromType: 5, toType: 5 }] },
  { maximumAnchorPairChecks: 1 });
assert.equal(truncated.truncated, true);
assert.equal(truncated.seedAdmissible, false);

console.log("critical nucleus grammar admission: all tests passed");
