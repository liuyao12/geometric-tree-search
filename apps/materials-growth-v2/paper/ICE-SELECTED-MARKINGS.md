# Ice markings: learn from tilings, not a union of competing candidates

14 September 2026. Follow-up to ICE-THERMAL-OVERLAP.md; same exploratory pilot,
frozen geometric dictionary and uniform t=1/2 hypothesis. No production-kernel change.

## Training semantics

The earlier scalar precheck required agreement between every candidate occurrence
meeting an atom, although not all those occurrences could coexist in a weighted
tiling. That is a deliberately strong all-occurrences diagnostic, not the intended
general inverse-tiling training target. Here equality edges are generated only
within selected, independently verified training tilings. Each alternative tiling
contributes its own equations; occurrences from different tilings are not put into
one simultaneous assembly.

Unobserved site variables remain **unassigned**, not distinct negative labels and
not assigned zero. The reference harness and independent checker now explicitly
skip missing assignments. These scalar marks transform trivially under proper
rotation; their support remains the template's atomic sites. This experiment does
not yet learn a new marking domain, geometric anchors or unrestricted t-values.

## Two training-cover controls

The first witness set is the earlier connected MILP selection. A second set is
obtained by reversing candidate order without using validation outcomes to select
the order. Both sets contain verified connected covers of all 100 training frames.
No new training configurations or geometric types are added. Equality components
are fitted first to one set, then to both sets.

| Marking training | Assigned classes | Unassigned sites | Conflicts in original 100 validation covers | Validation covers with conflicts |
| --- | --- | --- | --- | --- |
| One selected witness per training configuration | 11 | 486 | 18 points | 6 |
| Two selected witnesses per training configuration | 8 | 282 | 3 points | 1 |

For one witness set, class sizes are 1,064, 532 and nine classes of two variables.
For two witness sets they are 1,204, 602 and six classes of two variables. Thus
the additional labels are tiny equality components, not established macroscopic
order parameters or stable phase distinctions. Counts alone do not demonstrate
useful GCTS information. Additional training assignments can also constrain sites
that were previously missing, so these models are not simply globally ordered
from stronger to weaker restrictions.

Conflicts with a particular validation cover do not prove that the configuration
has no marked reconstruction. We added explicit pairwise marking exclusions to
the connected-selection control and reran it for each learned model. All 200
training/validation configurations still have independently verified connected
positive covers under each model. This proves existence in those finite pools,
not preservation of every unmarked solution or transfer to unseen trajectories.

## Reference-search comparison

The reference search receives the full registered candidate pools, not the selected
answers. Both learned variants, and their unmarked controls, finish 97 of 100
validation configurations, with only eight connected covers per lane. Three Ih
cases remain budget-unknown. Training on one witness set increases the aggregate
marked backtrack count; training on two sets leaves the aggregate backtrack count
unchanged and adds one branch. Neither experiment demonstrates useful acceleration.
Concurrent diagnostic jobs and these short runs are not a controlled wall-time study.

These are learned restrictions, not proved redundant pruning rules. A missing
observed connection is not automatically a negative example. A further learned
distinction is not valuable unless it transfers and improves the same verified
search task. This pilot has now been inspected during method development; it is
not a fresh confirmatory holdout. Trajectory and condition-provenance caveats remain.

## Verification and reproduction

Independent NetworkX equality graphs reproduce maximal classes and missing-site
domains. Independent point-state checks verify the marked selected and reference
solutions. The selector passes 30 exhaustive unmarked and 30 conflict-constrained
five-vertex tests, plus an odd-degree graph with a single bridge.

Starting from the previous pilot and dictionary artifacts:

```
python ice-selected-scalar.py DICTIONARY FIRST_SELECTION MARKS MARKED_DICTIONARY
python ice-thermal-selection.py COVER DICTIONARY 2 SECOND_SELECTION unmarked reverse
python ice-selected-scalar.py DICTIONARY FIRST_SELECTION ENSEMBLE_MARKS ENSEMBLE_DICTIONARY SECOND_SELECTION
python verify-ice-selected-scalar.py DICTIONARY ENSEMBLE_MARKS PROVENANCE MARK_CHECK FIRST_SELECTION SECOND_SELECTION
python ice-thermal-selection.py COVER ENSEMBLE_DICTIONARY 2 MARKED_SELECTION marked
python verify-ice-thermal-selection.py ENSEMBLE_DICTIONARY MARKED_SELECTION PROVENANCE SELECTION_CHECK
node ice-thermal-reference.mjs ENSEMBLE_DICTIONARY ../kernel.mjs REFERENCE_RESULTS
python verify-ice-thermal-reference.py ENSEMBLE_DICTIONARY REFERENCE_RESULTS PROVENANCE REFERENCE_CHECK
python test-ice-thermal-selection.py
```

The corrected training interface can now accept multiple separate occurrence
witnesses per configuration. The central unfinished problem remains joint discovery
of reusable weighted motifs and sufficiently informative geometric marking domains,
followed by filling-driven reconstruction beyond a supplied coordinate pool.
