"""Exact face-contact locking audit and correspondence to the delivered STL."""
from fractions import Fraction as Q
from itertools import combinations,product
from collections import defaultdict
from math import gcd,lcm
from functools import reduce
import json,subprocess,os,struct
from pathlib import Path
root=Path(__file__).resolve().parents[1]
node=os.environ.get('NODE_BINARY','node')
source="import {tetraBoundary} from './3d-reptiles/chair/tetra-relief.js';import {chairLeaves,apply} from './3d-reptiles/chair/chair44.js';const leaves=chairLeaves(1);console.log(JSON.stringify({leaves,faces:leaves.map(l=>tetraBoundary().map(f=>f.vertices.map(p=>apply(l.rotation,p.map(x=>x-12)).map((x,i)=>x+12+12*l.origin[i]))))}));"
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
constraints={}; contact_witnesses={}
for i,j in combinations(range(8),2):
 normals=set();witnesses=[]
 for p in planes[i].keys() & planes[j].keys():
  for a,n,ai in planes[i][p]:
   for b,m,bi in planes[j][p]:
    if n==tuple(-x for x in m) and contact(a,b,n):normals.add(n);witnesses.append((ai,bi,n))
 constraints[i,j]=sorted(normals);constraints[j,i]=sorted(tuple(-x for x in n) for n in normals)
 for ai,bi,n in witnesses:
  contact_witnesses.setdefault((i,n),{'neighbor':j,'movingTriangle':ai,'fixedTriangle':bi})
  contact_witnesses.setdefault((j,tuple(-x for x in n)),{'neighbor':i,'movingTriangle':bi,'fixedTriangle':ai})
# A short exact locking certificate: three linearly independent normal pairs
# n and -n force n dot v = 0, hence v = 0. Every normal has a positive-area
# contact witness, so moving toward the fixed neighboring solid is forbidden.
results=[]
for i in range(8):
 normals=sorted({n for j in range(8) if j!=i for n in constraints[i,j]})
 paired=[n for n in normals if tuple(-x for x in n) in normals]
 basis=next((b for b in combinations(paired,3) if dot(b[0],cross(b[1],b[2]))),None)
 assert basis is not None, 'No translation-lock certificate found'
 certificate=[]
 for n in basis:
  negative=tuple(-x for x in n)
  certificate.append({'normal':n,'positiveContact':contact_witnesses[i,n],
   'negativeContact':contact_witnesses[i,negative]})
 results.append({'tile':i,'origin':data['leaves'][i]['origin'],
  'normalCount':len(normals),'basisDeterminant':dot(basis[0],cross(basis[1],basis[2])),
  'onlyAllowedTranslation':[0,0,0],'certificate':certificate})
# Verify the delivered STL is exactly the tested geometry, not a proxy shape.
base=data['faces'][0]
minimum=[min(v[k] for f in base for v in f) for k in range(3)]
stl=(root/'3d-reptiles/chair/print/chair44-centered-48mm.stl').read_bytes()
count=struct.unpack_from('<I',stl,80)[0]
assert count==len(base) and len(stl)==84+50*count
printed=[]
for i in range(count):
 values=struct.unpack_from('<12fH',stl,84+50*i)
 printed.append([tuple(Q(values[j+k])*Q(2,3)+minimum[k] for k in range(3)) for j in (3,6,9)])
def signature(faces):return sorted(tuple(sorted(tuple(v) for v in face)) for face in faces)
assert signature(printed)==signature(base)
pairs=[]
for i,j in combinations(range(8),2):
 normals=constraints[i,j]
 if not normals:continue
 direction=sub(data['leaves'][i]['origin'],data['leaves'][j]['origin'])
 assert all(dot(n,direction)<=0 for n in normals)
 tangent=[n for n in normals if dot(n,direction)==0]
 guided=any(any(cross(a,b)) for a,b in combinations(tangent,2))
 pairs.append({'pair':[i,j],'extractionDirection':primitive(direction),
  'contactNormalCount':len(normals),'tangentGuideNormals':tangent,
  'twoIndependentGuidePlanes':guided})
assert len(pairs)==16
assert sum(p['twoIndependentGuidePlanes'] for p in pairs)==7
print(json.dumps({'printedSTLMatchesExactGeometry':True,
 'geometry':'Centered apex (2,1,1), merged cavities, 48 mm STL',
 'contactPairs':pairs,'individuallyTranslationLockedTiles':results,
 'scope':'Exact face-contact constraints, all other tiles fixed, no rotation. Full pairwise paths are separately checked by check-chair44-assembly.mjs.'},indent=2))
