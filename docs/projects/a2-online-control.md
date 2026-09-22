# Turtle control audit: the online objective excluded the known marking

## Correction

The [previous online experiment](a2-online-pairs.md) required **every negative
pair to have an immediate conflict between its two marking fields**. That
requirement excludes the known Turtle rank-3, extent-1 marking. Its failed
learned fields therefore do not establish that online GCTS learning is
ineffective, or that useful markings cannot extend beyond small patches.

The control works operationally through the candidate/frontier graph. Its
fixed pair can agree while the remaining candidate placements cannot complete
the surrounding frontier. This distinction must be part of the learning
objective, not discarded by the pair classifier.

This audit corrects the experimental specification and adds executable checks.
It does **not** implement or benchmark a revised online synthesis algorithm.
The existing strict solver is retained as the reproducible historical variant.

## Does the known marking fit the training examples?

System: Turtle only, index-3 sublattice, reflections allowed, known rank-3
marking with extent 1. Use the complete 247-pair catalogue and unmarked
pair-centered one-corona labels from order seed 1: 41 positives, 206 negatives,
no unresolved labels. Completion includes a viable exposed frontier.

The known field has **39 assigned components**, all representable inside the
learner's original 90-slot, halo-1 domain. Its transformation agrees exactly
with the sparse learned-marking representation on every catalogue pair. The
failure is therefore not missing support, integer values, or a different
reflection/component action.

| Test | Known marking result |
| --- | ---: |
| Positive fixed pairs with agreeing markings | 41 / 41 |
| Positive pairs with a completed marked one-corona | 41 / 41 |
| Negative fixed pairs with an immediate marking conflict | 193 / 206 |
| Remaining negatives with an immediately dead frontier | 8 |
| Remaining negatives exhausted after 1–2 placement attempts | 5 |
| Total negatives rejected by direct conflict or frontier search | 206 / 206 |

The 13 directly compatible negatives needed 32 placement attempts in the
original unmarked probes, versus 6 in total with the known marking. Eight
required no additional placement; five required one or two. Counts concern
search attempts, not complete elapsed-time speedups.

Pinning the known field in the historical SMT encoding confirms the mismatch:
all positive constraints are satisfiable, but requiring all 206 direct negative
conflicts is unsatisfiable. The first excluding constraint arrives at pair 13
in order seed 1. Allowing 193 direct exclusions admits the pinned control.
That count is a diagnostic measurement, **not a proposed learning target**.
The known assignments are never used to initialize a learner.

There is also a distinction between a positive pair and its first-found
completion: the known marking rejects 2 of the 41 original unmarked witnesses,
yet finds alternative marked completions for all 41 pairs. Freezing arbitrary
first-found witnesses would unnecessarily exclude it again.

## Longer growth controls

All runs use the actual GCTS-I `solveA2Tiling`, its complete point/candidate
graph, global dead/forced handling and generation-first growth scheduler.
Each starts from the same single rooted Turtle. Reflections and index-3
filtering are identical across arms. Each returned patch passes independent
capacity, marking and frontier replay using `verifyGrowth`.

### Matched 128-tile target

Both arms have a 60-second limit and marking score zero, so the marking only
changes candidate legality. Runs are sequential; arm order reverses for seed 3.
These are reuse measurements: there is no learning or synthesis in either arm.

| Seed | No marking | Known extent-1 marking |
| --- | --- | --- |
| 1 | Time limit: 88 tiles in 60 s | Reached 128 tiles in 3.70 s |
| 3 | Time limit: 88 tiles in 60 s | Reached 128 tiles in 2.95 s |

The known marking reaches the same finite target within the budget while the
unmarked search does not. Unmarked completion times remain unknown; no exact
completion-time speedup ratio is claimed.

### Larger target: 1,000 tiles, 60 seconds per arm

The learned arm uses the previous strict pair-only Turtle model after all 247
labels in training order 1. Score is again zero in all arms.

