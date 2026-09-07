# Basic tiling algorithm

This is the required baseline for new or revised tiling tree searches in this
project. GCTS markings, learned failure constraints and RL policies are layers
above it. They do not replace its point–candidate bookkeeping, forced moves,
contradiction detection or rollback. Existing engines must be audited before
being described as conforming. Non-tiling search problems may adapt the same
constraint–candidate structure, with their completeness conditions stated.

## State and complete candidate incidence

For a partial tiling, maintain the exact accumulated weight T(p). Every point
with 0 < T(p) < 1 is an unfinished obligation. This includes interior pockets,
not only points on a chosen outer boundary. The tiling representation must
state its finite support and its geometric admissibility predicates.

Maintain a bipartite graph:

- A point node for every unfinished obligation.
- A candidate node for each distinct legal transformed tile placement.
- An incidence whenever the candidate contributes positive t at that point.

A candidate may touch several unfinished points. It is one shared node, not
independent copies in their option lists. Enumerate every supported prototile
orientation and every support-point alignment at a newly exposed point. Do not
substitute candidates from one selected edge for the complete point domain.
Symmetry-equivalent placements can be deduplicated, preserving decorations.

Legal means that adding the tile respects all exact base constraints, including
T <= 1 and polygon non-overlap where applicable, plus the currently enabled
matching constraints. An incidence need not fill the entire remaining weight
in one placement. If the only candidate leaves the point unfinished with no
remaining candidates, propagation correctly discovers a contradiction.

## Propagate before branching

1. Check all unfinished points. A degree-zero point immediately kills the
   current branch, regardless of its distance or generation.
2. If any point has degree one, its sole candidate is forced. Place that tile,
   update the graph, and repeat from step 1. Shared forced candidates are placed
   once, updating every incident point.
3. Once there are no forced points, branch at a minimum-degree unfinished point.
   Generation, distance or a policy may break ties and order its candidates.
4. After a placement, return to propagation before making another branch
   decision. Restore both tiling and graph exactly when undoing a placement.

A pause or finite observation milestone may suspend propagation, retaining the
entire stack and graph. It must not present a state with a known dead point as
an attained milestone. A finite corona is not a proof of infinite extension.

## Incremental updates and undo

Keep forward point-to-candidate and reverse candidate-to-point incidence.
Index candidate dependencies on changed t support, geometry and marking
support, including marking extensions outside the tile. A placement invalidates
affected legal candidates at every incident point; newly unfinished points
introduce their complete candidate domains. Distant unaffected domains are
retained. Conservative spatial bounds may accelerate dependency lookup but
must never omit a possible interaction.

Trail candidate validity, graph incidences, point metadata and newly introduced
nodes along with placement weights and generations. Undo the complete delta
in reverse order. Do not rebuild every point domain at each decision, and do
not leave stale learned exclusions after rollback. If a constraint can become
weaker, change globally, or cease to be monotone under placement, its adapter
must explicitly revalidate or rebuild the affected graph.

## GCTS and RL layers

Markings add compatibility constraints to the candidate legality predicate.
Their full support belongs in dependency bookkeeping; drawing samples do not
define the support. Learned constraints require sound justification for hard
pruning. Any learning update must revalidate the active graph and prefix.

RL may rank legal candidates and eligible branch points after propagation,
using graph features. It cannot make an illegal candidate available, suppress
a required candidate without a sound constraint, skip a forced move, ignore a
dead point or corrupt rollback. Plain, GCTS and RL comparisons must share the
same base algorithm and candidate universe, and report forced placements,
branch decisions and constraint-check costs separately.

## Current Penrose implementation

`assets/tiling-frontier-graph.js` provides the shared graph bookkeeping.
`assets/penrose-point-search.js` supplies Penrose geometry, exact vertex weights
in units of 1/10, fixed decorated placements, matching predicates and DFS.
Both live P3 modes and every P1/P2/mixed selection use it. The independent P3
arrow predicate remains the unmarked rule; Ammann mode checks full extended
marking supports without calling that predicate. Intermediate displayed dots
are inspection samples, not additional unfinished t obligations.

The Penrose representation uses Z[zeta_5] vertices and forbids partial edge
contacts. Point contacts and unfinished pockets remain admissible intermediate
states and are represented by their unfinished vertices. Polygon overlap and
marking compatibility are checked continuously with exact field predicates.
A historical edge-first rhomb engine is retained only as an explicitly named
regression baseline, not as the live algorithm.

Verification must compare incremental domains with exhaustive fresh
re-enumeration, exercise actual forced chains and failed branches, check exact
rollback, and check global dead-point priority. A small example that grows
successfully is insufficient to establish bookkeeping correctness.
