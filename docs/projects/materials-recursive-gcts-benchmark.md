# Recursive GCTS benchmark for material growth

## Claim under test

From at most 1,000 species-labelled Cartesian positions, learn a bounded,
rotation-invariant hierarchy of overlapping clusters and local boundary
markings.  Use that hierarchy to continue a crystal or quasicrystal with fewer
search decisions than an atom-by-atom search, without being given a lattice,
unit cell, space group, cut-and-project coordinates, or generator labels.

“Exponential growth” applies to the implicit hierarchy: if the median support
amplification is `b > 1`, a level-`L` accepted macro placement represents
approximately `b^L` atoms.  Materializing or exporting `N` atomic coordinates
still has an unavoidable `O(N)` cost and must be reported separately.

## Benchmark ladder

All learners receive only positions and species.  Hidden construction metadata
is available only to the evaluator.

1. A randomly rotated binary crystal, to establish the easy periodic control.
2. A three-species icosahedral cut-and-project point set, to establish a true
   three-dimensional nonperiodic control with finite local complexity.
3. A composition-matched hard-core amorphous point set, as the null control.
4. Noisy and defected versions of 1–3.
5. Experimental or DFT structures with provenance and held-out spatial regions.

The algorithm must be shared across the suite.  A model-set lift, a recovered
translation lattice, or a Fibonacci-axis grammar may be reported as a competing
specialized baseline, but not as generic GCTS.

## Gates

### G0 — recursive representation

- At least three learned cluster levels beyond atoms.
- Every level has a finite, explicitly reported marking domain.
- Median support amplification at least 2 over two consecutive transitions.
- Identical hierarchy statistics after an arbitrary rigid motion.
- The amorphous null must not pass merely because a large ball contains atoms;
  its promoted recurring cluster types must vanish or pay their dictionary cost.

### G1 — blind continuation

Train on a radial core of 300–1,000 atoms and hide an outer annulus.  Place the
annulus without inspecting its atoms.  Score species/position precision and
recall after optimal rigid registration, minimum-distance violations, RDF and
coordination error, and structural-class agreement.  Passing requires at least
0.95 precision and recall on clean controls and zero hard-core violations.

### G2 — search advantage

Run atomic moves and recursive macro moves with identical compatibility rules,
frontier, timeout, and random seeds.  Report candidate evaluations, expanded
nodes, backtracks, accepted atoms per decision, wall time, peak memory, and
explicit-output time.  The target is a 10× reduction in expanded nodes at
10,000 represented atoms and increasing advantage at larger implicit sizes.

### G3 — marking causality

Compare learned markings with no markings, shuffled markings, radius-only
markings, and an oracle compatibility table while holding the cluster dictionary
and proposal order fixed.  A marking matters only if it reduces nodes/backtracks
or improves held-out validity.  The target is a 2× node reduction or a 10-point
success-rate improvement on at least one ambiguous quasicrystal/defect task.

### G4 — scaling

Report 10×, 1,000×, and 100,000× implicit continuation.  Separately materialize
fixed prefixes to establish linear output throughput.  A million-atom label is
not allowed unless one million coordinates are actually emitted or the result
is explicitly labelled an implicit representation.

## Current measured baseline

`scripts/materials_recursive_gcts.py` implements G0 as a generic colored-point
algorithm.  It learns an overlapping ball at each center, recursively colors
those centers with a bounded evidence-ranked vocabulary, expands the marking
domain geometrically, and learns the modal colored annular section for every
cluster type.

On the deterministic current fixtures:

| system | atoms | largest recurring supports by level | support ratios | top-level atoms / greedy macro decision | G0 |
|---|---:|---|---|---:|---|
| binary crystal | 515 | 7, 27, 203, 515 | 3.86, 7.52, 2.54 | 515 | pass |
| icosahedral model set | 507 | 14, 49, 270, 507 | 3.50, 5.51, 1.88 | 507 | pass |
| amorphous hard-core null | 507 | 0, 0, 0, 0 | 0, 0, 0 | 0 | reject |

These numbers establish recursive representation only.  They do not establish
G1 continuation, G2 search advantage, or G3 marking causality.  In particular,
the final level approaching the finite sample size is saturation, not evidence
of unlimited growth.

### First blind-frontier result

`scripts/materials_gcts_blind_continuation.py` trains on the 507-atom
icosahedral core and cannot inspect the 1,722 hidden atoms.  Three matching
colored atoms determine an arbitrary rigid orientation of a learned cluster.
The GCTS section is the bounded set of species-labelled pair distances learned
in the core; a proposed connection absent from that section rejects the patch.

| ablation | candidate patches | proposed sites | correct sites | precision | hidden recall |
|---|---:|---:|---:|---:|---:|
| cluster overlap, no marking | 16,340 | 24,288 | 84 | 0.0035 | 0.0488 |
| learned bounded marking | 60 | 180 | 180 | 1.0000 | 0.1045 |

This is a causal G3 result with the cluster dictionary, seed, confinement, and
alignment procedure held fixed: the marking removes every false-positive site
in the first wave and improves precision by 289×.  It is also partial G1
evidence, but not a G1 pass—the one-wave recall remains only 10.45%.  Iterated
frontier waves must preserve precision and reach at least 95% recall.

The initial iterative ablation exposed two further limits.  Independent
pair-distance sections reached 35.8% recall after four greedy waves but
precision fell to 81.7%.  Treating a mixed patch as an all-or-nothing decision
also stalled: at the ambiguous second wave a cluster could contain both a
forced site and an unresolved alternative.

The current implementation therefore lets a marking *improve* a proposal.
Clusters propose sites; a larger bounded section retains only the supported
part.  At level 2 the section is colored by learned level-1 cluster types, not
only atomic species:

| wave | action / marking | candidate patches | added hidden sites | cumulative hidden recall | precision |
|---|---|---:|---:|---:|---:|
| 1 | level-1 clusters + radius-2.25 section | 60 | 180 | 0.1045 | 1.0000 |
| 2 | level-1 proposals + radius-3 refinement | 8,100 | 60 | 0.1394 | 1.0000 |
| 3 | level-2 macros + level-1 colored section | 1,620 | 120 | 0.2091 | 1.0000 |

Thus clusters of clusters now make a successful blind continuation step: 360
of 1,722 hidden sites are reconstructed with no false atoms.  An exploratory
level-3 macro plus level-2 colored section of radius 4 selects another 80/80
correct sites (25.55% cumulative recall), but its current explicit 270-atom
candidate expansion is too slow for the regular test path.

The same generic local learner and marked-growth engine completely solve the
periodic control.  A 515-atom spherical core hides 904 atoms of the larger
crystal.  Four marked waves add 284, 366, 246, and 8 atoms respectively, ending
with all 1,419 oracle sites, 1.000 precision, and 1.000 hidden recall.  No unit
cell, lattice indices, translation vectors, or space-group label are supplied
to the learner; the hidden lattice coordinates are used only for evaluation.

| blind benchmark | training | hidden | final precision | hidden recall | status |
|---|---:|---:|---:|---:|---|
| binary crystal | 515 | 904 | 1.0000 | 1.0000 | G1 pass |
| icosahedral model set, tested path | 507 | 1,722 | 1.0000 | 0.2091 | partial |
| icosahedral model set, exploratory level 3 | 507 | 1,722 | 1.0000 | 0.2555 | partial |

These results also show that large supports alone are not hierarchical GCTS.
Unmarked level-2/level-3 macros have poor precision; the recursively colored
section is the component that makes their useful subset identifiable.

### Exact transform DAG

`scripts/materials_gcts_transform_dag.py` now converts exact, rotation-only
cluster types into a reusable DAG.  A parent stores child type IDs, proper rigid
transforms, and residual atoms not covered by complete children.  Provisional
fingerprint types are split by full colored congruence before reuse, including
a chirality split: mirror-related occurrences are distinct unless a proper
rotation maps them.

| system | recurring support sizes | root entries | represented atoms | root compression | level-3 dictionary: explicit / DAG |
|---|---|---:|---:|---:|---:|
| binary crystal | 7 → 57 → 474 | 36 | 474 | 13.17× | 8,531 / 777 |
| icosahedral model set | 14 → 55 → 471 | 30 | 471 | 15.70× | 4,451 / 441 |

Expansion reproduces the representative species and Cartesian coordinates
exactly, and every stored child transform has determinant +1.  Support grows by
3.93–8.56× per level on these finite controls.  This passes the implicit
representation portion of the exponential-growth benchmark: one accepted root
reference can stand for hundreds of atoms.  It does not remove the unavoidable
linear cost of emitting those coordinates.

### DAG parent search versus atomic search

`scripts/materials_gcts_dag_search_benchmark.py` tests the DAG as an actual
search action.  It generates 2,048 adversarial proper-rotation candidates; each
decoy is translated so at least one child of the correct type agrees with the
known level-2 configuration.  Atomic search transforms and scores every leaf of
every candidate.  DAG-GCTS scores the recursively colored child ports, accepts
one parent, and expands its atoms once.

| system | atomic leaves / DAG child marks | operation reduction | measured wall speedup | selected parent |
|---|---:|---:|---:|---|
| binary crystal | 474 / 24 | 19.56× | 19.73× | exact |
| icosahedral model set | 471 / 22 | 21.19× | 21.08× | exact |

This passes the 10× G2 search-advantage target for parent recognition and makes
the “exponential” distinction operational: the accepted action count is one
parent rather than 471–474 atomic leaves.  It assumes the child-cluster layer
has already been inferred; blind quasicrystal frontier completion remains the
harder unfinished benchmark.

### Blind DAG frontier experiment

`scripts/materials_gcts_dag_blind_frontier.py` now carries the learned DAG into
the blind icosahedral frontier rather than benchmarking preidentified parents.
It indexes rare, rotation-defining connector marks, keeps a bounded
frontier-diverse beam, composes exact SO(3) child/parent frames, proposes
level-3 parents from partial level-2 children, and separates a sparse expansion
DAG from a dense overlapping marking.  The latter retains every typed,
oriented level-2 port centered in the learned parent support, including ports
discarded by the nonoverlapping compression cover.  Ground truth is excluded
from the policy and used only after selection for scoring.

Starting from the proven three-wave state (507 training atoms plus 360 correct
continuations), the current beam has 500 level-1 and 500 level-2 hypotheses.
It finds 8,477 frontier parent poses.  The sparse-cover score alone has 138
top poses with three agreeing children.  Atomic section filtering improves a
selected proposal from 55.7% raw precision to 72.0%.  Rescoring with the full
overlapping level-2 port marking raises the best score to 11, leaves 68 top
poses, and selects 46 new sites, 40 of which match the held-out model set:
87.0% precision and 2.32% additional hidden recall.  This is the first measured
gain specifically from a cluster-of-clusters GCTS marking, but it is not yet an
acceptable growth action.

A bounded exterior halo was then learned from repeated occurrences in each
parent's canonical SO(3) frame.  The training set supplies 1,681 recurring
exterior ports across 13 of 14 level-3 types.  None are directly observed at
the blind frontier—as expected for a genuinely exterior section—but one-step
lookahead asks which ports become partially supported after a provisional
action.  It reduces the 68-way internal tie to 20 poses.  Feeding that future
support back to individual sites retains 21 atoms, 19 correct: **90.5%
precision** and 1.10% additional hidden recall.  This improves the action but
still does not meet the no-error recursive-growth requirement.

| blind level-3 policy | selected sites | correct | precision |
|---|---:|---:|---:|
| raw parent expansion | 149 | 83 | 55.7% |
| atomic section | 50 | 36 | 72.0% |
| internal overlapping level-2 ports | 46 | 40 | 87.0% |
| exterior one-step site lookahead | 21 | 19 | **90.5%** |
| lookahead + inferred module latent | 19 | 19 | **100%** |

Two negative ablations locate the remaining problem.  Requiring at least three
observed atomic neighbors changes nothing, so the six errors are not weakly
attached sites.  Voting across overlapping parent proposals also fails because
correlated pose variants vote together (392/554, 70.8%).  Full child-frame
matching rejects positionally coincident orientation decoys in a focused test,
but does not change this frontier result.  The surviving ambiguity therefore
requires a larger *hierarchical* context or tree-search lookahead, not a larger
atomic section or a missing rotation check.

Requiring each lookahead site to participate in two exterior ports is also
counterproductive (13/15, 86.7%).  Greedily displaying all mutually compatible
top branches accepts four macro actions and 60 unique sites, but only 52 are
oracle sites (86.7%).  Parallel display must therefore preserve the four branch
identities for rollback; compatibility alone is not evidence that every branch
is correct.

The current pure-Python end-to-end benchmark fell from 218 seconds to 148
seconds after caching type expansions, sharing SO(3) registrations, and
inverting dense port scoring.  An aggressive beam that retained only the 138
maximum sparse-cover poses was faster (134 seconds) but selected a different,
77.4%-precision action; it is rejected.  Sparse cover score is not a valid
upper bound on the denser overlapping marking.

Depth-2 branch evaluation also leaves all 20 branches tied: every branch
supports a distinct second parent with 21 internal port matches.  A
species-resolved pair marking over the full learned level-3 radius (9.94 local
length units) likewise leaves all 20 tied at score 0.9984.  Applying that
nonlocal section as a hard per-site filter is harmful (15/17, 88.2%).  The two
oracle mismatches therefore remain geometrically supported through two macro
depths and across the complete bounded marking domain.  Choosing the particular
held-out model-set realization now requires either a learned global/phason
state, external boundary information, or accepting multiple valid branches;
more static local thresholds are not justified by these ablations.

The input point cloud does, however, admit a zero-residual low-rank module
reconstruction.  A gated latent marking infers the quadratic unit, integer
six-dimensional lifts, internal acceptance window, and chemical shells from
the 507 known positions.  It activates only below a (10^{-5}) reconstruction
residual.  Applied after GCTS lookahead, it removes exactly the two false sites
and retains 19/19 correct atoms.  This is the first safe recursive IQC action
and a clean causal use case for a nonlocal marking.  It is not yet a generic
solution for arbitrary quasicrystals: the current module-family search is the
icosahedral quadratic control already implemented in
`materials_gcts_icosahedral_modelset.py`.

That learned model-set implementation is the current target baseline: it grows
507 atoms to 2,229 (4.40×) with 100% lift precision/recall, species accuracy,
and position accuracy.  Recursive GCTS must repeat its now-safe macro action to
match that result before the benchmark radius is increased toward million-atom
implicit representation.

`scripts/materials_gcts_dag_iterated_growth.py` remaps both hierarchy layers
after every accepted batch and backtracks through descending score strata when
the best stratum contains no new latent-valid sites.  Four measured waves add
70, 12, 1, and 14 atoms, all correct.  The state grows from the 867-atom
three-wave baseline to 964 atoms at 100% precision and 26.54% cumulative hidden
recall.  Waves 3 and 4 require three and twelve score strata respectively,
showing that rollback is operational.  This remains well below the 95% gate
and is not exponential growth yet.

An eight-wave run adds 103/103 correct atoms and reaches 970 total atoms at
100% precision, but hidden recall is only 26.89%.  The wave sizes are
70, 12, 1, 14, 1, 1, 2, and 2 atoms, and the run takes 426 seconds.  This is a
clear failure of the exponential-growth benchmark: after the first macro wave,
the frontier proposal mechanism degenerates into nearly atomic progress even
though the latent validator remains exact.

## Latent-directed rigid-parent ablation

`scripts/materials_gcts_latent_macro_growth.py` places complete learned level-3
DAG parents at centers proposed by the inferred internal-space marking.  A
ranked four-section marking and the unpruned fourteen-section atlas produce the
same result: 777 exact legal placements, of which a greedy overlapping cover
selects 90 and adds 210 atoms at 100% precision.  The largest marginal gain is
only five atoms.  This rules out overaggressive marking as the cause of the
plateau.  Rigid translated/rotated parents are primarily reconstruction
patches; by themselves they do not encode the quasicrystal inflation law.

## Recursive marked cluster rule

`scripts/materials_gcts_recursive_marked_growth.py` adds a distinct parametric
node to the transform hierarchy: `patch(R) -> patch(unit * R)`.  Its support is
not a copied finite atom list.  The learned six-dimensional acceptance section
is the GCTS marking that decides which module sites and chemical shells belong
to the enlarged parent.  From the same 507-atom input, the learner recovers
`unit = 1.618033988749895` with zero residual.  The first marked parent at
radius 14.562 contains 1,969 atoms; extending the requested envelope to radius
15 contains 2,229 atoms.  One recursive rewrite generates all 1,722 new atoms.
Held-out oracle evaluation reports 100% position and species precision and
recall, giving 1,722x action compression relative to atomwise placement.

This passes the exponential-style gate for the quadratic icosahedral control,
and it makes the role of the marking causal: removing the internal acceptance
section leaves the dense six-dimensional projection ill-defined.  It is not a
generic quasicrystal result.  The current module-family detector is specialized
to this control and must remain gated by its reconstruction residual.

## Generic translated-parent connection marking

`scripts/materials_gcts_recursive_connections.py` now tests a less specialized
route to the same hierarchy.  Every atom is the centre of a bounded local
colored cluster.  A cluster-of-clusters action connects a parent cluster to a
source cluster and proposes

`parent + scale * (source - parent)`.

The learned GCTS marking is a finite table over the parent local type, source
local type, and binned separation.  Separation is divided by the known level
scale before the marking is reused, so the same connection state can recur at
the next inflation level.  Local types use only colored radial neighbor counts;
the rule is invariant under rigid motion and has no lattice coordinates,
physical potential, cut-and-project lift, or material-specific labels.

On the ideal icosahedral control, the complete translated-parent action family
covers every target site in both 507→1,969 and 1,969→8,603.  This establishes
that translated copies of higher-order parents can be a complete generator,
not merely the origin-centred subset measured by the earlier iterated-marking
test.  The marking is learned only on the first transition (1,558 observed
connection states, 171 accepted) and then frozen.  The 1,969 already-known
sites are removed before scoring continuation; the target is the 6,634 genuinely
new sites:

| held-out consensus | proposed sites | correct | precision | target coverage |
|---|---:|---:|---:|---:|
| at least 1 overlapping action | 55,990 | 6,454 | 11.5% | **97.3%** |
| at least 2 | 35,626 | 6,034 | 16.9% | **91.0%** |
| at least 4 | 15,726 | 3,934 | 25.0% | 59.3% |
| at least 8 | 3,358 | 1,732 | **51.6%** | 26.1% |
| at least 16 | 504 | 332 | 65.9% | 5.0% |

This result identifies two distinct jobs that had previously been conflated.
The finite connection marking transfers almost the entire next patch, while
overlap agreement ranks confidence among its sites.  A high threshold is a
safe forced-move policy; a low threshold supplies a broad candidate frontier
for tree search.  No operating point yet meets 95% precision and recall at
once, so this is a useful generic GCTS benchmark rather than a solved growth
algorithm.  The next step is to learn a bounded marking on the *consensus
neighborhood itself*—a second-order cluster type—then search only the residual
ambiguous frontier.

### Second-order consensus-neighborhood marking

`scripts/materials_gcts_consensus_neighborhood.py` now promotes the overlap
field itself into another cluster level.  A proposed site's bounded descriptor
contains its action multiplicity, agreement of predicted colors, diversity of
parent/source connection states, and radial counts of neighboring proposals.
Both a continuous logistic section and a finite binned likelihood section are
learned.  These remain rigid-motion invariant and contain no physical energy,
lattice direction, or held-out oracle coordinate.

To prevent the first transition from labelling its own proposals, five spatial
parent folds are used.  Each fold's connection table is learned on the other
four folds and applied only to the excluded parents.  Known sites are removed.
The resulting 3,832 out-of-fold continuation proposals contain 1,462 positives
and 2,370 genuine negative
examples.  The second-order marking is fitted there, frozen, and applied to
66,110 novel-site proposals on the 1,969→8,603 transition.

The atom-growth factor learned from the training transition is 3.8836.  It
predicts 7,647 total next-level sites, hence a budget of 5,678 *new* sites after
the 1,969 known sites are merged, without inspecting the 8,603-site target.  At
fixed multiples of that continuation budget, the second-order marking causally
improves multiplicity-only ranking:

| next-level site budget | selected second-order policy | second-order P / R | vote-only P / R |
|---:|---|---:|---:|
| 2,839 (0.5×) | continuous section | **70.87% / 30.33%** | 53.89% / 23.06% |
| 5,678 (1×) | equal-rank section ensemble | **48.47% / 41.48%** | 43.64% / 37.35% |
| 11,356 (2×) | finite binned section | **32.69% / 55.95%** | 29.48% / 50.47% |

This is the first leakage-controlled gain from an explicit cluster of
connection proposals rather than from raw overlap multiplicity.  It is not a
G1 pass.  Absolute score thresholds calibrated on 507→1,969 transfer poorly
because candidate density and class prevalence change sharply at the next
level.  The current recursively stable policy therefore ranks the atom budget
predicted by the learned growth factor.  The next marking must model that
density transformation explicitly or learn a higher-order sparse cover so an
absolute forced-move decision remains calibrated across levels.

### Frontier attachment and third-order marking

`scripts/materials_gcts_frontier_attachment.py` adds the accepted
configuration to the marking domain.  For each recursive proposal it records
bounded colored neighbor counts and nearest distances to already accepted
atoms, together with source-color and learned target-color connection votes.
The latter is retained as a separate hypothesis: using the learned
state-to-color mode directly is a negative result (40.7% held-out species
accuracy versus 56.0% for the source-carried color).  The higher-order marker
may use their agreement, but does not replace the better color rule.

The frontier marker is trained on the same 3,832 cross-fitted continuation
proposals and frozen.  On the 66,110 held-out novel-site candidates it produces
a sharply purer frontier than consensus alone:

| ranked frontier budget | correct | precision | novel recall |
|---:|---:|---:|---:|
| 250 | 238 | 95.2% | 3.59% |
| 500 | 488 | **97.6%** | 7.36% |
| 1,000 | 868 | 86.8% | 13.08% |
| 2,000 | 1,530 | 76.5% | 23.06% |

An explicit third level then forms a broad provisional covering (twice the
learned novel-site budget), treats its colored proposal neighborhood as the
new marking domain, and fits another bounded section.  It improves the full
5,678-site operating point from 48.5% precision / 41.5% recall to **53.3% /
45.6%**.  Its diagnostic top 250 sites are 250/250 correct, but there is no
unlabelled score gap at rank 250, so that number is not used as a policy.

The operational policy accepts only the current maximum-score symmetry
plateau, merges it into the known configuration, and recomputes both frontier
levels.  Eight frozen-policy waves add:

`10 → 2 → 120 → 36 → 24 → 8 → 4 → 4`

All 208 proposed sites are correct, for 100% precision and 3.14% novel recall.
The 120-site third wave is a verified macro action selected as a cluster of
proposal clusters, not 120 atomwise oracle decisions.  Later plateaus shrink,
so this is safe hierarchical progress rather than exponential continuation.

The first implementation re-ranked a fixed proposal family.  The current
regenerative search now recomputes local cluster types after every accepted
macro and evaluates only incremental connection pairs involving a new parent or
source.  Its radial envelope is also learned rather than read from the held-out
target: the finite-sample extent ratio is 1.6629 and gives a 24.010 continuation
radius.  Eight regenerated waves add:

`12 → 104 → 12 → 4 → 36 → 24 → 24 → 12`

They contain **228/228 correct novel sites** (3.44% recall).  More importantly,
the available frontier grows from 63,890 to 66,254 candidates while accepted
sites are removed.  New actions therefore outpace consumption; this is actual
continuation from newly created clusters, not replay of a precomputed list.
The plateau sizes still do not amplify monotonically, so the exponential gate
remains open.

Two calibration ablations remain negative.  Scaling a training-pure prefix by
the expected surface factor selects 3,828 sites at only 60.2% precision, while
an absolute 99%-training-precision score threshold transfers at about 17%
precision.  Minimum-separation pruning changes no result because the false
branches are locally valid, non-colliding alternatives.  Maximum-score plateau
iteration is the only currently verified self-calibrating forced-move policy.

## Next implementation target

Continue the exact plateau search with new recursive connection proposals after
each accepted macro, and learn a branch-level lookahead marking when the top
plateau ceases to be pure.  Learn the transformation of proposal density and
class prevalence between hierarchy levels, or replace dense pair proposals
with a learned sparse parent cover.  Generalize the parametric recursive-node
interface so crystals learn a
translation quotient, substitution quasicrystals learn an inflation or
superspace section, and amorphous controls decline the deterministic rule.  Add
held-out perturbations and non-icosahedral model sets so a module-specific
success cannot masquerade as generic GCTS.  The generic G1 gate remains 95%
hidden recall with exact species and position validation.

## Generic parametric dispatcher and million-atom curve

> **Scoreboard correction.** This section is the specialized algorithmic
> ceiling, not the final generic GCTS pass. The shared dispatcher selects among
> translation quotient, internal section, substitution product, and planar
> address encoders. Its exact growth is valuable evidence and a target for the
> generic cluster/port grammar, but `family_specific_backends_remain = true`
> now forces the common research gate to stay red. Only unseen recursive
> execution by one frozen cluster/port grammar can turn that gate green.

