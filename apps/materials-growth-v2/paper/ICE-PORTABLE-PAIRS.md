# Ice: coupled endpoint markings now have a checked geometric representation

This follow-up exports actual rotation-covariant point markings and tests them
through the reference-order finite search. It does **not** establish successful
ice growth, transferable connection rules, or a computational advantage.

## Representation

The 269 pair-motif types used in the selected training covers retain their six
atomic anchors and inherited t=1/2 at each anchor. The new library has 9,200
training-observed decorated variants. Mark-only anchors lie at the centroids of
the two geometric components. Each anchor carries a colored displacement cloud
describing the corresponding learned junction neighborhood. Root versus neighbor
roles and opaque species are the colors; there are no target atom IDs, phase
labels or configuration IDs inside the motif values.

Both endpoint clouds are transported into the same base-motif frame using the
inverse of its registered rotation. Placement applies one common proper rotation
to the atomic anchors, mark anchors and both cloud values. Translation acts only
on anchor positions. The endpoint pair is observed jointly during training; an
arbitrary Cartesian product of separately observed endpoints is not inserted.
Exact-value deduplication is allowed, but no approximate merging is performed.
The 9,200 variants are a large empirical catalogue, not a compression success.

An m-assignment denotes clouds within 0.15 Å under a color-preserving bijection.
Overlapping assignments must contain one common cloud value. Atomic and centroid
anchors register to known point identities within 0.15 Å. Consequently the
subsequent integer-capacity point calculation is exact on the registered domain,
while the geometry and cloud comparisons remain numerical/tolerance-based.
This is not an exact Euclidean-tiling certificate.

## Supplied-filling gate

All 100 selected training covers admit the exported markings, covering 9,200
pair occurrences. At each junction, the actual geometric cloud supplies a common
witness for both incident marked motifs. Independent replay checks 18,752 accepted
endpoint assignments across training and developmental queries, source geometry,
proper rotations, component identities and exact integer filling. Maximum atomic
anchor residual is 0.1499651895 Å; maximum marking residual is 0.1499994306 Å.
This verifies the requested pre-search consistency gate, not independent learning
success: the catalogue was built to represent these training covers.

| Existing selected covers | Pair occurrences with compatible endpoint markings | Complete covers admitting the witnessed lift |
| --- | ---: | ---: |
| 100 training configurations | 9,200 / 9,200 | 100 / 100 |
| 100 developmental configurations | 76 / 9,200 | 0 / 100 |

Only 87 training occurrences have a witnessed compatible decoration sourced from
another configuration. Those counts are observed matches, not independent samples.
The fields fit training but currently behave predominantly as memorized contexts.

The 76/9,200 result is **not directly comparable** with the earlier 6,356/9,200
junction-recognition score. The earlier query may rotate a whole junction to its
best template. This test requires both endpoint contexts on one pair motif, locked
to that pair's registered pose. Its unit is a pair occurrence, not one junction.
It is a stronger and different question.

## Rotation sensitivity

For the first developmental frame of each phase, a follow-up enumerates all
species-preserving proper Procrustes proposals for each already assigned base
type. There are 386 such proposals for 368 selected pair occurrences. Endpoint
clouds still cannot rotate independently. Coverage remains 3/368, unchanged from
the saved-pose query on these four frames. This limited control does not show that
all continuous maximum-error feasible poses or all alternative base types have
been exhausted. It does indicate that simply adding these extra pose hypotheses
does not repair the observed gap.

## Reference-search engineering pilot

The first training and first developmental frames of VIII are chosen because
they have the smallest atom count in this pilot: 192 atoms each. This is a declared
engineering test, not a representative or outcome-selected success benchmark.
Every learned decoration is offered at every matching registered base pose,
without using the target junction cloud or the selected-cover answer to filter
candidates. The pools contain 59,051 and 48,504 decorated candidates. Inventory
prevents selecting two decorations of the same base placement.

