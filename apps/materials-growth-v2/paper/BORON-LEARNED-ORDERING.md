# Shared motif contexts: transfer exists, reconstruction remains unresolved

14 September 2026. A learned ordering control, not a new GCTS marking or a
wholly held-out model test. This returns from proof engineering to learning
from the family of observed configurations.

## Two learned preferences

For each target structure, withhold its selected training filling from the
ranking calculation and use only the other five structures' selected witnesses.
The first score is `(selected + 1) / (observed + 2)` for each motif type.
An unobserved type receives one half. Exact rational ordering is converted to
integer ranks, avoiding floating-point tie ambiguity.

The second score conditions on an overlap-context descriptor. For an occurrence,
record its motif type and the multiset of neighboring motif types with their
shared symmetry-role pairs. The feature contains neither atomic IDs nor world
coordinates, absolute orientation bins, species rules or target selection labels.
It is a coarse invariant of the frozen candidate-incidence model, not a complete
geometric descriptor of the surrounding material. Different geometric contexts
can collapse to the same feature. An unseen context falls back to the type score.

Scores only order legal candidates at the already chosen earliest-generation
point. Global dead points and forced moves retain priority; the complete candidate
pool, integer t-values and scalar m-values are unchanged. No low-score or unknown
context is rejected. The engine uses the existing parent-exclusion control and
linear frontier scheduler, with no composed-proof plug-in in these runs.

## What actually transfers?

An independent construction from shared point-incidence pairs reproduces every
context hash and ranking. Holding out the target's witness yields:

| Target | Shared context classes / target classes | Occurrences with shared context | Shared classes with mixed training-selection labels |
| --- | ---: | ---: | ---: |
| α | 0 / 2 | 0 / 108 | 0 |
| β-105 | 6 / 12 | 567 / 1,458 | 0 |
| β-106 | 27 / 90 | 2,268 / 4,779 | 7 |
| γ | 0 / 6 | 0 / 486 | 0 |
| τ-105 | 6 / 25 | 1,026 / 2,916 | 0 |
| τ-106 | 27 / 133 | 2,565 / 7,884 | 6 |

The hard structures therefore share nontrivial local descriptors with the other
family members. But some matched classes contain both selected and unselected
occurrences in the source witnesses. A deterministic classifier on this feature
alone cannot reproduce all those particular labels. That is **not** a proof that
local rules cannot reconstruct the material: the selected decomposition is not
unique, and rejecting one witness does not rule out another correct filling.

These counts are not independent material observations. Periodic images and
repeated occurrences contribute to them. The smoothed fractions are descriptive
ranking heuristics, not calibrated physical attachment probabilities or a
thermodynamic distribution.

## Search outcome

Each ranking is tested on all six targets, marked and unmarked: 24 runs in total,
with 100,000-advance / 15-second per-run limits. Both rankings complete α, β-105,
γ and τ-105 with connected exact covers in both lanes. Neither resolves β-106
or τ-106. Independent verifiers check the model reconstruction, final point sums,
marking consistency, connectivity, ranking counts and run-to-prior hashes.

No speedup or additional completed reconstruction is established. Throughput,
partial filling and backtracking counts at wall-time endpoints are not proxies
for success. Repeated ordering experiments should not substitute for solving
the underlying joint motif/occurrence/marking-learning problem.

## Withholding and invariance checks

- Clearing the target's selected witness leaves its learned ranking unchanged
  in all six folds, for both ranking methods.
- Type-score tests check 1,536 exact rational rank comparisons.
- Renumbering atom IDs and reversing occurrence enumeration preserve context
  features after the corresponding permutation. This does not test re-running
  noisy geometric registration under arbitrary rotations; the input dictionary
  and transported role assignments are fixed here.
- Independent context verification constructs neighbor relations via unordered
  incidence pairs rather than the learner's per-occurrence traversal.

The geometry dictionary and shared t/m model were previously fitted jointly on
all six inputs. Withholding applies **only to the preference learner**, not the
whole pipeline. Do not call these held-out material reconstructions, independent
same-condition ensemble results or learned matching-rule generalization.

## Consequence for GCTS

The family does supply shared motif-overlap information, but copying selection
frequencies is insufficient. The next learning objective must account for the
existence of compatible covers and alternative decompositions, rather than
equating one selected witness with the only valid way to assemble the atoms.
The new preferences are safe to investigate because they do not become hard
exclusions. They have not yet supplied the transferable m-values or successful
all-family growth sought by the project.

## Reproduce

```
python boron-type-priors.py INPUT LEARNING TYPE_PRIOR
python boron-context-priors.py INPUT LEARNING CONTEXT_PRIOR
python test-boron-type-priors.py INPUT LEARNING
python test-boron-context-priors.py INPUT LEARNING
node boron-face-reference-search.mjs INPUT LEARNING KERNEL TYPE_RUNS linear-exclusions 100000 15 type-prior TYPE_PRIOR
node boron-face-reference-search.mjs INPUT LEARNING KERNEL CONTEXT_RUNS linear-exclusions 100000 15 context-prior CONTEXT_PRIOR
python verify-boron-type-priors.py INPUT LEARNING TYPE_PRIOR TYPE_RUNS TYPE_CHECK
python verify-boron-context-priors.py INPUT LEARNING CONTEXT_PRIOR CONTEXT_RUNS CONTEXT_CHECK
python verify-boron-face-search.py INPUT LEARNING TYPE_RUNS TYPE_FILLING_CHECK
python verify-boron-face-search.py INPUT LEARNING CONTEXT_RUNS CONTEXT_FILLING_CHECK
```

Use new output paths and the same `precheck-v2.json` and connected learning
artifact as earlier boron experiments. The type-only run preceded addition of
the context-mode option to the harness. Its exact runner source is preserved
as `boron-type-prior-runner-snapshot.mjs` for source-hash verification, not as
the recommended executable entry point. To verify those archived type-only
results, append that snapshot path to the type verifier command. New runs use
the current harness and need no snapshot override. Public artifacts include
aggregate checks and source snapshots; raw coordinate models stay local.
