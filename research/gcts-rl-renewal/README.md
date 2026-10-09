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
