# Materials Growth v2 — geometry-first research implementation

A separate application; v1 is not replaced. Open `apps/materials-growth-v2/` from a static HTTP server. No build step or backend service is required. Coordinates and local imports remain in a browser worker.

Project direction: [balanced growth and a reproducible materials research platform](RESEARCH-ROADMAP.md).
That document defines the next implementation and validation gates; it does not
claim those capabilities already exist in this release.

## What this release establishes

### Resumable browser memory checkpoints

The browser uses `softMemory: true`: reaching a point/candidate quota pauses only
after the current placement and its domain expansion finish. Continue doubles
both working quotas relative to current usage and resumes the existing engine,
trail and stack. This is not a guarantee of unlimited memory; one transaction may
overshoot a quota, and browser/OS memory limits still apply. Unresolved geometry
and exhausted searches are not relabeled as resumable memory events. Headless
controls retain hard quotas by default, preserving historical benchmark semantics.
`test-memory-resume.mjs` compares repeated point/candidate pauses against an
uninterrupted control, including placements, frontier, generations and stack.

### Connecting disconnected supports

Adaptive discovery now checks the connectivity of the observed local-support
hypergraph. When first-shell proposals form separate finite components, it finds
components that match complete recurring local observations, then proposes unions
with their nearest component shell (minimum inter-component atom distance, shell
width `max(4*epsilon, 0.08*nearestDistance)`). Missing placement anchors are preferred;
no labels are interpreted as chemistry. Unions are capped at 38 atoms and retained
only after repeated proper rigid registration. Possible truncated connector
contexts are separated under the crop hypothesis and retained in exported metadata.
Small local motifs are not removed just because a larger connector contains them.

For the default ice VIII crop this gives one three-site local motif and five
connector classes (four 12-site and one 15-site class). The input is D2O: D labels
remain unchanged. Stage 02 distinguishes local/connector motifs and reports atom
coverage, placement-anchor coverage and observed support components separately.
At 0.03 Å, coverage remains 168/192 atoms, anchor coverage increases from 56 to 72,
and support components decrease from 56 to 30. These are finite-crop observations,
not a full reconstruction claim. The default single-seed control reaches 100 atoms
with both species and legal point assignments; periodic-reference fidelity is
reported independently and is not asserted by this test. Only 13/100 positions
match the periodic reference in its original frame in this run (no global
registration optimization is applied). This is not successful ice reconstruction;
the result is evidence that local compatibility remains insufficient. Run
`node apps/materials-growth-v2/test-ice-connectors.mjs`.

This is a one-level geometric connector proposal, not exhaustive irregular-cluster
discovery, certified volume filling, a chemical bond graph, or a physical growth
law. Uncovered crop atoms and missing anchors remain explicit. Continuous pose
completeness, strong GCTS marking learning and general material fidelity remain
open; introducing connector templates does not resolve those engine limitations.

### Adaptive discovery update

The default proposal now selects a first radial shell at the first adjacent
distance gap exceeding `max(4 * epsilon, 0.08 * nearestDistance)`. If no gap is
resolved, it falls back to a capped neighborhood; this is a heuristic, not a
universal shell detector. The legacy nearest-k control remains available.
Registered strict subsets of larger recurring motifs are separated as possible
crop fragments under the explicitly selected crop hypothesis. All partial
observations remain in the export and stage-02 gallery; “preserve all environments”
keeps them as motifs for surface/defect investigations. No boundary geometry or
periodic extension is inferred as fact. Residual coverage remains reported.

NaCl now yields the two seven-site octahedral motifs by default, without element
rules. FCC, BCC, diamond and graphene controls yield 13, 9, 5 and 4 sites
respectively. Stage 02 retains the full proposal scene and adds rotating motif
views with observation highlighting; marking glyphs remain exclusive to stage 03.
This does not solve arbitrary irregular cluster discovery, linear-support
registration, symmetry-group enumeration, or the GCTS growth integration gaps.
Run `node apps/materials-growth-v2/test-discovery.mjs` for the new controls.

Four stages: an observed configuration → repeated local supports → interval-valued local sections → reversible frontier search. The search receives only positions and opaque species labels. There are no molecular formulas, bonding rules, force fields, reference unit cells, or reference-extension coordinates in the learner or search.

This is a working **research baseline**, not a finished general-purpose materials generator. In particular, satisfying the learned point constraints does not establish that a generated patch is the continuation of the input material. The ice hold-out below deliberately exposes this distinction.