| Arm | Seed | Outcome | Retained tiles | Placement attempts | Backtracks |
| --- | ---: | --- | ---: | ---: | ---: |
| No marking | 1 | Time limit | 88 | 7,827 | 7,743 |
| Known extent 1 | 1 | Time limit | 362 | 1,536 | 1,232 |
| Strict learned | 1 | Exhausted in 0.068 s | 5 | 14 | 14 |
| No marking | 3 | Time limit | 88 | 8,085 | 8,001 |
| Known extent 1 | 3 | Time limit | 175 | 4,657 | 4,553 |
| Strict learned | 3 | Exhausted in 0.065 s | 5 | 14 | 14 |

Giving the old learned marking more time cannot repair that exhausted search.
Conversely, the known marking supports substantially larger finite viable
patches. None of the arms reached 1,000, so this table is a progress comparison,
not a comparison of completion times.

A separate reference run enabled the normal GCTS-I marking score, with a
500-tile target and **120-second** limit. Seeds 1 and 3 retained 362 and 175
tiles respectively, then timed out. These are still unknown results, not
exhaustion or evidence of an obstruction to infinite tiling. This extra run
changes both ranking and budget; it is not a controlled measurement of the
effect of doubling the time.

## What the learning objective needs

1. Keep positive pairs compatible and allow a choice of marked completions.
   Passing the fixed pair alone is insufficient; preserving every particular
   unmarked witness is too restrictive.
2. Separate **direct pair disagreement** from **rejection through frontier
   search**. A useful marking need not make every negative disagree immediately.
   Alternatives include optimizing a subset of direct exclusions, or encoding
   candidate eliminations that make a frontier point dead. Neither alternative
   is implemented by this audit, and neither alone guarantees large extension.
   Operational classification alone is also insufficient as an optimization
   goal: exhaustive unmarked search already rejects these negatives. Measure
   candidate eliminations and total search cost, including synthesis and replay,
   to establish an improvement.
3. Continue to use independent unmarked exhaustion for negative-label authority.
   Failure under a provisional marking is not evidence that an unmarked pair
   is impossible. Limits mean unknown.
4. Check that the known control is admissible before interpreting a new failed
   synthesis run. Keep it outside training. Validate learned completions and
   larger growth separately; do not infer these from a perfect pair score.

The longer controls establish the known marking's benefit at a finite target
and expose an overly restrictive objective in the earlier learner. A successful
revised **online-learning** speedup remains to be demonstrated.

## Reproduce and conformance

Requires Node and Python with `z3-solver` (tested 4.16.0). Generated supports,
witnesses and contact constraints stay under `/tmp`, outside the repository.
Only aggregate measurements are published in
[the control data](../../data/a2-online-control-2026-09-22.json).

```sh
# Generate the prior unmarked labels and strict learned model if absent.
node scripts/experiment-a2-online-pairs.mjs --tile=turtle --mode=baseline --seed=1
node scripts/experiment-a2-online-pairs.mjs --tile=turtle --mode=online --positive=pair --seed=1

node scripts/audit-a2-turtle-known-control.mjs
python3 scripts/test_a2_known_control_smt.py
node scripts/benchmark-a2-online-control.mjs
node scripts/benchmark-a2-online-control.mjs --arms=known --score=demo --target=500 --ms=120000 --label=demo-reference
node scripts/benchmark-a2-online-control.mjs --arms=unmarked,known --target=128 --ms=60000 --label=target128
```

The audit asserts all reported pair outcomes, exact known/sparse action,
representability, and independent successful-corona replay. The SMT regression
checks pinned-control admission and exclusion. Growth replay checks the final
retained patch independently. Complete negative exhaustion still relies on
the existing engine; there is no independent exhaustive-search certificate.

Pair-corona probes retain the reference finite-core boundary semantics: global
dead points are checked, but forced moves and branching are restricted to the
pair core while the exposed exterior requires viability. Growth benchmarks
use the normal whole-frontier scheduler. All experiments ran sequentially.
This is a Turtle/index-3 audit, not a Hat or full-lattice validation. No browser
demo code, generated learned assignments, or placement traces were changed
or bundled.
