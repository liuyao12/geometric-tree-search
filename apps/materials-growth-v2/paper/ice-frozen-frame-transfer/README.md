# Frozen-library transfer to excluded ice frames

## Cohort fixed before this run

We selected source validation frames 50–54 from each of Ih, II, VI and VIII:
`c00450`–`c00454`, `c00950`–`c00954`, `c01450`–`c01454`, and
`c01950`–`c01954`. These twenty IDs are absent from all 200 configurations
stored in the upstream dictionary, all support-training observations and all
supplied support poses. They also have no exact source-geometry hash duplicate
among the dictionary configurations. Selection used source indices, not search
outcomes; every selected frame is reported.

The independent cohort checker verifies byte identities of the frozen inputs,
the exact source-index selection, unchanged coordinate/metadata records and
exclusion from recorded dictionary and support observations. Corruption
controls reject changed coordinates, a repeated frame and a wrong source index,
even after updating the target-file hash.

This is **frame-disjoint transfer relative to this frozen pipeline**, not
independent-trajectory or condition-matched validation. Temperature/pressure
and trajectory identifiers remain unestablished for all twenty frames. The
full source corpus already existed locally, and this check does not audit all
earlier exploratory experiments or exclude distribution-level leakage.

## Frozen model and reconstruction

The learned support file and interval-marking file are byte-identical to those
used in the previous calibration experiment. No anchor, t-value, m-value,
landmark, channel representation or final positional tolerance is refitted.
The support learner remains conditional on supplied motif types and fitting
poses; it is not unrestricted joint anchor/t/m learning.

The new generator's `external-targets` mode reads separate target coordinates
while retaining and checking the original training-coordinate hash. It skips
the supplied pose list and starts every search without selected placements.
Known target atoms remain inputs to proper-rotation registration. The bounded
proposal procedure finishes without hitting its caps on all twenty frames;
this is not complete enumeration of continuous poses.

| Marking channels | Complete new targets | Saved unmarked covers retained | Attempts | Backtracks | Forced placements |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 20/20 | 20/20 | 3,237 | 1,154 | 20 |
| 1 | 20/20 | 5/20 | 3,243 | 1,137 | 24 |
| 2 | 20/20 | 0/20 | 2,827 | 745 | 27 |
| 4 | 20/20 | 0/20 | 3,029 | 952 | 34 |
| 8 | 20/20 | 0/20 | 2,576 | 480 | 118 |

Every phase has five successes at every channel count. Counters total the
twenty targets; each lane uses the same candidate geometry/order, reference
kernel and 300,000-step / 10-second per-target budget. Markings are learned
hypotheses, not proved redundant constraints. Retaining the ability to fill
these targets does not imply preserving every unmarked cover.

All 5,520 target atoms are independently checked in each lane. The checker
rebuilds each candidate's m-data from the frozen learned values, checks common
closed-interval intersections in exact doubled integers, and independently
replays source coordinates, proper rotations and exact rational t-sums within
the unchanged 0.15 Å positional tolerance. Kernel graph audits and exact
rollback pass. Missing channels, shifted values, altered t-data and a genuine
t-compatible/m-conflicting candidate pair are rejected by controls.

## Interpretation and costs

The earlier success was not confined to the twenty dictionary-seen calibration
frames: a frozen shared library also admits these twenty excluded source
frames. At two or more channels it changes the selected decompositions while
retaining finite reconstructability of each target. This is a positive
frame-transfer result, not proof that its learned connections capture material
structure beyond the target coordinates.

Eight-channel witnesses still have 5–50 shared-atom support components and up
to 25 repeated unordered type/t-support selections. Connected growth, robust
placement identity, learned off-atom marking support and expansion beyond the
sample remain open. Same-condition provenance remains a separate unmet gate.

Proposal generation plus separate feasibility diagnostics took 72.29 seconds.
Channel-search totals were approximately 0.99, 1.09, 1.31 and 1.68 seconds;
they exclude training, parsing, adapter construction and independent checks.
Some runs overlapped. Fewer backtracks are not a controlled wall-clock speedup
or evidence that the learned restrictions are necessary.

## Reproduction evidence

`manifest.json` records frozen source hashes and target metadata;
`cohort-check.json` verifies exclusion. `transfer.json` binds that cohort to
the actual candidate pool and search/check hashes. `summary.json` compares
channels; `search-N.json` and `check-N.json` contain selected IDs and independent
replay. The raw coordinate-bearing candidate pools and source coordinates are
not redistributed here, so these files are not a standalone reproduction
bundle. Source-corpus provenance is described in the earlier report sections.

With the hash-matching source files and fresh output directory:

```sh
python prepare-ice-frozen-targets.py FULL_COORD FULL_PROVENANCE DICTIONARY SUPPORT MARKINGS OUTPUT_DIR
python verify-frozen-frame-cohort.py OUTPUT_DIR/manifest.json OUTPUT_DIR/heldout-coordinates.json COHORT_CHECK
python repair-learned-support-gaps.py TRAIN_COORD SUPPORT POSES POSE_CHECK PROPOSALS external-targets all BASE_POOL OUTPUT_DIR/heldout-coordinates.json
```

Then use the frozen adapter, reference runner and independent marked checker
from `../ice-interval-reconstruction/`, passing the new target coordinate file
to geometry replay. The channel comparison summarizer and transfer binder are
included here. They expect the versioned filenames used in this experiment.
