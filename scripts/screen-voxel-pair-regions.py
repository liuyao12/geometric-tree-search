#!/usr/bin/env python3
"""Fresh finite-region pair tests, with independently checked negative proofs.

All integer placements covering a required voxel are considered. Placements may
extend outside the target; their full occupancy still participates in conflicts.
SAT means only this finite target is fillable. Timeout means unknown. Exclusions
require an UNSAT proof accepted by DRAT-trim. This is a specialized SAT control,
not the GCTS reference scheduler. No previously learned exclusions are used.
"""
import argparse
import gzip
import hashlib
import json
import subprocess
import time
from itertools import product
from pathlib import Path
from threading import Timer
from pysat.solvers import Glucose3
from certify_voxel_obstruction import construct


def region_problem(model, pair, radius):
    occupied = {tuple(v[i]+p['translation'][i]//2 for i in range(3))
                for p in pair for v in model['orientations'][p['oi']]['voxels']}
    target = sorted({tuple(v[i]+d[i] for i in range(3)) for v in occupied
                     for d in product(range(-radius,radius+1), repeat=3)})
    return {'model':{**model, 'required':[{'pos':[2*x+1 for x in q]} for q in target]}, 'fixed':pair}


def check_positive(data, placements):
    occupied = set()
    for p in placements:
        for v in data['model']['orientations'][p['oi']]['voxels']:
            q = tuple(v[i]+p['translation'][i]//2 for i in range(3))
            if q in occupied: raise AssertionError('SAT witness overlaps')
            occupied.add(q)
    target = {tuple((x-1)//2 for x in p['pos']) for p in data['model']['required']}
    if not target <= occupied: raise AssertionError('SAT witness misses target')
    if not all(p in placements for p in data['fixed']): raise AssertionError('SAT witness misses fixed pair')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True, help='Directory for summary and checked proof files')
    ap.add_argument('--radius', type=int, default=2)
    ap.add_argument('--seconds', type=float, default=5)
    ap.add_argument('--drat-trim', required=True)
    ap.add_argument('--ids', help='Optional comma-separated orbit IDs; default tests every orbit')
    a = ap.parse_args()
    if a.radius < 1 or a.seconds <= 0: ap.error('Positive radius and time budget required')
    source = json.loads(Path(a.input).read_text())
    if any(o.get('marks') for o in source['model']['orientations']): raise ValueError('Expected unmarked input')
    selected = set(map(int,a.ids.split(','))) if a.ids else None
    folder = Path(a.output); folder.mkdir(parents=True, exist_ok=True)
    (folder/'input.json').write_text(json.dumps(source))
    summary = {'version':1, 'tile':source['tile'], 'radius':a.radius, 'secondsPerPair':a.seconds,
               'rawPairs':source['rawPairs'], 'totalOrbits':len(source['rows']), 'rows':[],
               'scope':'Fresh unmarked finite region; SAT is a finite witness, UNSAT requires checked proof, limits are unknown.'}
    begun = time.perf_counter()
    for row in source['rows']:
        if selected is not None and row['id'] not in selected: continue
        started = time.perf_counter()
        data = region_problem(source['model'],row['pair'],a.radius)
        formula, variables, stats = construct(data,amo='sequential')
        result = {**row, 'status':'unknown', 'stats':stats}
        with Glucose3(bootstrap_with=formula.clauses,with_proof=True) as solver:
            timer=Timer(a.seconds,solver.interrupt); timer.daemon=True; timer.start()
            try: answer=solver.solve_limited(expect_interrupt=True)
            finally: timer.cancel();timer.join()
            result['solveMs']=(time.perf_counter()-started)*1000
            if answer is True:
                assignment=set(solver.get_model())
                placements=[{'oi':oi,'translation':[2*x for x in t]} for (oi,t),v in variables.items() if v in assignment]
                check_positive(data,placements)
                result.update(status='finite_fillable',placements=placements)
            elif answer is False:
                proof='\n'.join(solver.get_proof())+'\n'
                cnf=f'p cnf {formula.variables} {len(formula.clauses)}\n'+''.join(' '.join(map(str,c))+' 0\n' for c in formula.clauses)
                stem=folder/f"pair-{row['id']}"
                cp,pp=stem.with_suffix('.cnf'),stem.with_suffix('.drup')
                cp.write_text(cnf);pp.write_text(proof)
                check_start=time.perf_counter()
                try:
                    replay=subprocess.run([a.drat_trim,str(cp),str(pp),'-t','60'],text=True,capture_output=True,timeout=65)
                    if replay.returncode==0 and 's VERIFIED' in replay.stdout:
                        result.update(status='excluded',proof={'checker':'DRAT-trim','verified':True,'cnfSha256':hashlib.sha256(cnf.encode()).hexdigest(),'proofSha256':hashlib.sha256(proof.encode()).hexdigest(),'prefix':stem.name})
                    else: result['reason']='Independent proof check failed or exceeded budget'
                except subprocess.TimeoutExpired: result['reason']='Independent proof check timed out'
                result['verificationMs']=(time.perf_counter()-check_start)*1000
                for p in [cp,pp]:
                    p.with_suffix(p.suffix+'.gz').write_bytes(gzip.compress(p.read_bytes(),mtime=0));p.unlink()
            else: result['reason']='Solver time budget'
        result['totalMs']=(time.perf_counter()-started)*1000
        summary['rows'].append(result);summary['totalMs']=(time.perf_counter()-begun)*1000
        (folder/'summary.json').write_text(json.dumps(summary))
        print(json.dumps({k:v for k,v in result.items() if k not in ['placements','pair','key']}),flush=True)

if __name__=='__main__': main()
