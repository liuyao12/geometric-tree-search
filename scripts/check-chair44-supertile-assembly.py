"""Exact contacts of eight rigid eight-tile supertiles in a 64-tile patch."""
from fractions import Fraction as Q
from itertools import combinations,product
from collections import defaultdict
from math import gcd,lcm
from functools import reduce
import json,subprocess,os,struct
from pathlib import Path
root=Path(__file__).resolve().parents[1]
node=os.environ.get('NODE_BINARY','node')
source="""
import {ATOMIC_TEMPLATES} from './3d-reptiles/chair/tetra-relief.js';
import {CHAMBERS} from './3d-reptiles/chair/tetra-atoms.js';
import {chairLeaves,apply,multiply} from './3d-reptiles/chair/chair44.js';
const small=chairLeaves(2),leaves=chairLeaves(1).map(l=>({...l,origin:l.origin.map(x=>2*x)}));
// Confirm these are eight rigidly congruent copies of one eight-tile cluster.
const template=small.filter(l=>l.path[0]===0);
const signature=ls=>ls.map(l=>JSON.stringify([l.origin,l.rotation])).sort().join(';');
for(let i=0;i<8;i++){
 const parent=leaves[i];
 const expected=template.map(l=>({
  origin:apply(parent.rotation,l.origin.map(x=>x-1)).map((x,j)=>x+1+parent.origin[j]),
  rotation:multiply(parent.rotation,l.rotation)
 }));
 if(signature(expected)!==signature(small.filter(l=>l.path[0]===i)))throw Error('Noncongruent cluster');
}
const occupied=new Map(),groups=leaves.map(()=>new Map());
for(const l of small)for(const c of ATOMIC_TEMPLATES[l.variantId]){
 const cell=c.cell.map((x,i)=>x+l.origin[i]),k=cell.join(',');
 const old=occupied.get(k)||0n;if(old&c.mask)throw Error('Static overlap');
 occupied.set(k,old|c.mask);
 const group=groups[l.path[0]],entry=group.get(k)||{cell,mask:0n};
 entry.mask|=c.mask;group.set(k,entry);
}
const faces=groups.map(group=>{
 const boundary=new Map();
 for(const {cell,mask} of group.values())for(const chamber of CHAMBERS){
  if(!(mask&(1n<<BigInt(chamber.atom))))continue;
  for(const f of chamber.faces){
   const vertices=f.map(p=>p.map((x,i)=>x+12*cell[i]));
   const key=vertices.map(v=>v.join(',')).sort().join(';');
   if(boundary.has(key))boundary.delete(key);else boundary.set(key,vertices);
  }
 }
 return [...boundary.values()].flatMap(f=>f.slice(1,-1).map((_,i)=>[f[0],f[i+1],f[i+2]]));
});
console.log(JSON.stringify({leaves,small,faces}));
"""
data=json.loads(subprocess.check_output([node,'--input-type=module','-e',source],cwd=root))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def primitive(a):
 den=lcm(*(Q(x).denominator for x in a));v=[int(x*den) for x in a];g=reduce(gcd,v);return tuple(x//g for x in v) if g else tuple(v)
def area(poly):return sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])) if len(poly)>2 else Q(0)
def contact(a,b,n):
 axis=next(i for i,x in enumerate(n) if x)
 a=[tuple(Q(x) for i,x in enumerate(p) if i!=axis) for p in a];b=[tuple(Q(x) for i,x in enumerate(p) if i!=axis) for p in b]
 if any(max(min(p[k] for p in a),min(p[k] for p in b))>=min(max(p[k] for p in a),max(p[k] for p in b)) for k in range(2)):return False
 if area(b)<0:b.reverse()
 for u,v in zip(b,b[1:]+b[:1]):
  def dist(p):return (v[0]-u[0])*(p[1]-u[1])-(v[1]-u[1])*(p[0]-u[0])
  out=[]
  for p,q in zip(a,a[1:]+a[:1]):
   dp,dq=dist(p),dist(q)
   if dp>=0:out.append(p)
   if dp*dq<0:out.append(tuple((x*dq-y*dp)/(dq-dp) for x,y in zip(p,q)))
  a=out
  if len(a)<3:return False
 return area(a)!=0
planes=[]
for faces in data['faces']:
 index=defaultdict(list)
 for i,f in enumerate(faces):
  n=primitive(cross(sub(f[1],f[0]),sub(f[2],f[0])));d=dot(n,f[0]);sgn=1 if next(x for x in n if x)>0 else -1
  plane=tuple(sgn*x for x in (*n,d));index[plane].append((f,n,i))
 planes.append(index)
