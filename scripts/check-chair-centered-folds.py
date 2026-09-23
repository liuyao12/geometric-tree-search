"""Exact, finite fold-design audit; this is not the GCTS tiling scheduler.

Each square has one reversal bit (both blue halves reverse together). Bases
and centered apex heights stay fixed. Audit all pairwise wedge intersections,
then check the equality constraints imposed by the existing eight-chair patch.
"""
import collections
import itertools
import json
import os
from pathlib import Path
import runpy
import subprocess

root=Path(__file__).resolve().parents[1]
audit=runpy.run_path(str(root/'scripts/verify-chair-tetra-geometry.py'))
Q=audit['Q'];dot=audit['dot'];sub=audit['sub']
features=audit['current'];marks=audit['marks'];data=audit['D']
source="""
import {chairLeaves,VARIANTS,markPoint,key} from './3d-reptiles/chair/chair44.js';
const faces=new Map(),pairs=new Set();
for(const p of chairLeaves(1))for(const [i,m] of VARIANTS[p.variantId].marks.entries()){
 const face=key(markPoint(m).map((x,k)=>x+2*p.origin[k]));
 if(faces.has(face))pairs.add([faces.get(face),i].sort((a,b)=>a-b).join(','));else faces.set(face,i);
}
console.log(JSON.stringify([...pairs].map(s=>s.split(',').map(Number))));
"""
contacts=json.loads(subprocess.check_output([os.environ.get('NODE_BINARY','node'),'--input-type=module','-e',source],cwd=root,text=True))
choices=[]
for k,t in enumerate(features):
 _,m=marks[k];sign=data['features'][k]['sign']
 choices.append([t,(*t[:3],tuple(t[3][i]-Q(2,3)*sign*m['direction'][i] for i in range(3)))])
forbidden={}
for a,b in itertools.combinations(range(len(features)),2):
 i,j=marks[a][0],marks[b][0]
 for x,y in itertools.product([0,1],repeat=2):
  if i==j and x!=y:continue
  A,B=choices[a][x],choices[b][y]
  bad=audit['interior_overlap'](A,B) or any(audit['triangle_contact'](list(c),list(d)) for c in itertools.combinations(A,3) for d in itertools.combinations(B,3))
  if bad:forbidden.setdefault((i,j),set()).add((x,y))

def groups(pairs):
 parent=list(range(24))
 def find(i):
  while parent[i]!=i:i=parent[i]
  return i
 for a,b in pairs:parent[find(a)]=find(b)
 result=collections.defaultdict(list)
 for i in range(24):result[find(i)].append(i)
 return list(result.values())

def allowed(flips):
 return all((int(i in flips),int(j in flips)) not in blocked for (i,j),blocked in forbidden.items())

# Matching surfaces require identical reversal bits on an existing contact.
# For each centered profile, reversing both signs preserves complementarity;
# reversing just one makes it fail. The JS profile test checks this geometry.
components=groups(contacts)
assert sorted(map(len,components))==[8,16]
combinations=[]
for bits in itertools.product([0,1],repeat=len(components)):
 flips={i for bit,component in zip(bits,components) if bit for i in component}
 bad=[list(pair) for pair,blocked in forbidden.items() if (int(pair[0] in flips),int(pair[1] in flips)) in blocked]
 assert bad
 combinations.append(dict(flipped_components=list(bits),coincident_mark_pairs=bad))

hinges=[[0,1],[5,4],[6,8],[9,10],[14,13],[18,21],[19,16],[22,23]]
fold_groups=groups(hinges)
best=None
for count in range(len(fold_groups)+1):
 for subset in itertools.combinations(range(len(fold_groups)),count):
  flips={i for group in subset for i in fold_groups[group]}
  if allowed(flips):best=sorted(flips);break
 if best is not None:break
assert count==2 and best==[9,10,16,19]
assert any((a in best)!=(b in best) for a,b in contacts)
# These two reversed pairs exchange two equal-volume additions/removals.
assert sum(data['features'][k]['sign']*(-1 if i in best else 1) for k,(i,_) in enumerate(marks))==0
print(json.dumps(dict(scope='fixed half-square bases, centered height 1/3, per-square reversal',
 existing_supertile_components=components,all_matching_preserving_choices=combinations,
 minimum_reversed_hinge_pairs=count,collision_free_reversed_marks=best,
 preserves_existing_supertile=False)))
