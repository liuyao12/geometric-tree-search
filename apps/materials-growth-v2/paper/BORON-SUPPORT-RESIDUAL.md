# Composition control: certified zero support and residual capacity

The halo comparison motivated a direct test of whether combining existing sound
filters could resolve the remaining boron cases. This is not a learned marking
result or a new material-growth model.

The runner verifies the existing exact rational zero-support certificate against
the full candidate model, then wraps the unchanged point-search kernel with an
immutable exclusion layer, residual subset-sum propagation, parent-local failed
branch exclusions, and linear frontier scanning. The candidate pool is retained.
No training solution is supplied to search. Global dead/forced checks and
earliest-generation branching remain in force. All required points are roots.

The residual filter is rebuilt after state changes; its independently reconstructed
domains now also account for the immutable certified exclusions. This deliberately
auditable implementation is expensive and is not presented as optimized.

## Checks

- 100 synthetic models; 33,376 subsets independently enumerated.
- 362 visited states: independent graph reconstruction, scheduler checks, agreement
  with exhaustive satisfiability, and exact root rollback.
- The existing residual-only tests still pass: 50 models, 81 checked states,
  including a marking-only dependency.
- Twelve boron runs independently checked against the original input and learned
  t/m model; selected candidates respect the exact static certificates.

## Results

Each lane has a 100,000-advance / 15-second search limit. Original marking and
unmarked lanes both complete α-B, β-B105, γ-B and τ-B105. Neither completes
β-B106 or τ-B106. Unknown is not a proof of impossibility.

| Difficult input | Marked | Advances | Accepted prefix at stop | Result |
|---|---|---:|---:|---|
| β-B106 | No | 4,734 | 1,864 | Budget unknown |
| β-B106 | Yes | 3,700 | 1,886 | Budget unknown |
| τ-B106 | No | 2,463 | 2,095 | Budget unknown |
| τ-B106 | Yes | 1,774 | 1,574 | Budget unknown |

Accepted prefixes are legal but are not certified extendible. Their lengths are
not a quality metric or an improvement claim. Setup/certificate costs are outside
these search times; graph-audit overhead is included during search. No end-to-end
speedup is claimed, and single-run timings are not statistical evidence.

This closes one combination test, not the reconstruction objective. The next
research direction should examine the joint motif/decomposition model and useful
transferable connection information, rather than treating further combinations of
these same filters as evidence of a scientific advance. All six boron inputs were
used for fitting; condition-matched, independent family validation is still absent.

The runner and test are `boron-support-residual-search.mjs` and
`test-support-residual.mjs`. Final-state checks use
`verify-boron-zero-support-search.py`. The summary includes source hashes and
per-run diagnostics for replay with the recorded revisions.
