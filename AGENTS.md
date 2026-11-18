
## Publishing preference

The user checks the 3D tiler on GitHub Pages. After changes to
`apps/3d-lattice-tiler` and its dependencies, publish to the existing GitHub
Pages site and verify the live update, unless the user explicitly asks for
local-only work. Preserve unrelated work when preparing the publication.

## Base GCTS tiling search

Use the same search policy for every GCTS tiling problem. At each node, build or
update the bipartite graph of frontier points and legal placements. Backtrack
at a point with no moves, and take forced moves before branching. When there
are no forced moves, pool the distinct placements adjacent to all frontier
points that first entered the current board at the earliest step. Shuffle this
pool uniformly and try each move at most once at that node. Restore point
introduction times when backtracking. Point age means placement order, not
geometric distance or corona generation.

Treat geometric markings as compatibility constraints that remove edges from
this graph. The base tree search, including forced moves and randomized oldest
frontier choices, is the same with or without markings. The A2 engine exposes
this as `branchPolicy: "oldest-frontier"`; use it for baseline comparisons.

## Materials research retirement

The materials reconstruction and atomistic-growth proof-of-concept lane was
retired at the user's request on 2026-10-31. Preserve the basic 3D lattice tiler,
its geometric catalogues, polyhedral tilings and related crystallography toy
models. Do not recreate retired materials datasets, models or reconstruction
experiments unless the user explicitly requests that work again.
