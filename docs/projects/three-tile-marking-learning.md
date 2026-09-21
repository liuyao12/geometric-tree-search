# Learning point markings for the three article tile sets

## Current pipeline: classify complete pair coronas, then learn

`GCTS-I.html` embeds `GCTS-learning.html` in its **Learn markings** tab.
Entering the final Geometric Deep Learning section selects Turtle and starts
one fresh collection per page visit. Known rank-3 Turtle tiling starts at the
“The turtle admits a marking…” example (`#anchor-known-marking`). Scrolling back
restores that known-marking Tiling view. The learning section selects an approved
learned marking when available, otherwise no marking; background completion does
not replace the earlier known-marking example. Its inventory and training run
survive section crossings. Manual tab
changes and pauses do not restart collection; learning can run in the background.
The top tile-set controls apply to both panel tabs. Opening Learn markings manually
uses the selected inventory even outside the learning section. Selecting a new
inventory in Learn markings starts its first collection automatically; returning
to an already completed inventory displays its report without retraining. An
interrupted inventory is eligible to start again when selected. The
Classify & learn button still starts a fresh named run. A pending iframe startup
carries the selected inventory rather than defaulting to Turtle. Switching
inventories cancels an unfinished run; completed reports and named markings remain
available. Hat uses its full allowed symmetry group; the mixed inventory continues
to use rotations only in classification, training and marked search.

The current experiment enumerates every t-legal second placement whose positive
support touches the fixed first tile. Both root types are included for the mixed
inventory. These are ordered, rooted connections, not symmetry-orbit counts.
Turtle and Hat each allow 12 orientations including reflections; Turtle + Hat
allows six rotations per prototype and no reflections.

Each pair is classified **before any marking is trained**. A complete one-corona
means that every point in the union of the two core tiles' positive t-support
has total t-value 1 (integer capacity 12). The two core tiles remain fixed.
Additional tiles must respect capacity everywhere, including outside the core;
their outer boundary need not be completed, but **every unfinished exposed point
must have at least one legal candidate**. A dead outer point rejects that
completion; the search backtracks and may find another completion for the same
pair. Candidates obey the selected lattice, inventory, reflection policy,
placement uniqueness and all t-capacities. Every added tile touches a required
core point. This is a finite point-domain criterion, not a tile-count checkpoint
or a claim of infinite extendibility. Polygon outlines are only illustrations.

The unmarked search returns:

- **Valid:** a complete corona with independently verified integer capacities
  and a viable exposed frontier (no degree-zero point).
- **Invalid:** exhausted finite search for that pair and inventory.
- **Unresolved:** budget exhaustion or cancellation; never a negative label.

After all pairs have been examined, training uses every valid and invalid label,
with no held-out samples. Only the central valid pairs supply equality constraints;
the surrounding witness tiles do not silently add positive training connections.
A signed union-find equates overlapping point/channel variables, forces zero
on inconsistent sign cycles, and assigns distinct integer magnitudes to free
classes. Three channels transform by coordinate permutation and permutation-parity
sign. Assigned zero remains a value. Domains use positive t-support plus one,
two, or three nearest-neighbor A₂ layers; the best classification is retained.
This is deterministic constraint learning, not gradient descent.

A model is saved and automatically transferred to the matching tiling inventory
**only when the complete catalog is resolved, every valid pair is accepted,
and more than half of the invalid pairs are blocked**. A perfect classifier also
qualifies; the exact valid acceptance and invalid rejection counts are displayed.
The gate checks catalog coverage, uniqueness, counts and actual marking decisions.
Candidates that reject a valid pair or block too few invalid pairs remain
unapproved. JSON exports retain the labels, errors and point/value metadata.
Retries keep the same corona criterion and increase the selected unresolved
pair's budget. A timeout cannot replace an already resolved result.

### Viable-frontier criterion

Current runs use `viable-pair-one-corona-v2`. Stored markings from the earlier
core-only criterion remain available in that browser with their original
criterion recorded in the saved evidence; their values and history are not
deleted or relabeled as new evidence. New training cannot combine old core-only labels with v2 labels.

At seed 90210 and 5,000 attempted placements per pair, all checks resolve:

| Full-lattice inventory | Pairs | Valid accepted | Invalid blocked |
| --- | ---: | ---: | ---: |
| Turtle | 304 | 41 / 41 | 236 / 263 |
| Hat | 320 | 41 / 41 | 262 / 279 |
| Turtle + Hat | 624 | 70 / 70 | 501 / 554 |

