"""Independent exact dual proof and complete marking-conflict coverage checker."""
import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path


def dual(columns, capacity, pair, row):
    y={p:F(v) for p,v in row['y']};z={j:F(v) for j,v in row['z']}
    assert len(y)==len(row['y']) and len(z)==len(row['z'])
    domain={p for col in columns for p in col}
    assert set(y)<=domain and set(z)<=set(range(len(columns)))
    assert all(v>=0 for v in z.values())
    for j,col in enumerate(columns):
        assert sum(y.get(p,F(0))*weight for p,weight in col.items())+z.get(j,F(0)) >= int(j in pair)
    bound=capacity*sum(y.values())+sum(z.values())
    assert bound==F(row['bound']) and bound<2
    return bound


if __name__=='__main__':
    inp,learned,proofpath,dest=map(Path,sys.argv[1:])
    d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];proof=json.loads(proofpath.read_text())
    assert proof['inputHash']==hashlib.sha256(inp.read_bytes()).hexdigest()
    assert proof['learningHash']==hashlib.sha256(learned.read_bytes()).hexdigest()
    lookup={(v['fold'],tuple(v['candidates'])):v for v in proof['results']}
    assert len(lookup)==len(proof['results'])
    checked=set();results=[];mutations=0
    for fold,cfg in enumerate(d['configurations']):
        columns=[];marks=[];incidence=[[] for _ in range(cfg['atoms'])]
        for j,o in enumerate(cfg['occurrences']):
            col={};m={}
            for u,p in enumerate(o['ids']):
                role=r['roleOfSite'][d['types'][o['type']]['offset']+u]
                col[p]=r['weightsByRole'][role];m[p]=r['scalarLabelsByRole'][role];incidence[p].append(j)
            columns.append(col);marks.append(m)
        conflicts=set()
        for p,ids in enumerate(incidence):
            for i in ids:
                for j in ids:
                    if i<j and marks[i][p] is not None and marks[j][p] is not None and marks[i][p]!=marks[j][p]:conflicts.add((i,j))
        direct=0;certified=0
        for pair in sorted(conflicts):
            i,j=pair
            if any(v+columns[j].get(p,0)>r['capacity'] for p,v in columns[i].items()):
                direct+=1;continue
            key=(fold,pair);row=lookup[key]
            assert row['status']=='exact LP certificate: pair cannot complete'
            dual(columns,r['capacity'],pair,row);checked.add(key);certified+=1
            for bad in ({**row,'y':[],'z':[]},{**row,'bound':'0'}):
                try:dual(columns,r['capacity'],pair,bad)
                except AssertionError:mutations+=1
                else:raise AssertionError('invalid proof accepted')
        results.append({'file':cfg['file'],'allMarkConflictingPairs':len(conflicts),
                        'directCapacityProofs':direct,'exactDualProofs':certified,
                        'allMarkConflictsExcludedByUnmarkedExactFilling':direct+certified==len(conflicts)})
    assert checked==set(lookup)
    out={'scope':'Complete conflict coverage for these fixed finite t/m candidate models only; no transfer or infinite-growth theorem.',
         'proofHash':hashlib.sha256(proofpath.read_bytes()).hexdigest(),
         'mutationRejections':mutations,'results':results}
    dest.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
