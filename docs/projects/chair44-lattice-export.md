# Chair44 export to the 3D lattice tiler

[Open the imported tile](../../3d-lattice-tiler/?tile=chair44_relief&catalogue=all)
or [download the self-contained JSON](../../3d-reptiles/chair/chair44-exact-points.json).
The Chair44 scene has both links. The lattice tiler's Custom system panel accepts
the file, or its JSON text, through `point_model` format `gcts-exact-points-v1`.
The built-in Chair44 entry and imported file produce the same model.

## Geometry and transformation scope

The export retains the centered, merged-cavity solid: ninety-eight connected
planar faces, volume \(7\), with the same boundary as the Chair44 scene. No
pyramid is shifted, resized, or replaced. The physical boundary vertices lie
in \((1/12)\mathbb Z^3\), using the original small cube as the unit.

Allowed placements retain the existing Chair44 experiment: the twenty-four
proper cubic rotations and translations in \(\mathbb Z^3\). Reflections are
disabled for this export. Translations by arbitrary boundary-lattice steps
\(1/12\), or arbitrary Euclidean isometries, are **not** included. The JSON
states its placement domain; the importer, graph, and verifier all enforce it.

## Exact point model without rationalizing angles

The ordinary polyhedron importer uses solid-angle weights and only accepts
exact rational weights in v2. This solid has irrational solid angles. Rounding
those values would change the problem, so this export uses a different,
explicitly declared exact point model. It imports the nonconvex boundary
directly rather than taking a convex hull.

The existing exact arrangement partitions each unit cube into ninety-six
chambers and forty-nine distinct wedge-membership classes. One rational sample
per class suffices to distinguish all possible tile occupancies for the allowed
placements. These sites have \(t=1\) inside a placed solid and \(t=0\) outside.
Their full construction and completeness audit are in the
[relief geometry report](chair44-tetra-relief.md).

Using these occupancy bits alone in seed growth would leave no partially filled
points, so the generic engine would incorrectly treat a single tile as a closed
local patch. To expose gaps without changing that engine, add six auxiliary
sites per cube at
\[
 c+\left(\frac12,\frac12,\frac12\right)
   \mathbin{\pm}\frac1{96}e_i,
 \qquad i\in\{1,2,3\},\quad c\in\mathbb Z^3,
\]
where the vectors \(e_i\) are the three coordinate unit vectors.
These sites are distinct from the occupancy samples and form a rotation-invariant
set. Each carries the volume fraction of the placed tile within that cube.
These are **volume constraints**, not solid angles or material occupancy at
those auxiliary locations.

Each tetrahedral addition or removal has volume \(1/18\); per-cube volume
fractions are therefore integer multiples of \(1/18\). Capacity is eighteen:
occupancy sites have weight eighteen, and auxiliary sites have the integer
volume numerator. All coordinates are multiplied by ninety-six, so coordinates
and weights are exact integers. Allowed translations are multiples of
ninety-six in these computational coordinates. This finer computational scale
does not change the geometric mesh or broaden the translation group.

The reduction is faithful within the declared placement group:

- Occupancy samples detect every positive-volume overlap, because they cover
  every membership class of the complete arrangement.
- For nonoverlapping solids, per-cube volumes add to at most one, so the volume
  constraints reject no geometrically legal packing.
- Every touched but incompletely filled cube has positive volume below one.
  Its six auxiliary sites are frontier obligations. Reaching capacity there,
  together with nonoverlap, fills that cube without a positive-volume gap.
- Every candidate that can fill a touched cube contributes positive volume at
  those same sites, so enumerating all allowed support alignments is complete.

There are fifty-five declared sites per cube and 475 positive support entries
per orientation. No arrow, color, or precomputed inflation constraint is imported;
all marking lists are empty. GCTS can learn new markings through the existing
unmarked oracle. No prelearned marking is bundled.

## Shared algorithm conformance and limits

The imported tile uses the existing `GrowthGraph` and `CoronaGraph`, with shared
point/candidate incidence and reverse dependencies, global dead-end checks,
forced moves, earliest-generation branching, and exact rollback. Positive
volume support generates the frontier; this is not an alternate geometric
placement filter or a new specialized scheduler. Generic search does not call
the Chair44 inflation code. Complete candidate domains are retained within
resource budgets; a budget limit is reported as unknown.

Finite-window mode requires every declared site in the selected cube window.
Seed growth uses local activation and does not certify fair exhaustion of all
space or infinite extension. A viable finite patch is not an aperiodicity proof.
The historical solid-angle periodic/isohedral probes are disabled for imported
point domains because they would test a different model.

At seed ten, an eight-tile free-range run reaches a verified frontier with four
branch decisions and five backtracks. This is a distinct point representation
and its ordering differs from the Chair44 scene's specialized search; do not
compare raw branch counts as though both benchmarks were identical. No GCTS
speedup or successful completed marking-learning run is claimed by this export.

## Verification

- `node scripts/export-chair44-lattice.mjs --check` reproduces the JSON exactly.
- `node scripts/test-chair44-lattice-export.mjs` independently integrates all
  occupied chambers to check every volume weight, verifies all oriented boundary
  meshes, compares 8,232 pair placements against the geometric occupancy engine,
  and checks all 1,513 root candidates against its independently enumerated
  graph. It checks rollback, original supertile placements, and the eight-tile
  run with independent frontier and geometric replay.
- `node scripts/test-chair44-lattice-export-browser.cjs` exercises the scene's
  download/open links, preset preview, actual worker growth, cancellation, JSON
  file import, guarded probes/reflections, another catalog tile, and mobile
  layout. Set `GCTS_TEST_URL` to the site root to repeat it on the live deployment.


## Rigid assembly of the canonical supertile

Static nonoverlap and physical assembly are different questions. The point
solver checks final placements, not collision-free insertion paths. This audit
is a separate geometric validation and does not prune its search candidates.

For the canonical eight-tile supertile, write the small-cube-unit origins as
$\mathbf{o}_i$ and keep all orientations fixed. The continuous motion

$$
\mathbf{o}_i(\lambda)=\mathbf{o}_i+
\lambda\bigl(\mathbf{o}_i-(1,1,1)\bigr),\qquad \lambda\geq 0
$$

has no positive-volume collisions. The central tile has origin $(1,1,1)$ and
stays fixed; the other seven move out together. For sufficiently large
$\lambda$ all copies are separated. Reversing this path assembles the supertile
from eight separated rigid copies, with the central copy fixed.

By contrast, moving any one of the seven outer tiles along its same diagonal
while holding all the other tiles fixed causes an immediate collision. This
rules out those seven individual paths, not every sequential assembly route.

`node scripts/check-chair44-assembly.mjs` reproduces both results. It uses the
actual centered relief with merged cavities, decomposed into 672 occupied
convex chambers per copy. For all twenty-eight tile pairs it tests the full
half-line of relative translations using separating axes: face normals and
edge cross-products. Projection-overlap intervals have rational endpoints;
comparisons use exact integer products with safe-integer assertions. Boundary
contact is allowed, but positive-volume intersection is forbidden. Elementary
box motions also check interval signs, tangency, and delayed collisions.

This certifies an ideal rigid assembly path for this particular supertile.
It does not establish sequential insertion for arbitrary solver patches,
assembly at every inflation level, frictional feasibility, manufacturing
clearance, or aperiodicity of the unmarked solid. No geometry was changed.