All three qualify for saving. Some pairs keep their valid label but need different
witnesses: filling the core alone could previously stop at a dead outer frontier.
No learned models or generated reports accompany these measurements.

### Historical measurements (not bundled models)

Former core-only criterion, seed 90210, 5,000 attempted placements per pair:

| Inventory | Pairs | Valid | Invalid | Unresolved | Correct marking classifications | Invalid pairs still accepted |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Turtle | 304 | 41 | 263 | 0 | 277 / 304 (91.1%) | 27 |
| Hat | 320 | 41 | 279 | 0 | 303 / 320 (94.7%) | 17 |
| Turtle + Hat | 624 | 82 | 542 | 0 | 583 / 624 (93.4%) | 41 |

Increasing the domain through three layers did not improve these historical
scores. All valid pairs were accepted, with invalid rejection rates of 89.7%,
93.9% and 92.4%. These measurements document prior experiments; they do not
supply a marking to the page. **No learned models, labels, patches or generated
training reports are bundled in the repository or fetched by the demo.**
The ordinary fixed rank-1/rank-3 markings remain part of the implementation.
A clean browser has only no marking, rank 1 and rank 3 in the dropdown; named
learned entries appear only after successful browser training. Previously trained
local markings can be restored in the same browser.
Accepted models, when available, persist per inventory in local storage and
transfer automatically by the existing same-origin iframe message. A successful
fresh training run in the learning section selects learned marking, switches to
the Tiling tab and starts the marked search, including a repeated successful run
with unchanged values. Training runs entirely in the browser worker. Models stay
in browser local storage; evidence export is an explicit browser download. No
training result is uploaded or written back to the repository. Import
validation checks every recorded label against the marking; it does not rerun
all oracle searches or independently certify the provenance of external labels.
Recorded invalid cases have replayable settings, not formal proof transcripts.
Even perfect pair classification would certify only this finite criterion;
mark-only interactions beyond the audited pairs remain learned restrictions.

### Named marking history

Every successful fresh training run receives a UUID and a full UTC creation
timestamp in its stored evidence. Its compact display name uses local month,
day, hour and minute, plus point/value counts. The Tiling dropdown lists saved
runs for the selected inventory and lattice, newest first. A successful run selects
and starts its own entry; selecting an older entry uses that exact saved model.
The browser retains both the history and the last selection per inventory/lattice.
Old single-model storage slots migrate without discarding the previous marking.
Earlier entries explicitly tagged as bundled recordings are removed from local
storage. Actual locally trained markings are retained. Reopening a cached report
does not create another run.

The learner reports “Same values as …” when a new run has the same complete
point/channel assignments as an earlier marking in the same inventory and lattice.
Comparison ignores entry order,
names and display reduction; it does not claim to recognize mathematical
equivalence under relabeling or symmetry. The current exhaustive learner is
deterministic, so rerunning the same experiment commonly produces the same
values. Runs still retain distinct names and identities. JSON evidence exports
include the name, ID, creation time, settings and any exact-value match.
A storage failure leaves the current result usable and reports that it could
not be persisted; unreadable history is not overwritten.

`tests/test_marking_library.mjs` covers distinct run identities, repeated names
at one timestamp, exact-value comparisons, immutable entries, migration reuse,
reload/import identity and storage failures. Browser checks perform two complete
training runs, verify both dropdown entries and automatic starts, select and grow
an older model, and check retained selection/history after reload and mobile layout.
The matching rules, acceptance gate and shared search engine are unchanged.

### Interior markings in the display

The current panels preserve every interior t=1 point when reducing a marking.
Training already assigned these points; the previous unrestricted reduction
removed them because other overlapping assignments witnessed the same conflicts.
Retaining them shows the neighbor-exterior/tile-interior comparisons directly.
Remaining point deletions still preserve every original t-legal pair exclusion.
Zero-valued segments are visible gray, and the pair view paints every tile fill
before any marking, so later tiles cannot obscure neighboring markings.
This changes neither the trained values nor the corona classification scores.
The historical reduction benchmarks below retain the original reduction policy.

### Shared-engine conformance and verification

