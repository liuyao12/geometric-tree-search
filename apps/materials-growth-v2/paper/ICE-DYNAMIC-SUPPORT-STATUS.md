# Dynamic complementary support — correctness checkpoint, not a material result

The first implementation rebuilds base legality and then complementary support
to a fixed point after every placement or undo. It is a separately enabled
half-weight constraint filter; it does not replace the reference scheduler.
All surviving endpoint pairs remain distinct candidates in the frontier graph.

At an anchor's incidence-equivalent required atom:

- Total 0: a proposed half needs another live distinct-inventory complement.
- Total 1: the placed half already supplies that complement; base cloud checks
  compare the proposal with the actual active marking.
- Total 2: base occupancy excludes all further incident placements.

Rebuilding from restored base legality ensures that child-specific support
losses are not retained after rollback. Repeated endpoint removals are sound
necessary consequences, not new learned laws. This implementation assumes a
symmetric necessary pair-compatibility predicate (scalar equality or the
guarded cloud predicate supplied by the adapter).

## Evidence

`test-dynamic-factorized-support.mjs` checks 100 models, 5,427 states, 108,540
candidate memberships and 1,170 explicit rollbacks against independently
expanded decorated-candidate fixed-point pruning. Exhaustive enumeration of
312,500 selections finds 409 full fillings; all remain replayable through
dynamic propagation. This is scalar-marking evidence, not material growth.

`test-dynamic-factorized-cloud.mjs` checks permuted-cloud completion, rollback,
a signature false positive, two-sided numerical guards, unknown-not-pruned,
and rejection of unsupported capacity. The existing 150-model base cloud
lockstep suite also still passes with the adapter's default engine.

## Material pilot cost failure

The one-cover pilot was launched using the fully statically filtered model,
`/tmp/gcts-ice-one-factorized-full-support-v1.json`. Process 15480 was still in
root setup at elapsed 01:00, CPU time 1:01.35 and about 1.9 GB RSS; no setup
completion or search-advance output had been emitted. The owned process was
terminated with SIGTERM (exit 143), and no material result was certified.
The output directory `/tmp/gcts-ice-one-dynamic-factorized-search-v1` has no
successful run report. Do not confuse this stopped pilot with budget-unknown
after a completed search setup.

## Next implementation

Construct a complete, hash-bound endpoint-complement index on the static
survivors. Use the coordinate signature only as a conservative range index,
then retain all necessary pair matches. Independently verify completeness of
that graph against brute array queries. Dynamic support must test live indexed
partners, with inventory and opposite-endpoint availability, instead of rescanning
all endpoint choices. Retain the exhaustive domain and rollback tests. Only
after that integration should material pilots be rerun and independently checked.

Family-wide reconstruction, condition-matched provenance and growth beyond the
supplied positions remain unresolved. No speedup or new reconstruction claim.
