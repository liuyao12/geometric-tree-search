#!/usr/bin/env python3
"""Geometry/linkage controls for the archived five-proof argument."""
import copy,json
from pathlib import Path
from verify_p9_48258_certificate import audit_geometry,ROOT
bundle=ROOT/'data/p9-48258-grid-obstruction'
root=json.loads((bundle/'root-window.input.json').read_text())
pairs=[json.loads((bundle/f'pair-{n}.input.json').read_text()) for n in [22,24,27,29]]
assert audit_geometry(root,pairs)=={'orientations':3,'properRotations':24,'localPairs':4,'relativePairSchemas':192,'requiredVoxels':343}
for kind in ['lost_pair','extra_pair','wrong_field','learned_field','wrong_root','wrong_target','wrong_orbit','lost_local_proof']:
    r,ps=copy.deepcopy(root),copy.deepcopy(pairs)
    if kind=='lost_pair':r['pairExclusions'].pop()
    elif kind=='extra_pair':r['pairExclusions'].append(r['pairExclusions'][0])
    elif kind=='wrong_field':r['model']['orientations'][0]['cells'][0]['weight']+=1
    elif kind=='learned_field':r['model']['orientations'][0]['marks']=[{'pos':[0,0,0],'value':1}]
    elif kind=='wrong_root':r['fixed'][0]['translation'][0]=2
    elif kind=='wrong_target':r['model']['required']=[]
    elif kind=='wrong_orbit':r['model']['orientations'].pop()
    elif kind=='lost_local_proof':ps.pop()
    try:audit_geometry(r,ps);raise AssertionError('Accepted corrupted '+kind)
    except (ValueError,IndexError):pass
print('PASS exact voxel field, full proper orbit, 192 symmetry transfers, rooted target and eight corrupted-certificate controls.')
