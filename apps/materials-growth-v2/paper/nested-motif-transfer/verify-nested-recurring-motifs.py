"""Independent positive-pose, recurrence and hierarchy-cut replay.

Does not certify exhaustive rigid registration or scientific usefulness.
"""
import hashlib,json,sys
from pathlib import Path
from collections import defaultdict,Counter
import numpy as np
from ase.geometry import find_mic

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(coordp,metap,resultp):
    result=json.loads(resultp.read_text());cc={c['id']:c for c in json.loads(coordp.read_text())['configurations']};mm={r['id']:r for r in json.loads(metap.read_text())['configurations']}
    assert result['coordinateHash']==sha(coordp) and result['metadataHash']==sha(metap)
    train={r['id'] for r in mm.values() if r['split']=='train'}
    assert len(result['rows'])==len(cc) and {r['id'] for r in result['rows']}==set(cc)
    usage=defaultdict(set);maximum=0.;summary=[]
    for t in result['types']:
        assert t['sourceConfiguration'] in train
        c=cc[t['sourceConfiguration']];ids=t['sourceIds'];X=np.asarray(t['positions']);Y=np.asarray(c['positions'])[ids]
        assert len(set(ids))==len(ids) and len(ids)>1
        assert t['species']==[c['species'][i] for i in ids]
        _,errors=find_mic(X-X[0]-(Y-Y[0]),np.asarray(c['cell']),pbc=c['pbc']);assert max(errors)<1e-8
    for r in result['rows']:
        c=cc[r['id']];n=len(c['positions']);assert r['training']==(r['id'] in train)
        children={int(k):v for k,v in r['children'].items()};assert set(children)==set(range(n,2*n-1))
        sets={i:{i} for i in range(n)}
        for node in range(n,2*n-1):
            a,b=children[node];assert a<node and b<node and not sets[a]&sets[b];sets[node]=sets[a]|sets[b]
        assert sets[2*n-2]==set(range(n))
        assert len(r['proposals'])==n-2 and {p['node'] for p in r['proposals']}==set(range(n,2*n-2))
        for p in r['proposals']:
            assert set(p['ids'])==sets[p['node']] and len(p['ids'])==len(sets[p['node']])
            if not p['matched']:assert p['type'] is None and p['fit'] is None;continue
            t=result['types'][p['type']];fit=p['fit'];perm=fit['permutation'];ids=p['ids']
            assert sorted(perm)==list(range(len(ids))) and len(t['positions'])==len(ids)
            assert [c['species'][ids[i]] for i in perm]==t['species']
            R=np.asarray(fit['rotationRow']);tr=np.asarray(fit['translation'])
            assert abs(np.linalg.det(R)-1)<1e-8 and np.max(np.abs(R.T@R-np.eye(3)))<1e-8
            predicted=np.asarray(t['positions'])@R+tr;target=np.asarray(c['positions'])[np.asarray(ids)[perm]]
            _,errors=find_mic(predicted-target,np.asarray(c['cell']),pbc=c['pbc'])
            assert max(errors)<=result['epsilonAngstrom']+1e-9;maximum=max(maximum,float(max(errors)))
            if r['training']:usage[p['type']].add(r['id'])
    assert {str(k):len(v) for k,v in usage.items()}==result['trainingFrameUsage']
    for r in result['rows']:
        n=r['atoms'];children={int(k):v for k,v in r['children'].items()};proposals={p['node']:p for p in r['proposals']}
        costs={i:(1,1) for i in range(n)}
        for node in range(n,2*n-1):
            a,b=children[node];costs[node]=tuple(costs[a][j]+costs[b][j] for j in range(2))
            p=proposals.get(node)
            if p and p['matched'] and len(usage[p['type']])>=result['minimumTrainingFrames']:costs[node]=min(costs[node],(0,1))
        assert sorted(i for p in r['clusters'] for i in p['ids'])==list(range(n))
        for p in r['clusters']:
            if p['matched']:assert p==proposals[p['node']] and len(usage[p['type']])>=result['minimumTrainingFrames']
            else:assert len(p['ids'])==1 and p['type'] is None
        unmatched=sum(len(p['ids']) for p in r['clusters'] if not p['matched'])
        assert (unmatched,len(r['clusters']))==costs[2*n-2] and unmatched==r['unmatchedAtoms']
    for phase in sorted({m['phase'] for m in mm.values()}):
        rr=[r for r in result['rows'] if not r['training'] and mm[r['id']]['phase']==phase]
        summary.append(dict(phase=phase,frames=len(rr),fullyMatched=sum(r['unmatchedAtoms']==0 for r in rr),unmatchedAtoms=sum(r['unmatchedAtoms'] for r in rr),selectedSizes=dict(Counter(len(p['ids']) for r in rr for p in r['clusters']))))
    shared=[k for k,v in usage.items() if len({mm[i]['phase'] for i in v})>1]
    return dict(resultHash=sha(resultp),coordinateHash=sha(coordp),metadataHash=sha(metap),verifierHash=sha(Path(__file__)),summary=summary,types=len(result['types']),recurringTypes=sum(len(v)>=2 for v in usage.values()),sharedAcrossTrainingPhases=len(shared),sharedTypeSizes=dict(Counter(len(result['types'][k]['species']) for k in shared)),maximumVerifiedErrorAngstrom=maximum,
                limits='Checks source-derived template geometry, every positive periodic pose, training-only recurrence counts, partitions, and cut cost optimality within the recorded hierarchy. Does not certify hierarchy construction, absence of further matches, connection learning, t/m learning, physical conditions or growth.')
if __name__=='__main__':
    coordp,metap,resultp,out=map(Path,sys.argv[1:]);report=verify(coordp,metap,resultp)
    with out.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))
