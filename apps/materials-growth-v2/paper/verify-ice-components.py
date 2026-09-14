"""Independent periodic-image KD-tree / union-find check of frozen-threshold components."""
import json
from pathlib import Path
import sys
from itertools import product
from collections import Counter,defaultdict
import numpy as np
from scipy.spatial import cKDTree

folder=Path(sys.argv[1]);data=json.loads((folder/'coordinates.json').read_text())['configurations']
meta={c['id']:c for c in json.loads((folder/'provenance.json').read_text())['configurations']}
report=json.loads((folder/'components.json').read_text());results={c['id']:c for c in report['results']}
threshold=report['threshold'];groups=defaultdict(Counter);images=np.array(list(product((-1,0,1),repeat=3)))
assert set(results)=={c['id'] for c in data}
for c in data:
    cell=np.array(c['cell']);n=len(c['positions']);frac=np.array(c['positions'])@np.linalg.inv(cell)
    pos=(frac%1)@cell
    # This bound proves translations beyond +/-1 cannot lie within the cutoff.
    assert threshold<np.linalg.svd(cell,compute_uv=False).min()
    copies=(pos[None,:,:]+(images@cell)[:,None,:]).reshape(-1,3)
    tree=cKDTree(copies);parent=list(range(n))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,neighbors in enumerate(tree.query_ball_point(pos,threshold)):
        for j in neighbors:parent[root(i)]=root(j%n)
    components=defaultdict(list)
    for i in range(n):components[root(i)].append(i)
    composition=Counter(str(sorted(Counter(c['species'][i] for i in ids).items())) for ids in components.values())
    r=results[c['id']]
    assert r['components']==len(components) and dict(composition)==r['compositions'] and r['atoms']==n
    bucket=groups[(meta[c['id']]['phase'],meta[c['id']]['split'])]
    bucket['frames']+=1;bucket['atoms']+=n;bucket['components']+=len(components)
    bucket['OHHComponents']+=composition.get("[('H', 2), ('O', 1)]",0)
out={'verifiedFrames':len(data),'thresholdAngstrom':threshold,'gapEndpoints':report['gapEndpoints'],
 'groups':[dict(phase=k[0],split=k[1],**v) for k,v in groups.items()],
 'scope':'Frozen threshold independently checked; neither independent-trajectory transfer nor overlapping motif learning nor growth.'}
print(json.dumps(out,indent=2))
with Path(sys.argv[2]).open('x') as f:json.dump(out,f,indent=2)
