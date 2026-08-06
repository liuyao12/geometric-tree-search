# Hierarchical learning and overlapping GCTS covers for atomic point sets

## Research target

Learn a compressed, multiscale covering grammar directly from a finite colored
point set, then use that grammar to reconstruct a held-out region and continue
growth.  The learner must not receive lattice coordinates, a unit cell, space
group labels, or preferred orientations.

The recurring loop is

```text
colored point objects
  -> rotation-invariant cluster candidates
  -> overlapping-cover GCTS
  -> selected cluster instances as new colored point objects
  -> repeat
```

RL belongs inside the covering stage as a proposal/ranking policy for GCTS
branches.  GCTS owns constraint propagation, geometric compatibility,
backtracking, and the accepted cover.

## Input contract

A level receives only:

- stable object identifiers;
- a species or learned type label for each object;
- a position in three-dimensional Euclidean space;
- optionally, a bounded geometric support attached to a higher-level object.

The only global geometric assumption is a positive minimum separation at each
finite level.  Periodic cells may be used by dataset adapters to extract finite
windows, but they are not part of the learner's input.

Results must be equivariant to translation and proper rotation.  Reflections
are configurable: chemically chiral structures may require them to remain
distinct.

## Cluster candidates

For each possible anchor, construct a bounded neighborhood by a radius or a
closed nearest-neighbor shell.  Compare neighborhoods using species-preserving
distance graphs, with distance and angle descriptors used as a fast index.

A learned cluster type contains:

- a canonical rotation-invariant signature;
- one representative relative geometry;
- a set of observed occurrences and fitted rigid transforms;
- an interface consisting of exposed objects and bounded GCTS marks;
- a description cost.

Candidate learning intentionally over-generates.  Selection belongs to the
covering objective.

## Overlapping cover problem

Let `U` be the objects at the current level and `P` the candidate cluster
occurrences.  Each occurrence `p` covers a subset `S_p` of `U`.  Choose
occurrences `X` such that every required object is covered:

```text
for every u in U: sum(x_p for p with u in S_p) >= 1
```

Unlike exact cover, the inequality permits shared atoms or child clusters.
Pairwise and higher-order compatibility constraints encode whether two
occurrences agree on shared species, relative geometry, chirality, and marked
interfaces.

The first objective is a transparent minimum-description-length surrogate:

```text
dictionary cost
+ sum(placement costs)
+ overlap redundancy penalty
+ uncovered-object penalty
+ geometric/species inconsistency penalty
```

The initial finite solver uses branch-and-bound.  It branches on the most
constrained uncovered object, propagates forced placements and conflicts, and
memoizes equivalent marked boundary states.  Greedy selection is retained as a
baseline, not as the reference algorithm.

## Coarse graining

After selecting a cover, turn every selected occurrence into a new object.
Its position is a deterministic center (initially the centroid), its color is
the learned cluster type, and its support records the child identifiers.  Run
the same candidate learner and cover solver on these objects.

Stop adding levels when held-out description length no longer improves.  This
stopping rule is part of the amorphous null hypothesis: recurring local motifs
need not imply a useful recursive grammar.

## RL-GCTS interface

At a GCTS state, the environment enumerates legal or not-yet-refuted candidate
placements.  The policy may rank:

1. the uncovered pivot object;
2. candidate occurrences covering that pivot;
3. search nodes awaiting expansion;
4. learned macro-occurrences at higher hierarchy levels.

The transition remains a GCTS transition.  Reward is measured at matched cover
quality and includes reductions in expanded nodes and runtime.  Direct RL that
places unconstrained patches is an explicit ablation.

## First benchmark ladder

### A. Rotation and non-lattice invariance

Generate a finite, irregularly positioned set of planted overlapping motifs.
Apply an arbitrary proper rotation and translation.  Require identical cluster
types and occurrence incidence, up to object identifiers.

### B. Overlap is necessary

Use planted motifs that share boundary objects so that no disjoint partition
can express the ground truth.  Compare greedy selection with branch-and-bound
GCTS on cover cost, completeness, and expanded nodes.

### C. Crystalline positive control

Use a finite spherical binary crystal window.  The hierarchy should recover
large translational macro-clusters.  Translation is expected to match or beat
GCTS after the rule is learned.

### D. Locally ambiguous stacking

Use binary tetrahedral zincblende/wurtzite-style stacking, multiple nuclei, and
confined windows.  Small clusters are locally compatible with competing
continuations.  Test whether marked GCTS resolves these choices and whether RL
reduces the resulting search tree.

### E. Three-dimensional quasicrystal

Use a decorated icosahedral model set with a hidden radial annulus.  Measure
whether successive levels find non-translational reusable superclusters and
improve held-out reconstruction.

### F. Amorphous nulls

Compare a minimum-distance random point set, a point set with planted local
motifs but no higher-order grammar, and realistic glass snapshots.  A valid
method must stop deepening the hierarchy when predictive compression saturates.

