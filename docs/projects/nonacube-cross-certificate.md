# Reduction from lattice surrounds to a finite Boolean formula

## Exact model and theorem

A voxel with coordinate $v\in\mathbb Z^3$ denotes $v+[0,1]^3$.
Distinct voxel interiors are disjoint. Tiles have the nine-voxel support $P$
given on the [result page](nonacube-cross.html). Allowed copies use integer translations and the proper
cubic rotation group. Its action gives exactly three distinct centered
supports, in the coordinate planes. Reflections add no supports for this
particular tile.

For a finite set of voxels $A$, define its closed contact neighborhood

$$
N(A)=A+\{-1,0,1\}^3.
$$

Covering $N(A)$ fills every exterior voxel meeting $A$ at a face, edge or
vertex. For this integer-grid model, it puts the geometric union of $A$
inside the interior of the covered union. Face-neighbor coverage alone would
not suffice. Our finite surrounds need not have topological-ball unions.

Fix a root $R=P$. A complete first corona consists of disjoint allowed copies,
each meeting $N(R)\setminus R$, whose union with $R$ covers $N(R)$.
A two-corona patch additionally covers the contact neighborhood of every
selected tile meeting the root, with disjoint allowed copies. Outer copies
have no further surround requirement. Equivalently, layers are defined by
tile contact distance from the root, and every tile at distance less than
two is fully surrounded. Unneeded outer copies may be discarded.

**Theorem in this model.** There is a complete first corona and there is no
two-corona patch. Consequently $H_{\mathrm{lat},26}(P)=1$ and there is no
tiling of $\mathbb Z^3$ by allowed copies of $P$.

## Finite placement universe

For a voxel target $A$, let $C(A)$ be all allowed placements disjoint from
$R$ that contain at least one voxel of $A$. This is finite and exactly
enumerable: for each target voxel $q$ and each voxel $v$ of each orientation,
the only translation placing $v$ at $q$ is $q-v$.

Set

$$
Q=N(R)\setminus R,\qquad F=C(Q),
$$

$$
D_s=N(s)\setminus(R\cup s)\quad(s\in F),
\qquad T=Q\cup\bigcup_{s\in F}D_s,\qquad U=C(T).
$$

Here $s$ also denotes its occupied voxel set. There are 90 voxels in $Q$,
686 placements in $F$, and 8,140 placements in $U$. In particular, $F$ is a
subset of $U$; no previously chosen first corona is fixed. All potentially
selected first coronas vary in the formula.

The verifier independently scans every possible center in a rigorously
bounded box: in each coordinate, a placement intersecting $T$ has center
between the minimum target coordinate minus the maximum orientation
coordinate and the maximum target coordinate minus the minimum orientation
coordinate. It compares this inventory with the support-alignment generator.
This is an implementation cross-check; the finite-completeness argument above
is the mathematical justification.

## Boolean constraints

There is one Boolean variable $x_s$ for each $s\in U$, meaning select that
placement. Define $I(q)=\{s\in U:q\in s\}$. The clauses are:

1. For every pair of distinct intersecting placements $s,t\in U$,
   $\neg x_s\lor\neg x_t$. Intersections at **all occupied voxels** count,
   including voxels outside $T$. There are 509,064 distinct pairs.
2. For every $q\in Q$, $\bigvee_{s\in I(q)}x_s$.
3. For every $s\in F$ and $q\in D_s$,
   $\neg x_s\lor\bigvee_{t\in I(q)}x_t$.

The full formula has 569,020 clauses. There are no auxiliary variables,
symmetry-breaking clauses, arbitrary bounding-box walls, learned markings,
or preselected first-layer tiles in the input formula. The outer layer is
free to have exposed boundary and does not have to extend infinitely.
Input variable numbering and clause order are deterministic; the manifest
identifies the exact DIMACS bytes consumed by the proof checkers.

## Why UNSAT gives an upper bound

Suppose a two-corona patch exists. Its tiles covering $Q$ belong to $F$ and
therefore to $U$. Every voxel in $D_s$ around any such selected tile must be
covered by some patch tile. That tile intersects $T$, avoids the root, and
thus belongs to $U$. Select the patch's placements belonging to $U$ and
discard any irrelevant others. Pairwise disjointness satisfies the first
clause family; coverage of $Q$ satisfies the second; surrounding every
selected root neighbor satisfies the third. Thus a genuine patch gives a
satisfying assignment.

Conversely, a satisfying assignment gives disjoint copies surrounding the
root and every selected root neighbor. Any selected outer copy unnecessary
for that coverage can be discarded. The result is a two-corona patch under
the definition above. Only the forward implication is needed for the UNSAT
upper bound.

An infinite integer-grid tiling would supply such a finite patch: normalize
one tile as the root, retain all tiles meeting it, then all tiles needed to
surround those finitely many neighbors. All remain among the finite candidates
just enumerated. Consequently UNSAT rules out infinite tilings, including
aperiodic ones. Any patch with more complete coronas would also contain a
two-corona patch.

## Lower bound and computational proof

The positive artifact lists the root and 34 disjoint allowed copies. The
verifier checks each shape using proper cubic rotations, checks every voxel
for overlap, checks every copy meets the root, and checks all 90 required
voxels are occupied. This proves the lower bound independently of the solver
that originally found the witness. No minimum-number-of-surrounding-copies
claim is made.

The upper-bound artifact is a DRUP refutation, which is a restricted DRAT
proof. DRAT-trim checks it against the regenerated formula and produces LRAT
hints. The separate, formally verified `cake_lpr` checker validates those hints against the same formula.
The LRAT consumer needs neither the original SAT search nor confidence in
the hint generator. Both tools must report success with successful exit status.

This remains a computer-assisted theorem with a trusted boundary: the stated
geometric reduction, its implementation, the runtime/toolchain and the
connection from the bundled checker artifact to its upstream verification.
`cake_lpr` is verified using HOL4 and CakeML and distributed as generated
assembly plus a C runtime. We pin that upstream artifact and build it locally;
we do not rerun its entire HOL4/CakeML proof and compiler pipeline here.
Formal verification of the Boolean checker does not by itself formalize the
geometric reduction. See [verification package](../../data/nonacube-cross-certificate/VERIFY.md) for versions and controls.

## Relationship to GCTS

This is a specialized finite SAT benchmark. Unit voxel occupancy is an exact
point-value model; the full point/candidate incidence and all exterior overlap
dependencies are enumerated. The public input contains no extra pruning
assumptions. Proof additions justify the search's learned restrictions in
this rooted context.

The original proof came from a Glucose hybrid with compiled anchor constraints.
Its branching/restarts/backjumps are SAT scheduling, not GCTS's reference
earliest-generation scheduler. This package certifies the result without
requiring that solver or asserting a GCTS speedup, compact marking theorem,
or sound transfer of learned rules to arbitrary roots. Those are distinct
research questions.
