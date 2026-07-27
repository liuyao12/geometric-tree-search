# Learning Local Filters for GCTS

## Core Idea

Turn local GCTS failures into a compatibility filter.

Instead of trying to hand-design a perfect marking, build a dataset of local
placements, label them by exhaustive local search, train a marking or filter
from those labels, and use that filter during global GCTS.

This works especially well for lattice tiling problems where local
configurations can be enumerated exactly.

## Workflow

1. Fix a finite marking model.

   Choose:

   - tile type or tile types
   - lattice support around each tile
   - number of channels
   - symmetry group action
   - value alphabet, for example `{*, -1, 0, 1}`

   Here `*` is a wildcard and matches anything. `0` is an ordinary value.

2. Enumerate local placements.

   Start with one tile and enumerate all legal neighboring tile placements.

3. Run exhaustive local completion.

   For each local pair, try to complete a fixed local neighborhood, such as the
   1-corona around the pair.

   Label the pair as:

   - `positive`: local completion succeeds
   - `negative`: exhaustive local search fails
   - `inconclusive`: search hits a time, node, or tile cap

   Only exhaustive failures should become negative labels.

4. Convert labels into constraints.

   Positive samples give tentative equalities:

   ```text
   overlapping mark values should agree
   ```

   Negative samples give disequality clauses:

   ```text
   on this overlap, at least one mark value must differ
   ```

   These are not numeric inequalities like `<` or `>`.

5. Solve or train the marking.

   Assign values to marking variables while satisfying:

   - positive equalities
   - negative disequality clauses
   - symmetry action
   - wildcard behavior

6. Validate.

   Replay positive patches and check that the learned marking still accepts
   them.

7. Use the marking as a filter, not as the main heuristic.

   During GCTS:

   - choose frontier points geometrically
   - order candidates geometrically
   - reject candidates that fail the learned marking

   This prevents the marking from accidentally steering the search into a bad
   branch just because it creates many mark overlaps.

8. Benchmark by growth curve.

   Compare first-hit time and decision count for corona layers:

   - unmarked GCTS
   - learned marking filter
   - exact local oracle filter
   - marking plus residual exceptions, if needed

## Key Diagnostic

Always compare:

```text
unmarked GCTS
learned marking filter
exact local oracle filter
```

If the exact oracle beats unmarked but the learned marking does not, then the
data is good but the marking representation is too weak.

If neither beats unmarked, the local labels or the local search radius are
probably not informative enough.

## Residual Exception Hybrid

Sometimes the compact marking captures most of the oracle but misses a small
set of proven-negative local configurations.

Then use:

```text
candidate accepted iff
  geometric placement is valid
  and marking is compatible
  and candidate is not in the residual proven-negative table
```

This keeps most of the structure in the learned marking while explicitly
recording the few local obstructions the marking cannot express.

In the Hat experiment, the exact pair-corona oracle beat unmarked GCTS
decisively. The rank-3 marking captured most of that signal but left 17
proven-negative pair placements compatible. Adding those 17 residual pair
exceptions recovered the oracle growth curve.

## General GCTS Recipe

For a new lattice tiling or GCTS problem:

1. Identify a finite local obstruction radius.
2. Enumerate all local configurations at that radius.
3. Exhaustively label them as positive, negative, or inconclusive.
4. Train a compact equivariant compatibility structure.
5. Use it as a filter during global search.
6. Compare growth curves against unfiltered GCTS.
7. If the compact filter is lossy, either enlarge the marking model or keep a
   small residual exception table.
