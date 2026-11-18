
## Publishing preference

The user checks the 3D tiler on GitHub Pages. After changes to
`apps/3d-lattice-tiler` and its dependencies, publish to the existing GitHub
Pages site and verify the live update, unless the user explicitly asks for
local-only work. Preserve unrelated work when preparing the publication.

## Base GCTS search across projects

Use point-value incidence as the base GCTS model. Frontier points connect to
complete legal placement domains wherever the placement contributes a positive
point value. Markings remove incompatible incidences. The search rule is the same
with and without markings.

At each node, detect dead points globally, then exhaust forced moves globally.
Pool distinct moves adjacent to the frontier points with the earliest
chronological introduction step. Within that age group, prefer moves adjacent
to the last placement, meaning that their positive point supports intersect.
Choose randomly among equally preferred moves. After the first draw, fix one
incident frontier point and keep all of its legal moves as sibling alternatives,
including moves outside the adjacency preference. Preserve their randomized
order and restore point ages, domains, and branch state on rollback. Fixed finite
target obligations start at step zero. Geometric corona layers and spatial
distance do not determine point age.

Use `assets/gcts-point-branching.js` when working in the geometric-tree-search
repository. The A2 engine defaults to `branchPolicy: "oldest-frontier"` and
`requireEdgeSharing: false`. The Hat/Turtle demo in `GCTS-I.html` explicitly
enables shared-boundary-segment incidence and fixes a shared segment for sibling
alternatives. Its adjacency preference uses shared boundary segments. Keep this
polygon specialization out of the general point-value baseline. Other scheduling
policies must be named experimental controls. Preserve the original descriptions
and results of historical experiments.

## Materials research retirement

The materials reconstruction and atomistic-growth proof-of-concept lane was
retired at the user's request on 2026-10-31. Preserve the basic 3D lattice tiler,
its geometric catalogues, polyhedral tilings and related crystallography toy
models. Do not recreate retired materials datasets, models or reconstruction
experiments unless the user explicitly requests that work again.
