"""Independent replay of stored transports, cycle rank, and vector residuals.

Checks the supplied constraint graph, not completeness of geometry proposals
or globally optimal approximate vector assignments.
"""
import json
from pathlib import Path
import sys
import numpy as np

def verify(path):
    d=json.loads(Path(path).read_text());T={int(v):np.array(x) for v,x in d['siteTransports'].items()}
    vectors={int(v):np.array(x) for v,x in d['siteVectors'].items()};owner={}
    for i,c in enumerate(d['components']):
        for v in c['members']:assert v not in owner;owner[v]=i
        assert np.max(np.abs(T[c['root']]-np.eye(3)))<1e-10
    assert set(owner)==set(T)==set(vectors)
    for v,x in T.items():
        assert np.max(np.abs(x.T@x-np.eye(3)))<1e-9 and abs(np.linalg.det(x)-1)<1e-9
        assert abs(np.linalg.norm(vectors[v])-1)<1e-9
        root=d['components'][owner[v]]['root'];assert np.max(np.abs(vectors[v]-x@vectors[root]))<1e-9
    rows=[[] for _ in d['components']];actual=[[] for _ in rows];zero_edges={v:set() for v in T}
    for a,ra,b,rb in d['constraints']:
        assert owner[a]==owner[b];ra=np.array(ra);rb=np.array(rb)
        for R in (ra,rb):assert np.max(np.abs(R.T@R-np.eye(3)))<1e-9 and abs(np.linalg.det(R)-1)<1e-9
        E=ra@T[a]-rb@T[b];rows[owner[a]].append(E);actual[owner[a]].append(np.linalg.norm(ra@vectors[a]-rb@vectors[b]))
        if np.linalg.norm(E)<1e-8:zero_edges[a].add(b);zero_edges[b].add(a)
    for i,c in enumerate(d['components']):
        reached={c['root']};todo=[c['root']]
        while todo:
            for v in zero_edges[todo.pop()]-reached:reached.add(v);todo.append(v)
        assert reached==set(c['members']), 'Transforms are not supported by a spanning tree of exact transport edges'
        count=len(rows[i]);assert count==c['edges']
        B=np.array(rows[i]).reshape(-1,3)
        singular=np.linalg.svd(B,compute_uv=False)/np.sqrt(count) if count else np.zeros(3)
        gram=B.T@B/max(count,1)
        assert np.allclose(gram,c['meanGram'],atol=1e-10,rtol=1e-10)
        assert np.allclose(singular[::-1]**2,c['eigenvalues'],atol=1e-10,rtol=1e-10)
        assert int(sum(singular<=d['rankTolerance']))==c['numericalNullity']
        assert abs(np.sqrt(np.mean(np.square(actual[i])))-c['unitRootRmsMismatch'])<1e-9
        assert abs(max(actual[i],default=0)-c['unitRootMaximumMismatch'])<1e-9
    return {'file':Path(path).name,'variables':len(T),'constraints':len(d['constraints']),
        'components':len(d['components']),'largestComponentNullity':max(d['components'],key=lambda c:len(c['members']))['numericalNullity']}

if __name__=='__main__':
    results=[verify(Path(sys.argv[1])/f'{i}.json') for i in range(6)]
    out={'scope':__doc__,'results':results};print(json.dumps(out,indent=2))
    if len(sys.argv)>2:
        with Path(sys.argv[2]).open('x') as f:json.dump(out,f,indent=2)
