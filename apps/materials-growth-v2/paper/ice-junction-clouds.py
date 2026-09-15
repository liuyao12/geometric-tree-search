"""Learn rooted geometric junction clouds from selected finite ice covers.

The input decomposition, not chemistry, determines the component neighborhoods.
This is a developmental registration experiment, not tree search or blind growth.
Only coordinates, opaque species, learned components and selected edges enter
the learner. Metadata labels are not features. Proper rotations only.
"""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import time
import numpy as np
from ase.geometry import find_mic
from scipy.spatial import cKDTree

spec = importlib.util.spec_from_file_location('geometry', Path(__file__).with_name('ice-motif-dictionary.py'))
geometry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geometry)


def signature(groups):
    return tuple(tuple(g) for g in groups)


def permutations(groups, cap=100000):
    """Keep the root component fixed; exchange compatible neighbor components.

    Within each component, preserve opaque species labels. This is not complete
    enumeration of all unpartitioned point-cloud correspondences.
    """
    offsets = np.cumsum([0] + [len(g) for g in groups])
    internal = [geometry.maps(g) for g in groups]
    orders = [(0,) + p for p in itertools.permutations(range(1, len(groups)))
              if all(groups[i] == groups[j] for i, j in enumerate((0,) + p))]
    count = len(orders) * int(np.prod([len(p) for p in internal]))
    if count > cap:
        raise ValueError(f'Correspondence cap exceeded: {count}; no silent truncation')
    return np.asarray([[int(offsets[j] + v) for j, perm in zip(order, choices) for v in perm]
                       for order in orders for choices in itertools.product(*[internal[j] for j in order])])


def descriptor(x):
    x = np.asarray(x)
    distances = np.linalg.norm(x[:, None] - x[None, :], axis=2)
    # Root centroid is fixed at the origin. Both groups have necessary 2*eps bounds.
    return np.r_[np.sort(distances[np.triu_indices(len(x), 1)]), 2 * np.sort(np.linalg.norm(x, axis=1))]


def fit(source, target, perms, epsilon):
    """Origin-fixed proper Procrustes proposals, then maximum-error verification.

    Least-squares fitting is not a complete max-error feasibility solver.
    """
    x = np.asarray(source); y = np.asarray(target)[perms]
    xd = np.linalg.norm(x[:, None] - x[None, :], axis=2)
    yd = np.linalg.norm(y[:, :, None] - y[:, None, :], axis=3)
    keep = (np.max(np.abs(yd - xd), axis=(1, 2)) <= 2 * epsilon + 1e-10)
    keep &= np.max(np.abs(np.linalg.norm(y, axis=2) - np.linalg.norm(x, axis=1)), axis=1) <= epsilon + 1e-10
    if not np.any(keep): return None
    y = y[keep]; pp = perms[keep]
    u, _, vt = np.linalg.svd(np.einsum('ni,pnj->pij', x, y))
    fix = np.repeat(np.eye(3)[None], len(y), axis=0)
    fix[:, 2, 2] = np.linalg.det(u @ vt)
    rotations = u @ fix @ vt
    residual = np.linalg.norm(x[None] @ rotations - y, axis=2).max(axis=1)
    good = np.flatnonzero(residual <= epsilon + 1e-10)
    if not len(good): return None
    i = int(good[0])
    return {'rotationRow': rotations[i].tolist(), 'permutation': pp[i].tolist(), 'residual': float(residual[i])}


def junctions(c, cover, selected):
    assert all(c.get('pbc', [True, True, True]))
    parts = cover['components']; pairs = cover['componentPairs']
    assert len(set(selected)) == len(selected)
    assert sorted(i for p in parts for i in p) == list(range(len(c['positions'])))
    lifted = []; centers = []; groups = []
    for part in parts:
        ids = sorted(part, key=lambda i: (c['species'][i], i))
        x = geometry.lift(c, ids); center = x.mean(axis=0)
        lifted.append(x - center); centers.append(center)
        groups.append([c['species'][i] for i in ids])
    centers = np.asarray(centers); incidence = [[] for _ in parts]
    for edge in selected:
        a, b = pairs[edge]; assert a != b
        incidence[a].append((b, edge)); incidence[b].append((a, edge))
    # Declared existing uniform-half pair-union decomposition, not chemical valence.
    assert all(len(v) == 2 for v in incidence)
    for root, adjacent in enumerate(incidence):
        adjacent = sorted(adjacent, key=lambda be: (groups[be[0]], be[0]))
        neighbors = [a for a, _ in adjacent]
        shifts, _ = find_mic(centers[neighbors] - centers[root], c['cell'], pbc=True)
        vectors = np.vstack([lifted[root], *[lifted[a] + shift for a, shift in zip(neighbors, shifts)]])
        yield {'root': root, 'edges': [e for _, e in adjacent],
               'groups': [groups[root], *[groups[a] for a in neighbors]], 'vectors': vectors.tolist()}