The target scope is **crystalline, quasicrystalline, and amorphous materials**, including 2D structures. The algorithm does not receive a phase label or a periodicity assumption. Example names describe reference inputs, not a predicted phase of the output. These families are all in the regression suite, including a published melt-quenched Si configuration; that is test coverage, **not a claim that the current learner can grow all of them**. Statistical local-environment learning, richer overlap sections and long-range diffraction/order diagnostics are still needed. In particular, an amorphous target should be assessed by ensemble/local statistics, not by exact reproduction of one realization or a periodic unit cell.

## Single-atom growth and structural fidelity

The browser now starts stage 4 with **one atom at the origin**. Its label is taken from the observation atom closest to the centroid. No other training positions are fixed, no observation bounding-box emptiness mask is applied, and no training atom is merely hidden in the renderer. The rest of the input influences only the learned support/connection library. Support occurrence frequency breaks otherwise equal candidate-ordering scores in this mode. The master graph scheduler is unchanged. `seedMode: 'patch'` remains an explicit headless reconstruction control for historical tests, not the browser default.

`metrics.mjs` is an evaluation-only module: it is not imported by the search engine. The worker compares the generated patch to the training patch centered on the selected seed, using:

- Total and species-pair partial RDF curves, nearest-neighbor distances, composition total variation, four-nearest-neighbor angular-distribution total variation, and coordination counts within 1.25 times the reference median nearest-neighbor distance.
- A common origin-centered disk/ball window: radius is the smaller of the two patches' 90th-percentile radii, with RDF range 0.6 times that radius. Both curves use 64 linearly smoothed bins. Pairs are translation-edge-corrected by the ratio of window volume to its overlap with a translated copy. Total g(r) is normalized by N(N−1), shell volume and window volume; unlike-label partials use N_a N_b, and like-label partials use N_a(N_a−1). Planar references use area/ring normalization; nonplanar growth against a planar reference is flagged rather than scored with a 3D volume.
- RDF error is `sum(abs(g_ref-g_grown))/sum(g_ref+g_grown)`, **not a percent-correct value**. Missing partial-channel pairs report unavailable, not perfect agreement. Fewer than 24 atoms in either common window report insufficient data. Metric budgets are 1,500 atoms per common window, 50,000 atoms scanned per patch and 12 labels; a large outer growth region does not unnecessarily disable the core-window comparison.

