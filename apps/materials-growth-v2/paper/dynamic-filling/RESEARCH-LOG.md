# Complete decoration transfer: necessary-domain diagnostic

## Question and outcome

Do the frozen pair interfaces form reusable complete motif decorations?
The current evidence is insufficient. A necessary, fixed-pose geometric test
passes substantially fewer complete decorations than individual pair tests.
This changes the next step: optimize and validate whole-motif poses/ports
jointly before presenting the learned interfaces as tiles for growth.

Input: oxalic-acid modal-cell cohort, nested-v1 motif library,
periodic-interfaces-v1, and whole-contexts-full-v1. All contexts are assembled
from training occurrences; no evaluation ports are used to build a context.
The inventory has 647 contexts, of which 22 recur in two or more training
frames. No rare ports are deleted and there are no empty decorations.

| Evaluation cohort | Motifs | Neighbor type/count admits a context | Full directed-vector domain nonempty | Frames with every domain nonempty |
|---|---:|---:|---:|---:|
| alpha, all training contexts | 182 | 136 | 3 | 0/44 |
| alpha, recurrent contexts only | 182 | 72 | 0 | 0/44 |
| beta, all training contexts | 94 | 83 | 41 | 16/44 |
| beta, recurrent contexts only | 94 | 72 | 10 | 0/44 |

Every one of 669 admitted training motif occurrences passes with its saved
complete context. Checks also reconstruct training-port multiplicities,
endpoint types, recurrence counts and source occurrence ownership.

## Semantics

Each port retains the learned local vector of its interface model. Both A
and B values encode A-to-B displacement, so the B-role direction is negated
when testing its outgoing neighbor. The original proper motif rotation
transports the vector. Explicit periodic images remain separate neighbors;
a self-image edge supplies two directed neighbors, not a same-cell loop.

Every port must match a distinct proposed neighbor of the opposite endpoint
type, with vector error at most the frozen 0.30 angstrom target tolerance
(plus 1e-9 numerical allowance). Complete finite bipartite matching tests
this injection. Extra neighbors are allowed: this is only a necessary test.
Model IDs need not match those originally selected at evaluation.

530 small matching instances were compared with independent exhaustive
permutation enumeration. Additional controls cover self-image direction,
proper rotation, wrong type, missing neighbor, and repeated-port contention.

## Interpretation and limits

For alpha, 136 motifs have enough appropriately typed neighbors but only
3 pass the vector test. Type availability alone therefore does not explain
most failures. This does not distinguish arbitrary saved orientation choices
from genuine geometric variation: all ports share the original atom-valid
pose, and continuous re-registration has not been attempted here.

Neither the 16 beta frame positives nor the empty domains establish a GCTS
result. Paired-anchor coincidence, opposite endpoint decorations, multiway
common marking values, cross-interface collisions and t-sums are unchecked.
The Voronoi neighbor set and displacement-target prior are explicit
geometric choices, not base GCTS legality. Missing overlaps remain
unconstrained. Single-frame contexts are hypotheses. Absence in this finite,
fixed-pose diagnostic is not continuous-space impossibility.

The next experiment should seek a single atom-valid pose per motif that
supports its entire decoration, then couple those choices across neighbors.
Do not repair failures by silently widening tolerances, dropping rare ports,
or treating independently optimized pair poses as jointly realizable.

## Reproduction

```
python check-whole-context-domains.py metadata.json nested-v1.json \
  periodic-interfaces-v1.json whole-contexts-full-v1.json output.json
python test-whole-context-domains.py
```

Receipt: `/tmp/gcts-oxalic-modal-cohort-v1/whole-context-domains-v2.json`.
SHA256: `7a338de4ec378c965bd699522e70db684dfed8be24886753b6d08a0e38355f2b`.
Receipt binds input and checker hashes and retains positive matching witnesses.
This is a local research result; the deployed paper has not been changed.

## Follow-up: continuous whole-decoration pose fitting

`optimize-whole-context-poses.py` preserves all learned parameters and tests
one shared rigid pose for the atoms and every port of each candidate context.
It starts from bounded atom-correspondence registrations, assigns distinct
typed neighbors using linear assignment, then optimizes a proper rotation
and translation with explicit atomic and port residual constraints. The
assignment stays fixed within each optimization. Neighbors keep their saved
poses; self-image displacements are translation invariant.

