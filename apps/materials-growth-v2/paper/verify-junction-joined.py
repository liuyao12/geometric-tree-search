"""Check joint-neighborhood source provenance, proper rotations and training coverage.

Checks every retained witness, not completeness of approximate registration.
Rebuilds coordinates without using the learner's geometry construction code.
"""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

inp,learning,alternatives,junction,classes,joined,out=map(Path,sys.argv[1:])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(inp.read_text());r=json.loads(learning.read_text())['result'];alt=json.loads(alternatives.read_text())
j=json.loads(junction.read_text());old=json.loads(classes.read_text());data=json.loads(joined.read_text())
for key,path in [('inputHash',inp),('learningHash',learning),('alternativeHash',alternatives),('junctionHash',junction),('classConnectionHash',classes)]:assert data[key]==sha(path)
eps=data['epsilonAngstrom'];assert eps==j['epsilonAngstrom']
nodes=[{n['point']:n for n in row['nodes']} for row in j['folds']]
covers=[[r['selected'][f]]+[x['selected'] for x in alt['runs'] if x['fold']==f] for f in range(len(nodes))]
sourceclasses={(s['fold'],s['point'],frozenset(s['candidates'])):li for li,t in enumerate(j['library']) for s in t['sources']}

def geometry(f,points,states,cid):
    p,q=points;ns=[nodes[f][p],nodes[f][q]]
    selected=[n['states'][si] for n,si in zip(ns,states)]
    incident=[{e['candidate']:e for e in n['incident']} for n in ns]
    displacement=np.array(incident[0][cid]['vector']);assert np.linalg.norm(displacement+incident[1][cid]['vector'])<1e-7
    positions=[displacement];colors=[[-1]]
    for side in range(2):
        for candidate in selected[side]['candidates']:
            edge=incident[side][candidate];positions.append(np.array(edge['vector'])+side*displacement);colors.append([side]+edge['color'])
    return np.asarray(positions),colors

def checkfit(template,positions,colors,fit):
    p=np.asarray(template['vectors']);rot=np.asarray(fit['rotationRow']);perm=fit['permutation']
    assert sorted(perm)==list(range(len(p))) and len(p)==len(positions)
    assert np.max(np.abs(rot.T@rot-np.eye(3)))<1e-7 and abs(np.linalg.det(rot)-1)<1e-7
    assert all(template['colors'][i]==colors[perm[i]] for i in range(len(p)))
    residual=float(np.linalg.norm(p@rot-positions[perm],axis=1).max());assert residual<=eps+1e-8
    return residual

sources=0;fits=0;maxerror=0.;checks=[]
for template in data['library']:
    assert template['sources']
    for source in template['sources']:
        f=source['fold'];cid=source['candidate'];cover=set(covers[f][source['cover']]);o=d['configurations'][f]['occurrences'][cid]
        assert cid in cover and set(source['points'])==set(o['ids'])
        typ=d['types'][o['type']];roles=r['roleOfSite'][typ['offset']:typ['offset']+2]
        if source['points']!=o['ids']:assert len({(r['weightsByRole'][v],r['scalarLabelsByRole'][v]) for v in roles})==1
        key=[o['type']]
        for point,si in zip(source['points'],source['states']):
            node=nodes[f][point];actual=cover&{e['candidate'] for e in node['incident']}
            assert set(node['states'][si]['candidates'])==actual
            key.append(sourceclasses[f,point,frozenset(actual)])
        assert key==template['key']
        xyz,colors=geometry(f,source['points'],source['states'],cid)
        maxerror=max(maxerror,checkfit(template,xyz,colors,source['fit']));sources+=1
for f,row in enumerate(data['folds']):
    prev={e['candidate']:e for e in old['folds'][f]['edges']};assert {e['candidate'] for e in row['edges']}==set(prev)
    assert len(row['edges'])==len(prev);count=0;training=0;cross=0
    for edge in row['edges']:
        before=prev[edge['candidate']];assert edge['points']==before['points'] and edge['type']==before['type']
        assert len(edge['allowedPresentStates'])==len(set(map(tuple,edge['allowedPresentStates'])))
        assert set(map(tuple,edge['allowedPresentStates']))<=set(map(tuple,before['allowedPresentStates']))
        assert len(edge['allowedPresentStates'])==len(edge['classWitnesses'])==len(edge['geometricWitnesses'])
        for states,classpair,witness in zip(edge['allowedPresentStates'],edge['classWitnesses'],edge['geometricWitnesses']):
            template=data['library'][witness['template']];assert template['key']==[edge['type'],*classpair]
            cross+=any(s['fold']!=f for s in template['sources'])
            for point,si,li in zip(edge['points'],states,classpair):
                state=nodes[f][point]['states'][si]
                assert edge['candidate'] in state['candidates'] and any(w['library']==li for w in state['witnesses'])
            xyz,colors=geometry(f,edge['points'],states,edge['candidate'])
            maxerror=max(maxerror,checkfit(template,xyz,colors,witness));fits+=1
        count+=len(edge['allowedPresentStates'])
        for record in covers[f]:
            chosen=set(record)
            if edge['candidate'] not in chosen:continue
            states=[]
            for point in edge['points']:
                node=nodes[f][point];actual=chosen&{e['candidate'] for e in node['incident']}
                states.append(next(i for i,s in enumerate(node['states']) if set(s['candidates'])==actual))
            assert states in edge['allowedPresentStates'];training+=1
    assert count==row['allowedStatePairs'] and training==row['trainingConnectionsChecked']
    checks.append({'file':row['file'],'classOnlyStatePairs':sum(len(e['allowedPresentStates']) for e in prev.values()),'jointGeometryStatePairs':count,'trainingConnectionsChecked':training,'templateMediatedCrossConfigurationWitnesses':cross})
result={'scope':__doc__,'joinedHash':sha(joined),'sourceFitsChecked':sources,'targetFitsChecked':fits,'maxResidualAngstrom':maxerror,'checks':checks}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
