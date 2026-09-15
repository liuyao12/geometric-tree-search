"""Necessary complementary-support pruning for a fixed half-weight cloud model.

Every positive group is filled by exactly two distinct-inventory placements.
Common cloud values imply coordinate-wise sorted-color signatures differ by at
most twice the marking radius. Use this necessary condition only: surviving
partners are not certified compatible. Repeatedly remove unsupported candidates.
"""
from collections import defaultdict, deque
from functools import lru_cache
import json
import time
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import linear_sum_assignment


def signature(cloud):
    x = np.asarray(cloud['vectors'], dtype=float)
    assert x.ndim == 2 and x.shape[1] == 3 and len(x) and np.isfinite(x).all() and np.max(np.abs(x)) <= 10000
    assert len(x) == len(cloud['colors'])
    parts = defaultdict(list)
    for v, color in zip(x, cloud['colors']): parts[json.dumps(color, sort_keys=True)].append(v)
    layout = tuple((key, len(parts[key])) for key in sorted(parts))
    # An unordered color-preserving bijection also bounds every coordinate's
    # order statistics. Sorting axes separately is a relaxation, not a match.
    value = np.concatenate([np.sort(np.asarray(parts[key]), axis=0).T.ravel() for key, _ in layout])
    return layout, value


def prepare(model, clouds, groups):
    assert model['capacity'] == 2 and 0 <= model['cloudRadius'] <= 1
    group_of = {}; atoms_of = {}
    for g in groups:
        assert g['point'] not in atoms_of and g['atoms']
        atoms_of[g['point']] = set(g['atoms'])
        assert len(atoms_of[g['point']]) == len(g['atoms'])
        for atom in g['atoms']:
            assert atom not in group_of
            group_of[atom] = g['point']
    assert set(group_of) == set(model['required']) and len(set(model['required'])) == len(model['required'])
    memberships = []; buckets = defaultdict(list); features = {}; ids = set()
    for i, c in enumerate(model['candidates']):
        assert c['id'] not in ids; ids.add(c['id'])
        points = {t['point'] for t in c['t']}
        assert points and len(points) == len(c['t']) and all(t['value'] == 1 for t in c['t'])
        involved = {group_of[p] for p in points}
        assert points == set.union(*(atoms_of[g] for g in involved))
        marks = {m['point']: m for m in c['cloudM']}
        assert len(marks) == len(c['cloudM']) and set(marks) == involved
        own = []
        for point in sorted(involved):
            m = marks[point]; assert m.get('channel', 'portable') == 'portable'
            layout, v = signature(clouds[m['cloud']]); key = (point, layout)
            buckets[key].append(i); features[i, point] = v; own.append(key)
        memberships.append(own)
    return memberships, buckets, features


def prune(model, clouds, groups, full_cloud=False, progress=None):
    start = time.monotonic(); membership, buckets, features = prepare(model, clouds, groups)
    candidates = model['candidates']; n = len(candidates); alive = np.ones(n, dtype=bool)
    base = [c.get('base', c['id']) for c in candidates]
    trees = {key: cKDTree(np.asarray([features[i, key[0]] for i in members])) for key, members in buckets.items()}
    watchers = [set() for _ in candidates]; watched = {}; queue = deque(); queued = set(); removals = []
    # For bounded input vectors and radius, this deliberately loose numerical
    # padding dominates two membership guards and coordinate arithmetic error.
    threshold = 2 * model['cloudRadius'] + 1e-8
    queries = 0
    point_cloud = {(i, m['point']): m['cloud'] for i, c in enumerate(candidates) for m in c['cloudM']}
    vector_cache = {}; color_cache = {}
    @lru_cache(maxsize=500000)
    def pair_possible(i, j, point):
        ca, cb = point_cloud[i, point], point_cloud[j, point]
        for ci in (ca, cb):
            if ci not in vector_cache:
                vector_cache[ci] = np.asarray(clouds[ci]['vectors'])
                color_cache[ci] = np.asarray([json.dumps(c, sort_keys=True) for c in clouds[ci]['colors']])
        distance = np.linalg.norm(vector_cache[ca][:, None, :] - vector_cache[cb][None, :, :], axis=2)
        permitted = (color_cache[ca][:, None] == color_cache[cb][None, :]) & (distance <= threshold)
        if not permitted.any(axis=0).all() or not permitted.any(axis=1).all(): return False
        rows, columns = linear_sum_assignment(~permitted)
        return bool(permitted[rows, columns].all())
    def support(i, key):
        nonlocal queries
        queries += 1
        local = trees[key].query_ball_point(features[i, key[0]], threshold, p=np.inf)
        for j in sorted(buckets[key][k] for k in local):
            if alive[j] and base[j] != base[i] and (not full_cloud or pair_possible(min(i, j), max(i, j), key[0])):
                watched[i, key] = j; watchers[j].add((i, key)); return True
        watched.pop((i, key), None)
        if i not in queued: queue.append((i, key[0])); queued.add(i)
        return False
    for i in range(n):
        for key in membership[i]:
            if not support(i, key): break
        if progress and i % 10000 == 0: progress({'phase': 'initial-support', 'candidatesChecked': i, 'queued': len(queue)})
    while queue:
        i, point = queue.popleft()
        if not alive[i]: continue
        alive[i] = False; removals.append({'candidate': candidates[i]['id'], 'point': point})
        if progress and len(removals) % 10000 == 0: progress({'phase': 'propagation', 'removed': len(removals)})
        for key in membership[i]:
            target = watched.pop((i, key), None)
            if target is not None: watchers[target].discard((i, key))
        affected = sorted(watchers[i], key=lambda x: (x[0], repr(x[1])))
        watchers[i].clear()
        for other, key in affected:
            if alive[other] and watched.get((other, key)) == i: support(other, key)
    return {'kept': [c['id'] for i, c in enumerate(candidates) if alive[i]], 'removals': removals,
            'signatureThreshold': threshold, 'fullCloudBijection': full_cloud, 'queries': queries,
            'pairChecks': pair_possible.cache_info().misses, 'seconds': time.monotonic() - start}
