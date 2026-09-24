#!/usr/bin/env python3
"""Second blind SAT engine on the original encoder, without motif guidance."""
import argparse,sys,pathlib,importlib.util,json,time
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts/heesch-catalog'))
from pysat.solvers import Cadical195
from verify_papoutsis import rotations
spec=importlib.util.spec_from_file_location('original',ROOT/'scripts/search-nonacube-two-corona.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
OUT=ROOT/'data/heesch-catalog/positive-controls';rows={r['id']:r for r in json.load(open(ROOT/'data/heesch-catalog/catalog.json'))['systems']}
p=argparse.ArgumentParser();p.add_argument('--ids',default='polycube_p9_02127,polycube_p9_24025');p.add_argument('--seconds',type=float,default=120);args=p.parse_args()
for id in args.ids.split(','):
 old.SHAPES=tuple(sorted(rotations(rows[id]['voxels'])));data=old.build();begin=time.perf_counter();ans=None
 with Cadical195(bootstrap_with=data['clauses']) as solver:
  while time.perf_counter()-begin<args.seconds:
   solver.conf_budget(2000);ans=solver.solve_limited()
   if ans is not None:break
  r={'id':id,'k':2,'solver':'Cadical195','budgetSeconds':args.seconds,'motifSuppliedToSearch':False,'status':'SAT' if ans is True else 'UNSAT' if ans is False else 'unknown','searchAndSetupSeconds':time.perf_counter()-begin,'stats':solver.accum_stats()}
  if ans:
   m=set(solver.get_model());chosen=[s for i,s in enumerate(data['universe'],1) if i in m];first=[s for s in chosen if s in data['first']];needed=old.halo(data['root'].union(*(old.cells(s) for s in first)));chosen=[s for s in chosen if old.cells(s)&needed];r['witness']=old.verify(data,chosen)
 (OUT/(id+'-cadical-blind.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='witness'}),flush=True)
 if ans is False:raise RuntimeError('Positive control rejected')
