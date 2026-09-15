# Why the factorized ice search repeats failures

The first failed child in each of the four v4 pilot models already exposes
an unsupported endpoint value. Keeping the candidate's t-values and inventory
but erasing one endpoint mark still leaves a required point with no candidate.
The erased mark is unconstrained, so this relaxed state contains every possible
choice at that endpoint. A dead point therefore excludes the entire row or
column in this parent, not only the attempted decorated pair.

Independent Python replay checks all incident blocks and endpoint options at
each claimed dead point, with a separate color-preserving bijection matcher.
Eight certificates required 12,603 cloud-pair tests. All occur at the root.

| Library/frame | Endpoint choices per side | Distinct pairs excluded by the two certificates |
| --- | ---: | ---: |
| One-cover/training | 36 | 71 |
| One-cover/developmental | 120 | 239 |
| Multi-cover/training | 68 | 135 |
| Multi-cover/developmental | 222 | 443 |

The two certificates overlap in one pair, giving 2n−1 exclusions per example,
888 total. This is only the first failed child per frame, not an exhaustive
analysis of all failures. The search has not yet integrated these exclusions.
There is no speedup or completed reconstruction result from this diagnostic.

No identical serialized endpoint clouds occur in the one-cover library. The
multi-cover library has some duplicates, but hypothetical byte-identical merging
would leave 37,408,354 and 28,458,786 conceptual candidates respectively. No
merging was performed, and serialized identity is not a complete cloud-isometry
test. Duplicate cleanup alone cannot remove the bulk of the branching domain.

Next: implement a separately labeled, proof-producing complementary-support
filter that updates the complete candidate graph before reference scheduling.
Preserve shared inventory, endpoint dependencies and exact rollback. Check
known training lifts, tiny exhaustive solution equivalence and proof mutation
controls before new material runs. Never transfer these root-specific proofs
to other configurations as if they were learned material laws.

Artifacts: `/tmp/gcts-ice-{one,multi}-dead-cylinder-v1.json` and independent
checks `/tmp/gcts-ice-{one,multi}-dead-cylinder-check-v2.json`.
