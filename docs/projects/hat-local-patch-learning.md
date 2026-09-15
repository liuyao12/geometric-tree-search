# Hat connection constraints → geometric point codes

The final Geometric Deep Learning section of `GCTS-I.html` examines local Hat
connections. This is constraint discovery, not a prediction task: every collected
outcome contributes to the connection ledger, with no training/test split.
The ordinary Turtle demo and its usual tilings remain available. The separate
Turtle learning example is still labeled as fitting known data.

## Recorded experiment

Regenerate `assets/data/hat-local-patches.json` with:

```
node scripts/train-hat-local-patches.mjs /tmp/hat-local-patches.json
```

The seed is 90210. Every one of the 320 t-legal attachments to an identity Hat is
searched, with both Hats fixed, a 12-tile checkpoint and a budget of 120 attempted
placements. The collector supplies no Hat marking, substitution, preferred patch,
or geometric matching template. Its three outcomes are:

| Outcome | Connections | Meaning |
| --- | ---: | --- |
| Extended | 40 | Reached 12 Hats, with no dead point on the active frontier |
| Dead / excluded | 279 | Unmarked fixed-pair search exhausted all alternatives |
| Unresolved / retained | 1 | Attempt budget exhausted; no negative conclusion |

The 40 extensions give 36 distinct patches after deduplicating full t-data under
all 12 A₂ symmetries and translations. Collection and incremental encoding took
about 21.6 seconds in the recorded Node run. This is one bounded extension search
per connection, not enumeration of every larger patch or a uniform sample.

An exhausted child branch does not exclude its root connection. Only a `no`
result after exhausting the complete fixed-root search does so. The ledger
stores root transforms, target, budget, seed, attempts, backtracks, returned
patch, and the last dead-frontier witness. A last witness illustrates one failed
branch; replaying the exhaustive search is needed to establish the root result.
These are computational exclusions in the unmarked A₂ point model, not a claim
of a separately checked formal proof or a theorem about polygon tilings.

A finite checkpoint is provisional evidence. It does not certify infinite
extension or exact tiling of the whole plane. The UI's **Search farther** action
starts a deeper search from the selected pair, allowing the rest of its patch
to change. All outcomes return to the ledger and the code is recomputed. A deeper
timeout preserves an earlier extension witness; a proved failure supersedes it.
The full search history remains in the export. An excluded connection is not
searched again by this control.

## Geometric encoding and failure coverage

The fixed marking domain is the Hat's 24 positive t-sites plus one A₂ neighbor
step: 50 sites with three channels, or 150 assigned point/channel values.
Locations and t-values are fixed; this experiment does not move anchors.

All currently retained extension patches, including earlier successful searches
in each connection’s history, contribute overlap equations. A later exhaustive
failure removes that connection’s provisional patches from the equality evidence. Transport
point/channel variables by each placement's A₂ action, with channel permutations
and permutation-parity sign changes. A signed union-find solves equalities;
odd sign cycles force zero. Free classes get distinct integer magnitudes. These
labels separate every pair of transported variables that the observed equalities
do not force to agree. Assigned zero remains a value, not a missing entry.

Every failed connection is then checked against this code. The ledger records
whether it is separated and, if so, the world point, channel and unequal values.
The canvas circles that disagreement when inspecting the connection. Negatives
not separated by the code remain explicit exclusions in the connection catalog;
they are not silently discarded or relabeled as successes.

The recorded code has six equality classes, 76 nonzero values and 74 assigned
zeros. It separates 262 of the 279 dead connections, leaves 17 unseparated,
rejects none of the 40 witnessed extensions, and does not reject the unresolved
pair. Agreement does not establish extension. Conflict alone is not a proof of
failure: distinct labels on unconstrained classes are a hypothesis outside the
audited cases. More domain or cluster context may be needed for the 17 failures.

The code is a proposed compression of connection evidence. It is displayed and
audited, but **does not prune subsequent extension searches**. Those always use
the original unmarked point model, so a failure cannot be caused by the learned
hypothesis itself. Auditing the 320 t-touching root pairs does not certify all
mark-only contacts induced by an extended marking domain. No global redundant
marking theorem, learned substitution, RL macro search or speedup is claimed.
The catalog excludes failed root connections; it is not yet a general-purpose
pruning plug-in for arbitrary growing patches.

## Algorithm contract audit

- Coordinates are integer triples summing to zero; t-values are integer twelfths.
  All 12 A₂ transforms are allowed and each placement is selected at most once.
  Polygons author/draw the t-data but add no search legality predicates here.
- Root enumeration uses every orientation and positive-support alignment. An
  independent bounded-translation enumeration agrees on all 320 attachments.
- Growth uses the shared frontier–candidate graph, global dead-before-forced
  checks, then earliest generation and candidate-count ties, with exact rollback.
  All initial placements have generation zero in this experiment.
- `fixedInitialPlacements: true` prevents replacing the connection being tested.
  `completePointGrowth: true` additionally admits candidates that fill existing
  gaps without introducing new support points and checks the whole frontier for
  dead points before accepting a growth checkpoint. These options leave the
  established demos' default behavior unchanged; older benchmarks retain their
  previous semantics.
- All positive t-support exposed by placed tiles becomes an obligation. There is
  no spatial cutoff in growth mode; the required boundary argument is not used
  to restrict its candidates. Fair activation of untouched zero-valued points
  remains absent, so no whole-plane coverage conclusion follows.
- The engine still uses tolerance comparisons, but this experiment's coordinate
  and capacity arithmetic stays in small exact integers. The independent checker
  sums integer capacities without tolerance. This is not a repository-wide
  arithmetic or conformance certification.
- Tests replay all 279 negative searches with incremental-graph auditing and
  independently re-enumerate the last dead witness. They independently check
  every active frontier point in all 40 positive checkpoints, reproduce the
  model from all 36 distinct patches, check all A₂ symmetries, and verify timeout
  handling, fixed-root preservation and global dead-before-checkpoint behavior.
- The UI offers recorded evidence, full recollection, selected deeper search,
  pause/reset and JSON export. Reset terminates the worker; stale results cannot
  restore cancelled work. There are no held-out controls or prediction metrics.
