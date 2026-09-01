import {
  buildPeriodicIceIhBoundaryAudit,
  buildPeriodicIceIhBoundarySeries,
  derivePeriodicIceIhOxygenGraph,
} from "../apps/iqc-growth-live/ice-periodic-boundary-audit.mjs";

const expected = [
  [[1, 1, 1], 4, 8, "18", "69e6afa939d01156cd88a06596cdb77ccddd751e1afd66f8e4f0faf62a9a9702"],
  [[2, 1, 1], 8, 16, "114", "8344b04c865dd34c6c2747453d601156435ef21da0f46c24bcbc1269186e6d73"],
  [[3, 1, 1], 12, 24, "858", "dc5b1bd71b0bd431969695ba27fcdda327436cdb7462aa16cfa4b647f5248270"],
  [[2, 2, 1], 16, 32, "2970", "2a45111418ee256aea3551cf9053a4d5a7fc1584c50584f06cd9419a3ca31ade"],
];
const series = buildPeriodicIceIhBoundarySeries();
if (series.length !== expected.length) throw new Error("periodic boundary series changed length");
series.forEach((audit, index) => {
  const [repeats, molecules, edges, count, digest] = expected[index];
  if (JSON.stringify(audit.repeats) !== JSON.stringify(repeats) || audit.moleculeCount !== molecules
    || audit.oxygenConnections !== edges || audit.exactAssignmentCount !== count || audit.graphSha256 !== digest) {
    throw new Error(`periodic Ice-Ih audit changed for ${repeats.join("x")}`);
  }
  if (!audit.oxygenGraphDerivedFromDeclaredLatticeGeometry || !audit.everyOxygenFourConnected
    || !audit.everyMoleculeDonatesTwice || !audit.everyConnectionHasExactlyOneProton
    || !audit.periodicBoundary || audit.openBoundary || audit.targetUsed || audit.protonCoordinatesUsed
    || audit.physicalPotentialUsed || audit.thermodynamicEntropyInferred || audit.bulkLimitClaimed) {
    throw new Error("periodic boundary audit violated its scientific claim contract");
  }
  if (!/^[a-f0-9]{64}$/.test(audit.graphSha256)
    || Math.abs(audit.paulingReferenceLogAssignmentsPerMolecule - Math.log(1.5)) > 1e-15) {
    throw new Error("periodic boundary reference provenance changed");
  }
  const graph = derivePeriodicIceIhOxygenGraph(repeats);
  if (graph.incident.some((ports) => ports.length !== 4 || new Set(ports).size !== 4)
    || graph.edges.length !== 2 * graph.addresses.length) throw new Error("periodic graph is not four-regular");
});
if (Math.abs(series.at(-1).logAssignmentsPerMolecule - 0.4997698269872966) > 1e-12
  || series.at(-1).parallelPeriodicEdges !== 0 || series.at(-1).maximumEliminationScope !== 7) {
  throw new Error("largest exact periodic audit changed");
}
if (series.some((audit, index) => index > 0
  && audit.logAssignmentsPerMolecule >= series[index - 1].logAssignmentsPerMolecule)) {
  throw new Error("declared finite periodic sequence no longer approaches the reference monotonically");
}
for (const invalid of [[0, 1, 1], [1.5, 1, 1], [1, 1], "2x2x1", [3, 2, 1]]) {
  let rejected = false;
  try { buildPeriodicIceIhBoundaryAudit(invalid); } catch { rejected = true; }
  if (!rejected) throw new Error("invalid periodic repeats were accepted");
}

console.log("periodic Ice-Ih boundary audit: passed", series.map((audit) =>
  `${audit.repeats.join("×")}:${audit.exactAssignmentCount}`));
