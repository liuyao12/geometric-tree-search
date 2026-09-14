# Certified local conflict reuse on the boron family

14 September 2026. A search-engine control, not a learned physical or geometric
law transferable between materials. Production growth code is unchanged.

## What can safely be reused?

For a fixed, complete finite point model, let S be a legal set of placements
and p a required point. A certificate consists of p and S with two properties:

1. The t-sum of S at p is strictly below capacity.
2. Every candidate with positive support at p is already in S, exceeds capacity
   somewhere when added to S, or disagrees with an assigned marking in S.

No exact cover can contain S. Any such cover must add a new placement touching
p, but every such placement is already blocked. Overflow and marking conflict
persist when further compatible placements are added. Consequently S is a
valid forbidden combination (a nogood) for this fixed model, independent of
the order in which its members were selected.

This is stronger evidence than a repeated placement-set hash and narrower than
a general motif prohibition. The certificate is bound to actual candidate and
point identities. No rotation, translation or cross-configuration transfer is
performed. In particular, we do not forbid a motif merely because one placement
combination involving it failed.

## Implementation and safeguards

The generator finds sufficient blockers for each candidate at a dead point:
selected inventory, a sufficient sum of capacity contributions, or a conflicting
mark owner. It unions these witnesses and checks the resulting certificate
before storing it. Cores are sufficient, not proved minimal.

A candidate is removed when placing it would complete a stored forbidden
combination. The removal goes through the same point–candidate graph and
global dead/forced/earliest-generation scheduler. Every member of a certificate
depends on the t/m-support of every other member. These extra dependencies
ensure distant candidate domains are refreshed on placement and undo.

Rules persist across branch rollback and have a monotonically increasing
version. Their truth is independent of the branch, but their current effect
on candidate legality is rederived. A unary rule may legitimately change the
root graph. Tests therefore distinguish rollback under retained proofs from
an explicit cold reset: undo placements, clear the stack and proofs, rebuild
domains, then compare with the original root. This is not a claim that learned
rules disappear automatically on undo or that arbitrary stack serialization
has been tested.

This first version rejects dynamic candidate additions, incomplete pools,
activation callbacks, custom constraints, initial placements, fixed markings,
and multiple marking intervals on one candidate point/channel. Mark-only
points and interval-valued marks are supported. All positive-support points
must be required roots. These are declared implementation limits, not changes
to the general GCTS formulation.

Crucially, a branch-local failed-choice exclusion is not treated as a direct
physical certificate. A dead point involving such a blocker is skipped if
the complete physical candidate set is not also blocked by the proposed core.
The same applies to a rejection supported only by another stored certificate.
Composing those proofs is future work; no unproved global ban is substituted.

## Verification and results

Exhaustive tests on 200 small models inspect 1,360 search states and 357
generated certificates, comparing against all exact completions. No compatible
completion is removed. Additional controls check distant positive supports,
mark-only witnesses, unary-rule rollback/reset, invalid certificate rejection
and immutable candidate-pool enforcement.

On all six boron inputs, use the frozen jointly learned weights and markings,
full registered candidate pools, parent exclusions and linear frontier scan.
Run marked and unmarked lanes with 100,000-advance / 15-second budgets.
The supplied training selection is not given to search. An independent Python
verifier reconstructs each certificate's exact totals and markings, checks
every candidate at its dead point, and separately verifies that no certificate
excludes the known connected training witness. The existing independent
material verifier also checks the full final states and model reconstruction.

The completed structures remain α, β-105, γ and τ-105, all connected in both
lanes. β-106 and τ-106 remain budget-unknown. Certificate counts and final-state
checks are provided in the linked JSON artifacts; counts can differ at
wall-clock cutoffs. This adds independently checkable, sound conflict reuse
but does not yet solve the hard reconstructions or demonstrate a speedup.

The implementation pays for certificate checks and extra dependencies. The
`reusedRejections` diagnostic counts reason evaluations, including repeated
refreshes and audits; it is not a count of unique cuts or pruned subtrees.
Most difficult-case dead ends still depend on parent exclusions rather than
the direct physical witnesses accepted by this first proof language.

This remains supplied-coordinate finite reconstruction. The materials are
cross-structure controls, not a verified common-condition ensemble. These
proof constraints are not newly trained m-values, richer learned anchor
domains, blind growth or a scientific materials advance. They provide a
safe foundation for investigating stronger, composable conflict explanations.

## Reproduction

```
node test-certified-dead-point.mjs KERNEL
node boron-face-reference-search.mjs PRECHECK_V2 CONNECTED_LEARNING KERNEL OUTPUT_FOLDER linear-nogoods
python verify-boron-face-search.py PRECHECK_V2 CONNECTED_LEARNING OUTPUT_FOLDER FILLING_CHECK
python verify-boron-dead-point.py OUTPUT_FOLDER CONNECTED_LEARNING PROOF_CHECK
```

Use new output paths. The immutable input is `precheck-v2.json`; the learning
artifact is `periodic-connected-c12-v1.json`. Source hashes in run artifacts
identify the research modules and unmodified kernel. Coordinates and derived
candidate point models remain local; public artifacts contain aggregate
outcomes, verification results and hashes.
