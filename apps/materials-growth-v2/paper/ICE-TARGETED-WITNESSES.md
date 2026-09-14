# Targeted training tilings resolve the validation weight ambiguity

14 September 2026. Same frozen 350-type dictionary, 100 training configurations
and 100 developmental validation configurations. No new atomic data were added.

## Acquisition rule

Starting from the two-witness weight audit, select a template role whose weight
is not forced. In deterministic training order, find an occurrence of its type
and require that occurrence in a new connected degree-two cover. Every successful
cover contributes additional shared-site equations. Targets depend only on training
equations and candidate occurrences, not validation geometry or outcomes.

The acquisition stopped after exhausting available targets: 47 attempts produced
38 new training witnesses and nine solver-infeasible forced-occurrence cases.
An independent checker verifies positive filling, connectedness and inclusion of
each requested occurrence in every successful witness. These are specialized
selection controls, not reference-search outputs.

## Exact inference and transfer

| Quantity | Before targeting | After targeting |
| --- | --- | --- |
| Forced-half site variables | 1,806 | 2,082 |
| Free complementary sites | 12 | 0 |
| Sites unused in selected training tilings | 282 | 18 |
| Independent free weight parameters | 288 | 18 |
| Original validation covers independent of free weight choices | 86 / 100 | 100 / 100 |

The combined system has 65,376 training equations and 16,969 distinct complement
edges. The exact graph/rational verifier certifies the resulting weight family;
a separate integer-perturbation implementation confirms that all original
validation covers now fill for every remaining training-consistent weight choice.
The remaining 18 variables belong to three unused template types (57, 69, 81).
They are not assigned invented weights or silently deleted.

This removes the previously observed validation dependence on arbitrary weights
within this conditional model. It is **not a new 100/100 tree-search result**:
the supplied validation covers are unchanged, the occurrence-selection model is
still degree two, and the previously reported reference-search limitations remain.
It does not establish unrestricted discovery of half weights or blind growth.

## Why nine forced-occurrence attempts failed

For each failure, solve the fractional relaxation of the fixed degree-two graph
and maximize the target edge variable. All nine have an exact upper bound of zero.
Stored rational dual coefficients satisfy the dual equations and sign conditions.
An independent verifier, importing no optimizer, reconstructs the graph and checks
each bound exactly. Thus none of these failures is merely a timeout.

The certificates concern **those placements in those finite degree-two graphs**.
They do not prove a motif geometrically impossible, a material unrealizable, or
the unrestricted inverse-tiling problem infeasible. Some initially rejected types
are admitted through other training occurrences; this is contextual information,
not permission to ban an entire motif type.

## Marking implication and limits

The combined incidence graph has just two equality components, of sizes 1,388
and 694. Consequently scalar equalities on these same atomic domains again leave
only two assigned classes, with 18 sites missing. The extra small classes seen
with sparse witness sampling do not persist as training constraints accumulate.
This is not evidence of useful GCTS pruning. No new marking-search benchmark is
claimed by the weight audit.

The next substantive problem is to learn context-sensitive matching information
without imposing a chemistry rule, treating every missing connection as negative,
or memorizing a particular selected tiling. The current audit improves training
coverage; it does not solve that problem. Same-condition provenance and independent
trajectory evaluation are also still incomplete.

## Reproduce

```
python ice-targeted-witnesses.py DICTIONARY COVER PRIOR_WEIGHT_MODEL TARGET_FOLDER
python verify-ice-targeted-witnesses.py DICTIONARY TARGET_FOLDER WITNESS_CHECK
python ice-weight-identifiability.py DICTIONARY WEIGHT_MODEL FIRST_SELECTION SECOND_SELECTION TARGET_FOLDER/witness-*.json
python verify-ice-weight-identifiability.py DICTIONARY WEIGHT_MODEL WEIGHT_CHECK FIRST_SELECTION SECOND_SELECTION TARGET_FOLDER/witness-*.json
python ice-weight-transfer.py DICTIONARY WEIGHT_MODEL FIRST_SELECTION PROVENANCE TRANSFER
python verify-ice-weight-transfer.py DICTIONARY WEIGHT_MODEL FIRST_SELECTION TRANSFER TRANSFER_CHECK
python ice-required-edge-certificates.py DICTIONARY COVER TARGET_FOLDER/summary.json EDGE_CERTIFICATES
python verify-ice-edge-certificates.py DICTIONARY COVER EDGE_CERTIFICATES EDGE_CHECK
python test-ice-thermal-selection.py
```

Input artifacts are defined by the earlier thermal-ice reports. Additional
witness files contain only the training configuration they cover. Tests include
30 exhaustive unmarked, 30 conflict-constrained and 30 required-occurrence small
graphs, plus one odd-degree bridge control. Geometry and the reference kernel
were not changed in this experiment.
