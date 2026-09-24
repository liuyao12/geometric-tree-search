#!/usr/bin/env python3
"""One additional blind phase-order control; clauses and geometry unchanged."""
import pathlib,sys,json,time,threading,importlib.util
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts/heesch-catalog'))
from pysat.solvers import Glucose3
from verify_papoutsis import rotations
spec=importlib.util.spec_from_file_location('original',ROOT/'scripts/search-nonacube-two-corona.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
id='polycube_p9_02127';v=next(r['voxels'] for r in json.load(open(ROOT/'data/heesch-catalog/catalog.json'))['systems'] if r['id']==id);m.SHAPES=tuple(sorted(rotations(v)));d=m.build()
with Glucose3(bootstrap_with=d['clauses']) as s:
 s.set_phases(list(range(1,len(d['universe'])+1)))
 begin=time.perf_counter();timer=threading.Timer(60,s.interrupt);timer.start()
 try:a=s.solve_limited(expect_interrupt=True)
 finally:timer.cancel();timer.join()
 r={'id':id,'k':2,'solver':'Glucose3','variant':'All placement phases prefer selected; no motif or constraints supplied','budgetSeconds':60,'status':'SAT' if a is True else 'UNSAT' if a is False else 'unknown','seconds':time.perf_counter()-begin,'stats':s.accum_stats()}
 if a:
  positive=set(s.get_model());chosen=[x for i,x in enumerate(d['universe'],1) if i in positive];first=[x for x in chosen if x in d['first']];needed=m.halo(d['root'].union(*(m.cells(x) for x in first)));r['witness']=m.verify(d,[x for x in chosen if m.cells(x)&needed])
(ROOT/'data/heesch-catalog/positive-controls'/f'{id}-positive-phases.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='witness'}),flush=True)
