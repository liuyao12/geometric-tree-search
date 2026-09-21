#!/usr/bin/env python3
import random
from itertools import product
from solve_patch_period_quotients import hnf,det,reduce_site,cross,dot,normal,rotated,ROTATIONS,solve_quotient,quotient_pool,replay_period
rng=random.Random(1729);cases=0
for _ in range(300):
 b=[[rng.randrange(-3,4) for _ in range(3)] for _ in range(3)];d=abs(det(b))
 if not d:continue
 h=hnf(b);assert det(h)==d and hnf(h)==h
 for _ in range(6):
  i,j=rng.sample(range(3),2);q=rng.randrange(-3,4);b[i]=[x+q*y for x,y in zip(b[i],b[j])]
 assert hnf(b)==h
 reps=list(product(range(h[0][0]),range(h[1][1]),range(h[2][2])))
 numerators=[cross(b[1],b[2]),cross(b[2],b[0]),cross(b[0],b[1])]
 assert len({tuple(dot(q,n)%d for n in numerators) for q in reps})==d
 for q in reps[:5]:
  for v in b:assert reduce_site([q[i]+v[i] for i in range(3)],h)==q
 cases+=1
# Tiny exact-cover enumeration independent of SAT and prefix auxiliaries.
comparisons=0
for shape in [[[0,0,0]],[[0,0,0],[1,0,0]],[[0,0,0],[1,0,0],[0,1,0]]]:
 orientations=sorted({normal([rotated(p,r) for p in shape]) for r in ROTATIONS})
 for basis in [[[2,0,0],[0,2,0],[0,0,1]],[[3,0,0],[1,2,0],[1,0,1]],[[3,0,0],[0,3,0],[0,0,1]]]:
  if abs(det(basis))%len(shape):continue
  b,pool,_=quotient_pool(shape,orientations,basis);full=(1<<det(b))-1;masks=[sum(1<<q for q in p['sites']) for p in pool]
  def visit(used):
   if used==full:return True
   q=next(q for q in range(det(b)) if not used&(1<<q))
   return any(visit(used|mask) for mask in masks if mask&(1<<q) and not mask&used)
  expected=visit(0)
  for origin in [False,True]:
   r=solve_quotient(shape,orientations,basis,origin_symmetry=origin)
   assert (r['status']=='periodic_certificate')==expected and r['status']!='unknown'
   if expected:
    assert replay_period(orientations,r['basis'],r['certificate']['placements'],len(shape))
    broken=r['certificate']['placements'][:-1];assert not replay_period(orientations,r['basis'],broken,len(shape))
   comparisons+=1
print('PASS',cases,'integer lattice transformations, quotient signatures, and',comparisons,'exhaustive covers with/without origin symmetry.')
# Every orientation of a four-voxel rod wraps onto itself in a 2x2x2 quotient.
rod=[[x,0,0] for x in range(4)];orientations=sorted({normal([rotated(p,r) for p in rod]) for r in ROTATIONS})
assert solve_quotient(rod,orientations,[[2,0,0],[0,2,0],[0,0,2]])['status']=='unsat_period_lattice'
assert solve_quotient([[0,0,0]],[[[0,0,0]]],[[5000,0,0],[0,1,0],[0,0,1]],time_ms=1)['status']=='unknown'
print('PASS self-overlap exclusion and exhausted preparation budget remains unknown.')
from solve_patch_period_quotients import pair_constraint_edges
# Two domino anchors can have identical quotient occupancy but different pair
# incidences. They must remain distinct variables when pair constraints apply.
domino=[[0,0,0],[1,0,0]];orientations=sorted({normal([rotated(p,r) for p in domino]) for r in ROTATIONS});oi=orientations.index(normal(domino));basis=[[2,0,0],[0,1,0],[0,0,1]]
b,pool,roots=quotient_pool(domino,orientations,basis)
assert len(pool)==2 and pool[0]['sites']==pool[1]['sites']
assert pair_constraint_edges(pool,b,[(oi,oi,[1,0,0])])=={(1,2)}
assert solve_quotient(domino,orientations,basis,pair_exclusions=[(oi,oi,[1,0,0])])['status']=='periodic_certificate'
# A restriction between a tile and its period translate becomes a unit clause.
assert pair_constraint_edges(pool,b,[(oi,oi,[2,0,0])])=={(1,1),(2,2)}
assert solve_quotient(domino,orientations,basis,pair_exclusions=[(oi,oi,[2,0,0])])['status']=='unsat_restricted_quotient'
print('PASS separate placement identities, wraparound pair edges, self-period exclusions, and restricted-result labeling.')
# Cross-language replay uses a separately regenerated orientation table. Reverse
# and translate ours to ensure certificates carry geometry keys, not just IDs.
import json,os,shutil,subprocess
from pathlib import Path
node=os.environ.get('GCTS_NODE_BINARY') or shutil.which('node')
assert node,'Set GCTS_NODE_BINARY to run the independent JavaScript verifier'
module=(Path(__file__).resolve().parents[1]/'assets/polycube-periodic-tiler.js').as_uri()
fixtures=[]
for shape,basis in [([[0,0,0]],[[2,0,0],[1,2,0],[0,0,1]]),([[0,0,0],[1,0,0],[0,1,0]],[[3,0,0],[0,2,0],[0,0,1]])]:
 orientations=sorted({normal([rotated(p,r) for p in shape]) for r in ROTATIONS},reverse=True)
 orientations=[[[v[i]+[5,-2,1][i] for i in range(3)] for v in o] for o in orientations]
 result=solve_quotient(shape,orientations,basis)
 assert result['status']=='periodic_certificate'
 assert replay_period(orientations,result['basis'],result['certificate']['placements'],len(shape))
 fixtures.append({'voxels':shape,'certificate':result['certificate']})
js=f"import {{verifyPolycubePeriodicCertificate as verify}} from {json.dumps(module)};let s='';for await(const x of process.stdin)s+=x;for(const f of JSON.parse(s)){{if(!verify(f.voxels,f.certificate).verified)throw Error('Independent periodic replay failed');f.certificate.placements.pop();if(verify(f.voxels,f.certificate).verified)throw Error('Incomplete construction accepted');}}console.log('PASS independent JavaScript periodic certificate replay and damaged-certificate rejection.');"
p=subprocess.run([node,'--input-type=module','-e',js],input=json.dumps(fixtures),text=True,capture_output=True)
assert p.returncode==0,p.stderr
print(p.stdout.strip())
