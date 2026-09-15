# Learn halo locations from observed neighboring clusters

14 September 2026. Geometry-proposal stage; no new marking or growth result.

The rejected midpoint proposal placed points inside motifs without observing
inter-cluster sharing. This experiment instead uses the actual external atoms
of selected neighboring occurrences to propose halo locations in motif-local
coordinates. It does not prescribe a molecular formula, potential, bond angle
or radial shell.

## Learning rule

For each selected full-dimensional motif occurrence, fit a proper rigid pose
between its template and observed atoms. Find other selected occurrences that
share an atom, align their periodic image at that contact, and collect their
atoms outside the current motif. Transform these external atoms into the motif
frame. Deduplicate numerical replicas, cluster the observed locations by
complete-linkage at the inherited 0.03 Å tolerance, and use cluster means as
candidate anchor positions. All learned means remain within that tolerance of
the observations assigned to them.

This is learning locations from observed neighborhoods, conditional on the
existing motif library and selected training decompositions. It is not joint
discovery of the entire GCTS model. Neighborhood selection is one contact step,
not an unrestricted search over marking domains.

## Observed support

Across the twelve full-dimensional motif types, the learner proposes **303 halo
locations**. Of these, 146 are supported in every selected occurrence of their
type, and 45 have support in more than one of the six source configurations.
All 783 full-dimensional selected occurrences pass the global rigid-transform
invariance check. The other 12,636 selected occurrences are pair motifs and
are not used to learn their own halos.

| Shared motif type | Source configurations | Proposed anchors | Supported in every occurrence |
| --- | --- | ---: | ---: |
| 2 | β-105, τ-105 | 34 | 13 |
| 3 | β-105, τ-105 | 50 | 0 |
| 5 | β-106, τ-106 | 63 | 13 |

Type identifiers refer to the existing learned dictionary, not chemical rules.
An anchor absent from some observed neighborhood is not evidence that the
configuration is invalid. A union of alternative neighborhoods must not be
treated as a mandatory list of atoms to add. Some anchors have very little
support; they are candidates for later selection, not admitted matching rules.

Periodic replicas are not independent samples. The implementation also reports
deduplicated frame-coordinate point-cloud patterns, but those counts are not
fully quotiented by motif self-symmetry and must not be called distinct physical
environment classes. These are jointly fitted observations, not held-out transfer
or a verified same-condition ensemble.

## The pair-frame issue

Two sites determine an axis but not an azimuthal orientation about it. Assigning
an arbitrary transverse frame would silently encode an unsupported choice.
The four pair types therefore remain deferred for halo learning. Resolving
their continuous orientation freedom requires an explicit representation,
decorated variants or jointly learned neighboring geometry. This gap matters
because pair motifs account for most selected occurrences.

## Verification and next gate

An independent checker uses a library rotation fit and reconstructs neighbors
by intersecting occurrence atom sets, rather than the learner's incidence
traversal. It confirms every anchor-support count and coverage of the observed
external points. The maximum coverage error is 0.019264 Å; the largest base
registration residual is 0.029140 Å. These are numerical geometric checks, not
exact Euclidean identities. The checker does not establish optimality or
uniqueness of the location clustering.

Additional synthetic tests cover 40 proper rigid transformations, 40 common
correspondence permutations and rejection of an underdetermined pair frame.
The current t-values are unchanged. No m-values are fitted in this stage, and
no complete transported halo domain is yet compiled for search. Self-symmetry
handling, unmatched halo points, tolerance-consistent global point identities,
and consistency across all training fillings must be resolved before a growth
claim. The production app is unchanged.

The next experiment should select a useful subset of these recurrent locations
and fit matching values while preserving complete training fillings. It must
not activate a location only when a desired target atom is already known to
exist: the resulting domain must belong to the motif and transport with it.

```
python boron-halo-proposals.py INPUT LEARNING FACE_FOLDER PROPOSALS
python verify-boron-halo-proposals.py INPUT LEARNING FACE_FOLDER PROPOSALS CHECK
python test-boron-halo-frames.py
```

Use the original `precheck-v2.json` and `periodic-connected-c12-v1.json`.
Code and aggregate checks are published; learned coordinate clouds remain local.
