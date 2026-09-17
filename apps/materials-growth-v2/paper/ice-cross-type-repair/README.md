# Cross-type repair: conditional unmarked coverage reaches 20/20

The frozen learned motif library can fill all twenty calibration configurations when supplied valid prefixes are retained and residual neighborhoods may use other learned types. Eleven cases already passed pose-refitted replay. The reference point search now completes the other nine residual problems; independent source-coordinate replay verifies every selected placement and exact rational t sum.

This is a **conditional unmarked reconstruction result**, not full GCTS learning, single-atom growth or independent held-out validation.

## What changed

Do not restrict a missing occurrence to its old assigned type label. Retain geometrically valid supplied placements and propose other frozen learned motifs at underfilled atom sites. Correspondence proposals preserve opaque species labels and use pair-distance bounds, proper least-squares rotations, and a final 0.15 Å residual check. Anchors, weights and motif prototypes are not retrained.

Seven cases admit residual fillings immediately. One further case has no filling in that frozen residual proposal pool, and another has an overfilled fixed prefix. For these two cases, release every fixed placement touching a defective site (t total not equal to 1), then regenerate the residual pool. Five and eleven fixed placements are released respectively. This is an explicit one-neighborhood repair policy, chosen after the initial failures—not a claim of exhaustive global inference.

| Stage | Calibration configurations with verified unmarked fillings |
| --- | ---: |
| Learned support, old poses | 3/20 |
| Same support, refitted poses | 11/20 |
| Alternative-type residual repair | 18/20 |
| Release neighboring fixed placements in two failed cases | 20/20 |

## Reference search, separately from feasibility diagnostics

A separate mixed-integer diagnostic first establishes that candidate repairs exist. The exported point-search inputs contain only candidate pools and fixed prefixes—no selected diagnostic repairs. The reference `PointSearch` runs unchanged with every atom an active generation-zero obligation, integer capacity 2, all t contributions in integer half-weight units, and no m constraints. It follows global dead/forced checks and earliest-generation branching. Rollback restores the complete fixed-prefix state; graph audits pass.

The seven smaller searches add 1–4 placements each. After neighborhood release, the two searches add 12 and 19 placements. Fixed prefixes contain 63–127 placements in the smaller cases and 90 and 79 in the released cases. They contain substantial knowledge of the configurations. The searches are **not cold-start global reconstructions**. Tiny residual-search times are not a speedup benchmark and exclude learning, registration and independent audits.

## Independent verification and scope

Source replay reconstructs every transformed learned anchor, checks species, proper rotations, positional error, injective periodic matches and exact rational t totals over the entire configuration. Maximum selected residual is below 0.15 Å; no repeated type/ordered-atom correspondence occurs in these witnesses. Corruption controls reject an omitted repair, a duplicate selected candidate and a reflected pose. The union of eleven earlier successful calibration IDs and nine repair IDs is checked to equal the full twenty-case calibration set without duplication.

The candidate generator samples one closest periodic image per residual atom and one pose per template/ordered correspondence, with a 100,000-correspondence / 60-second limit per case. Two-point motifs retain only one tested proper orientation. No cap was reached in these runs, but the proposal process is still not complete continuous-pose enumeration. A failed proposal pool does not prove the material cannot be filled.

The upstream dictionary already saw the calibration configurations, and the initial occurrence proposals originate in the older half-weight pipeline. Marking compatibility, connectedness, independent-condition provenance and growth beyond input positions are not established. Previous tolerant markings still have poor positive retention; they are not silently applied or advertised as responsible for these successes.

## Evidence

- [Seven residual reference searches](local-search.json)
- [Their independent geometry/t replay](local-check.json)
- [Two neighborhood-release reference searches](released-search.json)
- [Their independent geometry/t replay](released-check.json)
- [Registration and separate pool exporter](repair-learned-support-gaps.py)
- [Reference-search runner](search-learned-support-repairs.mjs)
- [Independent verifier](verify-learned-support-gap-repair.py)
- [Corruption controls](test-learned-support-gap-search.py)

Coordinate-bearing pools and poses remain local, identified by hashes. The runner takes `pool kernel output`; the independent checker takes `--search coordinates learned-support pool search-result output`. These source snapshots and receipts are not a self-contained dataset release.
