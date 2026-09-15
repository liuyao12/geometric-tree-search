"""Rescue factorized ice connections using all training-library base types.

Retain prior positive witnesses; for unmatched connections, test every represented
base type with matching species and every proper Procrustes proposal passing the
position tolerance. Stop at the first witnessed connection. Not a complete
continuous maximum-error pose solver or blind-growth experiment.
"""
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np

spec = importlib.util.spec_from_file_location('portable', Path(__file__).with_name('ice-portable-pairs.py'))
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
coordinates, cover_path, dictionary_path, selection_path, library_path, precheck_path, output = sys.argv[1:]
paths = [coordinates, cover_path, dictionary_path, selection_path, library_path, precheck_path]
corpus, covers, dictionary, selection, library, precheck = [json.loads(Path(x).read_text()) for x in paths]
for key, path in zip(['coordinates','cover','dictionary','selection'], paths[:4]):
    assert library['sourceHashes'][key] == hashlib.sha256(Path(path).read_bytes()).hexdigest()
for path in paths[:5]:
    assert precheck['inputHashes'][Path(path).name] == hashlib.sha256(Path(path).read_bytes()).hexdigest()
cv = {r['id']: r for r in covers['results']}; ds = {r['id']: r for r in dictionary['configurations']}; ss = {r['id']: r for r in selection['results']}
old = {r['id']: r for r in precheck['results']}; coords = {c['id']: c for c in corpus['configurations']}
base_ids = {json.dumps([b['pairType'], b['componentSites']]): i for i, b in enumerate(library['baseMotifs'])}
variants = defaultdict(list)
for i, m in enumerate(library['motifs']): variants[m['base']].append(i)
stacks = {b: np.asarray([[v['vectors'] for v in library['motifs'][i]['cloudM']] for i in ids]) for b, ids in variants.items()}
result = []
for cid in [c['id'] for c in corpus['configurations'] if not ds[c['id']]['training']]:
    c = coords[cid]; d = ds[cid]; cover = cv[cid]; selected = ss[cid]['selected']
    query = {q['root']: p.cloud_value(q) for q in p.junction.junctions(c, cover, selected)}
    old_rows = {r['edge']: r for r in old[cid]['rows']}; rows = []
    for edge in selected:
        o = d['occurrences'][edge]
        previous = old_rows[edge]
        if previous['anyPoseMatched']:
            w = dict(previous['witnesses'][0], type=o['type'])
            rows.append({'edge':edge, 'savedPoseMatched':True, 'anyPoseMatched':True,
                         'procrustesProposals':0, 'witnessedPoseEntries':1, 'witnesses':[w], 'typesTested':0})
            continue
        y = p.junction.geometry.lift(c, o['ids'])
        species = [c['species'][i] for i in o['ids']]
        perms = p.junction.geometry.maps(species); yy0 = y[perms]; mean0 = yy0.mean(axis=1)
        yd = np.linalg.norm(yy0[:, :, None] - yy0[:, None, :], axis=3)
        poses = []; tested = 0
        for ti in sorted({base['pairType'] for base in library['baseMotifs']}):
            t = dictionary['types'][ti]
            if t['species'] != species: continue
            tested += 1; x = np.asarray(t['positions'])
            xd = np.linalg.norm(x[:, None] - x[None, :], axis=2)
            keep = np.max(np.abs(xd - yd), axis=(1, 2)) <= 2 * dictionary['epsilonAngstrom'] + 1e-10
            if not np.any(keep): continue
            yy=yy0[keep]; pp=perms[keep]; mean=mean0[keep]
            u, _, vt = np.linalg.svd(np.einsum('ni,pnj->pij', x, yy - mean[:, None, :]))
            fix = np.repeat(np.eye(3)[None], len(yy), axis=0); fix[:, 2, 2] = np.linalg.det(u @ vt)
            rotation = u @ fix @ vt
            errors = np.linalg.norm(x[None] @ rotation + mean[:, None, :] - yy, axis=2).max(axis=1)
            poses.extend((ti, pp[i].tolist(), rotation[i]) for i in np.flatnonzero(errors <= dictionary['epsilonAngstrom'] + 1e-10))
        matched = False; witnessed_poses = 0; witnesses = []
        for pose_index, (ti, permutation, r) in enumerate(poses):
            oo = dict(o, type=ti, permutation=permutation)
            ep = p.endpoints(oo, cover['components'], cover['componentPairs'][edge]); bid = base_ids.get(p.base_key(oo, ep))
            if bid is None: continue
            targets = [query[root] for _, root in ep]; ids = variants[bid]; rotated = stacks[bid] @ r
            possible_sides = []
            for side in range(2):
                colors = [library['motifs'][i]['cloudM'][side]['colors'] for i in ids]
                color_ok = np.asarray([[[a == b for b in targets[side]['colors']] for a in cc] for cc in colors])
                distance = np.linalg.norm(rotated[:, side, :, None, :] - np.asarray(targets[side]['vectors'])[None, None, :, :], axis=3)
                close = color_ok & (distance <= library['markingRadiusAngstrom'] + 1e-10)
                possible_sides.append(close.any(axis=1).all(axis=1) & close.any(axis=2).all(axis=1))
            endpoint_witnesses = []
            for side in range(2):
                accepted = None
                for j in np.flatnonzero(possible_sides[side]):
                    value = {'vectors': rotated[j, side].tolist(), 'colors': library['motifs'][ids[int(j)]]['cloudM'][side]['colors']}
                    fit = p.cloud.contains(value, targets[side], library['markingRadiusAngstrom'])
                    if fit is not None:
                        accepted = {'motif': ids[int(j)], 'fit': fit}; break
                endpoint_witnesses.append(accepted)
            here = all(w is not None for w in endpoint_witnesses)
            if here:
                matched = True; witnessed_poses += 1
                witnesses.append({'type':ti, 'permutation': permutation, 'rotationRow': r.tolist(), 'endpoints': endpoint_witnesses})
                break
        rows.append({'edge': edge, 'savedPoseMatched': old_rows[edge]['anyPoseMatched'], 'anyPoseMatched': matched,
                     'procrustesProposals': len(poses), 'typesTested':tested, 'witnessedPoseEntries': witnessed_poses, 'witnesses': witnesses})
    row = {'id': cid, 'edges': len(rows), 'savedPoseMatched': sum(r['savedPoseMatched'] for r in rows),
           'anyPoseMatched': sum(r['anyPoseMatched'] for r in rows), 'procrustesProposals': sum(r['procrustesProposals'] for r in rows), 'rows': rows}
    result.append(row); print(json.dumps({k: v for k, v in row.items() if k != 'rows'}), flush=True)
out = {'scope': __doc__, 'inputHashes': {Path(path).name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths},
       'codeHash': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'results': result, 'limits': 'All represented training base types considered for previously unmatched developmental connections; first positive witness retained. Procrustes proposals do not exhaust continuous maximum-error feasible poses. This does not prove that unmatched connections are impossible or forbidden.'}
with Path(output).open('x') as f: json.dump(out, f, indent=2)


