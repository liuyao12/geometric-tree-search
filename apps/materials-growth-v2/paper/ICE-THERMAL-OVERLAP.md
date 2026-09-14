# Thermal ice: overlapping motifs and the reconstruction gap

14 September 2026. Follow-up to ICE-DFT-REPORT.md. This is a finite supplied-coordinate
experiment, not blind growth or a demonstrated useful marking model.

## Fixed pilot and geometric candidates

The previously specified pilot contains the first 25 training and first 25
validation frames of each of Ih, II, VI and VIII: 100 training and 100 validation
frames. It preserves the author's split, not independent trajectories.

The existing training-only distance-gap component rule recovers three-atom
components. Applying another largest-gap rule to intercomponent minimum distances
fails: some inputs have no proposed connections. A declared broader proposal
radius, 1.5 times the training median nearest-intercomponent distance, supplies
pair unions. This is a restricted geometric proposal heuristic, not a learned
bonding law or complete continuous candidate enumeration.

Each six-site union is periodically lifted and registered to training representatives
using species-preserving permutations, continuous proper rotations and translation.
Maximum per-site residual is fixed at 0.15 Å. Sorted pair distances provide a
necessary rejection filter; accepted fits have explicit rigid witnesses. Failure
of the registration heuristic is not proof that no tolerance-feasible fit exists.
No reflections are allowed. The dictionary is frozen before validation, with
350 types, including 66 seen only once in training. These are tolerance-based
representative groups, not exact isometry classes or proof of a minimal dictionary.
Species are categorical inputs; no coordination or chemistry rules are imposed.

## The all-occurrences fit has a zero-weight loophole

A shared-site linear program maximizes the minimum t-value subject to all training
point sums being one. Its returned solution passes an independent exact rational
sum check, but sets 1,734 of 2,100 sites to zero and makes 166 entire types empty.
Empty t-support is not a valid nontrivial base tile. This witness is therefore a
diagnostic failure of this fitting setup, not an admitted growth library. No exact
infeasibility certificate for alternative positive fits is claimed.

Training overlap equalities produce only two maximal scalar m-classes. They add
no observed constraint beyond element compatibility in the subsequent search.

## Positive selection control versus reference tree search

We tested a separate uniform-weight hypothesis, t=1/2 on every site. A specialized
MILP selects pair unions with degree two at each component and enforces connectedness
using cuts. All 200 configurations admit such a connected positive cover. Independent
integer point totals, species/pose checks and graph connectivity verify these witnesses.
The value 1/2 is a tested hypothesis, not a learned optimum; the connectivity cuts
are not GCTS markings. Small controls include 30 exhaustive five-vertex cases and
an odd-degree graph with a single bridge, ensuring cut parity is handled correctly.

We then pass the **entire matched candidate pool**, not the MILP-selected answers,
to the unchanged reference PointSearch kernel. Every supplied target atom is an
explicit generation-zero root. Capacity is two, each positive site contributes one
integer unit, and each placement is selectable once. There is no additional
connectivity constraint. The lanes differ only by scalar markings. Budgets are
10,000 advances / one second per configuration per lane, checked between advances.

| Validation phase | Cases | Connected MILP covers | Reference exact covers, each lane | Reference connected covers, each lane |
| --- | --- | --- | --- | --- |
| Ih | 25 | 25 | 22 | 4 |
| II | 25 | 25 | 25 | 3 |
| VI | 25 | 25 | 25 | 1 |
| VIII | 25 | 25 | 25 | 0 |

Each reference lane returns 97 exact finite point covers, only eight with a
connected positive-support graph. Three Ih cases reach the budget, not a proof
of impossibility. Both lanes have identical aggregate branch/backtrack counts.
No GCTS advantage is demonstrated. Disconnected point covers are valid for the
declared finite point model; they expose its mismatch with a connected growth
objective, rather than a base-search bug. Connectedness alone would still not
establish correct long-range material structure.

## Verification and remaining gaps

The harness checks global dead/forced/generation ordering each advance, audits
incidence every 50 advances and at completion, and restores the root semantic
state. Independent Python checks replay selected point totals, marking agreements
and positive-support connectivity. Kernel SHA-256:
`747db2cb5e626968d4bbf18fc1cb804b4a66ad2f177f3d5b097bc4b53257ba85`.
This is not a new full kernel conformance certification or continuous-pose
completeness proof. Geometry is approximate; point arithmetic is exact.

The next target is joint occurrence/anchor/t/m learning that avoids zero-support
degeneracy and transfers useful connection constraints. Both disconnected results
and the unresolved Ih cases must remain tests. Enlarging tolerance, replacing
the reference search with the MILP, or merely requiring connectivity cannot be
reported as solving that target. No test-specific motifs were added in this run.

## Reproduce

After acquiring the corpus and creating the existing 200-frame pilot:

```
python ice-overlap-cover.py PILOT/coordinates.json PILOT/components.json PILOT/overlap-broad.json radius-upper
python ice-thermal-dictionary.py PILOT/coordinates.json PILOT/overlap-broad.json 0.15 PILOT/dictionary.json
python verify-ice-thermal-dictionary.py PILOT/coordinates.json PILOT/overlap-broad.json PILOT/dictionary.json PILOT/dictionary-check.json
python ice-thermal-selection.py PILOT/overlap-broad.json PILOT/dictionary.json 2 PILOT/selection.json
python verify-ice-thermal-selection.py PILOT/dictionary.json PILOT/selection.json PILOT/provenance.json PILOT/selection-check.json
node ice-thermal-reference.mjs PILOT/dictionary.json ../kernel.mjs PILOT/reference.json
python verify-ice-thermal-reference.py PILOT/dictionary.json PILOT/reference.json PILOT/provenance.json PILOT/reference-check.json
python test-ice-thermal-selection.py
```

Python requires NumPy, SciPy, ASE and NetworkX. Keep ice-motif-dictionary.py next
to ice-thermal-dictionary.py. Source data and derived coordinate dictionaries are
not rehosted pending source-license clarification; aggregate checks and scripts
are published. Prior cohort and trajectory caveats remain unchanged.
