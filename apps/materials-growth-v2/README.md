# Materials Growth v2 — geometry-first research implementation

A separate application; v1 is not replaced. Open `apps/materials-growth-v2/` from a static HTTP server. No build step or backend service is required. Coordinates and local imports remain in a browser worker.

## What this release establishes

Four stages: an observed configuration → repeated local supports → interval-valued local sections → reversible frontier search. The search receives only positions and opaque species labels. There are no molecular formulas, bonding rules, force fields, reference unit cells, or reference-extension coordinates in the learner or search.

This is a working **research baseline**, not a finished general-purpose materials generator. In particular, satisfying the learned point constraints does not establish that a generated patch is the continuation of the input material. The ice hold-out below deliberately exposes this distinction.

## Reduction and continuous geometry

- An atomic base placement contributes integer `t=1` at its anchor. A recurring anchored neighborhood supplies extended `m` support. Its other atoms are requirements for neighboring base placements, not additional unit contributions counted repeatedly. This is a point-model reduction, **not volumetric polyhedral tiling**.
- `m` has one scalar occupancy channel per opaque label. Missing assignments are unconstrained; zero is assigned. Channels transform trivially; their point positions transform under proper SE(3). Reflections are not allowed in this release.
- Clustering uses irregular nearest-k collections with cutoff ties, followed by colored rigid registration and maximum positional residual checks. It is still an **anchored nearest-neighbor proposal baseline**, not arbitrary subgraph mining. Uncovered atoms are reported, not silently repaired with invented chemistry or gap polyhedra. Periodic closure of a crop is not assumed by clustering.
- Rigid registration estimates real-valued rotations. Candidate poses come from observed occurrence rotations and transported relative connections, optionally supplemented by small rotations about local axes. There is no spatial lattice or global angular grid. Nevertheless this finite evidence pool is **not an exhaustive search of SO(3)**.
- Position correspondence uses a fixed-anchor epsilon ball and rejects ambiguous multiple correspondences. It does not chain near-neighbor matches transitively. A spatial hash accelerates lookup; it is not a lattice constraint. Mapping can depend on proposal order. Orientation-cache rounding and point-identical placement deduplication are approximate; this is not a symmetry certificate.
- Marking compatibility requires the **common intersection of all assigned closed intervals** at each point/channel, not pairwise approximate equality. Real-valued comparisons are approximate floating-point semantics; no exact geometric certificate is claimed.
- The optional complete bounding-box mask says that unobserved positions inside that explicit box are empty. Disable it for irregular/incomplete observation windows. No emptiness is inferred outside the mask. This is a problem-defining observation constraint, not learned chemistry.

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

An exported legal partial assignment is not a finished finite tiling. Frontier obligations may remain unfilled. Budget exhaustion and pauses are checkpoints/unknown, never proof of untileability. The display shows fixed observed atoms even before their anchors have been assigned; it reports seed reconstruction separately from new atoms. It renders the current branch, not the union of incompatible branches.

## Learning and visualization

The first representation fits empirical label occupancy at each registered local point using 24 gradient steps, followed by exact empirical-mean calibration. The chart reports actual fitting MSE, not validation accuracy. This fit is intentionally simple; colored registration already supplies strong label information, and no acceleration benefit is claimed. All samples are observation occurrences, not independent held-out examples. The halo is a value glyph, not a physical potential or a reconstructed equipotential surface.

Stage 2 highlights actual proposals in the full scene. Stage 3 gives each support a separate rotating coordinate view, with a selectable displayed channel. Stage 4 shows only atoms in the scene, with search bookkeeping alongside. Growth runs in one-minute bursts, pauses/resumes in the worker, and stops earlier on unresolved domains or explicit memory budgets. The browser implementation currently uses up to 20,000 cached points and 40,000 cached candidates, not an atom-count target. Initialization and an individual search transaction are not preemptible; the time budget is cooperative.

Examples reuse v1's documented fixtures, including a diffraction-derived **D₂O** ice VIII configuration (deuterium is not silently relabeled hydrogen). XYZ/CIF/JSON import uses the existing parser. File contents are processed locally. The periodic table/database UI from v1 is not yet ported.

## Tests and observed results

Run from the repository root:

```sh
node apps/materials-growth-v2/test-kernel.mjs
node apps/materials-growth-v2/test-material.mjs
node apps/materials-growth-v2/verify-artifact.mjs exported-audit.json
```

Kernel controls cover global ordering, shared forced placements, fractional residuals, marking-only dependencies, nontransitive interval examples, exact semantic rollback, atomic failed expansion, and 32 tiny models checked against exhaustive subset enumeration. Graph rebuilding checks incremental state but shares the legality predicate; subset verification separately accumulates point values. These tests are evidence, not exhaustive proof of implementation correctness.

Material controls include arbitrary proper rotation, opaque relabeling, zero marking error, independent assignment checks, graph checks, complete reconstruction of seed anchors, and preservation of both label species among new atoms. With position error 0.03 Å, marking error 0.05, 400 search steps, and the stated cache limits:

| Control             | Seed anchors reconstructed | New atoms           | Held-out extension agreement                                              |
| ------------------- | -------------------------- | ------------------- | ------------------------------------------------------------------------- |
| NaCl, nearest 6     | 216 / 216                  | 184 (71 Na, 113 Cl) | Not measured in this control                                              |
| Ice VIII, nearest 5 | 192 / 192                  | 208 (130 D, 78 O)   | **165 / 208** new sites match the unseen periodic reference within 0.03 Å |

The reference ice unit cell is used **only in the test evaluator**, never in search. The 43 off-reference additions are a known generalization failure. A partial branch need not have bulk stoichiometry, but that fact does not excuse off-reference coordinates. Short-range consistency does not yet uniquely identify the intended continuation. Increasing reach to 8 or 12 in an earlier ordering experiment did not resolve this and increased cache pressure. Do not advertise these runs as physically realistic ice growth or as a GCTS speedup over MD.

Next substantive milestone: learn stronger, orientation-aware overlap sections and irregular/hierarchical supports, and select them by held-out reconstruction/continuation tests while retaining the same kernel. Additional database examples or visual polish cannot substitute for that milestone.
