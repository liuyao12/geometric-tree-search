#!/usr/bin/env python3
"""Exact two-corona reduction with placement variables only (no auxiliary variables)."""
import argparse,importlib.util,itertools,json,pathlib,time
spec=importlib.util.spec_from_file_location('geometry',pathlib.Path(__file__).resolve().parents[1]/'search-nonacube-two-corona.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
NONACUBE_SHAPES=n.SHAPES
def build(shape='nonacube'):
 n.SHAPES=(((0,0,0),),) if shape=='cube' else NONACUBE_SHAPES
 root=n.cells((0,(0,0,0)));near=n.halo(root)-root;first=n.candidates(near,root)
 requirements={s:n.halo(n.cells(s))-root-n.cells(s) for s in first};target=set(near).union(*requirements.values());universe=sorted(n.candidates(target,root));ids={s:i+1 for i,s in enumerate(universe)};by={}
 for s,v in ids.items():
  for q in n.cells(s):by.setdefault(q,[]).append(v)
 pairs=set()
 for vs in by.values():pairs.update(itertools.combinations(vs,2))
 clauses=[[-a,-b] for a,b in sorted(pairs)]
 clauses += [by[q] for q in sorted(near)]
 for s in sorted(first):
  for q in sorted(requirements[s]):clauses.append([-ids[s]]+by[q])
 return {'root':root,'first':first,'universe':universe,'clauses':clauses,'stats':{'firstCandidates':len(first),'variables':len(universe),'clauses':len(clauses),'overlapPairs':len(pairs),'rootRequiredCells':len(near),'auxiliaryVariables':0}}
def write(data,prefix):
 stem=pathlib.Path(prefix);stem.parent.mkdir(parents=True,exist_ok=True)
 stem.with_suffix('.cnf').write_text('p cnf %d %d\n'%(len(data['universe']),len(data['clauses']))+''.join(' '.join(map(str,c))+' 0\n' for c in data['clauses']))
 stem.with_suffix('.placements.txt').write_text(''.join('%d %d %d %d\n'%((s[0],)+s[1]) for s in data['universe']))
 stem.with_suffix('.json').write_text(json.dumps(data['stats'],indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prefix',required=True);p.add_argument('--shape',choices=['nonacube','cube'],default='nonacube');a=p.parse_args();started=time.monotonic();data=build(a.shape);write(data,a.prefix);print(json.dumps({**data['stats'],'seconds':time.monotonic()-started}))