| Cohort/context eligibility | Fixed-pose positive motifs | Optimized positive motifs | Frames where every motif has a local witness |
|---|---:|---:|---:|
| alpha, all training contexts | 3/182 | 50/182 | 6/44 |
| alpha, recurrent only | 0/182 | 0/182 | 0/44 |
| beta, all training contexts | 41/94 | 69/94 | 32/44 |
| beta, recurrent only | 10/94 | 42/94 | 14/44 |

These recoveries establish that fixed registration accounts for some failed
necessary-domain tests. They do not establish simultaneous compatibility:
independently moving adjacent motifs changes their mutual displacement.
The next test must replay/solve the poses together, not count these local
witnesses as reconstructed frames. Pair-anchor agreement and filling remain
additional requirements even if that joint displacement test passes.

The independent `verify-whole-context-poses.py` reconstructs explicit-image
displacements from original poses/cells rather than saved residuals. It
checks atomic correspondence/species, proper rotations, distinct port
assignments, all directed-vector residuals, frame coverage and totals.
161 positive lanes passed; maximum atomic error was 0.15000000003392122
angstrom and maximum port error 0.30000000006333283 angstrom, within the
declared 1e-9 numerical allowance. These are approximate witnesses, not exact
certificates. Seven corruption tests reject changed translation, reflection,
nonbijective atom map, repeated neighbor, missing port, omitted evaluation
row and fabricated summary.

Limits: 12 initializations, 120 SLSQP iterations each, two seconds per lane,
20000 correspondence enumeration nodes. No time-budget stops occurred, but
the initialization/iteration bounds still apply; failed trials are unknown.
Only one positive witness per motif/eligibility lane is retained, not a
complete pose or context domain for search.

Result: `/tmp/gcts-oxalic-modal-cohort-v1/whole-context-poses-v1.json`, SHA256
`414a9ef42c09d5e0d4386c060acbefacd2a7b06f98fd0a6cb92d278a58a6272e`.
Replay: `/tmp/gcts-oxalic-modal-cohort-v1/whole-context-pose-check-v1.json`.

## Follow-up: simultaneous assembly and representation control

`audit-assembled-contexts.py` installs all saved local witnesses together.
It recomputes neighbor displacements and checks the two decorated endpoints
assigned to each explicit periodic edge. Reciprocal anchors must be within
0.30 angstrom; transported vector values must be within 0.30 angstrom.
All geometric tolerances retain the 1e-9 numerical allowance.

| Cohort/context eligibility | Complete local witness sets | Joint displacement passes | Joint displacement + reciprocal anchor/value passes |
|---|---:|---:|---:|
| alpha, all | 6/44 | 1/44 | 0/44 |
| alpha, recurrent only | 0/44 | 0/44 | 0/44 |
| beta, all | 32/44 | 29/44 | 2/44 |
| beta, recurrent only | 14/44 | 13/44 | 0/44 |

All 52 available frame/lane combinations pair every selected port with a
reciprocal one. Among their 812 proposed reciprocal pairs, 240 use the same
learned endpoint role, and all 240 fail vector agreement. Among the 572
complementary-role pairs, 94 fail vector agreement and 209 fail anchor
coincidence. Counts include both eligibility lanes, not independent samples.

A separately labeled representation ablation identifies a vector with its
negative, using `min(norm(v-w), norm(v+w))`. This removes the directed-sign
distinction from m, not from the displacement proposal prior. It changes the
marked problem and is not a soundness-preserving optimization of the original
marking. No additional complete configurations pass: anchor/other geometric
disagreements remain. This control therefore does not establish that sign
choice is the main assembly bottleneck.

`optimize-assembled-contexts.py` then varies all motif poses simultaneously,
with frozen contexts, correspondences and port assignments, enforcing atomic,
displacement, reciprocal anchor and vector residuals together. There are no
new positives. The two original beta positives remain; 28 trials hit the
160-iteration limit, none hit the three-second callback limit. Failures remain
unknown. This is one selected context per motif, not a search over alternative
decorations; it cannot establish failure of the learned library as a whole.

