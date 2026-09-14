# Boron search diagnostics: capacity propagation and failed-choice exclusions

14 September 2026. Engineering controls on the fixed, jointly learned model.
No new chemistry, learned markings or atomic coordinates are introduced.

## Two separately labelled controls

1. **Exact residual capacity filter.** At each required point, a candidate can
   survive only if its contribution plus some subset of the other currently
   available contributions equals the remaining capacity. A bitset subset-sum
   calculation removes unsupported candidates globally from the point/candidate
   graph and repeats to a fixed point. It preserves every completion of the
   complete finite point model: any actual completion supplies such a subset.
   Ignoring other overlap conflicts only relaxes this necessary condition.
2. **Parent-local failed-choice exclusions.** The existing reference harness
   retries alternatives after rollback but does not retain failed choices as
   exclusions in that parent state. This permits revisiting failed combinations
   in a different order. The new control trails a failed candidate's exclusion
   in its proved parent context, then returns to global dead/forced/generation-
   first decisions. Undoing that context removes the exclusion. This is not a
   global ban or a learned material-specific rule.

The controls are separate wrappers around the unchanged published point kernel.
They are not silently substituted into earlier reference benchmark results or
the production growth application. Their reasons remove candidates through the
same frontier graph; neither supplies a known training solution or changes the
generation-first branch rule. The combined control uses both mechanisms.

## Results

Each control was run marked and unmarked on all six original full candidate
pools with the same learned t/m-values. Budgets were 100,000 advances or 15
seconds per run. Some runs overlapped in wall-clock execution; this is not an
isolated timing study and does not support quantitative speedup claims.

| Search control | α, β-105, γ, τ-105 | β-106 and τ-106 |
| --- | --- | --- |
| Previously reported reference | Complete and connected, both lanes | Budget unknown, both lanes |
| Residual capacity | Complete and connected, both lanes | Budget unknown, both lanes |
| Parent-local exclusions | Complete and connected, both lanes | Budget unknown, both lanes |
| Both controls | Complete and connected, both lanes | Budget unknown, both lanes |

Residual capacity removes γ's one branch: all 324 placements are then forced.
Nevertheless it costs more work here. This first implementation rebuilds all
candidate legality after each state change, rather than maintaining an optimized
incremental proof dependency graph. Repeated-removal counters include rederived
cuts; they are not counts of distinct eliminated placements. Parent exclusions
avoid one source of repeated search but do not resolve the hard cases at this
budget. Partial fill counts and backtrack counts at unequal wall-clock endpoints
must not be presented as reconstruction success or a GCTS speedup.

These results keep the six-model connected training witness intact. The search
failure is computational, not evidence that those finite target models lack
solutions. Better local connection information remains a separate learning task.

## Verification

- A separate set-based subset-sum implementation checks the filtered point
  domains, distinct from the bitset implementation.
- Fifty small random models enumerate all candidate subsets to obtain their
  exact solution sets. Across 81 visited states, capacity pruning preserves
  every completion compatible with the selected prefix. Root rollback and a
  distant mark-only dependency control pass.
- Another 150 random models test parent exclusions with and without capacity
  filtering. Across 1,145 visited states and 176 failed-choice exclusions,
  exhaustive solution lists confirm no valid completion is removed in its
  parent context. Root state, including exclusions, is restored.
- On material runs the harness checks global decision priority, independently
  rebuilds incidence/reverse indexes every 100 advances and at terminal states,
  and checks root semantic rollback. For filtered runs it compares against the
  separate set-based fixed-point calculation.
- The independent final-state verifier reconstructs all candidate t/m-values
  from the frozen learning artifact, then checks totals, marking agreement and
  connectivity of every complete result. All 36 new material runs pass their
  final-state checks; passing a partial-state legality check is not completion.

## Scope and gaps

The residual wrapper explicitly requires a complete fixed finite pool, capacity
at most 24, and every positive-support point in the required target. It rejects
dynamic expansion and custom constraint callbacks. Mark-only points remain
supported. Source registrations remain approximate, while point capacities are
exact integers. Material tests have all roots at generation zero; synthetic
generation-priority controls are still needed to cover that scheduling rule.

