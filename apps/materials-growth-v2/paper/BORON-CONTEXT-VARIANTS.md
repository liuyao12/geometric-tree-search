# One geometric motif, multiple context-dependent marked variants

14 September 2026. Geometry-only development pilot; not a physical growth model.

## Representation change

The previous fits required one marking assignment per bare geometric motif.
This pilot permits several assignments. In each five-input training fold,
compute a common radius of 1.35 times the pooled median nearest-neighbor distance.
At each training atom, count neighbors within that radius in the same finite
minimum-image quotient used by the other controls. This chosen geometric
descriptor produces labels 5–9; no coordination number, bond rule, element-specific
chemistry or phase label is prescribed.

For each occurrence of a geometric three-site template, record its ordered
triple of observed site labels. Distinct triples become marked variants of that
template. This is an explicit descriptor-based hypothesis, not general learned
anchor discovery. The shared t=1/3 model is inherited from selected training.

Across the six folds, 633–851 geometric types produce 900–1334 marked variants;
160–262 types have multiple variants. All registered training occurrences
contribute observed variants, so the selected training covers satisfy the
markings directly. The library is frozen before reading held-out pose data.

Every learned variant is offered at every acceptable held-out geometric pose.
Site permutations are re-enumerated, rather than reusing deduplication based
on old scalar weights. The held-out neighborhood is not used to choose or
filter variants. An independent checker verifies this full Cartesian expansion
relative to the supplied poses, and independently recomputes training descriptors
using periodic image enumeration.

## Three search lanes

1. Unmarked collapsed: one candidate per base template/atom-support identity.
2. Unmarked expanded: same candidate IDs as marked, but erase m-values.
3. Marked: every learned variant, with scalar overlap agreement.

Variants of one base placement share an inventory constraint so they cannot be
counted multiple times. Both unmarked controls are necessary: erasing labels
without collapsing equivalent candidates can itself make the baseline slower
or change its branching order. The reference PointSearch kernel is unchanged.

| Omitted model | Collapsed unmarked backtracks | Expanded unmarked backtracks | Marked backtracks | Marked outcome |
| --- | ---: | ---: | ---: | --- |
| alpha | 3 | 38 | 134 | Finite cover |
| beta-105 | 21 | 18706 | 783 | Finite cover |
| beta-106 | 0 | 450 | 38025 | Time budget unknown |
| gamma | 258 | 21478 | 74661 | Step budget unknown |
| tau-105 | 843 | 41059 (time budget) | 2839 | Finite cover |
| tau-106 | 78633 | 118 | 1063 | Finite cover |

Budgets are 100,000 advances or 15 seconds per lane. These are single-order
pilot measurements with audit overhead, excluding training and construction
costs. They do not establish a general or end-to-end speedup. In particular,
the tau-106 improvement over the collapsed baseline cannot be attributed solely
to markings: its expanded unmarked baseline does even better.

## Internal agreement is not correct environment prediction

After search, the independent evaluator computes the omitted configuration's
neighbor descriptors using the frozen training radius. This information is
never fed back into candidate selection in this experiment.

| Completed marked cover | Labels matching post-hoc target descriptor | Components |
| --- | ---: | ---: |
| alpha | 7 / 12 | 1 |
| beta-105 | 97 / 105 | 6 |
| tau-105 | 198 / 210 | 2 |
| tau-106 | 186 / 212 | 1 |

All four covers pass exact integer filling, overlap-label agreement and
base-inventory uniqueness. However, some globally consistent labels disagree
with their geometric descriptor interpretation in the target. This is a useful
warning: agreement alone does not ensure that a latent marking carries its
intended meaning. The two unfinished runs are not classified as untileable.

## Scope and next direction

This implements multiple learned marked variants per geometric motif without
using the held-out phase or neighborhood as a selector. It does not yet deliver
reliable connection rules. More of the surrounding geometry may need to be
represented explicitly in the motif or anchor domain, rather than compressed
into a neighbor-count label whose meaning search does not enforce.

No new material coordinates were acquired. These boron models are not a
documented independent common-T/P ensemble. Target atom positions still supply
the finite candidate poses; all target points begin at generation zero. Proper
rotations use approximate Kabsch fits within 0.01 Å, without complete continuous
pose or periodic-image enumeration. The checks support finite point-cover
claims, not blind or connected material growth.

Runtime checks independently reconstruct the frontier graph, reverse incidence,
integer totals and inventory/mark legality. Root point/mark/graph rollback is
checked. A separate verifier checks training-only provenance, descriptor values,
variant membership, pose geometry, unfiltered variant expansion, final covers
and post-hoc descriptor agreement. No production growth rules were changed.

## Reproduce

Use the previous boron training, selected-cover and alternative-pose artifacts.
Keep the geometry helper scripts from those reports beside the new scripts.
Output directories must be new.

```
python boron-context-variants.py boron-holdout boron-selected boron-alternatives boron-context-variants
node boron-variant-search.mjs boron-context-variants /path/to/kernel.mjs boron-context-search
python verify-boron-context-variants.py boron-data/input-audit.json boron-holdout boron-context-variants boron-context-search verification.json
```

Public summaries omit source coordinates. Local artifacts retain frozen
libraries, poses, complete candidate point models and selections for replay.
