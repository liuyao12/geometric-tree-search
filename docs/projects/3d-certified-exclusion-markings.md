# Certified exclusions before GCTS search

The **Certified exclusions first** marking method is selectable in the 3D
lattice tiler and is the default for the nonacube cross. It implements a
negative-only alternative to the existing pair-corona classification experiment.
The latter's complete-catalogue acceptance gate is unchanged.

## Evidence and activation

Cold runs start with no exclusions or saved assignments. They enumerate
capacity-legal neighboring pairs, reduce them by verified point-group symmetry
and pair reversal, and first check for an exposed point with no legal completing
placement. Short unmarked pair-corona searches then look for further exhausted
cases. The oracle still uses complete candidate incidence, global dead points,
global forced moves, earliest-generation branching, and exact rollback.

Only an immediate dead point or complete search exhaustion certifies an invalid
pair. Attempt, time, memory, or catalogue limits leave cases unresolved. A
successful corona is retained as a finite witness, not infinite-tiling evidence.
Positive witnesses are not required to activate these certified exclusions.
A partial catalogue is usable because each exclusion is justified separately.
All other relative placements remain allowed by the marking.

Preparation receives at most forty percent of the lane's remaining budget,
capped at thirty seconds. The rest is available to search. If no exclusions
were certified, the lane explicitly continues unmarked, with an empty field;
that fallback is not saved as a learned marking. Nonempty fields are saved only
in browser-local history. Reuse reruns every negative proof, rebuilds the field
and its symmetry action, and rejects modified assignments or a different model.
The source tree contains no learned field or catalog-derived negative labels.

## Sparse marking construction

Suppose an impossible relative placement is \((i,0),(j,d)\), with common support
point \(q\). Give that exclusion its own component \(c\), assigning

\[
m_i^{(c)}(q)=0,\qquad m_j^{(c)}(q-d)=1.
\]

Every other slot of that component is absent. If both slots belong to the same
orientation, they are two different points of its field. An assigned zero is
not a wildcard. A disagreement between two copies occurs exactly at the
specified relative placement, or its reversal. No assumption about the
remaining pairs is needed. The construction applies to different species too.

Include the orbit of these two-slot components under the permitted point group.
The group permutes component indices; the two values themselves stay fixed.
The compiler checks that each component permutation is bijective and that every
possible disagreement corresponds to a proved excluded pair orbit. It also
replays each compiled exclusion against the fields. All marking points lie on
positive tile support. If the component budget would truncate a symmetry orbit,
that whole exclusion is omitted. This produces many sparse components; it is a
correctness-first construction, not a claim of a minimal marking.

Search receives only the resulting point fields. It uses the existing global
section, marking dependencies, candidate elimination, scheduler and rollback.
It does not call the pair oracle, scan forbidden-pair rules, or run a local
lookahead disguised as point marking during the subsequent search.

## Scope and comparison

These are proved redundant constraints for infinite exact tilings of the
specified unmarked point model. The proof is local: an infinite tiling containing
an excluded pair would provide a completion of the exact finite obligations
whose impossibility was proved. Marking agreement eliminates only such pairs.

This does **not** preserve all finite patches with merely viable current
frontiers. Some such patches cannot extend indefinitely. Therefore marked and
unmarked finite checkpoint searches have different accepted patch sets. The UI
reports this distinction and does not turn their timings into a same-problem
speedup claim. Failure of a capped run is still unknown, and geometric or
unrestricted Euclidean consequences require the model's separate faithfulness
argument. No Heesch-number conclusion follows from these experiments.

## Conformance and measured smoke runs

`node scripts/test-3d-certified-marking.mjs` verifies negative-only activation,
complete disagreement semantics, component covariance, preservation of other
relative poses, live graph domains against independent enumeration, exact
rollback, budget fallback, model provenance and tampered saved-proof rejection.
It also checks the browser worker's growth and fixed-window routes. The existing
point-search, reference-growth and marking-reuse regressions pass.

Exploratory cold runs on 2026-09-24 used proper rotations, seed ten, a target of
thirty-two tiles, a ten-second total budget and thirty-two attempts per pair.
These are correctness smoke measurements, not isolated throughput benchmarks.

| Tile | Certified method preparation | Subsequent result |
| --- | --- | --- |
| Turtle slab, proper rotations only | 113 negative pair orbits encoded; 3 positive and 8 unresolved; 339 components; about one second | Exhausted the marked search in 6 attempts with 430 marking eliminations. The unmarked proper-only control also exhausted, in 312 attempts. Preparation made the marked total slower. |
| Nonacube cross | 686 neighboring placements reduce to 60 pair orbits; no immediate dead-point exclusions; the short preparation left all 60 unresolved | Explicit unmarked fallback; no marking cuts and no acceleration established. |

The nonacube is therefore a useful test of honest partial evidence, but this
first pass has not yet found a useful marking for it. Stronger finite-obstruction
checks can be added as additional certified proof kinds. Triple obstructions
must not be silently projected into pair exclusions: every excluded relation
needs its own valid proof and a marking with a checked implication.
