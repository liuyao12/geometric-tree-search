# Penrose tiling: point–candidate search

Published app: https://liuyao12.github.io/geometric-tree-search/penrose-model-set/.
Publish on GitHub Pages; do not create a local preview.

## Required baseline

All live P1, P2, P3 and mixed searches use the repository's
[basic tiling algorithm](../../docs/basic-tiling-algorithm.md).
`assets/tiling-frontier-graph.js` maintains shared candidate identities,
forward and reverse incidence, a conservative spatial dependency index,
and reversible deltas. `assets/penrose-point-search.js` supplies exact
Penrose predicates and the search driver. `createPenroseGrowth` and
`createMixedGrowth` both enter this engine.

At every decision the entire unfinished-point graph is checked for dead
points, then degree-one forced moves. Only when none remain does the search
branch at minimum degree, with generation and distance breaking ties.
Candidates enumerate all rigid decorated vertex alignments, including legal
point contacts. Unfinished interior pockets remain obligations rather than
being discarded by a single-outer-boundary restriction. Exact polygon overlap,
partial edge contacts and corner sums exceeding ten are rejected.

GCTS markings filter this same graph. No RL policy is enabled in the demo;
future policies must operate after propagation and within the legal domains.
The old edge-first P3 search is explicitly named `createLegacyPenroseGrowth`
and retained only for historical regression comparisons.

The UI reports graph point/candidate/incidence counts, forced placements and
branch decisions. “Proposals” now counts tile-placement attempts after graph
filtering; pruning counters include legality checks during graph updates.
The graph reports candidate checks and confirms that initialization builds
once, with local updates and rollback thereafter. These counts are not directly
comparable to historical edge-first proposal counts.

## Matching and tile selection

P3's unmarked rule independently compares single/double edge arrows in fixed
rigid orientations. Marked mode compares complete extended Ammann supports
without calling the arrow predicate. P1/P2/custom selections use complete
colored edge ports as their unmarked rule, on the same graph.

The picker has ten types: thick/thin rhombs; kite/dart; three decorated
pentagons, diamond, boat and star. Types are allowed, not required to appear.
Rotations and reflections are included. Every candidate carries fixed bars.

P1/P2 templates are transferred from a consistently decorated P3 patch through
the HBS construction in Porrier, *HBS Tilings extended*,
https://arxiv.org/html/2307.14011v2, sections 2–3. Regenerate them with
`node scripts/generate-penrose-mixed-templates.mjs`. Exactly six P1 and two P2
templates recur across 116 P1 and 70 P2 occurrences. Runtime reads only fixed
templates, never a target/reference tiling.

The shared construction scale is preserved: P3 edges 1, P2 edges 1 and φ,
P1 edges √(7−4φ). P1 cannot share a whole edge with P2/P3 at that scale.
Mixed selections are experiments; finite success does not prove infinite
extendibility or require every selected type to occur.

## Controls and exact support

Run suspends at frontier corona 3, then Continue resumes the same graph and
stack to 5, 7, etc. Tile generation is one plus the minimum incident generation
(seed 0); corona is the minimum generation at points with 0 < t < 1, as in the
turtle demo. A known dead point prevents a milestone pause. Forced propagation
continues after resuming. A 100,000-placement-attempt and 2,000-tile safety guard
remain internal. Candidate ordering uses fixed seed 17.

The marked search uses finite tables in `assets/penrose-finite-marking-data.js`.
Rows contain exact Q(zeta_5) coordinates, one of five components, a 0/1 value,
and an activation extent. Undefined components impose no constraint. Every
placement rigidly transforms its fixed table and permutes the five components;
rotations/reflections never negate values. Runtime hashes shared coordinates
and compares defined values only. It calls neither edge matching nor line
incidence to determine marking compatibility.

Generate tables with `node scripts/generate-penrose-finite-markings.mjs`.
The generator exhaustively enumerates 8,012 nonoverlapping whole-edge,
vertex-aligned pairs, including rejected placements and mixed tile sets.
Edge-port rules label 7,486 allowed and 526 forbidden pairs. The P3 labels
are independently checked against arrows. P1/P2 use the transferred edge
port decorations; mixed rules remain experimental.

Bar intersections and candidate-defined interval witnesses propose paired
positive/exclusion points. The generator groups points by the decorated tile's
symmetries, records support combinations that would reject an allowed pair,
and selects compatible witness pairs with a greedy cover and redundancy
removal. This is not a proof of minimum cardinality. Extent zero covers every
forbidden edge placement. Additional extents select alternative covers;
their union gives monotone support growth through all 17 quarter steps.
Every good pair remains compatible. Supports are fixed before search and
never inferred from the currently chosen neighbors.

The certificate is `docs/penrose-finite-marking-certificate.json`.
`test-penrose-finite-markings.mjs` independently checks all catalog pairs,
P3 arrows, point provenance, every extent's support monotonicity, symmetry
quotients, and matching marked/unmarked search traces at extent zero.
Preserving every edge-compatible corner pair is more conservative than the
previous continuous predicate and can substantially increase backtracking.
The worker regression checks corona 3 and continuation toward 5; set
`PENROSE_LONG_CORONA_TEST=1` for the optional full corona-5 performance run.

This certifies the finite neighbor catalog, not all distant placements or
infinite extendibility. Additional support can meet nonneighbors during search;
no universal correctness claim is made for those experimental interactions.

Extent 0–4 also draws the corresponding continuous bar guides. Only dots carry
runtime values. Hover shows exact coordinates, vertex t sums, and the actual
partial m tables, including interior zeros. Candidate inspection reports only
shared fixed support points; rejected candidate values are kept separate from
the placed patch. “Integer points” restricts the drawing, not search, to
Z[zeta_5]. Showing bars, colors, width, or point visibility never changes
legality. Changing extent restarts marked search; unmarked search is unchanged.

The integer-ring points on a physical line through two distinct ring points
are already dense. Their lifts form an affine rank-two lattice in a plane
inside the rank-four lattice. On the real axis, they are m+nφ, lifted in the
basis (1,ζ,ζ²,ζ³) to (m,0,−n,−n). A bounded interval contains infinitely many
such points, so membership in the integer ring alone cannot define a finite
display or finite marking support. A finite candidate-derived set is used here;
no cut-and-project window is added to the search.

## Verification

- `test-tiling-frontier-graph.mjs`: shared nodes, dead-point priority, undo.
- `test-penrose-frontier.mjs`: exhaustive fresh-domain comparisons, global
  forced/minimum-degree selection and exact graph restoration on real failures.
- `test-penrose-mixed.mjs`: P1/P2/mixed legality, exact concave geometry,
  capacities, integral vertices, matching and inspection.
- `test-penrose-growth-worker.mjs`: real worker transport and P3/P2 corona
  3→5 continuation without rebuilding the graph.
- `test-penrose-demo-controls.mjs`: presets, empty-selection recovery,
  display-only settings and status.
- Existing arrow/stripe/extension tests validate the fixed matching predicates;
  `test-penrose-growth.mjs` explicitly preserves the historical edge-first trace.

- `test-penrose-candidate-contacts.mjs`: exact contact provenance, interval witnesses, integer filtering and unchanged search state.
