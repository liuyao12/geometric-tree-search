# Hat local patches → geometric point codes

This is actual inference from sampled local point-value tilings. It supplies no
Hat marking, substitution, preferred patch, or geometric matching template.
The earlier Turtle widget is a supervised reconstruction of known Turtle data;
its experiment selector now labels that distinction explicitly.

## Recorded experiment

The reproducible run is in `assets/data/hat-local-patches.json`. Regenerate with:

```
node scripts/train-hat-local-patches.mjs /tmp/hat-local-patches.json
```

The recorded configuration uses root-attachment shuffle seed 90210, 12 tiles per
patch, 120 attempted placements per local search, 16 unique training patches and
8 unique held-out patches. The complete 320-candidate root attachment universe
is shuffled; up to two shuffled passes are allowed, and 318 root contexts were tried before the requested sample count was
reached. Each patch is independently checked for integer point-capacity legality.
Patches are deduplicated under all 12 A₂ symmetries and translations using their
full t-data, including across the training/test boundary. The corrected attempt
ledger contains 39 successful extensions (15 duplicates), 278 exhausted root
contexts and one budget-limited result. These are distinct
whole patches, not necessarily disjoint sets of smaller contact motifs.

Only successful 12-tile checkpoints enter the data. Failed or budget-limited
searches remain in the attempt ledger; neither becomes a blanket negative
example or a proof about infinite tilings. The collection is biased by this
bounded growth procedure; it is not a complete enumeration or a uniform sample
of all local Hat tilings. Changing only the search seed initially produced many
duplicates, which is why distinct two-Hat root contexts are used.

## Learned representation

The marking domain is fixed before training: the Hat's positive t-support plus
one nearest-neighbor A₂ lattice step. This contains 50 sites, with three scalar
channels per site. The geometry and t-values of the Hat stay fixed. Anchor
locations are not optimized by gradient descent in this experiment.

Each of the 150 point/channel entries starts as an independent variable. For
each training patch, all placements transport these entries into world point/
channel coordinates. Entries at the same world point and channel are equated,
with channel permutation and permutation-parity sign changes under the A₂ group.
A signed union-find solves these observed equalities exactly. An odd sign cycle
forces its entire class to zero. All other equality classes get distinct signed
integer labels. Zero is an assigned value, never an absent channel.

The learned model has 6 equality classes, 76 nonzero entries and 74 explicit
zeros. All 16 training patches and all 8 held-out patches satisfy it. Of the
320 t-legal two-Hat root attachments, 58 also satisfy this marking: 262 are
excluded by the hypothesis. Training consistency is by construction; held-out
consistency is empirical evidence only. Different labels on unrelated classes
can exclude unseen valid patches, so these labels are **learned hypotheses**,
not proved redundant constraints. No infinite tiling theorem is claimed.

The exported local library contains each patch's base placement transforms and
canonical t-data. It is inspectable geometric cluster data. The present search
uses the inferred single-Hat marking; it does not yet propose those clusters as
RL macros or claim to discover a substitution.

## Fresh searches and cost

The recorded fresh seeds are 701 and 1709, with a 32-tile target and a budget of
500 attempted placements. Each compares a new unmarked run to a new run using
`SparseA2Marking` populated solely from the inferred point codes.

| Seed | Unmarked attempts | Marked attempts | Unmarked backtracks | Marked backtracks | Unmarked ms | Marked ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 701 | 417 | 145 | 386 | 114 | 1908 | 1804 |
| 1709 | 166 | 58 | 135 | 27 | 1153 | 1459 |

Both variants reached independently verified 32-tile finite patches. Collection
and encoding took approximately 23.3 seconds, separate from those search times.
The engine's marking score also affects candidate ordering; the experiment does
not isolate elimination from ordering. The two searches share t-data, seed,
scheduler, budget and target, but the learned marking restricts the problem.
There is no end-to-end speedup or solution-set-preservation claim. Engine prune
counters do not capture all fast graph invalidations; the 262 attachment count
comes from a separate exhaustive marking check, not that counter. Memory is not
measured. Browser worker timings include yielding and any pauses.

## Algorithm contract audit

- All t-data use integer twelfths on A₂. All m-values, coordinate comparisons
  and independent replay checks are exact integers.
- Root attachments exhaust every orientation and positive-support alignment
  with the identity seed; an independent bounded-translation enumeration agrees
  on all 320 candidates. No polygon-overlap predicate is added to this point model.
- Growth uses the shared A₂ frontier/candidate graph, complete domains,
  global dead/forced checks and generation-first branching. The initial two-Hat
  context is explicit; there is no learned candidate shortlist.
- Collection and comparison set `fixedInitialPlacements: true`. This new opt-in
  prevents the shared engine from unwinding the initial root context after failure.
  Its default remains false, preserving the original demos. Every accepted local
  sample is also checked to contain its advertised seed pair.
- Markings are frozen before held-out evaluation or fresh search. The existing
  sparse marking handles channel transforms, mark-only dependencies and exact
  marking rollback. Collection has no marking or learned filter.
- Shared-engine growth-stop, floating-tolerance and untouched-point activation
  limitations remain. A checkpoint may precede a global dead-point rescan. The
  independent verifier checks the finite patch's t-capacity and marking overlap;
  open frontier points are reported, not certified extendible or fully tiled.
- Whole-patch symmetry deduplication prevents reflected, rotated or translated
  copies crossing the split. Shared smaller motifs across the split are allowed.
- Tests replay all training/test patches, reproduce the fitted model from training
  alone, check covariance under every A₂ symmetry, independently enumerate root
  attachments, reject duplicates and audit the shared graph during a marked run.
- The worker supports pause and cancellation. Reset terminates it and stale
  messages cannot restore a cancelled run. The UI identifies the initial data as
  a recorded run and offers live recollection, fresh comparison and JSON export.

## Exploratory observation and next experiment

A separate development probe admitting shallower six-Hat patches collapsed the
one-step-halo signed marking to zero. The 12-Hat data retained nonzero classes.
That observation motivates deeper extension checks; it does not prove that any
six-Hat patch is globally invalid. The next tests should vary patch depth and
collection budgets, validate on larger independently collected patches, and use
cluster-level markings if a single-tile marking loses relevant context.
