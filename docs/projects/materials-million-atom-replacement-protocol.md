# Small-simulation to million-atom replacement protocol

## Purpose

This protocol tests the strongest intended materials claim:

> Given only molecular-dynamics trajectories or static configurations containing
> 256--1,024 atoms, learn a species-aware geometric grammar and use it to
> generate statistically faithful configurations containing at least one
> million atoms at substantially lower cost than direct million-atom molecular
> dynamics.

Crystals remain mandatory positive controls, but they are not the principal
novelty claim. The decisive targets are three-dimensional quasicrystals and
amorphous solids, where ordinary unit-cell replication is not an adequate
generator.

This is an acceptance protocol, not a promise that the claim is true. A result
passes only at a declared material, state point, boundary condition, and target
observable set. Failure on long-range statistics is a failure even when local
motifs, RDFs, or visual appearance agree.

## Exact boundary of the replacement claim

The product being replaced is a draw from a structural ensemble, or from the
distribution of final configurations produced by a declared preparation
protocol. It is not initially a time-resolved trajectory.

The generator may claim replacement when it produces independent million-atom
configurations with the same declared structural statistics as direct MD, at
the same composition, density, thermodynamic state, and boundary conditions.
The first claim does **not** include faithful transport coefficients, phonon
lifetimes, nucleation times, crack dynamics, aging clocks, or atom-by-atom time
correlations. Those require separate dynamical validation.

The input may contain positions, species, cell geometry, and time ordering of
the small simulations. The structural learner receives no lattice indices,
unit-cell labels, space group, quasicrystalline lift, substitution rule, motif
labels, or million-atom data. Periodic boundary metadata may be used to measure
distances in the observed small simulation, but may not be passed to the
grammar as a known replication rule.

The learned model may be stochastic. This is required for amorphous materials,
where one small configuration cannot determine a unique continuation. Its
output is a distribution of legal overlapping covers, not a single canonical
large structure.

## Experimental unit and data partition

The experimental unit is an independently initialized simulation, not a frame.
Nearby frames from one trajectory must never be split between training and
validation or test sets.

For each material and state point, prepare four disjoint collections:

1. **Small training set:** independent 256--1,024-atom trajectories or static
   configurations used to learn clusters, markings, hierarchy, and move
   ranking.
2. **Small validation set:** independent seeds and, where applicable, withheld
   temperatures, compositions, boundary shapes, or preparation schedules used
   for hyperparameter selection.
3. **Scaling validation set:** direct 10,000- and 100,000-atom references used
   only after the model and primary metrics are frozen.
4. **Sealed million-atom test:** independently produced direct-MD samples and
   metadata held by an evaluation script or investigator who does not train the
   generator.

At least eight independent configurations per method are required for a
screening comparison and at least 20 for a flagship claim. For slowly relaxing
glasses, effective sample size must be estimated from independently quenched
runs rather than inflated with correlated frames.

Spatial shell withholding remains a useful reconstruction test, but it is not
an independent statistical test when both shell and core come from one
trajectory. It must be reported separately from seed-level generalization.

### Leakage controls

- Freeze cluster radii, catalog penalties, marking support, hierarchy depth,
  stopping rules, policy weights, random-seed protocol, and all primary metrics
  before opening the million-atom reference.
- Select hyperparameters on aggregate performance across materials. Do not
  tune a separate model after inspecting each million-atom answer unless the
  result is labeled post hoc.
- Canonicalization may remove global translation and proper rotation, but may
  not use the hidden structure's orientation, lattice, diffraction peaks, or
  phase label.
- A reference potential used to generate the hidden MD data is not a permissible
  oracle during GCTS growth. Any energy calls made during growth are counted and
  must use a model declared before testing.
- Duplicate structures, common parent trajectories, periodically copied small
  cells, and configurations separated by less than the structural correlation
  time must be detected and removed across splits.
- All failed seeds, invalid configurations, timeouts, and out-of-distribution
  events remain in the denominator.

