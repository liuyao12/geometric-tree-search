#!/usr/bin/env python3
"""Check the binary-cover reduction independently on finite voxel patches."""
from collections import Counter
from copy import deepcopy
from itertools import product
from random import Random

from solve_point_pair_corona import solve, voxel_core_domain


def weights(voxels):
    result = Counter()
    for v in voxels:
        result[tuple(2*x+1 for x in v)] += 8
        for d in product([0, 1], repeat=3):
            result[tuple(2*(v[i]+d[i]) for i in range(3))] += 1
    return result


cube_weights = weights([(0, 0, 0)])
model = {'capacity': 8, 'placementDomain': {'kind': 'scaled_cubic', 'translationStep': 2},
         'orientations': [{'voxels': [[0, 0, 0]], 'cells': [{'pos': list(p), 'weight': w} for p, w in cube_weights.items()]}]}
pair = [{'oi': 0, 'translation': [0, 0, 0]}, {'oi': 0, 'translation': [2, 0, 0]}]
core = set(weights([(0, 0, 0), (1, 0, 0)]))
required = voxel_core_domain(model, core)
required_voxels = set(product(range(-1, 3), range(-1, 2), range(-1, 2)))
assert required == {tuple(2*x+1 for x in v) for v in required_voxels}

# Every possible subset around one corner: no multiplicity can be hidden by a
# fractional corner contribution because every repeated center exceeds capacity.
corner_neighbors = list(product([-1, 0], repeat=3))
for mask in range(256):
    voxels = [v for i, v in enumerate(corner_neighbors) if mask & (1 << i)]
    assert (weights(voxels)[(0, 0, 0)] == 8) == (len(voxels) == 8)

patches = [list(required_voxels), *[[v for v in required_voxels if v != missing] for missing in required_voxels]]
rng = Random(173)
universe = list(product(range(-2, 4), range(-2, 3), range(-2, 3)))
for _ in range(100):
    patch = list(required_voxels)
    for _ in range(rng.randrange(1, 10)):
        if rng.randrange(2):
            patch.append(rng.choice(universe))
        elif patch:
            patch.pop(rng.randrange(len(patch)))
    patches.append(patch)
for patch in patches:
    totals = weights(patch)
    point_exact = all(n <= 8 for n in totals.values()) and all(totals[p] == 8 for p in core)
    cover_exact = len(set(patch)) == len(patch) and required_voxels.issubset(patch)
    assert point_exact == cover_exact

for encoding in ('points', 'voxel-cover'):
    result = solve(model, pair, time_ms=10000, encoding=encoding)
    assert result['status'] == 'valid'
    voxels = [tuple(x//2 for x in p['translation']) for p in result['placements']]
    assert required_voxels.issubset(voxels) and len(set(voxels)) == len(voxels)

for mutation in ['capacity', 'domain', 'center', 'corner', 'voxels']:
    damaged = deepcopy(model)
    if mutation == 'capacity':
        damaged['capacity'] = 7
    elif mutation == 'domain':
        damaged['placementDomain']['translationStep'] = 1
    elif mutation == 'center':
        damaged['orientations'][0]['cells'] = [c for c in damaged['orientations'][0]['cells'] if c['pos'] != [1, 1, 1]]
    elif mutation == 'corner':
        damaged['orientations'][0]['cells'][-1]['weight'] = 2
    else:
        damaged['orientations'][0]['voxels'].append([0, 0, 0])
    try:
        voxel_core_domain(damaged, core)
    except ValueError:
        continue
    raise AssertionError('Accepted invalid reduction: ' + mutation)
print(f'PASS 256 corner subsets, {len(patches)} whole-patch equivalences, both solver encodings and invalid-model rejection.')
