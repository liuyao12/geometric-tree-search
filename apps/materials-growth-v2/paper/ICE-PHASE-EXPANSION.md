# Frozen ice-family expansion: model feasibility versus search performance

15 September 2026. Preliminary finite-model evidence, not a discovery or speedup.

The same frozen multi-cover library used for ice VIII was tested on the first
training and first author-test frame of Ih, II and VI. The six IDs were fixed
before search: c00000/c00400, c00500/c00900, c01000/c01400. Author-test frames
are called developmental here: independent trajectories are not established.
The library was trained on all four phases; this is not leave-one-phase-out
transfer. No additional learning or policy tuning occurred in this batch.

## Search outcomes

Both existing candidate-order policies used the same complete finite registered
factorized candidate universe and thirty-second checkpoint budget. The scheduler
remained global dead/forced/earliest-generation. Necessary complementary-support
pruning and full cloud checks were unchanged; both policies restore their roots.
No selected training cover or oracle answer is supplied to the search.

| Phase / split | Atoms | Baseline final placements | Support-rich final placements | Search result |
| --- | ---: | ---: | ---: | --- |
| Ih / training | 384 | 91 | 42 | Both budget-unknown |
| Ih / developmental | 384 | 36 | 46 | Both budget-unknown |
| II / training | 288 | 90 | 30 | Both budget-unknown |
| II / developmental | 288 | 72 | 35 | Both budget-unknown |
| VI / training | 240 | 35 | 37 | Both budget-unknown |
| VI / developmental | 240 | 53 | 17 | Both budget-unknown |

All twelve runs remain unresolved. Final placements are not maximum progress,
atom counts, or a prediction of success under a longer budget. Independent
replay checks all partial t totals, inventory and 1,168 cloud assignments.
There are 40,870 backtracks and zero degree-one forced placements across the
twelve runs. Necessary pruning alone did not make global assembly easy.

Compilation, pruning and conservative index completeness are independently
checked. Pruning preserves all five stored training lifts across the three
training frames. It reduces the six Cartesian pools from 2.18–66.86 million
candidates each to 158,162–515,799 each, without declaring the survivors globally
compatible. Root setup takes 0.14–0.49 seconds. Search timing excludes prior
learning, registration, preprocessing, index construction, file I/O and final
verification. Runs are serial but not a controlled statistical timing study.

## Separate positive-witness diagnostic

After all twelve search runs finished, an explicitly separate mixed-integer
feasibility diagnostic requested connected positive-support covers. It lifts
answers back to the same decorated candidates and supplies common cloud values
for independent replay. This is NOT the reference GCTS tree-search algorithm,
and connectivity is an extra diagnostic condition, not a hidden base rule.

| Phase | Training / developmental placements | Connected full fillings | Verified cloud assignments |
| --- | --- | --- | ---: |
| Ih | 128 / 128 | Both | 512 |
| II | 96 / 96 | Both | 384 |
| VI | 80 / 80 | Both | 320 |

All six positive witnesses pass: 1,824 supplied atom positions in total, 608
placements, 608 common marking values and 1,216 cloud assignments. Every result
has one positive-support component. The three training covers differ from all
their stored training support covers; developmental frames have no training
lift attached. These are alternative decompositions of supplied coordinates,
not newly generated configurations. Positive witnesses establish feasibility;
the diagnostic is not used to prove a negative result or to seed the timed search.

## What changes scientifically?

The shared frozen geometric library admits connected finite reconstructions
across three additional ice phases, including developmental frames. Thus these
six search timeouts cannot be attributed simply to the absence of any complete
compatible filling in the factorized model. The search still revisits many
decorated alternatives without global completion. This broadens the earlier
two-frame VIII diagnosis; it does not establish reliable GCTS reconstruction.

The next algorithmic experiment should improve coordination or learn stronger
markings, while preserving verified supplied fillings and the reference
scheduler. Any use of diagnostic witnesses as new training data must be a new,
explicitly labeled developmental iteration with fresh evaluation—not a claimed
independent rerun of this frozen experiment.

Important limits remain: half-weight t-values are inherited from a chosen
degree-two cover, not learned from scratch. Independent endpoint factorization
broadens the original coupled marking hypothesis. Candidate registration uses
known atom positions and a fixed fitted pose per occurrence, not a complete
continuous-pose enumeration. No growth beyond input coordinates, physical
plausibility, independent holdout, verified same-condition ensemble or rejection
of all wrong connections has been established. Phase and condition labels are
evaluation metadata, not inputs to the geometry learner or search.

## Reproduction and audit

```
python ice-phase-expansion.py PILOT FROZEN_MULTI_LIBRARY NEW_OUTPUT --node NODE
python ice-phase-existence.py NEW_OUTPUT
python summarize-ice-phase-expansion.py NEW_OUTPUT REPORT --include-connected-diagnostic
```

The manifest records the predetermined frame selection and frozen source hashes.
The aggregate checks all source/model/index/proof/result hash bindings. Source
and independent-check files are published; raw coordinate-derived cloud pools
remain local, so the downloads are an audit trail, not a self-contained data
redistribution. Existing source-acquisition and condition-provenance caveats
continue to apply.
