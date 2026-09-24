# Cold search, minimal failure, and affine anchor constraints

The [interactive replay](nonacube-cold-learning.html) follows an unmarked branch, deletion tests, all subsets of the learned core, and the actual point/candidate graph. This is a new experiment, separate from the earlier three-tile surround example.

## Search and the meaning of viability

A tile is an exact point-weight function. This experiment uses half-unit integer coordinates: voxel centers have weight eight, each incident cube contributes one at a corner, and capacity is eight. Translations have even coordinates. The center constraints make capacity legality equivalent to nonoverlap of unit voxels. Corners supply the fractional frontier. Only the tile geometry and its lattice orientations are initial knowledge.

The active growth frontier consists of positive, unsaturated point totals. More generally, for a declared required set \(Q\), the frontier is

\[
F=\{p\in Q:T(p)<1\},\qquad T(p)=\sum_{c\in P}t_c(p).
\]

Explicitly required zero-total points must also be included in a finite-target search. A candidate is adjacent to a frontier point when its contribution there is positive and the placement is legal everywhere. Do not generally restrict candidate incidence to fractional contributions: a candidate with value one can fill a zero-total required point.

The driver checks the whole frontier for zero degree, then for degree one. A singleton is forced. Otherwise it chooses an oldest point and samples its incident candidates uniformly with a seeded PRNG. It records the actual choices, domains and birth numbers. Following the user's stated chronology, this experiment uses **chronological first activation**, not the master reference's growth-layer generation. The difference is explicit; it is not a reference-scheduler performance comparison.

The displayed branch uses seed two, chosen to illustrate a reduction rather than a branch already minimal. It reaches failure with fifteen tiles. No learned marking or bad-patch catalogue was an input. The driver stops at this first failure; it does not claim to have traversed the remaining search tree.

The minimizer tries deleting distant tiles first, rebuilds the complete graph, and propagates forced placements. A deletion is accepted only if failure is still proved. It repeats passes and then verifies every proper subset. A budget limit remains unknown. Ten deletions leave a face-connected core of five tiles, including three tiles in the same orientation. The final core has an immediate zero-degree point. All thirty-one proper subsets pass; every nonempty proper subset already has minimum frontier degree at least two, without forced moves.

This certifies inclusion minimality for **failure of frontier/forced propagation**. It does not certify one-round, two-round or corona viability of the proper subsets, nor minimum cardinality among all obstructions.

## Locality and proof scope

For an immediate dead point, enumerate every candidate that could contribute there. Capacity blockers can only come from tiles whose supports meet those candidates' supports. This gives an exact dependency neighborhood; distance is a deletion heuristic, not the justification for omitting tiles. If forced placements are involved, their reasons must be followed back through the implication chain, which can be longer-range.

The current certificate lists all one hundred and twenty candidate placements incident to the core's dead point, and a complete set of capacity violations for each. The independent verifier reconstructs the geometry and candidates, audits every visited prefix against the bipartite graph, checks every deletion and subset, and checks that the five tiles are face-connected. Face connectivity is a reported geometric property, not an extra legality filter in the search.

A learned exclusion retains the assumptions that made its gap obligatory. Under the demonstrated growth criterion, every exposed fractional point must remain viable. Under a different finite target, a point outside the required set need not be filled. The marking evaluator therefore exposes a required-point guard. More complicated failures would need their full assumptions retained, not merely an unqualified forbidden shape.

## Fixed sections cannot express the requested classification

Suppose each tile assigns a fixed value, or a wildcard, at each anchor. Any disagreement is witnessed by two non-wildcard assignments at one point. If every proper pair agrees, the full patch agrees. The argument is unaffected by vector dimension, anchor extent, or nonlinear choices made while training those fixed values.

The extension changes what an anchor specifies: it imposes an **affine constraint on an unknown shared section value**. This is not pairwise equality of already assigned sections. A wildcard supplies no equation.

For a forbidden patch with \(k\) roles, use shared coordinates \(z\in\mathbb R^k\) satisfying

\[
\sum_{i=1}^{k}z_i=1.
\]

