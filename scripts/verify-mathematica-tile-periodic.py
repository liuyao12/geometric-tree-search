#!/usr/bin/env python3
"""Independently verify the declared rigid-motion infinite tiling certificate.

Reconstruct from the original Mathematica vertices/faces and explicit integer
rigid motions. Verify every point residue with exact t-values, then certify
continuous geometry by rational clipping and cancellation of oriented faces.
No SAT solver, JavaScript orientation numbering, or floating arithmetic needed.
"""
from fractions import Fraction as Q
from collections import defaultdict
from itertools import product
from functools import reduce
from math import gcd,lcm
import json,hashlib,importlib.util,argparse
from pathlib import Path

def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def primitive(v):
 m=lcm(*(x.denominator if isinstance(x,Q) else 1 for x in v)); w=[int(x*m) for x in v];g=reduce(gcd,w);w=tuple(x//g for x in w)
 return tuple(-x for x in w) if next(x for x in w if x)<0 else w

def clip(vs,axis,bound,sgn):
 out=[]
 for a,b in zip(vs,vs[1:]+vs[:1]):
  da=sgn*(a[axis]-bound);db=sgn*(b[axis]-bound)
  if da>=0:out.append(a)
  if (da>0 and db<0) or (da<0 and db>0):
   r=Q(da,da-db);out.append(tuple(x+r*(y-x) for x,y in zip(a,b)))
 return out

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--certificate',type=Path,default=root/'data/mathematica-lattice-tile-periodic.json')
parser.add_argument('--output',type=Path)
args=parser.parse_args()
cert=json.loads(args.certificate.read_text())
source_path=root/'data/mathematica-lattice-tile.json'
assert hashlib.sha256(source_path.read_bytes()).hexdigest()==cert['source_sha256']
spec=importlib.util.spec_from_file_location('derive_tile',root/'scripts/derive-mathematica-lattice-tile.py')
derive=importlib.util.module_from_spec(spec);spec.loader.exec_module(derive)
tile=derive.derive(json.loads(source_path.read_text()))
# Certify that the original shell is embedded: any two convex faces intersect
# only in their combinatorially shared vertex or edge. Segment/polygon clipping
# uses rational intervals, including coplanar edges.
V=tile['vertices'];F=tile['faces']
def segment_face(a,b,face):
 n=cross(sub(V[face[1]],V[face[0]]),sub(V[face[2]],V[face[0]]))
 da=dot(n,sub(a,V[face[0]]));db=dot(n,sub(b,V[face[0]]))
 if da==db and da:return []
 lo,hi=Q(0),Q(1)
 if da!=db:
  lo=hi=Q(da,da-db)
  if not 0<=lo<=1:return []
 for i,j in zip(face,face[1:]+face[:1]):
  e=sub(V[j],V[i]);sa=dot(n,cross(e,sub(a,V[i])));sb=dot(n,cross(e,sub(b,V[i])))
  delta=sb-sa
  if delta>0:lo=max(lo,Q(-sa,delta))
  elif delta<0:hi=min(hi,Q(-sa,delta))
  elif sa<0:return []
  if lo>hi:return []
 return [tuple(x+t*(y-x) for x,y in zip(a,b)) for t in (lo,hi)]
for i,f in enumerate(F):
 for g in F[i+1:]:
  shared=set(f)&set(g)
  assert len(shared)<=2
  for a,b in ((f,g),(g,f)):
   for u,v in zip(a,a[1:]+a[:1]):
    for p in segment_face(V[u],V[v],b):
     assert shared
     if len(shared)==1:assert p==tuple(V[next(iter(shared))])
     else:
      x,y=(V[k] for k in shared)
      assert cross(sub(p,x),sub(y,x))==(0,0,0) and dot(sub(p,x),sub(p,y))<=0
D=cert['dimensions']
assert len(D)==3 and all(type(d) is int and d>0 for d in D)
assert cert['period_vectors']==[[D[0],0,0],[0,D[1],0],[0,0,D[2]]]
assert type(cert['include_reflections']) is bool and cert['capacity']==24
data={'dimensions':D,'placements':[]}
totals=defaultdict(int)
for p in cert['placements']:
 R=p['rotation'];t=p['translation']
 assert len(R)==3 and all(len(row)==3 and all(type(x) is int for x in row) for row in R)
 assert len(t)==3 and all(type(x) is int for x in t)
 assert [[dot(a,b) for b in R] for a in R]==[[1,0,0],[0,1,0],[0,0,1]]
 determinant=dot(R[0],cross(R[1],R[2]))
 assert determinant in ([1,-1] if cert['include_reflections'] else [1])
 vertices=[tuple(dot(row,v) for row in R) for v in tile['vertices']]
 data['placements'].append({'vertices':vertices,'faces':[list(reversed(f)) for f in tile['faces']] if determinant<0 else tile['faces'],'translation':t})
 for point in tile['points']:
  q=tuple((dot(R[i],point['pos'])+t[i])%D[i] for i in range(3))
  totals[q]+=point['weight']
cell_volume=D[0]*D[1]*D[2]
assert len(totals)==cell_volume and set(totals.values())=={24}
assert len(data['placements'])*tile['volume']==cell_volume
planes=defaultdict(list);nfaces=0
for p in data['placements']:
 vs=[tuple(x+y for x,y in zip(v,p['translation'])) for v in p['vertices']]
 ranges=[range(-(max(v[i] for v in vs)//D[i]),(D[i]-min(v[i] for v in vs))//D[i]+1) for i in range(3)]
 for shift in product(*ranges):
  transformed=[tuple(v[i]+shift[i]*D[i] for i in range(3)) for v in vs]
  for f in p['faces']:
   polygon=[transformed[i] for i in f]
   for axis in range(3):
    polygon=clip(polygon,axis,0,1);polygon=clip(polygon,axis,D[axis],-1)
   if len(polygon)<3:continue
   area=(0,0,0)
   for a,b in zip(polygon,polygon[1:]+polygon[:1]):area=tuple(x+y for x,y in zip(area,cross(a,b)))
   if not dot(area,area):continue
   n=primitive(area);key=(*n,dot(n,polygon[0]));planes[key].append(polygon);nfaces+=1
bad=[];segments=0
for plane,polygons in planes.items():
 lines=defaultdict(lambda:defaultdict(Q))
 for poly in polygons:
  for a,b in zip(poly,poly[1:]+poly[:1]):
   if a==b:continue
   v=primitive(sub(b,a));axis=next(i for i,x in enumerate(v) if x)
   key=(*v,*cross(a,v));lo,hi=a[axis],b[axis];sgn=1
   if lo>hi:lo,hi,sgn=hi,lo,-1
   lines[key][lo]+=sgn;lines[key][hi]-=sgn;segments+=1
 for line,jumps in lines.items():
  if any(jumps.values()):bad.append({'plane':str(plane),'line':str(line),'jumps':str({k:v for k,v in jumps.items() if v})})
assert not bad, f'Nonzero oriented boundary: {bad[:4]}'
report={'result':'certified_infinite_tiling','exact_rational':True,'include_reflections':cert['include_reflections'],'source_shell_embedded':True,
        'dimensions':D,'tiles_per_cell':len(data['placements']),'cell_volume':cell_volume,
        'point_residues_verified':len(totals),'weight_at_every_residue':24,
        'clipped_faces':nfaces,'planes':len(planes),'edge_segments':segments,
        'uncancelled_lines':len(bad),'boundary_cancels':True,
        'geometry_proof':'Oriented surface contributions cancel exactly; periodic covering multiplicity is constant. Total tile volume equals cell volume, so the multiplicity is one.'}
print(json.dumps(report,indent=2))
if args.output:args.output.write_text(json.dumps(report,indent=2)+'\n')
