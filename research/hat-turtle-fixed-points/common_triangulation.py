import functools,math

def common_triangulation(U,V,sign):
 n=len(U);lower=1/math.sqrt(3);upper=math.sqrt(3)
 def cross(a,b):return (a.conjugate()*b).imag
 def margin(i,j,k):
  u1,u2=U[j]-U[i],U[k]-U[i];v1,v2=V[j]-V[i],V[k]-V[i]
  A=sign*cross(u1,u2);B=sign*(cross(u1,v2)+cross(v1,u2));C=sign*cross(v1,v2)
  ks=[lower,upper]
  if C>1e-9 and lower<-B/(2*C)<upper:ks.append(-B/(2*C))
  return min(A+B*t+C*t*t for t in ks)
 @functools.lru_cache(None)
 def solve(i,j):
  if j<=i+1:return (float('inf'),[])
  best=None
  for k in range(i+1,j):
   m=margin(i,k,j)
   if m<1e-8:continue
   a,b=solve(i,k),solve(k,j)
   if a is None or b is None:continue
   score=min(m,a[0],b[0])
   if best is None or score>best[0]:best=(score,a[1]+[(i,k,j)]+b[1])
  return best
 result=solve(0,n-1)
 if result is None:raise ValueError('No strictly positive common triangulation')
 return result[1],result[0]
