# Geometric Tree Search

**Geometric Tree Search (GTS)** is a working name for search problems where a
combinatorial object is built step by step under geometric constraints, and
where markings, macros, symmetries, or certificates can guide or prune the
search tree.

This repository is the public home for GTS experiments and playgrounds. The
first playground is a standalone JavaScript 3D lattice tiler, ported from an
Observable notebook and extended into a faster interactive tool.

## Playground

- [3D Lattice Tiler](./apps/3d-lattice-tiler/)  
  A browser playground for lattice polyhedra and polycubes on the integer
  lattice. It supports mixed tile systems, custom polycube construction, search
  tree inspection, and intermediate tiling snapshots.

## Big Picture

The project is motivated by the Observable essay:

- [Tree Search with Geometric Constraints I: Learning matching rules in tiling](https://observablehq.com/@liuyao12/tree-search-with-geometric-constraints)

A Markdown export of that post is included at
[docs/blog/tree-search-with-geometric-constraints.md](./docs/blog/tree-search-with-geometric-constraints.md).

## Run Locally

From the repository root:

```bash
python3 -m http.server 5174
```

Then open:

```text
http://127.0.0.1:5174/
```

or go directly to:

```text
http://127.0.0.1:5174/apps/3d-lattice-tiler/
```

## Repository Shape

- `apps/`: interactive browser playgrounds.
- `docs/blog/`: essays and long-form explanations.
- `docs/projects/`: project notes for individual GTS examples.

The current repo is intentionally small. More experiments can move here once
they have a clear public-facing page, demo, or reproducible result.