Synthetic controls cover explicit self-images, translation and proper rotation
invariance, collapsed image labels, directed marking disagreement, the separate
sign-invariant control and missing reciprocal ports. Source atom validity was
replayed before the assembly audit. No optimized positive certificates were
produced beyond the two unchanged, replayed input assemblies.

These are still not filling results. Edges only propose pairs; they do not
define geometric point identities. Cross-edge anchor collisions, multiway
common values and learned t-sums remain unchecked. Missing overlaps are not
GCTS rejection evidence. The next step must consider alternative decorations
jointly and resolve shared anchor/value consistency before using the filling
kernel; independent local witness selection is not sufficient.

Artifacts under `/tmp/gcts-oxalic-modal-cohort-v1/`:

- `assembled-contexts-v3.json`: SHA256
  `05cd89f0a735e3dc210a2912d6762174ae1c8c973dea6821133512da7bf00af4`.
- `joint-context-poses-v1.json`: SHA256
  `4ba2eaa1596894d2b0104f055e933e517291f49ac4baed23e05073b4a7df8f02`.
  This run used the earlier audit adapter (hash embedded in the receipt),
  before the additional sign-invariant diagnostic fields; optimization used
  only the original directed-vector representation.

## Follow-up: choose alternative decorations jointly

`search-context-assemblies.py` now tests alternative contexts, not just the
first local witness. The finite domain contains all saved original-pose
contexts with their injective port-to-neighbor assignments (enumerated up to
10000 nodes/context), plus the saved optimized local witnesses. Full
decorated identities are retained; only identical serialized witnesses are
deduplicated. Contexts recurring in at least two training frames are evaluated
in a separate lane from the all-training-context hypothesis lane.

The diagnostic uses fixed-order forward checking over binary geometric
compatibility and self-image constraints, up to 100000 search nodes. This is
explicitly **not** the reference GCTS filling engine: reciprocal edge pairing
and displacement priors are extra geometric conditions, there are no t-values,
and no continuous-placement completeness is asserted. Exhaustion refers only
to the declared finite pool. Missing overlap is not a marking rejection.

Five of 44 beta frames now have simultaneous reciprocal anchor/value and
displacement witnesses, up from two when taking the first local choice.
Each of the five selected port graphs has constructive integer-lift paths to
every motif and all three unit translations. Alpha remains 0/44. The
recurring-context-only lanes remain 0/44 for both phases. No enumeration or
search budget stops occurred. Maximum per-motif options were one for alpha
and 13 for beta, so this is not a broad continuous-search benchmark.

Each positive assembly is replayed by the separately implemented assembly
audit. The finite assignment enumerator agrees with exhaustive permutation
enumeration on 530 controls; the solver agrees with brute force on 300 seeded
small CSP instances. Both budget-stop paths are separately tested and return
unknown rather than exhaustion. The periodic path checker constructs and
replays integer-edge paths; it does not certify geometric tiling.

This establishes that first-choice selection lost some feasible combinations.
It does not solve transfer across the family: the positive assemblies require
contexts admitted even when seen only once, and complete recurrent contexts
still do not reconstruct either cohort. Full shared-point identity, common
multiway marking values, learned t-sums and blind growth remain outstanding.

Receipt: `/tmp/gcts-oxalic-modal-cohort-v1/context-choice-search-v2.json`.
The result binds the pose and baseline receipts, which transitively bind all
source data and learned model files. No deployed page changes in this step.

## Follow-up: geometric point-identity ambiguity before t-learning

`audit-anchor-neighborhoods.py` examines all 239 admitted training frames and
the five passing evaluation assemblies. It transports every learned anchor
and marking using its motif pose, constructs periodic distance-neighborhood
components at 0.30 angstrom, and attempts a common radius-0.15 ball for both
positions and marking values. The finite image enumeration has an explicit
singular-value omission bound. Components are an ambiguity diagnostic, NOT
automatically identified GCTS points.

Training yields 4740 two-anchor groups and 17 four-anchor groups. All pairs
have common positional and marking witnesses. Six four-anchor groups have
positional diameter greater than 0.30 angstrom; all 17 have marking diameter
greater than 0.30 angstrom. Thus merging every distance-connected component
would invent training inconsistencies that the individual interface pairs
did not have. Proximity is not a transitive equality relation.

