"""Exact arithmetic certificate for fixed points on all reflected tiles in the patch.

The material surface is a common triangulation that remains embedded throughout
hat-to-turtle deformation. Coefficients live in Q(sqrt(5)); sign tests are exact.
"""
from fractions import Fraction as F
from functools import lru_cache
import json,math,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).resolve().parent
D=json.loads((ROOT/'apps/hat-turtle-projection/patch.json').read_text())
A=json.loads((HERE/'anchors.json').read_text())

class Q5:
 def __init__(self,a=0,b=0):self.a,self.b=F(a),F(b)
 def __add__(self,o):
  if not isinstance(o,Q5):o=Q5(o)
  return Q5(self.a+o.a,self.b+o.b)
 __radd__=__add__
 def __neg__(self):return Q5(-self.a,-self.b)
 def __sub__(self,o):return self+-asq(o)
 def __rsub__(self,o):return asq(o)+-self
 def __mul__(self,o):
  o=asq(o);return Q5(self.a*o.a+5*self.b*o.b,self.a*o.b+self.b*o.a)
 __rmul__=__mul__
 def __truediv__(self,o):
  o=asq(o);n=o.a*o.a-5*o.b*o.b
  if not n:raise ZeroDivisionError
  return self*Q5(o.a/n,-o.b/n)
 def sign(self):
  if not self.b:return (self.a>0)-(self.a<0)
  if not self.a:return (self.b>0)-(self.b<0)
  if (self.a>0)==(self.b>0):return (self.a>0)-(self.a<0)
  strong=self.a*self.a-5*self.b*self.b
  v=self.a if strong>0 else self.b
  return (v>0)-(v<0)
 def __eq__(self,o):o=asq(o);return self.a==o.a and self.b==o.b
 def approx(self):return float(self.a)+math.sqrt(5)*float(self.b)
 def json(self):return [str(self.a),str(self.b)]
def asq(x):return x if isinstance(x,Q5) else Q5(x)
def defect(q):
 p,t,r,s=q
 return (4*r-2*p-t-Q5(0,1)*t,4*r+8*s-3*t+Q5(0,1)*(2*p+t))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def weights(a,b,c):
 target=(Q5(4),Q5(14));den=cross(sub(b,a),sub(c,a))
 wb=cross(sub(target,a),sub(c,a))/den;wc=cross(sub(b,a),sub(target,a))/den
 return [1-wb-wc,wb,wc]
@lru_cache(None)
def triangle_margin(d1,d2):
 p,q,r,s=d1;P,Q,R,S=d2
 x,y=F(p)+F(q,2),F(q,2);X,Y=F(P)+F(Q,2),F(Q,2)
 vx,vy=F(r,2),F(r,2)+s;VX,VY=F(R,2),F(R,2)+S
 orient=-1
 aa=orient*(x*Y-y*X);bb=orient*(x*VY-3*y*VX+3*vx*Y-vy*X);cc=orient*(vx*VY-vy*VX)
 # Area/cos(theta)^2 = sqrt(3)*(aa + bb*k/sqrt(3) + cc*k^2).
 values=[aa+bb/3+cc/3,aa+bb+3*cc]
 if cc>0 and F(1,3)<-bb/(6*cc)<1:values.append(aa-bb*bb/(12*cc))
 assert min(values)>0,(aa,bb,cc)
 return min(values)
# Verify an oriented combinatorial disk: each diagonal occurs in both directions,
# and the only unpaired edges are exactly the fourteen boundary edges.
from collections import Counter
edges=Counter((a,b) for t in A['triangulation'] for a,b in zip(t,t[1:]+t[:1]))
assert len(A['triangulation'])==12
for i in range(14):
 assert edges[(i,(i+1)%14)]==1 and edges[((i+1)%14,i)]==0
for (a,b),count in edges.items():
 assert count==1
 if b!=(a+1)%14:assert edges[(b,a)]==1
Q=D['vertices'];selected={x['tile']:x for x in A['anchors']}
assert set(selected)=={i for i,label in enumerate(D['labels']) if label=='H1'}
minimum=1.;min_margin=None;records=[]
for index,sol in selected.items():
 ids=D['tiles'][index]
 for tri in A['triangulation']:
  a,b,c=[Q[ids[i]] for i in tri]
  m=triangle_margin(tuple(y-x for x,y in zip(a,b)),tuple(y-x for x,y in zip(a,c)))
  min_margin=m if min_margin is None else min(min_margin,m)
 tri=sol['triangle'];assert tri in A['triangulation'];points=[Q[ids[i]] for i in tri]
 ws=weights(*[defect(q) for q in points]);assert all(w.sign()>0 for w in ws)
 coord=[sum(w*q[k] for w,q in zip(ws,points)) for k in range(4)]
 assert defect(coord)==(Q5(4),Q5(14))
 minimum=min(minimum,*[w.approx() for w in ws])
 records.append({'tile':index,'triangle':tri,'weights':[w.approx() for w in ws],'weightsExact':[w.json() for w in ws],'coordinates':[x.approx() for x in coord]})
certificate={'status':'exact finite-patch certificate','reflectedTiles':len(records),'totalTiles':len(D['tiles']),'field':'a + b sqrt(5), with a,b rational','alpha':A['alpha'],'beta':A['beta'],'defectPlane':{'x':4,'y':14},'triangulation':A['triangulation'],'minimumTrianglePolynomialOverSqrt3':str(min_margin),'minimumApproxBarycentricWeight':minimum,'allWeightsStrictlyPositive':True,'allDefectEquationsExact':True,'infiniteTilingClaim':False,'anchors':records}
(HERE/'certificate.json').write_text(json.dumps(certificate,indent=2)+'\n')
print(json.dumps({k:v for k,v in certificate.items() if k!='anchors'},indent=2))

# Ship only the derived floating-point coordinates to the browser. The exact
# weights above remain in the independent certificate.
runtime={k:certificate[k] for k in ['totalTiles','reflectedTiles','alpha','beta']}
runtime['certificate']='../../research/hat-turtle-fixed-points/certificate.json'
runtime['anchors']=[{k:a[k] for k in ['tile','coordinates','triangle','weights']} for a in records]
(ROOT/'apps/hat-turtle-projection/fixed-marks.json').write_text(json.dumps(runtime,separators=(',',':'))+'\n')
