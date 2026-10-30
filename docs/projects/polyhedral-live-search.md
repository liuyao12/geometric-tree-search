# Polyhedral live search: coverage and conformance

The quasicrystal workspace supplies live Run, Step, Pause, Reset and exact JSON export for all eight concrete sets with exact carrier data. The Socolar–Taylor print mesh remains display-only at the user's request. Schmitt's compiler and decorated hierarchy entries are reference families, requiring a specified finite inventory before they define a search problem.

## Rule coverage

| System | Default search | Missing data or restriction |
| --- | --- | --- |
| Ammann | Existing supplied face-dot rules, exact point values and optional GCTS learning | Weak rule system; finite evidence does not certify infinite extension |
| Danzer ABCK | Both hands, whole facets, blue-edge reflection rule | Geometric face-obligation adaptation; optional unmarked control |
| Danzer compounds | Exact convex and nonconvex compounds, whole-facet attachments | Uses the source face-to-face formulation; finite patch only |
| Čulík–Kari cubes | All 21 transcribed label records, equal face-centre symbols | Fixed frame; documented source-transcription corrections remain, without an independent aperiodicity proof |
| Socolar–Steinhardt | Exact carrier geometry | Source face decorations not ported |
| Goodman–Strauss I/L | Registered periodic quarter-grid point control | Source boundary colours absent; registration is an explicit additional restriction |
| Goodman–Strauss connected variant | Registered periodic quarter-grid point control, both cross identities retained | Source boundary colours absent; registration is an explicit additional restriction |
| SCD | Finite layer-address search with three offset choices | Proper copies only; a restricted construction domain, excluding continuous sliding |

The two Goodman–Strauss entries and SCD also offer a strict whole-facet geometry control. This domain can exhaust immediately because it requires coincidence of complete recorded boundary facets and complete common boundary features. Such exhaustion does not rule out partial-facet, sliding, differently registered, or source-marked tilings. The original meshes retain their facet subdivisions; no claim of subdivision-invariant geometric completeness is made.

The [Danzer source](https://www.math.uni-bielefeld.de/~frettloe/papers/ikosa.pdf) specifies reflection across faces containing a right-angle edge and discusses the equivalent compound system. The Goodman–Strauss carrier formulas and missing marking functions are in [the source paper](https://www.math.ucdavis.edu/~deloera/MISC/LA-BIBLIO/trunk/Goodman2.pdf). The [SCD construction](https://www.math.uni-bielefeld.de/~frettloe/papers/scdart.pdf) describes screw layers and their sliding freedom.

## Exact domains

All geometric predicates and transformations use BigInt arithmetic in \(\mathbb Q(\tau)\), where \(\tau^2=\tau+1\). Rational geometry is the subfield with zero \(\tau\) coefficient. Floating-point coordinates are created only by the one-way rendering adapter. No display coordinates feed search identities, rotations, overlap decisions, point assignments or exports.

The generic geometric engine enumerates every reversed cyclic full-facet correspondence between congruent recorded facets, constructs its proper rigid map with exact matrix inversion, and checks every mapped vertex. Reflected inventories are explicit where permitted. The Wang model permits translations only, including in its unmarked control. Orientations need not form a finite global group: each complete full-facet attachment domain is finite.

Solid overlap uses exact polygon-plane splitting and BSP intersection volume for closed oriented meshes, including the nonconvex compound and carrier boundaries. Boundary intersections must be covered by complete common recorded faces, edges or vertices. Invalid or non-closed meshes are rejected. Resource interruption marks domains incomplete and returns unknown; it never turns a partially enumerated domain into a proved dead end.

The Goodman registered controls use a periodic cube with \(3\) periods per axis, side length \(6\), and \(24^3\) quarter-grid cells. L centres lie in \(2\mathbb Z^3\); cross and I centres lie in \((2\mathbb Z+1)^3\). Integer capacity \(3\) represents full cell weight \(1\) and the central I-pyramid share \(1/3\). The three axial I placements dissect one thin cross. These weights are faithful to this declared registration, not a general voxel approximation of arbitrary placements. Rendered representatives are unwrapped; the finite certificate covers a periodic point domain, not a Euclidean box with open boundary.

The SCD control uses \(a=(5,0,0)\), \(b=(3,4,0)\), \(c=(3/2,2,1)\) and

\[
R=\begin{pmatrix}3/5&4/5&0\\-4/5&3/5&0\\0&0&1\end{pmatrix},\qquad Rb=a.
\]

This active rotation is derived from the ridges of the actual carrier in the data file; the former recipe matrix used the complementary angle and has been corrected. Copies occupy the addresses \((i,j,k)\) with \(-1\leq i,j\leq1\) and \(-2\leq k\leq2\). Each inter-layer offset has three discrete choices. Mark-only components at exact auxiliary points require all copies to agree on the offset history. These address capacities encode the restricted layer construction; they are not a finite-support encoding of unrestricted solid placement. The tests independently check all solid pairs in a completed crop for zero interior overlap.

## Shared algorithm contract

Both new engines keep complete frontier-point/candidate incidences and apply global dead-end detection, then global forced moves, then earliest-generation branching. Candidate count only breaks generation ties. Explicit finite target obligations start at generation zero. The geometric engine instead introduces face obligations with their owner's generation. Both use exact reversible trails; removing one candidate updates every frontier obligation it covers. Point-marking dependencies include mark-only support outside tile bounds and distinguish assigned zero from a free component.

The finite point engine explicitly records every required point, including untouched points with zero assigned total. It checks residual integer capacity, retains partially filled obligations, and independently replays all totals and overlapping marking values before reporting finite completion. The geometric engine has no finite volume-capacity target and is labelled as a geometric adaptation, not the pure point-capacity baseline. No missing source rules are invented or described as learned. The GCTS learner remains connected to the Ammann supplied-rule oracle only; its saved fields cannot be applied to another set.

Snapshots and exports distinguish a viable finite checkpoint, complete finite registered target, fixed-root domain exhaustion and budget/unknown. Geometric exhaustion concerns the displayed attachment domain. Preparation time and search time are reported separately. Pause preserves the branch stack; changing systems or rules starts a fresh engine and discards stale snapshots by epoch.

## Verification

Run:

```sh
node scripts/test-polyhedral-live-search.mjs
node scripts/test-polyhedral-search-worker.mjs
node scripts/test-icosahedral-search-worker.mjs
node scripts/test-icosahedral-gcts-worker.mjs
node scripts/test-icosahedral-display.mjs
node scripts/test-aperiodic-polyhedra.mjs
```

The new tests cover analytic rational box volumes, large exact translations, full and partial boundary contacts, global dead/forced/generation priority, complete geometric frontier domains, exact rollback, both ABCK hands and reflection filtering, incomplete-domain budgets, residual point capacity, mark-only invalidation and rollback, all seven added worker models, source/unmarked switching, finite completion and exact export. Completed registered controls independently replay at 108 I/L tiles, 54 connected-variant tiles and 45 SCD tiles. Their solid interiors are checked pairwise with exact arithmetic. These are finite regression results, not infinite tiling certificates.
