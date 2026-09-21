# GCTS learning in the 3D tiler (v1 and v2)

Both active GCTS lanes now follow the local-constraint loop documented in
[the master reference](../basic-tiling-algorithm.md), using the shared
`apps/3d-lattice-tiler/marking-learning.js` module. GCTS+RL uses the same learned
marking before its existing ordering/proposal layer. The original explorer is
`apps/3d-lattice-tiler/legacy.html`; the v2 workbench is `index.html`, also served
at the short `/3d-lattice-tiler/` URL.

## Collection, updates and activation

The learner takes the actual integer point weights and allowed orientations.
It enumerates capacity-legal neighboring pairs modulo verified root-orientation
orbits. Each pair remains fixed while the unmarked oracle fills every point in
its positive support. A positive requires both complete core sums and a viable
exposed frontier. Exhaustion is negative. Node, time, candidate, depth, catalog,
and marking-support bounds remain unresolved/incomplete; none can license a
negative label or an accepted marking. No recorded labels or markings are used.

A signed cubic point-group operation is admitted only when it maps every species'
weighted orientation set to itself and respects the slab translation domain.
Positive equality constraints are closed under these operations. The current
3D encoder uses **scalar categorical point codes**, with an induced permutation
of code labels under the group, rather than three directional real components.
Equivalently these labels index basis vectors with a permutation action. The
support includes the t-support plus one neighbor layer by default. For a slab
that layer is lateral and respects its A₂ lattice or sublattice; for Z³ it uses
the six axial neighbors. Every new resolved or unresolved sample updates the
reported prefix scores. Positives merge equality classes; negatives identify
required disagreement alternatives. This is incremental equality synthesis,
not a general SAT optimizer or gradient descent.

The reducer removes assignments in complete symmetry orbits while retaining a
witness for every currently distinguished negative. It preserves every positive
and the observed negative score, not all unobserved relative-placement decisions.
Interior points have no special retention or exclusion rule. Omission is `*`;
zero is an ordinary assigned value. The v2 matcher also supports independent
components of vector-valued inputs (null or `*` components are absent).

The shared Learn markings view shows actual corona steps on the left and current
codes on the right. Orange indicates changed assignments. Every orientation can
be inspected; hover reveals its current value or `*`. Counts cover all represented
orientations, not only one prototype. Browser paints may coalesce fast worker
frames; the evidence retains every pair and the current prefix score. On complete
classification the learner independently replays matching and requires all
positives to pass, more than half the negatives to be blocked (unless there are
none), and no unknown labels. Only then does marked tiling start automatically.
The view switches back to Tiling, with Learn markings available for inspection.

Successful runs receive a timestamp and UUID in browser storage under
`gcts-3d-markings-v1`. The stored domain contains exact weights, orientations,
reflections, lattice restrictions and support extent. Cold lanes still train
fresh; saved assignments are not silently reused. Storage failures leave the
validated run available for that visit. No learned data is written to the repo.

## Search semantics and conformance

`corona-graph.js` maintains the complete point/candidate graph for every exposed
positive frontier obligation. Candidate nodes are shared by all incident points.
Dependencies include every positive t-site. Applying and rolling back placements
updates affected candidate validity and all degrees. Point generations are the
minimum incident placement generation; a new tile has one plus the earliest
incident generation. A global degree-zero point precedes forced moves, then
branching uses earliest generation with degree as a tie-break. Inactive point and
candidate caches can survive rollback, but their validity and all active state
are restored. The oracle uses no geometric overlap, face or catalog predicate.
An independent verifier reconstructs weights and enumerates candidates afresh at
every exposed point before accepting a positive witness.

The completed marking is frozen before marked growth. It is used as assigned
m-values in ordinary global-section matching, including mark-only interactions.
There is no runtime forbidden-pair lookup. V2 uses the existing exact point-window
graph; its former residual-capacity/lookahead GCTS control is no longer the default
GCTS lane. It remains callable explicitly through `gctsLookahead: true` for
historical experiments. V1 uses `LearnedSection` in its existing search engine;
its historical conservative constructor remains an explicit
`gcts_learning_protocol: 'conservative'` control. Old measurements retain their
old semantics and are not relabeled as results for the new learner.

The oracle's point-model conformance does **not** complete a conformance migration
of v1's legacy geometric growth engine. Its existing geometric constraints,
scheduling options, shell semantics and comparison limitations remain. V2 still
solves a finite point window rather than unbounded space. Both engines distinguish
failure under learned markings from unmarked impossibility; the learner's finite
positive catalog is not a redundancy proof. No speedup is claimed. Learning is
charged to lane time, and on tiny easy targets costs much more than plain search.
A difficult 3D pair can reach the per-pair budget, preventing activation even
when a useful marking might exist with stronger evidence.
Both pages expose this limit as “Attempts per corona pair” (500 by default).

## Verification and measured controls

`node scripts/test-3d-marking-learning.mjs` tests dynamic incidence against fresh
candidate enumeration, nested generation/weight rollback, positive and negative
oracle fixtures, a complete core with a dead exterior frontier, unknown/resource
budgets, individual vector `*` versus assigned zero, both engine adapters,
reference-counted sections, and the browser-storage acceptance boundary.
`node scripts/test-3d-lattice-v2.mjs` retains tiny exhaustive point-window,
mark-only interaction, rollback, and scheduler tests.

Fresh collection with reflections allowed, one-layer support, and a 500-attempt
pair budget gives:

| Point model | Pairs | Positives passed | Negatives blocked | Marked growth |
| --- | ---: | ---: | ---: | --- |
| Cube | 26 | 26 / 26 | 0 / 0 | v1 eight-tile patch; v2 27-point window |
| Turtle, index-3 two-cap slab | 247 | 41 / 41 | 176 / 206 | v2 14-point window verified |
| Hat, index-3 two-cap slab | 227 | 41 / 41 | 166 / 186 | v2 14-point window verified |

The cube reduces to an empty, nonrestrictive marking. The slab classifications
match the corresponding 2D sublattice catalogs. Their representative v2 searches
recorded 178 and 110 marking-based candidate eliminations respectively. These are
finite regression controls, not a census of all 3D systems. Full 3D prisms are
separate models and can remain unresolved within the same time or node budgets.
Browser checks exercise both entry points, worker progress, current values,
automatic learning/tiling view changes, saved metadata, and clean page execution.
