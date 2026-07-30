# Point-capacity tiling on Delone and model sets

## The ambient object

The useful replacement for a lattice is not the whole cyclotomic field
\(\mathbb Q(\zeta_5)\), nor even the full planar cyclotomic module
\(\mathbb Z[\zeta_5]\). Their planar images are not discrete. For Penrose
tilings, use a regular model set (or a finite union of model sets)

\[
  \Lambda(W)=\{\pi(x):x\in L,\ \pi_{\mathrm{int}}(x)\in W\},
\]

where \(L\) is a lattice in a higher-dimensional physical/internal product,
\(\pi\) is one-to-one on \(L\), and the compact window \(W\) has nonempty
interior and negligible boundary. Then \(\Lambda(W)\) is a Delone set, a Meyer
set, and has finite local complexity.

De Bruijn's regular pentagrid is an equivalent concrete presentation for the
Penrose rhomb tiling used by the interactive app. Its vertices have coordinates
in a translate/scale of the cyclotomic module, while the pentagrid strip
indices carry the higher-dimensional lift.

## Weighted-patch formulation

Let \(\Lambda\subset\mathbb R^d\) be a Delone set of finite local complexity.
A prototile placement is represented by a finite weighted patch

\[
  f_T:\Lambda\longrightarrow \{0,\ldots,M\}
\]

with finite support: the points of \(\Lambda\) inside or on the boundary of the
placed tile. A family of placements is a tiling exactly when

\[
  \sum_T f_T(p)=M\qquad (p\in\Lambda)
\]

together with geometric non-overlap and any model-set or matching-rule
admissibility conditions. On a bounded search region, require equality at
interior sites and retain a deficit \(0\leq d(p)\leq M\) on the open frontier.

For Penrose rhombs, take \(M=10\) and measure corner angles in units of
\(36^\circ\). A thin rhomb contributes \(1\) or \(4\) at its corners; a thick
rhomb contributes \(2\) or \(3\). Thus a completed vertex star has total
\(360^\circ/36^\circ=10\).

## What replaces lattice translation

There is no transitive translation action on a general Delone set. The correct
local replacement is the patch groupoid (equivalently, translation classes of
pointed finite patches). A failure certificate is keyed by the canonical
translation class of a radius-\(r\) neighborhood around the failed site,
including:

- relative point coordinates or their exact algebraic lifts;
- current deficits \(d(p)\);
- tile/matching labels;
- internal-window or star-map data when it affects admissibility.

Finite local complexity guarantees only finitely many such local keys at each
fixed radius. This is the property needed for geometric memoization.

## First interactive experiment

`apps/penrose-model-set/` constructs a nonsingular pentagrid patch, dualizes
grid intersections into thin and thick rhombs, and replays a point-capacity
search trace.

After fixing the central tile, every Penrose vertex lies in a common translate
of the cyclotomic module:

\[
 \delta(T_0)+\mathbb Z[\zeta_5].
\]

This host is dense rather than Delone, so drawing a coefficient-height
exhaustion obscures the tiling. The canvas now shows only the smaller finite
support actually reachable by the active bounded patch:

\[
 S(T,R)=\{p:p\text{ is a vertex of an admitted }T\text{-tile in }R\}.
\]

The universal module remains the exact address space; it is no longer used as
background decoration. The active window oracle selects the relevant Delone
subset.

Speculative locally admissible branches are shown and rolled back; the accepted
completion is certified by the pentagrid window oracle.
This separates two layers that a general solver should keep distinct:

1. the universal point-capacity constraint on \(\Lambda\);
2. the host-specific admissibility oracle (a cut-and-project window here).

The next solver step is to enumerate all finite weighted patches admitted by a
chosen window, rather than using the canonical pentagrid completion as the
completion oracle.

### Exact arithmetic boundary

The combinatorial model contains no floating-point coordinates. A point is
stored as

\[
  x={1\over d}\sum_{j=0}^4 a_j\zeta_5^j,\qquad
  (a_0,\ldots,a_4,d)\in\mathbb Z^5\times\mathbb Z_{>0}.
\]

