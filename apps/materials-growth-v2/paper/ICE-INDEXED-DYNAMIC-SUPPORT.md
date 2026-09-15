# Indexed dynamic complementary support

The original dynamic filter repeatedly compared each endpoint with all possible
partners and failed to complete material root setup within one minute. The new
index enumerates a conservative signature neighborhood at each anchor, retaining
distinct endpoint identities and excluding only same-inventory partners. Every
indexed pair still goes through the unchanged runtime cloud predicate.

Independent brute-array replay checks every adjacency list against all relevant
signature records, without using the compiler's KD tree. It checks missing as
well as extra edges and verifies complete endpoint enumeration. The runner binds
the index and verifier report to the input model through SHA-256 hashes.

| Library/frame | Endpoint records | Directed links | Index construction seconds |
| --- | ---: | ---: | ---: |
| One/train | 41,967 | 522,470 | 2.51 |
| One/dev | 43,398 | 618,756 | 1.09 |
| Multi/train | 78,770 | 1,679,070 | 4.78 |
| Multi/dev | 81,131 | 2,046,818 | 2.53 |

These are conservative links, not certified agreements. Completeness follows
from the sorted-coordinate necessary bound, with numerical padding and bounded
input vectors. Raw and indexed variants each pass explicit-domain tests on
5,427 states / 108,540 memberships and 1,170 rollbacks, preserving 409 complete
solutions across 312,500 tiny selections. Base cloud lockstep tests still pass.

## First verified complete finite filling

The one-cover training frame c01500 (ice VIII, 192 required atoms) reaches full
occupancy using 64 placements. Independent replay verifies 128 cloud assignments
at 64 common values. Setup takes 1.06 seconds; search takes 4.76 seconds and 182
advances (181 placements attempted, 67 branches, 117 backtracks). This excludes
static filtering (6.64 seconds), index construction, input/output and independent
verification. Jobs overlapped, so this is not a controlled speedup study.

The selected support cover differs from the stored training cover and has THREE
connected components in the motif-overlap graph. This is a complete finite
point-value filling on supplied positions, not connected growth, a new physical
configuration, held-out transfer or an infinite-extension certificate. No global
connectivity rule was silently added to the base algorithm.

The one-cover developmental frame remains budget-unknown at 30 seconds, with 56
placements and three overlap components. Other indexed runs are reported in the
linked summaries; no result should be inferred from index counts alone.

Artifacts: `/tmp/gcts-ice-{one,multi}-complement-index-v1.json`,
`...-complement-index-check-v1.json`, `...-indexed-dynamic-search-v1/`, and
`...-indexed-dynamic-check-v1.json`. The index and coordinate-derived cloud pool
remain local; public reports expose hashes, counts, code and verification scope.

Next scientific gates remain connected reconstruction under explicitly declared
semantics, developmental transfer, verified same-condition provenance, and
growth beyond supplied positions. The underlying dynamic propagation still
globally rebuilds domains rather than maintaining incremental support watchers.
