# GCTS master reference: point values, frontier search, and plug-ins

This is the normative algorithm contract for current and future subprojects.
The conceptual reference is the Turtle demo in [GCTS-I.html](../GCTS-I.html).
Its shared growth engine uses global dead/forced checks, chronological point
age, adjacency preference within the oldest group, and randomized point-based
branching. The Hat/Turtle demo explicitly adds its shared-boundary-segment
specialization. Historical experiment records retain their original scheduling
and are not automatically conforming to this updated contract.

## 1. The mathematical object is values at points

Choose a discrete point domain L, allowed transformations G, and tile types.
Each tile is a finitely supported function t: L → [0, 1]. A placement c is a
tile type and an allowed transform, with t_c(p) = t(g⁻¹p). A nontrivial tile
has positive support. The base search uses these point values exclusively.
Lines, edges, polygons, faces, volumes, and intersections are not base objects
or additional legality tests. They may help author or draw the point data.
Faithfulness to a conventional geometric tile is a separate question; it
must not be silently assumed or enforced by the point-value solver.

A marking is a point-value assignment m on an explicitly declared domain,
possibly with several channels and a domain larger than the tile's positive
t-support. Marked values must agree wherever their domains overlap. Missing
means unconstrained; an explicitly assigned zero is a value, not missing.
For vector markings, declare how transformations act on values as well as
points, including channel permutations and sign changes.

For placements S, define T(p) = Σ[c in S] t_c(p). A legal partial state has
T(p) ≤ 1 everywhere and agreement of all active m-values. An exact tiling has
T(p) = 1 at every required point, with the same marking agreement. Markings
do not add like t-values. Mark-only points still constrain candidates even
when they are absent from the frontier.

Coordinates, t-values, and matching comparisons must have specified exact
semantics. Use integer units where available (Turtle uses capacity 12),
rationals, or an appropriate exact algebraic representation. Floating-point
tolerance alone is not an exact certificate; an approximate implementation
must identify itself and independently certify any claimed exact result.

The model declares tile inventory, allowed reflections/orientations, placement
identity and multiplicity. By default each transformed placement is selected
at most once, as in the article's sets K_i. Deduplicate only when all relevant
t-data, m-data, inventory identity, and transformation behavior are preserved.

## 2. Frontier points and complete candidate incidence

Maintain an explicit set Q of active required points. The frontier is
F = {p in Q : T(p) < 1}, including points with T(p) = 0 and interior pockets.

- For a finite target, activate every required point, including untouched
  points. Describe exterior conditions using point data and admissible
  placements. A partial-capacity boundary may be expressed by a fixed exterior
  contribution so the total target remains 1.
- For unbounded growth, activate seed obligations and newly exposed positive
  t-support. State how untouched zero-valued points are subsequently activated,
  for example by exhausting successively larger finite point sets. This must
  be fair if claiming coverage of the whole domain. An empty local frontier
  is not a certificate that the infinite domain is tiled.

The bookkeeping for every placement decision is a bipartite graph:

- A point node for each frontier obligation.
- One shared candidate node for each distinct currently legal placement
  touching the frontier.
- An edge (p, c) exactly when t_c(p) > 0. Store its contribution as well as
  the identities; it need not fill the entire deficit in one placement.

Enumerate every allowed tile orientation and every positive-support alignment
at each new frontier point. The candidate universe must be complete before
degree zero or one can mean dead or forced. Sampling, a top-k shortlist,
one-edge attachment, and an RL proposal list cannot supply this guarantee.
Lazy enumeration is acceptable only if exhaustion and singleton claims are
certified. Keep candidate dependencies on all t- and m-support, including
points outside Q. A candidate illegal anywhere is unavailable everywhere.

## 3. Decision order and chronological point ages

The reference order is the same with or without markings.

1. Check the entire active frontier for degree zero. Any such point kills
   the branch, including a distant point or one introduced late.
2. If any point has degree one, place its sole candidate and update the graph.
   Repeat the global dead/forced checks until no forced move remains. A shared
   forced candidate is placed once.
3. Collect the frontier points introduced at the earliest placement step and
   pool their distinct legal incident placements. Count a placement once even
   when several points are adjacent to it.
4. Within that age group, prefer placements neighboring the last placement.
   In the point model, neighboring means that their positive point supports
   intersect. Draw uniformly among adjacent moves when there are any, otherwise
   draw uniformly from the full priority pool.
