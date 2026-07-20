# Hat marking search

Goal: find a marking on the Hat that accelerates GCTS, ideally recovering
something equivalent to the substitution or Golden Ammann Bar structure rather
than merely adding an arbitrary heuristic.

## Sources used

- Smith, Myers, Kaplan, and Goodman-Strauss describe the Hat as a polykite that
  forces tilings to assemble through a substitution system:
  <https://cs.uwaterloo.ca/~csk/hat/>
- The public H7/H8 substitution demo gives exact symbolic edge steps for the Hat
  continuum. The `Hats` button sets `a = 1`, `b = sqrt(3)`, which converts to
  the A2 integer outline used in `scripts/hat_marking_search.py`:
  <https://cs.uwaterloo.ca/~csk/hat/h7h8.js>
- Akiyama and Araki identify the relevant special linear marking as the Golden
  Ammann Bar. Their paper states that one dashed segment is drawn on the fore
  side and three on the rear side, that these bars continue across tile
  boundaries, and that the fore/rear lengths occur in ratio `1:4`:
  <https://arxiv.org/html/2307.12322v7>

## Current local artifact

Run a single candidate benchmark:

```bash
python3 scripts/hat_marking_search.py \
  --mode benchmark \
  --target-tiles 35 \
  --target-corona 10 \
  --max-steps 70 \
  --node-limit 900 \
  --wall-time-ms 7000 \
  --segments m5-m10 \
  --validate-substitution-levels 2 \
  --substitution-tile H8 \
  --output runs/hat-substitution-m5-m10-target35-strict.json
```

Run a one-segment search with substitution validation as a hard filter:

```bash
python3 scripts/hat_marking_search.py \
  --mode search \
  --target-tiles 20 \
  --target-corona 4 \
  --max-steps 30 \
  --node-limit 220 \
  --wall-time-ms 5000 \
  --max-mark-segments 1 \
  --min-lattice-steps 1 \
  --endpoint-mode all \
  --limit 80 \
  --validate-substitution-levels 2 \
  --substitution-tile H8 \
  --require-substitution-valid \
  --output runs/hat-substitution-filter-lines-level2.json
```

Run a side-dependent GAB-like validation sample:

```bash
python3 scripts/hat_marking_search.py \
  --mode search \
  --search-family gab \
  --gab-ratio \
  --shuffle-candidates \
  --seed 23 \
  --validate-only \
  --min-lattice-steps 1 \
  --endpoint-mode all \
  --limit 1000 \
  --validate-substitution-levels 2 \
  --substitution-tile H8 \
  --require-substitution-valid \
  --output runs/hat-gab-ratio-shuffle1000-level2-validate-only.json
```

Run a signed GAB-like sample with capped benchmarks:

```bash
python3 scripts/hat_marking_search.py \
  --mode search \
  --search-family gab \
  --gab-ratio \
  --rear-sign-variants \
  --shuffle-candidates \
  --seed 101 \
  --target-tiles 35 \
  --target-corona 10 \
  --max-steps 70 \
  --node-limit 900 \
  --wall-time-ms 2000 \
  --min-lattice-steps 1 \
  --endpoint-mode all \
  --limit 200 \
  --max-benchmarks 10 \
  --validate-substitution-levels 3 \
  --substitution-tile H8 \
  --require-substitution-valid \
  --output runs/hat-gab-signed-shuffle200-seed101-level3-target35-capped.json
```

Run a staged 50-to-70 search:

```bash
python3 scripts/hat_marking_search.py \
  --mode staged \
  --search-family gab \
  --gab-ratio \
  --rear-sign-variants \
  --shuffle-candidates \
  --shuffle-seed 307 \
  --seed 23 \
  --target-tiles 50 \
  --target-corona 10 \
  --max-steps 90 \
  --node-limit 1600 \
  --wall-time-ms 9000 \
  --stage2-target-tiles 70 \
  --stage2-target-corona 10 \
  --stage2-max-steps 120 \
  --stage2-node-limit 3500 \
  --stage2-wall-time-ms 18000 \
  --stage1-min-decision-gain 50 \
  --stage1-require-target \
  --min-lattice-steps 1 \
  --endpoint-mode all \
  --limit 120 \
  --max-benchmarks 5 \
  --validate-substitution-levels 3 \
  --substitution-tile H8 \
  --require-substitution-valid \
  --output runs/hat-gab-signed-staged-shuffle307-seed23-50-70.json
```

The script:

- reconstructs the Hat on the A2 lattice;
- computes angle weights in units of `1/12`;
- keeps tile occupancy on the original A2 lattice;
- keeps markings on the doubled A2 lattice, so endpoints can be vertices or
  edge midpoints;
- supports side-dependent markings, with separate fore and rear/reflected
  segment lists;
- can switch marking value convention with `--mark-value-mode`; `reflection`
  keeps the Turtle-style sign flip, while `constant` and `presence` test
  unsigned/bar-like alternatives;
- can vary marking continuation length with `--mark-reach`; the Hat markings
  live on the doubled A2 lattice, and reach is specified in original A2 units;
- ports the H7/H8 substitution expansion from the public demo into integer A2
  arithmetic;
- validates whether a candidate marking is consistent on a generated
  substitution patch before treating it as a possible "true" marking;
- reports substitution-patch mark-continuity metrics, including long run
  lengths and a continuity score, so validation-only runs can rank
  Ammann-bar-like candidates before GCTS benchmarking;
- can mine a side-dependent edge-color marking from H7/H8 substitution
  adjacencies; this assigns colors to fore/rear edge midpoints and uses the
  existing mark-conflict rule to enforce observed local edge compatibilities;
- can run validation-only sieves before paying for full GCTS benchmarks;
- can enumerate rear sign variants and cap the number of expensive GCTS
  benchmarks in a sampled search;
