# Distinguishing missing connections from difficult search

The reference tree search timed out on three of four pilot problems. That did
not establish that their learned finite models lacked full fillings. A separate
positive-witness feasibility diagnostic now finds full fillings in all four,
including connected support covers when explicitly requested.

## Diagnostic, not a replacement benchmark

Each factorized block has two independent endpoint choices. At each anchor,
the diagnostic collects a verified common-cloud witness for an incident pair
of distinct-inventory blocks. Binary variables select blocks and witnessed
pairs. Constraints enforce every required atom's capacity, inventory and the
agreement between each selected block and its two endpoint pairs. Each positive
solution is lifted back to ordinary decorated candidates, then independently
replayed using the same source clouds and integer t-values.

The optional `--connected` query adds cut constraints when a witness consists
of several positive-support components. Every connected cover must cross each
nontrivial atom partition, so those cuts apply only to the explicitly requested
connected-cover diagnostic. The production base tree search is unchanged.
Unknown solver results or absent pair witnesses do not establish impossibility.

This is a SciPy mixed-integer feasibility oracle, not the GCTS reference search,
an RL learner, or a physics model. Its variable count and branching semantics
must not be used as the reference tree's candidate degrees. No oracle completion
was handed to the tree search or used to claim independent search success.

## Connected witnesses

| Library/frame | Witnessed local block pairs | Catalogue time | Solve time | Connectivity cuts |
| --- | ---: | ---: | ---: | ---: |
| One/train | 2,345 | 1.96 s | 0.21 s | 7 |
| One/dev | 1,872 | 0.42 s | 0.46 s | 31 |
| Multi/train | 2,535 | 3.04 s | 0.11 s | 2 |
| Multi/dev | 1,937 | 0.70 s | 0.37 s | 20 |

Each lifted result has 64 placements, covers all 192 required positions, and
has 64 common marking values. Independent checks verify 128 cloud assignments
per result and exactly one positive-support component. None has the same support
cover as a stored training lift. Catalogue and solver times exclude earlier
static filtering, index compilation, file input/output and independent replay.
Concurrent jobs make these diagnostic times unsuitable for speedup claims.

## What this changes

The current libraries already represent connected complete fillings for these
two registered ice-VIII frames. The developmental search timeout is therefore
not evidence that more training connections are necessary for this particular
finite reconstruction. The bottleneck is finding a coordinated choice through
the very large decorated search domain. The next reference-search experiments
should investigate admissible candidate ordering or verified cluster proposals,
without silently changing graph degrees or injecting a known answer.

This is NOT family-wide reconstruction: only c01500 and c01900 were compiled,
the latter is developmental rather than blind held-out data, allowed poses are
finite registrations to supplied positions, and condition-matched provenance
remains unresolved. The experiments do not generate new atomic positions or
establish negative-connection specificity.

Artifacts: `/tmp/gcts-ice-{one,multi}-existence-oracle-v1/` and independent
`...-existence-check-v1.json`; connected runs `...-connected-oracle-v1/` and
`...-connected-oracle-check-v1.json`. Full lifted coordinates remain local;
public reports provide hashes, result counts, code and verifier scope.
