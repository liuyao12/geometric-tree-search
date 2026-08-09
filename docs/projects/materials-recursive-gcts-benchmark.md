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
connection states, 171 accepted) and then frozen:

| held-out consensus | proposed sites | correct | precision | target coverage |
|---|---:|---:|---:|---:|
| at least 1 overlapping action | 57,899 | 8,363 | 14.4% | **97.2%** |
| at least 2 | 37,475 | 7,883 | 21.0% | **91.6%** |
| at least 4 | 17,315 | 5,523 | 31.9% | 64.2% |
| at least 8 | 4,395 | 2,769 | **63.0%** | 32.2% |
| at least 16 | 837 | 665 | 79.5% | 7.7% |
| at least 32 | 12 | 12 | **100%** | 0.14% |

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
four folds and applied only to the excluded parents.  The resulting 4,339
out-of-fold proposals contain 1,969 positives and 2,370 genuine negative
examples.  The second-order marking is fitted there, frozen, and applied to
68,019 proposals on the 1,969→8,603 transition.

The atom-growth factor learned from the training transition is 3.8836, which
predicts a next-level budget of 7,647 sites without inspecting the 8,603-site
target.  At fixed multiples of that budget, the second-order marking causally
improves multiplicity-only ranking:

| next-level site budget | selected second-order policy | second-order P / R | vote-only P / R |
|---:|---|---:|---:|
| 3,824 (0.5×) | continuous section | **75.63% / 33.62%** | 67.49% / 30.00% |
| 7,647 (1×) | finite binned section | **54.87% / 48.77%** | 52.87% / 47.00% |
| 15,294 (2×) | finite binned section | **37.79% / 67.19%** | 34.75% / 61.78% |

This is the first leakage-controlled gain from an explicit cluster of
connection proposals rather than from raw overlap multiplicity.  It is not a
G1 pass.  Absolute score thresholds calibrated on 507→1,969 transfer poorly
because candidate density and class prevalence change sharply at the next
level.  The current recursively stable policy therefore ranks the atom budget
predicted by the learned growth factor.  The next marking must model that
density transformation explicitly or learn a higher-order sparse cover so an
absolute forced-move decision remains calibrated across levels.

## Next implementation target

Learn the transformation of proposal density and class prevalence between
hierarchy levels, or replace dense pair proposals with a learned sparse parent
cover.  Generalize the parametric recursive-node interface so crystals learn a
translation quotient, substitution quasicrystals learn an inflation or
superspace section, and amorphous controls decline the deterministic rule.  Add
held-out perturbations and non-icosahedral model sets so a module-specific
success cannot masquerade as generic GCTS.  The generic G1 gate remains 95%
hidden recall with exact species and position validation.

## Generic parametric dispatcher and million-atom curve

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