- can run staged searches, screening at one target and only pressure-testing
  candidates that pass the first gate;
- can run a local `train-policy` mode that reuses the Turtle policy-gradient
  branch-order learner on Hat candidates;
- reuses the local reversible GCTS engine for marked vs unmarked benchmarks.

The separate from-scratch sampler in `scripts/hat_sample_marking.py` now defaults
to A2-lattice endpoint probes. Internally the marking engine still stores mark
coordinates at doubled scale because line markings may use edge midpoints, but
`--probe-mode a2` emits probes only at even doubled coordinates, i.e. actual A2
lattice points. The older `--probe-mode midpoint` remains only as a comparison
experiment.

The Hat outline currently used is:

```text
[(0,0,0), (1,0,-1), (1,1,-2), (3,0,-3), (4,1,-5),
 (3,2,-5), (3,3,-6), (1,4,-5), (0,6,-6), (-1,6,-5),
 (-1,5,-4), (-1,4,-3), (0,3,-3), (-1,2,-1)]
```

with angles:

```text
[3, 4, 9, 4, 3, 8, 3, 8, 3, 4, 6, 4, 9, 4]
```

## Results

The first fast candidate, `v2-v12`, is useful as a pruning line on tiny or
naive searches, but it is not a true Hat marking.

| run | none | `v2-v12` | lesson |
| --- | ---: | ---: | --- |
| H8 level-2 substitution validation | valid | invalid | conflicts on the known substitution patch |
| strict 20-tile GCTS | 163 decisions | 19 decisions | very fast locally |
| strict 50-tile GCTS | 377 decisions | 1308 decisions | slower at larger scale |
| naive 50-tile, 2400-node cap | 50 tiles | 49 tiles | loses under a larger node budget |

The level-2 H8 substitution filter is a useful discriminator. Of 55 one-line
vertex/midpoint candidates, only 8 passed. The top small-search survivors were
`m5-m10`, `v5-v11`, `m3-m12`, and `m4-m11`.

Those survivors are still not good enough:

| marking | validation | strict 20-tile decisions | strict 35-tile result |
| --- | --- | ---: | --- |
| none | valid | 163 | 35 tiles in 225 decisions |
| `m5-m10` | valid | 47 | 27 tiles, wall-time stop, 468 decisions |
| `v5-v11` | valid | 47 | 27 tiles, wall-time stop, 465 decisions |

## Side-dependent GAB-like search

The marking language now supports the Golden-Ammann-Bar-shaped asymmetry:

```text
fore: one segment
rear/reflected: three segments
```

The `--search-family gab --gab-ratio` generator builds one-fore/three-rear
candidates whose rear total lattice length is four times the fore length. A
shuffled sample of 1000 such candidates gave:

```text
runs/hat-gab-ratio-shuffle1000-level2-validate-only.json
H8 level-2 validation: 242 valid, 758 rejected
```

The best candidate in the first 50-candidate benchmark slice was:

```text
fore: v2-v12
rear: v13-m12, v7-m12, m5-m10
```

It is a better candidate than the earlier single-line markings because it is
H8 level-3 valid and helps two smaller strict searches:

| run | none | side-dependent candidate |
| --- | ---: | ---: |
| strict 20-tile GCTS | 163 decisions, 2.05s | 75 decisions, 1.95s |
| strict 35-tile GCTS | 225 decisions, 2.85s | 163 decisions, 3.36s |
| strict 50-tile GCTS | 50 tiles, 377 decisions, 4.44s | 42 tiles, 1071 decisions, 15.01s wall-time stop |

So this is not yet the true Hat marking. It is a useful pressure-test candidate:
substitution-valid to level 3, locally helpful, and still rejected by the larger
GCTS benchmark.

Segment signs matter. Keeping the same endpoints but assigning the rear signs

```text
rear: v13-m12:-1, v7-m12:-1, m5-m10
```

keeps H8 level-3 validity and improves the smaller strict searches:

| run | none | signed side-dependent candidate |
| --- | ---: | ---: |
| strict 20-tile GCTS | 163 decisions, 2.17s | 65 decisions, 1.72s |
| strict 35-tile GCTS | 225 decisions, 3.02s | 158 decisions, 3.19s |
| strict 50-tile GCTS | 50 tiles, 377 decisions, 4.83s | 46 tiles, 1018 decisions, 15.00s wall-time stop |

The same signed endpoints under `--mark-value-mode constant` reached the
20-tile target in 75 decisions, so the Turtle-style reflection sign flip is
still a stronger pruning convention for this candidate. But pure constant
values are too permissive as a validator: in a shuffled 1000-candidate GAB-like
sample, all 1000 candidates passed H8 level-2 conflict validation. That means
unsigned dashed bars need a stricter continuation validator before they can be
used as the main GAB model.

The best candidate so far came from a signed, capped seed-101 sample:

```text
fore: m0-m1
rear: v13-m12, v8-m7:-1, v7-v12
```

It is H8 level-4 valid and is the first candidate to improve the strict
50-tile benchmark in both decisions and wall time:

| run | none | signed `m0-m1` candidate |
| --- | ---: | ---: |
| strict 35-tile GCTS | 225 decisions, 2.93s | 182 decisions, 3.20s |
| strict 50-tile GCTS | 377 decisions, 4.49s | 242 decisions, 4.02s |
| strict 70-tile GCTS | 399 decisions, 4.58s | 786 decisions, 11.81s |

This is the first real medium-scale acceleration signal, but it is not yet the
desired large-patch marking because the advantage reverses by 70 tiles.

A better signed candidate was found by staged 50-to-70 search:

