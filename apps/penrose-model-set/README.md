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

The live marked search now uses `assets/penrose-online-markings.js`.
Each search starts with empty partial point tables. For a geometry-admissible
pair, existing points are compared first. A disagreement rejects it without
a line query. Previously teacher-verified relative placements are reused, including rejections.
Otherwise, the precise continuous bar predicate supplies an exact verdict.
At each frontier decision the learner selects at most one geometrically
admissible rejected candidate whose rejection is not already explained by
points. It adds one witness pair, chosen among existing learned addresses and candidate-induced
boundary points and interval witnesses to minimize newly needed table entries.
The two prototiles receive values 1 and 0 at the corresponding local address,
closed under their decorated symmetries. Values transform by a permutation of
the five families, never sign negation. Undefined components are not zeros.

Only a rejection that the existing points cannot explain adds a lesson.
Bookkeeping alone caches verdicts without training: the initial seed has an
empty marking, and irrelevant hypothetical neighbors do not flood the stencil.
There is no offline enumeration in the live path and no union of independently
chosen covers over extent settings. The displayed point count is the sum of
distinct learned addresses over the prototiles; symmetry copies count.
This greedy choice does not promise a globally minimum stencil.

Learning persists across backtracking and corona continuation. Reset, changing
tile selection, or changing enforced extent creates a fresh learner. Tables
are shared by all placements of a prototile and are never tailored to a chosen
neighbor. The bar teacher remains necessary for unresolved pairs: this is
online learning with exact verification, not an unverified point-only solver.
Unmarked search continues to use its independent edge predicate and does not
train the learner. `learnMarkings:false` is available to headless comparisons
for the original continuous marked predicate, with no extra UI control.

The base graph still classifies every candidate exactly. Every admitted pair
has passed the teacher; subsequent learned constraints are consequences of
that same rule. Therefore they cannot invalidate already legal graph nodes
or nodes restored on rollback. The graph's spatial bounds cover the complete
extended-bar envelope from initialization, so newly learned points never
escape the indexed region. No graph rebuilding or loss of forced moves is
needed as the tables grow.

Extent 0–4 extends stripe guides by that multiple of their length. In marked
mode the dots and hover values are the actual learned supports. Candidate
inspection only compares these tables, does not query the teacher or train,
and keeps candidate values separate from the placed patch. In unmarked mode
the earlier geometric contact illustration is retained. Integer filtering,
showing bars, colors, line weight and highlighting only change the drawing.

Validation: `test-penrose-online-markings.mjs` compares all 8,012 geometric
neighbor pairs against the bar teacher before and after learning, verifies
point provenance and reuse, and compares full graph/search traces for P3,
P2, P1 and mixed tiles. The existing actual-worker test retains corona 3 and 5
checks. This guarantees the teacher remains in control of search correctness;
it does not prove infinite extendibility or standalone stencil completeness.

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

## Offline finite-point experiment

The generated finite tables and their generator are retained for research,
but the live demo uses a separate online learner supervised by the earlier
continuous bar predicate. The finite experiment preserved all edge-compatible pairs,
including corner-only pairs that can violate the stronger Ammann constraints.
It also accumulated separate covers across extent settings, producing more
points without recovering the old pruning. Its certificate concerns that
weaker pair classification; it does not certify equivalence to the live rule.
A replacement should seek a small stencil reproducing the working bar rule
and test it against actual compatible patches.
