# Ice reconstruction without supplied placements

## Result and scope

The unchanged reference `PointSearch` reconstructs all 20 calibration targets
(5,520 atoms total) from empty placement states, using the same frozen learned
support library. These are finite, unmarked target reconstructions, not growth
beyond the known atoms and not a learned-marking result.

| Family | Configuration IDs | Atoms each | Verified complete | Candidates | Attempts | Shared-atom support components |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Ih | c00020–c00024 | 384 | 5/5 | 2,481–2,504 | 222–366 | 24–38 |
| II | c00520–c00524 | 288 | 5/5 | 2,602–2,874 | 96–115 | 9–14 |
| VI | c01020–c01024 | 240 | 5/5 | 1,928–2,048 | 80–81 | 3–7 |
| VIII | c01520–c01524 | 192 | 5/5 | 2,970–3,961 | 80–116 | 20–52 |

Each family uses five calibration frames, not five independent trajectories.
The upstream motif dictionary saw these frames. Identical-condition and
independent-trajectory admission remain unestablished.

## What was removed

In `no-fixed` mode the proposal generator skips the supplied pose list entirely.
No selected occurrence, fixed prefix, or separate MILP selection enters the
search input. Pose/check files are still read for source hashes and frame
selection. The frozen motif types, learned anchor coordinates and t-values
remain supplied from training. Target atom coordinates and opaque element
labels remain available for registration; no chemistry is encoded.

For every learned type and species-compatible target origin, correspondence
proposals use pair-distance bounds and a proper rigid fit, with final maximum
anchor error at most 0.15 Å. Caching periodic local clouds and applying the
existing origin-distance bound before recursion let this bounded pass finish
for all twenty frames. A small untruncated regression retained all 20 proposals
and 127 fixed placements by type, ordered correspondence and t-weight keys.
This is not a proof of continuous registration completeness: one closest
periodic image and one least-squares pose per ordered correspondence are used;
two-anchor supports retain only one sampled proper orientation.

## Search and independent checks

The finite candidate pool is declared as the search universe. All target atoms
are active roots at generation zero, capacity is two integer units, and each
candidate contributes its frozen learned half/unit weights. The master order
is global dead ends, global forced moves, then earliest generation. No m-data,
new pruning rule, or learned ordering policy is added. Graph audit and exact
rollback to the empty state pass for every run.

The independent checker replays source coordinates with periodic lookup,
checks proper rotations and unique species-preserving matches, and verifies
exact rational t-sums. All 5,520 atom targets have sum one. No duplicate
type/ordered-correspondence selections occur. Omitted placements, duplicate
selections and reflected poses are rejected in corruption controls.

A stricter diagnostic ignores the ordering of anchors and groups selected
poses by motif type and mapped atom/t-support. It finds 1–8 repeated selections
in the five Ih cases, 0–1 in II, zero in VI, and 8–44 in VIII. These are distinct
rigid-pose candidates under the declared inventory, not identical selected IDs;
they can nevertheless fill the same sampled support through different anchor
permutations. The sum-one result therefore does not establish distinct useful
connections. Symmetry-aware placement identity must be resolved before calling
these witnesses generative growth. This diagnostic does not justify blindly
merging poses that may act differently on future extended markings.

The checker also now verifies incomplete saved states instead of silently
skipping them: deleting a placement from a legal incomplete state remains an
incomplete result; falsely claiming completion is rejected. These checks do
not independently certify every scheduler transition.

## Costs and the failed precursor

The twenty-case run spent 73.09 seconds in proposal generation plus the
separate feasibility diagnostics, and 0.79 seconds in reference search and its
in-loop audits. Parsing, support training, output, and independent replay are
outside these timings. Each search had a 300,000-step / 10-second limit.
These are one-run diagnostic timings, not a speedup comparison.

An earlier truncated Ih pool had 1,173 candidates. Search remained unknown
after 100,000 attempts and again after 50 seconds (2,489,116 attempts), despite
an independently verified MILP witness. Its final state filled 369 atoms,
partially filled six and left nine untouched. The completed proposal pass
produced 2,504 candidates; reference search then completed in 244 attempts.
Both the candidate universe and order changed, so this is a proposal-sensitivity
observation, not evidence of learned-marking acceleration.

## What this does not establish

- Joint unrestricted learning of anchor count, positions, t and m: the current
  support learner still uses finite atom-derived proposals and supplied types
  and training poses; useful off-atom marking support is not yet learned.
- Correct connection discrimination: no m-values are present in this lane.
- Connected growth: selected covers have 3–52 shared-atom support components.
  These are graph components of tile supports, not chemical bonds.
- Generalization to new conditions, unseen trajectories or unseen phases.
- Single-atom initialization or expansion beyond a supplied target.

## Artifacts and reproduction

`summary.json` links source, candidate-pool, generator, kernel, search and
independent-check hashes. `search.json` records selections and counters;
`check.json` records independent geometry/filling replay. `precursor-search.json`
and `precursor-check.json` retain the failed smaller-pool result. Raw coordinate-
bearing libraries and candidate pools are not redistributed here, so these
receipts are not a standalone reproduction bundle. Source-corpus provenance is
documented in the earlier ice sections of the report.

With the hash-matching local inputs and Python NumPy/SciPy environment:

```sh
python repair-learned-support-gaps.py COORD SUPPORT POSES POSE_CHECK proposals.json no-fixed all pool.json
node search-learned-support-repairs.mjs pool.json KERNEL search.json 300000 10000
python verify-learned-support-gap-repair.py --search COORD SUPPORT pool.json search.json check.json
python test-learned-support-gap-search.py COORD SUPPORT pool.json search.json
node summarize-no-prefix-family.mjs proposals.json pool.json search.json check.json summary.json
```

All outputs are exclusive-create. Preserve historical inputs and use fresh
paths when repeating a run.