```text
fore: v13-m2
rear: m3-m6:-1, m6-m13:-1, v6-v10:-1
```

It is H8 level-4 valid and strongly accelerates both 50 and 70 tiles:

| run | none | signed `v13-m2` candidate |
| --- | ---: | ---: |
| strict 50-tile GCTS | 377 decisions, 4.49s | 51 decisions, 1.04s |
| strict 70-tile GCTS | 399 decisions, 4.75s | 71 decisions, 1.40s |
| strict 100-tile GCTS | 1289 decisions, 14.39s | 78 tiles, 3766 decisions, 60.04s wall-time stop |

This is now the strongest GCTS test candidate: it is substitution-valid through
H8 level 4 and much faster through 70 tiles. But the 100-tile test rejects it as
the final answer.

Changing the marking continuation reach did not fix the 100-tile failure:

| `--mark-reach` | validation | none at 100 | signed `v13-m2` candidate at 100 |
| ---: | --- | ---: | ---: |
| 0 | H8 level-4 valid | 100 tiles, 1289 decisions, 15.38s | 42 tiles, 2216 decisions, 30.01s wall-time stop |
| 1 | H8 level-4 valid | 100 tiles, 1289 decisions, 15.39s | 42 tiles, 1996 decisions, 30.01s wall-time stop |
| 2 | H8 level-4 valid | 100 tiles, 1289 decisions, 15.43s | 42 tiles, 1834 decisions, 30.02s wall-time stop |
| 3 | H8 level-4 valid | 100 tiles, 1289 decisions, 14.39s | 78 tiles, 3766 decisions, 60.04s wall-time stop |

The next stricter sweep tested whether the signed GAB-like family has any
member that generalizes to 100 tiles.

With a direct 70-to-100 staged gate, three shuffled slices of the broad signed
GAB-like family produced no Stage 2 survivors. Among the first 120 candidates in
each slice, roughly half were rejected by H8 level-4 substitution validation;
the candidates that were benchmarked either failed to reach 70 tiles or reached
70 with more decisions than the unmarked baseline.

With the original GAB-ratio family that produced `v13-m2`, a 50-to-100 staged
gate found four 50-tile accelerators. All four failed the 100-tile pressure
test:

| candidate | stage 1 at 50 | stage 2 at 100 |
| --- | ---: | ---: |
| `fore=v13-m2; rear=m3-m6:-1,m6-m13:-1,v6-v10:-1` | 51 decisions, 1.04s | 78 tiles, 2744 decisions, 45.05s wall-time stop |
| `fore=v8-v10; rear=m1-m11:-1,m5-m10:-1,m8-m9` | 266 decisions, 4.42s | 84 tiles, 3041 decisions, 45.05s wall-time stop |
| `fore=v8-v10; rear=v6-m6,m3-m6:-1,v7-v13:-1` | 175 decisions, 2.95s | 81 tiles, 3032 decisions, 45.05s wall-time stop |
| `fore=v5-v11; rear=v0-v6,v3-v8,v4-v12:-1` | 289 decisions, 5.36s | 73 tiles, 2832 decisions, 45.04s wall-time stop |

The unmarked 100-tile baseline reaches the target in about 1289 decisions and
15 seconds under these settings, so these are not merely slow successes; they
are clear failures to reproduce a scalable substitution-equivalent rule.

## Continuity-ranked sieve

The validator now also measures how the marks join into long straight runs on
the H8 substitution patch. This is a stronger cheap signal than "no conflicts":
it can distinguish markings that produce long Ammann-bar-like continuations from
markings that only happen not to collide.

Three H8 level-4 validation-only sieves were run:

```text
runs/hat-gab-ratio-signed-continuity-seed701-level4.json
runs/hat-gab-ratio-signed-continuity-seed702-level4.json
runs/hat-gab-broad-signed-continuity-seed703-level4.json
```

The top continuity candidates were then benchmarked directly at 100 tiles:

| candidate | continuity score | max run | 100-tile result |
| --- | ---: | ---: | ---: |
| `fore=v7-v8; rear=v6-m6:-1,m0-m5:-1,v12-v13:-1` | 65.077 | 264 | 42 tiles, 2876 decisions, 45.01s wall-time stop |
| `fore=v3-v7; rear=v3-m7:-1,m6-m13:-1,v3-v13:-1` | 58.881 | 209 | 99 tiles, 2293 decisions, 45.07s wall-time stop |
| `fore=v7-m12; rear=v12-v13:-1,v3-v13:-1,v3-v7:-1` | 58.798 | 208 | 77 tiles, 2599 decisions, 45.04s wall-time stop |
| `fore=v7-v8; rear=v13-m2:-1,v7-m7:-1,v1-v5:-1` | 58.776 | 211 | 99 tiles, 2313 decisions, 45.07s wall-time stop |

This is progress, but not success. Continuity ranking found candidates that are
much more substitution-like by the metric, and two nearly reached 100 tiles.
However, both were much slower than the unmarked baseline, which reaches 100
tiles in about 17 seconds and 1289 decisions in the same run family.

The first Hat `train-policy` experiment reused the Turtle single-placement
policy-gradient learner on the best 99-tile continuity candidate:

```text
runs/hat-continuity-top2-train-policy-smoke.json
runs/hat-continuity-top2-learned-target100.json
```

That learner did not help. The best 30-episode greedy training rollout reached
39 tiles, and the learned 45-second GCTS branch order reached only 42 tiles on
the marked candidate. This suggests the current linear action policy is still
too local for the Hat: it learns placement preferences, not a substitution
growth grammar.

## Mined H7/H8 edge marking

The first marking that clearly accelerates Hat GCTS is not a line marking. It is
a local edge-color marking mined from H8 substitution adjacencies. This should
be read as an H7/H8-family marking, not as a proof that all legal Hat tilings
must obey this coloring:

