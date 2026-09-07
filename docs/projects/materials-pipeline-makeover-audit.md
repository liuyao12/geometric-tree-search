# Materials Growth Lab: pipeline and search audit

6 September 2026. Public baseline: `04f1507612756559744a2985d3d749cf08dc1087`.

## Outcome

The main entry is a focused patch → cluster → marking → search workspace.
The previous page is preserved at `apps/iqc-growth-live/research.html`,
with its scientific modules, evidence atlas and receipts. Legacy portal
tests now read that route. The separate early React prototype at
`apps/materials-growth-lab` was not changed.

## Audit findings

| Area | Finding | Change and boundary |
|---|---|---|
| Search | The old live path ranks and commits compatible batches in `selectCommutingFrontierBatch`. No DFS rollback was found in this path. Displayed stack is accepted history; physical detachments are different. | Iterative DFS retains alternatives and restores atomic/placement state after failed continuation. |
| Interface | 49,678 lines of app logic and 2,929 lines of markup mix the experiment with many optional physics investigations. | Four-stage entry; research console is an explicit separate destination. |
| Seed | Reconstruction, full observed-window continuation, local nuclei and specialized traces have different evidence boundaries. | New search always begins with the entire supplied patch. No hidden target or family label in the learner/search API. |
| Clusters | Multiple shell, molecular and irregular implementations exist in research. | Bounded connected components, adaptive shells and center-free bond-neighborhood unions followed by full colored point-set congruence. Not exhaustive motif mining. |
| Coverage | Atom coverage, center assignments and volume filling differ. | Support union plus residual atoms covers the finite observation; empty volume and periodic extension remain unproved. |
| Orientations | Stabilizer size, observed orientations and channels differ. | Proper intrinsic frames, symmetry groups, and observed orientation classes modulo those symmetries are reported separately. |
| Marking | Training fit does not establish future continuation. | Channel/reach controls and observed connection-frequency regression; loss and directional glyphs are explicitly training diagnostics. |
| RL | No validated general agent is available. | Experimental online UCB bandit learns from novel-site reward and rollback penalties. No physical reward claim. |
| Hierarchy | Re-encoding and promotion do not imply stationary growth. | Optional repeated unions of two overlapping clusters require two atom-disjoint witnesses. One promotion level only. |
| Cost | Represented count and wall time can mislead. | Explicit atom counts, real search checks/backtracks, timed bursts, memory stops and independently retained best structure. |

## GCTS-I correspondence

The reference's `createLiveTilingSearch` analyzes the boundary, emits trials,
commits a choice, recursively explores and undoes failed branches.

| GCTS-I | Atomic workspace |
|---|---|
| oriented tile and translation | cluster and proper SE(3) pose |
| boundary candidates | learned overlap ports composed from placed clusters |
| occupancy overflow | unlike-species coincidence and distance exclusion |
| constrained frontier | positive-frontier degree ordering, all alternatives retained |
| single legal choice | forced-choice event |
| stack and undo | atomic/placement checkpoint and rollback |
| node budget | time pause and explicit memory limits |

This is structural alignment, not identical constraint semantics.
GCTS-I's volume occupancy and global marking compatibility cannot be
assumed for atomistic point sets. Here channels rank legal choices; they
are not a certified global vector-section consistency solver. The finite
learned catalogue samples continuous poses and is not complete over SE(3).
Exhaustion does not prove the material cannot grow.

## Module contracts

- `continuous-geometry.mjs`: colored proper-frame canonicalization, pose
  composition, numerical tolerance keys and spatial exclusion index.
- `continuous-learning.mjs`: position-only supports, recurring types,
  residuals, observed overlap ports, optional promotion and frequency model.
- `continuous-search.mjs`: iterative DFS; immutable observed atoms; whole
  cluster actions; rollback; independent best state; no target API.
- `continuous-worker.mjs`: interruptible progress and resumable timed search.
- `workspace.mjs`: full discovery scene, separate learning scenes,
  actual training curve, in-experiment marking library and downloadable atoms.

Numerical quantization has bin-boundary sensitivity and is not exact
arithmetic. Collinear supports retain continuous stabilizers and remain
residuals. Current exclusion is 0.68 times the smallest observed spacing
(at least twice matching tolerance), a declared geometric heuristic.
It is not an interatomic potential. No missing molecular atoms are invented.
The observed cover may contain rare crop-specific supports.

The previous console's specialized green benchmarks are not transferred
as accuracy certificates for this new engine.

Optional pair promotion deduplicates union supports before congruence tests
and admits at most 12 frequent eligible types, limiting subsequent port
expansion. The audit receipt records this cap; this is not exhaustive
hierarchical motif mining.

## Verification

`node apps/iqc-growth-live/test-continuous-pipeline.mjs` checks both NaCl
octahedra (24 proper symmetries and one observed orientation class),
continuation beyond the full 216-atom seed, posthoc ideal crystal species
and positions, immutable seed, proper rigid transforms, chirality,
model/vocabulary mismatch, decreasing training loss, finite-tree exhaustion,
actual rollback and exact seed restoration.
It also checks promoted ice clusters can continue growth, input permutation
invariance, and resuming an atom-budget stop without losing its alternative.

The release gate passed 52 app tests, 50 JavaScript portal contracts and
19 Python portal contracts. Desktop and narrow-screen browser checks covered
discovery, visible training, marking selection, search and timed pause.

Additional sample probes cover measured D₂O ice VIII, planar graphene,
published Cd–Yb and a disordered hard-core control. These are algorithmic
checks, not held-out physical validation. Overlapping occurrences are not
independent experimental samples.

The wider static-contract inventory also needs maintenance. Running all
257 contracts whose HTML source references were migrated produced 145
passes and 112 failures. Inspected examples require obsolete source
strings: build `20260827-282`, the former “Search a random real material”
label, and the former `coloredPairExclusion(site.species, atom.species)`
call. Those assertions were not weakened to make the audit green.
The current app tests and `*_portal_contract` release gate are checked
separately; a clean release gate does not imply a clean historical archive.

## Ice molecular-growth correction

An additional regression found that boundary-fragment overlap supports could
initially grow oxygen alone, despite identifying water as a cluster. For
molecular-dominated observations, the learner now closes all proposed supports
over repeated isolated components, learns contacts between complete components,
and leaves unrecognized crop fragments as seed residuals. Growth rejects a
placement that would fuse or partially overlap an existing molecule inconsistently.
This is a geometric, inferred-component constraint, not a chemical bond-order
model; mixed, reactive, or extended covalent systems need further validation.

The ice fixture has 56 complete D₂O molecules and 24 residual crop atoms. The
new regression tests both D and H and all four search policies, checking every
accepted prefix: each new O has exactly two hydrogen-isotope neighbors, and
each new hydrogen isotope belongs to one O. Rendering retains species colors
for new atoms and exposes live species counts.

## Remaining research

1. Transported section compatibility with disjoint-patch validation and
   constant/shuffled matched-candidate controls.
2. Stronger frequent irregular subgraph mining and tolerance/noise audits.
3. Certified mandatory boundary obligations; a dead local port currently
   does not imply an unsatisfied physical boundary condition.
4. Safe transposition and local-failure memoization to avoid exploring
   equivalent placement permutations.
5. Deeper promoted rules with independent transfer and stationary evidence.
6. Calibrated physical constraints through a stable adapter to the research
   console, without inheriting diagnostic scores as hard physical laws.
