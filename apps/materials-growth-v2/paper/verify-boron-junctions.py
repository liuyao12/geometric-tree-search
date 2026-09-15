"""Independent raw-geometry and training-cover checks for learned junctions."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

inp,learned,folder,alt,junction_path,out=map(Path,sys.argv[1:])
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];alternatives=json.loads(alt.read_text());a=json.loads(junction_path.read_text())
assert a['inputHash']==digest(inp) and a['learningHash']==digest(learned) and a['alternativeHash']==digest(alt)
eps=d['epsilonAngstrom'];geometry=[];training=[]
for f,cfg in enumerate(d['configurations']):
    raw=(folder/f'{f}-1.15-3.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==cfg['sourceHash']
    src=json.loads(raw);pos=np.array(src['positions']);cell=np.array(src['cell']);at=defaultdict(dict);faces=set()
    for j,o in enumerate(cfg['occurrences']):
        typ=d['types'][o['type']]
        if typ['kind']!='pair':faces.update(o['ids']);continue
        displacement=pos[o['ids'][1]]+np.array(o['imageShift']).dot(cell)-pos[o['ids'][0]]
        for u,p in enumerate(o['ids']):
            ru=r['roleOfSite'][typ['offset']+u];rv=r['roleOfSite'][typ['offset']+1-u]
            color=[o['type'],r['weightsByRole'][ru],r['weightsByRole'][rv],r['scalarLabelsByRole'][ru],r['scalarLabelsByRole'][rv]]
            at[p][j]={'vector':displacement if u==0 else -displacement,'color':color}
    geometry.append({p:v for p,v in at.items() if p not in faces})
    covers=[r['selected'][f]]+([] if a.get('trainingPolicy')=='six-original-fillings' else [x['selected'] for x in alternatives['runs'] if x['fold']==f])
    training.append([set(s) for s in covers])

maximum=0;source_checks=0;target_checks=0
def verify_fit(entry,edges,fit):
    global maximum
    q=np.array(fit['rotationRow']);perm=fit['permutation'];n=len(edges)
    assert sorted(perm)==list(range(n)) and len(entry['vectors'])==n
    assert np.max(np.abs(q.T@q-np.eye(3)))<1e-7 and abs(np.linalg.det(q)-1)<1e-7
    for i,j in enumerate(perm):assert entry['colors'][i]==edges[j]['color']
    residual=float(np.linalg.norm(np.array(entry['vectors'])@q-np.array([e['vector'] for e in edges])[perm],axis=1).max())
    assert residual<=eps+1e-8 and abs(residual-fit['residual'])<1e-7
    maximum=max(maximum,residual)

observed=defaultdict(set)
for entry in a['library']:
    assert sum(c[1] for c in entry['colors'])==r['capacity']
    assert entry['sources']
    for source in entry['sources']:
        f,p=source['fold'],source['point'];local=geometry[f][p];ids=source['candidates']
        assert set(ids)==set(local)&training[f][source['cover']]
        verify_fit(entry,[local[j] for j in ids],source['fit']);source_checks+=1
        observed[f,p].add(tuple(sorted(ids)))
checks=[]
for fold in a['folds']:
    f=fold['fold'];assert {n['point'] for n in fold['nodes']}==set(geometry[f])
    cross=0;multi=0
    for node in fold['nodes']:
        p=node['point'];local=geometry[f][p];assert {e['candidate'] for e in node['incident']}==set(local)
        for edge in node['incident']:
            raw=local[edge['candidate']];assert edge['color']==raw['color'];assert np.linalg.norm(np.array(edge['vector'])-raw['vector'])<1e-7
        keys=set()
        for state in node['states']:
            ids=state['candidates'];assert len(ids)==len(set(ids)) and set(ids)<=set(local)
            assert sum(local[j]['color'][1] for j in ids)==r['capacity']
            assert tuple(sorted(ids)) not in keys;keys.add(tuple(sorted(ids)));sources=set()
            for w in state['witnesses']:
                entry=a['library'][w['library']];verify_fit(entry,[local[j] for j in ids],w)
                sources.update(s['fold'] for s in entry['sources']);target_checks+=1
            assert sorted(sources)==state['sourceFolds']
        expected={tuple(sorted(set(local)&c)) for c in training[f]}
        assert observed[f,p]==expected and expected<=keys
        multi+=len(keys)>1;cross+=any(any(s!=f for s in state['sourceFolds']) for state in node['states'])
    checks.append({'file':fold['file'],'junctionPoints':len(fold['nodes']),'states':sum(len(n['states']) for n in fold['nodes']),
                   'multipleStatePoints':multi,'pointsWithCrossConfigurationSupport':cross,
                   'allTrainingCoversPreserved':True,'expandedCandidateCount':fold['expandedCandidateCount']})
challenges=[]
for run in alternatives['runs']:
    chosen=set(run['selected']);bad=0
    for node in a['folds'][run['fold']]['nodes']:
        actual={e['candidate'] for e in node['incident']}&chosen
        bad+=not any(actual==set(state['candidates']) for state in node['states'])
    challenges.append({'file':run['file'],'seed':run['seed'],'unsupportedJunctions':bad,'preserved':bad==0})
result={'scope':__doc__,'junctionHash':digest(junction_path),'libraryClasses':len(a['library']),
        'sourceFitsChecked':source_checks,'targetFitsChecked':target_checks,'maximumResidualAngstrom':maximum,
        'checks':checks,'alternativeChecks':challenges,
        'alternativeRole':'withheld decompositions on the same coordinates' if a.get('trainingPolicy')=='six-original-fillings' else 'included in training',
        'limits':'Recorded fits verified, not exhaustive approximate correspondence or independent material generalization.'}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
