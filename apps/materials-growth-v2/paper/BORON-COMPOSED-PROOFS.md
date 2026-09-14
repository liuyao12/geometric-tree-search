# Composing point-filling proofs through forced moves

14 September 2026. Proof-producing search control on the six frozen boron
models. This is not a new material marking learner or a physical rule.

## Three proof statements

The previous local certificate could explain only direct capacity, marking
or already-selected-inventory blockers. The new proof language additionally
uses previously established forbidden combinations and forced implications:

- **Dead point:** a legal placement set S leaves required point p unfilled;
  every candidate touching p is already selected, overflows capacity, conflicts
  with a mark, or would complete an earlier certified forbidden combination.
  Therefore no exact cover can contain S.
- **Forced placement:** the same argument blocks every candidate at p except
  c. Therefore every exact cover containing S must contain c.
- **Resolution:** if S cannot occur and c belongs to S, while A implies c,
  then `(S minus {c}) union A` cannot occur. This is ordinary propositional
  resolution, not a new inference rule or an algorithmic novelty claim.

References point only to earlier proof nodes. An independent checker can
replay the resulting acyclic proof graph without executing the search.
The exact integer filling and interval-intersection semantics are unchanged.

## Search and rollback

At a dead point, construct its clause and resolve away forced placements using
their recorded implication proofs, in reverse placement order. The remaining
clause refers only to current decisions. Register it as a persistent model-local
constraint and undo through the latest decision it contains. Intervening frames
may be skipped only because that same certified combination makes them fail.
This is a declared proof-directed backtracking control, not a claim to reproduce
the original search trace. It does not use unproved parent-local exclusions.

All subsequent decisions return to global dead points, global forced moves and
earliest-generation branching. Clauses remove candidates through the common
incidence graph. Cross-member dependency edges propagate their effects to
distant support points. Implication references associated with current forced
placements are trailed and removed on undo; globally valid proofs persist.
An explicit proof reset at an empty root reconstructs the original base state.
Retaining unary proofs can legitimately change the root candidate graph.

The engine inherits the previous immutable, complete finite-model restrictions:
all positive-support points required; no dynamic candidates, external constraints,
initial placements, fixed marks or activation callbacks. Distinct marking-only
points are allowed. No symmetry transfer, relaxed correspondence, chemistry,
training-solution placement IDs or periodic selection lock enters search.

## Verification

On 300 small models, exhaustive enumeration checks every produced statement
against every exact completion: 1,858 visited states, 1,494 proof nodes and 336
resolution steps. Compatible completions are retained and empty-root reset
checks pass. A separate satisfiable example exercises forced resolution, with
two deliberate invalid-proof rejections. These random tests do not themselves
exercise skipped intervening frames; the material runs below do.

The independent Python checker reconstructs all leaf point totals and marking
intersections, checks every candidate at the cited point, validates references
to earlier clauses and checks each exact resolution identity. Nine mutation
controls reject missing antecedents, unexplained candidates, altered conclusions
and invalid/forward references. A separate material verifier reconstructs all
candidate t/m-values from the learned library and checks the final states.

## Results: correct composition, unresolved reconstruction

Use the same six observed candidate pools and learned weights, with marked and
unmarked lanes, 100,000 advances or 15 seconds per run. The 12-run experiment
contains **82,872 verified proof nodes and 4,661 registered conflict clauses**.
Every statement is also checked against the known connected training witness;
none excludes it. This is a sanity check in addition to the general inference
rules, not the sole reason the clauses are sound.

| Model/lane | Registered clauses | Resolution nodes | Intervening frames skipped | Outcome |
| --- | ---: | ---: | ---: | --- |
| β-106, unmarked | 1,075 | 9,169 | 2,424 | Budget unknown |
| β-106, marked | 1,048 | 8,937 | 2,347 | Budget unknown |
| τ-106, unmarked | 1,277 | 19,734 | 49 | Budget unknown |
| τ-106, marked | 1,261 | 19,348 | 49 | Budget unknown |

The other four structures finish with connected covers in both lanes, without
requiring conflict learning. The two hard structures still fail to finish.
More expressive proofs are not automatically a faster implementation: generating
and checking proof nodes, retaining clauses and auditing dependencies add substantial
work. These runs do not demonstrate an end-to-end or GCTS-marking speedup.
The time limit is checked between advances; one advance or audit may overshoot.

This closes the earlier proof-composition gap but not the larger research goal.
The clauses are specific to a fixed candidate model, not transferable learned
motif markings. These are supplied-coordinate, in-sample finite reconstructions,
not coordinate-blind growth or a verified common-condition material ensemble.
Joint motif/marking learning, informative transfer and successful reconstruction
of every family member remain unresolved. More time-budget experiments alone
would not establish those advances.

## Reproduce

```
node test-composed-point-proofs.mjs KERNEL
python test-composed-proof-verifier.py
node boron-face-reference-search.mjs PRECHECK_V2 CONNECTED_LEARNING KERNEL OUTPUT_FOLDER linear-composed
python verify-boron-face-search.py PRECHECK_V2 CONNECTED_LEARNING OUTPUT_FOLDER FILLING_CHECK
python verify-boron-composed-proofs.py OUTPUT_FOLDER CONNECTED_LEARNING PROOF_CHECK
```

Use new output paths. Run artifacts contain source hashes, the full model,
selected placements, registered clauses and the proof graph. Public summaries
contain counts and hashes, not atomic coordinates or derived coordinate models.
The production kernel and growth app remain unchanged.
