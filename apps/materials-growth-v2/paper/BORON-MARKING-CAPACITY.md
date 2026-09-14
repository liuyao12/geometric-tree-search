# More marking channels are not enough on the current boron domain

14 September 2026. Representation-capacity audit and a site-decoration prototype.

## A precise limit, not a negative claim about GCTS

Fix the marking sites, transported role identities, exact equality matching,
invariant channel action and selected positive training fillings. Form a graph
whose vertices are marking variables and whose edges require equality at a
training overlap. Every training-compatible marking is constant on each
connected component. Assigning a distinct scalar label to every component
already separates all pairs of variables that this representation can separate.

Any number of additional invariant channels still assigns a constant tuple to
each component. It can merge components or retain their separation, but cannot
split one without violating a training equality. Thus extra channels alone
cannot strengthen the existing maximal component-label marking. This does not
cover changed domains, occurrence variants, nontrivial representation actions,
different decompositions, or approximate rather than exact marking agreement.

The independent audit reconstructs the 78 symmetry-tied components in the
current boron learner. Exhaustive controls examine 14,528 two-channel label
assignments on 50 small graphs; all 1,844 training-compatible assignments obey
the component restriction. The general statement follows from transitivity of
equality, not from those finite tests.

## Prototype: let the decoration break a motif's symmetry

Keep the learned t-values and their symmetry ties, but learn m separately on
the 219 individual template sites. Do not require two symmetry-related sites
to have equal m merely because their t-values agree. The six original selected
fillings give **89 site-label classes**, instead of 78 tied classes.

For each physical occurrence, transport those labels through each stored
proper self-registration permutation, plus identity; pair motifs also admit
the endpoint swap. Deduplicate only identical complete assignments. Different
decorations on the same physical occurrence disagree at some marked atom, so
two such variants cannot coexist. No additional physical copy is introduced.

This uses the previously stored self-pose witnesses, not an exhaustive
classification of approximate symmetries. An independent check validates 81
stored rotation matrices, permutations and self-registration residuals; the
largest residual is 0.022534 Å, within the inherited geometric admission bound.
Exact t/m checking is on source atom identities, not an exact Euclidean tiling
certificate. The new model is a restricted orientation-decorated experiment.

| Model | Physical candidates | Decorated candidates | Same partial-state legality as original marking? |
| --- | ---: | ---: | --- |
| α | 108 | 243 | Not established |
| β-105 | 1,458 | 1,566 | Not established |
| β-106 | 4,779 | 4,779 | Yes, by exact conflict-set comparison |
| γ | 486 | 540 | Not established |
| τ-105 | 2,916 | 3,132 | Not established |
| τ-106 | 7,884 | 7,884 | Yes, by exact conflict-set comparison |

All six original training fillings pass exact t-sum and m-agreement checks in
the compiled decorated models. This is in-sample fitting, not generalization.
The verifier independently reconstructs the equality partition, full witnessed
variant sets, site transports and training selections.

## Why we did not rerun the same hard searches

Each hard-model physical candidate has exactly one distinct decoration, and
the complete forbidden-pair sets are identical to the original: 648 pairs for
β-106 and 1,485 for τ-106. The t-data are unchanged. Consequently, after the
candidate-ID bijection, every partial placement set has the same legality and
the same frontier candidate domains. With the same policy and scheduler there
is no new pruning mechanism to test. We do not turn this into a wall-time
equivalence claim, and no new search-completion result is reported.

More channels or this particular symmetry relaxation therefore cannot solve
the hard cases on their existing point domain. The next meaningful hypotheses
must change marking neighborhoods, representation actions, or the jointly
learned motif/occurrence decomposition. New anchors must be geometrically
specified and learned, not target-ID labels or disguised prescribed answers.

The production app is unchanged. These prototypes do not close the goals of
shared-family learning, independent condition-matched validation, unrestricted
rotations, or growth beyond the supplied configuration.

```
python boron-site-decoration.py INPUT LEARNING COMPILED
python verify-boron-site-decoration.py INPUT LEARNING COMPILED CHECK
python test-marking-capacity.py
```

Use the original `precheck-v2.json` and `periodic-connected-c12-v1.json`.
Only code and aggregate checks are published, not raw source coordinates.
