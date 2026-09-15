# Registration without target-local junction states

The new registration path matches learned cloud-marked motifs directly against
available neighboring pair geometry. The generator does not read junction-state
tables, class-connection tables or selected fillings. Known fillings are used
only afterward to check coverage of the frozen proposal pool.

This removes a real dependency from the previous pipeline. It does **not** remove
all dependence on the target: the finite observed base-pair incidence and periodic
coordinates are still inputs. The library was trained on this family. This is
not blind growth, independent material generalization or continuous-pose
completeness.

## Geometry-only proposal procedure

For each applicable pair, the generator constructs a neighborhood containing all
available outgoing pair vectors at both endpoints. It does not select a junction
state first. Vectors carry the existing opaque pair-type and t/m decorations.
No chemistry or formation-history rule is introduced.

A connecting vector and a nonparallel vector define a proper-rotation frame
proposal. Color-compatible target vectors generate frame candidates. The full
two-endpoint cloud is then matched injectively and refined by a proper
least-squares rotation. Accepted fits are checked against unrounded coordinates
with maximum residual 0.03 Å. This permits arbitrary fitted rotations, not just
a fixed list of lattice orientations.

The proposal procedure has explicit limitations: an eight-times-tolerance
correspondence window, a 4,096-leaf cap for ambiguous frame proposals, and a
1e-9 Å quantized descriptor cache. Every retained fit is recomputed and checked
on unrounded geometry, but cached omissions and approximate frame seeding are
not exhaustiveness proofs. Rank-deficient frames are flagged. No cap was reached
on this dataset; that fact does not establish completeness over continuous
rotation neighborhoods.

## Independent checks

The pass tests 1,828,846 template/query combinations and produces 67,941 checked
registrations. An independent verifier reconstructs the raw periodic vectors,
checks proper rotations, endpoint correspondence, labels and local t sums, then
checks training coverage. Maximum residual is 0.02999134561 Å.

| Input | Registrations | Distinct arm-selection patterns | Earlier patterns retained | Additional patterns |
|---|---:|---:|---:|---:|
| β-B106 | 49,059 | 48,267 | 47,025 / 47,025 | 1,242 |
| τ-B106 | 18,882 | 18,720 | 18,369 / 18,369 | 351 |

The comparison concerns discrete arm selections, not equality of floating-point
rotation parameters or of entire marking-value sets. All earlier patterns and
all recorded training connections survive. Multiple registrations can realize
one arm-selection pattern. The other four inputs have no applicable pair-only
junction-to-junction edges; their base candidate pools are unchanged.

One hundred noisy rotation/permutation/distractor controls pass. A symmetric
octahedral control recovers four rotations around the connecting direction;
reflections are rejected for a chiral control and degenerate frames are flagged.

## Compilation and search

Compilation converts these registrations to the same portable cloud values used
by the existing search plug-in. It does not read old junction-state tables.
Only after the candidate pool is frozen does it select training lifts for
verification. All eighteen training records lift successfully.

The resulting β pool has 49,950 variants representing 4,725 base placements;
τ has 21,042 variants representing 7,452 base placements. The 54 and 432 omitted
base placements, respectively, remain omissions of a learned proposal model,
not certified impossibilities of the original unrestricted problem.

The unchanged search uses reference global priority and earliest-generation
branching, shared-placement inventory, conservative marking-set rejection and
checked common values at completion. Both cloud-enabled and disabled lanes use
the same registered pool. Four easier structures complete in the short
30-second-checkpoint tests; both B106 inputs remain unresolved. Those four
successes do not test nontrivial cloud constraints. There is no short-run
reconstruction gain or demonstrated speedup.

A separate τ-B106 extension completes in 109.69 seconds under a 300-second
checkpoint limit: 5,427 placements fill all 5,724 target positions, with one
connected positive-support component and 2,052 verified common marking values.
The independent checker reconstructs t totals, scalar agreement, inventory and
cloud witnesses. The recovered base-placement set equals the original training
decomposition. That selection was not passed to search, but this remains an
in-sample reconstruction, not a new decomposition or material prediction.

The run makes 5,761 advances, with 2,828 degree-one placements, 2,772 branch
choices and 260 backtracks. Counters include abandoned placements. There is no
matched extended-budget comparison. Timings include search audits but exclude
prior learning and registration; these single-machine diagnostics are not
statistical benchmarks. β-B106 remains unresolved in the short runs.

## Interpretation and remaining work

The concrete result is that geometric registration can recover all earlier
local patterns and additional compatible patterns without consulting their
target-state labels. It is a less target-specific way to build the candidate
pool—not proof that all possible arrangements have been found.

Observed base-pair incidence and the criterion for applying cloud decorations
are still derived from the known configuration. Seed-driven generation beyond
that configuration, uncertainty-aware pose completeness, more efficient graph
updates and a stronger common-value solver remain needed. Independent,
verified condition-matched family evaluation, including ice, remains unfinished.

## Reproduction

```
python test-portable-geometry-registration.py
python register-portable-geometry.py INPUT GEOMETRY_FOLDER PORTABLE REGISTRATIONS
python verify-portable-geometry-registration.py INPUT GEOMETRY_FOLDER PORTABLE REGISTRATIONS LEARNED ALTERNATIVES CHECK
python compare-geometry-registration-pools.py JUNCTIONS JOINED REGISTRATIONS COMPARISON
node compile-geometry-search.mjs COMPILED PORTABLE REGISTRATIONS ALTERNATIVES MODEL
node boron-portable-search.mjs MODEL KERNEL SEARCH_FOLDER
python verify-geometry-search.py INPUT COMPILED GEOMETRY_FOLDER REGISTRATIONS PORTABLE ALTERNATIVES MODEL SEARCH_FOLDER KERNEL SEARCH_CHECK
node boron-geometry-extended.mjs MODEL KERNEL EXTENDED_FOLDER
```

Use the same verifier with EXTENDED_FOLDER for the extension. Python requires
NumPy. Generated model and search paths must be new. The raw coordinate-derived
libraries and pools are not republished here; source/check downloads are audit
evidence, not a self-contained reproduction bundle. Prior provenance and data
acquisition requirements continue to apply.