```text
legend: R=1, O=2, Y=3, G=4, C=5, B=6, V=7, M=8, P=9, K=10

fore edge colors:
0:R, 1:O, 2:Y, 3:Y, 4:G, 5:C, 6:Y, 7:Y, 8:B, 9:C, 10:C, 11:G, 12:Y, 13:Y

rear edge colors:
0:G, 1:C, 2:Y, 3:Y, 4:V, 5:M, 6:Y, 7:Y, 8:G, 9:C, 10:P, 11:K, 12:Y, 13:Y
```

The miner treats each `(side, edge)` pair as a variable and unions two variables
whenever their edge midpoints coincide inside the known substitution patch. The
result is a 10-color edge marking over 28 fore/rear edge variables.

Validation:

| patch | shapes | result |
| --- | ---: | --- |
| H8 level 4 | 2,584 | valid, 10 classes |
| H8 level 5 | 17,711 | valid, same 10 classes |
| H7 level 5 | 15,127 | valid, same 10 classes |

GCTS results:

| target | none | mined edge marking |
| --- | ---: | ---: |
| 100 tiles | 100 tiles, 1289 decisions, 14.17s, corona 5 | 100 tiles, 141 decisions, 1.83s, corona 6 |
| 150 tiles | 106 tiles, 5748 decisions, 60.06s wall-time stop | 150 tiles, 191 decisions, 2.55s, corona 7 |
| 250 tiles | 106 tiles, 5863 decisions, 60.08s wall-time stop | 208 tiles, 4054 decisions, 60.29s wall-time stop, corona 8 |

Disabling the one-step boundary-alive filter made the 250-tile marked run worse:
174 tiles in 60.20s. A short `train-policy` smoke test on the edge marking also
did not beat the hand heuristic: in a 2-second target-150 evaluation, heuristic
reached 107 tiles, while the learned branch order reached 47.

This is finally a true GCTS test candidate for the H7/H8 substitution family. It
is substitution-derived, validated on both H7 and H8 level-5 patches, and
accelerates the 100- and 150-tile searches by a large margin. It is not a
complete characterization of all Hat tilings: the same-color edge rule may
forbid valid tilings that are outside this particular substitution construction.
The current single-tile GCTS also still stalls before 250 tiles.

So the current evidence says:

1. Simple straight segments can be good local obstructions.
2. The fastest local obstructions are often inconsistent with the known
   substitution tiling.
3. Substitution-consistent simple lines do not yet accelerate larger strict
   search.
4. Side-dependent one-fore/three-rear markings are now expressible and can pass
   substitution validation, but the first sampled survivors still fail the
   50-tile benchmark.
5. Signed rear patterns improve local pruning and can produce dramatic 50-to-70
   wins.
6. The best signed candidates now fail at 100 tiles, even when they are H8
   level-4 valid and pass a 50-tile acceleration gate.
7. Substitution-patch continuity is a useful ranking metric, but it does not
   by itself predict faster GCTS.
8. The current single-placement RL policy does not learn the missing Hat
   substitution structure.
9. Edge-color markings mined from substitution adjacencies are much stronger
   than line markings: the 10-color fore/rear edge marking reaches 150 tiles in
   2.55 seconds where the unmarked search times out at 106 tiles.

## Lessons for GCTS

The Hat is a better stress test than the Turtle precisely because cheap local
rules are misleading. A line can reduce the branching factor on a 20- or
35-tile patch while contradicting the substitution tiling at level 2. That gives
GCTS a concrete failure mode: optimizing only for short-horizon search speed can
learn false markings.

The validation target should therefore be:

- positive samples from generated H7/H8 substitution patches;
- positive samples from other known or independently generated Hat patches;
- negative samples from dead GCTS branches;
- candidate markings that must pass substitution consistency before they are
  rewarded for pruning search.

The likely next step is not more single-tile RL. It is to let GCTS use the
mined edge marking to generate larger valid patches, mine the remaining
branching bottlenecks near 200-plus tiles, and train a policy over marked
boundary states or macro-patches.

## Next implementation step

Line markings were too weak or too easy to overfit. The edge marking is strong
enough to use as the next platform, but the next useful implementation step is
still to move one level up:

- generate larger patches with the 10-color edge marking and inspect where the
  search stalls around 200-plus tiles;
- use the continuity score as a weak feature, not as the objective itself;
- train or search over boundary-state/macrotile features that can recognize
  when the search is assembling a substitution supertile;
- keep the 250-tile benchmark as the next hard gate, because 100 and 150 tiles
  are now solved by the edge marking.

The search should also add a stricter endpoint/continuation validator before
treating `constant` or `presence` marking values as a serious dashed-bar model,
because plain conflict validation accepts too many unsigned candidates.

The 10-color edge marking is now the best GCTS test candidate found so far, but
it should be treated as an H7/H8-family accelerator. Further work should test it
against independent Hat tilings before calling it a universal Hat marking, and
should focus on pushing the current 250-tile wall with macro-boundary features
or a stronger branch policy.

## From-scratch lattice marking attempt

The next experiment removes H7/H8 supervision and follows the marking
definition in `GCTS-I`: a marking is a function on lattice points, with support
allowed to extend outside the tile. The current default in
`scripts/hat_sample_marking.py` is therefore `--probe-mode lattice`:

- the finite support is a set of local A2 lattice sites, not edge-indexed
  `in/out` probes;
- `--lattice-reach 1` uses the Hat's occupied lattice support plus one A2
  graph-neighborhood, giving 50 local sites;
- the legacy `--probe-mode a2` and `--probe-mode midpoint` runs remain only as
  comparisons;
