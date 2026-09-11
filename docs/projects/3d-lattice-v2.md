# 3D Lattice Tiler v2

V2 replaces the main workbench at both existing entry points:
`/3d-lattice-tiler/` and `/apps/3d-lattice-tiler/`.
The complete previously published explorer remains at
`/apps/3d-lattice-tiler/legacy.html`; its engine, builders, catalog and controls
are unchanged. The new workbench reuses the published exact tile adapters,
Three.js renderer dependencies and separate periodic verifier.

## Experiment and scope

The unit of comparison is a **finite exact point window**, not a tile-count
growth milestone. Every point in a centered integer cube is a required root
obligation of generation zero. All integer translations of the supplied
orientations that touch this window are admissible. Selected placements are
distinct; integer t-values must sum to the common capacity at every required
point and must never exceed capacity anywhere, including the exterior.
The exterior is open: no other point is required to be filled. The target
is finite; a solution is not an infinite tiling certificate or a geometric
solid-cover certificate. Disconnected external components are not introduced.

The original catalog's orientation group is retained and exported explicitly.
In particular, the A₂ prism group has six layer-preserving orientations, not
all cubic rotations. Reflections are optional and shared by all lanes.
Numerical and symbolic weights are rejected rather than rounded. The SCD
geometry therefore remains available in the original explorer, but does not
enter v2's exact comparison without a suitable exact adapter. Its geometric
aperiodicity theorem would not prove aperiodicity of a different finite
point model or a different orientation group.

## Shared engine

`v2/search.js` enumerates the complete candidate universe by every support
alignment at every required point. One candidate node is shared by all its
incident points. Forward incidence and reverse t/m dependencies include
marking-only interactions outside the target. Applying a placement invalidates
every affected candidate at every incident point. Unaffected domains are
preserved. The same trail restores validity, degrees, selected placements,
totals and marking reference counts.

The scheduler checks all dead points first, then all forced points, then
minimum generation (minimum degree only breaks generation ties). Every
target point is an explicit generation-zero root, so this finite experiment
has no later-generation target points. Placement generation is one plus the
minimum incident root generation. No chronological birth order is used.
Future unbounded growth would need a separate fair activation rule and
additional generation trails; v2 does not claim to implement it.

## GCTS and cluster proposals

GCTS synthesizes orientation-equivariant vector markings by equating slots
for **every capacity-legal pair**. No bounded-window dead pair is generalized
into a global forbidden pair. These fields preserve all finite-window
solutions. The 256-slot synthesis budget uses a constant field fallback;
constant fields are elided at runtime because they cannot disagree. Rank,
fallback status, version and scope are exported. These conservative fields
may have no effect at all. V2 does not claim useful learned markings where
the fields are constant.

The additional GCTS pruning consists of proved residual-capacity tests and
context-local failed-move lookahead. At each unfilled point, available
contributions must have enough total mass, and their gcd must divide the
residual. At a genuine branch, up to eight candidates are tried with up to
three forced continuations. A resulting dead point or residual contradiction
proves only that candidate impossible in its current parent context.
Eliminations use the ordinary graph trail and are undone on leaving that
context. No sampling or probe limit truncates the base domains. These costs
and eliminations are separately recorded; they must not be described as
marking-derived eliminations.

The RL lane is an experimental **tabular cluster-return bandit** with bounded
rollout proposals. After the reference scheduler selects a branch, up to
four candidates seed irregular rollouts of up to three base placements.
Each continuation uses the same global scheduler, complete domain and point
legality. Every rollout is rolled back exactly. Expansions can mix supplied
species and orientations; they are not limited to periodic, isohedral or
known motifs. No catalog identity enters the policy.

Proposals are ranked using completed obligations plus their online mean
continuation return. The selected first placement orders the complete base
list; the remaining base alternatives are always retained. Execution returns
to the global scheduler after every placement. Proposal expansions, visits,
return values, training seed and provenance are exported. The table is capped
at 512 retained clusters; excess proposals may still guide the current choice
without being retained. This is finite irregular cluster learning, not a
hierarchical grammar learner or a trained cross-tile policy.

Rollout lookahead and learned returns are distinct components. The reference
experiment includes an ablation with learned values ignored during ordering
(`learnReturns: false`). A win by the cluster lane alone does not establish
that reinforcement learning caused the win. No held-out generalization claim
is made; every lane begins with empty learning state.

## Protocol and reproducibility

