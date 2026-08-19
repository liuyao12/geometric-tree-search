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

The background comparison includes a branch-complete count-target lane. It
enumerates every legal exposed-face extension, does not mistake an
instantaneously stranded frontier vertex for a permanent obstruction, and
charges node limits only when a placement is actually applied. This lane is
the only generic search allowed to certify that no connected patch of the
requested size exists; bounded failures in the faster vertex-MRV lanes remain
inconclusive.

The four unresolved Blanco–Santos census candidates are useful stress tests.
After the completeness and accounting correction, all four reached balanced
rank-3 60-tile patches in 12/12 three-seed trials. Exact internal-period checks
rejected 148,471 candidate bases without finding a periodic quotient. Those
finite witnesses are stronger candidate evidence, not an aperiodicity proof.

The implementation keeps the search engine in `engine.js` and the browser UI in
`app.js`.
