"""Independent atom-incidence and exact GF(2) verification of the cover challenge.

Reconstruct equations from actual pointwise motif markings, not saved cycle rows.
Uses dense boolean reduced row elimination, independent of the generator's
integer-bitset echelon solver and MILP optimizer. No SciPy optimizer is used.
"""
import hashlib
import json
from pathlib import Path
from collections import defaultdict, Counter
import sys
import numpy as np


def equations(c, selected, m, types):
    assert len(selected)==len(set(selected))
    totals=Counter();adj=defaultdict(list);index={ti:i for i,ti in enumerate(types)}
    for i in selected:
        o=c['occurrences'][int(i)];assert o['matched'] and o['type'] in index
        assert len(set(o['ids']))==len(o['ids'])
        totals.update(o['ids'])
        entries=[(o['ids'][j],m['ports'][str(o['type'])][u]) for u,j in enumerate(o['permutation'])]
        a,x=entries[0]
        for b,y in entries[1:]:
            bit=(1<<index[o['type']]) if x!=y else 0
            adj[a].append((b,bit));adj[b].append((a,bit))
    assert set(totals)==set(range(c['atoms'])) and set(totals.values())=={2}
    potentials={};rows=set();components=0
    for root in range(c['atoms']):
        if root in potentials:continue
        components+=1;potentials[root]=0;queue=[root]
        for a in queue:
            for b,delta in adj[a]:
                implied=potentials[a]^delta
                if b not in potentials:potentials[b]=implied;queue.append(b)
                else:rows.add(potentials[b]^implied)
    return rows-{0},components


def rref(rows,n):
    A=np.array([[(row>>i)&1 for i in range(n)] for row in sorted(set(rows)-{0})],dtype=bool).reshape(-1,n)
    rank=0
    for col in range(n):
        choices=np.flatnonzero(A[rank:,col])
        if not len(choices):continue
        pivot=rank+choices[0];A[[rank,pivot]]=A[[pivot,rank]]
        others=np.flatnonzero(A[:,col]);others=others[others!=rank]
        A[others]^=A[rank];rank+=1
    return A[:rank]


def verify(dictionary, marking, challenge, validation, selection):
    raw=Path(dictionary).read_bytes();d=json.loads(raw);mr=Path(marking).read_bytes();m=json.loads(mr)
    cr=Path(challenge).read_bytes();r=json.loads(cr);types=sorted(m['admittedTypes']);index={ti:i for i,ti in enumerate(types)}
    assert r['dictionaryHash']==m['dictionaryHash']==hashlib.sha256(raw).hexdigest()
    assert r['coverHash']==d['coverHash'] and r['markingHash']==hashlib.sha256(mr).hexdigest()
    byid={c['id']:c for c in d['configurations']};rows=set();groups=defaultdict(Counter)
    def mask(row):return sum(1<<index[ti] for ti in row)
    for row in m['rows']:rows.add(mask(row['oddMultiplicityTypes']))
    expected={(c['id'],seed) for c in d['configurations'] if c['training'] for seed in range(3)}
    assert {(v['id'],v['seed']) for v in r['results']}==expected and len(r['results'])==len(expected)
    refit=r['refitContrasts'];assert set(refit)==set(map(str,types)) and set(refit.values())<={0,1}
    chosen=mask([ti for ti in types if refit[str(ti)]])
    for v in r['results']:
        c=byid[v['id']];assert c['training'] and v['status']=='exact degree-two cover'
        local,components=equations(c,v['selected'],m,types);rows.update(local)
        assert components==len(v['cycleLengths'])
        old=all(row.bit_count()%2==0 for row in local)
        assert old==v['oldBinaryLiftable'] and all((row&chosen).bit_count()%2==0 for row in local)
        assert old or components>1
        a=groups['trainingAlternatives'];a['covers']+=1;a['oldBinaryRejected']+=not old;a['connected']+=components==1
    assert r['summary']=={'attempted':len(expected),'exactCovers':groups['trainingAlternatives']['covers'],
                          'oldBinaryRejected':groups['trainingAlternatives']['oldBinaryRejected'],
                          'connectedCovers':groups['trainingAlternatives']['connected']}
    A=rref(rows,len(types));B=rref([mask(row) for row in r['contrastRows']],len(types))
    assert np.array_equal(A,B) and len(A)==r['rank'] and len(types)-len(A)==r['nullity']
    forced=sorted(types[int(np.flatnonzero(row)[0])] for row in A if np.count_nonzero(row)==1)
    assert forced==r['forcedZeroTypes']
    assert all((row&chosen).bit_count()%2==0 for row in rows)
    # Enumerate all 2^nullity solutions to independently certify the contrast
    # optimum. This verification remains deliberately bounded.
    assert r['nullity']<=20
    pivots=[int(np.flatnonzero(row)[0]) for row in A];free=sorted(set(range(len(types)))-set(pivots))
    maximum=0
    for assignment in range(1<<len(free)):
        values=np.zeros(len(types),dtype=bool)
        for i,col in enumerate(free):values[col]=bool((assignment>>i)&1)
        for row,pivot in zip(A,pivots):values[pivot]=np.count_nonzero(row&values)%2
        assert not np.any((A.astype(int)@values.astype(int))%2)
        maximum=max(maximum,int(np.count_nonzero(values)))
    assert maximum==sum(refit.values())==r['refitContrastingTypes']
    vd=json.loads(Path(validation).read_text());vs=json.loads(Path(selection).read_text())
    assert vd['sourceDictionaryHash']==m['dictionaryHash'];vbyid={c['id']:c for c in vd['configurations']}
    assert len(vs['results'])==len(vbyid) and {v['id'] for v in vs['results']}==set(vbyid)
    for v in vs['results']:
        c=vbyid[v['id']];assert not c['training'] and v['status']=='connected positive finite cover'
        local,components=equations(c,v['selected'],m,types);assert components==1
        a=groups['validationSelectedCovers'];a['covers']+=1
        a['oldBinaryRejected']+=any(row.bit_count()%2 for row in local)
        a['refitRejected']+=any((row&chosen).bit_count()%2 for row in local)
    return {'challengeHash':hashlib.sha256(cr).hexdigest(),'groups':dict(groups),'verifiedRank':len(A),
            'verifiedNullity':len(free),'verifiedForcedZeroTypes':len(forced),'exhaustiveContrastMaximum':maximum,
            'scope':__doc__,'interpretation':'Training decomposition sensitivity; not a physical falsification or blind-growth test.'}


if __name__=='__main__':
    out=verify(*sys.argv[1:6])
    with Path(sys.argv[6]).open('x') as f:json.dump(out,f,indent=2)
    if len(sys.argv)>7:
        m=json.loads(Path(sys.argv[2]).read_text());r=json.loads(Path(sys.argv[3]).read_text())
        export={k:m[k] for k in ('dictionaryHash','admittedTypes','ports')}
        export.update(contrasts=r['refitContrasts'],challengeHash=out['challengeHash'],
                      scope='Binary contrast refit on original and alternative training decompositions. Learned restricted hypothesis; no physical rule.')
        with Path(sys.argv[7]).open('x') as f:json.dump(export,f)
    print(json.dumps(out,indent=2))
