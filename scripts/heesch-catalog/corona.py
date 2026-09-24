#!/usr/bin/env python3
"""Full touching-tile coronas for integer-grid polycubes; specialized SAT scheduling."""
import argparse,collections,gzip,hashlib,itertools,json,pathlib,time,threading
from pysat.solvers import Glucose3
from pysat.card import CardEnc,EncType
OFF=list(itertools.product((-1,0,1),repeat=3))
def norm(v):
 lo=tuple(min(p[a] for p in v) for a in range(3));return tuple(sorted(tuple(p[a]-lo[a] for a in range(3)) for p in v))
def orientations(voxels):
 out=set()
 for p in itertools.permutations(range(3)):
  parity=(-1)**sum(p[i]>p[j] for i in range(3) for j in range(i+1,3))
  for signs in itertools.product((-1,1),repeat=3):
   if parity*signs[0]*signs[1]*signs[2]==1:out.add(norm([tuple(signs[a]*v[p[a]] for a in range(3)) for v in voxels]))
 return sorted(out)
def halo(vs):return {tuple(v[a]+d[a] for a in range(3)) for v in vs for d in OFF}
def lattice_certificate(vs):
 n=len(vs)
 for coeff in itertools.product(range(n),repeat=3):
  residues=[sum(a*b for a,b in zip(v,coeff))%n for v in vs]
  if len(set(residues))==n:return {'kind':'cyclic-lattice','modulus':n,'coefficients':coeff,'residues':residues,'verified':True}
def build(vs,k):
 shapes=orientations(vs);root=frozenset(shapes[0]);cache={}
 def cells(s):
  if s not in cache:cache[s]=frozenset(tuple(v[a]+s[1][a] for a in range(3)) for v in shapes[s[0]])
  return cache[s]
 def candidates(target):
  pool=set()
  for q in sorted(target):
   for oi,o in enumerate(shapes):
    for v in o:
     s=(oi,tuple(q[a]-v[a] for a in range(3)))
     if s not in pool and not cells(s)&root:pool.add(s)
  return pool
 near=halo(root)-root;first=candidates(near);requirements={}
 if k==2:requirements={s:halo(cells(s))-root-cells(s) for s in first}
 target=set(near).union(*requirements.values());universe=sorted(first if k==1 else candidates(target));by=collections.defaultdict(list)
 for i,s in enumerate(universe,1):
  for q in sorted(cells(s)):by[q].append(i)
 clauses=[];top=len(universe)
 for q in sorted(by):
  if len(by[q])>1:
   e=CardEnc.atmost(by[q],1,top_id=top,encoding=EncType.seqcounter);top=e.nv;clauses.extend(e.clauses)
 for q in sorted(near):clauses.append(by[q])
 ids={s:i+1 for i,s in enumerate(universe)}
 for s in sorted(requirements):
  for q in sorted(requirements[s]):clauses.append([-ids[s]]+by[q])
 return {'shapes':shapes,'root':root,'first':first,'universe':universe,'cells':cells,'clauses':clauses,'variables':top,'by':by,'near':near,'target':target,'requirements':requirements}
def verify(data,chosen,k):
 occupied=set(data['root']);tiles=[]
 for s in chosen:
  c=data['cells'](s);assert not occupied&c;occupied.update(c);tiles.append(c)
 inner=set(data['root']);layer_counts=[];remaining=list(tiles)
 for _ in range(k):
  required=halo(inner);assert required<=occupied
  layer=[t for t in remaining if t&required];remaining=[t for t in remaining if not t&required];layer_counts.append(len(layer));inner.update(set().union(*layer))
 return {'root':sorted(data['root']),'tiles':[sorted(t) for t in tiles],'layerCounts':layer_counts,'verified':True}
def run(row,k,seconds,out):
 start=time.perf_counter();data=build(row['voxels'],k);build_s=time.perf_counter()-start
 stem=out/(row['id']+'-k'+str(k));clauses=data['clauses'];result={'id':row['id'],'k':k,'buildSeconds':build_s,'placements':len(data['universe']),'variables':data['variables'],'clauses':len(clauses)}
 with Glucose3(bootstrap_with=clauses,with_proof=True) as solver:
  begin=time.perf_counter();timer=threading.Timer(seconds,solver.interrupt);timer.start()
  try:answer=solver.solve_limited(expect_interrupt=True)
  finally:timer.cancel();timer.join()
  result.update(status='SAT' if answer is True else 'UNSAT' if answer is False else 'unknown',solveSeconds=time.perf_counter()-begin,stats=solver.accum_stats())
  if answer is True:
   model=set(solver.get_model());chosen=[s for i,s in enumerate(data['universe'],1) if i in model];result['witness']=verify(data,chosen,k)
  if answer is False:
   cnf='p cnf %d %d\n'%(data['variables'],len(clauses))+''.join(' '.join(map(str,c))+' 0\n' for c in clauses);proof='\n'.join(solver.get_proof())+'\n'
   for suffix,txt in [('cnf',cnf),('drup',proof)]:
    with gzip.GzipFile(str(stem)+'.'+suffix+'.gz','wb',mtime=0) as f:f.write(txt.encode())
   result['formulaSHA256']=hashlib.sha256(cnf.encode()).hexdigest();result['proofSHA256']=hashlib.sha256(proof.encode()).hexdigest()
 (pathlib.Path(str(stem)+'.json')).write_text(json.dumps(result));print(json.dumps({key:v for key,v in result.items() if key!='witness'}),flush=True);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--catalog',default='data/heesch-catalog/catalog.json');p.add_argument('--out',required=True);p.add_argument('--ids',required=True);p.add_argument('--k',type=int,choices=[1,2],default=1);p.add_argument('--seconds',type=float,default=10);p.add_argument('--periodic',action='store_true');a=p.parse_args();out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 rows=[r for r in json.load(open(a.catalog))['systems'] if r.get('voxels') and (not a.ids or r['id'] in a.ids.split(','))]
 for row in rows:
  if a.periodic:
   cert=lattice_certificate(row['voxels']);result={'id':row['id'],'certificate':cert};(out/(row['id']+'-lattice.json')).write_text(json.dumps(result));print(json.dumps(result),flush=True)
  else:run(row,a.k,a.seconds,out)