5. Fix an incident frontier point of the selected move. The siblings at this
   node are all legal placements incident to that point. Keep the first move
   first and try the other siblings in randomized order. The adjacency
   preference orders choices and does not delete legal sibling alternatives.
6. After a placement or rollback, run the global dead/forced checks again.
   Backtracking restores the fixed point and remaining siblings of its parent.

Point age is the chronological step when a point first entered the current
board. All seed obligations and fixed finite-target obligations start at step
zero. A new point introduced by the next placement gets that placement step.
Existing points keep their age. Undo the age when its introducing placement
rolls back. Geometric generations remain available for corona display and
checkpoint statistics.

The implementation is `assets/gcts-point-branching.js`. Its input consists of
point records, introduction ages, legal placements, a random source, and an
optional adjacency predicate. It contains no geometric edge representation.
The A2 engine uses this policy by default. An explicitly selected historical
ranking remains an experimental control.

### Polygon specialization in the Hat/Turtle demo

The demo explicitly sets `requireEdgeSharing: true`. Its graph keeps an
incidence only when the candidate shares a positive-length exposed boundary
segment incident to the frontier point. Subdivide sides at lattice points, so
a partial shared side qualifies. Within the oldest group, neighboring moves
share a boundary segment with the last tile.

Draw the first move from that priority pool, fix one shared exposed segment,
and retain only placements covering that same segment as sibling alternatives.
This uses the known polygon geometry of the demo. The general point-value
algorithm fixes a point instead.

Before reporting a finite exact solution, verify the entire target and
markings. A growth milestone must first rule out known dead points. Budget
exhaustion, cancellation, or a learner restart means unknown. A finite pause
during propagation is a checkpoint.

## 4. Incremental updates and exact rollback

Maintain forward and reverse incidence and dependency indexes for changed
t-values and m-values. A placement updates affected candidates at all their
incident points, removes completed obligations, and introduces complete
domains for new obligations. Keep unaffected domains. Extended marking
support can cause distant changes; a display viewport or a tile bounding box
alone is not a valid dependency limit.

Trail placements, point totals, marking assignments/reference counts,
generations, inventory, candidate validity, incidences, newly created nodes,
and branch-local exclusions. Undo every delta. A failed child is excluded only
in its justified parent context; it is not globally forbidden. Global learned
rules carry versions and scope. If rules change, revalidate the accepted prefix
and graph, and invalidate stale caches/trails or replay from a valid state.
A monotone local update is insufficient when a rule is weakened or removed.

The graph is the source of decision domains. Renderers and policy features
consume it; they do not maintain a second, divergent notion of legality.

## 5. GCTS plug-ins primarily eliminate candidates through markings

The main acceleration path is to construct useful m-values whose agreement
removes candidates, creating more forced moves and fewer genuine branches.
The same base engine runs with no additional marking, fixed markings,
learned markings, or combinations of compatible channels.

Each plug-in declares its point domains, value transformations, affected
dependencies, version, persistence/rollback behavior, and reason for rejection.
Constraint filters feed candidate removal back into the graph; they cannot
bypass the scheduler. Additional sound constraints, such as a residual
capacity impossibility certificate, may supplement marking elimination.

Keep three meanings distinct:

- **Problem-defining marking:** part of the requested tiling problem. Search
  is exact for that marked problem; the solution set may differ from the
  unmarked problem.
- **Proved redundant constraint:** justified by the original problem and its
  stated context. It may prune while preserving the claimed solution set.
- **Learned hypothesis:** supported by samples but not proved necessary.
  It may guide ordering or run as an explicitly restricted marked experiment.
  Failure under that hypothesis does not prove the original problem impossible.

An exhausted local search justifies only what its complete candidate universe,
boundary context, inventory, and marking version establish. Passing positive
examples or replaying a prefix is useful validation, not proof that a learned
rule preserves all solutions. Generalized or symmetry-transferred exclusions
must carry the assumptions needed for that transfer.

## 6. GCTS marking learning: the live local-constraint loop

The learning demonstration in `GCTS-I.html` is the reference workflow for the
GCTS lane, including both versions of the 3D tiler. This is constraint synthesis
from local extension tests, not prediction of unseen labels. Do not reserve a
holdout from the enumerated catalog: use every resolved sample as a constraint
or classification check. Independent replay tests implementation correctness;
it is not a train/test split.

