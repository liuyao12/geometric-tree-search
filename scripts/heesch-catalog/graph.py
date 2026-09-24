#!/usr/bin/env python3
"""Specialized fixed-corona voxel graph search, optionally with certified affine anchors."""
import argparse,importlib.util,json,pathlib,time
HERE=pathlib.Path(__file__).parent;spec=importlib.util.spec_from_file_location('corona',HERE/'corona.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
class Timeout(Exception):pass
def bits(mask):
 while mask:
  bit=mask&-mask;yield bit.bit_length()-1;mask-=bit
class Search:
 def __init__(self,data,learn,seconds,k=1):
  self.k=k
  self.d=data;self.learn=learn;self.seconds=seconds;self.poses=data['universe'];self.N=len(self.poses);self.inverse={(oi,tuple(t)):v for v,(oi,t) in enumerate(self.poses)};self.points=sorted(data['near'] if k==1 else data['target']);self.domains=[sum(1<<(v-1) for v in data['by'][q]) for q in self.points];by={q:sum(1<<(v-1) for v in vs) for q,vs in data['by'].items()};self.bad=[];self.cover=[];self.need=[];pi={q:i for i,q in enumerate(self.points)}
  for s in self.poses:
   cells=data['cells'](s);mask=0
   for q in cells:mask|=by[q]
   self.bad.append(mask);self.cover.append(sum(1<<pi[q] for q in cells if q in pi));self.need.append(sum(1<<pi[q] for q in data['requirements'].get(s,[]) if q in pi))
  self.chosen=0;self.stack=[];self.rules=[];self.known=set();self.inc=[[] for _ in self.poses];self.block=[0]*self.N;self.blocked=0;self.conflicts=0;self.nodes=self.leaves=self.decisions=self.forced=0;self.markEliminations=0;self.solution=None
 def update(self,r):
  old=r['state']
  if old==-2:self.conflicts-=1
  elif old>=0:
   self.block[old]-=1
   if self.block[old]==0:self.blocked&=~(1<<old)
  missing=r['mask']&~self.chosen
  if not missing:r['state']=-2;self.conflicts+=1
  elif missing&(missing-1)==0:
   v=missing.bit_length()-1;r['state']=v;self.block[v]+=1;self.blocked|=missing;self.markEliminations+=1
  else:r['state']=-1
 def push(self,v):
  assert not self.chosen&(1<<v);self.chosen|=1<<v;self.stack.append(v)
  for r in self.inc[v]:self.update(r)
 def pop(self,v):
  assert self.stack.pop()==v;self.chosen&=~(1<<v)
  for r in self.inc[v]:self.update(r)
 def learn_dead(self,q):
  if not self.learn:return
  domain=self.domains[q];core=list(self.stack)
  def covered(xs):
   if self.points[q] not in self.d['near'] and not any(self.need[v]&(1<<q) for v in xs):return False
   m=0
   for v in xs:m|=self.bad[v]
   return domain&~m==0
  if not covered(core):return # Never promote a dead point caused only by a branch exclusion.
  point=self.points[q];core.sort(key=lambda v:-sum((self.poses[v][1][i]-point[i])**2 for i in range(3)))
  for v in core[:]:
   trial=[w for w in core if w!=v]
   if covered(trial):core=trial
  mask=sum(1<<v for v in core)
  if not mask or mask in self.known:return
  assert covered(core) and all(not covered([w for w in core if w!=v]) for v in core)
  # Geometric atom at -translation meets the fixed root anchor only for this pose.
  role_atoms=[{'orientation':self.poses[v][0],'offset':[-x for x in self.poses[v][1]],'role':i} for i,v in enumerate(core)]
  assert [self.inverse[(a['orientation'],tuple(-x for x in a['offset']))] for a in role_atoms]==core
  r={'mask':mask,'state':-1,'roles':core,'requiredPoint':point,'atoms':role_atoms};self.rules.append(r);self.known.add(mask)
  for v in core:self.inc[v].append(r)
  self.update(r)
 def dfs(self,alive,uncovered,covered=0):
  self.nodes+=1
  if self.nodes%256==1 and time.perf_counter()-self.started>self.seconds:raise Timeout()
  forced=[]
  try:
   while True:
    alive&=~self.blocked
    if self.conflicts:self.leaves+=1;return False
    if not uncovered:self.solution=self.stack[:];self.leaves+=1;return True
    best=None;degree=self.N+1;bestkey=None;singleton=None
    for q in bits(uncovered):
     options=self.domains[q]&alive;n=options.bit_count()
     if n==0:self.leaves+=1;self.learn_dead(q);return False
     key=(0 if self.points[q] in self.d['near'] else 1,n,q)
     if bestkey is None or key<bestkey:best=(q,options);degree=n;bestkey=key
     if n==1 and singleton is None:singleton=(q,options)
    if singleton is not None:best=singleton;degree=1
    if degree!=1:break
    v=best[1].bit_length()-1;self.forced+=1;self.push(v);forced.append(v);alive&=~self.bad[v];covered|=self.cover[v];uncovered=(uncovered|self.need[v])&~covered
   self.decisions+=1
   for v in bits(best[1]):
    if self.blocked&(1<<v):continue
    self.push(v)
    try:
     if self.dfs(alive&~self.bad[v],(uncovered|self.need[v])&~(covered|self.cover[v]),covered|self.cover[v]):return True
    finally:self.pop(v)
    alive&=~(1<<v)
   return False
  finally:
   for v in reversed(forced):self.pop(v)
 def run(self):
  self.started=time.perf_counter()
  try:answer=self.dfs((1<<self.N)-1,sum(1<<i for i,q in enumerate(self.points) if q in self.d['near']));status='SAT' if answer else 'UNSAT'
  except Timeout:status='unknown'
  elapsed=time.perf_counter()-self.started;assert not self.stack and self.chosen==0
  result={'status':status,'seconds':elapsed,'nodes':self.nodes,'terminalLeavesVisited':self.leaves,'branchPoints':self.decisions,'forcedMoves':self.forced,'learnedPatterns':len(self.rules),'roleAtoms':sum(len(r['roles']) for r in self.rules),'markUnitEvents':self.markEliminations,'rules':[{'roles':r['roles'],'requiredPoint':r['requiredPoint'],'atoms':r['atoms']} for r in self.rules]}
  if self.solution is not None:result['witness']=c.verify(self.d,[self.poses[v] for v in self.solution],self.k)
  return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ids',required=True);p.add_argument('--seconds',type=float,default=30);p.add_argument('--out',required=True);p.add_argument('--max-volume-two-corona',type=int,default=20);p.add_argument('--lane',choices=['both','unmarked','affine'],default='both');p.add_argument('--k',type=int,choices=[1,2],default=1);a=p.parse_args();out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True);rows=json.load(open('data/heesch-catalog/catalog.json'))['systems']
 for row in rows:
  if row['id'] not in a.ids.split(','):continue
  if a.k==2 and len(row['voxels'])>a.max_volume_two_corona:
   r={'id':row['id'],'k':2,'status':'unknown','reason':'Declared volume guard for quadratic graph-overlap storage','volumeGuard':a.max_volume_two_corona};(out/(row['id']+'-resource-limit.json')).write_text(json.dumps(r));print(json.dumps(r),flush=True);continue
  for learn in ([False,True] if a.lane=='both' else [a.lane=='affine']):
   start=time.perf_counter();data=c.build(row['voxels'],a.k);s=Search(data,learn,a.seconds,a.k);prep=time.perf_counter()-start;r=s.run();r.update(id=row['id'],k=a.k,lane='affine-GCTS' if learn else 'unmarked-graph',preparationSeconds=prep)
   (out/(row['id']+'-'+r['lane']+'.json')).write_text(json.dumps(r));print(json.dumps({k:v for k,v in r.items() if k not in ['rules','witness']}),flush=True)
