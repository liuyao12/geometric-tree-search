# Learning the Hat and mixed rank-three markings

Each row in the shipped table assigns a value to one lattice point and one of three directions on a prototile. For a placement $g$ with coordinate permutation $\pi$, the transformed component at $gx$ is $\operatorname{sgn}(\pi)m_{\pi(j)}(x)$ in direction $j$. An absent component is $\ast$ and agrees with every value. The Hat search admits reflected Hats. The mixed search uses rotations and translations of both prototiles.

## Where the assignments come from

1. Run unmarked GCTS with the demo’s oldest-frontier scheduling and shared-boundary-segment rule. Record the placement sequence at each dead point. Four training seeds gave 436 Hat dead ends and 830 mixed dead ends.
2. Enumerate complete neighborhoods around each prototile using only the lattice geometry, point capacities and complete placement domains. Enumerate all ways to complete the first two neighborhoods and retain each second neighborhood admitting a further extension. Every full-plane tiling must realize one of these possibilities. The resulting lists contain 98 neighborhoods around a Hat in the Hat-only domain and 77 around each prototile in the mixed domain.
3. For a relative placement in a failed branch, try assigning opposite transformed values at a coincident point and direction. Keep a proposed assignment only if **every** new unequal overlap it creates across allowed relative placements is independently impossible in a full-plane tiling. Also encode the three-Hat and eight-tile mixed obstructions. After those examples, selection favors frequent failing placements and earlier rejection in the recorded branches. Remove an assignment when all geometric rejections keep their first rejecting extent.
4. Replay the actual sparse marking on the recorded dead ends. All 436 Hat dead ends and all 830 mixed dead ends conflicted. The first conflict preceded the last recorded move in 343 Hat and 706 mixed cases. Separately, the verifier enumerates conflicts from the production marking entries and checks each against unmarked neighborhoods. It certified 782 capacity-compatible ordered relative placements for Hat and 1,704 for mixed. This certifies preservation of every full-plane tiling in each stated domain.

The mixed marking has 31 Hat assignments and 30 Turtle assignments. The Hat-only marking has 33. In the mixed obstruction, tiles 1 and 7 disagree in component zero at $(1,-4,3)$. The largest occupied extent is 4 for Hat alone and 8 for mixed.

## Held-out growth

Six fresh seeds were used for each row, at each target. All rows used the same scheduler and fixed-root convention. The node budgets were 450 at 75 tiles and 900 at 150 tiles. Entries below give median backtracks; every marked run completed. Three of 36 corresponding unmarked Hat or mixed runs reached their target within budget. The raw trial file includes every capped run.

| Tile set and marking | 75 tiles | 150 tiles |
| --- | ---: | ---: |
| Hat, from failures | 2 | 7 |
| Mixed, from failures, Hat start | 1.5 | 7.5 |
| Mixed, from failures, Turtle start | 9 | 15.5 |
| Turtle, constant rank three, extent 9 | 31.5 | 69.5 |

The mixed Turtle-start trials at 150 tiles ranged from 0 to 273 backtracks. These results measure finite patch growth under the recorded seeds and budgets. [Individual trials](held-out.jsonl)

## Reproduce from the repository root

```sh
node research/failure-marking/run.mjs collect > /tmp/gcts-training.jsonl
node research/failure-marking/run.mjs geometry | python3 research/failure-marking/neighborhoods.py > /tmp/gcts-neighborhoods.json
python3 research/failure-marking/encode.py /tmp/gcts-neighborhoods.json /tmp/gcts-training.jsonl
node research/failure-marking/run.mjs replay /tmp/gcts-training.jsonl
node tests/test_failure_rank3.mjs
python3 tests/verify_failure_rank3.py
node research/failure-marking/run.mjs compare 75
node research/failure-marking/run.mjs compare 150
```

The encoder checks the shipped table by default. Pass `--write` to regenerate it. The solver reads only the table through `SparseA2Marking`. The training examples and proof catalogs are used offline.
