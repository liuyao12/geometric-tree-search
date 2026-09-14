"""Independent reconstruction of coverage, scalar agreement and exact dual proofs.

Does not run the fitting LP or import the learner. The face geometry itself is
verified by verify-boron-face-clusters.py; this checks its use and periodic pairs.
"""
from collections import Counter,defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

def verify(folder,path):
    folder=Path(folder);d=json.loads(Path(path).read_text());raw=(folder/'dictionary.json').read_bytes();base=json.loads(raw)
    assert d['dictionaryHash']==hashlib.sha256(raw).hexdigest();eps=d['epsilonAngstrom']
    offset=0
    for i,t in enumerate(d['types']):
        assert t['id']==i and t['offset']==offset;offset+=len(t['positions'])
        if t['kind']=='finite-face':
            assert t['positions']==base['types'][i]['positions']
            x=np.array(t['positions']);ties=set()
            for w in t['selfFits']:
                p=w['permutation'];assert sorted(p)==list(range(len(x)))
                R=np.array(w['rotationRow']);assert np.max(abs(R.T@R-np.eye(3)))<1e-9 and abs(np.linalg.det(R)-1)<1e-9
                assert max(np.linalg.norm(x@R+w['translation']-x[p],axis=1))<=eps+1e-9
                ties.update(tuple(sorted((a,b))) for a,b in enumerate(p) if a!=b)
            assert sorted(ties)==[tuple(x) for x in t['ties']]
        else:
            assert t['kind']=='pair' and t['ties']==[[0,1]] and t['length']>0
            assert np.allclose(t['positions'],[[-t['length']/2,0,0],[t['length']/2,0,0]])
    config_groups={}
    for c in d['configurations']:
        raw=(folder/f"{c['fold']}-1.15-3.json").read_bytes();src=json.loads(raw)
        assert c['sourceHash']==hashlib.sha256(raw).hexdigest() and c['atoms']==len(src['positions'])
        expected=[]
        for o in base['configurations'][c['fold']]['occurrences']:
            ids=src['components'][o['component']]['ids']
            expected.append((o['type'],tuple(ids[i] for i in o['permutation'])))
        actual=[];pairs=[];groups=[[] for _ in range(c['atoms'])]
        shifts={(a,b):s for a,b,s in src['edgeShifts']}
        for o in c['occurrences']:
            t=d['types'][o['type']];ids=o['ids'];assert len(ids)==len(t['positions']) and len(set(ids))==len(ids)
            if t['kind']=='finite-face':actual.append((o['type'],tuple(ids)))
            else:
                a,b=ids;assert o['imageShift']==shifts[a,b]
                length=np.linalg.norm(np.array(src['positions'][b])+np.array(shifts[a,b])@src['cell']-src['positions'][a])
                assert abs(length-o['length'])<1e-9 and abs(length-t['length'])/2<=eps+1e-9
                pairs.append(tuple(ids))
            for u,p in enumerate(ids):assert 0<=p<c['atoms'];groups[p].append(t['offset']+u)
        assert Counter(actual)==Counter(expected)
        assert Counter(pairs)==Counter(map(tuple,src['fallbackPairs']))
        assert all(groups);config_groups[c['file']]=groups
    passed=obstructions=0
    for r in d['results']:
        groups=[g for f in r['files'] for g in config_groups[f]]
        equations={(tuple(sorted(Counter(g).items())),1) for g in groups}
        active={v for g in groups for v in g}
        ties=[]
        if r['roleTies']:
            for t in d['types']:
                for a,b in t['ties']:
                    a+=t['offset'];b+=t['offset']
                    if a in active and b in active:
                        ties.append((a,b));equations.add((tuple(sorted(((a,1),(b,-1)))),0))
        assert r['requiredPoints']==len(groups) and r['uniqueEquations']==len(equations) and r['activeVariables']==len(active)
        if r['status']=='exact positive finite-quotient precheck passed':
            w=[Fraction(v) if v is not None else None for v in r['weights']];labels=r['labels']
            assert len(w)==offset and all(w[v] is not None and 0<w[v]<=1 for v in active)
            assert all(sum(w[v] for v in g)==1 for g in groups)
            assert all(w[a]==w[b] for a,b in ties)
            assert all(len({labels[v] for v in g})==1 for g in groups)
            assert all(labels[a]==labels[b] for a,b in ties)
            # Independently compute equality components, ruling out invented extra distinctions.
            adjacency=defaultdict(set)
            for group in groups+[list(p) for p in ties]:
                for v in group:adjacency[group[0]].add(v);adjacency[v].add(group[0])
            remaining=set(active);classes=0
            while remaining:
                todo=[remaining.pop()];classes+=1
                while todo:
                    for v in adjacency[todo.pop()] & remaining:remaining.remove(v);todo.append(v)
            assert classes==r['activeScalarClasses']==len({labels[v] for v in active});passed+=1
        elif r['status']=='exact restricted nonnegative filling obstruction':
            totals=defaultdict(Fraction);rhs=Fraction(0)
            for row in r['farkasRows']:
                terms=tuple(map(tuple,row['terms']));assert (terms,row['rhs']) in equations
                y=Fraction(row['multiplier']);rhs+=y*row['rhs']
                for v,c in terms:totals[v]+=y*c
            assert all(v>=0 for v in totals.values()) and rhs<0 and rhs==Fraction(r['farkasRhs']);obstructions+=1
        else:raise AssertionError('Unverified result: '+r['status'])
    out={'verifiedPositiveFits':passed,'verifiedExactObstructions':obstructions,'types':len(d['types']),
         'pairTypes':sum(t['kind']=='pair' for t in d['types']),'variables':offset,
         'results':[ {k:v for k,v in r.items() if k not in ('weights','labels','farkasRows')} for r in d['results']],
         'scope':'All-occurrences training diagnostic; not held-out transfer or growth.'}
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':
    out=verify(*sys.argv[1:3])
    if len(sys.argv)>3:
        with Path(sys.argv[3]).open('x') as f:json.dump(out,f,indent=2)
