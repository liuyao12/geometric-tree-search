"""Independent rational SAT and coplanar-area audit of all relief wedges."""
from fractions import Fraction as Q
from itertools import combinations
from collections import defaultdict, Counter
from pathlib import Path
import json,subprocess,os
root=Path(__file__).resolve().parents[1]
source="import {TETRA_FEATURES,tetraBoundary,BOUNDARY_SCALE} from './3d-reptiles/chair/tetra-relief.js'; import {BASE_MARKS} from './3d-reptiles/chair/chair44.js';console.log(JSON.stringify({features:TETRA_FEATURES,marks:BASE_MARKS,boundary:tetraBoundary(),boundaryScale:BOUNDARY_SCALE}));"
D=json.loads(subprocess.check_output([os.environ.get('NODE_BINARY','node'),'--input-type=module','-e',source],cwd=root,text=True))
marks=[(i,m) for i,m in enumerate(D['marks']) for _ in range(2 if m['color']=='blue' else 1)]
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def interior_overlap(a,b):
 edges=lambda t:[sub(x,y) for x,y in combinations(t,2)]
 axes=[cross(sub(y,x),sub(z,x)) for t in [a,b] for x,y,z in combinations(t,3)]+[cross(x,y) for x in edges(a) for y in edges(b)]
 for n in axes:
  if not any(n):continue
  A=[dot(n,p) for p in a];B=[dot(n,p) for p in b]
  if max(A)<=min(B) or max(B)<=min(A):return False
 return True

def area2(poly):return sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])) if len(poly)>2 else Q(0)
def triangle_contact(a,b):
 n=cross(sub(a[1],a[0]),sub(a[2],a[0]));d=dot(n,a[0])
 if any(dot(n,p)!=d for p in b):return False
 axis=next(i for i,x in enumerate(n) if x);a=[tuple(x for i,x in enumerate(p) if i!=axis) for p in a];b=[tuple(x for i,x in enumerate(p) if i!=axis) for p in b]
 if area2(b)<0:b.reverse()
 for u,v in zip(b,b[1:]+b[:1]):
  def dist(p):return (v[0]-u[0])*(p[1]-u[1])-(v[1]-u[1])*(p[0]-u[0])
  out=[]
  for p,q in zip(a,a[1:]+a[:1]):
   dp,dq=dist(p),dist(q)
   if dp>=0:out.append(p)
   if dp*dq<0:out.append(tuple((x*dq-y*dp)/(dq-dp) for x,y in zip(p,q)))
  a=out
  if len(a)<3:return False
 return area2(a)!=0


current=[tuple(tuple(Q(x,6) for x in p) for p in f['vertices']) for f in D['features']]
original=[]
for f,(_,mark),tet in zip(D['features'],marks,current):
 base=tet[:3]
 apex=tuple(sum(p[i] for p in base)/3+Q(f['sign'],3)*mark['direction'][i] for i in range(3))
 original.append((*base,apex))
def inspect(tetrahedra):
 overlaps=[];contacts=[]
 for i,j in combinations(range(len(tetrahedra)),2):
  if interior_overlap(tetrahedra[i],tetrahedra[j]):overlaps.append([i,j])
  if any(triangle_contact(list(a),list(b)) for a in combinations(tetrahedra[i],3) for b in combinations(tetrahedra[j],3)):contacts.append([i,j])
 return overlaps,contacts
old_overlaps,old_contacts=inspect(original)
assert old_overlaps==[]
assert sorted(tuple(sorted((marks[i][0],marks[j][0]))) for i,j in old_contacts)==[(9,12),(18,19)]
new_overlaps,new_contacts=inspect(current)
assert new_overlaps==[]
assert sorted(tuple(sorted((marks[i][0],marks[j][0]))) for i,j in new_contacts)==[(9,12),(18,19)]
assert all((x*3).denominator==1 for t in current for p in t for x in p)
for t,(_,mark),f in zip(current,marks,D['features']):
 assert t[3]==tuple(sum(p[i] for p in t[:3])/3+Q(f['sign'],3)*mark['direction'][i] for i in range(3))
for tet in current:
 a,b,c,d=tet
 assert abs(dot(sub(b,a),cross(sub(c,a),sub(d,a))))/6==Q(1,18)
# The rendered boundary itself cannot contain a duplicate/coincident patch.
triangles=[[tuple(Q(x,D['boundaryScale']) for x in p) for p in f['vertices']] for f in D['boundary']]
assert all(not triangle_contact(a,b) for a,b in combinations(triangles,2))
volume=sum(dot(a,cross(b,c))/6 for a,b,c in triangles)
assert volume==7
# Count connected planar faces using exact rational planes and shared edges.
planes=[];edges=defaultdict(list);parent=list(range(len(triangles)))
for i,triangle in enumerate(triangles):
 a,b,c=triangle;n=cross(sub(b,a),sub(c,a));pivot=next(x for x in n if x)
 planes.append(tuple(x/pivot for x in (*n,dot(n,a))))
 for a,b in zip(triangle,triangle[1:]+triangle[:1]):edges[tuple(sorted((a,b)))].append(i)
def root(i):
 while parent[i]!=i:i=parent[i]
 return i
for pair in edges.values():
 assert len(pair)==2, 'Boundary must be a closed triangular manifold'
 a,b=pair
 if planes[a]==planes[b]:parent[root(b)]=root(a)
face_sizes=Counter(Counter(root(i) for i in range(len(triangles))).values())
assert sum(face_sizes.values())==98
planar_faces=sum(face_sizes.values())
vertices={p for triangle in triangles for p in triangle}
assert len(vertices)-len(edges)+len(triangles)==2
# Every vertex link is a single cycle, including the newly joined cavity edges.
for vertex in vertices:
 link=defaultdict(set)
 for triangle in triangles:
  if vertex not in triangle:continue
  a,b=[p for p in triangle if p!=vertex];link[a].add(b);link[b].add(a)
 assert all(len(neighbors)==2 for neighbors in link.values())
 seen=set();pending=[next(iter(link))]
 while pending:
  p=pending.pop()
  if p in seen:continue
  seen.add(p);pending.extend(link[p]-seen)
 assert seen==set(link), 'Pinched boundary vertex'
# Merging coplanar triangulation edges preserves the Euler characteristic.
assert len(vertices)-(len(edges)-(len(triangles)-planar_faces))+planar_faces==2
print(json.dumps(dict(planar_faces=planar_faces,old_coincident_mark_pairs=[[9,12],[18,19]],new_interior_overlaps=0,raw_cut_contacts=len(new_contacts),boundary_coincident_faces=0,volume=str(volume),wedge_pairs=496,boundary_triangles=len(triangles))))