Finite growth is not a homogeneous periodic bulk sample. Window truncation, interfaces, incomplete frontier obligations and anisotropy remain important even after edge correction. The 90% window also omits outer outliers; no global correctness claim is based on it. The standard density/shell normalization and its homogeneous-system limitation are described in [LAMMPS' RDF documentation](https://docs.lammps.org/compute_rdf.html); our disk/ball edge correction is an explicitly different finite-window estimator. It passes a uniform-ball control with mean g ≈ 0.996, plus identity, rotation, wrong-scale, missing-label, planar and insufficient-data controls. No physical bond exclusions are applied.

RDF discards angles and does not establish long-range order or structural uniqueness. The new scores are **training-reference fidelity diagnostics**, not held-out accuracy, confidence intervals, phase classification or physical stability. Structure factors, orientational order parameters, independently sampled reference windows and replicate uncertainty are future evaluation requirements for distinguishing crystal/quasicrystal/amorphous outcomes rigorously.

`benchmark-results.json` records eleven single-seed cases under identical limits (160 steps or 10 cooperative search seconds, 8,000 cached points and 20,000 candidates). Eight produce enough atoms for metrics. The Cd–Yb crop stops on ambiguous correspondence; the quenched-Si and random-packing inputs produce no near-exact recurring supports at the tested 0.03 Å tolerance. These are learner/domain limitations, not impossible materials. The 2D cases have relatively small RDF and angular errors, while silicon demonstrates that modest radial error can coexist with considerably larger angular error. All results, including unresolved ones, are shown in the browser regression table. The browser's larger memory limits differ from this fixed test protocol.

## Reduction and continuous geometry

- An atomic base placement contributes integer `t=1` at its anchor. A recurring anchored neighborhood supplies extended `m` support. Its other atoms are requirements for neighboring base placements, not additional unit contributions counted repeatedly. This is a point-model reduction, **not volumetric polyhedral tiling**.
- `m` has one scalar occupancy channel per opaque label. Missing assignments are unconstrained; zero is assigned. Channels transform trivially; their point positions transform under proper SE(3). Reflections are not allowed in this release.
- Clustering uses adaptive first-shell or legacy nearest-k collections, followed by colored rigid registration and maximum positional residual checks. It is still an **anchored local proposal baseline**, not arbitrary subgraph mining. Uncovered atoms are reported, not silently repaired with invented chemistry or gap polyhedra. Periodic closure of a crop is not assumed by clustering.
- Rigid registration estimates real-valued rotations. Candidate poses come from observed occurrence rotations and transported relative connections, optionally supplemented by small rotations about local axes. There is no spatial lattice or global angular grid. Nevertheless this finite evidence pool is **not an exhaustive search of SO(3)**.
- Position correspondence uses a fixed-anchor epsilon ball and rejects ambiguous multiple correspondences. It does not chain near-neighbor matches transitively. A spatial hash accelerates lookup; it is not a lattice constraint. Mapping can depend on proposal order. Orientation-cache rounding and point-identical placement deduplication are approximate; this is not a symmetry certificate.
- Marking compatibility requires the **common intersection of all assigned closed intervals** at each point/channel, not pairwise approximate equality. Real-valued comparisons are approximate floating-point semantics; no exact geometric certificate is claimed.
- In the legacy headless `seedMode: 'patch'` control only, an optional complete bounding-box mask declares missing positions empty. The browser's single-seed mode always disables that mask and retains only the one seed observation.

## Master-algorithm ledger

Normative reference: `docs/basic-tiling-algorithm.md` (local contract read on 2026-09-10), based on `GCTS-I.html`. This implementation does not import the older geometric engines.

| Contract                                          | Implementation and scope                                                                                                                                                                                                                                                                                                               |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Point values and complete frontier incidence      | `kernel.mjs`: explicit Q, integer capacity units, weighted forward edges, shared candidate IDs, reverse incidence, and dependencies on all t/m points, including marking-only points.                                                                                                                                                  |
| Global dead → global forced → earliest generation | Certified-complete finite domains use this order. Degree only breaks generation ties. Material domains are all incomplete: no sampled singleton is labeled forced, and empty sampled domains are unresolved.                                                                                                                           |
| Generations                                       | Root obligations start at zero. Tile generation is one plus the minimum positive-support point generation. The adapter explicitly activates neighborhood obligations at the exposing tile's generation; it does not claim fair coverage of all continuous space.                                                                       |
| Rollback                                          | Totals, assignments, placements, activations, and generations are trailed. Undo revalidates the dependency closure of restored values, retaining unaffected domains. Immutable proposal caches persist; validity and incidence are reconstructed locally rather than literal edge-delta journaling. Failed kernel expansion is atomic. |
| Candidate completeness                            | Finite supplied kernel models are declared complete by the caller. The material adapter never certifies continuous-domain exhaustion. Cached alternatives are provisional, and unresolved branches may be set aside to explore other sampled alternatives.                                                                             |
| GCTS scope                                        | Empirical occupancy sections are learned hypotheses. Fixed seed observations/mask are problem-defining marks. No hypothesis is called a proved redundant constraint.                                                                                                                                                                   |
| Candidate ordering                                | After the graph scheduler chooses a point, candidates supported by connections transported from currently selected placements are tried first. Sources are checked against the live accepted prefix, so rolled-back placements do not retain preference. This is an observed-connection heuristic, not RL.                             |
| Rule changes                                      | Retraining or changing search controls discards the search instance. No old trail or candidate validity survives into the new marking experiment.                                                                                                                                                                                      |
| Verification                                      | Independent accumulation of selected t/m data checks capacity, interval intersection, and remaining obligations. Export includes the compiled model, selected IDs, observations, grammar, poses, marking version, parameters, and counters.                                                                                            |
| Remaining gaps                                    | Literal graph-delta journaling, certified continuous pose coverage, certified symmetry quotienting, generic irregular/hierarchical cluster discovery, geometric non-overlap beyond point correspondence, rich equivariant learned representations, held-out model selection, RL, and verified long-range material reproduction.        |

An exported legal partial assignment is not a finished finite tiling. Frontier obligations may remain unfilled. Budget exhaustion and pauses are checkpoints/unknown, never proof of untileability. The display shows the single seed even before its local context has been assigned, then only the currently selected additional atomic placements. It renders the current branch, not the union of incompatible branches.

## Learning and visualization

The first representation fits empirical label occupancy at each registered local point using 24 gradient steps, followed by exact empirical-mean calibration. The chart reports actual fitting MSE, not validation accuracy. This fit is intentionally simple; colored registration already supplies strong label information, and no acceleration benefit is claimed. All samples are observation occurrences, not independent held-out examples. The halo is a value glyph, not a physical potential or a reconstructed equipotential surface.

Stage 2 highlights actual proposals in the full scene. Stage 3 gives each support a separate rotating coordinate view, with a selectable displayed channel. Stage 4 shows only atoms in the scene, with search bookkeeping alongside. A single Run/Pause/Continue button controls growth without a duration limit. It automatically pauses after active-frontier coronas 3, 5, 7, and onward: all remaining frontier points must have generation greater than the threshold, with no degree-zero domain anywhere. Empty frontier is handled by the search termination path, not counted as infinitely many completed coronas. Manual pauses preserve the pending threshold; automatic pauses advance it. If one transaction crosses several thresholds, the next target is the next uncompleted odd generation. Checkpoints preserve the search stack and do not alter forced/branch ordering. These are finite active-domain checkpoints, not certified coverage of continuous space. Growth may stop earlier on unresolved domains or explicit memory budgets. The browser implementation currently uses up to 20,000 cached points and 40,000 cached candidates, not an atom-count target. Initialization and an individual search transaction are not preemptible; manual pause is serviced between worker transactions.

Examples reuse v1's documented fixtures, including a diffraction-derived **D₂O** ice VIII configuration (deuterium is not silently relabeled hydrogen). XYZ/CIF/JSON import uses the existing parser. File contents are processed locally. The periodic table/database UI from v1 is not yet ported.

Additional ideal controls are FCC Cu, BCC Fe, diamond Si, cubic CsCl and 2D h-BN, with explicitly illustrative, unrelaxed cell parameters. `asi-sample.mjs` contains frame 0 of the 216-atom file in Rosset, Drabold and Deringer's [a-Si research dataset](https://github.com/lamrosset/aSi-data), [DOI 10.5281/zenodo.14203730](https://doi.org/10.5281/zenodo.14203730), licensed CC BY 4.0. Attribution, original header, source blob identity and frame SHA-256 are retained. Coordinates/species are unchanged; forces and energies are omitted. The dataset spans disorder through paracrystallinity, so the sampled frame is named by provenance rather than treated as a phase certificate. Its periodic metadata is not passed into learning/search. The random Cu–Zr packing remains a separate negative control, not a thermodynamically validated glass.

## Tests and observed results

Run from the repository root:

```sh
node apps/materials-growth-v2/test-kernel.mjs
node apps/materials-growth-v2/test-material.mjs
node apps/materials-growth-v2/test-metrics.mjs
node apps/materials-growth-v2/test-single-seed.mjs apps/materials-growth-v2/benchmark-results.json
node apps/materials-growth-v2/verify-artifact.mjs exported-audit.json
```

Kernel controls cover global ordering, shared forced placements, fractional residuals, marking-only dependencies, nontransitive interval examples, exact semantic rollback, atomic failed expansion, and 32 tiny models checked against exhaustive subset enumeration. Graph rebuilding checks incremental state but shares the legality predicate; subset verification separately accumulates point values. These tests are evidence, not exhaustive proof of implementation correctness.

The following **historical full-patch controls** explicitly run `seedMode: 'patch'` and are not single-atom browser benchmarks. They include arbitrary proper rotation, opaque relabeling, zero marking error, independent assignment checks, graph checks, complete reconstruction of seed anchors, and preservation of both label species among new atoms. With position error 0.03 Å, marking error 0.05, 400 search steps, and the stated cache limits:

| Control             | Seed anchors reconstructed | New atoms           | Held-out extension agreement                                              |
| ------------------- | -------------------------- | ------------------- | ------------------------------------------------------------------------- |
| NaCl, nearest 6     | 216 / 216                  | 184 (71 Na, 113 Cl) | Not measured in this control                                              |
| Ice VIII, nearest 5 | 192 / 192                  | 208 (130 D, 78 O)   | **165 / 208** new sites match the unseen periodic reference within 0.03 Å |

The reference ice unit cell is used **only in the test evaluator**, never in search. The 43 off-reference additions are a known generalization failure. A partial branch need not have bulk stoichiometry, but that fact does not excuse off-reference coordinates. Short-range consistency does not yet uniquely identify the intended continuation. Increasing reach to 8 or 12 in an earlier ordering experiment did not resolve this and increased cache pressure. Do not advertise these runs as physically realistic ice growth or as a GCTS speedup over MD.

Next substantive milestone: learn stronger, orientation-aware overlap sections and irregular/hierarchical supports, and select them by held-out reconstruction/continuation tests while retaining the same kernel. Additional database examples or visual polish cannot substitute for that milestone.
