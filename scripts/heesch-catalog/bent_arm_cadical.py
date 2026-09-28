#!/usr/bin/env python3
"""Second SAT engine on the remaining centrally symmetric bend variant."""
import gzip,hashlib,json,pathlib,time
from pysat.solvers import Cadical195
import corona
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'data/bent-six-arm/variants'
row=next(r for r in json.loads((OUT/'catalog.json').read_text())['rows'] if r['id']=='bend_064')
data=corona.build(row['voxels'],1);start=time.perf_counter();answer=None
with Cadical195(bootstrap_with=data['clauses'],with_proof=True) as solver:
 while time.perf_counter()-start<120:
  solver.conf_budget(2000);answer=solver.solve_limited()
  if answer is not None:break
 result={'id':row['id'],'k':1,'solver':'Cadical195','budgetSeconds':120,'status':'SAT' if answer is True else 'UNSAT' if answer is False else 'unknown','searchAndSetupSeconds':time.perf_counter()-start,'placements':len(data['universe']),'variables':data['variables'],'clauses':len(data['clauses']),'stats':solver.accum_stats()}
 if answer is True:
  model=set(solver.get_model());result['witness']=corona.verify(data,[s for i,s in enumerate(data['universe'],1) if i in model],1)
 if answer is False:
  cnf=('p cnf %d %d\n'%(data['variables'],len(data['clauses']))+''.join(' '.join(map(str,c))+' 0\n' for c in data['clauses'])).encode();proof=('\n'.join(solver.get_proof())+'\n').encode()
  for suffix,value in [('cnf',cnf),('drup',proof)]:
   with gzip.GzipFile(str(OUT/(row['id']+'-k1.'+suffix+'.gz')),'wb',mtime=0) as f:f.write(value)
  result['formulaSHA256']=hashlib.sha256(cnf).hexdigest();result['proofSHA256']=hashlib.sha256(proof).hexdigest()
(OUT/(row['id']+'-k1.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='witness'}),flush=True)
