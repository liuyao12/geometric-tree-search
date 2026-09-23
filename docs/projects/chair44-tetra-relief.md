# Chair44 tetrahedral relief

The live [Chair44 viewer](https://liuyao12.github.io/geometric-tree-search/3d-reptiles/)
uses a tetrahedral wedge adapted from the earlier volume-\(27\) cube dissection. The apex adjustment separates the formerly coincident green–blue and green–green recess walls.
Arrows and Relief switch the display; Apply one and Run both search the new
geometric solid. Apply inflation remains the known marked substitution.
The old Offset/Centered pyramid controls have been replaced by this one solid.

## Solid and folds

A representative wedge has vertices
\[
(0,0,0),\quad(6,0,0),\quad(6,6,0),\quad(3,2,2).
\]
Scale it by \(1/6\) for each unit square of the chair. Its base occupies one
triangular half of that square and its normal height is \(1/3\). The earlier
apex \( (4,2,2) \) moves to \( (3,2,2) \), parallel to the hinge. This changes
the proportions but preserves the base, height, and volume \(1/18\).
Red adds a wedge; green removes one; blue adds one half and removes the other.
The triangular half follows the original half-arrowhead handedness: red lies
on the left of the directed diagonal, green on the right, as viewed outside.
The blue bump uses the red side and its recess the green side.

All eight green cuts have a unique congruent red bump obtained by a quarter-turn
about a full unit-square edge. All eight blue pairs exchange by a half-turn
about the square diagonal. This checks the endpoints, not a collision-free
simultaneous mechanism for the whole chair. As in the earlier cube mechanism,
a convex-edge hinge may need the outside \(270^\circ\) path rather than the
inside \(90^\circ\) path. No hinge hardware is included here.

There are sixteen additions and sixteen removals. Exact union-volume and
oriented-boundary checks give volume \(7\), and a closed mesh. All construction
coordinates are rational. The exported boundary subdivision uses integer
coordinates in units of \(1/6\), so multiplying this mesh by \(6\) gives an
explicit lattice polyhedron. This is a geometric realization being tested;
the aperiodicity/extension certificates for the previous square-pyramid relief
have **not** been transferred to this shape.

## Exact geometry as point values

The allowed placements are integer translations and the twenty-four proper
cubic rotations. Reflections and arbitrary free-space orientations are absent.
Within every unit cube, the forty-eight possible wedge positions have sixty
distinct boundary planes. Their exact rational arrangement has 7,776 convex
chambers. Every chamber lies entirely on one side of every wedge plane.
Distinct plane-sign signatures and exact total volume \(1\) certify the
partition during regeneration.

The chambers fall into 121 occupancy classes: points in the same class belong
to exactly the same subset of the forty-eight wedges. The generator selects
121 rational sample points, closed under the twenty-four proper rotations,
covering all those classes. Each sample stores integer numerators and an exact
denominator; the largest denominator is 1,056. This reduction retains every
possible occupancy distinction, including edge and corner contacts.

For each placement, \(t(p)=1\) exactly when its solid contains the sample;
otherwise \(t(p)=0\). There are no \(m\)-values and no color or arrow rejection
test. In a cube, any placed tile's occupancy is a Boolean combination of the
forty-eight wedge memberships and the constant base-cube occupancy. Therefore
samples representing all membership classes detect every positive-volume
intersection and gap for the declared placements. Shared zero-volume boundary
faces are permitted. This is an exact class reduction of the full arrangement,
not an approximate sampling test.

Occupancy is stored as an exact BigInt mask per cube. The renderer uses the
same wedge vertices to build 112 outward-oriented triangles, with integer
coordinates in sixths. Independent rational tests check the boundary volume,
edge pairing, wedge intersections, and coincident face areas. Separate tile
surfaces remain visible at matching contacts, with transparency and orientation
dimming; the correction removes unwanted contacts within a single tile.

## Search contract and scope

- Every cube touched by a placed tile activates all its chamber points. Missing
  points are frontier obligations, including enclosed gaps. Their generation
  is the minimum generation of placed tiles activating that cube.
- Enumerate every orientation and every support-cube alignment that can cover
  an active deficit. Every candidate is checked against all occupied chambers.
  There is no base-heptacube overlap shortcut or inflation-derived restriction.
- Maintain complete point-to-candidate incidences and shared candidate nodes.
  Scan the entire frontier for dead ends, then forced moves, then choose the
  earliest generation; minimum degree only breaks generation ties.
- A new tile has one plus the minimum generation of the frontier points it
  fills. Immutable snapshots restore the accepted prefix, generations, stack,
  and counters exactly. Worker cancellation discards unaccepted work; Undo
  groups Run into one transaction. Growth after inflation retains that patch.
- The graph is rebuilt each step; incremental dependency bookkeeping remains a
  gap against the master algorithm contract. Activation is local, not a fair
  exhaustion of the infinite domain. A viable finite patch is not an infinite
  tiling certificate. The thirty-two-attempt batch is resumable, not a failure
  verdict. No learned markings or RL proposals are enabled.

The initial graph has 1,513 legal candidates incident to active chamber deficits.
This includes partial cube contacts and should not be compared directly with the
old face-neighbor counts. A deterministic sixty-four-tile run finishes with four
branch decisions, two backtracks, and fifty-nine forced placements. This is a
consistent finite patch, not a proof that the new relief forces the hierarchy.

## Validation

Run `scripts/build-chair-tetra-atoms.py` to regenerate the rational arrangement,
audit its complete partition, and select all occupancy-class representatives.
Use `--check` to replay that audit and check the stored data without writing it.
`python3 scripts/verify-chair-tetra-geometry.py` independently checks all 496
wedge pairs and every pair of rendered triangles with rational arithmetic. It
reproduces the two old coincident contacts and verifies that the adjusted solid
has neither coincident face areas nor overlapping wedge interiors. Set
`NODE_BINARY` if Node is not on the path.
`node scripts/test-chair-tetra-relief.mjs` independently evaluates every sample against all wedge positions, verifies
complete occupancy-class representation, volume and closed oriented boundary,
checks all red/green and blue hinge endpoints, all 864 facing-mark comparisons,
and rotational covariance.
It independently enumerates the complete root translation box and replays every
frontier incidence. It also checks immutable rollback, growth from rotated and
translated inflation patches, and a sixty-four-tile run with real backtracking.

The browser suites `test-chair-marking-view-browser.cjs`,
`test-chair-geometric-browser.cjs`, and `test-chair-run-browser.cjs` cover rendered
mesh volume/closure, both display modes, all orientation highlights, mobile
layout, worker cancellation, Pause, grouped Undo, and growth after inflation.

The original arrows come from [Goodman–Strauss, Figures 2 and 5](https://arxiv.org/abs/2609.24779).
The [previous centered-relief study](chair44-centered-relief.md) and
[rounded hinge prototype](chair44-fold-out-design.md) describe different geometry.