- when two tiles meet, their transformed marking supports may overlap at lattice
  points;
- labels are trained as signed equality/inequality colors over side-free
  lattice-site variables;
- rear values are now required to be the same marking values as the fore side
  with opposite sign: `rear(site) = -fore(site)`.

The trainer in `scripts/hat_sample_marking.py` collects samples from unmarked
GCTS, not from substitution patches. It records:

- positive contacts from successful or boundary-viable candidate moves;
- negative contacts from candidate moves that immediately fail the one-step
  boundary-alive test;
- a signed graph-coloring problem that keeps positive contacts equal while
  enforcing the rear-opposite constraint, then tries to separate
  high-confidence negative contacts.
- a single-tile point/candidate bipartite graph metric, which counts how many
  candidate placements survive around one fixed seed tile.
- a positive-path validation gate, which replays sampled valid partial patches
  under the learned marking and rejects markings that conflict with those
  branches.

Initial results:

| run | probe mode | sample source | learned marking | result |
| --- | --- | --- | --- | --- |
| `hat-sampled-lattice-zero-smoke.json` | direct lattice, reach 1, zero support allowed | 5 deterministic short rollouts | 3 nonzero sites | passes positive-path validation; weak pruning, exhausts at 8 tiles |
| `hat-sampled-lattice-zero-tiny.json` | direct lattice, reach 1, zero support allowed | one short tree path | 50 nonzero sites | fails positive-path validation; reject |
| `hat-sampled-lattice-opposite-smoke.json` | direct lattice, reach 1 | 5 deterministic short rollouts | 2 magnitudes on 50 sites | 11 candidates and 28 edges, but exhausted at 3 tiles |
| `hat-sampled-lattice-opposite-tiny.json` | direct lattice, reach 1 | one short tree path | 7 magnitudes on 50 sites | 6 candidates and 20 edges, one dead frontier, exhausted at 3 tiles |
| `hat-sampled-probe-smoke.json` | midpoint | 5 deterministic short rollouts | 4 colors | 60 tiles in 143 decisions vs 479 unmarked, but not A2-clean |
| `hat-sampled-a2-probe-smoke.json` | legacy independent A2 endpoint | 5 deterministic short rollouts | 1 color | no graph pruning: 488 bipartite edges, same as unmarked; benchmark failed at 37 tiles in 8s |
| `hat-sampled-a2-probe-tiny.json` | legacy independent A2 endpoint | one short tree path | 3 colors | strong graph pruning: 231 edges vs 488 unmarked, but over-pruned and exhausted at 3 tiles |
| `hat-sampled-a2-opposite-smoke.json` | legacy rear-opposite edge-adjacent A2 | 5 deterministic short rollouts | 1 magnitude | 98 candidates and 152 edges, but exhausted at 3 tiles |
| `hat-sampled-a2-opposite-tiny.json` | legacy rear-opposite edge-adjacent A2 | one short tree path | 1 magnitude | 82 candidates and 125 edges, but exhausted at 2 tiles |
| `hat-sampled-probe-random60-target100.json` | midpoint | 60 random shallow rollouts | 4 colors | failed: 88 tiles in 30s vs unmarked 100 tiles |
| `hat-sampled-probe-treepath1-target100.json` | midpoint | one successful 80-tile tree path | 6 colors | failed: 88 tiles in 30s |
| `hat-sampled-probe-treepath-random4-target100.json` | midpoint | four randomized tree paths, two reaching 80 tiles | 4 colors | failed: 88 tiles in 30s |

The current single-seed graph comparison is:

| marking | frontier points | unique candidates | bipartite edges | forced points | lesson |
| --- | ---: | ---: | ---: | ---: | --- |
| unmarked | 14 | 320 | 488 | 0 | baseline around one Hat |
| H7/H8 edge-color marking | 14 | 314 | 470 | 0 | mild one-tile pruning, despite strong larger-search acceleration |
| zero-aware lattice smoke | 14 | 308 | 451 | 0 | passes known positives but barely prunes |
| zero-aware lattice tiny | 14 | 6 | 20 | 7 | fails positive-path validation; reject |
| lattice opposite smoke | 14 | 11 | 28 | 4 | direct GCTS-I marking, but much too strong |
| lattice opposite tiny | 14 | 6 | 20 | 7 | direct GCTS-I marking, creates a dead frontier |
| legacy A2 probe smoke | 14 | 320 | 488 | 0 | learned one color, so no pruning |
| legacy A2 probe tiny | 14 | 152 | 231 | 2 | prunes locally, but forbids valid continuations |
| legacy rear-opposite A2 smoke | 14 | 98 | 152 | 1 | symmetric but still over-prunes |
| legacy rear-opposite A2 tiny | 14 | 82 | 125 | 1 | symmetric and even stronger, but invalid |

For calibration, the known Turtle stripe marking, using the same one-seed graph
metric, is much milder:

| Turtle marking | frontier points | unique candidates | bipartite edges | forced points |
| --- | ---: | ---: | ---: | ---: |
| unmarked Turtle | 14 | 304 | 472 | 0 |
| three-direction stripes | 14 | 260 | 410 | 0 |

So the A2 probe tiny marking is far stronger than the known Turtle stripes in a
single-tile graph: about a 52% reduction in unique candidates, compared with
about 15% for Turtle. The difference is that the Turtle stripes are known-good
constraints, while the current A2 tiny probe marking appears to be a false
local obstruction.

The minimizer removes paired fore/rear lattice sites, preserving the
rear-opposite requirement:

```bash
PYTHONPATH=scripts python3 scripts/hat_minimize_marking.py \
  --input runs/hat-sampled-lattice-opposite-smoke.json \
  --output runs/hat-sampled-lattice-opposite-smoke-minimized.json \
  --candidate-limit 10 \
  --seed 0 \
  --trials 30 \
  --site-mode paired
```

