# Measured GCTS demonstrations

The workbench's default selector is reserved for measured demonstration presets.
The full research catalogue remains available through its separate link, and the
legacy explorer retains its original model. A hard or unresolved tile does not
qualify merely because its search is slow.

## Protocol

Each candidate is measured on seeds 1, 2 and 3 in all four lanes: free-range,
GCTS, RL clusters and GCTS + RL. Every lane starts cold. Markings are synthesized
from unmarked pair-corona checks; no assignments, labels, or patches are supplied
by the preset. Model construction, local learning, graph construction, cluster
work and verification count toward total time. The complete candidate graph,
reference scheduler and base candidate ordering are shared. Lane order rotates
across seeds and runs are sequential. The interactive demonstration runs GCTS
first so its learning and completed patch are visible before waiting for the
long baseline; all lanes still start cold with the same limits.

The selected preset uses the reflected Hat **single slab**, radius 18,
2,054 required points, a 120-second total lane budget, one million search attempts,
and 500 attempts per pair. Both slab caps carry the planar point weights on the
index-3 A₂ sublattice. This is a large planar problem displayed in 3D, not evidence
of a speedup on the non-layered polycube research cases.

Qualification requires an independently verified completed marked window on all
three seeds, and at least a twofold total-time advantage over free-range on every
seed, for GCTS or the combined lane. A free-range timeout supplies only a lower
bound on its completion time, not an exact speedup. Recorded configurations and
all lane results remain visible; this is a curated demonstration, not a claim of
performance across the whole catalogue or every ordering/device.

## Results and selection

Hat is the only included preset. All three free-range runs reached 120 seconds;
cold GCTS completed in 3.45–4.50 seconds, giving a measured lower bound of 26.6×
on every tested seed. GCTS + RL also completed every seed (4.56–15.06 seconds),
but was slower than GCTS alone in this comparison.

Turtle is excluded from the default demonstrations: on seed 3, free-range finished
in 2.58 seconds, versus 5.41 seconds for GCTS and 9.23 seconds for GCTS + RL.
Its strong gains on the other seeds do not satisfy the inclusion rule. It remains
available in the research catalogue. No non-layered polycube is labeled a verified
GCTS speedup case.

[All larger-window measurements](../../apps/3d-lattice-tiler/v2/reference/showcase-summary.json)
and [the complete exploration summaries](../../data/3d-gcts-showcase-exploration-2026-09-21.json)
include unselected cases, failed marked searches, and every measured lane.

## Why the marking support changed

The former one-step exterior support fits all labeled neighboring pairs but can
also constrain pairs whose positive tile supports never touch. Those contacts
are absent from that training catalogue. At radius 8, both reflected Hat and
Turtle exhausted the learned restriction even though free-range tiled the window.
Local classification alone did not establish usable larger growth.

For these presets, learn only at points of the tile's positive support (extent 0).
Then overlapping assigned marks imply overlapping tile support, so every such
capacity-legal pair occurs in the enumerated pair catalogue up to its verified
symmetry action. Individual entries may still be free. The ordinary marking
matcher and the acceptance gate are unchanged. Both tile systems still pass all
41 positive labels and block all negatives: 186 for Hat and 206 for Turtle.
Larger marked windows are then independently verified as a separate check.
This remains a learned restriction, not an infinite-extension theorem.

The research controls retain the exterior-support option, explicit browser-local
saved-marking reuse, and all earlier geometry. Continuing learning preserves the
checkpoint's chosen support. The demonstration comparison never silently reuses a
saved browser marking.

## Reproduce

```sh
node scripts/screen-3d-learned-catalog.mjs \
  --tiles=a2_turtle_prism,a2_hat_prism --radius=18 --mirrors=true \
  --modes=free,gcts,rl,both --seeds=1,2,3 --extent=0 \
  --time-ms=120000 --nodes=1000000 --output=/tmp/gcts-showcase-r18
```

The runner saves full replay artifacts only to the selected local output folder.
The repository contains aggregate measurements and source hashes, never learned
assignments. Each worker has a 1 GiB heap limit and an outer watchdog; a resource
or budget stop remains unknown. Failed marked searches do not prove unmarked
impossibility.

## Validation and limits

The support/window regression learns fresh fields, verifies the complete pair
classification, checks every assigned point belongs to tile support, and
independently replays a radius-8 marked window. Browser checks cover both v2 entry
URLs, measured settings, a fresh radius-18 learned tiling, the corner inset, and
navigation to the full research catalogue. Base search conformance checks cover
incidence, rollback, dead/forced/generation precedence and exact replay.

Small-window exploration is retained alongside the selected results. It shows
why merely increasing the time limit or selecting a difficult-sounding tile did
not demonstrate GCTS: learning overhead dominates the easy windows. No learned
marking is proved necessary, no infinite tiling is certified here, and no legacy
v1 speedup is inferred from v2 measurements.
