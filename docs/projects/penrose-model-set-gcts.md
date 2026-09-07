# Penrose GCTS on the cyclotomic integer lattice

## Current design (September 2026)

The ambient search object is the ring of integers of the fifth cyclotomic
field, O_K = ℤ[ζ₅], with independent basis (1, ζ₅, ζ₅², ζ₅³). A vertex address
is four integers. The relation 1 + ζ₅ + ζ₅² + ζ₅³ + ζ₅⁴ = 0 reduces the
legacy five-coefficient representation to

\[
(a_0-a_4,a_1-a_4,a_2-a_4,a_3-a_4).
\]

The Minkowski embedding z ↦ (σ₁(z), σ₂(z)), with σ₁(ζ₅)=ζ₅ and
σ₂(ζ₅)=ζ₅², embeds this rank-four module as a lattice in ℂ² ≅ ℝ⁴.
Its projection into either individual complex plane is dense. Thus a bounded
physical disk alone does not bound lattice enumeration. The new P3 solver
avoids exhaustive enumeration: only unit-edge rhombs attached to the finite
frontier are proposed. The canvas draws σ₁, and the inset draws the actual
σ₂ coordinates of the placed vertices. Both views use the same fixed rotation.

For the Penrose model-set condition one also retains the residue
Σ aᵢ mod 5, which is invariant under changing the five-coordinate gauge.
This labels the finite cyclic component of internal space; it is not a fifth
independent integer coordinate. Inset colors identify these residue layers.
The inset displays samples, not an invented acceptance-window outline.

## GCTS growth and its oracle

`makeCyclotomicSearch` starts with one exact seed chosen from ten orientations.
At each exposed edge it constructs the incident rhombs by adding/subtracting
unit directions in ℤ[ζ₅]. It uses no precomputed target tiling or target atom
list. Placements and shared vertices have canonical four-coefficient keys.

Each proposed corner contributes its angle in 36° units. The GCTS capacity
bound is ten: thin rhombs contribute (4,1,4,1), thick rhombs (2,3,2,3).
A candidate exceeding a site's current capacity is rejected before placement.
Surviving candidates must pass an exact local de Bruijn pentagrid predicate:
compute the other three strip indices from its two generating indices using
rational arithmetic in ℚ(√5), then compare all five indices. This predicate
certifies that admitted rhombs belong to one Penrose tiling, supplying both
non-overlap and matching admissibility. Capacity alone does not force Penrose
aperiodicity or prevent every geometric overlap.

The search orders exposed edges from the centre outwards, records actual
proposals and rejections, and caches failed placements. Capacity failures are
monotone while this solver only adds tiles; window failures are state
independent at a fixed phase. The cache is discarded on every new run.
Changing to a solver that rolls back would require invalidating or
state-keying capacity failures. The current exact-window mode normally has
one admitted continuation per exposed edge and needs no recursive backtracks.
The UI reports zero rather than manufacturing speculative rollbacks.

Targets and proposal budgets are finite. A partial catalog may exhaust its
frontier without reaching the target; budget exhaustion is reported separately.
Reaching a target certifies a connected finite patch, not an infinite tiling
proof or a claim that the boundary has no holes. P1 retains its separate
frontier DFS. P2 and mixed P2/P3 catalogs retain the earlier bounded atom-cover
solver described below.

## Golden-port experiment

`penrose-golden-bars.js` augments each rhomb edge with two exact ports at

\[
t\in\{1-\varphi/2,\varphi/2\},\qquad
\varphi=-\zeta_5^2-\zeta_5^3.
\]

These ports belong to (1/2)ℤ[ζ₅]; tile vertices still belong to ℤ[ζ₅].
The implementation enumerates segments between different edges, keeps those
parallel to one of the five cyclotomic directions, and repeatedly removes any
segment lacking a same-line continuation across an interior edge. Parallelism
is tested exactly by a·conj(b) = conj(a)·b, using integer ring arithmetic.
No floating-point tolerance decides which bars survive.

