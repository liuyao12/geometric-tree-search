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

## Reproduce

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
