# p9-48258: a checked obstruction to integer-grid tiling

**Result (2026-09-21): p9-48258 cannot tile the integer cubic grid by proper
cubic rotations and integer translations.** This removes the planar nine-cube
cross from the lattice aperiodic-monotile shortlist. It does not rule out a
Euclidean tiling using non-grid translations or arbitrary rotations. No true
aperiodic monotile has been established by this experiment.

The discovery followed complete local pair learning: 622 positive pairs and
64 negative pairs, with a conditional free-value marking separating all of them.
The proof below is independent of the numerical labels or the learned field.
It uses four explicit geometric pair obstructions and a finite window.
The [certificate manifest](../../data/p9-48258-grid-obstruction/manifest.json)
links the geometry, frontier conditions, Boolean formulas and proof traces by
SHA-256. No learned m-values are included or imported by the browser lanes.

## Tile and transformations

The prototype's occupied unit cells have lower corners

```
(0,0,2) (0,1,2) (0,2,0) (0,2,1) (0,2,2)
(0,2,3) (0,2,4) (0,3,2) (0,4,2).
```

The 24 proper signed-permutation rotations give three distinct normalized
orientations, lying in the yz, xz and xy planes. Placements translate these
cells by integer vectors. Certificate coordinates use half-unit coordinates:
voxel centers are odd, corners are even, and translations are even vectors.
At each center the tile contributes 8; at each corner it contributes the number
of incident occupied voxels; capacity is 8. Thus center capacity prohibits voxel
overlap, and a full corner requires all eight incident voxels to be covered.

The verifier independently reconstructs this center/corner field and the full
orientation orbit directly from the prototype. It rotates voxel centers, so
negative axes correctly include the reflected interval's lower-corner offset.

## Why the finite contradictions exclude an infinite grid tiling

1. **Every pair in an infinite tiling has a viable one-corona.** Let K be the
   pair's positive point support. Retain every tile of the infinite tiling whose
   support meets K. This is a finite set: there are finitely many orientations,
   anchors and integer alignments. It contains the pair and still completes K.
   At every positive incomplete exterior point, at least one omitted tile of
   the infinite tiling remains a legal additional candidate. Therefore the
   retained patch has viable frontier.
2. **Four relative pairs have no such corona.** For each, the finite candidate
   universe contains every placement covering a voxel incident to a pair corner.
   The formula forces the seeds, fills all those voxels, and forbids overlap
   everywhere, including outside the required region. It also imposes a finite
   selection of necessary frontier-viability conditions. At each selected corner,
   either no adjacent voxel is occupied, all eight are occupied, or at least one
   further tile touching that corner is disjoint from the selected patch. The
   last alternative enumerates all orientations and anchors, including placements
   outside the finite decision pool. All four formulas have checked UNSAT proofs.
   Since these conditions are necessary, no infinite tiling can contain a pair.
3. **Transfer only by exact symmetries.** Rotations, integer translations and
   exchange of the two seeds preserve these obstructions. Independently expanding
   the four representatives gives exactly 192 relative schemas across the three
   root orientations. The verifier requires exact equality with the window's
   exclusion list. No additional learned exclusions are used.
4. **Any infinite grid tiling supplies a rooted window solution.** Globally rotate
   and translate an arbitrary tile to the canonical orientation at translation
   zero. Retain it and all tiles meeting the required 7×7×7 region: lower cell
   corners x = −3…3, y = −1…5, z = −1…5. Every retained tile is in the enumerated
   finite candidate universe. They exactly cover the region without overlap and
   avoid all 192 forbidden pair schemas, because the original infinite tiling
   avoids them.
5. **That window is impossible.** Its CNF has a checked UNSAT proof. This
   contradicts step 4, excluding an infinite tiling in the declared model.

As a control, removing the frontier conditions makes each of the four local
formulas satisfiable; removing the pair exclusions makes the root-window
formula satisfiable. The obstruction depends on extension viability.

The selected frontier corners need not exhaust all possible exterior points:
UNSAT under a subset of necessary conditions is enough. Conversely, the finite
positive coronas used in learning do not assert infinite extension.

## Checked formulas and costs

| Case | Placement variables | Required voxels | Frontier conditions | CNF variables / clauses | RUP additions |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pair 22 | 1,408 | 180 | 48 | 4,497 / 135,073 | 38,663 |
| Pair 24 | 1,394 | 180 | 52 | 4,673 / 136,084 | 28,380 |
| Pair 27 | 1,392 | 180 | 40 | 4,403 / 134,073 | 21,050 |
| Pair 29 | 1,404 | 180 | 56 | 5,105 / 139,662 | 21,441 |
| Rooted window | 2,205 | 343 | 0 | 2,205 / 208,385 | 13,795 |

The window includes 35,808 translated pair-exclusion clauses. Each formula was
constructed directly from voxels, independently of the Z3 point-corona encoding,
and solved with PySAT 1.9.dev15 / Glucose3. Construction plus solving took
0.59–1.29 seconds per case after the necessary frontier conditions were available.
A separate standard-library Python RUP checker verified all additions, taking
25–199 seconds per case including generation. The second checker,
[DRAT-trim](https://github.com/marijnheule/drat-trim) at revision
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`, also verified all five traces. The
bundled formulas were regenerated byte for byte before the second replay;
geometry audit plus regeneration and checking took about 4.1 seconds total in
that replay. The initial direct external-check pass took about 4.4 seconds.
These are single-machine observations, not a controlled speedup benchmark.

Discovery was more expensive: the complete pair catalogue previously cost about
12.1 minutes, followed by marking synthesis and larger-window experiments. The
unmarked rooted window is fillable (an independently replayed 84-tile finite
patch exists), so merely completing that window would miss the obstruction.
The contradiction requires the necessary extension rules. This is a concrete
case where local GCTS learning helped expose a global lattice obstruction; it
is not a claim of a quick cold browser classification or of an aperiodic tile.

## Reproduce

From the repository root, standard-library-only verification is:

```sh
python3 scripts/verify_p9_48258_certificate.py
```

This checks every bundle digest, exact point/voxel correspondence, orientation
closure, pair symmetry expansion, root target, byte-identical CNF regeneration,
and all five RUP traces. Allow several minutes for the Python proof checker.
For a faster, separately implemented proof check, build the pinned DRAT-trim
revision and run:

```sh
python3 scripts/verify_p9_48258_certificate.py --checker=/path/to/drat-trim
```

To regenerate a proof (requires `python-sat==1.9.dev15`):

```sh
python3 scripts/certify_voxel_obstruction.py \
  --input=data/p9-48258-grid-obstruction/pair-22.input.json \
  --frontier-result=data/p9-48258-grid-obstruction/pair-22.frontier.json \
  --output=/tmp/pair-22.json
```

Use the corresponding input/frontier files for pairs 24, 27 and 29. For the
rooted window, use `root-window.input.json` and omit `--frontier-result`.
The generated proof may depend on solver version; the archived proof is checked
directly and does not require installing or trusting that solver.

This is a specialized SAT research control with an explicit infinite-to-finite
argument. It does not use the reference graph scheduler and does not replace
either browser lane with catalogue-specific pruning.