## Required ablations

- partition versus overlapping cover;
- greedy versus unguided GCTS;
- direct RL versus RL-guided GCTS;
- unmarked versus bounded GCTS markings;
- flat versus hierarchical dictionaries;
- learned versus supplied translations or inflation rules.

## Primary measurements

- held-out atom/species recovery under a distance tolerance;
- cover completeness and overlap consistency;
- total description length and compression by hierarchy level;
- expanded nodes, backtracks, and wall time;
- represented atoms per accepted macro-action;
- RDF, coordination, species-pair correlations, and structure factor;
- stability under arbitrary rotations, translations, and bounded noise.

The main speed claim is always reported at matched reconstruction and cover
quality:

```text
speedup = nodes expanded by unguided GCTS
          / nodes expanded by RL-guided GCTS
```

## Immediate milestone

The first runnable milestone joins three small, independently tested modules:

1. a lattice-agnostic rotation-invariant candidate learner;
2. a generic overlapping-cover GCTS solver with a greedy baseline;
3. deterministic crystal, irregular planted-motif, and amorphous point-set
   generators with radial train/validation splits.

Only after this interface works do we add hierarchy recursion and RL ranking.
That order prevents an RL policy from hiding errors in cluster discovery or
cover semantics.

## First search-guidance milestone

The first exact-cover guidance experiment uses finite rotated binary-crystal
windows learned through the same point-set API.  The 33-atom crop is the
teacher problem; the 123-atom crop is held out for transfer.

The GCTS kernel now represents supports, coverage, compatibility, exclusions,
and frontier marks as integer bitsets.  Its canonical memo key is the pair
`(uncovered objects, viable occurrences)`.  Branch partitioning assigns every
completion to one earliest selected pivot option, avoiding duplicate histories.
Both mechanisms are exact and independently ablatable.

A linear policy observes only cover-state features: candidate gain and cost,
overlap, domain scarcity, near-forcing, peer compatibility, progress, and
incumbent slack.  An exact teacher search on the 33-atom problem supplies
pairwise imitation labels.  Coordinates, lattice indices, and the 123-atom
solution are not training inputs.

At a matched 100-node budget on the 123-atom problem, unguided search retains a
14-cluster incumbent while the transferred ranking policy finds 13.  Frontier
memoization independently finds 13 at this budget; combining policy and memo
does not yet improve the incumbent further.  None of these bounded 123-atom
runs certifies optimality, so 13 is reported as an incumbent rather than an
optimum.

Bitset search raises throughput from roughly 500 to 9,000--12,000 expanded
nodes per second on this problem.  Frontier memoization reduces the certified
33-atom proof from 58 to 44 expanded nodes.  A dynamic disjoint-domain packing
bound is exact and tested, but has not yet made the 123-atom proof tractable.
Dynamic support-dominance pruning was tested and rejected because its runtime
cost greatly exceeded its pruning benefit.

This result establishes the intended RL boundary: the policy changes only the
order of GCTS branches, improves a held-out incumbent under a fixed search
budget, and cannot change legality or falsely claim optimality.  The next step
is to learn from descendant search effort or value targets across a diverse
family of covers rather than imitate one small crystalline optimum.

## Cross-family policy selection

The next curriculum contains three abstract cover families: learned clusters
from independently rotated crystal crops, fragment alternatives from
non-lattice corner-sharing motif networks, and covers with delayed pairwise
conflicts.  After construction, every case discards coordinates, rotations,
species, and any lattice metadata.  Six cases train the policies, three select
between them, and six remain untouched for evaluation.

An observational GCTS trace now reports every non-forced branch and candidate
subtree: descendant node count, whether a complete cover was encountered,
incumbent improvement, interruption state, and the best objective actually
found in that subtree.  Trace callbacks cannot alter branch order or solver
state.  Interrupted searches are never labeled infeasible.

Two linear policies are compared:

1. final-solution imitation, which ranks candidates appearing in a certified
   teacher solution;
2. descendant-value ranking, which combines subtree completion, incumbent
   improvement, and descendant search effort.

Both reduce validation search from 35 to 33 total expanded nodes.  The
predeclared conservative tie-break selects final-solution imitation.  It
matches unguided node counts and exact optima on all six untouched small test
cases, and on the separate 123-atom transfer finds the 13-cluster incumbent in
50 expansions where unguided GCTS retains 14.

The descendant-value target is not promoted: although it ties the selected
policy on the six small test cases, it retains a 17-cluster incumbent on the
123-atom transfer at both 50 and 100 expansions.  This failure is kept as an
explicit ablation.  The current scalar descendant reward is therefore an
environment baseline, not evidence that value learning already generalizes.
Future work should distinguish subtrees proven infeasible from those merely
pruned by an incumbent and should train on counterfactual branch rollouts.
