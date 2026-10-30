# Live GCTS marking learning for the icosahedral face search

The quasicrystal workspace has a cold **Learn GCTS marking** lane. It tests local
configurations, updates provisional point assignments after every label,
independently validates the completed field, saves a named browser-local run and
starts a fresh marked search. No learned assignments or labeled catalogues ship
with the application. Supplied-rule and unmarked controls remain available.

This is an explicitly **geometric face-corona adaptation** of the learning loop
in [the master contract](../basic-tiling-algorithm.md), not a newly established
finite point-capacity model. Exact overlap and face-contact predicates remain
the geometric oracle and growth control.

## System and finite marking support

The fixed problem is the 120 supplied Ammann decorated orientations with proper
rotations and integer star-module translations. Both source hands are present.
The learner does not copy supplied dot vectors into its variables. Its oracle
uses the supplied-rule problem: bare rhombohedra permit periodic tilings and
cannot justify rejecting those tilings as impossible.

For an oriented tile with center \(c\), the support is

\[
D_h=c+\left\{\frac12\sum_{i=0}^5 n_i u_i:
n_i\in\mathbb Z,\quad\sum_i|n_i|\leq h\right\}.
\]

Compact, extended and wide choices have \(h=1,2,3\): 13, 85 and 377 eligible
slots per oriented prototype. Interior, face and exterior slots remain eligible.
Compact support is the measured default. The abstract half-module is discrete
in its six-dimensional lift and dense in physical space. The engine enumerates
finite placement support, never all module points in a physical bounding box.

Lift coordinates and actions use `BigInt`; physical predicates use the existing
exact golden-field operators. The 60 proper rotations are derived with exact
Gram/determinant comparisons and verified on all 120 decorated orientations.
They act on lifts by signed permutations of six axes. Component indices stay
fixed; categorical labels have the verified induced permutation action.
Translation moves support and leaves values fixed. `*` is absent; code zero is
assigned. Approximate coordinates occur only in the rendering adapter.

## Oracle, samples and synthesis

The 156 neighboring face-pair classes have a verified orbit of all 17,280
directed attachments, \(120\cdot6\cdot24\). Every class is used, without a
held-out split. Edge-only, vertex-only and separated marking contacts are not
training examples.

Each oracle fixes both seed tiles, completes all their exposed faces and checks
that every exposed face of the resulting patch has a nonempty exact domain.
Both fixed seed tiles and their initial face obligations have generation zero.
It uses global dead/forced checks, earliest-generation branching and exact
rollback. Provisional fields never enter this oracle. A completed face-corona
with viable frontier is positive; a supplied-rule conflict or exhausted complete
search is negative. Attempt and tile limits are unresolved. Defaults are 1,024
attempts and 96 tiles per pair. Continue learning keeps resolved evidence and
retries unresolved pairs with larger budgets.

Positive overlaps impose equalities; negatives require an unequal assigned
overlap. An incremental equality encoder searches rotation-invariant free masks
and up to three independent categorical components. Each component rebuilds its
positive graph on its active support. A later positive can change previous
values. Live updates use 48 mask evaluations; final refinement uses 256. This
is bounded synthesis, not a complete SAT solver or a minimum-support theorem.
Random support proposals do not approximate coordinates or legality comparisons.

The main scene displays actual oracle placements and rollbacks. A separate
rotatable inset shows the provisional field. The sample inspector displays the
selected pair and current marking decision; its table includes individual free
entries. Point/value counts cover all 120 orientations. During marked growth,
hovering an assigned point exposes its exact serialized coordinates, values and
reference counts.

## Validation and runtime enforcement

Activation requires the complete catalog, no unresolved labels, acceptance of
every positive and rejection of more than half the negatives. Positive witnesses
are independently reconstructed with exact pairwise geometry, supplied marking
agreement, completed seed faces and freshly enumerated viable frontier domains.
Scores and the value permutation action are replayed independently.

The frozen field enters the ordinary `PointMarkingState`. All halo assignments
and reverse dependencies participate, regardless of geometric bounds or frontier
membership. A disagreement removes the candidate from every incident face.
Growth uses no learned pair lookup, failure-clause scan or corona lookahead.
Additional learned-removal counts credit only candidates whose supplied channels
still agree, avoiding double credit for original source-rule rejections.

Each model records versions, orientation/domain provenance, timestamp, name and
evidence. Browser-local runs remain separate; reload does not silently activate
an old run. Explicit reuse validates support and action and replays saved
positive witnesses and scores. Storage failure retains the model for that visit.
Changing or disabling a field reconstructs the search from its seed and drops
old trails and caches.

Local classification does not prove that a field preserves larger patches.
Unsampled marking-only contacts may block growth. Exhaustion with a field is a
restricted-model failure, not unmarked impossibility. There is no infinite
extension, full coverage or unique quasicrystal claim.

## Measured finite checks

Fresh compact-halo learning resolves 26 positives and 130 negatives, with none
unresolved. All 26 positives pass and all 130 negatives are blocked. Of the
negatives, 120 are direct supplied face conflicts and 10 require the fixed-pair
extension check. The final field has 1,080 active points and 1,320 assigned
values across all 120 orientations.

For a prolate left-hand root and branch-order seed 4, ordinary marked growth
reaches 60 tiles with viable frontier in 75 trials: 43 forced placements, 32
branches and 16 backtracks. It has 15 additional learned removals beyond the
supplied channels. The supplied-rule control previously required 93 trials and
34 backtracks. These counts exclude training and validation costs and are not
a speedup claim. Oracle, synthesis, elapsed learning and growth costs are shown
separately.

The extended halo also fits all 156 labels. Its tested rooted growth reaches
48 tiles and exhausts before 60 after 3,162 trials/backtracks. This demonstrates
why perfect face-pair scores do not establish unrestricted large-patch order.
Wider support remains a selectable experiment.

## Conformance evidence and gaps

- Exact support/action, cold empty fields, complete face-pair orbit, unresolved
  semantics, free/zero entries, the gate, serialization and invalid saved action
  rejection are tested.
- Independent full domain enumeration checks marked frontier incidence. Nested
  apply/undo checks restore values, reference counts, extended dependencies,
  candidate validity/incidence, face owners, spatial indexes and generations.
- Finite marked patches receive independent pairwise geometry and overlapping
  component checks. Existing worker and point-state tests retain pause/resume,
  step, reset, budget, zero/free and far-support coverage.
- A faithful finite positive-capacity model for the solids remains unspecified.
  Geometry is still required in this specialized lane.
- Training covers face neighbors, not every possible halo-only contact. Local
  evidence and synthesis do not certify infinite order.

Reproduce with:

```sh
node scripts/test-icosahedral-gcts-learning.mjs
node scripts/test-icosahedral-gcts-worker.mjs
node scripts/test-icosahedral-search-worker.mjs
node scripts/test-icosahedral-point-markings.mjs
node scripts/test-icosahedral-face-search.mjs
```

`GCTS_RECEIPT_PATH` optionally saves the fresh integration run's model and growth
statistics outside the application. Such output is not a bundled learned field.
