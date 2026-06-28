# 3D Lattice Tiler

The 3D Lattice Tiler is the first public GCTS playground.

It is a standalone JavaScript port of the Observable notebook:

<https://observablehq.com/@liuyao12/3d-lattice-tiler>

Open the local app at:

```text
apps/3d-lattice-tiler/
```

The app is meant as an exploratory testbed for GCTS ideas:

- choose one or more lattice tiles;
- build custom polycubes directly in a small Minecraft-style editor;
- run a frontier-point/candidate graph tiling search;
- inspect search-tree rows and intermediate snapshots;
- compare tile-type counts in mixed systems.

The implementation keeps the search engine in `engine.js` and the browser UI in
`app.js`.
