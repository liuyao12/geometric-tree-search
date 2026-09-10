# Periodic and isohedral point-quotient rewrite — 2026-09-10

The dedicated Translational and Isohedral lanes now use `apps/3d-lattice-tiler/periodic-search.js`. They search **integer point-value tilings** under the master point-value contract. A certificate proves that model; geometric faithfulness is a separate verification. The other four interactive lanes are unchanged by the published patch.

## Audit of both starting versions

The working directory and published main were different. The local geometric engine admitted general polyhedra only through a one-tile construction, restricted the multi-tile solver to polycubes, and defaulted to four copies. Its isohedral path was a greedy corona followed by generic growth, not a tile-transitivity decision.

The actual published source, `c39c17eb431106f54c2865b34f5fef88ca89fea4`, had a newer exhaustive weighted quotient enumerator and a genuine affine motif symmetry checker. Its exact-model gate required `prototiles.length === 1`. Reflections of a chiral tile created a second prototile, so **both exact lanes were bypassed for the eight-tile example**. A three-second reproduction of each lane ended inconclusively in `geometric_certificate_search_only`. Its determinant-first HNF traversal could also spend excessive time on small skew domains before reaching a simple larger cell. The audit does not establish that its symmetry verifier was unsound.

Publication applies targeted changes to this newer version, rather than replacing it with the older working directory. All 40 non-census registry entries were checked for identical names, vertices, faces and occupancy data. All 114 registry entries carrying automated census provenance were removed. Source datasets and historical results remain archived; custom user storage is untouched. Authored A₂ prisms and the manually supplied 16-vertex tile remain.

## New search and exactness scope

- Domain: Z³ modulo a full-rank integral HNF lattice, with optional even-sum FCC translation restrictions. Every quotient point, including untouched points, is an explicit required obligation of generation zero.
- Values: positive integer t-units and a common integer capacity. Periodic images at the same point are **summed**, including self-wrap contributions. Numerical solid angles are reported as unsupported exact data, not rounded into certificates. This lane has no added m-values or learned exclusions.
- Candidates: all supplied exact orientations and all allowed translations in the quotient. Complete forward and reverse incidence, shared candidates, selected-placement identity, totals and degrees are maintained. Root translation symmetry keeps all possible root orientations/species.
- Scheduler: global degree-zero first, then any global singleton, then minimum degree among the generation-zero obligations. Applying a row disables it and every affected conflicting row at all incident points. Undo restores totals, selection, validity, degrees and the conflict trail exactly. No geometry predicates or heuristic candidate pruning enter this graph.
- Domain order: each volume gets its boxes and the first 64 skew HNFs, followed by the remaining skew forms across volumes. This ordering was improved using the stress census; it is not a minimal-unit search. A found motif may have a smaller oblique fundamental cell.
- Bounds: visible motif limit defaults to eight; maximum quotient volume defaults to 512, HNF count to 20,000 and nodes per quotient to 4,000. Node/time/cancellation limits and skipped unfinished quotients remain explicit. Exhaustion of this bounded family is **unknown for unrestricted tiling**, never a non-tiling or non-isohedral proof. Mixed-species selections require all selected species unless configured otherwise; a reflected copy retains its parent species.
- Positive replay: an independent BigInt verifier reconstructs totals from the original unfurled point supports and HNF coordinates, checks distinct placement identity and translation rules, and requires every quotient total to equal capacity. Certificates include the complete oriented point model, motif, period lattice, reflection choice and engine version.
- Isohedral replay: after a periodic solution, test lattice-normalizing signed-permutation affine isometries. Each motif tile needs a witness mapping the root to it and permuting the **entire** motif, with full unwrapped tile shapes preserved. Store the permutations and affine maps. Failed symmetry checks continue through other periodic solutions. These are sufficient positive certificates; the bounded normalizer search is not a complete negative decider for arbitrary geometric isohedral tilings.
- Presentation: expanding a certificate is a finite preview, independent of its infinite point-tiling proof. It does not certify a requested finite geometric box or a completed adjacency shell. The motif bound no longer derives from the display count. Stream checkpoints apply backpressure so the benchmark can pause without background search continuing past its clock budget.

## Conformance evidence

`scripts/test-3d-periodic-rewrite.mjs` compares all reachable states of a small fractional instance against independent exhaustive candidate scans and checks exact rollback (37 states), global dead-before-forced ordering, late singleton priority, skew HNF reduction at negative points, distinct placement multiplicity, cancellation/limits, malformed and damaged certificates, and a periodic domino tiling which must fail isohedral certification. All finite obligations share generation zero; this does not audit the unrelated growth engines' generation conventions.

