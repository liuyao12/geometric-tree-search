# Turtle training illustration

The final Geometric Deep Learning section of GCTS-I contains an independent
Turtle training/tiling illustration. The added point-domain discussion and square
widget were removed. The original floating Turtle demo keeps its controls and
scroll stages. This widget does not alter its state or engine.

## What is trained

This is supervised fitting of the known Turtle point data, not discovery of its
matching rules from unlabeled patches. The status explicitly says that it fits
known Turtle data. There are 36 unique anchors, combining positive t-support and
rank-3 marking-only sites from `FixedTurtleMarking(1)`. All anchor x/y coordinates,
positive-support t-values and assigned m-components start perturbed. The third
coordinate is -x-y. Missing marking components remain missing; zero is assigned.

Gradient descent minimizes squared error to the example values, with an update
of 0.09 times the residual for 120 steps. The example includes the known support
and matching rule. A low loss is not an exactness certificate. Before tiling,
coordinates are rounded to A₂ integers, t-values to integer twelfths, m-values
to integers. The compiler checks residuals, collisions, complete known marking
agreement and that the fitted t-data reproduce the original Turtle. The frozen
support is passed directly to `SparseA2Marking`; there is no silent substitution
of a `FixedTurtleMarking` in the search.

## Search contract and limitations

- The unchanged shared A₂ engine searches Turtle placements with all 12
  orientations, complete positive-support alignments, forward/reverse candidate
  incidence, global dead/forced checks and earliest-generation branching.
- The seed is the identity Turtle at the origin. Newly exposed positive support
  activates obligations. This is a growth experiment; untouched points of the
  whole infinite lattice are not fairly activated.
- Fitted rank-3 m-values use channel permutations and parity sign changes under
  the same symmetry action as the original demo. Mark-only and zero-valued
  dependencies are included. `SparseA2Marking` supplies rollback reference counts
  and the shared graph handles candidate invalidations.
- The marking is the known marked Turtle problem reconstructed by a supervised
  fit; no new redundant-rule theorem or learned-pruning proof is asserted.
- The shared engine retains its historical floating comparison tolerances,
  generation/rollback implementation and growth-stop limitations. No broad new
  conformance or infinite-extension claim is made.
- A separate verifier reconstructs integer t-sums from frozen anchors and allowed
  placement transforms, checks capacity, duplicate placements, and every assigned
  m-overlap, independently of the solver's point totals and candidate cache.
  Open frontier points are reported, not claimed to have t-total 1.
- A 48-tile checkpoint is labeled a consistent finite Turtle patch. Budget
  exhaustion is unknown. No continuous-support exactness or infinite-tiling
  certificate is claimed. The preexisting growth limit may precede a full global
  dead-point scan; local consistency does not imply extendability.
- Training/search run separately and search runs in a worker. Reset terminates
  the worker; pause waits between search decisions. JSON export contains the
  supervised model, frozen points/marking, transforms, verification and statistics.
  Elapsed search time includes animation and pauses, so it is not a speed benchmark.

## Validation

`node tests/test_turtle_point_learning.mjs` checks three training seeds, movement
of coordinates and t-values, lattice-plane preservation, exact agreement of the
frozen marking with the example, and rejection of untrained/corrupted/colliding
models. An actual 12-tile search runs with the shared engine's exhaustive frontier
graph audit enabled, then passes the independent integer point verifier. Duplicate
placements and nonintegral transforms are rejected. The browser runs the full
48-tile illustration, tests pause/reset and the original Turtle controls, and
checks desktop/mobile layout and JSON replay. These are limited conformance
checks; they do not establish general continuous-anchor learning.
