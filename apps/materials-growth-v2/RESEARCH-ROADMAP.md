# Direction: a reproducible GCTS materials research platform

Status: project requirements, not implemented capabilities. Agreed direction:
favor growth throughout the frontier and make results useful to computational
materials scientists. Preserve v1 and the master reference scheduler.

## Scientific purpose and boundaries

Learn reusable geometric clusters and overlap sections from observed positions
and opaque atom labels, then search for consistent extensions. Support crystals,
quasicrystals, amorphous configurations and 2D materials without supplying a phase
label to the learner. This is structural inference, not a time-resolved physical
growth simulation. Geometry alone does not establish energetic stability,
thermodynamic accessibility or a unique continuation of a finite observation.

The first useful deliverable is a reproducible headless experiment with independent
validation, not a larger animated atom count. Browser views inspect that experiment.

## Balanced outward growth

- Maintain the complete declared frontier, including gaps and all directions;
  a display window must never remove obligations or dependencies.
- Retain reference mode: global dead checks, global forced closure, then branching
  at the earliest generation. Prefer the earliest generation among forced moves.
- Add a separately labeled generation-bounded variant. With minimum unresolved
  frontier generation g_min, defer forced moves beyond g_min + Delta. Delta is an
  explicit run parameter, not a geometric matching tolerance. If no eligible
  forced move exists, branch at the earliest unresolved generation. Check global
  dead ends before every decision. Revalidate deferred moves after every change;
  deferral is not candidate elimination. Trail all scheduling state on rollback.
- Neither mode may call a sampled singleton forced or an empty sampled pose pool
  impossible. Unknown domains require refinement or an explicit unresolved result.
- Within generation ties, permit a declared, geometry-aware preference for
  underserved directions. Never override legality or manufacture placements to
  obtain a round picture. Rotational covariance and sensitivity to tie-breaking
  belong in tests. A layered material must not be forced to fill a 3D sphere.
- Report generation spread and directional extent/coverage in the appropriate
  intrinsic dimension, including the full frontier and outer outliers. Distinguish
  incomplete candidate coverage from legitimate anisotropy and forced chains.

This variant changes scheduling and must not be labeled the master baseline.
Balanced appearance is a diagnostic, not proof of faithful search or structure.

## Implementation gates, in order

1. **Search/model conformance.** Compile cluster proposals to validated base
   placements with explicit positive support, shared-constituent accounting and
   marking support. Maintain complete point/candidate incidence for the declared
   domain. Demonstrate dead, forced, earliest-generation and rollback traces on
   independently enumerable finite controls. Test long forced chains with both
   schedulers, and distinguish a finite pose control from continuous-domain search.
2. **Meaningful GCTS learning.** Replace label-copy fitting with local overlap
   sections whose transformation action and uncertainty are explicit. Preserve
   positive overlap evidence, independently justified incompatibilities and
   unknown connections as different categories. Test unary materials where label
   agreement cannot supply connection discrimination. Keep learned exclusions
   labeled hypotheses unless separately proved redundant.
3. **Reconstruction before extrapolation.** Learn on a training region; evaluate
   on spatially held-out regions with a buffer appropriate to neighborhood reach.
   Prevent periodic copies of held-out motifs from leaking across the split.
   Test known-position reconstruction as a separate problem from free growth from
   one atom. Never feed evaluation coordinates into the free-growth search.
4. **Generalization across material families.** Include crystalline, quasicrystalline,
   amorphous, molecular and 2D controls. Test arbitrary rigid transforms, opaque
   relabeling, noise, crop boundaries and multiple initial seeds. Report unsupported
   inputs and unresolved runs rather than excluding them from results.
5. **Research workflow.** Provide versioned headless configurations, repeatable
   runs, resumable checkpoints and atom-coordinate exports with units, metadata
   and provenance. The UI should expose the same options and artifacts, including
   marking-library versions, rather than maintaining a separate experiment model.

## Evidence required for a scientific result

- Separate algorithmic legality, structural fidelity and physical plausibility.
  None is a substitute for the others. Optional external relaxation/energy
  evaluation is a distinct downstream calculation, not chemistry built into search.
- Report total/partial RDF, angular and coordination distributions, composition,
  density and reciprocal-space/order diagnostics, with dimensional normalization
  and finite-size limitations. Exact coordinate agreement is a reconstruction
  metric, not the general objective for independent amorphous realizations.
- Include held-out windows, multiple runs and uncertainty; disclose when available
  data cannot support an independent split. Keep training curves separate from
  validation curves. Do not present RDF error as percent correctness.
- Compare unmarked, fixed-marking and learned-marking experiments on identical
  base candidate models and budgets; compare schedulers separately. Report
  preprocessing, learning, candidate generation, search, verification, wall time,
  memory, forced moves, genuine branches, backtracks and unresolved domains.
- Export inputs/provenance, units, seeds, tolerances, pose-domain assumptions,
  rule versions, scheduler/Delta, software revision, termination reason and
  verification results. Do not claim acceleration over MD without a specified
  comparable scientific task and actual measured costs.

## Current blockers

The current adapter uses anchor-only positive support, occupancy-label sections
and incomplete sampled pose domains. It has not demonstrated the intended GCTS
propagation, balanced coverage or reliable held-out material continuation.
Additional examples and visual polish do not close these gates.
