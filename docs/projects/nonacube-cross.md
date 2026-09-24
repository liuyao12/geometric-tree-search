# Nonacube cross with two-unit arms

The tile consists of nine unit cubes, with lower-corner coordinates

\[
P=\{(0,0,0),(\pm1,0,0),(\pm2,0,0),(0,\pm1,0),(0,\pm2,0)\}.
\]

It is a flat four-arm cross, not the six-arm tridecacube already in the catalogue.
Proper cubic rotations give three distinct orientations. Reflections add none.

## What is established

On 2026-09-24, a [catalogue-wide exclusion study](nonacube-region-markings.html)
proved that this shape cannot tile the integer cubic lattice under cubic
rotations. It independently checked 58 finite-region pair obstructions and
replayed all three remaining branches of the marked root search. Every marking
exclusion is necessary in an infinite tiling, so the exhausted marked root rules
out the unmarked infinite lattice tiling too.

An independent unmarked two-corona calculation now establishes \(H=1\) for
integer translations and cubic rotations, using complete face/edge/vertex
surrounds with no topological-ball requirement. Its exhaustive formula is
unsatisfiable, with a separately checked proof. [Watch the complete recorded
search](nonacube-search-replay.html), including all decisions and backtracks,
or inspect its largest connected patch of 39 crosses, including the root.

This does not settle arbitrary Euclidean placements or the unrestricted
three-dimensional Heesch number. The previously located catalogue has no tiling
certificate; that historical absence alone was not a non-tiling proof.

The shape is entry 25373 (zero-based) in Georgios Papoutsis's
[nonocube input catalogue](https://github.com/gepa71/whuts-solver/blob/main/inputs/all_nonocubes.json).
Its [solution file](https://github.com/gepa71/whuts-solver/blob/main/results/nonocube_solutions/solution_25373.json)
is empty. The author's [description of the search](https://math.stackexchange.com/a/4150301)
explicitly says that failing to find a periodic tiling does not prove non-tiling.

We computed one complete surrounding corona and independently verified it by
integer voxel replay. Thus the three-dimensional Heesch number satisfies
\(H\geq1\); the separate two-corona proof supplies the lattice upper bound. The certificate has 34
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

## A certified forbidden pair

A stronger finite-region test now proves that two coplanar crosses with center
displacement \( (3,-2,0) \) cannot occur together in an infinite integer-grid
tiling. The pair nevertheless has a verified one-corona with viable frontier.
See the [illustrated pair and replayable proof](nonacube-forbidden-pair.html).
This establishes one exclusion, not a non-tiling or exact Heesch-number result.
The current cold browser learner does not yet run this stronger region oracle.

## Catalogue-wide pruning

The [full study](nonacube-region-markings.html) strengthens the earlier single-pair
result: 58 of 60 pair orbits are independently excluded, representing 676 of the
686 neighboring placements. The remaining two are budget-unknown and impose no
constraints. The compiled point fields exhaust the reference growth tree in
three placement attempts for each of three seeds. A separate verifier enumerates
the root domain and checks an immediate dead frontier for all three candidates.
The 58 proof traces, complete input, timings and replay scripts are published.
Fresh preparation took about 209 seconds; marked search took about one second.
These are different finite checkpoint problems, not a same-problem speedup.
The browser links the evidence; its cold learner does not load the recorded data.
