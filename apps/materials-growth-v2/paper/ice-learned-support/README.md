# Learning point support: count, coordinates and t

This is a new inference experiment, not an upgrade to the earlier fixed-anchor search results. The intended model learns anchor count, anchor positions, t-values and m-values. This pilot addresses the first three only. Joint m-learning remains open.

## Inputs and method

The same 80 fit frames provide source positions plus previously inferred motif types, poses and selected occurrence proposals. The learner does not read inherited anchor coordinates, occurrence atom lists/permutations or half weights. It inverse-transforms nearby source atoms, proposes shared same-species points within a fixed 4 Å reach, and refines their coordinates by means or minimum-enclosing-ball fits. Species are opaque labels; there are no chemical valence rules. Final correspondence must be unique within 0.15 Å.

A mixed-integer model minimizes the number of positive anchors over the finite candidate pool. Each anchor has an independent weight in [0,1] and a binary inclusion gate. Every training atom must receive total weight 1. No equal-weight constraint or prescribed anchor count is supplied. A motif type with no positive anchors is retired: its occurrences are omitted, not treated as zero-support tiles.

## Observations

The initial mean-only proposal fit was infeasible. A mean can fall outside the intersection of tolerance balls even when that intersection is nonempty. Minimax refinement, without increasing the final positional tolerance, yields 3,809 proposals and a solver-reported optimum with 1,509 positive anchors across 250 active motif types. There are 2–12 anchors per active type; two types are retired. Of the learned weights, 1,506 are 1/2 and three are 1. Positions move by up to 0.143806 Å from their observation-derived initialization.

Independent replay from source coordinates checks all 22,080 training atom sites across 80 configurations. It uses periodic image trees, not the learner's correspondence lists, and exact rational t sums after rationalizing weights within 1e-12. All 80 pass. Corrupting a coordinate or weight is rejected; removing the learner's correspondence lists does not change the independent result.

Only 3 of 20 unused calibration configurations pass the same replay. These are not fully held-out tests: the upstream geometric dictionary had already seen these configurations. Training success therefore does not establish transferable support learning.

## Evidence and limits

The [independent receipt](check.json) includes every configuration's result and the full learned artifact's SHA-256. The learned artifact and source corpus remain local rather than republishing coordinate-reconstructing data. The three Python sources are supplied here; NumPy and SciPy are required. The learner takes `coordinates dictionary library transfer output`; the checker takes `coordinates dictionary library learned-result output`. Inputs are the same pinned data used by the preceding ice studies.

Solver-reported cardinality optimality is not independently certified. The proposal universe is finite, seeded by atoms and bounded by a prescribed reach; arbitrary off-atom marking anchors are not learned. Motif types, occurrence proposals and rigid poses are supplied, and t support is fit conditional on them. This is not general joint learning, a tree-search result, a speedup, or evidence of common-condition/independent-trajectory provenance. The next requirement is jointly useful m-values and validation on genuinely unseen configurations, not relabeling this support-only fit as full GCTS learning.
