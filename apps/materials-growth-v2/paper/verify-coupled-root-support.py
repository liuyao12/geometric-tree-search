"""Independent necessary-support propagation using verified conservative adjacency.

No cloud-distance calculation: an empty domain even in this larger adjacency
model certifies failure of the declared finite paired model, not the material.
"""
import hashlib
import json
from pathlib import Path
import sys

directory, output = map(Path,sys.argv[1:])
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for phase in ['Ih','II','VI']:
    path=directory/phase
    data=read(path/'filtered.json'); index=read(path/'index.json'); check=read(path/'index-check.json')
    assert check['indexHash']==sha(path/'index.json')
    assert check['blocksHash']==index['blocksHash']==sha(path/'filtered.json')
    for model, graph in zip(data['models'],index['models'],strict=True):
        assert model['file']==graph['file'] and model['capacity']==2
        blocks=model['blocks']; record_id={tuple(r):i for i,r in enumerate(graph['records'])}
        candidates=[]; owners={}
        for bi,b in enumerate(blocks):
            assert all(t['value']==1 for t in b['t'])
            right={c['sourceCandidate']:j for j,c in enumerate(b['endpointChoices'][1])}
            assert len(right)==len(b['endpointChoices'][1])
            for i,c in enumerate(b['endpointChoices'][0]):
                if c['sourceCandidate'] not in right:continue
                j=right[c['sourceCandidate']];ends=[record_id[bi,0,i],record_id[bi,1,j]]
                ci=len(candidates);candidates.append((bi,ends))
                for endpoint in ends:
                    assert endpoint not in owners;owners[endpoint]=ci
        # Establish that each marking anchor requires exactly two incident
        # placements in any full filling, using a positive-support witness.
        for point in {p for b in blocks for p in b['markPoints']}:
            incident={i for i,b in enumerate(blocks) if point in b['markPoints']}
            assert any({i for i,b in enumerate(blocks) if any(t['point']==p for t in b['t'])}==incident for p in model['required'])
        adjacency=[]
        for ci,(bi,ends) in enumerate(candidates):
            adjacency.append([])
            for side,e in enumerate(ends):
                supported=set()
                for other in graph['neighbors'][e]:
                    if other not in owners:continue
                    cj=owners[other];bj=candidates[cj][0];_,os,_=graph['records'][other]
                    assert blocks[bi]['markPoints'][side]==blocks[bj]['markPoints'][os]
                    if blocks[bi]['inventory']!=blocks[bj]['inventory']:supported.add(cj)
                adjacency[-1].append(supported)
        live=set(range(len(candidates)));passes=0
        while True:
            removed={i for i in live if any(not (partners&live) for partners in adjacency[i])}
            if not removed:break
            live-=removed;passes+=1
        covered={t['point'] for i in live for t in blocks[candidates[i][0]]['t']}
        dead=sorted(set(model['required'])-covered)
        rows.append(dict(phase=phase,file=model['file'],initialPairs=len(candidates),remainingPairs=len(live),
                         passes=passes,deadRequiredPoints=dead,restrictedRootFailureCertified=bool(dead),
                         blocksHash=sha(path/'filtered.json'),indexHash=sha(path/'index.json'),indexCheckHash=sha(path/'index-check.json')))
report=dict(scope=__doc__,results=rows,codeHash=sha(Path(__file__)),
            limits='Relies on separately verified complete conservative index and prior factorized preprocessing. No conclusion from a nonempty fixed point. Does not certify floating-point geometric exactness or impossibility outside the paired finite learned hypothesis.')
with output.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps([dict(phase=r['phase'],file=r['file'],initial=r['initialPairs'],remaining=r['remainingPairs'],dead=len(r['deadRequiredPoints'])) for r in rows]))
