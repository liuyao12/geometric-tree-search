"""Exact conditional weight inference for two-incidence selected tilings.

Each row w_u+w_v=1 becomes a complement edge, including self-edges. A
non-bipartite component forces all weights to 1/2; a bipartite component has
one free parameter a and its complement 1-a. No numerical rank threshold.
The selected tilings were obtained with a degree-two hypothesis: this is not
unrestricted occurrence selection or independent discovery of that hypothesis.
"""
import hashlib
import json
from pathlib import Path
import sys
from collections import defaultdict
import networkx as nx

raw=Path(sys.argv[1]).read_bytes();d=json.loads(raw);g=nx.Graph();edges=[];hashes=[]
for path in sys.argv[3:]:
    b=Path(path).read_bytes();hashes.append(hashlib.sha256(b).hexdigest());chosen={r['id']:r for r in json.loads(b)['results']}
    for c in d['configurations']:
        if not c['training']:continue
        r=chosen[c['id']];assert r['status']=='connected positive finite cover';rows=defaultdict(list)
        for index in r['selected']:
            o=c['occurrences'][index]
            for u,j in enumerate(o['permutation']):rows[o['ids'][j]].append(d['offsets'][o['type']]+u)
        assert len(rows)==c['atoms'] and all(len(row)==2 for row in rows.values())
        for point,row in rows.items():
            g.add_edge(*row);edges.append({'sites':row,'configuration':c['id'],'point':point,'witnessSet':len(hashes)-1})
components=[]
for sites in sorted(nx.connected_components(g),key=lambda x:min(x)):
    graph=g.subgraph(sites);root=min(sites);color={root:0};parent={root:None};todo=[root];odd=None
    for u in todo:
        for v in sorted(graph[u]):
            if v not in color:color[v]=1-color[u];parent[v]=u;todo.append(v)
            elif color[u]==color[v] and odd is None:
                left=[u];right=[v]
                while parent[left[-1]] is not None:left.append(parent[left[-1]])
                while parent[right[-1]] is not None:right.append(parent[right[-1]])
                common=next(x for x in left if x in right)
                odd=left[:left.index(common)+1]+list(reversed(right[:right.index(common)]))+[u]
    components.append({'sites':sorted(sites),'kind':'forced-half' if odd is not None else 'free-complement',
                       'oddCycle':odd,'side0':sorted(x for x in sites if color[x]==0),'side1':sorted(x for x in sites if color[x]==1)})
unobserved=sorted(set(range(d['offsets'][-1]))-set(g));summary={
 'siteVariables':d['offsets'][-1],'trainingRows':len(edges),'uniqueComplementEdges':g.number_of_edges(),
 'forcedHalfSites':sum(len(c['sites']) for c in components if c['kind']=='forced-half'),
 'freeComplementSites':sum(len(c['sites']) for c in components if c['kind']=='free-complement'),
 'freeComplementParameters':sum(c['kind']=='free-complement' for c in components),
 'unobservedSites':len(unobserved),
 'totalFreeParameters':len(unobserved)+sum(c['kind']=='free-complement' for c in components)}
out={'scope':__doc__,'dictionaryHash':hashlib.sha256(raw).hexdigest(),'selectionHashes':hashes,
 'components':components,'unobservedSites':unobserved,'equations':edges,'summary':summary}
with Path(sys.argv[2]).open('x') as f:json.dump(out,f)
print(json.dumps(summary,indent=2))