def run(coordinates, cover_path, dictionary_path, selection_path, epsilon, output):
    if not np.isfinite(epsilon) or epsilon <= 0: raise ValueError('Positive finite tolerance required')
    paths = [coordinates, cover_path, dictionary_path, selection_path]
    raw = [Path(p).read_bytes() for p in paths]
    corpus, cover, dictionary, selection = map(json.loads, raw)
    hashes = [hashlib.sha256(r).hexdigest() for r in raw]
    assert dictionary['coordinateHash'] == hashes[0] and dictionary['coverHash'] == hashes[1]
    bycover = {r['id']: r for r in cover['results']}
    bydict = {r['id']: r for r in dictionary['configurations']}
    chosen = {r['id']: r for r in selection['results']}
    templates = []; buckets = {}; results = []; start = time.monotonic(); tests = 0
    for c in sorted(corpus['configurations'], key=lambda c: (not bydict[c['id']]['training'], c['id'])):
        training = bydict[c['id']]['training']; s = chosen[c['id']]
        assert s['status'] == 'connected positive finite cover'
        registrations = []
        for q in junctions(c, bycover[c['id']], s['selected']):
            key = signature(q['groups']); desc = descriptor(q['vectors'])
            b = buckets.setdefault(key, {'ids': [], 'descs': [], 'tree': None, 'indexed': 0, 'perms': permutations(q['groups'])})
            if len(b['ids']) - b['indexed'] >= 128 or (b['tree'] is None and b['ids']):
                b['tree'] = cKDTree(b['descs']); b['indexed'] = len(b['ids'])
            possible = b['tree'].query_ball_point(desc, 2 * epsilon + 1e-10, p=np.inf) if b['tree'] is not None else []
            possible += [i for i in range(b['indexed'], len(b['ids'])) if np.max(np.abs(b['descs'][i] - desc)) <= 2 * epsilon + 1e-10]
            found = None
            for j in sorted(possible):
                ti = b['ids'][j]; tests += 1
                f = fit(templates[ti]['vectors'], q['vectors'], b['perms'], epsilon)
                if f is not None: found = (ti, f); break
            if found is None and training:
                ti = len(templates)
                templates.append({'groups': q['groups'], 'vectors': q['vectors'], 'trainingOccurrences': 0})
                b['ids'].append(ti); b['descs'].append(desc)
                found = (ti, {'rotationRow': np.eye(3).tolist(), 'permutation': list(range(len(q['vectors']))), 'residual': 0.})
            row = {'root': q['root'], 'edges': q['edges'], 'matched': found is not None}
            if found is not None:
                ti, f = found
                if training: templates[ti]['trainingOccurrences'] += 1
                row.update(template=ti, **f)
            registrations.append(row)
        result = {'id': c['id'], 'training': training, 'junctions': len(registrations),
                  'matched': sum(r['matched'] for r in registrations), 'registrations': registrations}
        results.append(result)
        print(json.dumps({k: v for k, v in result.items() if k != 'registrations'} | {'templates': len(templates)}), flush=True)
    summary = {'templates': len(templates), 'singletonTemplates': sum(t['trainingOccurrences'] == 1 for t in templates),
               'trainingJunctions': sum(r['junctions'] for r in results if r['training']),
               'developmentJunctions': sum(r['junctions'] for r in results if not r['training']),
               'developmentMatched': sum(r['matched'] for r in results if not r['training']),
               'developmentConfigurationsComplete': sum(r['matched'] == r['junctions'] for r in results if not r['training']),
               'fitTests': tests, 'seconds': time.monotonic() - start}
    out = {'scope': __doc__, 'epsilonAngstrom': epsilon, 'sourceHashes': dict(zip(['coordinates', 'cover', 'dictionary', 'selection'], hashes)),
           'codeHashes': {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                          for name in ['ice-junction-clouds.py', 'ice-motif-dictionary.py']},
           'templates': templates, 'results': results, 'summary': summary,
           'limits': 'Frozen on training records only. Existing developmental split, not independent trajectories. Junctions are selected-cover neighborhoods; no negative-connection guarantee, edge-template export or search result. Missing registrations mean proposal unknown, not geometric impossibility.'}
    with Path(output).open('x') as f: json.dump(out, f)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__': run(*sys.argv[1:5], float(sys.argv[5]), sys.argv[6])
