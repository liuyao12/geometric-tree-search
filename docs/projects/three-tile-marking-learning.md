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

The current experiment enumerates every t-legal second placement whose positive
support touches the fixed first tile. Both root types are included for the mixed
inventory. These are ordered, rooted connections, not symmetry-orbit counts.
Turtle and Hat each allow 12 orientations including reflections; Turtle + Hat
allows six rotations per prototype and no reflections.

Each pair is classified **before any marking is trained**. A complete one-corona
means that every point in the union of the two core tiles' positive t-support
has total t-value 1 (integer capacity 12). The two core tiles remain fixed.
Additional tiles must respect capacity everywhere, including outside the core;
their outer boundary need not be completed. Every added tile touches a required
core point. This is a finite point-domain criterion, not a tile-count checkpoint
or a claim of infinite extendibility. Polygon outlines are only illustrations.

The unmarked search returns:

- **Valid:** a complete corona with independently verified integer capacities.
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
**only when the complete catalog is resolved and every classification agrees**.
The gate checks catalog coverage, uniqueness, counts and actual marking decisions.
An imperfect candidate remains visible with its errors and point/value metadata;
JSON export retains evidence but does not promote it to an installed marking.
Retries keep the same corona criterion and increase the selected unresolved
pair's budget. A timeout cannot replace an already resolved result.

### Recorded results

Seed 90210, 5,000 attempted placements per pair:

| Inventory | Pairs | Valid | Invalid | Unresolved | Correct marking classifications | Invalid pairs still accepted |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Turtle | 304 | 41 | 263 | 0 | 277 / 304 (91.1%) | 27 |
| Hat | 320 | 41 | 279 | 0 | 303 / 320 (94.7%) | 17 |
| Turtle + Hat | 624 | 82 | 542 | 0 | 583 / 624 (93.4%) | 41 |

Increasing the domain through three layers did not improve these scores. All
valid pairs are accepted, but no candidate reaches 100%, so **none is saved**.
`assets/data/tile-corona-markings.json` therefore has an empty model map.
`assets/data/tile-corona-{turtle,hat,mixed}.json` contains all labels, witnesses,
search settings, candidate values and training-domain trials. The ordinary
rank-1/rank-3 tiling modes remain available. Old provisional models are rejected
by the new gate; the learned option is disabled without an approved model.

Accepted models, when available, persist per inventory in local storage and
transfer automatically by the existing same-origin iframe message. Import
validation checks every recorded label against the marking; it does not rerun
all oracle searches or independently certify the provenance of external labels.
Recorded invalid cases have replayable settings, not formal proof transcripts.
Even perfect pair classification would certify only this finite criterion;
mark-only interactions beyond the audited pairs remain learned restrictions.

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
Only these points belong to the frontier. Candidate validity still depends on
all t- and m-support, including exterior points. Completion checks all required
capacities and ignores tile-count milestones. The normal growth mode is unchanged.

The complete point/candidate graph, global dead-before-forced order,
earliest-generation branching, orientation enumeration and exact rollback are
retained. Corona classification always uses `NoA2Marking`, so candidate markings
cannot create their own negative labels. Integer t-values and independent integer
witness verification support the exact finite result; the engine's generic
comparison tolerances do not substitute for that verification. No geometric
collision predicate is added. Conventional polygon fidelity and whole-plane
coverage are not established by these runs.

`tests/test_tile_corona_learning.mjs` checks all 1,248 catalog entries, all valid
corona witnesses, each candidate's predictions, incomplete/imperfect save gates,
and zero-budget semantics. An independent finite DFS agrees on one valid and the
hardest recorded invalid case per inventory; graph-audited engine replays agree
on the same cases. This is representative negative-search cross-checking, not
an independent reproof of every negative. Existing fixed-marking and Turtle
regressions also pass. Browser checks cover all three reports, automatic Turtle
collection, no imperfect transfers, old-model rejection, unresolved searches,
usual tiling controls and mobile/scroll tab behavior.

Regenerate and verify:

```
node scripts/train-tile-corona-markings.mjs /tmp/pair-corona-markings
node tests/test_tile_corona_learning.mjs
node tests/test_fixed_a2_marking.mjs
node tests/test_turtle_point_learning.mjs
```

The older `tile-connections-*` data, `tile-markings.json` and associated scripts
are retained as historical growth-checkpoint experiments. They are no longer
loaded by the active learning or tiling panels. The historical comparison below
applies to those old models, not to the current unapproved corona candidates.

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

Reproduce with `node scripts/benchmark-compact-markings.mjs output.json`.
[Full measurements](../../assets/data/marking-comparison.json) include timings,
reduction cost, roots/settings and placement hashes. No training examples are
held out or removed. The shared engine's existing infinite-coverage and geometric
faithfulness limitations remain unchanged.
