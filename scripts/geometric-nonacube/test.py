#!/usr/bin/env python3
"""Check counter propagation/rollback against brute force and a geometric positive control."""
import argparse,importlib.util,itertools,json,pathlib,random,subprocess,tempfile
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('build',HERE/'build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--solver',required=True);a=p.parse_args()
rng=random.Random(230924);totals={'cases':0,'learnedPatterns':0,'geometricUnits':0,'geometricConflicts':0}
with tempfile.TemporaryDirectory() as tmp:
 stem=pathlib.Path(tmp)/'test'
 def run(clauses,n):
  stem.with_suffix('.cnf').write_text('p cnf %d %d\n'%(n,len(clauses))+''.join(' '.join(map(str,c))+' 0\n' for c in clauses))
  stem.with_suffix('.placements.txt').write_text(''.join('0 %d 0 0\n'%i for i in range(n)))
  result=subprocess.run([a.solver,str(stem.with_suffix('.cnf')),str(stem.with_suffix('.drup')),'-','10','geometry',str(stem.with_suffix('.placements.txt'))],capture_output=True,text=True,check=True)
  return json.loads(result.stdout)
 def valid(selected,clauses):return all(any((abs(v) in selected)==(v>0) for v in c) for c in clauses)
 for k in range(60):
  n=8;clauses=[[v*rng.choice([-1,1]) for v in rng.sample(range(1,n+1),3)] for _ in range(rng.randrange(22,46))]
  truth=any(valid({i+1 for i in range(n) if mask&(1<<i)},clauses) for mask in range(1<<n));r=run(clauses,n)
  assert r['status']==('SAT' if truth else 'UNSAT'),(clauses,r)
  if truth:assert valid(set(r['selected']),clauses)
  totals['cases']+=1
  for key in ['learnedPatterns','geometricUnits','geometricConflicts']:totals[key]+=r[key]
 assert totals['learnedPatterns']>0 and totals['geometricUnits']>0
 data=b.build('cube');b.write(data,stem)
 result=subprocess.run([a.solver,str(stem.with_suffix('.cnf')),str(stem.with_suffix('.drup')),'-','10','geometry',str(stem.with_suffix('.placements.txt'))],capture_output=True,text=True,check=True);r=json.loads(result.stdout);assert r['status']=='SAT';assert valid(set(r['selected']),data['clauses'])
 selected=[data['universe'][v-1] for v in r['selected']];occupied=set(data['root'])
 for s in selected:
  cells=b.n.cells(s);assert not occupied&cells;occupied.update(cells)
 assert b.n.halo(data['root'])<=occupied
 for s in selected:
  if s in data['first']:assert b.n.halo(b.n.cells(s))<=occupied
 totals.update(cubeStatus=r['status'],cubeSelected=len(selected),cubeHalosCovered=True)
print(json.dumps(totals,indent=2))
