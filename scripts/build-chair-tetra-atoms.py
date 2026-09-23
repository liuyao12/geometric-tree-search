"""Exact plane-arrangement audit and rotation-closed occupancy representatives."""
from fractions import Fraction as Q
from itertools import combinations,product
from math import gcd,lcm

def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def plane(a,b,c):
 n=cross(sub(b,a),sub(c,a));d=dot(n,a);v=(*n,d);den=lcm(*(x.denominator for x in v));v=[int(x*den) for x in v];g=gcd(*v);v=tuple(x//g for x in v)
 return v if next(x for x in v if x)>0 else tuple(-x for x in v)
# all wedges inside a unit cube
wedges=[];planes=set()
for axis in range(3):
 tang=[i for i in range(3) if i!=axis]
 for sign in [0,1]:
  corners=[]
  for a,b in product([0,1],repeat=2):
   p=[Q(0)]*3;p[axis]=Q(sign);p[tang[0]]=Q(a);p[tang[1]]=Q(b);corners.append(tuple(p))
  for tri in combinations(corners,3):
   apex=tuple(sum(p[i] for p in tri)/3 if i!=axis else Q(1+sign,3) for i in range(3))
   tet=(*tri,apex);wedges.append(tet)
   planes.update(plane(*face) for face in combinations(tet,3))
print('Wedges',len(wedges),'planes',len(planes),flush=True)

corners=list(product(map(Q,[0,1]),repeat=3))
faces=[[p for p in corners if p[a]==s] for a in range(3) for s in [0,1]]
# order square faces around their center using adjacency
for i,face in enumerate(faces):
 order=[face[0]]
 while len(order)<4:order.append(next(p for p in face if p not in order and sum(x!=y for x,y in zip(p,order[-1]))==1))
 faces[i]=order

def clip(faces,p,sign):
 vals={v:sign*(dot(p[:3],v)-p[3]) for f in faces for v in f}
 if all(d>=0 for d in vals.values()):return faces
 if all(d<=0 for d in vals.values()):return None
 out=[];cut=set()
 for f in faces:
  poly=[]
  for a,b in zip(f,f[1:]+f[:1]):
   da,db=vals[a],vals[b]
   if da>=0:poly.append(a)
   if da*db<0:
    v=tuple((x*db-y*da)/(db-da) for x,y in zip(a,b));poly.append(v);cut.add(v)
   if da==0:cut.add(a)
  if len(poly)>=3:out.append(poly)
 # boundary order by adjacency from clipped faces
 edges=[]
 for f in out:
  for a,b in zip(f,f[1:]+f[:1]):
   if a in cut and b in cut:edges.append((a,b))
 order=[edges[0][0]]
 while len(order)<len(cut):
  nxt=next(b if a==order[-1] else a for a,b in edges if (a==order[-1] and b not in order) or (b==order[-1] and a not in order))
  order.append(nxt)
 out.append(order);return out
atoms=[faces]
for p in sorted(planes):
 atoms=[f for atom in atoms for s in [1,-1] if (f:=clip(atom,p,s)) is not None]



import json
from fractions import Fraction as Q
from itertools import permutations,product
from math import lcm,gcd
D=dict(atoms=atoms,wedges=wedges,planes=planes)
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def encoded(p):
 den=lcm(*(x.denominator for x in p));return tuple(int(x*den) for x in p),den
planes=[]
for t in wedges:
 ps=[]
 for i,op in enumerate(t):
  a,b,c=[p for j,p in enumerate(t) if i!=j];n=cross(sub(b,a),sub(c,a));d=dot(n,a);sgn=1 if dot(n,op)>d else -1
  nums,den=encoded((*n,d));g=gcd(*nums);ps.append(tuple(sgn*x//g for x in nums))
 planes.append(ps)
def signature(p):
 nums,den=encoded(p)
 return sum(1<<i for i,ps in enumerate(planes) if all(dot(q[:3],nums)>q[3]*den for q in ps))
classes={};volume=Q(0);signatures=set()
for k,faces in enumerate(atoms):
 vs={v for f in faces for v in f};p=tuple(sum(v[i] for v in vs)/len(vs) for i in range(3));mask=signature(p)
 # Non-straddling, unique plane-sign signatures, and total volume certify the
 # common arrangement. Run the exact audit during every regeneration.
 plane_sig=[]
 for plane in sorted(D['planes']):
  value=dot(plane[:3],p)-plane[3];assert value
  s=1 if value>0 else -1;plane_sig.append(s)
  assert all(s*(dot(plane[:3],v)-plane[3])>=0 for v in vs)
 assert tuple(plane_sig) not in signatures;signatures.add(tuple(plane_sig))
 for face in faces:
  for j in range(1,len(face)-1):volume+=abs(dot(sub(face[0],p),cross(sub(face[j],p),sub(face[j+1],p))))/6
 previous=classes.get(mask)
 if previous is None or encoded(p)[1]<encoded(previous)[1]:classes[mask]=p
 if k%2000==0:print('Audited',k,'chambers',len(classes),'classes',flush=True)
assert volume==1
classes[0]=(Q(1,2),)*3
rotations=[]
for perm in permutations(range(3)):
 for signs in product([-1,1],repeat=3):
  inv=sum(perm[i]>perm[j] for i in range(3) for j in range(i+1,3));det=(-1)**inv*signs[0]*signs[1]*signs[2]
  if det==1:rotations.append((perm,signs))
chosen={};covered=set()
for mask,p in sorted(classes.items()):
 if mask in covered:continue
 for perm,signs in rotations:
  q=tuple(Q(1,2)+signs[i]*(p[perm[i]]-Q(1,2)) for i in range(3));m=signature(q)
  assert m in classes;chosen[q]=m;covered.add(m)
assert covered==set(classes)
points=[dict(point=list(encoded(p)[0]),den=encoded(p)[1],signature=hex(mask)[2:]) for p,mask in sorted(chosen.items())]
assert all(max([*map(abs,p['point']),p['den']])*100000<2**53 for p in points)
print('Complete',len(atoms),'chambers;',len(classes),'occupancy classes;',len(points),'symmetric samples; max denominator',max(p['den'] for p in points),flush=True)

from pathlib import Path
import sys
source='// Generated by scripts/build-chair-tetra-atoms.py; exact occupancy-class representatives.\n'
source+='export const ATOMS = '+json.dumps(points,separators=(',',':'))+';\n'
source+='export const WEDGES = '+json.dumps([[[int(x*6) for x in v]for v in t]for t in wedges],separators=(',',':'))+';\n'
source+='export const OCCUPANCY_SIGNATURES = '+json.dumps([hex(m)[2:] for m in sorted(classes)],separators=(',',':'))+';\n'
source+='export const CHAMBER_COUNT = '+str(len(atoms))+';\n'
# The same exact chambers provide the Boolean-union surface. Outward-oriented
# coincident chamber faces cancel, including internal walls between joined dents.
representative={int(p['signature'],16):i for i,p in enumerate(points)}
chambers=[]
for faces in atoms:
 vs={v for f in faces for v in f};center=tuple(sum(v[i] for v in vs)/len(vs) for i in range(3))
 outward=[]
 for f in faces:
  f=list(f);n=cross(sub(f[1],f[0]),sub(f[2],f[0]))
  if dot(n,sub(center,f[0]))>0:f.reverse()
  assert all((x*12).denominator==1 for v in f for x in v)
  outward.append([[int(x*12) for x in v] for v in f])
 chambers.append(dict(atom=representative[signature(center)],faces=outward))
source+='export const CHAMBERS = '+json.dumps(chambers,separators=(',',':'))+';\n'
path=Path(__file__).resolve().parents[1]/'3d-reptiles/chair/tetra-atoms.js'
if '--check' in sys.argv:assert path.read_text()==source,'Generated point data is stale'
else:path.write_text(source)
