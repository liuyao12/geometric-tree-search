# Search with the lifted hat–turtle polygon

This app grows connected patches of a fixed fourteen-vertex polygon in a rank-four lattice. Every accepted placement must obey the exact point-capacity model in **both** the hat and turtle projections, and agree on the four-dimensional positions of every shared projected boundary vertex. It searches from one rooted tile; no substitution patch, precomputed tiling, learned marking, or preferred placement catalog is used.

A growth checkpoint is a **consistent finite patch with an open boundary**. It is not a certificate of an infinite tiling, and it does not fill four-dimensional volume. The object being built is a tiled surface in four-dimensional Euclidean space.

## Coordinates, transformations and the extra freedom

The integer coefficients represent two triangular planes, with Cartesian coordinates

\[
(p,q,r,s)\longmapsto\left(p+\frac q2,\frac{\sqrt3 q}{2},\frac{\sqrt3 r}{2},\frac r2+s\right).
\]

Thus the lattice is isomorphic to \(\mathbb Z^4\), with an oblique coefficient basis. Its Euclidean metric is not the ordinary orthonormal coefficient metric.

In their respective triangular bases, the endpoint projections are

\[
H(p,q,r,s)=(p+r-s,q+r+2s),
\qquad T(p,q,r,s)=(2p+q+r,-p+q+s).
\]

The basis vectors for the hat are \((1/2,0)\) and \((1/4,\sqrt3/4)\); for the turtle they are \((\sqrt3/4,1/4)\) and \((0,1/2)\). The differing planar bases explain why the coordinate formulas are not interchangeable.

The allowed linear transformations are the twelve simultaneous planar rotations/reflections of the two Cartesian coordinate planes. In coefficient coordinates the generators are

\[
\rho(p,q,r,s)=(-q,p+q,-s,r+s),
\qquad \sigma(p,q,r,s)=(p+q,-q,r,-r-s).
\]

Arbitrary integer translations are allowed in principle. For a fixed projected hat translation their full fiber is

\[
a+m k_1+n k_2,\qquad
k_1=(-1,-1,1,0),\quad k_2=(1,-2,0,1),\quad m,n\in\mathbb Z.
\]

Both kernel generators vanish under the hat projection, whereas

\[
T(k_1)=(-2,0),\qquad T(k_2)=(0,-2).
\]

Consequently, fixing both projected translations leaves at most one integer lift. Given desired hat coordinates \((x,y)\) and turtle coordinates \((z,w)\), that lift is

\[
r=\frac{2x+y-z}{2},\qquad s=\frac{-x+y-w}{2},\qquad
p=x-r+s,\qquad q=y-r-2s,
\]

provided all four quantities are integers. Fixing only the hat move leaves two independent integer translation parameters. For this lattice and these projections there is no additional linear rigid lattice symmetry inducing a fixed planar point symmetry, beyond the corresponding simultaneous rotation/reflection. General integer shears are excluded: they change the lifted polygon's Euclidean shape.

## Point model and physical faithfulness

The domain is a disjoint union of the two projected point domains. There are two kinds of samples in each projection:

1. Boundary vertices, with angle contributions in integer twelfths of a full turn. The target capacity is twelve.
2. Interior atomic samples, each with contribution twelve and target capacity twelve.

Every allowed polygon edge is along a triangular-grid line or a median line through lattice vertices. Divide every elementary triangular-grid triangle by its three medians, producing six small right triangles. The centroid of each small triangle is a discrete sample. Its barycentric coordinates, with respect to the containing elementary triangle, are a permutation of

\[
\left(\frac{11}{18},\frac5{18},\frac2{18}\right).
\]

All allowed boundaries are unions of edges of this common subdivision. Hence the interiors of these atomic triangles partition every allowed projected tile. Two tile interiors overlap with positive area exactly when they share at least one occupied atomic sample. Exact integer capacity comparisons therefore test nonoverlap without using a separate polygon-intersection predicate. Missing boundary coverage is tracked by the vertex-angle samples. The hat has 192 occupied atomic samples; the turtle has 240. The runtime stores sample coordinates with denominator eighteen, so all subsequent geometry, translations, sums and comparisons are integer.

The fixed vertex angles are recognized once from their thirty-degree direction classes and converted to integer units. Tests verify those units and the atomic subdivision for every orientation. No floating tolerance is used in search legality. Coordinates are well within JavaScript's exact integer range for the displayed tile limits.

## Markings and coherent surfaces

At each boundary vertex sample, the marking is its absolute four-dimensional integer coordinate. Overlapping assigned markings must agree, in each projection. The marking action includes the simultaneous rotation/reflection and the four-dimensional translation.

