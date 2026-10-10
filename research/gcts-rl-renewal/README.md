# GCTS + RL renewal

Fresh research beginning October 8, 2026. The turtle learner imports only the
vertices and angle units of the article. It starts with no marking, zero policy
weights, no saved model, no known tiling, and no supplied substitution. Historical
experiments elsewhere in the repository are comparison context only.

The user revised the program after the first pilots: a turtle substitution is
optional. The practical goal is exact tiling of regions with fixed or explicitly
movable boundaries, and compatible growth toward the plane. Clusters become
tiles with their own markings at successive levels. Local boundary solutions
and multiscale assembly are the central next experiments.

The report is at [the existing GitHub Pages destination](https://liuyao12.github.io/geometric-tree-search/docs/research/gcts-rl-renewal/).

The [separate Wang-style proof notebook](https://liuyao12.github.io/geometric-tree-search/docs/research/gcts-rl-renewal/wang-proofs.html)
lists concrete proofs discovered by the current direct point-tile searches.
Its reader supports compact root certificates, every local lemma definition,
and complete independently checked primitive root expansions, with clickable
earlier-line references and exact certificate downloads. Each line also has
a mechanical English reading and a separate inference-rule explanation;
nested brackets preserve logical scope. The English is a reading aid, not
an independently checked natural-language proof. Current examples are
bounded contextual arithmetic. Separate notebooks now contain searched induction proofs and a finite Euclidean congruence experiment.

The tile view reconstructs all 29 selected placements for those ten proofs from
the independently audited point types. Square bodies draw discrete capacity
points; formula circles and outer ownership squares draw the actual m-values.
The isolated view exposes distant formula markings with no occupancy there.
Compact proof-line links bind exact accepted certificate hashes. This is a
positional finite generalized Wang encoding, not a uniform four-edge inventory.
The viewer adds no rules, search results, or new measured engine behavior.
Its tile-row translation follows actual premise ports in logical cell order.
Each cell displays the formula encoded by its port and explains the precise
changed subexpression by matching it to the named equality axiom. Cluster view
combines internal cells into one readable step. Universal closing inferences
are shown separately from the occupied cells. Forty-four cells and thirty-four
rewrites are checked; mutation controls reject altered ports, reasons, axiom
instances and targets. The equation chain introduces no additional arithmetic inference.
A complete equation chain and a short mathematical argument now sit directly
below the tile diagram. The cell labels tie each equality to its actual tile;
the detail selector also reads an entire searched cluster as one step.
The cluster chain retains the original starting expression when the first
cluster contains more than the reflexivity cell.

Notebook 33 adds a complete inventory of searched metatiles and an explicit
coarse point model. A group of one, two or three slots has capacity twelve;
covering one member contributes twelve divided by group size. Distinct
candidate identities are m-values at each owned primitive slot, preventing
overlapping expansions. All logical ports, including internal ones, remain.
Exact capacity plus ownership gives solution equivalence to the original
finite envelope; every original solution lifts through the complete primitive
fallback. This does not assert primitive scheduler-path equivalence. It is
a separately declared positional representation with identity transforms.

The point graph retains complete incidence, global dead/forced precedence,
earliest generations, fractional residuals and exact rollback. Atomic
metatiles are justified by the explicit finite solution-equivalence argument,
not by sampled proposal degrees. The macro inventory must be complete.
The classical comparison uses binary arc consistency and MRV on the original
primitive variables, with independently checked unsupported-value deletions.
Both trial caps are 50000 but count different units: expanded point placements
versus explicit classical assignments. All propagation, representation and
trace-instrumentation work lies inside the five-second search wall. Cold
cost includes catalog checking, proof expansion, hierarchy and native checking;
reuse lanes additionally owe fresh donor/library discovery.

Reproduce the current fresh experiment and its separate proof reader:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_coarse_proofs.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_coarse_proofs.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_coarse_proof_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_coarse_proof_view.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/export_wang_proof_notebook.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/export_wang_tile_view.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/test_wang_tile_view.py
```

The producer begins with an empty library and searches both donor statements
again. It never imports previous proof/cluster/policy artifacts. Evaluation
does not enter mining. Sources are SHA-pinned before execution. The independent
auditor reconstructs every full decided point graph, every classical revision,
all closed or open tree prefixes, full primitive and hierarchical proofs,
library provenance and native input/program bindings. It imports no graph,
search, miner or catalog producer. Universal compiler soundness and independent
native-instruction replay remain outside its scope. Historical notebooks and
their measured sources/artifacts remain byte-preserved.

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
4. **Marked cluster tiles at multiple scales.** Promote local solutions into
   real aggregate types with exact expansions, inherited interfaces and new
   level-specific marking channels. Learn how those types assemble at the next
   level. A stationary substitution is an optional route, not a completion gate.
5. **Practical region solving and plane coverage.** Benchmark fixed boundaries,
   explicitly movable boundary variables and growing nested cores, counting
   learning/reuse cost, memory and independently verified covered obligations.
   A plane construction needs a compatible unbounded continuation or coverage
   invariant. Finite growth alone does not pass; aperiodicity is a separate goal.
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
checks. Faithfulness was open in the initial milestone. Notebook 22 below now
gives a written polygon/cell-region theorem with independently checked finite
hypotheses for this declared inventory. Distinct orientations remain distinct
inventory identities.

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
completes generated stars. At this pilot's publication, a developed-complex
to plane-tiling equivalence was still open. The analytic theorem below now
addresses it for a connected assignment with every generated star saturated.
This does not activate every point of the dense module or characterize the
hierarchical Penrose subset. The historical finite witnesses do not satisfy
full saturation; compatible infinite continuation remains open.

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

## Continuing research

Fit the spatial types into a multi-type grammar with exact coordinate transforms,
stationary productions and repeatable interfaces. Penalize boundary mismatch and
uncovered obligations. Search
inflation matrices without providing a known scalar, and try hierarchical
composition; preserve single-tile fallback. Certify exclusions of larger motifs
before adding further marking channels. For Penrose, construct compatible
unbounded saturation and learn hierarchical proposals beyond local star samples. The computational
proof pilot below implements a generic checker. For mathematical logic, the
remaining bridge is an explicit translation of the first-order kernel and
checked theory schemas, followed by harder benchmarks.

## Generic computational proof system: word rules, compiled checker, RL

`rewrite_machine.py` defines a formal proof relation over arbitrary finite
alphabets and directed word rules. An assertion is \(u\Rightarrow_R^*v\);
its certificate is a sequence of rule indices and substring positions.
`check_derivation` checks those operations independently of any TM or tiling
code. The theory and target are supplied externally, never registered by a
certificate. Empty left or right sides permit insertion and deletion.

`ProofMachine` compiles the declared theory and target into literal finite TM
transitions. Its fixed-capacity input word buffer is followed by unknown proof
bytes. Unary positions, rule tokens and terminators are checked; malformed
proofs and buffer overflow reject. The same generated machine works at every
capacity. An explicit padding token permits larger proof-length bounds without
inventing extra proof steps. Successful checking erases the work tape, returns
to a fixed marker and enters an absorbing accepting state. The independent
word semantics, operational TM replay and Wang point replay all check found
certificates. The compiler has semantic tests, not a machine-checked general
correctness proof.

`tm_theory` makes the computational expressiveness explicit. A well-formed
configuration is \(L\alpha q a\beta R\), with disjoint symbol namespaces and
one state marker. A right transition \(\delta(q,a)=(p,b,+1)\) gives
\(qac\to bpc\) for each tape letter \(c\), and \(qaR\to bpBR\) at the
border. Left moves give \(cqa\to pcb\) and \(Lqa\to LpBb\); stationary
moves give \(qa\to pb\). Here \(B\) is the declared blank symbol. Every
non-halting reachable word remains a configuration, and its sole possible
rewrite is exactly the machine's transition. Border rules extend blank tape.
Only the halt state can erase its adjacent tape symbols, then apply
\(Lq_{\rm halt}R\to\mathtt{ACCEPT}\). Thus target reachability is equivalent
to arbitrary machine acceptance. This is an implemented version of the
classical [Post construction](https://wolframscience.com/prizes/tm23/images/Post2.pdf),
not a new universality theorem. It establishes expressiveness of the formal
relation; it does not yet compile our separate Hilbert kernel or all mathematical
theories to word rules.

`lazy_wang.py` avoids materializing millions of types. Every allowed local triple
has zero heads, a center head, a left head, or a right head. Four disjoint
Cartesian blocks represent and count the complete inventory exactly. A candidate
identity consists of its center and triple; its reverse occupancy incidence is
exactly that center. Domains restrict these blocks only by declared boundary
conditions and assigned point markings. All rectangle centers are explicit
generation-zero roots, and all placed tiles have generation one. Global dead
ends precede global forced moves; branching ties use row then column within the
common earliest generation. Iterative DFS retains every alternative. Trail
rollback restores selections, marks, complete domains, order and generations.
Independent checks use direct operational transitions and exact point values,
never symbolic domains. Tests compare those domains and counts with a fully
enumerated inventory and check both marking dependency patterns.

The additional neighbor-value marking is an **analytic control**, not a learned
failure marking. Standard colors already give \(W=(a,b)\), \(E=(b,c)\), so
horizontal agreement implies \(a=S_{\rm left}\) and \(c=S_{\rm right}\).
Assigning those values at the two neighboring bottom-value points is redundant
for complete rectangles, with blank exterior side pairs. It may reject finite
prefixes sooner. This is a specialized finite Wang problem; it does not supply
a marking or substitution to the turtle learner.

`proof_search.py` trains REINFORCE on all applicable word-rule singletons and
two-step sequences. Each executed constituent is independently valid; rewards
charge actual word moves and machine steps. A checked proposal compiles to a
whole rectangle of preferences. Every preferred tile still uses the graph's
global scheduler; invalid preferences fall back to all base options. Frozen
policies affect ordering only. A bounded operational check remains unknown if
its step budget expires; it does not invalidate an independently checked word
proof, and the full rectangle preference needs its own accepting replay.

`fair_search` dovetails powers-of-two capacities, proof lengths and heights,
revisiting each fixed triple with increasing node budgets. There is no wall
cutoff in unlimited execution. A finite derivation fits a finite word capacity
and proof length; padding and absorbing acceptance place it within larger
enumerated bounds. For one recurring triple, a sufficient node budget eventually
exhausts the complete finite DFS. Optional learned preferences preserve this
argument because no alternatives are removed. This semidecides derivability;
it need not stop on negative cases. The exported stage-limited control returns
unknown, not unprovability.

The cold pilot uses a declared four-rule theory with cycles and length changes.
Training has 64 episodes on source lengths four to six, zero initial weights,
and no imported certificate. Three held-out sources have lengths one to three
from the same theory and target family. At identical rectangle bounds and
100,000 placements/five seconds, standard Wang reaches none, analytic GCTS
reaches one, and each learned lane reaches all three. This small example tests
the implementation; it is not evidence of general mathematical proof-search
performance. Time includes construction and successful replay, with proposal
costs in the lane total and training reported separately.

Packed JSON proofs store a symbol table, used tile types, the complete grid and
initial row. `audit_proof_search.py` reconstructs programs from a separate fixed
problem declaration, checks every certificate through word/TM/point semantics,
and rejects changed tile outputs, malformed symbol IDs, inputs and targets.
Semantic tests additionally reject forged theory rules and malformed generations,
exercise every machine transition shape and both tape borders, and preserve
singletons, fallback and exact rollback.

```sh
python3 research/gcts-rl-renewal/run_proof_search.py
python3 research/gcts-rl-renewal/audit_proof_search.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py' -v
```

The program remains active: practical boundary-conditioned tiling, learned
cluster markings, plane coverage, Penrose hierarchy and compatible infinite continuation, the first-order
kernel compiler and substantial mathematical proof benchmarks remain open.

## Boundary solutions and first-class cluster tiles

`cluster_tiles.py` implements an explicitly declared aggregate tile system.
Types carry summed occupancy over distinct base constituents, inherited marking
components, level-own scalar markings and child maps. Every marking component
is attached to a physical lattice point and a channel; it does not create a new
occupancy obligation. Symmetries transform its point, leaving the channel and
integer color unchanged. Missing is free and assigned zero is meaningful.

Parent construction unions shared constituent identities, so repeated context
descriptions do not duplicate occupancy. Selected aggregate placements have
disjoint base ownership. The dependency graph indexes both point components
and constituent ownership. Independent enumeration checks complete type,
orientation and positive-support alignments. Snapshots restore ownership,
roots, generations, point data and complete incidence. Flattening every accepted
aggregate to base placements verifies exact occupancy and marking semantics.
Child maps must descend in level and preserve inherited marks; forged child
expansions, omitted channels and cyclic hierarchies reject.

Atomic placement is exact for this **aggregate inventory**, with the reference
scheduler applied at that level. It is not a shortcut claiming equivalence to
the base macro scheduler. Including every unmarked singleton gives every base
solution an all-singleton representation; new restrictions on cluster channels
then affect only the use of those higher-level types. With only a sampled
cluster inventory, exhaustion cannot prove the original base problem impossible.
Future cluster failure markings must declare whether they are problem-defining,
restricted hypotheses or independently proved redundant for a stated universe.

`export_cluster_types.py` explicitly reuses fourteen searched motif expansions
and one observed child assembly from iteration 03. It imports no old marking,
policy or human substitution. The sixteen-type inventory includes the base
singleton; all 192 transformed expansions independently replay. New cluster
marking channels remain free. This is construction evidence, not a speed
benchmark or completed failure-learning experiment.

For a finite required region \(D\), fixed exterior values define the problem
\(T_{\rm ext}(p)+\sum_{c\in S}t_c(p)=1\) for \(p\in D\), with exact
marking agreement and declared admissible placements. A movable boundary adds
explicit shape/position variables and point conditions that backtrack with the
state. The useful boundary trace contains residual capacities, all marking
components including exterior dependencies, and base ownership. Joining local
solutions is a discrete compatibility relation, not linear superposition.

The next experiments will test larger collars before retaining local cores,
coarse interface problems for long-range obstructions, and refinement after a
coarse failure. These are proposed transfers from
[Hou and Wu's multiscale construction/oversampling](https://authors.library.caltech.edu/records/spv1w-bz590)
and [Xu and Zikatanov's multigrid framework](https://arxiv.org/abs/1611.01917).
Their PDE convergence guarantees do not transfer automatically. The benchmark
must measure verified region completion, wall time, construction/learning cost,
memory, boundary robustness and expansion checking across tile systems.

```sh
python3 research/gcts-rl-renewal/export_cluster_types.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py' -v
```

## Finite boundary pilot and searched solution tiles

`region_tiles.py` declares immutable required points \(D\), a finite admissible
support envelope \(P\), fixed exterior occupancy and marking components, and
fixed exterior base ownership. Only \(D\) is a completion obligation; all
occupancy remains capacity-legal everywhere, including outside \(D\). Every
required zero is active from the start. Mark-only points are not restricted to
\(P\). Exterior support and required roots have generation zero, so every
placed candidate touching a required root has tile generation one. This is a
finite boundary convention, not a measurement of spatial growth layers.

The compiler enumerates every type, all twelve symmetries and all translations
anchoring a positive point inside \(P\). It retains every initially legal
placement. Immutable exterior conditions allow an exact initial filter;
subsequent graph updates handle every mutable occupancy, component and base
ownership dependency. Independent domains enumerate all support alignments
without the compiler index. Search uses the reference global scheduler and
full snapshots. Exhaustion exports a complete tree; the independent checker
re-enumerates all domains and alternatives. A cutoff returns unknown. The
cooperative ten-second limit includes compilation but can only interrupt at
search checkpoints. No marking learner is hidden inside this compiler.

`run_regions.py` explicitly reuses sixteen unmarked types and earlier unmarked
core patches. Four evaluation holes use two patches as fixed exterior contexts;
six training holes use a third patch. Removed placements appear only in the
problem-authoring feasibility controls, never in search or policy features.
Two extra targets, a hexagonal core and a notched core with a disconnected
pocket, have no donor/exterior/feasibility witness. REINFORCE starts at zero,
trains for 24 episodes, and charges actual base-placement attempts and nodes.
Ten rollouts complete. Frozen evaluation has all singleton fallbacks and full
DFS alternatives. One seed per case is an implementation pilot, not a reliable
speed estimate.

All six targets complete in all three lanes. Both declared movable families
also complete in every lane: their remote member exhausts with a checked dead
domain; their translated member succeeds. Each family shares a fixed exterior
and envelope across three explicit required sets. Each member receives its own
budget and fresh state. This is finite existential shape/position selection,
not continuous boundary optimization. Unknown members remain unknown even if
another member succeeds.

The singleton reference is faster on every case. On the witness-free targets,
RL reduces aggregate backtracking to zero, but aggregate inventory construction
and bookkeeping outweigh that gain. Atomic aggregate inventory and singleton
scheduling differ, so their comparison is not a matched GCTS-marking benchmark.
Peak process memory is about 604 MiB; construction, training and auditing costs
are explicit. Graph metrics inherited from `Graph` classify ownership-only
removals in its generic `completed_frontier` category; they do not identify a
learned marking effect or a separately measured ownership elimination rate.

Six searched completions become new parent types with descending child maps;
all 72 transformed expansions independently flatten. Their completion guarantee
is boundary-context-specific. The types are legal partial tiles elsewhere,
where their interfaces must still match. All own-level channels remain free.
This implements local-solution extraction, not learned multiscale failure
markings or a recurrent substitution.

`audit_regions.py` reconstructs problem declarations externally, checks 55
serialized states (34 complete), replays 268 new base constituents and eleven
negative-tree nodes, and rejects 137 altered certificates. Exact rational
polygon clipping finds no positive-area overlaps in the 24 displayed finite
patches. That independent audit does not prove general geometric faithfulness,
continuous region coverage or infinite extension. Six new conformance tests
cover required zeros, unrequired exterior points, full boundary domains,
snapshot rollback, distant assigned-zero components, finite-family state
reset, complete negative trees and export tampering. That milestone passed 57
tests; the cluster marking pilot below brings the suite to 63.

```sh
python3 research/gcts-rl-renewal/run_regions.py
python3 research/gcts-rl-renewal/audit_regions.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py' -v
```

Next: compress/reuse exact boundary interfaces, learn own-level cluster marking
channels from independently certified failures, and search coarse assemblies
with checked refinement. Larger regions, other tile systems, plane continuation
and the first-order kernel-to-machine bridge remain open. Turtle substitution
remains an optional route to a plane proof.

## Own-level cluster markings from complete base failures

`run_cluster_marking.py` selects the smallest previously searched level-one
cluster with both turtle handednesses, breaking ties by identity. It imports
only its unmarked shape and the singleton type. All prior markings, policies,
substitutions and known tiling witnesses are excluded. The prototype contains
two base turtles. Its 420 capacity-legal self-contacts have disjoint base
ownership; orientation aliases remain distinct inventory identities.

`cluster_learning.py` fixes each pair's four base constituents and labels it
with the complete **unmarked base** inventory. It uses global dead/forced checks
and earliest-generation branching, copying the complete state and graph on
rollback. Positives fill the initial support and retain a viable exposed
frontier. Negatives export complete trees; limits return unresolved. All labels
resolve at the initial 2,000-node/five-second bounds: eight positive and 412
negative. The cold base caches reset every 70 contacts, explicitly recorded.

The online encoder starts with every own-level component free. After each
positive it merges every overlapping prototype position. Negatives supply
inequality alternatives, and unknown samples would impose nothing. Full
provisional assignments are inspection records, never oracle input. Final
sparsification retains 18 values on 51 prototype support points, leaves 33 free,
and uses twelve scalar equality colors. Missing is free; color zero is assigned.
The new `cluster:1` marking accepts all eight positives and rejects 380 of the
412 negatives. Assignments exist only in the fresh experiment and its exported
inspection snapshot; subsequent runs must freshly learn or declare reuse.

`audit_cluster_marking.py` checks all 3,146 negative-tree nodes and every positive
through a separate literal-support enumerator. Its cache stores transformed
values only, never search domains or branch legality. It independently enumerates
every possible scalar disagreement, including contacts found by marking support
alignment rather than the occupancy catalog. All 380 are checked base failures;
5,040 transformed catalog contacts verify the scalar action. Thus every complete
unmarked base **point-model** tiling decorated by disjoint occurrences of this
cluster satisfies the marking. This is conditional redundancy, not existence,
plane coverage, preservation of finite groupings, or a claim about overlapping
cluster descriptions. Shared-context composition still requires compatible
inherited values and its own scope.

The first positive two-cluster assembly becomes a level-two parent with four
distinct base constituents, two descending child maps and 35 inherited assigned
components. Its own channel remains free. Twelve transformed parent expansions
replay. This is the first checked example of failure markings propagating into
the next cluster layer, not a recurrent substitution.

The six boundary targets from `run_regions.py` receive matched four-lane tests
with the same two-type inventory, point conditions, atomic scheduler and bounds.
All base singletons remain available. A new zero-start policy trains on unmarked
holes; both RL lanes use those same frozen weights. All 24 evaluation runs
complete. On the notched-core/pocket case, GCTS reduces backtracks from 31 to 13
and total time from 1.21 to 0.98 seconds, but it does not improve every case. RL
is slower on both witness-free targets. One seed per target cannot establish a
stable speedup. This two-type study differs from the prior sixteen-type study;
its timings are not a direct cross-study acceleration comparison.

Learning/synthesis costs 17.19 seconds, RL training 1.10 seconds, the pipeline
30.35 seconds, and separate audit 34.94 seconds. Peak process memory is about
277 MiB. Independent replay checks 48 finite states (35 complete), 290 new base
placements and 107 rejected alterations. All 24 displayed finite region patches
pass rational polygon non-overlap checks. Six new tests cover complete contact
enumeration, independent cached-value domains, negative-tree alternatives,
online equality/unknown/free semantics, inherited scalar channels and typed
certificates. The entire suite passes 63 tests.

```sh
python3 research/gcts-rl-renewal/run_cluster_marking.py
python3 research/gcts-rl-renewal/audit_cluster_marking.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py' -v
```

Next: learn compatibility across multiple cluster types, use higher-level
failure contexts for new channels, and compress exact interfaces for coarse
assembly/refinement. Practical large-region performance, unbounded plane
continuation, Penrose hierarchy and compatible infinite continuation and the logic-kernel compiler
remain open. Substitution is an optional route to a plane construction.


## Conditional analytic rhomb faithfulness and full-star extension

The new result is a theorem about the declared sector model, with a written
analytic proof in `docs/research/gcts-rl-renewal/penrose-faithfulness.html`.
A nonempty vertex-connected, capacity-legal assignment with all ten sectors
full at every generated vertex develops bijectively into an edge-to-edge plane
tiling. It does not require all points of the dense module to be vertices.
The converse holds for edge-to-edge tilings by the declared unit placements.
This theorem is not a discovered infinite continuation, a Penrose arrow
characterization or a machine-checked Hilbert proof.

The proof has four steps. Directional sector partitions force exactly two
opposite partners on each whole unit edge. The glued abstract faces form a
connected flat surface without boundary, with their given coordinates providing
a local isometry to the plane. Barycentric graph distance extends affinely to a
continuous function with gradient norm at most \(12\): all template triangles
have half-edge length \(1/2\), corner-to-centre length at most \(1\), and
absolute determinant at least \(1/8\). Every intrinsic ball of radius
\(R\) consequently lies in a finite subcomplex whose vertices have graph
distance at most \(\lceil12R+1\rceil\). Closed balls are compact, proving
metric completeness. The complete-local-isometry covering theorem, followed
by simple connectivity of \(\mathbb R^2\), makes development a bijection.
The covering theorem is Proposition 4.9 of Urs Lang's primary ETH lecture
notes, linked from the proof. The surface and completeness arguments are ours.

`penrose_complex.py` independently declares both outlines and reconstructs
sector support. `audit_penrose_complex.py` checks equality with the actual
unmodified search model: all 80 corner identities, 40 physical corners and
708 complete stars. An independent cyclic-composition enumeration proves the
finite catalog complete. All 4,010 radial seams have opposite unit partners;
all 7,080 rotated stars agree with the exact geometric action. Exact rational
cyclotomic arithmetic checks 160 barycentric triangles and all corner-chart
altitudes. A separate polygon audit checks 9,925 local face pairs without
overlap. The infinite topological inference remains the explicit written proof,
not something those finite counts alone establish.

The same audit replays the unchanged 320 historical point patches. Their 2,210
complete vertices match the star catalog, realizing 432 distinct stars. Their
6,544 exposed vertices are incomplete. These patches therefore do not meet
the theorem's full-saturation assumption. Source and historical-artifact hashes,
and the exact proof-document hash, are saved in `penrose-complex-001.json`.
The older artifact's open-faithfulness label records its original state.

Connectivity is essential. An explicitly analytic comparison control uses
two entire periodic thick-rhomb grids on the disjoint vertex cosets
\(\Lambda=\mathbb Z+\mathbb Z\zeta_5\) and
\(\varphi^{-1}+\Lambda\). Both components saturate their stars and each
covers the plane; their overlaid union is point-legal yet geometrically overlaps.
These known grids are controls only and never seed discovery or policy training.
Finite partial point patches continue to require their separate geometry audit.
The turtle's scalar angle weights do not provide the directional partition
needed for this theorem.

`penrose_star_search.py` is a fresh unmarked higher-context pilot. It recomputes
the full-star catalog from prototypes and covers all 708 stars using 75 verified
rotation orbits. Each fixed star has three through ten distinct rhombs. The
required target is every sector at every vertex of the entire fixed cluster,
not just its already full central vertex. Search retains both kinds, all ten
rotations and every point-support alignment in the original complete graph.
No old patch, marking, arrows, policy or substitution is imported. Immutable
geometry is diagnostic only; polygons do not decide candidate legality.
Caches reset after ten orbits. Every generated star slot is an explicit
zero-generation root; later tile generations follow the existing point rule.
Snapshots restore the complete state and graph. Global dead/forced checks
precede earliest-generation branching, with initial-core, degree and exact-key
ties. A 2,000-node or three-second cooperative cutoff means unresolved.

All 75 representatives complete, with no negatives or unresolved results.
Independent representative domains check every exposed slot. The transferred
708 completions replay exact point coverage and one legal candidate per exposed
slot, totaling 100,090 frontier witnesses. Seed aliases are canonicalized only
in the diagnostic context catalog; the search inventory keeps every alias.
The transformation audit checks the exact rotation action and identical
unmarked support of replaced seed aliases. This is a symmetry transfer of
finite existence and viability certificates, not 708 separate searches or a
claim of identical lexicographic branch order after rotation.

`audit_penrose_stars.py` reconstructs the declared contexts externally, replays
saved placements, targets, generations and every frontier witness, audits all
75 representative polygons, and rejects altered targets and omitted frontier
witnesses. It checks 1,886 representative base placements and 17,689 transformed
placements. The pilot finds no failed context from which to synthesize a new
marking. No marking or RL policy is activated; no acceleration comparison is
claimed. One-corona existence still does not imply infinite extension.
Search, first audit, separate saved-data replay, peak memory and source hashes
are reported separately in `penrose-stars-001.json`.

```sh
python3 research/gcts-rl-renewal/audit_penrose_complex.py
python3 research/gcts-rl-renewal/audit_penrose_complex.py --check docs/research/gcts-rl-renewal/penrose-complex-001.json
python3 research/gcts-rl-renewal/penrose_star_search.py
python3 research/gcts-rl-renewal/audit_penrose_stars.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py' -v
```

Semantic checks now include independent star completeness, rejected omitted
stars and altered edge partners, exact metric bounds and degenerate templates,
partial-star versus whole-patch completion, declared integer transforms,
rotation-orbit coverage, zero-root generations, exact transformed viability,
changed targets, cutoffs-as-unknown and an independently exhausted marked
control. That restrictive control is test-only; discovery always starts unmarked.
Compatible unbounded saturation, a Penrose hierarchy, practical multiscale
acceleration and the first-order-kernel compiler remain open.

The complete suite at this milestone passed 76 tests, including 13 new complex
and full-star checks. Earlier snapshots retain their milestone test counts.

## First-order kernel to Wang bridge: finite catalogs and a fair union

Earlier sections retain the open/closed status of their respective milestones.

`kernel_machine.py` compiles all supported `logic.Kernel` inference relations
inside an externally fixed finite syntax catalog. The catalog is constructed
from declared formulas, instantiation terms, variables and substitution
templates before any proof search. The resulting literal deterministic machine
has one Boolean tape cell per formula. Unknown certificate symbols select
inference commands; each command checks all its premises and sets the conclusion
cell. Every cell starts false. Acceptance checks the externally declared target,
erases the workspace and returns to a unique absorbing accepting configuration.
No host-language checker callback occurs in the machine transition loop.
Alternative instantiation terms or equality templates yielding the same
formula/rule relation share one canonical checked witness; derivability, not
certificate multiplicity or the exact spelling of an input proof, is preserved.

All eight kernel kinds are represented: registered closed axioms, propositional
tautologies, reflexivity, capture-avoiding universal instantiation, universal
distribution with its free-variable side condition, equality substitution,
modus ponens and generalization. The machine supports repeated commands and
arbitrarily long finite certificates, without storing chronological line
references. `Catalog.proof` independently reconstructs those references and
checks the result against the external kernel. If the target was proved before
the end, it retains the valid prefix ending at the last target line.

The finite correctness argument is an induction on commands: every set cell
has a valid kernel derivation, and each inference adds another valid derivation.
Conversely, a kernel proof whose formulas and schema parameters occur in the
catalog translates line by line to commands. This gives exact provability in
the finite compiled inference closure. It does not prove that failure in that
closure means failure in the full first-order theory.

`language_stage` enumerates all terms and formulas up to a declared AST-node
bound over the finite signature. Its variable set includes names from the
problem and an increasing shortlex enumeration of all Python Unicode strings.
Every finite literal kernel proof, including substitution templates and terms,
eventually lies inside one catalog. `kernel_search.fair_search` dovetails syntax
bounds, powers-of-two certificate lengths and rectangle heights, revisiting
each rectangle with an unbounded node allowance. Padding and absorbing
acceptance preserve shorter witnesses. Thus, with unlimited resources, every
proof accepted by this kernel is eventually represented and found. This is
relative computational completeness, not a formally verified semantic
completeness theorem. The unrestricted syntax enumerator is extremely expensive;
only bounded semantic controls have run. A single fixed serialized-AST checker,
checked infinite axiom schemas and a formal compiler proof remain open.

The existing `lazy_wang` engine retains the exact doubled-grid point model,
complete symbolic candidate incidence, global dead/forced/earliest-generation
scheduler and exact rollback. All finite centers are zero-generation roots;
every placement has generation one. Each candidate has one positive occupancy
center; its edge and optional extended marking dependencies remain global.
The optional neighbor-value marking is the earlier analytic redundant control,
not a learned failure marking. Learned kernel inference sequences are proposals
only: their literal computation becomes a preferred rectangle, every constituent
uses the graph scheduler, and every base alternative remains available.

`run_kernel_machine.py` trains 128 zero-weight REINFORCE episodes on six assertion
controls with two unused theory axioms. Evaluation uses the same assertions
with three unused axioms, one seed, eight unknown certificate slots and 384
transition rows. This is a same-assertion distractor control, not mathematical
generalization. Every lane has the same 100,000-attempt and cooperative
three-second search budgets, including domain construction. Proposals have a
five-command horizon. Mean lane time includes failed budget-limited attempts;
it is not an equal-success speed ratio. Training, compilation, preference
construction, successful search replay and independent audit costs are reported.

The saved pilot has 66 checked training proposals. Standard Wang completes
one of six controls, the analytic marking completes three, and both RL lanes
complete five. Distribution remains unresolved in all lanes in this distractor
configuration. Fourteen accepting rectangles replay as external kernel proofs,
with 111,744 base point placements and 56 rejected changes to targets, rows,
proofs and fact boundaries. The cold proposal learned no new failure marking.

`audit_kernel_machine.py` constructs schemas independently and intersects their
conclusions with the catalog, checks the exact inference inventory, reconstructs
the externally defined evaluation problems, replays every training command
sequence, checks the direct TM computations and all point sums/marks, and
decodes saved proofs without allowing certificate-selected axioms. The separate
arithmetic control supplies the earlier 15-line addition proof only to test the
compiler: it becomes 15 commands, 267 states, 1,260 literal transitions and
1,052 machine steps. Its witness-derived catalog and proof never enter training
or discovery. It is a compiler round trip, not a new arithmetic discovery.

```sh
python3 research/gcts-rl-renewal/run_kernel_machine.py
python3 research/gcts-rl-renewal/audit_kernel_machine.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py' -v
```

At that milestone the suite passed 84 tests. The eight new tests cover independent rule
enumeration, literal-machine versus kernel acceptance, captured variables,
invalid distribution, proof translation, nonfinal targets, empty/forged
certificates, Unicode grammar fairness, budget labels, unseeded Wang proof
search and redundant-marking controls. Existing graph completeness and rollback
tests still apply to the unchanged engine. Harder proofs, hierarchical proof
clusters, practical multiscale tiling acceleration and certified turtle or
search-produced Penrose plane continuation remain open.

## Two-level learning and repeated authored boundary requests

`run_multiscale_regions.py` imports only the unmarked singleton and the two
searched mixed-handed two-turtle shapes `cluster-2` and `cluster-3` from the
declared, hashed `cluster-types-001.json`. Every palette starts free; the policy
starts at zero. No earlier marking, policy, donor, boundary or completion witness
enters this experiment. A separate development repeat of level-one learning and
one preliminary resident-inventory control are explicitly recorded as preliminary
work, not inputs to the official run. Targeted tests overlapped a few seconds of
second-level labeling; no learning-throughput claim is made. Regional evaluation
was sequential without another research job running.

`multiscale_learning.py` shares one scalar channel among distinct prototypes at
the same level. Its equality slots are tagged by type and point. The complete
rooted catalog includes all twelve orientations, every positive-support alignment,
disjoint base ownership and capacity legality. Every label oracle strips **all**
own and inherited markings, fixes the flattened base constituents, and searches
the full unmarked base inventory. A positive fills the initial support and checks
viable exposed frontier domains. A negative requires an independently checked
complete base failure tree. A cutoff remains unknown and constrains no values.
Positive contacts merge overlap slots; negatives supply inequality alternatives.
The snapshot contains the actual provisional assignment after every label.
Sparsification retains differing overlap witnesses; assigned zero remains a value.

The first stage has \(1{,}818\) contacts: \(22\) positive and \(1{,}796\) negative,
with no unknowns. Its \(41\) assignments across \(104\) slots use \(16\) colors and
exclude \(1{,}442\) negatives, accepting all positives. Every possible sparse
scalar exclusion is enumerated independently before activation; each has a base
failure certificate. Normalizing a pair by a lattice symmetry transfers that
certificate, so every complete unmarked base point tiling decorated by disjoint
occurrences of these shapes satisfies their shared marking. This conditional
redundancy neither proves existence nor preserves all finite coarse groupings.
All unmarked singleton paths remain available in regional search.

A newly searched positive cross-type assembly supplies the four-turtle
`searched-multiscale-parent`. Its two descending child maps preserve every
level-one component. The next label study uses its unmarked flattened shape,
then decorates it with a new `cluster:2` channel alongside inherited `cluster:1`.
All \(677\) parent self-contact contexts are negative. The new palette assigns
\(30\) values in \(100\) slots and excludes \(647\) contacts; inheritance alone
excludes \(577\), so the new channel adds \(70\). The remaining \(30\) certified
failures are not represented by this sparse scalar palette.

There is also a parent-only obstruction. At \(p=(-4,-6,10)\) the root parent
contributes \(t(p)=\tfrac13\). Any complete point tiling by this parent alone
requires another parent at that point. Normalize the root's pose. The disjoint,
capacity-legal pair lies in the exhaustive contact catalog, but its complete
unmarked base failure tree contradicts a complete continuation. The saved audit
checks all \(796\) parent failure-tree nodes and \(4{,}032\) support/group
compositions. This is an analytic lifting of checked finite trees, not a formally
encoded Hilbert proof. It rules out only the declared parent-only point inventory;
the mixed hierarchy and base turtle plane problem remain open. A locally completed
assembly need not be a recurrent metatile. Next parent selection should test
cross-type coarse continuation, rather than insist that this one parent recur.

The four evaluation targets are authored without a donor or feasibility witness:
cores of radii \(4,6,8\), and a notch with a disconnected pocket. Their common
support envelope has radius \(14\), with zero exterior. Every required point is
activated at generation zero and must reach full capacity; elsewhere contributions
remain capacity-legal. These are independent finite requests, not a nested
continuation or a geometric coverage certificate. Training has four smaller
translated targets and twelve zero-start episodes, of which three rollouts
complete. Evaluation has two seeds per target, six lanes and the same
\(4{,}000\)-node, five-second cooperative limits including request construction.
Unknown attempts are included in timing means.

RL and GCTS+RL finish all eight requests, while the unmarked hierarchy and both
marking-only hierarchies finish six. The singleton reference also finishes eight
and is fastest: mean request times are \(1.03\) seconds for singletons,
\(1.53\) for RL and \(1.62\) for GCTS+RL. The parent’s own channel makes almost
no additional regional difference beyond inheritance. These data do not show a
practical multiscale acceleration. The singleton comparison changes the atomic
inventory; the four-type marking/RL lanes have matched shapes and scheduler.

`resident_regions.py` freezes the complete placement universe for an immutable
envelope and type/marking version. Each boundary request rejects only placements
incompatible with that request’s immutable exterior and creates a fresh state and
complete point/candidate graph. All occupancy, marking and ownership dependencies,
including extended mark-only points, remain indexed. No previous roots, exclusions,
marks, ownership or branch states leak between requests. The reference scheduler
is unchanged: global dead, global forced, then earliest generation, with minimum
domain only breaking generation ties. Snapshots restore all mutable state exactly.
RL preferences order validated atomic cluster placements; full evaluation retains
every alternative. Aggregate scheduling is distinct from base macro execution.

The matched representation control repeats all eight unmarked requests cold.
Both versions complete the same six and leave two unknown; all six completed
states and search counters match exactly. Cold requests total \(31.44\) seconds;
resident requests plus the full one-time \(1.46\)-second build cost total
\(26.99\) seconds. Restricting to the six identical completed traces gives
\(21.38\) seconds cold versus \(16.90\) seconds resident including the full
build charge. This is an exact representation optimization, not a learned
marking result or an equal-success comparison of all budget-limited traces.

Up-front costs are material: both cold learners plus their activation audits
take \(184.37\) seconds, RL training \(11.67\), the complete official pipeline
\(342.58\), and the separate saved-data audit \(102.45\). Peak process memory
is \(1{,}220.47\) MiB. Each frozen inventory’s construction cost is reported;
the raw and RL lanes share one version, and the fully marked/RL lanes share
another. The learning cost exceeds this batch’s observed saving. Broader boundary
families, cache amortization, collars, compatible mixed coarse inventories and
adaptive refinement are the next practical gates.

`audit_multiscale_regions.py` reconstructs shapes, parent maps, all external
boundaries and inventories; independently enumerates contacts; replays every
base failure tree and positive witness; recomputes provisional and sparse values;
and checks all actual scalar disagreements in all root orientations. It checks
\(8{,}820\) failure-tree nodes, \(22\) positives, \(29{,}940\) scalar contacts,
all \(68\) exported states and \(892\) base placements. There are \(51\) completed
states including training and cold controls. All displayed completed patches pass
separate exact polygon non-overlap. Changed poses, omitted failure branches and
omitted base expansions reject. No general turtle geometric faithfulness theorem
or plane construction follows.

```sh
python3 research/gcts-rl-renewal/run_multiscale_regions.py
python3 research/gcts-rl-renewal/audit_multiscale_regions.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py' -v
```

At that milestone the suite passed 98 tests. Fourteen new controls exercise shared
type-tagged palettes, unmarked catalog independence, unknown labels, actual scalar
exclusions, child-mark preservation and symmetry, resident domain completeness,
extended zero-valued dependencies, exact rollback, fresh request state, immutable
version/envelope guards, and reference trace equivalence. The original engine and
prior source-hashed snapshots are unchanged. The HTML report loads each level’s
large history only when selected and exposes both palettes, inherited values,
individual failure trees and every regional lane/seed. The research goal remains
active, with substitution optional under the user’s revised objective.

## Joint parent-library gate and a proof by type elimination

`coarse_continuation.py` declares a new coarse-only inventory from **all**
\(22\) prior positive level-one contacts. These contribute \(13\) distinct
four-turtle shapes modulo the declared twelve symmetries and translation.
Both source child definitions are unmarked. Exact transformed child maps
normalize each parent, descend in level and flatten to distinct base placements.
The prior positives are reused as shape declarations; their base completion
witnesses, learned palettes and policy weights never enter coarse search.
The saved-data audit separately replays all positives and checks every alias by
a literal group/translation orbit, independently of `spatial.canonical`.

Each gate fixes one normalized parent at generation zero and activates all its
positive support. Only the \(13\) declared parent types may be placed; auxiliary
children validate their maps but are excluded from candidate incidence. There
is no support envelope or singleton fallback. Every exposed point receives all
parent orientations and positive-support alignments over the entire lattice.
The initial support must fill and exposed frontier domains must remain viable.
An exhausted tree refutes a complete coarse continuation. A cutoff remains
unknown. A finite positive, had one been found, would still be finite evidence.

`RootModel` compiles candidates against the immutable fixed root. Its Boolean
rejection cache avoids retaining full illegal footprints. Every root-compatible
candidate retains full point/mark/base-ownership dependencies and dynamic legality.
Root-incompatible candidates cannot revive below this root; branch snapshots
retain the root and restore every other value, generation and incidence.
Constructor caches for hierarchy validation are cleared before graph construction
so auxiliary child placements cannot leak through reverse dependencies. The
independent oracle enumerates literal full type/orientation/support alignments
without root-compilation filters. Global dead, global forced and earliest
generation remain the scheduler order. Aggregate level and search generation
are separate quantities.

The initial unmarked gate finds \(4\) complete root failures and leaves \(9\)
unknown, under \(4{,}000\)-node and fifteen-second cooperative bounds. The four
failures use \(6\) tree nodes. `coarse_fixed_point.py` imports those checked
exclusions, retains every unknown and rechecks the remaining inventory. A new
failure extends an inductive claim about complete tilings by the original
library; the inventory omission carries that proved context. Each round uses
\(6{,}000\) nodes and twenty seconds per root. The subsequent nine-type round
excludes four more types with \(74\) tree nodes. The final five-type round
excludes all five with \(65\) nodes. No type survives. The complete proof uses
\(145\) unmarked coarse tree nodes across the three rounds.

The lifting argument is explicit. Assume a complete original-library point
tiling. Normalize any used parent by a symmetry and translation. Every finite
prefix has a legal remaining tiling member at each incomplete frontier point.
A complete finite failure tree lists every branch alternative and ends only
at an independently re-enumerated empty domain. Following the assumed tiling
through the tree is therefore impossible. Types excluded in the first round
cannot occur. A complete original-library tiling consequently uses only the
remaining inventory. Apply the same argument to each later round, until no
type remains. This proves that the joint \(13\)-type library has no complete
point tiling, with disjoint base ownership. It is an analytic induction over
machine-checked finite trees, not a formally encoded first-order derivation.

This conclusion does not decide the base turtle plane problem, exclude these
parents from larger inventories, or forbid their use in finite regions alongside
singletons. The preceding regional study uses them legally in that context.
These coarse failure trees cannot supply a claim of redundant pruning for a
different base or mixed inventory. A fixed coarse library is a diagnostic here;
practical region solving may keep fine-scale refinement and irregular local
solutions without demanding a stationary parent-only tiling.

`capacity_pruning.py` is a separate analytic control, with no learned GCTS
marking. Future contributions at a completed point sum to its deficit. The
declared positive values \(\{3,4,6,8,9,12\}\) generate an additive monoid whose
unreachable deficits up to capacity \(12\) are \(\{1,2,5\}\). Removing a candidate
that leaves such a deficit is necessary for complete point tilings. Candidate
removal uses the same graph and records the analytic reason; exact state copies
preserve the constraint version. For **finite region** problems, apply this rule
only to required points: optional exterior points may remain incomplete. The
unit tests exercise this distinction.

The present analytic gate applies the rule to all activated positive support,
explicitly strengthening the finite corona semantics to numerical future
completion. Its initial thirteen-type control finds three failures and leaves
ten unknown, rather than the reference’s four failures and nine unknown. The
elimination proof uses none of these analytic premises. Fewer candidates did
not produce a stronger bounded result. No marking-learning or RL cost is hidden:
neither mechanism runs in this gate.

Costs include complete graph construction and unresolved attempts. The initial
reference plus its first independent audits takes \(203.35\) seconds; the
analytic control \(193.58\); subsequent elimination rounds and first audits
\(260.62\). Each is one sequential pass; different proved inventory contexts
and cooperative overshoot prevent an equal-success speed interpretation.
Search-process peak memory was not instrumented in these initial gates, a
performance-reporting gap; compiled-key counts are retained. The separate
saved-data audit reports its own duration and peak process memory. Audit and
test timing can overlap, and neither is a search-throughput measurement.

`audit_coarse_gate.py` reconstructs the external library, literal positive
shape aliases, every root and active-inventory premise, base expansion,
generations, coverage and result scope. It replays \(40\) exported prefixes,
all \(145\) reference/elimination failure-tree nodes and the three independent
analytic nodes. It checks \(156\) transformed parent expansions, independently
enumerates the numerical monoid, and rejects \(16\) altered trees. No finite
coarse completion was found. The canonical JSON preserves all three studies,
including every cutoff and proof premise; earlier snapshots and source-hashed
engines are unchanged.

```sh
python3 research/gcts-rl-renewal/coarse_continuation.py
python3 research/gcts-rl-renewal/capacity_pruning.py
python3 research/gcts-rl-renewal/coarse_fixed_point.py
python3 research/gcts-rl-renewal/audit_coarse_gate.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py' -v
```

The current suite passes 105 tests, including seven new controls for complete
parent normalization and child maps, auxiliary-inventory isolation, immutable
root domains versus literal enumeration, rollback, the numerical completion
constraint and its finite boundary scope, unknown budgets and changed leaves.
The report exposes the three-round proof, every parent and first dead leaf,
and the separate analytic control. Next: generate broader variable-size parent
families, choose them for useful cross-type continuation and boundary reuse,
and retain singleton refinement for practical regional tasks. Plane construction,
Penrose hierarchy and general hierarchical proof search remain open.

## Variable-size local proposals in the same singleton graph

`boundary_macros.py` returns to practical boundary solving with an unchanged
singleton inventory and scheduler in every comparison lane. Eight fresh local
completions supply connected temporal windows. Mining finds \(59\) distinct
shapes from \(75\) windows and retains \(20\) clusters, four each of sizes
\(2\) through \(6\). No prior marking, cluster artifact, policy or completion
witness is imported. The local shapes have exact occupancy/residual traces and
free own-level markings; this pilot does not learn a new GCTS channel.

The proposer aligns transformed shapes at scheduled base candidates, counts
already-owned context once, and validates every new constituent against the
complete point graph. It returns a schedulable prefix when the next obligation
leaves the patch. Every singleton action remains available. Proposals never
supply degrees, forced moves or pruning premises. State and graph copies restore
all point values, ownership and generations. Search budgets charge actual base
placements, including every explored macro constituent; enumeration and proposal
validation consume the cooperative wall budget. No negative certificate is
exported by this heuristic search.

A zero-start linear REINFORCE policy trains for \(24\) episodes on four small
local boundary problems. Seven rollouts complete. The policy sees residual
capacity counts, required and optional contributions, filled obligations and
proposed size. Both RL evaluation lanes use the same frozen policy. Training,
donor and evaluation seeds are distinct, although local shapes may recur.
All lanes use the same \(4{,}596\)-pose resident singleton inventory, four
authored held-out targets, two seeds, \(8{,}000\) explored base placements and
six cooperative seconds per request. Lane order rotates by target and replica.

Base and untrained cluster proposals both complete all eight fixed runs. Mean
request times are \(0.508\) and \(1.845\) seconds. Clusters reduce base attempts
from \(576\) to \(475\), and backtracks from \(463\) to \(335\), but cost
\(3.63\) times the request time. Proposal work alone takes \(11.44\) seconds
over the eight macro runs. Both RL lanes complete six cases, with two cutoffs;
their means \(1.685\) and \(2.488\) seconds are not equal-success comparisons.
No practical speedup is demonstrated.

An explicit three-member movable boundary family keeps the envelope fixed. Each
lane starts with an uncompleted edge target, then exactly fills the shifted core
using fresh state and roots. Base lanes take about \(0.324\) seconds, while
cluster lanes take \(1.716\) and \(1.554\). The first member's exhaustion is
uncertified; the later existential witness needs no negative premise.

Cold resident construction takes \(0.222\) seconds; new donors \(1.101\),
mining \(0.012\), proposal-index build \(0.042\), and policy training
\(29.584\). The complete sequential official process takes \(87.527\)
seconds and peaks at \(235.16\) MiB. Reusable learning costs total \(30.740\)
seconds; lower base-attempt counts cannot pay for them in this batch. Request
times include graph construction and proposal validation. Process peak memory
is not per-lane allocation; cooperative bounds can overshoot at a checkpoint.

`audit_boundary_macros.py` independently constructs every literal transformed
singleton pose inside the external envelope. It scans that complete inventory
before every exported move, checking global dead/forced/earliest scheduling,
values, ownership, generations and required coverage. All \(72\) saved states
and \(601\) moves replay; \(47\) states complete their targets. Every mined
shape reconstructs solely from new donors, and \(68\) changed schedules reject.
All \(32\) displayed complete evaluation/movable patches pass the separate
exact polygon non-overlap audit. The final saved-data replay takes \(7.881\)
seconds. These are finite point-model completions, without a general geometric
faithfulness or plane theorem.

```sh
python3 research/gcts-rl-renewal/run_boundary_macros.py
python3 research/gcts-rl-renewal/audit_boundary_macros.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py' -v
```

All \(114\) semantic tests pass, including nine new controls for literal full
inventory equality, variable-size mining provenance, singleton retention,
scheduled cluster constituents, exact snapshots, context ownership, base-move
budget accounting, fresh boundaries and rejection of altered schedules or
Boolean integer data. Earlier source-hashed engines and snapshots are unchanged.
The HTML report exposes the matched results, all saved patches, their proposal
groupings and each exact residual interface. Next: compile boundary compatibility
to reduce proposal cost, broaden collar/boundary families, and learn a policy
that improves total time at useful scales. The full research goal remains active.

## Exact compilation, shared prefixes and whole-state proposal reuse

`compiled_macros.py` optimizes the preceding proposal relation without changing
the singleton candidate graph or offered actions. A new cold experiment uses
eight fresh donors, \(86\) connected windows and \(67\) distinct shapes, retaining
\(20\) clusters of sizes \(2\) through \(6\). No saved artifact, marking or policy
enters this run. The new library differs from the preceding experiment; timings
across those two pilots are not equal-problem speed comparisons.

The compiler enumerates every allowed placement of those shapes inside the
fixed positive-support envelope. It stores \(42{,}150\) patches and \(149{,}964\)
constituent incidences across all \(4{,}596\) singleton poses. For every patch,
every member is an index key. Already-owned context is removed once. Individual
legality, proposal ranking and full-patch validation remain the reference rules.
A fixed owned exterior pose outside the compiled envelope invokes the original
procedure; changed envelopes or tile/marking versions reject. The present
compiler supports the declared unmarked identity singleton only.

Graph-prefix snapshots are immutable during planning. A new prefix gets fresh
copies and the normal update; identical prefixes share the same result. The
bounded memoization key contains the entire required set, point totals, assigned
marking data, ownership, selected poses, roots, generations and scheduled domain.
This is a conservative whole-state cache, not a locality theorem for global
forcing. Executed constituents still pass the real singleton scheduler. No
cache or proposal supplies degrees, forced moves or base-candidate exclusions.

The analytic equivalence argument separates the three optimizations. Every raw
individually legal proposal with all owned context inside the envelope appears
in the complete compiled incidence. Both procedures remove the same context,
rank identical pending sets and plan through identical point graphs. Identical
prefixes have identical semantic snapshots by induction over their base moves.
The complete state key fixes the frozen graph semantics and offered list. The
outside-context fallback preserves the reference relation. This is scoped
reasoning supported by independent finite enumeration and controls, without a
formally encoded first-order proof or an exhaustive mutable-state test.

Seven lanes separate base, raw proposals, compilation, prefix sharing, whole-state
caching, raw proposals with RL and cached proposals with RL. Each uses the same
four authored targets, two seeds, \(8{,}000\) base attempts and six cooperative
seconds. Lane order rotates. A fresh policy trains for \(24\) episodes on the
small local problems; seven complete. Both RL lanes share its frozen weights.
Learning cost is \(30.415\) seconds, donors \(1.102\), mining \(0.052\), raw
alignment construction \(0.003\), cold compilation \(0.331\), and common
resident inventory \(0.213\). The full sequential process, including finite-work
controls and movable cases, takes \(186.041\) seconds and peaks at
\(251.05\) MiB. Process peak is not per-lane allocation.

Base search completes all eight fixed runs, with mean request time \(0.407\)
seconds. Every proposal lane completes six. Mean request times, including
unknowns, are \(3.329\), \(2.819\), \(2.465\), \(2.404\), \(2.520\) and
\(1.787\) seconds respectively. They are not equal-success speed ratios. The
six matched completed raw/cached cases have identical search traces and take
\(14.621\) versus \(7.218\) total seconds, with compilation separately charged.
Faster unresolved lanes explore more of the same difficult search; that does
not establish a better policy or overall advantage over base search.

Eight warm finite-work controls remove the wall cutoff and cap exploration at
\(200\) base placements. Seven targets complete; one remains unknown in both
representations. Every pair agrees in state, scheduled moves, nodes, branches,
forced moves, backtracks and macro constituents. Raw requests total \(13.869\)
seconds; cached requests \(5.806\), plus \(0.331\) cold compilation. These controls
run after the held-out batch, with common placement data warm; they prove an
observed bounded-work latency improvement, not eight solved targets.

All five movable-family lanes exactly select the shifted core, with fresh state
for each member. Base takes \(0.737\) seconds; raw/cached \(3.004/1.476\), and
raw/cached with RL \(1.644/0.680\). This is one finite-family control, without
a general practical speed claim.

`audit_compiled_macros.py` independently rebuilds every literal singleton pose,
the transformed patch set and every constituent incidence. It checks \(114\)
saved states, \(1{,}195\) scheduled moves, \(78\) completed targets, eight exact
finite-work pairs and \(24\) equal completed representation pairs. It compares
\(11\) full offered lists and repeated cache hits. Six additionally inspected
offered continuations contain \(15\) new moves, all independently replayed; one
ends at a known dead point. Such a sequence has legal capacities and scheduled
constituents, but search must detect its endpoint and roll back. This exposes
a useful failure signal for the next policy/marking experiment.

All \(49\) displayed complete evaluation/movable patches pass separate exact
polygon non-overlap. The final saved-data audit takes \(24.927\) seconds, rejects
\(109\) changed schedules and preserves its source/helper hashes. It exports
actual offered sequences for the report's prefix tree and expanded boundary
view, including the dead endpoint. Saved partial prefixes are finite point data,
without a complete solution, plane guarantee or geometric faithfulness theorem.

```sh
python3 research/gcts-rl-renewal/run_compiled_macros.py
python3 research/gcts-rl-renewal/audit_compiled_macros.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py' -v
```

All \(123\) semantic tests pass. Nine new controls cover complete patch incidence,
reference/shared/cached action equivalence at every donor prefix, exact rollback,
generation and assigned-zero cache keys, envelope/marking guards, isolated lane
caches, exact base-attempt traces, cancelled validation and owned-exterior fallback.
Earlier source-hashed engines and snapshots are unchanged. Representation reuse
is now measured; practical region acceleration still needs better decisions or
certified geometric failure markings. Collars, higher-level interfaces, compatible
plane continuation, Penrose hierarchy and general proof search remain active.

## Failure interfaces from variable local solutions

The next cold milestone, `failure-interfaces-001.json`, separates two mechanisms:
verified scalar GCTS markings on promoted cluster tiles, and an analytic filter
on regional macro endpoints. Neither imports prior shapes, weights, markings or
completion witnesses. Eight fresh donor runs use seeds \(100000\) through
\(100007\); the miner selects twenty connected windows of two through six base
tiles. The most recurrent two- and three-turtle shapes pass fresh unmarked
one-corona probes. They are `local-2` and `local-3`, both level one.

The full shared contact catalog contains \(2056\) contacts: \(65\) positive,
\(1991\) negative and no unknowns. The online learner begins with free values,
unites tagged point classes from positive contacts and selects sparse witnesses
for negative inequalities. Its final `cluster:1` channel has \(39\) assigned
values, \(86\) free entries and three colors. All \(1341\) actual scalar
exclusions have independently checked unmarked base-corona failure trees.
Every positive contact is accepted. Provisional values never filter that oracle.

A newly searched positive cross-type contact supplies `local-parent-5`: two
descending child maps and five distinct base constituents. It inherits the child
channel, then learns a separate `cluster:2` channel from unmarked base searches.
The parent's full self-contact catalog has \(882\) contacts: seven positive,
\(875\) negative and no unknowns. Its own palette assigns \(37\) values, leaves
\(85\) free and uses \(24\) colors. It excludes \(839\) certified negatives;
\(573\) are already excluded by inherited values, so \(266\) are new. Counts
overlap. The positive self-contacts supply finite continuation evidence that
the earlier all-negative four-turtle parent lacked. They do not establish a
continuing parent-only library, substitution or plane construction.

Under a complete unmarked base point tiling, disjoint occurrences of these
shapes cannot have an impossible base contact. The verified scalar constraints
are redundant under that premise. Finite required regions may leave exterior
support incomplete, so these same values can restrict an otherwise valid finite
grouping. Whole-plane redundancy and finite-region grouping preservation are
different claims. Both aggregate inventories retain the base singleton.

`ViableProposer` wraps the unchanged compiled proposer. Each multi-move option
is replayed with immutable shared prefix snapshots and the complete singleton
graph. It removes the option only if the endpoint has a required point with an
empty domain. Every singleton alternative remains, including ones belonging to
the rejected sequence. Execution still checks the ordinary global dead/forced/
earliest-generation scheduler before each base constituent. A nondead endpoint
is an unresolved continuation, not a full solution.

The empty-domain leaf is valid only under its exact prefix, required set and
positive-support envelope. It is an analytic proposal filter, not GCTS learning
or a base-candidate exclusion. A fixed-region leaf cannot become a universal
point marking without a further proof. Whole-state keys include assigned zero,
point totals, ownership, selected poses, roots, generations and the scheduled
domain; the frozen compiler enforces inventory and envelope compatibility.
Exact copies protect rollback. Interrupted validation cannot install a partial
endpoint cache entry.

A new zero-start policy trains for \(24\) rollouts using the filtered proposer;
eight complete. Evaluation seeds start at \(102000\) and are disjoint from
donor/training seeds. Both RL lanes share the same frozen policy. Five matched
lanes solve the same four authored boundaries with two replicas, \(8000\)
explored base placements and six cooperative seconds per request. Base search
completes all eight, compiled and filtered proposals seven each, and both RL
lanes six. Mean request times, including unknowns, are respectively
\(0.425\), \(1.557\), \(1.683\), \(2.430\) and \(2.466\) seconds. Filtered
untrained/RL lanes reject \(17/76\) dead multi-move offers, including cached
repeats; these are not counts of unique failure certificates.

The seven matched completed compiled/filtered pairs take \(6.453/7.462\)
seconds and \(504/484\) base attempts. The six matched completed RL pairs take
\(7.431/7.719\) seconds and \(622/550\) attempts. The filter reduces attempts
but increases total time in this batch. Unknown cases have no negative proof.
Earlier pilots use different libraries and seeds and are not timing controls.

A separate atomic-tile control uses the singleton, both children and the parent
as candidates, with exactly the same geometries in free/marked versions. It has
aggregate steps rather than the singleton macro scheduler, with \(4000\) nodes
and six seconds. Each version completes three of four targets. Mean request
times are \(2.411/2.700\) seconds, with \(209/239\) nodes and \(93/118\)
backtracks. Separate inventory construction costs \(1.381/2.204\) seconds.
The learned marking produces no speed or backtrack advantage here.

Cold costs include \(0.215\) seconds for the singleton inventory, \(1.256\)
for donors, \(0.057\) for mining and \(0.398\) for proposal compilation.
Child/parent complete catalog, label/synthesis and first independent proof
replay stages take \(313.473/97.252\) seconds. Policy training costs \(7.809\)
seconds. The complete sequential process takes \(515.244\) seconds and peaks
at \(884.89\) MiB; this is process peak, not per-lane allocation.

`audit_failure_interfaces.py` independently re-enumerates both literal contact
catalogs and replays their online histories, all \(17134\) negative proof nodes,
\(72\) positive witnesses and \(35256\) scalar symmetry contacts. It checks
\(80\) saved states, \(690\) scheduled base moves, \(30\) sampled fixed-boundary
failure leaves and \(96\) transformed aggregate expansions. \(56\) states
complete their targets. All \(40\) displayed complete evaluation patches pass
exact polygon non-overlap. The saved-data audit takes an additional \(259.375\)
seconds and rejects \(102\) altered prefix schedules/leaves, plus four altered
stage proofs. Source, helper, test and full stage-artifact hashes are recorded.
The report copies two checked positive samples directly from their hashed stage
files for initial display; full contact histories load only on inspection.

```sh
python3 research/gcts-rl-renewal/run_failure_interfaces.py
python3 research/gcts-rl-renewal/audit_failure_interfaces.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test_*.py'
```

All \(131\) semantic tests pass. Eight new controls exercise known-dead macro
removal with all singleton fallback, literal contextual proof checking, tampered
point/pose/envelope rejection, boundary scope, exact rollback, assigned-zero
cache versions, cancellation and unknown budgets. The known-dead regression
fixture uses the preceding published run only in tests; cold discovery/training
never loads it. Earlier source-hashed modules and artifacts are unchanged.
The next research gate is joint continuation of the positive variable-size
assemblies and useful boundary-conditioned responses, measured by total solve
cost. Practical acceleration, compatible plane growth, Penrose hierarchies and
general proof search remain open.

## A marking-guided case proof and a logical hierarchy bridge

`hierarchy-bridge-001.json` explicitly reuses the preceding five-turtle shape,
its verified palettes and all seven positive self-contacts. Acquisition and
prior proof costs remain recorded; no earlier policy or completion enters a
new search. Those contacts produce four distinct ten-turtle types. Each has
two descending child maps to disjoint five-turtle parents, inherits their
channels and has a free level-three channel.

The marked five-parent root graph has an empty domain at
\(p=(-10,2,8)\), where its occupancy is \(8/12\). That is a proof suggestion,
not an unmarked conclusion. An independent unmarked parent-only scan at this
point includes all orientations and positive-support alignments and finds
\(17\) capacity-legal, ownership-disjoint covering placements. Every pose
matches a previously searched negative parent contact. Replaying their full
unmarked base-corona trees checks \(153\) proof nodes.

Assume a complete point tiling using only the five-turtle parent and its
allowed transforms. A used parent normalizes to the root. Its partial point
needs a further parent from that exhaustive domain. Each possible root pair
has a complete unmarked base failure tree, so no complete base extension can
contain it. This contradicts the assumed complete tiling. The contradiction
uses directly checked unmarked certificates; it does not rely on treating
learned markings as universal rules. All twelve transformed/translated case
domains agree exactly with the normalized cover.

Every complete point tiling by the four ten-turtle types would refine into
a complete tiling by the five-turtle parent. Point contributions sum exactly,
allowed transforms compose, and the two child owners are disjoint within
and across the declared aggregate placements. The parent-only obstruction
therefore rules out that entire ten-turtle library too. These are explicit
analytic lifting arguments over executable finite checks. They do not refute
the base turtle, a finite region with singleton refinement, or a different
coarse library. They are not an internal formalization of infinite sets or
a geometric faithfulness theorem.

Fifteen coarse controls use each root in free coarse, marked coarse and marked
coarse-plus-singleton inventories. Every active type is explicitly declared;
auxiliary child definitions never enter candidate domains. Root compilation
removes only placements already incompatible with the immutable root. The
complete graph implements global dead/forced/earliest-generation decisions.
Every branch copies exact state and incidence; new source exports actual
scheduled steps, attempted base constituents, graph peaks, removal reasons,
construction cost and complete failures. The independent oracle rebuilds all
domains before every exported move. All limits yield unknown, never a proof.

With \(4000\) nodes and \(15\) cooperative seconds, the free five-parent gate
remains unknown at \(16.304\) seconds, while the marked gate has a one-node
failure in \(0.247\) seconds. A complete update can overrun the wall limit.
This is not a finite-search equivalence or equal-success speed ratio: learned
constraints can strengthen finite coarse-corona requirements, while the case
proof separately establishes the complete-point obstruction. The free joint
ten-type gates prove two root failures and leave two unknown; every marked
ten-type root fails immediately. The short marked trees total five nodes;
free negative trees add three. Saved unknown prefixes are not plane witnesses.

Aggregate singleton fallback completes the five-turtle root support in
\(5.172\) seconds but leaves all four ten-turtle root supports unknown.
A separate fresh fine-only process expands the same fixed roots into base
seeds at generation zero, imports no completion, and uses every base candidate.
All five supports complete with viable exposed obligations in
\(0.522,0.734,0.741,1.288,1.320\) seconds respectively. Total fine response
and first replay cost is \(5.645\) seconds. The root's cluster channels cannot
restrict future unmarked base tiles, which assign no such values. All
\(107\) new moves are independently re-applied with the original marked
aggregate root and literal fine scheduler. These are response-cost controls
for identical fixed point boundaries, with different inventories and step
sizes, rather than identical traces or a general speed claim. Learning when
to change resolution is now a concrete practical target.

The logical bridge binds three externally checked geometric lemmas:
\(\operatorname{Plane10}\Rightarrow\operatorname{Plane5}\),
\(\operatorname{Plane5}\Rightarrow\operatorname{CoveredRoot5}\), and
\(\neg\operatorname{CoveredRoot5}\). These predicates describe existence in
the explicit coarse systems and the normalized extension case; their semantic
binding is checked by the case-cover/refinement code and analytic lifting.
The existing kernel checks the propositional assembly of
\(\neg\operatorname{Plane5}\) and \(\neg\operatorname{Plane10}\).
The geometry proofs remain external to the literal finite fact-tape machine.

The externally fixed envelope has \(15\) formulas and \(14\) independently
enumerated inference relations, with three irrelevant control facts. Two
literal machines use \(236/237\) states and \(1052/1054\) transitions.
All proof rectangles have \(12\) unknown command slots, \(34\) columns and
\(1536\) transition rows. A new policy practices on the same two assertions
for \(48\) episodes; all succeed. Both learned-proposal lanes find checked
rectangles for both assertions, while no-proposal lanes remain unknown at
\(100000\) attempts and three cooperative seconds. This is same-assertion
practice, not held-out mathematical generalization.

The supplementary `hierarchy-proposal-control-001.json` uses a new zero-weight
process, no training and the same evaluation seeds. It also finds both
accepting rectangles. Thus proposal preferences help this bounded certificate
search, but the batch supplies no learned-policy advantage. That control ran
alongside the expensive research audit, so its times are not matched latency
comparisons. Analytic neighbor values are separately labeled redundant Wang
constraints; they are not geometric marking learning.

The main sequential search/training/first-replay process costs \(231.984\)
seconds and peaks at \(2274.31\) MiB. The supplementary zero-weight process,
including its own two rectangle checks, costs \(4.492\) seconds and peaks at
\(185.59\) MiB. The full independent hierarchy audit costs an additional
\(773.207\) seconds and peaks at \(4149.72\) MiB. All are process peaks,
not per-lane allocation. Complete literal coarse domains are expensive to
construct and verify; this implementation is not a practical broad solver.

The audit checks \(17\) base cases, seven positive promotion contacts, four
refinement types, \(12\) case-cover symmetries and \(192\) transformed
expansions. All \(15\) aggregate states and \(39\) scheduled coarse moves
replay, as do the five fine-only responses. The logical rule catalog and all
\(48\) training sequences reconstruct. Four main Wang rectangles contain
\(208896\) independently checked cells; the zero-weight process checks two
more rectangles. \(18\) altered cases, source premises, schedules, targets
and fact boundaries reject. All six completed response patches pass exact
polygon non-overlap. Displayed case certificates are exact copies from their
hashed source contacts.

```sh
python3 research/gcts-rl-renewal/run_hierarchy_bridge.py
python3 research/gcts-rl-renewal/run_fine_refinement.py
python3 research/gcts-rl-renewal/audit_hierarchy_bridge.py
python3 research/gcts-rl-renewal/run_hierarchy_proposal_control.py
python3 -m unittest discover -s research/gcts-rl-renewal -p 'test_*.py'
```

All \(139\) semantic tests pass. Eight new controls cover complete case
coverage, omitted/duplicate cases, strict pose data, corrupted lower proofs,
positive/wrong-point premises, disjoint refinement maps, literal marked
domains and rollback, unknown budgets and logical fact binding. Earlier
source-hashed modules and published artifacts are unchanged.
The next practical gate is boundary-response and resolution selection under
the fine scheduler. The broad proof program still needs a fixed unbounded
serialized-syntax checker, checked infinite theory schemas and internal
geometry definitions. Base plane coverage, Penrose hierarchy and general
computational proof search remain active.

## Iteration 15: exact local responses and a resolution policy control

<code>boundary_responses.py</code> introduces sampled local operations with exact
incoming and outgoing occupancy. A response records every point of
\(U_C=\operatorname{supp}t_C\), including explicit incoming zero, an ordered
distinct base expansion, its aggregate contribution and descending child maps.
This implementation is explicitly unmarked. Occupancy traces are not learned
GCTS equality markings, and the sampled atlas is not a complete solution relation.

The finite composition law is
\[
R_C:b_C\mapsto b_C+t_C,\qquad
b_B=b_A+t_A\text{ on }U_A\cap U_B,\qquad
t_{A;B}=t_A+t_B.
\]
The combined input uses \(b_A\) on \(U_A\) and \(b_B\) elsewhere in \(U_B\).
Children must have disjoint base owners. Positivity and the checked final
capacity bound imply capacity legality of every ordered prefix. Direct point
expansion and the two parenthesizations of compatible operations agree.
These are analytic finite-operation arguments with executable checks; they
do not establish extension to a far boundary or a universal geometric theorem.
Retaining only a geometric outline would omit possible interior conflicts.

Sixteen fresh local completions, with no imported marking, donor, completion
or policy, provide \(40\) connected responses of \(2,3,4,6,8\) turtles.
Mining considered windows up to \(12\), but no such large selected response
occurred. Their closure has \(187\) nodes and \(228\) child maps. The complete
resident envelope contains \(8436\) base poses. Template lookup first uses
the exact first-tile input trace, then checks all remaining support and owners.
It can reuse an operation when unrelated remote data change; that does not
authorize a globally unscheduled move.

Each search starts with every required point, including untouched zero.
All lanes use the same complete singleton incidence graph, generation-zero
root obligations, global dead/forced/earliest-generation scheduler, copied
exact state and graph rollback, \(4000\) explored base moves and six cooperative
seconds. Response proposals never supply degrees or remove singleton choices.
Internal local capacity is validated when the atlas is built. At execution,
every constituent passes the current global scheduler; a mismatch closes
the proposal at its legal prefix. Unlike the older compiler, it does not
construct another complete graph to prevalidate each whole response.
That changes the proposal/exploration relation, so it is not an equivalence
optimization of the earlier macro benchmark.

The main two-replica, six-target batch reports:

| Lane | Checked exact requests | Total request seconds | Explored base moves |
| --- | --- | --- | --- |
| Base | 9 / 12 | 22.304 | 3274 |
| Same response shapes, aggregate capacity only | 5 / 12 | 49.431 | 7520 |
| Trace-matched responses up to four tiles | 10 / 12 | 20.272 | 2190 |
| Full hierarchy, zero-weight policy | 7 / 12 | 39.505 | 5503 |
| Full hierarchy, move-ranking RL | 6 / 12 | 39.838 | 4406 |

Compact responses solve two base-unknown requests and miss one base success.
On the eight shared completed requests, base costs \(3.634\) seconds and
compact responses \(6.019\). Thus the mixed overall outcomes are not an
equal-success speed ratio. Capacity-only proposals interrupt \(4193\) times;
many execute only one constituent. A valid local operation can be a poor
global search action, and duplicate stopped prefixes need further work.
The fresh move-ranking policy completes \(14/48\) local rollouts. It supplies
no improvement over its zero-weight control. Shapes may recur; distinct seeds
and changed target placements are not unseen-shape generalization.

Main sequential cost is \(241.318\) seconds, peak \(362.95\) MiB. Donors cost
\(4.074\) seconds, mining \(0.390\), and policy training \(26.829\); each atlas
build and the cold \(0.407\)-second universe are separately exported. These
are process costs and peaks, not per-lane allocation. Unknown cutoffs carry
no negative certificate. Heuristic exhaustion is explicitly uncertified.
The movable-boundary control remains an existential finite family of three
authored targets, with every earlier attempt preserved.

<code>response_resolution.py</code> is an adaptive follow-up designed after
observing the main failures. It reuses only the explicitly hashed atlas and
starts a new policy. One REINFORCE decision selects base, compact or hierarchical
proposals before each full request. Problem features use only the externally
declared required set and exterior. Choosing base avoids response lookup;
the upfront library and learning costs are still charged. It does not adapt
a stalled prefix or refine an aggregate candidate inventory.

Forty-two fresh full-search training runs on seven declared boundaries cost
\(36.241\) seconds. Evaluation uses new seeds, three rotated paired lanes and
the same six target definitions. Base and the learned controller both finish
\(11/12\); the learned controller chooses base for every request. Their
completed semantic paths match. Uniform zero-weight ties choose base three
times, compact six and hierarchy three, finishing \(12/12\). The controller
misses the difficult notched replica where a compact zero-weight choice
succeeds. This experiment establishes no learned-policy superiority.
The follow-up process costs \(103.751\) seconds, peak \(333.61\) MiB, plus the
explicit reused donor/mining cost. Audits did not run beside either search
process. This adaptive design is not an independent validation of the earlier
hypothesis, and elapsed cutoff paths can differ between equivalent base runs.

The independent main audit reconstructs \(187\) local operations, \(42\)
donor occurrences, \(480\) transformed expansions, \(148\) saved states and
\(1638\) scheduled moves. Sixteen full literal domains equal the incremental
graph. Missing input, boolean capacity, altered output, duplicate ownership,
wrong child maps, generations and schedules reject. The supplementary audit
also reconstructs the entire on-policy weight update history independently
from recorded rewards, declared features and seeded choices, and checks
every saved controller schedule against the literal full inventory.
Geometry remains an illustration of point data; this batch does not add a
new polygon faithfulness theorem. These finite laws are possible proof-block
interfaces, not an internal formalization of infinite tilings.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_boundary_responses.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_response_resolution.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_boundary_responses.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_response_resolution.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test_*.py'

Eleven new response tests cover composition, associativity, all symmetries,
strict input/output data, owner maps, complete domains and fallback, exact
transactions, local reuse versus remote dead obligations, unknown budgets
and zero-policy semantic equivalence. Three new controller tests cover
externally declared features, independently reconstructed resolution choices
and fresh initial policy state. Earlier source-hashed modules and artifacts
are preserved. The next practical gate is avoiding identical stopped-prefix
work and selecting resolution from the current boundary rather than a whole
request alone. The broad proof checker, Penrose hierarchy and plane coverage
remain open.

## 16. Fixed serialized checker, induction and exact logical blocks

The fixed program in `serialized_kernel.py` reads UTF-8 JSON bytes under
`gcts-fol-1`. The protocol contains a signature, closed finite theory axioms,
registered schema names, ordered block declarations, a root proof and its
target. It has no compiled formula catalog, variable-name envelope, prescribed
arity or semantic term-size bound. The host parser and checker still have
native resource limits; explicit byte/work limits and native recursion or
memory exhaustion return `unknown_resource_budget`. A rejected certificate
is not evidence that its target is unprovable.

The primitive logical rules independently implement those of `logic.Kernel`:
closed axiom membership, propositional tautology, reflexivity, universal
instantiation, universal distribution, equality substitution, modus ponens
and generalization. Substitution renames bound variables using the same
deterministic fresh-name convention, separately implemented. Unknown fields,
duplicate JSON keys, floats, nonfinite numbers, booleans in integer positions,
malformed syntax and nonprior proof references reject. Proof data is never
executed. Source-hashed earlier modules are unchanged.

The explicitly enabled `nat-induction` schema requires the declared zero and
successor signature. Each formula instance is constructed from its submitted
template, with capture-avoiding substitution and universal closure of all
other free variables. This is an axiom assumption of the declared theory,
not a theorem about arbitrary interpretations. The authored example checks
\(\forall n\;(0+n=n)\) from the two recursive addition axioms and induction.
It does not discover that theorem. One registered infinite schema is now
implemented; arbitrary effective theory-schema interpreters remain open.

A block is an exact interface \(\Gamma\vdash\varphi\), with an explicit proof.
It may assume only its declared premises and call previously checked blocks.
Call arguments must be equal to those premises, and its conclusion must match.
All declarations are checked, including unused ones. Generalization is
permitted only for a variable absent from the premises' free variables.
The arithmetic response receives the closed recursion axiom, then derives
its open successor case internally; declaring that open case as an input
would permit an invalid generalization and is rejected. Blocks currently
have exact formulas, not schematic instantiation for arbitrary new inputs.

Callers may pin `problem_hash(request)` via `expected_problem_sha256` to bind
the protocol, theory and target while allowing changes to the proof and
blocks. Five binding controls include three proposals that accept relative
to their changed problem but reject against the original pin. Unpinned checks
are relative to the supplied declaration and do not authenticate user intent.

The saved batch has \(25\) positive certificates, \(24\) adversarial
rejections, and all \(771\) formulas in the declared two-atom grammar with at
most five AST nodes: \(184\) tautologies and \(587\) nontautologies. Names,
arities, capture avoidance, induction parameter closure and generalization
side conditions have separate probes. Two valid proofs return unknown under
explicit limits. The five problem-binding controls and eight repeated-use
certificates bring the independent replay total to \(835\), with \(5099\)
expanded primitive lines. A separate test forces native JSON-depth exhaustion
and checks that it remains unknown. The full research suite passes \(166\)
tests, including thirteen new tests.

`audit_serialized_kernel.py` does not import the new checker or certificate
generator. It independently decodes the data, checks all interfaces and
schemas, then expands each block and root into the frozen earlier kernel.
To check an open-premise block in that closed-axiom oracle, it temporarily
universally closes and instantiates its premises, while separately enforcing
the eigenvariable restriction against the original open premises. Such
temporary local axioms do not enter the root expansion. The two reused
coarse-obstruction assemblies are hash-bound to `hierarchy-bridge-001.json`;
their geometric lemmas remain external axioms with the earlier case proofs
as provenance. This turn does not reprove those geometry certificates.

The representation control deliberately repeats the same authored lemma.
Five sequential cold checks alternate encoding order and include parsing,
theory and block validation. A single call is slower and larger with blocks:
\(0.723\) versus \(0.547\) milliseconds, \(9201\) versus \(6723\) bytes.
At \(128\) identical uses, blocks check \(153\) stored lines in \(1.878\)
milliseconds and store \(27870\) bytes. The same primitive expansion checks
\(1796\) lines in \(66.514\) milliseconds and stores \(705377\) bytes.
These measurements establish a representation benefit on identical reuse,
not search acceleration, new-theorem generalization or learned abstraction.
The sequential control process costs \(0.654\) seconds, peak \(39.94\) MiB;
full independent expansion is a separate \(0.200\)-second cost.

The fixed effective inference algorithm suggests an abstract semidecision
procedure by dovetailing finite certificates and resources. This enumeration
argument is not a practical search result or a semantic completeness proof.
The checker remains a Python host implementation. Its literal Turing-machine
translation, compiler correspondence with the Wang point model, machine-checked
kernel soundness, internal geometric theories, and learned proof-block search
remain open. No point-search engine or marking is changed in this batch.
Proof blocks are possible logical counterparts of tiling response interfaces,
not yet geometric tiles or a new GCTS elimination channel.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_serialized_kernel.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_serialized_kernel.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test_*.py'

## 17. One literal interpreter, programs as data and source-machine simulation

`uniform_stack_machine.py` constructs one literal tape machine without any
program or input argument. Its exported table has \(69\) states, \(40\)
tape symbols and \(1208\) transitions. All saved controls have the same
table hash. Program records, unary addresses and two binary stacks are tape
data. The runner executes literal table lookups, writes and head moves;
decoding instruction checkpoints is observation and does not select a
transition. The existing Wang compiler represents the complete fixed
inventory of \(10892800\) local triple types symbolically.

`stack_program.py` supplies a separate operational reference and general
finite-Turing-machine translation. Instructions are four bit pushes, two
pops with empty/zero/one branches, a jump and two terminal commands. Addresses
are natural numbers. Executing an address outside the program rejects;
unreachable dangling addresses are legal. Every record must have valid
grammar, including unused records. Invalid syntax rejects; valid execution
that exhausts stack capacity or steps returns unknown.

The literal tape begins with two blanks, the start head on `L`, program
records, `#`, left bits and padding, `|`, right bits and padding, `$` and
two blanks. Each stack has a contiguous bit prefix followed only by `P`.
At every fetch, the program and all temporary address marks are restored.
An active opcode selects a stack action and branch; its address cursor marks
one unary unit while a target marker advances one complete record. Restoring
the cursor and target yields precisely the next instruction boundary. A
successful terminal erases the workspace and returns an accepting head on
`L`, giving a fixed accepting row for the declared tape width. The saved
checkpoint immediately before cleanup retains the final stack configuration.

For a source alphabet \(\Gamma\), the translation uses
\(w=\max(1,\lceil\log_2|\Gamma|\rceil)\) bits per symbol; blank is zero.
At each source-state entry, both stack lengths are divisible by \(w\).
The left top encodes the nearest symbol left of the head; the right top
encodes the current symbol. Codes pop most significant first. Empty whole
blocks read as blank, and unused codes reject. After reading the current
symbol, a right move pushes the written symbol left; a stationary move
pushes it right; a left move pushes it right, reads the left top and pushes
that as the new right top. These cases preserve the entire relative source
tape, with implicit blank tails. Intermediate bit prefixes are not source
configurations. Induction on source steps gives an analytic correspondence
argument. Each finite accepting source execution fits sufficiently large
finite stack capacities and time. The fixed inventory thus has general
computational expressiveness over the family of such finite boundaries;
this is not a formally verified compiler theorem or an unrestricted
checker port. A fixed capacity alone cannot simulate arbitrary executions.

The sequential batch checks all \(225\) pairs of binary words through
length three, \(21\) operation controls and \(8\) serialized-term byte
comparisons. The latter perform equality only: they do not validate ASTs,
signatures, substitution, schemas or inference. Five source tables cover
right/left/stationary moves, extending blank tape, nonbinary symbol alphabets,
undefined transitions and the earlier unary addition machine. Five malformed
inputs include unused bad records and a padding hole. These are authored
implementation controls, with no learned policy or theorem discovery.

The addition translation has \(286\) instructions and \(56219\) program
bytes. Its source execution and the full operational stack reference agree,
but the literal interpreter remains unknown at \(5000000\) steps. Three
smaller positive source controls complete; the undefined-transition control
rejects. Unary address operands can make program size quadratic in the
instruction count and repeated lookup expensive. Compact addressing and
measured reusable operations are a practical gate before porting the full
first-order checker. This batch is computational infrastructure, not a
practical proof-search acceleration.

Three authored Wang component problems use a clamped program, declared
stack layout and accepting top; two permit one unknown bottom bit. Rotated
lanes compare standard colors, analytic redundant neighbor point values,
and an authored trajectory preference retaining all alternatives. Each lane
has \(20000\) attempted placements and a cooperative \(4\)-second bound.
Base search finishes none of the three within this budget. The other lanes
each finish all three, giving six checked rectangles and \(34794\) point
cells. Analytic neighbor values are not learned GCTS markings. Supplied
trajectories are calibration controls, not learned proposals or evidence of
RL superiority. Unknown searches have no negative proof.

The unchanged symbolic engine maintains the complete center/candidate graph
with implicit one-center reverse incidence, all color dependencies, global
dead/forced precedence and exact trail rollback. All centers are initial
generation-zero roots, so generation priority ties throughout; its spatial
tie order is preserved. Tests check full domain restrictions and transaction
fingerprints against this table. These specialized deterministic-computation
rectangles preserve the earlier engine semantics; no turtle or Penrose
engine, policy, markings or source-hashed earlier module is changed.

`audit_uniform_machine.py` does not import the new instruction reference,
translator, interpreter or generator. It independently parses records,
executes the exported literal table, decodes each fetch and compares source
configurations. It checks \(259\) runs and \(3093\) fetch boundaries, five
raw grammar controls and twelve exhaustive finite symbol-domain restrictions.
The full inventory count is derived analytically from disjoint head-position
cases. Each accepting rectangle is independently bound to its external
program, stack layout, bottom pattern and top before the frozen point checker
and a separately implemented local transition check. Program, top, pattern,
grid and instruction-checkpoint mutations reject. All six rectangles replay.
The new audit and reused helpers are source-hashed; the main experiment also
binds the source-checkpoint helpers it invokes as control assertions.

The complete sequential process costs \(9.467\) seconds, peak \(83.89\)
MiB, including the limited addition execution and all rectangle requests.
Table construction costs \(0.485\) milliseconds. Independent replay costs
\(5.267\) seconds separately and did not run beside the timed batch. All
\(178\) research tests pass in \(58.869\) seconds, including twelve new
tests for strict data, complete symbol domains, literal row correspondence,
source configuration simulation, all instruction branches, immutable tables,
cutoff semantics and rollback. Counts, raw timings, limits, traces, source
tables and hashes are exported in `uniform-machine-001.json`.

The visual report shows actual saved instruction boundaries and their stacks,
decoded source configurations only at source-state entry addresses, and the
literal tape rows recovered from checked Wang point certificates. A finite
accepting computation rectangle is not a plane-tiling theorem. The complete
serialized logical checker remains in Python; its instruction-language port,
schema implementation, internal geometric theories, formally checked
soundness/simulation, and learned proof blocks remain open. Practical tiling
research also still needs current-boundary resolution and avoidance of
repeated stopped prefixes. Substitution remains optional.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_uniform_machine.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_uniform_machine.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test_*.py'

## 18. Relative binary operands, next links and the completed addition control

`binary_stack_machine.py` constructs another fixed literal interpreter, with
\(119\) states, \(47\) symbols and \(1899\) transitions. No program or input
enters construction. Both compact encodings use this same table and its
\(29112411\) symbolic Wang types. Earlier source-hashed modules, inventories,
artifacts and semantics are preserved.

The instruction tuples still use absolute natural targets. `binary_program.py`
encodes each operand as a signed binary displacement from its instruction
index. At record \(i\), the resolved target is
\(j=i+\operatorname{sgn}\cdot\operatorname{value}_2(b)\). Literal `>` and `<`
introduce nonnegative and negative distances. Digits have no leading zeros;
negative zero is rejected. An optional literal `n` denotes \(j=i+1\).
The parser also gives operational semantics to signed targets past the first
record; unused ones are legal, while executing an out-of-range target rejects
when enough resources are available. The host encoder still accepts only the
original absolute-natural instruction tuples. All generated source-machine
programs have that original semantics.

The tape adds an `A` delimiter and empty scratch padding between program and
the unchanged `#`/left-stack/`|`/right-stack/`$` layout. A signed jump copies
its magnitude into scratch, records the direction in the delimiter, marks
the current opcode as its initial target, then decrements and moves one whole
record in that direction. It erases scratch and restores the direction,
operand and target marks before each fetch. A next link restores the active
opcode and scans straight to the next record, without scratch. These cases
preserve the two-stack semantics and the earlier general source-TM simulation
at its state-entry addresses. This is an analytic correspondence argument
with independent executable evidence, not a formally verified compiler.

Scratch is a declared resource. Its initial contents must all be padding,
and stack bits must precede padding with no holes. Grammar validation includes
unused records. Insufficient scratch or stack capacity returns unknown. In
particular, a jump may run out of scratch before its out-of-range target can
be resolved. Separate controls check both that unknown and rejection with
enough scratch. Unknown never supplies a negative proof.

This is adaptive engineering following r17's addition cutoff. A development
probe found that changing only to a compact absolute counter still repeated
large prefix scans. The final design uses local signed displacements and
explicit next links. Of the authored addition control's \(240\) instruction
transitions, \(162\) go to the next instruction. Those observations guided
the design; these are not fresh independent generalization controls.

The official batch has \(287\) compact component runs: \(225\) short-word
equalities, \(42\) instruction controls, \(16\) serialized-term byte
comparisons and four scratch/next-link controls. Byte equality still performs
no syntax, signature, substitution, induction or inference checking. Five
source computations are explicitly reused from hash-bound
`uniform-machine-001.json`. Three replicas rotate three lanes: historical
unary, relative binary, and relative binary with next links. Every request
has \(20000000\) literal steps and the same source table, input and stack
capacities. Tables are constructed once; each request starts with a fresh
tape, and per-request time includes layout and encoding. Table construction
is reported separately. All \(45\) requests, including unknowns, are saved.

Both compact encodings accept the addition certificate control, preserving
all \(241\) stack instruction boundaries and \(30\) source configurations
including the terminal state. Relative binary needs \(2017\) program bytes
and \(10838203\) literal steps, median \(2.1691\) seconds. Next links need
\(1737\) bytes and \(7223231\) steps, median \(1.4628\) seconds. The same
new table accepts both data representations. The historical \(56219\)-byte
program remains unknown at \(20000000\) steps, with \(37\) observed
instruction boundaries; its median cutoff time is \(3.8677\) seconds.
There is no complete-runtime ratio against this cutoff. The other four source
controls terminate correctly in every lane, including the expected rejection
of an undefined transition. No learned policy, new theorem or inference is
discovered here. The arithmetic machine checks a supplied unary result for
\(1+1=2\); it remains distinct from the first-order kernel.

Comparing unary with compact also changes the counter location, marker seeks
and interpreter table, so it is not an address-only causal ablation. The
two compact lanes keep the same table and original instruction sequence;
their data encoding and declared scratch need differ. Three small authored
replicas are local engineering measurements, not statistical evidence of
general acceleration, practical proof search or region solving.

The unchanged Wang engine checks the new table on three authored component
problems, with externally clamped programs and accepting tops. Two have one
unknown input bit. Base search finishes none within \(20000\) attempts and
a cooperative \(4\)-second bound. Analytic redundant neighbor values and
supplied authored trajectories each finish all three, yielding six rectangles
with \(26280\) checked point cells. These markings and preferences are
controls, not learned GCTS or RL. New tape widths, heights and table sizes
change the point problems relative to r17; cross-representation rectangle
timings are not a matched search-speed claim.

All required centers have root generation zero and unit occupancy. Complete
symbolic domains retain every permitted base type and all color dependencies.
Global dead/forced checks, spatial generation-tie order and trail rollback are
unchanged. Tests compare full symbolic domain representations on rollback,
without expanding the complete inventory. Tiny exhaustive restrictions agree
with separately computed local rules. Accepting point certificates bind the
program, scratch width, stack layout, input pattern and top externally before
independent checking. They are finite computation proofs, not plane tilings.

`audit_binary_machine.py` imports none of the compact encoder, interpreter,
VM or generator. It independently parses signed operands, reconstructs the
initial layout, executes the literal table, implements stack semantics and
checks source configurations through the frozen earlier sparse-source helper.
It verifies the reused source artifact and all paired inputs. The audit checks
\(317\) compact runs and \(15\) historical runs, \(6920\) total fetches,
\(246\) compact source-state entries, nine raw syntax/layout controls and
twelve exhaustive finite domain restrictions. All six rectangles replay.
Changed scratch width, program, input pattern, top, cell and checkpoint reject.
The main process costs \(38.728\) seconds, peak \(96.08\) MiB; construction
is \(1.053\) milliseconds for compact and \(0.549\) for historical. Independent
replay costs \(33.950\) seconds separately. No audit or tests ran beside the
official timed process. Source, helper, table and reused-artifact hashes are
exported; the full suite record binds the test sources and output log.

All \(192\) research tests pass in \(61.470\) seconds, including fourteen
new tests for relative jumps, canonical syntax, next links, scratch cutoffs,
full source configurations, literal row laws, symbolic domains and rollback.

The direct dense rectangle for the completed addition run would have
\(1850\times7223231=13362977350\) required point centers. That is a calculated
size, not a built or checked dense certificate. A practical next gate is
compressed computation certificates and verified blocks carrying exact input
and output interfaces, with identity regions represented implicitly. Such
certificates and learned computational blocks are not implemented here.
The serialized first-order checker still needs porting, internal geometry
theories and learned proof-block search remain open, and the practical turtle
and Penrose hierarchy objectives continue. Substitution is optional.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_binary_machine.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_binary_machine.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test_*.py'


## 19. Checked computation responses and an implicit headless frame

`computation_blocks.py` is a specialized certificate calculus for the unchanged
fixed literal interpreter. It is not a replacement for the GCTS candidate
engine or an RL proposer. Every input, table and authored source control is
explicitly reused from the SHA-bound `binary-machine-001.json` artifact.
No frozen earlier source, table, marking, search algorithm or artifact changes.

A local block declares an entry/exit state, head displacement, literal duration,
input allowed-symbol sets, constant writes and the full head excursion. Its
semantic interface is

\[
 B:(q,h;\ a_p\in P_B(p))\longmapsto(q',h+\delta_B;\ a'_p),\qquad
 a'_p=\begin{cases}W_B(p)&p\in\operatorname{dom}W_B,\\a_p&\text{otherwise}.\end{cases}
\]

Missing conditions are unrestricted, whereas an explicit symbol index zero is
an assigned write. Primitive leaves cite a literal transition. Copy-sweep
leaves collect all symbols for which the table proves
\(\delta(q,a)=(q,a,d)\), with \(d\in\{-1,1\}\). Every visited cell must
have an eligible symbol. The tape is preserved and the head ends at
\(h+nd\) after exactly \(n\) steps. These are proved table consequences,
not learned point markings. Symbolic input sets express disjunctions; their
concrete instantiations still use the exact original Wang equality values.

A parent checks state equality, translates its next child's requirements by
its current head displacement and substitutes earlier constant writes. A
later read of a written cell must admit that symbol; otherwise input sets
intersect. Empty intersections reject. Constant writes equal to a singleton
input condition can be removed. Intersections and substitution compose exact
local responses, with the entire head excursion retained. Every declaration,
including an unused one, is checked. Backward-only references exclude cycles.
Interfaces are derived from bodies, and exported observations are compared
with those derivations. The root binds the full initial/final tapes, table,
step count, terminal status and limit. A caller can pin that external problem
hash. Without a pin the API checks the submitted declared problem.

The headless radius-one law \(F(a,b,c)=b\) supplies the implicit frame.
At each operational step, at most three neighborhoods contain the unique
head. Their Wang cells match the literal transition; every other north symbol
is its unchanged south symbol. The head remains strictly inside the two blank
outer columns. Thus a checked response has an implicit finite expansion into
all the ordinary Wang cells, with unit center occupancy and agreement of
horizontal/vertical marks. Composition is an analytic proof by induction on
this finite DAG. The Python checker has no machine-checked soundness theorem.
The large expansion is not materialized; three small responses are explicitly
expanded and independently checked as ordinary point certificates.

The official batch checks all \(287\) earlier compact component controls,
five earlier source computations using the next-link representation, three
point-certificate controls and three addition prefixes at limits
\(0,100,5000\), yielding \(298\) responses. Time, stack, workspace and
blank-frame cutoffs remain unknown; they supply no accepting proof. The source
programs and all their full input/output bindings are checked against the
preceding artifact. The arithmetic control still checks an authored unary
certificate for \(1+1=2\), rather than discovering a theorem or executing the
serialized first-order kernel.

The completed addition response represents \(7223231\) literal steps with
\(24631\) distinct declarations and \(47714\) sequential tokens. The DAG
request has \(918515\) bytes, including tape boundaries and observed
interfaces. The flat copy-sweep request has \(1231459\) bytes; the literal
replay request has \(15082\) bytes and pays for executing the table.
The implicit dense rectangle has
\(1850\times7223231=13362977350\) required point centers. Its compressed
accepting certificate now checks through the response calculus and the Wang
row laws; this is distinct from constructing those billions of point objects.

Five source controls each have three replicas rotating literal replay, flat
sweep checking and fresh DAG interface checking. Every timed call parses a
fresh serialized request and binds the same complete computation. Addition's
median check times are \(0.0725\) seconds for flat sweeps, \(0.6971\) for
the DAG and \(1.6111\) for literal replay. The smaller DAG is slower
than the flat certificate in this control. DAG construction costs
\(2.167\) seconds separately, so a checking benefit does not establish an
end-to-end benefit for one use. The generation/benchmark stage takes
\(20.494\) seconds, peak \(207.80\) MiB; artifact writing and independent
verification are separate. No audit or tests ran alongside the final timed
stage. Development probes adjusted interval composition and resource handling
before this final run; these reused authored cases are not an independent
learning/generalization test.

`audit_computation_blocks.py` imports none of the new producer, verifier or
flat control. It derives each interface by cellwise symbolic substitution,
rather than the production interval algorithm. It binds every earlier input,
output, limit, table and component catalog; replays all literal computations;
checks all declarations and observed interfaces; expands the small point
certificates; and rejects changed bodies, cycles, boundaries, durations,
sequential traces, tables, interfaces and unused declarations. The frozen
literal and Wang helpers are explicit source-hashed dependencies. Exhaustive
headless, transition-neighbor and accepting-neighbor checks connect the
certificate semantics to the actual unchanged radius-one implementation.

The final independent audit passes \(298\) controls and \(219269\) declarations, representing \(14395227\) literal steps and \(529392\) sequential tokens. All literal replays agree. The three dense controls contain \(13140\) checked cells. Wang row laws exhaust \(103823\) headless triples, \(4194891\) transition/neighbor pairs and \(103823\) accepting triples. Ten changed certificates reject. Independent audit time is \(39.714\) seconds, including the row-law checks.

All \(208\) research tests pass in \(64.387\) seconds, including sixteen new tests for symbolic substitution, all small copy-schema concretizations, translated frames, actual dense point expansion, associativity, zero-valued writes, input conflicts, invalid/unused declarations and resource limits. The artifact binds every test file and the successful suite log.

This milestone provides an inspectable local response and composition system
for finite computations. It does not change any search candidate set, markings,
generations, dead/forced precedence or rollback, and runs no compressed GCTS
search. Its measured verification benefits are separate from proof-search or
practical region-tiling acceleration. Exact symbolic paths can overspecialize
an input, and repeated interface derivation can cost more than an efficient
flat check. Useful learned block discovery, selective reuse, the full logical
checker port, internal geometry, current-boundary turtle decisions and Penrose
continuation remain open. Substitution remains optional.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_computation_blocks.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_computation_blocks.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py'

## 20. Resolve responses at the current frontier; visit each base child once

`frontier_responses.py` returns to practical turtle region solving. It explicitly
reuses notebook 15's SHA-bound unmarked response atlas, without importing any
earlier policy or markings. No frozen engine, geometry, atlas or artifact changes.
This is an adaptive engineering follow-up on the six earlier declared targets;
new seeds do not make these independent boundary-generalization controls.

The previous traversal treats every response and singleton as a separate DFS
action. Several actions can share the first key, execute only that first move
and then explore the same child again. The new traversal groups proposals by
their first base key, selects a preferred suffix for each and visits each base
child once. At later states, a pending suffix orders the actual selected base
domain, retaining every other alternative. This is an analytic reorganization
of complete base search, not learned pruning. It changes macro branching
granularity and order, so it is not a same-path caching ablation.

All mutable graph obligations remain base tiles. Global dead checks precede
forced moves and earliest-generation branching; candidate count only breaks
generation ties. Every response constituent is revalidated against that full
graph. A mismatching forced or branch domain closes the suffix. Exact state
and graph copies implement rollback. Atlas proposals never alter domains,
marks, generations, the required set or the admissible support envelope.
All singleton alternatives survive full evaluation. A cutoff is unknown;
finite exhaustion without an independently checked tree is uncertified.

At each fresh branch, the controller chooses base, compact responses of at
most \(4\) constituents, or the full sampled hierarchy of at most \(12\).
It sees actual remaining obligations, domain degrees, contact with already
placed support, accepted tiles and recent per-mode interruptions. The learned
policy also ranks proposals. Interruption records bind the complete ordered
prefix and the declared boundary, rather than only a local trace. These exact
context hashes are diagnostics and never become exclusions or a cache of
negative facts. The controller is not restricted to a supplied tiling strategy,
but this batch's available multiscale responses are the previously mined atlas.

The discrete boundary-solution analogy separates local solving, interface
compatibility and scale selection. For occupancy scaled from twelfths,

\[
 O_C(p)=I_C(p)+\Delta_C(p)\leq1.
\]

Every positive-support point has an incoming value, including explicit zeros
and interior points. Children require shared input/output agreement and
disjoint base ownership. Thus each atlas entry is an exact local operation
for one incoming trace. It is not the complete relation for every possible
boundary condition. Coarser sufficient interfaces, useful failure markings at
each level, adaptive refinement and compatible coarse continuation remain open.
A stationary substitution is optional.

Fresh REINFORCE starts at empty weights and uses \(48\) single-path rollouts
on seven separate declared boundaries. Training costs \(14.672\) seconds;
\(5\) rollouts complete. Reward is verified required-point coverage plus
completion, minus real base attempts and elapsed cost. A sampled dead path
does not refute its boundary. Full evaluation keeps all alternatives. Two
replicas rotate seven lanes, sequentially, on each of six earlier targets.
Each gets \(4000\) actual base attempts and five cooperative seconds,
including boundary binding, graph construction and proposal lookup.

| Lane | Completed | Total request seconds | Base attempts | Duplicate action children avoided |
| --- | ---: | ---: | ---: | ---: |
| Earlier base | 10 / 12 | 20.514 | 2041 | — |
| Earlier hierarchy | 7 / 12 | 36.124 | 4573 | — |
| Unique base | 10 / 12 | 20.323 | 2082 | 0 |
| Unique compact | 10 / 12 | 27.890 | 3263 | 344 |
| Unique hierarchy | 7 / 12 | 30.257 | 3395 | 433 |
| Uniform current-frontier controller | 12 / 12 | 7.853 | 632 | 149 |
| Learned frontier and ordering | 12 / 12 | 12.871 | 1875 | 0 |

The learned gate chooses base at all \(582\) fresh evaluation branches and
executes no response; its move ranking changes the base order. The uniform
gate chooses base/compact/hierarchy \(76/84/69\) times. Both complete all
twelve requests, and the uniform control is faster on this small reused target
set. On the ten requests completed by both earlier base and uniform control,
base takes \(10.459\) seconds and uniform \(5.797\). This is a useful
ordering observation, not established general acceleration or RL superiority.
Different completion sets in the other lanes preclude an overall
equal-success speed ratio.

Unique hierarchy still completes \(7\) requests. It avoids \(433\) duplicate
action children and explores \(3395\) base moves versus the earlier
hierarchy's \(4573\); these paths and ordering differ. Its \(133\) closed
response attempts include \(116\) interruptions, \(95\) after just one
move. Compact response attempts likewise mostly interrupt after one move.
Grouping fixes duplicate children but does not make those suffixes suitable
for the globally scheduled boundary. No learned marking is synthesized here.

The complete sequential process costs \(187.150\) seconds, peak
\(786.28\) MiB. The full \(8436\)-pose envelope inventory costs
\(0.374\) seconds; the two validated atlas builds cost \(0.364\).
Reused donor/mining costs are explicitly reported in notebook 15. This is
not fresh atlas discovery. No audit or tests run beside the timed process.
Independent saved-data audit costs another \(60.633\) seconds separately,
peak \(204.59\) MiB. Peak memory covers the whole process, not a per-lane
memory comparison; practical memory cost remains material.

`audit_frontier_responses.py` imports neither the new solver, its feature
routines nor its driver. Literal enumeration checks \(144\) saved states
and \(1874\) scheduled moves. All response preconditions and offsets replay;
\(773\) sampled complete parent domains and current-state feature vectors
agree. Six finite-work controls reproduce the full base-only and zero-policy
paths under equal attempt limits, rather than a wall-clock cutoff. Independent
algebra reconstructs all \(48\) updates and \(468\) choices. Random sampling
and all abandoned branches are not independently replayed. The atlas's
\(187\) nodes and \(228\) child maps check; eleven changed schedules,
states, samples, features or weights reject. All \(68\) completed evaluation
patches pass exact polygon non-overlap. No exhaustive negative tree or plane
certificate is exported.

The new semantic controls check unique grouping with every fallback retained,
rejected missing or foreign keys, finite-work path equality, actual complete
domains at every visited test branch, exact parent preservation, unknown
cutoffs, global dead precedence, mutable frontier features and preference-only
learning. All \(217\) research tests pass in \(69.596\) seconds, with every test source and the suite log bound into the new artifact.
The visual report lets readers inspect the actual saved region patch and the
singleton/response constituents at each scheduled step. General region
faithfulness, independent target families, movable shape optimization, Penrose
continuation, plane coverage and useful learned proof blocks remain active.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_frontier_responses.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_frontier_responses.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py'

## 21. Parametric cluster inputs and scheduler-adaptive constituent orders

`conditional_clusters.py` derives a family of local solutions from each
unmarked response in the explicitly reused, SHA-bound notebook 15 atlas.
For a cluster with distinct owners and nonnegative integer-twelfth occupancies,

\[
 \hat\Delta_C(p)=\sum_{c\in C}\hat t_c(p),\qquad
 u_C(p)=12-\hat\Delta_C(p),\qquad
 0\le\hat I(p)\le u_C(p).
\]

Every subset \(U\subseteq C\), hence every prefix of every permutation, obeys

\[
 \hat I(p)+\sum_{c\in U}\hat t_c(p)
 \le\hat I(p)+\hat\Delta_C(p)\le12.
\]

This elementary monotonicity argument proves local capacity legality under
the derived bounds. It does not prove future completion. Bounds cover the
whole positive support, including interior points and explicit zero bounds.
Outside that support the response preserves occupancy. Compatible distinct
children add increments; their sequential translated input requirements
intersect, giving the same aggregate upper bounds. The audit checks every
derived interface and child law. There is no machine-checked implementation
soundness theorem. Marked clusters would additionally require agreement of
all assigned point values. This pilot has no learned markings or exclusions;
the bounds are parametric proposal interfaces, not equality m-values.

The previous atlas offered continuations from the first recorded member.
The new representation compiles every admissible pose of the sampled library
and indexes it by every constituent. A proposal may begin at any member in
the actual selected base domain. Fixed-order controls then follow the
remaining original list; adaptive controls prefer every remaining member in
the actual globally selected domain. A mismatch interrupts the proposal.
Global dead/forced precedence, earliest-generation branching and complete
singleton fallback remain unchanged. Each base key has one child. Branches
copy all state and graph fields and discard failed copies for exact rollback.

The index contains \(480\) transformed templates, \(180240\) sampled-library
poses and \(711924\) member incidences over all \(8436\) base keys. Its
completeness is about this sampled atlas, not all possible clusters. The
selected library's realized cluster sizes are \(2,3,4,6,8\); the declared
full-resolution cap remains \(12\). The two representations of a matching
cluster are deduplicated by exact owners and starting key before offering.
Each query scans at most \(256\) schema instances, round-robin across the
selected base keys and interleaved cluster sizes, and offers at most eight
responses. These proposal quotas never supply base degree counts or pruning.
Trace/fixed, trace/adaptive, interval/fixed and interval/adaptive controls use
the same complete compiled pose index and quota. Fixed/adaptive controls have
identical initial proposal pools at the same state; later paths diverge.
Input broadening changes which poses match, as intended by that comparison.

New fixed targets are a long strip, annular obligations, two lobes, and a
fixed exterior with a distant pocket, requiring respectively
\(149,210,177,129\) points. Seven training boundaries use different strip
widths, ring radii, lobe placements and exterior data. The declarations were
frozen before the official run, after observing r20's interruption evidence.
They are new authored shapes in this research pilot, not a standard independent
benchmark suite or proof of broad generalization. The earlier donor geometry
and finite hierarchy are explicitly reused; no earlier policy or markings enter.

These remain exact point problems. Every required point must reach unit
occupancy, and every positive tile support must lie within the same declared
envelope. The annulus interior has no obligations and permits placements;
it is not a forbidden physical hole. Exterior values and owners are externally
declared. A general continuous-boundary faithfulness theorem remains open.
All required obligations are roots of generation zero; new support and tile
generations follow the unchanged reference rule. The candidate graph includes
every legal base placement and all t/m dependencies, independently of this
atlas. No geometric containment or polygon predicate runs inside search.

Fresh REINFORCE learns both current resolution and validated cluster ordering
from \(48\) single-path rollouts, with verified coverage/completion minus
actual base attempts and elapsed cost. Training costs \(13.286\) seconds;
\(5\) rollouts complete. A sampled dead rollout does not refute its boundary.
Full evaluation retains every base alternative. Two replicas rotate seven
lanes sequentially on the four new fixed targets, each with \(4000\) actual
base attempts and five cooperative seconds, including binding, complete graph
construction and lookup. No audit or tests run beside this timed process.

| Input and execution control | Completed | Total request seconds | Base attempts | Response constituents | Reordered constituents |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base | 8 / 8 | 7.563 | 883 | 0 | 0 |
| Exact trace, fixed order | 8 / 8 | 4.107 | 284 | 15 | 0 |
| Exact trace, adaptive order | 8 / 8 | 3.788 | 243 | 16 | 2 |
| Capacity bounds, fixed order | 8 / 8 | 6.660 | 454 | 214 | 0 |
| Capacity bounds, adaptive order | 8 / 8 | 6.417 | 453 | 213 | 3 |
| Capacity bounds, uniform gate | 8 / 8 | 8.039 | 954 | 318 | 7 |
| Capacity bounds, learned gate and ranking | 8 / 8 | 7.376 | 752 | 288 | 24 |

These constituent and reorder counts cover all explored branches, not just
the saved path. The fresh learned gate chooses the full hierarchy at all
\(204\) fresh fixed-evaluation resolutions; it now executes actual clusters.
It closes \(204\) response continuations, of which \(16\) use the complete
cluster. The interval/adaptive control closes \(196\), with \(10\) complete.
Most broadened responses still interrupt. Both adaptive controls have slightly
lower aggregate request cost than their corresponding fixed-order controls,
but these small engineering measurements do not establish a general speedup.
Exact-trace controls lead on this new set. RL is close to base before adding
its training and pose-compilation costs; no end-to-end learned advantage is
established. Learning a capacity-legal region is distinct from learning a
useful globally scheduled continuation.

Two finite movable families each allow three authored strip positions. All
seven lanes solve both families on their first member. Each member would have
its own three-second budget, and every attempted outcome would be exported.
The controls verify finite-family selection and exact replay but do not test
moving an initially stalled boundary or continuous shape optimization.
Base's two family requests cost \(0.882\) seconds, trace/adaptive
\(0.821\), interval/adaptive \(1.712\), uniform \(0.800\) and RL
\(0.770\), without an inference from these two small requests.

The sequential process costs \(78.561\) seconds, peak \(953.34\) MiB.
Complete sampled-library pose compilation costs \(2.434\) seconds separately
from request totals. The envelope inventory is also charged separately in the
artifact. Earlier donor/mining costs remain reported in notebook 15, rather
than being treated as free fresh discovery. The process peak is not a
per-lane memory comparison; its near-gigabyte cost makes practical memory
reduction a necessary next gate. Independent audit costs another
\(75.761\) seconds, peak \(182.09\) MiB.

`audit_conditional_clusters.py` imports none of the new producer, search,
feature routines or driver. It independently authors the declared boundaries
from literal integer sets, derives all \(187\) capacity interfaces and
\(114\) composition laws, checks \(228\) source child maps and brute
anchor-and-membership enumerates the entire \(180240\)-pose index. Its
fingerprint and \(711924\) incidences agree with the producer's set-intersection
compilation. Literal replay checks \(122\) saved states, \(1421\) scheduled
moves and \(27\) saved reorders; \(630\) sampled complete parent domains
and mode features agree. All \(48\) updates and \(384\) choices reconstruct
algebraically through an explicitly frozen, source-hashed audit helper.
Two finite-work base-path controls agree with r20. Nine changed records reject;
all \(70\) completed fixed/movable patches pass polygon non-overlap.
Random sampling and every abandoned branch are not independently replayed.
No exhaustive negative tree or plane certificate is exported.

All \(228\) research tests pass in \(78.320\) seconds. Eleven new controls
cover the exhaustive single-point interval law, every permutation of a small
cluster under several admissible inputs, all member incidences, forced-member
ordering, complete domains at every visited test branch, exact parent
preservation, global dead precedence, unknown cutoffs, seeded zero-policy
equivalence, preference-only learning and distinct authored families. The
artifact binds every test source and the full suite log. The visual report
compares one observed trace with its parametric bounds and highlights actual
reordered members in saved patches. Harder targets, useful learned productions
and failure markings, cheaper indices, boundary faithfulness, Penrose
continuation, compatible infinite coverage and the full proof-checker port
remain active. A stationary substitution remains optional.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_conditional_clusters.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_conditional_clusters.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py'

## 22. Turtle polygon and cell-region faithfulness

`turtle_cells.py` is an inspection/certificate module, not a new search engine
or geometry filter. It leaves all frozen point, marking, inventory, frontier,
generation, rollback and proposal semantics unchanged. The written theorem is
in `docs/research/gcts-rl-renewal/turtle-faithfulness.html`; its bytes are bound
by the new `turtle-cells-001.json` artifact. This is an analytic mathematical
argument with independently checked finite hypotheses, not a formally checked
implementation theorem or a discovered infinite construction.

Subdivide every elementary lattice triangle into its six vertex/midpoint/
barycenter flags. Each flag belongs to one original lattice point, and each
point owns twelve flags. The closed union of a point's flags is its barycentric
cell \(C_p\). In first-two-component coordinates, a flag has area \(1/12\)
and a cell has area \(1\). All flag interiors are disjoint, and the cells
cover the plane. For a point set \(Q\), put
\(\Omega_Q=\bigcup_{p\in Q}C_p\).

The prototype polygon is exactly the union of \(240\) complete flags; their
counts at each of its \(28\) positive points agree with the frozen integer
occupancies. The producer checks all \(1188\) potentially intersecting flags
by rational convex clipping against an ear triangulation, with \(13068\)
triangle/flag candidate pairs. Each intersection is empty or a whole flag,
and their areas equal the polygon area. All twelve signed coordinate
permutations preserve flags and their point owners. The independent auditor
instead generates flags face first, uses rational ray membership, cancels
oriented internal edges, and checks exact polygon-side coverage. It directly
reconstructs all twelve outlines and checks \(528\) boundary segments.

Every potentially intersecting pair reduces by symmetry and translation to
one of \(2443\) distinct-owner cases in inclusive bounding rectangles. All
\(1047\) positive-area overlaps have a point-capacity conflict; all
\(1396\) non-overlaps have none. The \(304\) capacity-legal pairs sharing
positive point support agree with the earlier contact count. Outside the
rectangles, both polygon boxes and positive supports are separated. The
producer checks shared flag interiors; the independent audit uses
\(12251\) rational scanline bands, including every polygon-segment
intersection height. Thus it detects thin overlaps that an arbitrary midpoint
sample could miss. The pair table's SHA-256 is
`4d7f18f6b29a638ec5f9c50dd5ac532fc7ebc9f0571ea13bcb614d25d35b9594`.

For any legal set of declared turtle placements, counts at a point are counts
of distinct occupied flags. This gives the written universal result:

\[
 \bigl(\forall p:\hat T_S(p)\le12\bigr)
 \quad\Longleftrightarrow\quad
 \text{distinct polygon interiors are disjoint},
\]
\[
 \bigl(\forall p\in Q:\hat T_S(p)=12\bigr)
 \quad\Longleftrightarrow\quad
 \Omega_Q\subseteq P(S).
\]

Containment of tile positive supports in \(A\) is equivalent to polygon
containment in \(\Omega_A\). Therefore the existing required points and
allowed envelope mean \(\Omega_Q\subseteq P(S)\subseteq\Omega_A\).
Required and allowed sets need not agree: extra coverage is permitted. An
annulus's unrequired interior is not a forbidden hole. Arbitrary prescribed
continuous curves require their own boundary authoring or a declared
approximation. No polygon predicate is added to candidate legality.

The new artifact explicitly reuses the SHA-bound notebook 21 request artifact.
All \(70\) completed fixed and movable-family requests are replayed as flag
unions, with \(129360\) required flags covered, no duplicated occupied flags,
no flags outside their envelopes, and exterior point sums realized by the
declared fixed polygons. This is stronger verification of old results, not
new solving, policy training or a speedup experiment. Arbitrary abstract
exterior values do not automatically have such a polygon realization.
Compatible cluster expansions inherit the geometry theorem; the earlier
capacity-input law has a polygon interpretation when its incoming state is
also realized by legal declared tiles.

A turtle has coordinate area \(20\), or Euclidean area \(10\sqrt3\).
For a finite closed cell region with zero exterior, \(|A|=20|S|\) is necessary.
The radius-five hexagon has \(91\) points, giving an analytic area obstruction
without search. Divisibility is not sufficient. Legal saturation of the whole
lattice would tile the plane; this theorem does not produce that assignment
or compatible infinite continuations of finite patches.

The finite producer costs \(0.703\) seconds, peak \(107.31\) MiB; the
sequential independent audit costs \(5.043\) seconds, peak \(121.98\) MiB.
Eleven changed records reject, including omitted flags/pairs, changed geometry,
recomputed pair fingerprints, forged coverage, and equal-looking floating or
Boolean coordinates. All \(240\) research tests pass in \(77.672\) seconds.
Twelve new tests exercise symmetry composition,
fractional clipping, boundary omissions, thin scanline overlaps, exact cells,
envelope constraints, ownership, strict integer semantics and old region
replay. Their full-suite results and source bindings are exported in the new
artifact. The visual report exposes point-owned flags, real pair controls and
the actual continuous required regions. Practical acceleration, cheaper
indices, learned failure interfaces, harder boundaries, Penrose continuation,
the logical checker port and an infinite turtle construction remain active.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_turtle_cells.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_turtle_cells.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py'

## 23. Complete logical semantics as a fixed tree program

The proof-system track now has a complete semantic port of `gcts-fol-1`,
including signature and syntax checking, every inference rule, free-variable
conditions, capture-avoiding substitution, registered natural-number induction
and exact checked-block interfaces. This removes the host inference callbacks
from the execution path. It is an intermediate operational port; literal
tape/Wang lowering remains open.

`fol_checker.tree` is fixed source in a small Python-shaped language. It has no
imports, dynamic calls, host data-structure operations, exceptions or access to
the proof as executable code. `tree_machine.py` compiles it into \(64\) static
functions and \(1958\) instructions. The generic operations are constants,
register moves, pair allocation and projections, pair and atom tests, byte
successor, Boolean negation, branches, jumps, static calls and returns. Atoms
are bytes plus nil; immutable pairs form an acyclic hash-consed heap. Explicit
frames implement recursive calls without native function recursion. Neither
the generic interpreter nor any primitive knows terms, formulas or inference
rules. The fixed declaration's SHA-256 is
`5f3aaf81e325654d30cc116a8f412c3152e75ccb4e0d781882180e8d0ec1fa31`.

The native adapter strictly parses serialized JSON, rejects duplicate keys
and noninteger numbers, and pins the external theory and target. It encodes
only syntax: distinct tags for objects, arrays, strings, naturals, negatives,
Booleans and null. Text is a UTF-8 byte list using surrogate-pass encoding;
naturals are unary lists. The program checks all semantics over those trees,
including decimal fresh names and ordered Unicode free-variable closure.
Unary numbers and whole-tree comparison are intentionally simple and costly.
Native parser, allocation and hashing limits remain declared adapters.
Every byte, heap or step exhaustion is an explicit unknown result, never a
failed theorem, learned failure label or pruning certificate.

All \(834\) semantic cases agree with the frozen serialized host checker:
\(217\) accept and \(617\) reject. This includes the \(816\) earlier controls,
with exhaustive two-atom propositional syntax through five nodes, plus
\(18\) port controls. New controls force freshness past twelve occupied names,
shadowed binders, Unicode/surrogate ordering, forbidden distribution variables,
unused invalid blocks, malformed signatures and repeated arithmetic blocks.
No finite syntax catalog restricts the request grammar. Finite comparisons do
not establish universal semantic equivalence or kernel soundness.

The authored addition control proves
\(\forall n:\operatorname{add}(\operatorname{zero},n)=n\) from right-recursive
addition axioms and the registered induction schema. The same checked response
is called \(1\), \(4\) and \(16\) times; the matched control expands every
primitive line while preserving the same external theorem. At \(1\) call,
blocks cost \(576825\) instructions against \(450585\) for expansion.
At \(4\), the counts are \(610281\) and \(1652010\). At \(16\), they are
\(745005\) and \(6896190\), with \(1.508\) versus \(13.909\) seconds:
checked interfaces use \(9.26\) times fewer instructions. Blocks themselves
are verified once per request. These are authored proof abstractions, without
block discovery, RL training or GCTS proof search. Across all controls,
the tree checker costs about \(969\) times the host reference time; this does
not establish practical acceleration.

`audit_tree_kernel.py` imports none of the compiler, producer, host logical
kernel or request generators. It independently validates acyclic exact heaps,
decodes the syntax input back to the external request, checks theorem and
program pins, and executes the small-step instruction semantics with a
separate frame implementation. All \(837\) machine runs replay, including
three valid proofs stopped by machine budgets. It reconstructs
\(31922347\) instructions, terminal statuses, profiles, node counts, frame
peaks, event prefixes and complete event digests. Eight independent pre-machine
parse/resource/binding controls agree. Fifteen mutations reject, covering
altered requests and pins, bad heaps, altered events/results, limits and
changed program instructions.

All \(254\) research tests pass in \(82.075\) seconds. Fourteen new tests
exercise generic control flow, strict heaps and input types, capture avoidance,
Unicode ordering, logical side conditions, external pins, resource outcomes
and replay mutations. The full-suite log and all test-source hashes are bound
in the new artifact.

The sequential producer costs \(66.555\) seconds, peak \(54.16\) MiB;
independent replay costs \(68.412\) seconds, peak \(80.77\) MiB. The producer
exports the fixed declaration, every encoded initial heap, raw certificate
bytes, outcomes, costs, explicit limits and source bindings in
`tree-kernel-001.json`. The report exposes the trust boundary, measured
block reuse, actual function-call profiles and saved event prefixes.

No tiling graph, candidate legality, scheduler, policy, marking or historical
certificate is changed. The next literal stage must represent the heap,
registers and frames on finite tape, implement their generic operations with
the existing fixed interpreter, bind the external request, and independently
verify accepting Wang rectangles. A universal equivalence proof, useful
proof-block discovery, internalized geometric lemmas and harder proof search
remain open. Practical region acceleration, richer boundary interfaces,
Penrose continuation and an infinite turtle construction remain active.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_tree_kernel.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_tree_kernel.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py'

## 24. The complete checker executes on a literal single tape

The complete fixed logical program now compiles into finite single-tape
read/write/head transitions. Every tree instruction is lowered: constants,
moves, canonical pair allocation, projections, node-range and atom tests,
byte successor, Boolean operations, branches, calls and returns. There is no
runtime host heap, register or inference callback. The upstream program pin
remains
`5f3aaf81e325654d30cc116a8f412c3152e75ccb4e0d781882180e8d0ec1fa31`.
Native serialized-syntax parsing and external theorem binding remain explicit
input adapters. A free-certificate Wang proof-search boundary is still open.

`tape_tree_machine.py` derives control-flow liveness and colors simultaneous
values into physical register bands. The largest function declares \(298\)
logical registers; the entire checker uses \(14\) physical registers.
Registers hold canonical little-endian binary node IDs. One tape band stores
records of the form `ID:left,right;`; equality scans preserve canonical
cons sharing. A next-ID band allocates new records. Calls save only live
caller values in reversed binary words, followed by a fixed-width return
address. Returns restore those values and copy the result. Callee live inputs
and any live uninitialized registers receive their specified initial values.
The full system has \(29\) bands, including arguments, scratch, heap, next ID
and recursive frames.

The intermediate selected-tape microcode has \(80096\) states. Each action
reads one symbol, writes one symbol and moves one selected cursor.
The physical lowering encodes those cursors as ordinary marks in one tape.
Literal states scan to the tape start, selected band header and cursor, then
perform the specified action and mark the new cursor. There are \(400471\)
literal states and \(46\) symbols, fixed independently of the request.
Same-symbol default rows are a compact finite-table representation; expanding
the alphabet gives only ordinary literal transitions. The uncompressed binary
table costs \(46063808\) bytes; the published compressed table costs
\(6330629\) bytes, and compressed microcode costs \(990401\) bytes.

`tape_runner.cpp` interprets only that finite table. For an unchanged-symbol
self-loop scan, it uses exact occurrence indices to find the first stop symbol.
The intervening state and symbols stay unchanged, and the complete number of
literal transitions is retained. Index updates follow every write. This is a
generic copy-sweep acceleration, independent of mathematical or heap meaning.
It does not choose a logical inference or prune a proof candidate. The FNV
microevent checksum is diagnostic, not a cryptographic proof; independent
execution and checked finite lowering laws supply the implementation evidence.

All \(13\) recorded requests agree with the reference tree checker: \(9\)
accept and \(4\) reject. They include the first eight primitive controls,
the full addition-by-induction certificate with checked proof blocks, missing
induction authorization, a wrong final target, forbidden generalization and
captured instantiation. All eleven inference rules participate across these
requests. The compiler does not restrict requests to these examples or to a
finite syntax catalog. This experiment does not repeat all \(834\) earlier
semantic controls on the tape.

The full induction proof accepts after \(1545494015\) selected symbol
operations, representing \(21932859109252\) literal transitions.
Its observed literal-run wall time is \(94.311\) seconds; independent selected
symbol execution takes \(10.443\) seconds. The earlier tree interpreter takes
\(1.143\) seconds. This is a completed operational lowering, without a
practical solver or proof-search speed claim. Cold native compilation costs
\(1.298\) seconds and source lowering \(1.742\) seconds. Sequential production
costs \(394.603\) seconds, peak \(885.13\) MiB. Table size, cold memory and
the underlying transition volume are substantial limits.

The first full-induction attempt exhausted its heap band; no logical rejection
was inferred. The successful lane uses a declared additional \(65536\) heap
cells. A recorded smaller-band control with \(4096\) additional cells still
returns `unknown_space_budget` after \(1239272267\) symbol operations.
Partial literal-step budgets of \(0\), \(1\) and \(10000\) return unknown.
Those outcomes cannot justify a failure marking, an impossibility statement
or candidate elimination.

`audit_tape_kernel.py` imports neither the lowering nor its serializer or
runner. It derives every finite physical row independently, checks all
\(12154622\) defined transitions after default expansion, and checks all
\(1958\) liveness equations and simultaneous-value color constraints.
It decodes and binds every request heap to the external serialized theorem,
checks the fixed program and source/artifact pins, then rebuilds and reruns
`audit_tape_micro.cpp`, a separate interpreter with no copy-sweep acceleration.
Across the \(13\) main cases it reconstructs \(4300810222\) symbol operations
and \(58761262127724\) literal transitions. Complete tape outputs agree.
The smaller space control also re-executes as unknown. The sequential
independent audit costs \(43.121\) seconds, peak \(703.08\) MiB. Its source
and the test sources are hash-bound in the new report artifact. A terminal
JSON-newline repair after production is explicitly recorded with both
executed and published driver hashes; it changes no computation.

All \(268\) research tests pass in \(82.808\) seconds. Fourteen new tests
exercise recursive/live frames, argument aliasing, loop liveness, entry defaults,
node boundaries, canonical heap sharing, partial operations, short circuiting,
explicit space exhaustion, finite table laws and changed register colors.
The full test log fingerprint and all \(29\) test-source hashes are exported.

This is implementation evidence, with the native toolchain and upstream
compiler as part of the trust boundary. It is not a formal proof that the
whole compiler preserves every possible certificate. The existing Wang local
rule can describe accepting computations, but this large checker has no
exported accepting Wang rectangle or sound hierarchical certificate yet.
Its proof-search boundary still must leave certificate data free while
enforcing syntax, initial-state protocol and external theorem binding.
Useful proof search, discovered proof abstractions and internal geometric
lemmas remain active. No tiling graph, scheduling, markings, policy, historical
certificate or other research engine is changed. Practical region tiling,
Penrose continuation and a compatible infinite turtle construction remain
active alongside the proof-system track.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_tape_kernel.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_tape_kernel.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py'


## 25. Free proof input constructed by the tape machine

`proof_boundary.py` adds a literal input constructor to the complete checker;
`boundary_syntax.tree` adds a tagged-tree syntax wrapper. The fixed problem
band holds protocol, theory and target. The free band holds blocks and proof.
An atom command is `0` followed by nine little-endian bits for a value in
\(\{0,\ldots,256\}\), where \(256\) is nil. A `1` constructs an ordered pair;
`;` ends a stream and permits only blank padding before a fixed `:` frame end.
No free command supplies a node ID, heap record or executable instruction.
Canonical-cons microcode constructs every pair from already-existing values.

The fixed stream first produces exactly three values, which are popped into
reserved bands. Its constructor stack must be empty before free commands run.
The free stream starts from that empty stack and must produce exactly two
values. The final request has fixed field names. Independent snapshots inspect
its actual root and entire canonical heap before semantic checking begins.
This closes the proof-dependent host heap-construction adapter at the
operational level. Host code encodes authored control proposals and declares
the fixed external problem; runtime acceptance depends on the finite table.

The input language is explicitly **tagged byte trees**, not JSON text.
The fixed wrapper checks objects, arrays, exact byte strings, natural and
negative integers, Booleans and null; it rejects duplicate keys, improper
lists, invalid tags and negative zero. UTF-8 JSON encodings used in the controls
are a subset of this byte-string language. No finite formula catalog narrows
the complete checker. All eleven logical rules, checked blocks and registered
induction remain in the program.

The published table has \(92457\) selected-symbol states, \(462276\) literal
states, \(60\) symbols and \(43\) bands. Its binary table is \(52901688\) bytes
before compression. The syntax wrapper and complete semantic checker comprise
\(69\) functions; the program SHA-256 is
`877c47879b027b08f02d3923d1e6dd9ccaf9a12e354567109f1aaa640a8fb673`.
The report records whole-checker execution, constructor costs, native timings,
unknown resource controls and source/artifact bindings without a speed claim.

Two preliminary trials are retained in the exported provenance. The first
terminated after main computations because a resource control declared an
invalid initial heap capacity. The second completed its finite controls, but
adversarial review found that free pair commands could consume fixed stack
values. The corrected constructor freezes the assertion values and resets its
stack before free commands; a regression control rejects cross-boundary
consumption even when later commands would restore the old total stack size.
Only the corrected machine is published. Preliminary work is additional; the first trial records a log-observation span rather than a certified benchmark time.

`audit_proof_boundary.py` imports no producer, lowering, input encoder,
serializer, runtime proof logic or native literal runner. It independently
parses the wire, reconstructs the expected canonical request heap, stops its
separate symbol interpreter at the actual constructor handoff and compares
allocation order and request root. It then executes the complete program,
checks all literal lowering rows and CFG liveness equations, replays malformed
and resource controls, and rejects changed trust bindings. Externally fixed
program, microcode and literal-table fingerprints cannot be replaced by
certificate-side declarations. The audit exports exact free-cell ranges,
allowed symbols, fixed frame and cursor positions, and fixed assertion hashes.

[The written boundary law](../../docs/research/gcts-rl-renewal/proof-boundary-law.html)
derives the two directions between an accepting run of this table and a
compatible Wang rectangle with a free certificate bottom. It explicitly binds
all other initial data and the single physical head. It is an analytic
construction, supported by finite implementation checks. It does not export
an accepting full-checker rectangle or prove upstream compiler and logical
soundness in a formal system. The table's local Wang reduction is a
proof-system adaptation; no tiling engine, frontier, generation, scheduler,
rollback, marking or RL policy changes here.

The corrected induction control accepts after \(2181777376\) selected-symbol
operations and \(30060767529466\) literal transitions. The constructor itself
uses \(249464824\) symbol operations and assembles \(832\) canonical nodes.
The literal runner takes \(146.487\) seconds, compared with the earlier
host-built-input lane's \(94.311\) seconds. The new lane also includes the syntax
wrapper. Corrected production costs \(216.139\) seconds, peak \(971.95\) MiB;
native compilation costs \(1.188\) seconds and lowering \(1.718\) seconds.
All \(13\) logical controls agree with the earlier checker, with \(9\) accepts
and \(4\) rejects. Three have literal runs; all have complete selected-symbol
runs. All \(16\) malformed, changed-target and resource controls replay.
The independent table audit checks \(17899987\) defined transitions and
\(2158\) liveness equations, and independently re-executes \(6433672369\)
whole-program symbol operations. The final independent audit costs \(56.628\) seconds, peak \(715.25\) MiB. An earlier \(57.808\)-second replay before stricter Boolean/integer external binding is additionally recorded. These finite results do not establish
universal compiler equivalence or a practical proof-search speedup.

The next step is a compact accepting response certificate for the full checker,
with derived cluster interfaces and inspectable expansions into the same local
Wang tiles. Useful learned proof abstractions and proof search remain open,
alongside practical region tiling, Penrose continuation and compatible infinite
turtle growth. Resource exhaustion remains unknown.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_proof_boundary.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_proof_boundary.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py'

All \(285\) research tests pass in \(90.177\) seconds. The \(30\) test-source files and complete test log are SHA-256-bound in the new artifact. New tests cover free/fixed stack isolation, exact field counts, malformed commands, padding, all finite atom encodings, canonical sharing, syntax types and duplicate keys, literal unknowns, and strict external Boolean/integer bindings.

## Notebook 26: accepting responses for the complete tape checker

`run_micro_cert.py` records three composed computation certificates for the
unchanged notebook 25 program, microcode, finite literal table and actual input
streams. The independent native verifier `micro_response_check.cpp` derives every
node interface from primitive actions, exact copy sweeps and descending binary
composition. No supplied interface or expanded root replay determines acceptance.
The root checks all input requirements, band extents, unchanged frame, final
cursors and exact literal-transition count; its complete derived output agrees
with the earlier independent tape execution.

The full addition-by-induction case accepts with \(4{,}483{,}731\) distinct
nodes, depth \(57\), \(483{,}826{,}358\) expanded primitive/sweep leaves,
\(2{,}181{,}777{,}376\) selected-symbol operations and
\(30{,}060{,}767{,}529{,}466\) literal transitions. Reflexivity accepts;
the captured-instantiation input rejects. Rejection certifies that supplied
proof's run, without an unprovability claim about its target.

Each band's response contains symbol-set preconditions, exact final writes,
cursor displacement and a visited extent relative to its incoming cursor. It also
derives an affine literal-cost law. These sets describe boundary families, not
set-valued GCTS markings. For a self-copy sweep of length \(n\) in direction
\(d\in\{-1,1\}\), the literal constant is
\(\kappa=d\,n(n-1)+3n\). Composition substitutes the earlier final cursor
and physical head into the later law. Descending references give structural
induction; repeated nodes instantiate their complete expansion at newly derived
positions. Every represented finite symbol run can instead use primitive leaves
alone. The written [response law](../../docs/research/gcts-rl-renewal/micro-response-law.html)
connects these interfaces and the independently audited literal selection law to
the accepting Wang expansion. The dense rectangle is not exported. Native
toolchain and algorithms remain trusted; universal compiler equivalence and
intended first-order logical soundness are still formalization goals.

The builder uses authored instruction, parser-token and heap-record grouping
states plus structural interning. This is a compression control, with no learned
block discovery, RL training, proof search or candidate pruning. The complete
tiling graph, global dead/forced precedence, generations, exact rollback and
scalar marking semantics are unchanged. Node, expansion, interface-work and
memory cutoffs remain unknown.

The full builder takes \(17.359\) wall seconds, peaks at \(515.47\) MiB,
and produces \(20{,}084{,}694\) compressed bytes
(\(71{,}739{,}740\) raw). The verifier takes \(24.584\) wall seconds,
peaks at \(1252.70\) MiB and derives \(702{,}373{,}961\) intervals,
with \(26{,}871{,}923\) live at peak. The full case including compression
takes \(51.760\) seconds. Earlier selected replay takes \(14.481\)
seconds; the literal runner takes \(146.487\). This gives a checked compact
representation of the huge expansion, without an advantage over selected replay.
Cold native compilation takes \(1.382\) seconds; the entire sequential producer
takes \(59.105\) seconds.

`audit_micro_cert.py` derives all three certificates afresh, independently
applies each root to its saved input, checks the fixed theory/target binding and
whole outputs, audits the complete literal table law and rejects altered roots,
start states, leaf states and external program/table pins. It takes \(31.062\)
seconds, with a \(729.00\)-MiB driver peak including the finite-table audit.
Its verifier has a separately reported native peak. Four official resource
controls return unknown. Pilot history records three insufficient grammar budgets,
an interface-work limit, a preliminary wrong sweep-count formula corrected before
certification, and a successful pilot whose time wrapper failed after completion.
The corrected official runs include native peak-memory measurements.

All \(299\) research tests pass in \(97.742\) seconds. The \(31\) source
files and complete test log are SHA-256-bound in `micro-responses-001.json`.
New tests compare all \(147\) finite symbol actions and both copy-sweep
directions against literal execution; compare \(30\) seeded mixed-band traces;
check read-after-write, restored writes, masks as sets and affine cost composition;
reject cycles, unused invalid nodes, fake supplied interfaces, changed declarations
and wrong input/frame bindings; and preserve unknown resource cutoffs. The
published full induction response is included.

The next gate is useful learned mathematical blocks and RL proposals evaluated
against total proof-search cost. Repeated exact block boundaries offer the PDE
analogy a concrete finite solution operator, but no multigrid convergence theorem.
Practical region tiling, movable boundaries, Penrose continuation and compatible
infinite turtle growth remain active alongside this proof-system work.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_micro_cert.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_micro_cert.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py'


## Notebook 27: searched mathematical block interfaces and RL proposals

The block library and policy start empty. `proof_block_problems.py` supplies two
right-recursive addition axioms, the registered natural-induction schema, and
statement families; it supplies no witness. The new semantic proposer
`proof_block_search.py` enumerates both directions of equations at matching
subtrees in a finite term envelope, uses bounded bidirectional search, and emits
actual primitive proof lines. An authored innermost-variable induction tactic
searches base and step derivations, uses a checked deduction construction, and
supports recursively proved base cases. This is a specialized equational
proposal fragment, not complete first-order search or a GCTS path benchmark.

The six discovered closed lemmas prove additions by one, two and three
successors, left-zero addition, associativity and four-leaf reassociation. The
unit-two definition calls unit one; unit three depends on the earlier unit
blocks; the four-leaf proof calls associativity. Left zero has \(50\) stored
primitive lines, associativity \(138\); the four-leaf definition stores
\(25\) lines and expands to \(299\). Every promoted definition is checked
before use. Quantifiers supply variable substitutions, while equality
substitution fits a solved expression into a larger context. This is a concrete
proof analogue of learning a local boundary response and composing it into a
coarser constituent. There is no multigrid convergence theorem or automatically
learned tape segmentation.

The official producer `run_proof_blocks.py` spends \(0.066542\) seconds on
cold discovery and promotion and \(2.382526\) seconds training a zero-start
REINFORCE policy for \(192\) episodes on \(24\) distinct statements,
with \(279\) updates and \(1831\) audited decisions. Features, induction
tactic and statement families are authored. Reward charges a work proxy
(proposal enumeration plus expanded primitive-rule cost), not wall time.
Evaluation freezes the policy and uses \(18\) distinct statements with new
variables, deeper contexts, longer bracketings and larger successor counts.
The split tests transfer within these authored families, not general new
mathematical theories.

| Proposal lane | Accepted / unknown | Fallback nodes | Propose seconds | Native full-check seconds |
| --- | --- | --- | --- | --- |
| Primitive equations | 6 / 12 | 68306 | 11.752403 | 1.191548 |
| Learned blocks | 18 / 0 | 843 | 0.535162 | 12.451351 |
| Blocks + random rollouts | 18 / 0 | 843 | 0.799038 | 11.604349 |
| Blocks + RL rollouts | 18 / 0 | 503 | 0.702406 | 18.537795 |

Each fallback attempt has a \(1200\)-node limit and term-size slack \(3\);
the authored induction tactic can trigger additional attempts. Free hypothesis
variables are rigid; only explicitly quantified variables are match parameters.
Both rollout lanes retain the bounded fallback. Proved lemma actions extend
that bounded fragment; these lanes do not have identical reachable paths.
Unknown results prove neither impossibility nor unprovability. RL reduces
fallback exploration, but plain block reuse proposes proofs faster. Including
full checking reveals some longer RL-generated proofs. Single sequential wall
measurements do not establish stable timing rankings, and no practical RL
advantage is claimed. Learning and interface costs remain additional.

All \(66\) accepted discovery/evaluation roots passed the unchanged complete
tree checker. The original production completed normally in \(828.410049\)
seconds, including \(812.164846\) seconds of full Python tree execution.
`tree_runner.cpp` interprets the same thirteen generic byte/pair/register
operations with explicit call frames and no mathematical callback. This native runner uses the macOS system SDK for CommonCrypto SHA-256; its
transport and interpreter are new source files, with no checker-grammar change.
Native replay of every actual input takes \(48.172716\) seconds including
\(0.535797\) seconds cold compilation. Every complete event SHA-256,
instruction count, call profile, heap size and final value agrees with the
completed original run. The original proof program, grammar, literal table and
microcode are unchanged. The native adapter and toolchain remain trusted.

`audit_proof_blocks.py` independently expands every accepted proof and all
block definitions into the frozen primitive kernel, checks each saved searched
move, reconstructs full RL choice domains, gradients, charged rewards and
updates, and independently constructs all native input heaps. It does not
independently reconstruct the RNG stream. Target, theory, block-body and block
order mutations reject. The audit takes \(4.078541\) seconds with a
\(197.828\)-MiB driver peak. Separate native tests compare full instruction
digests, output heaps and frame/profile behavior with two distinct interpreters,
including all opcodes, recursive calls, canonical sharing, partial operations,
short circuiting, strict input/pin guards, and unknown step/heap cutoffs.

The two-level searched unit-two proof also accepts through the unchanged
free-input tape constructor and response checker. It has \(5{,}009{,}167\)
distinct response nodes, depth \(52\), \(575{,}346{,}389\) expanded leaves,
\(2{,}499{,}026{,}663\) symbol operations, and
\(39{,}320{,}289{,}926{,}752\) literal transitions. Selected execution costs
\(17.735528\) wall seconds; construction \(22.396415\); verification
\(30.198640\), with a \(1376.750\)-MiB checker peak. Full cold production
including fresh discovery, native compilation and compression takes
\(85.058370\) seconds. The compressed grammar is \(22{,}634{,}288\)
bytes, with \(80{,}146{,}716\) raw bytes. This is a checked response and its
unchanged Wang expansion law, without an exported dense rectangle. Routine
cuts remain authored; the mathematical constituent is searched proof data.

The larger left-zero block reused in evaluation's first new context accepts in
\(75.699823\) seconds, with \(11{,}311{,}733{,}838\) symbol operations
and \(266{,}800{,}362{,}886{,}152\) literal transitions. Its builder reaches
the declared \(9{,}000{,}000\)-node limit after \(54.970128\) seconds,
so it has **no accepting composed certificate**. The resource result is
unknown. At least \(130.669951\) seconds were measured; compilation, cold
search and complete wrapper times were not retained. Its exact input was
recovered and byte-compared against the retained original input after the driver
stopped at the reported cutoff. The unchanged trial source is archived as
`run_learned_proof_tape_trial.py`; the recovery and scope are explicit in
`learned-proof-tape-cutoff-001.json`. The smaller control's initial selection
was corrected before tape execution to reuse the original discovery witness,
rather than rediscovering its already-promoted target through a different block.

`audit_learned_proof_tape.py` freshly derives every smaller response, independently
checks the constructor's actual heap, applies all root requirements and writes,
checks whole outputs and the complete finite literal table law, and rejects
altered bindings and grammar declarations. It re-executes the full larger
accepted symbol computation. That does not certify its exhausted response
builder. The audit takes \(124.339904\) seconds, including a
\(81.674350\)-second fresh replay of the larger accepted run, and peaks at
\(744.891\) MiB in its driver. That driver peak includes the finite-table
audit; the native response verifier has its own separately measured peak.
Seven changed binding/grammar controls reject and an interface limit remains
unknown. The native toolchain and intended logical/compiler soundness remain
trusted/open. Resource controls remain unknown.

The tiling/search algorithm contract is preserved: no new failure marking,
pruning or tiling-engine mutation is added; complete frontier bookkeeping,
global dead/forced precedence, earliest generation, exact rollback and scalar
point values are unchanged. New work adapts the semantic proposal layer and
records its specialized envelope separately. Next: abstractions selected by
total proof/search/interface cost, feasible large responses, broader mathematical
families, and practical region tiling with compatible movable boundaries.
Penrose continuation and compatible infinite turtle growth remain active;
substitution is an optional route.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_proof_blocks.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_proof_block_native.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_proof_blocks.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_learned_proof_tape.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_learned_proof_tape.py
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s research/gcts-rl-renewal -p 'test*.py'

All \(322\) research tests pass in \(100.019554\) wall seconds
(\(99.248\) seconds reported by unittest). The \(33\) test-source files
and full log are SHA-256-bound in `learned-proof-blocks-001.json`. The new
\(23\) tests cover searched proof expansion and promotion, dependency
closure, reverse equations, fresh context holes, capture avoidance, recursive
base cases, rigid matching, policy/fallback separation, unknown fragments,
external pins and complete generic native execution controls.

## Notebook 28: sample mathematics, an assessment, and the new priority

The primary research track is now **Wang-style automatic proof search with
succinct semantic constituents and finite distant GCTS markings**. Turtle and
Penrose remain regression and occasional geometric controls. Their infinite
tiling goals remain open; no goal is declared complete. This priority follows
the user's latest direction, superseding the original emphasis on mandatory
substitution discovery. The live interactive certificate gallery is
`docs/research/gcts-rl-renewal/proof-gallery.html`.

The success criterion is a derivation found from a statement and formal theory,
without a human supplying its inference sequence or a theorem-specific proof
skeleton. An authored general tactic is a declared search prior. The current
PA and Euclid witnesses are found automatically within such priors, but their
discovery uses ordinary symbolic rewriting and Horn saturation. **These new
examples do not establish a contribution from GCTS to their discovery.**
The fixed checker and tape/Wang encoding validate computations; that role must
not be relabeled proof search. Earlier tiny direct Wang controls have some
actual search evidence: analytic distant markings accept one of three word
problems where plain Wang accepts none, and three of six finite first-order
controls where plain Wang accepts one. These unchanged historical data are
specialized envelopes, not practical general mathematical performance.
Notebook 27's RL lane shows no practical gain over plain learned-block reuse.

`peano_problems.py` declares six usual first-order PA axioms for successor,
addition and multiplication, plus the registered induction schema. Its twelve
statements include left-zero and left-successor addition, addition by one,
addition commutativity/associativity, both multiplication unit laws, left-zero
multiplication, distributivity, multiplication by a successor in the first
factor, and multiplication commutativity/associativity. In particular:

\[
\forall a,b\;(a+b=b+a),\qquad
\forall a,b\;(a\cdot b=b\cdot a),\qquad
\forall a,b,c\;(a\cdot(b+c)=a\cdot b+a\cdot c).
\]

`run_peano.py` starts from an empty lemma library. The unchanged equational
proposer uses bidirectional contextual rewriting with a \(5000\)-node
budget per attempt and term slack \(3\). Its authored induction tactic
uses the innermost quantified variable and at most \(3\) nested induction
levels. No old witness library or policy is imported. Every found proof is
checked, compacted, fully checked on the fixed native tree program, and only
then promoted. All \(12\) proofs accept. Proposal time is \(0.744944\)
seconds; complete native checking \(17.369402\) wall seconds; full cold
family production \(20.523299\) seconds. These are sequential single-run
measurements, not benchmark rankings. This batch adds no RL training.

`euclid_problems.py` declares a guarded first-order construction/congruence
fragment, with point, circle incidence, noncollinearity, betweenness, segment
and triangle interfaces. Triangle/segment guard definitions are explicit in
both directions. Equal-radius circle intersection existence and SAS are
axioms. The circle intersection operator and I.1's candidate witness are
supplied in the statement; the search verifies its properties rather than
discovering the construction operator. No coordinate values or image
measurements enter proof search or checking. This is inspired by Euclid's
style and by the formal system \(E\), but does not implement all of \(E\),
Euclid's postulates, continuity or the parallel postulate.

`horn_proof_search.py` is a generic bounded Horn/equality saturation proposer.
Facts have derivation DAGs; only the solved goal's dependency closure is
materialized as a Hilbert proof. It handles conjunctions, conditional facts,
universal instances, equality symmetry/transitivity and checked earlier
blocks. A deduction transformation closes the conditional proof. The
author supplies no target-specific derivation. The measured search envelope
has \(12\) rounds, \(1500\) facts and \(200000\) match attempts; cutoffs
remain unknown. Its four examples are:

| Example | Independent primitive proof | Fixed native program |
| --- | --- | --- |
| I.1 equilateral triangle properties | accepted | accepted |
| I.5 main equal-base-angle conclusion | accepted | accepted |
| Constructed triangle's equal base angles, using both searched blocks | accepted | accepted |
| I.10 midpoint verification with a supplied bisector and betweenness | accepted | unknown instruction budget |

I.5's exterior-angle clause is not proved. I.10's angle bisector construction
and existence are not proved. The host and independent primitive replay
check its conditional derivation; the fixed program reaches \(100000000\)
instructions, and no completed machine certificate is claimed for it.
Final geometry proposal time is \(0.371606\) seconds, full native checking
including the cutoff \(28.459682\) seconds, and complete cold production
\(30.354846\) seconds.

Two geometry prototypes are preserved with their original full source bytes
in `euclid-pilot-source-001.json` and `euclid-interface-pilot-source-001.json`.
They retain respectively all primitive guards, then named statement guards
with primitive SAS premises. Each accepts I.1 on the machine and reaches
three cutoffs, taking \(38.293928\) and \(38.122444\) seconds overall.
The final representation uses two defined triangle interfaces in SAS instead
of eleven repeated primitive premises. The mathematical guard conditions
are equivalent under their explicit definitions, but the pinned theory and
statement representations differ. This is representation exploration, not a
matched speed comparison of an unchanged formal problem. Archived source
pins, exact original requests and unknown outcomes are independently audited.

`proof_compaction.py` first checks **every** input line and declared block,
including unused material. In an unchanged assumptions context it aliases
only exact identical formulas to earlier occurrences, keeps the final
formula's dependency closure, renumbers actual references, and removes only
unreachable already-checked definitions. Every declared premise remains,
including unused premises that restrict eigenvariables. It then checks the
whole output against the same external theory/target pin. No alpha conversion,
new inference rule or altered semantic boundary is introduced.

`run_proof_compaction.py` reuses the exact \(66\) actual Notebook 27
requests; it performs no new search. It runs original and compact requests
on the unchanged complete native program in alternating order. All accept.
Instructions decrease from \(398061855\) to \(319557779\), or
\(19.7\%\). Original/compact full native wall totals are \(46.542426\)
and \(36.793891\) seconds; whole-input checking and compaction add
\(3.609566\) seconds. The complete producer costs \(111.466613\)
seconds including fresh Python reference controls and serialization.
The earlier large cutoff case's left-zero block shrinks from \(50\) to
\(28\) lines, with \(2309467\) to \(1223779\) tree instructions and
the identical target and external pin. **Its accepting tape-response
certificate has not been rebuilt.** The earlier cutoff remains unknown.

`audit_proof_compaction.py` independently reconstructs all alias/dependency
maps, interfaces, removed definitions and native input heaps, expands every
original and compact root/definition into the frozen primitive kernel, and
independently replays all tree instructions on two optimized controls. It
takes \(27.724240\) seconds. This is not an independent instruction replay
of all \(66\) native runs. `audit_theorem_examples.py` binds externally
pinned theories/statements, checks all earlier-only library provenance,
normalization graphs and native input heaps, and independently expands every
PA/geometry proof and promoted block. PA searched edges are independently
reconstructed, including sound inversions of actual backward-tree edges:
variable-erasing equations such as \(x\cdot0=0\) can be inverted using
the recorded instance even when the variable cannot be inferred locally.
The audit never calls the producer or proposer. Full geometry saturation and
the new examples' entire native instruction traces are not independently
reconstructed. The PA and geometry audits cost \(3.060434\) and
\(5.974678\) seconds. Changed statements, axioms, last formulas, reference
order, signatures and dependency maps reject. Universal logical soundness,
compiler equivalence and the native toolchain remain trusted/open.

The next decisive experiment uses **semantic proof tiles**. An inference
constituent occupies a proof cell with \(t=1\); scalar \(m\)-values bind
exact syntax IDs at its conclusion and at earlier premise points. Distant
support can encode non-adjacent proof references directly. Each finite
envelope enumerates valid syntax/rule instances and offsets; scope and
substitution interfaces must be explicit. Learned lemma tiles expand to
checked lower-level proofs. Compare the same grammar in ordinary symbolic
search, adjacency-only encoding, distant GCTS markings, and then RL/learned
clusters. Withhold all derivations and theorem-specific skeletons. Charge
catalog/graph construction, search, learning, interface expansion, verification
and memory. The design is not yet a completed semantic GCTS proof engine.
Finite envelopes must grow fairly for expressive coverage; no fixed tile
with unbounded reach or truth oracle is assumed.

Conformance is unchanged in this batch: semantic proposers and proof-data
representations are adaptations, not tiling-engine mutations. No new GCTS
pruning or learned failure marking is claimed. The proposed semantic engine
must retain complete frontier/candidate bipartite bookkeeping for distant
marks, global dead/forced precedence, earliest-generation branching, exact
rollback and proved-vs-learned pruning separation before supporting a GCTS
performance claim.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_peano.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_euclid.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_theorem_examples.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_proof_compaction.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_proof_compaction.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_theorem_tests.py

All \(347\) research tests pass in \(98.687733\) wall seconds
(\(97.854\) seconds reported by unittest). The \(35\) test files and
complete log are SHA-256-bound in `theorem-tests-001.json`; historical
artifacts remain unchanged. The \(25\) new tests cover whole-input-safe
normalization, eigenvariable contexts, exact interface pins, all cold PA
proofs, searched geometry composition, missing intersection/congruence
assumptions, unknown search budgets and rejected false constructions.

## Notebook 29: direct semantic GCTS proof search

The primary track is Wang-style proof search; Turtle and Penrose remain
regression and occasional geometric controls. The new live report is
`docs/research/gcts-rl-renewal/semantic-proofs.html`. Notebook 28's larger
PA and Euclid examples remain symbolic-tactic results. This batch supplies
actual direct GCTS proof discovery on smaller logical/arithmetic statements.
No proof sequence, theorem-specific skeleton, old policy or searched lemma
library enters either lane. The general rule compilers are authored priors.

`semantic_proof_tiles.py` adapts the unchanged `turtle.State` and `Graph`.
For proof slot \(i\), occupancy is \(t(2i,0)=1\), represented by
integer capacity \(12\). A tile assigns its conclusion syntax ID at
\((2i,1)\), and each premise ID at \((2j,1)\) with \(j<i\).
The target fixes the final output marker. Syntax ID zero is assigned,
not absent. Repeated premise references are permitted if their required
values agree. Every rule/slot/earlier-reference instance is eagerly enumerated;
all occupancy and marking-only incidences are indexed before search. The
finite allowed support consists of all proof cells, with generation-zero
roots. Scalar disagreement eliminates candidates through the complete graph.
No semantic oracle callback runs during GCTS placement legality.

The direct finite encoding has an elementary correspondence: a complete
point tiling contains one tile per proof cell; its agreeing formula ports
and strict earlier offsets reconstruct a command derivation in slot order.
Conversely, each valid command sequence of the declared grammar yields a
complete point tiling. Rule instances retain their witnesses, so two choices
can prove the same formula differently. Copies and unused commands are
allowed. Geometric placement order may differ from logical dependency order.
These are **positional finite types with identity transforms**, not a uniform,
translation-invariant adjacency-only Wang inventory. Grammar and reach grow
with the finite envelope. Current markings are **problem-defining**, not newly
learned redundant exclusions. The checker/compiler's general semantic
soundness remains trusted/open rather than newly formalized.

`semantic_proof_catalogs.py` has two declared priors. The FOL generator uses
a bounded subformula and schema closure of theory/target syntax, compiling
all primitive relations inside that declared inventory. It is not the earlier
fair grammar ladder. The arithmetic generator enumerates every term within
a node bound, every quantified-variable substitution from that grammar,
both directions of each equational axiom, and every term position with
nonidentity endpoints inside the grammar. Missing variables in a reverse
variable-erasing equation are enumerated explicitly. Each rewrite is a
compiled derived inference from the fixed primitive equality kernel and is
checked before search; it is not an input proof path. Universal arithmetic
parameters are closed after decoding. No induction rule is generated.

`semantic_proof_problems.py` contains only external theories, statements and
finite bounds. `run_semantic_proofs.py` rebuilds fresh catalogs for both lanes
and checks their declaration hashes agree. The specialized chronological
symbolic DFS enumerates the same valid logical certificates; its scheduler
and representation differ from GCTS. It is **not an unmarked run of the same
point graph**, nor an adjacency-only/distant-marking ablation. Run order is
counterbalanced by case. The node and search-time limits are \(50000\) and
\(5\) seconds; candidate construction and graph initialization consume the
GCTS time limit. Catalog construction, validation, decoding, complete native
verification and shared compilation are additionally charged. Budget cutoffs
are unknown, not failed theorem proofs.

Both lanes find \(11\) of the \(13\) cases: two implication steps, a
premise join, equality generalization, universal instantiation, function
congruence, \(1+1=2\), \(2+1=3\), \(1+2=3\), \(2+2=4\),
\(\forall a\;(a+1=\operatorname{S}(a))\), and \(1\cdot1=1\).
Both exhaust the deliberately shorter implication envelope and absent-fact
control. Every one of the \(22\) decoded certificates is accepted by the
unchanged fixed native checker program, whose SHA-256 is
`5f3aaf81e325654d30cc116a8f412c3152e75ccb4e0d781882180e8d0ec1fa31`.
GCTS visits \(644\) states versus \(12375\) for the symbolic control,
but search costs \(4.511720\) versus \(0.121492\) seconds. Equality
congruence favors GCTS, with \(10\) versus \(11426\) nodes and
\(0.012550\) versus \(0.069771\) search seconds. Multiplication favors
the symbolic control: GCTS takes \(4.444571\) search seconds, versus
\(0.049931\). This is real automatic proof assembly with GCTS, but no
general speed advantage or useful RL contribution is established.

Whole cold-run totals are \(7.586207\) and \(2.277170\) seconds.
The first native launch in the GCTS lane costs \(1.003277\) seconds,
versus about \(0.01\) for subsequent tiny checks; this is retained. Shared
native compilation costs \(1.054998\) seconds. Full producer time is
\(11.129331\) seconds and peak driver memory \(144818176\) bytes.
These are single sequential measurements, not benchmark rankings. All
catalogs, actual placement traces, decoded requests, complete GCTS trees,
resource results and source hashes are in `semantic-proofs-001.json`.

`audit_semantic_proofs.py` imports no generator, proposer or point graph.
It independently reconstructs every external statement/theory, enumerates
every positional candidate, recomputes all saved frontier domains and replays
all complete GCTS trees with global dead/forced precedence, branch choice,
every failed alternative and exact work counters. It independently enumerates
all bounded arithmetic terms and \(1232\) contextual rewrite edges,
including variable-erasing reversals, and checks the complete primitive FOL
inventory inside its declared language. Every compiled arithmetic rule and
every decoded proof is expanded independently into the frozen primitive
kernel. Audit-only tautology/MP suffixes force checking every emitted primitive
prefix even if the original final command aliases an earlier assumption or
block input. Historical auditors and measured sources stay byte-identical.
Native program and exact input-heap hashes bind every complete native run;
independent instruction replay of all native runs is not claimed. Symbolic
abandoned prefixes are not exported or independently tree-replayed. The
audit costs \(6.186143\) seconds.

The unchanged engine preserves complete candidate incidence, distant
mark-only updates, global dead ends before global forced moves, then earliest
generation with degree breaking ties, and exact snapshot rollback. These
proof cells have single-point full occupancy; inherited fractional-occupancy
semantics are tested by the earlier suite, not newly exercised by this grammar.
All \(368\) research tests pass in \(103.625896\) wall seconds
(\(102.887\) reported by unittest). The new \(21\) tests cover exact
incremental-domain/rollback agreement, scheduler precedence, zero and missing
marking distinctions, distant dependencies, repeated reference compatibility,
independent inventories, variable-erasing reversals, a tiny exhaustive
logical/point certificate-set comparison, unknown budgets and rejected
altered trees, ports, proofs and unused invalid prefixes. The fresh ledger
`semantic-proof-tests-001.json` leaves historical experiment artifacts intact.
`run_semantic_view.py` produces a small browser projection bound to its full
parent artifact by SHA-256; the visual controls show actual placement order,
logical commands, decoded formulas and all costs.

Next gates: matched semantic encoding ablations; automatic promotion and
reuse of searched subproofs as multi-level tiles; RL proposals with complete
fallback and total-cost evaluation; a fair semantic grammar with induction
and fresh binding. A failed bounded envelope must never become an unsound
logical exclusion. Larger geometry and PA proof discovery through GCTS,
uniform Wang expressivity, useful hierarchy/RL, broad speed comparisons and
formal soundness remain open. The research goal remains active.

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_semantic_proofs.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_semantic_proofs.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_semantic_tests.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_semantic_view.py

## Notebook 30: mined proof fragments and hierarchical GCTS proposals

The primary track remains Wang-style proof search. This batch starts with
an empty library and two authored donor statements,
\(\forall a\;(a+1=\operatorname{S}(a))\) and
\(\forall a\;(a+2=\operatorname{S}(\operatorname{S}(a)))\).
No proof path or fragment statement is supplied. `proof_clusters.py` searches
with the unchanged complete semantic base graph, mines every eligible
source dependency-chain window of two to four moves, and checks its universally
closed equation interface. Four distinct templates are promoted. Two have
level two because their definitions retain an actual level-one child call
used by the earlier donor search. All child dependencies are earlier-only.
The level is a proof-program dependency level, not a frontier generation.

Template substitution, both orientations and every surrounding term context
are compiled into existing bounded base rule instances. All intermediate
terms must remain inside the same declared grammar. A fragment's member
cells are a contiguous logical move span; its preceding input may reference
any earlier cell. The proposer uses a fixed authored priority (goal-containing,
move count, hierarchy level, deterministic identity); there is **no RL** in
this batch. Every proposal constituent is an ordinary base candidate.

Conformance is preserved at the complete primitive graph: global dead ends,
then global forced moves, then earliest generation with candidate count breaking
ties. Before each transaction step, that global decision is recomputed on an
exact copied state and copied graph. Forced moves outside a fragment execute
as well. A proposed branch member must occur at the selected point. Scheduler
refusal is a proposal rejection, not a proved logical failure. Every base
alternative remains, and the parent is unchanged after successful, failed or
cut-off transaction validation. Base placement attempts include all constituent
and forced steps. An attempt or time cutoff is **unknown**. An index cap only
truncates the proposal index, never the complete primitive candidate universe.

`proof_cluster_problems.py` supplies only theories, targets and finite bounds.
Ten evaluation cases (eight mathematical targets and two finite controls) are
never mined. Two deterministic repeats rotate lane order, retaining a fresh
identical base catalog, target, term envelope, cell bound and scheduler in all
four lanes. Plain GCTS has no learned library; level-one and full hierarchy
lanes propose sequences; rank-only uses the same full hierarchy to reorder the
next individual base move. This is a **matched base-graph sequence/ranking
comparison**, not an adjacency-versus-distant encoding ablation. The hierarchy
is a checked proof representation and proposer; it is not a collapsed coarse
graph, and it does not shrink the primitive cell envelope.

Measured totals over twenty requests per lane are:

| Lane | Verified / finite exhausted / unknown | States | Base attempts | Search seconds | Cold request seconds |
| --- | --- | --- | --- | --- | --- |
| Plain GCTS | 16 / 4 / 0 | 2324 | 2304 | 19.097064 | 30.623473 |
| Level-one sequences | 16 / 4 / 0 | 1426 | 1464 | 11.371594 | 21.656236 |
| Full hierarchy sequences | 16 / 4 / 0 | 1304 | 1338 | 11.045820 | 21.444932 |
| Hierarchy ranks single tiles | 14 / 4 / 2 | 1763 | 1743 | 14.289677 | 24.925233 |

Cold costs include fresh catalog validation, model/graph/index construction,
proposal enumeration and scheduler validation, decoding, hierarchical compilation,
full-prefix host checking and the complete fixed native machine. All donor
search, checking, mining and whole-library native validation costs
\(1.586897\) seconds. Charging it once to the full hierarchy gives
\(23.031829\) seconds versus plain search's \(30.623473\), before adding the
same shared \(1.006123\)-second native compilation to either lane. Full family
production costs \(103.137680\) seconds. Driver peak memory is
\(350437376\) bytes, including accumulated artifacts; it is not a per-lane
memory ranking. Every search has a \(5\)-second wall and \(50000\) actual
base-attempt limit. Catalog and final verification are outside the search wall.

The nested-right addition example drops from \(391\) plain states to \(4\)
hierarchy states and uses two actual fragments, one inside an argument followed
by a level-two fragment. The latter transaction chooses its last cell first.
Multiplication instead uses \(547\) sequence states versus \(515\) plain states,
with modest extra cold time. Its rank-only repeats both reach the wall limit
and remain unknown. The second hierarchy level saves only \(0.211304\) cold
seconds beyond level one over the whole family before charging discovery.
These are specific controlled results, not a general performance ranking.
The unequal-outcome rank-only aggregate is not an equal-success comparison.

`hierarchical_certificate` first validates the entire original decoded request,
then replaces actual goal-chain transaction spans by checked instantiated block
calls. It includes all and only reachable definitions in dependency order and
checks the complete output request under the unchanged external problem hash.
There are \(62\) complete evaluation native acceptances, two donor acceptances
and one whole-library acceptance. No mathematical proof is accepted merely
because a fragment has a shorter root certificate.

`audit_proof_clusters.py` imports no proposer, miner, graph implementation,
catalog producer or measured driver. It independently reconstructs all external
theories and targets, bounded base rewrite inventories, all eligible mined windows,
source member and whole-certificate provenance, actual earlier child spans,
all instantiated proposal indexes, domain samples, and every complete saved
search tree/transaction with exhaustive base fallback. It checks the separate
rank-only order, exact counters, every promoted definition, each decoded proof
and each hierarchical output by full-prefix primitive expansion. It binds every
native input/program to the original external problem. The audit passes in
\(25.463079\) seconds. It does not independently replay every native instruction,
certify truncated unknown trees, or prove general compiler soundness.

The full suite passes \(392\) tests in \(107.851559\) wall seconds. New meaningful
tests cover actual two-level discovery, provenance, unchanged base universes,
complete transaction domains and scheduler roles, exact rollback, duplicates,
mid-transaction unknown cutoffs, index/pool fallback, finite exhaustion,
rank-only singleton semantics, full expansions, altered interfaces/roles,
dropped fallback branches and independently reconstructed external declarations.
Historical measured sources and artifacts, including notebooks 28 and 29, remain
byte-for-byte unchanged.

Reproduce (from the repository root; no imported old policy or library):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_proof_clusters.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_proof_clusters.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_cluster_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_proof_cluster_view.py
```

The report is `docs/research/gcts-rl-renewal/proof-clusters.html`. Its small
projection (`proof-cluster-view-001.json`) pins the full audited artifact and
exporter by SHA-256. The full artifact records every complete tree, unknown
partial prefix, proposal trace, source, inventory, proof request and native result.
The tests have a separate source-pinned full log. Next gates are zero-start RL
selection against these exact controls, a broader statement family, induction and
a fair grammar, and a genuine coarse interface graph with constraint-solver
comparisons. Learned failure markings and universal compiler soundness are still
open; bounded failures cannot justify unproved pruning. Turtle and Penrose remain
occasional geometric controls, and discovering their substitution rules is optional.

## Notebook 31: zero-start RL selects checked proof fragments

`proof_cluster_policy.py` adds a sequential softmax controller that can select
any compatible bounded learned-fragment instance or defer to ordinary GCTS.
It uses twelve authored graph/interface features: deferral, deferral with
multiplication/progress/degree, member count, hierarchy level, final-cell
membership, direction, context depth, term shrinkage, already-placed input,
and member degrees. It reads current graph domains and exact term syntax;
no future proof sequence or expert trajectory is supplied. The policy's
floating-point scores order proposals only. They do not define point legality
or prove a theorem.

The historical measured `proof_clusters.py` remains byte-for-byte unchanged.
The new DFS isolates the policy hook and reuses the same exact model, complete
primitive graph, proposal compiler, reversible constituent transaction and
proof compiler. With no policy its paths, domains and counts match the frozen
notebook-30 search. Every state still checks global dead ends, then forced
moves, then earliest generation with degree breaking ties. Proposals retain
all original base alternatives. A sampled pool never supplies degrees.
All finite roots remain generation zero; base tiles have one capacity-12
occupancy point and exact scalar distant formula ports. The grammar remains
specialized positional arithmetic, with identity transforms and no induction,
uniform adjacency-only compiler, newly learned failure marking or coarse graph.

`run_proof_policy.py` freshly searches the two donors and re-mines the four
checked fragments; it imports no artifact library or old weights. Eight
training statements from `proof_policy_problems.py` are separate from the ten
frozen evaluation statements, even when comparing external problem hashes
without cell bounds. Three seeds, \(1\), \(7\) and \(19\), start with all twelve
weights zero. Four epochs rotate the training-statement order, making
\(32\) episodes per seed. The validated training catalogs are built once and
shared across seeds; model, graph and index are rebuilt each episode.
Evaluation never updates weights or promotes fragments.

Sampling is sequential without replacement over a softmax distribution, with
a deferral action and a cap of eight proposal preferences. All compatible
instances in the bounded index are eligible, rather than just the fixed
heuristic's first eight. The fixed prior ranks the same instance universe by
final-cell membership, length, level and deterministic identity. A declared
\(32\)-bit LCG exports every uniform variate. Deterministic frozen evaluation
uses score order and identity ties; zero weights are a separate untrained
control, not the authored fixed prior.

A reached proposal's delayed return is

\[
r(a)=\mathbf{1}\{\text{full native acceptance and successful continuation}\}
 -\frac{\log(1+C(a))}{\log(1+50000)}.
\]

\(C(a)\) counts all actual validation and continuation base attempts; deferral
counts all base-fallback attempts. Rejected and exhausted proposal branches
can receive negative work rewards, but never prune base candidates. The
complete request is checked before any positive proof credit. Pre-sampled
suffixes after an earlier successful child receive no credit. Unknown trees
supply no weight or baseline update; their overall outcomes stay unknown.
Each episode freezes its weights and applies a projected batch update after
checking, with rate \(0.2\), clipping to \([-6,6]^{12}\), and baseline update
\(b'=0.9b+0.1r\). This is a REINFORCE-style experiment inspired by
[Williams (1992)](https://doi.org/10.1007/BF00992696), not a new convergence or
unbiased-gradient theorem for this capped pseudo-random DFS. Reward optimizes
a base-work proxy; full elapsed evaluation cost determines whether it helped.

All three seeds have \(28\) native-accepted training proofs and four unknown
attempts on multiplication inside a successor. That target's grammar has
\(3545\) base rules and is cut off at the five-second search budget. The pilot
also retained unknown outcomes at ten seconds under the fixed prior,
zero weights and one sampled policy; no pilot witness or policy is imported
into the measured run. The multiplication-specific coefficient remains zero
in every measured update chain because these incomplete traces supply no
credit, and the simpler multiplication case has zero gradient in that feature.

Evaluation has five lanes and one deterministic request per seed, statement
and lane. Order rotates by case and seed index. All share the exact external
problem, base declaration SHA, term/cell bounds, complete candidate universe,
root generations, global scheduler, five-second wall and \(50000\) actual
base-attempt budget. Catalog and final verification lie outside the search
wall. The matched evaluation totals are:

| Seed | Lane | Verified / finite exhausted / unknown | Base attempts | Cold request seconds |
| --- | --- | --- | --- | --- |
| 1 | Plain GCTS | 8 / 2 / 0 | 1152 | 14.724649 |
| 1 | Level one | 8 / 2 / 0 | 732 | 10.801033 |
| 1 | Fixed hierarchy | 7 / 2 / 1 | 660 | 11.065854 |
| 1 | Zero weights | 8 / 2 / 0 | 672 | 10.933090 |
| 1 | Trained | 8 / 2 / 0 | 669 | 10.854248 |
| 7 | Plain GCTS | 8 / 2 / 0 | 1152 | 14.988673 |
| 7 | Level one | 8 / 2 / 0 | 732 | 11.079584 |
| 7 | Fixed hierarchy | 8 / 2 / 0 | 669 | 10.647622 |
| 7 | Zero weights | 8 / 2 / 0 | 672 | 10.682554 |
| 7 | Trained | 8 / 2 / 0 | 1152 | 14.658055 |
| 19 | Plain GCTS | 8 / 2 / 0 | 1152 | 15.343842 |
| 19 | Level one | 8 / 2 / 0 | 732 | 10.677222 |
| 19 | Fixed hierarchy | 8 / 2 / 0 | 669 | 10.681090 |
| 19 | Zero weights | 8 / 2 / 0 | 672 | 10.732782 |
| 19 | Trained | 8 / 2 / 0 | 669 | 10.387478 |

**Useful RL acceleration is not established.** Seed seven learns enough
deferral to reproduce plain-search work. Seeds one and nineteen mostly match
the fixed hierarchy's work. Zero weights already obtain nearly that same
work on this family. Training costs \(23.185003\), \(23.252945\) and
\(28.484853\) seconds respectively, plus \(8.657584\) seconds for shared
training-catalog construction. Fresh donor discovery and whole-library checking
cost \(1.895281\) seconds, and shared native compilation costs
\(1.020798\) seconds. No measured gain repays those training costs on the
held-out family. The fixed-prior first multiplication repeat is near the wall
cutoff and remains unknown; its unequal-outcome aggregate is not an
acceleration ranking. Three seeds on ten fixed targets are not broad theorem
generalization or a statistically supported timing ranking.

The measured producer costs \(270.489981\) seconds. Its peak driver memory
is \(882540544\) bytes, including accumulated catalogs, trees and artifacts;
it is not a per-lane memory comparison. There are \(119\) complete evaluation
native acceptances, \(84\) training acceptances, two donor acceptances and one
whole-library acceptance. Thirty evaluation requests exhaust their finite
control envelopes, and thirteen total search requests remain unknown.

`audit_proof_policy.py` imports no policy, miner, graph implementation,
catalog producer or driver. It independently reconstructs external training
and evaluation declarations, every bounded base inventory and newly mined
window; enumerates every policy pool and feature vector; recomputes every
softmax probability, LCG variate, sampled choice and log-probability gradient;
checks delayed subtree attempt counts, reached-choice credit, baselines and
projected updates; and replays every complete tree and positive full-prefix
primitive expansion. All native inputs/programs bind to the original external
problem. It passes in \(55.568325\) seconds. Unknown saved contexts and draws
are checked, but their truncated trees are not proved complete. Every native
instruction and general compiler soundness remain outside this audit's scope.

All \(425\) research tests pass in \(108.028274\) wall seconds. New tests cover
zero initialization, numerical log-probability derivatives, the declared random
stream, frozen evaluation, exact base fallback and prior-path equivalence,
unchanged graph domains, unknown update gates, sampled-suffix censoring,
full-native credit gates, exact attempt recounts, training/evaluation separation,
proposal/index caps, malformed weights, clipping, complete proof expansion,
and independent replay rejecting altered draws, gradients, pools, tree event
identities, delayed costs and update outputs. Historical sources and artifacts
through notebook 30 are preserved byte-for-byte.

Reproduce from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_proof_policy.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_proof_policy.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_policy_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_proof_policy_view.py
```

The report is `docs/research/gcts-rl-renewal/proof-policy.html`, with full
source-pinned data in `proof-policy-001.json`, a parent/exporter SHA-bound
small browser projection, and a separate full test ledger. The next credit
experiment should retain verified local transitions and already closed
subtrees inside a partial search trace, with actual progress/cost rewards and
an unknown overall result. The subsequent gates remain a broader fair grammar,
induction, genuinely coarse interface graphs and constraint-solver comparisons.
Wang-style proof search remains primary; Turtle/Penrose geometric controls,
certified failure markings, arbitrary boundary composition, general proof
language/compiler soundness and infinite-plane research remain open. The full
active goal is not declared complete.

## Notebook 32: independently replayed credit from open search prefixes

`partial_proof_policy.py` preserves the actually executed DFS prefix when a
wall or placement budget is reached. A tri-state recursion retains completed
children, failed branches, interrupted constituent transactions and exactly
one open suffix. `search_tree` remains absent for an unknown result; the new
`partial_tree` holds its executed prefix. No cutoff becomes finite exhaustion
or a theorem certificate. Historical sources and measurements through notebook
31 remain byte-for-byte unchanged.

The model, complete candidate graph, global scheduler, proposal compiler and
transaction logic are reused unchanged. All required finite roots are generation
zero; each base placement has exact capacity-12 single-cell occupancy and scalar
distant output/premise markings. Branching follows global dead and forced checks,
then earliest generation with degree breaking ties. Every primitive alternative
remains available after a failed proposal. The frozen notebook-31 `Policy` class,
twelve features, softmax probabilities, capped proposal pool and LCG are shared
by both return signals. This is still specialized positional equational search
with identity transforms, not new failure-marking synthesis, induction, a uniform
four-edge compiler or a genuinely coarse cluster graph.

The complete-tree control retains the previous reward and gives unknown requests
no update. The local signal uses

\[
r_{\mathrm{local}}(a)=
\mathbf{1}\{\text{full native acceptance and successful continuation}\}
+\frac{D(a)}{n}-\frac{\log(1+C(a))}{\log(1+50000)}.
\]

Here \(n\) is the fixed cell envelope. \(C(a)\) includes every executed base
attempt in a proposal and its observed continuation, or in base fallback for
deferral. \(D(a)\) is the largest observed viable filled-cell increase from the
action's parent. A viable point state has no degree-zero frontier in its complete
graph. This is a progress proxy, not a theorem or extension guarantee. Returns
of nested actions overlap and must not be summed as disjoint work or progress.
Interrupted transactions roll back and earn no committed occupancy gain; their
actual validation steps still cost work. A zero-step interruption gets no local
credit. Unreached sampled suffixes are censored, and deferral needs actual base
fallback execution. All coefficients freeze during each episode; both signals
use rate \(0.2\), clipping to \([-6,6]^{12}\), and baseline
\(b'=0.9b+0.1r\). No unbiased-gradient or convergence theorem is claimed.

Before either learner updates, `audit_partial_proof_policy.replay` independently
reconstructs every visited point domain and selected move, including open prefixes,
all policy draws and literal attempted work. This online gate is charged to both
learners. The driver also independently validates each training inventory. It
freshly searches the two donors, mines the same four checked fragments, and imports
no saved policy, library or pilot witness. Eight training statements and ten
external evaluation statements remain disjoint even without cell-bound hashes.
Signals train separately from zero in seeds \(1\), \(7\) and \(19\), for four
rotating epochs of \(32\) episodes. Learner order alternates. A seed match does
not guarantee identical later trajectories: differing updates change choices,
draw counts and resource-limited prefixes.

All six learners verify \(28\) training proofs and retain four unknown attempts
on multiplication inside a successor. The complete control updates none of its
\(12\) unknown requests. Local credit updates all \(12\), with \(165\) total
reached-choice credits and no theorem bonuses on those unknown requests. Its
final multiplication coefficients are \(-0.312192\), \(-0.364795\) and
\(-0.256977\); the control coefficients remain zero.

**Partial credit is obtained; useful RL acceleration is not demonstrated.** All
local policies verify eight held-out targets and exhaust two finite controls, but
use \(1196\) base attempts versus plain GCTS's \(1152\) on the same outcomes.
Local policies defer on the addition cases, then make ten reverse fragment
proposals on multiplication. Their direction coefficients favor reverse moves;
the actual saved trees independently verify those choices. This is an observable
weakness of the occupancy proxy, not a causal ablation or rejection of RL in
general. This proxy should not be adopted as the main accelerator.

| Seed | Lane | Verified / finite exhausted / unknown | Base attempts | Cold requests seconds | Training including online replay seconds | Separate lifecycle charge seconds |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Plain GCTS | 8 / 2 / 0 | 1152 | 14.561489 | 0 | 15.568617 |
| 1 | Fixed prior | 7 / 2 / 1 | 646 | 10.831865 | 0 | 13.422732 |
| 1 | Zero weights | 8 / 2 / 0 | 672 | 10.859066 | 0 | 13.449933 |
| 1 | Complete control | 8 / 2 / 0 | 669 | 11.368358 | 27.361655 | 65.207097 |
| 1 | Local progress | 8 / 2 / 0 | 1196 | 15.778886 | 27.338219 | 69.594190 |
| 7 | Plain GCTS | 8 / 2 / 0 | 1152 | 15.733116 | 0 | 16.740243 |
| 7 | Fixed prior | 7 / 2 / 1 | 645 | 11.167528 | 0 | 13.758395 |
| 7 | Zero weights | 8 / 2 / 0 | 672 | 11.232842 | 0 | 13.823709 |
| 7 | Complete control | 8 / 2 / 0 | 1152 | 15.932457 | 27.304941 | 69.714482 |
| 7 | Local progress | 8 / 2 / 0 | 1196 | 15.626732 | 27.435967 | 69.539784 |
| 19 | Plain GCTS | 8 / 2 / 0 | 1152 | 14.755299 | 0 | 15.762427 |
| 19 | Fixed prior | 8 / 2 / 0 | 669 | 11.229438 | 0 | 13.820305 |
| 19 | Zero weights | 7 / 2 / 1 | 638 | 11.297888 | 0 | 13.888755 |
| 19 | Complete control | 8 / 2 / 0 | 669 | 10.910608 | 27.354969 | 64.742662 |
| 19 | Local progress | 8 / 2 / 0 | 1196 | 15.493817 | 27.378856 | 69.349758 |

The common native compilation costs \(1.007127\) seconds; fresh donor discovery
and whole-library checking cost \(1.583740\); shared training catalogs including
independent inventory checks cost \(23.886217\). Online prefix gates cost about
\(4.2\) seconds per learner, inside the training column. Each lifecycle row charges
the full common compilation, reuse rows charge the full library, and each trained
row charges the entire shared catalog setup. Do not sum these rows: they are
separate per-policy costs with repeatedly charged common setup. No local training
cost is repaid on this family.

Evaluation uses five frozen lanes with rotating order, identical external problems,
fresh base catalogs, primitive candidate universes, root generations, scheduler,
five-second search wall and \(50000\) actual-placement budget. The fixed prior
is unknown on multiplication in seeds one and seven; the zero policy is unknown
there in seed nineteen. Those near-wall cutoffs remain unknown, and unequal-outcome
aggregates are not timing rankings. Three seeds on ten fixed evaluation statements
do not establish broad theorem generalization or statistical significance.

The producer finishes in \(394.679570\) seconds and has peak driver memory
\(1205911552\) bytes, including accumulated catalogs and traces. This is not a
per-lane memory comparison. There are \(168\) training native acceptances,
\(117\) evaluation acceptances, two donor acceptances and one whole-library
acceptance. Thirty evaluation requests exhaust finite controls; \(24\) training
and three evaluation requests remain unknown. The final audit verifies all
\(342\) executed training/evaluation prefixes, including all \(27\) open ones,
in addition to the original donor searches and hierarchy checks.

`audit_partial_proof_policy.py` imports no search, graph, policy, miner or catalog
producer. It independently recomputes all base inventories, every complete and
open DFS prefix, viable occupancy, cutoff boundaries, actual-choice order and
counts, policy pools/draws/gradients, both return and update chains, every online
gate, searched fragment windows, positive primitive proof expansions and native
program/input bindings. It passes in \(105.068606\) seconds. This is an
implementation audit, not a universal compiler soundness theorem or independent
native-instruction replay. The offline audit and full regression suite ran after
the measured producer completed; their reported durations are wall times, not
an acceleration comparison.

All \(453\) tests pass in \(116.950608\) wall seconds. The \(28\) new tests cover
complete-search and complete-return parity with the frozen engine, zero/wall/base
and inside-transaction cutoffs, rollback, censoring, unknown local updates without
theorem labels, native bonus gates, literal work recounts and independent replay
rejecting altered viability, occupancy, transaction steps, counters, final result
labels, progress returns, theorem bonuses and projected weights.

Reproduce from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_partial_proof_policy.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_partial_proof_policy.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_partial_policy_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_partial_policy_view.py
```

`docs/research/gcts-rl-renewal/partial-policy.html` shows the actual executed
prefix, open boundary, policy choices, rewards and coefficient changes, plus
all matched evaluation costs and certificates. The projection binds the full
audited artifact and exporter by SHA-256. The next priority is a genuinely coarse
checked proof interface, with certified expansion and distant markings, compared
against the primitive graph and a constraint-solver control. Broader grammar and
induction remain necessary for human-style mathematical search. Wang-style proof
tiles remain primary; Turtle/Penrose controls, learned certified failure markings,
arbitrary boundary composition, general compiler soundness and infinite-plane
research remain open. The overall goal remains active.

## Notebook 34: searched induction and certified proof-resource markings

Fresh point searches now discover proofs of \(\forall n\,(0+n=n)\) and
\(\forall n\,(1+n=S(n))\), relative to the displayed addition equations and
authorized natural-number induction schema. No derivation path, chosen induction
variable, previous proof, library or policy is supplied. This is an arithmetic
fragment with induction, rather than a claim to unrestricted Peano proof search.
All quantified target variables are offered as induction alternatives.

`induction_proof_catalogs.py` constructs the entire bounded term grammar and all
axiom instances, both rewrite directions, every contextual occurrence, and every
fixed-induction-hypothesis occurrence. Direct, base and conditional successor
equations coexist. The hypothesis is a fixed equality in free variables, never
an arbitrarily instantiable axiom. Generalization is a root inference with checked
side conditions. A two-input induction cell receives the closed base and closed
successor implication and establishes the original target with its original
quantifier order. Generic compiled inference definitions are supplied rules;
their selection, premise references and proof sequence are searched. Every
definition in the complete inventory is independently expanded before claiming
the inventory audit passed.

The fresh producer compares plain GCTS, dependency-height markings,
ancestral-cell markings and a classical binary arc-consistency/MRV control on
\(7\) externally nominated cases, totaling \(28\) requests. Each lane rebuilds
and validates its own identical catalog. The search wall is \(15\) seconds,
including representation construction, resource-bound computation and trace
recording; the attempt cap is \(50000\). Point attempts count placements;
classical attempts count assignments after propagation. Native acceptance and
catalog costs are included in cold request time. Lane order rotates across cases;
there is one timing run per lane/case, so no replicated or general speedup claim.

For \(\forall n\,(0+n=n)\), plain GCTS makes \(4454\) placement attempts and
takes \(9.890196\) cold seconds; the support-marked lane makes \(1123\)
attempts and takes \(2.677358\) cold seconds. Both use \(7\) proof cells and
expand to \(77\) independently checked primitive lines. The weaker depth lane
uses \(3862\) attempts and \(7.447124\) cold seconds. The classical control
uses \(12\) explicit assignments and \(0.511066\) cold seconds. Its work unit
differs from a placement attempt; support-test costs remain separately recorded.

For \(\forall n\,(1+n=S(n))\), support-marked GCTS finds a \(7\)-cell,
\(77\)-primitive-line proof in \(975\) placement attempts and \(7.037670\)
cold seconds. Plain and depth-marked GCTS remain unknown at the wall. The
classical control verifies this theorem in \(1.096803\) cold seconds. It also
discovers \(\forall n\,(0\cdot n=0)\), using \(8\) cells and \(105\)
expanded primitive lines in \(1.934710\) cold seconds; all point lanes remain
unknown for this request. The reader labels that proof as a classical discovery.

The larger target \(\forall a\forall b\,(S(a)+b=S(a+b))\) remains unknown in
every lane. Its complete grammar retains both induction alternatives \(a\) and
\(b\), with \(159\) terms, \(803\) formulas, \(1636\) rules and \(822\)
compiled definitions. We do not infer unprovability from the cutoff. Removing
induction authorization and shortening the left-zero envelope to \(6\) cells
exhaust their finite envelopes in all lanes. The shifted target
\(\forall n\,(0+n=S(n))\) exhausts with both certified markings and the
classical control; plain GCTS remains unknown. These are scoped finite controls.

### Sound resource bounds as actual point markings

`induction_proof_tiles.py` retains all original candidate types. No resource
classifier runs during search. The complete formula-rule hypergraph yields a
least dependency height and a stronger lower bound on distinct ancestral cells.
For each formula \(F\), its full backward formula cone \(C(F)\) includes every
syntactic premise edge, including cycles and unreachable alternatives. If a
rule's premise cones are pairwise disjoint, actual ancestral cell sets cannot
overlap, so their bounds may be added. Otherwise only their maximum is used.
Each inference adds one cell. Positive-cost relaxation starts with seeds at
\(1\); formulas with no finite derivation stay unreachable. The independent
auditor recomputes cones by per-formula backward traversal and bounds by
synchronous relaxation, then validates every recorded producer witness pass.

The fixed-point inequalities, followed by induction on an actual proof DAG,
show that a formula's bound \(b(F)\) is no greater than its distinct ancestral
cell count. At zero-based slot \(j\), it must satisfy \(b(F)\le j+1\).
Output and remote premise contacts write \(m=1\) at \((2j,4)\) if their bound
is unreachable or too large, and \(m=0\) otherwise. Fixed boundary zeros at
all these marking-only points eliminate impossible contacts through ordinary
mark agreement and the complete frontier/candidate graph. Every original exact
proof survives. The weaker depth lane marks outputs at \((2j,3)\). These are
certified redundant constraints, not learned failures or RL. For left-zero
addition, the ancestral bound is \(7\) and a \(7\)-cell proof is found; this
also certifies the minimum cell count in this particular compiled grammar.

The base engine follows the master contract: exact capacity \(12\), scalar
marking agreement, all required finite roots at generation zero, complete
incidence, global dead ends before forced moves, then earliest generation with
degree ties, and exact state/graph copies for rollback. All original point
solutions remain available. The classical control has separately labeled AC/MRV
semantics and the same original proof envelope.

### Evidence, reader and remaining gates

The independent auditor passes all \(28\) request traces in \(168.959831\)
seconds. It reconstructs every complete inventory, compiled definition,
resource bound, point graph, scheduler decision, classical support removal,
closed or open branch prefix and decoded proof. All \(7\) positive request
certificates receive full native acceptance, with program/input bindings audited.
Native instruction execution and universal compiler soundness remain trusted
layers. This is not an independent native-instruction replay result.

All \(512\) Python research tests pass in \(121.246\) unittest seconds. The
\(13\) new engine tests include shared/repeated-premise counterexamples,
disjoint-premise ancestry, unreachable cycles, independently checked complete
inventory, fixed hypothesis and schema authorization, preserved tiny solution
sets, remote-mark graph differential checks, exact rollback, and closed/open
prefix audits. The separate tile decoder checks \(22\) actual cells in
\(3\) proof records, validates all \(10\) axiom/hypothesis rewrites and
\(3\) induction joins, and rejects \(39\) mutations of ports, occupancy,
references, rewrite metadata, hypothesis scope, authorization and block
interfaces. Natural-language wording is an explanation of checked formula
steps, not an additional proof kernel.

The producer takes \(200.577199\) seconds, including \(0.965064\) seconds
for native compilation, and peaks at \(1196605440\) driver bytes. Full traces
are losslessly compressed into \(7\) immutable case files totaling
\(5462703\) bytes, each bound to its compressed and raw SHA-256 and lengths.
`induction-proofs-001.json` holds the measured source pins, external problems,
native program pin and full audit; `induction-proofs-view-001.json` is a separate
read-only projection bound to that final manifest. Historical measured sources
and evidence artifacts remain unchanged.

Reproduce from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_induction_proofs.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_induction_proofs.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_induction_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/export_induction_proofs.py
node research/gcts-rl-renewal/test_induction_tile_reading.cjs
```

`induction-proofs.html` shows the actual searched cells, formula/owner/resource
markings and remote contacts. Its human reading follows logical premise order,
separately recording actual search placement order. Each cell opens the exact
root inference; checked definitions and the full primitive expansion are
inspectable line by line. The browser checks the manifest and certificate hashes
and validates each tile's premise/output bindings before showing its reading.
A real initially eliminated candidate illustrates remote marking conflict.

This makes the requested proof-search idea more concrete: a statement can lead
to a checked induction argument without a human supplying that argument's
sequence. The search remains restricted by a goal-derived bounded grammar and
has no advantage over the classical control on these positive requests. The
next meaningful gate is fresh discovery and reuse of conditional proof fragments,
with RL proposing their compositions and the same library offered to classical
search. The two-variable statement is an open benchmark. Euclid-style geometric
obligations, unrestricted expressiveness, a uniform finite tile inventory,
certified learned failure markings, practical fixed/movable boundary composition
and infinite-plane constructions remain open. Turtle and Penrose stay occasional
geometric controls. The full research goal remains active.

## Notebook 35: fresh induction-fragment transfer with matched controls

Two new source searches discover the left-zero and left-one addition arguments,
with no supplied proof, library or policy. Every connected fragment of two or
three source proof cells is mined. Merging identical shapes yields \(11\)
schemas with \(22\) source occurrences, bound to their exact certificates and
cell members. Schemas retain inference families, normalized cell positions and
all premise offsets. Literal formulas, variables, hypothesis bodies and rewrite
AST paths are not copied as instance restrictions. Complete recipient rule
types and exact formula-port agreement determine the new instances.

These are proposals for valid recipient metatiles. They assert no new lemma or
pruning condition. Generalization remains a checked closed-root inference;
it never becomes an open-premise rule inferring \(\forall n\,P(n)\) from
an assumption \(P(n)\). The kernel rejects that eigenvariable violation.
All original singleton placements remain available.

### Results and full cost

All four lanes share the external theory, complete goal-derived grammar,
cell envelope and certified redundant resource constraints. Both motif lanes
receive the same fresh library. Two repetitions rotate lane order, with a
\(20\)-second search wall and \(50000\) expanded-attempt cap. Full failed
prefixes and open suffixes are retained.

For \(\forall a\forall b\,(S(a)+b=S(a+b))\), with \(11\) cells and
term bound \(5\), both GCTS motif runs discover the proof in \(341\) states
and \(349\) expanded placement attempts. Search times are \(15.242630\)
and \(15.028866\) seconds; cold query times are \(18.905595\) and
\(18.214289\). Both native executions accept after \(8372957\)
instructions. The certificate expands independently to \(146\) primitive
lines. The successful GCTS tiling selects two metatiles, on logical cells
\((1,2,3)\) and \((4,5)\), plus singleton tiles for the remaining cells.

Matched GCTS without motifs remains unknown in both runs. That discovery
difference does not provide a time-to-proof speedup ratio. Classical AC/MRV
also proves the theorem when given the same resource constraints, which the
Notebook 34 classical control did not receive. Its base lane uses \(2807\)
states and \(2806\) explicit assignments in both runs. With motifs it uses
\(6\) states and \(10\) constituent assignments, with three proposal trials, two on the accepted
path. Point placement attempts and classical assignments are different
units.

Mean classical cold query costs are \(15.097563\) seconds without motifs
and \(3.921776\) with the reused library. Fresh learning costs
\(13.177962\) seconds, including source searches, catalog validation, native
checks, mining, merging and source trace storage. A first classical motif query
therefore costs about \(17.099738\) seconds before common compilation, more
than the base query. Repeated timing replicas do not themselves demonstrate
workload amortization. Charge training once to either motif lane as an alternative
lifecycle comparison; broader recipient statements are still needed.

Transfer is mixed. For \(\forall n\,(0\cdot n=0)\), both GCTS lanes
remain unknown. Both classical lanes find the same accepted proof in \(13\)
states. Trying motifs raises explicit assignments from \(12\) to \(17\);
one of the three motif trials is on the accepted path; failed alternatives
are absent from it. Mean cold
cost rises from \(1.986120\) to \(2.074484\) seconds. There are \(16\)
complete recipient instances for multiplication and \(59\) for successor
addition. Missing-schema, shortened-envelope and shifted-target controls all
exhaust their specific envelopes, without a general non-provability claim.

### Encoding, checks and readable proofs

A metatile sums distinct constituent occupancies and unions compatible
formula/resource markings, with one atomic owner identity. Expansion preserves
the original formula/capacity problem; conversely, every original proof can
still use singleton tiles. Renaming private owner values on expansion preserves
those original constraints. Adding atomic types can change point degrees,
forced moves and scheduling. The equivalence concerns solution sets, not the
original primitive trace. Within the enlarged model, full incidence, global
dead/forced checks, earliest generation and copied rollback follow the master
contract, with generation-zero finite roots. Tiny exhaustive tests compare
all expanded solutions and every incremental graph, including remote marks.

Classical motifs reversibly assign their constituent variables, retaining
ordinary-value fallback. Already fixed variables still pay an explicit-assignment
cost. Its diagram is a checked point lift of the final assignment; overlapping
proposal descriptions are not counted as extra occupancy or atomic placements.

All \(530\) Python research tests pass in \(125.300\) unittest seconds.
The \(18\) new tests cover fresh provenance, complete recipient joins,
fixed-hypothesis family transfer, all tiny solutions, remote graph updates,
rollback, fallback, complete/open traces and altered graph/AC/witness events.
The independent audit passes all \(42\) source/evaluation requests in
\(202.002082\) seconds. It imports no miner, generator, graph, solver or
producer. It reconstructs source/recipient grammars, all source fragments and
recipient instances by exact relational joins, every graph and classical
support deletion, every executed prefix and open suffix, and proof/native
bindings. All \(12\) positive requests receive native acceptance. Compiler
and native instruction execution remain trusted.

The new reader validates \(63\) cells in \(7\) accepted records, actual
atomic marking unions or classical witness/proposal bindings, and rejects
\(55\) altered readings. Each cell shows its formula, ordinary English
statement, inference reason and clickable root line. All local definitions
and primitive lines can be examined. English explains a checked formula/rule
pair; it is not another proof kernel.

The producer takes \(230.544979\) seconds and peaks at \(1842970624\)
accumulated driver bytes. Seven lossless donor/evaluation shards total
\(8551711\) compressed bytes, binding raw/compressed bytes and lengths.
Every measured source is pinned; the projection binds the final audited
manifest. Historical measured source/evidence files remain unchanged.

Reproduce in a separate checkout from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_induction_cluster_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_induction_clusters.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_induction_clusters.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/export_induction_clusters.py
node research/gcts-rl-renewal/test_induction_cluster_reading.cjs
```

This supports automatic proof discovery and reusable geometric interfaces.
Classical search also benefits from the interfaces and remains faster, so a
distinctive GCTS advantage is still unproved. Next: a fresh RL policy for
composing/selecting validated proposals, with the same library and training
charge provided to classical controls. Broader grammar transfer, hierarchical
constructs, Euclid-style constructions, succinct statement boundaries and a
uniform finite computational tile inventory remain open. The bounded positional
grammar has not established unrestricted expressive reach or completeness.
Turtle and Penrose remain occasional geometry controls; practical fixed/movable
boundaries and certified infinite constructions remain in the active program.


## Notebook 36: fresh RL ordering of induction clusters

The preceding classical narrative has been corrected from the raw traces:
successor addition tries \(3\) proposals and retains \(2\) on its accepted
path; multiplication tries \(3\) and retains \(1\). The immutable proofs,
traces and reader already contained the correct paths. No measured evidence
was changed.

The new cold experiment receives only source statements, axioms and grammar
bounds. Its two bootstrap searches newly discover left-zero and left-one
addition proofs, then mine every connected two/three-cell fragment. They produce
\(11\) schemas with \(22\) certificate-bound source occurrences. The newly
reconstructed library happens to have the same bytes as Notebook 35; no prior
library or result is an input. The \(20\) subsequent source-only episodes
start from all-zero parameters and perform seeded sampling without replacement
of every applicable cluster. All source episodes produce native-accepted proofs.

The policy changes macro ordering only. Every singleton remains in the complete
fallback, and the same point/candidate graph performs global dead/forced checks,
earliest-generation branching and exact copied rollback. The underlying atomic
metatile expansion/equivalence is unchanged. Classical AC/MRV receives the same
policy/library, necessary resource constraints and ordinary-value fallback.
Both evaluation lanes use exactly the same feature meanings, applied to their
actual filled cells; classical propagation can produce a different state.

Features measure size, final-cell contact, relative location/span, internal
premises, filled external premises, premise distance, conditional/generalization/
induction families and progress. They do not inspect literal formulas, variables,
AST locations or teacher paths. Integer features use scale \(1024\), integer
parameters scale \(10^6\), and greedy evaluation uses exact integer dot
products with fixed ordering as a tie breaker. Each policy is frozen within an
episode. Only actually executed macro choices receive score gradients; the
unused sampled suffix receives none. Native acceptance precedes proof credit.

The episode return is
\[
R=\mathbf{1}_{\mathrm{accepted\ proof}}+\frac{1}{10}\frac{k}{n}-
\min\left(1,\frac{a}{A}\right),
\]
where \(k\) counts filled original proof cells, \(n\) is the envelope,
\(a\) counts constituent attempts and \(A\) is the declared cap. Unknown
cutoffs are not negative labels. Executed gradients receive the same return and
are averaged before a rate-\(0.2\) quantized parameter update. This initial
small experiment uses no learned value baseline; changed coefficients and
source success do not certify policy improvement.

The practical transfer gate fails. GCTS fixed ordering discovers
\(\forall a\forall b\,(S(a)+b=S(a+b))\) in both repetitions, at
\(341\) states / \(349\) expanded attempts. RL ordering remains unknown
at its \(20\)-second search walls, with \(461\) / \(459\) states and
\(470\) / \(468\) expanded attempts. No time-to-proof speedup ratio can
be calculated against those unknowns. Classical fixed ordering uses \(6\)
states and \(10\) assignments; RL uses \(22\) and \(28\). Both find
checked \(146\)-primitive-line proofs. Search-time means are nearly equal;
mean cold query costs are \(4.042239083\) for RL versus
\(4.151877937\) seconds for fixed ordering. The minor timing
difference does not repay training. Discovery/mining costs
\(10.389209917\) seconds and RL learning/native checks/
storage adds \(11.413561917\), giving first-query costs
\(25.845076958\) versus
\(14.541087854\) seconds before common
compilation. Two repetitions do not establish workload amortization.

On \(\forall n\,(0\cdot n=0)\), both GCTS orders remain unknown;
both classical orders use \(13\) states / \(17\) explicit assignments.
Missing-schema, shortened-envelope and shifted-target controls exhaust only
their nominated finite envelopes. Among \(40\) recipient requests,
\(10\) are exact, \(6\) unknown and \(24\) finite exhaustions.
Together with discovery and learning, all \(62\) requests pass independent
audit, and all \(32\) positives receive complete native acceptance.

The auditor imports no solver, policy, miner or producer. It independently
rebuilds inventories, connected fragments and complete recipient joins; every
point graph and AC deletion; every seeded draw, feature binding and executed
gradient; each reward and integer update; all complete/open prefixes and native
bindings. Its cost is \(164.661064\) seconds.
The \(544\)-test full research suite passes in \(118.446\) unittest
seconds. Fourteen new tests include exact feature parity, finite-difference
score gradients, zero-policy trace equivalence, adverse ordering with full
fallback, tri-state cutoffs and adversarial draw/gradient/update rejection.

The reader includes each actual source-episode proof as well as all accepted
recipient alternatives: \(27\) proof records,
\(203\) cells, \(51\) actual metatiles
and \(235\) rejected altered readings. Cells
retain readable formulas, English statements and inference reasons. Classical
proposal paths are distinct from atomic point-placement chronology.

The producer costs \(215.822446\) seconds, with an accumulated
driver peak of \(495730688\) bytes. Lossless source,
training and evaluation shards total \(1189537\)
compressed bytes. All \(39\) measured sources are pinned, and historical
source/evidence bytes remain unchanged. Development included a source-only
pilot and a stopped run before evaluation while fixing the episode statement
binding; those are not held-out evaluations or performance evidence. The
reported experiment restarts with zero policy and empty library.

Reproduce from the repository root in a separate checkout:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_induction_cluster_policy_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_induction_cluster_policy.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_induction_cluster_policy.py
PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/export_induction_cluster_policy.py
node research/gcts-rl-renewal/test_induction_cluster_policy_reading.cjs
```

This is evidence against this initial policy’s practical transfer, not against
RL or automated proof search in general. The exact marked search and structural
cluster transfer remain checkable contributions. Next: stronger source-only
training with variance control, broader statement grammars and hierarchical
cluster synthesis; retain matched classical access and full lifecycle costs.
Uniform finite mathematical tile encodings, general proof-search completeness,
Euclid-style constructions, practical fixed/movable tiling boundaries and
certified infinite constructions remain open in the active research program.

## Euclidean notebook 1: directed proof cells and separate geometry

The [separate Euclidean notebook](https://liuyao12.github.io/geometric-tree-search/docs/research/gcts-rl-renewal/euclidean-proofs.html?v=20261009-e1#reader)
uses no arithmetic functions or induction schema. Its declared foundation is
noncollinearity, equal segment lengths, equal unsigned angles, ordered triangle
congruence, SAS, ASA, corresponding parts and elementary reversal/symmetry rules.
It searches proof sequences; no human proof path, earlier witness, saved policy
or learned library is input.

The classical arc-consistency control discovers the internal base-angle part of
Euclid I.5 and its converse I.6, each in \(10\) cells, expanding into \(91\) and
\(90\) primitive lines. GCTS reaches the \(3\)-second pilot budget on both.
Both solvers discover the elementary vertex-order/noncollinearity lemma;
GCTS uses \(4\) states and \(3\) cells. This first geometry pilot shows no
distinctive GCTS advantage. It is a single cold trial per lane, with construction
and search included, rather than a statistical performance benchmark.

The modern congruence foundation is explicit and differs from Euclid's original
dependency order. The search does not prove SAS/ASA, reconstruct his auxiliary
constructions, or include the exterior-angle part of I.5. Diagrams are illustrative;
coordinates never enter the checker. The fragment grounds every admissible Horn
rule over three distinct free vertex names and keeps the whole backward goal
cone, including cycles. Five-premise congruence rules compile into four binary
cells. Fixed hypotheses are discharged as implications; checked universal
generalization closes the theorem after the point tiling.

Proof tiles have a fixed premise-to-conclusion direction: translation only,
with rotation and reflection forbidden. The current finite positional inventory
fixes each cell and premise offset; a uniform inventory reusable under arbitrary
translations is still open. Formula, ownership and certified resource markings
are blue, green and gold. IDs distinguish values within each layer. The earlier
arithmetic reader now uses the same layer convention for its actual formula and
ownership points. Color changes only the visualization.

All \(12\) search/control records pass an independent complete inventory and
full-prefix audit, including frontier/candidate graphs, decisions, exact copied
rollback, AC revisions, decoded interfaces and primitive expansion. All \(4\)
accepted requests have complete native acceptance with independently verified
code/input bindings. Removing SAS or ASA exhausts the respective weakened finite
fragment; shortening I.5 to \(9\) cells is exhausted by the classical control,
while GCTS reaches its budget. These controls do not refute the theorem.

Reproduction:

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/test_euclidean_proofs.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_euclidean_proofs.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_euclidean_proofs.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/export_euclidean_proof_notebook.py
    node research/gcts-rl-renewal/test_euclidean_reader.cjs

The compiler retains the master point-search contract: exact occupancy and
agreeing marks, complete bipartite bookkeeping, global dead/forced/earliest
generation selection, and exact rollback. All finite strip roots have generation
zero. The specialized finite syntax envelope and goal-cone compilation are
explicitly labeled. RL and learned geometric clusters remain future experiments.
The unfinished hierarchical arithmetic development is preserved separately and
is not part of this published geometry pilot.

## Symbolic object language and the Hilbert foundation

The user's further clarification fixes Hilbert's geometry as the research
foundation. Statements are symbolic formulas first; proof tiles then encode
symbolic inferences, formula IDs and dependencies. The object language has no
coordinate evaluator or geometric oracle. The tile layout uses separate proof
coordinates, with no connection to coordinates of the objects under discussion.
An illustrative triangle supplies no inference facts.

A post-search symbol-renaming control replaces every geometric predicate name
with an arbitrary table/chair/cup/furniture relation name, and replaces all
axiom names. All three displayed proofs remain accepted by the generic host,
primitive and native checkers. Every exact candidate and certified resource
marking is unchanged. A fresh elementary GCTS search has the identical complete
search tree and placements. Independent audit verifies the name bijection,
all interfaces, native input/code bindings, complete point inventories and both
full elementary graph/rollback traces; six altered-signature or missing-axiom
controls are rejected. This tests representation invariance, not discovery of
new theorems or arbitrary changes to the axioms.

The source baseline is [Hilbert's second edition, 1903, with the original text
and parallel translation](https://www.maths.tcd.ie/~dwilkins/Courses/MA232A/MA232A_Mich2017/HilbertAxioms_ParallelText.html).
Its congruence axiom III.6 gives remaining angle congruences. Full SAS congruence
and ASA are subsequent theorems. The present pilot assumes full SAS/ASA and must
remain labeled a comparison fragment; its certificates are not yet proofs
from Hilbert's complete axiom system.

The next milestone is a source-pinned planar formalization of incidence,
order and the literal congruence axioms, using point/line sorts represented by
explicit guards in the existing first-order checker. Rays, segments, angles
and noncollinearity need visible definitions rather than geometric callbacks.
Full SAS and ASA must enter as checked derived results. The parallel axiom
and a documented logical formulation of continuity follow separately; the
present checker has no continuity or completeness schema. Each result will
show its exact enabled axiom groups and definition/lemma dependencies.

Reproduce the renaming control after the audited Euclidean pilot:

    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/run_symbol_renaming.py
    PYTHONDONTWRITEBYTECODE=1 python3 research/gcts-rl-renewal/audit_symbol_renaming.py

The symbolic pipeline, arbitrary-name formula and explicit Hilbert status table
are in the [live notebook's foundation section](https://liuyao12.github.io/geometric-tree-search/docs/research/gcts-rl-renewal/euclidean-proofs.html?v=20261009-e1.1#symbolic-foundation).

## Notebook 37: actual Hilbert planar incidence

The first Hilbert fragment is now implemented in
[its own proof reader](https://liuyao12.github.io/geometric-tree-search/docs/research/gcts-rl-renewal/hilbert-proofs.html?v=20261010-h1#reader).
The planar axioms I.1–I.3 of the source edition are formalized with unary
point/line sort predicates, uninterpreted incidence and logical equality.
Existence uses the kernel abbreviation
\(\exists x\,P(x):=\neg\forall x\,\neg P(x)\).
Sort coverage, disjointness and incidence typing are displayed as presentation
declarations, separately from the geometric axioms. “Determine a line” in
I.1–I.2 is split into existence and uniqueness. Both clauses of I.3 are present.
This correspondence is explicitly reviewed; source hashes do not prove it.

Two fresh GCTS searches discover the planar part of Hilbert's first theorem
(two distinct lines have at most one common point) and an incidence-transfer
lemma (two lines sharing distinct points have the same incident points).
Their \(2\) and \(4\) selected cells expand into \(21\) and \(32\) ordinary
primitive lines. All four positive GCTS/classical requests have complete
native acceptance and independent primitive replay. The theories contain no
SAS, ASA, arithmetic or induction schema, construction functions, drawing
or coordinate oracle.

The compiler generates every sorted outer grounding, every orientation of
its propositional clauses, and every declared atomic equality substitution.
It retains the complete backward goal cone, including cycles. Collecting a
conjunction and expanding an instantiated axiom are authored generic logical
blocks. GCTS selects the proof and earlier references; no theorem-specific
proof sequence, supplied correspondence, development pickle, earlier proof,
policy or finite interpretation is an input. The native program is unchanged.
The finite sorted grammar and positional strip are specialized; inner
quantified formulas remain opaque, and witness elimination is not searched.

All \(14\) cold trial/control records pass independent complete inventory,
resource, point/AC prefix, decision and rollback audits. The missing-uniqueness,
short-strip and wrong-statement controls exhaust their declared finite grammar.
Separate finite interpretations satisfy the full incidence fragment, falsify
the deliberately wrong statement, and give countermodels for both conclusions
when uniqueness alone is removed. These interpretations are not models of
order or full Hilbert geometry, and never enter proof search. A renaming test
also checks the proof with table/chair/relation symbols.

GCTS uses \(3\) and \(8\) states; classical arc consistency uses \(1\) and
\(2\). The longer native check takes about \(25\) seconds and
\(239{,}592{,}485\) interpreter steps. The initial native step budget proved
insufficient; the full matrix was rerun with a fixed \(10^9\)-step gate.
This is one cold trial per control, with no performance advantage or RL claim.
The reader separates catalog/search, native verification and total cold costs.
Generic compilation and the full subsequent audit are additional overhead.

Reproduce in this order:

    python3 research/gcts-rl-renewal/run_hilbert_incidence.py
    python3 research/gcts-rl-renewal/audit_hilbert_incidence.py
    python3 research/gcts-rl-renewal/export_hilbert_incidence.py
    python3 research/gcts-rl-renewal/test_hilbert_incidence.py
    node research/gcts-rl-renewal/test_hilbert_reader.cjs

The browser reader verifies the actual colored point layers and rejects
\(44\) altered rows across the \(6\) cells. Both complete primitive proofs
have readable formulas and English. Global dead ends, global forced moves,
earliest-generation branching and exact rollback retain the master contract;
all finite strip roots have generation zero. No tile rotation/reflection is
available. Authored compiled blocks are not learned lemma clusters.

Next: searched witness introduction/elimination, explicit betweenness and
Pasch, then the literal congruence axioms and derived full SAS/ASA. The native
truth-assignment cost deserves an independently verified optimization. Full
Hilbert geometry, useful learned proof clusters, uniform reusable proof tiles,
practical arbitrary-region tiling, turtle/Penrose continuation and the wider
substitution/proof-system goals remain active and incomplete.

## Notebook 38: quantified Hilbert witness proofs

The foundation remains the frozen symbolic planar incidence fragment from
notebook 37. `quantified_proof_rules.py` compiles generic existential
introduction/elimination, universal scope and distribution into the unchanged
FOL kernel. Generalization of a free theorem remains an explicit root tile;
it cannot be hidden inside a block whose open premise contains that variable.
Temporary conditions remain inside implication formulas, and escaping
witnesses are rejected. `hilbert_quantified_tiles.py` hygienically instantiates
the current outer binder after capture avoidance, including collisions with
later role names.

The uniform bounded backward grammar includes all declared productions and
cycles. The target, source syntax and finite bounds generate its inventory;
no theorem proof, stored policy, finite interpretation or coordinate fact is
input. Existential introduction is restricted to binder parameters, context
extension to two layers, and formulas to the declared node bound. Generic
context transport is enabled for the line/point target and disabled for the
joining-line target, as calibrated in development. This is an authored
specialized proof calculus, not a complete first-order prover or a uniform
four-edge Wang inventory. No RL is used in this experiment.

Fixed cold trials with a 30-second search limit and 10,000-attempt limit:

| Statement | GCTS | Classical AC/MRV | Primitive certificate |
| --- | --- | --- | --- |
| Every line contains a point | 10 cells; 229 states; 228 attempts | 5 states; 4 assignments | 46 lines |
| Two distinct points have a unique joining line | Unknown at the search budget; 83 states | 12 cells; 12 states; 11 assignments | 65 lines |

All three positive requests pass independent primitive replay and complete
native checking with a fixed one-billion-step gate. All 14 positive/control
records pass independent complete grammar reconstruction, every block
expansion, full point/CSP prefix and rollback audit, resource bounds and native
binding. Relevant axiom omissions and one-cell-shorter strips exhaust these
finite grammars. Separate abstract incidence models show that an empty line,
a missing joining line and nonunique lines falsify the relevant statements
while preserving all the other axioms. Their membership tables never enter
search. These results show automated proof discovery and no distinctive
GCTS speed advantage.

The separate HTML reader shows 22 directed cells, four explicit binder cells,
full formulas and exact English translations, colored point values, and 111
primitive lines across its two selected proofs. It validates all cells and
rejects 140 mutations. For the CSP proof, its diagram is the independently
reconstructed equivalent GCTS point encoding, not the internal CSP data.
The complete ~96 MB trace is distributed as deterministic gzip; the reader
records both the archive hash and the uncompressed hash. It does not fetch
that archive during normal reading.

Reproduce:

```sh
python3 research/gcts-rl-renewal/test_hilbert_quantified.py
python3 research/gcts-rl-renewal/run_hilbert_quantified.py
python3 research/gcts-rl-renewal/audit_hilbert_quantified.py
python3 research/gcts-rl-renewal/export_hilbert_quantified.py
python3 research/gcts-rl-renewal/run_hilbert_quantified_validation.py --node /path/to/node
```

To audit the published trace without rerunning search, decompress
`docs/research/gcts-rl-renewal/hilbert-quantified-001.json.gz` into the sibling
`.json` file first. The producer reads no archive or prior proof. The native
compile/runtime costs and subsequent independent audit are separate from the
reported cold per-query costs. Full Hilbert geometry, learned quantified
clusters, uniform translation-reusable tiles and the wider practical/infinite
tiling objectives remain active.

## Witness family transfer and one shared inventory (2026-10-10)

`hilbert-clusters.html` is notebook 39. One freshly discovered, completely
native-accepted line/point proof supplies all connected two/three-cell fragments:
17 source occurrences merge into 16 family schemas. Exact indexed joins retain
all compatible recipient rule/formula/contact instances and every base fallback.
The unique-joining recipient has 7,383 instances. Each of two rotating replicas
finds its GCTS proof in 19 states and 22 expanded attempts with two actual
three-cell clusters; base GCTS reaches the 30-second search budget. CSP uses
12 states without families and 7 with them. On reordered existence, GCTS uses
901 versus 195 states, and CSP 22 versus 3. Learning costs 9.9459 seconds;
first-query costs add this once to either cluster lane. No RL is used here.

The 29 source/recipient records receive complete independent grammar, block,
cluster provenance, whole instance, point/CSP prefix, rollback, resource and
native-binding audits. All 15 positive requests have complete acceptance by the
unchanged checker. The manifest binds deterministic compressed case archives;
normal reading uses a separate projection. Three actual GCTS proofs show 29
cells, four selected clusters and 148 primitive lines. Reader validation rejects
390 altered records; four exact join regressions pass.

The original measured auditor expected a nonexistent statement `theory` field.
The corrected `audit_hilbert_witness_clusters_v2.py` binds the complete catalog
foundation instead, without changing measured search files or traces. It also
reconstructs the frozen merger's provenance alias: a duplicate motif appends
its source to the first occurrence's shared list. Every connected occurrence
and the resulting whole library are reconstructed, including this storage
behavior. The corrected audit records its own source hash separately.

The user's chosen architecture is **one shared first-order base inventory**,
with explicit connectives, equality, quantifiers, substitution and scope, and
arithmetic/Hilbert axiom declarations encoded as data. Readability and useful
inferences take precedence over minimum tile count. A fixed finite inventory
requires syntax strings over a fixed alphabet, rather than a new whole-formula
color for each query. That uniform encoding is not implemented by the current
bounded compilers. Current learned families vary formulas and translate fixed
relative offsets. Receptor-dependent layout, recursive composition, training
selection and cross-theory use of one unchanged inventory are next gates.
Aperiodicity alone does not supply a universal interpreter. A computation
encoding and proof of correspondence with finite accepting patches are needed;
no universal or aperiodic base set is claimed for the current notebooks.

Existing lemma matching and automated learning-based proof search are covered
in the notebook's primary-source references. Our evidence supports automatic
proof selection and learned reuse, not superiority to established theorem
provers or a practical RL advantage. The CSP control benefits from the same
families and uses fewer states. The broader research goal remains active.

```sh
python3 research/gcts-rl-renewal/run_hilbert_witness_clusters.py
python3 research/gcts-rl-renewal/audit_hilbert_witness_clusters_v2.py
python3 research/gcts-rl-renewal/export_hilbert_witness_clusters.py
python3 research/gcts-rl-renewal/run_hilbert_cluster_validation.py --node /path/to/node
```

## Notebook 40: one fixed finite palette, two fresh proof inputs

The chosen architecture is now tested at the **shared-checking** level.
`shared_wang_inventory.py` binds the unchanged Notebook 25 literal table to a
single finite Wang palette. It encodes configuration symbols and overlapping
triples without allocating the entire palette. The four disjoint families
contain \(216000\) headless copies, \(64440169200\) central-head types and
\(99851616000\) types for each side-head position, totaling
\(264143617200\). The \(60\)-symbol, \(462276\)-state machine and inventory
fingerprint do not depend on the theory, statement or formula names. This
large infrastructural palette is not a practical everyday proof vocabulary.

`run_shared_wang.py` first discovers both proofs afresh with the unchanged
complete point engine. The addition fragment proves
\(\forall a\,(a+S(0)=S(a))\) in \(5\) states and \(4\) attempts using
\(3\) semantic cells, expanding into \(24\) primitive lines. The full
planar-incidence input and explicit sort presentation prove
\(\forall a\forall u\,(\operatorname{Inc}(a,u)\Rightarrow
\operatorname{Point}(a))\) in \(8\) states and \(7\) attempts using
\(2\) semantic cells and \(15\) primitive lines. These are deliberately
small cross-theory infrastructure controls, not new mathematical discoveries.
No stored proof, learned library, policy, model or coordinate oracle enters
either search. The logical calculus and compiled rewrite/axiom families are
authored; search selects their actual sequence and earlier references.

Both resulting certificates execute on the identical frozen literal table.
Only encoded theory, target and certificate boundary data change. Arithmetic
accepts after \(1948300359\) selected-symbol operations and
\(28008765725500\) literal transitions; incidence accepts after
\(2213744978\) symbol operations and \(46539576605650\) literal transitions.
Literal wall times are \(126.356398\) and \(155.594288\) seconds. Fresh search
and decoding cost \(0.044762\) and \(0.040207\) seconds; full production
costs \(343.147068\) seconds including native compilation, independent
symbol executions, negative controls and export. No performance benefit is
claimed. The literal interpreter accelerates exact self-copy sweeps while
counting every represented transition.

`audit_shared_wang.py` imports neither the producer nor its inventory class.
It checks all \(17899987\) defined literal transitions, independently
reconstructs both complete finite grammars and every point-search decision,
checks exact proof decoding, constructs and inspects both canonical request
heaps, and reruns both complete symbol computations. The full outputs, counts
and event digests agree with literal execution. Independently replayed prefixes
bind the \(130\) pictured local squares to the actual input requests; all
\(650\) altered tile readings reject. Both wrong fixed-target controls reject,
and the zero-step control stays unknown. The successful audit costs
\(70.395781\) seconds. A preliminary audit reached the incidence grammar and
stopped because canonical JSON sorted binder-map keys. The corrected auditor
recovers their order from the unchanged axiom syntax and checks exact binder
membership. No measured producer, proof, search trace or machine changed.

The reader displays actual translation-only squares with colored vertical
symbol and horizontal pair markings, exact identities and scalar/ordered-pair
values. Its separate readable row translates each semantic cell into a formula
and words, and opens every primitive line and local checked block. These
semantic cells remain query-grounded proof-search objects, distinct from the
literal four-edge base set. Every displayed line, table row and statistic is
bound to the audited data. Four inventory tests agree with the older independent
radius-one compiler; the reader rejects \(1077\) mutations. Browser checks cover
both inputs, marking layers, cell selection, proof expansion, successful
typesetting and absence of horizontal page overflow.

**The fixed-inventory proof-search gate remains open.** Next is a common logical
macro compiler with inspectable expansions into this same palette, preserving
open assumptions, capture avoidance, scope and complete primitive fallback.
Readable connective, quantifier, equality and lemma families should be checked
responses over the core, not new whole-formula colors. Existing compressed
response infrastructure supports expansions, but a general practical logical
cluster compiler and search over the uniform core are not implemented. General
computable axiom-enumeration certificates, formal upstream compiler/kernel
soundness, adaptable receptor layouts, recursive learned promotion and net RL
benefit also remain open. The broader research goal stays active.

```sh
python3 research/gcts-rl-renewal/run_shared_wang.py
python3 research/gcts-rl-renewal/audit_shared_wang.py
python3 research/gcts-rl-renewal/export_shared_wang.py
python3 research/gcts-rl-renewal/validate_shared_wang.py
```

## Notebook 41: actual per-inference clusters and the polyomino proposal

`logical-wang-clusters.html` connects readable logical commands to concrete
fragments of the unchanged Notebook 40 fixed checker. The observed compiler
changes only compression cut points. It runs the same finite selected-symbol
transition table, with no formula, parser, inference or logical callbacks in
its native execution. Observation metadata identifies the reviewed non-sweep
entry to the proof-line loop; it never changes execution or acceptance.

The controls explicitly reuse the two discovered arithmetic/incidence
certificates and four authored rule/scope certificates. They produce
\(75\) actual line fragments over \(85\) decoded checkpoints: \(28\) arithmetic,
\(17\) incidence, one quantifier-distribution, \(26\) addition-induction,
two open-premise-generalization and one captured-instantiation fragments.
All eleven command forms have successful instances. Two attempted commands
reject. Root commands and commands inside lemma definitions are counted here;
this is different from earlier expanded primitive-line counts.

Production costs \(214.661\) seconds, including native compilation, building,
deriving and compressed transport. The successful independent audit costs
\(126.663\) seconds. Every grammar node is derived again from primitive symbol
actions and exact copy-sweep laws. Every observed response is independently
applied to the actual incoming tapes, cursors and physical head. Its heap and
registers are decoded and bound to the theory, target, hypotheses, forbidden
variables, prior checked lemma registry, prior facts and remaining proof
commands. Exact affine costs and full final tapes match earlier pinned runs.
The audit rejects \(46\) changed context/boundary/fragment bindings. Its first
attempt exposed a test-scope error: a rejected block can stop before the root
is reached. Binding the complete encoded input before testing a changed root
corrects that audit; no measured producer or execution was altered.

The reader binds all displayed fields to the audited projection and displays
\(2025\) actual cropped literal squares, from \(75\) three-transition entry
samples. These samples are explicitly not whole inference computations.
Three focused native tests compare new observed fragments with the old
whole-run builder/checker, including right/left scans, cross-band writes,
nonzero incoming physical heads, rejection and forged observation IDs.
The reader rejects \(1384\) mutations. Literal colors remain exact scalar or
ordered-pair values; response masks are admissible symbol sets and are not
set-valued GCTS markings. Dense rectangles have full physical tape width and
blank side guards, with exact heights from the operational transition costs.
Their huge dense area is not exported. Full compressed grammars, checkpoints
and derived response artifacts are published for inspection.

**Conformance:** this is an operational cluster compiler/verification adapter,
not a new GCTS search lane. No candidate universe, scheduler, pruning,
rollback, marking learner or RL proposal policy is changed. The literal point
model and fixed inventory remain unchanged. Each instance is grounded in its
actual context and layout. Parametric inference families, adaptable receptor
layouts, direct fixed-core proof search and a net RL advantage remain open;
the broad research goal stays active.

The user's polyomino suggestion is now a separate research gate: compile the
validity conditions into one uncolored, translation-only polyomino inventory
and the encoded statement/acceptance boundary. The final checker must ignore
learned GCTS search markings. Wang-to-polyomino reductions provide direct
precedent: [Golomb (1970)](https://doi.org/10.1016/S0021-9800(70)80055-2),
[Ollinger (2009)](https://doi.org/10.1007/978-3-642-00982-2_54), and
[Yang and Zhang (2024)](https://arxiv.org/abs/2403.13472). These are
computational/geometric expressivity results, not measurements of practical
proof search. [HOList/DeepHOL (2019)](https://arxiv.org/abs/1904.03241) supplies
precedent for RL-guided theorem proving on top of trusted logical checking.
The particular polyomino/GCTS combination has no established advantage here.

A forward encoding alone is insufficient. Prove reverse decoding for every
allowed completed finite region, including macro alignment, intended input
and acceptance framing, and exclusion or decoding of alternate decompositions.
A variable-tile-set plane undecidability theorem does not by itself establish
one fixed practical finite proof-certificate system. The input should change
only the encoded region/boundary, with the base inventory fixed. Ranking by
markings preserves complete primitive fallback under fair search. Proved
redundant markings may prune; unproved hypotheses may restrict exploration,
but failure remains unknown for the unmarked problem. A successful tiling
that passes the unmarked verifier remains valid regardless of the search
heuristic. No polyomino proof compiler has yet been implemented.

```sh
python3 research/gcts-rl-renewal/run_logical_wang_clusters.py
python3 research/gcts-rl-renewal/audit_logical_wang_clusters.py
python3 research/gcts-rl-renewal/export_logical_wang_clusters.py
python3 research/gcts-rl-renewal/validate_logical_wang_clusters.py
```

### Checking cost and direct propositional receptors

Checking cost is the priority; the known color-to-notch encoding is not itself
a new contribution. For \(M\) marking assignments, exact point/channel indexing
and agreement take expected \(O(M)\) dictionary work plus exact value comparison,
or deterministic \(O(M\log M)\) sorting. Distant support does not require all-pairs
comparison. Hashing is only an index; actual keys and values are compared.
Occupancy and full target coverage are checked separately. Internal certified
clusters can be reused, with each use bound to its actual definition,
parameters, scope/context and kernel version. Current low-level response
checks cost \(27.333\) seconds for arithmetic and \(31.627\) for incidence;
these are not timings of simple marking agreement.

The next direct design gate is propositional inference through extended
marking support. A modus-ponens instance at line \(k\) references prior lines
\(i,j\) and puts \(\phi(A)\), \(\phi(A\Rightarrow B)\), \(\phi(B)\) at their
formula ports. The source and use assignments must agree exactly. The
allowed inference family must enforce the implication's structure and
checked hypothesis/axiom origins; equality of arbitrary labels alone does
not establish inference. Sparse references avoid copying the entire proof
history onto every line. RL may propose which lines to connect, as in the
attention analogy, while proof matching uses exact symbolic values.

Whole-formula IDs are suitable only as a bounded symbolic prototype. To
realize one fixed finite literal inventory, compile fixed-alphabet formula
encodings into syntax and routing clusters, preserving full string or
certified canonical DAG equality. Formula length and reference distance
change assemblies, not base tile types. Logical rule markings are part of
validity and must be checked (or replaced by verified symbolic equivalents);
learned search-only markings may be omitted. Quantifiers later require
capture avoidance and scope interfaces. The proposed direct compiler and
fresh propositional search have not yet been implemented. Compare identical
inventories with forward chaining/CSP and measure sparse marking, symbolic
proof and certified cluster checks separately. Broad goal remains active.

## Notebook 42: direct finite-alphabet propositional receptors

The direct design now has a bounded implementation in
[the separate reader](../../docs/research/gcts-rl-renewal/propositional-receptors.html).
The existing `turtle.State`/`Graph` engine is reused unchanged. A positional
adapter enumerates every inference/reference instance; no theorem proof is
provided. Its query-independent primitive catalog has \(288\) explicit
\(H_1,H_2,H_3\) axiom instances and \(708\) modus-ponens instances, generated
from \(P,Q\) and the four implications between them as schema parameters.
Every formula is a prefix word in the fixed alphabet `P,Q,i,n,e`, with `e`
as terminator. Scope is the assigned value \(0\). Formula IDs are not marking
values. The target and given hypotheses constrain exact boundary ports.

A cold graph search discovers \(\vdash P\Rightarrow P\) in \(5\) primitive
lines and \(220\) visited states. It actually places slots in the order
\(5,1,4,2,3\), using distant backward marking constraints. Other fresh
discoveries include weakening, two successive premise connections and
classical contraposition. No general tautology oracle supplies these lines.
The discovered identity certificate becomes a substitution-dependent logical
family, and fresh search uses that family with weakening to obtain
\(\vdash P\Rightarrow(Q\Rightarrow Q)\), in \(3\) commands expanding to
\(7\) primitive lines.

Substitution preserves each axiom schema and modus ponens, hence preserves
the complete discovered identity proof. Each used concrete expansion is
also checked independently. However, a family use is currently a derived
proof-cell rule with a **logical** expansion. A capacity-preserving geometric
decomposition of that one occupied cell into its primitive cells is not
established. Compound identity uses instantiated schema parameters outside
the initial bounded pool; this changes the bounded inventory's expressivity,
rather than just compressing an existing five-slot certificate. All compared
methods receive the same family-enabled inventory within that condition.
Direct lowering of these adaptable families into the previously fixed Wang
inventory remains open.

REINFORCE trains on \(24\) fresh rollouts of \(Q\Rightarrow Q\), with one
successful proof. It proposes variable-length continuation clusters of
\(1\)–\(3\) actual proof-cell placements, validated through the complete
global scheduler. Every base alternative remains available. The independent
auditor reproduces the actual seeded choices, rewards, gradients and all
eight numeric weights. Training plus its candidate compilation costs
\(2.885\) seconds. The evaluation is a weak atom-renaming transfer test,
not a demonstration of structural generalization.

For identity, ordinary point search takes \(5.445\) seconds, RL-guided point
search \(5.848\) seconds, and both visit \(220\) states. Compilation is
charged separately in the tables. Ordinary saturation finds the same
five-line proof in about \(0.5\) milliseconds. Chronological DFS is a
matched exact-length grammar control but reaches its \(6000\)-node budget
on identity. Saturation shares known formulas and has no exact slot-count
bound, so its recovered length is displayed explicitly. It finds a seven-line
compound identity proof while the five-slot ground envelope exhausts; these
results are consistent. Primitive seven-slot GCTS search for the family
composition conclusion reaches its \(12\)-second budget, while its
family-enabled three-slot search succeeds. Saturation also uses that family
efficiently, and already solves the primitive problem in under a millisecond.
There is no distinctive GCTS speed advantage or net RL benefit here.

Measured sparse agreement costs roughly \(3\)–\(13\) microseconds on
\(14\)–\(102\) actual assignments. Median logical expansion checks cost
roughly \(15\)–\(156\) microseconds. These \(80\)-repeat microbenchmarks
use already decoded objects and exclude parsing, transport and inventory
binding; the full independent certificate check is reported separately.
The production run costs \(72.163\) seconds. Process peak memory is about
\(1019\) megabytes, across the whole run rather than one lane. Explicit
ground candidate construction and graph snapshots are the current bottleneck.

The independent audit costs \(7.244\) seconds. It checks all terminal point
search trees including complete negative envelopes, every used point tile,
the displayed proof's exact decoding, all primitive and family expansions,
the independent task registry, graph samples and continuation proposals. It
rejects \(38\) mutations. Unknown budgets are not negative certificates.
Fourteen conformance tests cover complete forward/reverse incidence, remote
mark-only updates, prefix termination, global scheduling, exact rollback,
shared fractional candidates, and equality of tiny point/logical certificate
sets. An initial reader-comparison audit mismatch was only list/tuple
normalization for a family's serialized expansion; the producer and measured
executions were unchanged. The auditor normalizes both before comparison.

**Conformance:** required point \((2j,0)\), capacity \(12\); scope point
\((2j,1)\); token \(r\) at \((2j,2+r)\). All required slots are generation
\(0\) roots; placed tile generations are \(1\). Positive support is one
slot; finite marking support includes all referenced earlier ports, including
occupied and mark-only points outside the frontier. Complete ground families
and all backward references are declared. Transformations are identity,
not rotations. This is a positional family adaptation, not a claim of a
new fixed translation-invariant finite inventory. Logical markings define
validity; no learned redundant marking synthesis is implemented. Quantified
substitution, capture avoidance, context transitions, family-to-literal
compilation, net RL value and the broad turtle/Penrose certificates remain
open. The original goal remains active.

```sh
python3 research/gcts-rl-renewal/run_propositional_receptors.py
python3 research/gcts-rl-renewal/audit_propositional_receptors.py
python3 -m unittest discover -s research/gcts-rl-renewal -p test_propositional_receptors.py
```


## Notebook 43: discovered propositional families to the fixed Wang core

[The separate reader](../../docs/research/gcts-rl-renewal/propositional-wang.html)
connects the bounded direct receptor model to the unchanged common literal core.
The generic syntax compiler accepts checked source proofs, an atom-to-formula
mapping and an explicit first-order signature. It preserves every primitive line
of each concrete family definition, binds backward references, checks the complete
request and emits only encoded input. Hypotheses become exactly declared closed
premise axioms; quantified open-premise transport is not implemented.

A fresh three-slot search finds \(Q\Rightarrow(P\Rightarrow P)\) using
Notebook 42's actually discovered identity family. No proof path is supplied.
This exchanges the two atoms of the earlier family-weakening theorem; it does not
establish structural generalization. Both ordinary and frozen-policy searches
visit \(8\) states. Their search times are \(0.025801\) and
\(0.028465\) seconds, with candidate construction \(0.072794\) and
\(0.072229\) seconds. Reused policy training costs \(2.885\) seconds.
There is no net RL advantage or new classical-method speed comparison.

Five certificates accept: the fresh hierarchy, the earlier primitive identity,
the earlier compound identity-family instance, and two symbolic formula transports.
For arithmetic, the new one-slot identity template substitutes
\(A=\forall x\,(x+0=x)\). For symbolic Hilbert syntax it substitutes
\(A=\forall x\forall u\,(\operatorname{Inc}(x,u)\Rightarrow
\operatorname{Point}(x))\). Both prove only \(A\Rightarrow A\), with
no domain axioms; neither proves \(A\). Two deliberately altered certificates
reject: an invalid first formula in a family definition and a changed fixed target.
Rejection is not a non-derivability result.

The program, selected-symbol code, literal transition table and inventory
fingerprint are exactly the pinned Notebook 40 versions. Fresh native executions
agree with their full derived responses and all final register bands. Every
compression node is independently derived again. The audit reconstructs all
\(51\) contexts and binds \(40\) inference fragments to actual source
lines, definitions, heap values, cursors, theory, target, checked inventory, prior
facts and pending commands. It independently replays all fresh terminal point
search trees and rejects \(70\) source/context/response mutations. Production
costs \(256.036\) seconds including \(1.534\) seconds native executable
compilation; independent audit costs \(58.297\) seconds. Per-case syntax,
builder, response derivation, literal execution and independent audit times are
reported separately. Exact scan acceleration is used by the actual literal runner.

Nine compiler regressions cover previous discoveries, hypothesis reference shifts,
full primitive expansions, symbolic signatures, invalid prefixes/parameters,
future references and definition deduplication. The complete reader is bound to
its audited projection and frozen bootstrap. It validates \(1080\) actual
cropped tile instances and rejects \(1155\) reader mutations. All seven cases
and three marking layers render with no math errors or outer page overflow.
The displayed entry samples are \(9\)-column, \(3\)-transition crops,
not whole inference rectangles. Most logical checking occurs later.

**Conformance and remaining scope:** the existing complete point graph, global
scheduler, exact rollback, finite marking alphabet and validated RL continuation
proposals are unchanged. This is a generic syntax-to-core compiler, not a new
search engine. It creates a fresh operational rectangle using the frozen literal
palette. A capacity-preserving geometric decomposition of one semantic family
slot into its primitive cells remains open. Concrete response fragments remain
bound to receiver context and layout; cross-request cache transport is not proved.
Search operates over semantic families, not directly over literal tiles. Universal
formal compiler/kernel soundness, adaptive cluster geometry, quantified open
premises, learned redundant failure markings, substantial domain-theorem discovery
and the original turtle/Penrose objectives remain active.

```sh
python3 research/gcts-rl-renewal/run_propositional_wang.py
python3 research/gcts-rl-renewal/audit_propositional_wang.py
python3 research/gcts-rl-renewal/export_propositional_wang.py
python3 research/gcts-rl-renewal/validate_propositional_wang.py
```


## Notebook 44: exact factored propositional receptor domains

[The separate reader](../../docs/research/gcts-rl-renewal/factored-receptors.html)
removes the explicit rule/reference placement product from the bounded point
search. Rule IDs and their iteration order remain canonical. Schema instances
are generated lazily. For modus ponens, independently compatible earlier ports
form two sets, \(X\) and \(Y\), with exact domain size
\(|X||Y|-|X\cap Y|\). Integer masks store the sets; complete iteration streams
all distinct reference pairs. The finite implication catalog is still built.

Global dead ends precede forced moves, followed by earliest generation and then
degree ties. Each candidate's only occupied support is its own full-capacity
proof point, so the complete reverse incidence is a singleton. New complete
formula ports update their own unfilled slot and every later slot. Copies restore
the exact point state and factor domains. This is a specialization to complete
canonical words and single-slot placements; arbitrary partial character marks,
fractional/shared occupied support and extra marking channels are unsupported.

Fresh search receives axioms, statements and finite bounds, without proof paths.
A query-independent pool of \(20\) parameters produces \(33352\) primitive rules.
It discovers \(P\Rightarrow Q\) from \(\neg\neg P\Rightarrow\neg\neg Q\)
in four lines, \(\neg P\Rightarrow\neg P\) in five, and
\(\neg P\Rightarrow(Q\Rightarrow Q)\) with a three-command family composition.
The identity family is promoted from this run's fresh primitive identity proof;
its use has the same logical-expansion scope as Notebook 42.

| Case | Factored total seconds | Ground total seconds | Factor search states | Saturation search seconds |
| --- | --- | --- | --- | --- |
| Plain identity | 0.049325 | 5.725634 | 220 | 0.000491 |
| Closed atom, one slot | 0.001681 | 0.003555 | 1 | 0.000952 |
| Double-negation premise | 2.296796 | Not run | 200 | 0.019120 |
| Negated identity | 4.221706 | Not run | 1808 | 0.011031 |
| Negated identity family | 0.080876 | 0.177472 | 2 | 0.011408 |
| Negated family weakening | 0.119330 | Not run | 18 | 0.018933 |

Factored totals include its catalog construction, model creation and search.
Ground totals include placement construction and search using the same prepared
rule catalog; shared independent inventory verification is outside both times.
All three ground/factor terminal trees match exactly. Identity improves by about
\(116\) times and materializes \(218\) used placements from a declared
\(15600\)-candidate universe. Ground cases above the predeclared
\(50000\)-candidate cap are not run; those omissions are not measured failures.
Saturation uses the same finite inventory, shares facts and has no exact slot-count
bound; its displayed search time excludes common catalog construction. Recovered
proof lengths and whether they fit the slot bound are retained. Classical
saturation remains faster. Frozen RL changes no state counts; reused prior
training costs \(2.885\) seconds separately. These are single-run measurements.

The independent audit reconstructs all rule inventories and candidate degrees by
explicit short-reference-pair enumeration. It replays every terminal search tree,
checks every positive point certificate and primitive expansion, verifies every
actual factor frame, and reconstructs all \(46\) recorded greedy policy proposal
steps from the frozen scores. It rejects \(34\) corrupted records. Search
production costs \(40.132\) seconds and audit \(33.093\) seconds. Whole-process
peak memory is \(210829312\) bytes across all lanes, not a per-lane comparison.

The new conditional proof compiles to the unchanged literal Wang core. Its exact
closed hypothesis is declared as premise axiom, emitted first and referenced with
the corresponding index shift. All five machine commands accept. Independent
response derivation reconstructs their complete input/output contexts, target,
theory, prior facts, pending commands and literal fragment costs. Actual execution
agrees on all register bands; the fixed inventory fingerprint is unchanged. Exact
scan acceleration is used. Native production costs \(23.627\) seconds and its
independent audit \(5.917\) seconds; three altered premise/target/reference
transports reject.

Ten regressions test inventories, schema unification, every small mask product,
complete partial-state forward/reverse incidence, remote ports, global scheduling,
rollback, matched terminal trees, budget scope and family expansion. Reader
validation checks all five positive proofs and five native commands, rejects
\(413\) altered projections and binds the complete projection to both audits.
The colored cells are actual direct-search point markings, not literal Wang
squares. Quantified receptors, certified cross-request caching, adaptive geometric
clusters, learned redundant failure markings, useful RL, stronger comparisons and
the original turtle/Penrose objectives remain active.

```sh
python3 research/gcts-rl-renewal/run_factored_receptors.py
python3 research/gcts-rl-renewal/audit_factored_receptors.py
python3 research/gcts-rl-renewal/run_factored_wang.py
python3 research/gcts-rl-renewal/audit_factored_wang.py
python3 research/gcts-rl-renewal/export_factored_receptors.py
python3 research/gcts-rl-renewal/validate_factored_receptors.py
```

## Notebook 45: quantified receptors, actual scope and predicate families

[The quantified reader](../../docs/research/gcts-rl-renewal/quantified-receptors.html)
extends the bounded direct point model to first-order formulas. The declared
signature, closed theory axioms, open hypotheses, terms, variables and finite
instantiation/wrapping bounds generate the inventory independently of the target.
No proof path is supplied. Capture-safe universal elimination, generalization,
modus ponens and conjunction projection have all eligible finite instances.
Existential notation abbreviates \(\neg\forall\neg\); witness search is absent.

Each line fills one capacity-\(12\) slot. Its canonical ASCII formula word ends
with a delimiter and assigns one value at each distant syntax point. A fixed
scope point for each declared variable has value \(1\) exactly when that variable
is free in any open hypothesis, and \(0\) otherwise. Generalization assigns
\(0\) at the same point. These values participate in actual overlap checking and
the exact domains; missing does not mean zero. The local context point on each
line is explicitly zero. The reader shows all actual scope and character values.

Fresh search discovers a four-line universal-modus-ponens derivation, arithmetic
\(\forall x\,S(x+0)=S(x)\) from addition by zero and successor congruence, and
\(\forall u\,\forall x\,(\mathrm{Inc}(x,u)\Rightarrow\mathrm{Point}(x))\)
from the sole one-sorted incidence typing axiom
\(\forall x\,\forall u\,(\mathrm{Inc}(x,u)\Rightarrow
(\mathrm{Point}(x)\land\mathrm{Line}(u)))\).
The arithmetic axioms are explicit inputs, not discovered facts. This geometry
example is a logical quantifier/typing consequence in a Hilbert-style symbolic
language, without a new existence, metric or full Euclidean theorem.

An ambient hypothesis \(S(y)\) permits generalizing \(x\) but not \(y\).
The one-slot \(P(x)\) to \(\forall x\,P(x)\) request fails at the actual
scope point. Capture-safe instantiation of
\(\forall x\,\exists y\,R(x,y)\) at \(y\) renames the bound variable;
the captured conclusion \(\exists y\,R(y,y)\) is rejected by the finite
grammar. Independently, the off-diagonal relation on two objects satisfies the
premise and falsifies that conclusion. Budget cutoffs remain unknown.

The freshly discovered universal-modus-ponens proof is promoted to a predicate
family. Predicates specialize capture-safely to arithmetic equalities or symbolic
incidence, with the original primitive proof and ambient scope guard preserved.
At seven arithmetic slots, GCTS states fall from \(2330\) to \(393\), while
primitive expansion grows from \(10\) to \(14\) commands. A six-slot family
proof has \(294\) states and \(13\) primitive commands. Incidence can use one
family cell with six primitive commands. At four fixed slots it instead repeats
that family four times, producing \(24\) commands. Filled fixed boundaries do
not establish minimum proof lengths. Families change the atomic inventory and
scheduling granularity; logical expansion is not a capacity-preserving geometric
cluster decomposition. All controls receive the same library.

| Case | Grammar seconds | GCTS search seconds / states | Chronological search seconds / states | Saturation search seconds |
| --- | --- | --- | --- | --- |
| Universal modus ponens | 0.000470 | 0.002705 / 35 | 0.004760 / 663 | 0.000033 |
| Open ambient variable | 0.000518 | 0.002500 / 30 | 0.003213 / 396 | 0.000032 |
| Arithmetic, seven primitive slots | 0.003216 | 0.410873 / 2330 | Unknown at 0.794830 / 30001 | 0.000354 |
| Incidence typing | 0.005891 | 0.035026 / 87 | 0.438784 / 7098 | 0.001155 |
| Arithmetic family, seven slots | 0.003755 | 0.075788 / 393 | Unknown at 0.826552 / 30001 | 0.000368 |
| Incidence family, one slot | 0.000623 | 0.000202 / 2 | 0.000009 / 2 | 0.000024 |
| Arithmetic family, six slots | 0.003354 | 0.049686 / 294 | 0.361814 / 12039 | 0.000362 |

These are single-run search times, excluding model binding, certificate assembly,
independent checking and native execution. Grammar construction is charged
separately; reader totals add it to each search. Saturation shares facts and has
no exact slot-count bound; its recovered primitive lengths are retained.
Whole search production costs \(3.429269\) seconds, with peak process RSS
\(30474240\) bytes across all lanes, not a per-lane memory comparison.
Saturation remains much faster. No distinctive GCTS advantage is established,
and this extension has no RL lane or learned redundant failure constraints.

The graph keeps complete factored domains and forward/reverse incidence.
Independent input-reference masks yield \(|X||Y|\) candidates, subtracting
\(|X\cap Y|\) only when two distinct required input formulas prohibit a repeated
reference; identical inputs allow it. Complete canonical iteration enumerates
all references. Actual scope values filter the factors. Global dead ends precede
forced moves, then generation precedes degree ties. Required points start at
generation zero; placements assign successor generations. Exact rollback copies
all ports, point state, scope values, domains and ordering. This specializes to
complete formula words, single-slot occupancy and identity transformations.

The independent audit reconstructs all twelve inventories using a separate
substitution implementation, explicitly enumerates all reference domains,
replays every terminal GCTS tree and factor frame, checks every positive point
certificate and control proof, and checks the entire source-to-primitive
compilation. An ordinary deduction compiler discharges every open hypothesis;
both existing host kernels replay all generated lines against the exact theory
and target. Generalization uses the conservative global open-hypothesis context.
The audit rejects \(86\) corruptions in \(2.295267\) seconds.

Four compiled certificates accept in the unchanged literal Wang machine:
arithmetic, incidence typing, the open ambient-variable sequent, and the
six-slot arithmetic family proof. All \(43\) register bands and exact literal
counts agree. The native reader binds \(42\) actual command fragments to their
input/output hypotheses, forbidden variables, prior facts, pending commands,
lemma inventory and target. The open case is an actual checked sequent
declaration followed by a root identity probe; its \(217\)-command discharged
theorem is separately host-checked, not claimed as a native execution.
Exact scan acceleration is used. Whole native production costs \(215.104221\)
seconds, including \(2.161264\) seconds of shared executable compilation.
The independent operational audit costs \(35.348257\) seconds and rejects
\(12\) altered input/theory/reference transports. The frozen palette fingerprint
remains `0db5a804c3051683c42e339278c0f02faa948d0815ee3d8a25be039a7b86c455`.

Twelve regressions cover independent inventories, all small mask products,
repeated inputs, scope-zero versus missing, capture, target independence,
partial-state complete incidence, scheduling, generations, exact rollback,
family expansion, discharged proofs, point certificates and cutoff scope.
The independent browser reader validates ten positive proof records, their
primitive/discharged proofs, actual points and all \(42\) native command
contexts. It rejects \(8723\) point-mark mutations, \(44\) source-formula
mutations, \(115\) primitive-command mutations, \(140\) native-context
mutations and three tautology/scope regressions. Visual checks exercise all
\(44\) source lines, \(30\) marking-layer views and four native views.

The direct character ports are problem-defining exact markings, not learned
attention weights or adjacent literal Wang squares. The fixed core is used for
checking compiled discoveries; search still operates in the bounded semantic
front end. Universal formal compiler/kernel soundness, arbitrary partial syntax
marks, fractional/shared support, changing scope contexts, induction and witness
search, adaptive geometric clusters, certified cross-request caching, learned
failure markings, useful RL, stronger comparisons and the original turtle/Penrose
objectives remain active.

```sh
python3 research/gcts-rl-renewal/run_quantified_receptors.py
python3 research/gcts-rl-renewal/audit_quantified_receptors.py
python3 research/gcts-rl-renewal/run_quantified_wang.py
python3 research/gcts-rl-renewal/audit_quantified_wang.py
python3 research/gcts-rl-renewal/export_quantified_receptors.py
python3 research/gcts-rl-renewal/validate_quantified_receptors.py
```

## Notebook 46: movable proof boundary and certified failure markings

[The region reader](../../docs/research/gcts-rl-renewal/movable-regions.html)
uses a finite region of \(B+1\) full-capacity cells with at most \(B\)
inferences. Point values impose \(\phi_0=1\) and \(\phi_{B+1}=0\).
An inference assigns its incoming/outgoing values \((1,1)\); an end cell
assigns \((1,0)\); padding assigns \((0,0)\). Exact agreement forces a
contiguous inference prefix, one end cell and a padding suffix. The end
binds the preceding formula to the requested conclusion. When that formula
is already the last hypothesis, a zero-inference control closes immediately.
Padding covers required points but supplies no mathematical inference.

The inventory and character/scope semantics are the unchanged bounded
quantified grammar from Notebook 45, plus end/padding placements. Eleven
experiments include eight discovered derivation records, two exhausted
scope/capture controls and one supplied-target control. The statements and
explicit arithmetic/incidence axioms are unchanged; no new theorem family
is claimed. The universal inference family is promoted from this run's
fresh primitive donor proof. Its incidence recipient uses one family cell,
an end and three padding cells, with six expanded primitive commands.
The former fixed four-proof-cell region repeated the family four times.
Candidate ordering tries padding first but guarantees no shortest proof.

The end/padding suffix is also exported as an exact aggregate: its occupancy
is the sum of its distinct base placements and its marking is their compatible
union. The footprint varies with the endpoint. Independent verification
checks every constituent and the complete aggregate. It is an inspectable
closure cluster; the search executes the complete base inventory and uses
no cluster shortcut. A capacity-preserving decomposition of semantic lemma
cells remains open.

The initial learned layer is empty. Every exhausted depth-two branch supplies
a fixed compatible pair and its complete remaining-region tree. A separate
explicit verifier establishes exhaustion with exactly those two placements
fixed in the original system. All fourteen resolved negative pairs are used.
Each pair receives one remote point: value \(0\) on its first placement,
\(1\) on its second, and missing on every other placement. Normal point
agreement removes the incompatible candidate through the complete graph.
There is no runtime failure-pair callback or clause scanner.

The marking is frozen before the marked run. Its context hash binds the
catalog, target, hypotheses, bound, exact initial values, capacity and identity
transformations. These are certified redundant constraints for that finite
positional system, without a complete corona catalog, prototype translation
symmetry or another-context transfer theorem. All positive marked tilings
are also independently accepted after erasing the learned points. Expanded
mathematical proofs are checked by both host kernels, independently of this
search layer. The failure history is needed to justify redundancy, not to
accept a positive mathematical proof.

| Case | Initial states | Marked states | Initial search seconds | Marked search seconds | Training and certification seconds |
| --- | --- | --- | --- | --- | --- |
| Universal inference | 52 | 31 | 0.004817 | 0.002637 | 0.009505 |
| Open ambient variable | 47 | 26 | 0.003868 | 0.002292 | 0.008935 |
| Arithmetic | 3228 | 2506 | 0.570804 | 0.463379 | 1.086905 |
| Incidence typing | 148 | 99 | 0.057582 | 0.040846 | 0.099033 |
| Incidence universal inference | 47 | 26 | 0.012117 | 0.002592 | 0.017173 |
| Arithmetic family | 414 | 414 | 0.080510 | 0.077512 | 0.080731 |
| Incidence family | 7 | 7 | 0.000784 | 0.000479 | 0.000840 |

Search times above exclude grammar construction. Training includes the initial
model/search, independent pair certification and marked-model encoding, but
excludes shared grammar construction. The reader adds common grammar cost to
lane figures and initial model binding to the baseline; marked encoding is
charged once in training. Add training to the marked lane for a first marked
solve. Shared independent inventory verification, control model creation,
positive certificate assembly and compilation/checking are outside lane figures
and included in complete production. No first-solve advantage follows.

Forward DFS uses the same catalog and marked point rules but grows proof
lines chronologically and stops at the goal; its positive layouts are
independently checked. It reaches the \(40001\)-state cutoff in arithmetic,
incidence typing and arithmetic-family tests. Those results are unknown.
Saturation shares facts and its recovered proofs are checked against the
same maximum inference bound. It remains much faster. There is no RL lane
or distinctive overall GCTS advantage. Timings are exploratory single runs.
Complete search production costs \(21.341038\) seconds, with whole-process
peak RSS \(57065472\) bytes across all lanes.

The independent audit reconstructs all eleven inventories and every terminal
initial/marked tree, explicitly enumerates reference products, expands all
actual positive factor frames, checks full tile data and generations, extracts
the failed-pair provenance from the initial trees, and independently replays
every complete exclusion certificate. It checks the exact sparse encoder,
all positive classical certificates, learned-mark erasure, closure aggregates,
whole source compilation and discharged theorems. It rejects \(127\)
altered records in \(11.282067\) seconds.

Four compiled requests match Notebook 45's arithmetic, incidence typing,
ambient-variable and six-slot arithmetic-family requests exactly. Fresh wire
serialization reconstructs the same complete machine input bytes and bootstrap.
The archived operational audit, unchanged sources, palette fingerprint and
all grammar/checkpoint/response hashes are verified before reuse. This reuses
the previously executed \(42\) command fragments, with no new native execution.
Exact-input verification costs \(1.300106\) seconds and rejects sixteen altered
requests or input frames. Changed-input response transport remains unproved.
The open case retains its checked sequent declaration and labeled root probe;
its longer discharged theorem is separately host-checked.

Nine regressions cover the explicit flow boundary, partial graph domains,
brute point legality, both incidence directions, rollback, scheduling,
generations, failed-pair marks, scope/capture, cluster sums, zero-line control,
budget scope and context isolation. The extracted JavaScript quantifier checker
is byte-for-byte unchanged. Reader validation checks eighteen positive lane
records and nine erased proofs, rejecting \(13578\) point mutations,
\(66\) source changes, \(54\) structural changes, \(150\) primitive changes
and \(18\) projection changes. Browser checks exercise all \(100\) tile views,
fourteen learned-pair diagrams and an expandable four-line family body.

Complete formula words, full-capacity unit support and identity transformations
remain the specialization. Arbitrary partial syntax, fractional/shared support,
dynamic scope, general geometric marking prototypes, adaptable lemma geometry,
cross-request transports, useful RL, stronger comparisons, universal formal
compiler/kernel soundness and the original turtle/Penrose objectives remain active.

```sh
python3 research/gcts-rl-renewal/run_movable_regions.py
python3 research/gcts-rl-renewal/audit_movable_regions.py
python3 research/gcts-rl-renewal/export_movable_regions.py
python3 research/gcts-rl-renewal/validate_movable_regions.py
```


## Notebook 47 — transporting a closed-prefix failure

The previous goal turn made concrete progress: Notebook 46 was published as
`fca09a224d288d470c0b274527653ee0e358aa6f`, and all eighteen deployed files were
verified against their exact hashes. Its authoritative publication record is
`.gcts-active/movable-regions-20261010/publication-result.json`. The broad goal
remains active.

This extension uses the unchanged Notebook 46 point engine. Five independently
replayed donor profiles contribute all fourteen resolved negative pairs. Every
pair contains a structural end or padding tile. Ten new requests enlarge the
bound by one (unchanged signature) or four (bijectively renamed signature).
The later searches are newly executed; old success paths are not replayed as
recipient discoveries. No source proof path or target failure marking is
supplied to the initially unlearned recipient lane.

For donor bound $B_0$, end at $j$ gives $e=j$ and padding at $j$ gives $e<j$.
Every accepted pair therefore forces $e\leq B_0$. A hypothetical recipient
completion at bound $B\geq B_0$ can be restricted to cells $0,\ldots,B_0$:
removed cells are padding and the cut still has continuation zero. Backwards
references remain inside the prefix. Inverting a checked signature bijection
preserves variables, scope, arities, axioms, hypotheses, complete formula/rule
catalogs and every inference. Whole syntax words are reserialized; word lengths
may change. The resulting donor completion contradicts the independently
exhausted donor-pair tree. This sufficient transfer argument is implemented by
`check_transported_markings.py`; it is not a universal compiler soundness theorem
formalized in the arithmetic kernel.

The checker reconstructs both complete inventories independently. It verifies
all rule-map entries, parameters and scope guards, the mapped target and open
hypotheses, initial context hashes, every closing bound, and donor certificate
identities. `certify_donor` freshly exhausts the archived donor trees before
checks are supplied to `verify` within the same audited process. Persistent
claims of an accepted label or a matching hash are insufficient on their own.
The separate auditor additionally exhausts every transported recipient pair
using explicit reference products, with no producer graph/model imports.

Observed state counts, initially unlearned to transported:

| Recipient | Initial states | Transported states | Fresh depth-two pairs |
| --- | ---: | ---: | ---: |
| Universal MP, larger bound | 53 | 32 | 1 |
| Universal MP, renamed | 56 | 35 | 0 |
| Ambient open variable, larger bound | 48 | 27 | 1 |
| Ambient open variable, renamed | 51 | 30 | 0 |
| Arithmetic, larger bound | 3229 | 2507 | 0 |
| Arithmetic, renamed | 3232 | 2510 | 0 |
| Incidence typing, larger bound | 149 | 100 | 0 |
| Incidence typing, renamed | 152 | 103 | 0 |
| Incidence universal inference, larger bound | 48 | 27 | 1 |
| Incidence universal inference, renamed | 51 | 30 | 0 |

Extra padding moves useful failures below depth two. Reuse supplies known
obstructions that this particular fresh sampling depth misses. Every resolved
fresh sample is also used; no holdout is reserved from either pair catalog.
This is a finite positional sampling study, not the complete geometric
one-corona learner required for prototype markings.

All thirty recipient point proofs pass after learned-value erasure. The reader
also checks a successful unsafe-transfer counterexample: two instantiation
seeds fail at bound two but succeed at bound four, with MP and generalization
found by the search. Because those seeds include no structural closing tile,
the transfer checker refuses to prune them in the larger region.

Warm transported costs include grammar construction, model binding, proposal
construction, independent transport checking and search. First reuse separately
pays fresh donor-pair replay. Cold reuse also includes original donor learning
and grammar costs, with one donor replay serving the two shown recipients.
Fresh costs include the initial solve, certification, encoding and second solve.
Positive tile construction, independent point checking, command compilation and
kernel checking are recorded separately and included in whole production.
Verification overhead exceeds the warm state-saving benefit in most of these
small single runs. Saturation remains substantially faster. There is no RL lane
and no distinctive overall GCTS speed advantage established by this extension.

Conformance scope: exact integer capacity twelve on unit cells; all required
points activated; full lazy reference factors and singleton reverse incidence;
global dead/forced checks before generation-first branching; explicit remote
values; root generation zero and successor one; immutable marking per search;
exact state/graph rollback. The engine's prior conformance tests are unchanged.
New tests compare transported remote domains to independent enumeration,
exercise actual positive prefix restriction, reject altered metadata/arity/
guards/contexts/targets/maps and unknown failure certificates, and verify the
no-closing-seed counterexample. Full recipient trees and positive capacities,
marking agreement, reference syntax and primitive compiler binding are audited.
Fractional/shared support, partial syntax, general geometric transport and
adaptive capacity-preserving semantic lemma macros remain outside this engine.

These cells are semantic point tiles, not literal Wang squares. Changed requests
are newly checked by the host kernels. No native response is transported to a
changed request, and no new native execution occurs here. Signature renaming
preserves theorem shape; it does not constitute a newly discovered mathematical
theorem family. Incidence geometry is still symbolic typing rather than metric
Euclidean existence. Dynamic scopes, witness/induction search, useful RL,
stronger comparisons, universal formal kernel/compiler soundness and the
original turtle/Penrose objectives remain active.

Reproduce from the repository root:

```sh
python3 research/gcts-rl-renewal/run_transported_markings.py
python3 research/gcts-rl-renewal/audit_transported_markings.py
python3 research/gcts-rl-renewal/export_transported_markings.py
python3 research/gcts-rl-renewal/validate_transported_markings.py
```

The standalone reader is `docs/research/gcts-rl-renewal/transported-markings.html`.
Its data, audit and validation are separate versioned artifacts. The projection
is reproduced byte-for-structure before validating all displayed point values,
source lines, primitive commands and transport hypotheses.

## Notebook 48: adaptive propositional clusters with original capacities

`adaptive_receptor_clusters.py` mines primitive MP fragments from fresh
complete GCTS searches. No supplied proof sequence or derived semantic rule is
used. A four-line donor produces families of two, three and four original cells;
a six-line donor uses the four-cell family and produces a six-cell level-two
family containing that actual child. Atom abstraction yields formula parameters.
The new family interface joins parameters to compound formulas and external
receptors that are supplied hypotheses or actually occupied earlier cells.
Increasing cell embeddings allow gaps. This is a capped hint inventory, never
a base-domain generator or pruning rule.

All original inference/end/padding placements and their complete factored
incidence remain in the frozen movable-region model. Clusters do not occupy a
single replacement cell. Their capacities sum over distinct constituents and
their markings are the compatible union. Execution is a copy transaction;
every constituent obeys global dead/forced checks and generation-first branch
selection. Unrelated forced moves may interleave. A later incompatible branch,
dead end or budget interruption returns the original state and graph exactly.
Every base fallback alternative remains, including after a failed macro.

The experiment performs fresh donor discovery, promotion, 24 on-policy RL
episodes from zero weights, and six evaluations with disjoint names/formulas.
This is weak structural holdout: most evaluation and training proofs are chains;
one longer case and compound substitutions extend that family. Features include
cluster size, target conclusion, progress, compactness and an explicit defer
action. Frozen evaluation weights only propose sequences. Rewards use verified
success minus normalized log placement work. They never establish pruning.

All 50 whole searches and 1991 explicit states pass the separate checker, which
imports neither producer graph masks nor matcher/transaction/controller.
All 135 actual random draws, feature vectors, gradients, returns and updates
replay independently. It verifies original capacities/marks, learned source
windows, actual hierarchy children, every constituent's scheduler decision,
full fallback exhaustion, exact base inventory and kernel request binding.
Ten mutated cluster/policy/search records reject. Five unit tests exercise all
tiny certificate-set equivalence, remote compound supports, gapped scheduler
interruptions, exact rollback, unknown budget semantics and base fallback.

| Evaluation | Base attempts | Fixed clusters | Zero policy | Trained RL |
| --- | ---: | ---: | ---: | ---: |
| Longer held-out chain | 373 | 146 | 373 | 403 |
| Compound formula receptors | 22 | 20 | 22 | 21 |
| Distracting implications | 37 | 26 | 37 | 39 |
| Short compound chain | 9 | 9 | 9 | 9 |
| Region too small | 3 | 3 | 3 | 3 |
| Missing link | 4 | 4 | 4 | 4 |

All four positive fixed-proposal totals exceed base totals in this single run.
For the longer chain the totals are approximately 36 versus 97 milliseconds,
even before shared donor discovery and audit are charged. Trained RL mostly
worsens search; zero-weight deterministic policy defers every time and reveals
proposal-enumeration overhead. Saturation uses fresh grammar/model construction
and logical checking; when its proof fits, exact region assembly and host-kernel
checking are charged too. In the too-small region, saturation finds a longer
proof and is explicitly not a matched bounded-outcome solver. No distinctive
GCTS/RL speed advantage is established by these chain-shaped examples.

The reader checks 18 point certificates (two donors plus sixteen evaluations),
six accepted cluster expansions and 128 original occupied cells. It shows
all selected scalar character/context/continuation values, primitive formulas,
English reference lines, external bindings, child offsets and scheduler traces.
The sparse plot is actual point data; cell cards are semantic capacity summaries,
not literal Wang tile types. Every compiled sequent binds supplied hypotheses
as named premise axioms. There is no expanded implication-discharge certificate:
during development the existing repeated-discharge adapter grew the six-line
seven-hypothesis example to 232,778,007 request bytes and hit its byte limit.
That aborted probe is outside the final measured run. Compact checked assumption
handling remains an implementation gap.

Conformance scope is unchanged exact integer twelfths on full positional cells,
complete formula ports and root generation zero/successor one, with remote
mark-only dependencies and copy rollback. New tests specifically validate the
adaptive aggregate and scheduler transaction. Fractional shared support,
unrestricted family discovery, dynamic scopes, quantified cluster adaptation,
learned redundant failures, direct literal-palette search and new native Wang
executions are not implemented here. The broader research goal remains active.

Reproduce from the repository root:

```sh
python3 research/gcts-rl-renewal/run_adaptive_clusters.py
python3 research/gcts-rl-renewal/audit_adaptive_clusters.py
python3 research/gcts-rl-renewal/export_adaptive_clusters.py
python3 research/gcts-rl-renewal/validate_adaptive_clusters.py
```

The standalone visual reader is `docs/research/gcts-rl-renewal/adaptive-clusters.html`.
The full raw experiment retains every training and evaluation trace. The reader
projection omits repeated trees; validation reproduces it exactly from the
independently audited raw data and checks all displayed point/cluster values.

## Notebook 49: compactly discharge searched contexts

The new `compact_contexts.py` adapter lifts a discovered sequent under one
balanced conjunction, using only existing primitive kernel commands. It
discharges every hypothesis, preserves the original theory, installs no premise
axioms or trusted rule, and universally closes the conditional statement.
Fresh complete point searches include a shared-dependency propositional proof,
an actual conditional successor/addition fact, symbolic incidence typing, a
valid quantified context, an invalid eigenvariable control and an empty source
derivation. Three non-chain windows are mined; both compound transfer proposals
are scheduler-rejected with complete fallback. This is a limitation, not an
acceleration claim. No new RL training is included.

Reproduce the independent binding checks and unchanged-core native execution:

```sh
python3 research/gcts-rl-renewal/run_compact_contexts.py
python3 research/gcts-rl-renewal/audit_compact_contexts.py
python3 research/gcts-rl-renewal/run_context_wang.py
python3 research/gcts-rl-renewal/audit_context_wang.py
python3 research/gcts-rl-renewal/export_compact_contexts.py
python3 research/gcts-rl-renewal/validate_compact_contexts.py
```

The native producer runs a fresh 14-command branched theorem and an invalid
projection in the frozen common Wang palette. The full literal execution and
every independently derived operational fragment agree, with explicit empty
root context. Native production takes several minutes; the compressed grammar
and full context audit remain downloadable. The visual reader is
`docs/research/gcts-rl-renewal/compact-contexts.html`. Source discovery, deterministic
discharge and literal computation are displayed as distinct stages. Command
compression is not a proof-search speed claim or a universal compiler proof.

## Notebook 50: retain a family through unrelated scheduler decisions

The new `resumable_clusters.py` controller places one original candidate per
transition. A branch-local family changes preferences at the selected point,
waits while other cells are chosen, and resumes when a remaining member becomes
eligible. Missing constituents contribute no occupancy or markings. Failed
children restore the parent state, complete graph and active hint. Every original
alternative remains. An unfinished family is never promoted as a checked lemma.

Two fresh donors create seven formula families, with actual completed child
provenance in two level-two windows. Twenty-four fresh sampled episodes train
five softmax weights from zero using a declared work proxy. Nine held-out cases
compare base, fixed resumable, zero-policy, trained resumable and atomic search;
the two fixed controls share the same scoring rule and proposal cap. Chronological
DFS uses a separate entered-node budget and schedule. Saturation is not proof-length
bounded; its four-line proof for a two-line region is labeled as exceeding that
region. Positive classical proofs that fit are bound to exact original tilings
and receive the same discharged primitive checks.

Independent replay reconstructs all 71 search records, 23,825 explicit states,
complete declared proposal pools and scan counts, pending sets, hint phases,
fallback alternatives, source children, 67 sampled actions and all updates.
Thirteen operational corruptions reject. Five tests check every tiny exact
solution, exact parent rollback, interrupted families, bounded negatives, unknown
partial trees and corrupt aggregates. The reader replays every positive path,
original point value, completion and hierarchy; Node checks every primitive
certificate with additional point, formula, context and lifetime mutations.
Classical negative and unknown search traces are not independently replayed.

Reproduce from the repository root:

```sh
python3 research/gcts-rl-renewal/run_resumable_clusters.py
python3 research/gcts-rl-renewal/audit_resumable_clusters.py
python3 research/gcts-rl-renewal/export_resumable_clusters.py
python3 research/gcts-rl-renewal/validate_resumable_clusters.py
```

The visual reader is `docs/research/gcts-rl-renewal/resumable-clusters.html`.
Its source lines are in logical order; the separate timeline is the actual
placement order, including end tiles and forced placements. Dashed cells are
pending family members. Colored sparse point diagrams show the selected original
tile only. Square cell cards are semantic capacity summaries, not literal Wang
types. The shared primitive logic, compact discharge and native palette are
unchanged; this experiment adds no new native execution or failure marking.

Four propositional cases reduce attempts; the longer proof goes from 76 base
attempts and 63 atomic attempts to 21 for each resumable controller. Fixed
resumable total costs are slower than base on all six positive cases; RL matches
fixed attempts and demonstrates no additional benefit. Saturation is faster on
every positive. Arithmetic and incidence use no learned family. This is limited
evidence for scheduler-compatible family reuse, not a useful speed advantage
over general proof search. The positional, full-capacity, generation-zero root
adaptation and broader turtle/Penrose/universal-proof-system gaps remain active.

## Notebook 51: exact lazy indexes for the same family join

`indexed_family_join.py` indexes only demanded syntax nodes, available formula
receptors, original aggregate values and deterministic ordering digests. Caches
belong to one immutable model/library snapshot and are empty at every solve.
`indexed_family_search.py` preserves the complete base graph, retained hint
semantics and every original fallback. Its fixed-controller tree and entire
ordered proposal pool equal full enumeration exactly. The engine remains the
positional full-capacity adaptation; no new marking or native Wang execution is
introduced. Dynamic marking changes and general cache invalidation are outside
this immutable-solve experiment.

Fresh donors rebuild seven patterns at two hierarchy levels. Twenty-four fresh
sampled episodes retain the earlier semantic-scan reward proxy; this is not
actual CPU or wall time. Eleven evaluation goals include a longer eight-line
propositional proof and a compound-formula case with irrelevant implications.
Five point lanes run eight independent cold solves each, cycling the observation
order. Total costs include grammar/model construction, all index construction,
search/joins and positive point/source/discharged-kernel checking. Raw trace
serialization and whole independent audit are separate. Classical controls are
fresh single observations with their own schedule/budget limitations.

All 81 retained searches, 27,724 explicit states, 52 actual index records and
30,437 queries pass independent full enumeration. It derives every demanded
syntax table, every query in tree order, all cache counters and immutable
bindings. Thirteen existing corruptions and nine new index/cache corruptions
reject. The five new tests compare all tiny solutions, graph domains and pools,
exact parent rollback, compound receptors, changed snapshots, bounded negatives
and unknown partial trees. Every repeated solve is producer-checked and must
match its retained primary semantic digest. Only primary complete traces are
independently replayed; repeat summaries and digest bindings are checked.

Reproduce from the repository root:

```sh
python3 research/gcts-rl-renewal/run_indexed_families.py
python3 research/gcts-rl-renewal/audit_indexed_families.py
python3 research/gcts-rl-renewal/export_indexed_families.py
python3 research/gcts-rl-renewal/validate_indexed_families.py
```

The reader is `docs/research/gcts-rl-renewal/indexed-families.html`. Compressed raw
data preserve full primary trees, index tables/queries and all cold observations.
The exact reader projection includes both the entry review and any replacement
hint at a step, preserving expire-and-replace lifetimes in the larger examples.
It renders proof formulas/English, actual selected tile values, demanded lookups
and all forty timing dots for the selected goal.

Indexing reduces some enumeration overhead while increasing cold costs on other
cases. Family reuse reduces the larger proof from 759 to 129 attempts. Fixed
and RL choose identical families and placements, with equal non-time metrics on
every evaluation. The differing, overlapping bimodal timing samples cannot be
credited to RL. Saturation's single times are below all positive point-lane
medians. This is limited evidence about representation cost and exact family
matching, not a general speed advantage. The full research objective remains active.

## Notebook 52: quantified families with capture-avoiding contexts

Fresh statement-only donors produce mixed windows of universal instantiation,
modus ponens and generalization. The miner reconstructs unary formula contexts,
typed term/function parameters and exact guard variables. Bound-variable names
use binder distances inside proposal matching. Free variables retain their
identities, and inserting a term into a context preserves its free occurrences.
Actual ground rules, serialized formula words and scope points are unchanged.
The conservative ambient scope test prohibits generalization over a variable
free in any supplied hypothesis. The capture-sensitive case explicitly renames
an inner binder during instantiation, then generalizes the remaining free
variable. A captured replacement and an open-scope generalization both reject.

Three fresh searched donors yield 31 families. One six-cell parent strictly
contains an actual completed five-cell child from the compound donor, providing
two hierarchy levels without counting a same-size copy as a larger family.
Pending members still assign no occupancy or markings. The original global
dead-end/forced/earliest-generation scheduler and complete fallback remain in
force, with exact parent rollback. Lazy indexes belong to an immutable
model/library snapshot. This experiment adds no learned pruning, failure marking
or native Wang-machine execution; the earlier literal palette remains frozen.

Sixteen fresh sampled episodes start at zero weights and use the declared work
proxy, not CPU time. Eleven evaluation statements run four matched point lanes
and four independent cold observations each, rotating their order. All 176
solves include fresh grammar/model construction, empty caches, matching and
positive point/source/kernel checks, with identical placement/time limits.
All repeats must match the retained primary semantic digest. Classical controls
are fresh single observations with separate schedules and budget semantics.

The independent implementation reconstructs all 63 retained searches, 120,133
states and 1,274,240 matching queries. It imports neither the producer's miner
nor its matcher, index or graph factors. Source windows, typed binding tables,
ordered proposal pools, scope, full original alternatives, cache counters,
on-policy draws and all updates pass. Fifteen deliberate corruptions reject.
Five tests compare all tiny branch domains and exact parent rollback, complete
enumeration against indexed pools/trees, source abstractions, scope, snapshot
changes and unknown partial trees. Both primitive kernels check all 35 positive
reader certificates. Node checks also corrupt point values, each source line,
contexts, index data, hint lifetimes, timing summaries and strict containment.

Reproduce from the repository root:

```sh
python3 research/gcts-rl-renewal/run_quantifier_families.py
python3 research/gcts-rl-renewal/audit_quantifier_families.py
python3 research/gcts-rl-renewal/export_quantifier_families.py
python3 research/gcts-rl-renewal/validate_quantifier_families.py
```

The full producer took about 126.56 seconds, excluding independent replay; the
independent audit took about 487.82 seconds. The 311,172,934-byte raw JSON is
stored as a deterministic 6,134,564-byte gzip. The reader projection retains
positive-leaf hints, distinct actual queries with occurrence counts, all cold
observations and original source/certificate data. Full failed branches, pools,
policy events and ordered queries remain in the raw archive. Only primary full
trees are independently replayed; full repeat and classical negative/unknown
traces are not. Wall clocks are measured observations.

The reader is `docs/research/gcts-rl-renewal/quantifier-families.html`. It shows
source formulas and English for every line, concrete formula-context receptor
bindings, colored original point assignments, the strict child/parent hierarchy
and all 16 timing dots for the selected goal. Existing arithmetic and incidence
statements remain separate conditional symbolic controls, with no new arithmetic
axioms or full Hilbert-geometry development.

Fixed families reduce the eight-inference chain from 29,084 to 12,085 attempts;
cold medians are about 3.52 and 3.19 seconds. The compound chain goes from 358 to
104 attempts and about 100 to 93 milliseconds. Fixed guidance increases total
cost on every other positive case. The trained policy defers on every evaluation,
matches base placements and attempts, and pays proposal construction costs; it
is slower on every positive case. Saturation's single observations are faster
than every positive point-lane median. This is evidence for first-order family
reuse and a strict larger structure, with no demonstrated RL advantage or
general proof-search speed advantage. Avoiding proposal costs before a policy
defers is a possible next experiment, not an implemented result.

Conformance remains a positional, full-capacity, integer-twelfths adaptation,
with identity transformations, generation-zero root obligations and
generation-one original placements. Mining accepts supported windows with
nullary/unary donor predicates; a unary context may itself contain higher-arity
predicates, functions, equality and nested quantifiers. The finite grammar and
conservative scope rule do not make this a complete first-order prover.
Fractional capacity, unrestricted transformations, general quantified family
discovery, useful RL acceleration and the original turtle/Penrose plane-tiling
objectives remain open. The full research goal remains active.


The October 10 propositional attention clarification adds an inspectable view of
Notebook 42's existing searched identity proof. Its last modus-ponens tile has
remote premise markings and positive occupancy only at its own cell. Changing
the antecedent reference shows the actual character or internal function
conflict. The browser pins the unchanged discovery artifact and reconstructs
all five primitive rules, original point tiles and the requested boundary.
This view runs no new proof search and trains no attention model. A learned
policy can propose premise connections, while declared inference rules and
exact point agreement enforce validity. Arbitrary reach still needs a
parameterized family or explicit routing in a fixed local inventory.

```sh
node research/gcts-rl-renewal/test_propositional_attention.cjs
python3 research/gcts-rl-renewal/validate_propositional_attention.py
```

The live explanation is at
[the distant inference view](https://liuyao12.github.io/geometric-tree-search/docs/research/gcts-rl-renewal/propositional-receptors.html?v=20261010-pa1#attention-panel).


Notebook 53 moves the request/defer decision before family matching. Eight
features come directly from the complete original graph. A request enables the
unchanged fixed member selector; no request can prune a base alternative or
bypass global dead/forced propagation. A zero gate constructs no family index,
and an always-on gate reproduces the earlier fixed controller's full trees.

Three fresh donor searches produce 31 quantified families at two levels.
Sixty-four sampled zero-start episodes use observed inclusive cold-solve time
with a declared averaged score-gradient update. Eleven evaluation goals have
five lanes and four rotating cold observations each: 220 solves. The trained
gate defers everywhere, misses the two useful fixed-family cases, and has no
demonstrated advantage over a zero gate. Comparing zero gate with eager zero
isolates matching overhead on the same original placement trees. Saturation's
single observations remain faster on every positive point case.

The independent audit reconstructs 122 primary searches, 159464 original
domain states, 818170 matching queries, 11822 request decisions and 1276 sampled
draws; 15 corruptions reject. It checks all gate features/actions/gradients,
conditional exact joins, original alternatives, hierarchy, scope and recorded
clock/update algebra. Eleven complete trained-gate trees equal base after gate
metadata is erased. Repeated timing summaries are digest-bound to primary
traces; full repeat trees and clocks are not independently reproduced.

The compact reader preserves positive-leaf decisions, original tiles, hints,
complete demanded syntax tables, distinct queries with multiplicities, all
numeric training events, and each cold observation. It independently counts
original candidate domains before each displayed request. Both primitive
kernels accept its 43 positive certificates, including duplicate lane proofs.
No new literal Wang execution, learned failure marking or general speed claim
is added. The wider program and useful conditional RL remain active.

```sh
python3 research/gcts-rl-renewal/run_proposal_gate.py
python3 research/gcts-rl-renewal/audit_proposal_gate.py
python3 research/gcts-rl-renewal/export_proposal_gate.py
python3 research/gcts-rl-renewal/validate_proposal_gate.py
```

Read [the request-gate notebook](https://liuyao12.github.io/geometric-tree-search/docs/research/gcts-rl-renewal/proposal-gate.html?v=20261010-pg1#reader).
