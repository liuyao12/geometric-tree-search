#!/usr/bin/env python3
"""Exact uniform-dihedral obstruction. Also allows flat-face contributions at a root edge."""
import collections,json,pathlib
from fractions import Fraction as F
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
D=json.load(open('data/heesch-catalog/catalog.json'));rows=[]
for system,name in [('tet_oct','Tetrahedron'),('tet_oct','Octahedron'),('perovskite','Cuboctahedron'),('laves_c15','TruncTetra')]:
 t=next(x for r in D['systems'] if r['id']==system for x in r['components'] if x['name']==name);V=[tuple(map(F,v)) for v in t['vertices']];center=tuple(sum(v[i] for v in V)/len(V) for i in range(3));normals=[];edges=collections.defaultdict(list)
 for fi,face in enumerate(t['faces']):
  normal=cross(sub(V[face[1]],V[face[0]]),sub(V[face[2]],V[face[0]]));assert dot(normal,normal)>0
  if dot(normal,sub(center,V[face[0]]))>0:normal=tuple(-x for x in normal)
  assert all(dot(normal,sub(V[v],V[face[0]]))==0 for v in face)
  assert all(dot(normal,sub(v,V[face[0]]))<=0 for v in V);normals.append(normal)
  for a,b in zip(face,face[1:]+face[:1]):edges[tuple(sorted((a,b)))].append(fi)
 angles=set()
 for adjacent in edges.values():
  assert len(adjacent)==2;a,b=(normals[i] for i in adjacent);num=-dot(a,b);den=dot(a,a)*dot(b,b);angles.add((1 if num>0 else -1 if num<0 else 0,num*num/den))
 result={'system':system,'component':name,'edgeCount':len(edges),'dihedralCosines':[{'sign':sign,'square':str(square)} for sign,square in sorted(angles)]}
 if len(angles)==1:
  sign,square=next(iter(angles));assert sign<0 or square<F(1,4);max_count=3 if sign<0 else 5
  previous=(F(1),F(0));current=(F(0),F(1));checks=[]
  for k in range(1,max_count+1):
   a,b=current;assert a*b==0;value=a*a+b*b*square;assert value!=1;checks.append({'edgeSectors':k,'cosineSquaredOfAngleSum':str(value)})
   previous,current=current,(2*b*square-previous[0],2*a-previous[1])
  result.update(heesch=0,verified=True,certificate='uniform-edge-angle',maximumEdgeSectors=max_count,checks=checks,scope='All Euclidean rigid motions; generic root-edge point permits edge sectors and flat-face half-spaces. No face-to-face assumption.')
 else:result.update(heesch=None,verified=False,status='This angle test does not decide the mixed-dihedral case.')
 rows.append(result)
pathlib.Path('data/heesch-catalog/edge-obstructions.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
