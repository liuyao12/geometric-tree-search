# Geometrically Constrained Tree Search

**Geometrically Constrained Tree Search (GCTS)** is a working name for search problems where a
combinatorial object is built step by step under geometric constraints, and
where markings, macros, symmetries, or certificates can guide or prune the
search tree.

This repository publishes the GCTS notes and playgrounds as a static GitHub
Pages site. The main way to use it is to open the page in a browser:

- [Geometrically Constrained Tree Search](https://liuyao12.github.io/geometric-tree-search/)

## Browser Pages

- [Geometrically Constrained Tree Search I: Learning matching rules in tiling](https://liuyao12.github.io/geometric-tree-search/GCTS-I.html)
  The primary browser version of the essay, with margin notes and a sticky
  draggable/zoomable Turtle side app that shows t-values in units of 1/12, then advances from lattice, to tiling, to markings, to a learned-patch view as readers scroll.
- [3D Lattice Tiler](https://liuyao12.github.io/geometric-tree-search/apps/3d-lattice-tiler/)
  A browser playground for lattice polyhedra and polycubes on the integer
  lattice. It supports mixed tile systems, custom polycube construction, search
  tree inspection, and intermediate tiling snapshots.

## Big Picture

The primary article is maintained in this repository as the canonical browser
version of the essay.

The in-repository source for the primary article is
[GCTS-I.html](./GCTS-I.html), and a Markdown export of that post is included at
[docs/blog/tree-search-with-geometric-constraints.md](./docs/blog/tree-search-with-geometric-constraints.md).

## Local Development

The site does not require a build step. To preview changes locally from the
repository root:

```bash
python3 -m http.server 5174
```

Then open:

```text
http://127.0.0.1:5174/
```

or go directly to the local app preview:

```text
http://127.0.0.1:5174/apps/3d-lattice-tiler/
```

## Headless Runner

The 3D tiler can also run without the frontend UI. This is useful for baseline
runs, long searches, and comparing later GCTS heuristics against the current
engine.

```bash
node scripts/run-tiler-cli.mjs --figure letter_o::0 --target 80 \
  --output runs/letter-o-summary.json \
  --trace runs/letter-o-trace.ndjson
```

Useful options:

- `--list-figures` prints figure ids and names.
- `--criterion layer --target 4` switches from tile count to target layers.
- `--move-order repeat` tries same-orientation placements first.
- `--move-order periodic` prefers placements that continue a spacing already
  seen between same-orientation copies of the tile.
- `--move-order symmetric` prefers placements whose resulting frontier has more
  reflected pairs of exposed faces and a less lopsided bounding box.
- `--move-order layer` prioritizes moves that advance the earliest frontier
  layer; `balanced` combines that with same-orientation and periodic preference.
- `--face-order constrained` chooses the earliest-added frontier point with the
  fewest legal candidates before ordering that point's candidate moves.
- `--face-order pocket` chooses the earliest-added, heaviest frontier point
  first, which tends to fill tight spots before loose boundary growth.
- In 3D searches, legal candidate placements must attach along at least three
  non-collinear active frontier points; planar/2D systems use two by default.
- `--polycube-lattice d3` runs polycube systems on the D3 sampling lattice,
  adding face-center samples in addition to cube vertices; `z3` is the default.
- `--wall-time-ms 120000` stops gracefully after two minutes and still writes a
  best-effort JSON summary.
- `--trace` writes compact NDJSON events that can be inspected or summarized by
  scripts without rendering images.
- `--branch-details` adds candidate translations and heuristic scores to branch
  events in the trace.
- `--placement-details` adds the current placement translations and orientations
  to snapshots.

These are branch-ordering preferences, not pruning rules. Less symmetric or
less human-looking branches remain in the tree unless an explicit cap is set.

## Repository Shape

- `apps/`: interactive browser playgrounds.
- `scripts/`: local runners and analysis tools.
- `docs/blog/`: essays and long-form explanations.
- `docs/projects/`: project notes for individual GCTS examples.

The current repo is intentionally small. More experiments can move here once
they have a clear public-facing page, demo, or reproducible result.