1. **Declare the system.** Fix the tile inventory, lattice or sublattice,
   allowed transformations, component action, and finite marking support.
   A learned marking belongs to this tile-and-lattice system. A change of domain
   needs its own validation. Never seed the learner with a known marking,
   catalog tiling witness, or bundled learned assignments.
2. **Collect neighboring pairs.** Enumerate all distinct capacity-legal ways
   a second tile can meet a rooted tile. Symmetry representatives are allowed
   only with a verified action and complete orbit coverage. Report pairs as
   pairs; their validity is not known at enumeration time.
3. **Label by unmarked search.** Keep both tiles fixed and attempt to complete
   their one-corona: every point in the pair's positive t-support must reach
   capacity. At success, every exposed frontier point must still have at least
   one legal candidate. Use the complete point/candidate graph and reference
   scheduler. A witnessed completion with viable frontier is positive; an
   exhausted complete search is negative. Time, node, depth, cancellation or
   memory limits mean unresolved, never negative. A positive one-corona is not
   a certificate of arbitrarily large or infinite extension.
4. **Update after each result.** Keep the current equality/constraint state
   and update the provisional marking as each new label arrives. Positive
   samples require agreement at every overlap where both components are
   assigned. A **directly** rejected negative needs at least one overlap where
   both are assigned and disagree. This is one rejection mechanism, not a
   requirement for every negative: agreement of the two fixed tiles may still
   eliminate frontier candidates and reveal a dead point, immediately or after
   further search. State whether synthesis targets direct pair conflicts or
   operational rejection through the frontier graph. Negatives supply inequality
   alternatives, not positive equalities. An incremental equality encoder may
   test negatives and choose its support; a SAT solver may solve the combined alternatives.
   State which method is actually used. Unresolved samples impose neither
   positive nor negative constraints.
5. **Allow individual free values.** Each component may be `*`, meaning absent
   and compatible with every value. Zero remains an assigned value. Interior,
   boundary and exterior points are all eligible. When a value becomes free, remove
   its incident positive equality edges before solving again; deleting its
   assignment after merging classes leaves spurious equality paths. There is no requirement to
   retain interior points: exterior markings on neighboring tiles can overlap
   and disagree. Sparsification is secondary to passing positives and retaining
   the required negative exclusions; describe its validation scope and any
   symmetry constraints. Do not interpret a greedy exterior-only result as a
   theorem that interior assignments can never help.
6. **Show the real learning.** Display the current corona attempt, its outcome,
   the evolving point values and individual `*` entries, resolved/unresolved
   counts, and actual classification scores. Provisional values may change;
   they must not filter the unmarked search that supplies their own labels.
   Make collected pairs inspectable with their oracle label, current marking
   decision, agreeing/conflicting overlap values, and any positive corona
   witness. Distinguish the unmarked witness from the learned pair decision.
   Include the number of active points and assigned component values, stating
   whether counts cover prototypes or all represented orientations.
   Tiling views must inspect the active placed marking section, including
   overlapping assignment counts; their displayed values must follow rollback
   and must not come from an unrelated known or selected saved marking.
7. **Validate, then activate.** Replay every labeled pair with the completed
   marking. The current demo gate requires the complete catalog, no unresolved
   labels, acceptance of every positive, and rejection of more than half the
   negatives (or all positives when there are no negatives). Report the actual
   score; this threshold is not perfect classification. Only then save a named,
   timestamped browser-local model and start the marked tiler automatically.
   Keep separate runs and their tile/lattice provenance. Do not put learned
   markings into the source tree. Cold benchmark lanes may save their results
   for inspection but must not silently reuse earlier runs. Explicit browser-library
   reuse must recheck system identity, complete catalog coverage, positive corona
   witnesses and marking scores; report replay cost separately from original
   training. Saved negative labels keep their original proof scope.
8. **Use markings as markings.** The tiler compares assigned point components
   through its normal global section and candidate dependency graph. Do not
   substitute a runtime pair classifier, failure-clause scanner, or lookahead
   for learned m-values while labeling that behavior GCTS learning. Freeze a
   validated marking before a new marked search; if it changes during a search,
   revalidate/replay the entire prefix and graph as required in section 4.

