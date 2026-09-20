# Off-atom interface pilot — a negative transfer result

19 September 2026. This is a diagnostic, not a GCTS growth rule.

The [nested motif experiment](README.md) covers both crystal forms, but
does not constrain how the pieces connect. We tested a first train-only
model of off-atom interface points on those saved motif partitions.

## Declared model

Each motif proposes the nearest other motif by periodic centroid distance;
the undirected union supplies pair observations. This is an explicit,
restricted geometric proposal prior, not a complete physical connection graph.
Pairs are keyed by their two dictionary types. Equal types retain endpoint
roles; symmetry-equivalent role exchanges are not silently quotiented.

For observed rotations RA, RB and periodic centroid displacement d, learn
six continuous coordinates xA, xB to fit

    xA RA − xB RB = d.

Least squares fits all observations assigned to a model. Its null-space
gauge is chosen nearest the mean observed midpoint coordinates. The points
are not pinned to atoms or fixed midpoints; an eight-pose synthetic test
recovers prescribed non-midpoint anchors at full rank. Single-pose rank is
only three: such points are underdetermined, not uniquely learned geometry.

Each endpoint also learns the mean local displacement vector. These vector
values transform with its motif's rotation. Using displacement as a target
is a representation prior to avoid the vacuous all-zero equality solution.
It is not an energy, chemical bond or formation-history assumption.

Greedy training-only model splitting accepts a refit only if every member
passes: anchor separation ≤ 0.30 Å, transported value separation ≤ 0.30 Å,
and each value within 0.30 Å of its observed displacement target. The first
two tests supply pairwise midpoint witnesses in radius-0.15 balls. A pairwise
witness is not a certificate for a larger overlap group. Evaluation requires
at least two fitting frames supporting a frozen model. No evaluation refits.

## Independently checked result

306 models, 59 recurring; 612 endpoint anchors. All anchors are more than
0.15 Å from their corresponding template atoms. Median radius from motif
origin is 2.00 Å; maximum is 9.65 Å. No locality bound was imposed, so large
anchor excursions are a failure to address, not evidence of useful reach.

| Evaluation form | Matched pair proposals | Frames with every proposed pair matched |
|---|---:|---:|
| alpha | 2 / 99 | 0 / 44 |
| beta | 15 / 49 | 15 / 44 |

Ordered diagnosis across all 148 pairs, evaluating the finite frozen models:

- 19: no recorded model for the type pair;
- 12: models exist but none recur in two fitting frames;
- 82: eligible models fail anchor coincidence;
- 14: anchors can meet, but transported values fail agreement;
- 4: anchor/value agreement passes, but the displacement-target prior fails;
- 17: a model passes all three tests.

These are failures of this representation and proposal scheme. They do not
prove the observed connections impossible or illegal.

**Critical semantic limitation:** missing marking overlap means unconstrained
in GCTS. A missed interface cannot be treated as a marking rejection. We have
not learned positive t-support requiring the interface to be filled, combined
pair models into reusable full tile decorations, or verified global overlap
consistency. This diagnostic is not installed in the production search.

## Verification and reproduction

The checker independently reconstructs periodic displacements with a certified
finite image enumeration, checks the entire nearest-pair proposal set against
saved motif poses, training-only recurrence, positive positions/values, and
common pair witnesses. It exhausts the recorded eligible interface models
for the failure breakdown, not arbitrary continuous registrations. Base
motif correctness is checked by the preceding nested-motif verifier.

Controls reject displaced anchors, altered markings, invented recurrence,
omitted pairs and changed source displacements. A synthetic fit verifies
free-position recovery and records the single-observation rank deficiency.
Condition-matched cohort provenance remains unresolved.

After reproducing `cohort` and `nested.json` as described in README.md:

```sh
python learn-offatom-interfaces.py cohort/coordinates.json cohort/metadata.json nested.json interfaces.json
python verify-offatom-interfaces.py cohort/coordinates.json cohort/metadata.json nested.json interfaces.json interface-check.json
python test-offatom-interfaces.py cohort/coordinates.json cohort/metadata.json nested.json interfaces.json
```

The public check receipt binds these results to their source/model hashes.
Coordinate-bearing full models are regenerated, not redistributed here.
