# Extending hard catalogue tiles through viable-frontier patches

This research follow-up uses the same unmarked point constraints and viable
frontier condition as GCTS learning, with a separate SAT scheduler. It does not
change the browser's reference graph lane. Learned assignments remain outside the
repository. The [aggregate receipt](../../data/3d-viable-frontier-search-2026-09-21.json)
records the bounded searches; [finite witnesses](../../data/3d-viable-frontier-witnesses-2026-09-21.json)
contain geometry and placements, without learned markings.

## Current catalogue progress

The p10-346304 catalogue now has **54 positive, 24 negative and 1,846 unresolved
pairs**, out of 1,924 pairs in 365 symmetry classes. Ten classes have positive
witnesses and four have negative outcomes. All four negative classes now have
independently checked RUP proofs, covering all 24 negative pairs. The provisional 144-value marking, counted across eight orientations,
passes all 54 positives and blocks all 24 negatives. It remains **unaccepted**:
most of the catalogue is unresolved, and no marked growth run has started.

After the first three positive classes, a six-pair pass proposed from class 223's
45-tile witness resolves classes 188 and 197 in 8.62 and 4.07 seconds, adding 12
positive pairs. Four checks reach their ten-second budgets. Their saved necessary
frontier conditions are retained for later continuation. The two new witnesses
contain 41 and 48 tiles. No direct label is inferred from proximity or the ranking.

The next twelve proposals from class 197's witness resolve five further classes:
255, 321, 49, 81 and 82. They add 27 positive pairs (class 255 has three members;
the others have six). Their 38-, 42-, 43-, 43- and 47-tile witnesses pass independent
weighted-point and voxel replay. Oracle calls take 7.80, 4.77, 6.64, 5.47 and
5.22 seconds; classes 255 and 81 also inherit earlier unsuccessful calls and
necessary frontier conditions. Seven checks remain unresolved at ten seconds.
These runs use no phase hints. All twelve results, including the unresolved
checkpoints, are retained. The published receipt now lists 52 oracle calls and
1,624 independently replayed dead-point records, and the geometric witness
bundle contains thirteen cases. None contains learned m-values.

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

### Proofs for the other three negative classes

The original negative classes now also have independent proof bundles:
[class 2](../../data/p10-346304-pair-obstructions/orbit-2/manifest.json),
[class 3](../../data/p10-346304-pair-obstructions/orbit-3/manifest.json), and
[class 8](../../data/p10-346304-pair-obstructions/orbit-8/manifest.json).
Each formula is rebuilt from its exact pair, center/corner model and retained
necessary frontier conditions. Glucose produces an UNSAT trace; DRAT-trim checks
it, extracts the needed lemmas, and checks the resulting additions-only trace
again in RUP-only mode. The generation, trimming and checking costs are in the
aggregate receipt and are separate from the search timings above.

| Class | Retained frontier conditions | CNF variables | CNF clauses | Final checker time |
| --- | ---: | ---: | ---: | ---: |
| 2 | 12 | 5,420 | 986,321 | 0.43 s |
| 3 | 4 | 4,722 | 975,997 | 0.37 s |
| 8 | 32 | 9,331 | 1,142,090 | 0.63 s |

Together with class 182, the four proofs cover all 24 currently negative rooted
pairs. They justify 192 distinct relative-placement schemas under proper cubic
rotations and exchanging the two tiles. They do not classify any unresolved
pair or exclude a tiling of the whole tile. The periodic comparison below still
uses **class 182 alone**; the larger proof set was produced afterward.

Replay each bundle with `scripts/verify_voxel_pair_certificate.py`, substituting
its directory in the `--bundle` argument. The shared verifier reconstructs the
formula and checks the compressed trace without learned assignments.

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


## Complete periodic-quotient controls

The earlier patch-period probe allowed only placements seen in its source patch.
The new `solve_patch_period_quotients.py` uses a patch only to propose **period
lattices**. For each proposed period it includes every allowed orientation at
every translation in the finite quotient. An exact cover then gives an infinite
periodic grid construction. Tiles overlapping their own periodic copies are
excluded. The formula keeps distinct orientation/anchor identities even when
they occupy the same quotient sites; merging those identities can make relative
pair clauses unsound. Global translation symmetry places some anchor at zero,
without fixing its orientation.

