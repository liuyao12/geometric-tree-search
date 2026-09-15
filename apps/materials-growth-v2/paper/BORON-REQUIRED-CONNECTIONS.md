# Required connections: a matched-budget reconstruction test

The latest τ-B106 reconstruction completes in 57.62 seconds with zero backtracks.
The original marked baseline remains unresolved at the same 100-second limit.
The new witness has 5,400 base placements, fills all 5,724 supplied atom positions,
has one connected positive-support component, and lifts to explicit scalar junction
markings. This is a positive operational result on an in-sample finite task, not
a universal or end-to-end speedup claim.

## What changed

Junction propagation already identifies connections that occur in every remaining
local marking choice. Those connections are therefore required within the current
learned model and branch context. Previously, the search could choose an optional
connection first. The new policy prefers required connections when breaking ties
within the earliest frontier generation.

Global dead ends and degree-one forced moves still precede every branch. Later
generations never outrank earlier ones. No base candidate is removed by the
ordering policy, and required choices remain ordinary branch choices in the
counters—not relabeled degree-one forced moves. The learned marking restriction
and the additional propagation are unchanged from the junction model.

The policy passes 150 small models checked against 16,448 exhaustive subsets,
including global priority and generation controls, independent graph reconstruction,
and restoration of the required-connection cache after rollback.

## Matched search limits

Each run is limited to 100 seconds or 1,000,000 advances, whichever comes first.
The runs are sequential on the same local machine, using the same fixed base
candidate pools, original t/m values and root obligations. The junction lane adds
the previously learned junction restriction, its propagation and the declared
generation-tie policy. The baseline does not use those learned junction constraints.
This comparison does not isolate the contributions of propagation and ordering.
The online graph-audit overhead is included in the search times.

| Input | Lane | Search seconds | Advances | Result |
|---|---|---:|---:|---|
| β-B106 | Original marked baseline | 100.02 | 536,500 | Budget unknown |
| β-B106 | Junction + required preference | 100.06 | 14,932 | Budget unknown |
| τ-B106 | Original marked baseline | 100.05 | 337,400 | Budget unknown |
| τ-B106 | Junction + required preference | 57.62 | 5,401 | Exact connected finite filling |

The τ run accepts 5,400 placements: 2,555 degree-one forced placements and 2,845
branch choices. Of those branch choices, 2,473 receive the required-connection
preference. There are zero backtracks. These counts do not imply that every one
of the remaining choices was independently optional.

An extended β-B106 run with the new preference also remains unknown at 300 seconds
(47,637 advances). Its final 2,897-placement prefix is legal but not certified
extendible. Prefix length is not a reconstruction success metric.

A further proof-based rollback control skips a required-choice parent only after
restoring it and independently checking that forbidding the chosen connection
causes a contradiction. Exhaustion of its required child then exhausts that parent;
alternative placement orders need not be revisited. This rule is scoped to the
fixed learned junction model, not to the original unrestricted problem. It passes
the small exhaustive tests and a specific adversarial rollback case. On β-B106 it
makes 1,404 independently checked parent prunes but remains unknown at 100 seconds
(11,420 advances). This negative control does not change the reconstruction count.

## Not a replay of a training decomposition

The τ witness differs from all three supplied training records for that input:

| Training record | Training placements | Symmetric difference from search witness |
|---|---:|---:|
| Original | 5,427 | 967 |
| Alternative 101 | 5,417 | 819 |
| Alternative 202 | 5,412 | 830 |

This is a new placement-set combination of learned local patterns on unchanged
coordinates, **not a new atomic structure or a new material prediction**. A separate
novelty script records the source hashes and these set comparisons. Independent
checks verify the full original t/m model, all 2,052 junction choices and connectivity;
the explicit compiler then checks its scalar marking lift with the native verifier.

## Interpretation and remaining work

The baseline and junction lane seek a valid filling of the same supplied atomic
configuration, but the junction lane searches a learned subset of the original
model's fillings. The comparison is not evidence that the marking restriction
preserves every possible solution. Learning, compilation and setup costs are
outside the search timings; this is one local run, not a statistical benchmark.
No speedup ratio or independently generalized materials claim is made.

Five of six available boron structures have verified finite reconstructions across
the recorded experiments, with differing budgets. β-B106 remains unresolved.
Whole-pipeline independent family validation, verified identical-condition cohorts,
and growth beyond supplied coordinates remain open. The next learning gap is
joint information about neighboring junctions, not just their separate local states.

Files: `junction-mandatory-order.mjs`, `test-junction-mandatory-order.mjs`,
`boron-junction-mandatory-search.mjs`, `boron-junction-required-extended.mjs`,
`junction-decomposition-novelty.py`, plus the existing junction verifiers and
explicit marking compiler. Summary and check artifacts accompany the report.
The additional control uses `junction-required-backjump.mjs`,
`test-junction-required-backjump.mjs`, and `boron-junction-proof-search.mjs`.
