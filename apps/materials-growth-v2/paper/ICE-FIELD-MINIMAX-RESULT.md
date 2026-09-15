# Worst-atom pose fitting recovers 97 of 100 supplied ice covers

## Question and fixed inputs

Does least-squares registration discard valid approximate motif placements?
Acceptance limits the **maximum** atom-position error to 0.15 Å, whereas
Procrustes registration minimizes the sum of squared errors. These objectives
need not select the same pose.

This developmental diagnostic retains the existing 80-frame fitting-decoration
library, original 100 developmental configurations, component partitions,
half-weight t-values and global Gaussian-field radius 1.1063594889735058.
No developmental motif or marking is inserted into training. The base geometry
dictionary had already seen all 100 training frames, including calibration;
this is not a fresh end-to-end holdout. The original calibration gate failed
on missing fitting bases, so the global radius remains explicitly diagnostic.

## Method

Revisit the original 41 failed occurrences. Enumerate fitting bases and
label-preserving correspondences with the same inferred component partition.
A necessary pair-distance screen precedes proper Procrustes alignment. For
screened correspondences failing the maximum-error gate, locally optimize
rotation and translation against maximum normalized atom error using SLSQP.
Zero auxiliary marking arrays make this optimizer geometry-only. Afterwards,
test both learned endpoint fields under the same proper rotation and retain
the first positive witness. Original positive witnesses remain unchanged.

## Results

| Registration control | Accepted occurrences / 9,200 | Complete supplied covers / 100 |
| --- | ---: | ---: |
| Original assigned bases | 9,159 | 67 |
| Alternative fitting bases, Procrustes | 9,168 | 74 |
| Alternative fitting bases, maximum-error refinement | 9,196 | 97 |

The last control makes 496 local refinements and recovers 37 of the original
41 failed occurrences. Complete covers: Ih 24/25, II 23/25, VI 25/25, VIII 25/25.
Four occurrences in three frames remain without accepted geometric proposals:
c00420 edge 25; c00910 edge 89; c00918 edges 48 and 150. Local optimizer failure
does not prove nonexistence of a valid continuous pose.

Independent replay checks all 37 new witnesses and 74 endpoint fields from
source coordinates, without importing the fitting producer or optimizer.
It verifies fitting membership, proper rotations, permutations, periodic
position errors, t-support, component identities and source-derived common
field witnesses. Maximum checked positional error is 0.14905230354827143 Å;
maximum endpoint field distance is 1.056929268486711. Together with the previous
positive-witness check, this verifies 97 complete supplied covers numerically.
It is not an interval-arithmetic exact certificate.

Two small optimizer controls verify the distinction between average and maximum
error and the unknown status of unsuccessful local fitting. The separate
negative-test runner corrupts rotations, translations, field distances and the
case list to test witness rejection.

## What this does not establish

These are supplied-cover feasibility checks, not reconstructions found by the
reference GCTS tree search. The unchanged broad marking radius previously
rejected zero of 1,367,236 fixed-pose single-decoration replacements; this
experiment does not fix that specificity failure or demonstrate a speedup.
General anchor and t-value learning, useful connection learning, reconstruction
without supplied decompositions, complete continuous-pose search and growth
beyond supplied coordinates remain open. File-linked equal-condition and
independent-trajectory provenance also remain unverified.

The next useful step is to retain the recovered geometric candidates while
testing more selective, jointly trained connection markings that still admit
the known covers. Do not interpret these positive witnesses as evidence that
the current markings eliminate wrong connections.

Artifacts: `ice-field-minimax-bases.json`, `ice-field-minimax-bases-check.json`,
`ice-field-alternative-bases.py` (with `--minimax`),
`verify-ice-field-alternative-bases.py`, `ice-joint-pose.py`,
`test-ice-geometry-minimax.py`, `test-ice-alternative-witness-check.py`.
