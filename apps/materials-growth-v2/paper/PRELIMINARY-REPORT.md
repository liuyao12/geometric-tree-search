# Preliminary report: local consistency versus continuation

13 September 2026. Not peer reviewed.

There has been substantial methodological progress, but the main materials
result remains outstanding. A generated 14-atom prefix was extended to a
verified 34-atom finite union. Only 14 atoms have centered supports; 20 new
centers still require support assignments. This is not sustained growth.

The second continuation failed in its declared finite proposal model. Exact
distance checks identify a three-point obstruction involving two newly added
atoms and one inherited atom. All 83,182 donor-site injections fail necessary
distance conditions across 6,912 source neighborhoods. A second verified
34-point alternative retains this same obstruction.

The new lookahead experiment reported exhaustion of its 223-location finite
representative catalog after 92 states and four rejections using one distinct
certificate. It used 41,960 iterator comparisons and 97,092 lookahead work units.
Independent saved-result audits verify source data, historical pose contexts,
admission and local certificates; they do not independently replay the entire
DFS or reconstruct every historical partial state.

The new rule explicitly requires future poses to pass exact source/world pair
distance admission at tau=1e-8 Å. It is an added geometric contract, not an
unproved implication of a floating rotation check. With representative error
epsilon=0.1 Å and a pinned center, necessary radial and neighbor-pair errors are
epsilon+tau and 2epsilon+tau. This is currently a geometric supplement, not yet
a point-marking implementation or a demonstrated GCTS speedup.

All samples used here are development data. The 6,912 neighborhoods come from
32 frames (0–7 and 24–47) of the silicon dataset already cited in the paper;
correlated frames are not independent specimens. No energy, chemistry or
formation-history model is imposed. Geometry alone does not establish physical
realism or the statistical distribution of amorphous structures.

## Reproduce the public geometric checks

With Node.js 24 or later, from this directory:

```
node verify-preliminary-evidence.mjs
```

Use a repository checkout, or download `preliminary-evidence.json`,
`verify-preliminary-evidence.mjs`, and all four modules in `preliminary-checkers/`:

- [Whole-union checker](preliminary-checkers/research-common-representative-witness.mjs)
- [Separation checker](preliminary-checkers/research-verify-representative-separation.mjs)
- [Pair-admission checker](preliminary-checkers/research-exact-pair-distance-admission.mjs)
- [Obstruction checker](preliminary-checkers/research-pair-admitted-two-neighbor-obstruction.mjs)

The script verifies the bundle SHA256, both 34-point unions, their separation,
all 14 indexed source/world pair admissions, and the obstruction across all
donor injections. It does not rerun source-transport authentication, clustering,
the full search, or resource supervision. Those claims have different scopes.
Source-run hashes are included in the bundle; the raw research runs remain
distinct from this curated public evidence package.

## Remaining scientific requirements

Retain the actual parent search and revise support choices rather than repeatedly
freezing an unextendable boundary. Require supports at every previously exposed
atom. Then demonstrate repeated extension at larger scales, independent test
configurations, density/scattering/angular and higher-order structural fidelity,
diversity, and matched baseline comparisons with all costs included.

Reversible parent/child search and budget handling pass independent synthetic
tests. The production depth-two material experiment has not yet run. Neither
medium-range amorphous generation, physical discovery nor superiority to
existing methods is currently established.
