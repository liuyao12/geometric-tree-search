# Chair44 tetrahedral relief

The live [Chair44 viewer](https://liuyao12.github.io/geometric-tree-search/3d-reptiles/)
uses the centered tetrahedron from the earlier volume-\(27\) cube dissection.
Touching dents join into a cavity: the renderer draws the actual solid boundary,
with their internal walls removed. No apex displacement is used.
Arrows and Relief switch the display; Apply one and Run search the geometric
solid. Apply inflation remains the known marked substitution.

## Solid and folds

In the original lattice units, a representative wedge has vertices
\[
(0,0,0),\quad(3,0,0),\quad(3,3,0),\quad(2,1,1).
\]
The apex is directly above the base centroid \((2,1,0)\), at integer height.
Scale by \(1/3\) for each unit square of the chair: the normal height is then
\(1/3\), and the wedge volume is \(1/18\). All pyramid vertices are on this
original lattice. The earlier sideways displacement has been undone.

Red adds a wedge; green removes one; blue adds one half and removes the other.
The triangular half follows the original half-arrowhead handedness: red lies
on the left of the directed diagonal, green on the right, as viewed outside.
The blue bump uses the red side and its recess the green side.
The eight intended green/red pairs remain congruent under quarter-turns about
their full-edge hinges. All eight blue pairs exchange by half-turns about the
square diagonals. These are endpoint checks, not a collision-free simultaneous
mechanism; no hinge hardware is included. A convex-edge hinge may require the
outside \(270^\circ\) path rather than the inside \(90^\circ\) path.

There are sixteen additions and sixteen removals. The final volume is \(7\).
Two pairs of raw cuts meet along a positive-area patch: one green/blue and one
green/green. They have no overlapping interiors. Such a shared wall lies
inside the combined cavity and is not a face of the remaining solid. Taking
the exact union removes it; transparency is not used to conceal duplicate faces.
The boundary is closed, with every vertex link a single cycle.

Joining these cavities introduces intersection vertices on a finer lattice.
For example, in normalized chair coordinates one junction is
\((3/4,3/2,7/4)\). Thus the **apexes** retain the original lattice, while the
complete boundary uses coordinates in \((1/12)\mathbb{Z}^3\). Multiplying the
normalized solid by \(12\) gives integer boundary vertices. This distinction
matters when choosing manufacturing dimensions.

### Bump/dent reversal experiment

With the half-square bases and centered height fixed, give each marked square
a reversal bit; both blue halves reverse together. Retaining the contacts in
the existing eight-chair supertile forces all sixteen red/green bits to agree,
and all eight blue bits to agree. Each of the four resulting choices has at
least one coincident raw wall. Reversals alone cannot remove all of them under
these assumptions.

Reversing the two red/green pairs at zero-based mark indices \((9,10)\) and
\((16,19)\) does avoid all raw wedge contacts and preserves volume, but breaks
some existing supertile contacts. The live model therefore retains its matching
and joins the touching dents instead. This finite design audit is not a proof
that other reversal patterns cannot tile by some different construction, nor
that the centered relief forces aperiodicity.

## Exact geometry as point values

The allowed placements are integer translations and the twenty-four proper
cubic rotations. Reflections and arbitrary free-space orientations are absent.
Within every unit cube, twenty-four possible wedge positions have twenty
distinct boundary planes. Their exact rational arrangement has ninety-six
convex chambers. Every chamber lies entirely on one side of every wedge plane.
Distinct plane-sign signatures and total volume \(1\) certify the partition.

The chambers fall into forty-nine occupancy classes: points in the same class
belong to the same subset of the wedges. Forty-nine rational representatives,
closed under proper cubic rotations, cover every class. Each sample stores
integer numerators and an exact denominator, at most forty-eight.

For each placement, \(t(p)=1\) exactly when its solid contains the sample;
otherwise \(t(p)=0\). There are no \(m\)-values and no color or arrow rejection
test. In a cube, tile occupancy is a Boolean combination of wedge memberships
and the constant base-cube occupancy. Class representatives therefore detect
every positive-volume intersection and gap for the declared placements.
Shared zero-volume boundaries are permitted. This is an exact reduction of the
complete arrangement, not approximate sampling.

Occupancy uses an exact BigInt mask per cube. Rendering uses the same occupied
chambers and cancels their shared faces, including the internal cavity walls.
Its 284 triangles merge into **98 connected planar faces**, regardless of color;
disconnected regions in the same plane count separately. Fold outlines include
all six original tetrahedron edges, so some are construction lines rather than
edges of the combined solid. Separate tiles retain their contact surfaces,
transparency, and orientation dimming.

## Export to the lattice tiler

The [exact point export](chair44-lattice-export.md) retains this geometry and
imports it into the shared lattice tiler without rounding solid angles.

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
checks the centered lattice apexes, detects the two raw cut contacts, and verifies
that the actual boundary has no coincident face areas or pinched vertices.
`python3 scripts/check-chair-centered-folds.py` enumerates the finite reversal
constraints and checks the alternative that breaks the existing supertile. Set
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
