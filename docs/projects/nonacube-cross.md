# Nonacube cross with two-unit arms

The tile consists of nine unit cubes, with lower-corner coordinates

\[
P=\{(0,0,0),(\pm1,0,0),(\pm2,0,0),(0,\pm1,0),(0,\pm2,0)\}.
\]

It is a flat four-arm cross, not the six-arm tridecacube already in the catalogue.
Proper cubic rotations give three distinct orientations. Reflections add none.

## What is established

As checked on 2026-09-23, we have not located a space-tiling certificate or a
published exact three-dimensional Heesch number for this shape. This is a
statement of the evidence found, not a claim that the question is an established
open problem in the literature.

The shape is entry 25373 (zero-based) in Georgios Papoutsis's
[nonocube input catalogue](https://github.com/gepa71/whuts-solver/blob/main/inputs/all_nonocubes.json).
Its [solution file](https://github.com/gepa71/whuts-solver/blob/main/results/nonocube_solutions/solution_25373.json)
is empty. The author's [description of the search](https://math.stackexchange.com/a/4150301)
explicitly says that failing to find a periodic tiling does not prove non-tiling.

We computed one complete surrounding corona and independently verified it by
integer voxel replay. Thus the three-dimensional Heesch number satisfies
\(H\geq1\); its exact value is not established here. The certificate has 34
copies around the central tile. Every one touches the central tile, the copies
are pairwise nonoverlapping, and all 90 exterior voxels meeting the central tile
at a face, edge, or vertex are filled. Consequently the entire central tile is
inside the interior of the union. This is stronger than filling only its
face-adjacent cells. No minimal surround-number claim is made.

[Download the corona coordinates](../../data/nonacube-cross-corona.json).
Replay the certificate with `node scripts/verify-nonacube-cross.mjs`.
The finite packing was obtained from exact Boolean constraints: enumerate every
orientation and every support alignment at the 90 required cells, remove root
overlaps, require one cover per required cell and at most one cover at every
candidate voxel, including exterior voxels. There are 686 candidate placements.
This auxiliary SAT calculation is a specialized certificate search, not a GCTS
benchmark or an implementation of the reference growth scheduler.

## App model and conformance scope

The new catalogue entry uses the existing center-and-corner point model in v2:
full capacity at voxel centers and exact eighths at corners, cubic rotations,
and integer physical translations. The legacy explorer also registers the
same nine voxels. No search scheduler, marking, rollback, or learning rule was
changed. The checked witness is evidence only for a finite geometric corona;
it does not train the browser learner or seed its growth search. The existing
point-model and geometric-scope limitations remain in force. Neither a finite
growth checkpoint nor a bounded periodic miss determines the Heesch number.

## Certified exclusions first

The app now defaults this tile to the [certified negative-only marking method](3d-certified-exclusion-markings.md). The initial short checks certified no invalid pair orbits, so the lane explicitly falls back to unmarked search. This does not change the Heesch-number evidence above.