This keeps a paired site only if deleting it would increase either
`unique_candidates` or `bipartite_edges` in the one-seed graph.

| marking | support sites | mark entries per side | graph |
| --- | ---: | ---: | --- |
| lattice opposite smoke | 50 | 50 | 11 candidates, 28 edges |
| minimized lattice opposite smoke | 26 | 26 | 11 candidates, 28 edges |
| lattice opposite tiny | 50 | 50 | 6 candidates, 20 edges |
| minimized lattice opposite tiny | 20 | 20 | 6 candidates, 20 edges |
| legacy rear-opposite A2 smoke | 34 | 43 | 98 candidates, 152 edges |
| minimized legacy rear-opposite A2 smoke | 31 | 40 | 98 candidates, 152 edges |

The minimized lattice versions still exhaust almost immediately, so the
GCTS-I-compatible marking language is now cleaner, but the current sample labels
remain too noisy.

The direct lattice marking is a single scalar channel: one integer value at each
support site on the fore side, with the rear side determined by negating those
values on the same support.

The first direct-lattice learner incorrectly forced every support site to carry
a nonzero value. Under the rear-opposite rule, some positive contacts imply
`x = -x`, which should mean "do not mark this site" rather than "learn a
contradictory nonzero color." The zero-aware learner treats those components as
unmarked. That produces a marking that passes its sampled positives, but it is
far too sparse to help.

## Rank-3 lattice bundle

The Turtle stripe marking has three natural channels, one for each A2 lattice
direction, and the lattice symmetry group permutes those channels. The Hat
sampler now supports the same representation:

- each local A2 support point carries three possible channel entries;
- rotations/reflections transform both the support point and the channel;
- rear-side values are still exactly the negative of the fore-side values;
- zero components remain unmarked instead of being forced to carry a color.

The smoke rollout case is a useful warning sign. With 5 deterministic short
rollouts, all 150 site-channel variables were forced to zero, so the learned
marking passed positive replay validation but did not prune anything.

The more interesting run used tree-path samples:

```bash
python3 scripts/hat_sample_marking.py \
  --probe-mode lattice \
  --channels 3 \
  --lattice-reach 1 \
  --sample-source tree-path \
  --episodes 5 \
  --sample-target-tiles 20 \
  --benchmark-target-tiles 60 \
  --benchmark-max-steps 90 \
  --max-steps 40 \
  --node-limit 500 \
  --sample-wall-time-ms 2500 \
  --wall-time-ms 8000 \
  --candidate-limit 10 \
  --frontier-limit 10 \
  --output runs/hat-sampled-lattice-rank3-zero-tree5.json
```

Result:

| metric | value |
| --- | ---: |
| sampled paths | 5 |
| max sampled path | 20 tiles, corona 3 |
| physical A2 support | 50 sites |
| site-channel variables | 150 |
| zeroed variables | 74 |
| emitted fore entries | 76 |
| emitted rear entries | 76 |
| positive-path validation | passed all 5 paths |
| one-seed candidates | 320 -> 58 |
| one-seed bipartite edges | 488 -> 138 |
| 60-tile benchmark | 48 tiles, corona 4, node-limit stop |

The paired-site minimizer can then remove physical support points while
preserving the one-seed candidate graph:

```bash
PYTHONPATH=scripts python3 scripts/hat_minimize_marking.py \
  --input runs/hat-sampled-lattice-rank3-zero-tiny.json \
  --output runs/hat-sampled-lattice-rank3-zero-tiny-minimized.json \
  --candidate-limit 10 \
  --seed 0 \
  --trials 20 \
  --site-mode paired
```

For the one-path candidate, minimization reduced the marking from 38 physical
fore sites to 18 physical fore sites, and from 76 fore entries to 36 fore
entries, while keeping the same `58` candidates and `138` bipartite edges in
the one-seed graph. The rear side uses the same 18 A2 sites with all signs
negated. The refreshed five-path run produced the same 76-entry fore marking as
the one-path artifact, so this minimized picture is a compact version of the
same learned rule.

This is the first from-scratch A2-clean marking that both prunes strongly and
keeps its sampled positive paths alive. It is not yet evidence of a universal
Hat rule: the negative labels still come from local failed branches, and the
growth benchmark below shows that the learned marking has not recovered a
substitution-equivalent mechanism.

## Growth curve benchmark

The growth-curve benchmark records the first wall-clock time when a GCTS run
reaches each corona layer around the seed tile. It uses the same local search as
the other benchmarks, with a high `target_corona`, and records first-hit times
inside that one run:

```bash
PYTHONPATH=scripts python3 scripts/hat_growth_curve.py \
  --max-layers 8 \
  --wall-time-ms 60000 \
  --node-limit 24000 \
  --target-tiles 400 \
  --max-steps 450 \
  --candidate-limit 10 \
  --frontier-limit 10 \
  --lattice-marking runs/hat-sampled-lattice-zero-smoke.json \
  --output runs/hat-growth-curve-zero-layer8.json \
  --plot runs/hat-growth-curve-zero-layer8.png
```

Result on this machine:

| method | layer 1 | layer 2 | layer 3 | layer 4 | layer 5 | layer 6 | layer 7 | layer 8 | final |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| unmarked GCTS | 35 ms | 178 ms | 2328 ms | 4599 ms | 4927 ms | - | - | - | timed out at 60.1s, corona 5 |
| zero-aware learned lattice marking | 30 ms | - | - | - | - | - | - | - | exhausted at 126 ms, corona 1 |
| H7/H8 edge-marked GCTS | 35 ms | 184 ms | 322 ms | 567 ms | 1306 ms | 1726 ms | 2218 ms | 2771 ms | reached layer 8 |
| H8 substitution level 4 | 94 ms | 94 ms | 94 ms | 94 ms | 94 ms | 94 ms | 94 ms | 94 ms | generated patch, no search decisions |

