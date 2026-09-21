#!/usr/bin/env python3
"""Hints are reversible SAT preferences, for both available backends/encodings."""
import copy,json
from pathlib import Path
from solve_voxel_pair_corona import solve,solve_window
from test_voxel_frontier_window import model,point_replay
for backend in ['glucose3','cadical195']:
 for amo in ['pairwise','sequential']:
  # The preferred placement conflicts with the fixed seed. It must be rejected.
  m=model([[[0,0,0]]]*6)
  data={'model':m,'fixed':[{'oi':0,'translation':[0,0,0]}]}
  hint=[{'oi':1,'translation':[0,0,0]},{'oi':1,'translation':[100,0,0]}]
  r=solve_window(data,backend=backend,amo=amo,phase_hints=hint)
  assert r['status']=='valid';point_replay(data,r)
  assert r['stats']['phaseHints']==1 and r['stats']['phaseHintsOutsidePool']==1
  assert hint[0] not in r['placements']
  assert solve_window(data,backend=backend,amo=amo,max_rounds=0)['status']=='unresolved'
  for bad in [[{'oi':0,'translation':[1,0,0]}],[{'oi':8,'translation':[0,0,0]}],[{'oi':True,'translation':[0,0,0]}]]:
   try:solve_window(data,backend=backend,amo=amo,phase_hints=bad)
   except ValueError:pass
   else:raise AssertionError('Invalid hint accepted')
 geometry=json.loads((Path(__file__).resolve().parents[1]/'data/3d-p9-42947-pair-obstructions-2026-09-21.json').read_text())
 data={'model':model(geometry['orientations']),'pair':geometry['obstructions'][0]['pair']}
 for amo in ['pairwise','sequential']:
  assert solve(data,backend=backend,amo=amo,phase_hints=data['pair'])['status']=='invalid'
print('PASS both backends and encodings: reversible contradictory hints, outside-pool hints, malformed inputs, finite witnesses, proved negative and unknown budgets.')
