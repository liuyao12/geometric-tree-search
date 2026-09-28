# Chair44: checking the printed concavities and sliding fit

The current centered-apex print model passes **pairwise sliding checks**, but
**the complete canonical supertile is locked against individual translation**.
These are ideal rigid-body geometric results, not a physical print test.
No geometry or manufacturing clearance was changed in this audit.

## Which geometry was tested

The apex remains \((2,1,1)\) in the original side-three coordinates. The model
has ninety-eight connected planar faces; touching cavities are joined. The
check reads the actual forty-eight-millimeter STL from the print package and
compares every triangle, exactly after undoing its scale and translation,
with the geometry used for collision checking. They agree.

## Pairwise insertion: clear

The canonical eight-chair supertile has sixteen tile pairs with positive-area
face contact. Every pair has a collision-free straight extraction path with
one copy fixed and the other moving; reverse it for insertion. All other copies
are absent for this pairwise test.

If the final small-cube-unit origins are \(\mathbf{o}_i,\mathbf{o}_j\), keep
copy \(j\) fixed and move copy \(i\) along

\[
\mathbf{o}_i(t)=\mathbf{o}_i+t(\mathbf{o}_i-\mathbf{o}_j),\qquad t\geq0.
\]

Orientations remain fixed. The test covers the entire continuous half-line,
not discrete animation frames, and the two copies eventually separate.
Boundary contact is permitted; positive-volume intersection is forbidden.

Nine outer-to-outer mating pairs extract along a coordinate axis. The seven
pairs involving the center copy extract along a body diagonal. Each of these
seven pairs has three tangent contact-plane normal directions, including two
linearly independent normals. Consequently, some nonparallel faces remain in
contact during the final portion of insertion and act as sliding guides.
This does not claim face contact over the entire path from separated copies.

The continuous collision check decomposes each solid into 672 occupied convex
chambers, using exact integer coordinates. Separating-axis tests include all
face normals and edge cross-products. Projection-overlap intervals are compared
as rationals using safe-integer cross-products. Every chamber pair is checked;
all twenty-eight tile pairs pass, including the twelve without positive-area
face contact in the final supertile.

## Completed supertile: no independent sliding direction

For each of the eight copies, hold the other seven fixed. If an outward face
normal of the moving copy is \(\mathbf n\) at a positive-area contact, an
infinitesimal translation \(\mathbf v\) must satisfy

\[
\mathbf n\cdot\mathbf v\leq0.
\]

Each copy has contact normals in three independent pairs
\(\mathbf n_1,-\mathbf n_1\), \(\mathbf n_2,-\mathbf n_2\), and
\(\mathbf n_3,-\mathbf n_3\). The two signs force
\(\mathbf n_k\cdot\mathbf v=0\) for every \(k\). The normal matrix has nonzero
determinant, so \(\mathbf v=0\). Each normal in the certificate is backed by
an exactly clipped, positive-area pair of contacting boundary triangles.
This rules out all straight extraction directions, not just sampled axes or
diagonals. Reversing a straight insertion path would give an extraction path;
therefore no copy can be the last one slid into this completed arrangement
while the other seven stay fixed.

This check does not analyze rotation-assisted insertion. Coordinated motion is
possible: the earlier continuous test certifies that all seven outer copies
can move outward together, with the center fixed. Reversing that motion gives
an ideal assembly route for this supertile.

## What this means before printing

The concavities do not obstruct the tested individual mating pairs. They do
produce collective locking when all copies are together. The current geometry
is suitable for investigating a mating pair or coordinated assembly; it should
not be presented as verified for building the complete supertile by inserting
one fixed-orientation copy at a time. Nor does this test cover all arrangements
that the unrestricted-growth point solver may find.

The files have exact nominal dimensions with no added clearance. Surface
roughness, shrinkage, friction, support scars and access for gripping are outside
this geometric test. A two-copy trial is the next practical check before a full
set is manufactured.

## Reproduce

- `NODE_BINARY=/path/to/node python3 scripts/check-chair44-sliding.py` verifies
  the delivered STL, exact face contacts, seven guided pairings, and eight
  independent-translation locking certificates.
- `node scripts/check-chair44-assembly.mjs` verifies all complete pairwise
  extraction paths and simultaneous extraction, using continuous collision
  checks and elementary motion regression cases.
- The [exact contact and locking certificates](chair44-sliding-verification.json)
  list tile origins, contact normals, triangle witnesses and basis determinants.

These are separate geometric assembly audits. They do not alter the tiling
engine, its point-domain candidate graph, or its pruning rules.