The substitution row is a reference, not a tree search: the H8 level-4 patch has
2,584 tiles and corona 49, so all layers 1-8 are available as soon as the patch
is generated.

A second run used the minimized rank-3 learned lattice marking:

```bash
PYTHONPATH=scripts python3 scripts/hat_growth_curve.py \
  --max-layers 8 \
  --wall-time-ms 60000 \
  --node-limit 24000 \
  --target-tiles 400 \
  --max-steps 450 \
  --candidate-limit 10 \
  --frontier-limit 10 \
  --lattice-marking runs/hat-sampled-lattice-rank3-zero-tiny-minimized.json \
  --output runs/hat-growth-curve-rank3-tiny-minimized-layer8.json \
  --plot runs/hat-growth-curve-rank3-tiny-minimized-layer8.png
```

| method | layer 1 | layer 2 | layer 3 | layer 4 | layer 5 | layer 6 | layer 7 | layer 8 | final |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| unmarked GCTS | 36 ms | 179 ms | 2346 ms | 4649 ms | 5006 ms | - | - | - | timed out at 60.1s, corona 5 |
| minimized rank-3 learned lattice marking | 48 ms | 214 ms | 1142 ms | 17016 ms | 42324 ms | 44694 ms | - | - | timed out at 60.1s, corona 6 |
| H7/H8 edge-marked GCTS | 36 ms | 188 ms | 326 ms | 575 ms | 1319 ms | 1746 ms | 2250 ms | 2822 ms | reached layer 8 |
| H8 substitution level 4 | 99 ms | 99 ms | 99 ms | 99 ms | 99 ms | 99 ms | 99 ms | 99 ms | generated patch, no search decisions |

The minimized rank-3 marking clearly prunes early: it reaches layer 3 roughly
twice as fast, and the 20-tile benchmark drops from 190 decisions to 70
decisions. It also reaches one more corona layer than the unmarked run in the
60-second growth test. However, layers 4-6 are much slower than the H7/H8
edge-marking, so this is still not a substitution-equivalent mechanism.

The unminimized 38-site version reached layers 3 and 4 quickly but timed out at
corona 4. Minimization therefore removed some actively harmful constraints, not
only redundant ones.

Raising the per-series wall-clock cap to 5 minutes gives more late-layer data:

```bash
PYTHONPATH=scripts python3 scripts/hat_growth_curve.py \
  --max-layers 10 \
  --wall-time-ms 300000 \
  --node-limit 150000 \
  --target-tiles 1200 \
  --max-steps 1200 \
  --candidate-limit 10 \
  --frontier-limit 10 \
  --lattice-marking runs/hat-sampled-lattice-rank3-zero-tiny-minimized.json \
  --output runs/hat-growth-curve-rank3-tiny-minimized-layer10-5min.json \
  --plot runs/hat-growth-curve-rank3-tiny-minimized-layer10-5min.png
```

| method | layer 1 | layer 2 | layer 3 | layer 4 | layer 5 | layer 6 | layer 7 | layer 8 | layer 9 | layer 10 | final |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| unmarked GCTS | 35 ms | 178 ms | 2355 ms | 4610 ms | 4934 ms | 252972 ms | - | - | - | - | timed out at 300.1s, corona 6 |
| minimized rank-3 learned lattice marking | 47 ms | 204 ms | 1105 ms | 16291 ms | 40897 ms | 43146 ms | - | - | - | - | timed out at 300.1s, corona 6 |
| H7/H8 edge-marked GCTS | 35 ms | 186 ms | 324 ms | 571 ms | 1316 ms | 1785 ms | 2306 ms | 2868 ms | 101518 ms | - | timed out at 300.4s, corona 9 |
| H8 substitution level 4 | 94 ms | 94 ms | 94 ms | 94 ms | 94 ms | 94 ms | 94 ms | 94 ms | 94 ms | 94 ms | generated patch, no search decisions |

The longer run sharpens the diagnosis. The rank-3 learned marking is genuinely
helpful around layer 3 and reaches layer 6 much sooner than the unmarked search
(`43.1s` vs `253.0s`), but it does not get beyond corona 6 within 5 minutes.
The H7/H8 edge marking remains in a different class, reaching layer 9 before
its own 5-minute cap, though it also fails to reach layer 10 under this local
GCTS configuration.

So the from-scratch route is not solved yet. The direct lattice marking language
is implemented on the A2 lattice, but the current negative label is too noisy: a
one-step boundary-dead candidate is not necessarily a forbidden local contact.
It may be a locally legal contact that fails because of the surrounding partial
boundary. The graph metric is useful because it separates failure modes: the
legacy five-rollout A2 probe sample learned no obstruction, the nonzero direct
lattice samples learn symmetric obstructions that are much too strong, and the
zero-aware direct lattice sample leaves its known positives alive but is too
sparse to accelerate growth.

The next from-scratch version should collect stronger negative evidence:

- compare contacts against many independently successful patches, not just
  one-step boundary failures;
- treat "forbidden" as high-confidence absence from viable patches plus repeated
  presence in independently dead branches;
- label candidate contacts by deeper continuation tests, not only one-step
  boundary-alive checks;
- keep direct lattice supports, but train them with a held-out benchmark so
  false negatives are caught before the 100-tile run.

## Cluster RL over learned markings

The next experiment lifts the action space from single-tile moves to whole-tile
clusters:

- ordinary GCTS first mines connected cluster templates from a partial patch;
- each template is stored relative to an anchor tile, so it can be applied
  around any congruent existing tile;
