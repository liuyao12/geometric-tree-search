# Six-structure boron comparison: learned halo markings

This is a finite known-coordinate reconstruction experiment, not blind material
growth, a complete continuous-rotation search, or an exhaustive survey of boron.
The six available structures from the 2016 study are tested separately.

| Structure | Atoms in periodic test configuration | Training t/m check | Original marking search | Original + halo search |
|---|---:|---|---|---|
| α-B | 324 | Pass | Complete | Complete |
| β-B105 | 2,835 | Pass | Complete | Complete |
| β-B106 | 2,862 | Pass | Budget unknown | Budget unknown |
| γ-B | 756 | Pass | Complete | Complete |
| τ-B105 | 5,670 | Pass | Complete | Complete |
| τ-B106 | 5,724 | Pass | Budget unknown | Budget unknown |

## What was learned and checked

The preceding learner proposed 303 halo locations from neighboring training
clusters. This experiment transports every halo location at each stored pose,
including unmatched locations: 8,154 transported points without a nearby atom
are retained as marking-only sites. An additional scalar channel is fitted with
64 equality classes over 460 variables. Original t-values and the original
marking channel remain unchanged. No chemistry or physical energy enters this fit.

Point identities use atom-first, fixed representatives within 0.03 Å, followed
by fixed representatives for remaining halo points. Transitive distance chains
are not used. This is one order-dependent approximate correspondence hypothesis,
not an enumeration of all geometrically admissible correspondences. Pair motifs
do not receive off-axis halos: two points do not determine an axial rotation.

An independent checker reconstructs transported geometry, labels and all six
training fillings. A separate saved-search checker verifies all twelve search
models and final t/m assignments, and confirms that twelve previously generated
alternative connected fillings also remain valid with the new channel.

## Search protocol and result

Both lanes use the unchanged point-search kernel with linear frontier scanning
and branch-local exclusions. They use identical candidate pools, all target atom
points initially at generation zero, and limits of 100,000 advances or 15 seconds
per run. Setup is measured separately. Graph audits, final verification and exact
root rollback are checked; periodic copies are not independent samples.

Both lanes complete four of six configurations. The two difficult configurations
remain budget-unknown, not proved impossible. Halo checks add overhead; this run
provides no speedup or completion advantage. Timing is a single local run, not a
statistical performance study.

The additional channel excludes 540 new capacity-compatible candidate pairs in
β-B106 and 972 in τ-B106. Every such pair contains a candidate excluded by the
previous exact zero-support certificates. Thus these counts do not establish
new structural discrimination beyond the existing global capacity constraints.

## Scope and next test

All six inputs contributed to fitting; none is a held-out material. τ structures
are retained as geometric tests, not endorsed ground states: the 2017 erratum
(doi:10.1103/PhysRevLett.118.159902) withdrew the original τ ground-state assignment.
The ten additional τ-B106 S1–S10 coordinate sets have not been acquired. Consequently
“all six available structures” must not be shortened to “all boron crystals.”

The next substantive target is completion of β-B106 and τ-B106 without supplying
the known selected filling, followed by independent pose/structure holdouts and
seed-driven growth. This experiment does not yet demonstrate those capabilities.

## Reproduction

The published learner, geometric verifier, search runner and saved-result verifier
are `boron-halo-markings.py`, `verify-boron-halo-markings.py`,
`boron-halo-search.mjs` and `verify-boron-halo-search.py`. They use the preceding
boron face-cluster and halo-proposal artifacts. Checks and search summaries are
published alongside this report; raw input coordinates are not redistributed.

Compiled model SHA256:
`254757fbb972e805416a091273a14728c3c991d2dfbe31fcf0678a0c8b6896a3`.
Kernel SHA256:
`747db2cb5e626968d4bbf18fc1cb804b4a66ad2f177f3d5b097bc4b53257ba85`.
