"""Four fixed-cover decoration-search controls; no saved decoration is preferred."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.distance import cdist
libp,transferp,pairp,dictp,out=map(Path,sys.argv[1:])
lib,transfer,pair,dictionary=[json.loads(p.read_text()) for p in [libp,transferp,pairp,dictp]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert pair['sourceHashes'][libp.name]==sha(libp) and pair['sourceHashes'][transferp.name]==sha(transferp) and pair['sourceHashes'][dictp.name]==sha(dictp)
dd={c['id']:c for c in dictionary['configurations']};allowed={s['motif'] for r in lib['trainingRegistrations'] if r['id'] in transfer['fitFrames'] for s in r['selected']};bybase=defaultdict(list)
for i in sorted(allowed):bybase[lib['motifs'][i]['base']].append(i)
models=[]
for cid in ['c00400','c00900','c01400','c01900']:
    row=next(r for r in pair['results'] if r['id']==cid);fields=[];candidates=[];required=set()
    for s in row['selected']:
        edge=s['edge'];ids=dd[cid]['occurrences'][edge]['ids'];required.update(f'a:{a}' for a in ids);R=np.asarray(s['rotationRow'])
        for i in bybase[lib['motifs'][s['motif']]['base']]:
            marks=[]
            for side,root in enumerate(s['roots']):
                f=lib['motifs'][i]['fieldM'][side];x=np.asarray(f['vectors']);a=np.asarray(f['amplitudes']);c=np.asarray(f['colors'])
                norm=float(np.sum(a[:,None]*a[None,:]*np.exp(-cdist(x,x,'sqeuclidean')/(2*f['sigma']**2))*(c[:,None]==c[None,:])))
                marks.append(dict(point=f'm:{root}',field=len(fields)));fields.append(dict(vectors=(x@R).tolist(),amplitudes=f['amplitudes'],colors=f['colors'],sigma=f['sigma'],norm=norm))
            candidates.append(dict(id=f'{edge:06d}:{i:06d}',base=f'edge:{edge}',edge=edge,motif=i,t=[dict(point=f'a:{a}',value=1) for a in ids],m=[],fieldM=marks))
    models.append(dict(id=cid,model=dict(capacity=2,required=sorted(required),complete=True,radius=.6,fields=fields,candidates=candidates)))
report=dict(scope=__doc__,sourceHashes={p.name:sha(p) for p in [libp,transferp,pairp,dictp]},codeHash=sha(Path(__file__)),models=models,limits='Known geometric decomposition and poses supplied; all fitting decorations per base enumerated jointly. Complete only for this finite registered model. Radius selected developmentally; no blind growth or full geometric reconstruction.')
with out.open('x') as f:json.dump(report,f,separators=(',',':'))
print([(m['id'],len(m['model']['candidates'])) for m in models])
