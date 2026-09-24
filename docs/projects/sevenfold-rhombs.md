# Sevenfold rhomb search control

Added to both Penrose entry pages on 2026-09-23. Direct link:
[sevenfold tab](https://liuyao12.github.io/geometric-tree-search/apps/penrose-model-set/?ring=7).

## Mathematical scope

The unit-edge rhombs have acute angles \(k\pi/7\), for \(k\in\{1,2,3\}\).
Coordinates are exact safe integers in the independent basis
\(1,\zeta_7,\ldots,\zeta_7^5\), with
\(\zeta_7=e^{2\pi i/7}\) and \(1+\zeta_7+\cdots+\zeta_7^6=0\).
Directions are \((-\zeta_7^4)^j=e^{j\pi i/7}\).
Overflow throws rather than rounding. The point domain is the algebraic
module, which is dense in its physical embedding, not a discrete planar lattice.
The search activates only the finitely many exposed vertex obligations.

The corner support has integer weights \(k,7-k,k,7-k\), with capacity \(14\).
This is not a faithful polygon model by itself. The explicitly labeled
**geometric control** also checks convex polygon separation and rejects
vertex-on-edge-interior contacts. These predicates use floating point with
absolute tolerance \(10^{-9}\). No exact geometric certificate is claimed.

There are \(21\) geometrically distinct oriented templates and \(84\)
vertex-anchored moves when all three shapes are selected. The catalog covers
rotations by \(\pi/7\); reflections produce equivalent rhomb placements.
Identity includes the shape, exact support and its weights, and translation.
Templates are deduplicated only with the same point data. Selected shapes are
permitted, not required, and each placement can be used at most once.

## Optional problem-defining marking

The unmarked problem permits periodic tilings. The optional experimental rule
forbids two equal-shaped rhombs from sharing an edge. At each edge midpoint in
\(\tfrac12\mathbb{Z}[\zeta_7]\), a shape-and-unoriented-direction channel gets
value \(0\) or \(1\) according to lexicographic order of the directed boundary
edge's endpoints. Opposite boundary directions disagree. Different shapes
have undefined values in each other's channels. Missing is never zero.
Midpoints are represented by doubled integer coordinates.

Rotations permute direction channels and swap the two values when the
canonical direction reverses. Reflection additionally reverses the
counterclockwise boundary order. Markings are reconstructed from the oriented
boundary after transformation. Translations leave channel and value unchanged.
Marking supports lie inside each tile bounding box, so the shared spatial
dependency index covers both corner and marking contacts. Pairwise equality
checks implement agreement of the active global marking section; this is
fixed input, not learned data or an obstruction classifier.

The restriction is experimental: no claim of redundancy, infinite extension,
or aperiodicity. Exhaustion means failure of the selected restricted seeded
problem only. Budgets mean unknown. Reset discards the search; Continue keeps
its stack. Changing the selected shapes or rule resets the search.

## Contract evidence and gaps

- Uses the complete shared point–candidate graph. Every new frontier vertex
  enumerates every selected orientation and positive-support alignment.
- Selects from the graph using global dead ends, global forced moves, then
  earliest generation. Minimum degree only breaks generation ties. This
  adapter reads the graph directly and does not change existing Penrose
  scheduling or benchmark semantics.
- Seed generation is zero. Placement generation is one plus the minimum
  existing incident point generation. Point generation is the minimum
  incident tile generation. Both roll back with the branch.
- Uses incremental graph transactions, reverse incidence and spatial
  dependencies. Failed-child exclusions have parent scope and roll back.
  Audits compare legal domains against fresh exhaustive enumeration, allowing
  only explicitly tracked ancestor-context failed-child exclusions.
- Growth pauses after reaching a tile-count milestone with no known dead
  frontier point. It is a finite consistent patch, not an exact finite target
  solution or a proof of infinite extension. Untouched points are not fairly
  activated across the entire infinite module.
- No RL, GCTS training, local impossibility certificates, published sevenfold
  decoration, or substitution oracle is implemented in this control.
- Geometry tolerances remain a certification gap; reported patches are
  numerical geometric controls. The tests independently clip polygons to
  check intersection area, but that verifier is also numerical.

`tests/test_sevenfold_rhombs.mjs` verifies directions, the cyclotomic relation,
unit edges, angles, catalog size, marking conflicts and translation,
global scheduling, complete domains, coordinate/capacity replay, independent
polygon overlap checks, selected inventories, budget status, and exact
restoration of placements, totals and generations across 269 backtracks.
It checks both modes at 30 tiles. Browser verification additionally reached
80 unmarked tiles and 40 restricted tiles with seed 1; the latter required
1883 proposals and 1844 backtracks. These are observed finite results, not
performance or extendibility theorems. Browser checks cover both tabs,
Continue, Step, reset through rule changes, and mobile layout.

## Literature

- Joshua E. Socolar, [Weak matching rules for quasicrystals](https://scholars.duke.edu/publication/656337),
  *Communications in Mathematical Physics* 129 (1990), 599–619.
  Weak rules exist for rotational orders not divisible by four. This result
  does not establish the experimental equal-neighbor restriction above.
- Theo P. Schaad, [A Challenging 7-Fold Tiling Puzzle](https://arxiv.org/abs/2112.00625)
  (2021), a sevenfold rhomb substitution construction with three base shapes.
- Nicolas Bédaride and Thomas Fernique,
  [No Weak Local Rules for the 4p-Fold Tilings](https://arxiv.org/abs/1409.0215)
  (2015), for the distinction and boundary of undecorated weak local rules.
