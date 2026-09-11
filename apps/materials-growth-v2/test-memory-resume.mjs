import assert from "node:assert/strict";
import { discover, learnSections } from "./learning.mjs";
import { samplePatch } from "./samples.mjs";
import { MaterialExperiment } from "./material.mjs";
const drain = (g) => {
  let r;
  do {
    r = g.next();
  } while (!r.done);
  return r.value;
};
const g = drain(discover(samplePatch("nacl").atoms, { epsilon: 0.03 }));
const m = drain(learnSections(g));
for (const limit of ["maximumPoints", "maximumCandidates"]) {
  const control = new MaterialExperiment(g, m, {
    maximumPoints: 100000,
    maximumCandidates: 100000,
  });
  const limited = new MaterialExperiment(g, m, {
    maximumPoints: 100000,
    maximumCandidates: 100000,
    softMemory: true,
  });
  limited.options[limit] =
    limit === "maximumPoints"
      ? limited.registry.points.length
      : limited.engine.candidates.size;
  let pauses = 0;
  for (let i = 0; i < 40; i++) {
    const expected = control.step();
    const event = limited.step();
    if (event.kind === "budget") {
      pauses++;
      const state = limited.engine.semanticState();
      assert.equal(limited.step().kind, "budget");
      assert.deepEqual(limited.engine.semanticState(), state);
      const previous = limited.options[limit];
      limited.continueWithMoreMemory();
      assert(limited.options[limit] > previous);
      assert.deepEqual(limited.engine.semanticState(), state);
    } else assert.equal(event.kind, expected.kind);
    assert.deepEqual(
      limited.engine.semanticState(),
      control.engine.semanticState(),
    );
    assert.deepEqual(limited.engine.stack, control.engine.stack);
    assert(limited.snapshot(false).validation.legal);
  }
  assert(pauses > 0, limit);
}
console.log(
  "PASS point/candidate memory pauses resume identical placements, frontier, stack and generations to unrestricted control",
);
