"""Bounded whole-decoration pose witnesses; not global filling or growth.

One proper pose transports every atom and port of a motif together. Neighbors
remain at their saved poses; self-image displacements remain unchanged.
No learned parameters or error bounds are refitted on evaluation data.
"""
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
import numpy as np
from ase.geometry import find_mic
from scipy.optimize import linear_sum_assignment, minimize
from scipy.spatial.transform import Rotation


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def neighbors_for(frame, interfaces, k):
    neighbors = []
    for oi in frame['observations']:
        o = interfaces['observations'][oi]
        for role, own, other, sign in [('A', 'clusterA', 'clusterB', 1), ('B', 'clusterB', 'clusterA', -1)]:
            if o[own] == k:
                neighbors.append(dict(observation=oi, role=role, type=o['typeB' if role == 'A' else 'typeA'],
                                      d=sign * np.asarray(o['d']), moves=o[other] != k))
    return neighbors


def port_data(context, models):
    vectors, types = [], []
    for mi, role in context['ports']:
        vectors.append(np.asarray(models[mi]['value' + role]) * (1 if role == 'A' else -1))
        types.append(models[mi]['typeB' if role == 'A' else 'typeA'])
    return np.asarray(vectors), types


def assign(vectors, types, rotation, neighbors, delta):
    D = np.asarray([n['d'] - delta * n['moves'] for n in neighbors])
    cost = np.linalg.norm((vectors @ rotation)[:, None] - D[None, :], axis=2)
    allowed = np.array([[t == n['type'] for n in neighbors] for t in types])
    rows, cols = linear_sum_assignment(np.where(allowed, cost, 1e9))
    if len(rows) != len(vectors) or not all(allowed[rows, cols]):
        return None
    return cols.tolist(), float(max(cost[rows, cols]))


