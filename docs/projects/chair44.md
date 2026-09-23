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