Tile corners, centers, host sites, edge ports, translations, keys, and
adjacency tests retain this representation. Pentagrid intersections require
floors and comparisons in \(\mathbb Q(\sqrt5)\); these are represented by
reduced triples \((a,b,d)\) for \((a+b\sqrt5)/d\) and compared using integer
arithmetic. Radius decisions use the exact squared cyclotomic norm. The single
lossy boundary is `exactToPoint`, called by the canvas renderer after all
tiling decisions have been made.

## Penrose catalog

The app exposes all three classical presentations:

- P3: thick and thin rhombs;
- P2: kite and dart;
- P1: three differently matched pentagons (P-5, P-3, P-2), star, boat, and
  diamond.

P1, P2, and P3 are mutually locally derivable, but their prototiles are not
freely interchangeable under the classical matching rules. P3 is generated
directly by the pentagrid. P2 is now a genuine exact local derivation: retain
the two oriented right edges of every thin rhomb and add the long diagonal of
every thick rhomb; the bounded four-edge faces of that graph are the kites and
darts. Their corner-capacity vectors are respectively permutations of
\((2,2,2,4)\) and \((1,2,1,6)\), and every completed vertex still sums to ten.

The P1 six-tile family remains visible as a disabled catalog reference until
its exact recomposition is implemented. Cross-family pseudo-mixing has been
removed rather than presenting recolored P3 atoms as if they were P2 or P1
tiles.

Catalog selection is staged. The P2 and P3 buttons replace the current
selection with the corresponding two-tile preset; individual implemented tiles
may then be removed or added across the two families. No model is rebuilt until
`Run selected set` is pressed.

Mixed P2/P3 search uses a common exact atomization rather than polygon
intersection tests. A thin P3 rhomb is one atom, a thick P3 rhomb is split into
two atoms along its long diagonal, each P2 dart is the union of two such atoms,
and each P2 kite is the union of one thin-rhomb atom and two thick half-rhombs.
Candidate placements are therefore compatible precisely when their finite atom
sets are disjoint. The live search is an exact-cover DFS over those atom IDs,
with the point-capacity bound checked before descent. A family preset chooses
the canonical target patch and candidate-order preference, but every selected
P2/P3 tile type remains available to the solver.

## First GCTS marking experiment

The P3 marking learner now uses seven independent regular-window patches as
positive data. Each oriented rhomb half-edge is described by tile kind,
orientation, physical edge family, traversal sign, and which endpoint is
acute. Legal shared edges impose equality constraints. Union-find learning
reduces the resulting 40 oriented half-edge types to exactly five classes.
Rotations act by the cyclic permutation of these five classes.

The same training patches provide a residual vertex-corona filter. After
forgetting the arrow/bar decoration, the learner sees seven cyclic vertex-star
types. This agrees with the fact that the decorated P3 atlas has an additional
distinction that is lost by the undecorated angle sequence.

This first marking passes every learned edge overlap and every rhomb cochain
closure check. It is not yet a full recovery of the classical single/double
arrow marking: the five classes primarily recover the five direction
cochains, while the residual vertex table carries additional local information.

For the Ammann-bar attempt, opposite equal-class edge ports are connected
inside each rhomb. The resulting strands meet continuously at shared edges,
but a strict straightness audit fails: midpoint support produces kinked
topological strands, not classical Ammann bars. The next marking model must
allow one- and two-port edge supports at the golden-ratio positions. This is a
useful negative result because continuity alone is weaker than straight Ammann
continuation.

### Where the bars live, and what is trained

An Ammann bar is not a subset of the Penrose vertex set. It crosses tile
interiors, and its endpoints on a tile boundary are normally interior points
of an edge. We therefore augment the vertex host by an exact edge-port support

\[
 \Lambda_{\rm mark}=\Lambda_{\rm vert}\ \cup\
 \{(1-t)v+tw:[v,w]\text{ is an admitted edge},\ t\in P\},
\]

