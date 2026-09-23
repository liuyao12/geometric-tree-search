# Chair44 on the 3D reptiles page

Implemented September 23, 2026. Source: Chaim Goodman–Strauss,
[Notes on a strongly aperiodic monotile in \(E^3\)](https://arxiv.org/abs/2609.24779),
September 21, 2026, Figures 2 and 5 (CC BY 4.0). The original Chair44 construction
is due to [Ioannis Tsiokos](https://arxiv.org/abs/2609.19214).

## Decoration and inflation

`3d-reptiles/chair/chair44.js` transcribes the 24 arrows from the folded net in
Figure 5. Its full central square is the face at \(z=0\); the removed cube has
lower corner \((1,1,1)\). The other five outer faces follow the net folds.
The three socket arrows follow the paper's translated front-socket/back-corner
fit, reversing red and green while retaining blue. There are eight arrows of
each color. An arrow's color and tangent vector are both significant.

The renderer draws this marked version, not the microscopic pyramid geometry
of the original shape-only construction. The prototype admits 24 distinct proper
cubic rotations. Inflation composes full rotation matrices, never coordinate
reflections chosen solely from a missing corner. The child rotations are
obtained by checking the eight geometric children against both internal arrow
contacts and inherited parent-corner arrows. Retained-copy expansion preserves
the full marked patch. This finite construction check is separate from search.

## Point model and search contract

The declared ambient domain contains integer cell indices and doubled-coordinate
unit-panel centers as separate channels. At each of the seven occupied cell
indices, \(t=1\); elsewhere \(t=0\). Arithmetic and comparisons use exact small
integers. A panel contributes a marking at
\[
 p=2c+(1,1,1)+n,\qquad m(p)=(a,\sigma n),
\]
where \(c\) is its incident occupied cell, \(n\) its outward unit normal,
\(a\) its diagonal tangent arrow, and \(\sigma\) is \(1\) for red,
\(-1\) for green, and \(0\) for blue. Proper rotations act on both vector
components. Equality of these six-component values encodes aligned blue/blue
and red/green contacts; blue's zero is an assigned value, not missing.

`chair-gcts.js` starts from one tile and allows every integer translation of
all 24 proper rotations of that same prototile, without multiplicity limits.
Every empty face-neighbor cell is an active obligation. New obligations take
the minimum generation of their incident placed neighbors; a placement takes
one plus the minimum existing obligation generation on its support. The seed
has generation zero. Continuing earliest-generation growth would expand the
active domain outward; automatic running pauses every 64 placements, Apply one can continue, and the demo makes no claim
to cover the infinite domain.

For every active point, all seven positive-support alignments of every rotation
are enumerated. One candidate node is shared by all its incident frontier
points. Occupancy or marking conflicts anywhere discard it everywhere. The
whole graph is checked for dead points, then singleton points, before branching
at the earliest generation (degree breaks generation ties). Branch alternatives
and complete placement/generation snapshots supply rollback. Markings are fixed
problem-defining data, not learned restrictions or a redundant pruning theorem
for the unmarked chair. No inflation witness, parent address, collar inventory,
known neighbor list, or precomputed plan is passed to the search.

## Evidence and limits

Run `node scripts/test-chair-gcts-growth.mjs`.

- An independent occupancy/contact verifier checks colors, opposite normals,
  and tangent arrows without calling the production marking encoder.
- Exhaustive translation/rotation enumeration gives exactly 44 face-adjacent
  neighbors. The seed's full candidate graph equals that independently found set.
- Both directions of point/candidate incidence are checked.
- Levels zero through three cover exactly the expected enlarged chair, without
  gaps, overlaps, or mismatched internal panels (up to 512 tiles).
- All 24 parent orientations and all seven outer retained-child choices preserve
  the child's full rigid transform.
- Search reaches a consistent 64-chair finite patch: 59 forced placements,
  four branch decisions, zero backtracks. The entire remaining frontier is viable.
- Global dead/forced/generation precedence has explicit adversarial tests. A
  legal two-chair patch with a dead frontier exercises branch backtracking and
  independent replay of the recovered patch.
- User undo restores the complete preceding state, including branch alternatives
  and generations. Desktop/mobile browser checks exercise inflation, mode
  switching, local growth, rotation selection, and the marking toggle.

The graph is fully rebuilt after each placement; only immutable candidate
geometry is cached. This is correct reference scheduling, but does not implement
the contract's incremental dependency-index optimization. This page is not a
performance benchmark or an independently formalized proof of aperiodicity.
The search selects one handedness with proper rotations. It does not enumerate
mixed-handed partial patches or certify their lack of infinite extension.
The paper supplies the infinite hierarchy and strong-aperiodicity argument.

Apply one and Apply inflation are both visible. They select the local-growth or
nested-inflation view respectively and retain separate histories. Run pauses at
each 64-chair checkpoint; Apply one continues from the verified patch.

The translucent renderer retains all 24 arrows per tile, including both marked
sides of tile-to-tile contacts. Frontier-only marking lists remain search/status
data and do not determine which arrows are drawn. Local growth and undo share
the inflation view's fixed seed coordinate frame. Apply one preserves the orbit
target and viewing direction, moving the camera backward only when the patch
would leave the padded view. Undo does not automatically zoom back in.


Chair44 is now served directly at `/3d-reptiles/`. The old `/3d-reptiles/chair/`
address redirects there, retaining query and fragment. Quaquaversal has its own
page at `/3d-reptiles/quaquaversal/`, reusing the existing prism assets.

The orientation display has eight permanent nodes, indexed by the missing-corner
direction. Every node groups three decorated rotations; this is a visualization
quotient only, and the engine still allows all 24 proper rotations. All three
coordinate quarter-turn generators and all tile rotations have determinant
\(1\); reflections are not included. The second inflation already uses all
24 decorated orientations.

`orientation-graph.js` builds the undirected simple rotation-action graph from
those three proper generators, giving 12 edges and degree three at each node.
It is a Schreier graph on the eight directions (the underlying graph is a cube),
not an assertion that these eight directions are a subgroup of rotations.
Tests verify generator orthogonality and determinant, every edge's rotation
witness, and the three-to-one grouping. Both construction views keep all eight
nodes visible, with absent directions faded and tile counts controlling size.

Local steps (including Run and Undo) replace the rendered patch in one frame at
its normal opacity; only a necessary camera dolly is animated. Inflation keeps
its existing cross-fade. Pause stays enabled during automatic steps and cancels
the single pending step timer. Browser regression checks cover pause during a
camera transition, pause between steps, rapid resume, checkpoint stopping, and
reduced-motion mode. The solver and its decision/rollback semantics are unchanged.


## Scalar lattice realization

The compact panel value already used by the local search is \(m=(a,b)\),
where \(a\) is the tangent arrow vector and \(b=\sigma n\), with
\(\sigma=1,-1,0\) for red, green, blue. On a shared panel, the outward normals
are opposite. Equality of \(b\) is therefore equivalent to blue/blue or
red/green, and equality of \(a\) imposes the arrow direction.

`chair-lattice.js` expands this into a scalar, pure-pullback point marking.
Use the ambient lattice \(\mathbb Z^3\), with physical unit length \(12\),
occupancy obligations on \((6,6,6)+12\mathbb Z^3\), and translations by
\(12\mathbb Z^3\). Each occupied cube indexed by \(c\) has
\(t(12c+6\mathbf1)=1\); all other values of \(t\) vanish.
At each boundary panel center \(P=12c+6\mathbf1+6n\), set
\[
 m(P+d)=a\cdot d,\qquad m(P+2d)=b\cdot d,
 \quad d\in\{\pm e_1,\pm e_2,\pm e_3\}.
\]
This gives 288 scalar assignments per tile, with alphabet \(\{-1,0,1\}\).
Zero is assigned and constraining; all unlisted marking values are absent.
Distinct panel centers differ by at least six in some coordinate, while each
stencil lies within two steps of its center. Thus stencils at distinct panels
are disjoint for every allowed placement, including edge-only and corner-only
contacts. At a common panel the stencil equality recovers exactly both vectors.
This proves equivalence of scalar matching and the original arrow test on every
capacity-legal partial patch, not only on the tested examples.

A proper rotation \(R\) acts on prototype points by
\(p\mapsto R(p-12\mathbf1)+12\mathbf1\), followed by an allowed translation.
It permutes the signed coordinate directions. Since
\((Ra)\cdot(Rd)=a\cdot d\), scalar values need no sign change or channel action:
only their locations move. The downloadable `chair44-lattice.json` contains the
7 occupancy values, 288 marking values, transformation matrices, required
occupancy sublattice, and explicit missing/zero semantics.

`node scripts/test-chair-lattice.mjs` verifies every proper rotation by scalar
pullback, all 864 facing-panel direction/color combinations, all 3000 relative
orientation/translation cases in the radius-two cube, the same 44 adjacent
neighbors, and inflation patches through 512 tiles. The point verifier does not
call the production compact matching encoder. The search keeps its equivalent
compact panel representation, avoiding a twelvefold expansion of the marking
support. No search policy or geometric pruning is added. This is an exact known
encoding of the supplied arrow problem, not evidence of learned discovery or
of redundancy for the unmarked chair. It can serve as an independent control
when testing marking synthesis.

## Undo actions and returning to inflation

A Run click records its complete starting growth state. All steps until Pause,
completion, or another action share one UI undo entry, restoring placements,
branch stack, counters, generations, checkpoint target, and prior history.
Resuming starts a new undoable Run action. Apply one keeps its own single-action
undo entry; solver branch rollback remains separate from these UI groups.
Undo may interrupt an active Run, cancelling its queued step and camera motion.

From local matching, Apply inflation cancels Run and displays the existing saved
inflation state without expanding it. A subsequent click advances inflation.
Returning is permitted even at the maximum inflation level. Local and inflation
states retain their separate histories.

## Arrow and scalar-value display

The marking toggle selects either the arrows or the actual scalar lattice
marking from `chair-lattice.js`. `lattice-visual.js` places points at the exported
lattice coordinates divided by 12, in the same fixed tile frame as the arrows.
Negative values use purple diamonds, zero values use hollow gray circles, and
positive values use teal discs. Assigned zeros are rendered; absent points are
not. Coincident agreeing assignments are drawn once, retaining an assignment
count, so touching tiles never erase their shared marking.

Point geometry is built only when requested, then retained for toggling. The
choice persists through inflation, local steps, Run, Undo, and mode changes,
including a toggle during a visual transition. This is a display choice only;
it does not change the point model or search state.

`node scripts/test-chair-marking-view-browser.cjs` checks every displayed point,
value, and shared-assignment count against the scalar model for single tiles,
a supertile, and local growth; it also exercises transitions, grouped Run undo,
returning to inflation, the legends, and mobile layout.


## Rank and colored relief

The expanded lattice marking has rank one: each marked lattice point carries
one scalar value. Its larger spatial support replaces the six components of
the compact face-center encoding. This is a statement about the refined
lattice model, not a claim about minimum support on the original lattice.

The Relief display implements a concrete version of the bumps/nicks recipe in
[Goodman–Strauss, Section 2](https://arxiv.org/html/2609.24779v1#S2).
It is not a reproduction of Tsiokos's numbered microscopic pyramids.
Each red panel has a shallow square pyramid, each green panel its recessed
counterpart, and each blue panel a pair with opposite heights on opposite sides
of the arrow diagonal. The colored faces are the actual sides of those bumps
and recesses. Their footprints are cut out of the neutral tile surface; the
original flat body is hidden only while Relief is selected. Translucent bodies
and lower-opacity reverse faces retain the view of back and shared markings.

Use local coordinates \(u\) along \(a\times n\) and \(v\) along \(a\), normalized
in the panel. For opposing normals and aligned arrows, the coordinates transform
as \((u,v)\mapsto(-u,v)\). The blue height profile satisfies
\(h_B(-u,v)=-h_B(u,v)\), and the red/green profiles satisfy
\(h_G(-u,v)=-h_R(u,v)\). Their asymmetric offset along \(v\) records the arrow's
direction. Each pyramid has height magnitude \(0.12\); all footprints stay
strictly inside their unit panels. There are \(16\) protrusions and \(16\)
recesses, with zero net volume change.

`node scripts/test-chair-relief.mjs` compares exact pyramid bases and tips for
all \(864\) facing-panel combinations, checks all \(24\) proper rotations,
and verifies the signed-volume balance. The browser test checks that the mesh
is closed with consistently oriented edges and volume \(7\), and checks a
supertile's volume, display toggles, growth, grouped undo, and mobile layout.
Collinear triangulation edges between the two blue cutouts are subdivided so
there are no mesh T-junctions.

The equality test remains the search's rule; this display does not introduce
mesh-intersection pruning. Its checked equivalence concerns the allowed
unit-grid face contacts. It is not a separate certification of the fabricated
shape under arbitrary continuous placements.