## Benchmark matrix

Every row uses at least two chemical species and arbitrary three-dimensional
positions and orientations. Exact synthetic controls establish correctness;
realistic potential-driven systems establish relevance.

| Family | Required systems | What it tests | Required classification |
|---|---|---|---|
| Periodic static controls | NiAl/B2, Cu3Au/L1\(_2\), GaAs/zinc blende, NaCl/rock salt, SrTiO\(_3\)/perovskite | Blind discovery of translation, species-preserving symmetry, defects, and the trivial replication ceiling | Primitive basis, Bravais lattice, crystal system, point group, space group, Wyckoff environments |
| Thermal crystals | At least one ionic, one covalent, and one metallic crystal at two temperatures | Tolerance to displacement, strain, vacancies, and anharmonic local distributions | Bulk space-group stability versus tolerance; defect and domain map |
| Stacking competition | Zinc-blende/wurtzite or close-packed polytype competition, with single and multiple nuclei | Locally ambiguous continuation, interfaces, confinement, and long-range stacking statistics | Domain-specific space group, orientation, stacking-fault statistics |
| Exact quasiperiodic controls | Coupled icosahedral model set and a decorated inflation system | Recovery of non-translational hierarchy without a separable-axis shortcut | Point group, reciprocal-module rank, inflation data, hidden model-set agreement for audit only |
| Quasicrystal/approximant material | At least one binary or ternary icosahedral or decagonal model with a validated potential, including a competing approximant | Whether learned clusters of clusters preserve aperiodic order, phason disorder, chemistry, and phase competition | Quasicrystal versus approximant, point symmetry, diffraction module, phason-strain statistics; superspace-group candidate where available |
| Simple glass | Binary mixture with a standard glass-forming potential at two quench rates | Stochastic continuation, medium-range order, density fluctuations, and preparation dependence | No forced global space group; local motif and crystallinity distribution |
| Materials glass | At least one metallic, network, or chalcogenide glass with a validated potential | Transfer beyond a toy mixture and chemically meaningful coordination topology | Local point-symmetry, motif-network, ring, and incipient-crystal labels |
| Nulls and adversarial cases | Minimum-distance random set, IID species coloring on a crystal, phase-separated mixture, strained crystal, polycrystal | Memorization, false hierarchy, accidental diffraction, and invalid global classification | Correct rejection or domain-wise classification |

Crystalline controls are run for every generic algorithm revision. An
improvement on a quasicrystal or glass does not excuse a regression in exact
coverage, chirality, species preservation, or symmetry recovery on crystals.

## Compared methods

The following methods receive identical small training data unless a row is
explicitly an oracle ceiling:

1. **Periodic replication:** discover the smallest translation cell from the
   small configuration and replicate it. This is the strongest cheap crystal
   baseline and an intentionally bad glass baseline.
2. **Resampled local environments:** grow by matching local invariant
   neighborhoods, with no global constraint propagation.
3. **Direct learned generator:** an autoregressive, diffusion, or RL placement
   policy using the same cluster candidates but no GCTS legality layer.
4. **Flat unmarked GCTS:** overlapping cluster cover with geometry and species
   agreement but no learned marking.
5. **Positive-mark GCTS:** finite-support markings learned only from accepted
   continuations.
6. **Positive-and-negative GCTS:** positive markings plus nogoods from fully
   exhausted failures; capped searches never supply negative labels.
7. **Hierarchical GCTS:** clusters of clusters and macro-actions, with the same
   bounded marking semantics at each level.
8. **RL-guided hierarchical GCTS:** RL ranks legal branches or proposes
   cluster/rule changes; it cannot override GCTS legality or validation.
9. **Supplied-grammar ceiling:** known unit cell, inflation rule, model-set
   window, or generator-specific hierarchy. This measures headroom and is not a
   learned result.
10. **Direct million-atom MD:** sealed reference and cost baseline, run with the
    declared potential, ensemble, preparation schedule, and independent seeds.

