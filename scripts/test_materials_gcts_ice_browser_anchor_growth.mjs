import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

import {
  executeIceMolecularAnchorGrowth,
  validateIceMolecularPortArtifact,
} from "../apps/iqc-growth-live/ice-molecular-anchor-growth.js";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const artifact = JSON.parse(await readFile(
  resolve(root, "apps/iqc-growth-live/ice-molecular-port-artifact.json"), "utf8"));
for (const forbidden of ["targetSites", "targetAtoms", "emittedAnchors", "acceptedCandidateIds"]) {
  if (JSON.stringify(artifact).includes(`\"${forbidden}\"`)) throw new Error(`artifact leaks ${forbidden}`);
}

if (!validateIceMolecularPortArtifact(artifact)) throw new Error("artifact did not validate");
const ih = executeIceMolecularAnchorGrowth(artifact, "iceIh");
const ic = executeIceMolecularAnchorGrowth(artifact, "iceIc");

const counts = (trace) => trace.waves.map((wave) => wave.acceptedAnchors);
if (JSON.stringify(counts(ih)) !== JSON.stringify([16, 8, 0])) throw new Error(`Ih counts ${counts(ih)}`);
if (JSON.stringify(counts(ic)) !== JSON.stringify([12, 0])) throw new Error(`Ic counts ${counts(ic)}`);
if (ih.emittedAnchors.length !== 24 || ic.emittedAnchors.length !== 12) throw new Error("wrong emitted anchor union");
if (!ih.fixedPoint || !ic.fixedPoint || !ih.exactBackendCountParity || !ic.exactBackendCountParity) throw new Error("backend parity/fixed point failed");
if (ih.targetUsed || ic.targetUsed || !ih.alternativesAreMutuallyExclusive || !ic.alternativesAreMutuallyExclusive) throw new Error("leakage/alternative contract failed");
if (ih.stationaryOrExponentialClaim || ic.stationaryOrExponentialClaim) throw new Error("finite trace overclaimed recurrence");
if (!ih.orientationAudit.consistent || !ic.orientationAudit.consistent
  || ih.orientationAudit.constrainedEdgesSatisfied !== 40
  || ih.orientationAudit.constrainedEdgesTotal !== 40
  || ih.orientationAudit.resolvedAnchors !== 9
  || ih.orientationAudit.ambiguousAnchors !== 24
  || ih.orientationAudit.globallySupportedHypotheses !== 125
  || ih.orientationAudit.stateCountExact !== "352321536000"
  || Math.abs(ih.orientationAudit.logStateCount - 26.58781005014425) > 1e-9
  || ih.orientationAudit.stateSpaceSha256 !== "4fe309af70f9f877133dcc92fb64ff8ff07b01883e4abb6574db28e22dad3407"
  || ic.orientationAudit.constrainedEdgesSatisfied !== 16
  || ic.orientationAudit.constrainedEdgesTotal !== 16
  || ic.orientationAudit.stateCountExact !== "16777216"
  || ic.orientationAudit.stateSpaceSha256 !== "c910a20ee452df714901730838dbb09f8141caa32c2c250f1cb2960ab358784b"
  || ic.orientationAudit.resolvedAnchors !== 5
  || ic.orientationAudit.ambiguousAnchors !== 12) {
  throw new Error("finite proton-orientation constraint audit changed");
}
for (const trace of [ih, ic]) {
  const audits = [trace.seedOrientationAudit, ...trace.waves.map((wave) => wave.orientationAudit)];
  if (audits.some((audit) => !audit || audit.targetUsed || audit.physicalPotentialUsed
    || audit.canonicalBranchMaterialized || audit.constrainedEdgesSatisfied !== audit.constrainedEdgesTotal
    || !/^\d+$/.test(audit.stateCountExact) || !/^[a-f0-9]{64}$/.test(audit.stateSpaceSha256)
    || audit.poseMarginals.length !== audit.anchors)) {
    throw new Error("orientation audit leakage/claim-boundary contract failed");
  }
  for (const audit of audits) for (const marginal of audit.poseMarginals) {
    const total = marginal.alternatives.reduce((sum, alternative) => sum + BigInt(alternative.assignmentCount), 0n);
    if (total !== BigInt(audit.stateCountExact)) throw new Error("exact pose marginals do not partition the global state space");
  }
  if (trace.orientationAudit.allHydrogensResolved) throw new Error("finite boundary falsely resolved every proton pose");
}

const poisonedExpectation = structuredClone(artifact);
poisonedExpectation.cases.iceIh.expectedAcceptedAnchors = [999];
const targetBlindReplay = executeIceMolecularAnchorGrowth(poisonedExpectation, "iceIh");
if (JSON.stringify(counts(targetBlindReplay)) !== JSON.stringify([16, 8, 0])
  || targetBlindReplay.exactBackendCountParity) throw new Error("expected counts influenced branch generation");

console.log("browser frozen ice anchor growth: passed", { Ih: counts(ih), Ic: counts(ic) });
