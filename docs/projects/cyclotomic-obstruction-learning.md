# Learning GCTS markings without known bars

The experimental learner takes a finite exact tile/orientation catalog in
Q(zeta_5), corner weights, and the problem's geometric and local constraints.
It does not read Ammann bars, line families, reference patches, or labels
obtained from known markings. Shape alone does not identify a desired
aperiodicity rule; supplied edge arrows are common inputs to the plain and
learned P3 searches. Known Ammann markings remain a separate benchmark.

## Learn only from a certified obstruction

The ordinary point–candidate graph drives the search: propagate forced moves,
select a smallest nontrivial domain, and backtrack on a dead point. On reaching
a dead point p, examine pairs of placed tiles. A pair can teach a rule only
when an independent finite check proves it cannot be completed around p.

First try the cheap certificate: every candidate incident at p is blocked by
one of the two tiles or exceeds the remaining corner capacity. Otherwise,
exhaustively try subsets of compatible candidates that would complete the
corner weight at p. Other frontier obligations are relaxed, making failure
sound: even the relaxed problem cannot complete. Success proves only local
fillability. A capped check is inconclusive and teaches nothing.

The candidate list comes from exact vertex alignment of the finite oriented
catalog, not from enumerating a Euclidean disk in the projected ring. Integral
input gives integral offsets; rational input stays exactly in Q(zeta_5).
The implementation assumes positive corner weights and a finite supplied
orientation group (the default uses rotations by powers of -zeta_5 and
conjugation). It does not enumerate every possible field rotation.

A general failed cluster must not be mislabeled a forbidden pair. If no pair
certificate exists, the current implementation learns no global rule. Local
failed-child exclusions still roll back with their search context. At most one
new pair orbit is learned at a dead-point event; lessons persist across
backtracking and revalidate the point–candidate graph transactionally.

## Compile the proof into actual point values

A blocker bitset is useful for obtaining a proof, but it is **not** the GCTS
matching rule. Runtime matching is equality of partial values on coincident
points, as in the main project definition.

For a proven impossible pair with oriented types A,B and origins a,b, allocate
a fresh channel. Choose the certified obstruction point p. Put value 0 on A at local point
p-a and value 1 on B at local point p-b. The placements then disagree at world
point p. Shared-vertex certificates therefore need no new geometric addresses. This rejects exactly
that forbidden relative placement, including the reverse unordered pair.
Missing channels remain undefined, not zero. Different proofs have separate
channels, preventing accidental conflicts between unrelated rules.

Apply every allowed rigid action g to both tiles and to the witness p; the
new world witness is g(p), which need not be the canonical origin of g(A).
The group acts by permuting the resulting channels. Tests check both the exact
forbidden relative-pair orbit and the equivariance of the actual point values.
This is an adaptive finite-rank marking, not a claim to rediscover the classical
five-family Ammann decoration. Runtime packs binary channel values into bitsets
only to accelerate the same equality test.

Previously certified rules can be frozen and reused. Loading rechecks the
certificates from the problem constraints; a saved claim is not trusted merely
because an earlier run recorded it. Initial learning starts with no points.

## Implementation and evaluation

- `assets/cyclotomic-tile-catalog.js`: exact finite catalog and symmetry adapter.
- `assets/cyclotomic-local-certificate.js`: finite relaxed point-completion proof.
- `assets/cyclotomic-obstruction-marking.js`: direct dead-point proof harvester.
- `assets/cyclotomic-pair-marking.js`: equivariant partial-point compiler/matcher.
- `assets/cyclotomic-obstruction-search.js`: shared baseline and learned search.
- `scripts/penrose-blind-problem.mjs`: independent P3 shape/arrow input.
- `scripts/penrose-known-benchmark.mjs`: isolated continuous Ammann benchmark.

Run `node scripts/test-cyclotomic-pair-marking.mjs`,
`node scripts/test-cyclotomic-obstruction.mjs`, and
`node scripts/test-tiling-frontier-graph.mjs` for the representation,
certificates, rational non-Penrose fixture, and rollback checks.
`node scripts/benchmark-cyclotomic-validation.mjs` measures cold training and
three alternating-order repetitions on four held-out seeds. Every lane uses
a fresh problem and the same 30-tile target. Frozen runtime includes certificate
loading and verification. Known bars add stronger constraints and are reported
as a separate lane, never used to teach the learner.

Performance results are experimental, tied to the stated input/target, and
must include the training cost. A tile-count target is not a common-corona
benchmark. A separate experimental page presents cold online learning, plain search,
and known bars; the working Ammann demo remains available.

