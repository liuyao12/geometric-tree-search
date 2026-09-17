# Learned interval markings: alternate covers reconstruct the same targets

## Main result

The frozen training-only interval markings admit complete reference-search
reconstructions of all twenty known ice calibration targets at 1, 2, 4 and 8
channels. Each run starts without selected placements. The original finite
geometry candidate pool, candidate order, target, kernel and search budget are
unchanged; only m-data are added. These are 80 verified marked finite fillings.

| Channels | Saved unmarked covers retained | Targets reconstructed by fresh marked search | Attempts | Backtracks | Forced placements |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 20/20 | 20/20 | 2,890 | 775 | 11 |
| 1 | 4/20 | 20/20 | 2,958 | 818 | 22 |
| 2 | 0/20 | 20/20 | 2,632 | 530 | 17 |
| 4 | 0/20 | 20/20 | 2,905 | 772 | 29 |
| 8 | 0/20 | 20/20 | 2,621 | 492 | 112 |

Counters are totals across twenty targets. The retention column tests the
specific saved unmarked search witnesses, not all unmarked solutions and not
the earlier supplied-pose covers. At two or more channels none of those saved
unmarked witnesses satisfies the markings, but new search finds other covers
of every target. Thus rejecting a particular decomposition is not the same as
excluding its atom configuration. This does not prove the new decomposition
has the physically or scientifically desired connections.

## Training and transfer

The marking bytes are identical to `../ice-tolerant-markings/markings.json`
(SHA-256 `5d391d6b13c2be56f7f015d50c5e13b27f21207a52596b56f495ce5365646578`).
No retraining on search outcomes or calibration connections was performed.
The earlier independent training receipt checks all 80 fitting configurations.
Landmark distances in the training-overlap graph define scalar integer values;
each is interpreted as a closed interval of radius one half. Multiple channels
use a Cartesian product, and rotations act trivially on the scalar values
while transforming their anchor positions.

The same learned type and anchor index determine m at every registered pose.
Element labels are opaque matching labels, not chemistry rules. Existing
learned anchor positions and t-values are frozen. This is sequential transfer
of separately learned t-support and m-values, not joint optimization of anchor
number, location, t and m. There is still no learned marking-only support.

The four ice phases use one common support/marking library. These are calibration
frames seen by the upstream dictionary, not independent new-condition tests.
Neither identical-condition admission nor independent-trajectory provenance is
established. The result is therefore developmental, not a generalization claim.

## Verification

The new checker independently rebuilds every candidate's interval assignments
from learned type/anchor values, checks the complete candidate order and
geometry against the unmarked pool, and checks exact common intersections
using doubled integers. It also invokes source-coordinate replay for proper
rotations, unique species-preserving matches within 0.15 Å and exact rational
t-sums. It does not merely accept pairwise matches along a chain.

Corruption controls reject a missing marking channel, a shifted interval,
changed t-data, and an actual t-capacity-compatible but m-conflicting pair.
The last control establishes that these markings can reject genuine candidates
in this pool, not just abstract anchor labels. It is not evidence that the
rejected pair is physically invalid. Kernel graph audits and rollback pass.

## Identity ablation and limitations

A separate unmarked inventory ablation retains one deterministic representative
per motif type and unordered mapped t-support. All twenty targets still fill,
so the prior reconstruction success does not require that particular source
of repeated-support multiplicity. This is a restricted inventory experiment,
not a proof that continuous poses are symmetry-equivalent. It is not applied
to marked pools: different anchor permutations can carry different m-values.

Repeated mapped supports and disconnected covers persist in the marked
results; eight-channel covers have 7–40 shared-atom support components and up
to 28 repeated unordered type/t-support selections. No single-atom growth or
extension beyond known target coordinates is established. A connected support
graph alone would not establish those properties either.

Markings are learned hypotheses that change the solution set, not proved
redundant constraints. The lower eight-channel backtrack count is not a
speedup certificate or a guarantee of preserving every unmarked solution.
The channel experiments overlapped in execution, and their 0.94–1.69-second
search totals are not a controlled timing comparison. Training, geometry
registration, adapter construction, parsing and independent replay are not
included. No wall-clock performance advantage is claimed.

## Evidence and reproduction

`summary.json` links each pool, search and check by hash. `search-N.json` stores
selected candidate IDs and counters; `check-N.json` stores the independent
marking and geometric checks. The raw coordinate-bearing pools are not
redistributed, so this is not a standalone reproduction bundle. The earlier
sections contain source-corpus provenance and frozen learning artifacts.

For each N in 1, 2, 4 and 8, using fresh output paths:

```sh
node decorate-learned-support-pool.mjs BASE_POOL SUPPORT MARKINGS N MARKED_POOL
node search-learned-support-repairs.mjs MARKED_POOL KERNEL SEARCH 300000 10000
python verify-learned-support-marked-search.py COORD SUPPORT MARKINGS BASE_POOL MARKED_POOL SEARCH CHECK
python test-learned-support-marked-search.py COORD SUPPORT MARKINGS BASE_POOL MARKED_POOL SEARCH
```

The independent geometry helper must be beside the marked checker. Marked
search uses the unreduced source pool, not the unmarked identity ablation.
