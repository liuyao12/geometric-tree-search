# Learned compounds across boron configurations

## Motivation and construction

The difficult training decompositions are connector-heavy: β-B106 selects 3,132
pair placements and 54 larger face motifs; τ-B106 selects 5,265 pairs and 162 face
motifs. Adding more filters did not solve their reference searches. This experiment
therefore learns finite compositions of existing motifs.

For each selected face motif, collect selected pairs sharing an atom with it.
Transform their external endpoints into its proper-rotation frame. The 783 source
occurrences produce 92 stored neighborhood entries; coordinate rounding is used
for storage deduplication, not for asserting a complete isometry classification.

Whole neighborhoods did not transfer across configurations within 0.03 Å. The
revised proposal step retains matching subcompounds containing a face motif and
at least two connectors. It tries the recorded self-symmetries of the central
motif at each observed target occurrence. Pair endpoint reversal is permitted
only when both endpoint t/m assignments are preserved. Endpoint numbering alone
is not an orientation constraint.

Every compound stores its constituent base placements and aggregate t/m values.
Their integer t-sums must not exceed capacity; overlapping assigned m-values must
agree. No weights are renormalized. No physical potential or chemical rule is used.

## Independent verification

A separate checker reconstructs periodic images and proper fits with a library
rotation solver, verifies source selections, decorated symmetry actions, target
expansions, and cross-configuration provenance. It checks 783 source occurrences
and 39,123 geometric witnesses. The maximum external endpoint residual is
0.028527 Å, below the declared 0.03 Å tolerance. Arithmetic filling checks are
exact integers; geometric matching remains approximate.

| Target | All compiled proposals | Proposals supported by another configuration |
|---|---:|---:|
| α-B | 27 | 0 |
| β-B105 | 486 | 324 |
| β-B106 | 108 | 54 |
| γ-B | 54 | 0 |
| τ-B105 | 1,188 | 270 |
| τ-B106 | 324 | 54 |

The 702 cross-configuration proposals are embeddings, not 702 independent samples
or distinct motif types. The difficult B106 cases receive compounds containing
three or five base placements. Periodic replicas are not independent evidence.

## Reference-search comparison

Only compounds observed in another configuration are eligible for the guidance
lane. They receive a soft preference when all remaining constituents are jointly
compatible with the current state. Partly built compounds receive higher priority.
No compound executes atomically: the original base engine still performs every
placement, global dead/forced propagation, and earliest-generation branching.
All base candidates remain available; absence from the proposal library never
eliminates a candidate. This is guidance, not learned exclusion marking or RL.

Both lanes use the original marked model, identical observed candidate pools, all
target points as roots, and limits of 100,000 advances or 15 seconds. All twelve
saved runs pass an independent reconstruction of the original input t/m model.
Runtime audits check forward/reverse domains, decision order, and exact rollback.

Both lanes complete α-B, β-B105, γ-B and τ-B105. β-B106 and τ-B106 remain
budget-unknown. There is no demonstrated completion or speed advantage. In this
unoptimized prototype, evaluating proposals even during forced propagation adds
noticeable overhead. Learning/compilation costs are not included in reported
search times; no end-to-end efficiency claim is made.

## What changed, and what did not

This creates a geometrically checked compound library with inspectable base
expansions and some cross-configuration reuse. It does not yet re-learn the base
t-values, replace the decomposition, learn new useful m-values, or reconstruct
the two difficult structures. Excluding a target's compound observations is not
whole-pipeline holdout: the base dictionary and t/m were fitted jointly on all six.
These inputs also lack a verified identical-condition cohort designation.

The current proposal family is limited to compounds around face motifs. Much of
the difficult pair network lies outside those neighborhoods. Pair-only compound
discovery and joint decomposition/weight fitting remain important next tests.
Stored-pose matching is not continuous-pose completeness or seed-driven growth.

Files: `boron-compound-proposals.py`, `verify-boron-compounds.py`,
`boron-compound-search.mjs`, and `verify-boron-compound-search.py`.
Proposal artifact SHA256:
`f36a0a7f7d9afcb46e7d076b40311efcdbe948c3bef4074f44fee7c441da117c`.
Aggregate checks and full search summaries accompany the report. Raw coordinates
are not redistributed here.
