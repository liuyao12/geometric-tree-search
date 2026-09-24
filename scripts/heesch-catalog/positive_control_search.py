#!/usr/bin/env python3
"""Blind positive-control search with the original nonacube encoder.

Only tile geometry changes; periodic motif data is never passed to the solver.
A cutoff is unknown and never promoted to a contradiction.
"""
import argparse,sys,pathlib,importlib.util,json,time,threading,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts/heesch-catalog'))
from pysat.solvers import Glucose3
from verify_papoutsis import rotations
spec=importlib.util.spec_from_file_location('original',ROOT/'scripts/search-nonacube-two-corona.py');original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
import corona
OUT=ROOT/'data/heesch-catalog/positive-controls';OUT.mkdir(exist_ok=True)
rows={r['id']:r for r in json.load(open(ROOT/'data/heesch-catalog/catalog.json'))['systems']}
parser=argparse.ArgumentParser();parser.add_argument('--ids',default='polycube_p9_02127,polycube_p9_24025');parser.add_argument('--seconds',type=float,default=180);args=parser.parse_args()
for id in args.ids.split(','):
 begin=time.perf_counter();row=rows[id];original.SHAPES=tuple(sorted(rotations(row['voxels'])));data=original.build();build=time.perf_counter()-begin
 print(id,'built',data['stats'],flush=True)
 clauses=data['clauses'];cnf=('p cnf %d %d\n'%(data['stats']['variables'],len(clauses))+''.join(' '.join(map(str,c))+' 0\n' for c in clauses)).encode();digest=hashlib.sha256(cnf).hexdigest()
 with Glucose3(bootstrap_with=clauses) as solver:
  start=time.perf_counter();timer=threading.Timer(args.seconds,solver.interrupt);timer.start()
  try:answer=solver.solve_limited(expect_interrupt=True)
  finally:timer.cancel();timer.join()
  result={'id':id,'k':2,'engine':'Original nonacube two-corona encoder, with only SHAPES replaced','motifSuppliedToSearch':False,'budgetSeconds':args.seconds,'status':'SAT' if answer is True else 'UNSAT' if answer is False else 'unknown','buildSeconds':build,'searchSeconds':time.perf_counter()-start,'stats':solver.accum_stats(),'problem':data['stats'],'formulaSHA256':digest}
  if answer:
   positives=set(solver.get_model());chosen=[s for i,s in enumerate(data['universe'],1) if i in positives]
   first=[s for s in chosen if s in data['first']];needed=original.halo(data['root'].union(*(original.cells(s) for s in first)));chosen=[s for s in chosen if original.cells(s)&needed];result['witness']=original.verify(data,chosen)
 (OUT/(id+'-blind.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='witness'}),flush=True)
 if answer is False:raise RuntimeError('Known periodic positive control rejected')
