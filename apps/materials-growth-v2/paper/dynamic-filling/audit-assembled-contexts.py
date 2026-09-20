"""Replay saved whole-decoration choices simultaneously, without refitting.

Checks directed displacement priors and reciprocal proposed port pairs. This
is a diagnostic of saved choices, not search exhaustion or GCTS filling.
Missing reciprocal overlaps mean unsupported by this interface diagnostic,
not forbidden by the GCTS marking rule.
"""
import hashlib
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(cell, clusters, frame, interfaces, contexts, witnesses):
    neighbors = [[] for _ in clusters]
    for oi in frame['observations']:
        o = interfaces['observations'][oi]
        neighbors[o['clusterA']].append((oi, 'A', o['clusterB'], np.asarray(o['imageShift'])))
        neighbors[o['clusterB']].append((oi, 'B', o['clusterA'], -np.asarray(o['imageShift'])))
    ports = {}
    displacement_errors = []
    for k, w in enumerate(witnesses):
        R = np.asarray(w['pose']['rotationRow'])
        tr = np.asarray(w['pose']['translation'])
        context = contexts[w['context']]
        assert len(context['ports']) == len(w['neighbors']) == len(set(w['neighbors']))
        for (mi, model_role), j in zip(context['ports'], w['neighbors']):
            oi, edge_role, other, shift = neighbors[k][j]
            model = interfaces['models'][mi]
            other_tr = np.asarray(witnesses[other]['pose']['translation'])
            vector = np.asarray(model['value' + model_role]) @ R
            displacement = other_tr + shift @ cell - tr
            displacement_errors.append(float(np.linalg.norm(vector * (1 if model_role == 'A' else -1) - displacement)))
            assert (oi, edge_role) not in ports
            ports[oi, edge_role] = dict(cluster=k, other=other, shift=shift,
                                       modelRole=model_role,
                                       anchor=np.asarray(model['anchor' + model_role]) @ R + tr,
                                       value=vector)
    pairs, unpaired = [], 0
    for (oi, role), port in ports.items():
        opposite = (oi, 'B' if role == 'A' else 'A')
        if opposite not in ports:
            unpaired += 1
            continue
        if role != 'A':
            continue
        other = ports[opposite]
        pairs.append(dict(observation=oi,
                          complementaryModelRoles=port['modelRole'] != other['modelRole'],
                          anchorError=float(np.linalg.norm(port['anchor'] - other['anchor'] - port['shift'] @ cell)),
                          valueError=float(np.linalg.norm(port['value'] - other['value'])),
                          signInvariantValueError=float(min(np.linalg.norm(port['value'] - other['value']),
                                                            np.linalg.norm(port['value'] + other['value'])))))
    return dict(ports=len(ports), unpairedPorts=unpaired,
                maximumDisplacementError=max(displacement_errors, default=0),
                displacementPass=all(e <= interfaces['valueTargetTolerance'] + 1e-9 for e in displacement_errors),
                reciprocalPairs=pairs,
                signInvariantPairPass=unpaired == 0 and all(p['anchorError'] <= interfaces['positionPairTolerance'] + 1e-9
                                                         and p['signInvariantValueError'] <= interfaces['valuePairTolerance'] + 1e-9 for p in pairs),
                reciprocalPairPass=unpaired == 0 and all(p['anchorError'] <= interfaces['positionPairTolerance'] + 1e-9
                                                       and p['valueError'] <= interfaces['valuePairTolerance'] + 1e-9 for p in pairs))


def main():
    paths = list(map(Path, sys.argv[1:]))
    coordp, metap, motifp, interfacep, contextp, domainp, posep, out = paths
    coords, meta, motifs, interfaces, inventory, baseline, poses = [json.loads(p.read_text()) for p in paths[:-1]]
    for key, p in [('coordinateHash', coordp), ('metadataHash', metap), ('motifHash', motifp),
                   ('interfaceHash', interfacep), ('contextHash', contextp), ('baselineHash', domainp)]:
        assert poses[key] == sha(p)
    spec = importlib.util.spec_from_file_location('checker', Path(__file__).with_name('verify-whole-context-poses.py'))
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    checker.verify(coords, meta, motifs, interfaces, inventory, baseline, poses)
    cc = {r['id']: r for r in coords['configurations']}
    mm = {r['id']: r for r in meta['configurations']}
    rr = {r['id']: r for r in motifs['rows']}
    ff = {r['configuration']: r for r in interfaces['frames']}
    grouped = defaultdict(list)
    for r in poses['rows']:
        grouped[r['configuration']].append(r)
    rows = []
    for cid, group in grouped.items():
        group.sort(key=lambda r: r['cluster'])
        assert [r['cluster'] for r in group] == list(range(len(rr[cid]['clusters'])))
        for li in range(2):
            witnesses = [r['lanes'][li]['witness'] for r in group]
            row = dict(configuration=cid, recurringOnly=bool(li), available=all(w is not None for w in witnesses))
            if row['available']:
                row.update(audit(np.asarray(cc[cid]['cell']), rr[cid]['clusters'], ff[cid], interfaces, inventory['contexts'], witnesses))
            rows.append(row)
    summary = []
    for phase in sorted({m['phase'] for m in mm.values()}):
        for recurring in [False, True]:
            group = [r for r in rows if r['recurringOnly'] == recurring and mm[r['configuration']]['phase'] == phase]
            ready = [r for r in group if r['available']]
            summary.append(dict(phase=phase, recurringOnly=recurring, frames=len(group), available=len(ready),
                                jointDisplacementPass=sum(r['displacementPass'] for r in ready),
                                allPortsReciprocal=sum(r['unpairedPorts'] == 0 for r in ready),
                                reciprocalPairPass=sum(r['reciprocalPairPass'] for r in ready),
                                signInvariantBothPass=sum(r['displacementPass'] and r['signInvariantPairPass'] for r in ready),
                                bothPass=sum(r['displacementPass'] and r['reciprocalPairPass'] for r in ready)))
    result = dict(scope=__doc__, poseHash=sha(posep), codeHash=sha(Path(__file__)), summary=summary, rows=rows,
                  limits='One saved choice per motif/lane, no search over alternatives. Reciprocal edge pairing is a diagnostic proposal, '
                         'not geometric point identity. Cross-edge collisions and multiway common marking witnesses remain unchecked. '
                         'Sign-invariant values are a separate representation ablation, identifying v with -v under '
                         'distance min(norm(v-w),norm(v+w)); they change the marked problem, not just its optimization. '
                         'No t-values, filling or material growth. Missing local witnesses and failed saved assemblies do not prove impossibility.')
    with out.open('x') as f:
        json.dump(result, f, indent=2)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
