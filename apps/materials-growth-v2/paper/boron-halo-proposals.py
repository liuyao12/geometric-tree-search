"""Learn candidate halo anchor locations from selected neighboring occurrences.

Geometry only; given motif/selection training witnesses. Pair frames are not
arbitrarily fixed: halo learning for rank-deficient motifs is deferred.
"""
from collections import defaultdict
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import cdist


def frame(template,xyz):
    p=np.asarray(template);x=np.asarray(xyz);pc=p.mean(0);xc=x.mean(0)
    assert np.linalg.matrix_rank(p-pc,tol=1e-8)==3
    u,_,vt=np.linalg.svd((p-pc).T@(x-xc));sign=np.eye(3);sign[-1,-1]=np.linalg.det(u@vt)
    rotation=u@sign@vt
    assert abs(np.linalg.det(rotation)-1)<1e-8
    translation=xc-pc@rotation
    return rotation,translation,float(np.linalg.norm(p@rotation+translation-x,axis=1).max())


def learn(d,r,folder):
    observations=defaultdict(list);rank_deferred=defaultdict(int);fit_max=0;transformed_checks=0
    angle=.371;global_q=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
    global_t=np.array([7.3,-4.1,2.9])
    for fold,cfg in enumerate(d['configurations']):
        raw=(Path(folder)/f'{fold}-1.15-3.json').read_bytes();src=json.loads(raw)
        assert hashlib.sha256(raw).hexdigest()==cfg['sourceHash']
        positions=np.array(src['positions']);cell=np.array(src['cell']);chosen=r['selected'][fold]
        lifted={};at=defaultdict(list)
        for j in chosen:
            o=cfg['occurrences'][j]
            if d['types'][o['type']]['kind']=='finite-face':
                group=src['components'][o['component']];shifts=dict(zip(group['ids'],group['imageOffsets']))
                lifted[j]={p:positions[p]+np.array(shifts[p])@cell for p in o['ids']}
            else:lifted[j]={o['ids'][0]:positions[o['ids'][0]],o['ids'][1]:positions[o['ids'][1]]+np.array(o['imageShift'])@cell}
            for p in o['ids']:at[p].append(j)
        for j in chosen:
            o=cfg['occurrences'][j];typ=d['types'][o['type']];template=np.array(typ['positions'])
            if np.linalg.matrix_rank(template-template.mean(0),tol=1e-8)<3:
                rank_deferred[o['type']]+=1;continue
            xyz=np.array([lifted[j][p] for p in o['ids']]);rotation,translation,error=frame(template,xyz)
            assert error<=d['epsilonAngstrom']+1e-8;fit_max=max(fit_max,error)
            external={};own=set(o['ids'])
            for p in o['ids']:
                for neighbor in at[p]:
                    if neighbor==j:continue
                    shift=lifted[j][p]-lifted[neighbor][p]
                    for q,point in lifted[neighbor].items():
                        if q in own:continue
                        local=(point+shift-translation)@rotation.T
                        external[tuple(np.round(local,8))]=local
            cloud=np.array(list(external.values())).reshape(-1,3)
            if len(cloud):
                # Rigid change of global coordinates must leave the local cloud unchanged.
                rq,tq,_=frame(template,xyz@global_q+global_t)
                reconstructed=((cloud@rotation+translation)@global_q+global_t-tq)@rq.T
                assert np.max(np.abs(reconstructed-cloud))<1e-8;transformed_checks+=1
            key=tuple(sorted(tuple(np.round(p,6)) for p in cloud))
            observations[o['type']].append({'fold':fold,'occurrence':j,'cloud':cloud,'key':key})
    types=[];eps=d['epsilonAngstrom']
    for ti,typ in enumerate(d['types']):
        rows=observations[ti]
        if not rows:
            types.append({'type':ti,'status':'deferred: no full-rank training frame','selectedOccurrences':rank_deferred[ti]});continue
        unique={}
        for row in rows:
            for p in row['cloud']:unique.setdefault(tuple(np.round(p,8)),p)
        points=np.array(list(unique.values())).reshape(-1,3)
        if len(points)>1:groups=fcluster(linkage(points,method='complete'),t=eps,criterion='distance')
        else:groups=np.ones(len(points),dtype=int)
        anchors=[];max_radius=0
        for label in sorted(set(groups)):
            group=points[groups==label];center=group.mean(0);radius=float(np.linalg.norm(group-center,axis=1).max());assert radius<=eps+1e-8
            max_radius=max(max_radius,radius);supported=[]
            for row in rows:
                if len(row['cloud']) and float(cdist([center],row['cloud']).min())<=eps+1e-8:supported.append(row)
            anchors.append({'position':center.tolist(),'maximumTrainingClusterRadius':radius,
                'supportOccurrences':len(supported),'supportDistinctObservedClouds':len({x['key'] for x in supported}),
                'supportConfigurations':sorted({x['fold'] for x in supported})})
        # Not every proposed anchor need be present in every environment.
        frequencies=[a['supportOccurrences']/len(rows) for a in anchors]
        types.append({'type':ti,'status':'proposed geometry; marking not trained','selectedOccurrences':len(rows),
                      'distinctObservedClouds':len({x['key'] for x in rows}),
                      'sourceConfigurations':sorted({x['fold'] for x in rows}),
                      'anchors':anchors,'minimumOccurrenceSupportFraction':min(frequencies,default=0),
                      'anchorsSupportedInEveryOccurrence':sum(f==1 for f in frequencies),
                      'maximumAnchorClusterRadius':max_radius})
    return {'scope':__doc__,'epsilonAngstrom':eps,'maximumRegistrationResidual':fit_max,
            'globalRigidTransformChecks':transformed_checks,'types':types,
            'limits':['Observed-cloud deduplication is not independent trajectory evidence.',
                      'Neighborhoods come from selected training decompositions, not all valid fillings.',
                      'Locations learned as cluster means of external atoms; no chemistry or potential.',
                      'Shared marking values, complete transformed halo domains, and search are not implemented by this proposal stage.']}


if __name__=='__main__':
    inp,learned,folder,dest=map(Path,sys.argv[1:])
    d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result']
    result=learn(d,r,folder);result.update(inputHash=hashlib.sha256(inp.read_bytes()).hexdigest(),learningHash=hashlib.sha256(learned.read_bytes()).hexdigest())
    dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in t.items() if k!='anchors'}|{'anchorCount':len(t.get('anchors',[]))} for t in result['types']],indent=2))
