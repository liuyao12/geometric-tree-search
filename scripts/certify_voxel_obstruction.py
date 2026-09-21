#!/usr/bin/env python3
"""Independent voxel CNF + Glucose proof, checked with a separate RUP checker.

Pair mode requires its core and any requested viable-frontier predicates.
Window mode requires the supplied finite target and explicit pair exclusions.
No learned m-values are read. The geometric-to-CNF reduction remains an audited
part of the argument; the trace certifies the emitted finite CNF is UNSAT.
"""
import argparse, hashlib, json, time
from collections import defaultdict
from itertools import product, combinations
from pathlib import Path
from lib.check_rup import RUPChecker

class Formula:
    def __init__(self): self.clauses=[]; self.variables=0
    def new(self): self.variables+=1; return self.variables
    def any(self, literals):
        literals=list(dict.fromkeys(literals)); v=self.new()
        self.clauses.append([-v]+literals)
        self.clauses.extend([v,-x] for x in literals)
        return v
    def all(self, literals): return -self.any([-x for x in literals])

def construct(data, frontier_points=None):
    model=data['model']
    if model['capacity'] != 8 or model['placementDomain'] != {'kind':'scaled_cubic','translationStep':2}: raise ValueError('Wrong voxel domain')
    orientations=[list(map(tuple,o['voxels'])) for o in model['orientations']]
    for cells in orientations:
        if not cells or len(set(cells)) != len(cells) or any(len(v)!=3 or any(type(x) is not int for x in v) for v in cells): raise ValueError('Invalid voxels')
    pair=data.get('pair'); fixed=pair if pair is not None else data.get('fixed',[])
    def spec(p):
        t=p['translation'];oi=p['oi']
        if type(oi) is not int or not 0<=oi<len(orientations) or len(t)!=3 or any(type(x) is not int or x%2 for x in t): raise ValueError('Invalid placement')
        return oi,tuple(x//2 for x in t)
    seeds=[spec(p) for p in fixed]
    if len(set(seeds))!=len(seeds) or pair is not None and len(pair)!=2: raise ValueError('Invalid seed collection')
    def cells(s): return [tuple(v[i]+s[1][i] for i in range(3)) for v in orientations[s[0]]]
    if pair is not None:
        # All corners of every seed voxel must be full: precisely the union
        # of their Chebyshev-distance-one voxel neighborhoods.
        target={tuple(v[i]+d[i] for i in range(3)) for seed in seeds for v in cells(seed) for d in product([-1,0,1],repeat=3)}
    else:
        target=set()
        for p in model['required']:
            q=p['pos']
            if len(q)!=3 or any(type(x) is not int for x in q): raise ValueError('Invalid target')
            if all(x%2 for x in q): target.add(tuple((x-1)//2 for x in q))
            elif all(x%2==0 for x in q): target.update(tuple(q[i]//2+d[i] for i in range(3)) for d in product([-1,0],repeat=3))
            else: raise ValueError('Target must be a center or corner')
    if not target: raise ValueError('Empty target')
    candidates=set(seeds)
    for q in target:
        for oi,o in enumerate(orientations):
            for anchor in o: candidates.add((oi,tuple(q[i]-anchor[i] for i in range(3))))
    f=Formula();variables={s:f.new() for s in sorted(candidates)};by_voxel=defaultdict(list)
    for s,v in variables.items():
        for q in cells(s): by_voxel[q].append(v)
    for q,vs in by_voxel.items():
        f.clauses.extend([-a,-b] for a,b in combinations(vs,2))
        if q in target: f.clauses.append(vs)
    for q in target:
        if q not in by_voxel: f.clauses.append([])
    for s in seeds: f.clauses.append([variables[s]])
    exclusions=set()
    for pair_template in data.get('pairExclusions',[]):
        if len(pair_template)!=2: raise ValueError('Invalid pair template')
        a,b=map(spec,pair_template);delta=tuple(b[1][i]-a[1][i] for i in range(3))
        for (oi,t),v in variables.items():
            other=(b[0],tuple(t[i]+delta[i] for i in range(3)))
            if oi==a[0] and other in variables: exclusions.add(tuple(sorted((v,variables[other]))))
    f.clauses.extend([-a,-b] for a,b in sorted(exclusions))
    occupied={};available={}
    def occ(q):
        if q not in occupied: occupied[q]=f.any(by_voxel.get(q,[]))
        return occupied[q]
    def avail(s):
        if s not in available: available[s]=f.all([-occ(q) for q in cells(s)])
        return available[s]
    for q in frontier_points or []:
        if len(q)!=3 or any(type(x) is not int or x%2 for x in q): raise ValueError('Invalid corner')
        adjacent=[tuple(q[i]//2+d[i] for i in range(3)) for d in product([-1,0],repeat=3)]
        incident={(oi,tuple(p[i]-v[i] for i in range(3))) for p in adjacent for oi,o in enumerate(orientations) for v in o}
        choices=[avail(s) for s in sorted(incident)]
        neighbors=[occ(p) for p in adjacent]
        f.clauses.append([-f.any(neighbors),f.all(neighbors)]+choices)
    return f,variables,{'candidates':len(variables),'targetVoxels':len(target),'pairExclusionEdges':len(exclusions),'frontierPoints':len(frontier_points or [])}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);parser.add_argument('--frontier-result');parser.add_argument('--output',required=True)
    from pysat.solvers import Glucose3
    a=parser.parse_args();raw=Path(a.input).read_bytes();data=json.loads(raw)
    prior=json.loads(Path(a.frontier_result).read_text()) if a.frontier_result else None
    if prior:
        expected=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if prior.get('problemSha256')!=expected: raise ValueError('Frontier receipt belongs to another problem')
    started=time.perf_counter();f,variables,stats=construct(data,prior.get('frontierPoints') if prior else None)
    with Glucose3(bootstrap_with=f.clauses,with_proof=True) as solver:
        sat=solver.solve();proof=solver.get_proof() if not sat else []
        assignment=solver.get_model() if sat else []
    stats.update(variables=f.variables,clauses=len(f.clauses),solveMs=(time.perf_counter()-started)*1000)
    dimacs=f'p cnf {f.variables} {len(f.clauses)}\n'+''.join(' '.join(map(str,c))+' 0\n' for c in f.clauses)
    trace='\n'.join(proof)+'\n';out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.with_suffix('.cnf').write_text(dimacs);out.with_suffix('.drup').write_text(trace)
    checked=RUPChecker(f.clauses).verify(proof) if not sat else None
    result={'status':'SAT' if sat else 'UNSAT','stats':stats,'proofCheck':checked,'inputSha256':hashlib.sha256(raw).hexdigest(),'cnfSha256':hashlib.sha256(dimacs.encode()).hexdigest(),'proofSha256':hashlib.sha256(trace.encode()).hexdigest(),'totalMs':(time.perf_counter()-started)*1000}
    if sat: result['placements']=[{'oi':oi,'translation':[2*x for x in t]} for (oi,t),v in variables.items() if v in set(assignment)]
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='placements'}),flush=True)
if __name__=='__main__': main()
