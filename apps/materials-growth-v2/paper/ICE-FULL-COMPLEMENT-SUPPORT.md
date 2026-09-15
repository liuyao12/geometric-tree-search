# Full-correspondence complementary support

The signature filter now has an optional `--full-cloud` mode. For a possible
complement, construct the color-preserving pairwise-distance bipartite graph
and require a perfect matching. The producer uses a linear-assignment solver;
independent replay uses an augmenting-path matcher. Both use a conservative
2r + 1e-8 distance allowance (plus the membership guard), so this necessary
test is looser than the runtime cloud rule. It cannot replace terminal common
marking-value verification or establish global extendibility.

The signature-only default is retained. The fixed-point removal argument,
half-weight capacity assumptions, anchor/required-atom incidence checks and
inventory requirements are unchanged. A proof records which mode produced it.
Every retained endpoint keeps its original cloud, rather than a fitted proxy.

| Library/frame | Original choices | Signature survivors | Full-correspondence survivors | Filter seconds |
| --- | ---: | ---: | ---: | ---: |
| One/train | 21,289,071 | 4,753,326 | 1,934,561 | 6.64 |
| One/dev | 12,640,506 | 4,934,012 | 2,245,516 | 6.11 |
| Multi/train | 41,672,906 | 15,417,706 | 6,737,717 | 14.82 |
| Multi/dev | 32,941,016 | 16,177,545 | 7,809,448 | 14.70 |

All stored training lifts survive. The filter removes 321,568 endpoint records
in total. Independent material proof replay is stored separately, not inferred
from successful compilation. Exhaustive controls preserve 58 full solutions
across 62,500 tiny selections. A two-point-cloud regression rejects identical
coordinate signatures with no correspondence and preserves a permuted copy.

Preprocessing times exclude file I/O and independent verification. Concurrent
jobs preclude a controlled speed comparison. This is stronger necessary pruning
within a fixed learned model, not a new transferable marking or a family-wide
material reconstruction claim. No new physics or chemistry is assumed.

Artifacts: `/tmp/gcts-ice-{one,multi}-factorized-full-support-v1.json`,
`...-factorized-full-proof-v1.json`, `...-factorized-full-check-v2.json`, and
`...-factorized-full-search-v1/`. Next integration target is branch-dependent
complement loss with reversible graph updates, not further static counting.

All four searches ended budget-unknown after 30 seconds. Final selected counts
were 43/55 for one-cover training/dev and 43/46 for multi-cover. Root rollback
passed. Independent selected-state replay checks 86/110 and 86/92 assigned
clouds at 44/56 and 44/47 common-value points. One-cover training recorded one
forced placement; the other pilots recorded none. No complete reconstruction
or end-to-end speedup has been demonstrated.
