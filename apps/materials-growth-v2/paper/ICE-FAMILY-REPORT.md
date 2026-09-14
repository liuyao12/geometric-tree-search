# Ice-family preliminary report — 14 September 2026

Eight synthetic ice configurations (four Ih and four Ic) provide a first
family-level structural control. They were generated with GenIce2 2.2.13.3 and
TIP3P geometry. Temperature and pressure are unknown, not an asserted shared
equilibrium condition. Generator chemistry is not supplied to the learner:
only atom positions, species and periodic cells; molecule ordering is shuffled.
See [GenIce](https://github.com/genice-dev/GenIce2) and the downloadable provenance.

Geometry-derived components recover the three-atom molecular units, but these
alone do not connect the material. A training-selected inter-component adjacency
gives six-site union supports with shared weight 1/4 and exact filling. Their
six-type training dictionary covers all held-out selected supports within 0.05 A.

Composing pairs of these supports produces nine-site motifs with contributions
1/4 on endpoint components and 1/2 on the shared component. The frozen training
dictionary has 79 types (11 singletons), not a claimed minimal set. Matches use
proper rotations and species/weight/block-preserving correspondences; the
algorithm does not exhaust every unrestricted nine-site correspondence.

Initially, a particular grouping misses 13 and 10 motifs on held-out Ih samples.
Enumerating alternative paths and selecting a partition recovers both samples
without adding types, changing weights or inserting test-specific motifs.

| Held-out configuration | Matched alternative paths | Selected motifs | Exactly filled atoms |
| --- | ---: | ---: | ---: |
| Ih c002 | 685/768 | 128 | 384/384 |
| Ih c003 | 688/768 | 128 | 384/384 |
| Ic c006 | 384/384 | 64 | 192/192 |
| Ic c007 | 384/384 | 64 | 192/192 |

Independent verification checks source hashes, frozen dictionary identity,
constituent inventory, exact weighted filling, species and weight roles, proper
rotations and periodic geometric residuals (maximum 0.048711 A). Selection uses
a specialized graph matching feasibility control, **not** base GCTS tree search.

## What marking learning has not achieved

All 711 scalar site variables of the larger dictionary collapse to two equality
classes, exactly H and O. The frozen markings agree on all four recovered test
covers but add no connection constraint beyond species matching. Independent
graph traversal verifies this partition. More motifs did not by themselves
produce more informative scalar markings.

An exploratory vector pilot on the smaller dictionary learned molecular
orientation. Apparent rejections from four channels disappear after joint pose
adjustment within unchanged tolerances. These pilots are not evidence of useful
network-level selectivity, forbidden-connection accuracy or a speed advantage.
The bundle below verifies the larger-dictionary filling/scalar results, not the
smaller vector pilot.

## Reproduce the principal result

Download the files from `ice-evidence/` together. Node.js performs the geometric
and exact integer-quarter checks; the scalar checker needs only Python's standard
library:

```
node verify-ice-composed.mjs coordinates.json selected-supports.json selected-dictionary.json overlap-regular-sweep.json composed-dictionary.json
python verify-ice-composed-markings.py composed-dictionary.json selected-dictionary.json composed-markings.json
```

The published bundle contains explicit witnesses, not all rejected alternative
poses or an independent proof of optimality/completeness of graph matching.
Coordinates are known during matching. This is not blind growth, unknown-structure
reconstruction, physical validation, an independent experimental ensemble or a
Nature-level result. Production growth code is unchanged.

The next necessary gates are informative marking domains/representations,
robust joint pose matching, simultaneous global consistency, and coordinate-blind
reconstruction under the reference scheduler. Ice, boron, SiC and silicon remain
the intended broader family programme; only the experiments stated here are done.
