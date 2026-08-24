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

const poisonedExpectation = structuredClone(artifact);
poisonedExpectation.cases.iceIh.expectedAcceptedAnchors = [999];
const targetBlindReplay = executeIceMolecularAnchorGrowth(poisonedExpectation, "iceIh");
if (JSON.stringify(counts(targetBlindReplay)) !== JSON.stringify([16, 8, 0])
  || targetBlindReplay.exactBackendCountParity) throw new Error("expected counts influenced branch generation");

console.log("browser frozen ice anchor growth: passed", { Ih: counts(ih), Ic: counts(ic) });
