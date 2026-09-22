# Learning and extending a family of markings

This experiment tests the workflow proposed after the
[known-marking consensus experiment](a2-corona-consensus.md): start with no
marking, complete the rooted one-corona catalogue, synthesize several different
markings, and repeatedly enumerate and intersect larger marked coronas.

## Exact scope

The two systems are Turtle only and Hat only, each on the index-3 sublattice,
with all 12 orientations including reflections. The t-values use integer
units of capacity 12. A corona uses positive t-support contact; its inner
layers are filled and its exposed frontier has a legal candidate at every
point. This is a finite point-model experiment, not an infinite-tiling proof.
The mixed rotation-only system and full lattice are not tested here.

The initial catalogue is around **one rooted tile**. A capacity-legal attachment
is positive exactly when it occurs in some complete viable rooted one-corona;
it is negative if it occurs in none. This is different from the GCTS-I learner's
stronger one-corona-around-a-fixed-pair criterion. No holdout or known marking
is used. Every original corona, including all its boundary-to-boundary marking
overlaps, contributes agreement constraints.

## The marking space actually searched

Each prototype domain is within one sublattice step of the tile's t-support,
and is further restricted to points covered by **every** original one-corona.
Every point has three independently optional components. Transformations
permute components and multiply labels by the permutation parity, as in the
GCTS-I signed rank-3 learner. Both tiles use this action; the previous known
Hat control used a scalar rank-1 action and is a different hypothesis class.

For a chosen assigned/free support, the solver rebuilds all signed positive
equalities. An odd signed cycle forces zero; other equivalence classes receive
distinct signed integer labels. Thus each fixed support receives its most
separating equality solution. Negatives are scored by whether at least one
assigned overlap disagrees. Making a component `*` removes its incident
constraints **before** solving again.

A seeded coordinate search tries 32 starting supports, at most six improving
single-component changes per start. It also evaluates the fully assigned
support. Final candidates from those starts are deduplicated by their decisions on the complete
attachment catalogue, so retained alternatives are not just label renamings.
We retain the best three by negative rejection count, then support size.
This is a bounded search through support patterns, not a complete SAT solution
space or a proof of optimal classification. Label-class mergers and other
representation actions are not searched.

## Staged continuation

For each retained marking independently:

1. Reduce support while retaining all capacity-legal pair conflicts, including
   pairs that meet only in marking support.
2. Completely enumerate its marked one-coronas and intersect their glued
   sections. A missing or varying component remains `*`.
3. Reduce that intersection and use it to enumerate two-coronas.
4. Repeat with three-coronas. Promote only complete, nonempty catalogues.

At every stage the enumeration is fresh under the new marking. We do not just
filter the previously saved unmarked catalogue. Each completed extension
preserves global tilings compatible with that candidate's initial marking.
Initial learned markings remain restrictions: fitting every finite one-corona
does not prove preservation of every unmarked global tiling.

A finite original corona can lose frontier viability under the learned marking
while all its placed marking values agree. Likewise a later extension can
exclude previously accepted finite boundary arrangements. These are distinct
checks, not a contradiction in the positive training constraints.

## Measurements

All reported counts are for one prototype. A/B/C refer to separately learned
restrictions, ordered by their initial failed-attachment rejection score.

| System | Complete unmarked 1-coronas | Positive attachments | Negative attachments | Fully assigned: negatives blocked | Best with `*` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Turtle | 74 | 41 | 206 | 176 | 193 |
| Hat | 105 | 44 | 183 | 0 | 102 |

The support search retained eight distinct endpoint decision patterns for Turtle
and six for Hat, of which three each were continued. It tested 17,313 support
fits for Turtle and 15,009 for Hat. All original whole coronas pass every
retained initial marking.

### How the fields developed

| System / marking | Initial negatives blocked | Initial compact values | After round 1 | After round 2 | After round 3 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Turtle A | 193/206 | 30 | 36 | 61 | 99 |
| Turtle B | 191/206 | 24 | 24 | 30 | 36 |
| Turtle C | 188/206 | 28 | 29 | 37 | Unknown; not promoted |
| Hat A | 102/183 | 16 | 18 | 22 | Unknown; not promoted |
| Hat B | 83/183 | 19 | 23 | 36 | Unknown; not promoted |
| Hat C | 48/183 | 23 | 29 | 81 | Unknown; not promoted |

