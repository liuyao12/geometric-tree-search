"""Replay positive complete-decoration pose witnesses without the optimizer."""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from ase.geometry import find_mic


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify(coords, meta, motifs, interfaces, inventory, baseline, result):
    cc = {r['id']: r for r in coords['configurations']}
    mm = {r['id']: r for r in meta['configurations']}
    rr = {r['id']: r for r in motifs['rows']}
    ff = {r['configuration']: r for r in interfaces['frames']}
    expected = {(r['configuration'], m['cluster']) for r in baseline['rows'] if not r['training'] for m in r['motifs']}
    actual = [(r['configuration'], r['cluster']) for r in result['rows']]
    assert len(actual) == len(set(actual)) and set(actual) == expected
    assert motifs['epsilonAngstrom'] == .15 and interfaces['valueTargetTolerance'] == .30
    positive = 0
    max_atom, max_port = 0., 0.
    for row in result['rows']:
        cid, k = row['configuration'], row['cluster']
        c, cluster = cc[cid], rr[cid]['clusters'][k]
        assert not rr[cid]['training'] and not ff[cid]['training']
        template = motifs['types'][cluster['type']]
        neighbors = []
        for oi in ff[cid]['observations']:
            o = interfaces['observations'][oi]
            a, b = o['clusterA'], o['clusterB']
            if a == k:
                neighbors.append((b, np.asarray(o['imageShift']), o['typeB']))
            if b == k:
                neighbors.append((a, -np.asarray(o['imageShift']), o['typeA']))
        assert len(row['lanes']) == 2
        for li, lane in enumerate(row['lanes']):
            assert lane['recurringOnly'] == bool(li)
            w = lane['witness']
            if w is None:
                continue
            context = inventory['contexts'][w['context']]
            assert context['baseType'] == cluster['type']
            assert not lane['recurringOnly'] or context['trainingFrames'] >= 2
            assert rr[context['sourceConfiguration']]['training']
            p = w['pose']
            R, tr = np.asarray(p['rotationRow']), np.asarray(p['translation'])
            assert R.shape == (3, 3) and tr.shape == (3,)
            assert np.all(np.isfinite(R)) and np.all(np.isfinite(tr))
            assert np.max(np.abs(R.T @ R - np.eye(3))) < 1e-8 and abs(np.linalg.det(R) - 1) < 1e-8
            perm = p['permutation']
            assert sorted(perm) == list(range(len(template['positions'])))
            target_ids = [cluster['ids'][j] for j in perm]
            assert template['species'] == [c['species'][j] for j in target_ids]
            delta, _ = find_mic(np.asarray(template['positions']) @ R + tr - np.asarray(c['positions'])[target_ids], np.asarray(c['cell']), pbc=c['pbc'])
            atom_error = float(max(np.linalg.norm(delta, axis=1)))
            assert atom_error <= .15 + 1e-9
            assignment = w['neighbors']
            assert len(assignment) == len(context['ports']) == len(set(assignment))
            assert all(isinstance(j, int) and 0 <= j < len(neighbors) for j in assignment)
            for (mi, role), j in zip(context['ports'], assignment):
                model = interfaces['models'][mi]
                other, shift, typ = neighbors[j]
                assert model['type' + role] == cluster['type']
                assert model['typeB' if role == 'A' else 'typeA'] == typ
                # Reconstruct explicit-image displacement from source poses,
                # not the optimizer's cached displacement or residual.
                other_tr = tr if other == k else np.asarray(rr[cid]['clusters'][other]['fit']['translation'])
                d = other_tr + shift @ np.asarray(c['cell']) - tr
                v = np.asarray(model['value' + role]) @ R * (1 if role == 'A' else -1)
                error = float(np.linalg.norm(v - d))
                assert error <= .30 + 1e-9
                max_port = max(max_port, error)
            max_atom = max(max_atom, atom_error)
            positive += 1
    summary = []
    for phase in sorted({m['phase'] for m in mm.values()}):
        group = [r for r in result['rows'] if mm[r['configuration']]['phase'] == phase]
        for li in range(2):
            ids = {r['configuration'] for r in group}
            summary.append(dict(phase=phase, recurringOnly=bool(li), motifs=len(group),
                                positives=sum(r['lanes'][li]['witness'] is not None for r in group),
                                allPositiveFrames=sum(all(r['lanes'][li]['witness'] is not None for r in group if r['configuration'] == cid) for cid in ids)))
    assert result['summary'] == summary
    return dict(checkedPositiveLanes=positive, maximumAtomError=max_atom, maximumPortError=max_port, summary=summary,
                limits='Positive local witnesses only; neighbor poses are fixed separately for each motif. '
                       'No global pose compatibility or filling claim. Source library construction and negative outcomes not re-proved here.')


if __name__ == '__main__':
    paths = list(map(Path, sys.argv[1:]))
    coordp, metap, motifp, interfacep, contextp, domainp, resultp, out = paths
    data = [json.loads(p.read_text()) for p in paths[:-1]]
    result = data[-1]
    for key, p in [('coordinateHash', coordp), ('metadataHash', metap), ('motifHash', motifp),
                   ('interfaceHash', interfacep), ('contextHash', contextp), ('baselineHash', domainp)]:
        assert result[key] == sha(p)
    checked = verify(*data)
    checked.update(resultHash=sha(resultp), verifierHash=sha(Path(__file__)))
    with out.open('x') as f:
        json.dump(checked, f, indent=2)
    print(json.dumps(checked))
