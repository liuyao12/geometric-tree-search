# A2-layered non-polycube search

The first non-polycube family now exposed in the 3D lattice catalogue uses the
affine triangular layers `x + y + z = c`.

The base polygons are the exact A2 hexagon, hat, and turtle already used by
the intrinsic two-dimensional GCTS demo. Each is extruded by `(1,1,1)`, so its
two end faces lie on levels 0 and 3. The resulting vertices remain in `Z^3`;
no voxelization is used.

## Exact lattice-function weights

The A2 engine stores planar angles in twelfths of a full turn. At an end face
of the prism the three-dimensional solid angle is half of the planar cone, so
a planar weight `a` becomes `2a` in the standard forty-eighth convention. At
an intermediate section it would become `4a`. Thus the layered generator is
an exact realization of the lattice-tile function in GCTS-I even when the
visible hat or turtle prism is non-convex.

The hexagonal prism is marked as an ordinary convex polyhedron and is the
positive periodic control. Hat and turtle are deliberately marked
`lattice_function`, not convex polyhedra: legality is decided by exact lattice
solid-angle occupancy, and the engine must not apply convex SAT overlap or a
convex one-tile certificate to them.

## Symmetry scope

These tiles do not use all 24 proper rotations of the cubic lattice. Their
fixed lattice is the foliation by A2 layers, so the direct point group is the
six-element subgroup carrying `(1,1,1)` to `+(1,1,1)` or `-(1,1,1)`. Reflected
copies add the other six A2 isometries only when the UI's reflection option is
enabled. The pre-processing report records this group and the tile stabilizer
before any lane is clocked.

This restriction matters: treating the UI's historical polycube “FCC” tier as
the same object would be incorrect. That tier merely refines polycube sample
points and permits even-sum translations; it does not change the symmetry
group for general non-polycubes.

## Certificate boundary

The extruded hat and turtle are useful structured GCTS benchmarks, but they
are not asserted to be strongly aperiodic three-dimensional monotiles. A
product tiling can retain a translation along the extrusion direction, and
the unrestricted three-dimensional tile may admit configurations not visible
in the planar theorem. Their catalogue label is therefore “layered aperiodic
lead,” not “known aperiodic monotile.”

The next census should move beyond product prisms by enumerating exact lattice
functions on several adjacent A2 layers and retaining only shapes with no
obvious axial period. Periodic certificates remain positive proofs; bounded
failure of translational or isohedral lanes remains inconclusive. Exact GCTS
corona obstructions should be reported only in the explicitly searched
lattice-function model.

## Multi-layer polyprism census

`assets/a2-layered-polyprisms.js` enumerates connected unions of elementary
triangular prisms in the A2-layer honeycomb. Equivalence uses translations and
the fixed six-element proper layer group. Single-layer shapes and repeated
identical cross-section products are flagged as product prisms and omitted
from the search pool.

The complete fixed-lattice census counts through size six are 1, 2, 4, 15,
50, and 237; after the product filter, the first two candidates occur at size
three. The patch-growing translational lane initially certified 44 of the 45
size-five non-products and left `a2lp_5_00003` unresolved. A 30-second rerun
grew 37 copies but exhausted only motifs through three copies, exposing that
patch growth was the bottleneck rather than the quotient decision itself.

The superseding screen solves each weighted HNF quotient directly with Z3.
It requires exactly 48 solid-angle units at every quotient class, fixes one
root copy only by translation and global proper-layer symmetry, and replays
every positive independently using Cramer's-rule quotient coordinates. All 45
size-five non-products have verified two-copy quotients of determinant 5,
including `a2lp_5_00003`. All 222 size-six non-products have verified one-copy
quotients of determinant 3. There are consequently no aperiodic candidates in
this census through size six, and the formerly unresolved catalogue entry has
been removed.

The original patch screens remain as diagnostics in
`data/a2-layered-size5-screen.ndjson` and
`data/a2-layered-size6-screen.ndjson`. The authoritative exact positive
reports are `data/a2-layered-size5-periodic-z3-all.ndjson` and
`data/a2-layered-size6-periodic-z3-all.ndjson`. Bounded failure of a future
quotient size will still be reported as unresolved; only an independently
replayed positive is called periodic.

Size seven is the first selective census. Of 1,119 non-product candidates,
910 have exact two-copy determinant-7 quotients. Direct meet-in-the-middle
search then finds four-copy determinant-14 quotients for 98 of the remaining
209. The other 111 exhaust all 399 HNF bases at four copies with no solver
unknowns. Their report is
`data/a2-layered-size7-periodic-z3-through4.ndjson`; these 111, rather than the
earlier timeout survivors, form the next exact-corona/GCTS pool. Failure
through four copies does not exclude a larger periodic domain.

Every one of the 111 exact-through-four survivors has an independently
replayed root-corona witness. A focused second-corona CEGAR screen then tested
eight especially compact root coronas. For each candidate, eight distinct
first-corona patches were proved unable to saturate their complete support;
the outer first-corona solver still has untested models, so all eight remain
inconclusive. This is recorded in
`data/a2-layered-size7-corona2-focused.ndjson`. Exact-model blocking is used:
the search never generalizes an obstruction to an untested corona merely
because the patches look similar.