Role \(i\) supplies the equation \(z_i=0\). All roles together are inconsistent. For any proper role set \(S\), choose \(j\notin S\); the vector \(e_j\) satisfies every supplied equation and the normalization. Thus every proper subset passes, including the empty subset. There is no nonlinear solver involved. The restricted evaluator implements this affine consistency test exactly by counting which coordinates have been forced to zero.

This is constructive synthesis: the failed geometry determines the anchor offsets, while the algebraic template supplies a guaranteed encoding. SAT is not necessary to establish representability. It could later reduce support, channels or dimension while preserving the required classifications and the geometric soundness argument.

## Anchor compilation, repeated orientations, and stabilizers

Let the learned placements have orientations \(o_i\), centers \(c_i\), and a certified dead point \(p\). For each lattice point-group element \(g\), create a channel. Place role \(i\)'s equation on orientation \(g o_i\) at offset

\[
a_{g,i}=g(p-c_i).
\]

At an arbitrary world point \(q\), the equation for role \(i\) in channel \(g\) can only be supplied by a tile centered at

\[
q-a_{g,i}=(q-gp)+gc_i.
\]

Since a contradiction requires all roles, its contributors reconstruct exactly a translated symmetry copy of the learned patch. Conversely, every such copy contributes all equations at its transformed dead point. No unrelated arrangement can trigger that channel. This argument still works when multiple roles have the same tile orientation: their distinct offsets identify distinct placements. The earlier prototype's distinct-orientation restriction is unnecessary for this construction.

For a lattice symmetry \(h\), anchors transform geometrically and channels transform by

\[
(g,i)\longmapsto(hg,i).
\]

In particular, for any tile stabilizer symmetry \(h\in H\), the resulting prototype constraint field is equivariant. For the flat nonacube, this includes its square symmetries and reflection in its plane. Values at symmetry-related arm anchors are tied through the channel permutation; they are not fitted independently. This uses a nontrivial action on the fiber. Requiring every channel to be an invariant scalar would be a stronger restriction than the construction uses.

There are forty-eight channels and five roles in this example, hence two hundred and forty prototype assignments. Unassigned point/channel entries are wildcards. The verifier audits the inverse-position argument and the full group action, including the stabilizer subgroup. It also tests all subsets under every point symmetry and two translations, with exact rollback after every insertion sequence.

Separate learned patterns can use separate channels, preserving the exact-pattern argument. Compressing or sharing channels requires a new soundness check; passing a finite set of positive examples alone would not establish it.

## What is implemented and what remains

The implemented cycle is unmarked branch → certified deletion tests → all-subset validation → affine anchor compilation → verification → replay of the failed decision. Of the four candidates at that final decision, the new marking rejects exactly the failed candidate. The runtime checks constraints at points; it does not query a SAT oracle or scan a list of forbidden patches.

This is not yet an online production learner. The current driver stops before backtracking; it does not update the production candidate graph with the new rule or search the remaining branches. A full integration must remove rejected candidate nodes from every incident frontier domain, revalidate the current prefix when a rule changes, and trail graph and marking state together. The current experiment makes no speedup claim.

Conformance with the [master algorithm contract](../basic-tiling-algorithm.md):

- Exact integer point values; complete oriented candidate alignments; capacity legality throughout each support.
- Shared `CoronaGraph` provides complete forward/reverse incidence, global dead/forced checks, and an existing rollback implementation. This verifier independently audits domains on every recorded search prefix.
- User-requested chronological-birth branching is explicitly a scheduling variant; it is not relabeled as reference growth-layer generation.
- No learned filter affects the unmarked labels. Negative evidence, graph-viable subsets, budget-unknown states and stronger extension claims are distinguished.
- The affine marking extension has declared anchors, fiber normalization, symmetry action, wildcard semantics, required-point guard and independently checked rollback.
- Production online activation, common graph/marking rollback, complete backtracking after learning, and time/branch benchmarks remain integration work.

Reproduce from the repository root:

```sh
node scripts/learn-nonacube-cold-patch.mjs 2
node scripts/verify-nonacube-cold-patch.mjs --receipt
```

Neither command needs a SAT solver. The receipt binds to the study file by SHA-256. The study includes the original branch, the ordered deletion tests, all subset labels and the blocked-candidate certificate.
