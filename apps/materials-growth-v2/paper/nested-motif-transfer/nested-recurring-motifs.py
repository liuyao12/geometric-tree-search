"""Learn a multiscale geometric dictionary before choosing a disjoint cover.

All non-root, non-singleton single-linkage nodes are proposals. Retain types
seen in at least two fitting frames; choose a tree cut minimizing unmatched
atoms, then number of pieces. No element-specific geometry or molecule size.
This is a motif proposal experiment, not joint anchor/t/m learning or growth.
"""
import hashlib, importlib.util, json, sys
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
from ase import Atoms
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    coordp,metap,out=map(Path,sys.argv[1:])
    spec=importlib.util.spec_from_file_location('rigid',Path(__file__).with_name('bounded-rigid-registration.py'))
    rigid=importlib.util.module_from_spec(spec);spec.loader.exec_module(rigid)
    corpus=json.loads(coordp.read_text())['configurations'];metadata=json.loads(metap.read_text())['configurations']
    training={r['id'] for r in metadata if r['split']=='train'}
    types=[];rows=[];usage=defaultdict(set);index=defaultdict(list);nodes_searched=0;stops=0;epsilon=.15
    for ci,c in enumerate(sorted(corpus,key=lambda c:(c['id'] not in training,c['id']))):
        a=Atoms(c['species'],positions=c['positions'],cell=c['cell'],pbc=c['pbc']);n=len(a)
        vectors=a.get_all_distances(mic=True,vector=True);dist=np.linalg.norm(vectors,axis=2)
        tree=linkage(squareform(dist,checks=False),method='single');members={i:[i] for i in range(n)};children={};proposals=[]
        for k,(u,v,d,size) in enumerate(tree):
            node=n+k;u=int(u);v=int(v);members[node]=members[u]+members[v];children[node]=(u,v)
            if node==2*n-2:continue
            ids=sorted(members[node],key=lambda i:(c['species'][i],i));species=tuple(c['species'][i] for i in ids)
            lifted={ids[0]:np.asarray(c['positions'][ids[0]],dtype=float)};pending=set(ids[1:])
            while pending:
                _,uu,vv=min((dist[uu,vv],uu,vv) for uu in lifted for vv in pending)
                lifted[vv]=lifted[uu]+vectors[uu,vv];pending.remove(vv)
            Y=np.asarray([lifted[i] for i in ids]);center=Y.mean(axis=0)
            descriptor=np.sort(np.linalg.norm(Y[:,None]-Y[None,:],axis=2)[np.triu_indices(len(ids),1)])
            found=None
            for ti in index[species]:
                if c['id'] not in training and len(usage[ti])<2:continue
                t=types[ti]
                if np.max(np.abs(np.asarray(t['descriptor'])-descriptor))>2*epsilon+1e-9:continue
                fit,stats=rigid.fit(t['positions'],Y,species,epsilon)
                nodes_searched+=stats['nodes'];stops+=stats['truncated']
                if fit is not None:found=(ti,fit);break
            if found is None and c['id'] in training:
                ti=len(types);types.append(dict(species=list(species),positions=(Y-center).tolist(),descriptor=descriptor.tolist(),sourceConfiguration=c['id'],sourceIds=ids));index[species].append(ti)
                found=(ti,dict(permutation=list(range(len(ids))),rotationRow=np.eye(3).tolist(),translation=center.tolist(),residual=0.))
            if found and c['id'] in training:usage[found[0]].add(c['id'])
            proposals.append(dict(node=node,ids=ids,matched=found is not None,type=found[0] if found else None,fit=found[1] if found else None))
        rows.append(dict(id=c['id'],training=c['id'] in training,atoms=n,children=children,proposals=proposals))
        if ci%40==0:print(json.dumps(dict(frames=ci+1,types=len(types),registrationNodes=nodes_searched)),flush=True)
    for row in rows:
        candidates={p['node']:p for p in row['proposals'] if p['matched'] and len(usage[p['type']])>=2}
        n=row['atoms']
        def cut(node):
            if node<n:return (1,1),[dict(node=node,ids=[node],matched=False,type=None,fit=None)]
            left,right=row['children'][node];a,aa=cut(left);b,bb=cut(right);cost=(a[0]+b[0],a[1]+b[1]);selected=aa+bb
            if node in candidates and (0,1)<cost:return (0,1),[candidates[node]]
            return cost,selected
        cost,selected=cut(2*n-2);row['clusters']=selected;row['unmatchedAtoms']=cost[0]
    report=dict(scope=__doc__,coordinateHash=sha(coordp),metadataHash=sha(metap),codeHash=sha(Path(__file__)),rigidHelperHash=sha(Path(__file__).with_name('bounded-rigid-registration.py')),
                epsilonAngstrom=epsilon,minimumTrainingFrames=2,types=types,rows=rows,trainingFrameUsage={str(k):len(v) for k,v in usage.items()},registrationNodes=nodes_searched,registrationBudgetStops=stops,
                limits='Frozen greedy library and hierarchy-constrained cover, not GCTS search. Non-singleton supports must recur in fitting frames. Atom sites and single-linkage proposal trees remain prescribed; no learned t/m, no connection restrictions, no proof of continuous-pose completeness. No condition-matched or trajectory-independent claim. Evaluation outcomes must not be used to tune this dictionary.')
    with out.open('x') as f:json.dump(report,f)
    mm={r['id']:r for r in metadata}
    for phase in sorted({r['phase'] for r in metadata}):
        rr=[r for r in rows if not r['training'] and mm[r['id']]['phase']==phase]
        print(json.dumps(dict(phase=phase,frames=len(rr),fullyMatched=sum(r['unmatchedAtoms']==0 for r in rr),unmatchedAtoms=sum(r['unmatchedAtoms'] for r in rr),selectedSizes=dict(Counter(len(s['ids']) for r in rr for s in r['clusters'])))),flush=True)
if __name__=='__main__':main()
