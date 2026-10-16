# GCTS master reference: point values, frontier search, and plug-ins

This is the normative algorithm contract for current and future subprojects.
The conceptual reference is the Turtle demo in [GCTS-I.html](../GCTS-I.html).
Its shared A₂ growth engine supplies the reference decision order: global
dead ends, global forced moves, then earliest generation. Existing programs
and historical experiment notes are not automatically conforming; the audit
below records known gaps. This contract supersedes older descriptions that
put minimum candidate count before generation or geometry inside the base.

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

## 3. Decision order and generations

The order is mandatory:

1. Check the entire active frontier for degree zero. Any such point kills
   the branch, including a distant or late-generation point.
2. Otherwise, if any point has degree one, place its sole candidate and update
   the graph. Repeat from step 1 until no forced move remains. A shared forced
   candidate is placed only once. If it leaves an unfillable residual deficit,
   the next iteration detects the dead end.
3. Otherwise choose a point in the earliest frontier generation. Candidate
   count, distance, a deterministic key, or a policy may break ties within
   that generation. A later point with two options does not outrank an earlier
   point with ten. Choose among its legal incident candidates and recurse.
4. On failure, restore the complete state and try the remaining alternatives.
   After every change, return to global dead/forced checks before branching.

Use the Turtle growth convention for generations: seed tiles and explicitly
activated root obligations have generation 0. A newly placed tile gets one
plus the minimum existing point generation on its positive t-support; a new
disconnected root, when the target requires one, starts at 0. A point's
generation is the minimum generation of its currently incident placed tiles
and any explicit root obligation. Save and restore this metadata on rollback.
It is a growth layer, not the chronological placement index, distance, or
current graph degree. Declared scheduling variants belong in separate
experiments and cannot be labeled the reference baseline.

Before reporting a finite exact solution, verify the entire target and
markings. A growth milestone may pause a run with its stack intact, but must
first rule out known dead points; it does not establish infinite extension.
Budget exhaustion, cancellation, or a learner restart means unknown, not
untileable. Forced propagation can itself continue indefinitely on an infinite
domain; a finite pause is a checkpoint, not a new branch decision.

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
   assigned. A rejected negative needs at least one overlap where both are
   assigned and disagree. Negatives supply inequality alternatives, not
   positive equalities. An incremental equality encoder may test negatives
   and choose its support; a SAT solver may solve the combined alternatives.
   State which method is actually used. Unresolved samples impose neither
   positive nor negative constraints.
5. **Allow individual free values.** Each component may be `*`, meaning absent
   and compatible with every value. Zero remains an assigned value. Interior,
   boundary and exterior points are all eligible. There is no requirement to
   retain interior points: exterior markings on neighboring tiles can overlap
   and disagree. Sparsification is secondary to passing positives and retaining
   the required negative exclusions; describe its validation scope and any
   symmetry constraints. Do not interpret a greedy exterior-only result as a
   theorem that interior assignments can never help.
6. **Show the real learning.** Display the current corona attempt, its outcome,
   the evolving point values and individual `*` entries, resolved/unresolved
   counts, and actual classification scores. Provisional values may change;
   they must not filter the unmarked search that supplies their own labels.
   Include the number of active points and assigned component values, stating
   whether counts cover prototypes or all represented orientations.
7. **Validate, then activate.** Replay every labeled pair with the completed
   marking. The current demo gate requires the complete catalog, no unresolved
   labels, acceptance of every positive, and rejection of more than half the
   negatives (or all positives when there are no negatives). Report the actual
   score; this threshold is not perfect classification. Only then save a named,
   timestamped browser-local model and start the marked tiler automatically.
   Keep separate runs and their tile/lattice provenance. Do not put learned
   markings into the source tree. Cold benchmark lanes may save their results
   for inspection but must not silently reuse earlier runs.
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
propagation and earliest-generation selection. Its absence is not a proof that
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
  earlier generation outranks a later point of smaller non-singleton degree.
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

Source inspection on 2026-09-08 establishes the following limited status;
it is not a completed repository-wide runtime audit.

| Implementation | Observed alignment and remaining work |
| --- | --- |
| Turtle article / `assets/a2-tiling-engine.js`, growth mode | Uses shared point–candidate incidence, global dead/forced checks, then generation-first ordering. Integer twelfths represent occupancy, although comparisons use tolerances. Audit target-stop checks, untouched-point activation, and exactness claims against this contract. |
| A₂ finite-boundary mode in the same engine | Uses a separate target traversal and polygon containment/overlap checks. Needs conversion to point-defined boundary data and the same global graph scheduler before claiming full conformance. |
| `assets/tiling-frontier-graph.js` / `assets/penrose-point-search.js` | Shared incidence and reversible updates exist, but the graph currently ranks degree before generation; Penrose also uses polygon/contact predicates and continuous marking support. These require an explicit point-model implementation or a separately labeled geometric experiment. |
| `apps/3d-lattice-tiler/lattice-search.js` | Has a point-value search path and candidate cache; its point births use placement order. Audit generation semantics, global propagation, complete incidence, and marking updates. |
| `apps/3d-lattice-tiler/engine.js` and other geometric engines | Geometry, strategy shortcuts, and forced-move throttling need auditing. A geometric or specialized control can remain useful, but is not automatically the shared point-value baseline. |
| 3D shared pair-corona learner, `apps/3d-lattice-tiler/corona-graph.js` | Complete dynamic point/candidate incidence, global dead/forced checks, earliest-generation branching, exact integer weights and rollback; positive witnesses independently replayed with viable frontier. Finite pair labels supply learned restrictions. See [both-version learning report](projects/3d-gcts-marking-learning.md); v1 geometric growth gaps remain separate. |
| 3D center-and-corner polycube research model, `apps/3d-lattice-tiler/voxel-point-model.js` | Explicit center constraints make capacity legality equivalent to voxel nonoverlap for cubic rotations and integer physical translations. Shared learning/search and independent voxel replay are tested; no unrestricted geometric alignment or infinite-tiling claim. See [geometric audit and oracle experiments](projects/3d-voxel-marking-research.md). |
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
