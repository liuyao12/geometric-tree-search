# A geometric failure proof can be reused across decoration variants

The repeated ice VI failure admits a smaller explanation. Greedy deletion
reduces the 44 selected geometry inventories to nine:

`edge:123`, `edge:154`, `edge:155`, `edge:169`, `edge:171`, `edge:205`,
`edge:40`, `edge:42`, `edge:63`.

Their coexistence leaves required atom `a:118` underfilled while exhausting or
blocking all five geometric inventories that could contribute there:

| Candidate inventory | Why it cannot fill atom 118 |
| --- | --- |
| edge:38 | Would exceed capacity at atom 141 |
| edge:153 | Would exceed capacity at atom 152 |
| edge:172 | Would exceed capacity at atom 45 |
| edge:204 | Would exceed capacity at atom 206 |
| edge:205 | Its single inventory item has already been used |

The listed blocking atoms already have integer total 2, and each blocked
placement would add 1. No field value enters this proof. Positive additions
cannot restore consumed inventory or decrease occupied capacity, so no complete
filling can contain all nine inventories, regardless of their decorations.
The core is inclusion-minimal for this dead-point predicate and deletion order,
not proven minimum-cardinality or minimal for all possible contradictions.

## Implementation and scope

A Python extractor produces the core and explicit blockers. A separate
JavaScript validator reconstructs every geometry support, recomputes integer
totals and checks every candidate incident to the underfilled point before
constructing search. The model hash must match. Invalid or missing-inventory
certificates are rejected. A small exhaustive decorated fixture preserves all
three complete fillings, rejects the two conflicting decorated subsets and
tests nonlocal graph refresh and rollback.

The resulting exclusion is a proved redundant constraint for this fixed pool,
not a learned material marking. It applies through the ordinary candidate graph:
reject a candidate if its inventory would complete the forbidden set. The rule
is static for the whole run; no rules are inserted behind captured branch
lists, and cached branch decisions are not silently reused across rule versions.
The global dead/forced/earliest-generation scheduler is unchanged. It is not a
claim that arbitrary states sharing geometry may be merged.

## Search result: the single core does not resolve reconstruction

| Lane | Search seconds | Attempts | Backtracks | Selected placements | Fully filled atoms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Unmarked + static core | 30.001 | 1,807 | 1,764 | 43 | 117 / 240 |
| Gaussian-marked + static core | 30.002 | 1,607 | 1,564 | 43 | 117 / 240 |

Both runs remain budget-unknown. Independent geometric/field replay confirms
legal partial states with 24 half-filled and 99 untouched atoms, in five support
components. Maximum position error is 0.1489893 Å; maximum observed field pair
distance is 1.13814, below 1.2. Root semantic-state rollback passes in both lanes.

These are single-run, search-only timings. Trace acquisition, core extraction,
export and independent audit are excluded; setup now includes factory and core
validation and is reported separately. No cold-start speedup, successful
reconstruction or learned-GCTS benefit is established.

## Next requirement

One certified obstruction prevents its own incompatible combination but does
not explain other failures. Further work should derive additional, possibly
composed proofs, with an explicit dependency chain and independent replay.
Do not erase marking distinctions or transfer exclusions to another pool on
the basis of this single example. The larger objective remains unmet: shared
learned motifs and markings must reconstruct material families, with learned
anchors/t-values, reliable common-condition provenance and growth beyond known
positions. The current experiment addresses only finite-pool proof reuse.

Versioned evidence and sources are in `ice-static-cores/`: `cores.json`,
`results.json`, `check.json`, the extractor, static core adapter and tests.
Previous results and source versions remain unchanged.
