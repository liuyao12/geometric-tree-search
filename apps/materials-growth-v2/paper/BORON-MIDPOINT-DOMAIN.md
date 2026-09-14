# An enlarged marking domain must actually overlap

14 September 2026. Rejected anchor proposal; no new search or growth result.

## Proposal and limits

For every motif, propose the midpoint of each pair of its sites as an additional
marking anchor. Keep the original positive t-support and t-values. Tie midpoint
roles under stored self-registration permutations and require internal marking
assignments to be single-valued. Learn scalar equalities only where selected
training occurrences assign labels to the same anchor.

The locations are deterministic geometric proposals, **not freely learned
anchors**. The scalar labels are fitted, but a large label count is not evidence
of learned inter-cluster connections. This is deliberately a domain-admission
test before running another search.

Occurrences are lifted using their stored periodic image offsets. Midpoints are
wrapped into the source cell and identified by fractional coordinates rounded
to a grid of 10^-9. Distinct atom pairs can therefore share a geometric anchor;
the identity is not an unordered atom-pair ID. However, this very fine snapping
is a declared finite identity control, not matching within the full registration
error bar. It does not establish robust continuous-space or tolerance-complete
matching. Altering snapping or permitting wider matching can change the result.

## Result: no connection supervision

The proposal yields 2,097 template anchor variables and 1,617 equality classes.
**Every variable has zero inter-cluster sharing in the selected training
fillings.** The classes arise from self-symmetry and internal coincidences,
not observed connections between distinct selected clusters.

| Structure | Distinct compiled anchors | Shared between selected clusters | New conflicts not already forbidden by t |
| --- | ---: | ---: | ---: |
| α | 1,728 | 0 | 0 |
| β-105 | 28,296 | 0 | 0 |
| β-106 | 25,866 | 0 | 0 |
| γ | 5,022 | 0 | 0 |
| τ-105 | 57,348 | 0 | 0 |
| τ-106 | 53,568 | 0 | 0 |

The selected positive supports overlap in at most one atom per pair of clusters
in all six configurations. Pair midpoints internal to those supports consequently
provide no shared-pair supervision; the compiled coordinate check also finds no
inter-cluster coincidences between different pairs. There are 27 and 54 new
marking-conflicting candidate pairs in β-106 and τ-106, respectively, but every
one already exceeds t-capacity somewhere. All training markings agree.

## Verification scope

A separate checker reconstructs training incidence, selected atom-overlap
multiplicities, every conflicting pair of compiled anchors, and global pairwise
t-capacity tests. It agrees with the generator on all six models. It does not
independently reconstruct the geometric quantizer or prove robust midpoint
coincidence under perturbations. The no-added-pruning conclusion applies to the
compiled fixed domain, not every possible midpoint-matching convention.

No repeat tree search is needed to establish the lack of additional pruning in
this model: all its new exclusions are already direct t-capacity exclusions.
No production code is changed and these anchors are not admitted as a useful
learned growth library.

## Consequence

A useful next proposal should place marking support in genuinely overlapping
neighborhoods of neighboring clusters, or learn a nontrivial transformation
action at existing contacts. It must demonstrate repeated inter-cluster
observations and pre-search consistency before a large training or search run.
Adding many unshared points inside clusters fails that requirement.

This is a diagnostic about this selected boron decomposition. It is not a
negative result about all midpoint domains, ice, other families, or GCTS. The
goal of learning anchors and transferable connection rules remains open.

```
python boron-midpoint-domain.py INPUT LEARNING FACE_FOLDER COMPILED
python verify-boron-midpoint-domain.py INPUT LEARNING COMPILED CHECK
```

Use `precheck-v2.json` and the original `periodic-connected-c12-v1.json`.
Code and aggregate checks are public; compiled coordinates remain local.
