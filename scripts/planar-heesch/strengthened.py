"""Exact-distance parent constraints: an additional complete SAT control."""
import argparse,collections,json,pathlib,time,threading,gzip,hashlib,tempfile,subprocess
from pysat.solvers import Glucose4
from engine import Grid,build,verify

def strengthen(grid,data):
 inc=collections.defaultdict(list)
 for (i,j),v in data['ids'].items():
  for q in data['tiles'][i]:inc[q,j].append(v)
 for (i,j),v in data['ids'].items():
  if j==1:continue
  near=grid.halo(data['tiles'][i])-data['tiles'][i]
  if near&data['root']:
   data['clauses'].append([-v]);continue
  parents={w for q in near for w in inc.get((q,j-1),())}
  data['clauses'].append([-v]+sorted(parents))
 return data

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--seconds',type=float,default=180);parser.add_argument('--checker',required=True);args=parser.parse_args()
 row=next(r for r in json.load(open('data/planar-heesch/catalog.json')) if r['id']=='iamond-20-131');g=Grid(row['family']);start=time.perf_counter();d=strengthen(g,build(g,g.from_source(row['cells']),5))
 r=dict(id=row['id'],family=row['family'],cells=row['cells'],depth=5,encoding='exact-parent',solver='Glucose4',buildSeconds=time.perf_counter()-start,variables=d['variables'],clauses=len(d['clauses']))
 with Glucose4(bootstrap_with=d['clauses'],with_proof=True) as s:
  start=time.perf_counter();timer=threading.Timer(args.seconds,s.interrupt);timer.start()
  try:answer=s.solve_limited(expect_interrupt=True)
  finally:timer.cancel();timer.join()
  r.update(status='UNSAT' if answer is False else 'SAT' if answer is True else 'unknown',solveSeconds=time.perf_counter()-start,stats=s.accum_stats());proof='\n'.join(s.get_proof())+'\n' if answer is False else None
  if answer is True:
   model=set(s.get_model());chosen=sorted({i for (i,j),v in d['ids'].items() if v in model});r['witness']=verify(g,g.from_source(row['cells']),d['root'],[d['tiles'][i] for i in chosen],5)
 out=pathlib.Path('data/planar-heesch/longer-runs/iamond-20-131-parent-k5')
 if proof is not None:
  cnf=f"p cnf {d['variables']} {len(d['clauses'])}\n"+''.join(' '.join(map(str,c))+' 0\n' for c in d['clauses'])
  for suffix,txt in [('cnf',cnf),('drup',proof)]:
   raw=txt.encode();r[suffix+'SHA256']=hashlib.sha256(raw).hexdigest()
   with gzip.GzipFile(str(out)+'.'+suffix+'.gz','wb',mtime=0) as f:f.write(raw)
  with tempfile.TemporaryDirectory() as tmp:
   a=pathlib.Path(tmp)/'f.cnf';b=pathlib.Path(tmp)/'p.drup';a.write_text(cnf);b.write_text(proof);start=time.perf_counter()
   check=subprocess.run([args.checker,str(a),str(b)],capture_output=True,text=True,timeout=180)
   r.update(proofVerified='s VERIFIED' in check.stdout,proofCheckSeconds=time.perf_counter()-start);assert r['proofVerified'];pathlib.Path(str(out)+'.checker.log').write_text(check.stdout+check.stderr)
 pathlib.Path(str(out)+'.json').write_text(json.dumps(r));print(json.dumps(r),flush=True)
