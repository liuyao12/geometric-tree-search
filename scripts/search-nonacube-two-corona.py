#!/usr/bin/env python3
"""Exact unmarked two-corona SAT search, allowing the first corona to vary.

Specialized SAT scheduling, separate from GCTS growth. Every selected tile that
meets the root must be completely surrounded. Outer tiles need not admit further
extension. No infinite-tiling exclusions or learned markings are used.
"""
import argparse,json,pickle,time
from collections import defaultdict
from itertools import product
from pathlib import Path
from threading import Timer
from pysat.card import CardEnc,EncType
from pysat.solvers import Glucose3,Cadical195,Minisat22

OFFSETS=tuple(product((-1,0,1),repeat=3))
SHAPES=tuple(tuple([(0,0,0)]+[tuple(d if k==a else 0 for k in range(3)) for a in axes for d in (-2,-1,1,2)]) for axes in ((0,1),(0,2),(1,2)))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def cells(s):return frozenset(add(v,s[1]) for v in SHAPES[s[0]])
def halo(vs):return {add(v,d) for v in vs for d in OFFSETS}
def candidates(target,root):
    found=set()
    for q in sorted(target):
        for oi,o in enumerate(SHAPES):
            for v in o:
                s=(oi,tuple(q[k]-v[k] for k in range(3)))
                if s not in found and not cells(s)&root:found.add(s)
    return found

def build():
    begun=time.perf_counter();root=cells((0,(0,0,0)));near=halo(root)-root
    first=candidates(near,root)
    requirements={s:halo(cells(s))-root-cells(s) for s in first}
    possible_target=set(near).union(*requirements.values())
    universe=sorted(candidates(possible_target,root));variables={s:i+1 for i,s in enumerate(universe)}
    by_voxel=defaultdict(list)
    for s,v in variables.items():
        for q in sorted(cells(s)):by_voxel[q].append(v)
    clauses=[];top=len(universe)
    for q in sorted(by_voxel):
        vs=by_voxel[q]
        if len(vs)>1:
            enc=CardEnc.atmost(vs,1,top_id=top,encoding=EncType.seqcounter);clauses.extend(enc.clauses);top=enc.nv
    for q in sorted(near):clauses.append(by_voxel[q])
    for s in sorted(first):
        for q in sorted(requirements[s]):clauses.append([-variables[s]]+by_voxel[q])
    stats={'firstCandidates':len(first),'totalCandidates':len(universe),'variables':top,'clauses':len(clauses),'preparationMs':(time.perf_counter()-begun)*1000}
    return {'root':root,'first':first,'universe':universe,'clauses':clauses,'stats':stats}

def verify(data,chosen):
    root=data['root'];occupied=set(root);first=[];outer=[]
    near=halo(root)-root
    for s in chosen:
        vs=cells(s)
        if vs&occupied:raise AssertionError('Overlap')
        occupied.update(vs)
        (first if vs&near else outer).append(s)
    if not halo(root)<=occupied:raise AssertionError('Incomplete first corona')
    inner=root.union(*(cells(s) for s in first))
    if not halo(inner)<=occupied:raise AssertionError('Incomplete second corona')
    boundary=halo(inner)-inner
    if any(not cells(s)&boundary for s in outer):raise AssertionError('Disconnected outer tile')
    return {'root':sorted(root),'corona1':[sorted(cells(s)) for s in first],'corona2':[sorted(cells(s)) for s in outer],
            'verified':True,'scope':'Integer translations, all three cubic orientations; full face/edge/vertex surrounds in both layers.'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cache',required=True);ap.add_argument('--output');ap.add_argument('--solver',choices=['glucose3','cadical195','minisat22'],default='cadical195');ap.add_argument('--seconds',type=float,default=300);ap.add_argument('--build-only',action='store_true');ap.add_argument('--proof-prefix');a=ap.parse_args()
    p=Path(a.cache)
    if p.exists():data=pickle.loads(p.read_bytes())
    else:data=build();p.write_bytes(pickle.dumps(data))
    print(json.dumps(data['stats']),flush=True)
    if a.build_only:return
    if not a.output:ap.error('--output is required')
    start=time.perf_counter();last=start;answer=None
    solver_class={'glucose3':Glucose3,'cadical195':Cadical195,'minisat22':Minisat22}[a.solver]
    if a.proof_prefix and a.solver!='glucose3':ap.error('Proof export currently requires glucose3')
    solver_options={'with_proof':True} if a.proof_prefix else {}
    with solver_class(bootstrap_with=data['clauses'],**solver_options) as solver:
        while time.perf_counter()-start<a.seconds:
            if a.solver=='cadical195':
                solver.conf_budget(2000);answer=solver.solve_limited()
            else:
                timer=Timer(min(10,a.seconds-(time.perf_counter()-start)),solver.interrupt);timer.daemon=True;timer.start()
                try:answer=solver.solve_limited(expect_interrupt=True)
                finally:timer.cancel();timer.join();solver.clear_interrupt()
            if answer is not None:break
            if time.perf_counter()-last>=10:
                print(json.dumps({'status':'running','solver':a.solver,'seconds':time.perf_counter()-start,'stats':solver.accum_stats()}),flush=True);last=time.perf_counter()
        result={'status':'SAT' if answer is True else 'UNSAT' if answer is False else 'unknown','solver':a.solver,'seconds':time.perf_counter()-start,'stats':solver.accum_stats(),'problem':data['stats']}
        if answer is False and a.proof_prefix:
            stem=Path(a.proof_prefix);cnf=f"p cnf {data['stats']['variables']} {len(data['clauses'])}\n"+''.join(' '.join(map(str,c))+' 0\n' for c in data['clauses']);stem.with_suffix('.cnf').write_text(cnf);stem.with_suffix('.drup').write_text('\n'.join(solver.get_proof())+'\n');result['proofPrefix']=str(stem)
        if answer is True:
            positive={v for v in solver.get_model() if v>0};chosen=[s for i,s in enumerate(data['universe'],1) if i in positive]
            # Drop irrelevant outer placements; all first-layer obligations stay.
            first=[s for s in chosen if s in data['first']];needed=halo(data['root'].union(*(cells(s) for s in first)))
            chosen=[s for s in chosen if cells(s)&needed]
            result['certificate']=verify(data,chosen)
        Path(a.output).write_text(json.dumps(result));print(json.dumps({k:v for k,v in result.items() if k!='certificate'}),flush=True)
if __name__=='__main__':main()