Period proposals come from triples of repeated equal-orientation displacement
vectors, deduplicated by integer Hermite normal form and proper rotations. This
is a sampled search, not an exhaustive screen above the catalogue's previous
13-copy HNF boundary. The tested periods have 14–21 tiles per cell.

The second control adds the 48 relative-pair schemas proved impossible by class
182. It rechecks the published RUP proof before use and admits no learned
assignments. A pair related by a nonzero period vector can give a unit exclusion:
selecting that quotient placement would force both forbidden tiles in the lifted
infinite tiling. A separate JS point-group calculation reproduces all 48 schemas.
These clauses are proved necessary in the grid domain; this is a clause-filter
control, not the browser GCTS marking lane.

| Sample and control | Period lattices checked | UNSAT for that lattice | Budget unresolved | Periodic constructions | Quotient calls total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Initial eight-witness proposals, plain | 24 | 7 | 17 | 0 | 101.43 s |
| Same initial proposals, proved pair | 24 | 12 | 12 | 0 | 99.07 s |
| Expanded thirteen-witness proposals, plain | 32 | 7 | 25 | 0 | 143.12 s |
| Same expanded proposals, proved pair | 32 | 7 | 25 | 0 | 143.50 s |

The [plain pilot](../../data/3d-p10-period-pilot-2026-09-21.json),
[pair-filter pilot](../../data/3d-p10-period-pair-pilot-2026-09-21.json), and
[expanded matched run](../../data/3d-p10-period-controls-2026-09-21.json) retain
individual bases, outcomes, actual times, bounds and source hashes. Each call
has a nominal five-second budget, including formula preparation; interrupted
calls can slightly exceed it. The expanded run alternates which control goes
first. Its proof verification and preparation cost another 4.82 seconds; total
wall time is 291.66 seconds. Earlier patch construction, corona learning and
proof generation are additional costs. The pilot's reported run time excludes
proof preparation; its checker-only time is recorded separately. These are
single-pass diagnostics, not a cold GCTS speedup benchmark. A short independent
proof test also overlapped part of the expanded run.

The five extra pilot completions do not persist as an advantage on the new
sample. Both expanded controls finish the same seven lattices. Across both
samples, 56 distinct lattices were attempted and 19 received trusted-solver
UNSAT results. Each result excludes only that period lattice. The individual
periodic UNSAT searches do not have exported proof traces; the independently
checked proof is the redundant pair constraint. No global non-tiling,
aperiodicity, or infinite-extension conclusion follows.

The expanded proposal pool contains 168 lattices from the top 96 of 524 observed
displacement vectors. Thirteen of those appeared in the pilot; 32 new ones were
selected. Untested proposals and other period lattices remain open. Certificates,
when found, include explicit orientation geometry keys and translations; tiny
positive controls pass the separate JavaScript periodic verifier even when the
solver's orientation table is reordered and translated.

Reproduce the expanded comparison after installing `python-sat==1.9.dev15`:

```sh
python3 scripts/benchmark_patch_period_quotients.py \
  --input=data/3d-viable-frontier-witnesses-2026-09-21.json \
  --tile=p10-346304 --output=/tmp/p10-period-controls.json \
  --pair-certificate=data/p10-346304-pair-obstruction \
  --checker=/path/to/drat-trim \
  --skip-report=data/3d-p10-period-pilot-2026-09-21.json \
  --min-copies=14 --max-copies=64 --max-vectors=96 --max-bases=32 \
  --time-ms=5000
python3 scripts/test_patch_period_quotients.py
python3 scripts/audit_patch_period_receipts.py
python3 scripts/test_patch_period_pair_certificate.py \
  --bundle=data/p10-346304-pair-obstruction --checker=/path/to/drat-trim
```

The tests require Node on `PATH` or `GCTS_NODE_BINARY`. They cover 275 integer
basis transformations, fourteen exhaustive tiny covers with and without origin
symmetry, self-overlap, wraparound pair clauses, distinct placement identities,
budget-unknown behavior, independent certificate replay, and damaged-certificate
rejection. The receipt audit reconstructs all proposal identities and complete
placement-pool sizes; it does not re-prove the historical timed UNSAT outcomes.
The pilot source hashes identify the early implementation; its occupancy
deduplication changed none of the tested p10 pools, as the audit confirms.
No learned marking is included in these data or tools.

No infinite construction or true aperiodic monotile has been established.