For phase 173 and 120 tiles, this leaves 313 of 1,200 candidate segments,
508 supported interior endpoints, 118 boundary endpoints, and all five
families. Boundary endpoints are unresolved, not counted as successful joins.
The app draws these retained segments as solid colored lines. The optional
old midpoint-cochain experiment remains available as a diagnostic baseline.

This is **finite-patch golden-port propagation**, not yet an Ammann matching
rule rediscovery. In particular, it does not learn one transferable decoration
per marked prototile, show that the decoration rejects precisely the forbidden
contacts, or establish Fibonacci spacing and infinite continuation. Selection
uses the already window-certified patch. Multiple phases passing this geometric
audit are not a held-out transfer test of a fixed learned rule. Those are the
next research gates before replacing the window predicate by learned GCTS
markings. The five direction channels should not be confused with the rank-four
integer coordinate lattice.

## Arithmetic and validation

`cyclotomic-five.js` implements canonical rational ring coordinates,
multiplication modulo Φ₅, the star automorphism, residue layers, and golden
ports. Intermediate integer products use BigInt; conversion back to bounded
integer storage checks safe-integer range. Rational denominators are permitted
for centres and markings but excluded from integer residue-layer queries.
The existing exact ℚ(√5) machinery handles pentagrid floors and ordering.
Only the rendering embeddings use floating-point trigonometry.

Run `node scripts/test-penrose-cyclotomic.mjs` for ring identities, gauge
invariance, conjugate embeddings, golden-port reversal, deterministic growth,
empty/partial/budget-limited catalogs, and 600 rhombs across five phases checked
against independent bounded pentagrid enumeration. It also independently
checks matching endpoints for all retained interior golden segments. Run
`node scripts/test-penrose-exact.mjs` for the P1/P2/mixed-catalog regressions
and the historical midpoint learner.

The exact pentagrid construction follows N. G. de Bruijn, “Algebraic theory
of Penrose's non-periodic tilings of the plane. I, II” (1981):
<https://pure.tue.nl/ws/files/4344195/597566.pdf>.
For the relation between Ammann patterns and projection constructions, see
Boyle and Steinhardt, “Coxeter pairs, Ammann patterns, and Penrose-like tilings”:
<https://arxiv.org/abs/1608.08215>.

## Earlier catalog and midpoint experiments

The following records the retained P1/P2 paths and the original midpoint
learner; the current P3 lattice-growth path and golden-port audit are above.

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

P1 uses an online exact frontier search. A public-domain reference patch is
used offline only to recover the six prototile shapes, legal edge contacts, and
which of the ten unit-edge directions each edge follows. It is not used as the
target support. Runtime growth starts from one tile, generates candidates on
exposed edges, and creates a new cyclotomic vertex only when a placement needs
it. The reference data itself contains no SVG coordinates: its 435 vertices
are integer coefficient vectors in \(\mathbb Z[\zeta_5]\), and its 241 tiles
are lists of those exact vertex IDs.
The three congruent pentagons remain distinct matched types; interior P-5,
P-3, and P-2 instances are verified by their five, three, and two pentagon
neighbors respectively. Corner weights are derived from exact direction turns,
giving only \(1,3,4,\) and \(7\) units and a maximum completed-site total of ten.

Candidate collision tests, two-axis broad-phase bounds, segment intersections,
edge matching, and point-capacity checks are all exact integer computations in
\(\mathbb Q(\sqrt5)\). A successful bounded growth patch is required to have
one degree-two boundary cycle. Thus it has one open outside frontier and no
enclosed holes. No background support points are drawn in P1 mode.

Catalog selection is staged. The P1, P2, and P3 buttons replace the current
selection with their complete presets; individual tiles may then be removed or
added. No model is rebuilt until `Run selected set` is pressed. P1 grows on its
own dynamically created host, while P2/P3 mixing uses the common atomization
below; a common three-presentation atomization remains future work.

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
