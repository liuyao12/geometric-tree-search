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
not a general SAT optimizer or gradient descent. Since v2.2.4, each update also
tries symmetry-preserving masks of free values and rebuilds equality components
on the active slots. An inactive slot cannot bridge two assigned classes. The
previous separator remains a scored fallback; a bounded search tries up to 64
masks per sample and 2,048 at final refinement. These are synthesis budgets, not
oracle cutoffs, and do not imply optimal support. Every new positive revalidates
the previous mask. Both v1 and v2 use this shared implementation.

The reducer removes assignments in complete symmetry orbits while retaining a
witness for every currently distinguished negative; support-mask proposals may
separate additional negatives by freeing equality bridges. It preserves every positive
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

Historical v2.2.3 collection with reflections allowed, one-layer support, and a 500-attempt
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

## Faster live corona checks (v2.2.3; also used by v1)

The shared oracle now keeps one total record per spatial point, referenced by
every candidate using that point. Candidate weights share their orientation's
array. Legality checks read those totals directly instead of repeating string-key
map lookups for every candidate cell. Applying and undoing a placement updates
the same records; audits compare them with independently reconstructed domains
and the existing totals map. Experimental branch-cache removal also releases
unreferenced point records. Candidate limits, decision order, and label semantics
are unchanged.

The diagnostic comparison against commit `d4377be` checks every apply/rollback
prefix (including interrupted mutations), final labels, reasons, counts and
placements. All ten cases matched exactly. Measurements from one sequential
AB/BA pass with a 500-attempt limit and no time limit:

| Pair | Previous oracle | Shared point records |
| --- | ---: | ---: |
| p9-42947, vertex model, first | 1,228 ms | 444 ms |
| p9-42947, vertex model, second | 1,277 ms | 450 ms |
| p9-42947, center/corner model, second | 1,470 ms | 594 ms |
| p10-054782, center/corner model, first | 930 ms | 440 ms |
| FCC, first | 605 ms | 298 ms |

These are oracle timings, including trace instrumentation, not a claim that the
GCTS lane beats unmarked search. Difficult examples still stop unresolved at
their attempt or dependency budget. The change does not relax the acceptance
gate or convert a budget stop into a negative label. Full Turtle/Hat learning and
marked finite-window regression checks retain the scores above. Every learning
phase now reports elapsed time; the v2 lane includes preparation so its displayed
clock no longer drops to zero between sample updates.

Reproduce with `scripts/benchmark-3d-corona-shared-points.mjs`, supplying the
previous oracle module as its first argument. The complete aggregate receipt,
source hashes and trace digests are in
[the shared-point comparison](../../data/3d-corona-shared-points-2026-09-21.json).
It contains no learned marking assignments.


## Conditional free values in both live lanes (v2.2.4)

The browser learner now performs the support-mask step after each label and a
final refinement before independent replay and activation. The preview updates
its current values during refinement. There are no bundled markings or imported
labels in either browser lane. The unmarked graph still supplies every label;
unknown, incomplete and failed acceptance outcomes never start marked tiling.

Current complete slab regressions retain all 41 positives and increase rejection
from 176 to **192 / 206** for Turtle and from 166 to **176 / 186** for Hat.
Both marked finite windows independently verify. The cube retains an empty
marking and both engine adapters pass. These scores need not equal the 2D demo:
the 3D learner uses scalar codes on the declared slab point model.

`test-3d-masked-point-encoder.mjs` tests a free slot splitting a positive equality
path and a later positive forcing the previous separator to change.
`test-3d-live-mask-catalog.mjs` exercises the live incremental encoder against
all 686 recorded p9-48258 labels: 622 positives pass, all 64 negatives are blocked,
using 60 values. It also exhausts possible extra marking contacts. This is a
synthesis regression against recorded research labels, not a claim that the
browser's bounded graph oracle finishes that hard catalogue. See the
[full research receipt and oracle limitations](3d-point-corona-sat.md).

## Browser marking library and standalone runs (v2.2.5; also v1)

Both pages now provide **Learn new marking** and a **Saved marking** selector.
A fresh browser has no saved assignments. Each successful fresh run receives
its own short timestamp, point/value counts, and unique identity. Learning still
automatically starts marked tiling. **Tile with marking** explicitly reuses the
selected browser-local result without collecting a fresh set of labels. Storage
failure retains that run for the current visit.

The selector matches exact tile weights, orientation identities, reflection
policy, and placement domain. A different finite target size can reuse the same
system's marking; a different lattice, tile inventory, or reflection policy cannot.
Both workers check this identity again, enumerate the complete pair catalogue,
replay every saved positive corona with frontier viability, and recompute all
positive/negative marking decisions before activation. Incomplete, malformed,
duplicate, incompatible-version, and below-threshold records are rejected. Stored
negative labels retain the original exhausted-search provenance; this replay is
not a new proof of each negative or of infinite extension.

Reuse reports validation time separately from the original training cost. Cold
comparison and suite buttons still train from scratch. A standalone reuse run
is not mixed into the cold comparison's speedup claim. No learned assignments
are distributed in the application or this repository.

`node scripts/test-3d-marking-reuse.mjs` covers exact system matching, changed target
size, missing/duplicate pairs, invalid positive witnesses, malformed fields,
storage failure, fresh training, and both worker/engine reuse paths. Browser checks
cover empty storage, learning-to-tiling switching, reload persistence, reflection
filtering, distinct new runs, and both pages with no script errors. Reproduce with
`scripts/test-3d-marking-library-browser.cjs` (Playwright; `GCTS_TEST_URL` points
to the repository root URL, and `CHROME_PATH` can select an installed Chromium).

## Inspecting the marking used by a tiling (v2.2.6; also v1)

Both Tiling views now draw assigned learned point values, including points outside
positive t-support. **Markings** toggles this overlay independently of occupancy
points and geometry. Hover reports the lattice coordinate, component value, and
number of tile assignments agreeing there. Free components do not create points;
assigned zero remains visible. Values come from the active search, not the saved
selector's current choice or a known marking.

V2 reconstructs the section from its returned model and placements. V1 exports
its actual reference-counted section in snapshots and per-move updates, including
removals on rollback. The same data travels through live display and history
replay. Root markings are emitted immediately after validation, before growth.
Switching to an unmarked system clears the overlay. This display change adds no
legality rule and changes neither the learner nor the acceptance threshold.

Verification: `test-3d-marking-display.mjs` checks component wildcards, assigned
zero, overlap counts and rollback, then compares v1 snapshot/delta transport with
an independent placement reconstruction. `test-3d-marking-overlay-browser.cjs`
trains Turtle and Hat in a fresh browser, verifies both finite marked windows,
and checks hovered values/counts against the worker results. It also checks v1
with a browser-generated constant-zero control after a genuine cube learning run.
No learned assignments are bundled. The existing learning and reuse suites pass;
Turtle retains all 41 positives and blocks 192/206 negatives, and Hat retains all
41 positives and blocks 176/186 negatives in the reflected index-3 slab controls.
These finite classification results do not establish infinite extension.
