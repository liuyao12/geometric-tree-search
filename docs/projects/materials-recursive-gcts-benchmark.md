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
five macro actions (12.9 seconds in the recorded Python run). The learned
507-atom IQC section streams 2,791,097 positions in six actions (4.0 seconds).
Neither output cloud is retained. Instead, an order-independent 256-bit sum of
per-site cryptographic hashes is compared with a structurally independent
oracle: direct rocksalt half-grid parity for NaCl, and the sealed unit/window/
shell constants for the IQC. Both digests and species counts match exactly.
The observed geometric means are 8.000 and 4.202 sites per recursive action.
This closes the **explicit million-site emission** benchmark for the two ideal
systems while preserving the crucial distinction: writing coordinates is
O(N), and the generic locally learned cover grammar remains red.

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

From 93 seed-interior parents, 25 of 444 observed metric port classes pass the
train-only support/purity rule. Frozen on the 1,969-site frontier, they admit
5,052 connection actions whose overlaps collapse to 380 distinct novel sites.
All 380 are present in the 8,603-site held-out target: 100% precision, 5.73%
recall, and two or three independent votes per site. The matched coarse-state
ablation proposes 3,404 sites with 500 true (14.69% precision), so metric ports
give a 6.81x precision gain. This gate is green for exact transferred port
execution, while recursive full-growth recall remains red.

The executor now inserts the 380 predicted species labels, recomputes motif
types on the resulting 2,349-site partial cloud, and reapplies the same frozen
atlas. No oracle species or positions are inserted. Wave 2 exposes 3,960 novel
one-port candidates but none has the two independent overlaps required for
acceptance, so growth stalls. This is a sharper red regenerative gate: metric
ports transfer and execute, but the first action does not reconstruct the
higher-order port-incidence state needed by the next action. The next learned
supercluster must carry that incidence graph as part of its production.

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
