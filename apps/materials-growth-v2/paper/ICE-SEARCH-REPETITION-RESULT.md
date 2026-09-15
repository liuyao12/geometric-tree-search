# Decoration variants repeatedly revisit a geometric dead end

## Diagnosis

Instrument the first 500 advances of each existing ice VI registered-pool
search, with no ordering or pruning change. Both lanes visit 45 distinct sets
of selected geometry inventories and repeat such a set on 455 decisions.
There are 452 dead-end visits, all associated with one selected geometry set.
At the reported dead point, no unused inventory fits the remaining integer
capacity even when every marking is ignored. Four saved representative
witnesses (two per lane) are independently checked against the complete input
candidate list. Aggregate visit counts come from instrumentation; the checker
does not independently replay the full search trace.

Repeated selected geometry does not in general imply equivalent marked search
states: fields, generations and stack exclusions may differ. Here the verified
dead-point obstruction itself is independent of the decorations. This is a
specific opportunity for sound geometric proof reuse, not permission to merge
arbitrary marked states or globally forbid a motif.

## One-step capacity look-ahead control

Test a separate proved-redundant filter. For a candidate c, hypothetically add
its positive t-support and consume its inventory. If any required point remains
unfilled and no unused geometry inventory fits there, reject c. Ignore markings
in this check, giving a superset of feasible future candidates. Subsequent
positive placements cannot restore capacity or inventory, so such c cannot
belong to a complete filling of the declared static finite pool.

All decorations of one geometry inventory share this verdict because their
t-support is checked identical. Cache verdicts only within the current state;
clear the cache on every refresh and rollback. Remove candidates through the
same graph; do not alter global dead/forced/earliest-generation scheduling.
This filter is additional capacity reasoning, not a learned GCTS marking.

Exhaustive subset checks over 80 small generated models inspect 476 reachable
states, preserve 139 complete fillings, and verify that 504 rejected extensions
have no full continuation. Shared-inventory decoration variants and root
rollback are tested. These tests support the finite-capacity argument, not
general continuous-space completeness or a full adapter-conformance claim.

## Material outcome: no improvement in completion

| Lane with look-ahead | Seconds | Attempts | Backtracks | Selected placements | Fully filled atoms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Unmarked | 30.030 | 1,472 | 1,430 | 42 | 111 / 240 |
| Marked | 30.006 | 1,279 | 1,236 | 43 | 111 / 240 |

Both remain budget-unknown. Independent replay verifies all selected geometry,
t-values and fields, and root rollback passes. The unmarked final state has 30
half-filled and 99 untouched atoms; the marked state has 36 and 93. These are
final search states, not best progress or monotone growth. Displayed timings
exclude setup, export and independent replay. Single-run counts do not establish
a statistically supported performance comparison.

The filter removes immediate capacity failures but does not resolve the search
bottleneck. Do not promote it as an acceleration result or replace the default
app with it. The next step should reuse independently certified geometric
failure contexts across decoration alternatives, while preserving marking
distinctions, exact rollback and the reference scheduler. Any such reuse needs
context-scoped proofs and tests; the present diagnosis is not that implementation.

The prior 97 supplied-cover witnesses and four fixed-cover marking searches
remain distinct controls. Learned anchors/t-values, useful connection learning,
family-wide reconstruction, complete continuous registration, growth beyond the
input and verified common-condition provenance remain open.

Versioned sources and evidence are published under `ice-search-repetition/`:
`profile.json`, `profile-check.json`, `lookahead-results.json`,
`lookahead-check.json`, and their producer/checker modules. The large model is
unchanged and not redistributed; its hash is recorded in the result files.
