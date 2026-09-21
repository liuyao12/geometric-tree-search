#!/usr/bin/env python3
import copy
from collections import defaultdict
from itertools import product
from solve_voxel_point_window import solve

def model(voxels, required, values=(None, None)):
    weights = defaultdict(int)
    for v in voxels:
        weights[tuple(2*x+1 for x in v)] = 8
        for d in product([0, 1], repeat=3):
            weights[tuple(2*(v[i]+d[i]) for i in range(3))] += 1
    return {'capacity':8, 'placementDomain':{'kind':'scaled_cubic', 'translationStep':2}, 'required':[{'pos':p} for p in required], 'orientations':[{'voxels':voxels, 'cells':[{'pos':list(p),'weight':w} for p,w in weights.items()], 'marks':[{'pos':[0,1,1],'value':values[0]},{'pos':[2*len(voxels),1,1],'value':values[1]}]}]}

def valid(m, placements, marked=True):
    totals, marks = defaultdict(int), {}
    for p in placements:
        o = m['orientations'][p['oi']]
        for c in o['cells']:
            q = tuple(c['pos'][i]+p['translation'][i] for i in range(3))
            totals[q] += c['weight']
            if totals[q] > 8: return False
        if marked:
            for c in o['marks']:
                if c['value'] is None or c['value'] == '*': continue
                q = tuple(c['pos'][i]+p['translation'][i] for i in range(3))
                if q in marks and marks[q] != c['value']: return False
                marks[q] = c['value']
    return all(totals[tuple(p['pos'])] == 8 for p in m['required'])

def brute(m):
    translations = set()
    for p in m['required']:
        for c in m['orientations'][0]['cells']:
            t = tuple(p['pos'][i]-c['pos'][i] for i in range(3))
            if all(x%2 == 0 for x in t): translations.add(t)
    candidates = [{'oi':0,'translation':list(t)} for t in translations]
    for chosen in product([False, True], repeat=len(candidates)):
        if valid(m,[p for p,b in zip(candidates,chosen) if b]): return True
    return False

count = 0
for voxels in [[[0,0,0]],[[0,0,0],[1,0,0]]]:
    for required in [[[1,1,1]],[[1,1,1],[3,1,1]],[[1,1,1],[3,1,1],[5,1,1]],[[0,0,0]]]:
        for values in product([None,0,1],repeat=2):
            m=model(voxels,required,values);answer=solve(m,marked=True,time_ms=2000)
            expected=brute(m)
            assert answer['result']==('finite_exact' if expected else 'restricted_model_failure'),answer
            if expected: assert valid(m,answer['placements'])
            count+=1
m=model([[0,0,0]],[[1,1,1],[3,1,1]],(0,1))
assert solve(m,marked=False)['result']=='finite_exact'
assert solve(m,marked=True)['result']=='restricted_model_failure'
assert solve(m,max_candidates=1)['result']=='unknown'
bad=copy.deepcopy(m);bad['orientations'][0]['cells'].append(bad['orientations'][0]['cells'][0])
try: solve(bad);raise AssertionError('Duplicate accepted')
except ValueError: pass
print(f'PASS {count} exhaustive finite-window/marking controls, independent witness replay, budget and duplicate-site rejection.')
