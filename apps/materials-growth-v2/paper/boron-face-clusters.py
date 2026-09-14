"""Geometry-only face-connected cluster proposals on periodic supercells.

Merge graph triangles sharing an edge. Reject winding components as finite
motifs. Retain every remaining edge as a pair proposal and uncovered atoms as
singletons. This establishes atom coverage, not learned additive t filling.
No target motif size, boron chemistry, or named polyhedron is supplied.
"""
import collections
import hashlib
import itertools
import json
from pathlib import Path
import sys
import numpy as np
from ase import Atoms
from ase.neighborlist import neighbor_list

def components(n,edge_shifts):
    adjacency=[set() for _ in range(n)]
    for a,b in edge_shifts:adjacency[a].add(b)
    triangles=[]
    for a in range(n):
        for b in sorted(x for x in adjacency[a] if x>a):
            triangles.extend((a,b,c) for c in sorted(adjacency[a]&adjacency[b]) if c>b)
    parents=list(range(len(triangles)))
    def root(a):
        while parents[a]!=a:parents[a]=parents[parents[a]];a=parents[a]
        return a
    edge_owner={}
    for i,tri in enumerate(triangles):
        for edge in itertools.combinations(tri,2):
            if edge in edge_owner:parents[root(i)]=root(edge_owner[edge])
            else:edge_owner[edge]=i
    groups=collections.defaultdict(list)
    for i,tri in enumerate(triangles):groups[root(i)].append(tri)
    result=[]
    for faces in groups.values():
        edges=sorted({pair for tri in faces for pair in itertools.combinations(tri,2)})
        ids=sorted({v for e in edges for v in e});adj={v:[] for v in ids}
        for a,b in edges:adj[a].append(b);adj[b].append(a)
        offsets={ids[0]:np.zeros(3,dtype=int)};todo=[ids[0]];winding=set()
        while todo:
            a=todo.pop()
            for b in adj[a]:
                offset=offsets[a]+np.array(edge_shifts[a,b])
                if b not in offsets:offsets[b]=offset;todo.append(b)
                elif np.any(offset!=offsets[b]):winding.add(tuple((offset-offsets[b]).tolist()))
        result.append({'ids':ids,'faces':[list(x) for x in faces],'edges':[list(x) for x in edges],
            'imageOffsets':[offsets[i].tolist() for i in ids],'windingVectors':sorted(winding)})
    return result

def run(c,rep,scale):
    primitive=Atoms('B'*c['atoms'],positions=c['positions'],cell=c['cell'],pbc=True)
    distances=primitive.get_all_distances(mic=True);np.fill_diagonal(distances,np.inf)
    radius=float(np.median(distances.min(axis=1)))*scale
    atoms=primitive.repeat((rep,rep,rep));ii,jj,ss=neighbor_list('ijS',atoms,radius)
    shifts={}
    for i,j,s in zip(ii,jj,ss):
        key=(int(i),int(j));value=tuple(map(int,s))
        assert i!=j,'Supercell too small: self-image neighbor'
        assert key not in shifts or shifts[key]==value,'Supercell too small: multiple image edges'
        shifts[key]=value
    groups=components(len(atoms),shifts);finite=[g for g in groups if not g['windingVectors']]
    used={tuple(e) for g in finite for e in g['edges']}
    fallback=sorted((a,b) for a,b in shifts if a<b and (a,b) not in used)
    covered={v for g in finite for v in g['ids']}|{v for e in fallback for v in e}
    singletons=sorted(set(range(len(atoms)))-covered)
    for g in finite:
        g['positions']=(atoms.positions[g['ids']]+np.array(g['imageOffsets'])@atoms.cell.array).tolist()
        degree=collections.Counter(v for e in g['edges'] for v in e)
        g['degreeSequence']=sorted(degree.values())
    summary={'file':c['file'],'repeat':rep,'radiusScale':scale,'atoms':len(atoms),'radius':radius,
        'triangleComponents':len(groups),'finiteComponents':len(finite),'windingComponents':len(groups)-len(finite),
        'finiteSizeCounts':dict(sorted(collections.Counter(len(g['ids']) for g in finite).items())),
        'fallbackPairs':len(fallback),'singletonAtoms':len(singletons),'coveredAtoms':len(covered)+len(singletons)}
    return {'summary':summary,'cell':atoms.cell.array.tolist(),'positions':atoms.positions.tolist(),
        'edgeShifts':[[a,b,list(s)] for (a,b),s in sorted(shifts.items()) if a<b],
        'components':groups,'fallbackPairs':fallback,'singletons':singletons}

if __name__=='__main__':
    raw=Path(sys.argv[1]).read_bytes();source=json.loads(raw)['results'];dest=Path(sys.argv[2]);dest.mkdir();summaries=[]
    for i,c in enumerate(source):
        for scale in (1.15,1.35):
            for rep in (2,3):
                result=run(c,rep,scale);result['inputHash']=hashlib.sha256(raw).hexdigest()
                with (dest/f'{i}-{scale}-{rep}.json').open('x') as f:json.dump(result,f)
                summaries.append(result['summary']);print(json.dumps(result['summary']),flush=True)
    (dest/'summary.json').write_text(json.dumps({'scope':__doc__,'results':summaries},indent=2))
