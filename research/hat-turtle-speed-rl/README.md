# Geometry-only fixed-boundary hat and turtle study

The study generates its own training tasks. Unmarked geometric tree search grows
finite patches using the repository's exact hat and turtle outlines. A task cuts
out a connected set of tiles and preserves every exterior tile meeting an edge
of the cut. The search sees the empty cavity as an exact set of triangular atoms
in the \(A_2\) model. The saved original placement list is available for
replay and stays outside the solver inputs. Cavity construction gives a
guaranteed-tileable finite benchmark.

`dataset.py` uses separate source seeds for training and evaluation.
`experiment.py` checks that those sets are disjoint and removes repeated
cavities up to lattice symmetries and translation. It extracts held-out tasks
after writing the frozen policy and cluster bank. Timing repetitions share the
same policy, cavity and search seed. The order of timed lanes is shuffled within
each repetition.

All lanes share the complete primitive placement inventory and the same point
scheduler. The scheduler checks for dead domains before choosing a singleton
or a minimum-degree point. All cavity obligations start at generation zero.
Atoms with identical candidate incidence are collapsed as equivalent columns.
Cluster moves cover the scheduled point, apply a disjoint set of primitive
placements together, and leave the primitive alternatives available.

The bank is mined from independently checked plain-GCTS training solutions.
A template must recur in at least two source lineages. A parent expands into
two disjoint touching children. The bank retains up to twelve templates at
each of the three levels. Training starts from zero weights and uses a
linear-softmax REINFORCE update over the first branch tried at each choice
point. The episode reward compares successful search work and search
wall time with plain GCTS on the same cavity. Incomplete episodes receive a
negative reward scaled by their best viable coverage. Hierarchy-free RL,
pairs-only RL, random hierarchy and largest-first hierarchy are controls.

Successful placements are separately rerasterized from the shape outlines
and checked for full exact occupancy, angle capacity, disjointness and contact
with the fixed collar. The replay shares the exact authoring kernel with
search. A bounded search failure would remain an unsolved case. This model
measures fixed-boundary reconstruction with integer translations and twelve
orientations. Its nested templates are finite arrangements.

## Reproduction

Use Python 3.12 for comparable timing. Pillow is needed for the report diagram.

```sh
python3 dataset.py ./cavity-data --train 20 --test 8 --workers 4
python3 experiment.py ./cavity-data hat ./hat-results.json
python3 experiment.py ./cavity-data turtle ./turtle-results.json
python3 forced.py ./cavity-data ./hat-results.json ./hat-forced.json
python3 forced.py ./cavity-data ./turtle-results.json ./turtle-forced.json
python3 report.py ./hat-results.json ./turtle-results.json ./reader --dataset-seconds 177.808 \
  --forced ./hat-forced.json ./turtle-forced.json
```

Use the generation time from your run as `--dataset-seconds`. The two
experiments should run in sequence for comparable wall times. The raw data
include source patches, cavity footprints, collars and replay witnesses. The
results retain each policy's per-case choices and timings. The bank and
weights are in the adjacent `*.policy.json` files. Wall-time measurements in
the reward can cause independently trained policies to differ.

The follow-up admits a cluster only when it can certify that every child
placement is forced in sequence. Its cavities come from the same held-out
source lineages as the main experiment, with symmetry-equivalent and
previously measured cavities excluded. Both forced variants use the original
frozen bank. The largest-first variant omits policy scores.
