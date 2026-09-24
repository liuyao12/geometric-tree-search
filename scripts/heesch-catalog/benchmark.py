#!/usr/bin/env python3
"""Three sequential cold runs of each engine on identical fixed-corona targets."""
import argparse,importlib.util,json,pathlib,time,statistics,platform
from pysat.solvers import Glucose3
HERE=pathlib.Path(__file__).parent;spec=importlib.util.spec_from_file_location('graph',HERE/'graph.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
parser=argparse.ArgumentParser();parser.add_argument('--ids',default='3_cross,t_cross,large_buckled_ring,polycube_p10_052670');parser.add_argument('--lanes',default='unmarked-graph,affine-GCTS,Glucose3');parser.add_argument('--k',type=int,choices=[1,2],default=1);parser.add_argument('--out',default='data/heesch-catalog/benchmarks');args=parser.parse_args()
rows=json.load(open('data/heesch-catalog/catalog.json'))['systems'];out=pathlib.Path(args.out);out.mkdir(exist_ok=True);summary=[]
for row in rows:
 if row['id'] not in args.ids.split(','):continue
 for lane in args.lanes.split(','):
  runs=[]
  for repeat in range(3):
   start=time.perf_counter();data=g.c.build(row['voxels'],args.k);build=time.perf_counter()-start
   if lane=='Glucose3':
    init=time.perf_counter();solver=Glucose3(bootstrap_with=data['clauses'],with_proof=False);setup=time.perf_counter()-init;begin=time.perf_counter();answer=solver.solve();r={'status':'SAT' if answer else 'UNSAT','seconds':time.perf_counter()-begin,'stats':solver.accum_stats()};solver.delete()
   else:
    init=time.perf_counter();s=g.Search(data,lane=='affine-GCTS',180,args.k);setup=time.perf_counter()-init;r=s.run()
   assert r['status']=='UNSAT';r.update(id=row['id'],k=args.k,lane=lane,repeat=repeat,formulaBuildSeconds=build,engineSetupSeconds=setup,totalSeconds=build+setup+r['seconds']);runs.append({key:v for key,v in r.items() if key not in ['rules','witness']})
   if repeat==0:(out/(row['id']+'-'+lane+'.json')).write_text(json.dumps(r))
  entry={'id':row['id'],'lane':lane,'runs':runs,'medianSearchSeconds':statistics.median(r['seconds'] for r in runs),'medianTotalSeconds':statistics.median(r['totalSeconds'] for r in runs)};summary.append(entry);print(json.dumps(entry),flush=True)
if (out/'summary.json').exists():
 old=json.loads((out/'summary.json').read_text());keys={(r['id'],r['lane']) for r in summary};summary=[r for r in old['results'] if (r['id'],r['lane']) not in keys]+summary
(out/'summary.json').write_text(json.dumps({'python':platform.python_version(),'host':platform.machine(),'repetitions':3,'sequential':True,'proofRecordingInTimedRuns':False,'results':summary},indent=2)+'\n')
