# Penrose tiling with and without marking

Published app: <https://liuyao12.github.io/geometric-tree-search/penrose-model-set/>.
Use GitHub Pages for previews and publication.

The default page runs two live DFS searches in independent workers. Both start
from the same thick rhomb in ℤ[ζ₅], use the same candidate-order seed, and check
exact non-overlap, corner capacity and a single simple outer boundary. Neither
lane uses a window oracle or a precomputed target tiling. Only the right lane
enforces the complete fixed Ammann markings.

Run both, pause, step, and reset use shared controls. Target, proposal budget
and shuffle seed restart both searches. Show stripes only changes the drawing;
it never changes enforcement. Pan and zoom are synchronized. Workers yield
bounded batches so the comparison shows genuine trials and rollback as work
is performed, rather than replaying a precomputed success trace.

Unmarked rhombs can tile in ways that are not Penrose tilings. Thus this is a
comparison of constraint enforcement, not an equal-solution speed benchmark.
With the default seed 17 and target 60, the unmarked lane takes 148 proposals;
the marked lane takes 4,461 proposals, including 725 marking prunes and 607
backtracks. The narrower solution space does not guarantee a faster search.
A bounded patch or a budget stop makes no claim about infinite tileability.

`reference.html` preserves the previous window-certified catalog and fixed
marking reference (P1/P2/P3), powered by the existing `app.js`.

Validation from the repository root:

```sh
node scripts/test-penrose-growth.mjs
node scripts/test-penrose-growth-worker.mjs
node scripts/test-penrose-ammann.mjs
node scripts/test-penrose-cyclotomic.mjs
node scripts/test-penrose-exact.mjs
```

See `../../docs/projects/penrose-model-set-gcts.md` for the mathematics and the
separate roles of the oracle-free comparison and window-certified reference.
