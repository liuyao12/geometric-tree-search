# GCTS + RL renewal

Fresh research beginning October 8, 2026. The turtle learner imports only the
vertices and angle units of the article. It starts with no marking, zero policy
weights, no saved model, no known tiling, and no supplied substitution. Historical
experiments elsewhere in the repository are comparison context only.

The report is at [the existing GitHub Pages destination](https://liuyao12.github.io/geometric-tree-search/docs/research/gcts-rl-renewal/).

Run a cold iteration and the semantic conformance checks:

```sh
python3 research/gcts-rl-renewal/run.py
python3 research/gcts-rl-renewal/run_spatial.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py' -v
python3 research/gcts-rl-renewal/audit_geometry.py
python3 research/gcts-rl-renewal/audit_spatial.py
python3 research/gcts-rl-renewal/probe_halo.py --deepen-unresolved
python3 research/gcts-rl-renewal/validate_halo.py
```

The runner is standard-library only, with Python 3.10 or newer recommended.
Each cold turtle runner recomputes the complete pair catalog, verifies failure certificates,
synthesizes a marking, trains policies, mines inspectable sequences from its own
searched patches, evaluates on disjoint seeds, and runs two limited inflation
controls. Checkpoints are written after completed stages. Training and solver
construction costs are included in the report. Saved JSON is inspection evidence;
the cold runners never read it as a starting model or as a tiling witness.

Evaluation uses several fixed pair starts, with identical starts in all lanes.
Policy training and donor search start from one tile; their random seeds are
disjoint. Evaluation pairs may appear as subpatches of donor trajectories, so
this does not claim strict patch-disjoint policy generalization. GCTS uses every
resolved pair label, as required by the shared learning contract.

## Goals and success criteria

1. **Exact unmarked turtle baseline.** Complete candidate incidence; global
   dead ends and forced propagation before generation-first branching; exact
   occupancy, marking comparison, rollback, and independent witness replay.
2. **Geometric failure encoding.** Every negative has a complete replayable
   exhaustion certificate. Learn point-value agreement data from all resolved
   contacts. Give the support and symmetry assumptions of any redundancy claim.
   Extended-support restrictions stay hypotheses until mark-only contacts are
   covered by an additional proof.
3. **RL sequences.** Learn irregular cluster proposals, expose all constituent
   placements, validate them, obey the scheduler during execution, retain every
   base move, and evaluate on disjoint seeds with construction costs reported.
4. **Substitution discovery.** Infer several metatile types from patches, propose
   exact expansion maps, and export rules as lists of base placements. Repeated
   motifs alone do not pass. Check coverage, interfaces, and at least three
   recursion levels before calling a rule an experimental substitution.
5. **Plane construction, if attainable.** An exact substitution needs compatible
   collars and an expanding nested construction or an equivalent coverage proof.
   Finite growth, a visually plausible patch, and a spectral radius alone do not
   pass. Aperiodicity is a further independent assertion.
6. **Penrose over \(\mathbb Z[\zeta_5]\).** Exact rank-four arithmetic first.
   Declare a faithful point model and admissible translations before transferring
   the learner; the physical module is dense, so polygon interiors cannot simply
   be represented by finitely many lattice samples. No supplied arrows or rule
   may enter the discovery lane. Unmarked rhombs also permit periodic tilings;
   finding a Penrose-compatible subsystem is not redundant pruning of all rhomb
   tilings.
7. **Checkable computational proof search.** Embed Wang edge agreement as point
   markings. Establish finite accepting computation certificates for a general
   transition compiler. Next connect a trusted, total proof checker for an
   explicitly chosen recursively axiomatized theory, enumerate proof programs,
   and search accepting rectangles. Turing completeness is expressiveness, not
   a guarantee of deciding every statement or terminating on unprovable inputs.

## Conformance evidence and gaps

The domain is \(A_2=\{(x,y,z)\in\mathbb Z^3:x+y+z=0\}\), with twelve signed
coordinate permutations and integer capacity \(12\). A tile has 28 positive
point values; the only geometric calculation authors those values by an exact
rational polygon membership test. Search does not add polygon intersection
checks. Faithfulness to conventional polygon tilings has not been independently
proved. Distinct orientations remain distinct inventory identities.

`Graph` maintains forward and reverse shared incidence. All positive support
alignments are enumerated. Dependency changes at occupancy and marking-only
points update every incident domain while preserving unaffected domains.
`State.copy` and `Graph.copy` restore all semantic branch data exactly. Interned
placements are immutable, append-only caches; they contain no branch exclusions.
Rules are frozen within a run; a new rule creates a new model and replays seeds.

The tests compare incremental domains with independent enumeration, check
zero-valued obligations, shared fractional candidates, remote marking-only
disagreements including assigned zero, generation precedence, exact snapshots,
symmetry closure, independently checked failure proofs, budget-as-unknown, and
rejected tampered computation certificates. The catalog proof trees use the
independent enumerator at every node; positive witnesses use an independent
integer replay and frontier viability check.

Growth activates newly occupied support, but does not yet activate a fair
exhaustion of all untouched points. Results are consistent finite point patches,
never plane tilings. Sequence and spatial proposals have bounded lengths, with
base fallback preserving the complete search universe. Spatial proposals may
rotate and reflect; their schedulable prefixes are planned on graph snapshots.
The original sequence runner retains its unchanged default proposal path.
Hierarchical grouping now exports three disjoint finite partition levels with
exact interfaces, but higher-level types are only observed parent shapes.
Stationary recursive productions and expanding coverage remain open.
Finite inflation controls declare fixed exterior point contributions and a
single-shape integer dilation, so their failures do not rule out a metatile
substitution. Memory is process peak resident memory, not per-lane allocation.

## Soundness boundary for the smallest marking

The complete rooted contact catalog contains every legal pair with shared
positive occupancy. All twelve orientations are closed under composition and
inverse. The marking is scalar under that action and its assigned support is a
subset of the positive occupancy support. Independent checks establish that
every rejected contact belongs to the certified negative set, including all
transformed contacts.

Suppose a complete unmarked point-model tiling had disagreeing marking values.
The two tiles carrying those values share positive occupancy and can be moved
to a catalog representative. Its negative proof tree exhausts every possible
continuation, yet the complete tiling supplies a legal continuation at every
frontier decision, contradicting a dead leaf. Thus every complete unmarked
point-model tiling satisfies the smallest marking. This is a redundancy lemma,
not an existence proof and not a claim that every legal finite prefix survives.

## Second iteration: spatial proposals and proof certificates

The second runner recomputes and independently checks all original contact
labels; it never loads the first snapshot. Six new donor searches reach 64 tiles.
Enumerating connected subsets of size two through four gives 18,752 occurrences,
1,680 exact shape types after symmetry and translation, and 1,422 types occurring
in at least two donors. Eight recurrent types enter the frozen proposal library.
Twenty-four REINFORCE episodes execute 25 extra continuation moves. Training and
donor trajectories do not include evaluation trajectories, although local shapes
can overlap. Every legal base candidate is retained.

At a target of 64 tiles, with three fixed evaluation pairs, 2,000 nodes and
12 seconds per lane, GCTS reaches one start and the other lanes reach none.
Two GCTS starts exhaust below the target; positive one-corona labels did not
promise longer extension. RL often returns unknown at the budget. Spatial RL
has not demonstrated an acceleration. Do not compare this target directly with
the first experiment's 32-tile target as a change in performance.

The successful GCTS patch partitions into 42, 24, and 14 groups at the three
inspection levels. `audit_spatial.py` independently reconstructs every aggregate
from base point values, checks all child maps and disjoint expansions, rejects
tampered interfaces and repeated children, and runs the separate rational
polygon audit. This is finite evidence, not a discovered substitution.

`logic.py` is a certificate kernel for classical first-order logic with equality.
It validates immutable syntax, closed registered theory axioms, propositional
tautologies, hygienic universal instantiation, quantifier distribution with its
free-variable condition, equality substitution, modus ponens, and generalization.
No open theory assumptions are accepted. Existential quantification may be
defined through negation and universal quantification. The example discovers
\(S(0)+S(0)=S(S(0))\) with two rewrites and emits 15 checked Hilbert lines. The
search proposer is bounded forward ground-equation rewriting, not a complete
first-order proof search. Infinite theories need checked axiom schemas or
enumeration witnesses; the implementation is not a formally verified kernel.

The separate Wang experiment leaves two input symbols unknown and finds the
unary certificate for \(1+1=2\). Its verifier works for arbitrary finite unary
addition inputs. Complete cell domains use exact bitsets of all 5,684 tile types,
with global dead/forced scheduling and all root generations zero. Only placed
edge markings shrink adjacent domains; snapshots restore domains and selections.
The found rectangle has 11 columns and 32 transition rows. Operational TM replay,
independent point checking, arithmetic counting, and input tamper rejection pass.
This machine is not yet a compiler for `logic.py` proofs. A universal proof
search still needs that explicit bridge and fair unbounded certificate/rectangle
enumeration. No claim of a general theorem-prover implementation is made.

`probe_halo.py` is a separately labeled reused-data control. It resynthesizes
the radius-one hypothesis from the second run's labels and enumerates additional
mark-only disagreements, then labels those pairs by unmarked search. It never
activates the hypothesis. All 976 additional disagreeing contacts exhaust; one
needs the declared larger node/time budget. `validate_halo.py` independently
checks every canonical excluded contact, including the 236 excluded original
contacts. Every possible disagreement is an alignment of two assigned marking
points; this finite alignment enumeration covers exterior-only interactions.
Scalar equivariance checks transfer the exclusions through all twelve symmetries.
Together with the complete negative proof trees, this establishes the same
conditional redundancy lemma for the radius-one marking: every complete
unmarked point-model tiling satisfies it. It is not an existence proof, and the
larger marking was not used in the second iteration's benchmarks.

Dead leaves of this validator re-enumerate the stated empty frontier point;
internal nodes re-enumerate the entire frontier, certify global scheduler order,
and check every alternative. This preserves the inference while avoiding work
at unrelated points in a dead leaf. Additional tests compare its domains and
checked trees with the original exhaustive checker, and reject omitted branches
or fabricated dead points. The original runner's verification path is unchanged.

## Third iteration: context, structural descriptors, and core coverage

`run_continuations.py` explicitly reuses the compact marking from iteration 02
and the independently certified radius-one marking. It checks artifact and
engine provenance and records historical construction/replay costs. It imports
no saved policy, motif, patch witness, human marking or substitution. New donor
and policy seeds are disjoint from evaluation seeds. This is a reused-model
study; it must never be presented as a third cold start.

`spatial_context.py` treats already selected placement identities as context.
It validates the summed occupancy and marking union of NEW constituents, then
checks the actual global scheduler at each executed constituent. A declared
validation budget bounds only the macro proposal pool; all legal singleton
candidates remain. Structural checks are cached per exact relative expansion
and marking version. Proposal and validation costs are reported.

`diverse_motifs.py` bins candidate motifs by size and handedness balance,
invariant under the complete declared lattice group. Every bin is eligible;
no named metatile family is supplied. The fresh donors yield fourteen selected
types, including eight mixed-handed types. The frequency control has eight.
`boundary_grammar.py` derives exact boundary direction cycles and convex hull
words from already checked finite clusters. Polygon descriptors never decide
base legality. Removing lengths defines an abstract class, not an exact shape.
Greedy finite grouping under both rules found no class with three distinct
growing base-tile counts. This is a failed structural hypothesis, not a
substitution discovery or an impossibility theorem about substitutions.

`coverage.py` activates the complete nested cores
\(Q_r=\{(x,y,z)\in A_2:\max(|x|,|y|,|z|)\le r\}\), including untouched
zeros as generation-zero roots. Later cores activate in child transactions,
with the earlier search stack retained. Later failure can restore and change
earlier checkpoint placements. All twelve matched runs through radii
\(0,4,8,12\) filled the final core's 469 points. Exposed exterior obligations
are still incomplete. This is a finite prefix of a fair activation scheme;
there is no certified infinite continuation or continuous plane coverage.

The tile-count evaluation asks for 128 tiles, with three single-root starts,
10,000 nodes and 15 seconds. `repeat_evaluation.py` replaces its original timing
pass because that pass overlapped other research processes. Both measurements
and the added cost remain in the artifact. Repeated searches reset models,
caches and seeded proposers while retaining the same frozen trained policy.
They run sequentially. No stable GCTS or RL acceleration is established here.
These targets differ from iterations 01 and 02 and cannot support a direct
cross-iteration timing claim.

`audit_continuations.py` independently sums all motif and hierarchy interfaces,
checks unique base partitions and child relations, verifies each successful
core point, re-enumerates all exposed checkpoint domains, and checks the final
and donor polygons by exact rational clipping. `replay_proofs.py` replays the
exported logic and Wang certificates from JSON. The theory is declared outside
the proof, so a certificate cannot nominate a new trusted axiom. The actual
first-order-kernel-to-machine compiler remains open.

```sh
python3 research/gcts-rl-renewal/run_continuations.py
python3 research/gcts-rl-renewal/repeat_evaluation.py
python3 research/gcts-rl-renewal/audit_continuations.py
python3 research/gcts-rl-renewal/replay_proofs.py
```

The repeat is only needed to reproduce the recorded correction; an ordinary
rerun of the complete pipeline should run without simultaneous research jobs.

## Penrose pilot: a declared connected vertex-star point problem

`penrose_sectors.py` uses
\(L=\mathbb Z[\zeta_5]\times\{0,\ldots,9\}\). Each rhomb occupies its
angular sectors at its four vertices with \(t=1\), ten positive slots total.
Each placed vertex activates all ten slots, including zeros. Every generated
slot is explicitly a generation-zero root; after the seed, connected tile
generations are therefore one. This convention is explicit and follows the
root rule, although it does not measure expanding spatial layers.

The ten allowed rotations use \(\eta=-\zeta_5^3\), with the action
\((v,s)\mapsto(\eta^r v+a,s+r\bmod 10)\). Markings are scalar values under
that action. A transformed placement identity is `(kind, rotation, translation)`
and can be selected once. Geometrically identical orientation aliases remain
distinct inventory identities. Their positive supports prevent simultaneous
selection. Reflected unmarked rhomb outlines are represented by rotations;
there is no additional reflection action on future decorations in this pilot.

Candidate domains enumerate both tile kinds, every rotation, and every positive
support alignment. The graph stores forward/reverse incidence and complete
occupancy/mark dependencies. Global dead ends precede global forced moves;
earliest-generation branching uses initial-core priority only to break a
generation tie, then degree and exact keys. Child snapshots restore active
zero obligations, roots, generations, inventory, values and the full graph.
Polygon tests never participate in candidate generation or legality.

`run_penrose.py` starts unmarked and tests all 160 capacity-legal contacts for
each root kind. All 320 complete their initial vertex stars with a viable
exposed frontier; all pass independent point replay. Exact algebraic polygon
tests found no overlaps among 39,467 tile pairs in those finite witnesses.
The learner uses every resolved label and permits markings at all eighty
prototype slots, including zero occupancy. With no negative labels, the
positive equalities merge all slots into one class, and sparsification leaves
all slots free. No nontrivial failure marking is discovered. Identical baseline
and empty-marking growth controls confirm this; they are not evidence of a
GCTS acceleration or of Penrose aperiodicity.

The physical module is dense. A disconnected control with displacement
\(\varphi^{-1}\) has disjoint vertex supports and positive-area polygon overlap,
certified by integer comparisons in \(\mathbb Q(\sqrt5)\). For any finite
support, infinitely many distinct small translations eventually avoid its
finite difference set; thus unrestricted finite-support capacity cannot equal
geometric non-overlap. Search instead grows a vertex-connected component and
completes generated stars. A complete developed-complex to plane-tiling
equivalence still needs proof. It does not activate every point of the dense
module. It also does not characterize the hierarchical Penrose subset of
unmarked rhomb tilings. These are explicit remaining model and discovery gaps.

```sh
python3 research/gcts-rl-renewal/run_penrose.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py' -v
```

Semantic checks cover all rotations, zero activation, exact algebraic signs,
shared candidate incidence, incremental/exhaustive equality, rollback, global
scheduler precedence, marking-only dependencies including assigned zero,
independent positive and negative certificates, and fabricated dead-leaf
rejection. The deliberately restrictive test marking is a control only and
never enters discovery.

## Next research iteration

Fit the spatial types into a multi-type grammar with exact coordinate transforms,
stationary productions and repeatable interfaces. Penalize boundary mismatch and
uncovered obligations. Search
inflation matrices without providing a known scalar, and try hierarchical
composition; preserve single-tile fallback. Certify exclusions of larger motifs
before adding further marking channels. For Penrose, close the developed-complex
gap and learn hierarchical proposals beyond pair-star samples. For logic,
compile an actual proof checker before comparing
learned policies with conventional proof enumeration.
