"""Independently verify registered geometry, training lifts, and search witnesses.

Rebuild integer point totals and scalar marks. Verify cloud witnesses with the
separate Python membership implementation, not the JavaScript search filter.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

inp,compiled,junction,joined,portable,alt,model_path,search,kernel,out=map(Path,sys.argv[1:])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(inp.read_text());base=json.loads(compiled.read_text());j=json.loads(junction.read_text());p=json.loads(portable.read_text());a=json.loads(alt.read_text());data=json.loads(model_path.read_text())
for key,path in [('compiledHash',compiled),('junctionHash',junction),('joinedHash',joined),('portableHash',portable),('alternativeHash',alt)]:assert data[key]==sha(path)
assert base['inputHash']==sha(inp) and p['inputHash']==sha(inp)
assert data['sourceHash']==sha(Path(__file__).with_name('compile-portable-search.mjs'))
spec=importlib.util.spec_from_file_location('cloud',Path(__file__).with_name('portable-cloud-markings.py'))
cloud=importlib.util.module_from_spec(spec);spec.loader.exec_module(cloud)
registration_checks=0;training_checks=0;max_anchor=0.;max_field=0.;results=[]
models={}
for row in data['models']:
    f=row['fold'];model=row['model'];models[f]=model;bybase={c['id']:c for c in base['models'][f]['candidates']};nodes={n['point']:n for n in j['folds'][f]['nodes']}
    assert model['capacity']==base['models'][f]['capacity'] and model['required']==base['models'][f]['required'] and model['cloudRadius']==p['markingRadiusAngstrom']
    assert len({c['id'] for c in model['candidates']})==len(model['candidates'])
    for c in model['candidates']:
        original=bybase[c['base']];assert c['t']==original['t'] and c['m']==[m for m in original['m'] if m['channel']=='0']
        if c['registration'] is None:assert not c['cloudM'];continue
        reg=c['registration'];motif=p['motifs'][reg['template']];rot=np.asarray(reg['rotationRow'])
        assert np.max(np.abs(rot.T@rot-np.eye(3)))<1e-7 and abs(np.linalg.det(rot)-1)<1e-7
        occurrence=d['configurations'][f]['occurrences'][int(c['base'])]
        assert occurrence['type']==motif['pairType'] and c['t']==[{'point':str(point),'value':value} for point,value in zip(occurrence['ids'],motif['t'])]
        left,right=occurrence['ids'];delta=np.asarray(next(e['vector'] for e in nodes[left]['incident'] if e['candidate']==int(c['base'])))
        error=float(np.linalg.norm(np.array(motif['anchors'][1])@rot-delta));assert error<=p['positionToleranceAngstrom']+1e-8;max_anchor=max(max_anchor,error)
        assert len(c['cloudM'])==2
        for side,(point,mark) in enumerate(zip(occurrence['ids'],c['cloudM'])):
            assert mark['point']==str(point) and set(mark)=={'point','cloud'}
            value=data['clouds'][mark['cloud']];assert value['colors']==motif['cloudM'][side]['colors']
            assert np.max(np.abs(np.asarray(value['vectors'])-np.asarray(motif['cloudM'][side]['vectors'])@rot))<1e-10
        registration_checks+=1

def verify_selected(model,ids,supplied=None,require_clouds=True):
    global max_field
    assert len(ids)==len(set(ids));chosen=set(ids);byid={c['id']:c for c in model['candidates']};assert chosen<=byid.keys()
    totals=dict.fromkeys(model['required'],0);scalar={};owners=set();marks={}
    for cid in ids:
        c=byid[cid];assert c['base'] not in owners;owners.add(c['base'])
        for t in c['t']:totals[t['point']]+=t['value']
        for m in c['m']:
            key=(m['point'],m.get('channel','0'));assert m['lo']==m['hi'];assert key not in scalar or scalar[key]==m['lo'];scalar[key]=m['lo']
        for m in c['cloudM']:marks.setdefault((m['point'],m.get('channel','portable')),[]).append(data['clouds'][m['cloud']])
    assert all(v<=model['capacity'] for v in totals.values())
    count=0
    if require_clouds:
        provided={tuple(json.loads(w['point'])):w['witness'] for w in supplied} if supplied is not None else None
        if provided is not None:assert len(provided)==len(supplied) and set(provided)==set(marks)
        for point,assignments in marks.items():
            if provided is None:
                proposal=cloud.propose_common_witness(assignments,model['cloudRadius']);assert proposal['status']=='verified-witness';witness=proposal['witness']
            else:witness=provided[point]
            fits=cloud.common_witness(assignments,witness,model['cloudRadius']);assert fits is not None;max_field=max(max_field,max(f['maxResidual'] for f in fits));count+=1
    return all(v==model['capacity'] for v in totals.values()),count,owners

for row in data['models']:
    f=row['fold'];references=[set(base['models'][f]['trainingSelected'])]+[{str(i).zfill(6) for i in run['selected']} for run in a['runs'] if run['fold']==f]
    assert len(row['trainingLifts'])==len(references)
    for record,expected in zip(row['trainingLifts'],references):
        full,count,owners=verify_selected(row['model'],record['selected']);assert full and owners==expected and count==record['verifiedCommonValues'];training_checks+=1
summary=json.loads((search/'summary.json').read_text());assert summary['modelHash']==sha(model_path)
assert len(summary['results'])==2*len(models)
files=sorted(search.glob('[0-9]-*.json'));assert len(files)==len(summary['results'])
for file in files:
    run=json.loads(file.read_text());assert run['modelHash']==sha(model_path) and run['kernelHash']==sha(kernel)
    for name,value in run['sourceHashes'].items():assert sha(Path(__file__).with_name(name))==value
    r=run['result'];saved=next(s for s in summary['results'] if s['fold']==r['fold'] and s['enabled']==r['enabled']);assert saved=={**r,'selected':len(r['selected'])}
    model=models[r['fold']];claimed=r['status']=='verified finite registered filling'
    certify_clouds=r['enabled'] and r['markingStatus']=='verified-common-values'
    full,count,_=verify_selected(model,r['selected'],run['commonWitnesses'] if certify_clouds else None,certify_clouds)
    assert full==r['scalarComplete'] and (not claimed or full and (not r['enabled'] or certify_clouds))
    assert not (r['enabled'] and r['markingStatus']=='unknown-common-value' and claimed)
    results.append({'file':r['file'],'portableEnabled':r['enabled'],'status':r['status'],'selected':len(r['selected']),'scalarComplete':full,'verifiedCommonValues':count})
result={'scope':__doc__,'modelHash':sha(model_path),'portableHash':sha(portable),'registeredVariantsChecked':registration_checks,'trainingLiftsChecked':training_checks,'maxAnchorResidualAngstrom':max_anchor,'maxCommonValueResidualAngstrom':max_field,'results':results,
        'limits':'Finite pose registrations remain proposed using the old target tables. Missing cloud witnesses are not certified legal markings. No continuous-pose completeness or independent family transfer claim.'}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