Turtle B initially gained **no** common values, but did gain values at the next
two radii. Turtle A completed 37, 360 and 1,945 marked coronas at successive
stages; B completed 37, 385 and 2,592. A’s final intersection has 103 assigned
values before reduction and 99 on 77 points afterward. These catalogues use
different input markings at each radius and should not be compared as a
single nested sequence of unmarked catalogue counts.

Turtle A’s first third-round attempt timed out after 60.03 seconds. A retry
completed in 67.16 seconds; both costs are retained. Turtle C and all three
Hat alternatives have incomplete third rounds. Their provisional intersections
were excluded from growth tests. Every retained alternative completed two rounds.

### Actual GCTS-I growth

Target: 100 tiles; limit: 6 seconds and 100,000 attempts. Seeds: 1 and 3.
All marking scores are zero. Arms run sequentially, in reverse order for the
second seed. Returned finite patches pass independent marking/frontier replay.

#### Turtle

For A, the second extension reached 100 tiles in 0.94–0.96 s, versus 2.18–2.47 s initially. B already reached the target in about 0.8 s before extension. Unmarked growth timed out at 6 s on both seeds. The best initial classification score did not identify the fastest marking.

| Arm | Seed 1: time / tiles | Attempts / backtracks | Seed 3: time / tiles | Attempts / backtracks |
| --- | ---: | ---: | ---: | ---: |
| Unmarked | 6.00 s (limit) / 68 | 1780 / 1726 | 6.00 s (limit) / 68 | 2089 / 2023 |
| A initial | 2.18 s / 100 | 377 / 278 | 2.47 s / 100 | 500 / 401 |
| A after round 1 | 2.37 s / 100 | 492 / 393 | 0.92 s / 100 | 145 / 46 |
| A after round 2 | 0.94 s / 100 | 140 / 41 | 0.96 s / 100 | 141 / 42 |
| A after round 3 | 1.29 s / 100 | 130 / 31 | 2.58 s / 100 | 353 / 254 |
| B initial | 0.78 s / 100 | 130 / 31 | 0.81 s / 100 | 163 / 64 |
| B after round 1 | 0.82 s / 100 | 130 / 31 | 0.82 s / 100 | 163 / 64 |
| B after round 2 | 0.82 s / 100 | 130 / 31 | 0.88 s / 100 | 163 / 64 |
| B after round 3 | 0.86 s / 100 | 130 / 31 | 0.96 s / 100 | 163 / 64 |
| C initial | 6.00 s (limit) / 85 | 1273 / 1204 | 6.00 s (limit) / 89 | 1240 / 1158 |
| C after round 1 | 6.01 s (limit) / 85 | 1266 / 1185 | 6.01 s (limit) / 89 | 1234 / 1157 |
| C after round 2 | 6.01 s (limit) / 85 | 1231 / 1151 | 6.00 s (limit) / 89 | 1219 / 1142 |

#### Hat

The Hat extensions did not improve these growth runs. The initial A marking reached 100 tiles on seed 1; its extensions hit the time limit. See both seeds and every alternative below. Stronger constraints need not produce faster growth.

| Arm | Seed 1: time / tiles | Attempts / backtracks | Seed 3: time / tiles | Attempts / backtracks |
| --- | ---: | ---: | ---: | ---: |
| Unmarked | 6.00 s (limit) / 79 | 2542 / 2483 | 6.01 s (limit) / 75 | 3119 / 3057 |
| A initial | 3.97 s / 100 | 1692 / 1593 | 6.01 s (limit) / 98 | 2285 / 2195 |
| A after round 1 | 6.01 s (limit) / 98 | 2169 / 2077 | 6.01 s (limit) / 98 | 2510 / 2423 |
| A after round 2 | 6.01 s (limit) / 95 | 1219 / 1151 | 6.00 s (limit) / 97 | 1237 / 1148 |
| B initial | 6.01 s (limit) / 88 | 2187 / 2104 | 6.01 s (limit) / 94 | 2391 / 2329 |
| B after round 1 | 6.01 s (limit) / 88 | 2505 / 2440 | 6.00 s (limit) / 90 | 2544 / 2464 |
| B after round 2 | 6.01 s (limit) / 86 | 2448 / 2366 | 6.01 s (limit) / 90 | 2654 / 2595 |
| C initial | 6.01 s (limit) / 77 | 1753 / 1689 | 6.01 s (limit) / 94 | 1722 / 1638 |
| C after round 1 | 6.01 s (limit) / 91 | 1460 / 1377 | 6.01 s (limit) / 93 | 1666 / 1577 |
| C after round 2 | 6.00 s (limit) / 97 | 1501 / 1415 | 6.01 s (limit) / 80 | 1645 / 1570 |

