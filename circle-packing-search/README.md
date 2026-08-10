# Corner-generated circle packing tree search

This subproject searches for packings in the unit disk using circles whose
radii have integer bends

\[
\{b:b\in S\},\qquad r=1/b,\qquad S\subset\mathbb Z,\quad b\ge 2.
\]

The target condition is:

- every bend in `S` is used at least once; and
- every small circle is tangent to at least three other boundary components,
  where the unit-circle boundary counts as one component; and
- those contact directions are not contained in a closed semicircle. Equivalently,
  the largest angular gap between consecutive contacts is strictly less than
  180 degrees, so the circle is locally held when its neighbors are fixed.

The search is deliberately restricted to **corner-generated packings**.  It is
a constructive search, not yet a proof procedure for all possible packings.

## Search state

The outer boundary is support `-1`.  A corner is an oriented pair of tangent
supports `(a, b)`.  Its orientation selects the left-hand one of the two
possible sides of the contact.  For every allowed radius, the solver intersects
the two corresponding offset circles and proposes the center on that side.

A proposal is accepted only if the new closed disk lies in the unit disk and
its interior is disjoint from every existing disk.  All tangencies created by
an accepted placement are recorded, not just the two used to construct it.
Consequently a successful state has a directly checkable contact-graph
certificate.

The initial disk is tangent to the unit boundary at angle zero. States are
canonicalized under every rotation and reflection of the unit disk, and child
states with the same canonical key are generated only once. This removes the
mirror choice for the second circle and symmetric corner choices later in the
search.

The implementation does not maintain a literal circular-arc polygon.  The
oriented tangent-pair frontier is an equivalent local representation for the
move rule: a geometrically legal disk on either side of a contact belongs to a
component of the remaining region.  This also avoids special cases when a new
circle makes three or more contacts at once.

## Run

Open the browser app at [`apps/circle-packing-search/`](../apps/circle-packing-search/)
through the repository's static server, or use the Python reference CLI below.
The browser implementation shares the same move grammar and adds pausable,
single-step tree search with a live contact-graph drawing.
It includes every positive numerical witness found by an iterative sweep of
the nonempty bend subsets of `{2,3,4,5,6}` through an eight-circle horizon:
`{3}`, `{2,3}`, `{2,4}`, `{2,3,4}`, `{2,3,6}`, `{2,3,4,6}`, and
`{2,3,5,6}`. Selecting one displays it immediately without rerunning the
search. This is a catalog of verified positive cases, not a proof that every
omitted set is impossible; several larger negative searches reached the node
limit. The `{3,4,5,6}` input remains a search preset, but its former
seven-circle witness does not satisfy the stricter local-holding condition.

A second headless sweep tests three extensible packing families beyond bend 6:

```bash
node scripts/scan-circle-packing-families.mjs \
  --min-bend=7 --max-bend=20 --max-circles=8 --node-limit=100000
```

That sweep contributed the saved positive cases `{2,4,7}`, `{2,3,6,11}`,
`{2,3,6,14}`, `{2,3,15}`, `{2,3,6,15}`, and `{2,4,18}`.

From the repository root:

```bash
python3 scripts/run_circle_packing_search.py 3 --max-circles 7
python3 scripts/run_circle_packing_search.py 3 4 --max-circles 12 \
  --node-limit 500000 --output runs/circle-packing-3-4.json
```

The program exits with status 0 when it finds a certified packing, 1 when the
bounded search is exhausted, and 2 when a node limit interrupts the search.
The area bound gives at most `(max S)^2` circles, but that bound is usually far
too large for a first experiment, so `--max-circles` is an explicit practical
search horizon.

## Current scope

- Floating-point predicates are used with a configurable tolerance.  Output is
  therefore a numerical certificate, not an exact proof.
- Only contact-connected configurations generated from the boundary seed are
  explored.
- The search is complete only within its stated move grammar and circle-count
  horizon.
- State canonicalization removes insertion-order duplicates after fixing the
  seed, but does not yet quotient reflection or more subtle contact-graph
  symmetries.
