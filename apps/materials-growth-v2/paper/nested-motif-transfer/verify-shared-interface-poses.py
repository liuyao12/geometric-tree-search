"""Replay shared poses; independently witness connectivity in periodic graphs."""
import copy,hashlib,importlib.util,json,sys,tempfile
from pathlib import Path
from collections import defaultdict,deque

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def forest_components(n,edges):
    parent=list(range(n))
    def root(i):
        while parent[i]!=i:i=parent[i]
        return i
    for a,b,s in edges:
        assert root(a)!=root(b),'Not a forest: independent rank-zero proof does not apply'
        parent[root(a)]=root(b)
    return len({root(i) for i in range(n)})

def periodic_paths(n,edges,bound=4):
    adjacency=[[] for _ in range(n)]
    for ei,(a,b,s) in enumerate(edges):
        assert 0<=a<n and 0<=b<n and len(s)==3 and all(isinstance(v,int) for v in s)
        adjacency[a].append((b,s,ei,1));adjacency[b].append((a,[-v for v in s],ei,-1))
    start=(0,0,0,0);goals={(i,0,0,0) for i in range(n)}|{(0,1,0,0),(0,0,1,0),(0,0,0,1)};parents={start:None};queue=deque([start])
    while queue and not goals<=parents.keys():
        node=queue.popleft();a,*cell=node
        for b,s,ei,sign in adjacency[a]:
            q=tuple(cell[k]+s[k] for k in range(3))
            if max(map(abs,q))>bound:continue
            next_node=(b,*q)
            if next_node not in parents:parents[next_node]=(node,ei,sign);queue.append(next_node)
    assert goals<=parents.keys(),'No constructive connectivity witness inside the declared box'
    proofs=[]
    for goal in sorted(goals):
        path=[];node=goal
        while parents[node] is not None:
            previous,ei,sign=parents[node];path.append((ei,sign));node=previous
        path.reverse();a=0;cell=[0,0,0]
        for ei,sign in path:
            x,y,s=edges[ei]
            assert a==(x if sign==1 else y);a=y if sign==1 else x;cell=[cell[k]+sign*s[k] for k in range(3)]
        assert (a,*cell)==goal;proofs.append(dict(target=goal,steps=len(path)))
    return proofs

def main():
    coordp,metap,motifp,interfacep,pairp,sharedp,proposalp,out=map(Path,sys.argv[1:]);shared=json.loads(sharedp.read_text());pairs=json.loads(pairp.read_text());interfaces=json.loads(interfacep.read_text());motifs=json.loads(motifp.read_text());proposals=json.loads(proposalp.read_text());meta=json.loads(metap.read_text());coords=json.loads(coordp.read_text())
    for key,path in [('coordinateHash',coordp),('metadataHash',metap),('motifHash',motifp),('interfaceHash',interfacep),('pairResultHash',pairp)]:assert shared[key]==sha(path)
    for key,path in [('coordinateHash',coordp),('metadataHash',metap),('motifHash',motifp)]:assert proposals[key]==sha(path)
    checker=load('pose_checker','verify-reposed-interfaces.py');checker.verify(coordp,metap,motifp,interfacep,pairp)
    mm={r['id']:r for r in meta['configurations']};rr={r['id']:r for r in motifs['rows']};cc={r['id']:r for r in coords['configurations']};byframe=defaultdict(list)
    for r in pairs['rows']:byframe[r['configuration']].append(r)
    assert len(shared['rows'])==len(byframe) and {r['configuration'] for r in shared['rows']}==set(byframe)
    replay=copy.deepcopy(pairs);lookup={r['observation']:r for r in replay['rows']};shared_counts=defaultdict(int);forest_counts=defaultdict(int)
    for r in shared['rows']:
        cid=r['configuration'];n=len(rr[cid]['clusters']);assert n==r['motifs']
        expected_edges=sorted((interfaces['observations'][p['observation']]['clusterA'],interfaces['observations'][p['observation']]['clusterB']) for p in byframe[cid])
        assert sorted((a,b) for a,b,s in r['periodicEdges'])==expected_edges
        components=forest_components(n,r['periodicEdges']);assert components==r['proposalComponents'];forest_counts[mm[cid]['phase']]+=1
        assert r['pairwiseComplete']==all(p['witness'] is not None for p in byframe[cid])
        if r['poses'] is None:assert r['search']['status']!='consistent';continue
        assert r['search']['status']=='consistent' and len(r['poses'])==n
        expected={p['observation'] for p in byframe[cid]};assert {p['observation'] for p in r['selected']}==expected and len(r['selected'])==len(expected)
        for selected in r['selected']:
            oi=selected['observation'];o=interfaces['observations'][oi];assert o['configuration']==cid
            lookup[oi]['witness']=dict(interface=selected['interface'],poseA=r['poses'][o['clusterA']],poseB=r['poses'][o['clusterB']],errors=selected['errors'])
        shared_counts[mm[cid]['phase']]+=1
    # Same summary applies: this audit changes witnesses, not the successful
    # pair set. Every shared motif supplies exactly one stored pose above.
    with tempfile.TemporaryDirectory(prefix='gcts-shared-replay-') as directory:
        path=Path(directory)/'replay.json';path.write_text(json.dumps(replay));check=checker.verify(coordp,metap,motifp,interfacep,path)
    periodic=load('periodic','periodic-interface-proposals.py');proof_rows=[]
    assert len(proposals['rows'])==len(byframe) and {r['configuration'] for r in proposals['rows']}==set(byframe)
    for r in proposals['rows']:
        assert r['status']=='verified-image-bound';cid=r['configuration'];n=len(rr[cid]['clusters']);proofs=periodic_paths(n,r['edges'])
        # Numerical stability control, separate from the integer path proof.
        bigger=periodic.propose([p['fit']['translation'] for p in rr[cid]['clusters']],cc[cid]['cell'],max_shell=r['shell']+1,start_shell=r['shell']+1)
        assert bigger['edges']==[tuple(e) for e in r['edges']]
        proof_rows.append(dict(configuration=cid,unitTranslationPaths=3,motifReachabilityPaths=n-1,maxPathSteps=max(p['steps'] for p in proofs),largerImageBoxSameEdges=True))
    report=dict(sharedHash=sha(sharedp),proposalHash=sha(proposalp),verifierHash=sha(Path(__file__)),sharedPoseFrames=dict(shared_counts),nearestGraphForestFrames=dict(forest_counts),periodicGraphsWithConstructiveConnectivityProof=len(proof_rows),largerImageBoxStableGraphs=len(proof_rows),poseReplayMaximumAtomError=check['maximumAtomErrorAngstrom'],rows=proof_rows,
                limits='Positive shared-pose replay and integer paths in recorded candidate graphs. A forest proves zero translation cycles regardless of edge shifts. Enlarged-box agreement is a numerical geometry control, not exact Voronoi certification. No learned markings on the new periodic proposals, cross-interface common-value audit, t-learning, reconstruction or growth.')
    with out.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='rows'}))
if __name__=='__main__':main()