The evaluation assemblies yield 68 pairs and one four-anchor group. The latter
is in `oxalic-beta-0160` and has both positional and marking diameter
obstructions. The other four assemblies (`0130`, `0134`, `0137`, `0145`) have
14 isolated two-anchor neighborhoods each. This does not prove a unique point
domain or exact filling, and does not invalidate the fifth assembly: the
four-anchor group need not represent one geometric point. The common-point
identification model must be specified/learned rather than silently imposed.

Common-ball positives retain their numerical centers and checked maximum
residuals. Negatives are called diameter obstructions only when a pair is
farther apart than twice the allowed radius; otherwise failed optimization
is labeled unknown. Tests include pairwise-close points without a common
ball, periodic images, rigid motions, and a nontransitive proximity chain.

Do not train t-values by assigning a single capacity-1 obligation to each
distance-connected component. First resolve which local anchors represent
the same point and preserve uncertainty where the data do not determine it.
This is a geometric learning requirement, not a chemistry/physics rule.

Receipt: `/tmp/gcts-oxalic-modal-cohort-v1/anchor-neighborhoods-v1.json`, SHA256
`10d25dd143e315b9a76f8c1600b11cc1d8063ff51e008cf8ad4cf86a1f85915e`.

## Follow-up: inferred point partitions and regularized rational t

`learn-context-point-weights.py` resolves each proximity neighborhood without
consulting edge IDs: enumerate its set partitions, require each block to have
common radius-0.15 position AND vector-marking witnesses, and minimize the
number of blocks. This minimum-point-count objective is an explicit prior.
The anchor/value estimates themselves were learned from proposed edges, so
this is not independent discovery of connections.

All 4826 audited neighborhoods have a unique minimum under that prior. The
four-anchor ambiguity groups split into two compatible pairs, including the
one in evaluation frame beta-0160. Independent verification enumerates set
partitions by restricted-growth labels rather than the learner recursion.
Uniqueness follows even using only pairwise diameter necessary conditions,
while the selected blocks have checked common-ball centers.

Weights belong to `(complete context, local port)` identities and are fit
using training equations only. The 4774 equations contain 9256 variables and
leave 4612 free parameters. Minimize squared norm subject to every training
point sum being one. Since the inferred training blocks all have two members,
this is an exactly solvable graph-incidence problem: a bipartite component
with side sizes a,b assigns b/(a+b) and a/(a+b); odd-cycle components assign
one half. The present components have at most three variables and no odd
cycles. The fitted histogram is 9160 half-weights, 64 one-third weights and
32 two-third weights. These values are regularized choices, not uniquely
identified by the observations.

All five evaluation assemblies satisfy all 14 rational point-sum equations
per frame with these frozen weights. They were selected before fitting t;
evaluation equations were not used to fit the weights. The entire evaluation
cohort is still 88 frames; these five are a selected successful subset, not
five independently chosen test cases. No broad reconstruction-rate claim.

`verify-context-point-weights.py` reconstructs the geometric/vector witnesses
from source poses, checks partitions independently, and checks all training
and evaluation sums using rational arithmetic. It also produces 4612 exact
stationarity certificates (`w=A^T lambda`, `Aw=1`) for the minimum-norm fit and
checks the nullity. Separate tests compare the fitting formula against dense
least squares/rank on 300 small random graphs, check Bell partition counts,
relabeling invariance and the partition size budget.

This is the first regularized t fit in this whole-decoration lane. It is not
yet a reference-engine filling result: geometric witnesses are approximate,
point identity uses a declared prior, rigid support consistency across all
placements and material-wide atom obligations remain to be implemented and
checked. Target-conditioned candidate geometry is still used. No blind growth
or identical-condition provenance is established.

Artifacts under `/tmp/gcts-oxalic-modal-cohort-v1/`:

- `context-point-weights-v1.json`, SHA256
  `f13c54b9653e2cef896df441dc0a01d0859928bfd5ec7bd5176e29db96605cf7`.
- `context-point-weight-check-v1.json` contains the independent replay.

## Follow-up: reference point-kernel integration, with explicit scope

