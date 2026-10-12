# Shared algorithm contract

Before creating or modifying a tiling/search subproject, read
[docs/basic-tiling-algorithm.md](docs/basic-tiling-algorithm.md). It is the master
reference for current and future work, based on the Turtle demo in GCTS-I.html.

- Base tiles and markings are values at points. Exact tiling means t-values
  sum to 1 and overlapping assigned m-values agree.
- Maintain complete frontier-point/candidate bipartite bookkeeping.
- Check global dead ends, propagate global forced moves, then branch at the
  earliest generation. Minimum candidate count may only break generation ties.
- GCTS markings eliminate candidates through that graph. RL primarily proposes
  validated clusters, without restricting proposals to known tiling strategies.
- Preserve exact rollback and distinguish proved pruning from learned hypotheses.
- Record conformance evidence and gaps for the engine being changed. Existing
  code is not evidence that a conflicting rule is permitted. Specialized or
  geometric controls must be labeled, and their benchmark semantics preserved.

Consult the master reference for full point-domain, generation, plug-in,
verification, and result-reporting requirements.

## Publishing preference

The user checks the 3D tiler on GitHub Pages. After changes to
`apps/3d-lattice-tiler` and its dependencies, publish to the existing GitHub
Pages site and verify the live update, unless the user explicitly asks for
local-only work. Preserve unrelated work when preparing the publication.
