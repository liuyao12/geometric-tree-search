"""Rank from local overlap contexts in other configurations; never reject.

Context = own motif type plus a multiset of neighboring motif types and shared
symmetry-role pairs. No atom IDs, coordinates, orientation bins, chemistry or
target selected-witness labels are included in the feature. Geometry/weights
still come from the joint six-input model, so this is not held-out model fitting.
"""
from collections import defaultdict,Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


def context_hashes(d,learning):
    roles=learning['result']['roleOfSite'];result=[]
    for c in d['configurations']:
        at=defaultdict(list)
        for i,o in enumerate(c['occurrences']):
            offset=d['types'][o['type']]['offset']
            for u,p in enumerate(o['ids']):at[p].append((i,roles[offset+u]))
        hashes=[]
        for i,o in enumerate(c['occurrences']):
            neighbors=defaultdict(list);offset=d['types'][o['type']]['offset']
            for u,p in enumerate(o['ids']):
                for j,role in at[p]:
                    if i!=j:neighbors[j].append((roles[offset+u],role))
            feature=[o['type'],sorted((c['occurrences'][j]['type'],sorted(pairs)) for j,pairs in neighbors.items())]
            hashes.append(hashlib.sha256(json.dumps(feature,separators=(',',':')).encode()).hexdigest())
        result.append(hashes)
    return result


def fit(d,learning):
    hashes=context_hashes(d,learning);folds=[]
    for target,c in enumerate(d['configurations']):
        counts=Counter();selected=Counter();typecounts=Counter();typeselected=Counter()
        for source,other in enumerate(d['configurations']):
            if source==target:continue
            chosen=set(learning['result']['selected'][source]);assert len(chosen)==len(learning['result']['selected'][source])
            for i,o in enumerate(other['occurrences']):
                h=hashes[source][i];counts[h]+=1;typecounts[o['type']]+=1
                if i in chosen:selected[h]+=1;typeselected[o['type']]+=1
        rows=[];scores=[]
        for i,o in enumerate(c['occurrences']):
            h=hashes[target][i];matched=counts[h]>0
            s,n=(selected[h],counts[h]) if matched else (typeselected[o['type']],typecounts[o['type']])
            rows.append({'contextHash':h,'contextObserved':counts[h],'contextSelected':selected[h],
                         'source':'context' if matched else 'type-fallback','numerator':s+1,'denominator':n+2})
            scores.append(Fraction(s+1,n+2))
        order={v:i for i,v in enumerate(sorted(set(scores)))}
        folds.append({'excluded':target,'file':c['file'],'trainingConfigurations':[i for i in range(len(hashes)) if i!=target],
                      'occurrenceRanks':[order[v] for v in scores],'rows':rows,
                      'matchedContextOccurrences':sum(r['source']=='context' for r in rows),
                      'uniqueTargetContexts':len(set(hashes[target])),'uniqueMatchedContexts':len({r['contextHash'] for r in rows if r['source']=='context'})})
    return folds


if __name__=='__main__':
    raw=Path(sys.argv[1]).read_bytes();lr=Path(sys.argv[2]).read_bytes();d=json.loads(raw);learning=json.loads(lr)
    assert learning['inputHash']==hashlib.sha256(raw).hexdigest()
    out={'scope':__doc__,'inputHash':hashlib.sha256(raw).hexdigest(),'learningHash':hashlib.sha256(lr).hexdigest(),'folds':fit(d,learning)}
    with Path(sys.argv[3]).open('x') as f:json.dump(out,f)
    print(json.dumps([{k:v for k,v in f.items() if k not in ('rows','occurrenceRanks')} for f in out['folds']],indent=2))
