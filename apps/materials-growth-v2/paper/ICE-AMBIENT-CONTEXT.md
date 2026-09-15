# Cover-independent marking control

## Question

The preceding junction marking contains a root component and the two neighbors
selected by a particular half-weight cover. This is a valid cover-dependent
hypothesis, but it is not an invariant description of the underlying atomic
configuration. Can a cover-independent local description support reconstruction?

This control retains the learned base geometry, component partition, training
configurations, registrations and t=1/2 values. It changes only the neighborhood
used to construct m: root plus every neighbor in the frozen, geometry-derived
component proposal graph. No chemical formula, coordination number, phase label,
energy or formation history enters the values. The graph still depends on the
earlier geometric threshold; “cover-independent” does not mean neighborhood-free.

## Marking semantics

Cloud entries are displacement vectors from the root component centroid. Colors
contain only the root/non-root role and opaque input species. A single proper
base rotation transports both endpoint clouds. Translations act on anchors.
Periodic context construction uses one minimum-image displacement per component
pair, not all periodic images. The overlap marking radius remains 0.15 Å.

The new clouds contain 15–42 atoms in this corpus; the old selected-cover clouds
contain nine. This is a different marking hypothesis, not a proved redundant
constraint, a compression comparison or a change to the reference scheduler.

## Supplied-cover verification

- Same 278 base motifs and 100 training configurations.
- Same 168 supplied covers; 43,680 integer atom totals checked across those covers.
- 29,120 endpoint assignments replayed against source atomic coordinates.
- Maximum observed transport residual: 2.29e-14 Å.
- 10,090 distinct selected occurrences. Of these, 1,057 had different stored
  markings under alternative covers in the old library; none do in this control.
- 10,090 new decorated motifs versus 11,147 old ones. Different neighborhood
  semantics prohibit interpreting this count change as a compression gain.

The independent verifier reconstructs source contexts without the new context
constructor. Its periodic check enumerates 125 images around fractional wrapping
for these bounded ice cells; it does not certify arbitrary skew-cell closest
vectors. Synthetic tests cover graph-order invariance, rigid transport, and
the contrast with selected-cover neighborhoods.

These are positive checks on supplied covers, not search or transfer results.

## Reconstruction experiment

The frozen protocol uses the same first training and developmental frames of
Ih, II and VI, observed coupled endpoint pairs, the reference dead/forced/
earliest-generation scheduler, and 30-second search budgets. Factorized
preprocessing is a necessary superset filter only; off-diagonal pairs are not
admitted by the coupled search. Each saved result requires independent t,
inventory, coupling and common-cloud witness checks.

The expanded Ih source is 638 MB. The original Node loader hit its single-string
limit before search. The bounded-string JSON reader fixes that input limitation
without truncating candidates or changing numeric values. It is not bounded-memory
streaming: both the input buffer and parsed objects still reside in memory.
The full Ih block verification then passed for 213,670 coupled candidates across
two frames. The pipeline resumed from that hash-verified compilation checkpoint.

## Six-frame outcomes

| Frame | Result | Final selected placements |
| --- | --- | ---: |
| Ih training | Independently verified complete, connected | 128 |
| Ih developmental | Restricted root failure | 0 |
| II training | Budget-unknown | 51 |
| II developmental | Restricted root failure | 0 |
| VI training | Budget-unknown | 51 |
| VI developmental | Engine-reported finite exhaustion after 12 attempts | 0 |

The Ih completion recovers the original training support cover. Independent
selected-state replay checks 460 endpoint assignments across all final states;
all six root rollbacks pass. A separate full-cloud necessary-support check
certifies 366 uncovered required points in developmental Ih and 6 in II. It
finds no root obstruction for VI; the independent final-state verifier does not
certify the entire exhausted VI search tree. That distinction must remain visible.

One training completion out of three, and no developmental completion, is not
an improvement over the earlier paired control. The neighborhood construction
does eliminate dependence on the selected cover, but does not by itself solve
transfer or reconstruction. More forced moves or different final partial sizes
are not completion or speedup evidence. Identical physical conditions, independent
trajectories, general anchor/t learning, complete continuous poses and beyond-input
growth remain open.
