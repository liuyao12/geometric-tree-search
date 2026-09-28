#!/usr/bin/env python3
"""Look for a full first corona across the bend census; save exact witnesses.

Two independent solver orders may share --out. A verified SAT witness stops
both passes at the next per-shape boundary. UNSAT runs without proofs are
screening results only and do not add certified upper bounds.
"""
import argparse,json,pathlib,time,threading
from pysat.solvers import Glucose3,Cadical195,Gluecard3,Minicard,Kissat404
import corona
from verify_bent_six_arm import rotations,normalized,star
ROOT=pathlib.Path(__file__).resolve().parents[2]
def check(row,witness):
 shapes=rotations(row['voxels']);root=frozenset(map(tuple,witness['root']));assert normalized(root) in shapes
 seen=set(root);boundary=star(root)
 for raw in witness['tiles']:
  tile=frozenset(map(tuple,raw));assert normalized(tile) in shapes and not seen&tile and tile&boundary
  seen.update(tile)
 assert boundary<=seen
 return {'verified':True,'method':'Independent quarter-turn congruence, voxel nonoverlap, and cube-vertex sectors','surroundingTiles':len(witness['tiles']),'totalTiles':1+len(witness['tiles']),'rootBoundaryVoxels':len(boundary-root),'coveredVoxels':len(seen),'eachTileTouchesRoot':True}
def main():
 p=argparse.ArgumentParser();p.add_argument('--solver',choices=['glucose','cadical','gluecard','minicard','kissat'],default='glucose');p.add_argument('--seconds',type=float,default=4);p.add_argument('--conflicts',type=int,default=200000);p.add_argument('--reverse',action='store_true');p.add_argument('--out',default='data/bent-six-arm/variants/first-coronas');p.add_argument('--ids');p.add_argument('--negative',action='store_true');p.add_argument('--incremental',action='store_true');args=p.parse_args();assert not args.incremental or args.solver in ['gluecard','minicard']
 out=ROOT/args.out;out.mkdir(parents=True,exist_ok=True);rows=json.loads((ROOT/'data/bent-six-arm/variants/catalog.json').read_text())['rows'];rows=[r for r in rows if r['id'] not in ['bend_018','bend_036'] and (not args.ids or r['id'] in args.ids.split(','))]
 if args.reverse:rows.reverse()
 results=[]
 for row in rows:
  if list(out.glob('*-witness.json')):break
  start=time.perf_counter();data=corona.build(row['voxels'],1);build=time.perf_counter()-start;cls={'glucose':Glucose3,'cadical':Cadical195,'gluecard':Gluecard3,'minicard':Minicard,'kissat':Kissat404}[args.solver];native=args.solver in ['gluecard','minicard']
  start=time.perf_counter()
  with cls(bootstrap_with=([] if args.incremental else [data['by'][q] for q in sorted(data['near'])]) if native else data['clauses']) as solver:
   if native:
    for q in sorted(data['by']):
     if len(data['by'][q])>1:solver.add_atmost(data['by'][q],1)
   setup=time.perf_counter()-start;start=time.perf_counter();answer=None
   if args.solver not in ['cadical','kissat']:
    solver.set_phases([(-i if args.negative else i) for i in range(1,len(data['universe'])+1)]);timer=threading.Timer(args.seconds,solver.interrupt);timer.start()
    try:
     if args.incremental:
      stages=[];required=set();ordered=sorted(data['near'],key=lambda q:(len(data['by'][q]),q))
      while time.perf_counter()-start<args.seconds:
       answer=solver.solve_limited(expect_interrupt=True)
       if answer is not True:break
       model=set(solver.get_model());missing=[q for q in ordered if not any(v in model for v in data['by'][q])]
       stages.append({'required':len(required),'uncovered':len(missing)})
       if not missing:break
       answer=None
       for q in missing[:8]:solver.add_clause(data['by'][q]);required.add(q)
     else:answer=solver.solve_limited(expect_interrupt=True)
    finally:timer.cancel();timer.join()
   elif args.solver=='kissat':
    solver.conf_budget(args.conflicts);answer=solver.solve_limited()
   else:
    while time.perf_counter()-start<args.seconds:
     solver.conf_budget(500);answer=solver.solve_limited()
     if answer is not None:break
   result={'id':row['id'],'solver':args.solver,'positivePlacementPhases':args.solver not in ['cadical','kissat'] and not args.negative,'encoding':'native-cardinality' if native else 'sequential-counter','incrementalCoverage':args.incremental,'budgetSeconds':None if args.solver=='kissat' else args.seconds,'conflictBudget':args.conflicts if args.solver=='kissat' else None,'buildSeconds':build,'setupSeconds':setup,'searchSeconds':time.perf_counter()-start,'placements':len(data['universe']),'status':'SAT' if answer is True else 'UNSAT-unchecked' if answer is False else 'unknown','stats':None if args.solver=='kissat' else solver.accum_stats()}
   if args.incremental:result['stages']=stages
   if answer:
    model=set(solver.get_model());w=corona.verify(data,[s for i,s in enumerate(data['universe'],1) if i in model],1);verification=check(row,w)
    result['verification']=verification
    witness={'id':row['id'],'scope':'Proper cubic rotations, integer translations, full touching first corona','lowerBound':1,'prototype':row['voxels'],**w,'independentVerification':verification}
    (out/(row['id']+'-'+args.solver+'-witness.json')).write_text(json.dumps(witness,indent=2)+'\n')
   results.append(result);(out/(args.solver+'-screen.json')).write_text(json.dumps({'solver':args.solver,'secondsPerShape':None if args.solver=='kissat' else args.seconds,'conflictsPerShape':args.conflicts if args.solver=='kissat' else None,'reverseOrder':args.reverse,'results':results,'stoppedAfterWitness':bool(answer)},indent=2)+'\n');print(json.dumps(result),flush=True)
  if answer:break
if __name__=='__main__':main()
