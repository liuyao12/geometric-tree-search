# Static complementary-support filter

This is proved necessary preprocessing for the declared finite half-weight
model, not a newly learned material marking. Each marking anchor is associated
with a required atom having exactly the same block incidence. The association
is checked from the point model, without atom-species or chemical rules.
With integer capacity two and unit contributions, a selected block needs a
second distinct-inventory block there. Both assignments must admit a common
marking value. Their sorted per-color coordinate signatures must consequently
be within twice the marking radius (plus a conservative numerical guard).

The filter removes unsupported endpoint choices, propagating when a block's
opposite endpoint becomes empty. It retains all surviving decorated choices
separately. The ordinary full-incidence, global-dead/forced, earliest-generation
search then runs on the filtered pool. Counts/forced moves may change because
of proved pruning, not because choices were projected onto geometry.

Soundness is by induction over the elimination list: a valid full filling
containing a removed endpoint would require a distinct-inventory partner that
survived all earlier removals and passes the necessary signature test. Such a
partner is absent, or the opposite endpoint already has no surviving choice.
Thus no valid full filling can use the removed endpoint.

The signature is deliberately a relaxation: different axes may use different
permutations. Surviving pairs need not admit a colored bijection or a common
marking value. The search still checks these conditions. No failure is carried
between configurations or treated as a physical law.

## Validation

- Independent NumPy brute-array replay (no producer KD tree) checks all 198,815
  endpoint removals across the four pilots.
- The one-cover and multi-cover training lifts remain available (one and two
  respectively). Developmental frames have no supplied lift.
- Exhaustive singleton-cloud controls: 100 models, 62,500 selections, all 58
  full solutions preserved after 1,151 endpoint removals.
- Filtered-run witnesses require the separate Python cloud-membership verifier;
  filtering alone does not certify a reconstruction.

| Library/frame | Original choices | Remaining choices | Preprocessing seconds |
| --- | ---: | ---: | ---: |
| One/train | 21,289,071 | 4,753,326 | 3.57 |
| One/dev | 12,640,506 | 4,934,012 | 3.34 |
| Multi/train | 41,672,906 | 15,417,706 | 6.25 |
| Multi/dev | 32,941,016 | 16,177,545 | 5.57 |

Times exclude file loading/serialization and independent audit. They are not
end-to-end speedup evidence. Guarded floating-point cloud semantics remain
approximate; integer occupancy totals are exact. These are finite registered
poses, not complete continuous-pose search or blind material growth.

Local artifacts use `/tmp/gcts-ice-{one,multi}-factorized-supported-v1.json`,
`...-factorized-support-proof-v1.json`, and `...-factorized-support-check-v1.json`.