The failure-recording principle is related to constraint learning: Dechter,
[Learning While Searching in Constraint-Satisfaction-Problems (1986)](https://cdn.aaai.org/AAAI/1986/AAAI86-029.pdf).
The exact sparse equivariant point compilation above is the proposed
implementation here, rather than a claim that the paper supplies these markings.

## Recorded result (2026-09-08)

Three alternating-order repetitions on held-out seeds 5, 11, 23, 47,
with fresh problem instances and a 30-tile target, gave 44.34 seconds total
for plain search and 18.62 seconds for the frozen learned model (2.38×).
Training on seeds 1 and 17 cost 7.25 seconds. At the measured mean saving,
that cost is recovered after about four reused runs. The model has 31 pair
orbits and 100 geometric addresses across 20 oriented tile types, with 620
binary channels. Channel entries are not additional geometric points.

A separate seed-5 corona-3 check reached the same frontier depth in 2.38 seconds
with the frozen model, versus 6.09 seconds plain and 25.54 seconds with known
continuous bars. The patches had different tile counts (104, 92, and 140).
This single corona run is a check, not a repeated corona-speed claim. Known
bars substantially reduce proposals, but the current continuous implementation
has a high per-check cost. These measurements do not imply that cold online
learning is faster on every run or that the learned marking is Ammann-equivalent.

The worker separately passed cold online pause/continue checks at coronas 3
and 5 (159 and 298 tiles). Source and the complete timing/certificate report
are published alongside the experimental page; no local preview was used.
See [recorded benchmark](../cyclotomic-learning-benchmark.json).

## Main app: concurrent lanes and memory counts

The main Penrose entry point now runs learned points, explicit edge arrows,
and continuous Ammann bars in independent workers. Run all advances each to
the shared corona milestone; a completed lane waits while others continue.
Lane selection changes only the canvas and inspection, not the search. Pause
all stops scheduling new batches, Continue all advances the milestone, and
Reset all replaces all workers and empties the learner. The previous P1/P2/P3
app remains at `apps/penrose-model-set/ammann.html`.

Memory cost is reported as logical records rather than estimated bytes:
unique oriented-template point addresses and defined scalar entries; active
world marking addresses and stored 0/1 values; active t-field points and
values; current graph candidate records and legal incidences; and learner
certificate/cache counts. Undefined components are not stored values. The
Ammann lane instead reports continuous segment geometry, endpoint references,
and family labels, without inventing a discrete marking table. These are not
total heap measurements: object overhead, undo closures, geometry caches,
and message/display copies are excluded.

## P1, P2, P3 and mixed selections

The main selector offers P3 rhombs, P2 kite/dart, P1 pentagonal tiles, all tiles,
and arbitrary subsets. A selection change resets all three workers to the
same allowed catalog. Switching lanes continues to preserve their searches.
Pure rhomb selections retain the independent arrow input. P1/P2 and mixed
selections use the boundary-only dataset in `penrose-local-templates.js`,
exported from the existing transferred decorations. These are supplied local
rules, not a claim to infer aperiodicity from undecorated P1/P2 shapes.

Each port records an exact point and an unoriented normal axis. Both transform
under the rigid action; the learner never receives bar interiors or extension
geometry. Tests compare shared-edge decisions with the existing boundary
extractor and verify known decorations survive quotienting by symmetries.
The benchmark reconstructs its bars separately from template rigid transforms.

Mixed inputs use the existing common scale and whole-edge convention. P1
cannot share whole edges with P2/P3 at that scale; mixed P2/P3 can be attempted.
Selecting a tile permits it rather than requiring it, and an arbitrary subset
may exhaust its frontier. No mixed input is promised an infinite Penrose tiling.

## Performance repair (2026-09-08)

The multi-set app repeatedly normalized small exact coordinates with BigInt,
reconstructed boundary labels for discarded candidates, repeated equivalent
relative-pair tests, exported full models/proof tables every display batch,
and translated each displayed point once per scalar fiber value. Three workers
amplified the serialization and main-thread rendering cost.

The repaired implementation uses checked safe-integer arithmetic with the
original BigInt fallback; lazy boundary labels; bounded relative-pair caches
(8192 results per predicate); lightweight corona checks; cached model exports;
compact worker frames with model definitions only when their revision changes;
and display caches grouped by geometric address. Batches run for approximately
50 ms, with Step and exact corona pauses retained. The geometric and Ammann
predicates are unchanged; cached predicates exclude dynamic capacity and learned
constraints. No branch ordering or proof criterion was weakened.

Two alternating-order comparisons against commit `1e5094b69` gave:

| Benchmark | Before | After | Speedup |
| --- | ---: | ---: | ---: |
| P3, corona 3, worker + display preparation | 15.89 s | 2.12 s | 7.49× |
| P2, eight-tile core search | 0.98 s | 0.30 s | 3.29× |
| P1, eight-tile core search | 19.67 s | 7.11 s | 2.77× |

P3 reached the same 159 tiles with 380 proposals and 28 rules. Its display
traffic dropped from approximately 55.8 MB to 1.25 MB. P1/P2 full event traces
and learned table hashes agree exactly across versions. The P3 benchmark
includes structured cloning and point-display preparation, not browser paint
or three-worker CPU contention; these timings are not universal device promises.
See [performance report](../penrose-speed-report.json).

The optimized arithmetic was compared with the former BigInt implementation
on 60,000 randomized operations, including large coefficients and overflow.
Additional checks cover relative-pair translation invariance and eviction,
all tile sets, graph rollback, model delta messages, cached point inspection,
known-bar rendering data, and corona-3/5 continuation.

### Individual search controls

The main app now runs one selected method at a time. Switching methods pauses
the current search and keeps its patch, marking, corona target, and elapsed
active time. Workers initialize lazily; a pending batch finishes before another
worker receives work. Run/Continue and Step affect only the selected method,
and Reset clears only that method. Changing allowed tiles clears all methods.
The timer accumulates worker-request time (including initialization and snapshot
delivery), excludes idle/paused time, and resumes from its retained total.
The controller test covers exclusive dispatch, independent milestones, compact
model retention, pause/resume timing, and reset/stale-result isolation.
