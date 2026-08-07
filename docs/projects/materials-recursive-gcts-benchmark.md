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

## Next implementation target

Generalize the parametric recursive-node interface so crystals learn a
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
