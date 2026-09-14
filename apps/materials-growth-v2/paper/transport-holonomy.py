"""Fixed-pose vector consistency through spanning-tree transport and cycle closure.

For R_a v_a = R_b v_b, a spanning tree expresses all vectors in a component
as orthogonal transports of one root vector. Cycle residuals give a 3x3 Gram
matrix. This tests numerical exact compatibility, not optimal tolerance fitting:
the unit-root diagnostic forces tree equations exactly instead of distributing
errors over every variable. It is not a global least-squares optimizer.
"""
import numpy as np

def analyze(nodes,edges,rank_tolerance=1e-8):
    adjacency={v:[] for v in nodes}
    for a,ra,b,rb in edges:
        ra=np.asarray(ra);rb=np.asarray(rb)
        adjacency[a].append((b,rb.T@ra));adjacency[b].append((a,ra.T@rb))
    unseen=set(nodes);components=[];transports={};owner={}
    while unseen:
        root=min(unseen);unseen.remove(root);todo=[root];members=[root];transports[root]=np.eye(3)
        while todo:
            a=todo.pop()
            for b,R in adjacency[a]:
                if b in unseen:
                    unseen.remove(b);todo.append(b);members.append(b);transports[b]=R@transports[a]
        index=len(components)
        for v in members:owner[v]=index
        components.append({'root':root,'members':sorted(members),'gram':np.zeros((3,3)),'edges':0,'residualMatrices':[]})
    for a,ra,b,rb in edges:
        c=components[owner[a]];assert owner[a]==owner[b]
        E=np.asarray(ra)@transports[a]-np.asarray(rb)@transports[b]
        c['gram']+=E.T@E;c['edges']+=1;c['residualMatrices'].append(E)
    vectors={};results=[]
    for c in components:
        G=c['gram']/max(1,c['edges'])
        if c['edges']:
            _,singular,vh=np.linalg.svd(np.array(c['residualMatrices']).reshape(-1,3),full_matrices=False)
            singular/=np.sqrt(c['edges']);eigenvalues=singular[::-1]**2;root_vector=vh[-1]
        else:singular=np.zeros(3);eigenvalues=singular.copy();root_vector=np.array([1.,0,0])
        rank=int(np.sum(singular>rank_tolerance))
        for v in c['members']:vectors[v]=(transports[v]@root_vector).tolist()
        residuals=[np.linalg.norm(E@root_vector) for E in c['residualMatrices']]
        results.append({'root':c['root'],'members':c['members'],'edges':c['edges'],
            'meanGram':G.tolist(),'eigenvalues':eigenvalues.tolist(),'numericalNullity':3-rank,
            'unitRootRmsMismatch':float(np.sqrt(np.mean(np.square(residuals)))) if residuals else 0.,
            'unitRootMaximumMismatch':float(max(residuals,default=0))})
    return {'scope':__doc__,'rankTolerance':rank_tolerance,'components':results,'siteVectors':vectors,
            'siteTransports':{v:T.tolist() for v,T in transports.items()}}
