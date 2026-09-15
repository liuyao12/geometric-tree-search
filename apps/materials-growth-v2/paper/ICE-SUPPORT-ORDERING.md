# Candidate ordering without changing the GCTS frontier

The support-rich policy ranks each endpoint by its static conservative partner
count. Within a geometric block, higher-count endpoint choices come first. A
block is ranked by the smaller of its two best endpoint counts; ties use the
original index. The score uses only the existing hash-bound complement index,
not a training selection, feasibility-oracle witness or material label.

This is candidate ordering only. The global dead/forced/earliest-generation
scheduler, point totals, generations, legality, full decorated candidate degrees,
dynamic support pruning and rollback are unchanged. The iterator snapshots its
parent's incidence so that completing and recreating a point in a child cannot
lose parent alternatives. It enumerates every parent candidate exactly once.

## Checks

The ordered version matches independent explicit candidate domains over 6,157
tiny states and 123,140 memberships, including 1,170 state rollbacks and 273
iterator rollback checks. All 409 full solutions among 312,500 selections remain
replayable. Completed/exhausted DFS outcomes agree with exhaustive enumeration.
These are scalar controls; actual cloud states are independently checked below.

## Four fixed-policy pilots

| Library/frame | Search seconds | Final placements | Result |
| --- | ---: | ---: | --- |
| One/train | 30.05 | 26 | budget-unknown |
| One/dev | 30.05 | 24 | budget-unknown |
| Multi/train | 30.04 | 31 | budget-unknown |
| Multi/dev | 23.99 | 64 | complete finite filling |

The completed developmental c01900 frame has all 192 required positions filled,
128 independently verified cloud assignments, 64 common values and THREE
positive-support components. It took 115 advances, 114 attempted placements,
64 branches and 50 backtracks. No forced placements occurred. Setup took 2.56
seconds, separately from static filtering, indexing, file I/O and verification.
Jobs ran concurrently; no end-to-end speedup claim is made.

All final states and root rollbacks pass their respective checks. The result
was found by the reference-scheduled dynamic search, not the mixed-integer
existence oracle. However, it is developmental, finite and registered to known
positions—not blind held-out growth or connected reconstruction. The policy is
not uniformly better: the previously completed one-cover training case now
times out. Report all four outcomes, not only the successful one.

Artifacts: `/tmp/gcts-ice-{one,multi}-support-ordered-search-v1/` and
`...-support-ordered-check-v1.json`. This supplies a tested ranking interface for
further experiments; it is a heuristic, not a newly trained marking model.
Family-wide reconstruction and verified same-condition provenance remain open.
