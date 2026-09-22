# Online marking synthesis during pair-corona search

> **Correction after testing the known Turtle control:** this experiment
> required every negative pair to disagree immediately. That excludes the
> known extent-1 marking: it directly rejects 193/206 negatives and rejects
> the other 13 through frontier search, while completing all 41 positives.
> The measurements below remain valid for this overly restrictive variant;
> they do not test the broader operational learning objective successfully.
> See the [control audit and longer runs](a2-online-control.md).

## Result

The requested feedback loop was implemented headlessly and tested on Turtle
and Hat, starting with **no marking** and no previously collected labels.
This configuration did **not** accelerate collection. It also exposed two
failures that must be addressed before adopting the loop in the demo:

1. A marking can perfectly classify every labeled pair yet prevent essentially
   all larger marked growth. Passing the positive pair does not ensure that
   its surrounding tiles can carry the same marking.
2. Requiring every first-found positive corona to remain compatible is too
   strong. Some of those finite witnesses contain boundary pairs that later
   receive exhaustive negative labels. Keeping that whole witness and forbidding
   that pair are contradictory requirements.

These are results for the tested solver, support choices and pair orders,
not impossibility claims about online GCTS learning or all possible markings.
The previous [staged experiment](a2-corona-workflow.md) retained several
markings and did not require perfect rejection of every negative attachment;
its successful Turtle fields do not contradict this result.

## Protocol

- Turtle only and Hat only; index-3 sublattice; reflections allowed; three
  components transforming by permutation and permutation parity.
- Complete capacity-legal neighboring pair catalogues: 247 Turtle and 227 Hat
  pairs. This time the label is the GCTS-I **pair-centered** one-corona criterion,
  including viable exposed frontier, not the earlier rooted-tile criterion.
- Two shuffled orders, seeds 1 and 3, with matched per-pair search seeds.
  No sample holdout and no future labels available to synthesis.
- Actual GCTS-I `solveA2Tiling`; every arm uses marking score zero. The marking
  changes candidate legality through the existing graph, not a separate pair
  classifier replacing point-value matching.
- Unmarked oracle: up to 5,000 attempts / 1,500 ms per pair. Provisional marked
  probe: up to 128 attempts / 150 ms. Every oracle label resolved in these runs.
- After each resolved label, an incremental **Z3 4.16.0 SMT solver** chooses
  Boolean assigned/free slots and integer values. Positive assigned overlaps
  must agree; every negative pair has a disjunction of assigned disagreements.
- Values are bounded by ±N for N prototype slots. This does not restrict the
  signed equality/disequality partitions: zero and at most N distinct magnitudes
  suffice. Zero is an assigned value; `*` is absence.
- Initial support is a one-sublattice-step halo around the tile. On UNSAT,
  retry with a larger halo, up to three. Each check has a 500 ms solver timeout.
  UNSAT/unknown disables the marking. It does not label a geometric pair.
- After SAT, greedily omit individual components while retaining a witness for
  every observed negative. Deletion preserves existing positive agreement;
  this is not a minimum-support optimization or a search of all SAT solutions.
  Independently replay every observed constraint before activating a revision.
- Freeze each revision for its next pair query and start a fresh search graph;
  no stale graph or rollback trail crosses revisions.

### Label authority

A marked success supplies a positive only after independent unmarked
capacity/core/frontier replay. If the marking rejects the fixed pair, its
search exhausts, or its probe times out, run the unmarked oracle. A negative
requires an exhausted **unmarked** search. A provisional rejection is never
silently promoted into a negative sample.

The baseline always uses the unmarked oracle. The online arms use either
**pair-only** positive constraints, or stronger **whole-witness** positive
constraints. The latter is a diagnostic control for the missing surrounding
agreements, not a recommendation to freeze arbitrary completions permanently.

## Measurements

All catalogues resolved completely. Turtle had 41 positive / 206 negative
pairs; Hat had 41 positive / 186 negative pairs. Both online variants reproduced
every baseline label.

### Cold collection: no early speedup