`compile-context-filling.py` builds a target-conditioned finite model for the
five already successful beta assemblies. Each target has 16 source atom sites
and 14 inferred latent sites. Every frozen context of the matching base type
is tested at each saved atom-valid pose. Every port alignment within 0.15
angstrom is enumerated geometrically, without using the proposed edge IDs;
multiple local ports may fold onto one periodic point and their contributions
are aggregated. Atom sites have unit t occupancy as an explicit prior; ports
use the learned rational t. Capacity six represents every contribution exactly.

This yields only 2, 3, 2, 2, 3 candidates after testing 812, 399, 546, 448, 546
context/pose combinations respectively. These are intentionally a small
integration control, not a reconstruction benchmark: the target latent sites
were derived from prior successful assemblies. Fixed supplied motif placements
are not a complete continuous placement domain.

`run-context-filling.mjs` imports the existing `PointSearch` unchanged. All
30 target obligations are active generation-zero roots. Global dead/forced
and generation-first scheduling, incidence updates and rollback are provided
by that kernel. The graph is checked by exhaustive rebuilding after each
step; the independent kernel verifier checks each completed occupancy model.
The existing kernel tests also pass (dead/forced/generation, fractions,
interval intersection, mark-only dependencies, rollback, 32 exhaustive
controls and incomplete domains).

All five unmarked runs and all five marked runs complete, selecting two
placements each. Three cases use two forced placements; two use one forced
placement and one branch. There are no backtracks. Marked and unmarked traces
have the same counts, so **there is no marking acceleration result here**.

The engine's native componentwise intervals enclose the intended Euclidean
vector balls; this is a declared relaxation, not an equivalence. The separate
`verify-context-filling.py` re-enumerates the entire declared candidate universe
using a separate periodic geometry implementation, checks source atom fits,
reconstructs all learned t and m, verifies exact rational point sums, and
checks actual common Euclidean marking-ball witnesses on the selected covers.
All ten results pass. Maximum atom error is 0.15000000000193064 angstrom
(within the stated numerical allowance); maximum marking-ball radius is
0.13056932311533506 angstrom. Corruption controls reject an omitted candidate,
changed t contribution and duplicate selected placement, even with updated
input hashes.

Artifacts under `/tmp/gcts-oxalic-modal-cohort-v1/`:

- `context-filling-pool-v1.json`, SHA256
  `6e83828ba6c121dbd8b0e7bd7840101f9ec6d5cb1c5a5d34cf11dd904b1a4e17`.
- `context-filling-search-v1.json`, SHA256
  `6a434a14246d964722575792f041fc7f73a31ca8bd83230c4a8dfc3a3f9090bf`.
- `context-filling-check-v1.json` records independent replay.

The main gap is now beyond the adapter: produce a substantially broader
candidate domain without deriving latent target sites from a successful
assembly, and validate unseen configurations/seeded growth. This integration
does not establish broad family transfer, matched-condition provenance,
continuous completeness, or blind growth.

## Follow-up: contact domains not conditioned on a successful assembly

`propose-unseeded-anchor-contacts.py` evaluates all 88 held-out frames. It uses
the original atom-valid motif poses, all frozen training contexts, and only
the training-fitted weights field of the weight artifact. It does not use
the successful-assembly choices or their inferred latent sites. Known target
atom positions and the fitted motif partition remain inputs; “unseeded” in
the filename does not mean blind growth.

Candidate alternatives may share a computational support record only when
cluster occurrence, interface, role and learned weight are identical; full
context identities are retained. The generator enumerates pairs/triples
whose positive t sum is one and which have common position and marking balls.
Given the current weight sizes (1/3, 1/2, 2/3), these exhaust possible sizes
of a filled group of distinct support occurrences. Periodic neighbor lookup
uses a reduced cell and an explicit omitted-image distance bound. Budget or
unresolved common-ball cases are reported, never converted into pruning.

The initial domains contain 26044 alpha context candidates and 13487 beta
candidates, with 129821 and 67064 pair contacts respectively. No triples,
image budget stops or unresolved triple tests occur. Initially, every motif
has some all-ports-supported context in 34/44 alpha and 36/44 beta frames.
These counts are NOT assembly counts: partner contexts may be mutually
exclusive alternatives at the same motif occurrence.

