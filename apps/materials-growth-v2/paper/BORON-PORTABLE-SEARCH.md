# Portable markings enter the finite reconstruction search

The experimental search now consumes the intrinsic displacement-cloud marking
values, rather than scalar IDs for target-local junction states. Candidate
rejection and backtracking use those values. This is an integration result,
not a new reconstruction or speedup result, and not yet unrestricted growth.

## Scope of the registered model

The exported motif is rotated into each recorded registration. Its endpoint
clouds rotate with it. Target point IDs identify the finite t-support, but no
target-state index is stored as a marking value. Existing target-state tables
still propose the registrations. Their replacement by a complete geometric
candidate generator is unfinished; the present pool is complete only as an
explicitly enumerated finite registered model, not over continuous rotations.

Cloud decorations currently apply to pairs joining two pair-only junctions.
Other base placements keep their original scalar markings without additional
cloud decoration. This changes the model relative to earlier full junction-state
encodings. In particular, the earlier τ reconstruction is not a speed baseline
for this experiment.

| Input | Registered variants | Distinct represented base placements |
|---|---:|---:|
| α-B | 108 | 108 |
| β-B105 | 1,458 | 1,458 |
| β-B106 | 47,916 | 4,725 |
| γ-B | 486 | 486 |
| τ-B105 | 2,916 | 2,916 |
| τ-B106 | 20,529 | 7,452 |

The learned registration pool omits 54 original β-B106 base placements and 432
τ-B106 placements. Those omissions are learned restrictions, not proofs that
these placements are impossible in the original model. Both comparison lanes
use the same registered pool and the same shared-placement inventory.

## A conservative marking filter, not an unchecked equality shortcut

At an overlapping marking anchor, each assignment specifies a set of possible
colored displacement clouds with radius 0.06 Å. If two assignments share a
value, a color-preserving bijection between their centers must exist within
twice that radius. Absence of such a bijection rejects the candidate. The
implementation includes both assignments' numerical membership guards in that
triangle bound; a dedicated boundary regression test checks this case.

Pairwise compatibility alone does not prove that all assignments share a value.
The graph therefore uses a conservative relaxation of the common-value
constraint. A terminal result is certified only after finding and checking a
single common cloud at every marked anchor. Failure of the incomplete witness
proposer returns unknown, not an exhausted search or a reason to prune. Partial
states without a common-value witness are not certified legal marked patches.

The reference kernel still determines global dead ends, degree-one moves and
earliest-generation branching. Its graph is the source of candidate domains.
The plug-in rebuilds inventory and marking dependencies after each change and
rollback, including mark-only anchors. This initial full rebuild is intentionally
simple and expensive; it is not an optimized incremental implementation.

Several variants may represent one geometric base placement. They share an
inventory identity and cannot be selected together, even if their t-values leave
enough capacity. This exclusion is essential: replacing mutually conflicting
scalar IDs by tolerant cloud values must not allow duplicate placement stacking.

## Tests and interpretation

The integration passes 150 small models compared with 38,400 independently
enumerated subsets, with 730 visited-state audits. Tests cover full forward and
reverse graph agreement, global priority, earliest generation, exact rollback,
extended marking dependencies and shared-placement inventory. Separate controls
ensure that a feasible but undiscovered common value stays unknown rather than
being pruned, including a near-boundary numerical-guard case.

All six material inputs are run with cloud filtering enabled and disabled,
using a 30-second / 1,000,000-advance checkpoint limit per lane. Auditing and final
verification can cross that checkpoint, and their measured cost is retained.
Setup is reported separately. This is a short diagnostic run, not a statistically
controlled performance study. Compilation, prior learning and validation are
outside the reported search times. The scalar-only control also retains redundant
marked variants, so it is not a competitive optimized unmarked baseline.

The four easier inputs reconstruct in both lanes. Their extra cloud layer is
vacuous, because they have no relevant junction-to-junction edges. Both B106
inputs remain unresolved in the short runs. There is no additional reconstruction
or demonstrated speedup. Final partial cloud witnesses, where found, establish
only present marking consistency, not future extendibility.

An independent Python checker rebuilds integer t totals, checks scalar markings
and shared inventory, verifies rotated cloud data and anchor registration, and
checks common-value witnesses using the separate Python membership routine.
All 18 supplied training lifts remain valid. The report includes the final
twelve-run summary and independent checks; raw coordinate-derived model pools
remain local.

## Next missing pieces

The portable representation now participates in a reference-ordered search,
but target-table-free pose generation and transferable decoration applicability
remain necessary. The marking relaxation also needs a more capable common-value
solver, with certified contradictions rather than heuristic failure. Efficient
dependency updates are needed before performance comparisons. Independent
condition-matched family evaluation, including ice, and expansion beyond the
supplied coordinates remain open.

## Reproduction

```
node test-portable-cloud-filter.mjs KERNEL
node compile-portable-search.mjs COMPILED JUNCTIONS JOINED PORTABLE ALTERNATIVES MODEL
node boron-portable-search.mjs MODEL KERNEL SEARCH_FOLDER
python verify-portable-search.py INPUT COMPILED JUNCTIONS JOINED PORTABLE ALTERNATIVES MODEL SEARCH_FOLDER KERNEL CHECK
```

The verifier checks all twelve saved runs against their summary. Python requires
NumPy and the previously published portable cloud module. Model and search output
paths must be new. Prior data provenance and construction requirements still
apply; source/check downloads are not a self-contained raw-data bundle.
