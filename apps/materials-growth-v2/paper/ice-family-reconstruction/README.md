# Frozen-library ice family reconstruction follow-up

We extended the assigned-base registration exporter from ice VI to developmental ice Ih (`c00400`) and ice II (`c00900`). All cases use byte-identical coordinate-derived motif dictionaries, training field libraries and fit-frame lists. The geometric tolerance remains 0.15 Å and the developmental field radius remains 0.6. No selected tiling, mixed-integer answer, or earlier configuration's geometric exclusions is supplied to the two new searches.

The reference scheduler, Gaussian field adapter and proof-composition runner are unchanged from `../ice-composed-reconstruction/`. Each new case gets one segment of at most 40 rounds / 120 cooperative seconds; the earlier VI result used two segments. These are feasibility diagnostics, not an equal-budget speed comparison. Timings exclude parsing, export and independent audit; some audits ran concurrently with the Ih search. No performance claim follows.

Each new result has independent integer proof-DAG checks and replay of selected rotations, atomic coverage, species, and Gaussian field agreement. The generic replay checker additionally checks selected candidate membership. Its regression run reproduces all earlier VI state metrics. Historical verifier snapshots are preserved.

`summary.json` verifies source hashes, result-to-check links and shared library identity. `*-results.json` contains round-by-round evidence and selected placements; `*-state-check.json` and `*-proof-check.json` are the independent receipts. All point targets remain active even where registrations lack fitting decorations. The large generated candidate models and source-coordinate corpus remain local; this is not a self-contained benchmark download.

Remaining gaps: no complete continuous-pose enumeration, no general learning of anchors or half weights, no demonstrated same-condition / independent-trajectory provenance, no blind extension beyond known atom positions, and no learned-marking speedup. A partial final state is not a proof of extendability, and a timeout is not an impossibility proof. Completing one ice phase does not establish family-wide reconstruction.
