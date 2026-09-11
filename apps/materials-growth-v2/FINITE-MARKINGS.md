# Finite compatibility relations as point markings

## Status and intended contribution

This is an exact reference compiler for a **fixed finite candidate universe**.
It closes a verification gap between a relational exclusion predicate and the
point-value GCTS kernel. It is not a claim of a new general CSP encoding, an
efficient learned material model, or a continuous spatial marking field.
Production growth is unchanged. The compiler can serve as an oracle against
which a future compact, transferable marking learner is compared.

## Construction and equivalence

Let V be the frozen candidate set and E its declared unordered forbidden pairs.
Each candidate retains its original t-values, markings and activation list.
For every edge {a,b}, add a fresh auxiliary point p_ab outside the original
domain. Assign m_a(p_ab)=0 and m_b(p_ab)=1; all other candidates leave this
point unassigned. No t-value or activation is added at an auxiliary point.

**Proposition (finite encoding).** For every subset S of V, the augmented point
model is legal if and only if the original point model is legal and S contains
no pair in E. The same equivalence holds for exact coverage of an unchanged
declared target.

**Proof.** Selecting both endpoints of any forbidden edge assigns unequal
values at its witness point, so the marking test rejects. If S contains no
forbidden pair, each auxiliary witness receives at most one of its two values,
so it adds no conflict. Original t/m constraints and required points are
unchanged. These implications prove both partial and exact-target claims.

This elementary construction is presented as a reference implementation, not
as a novel mathematical theorem.

## Exact compression

Two reductions are implemented in the material study:

1. If an endpoint pair is already illegal under the original t/m model, its
   explicit exclusion is redundant in that fixed context and can be omitted.
   This is proved redundancy, not inference from a missing observation.
2. Group edges with a common endpoint a into a star. One witness carries 0 on
   a and 1 on each leaf. It creates exactly the star's edges, not conflicts
   among leaves. Greedy maximum-degree star grouping need not be optimal.

Each witness more generally represents a complete bipartite conflict relation.
The number of auxiliary points or assignments is a representation cost, not a
speedup certificate. The pairwise reference uses |E| points and 2|E| assignments.
There is no demonstrated bound on transferable motif-level marking complexity.

## Conformance record

- Domain: original finite point IDs disjoint from fresh auxiliary witness IDs.
  Original t arithmetic is retained; new m-values are exact binary scalars.
  Callers must pass target/fixed-mark point IDs absent from candidate supports
  through `reservedPoints`, so witnesses cannot collide with those external IDs.
- Transformations: candidate poses are already instantiated. Witnesses are
  candidate-conditioned, not material-coordinate fields. This does not implement
  a reusable SO(3)-equivariant section over an atomic motif.
- Frontier: original target and activation only. Auxiliary points are mark-only.
- Enumeration: complete for the explicitly supplied candidate list, not for all
  possible continuous poses or material continuations.
- Dependencies: auxiliary marks enter the existing full t/m dependency indexes.
  No private legality graph or modified scheduler is used.
- Scheduling and rollback: the existing kernel handles global certified dead
  ends, global certified forced moves, earliest-generation branching, and trails.
  Controls include unsatisfiable instances and failed branches.
- Rule scope: E defines the restricted model; it is not necessarily implied by
  the original unmarked problem. Removing base-implied edges is separately proved.
- Persistence: compiled libraries are immutable. New candidates or revised rules
  require recompilation and restart/replay. No live mutation protocol is supplied.
- Evidence: exhaustive subset equivalence for 16 ten-candidate controls and two
  twelve-candidate material-derived libraries; matched search traces for finite
  controls, including grouped witnesses. This is not a full production engine audit.
- Material limitation: the frozen libraries are selected to exercise exclusions,
  not randomly sampled or held out. Both directions of the geometric predicate
  are evaluated; their intersection defines the unordered relation. Directional
  disagreements must be disclosed rather than claiming equivalence to an
  order-dependent predicate.

## Why the ice diagnostic matters

At 220 atoms, all 14 absent reference sites in the declared evaluation sphere
already exist as active unfilled obligations. At 440 atoms, two remain and are
still pending. The finite-prefix coverage deficit therefore does not establish
missing connection information or justify adding constraints. It also does not
prove eventual completion. Evaluations must distinguish pending obligations,
unactivated required geometry and actual conflicts before attributing failures.

## Next scientific gate

Develop motif-local, rotation-aware markings that approximate or factor the
finite oracle across unseen placements. Measure false exclusions on independent
configurations and full pipeline cost. Do not interpret candidate-indexed binary
witnesses as learned physical potentials or as a demonstrated materials advance.
