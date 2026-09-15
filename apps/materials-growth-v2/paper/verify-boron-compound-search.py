"""Rebuild the unchanged marked model and check every saved compound-policy run."""
import hashlib
import json
from pathlib import Path
import sys

inp,learned,compound_path,folder,kernel,out=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];compounds=json.loads(compound_path.read_text())
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert compounds['inputHash']==digest(inp) and compounds['learningHash']==digest(learned)
checks=[]
for fold,cfg in enumerate(d['configurations']):
    candidates=[]
    for j,o in enumerate(cfg['occurrences']):
        typ=d['types'][o['type']];t=[];m=[]
        for u,p in enumerate(o['ids']):
            role=r['roleOfSite'][typ['offset']+u];t.append({'point':str(p),'value':r['weightsByRole'][role]})
            label=r['scalarLabelsByRole'][role]
            if label is not None:m.append({'point':str(p),'channel':'0','lo':label,'hi':label})
        candidates.append({'id':f'{j:06d}','t':t,'m':m})
    expected={'capacity':r['capacity'],'required':list(map(str,range(cfg['atoms']))),'candidates':candidates}
    for policy in ('baseline','cross-compound'):
        run=json.loads((folder/f'{fold}-{policy}.json').read_text());result=run['result']
        assert run['model']==expected and run['kernelHash']==digest(kernel) and run['compoundHash']==digest(compound_path)
        for name,value in run['sourceHashes'].items():assert digest(Path(__file__).with_name(name))==value
        assert result['proposals']==sum(any(s!=fold for s in p['sourceFolds']) for p in compounds['folds'][fold]['proposals'])
        ids=result['selected'];assert len(ids)==len(set(ids));totals=dict.fromkeys(expected['required'],0);marks={}
        for i in ids:
            c=candidates[int(i)];assert c['id']==i
            for x in c['t']:totals[x['point']]+=x['value']
            for x in c['m']:
                p=x['point'];assert p not in marks or marks[p]==x['lo'];marks[p]=x['lo']
        assert all(0<=t<=r['capacity'] for t in totals.values())
        complete=all(t==r['capacity'] for t in totals.values())
        assert complete==(result['status']=='exact finite point-cover witness')
        checks.append({'file':cfg['file'],'policy':policy,'complete':complete,'selected':len(ids),'filledPoints':sum(t==r['capacity'] for t in totals.values())})
result={'scope':__doc__,'compoundHash':digest(compound_path),'summaryHash':digest(folder/'summary.json'),'checks':checks}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'runsVerified':len(checks),'complete':sum(x['complete'] for x in checks)}))
