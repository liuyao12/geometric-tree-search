"""Independent replay of registered three-site geometry and positive t/m witnesses.

Does not establish candidate completeness, continuous-pose exhaustion, or LP
infeasibility. Requires the audited coordinate file, not a source phase label.
"""
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np

def verify(source_path, result_path):
    raw=Path(source_path).read_bytes();source=json.loads(raw)
    data=json.loads(Path(result_path).read_text())
    assert hashlib.sha256(raw).hexdigest()==data['inputHash']
    source={c['file']:c for c in source['results']}
    types=data['types'];epsilon=data['epsilonAngstrom'];occurrences=0
    for c in data['configurations']:
        original=source[c['file']];cell=np.array(original['cell']);inv=np.linalg.inv(cell)
        seen=set()
        for o in c['occurrences']:
            ids=o['ids'];assert len(set(ids))==3 and tuple(ids) not in seen;seen.add(tuple(ids))
            lifted=np.array(o['liftedPositions'])
            shifts=(lifted-np.array(original['positions'])[ids])@inv
            assert np.max(np.abs(shifts-np.rint(shifts)))<1e-9
            distances=np.linalg.norm(lifted[:,None]-lifted[None,:],axis=2)
            assert any(sum(distances[a,b]<=c['radius']+1e-9 for b in range(3) if b!=a)==2 for a in range(3))
            R=np.array(o['rotationRow']);assert np.max(np.abs(R.T@R-np.eye(3)))<1e-9
            assert abs(np.linalg.det(R)-1)<1e-9
            assert sorted(o['permutation'])==[0,1,2]
            transformed=np.array(types[o['type']]['positions'])@R+o['translation']
            residual=float(np.max(np.linalg.norm(transformed-lifted[o['permutation']],axis=1)))
            assert residual<=epsilon+1e-9 and abs(residual-o['residual'])<1e-9
            occurrences+=1
    passed=[]
    for r in data['results']:
        if r['status']!='exact finite-quotient precheck passed':continue
        weights=list(map(Fraction,r['weights']));labels=r['labels'];active=set()
        for name in r['configurations']:
            c=next(c for c in data['configurations'] if c['file']==name)
            totals=[Fraction(0)]*c['atoms'];assigned=[set() for _ in totals]
            for o in c['occurrences']:
                for u,p in enumerate(o['permutation']):
                    v=3*o['type']+u;point=o['ids'][p];active.add(v)
                    assert 0<weights[v]<=1
                    totals[point]+=weights[v];assigned[point].add(labels[v])
            assert all(v==1 for v in totals) and all(len(s)==1 for s in assigned)
        for t in types:
            for a,b in t['symmetryTies']:
                assert weights[3*t['id']+a]==weights[3*t['id']+b]
                assert labels[3*t['id']+a]==labels[3*t['id']+b]
        assert len({labels[v] for v in active})==r['activeScalarClasses']
        passed.append(r['configurations'])
    out={'verifiedRegisteredOccurrences':occurrences,'types':len(types),'exactPositiveWitnesses':passed,
         'infeasibilityIndependentlyCertified':False,'blindGrowthTested':False}
    print(json.dumps(out));return out
if __name__=='__main__':verify(sys.argv[1],sys.argv[2])
