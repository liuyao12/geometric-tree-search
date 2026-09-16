# Learning point markings for the three article tile sets

`GCTS-I.html` now has **Tiling** and **Learn markings** views in the same floating
panel. The second view embeds the independent `GCTS-learning.html` page. The
article's final Geometric Deep Learning section links to it without a second
in-article canvas. Entering the Geometric Deep Learning section automatically
selects Turtle, opens the learning view and starts a fresh collection once per
page visit. A pending-start handshake handles an iframe that has not loaded yet.
Manual tab changes, pauses, resizing and further scrolling do not restart it.
Learning can continue while the tiling view is visible.

## Inventories and learned results

Each model is learned separately from unmarked extension searches; the known
Turtle marking is never supplied to this learner. All collected positive and
negative outcomes are used, with no held-out split. The current recorded runs
use seed 90210, target 12 tiles and 120 attempted placements per connection.

| Tile set | Symmetries per tile | Connections | Extended | Exhausted | Unknown | Failures separated by code |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Turtle only | 12, including reflections | 304 | 39 | 263 | 2 | 236 |
| Hat only | 12, including reflections | 320 | 40 | 279 | 1 | 262 |
| Turtle + Hat | 6 rotations; no reflections | 624 | 69 | 554 | 1 | 501 |

The mixed inventory includes both same-type and cross-type connections. Both
root tile types are enumerated. These are ordered, rooted connections; symmetry
or exchange can relate different rows, so the count is not an orbit count.
Each possible second placement has positive t-support touching the root and
respects point capacity. Whole successful patches are deduplicated under the
allowed symmetry group and translations, preserving tile identity.

Turtle yields 35 unique patches, 9 equality classes and 85 nonzero entries out
of 168 assigned channels. Hat yields 36 patches, 6 classes and 76/150 nonzero
entries. The mixed model yields 60 patches, 11 classes and 318/318 nonzero
entries across the two prototypes. Recorded collection times were approximately
26.6, 21.3 and 51.4 seconds respectively; timings include yielding and incremental
encoding. They are not acceleration benchmarks.

A separate marked growth check at seed 701, target 24 and budget 2000 reached
24 tiles for each model (23, 129 and 696 attempted placements respectively).
The mixed check contains both tile types and no reflected placements. These
are finite consistency checks, not infinite-tiling certificates or prediction
scores. Full evidence and the marked check are in
`assets/data/tile-connections-{turtle,hat,mixed}.json`; the small
`assets/data/tile-markings.json` contains models for the main panel.

Regenerate with:

```
node scripts/train-tile-connection-markings.mjs /tmp/three-tile-markings
```

## Encoding and result transfer

For each prototype, the domain is its positive t-support plus one nearest-neighbor
A₂ step, with three assigned scalar channels at every site. Locations and tile
values remain fixed. Point/channel variables from all retained extension
witnesses are equated on overlap. A signed union-find solves the equations;
odd sign cycles force zero, and free classes receive distinct integer magnitudes.
Under a symmetry, channels permute and values acquire permutation-parity sign.
Assigned zero is not missing. The mixed learner shares equality classes between
the two tile types through cross-type observations; it does not combine two
independently learned single-tile models.

Every negative root connection is audited against the proposed code, including
an inspectable conflicting point/channel where available. Failures that the
fixed domain cannot distinguish remain in the explicit ledger. Finite extension
is provisional. Timeout remains unknown; a deeper timeout cannot erase an
existing finite witness. Deeper unmarked failure supersedes earlier positive
checkpoints for that connection. All search history is exported.

The learner posts a versioned, inventory-specific model to its parent after
collection or deeper evidence updates. The main panel checks message origin and
source, inventory, reflection setting, complete point/channel domain, and exact
integer values. A completed live run automatically selects its model in the matching tiling view,
resets stale search state and displays the new marking. The next tiling run uses
`SparseA2Marking`; no manual transfer control is needed. The learning view stays
open so completion does not interrupt inspection. Changing rules never reuses a stale graph or incompatible
prefix. A separate-page session saves its current model automatically through
session storage when returning to the main page. Restoring that explicit model
takes precedence over the article's automatic Turtle start.

Both views display marking metadata: points, total assigned channel values,
nonzero values and distinct scalar values. Explicit zeros count toward the total;
coordinates on different tile prototypes count as separate marking points.
Turtle has 56 points / 168 values, Hat 50 / 150, and mixed 106 / 318. Metadata also
accompanies JSON evidence exports.

Recorded models are available immediately. **Usual Turtle**, unmarked search,
and the original Turtle controls remain available. Learned rules are explicitly
labeled provisional in the tiler: failure under them does not prove failure
of the unmarked problem. Extension searches in the learning page always remain
unmarked, so learned restrictions cannot generate their own negative evidence.

## Shared algorithm contract and validation

- Integer A₂ triples, capacity 12, and unique tile/transformation identities define
  the point model. Polygons author and draw the point data; polygon predicates
  are not additional legality constraints in this growth experiment.
- Root searches keep both initial placements fixed. Complete growth mode admits
  candidates that only fill existing gaps, sets root generations to zero, and
  scans the full frontier for dead points before accepting a checkpoint.
- Candidate enumeration covers every allowed tile/orientation/support alignment.
  `allowReflections: false` filters orientations before candidate generation and
  also rejects disallowed initial orientations. Inversion on the A₂ plane is a
  rotation; reflection parity comes from the coordinate permutation, not the
  common coordinate sign.
- The engine uses global dead-before-forced decisions, earliest-generation
  branching, complete forward/reverse incidence, and reversible t/m state.
  Sparse markings include mark-only support dependencies and explicit zeros.
- The engine's comparison tolerances operate on small exact integer capacities
  in this experiment. Independent verification uses integer sums and equality.
- Unbounded growth activates exposed positive support, not a fair exhaustion of
  untouched zero-valued points. The result does not establish whole-plane
  coverage or an infinite construction. Point-model correctness is separate
  from faithful realization by conventional polygons.
- Root failure means exhaustive search in the specified unmarked point problem.
  The last dead point is an example branch witness, not a full proof transcript.
  Replay and graph audits check the computation; this is not a formal proof
  kernel. Code conflicts outside audited roots, including mark-only interactions,
  remain hypotheses and can restrict the unmarked solution set.
- The default shared-engine reflection behavior and legacy Turtle benchmark
  behavior are preserved. New inventories and learned-mode searches use the
  complete point-growth options explicitly.

`tests/test_tile_connection_learning.mjs` independently enumerates all 1,248
rooted connections by integer translations; replays all 1,096 exhausted root
searches with graph auditing; independently checks every active frontier in the
148 positive checkpoints; reproduces all three models; checks covariance under
each allowed symmetry; and verifies marked growth, budgets, retained evidence,
and reflection/model mismatch rejection. The existing Turtle regression passes.
Browser checks exercise all three model handoffs, exact marked compatibility,
both tile types without reflections, background learning, deeper evidence,
export, cancellation, ordinary Turtle, and desktop/mobile layout.
