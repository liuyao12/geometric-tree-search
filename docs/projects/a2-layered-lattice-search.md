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
three. In the initial size-five screen, 44 of the 45 non-product candidates
received exact two-tile translational boundary-quotient certificates. The
remaining record, `a2lp_5_00003`, is unresolved: longer translational and
isohedral runs reached finite patches but produced neither a periodic
certificate nor a negative proof. “Unresolved” here is deliberately not a
claim of aperiodicity.

At size six there are 222 non-product candidates. The first short pass gives
149 exact two-tile translational certificates and leaves 73 bounded-unresolved
records. This is a triage result only: a four-second rerun of the first twenty
short-pass survivors eliminated nine more periodically, so the 73 must not be
treated as a stable candidate count until the deeper pass is complete.

The machine-readable screen is `data/a2-layered-size5-screen.ndjson`. Rebuild
it with:

```bash
node scripts/screen-a2-layered-polyprisms.mjs --size=5 --time-ms=1200 --motif-tiles=8
```

Run the regression with:

```bash
node scripts/test-3d-a2-layered-prisms.mjs
node scripts/test-a2-layered-polyprism-census.mjs
```
