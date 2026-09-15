"""Factorized endpoint pose sensitivity on all developmental configurations.

Enumerate all species-preserving proper Procrustes proposals for the already
assigned base type, not all types or all continuous maximum-error feasible poses.
Endpoint markings remain locked to the base rotation.
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
    old_rows = {r['edge']: r for r in old[cid]['registrations']}; rows = []
    for edge in selected:
        o = d['occurrences'][edge]; t = dictionary['types'][o['type']]
        x = np.asarray(t['positions']); y = p.junction.geometry.lift(c, o['ids'])
        perms = p.junction.geometry.maps(t['species']); yy = y[perms]; mean = yy.mean(axis=1)
        xd = np.linalg.norm(x[:, None] - x[None, :], axis=2)
        yd = np.linalg.norm(yy[:, :, None] - yy[:, None, :], axis=3)
        keep = np.max(np.abs(xd - yd), axis=(1, 2)) <= 2 * dictionary['epsilonAngstrom'] + 1e-10
        yy = yy[keep]; pp = perms[keep]; mean = mean[keep]
        u, _, vt = np.linalg.svd(np.einsum('ni,pnj->pij', x, yy - mean[:, None, :]))
        fix = np.repeat(np.eye(3)[None], len(yy), axis=0); fix[:, 2, 2] = np.linalg.det(u @ vt)
        rotation = u @ fix @ vt
        errors = np.linalg.norm(x[None] @ rotation + mean[:, None, :] - yy, axis=2).max(axis=1)
        poses = [(o['permutation'], np.asarray(o['rotationRow']))] + [(pp[i].tolist(), rotation[i]) for i in np.flatnonzero(errors <= dictionary['epsilonAngstrom'] + 1e-10)]
        matched = False; witnessed_poses = 0; witnesses = []
        for pose_index, (permutation, r) in enumerate(poses):
            oo = dict(o, permutation=permutation)
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
            if pose_index == 0: assert here == old_rows[edge]['factorized']
            if here:
                matched = True; witnessed_poses += 1
                witnesses.append({'permutation': permutation, 'rotationRow': r.tolist(), 'endpoints': endpoint_witnesses})
        rows.append({'edge': edge, 'savedPoseMatched': old_rows[edge]['factorized'], 'anyPoseMatched': matched,
                     'procrustesProposals': len(poses) - 1, 'witnessedPoseEntries': witnessed_poses, 'witnesses': witnesses})
    row = {'id': cid, 'edges': len(rows), 'savedPoseMatched': sum(r['savedPoseMatched'] for r in rows),
           'anyPoseMatched': sum(r['anyPoseMatched'] for r in rows), 'procrustesProposals': sum(r['procrustesProposals'] for r in rows), 'rows': rows}
    result.append(row); print(json.dumps({k: v for k, v in row.items() if k != 'rows'}), flush=True)
out = {'scope': __doc__, 'inputHashes': {Path(path).name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in paths},
       'codeHash': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'results': result, 'limits': 'An all-developmental fixed-base factorized-endpoint sensitivity diagnostic. No complete continuous-pose or all-template enumeration. This does not prove that unmatched connections are impossible or forbidden.'}
with Path(output).open('x') as f: json.dump(out, f, indent=2)