def main():
    coordp, metap, motifp, interfacep, contextp, domainp, out = map(Path, sys.argv[1:])
    coords, meta, motifs, interfaces, inventory, baseline = [json.loads(p.read_text()) for p in
                                                            [coordp, metap, motifp, interfacep, contextp, domainp]]
    for key, p in [('metadataHash', metap), ('motifHash', motifp), ('interfaceHash', interfacep), ('contextHash', contextp)]:
        assert baseline[key] == sha(p)
    assert interfaces['coordinateHash'] == motifs['coordinateHash'] == sha(coordp)
    enum = load('pose_enum', 'enumerate-rigid-proposals.py')
    cc = {r['id']: r for r in coords['configurations']}
    mm = {r['id']: r for r in meta['configurations']}
    rr = {r['id']: r for r in motifs['rows']}
    ff = {r['configuration']: r for r in interfaces['frames']}
    contexts, models = inventory['contexts'], interfaces['models']
    epsilon, tolerance = motifs['epsilonAngstrom'], interfaces['valueTargetTolerance']
    rows = []
    for frame in baseline['rows']:
        if frame['training']:
            continue
        cid = frame['configuration']
        c = cc[cid]
        for entry in frame['motifs']:
            k = entry['cluster']
            cluster = rr[cid]['clusters'][k]
            template = motifs['types'][cluster['type']]
            X = np.asarray(template['positions'])
            p = cluster['fit']
            R0, t0 = np.asarray(p['rotationRow']), np.asarray(p['translation'])
            predicted = np.empty_like(X)
            predicted[p['permutation']] = X @ R0 + t0
            delta, _ = find_mic(np.asarray(c['positions'])[cluster['ids']] - predicted, np.asarray(c['cell']), pbc=c['pbc'])
            Y = predicted + delta
            extra, stats = enum.enumerate_poses(X, Y, template['species'], epsilon)
            poses = [p] + extra
            neighbors = neighbors_for(ff[cid], interfaces, k)
            row = dict(configuration=cid, cluster=k, registration=stats, lanes=[])
            rows.append(row)
            for recurring in [False, True]:
                lane = dict(recurringOnly=recurring, witness=None, trials=0, budgetStopped=False)
                row['lanes'].append(lane)
                original = [v for v in entry['compatibleContexts'] if not recurring or contexts[v['context']]['trainingFrames'] >= 2]
                if original:
                    v = original[0]
                    lane['witness'] = dict(context=v['context'], pose=p, neighbors=v['neighbors'], optimized=False)
                    continue
                trials = []
                for ci in entry['typeCountCompatibleContexts']:
                    if recurring and contexts[ci]['trainingFrames'] < 2:
                        continue
                    vectors, types = port_data(contexts[ci], models)
                    for pose in poses:
                        assignment = assign(vectors, types, np.asarray(pose['rotationRow']), neighbors, np.asarray(pose['translation']) - t0)
                        if assignment:
                            trials.append((assignment[1], ci, pose, assignment[0]))
                trials.sort(key=lambda v: v[0])
                started = time.monotonic()
                class Budget(Exception):
                    pass
                for _, ci, pose, assignment in trials[:12]:
                    if time.monotonic() - started > 2:
                        lane['budgetStopped'] = True
                        break
                    lane['trials'] += 1
                    vectors, _ = port_data(contexts[ci], models)
                    A = np.asarray(pose['rotationRow'])
                    tr = np.asarray(pose['translation'])
                    Q = Y[pose['permutation']]
                    D = np.asarray([neighbors[j]['d'] for j in assignment])
                    moves = np.asarray([neighbors[j]['moves'] for j in assignment])[:, None]
                    def state(z):
                        R = A @ Rotation.from_rotvec(z[:3]).as_matrix()
                        translation = tr + z[3:6]
                        errors = np.r_[np.linalg.norm(X @ R + translation - Q, axis=1) - epsilon,
                                       np.linalg.norm(vectors @ R - D + moves * (translation - t0), axis=1) - tolerance]
                        return R, translation, errors
                    def callback(z):
                        if time.monotonic() - started > 2:
                            raise Budget()
                    z = np.zeros(7)
                    z[6] = max(0, float(max(state(z)[2])))
                    try:
                        solved = minimize(lambda z: z[6], z, method='SLSQP',
                                          bounds=[(-np.pi, np.pi)] * 3 + [(-.3, .3)] * 3 + [(0, None)],
                                          constraints={'type': 'ineq', 'fun': lambda z: z[6] - state(z)[2]},
                                          callback=callback, options={'maxiter': 120, 'ftol': 1e-10})
                    except Budget:
                        lane['budgetStopped'] = True
                        break
                    R, translation, errors = state(solved.x)
                    if max(errors) <= 1e-9:
                        lane['witness'] = dict(context=ci, neighbors=assignment, optimized=True,
                                               pose=dict(rotationRow=R.tolist(), translation=translation.tolist(),
                                                         permutation=pose['permutation']), maxViolation=float(max(errors)))
                        break
                lane['trialCapReached'] = len(trials) > 12 and lane['trials'] == 12 and lane['witness'] is None
            if len(rows) % 20 == 0:
                print(json.dumps(dict(motifs=len(rows), positiveLanes=sum(l['witness'] is not None for r in rows for l in r['lanes']))), flush=True)
    summary = []
    for phase in sorted({m['phase'] for m in mm.values()}):
        group = [r for r in rows if mm[r['configuration']]['phase'] == phase]
        for li, recurring in enumerate([False, True]):
            ids = {r['configuration'] for r in group}
            summary.append(dict(phase=phase, recurringOnly=recurring, motifs=len(group),
                                positives=sum(r['lanes'][li]['witness'] is not None for r in group),
                                allPositiveFrames=sum(all(r['lanes'][li]['witness'] is not None for r in group if r['configuration'] == cid) for cid in ids)))
    report = dict(scope=__doc__, coordinateHash=sha(coordp), metadataHash=sha(metap), motifHash=sha(motifp),
                  interfaceHash=sha(interfacep), contextHash=sha(contextp), baselineHash=sha(domainp),
                  codeHash=sha(Path(__file__)), enumeratorHash=sha(Path(__file__).with_name('enumerate-rigid-proposals.py')),
                  rows=rows, summary=summary,
                  limits='Necessary local witnesses only; different motifs are tested with their neighbors fixed, '
                         'so their positive optimized poses are not a simultaneous configuration. '
                         'At most 12 initializations, 120 iterations each and two seconds per lane. '
                         'Correspondences bounded at 20000 nodes. Port assignments held fixed in each trial. '
                         'Failures unknown. No t-values, paired-anchor/common-value/global GCTS verification.')
    with out.open('x') as f:
        json.dump(report, f, indent=2)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
