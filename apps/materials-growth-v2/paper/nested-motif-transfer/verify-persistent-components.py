"""Independent periodic pose replay and exact partition checks; no score audit."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
import numpy as np
from ase.geometry import find_mic
coordp,metap,resultp,out=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
corpus=json.loads(coordp.read_text());metadata=json.loads(metap.read_text());result=json.loads(resultp.read_text())
assert result['coordinateHash']==sha(coordp) and result['metadataHash']==sha(metap)
cc={c['id']:c for c in corpus['configurations']};mm={r['id']:r for r in metadata['configurations']}
train={r['id'] for r in metadata['configurations'] if r['split']=='train'}
assert set(cc)=={r['id'] for r in result['rows']}
assert all(t['sourceConfiguration'] in train for t in result['types'])
rows=[]
for r in result['rows']:
    c=cc[r['id']];assert r['training']==(r['id'] in train)
    assert sorted(i for s in r['clusters'] for i in s['ids'])==list(range(len(c['positions'])))
    maximum=0.;matched=0
    for s in r['clusters']:
        if not s['matched']:continue
        t=result['types'][s['type']];fit=s['fit'];perm=fit['permutation'];ids=s['ids']
        assert sorted(perm)==list(range(len(ids))) and len(t['positions'])==len(ids)
        assert [c['species'][ids[i]] for i in perm]==t['species']
        R=np.asarray(fit['rotationRow']);tr=np.asarray(fit['translation'])
        assert abs(np.linalg.det(R)-1)<1e-8 and np.max(np.abs(R.T@R-np.eye(3)))<1e-8
        predicted=np.asarray(t['positions'])@R+tr;target=np.asarray(c['positions'])[np.asarray(ids)[perm]]
        _,error=find_mic(predicted-target,np.asarray(c['cell']),pbc=c['pbc'])
        assert max(error)<=result['epsilonAngstrom']+1e-9;maximum=max(maximum,float(max(error)));matched+=1
    rows.append(dict(id=r['id'],phase=mm[r['id']]['phase'],training=r['training'],clusters=len(r['clusters']),matched=matched,fullyMatched=matched==len(r['clusters']),maxMatchedErrorAngstrom=maximum))
summary=[]
for phase in ['alpha','beta']:
    for training in [True,False]:
        group=[r for r in rows if r['phase']==phase and r['training']==training]
        summary.append(dict(phase=phase,training=training,frames=len(group),fullyMatched=sum(r['fullyMatched'] for r in group),matchedClusters=sum(r['matched'] for r in group)))
report=dict(resultHash=sha(resultp),coordinateHash=sha(coordp),verifierHash=sha(Path(__file__)),summary=summary,rows=rows,
            limits='Checks partition coverage and every claimed periodic proper-isometry match. Does not verify optimality of the persistence score, completeness of correspondence search, matching uniqueness, overlap connections or GCTS filling/marking values. Development split, not condition-matched or trajectory-independent validation.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(summary))
