"""Independent periodic edge, face partition, winding, coverage and pose checks."""
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np
import networkx as nx
from scipy.spatial import cKDTree

def verify(source,folder):
    raw=Path(source).read_bytes();inputs=json.loads(raw)['results'];folder=Path(folder);reports=[]
    for fold,c in enumerate(inputs):
        for scale in (1.15,1.35):
            for rep in (2,3):
                d=json.loads((folder/f'{fold}-{scale}-{rep}.json').read_text());s=d['summary']
                assert d['inputHash']==hashlib.sha256(raw).hexdigest()
                cell=np.array(d['cell']);positions=np.array(d['positions']);assert np.allclose(cell,np.array(c['cell'])*rep)
                expected=np.concatenate([np.array(c['positions'])+np.array(shift)@c['cell'] for shift in itertools.product(range(rep),repeat=3)])
                assert np.allclose(positions,expected)
                inverse=np.linalg.inv(cell);assert np.min(1/np.linalg.norm(inverse,axis=0))>2*s['radius']
                # The plane-height bound makes neighboring image cells sufficient.
                offsets=np.floor(positions@inverse).astype(int);wrapped=positions-offsets@cell
                shifts=list(itertools.product((-1,0,1),repeat=3));images=np.concatenate([wrapped+np.array(shift)@cell for shift in shifts])
                tree=cKDTree(images);expected_edges={};n=len(positions)
                for i,neighbors in enumerate(tree.query_ball_point(wrapped,s['radius'])):
                    for index in neighbors:
                        j=index%n;shift=np.array(shifts[index//n])-offsets[j]+offsets[i]
                        if i==j and not np.any(shift):continue
                        assert i!=j and (i,j) not in expected_edges
                        expected_edges[i,j]=tuple(map(int,shift))
                edges={}
                for a,b,shift in d['edgeShifts']:edges[a,b]=tuple(shift);edges[b,a]=tuple(-x for x in shift)
                assert edges==expected_edges
                graph=nx.Graph();graph.add_nodes_from(range(n));graph.add_edges_from((a,b) for a,b in edges if a<b)
                triangles={tuple(sorted((a,b,c))) for a in graph for b in graph[a] for c in graph[a] if a<b<c and graph.has_edge(b,c)}
                face_graph=nx.Graph();face_graph.add_nodes_from(triangles);by_edge={}
                for tri in triangles:
                    for edge in itertools.combinations(tri,2):by_edge.setdefault(edge,[]).append(tri)
                for faces in by_edge.values():
                    for a,b in itertools.combinations(faces,2):face_graph.add_edge(a,b)
                wanted={frozenset(g) for g in nx.connected_components(face_graph)}
                assert wanted=={frozenset(tuple(f) for f in g['faces']) for g in d['components']}
                finite_edges=set();covered=set()
                for g in d['components']:
                    ids=g['ids'];assert ids==sorted({v for tri in g['faces'] for v in tri})
                    ge={tuple(x) for x in g['edges']};assert ge=={edge for tri in g['faces'] for edge in itertools.combinations(tri,2)}
                    part=nx.Graph();part.add_edges_from(ge);lift={ids[0]:np.zeros(3,dtype=int)};todo=[ids[0]];wind=False
                    while todo:
                        a=todo.pop(0)
                        for b in sorted(part[a]):
                            candidate=lift[a]+edges[a,b]
                            if b not in lift:lift[b]=candidate;todo.append(b)
                            elif np.any(lift[b]!=candidate):wind=True
                    assert wind==bool(g['windingVectors'])
                    if not wind:
                        stored=dict(zip(ids,np.array(g['imageOffsets'])))
                        assert all(np.array_equal(stored[b]-stored[a],edges[a,b]) for a,b in ge)
                        assert np.allclose(g['positions'],positions[ids]+np.array(g['imageOffsets'])@cell)
                        finite_edges.update(ge);covered.update(ids)
                fallback={tuple(e) for e in d['fallbackPairs']};assert fallback=={(a,b) for a,b in edges if a<b}-finite_edges
                covered.update(v for edge in fallback for v in edge)
                assert set(d['singletons'])==set(range(n))-covered
                assert len(covered)+len(d['singletons'])==s['coveredAtoms']==n
                reports.append(s)
    dictionary=json.loads((folder/'dictionary.json').read_text());fits=0;icosa=0
    for c in dictionary['configurations']:
        path=folder/f"{c['fold']}-1.15-3.json";raw=path.read_bytes();d=json.loads(raw)
        assert hashlib.sha256(raw).hexdigest()==c['sourceHash']
        for o in c['occurrences']:
            g=d['components'][o['component']];x=np.array(dictionary['types'][o['type']]['positions']);y=np.array(g['positions'])
            R=np.array(o['rotationRow']);assert np.max(np.abs(R.T@R-np.eye(3)))<1e-9 and abs(np.linalg.det(R)-1)<1e-9
            assert sorted(o['permutation'])==list(range(len(y)))
            error=max(np.linalg.norm(x@R+o['translation']-y[o['permutation']],axis=1))
            assert error<=dictionary['epsilonAngstrom']+1e-9 and abs(error-o['residual'])<1e-9
            graph=nx.Graph();graph.add_nodes_from(g['ids']);graph.add_edges_from(g['edges'])
            claim=len(g['ids'])==12 and nx.is_isomorphic(graph,nx.icosahedral_graph());assert claim==o['icosahedralGraph']
            fits+=1;icosa+=claim
    for fold in range(6):
        for scale in (1.15,1.35):
            a,b=[r for r in reports if r['file']==inputs[fold]['file'] and r['radiusScale']==scale]
            assert {k:v/8 for k,v in a['finiteSizeCounts'].items()}=={k:v/27 for k,v in b['finiteSizeCounts'].items()}
    out={'verifiedSupercellRuns':len(reports),'verifiedRegisteredFiniteComponents':fits,
        'verifiedIcosahedralGraphs':int(icosa),'finiteCountScalingChecked':True,'dictionarySummary':dictionary['summary'],
        'fractionalFillingTested':False,'growthTested':False}
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':
    out=verify(*sys.argv[1:3])
    if len(sys.argv)>3:
        with Path(sys.argv[3]).open('x') as f:json.dump(out,f,indent=2)
