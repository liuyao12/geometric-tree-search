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

For a large census, `--stop-after=periodic` writes the cheap exact periodic
classification without launching an isohedral or corona search on every miss.
Feed only its unresolved rows into the next stage with `--input-report`;
`--stop-after=isohedral` similarly stops before the corona search. This makes
the certificate-cost funnel resumable and prevents expensive lanes from being
run on shapes already eliminated by a smaller exact quotient. When the HNF
torus pass is intended to be exhaustive at the current copy bound,
`--box-screen=false --general-periodic=false` avoids redundant constructive
fallbacks and produces a clean input pool for the next motif-size shard.
`--report-chirality=false` skips mirror classification on intermediate rows;
chirality can be computed only for the much smaller final survivor pool.
If a periodic shard mixes completed misses with budget stops,
`--input-stopped-by=time_limit` replays only the latter, while
`--input-stopped-by=exhausted` advances only shapes whose current copy range was
fully checked. This prevents a timed-out two-copy search from being silently
skipped when the next shard starts at three copies. Comma-separate multiple
paths in `--input-report` to consume a sharded census without first rewriting
its receipts.

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

The complete one-sided volume-nine census contains 48,311 polycubes. The first
pass certified 48,260 as periodic: 20,238 with one-copy motifs, 26,922 with
two, 309 with three, 731 with four, and 60 with six. A complete HNF pass through
eight copies then certifies `p9-43172` and `p9-43188`, bringing the periodic
count to 48,262 and the bounded-inconclusive count to 49. Their 8-copy quotient
has period vectors `(3,0,0)`, `(0,8,0)`, `(0,0,3)` and partitions all 72 quotient
cells under an independent Cramer's-rule verifier.

The original four catalogue entries are two enantiomeric pairs:
`p9-42947`/`p9-42969` and `p9-43172`/`p9-43188`. Because reflection of all of
space preserves tiling existence, one representative per pair is sufficient
even though reflected copies remain forbidden within a tiling. The catalogue
therefore moves `p9-43172` to periodic controls and keeps only `p9-42947` as an
unresolved free-polycube representative. It exhausts all 169,511 HNF quotients
for every motif size from one through thirteen copies and has an exact
radius-four corona. This includes all 130 one-copy HNFs; the earlier cyclic
one-copy preflight alone was only sufficient, not exhaustive. The resumed exact
search eliminated copy counts 9–12 independently, without replaying the
already exhausted smaller motifs; its receipt is
`data/polycube-volume9-periodic-through13-2026-08-20.json`. A 30-second exact
radius-five run visited 2,574,336 nodes without completing, while a separate
continuation portfolio rejected 7,387 complete radius-four patches because
each immediately trapped before radius five. That portfolio did not exhaust
all radius-four patches, so this remains a GCTS stress candidate, not evidence
of aperiodicity. The deeper machine-readable receipt is
`data/polycube-volume9-deep-screen-2026-08-20.json`; the earlier six-copy
summary is retained as historical input.

The volume-ten census contains 346,543 proper-rotation classes, with canonical
key digest `1754dfee…c77e1ad`. A gap-checked eight-shard HNF pass plus a separate
retry of every initial budget stop certifies 112,531 one-tile and 210,113
two-tile quotients. The other 23,899 shapes each exhaust all 217 one-copy and
1,085 two-copy HNF bases with no remaining timeout. They are only the input to
the next independently budgeted copy-size screen, not aperiodic candidates.
The machine-readable receipt is
`data/polycube-volume10-periodic-through2-2026-08-20.json`.

An independently budgeted three-copy pass then certifies 905 more periodic
tiles. Every positive certificate is replayed by the separate Cramer's-rule
quotient verifier. After retrying every wall-clock stop, the remaining 22,994
shapes each exhaust all 2,821 three-copy HNF bases, in addition to the 1,302
smaller bases already exhausted. These are the exact inputs to the four-copy
screen—not claims of aperiodicity. The gap-free cumulative receipt is
`data/polycube-volume10-periodic-through3-2026-08-20.json`.

The continuation solver now extracts a proof-relevant reason from a trapped
patch instead of memoizing the entire boundary. For a radius-five target cell,
it enumerates every root-compatible tile placement through that cell and finds
a small hitting set of already fixed radius-four placements that blocks all of
them. That hitting set is a sound nogood for every outer patch containing the
same placements. In the first witness only two fixed tiles block all 72 ways to
cover `(0,-3,-1)`. Four seeded outer searches transferred these clauses by
exact placement keys, accumulated 6,573 clauses (average final size 3.94,
maximum 7), and pruned 4,949,332 branches after only 54 full continuation
checks. No radius-five witness appeared, but the outer search did not exhaust;
the result therefore remains inconclusive. See
`data/polycube-volume9-continuation-nogoods-2026-08-20.json`.

The same proof mechanism now resolves conflicts through a nontrivial
continuation subtree. A child failure clause contains its trial placement;
removing that placement after every branch has failed and unioning the residual
conditions proves the parent pivot impossible. Repeating this process at the
fixed-patch root yields an outer-only clause. A six-cube regression requires
two exact-cover nodes before producing a three-placement outer conflict, and a
fresh search with only those three fixed placements exhausts independently.
No conflict is returned after a node or time limit. The currently sampled
`p9-42947` radius-four failures are still immediate conflicts, so this improves
the general GCTS proof engine without changing that candidate's classification.

