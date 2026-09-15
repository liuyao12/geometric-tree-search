"""Rebuild base candidates and verify final implicit-junction marking lifts."""
import hashlib
import json
from pathlib import Path
import sys

inp,learned,junction_path,folder,kernel,out=map(Path,sys.argv[1:])
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];junctions=json.loads(junction_path.read_text())
assert junctions['inputHash']==digest(inp) and junctions['learningHash']==digest(learned)
checks=[]
for path in sorted(folder.glob('[0-9]-*.json')):
    run=json.loads(path.read_text());result=run['result'];f=result['fold'];cfg=d['configurations'][f];candidates=[]
    for j,o in enumerate(cfg['occurrences']):
        typ=d['types'][o['type']];ts=[];ms=[]
        for u,p in enumerate(o['ids']):
            role=r['roleOfSite'][typ['offset']+u];ts.append({'point':str(p),'value':r['weightsByRole'][role]})
            label=r['scalarLabelsByRole'][role]
            if label is not None:ms.append({'point':str(p),'channel':'0','lo':label,'hi':label})
        candidates.append({'id':f'{j:06d}','t':ts,'m':ms})
    model={'capacity':r['capacity'],'required':list(map(str,range(cfg['atoms']))),'candidates':candidates}
    assert run['model']==model and run['kernelHash']==digest(kernel) and run['junctionHash']==digest(junction_path)
    for name,value in run['sourceHashes'].items():assert digest(Path(__file__).with_name(name))==value
    ids=result['selected'];assert len(ids)==len(set(ids));chosen=set(map(int,ids));totals=dict.fromkeys(model['required'],0);marks={}
    for j in chosen:
        c=candidates[j]
        for x in c['t']:totals[x['point']]+=x['value']
        for x in c['m']:
            p=x['point'];assert p not in marks or marks[p]==x['lo'];marks[p]=x['lo']
    assert all(v<=r['capacity'] for v in totals.values());complete=all(v==r['capacity'] for v in totals.values())
    assert complete==(result['status']=='exact finite point-cover witness')
    parent={p:p for p in model['required']}
    def root(p):
        while parent[p]!=p:parent[p]=parent[parent[p]];p=parent[p]
        return p
    for j in chosen:
        points=[x['point'] for x in candidates[j]['t']]
        for p in points[1:]:parent[root(p)]=root(points[0])
    components=len({root(p) for p in parent}) if complete else None
    junction_checks=0
    if result['junction']:
        for node in junctions['folds'][f]['nodes']:
            local=chosen&{e['candidate'] for e in node['incident']}
            assert any(local<=set(state['candidates']) for state in node['states'])
            if complete:assert any(local==set(state['candidates']) for state in node['states'])
            junction_checks+=1
    checks.append({'file':cfg['file'],'junction':result['junction'],'complete':complete,'selected':len(ids),'positiveSupportComponents':components,
                   'junctionLiftsChecked':junction_checks,'filledPoints':sum(v==r['capacity'] for v in totals.values())})
assert checks
result={'scope':__doc__,'junctionHash':digest(junction_path),'summaryHash':digest(folder/'summary.json'),'checks':checks}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
