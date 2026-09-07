import assert from "node:assert/strict";
import { identifyClusters, trainMarking } from "./continuous-learning.mjs";
import { samplePatch } from "./continuous-samples.mjs";
import { ContinuousSearch } from "./continuous-search.mjs";
import { distance, keySites } from "./continuous-geometry.mjs";

const drain = (iterator) => {
  let next;
  while (!(next = iterator.next()).done) {}
  return next.value;
};
const results = [];
for (const isotope of ["D", "H"]) {
  const atoms = samplePatch("ice").atoms.map((a) => ({
    ...a,
    species: a.species === "D" ? isotope : a.species,
  }));
  const grammar = drain(identifyClusters(atoms));
  assert.equal(grammar.audit.molecularSupportClosure, true);
  assert.equal(grammar.audit.recurringMolecules, 56);
  assert.equal(
    grammar.residuals.length,
    24,
    "crop fragments retained as seed, not learned as molecules",
  );
  for (const type of grammar.types) {
    assert.equal(
      type.sites.filter((a) => a.species === isotope).length,
      2 * type.sites.filter((a) => a.species === "O").length,
    );
    assert.ok(type.molecularGroups.every((group) => group.length === 3));
  }
  const marking = drain(trainMarking(grammar));
  const molecularCollision = new ContinuousSearch({
    ...grammar,
    occurrences: [],
    atoms: [
      { species: "O", position: [0, 0, 0] },
      { species: isotope, position: [0.98, 0, 0] },
      { species: isotope, position: [-0.24, 0.95, 0] },
    ],
  });
  const competingMolecule = [
    { species: "O", position: [0, 0, 0] },
    { species: isotope, position: [0, 0, 0.98] },
    { species: isotope, position: [0, 0, -0.98] },
  ];
  assert.equal(
    molecularCollision.inspect(competingMolecule),
    2,
    "ordinary exclusion alone admits a second molecular orientation",
  );
  assert.equal(
    molecularCollision.inspect(competingMolecule, [[0, 1, 2]]),
    null,
    "molecular ownership prevents four hydrogens sharing an oxygen",
  );
  assert.equal(molecularCollision.stats.molecularConflicts, 1);
  for (const policy of ["frequency", "marking", "unmarked", "rl"]) {
    const search = new ContinuousSearch(grammar, {
      policy,
      marking,
      maximumAtoms: 260,
    });
    for (
      let steps = 0;
      steps < 20000 &&
      !search.status.endsWith("limit") &&
      search.status !== "exhausted";
      steps++
    ) {
      const event = search.advance();
      if (event.type !== "accept") continue;
      const current = search.spatial.records;
      // Every accepted prefix must preserve full molecules, not only the final snapshot.
      for (const atom of current.slice(atoms.length)) {
        const bonded = current.filter(
          (other) =>
            other !== atom &&
            distance(atom.position, other.position) <= grammar.molecularCutoff,
        );
        if (atom.species === "O") {
          assert.equal(
            bonded.length,
            2,
            "new oxygen must come with exactly two hydrogens",
          );
          assert.ok(bonded.every((a) => a.species === isotope));
        } else {
          assert.equal(
            bonded.length,
            1,
            "new hydrogen must belong to one molecule",
          );
          assert.equal(bonded[0].species, "O");
        }
      }
    }
    const grown = search.spatial.records.slice(atoms.length);
    assert.ok(grown.filter((a) => a.species === "O").length >= 8);
    assert.ok(grown.filter((a) => a.species === isotope).length >= 16);
    assert.equal(
      keySites(search.spatial.records.slice(0, atoms.length)),
      keySites(atoms),
    );
    results.push({ isotope, policy, grown: grown.length });
  }
}
console.log(JSON.stringify({ pass: true, cases: results }));
