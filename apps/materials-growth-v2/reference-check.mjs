// Evaluation only: never imported by learning, candidate generation or search.
import { compose, inverse, transform } from "./geometry.mjs";
export function checkPeriodicReference(sample, experiment, state) {
  if (!sample.evaluation) return null;
  const { cell, sites } = sample.evaluation;
  const first = experiment.engine.candidates.get(
    experiment.engine.placed.keys().next().value,
  );
  if (!first) return null;
  const type = experiment.grammar.types[first.meta.type];
  // One fixed rigid alignment for the ENTIRE generated patch. Select among
  // occurrence witnesses of its first placement, never align atoms separately.
  let best = 0;
  for (const o of type.occurrences) {
    const pose = compose(o.pose, inverse(first.meta.pose));
    let matched = 0;
    for (const atom of state.atoms) {
      const p = transform(pose, atom.position);
      if (
        sites.some(
          (s) =>
            s.species === atom.species &&
            Math.hypot(
              ...p.map((v, k) => {
                const d = v - s.fractional[k] * cell[k];
                return d - Math.round(d / cell[k]) * cell[k];
              }),
            ) <= experiment.grammar.epsilon,
        )
      )
        matched++;
    }
    best = Math.max(best, matched);
    if (best === state.atoms.length) break;
  }
  return {
    matched: best,
    total: state.atoms.length,
    fraction: best / state.atoms.length,
    scope:
      "Species-resolved site membership under one global rigid alignment, modulo the reference cell. Not a density, coverage or completeness proof. Evaluation metadata never enters search.",
  };
}
