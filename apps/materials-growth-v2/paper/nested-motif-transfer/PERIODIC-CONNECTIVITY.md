# Shared poses are not yet an outward-connected structure

19 September 2026. Follow-up to [CONTINUOUS-POSES.md](CONTINUOUS-POSES.md).

## Shared-pose audit

For every evaluation motif, retain its original pose and all saved positive
pair-witness poses. For every proposed pair, re-evaluate the recurring frozen
interface models across those domains. A bounded finite-domain CSP requires
one pose per motif for all incident pairs. This is a diagnostic CSP, not the
GCTS frontier scheduler; it makes no base-tree-search conformance claim.

The 3 alpha and 29 beta frames whose pairs all had witnesses retain a
shared-pose assignment. Independent replay transports every atom, anchor and
vector marking with that same motif pose. The finite CSP is also checked
against independent exhaustive enumeration on 100 synthetic controls,
including contradictory cycles and budget stops. Exhausting these saved pose
domains does not establish continuous infeasibility.

Of these frames, zero alpha and 28 beta frames have a connected quotient
graph inside one cell. That apparently positive beta count is insufficient.

## Periodic topology exposes the missing requirement

Record each edge as (motif i, motif j, integer cell shift). Cycles accumulate
integer translation vectors. A graph can connect inside one unit cell while
its periodic copies remain separate. Full three-dimensional connectivity
requires paths generating every lattice translation, not just a connected
finite quotient. Rank three alone is insufficient if the generated subgroup
has index greater than one.

All 88 original nearest-centroid proposal graphs are forests. An independent
forest check therefore proves that there are no nonzero translation cycles,
regardless of the particular edge-image labels. Their periodic lifts consist
of finite fragments. This does not prove anything impossible about the input
crystals; it exposes an inadequate proposal graph.

Cross-interface common marking values and positive t-filling remain separate
requirements even when a graph passes this topology check.

## Revised candidate generator

A separate geometry-only generator computes periodic Voronoi neighbors of
the motif centroids, including self-image edges and multiple images of the
same motif pair. It uses no species, phase, energy or chemical rule. These
neighbors are candidates; the learner is not required to use them all.

The generator expands a lattice-image box until

    (shell + 1) * smallest_singular_value(cell) - center_span
        > 2 * largest_central_Voronoi_cell_radius.

The left side bounds the distance to every omitted image. With this strict
margin, omitted images cannot clip the central cells, subject to the numerical
accuracy of the Voronoi construction. No random geometric jitter is used.
This is not an exact-arithmetic Voronoi certificate; degeneracies remain a
numerical concern. The default maximum shell is five; failure to establish
the bound is reported as unknown.

All 88 evaluation graphs pass the image bound. Alpha has 23–63 undirected
periodic edges per frame, beta 14–30. Every graph admits explicit finite paths
from one motif to every other motif in the reference cell and to copies of
the starting motif translated by each unit basis vector. An independent BFS
constructs and replays these integer-labeled paths. This proves connectivity
of the recorded abstract periodic graph; it does not prove a learned tiling.
All 88 edge sets are unchanged when the image box is enlarged by one shell.

Controls cover isolated periodic fragments, planar rank-two graphs, an
index-two sublattice, cubic self-image neighbors, enlarged image boxes and
rigid motions. Independent constructive paths correctly reject the index-two
case despite its rank-three cycle group.

## What remains

The 88 connected candidate graphs are a generator property, **not 88 successful
GCTS reconstructions**. The old 306 interface models were not trained on this
new domain. The next experiment must learn interface supports, filling weights
and markings on these periodic candidates and recheck the supplied tilings
before search. Provenance for identical physical conditions, complete shared
marking consistency, freely learned anchor count and blind growth remain open.

## Reproduce

After producing the source cohort, nested dictionary, interface models and
continuous pair witnesses as described in the previous notes:

```sh
python test-periodic-interface-proposals.py
python check-shared-interface-poses.py cohort/coordinates.json cohort/metadata.json nested.json interfaces.json continuous.json shared.json
python periodic-interface-proposals.py cohort/coordinates.json cohort/metadata.json nested.json periodic.json
python verify-shared-interface-poses.py cohort/coordinates.json cohort/metadata.json nested.json interfaces.json continuous.json shared.json periodic.json shared-periodic-check.json
```

Keep all scripts in this directory together. The shared verifier also uses
the existing pose and periodic-image checkers. The public receipt contains
hashes, counts and compact path summaries; coordinate-bearing full proposal
files are regenerated, not redistributed.
