# Ordered geometric proof composition works; reconstruction remains open

The single exclusion from the previous control did not resolve ice VI search.
This experiment composes further geometric exclusions instead of repeatedly
enumerating decorations of already-explained failures.

## Protocol

Use the unchanged ice VI pool: 229 registered geometry inventories, 13,612
coupled decorated candidates and all 240 required atom points. No selected
cover or separate feasibility-solver answer is passed to search. Marked runs
use the existing developmental radius 0.6 and integer half weights.

Start with no conflict proofs. Within each round the ordinary point kernel
uses global dead/forced/earliest-generation decisions. At a reported dead point,
attempt to explain the absence of every geometric candidate using only occupied
integer capacity, consumed inventory and earlier verified exclusions. Ignore
markings when constructing the proof. If successful, greedily shrink the
selected inventory set, record explicit blockers and earlier-proof indices,
restore the old search to its root, validate the extended proof set and restart.

Rules are immutable within each run; no new exclusion is inserted behind a live
branch stack. This is an explicitly restarted proof-acquisition experiment, not
the uninterrupted baseline. Stop after 40 rounds or 120 seconds. The actual run
hits the 40-round limit in 53.257 seconds, including restart construction and
core derivation, but excluding input parsing and final independent verification.

## Verification

The independent Python checker imports none of the producer code. For each
proof it checks the integer totals, target deficit, complete incident-inventory
list and every blocking reason. A reference to another proof must point strictly
backward to an already-verified exclusion. This establishes an acyclic proof
chain, not a learned extrapolation from a timed-out search.

| Quantity | Verified result |
| --- | ---: |
| Exclusions | 40 |
| Exclusions using earlier proofs | 30 |
| Explicit blocking arguments | 219 |
| Maximum dependency depth | 8 |
| Inventory-set sizes | 5–24 |

Small-model exhaustive tests construct 386 proofs, including 55 composed proofs,
and check 823 proof/complete-solution pairs without excluding a complete filling.
Attempting to validate a composed proof without its ancestors is rejected. The
standalone checker also rejects four corrupted material artifacts: missing
blocker, missing owner, cyclic dependency and mismatched model hash.

These are exact integer proofs relative to the fixed inventory/support model.
The atom registration and Gaussian comparisons remain approximate; the proof
does not certify continuous-pose enumeration or transfer to another pool.

## Search status

The rounds perform 2,582 advances in total. Some rounds select 77 placements;
none completes the required 80-placement filling. The final selected state has
74 placements, 216 fully filled atoms, 12 half-filled and 12 untouched atoms,
in four support components. Independent replay verifies the position residuals
(maximum 0.1489893 Å), integer t totals and field pairs (maximum distance
1.17052, below 1.2). Root rollback checks pass in all rounds.

**The final state is a harvested dead end, not an extendable growth patch.** It
was observed under the first 39 exclusions and supplies the 40th proof. The final
40-proof library has not yet been used for another round in this artifact. The
larger filled-atom count must not be presented as successful reconstruction or
a monotone growth milestone. Status remains budget-unknown, and no speedup is
claimed against the 30-second uninterrupted controls.

## Meaning and remaining work

The implemented advance is checkable composition and reuse of geometry-only
failure arguments across decoration choices. It is not learned GCTS marking
selectivity, a physical discovery or complete material reconstruction. Further
rounds can use the checked proof library, but any claim of reconstruction still
requires a complete independently replayed filling. Shared learned anchors/t,
useful family-level connection markings, common-condition provenance, complete
continuous registration and growth beyond input coordinates remain unresolved.

Versioned sources and evidence are in `ice-composed-cores/`: the loop and core
producer, JavaScript validator, independent Python proof checker, negative
controls, `results.json`, `proof-check.json` and `state-check.json`. The generated
large input model is unchanged and not bundled; its hash is recorded.
