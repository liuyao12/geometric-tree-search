# Shared-family checkpoint — 20 September 2026

This is a frozen preliminary snapshot, not a new end-to-end growth claim.
The source-coordinate corpus is not republished; data licensing is unresolved.
`results.json` contains aggregate results and SHA-256 provenance receipts.

## Distinct experiments, not a funnel

- A three-site geometric core was fitted using 1,600 training frames; 400 author-evaluation frames were excluded from fitting. Both use proper label-preserving rigid fits at a declared 0.15 Å tolerance. No molecular formula was prescribed.
- Connection pilot: first four source frames per phase and author split, 16 training plus 16 evaluation. Shared off-atom interfaces are fitted only on training data. Geometry fitting and connection fitting therefore have different training scopes.
- Training reconstruction: all 16 cases have complete finite contact domains and independent connected-periodic reconstruction checks. There are 1,472 placements, 1,471 forced, one branch and no backtracks. Summed search-only time is 10.33 seconds, excluding substantial preprocessing and verification. It is not an end-to-end runtime or speedup.
- Pose diagnostic: the same frozen pair models connect 5/16 evaluation graphs with fixed poses, and 13/16 when a separate maximum-edge optimization chooses a consistent atom-valid pose per motif. This is not the base tree search or a joint filling certificate.
- Larger-data pair diagnostic: 25 training and 25 evaluation frames per phase. Independent replay verifies 98/100 connected evaluation pair graphs. A different cohort size prevents treating this as a same-target rate comparison. Full-decoration reconstruction is pending.

## The important negative result

For the first pilot evaluation frame, c00400, all 376,832 eligible context/pose candidates and 583,168 raw supports were independently checked. A separate periodic position/mark index reproduces all 559,059 half-weight contacts. Independent candidate-centric pruning agrees with the producer: no candidate survives. These are separately hash-bound checks of the same saved inventory.

This excludes a filling only in the declared finite frozen decoration/pose model and approximate contact rules. It does not prove that ice, another learned library, or the full continuous-pose problem is impossible. All 1,472 full pilot decorations occur in only one training frame. Successful training recovery has not yet become reusable family-level rules.

## Algorithm and inference limits

The compact reconstruction engine recomputes complete finite incidence before global dead-end checks, forced propagation and earliest-generation branching. It has exact rollback, but not incremental incidence updates. Source/product candidate order differs from the historical JavaScript engine. Target atoms and finite motif poses remain supplied. Contact preprocessing already uses learned markings; this is not an unmarked-versus-GCTS control.

Anchor neighborhoods use a declared minimum-point-count partition prior; weights use an exact rational minimum-norm fit with sharing across identical interface roles. The 19 ambiguous training neighborhoods split into valid distinct points rather than being merged indiscriminately. All 3,265 training point sums equal one. Geometry remains approximate. Arbitrary anchor-support discovery and exhaustive continuous rotations remain open.

The [source repository](https://github.com/venkatkapil24/fine-tuning-MLPs-ice-polymorphs) is pinned to `c9a4bb534b35bfc8f467d7388f3056325bd2dd4e`. The [source paper](https://doi.org/10.1039/D4FD00107A) supplies a common sampling protocol, but per-frame conditions and independent trajectories are not verified; the released VIII cell count differs from the paper's description. Source splits are developmental evidence, not an independently prepared benchmark.

Oxalic acid's separately completed larger-budget training cohort has 232 connected reconstructions and eight unresolved cases out of 240. Later ordering controls are excluded from this snapshot. Conditions and independent-trajectory provenance are unverified there too.

The production growth application is unchanged. No Nature-level result, physical mechanism, blind growth or performance advantage is claimed.
