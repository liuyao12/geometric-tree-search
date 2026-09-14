"""Exact pairwise t/m redundancy audit in the fixed observed candidate pool."""
from collections import defaultdict
from itertools import combinations
import hashlib
import json
import sys
from pathlib import Path


def audit(d,r):
    results=[]
    for cfg in d['configurations']:
        points=defaultdict(list);values=[]
        for i,o in enumerate(cfg['occurrences']):
            ts={}
            for u,p in enumerate(o['ids']):
                role=r['roleOfSite'][d['types'][o['type']]['offset']+u]
                t=r['weightsByRole'][role];m=r['scalarLabelsByRole'][role]
                assert p not in ts and 0<t<=r['capacity']
                ts[p]=(t,m);points[p].append((i,m))
            values.append(ts)
        conflicts=defaultdict(list)
        for p,group in points.items():
            for (i,a),(j,b) in combinations(group,2):
                if a is not None and b is not None and a!=b:
                    conflicts[i,j].append(p)
        blocked=[];surviving=[]
        for (i,j),sites in sorted(conflicts.items()):
            overflow=next((p for p in values[i].keys()&values[j].keys()
                           if values[i][p][0]+values[j][p][0]>r['capacity']),None)
            row={'candidates':[i,j],'markConflictPoints':sites}
            if overflow is None:surviving.append(row)
            else:blocked.append({**row,'capacityWitness':overflow})
        results.append({'file':cfg['file'],'conflictingPairs':len(conflicts),
                        'capacityBlockedPairs':len(blocked),'capacityCompatiblePairs':len(surviving),
                        'redundancyWitnesses':blocked,'survivingPairs':surviving})
    return {'scope':'Fixed finite observed pool, scalar exact labels on atom sites; pairwise redundancy is not general geometric transfer.',
            'results':results}


if __name__=='__main__':
    inp,learned,dest=map(Path,sys.argv[1:])
    d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result']
    out=audit(d,r);out['inputHash']=hashlib.sha256(inp.read_bytes()).hexdigest();out['learningHash']=hashlib.sha256(learned.read_bytes()).hexdigest()
    dest.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in row.items() if k not in ('redundancyWitnesses','survivingPairs')} for row in out['results']],indent=2))
