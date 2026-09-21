#!/usr/bin/env python3
import json,copy
from collections import Counter
from itertools import product
from pathlib import Path
from solve_voxel_pair_corona import solve
from solve_point_pair_corona import solve as reference
from certify_voxel_obstruction import construct
from verify_p9_48258_certificate import weights

def model(voxels):return {'capacity':8,'placementDomain':{'kind':'scaled_cubic','translationStep':2},'orientations':[{'voxels':voxels,'cells':[{'pos':list(p),'weight':w} for p,w in weights(voxels).items()]}]}
def replay(data,result):
    # Reconstruct the original weighted point model, independent of the oracle's
    # voxel bit masks. Check all capacity constraints, core sums, and frontier.
    m=data['model'];supports=[[(tuple(c['pos']),c['weight']) for c in o['cells']] for o in m['orientations']]
    placements=result['placements'];seen=set();totals=Counter()
    for p in placements:
        oi,t=p['oi'],tuple(p['translation']);assert (oi,t) not in seen;seen.add((oi,t));assert all(x%2==0 for x in t)
        for q,w in supports[oi]:totals[tuple(q[i]+t[i] for i in range(3))]+=w
    assert max(totals.values())<=8
    core={tuple(c['pos'][i]+p['translation'][i] for i in range(3)) for p in data['pair'] for c in m['orientations'][p['oi']]['cells']}
    assert all(totals[q]==8 for q in core)
    assert all((p['oi'],tuple(p['translation'])) in seen for p in data['pair'])
    def legal_at(q):
        for oi,support in enumerate(supports):
            for anchor,_ in support:
                t=tuple(q[i]-anchor[i] for i in range(3))
                if any(x%2 for x in t) or (oi,t) in seen:continue
                if all(totals.get(tuple(v[i]+t[i] for i in range(3)),0)+w<=8 for v,w in support):return True
        return False
    if result['status']=='valid':assert all(n==8 or legal_at(q) for q,n in totals.items())

for voxels,delta in [([[0,0,0]],2),([[0,0,0],[1,0,0]],4)]:
    data={'model':model(voxels),'pair':[{'oi':0,'translation':[0,0,0]},{'oi':0,'translation':[delta,0,0]}]}
    new=solve(data,time_ms=3000);old=reference(data['model'],data['pair'],time_ms=3000,encoding='voxel-cover',frontier='occupancy')
    assert new['status']==old['status']=='valid';replay(data,new)
    assert solve(data,max_rounds=0)['status']=='unresolved'
    f,_,_=construct(data);q=[[0,0,0],[delta+4,2,0]]
    for p in q:f.constrain_frontier(p)
    g,_,_=construct(data,q);assert f.clauses==g.clauses
base=Path('data/p9-48258-grid-obstruction')
for n in [22,24,27,29]:
    data=json.loads((base/f'pair-{n}.input.json').read_text());new=solve(data,time_ms=10000)
    assert new['status']=='invalid';print('Certified negative',n,'recovered in',round(new['stats']['elapsedMs']),'ms',flush=True)
    resumed=solve(data,time_ms=10000,resume_points=new['frontierPoints']);assert resumed['status']=='invalid'
    short=solve(data,time_ms=1);assert short['status']=='unresolved'
# A nontrivial positive needs repeated frontier refinements and candidates that
# can extend beyond the SAT pool. Replay the original weighted point model.
geometry=json.loads(Path('data/3d-p9-42947-pair-obstructions-2026-09-21.json').read_text())
record=json.loads(Path('data/3d-p9-42947-local-catalogue-2026-09-21.json').read_text())
positive_model=model(geometry['orientations'][0])
positive_model['orientations']=[model(o)['orientations'][0] for o in geometry['orientations']]
positive_data={'model':positive_model,'pair':record['groups'][40]['pair']}
positive=solve(positive_data,time_ms=15000)
assert positive['status']=='valid';assert positive['stats']['rounds']>1;replay(positive_data,positive)
print('Nontrivial positive replayed after',positive['stats']['rounds'],'SAT rounds',flush=True)
# Exclude optional markings and malformed point representations from this oracle.
bad=copy.deepcopy(data);bad['model']['orientations'][0]['marks']=[{'pos':[0,0,0],'value':1}]
try:solve(bad);raise AssertionError('Marked oracle accepted')
except ValueError:pass
bad=copy.deepcopy(data);bad['model']['orientations'][0]['cells'][0]['weight']+=1
try:solve(bad);raise AssertionError('Inexact voxel reduction accepted')
except ValueError:pass
print('PASS independent weighted positive replay, Z3 controls, four proof-certified negatives, incremental/static equality, resume, timeout and malformed-model controls.')
