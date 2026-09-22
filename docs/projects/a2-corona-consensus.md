# Extending a marking by corona consensus

## Question and precise construction

Can the markings glued over all possible neighborhoods of a tile share a larger
common marking, and can assigning that common part to the tile prune growth?
Yes: there is a finite local-consequence construction to test this directly.

Fix the tile system, lattice, transformations and an existing marking `m`.
For a fixed root tile, enumerate all compatible `k`-coronas. In this experiment,
two tiles are adjacent when their **positive t-supports meet**. A k-corona
contains tiles at contact distance at most k, fills every point supported by a
tile at distance less than k, and leaves at least one legal candidate at every
exposed point. Distances are recomputed from the complete patch, not inferred
from placement order. These are point-domain coronas, not polygon-intersection
or face-to-face coronas.

For each corona C, glue the placed copies of m into a partial section s_C. Define

> E_k(m)(p, component) = v if every corona assigns v there; otherwise `*`.

A missing assignment in even one corona makes that component free. Assigned
zero is a value, not absence. Keep the old root marking and transport the new
support with the same point-group action. The Turtle rank-3 action permutes
components and signs; the Hat rank-1 marking is a scalar invariant.

Every globally m-compatible tiling supplies one of these rooted coronas around
each tile. Consequently its glued marking must contain E_k(m) at every tile.
Adding E_k(m) therefore preserves those global tilings, **conditional on complete
corona enumeration and the implementation's exact point model**. This is stronger
than fitting sampled labels, but it is not an externally certified enumeration
proof, nor a proof that the original marking is redundant for unmarked tilings.

A finite viable corona can fail the extended marking at its boundary: the
extension also requires the boundary tiles to have their own k-coronas. Such a
failure is not a counterexample to the global implication. Incomplete enumeration
is different: its intersection can be too large and must remain a hypothesis.

## Completed enumerations

All rows use the known marking with extent 1 and allow reflections. Root
orientation and position are fixed; different coronas are deduplicated as sets
of placements. Counts are not symmetry-orbit counts. Values count assigned
components on **one prototype**, not all orientations.

| Tile / lattice | Rank | Corona | Complete coronas | Original values | Common values | Added values |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Turtle / index-3 | 3 | 1 | 73 | 39 | 102 | 63 |
| Turtle / index-3 | 3 | 2 | 618 | 39 | 191 | 152 |
| Turtle / index-3 | 3 | 3 | 3,005 | 39 | 327 | 288 |
| Turtle / full A₂ | 3 | 2 | 569 | 84 | 743 | 659 |
| Hat / index-3 | 1 | 2 | 679 | 18 | 113 | 95 |

The Hat 3-corona run stopped at 90 seconds: 1,331 coronas had been found after
58,053 placements. It is **incomplete**, and its apparent common values were not
promoted or benchmarked as an extension.

## Reducing the cost of the extension

The full common section is expensive to check. A greedy reduction retains every
original assignment and enough additional assignments to preserve **every pair
conflict** introduced by the extended marking. The check enumerates all relative
marking-support alignments, including contacts only in marking support outside
the tiles' positive t-support. It is not limited to the neighboring-pair training
catalogue. Any multi-tile disagreement is pairwise, so this reduction preserves
the marking's compatibility predicate for capacity-legal patches.

| Extension | Full values | Compact values | Compact points | Additional pair conflicts preserved |
| --- | ---: | ---: | ---: | ---: |
| Turtle index-3, 2-corona | 191 | 109 | 69 | 3,758 |
| Turtle index-3, 3-corona | 327 | 144 | 93 | 7,375 |
| Turtle full A₂, 2-corona | 743 | 274 | 153 | 13,352 |
| Hat index-3, 2-corona | 113 | 67 | 67 | 3,349 |

Pair counts fix the first orientation and include relative placements that meet
only through marking support. They are not counts of rejected growth nodes or
newly proved untileable unmarked pairs. The reduction is not a minimum-support
proof.

## Growth measurements

The benchmark runs the actual `solveA2Tiling` used by GCTS-I, with complete point
growth, a fixed root, reflections, and seeds 1, 3 and 10. Both arms use the
**original marking's candidate score**, so additional support changes legality
without adding a different score heuristic. Arm order alternates. Independent
point/marking/frontier replay checks every final patch.

