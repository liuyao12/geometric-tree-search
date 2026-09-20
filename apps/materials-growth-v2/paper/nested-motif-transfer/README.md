# Nested recurring motifs: oxalic-acid family diagnostic

19 September 2026. Developmental geometric experiment, not a growth result.

## Source and cohort

Source: [MolCrys-MACE](https://github.com/water-ice-group/MolCrys-MACE/tree/36a5da6583bdce806d4e5ece5c4c0e355076a887), pinned commit
`36a5da6583bdce806d4e5ece5c4c0e355076a887`.
The acquisition script reads the alpha and beta TRAIN.traj files with ASE;
it does not execute the repository's scripts or models. Coordinates are not
redistributed in this report.

For each phase, retain the modal atom count (alpha 32, beta 16): 164 frames.
The first 120 eligible frames fit the dictionary; the remaining 44 evaluate
it. These source-order splits are not independent-trajectory holdouts.
The released simulation input decks say 298 K and 1 bar, but do not establish
the conditions of these TRAIN.traj frames. No frame is admitted as verified
condition-matched. Metadata is separate from the geometric learner.

## Algorithm

The earlier persistence-score method chose one disjoint single-linkage cut
before learning its dictionary. The new method retains every non-root,
non-singleton node of that hierarchy as a proposed irregular point cloud.
Periodic coordinates are lifted along short connecting edges. A greedy
training-only dictionary registers species-preserving proper rotations with
maximum residual at most 0.15 angstrom. Dictionary references are source
clouds, not jointly optimized anchor positions. Each correspondence search
is bounded at 20,000 nodes; budget exhaustion means unknown.

Only types matched in at least two distinct fitting frames are eligible.
After freezing the dictionary, dynamic programming selects a hierarchical
partition: first minimize uncovered atoms, then minimize the number of
pieces. Singletons represent failures, not learned successful motifs.
This is not the GCTS tree search, and does not modify its scheduler.

## Observations

| Evaluation phase | Previous cut | Nested recurring cut |
|---|---:|---:|
| alpha | 3 / 44 | 44 / 44 |
| beta | 41 / 44 | 44 / 44 |

The raw dictionary has 291 types, of which 92 recur in fitting frames and
24 recur across both fitting phases. Those shared types have sizes 2 (two
types), 3 (one), 4 (four), and 8 (seventeen). They are approximate registered
representatives, not certified exact isometry classes.

Selected evaluation pieces: alpha has 157 eight-atom, five sixteen-atom,
16 four-atom and four two-atom pieces; beta has 83 eight-atom, nine four-atom
and two two-atom pieces. Every evaluation atom belongs to exactly one piece.
The maximum independently replayed positive registration error across all
recorded proposals is 0.149996470912 angstrom.

Independent checks replay source-template geometry, all positive poses,
training recurrence, partitions and cut cost within the supplied hierarchy.
Controls reject altered recurrence, evaluation-sourced templates, an omitted
piece, a shifted pose and a reflected pose. Separate rigid matcher controls
cover rotated/permuted 8/16/32-point clouds, exhaustive six-point comparisons,
reflection rejection and explicit budget stops.

## Interpretation and limitations

Retaining subclusters resolves a specific transfer failure. It also makes
the representation less restrictive: smaller pieces can fit more structures.
This is not evidence of correct connections, improved GCTS search, physical
validity, joint anchor/t/m learning, or growth beyond supplied coordinates.
Tree ties, greedy dictionary order and approximate non-transitive matching
remain limitations. The proposal universe is not exhaustive continuous geometry.
The next test must learn and validate connections between these pieces.

## Reproduce

Python environment used: Python 3.12, NumPy 2.5.3, SciPy 1.18.1, ASE 3.29.0.
Fetch the linked scripts in this directory into one working directory.
Output paths below must not already exist.

```sh
python acquire-molcrys-polymorphs.py source
python verify-molcrys-polymorphs.py source source-check.json
python prepare-modal-cell-cohort.py source/coordinates.json source/provenance.json cohort
python persistent-component-proposals.py cohort/coordinates.json cohort/metadata.json baseline.json
python verify-persistent-components.py cohort/coordinates.json cohort/metadata.json baseline.json baseline-check.json
python nested-recurring-motifs.py cohort/coordinates.json cohort/metadata.json nested.json
python verify-nested-recurring-motifs.py cohort/coordinates.json cohort/metadata.json nested.json check.json
python test-nested-recurring-motifs.py cohort/coordinates.json cohort/metadata.json nested.json
python test-bounded-rigid-registration.py
```

Saved check files bind results to coordinate/metadata hashes. Full local
results contain coordinate-bearing templates, so are regenerated rather than
bundled here. The graph is a presentation of these saved counts, not a new
experiment. The original single-scale baseline was independently replayed
again on 19 September before making this comparison.