Pair classification and subsequent tiling growth are distinct checks. A marking
can fit every labeled pair yet block all larger patches, including through
mark-only contacts absent from the catalog. Its exclusions remain a **learned
restriction** unless separately proved redundant. Failure of the marked search
must not become an unmarked non-tiling claim. Retain the unmarked baseline,
report learning and verification costs, and record actual marked-growth results.
Known markings are comparison controls, not an implicit learning target.

Independent marking components may use different free-value supports. Each must
satisfy every positive overlap constraint; a negative is rejected when at least one
component has an assigned disagreement. Rebuild and revalidate every component when
new labels arrive. Declare the component transformation action and synthesis budget;
combining bounded scalar searches is not a completeness or minimum-rank proof.
Count distinct spatial points separately from assigned component values.

Explicit continuation may retain resolved labels for the same tile/lattice and
support. Recheck identity, catalogue membership and positive witnesses; rebuild
constraints from the labels. Retry unresolved checks with declared budgets,
keeping them unknown until resolved. Report cumulative training cost separately
from the latest attempt. A continuation is not a cold comparison run.

### 6.1 Extending an existing marking through corona consensus

Given a known marking, enumerate all compatible k-coronas around a rooted tile,
glue their placed marking sections, and intersect those partial sections. Assign
a component only when every corona assigns the same value there; a missing value
in any corona leaves it free. Transport the resulting common section with the
original marking's symmetry action. Complete enumeration makes these assignments
necessary for globally extendable tilings of the original **marked** model.
It does not prove that the original marking is redundant for unmarked tilings.
An unfinished enumeration yields only a hypothesis and must not be promoted.

A finite corona may fail when every boundary tile is decorated with the new
extension: that requires those boundary tiles to admit their own neighborhoods.
Separate root-consensus verification, whole-patch marking agreement, and full
frontier viability. Support reduction may preserve all pairwise conflicts, but
must include mark-only contacts, not just positive t-support neighbors. Compare
the same base search and ranking, report derivation separately from reuse, and
measure total costs rather than assuming that a stronger marking is faster.
See [the Hat/Turtle corona-consensus experiment](projects/a2-corona-consensus.md)
for complete 2- and 3-corona enumerations, bounded benchmarks and limits.

### 6.2 Alternating learned markings and complete coronas

A staged experiment may start from a complete unmarked rooted one-corona
catalogue, learn several alternative markings, then apply section 6.1 at
successive radii. This rooted catalogue differs from section 6's pair-centered
oracle: a positive attachment occurs in at least one rooted corona; absence is
negative only after complete enumeration. Declare which criterion supplies labels.

Fit agreement throughout every original positive corona, including overlaps
between its boundary tiles. Declare a finite prototype marking domain; one
option restricts it to points covered by every original corona. Search over
individual free components, rebuilding equalities after each support change.
Distinct alternatives must differ in compatibility, not merely label names.
A bounded collection of such alternatives is not the complete marking space.

For each alternative independently, enumerate compatible one-coronas, intersect
their sections, then use that extension to enumerate two-coronas, and so on.
Promote only completed nonempty intersections. A stage with no new common
values is a plateau at that radius, not non-tiling evidence. Exhaustive emptiness
rules out that marked system; a cutoff is unknown. All extensions preserve only
their initial learned restriction, whose global soundness remains unproved.

Keep alternatives separate. A branch may maintain the subset of markings
compatible with its entire patch; it cannot choose a different unrelated marking
at each tile. Benchmark initial and extended markings with the same search and
ranking, retain the unmarked control, and charge catalogue collection, fitting,
retries, verification and reduction separately from reuse. See the
[staged Hat/Turtle experiment](projects/a2-corona-workflow.md).

### 6.3 Online marking probes while collecting pair labels

An explicitly selected online experiment may use the current provisional
marking to seek the next pair's corona before its unmarked oracle call. Start
with empty support. A successful marked completion is a positive only after
independent unmarked core/frontier replay. A rejected fixed pair, exhausted
marked search or marked timeout is not an unmarked negative: retry without the
marking. Only an exhausted unmarked search supplies a negative; unresolved
calls remain unknown. Do not silently skip unexamined pairs using a hypothesis.