### Turtle, index-3 lattice: compact 3-corona marking

Target: 300 tiles; limit: 20 seconds and 100,000 attempts per run. This final
comparison ran without concurrent experiment jobs.

| Seed | Known marking | Extended marking | Attempts: known → extended | Backtracks: known → extended |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 14.00 s; 300 tiles | 11.22 s; 300 tiles | 883 → 496 | 584 → 197 |
| 3 | Unknown at 20 s; 154 tiles | 12.54 s; 300 tiles | 2,094 → 632 | 1,944 → 333 |
| 10 | 13.53 s; 300 tiles | 10.33 s; 300 tiles | 877 → 471 | 578 → 172 |

The table reports search time; independent replay adds roughly 28–60 ms per
run and is recorded separately.

The two completed baseline runs used about 1.25× and 1.31× as much search time.
The timeout gives a lower bound, not an exact baseline completion time. These
are three bounded runs, not a general speedup guarantee.

**Preparation matters:** deriving the 3-corona intersection took 84.26 seconds
in the recorded run, with other enumeration jobs active; compaction took 0.62
seconds. The growth timings above reuse that field and exclude derivation.
A single cold comparison does not establish an end-to-end speedup. The initial
uncompacted 2-corona experiment also reduced attempts on two seeds but was slower
at a 100-tile target; one seed used more attempts. Stronger pruning is not
monotone improvement in wall time or in a heuristic's chosen path.

### Other systems

For the Turtle on full A₂, the compact 2-corona extension reached 100 tiles in
all three runs, reducing attempts from 256 to 168 and backtracks from 157 to 69.
However it took about 8.1–8.6 seconds versus 3.8–3.9 seconds for the original:
checking 274 values instead of 84 outweighed the smaller tree. No speed gain is
established there.

For Hat on index-3, both markings timed out on all three 100-tile runs at
10 seconds. The original reached 86/94/94 tiles and the extension 86/89/89.
All 679 enumerated 2-coronas remain compatible with the extension and retain a
viable frontier, but no growth benefit was established.

All raw aggregate rows are in [the JSON summary](../../data/a2-corona-consensus-2026-09-21.json).
The main result is a useful Turtle index-3 example; it must not be generalized
to all Hat/Turtle lattices or to unmarked tilings.

## Replay and boundaries

All 3,005 Turtle index-3 3-coronas satisfy the original marking and viable-frontier
criterion. Applying the extension to every tile leaves 2,996 internally
compatible, of which 1,782 retain a viable frontier under the extension.
The 9 internal failures occur between extended fields of boundary tiles; they
cannot belong to a global tiling with the original marking. Every returned
300-tile benchmark patch passes both original and extended marking checks.

For Turtle index-3 2-coronas, all 618 remain internally compatible and 514 retain
extended frontier viability. For full A₂ 2-coronas, the corresponding counts are
569/569 and 490/569. This separates root consensus from the stronger condition
that every tile in a finite patch can carry the same extension.

Tests independently enumerate the Turtle one-corona using plain maps and a
different branch order, reproduce all 73 patches, check exact 1–3-coronas of a
tiny line system, and independently reconstruct the glued sections and common
intersection of the supplied completed catalogues. Cutoffs cannot be promoted.
No external SAT/UNSAT certificate or infinite geometric tiling proof is claimed.

## Reproduce

```sh
node scripts/experiment-a2-corona-consensus.mjs \
  --tile=turtle --rank=3 --lattice=index3 --radius=3 \
  --ms=180000 --nodes=1000000 --solutions=100000
node scripts/compact-a2-corona-consensus.mjs \
  /tmp/a2-corona-consensus/turtle-r3-index3-c3.json
node scripts/benchmark-a2-corona-consensus.mjs \
  --input=/tmp/a2-corona-consensus/turtle-r3-index3-c3-compact.json \
  --target=300 --ms=20000 --nodes=100000
node scripts/test-a2-corona-consensus.mjs \
  /tmp/a2-corona-consensus/turtle-r3-index3-c3.json
```

Generated assignments and corona patches remain outside the repository in the
chosen output directory. The repository contains the experiment code, aggregate
measurements and this report. No derived marking is bundled into GCTS-I, and its
browser-local marking library is unchanged.