Where practical, include a contemporary non-GCTS structure generator as a
scientific baseline. The exact model class must be frozen in the preregistration
rather than selected after seeing the answer.

## What statistical fidelity means

No single observable establishes fidelity. Metrics are computed for each
independent sample, with species-resolved versions wherever meaningful.

### Local scale

- density and composition;
- partial radial distribution functions `g_ab(r)`;
- coordination-number and neighbor-species distributions;
- bond-length and bond-angle distributions;
- local orientational order and invariant environment descriptors;
- Voronoi-index or polyhedral-motif populations;
- hard collision, minimum-distance, and invalid-valence rates.

### Medium range

- motif--motif correlations as a function of distance and orientation;
- ring-size, network-connectivity, and chemical-short-range-order statistics;
- cluster persistence and hierarchy reuse by spatial scale;
- stacking sequences, domain sizes, interface morphology, and defect-complex
  distributions;
- void-size distributions and pore/network connectivity when applicable.

### Long range

- partial structure factors `S_ab(q)`, including peak positions, widths,
  intensities, and diffuse scattering;
- the lowest accessible `q` decade, number variance, and windowed density and
  composition fluctuations;
- orientational correlation lengths and domain-orientation distributions;
- crystal defect density and strain correlations;
- quasicrystal reciprocal-module consistency, phason strain/flips, inflation
  statistics, and approximant leakage;
- glass crystallinity, phase separation, and spurious periodicity.

The million-atom box is scientifically necessary primarily for these
long-wavelength tests. Agreement only up to the linear size of the 1,024-atom
training box is not extrapolation.

### Distribution-level tests

For each preregistered scalar or curve metric `m`, report the discrepancy
ratio

\[
R_m = \frac{d(m_{\mathrm{generated}},m_{\mathrm{reference}})}
             {d(m_{\mathrm{reference\ split\ A}},
                m_{\mathrm{reference\ split\ B}})},
\]

where `d` and all binning or kernels are frozen before testing. The
denominator measures irreducible reference-to-reference variation. Report
bootstrap confidence intervals over independent seeds, not atoms.
For an exact control whose reference-to-reference discrepancy is zero, the
corresponding generated discrepancy must also be zero rather than dividing by
an arbitrary numerical floor.

Also train a held-out two-sample classifier on invariant multiscale summaries.
Training this classifier must not feed back into the generator. Its balanced
test AUC should be reported with a seed-level confidence interval. Visual
similarity is never a primary metric.

## Held-out physical audit

Structural agreement is followed by a physical audit that was not available
to the generator:

1. Evaluate energies and forces on generated and direct-MD configurations with
   at least one held-out potential or potential committee member not used for
   grammar learning, proposal ranking, rejection, or hyperparameter selection.
2. Perform the same short, tightly specified minimization or low-temperature
   relaxation on both sets.
3. Compare initial energy and force distributions, maximum force tails,
   relaxation energy per atom, RMS displacement normalized by nearest-neighbor
   distance, defect creation, phase changes, and post-relaxation structural
   metrics.
4. For small randomly selected environments, use higher-accuracy calculations
   where affordable to detect shared bias between the reference and audit
   potentials.

Relaxation is an audit, not a repair budget. A generator that produces a wrong
structure which a long relaxation converts into the reference phase has
failed. Any relaxation used routinely to construct the delivered sample is
part of generation cost and must be included in the method definition.

## Crystallographic and nonperiodic categorization

Classification is performed after generation by an evaluator that was not an
input to growth.

For a periodic single crystal, remove a preregistered boundary layer, infer a
primitive cell, and report species-preserving symmetry operations, Bravais
lattice, crystal system, point group, Hermann--Mauguin symbol, space-group
number, and occupied Wyckoff environments. Because thermal noise makes a hard
label tolerance-dependent, sweep a fixed tolerance grid and report the stable
label interval and confidence, not only the most permissive answer.

