"""Fit equivariant finite allowed-state markings to the cold five-tile core.
These fits are hypotheses, never certified search exclusions.
"""
import argparse,json,itertools,time,sys,pathlib
from threading import Timer
from pysat.solvers import Glucose3
ROOT=pathlib.Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args();OUT=pathlib.Path(a.output);OUT.mkdir(parents=True,exist_ok=True)
D=json.loads((ROOT/'data/nonacube-cold-learning/study.json').read_text());fixed=D['minimal']['fixed'];normal=[2,1,0]
gens=[((1,0,2),(1,1,1)),((0,2,1),(1,1,1)),((0,1,2),(-1,1,1))]
def tr(p,g):return tuple(g[1][i]*p[g[0][i]] for i in range(3))
def parity(p):return (-1)**sum(p[i]>p[j] for i in range(3) for j in range(i+1,3))
def run(rank,extent,action,mode):
 begin=time.time();points=list(itertools.product(range(-extent,extent+1,2),repeat=3));idx={p:i for i,p in enumerate(points)};states=list(itertools.product([-1,0,1],repeat=3)) if rank==3 else [(i,) for i in [-2,-1,0,1,2]];vi={v:i for i,v in enumerate(states)};P=len(points);V=len(states);parent=list(range(3*P*V))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def union(a,b):
  a=root(a);b=root(b)
  if a!=b:parent[b]=a
 def slot(oi,pi,v):return (oi*P+pi)*V+v
 for g in gens:
  sm=[vi[tr(v,g)] if rank==3 else vi[(v[0]*(parity(g[0])*g[1][0]*g[1][1]*g[1][2] if action=='sign' else 1),)] for v in states]
  for oi in range(3):
   newoi=normal.index(g[0].index(normal[oi]))
   for pi,p in enumerate(points):
    pj=idx[tr(p,g)]
    for v in range(V):union(slot(oi,pi,v),slot(newoi,pj,sm[v]))
 roots={};variables=[]
 for i in range(len(parent)):
  r=root(i)
  if r not in roots:roots[r]=len(roots)+1
  variables.append(roots[r])
 allowed=lambda oi,pi:tuple(variables[slot(oi,pi,v)] for v in range(V))
 contributions={}
 for role,s in enumerate(fixed):
  for pi,p in enumerate(points):q=tuple(p[i]+s['translation'][i] for i in range(3));contributions.setdefault(q,[]).append((role,allowed(s['oi'],pi)))
 positives=set()
 for absent in range(5):
  for rows in contributions.values():
   sig=tuple(sorted(set(row for role,row in rows if role!=absent)))
   if sig:positives.add(sig)
 negative=[tuple(sorted(set(row for _,row in rows))) for q,rows in contributions.items() if len(rows)==5 and (mode=='free' or q==tuple(D['minimal']['deadPoint']))]
 clauses=[];top=len(roots)
 for sig in sorted(positives):
  ws=[]
  for v in range(V):
   top+=1;ws.append(top)
   for row in sig:clauses.append([-top,row[v]])
  clauses.append(ws)
 bs=[]
 for sig in negative:
  top+=1;bs.append(top)
  for v in range(V):clauses.append([-top]+[-row[v] for row in sig])
 clauses.append(bs)
 build=time.time()-begin
 with Glucose3(bootstrap_with=clauses) as solver:
  timer=Timer(30,solver.interrupt);timer.start()
  try:answer=solver.solve_limited(expect_interrupt=True)
  finally:timer.cancel();timer.join()
  result={'anchorMode':mode,'rank':rank,'extentHalfUnits':extent,'action':action,'alphabetSize':V,'prototypeSlots':3*P,'independentMemberships':len(roots),'variables':top,'clauses':len(clauses),'buildSeconds':build,'seconds':time.time()-begin,'status':'SAT' if answer is True else 'UNSAT' if answer is False else 'unknown','stats':solver.accum_stats()}
  if answer is True:
   model=set(solver.get_model());fields=[[[v for v in range(V) if variables[slot(oi,pi,v)] in model] for pi in range(P)] for oi in range(3)]
   result['nonwildcardSlots']=sum(len(a)!=V for field in fields for a in field);result['emptySlots']=sum(not a for field in fields for a in field)
   assert not result['emptySlots']
   # All proper subsets, every marked world point, independent bit-set replay.
   for mask in range(32):
    failed=False
    for q,rows in contributions.items():
     common=set(range(V))
     for role,row in rows:
      if mask&(1<<role):common.intersection_update(v for v,x in enumerate(row) if x in model)
     failed |= not common
    assert failed==(mask==31)
   json.dump({'result':result,'points':points,'states':states,'fields':fields},open(OUT/('%s-%d-%s-%d.json'%(mode,rank,action,extent)),'w'))
 print(json.dumps(result),flush=True)
for mode in ['free','gap']:
 for rank,action in [(1,'trivial'),(1,'sign'),(3,'standard')]:
  for extent in ([3,5,7] if mode=='free' else [5,7]):run(rank,extent,action,mode)