After each resolved label, solve assigned/free component constraints using
only the observed prefix. Every positive pair must agree. Requiring an assigned
disagreement for every negative defines a **strict direct pair classifier**;
it is not a necessary condition for a useful GCTS marking. A negative can instead
be rejected by a dead frontier or exhausted marked extension search. Record
direct conflict, immediate dead frontier, subsequent exhaustion, success, and
budget-unknown separately. Declare whether the solver is SAT/SMT or a bounded
heuristic and state the support and value action.
Recheck every accepted synthesis against its observed constraints. If the
constraint system is unsatisfiable or times out, disable that marking instead
of treating it as a tiling impossibility proof. A new pair search starts with
a fresh graph under the new version; a continuing search must replay its prefix.

Perfect pair classification is insufficient to guarantee any larger marked
tiling. Conversely, preserving every first-found positive corona as a hard
agreement constraint can conflict with directly excluding negative pairs: a finite
corona may contain a boundary pair that has no corona of its own. Such a witness
must be replaceable; a positive pair does not certify every completion around
it. Distinguish alternative completions from alternative markings, and keep
their hypotheses separate from original unmarked proofs.

When a known working marking exists, test it as an independent control against
the proposed training objective and support before interpreting a failed
learning run. Check representability, symmetry action, all positive pairs and
their marked completions, and both direct and frontier-mediated negative
rejection. Do not feed its assignments or measured rejection count into the
learner as targets. The Turtle extent-1 control directly rejects 193 of 206
negative pairs; the other 13 fail via its frontier search. Requiring 206 direct
conflicts excludes this control, although all 41 positive pairs have marked
completions. A positive completion is an existential choice: two first-found
unmarked witnesses disagree with the control, while alternative completions
work. See the [known-control audit](projects/a2-online-control.md).

Compare complete cold collection time, including synthesis, replay, failed
probes and fallback calls, with the same unmarked baseline and pair order.
Checkpoint tiling benchmarks must state the exact observed prefix and cannot
claim end-to-end savings while excluding its acquisition cost. The
[headless online-pair experiment](projects/a2-online-pairs.md) records both
failure modes and the absence of a speedup for its strict direct-conflict
configuration. Its exclusion of the known Turtle solution prevents using that
result as evidence against operational online GCTS learning.

### 6a. Certified negative-only alternative

A separately labeled certified-exclusion experiment may activate a partial set
of proved local impossibilities without positive witnesses or a fully resolved
pair catalogue. Every marking disagreement must imply a certified excluded
configuration, including all allowed transforms, pair reversals, and mark-only
contacts. Unknown or untested configurations must remain unrestricted. State
and verify the point-group action on marking components and values. Re-prove
saved negatives before reuse; do not trust persisted labels as certificates.

This alternative does not relax the learned-restriction gate in section 6.
It preserves infinite exact tilings of the stated point model, but may remove
finite patches that cannot extend. Preserve that distinction in checkpoint and
benchmark reporting. With no certified exclusions, report an unmarked fallback.
See [the implementation and conformance report](projects/3d-certified-exclusion-markings.md).

## 7. RL proposes clusters

The primary RL role is proposing, composing, and selecting clusters: finite
collections of base placements with relative transforms and optional markings.
Periodic and isohedral constructions are useful initial proposal generators.
They are not restrictions on the hypothesis space. Allow irregular clusters,
mixed orientations/types, and hierarchical composition without presupposing a
known tiling strategy, substitution, or repeated unit cell.

Every cluster has an inspectable expansion to base placements. Validate its
internal t-sums, marking agreement, inventory, and interface with the current
state using the same point rules. Its aggregate t is the sum over its distinct
constituents; its aggregate m is their compatible union. Overlapping cluster
descriptions must identify shared placements so they are not counted twice.

A proposal supplies base candidates or continuation preferences after global
propagation and chronological point-age selection. Its absence is not a proof that
a base candidate is impossible. Retain base-placement fallback for completeness.
If executing a cluster as a macro, process constituent placements through the
same scheduler and propagation, with a reversible transaction. Any shortcut
needs an equivalence argument; never turn a sampled cluster pool into the
degree counts used to declare a base move forced.

Useful learning signals include verified growth, reduced branching and
backtracking, useful candidate eliminations, and proposal/validation cost.
Reward base placements or satisfied obligations, not the number of macros.
Export a learned cluster library with transforms, expansions, marking versions,
training provenance, and held-out evaluation. A promising cluster is not yet
an infinite-tiling or substitution certificate.

## 8. Verification and comparison contract

For each engine, test the following before claiming conformance:

- Incremental domains equal independent exhaustive re-enumeration, including
  zero-valued required points, pockets, and extended marking-only interactions.
- Global dead ends outrank all forced moves; forced moves outrank all branches;
  earlier point introduction outranks a later point of smaller non-singleton degree;
  adjacency only breaks age ties, and siblings retain the same branching point.
- Fractional residuals and candidates shared by several points behave correctly.
- Failed branches and cluster transactions restore complete state exactly;
  rule changes cannot revive stale graph data or retain unjustified exclusions.
- Tiny instances agree with an independent exhaustive point-value verifier.
  Symmetries preserve the full decorated model, including reflection channels.

Compare baseline, GCTS, and RL on the same point model, seed/target, complete
base candidate universe, scheduler, budget, and solution semantics. Declare
any added marking that restricts the problem. Report attempts, accepted base
placements, forced placements, genuine branch decisions, backtracks, candidate
eliminations by reason, graph sizes, wall time, and memory. Include learning,
cluster construction, validation, and cache warmup costs; distinguish cold and
reused runs and separate training examples from evaluation examples.
Fewer branches, more forced moves, and higher elimination counts are
intermediate outcomes, not speedup certificates. Judge acceleration by the
total cost of reaching the same verified result, including the plug-in's cost.

Result labels must distinguish finite exact tiling, consistent finite patch,
certified infinite construction, exhausted finite search, restricted-model
failure, and unknown. Store enough point data, placements, marking rules,
configuration, and versions for independent replay and verification.

## 9. Current implementation audit and migration

The November 18, 2026 update shares the point selector across the A2, J,
frontier-graph, 3D growth, 3D corona, and finite-window point engines. It adds
chronological point ages and preserves fixed-point siblings. The Hat/Turtle
demo explicitly retains the segment specialization. The earlier audit below
records remaining model and verification gaps.

Source inspection on 2026-09-08 established the following limited status;
it is not a completed repository-wide runtime audit.

