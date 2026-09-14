# Frozen-library validation beyond the ice pilot

14 September 2026. Remaining 300 author-validation configurations: 75 each of
Ih, II, VI and VIII, frames 25–99 of each released validation file. These were
not used in pilot motif, weight or marking fitting. They had previously undergone
basic corpus/component checks. The author's split is not an independent-trajectory
holdout, and file-level condition provenance remains incomplete.

## Frozen model and admission

Use the existing 350 geometric representatives without any new templates,
tolerance adjustment or distance-threshold recalibration. The trained maximum
site residual remains 0.15 Å (a fixed experiment setting, not an optimized error
bar). Admit the 347 types for which all six site weights are forced to 1/2 by the
targeted training equations. The remaining three types remain recorded but are
not supplied with guessed weights. This is a declared learned-library admission
rule, not proof that those three geometric types are impossible.

The unchanged radius proposal produces 83,564 pair-union occurrences; 83,218 have
witnessed fits to admitted types. An independent periodic-image/KD-tree audit
reconstructs the candidate supports, verifies all accepted proper rotations and
species correspondences, and checks unchanged templates, tolerances, thresholds,
source coordinates and exclusion from the pilot. Maximum accepted residual is
0.14999936 Å. Failed registration is not a complete continuous non-match proof.

## Existence versus search

The specialized connected degree-two selection control finds exact positive
covers for all 300 configurations. Independent integer point totals and graph
checks verify them. The reference search receives the full registered candidate
pool, not these selected answers. It activates all supplied target atoms at
generation zero and uses exact capacity-two arithmetic.

| Phase | Configurations | Connected selection-control covers | Reference exact covers | Reference connected covers | Parent-exclusion exact covers | Parent-exclusion connected covers |
| --- | --- | --- | --- | --- | --- | --- |
| Ih | 75 | 75 | 64 | 20 | 66 | 21 |
| II | 75 | 75 | 75 | 4 | 75 | 4 |
| VI | 75 | 75 | 75 | 3 | 75 | 3 |
| VIII | 75 | 75 | 75 | 0 | 75 | 0 |
| Total | 300 | 300 | 289 | 27 | 291 | 28 |

Counts are per lane; adding the current scalar markings leaves each result
unchanged. Budgets are 10,000 advances and one second per case, tested between
advances. Incomplete results are unknown, not untileable. The branch-exclusion
variant records failed choices only in their justified parent context and rolls
those exclusions back. It preserves global dead/forced/generation ordering.
It is separately labeled, not silently substituted for the reference baseline.

The existing exclusion tests were rerun: 150 exhaustive small models across two
variants, 1,145 inspected states and 176 failed choices, preserving completions
and root rollback. Both large-run harnesses audit graph incidence periodically,
check decision priority each advance, and restore the root semantic state.
Independent final-state verification checks every selected occurrence, point sum,
marking agreement and positive-support component count. This is not a full new
kernel conformance certification or an unrestricted geometric search proof.

## Interpretation

The model transfers beyond the pilot sufficiently to admit connected finite
covers throughout the remaining validation set. It does not yet reliably find
them through the intended search: even the exclusion control leaves nine cases
unknown, and most completed point covers have disconnected positive-support
graphs. Connectedness alone would still not prove the correct long-range material
structure. No GCTS acceleration, physical growth law or blind extrapolation is
demonstrated. Concurrent diagnostic jobs are not a controlled wall-time comparison.

These new outcomes are kept separate from the pilot results. They do not justify
retroactively choosing a tolerance or calling a selected-cover existence witness
a successful growth run. Context-sensitive markings, general occurrence/weight
learning, and reconstruction without the supplied coordinate pool remain open.

## Reproduction

```
python ice-frozen-validation.py CORPUS PILOT_DICTIONARY PILOT_COVER TRAINED_WEIGHT_MODEL OUTPUT
python verify-ice-frozen-validation.py OUTPUT PILOT_DICTIONARY TRAINED_WEIGHT_MODEL OUTPUT/registration-check.json PILOT_COVER CORPUS
python ice-thermal-selection.py OUTPUT/cover.json OUTPUT/dictionary.json 2 OUTPUT/selection.json
node ice-thermal-reference.mjs OUTPUT/dictionary.json ../kernel.mjs OUTPUT/reference.json
node ice-thermal-reference.mjs OUTPUT/dictionary.json ../kernel.mjs OUTPUT/exclusions.json branch-exclusions
python verify-ice-frozen-results.py OUTPUT/dictionary.json OUTPUT/selection.json OUTPUT/provenance.json OUTPUT/selection-check.json
python verify-ice-frozen-results.py OUTPUT/dictionary.json OUTPUT/reference.json OUTPUT/provenance.json OUTPUT/reference-check.json
python verify-ice-frozen-results.py OUTPUT/dictionary.json OUTPUT/exclusions.json OUTPUT/provenance.json OUTPUT/exclusions-check.json
node test-branch-local-exclusions.mjs ../kernel.mjs
```

Keep branch-local-exclusions.mjs beside the harness, and residual-capacity-filter.mjs
beside its existing test. Python requires NumPy, SciPy, ASE and NetworkX. Source
coordinates and derived coordinate dictionaries are not rehosted; scripts and
aggregate verification evidence are published.
