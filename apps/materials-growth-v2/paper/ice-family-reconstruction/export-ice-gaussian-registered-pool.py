"""Ice all assigned-base registered placements, without a selected cover.

Finite dictionary registrations only, not complete continuous-pose enumeration.
Unsupported assigned registrations are reported, not silently filled from
the known decomposition or omitted from the atomic target.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.distance import cdist
libp,transferp,coverp,dictp,out=map(Path,sys.argv[1:6])
cid=sys.argv[6] if len(sys.argv)>6 else 'c01400'
lib,transfer,cover,dictionary=[json.loads(p.read_text()) for p in [libp,transferp,coverp,dictp]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert lib['sourceHashes']['cover']==sha(coverp) and lib['sourceHashes']['dictionary']==sha(dictp) and transfer['libraryHash']==sha(libp)
row=next(r for r in dictionary['configurations'] if r['id']==cid);cv=next(r for r in cover['results'] if r['id']==cid)
allowed={s['motif'] for r in lib['trainingRegistrations'] if r['id'] in transfer['fitFrames'] for s in r['selected']};bybase=defaultdict(list)
for i in sorted(allowed):bybase[lib['motifs'][i]['base']].append(i)
bases={(b['pairType'],tuple(map(tuple,b['componentSites']))):i for i,b in enumerate(lib['baseMotifs'])}
fields=[];candidates=[];registrations=[];missing=[]
for edge,o in enumerate(row['occurrences']):
    if not o.get('matched'):missing.append(dict(edge=edge,reason='unmatched geometric type'));continue
    atoms=[o['ids'][j] for j in o['permutation']]
    ends=sorted((tuple(j for j,a in enumerate(atoms) if a in cv['components'][root]),root) for root in cv['componentPairs'][edge])
    base=bases.get((o['type'],tuple(s for s,r in ends)))
    if not bybase[base]:missing.append(dict(edge=edge,reason='no fitting decorations for assigned base'));continue
    R=np.asarray(o['rotationRow']);roots=[r for s,r in ends];registrations.append(dict(edge=edge,base=base,roots=roots,rotationRow=o['rotationRow']))
    for i in bybase[base]:
        marks=[]
        for side,root in enumerate(roots):
            f=lib['motifs'][i]['fieldM'][side];x=np.asarray(f['vectors']);a=np.asarray(f['amplitudes']);c=np.asarray(f['colors'])
            norm=float(np.sum(a[:,None]*a[None,:]*np.exp(-cdist(x,x,'sqeuclidean')/(2*f['sigma']**2))*(c[:,None]==c[None,:])))
            marks.append(dict(point=f'm:{root}',field=len(fields)));fields.append(dict(vectors=(x@R).tolist(),amplitudes=f['amplitudes'],colors=f['colors'],sigma=f['sigma'],norm=norm))
        candidates.append(dict(id=f'{edge:06d}:{i:06d}',base=f'edge:{edge}',edge=edge,motif=i,t=[dict(point=f'a:{a}',value=1) for a in o['ids']],m=[],fieldM=marks))
model=dict(capacity=2,required=[f'a:{a}' for a in range(row['atoms'])],complete=True,radius=.6,fields=fields,candidates=candidates)
report=dict(scope=__doc__,sourceHashes={p.name:sha(p) for p in [libp,transferp,coverp,dictp]},codeHash=sha(Path(__file__)),models=[dict(id=cid,model=model)],registrations=registrations,missing=missing,limits='All assigned-base finite registered alternatives, no selected geometric cover. All atom targets remain active. Missing fitting registrations explicit; exhaustion cannot prove continuous-space impossibility. Approximate geometry, developmental radius, inherited half weights and unknown condition provenance.')
with out.open('x') as f:json.dump(report,f,separators=(',',':'))
print(json.dumps(dict(id=cid,registeredPlacements=len(registrations),missing=len(missing),decoratedCandidates=len(candidates),requiredAtoms=row['atoms'])))
