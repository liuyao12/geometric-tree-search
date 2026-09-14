"""Exact symbolic and odd-cycle checks, rebuilding every row from training selections."""
import json
import hashlib
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
import sys

raw=Path(sys.argv[1]).read_bytes();d=json.loads(raw);r=json.loads(Path(sys.argv[2]).read_text())
assert r['dictionaryHash']==hashlib.sha256(raw).hexdigest();rebuilt=[];hashes=[]
for path in sys.argv[4:]:
    b=Path(path).read_bytes();hashes.append(hashlib.sha256(b).hexdigest());chosen={x['id']:x for x in json.loads(b)['results']}
    for c in d['configurations']:
        if not c['training'] or c['id'] not in chosen:continue
        points=defaultdict(list)
        for index in chosen[c['id']]['selected']:
            o=c['occurrences'][index]
            for u,j in enumerate(o['permutation']):points[o['ids'][j]].append(d['offsets'][o['type']]+u)
        assert len(points)==c['atoms'] and all(len(v)==2 for v in points.values())
        for p,v in points.items():rebuilt.append({'sites':v,'configuration':c['id'],'point':p,'witnessSet':len(hashes)-1})
assert hashes==r['selectionHashes'] and rebuilt==r['equations']
adj=defaultdict(set)
for row in rebuilt:
    a,b=row['sites'];adj[a].add(b);adj[b].add(a)
expressions={};membership={};forced=0;free=0
for ci,c in enumerate(r['components']):
    sites=set(c['sites']);assert sites and not(sites&set(expressions))
    reached={min(sites)};todo=list(reached)
    for x in todo:
        assert adj[x]<=sites
        for y in adj[x]:
            if y not in reached:reached.add(y);todo.append(y)
    assert reached==sites
    if c['kind']=='forced-half':
        cycle=c['oddCycle'];assert cycle[0]==cycle[-1] and (len(cycle)-1)%2==1
        assert all(b in adj[a] for a,b in zip(cycle,cycle[1:]))
        assert set(cycle)<=sites
        for x in sites:expressions[x]=(Fraction(1,2),0,None)
        forced+=len(sites)
    else:
        assert c['kind']=='free-complement' and c['oddCycle'] is None
        a=set(c['side0']);b=set(c['side1']);assert not(a&b) and a|b==sites
        for x in a:expressions[x]=(Fraction(0),1,ci)
        for x in b:expressions[x]=(Fraction(1),-1,ci)
        free+=1
    for x in sites:membership[x]=ci
for row in rebuilt:
    a,b=row['sites'];x,y=expressions[a],expressions[b]
    assert membership[a]==membership[b] and x[0]+y[0]==1 and x[1]+y[1]==0 and x[2]==y[2]
assert set(r['unobservedSites'])==set(range(d['offsets'][-1]))-set(expressions)
summary={'siteVariables':d['offsets'][-1],'trainingRows':len(rebuilt),
 'uniqueComplementEdges':len({tuple(sorted(row['sites'])) for row in rebuilt}),
 'forcedHalfSites':forced,'freeComplementSites':len(expressions)-forced,'freeComplementParameters':free,
 'unobservedSites':len(r['unobservedSites']),'totalFreeParameters':free+len(r['unobservedSites'])}
assert summary==r['summary']
out={'verified':True,**summary,'exactArithmetic':'Fractions and affine free parameters in [0,1]',
 'scope':'Complete weight solution family conditional on the supplied degree-two training selections; not unrestricted inverse-tiling learning.'}
with Path(sys.argv[3]).open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
