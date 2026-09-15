"""Static necessary support for half-weight Cartesian cloud-marked blocks.

An anchor must have a required atom with exactly the same block incidence.
That atom needs two distinct-inventory placements. Each endpoint must therefore
have a compatible endpoint in another live block. Sorted coordinate signatures
give a deliberately relaxed test; survivors are NOT certified compatible.
"""
from collections import defaultdict
import importlib.util, pathlib
import numpy as np
from scipy.spatial import cKDTree
spec=importlib.util.spec_from_file_location('half',pathlib.Path(__file__).with_name('half-cloud-support.py'))
half=importlib.util.module_from_spec(spec);spec.loader.exec_module(half)

def prune(row,clouds):
    assert row['capacity']==2 and 0<=row['cloudRadius']<=1
    blocks=row['blocks'];atoms=defaultdict(set);anchors=defaultdict(set)
    for i,b in enumerate(blocks):
        assert len(b['markPoints'])==2 and len(set(b['markPoints']))==2
        assert len({t['point'] for t in b['t']})==len(b['t'])
        assert all(t['value']==1 for t in b['t'])
        for t in b['t']:atoms[t['point']].add(i)
        for p in b['markPoints']:anchors[p].add(i)
    witnesses={}
    for p,incidence in anchors.items():
        possible=[a for a in row['required'] if atoms[a]==incidence]
        assert possible, 'Anchor lacks a required half-capacity incidence witness'
        witnesses[p]=possible[0]
    records=[];buckets=defaultdict(list);endpoint_records={}
    for i,b in enumerate(blocks):
        for side,choices in enumerate(b['endpointChoices']):
            endpoint_records[i,side]=[]
            for j,c in enumerate(choices):
                layout,x=half.signature(clouds[c['cloud']]);key=(b['markPoints'][side],layout)
                k=len(records);records.append((i,side,j,key,x));buckets[key].append(k);endpoint_records[i,side].append(k)
    trees={key:cKDTree(np.asarray([records[k][4] for k in ids])) for key,ids in buckets.items()}
    alive=np.ones(len(records),dtype=bool);counts={(i,s):len(ids) for (i,s),ids in endpoint_records.items()}
    threshold=2*row['cloudRadius']+1e-8;removals=[];passes=0;queries=0
    while True:
        passes+=1;changed=False
        for k,(i,side,j,key,x) in enumerate(records):
            if not alive[k]:continue
            if counts[i,1-side]==0:
                reason='empty-other-endpoint'
            else:
                queries+=1;local=trees[key].query_ball_point(x,threshold,p=np.inf)
                supported=False
                for index in local:
                    q=buckets[key][index];other,other_side,_,_,_=records[q]
                    if alive[q] and counts[other,1-other_side]>0 and blocks[other]['inventory']!=blocks[i]['inventory']:
                        supported=True;break
                if supported:continue
                reason='no-complement-signature'
            alive[k]=False;counts[i,side]-=1;changed=True
            removals.append({'block':i,'side':side,'index':j,'reason':reason})
        if not changed:break
    allowed=[[[records[k][2] for k in endpoint_records[i,side] if alive[k]] for side in (0,1)] for i in range(len(blocks))]
    return {'allowed':allowed,'removals':removals,'anchorWitnesses':witnesses,'threshold':threshold,'passes':passes,'queries':queries}
