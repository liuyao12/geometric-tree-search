"""Rebuild raw periodic geometry and check registrations and training coverage.

Training selections are used only here, after geometry-only proposal generation.
Accepted fits are checked; omitted approximate poses are not certified impossible.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

inp,folder,portable,registration,learned,alternatives,out=map(Path,sys.argv[1:])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(inp.read_text());p=json.loads(portable.read_text());data=json.loads(registration.read_text());r=json.loads(learned.read_text())['result'];alt=json.loads(alternatives.read_text())
assert data['inputHash']==p['inputHash']==sha(inp) and data['portableHash']==sha(portable)
assert p['learningHash']==alt['learningHash']==sha(learned) and alt['inputHash']==sha(inp)
assert data['sourceHash']==sha(Path(__file__).with_name('register-portable-geometry.py'))
maximum=0.;checked=0;checks=[]
for f,cfg in enumerate(d['configurations']):
    raw=folder/f'{f}-1.15-3.json';assert sha(raw)==cfg['sourceHash'];src=json.loads(raw.read_text());xyz=np.array(src['positions']);cell=np.array(src['cell'])
    at=defaultdict(dict);face=set()
    for cid,o in enumerate(cfg['occurrences']):
        base=p['baseMotifs'][o['type']]
        if base['kind']!='pair':face.update(o['ids']);continue
        a,b=o['ids'];delta=xyz[b]+np.array(o['imageShift'])@cell-xyz[a]
        for side,point in enumerate((a,b)):
            at[point][cid]={'vector':delta*(1 if side==0 else -1),'color':[o['type'],base['t'][side],base['t'][1-side],base['scalarM'][side],base['scalarM'][1-side]]}
    nodes={point:edges for point,edges in at.items() if point not in face}
    expected={cid for cid,o in enumerate(cfg['occurrences']) if len(o['ids'])==2 and all(point in nodes for point in o['ids'])}
    edges=data['folds'][f]['edges'];assert len(edges)==len(expected) and {e['candidate'] for e in edges}==expected
    patterns={};count=0
    for e in edges:
        cid=e['candidate'];occ=cfg['occurrences'][cid];assert e['points']==occ['ids'];left,right=e['points'];delta=nodes[left][cid]['vector'];patterns[cid]=set()
        for fit in e['registrations']:
            motif=p['motifs'][fit['template']];assert motif['pairType']==occ['type'];rot=np.array(fit['rotationRow'])
            assert np.max(np.abs(rot.T@rot-np.eye(3)))<1e-7 and abs(np.linalg.det(rot)-1)<1e-7
            source=[motif['anchors'][1]];target=[delta.tolist()]
            for side,point in enumerate((left,right)):
                selected=fit['selectedArms'][side];assert cid in selected and len(selected)==len(set(selected))
                assert set(selected)<=nodes[point].keys() and len(selected)==len(motif['cloudM'][side]['vectors'])
                assert [nodes[point][i]['color'] for i in selected]==motif['cloudM'][side]['colors']
                assert sum(nodes[point][i]['color'][1] for i in selected)==p['capacity']
                source.extend((np.asarray(motif['cloudM'][side]['vectors'])+side*np.asarray(motif['anchors'][1])).tolist())
                target.extend([(nodes[point][i]['vector']+side*delta).tolist() for i in selected])
            error=float(np.linalg.norm(np.asarray(source)@rot-np.asarray(target),axis=1).max());assert error<=data['epsilonAngstrom']+1e-8
            assert abs(error-fit['residual'])<1e-8;maximum=max(maximum,error);checked+=1;count+=1
            patterns[cid].add(tuple(tuple(sorted(s)) for s in fit['selectedArms']))
    records=[r['selected'][f]]+[v['selected'] for v in alt['runs'] if v['fold']==f];coverage=[]
    for ci,record in enumerate(records):
        chosen=set(record);required=0;missing=[]
        for cid in expected&chosen:
            required+=1;points=cfg['occurrences'][cid]['ids'];pattern=tuple(tuple(sorted(chosen&nodes[point].keys())) for point in points)
            if pattern not in patterns[cid]:missing.append(cid)
        coverage.append({'record':ci,'selectedCoupledEdges':required,'missingRegisteredConnections':len(missing)})
    checks.append({'file':cfg['file'],'candidateEdges':len(edges),'registrationsChecked':count,'distinctLocalConnectionPatterns':sum(len(s) for s in patterns.values()),'trainingCoverage':coverage})
result={'scope':__doc__,'registrationHash':sha(registration),'portableHash':sha(portable),'checkedRegistrations':checked,'maxResidualAngstrom':maximum,'ambiguousOrTruncatedTemplateQueries':data['ambiguousOrTruncatedTemplateQueries'],'checks':checks,
        'allTrainingConnectionsCovered':all(not row['missingRegisteredConnections'] for c in checks for row in c['trainingCoverage']),
        'limits':'No known cover was used by the generator. The learned library is in-sample, base-pair incidence is target-derived, and approximate proposal completeness is not established.'}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
