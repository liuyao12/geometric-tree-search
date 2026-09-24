#!/usr/bin/env python3
"""Audit each learned anchor rule against all geometric covers; stress exact counter rollback."""
import argparse,importlib.util,json,pathlib,random
HERE=pathlib.Path(__file__).parent;spec=importlib.util.spec_from_file_location('graph',HERE/'graph.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
parser=argparse.ArgumentParser();parser.add_argument('--folder',default='data/heesch-catalog/benchmarks');parser.add_argument('--output',default='data/heesch-catalog/marking-verification.json');args=parser.parse_args()
rows={r['id']:r for r in json.load(open('data/heesch-catalog/catalog.json'))['systems']};out=[];rng=random.Random(924)
for path in sorted(pathlib.Path(args.folder).glob('*-affine-GCTS.json')):
 run=json.loads(path.read_text());data=g.c.build(rows[run['id']]['voxels'],run['k']);s=g.Search(data,True,60,run['k']);total=0
 for rule in run['rules']:
  ids=rule['roles'];assert len(ids)==len(set(ids));q=tuple(rule['requiredPoint']);assert q in data['target'];patch=[data['cells'](data['universe'][v]) for v in ids];occupied=set(data['root'])
  for cells in patch:assert not cells&occupied;occupied.update(cells)
  # Enumerate cover placements directly from every oriented voxel alignment.
  covers=set()
  for oi,o in enumerate(data['shapes']):
   for cell in o:
    t=tuple(q[a]-cell[a] for a in range(3));cover=frozenset(tuple(v[a]+t[a] for a in range(3)) for v in o)
    if not cover&data['root']:covers.add(cover)
  def required_without(absent=None):return q in data['near'] or any(q in data['requirements'].get(data['universe'][v],[]) for i,v in enumerate(ids) if i!=absent)
  assert required_without() and all(any(cover&p for p in patch) for cover in covers)
  assert all(not required_without(absent) or any(not any(cover&p for i,p in enumerate(patch) if i!=absent) for cover in covers) for absent in range(len(patch)))
  for i,(v,atom) in enumerate(zip(ids,rule['atoms'])):
   oi,t=data['universe'][v];assert atom=={'orientation':oi,'offset':[-x for x in t],'role':i}
  total+=1
  r={'mask':sum(1<<v for v in ids),'state':-1,'roles':ids};s.rules.append(r)
  for v in ids:s.inc[v].append(r)
  s.update(r)
 # This audit recomputes all channels from scratch; the search uses incidences.
 def check():
  expected=[0]*s.N;conflicts=0
  for r in s.rules:
   missing=[v for v in r['roles'] if not s.chosen&(1<<v)]
   if not missing:conflicts+=1
   elif len(missing)==1:expected[missing[0]]+=1
  assert expected==s.block and conflicts==s.conflicts;assert s.blocked==sum(1<<i for i,n in enumerate(expected) if n)
 check()
 for _ in range(100):
  chosen=rng.sample(range(s.N),min(15,s.N))
  for v in chosen:s.push(v)
  check()
  for v in reversed(chosen):s.pop(v)
  check()
 out.append({'id':run['id'],'rulesVerified':total,'everyRuleMinimalForItsCertifiedRequiredPoint':True,'anchorInverseMapVerified':True,'rollbackTrials':100});print(json.dumps(out[-1]),flush=True)
pathlib.Path(args.output).write_text(json.dumps(out,indent=2)+'\n')
