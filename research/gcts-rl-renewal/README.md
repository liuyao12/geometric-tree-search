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

The complete current research suite passes 76 tests, including 13 new complex
and full-star checks. Earlier snapshots retain their milestone test counts.