These are **problem-defining equality markings**. They define a connected coherent lift, rather than an arbitrary collection of independently translated tiles. The claim is not that all abstract two-projection packings must satisfy these markings.

The first tile is fixed at the origin, removing the global translation freedom. Every active frontier point is a partially filled boundary vertex with an already assigned lift. For each orientation and every local boundary vertex that can contribute to its deficit, align that local lift to the assigned four-dimensional point. This uniquely determines the candidate translation. Interior atomic samples have full contribution and cannot fit a positive frontier deficit. This is a complete finite candidate universe for the stated connected marked growth model. There is no finite box or arbitrary cutoff on hidden translations.

The resulting vertices can be written as a graph of two integer height coordinates over the hat position:

\[
(x,y)\longmapsto\bigl(x-r(x,y)+s(x,y),\ y-r(x,y)-2s(x,y),\ r(x,y),\ s(x,y)\bigr).
\]

The fixed twelve-triangle subdivision fills each non-planar tile. The validator proves, using integer quadratic inequalities, that these triangles have strictly consistent orientation throughout the hat–turtle parameter interval. A complete planar tiling with coherent shared vertices and this valid filled-tile subdivision lifts to a piecewise-flat embedded surface homeomorphic to the plane. Its vertices are lattice points; its continuous triangles are in Euclidean space. Finite patches can have holes or pinched boundaries. The app shows two different three-dimensional shadows, each retaining one of the two height coordinates. The shadows can overlap even when the four-dimensional surface does not.

## Conformance to the shared algorithm contract

Read [the master reference](../../../docs/basic-tiling-algorithm.md). This is a new point-value engine, rather than a modification of an older geometric search.

| Requirement | Implementation and verification |
| --- | --- |
| Exact point arithmetic | Integer capacities and denominator-eighteen sample numerators; integer four-coordinate equality markings. |
| Complete frontier/candidate graph | One shared candidate per orientation and four-translation; full orientation/positive boundary-support alignment at every active point. Forward domains and reverse candidate/frontier incidence are maintained. |
| All-support dependencies | A conservative spatial-chunk index includes every point of both projected supports, including interior atoms and assigned markings outside the active frontier. A changed chunk revalidates every cached candidate that might depend on it. Extra revalidation is allowed; missing dependencies are not. |
| Global scheduler | Scan all frontier domains for degree zero; otherwise use any degree-one domain; otherwise branch at minimum generation, breaking ties by domain size and a deterministic point key. Candidate ordering within that choice prefers filled obligations, then a reproducible random tie. |
| Generations | Root tile generation zero. Each new tile gets one plus the minimum generation on its already active support; point generation is the minimum incident placed-tile generation. |
| Rollback | Trail point totals, coordinate markings/reference counts, point generations, active domains and candidate validity. Restore every delta before a sibling. Cache geometry and conservative dependency indexes are branch-independent. Failed children remain local to their parent recursion frame. |
| Verification | Independent placement replay recomputes capacities, markings, duplicate placements and lifted edge incidence. Audit mode compares every incremental frontier domain to exhaustive re-enumeration. Root domains are additionally checked against independent whole-patch replay of every alignment. |
| Plug-ins | No learner, GCTS synthesis, RL, or external cluster proposals. The coordinate equality marking is part of the requested problem. |
| Stopping | A checkpoint first passes the global dead-domain scan. Node/stop limits and a safety limit of 30,000 cached candidates mean unknown, not untileable. A paused worker retains the actual search stack. |

The active obligations are the exposed vertices introduced by the connected growth. This demo does not implement an exhaustion of all untouched planar points, and makes no claim that its finite growth checkpoints establish an infinite tiling. Endpoint legality is checked throughout; intermediate pictures are visualizations of the fixed lift, not an additional global search constraint.

## Reproduction

Serve this directory over HTTP. No build or package installation is required. MathJax supplies mathematical typesetting. Search runs in a module worker.

Run the checks with Node.js:

```
node apps/hat-turtle-projection/lifted-search/validate.mjs
```

`validation.json` records an audited twenty-tile growth checkpoint, independent replay, exact translation-fiber identities, all orientation/atomic-support checks, the continuous triangulation orientation check, scheduler tests, rollback, and unknown-on-budget behavior. Browser checks cover start, pause/resume, both projected views, both height shadows, and export availability.

The fourteen base vertices were taken from the already published coherent lift in the parent app, generated from Craig Kaplan's BSD-licensed hatviz construction. This app uses that single tile's geometry, not the source patch's placements. See the parent app's provenance and license. The general lift is described by [Nan Ma and Arnaud Chéritat](https://www.math.univ-toulouse.fr/~cheritat/2023-monotile/4D-lift/index.html).