The optional `requiredPoints` mode of `solveA2Tiling` explicitly activates every
finite obligation, including untouched zero-valued points, at generation zero.
The new `requireViableFrontier` option also tracks every exposed unfinished
point of the whole patch in the complete candidate-incidence graph. A global
degree-zero scan precedes acceptance, even when all core points have already
reached capacity and the placement budget is exhausted. Candidate validity still
depends on all t- and m-support, including exterior points.

This is explicitly a bounded corona check: outer points are viability probes,
not additional fill obligations. Forced propagation and branching choose among
required core points after the global dead-point scan; outer singleton probes
are not filled, which would expand the requested corona. The target therefore
remains finite. Graph incidence, dependencies and rollback cover both classes.
The optional mode defaults off, preserving historical core-only engine callers
and ordinary growth. Completion ignores tile-count milestones.

In this finite mode, exhausted search branches are skipped when branching but
remain in the geometric candidate graph if they are still t/m-legal. Failing
to extend a candidate to a complete corona does not erase it as a legal
one-step continuation of an outer frontier point. This distinction also keeps
graph audits exact after backtracking.

The complete point/candidate graph, global dead-point checks before core forced moves,
earliest-generation branching, orientation enumeration and exact rollback are
retained. Corona classification always uses `NoA2Marking`, so candidate markings
cannot create their own negative labels. Integer t-values and independent integer
witness verification support the exact finite result; the engine's generic
comparison tolerances do not substitute for that verification. No geometric
collision predicate is added. Conventional polygon fidelity and whole-plane
coverage are not established by these runs.

`tests/test_tile_corona_learning.mjs` checks all 1,248 catalog entries, all valid
freshly generated corona witnesses, each candidate's predictions, incomplete, false-rejection and majority-rejection save gates,
and zero-budget semantics. An independent finite DFS agrees on one valid and the
hardest recorded invalid case per inventory; graph-audited engine replays agree
on the same cases. This is representative negative-search cross-checking, not
an independent reproof of every negative. Every valid witness also passes a
separate all-frontier enumerator. `tests/test_corona_frontier.mjs` generates an
old-style completion with seven dead outer points at runtime, rejects it even
when its core is already filled, and verifies an alternate viable completion for
the same pair. A Hat sublattice regression also checks that exhausted branches
do not hide legal frontier candidates. Graph audits cover the exposed frontier
and rollback.
Existing fixed-marking and Turtle
regressions also pass. Browser checks cover all three reports, automatic Turtle
collection, automatic learned tiling after successful training, legacy history, unresolved searches,
usual tiling controls and mobile/scroll tab behavior.

Regenerate and verify:

```
node scripts/train-tile-corona-markings.mjs /tmp/pair-corona-markings
node tests/test_tile_corona_learning.mjs
node tests/test_corona_frontier.mjs
node tests/test_fixed_a2_marking.mjs
node tests/test_turtle_point_learning.mjs
```

The old generated `tile-connections-*`, `tile-corona-*`, `tile-markings`,
`hat-local-patches` and marking-comparison files have been removed. Tests now
collect their evidence and train models in memory; storage tests use an explicitly
synthetic fixture. CLI experiment scripts default to temporary output folders.
Generated output paths are ignored by Git. The historical comparison below
records past measurements and remains reproducible by running those algorithms;
it is not a source of pre-trained values for the application.

## Watching the one-corona check

The learning canvas streams actual pair-start, placement, dead-end, backtracking,
and pair-result events from the unmarked search. It keeps the fixed pair darker
than the surrounding tiles. Gold dots mark unfinished required points of the
fixed pair; green dots have total t-value 1. A red ring marks a reported dead end,
including dead outer points. Blue rings show the exposed frontier after its
viability check passes.
The viewport stays fixed during each pair's search. Success, exhausted failure,
and budget-limited unresolved results have distinct labels, shown before the
next pair starts. Retry unresolved uses the same animated path.

The counter reports completed checks as “320 pairs”, with no denominator or
precomputed classification counts. A running pair has its own sequential number;
valid/invalid/unresolved totals accumulate only after each search returns.
The finite candidate enumeration can know its catalog size internally, but it
has no validity labels before searching.

Learning always uses Fast speed, without an extra frame hold or speed selector. The worker drains its frame queue
through the existing search-demand hook and waits for a display acknowledgment,
so rendering cannot build up an unbounded backlog. Pause gates further frames;
reset, inventory/domain changes, and worker replacement cancel the old queue.
This changes presentation timing only: candidate enumeration, node budgets,
generation order, exact rollback, and classification/training criteria are
unchanged. The complete catalog regression checks event order alongside the
existing independent search and marking checks. Browser checks verify visible
placement/backtracking/success/failure, pause/resume, and the full fresh Hat run.

