# Printable tiling animation: search contract

The page uses a frozen copy of the project's shared `assets/a2-tiling-engine.js`
and its failure-memo dependency, copied on 2026-10-16. The engine is unchanged;
`model.js` declares this demonstration and `worker.js` adapts its events. This
snapshot isolates the printable preview from unrelated engine experiments.

## Model and scope

The point domain is the full integer plane $x+y+z=0$. Occupancy uses integer
units with capacity $12$, representing $t$ in twelfths. Canonical vertex weights
are the Turtle game's angle weights, with $12$ at interior points. The shared
orientation authoring routine rounds lattice angles to integer twelfths; tests
independently check the canonical corner weights.

The marking is the game's three signed stripe components, extended three
lattice steps beyond each segment. Missing components remain unconstrained.
This does **not** introduce the additional zero assignments of the article's
`FixedA2Marking`. Reflections permute channels and reverse their signs; rotations
permute channels. Physical flips correspond to reflection in the plane plus
reversal of the tile's vertical axis, so the rigid CAD transform is proper.

The live modes are Turtle only, one protected Trefoil filled by Turtles, and
mixed Turtles/Trefoils. A fixed seed has generation zero. In the one-Trefoil mode,
additional Trefoils are excluded by the declared inventory filter. There is no
board containment test, polygon-overlap filter, witness preference, substitution,
RL proposal, or learned marking in this search. The board is illustrative.

## Frontier and rollback

`maximize`, `completePointGrowth`, and `rescanAfterBacktrack` are enabled. The
shared engine exhaustively aligns every positive-support anchor with exposed
frontier points and maintains shared candidate incidence and marking dependency
indexes. Global dead points precede forced moves; branching uses the earliest
generation before candidate-count ties. Failed branches restore the graph,
point totals, marking references, and generations, then rescan globally.

Activation follows newly exposed positive support. This demonstration does not
fairly activate all untouched points of the infinite plane and makes no infinite
tiling claim. A 128-tile checkpoint is reported only after the engine's global
dead-point scan. The node budget is 20,000; budget exhaustion is unknown.

## Animation and controls

In the three growth modes, only actual solver placement and backtrack events move tiles. A worker retains
the DFS stack behind acknowledged event batches; Pause freezes the displayed
motion and withholds the next acknowledgement. Step finishes exactly one tile
arrival/removal. Restart and sample changes terminate the old worker; late events
from it are ignored. The camera and settled tile transforms are preserved while
arrivals descend vertically and removals fly upward. Connectors are drawn from
coincident stripe endpoints; this drawing routine never decides search legality.

## Verification

Run `node tests/test_printable_live_tiling.mjs` from the repository root:

- All three live modes reach a 16-tile checkpoint with full frontier-domain audits.
- Every emitted state is independently replayed for integer capacity and signed
  marking agreement, without using the engine's mutable marking/contact state.
- Mixed mode, seed 1, produces two genuine backtracks; each removes exactly the
  last accepted placement and preserves its prefix. Cancellation remains unknown.
- CAD transforms match projected canonical vertices for every orientation and
  preserve the correct face orientation.

Browser checks cover Step, Run/Pause, stable paused state, sample switching,
view rotation/zoom, and the static gallery. A separate 32-tile live display
snapshot was checked for polygon intersections and had none; this is a finite
rendering check, not a new legality filter or a physical fitting certificate.
Nominal clearances, board fit of arbitrary live patches, print tolerance and
snap retention are not certified by the point search.

## Paired move mode

`flip-worker.js` grows a fresh 48-tile one-Trefoil patch with the same point
engine, then explores its local rearrangement graph in `flips.js`. This is a
separate, specialized rearrangement demonstration, not a frontier scheduler or
a pruning rule. The three growth modes remain unchanged. No static sample
placements or preselected move sequence are loaded.

Each move applies a single lattice reflection or half-turn to one edge-adjacent
Trefoil/Turtle pair. It must preserve the complete subdivided outline and exact
integer point totals, and every resulting assigned marking must agree throughout
the current patch. All other tiles stay fixed. Breadth-first exploration is
bounded to 300 expanded states; the animation follows a longest discovered
shortest path without repeated states. This is a finite-patch experiment, not a
claim of an infinite trefoil walk or the longest possible path. Restart grows a
new random seed. The displayed lifting path is illustrative, not a physical
collision certificate for reliefs/connectors or board fit.

`tests/test_printable_pair_moves.mjs` independently reconstructs all occupancy
and marking assignments from prototypes at every move, verifies the unchanged
exterior and aggregate occupancy, and checks the rigid 3D animation endpoint
against the exact resulting CAD pose. Seed 10 gives eight distinct moves in a
component of 18 states, including reflections and half-turns.