The 16-vertex tile is rediscovered without importing a stored construction: eight tiles in a 6×6×6 box, four of each handedness. Both dedicated lanes independently certify it. The isohedral certificate contains eight orbit witnesses. The proper-rotation 64-copy source witness remains separately checked by the existing solid-angle/source regression; the rewrite does not infer a proper-only eight-tile construction.

The public-version adapter and browser worker were tested. Browser runs display the periodic patch, reuse motif colors, and report certified unit cells in both lanes. The visible reflection control is necessary to reproduce this particular eight-tile result. Independent exact rational clipping and oriented-face cancellation also certifies the new witness geometrically (216 residues, 255 clipped faces, 868 edge segments, zero uncancelled boundary lines). Independent exact rational clipping and oriented-face cancellation also certifies the new witness geometrically (216 residues, 255 clipped faces, 868 edge segments, zero uncancelled boundary lines).

## Reproducible stress search

`scripts/search-3d-lattice-stress.mjs 7` enumerates every connected polycube through seven cubes, modulo translation and proper cubic rotations, keeping mirror classes distinct. It uses the app's exact solid-angle point data, cold per-candidate runs, at most eight motif copies and 750 ms per lane. It saves every candidate, bounds, elapsed work, certificate and symmetry result; it additionally checks each witness against voxel occupancy to distinguish a point-value certificate from a geometric polycube certificate. A 12-item shortlist includes importable custom tile definitions.

The initial diagonal-first screen through six cubes found 205 periodic and 190 isohedral point certificates among 207 tiles. After prioritizing a small number of skew HNFs at each volume, the same family returned 207 periodic and 207 isohedral point certificates in about two seconds total. These are empirical timing observations, not a learned pruning theorem. Final counts and the expanded census are in `runs/3d-periodic-rewrite-20260910/stress-summary.json`.

Historical scripts describing voxel exact cover or geometric face-to-face obstruction retain those semantics; the new point-value lane must not inherit their negative conclusions. No aperiodicity or non-tiling claim follows from the unresolved stress cases.

## Live progress repair (2026-09-10)

The initial rewrite emitted geometry only after certification, and the six-lane
comparison worker discarded periodic progress. Consequently, an unfinished or
inconclusive periodic search had no displayed tile or growth-curve samples.

Both periodic lanes now immediately publish an input seed preview. As search
proceeds they retain the largest consistent motif candidate observed after the
global dead-point check, and send cell/node progress through cooperative worker
checkpoints. These previews are not growth milestones or proofs of extension.
The curve holds the retained preview count while the cell search continues;
only the independently checked certificate produces the repeating patch.
Bounded or unsupported searches retain the preview and report the actual scope
or unsupported-data reason. The other four lanes retain their growth semantics.

Verification: `scripts/test-3d-periodic-worker.mjs` runs the actual comparison
worker with Node's message transport for both lanes, testing pre-certificate
geometry, inconclusive history and scope, unchanged-count certificate snapshots,
progress across pause/resume, and unsupported exact-data previews. The existing
periodic regression suite also passes, including independent eight-tile periodic
and isohedral replay, graph rollback, global scheduler, and cancellation.

## Active placement trace and replay (2026-09-10)

The largest-candidate preview described above has been replaced, at the user's
request, by the actual search stack. Every root/child placement, rejection, and
genuine rollback emits a full state with its cell, action, and failure reason.
This includes dead trial states; they are labeled rejections, never milestones.
Successful recursive unwinding and resource-limit cleanup are not displayed as
failed branches. Returning to zero is an ordinary rollback, not a non-tiling
certificate. The point rules, candidate order, and positive verifiers are unchanged.

Each trace callback suspends the producer until its corresponding message is
consumed. Pause and cancellation therefore retain/control the actual stack.
The live renderer refreshes at up to 20 Hz; every attempted state is retained
for the existing history arrows and a new four-steps-per-second Replay control.
Replay uses recorded search timestamps and does not delay or alter search.
The outlined cell is context for the current recorded attempt. Preparing new
candidate domains remains a separate cell/node progress phase. Trace-generation
cost is included in search time; these timings should not be equated with older
runs that did not retain every attempt.

The worker regression exercises both lanes' failing roots and checks every
placement/removal against a stack replay. A two-type fixture checks nested
backtracking, rejection of wrong inventory, successful completion without fake
rollback, and cancellation while a trial callback is suspended. The existing
graph/scheduler/independent eight-tile certificate tests continue to pass.
