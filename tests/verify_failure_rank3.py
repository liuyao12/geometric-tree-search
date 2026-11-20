"""Independently replay the excluded relative placements from the live model."""
import json
import os
import subprocess
from pathlib import Path
from a2_neighborhoods import neighborhoods

if not __debug__:
    raise SystemExit('Run with assertions enabled.')
cmd = [os.environ.get('NODE','node'), Path(__file__).with_name('test_failure_rank3.mjs'), '--geometry']
for set_id, shapes in json.loads(subprocess.check_output(cmd)).items():
    candidates = set()
    for root in (r for r in shapes if r['index'] == 0):
        weights = {(x,y):w for x,y,w in root['sites']}
        for r in shapes:
            # Distinct offsets are exhausted by equating two marked positions.
            for x,y,c,v in root['marks']:
                for a,b,k,w in r['marks']:
                    if k != c or v == w:
                        continue
                    dx,dy = x-a,y-b
                    if all(weights.get((dx+u,dy+h),0)+z<=12 for u,h,z in r['sites']):
                        candidates.add((root['tile'],r['tile'],r['index'],dx,dy))
    # An impossible pair may be easiest to certify from its other endpoint.
    # Compute its exact inverse from the production orientation matrices.
    sym = {r['index']:r['symmetry'] for r in shapes}
    def move(i,x,y):
        a,b,_ = sym[i]['permutation']
        p = x,y,-x-y
        return sym[i]['sign']*p[a],sym[i]['sign']*p[b]
    inv = {i:next(j for j in sym if move(j,*move(i,2,5)) == (2,5)) for i in sym}
    certified = set()
    for s,_,balls,possible in neighborhoods(shapes):
        for key in sorted(candidates):
            root,t,i,x,y = key
            if root != s or key in certified or possible((t,i,x,y)):
                continue
            certified.add(key)
            certified.add((t,root,inv[i],*move(inv[i],-x,-y)))
        print(set_id,s,len(balls),'unmarked neighborhoods',flush=True)
    assert certified == candidates, sorted(candidates-certified)[:10]
    print(set_id,len(candidates),'geometrically admissible relative placements excluded and certified',flush=True)
