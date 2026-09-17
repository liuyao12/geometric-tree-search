# Why atom-only scalar markings collapse in this learned support

This follow-up learns scalar m-values on the preceding variable-size t-support. It is not joint optimization of m-support locations, t and m. Proper rotations transform anchor positions; scalar values are invariant.

## Learning and independent check

Each of the 1,509 learned positive-support anchors initially has a free scalar. Whenever two transformed anchors meet at the same training atom, impose equality. Connected components of that equality graph receive distinct integer labels. The labels are gauge choices: their magnitude and ordering have no physical meaning. Assigned zero is a value, not an absent marking.

An independent checker reconstructs correspondences from the original periodic coordinates, learned positions and supplied poses. It does not read the learner's correspondence lists or union-find state. All 80 training frames and 22,080 atomic sites replay, yielding 9,168 distinct equality edges. Graph traversal confirms rank 1,504 and five free classes, with sizes 1,004, 502, 1, 1, 1. The two large classes contain the two opaque element labels separately. The singleton anchors have t = 1.

Corruption tests reject an observed class split, a code that merges distinguishable classes, and an omitted equality edge. Merging classes is still an agreement-compatible marking, but fails the specific claim of a maximally separating encoding; it is not an illegal tiling.

## Exact conditional redundancy certificate

For all 630,763 same-species anchor pairs (including self pairs) with t_i + t_j ≤ 1, the learned m-values agree. Thus any t-legal, species-preserving overlap already satisfies these markings. Unit-weight anchors cannot overlap another positive contribution. Since this model assigns m only on positive t-support, the markings eliminate **no additional candidates** under these assumptions.

The reason is structural, not optimizer failure. Any scalar solution of the same equalities is constant on each connected component. Adding scalar channels with the same invariant action repeats those equalities channel by channel. It cannot distinguish anchors already connected by an equality path.

This is **not** a no-go result for GCTS generally, the earlier Gaussian-field variants, nontrivial transformation actions, context-dependent decorations, nonzero m-tolerances, or learned off-atom/mark-only anchors. Those are different hypothesis spaces. In particular, approximate agreement along a chain does not force its endpoints to be equal; the component-rank argument uses exact m-equality. It is also not a proof that unobserved material connections are physically impossible.

## Evidence and next requirement

- [Learned values and equality graph](markings.json)
- [Independent source replay and redundancy certificate](check.json)
- [Learner](learn-support-equality-markings.py)
- [Verifier](verify-support-equality-markings.py)
- [Corruption tests](test-support-equality-markings.py)

The learner takes `learned-support support-check output`; the verifier takes `coordinates dictionary library learned-support markings output`. Large support/coordinate artifacts remain local; their hashes identify the exact inputs. All earlier training-cover biases and calibration failures remain.

The next representation must learn useful extended m-support and/or context-dependent markings rather than merely adding channels to this atom-only model. This result diagnoses that requirement; it does not claim to have implemented or validated the richer model.