A first-corona forcing audit then tested whether the candidate exhibits a local
seed for hierarchical structure. Naive depth-first enumeration was misleading:
four placements occurred in all 959,539 sampled coronas. Exact probes forbidding
each placement immediately found valid alternatives. Testing every placement in
a legal nine-tile baseline corona likewise found nine of nine replaceable; an
independent checker verified every alternative's congruence, non-overlap,
forbidden-placement absence, and target coverage. Since any individually forced
placement would occur in the baseline, none exists at radius one in this fixed
frame. This does not exclude forced choices among placement sets, adjacency
types, or larger supertiles. See
`data/polycube-volume9-corona-forcing-2026-08-20.json`.

The contact-type quotient reveals the first positive structural constraint.
There are 605 root-compatible placements and 69 contact types after quotienting
by the root stabilizer. A cutting-plane loop alternated exact minimum hitting
sets with independently verified GCTS counterexample coronas. The first
four-type obstruction was merely the complete list of ways to cover one target
cell, so all 11 such single-cell clauses were excluded. After 92 corona
constraints, the minimum admissible hitting-set size reached six; forbidding
those six types (36 placements) exhausts the exact first-corona search in four
nodes across eight tie-order seeds. Thus every first corona realizes at least
one of six contact states, and no smaller non-single-cell contact disjunction is
possible. This is a genuine local relation, but it has not yet been propagated
between neighboring roots or organized into a substitution hierarchy. See
`data/polycube-volume9-contact-disjunction-2026-08-20.json`.

Renormalizing the neighboring tile as root gives the directed reciprocal graph
for those six states. Nine of the 36 active placements remain active at both
ends: type 3 reverses to 44, type 44 reverses to 3, and type 29 reverses to
itself. The remaining active contacts reverse to types outside the six-state
set. Fixed representatives of both reciprocal cycles survive exact radius-four
searches: `3↔44` reaches 74 placements after 283,688 nodes and `29↔29` reaches
66 after 77,074 nodes. Thus the local disjunction admits stable finite dimers
and does not itself force a hierarchy. See
`data/polycube-volume9-contact-propagation-2026-08-20.json`.

Conditioning on complete first-corona exteriors is considerably more selective
than conditioning on one contact. Canonicalizing exterior occupancy under the
root stabilizer gave 2,522 distinct states across four 1,000-corona seeded
samples. Exact fixed-boundary searches proved that 1,922 cannot reach radius
two; 600 have independently verified radius-two extensions, and repeated
states agreed across seeds. No continuation needed more than 41 exact-cover
nodes. In a separate learned traversal, 2,070 explained failures produced
2,089 clauses and 41,824 prunes. The portfolio now memoizes these canonical
obstructed boundary states as well as learning exact placement clauses. A
shallow-clause transfer ablation did not improve the radius-four path, so the
solver retains on-demand lookahead rather than paying that preload cost. The
census is still sampled and therefore does not resolve tiling or aperiodicity.
See `data/polycube-volume9-corona-boundary-states-2026-08-20.json`.

Deeper boundary sampling makes the proposal-selection problem explicit. The
first 400 radius-two states across four unlearned traversals all fail before
radius three, despite the known radius-three witness. On-demand clauses shift
a later 1,000-state traversal to 462 survivors. The analogous radius-three to
four run remains trapped: 41 sampled states all fail and the outer search makes
10,100,253 nogood prunes in 30 seconds without reaching a survivor, even
though an independent direct search has a verified radius-four corona. This
separates geometric nonexistence from a reproducible, measurable ordering
failure that future GCTS proposal policies must beat.

The first replacement policy is a bounded direct-depth proposal. Before
enumerating lower-radius leaves, it asks the next-radius exact solver directly;
a witness jumps forward, while an incomplete run contributes only sound exact
nogoods to the fallback continuation portfolio. This solves the held-out
radius-three-to-four benchmark in 4,786 nodes and 139 ms under a one-second
cap, with an independent witness check. It does not solve radius five: at an
equal twelve-second total budget, a two-second direct proposal plus ten seconds
of outer search covers less of the tree than the twelve-second baseline and
finds no witness. The phase is therefore available as an explicit option but
is not enabled by default.

The adaptive proposal profile uses a 250 ms pilot. It retains the 129 ms
radius-four escape and, when radius five remains incomplete, falls back while
preserving 98.2% of equal-budget node coverage. This is a bounded compromise,
not a radius-five improvement. Coherent symmetry closure of whole nogood
clauses was also exact but ineffective: at one million outer nodes it added
1,820 root-stabilizer images without changing depth or continuation checks and
with essentially unchanged time and pruning. The option remains available for
controlled comparisons but is disabled by default.

## Next engineering milestones

1. Persist the full volume-nine NDJSON certificate receipts, not only their
   checked-in summary, in a compact replayable format.
2. Minimize resolved subtree clauses and add proof traces that replay each
   resolution step, not only the final independently checked outer conflict.
3. Continue the dedicated HNF exact-cover search beyond thirteen-copy motifs;
   the range-resume option now avoids repeating exhaustively checked sizes and
   the one-copy range now covers non-cyclic quotient groups too.
4. Use successful isohedral coronas to propose, rather than assume, larger
   finite quotients.
5. For durable survivors, search for recurring supertiles and verify a forced
   substitution grammar on every legal corona type. For `p9-42947`, condition
   on the incoming non-active reciprocal states and test whether their required
   outgoing six-state choices form only finite cycles or support unbounded
   state paths.