| Tile / order seed | Unmarked | Online pair-only | Online whole-witness |
| --- | ---: | ---: | ---: |
| Turtle / 1 | 4.42 s | 15.34 s | 25.11 s |
| Turtle / 3 | 4.34 s | 14.69 s | 34.60 s |
| Hat / 1 | 3.07 s | 11.47 s | 12.19 s |
| Hat / 3 | 3.24 s | 10.74 s | 10.78 s |

These totals include startup, search, SMT, label replay, failed marked probes
and unmarked fallbacks. Pair-only SMT accounted for about 6.4–9.8 seconds per
run. The unmarked local checks are relatively cheap on this sublattice; none of
the online runs was faster even when synthesis time was excluded.

### Did the marking find the next positive completion?

| Tile / seed | Positive completions found with pair-only marking | Positive completions found with whole-witness marking | False negatives avoided: pair-only | False negatives avoided: whole-witness |
| --- | ---: | ---: | ---: | ---: |
| Turtle / 1 | 0 | 17 | 41 | 4 |
| Turtle / 3 | 3 | 11 | 38 | 3 |
| Hat / 1 | 0 | 13 | 41 | 4 |
| Hat / 3 | 1 | 4 | 39 | 2 |

“False negatives avoided” counts restricted-pair or exhausted marked searches
that the unmarked fallback subsequently completed. Timeouts rescued by fallback
are counted separately in the aggregate data. A marked search failure must not
be treated as a negative label. Whole-witness markings were disabled after their
constraints became UNSAT or solver-unknown; later labels then used unmarked search.

### Could the intermediate markings tile?

Markings were frozen after 16, 64, 128 and all pairs from training order 1.
Each was tested from a single seed tile using growth seeds 1 and 3, targeting
100 tiles with a 3-second limit. These are reuse tests, excluding prefix learning.
No tested checkpoint reached 100. The final **pair-only** models perfectly fit
all labels but both exhausted their marked searches, retaining only five-tile
viable patches. This failure concerns those particular marking models.

| Tile / model at checkpoint | Assigned values | Seed 1: outcome / retained tiles | Seed 3: outcome / retained tiles |
| --- | ---: | --- | --- |
| Turtle / unmarked | 0 | Time limit / 53 | Time limit / 53 |
| Turtle / pair-16 | 11 | Exhausted / 6 | Exhausted / 6 |
| Turtle / pair-64 | 16 | Exhausted / 2 | Exhausted / 2 |
| Turtle / pair-128 | 22 | Exhausted / 2 | Exhausted / 2 |
| Turtle / pair-247 | 24 | Exhausted / 5 | Exhausted / 5 |
| Turtle / witness-16 | 14 | Exhausted / 22 | Exhausted / 22 |
| Turtle / witness-64 | 21 | Exhausted / 66 | Exhausted / 66 |
| Turtle / witness-128 (disabled; unmarked) | 0 | Time limit / 53 | Time limit / 53 |
| Turtle / witness-247 (disabled; unmarked) | 0 | Time limit / 53 | Time limit / 53 |
| Hat / unmarked | 0 | Time limit / 73 | Time limit / 38 |
| Hat / pair-16 | 9 | Exhausted / 7 | Exhausted / 7 |
| Hat / pair-64 | 18 | Exhausted / 2 | Exhausted / 2 |
| Hat / pair-128 | 23 | Exhausted / 1 | Exhausted / 1 |
| Hat / pair-227 | 23 | Exhausted / 5 | Exhausted / 5 |
| Hat / witness-16 | 10 | Time limit / 45 | Time limit / 47 |
| Hat / witness-64 | 19 | Exhausted / 22 | Exhausted / 22 |
| Hat / witness-128 (disabled; unmarked) | 0 | Time limit / 73 | Time limit / 38 |
| Hat / witness-227 (disabled; unmarked) | 0 | Time limit / 73 | Time limit / 38 |

Before their inconsistent constraints accumulated, witness-based Turtle fields
retained up to 66 tiles, an improvement over the tested pair-only models but
still an exhausted marked search below the target. Later disabled-model rows
are explicitly unmarked controls, not successful learned markings.