## Learning on the sublattice

The Learn markings page offers a **sublattice** checkbox. Switching it starts
classification and training on that domain. The training and tiling lattice
controls are independent while choosing what to train. Saved markings belong to
both the tile system and lattice. The Tiling dropdown lists only matching runs;
switching lattice selects its remembered marking, or no marking if none exists.
Known rank-1/rank-3 selections remain known markings when changing lattice.
Successful training selects its own lattice before automatically starting tiling.
Reports, automatic-start state and remembered selections are separate for each
inventory and lattice. Existing browser models without a lattice field retain
full A₂ semantics; existing run IDs and point values are preserved.

The details banner has been removed. Names use local `MM-DD HH:mm` followed by
point and assigned-value counts (including explicit zeros, counting points per
tile prototype). Same-minute runs in a domain get `#2`, `#3`, etc. Existing names
are formatted this way when loaded, without discarding their stored evidence.

`A2` is the full integer plane x+y+z=0. `turtle-sublattice` is its index-three
subgroup x≡y≡z (mod 3). Both t-support and m-support are restricted to it; retained
t-values stay in integer twelfths. Permutations and overall sign preserve this
domain, and translations belong to it. The same individual-reflection / mixed-
rotation policy remains. One marking-support layer uses the six sublattice
neighbors ±(2,−1,−1), ±(−1,2,−1), ±(−1,−1,2). Training tries one through three
such layers; this is not just hiding full-lattice markings in the drawing.

The full candidate catalog and one-corona obligations are regenerated using
restricted t-values. `latticePointFilter` passes that restriction to the existing
shared graph engine for classification. Subsequent marked tiling uses the tiler's
matching t-domain and the saved marking's point assignments.
The reducer uses restricted t-capacities when deciding which marking conflicts
must survive point removal, including mark-only overlaps. Cached learners include
the training domain; saved-value comparisons include tile system, lattice and
point assignments. Stored classification evidence is validated on that same
domain. Application in the demo requires the tile system and lattice to match.
No trained point assignments or reports are bundled.

At seed 90210 and 5,000 attempts per pair, browser-equivalent runs give:

| Sublattice inventory | Pairs | Valid accepted | Invalid blocked | Saved? |
| --- | ---: | ---: | ---: | --- |
| Turtle | 247 | 41 / 41 | 176 / 206 | Yes |
| Hat | 227 | 41 / 41 | 166 / 186 | Yes |
| Turtle + Hat | 473 | 71 / 71 | 344 / 402 | Yes |

All these checks resolved under the viable-frontier criterion and all three
models pass the existing save gate. Earlier core-only sublattice checks had
44 Hat and 83 mixed positives, whose equality constraints prevented useful
rejection. The stricter labels yield nontrivial qualifying markings.

Conformance evidence: `tests/test_sublattice_learning.mjs` checks exact restricted
t-data, subgroup-preserving placements and transformations, all catalog witnesses,
independent finite DFS and graph-audited valid/invalid replays per inventory,
exhaustive bounded pair compatibility before/after reduction, domain validation,
and graph-audited marked growth on the matching sublattice.
Storage and browser checks cover per-domain selection, old history, compact
names and automatic tiling on the training lattice. Full-lattice regression
coverage remains in `tests/test_tile_corona_learning.mjs`. The existing generation
scheduler and rollback code are unchanged. One-corona labels certify only their
finite point obligations; growth checkpoints do not prove whole-plane coverage
or geometric faithfulness of the restricted point model.

## Fixed scalar markings for Hat and mixed search

`FixedA2Marking` applies the rank-1 marking to each selected prototype.
`FixedTurtleMarking` retains its existing API and Turtle data. Hat uses scalar
one on the lattice points of chords 0–6, 2–10, 4–12 and 8–10 (indices in
`A2_TILE_LOOPS.hat`), including the selected number of primitive lattice steps
beyond each endpoint. Other positive t-support sites are explicitly zero.
All symmetries transform point locations and leave scalar values unchanged.
The mixed inventory uses the same scalar channel across both prototypes and
retains its six rotations per tile, with no reflections. The renderer draws
these same domains; rank 3 is not defined here for Hat.

