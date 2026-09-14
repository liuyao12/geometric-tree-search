# Boron corpus correction and condition audit

14 September 2026. This corrects an omission in our earlier source review.

The 2017 [Erratum](https://doi.org/10.1103/PhysRevLett.118.159902) withdraws the
original τ ground-state assignment. It identifies inconsistent pseudopotentials
in the original energy comparisons and reports ten τ-B106 occupancy arrangements
recalculated with PBE and the newer pseudopotential. This is separate from the
[Reply](https://doi.org/10.1103/PhysRevLett.118.089602) attached to the original
Caltech record. Table I and reference 8 identify the additional coordinate set.

The independent [Comment](https://doi.org/10.1103/PhysRevLett.118.159601)
compared calculations on the supplied structures using two codes and two VASP
pseudopotentials; its energy comparisons exposed the inconsistency. Neither
these energy results nor the correction are GCTS training rules.

## What is actually in our corpus?

| Entry | Coordinates in hand | Training/search status | Condition-matched status |
| --- | --- | --- | --- |
| Original six CIFs | Six source hashes rechecked | Previously reported geometry and finite-model tests | Not established |
| Correction's S-1 through S-10 | Not acquired | Not tested | Not admitted |

Our metadata scan inspects every tag in each original CIF. None contains a
temperature, pressure, computing or refinement tag. Creation dates and VESTA
export labels do not establish simulation conditions. The files therefore do
not supply numerical T/P or a verifiable per-file relaxation protocol. The
literature's energy-calculation discrepancy does not itself prove which
relaxation settings produced each specific coordinate file.

The correction's published Google Drive link and its ordinary download endpoint
redirected to sign-in in this session. We did not acquire the coordinates or
attempt to bypass authentication. Ten explicit pending rows preserve S-1 through
S-10 in the register. They cannot count as successes, failed growth runs, or ten
new distinct crystals: overlaps with our original models remain undetermined.

## Consequences for the experiment

The existing geometric, exact-filling and finite-search witnesses are unchanged.
They concern the stored coordinates, not a thermodynamic stability assertion.
Their proper label remains **cross-structure controls**, not an exhaustive boron
census, equilibrium ensemble or demonstrated same-condition training set.

For the next corpus version, acquire the corrected occupancy-resolved coordinates,
verify explicit atoms and periodic images, establish file-level computational
settings and distinguish numerical condition evidence from inference. Split by
whole configuration before learning. Do not fill missing records with copies,
random coordinate perturbations or guessed occupancy arrangements.

This remains physics- and formation-history-agnostic GCTS: conditions and source
methods are used to define and evaluate a data cohort, not fed to cluster
discovery, marking values, pose proposals or search. A correction in the source
literature is not permission to prescribe boron bonding motifs.

## Reproduce

```
python boron-provenance-audit.py boron-data boron-provenance.json
python test-boron-provenance.py boron-data boron-provenance.json
```

Requires Gemmi and the earlier audited CIF folder. The output includes hashes,
tag inventories and source references, but no raw coordinates. The script
checks local metadata; the cited literature findings and dated link-access
observation are curated evidence, not automatically rediscovered by the script.
