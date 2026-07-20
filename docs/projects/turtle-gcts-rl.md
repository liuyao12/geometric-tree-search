# Turtle GCTS + RL local experiment

This is a private/local experiment track for applying GCTS plus reinforcement
learning to the Turtle tiling. It should stay out of the website until there is
a visible result worth showing.

## Why start with the Turtle

The repository already has a Turtle implementation in
`apps/turtle-tiling-game/app.js`: triangular-lattice coordinates, angle weights
in units of `1/12`, and the straight-line stripe matching rule. That makes it a
better first target than the Hat, because we can spend the experiment budget on
search and learning rather than geometry transcription.

The Python runner ports that geometry directly:

```bash
python3 scripts/turtle_gcts_rl.py \
  --episodes 30 \
  --target-tiles 90 \
  --target-corona 6 \
  --max-steps 140 \
  --node-limit 3000 \
  --policy-out runs/turtle-gcts-rl-policy.json \
  --output runs/turtle-gcts-rl-demo.json
```

The runner is stdlib-only. It writes a JSON summary with training checkpoints,
baseline comparisons, learned weights, the best patch placements, and simple
macro-signature counts.

## Current setup

- Tile: marked Turtle.
- Orientations: 12 unique marked orientations.
- Occupancy points per orientation: 28.
- Mark points per orientation: 38.
- GCTS state: angle-sum occupancy, stripe compatibility, frontier points,
  frontier-candidate graph, forced moves, one-step boundary viability checks,
  node budget, and wall-clock budget.
- RL state/action: a linear softmax policy over candidate placements. Features
  include stripe-line matches, new/overlap point counts, frontier value,
  orientation id, reflection sign, and translation residues modulo 2/3/4.
- Training loop: policy-gradient updates from constrained greedy rollouts.
- Evaluation loop: GCTS backtracking, with random, hand heuristic, or learned
  branch ordering.

## First local run

Local run on 2026-06-30:

```text
runs/turtle-gcts-rl-demo.json
target: 90 tiles, corona 6, node limit 3000
```

Results:

| branch order | best tiles | corona | elapsed | stop |
| --- | ---: | ---: | ---: | --- |
| random GCTS | 90 | 5 | 5.16s | target_tiles |
| heuristic GCTS | 90 | 5 | 14.01s | target_tiles |
| learned GCTS | 86 | 5 | 33.10s | search budget |

The best training rollout reached 73 tiles and corona 5 before a dead frontier.
The best evaluated patch was from random GCTS. Its most frequent raw neighbor
signatures included:

```text
4->6 |  4,-6,2    count 5
0->9 | -6, 2,4    count 5
10->10 | -4,2,2   count 5
```

Those signatures are not a substitution rule. They are only repeated local
attachments, but they are useful evidence for what a macro-discovery pass should
cluster.

## Lessons

1. Constraint propagation carries most of the early win. The stripe matching
   rule plus forced frontier points already turns the Turtle into a tractable
   local search problem for moderate patches.

2. Backtracking matters more than the first learned policy. Greedy rollouts die
   quickly; the same candidate generator with reversible GCTS reaches 90 tiles.

3. The hand heuristic is not obviously better than randomness. On the first
   90-tile run, random branch ordering reached the target faster and with fewer
   visited decisions than the local heuristic.

4. The current RL signal is too local to reproduce substitution. A linear policy
   over individual placements learned orientation/residue preferences, but it
   did not learn a reliable growth grammar. That is not too surprising: the
   substitution rule is a patch-level object, while the current action is a
   single tile placement.

5. Scaling exposes two costs: candidate generation grows with the frontier, and
   the policy needs macro-actions. A capped 140-tile probe produced useful best
   partials, but the uncapped run was too slow for interactive iteration.

## Next experiment

The next version should make the learning target more substitution-like:

- export branch traces from successful GCTS runs and train from elite paths;
- cluster repeated neighbor signatures into candidate macro tiles;
- represent a patch boundary as a typed cyclic string or small graph;
- let RL choose among macro completions, not just single-tile placements;
- cache candidate lists incrementally so larger patches are cheap enough to
  sample many times.

The likely path is not "RL discovers the substitution from scratch" in one
flat policy. It is more likely: GCTS generates valid patches, macro mining finds
recurring patch types, and RL learns which macro boundary to expand next.
