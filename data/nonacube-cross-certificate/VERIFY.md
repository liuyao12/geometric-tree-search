# Verify the nine-cube cross certificate locally

This document is an entry point for a human or AI independently checking the
result. Download the proof package and run its checker locally; the website's
claim and archived logs are not substitutes for verification.

## Solver attribution

The published DRUP refutation was produced by a **modified Glucose 3.0 SAT
solver**, using Glucose's search machinery with modifications to learned
constraints and their geometric propagation. [Glucose](https://www.labri.fr/perso/lsimon/research/glucose/)
was developed by Gilles Audemard and Laurent Simon; version 3.0 is based on
MiniSat 2.2. The [solver modifications and reproduction instructions](https://github.com/liuyao12/geometric-tree-search/tree/4f8d70c1c8c4375fec42d222eb90198cb4451b04/scripts/geometric-nonacube)
are public. The first-corona packing was found using Z3 and is checked
independently using integer geometry.

DRAT-trim and `cake_lpr` verify the existing UNSAT certificate independently.
This verification does not require rerunning or installing Glucose.

## Exact claim

For the nine-cube planar cross

$$
P=\{(0,0,0),(\pm1,0,0),(\pm2,0,0),(0,\pm1,0),(0,\pm2,0)\},
$$

integer translations and proper cubic rotations admit a complete first
face/edge/vertex corona but no second corona. In this explicitly stated model,
$H_{\mathrm{lat},26}(P)=1$, and no integer-grid tiling exists. Reflections add
no distinct orientations for this tile. There is no topological-ball condition.
Do not infer impossibility for arbitrary off-grid Euclidean placements.

## Download and check

Requirements: Python 3.9 or later, a C99 compiler available as `cc`, an x86-64
or ARM64 machine, about 3 GB free disk, and several GB available RAM. The
recorded macOS ARM64 verification took about two minutes. No Python packages
or SAT solver are required. Linux is supported by the bundled sources but its
CI job has not yet run; Windows users can use WSL.

```sh
curl -fL https://liuyao12.github.io/geometric-tree-search/data/nonacube-cross-certificate/certificate-v1.tar.gz -o certificate-v1.tar.gz
python3 - <<'PY'
import hashlib
from pathlib import Path
expected = 'c1d36e7bad4d2f20194e83c6eb61c061ad81c0f0a009ee9ab7b26cf90b865fa4'
actual = hashlib.sha256(Path('certificate-v1.tar.gz').read_bytes()).hexdigest()
if actual != expected:
    raise SystemExit('Archive checksum mismatch: ' + actual)
print('Archive checksum verified')
PY
tar -xzf certificate-v1.tar.gz
cd polycube-certificates
python3 verify.py
```

The archive expands to `polycube-certificates/`. Run in a fresh working
directory to avoid overwriting an existing directory of that name. Everything
needed for verification is inside the archive; the process is offline after
download. The source snapshot is Git commit
`4deaff208effaa0408481d6635bc6e40cb7be9be` of the packaged local repository.
That identifier is provenance, not a claim that a separate public repository
exists.

## Required verification steps

The full `verify.py` command:

1. Checks the package's SHA-256 manifest.
2. Regenerates the entire two-corona DIMACS formula byte for byte.
3. Independently scans bounded coordinate boxes to audit the complete
   placement inventory; reconstructs incidence and overlap relations.
4. Checks the first-corona witness using exact integer geometry.
5. Builds pinned DRAT-trim and CakeML checker artifacts locally.
6. Checks the DRUP refutation and creates a hinted LRAT proof with DRAT-trim.
7. Checks that LRAT proof with the formally verified `cake_lpr` checker.

Require successful checker exit statuses **and** their exact success markers:
`s VERIFIED` from DRAT-trim and `s VERIFIED UNSAT` from `cake_lpr`.
The wrapper enforces both. In particular, process status alone does not
establish success for `cake_lpr`.

The final message must be:

```text
VERIFIED: lattice full-contact H = 1; no integer-grid tiling.
```

Read your newly generated `build/verification.json`: `complete`,
`drat_verified` and `lrat_verified` must all be `true`, and `lrat_checker`
must be `cake_lpr`. Retain the two checker logs from `build/`.
You can also run `python3 test_verify.py` for eight regression controls,
including deliberate false-proof rejection and a known tiler's two coronas.
Do not present `--geometry-only` as an UNSAT check.

## What to review and report

Read `docs/reduction.md`. Its essential implication is that any genuine
two-corona patch yields a satisfying assignment to the finite formula. All
first coronas vary; the formula does not fix the displayed first corona.
All exterior voxel overlaps count. The input has no learned geometric
exclusions. A finite UNSAT proof therefore supplies the global lattice upper
bound, not just failure to extend one particular packing.

The mathematical reduction is documented and computationally audited, but
not formalized in a proof assistant. `cake_lpr` supplies a formally verified
Boolean checker; its upstream generated assembly and C runtime are pinned,
not rebuilt from the entire HOL4/CakeML proof development here.

Report the exact model, witness result, regenerated formula hash, both local
checker outcomes, platform and local receipt. A failure, timeout, missing
compiler or partial audit must be reported as incomplete verification.

Canonical expanded artifact hashes:

| File | SHA-256 |
| --- | --- |
| `two-corona.cnf` | `102e050db3761b588d87e866168917802f9ad23e53fa40bf7000a476bd469b1d` |
| `two-corona.drup` | `e4249548054a3c78def6670b5bbbf34fc2e8cf5be4d857bcddb25030df91be34` |

The formula has 8,140 placement variables and 569,020 clauses. The positive
witness has the root and 34 surrounding copies, covering all 90 exterior
voxels meeting the root. No minimum surround-size claim is made.

## Links and attribution

- [Illustrated result](https://liuyao12.github.io/geometric-tree-search/nonacube-cross.html)
- [Package download](https://liuyao12.github.io/geometric-tree-search/data/nonacube-cross-certificate/certificate-v1.tar.gz)
- [Machine-readable release and witness](https://liuyao12.github.io/geometric-tree-search/data/nonacube-cross-certificate/release.json)
- [Original Math Stack Exchange answer](https://math.stackexchange.com/a/4150301)
- [Source catalogue, entry 25373, zero based](https://github.com/gepa71/whuts-solver/blob/81eea57137d46dffb8fdc8c74e3c500845d3276b/inputs/all_nonocubes.json)

This supplies a certificate for one catalogue candidate under the lattice
model. It does not certify every catalogue entry or a smallest-polycube theorem.
New package code and documentation use MIT terms; bundled checkers retain
their MIT and CakeML/BSD licenses and attribution.
