# Moving-anchor calibration in GCTS-I

The new lane is a first controlled experiment for learning finite point supports.
It does not implement general continuous-domain GCTS or discover a square tile
without supervision. The existing Turtle engine and its benchmarks are unchanged.

## Training model

Four prototype anchors begin within 0.25 of square corners, with perturbed t and
nonzero alternating m. All coordinates and values are trainable; t stays in [0,1].
The initialization already selects a marking basin. Seeded initialization is
identical in the moving and frozen-anchor controls.

The loss is the sum of squared residuals for:

- Four supplied horizontal/vertical corner-contact relations under fixed unit
  translations. This fixes the topology and scale of the intended square.
- Prototype centroid (1/2,1/2), fixing its otherwise free translation.
- Sum of the four t-values equal to 1 and equal corner t-values (square symmetry).
- Opposite m-values across each unit translation, and mean squared m equal to 1.

These constraints deliberately identify a square with t = 1/4 and an alternating
nonzero marking. They are a supervised calibration target, not a learned pruning
theorem, material energy, or RL reward. Straight segments only illustrate the
anchors. Exact coincidence tests are not differentiated. The contact equations
provide the smooth surrogate; there is no learned contact topology, acceptance
window, separation guarantee for general models, or held-out evaluation here.

Gradient descent uses a fixed step size 0.06 for 300 steps. The freeze control
holds the initial coordinates while training the values. Its residual contact
loss is expected; failure is not evidence of untileability for another domain.

## Frozen exact experiment and contract audit

- **Arithmetic/domain:** an explicitly labeled projected square hypothesis.
  Compilation requires all coordinates/values to be within 0.025 of the square
  target before rounding coordinates to integers, t to integer twelfths and m to
  signs. It checks square t-symmetry and the alternating marking after rounding.
  Exactness belongs to the rounded model, never the floating-point optimizer.
- **Required points:** all 16 sites of (Z/4Z)^2. Opposite boundary edges are
  identified. This is a finite torus experiment, not an unbounded growth claim.
  All roots, including zero-total sites, are active from the start.
- **Placements:** 16 integer translations, each with either of two explicit
  marking phases. Unit translation reverses m; the even period makes this action
  well-defined on the torus. Rotations/reflections are not searched. Each of the
  32 decorated placements can be selected at most once. Phase identity is kept.
- **Point data:** each tile contributes 3/12 at four corners. m is assigned at
  those same points, including all wrapping contacts. No extended marking-only
  domain is present in this experiment. The marking defines a restricted problem;
  failure cannot disprove the unmarked problem.
- **Candidate graph:** exhaustive forward and reverse incidence rebuilt from
  selected placements at every step. Candidate legality checks all four t/m
  dependencies. This small reference experiment has no incremental cache.
- **Scheduler:** global dead points, then global forced moves, then branching.
  Every required point is an explicit generation-0 root, so minimum degree only
  breaks generation ties. General growth-generation bookkeeping is not exercised.
- **Rollback:** immutable selected-id arrays at branches; graph/totals/marks are
  freshly reconstructed. Cancellation and budget exhaustion do not prove failure.
- **Verifier:** reconstructs t-sums and m-agreement from prototype coordinates
  and transforms, without trusting solver graph totals or cached candidate supports.
  Rejects omitted placements, duplicates and inconsistent phases.
- **Results/cost:** reports attempts, accepted placements, forced moves, branch
  decisions, backtracks, current exclusions by reason, graph sizes, active training
  time and active search time. Playback time is separately exported. No speedup
  comparison is claimed. Memory is not measured. Exclusion counts are current
  graph counts, not unique cumulative eliminations.
- **Replay:** JSON includes initial/trained anchors, seed, freeze flag, objective
  terms, version, projected prototype, selected transforms, outcome and timings.

## Validation (2026-09-15)

Run `node tests/test_anchor_learning.mjs`. Analytical gradients agree with central
finite differences for all 16 parameters. Five seeds converge and compile. For
seed 7, loss drops from 1.484433 to approximately 2.1e-30; frozen-anchor loss stays
at 0.337499. The exact search finds 16 placements in 16 attempts, with 9 forced
moves, 7 branch decisions and no backtracks.

An independent exhaustive check examines all 65,536 marking-phase assignments
and finds two exact solutions. This enumeration is complete here: total required
mass is 16, each placement contributes mass 1, and opposite phases at one origin
conflict, so a solution must use one placement at every origin. Additional checks
cover global decision priority, fractional incidence, reversible parent state,
cancellation, unknown on budget exhaustion, and corrupted-result rejection.

Remaining work: independently enumerate domains on more general instances, test
nontrivial rollback after failed children, extended mark-only domains and mixed
generations, and implement incremental updates before any full shared-engine
conformance claim. The present calibration is not evidence of general continuous
support learning, search acceleration, or unrestricted cluster discovery.