These are problem-defining fixed markings, not learned rules or an assertion
that every unmarked patch extends. The search scheduler and rollback algorithm
are unchanged. `tests/test_fixed_a2_marking.mjs` checks the explicit Hat support,
assigned-zero conflicts, extension-only points, scalar transformation under
all orientations, contact rollback, and 12-tile marked growth for each set.
All three pass the engine's frontier graph audit and independent integer t-sum
and m-equality replay; the mixed witness includes both prototypes. The existing
Turtle point-learning regression also passes. These are consistent finite
patches, not infinite-tiling certificates; the activation and geometric-fidelity
gaps in the shared-engine audit above still apply.

## Historical growth-based models: point reduction and comparison

Completed models now carry a `reducedSupport` alongside their original `support`.
The reduced support is used for matching, dependency bookkeeping and drawing.
The dense values remain available for evidence export and the original candidate
ranking, so removing redundant matching points does not change search choices.
Progressive training displays its current dense model; completed and recorded
models are reduced automatically before they reach the tiler.

The reduction removes whole prototype points, including all assigned zero values
at those points. For every allowed relative orientation and integer translation,
we enumerate all unequal overlapping point/channel pairs. Relative placements
already excluded by integer t-capacity need no marking witness. Mark-only overlaps
remain in the enumeration. A point can be deleted only if every previously
forbidden t-legal pair retains at least one disagreement witness. Equivariance
allows the first tile to be fixed at orientation zero. Outside the finite
support-difference bounds there can be no marking overlap. Consequently this
preserves the learned compatibility relation for every legal pair, and therefore
for every finite patch; it is not merely a check against the recorded samples.
This does not prove that the learned hypotheses equal the known marking.

| Inventory | Original points / values | Active points / values | Preserved pair exclusions |
| --- | ---: | ---: | ---: |
| Turtle | 56 / 168 | 30 / 90 | 1,296 |
| Hat | 50 / 150 | 27 / 81 | 1,234 |
| Turtle + Hat | 106 / 318 | 58 / 174 | 2,533 |

`tests/test_marking_reduction.mjs` independently enumerates a rectangular range
of translations from support bounds (rather than using the reducer's conflict
witness generator). It checks 10,500 t-legal relative placements, verifies
identical full/reduced exclusions, rejects tampered reductions, exercises ranking
rollback, and audits the frontier graph during marked growth for all three sets.
Imported reduced supports are checked for whole-point subset membership and for
preservation of every original conflict before use.

The 32-tile comparison uses identical orientation-zero fixed roots, complete
point growth, a budget of 1,500 attempts, seeds 1, 7 and 10, and each inventory's
original reflection policy. Known markings use extent 1: Turtle rank 3, Hat and
mixed rank 1. All modes reached 32 tiles. These are finite consistency checks,
not infinite-tiling certificates or held-out prediction scores.

| Inventory | Known attempts | Learned attempts, dense or reduced |
| --- | ---: | ---: |
| Turtle | 31, 31, 31 | 31, 31, 31 |
| Hat | 34, 34, 34 | 110, 110, 58 |
| Turtle + Hat | 36, 36, 36 | 708, 738, 708 |

Reduced and dense learned searches have identical attempts, backtracks and
placement hashes in all nine runs. Reduced matching took less time in these
single-run measurements; times are machine-dependent and not a speed guarantee.
Hat and mixed learned rules still need substantially more search than known
rank 1. We do not claim parity with known markings for those inventories.

Reproduce with `node scripts/benchmark-compact-markings.mjs /tmp/marking-comparison.json`.
The generated measurements include timings,
reduction cost, roots/settings and placement hashes. No training examples are
held out or removed. The shared engine's existing infinite-coverage and geometric
faithfulness limitations remain unchanged.

### Tooltip marking source

The tooltip reads the transformed, active marking entries of visible placements,
including exterior marking points and explicit zeros. Scalar formatting applies
only to the known rank-1 marking. Learned markings always show their actual
three-component values, regardless of the previously selected known rank;
missing components remain `*`, not implicit zero.

Browser regression checks reproduce the former rank-1-to-learned collapse, then
compare displayed tooltip vectors against independently materialized learned
entries across all three inventories on both lattices, after rank-1 and (for
Turtle) rank-3 selections. This presentation fix does not change t/m values,
classification, candidate pruning, scheduling or rollback.
