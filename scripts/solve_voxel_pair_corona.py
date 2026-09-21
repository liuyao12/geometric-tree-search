#!/usr/bin/env python3
"""Incremental Glucose research oracle for a viable unmarked voxel pair corona.

Exact finite seed-support reduction, full voxel overlap, all exposed corners.
Separate SAT scheduling; no learned markings or reference-lane speedup claim.
"""
import argparse,hashlib,json,time
from collections import Counter
from itertools import product
from pathlib import Path
from threading import Timer
from pysat import __version__ as pysat_version
from pysat.solvers import Glucose3
from certify_voxel_obstruction import construct
from solve_point_pair_corona import voxel_core_domain

class Limit(Exception):pass

def solve(data,time_ms=10000,max_rounds=1000,frontier_batch=4,resume_points=None):
    if type(time_ms) is not int or time_ms<1 or type(frontier_batch) is not int or frontier_batch<1 or type(max_rounds) is not int or max_rounds<0:raise ValueError('Invalid budget')
    started=time.perf_counter();deadline=started+time_ms/1000
    def budget():
        if time.perf_counter()>=deadline:raise Limit('time budget')
    m=data['model'];pair=data['pair']
    if data.get('pairExclusions') or data.get('fixed') or any(o.get('marks') for o in m['orientations']):raise ValueError('Oracle requires an unmarked pair problem')
    for o in m['orientations']:
        if len({tuple(c['pos']) for c in o['cells']})!=len(o['cells']) or any(type(c['weight']) is not int for c in o['cells']):raise ValueError('Invalid point weights')
    core={tuple(c['pos'][i]+p['translation'][i] for i in range(3)) for p in pair for c in m['orientations'][p['oi']]['cells']}
    voxel_core_domain(m,core)
    orientations=[list(map(tuple,o['voxels'])) for o in m['orientations']]
    corner_offsets=list(product([0,1],repeat=3))
    def cells(spec):return [tuple(v[i]+spec[1][i] for i in range(3)) for v in orientations[spec[0]]]
    incident_offsets=[]
    for o in orientations:incident_offsets.append(sorted({tuple(v[i]+d[i] for i in range(3)) for v in o for d in corner_offsets}))
    result={'status':'unresolved','reason':None,'placements':pair,'nogoods':[]}
    stats={'backend':'glucose3-incremental','solverVersion':'python-sat '+pysat_version,'encoding':'voxel-cover','frontier':'occupancy','frontierBatch':frontier_batch,'scope':'Exact finite seed-support corona with viable frontier; nonreference SAT scheduling'}
    f=None;rounds=0;cache={}
    try:
        budget();f,variables,initial=construct(data,resume_points,budget);stats.update(initial)
        by_variable={v:cells(s) for s,v in variables.items()}
        universe=sorted({q for vs in by_variable.values() for q in vs});indices={q:i for i,q in enumerate(universe)}
        masks={v:sum(1<<indices[q] for q in qs) for v,qs in by_variable.items()}
        def available_masks(q):
            if q not in cache:
                options=[]
                for oi,offsets in enumerate(incident_offsets):
                    for offset in offsets:
                        t=tuple(q[i]-offset[i] for i in range(3));mask=0
                        for v in orientations[oi]:
                            index=indices.get(tuple(v[i]+t[i] for i in range(3)))
                            if index is not None:mask|=1<<index
                        options.append(mask)
                cache[q]=list(set(options))
            return cache[q]
        stats['preparationMs']=(time.perf_counter()-started)*1000
        budget()
        with Glucose3(bootstrap_with=f.clauses) as solver:
            loaded=len(f.clauses)
            for _ in range(max_rounds):
                budget()
                if len(f.clauses)>loaded:solver.append_formula(f.clauses[loaded:]);loaded=len(f.clauses)
                timer=Timer(max(.001,deadline-time.perf_counter()),solver.interrupt);timer.daemon=True;timer.start()
                try:answer=solver.solve_limited(expect_interrupt=True)
                finally:timer.cancel();timer.join();solver.clear_interrupt()
                rounds+=1
                if answer is False:result.update(status='invalid',reason='complete finite voxel formula exhausted');break
                if answer is not True:raise Limit('solver: timeout')
                budget();assignment=set(solver.get_model());selected=[(s,v) for s,v in variables.items() if v in assignment]
                occupied=0;counts=Counter();placed=[]
                for (oi,t),v in selected:
                    if occupied&masks[v]:raise AssertionError('SAT witness overlaps')
                    occupied|=masks[v];placed.append({'oi':oi,'translation':[2*x for x in t]})
                    for q in by_variable[v]:
                        for d in corner_offsets:counts[tuple(q[i]+d[i] for i in range(3))]+=1
                # Candidates beyond this finite universe are allowed as frontier
                # witnesses. Their masks omit cells no selected tile could occupy.
                dead=[]
                for q,n in sorted(counts.items()):
                    budget()
                    if n==8:continue
                    if n>8:raise AssertionError('Corner capacity exceeded')
                    if not any(mask&occupied==0 for mask in available_masks(q)):
                        dead.append(tuple(2*x for x in q))
                        if len(dead)>=frontier_batch:break
                result['placements']=placed
                if not dead:result.update(status='valid',verification={'coreComplete':True,'frontierViable':True});break
                for q in dead:
                    if q in f.constrained:raise AssertionError('Encoded corner remains dead')
                    f.constrain_frontier(q)
                    result['nogoods'].append({'deadPoint':list(q),'placements':placed})
            else:raise Limit('frontier refinement budget')
    except Limit as e:result.update(status='unresolved',reason=str(e))
    stats.update(rounds=rounds,elapsedMs=(time.perf_counter()-started)*1000,frontierConstraints=len(f.constrained) if f else 0,variables=f.variables if f else 0,clauses=len(f.clauses) if f else 0,cachedFrontierPoints=len(cache))
    return {**result,'stats':stats,'frontierPoints':sorted(f.constrained) if f else sorted(set(map(tuple,resume_points or [])))}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--time-ms',type=int,default=10000);p.add_argument('--max-rounds',type=int,default=1000);p.add_argument('--frontier-batch',type=int,default=4);p.add_argument('--resume');a=p.parse_args()
    data=json.loads(Path(a.input).read_text());sha=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest();prior=json.loads(Path(a.resume).read_text()) if a.resume else None
    if prior and (prior.get('problemSha256')!=sha or prior.get('stats',{}).get('frontier')!='occupancy'):p.error('Resume belongs to another problem')
    result=solve(data,a.time_ms,a.max_rounds,a.frontier_batch,prior.get('frontierPoints') if prior else None);result['problemSha256']=sha
    result['stats']['cumulativeMs']=result['stats']['elapsedMs']+(prior['stats'].get('cumulativeMs',prior['stats']['elapsedMs']) if prior else 0)
    Path(a.output).write_text(json.dumps(result));print(json.dumps({k:v for k,v in result.items() if k not in ('placements','frontierPoints','nogoods')}),flush=True)
