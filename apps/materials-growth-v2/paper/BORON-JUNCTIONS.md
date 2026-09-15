# Learned junction markings: a new τ-B106 reconstruction

The learned junction model now reconstructs the finite τ-B106 configuration:
5,724 required atom positions, 5,427 selected base placements, and one connected
positive-support component. An independent checker verifies exact t-sums, original
m-values and all 2,052 junction choices. This is a new finite reconstruction result,
not blind growth or a demonstrated speedup.

## Learning connections rather than ordering proposals

At points incident only to pair motifs, collect the selected incident placements
from each training filling. Their periodic displacement vectors, motif identities
and endpoint t/m decorations define a rooted geometric junction. Proper rotations
are fitted within 0.03 Å; arbitrary endpoint numbering is not a geometric feature.
The t-values remain the previously learned integer weights. No chemistry, energy,
temperature or formation history enters this learner.

Training uses six original fillings and twelve generated alternative fillings.
Only four alternatives are genuinely different; the others reproduce originals.
After per-point duplicate removal there are 6,322 observed junction choices and
388 stored geometric templates. Representatives are fixed, not transitively merged.
The dictionary is not claimed to be a minimal or exhaustive isometry classification.

The compiler enumerates local incident subsets whose t-values sum to capacity and
retains those with a verified template fit. All six original and all twelve
alternative fillings remain representable. Recorded geometry is independently
reconstructed: 6,322 source fits and 19,305 target fits pass, with maximum residual
0.029985 Å. A failed fit is not a certificate that no approximate rotation exists.

| Configuration | Constrained junction points | Admitted local states | Explicit marked variants |
|---|---:|---:|---:|
| α-B | 0 | 0 | 108 |
| β-B105 | 27 | 27 | 1,458 |
| β-B106 | 1,350 | 11,016 | 111,942 |
| γ-B | 0 | 0 | 486 |
| τ-B105 | 54 | 54 | 2,916 |
| τ-B106 | 2,052 | 7,587 | 40,608 |

These counts are finite embeddings in known configurations, not independent
samples. Most hard-case junctions still have multiple admitted states.

## Explicit GCTS marking interpretation

For a junction point p, let S be an admitted set of incident base placements,
with total t-capacity exactly filled. Give S a distinct scalar label at p. A base
placement has one marked copy for every compatible choice of such a label at each
of its constrained endpoints. Its original t-values and original marking channel
are unchanged; an additional `junction` channel carries the labels.

The labels are finite encodings of geometrically embedded junction states at a
point. This construction is presently compiled on the observed point domain,
not supplied as an unrestricted continuous-space transformation library.

**Complete-filling equivalence.** If incident copies agree on label S, every
selected base placement there belongs to S. Since contributions are positive and
S sums exactly to capacity, a complete filling must select all of S. Conversely,
if a base filling uses an admitted local state at each junction, choosing those
labels provides compatible copies of every selected base placement. Distinct copies
of the same base placement disagree on at least one shared junction label, so they
cannot both be selected. No extra inventory rule is needed for these variants.

The explicit compiler creates all the variants counted above. The native point-value
verifier checks nineteen lifted fillings: eighteen training records and the new
τ-B106 search witness. Two exhaustive cyclic toy controls also confirm equality
of the projected solution sets, including duplicate-base exclusion.

## Implicit propagation and the reference search

Materializing 111,942 β-B106 copies is avoidable. The prototype maintains possible
junction labels implicitly and removes a base candidate when no compatible label
can support it. These removals update the complete frontier/candidate graph.
Global dead ends, global degree-one moves, earliest-generation branching and exact
rollback are retained. No known selected filling is passed to the search engine.

This is a projected marking plug-in, not the literal expanded-variant search trace.
Its complete solutions have the explicit marking realization above. The learned
junction library restricts the problem: failure cannot prove the original unmarked
problem impossible, and passing the training fillings does not prove preservation
of every other valid filling.

The first implementation propagates unavailable connections. A cached version
avoids repeated legality evaluation and matches it for 600 advances on each hard
input. A stronger prototype propagates both absent and mandatory connections
between junctions. Each implementation passes 150 small-model checks against
16,448 independently enumerated subsets, plus graph, scheduling and rollback checks.
Geometry tests cover 100 rotation/permutation cases, 100 chiral reflection rejections,
100 decoration mutations, and a rank-one rotational case.

## Reconstruction results and budget limits

The initial 15-second / 100,000-advance comparison still completes four of six
inputs in both lanes. We then give the original implicit junction implementation
up to 300 seconds / 1,000,000 advances on each difficult input:

| Input | Search time | Advances | Result |
|---|---:|---:|---|
| β-B106 | 300.05 s | 11,580 | Budget unknown |
| τ-B106 | 93.48 s | 5,694 | Exact connected finite filling |

The τ witness fills all 5,724 required points and lifts to ordinary scalar markings.
Together with the four easier cases, five of the six available structures now have
verified reference-based finite reconstructions under these experiments. Budgets
are not uniform across this count. There is no matched extended-budget baseline
in this report, so this is **not a speedup claim**. Setup, learning and compilation
costs are outside the tabulated search times; single local timings are not a
statistical performance study. The later two-polarity propagation prototype still
leaves both difficult cases unknown in its 15-second runs.

## A failed shortcut: train only on the original filling

Training on just the six original fillings reduces the library to 115 templates.
It preserves those six but rejects all four genuinely different withheld B106
decompositions: 747 and 775 unsupported junctions in the two β alternatives, and
706 and 734 in the τ alternatives. These are withheld decompositions on the same
coordinates, not independent material samples. We therefore retain the broader
ensemble instead of presenting the restrictive model as an improvement.

## Remaining scope

β-B106 is unresolved. Junctions touching larger face motifs remain outside this
new marking domain. Neighboring junction contexts are not yet learned jointly.
All six coordinate sets contribute to the base dictionary, t/m and junction
training; identical-condition provenance and independent whole-pipeline holdout
are still missing. The existing boron provenance/erratum caveats remain in force.
This result does not establish continuous-pose completeness, seed-driven growth,
new physical predictions, or completion of the broader family-reconstruction goal.

Junction artifact SHA256:
`56a6fd34c6620378aebbb8f5f14129feaeb8f327ce66825051716392cbdd2955`.
The report publishes code, aggregate checks and per-run summaries, not raw source
coordinates. `compile-junction-markings.mjs` gives the explicit scalar realization;
`verify-boron-junction-search.py` reconstructs and checks saved search results.
