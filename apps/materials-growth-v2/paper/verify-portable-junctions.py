"""Verify portable exports and common cloud witnesses for all training covers.

Uses the separately raw-geometry-checked junction artifact. Does not claim a
complete pose generator or a complete algorithm for continuous set intersection.
"""
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

inp,learned,alt,junction,joined,portable,out=map(Path,sys.argv[1:])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];a=json.loads(alt.read_text());j=json.loads(junction.read_text());coupling=json.loads(joined.read_text());library=json.loads(portable.read_text())
for key,path in [('inputHash',inp),('learningHash',learned),('jointGeometryHash',joined)]:assert library[key]==sha(path)
assert coupling['junctionHash']==sha(junction) and j['alternativeHash']==sha(alt)
assert len(library['motifs'])==len(coupling['library']);eps=library['positionToleranceAngstrom'];radius=library['markingRadiusAngstrom'];assert radius==2*eps
assert len(library['baseMotifs'])==len(d['types'])
for base,typ in zip(library['baseMotifs'],d['types']):
    assert set(base)=={'kind','anchors','t','scalarM'} and base['kind']==typ['kind'] and base['anchors']==typ['positions']
    roles=r['roleOfSite'][typ['offset']:typ['offset']+len(typ['positions'])]
    assert base['t']==[r['weightsByRole'][u] for u in roles] and base['scalarM']==[r['scalarLabelsByRole'][u] for u in roles]
spec=importlib.util.spec_from_file_location('cloud',Path(__file__).with_name('portable-cloud-markings.py'))
cloud=importlib.util.module_from_spec(spec);spec.loader.exec_module(cloud)
for motif,entry in zip(library['motifs'],coupling['library']):
    assert set(motif)=={'pairType','anchors','t','scalarM','cloudM'}
    assert motif['pairType']==entry['key'][0] and motif['anchors']==[[0.,0.,0.],entry['vectors'][0]]
    typ=d['types'][motif['pairType']];roles=r['roleOfSite'][typ['offset']:typ['offset']+2]
    assert motif['t']==[r['weightsByRole'][u] for u in roles] and motif['scalarM']==[r['scalarLabelsByRole'][u] for u in roles]
    for side in range(2):
        mark=motif['cloudM'][side];assert set(mark)=={'vectors','colors'}
        selected=[(v,c) for v,c in zip(entry['vectors'],entry['colors']) if c[0]==side]
        assert mark['colors']==[c[1:] for v,c in selected]
        assert np.max(np.abs(np.array(mark['vectors'])-(np.array([v for v,c in selected])-side*np.array(entry['vectors'][0]))))<1e-12

rotation=np.array([[0.,0.,1.],[1.,0.,0.],[0.,1.,0.]])
checks=[];maximum=0.;anchor_max=0.
for f,cfg in enumerate(d['configurations']):
    nodes={n['point']:n for n in j['folds'][f]['nodes']};edges=coupling['folds'][f]['edges']
    covers=[r['selected'][f]]+[x['selected'] for x in a['runs'] if x['fold']==f]
    assignments_checked=0;common_checked=0;rotated_checked=0;discovered=0;unknown=0
    for record in covers:
        chosen=set(record);states={};witnesses={};assignments=defaultdict(list)
        for p,n in nodes.items():
            selected=[e for e in n['incident'] if e['candidate'] in chosen]
            states[p]=next(i for i,s in enumerate(n['states']) if set(s['candidates'])=={e['candidate'] for e in selected})
            witnesses[p]={'vectors':[e['vector'] for e in selected],'colors':[e['color'] for e in selected]}
        for edge in edges:
            if edge['candidate'] not in chosen:continue
            pair=[states[p] for p in edge['points']];index=edge['allowedPresentStates'].index(pair)
            fit=edge['geometricWitnesses'][index];motif=library['motifs'][fit['template']]
            p,q=edge['points'];delta=np.array(next(e['vector'] for e in nodes[p]['incident'] if e['candidate']==edge['candidate']))
            registered=np.array(motif['anchors'][1])@np.array(fit['rotationRow']);err=float(np.linalg.norm(registered-delta));assert err<=eps+1e-8;anchor_max=max(anchor_max,err)
            for side,point in enumerate((p,q)):
                mark=cloud.transform(motif['cloudM'][side],fit['rotationRow'])
                assignments[point].append(mark);assignments_checked+=1
        for p,marks in assignments.items():
            fits=cloud.common_witness(marks,witnesses[p],radius);assert fits is not None
            maximum=max(maximum,max(x['maxResidual'] for x in fits));common_checked+=1
            assert cloud.common_witness([cloud.transform(m,rotation) for m in marks],cloud.transform(witnesses[p],rotation),radius) is not None
            rotated_checked+=1
            proposal=cloud.propose_common_witness(marks,radius)
            if proposal['status']=='verified-witness':
                assert cloud.common_witness(marks,proposal['witness'],radius) is not None;discovered+=1
            else:unknown+=1
    checks.append({'file':cfg['file'],'trainingRecords':len(covers),'endpointAssignments':assignments_checked,'commonWitnessChecks':common_checked,'rotatedCommonWitnessChecks':rotated_checked,'consensusDiscoveredWithoutTargetCloud':discovered,'consensusUnknown':unknown})
result={'scope':__doc__,'portableHash':sha(portable),'jointGeometryHash':sha(joined),'junctionHash':sha(junction),'motifs':len(library['motifs']),'markingRadiusAngstrom':radius,'maxMarkingResidualAngstrom':maximum,'maxAnchorRegistrationResidualAngstrom':anchor_max,'checks':checks,
        'sourceHashes':{name:sha(Path(__file__).with_name(name)) for name in ['portable-cloud-markings.py','export-portable-junctions.py','verify-portable-junctions.py','test-portable-cloud-markings.py']},
        'limits':'Checks both supplied training-neighborhood witnesses and proposals using assignments alone. Placements still come from known-coordinate registrations. No independent generalization, pose completeness, or new search reconstruction is established.'}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
