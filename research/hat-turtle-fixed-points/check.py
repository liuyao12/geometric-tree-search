"""Investigate copy-specific fixed material points in the existing lifted patch."""
import json,math,pathlib
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[2]
D=json.loads((ROOT/'apps/hat-turtle-projection/patch.json').read_text())
Q=np.array(D['vertices'],float);I=np.array(D['tiles']);P,Qc,R,S=Q.T
U=P+Qc/2+1j*math.sqrt(3)*Qc/2
V=math.sqrt(3)*R/2+1j*(R/2+S)
REF=np.where(np.array(D['labels'])=='H1')[0]
CU=U[I[REF]].mean(axis=1);CV=V[I[REF]].mean(axis=1)
u=CU-CU.mean();v=CV-CV.mean()
alpha_fit=np.vdot(u,v)/np.vdot(u,u)
print('alpha fit',alpha_fit,flush=True)
def cross(a,b):return (a.conjugate()*b).imag
def hull(points):
 p=sorted(set(complex(z) for z in points),key=lambda z:(z.real,z.imag))
 def half(p):
  h=[]
  for z in p:
   while len(h)>1 and cross(h[-1]-h[-2],z-h[-1])<=1e-10:h.pop()
   h.append(z)
  return h
 return half(p)[:-1]+half(p[::-1])[:-1]
def clip(poly,a,b):
 if not poly:return []
 out=[]
 for p,q in zip(poly,poly[1:]+poly[:1]):
  cp=cross(b-a,p-a);cq=cross(b-a,q-a)
  if cp>=-1e-10:out.append(p)
  if (cp>1e-10 and cq<-1e-10) or (cp<-1e-10 and cq>1e-10):out.append(p+(q-p)*cp/(cp-cq))
 return out
for alpha in [(math.sqrt(3)-1j*math.sqrt(5))/4,(math.sqrt(3)+1j*math.sqrt(5))/4,alpha_fit]:
 W=V-alpha*U
 common=hull(W[I[REF[0]]]);count=0
 for index in REF:
  h=hull(W[I[index]])
  for a,b in zip(h,h[1:]+h[:1]):common=clip(common,a,b)
  count+=1
  if not common:break
 area=abs(sum(cross(a,b) for a,b in zip(common,common[1:]+common[:1])))/2 if common else 0
 print('alpha',alpha,'intersected',count,'of',len(REF),'common convex hull vertices',len(common),'area',area,flush=True)
 if common:
  beta=sum(common)/len(common)
  print('candidate beta',beta,flush=True)

def in_triangle(p,a,b,c,eps=1e-9):
 den=cross(b-a,c-a)
 if abs(den)<1e-10:return None
 wb=cross(p-a,c-a)/den;wc=cross(b-a,p-a)/den;wa=1-wb-wc
 return (wa,wb,wc) if min(wa,wb,wc)>=-eps else None

def triangulate(poly):
 sign=1 if sum(cross(a,b) for a,b in zip(poly,poly[1:]+poly[:1]))>0 else -1
 rem=list(range(len(poly)));tri=[]
 while len(rem)>3:
  for k in range(len(rem)):
   a,b,c=rem[k-1],rem[k],rem[(k+1)%len(rem)]
   if sign*cross(poly[b]-poly[a],poly[c]-poly[a])<1e-9:continue
   if any(in_triangle(poly[j],poly[a],poly[b],poly[c]) is not None for j in rem if j not in (a,b,c)):continue
   tri.append((a,b,c));rem.pop(k);break
  else:raise RuntimeError('No ear')
 tri.append(tuple(rem));return tri,sign
alpha=(math.sqrt(3)-1j*math.sqrt(5))/4
W=V-alpha*U
first=I[REF[0]]
_,sign=triangulate(list((U[first]+V[first])/math.sqrt(2)))
from common_triangulation import common_triangulation
triangles,common_margin=common_triangulation(U[first],V[first],sign)
print('triangles',triangles,'sign',sign,flush=True)
mins=[]
for i,j,k in triangles:
 a,b,c=first[[i,j,k]];u1,u2=U[b]-U[a],U[c]-U[a];v1,v2=V[b]-V[a],V[c]-V[a]
 A=sign*cross(u1,u2);B=sign*(cross(u1,v2)+cross(v1,u2));C=sign*cross(v1,v2)
 ks=[1/math.sqrt(3),math.sqrt(3)]
 if C>1e-9 and min(ks)<-B/(2*C)<max(ks):ks.append(-B/(2*C))
 mins.append(min(A+B*t+C*t*t for t in ks))
print('minimum triangle determinant coefficients on full interval',mins,flush=True)
common=hull(W[first])
for index in REF:
 h=hull(W[I[index]])
 for a,b in zip(h,h[1:]+h[:1]):common=clip(common,a,b)
beta=math.sqrt(3)/2+1.75j
solutions=[];failed=[];minweight=1
for index in REF:
 ids=I[index];best=None
 for tri in triangles:
  weights=in_triangle(beta,*W[ids[list(tri)]])
  if weights is not None and (best is None or min(weights)>min(best[1])):best=(tri,weights)
 if best is None:failed.append(int(index))
 else:
  minweight=min(minweight,min(best[1]));solutions.append((int(index),best))
print('actual triangulated surface: found',len(solutions),'failed',len(failed),'min barycentric weight',minweight,'beta',beta,flush=True)
if not failed and min(mins)>1e-9:
 anchors=[]
 for index,(tri,weights) in solutions:
  ids=I[index][list(tri)];coord=sum(Q[id]*w for id,w in zip(ids,weights))
  anchors.append({'tile':index,'triangle':list(tri),'weights':list(map(float,weights)),'coordinates':list(map(float,coord))})
 result={'alpha':[alpha.real,alpha.imag],'beta':[beta.real,beta.imag],'reflectedTiles':len(REF),'triangulation':[list(t) for t in triangles],'minTriangleDeterminant':min(mins),'minBarycentricWeight':minweight,'anchors':anchors}
 (pathlib.Path(__file__).parent/'anchors.json').write_text(json.dumps(result,indent=2)+'\n')
