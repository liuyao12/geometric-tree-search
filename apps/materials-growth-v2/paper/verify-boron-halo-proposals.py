"""Independent library pose fit and neighbor-set reconstruction for halo support.

Checks support/coverage, not optimality or uniqueness of the anchor clustering.
"""
from collections import defaultdict
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial.distance import cdist

inp,learned,folder,proposals,dest=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];h=json.loads(proposals.read_text())
assert h['inputHash']==hashlib.sha256(inp.read_bytes()).hexdigest()
assert h['learningHash']==hashlib.sha256(learned.read_bytes()).hexdigest()
clouds=defaultdict(list);eps=h['epsilonAngstrom'];max_error=0
for fold,cfg in enumerate(d['configurations']):
    raw=(folder/f'{fold}-1.15-3.json').read_bytes();src=json.loads(raw)
    assert hashlib.sha256(raw).hexdigest()==cfg['sourceHash']
    pos=np.array(src['positions']);cell=np.array(src['cell']);sets={};lifted={}
    for j in r['selected'][fold]:
        o=cfg['occurrences'][j];sets[j]=set(o['ids'])
        if d['types'][o['type']]['kind']=='finite-face':
            comp=src['components'][o['component']];shifts=dict(zip(comp['ids'],comp['imageOffsets']))
            lifted[j]={p:pos[p]+np.asarray(shifts[p]).dot(cell) for p in o['ids']}
        else:lifted[j]={o['ids'][0]:pos[o['ids'][0]],o['ids'][1]:pos[o['ids'][1]]+np.asarray(o['imageShift']).dot(cell)}
    for j in r['selected'][fold]:
        o=cfg['occurrences'][j];typ=d['types'][o['type']]
        if 'anchors' not in h['types'][o['type']]:continue
        p=np.asarray(typ['positions']);x=np.array([lifted[j][a] for a in o['ids']]);pc=p.mean(0);xc=x.mean(0)
        rotation,_=Rotation.align_vectors(x-xc,p-pc)
        fitted=rotation.apply(p-pc)+xc
        error=float(np.linalg.norm(fitted-x,axis=1).max());assert error<=eps+1e-8;max_error=max(max_error,error)
        cloud={}
        for k,other in sets.items():
            if j==k:continue
            common=sets[j]&other
            if not common:continue
            assert len(common)==1
            a=next(iter(common));shift=lifted[j][a]-lifted[k][a]
            for b in other-sets[j]:
                local=rotation.inv().apply(lifted[k][b]+shift-xc)+pc
                cloud[tuple(np.round(local,8))]=local
        points=np.array(list(cloud.values())).reshape(-1,3)
        key=tuple(sorted(tuple(np.round(p,6)) for p in points))
        clouds[o['type']].append((fold,points,key))
checks=[]
for row in h['types']:
    ti=row['type']
    if 'anchors' not in row:
        p=np.array(d['types'][ti]['positions']);assert np.linalg.matrix_rank(p-p.mean(0),tol=1e-8)<3
        checks.append({'type':ti,'status':'rank-deficient frame correctly deferred'});continue
    observations=clouds[ti];anchors=np.array([x['position'] for x in row['anchors']])
    assert len(observations)==row['selectedOccurrences']
    assert len({key for _,_,key in observations})==row['distinctObservedClouds']
    distances=[cdist(anchors,points) for _,points,_ in observations]
    coverage=max((float(distance.min(axis=0).max()) for distance in distances if distance.size),default=0)
    assert coverage<=eps+1e-8
    for index,anchor in enumerate(row['anchors']):
        supported=[obs for obs,dist in zip(observations,distances) if dist.shape[1] and float(dist[index].min())<=eps+1e-8]
        assert len(supported)==anchor['supportOccurrences']
        assert sorted({f for f,_,_ in supported})==anchor['supportConfigurations']
        assert len({key for _,_,key in supported})==anchor['supportDistinctObservedClouds']
    checks.append({'type':ti,'anchors':len(anchors),'selectedOccurrences':len(observations),
                   'frameCoordinateCloudPatterns':row['distinctObservedClouds'],
                   'anchorsSupportedInEveryOccurrence':sum(a['supportOccurrences']==len(observations) for a in row['anchors']),
                   'maximumObservedPointCoverageError':coverage,'sourceConfigurations':row['sourceConfigurations']})
out={'scope':__doc__,'proposalsHash':hashlib.sha256(proposals.read_bytes()).hexdigest(),
     'totalProposedAnchors':sum(len(t.get('anchors',[])) for t in h['types']),
     'maximumIndependentPoseResidual':max_error,'checks':checks}
dest.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