The browser runs the four lanes sequentially in fresh workers. The recorded
reference rotates lane order across seeds. Total time includes model
preparation, marking synthesis, complete graph construction, online learning,
proposal validation and final independent verification. Module loading and
message/renderer transport are excluded. The same time limit and 10,000 base
placement-attempt limit apply to every lane. Probe work is charged to wall time
and reported separately; it does not masquerade as a base attempt.

Each engine also enforces a 180,000-candidate resource limit and a depth
limit of 1,024. Hitting either bound cannot prove failure. A browser watchdog
can stop a worker at the selected time limit plus 15 seconds, covering
synchronous preprocessing and graph construction. Time is checked at safe
points, so a run may exceed its nominal limit slightly. Cancellation is
unknown. No interrupted result is relabeled untileable.

The graph chart samples actual current completion, including decreases on
backtracking, rather than reporting only maxima. A budget result can display
the best retained partial state; it is explicitly unverified as a complete
window. Memory is a rough graph/trail footprint estimate, not JS heap or
process RSS; it excludes engine code, workers, renderer and runtime overhead.

Result labels:

- `finite_exact`: independent replay verifies the entire required window and
  every capacity/marking condition, including exterior interactions.
- `exhausted_finite`: the entire finite tree is exhausted under this model.
- `unknown`: time, attempt, depth, memory, watchdog or cancellation limit.
- Unsupported exact input: the comparison is unavailable, not a negative.

Periodic and isohedral probes use the existing exact quotient engine as
separate structural controls (up to eight motif copies). Their certificates
and scope are exported separately. Failure within the bounded family is
unknown, not evidence of aperiodicity. Research cases that miss those probes
are separated from cases where a small certificate was found.

Reproduce:

```sh
node scripts/test-3d-lattice-v2.mjs
node scripts/benchmark-3d-lattice-v2.mjs /tmp/lattice-v2-benchmark
node scripts/verify-3d-lattice-v2-evidence.mjs exported-evidence.json
```

The reference evidence and full summary are linked from the live workbench.
No timing is guaranteed across devices. Three seeds and a 27-point window
are a short diagnostic experiment, not a broad performance study.

## Recorded reference results

Five cases, seeds 1–3, a 27-point target, proper rotations only, and two
seconds / 10,000 attempts per lane produced 6 / 15 verified windows for
free-range, 6 / 15 for GCTS, 6 / 15 for RL clusters and 7 / 15 for the
combination. The combined lane solves hat-prism seeds 1 and 2 and turtle
seed 1 while the baseline remains unknown. The baseline wins other seeds;
there is no overall speedup theorem or statistically established superiority.

Ignoring learned returns during RL ordering still solves the same 6 / 15
instances. That ablation retains table update cost and isolates the ordering
term. The present gains are evidence for rollout-assisted cluster ordering,
not an isolated reinforcement-learning benefit. Useful learned markings also
remain an open research task; constant fields cannot explain a gain.

The eight-copy periodic and isohedral probes both remain unknown within two
seconds for hat, turtle and tuning fork. They both find point certificates
for buckled ring and twisted H, which the UI therefore labels periodic stress
controls. The 16-vertex tile and cube remain explicit known-periodic controls.
None of these bounded misses is a proof of nonperiodicity.

[All measurements](../../apps/3d-lattice-tiler/v2/reference/summary.json) and
[full replay evidence, compressed JSON](../../apps/3d-lattice-tiler/v2/reference/evidence.json.gz)
include every reported seed, successes and failures, all base placement data,
marking metadata, cluster expansions and structural probe certificates.
Timings are local observations on this machine, with ordinary host variability.

## Conformance evidence and remaining gaps

`scripts/test-3d-lattice-v2.mjs` checks independently exhaustive tiny-model
agreement for all four lanes, fractional residuals, shared candidates,
untouched required points, full rollback, explicit-zero and extended
marking-only interactions, dead/forced/generation precedence, budget labels,
and cluster/probe transaction correctness. `verify()` independently rebuilds
the point sums and markings directly from exported base placements; it does
not use graph state or search caches. Browser checks cover running, stopping,
lane selection, geometry controls, reflection changes, periodic probes,
custom JSON, export, unsupported input and mobile layout.

Remaining limits: no geometric-solid verifier for general returned patches;
no unbounded frontier activation; no learned marking synthesis from higher
order obstruction certificates; no hierarchical cluster composition; no
proof of nonperiodicity for the showcased point problems; no statistical
claim that the new lanes outperform free-range across the tile population.
The original engine and historical benchmark semantics are preserved behind
the original-explorer link and are not retroactively declared conforming.
