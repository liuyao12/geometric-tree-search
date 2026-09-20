"""Irregular hierarchical component proposals and a frozen rigid dictionary.

No atom-centred radius, molecule size, element-specific distance or chemistry
rule. A declared persistence score chooses a disjoint cut of a single-linkage
tree. This is a geometric proposal heuristic, not joint GCTS learning.
"""
import hashlib,importlib.util,itertools,json,math,sys
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from ase import Atoms
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform

coordp,metap,out=map(Path,sys.argv[1:]);epsilon=.15
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('rigid',Path(__file__).with_name('bounded-rigid-registration.py'))
rigid=importlib.util.module_from_spec(spec);spec.loader.exec_module(rigid)
corpus=json.loads(coordp.read_text())['configurations'];metadata=json.loads(metap.read_text())['configurations']
training={r['id'] for r in metadata if r['split']=='train'}
types=[];rows=[];registration_nodes=0;registration_budget_stops=0
for c in sorted(corpus,key=lambda c:(c['id'] not in training,c['id'])):
    a=Atoms(c['species'],positions=c['positions'],cell=c['cell'],pbc=c['pbc']);n=len(a)
    vectors=a.get_all_distances(mic=True,vector=True);dist=np.linalg.norm(vectors,axis=2)
    tree=linkage(squareform(dist,checks=False),method='single')
    members={i:[i] for i in range(n)};birth={i:0. for i in range(n)};children={};parent={}
    for k,(u,v,d,size) in enumerate(tree):
        node=n+k;u=int(u);v=int(v);members[node]=members[u]+members[v];birth[node]=float(d);children[node]=(u,v);parent[u]=parent[v]=node
    root=2*n-2
    def cut(node):
        if node<n:return 0.,[node]
        left,right=children[node];s1,k1=cut(left);s2,k2=cut(right)
        score=(len(members[node])-1)*(birth[parent[node]]-birth[node]) if node!=root else -math.inf
        return (score,[node]) if score>s1+s2+1e-10 else (s1+s2,k1+k2)
    score,nodes=cut(root);selected=[]
    for node in nodes:
        ids=sorted(members[node],key=lambda i:(c['species'][i],i));species=tuple(c['species'][i] for i in ids)
        # Lift through the connected short-distance graph, not independent
        # distances to one arbitrary centre. Record the resulting rigid cloud.
        lifted={ids[0]:np.asarray(c['positions'][ids[0]],dtype=float)};pending=set(ids[1:])
        while pending:
            edges=[(dist[u,v],u,v) for u in lifted for v in pending]
            _,u,v=min(edges);lifted[v]=lifted[u]+vectors[u,v];pending.remove(v)
        Y=np.asarray([lifted[i] for i in ids]);center=Y.mean(axis=0);Y0=Y-center
        found=None
        descriptor=np.sort(np.linalg.norm(Y[:,None,:]-Y[None,:,:],axis=2)[np.triu_indices(len(ids),1)])
        for ti,t in enumerate(types):
            if tuple(t['species'])!=species:continue
            if len(ids)>1 and np.max(np.abs(np.asarray(t['descriptor'])-descriptor))>2*epsilon+1e-9:continue
            fitted,stats=rigid.fit(t['positions'],Y,species,epsilon)
            registration_nodes+=stats['nodes'];registration_budget_stops+=stats['truncated']
            if fitted is not None:found=(ti,fitted);break
        if found is None and c['id'] in training:
            ti=len(types);types.append(dict(species=list(species),positions=Y0.tolist(),descriptor=descriptor.tolist(),sourceConfiguration=c['id'],sourceIds=ids))
            found=(ti,dict(permutation=list(range(len(ids))),rotationRow=np.eye(3).tolist(),translation=center.tolist(),residual=0.))
        selected.append(dict(ids=ids,birth=birth[node],death=birth[parent[node]] if node!=root else None,
                             matched=found is not None,type=found[0] if found else None,fit=found[1] if found else None,
                             registrationEligible=True))
    assert sorted(i for s in selected for i in s['ids'])==list(range(n))
    rows.append(dict(id=c['id'],training=c['id'] in training,atoms=n,partitionScore=score,clusters=selected))
usage=defaultdict(set)
for r in rows:
    if r['training']:
        for s in r['clusters']:
            if s['matched']:usage[s['type']].add(r['id'])
report=dict(scope=__doc__,coordinateHash=sha(coordp),metadataHash=sha(metap),codeHash=sha(Path(__file__)),
            rigidHelperHash=sha(Path(__file__).with_name('bounded-rigid-registration.py')),epsilonAngstrom=epsilon,types=types,rows=rows,
            trainingFrameUsage={str(k):len(v) for k,v in usage.items()},registrationNodes=registration_nodes,registrationBudgetStops=registration_budget_stops,
            limits='Full atom partition by geometric persistence; not an overlap-connected tiling or learned t/m model. Greedy proper-isometry representatives learned only from fitting frames; reference coordinates are not jointly optimized. Registration is capped at 20000 correspondence nodes per attempted fit; budget stops do not prove non-isometry. Single-linkage tie behavior and dictionary non-transitivity require further symmetry controls. No physical-state, matched-condition or independent-trajectory claim.')
with out.open('x') as f:json.dump(report,f,indent=2)
for split in [True,False]:
    rr=[r for r in rows if r['training']==split]
    print(json.dumps(dict(training=split,frames=len(rr),clusterSizes=dict(Counter(len(s['ids']) for r in rr for s in r['clusters'])),fullyMatched=sum(all(s['matched'] for s in r['clusters']) for r in rr),unsupported=sum(not s['registrationEligible'] for r in rr for s in r['clusters']))))
print(json.dumps(dict(types=len(types),recurringTrainingTypes=sum(len(v)>1 for v in usage.values()))))
