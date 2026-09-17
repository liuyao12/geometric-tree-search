# Refitting poses after learning support

The support learner moved anchors but previous replay kept rigid poses fitted to the old motifs. This follow-up changes only those rigid poses. Learned support count, positions, t-values, marking values, occurrence identities and the final 0.15 Å positional tolerance remain frozen.

## Procedure

Preserve every already-valid pose exactly. For an invalid pose whose nearest same-label matches initially lie within 0.30 Å, try at most twelve ICP/Kabsch iterations with proper rotations, then bounded local minimax refinement if needed. The wider initialization neighborhood is not the acceptance tolerance. Final matches must be unique and within 0.15 Å. No atom-list correspondence from the old motif is supplied to the fitter.

The algorithm recovers 24 previously invalid local registrations; two remain unmatched. It preserves 9,155 already-valid registrations. Empty-support/unknown types are not repaired or silently supplied from another library. This is a local proposal method, not exhaustive continuous-pose enumeration or a proof that the two remaining fits are impossible.

## Independent replay

All 80 training configurations still pass. Calibration t-filling improves from 3/20 to **11/20**, checked by independent periodic coordinate matching and exact rational t sums. Eight of the nine remaining failed configurations contain at least one type absent from the fitted support library; one of those also has unmatched anchors. The remaining failed configuration has a local geometric mismatch without a missing type. One failed configuration also overfills an atom. Failures are not declared impossible.

The verifier checks the frozen-input hashes, complete occurrence identity set, unchanged type identities, proper rotation matrices, positional tolerance, unique atom matches and rational weights. Corruption tests reject reflections, changed type identities and missing pose records. A separate test confirms that all previously valid poses are unchanged.

## Markings are a separate test

With the same previously learned tolerant markings, independent replay retains:

| Channels | Training retained | Retained among 11 t-valid calibration tilings |
| --- | ---: | ---: |
| 1 | 80/80 | 3/11 |
| 2 | 80/80 | 2/11 |
| 4 | 80/80 | 1/11 |
| 8 | 80/80 | 0/11 |

More channels still harm positive retention in this construction. Neither the improved pose fit nor these marking checks are tree-search reconstructions: the occurrence proposals and type identities remain supplied. The upstream dictionary already saw the calibration frames. No independent-condition provenance, full family generalization, speedup, joint anchor/t/m learning, or growth beyond the sample is established.

## Evidence and commands

- [Independent support replay](support-check.json)
- [Independent marked replay](marking-check.json)
- [Local pose fitter](refit-learned-support-poses.py)
- [Support verifier](verify-learned-ice-point-support.py)
- [Marking verifier](verify-tolerant-support-markings.py)
- [Corruption controls](test-refitted-support-poses.py)

The fitter takes `coordinates dictionary library learned-support output`. The support checker takes `coordinates dictionary library learned-support output poses`; the marking checker takes `coordinates dictionary library learned-support markings output poses`. Coordinate-bearing pose artifacts remain local; receipts identify their hashes. Historical results and code snapshots remain unchanged.
