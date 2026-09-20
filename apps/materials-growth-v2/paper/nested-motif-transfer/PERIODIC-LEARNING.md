# Frozen learned interfaces on the periodic candidate graph

20 September 2026. Follow-up to [PERIODIC-CONNECTIVITY.md](PERIODIC-CONNECTIVITY.md).

## Model and split

Use the unchanged nested motif dictionary, 120 fitting plus 44 evaluation
frames per phase, and the periodic Voronoi candidate generator. Fitting
contains 120 admitted alpha frames and 119 beta frames; one beta frame has
an incomplete recurring-motif partition and is explicitly excluded.
All 88 evaluation frames have complete motif partitions.

Each candidate is an ordered pair of motif roles and an integer lattice
image shift. Unlike the nearest-neighbor pilot, different images of one
pair are different observations, and self-image edges remain nonzero. No
minimum-image collapse is applied to the stored displacement.

Fit off-atom endpoint locations and transported vector values using the same
greedy training-only procedure and priors as [OFFATOM.md](OFFATOM.md). The
maximum pair-position, pair-value and displacement-target errors remain
0.30 Å. Each pair supplies midpoint witnesses of radius 0.15 Å. Atom poses
remain those of the frozen nested dictionary, with the original 0.15 Å
registration tolerance; no continuous optimization is applied in this lane.

All proposed training pairs fit by model splitting, but evaluation and the
reported matched graphs use only models seen in at least two fitting frames.
An unobserved pair remains unsupported, not physically or mathematically
proved forbidden. The graph need not retain every Voronoi edge: those edges
are a candidate domain, not mandatory bonds.

## Results

3,241 models were fitted, of which 754 recur in two or more fitting frames.
Only four fitted models occur across both crystal forms. This indicates a
fragmented, context-specific representation; it is not evidence that the
phases inherently require different markings. The source poses and greedy
dictionary assignments can also contribute to fragmentation.

| Phase / split | Admitted frames | Candidate edges | Recurring-model matches | Connected periodic matched graphs |
|---|---:|---:|---:|---:|
| alpha fitting | 120 / 120 | 3,031 | 1,087 | 42 |
| alpha evaluation | 44 / 44 | 1,290 | 229 | 4 |
| beta fitting | 119 / 120 | 1,743 | 1,198 | 80 |
| beta evaluation | 44 / 44 | 663 | 365 | 23 |

The complete record contains 6,727 candidate observations, including 1,647
self-image observations. All parameters are frozen before evaluation.

For every matched pair, the same fixed motif pose transports its atoms,
anchor and vector value. Thus this lane does not combine independently
optimized poses for a shared motif. Connectivity means paths to every motif
in the reference cell and to all three unit translations; rank three without
index one is insufficient. Independent integer path witnesses verify every
reported positive matched graph, including the 27 evaluation cases.

These counts do not compare directly with the earlier 3/44 and 29/44 shared-pose
results: that experiment used a different, insufficient nearest-neighbor
graph, different learned models and additional pose optimization.

## Verification

The verifier replays source motif geometry, training-only model membership,
explicit image displacements, transported point/value agreement and common
pair witnesses. It checks every configuration's candidate edge set and
replays constructive paths in the accepted periodic graphs. Corruption
controls reject a self-image collapsed to the same cell, erased image
displacements, invented recurrence, altered markings and omitted evaluation
observations. Numerical Voronoi regeneration is a consistency check, not an
independent exact-arithmetic tessellation certificate.

The largest checked pair-position, pair-value and target residuals are
0.299990843264, 0.299947697893 and 0.299990843264 Å respectively. Positive checks
use numerical slack 10^-9 Å. This is not an exact geometric certificate.

## What this does not yet establish

This experiment learns interfaces on an outward-connected candidate domain;
it is not a GCTS tiling or growth result. We have not learned positive
t-support, assembled reusable complete motif decorations, or checked all
cross-interface coincidences and common values at multi-way overlaps.
An abstract connected graph with valid pairs can still fail those tests.
Missing marking overlap remains unconstrained; it is not rejection.

Anchor endpoint roles are prescribed per pair; model count is chosen greedily.
Free support count, positions and t/m values are not jointly optimized. Source
coordinates are still supplied. The source-order split is developmental,
not an independent-trajectory test; same-condition provenance remains
unverified. No performance advantage, physical validity or blind growth is
claimed. Production material growth and its reference scheduler are unchanged.

## Reproduce

After creating `cohort` and `nested.json` as described in README.md, keep the
scripts from this directory together:

```sh
python learn-periodic-interfaces.py cohort/coordinates.json cohort/metadata.json nested.json periodic-interfaces.json
python verify-periodic-interface-learning.py cohort/coordinates.json cohort/metadata.json nested.json periodic-interfaces.json periodic-interface-check.json
python test-periodic-interface-learning.py cohort/coordinates.json cohort/metadata.json nested.json periodic-interfaces.json
```

The learner reuses the frozen definitions in `learn-offatom-interfaces.py`
and `periodic-interface-proposals.py`; source hashes are recorded. The
verifier also uses the existing motif and periodic path checkers. Full
coordinate-bearing models are regenerated rather than bundled; the public
receipt binds the result, coordinates, metadata and motif dictionary hashes.