`scripts/materials_gcts_parametric_recursive.py` now exposes one discovery
contract over an unlabeled colored point cloud.  The local recursive hierarchy
is learned first and gates all later rules.  The NaCl control learns supports
of 7, 27, and 164 atoms, then discovers three composable species-preserving
translations directly from the finite cloud; removing its supplied periodic
cell does not change the generated 2x2x2 continuation.  The IQC learns supports
of 14, 49, and 270 atoms, registers its ten shortest-bond axes to a canonical
icosahedral frame, and activates the internal-section rule only at low lift
residual.  An arbitrary SO(3) rotation plus translation is inverted before
learning and restored after growth.  The amorphous control has supports
0, 0, and 0 and declines deterministic continuation.

The dispatcher also recognizes a second, non-icosahedral quasiperiodic family.
For the 729-atom three-dimensional Fibonacci-product control, it recovers three
orthogonal shortest-bond axes, two gap clusters, the minimum-description
substitution `A -> AB, B -> A`, and an eight-entry species decoration marking.
Its recursive supports are 4, 17, and 81 atoms.  One held-out rewrite produces
3,375 exact positions and species.  A rotated and translated input produces the
same transformed continuation, including when axis reversal selects the
conjugate word presentation.

The internal-section enumerator no longer scans a six-dimensional coefficient
box.  It writes each Cartesian coordinate as `a + b*unit`, filters the physical
and conjugate internal intervals, enforces the three lift parity constraints,
and combines only surviving coordinate sections.  The learned IQC rule's
second inflation contains 8,603 atoms and matches an independent hidden-window
and species certificate.  `scripts/materials_gcts_recursive_scaling_benchmark.py`
measures the complete implicit curves:

| action | NaCl atoms | icosahedral IQC atoms | Fibonacci-product atoms |
|---:|---:|---:|---:|
| 0 | 216 | 507 | 729 |
| 1 | 1,728 | 1,969 | 3,375 |
| 2 | 13,824 | 8,603 | 13,824 |
| 3 | 110,592 | 37,073 | 59,319 |
| 4 | 884,736 | 155,097 | 250,047 |
| 5 | 7,077,888 | 657,057 | 1,061,208 |
| 6 | — | 2,791,097 | — |

On the development machine, count-only IQC enumeration through action 6 takes
2.72 seconds for the last level and about 39 MB peak process memory.  A separate
materializing run produced 1,007,649 atoms at radius 115 in 2.32 seconds, with
about 400 MB peak memory.  These are algorithm/runtime benchmarks, not MD
equivalence: no dynamics, defects, stresses, or thermodynamics are inferred.

`scripts/materials_gcts_million_emission_benchmark.py` replaces that earlier
ad-hoc materialization note with a reproducible explicit certificate. The
learned 216-atom NaCl quotient streams 7,077,888 species-labelled positions in
five macro actions (16.2 seconds in the current recorded Python run). The
507-atom IQC first learns the same three-component GCTS mark used by local
port growth, then promotes it to a rank-six address macro and streams 2,791,097
positions in six actions (9.7 seconds). The learned Fibonacci-product
substitution streams 1,061,208 sites in five actions (2.6 seconds).
Neither output cloud is retained. Instead, an order-independent 256-bit sum of
per-site cryptographic hashes is compared with a structurally independent
oracle: direct rocksalt half-grid parity for NaCl, sealed unit/window/shell
constants for the IQC, and an independently generated hidden substitution
word for the Fibonacci product. All three digests and species counts match
exactly. The observed geometric means are 8.000, 4.202, and 4.292 sites per
recursive action. This closes the **explicit million-site emission** benchmark
for one crystal and two quasicrystal controls. IQC emission performs no
coordinate lifting, model refit, target
lookup, or physical-potential call; a regression makes coordinate lifting
raise during macro inference. This gives GCTS a concrete multiscale role:
local port search validates and propagates the marking through 66,935 exact
sites, then the same mark becomes the fast clusters-of-clusters address
production. Writing coordinates remains O(N), and the stricter requirement
that crystal, substitution, and IQC use one production kind remains red.

The inference artifacts are now physically separated from their trainers.
The local `PortCoverGraph` retains the 789 promoted typed-distance ports,
frontier width, origin, and carried mark, but drops all 13,111 fitting-only
port pairs and the global section. The promoted million-site artifact is
smaller still: `MarkedAddressMacro` contains only the learned algebraic unit,
window radius, species thresholds, origin, and rigid frame. It contains no
port atlas, seed marks, target sites, or fitting model. Structural regressions
enforce both exclusions, so the cost comparison no longer counts discarded
training evidence as required inference state.

## Perturbation gate

`scripts/materials_gcts_noise_robustness_benchmark.py` adds independent Gaussian
coordinate noise before discovery and removes the crystal's periodic metadata.
At sigma 0.005 in the control length units, all three deterministic families
retain a rule: NaCl learns supports 7, 27, 137 and grows to 1,728 atoms; the
icosahedral control learns 14, 49, 270 and grows to 1,969; the Fibonacci product
learns 4, 11, 51 and grows to 3,375.  Four independently seeded 507-atom
hard-core amorphous controls produce zero deterministic false positives.

At sigma 0.01, the IQC and Fibonacci controls lose their level-3 recurring
support and the dispatcher returns `none`.  This is the intended conservative
failure mode.  The noise path currently recovers and snaps an underlying ideal
topology.  It does not extrapolate phonons, thermal displacement correlations,
defects, stress fields, or time evolution; those require a residual/displacement
field model layered on top of the recursive structural rule.

## Multi-species crystal and local-defect suite

`scripts/materials_gcts_real_crystal_benchmark.py` applies the same unlabeled,
cell-free discovery path to six crystallographic prototypes: NiAl B2, Cu3Au
L1_2, GaAs zinc blende, NaCl rock salt, SrTiO3 perovskite, and the 168-atom
Cd6Yb 1/1 approximant cell.  The first five inputs contain 128--320 atoms.  The
Cd6Yb case uses an observed 2x2x2 crop (1,344 atoms), because one isolated unit
cell contains no repeated translation from which a cell-free learner could
infer its quotient.  All six learn three translations and a consensus colored
motif, then produce the exact held-out 2x2x2 continuation: 8x as many atoms,
with exact position and species sets.

The quotient learner scores candidate translation bases by how completely a
small colored motif explains the observed finite box.  This matters when the
input contains a non-repeating residual.  In
`scripts/materials_gcts_defect_locality_benchmark.py`, a 3x3x3 NaCl crop is
modified by one vacancy, one Na-to-K substitution, or one Xe interstitial.  A
single quotient action produces 1,727, 1,728, and 1,729 atoms respectively,
matching the clean 6x6x6 continuation with exactly the original one-off defect.
The defect is not multiplied into the seven synthesized blocks.

This is the first operational separation between a learned cluster-of-clusters
and its residual field: consensus structure receives the recursive rewrite;
unexplained local state is carried once.  It is still a static ideal-geometry
test.  The next gate is to learn smooth displacement/strain residuals and to
test defects near a growth frontier; the current code does not predict defect
energetics, kinetics, or finite-temperature dynamics.

## Explicit recursive application and marking ablation

The earlier scaling table used exact count recurrences, but the one-step IQC
and substitution materializers did not retain the enlarged parent envelope.
Calling them twice therefore regenerated the first child.  This is now an
explicit regression gate rather than an implicit projection.
`apply_rule_actions` keeps the original training cloud as the marking witness
and advances the parent state by an arbitrary number of recursive actions.
`scripts/materials_gcts_explicit_recursive_benchmark.py` materializes two
levels and independently checks every colored site:

| family | input | action 1 | action 2 | atomwise placements / macro action |
|---|---:|---:|---:|---:|
| NaCl translation quotient | 216 | 1,728 | 13,824 | 6,804.0 |
| icosahedral internal section | 507 | 1,969 | 8,603 | 4,048.0 |
| Fibonacci-product substitution | 729 | 3,375 | 13,824 | 6,547.5 |

Thus the same learned node now acts on a cluster, then on the resulting
cluster-of-clusters.  These ratios measure discrete placement decisions, not
wall-clock speedups over MD.

`scripts/materials_gcts_recursive_marking_ablation.py` makes the role of the
marking causal.  For the second IQC inflation, the learned integer module,
physical-radius bound, and lift-parity connections admit 6,171,443 candidate
sites if its bounded internal section is removed.  The section retains 8,603,
rejecting 99.86% of algebraically connected but incompatible candidates.  For
the Fibonacci product, there are 392 bounded two-symbol child grammars before
observed parent sections are enforced and six remain consistent; the learned
minimum-description marking selects `A -> AB, B -> A`.  For NaCl, quotient
geometry without a species-preserving marking leaves `2^56` possible binary
decorations across the seven new images, while the colored connection marking
selects one.

The ablation deliberately removes only the section/connection marking while
retaining the learned geometry.  It therefore measures GCTS information rather
than comparing against a completely uninformed random generator.

## Markings on non-ideal parent geometry

`scripts/materials_gcts_hierarchical_residual.py` adds a synthetic but fully
held-out displacement benchmark.  Its input is a 1,024-atom NiAl B2 point cloud
with no cell or axes.  The atomic coordinates contain a bounded displacement
decoration generated at three nested binary parent levels.  The learner first
recovers a short same-species translation frame and the two-atom colored
quotient.  It then fits seven possible octant sections at each observed level
and tests whether the section vectors themselves follow a low-residual scalar
recurrence.  This is a marking on a cluster-of-clusters, rather than another
atom type or a physical interatomic potential.

The hidden recurrence ratio is 0.58; the learner obtains
0.5799999999999651.  Both the coordinate fit and the between-level recurrence
have relative error below `6e-13`.  Extrapolating the next two parent markings
materializes 1,024 -> 8,192 -> 65,536 atoms with exact colored position sets,
or 32,256 atomwise placements per macro action.  A flat ablation copies the
observed 8x8x8 displacement block but omits its new parent section.  It retains
the chemical quotient while missing held-out coordinates by 0.00620 angstrom
RMS; the marked rule is accurate to `5e-14` angstrom RMS.  A rotated and
translated input gives the correspondingly transformed output.

An IID displacement field on the identical B2 geometry is a negative control.
It is rejected because either the finite hierarchy fit or its between-level
recurrence exceeds the 10% relative-error gate.  Thus the engine does not call
every coordinate residual a recursively growable marking.

This control establishes the interface and causal advantage, not a claim about
phonons or real strain fields.  Its octant recurrence is deliberately known to
exist, the input is dyadic, and there is no energetic relaxation.  The next
tests must mix a recurrent displacement marking with isolated frontier defects
and replace the planted recurrence with modulations measured in real material
configurations.

## Recurrent parent field with local frontier defects

`scripts/materials_gcts_frontier_defect_benchmark.py` combines the recursive
displacement marking with sparse residual handling.  A vacancy, Na-to-K-style
substitution label, or interstitial is placed on the frontier of the observed
8x8x8 B2 parent.  The structural learner excludes rare chemical labels while
fitting the quotient and parent sections, reconstructs the expected observed
parent, and records only its sparse set difference as additions or removals.
Those residual operations are carried once after every structural rewrite.

After two actions the three cases contain 65,535, 65,536, and 65,537 atoms.
Their exact held-out position/species sets contain one vacancy, one
substitution, and one interstitial respectively.  Copying the complete
observed parent at each action would instead create 64 instances.  Thus the
recursive marking applies to the consensus cluster-of-clusters while the
nonrecurring state remains local, including when it occurs at the attachment
frontier.

This test exposed a frame-identifiability issue: averaging local translation
vectors lets a missing edge atom perturb the global basis.  The learner now
jointly fits the translation frame, motif, and parent sections.  Constant and
single-bit (affine) octant modes are assigned to the quotient frame; only
pairwise and triple octant interactions are allowed in the GCTS marking.  This
gauge makes the decomposition exact with sparse missing samples and prevents a
defect from leaking into every generated coordinate.

The defect policy is intentionally conservative.  Residual additions and
removals must total at most 2% of the observed cloud, and no new defect is
predicted.  Energetic defect propagation, dislocation motion, and relaxation
remain outside the present static continuation benchmark.

## Experimental dodecagonal approximant from COD