A necessary fixed-point consistency check accounts for that exclusivity.
For each contact, every participating motif must have an active context
containing all its ports in that contact. A context survives only if every
one of its ports has such a contact compatible with that context. Repeating
this removes all alpha contexts and leaves 15 beta contexts across six frames.
All six have an option for every motif. This is still only a necessary
condition: contact covers, geometric point identity and joint selection remain
to be solved. The finite original-pose pool is not continuous-space complete.

Twenty independent periodic-neighbor comparisons match exhaustive minimum-image
tests. On 200 small random systems, exhaustive context/contact-cover enumeration
finds 210 covers; the consistency pruning preserves every one. These tests
check necessary-pruning soundness, not sufficiency of its surviving domains.

Artifact: `/tmp/gcts-oxalic-modal-cohort-v1/unseeded-anchor-contacts-v2.json`.
The next search should operate on these unconditioned surviving context/contact
domains, not regenerate latent target sites from an already chosen cover.

## Follow-up: joint contacts and dynamic reference-engine obligations

`search-unseeded-contacts.py` selects contexts and a disjoint cover of their
ports by contacts. All six surviving beta frames admit such a cover. This is
a finite combinatorial diagnostic, not the reference scheduler; 200 small
independent exhaustive controls and the budget control pass.

More importantly, `compile-dynamic-context-filling.py` builds a reference-engine
model directly from the full surviving contact domains, **without reading
the selected contact covers**. All contact representatives become possible
latent sites. Sites use fractional coordinates rounded to 12 decimal places
modulo the supplied periodic cell, an explicitly numerical finite-domain
convention. All compatible port alignments are enumerated. Root obligations
are only the 16 or 32 atom sites; latent positive supports become active when
a tile is placed. Source atom occupancy remains a unit-weight prior.

All 88 compiled pools are complete within their declared finite domain. The
six nonempty pools have 2, 2, 4, 416, 2, 2 candidate placements respectively.
The unchanged reference `PointSearch` completes the six beta frames and
exhausts the other 82 pools. The successful frames are beta-0134, 0145, 0154,
0155, 0160, and 0162. Each solution selects two motif placements and fills 16
atom plus 14 activated latent obligations. Unselected latent sites are not
required. The runner's independent verifier now includes every touched
positive-support point, not just the original atom roots.

`verify-dynamic-context-filling.py` independently re-enumerates all 88 finite
pools, reconstructs learned supports/weights from source models and poses,
and checks all six solutions. Rational sums are exactly one at every active
point; position/marking common-ball residuals satisfy the numerical bounds.
The maximum observed marking radius across successes is approximately
0.14550 angstrom. Constructive integer-lift paths verify each selected periodic
connection graph reaches both motifs and the three unit translations.

The reference-engine tests additionally exercise dormant-point activation,
generation assignment, a newly exposed dead obligation outranking an existing
forced atom move, full-positive-support verification and rollback. The six
successful real cases take two accepted placements each, with a total of
three branches and no backtracks. This is not a speedup result: the pool was
already reduced using learned marking consistency, so removing marks from
this pool would not constitute an unmarked baseline.

This closes the selected-cover dependency for latent target sites in this
lane, but not target dependence itself: atom coordinates, motif partition,
original fitted poses and periodic cell remain given. No alpha frames pass,
most beta frames fail the restricted pool, and continuous poses, independent
trajectories, condition provenance and blind growth remain unresolved.

Artifacts under `/tmp/gcts-oxalic-modal-cohort-v1/`:

- `unseeded-contact-search-v1.json`: finite context/contact diagnostic.
- `dynamic-context-filling-pool-v1.json`, SHA256
  `60b67d8ecd0cada7a2e1924c3a0c35a0c2c2ec2e1e4c03e7b6c44fead2554176`.
- `dynamic-context-filling-search-v1.json`, SHA256
  `cb19a9ed5daf83882b3368da27db55a1e85e5f45b4912a636726bdcdb21131ed`.
- `dynamic-context-filling-check-v1.json`: independent replay of all pools and
  the six positive certificates. The deployed report has not yet been updated.
