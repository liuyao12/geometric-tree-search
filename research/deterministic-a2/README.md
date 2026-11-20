# Deterministic GCTS with certified online markings

This reference program takes one finite point-valued tile in $A_2$, starts with every marking component unassigned, and learns during search. The input supplies exact rational weights, translations are by lattice vectors, and all twelve lattice orientations are allowed. It imports the base point-incidence branch selector used in GCTS. It has no precomputed Hat exclusions or training data.

## Run

From this directory, with Node.js:

```sh
node run.mjs two-weights.json > result.jsonl
node verify.mjs two-weights.json result.jsonl
node test.mjs
```

A tile file supplies a positive common denominator in `capacity` and rows `[x,y,numerator]` in `points`. The third lattice coordinate is $-x-y$. Decimal integer strings support large coordinates and weights. `hat`, `turtle`, and `hexagon` load the existing polygon point weights as convenience inputs. The lexicographically first positive site is the origin of the output's prototile frame; translated copies with identical weight functions have a single placement identity.

The optional second argument to `run.mjs` is a settings file. For example, the following settings grow two successive hexagonal windows. Save these settings to `settings.json` and run `node run.mjs two-weights.json settings.json`.

```json
{"radius":1,"through":2,"seed":6,"nodes":100000,"extent":0,"proposals":32,"proofRadius":0,"proofNodes":0}
```

`radius` is the first target radius. Omitting `through` requests one window. An integer end radius requests successive windows. A null end radius continues until a window is exhausted or a budget is reached. `nodes` is a per-window move budget shared by all revisions within that window. A null node budget allows exhaustive search. Each output line contains the settings, learned assignments, witnessed failures, and the placements covering the requested window. A placement ID records its canonical orientation index followed by the translation of the oriented tile's first site.

## Search and learning

1. Fix one copy of the tile. Require full capacity at **every** lattice point of the target hexagon, including untouched points. Enumerate each move that contributes positive weight to a required point. Allow placements to extend beyond the hexagon and enforce capacity everywhere they reach. This works for disconnected supports as well.
2. Use the standard global dead-point, forced-move, oldest-point and last-placement adjacency priorities. Fixed target points all start at step zero. Canonical domain enumeration and a fixed pseudorandom seed make the draw reproducible. Each search frame retains the ordered alternatives incident to its chosen point.
3. On a dead point or a fully exhausted subtree, try two unequal signed values that meet on one global lattice point and axis of two placements in the failed patch. `extent` bounds the local marking domain and `proposals` bounds the number of candidates examined at one failure. Setting `proposals` to zero runs the unmarked control. Close the proposed assignments under all affine symmetries of the tile's weight function. A zero is an assigned value, and an absent component is $\ast$.
4. Enumerate the unequal overlaps created by the additions, both with one another and with previously committed values. Fix the first tile in its canonical frame. For every allowed orientation of the second tile, equating the positions of two assigned values determines the only translation that can make them coincide. Test each such relative pair with **unmarked** GCTS. Force both placements and require completion of their positive supports plus a halo of `proofRadius` lattice steps. Only exhaustion is a certificate. A finite cover or a proof search cutoff leaves the proposal uncommitted. With `proofNodes` set to zero, overcapacity and empty-domain certificates are still available.
5. On acceptance, keep the assignments and rebuild from the fixed root. Exact exhausted placement sets are retained within the window; earlier domains and an earlier prefix can have become incompatible. When advancing to a larger window, retain the marking and search afresh for the placements. `verify.mjs` independently enumerates all conflicting pairs from an exported table, replays the unmarked proof searches, checks the tile symmetries, and checks the returned covers point by point.

## What is guaranteed

**Soundness.** Suppose a full-plane tiling were excluded for the first time by a revision. It would contain two placements assigning unequal values at an overlapping site and component. Up to a lattice symmetry, that relative pair was explicitly tested. Restricting the full tiling to the two fixed copies and the tiles supplying the proof window would give an unmarked finite completion. This contradicts exhaustion. Hence every accepted revision preserves every full-plane tiling of the input.

**Finite search.** A finite window has finitely many incident placements. With no search cutoff, its branches can be exhausted. There are finitely many available assignments at the configured extent and every accepted revision adds at least one, so learning cannot cause an infinite sequence of restarts in one window. `covered` certifies the displayed window. `exhausted` rules out a full-plane tiling containing the root, and every tiling by this single prototile can be moved to that root. `unknown` records a search cutoff.

**Increasing windows.** If a full tiling exists, exhaustive runs cover every requested radius. Conversely, if every radius has a cover, local finiteness permits a diagonal subsequence agreeing on each finite set of placement choices. Compactness also implies a finite unmarked obstruction whenever a fixed pair is impossible in every full tiling. [Background on the finite-obstruction argument](https://terrytao.wordpress.com/2021/08/19/undecidable-translational-tilings-with-only-two-tiles-or-one-nonabelian-tile/)

**Producing one tiling in the limit.** When `through` is supplied, the default is `stabilize: true`. Order all placements once by the hexagonal norm of the translation, then its coordinates, then orientation. Every placement has finitely many predecessors. Encode a cover by its presence bits in that order, with zero preferred. For each window, use further base GCTS feasibility queries to select its lexicographically least feasible bit sequence. To settle the next bit, try forbidding the placement while holding all previous decisions fixed; the current witness often already omits it. Only the finitely many placements incident to the window need consideration, because dropping any other optional tile preserves feasibility. Failures inside these artificially restricted queries are confined to that query.

Allow arbitrary optional tiles beyond a window when comparing its feasible set with that of a larger window. The larger window requires completion at more points, and the marking can only acquire certified assignments. Its feasible set is therefore a subset. The least bit sequence can only increase lexicographically, so each finite prefix can change only finitely often. With exhaustive searches on a tile that tiles, the printed window covers consequently converge at every placement to one full-plane tiling. The algorithm can revise earlier choices and supplies no general time bound for the last revision of a given bit.

The ordering queries share the window's node budget and can be expensive. For the supplied two-site example and the settings above, radius two used 25 trial placements to find a cover and another 64,014 to determine the least cover. Set `stabilize` to false to return the first cover at each radius. Single-window requests use that faster setting by default.

**Limits of the encoding.** A fixed point marking detects a clash between two placements. A failed patch in which every pair occurs in some full tiling cannot be excluded by this kind of sound marking. Search still backtracks normally. The same compactness argument gives a finite obstruction for every genuinely impossible fixed pair. A verifier that systematically increases its proof radius and budget can therefore eventually certify *any given sound finite candidate table*. The prototype uses the configured bounds and may miss such tables. Discovery of a useful marking and improvement in running time depend on the tile.

## Reproducible example

The two-site example has weights $5/12$ and $7/12$. One copy in the same orientation at every lattice translate gives a full tiling. If two $5/12$ ends coincide, the missing $2/12$ cannot be supplied by any placement. With the example settings above, the search encounters such a failure and learns $(+1,\ast,-1)$ at the $5/12$ site, with all components unassigned at the other site. Its induced exclusions are independently replayed. The test also checks that an unsafe signed table fails verification, that a cutoff produces no false certificate, and that the Hat can learn from an initially empty table.
