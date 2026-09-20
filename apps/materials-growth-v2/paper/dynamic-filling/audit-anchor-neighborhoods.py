"""Periodic proximity audit of learned anchor supports, not point identification.

Distance-connected components at the declared .30 angstrom pair tolerance
are conservative ambiguity groups. They are NOT automatically merged GCTS
points. Common radius-.15 position/value balls are tested for each group.
"""
import hashlib
import importlib.util
import itertools
import json
import sys
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.optimize import minimize


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def common_ball(points, radius=.15):
    P = np.asarray(points)
    center = P.mean(axis=0)
    if len(P) > 2 and max(np.linalg.norm(P-center,axis=1)) > radius+1e-9:
        z = np.r_[center, max(np.linalg.norm(P-center,axis=1))]
        fit = minimize(lambda z:z[3], z, method='SLSQP', bounds=[(None,None)]*3+[(0,None)],
                       constraints={'type':'ineq','fun':lambda z:z[3]**2-np.sum((P-z[:3])**2,axis=1)},
                       options={'maxiter':200,'ftol':1e-12})
        center = fit.x[:3]
    measured = float(max(np.linalg.norm(P-center,axis=1)))
    # A diameter > 2r supplies a necessary-condition failure independent of
    # optimizer termination; otherwise a missing witness remains unknown.
    diameter = float(max(np.linalg.norm(P[:,None]-P[None,:],axis=2).ravel()))
    return dict(center=center.tolist(), maximumDistance=measured, diameter=diameter,
                status='common-ball-witness' if measured <= radius+1e-9 else
                       'diameter-obstruction' if diameter > 2*radius+1e-9 else 'unknown-no-ball-witness')


def proximity_groups(points, cell, tolerance=.30):
    P, C = np.asarray(points), np.asarray(cell)
    n = len(P)
    shifts = np.asarray(list(itertools.product(range(-2,3),repeat=3))) @ C
    minimum = np.linalg.svd(C,compute_uv=False)[-1]
    inverse = np.linalg.inv(C)
    adjacency = [[] for _ in P]
    for i in range(n):
        delta = P[i+1:]-P[i]
        if not len(delta):
            continue
        base = delta-np.round(delta@inverse)@C
        images = base[:,None,:]+shifts[None,:,:]
        lengths = np.linalg.norm(images,axis=2)
        best = np.argmin(lengths,axis=1)
        distances = lengths[np.arange(len(base)),best]
        assert np.all(3*minimum-np.linalg.norm(base,axis=1) > distances+1e-8), 'Image bound not certified'
        for offset in np.flatnonzero(distances <= tolerance+1e-9):
            j = i+1+int(offset)
            d = images[offset,best[offset]]
            adjacency[i].append((j,d))
            adjacency[j].append((i,-d))
    seen, groups = set(), []
    for start in range(n):
        if start in seen:
            continue
        lifted, pending, winding = {start:P[start]}, [start], False
        seen.add(start)
        while pending:
            i = pending.pop()
            for j,d in adjacency[i]:
                candidate = lifted[i]+d
                if j in lifted:
                    winding |= np.linalg.norm(candidate-lifted[j]) > 1e-7
                else:
                    lifted[j] = candidate
                    pending.append(j)
                    seen.add(j)
        ids = sorted(lifted)
        groups.append((ids, np.array([lifted[j] for j in ids]), bool(winding)))
    return groups


def main():
    coordp, motifp, interfacep, contextp, choicep, out = map(Path,sys.argv[1:])
    coords,motifs,interfaces,inventory,choices = [json.loads(p.read_text()) for p in [coordp,motifp,interfacep,contextp,choicep]]
    assert interfaces['coordinateHash']==motifs['coordinateHash']==sha(coordp)
    assert inventory['interfaceHash']==sha(interfacep) and inventory['motifHash']==sha(motifp)
    cc={r['id']:r for r in coords['configurations']}
    rr={r['id']:r for r in motifs['rows']}
    cr={r['configuration']:r for r in inventory['rows']}
    evaluated={r['configuration']:r['witness'] for r in choices['rows'] if r['witness'] is not None and not r['recurringOnly']}
    rows=[]
    for frame in interfaces['frames']:
        cid=frame['configuration']
        if frame['status']!='admitted' or (not frame['training'] and cid not in evaluated):
            continue
        clusters=rr[cid]['clusters']
        witnesses=[dict(context=cr[cid]['motifs'][k]['context'],pose=p['fit']) for k,p in enumerate(clusters)] if frame['training'] else evaluated[cid]
        anchors,values,labels=[],[],[]
        for k,w in enumerate(witnesses):
            context=inventory['contexts'][w['context']]
            R,tr=np.asarray(w['pose']['rotationRow']),np.asarray(w['pose']['translation'])
            for pi,(mi,role) in enumerate(context['ports']):
                m=interfaces['models'][mi]
                anchors.append(np.asarray(m['anchor'+role])@R+tr)
                values.append(np.asarray(m['value'+role])@R)
                labels.append(dict(cluster=k,context=w['context'],port=pi,interface=mi,role=role))
        groups=[]
        for ids,P,winding in proximity_groups(anchors,cc[cid]['cell']):
            groups.append(dict(members=[labels[j] for j in ids], winding=winding,
                               position=common_ball(P) if not winding else dict(status='unknown-periodic-winding'),
                               marking=common_ball([values[j] for j in ids])))
        rows.append(dict(configuration=cid,training=frame['training'],anchors=len(anchors),groups=groups))
    summary=[]
    for training in [True,False]:
        subset=[r for r in rows if r['training']==training]
        groups=[g for r in subset for g in r['groups']]
        summary.append(dict(training=training,frames=len(subset),groups=len(groups),
                            sizes=dict(Counter(len(g['members']) for g in groups)),
                            positionStatuses=dict(Counter(g['position']['status'] for g in groups)),
                            markingStatuses=dict(Counter(g['marking']['status'] for g in groups)),
                            multiPortGroups=sum(len(g['members'])>2 for g in groups)))
    result=dict(scope=__doc__,coordinateHash=sha(coordp),motifHash=sha(motifp),interfaceHash=sha(interfacep),
                contextHash=sha(contextp),choiceHash=sha(choicep),codeHash=sha(Path(__file__)),summary=summary,rows=rows,
                limits='Connected-neighborhood convention is a conservative diagnostic, not a declared equality relation. '
                       'Proximity does not require merging. Common-ball failure for a group is not GCTS impossibility. '
                       'A positive point/value witness does not learn t or prove coverage. No new search pruning authorized.')
    with out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(summary))


if __name__=='__main__':main()
