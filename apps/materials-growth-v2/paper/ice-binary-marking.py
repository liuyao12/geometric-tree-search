"""Restricted binary marking synthesis on the two geometric ports of pair motifs.

Each type has a binary port contrast d; each occurrence may use either globally
flipped marking variant. Selected cycle witnesses require XOR(d along cycle)=0.
Maximize the number of contrasting types. This is a declared hypothesis class,
not unrestricted marking learning or evidence of a physical parity law.
"""
import hashlib
import json
from pathlib import Path
import sys
from collections import Counter
import numpy as np
from scipy.sparse.csgraph import connected_components

raw=Path(sys.argv[1]).read_bytes();d=json.loads(raw);cover=json.loads(Path(sys.argv[2]).read_text());w=json.loads(Path(sys.argv[3]).read_text())
assert w['dictionaryHash']==hashlib.sha256(raw).hexdigest()
forced={i for c in w['components'] if c['kind']=='forced-half' for i in c['sites']}
admitted=[i for i,(a,b) in enumerate(zip(d['offsets'],d['offsets'][1:])) if set(range(a,b))<=forced]
ports={}
for ti in admitted:
    x=np.array(d['types'][ti]['positions']);distance=np.linalg.norm(x[:,None]-x[None,:],axis=2)
    n,labels=connected_components((distance<cover['componentThreshold'])&(distance>0),directed=False)
    assert n==2;ports[str(ti)]=labels.tolist()
byid={c['id']:c for c in d['configurations']};rows=[];hashes=[]
for path in sys.argv[5:]:
    b=Path(path).read_bytes();hashes.append(hashlib.sha256(b).hexdigest())
    for r in json.loads(b)['results']:
        c=byid[r['id']]
        if not c['training']:continue
        assert r['status']=='connected positive finite cover'
        types=[c['occurrences'][i]['type'] for i in r['selected']];assert set(types)<=set(admitted)
        row=sorted(ti for ti,count in Counter(types).items() if count%2)
        rows.append({'configuration':c['id'],'witnessSet':len(hashes)-1,'oddMultiplicityTypes':row,'cycleLength':len(types)})
# All contrasts one reaches the absolute upper bound if feasible. Otherwise this
# simple synthesis attempt fails explicitly; it does not fabricate a solution.
feasible=all(len(row['oddMultiplicityTypes'])%2==0 for row in rows)
out={'scope':__doc__,'dictionaryHash':hashlib.sha256(raw).hexdigest(),'selectionHashes':hashes,
 'admittedTypes':admitted,'ports':ports,'contrasts':{str(ti):1 for ti in admitted} if feasible else None,
 'rows':rows,'allContrastFeasible':feasible,'objectiveUpperBound':len(admitted),'objectiveAttained':len(admitted) if feasible else None,
 'bias':'All selected connected degree-two witnesses have even cycle length; maximal binary contrast may reflect that selection construction rather than material structure.'}
with Path(sys.argv[4]).open('x') as f:json.dump(out,f)
print(json.dumps({k:v for k,v in out.items() if k not in ('ports','contrasts','rows','selectionHashes','admittedTypes')},indent=2))