`scripts/materials_gcts_cod_approximant_benchmark.py` vendors the measured
coordinates and symmetry operations of Crystallography Open Database entry
[1521830](https://www.crystallography.net/cod/1521830.html).  The structure is
the periodic Ta-V-Te approximant reported alongside a dodecagonal
quasicrystalline telluride.  Its P -4 21 m cell has 314 symmetry-expanded
sites.  Shared, fractionally occupied Ta/V positions are retained as a
virtual-crystal `Ta/V` point color rather than converted to an invented random
occupational realization.

From that one experimental cell, the generic bounded hierarchy learns
recurring supports of 11, 39, and 139 atoms.  Recurring clusters cover 96.82%,
99.36%, and 99.36% of the measured sites, with marking confidence 0.748,
0.842, and 0.810.  Randomly permuting the same chemical-color multiset changes
the supports to 4, 37, and 138, establishing that the first hierarchy in
particular uses measured chemical decoration rather than geometry alone.

The experimental CIF explicitly supplies a periodic cell, so the classifier
calls the resulting top parent a `periodic crystalline approximant`; it does
not infer “quasicrystal” from the publication title or chemical family.  Cell
parent actions give the exact count curve 314 -> 2,512 -> 20,096 -> 160,768 ->
1,286,144.  Two explicit actions preserve every measured coordinate and
virtual-crystal color, corresponding to 9,891 atomwise additions per macro
action.

This is the first externally sourced approximant benchmark, but it is not a
true aperiodic-coordinate dataset.  Its million-site continuation ultimately
uses the experimental periodic boundary condition.  The internal 139-atom
GCTS hierarchy makes the cell interpretable as clusters of clusters; the
translation of that complete cell is still the easy crystalline part.  A true
quasicrystal test requires an aperiodic diffraction/superspace refinement or a
large experimentally reconstructed patch with a held-out region.

## Experimental aperiodic Sc-Zn hierarchy

`scripts/materials_gcts_experimental_sczn_benchmark.py` downloads the
supplementary real-space model from the Sc-Zn icosahedral-quasicrystal
refinement and verifies its pinned SHA-256 before parsing it.  The P1 model has
41,981 atom rows and 37,531 merged point sites; coincident Sc/Zn occupational
alternatives remain the virtual color `Sc/Zn`.  This is a genuine finite
aperiodic model rather than a periodically repeated approximant cell.

Atom-centred clustering is the wrong abstraction for this input: the refined
Tsai clusters are centred in voids.  The new learner therefore ranks chemical
colors by rarity and searches for recurrent antipodal shells.  It is not given
the element name, cluster centres, or paper's cluster labels.  It selects Sc
and recovers 173 complete twelve-site shells with learned mean radius 4.9149
angstrom.  Their median 7.8-angstrom decoration contains 156 measured point
sites.  The cluster-centre graph independently has two dominant learned links,
12.0 and 13.8 angstrom.

The centre graph supplies a real clusters-of-clusters benchmark.  A bounded
radial section records counts on the two connection shells; successive levels
add their learned inflated copies.  Quantizing counts in bins of four makes the
section insensitive to the cut boundary of the finite experimental model.
Three recurring levels have largest supports 13, 38, and 98 fundamental
clusters and cover 98.84%, 97.11%, and 74.57% of detected centres.  Their next-
shell boundary markings have confidences 0.573, 0.470, and 0.481.  Thus this is
an actual hierarchy over void-centred atomic clusters, not a relabeling of
individual atoms.

A blind scale-and-origin scan learns 1.618 as the best inflation proposal,
within `3.4e-5` of the golden ratio.  One parent proposal accounts for ten
accepted fundamental-cluster placements, or 1,560 decorated atom instances,
instead of ten separate cluster decisions.  This is the first measured
supercluster action in the suite.

The unmarked proposal by itself is intentionally weak: its spatially held-out
precision is only 3/18.  A bounded GCTS section now describes the measured
7.8-angstrom atomic decoration around a `(parent centre, source centre)` pair.
It uses intrinsic radial bands and projections onto the pair axis, so a rigid
rotation and translation leave it unchanged.  A radial/axial histogram and an
independent set of even angular moments each choose their three-neighbour
threshold using training leave-one-out predictions only.  Requiring both
sections to accept gives 3/3 on the original small held-out split.  Pair
distance alone gives only 3/8; one histogram section gives 3/5.  Removing the
Sc/Zn colors does not change this split, so this gain is properly attributed to
the bounded geometric marking rather than chemistry.

`scripts/materials_gcts_section_marking.py` now contains the material-generic
algorithm used by the stronger replication.  Its inputs are an arbitrary
colored point cloud, independently learned centers, and proposed
`(parent, source)` pairs.  It contains no element names, lattice coordinates,
or quasicrystal labels.  Both finite descriptors are exactly invariant under a
common rigid motion.  Settings are selected by cross-validation that holds out
complete parent groups, preventing proposals around one parent from leaking
across the fit/validation boundary.  A periodic B2-like positive control, in
which every quotient translation is legal, correctly reduces to an
always-accept section instead of inventing false restrictions.

`scripts/materials_gcts_multi_origin_marking_benchmark.py` applies that generic
API to the measured model.  It excludes the inflation origin's trivial fixed
point, trains on 83 complete parent centres, and holds out 90 different parent
centres.  The split is a 16-angstrom spatial checkerboard of parent coordinates
and never reads a target label.
There are 2,261 training candidates and 2,441 held-out candidates.  Only 218
held-out proposals are real continuations, so accepting everything has 8.93%
precision and creates 2,223 false search branches.

The fully automatic grouped fit chooses `k=3, threshold=0.35` for the histogram
and `k=7, threshold=0.35` for the moment section.  Their conjunction accepts
159 placements, 120 of which are correct: 75.47% precision and 55.05% recall.
False branches fall from 2,223 to 39, a 57-fold reduction, and the verified
placements represent 18,720 decorated atom instances.  A separately reported
precision-first operating point freezes the earlier `k=3` thresholds 0.65 and
0.85.  It retains 84.09% precision and 33.94% recall, with 14 false branches—a
158.8-fold reduction.  This establishes a causal role for GCTS marking: the
inflation rule proposes geometry, while the bounded section controls the
precision/recall and branching of the ensuing tree search.

This still does **not** justify unrestricted experimental growth.  Recall is
deliberately low, the finite model cannot certify iterations outside its
boundary, and 14 false branches still require overlap checks or backtracking.
The remaining gates are a complete multi-parent cover of the next ideal level
and the same frozen marking on a second experimental reconstruction.

## Frozen marking reused across ideal-IQC levels

`scripts/materials_gcts_ideal_iqc_iterated_marking.py` exercises the new generic
API across successive scales instead of randomly splitting one patch.  It fits
only the 507 -> 1,969 transition, freezes the marker, then presents every
nontrivial origin-centred inflation candidate from the independently generated
1,969 -> 8,603 transition.  No label from the second transition is used during
training or setting selection.

The first transition has 222 valid mapped actions.  The next has 944, a
4.252-fold increase close to the volumetric inflation rate.  An unmarked search
would branch on all 1,968 candidates at 47.97% precision and retain 1,024 false
branches.  The high-recall histogram section retains 612 correct actions out of
1,052: 58.17% precision, 64.83% recall, and only 440 false branches.  Thus the
number of correct actions captured by the frozen marker grows 222 -> 612, a
2.757-fold recursive action factor.  The conjunctive section is more
conservative: 252/392 correct, 64.29% precision, and 140 false branches, a
7.31-fold reduction from the unmarked search.

This is the first cross-level, frozen-marking certificate.  It proves that a
bounded GCTS section learned at one inflation level can remain predictive at
the next and can carry an exponentially increasing subset of correct actions.
It does not yet generate all 8,603 atoms: the test classifies the subset reached
by origin-centred inflation, while the remaining sites require translated
parent actions or a complete substitution cover.

## Current crystal/quasicrystal scaling gates

### Common two-level exponential-action protocol

`scripts/materials_gcts_recursive_program.py` now gives the planar atlas and
the three 3D recursive learners one family-blind contract. It first uses a
rotation-invariant covariance screen plus exact seed replay to recognize an
intrinsically planar union; otherwise it calls the existing structure-blind
3D dispatcher. No crystal, quasicrystal, dimensionality, cell, or held-out
label is passed to the selector.

`scripts/materials_gcts_common_recursive_benchmark.py` applies the same gate
to every admitted program: exactly materialize two independently generated
unseen levels, then—and only then—allow a symbolic count to one million. A
flat action means placing one learned primitive cluster; a recursive action
means promoting one cluster-of-clusters program level.

| learned from positions + species | explicit certificate | minimum sites/action factor | first symbolic ≥1m | flat cluster actions / recursive actions | compression | marking ablation effect |
|---|---:|---:|---:|---:|---:|---:|
| NaCl translation quotient | 216 → 1,728 → 13,824 exact | 8.000× | action 5: 7,077,888 | 884,709 / 5 | 176,942× | rejects all but one colored quotient decoration |
| icosahedral internal section | 507 → 1,969 → 8,603 exact | 3.884× | action 6: 2,791,097 | 199,328 / 6 | 33,221× | rejects 99.86% of algebraic lift candidates |
| Fibonacci-product substitution | 729 → 3,375 → 13,824 exact | 4.096× | action 5: 1,061,208 | 265,120 / 5 | 53,024× | rejects 98.47% of bounded rewrite grammars |
| rotated 30° hBN pose/address macro | 746 → 2,954 → 11,696 exact | 4.000× | action 5: 1,048,576 | 261,958 / 5 | 52,392× | pose ablation loses 50% recall |

The common pass criteria are deliberately stronger than a million-site count:
two exact unseen levels, minimum multiplicative factor above 3, at most six
recursive actions to one million represented atoms, at least 10,000× fewer
program actions than flat primitive-cluster placement, a causal marking
ablation, and rejection of the amorphous negative control. Explicit coordinate
emission remains linear in atom count. The exponential result is compression
of represented structure per recursive action, not a claim of sublinear MD or
free materialization.

The geometric evidence extractors are still specialized (translation
residues, quadratic internal section, gap substitution, planar address atlas).
The finite recursive executor is no longer entirely specialized: the typed
transform/section compiler described below handles translation, substitution,
planar pose/address graphs, and a parametric continuous internal-section
generator through one production contract.

### First shared typed transform/section compiler

`scripts/materials_gcts_typed_productions.py` compiles discovered geometric
evidence into one finite grammar. Each parent type has transformed child
references at local addresses plus bounded section marks describing which
faces of the parent neighborhood they contact. These marks are connection
labels, not physical potentials. The executor contains no crystal-versus-
quasicrystal branch: it repeatedly applies the same type-incidence rewrite.

| point-set input | induced graph | exact count certificate | symbolic ≥1m |
|---|---:|---:|---:|
| 216-atom NaCl | 1 type, 1 production, 8 child references | 216 → 1,728 → 13,824 | action 5: 7,077,888 |
| 507-atom ideal IQC | 1 parametric production, rank-6 address domain, learned 3D section | 507 → 1,969 → 8,603 exact | action 6: 2,791,097 |
| 729-atom Fibonacci product | 8 types, 8 productions, 27 child references | 729 → 3,375 → 13,824 | action 5: 1,061,208 |
| 746-atom rotated 30° hBN | 2 pose types, 2 productions, 8 child references | exact circular crops 746 → 2,954 → 11,696; address envelopes 1,024 → 4,096 → 16,384 | action 5: 1,048,576 |

`scripts/materials_gcts_typed_production_benchmark.py` verifies that all four
graphs are unchanged by a tested proper rotation and translation, agree with
two levels of explicit atom geometry, reach one million through the same
counter rewrite, and reject the amorphous control. Planar materialization is a
circular crop of a square recursive address envelope, so both counts are
reported rather than conflated. The compiler never
reads the discovered rule's family string; it selects an adapter from which
structural evidence fields are actually present. Finite productions use one
type-incidence counter. The IQC production is necessarily parametric: it
enumerates integer rank-6 addresses in the physical envelope and accepts them
with the learned bounded 3D internal section. They share a production contract,
not one finite execution algorithm. This is a real common recursive layer, but
not yet a common geometric learner: translation residues, gap words, planar
poses, and algebraic lifts are still extracted by different front ends.

This extension also found a coordinate-frame defect in the planar selector:
its growth envelope had been centred at the ambient origin. The generic
recursive entry point now infers the observation centre from the finite sample,
so a translated and rotated input produces the same typed graph.

### Family-blind hypothesis competition

The earlier selector still tried recognizers in a hand-written order and
returned after the first successful family. That control flow has now been
removed. `discover_recursive_program_candidates` attempts the planar,
translation, product-substitution, and internal-section hypotheses without a
phase-category guard. Every admitted proposal reports normalized seed
residual, description entries, exact seed replay, recursive hierarchy support,
seed mismatch, and a common fit-plus-description score. Selection is the
minimum score and is invariant to proposal order.

`scripts/materials_gcts_model_selection_benchmark.py` provides a nontrivial
competition rather than four one-candidate demonstrations. The Fibonacci
product admits both its exact substitution grammar and an approximate finite
translation quotient. That quotient reproduces only 194 of 729 observed sites
exactly and is penalized for its seed mismatch. The common score selects
substitution at 0.019204 versus 1.560741 for the quotient, a margin of
1.541536. NaCl selects its quotient,
the ideal IQC its internal section, and rotated 30-degree hBN its planar atlas.
The amorphous control admits zero proposals. No crystal, quasicrystal, planar,
or amorphous label is provided to proposal generation or selection.

### Unified selector robustness gate

`scripts/materials_gcts_selection_robustness.py` perturbs the inputs before the
family-blind proposal stage and evaluates the selected program against a clean,
larger scaffold. This tests the integrated selector rather than invoking a
known family-specific learner directly.

| observed seed | selected production | clean grown P / R / species | registered RMS |
|---|---|---:|---:|
| NaCl + 0.005 A Gaussian noise | translation quotient | 100% / 100% / 100% | 0.0163 A |
| ideal IQC + 0.005 A Gaussian noise | internal section | 100% / 100% / 100% | 0.0244 A |
| Fibonacci product + 0.005 A Gaussian noise | substitution | 100% / 100% / 100% | 0.0108 A |
| 30-degree hBN + 0.006 A noise + 3.5% vacancies | planar pose/address | 100% / 99.20% / 100% | 0.0149 A |

A single NaCl chemical substitution retains the quotient hypothesis but is
correctly marked as an inexact seed replay. A 1%-vacancy noisy IQC initially
exposed a frame-origin failure: the arithmetic centroid moves off the
algebraic module when atoms are missing. The learner now estimates the
inversion centre from the densest cluster of antipodal-pair midpoints. With no
oracle centre or hidden lift, it selects the internal section in 1.74 seconds
and reconstructs all 1,969 clean first-level sites at 100% position/species
precision and recall. A bounded lift-complexity preflight still prevents an
invalid frame from entering a large coefficient box. Two independently seeded
amorphous controls admit zero proposals. More severe and nonuniform 3D damage
remains open.

### Finite-window and minimum-description stability

`scripts/materials_gcts_finite_window_benchmark.py` changes the observed
window before discovery. It covers cubic crystal boxes, spherical IQC crops,
Cartesian substitution products, and circular bilayer disks. For every input,
the family-blind selector is rerun, its learned parameter signature is compared
across sizes, and one clean continuation beyond the observed window is checked
by exact position/species set.

| family | observed atom range | windows | stable learned parameters | next window |
|---|---:|---:|---|---|
| NaCl quotient | 64–512 | 3 | 8-atom motif; 5.64 A orthogonal translation Gram matrix | exact |
| ideal IQC section | 345–919 | 3 | unit phi; window 1.5; shell fractions 0.5 / 0.75 | exact |
| Fibonacci substitution | 216–1,728 | 3 | `A -> AB`, `B -> A`; same eight decorations | exact |
| twisted hBN atlas | 470–1,130 | 3 | one motif class, two poses, same translation Gram matrices | exact |

The test exposed a periodic overfit: the 512-atom NaCl window initially chose
a perfectly fitting 64-atom 2x supercell motif. The old tie-breaker favored
larger determinant. It now minimizes quotient description length after fit
quality and recovers the primitive 8-atom motif at all three sizes. Parameter
stability is therefore a separate gate from exact growth: a redundant
supercell can continue exactly while failing to learn the smallest recurring
cluster-of-clusters rule.

### End-to-end cost and count semantics

`scripts/materials_gcts_end_to_end_cost.py` times discovery, exact two-level
coordinate emission, fast million-scale representation counting, and an exact
count audit separately. The recorded Python run is a reproducible algorithmic
baseline, not a comparison with a production MD code.

| system | learn | exact two-level output | fast >=1m count | exact audit | flat / recursive actions |
|---|---:|---:|---:|---:|---:|
| NaCl, 216 atoms | 0.337 s | 13,824 in 0.051 s | 7,077,888 exact in 20 us | arithmetic exact | 176,942x |
| ideal IQC, 507 atoms | 1.756 s | 8,603 in 0.264 s | 2,788,759 estimate in 106 us | 2,791,097 in 2.489 s | 33,221x |
| Fibonacci QC, 729 atoms | 2.482 s | 13,824 in 0.031 s | 1,061,208 exact in 73 us | arithmetic exact | 53,024x |
| twisted hBN, 746 atoms | 3.371 s | 11,696 in 0.214 s | 1,048,576 exact in 11 us | arithmetic exact | 52,392x |

The finite graphs have exact incidence counts. The IQC has an exact compact
radius-plus-section representation, but exact finite-window cardinality is not
constant-time: it enumerates accepted rank-6 sites. Its fast count instead
uses the learned physical-ball volume times internal-window volume divided by
the inferred rank-6 covolume. At action 6 it differs from exact enumeration by
0.0838%. Explicit coordinate output is linear for every family. Therefore the
current exponential claim is strictly about sites represented per recursive
program action and program-description compression. It is not yet evidence
that GCTS beats million-atom MD in wall time or reproduces dynamics.

### Matched-quality tree-search marking ablation

`scripts/materials_gcts_matched_search_ablation.py` holds the target,
candidate frontier, accepted-move count, and immediate conflict check fixed.
Each incompatible proposal produces one failed branch/backtrack. For an
unmarked uniformly shuffled frontier, expected inspections to obtain `k` of
`K` valid actions among `N` proposals are the exact negative-hypergeometric
order statistic `ceil(k(N+1)/(K+1))`. The marked search uses the measured
filtered frontier. This avoids comparing a high-recall unmarked run with a
lower-recall marked run.

| system / marking | matched correct moves | unmarked expected checks | marked checks | unmarked / marked false backtracks |
|---|---:|---:|---:|---:|
| NaCl compiled colored quotient | 1 | 36,028,797,018,963,968 | 1 | 36,028,797,018,963,967 / 0 |
| ideal IQC compiled internal section | 8,603 | 6,170,727 | 8,603 | 6,162,124 / 0 |
| Fibonacci compiled ordered substitution | 6 | 337 | 6 | 331 / 0 |
| frozen learned IQC local halo, unseen level | 252 | 526 | 392 | 274 / 140 |

The first three rows test the marking embedded in the learned recursive
production at full recall: proposal reductions are 3.60e16x, 717x, and 56.2x.
They prove that the sections are causal, but those sections are also part of
the compact generator. The fourth row is the stricter GCTS-learning result:
the local section is trained only on the 507 -> 1,969 transition and frozen on
1,969 -> 8,603. At the same 252 correct accepted moves it reduces proposal
checks by 1.34x and failed branches by 1.96x. It is useful but not yet a
dramatic universal tree-search win; increasing held-out recall without losing
this precision is the next marking objective.

| system | observed input | learned supports | recursive factor | million-site gate | strongest certificate |
| --- | ---: | --- | ---: | ---: | --- |
| NaCl crystal | 216 atoms | 7 -> 27 -> 164 | exactly 8x/action | action 5: 7,077,888 | exact position/species quotient |
| ideal icosahedral model set | 507 atoms | 14 -> 49 -> 270 | about 4.2x/action; frozen marked subset 2.757x | action 6: 2,791,097 | two explicit inflations, independent 6D acceptance test, and cross-level frozen marking |
| Fibonacci-product quasicrystal | 729 atoms | 4 -> 17 -> 81 | about 4.2x/action | action 5: 1,061,208 | recovered substitution grammar |
| experimental Sc-Zn IQC | 37,531 sites / 173 centres | 13 -> 38 -> 98 | learned phi proposal | not claimed | generic grouped fit: 75.47% precision / 55.05% recall; precision-first: 84.09% |
| amorphous control | 507 atoms | none beyond local | none | rejected | no deterministic macro rule |

The first three rows set the exponential-style action benchmark.  The
experimental row must match their multi-step certificate before its learned
phi action is allowed to project a million-site count.

## Geometry-bearing cluster-of-clusters gate

`scripts/materials_gcts_cover_grammar.py` closes one earlier accounting
loophole. A higher-level cluster no longer records only child counts and turns
the remainder into anonymous species counts. Each production now carries
rigid child poses, the parent-local atom identities shared by overlapping
children, coordinate-bearing gap terminals, and a full prototype replay. The
recursive executor expands lower-level productions and merges same-species
overlaps geometrically.

| finite training cloud | stored productions | exact recursive prototype replays | overlapping productions | minimum modal reuse |
| --- | ---: | ---: | ---: | ---: |
| NaCl, 216 atoms | 68 | 68 | 52 | 33.3% |
| ideal IQC, 507 atoms | 48 | 48 | 36 | 30.0% |
| hard-core amorphous null, 507 atoms | 0 | 0 | 0 | rejected |

This gate is intentionally **red**. Exact replay proves that the learned cover
is executable and that gaps retain geometry; it does not prove continuation.
One modal right-hand side does not yet explain 90% of occurrences. The next
step is to retain context-marked production alternatives, freeze them on an
inner window, and measure exact replay on unseen outer occurrences. Until that
passes, the million-site rows above remain certificates of the specialized
quotient/substitution/section/address backends—not of this generic grammar.

### Frozen alternative-selection gate

`scripts/materials_gcts_contextual_alternatives.py` now retains a finite set of
right-hand-side alternatives instead of silently discarding every non-modal
cover. It uses a deterministic two-training/one-held-out occurrence split and
freezes the rule table before scoring held-out occurrences.

| finite cloud | train / held-out occurrences | RHS alternatives | held-out RHS seen in train | parent-only modal | bounded halo / port mark |
| --- | ---: | ---: | ---: | ---: | ---: |
| NaCl | 438 / 210 | 70 | 100% | 90.0% | 90.0% |
| ideal IQC | 1,014 / 504 | 59 | 99.60% | 88.49% | 88.49% |

This is another intentional red gate. The finite vocabulary is adequate, but
the current halo is constant within each coarse parent type and the first
bounded child-port multiset adds no discriminating information. A GCTS marking
must use already-placed incoming connection/overlap ports—not atoms that the
candidate would create—and must beat both the parent-only modal rule and a
shuffled-port control. Because overlapping occurrences share atoms, this split
is diagnostic only; the acceptance benchmark will train inside one window and
test outside a guard band in larger NaCl and IQC windows.

`scripts/materials_gcts_guarded_spatial_split.py` establishes that stronger
test geometry on 13,824-site NaCl and 8,603-site IQC clouds. A fixed plane with
normal `(1,2,3)/sqrt(14)` separates training and held-out centres. At each
level the unused band is the sum of every lower-level body radius plus marking
width, and the outer boundary is eroded by the same amount. NaCl retains
785 / 785 level-three centres. IQC retains 532 / 532 level-two centres but no
level-three centres in the present 8,603-site patch. Thus three NaCl and two
IQC levels have disjoint raw-atom dependency domains; IQC level 3 remains an
explicit red gate requiring a larger patch. This fixture blocks random
overlapping-occurrence splits from becoming the acceptance result.

`scripts/materials_gcts_frozen_hierarchy.py` supplies the first train-only
encoder/transform split. A spatial index replaces the quadratic full distance
table for the 13,824/8,603-site clouds. The training half alone fixes nearest-
neighbor scale, species colors, rotation-invariant signature maps, the
promoted-color maps, and an unknown sentinel. Transforming the disjoint half
finds 100% of both NaCl and IQC signatures in the frozen dictionary at every
certified level, without regrouping or type renumbering.

That success exposed an arbitrary top-four promotion bottleneck: it retained
98.41%, 74.57%, and 24.48% of held-out NaCl centres, but only 17.94%, 15.39%,
and 33.95% of IQC centres. The encoder now selects the shortest frequency-
ordered vocabulary covering 95% of training centres, capped at 64 types. It
learns 4/6/16 promoted colors for NaCl and 51/30 for IQC. Without seeing the
held-out side, these cover 98.41%/96.81%/95.29% and 95.59%/95.68%,
respectively. The certified hierarchy-state transfer gate now
passes. Frozen production selection, incoming-port marking causality, and
actual continuation remain separate requirements.

### Causal inward-halo search ablation

`scripts/materials_gcts_incoming_port_ablation.py` prevents another possible
leak: the marking may see only the inward half of the bounded halo, standing
for atoms already grown toward the observation center. Held-out parent atoms
choose the correct answer for scoring, but never enter the ranking features.
At the deepest certified hierarchy levels (NaCl level 3, IQC level 2), the
train-selected vocabularies have one right-hand side per parent: 16/16 for
NaCl and 30/30 for IQC. Parent type therefore forces every move, and both modal
baselines have zero decomposition backtracks. Neither is a task on which a
marking can demonstrate causal value.

This negative gate is informative: when the stored parent geometry already
determines its cover decomposition, GCTS has nothing useful to choose. The
next matched-quality experiment must rank *neighboring macro placements at a
live frontier*, where several transformed clusters can genuinely compete and
incoming overlap/connection ports can exclude future conflicts.

That experiment now passes. `scripts/materials_gcts_frontier_search_ablation.py`
reuses the actual recursive IQC frontier rather than a hypothetical candidate
population. The marker is fit on the 507 -> 1,969 transition and frozen on
1,969 -> 8,603. Every arm receives the same 66,110 candidate points and stops
after finding the same 120 correct novel sites—the first pure maximum-score
macro of the existing regenerative search.

| ordering | proposal checks | immediate failed branches | precision at matched stop |
| --- | ---: | ---: | ---: |
| learned incoming GCTS marking | **120** | **0** | 100% |
| overlap-vote baseline | 232 | 112 | 51.72% |
| 30 equal-budget train-label-shuffled marker refits | median 4,608; best 404 | median 4,488 | 2.60% at median |

The learned marking cuts matched work by 1.93x versus overlap ordering and
38.40x versus the shuffle median, and beats every shuffled refit. Held-out
labels never enter fitting; shuffles preserve the proposal descriptors and
positive count while destroying their association. This is the first causal
GCTS result at the correct search interface. It does not make the exponential
gate pass: it certifies one 120-site forced macro, while sustained recursive
macro amplification and the third cumulatively guarded IQC hierarchy level
remain open.

### Order-independent spatial support hierarchy

The earlier `materials_gcts_spatial_macro_audit.py` records the colored 3D
coordinates of all 368 sites accepted exactly over 16 regenerative waves. Its
time-window analysis found 12 four-site candidates of one rigid type, but every
occurrence lay in one window. That candidate is still rejected: grouping
consecutive moves is not clusters-of-clusters evidence.

`materials_gcts_spatial_support_hierarchy.py` removes construction order from
the learner. Given only colored positions, disjoint domain labels, and bounded
radii, it makes an exact connected cover, then recursively covers the resulting
clusters with clusters. Its fast type key is the species-labelled pair-distance
multiset, so translation, rotation, reflection, point permutation, atom IDs,
lattice metadata, and phase labels do not enter. A production compiler must
still collision-resolve homometric keys by explicit congruence. Unpromoted
components remain explicit gap terminals, so each level still covers its entire
assigned domain.

`materials_gcts_spatial_sector_benchmark.py` applies this generic learner to
the accumulated exact IQC frontier. Eight octants are separated by a small
guard around their coordinate planes; 296 of 368 atoms remain. The result is:

| level | recurrent geometry types | recurrent occurrences | largest support | assigned-atom coverage |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 4 | 152 | 3 | 100% |
| 2 | 3 | 56 | 11 | 100% |
| 3 | 1 | 8 | 37 | 100% |

Support amplification is therefore `11/3 = 3.67x` and `37/11 = 3.36x`.
This passes the scoped three-level spatial hierarchy gate and gives a genuine
cluster-of-clusters certificate independent of move order. At the smaller
observed factor, nine additional symbolic promotions would exceed one million
represented sites. That is a projection, not yet a growth certificate:
unseen-level production replay, causal GCTS marking on the promoted ports, and
explicit output checks remain required.

The companion frozen test separates the eight domains by the sign of `x`.
`materials_gcts_frozen_spatial_grammar.py` fits its length unit, type
dictionaries, and production alternatives using only four negative-x domains
(148 atoms), then transforms the four positive-x domains (148 atoms) with those
objects frozen. The origin and guard width are predeclared from the known inner
configuration, rather than estimated from held-out frontier atoms.

The learned vocabularies contain `4 / 3 / 1` types and eight parent-to-child
productions. Held-out type occurrence coverage, atom coverage, and exact child
production agreement are all 100% at all three levels; there are no unseen
types or productions. This is dictionary and cover-grammar transfer across a
spatial half-space, not yet causal outward growth. Each parent has exactly one
RHS in this fixture, so a marking cannot improve decomposition; the separate
live-frontier ablation is where incoming GCTS marking has a causal choice.

### Large cumulative-guard color transfer

The prior 8,603-site IQC fixture has no level-three held-out center after the
correct cumulative dependency guard. `oracle_patch_fast` removes that sample
size bottleneck. It splits the six integer lift coordinates into two triples,
hashes one set in internal space, and joins only pairs that can enter the
bounded acceptance window. Tests require exact lift, position, and species-set
equality with the original `(2b+1)^6` enumerator. It produces a converged
155,097-site radius-61.69 fixture in about 2.5 seconds on the development host.

`materials_gcts_guarded_radial_hierarchy.py` fits only inside radius 35 and
uses cumulative dependency radii `2.054 / 5.855 / 12.885`. Held-out centers
start outside the training radius plus the corresponding dependency radius and
end inside the oracle boundary minus that radius. Therefore raw training and
held-out domains are disjoint by construction.

| level | training centers | held-out centers | exact-key coverage | bounded GCTS-color coverage |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 23,919 | 106,162 | 75.5% | 100% |
| 2 | 16,587 | 70,458 | 0% | 100% |
| 3 | 6,953 | 4,260 | 0% | 100% |

The bounded color is a coordination histogram plus an angular-incidence
histogram over a finite neighborhood. Nearest-color tolerances are derived
only from spacing among training colors: one training nearest-neighbor width
for levels 1–2 and two widths for level 3. No held-out label selects the
tolerance. A matched-density amorphous hard-core XYZ cloud is evaluated with
the same frozen encoder and reaches 42.6% / 97.2% / 24.1% coverage. The common
gate rejects it because both primitive and deepest hierarchical color transfer
must exceed 50%.

This is a positive finite-color transfer result with a meaningful negative
control. It is not yet a claim that the exact parent geometry or its outward
placement has transferred. Frozen production replay and causal frontier search
on the larger fixture remain red requirements before counting additional
symbolic promotions toward one million sites.

### Frozen exact-production recognition

`materials_gcts_guarded_production_atlas.py` retains every distinct sampled
species-labelled child-distance graph for each frozen parent color. The graph
has a distinguished center and all colored pair distances, so it tests full
relative geometry while remaining invariant to translation, rotation, and
atom ordering. No modal alternative is silently selected.

With 1,024 deterministic training and held-out parent samples per level:

| level | known held-out parent color | frozen RHS alternatives | maximum alternatives/color | exact held-out geometry |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 98.7% | 138 | 5 | 67.4% |
| 2 | 97.9% | 195 | 1 | 0% |
| 3 | 100% | 95 | 1 | 0% |

Thus bounded colors transfer but do not uniquely determine exact production
geometry. This is the expected place for GCTS marking to matter: the next rule
key must add a bounded graph of already-grown incoming ports and choose among
the compatible alternatives. Enlarging the color until it memorizes exact
held-out geometry would defeat the purpose. The execution gate also remains
red: recognizing a rigid distance graph is not equivalent to recovering a
proper SE(3) pose from frontier correspondences and emitting its children.

### Causal incoming-port ablation

The first marking test deliberately exposes only the already-grown side of a
spherical frontier. For a proposed center, its key is the bounded multiset of
species/type and quantized center distances for smaller-radius neighbors. The
outward child-distance graph is the label, never an input. Fitting uses only
the 28,211-atom inner configuration; held-out geometry is scoring-only.

At level 1, 285 of 2,048 deterministic held-out parents have a recurring frozen
incoming context. On this identical matched subset, the parent-color modal
baseline selects 31 exact outward productions, the learned marking selects
104, and 30 within-parent label-shuffled refits range from 26 to 44 (median
35.5). The learned marking therefore beats every equal-capacity shuffle in
this ablation. However, coverage is only 13.9%, and levels 2 and 3 have no
exactly recurring incoming contexts. The overall gate stays red until a
symmetry-quotiented port representation transfers at every recursive level and
drives proper-pose execution at matched output quality.

The recursive centre-connection benchmark previously received the ideal
inflation factor as an argument. It now infers that factor from the 507-atom
seed alone. Candidate ratios come from recurrent peaks in the pair-distance
spectrum plus generic positive roots of low-coefficient quadratic polynomials.
They are ranked by weighted spectral closure at both `s` and `s²`; requiring
two levels rejects a tempting one-level ratio near 1.902. The selected value is
`1.618033988749895`, with 51.24% and 55.85% closure. This inferred value—not a
hidden φ constant—now trains and applies the frozen recursive connection
marking. Target windows remain scoring-only.

That correction exposed a second leakage distinction. The older connection
table learned action labels from the complete 507 → 1,969 transition. The new
`materials_gcts_sealed_connection_benchmark.py` fits labels only for 93 inner
parents whose inferred-scale images remain inside the 507-atom seed. The
1,969-site state and 8,603-site target never enter fitting. On the outward
evaluation frontier the table proposes 3,404 distinct novel sites; 500 are
true, or 14.69% precision and 7.54% recall. Raising overlap-vote thresholds
does not produce a high-precision/high-recall operating point. Comparing a
candidate's partial radial coordination to complete training neighborhoods is
also anti-informative, confirming that the useful GCTS section is a graph of
incoming overlap ports, not a potential-like coordination score. This sealed
result is now the causal generic connection baseline and is intentionally red.

`materials_gcts_metric_port_atlas.py` makes the first useful generic
connection correction. The coarse 0.5-wide separation bin is replaced by the
motif-centre connection length itself. At application, the length is divided
by the current recursively inferred scale before matching. Thus a port class
is `(parent motif type, source motif type, normalized metric length)` and is
invariant to translation, arbitrary rotation, atom ordering, and inflation
level. No proposed coordinate or target occupancy enters the key.

Proposals leaving the observed seed are censored rather than mislabeled
negative. Across all 507 parents, 73 of 544 observable metric port classes
pass the train-only rule. Frozen on the 1,969-site frontier, they collapse to
860 distinct novel sites. All 860 are in the held-out target: 100% precision
and 12.96% recall. The matched coarse-state
ablation proposes 3,404 sites with 500 true (14.69% precision), so metric ports
give a 6.81x precision gain. This gate is green for exact transferred port
execution, while recursive full-growth recall remains red.

The executor inserts the 860 predicted species labels, producing a 2,829-site
partial cloud with 100% correctness. No oracle species or positions are
inserted. Admitting every train-supported single port then adds 13,020 sites
and every one is false. The regenerative gate rejects this branch: metric
ports transfer once, but do not reconstruct the higher-order overlap state.

The accepted port-action incidence graph is now promoted explicitly. Two sites
are in the same supercluster when a chain of accepted overlaps shares parent
or source motif centres. The 860-site exact patch has two large connected
components of 500 and 240 sites plus 32 smaller components, all available as
nonconflicting macros.
Their coordinate fingerprints are different isometry classes, and direct
inflation of either component produces no valid next sites. Accordingly this
is a real clusters-of-clusters representation and parallel-action compression,
but it is not mislabeled as recursive exponential growth.

### Regenerative port-pair section

The next GCTS section is learned one order higher: for every observed endpoint
inside the seed, it records unordered pairs of metric ports whose actions
co-support that endpoint. There are 271 train-supported port-pair classes.
Its 6.155 Å frontier width is derived from the longest train-supported port
after recursive normalization, rather than tuned on held-out performance.
Frozen on the unseen frontier, the pair section executes three nonempty waves:

| wave | sites inserted | correct | precision |
| ---: | ---: | ---: | ---: |
| 1 | 260 | 260 | 100% |
| 2 | 192 | 192 | 100% |
| 3 | 60 | 60 | 100% |

It adds 512 exact species-labelled sites, growing 1,969 → 2,481 without target
positions or oracle colors entering fitting or insertion, then stalls on wave
4. This is the first regenerative result from the generic cluster/port engine:
newly placed clusters create valid incoming contexts for later moves. It does
not pass the exponential gate because the sequence does not amplify. The next
promotion target is therefore a recurrent port-incidence component whose
support factor stays above one across unseen levels.

### Amplifying higher-order batch

A separate scale benchmark asks whether the higher-order action itself grows
with recursive level. The least-supported pair-section endpoint in the seed
has 11 underlying metric-port actions. Without inspecting held-out labels, the
frozen rule uses `ceil(11 / scale^level)` as its consensus threshold. This is
seven votes at the first unseen inflation and five at the second.

| unseen scale | state → target | pair-supported | accepted / true | precision | novel recall |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1,969 → 8,603 | 260 | 80 / 80 | 100% | 1.21% |
| 2 | 8,603 → 37,073 | 1,620 | 480 / 480 | 100% | 1.69% |

The exact accepted batch therefore amplifies by 6x across two unseen scales.
This is the first exponential-style clusters-of-clusters certificate for the
generic port grammar: the marking, scale, port vocabulary, pair vocabulary,
frontier width, and thresholds all come from the 507-atom seed. It does not
claim complete reconstruction or a generic million-site rollout; coverage is
still sparse, and those remain red gates.

The second reference window is generated by the exact meet-in-the-middle
oracle. Its 37,073-site count is unchanged for coefficient bounds 10 through
14; the smaller bound-8 crop (29,309 sites) is rejected as truncated.

### Cross-family transfer audit

The same experiment on the non-icosahedral 3-D Fibonacci-product control
identifies a different useful finite section: similarity about a recurrent
fixed anchor. Learned from the 729-site seed, it emits 2,090 / 2,090 and then
7,222 / 7,222 exact novel sites on the 3,375 → 13,824 and 13,824 → 59,319
transitions. This is substantially denser than the IQC pair batch.

The anchor section fails on the IQC, while the spherical port-pair section
fails on the Fibonacci product, so the grammar exposes both as finite marking
hypotheses. A shared seed-only selector chooses the anchor hypothesis only when
at least 25% of observed sites have an exact similarity image. IQC has 61/507
anchor support and selects port pairs; Fibonacci has 216/729 and selects the
anchor. The threshold, hypotheses, and tie-break are frozen before held-out
scoring, and no phase label enters selection. Both selected markings pass two
unseen scales, turning this cross-family selection gate green.

The competition also includes the translation-quotient hypothesis. On the
216-site NaCl cloud it is selected from colored point geometry and emits the
exact 1,728- and 13,824-site continuations. Crystal, icosahedral, and
substitution-quasiperiodic systems therefore share one hypothesis-selection
interface and all pass two unseen levels. The following geometry VM removes
the family dispatch from their coordinate/species execution.

### Generic colored-point geometry VM

The three selected hypotheses now compile to one declarative execution
contract. A `translation_cover`, `anchor_similarity`, or `overlap_section`
instruction consumes a colored point cloud and emits a set of new
species-labelled Cartesian sites. State merging, deduplication, and scoring no
longer dispatch on a material family.

| selected instruction | unseen level 1 | unseen level 2 | position/species precision |
| --- | ---: | ---: | ---: |
| NaCl translation cover | 1,512 | 12,096 | 100% / 100% |
| IQC overlap section | 80 | 1,254 | 100% / 100% |
| Fibonacci anchor similarity | 2,090 | 7,222 | 100% / 100% |

This audit exposed and fixed an important hidden failure. The earlier IQC
coordinate benchmark reused the majority species attached to a seed port; it
correctly colored only 60/80 first-scale sites and 0/480 second-scale sites.
The VM instead evaluates the learned bounded internal color section at every
accepted endpoint. No oracle species enters execution, and all 1,334 accepted
IQC sites are now chemically correct. A rigid-motion regression also verifies
that a compiled instruction moves with its cloud within the declared 1e-4
congruence tolerance.

The VM is a shared interpreter, but its three compiler adapters remain distinct
geometric hypothesis learners. The next full-genericity gate is to express
their payloads as one recursively nestable port/cover graph rather than three
opcodes.

That normalization is now implemented by `materials_gcts_port_cover_graph.py`.
Every node has exactly the same schema:

1. a finite binding domain and arity;
2. an affine output map over the bound cluster centres;
3. grouping by coincident output (the covering overlap);
4. a bounded connection/consensus section;
5. a color section; and
6. child-node references for recursive promotion.

The three controls compile to one self-recursive node each. Translation cover
uses integer-cell bindings and an always section; anchor similarity uses typed
unary bindings and its admitted-type section; IQC uses binary metric-port
bindings and its learned port-pair section. The evaluator itself has no opcode
or phase-family dispatch. Re-running the coordinate/species benchmark through
this graph produces the identical six exact outputs above. This closes the
common-interpreter gate; learning multi-node graph topology and dense generic
IQC coverage remain open.

### Self-fed multiscale graph continuation

The complete-heldout-state audit is not causal growth: missing target atoms can
provide ports even if they are never directly scored as predictions. A new
gate therefore starts from the 1,969-site state and inserts only the graph's
own species-labelled emissions before retyping and executing again.

| recursive level | successive self-fed waves | exact sites added |
| ---: | --- | ---: |
| 1 | 260 → 192 → 120 → 80 | 652 |
| 2 | 792 → 204 | 996 |
| 3 | 360 → 240 → 120 | 720 |

All nine nonempty waves are 100% correct in position and species. The graph
adds 2,368 sites and grows the partial cloud from 1,969 to 4,337 atoms. The
155,097-site converged radius-`9 phi^4` oracle is used only for scoring; no
held-out position or color enters insertion. The extra vote cutoff from the
sparse amplifying-batch audit is omitted because membership in a learned port
pair is already the finite higher-order GCTS marking.

This passes a genuine self-fed, three-scale regeneration gate. It is still not
exponential: exact sites per recursive level are `652 → 996 → 720`, so support
does not grow monotonically. Dense growth will require learning another parent
frontier state or a complementary gap-production node rather than lowering the
precision gate.

### Section-assisted gap production

Pair consensus is precise but leaves holes that eventually remove its own
frontier support. The complementary graph node binds one learned metric port,
uses its affine endpoint as a gap proposal, then evaluates the learned bounded
section as an actual connection/failure predicate. Only an accepted endpoint
is colored and inserted. This operationalizes the accept/reject surface
requested for the visual pipeline. However, this section is evaluated in the
learned global IQC superspace; it is not yet a fixed-radius local halo around a
cluster.

| recursive level | exact self-fed sites | nonempty waves |
| ---: | ---: | ---: |
| 1 | 3,304 | 8 |
| 2 | 1,332 | 4 |
| 3 | 300 | 2 |
| 4 | 2,520 | 3 |
| 5 | 780 | 2 |
| 6 | 120 | 1 |

The section rejects 420 invalid candidate endpoints. All 8,356 accepted sites
are independently certified against the hidden six-dimensional model in both
position and species, while the hidden model contributes nothing to fitting or
state. The cloud grows from 1,969 to 10,325 atoms over 20 nonempty self-fed
waves. A coordinate-magnitude-derived lift bound replaces the old fixed bound
16; without that numerical correction, valid large-level sites were
misclassified by the scorer and marking.

This greatly improves generic coverage but still fails the exponential gate:
per-level support oscillates and ends `2,520 → 780 → 120`. A successful next
production must promote the recurrent level-4 frontier state while replacing
the global internal section with a finite, bounded local cluster marking.

### Carried local section marking

`scripts/materials_gcts_propagated_marking.py` makes that replacement at
inference time. The fitted 507-atom seed gives every seed cluster a
three-component mark. A two-cluster port transports those incoming marks to a
candidate with one learned affine rule; the transported mark alone decides
connection/failure and species. The growth loop never lifts a candidate's
global coordinate and never queries the global section. A regression replaces
the lift function with an exception during inference to enforce this boundary.

| recursive level | self-fed waves | exact colored sites |
| ---: | --- | ---: |
| 1 | `582, 60` | 642 |
| 2 | `360, 180` | 540 |
| 3–6 | none | 0 |

Thus 507 atoms become 1,689 using 1,182 / 1,182 exact locally marked additions.
This is the first operational bounded connection marking rather than a global
candidate lookup. It also exposes the next obstruction cleanly: the available
port grammar exhausts after two levels, so the exponential gate remains red.
The next production therefore promotes the 1,689-site recurrent cover and
learns ports between larger-support objects.

A categorical-distillation control explains why the carried state matters. A
whitelist of the seed's ten exact port-multiset contexts has perfect acceptance
precision on only 540 of 8,356 section-accepted sites (6.46% recall) in the
six-level ceiling trace. Coarser port-pair membership reaches 13.16% recall at
97.35% precision. Moreover, one transferred context changes chemical color.
Local incident categories alone therefore do not contain the phase information
needed by the IQC; it must be carried and updated by the marking.

### Self-fed clusters-of-clusters promotion

`scripts/materials_gcts_cluster_promotion_benchmark.py` performs that loop
without introducing a held-out target. It enlarges each cluster's observation
radius by the learned recursive scale, recomputes isometry-invariant colored
support types on the 1,689 sites generated above, and fits their ports against
that generated cover only. The number of recurrent types stays finite at 30,
while average support rises from 29.70 atoms to 98.57 atoms (3.32×) and the
largest promoted cluster covers 225 atoms. This is a cluster of clusters in
the operational sense: the symbol count remains fixed while each symbol's
covered child support grows.

The promoted grammar contains 789 ports and 13,111 compatible port pairs. It is
then frozen and self-fed at three increasing port scales. Exact colored
additions are `3,234 → 8,924 → 17,674`, successive factors 2.76× and 1.98×
(geometric mean 2.34×). The cloud reaches 31,521 atoms from the 507-atom seed.
Every one of the 29,832 promoted additions is independently certified against
the hidden model, which is a post-hoc scorer only. Candidate acceptance and
chemistry use the carried three-component marks.

This clears a finite three-level exponential-style promotion gate. It is not
yet a million-atom or cross-family result: vocabulary size (789 ports) is high
enough that description length must be compared with a flat generator, and
the same promotion code must transfer to the crystal and second-quasicrystal
controls before it can satisfy the stricter single-production benchmark.

The seed compiler no longer receives the IQC's physical unit or hand-written
radial cutoffs. It discovers the inflation rule, clusters the observed
nearest-neighbor distances, selects the smallest shell with at least 5% seed
support, expresses four descriptor radii in that learned unit, and treats the
outer observation boundary as censored. This family-blind route recovers the
same compact 73-port seed atlas and 271 port-pair section.

### Executed cross-family program gate

`scripts/materials_gcts_executable_program.py` now exposes one discovery call
and one explicit-action call. The selector receives only positions and species;
it chooses a translation quotient, carried-port promotion, or substitution
production from seed evidence. `scripts/materials_gcts_common_executed_benchmark.py`
then executes and scores three materialized actions rather than accepting a
symbolic atom count:

| seed | learned production | explicitly scored atom counts | per-action total growth |
|---|---|---|---|
| 216-atom NaCl | translation quotient | `216 → 1,728 → 13,824 → 110,592` | `8.00×, 8.00×, 8.00×` |
| 507-atom IQC | carried-port promotion | `507 → 4,923 → 13,847 → 31,521` | `9.71×, 2.81×, 2.28×` |
| 729-atom Fibonacci product | substitution product | `729 → 3,375 → 13,824 → 59,319` | `4.63×, 4.10×, 4.29×` |

All 252,953 materialized output sites are exact in position and species, all
states are self-fed, and neither family labels nor held-out atoms enter growth.
This makes the cross-family execution gate green. A stricter gate remains red:
three learned production kinds still sit behind the common API. The next
unification target is to express translation and substitution as the same
carried port/cover production used by the promoted IQC, rather than hiding
their distinct executors behind a dispatcher.

The frozen IQC production also executes a fourth promoted scale: it adds
35,414 / 35,414 exact colored sites and reaches 66,935 atoms. This is another
2.00× increase in novel sites, but it exposes a computational failure in the
radial-port implementation. A volume-style neighbor scan took 609.8 s for that
wave. An exact bounding-box spherical-shell index reduces it to 440.8 s
(27.7%) while returning the identical sites. The runtime is still far from a
credible million-atom engine. The implementation now uses the faster grid on
small clouds and shell pruning above 25,000 sites; the next kernel must index
exposed promoted ports rather than repeatedly joining atom pairs.

The bounded descriptor and port scans now use exact spatial hashes. Their
runtime depends on local density and learned port radius rather than scanning
all atom pairs; a brute-force regression certifies identical local colors.

`scripts/materials_gcts_regenerative_scaling_audit.py` turns the existing
regenerative trace into an explicit red scaling gate. Extending the frozen
policy to 16 waves gives
`12,104,12,4,36,24,24,12,8,24,24,24,24,12,12,12`, totaling 368/368 correct
sites. Frontier supply increases despite accepted candidates being removed,
and the largest forced macro contains 104 sites. Yet four-wave groupings shrink
`132 → 96 → 80 → 60`; geometric mean wave growth is 1.0 and the log-cumulative
fit has R² 0.605. Thus neither local waves nor naively grouped wave states
amplify. The next hierarchy must learn a different recurrent frontier state,
rather than treating these exact local macros as exponential by fiat.

`scripts/materials_gcts_frontier_state_grammar.py` now makes that next state
search structural rather than count-based. It builds an adaptive
nearest-neighbour graph on each target-free wave, enumerates connected colored
subgraphs through five sites, and canonicalizes them modulo translation,
positive uniform scale, and proper rotation. The 16-wave IQC trace produces
2,563 candidates and 119 normalized classes. Five classes recur across
independent waves: two two-site, two three-site, and one four-site type. A
deterministic non-overlapping cover selects 156 occurrences covering 336 / 368
exact emitted sites; 32 colored sites remain explicit residual terminals. All
92 admitted non-collinear occurrences replay through fitted proper-SE(3)
poses.

This improves representation without relaxing stationarity. One two-site class
repeats the golden-ratio scale over waves 7--9, but its unique support contracts
`24 -> 12 -> 8`; as a segment it also has a continuous rotational stabilizer
and is not a finite oriented port state. The proper three-site class seen on
waves 14--16 has constant 12-site support and scale ratios 1.2217 then 0.9654.
No class therefore has both repeated expanding scale and repeated expanding
support, and the strict witness count remains zero. A synthetic
`3 -> 6 -> 12` triangle control at scales `1 -> 2 -> 4` passes the same
compiler; colored mirror and amorphous controls remain red. The next generic
step is a certified transition grammar among frontier-state types.

That transition grammar is now implemented. It packs atom-disjoint finite
proper occurrences independently by state type, assigns each next-wave state
to its nearest compatible parent, and stores the entire child set in the
parent's normalized frame. The canonical key jointly quotients the parent
proper symmetry and each child symmetry while retaining relative scale,
rotation, translation, chemistry, and multiplicity. A stationary rule needs
the identical multi-child key on two consecutive transitions with at least two
independent parent occurrences on each.

The exact IQC trace contains three finite proper types, 30 packed occurrences,
and eight complete parent-production observations. They form five exact rules.
Four are heterogeneous multi-child rules, and the largest contains three
children of three distinct state types. This corrects an earlier compiler
artifact that split each child type into a separate unary rule. The scientific
gate stays red for the stronger reason: none of those mixed rules occurs on a
second transition and none has positive description saving. No stationary rule
reaches the target-free executor. A generic expanding control does pass: two
colored triangle parents learn the same two-child rule twice, the executor
reproduces the next two explicit waves, and 18 symbolic actions represent
1,572,864 sites. A separate heterogeneous two-type control also replays two
levels exactly, but is not fed to the scalar symbolic counter; a mixed-state
recurrence requires a learned vector substitution matrix. Thus execution is no
longer the missing API. The remaining scientific blocker is cross-transition
recurrence and compression of the real IQC frontier productions.

The transition learner now also enforces global child ownership: each
next-wave state is assigned once across all typed parents. This removes a
second optimistic failure mode in which the same child could appear in several
incompatible parent rules. A dedicated positions-and-species-only control then
learns the closed two-state system `A -> AB`, `B -> A` from three explicit
waves containing 12, 18, and 30 colored sites. The common proper-similarity
scale is learned as 2, the matrix `[[1,1],[1,0]]` has spectral growth
1.6180339887, and total description saving is 3 despite the necessary unary
second row. The target-free executor reproduces both observed explicit levels
and, without receiving it during fitting, exactly predicts the 48-site fourth
wave; the vector symbolic evaluator reaches 1,178,508 represented sites in 24
actions. Its program digest is invariant under atom permutation
and a generic proper rigid motion.

This closes an important API gap for quasicrystal-like grammars: expansion is
audited for a complete finite-state substitution matrix, rather than requiring
every individual rule to branch. It remains a generic algebra/control. The
actual 16-wave IQC trace produces no recurrent closed state set, so its
multi-state exponential gate remains red.

A fixed 24-wave extension rules out a simple observation-horizon explanation.
The first 16 waves are exact; wave 17 greedily selects 60 false sites, although
the rank-2 band is 48/48 exact and ranks 3--4 are also exact. All four bands are
hard-core valid, and the wrong band has substantial recurring-state cover, so
neither collision rejection nor internal compression is a causal selector.
The score gap between ranks 1 and 2 is 0.0001877. The candidate tree already
contains the correct branch; the next generic gate is beam lookahead and
rollback using boundary connection state only. Later waves are not admitted as
exact recurrence evidence until that branch choice is repaired.

The first beam implementation freezes ranks 1--2, expands both through the
same target-free connection grammar, and ranks the leaves by future boundary
consistency before using the immediate marking as a tie-break. The wrong branch
has future score 0.9997197; the exact sibling has 0.9997951, so one rollback
recovers all 48 sites. A cumulative sum would remain wrong. This separates the
roles cleanly: the marking proposes locally plausible actions, while search
value adjudicates delayed compatibility. Because the policy was diagnosed on
this same trace, the result is exploratory and the confirmatory flag remains
false.

The implementation now executes the policy beyond that single fork. Width two
fails immediately: waves 18--24 contain 40 correct and 72 false selected sites.
Increasing to width four reaches the exact rank-4 wave-18 band, but a pure leaf
score still yields only 36 correct versus 68 false sites on waves 19--24. The
first exact continuation at waves 18 and 19 is rank 4; the correct branch is
present, but scalar score is not a transferable branch value.

A second target-free objective ranks the same four immutable bands by the
number of compatible frozen frontier actions remaining after provisional
placement, using future marking score only as a tie-break. It selects exact
ranks 2 / 4 / 4 on exploratory waves 17--19. Frozen before wave 20, it selects
ranks 2 / 3 / 1 / 4 / 4 on waves 20--24 and adds 120 / 120 exact sites with
four rollbacks. The complete option-preserving trace is 572 / 572 exact and
frontier supply rises from 63,890 to 67,806. The temporal held-forward gate is
green. The run is not spatially independent, its 24 constant-size waves do not
form a stationary substitution, and the generic exponential IQC gate remains
red.

The spatial confirmation is deliberately fail-closed. The marking and
connection grammar are fit only on the 507- and 1,969-site concentric origin
windows. At a disjoint diagnostic centre `(30, 0, 0)`, width four misses even
though the first exact colored score band is rank five; that observation
freezes width five before a second centre is evaluated. The second centre
`(18, 25, 14)` is 33.838 from the origin and 31.064 from the first centre, so
its whole radius-14.562 scoring ball overlaps neither the training domain nor
the first scoring ball. The centre norms also differ, excluding any
origin-fixing proper rotation between the nuclei.

The second run freezes 5,616 bounded candidate sites and the width-five branch
decision before constructing the target. Posthoc scoring finds 431 correct
colored candidates in that frozen universe, but all five retained score bands
are false; the first band containing any correct colored site and the first
pure-correct band are both rank seven. Thus candidate generation transfers,
while the fixed breadth/value policy does not. The one-shot spatial gate is
red and is not a stationary or exponential certificate. The next admissible
improvement must choose breadth or branch value from training/frontier state,
then face a new spatial nucleus; this target cannot be reused for tuning.

A multi-configuration learner implements that feedback loop without adding a
material or origin label. It pools the same rigid-motion-invariant local
descriptor over three mutually disjoint nuclei—the origin and the two completed
diagnostics—giving 15,830 training candidates and 3,171 positives. The marker
and width-four option-supply search are then frozen before opening a fourth
radius-14.562 nucleus at `(-20, 20, 20)`, disjoint from all three training
balls. The exact 2-site action is now present at rank four inside the retained
beam, whereas the single-origin marking placed the correct basin below its
frozen breadth. This is a genuine proposal-ranking improvement.

The one-step branch value still selects rank two, emitting three false sites.
Accordingly the multi-nucleus spatial gate remains red. Its failure is more
specific: candidate geometry transfers and the learned marking retains the
right action, but the executor collapses the beam to one configuration after
only one lookahead. The next tree-search benchmark must keep complete
alternative configurations alive for multiple depths and count actual
rollback/backtrack work before committing; widening the same one-step rule is
already falsified.

The executor now implements that persistent state explicitly. Four complete
configuration states—atoms, colors, remaining frozen proposals, regenerated
ports, and collision state—are carried through three depths; 36 branches are
evaluated before the first move is committed. A robust local marking uses the
minimum score across three leave-one-nucleus-out models. On the fourth nucleus,
this combination selects path `4 / 3 / 3` and recovers an exact 3-site first
action. This is diagnostic because the fourth target was already opened by the
preceding test.

The policy is frozen without modification and tested once at a fifth centre
`(20, -25, 20)`. Its target-ball separation from every prior centre is at least
33.541, above the required 29.125. The exact 1-site action again appears inside
the four retained roots at rank four, but the three-depth frontier-cardinality
objective selects `2 / 3 / 2` and emits one false site. Target membership is
attached only after all 36 branch expansions and the choice are immutable.
The fifth-nucleus gate is therefore red. Two independent nuclei now show the
same causal boundary: multi-nucleus marking retains the correct geometry, while
frontier size—even after real multi-depth search—is not a transferable value
function. The next admissible change is a train-only learned value over branch
connection state, using this persistent beam unchanged.

The first such value model is deliberately finite and auditable. Across the
two completed diagnostic nuclei, exact-action counts for root ranks one through
four are `(0, 0, 1, 2)` out of two each. With a frozen Beta(1,1) prior, the
rank-value channel is `(0.25, 0.25, 0.50, 0.75)`. Rank is the ordering of the
already learned local marking, not an absolute coordinate or IQC label; future
frontier cardinality remains only a tie-break. The candidate set, robust
leave-one-nucleus-out marking, width four, branching four, and depth three are
otherwise unchanged.

This model is frozen before a sixth nucleus at `(-20, -20, -25)` is opened.
Its complete scoring ball is separated from every prior ball by at least
37.749, versus 29.125 required. The four candidate roots contain one exact
1-site action at rank four. After 36 target-free branch expansions, the value
selects path `4 / 2 / 2`; posthoc scoring confirms 1 / 1 correct colored site
and zero false sites. The one-action spatial branch-selection gate is green.
This is not yet a sustained-growth result: no second confirmed action,
stationary production, amplification factor, or exponential certificate is
inferred from it.

The same sixth nucleus is then reused only diagnostically for two self-fed
waves. The first action stays exact, while the second width-four choice is
false. Crucially, a frozen snapshot of twelve score bands (the extra bands are
inspected but not expanded) contains exact 1-site actions at ranks six and
twelve; ranks one through five are all false. Thus the second-wave failure is
not missing geometry and cannot be repaired by a different value over the same
four roots. It is a learned action-channel coverage failure. Active branching
width and diagnostic snapshot reach are now separate audit fields. Any move to
six or twelve active channels must be chosen using training-side pose/port
coverage and face a new nucleus; the opened sixth target is not a tuning gate.

The finite channel learner therefore retains every rank at which an exact
alternative occurred in the completed training observations. Those ranks are
`3, 4, 6, 7, 12`, fixing channel reach at 12. The rank-value posterior is
refit with heterogeneous support: ranks 1--4 have four observations, ranks
5--12 have two. Enumeration width becomes 12, while only four complete
configuration states survive each beam layer. This ties channel count to
observed connection/pose coverage rather than to a manually selected slider.

The predeclared seventh-nucleus invocation lost its result at the execution
transport boundary. Because it may have opened the target, it is recorded as
consumed/unknown and is never rerun. The unchanged artifact is tested at an
eighth centre `(-25, 20, -20)`, separated from every prior target centre by at
least 37.749. It evaluates 108 target-free branches over three depths, selects
path `4 / 12 / 11`, and emits 1 / 1 exact colored site. The one-action learned
channel/value gate is green on this fresh nucleus. Sustained self-fed growth,
stationarity, and exponential amplification remain separate red gates.

Two completed second-wave diagnostics then justify one bounded contextual
extension. In the initial state, exact rank four appears in all four available
frontiers, giving posterior value `5/6`. Conditional on the previous committed
root being rank four, both independent observations contain exact ranks six and
twelve, giving each `3/4`; all other ranks receive `1/4`. This is an order-one
carried connection mark. It contains only the previous finite channel ID and
the candidate channel rank, never a coordinate, target site, nucleus identity,
or material-family label.

The contextual artifact is frozen and executed for two waves at a ninth centre
`(-25, -20, 20)`, whose radius-14.562 target ball is disjoint from every prior
ball by at least 37.749. Twelve root channels are enumerated, four complete
states are retained, and 108 real branches are expanded per wave. The selected
paths are `4 / 12 / 11` and, after carrying context four, `12 / 9 / 10`.
Posthoc scoring gives wave truth `(1, 1)`, falsehood `(0, 0)`: two exact
self-fed colored sites. The two-wave spatial tree-search gate is green. Its
unit wave sizes show no amplification, and no repeating production or scale is
inferred; stationary and exponential IQC gates remain red.

A third ordinal context is then trained without ambiguity: after the confirmed
`4 / 12` prefix, the sixth, eighth, and ninth diagnostic nuclei all have an
exact rank-six action, yielding posterior `4/5`. The resulting states are
`0`, `4`, and `12`. On a tenth disjoint nucleus `(30, -25, -20)`, the model is
executed for three target-free waves. It fails immediately: the exact initial
action is rank eleven, while the table selects rank four. The later frozen
snapshots likewise contain exact geometry at different ranks, but the already
wrong state makes those paths unusable. All three emitted sites are false.

This is a constructive red result: finite channel reach 12 is adequate, but
ordinal score rank is not a transferable channel identity. Rank changes when
the local candidate population changes even if the underlying port relation is
the same. Subsequent GCTS values must be indexed by symmetry-quotiented
parent/source cluster identity and connection-port semantics; rank may only be
a deterministic executor ordering and cannot carry physical state.

Four ID-free categorical quotients are evaluated next on the same frozen
candidate geometry. Exact local evidence, full parent/source radial types,
and coarse colored port types each have zero held-out channel coverage on the
tenth nucleus. Removing geometry down to connection chemistry raises overall
candidate coverage to 25%, but the one exact held-out action is still not a
train-exact chemistry class. No key sees target membership before it freezes,
and none authorizes geometry; they only rank existing certified candidates.
This falsifies a finite lookup-table marking at the tested resolutions. The
next admissible representation is a continuous rigid-motion-invariant section
learned across multiple nuclei, backed by the unchanged exact port/collision
certificates.

The continuous replacement is now measured on a fresh eleventh nucleus. Nine
completed disjoint nuclei supply 49,716 candidate rows and 3,695 exact colored
positives. The label is species-aware: correct position with incorrect species
is negative. The descriptor remains a bounded radial/color/vote section and is
invariant under common proper-SE(3); exact ports and collision checks remain the
admission layer. Leave-one-nucleus-out fitting places an exact action within
the fixed twelve-band reach in 8 / 9 nuclei (first in 2 / 9), so the training
evidence is useful but not uniformly easy.

The full model digest is
`bb891f2c5055afe529c77c2834632c4df654bb2c9c944b1a4ae888535d980697`.
It is frozen before constructing the radius-14.562 target about
`(0, 0, -50)`. Minimum separation from every training centre is 37.749, above
the 29.125 disjoint-ball requirement. The target-free width-four,
twelve-channel, depth-three search selects path `1 / 5 / 12`; the first band
is the exact action and emits 4 / 4 correct colored sites with no false site.
This is a green one-action spatial confirmation for a continuous GCTS local
section. It does not certify a second self-fed wave, a promoted macro,
stationarity, amplification, or exponential IQC growth.

The identical model is next frozen for two waves at `(0, 50, 0)`, again outside
every prior target ball. Both decisions enumerate twelve candidate bands.
Wave one selects path `1 / 5 / 12` and emits 4 / 4 exact colored sites. On the
self-fed frontier, the exact action remains available at rank five, but the
section selects path `1 / 7 / 8` and emits 0 / 4 correct sites. Overall
precision is therefore 4 / 8 and the two-wave spatial gate is red. This rules
out missing geometry and insufficient channel reach as the immediate cause.
The continuous section was trained only on seed frontiers; the justified next
step is to include target-free post-commit states from the known training
nuclei, not to carry ordinal rank or tune against this failed target.

The follow-up performs exactly that intervention without using the failed
nucleus. Eight of nine training nuclei expose an exact teacher-forced first
band. Their post-commit states supply 44,439 candidates and 3,205 exact colored
positives; a separate continuous section is fitted and selected at every depth
after the first commit. At a new disjoint centre `(-50, 0, 0)`, wave one emits
4 / 4 exactly. Wave two retains an exact action at rank four, but selects rank
one and emits 0 / 4. The gate remains red. Therefore training-state exposure
is not the only problem: the existing continuous descriptor contains bounded
radial/color/vote statistics but not a continuous summary of the actual
parent/source port states. That symmetry-invariant connection distribution is
the next representation change to test.

That representation change succeeds. `port-state-v2` adds only continuous,
rigid-motion-invariant summaries of the already frozen connection evidence:
weighted separation-bin moments, parent/source neighborhood sizes,
same-color/same-shape fractions, state and parent diversity/purity, and source
and target color entropy. It contains no raw type identifier, Cartesian
position, global direction, nucleus ID, phase label, or heldout atom. Exact
proper-SE(3) ports, species votes, and collision checks remain unchanged.

All nine training nuclei now supply an exact teacher-forced first action. Their
post-commit corpus has 50,065 candidates and 3,677 exact colored positives.
The seed and self-fed model digests are respectively `d489513f...eecbb5` and
`0629b18e...dfe0b`. Both freeze before the outer target about `(0, -50, 0)` is
constructed. The unchanged twelve-band, width-four, depth-three executor ranks
the exact action first on both frontiers, selects `1 / 6 / 8` then `1 / 7 / 6`,
and emits 4 / 4 plus 4 / 4 exact colored sites. The two-wave spatial gate is
green with no ordinal carried state. This proves self-fed finite marking
transfer; four-site wave size, no promoted recurring rule, and no amplification
leave stationary and exponential IQC growth red.

### Whole-action antichain preflight

The next experiment does not reinterpret the successful `4 + 4` sites as
parallel growth. It asks the continuous section to admit several complete
score bands that are pairwise compatible with the seed and with one another.
Such a batch is an antichain: every band remains an ordinary tree-search
action, but the accepted bands can be committed in any permutation.

The first train-only calibration uses the raw port-state probabilities. A
zero-error cutoff selects 50 / 50 seed-state sites from 49,716 rows and 24 / 24
self-fed sites from 50,065 rows. Frozen on a new disjoint centre `(0, 0, 50)`,
neither cutoff admits a band, so execution stops before wave one. This is a
score-scale transfer failure, not a collision or target-leakage result.

The replacement acts on whole bands. Its 15 rigid-motion-invariant features
contain score margin/rank, band and frontier size, vote consensus, source and
target port-role purity, state entropy, and parent multiplicity. They contain
no candidate coordinate, raw type ID, nucleus ID, phase label, or heldout
atom. The first 24 bands in each of nine nuclei give 216 seed actions with 57
pure positives and 216 self-fed actions with 48 pure positives. Ridge strength
and threshold are selected by leaving out entire nuclei. No threshold reaches
the predeclared 95% action precision for either stage, so the benchmark fails
closed before constructing the reserved `(50, 50, 0)` seed or target.

This is a stronger and more useful red result than another hand-chosen score
cutoff. The continuous section transfers as a ranking for one action, but local
scores do not yet authorize a multi-action batch. The justified next search
state must carry unresolved outgoing port obligations through bounded
lookahead/backtracking; exact geometry, collision checks, and the final sealed
site/species score remain separate gates.

A first target-free lookahead implements that search-state change at aggregate
resolution. Every candidate band is applied to the exact training frontier;
the resulting frozen proposals supply connection consensus, recurrent-state
support/purity, parent multiplicity, and unresolved singleton load. Those 28
future/delta values augment the 15 local band values. They contain neither
coordinates nor raw IDs and are rigid-motion and insertion-order invariant.

The group-heldout models now find a zero-error operating point, but only by
retaining one seed action and one self-fed action out of 216 in each table.
That is insufficient for the stated parallel-growth task. Before any new
target is opened, the preflight requires 95% precision and at least 18 retained
actions per stage—two per training nucleus in aggregate. The measured `1 / 18`
and `1 / 18` coverage therefore keep the gate red. Aggregate successor
statistics improve purity but collapse action coverage; the next justified
representation carries the actual bounded incidence multiset of unresolved
ports through backtracking rather than compressing it to moments.

That explicit state is now implemented. A semantic role contains only the
parent and source cluster colors, their cumulative neighbor-count types, and a
normalized separation bin. Whole actions carry at most eight such roles;
action IDs remain exact search identities but never enter the state. A child
must consume at least one carried role, and a branch is rolled back when an
explicit obligation has no candidate continuation. Synthetic adversarial
tests reject a higher-scoring stranded root and a disconnected child.

The nine-nucleus train-only audit builds 504 exact actions with 23 pure
coordinate-and-species positives. Leaving out whole nuclei, 97.40% of role
mass is already present in the remaining training folds, so vocabulary
novelty is not the principal failure. The explicit search explores 306 actions,
backtracks 49, and finds two-action connected paths on eight of nine folds.
Posthoc, however, all 16 selected actions are false and emit 120 false sites.
No individual role or order-two same-site role pattern reaches transferable
90% purity: apparently pure patterns occur in only one nucleus. The reserved
confirmation centre is still unopened. This rules out both marginal port
admission and topological closure as sufficient GCTS markings; the next model
must retain joint incidence geometry while exact placement and collision
certificates remain unchanged.

The next preflight changes the action resolution rather than the target. Whole
equal-score bands are split into 44,602 collision-free candidate cluster
centres (3,689 exact colored positives). Each ID-free descriptor combines the
semantic port roles and order-two incidences with proposal-neighbour distances
and the colored metric graph of the nearest occupied neighbors. Pairwise
neighbor distances supply an invariant angular surrogate that radial shells
alone cannot encode. The descriptor is
invariant under atom permutation and common proper-SE(3) motion; absolute
coordinates, the nucleus centre, target atoms, and raw occurrence IDs are not
serialized. Nine leave-one-nucleus-out models see 99.49% of heldout tokens and
assign fitted weight to 98.89%. The complete calibrated score level admits
25 / 26 exact compatible candidates (96.15% precision), but they occur in only four of nine
nuclei. The unchanged gate requires at least 18 placements and coverage of all
nine, so the reserved confirmation remains sealed.

The interface geometry controls now have a direct backend audit. The bounded
hypothesis grid is exactly one/two/three-shell reach crossed with coarse/fine
distance quantization; all six arms see the same 44,602 exact candidate
placements. In every outer fold an inner leave-one-nucleus-out loop on the
other eight chooses the descriptor geometry and a complete-score threshold.
This fully nested selection exposes calibration shift rather than curing it:
the frozen outer models select 41 / 65 correct actions (63.08%) and only six
nuclei are error-free. A fixed top-two rank removes the score-scale failure
and gives two exact actions on each of eight generic nuclei, but both actions
at the unique symmetry-centred nucleus are false (16 / 18, 88.89%). Its first
exact action is rank 189 with eight neighbors and remains rank 121 after
expanding the section to 32 neighbors. The centred stratum is therefore an
explicit out-of-distribution red control; it is not dropped or used to justify
opening the reserved confirmation nucleus.

The next fixed experiment projects the same tokens into semantic channels: all
members of one token family contribute their average evidence, so orbit size
cannot multiply a family's vote. A target-free selector uses the larger exact
top-score equality orbit to choose detailed versus channel scoring, with ties
fixed to detailed. At reach three, distance width 0.25, eight neighbors, and a
two-action antichain, leave-one-nucleus-out development is 18 / 18 exact. The
rule is frozen in commit `644d69f`; a second preregistration commit fixes the
reserved target order and protocol digest before execution. The disjoint
confirmation at `(0, 0, -50)` is 0 / 2: the detailed and channel top bands have
sizes four and two, the rule chooses detailed, and both selected placements are
false. The target is opened once after the candidate, descriptor, model, and
selection hashes are immutable. This falsifies orbit-size selection rather
than the finite pose/port representation and supplies a concrete requirement
for a learned joint role-incidence geometry section.

Post-confirmation development keeps the next disjoint centre sealed. A
deterministic disagreement selector—channel scoring whenever detailed and
channel top-orbit cardinalities differ—recovers 18 / 20 group-heldout actions,
not the required 20 / 20. A second, fully nested candidate-level learner
cross-fits the base token marking inside every outer fold and fits a 15-feature
linear section over score, rank, orbit cardinality, token-family count, and
evidence coverage. Ridge values 0.1, 1, and 10 all select 0 / 20 exact actions.
The candidate graph digest is unchanged. These controls rule out scalar
mixtures of the two sections; transferable selection must preserve joint
port-incidence geometry rather than summarize it into scores.

The first graph-valued correction couples the primary symmetry-quotiented port
role directly to each occupied colored shell and occupied-neighbor metric edge.
It adds 6,140 role--shell and 19,837 role--edge types while preserving the exact
candidate digest. In ten outer held-out folds, 97.66% of descriptor tokens have
train-frozen weights, but the best two-action result is 15 / 20. Raising the
minimum support/group evidence from 4/2 to 16/3 or 32/3 yields 14 / 20; a 64/5
floor yields 8 / 20. This is not a vocabulary-coverage problem. A marginal sum
over relational edge tokens loses graph topology, so the next bounded marking
must canonicalize finite incidence subgraphs or perform finite message passing.

The bounded message-passing control initializes occupied nodes by species and
candidate-relative radial shell and performs one or two complete-graph message
rounds with quantized pair distance as the edge label. Every resulting node and
graph color is conditioned on the primary symmetry-quotiented port. Both depths
select 14 / 20 exact heldout actions. The exact hashes produce 80,323 node
colors after one round and 161,768 after two, revealing representation
fragmentation rather than missing candidate geometry. Because these colors are
ranking features only, collisions cannot authorize a placement. The next
bounded learner must fit a finite quotient of message colors on training folds
instead of retaining exact neighborhood hashes.

That finite-quotient gate has now been run. Exact one-round colors are
coarsened by train-development distance divisors two, four, and eight and by
symmetry-reduced parent/source role projections. The smallest exact arm has
12,954 node and 5,787 graph colors, but every exact-hash arm still selects
14 / 20 actions. An additive incidence quotient replaces whole-graph hashes
with bounded colored node and metric-edge multiplicity tokens; it compresses
to 457 node and 976 graph types and improves only to 15 / 20. A separate
positive codebook then admits a prototype only when its finite graph view
occurs in at least two or three independent train nuclei. The selected
three-nucleus codebook contains 356--358 prototypes across folds and selects
11 / 20. All arms rank the same exact candidate graph, and the declared next
centre `(0, 50, 0)` is not constructed. The result is therefore a clean red
gate: finite compression is real, but neither additive bags nor nearest
recurrent graph prototypes provide the missing branch value.

The development corpus was then expanded under a separate committed protocol.
Eight radius-14.562 centres were selected geometrically and committed in
`fc80434` before any of their atoms were materialized. Their minimum separation
from prior or reserved domains is 37.417, and their mutual minimum is 44.721,
both above the required 29.125. The common model-set crop is stable between
coefficient bounds 24 and 25, with 476--496 seed and 2,028--2,064 target atoms
per new nucleus. The frozen additive quotient selects 14 / 16 new actions and
30 / 36 over all eighteen leave-one-nucleus-out folds. Increasing recurrence
support/group floors gives 28, 24, or 27 / 36 rather than an improvement.

The next train-only model treats the bounded incidence configuration as a
conditional state. It learns full node/edge/graph purity, then backs off to
node/graph, graph/port, and coarse port/color/occupancy states when evidence is
insufficient. Its best fixed floor has 4,353--4,636 supported fine states per
fold but selects only 29 / 36 actions. This falsifies whole-state lookup as the
missing GCTS value. The exact candidate graph is unchanged, all expanded
targets are development data, and the reserved `(0, 50, 0)` confirmation has
not been constructed.

The next correction restores attachment orientation rather than treating the
separation bin as a complete pose. Candidate-to-parent axes are related to the
already occupied neighborhood through dot products and signed scalar triple
products. This is invariant under global proper SE(3), retains chirality, and
does not introduce a lattice axis. Angular widths 0.125, 0.25, and 0.5 produce
9,580, 6,501, and 4,414 finite orientation tokens. Fine channels score 28--29 /
36; the coarsest exactly ties the 30 / 36 unoriented baseline.

A nested order-independent control then replaces greedy placement by one tree
node containing an unordered compatible pair. Each outer fold fits its
individual shortlist on the other seventeen nuclei; every inner pair corpus is
formed with the inner nucleus excluded as well. All 120 compatible pairs from
the top sixteen actions are scored. Every nucleus contains an exact pair in
that frozen shortlist (6--120 exact pairs per nucleus), yet all bounded pair
grids again select 30 / 36. Therefore the current six failures cannot be
attributed to missing rotations, absence of correct candidate pairs, or action
permutation order. The exact candidate graph is unchanged and the reserved
confirmation remains unopened.

The first model to improve the expanded result values the state created by an
action. For every outer fold, the additive model supplies a top-16 shortlist.
Each shortlisted action is placed hypothetically; local cluster types and
connection proposals are recomputed, and a finite descriptor records only the
new outgoing frontier's size, vote and parent mass, chemistry, port roles,
order-two incidences, and normalized distances. The development target is used
only for fold labels, never to construct the successor. Across folds, 19--46
unique candidate successors are evaluated per nucleus. With support/group
floors 16/4 and unit mixing, the corrected causal-endpoint value selects
32 / 36 rather than 30 / 36. A bounded second step then
executes the four strongest target-free outgoing children of every root. It
evaluates 76--184 child branches per nucleus and increases supported rollout
tokens substantially and reaches 33 / 36 with 16 / 18 exact nuclei. Thus
another unordered frontier shell is not sufficient; the next representation
must retain which port obligation survives
along which root-to-child path. The reserved confirmation remains sealed.

Keeping the directed path instead of pooling it is materially better. A path
descriptor joins the root successor, the incoming child-port roles and
order-two patterns, and the child successor. All path geometry is serialized
before labels are read; a training path is positive only when both root and
child have the correct species-position. The root value is the maximum over
four train-supported child continuations. This reaches 33 / 36 actions. The
same audit widened from four to sixteen children, producing 176--256 paths per
heldout nucleus and at least two exact paths in every nucleus. Selection rises
to 34 / 36 with 16 / 18 exact nuclei. Candidate supply is therefore complete
at this bounded depth; the remaining two mistakes are score-transfer failures
among present alternatives. The reserved confirmation remains unopened.

A generic multi-configuration connection merger was then tested before any
further scoring change. It pools positive and negative state counts, target
chemistry, and the number of independent configurations with a correct
connection. Directly merging exact raw local types is strongly negative:
boundary-perturbed cluster-count identities fragment the state key. At the
loosest 2-support / 2-group / 0.5-purity gate, correct root candidates exist in
14 / 18 heldout nuclei and an exact root→child continuation in only 7 / 18;
stricter recurrence floors collapse supply further. The heldout target is used
only after candidate generation to score this ceiling. Multi-configuration
evidence therefore must be learned after a shared recurrent cluster quotient,
not by unioning raw connection markings.

The recurrent-first order was then tested directly. From ten training nuclei,
the generic learner retains 455 local pose classes occurring in at least two
independent configurations, maps each raw local type to that frozen quotient,
and only afterward pools connection evidence. All eight expanded validation
nuclei contain a correct first action and an exact root-to-child continuation.
The former 7 / 8 result was caused by a directed bookkeeping defect: a newly
placed cluster may be the source endpoint of an affine connection, yet the
successor search retained only geometric-parent indices. A separate causal
endpoint map now preserves both dependencies without changing the ordered
parent/source state used by the marking. This passes the 8 / 8 development
supply gate without relaxing support or purity; the reserved confirmation crop
remains unopened until the corrected rule is committed and preregistered.

The corrected rule was committed, then separately preregistered with source
hashes and a supply-only gate before the reserved centre `(0, 50, 0)` was
opened once. The frozen model contains 455 recurrent prototypes and 21,841
admitted states. Before target access it serializes 672 root candidates and
1,104 causal one-step successors. Posthoc scoring finds 38 exact colored roots
and four exact root-to-child paths; the first appears after scanning eight
correct roots. The nearest development centre is 33.838 units away, above the
29.125 disjoint-domain requirement. This is a positive transfer confirmation
for finite GCTS candidate supply. Because target labels identify which paths
are exact and no frozen value selects one, autonomous selection remains open;
stationary and exponential claims remain red.

The follow-on recurrent-path selector keeps that supply fixed and learns only
a bounded connection value section. Its descriptor contains the candidate
action incidence, the newly placed root's causal successor state, order-two
incoming port patterns, predicted colors, and a normalized root-to-child
distance; it contains no target coordinate. The prerequisite 256-root by
16-child tree contains exact paths in all eight development nuclei, with
posthoc counts `13 / 2 / 8 / 8 / 1 / 14 / 13 / 13`. Group-heldout marking
selects an exact path first in `7 / 8`; the remaining nucleus has one exact
path among 293 frozen alternatives. Candidate supply therefore passes, while
the autonomous selector gate remains red and no new sealed confirmation is
authorized.

The first explicit clusters-of-clusters path value adds a target-free
compatibility calculation rather than another token reweighting. For every
tentative root→child insertion it incrementally recomputes the nearest frozen
prototype residual of both new clusters and every affected existing cluster.
An exact parity test compares those increments to full reclustering, while
proper rigid motion and input permutation leave the result unchanged. The
bounded section also carries the connection direction relative to a frontier
normal estimated from the nearest eight occupied sites; no global origin or
target coordinate enters. With fixed eight-to-one hard-negative sampling and
ridge `0.1`, group-heldout selection remains `7 / 8`, but the lone exact path's
rank falls from 101 to 21 (`4.81×` less branch work before reaching it).
This is a measured clusters-of-clusters pruning gain, not a passed autonomous,
stationary, or exponential gate.

The follow-on audit corrects an overly restrictive execution assumption. The
directed-path diagnostic required every third action to descend from the last
inserted cluster, although the intended GCTS covering search may next use any
exposed frozen port in the current configuration. Ten training nuclei provide
20,716 candidate descriptors and 1,151 correct actions across three self-fed
stages. A stage-aware leave-one-nucleus-out grid selects a support-4,
two-independent-group, 0.5-shrinkage finite incidence marking without reading
heldout targets. Conditional on one known-exact two-action prefix per heldout
nucleus, the complete post-commit frontiers contain 57--75 exact actions. The
clusters-of-clusters compatibility baseline reaches the first exact action at
ranks `3 / 3 / 4 / 4 / 1 / 9 / 9 / 9`; the finite post-commit marking reaches
`3 / 4 / 3 / 3 / 1 / 1 / 1 / 1`. A width-four configuration beam therefore
has complete conditional supply, but top-one selection succeeds in only four
of eight. Because heldout truth constructs the exact prefix, this is explicitly
a conditional search audit, not autonomous continuation, stationarity, or an
exponential IQC certificate.

The corresponding orientation-capacity control holds every exact candidate
fixed and augments only its marking descriptor. Attachment axes are encoded by
dot products and signed triple products in the occupied local frame, quotienting
global proper rotation and translation while preserving chirality. A grouped
training comparison over angular widths 0.125 / 0.25 / 0.5 and additive versus
one-vote-per-channel scoring selects width 0.125 with channel normalization:
it ranks an exact action first in 23 of 28 eligible training stages and retains
28,558 weighted tokens. Heldout transfer is negative. The first-exact ranks are
`5 / 1 / 7 / 6 / 1 / 3 / 3 / 3`, only two of eight top-one choices are exact,
and the required conditional beam widens from four to seven. Hence observed
cluster rotations are an input to the marking representation, but raw rotation
cardinality is not the channel count. Capacity remains admissible only when a
finite recurrent pose × port quotient improves heldout evidence.

That quotient is now implemented with the stage ownership requested by the
interactive lab. The clustering audit freezes the 0.125-radian proper-pose
atlas upstream; the marking fit cannot silently change its angular resolution.
Five invariant evidence channels pool connection role, proposal multiplicity,
occupied shell, neighboring incidence, and pose/chirality token responses.
Grouped train-only selection chooses token support 4 across two independent
nuclei and state width 1.0, yielding 437 recurrent states. The exact candidate
set is unchanged. On the eight conditional post-commit frontiers the first
exact ranks become `1 / 1 / 1 / 1 / 1 / 1 / 1 / 1`, versus
`3 / 4 / 3 / 3 / 1 / 1 / 1 / 1` before the quotient. The conditional top-one
development gate is therefore green. Its model digest is
`9b83898155f5d729499c441bcbafa6491b553196fe87de756cb6281b8b856b13` and
its candidate/descriptor digest is
`a241b449374deadd73ff32fc48f45c87412e0fa8073c6fac35848e5bc5e785b4`.
This still uses truth to construct the known-exact two-action prefix; a new
sealed self-fed nucleus is required before calling the selection autonomous.

The sealed self-fed check has now been run and fails. The first preregistered
centre `(-70, -70, 30)` is recorded consumed/unknown after bound-24 and
bound-25 target crops disagreed; no score was computed and that nucleus is not
reused. A replacement at `(-50, 50, -10)` is 40.31 units from every prior
target centre and uses a bound-32 / bound-33 stable crop. The frozen 437-state
policy constructs a target-free width-four, reach-four, depth-three tree with
`4 / 16 / 16` candidate snapshots and four retained configurations per depth.
The chosen branch is genuinely self-fed but posthoc only one of its three
colored sites is exact. Candidate digest
`028acae9f4c2105f506b06de0e2c8d6aa238bd8d6e7fb3932c8d682af148529e`
and pre-target trace digest
`d2a0290f5bf819a7234803b71ac38fcb539e8ace4409b8156e2c73aeb6f6e49d`
freeze the failure. Conditional branch selection is green; autonomous top-one,
sustained, stationary, and exponential IQC growth remain red.
Post-confirmation replay on this now-consumed development nucleus separates
supply from value. The tree contains one exact path, whose within-parent ranks
are `1 / 4 / 4`; exact-candidate counts are `1 / 7 / 7`, and the exact prefix
survives every depth. Yet cumulative state probability ranks that path 10th of
10 terminal configurations, while the selected path has truth pattern
`exact / false / false`. Group-heldout capacity controls show that beam
4 / 8 / 16 at action reach four all retain exact paths in only 6 / 10 training
nuclei and select 4 / 10; reach eight plus beam sixteen reaches only 7 / 10
supply and still 4 / 10 selection. Individual correct-action ranks reach 17,
28, and 847. Hence neither raw width nor geometry is the accepted fix: the
next gate is a learned recurrent branch value with bounded search cost.

An individual two-step port graph then separates candidate supply from marking
failure. One canonical representative of each local descriptor class is
ranked by the frozen connection score, and the first 128 per nucleus are
expanded without a target. A child is admitted to the graph only when the
newly placed root is one of its witnessed parents and exact exclusion geometry
passes. All nine known nuclei contain exact root→child pairs; their counts are
`12 / 53 / 24 / 14 / 27 / 27 / 27 / 27 / 6`. The carried obligation is one
primary symmetry-quotiented port (vote multiplicity is evidence, not extra
cardinality), while the remaining roles stay as order-two marking patterns.
The first executor nevertheless selected zero of nine exact paths because it
added an unrelated raw child-vote score after evaluating the learned joint
root→child value. Removing that double count leaves the candidate graph fixed
and raises group-heldout selection to five of nine. This is a sharper red
result: the finite exact tree already contains the answer in every nucleus,
and correct score composition exposes useful marking transfer, while four
boundary environments still require a transferable path-value section.

A fixed third-frontier control asks whether that value is simply the size or
quality of the immediately available continuation. For each nucleus, the 512
highest raw-child-evidence paths are frozen without labels; exact alternatives
remain present in every shortlist (`12 / 22 / 15 / 10 / 13 / 13 / 13 / 13 /
2`). Each path is executed one additional step without committing it. The
bounded descriptor records the outgoing semantic roles, order-two incidence
patterns, vote and parent mass, predicted color set, and normalized radial
histogram—never a target coordinate or global origin. Group-heldout selection
is only four of nine, worse than the corrected two-step section's five of nine.
Immediate frontier supply is therefore another measured negative value
function, not justification to open the reserved nucleus.

## Generic intrinsic-2D atlas gate

`scripts/materials_gcts_2d_generic_atlas.py` removes the original moire
fixture's assumptions of exactly two binary XY sheets.  From positions and
species alone it learns connected affine components, rank-two colored
translations in arbitrary 3D orientation, the complete motif modulo the
translation torus, motif isometry classes, and one finite pose marking per
component.

| control | seed -> held-out | learned motif poses | atoms per pose action | position/species |
| --- | ---: | --- | ---: | ---: |
| globally rotated graphene-like monolayer | 373 -> 1,495 | 1 x C2 | 1,122 | 100% / 100% |
| globally rotated 30-degree hBN-like bilayer | 746 -> 2,990 | 2 x BN | 1,122 | 100% / 100% |
| globally rotated 13-degree Janus MoSSe-like bilayer | 878 -> 3,578 | 2 x MoSSe | 1,350 | 100% / 100% |
| globally rotated, anisotropically strained 17-degree hBN-like bilayer | 748 -> 2,990 | 2 x BN | 1,121 | 100% / 100% |

Keeping only one pose per motif-isometry class leaves both bilayers at exactly
50% recall; restoring the learned cluster-of-clusters pose marking restores
100%.  This is a causal marking ablation with the motif dictionary fixed.

### Cross-layer registry model selection

Compact whole-structure generation does not imply that exact local interlayer
registry has a finite vocabulary. `scripts/materials_gcts_2d_registry_selection.py`
learns rotation-invariant, species-resolved cross-layer sections at increasing
radii inside the same 932-atom seed, then chooses its marking representation
before opening a 2,384-atom held-out disk.

| bilayer | local states at 5 / 10 / 15 Å | seed-local coverage on held-out registry | selected marking |
|---|---:|---:|---|
| aligned | 2 / 2 / 2 | 100% | finite local registry + pose fallback |
| commensurate 21.7868° | 10 / 10 / 10 | 99.53% | finite local registry + pose fallback |
| 30° incommensurate | 10 / 33 / 71 | 30.22% | two-state cluster-of-clusters relative pose |

The 30° local vocabulary has empirical growth exponent 0.890 and reaches 223
states in the held-out window, so the learner rejects it as an unbounded exact
local marking rather than memorizing ever more environments. Its two learned
component poses still generate the held-out structure exactly. The choice uses
only vocabulary growth inside the seed; family labels and held-out atoms are
excluded.

`scripts/materials_gcts_2d_robustness.py` deletes 3.35% of a 746-atom hBN seed
and adds 0.006 Angstrom Gaussian coordinate noise.  The learner covers the
vacancy-isolated residual atoms, recovers both BN poses with minimum translation
support 0.878, and reconstructs the clean 2,990-atom scaffold at 100% registered
position/species precision and recall with 0.0031 Angstrom RMS error.  The pose
ablation remains at 50%.  This is scaffold recovery, not prediction of future
random defects or thermal displacements.

`scripts/materials_gcts_2d_recursive_macro.py` promotes the learned two
translation ports into a cluster-of-clusters address grammar.  Each level has
four transformed references to the preceding level and therefore represents
`4^l` motif occurrences without copying atoms.  Explicit level 6 exactly
expands to the independent 2,990-atom held-out disk.  Level 9 represents
1,048,576 atoms using ten node definitions.  Starting at the 746-atom
seed-equivalent level requires five hierarchy promotions, versus 499,627 flat
motif placements, a 99,925x symbolic action-count reduction.  Explicit output
remains linear and is reported separately.

## Molecular cover gate: ice Ih and ice Ic

`scripts/materials_gcts_ice_cover.py` tests a qualitatively different failure
mode. An ice configuration is not usefully connected by treating each atom as
the center of a fixed-radius cluster. The geometry-first learner instead finds
one H2O isometry class, overlapping water-dimer bridges, and six-water
oxygen-ring boundaries. The ring interiors contain no atoms, but their
boundaries are retained as gap/connection clusters.

| fixture | atoms / H2O | H2O classes | bridge occurrences / classes | ring gaps / classes | water-only recall | full cover search |
|---|---:|---:|---:|---:|---:|---:|
| proton-ordered ice Ih | 216 / 72 | 1 | 115 / 6 | 38 / 17 | 1.39% | 100%, 37 placements, 0 backtracks |
| proton-ordered ice Ic | 192 / 64 | 1 | 98 / 4 | 23 / 12 | 1.56% | 100%, 32 placements, 0 backtracks |

This is a causal cluster-representation result: the atom dictionary and target
are fixed, and only the overlapping connection/gap clusters are ablated. It
certifies reconstruction of each known periodic window, not yet blind
continuation into a larger ice crystal or prediction of proton disorder.

The live sample selector now exposes three complementary paths: saved curated
families (including ice and intrinsic-2D controls), composition-first random
search over NOMAD, and the existing advanced local import. Database search
does not assign a structural family before growth; curated labels are explicit
benchmark metadata and remain excluded from the learner.

## Published Cd5.7Yb nested-window transfer gate

`scripts/materials_gcts_cdyb_oracle.py` is an offline standard-library port of
the published Feuerbacher V1.5 generator. It preserves the six-dimensional
projections, V/B/E occupation domains, truncations, and physical-space shifts,
and independently matches the archived NumPy notebook at ten decimal places.
The archive DOI, CC-BY-4.0 license, MD5, and SHA-256 are pinned in the module.
Artificial `Zn` empty-centre markers are excluded from the physical Cd/Yb
configuration.

`scripts/materials_gcts_nested_transfer_benchmark.py` defines the reusable
sealed protocol. A fitter receives only an inner colored point cloud; the
frozen program and that same seed are the only inputs to marked and unmarked
growth. Two larger annuli remain scorer-only. The pass gate requires complete
seed coverage including residual/gap classes, at least 99% precision and 90%
recall on both unseen annuli, 99% species accuracy, three hierarchy levels,
and a 10x marking reduction in total and failed proposals at matched recall.
It also rejects program mutation, known-region contradictions, out-of-boundary
emissions, phase-label use, and physical-potential use.

The first real-model baseline uses converged 60 Angstrom oracle geometry and a
predeclared off-centre origin `(3.1, 5.7, 8.2) Angstrom`:

| radial window | physical Cd/Yb atoms | role |
|---:|---:|---|
| 14.0 Angstrom | 506 | learner input |
| 18.0 Angstrom | 1,056 | validation annulus |
| 21.0 Angstrom | 1,672 | test annulus |

The normalized outer fixture hash is
`166e3f4b7e1588766f8b732574675b4f4563fe13a34f5ec400cc0dfac22fe9d6`.
The offset is a methodological correction, not a favorable random choice. A
crop centred on the model's global icosahedral fixed point produced many
60-fold shell orbits but almost no transfer of their exact local vocabulary;
those are global rotations, not independent translated occurrences. The
off-centre split is now primary and the centred crop is an adversarial
symmetry-bias control.

The generic cell-free support learner now uses adaptive shells only as seeds,
merges touching seeds into irregular atom collections, distinguishes complete
colored metric graphs, and performs deterministic set cover with explicit gap
classes. On the off-centre Cd--Yb seed, repeated supports cover 99.407% of the
506 atoms and one residual class makes the cover exact. With all fitting frozen,
the same support vocabulary covers 77.091% of the 550 atoms in the first unseen
annulus (99.802% of the known inner core). This is materially stronger than the
old zero-transfer adapter, but it remains recognition rather than growth.

Each learned support is additionally fitted with a centroid-local proper
rotation. Witnessed overlaps are stored as finite, species-preserving relative
SE(3) poses, quotiented by the proper colored automorphism groups of both
supports. Improper reflections, unlike-species coincidences, and near
collisions are rejected. On a greedy frozen cover of the first unseen Cd--Yb
window, 245 of 683 held-out port classes and 31.235% of witnessed overlap
relations occur in the training atlas. Corresponding weighted relation recall
is 74.576% for NaCl and 35.294% for the ideal icosahedral model set. The target
never refits types, frames, or ports.

The first causal marking is deliberately bounded: `(middle support type,
incoming oriented port)` ranks the next outgoing port, using only a previously
placed connection. Marked and unmarked arms enumerate identical candidates;
twenty within-parent label shuffles preserve all output marginals. Proposal
check reductions are only 1.025x for NaCl, 1.012x for the ideal model set, and
1.005x for Cd--Yb. The marking beats every shuffle only for NaCl. Exact context
coverage is merely 7.62% and 5.51% on the two quasicrystal cases, so this gate
is red: the predeclared gate requires at least two systems to beat every
shuffle with at least a 2x failed-check reduction. It points to the next
generic task: learn a lower-cardinality bounded
section/backoff over oriented ports, then replay frozen productions at a live
frontier. The common recursive selector still emits zero held-out Cd--Yb sites;
no representation-transfer number here is reported as autonomous continuation.

### Target-blind frontier replay

`scripts/materials_gcts_frozen_frontier_replay.py` closes an important causal
gap between vocabulary transfer and growth. Fitting detaches only proper
cluster prototypes and train-admitted overlap ports. Replay receives that
artifact, already placed occurrences, explicit residual atoms, and an optional
public radial boundary. It cannot enumerate supports or fit poses against a
target. Candidate positions are obtained only by composing a frozen relative
SE(3) port with a placed pose; held-out atoms enter the separate scorer after
the run.

The cross-family one-step gate deliberately distinguishes three questions:

| system | frozen productions | sealed candidates | greedy novel / correct | best correct atoms among the same candidates | conclusion |
|---|---:|---:|---:|---:|---|
| NaCl, 216 -> symmetric 5,832-site scorer crop | 1,424 | 33 | 1 / 1 | 6 | grammar has an exterior action; policy is weak |
| ideal IQC, 507 -> 2,229 | 896 | 0 | 0 / 0 | 0 | missing exterior production |
| off-centre Cd--Yb, 506 -> 1,056 | 11,870 | 52 | 3 / 3 | 19 | grammar has useful actions; policy and recall are weak |

The oracle column is computed only after target-blind enumeration and never
selects the replayed action. It is a ceiling on what a marking could achieve
with the exact frozen action set. NaCl uses a symmetric explicit oracle crop;
the previous positive-octant replication incorrectly penalized a valid
outward move on the omitted side. One correct action is not a continuation
pass: Cd--Yb recall is only 0.545%, and the ideal IQC cannot move at all.

### Lower-cardinality bounded port marking

`scripts/materials_gcts_bounded_port_marking.py` removes proper-prototype IDs
from the marking state and action abstraction. Its bounded local tokens use
support size and species histogram, overlap composition/count, normalized
translation, proper-rotation angle, and the incoming-to-outgoing angle in the
shared cluster frame. Exact port IDs remain the candidate actions and stable
tie-breaks. Tables are capped at two incoming ports, 32 exact states, and 64
one-port backoff states, with minimum train support 32.

Scientific scoring uses larger frozen windows, not an interleaved occurrence
split. Target relations are admitted only when their canonical pose is already
one of the train-frozen port keys. Marked, unmarked, and shuffled-label arms
have identical candidate digests.

| system | raw ports -> abstract action states | target decisions | exact / backoff coverage | mean checks marked / unmarked / shuffle median | gain over unmarked |
|---|---:|---:|---:|---:|---:|
| NaCl | 1,424 -> 468 | 352 | 1.42% / 4.26% | 113.18 / 114.20 / 114.98 | 1.009x |
| ideal IQC | 896 -> 411 | 360 | 0% / 39.44% | 26.28 / 27.86 / 26.28 | 1.060x |
| Cd--Yb | 11,870 -> 4,183 | 258 | 0% / 0% | 132.44 / 132.44 / 132.44 | 1.000x |

The IQC improvement is exactly reproduced by shuffled labels, and Cd--Yb has
no transferred marking context. The causal gate therefore stays red. The next
generic implementation target is a sparse recurring port-graph grammar:
reduce the redundant overlapping occurrence graph, mine exact port-labelled
subgraphs with SE(3) cycle consistency, promote their boundary ports, and
admit a stationary recursive production only after the normalized rule is
observed at two adjacent learned scales. Frozen target enumeration remains
scoring-only throughout that promotion loop.

### Sparse recurring port-graph macros

`scripts/materials_gcts_sparse_occurrence_graph.py` reduces the raw overlap
hypergraph before any macro is mined. Its deterministic approximation first
chooses an overlapping cover, then adds minimum-new-node witnessed connector
paths, a maximum-overlap spanning forest, and one canonical representative of
each short cycle signature. It makes no global set-cover or Steiner optimality
claim.

| system | source occurrences / undirected edges | cover + connector occurrences | retained edges | node / edge reduction | retained components |
|---|---:|---:|---:|---:|---:|
| NaCl | 576 / 24,888 | 36 + 1 | 65 | 93.58% / 99.739% | 1 |
| ideal IQC | 780 / 26,880 | 52 + 0 | 87 | 93.33% / 99.676% | 1 |
| Cd--Yb | 623 / 39,072 | 55 + 2 | 85 | 90.85% / 99.782% | 11 |

Every repeated-support atom remains covered. The Cd--Yb source graph already
has 19 connected components, so the retained graph cannot become connected
without unsupported edges; eleven components remain.

`scripts/materials_gcts_port_graph_macros.py` mines rooted connected induced
subgraphs of this sparse graph. A cheap graph code is only a bucket: retained
classes must agree under exact directed port-labelled graph isomorphism and
under root-symmetry-canonical full colored SE(3) geometry. Observed poses also
close every internal edge composition. Evidence requires at least two macro
atom unions with at most 10% overlap and positive structural-token MDL saving.

| system | sparse directed edges | positive-MDL two-child macro types | largest atom union | largest MDL saving | maximum cycle residual |
|---|---:|---:|---:|---:|---:|
| NaCl | 130 | 3 | 18 | 2 tokens | 1.49e-15 |
| ideal IQC | 174 | 42 | 35 | 11 tokens | 4.47e-15 |
| Cd--Yb | 170 | 2 | 40 | 2 tokens | 2.28e-15 |

Each `MacroType` stores child placements, exact colored atom union, internal
ports, boundary slots with occurrence frequency, and independent occurrence
proofs. This is the first generic cluster-of-clusters representation in the
new pipeline. It is not yet recursion: macro types are not yet fed back as
nodes, structural tokens are not entropy-coded bits, and canonicalization is
currently bounded to five nodes.

### Stationary recursive-production contract

`scripts/materials_gcts_stationary_port_graph_contract.py` defines the sealed
gate for the next pass. Compilation sees only a finite colored Cartesian cloud;
execution sees only the frozen program and seed; two held-out point clouds enter
the scorer afterward. A pass requires exactly one production kind,
`recurring_port_graph_macro`, across crystal, ideal-IQC, and Cd--Yb roles, plus:

- the same normalized production and learned similarity at two adjacent
  observed promotion levels;
- complete training cover, at least 95% repeated coverage, finite oriented
  ports, carried causal marking, and self-fed execution;
- exact species/position output for the first two unseen levels and independent
  reconciliation of explicit and symbolic unique-site counts;
- strictly greater than 3x represented-site growth for three consecutive
  actions and at least one million represented sites by action seven;
- permutation/proper-SE(3) invariant program signature, equivariant output,
  clean leakage audit, and deterministic rejection of an amorphous control.

The callback-based contract has passing and deliberately failing harness tests,
but the current macro miner does not yet implement those callbacks. Therefore
the stationary/exponential gate remains explicitly red.

### Recursive macro-as-node promotion with exact support quotient

After the unchanged positive-MDL admission gate,
`scripts/materials_gcts_promoted_type_quotient.py` groups only colored atomic
supports that are exactly congruent by a proper rigid motion. It selects a
deterministic minimum-dictionary representative and retains every unique exact
training support for promotion. It does not pool duplicate derivations into
extra MDL evidence. Improper mirrors, changed chemistry, and uniform-scale-only
similarity remain distinct; the latter cannot be merged while occurrences
carry SE(3) poses without an explicit scale.

The callback order is explicitly sparse/disjoint admission, optional dense
exact matching over the frozen training graph, exact-support quotient, then
promotion. Dense deployment is disabled in the default cross-family timing
run until the IQC matcher is scalable; enabling it changes deployment support,
never the admitted types, their disjoint evidence, or their MDL scores.

`scripts/materials_gcts_macro_promotion.py` then turns each quotient `MacroType`
into the next level's ordinary oriented node. The exact colored atom union is
recentered into a prototype and its proper rotational automorphism group is
learned. Every macro occurrence is independently re-rendered from its child
poses and fitted back to the prototype; atom-index unions remain explicit.
Only training macro pairs with witnessed shared atoms enter the overlap atlas.
Cross-boundary child-port witnesses form a separate finite boundary atlas, so
non-overlapping adjacency is carried without pretending that it covers atoms.

| system | admitted types | exact quotient types | occurrence records / unique exact supports | fit failures |
|---|---:|---:|---:|---:|
| NaCl | 3 | 2 | 6 / 4 | 0 |
| ideal IQC | 75 | 32 | 198 / 87 | 0 |
| Cd--Yb | 2 | 1 | 4 / 2 | 0 |

The promoted program exposes the same prototype/occurrence/support/atlas
contract as the primitive program. `scripts/materials_gcts_recursive_port_hierarchy.py`
therefore applies the unchanged sparse reducer and exact macro miner repeatedly,
stopping when no positive-MDL macros remain:

| system | source types by level | admitted macros | quotient macros | representative MDL saving | largest support reached | termination |
|---|---:|---:|---:|---:|---:|---|
| NaCl | 7, 2 | 3, 0 | 2, 0 | 4, 0 | 18 | no positive MDL |
| ideal IQC | 13, 32, 9 | 75, 22, 0 | 32, 9, 0 | 139, 21, 0 | 94 | no positive MDL |
| Cd--Yb | 91, 1 | 2, 0 | 1, 0 | 2, 0 | 40 | no positive MDL |

Thus the exact quotient substantially removes duplicate execution dictionaries
without changing the admitted evidence or the covered training supports. The
ideal IQC still exhibits two learned compression levels; NaCl and Cd--Yb stop
after one. None is yet an exponential certificate.

`scripts/materials_gcts_stationary_production_signature.py` supplies the
strong comparison that prevents a raw pose-key coincidence from becoming a
stationary claim. It canonicalizes a connected finite-child production modulo
global proper SE(3), child order, declared proper child gauges, and one inferred
uniform translation scale. It preserves child chemistry and chirality,
relative rotations, directed port incidence, overlap chemistry, and boundary
direction/outside chemistry. Stationarity requires three consecutive observed
levels, two matching adjacent comparisons with the same learned scale,
independent low-overlap occurrences, positive MDL saving, and train-only
provenance.

Controls for a single repeated scale, disconnected copied patches, perturbed
amorphous geometry, nonuniform dilation, an improper mirror, changed chemistry
or chirality, and reversed port direction all stay red. The real adapter can
certify individual chemistry/chirality-preserving production signatures, but
the learned hierarchies do not supply three consecutive positive levels with a
single common production and equal learned adjacent scales. Consequently all
real stationary witness counts are zero and the million-site gate remains red.

### Learned stationary crystal control

`scripts/materials_gcts_crystal_stationary_benchmark.py` supplies the positive
control without receiving a unit cell, axes, a space group, a material-family
label, a radix, or a target scale. From the colored point cloud and the admitted
irregular-support occurrence graph, it finds three independent recurring
species-preserving translations. It then infers an integer radix and the
complete child-offset set only when the same nested production is witnessed at
three scales in each of two independent training configurations and improves a
two-part description length.

For NaCl, a 216-atom discovery subset and two 1,024-atom training samples yield
three generators, radix 2, eight child offsets, scale 2, and population
substitution matrix `((8,),)`. The frozen rule recursively materializes two
separate held-out configurations with one-to-one species/position equality: 16
sites at the first level and 128 at the second. Seven symbolic applications
represent 4,194,304 sites from the two-site motif. A ternary synthetic control
independently infers radix 3 and 27 children, guarding against a hidden binary
octuplication constant. The identical pipeline rejects the ideal IQC and an
amorphous cloud because neither has three independent recurring colored
translations. This closes the learned *crystal* stationary benchmark; it does
not close the generic quasicrystal benchmark.

The hardened full-relation audit asks whether that learned crystal vocabulary
is also supported by the generic oriented-port representation. A single sparse
216-atom presentation remains evidence-starved: exact width-eight search admits
only six size-two macros. The confirmatory audit therefore uses two independent
bounded 216-atom presentations. Their complete learned relation graph has
29,988 relations joining 52 cells and admits maximum child width eight. The
exported macro has 8 children, 24 directed ports, a 52-atom colored union, 2
atom-disjoint occurrences, and structural MDL saving 30.

The relation program is frozen before recursive replay. Across three learned
factors the independent witnessed-relation totals are `1,478 / 750 / 86`; the
strong chemistry, chirality, directed-incidence, exact-population, and
stationarity contract accepts the common production with learned scale 2.
Input permutation and global proper-SE(3) metamorphic tests pass, as do the
ideal-IQC, amorphous, and ternary controls.

One limitation remains explicit. The radix and child-offset vocabulary is
proposed by the positions-only stationary grid learner and then validated
against frozen port relations. A pure-port learner that discovers this closure
vocabulary without the grid proposal is future work. The certificate therefore
strengthens the separate crystal baseline without changing the red generic IQC
stationarity result.

### Sparse evidence, dense deployment, and the current marking result

`scripts/materials_gcts_dense_macro_matching.py` preserves the nearly
atom-disjoint sparse occurrences as recurrence/MDL evidence, while finding all
exact proper-SE(3) deployments of admitted macro types for execution. This
separation prevents abundant overlapping placements from manufacturing
recurrence evidence. On the 507-atom ideal-IQC training configuration, a
one-macro seed produces 16 accepted placements and 86 / 86 correct novel atoms.
Because the same configuration supplied the dense matching geometry, this is a
target-blind reconstruction test, not a held-out continuation result.

The dense NaCl reconstruction exposes genuine policy headroom. A bounded
train-frequency connection score reaches the matched correct output with fewer
proposals and higher precision than the unmarked ordering, but it does not beat
31 within-parent shuffled-label controls: its wrong-placement-plus-backtrack
work has empirical `p = 0.40625`. The causal GCTS-marking gate therefore stays
red. A future pass must fit the support grammar, dense deployments, and marking
on a genuinely disjoint training domain, enumerate the same frozen actions in
every arm, and beat both the parent-only baseline and shuffled controls on an
unseen outward frontier.

### Spatially disjoint IQC continuation and confirmatory marking

The next gate removes the fitted-geometry ambiguity. The exact IQC oracle is
used only to prepare immutable colored Cartesian crops; no lift, family label,
cell, golden-ratio value, or target site crosses into the learner. A sphere of
radius 11 about `(-16, 0, 0)` supplies 887 training atoms. A radius-7 sphere
about `(5, -17, 4)` supplies a 231-atom seed, while its radius-11 extension is
reserved for scoring. The training and scoring crops have zero raw atom IDs in
common, their centres are 27.313 units apart (greater than the sum of their
radii), and their squared norms differ, so no origin-fixing proper rotation
maps one benchmark centre to the other.

`scripts/materials_gcts_frozen_frontier_replay.py` now uses an incremental
27-cell spatial index, occupied-site map, pose set, and lazy port-orbit cache.
Exact brute-force parity covers candidate identity, action order, and replay
certificates. On the earlier exploratory disjoint patch, the frozen primitive
grammar grows target-blind from 223 atoms:

| actions | proposed atoms | correct atoms | precision | held-out recall |
|---:|---:|---:|---:|---:|
| 1 | 2 | 2 | 100% | 0.31% |
| 10 | 23 | 21 | 91.30% | 3.21% |
| 100 | 266 | 201 | 75.56% | 30.73% |

Thus the primitive irregular grammar really has unseen exterior actions, but
unmarked precision decays. The densely promoted macro grammar remains a useful
negative control: all 3,144,240 composed IQC proposals reproduce already known
poses, so it has no exterior action yet.

`scripts/materials_gcts_confirmatory_action_consensus_benchmark.py` freezes a
simple rule after that exploratory patch: rank an entire cluster placement by
the sum of normalized train-production frequency and the minimum live support
for any atom it would emit. Live support counts distinct candidate poses, so it
is a finite GCTS connection/overlap marking rather than a potential. The rule,
100-action budget, candidate geometry, and 31 degree-preserving bipartite
incidence shuffles are frozen before the confirmatory target crop is built. A
public radius-11 boundary censors unscored exterior proposals before labels.

| confirmatory arm | exact actions in first 100 | wrong emitted-site counts | work to recover the same 177 correct sites |
|---|---:|---:|---:|
| frequency + GCTS consensus | **97** | **4** | **99 proposals + 3 backtracks** |
| frequency only | 90 | 14 | 145 + 24 |
| consensus only | 95 | 6 | 240 + 44 |
| 31 degree-preserving shuffles | at most 93 | at least 9 | best total 151 |

Exact-action, wrong-site, and matched-work empirical p-values are each
`1 / 32 = 0.03125`. This is the first sealed result in this pipeline where the
GCTS marking itself significantly improves whole-cluster search ordering.
Invalid actions are scorer-labelled for the ablation; it is an ordering test,
not a claim that every wrong proposal is immediately observable online.

`scripts/materials_gcts_batch_frontier_search.py` supplies the corresponding
target-free executor. Each wave freezes the current candidates, computes
whole-placement consensus, and commits a mutually compatible antichain; only
those accepted occurrences feed the next wave. With the strict action-level
threshold ratio `15 / 21` learned on the training patch, the confirmatory run
accepts `3, 17, 4, 30, 5` clusters over five waves and emits 109 / 109 exact
novel atoms (16.62% held-out recall). Fixed diagnostic thresholds expose the
trade-off: zero threshold emits 409 / 435 correct, while 0.5 emits 312 / 320.
The exact five-wave result is genuine self-fed finite continuation. Its
nonstationary wave counts do not certify exponential growth; promotion of
these accepted action graphs is the next clusters-of-clusters gate.

`scripts/materials_gcts_action_macro_promotion.py` now performs that promotion
without a scorer. It renders every accepted occurrence, joins nodes through
exact colored overlap or a witnessed shared-parent attachment, splits connected
components, and records proper-SE(3) child poses, colored unions, overlap and
frozen-boundary certificates. On the exact five-wave confirmation, 59 accepted
placements become eight action macros with child counts
`3, 17, 3, 1, 26, 4, 4, 1`. All eight exactly cover their accepted nodes and
pass union, overlap, boundary-port, and antichain audits. Six nontrivial
components admit stationary canonicalization; each normalized key occurs in
only one wave. The three-wave recurrence count is therefore zero and no scale
law is claimed. A synthetic control accepts three translated congruent waves
and rejects a noncongruent third wave, verifying that this red IQC result is not
caused by a promoter incapable of detecting recurrence.

### Canonical IQC hierarchy: action history versus atomic re-clustering

The action-history route remains a useful negative baseline. Exact connected
subgraphs retain colored unions, directed port incidence, and
symmetry-quotiented proper-SE(3) relative poses. With the corrected invariant
canonicalizer it admits 11 types; every type has maximum dense multiplicity two,
and promotion reaches only two positive levels. Previously reported
action-history counts are superseded and must not be used as the current
recursion evidence.

The stronger history-free route re-clusters the atoms after growth instead of
requiring a repeated move history. Six patch-local clouds contain 2,064 atoms.
Seventy-eight repeated irregular support types have 1,122 occurrences; explicit
gap clusters cover the remaining atoms, giving a complete cover. No action ID,
material-family label, unit cell, or target enters discovery. Boundary-aware
recursive promotion produces:

| route | exact-support quotient types by pass | claim |
|---|---|---|
| one representative per geometry class | `73 -> 17 -> 5 -> 3 -> 2 -> 1 -> 0` | six positive train-compression levels |
| mutually exclusive exact derivations retained | `73 -> 17 -> 6 -> 3 -> 2 -> 1 -> 0` | more exact alternatives, same depth |

The strict production comparison successively audits topology/arity, species
identity and decoration chirality, directed port semantics, normalized proper-
SE(3) poses, and exact nonnegative-integer population substitution. No common
production survives the required three consecutive levels with equal learned
adjacent scales. Stationarity therefore remains red despite the deeper train
compression.

### Sealed re-encoding of the history-free hierarchy

Eight predeclared, mutually raw-ID-disjoint grown patches are split five for
training and three for heldout scoring. Frozen primitive supports cover all
1,248 / 1,248 held-out atoms, including explicit gaps. At the first promoted
level, 256 of 259 frozen quotient types replay and their exact unions still
cover every held-out atom. The three absent IDs are `184`, `185`, and `252`.
All three require primitive type 49, a 23-atom support with exactly two training
occurrences, both in patch 2 near the public crop boundary, and zero heldout
occurrences. Their associated port relations therefore have no heldout witness.
This is a rare patch-local boundary/crop artifact and insufficient independent
multiplicity. It is not a failure to try the right exact derivation: the frozen
semantic mapper tests every train-fitted alternative, preserves its exact
action-terminal identity, has zero ambiguous atom unions and exact assignment
precision 1.0, but remains at 256 / 259 types. No heldout atom is novel to the
primitive support vocabulary.

This separates three claims that should not be merged:

| claim | status |
|---|---|
| train compression on re-clustered grown atoms | green through six positive quotient levels |
| primitive heldout support/atom coverage | green, 1,248 / 1,248 |
| unfiltered promoted type map | red; 3 / 259 level-one types are patch-2-only boundary artifacts |
| strict-majority recurrent-core re-encoding | green through four exact levels, with explicit residual terminals |
| autonomous continuation and stationary/exponential growth | red; heldout positions are observed and stationary witnesses remain zero |

The production policy now fails closed on patch-local artifacts. A generic
train-only recurrent-core selector retains an exact quotient macro only when it
occurs in a strict majority of the five independent training namespaces
(`3 / 5`). Repeated occurrences inside one patch cannot satisfy the gate,
cross-patch occurrences are invalid evidence, and the original macro IDs and
exact action terminals are never renumbered. Atoms not represented by the
selected core are exported as exact `(patch, raw index, species, position)`
terminals. The core plus those terminals has a coordinate/species SHA
certificate equal to the complete atom cloud.

The main width-five audit freezes the learned training vocabulary—including
supports, ports, quotient types, and exact derivation alternatives—then
**re-encodes** the three fully observed heldout patches without refitting:

| recursive level | raw -> selected/exact types | exact occurrences | exact core atoms / 1,248 | residual atom terminals | minimum heldout namespaces | maximum support atoms |
|---|---:|---:|---:|---:|---:|---:|
| 1 | `520 -> 148` | 1,495 | 1,220 | 28 | 2 | 78 |
| 2 | `53 -> 10` | 85 | 1,033 | 215 | 3 | 78 |
| 3 | `16 -> 4` | 29 | 925 | 323 | 3 | 110 |
| 4 | `3 -> 1` | 9 | 870 | 378 | 3 | 111 |

Every selected type has at least two exact proper-SE(3) heldout occurrences,
and the residual certificate makes every level a complete representation.
However, the matcher receives all 1,248 heldout positions: heldout geometry is
observed to enumerate and match types, while only the learned vocabulary is
frozen. These numbers are therefore frozen-vocabulary representation
transfer, not target-blind proposal, continuation, or material growth.

The selected hierarchy has no action amplification above three, no normalized
stationary production key common to three consecutive levels, and no evidence
of a self-fed exterior executor. Accordingly `autonomous_growth = false` and
`exponential = false`; the IQC gate remains red. The separate learned NaCl
stationary crystal control is unchanged.

### Target-blind recurrent-macro continuation

The re-encoding result above is no longer the strongest executable IQC claim.
A separate sealed benchmark trains on five mutually raw-ID-disjoint **raw IQC**
radius-11 windows (4,405 atoms), rather than on patches produced by an earlier
growth policy. The generic width-three miner yields 322 exact first-level
macros; the train-only strict-majority gate retains 141, represented by 844
training occurrences, 5,886 overlap ports, and 5,820 witnessed boundary ports.

The evaluation window is centered at `(40, 0, 0)` and shares no raw atom ID
with the five training windows. Its radius-7 seed contains 226 atoms. Frozen
support enumeration and exact macro fitting find two placed first-level macro
occurrences; all seed atoms, including those outside those macro supports,
remain explicit collision constraints. The executor has no target or ranker
callback. It composes only frozen port orbits with the preceding placed
frontier, rejects improper poses, unlike-species coincidences, sub-minimum
collisions, insufficient overlap, and positions outside the public radius-11
boundary, then commits compatible whole macros. Every accepted placement
carries an overlap-inclusion and train-witnessed-adjacency certificate.

| wave | eligible whole macros | accepted | emitted atoms |
|---:|---:|---:|---:|
| 1 | 44 | 16 | 92 |
| 2 | 18 | 8 | 56 |
| 3 | 0 | 0 | 0 |

The 873-atom scoring crop is opened only after the proposal trace is frozen.
Of 148 proposed novel atoms, 136 are exact species/position matches and 12 are
wrong: precision is 91.89% and recall over the 647 atoms outside the seed is
21.02%. Candidate batches have immutable SHA digests, all 24 acceptances are
self-fed clusters-of-clusters actions, and target use during proposal or
ranking is false. Thus autonomous macro continuation is now implemented and
measured, but the gate remains red. A scheduling audit shows that “number of
waves” is not a scientific depth measure: lowering the per-wave batch cap from
40 to 8 changes `16 -> 8 -> 0` into `8 -> 8 -> 8 -> 0`, while producing the
identical 148-atom union. The invariant parent-child DAG has causal depth two
and reaches a finite fixed point. Precision is below 99%, recall is far below
95%, and there is no recursive amplification.

The first matched marking audit now labels every eligible proposal on five
train-only radius-7 to radius-11 frontiers, rather than fitting only accepted
connections. This supplies 718 actions (693 valid and 25 invalid) and freezes
310 bounded order-two log-odds states. All 33 evaluation arms share the same
44 first-wave candidates, and every trace is frozen before the target factory
is opened. However, all 62 evaluated commit candidates have unseen marking
contexts: exact transfer is 0, parent/production backoff transfer is 0, the
first wave has one score and zero rank inversions. Marked and unmarked both
emit 148 atoms with 136 correct; all 31 within-parent label shuffles tie and
give empirical `p = 1`. The causal macro-marking gate therefore remains red
for a precise reason: the present marking vocabulary does not transfer from
internal training frontiers to the exterior evaluation roles.

An ID-free quotient now addresses that exact failure without changing the
candidate geometry. Its hierarchy uses a symmetry-canonical port-pose key,
then `(connection kind, overlap-species set)`, then a kind-only marginal. Bin
widths are chosen by leave-one-training-patch-out log loss over nine fixed
schemas. Coverage rises from zero to all 62 evaluated candidates: 16 use the
full incident context, 14 the pose-only backoff, 30 the overlap-chemistry
backoff, and 2 the kind marginal. It creates five distinct first-wave scores
and 112 pairwise rank inversions. The final atom set is still 136 / 148, while
matched exact-action work falls from 71 to 51; with 31 label shuffles the
empirical result is only `p = 0.25`, so it is useful compression but not yet a
causal marking win.

A second, continuous mark now uses 35 ID-free proper-SE(3) invariants: prototype
composition, radial/pair moments and proper-symmetry counts; normalized port
translation/rotation and overlap chemistry; live overlap/emission fractions;
train evidence; at most two incoming-port summaries; and live proposal-witness
and emitted-site-consensus statistics. Ridge strength is
selected only by five-fold spatial training validation. Its log loss is
`0.0186` versus the global prior's `0.1511`; the unopened evaluation frontier
gets 29 distinct first-wave scores and 362 rank inversions. Yet unpruned
execution again produces 136 / 148. A threshold frozen from out-of-fold
training at 100% precision/recall prunes to 14 macro placements but produces
134 correct and the same 12 wrong atoms (91.78% precision). Some shuffled
threshold arms emit no shared correct atom, so matched work is explicitly
incomparable rather than selectively dropping those controls. This exposes a
train-to-exterior calibration shift; neither mark is integrated as the
default policy.

Uniformly jittering the five training nuclei is not the remedy. Thirty
predeclared ±1-nearest-neighbor shifts yield 25 executable frontiers and grow
the training table from 718 to 3,119 candidates, but failures rise only from
25 to 30. Evaluation parent-role coverage remains 0 / 62 and the median
standardized role distance remains 5.32. The apparent validation improvement
is positive duplication, while projected score spread contracts. This
augmentation is rejected; the next sampler must maximize train-only role and
failure diversity explicitly.

That sampler is now implemented. It enumerates 596 patch-specific
boundary-exposed representatives and selects a geometry-only cover of all 141
learned parent macro types before candidate labels exist. The result rules out
simple role omission: every one of the 48 incorrect sealed candidate actions
uses an exact `(parent type, production)` pair observed as correct in the
training windows. Ranking therefore cannot infer failure from rule identity.
Inward-prefix contexts and class balancing change work order but do not remove
the errors; a fifth-patch threshold rejects correct actions instead.

The terminal-level diagnosis is sharper. Eight of the 12 final wrong atoms
sit at exact target coordinates but carry `Y` where the sealed target carries
`Z`; four proposed `Z` sites are absent, one nearest-neighbour spacing from the
closest target site. Thus the remaining error is mostly context-dependent
chemical decoration of otherwise useful geometry. A bounded colored-site
section uses only the proposed species plus rotation-invariant local neighbour
distances. Four patches provide 3,047 deduplicated terminal records, only ten
of which are recolor/absence cases; the fifth patch freezes the alternative
margin at 100% precision and recall. Before the sixth target is opened, the
section predicts four recolors and ten absences. Posthoc scoring is worse:
124 correct and 16 wrong atoms, 88.57% precision. This is retained as an
honest red diagnostic and is not integrated into self-fed execution. The next
marking representation must learn reusable decoration alternatives at the
cluster/cluster-of-clusters level rather than postprocess isolated sites.

That geometry-first representation is now explicit. The learner hides all
species labels while fitting 35 irregular geometric support types from the
4,405-atom training corpus, then attaches the observed colored decorations
modulo each support's proper rotational symmetry. The factored vocabulary has
275 exact decoration alternatives; 29 / 35 geometry types have more than one.
On the disjoint 873-atom window, every geometry type transfers and supports
cover 841 atoms (96.33%). Train-seen decorations cover 795 atoms (91.07%),
although only 706 / 4,519 frozen occurrences have their exact decoration in
training. Expanding the alternatives naively would produce 49,735 colored port
classes, versus 7,731 factored geometry ports for the same 778,380 witnessed
relations, a 6.43-fold vocabulary penalty.

The first bounded GCTS decoration section uses one or two already-inward
overlap ports. On a common heldout causal sample, two-port composition predicts
30.37% of decorations, versus 25.79% for one port and 20.34% for the modal
geometry decoration. This apparent gain is not yet causal evidence: 31
within-geometry label shuffles have median accuracy 31.81% and give
`p = 0.875`. The marking gate therefore remains red.

An overlap-cover solver now tests the alternatives jointly. The complete
heldout positions are supplied, the radius-7 seed contributes 226 known
species, and all 647 outer species stay sealed until scoring. All 4,519 frozen
geometry occurrences are optional covering proposals. A proposal may
propagate only after overlapping an already labelled atom, and only labels
unanimous across its remaining train-observed alternatives are committed. The
solver retains geometry over 831 / 873 atoms and infers 279 outer labels: 267
are correct and 12 wrong, for 95.70% precision and 41.27% recall. It is a
reconstruction baseline, not autonomous coordinate growth; the unchanged 99%
precision / 90% recall gate remains red. The next step is bounded branch-and-
backtrack selection among exact decoration alternatives, with marking used to
order identical candidate sets.

That bounded search is now executable. It freezes 55,483 exact actions—one
geometric occurrence, one train-observed decoration, and one proper rotational
gauge—and exposes no target-species argument. A beam state stores only seed or
committed species and selected occurrences; unlike-species overlap prunes the
branch. Every arm receives the identical candidate SHA. With a predeclared
six-atom overlap and 99% train-posterior threshold, the GCTS connection policy
finds 354 correct labels among 415 inferred outer atoms (85.30% precision,
54.71% recall). The modal arm finds only 116 / 140 (82.86% precision, 17.93%
recall). All 31 within-geometry label shuffles collapse to the modal result, so
both precision and correct-atom comparisons give `p = 0.03125`. This is the
first significant evidence that learned GCTS ranking/admission improves the covering
search over identical cluster alternatives. It is not a reconstruction pass:
61 labels remain wrong and the 99% / 90% gate stays red.

The first geometry-first cluster-of-clusters decoration audit also prevents a
misleading shortcut. Width-three mining admits 1,263 macros and exact geometry
quotienting retains 457 types with 18,660 dense train occurrences and 15–55
atoms per support. On a deterministic sparse heldout primitive cover, only 12
macro geometry types / 13 occurrences transfer, covering 254 atoms. The train
vocabulary contains 1,229 whole-macro decoration alternatives, but none of the
13 heldout macro decorations is train-seen. Treating a whole macro's chemistry
as its identity therefore increases memorization rather than transfer.

Using macro geometry only as a bounded mark on each primitive child is better
but still red. `(macro type, child role)` covers all 27 transferred child
samples and predicts 5 / 27 decorations, versus 2 / 27 for the primitive modal
baseline. Thirty-one within-primitive-type shuffles reach as high as 6 / 27;
the learned result has `p = 0.1875`. The next hierarchy representation must
retain exact child decoration alternatives while quotienting the macro boundary
mark more coarsely than exact macro type/role. Full promoted-atlas construction
was also removed from this audit: an atom-inverted exact overlap index and
lightweight prototype/pose deployment avoid an unnecessary multi-gigabyte
all-pairs port expansion.

A train-selected lower-cardinality macro-boundary key does not rescue the
ideal-IQC chemistry. Leave-one-patch-out selects a `boundary_fine` descriptor
from child geometry, macro arity, graph degree, boundary incidence/direction,
normalized radial role, and support-size ratios; it contains no macro or
occurrence ID and no world pose. It still predicts only 5 / 27 heldout child
decorations (`p = 0.125` against 31 within-child-type shuffles). Combining all
boundary marks per unique child gives 3 / 19 (`p = 0.21875`). The exact
alternative ceiling explains much of the failure: only 9 / 27 role samples and
7 / 19 unique children have their correct full decoration anywhere in train.

Factorizing a decoration into a maximum-information tree of unary and pairwise
site sections can emit unseen combinations, but unconstrained composition is
also insufficient. On ideal IQC it raises heldout exact occurrence accuracy
only from 4.96% to 5.44% and site accuracy from 68.68% to 69.78%; 811 predicted
whole decorations are unseen in train and none is exactly correct. The partial
section is retained as an honest red generator, not added to search.

### Published Cd--Yb disjoint reconstruction

The same generic geometry/decoration pipeline now has a stronger real-material
test. Two predeclared, mutually disjoint radius-14 crops of the published
Cd5.7Yb model provide 969 train atoms; a third radius-14 crop, at least 30.55
angstrom from either train centre, provides 478 evaluation atoms. The learner
receives positions/species only—no cut-and-project coordinates, source-site
labels, family name, cell, or physical potential. With species hidden during
geometry fitting, 166 support types and 713 frozen evaluation occurrences
cover 449 / 478 atoms (93.93%). This is a large improvement over the earlier
single 506-atom crop's 277 / 478 (57.95%) coverage. Whole-decoration modal and
pair-factor models both reach 66.20% exact occurrence and 94.57% site accuracy;
the remaining 29 explicit singleton gap clusters are only 27 / 29 correct
under a bounded radial/nearby-cluster KNN mark.

Joint covering search resolves that ambiguity much more strongly than
independent classification. A radius-7 colored seed contains 59 atoms. Every
arm then receives the same 1,385 exact actions formed from 713 frozen geometry
occurrences and 174 train-observed decoration alternatives. With a five-atom
overlap and 99% train-posterior threshold, GCTS reconstructs 378 / 378 novel
atoms exactly: 100% precision and 90.21% recall over the 419-atom outer region.
The modal arm and all 31 within-geometry label shuffles reconstruct 377 / 377,
for 89.98% recall. Precision is at 100% for every arm; the meaningful causal
comparison is extra correct reach at no precision loss, where GCTS gives
`p = 0.03125`. Thus the unchanged 99%-precision / 90%-recall reconstruction
gate and the matched-quality GCTS marking gate are green on a published
icosahedral material model. Coordinates are supplied and the search reaches a
finite fixed point, so autonomous continuation, stationary recurrence, and
exponential growth remain red.

### Published Cd--Yb autonomous frontier continuation

Reconstruction no longer supplies the outer coordinates in this follow-up.
The two 969-atom training crops fit 175 colored irregular cluster types, 804
occurrences, and 14,595 finite proper-SE(3) overlap ports. Six candidate
consensus thresholds are evaluated only on radius-7 to radius-14 training
reconstructions. Threshold 0.6 is the highest-reach choice for which both
training windows retain at least 99% precision (both are in fact exact).

The frozen grammar then sees only the disjoint 59-atom colored seed and a
public radius-14 boundary. Six recognized clusters cover 49 seed atoms; ten
explicit singleton gap clusters complete the seed. All evaluation executions
finish and their candidate/action/site digests are frozen before the 478-atom
target factory is called. Five self-fed waves accept
`3 -> 18 -> 9 -> 35 -> 7` complete clusters and emit 179 novel coordinates;
the scorer finds 177 correct and 2 wrong, or 98.88% precision and 42.24% recall
over the 419 outer atoms. An unfiltered diagnostic emits 366 atoms and reaches
68.26% recall at 78.14% precision, while strict consensus emits 19 / 19 at
only 4.53% recall. This makes the bounded finite-autonomous continuation gate
green without hiding its precision/coverage trade-off.

The selected target-free trace also feeds the cluster-of-clusters loop.
Commuting wave placements become colored action macros with exact node cover,
proper poses, colored unions, overlap intersections, frozen incoming ports,
and antichain certificates. No normalized action-macro production recurs over
three waves. Continuing the same threshold past the calibrated five waves also
accumulates errors. The result is therefore finite autonomous real-material
continuation, not sustained stationarity or exponential symbolic growth.

### Bounded local section and causal growth ablation

The first autonomous errors are locally valid port applications, so raw
production identity and prototype-size envelopes do not transfer reliably.
The improved marking uses the local frontier itself. For every candidate it
measures the closest proposed-site distance to the already placed cloud in the
training-derived nearest-neighbor unit and counts distinct frozen
cluster-connection witnesses for the same pose. Among the 390 train-selected
candidate samples, the distance distribution has a train-fitted gap at 2.118
nearest-neighbor units. On its close side, the minimum witnessed correct action
has five independent connections. The frozen section therefore rejects a close
proposal with fewer than five witnesses. It neither generates coordinates nor
uses absolute position, direction, family, cell, potential, source-site label,
or evaluation target.

The original evaluation nucleus now executes
`3 -> 18 -> 9 -> 35 -> 5 -> 1 -> 0` placements and emits 178 / 178 correct
atoms (100% precision, 42.48% outer recall). A second predeclared radius-14
nucleus at `(-15, 10, -15)`, disjoint from both training crops and the first
evaluation crop, executes `2 -> 12 -> 6 -> 4 -> 10 -> 14 -> 0` and emits
117 / 117 (100% precision, 27.73% recall). The corresponding unmarked runs
emit 193 / 220 and 168 / 224, for 83 false atoms in aggregate.

The causal null preserves every frozen candidate and, separately within each
wave, the complete witness-count multiset, but permutes witness counts among
placements before the scorer is opened. All 31 shuffled policies run their
full self-fed consequences on both nuclei. None reaches the learned section's
295 correct atoms at zero error (`p = 0.03125`). Thus finite autonomous
continuation, transfer across two nuclei, and the matched GCTS-marking gate are
green on the published Cd--Yb model. Target-free promotion certifies the
resulting action macros, but no normalized production recurs across three
waves; sustained stationary and exponential quasicrystal growth remain red.

An extended radius-25 diagnostic from the same first-wave candidate batch emits
416 atoms over three waves and matches 374 (89.90% precision), but 39 scoring
atoms overlap a training window. It is retained only as a depth diagnostic and
is not a sealed result.

### Deep Cd--Yb hierarchy and frozen transfer boundary

The history-free cluster-of-clusters loop now has a substantially larger
real-material corpus. Five mutually disjoint radius-14 crops of the published
Cd5.7Yb model contain 2,385 atoms. Each crop is recentered and packed into a
separate 80-angstrom namespace before learning, which prevents a support or
port from joining nearly touching crop boundaries. The positions/species-only
cover is complete: 2,360 atoms belong to recurring irregular supports and 25
are explicit gap terminals. It learns 274 primitive support types, 1,697
occurrences, and 21,056 finite proper-SE(3) ports.

Exact macro mining, derivation quotienting, and promotion then produce nine
positive levels:

`80 -> 36 -> 22 -> 15 -> 8 -> 6 -> 4 -> 2 -> 1 -> 0`.

The largest exact colored support rises from 67 to 472 atoms. Every admitted
macro has at least two low-overlap proof occurrences and every occurrence is
confined to one crop namespace. At level one, 79 / 80 retained quotient types
are witnessed in at least two disjoint windows; the remaining type is confined
to one. Every retained type at the later positive levels has two-window
evidence. The five windows are distinct exact configurations, although
disjoint atom domains alone do not imply statistical independence. The loop
terminates at evidence exhaustion. This is genuine deep clusters-of-clusters
compression, not a visible extra pipeline stage. The exact nine-level depth is
deterministic on this packed corpus; robustness to resampling and positional
perturbation has not yet been established.

The unchanged strict stationarity audit remains red. No production key is
shared across three consecutive levels; the first failing field is already
child-count/topology, before chemistry, directed ports, normalized proper pose,
scale, or population substitution can rescue it. Declining support-growth
ratios and eventual crop saturation are not labelled exponential growth.

A separate frozen audit observes two reserved, mutually disjoint radius-14
windows containing 959 atoms. It does not refit or renumber the training
grammar. A finite region need not instantiate every symbol in a grammar, so
the corrected deployment keeps the complete frozen type/port vocabulary while
allowing absent types to remain dormant. Only exact active occurrences can
seed the next level; dormant symbols are never counted as transferred.

| level | frozen types | active types | dormant types | active occurrences | covered atoms |
|---:|---:|---:|---:|---:|---:|
| 1 | 80 | 53 | 27 | 92 | 560 / 959 |
| 2 | 36 | 20 | 16 | 26 | 445 / 959 |
| 3 | 22 | 8 | 14 | 8 | 314 / 959 |
| 4 | 15 | 2 | 13 | 2 | 170 / 959 |
| 5 | 8 | 0 | 8 | 0 | 0 / 959 |

Thus the frozen hierarchy has four positive heldout re-encoding levels rather
than one. Every attempted level preserves frozen IDs, all frozen overlap and
boundary ports, exact proper-SE(3) replay, train-admitted relations, and a
complete coordinate/species representation through explicit residual
terminals. Each active type has only one-window/one-independent-occurrence
minimum evidence in this small heldout corpus, and level five stops when no
exact active occurrence remains.

The negative controls explain why this cannot be turned green by a convenient
filter. Every one of the 27 absent first-level types occurs in two of five
training windows, as do 50 / 53 active types; a strict-majority core retains
only two types and covers 13.56% of heldout atoms. Four predeclared
chemistry/chirality/proper-geometry descriptors produce 80, 80, 79, and 77
classes, but none forms a port-consistent semantic class recurrent across
three training namespaces, and exact derivation alternatives recover zero
absent types. Heldout-tuned pooling is therefore rejected.

Because the heldout coordinates are observed for matching, this is exact
four-level re-encoding—not autonomous emission. The nine-level train hierarchy
and four-level frozen deployment are stronger clusters-of-clusters evidence,
while transferable vocabulary closure, stationary recurrence, and exponential
Cd--Yb growth remain red.

### From hierarchy re-encoding to seed-only macro execution

The next benchmark asks whether the frozen higher levels can actually emit
coordinates. It uses the same five training crops and a predeclared evaluation
centre `(35, 30, 20)` in a wider published-model crop. The learner receives a
478-atom radius-14 seed and a public radius-25 boundary. The 2,696-atom scoring
target is at least 49.244 angstrom from every training centre—greater than the
39-angstrom sum of train and target radii—and is opened only after every
candidate trace is immutable.

The seed contains 276 frozen primitive occurrences and 500 train-admitted
primitive relations, but no complete level-one promoted macro. Consequently,
the exact hierarchy executor cannot start any of its nine frozen levels. A
NaCl control recognizes and executes its frozen level-one macro with exact
certificates, so this is a Cd--Yb vocabulary/recognition failure rather than a
missing executor API.

GCTS can recognize a partial macro instead. The generic matcher anchors a
frozen RHS on already observed child clusters, enumerates every finite proper
symmetry gauge, requires a train-admitted internal or boundary port from the
anchor to a missing child, and rejects collisions, public-boundary violations,
and cross-parent ambiguity. Two-child recognition remains empty. Allowing one
finite child witness over all 181 exact derivation alternatives produces 82
target-blind completion candidates and 333 unique proposed atoms. Posthoc only
6 / 82 complete actions are exact; the other 76 show why completion must be a
tree-search decision rather than an unconditional macro copy.

A bounded GCTS mark is fitted only on five radius-7 to radius-14 training
frontiers. Those contain 14 completion candidates—8 positive and 6 negative.
Five-fold leave-one-patch-out freezes threshold 0.25 and a top-five budget.
On the sealed radius-14 to radius-25 frontier, the marked top five contain one
exact and four wrong actions, emitting 16 correct and 18 wrong sites. Constant
ordering also finds one exact action (13 correct / 24 wrong sites); a
frequency baseline finds none. All 31 within-parent train-label shuffles tie
the marked result, giving `p = 1`.

Thus partial promoted completion is now finite, target-blind, proper-SE(3),
port-witnessed, and executable in principle, but its current marking does not
transfer. The next algorithmic target is a lower-cardinality or learned
continuous local section trained on a more diverse set of train-only frontier
failures, followed by a newly predeclared confirmatory nucleus. No autonomous
hierarchical or exponential claim is made from this red result.

### Publicly preregistered second nucleus

The next test was frozen in two public commits before its target was accessed.
The geometry manifest fixes centre `(35, 35, -35)`, radius-14 seed, radius-25
public boundary, and an atom-domain separation above 55 angstrom from every
training window and the previously opened evaluation nucleus. Protocol v2
additionally freezes the actual 28-row training-corpus digest, continuous-model
weights and digest, five source-file hashes, feature schema, top-five/no-threshold
decision rule, three waves per level, four levels, and 31 deterministic
within-window label-shuffle refits. Its one-shot guard enforces the order

`protocol -> train -> model -> seed -> candidates -> controls -> execution -> target -> score`.

One harness invocation aborted before the seed because it looked for geometry
fields on protocol v2 rather than the referenced v1 geometry manifest. The
zero-target-access abort and sole field-source correction were committed as an
erratum before proceeding. The scientific run then opened and scored the target
exactly once.

The common first wave contains 36 target-blind candidates. None is a completely
exact macro action. The continuous mark's top five emit 27 correct among 56
unique proposed sites (48.21% site precision); stable and frozen-frequency
ordering each emit 10 correct among 41 (24.39%). This numerical improvement is
not causal evidence: all 31 shuffled-label refits select the same marked result,
so exact-action, correct-site, and matched-work tests all give `p = 1`. Marked
matched work is 8 checks versus 14, a 1.75x reduction below the frozen 2x gate.

The marked executor still demonstrates real clusters-of-clusters mechanics. It
accepts `5 -> 5 -> 5` placements at level one, `5 -> 5 -> 5` at level two,
`1 -> 0` at level three, and `0` at level four. That is seven consecutive
nonempty self-fed waves. Posthoc, its frozen union contains 247 of the 2,217
outer-shell target atoms, or 11.14% recall. The primary marking gate and the
sustained-growth gate both remain red; stationarity and exponential growth are
unchanged and red. The complete result, event sequence, candidate/plan/execution
digests, and null arrays are stored as a hash-checked fixture, and the benchmark
now refuses to reopen the consumed scientific target.

### Moving the section inside a macro

The sealed failure shows why a whole promoted macro is too coarse a GCTS
decision: none of its first-wave actions is entirely exact, although 27 of the
56 marked emitted atoms are correct. The replacement section does not alter
candidate geometry or IDs. It learns a bounded score for each emitted site
from ten local proper-SE(3)-invariant quantities: chemistry, distances to the
RHS centre, seed, witnessed children and other emissions, local coordination,
overlap multiplicity, matched-child fraction, missing-child count, and frozen
port evidence.

The five authorized training windows now use three predeclared inner radii
(`5.6`, `7.0`, and `8.4` Angstrom) and the same fixed nearest-neighbor shifts.
They produce 123 macro candidates and 1,245 unique candidate-site examples, of
which 871 are supported and 374 unsupported. Nested grouped validation gives
site AUC 0.8864 and action AUC 1.0. Both exceed every one of 31 within-window
label shuffles (`p = 0.03125`). The broader corpus therefore improves both site
and whole-action ordering rather than merely duplicating easy positives.

Admission remains more stringent than ranking. A zero-observed-error threshold
is placed 1.5 logit units above the largest negative grouped-OOF score. Holding
that margin fixed gives 172 / 176 correct held-window selections (97.73%
precision, 19.75% recall), and every nonempty fold is at least 96.15% precise.
The final serialized threshold is `0.9990244124431729` and selects 70 / 70 OOF
sites (8.04% recall). But the margin was selected using all five training
windows. When margin selection is repeated inside every outer fold, it reaches
274 / 290 correct (94.48% precision), below the unchanged 95% deployment gate.
The candidate model is now nonempty and substantially better calibrated, but
the model-selection procedure remains red; no new Cd--Yb target is opened.

A separate exact-decomposition control tests whether geometry alone should cut
the action more finely. Port-connected missing children do not split these 14
training candidates. A Gabriel-graph frontier peel creates ten explicit
residual subclusters and preserves all 148 novel sites exactly, but lowers
emitted-site precision from 110 / 148 to 62 / 90 without changing the 8 exact /
6 mixed action count. It is retained as a negative control, not a growth rule.

The generic executor therefore uses exact port-connected components as the
atomic commitment boundary, applies the frozen site section within each
component, accepts a conflict-free high-score subset, and records every
unaccepted obligation as an exact species/position/owner residual. A partial
site mask never creates an occurrence. A child occurrence becomes admissible
only after its entire frozen colored support is present; a parent is promoted
only after every child is complete, every internal and boundary port is
admitted and independently reverified, and an exact proper-SE(3) prototype fit
succeeds. Synthetic controls demonstrate partial deferral, later child
completion, and exact parent promotion. The NaCl two-wave control emits 48 / 48
correct sites, while making no compression claim. Because the Cd--Yb threshold
fails closed, this machinery is not yet deployed on a new Cd--Yb target. No new
Cd--Yb target is used in fitting or these controls.

### Bounded recurrent branch value

The first autonomous pose-port confirmation fails in value rather than
geometry: its exact three-action terminal configuration is present but ranks
tenth. A geometry-only maximin expansion adds twelve development nuclei and
retains every one regardless of outcome. The resulting 30-group corpus has
354 invariant depth-three branches, 211 exact, and exact supply in 21 groups.
The cumulative state-probability product selects 17 / 21. A target-free
nearest-recurrent value uses nine proper-SE(3)-invariant branch measurements
plus the order-independent action-color population. Whole-group selection
chooses `k = 9` and selects 20 / 21 exact branches (`95.24%`) without changing
the candidate set. Its frozen model digest is
`dcaae79dc2a8c3edf1caec7fc32b05054077c125e8b1e5ad93c11e8097be56ce`.

Reusing the already-consumed failure only after fitting moves its exact branch
from rank 10 to rank 1. Refitting the upstream finite pose-port model on all 30
groups gives 12 / 12 exact terminal configurations on that diagnostic. This
is green development evidence only.

The separately committed confirmation at `(40, -40, -80)` has now run once.
Before its seed was generated, the 30-group pose-port marking was frozen as a
typed compressed vocabulary containing 148,729 token weights and 876 recurrent
states; its state and branch model digests, reach four, beam four, depth three,
target-open ordering, and exact `3 / 3` gate were preregistered. The target-free
tree froze `4 / 16 / 16` candidates, retained four configurations at each
depth, and produced four terminal branches. Only then did a single target
factory verify coefficient bounds 44 and 45 and expose 2,033 scoring atoms.
No terminal branch is all-exact; the selected branch places `2 / 3` colored
sites correctly. Candidate digest
`9ef36560339e20e6b384a6a85199e5e277b5213a3e9845ef81b07526fd1cda48`
and pre-target trace digest
`0a30b5945c7fdcc81f4f71e3e6ccbdbdcd3bcd3b88936601afa27430290fcf80`
are preserved. Thus the fresh failure is upstream candidate supply/beam
retention, not merely terminal-value ranking. Autonomous, stationary, and
exponential IQC growth remain red.

The search-value implementation now acts before terminal pruning. A fixed
target-free schedule (`4 / 4 / 8` local reach, bounded color-population
diversity) freezes 1,259 partial configurations over the same 30 development
nuclei, of which 934 have exact colored prefixes. Separate recurrent heads use
the same ten invariant branch measurements and order-independent color counts;
neighbor capacities are selected independently by leaving out whole nuclei.
Depths one through three choose `k = 25 / 15 / 9` and select exact prefixes in
`29 / 29`, `27 / 28`, and `25 / 28` supplied stages. The combined `81 / 85`
(`95.29%`) clears the frozen-snapshot gate. Score ties are evaluated as complete
equivalence classes: a mixed exact/false top tie cannot pass by insertion
order. Candidate digest is
`649fd2786f9030051bf160f6ff9dbc850c89002f25d44cc25d907e9c2769606c`.

Closed-loop execution remains red. On the consumed confirmation nucleus, the
three frozen heads produce zero exact terminal configurations at beams 4, 8,
and 16; every selected result remains `2 / 3` correct. Thus the new heads are a
real transferable marking improvement on frozen partial states, but not yet a
self-fed autonomous scheduler or an exponential-growth certificate.

A finite recurrent-state beam then replaces color-only diversity. Each
candidate is normalized by its train-fold depth head and quantized without
coordinates, IDs, material labels, or target atoms. The selected state widths
are `4 / 4 / 2`, per-state quotas `1 / 2 / 1`, and total budgets `4 / 4 / 8`.
This retains at least one exact prefix in all `29 / 29`, `28 / 28`, and
`28 / 28` supplied frozen stages—85 / 85 overall. The same fixed scheduler is
still red in the consumed closed loop: it keeps `2 / 4 / 8` configurations,
finds zero exact terminal branches, and selects `2 / 3` correct colored sites.
The remaining failure is therefore transfer under the self-fed state
distribution, not raw beam capacity or frozen-snapshot state coverage.

One group-sealed branch-value aggregation round now targets that distribution
shift directly. In each of five folds, four heldout nuclei are absent from the
value fit; the pose-port state model used by the on-policy rollouts is likewise
refit without them. The other 26 nuclei contribute 4,037 visited partial
branches (3,224 exact). The fit keeps both labels when identical invariant
descriptors have different futures rather than using candidate order to erase
the alias. The frozen closed-loop audit improves terminal exact-path supply
from `16 / 20` to `18 / 20`, top selection from `10 / 20` to `13 / 20`, and
selected correct moves from `44 / 60` to `51 / 60`. This gives a sharper
failure decomposition: two nuclei have no exact retained terminal, while five
contain an exact terminal that is misranked.

The estimate is not fully nested end to end. The older broad snapshot features
were generated once with the shared upstream pose-port model, although rows
from heldout nuclei are excluded from every branch-value fit. The 13 / 20
result is therefore a branch-value development comparison rather than a sealed
pipeline estimate. It is red even under that weaker interpretation: the gate
requires both at least 90% supply and 90% exact selection; supply is exactly
green, selection is only 65%, and a new confirmation is not authorized.

The immutable on-policy corpus digest is
`3683f5091e954c0605fa0115193365a9210a26074e61f1ee539cbbd12831d53f`;
the target-free closed-loop candidate digest is
`395eba0f5a5e66a43a4367cb5e447d48082c67aed60497c9a5631791e5d76cbd`.
These results are development cross-validation, not an autonomous-growth or
stationary-production certificate.

The follow-up fully nests the upstream marking and makes the proposed channel
semantics explicit. For every fold, the pose-port model is refit without all
four heldout nuclei before either broad or on-policy branches are generated.
Each action contributes five finite proper-SE(3)-quotiented channel responses;
the responses form an order-independent multiset, while six colored pair-
distance fields retain how connection geometry is assigned to `XX / XY / XZ /
YY / YZ / ZZ` roles. Exact coordinates remain only in candidate construction
and scoring certificates.

With the candidate reach and recurrent-state beam held fixed, the ablation is:

| branch representation | exact selected | exact terminal supplied |
|---|---:|---:|
| base aggregate statistics | 14 / 20 | 17 / 20 |
| base + colored connection geometry | 15 / 20 | 17 / 20 |
| base + five pose-port channels/action | 14 / 20 | 16 / 20 |
| coupled geometry + pose-port channels | 15 / 20 | 16 / 20 |

The one-round on-policy refit of the coupled model decreases exact selection
to `14 / 20`; it is not retained as an improvement. Raw pose-orbit/channel
identity alone therefore does not improve the value function. The modest
positive signal comes from channel-conditioned colored geometry, consistent
with treating a GCTS marking as a local connection section rather than one
scalar or one slot per observed rotation. The result is fully nested but still
red at 75%, below the 90% gate. Its corpus digest is
`8ebfa3e6cc445fd84d33089ef92c96dbe238108dc6958a73ef6e929953e7d0e3`;
its target-free closed-loop candidate digest is
`3658d67adddd8f92d07471e5681b6ce60583861bbbf655a3ed84cb0bf76871af`.

### Fixed-width marking library and terminal value

The four representations are also executed as a marking-library portfolio.
Each marking produces a state-diverse ordering, but round-robin allocation
shares the unchanged `4 / 4 / 8` total beam; this is not a fourfold beam or
proposal-budget increase. The portfolio raises exact-terminal supply from the
single coupled marking's `16 / 20` to `18 / 20`. Its raw order is deliberately
not presented as a value win: it selects only `13 / 20` exact paths and
`51 / 60` correct moves.

For each outer fold, the terminal value is fitted on the portfolio terminal
states actually visited in the other 26 nuclei. A nested whole-nucleus audit
selects both the representation and nearest-recurrent capacity from the fixed
grid. Fold choices are `ports:k3`, then `base:k9 / k5 / k1 / k9`. Frozen on the
four outer nuclei, this value selects `16 / 20` exact terminal paths and
`54 / 60` correct colored moves. Every score equality class is checked in
full; mixed exact/false top ties are zero. Relative to the portfolio, this is a
three-nucleus gain; relative to the best single marking it is a one-nucleus
gain.

The audit now separates four remaining failures: two are exact-terminal supply
failures and two are supplied-but-misranked. A fully nested ridge-logistic
control does not solve the discrete port alternatives: broad-only execution is
`12 / 20`, and merging the on-policy rows reduces it to `10 / 20`. It is
rejected rather than added as another marking option.

The portfolio terminal corpus digest is
`9625d469f8d6b1e6956cf56690aeb919fe6b465a28374b7f2d61e2067e11ed81`;
the portfolio trace digest is
`56b41e6a3d25223d844260c6c1a011d688f585794be064eb55d9e078bad8c47f`;
the terminal-value trace digest is
`3eb94332bd850eff19b1612ca3d833b15bdcd7044240a5226381731495afee37`.
The exact-selection rate is 80%, still below the committed 90% development
gate, so no new one-shot confirmation is authorized.

The subsequent pruning audit deliberately holds the benchmark gate fixed.
Increasing root proposal reach to 12 makes a correct first action available in
all 20 nuclei, but the unchanged `4 -> 4 -> 8` beam ends with only 17 exact
terminals and selects 13. Independent depth values select 16 with supply 17;
backward descendant-viability labels, propagated only along frozen tree edges,
select 15 with supply 16.

A target-free `12 -> 4 -> 8` lookahead evaluates 7,312 proposals and contains
an exact terminal in all 20 nuclei. This is a supply ceiling, not a value win:
a broad-distribution terminal model selects 12. A canonical feature binding
each symmetry-quotiented pose/port response to its inter-action edge geometry
selects 15, and all five inner folds reject the new edge representation. A
group-heldout action-consensus policy chooses support widths `1 / 1 / 3 / 9 /
5` but selects only 13. None beats the fixed portfolio terminal baseline of
16, so the uncertainty has moved from proposal reach to transferable terminal
valuation. The `18 / 20` confirmation gate remains red and no new target is
opened.

The executor's unordered branch deduplication does not erase whether the same
compatible three-action set could have been assembled in several orders. A
fixed audit counts those parent/order derivations first (maximum `3! = 6`) and
then applies four target-blind terminal rankings. Correct terminals have full
six-order support in `17 / 20` nuclei, but false terminals also have it in
`11 / 20`; both occur in the same `8 / 20`. Multiplicity-first and
score-times-multiplicity fall to `14 / 20` exact selections and `52 / 60`
correct moves. Adding `0.1 log(multiplicity)` only ties the unmodified broad
score at `15 / 20` and `53 / 60`. Order multiplicity is therefore retained as
a truthful visualization of commuting moves, not promoted to a GCTS value
channel.

The next value is a genuine local section rather than another branch-score
transform. A fixed 180-component tensor records species-resolved radial and
pair-angle histograms between the three proposed colored attachments and atoms
already occupied by the search. It is invariant under proper SE(3), contains
no lattice coordinates or absolute origin, and cannot alter the frozen action
geometry. Nested whole-nucleus selection chooses representations
`radial / base+section / base / section / base+radial` with neighbor counts
`1 / 3 / 9 / 15 / 3`. On the same 20 outer nuclei it selects `17 / 20` exact
terminals and `55 / 60` correct moves from `18 / 20` terminal supply, improving
the fixed portfolio by one exact nucleus but remaining below the `18 / 20`
gate. A larger joint-support tensor stays at 17 and loses one correct move;
legacy atom-centred prototype-closure scalars are chosen in zero folds. Only
the compact halo enters the experimental marking library. Because radial and
pair-angle invariants also quotient reflection, this version reports
`chirality_preserved=false`. A separate 30-channel pseudoscalar extension sums
species-labelled ordered neighbor triple products with fixed radial moments.
It is invariant under atom permutation and proper SE(3), changes sign under
reflection, and reports `chirality_preserved=true`. The inner selector chooses
it in two folds, but outer transfer falls to `15 / 20` exact terminals while
remaining at `55 / 60` correct moves. It is therefore exposed only as an
opt-in chiral-material marking; the nonchiral 180-channel halo remains the IQC
default.

The follow-on cluster section removes the atom-centred assumption. Ten
geometry-only nuclei are fitted independently, and exact colored metric-graph
isomorphism retains 53 irregular support classes recurring in at least three
nuclei. Scalar partial completion reaches `17 / 20` exact and `55 / 60`
correct; pair-incidence summaries remain `17 / 20` and fall to `54 / 60`.
An exact typed port graph preserves support identity, shared-species distance
profiles, and symmetry-resolved chirality, but sparse categorical backoffs are
selected in zero folds.

The continuous graph-kernel control therefore compares those same certified
nodes and ports by optimal assignment. Every capacity choice is nested inside
the corresponding outer fold: support-type weights are `0 / .25 / 1`,
node/edge weights are `(1,.5) / (1,1) / (.5,1)`, and neighbor counts are
`1 / 3 / 5 / 9 / 15 / 25`. Inner selection prefers the kernel in folds 1 and
2, showing useful similarity beyond exact graph identity. The sealed aggregate
nevertheless remains `17 / 20` exact and `54 / 60` correct from `18 / 20`
supplied terminals. No target label is available before selection. Continuous
port-graph similarity is therefore retained as an honest research control,
not promoted to the default marking, and the reserved confirmation target
remains unopened.

A bounded message-passing control then transports action chemistry,
partial-support completion, independent-nucleus evidence, shared-interface
chemistry, normalized separation/profile moments, and certified chirality
through the same ports for at most two rounds. It contains no coordinates,
global frame, lattice index, action ID, or target label. The fully nested
selector chooses one round in every fold; inner exact-group counts are
`23 / 25`, `24 / 26`, `22 / 25`, `22 / 26`, and `24 / 25`. It is strictly
preferred over the existing scalar, categorical, and assignment-kernel values
in zero folds. The fixed message encoder is therefore rejected without
changing the `17 / 20` outer result or opening confirmation. A future learned
message map would require its own grouped regularization and shuffled-label
control rather than inheriting credit from this negative.

### Finite-state substitution cycles

Stationarity is not broadened informally to rescue the IQC result. A strict
finite-state alternative permits a period-`p` sequence of exact production
states only after `2p+1` consecutive observations, so every state and directed
transition is seen twice. State identity preserves canonical chemistry,
chirality, proper geometry, directed overlap/boundary ports, and overlap
chemistry. Repeated transitions must have equal independently learned scales
and identical exact population-substitution matrices, and the entire cycle
must recur on heldout or self-fed evidence. A synthetic two-state cycle passes;
short prefixes, shuffled states, chemistry/population mutations, and replayed
rather than independently observed heldout scales fail.

The current IQC hierarchy has four positive levels, while the smallest
nontrivial period-two cycle needs five. Its exact adjacent-state intersections
are `0, 0, 0`, its exact three-level intersections are `0, 0`, and heldout
levels merely re-encode frozen geometry rather than independently observe a
scale. Finite-state recurrence therefore remains red alongside stationary
recurrence.

### Train-only hierarchy selection and semantic controls

`scripts/materials_gcts_hierarchy_selection_environment.py` exposes a bounded
future-RL interface: state is the current exact promoted program plus retained
derivation alternatives; actions choose a train-admitted quotient subset or
derivation policy; reward combines exact cover, MDL saving, and future witnessed
port connectivity. Stationarity is an external gate, never a branch label.

A deterministic width-three beam over a fixed eight-level horizon chooses the
alternative-consistent policy. Relative to the all-representative greedy path,
it changes promoted occurrence retention from
`153 -> 34 -> 10 -> 6 -> 4 -> 2` to
`324 -> 78 -> 26 -> 12 -> 8 -> 4` and improves the fixed-horizon score from
`-63.205` to `-34.592`. It still reaches only six positive levels and produces
no stationary witness. The result is therefore improved hierarchy selection,
not avoidance of evidence exhaustion. This beam is a train-compression
comparator rather than the executable transfer policy; promoted heldout
matching is supplied by the strict-majority re-encoding above.

The guarded semantic-quotient experiment preserves every exact proper-SE(3)
terminal as a replay alternative, but the exact quotient is rejected by the
train-only shuffle and perturbation controls.
Approximate connection grammars are labelled approximate and cannot satisfy the
strict exact-recursion gate.

### Width-eight search and the hardened NaCl relation certificate

Cached partition refinement removes factorial child-order enumeration while
preserving exact permutation and proper-SE(3) invariance. The apparent earlier
negative was an evidence issue: one sparse 216-atom audit finds only six
size-two macros. With two independent bounded presentations and all 29,988
learned relations retained, the search admits child width eight and exports the
`8 children / 24 directed ports / 52 atoms / 2 atom-disjoint occurrences /
MDL 30` production summarized in the crystal section above. Frozen-relation
replay supplies `1,478 / 750 / 86` witnesses over three learned factors and the
strong stationary signature recurs at scale 2.

This does not erase the discovery boundary: the positions-only grid learner
still proposes radix and offsets before the port graph validates them. Pure-
port closure learning remains open, and the IQC stationary result remains red.