These checks do not establish all-stack serialization/restart, arbitrary dynamic
marking changes, continuous candidate completeness, held-out transfer or blind
material growth. Tiny exhaustive tests are bounded evidence, not a proof that
the entire implementation is free of bugs. The mathematical necessity arguments
apply to the declared fixed models, not an incomplete sampled pose universe.

## Follow-up: scheduler overhead and repeated placement sets

A representation-only scheduler now scans the frontier once rather than
constructing candidate-ID arrays at every point and sorting the whole frontier.
It preserves the original comparator, first encountered dead/unknown point,
global forced-move priority, generation ordering and candidate preference.
The production kernel remains unchanged. This is not new pruning or a learned
GCTS marking. Pure deterministic preference callbacks are assumed.

Lockstep tests on 160 small models cover 4,207 decisions, 1,007 advances,
mark-only dependencies, root rollback and synthetic mixed generations and
incomplete domains. Four hard material lanes each match the original engine
for 5,000 advances, including returned actions, counters and checked semantic
states. State equality is checked every 100 advances and at the end; decision
and action equality are checked at every advance.

At branch visits in these prefixes, the same sorted placement set recurs:

| Model | Branch visits per lane | Repeated placement sets per lane |
| --- | ---: | ---: |
| β-106 | 1,329 | 1,034 |
| τ-106 | 1,084 | 859 |

Counts hold separately for marked and unmarked lanes. These are not identical
full search states: stacks can retain different remaining alternatives. A
hash of a placement set is not a sufficient justification for rejecting a
branch, and no transposition pruning was introduced in this experiment.

The linear scheduler was run on all six materials, marked and unmarked, with
the original 100,000-advance / 15-second budgets. A second 12-run control adds
parent exclusions and orders candidates by descending sum of their t-values
only after selecting the usual earliest-generation point. That heuristic
contains no selected training-answer IDs, chemistry or new candidate gate.
It is hand-chosen, not learned GCTS. Both controls still complete α, β-105, γ
and τ-105 with connected covers; β-106 and τ-106 remain budget-unknown.

All 24 final states pass independent candidate reconstruction, exact filling,
marking consistency and connectivity checks. Partial-state legality is not
success. The linear version visits more states before some time cutoffs, but
this is not a controlled speedup study; executions partly overlap and have
audit overhead. More throughput and this simple candidate preference do not
resolve the difficult inputs. Certified local conflict reuse is a next test,
not an implemented result or a substitute for learning informative markings.

Additional reproduction commands (new output paths):

```
node test-linear-frontier-decision.mjs KERNEL
node boron-decision-lockstep.mjs KERNEL ORIGINAL_SEARCH_FOLDER LOCKSTEP_JSON
node boron-face-reference-search.mjs PRECHECK LEARNING KERNEL LINEAR_FOLDER linear
node boron-face-reference-search.mjs PRECHECK LEARNING KERNEL MASS_FOLDER linear-exclusions 100000 15 filling-mass
python verify-boron-face-search.py PRECHECK LEARNING LINEAR_FOLDER LINEAR_CHECK
python verify-boron-face-search.py PRECHECK LEARNING MASS_FOLDER MASS_CHECK
```

The source artifact used here is `precheck-v2.json`, verified by the input
hash recorded in `periodic-connected-c12-v1.json`. Do not substitute the
older `precheck.json` merely because it has the shorter filename.

## Earlier control reproduction

```
node test-residual-capacity-filter.mjs /absolute/path/kernel.mjs
node test-branch-local-exclusions.mjs /absolute/path/kernel.mjs
node boron-face-reference-search.mjs precheck.json connected.json /absolute/path/kernel.mjs residual-results residual
node boron-face-reference-search.mjs precheck.json connected.json /absolute/path/kernel.mjs exclusion-results branch-exclusions
node boron-face-reference-search.mjs precheck.json connected.json /absolute/path/kernel.mjs combined-results residual-exclusions
python verify-boron-face-search.py precheck.json connected.json residual-results residual-verification.json
python verify-boron-face-search.py precheck.json connected.json exclusion-results exclusion-verification.json
python verify-boron-face-search.py precheck.json connected.json combined-results combined-verification.json
```

Use new output directories and the previous six-model training artifacts. Keep
the wrapper modules next to the harness. Published summaries contain all runs;
local per-run models retain the final selected placement lists for replay.
