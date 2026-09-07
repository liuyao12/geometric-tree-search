# Penrose tiling: edge arrows and Ammann bars

Published app: <https://liuyao12.github.io/geometric-tree-search/penrose-model-set/>.
Use GitHub Pages for publication; no local preview.

One canvas and one worker run genuine DFS growth in ℤ[ζ₅]. With **Enforce
Ammann bars** off, `penrose-arrows.js` explicitly matches the type and direction
of standard single/double Penrose edge arrows. With it on, only the complete
Ammann port/direction rule is checked; the search never invokes the arrow
predicate. Both modes retain exact non-overlap, corner capacity and a single
outer boundary. There is no window oracle or precomputed target tiling.

The independent arrow template follows slide 17 of [Treibergs, Penrose
Tiling](https://www.math.utah.edu/~treiberg/PenroseSlides.pdf#page=17).
The thin template's acute starting corner is rotated 180° to align its state
index with the fixed Ammann template. Tests exhaust all 640 oriented local
adjacencies: 160 are accepted and 480 rejected by both predicates. This local
correspondence makes the complete rules equivalent on finite patches.

The checkbox switches the predicate and restarts from the same seed. Seed,
target and budget also restart. Start/Pause, Step and Reset control playback.
Show edge arrows / Show Ammann bars, direction highlighting, colors and line
weight only affect rendering. Highlighting 1 or 3 directions never weakens
enforcement: all five are always checked in Ammann mode. The growth API rejects
partial enforcement. The lower-level Ammann solver retains diagnostic partial
signatures for reference use.

Both modes now reject arbitrary periodic rhomb tilings. Seed 17, target 60
uses 4,461 proposals and 607 backtracks in each mode, with 725 rejections by
the selected matching predicate. Worker compute time excludes playback and
rendering; equivalent search paths need not have equal compute cost. A finite
patch or budget stop does not prove infinite extendibility.

`reference.html` preserves the window-certified P1/P2/P3 catalog.

Validation (Node, no local browser preview):

```sh
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