where \(P\subset\mathbb Q(\sqrt5)\) is a finite, convention-dependent set of
port parameters. Representative golden positions include
\(\varphi/2=(1+\sqrt5)/4\) and
\(1-\varphi/2=(3-\sqrt5)/4\). These points remain exactly algebraic even when
they are not vertices.

The learner now materializes the parameter tensor

\[
 \theta[\text{tile kind},\text{orientation},\text{support port},\text{channel}]
 \in\mathbb R^{2\times10\times4\times5}.
\]

Only the entries of \(\theta\) are floating-point trainable values. Its indices
and geometric support are exact. The displayed midpoint experiment activates
40 of 400 dense slots; \(C_5\) equivariance and the learned half-edge
identifications tie many of them. Replacing the four midpoint half-edge slots
by a richer finite set of exact single/double golden ports does not change the
solver architecture.

### Criterion for rediscovery

A learned decoration counts as an Ammann-bar rediscovery only up to the natural
equivalences: permutation of the five channels, reversal of channel signs,
translation of height-function origins, and other coboundary/gauge changes.
Literal agreement of colors or arrow glyphs is irrelevant. The audit requires:

1. every legal shared edge has matching exact ports and channel labels;
2. the learned labels accept the same edge-adjacency language, rejecting
   geometrically attachable but classically forbidden pairs;
3. connected ports continue on exactly collinear algebraic lines, not merely
   visually close lines;
4. the five channels close around every tile and integrate to five consistent
   height functions;
5. the same results hold on held-out window phases and larger patches.

These conditions distinguish a genuine rediscovery from an easier surrogate.
The present midpoint marking passes rank, closure, continuity, and observed
legal-pair coverage. It fails exact straightness and empirical specificity:
all 80 opposite-sign, same-direction candidate pairs receive the same channel,
including 48 pairs not observed as legal. The app therefore labels it
**not yet Ammann-equivalent**, even though its colored strands look structured.

### Early-pruning comparison

The app fits on five exact window phases and replays one fixed, deterministic
candidate order at every shared-edge contact in two held-out phases. Three
filters see precisely the same proposals:

- point capacity alone;
- the rank-five direction channel alone;
- the sparse learned edge-compatibility tensor.

The benchmark counts a rejected proposal before descent as an early prune and
an accepted wrong proposal as a backtrack. It also counts false prunes of the
known legal continuation, which is the essential safety metric. In the current
deterministic run over 1,770 held-out contacts, capacity-only and rank-five
search each examine 7,176 proposals and incur 5,406 backtracks. The
compatibility tensor examines 3,147, incurs 1,377 backtracks, prunes 4,029
proposals before descent, and loses zero legal continuations. This is 43.9% of
the baseline node work, or a 2.28-fold reduction in examined proposals.

This is a boundary-contact microbenchmark, not yet a wall-clock claim for the
full tiler. Its purpose is to isolate exactly the mechanism requested: whether
the learned marking rejects bad branches before recursive geometric search.

The implementation follows the cochain viewpoint: matching data is stored as a
rank-five antisymmetric edge system, and bar continuity is tested separately
from cycle closure. See Pardo-Guerra, Washburn, and Allahyarov, “Matching Rules
as Cocycle Conditions: Discrete Potentials on Penrose and Canonical Projection
Tilings” (2026), <https://arxiv.org/abs/2603.13553>.

For the straight-line geometric viewpoint and the equivalence between
appropriate Ammann-bar continuity and edge matching, see “Ammann Bars for
Octagonal Tilings” (2022), <https://arxiv.org/abs/2205.13973>. The octagonal
paper uses Penrose bars as the motivating comparison; it does not by itself
specify the port convention used by this app.

## Reference

N. G. de Bruijn, “Algebraic theory of Penrose's non-periodic tilings of the
plane. I, II,” *Indagationes Mathematicae* 43 (1981), 39–66.
Publisher PDF: <https://pure.tue.nl/ws/files/4344195/597566.pdf>
