# Live cyclotomic tiling atlas

Entry point: [the live atlas](https://liuyao12.github.io/geometric-tree-search/apps/penrose-model-set/atlas.html).

This is a gallery of known construction controls, separate from the GCTS
search experiments. It displays Penrose rhombs, kite-and-dart recutting,
Robinson triangle subdivision, a finite original Penrose reference,
Tübingen triangles, Ammann–Beenker, sevenfold rhombs and root-lattice
triangles, dodecagonal rhombs, and elevenfold rhombs.

## Construction and provenance

- Rhombs: multigrid duality. Each regular pairwise grid intersection selects
  a lattice square whose projection is a rhomb. Directions are powers of
  \(\zeta_m\) for odd \(m\), and of \(\zeta_{2m}\) for even \(m\).
  See [Lutfalla](https://drops.dagstuhl.de/entities/document/10.4230/OASIcs.AUTOMATA.2021.9).
- Penrose: the pentagrid offsets have sum zero. P3 arrows use the standard
  two rigid orientations per shape, with shared-edge consistency solved
  over the entire constructed patch. P2 uses long thick-rhomb diagonals
  and thin-rhomb double-arrow edges. Robinson triangles split thick rhombs
  along the long diagonal and thin rhombs along the short one. These two
  transformations preserve the selected phase and source patch.
- Tübingen and sevenfold triangles: project triangular Delaunay faces of
  \(A_4\) and \(A_6\) selected by the affine physical section. Nearest
  root-lattice points are computed by flooring coordinates and rounding
  up the largest fractional parts to make their sum zero. A triple tie
  across that cutoff gives three lattice vertices. This implements the
  Voronoi/Delaunay construction in
  [Egan’s notes](https://www.gregegan.net/APPLETS/12/deBruijnNotes.html).
  The [Tübingen reference](https://tilings.math.uni-bielefeld.de/substitution/tuebingen-triangle/)
  distinguishes the two outlines from four handed substitution types.
  This viewer colors the outlines only.
- P1: reuse the existing integer-coordinate reference data in
  `assets/penrose-p1-patch.js`, with its existing public-domain provenance.
  No new growth or substitution algorithm is claimed for this finite patch.

The dodecagonal example is a six-grid rhomb construction, not an
implementation of the Socolar square–hexagon–rhomb tile set. No substitution
or universal local matching rule is inferred from its coordinate ring.

## Controls

Reveal animates a computed finite patch. Moving the section recomputes it;
new tiles are highlighted during animation. Phase is retained when switching
presentations. Patch radius changes the size of the requested region. The
finite P1 reference disables phase and radius controls. Shape highlighting,
pan/zoom, source-rhomb overlays, tile inspection, and SVG export are available.
The second view plots a conjugate embedding of the selected vertices; for
higher-degree fields it is only one internal-plane projection.

## Algorithm-contract audit

This engine is explicitly a **specialized geometric construction control**,
not the point-value GCTS baseline. It has no frontier graph, branch scheduler,
rollback, learned marking, candidate elimination, or search benchmark.
The geometric polygons are the construction output, not a substitute
implementation of the normative point model.

Vertex addresses are integer vectors reduced modulo \(\Phi_n\).
Intersections, section selection, and canvas embedding use floating-point
arithmetic. Near-singular section crossings are rejected with a status
message, leaving the last regular patch visible. These checks do not turn
the visualization into an exact certificate of an infinite tiling.

The multigrid enumeration range is justified by bounding the difference
between the projected floor vector and \((m/2)q\). Root-lattice enumeration
uses the analogous bounded projection error and all coordinate triples.
The visible patch is selected by tile center; its boundary is jagged. P2
retains only complete recut faces and therefore has a smaller fringe.

## Validation

Run `node tests/test_cyclotomic_atlas.mjs`.

The checks cover ten constructions, three nonsingular phases for each
generated family, cyclotomic reduction, integer addresses, nonzero areas,
expected outline counts, manifold edge incidence, equal rhomb side lengths,
and 6,264 independent interior coverage probes. Root-lattice triangles also
have their nearest-lattice witnesses checked against the Voronoi inequalities.
Penrose shared arrows and area-preserving triangle subdivision are verified.
Phase changes must change a patch, and repeated inputs must reproduce it.

Browser validation covers selection of every construction, phase changes,
real animation, reveal/pause/replay, known arrows, source overlay, zoom/fit,
inspection, conjugate view, SVG download, MathJax, and a narrow mobile viewport.
SVG export contains the full colored polygon patch, not matching decorations.

Remaining limits: numerical section predicates; a finite P1 patch;
no new markings for higher orders; no automated MLD classification;
and no assertion that this is an exhaustive catalog of known tilings.
