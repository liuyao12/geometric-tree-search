# Next experiment: factorized endpoint unions in reference search

The coupled raw-cloud pilot remains unresolved for both one-cover and multi-cover
libraries on c01500/c01900 at 30 seconds. Do not infer factorized search performance
from these runs: their markings still require training-observed endpoint pairs.

## Proposed declared model, not an implemented result

A geometric base placement carries, at each endpoint, the union of the colored
cloud balls observed for that endpoint of its base motif. One proper placement
rotation acts on every possible value. The two endpoints are independent choices.
This is a factorized learned hypothesis, not a redundant constraint for the
coupled model. Coordinates/configuration IDs must not become marking values.

The explicit comparator enumerates the Cartesian product of endpoint choices,
with one shared inventory identity for each geometric placement. The implicit
model would retain one candidate per geometric placement and defer the endpoint
value choice. Its certificate must establish equivalence of *projected geometric
solutions*, not identity of decorated candidate graphs or forced-move counts.
Keep an explicit reference lane; label any projected scheduling semantics. The
master contract forbids silently deduplicating different m-values.

For the current half-weight model only, each marked endpoint coincides with a
whole positive-support component, so at most two placements may mark it. This
must be validated, not assumed for arbitrary models. Two colored-cloud balls
intersect if a color-preserving bijection places every pair of centers within
twice the radius: the matched midpoints witness the intersection. For unions,
one pair of constituent balls suffices. More than two assignments requires a
genuine common-value solver, not pairwise compatibility chaining. Numerical
membership guards must be accounted for conservatively; proposal failure is
unknown, never a pruning certificate.

## Gates before material claims

1. Compare tiny explicit Cartesian-product models and the proposed implicit
   representation, including shared inventory, rotations, rollback and common
   cloud witnesses. State clearly whether candidate-graph/scheduler semantics
   are changed by projection; do not call projected moves reference forced moves.
2. If projection changes semantics, prefer an exact compact representation of
   decorated candidate domains, with certified cardinalities/zero/singleton
   queries, so the original reference decision order remains meaningful.
3. Independently verify any compiled finite candidate universe and training
   lifts; do not consult training-selected covers in the solver.
4. Verify every terminal t total and common m witness, and report connectedness.
5. Test the same one-cover/multi-cover libraries, then more configurations. No
   continuous-pose completeness, specificity or blind-growth claim follows from
   finite known-position reconstruction alone.