The leading compact candidate `a2lp_7_00232` has a longer exact-model CEGAR
run: 64 distinct first coronas are individually proved unable to extend to a
second corona. The outer model is still not exhausted, so this strengthens
the finite obstruction evidence without changing its unresolved status. See
`data/a2-layered-size7-corona2-a2lp_7_00232-deep.ndjson`.

A complete coupled radius-two formulation is also implemented in
`scripts/screen-a2-layered-corona2-direct.py`: Boolean variables choose the
first corona and the final patch simultaneously, while implications require
exact saturation of precisely the support activated by the chosen first
corona. For `a2lp_7_00232` this has 580 first-placement variables, 4,643 final
placement variables, and 88,217 sparse incidences. The QF finite-domain/PB
backend remained undecided at its 180-second limit; the hash-committed report
is `data/a2-layered-size7-corona2-direct-a2lp_7_00232-qffd.ndjson`. This is a
complete formulation but an incomplete solve, so it changes no classification.

`scripts/screen-a2-layered-corona2-core-cegar.py` supplies the next exact
decomposition. An inner UNSAT core is converted into a sound placement-subset
clause: all unselected placements remain available as potential helpers, so
the clause can block every first corona containing that obstruction without
assuming geometric similarity. The initial copy-capped run is retained in
`data/a2-layered-size7-corona2-core-a2lp_7_00232-cap21.ndjson` as a timeout
diagnostic, not as obstruction evidence.

For `a2lp_7_00232`, the first 16-placement core was independently reduced and
replayed as a 12-placement obstruction against 2,291 possible helper
placements. It is sound but not claimed minimal. Resuming the outer search
from that marking learned four further clauses in 38 seconds, then a longer
515-second continuation learned 32 more. The resulting 37 sound clauses are
recorded in
`data/a2-layered-size7-corona2-core-a2lp_7_00232-long.ndjson`; the independently
replayed reduced core is in
`data/a2-layered-size7-corona2-core-a2lp_7_00232-minimized.ndjson`. The outer
first-corona space is still not exhausted, and no radius-two witness has been
found, so the candidate remains unresolved rather than being called a
non-tiler or an aperiodic monotile.

The same resumable core search has now been run on all eight focused
candidates. After a further 32 exact rounds per candidate and removal of
clauses subsumed by stronger learned clauses, the retained family-obstruction
counts are 48 (`00128`), 45 (`00211`), 68 (`00232`), 48 (`00235`), 47
(`00694`), 47 (`00755`), 48 (`00777`), and 47 (`00809`). Every run remains
unresolved: none exhausted the outer first-corona space and none found a
radius-two witness. Per-candidate reports end in `-extended.ndjson`.

A separate longer periodic screen attempted six- and eight-copy quotients.
Every candidate reached its 120-second limit while still at six copies,
visiting between 41 and 127 of the 741 determinant-21 HNF bases and returning
between two and twenty solver unknowns. It found no positive certificate, but
is not an exhaustion result. The three batch reports are
`data/a2-layered-size7-periodic-z3-focus6to8-part1.ndjson` through `part3`.

`scripts/screen-a2-layered-substitution.py` exactly subdivides a scalar-inflated
supertile into atomic A2 prism cells, enumerates every properly oriented copy
contained in it, and solves the resulting finite exact cover. All eight
candidates have certified no scalar self-substitution at scales 2 through 6.
Simple failures carry a separately replayed uncovered-cell obstruction; deeper
failures are replayed by an independent Z3 pseudo-Boolean exact-cover model.
This excludes only scalar `sI` rep-tile rules. Non-scalar integer inflation
matrices, decorated orientation states, and substitutions using several
metatile shapes remain open.

For the cellular anisotropic family, the triangular cross-section can only be
scaled uniformly up to an A2 lattice symmetry; a general Eisenstein multiplier
rotates an edge off the triangular cell complex. The remaining non-scalar
single-supertile maps therefore have independent integer planar and layer
scales `(s,c)`. The exact family screen exhausts all 42 pairs with
`2 <= s,c <= 8` and `s != c` for every focused candidate. All 336 finite
exact covers are certified negative: 246 have an independently replayed local
uncovered-cell obstruction, and 90 are independently replayed UNSAT by Z3.
The combined report is
`data/a2-layered-size7-substitution-anisotropic-s2to8-focused.ndjson`.

The machine-readable screen is `data/a2-layered-size5-screen.ndjson`. Rebuild
it with:

```bash
node scripts/screen-a2-layered-polyprisms.mjs --size=5 --time-ms=1200 --motif-tiles=8
python3 scripts/screen-a2-layered-periodic-z3.py \
  --input data/a2-layered-size5-screen.ndjson \
  --output data/a2-layered-size5-periodic-z3-all.ndjson \
  --max-copies 2
```

Run the regression with:

```bash
node scripts/test-3d-a2-layered-prisms.mjs
node scripts/test-a2-layered-polyprism-census.mjs
```