| Frame | Same-pool markings off | Markings on |
| --- | --- | --- |
| VIII training c01500 | Finite filling at 7.12 s; 3 disconnected support components | Unknown at 30 s; 33 selected placements |
| VIII developmental c01900 | Unknown at 30 s; 63 selected placements | Unknown at 30 s; 47 selected placements |

No run demonstrates connected material growth or a GCTS advantage. Markings-off
retains redundant variants for the matched-pool control; a collapsed unmarked
baseline would be required for a competitive timing claim. Learning, compilation
and setup are outside the reported search times. These single-run checkpoints do
not justify a statistical runtime conclusion.

The unchanged reference harness checks the full frontier for dead ends, then
forced moves, then generation-first branches. All finite target atoms are active
generation-zero roots. Cloud disjointness removes candidates through the graph;
pairwise compatibility is a relaxation, so completion additionally requires a
verified common cloud witness. Failure of the incomplete witness proposer means
unknown, never pruning. Full dependency rebuilding and rollback include mark-only
anchors and shared-placement inventory. Independent replay checks all 107,555
compiled candidates and all four final states. The harness checks forward/reverse
incidence, decision order and root rollback during its runs. Existing exhaustive
controls cover 150 tiny models, 38,400 subsets and 730 visited states.

## What this changes—and what remains open

The experiment closes a representational gap: paired, motif-local geometric
markings can be transported with one tile pose, checked on the training tilings,
and consumed by the reference point search. It exposes two unresolved problems:
weak connection transfer and expensive search through many nearly memorized
decorations. Neither may be hidden by declaring every missing query forbidden.

The next algorithmic check should identify candidates with no compatible
complement at a half-filled component. Such a candidate cannot occur in a complete
filling of this fixed marked model. Any proposed preprocessing must prove that
implication, preserve the marked solution set, and be checked against exhaustive
small cases before it is used; it must not replace the reference scheduler.

A separate controlled experiment should test whether less detailed, factorized
geometric channels preserve useful connection information with better transfer—for
example, separating relative component geometry from internal coordinate variation.
Keep the base point model, supplied-filling gate and full-configuration metrics
fixed. Broader samples and additional pose/type hypotheses also remain candidates
for investigation; no present result identifies a single cause.

The earlier cohort-provenance limitations remain: these are developmental frames,
not independently verified same-condition trajectories. No physics or chemistry
rule enters the exporter or search. Raw coordinate-derived libraries are not
republished; public checks and hashes are audit evidence, not a self-contained
reproduction bundle. The production growth UI is unchanged.

## Reproduction

```
python ice-portable-pairs.py COORDINATES COVER DICTIONARY SELECTION JUNCTIONS LIBRARY
python ice-portable-precheck.py COORDINATES COVER DICTIONARY SELECTION LIBRARY PRECHECK
python verify-ice-portable.py COORDINATES COVER DICTIONARY SELECTION JUNCTIONS LIBRARY PRECHECK CHECK
python test-ice-portable-pairs.py COORDINATES COVER DICTIONARY SELECTION JUNCTIONS LIBRARY PRECHECK
python compile-ice-portable-search.py DICTIONARY COVER LIBRARY c01500,c01900 MODEL
node boron-portable-search.mjs MODEL KERNEL NEW_SEARCH_FOLDER
python verify-ice-portable-search.py DICTIONARY COVER LIBRARY MODEL SEARCH_FOLDER KERNEL SEARCH_CHECK
python ice-portable-pose-audit.py COORDINATES COVER DICTIONARY SELECTION LIBRARY PRECHECK POSE_CHECK
```

The existing generic cloud-search harness retains its historical boron filename;
no boron-specific rule is applied to these ice inputs. Python dependencies are
NumPy, SciPy and ASE. Use the preceding junction experiment's exact inputs and
library hashes. Tests also check 100 two-ended rotation compositions/inverses,
reflection rejection and four deliberate export corruptions.
