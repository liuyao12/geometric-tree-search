import assert from "node:assert/strict";
import { identifyClusters } from "./continuous-learning.mjs";
import { ContinuousSearch } from "./continuous-search.mjs";
import { canonicalSupport, distance } from "./continuous-geometry.mjs";
import { samplePatch } from "./continuous-samples.mjs";

const drain = (iterator) => {
  let next;
  while (!(next = iterator.next()).done) {}
  return next.value;
};
const observed = samplePatch("ice").atoms;
const baseline = drain(identifyClusters(observed));
const baselineKeys = baseline.types.map((t) => t.key).sort();
const results = [];
// Neither anonymous label is an element name; reverse their lexical order too.
for (const labels of [
  { D: "opaque-A", O: "opaque-Z" },
  { D: "opaque-Z", O: "opaque-A" },
]) {
  const inverse = Object.fromEntries(
    Object.entries(labels).map(([a, b]) => [b, a]),
  );
  const atoms = observed.map((a) => ({ ...a, species: labels[a.species] }));
  const grammar = drain(identifyClusters(atoms));
  assert.deepEqual(
    grammar.types
      .map(
        (t) =>
          canonicalSupport(
            t.sites.map((a) => ({ ...a, species: inverse[a.species] })),
            grammar.tolerance,
          ).key,
      )
      .sort(),
    baselineKeys,
  );
  assert.equal(grammar.ports.length, baseline.ports.length);
  const componentKeys = new Set(
    grammar.types
      .filter((t) => t.kind === "connected component")
      .map((t) => t.key),
  );
  const search = new ContinuousSearch(grammar, {
    policy: "unmarked",
    maximumAtoms: 240,
  });
  for (
    let i = 0;
    i < 20000 &&
    !search.status.endsWith("limit") &&
    search.status !== "exhausted";
    i++
  ) {
    if (search.advance().type !== "accept") continue;
    const records = search.spatial.records,
      seen = new Set();
    for (let j = 0; j < records.length; j++) {
      if (seen.has(j)) continue;
      const component = [j];
      seen.add(j);
      for (let k = 0; k < component.length; k++)
        for (let p = 0; p < records.length; p++)
          if (
            !seen.has(p) &&
            distance(records[component[k]].position, records[p].position) <=
              grammar.molecularCutoff
          ) {
            seen.add(p);
            component.push(p);
          }
      if (component.some((p) => p >= atoms.length))
        assert.ok(
          componentKeys.has(
            canonicalSupport(
              component.map((p) => records[p]),
              grammar.tolerance,
            )?.key,
          ),
          "every new connected component must match an observed geometric support",
        );
    }
  }
  assert.ok(search.spatial.records.length > atoms.length + 30);
  results.push({
    labels,
    types: grammar.types.length,
    ports: grammar.ports.length,
    grown: search.spatial.records.length - atoms.length,
  });
}
console.log(JSON.stringify({ pass: true, anonymousLabelCases: results }));