For polycrystals, first segment orientation-coherent domains. Assign a space
group and orientation to each sufficiently large domain and classify grain
boundaries separately; a single global `P1` label is not informative.

For quasicrystals, ordinary three-dimensional space groups are not sufficient.
Report rotational point symmetry, rank and fit residual of the reciprocal
module, diffraction selection rules, inflation factor and substitution matrix
when discovered, phason strain, and the nearest approximant family. Add a
higher-dimensional superspace-group candidate only when the lift and indexing
are independently stable.

For amorphous samples, report absence of a tolerance-stable long-range space
group, together with local point-symmetry, motif, coordination-network, and
incipient-crystal distributions. Do not relabel amorphous output as globally
`P1` merely because no other group fits.

## Isolating the contribution of GCTS marking

Marking is a capacity-controlled hypothesis. Sweep support radius, active
support size, channel rank, and hierarchy level while charging each in the
description length. For every setting, replay all protected positive examples
and record false accepts, false rejects, unresolved frontiers, expanded nodes,
backtracks, physical-oracle calls, wall time, memory, and output fidelity.

The central ablation holds cluster discovery and candidate actions fixed while
changing only:

- no marking;
- positive finite-support marking;
- negative nogoods alone;
- positive and negative marking;
- hierarchical marking;
- the same learned policy without GCTS;
- GCTS with the same policy replaced by a fixed heuristic.

Marking plays a noticeable role only if, on untouched materials, it either
reduces median expanded nodes or wall time by at least 2x, or reduces
expensive physical-oracle calls by at least 50%, while remaining within the
same fidelity confidence interval and introducing no protected false reject.
The result must transfer beyond the system on which the mark was selected. If
no quasicrystal or amorphous benchmark passes this gate, marking is removed from
the primary scientific claim even if the overall generator succeeds.

## Cost and scaling accounting

Cost includes every operation needed to produce an independent usable sample:

\[
C_{\mathrm{GCTS}} = C_{\mathrm{small\ MD}} + C_{\mathrm{learning}}
 + C_{\mathrm{growth}} + C_{\mathrm{required\ relaxation}}.
\]

Report wall time, CPU core-hours, GPU-hours by device model, peak host and
device memory, energy consumed when measurable, physical force/energy calls,
and effective independent samples. Data conversion, neighbor construction,
failed searches, policy training, and invalid output retries are included.

Direct MD cost includes initialization, equilibration or preparation, the
declared production interval, and decorrelation. If one trajectory yields
several correlated frames, cost is divided only by its effective number of
independent samples. Both methods write the same output fields and precision.

Report both single-use and amortized cost:

\[
C_{\mathrm{one}} = C_{\mathrm{small\ MD}}+C_{\mathrm{learning}}+C_{\mathrm{sample}},
\qquad
C_{M} = \frac{C_{\mathrm{small\ MD}}+C_{\mathrm{learning}}}{M}
       +C_{\mathrm{sample}}.
\]

Implicit macro representations may demonstrate compression and interactive
growth speed, but the primary million-atom timing ends only after all atom
positions and species have been materialized and audited. Compare scaling at
10,000, 100,000, and 1,000,000 atoms on the same hardware. Ideal hierarchy
may reduce search decisions, but materialization remains at least linear in
the number of output atoms.

## Preregistered go/no-go criteria

All primary metrics, tolerances, weights, and confidence procedures are frozen
before the sealed test. A material-level flagship pass requires all of:

1. **Validity:** every generated sample has consistent overlaps and species
   assignments, at least 99.9% of atoms satisfy the preregistered geometric
   validity tests, and the remaining violations are disclosed. Invalid samples
   cannot be silently regenerated.
2. **Local and medium-range fidelity:** the upper 95% confidence bound of
   `R_m` is at most 1.5 for every primary local and medium-range metric, and
   the median `R_m` is at most 1.0.
3. **Long-range fidelity:** the same bound holds for preregistered low-`q`,
   domain, phase, and quasicrystal/glass metrics. Failure here cannot be offset
   by better RDF agreement.
