# Learning a minimal forbidden patch

The [interactive experiment](nonacube-patch-constraints.html) contains a certified three-cross obstruction, complete surrounds of each pair, and an isolated prototype of constraint-valued markings. It does not change the production GCTS learner or its fixed-value equality rule.

## Labeling criterion and certificate

For a fixed nonoverlapping core, a positive label means there exists a nonoverlapping collection of further crosses covering every cell in its complete face/edge/vertex halo. No extension requirement is imposed on the outermost tiles. A negative label means this finite completion is impossible. A timeout is unknown, never negative.

The enumerator fixes one horizontal cross at the origin and considers nonoverlapping pairs of neighbors. It screens for an uncovered root-halo cell with no possible cover, then asks a finite SAT oracle for a complete surround of each pair. It stops at the first triple with three positive pair witnesses. This is an immediate-dead-cell search within a rooted family, not a complete catalogue of obstructions or a traversal following the production GCTS scheduler.

The resulting placements are:

| Role | Plane | Center |
| --- | --- | --- |
| A | \(xy\) | \((0,0,0)\) |
| B | \(xz\) | \((-3,-1,-2)\) |
| C | \(yz\) | \((-1,-3,1)\) |

The required gap is \(p=(-1,-1,0)\). There are exactly \(27\) translated crosses covering that cell. Every one overlaps the fixed triple. The certificate lists every cover and its blocking roles. The verifier reconstructs the covers from the shape independently.

Each pair has a published complete-surround witness. These establish inclusion minimality: every proper subset has a surround. A singleton inherits a covering packing from a pair witness; unnecessary tiles can be discarded. This does not claim the triple is a globally smallest obstruction under every boundary convention.

## Why the marking rule needs an extension

A fixed marking assigns a value \(m_i(x)\) wherever tile \(i\) has marked support. Under equality matching, a contradiction means two assigned values differ at some point. That same contradiction already occurs in the corresponding pair. Consequently, if every pair passes, the full triple passes. Increasing vector dimension, support, or symmetry representation does not change this argument.

This limitation concerns direct marking compatibility. It does not prevent the existing frontier graph from detecting higher-order coverage failures. Indeed, that graph can already detect this example's uncovered cell.

The proposed extension gives each tile an admissible set \(F_i(x)\) for a shared section value. Compatibility at a point and channel means

\[
\bigcap_i F_i(x)\ne\varnothing.
\]

For this triple, synthesis tries finite sets of basis-vector values. It finds

\[
F_A=\{e_2,e_3\},\qquad F_B=\{e_1,e_3\},\qquad F_C=\{e_1,e_2\}.
\]

All proper intersections are nonempty; the full intersection is empty. Exhaustive independent verification excludes constructions using only one or two states. This is constraint satisfaction for a section whose value is not yet chosen, rather than equality between already assigned section values.

For an abstract obstruction with \(k\) roles, the same local construction is

\[
F_i=\{e_j:1\le j\le k,\ j\ne i\}.
\]

It rejects precisely the full role set. Compiling those roles onto indistinguishable geometric tiles without unintended matches is a separate requirement. The implemented compiler is restricted to this three-role case with distinct cross orientations. It does not assert that the same compiler handles arbitrary repeated-orientation patches.

## Geometric compilation and symmetry

Let role \(i\) have center \(c_i\) and orientation \(o_i\). For each signed permutation \(g\) of the coordinate axes, create a separate channel. On orientation \(g o_i\), place constraint \(F_i\) at prototype point

\[
g(p-c_i).
\]

There are \(48\) channels and \(144\) prototype assignments. A lattice point-group operation \(h\) permutes channels by \(g\mapsto hg\). Translations move the marked support. This realizes an equivariant constraint field on a trivial vector bundle with finite admissible basis-vector values in each channel.

The absence of unintended exclusions has an exact argument. In a fixed channel, each orientation has exactly one role-specific atom. An atom of role \(i\) can contribute at world point \(q\) only from a placement with center

\[
q-g(p-c_i)=(q-gp)+gc_i.
\]

An empty intersection requires all three roles. Their centers therefore reconstruct exactly a translated symmetry copy of the certified triple. Conversely, every such copy has an empty intersection at its transformed gap. Additional unrelated placements cannot produce a different rejection pattern. The verifier audits the finite prototype fields used by this argument, beyond its sampled translation checks.

Runtime maintains exclusion counts for each state at each point and channel. Inserting a tile increments the relevant counts; rollback removes precisely those contributions. A conflict occurs when every state is excluded. Runtime neither asks SAT nor scans a patch catalogue.

## Boundary scope and algorithm conformance

In an infinite tiling the gap must be covered. In a finite-corona task, an outer-boundary hole may be allowed. Apply this learned rule only when the transformed gap belongs to the current required-cell set. `ConstraintSection` exposes that guard, and the verifier tests both inactive and active cases. Guard updates must follow the search target and roll back with it in any future engine integration.

This experiment uses the master [algorithm contract](../basic-tiling-algorithm.md) as follows:

- Base geometry and positive witnesses use exact lattice occupancy, with no overlaps anywhere, including outside the required halo.
- Negative labels are proved by exhaustive covering candidates; positive labels have independently checked placements. Budget exhaustion remains unknown.
- The finite SAT oracle is a specialized labeling control, not a GCTS benchmark lane. Its branching order does not implement the master frontier scheduler.
- The proposed marking runtime has verified exact rollback and an explicit symmetry action. Its changed semantics are labeled, and no production lane uses it.
- Production frontier/candidate bookkeeping, global dead/forced propagation, generation ordering, candidate elimination and learning integration remain unchanged. This prototype has not yet supplied conformance evidence for those integration steps.
- The example establishes representability under the proposed rule. It provides no speedup measurement; the existing frontier graph already catches its immediate dead cell.

A next stage would enumerate deeper failed patches, minimize them by certified deletion tests, and retain every coverage or boundary assumption in each rule. Multiple rules require independent channels or another proved combination scheme. Synthesis must then be verified against all proper subsets and against geometric cross-talk, with setup and search costs reported separately.

## Reproduction

From the repository root, with `python-sat` installed:

```sh
python3 scripts/learn-nonacube-patch-constraints.py
node scripts/verify-nonacube-patch-constraints.mjs --receipt
```

The study file records the exact fixed placements, all blocked covers, all three pair witnesses, synthesis results and search scope. The independent verifier needs no SAT package. Its receipt binds to the study file's SHA-256 digest, checks every subset under all cubic symmetries and several translations, audits covariance and exact-pattern compilation, and checks rollback and the finite-boundary guard. The measured enumeration time may differ across reruns.
