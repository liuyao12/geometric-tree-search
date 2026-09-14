# Boron scalar markings are sensitive to training-cover choice

14 September 2026. Follow-up to the single-cover reference-search pilot.

## Training-only experiment

For each of six leave-one-configuration-out folds, keep the five training
configurations, frozen geometric dictionary and previously chosen k=3. Generate
eight additional valid covers for each training configuration by seeded
candidate-order shuffles in the subset solver. Pool their positive marking
equalities with the original selected cover, using the same template symmetry
ties and leaving unobserved components unassigned.

All nine covers of each training configuration are distinct. The independent
verifier checks 270 integer covers across the folds, including the 30 original
covers. These are **alternative decompositions of existing coordinates**, not
270 independent atomic configurations, material samples or physical ensemble
members. No held-out coordinates enter generation or marking learning.

| Omitted model | 1 cover/input | 2 covers/input | 3 covers/input | 5 covers/input | 9 covers/input |
| --- | ---: | ---: | ---: | ---: | ---: |
| alpha | 46 | 26 | 16 | 5 | 1 |
| beta-105 | 42 | 19 | 14 | 7 | 3 |
| beta-106 | 37 | 25 | 16 | 7 | 1 |
| gamma | 43 | 29 | 17 | 5 | 2 |
| tau-105 | 58 | 29 | 13 | 6 | 3 |
| tau-106 | 19 | 15 | 18 | 10 | 4 |

Entries are observed scalar equality classes. Old components can merge while
newly observed variables introduce additional classes, so total class count
need not decrease at every step. Final assigned-variable counts are 2250,
2244, 1932, 2196, 2157 and 1479, respectively. Unobserved variables remain
unassigned, rather than being assigned arbitrary negative labels.

The original markings conflict with 39, 32, 39, 32, 32 and 32 of the forty
additional covers in each fold: 206/240 in total. These are valid unmarked
weighted covers of the same training structures. This demonstrates sensitivity
to cover selection. It does not prove that a useful learned marking must retain
every possible cover: a chosen restricted representation could still support
all desired structures. That preservation and usefulness must be demonstrated.

## Search with the frozen nine-cover marking

Keep the candidate IDs, order, t data, inventory identities, target points,
kernel and budgets fixed to the previous pilot. Re-export only m assignments.
Both marked and unmarked runs now finish all six finite targets. Independent
checks verify the training marking partitions, integer target coverage, marking
agreement and inventory uniqueness. Runtime checks independently rebuild the
candidate graph and verify root point/mark/graph rollback.

| Omitted model | Unmarked backtracks | Nine-cover marked backtracks |
| --- | ---: | ---: |
| alpha | 3 | 3 |
| beta-105 | 21 | 21 |
| beta-106 | 0 | 0 |
| gamma | 258 | 258 |
| tau-105 | 843 | 843 |
| tau-106 | 78707 | 78700 |

The unmarked models, selected IDs and counters exactly reproduce the previous
pilot. The first five marked runs have identical selected IDs and counters to
their respective baselines. For the first four, no target point even has two
different assigned labels across the candidate pool; markings cannot cause
a conflict in those fixed models. Tau-105 has 16 such points but no change to
this search trajectory. Tau-106 has four and saves seven backtracks, with no
demonstrated runtime or end-to-end advantage.

Marked component counts are 1, 4, 1, 1, 1, 1, the same as unmarked counts.
The disconnected beta-105 cover still does not establish single-seed growth.
The earlier large tau-105 backtrack reduction disappears under this pooling
protocol, and marked tau-106 no longer reaches the step budget.

## Interpretation and limits

The single-cover labels were not stable under additional geometric cover
choices. Pooling makes this scalar hypothesis less restrictive on these
observations, but largely removes its effect on search. Adding assignments at
previously unmarked sites can introduce constraints, so pooled models are not
automatically monotone relaxations of earlier models in general.

This is a robustness diagnostic, not evidence that all nonconstant markings or
GCTS must fail. It argues against claiming the previous labels as established
material connection rules. A richer representation—potentially learned anchor
domains, transformation-aware values, or explicit marked motif variants—must
be tested without silently encoding a known tiling or its chemistry.

The fixed candidate models still use known target positions, atom-ID coverage,
approximate Kabsch registration, and a limited periodic-image representation.
All target points are generation-zero roots; this is finite reconstruction,
not connected seed growth or complete continuous-space search. The data are
not an independent common-temperature/pressure ensemble. No production growth
rules were changed and no GCTS speedup is claimed.

## Reproduction

Use the previous boron holdout, selected-training and reference-search artifacts.
Keep the helper scripts from those reports beside the new scripts. Output
directories must be new.

```
python boron-cover-ensemble.py boron-holdout boron-selected boron-cover-ensemble
python verify-boron-cover-ensemble.py boron-holdout boron-selected boron-cover-ensemble cover-checks.json
python export-boron-ensemble-marks.py boron-cover-ensemble boron-pooled-marks
node boron-reference-search.mjs boron-alternatives boron-pooled-marks boron-selected /path/to/kernel.mjs boron-pooled-search boron-search
python verify-boron-reference.py boron-holdout boron-alternatives boron-selected boron-pooled-marks boron-pooled-search search-checks.json boron-cover-ensemble
```

The final search argument fixes the earlier candidate universe. The final
verifier argument requests independent reconstruction of the pooled, rather
than single-cover, marking graph. Public summaries omit source coordinates.
