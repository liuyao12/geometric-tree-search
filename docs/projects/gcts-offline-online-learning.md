# Two learning regimes for GCTS tilings

The 2D and 3D playgrounds now use deliberately different sources of negative
evidence.

## 2D: exhaustive labels, then a fixed marking

For a lattice polygon there are finitely many symmetry-reduced legal placements
of a second tile against a fixed seed.  For every such two-tile union, the local
oracle searches the finite tree whose goal is to close every angle-deficit
lattice point belonging to the original pair.  The label is:

- **positive** when a complete one-corona is found;
- **negative** only when that local tree is exhausted;
- **inconclusive** when a node, time, tile, frontier, or candidate cap prevents
  an exhaustive proof.

Only positive and proven-negative rows enter training.  A marking can be called
**fixed** only when there are no inconclusive rows, all positive patches replay,
and the learned marking rejects the intended negative contacts.  Benchmarking
then starts a new tiling search from the seed; it does not continue the data
generation search.

### 2D live alternative: train, validate, freeze, replay

The A₂ playground also implements an online route for the live demonstration.
It starts from an empty rank-3 bundle. An immediately stranded frontier after a
trial placement is a finite negative certificate, so the learner allocates two
sparse support sites in independently chosen channel domains and adds a signed
disequality. Accepted prefixes become positive constraints and must remain
replayable. The channel values are unrestricted real-valued labels; only the
equalities and disequalities matter.

Because one local disequality can affect many transformed placements, a learned
revision is a hypothesis rather than automatically a global theorem. The demo
therefore screens revision 0 and sampled learned revisions on a fresh, longer
search, confirms the strongest learned candidates on a second branch order,
then freezes the best successful marking and restarts the tiler from scratch.
This is geometric memoization with held-out model selection, not continuation
of the training branch.

The shared benchmark currently selects a six-site Turtle marking after training
to 30 placements. On four disjoint 60-placement test branch orders it reduces
median nodes from 820 to 493; the human-engineered marking reaches 193. The same
tile-agnostic learner selects a 16-site Hat marking and reduces held-out median
nodes from 283 to 54 at 40 placements. Reproduction commands are in the root
README.

For the Hat, the complete pipeline is:

```sh
python3 scripts/hat_pair_corona_marking.py \
  --pair-exhaustive \
  --pair-node-limit 0 \
  --pair-wall-time-ms 0 \
  --pair-max-tiles 0 \
  --pair-frontier-limit 0 \
  --pair-candidate-limit 0 \
  --require-complete-dataset
```

The JSON artifact contains the canonical placement key, label, proof status,
learned support, replay audit, fixed-marking validation, and fresh marked versus
unmarked benchmark.

## 3D: transactional online failure marking

The 3D tiler exposes **Learn failure markings**.  It starts with literal empty
support.  When, and only when, a child subtree has been fully exhausted, it
attempts this transaction:

1. snapshot the surviving parent prefix;
2. add a pair of equivariant lattice probes whose transformed positions meet in
   the failed placement;
3. extend the probe domain farther along the lattice when the current domain
   cannot express a safe mismatch;
4. solve equality constraints from every protected prefix and disequality
   clauses from every proven failed branch;
5. replay all protected prefixes and re-reject all earlier failures;
6. commit a new marking revision and invalidate candidate caches.

A stopped, paused, node-capped, time-capped, candidate-capped, or branch-capped
search is not a proof and teaches no negative label.  If no safe mark extension
exists within the configured reach, the move remains available and the learner
records it as unencodable.  This makes the marking an auditable geometric
certificate rather than an opaque branch-key memo table.
