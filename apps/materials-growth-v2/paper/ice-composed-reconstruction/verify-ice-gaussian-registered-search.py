"""Independent selected geometry/t/field replay without a prescribed cover."""
import hashlib
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
args=list(sys.argv[1:]);loop=bool(args and args[0]=='--loop')
if loop:args.pop(0)
coordp,coverp,dictp,libp,transferp,modelp,resultp,out=map(Path,args)
corpus,cover,dictionary,lib,transfer,result=[json.loads(p.read_text()) for p in [coordp,coverp,dictp,libp,transferp,resultp]]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
assert result['sourceHash']==sha(modelp)
assert lib['sourceHashes']['coordinates']==sha(coordp) and lib['sourceHashes']['cover']==sha(coverp) and lib['sourceHashes']['dictionary']==sha(dictp)
assert transfer['libraryHash']==sha(libp)
allowed={s['motif'] for r in lib['trainingRegistrations'] if r['id'] in transfer['fitFrames'] for s in r['selected']}
cc={r['id']:r for r in corpus['configurations']};cv={r['id']:r for r in cover['results']};dd={r['id']:r for r in dictionary['configurations']}
runs=[dict(id='c01400',enabled=True,selected=result['selected'],status=result['status'])] if loop else result['results']
assert [(r['id'],r['enabled']) for r in runs]==([('c01400',True)] if loop else [('c01400',False),('c01400',True)])
rows=[]
for run in runs:
    cid=run['id'];c=cc[cid];pos=np.asarray(c['positions']);cell=np.asarray(c['cell']);inv=np.linalg.inv(cell);shifts=np.asarray(list(itertools.product(range(-4,5),repeat=3)))@cell;smin=np.linalg.svd(cell,compute_uv=False)[-1]
    def mic(delta):
        x=delta-np.round(delta@inv)@cell;v=x+shifts;best=v[np.argmin(np.linalg.norm(v,axis=1))]
        assert 5*smin-np.linalg.norm(x)>np.linalg.norm(best)+1e-10;return best
    owners=set();totals=np.zeros(len(pos),dtype=int);inc=defaultdict(list);adj=defaultdict(set);maxpos=0.
    for key in run['selected']:
        edge,i=map(int,key.split(':'));assert i in allowed and edge not in owners;owners.add(edge)
        o=dd[cid]['occurrences'][edge];assert o['matched'];b=lib['baseMotifs'][lib['motifs'][i]['base']];assert b['pairType']==o['type'];R=np.asarray(o['rotationRow']);assert np.max(np.abs(R.T@R-np.eye(3)))<1e-10 and abs(np.linalg.det(R)-1)<1e-10
        atoms=[o['ids'][j] for j in o['permutation']];assert b['species']==[c['species'][a] for a in atoms]
        pred=np.asarray(b['anchors'])@R+o['translation'];error=max(np.linalg.norm(mic(pred[j]-pos[a])) for j,a in enumerate(atoms));assert error<=lib['positionToleranceAngstrom']+1e-9;maxpos=max(maxpos,float(error))
        assert b['t']==[1]*len(atoms)
        for a in atoms:totals[a]+=1;assert totals[a]<=2
        roots=[]
        for side,sites in enumerate(b['componentSites']):
            matches=[root for root in cv[cid]['componentPairs'][edge] if {atoms[j] for j in sites}==set(cv[cid]['components'][root])];assert len(matches)==1;root=matches[0];roots.append(root)
            f=lib['motifs'][i]['fieldM'][side];assert f['sigma']==.4;inc[root].append((np.asarray(f['vectors'])@R,np.asarray(f['amplitudes']),f['colors']))
        assert len(set(roots))==2;adj[roots[0]].add(roots[1]);adj[roots[1]].add(roots[0])
    full=bool(np.all(totals==2))
    if not loop:assert full==run['scalarComplete']
    maxfield=0.;bad=0;paircount=0
    for values in inc.values():
        assert len(values)<=2
        if len(values)<2:continue
        a,b=values;x=np.vstack([a[0],b[0]]);w=np.r_[a[1],-b[1]];colors=np.r_[a[2],b[2]];delta=x[:,None,:]-x[None,:,:]
        terms=w[:,None]*w[None,:]*np.exp(-np.sum(delta*delta,axis=2)/.32)*(colors[:,None]==colors[None,:]);sq=math.fsum(map(float,terms.ravel()));assert sq>=-1e-10;dist=math.sqrt(max(0,sq));maxfield=max(maxfield,dist);bad+=dist>1.2+1e-8;paircount+=1
        if run['enabled']:assert dist<=1.2+1e-8
    seen=set();components=0
    for root in adj:
        if root in seen:continue
        components+=1;queue=[root]
        while queue:
            a=queue.pop()
            if a in seen:continue
            seen.add(a);queue.extend(adj[a]-seen)
    if run['status']=='complete-awaiting-independent-replay':assert full
    rows.append(dict(id=cid,enabled=run['enabled'],selectedPlacements=len(owners),complete=full,filledAtoms=int(sum(totals==2)),halfFilledAtoms=int(sum(totals==1)),untouchedAtoms=int(sum(totals==0)),supportComponents=components,maxPositionErrorAngstrom=maxpos,checkedFieldPairs=paircount,incompatiblePairs=bad,maxFieldDistance=maxfield))
report=dict(sourceHashes={p.name:sha(p) for p in [coordp,coverp,dictp,libp,transferp,modelp,resultp]},verifierHash=sha(Path(__file__)),results=rows,limits='Independent numerical replay of selected geometry, integer t, field assignments and connectivity counts. No proof of complete registration enumeration, runtime graph/scheduling, absence of solutions on failure, complete continuous-space growth or same-condition provenance.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(rows),flush=True)