[Aggregate data](../../data/a2-online-pairs-2026-09-22.json) contain all collection
costs, update statuses, checkpoint timings and verification results.

## Why keeping all completed witnesses fails

The diagnostic normalizes every ordered two-tile subpatch of each positive
witness to a rooted pair and checks it against previously/finally classified
negatives. It verifies the transformation by exact t-support coordinates and
weights, not just an orientation ID. All four whole-witness runs contain a
positive witness and a transformed negative pair inside that witness:

| Tile / order seed | First prefix with a contradiction | Positive witness obtained at pair | Negative pair labeled at pair |
| --- | ---: | ---: | ---: |
| Turtle / 1 | 102 | 102 | 45 |
| Turtle / 3 | 84 | 14 | 84 |
| Hat / 1 | 84 | 13 | 84 |
| Hat / 3 | 49 | 10 | 49 |

Under the shared equivariant marking action, a field **directly** rejecting that
negative pair must also reject its transformed copy inside the witness. This is a direct
inconsistency between those two training requirements, independent of how large
the marking halo is. Z3 timeouts earlier in the run are still reported as
unknown; this separate diagnostic supplies the concrete inconsistency.

A finite viable corona is not a certificate that each of its boundary pairs
can be surrounded in turn. The positive **root pair** can remain a positive
local example while this particular completed witness is discarded. A next
implementation should allow alternative completions instead of requiring all
first-found witnesses simultaneously.

## Verification, limits and next implication

- Independent replay verified every positive witness and every snapshot's
  prefix constraints; contact encoding agrees with direct transformed-marking
  comparisons, including individual free entries and signed values.
- All 1,896 online labels exactly match their corresponding baseline labels.
  Every online negative has its own exhausted unmarked oracle call.
- SMT unit tests cover initial empty support, assigned zero, free variables
  breaking equality paths, contradictory labels and incremental negatives.
- Both tiled checkpoints and explicit witness contradictions were independently
  checked. Complete unmarked negative searches use the existing engine; no
  external exhaustive certificate is claimed.
- The finite pair-corona mode checks global dead points but only forces/branches
  inside the pair core; the exterior is a viability boundary. Unbounded tiling
  checkpoints use the normal whole-frontier generation scheduler.
- Pair search, SMT, fallback, validation and process overhead are charged to
  cold collection time. Checkpoint tiling timings exclude prefix learning and
  therefore cannot establish an earlier end-to-end speedup.
- These are two pair orders and one solver model-selection policy. This does
  not exhaust the space of markings, full-lattice systems, or mixed tile sets.

The test supports an online **hypothesis-and-correction** loop, but not treating
a provisional marking as a sound rejection oracle. Useful next constraints
would preserve a choice among positive completions and reject marking models
whose own marked growth exhausts, while keeping alternatives available. That
selection problem was not solved by this initial experiment.

## Reproduce

Install Python's `z3-solver` (tested 4.16.0). Node runs the existing tiling engine;
a persistent Python process handles SMT requests. Generated files default to
`/tmp/a2-online-pairs` and remain outside the repository.

```sh
# Repeat these three commands for --tile=hat and --seed=3.
node scripts/experiment-a2-online-pairs.mjs --tile=turtle --mode=baseline --seed=1
node scripts/experiment-a2-online-pairs.mjs --tile=turtle --mode=online --positive=pair --seed=1
node scripts/experiment-a2-online-pairs.mjs --tile=turtle --mode=online --positive=witness --seed=1
python3 scripts/test_a2_online_marking_sat.py
node scripts/test-a2-online-pairs.mjs
node scripts/diagnose-a2-online-pairs.mjs
node scripts/benchmark-a2-online-pair-checkpoints.mjs
```

Recorded collection order: Turtle then Hat; for each, baseline → pair-only →
whole-witness at seed 1, reversed at seed 3. All collection and checkpoint jobs
ran sequentially without concurrent experiment jobs. The main browser demo was
not changed, and no generated markings, witnesses or placement traces are bundled.
