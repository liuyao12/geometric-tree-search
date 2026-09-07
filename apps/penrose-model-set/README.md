# Penrose tiling: P1, P2, P3 and mixed selections

The tile picker exposes ten fixed decorated prototiles: two P3 rhombs, P2 kite
and dart, and P1's three pentagons, diamond, boat and star. Presets select a
family; individual checkboxes permit arbitrary subsets. Selected types are
allowed, not mandatory. P3 remains the default.

`penrose-mixed-growth.js` performs whole-edge DFS for custom selections, with
exact concave-polygon overlap, T-junction rejection, corner capacities and one
outer boundary. Its unmarked mode explicitly compares edge ports. Its marked
mode instead compares entire extended marking supports, including isolated
contacts and intervals through concave polygons; it never calls the edge-port
predicate. Each branch places a rigid decorated orientation. Both P3 tiles
selected alone retain the original independent arrow/CSP engine below.

The shared construction scale is deliberate. P3 edges have length 1, P2 edges
1 and φ, and P1 edges √(7−4φ). Thus P2/P3 may mix along full edges, while P1
cannot attach to P2/P3 under this engine's whole-edge convention. Resizing P1
independently would change the relationship between its markings and the
other sets. The picker states this limitation. A mixed finite patch is an
experiment, not a certification of infinite extendibility.

Templates are generated offline by `scripts/generate-penrose-mixed-templates.mjs`:
identify HBS cells through pentagon centers in the supplied exact P1 patch;
enumerate and consistently decorate their rhomb decompositions; derive P2
faces from thick diagonals and thin double-arrow edges; clip the resulting
Ammann lines to P1/P2 polygons. This reproduces exactly six P1 and two P2 rigid
templates, across 116 P1 and 70 P2 occurrences. Runtime imports only these
fixed templates, never the reference patch. See Porrier, *HBS Tilings
extended*, https://arxiv.org/html/2307.14011v2, sections 2–3.

`test-penrose-mixed.mjs` checks all templates, exact concave clipping, both
predicates on P1/P2/mixed growth, capacities, non-overlap, integral vertices,
corona bookkeeping and hover values. The marked 20-tile P2/P3 regression
contains all four kinds. Worker tests check P2 corona pauses and continuation
in addition to the original P3 tests. Controller tests cover presets,
individual selection, empty-selection recovery and display controls.

## Standard two-rhomb preset

## Corona milestones

The interactive demo uses frontier corona count instead of a tile target.
Run pauses at corona 3; the next Run continues the existing DFS/worker to 5,
then 7, and onward. It never reseeds or discards the stack at a milestone.
This uses the active turtle engine's criterion: seed generation 0, each new
tile's generation one plus the minimum incident generation, and corona equal
to the minimum generation at an unfinished vertex (0 < sum(t) < 1). Depths
are restored on rollback. Corona mode prioritizes the earliest frontier
generation, then physical distance. Merely reaching an outer tile is not
corona completion. The worker stops its batch at the milestone placement.

The UI exposes Run/Pause/Continue, Step, Reset and marking controls. A single
status shows ready, tiling, or “pausing at corona N”; there is no permanent
milestone reminder or playback selector. Worker batches remain bounded and
use a fixed automatic rate. Branch ordering
uses fixed seed 17 for repeatable comparisons; Continue does not reseed. A
100,000-proposal guard and 2,000-tile safety limit remain internal. Tile-count
mode remains an API option for regression comparisons. With seed 17 and extent
2, coronas 3 and 5 are reached at 77 and 208 tiles (317 and 2,003 cumulative
proposals). Historical tile-count timings below refer to the API mode.


Published app: <https://liuyao12.github.io/geometric-tree-search/penrose-model-set/>.
Use GitHub Pages for publication; no local preview.

One canvas and one worker run genuine DFS growth in ℤ[ζ₅]. With **Enforce
Ammann bars** off, `penrose-arrows.js` explicitly matches the type and direction
of standard single/double Penrose edge arrows. With it on, only the complete
Ammann rule with the selected extension is checked; the search never invokes the arrow
predicate. Both modes retain exact non-overlap, corner capacity and a single
outer boundary. There is no window oracle or precomputed target tiling.

The independent arrow template follows slide 17 of [Treibergs, Penrose
Tiling](https://www.math.utah.edu/~treiberg/PenroseSlides.pdf#page=17).
The thin template's acute starting corner is rotated 180° to align its state
index with the fixed Ammann template. Tests exhaust all 640 oriented local
adjacencies: 160 are accepted and 480 rejected by both predicates. This local
correspondence makes the extent-zero rules equivalent on finite patches.

The checkbox switches the predicate and restarts from the same seed. Run/Pause/Continue, Step and Reset control the search.
Show edge arrows / Show Ammann bars, direction highlighting, colors and line
weight only affect rendering. Highlighting 1 or 3 directions never weakens
enforcement: all five are always checked in Ammann mode. The growth API rejects
partial enforcement. The lower-level Ammann solver retains diagnostic partial
signatures for reference use.

**Extent** ranges from 0 to 4 in quarter steps (UI default 2). It extends each
stripe at both ends by that multiple of its own original length. The visible
extensions are dashed. Changing extent restarts marked search; in arrow mode
it changes only the illustration. For each direction, the marking is 1 on the
extended stripe and 0 elsewhere inside the tile, with undefined values outside
that component's support. Extension/tile overlap must agree, even between
tiles without a common edge. Crossing different directions does not conflict.
The constraints use exact rational cyclotomic predicates; conservative bounding
boxes skip distant pairs, and cached state-pair masks avoid repeated geometry.

Both modes reject arbitrary periodic rhomb tilings. Seed 17, target 60 uses
4,461 proposals and 607 backtracks at extent zero. With extent 2 it uses 221
proposals and no backtracking. This is a search-tree comparison, not a claim
of equal per-proposal cost or guaranteed runtime improvement. Worker compute
time excludes playback and drawing. Finite patches do not prove infinite
extendibility. Tests retain 240 window-certified reference tiles at extents
0.25, 2 and 4 and witness a conflict between non-edge-neighboring tiles.

Hover over dots to inspect exact coordinates and summed corner weights t(x).
The bar view includes intermediate points throughout stripes and extensions.
The Points selector chooses 4, 8 or 16 exact rational subdivisions per original
stripe length (default 8), without changing solver state. These are inspection
samples in ℚ(ζ₅), not all integer-ring points; whole-segment checks remain active. The five-component marking m is
sampled at the hovered point: 1 means on a bar, 0 means off the bar inside a
tile, and — means outside that component's support. Per-tile values must agree
where both are defined; they are not summed. Stored t support still consists
of vertices (weights / 10); other sample points have t = 0. Coordinates retain
exact rational denominators in ℚ(ζ₅).

`reference.html` preserves the window-certified P1/P2/P3 catalog.

Validation (Node, no local browser preview):

```sh
node scripts/test-penrose-extensions.mjs
node scripts/test-penrose-point-inspection.mjs
node scripts/test-penrose-arrows.mjs
node scripts/test-penrose-marking-settings.mjs
node scripts/test-penrose-demo-controls.mjs
node scripts/test-penrose-growth.mjs
node scripts/test-penrose-growth-worker.mjs
node scripts/test-penrose-ammann.mjs
```

The growth tests verify that Ammann mode makes zero arrow checks and arrow
mode makes zero Ammann checks. The controller uses a DOM/transport double;
the worker integration test loads the actual worker module.
