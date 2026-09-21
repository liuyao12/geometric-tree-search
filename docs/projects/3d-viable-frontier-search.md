# Extending hard catalogue tiles through viable-frontier patches

This research follow-up uses the same unmarked point constraints and viable
frontier condition as GCTS learning, with a separate SAT scheduler. It does not
change the browser's reference graph lane. Learned assignments remain outside the
repository. The [aggregate receipt](../../data/3d-viable-frontier-search-2026-09-21.json)
records the bounded searches; [finite witnesses](../../data/3d-viable-frontier-witnesses-2026-09-21.json)
contain geometry and placements, without learned markings.

## Current catalogue progress

The p10-346304 catalogue now has **27 positive, 24 negative and 1,873 unresolved
pairs**, out of 1,924 pairs in 365 symmetry classes. Five classes have positive
witnesses and four have negative outcomes. One of the negative classes now has
an independently checked proof; the original three retain their trusted-solver
scope. The provisional 96-value marking, counted across eight orientations,
passes all 27 positives and blocks all 24 negatives. It remains **unaccepted**:
most of the catalogue is unresolved, and no marked growth run has started.

After the first three positive classes, a six-pair pass proposed from class 223's
45-tile witness resolves classes 188 and 197 in 8.62 and 4.07 seconds, adding 12
positive pairs. Four checks reach their ten-second budgets. Their saved necessary
frontier conditions are retained for later continuation. The two new witnesses
contain 41 and 48 tiles. No direct label is inferred from proximity or the ranking.

## A stronger finite-window check

A filled point window can still leave dead points outside its target. The new
`solve_voxel_frontier_window.py` control also requires every exposed point to
have at least one capacity-legal candidate, including candidates extending
outside the finite placement pool. The center-and-corner reduction turns the
finite target into an exact voxel cover. Each failed outer point adds its exact
necessary availability condition to the retained SAT solver.

The condition is necessary for extension: from an infinite grid tiling, select
its tiles covering the finite target and its fixed seeds. Any exposed point
retains an omitted legal contributing tile. Thus an UNSAT proof could exclude
extension in the declared grid domain. A finite positive witness, however, does
not prove arbitrarily large or infinite extension.

Independent weighted-point and voxel replay verifies these completions:

| Tile and target | Tiles | Required point sites | Exposed points | Dead exposed points | Oracle time |
| --- | ---: | ---: | ---: | ---: | ---: |
| p9-42947, rooted five-cube | 34 | 91 | 527 | 0 | 1.13 s |
| p10-346304, rooted five-cube | 31 | 91 | 576 | 0 | 5.76 s |
| p10-346304, full support of one root tile | 32 | 54 | 593 | 0 | 6.23 s |

The five-cubes require 125 voxels after completing target corners. The root
corona requires 108 voxels. These targets differ: the five-cube does not fully
saturate the p10 root's whole support. The single-root corona does.

The p9 seven-cube remained unresolved after a 30-second run and a 60-second
continuation, which retained the earlier 64 frontier conditions and reached 120.
Its last patch fills the core but has 19 dead frontier points. It is **not** a
successful viable-frontier completion. The p10 seven-cube also remained
unresolved in its 30-second control.

## Patches propose samples; full coronas supply labels

Neither five-cube contains an adjacent pair whose entire point support is full.
The p10 root corona fully saturates only the root. None can directly provide a
positive pair label. Instead, the proposal runner ranks observed unresolved
pairs by the number of still-unfilled core points, then runs a full pair-corona
check. Every positive witness and symmetry transport is independently replayed.

The first eight pairs proposed by the p10 five-cube remained unresolved at five
seconds each. Repeating them with the patch's placements as preferred SAT truth
values also left all eight unresolved. These are reversible preferences, not
additional clauses, assumptions, fixed tiles, or labels.

The full single-root corona provides better proposals. Three of its first four
pair checks resolve positively: classes 1, 43 and 223, covering 15 catalogue
pairs. Their witnesses contain 36, 35 and 45 tiles respectively, with complete
pair cores and viable frontiers. Class 1 retains a prior unsuccessful attempt's
24 necessary frontier conditions; the other two start without such conditions.

Matched controls using the same ten-second budgets and inherited conditions
also finish without phase hints:

| Pair class | With patch preferences | Without preferences |
| --- | ---: | ---: |
| 1 | 4.93 s | 4.90 s |
| 43 | 6.83 s | 6.73 s |
| 223 | 6.11 s | 5.34 s |

This supplies no evidence that preferred SAT phases accelerate these checks.
The useful change is obtaining and checking more informative pair proposals,
with larger budgets where needed. Proposal generation, prior attempts, patch
construction and proof checking are additional costs; these timings are not a
cold GCTS speedup benchmark.

## A checked p10 pair exclusion

Continuing class 182, from the five-cube proposals, proves that it cannot complete
its one-corona with a viable frontier. The continuation takes 10.95 seconds after
its 5.01-second hinted attempt. It excludes six rooted catalogue pairs, or 48
relative placement schemas after proper rotations and tile exchange.

The proof is [published separately](../../data/p10-346304-pair-obstruction/manifest.json).
The checker independently reconstructs the eight proper-rotation orientations,
center/corner weights, nonoverlapping seed pair and finite CNF. It then verifies
the RUP trace using DRAT-trim, without search hints or learned markings. The
formula has 11,450 variables and 1,103,168 clauses, including 99 necessary frontier
conditions. The published trace has 69,520 additions; deletions were removed and
the resulting trace rechecked in RUP-only mode. External checking took about
4.2 seconds. The original slow Python-checker attempt hit its 120-second wrapper
limit, so this report makes no claim that that checker completed.

If this relative pair occurred in an infinite grid tiling, its covering tiles
would give a viable finite corona, contradicting the certificate. The exclusion
is therefore necessary in that grid domain. It is not a non-tiling proof for the
whole tile, an unrestricted Euclidean statement, or an aperiodicity result.
It also shows why occurrence inside a viable finite window alone must not be
turned into a positive pair label.

## Encoding controls and verification

The optional sequential at-most-one encoding reduces the p9 seven-cube formula
from about 1.39 million clauses to about 175 thousand in the recorded runs, but
does not finish its 30-second check. A CaDiCaL control also remains unresolved.
The p10 class-102 sequential and CaDiCaL checks remain unresolved at ten seconds.
Smaller formulas and alternate solvers have not established a speedup here.
The default pairwise encoding is preserved, and all five earlier p9-48258 proofs
still regenerate and pass DRAT-trim verification.

Glucose uses an interruptible time budget. CaDiCaL is polled between bounded
conflict chunks because its installed PySAT adapter has no asynchronous
interrupt; actual elapsed time is reported. Limits always remain unknown.

Reproduce the positive witness replay and the new pair proof:

```sh
node scripts/verify-3d-frontier-witnesses.mjs
python3 scripts/verify_voxel_pair_certificate.py \
  --bundle=data/p10-346304-pair-obstruction \
  --checker=/path/to/drat-trim
```

The proof verifier requires Python's standard library and a separately built
DRAT-trim executable. The search tools additionally use `python-sat==1.9.dev15`.
Tests cover independent point/frontier replay, outside-pool frontier candidates,
fixed seeds, exact pair/window equivalence, 1,022 exhaustive Boolean projections
of the two nonoverlap encodings, both solver backends, reversible contradictory
phase hints, bounded unknown outcomes, proposal transports, empty proposal
reports, and imported unattempted pair classes.

No infinite construction or true aperiodic monotile has been established.