4. **Indistinguishability:** the invariant two-sample classifier has test AUC
   at most 0.55 and its 95% confidence interval includes 0.5.
5. **Physical audit:** generated samples lie inside the 95% direct-reference
   envelope for the primary held-out energy, force, and short-relaxation
   metrics, with no systematic phase conversion under audit relaxation.
6. **Classification:** static crystals recover the correct space group on all
   seeds; thermal crystals recover the reference tolerance-stability profile;
   quasicrystals are not mislabeled as periodic approximants; amorphous samples
   acquire no spurious stable long-range group.
7. **Cost:** the first research success requires at least 10x lower
   cost per independent million-atom sample than direct MD. The stated flagship
   target is at most 1% of direct-MD cost, including small-data generation and
   learning, either for one sample or at a declared amortization count `M`.
8. **Robustness:** no protected crystal control regresses, and the claim holds
   for at least one quasicrystal and one amorphous system not used for
   hyperparameter selection.

Threshold sensitivity must be published. A result that passes only after
changing the preregistered metric set, discarding difficult seeds, or omitting
the lowest wavevectors is exploratory, not confirmatory.

## Staged execution

### Stage 0: harness and sealed evaluation

Implement deterministic data manifests, seed-level splits, metric scripts,
cost logs, invalid-output accounting, and a sealed-reference evaluator. Verify
that copied, randomly colored, phase-separated, and collision-corrupted
samples fail the intended metrics.

### Stage 1: crystalline calibration

Scale each exact protected crystal from 256--1,024 observed atoms to at least
one million. Recover its primitive basis and space group blindly, match exact
replication, and demonstrate that the learner stops at translation rather than
inventing an expensive hierarchy. Add finite-temperature displacement and
defect tests. Failure blocks later stages.

### Stage 2: exact nonperiodic hierarchy

Run the coupled icosahedral and decorated-inflation controls with arbitrary
rotations and finite coordinate noise. Hide the lift, window, and substitution
rule. Require predictive held-out shells, correct million-scale diffraction,
and recovery of the supplied-grammar ceiling within declared tolerance.

### Stage 3: potential-driven quasicrystal competition

Use independent small simulations spanning quasicrystal, approximant, and
competing crystalline outcomes. Freeze the grammar before opening larger
references. Test multiple nuclei, confinement shapes, orientations, and a
withheld state point. This is the first decisive test of non-translational
hierarchy and bounded marking.

### Stage 4: amorphous generation

Begin with a standard binary glass former, then add a chemically distinct
materials glass. Train on multiple independently quenched small boxes and test
million-atom ensembles across at least two quench rates. A successful method
must preserve stochastic diversity and long-wavelength density/composition
fluctuations without crystallizing or periodically copying the training box.

### Stage 5: confirmatory million-atom challenge

Lock the code, model hashes, environments, metrics, and cost procedure. Run the
sealed direct-MD reference and GCTS generators on matched hardware. Open results
once, publish every seed, and classify the claim separately for each material:
pass, structural failure, physical-audit failure, cost failure, or
inconclusive.

## Interpretation of outcomes

A crystal-only success demonstrates engineering correctness, not the central
scientific result. A quasicrystal-only success supports discovery of
compressible nonperiodic hierarchy. An amorphous-only success supports a useful
stochastic structural generator but not necessarily hierarchical compression.
Success on both, with the GCTS ablation passing and cost below the declared
threshold, supports the full structural-replacement claim.

Conversely, failure is informative. If local metrics pass but low-`q`
statistics fail, the small simulations did not determine the necessary
long-range ensemble. If the direct policy matches hierarchical GCTS, the
grammar may still be useful but GCTS marking is not the mechanism. If held-out
relaxation causes large reconstruction, geometry alone is not a physically
closed generator at that state point. The protocol is designed to distinguish
these outcomes rather than hide them behind one visual demonstration.