- a proposed cluster may overlap the current patch only by exact whole tile
  placements, checked by the tile's vertex set;
- all new tiles in the cluster are still validated through the usual occupancy
  and marking-conflict checks;
- the cluster itself carries the union of the constituent tile markings, so the
  learned rank-3 marking continues to prune cluster placements;
- a policy-gradient proposer learns weights over cluster size, support, overlap,
  mark matches, fill, and template identity features.

The implementation is in `scripts/hat_cluster_rl.py`.

Smoke command:

```bash
PYTHONPATH=scripts python3 scripts/hat_cluster_rl.py \
  --marking rank3 \
  --mine-episodes 1 \
  --mine-target-tiles 40 \
  --mine-target-corona 4 \
  --mine-max-steps 80 \
  --mine-node-limit 800 \
  --mine-wall-time-ms 6000 \
  --max-cluster-tiles 4 \
  --cluster-radius 2 \
  --template-limit 40 \
  --active-template-limit 25 \
  --train-episodes 8 \
  --cluster-wall-time-ms 1500 \
  --max-cluster-steps 30 \
  --eval-runs 1 \
  --target-tiles 60 \
  --target-corona 5 \
  --single-wall-time-ms 8000 \
  --single-node-limit 3000 \
  --tree-wall-time-ms 8000 \
  --tree-node-limit 800 \
  --tree-branch-limit 8 \
  --output runs/hat-cluster-rl-rank3-smoke.json
```

Smoke result:

| method | time | tiles | corona | stop |
| --- | ---: | ---: | ---: | --- |
| single-tile GCTS, rank-3 marking | 8.0s | 26 | 3 | wall time |
| heuristic cluster-tree | 0.36s | 16 | 5 | target corona |
| learned cluster-tree | 0.56s | 19 | 5 | target corona |

A medium target-corona run:

```bash
PYTHONPATH=scripts python3 scripts/hat_cluster_rl.py \
  --marking rank3 \
  --mine-episodes 1 \
  --mine-target-tiles 90 \
  --mine-target-corona 6 \
  --mine-max-steps 300 \
  --mine-node-limit 10000 \
  --mine-wall-time-ms 30000 \
  --max-cluster-tiles 5 \
  --cluster-radius 2 \
  --template-limit 80 \
  --active-template-limit 30 \
  --train-episodes 35 \
  --cluster-wall-time-ms 2500 \
  --max-cluster-steps 70 \
  --anchor-limit 16 \
  --cluster-candidate-limit 24 \
  --eval-runs 3 \
  --target-tiles 140 \
  --target-corona 7 \
  --single-wall-time-ms 30000 \
  --single-node-limit 12000 \
  --single-max-steps 400 \
  --tree-wall-time-ms 30000 \
  --tree-node-limit 2500 \
  --tree-branch-limit 8 \
  --output runs/hat-cluster-rl-rank3-medium.json
```

| method | time | tiles | corona | macro decisions | stop |
| --- | ---: | ---: | ---: | ---: | --- |
| single-tile GCTS, rank-3 marking | 30.0s | 41 | 4 | - | wall time |
| heuristic cluster-tree | 1.28s | 37 | 7 | 9 | target corona |
| learned cluster-tree | 3.30s | 51 | 8 | 16 | target corona |

This shows that learned clusters can use the rank-3 marking to jump to deeper
corona layers much faster than single-tile GCTS, even though the underlying
marking alone stalls around corona 6 in the earlier growth curves.

A tile-focused run raises the corona target so the policy cannot stop after a
short radial chain:

```bash
PYTHONPATH=scripts python3 scripts/hat_cluster_rl.py \
  --marking rank3 \
  --mine-episodes 1 \
  --mine-target-tiles 90 \
  --mine-target-corona 6 \
  --mine-max-steps 300 \
  --mine-node-limit 10000 \
  --mine-wall-time-ms 30000 \
  --max-cluster-tiles 5 \
  --cluster-radius 2 \
  --template-limit 80 \
  --active-template-limit 30 \
  --train-episodes 18 \
  --learning-rate 0.16 \
  --temperature 0.8 \
  --cluster-wall-time-ms 3500 \
  --max-cluster-steps 120 \
  --anchor-limit 16 \
  --cluster-candidate-limit 24 \
  --eval-runs 2 \
  --target-tiles 110 \
  --target-corona 20 \
  --single-wall-time-ms 30000 \
  --single-node-limit 12000 \
  --single-max-steps 400 \
  --tree-wall-time-ms 30000 \
  --tree-node-limit 3000 \
  --tree-branch-limit 8 \
  --output runs/hat-cluster-rl-rank3-tilefocus.json
```

| method | time | tiles | corona | macro decisions | stop |
| --- | ---: | ---: | ---: | ---: | --- |
| single-tile GCTS, rank-3 marking | 30.0s | 48 | 4 | - | wall time |
| heuristic cluster greedy | 3.8s | 65 | 10 | 17 | wall time |
| learned cluster greedy | 3.8s | 46 | 10 | 21 | wall time |
| heuristic cluster-tree | 12.0s | 112 | 15 | 30 | target tiles |
| learned cluster-tree | 16.7s | 98 | 20 | 46 | target corona |

This is the best from-scratch result so far with the learned rank-3 marking:
macro-clusters turn a 30-second 48-tile/corona-4 single-tile search into a
12-second 112-tile/corona-15 cluster-tree search. The learned proposer is not
strictly better yet: it reaches corona 20 with fewer tiles, while the heuristic
cluster proposer fills the requested 110 tiles faster. That suggests the reward
is currently too corona-heavy. The next reward should include compact area or
boundary closure, not just tile count plus corona.