| Implementation | Observed alignment and remaining work |
| --- | --- |
| Turtle demo / `assets/a2-tiling-engine.js`, growth mode | The shared engine defaults to chronological point ages, adjacency within the oldest group, and fixed-point siblings. The demo explicitly enables segment incidence and fixed-segment siblings. Integer twelfths represent occupancy, with tolerances in comparisons. Finite checkpoints do not certify infinite extension. |
| A2 finite-boundary mode in the same engine | All target obligations start at age zero and use the common point selector with global dead/forced checks. Polygon containment and overlap remain part of this adapter, so a pure point-defined boundary model remains separate work. |
| `assets/tiling-frontier-graph.js` / `assets/penrose-point-search.js` | The default shares chronological ages, adjacency preference, and fixed-point siblings with the base selector. Explicit generation-first/degree-first settings remain historical controls. Penrose still adds geometric/contact predicates in its adapter and is a specialized geometric experiment. |
| `apps/3d-lattice-tiler/lattice-search.js` | Has a point-value search path and candidate cache; its point births use placement order. Audit generation semantics, global propagation, complete incidence, and marking updates. |
| `apps/3d-lattice-tiler/engine.js` and other geometric engines | Geometry, strategy shortcuts, and forced-move throttling need auditing. A geometric or specialized control can remain useful, but is not automatically the shared point-value baseline. |
| 3D seed-growth comparison, `apps/3d-lattice-tiler/growth-search.js` | Both live versions share chronological point ages, global dead/forced checks, adjacency preference, and fixed-point siblings through the common selector. Marks eliminate candidates through the same graph. RL rollout ranking remains an explicit experimental mode. Whole-frontier replay verifies finite checkpoints. Earlier timing and prefix-comparison records describe their original algorithms. See [historical growth evidence](projects/3d-reference-growth-audit.md). |
| 3D finite-window point engine, `apps/3d-lattice-tiler/v2/search.js` | Complete finite-target incidence uses the common point selector with every target obligation at age zero, global propagation, fixed-point siblings, and exact rollback/replay. The fixed-window target differs from unbounded seeded growth. Historical timing records retain their original scheduling. |
| 3D shared pair-corona learner, `apps/3d-lattice-tiler/corona-graph.js` | Complete dynamic point incidence uses the common selector and chronological point births. Both fixed seed placements introduce age-zero points. Exact integer weights, independent corona/frontier replay, and reversible candidate caches retain their existing proof scopes. Finite pair labels supply learned restrictions. |
| 3D center-and-corner polycube research model, `apps/3d-lattice-tiler/voxel-point-model.js` | Explicit center constraints make capacity legality equivalent to voxel nonoverlap for cubic rotations and integer physical translations. The fourteen research catalogue entries in v2 use this model, with independent voxel replay for positive coronas and final results; v1 retains its legacy model. See [live catalogue scope](projects/3d-research-catalogue.md). Shared learning/search and independent voxel replay are tested; no unrestricted geometric alignment or infinite-tiling claim. See [geometric audit and oracle experiments](projects/3d-voxel-marking-research.md). |
| Finite point-corona PB/SAT research control, `scripts/solve_point_pair_corona.py` | Same unmarked point sums and viable-frontier existence question, with a proved finite seed-support reduction, validated binary voxel encoding and optional exact occupancy-frontier conditions, added singly or in explicit batches. Pair symmetries carry explicit transports and all positive members are replayed. Uses different scheduling, not the reference graph lane. Trusted-solver UNSAT rather than an exported proof. See [local-label refinement](projects/3d-point-corona-sat.md). |
| 3D finite voxel-window SAT control, `scripts/solve_voxel_point_window.py` | Validated center/corner-to-voxel reduction, full finite placement universe, scalar point marking agreement; 72 exhaustive small comparisons. Separate SAT scheduling, no frontier viability requirement beyond the finite target. Learned UNSAT remains restricted. See [larger-window controls](projects/3d-point-corona-sat.md#larger-growth-and-period-proposals-after-complete-pair-learning). |
| Incremental voxel pair-corona SAT control, `scripts/solve_voxel_pair_corona.py` | Same finite unmarked corona and full viable-frontier question, with retained Glucose or CaDiCaL clauses and cached voxel overlap masks including outside-pool candidates. Optional sequential nonoverlap constraints and reversible phase hints are separately identified controls. Positive witnesses and dead frontiers replay in the independent point verifier. Unknown budgets remain unresolved. Separate SAT scheduling; see [oracle report](projects/3d-point-corona-sat.md#incremental-voxel-sat-oracle). |
| Finite voxel-window viable-frontier control, `scripts/solve_voxel_frontier_window.py` | Requires the full finite point target and a legal candidate at every exposed point, including candidates outside the placement pool. Independently replayed in weighted-point and voxel models. Verified patches propose new pair tests, never inferred labels; the incomplete p10 catalogue remains unaccepted. Separate SAT scheduling. See [frontier-window and pair-proof report](projects/3d-viable-frontier-search.md). |
| Complete periodic-quotient research control, `scripts/solve_patch_period_quotients.py` | Patches propose period lattices; each check contains every proper orientation and quotient translation, excludes self-overlap, and retains distinct placement identities. Optional relative-pair clauses require an independently replayed RUP certificate. Separate SAT scheduling, with global translation symmetry but no fixed root orientation. Positive certificates replay through an independent JS quotient verifier; UNSAT covers only the selected period lattice and relies on the SAT solver. See [sampled-period controls](projects/3d-viable-frontier-search.md#complete-periodic-quotient-controls). |
| p9-48258 voxel CNF proof control, `scripts/certify_voxel_obstruction.py` | Independently regenerated voxel formulas; all five UNSAT traces checked by Python RUP and DRAT-trim. Exact symmetry expansion plus an infinite-to-finite projection excludes integer-grid tiling for this catalogue shape. Separate SAT scheduling; no unrestricted Euclidean alignment or aperiodicity claim. See [certificate and scope](projects/p9-48258-grid-obstruction.md). |
| Historical RL runners and other subprojects | Candidate-ranking policies and known-strategy experiments are useful controls. Audit individually; they do not establish implementation of unrestricted cluster proposal learning. |

For each current or future subproject, record: point domain and arithmetic;
t/m data and transformations; target/activation rule; complete candidate
generator; generation convention; scheduler and rollback; enabled plug-ins
and their proof scope; independent verifier; conformance tests; remaining gaps.
Non-tiling applications must state their reduction to this model or label their
different constraint–candidate formulation as an adaptation. Do not silently
redefine exact tiling to cover a packing, optimization, or approximate model.

New work should use this contract from the start. Revisions to existing engines
should close and test the relevant gaps before changing their status to
conforming. Historical benchmarks retain their original algorithm descriptions.
