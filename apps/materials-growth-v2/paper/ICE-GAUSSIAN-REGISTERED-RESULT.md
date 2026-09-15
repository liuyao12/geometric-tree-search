# Removing the supplied cover exposes the geometric search bottleneck

The four earlier Gaussian-marking controls were conditioned on supplied
geometric decompositions. This next control removes that selected cover for
developmental ice VI, c01400. It includes all assigned-base registrations having
fitting decorations: 229 geometry inventories and 13,612 coupled decorated
candidates, out of 235 proposed registrations. Six unsupported registrations are
explicitly recorded. All 240 atomic targets remain active, including atoms not
touched by current placements. Neither search is given a selected cover.

This is still a finite registered pool on known atom positions. It is not
complete continuous-pose enumeration, and missing registrations are not proof
that their geometry is impossible. Radius 0.6 remains developmental rather than
independently calibrated; half weights remain inherited rather than learned.

## A sound extension of the marking adapter

The old adapter required at most two candidate geometry inventories per marking
anchor. That was unnecessarily restrictive: many alternatives can coexist in
the pool even though at most two can be selected. The revised adapter checks
either the inventory bound or a shared positive t-support point at which every
candidate contributes more than one third of capacity. Three selected candidates
would exceed integer capacity, so at most two fields can be active. Consequently
their Hilbert-ball midpoint remains a valid common-value witness when their
distance is at most twice the radius. This is a structural capacity certificate,
not an empirical assumption or a chemistry rule.

Tests enumerate 160 subsets across integer capacities, checking 60 feasible
states; unsupported three-assignment models and duplicate marks are rejected.
The earlier analytic marking-only/dead-end/backtracking/rollback control still
passes. These are initial tests, not a complete general conformance suite.

## Search results

| Lane | Search seconds | Attempts | Backtracks | Selected placements | Fully filled atoms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Unmarked | 30.014 | 1,899 | 1,855 | 44 | 117 / 240 |
| Gaussian-marked | 30.010 | 1,740 | 1,696 | 44 | 117 / 240 |

Both results are **budget-unknown**, not impossible. Each final state also has
30 half-filled and 93 untouched atom sites, in six selected support components.
Independent replay checks fitting membership, proper rotations, periodic atom
errors, integer t totals, inventory, field comparisons and support connectivity.
Maximum checked atom error is 0.1489893 Å. Both final states satisfy the field
condition, with maximum pair distance 1.13814 below 1.2. Root rollback checks pass.

The point kernel retains global dead-end checks, global forced moves and
earliest-generation branching. The finite target has all atom points activated
as roots. The marking adapter refreshes the complete dependency graph, including
mark-only points and inventory. A 30-second cooperative budget can overrun by
one atomic update. Setup, export and final audit are outside displayed search
time; this is not an end-to-end or statistically repeated speed comparison.

## Does an unmarked filling exist in this pool?

After both searches terminated, a separate mixed-integer feasibility diagnostic
found an 80-placement unmarked filling in 0.038 seconds of solver time. Direct
replay against the original dictionary, independently of that matrix assembly,
confirms every one of the 240 atoms receives exactly two half contributions.
This answer was not fed into either search. It certifies an unmarked finite
filling only: no Gaussian marking assignment or connectedness claim is attached
to that separate witness. Its timing excludes input parsing and is not a fair
end-to-end comparison with the decorated tree-search model.

## Interpretation

There is an unmarked finite solution, yet the present decorated reference
search does not find one within this budget. Markings do not improve completion
here. The next work should inspect repeated geometric search states across
decoration variants and add sound support reasoning or useful learned marking
constraints, without replacing the prescribed scheduler or treating sampled
candidate absence as impossibility. The full objective remains open: learned
anchors/t, selective connections, reconstruction across material families,
complete continuous proposals, growth beyond the input and verified
same-condition provenance.

Public artifacts include the two search results, independent selected-state
replay, separate unmarked feasibility result, and versioned adapter/runner
sources under `ice-registered-search/`. The large generated model is not bundled.
Earlier fixed-cover source files and results retain their original versions.