### Costs and interpretation

The growth tables reuse already derived markings. The complete three-alternative
campaign, including catalogue collection, fitting, enumeration, independent
corona replay, reduction, bounded failures and retries, took:

- Turtle: 315.12 seconds of elapsed process time; initial support fitting alone 0.86 seconds.
- Hat: 256.99 seconds of elapsed process time; initial support fitting alone 0.84 seconds.

Initial Turtle and Hat campaign jobs ran concurrently, so these process times
are not additive wall time and are not isolated performance benchmarks. Growth
benchmarks ran without concurrent experiment jobs. Independent final-patch
replay is timed separately in the aggregate rows. There is **no demonstrated
cold end-to-end speedup** after paying the complete learning campaign cost.

The workflow produces additional constraints, and one Turtle continuation
reduces both search attempts and reuse time. Alternative B shows why local
classification score and support expansion alone are insufficient selection
criteria. More assigned values can cost more to check or alter the chosen
search path unfavorably; the Hat and Turtle first-round results illustrate this.

[Aggregate measurements](../../data/a2-corona-workflow-2026-09-22.json) include
every stage, limit, completed catalogue count and benchmark arm.

## Verification and algorithm conformance

- A separate plain-map enumerator with lexical branching reproduces the exact
  unmarked one-corona catalogues for both tiles.
- Every initial marking accepts every original whole corona. Individual `*`
  tests confirm that removing a variable breaks an equality path, rather than
  leaving a spurious merged class.
- Every saved marked corona is independently checked for t-capacity, marking
  agreement, core completion and frontier viability.
- Complete-stage intersections are independently reconstructed from all glued
  sections, including missing values and explicit zero.
- An independent full/compact pair comparison covers every relative marking
  alignment and confirms that support reduction preserves compatibility.
- Every returned benchmark patch is independently replayed with its own marking
  and a complete frontier candidate check.

The corona enumerator is a specialized finite-core control: it checks dead
points globally but branches/propagates only obligations within the specified
core, leaving the outer frontier as a viability condition. Its results are not
reported as the unrestricted growth scheduler. The tiling benchmarks use the
actual GCTS-I `solveA2Tiling`, with global dead/forced checks and generation-first
branching. All arms use marking score zero, the same root, lattice, orientations,
limits and seeds. A marking changes candidate legality only. Alternatives are
run separately, never mixed tile by tile.

Independent replay is not an external certificate of exhaustive enumeration.
Timeouts remain unknown and their provisional common sections are never used
by the tiler. Sequential benchmark timings exclude synthesis and replay; the
recorded derivation costs include bounded failures and retries and are reported
separately. Initial Turtle and Hat enumeration jobs overlapped in time.

## Reproduction

```sh
node scripts/experiment-a2-corona-workflow.mjs --tile=turtle --ms=60000
node scripts/experiment-a2-corona-workflow.mjs --tile=hat --ms=60000
# If Turtle model 0's third stage was incomplete, retry it from its saved input:
node scripts/experiment-a2-corona-workflow.mjs --tile=turtle --retry=0:3 --ms=240000
node scripts/test-a2-corona-workflow.mjs
node scripts/benchmark-a2-corona-workflow.mjs --tile=turtle --target=100 --ms=6000
node scripts/benchmark-a2-corona-workflow.mjs --tile=hat --target=100 --ms=6000
```

Default generated output is `/tmp/a2-corona-workflow`. Assignments, support
patterns and corona patches stay outside the repository. Only the code,
aggregate measurements and report are published; the browser marking library
and ordinary GCTS-I demo are unchanged.
