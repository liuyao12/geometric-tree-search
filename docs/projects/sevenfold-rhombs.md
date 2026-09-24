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

## Published Socolar marking

The current default is the nearest-neighbor arrow construction of Socolar
(1990), Section 5, Figure 4, pp. 610–611. It replaces the unsupported
experimental equal-neighbor ban originally added to this page. The unmarked
comparison remains available. Equal-shaped neighbors are allowed when their
particular orientations and edge decorations match.

Let \(e_m=\zeta_7^m\), with indices modulo \(7\). An edge parallel to \(e_m\)
carries three bits. For \(k\in\{1,2,3\}\), bit \(k\) specifies whether the
next tile of that shape on the left of \(e_m\) uses the other edge axis
\(m+k\) or \(m-k\). On the right the specified choice is reversed.
Socolar’s shape index refers to an angle \(2k\pi/7\); its correspondence to
our acute-angle indices is \(1\mapsto2,2\mapsto3,3\mapsto1\).

For a counterclockwise boundary edge directed as \(s e_m\), let \(n\) be
the other edge axis and \(k=\min((n-m)\bmod7,(m-n)\bmod7)\). Its own-shape
bit is fixed by \(s\operatorname{sgn}(n-m)\), using the representative of
\(n-m\) in \(\{-3,-2,-1,1,2,3\}\). Opposite edges flip this bit and
preserve the other two bits. Each of the two edge families has two free bits,
giving \(16\) states of a fixed oriented rhomb. Half-turn rotation pairs
these states: there are \(8\) decorated prototiles per shape, counting
reflected variants separately, hence \(24\) altogether. The complete
orientation catalog has \(336\) templates and \(1344\) anchored moves.

Bits are stored as an integer from \(0\) to \(7\) at the exact doubled
midpoint in an axis channel. Matching compares assigned values for equality.
For display, the first bit chooses the arrow direction along \(e_m\); after
complementing all bits for a reversed arrow, the other two bits choose one
of four arrow types. One to four arrowheads distinguish those types. This
is an equivalent relabeling of the arrows, not a transcription of the
particular graphical glyphs in Socolar’s Figure 4.

Rotation permutes the axis channels and complements all bits when the
canonical star direction reverses. Reflection permutes axes; its reversals
of left/right and of axis-index differences cancel, preserving the bit
vector relative to the reflected star direction. Translation preserves
labels. The full set is used: no phase-specific deletion from Section 6 is
imposed. These are published problem-defining labels, not learned data.

The induced row alternation condition has Socolar’s proved weak matching
property for the prime order \(7\). It bounds internal-space displacement,
excludes nonzero translational periods, and permits local flips. It does not
force every tiling to be locally isomorphic to a single canonical projection.
The theorem concerns infinite plane tilings, not arbitrary finite partial
patches or the floating-point implementation’s certification status.

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
- No RL, GCTS training, local impossibility certificates, or substitution
  oracle is implemented. The Socolar arrows are a known-rule control.
- Candidate ordering within the selected point favors filling existing
  corners, then a seeded deterministic hash. It does not exclude candidates.
  A bounded geometry cache shares results across decoration variants.
- Geometry tolerances remain a certification gap; reported patches are
  numerical geometric controls. The tests independently clip polygons to
  check intersection area, but that verifier is also numerical.

`tests/test_sevenfold_rhombs.mjs` checks coordinates, angles, inventories,
global scheduling, domain completeness, budget status, and exact restoration
of active placements, capacities and generations over backtracking. It also
checks the 336-template / 1344-move marked catalog, opposite-edge bit
transport, both acceptance and rejection of same-shaped neighbors, exact closure under
rotation/reflection, and all 24 decorated rotation classes.

`tests/socolar-multigrid.mjs` independently constructs a 446-tile dual of a
periodic seven-grid. It derives labels by union-find transport along rows,
rather than asking the production decorator for its labels. Every resulting
label tuple must occur in the production catalog. Independent polygon
clipping checks nonoverlap; replay checks capacities and matching. Direct
reading of 685 row chains checks alternation of the two other-axis choices.
These are finite implementation checks, not a new proof of Socolar’s theorem.
The original equal-neighbor benchmark numbers are obsolete for this rule.

## Literature

- Joshua E. Socolar, [Weak matching rules for quasicrystals](https://scholars.duke.edu/publication/656337),
  *Communications in Mathematical Physics* 129 (1990), 599–619.
  Sections 4–6 establish the theorem, construct nearest-neighbor arrows,
  and discuss the sevenfold example and local flips.
- Theo P. Schaad, [A Challenging 7-Fold Tiling Puzzle](https://arxiv.org/abs/2112.00625)
  (2021), a sevenfold rhomb substitution construction with three base shapes.
- Nicolas Bédaride and Thomas Fernique,
  [No Weak Local Rules for the 4p-Fold Tilings](https://arxiv.org/abs/1409.0215)
  (2015), for the distinction and boundary of undecorated weak local rules.