constraints={}; contact_witnesses={}; pair_witnesses={}
for i,j in combinations(range(8),2):
 normals=set();witnesses=[]
 for p in sorted(planes[i].keys() & planes[j].keys()):
  for a,n,ai in planes[i][p]:
   for b,m,bi in planes[j][p]:
    if n==tuple(-x for x in m) and contact(a,b,n):normals.add(n);witnesses.append((ai,bi,n))
 constraints[i,j]=sorted(normals);constraints[j,i]=sorted(tuple(-x for x in n) for n in normals)
 for ai,bi,n in witnesses:
  pair_witnesses.setdefault((i,j,n),{'movingTriangle':ai,'fixedTriangle':bi})
  pair_witnesses.setdefault((j,i,tuple(-x for x in n)),{'movingTriangle':bi,'fixedTriangle':ai})
  contact_witnesses.setdefault((i,n),{'neighbor':j,'movingTriangle':ai,'fixedTriangle':bi})
  contact_witnesses.setdefault((j,tuple(-x for x in n)),{'neighbor':i,'movingTriangle':bi,'fixedTriangle':ai})

# Each union has exactly the volume of eight printed tiles; internal chamber
# walls have been cancelled before the contact analysis.
for faces in data['faces']:
 assert sum(dot(a,cross(b,c)) for a,b,c in faces)==6*56*12**3
assert len(data['small'])==64
assert all(sum(l['path'][0]==i for l in data['small'])==8 for i in range(8))
def certificate(i,j,basis):
 out=[]
 for n in basis:
  witnesses=[]
  for normal in (n,tuple(-x for x in n)):
   ids=pair_witnesses[i,j,normal]
   witnesses.append({'normal':normal,**ids,
    'movingVertices':data['faces'][i][ids['movingTriangle']],
    'fixedVertices':data['faces'][j][ids['fixedTriangle']]})
  out.append(witnesses)
 return out
pairs=[]
for i,j in combinations(range(8),2):
 normals=constraints[i,j]
 if not normals:continue
 direction=sub(data['leaves'][i]['origin'],data['leaves'][j]['origin'])
 paired=[n for n in normals if tuple(-x for x in n) in normals]
 basis=next((b for b in combinations(paired,3) if dot(b[0],cross(b[1],b[2]))),None)
 pairs.append({'pair':[i,j],'contactNormalCount':len(normals),'radialDirection':direction,
  'radialBlockedBy':[n for n in normals if dot(n,direction)>0],
  'translationLocked':basis is not None,
  'basisDeterminant':dot(basis[0],cross(basis[1],basis[2])) if basis else None,
  'certificate':certificate(i,j,basis) if basis else None})
locked=[p for p in pairs if p['translationLocked']]
assert len(pairs)==16 and len(locked)==7
assert all(4 in p['pair'] for p in locked)
# Independently replay the continuous-SAT collision witness at an exact time.
# Its convex chambers are identified by their original tile paths and indices.
witness=json.loads((root/'docs/projects/chair44-supertile-collision.json').read_text())['result']
A=[tuple(map(Q,p)) for p in witness['movingVertices']]
B=[tuple(map(Q,p)) for p in witness['fixedVertices']]
def overlap(a,b):
 edges=lambda t:[sub(x,y) for x,y in combinations(t,2)]
 axes=[cross(sub(y,x),sub(z,x)) for t in (a,b) for x,y,z in combinations(t,3)]
 axes += [cross(x,y) for x in edges(a) for y in edges(b)]
 for n in axes:
  if not any(n):continue
  aa=[dot(n,p) for p in a];bb=[dot(n,p) for p in b]
  if max(aa)<=min(bb) or max(bb)<=min(aa):return False
 return True
assert not overlap(A,B)
time=Q(1,20)
assert overlap([tuple(x+time*d for x,d in zip(p,witness['direction'])) for p in A],B)
print(json.dumps({'smallTiles':64,'rigidSupertiles':8,'tilesPerSupertile':8,
 'staticNonoverlap':True,'rigidCongruenceVerified':True,'unionVolumePerSupertile':56,
 'coordinateScale':12,'boundaryTrianglesPerSupertile':[len(f) for f in data['faces']],
 'supertiles':data['leaves'],'contactPairs':pairs,
 'pureTranslationAssemblyBlocked':True,
 'reason':'Each outer supertile is translation-locked to the center even in isolation; their relative velocities must all be zero.',
 'independentCollisionWitnessTime':str(time),
 'scope':'Rigid unions of eight current centered-relief tiles, canonical level-two placement. Rotations, deformation and motion within each supertile are not tested.'},indent=2))
