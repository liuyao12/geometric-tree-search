# Search protocol for a 3D aperiodic polycube

## Mathematical target

The target is one connected finite union of unit cubes in `Z³` that tiles
three-space but admits no tiling with a nonzero translational symmetry. This is
much stronger than exhibiting one nonperiodic substitution tiling: the 3D
chair does that, but also has periodic tilings.

The single-polycube problem in dimension three appears to remain open. The
high-dimensional periodic tiling conjecture is false, but that construction
does not currently supply a `Z³` polycube monotile. By contrast, translational
tiling of `Z³` by a set of three polycubes is already undecidable.

Primary references:

- Greenfeld and Tao, [A counterexample to the periodic tiling conjecture](https://annals.math.princeton.edu/2024/200-1/p02).
- Yang and Zhang, [On the Undecidability of Tiling the 3-dimensional Space with a Set of 3 Polycubes](https://arxiv.org/abs/2508.00192).
- Socolar and Taylor, [An aperiodic hexagonal tile](https://arxiv.org/abs/1003.4279), including a three-dimensional geometric realization of its matching rules.

## Why isohedral is a lead, not a separate certificate

An isohedral tiling has a symmetry group acting transitively on its tiles. For
a bounded tile in Euclidean three-space this action is discrete and
cocompact, hence crystallographic; its translation subgroup has finite index.
Thus an actual isohedral tiling is periodic. A short isohedral-looking patch is
useful because it points the periodic-cell search toward a promising local
rule, but it does not by itself prove that the rule extends infinitely.

## Certificate-cost funnel

1. **Cheap constructive witnesses.** Try one-copy quotient homomorphisms and
   small exact box fills first. A box fill is repeated by its three side
   vectors, so it is already an infinite periodic certificate. The checker
   also enumerates the box lattice's affine cubic symmetries; if their action
   on the motif is transitive, it records the stronger (overlapping)
   isohedral certificate. Direct face-pairing, prism, layered, and verified
   inflation/reptile templates are further cheap families to add. Any
   successful construction proves that the candidate tiles.
2. **General periodic certificate.** Search finite quotients of `Z³`, represented by
   Hermite normal forms, for an exact cover by oriented copies. A hit proves a
   periodic infinite tiling and eliminates the candidate.
3. **Finite extension obstruction.** Anchor one copy and exhaust all legal
   patches through a complete adjacency-corona depth. If no branch reaches the
   requested layer, no infinite tiling can contain the anchor. For a single
   prototile, cubic symmetry makes this a non-tiling certificate.
4. **Unresolved survivor.** A candidate that passes both bounded searches may
   tile only with a larger period, may fail at a deeper corona, or may be
   genuinely aperiodic. No one of these possibilities is favored merely by
   survival.

The two positive semi-decisions—enumerating periodic cells and enumerating
larger legal patches—should be dovetailed with the negative finite-obstruction
search. A genuine aperiodic candidate needs both an explicit infinite tiling
construction (normally a forced hierarchy) and a proof excluding every
periodic tiling.

For polycubes, the first obstruction pass bypasses polyhedral face/solid-angle
bookkeeping. It treats unit cubes as an exact-cover problem, chooses the most
constrained uncovered root-boundary cell, and memoizes failed occupied-cell
states. The capped 8-ring decacube is rejected at the root because its central
cell has no legal covering placement. The ordinary planar 8-ring, by contrast,
does have a first corona and therefore correctly survives this shallow test;
its known non-tiling obstruction lies deeper.

## Reproducible first pass

```bash
node scripts/test-polycube-enumerator.mjs
node scripts/screen-3d-aperiodic-polycubes.mjs \
  --size=6 \
  --box-max-tiles=4 \
  --periodic-max-tiles=4 \
  --obstruction-layer=1 \
  > runs/polycubes-volume6.ndjson
```

Searches use proper rotations by default. `--include-reflections=true` changes
both enumeration and placement semantics. Every output row includes the
canonical voxel key, coordinates, chirality, budgets, and proof-strength
classification so a survivor can be replayed exactly.

The `easy_witness.isohedral_certificate` field is a proof about the infinitely
repeated box motif. The later `isohedral.patch_found` field is deliberately
only a search lead: it reports a reusable finite corona and cannot eliminate a
candidate until an exact space-group or quotient certificate is reconstructed.

Replay a single row without enumerating its whole volume class:

```bash
node scripts/screen-3d-aperiodic-polycubes.mjs \
  --key='0,0,0;0,0,1;0,1,0'
```

## Baseline census (August 2026)

The proper-rotation (one-sided) census through volume eight gives:

| Volume | Candidates | Exact periodic | Remaining |
| ---: | ---: | ---: | ---: |
| 1 | 1 | 1 | 0 |
| 2 | 1 | 1 | 0 |
| 3 | 2 | 2 | 0 |
| 4 | 8 | 8 | 0 |
| 5 | 29 | 29 | 0 |
| 6 | 166 | 166 | 0 |
| 7 | 1,023 | 1,023 | 0 |
| 8 | 6,922 | 6,921 | 1 |

For the 6,921 periodic octacubes, the first certificates found use 4,611
one-tile, 2,291 two-tile, 5 three-tile, 13 four-tile, and 1 six-tile motifs.
The sole remainder is the planar `3×3` ring with its center removed. The new
bit-mask exact-cover solver shows that it has complete coronas through radius
three (12, 28, and 46 neighboring copies in the first witnesses). Radius four
remains bounded-inconclusive. This makes the ring a useful negative-search
stress case, but does not establish whether it tiles space.

The complete one-sided volume-nine census contains 48,311 polycubes. Exact HNF
quotient searches certify 48,260 as periodic: 20,238 with one-copy motifs,
26,922 with two, 309 with three, 731 with four, and 60 with six. No finite
non-tiling certificate was found; 51 remain bounded-inconclusive, including 23
that timed out in the shallower four-copy pass. Of the 28 deep-pass survivors,
eight exhaust every HNF through six copies. The catalogue retains four
nonplanar members (`p9-42947`, `p9-42969`, `p9-43172`, and `p9-43188`) that
also have exact radius-three coronas and leave radius four incomplete at the
two-second bound. They are GCTS stress candidates, not aperiodic candidates in
the evidentiary sense. The machine-readable summary is
`data/polycube-volume9-screen-summary-2026-08-20.json`.

## Next engineering milestones

1. Persist the full volume-nine NDJSON certificate receipts, not only their
   checked-in summary, in a compact replayable format.
2. Canonicalize rooted boundary states under translations and cubic rotations,
   then memoize exhausted subtrees.
3. Extend the dedicated HNF exact-cover search beyond six-copy motifs with DLX
   or SAT and independently verify every stored quotient.
4. Use successful isohedral coronas to propose, rather than assume, larger
   finite quotients.
5. For durable survivors, search for recurring supertiles and verify a forced
   substitution grammar on every legal corona type.
