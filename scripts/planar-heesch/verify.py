#!/usr/bin/env python3
"""Replay witnesses, regenerate recorded formulas, audit tiny completeness."""
import collections,gzip,hashlib,itertools,json,pathlib,sys
from engine import Grid,build,enumerate_free,normalize,verify
root=pathlib.Path('data/planar-heesch');checks=[]
# Independent bounded rectangular translation scan for tiny k=1,2 universes.
for family in ('omino','hex','iamond'):
 g=Grid(family);shape=((0,0,0),);orients=g.orientations(shape)
 for k in (1,2):
  d=build(g,shape,k);seed=d['root'];previous={seed};pool=set()
  for _ in range(k):
   verts={v for t in previous for p in t for v in g.vertices(p)};new=set()
   for o in orients:
    for x,y in itertools.product(range(-8,9),repeat=2):
     t=frozenset((a+x,b+y,s) for a,b,s in o)
     if not t&seed and any(v in verts for p in t for v in g.vertices(p)):new.add(t)
   pool.update(new);previous=new
  assert pool==set(d['tiles']),(family,k,len(pool),len(d['tiles']))
  # Independent exhaustive exact cover for one-cell first-corona controls.
  if k==1:
   from engine import solve
   r=solve(g,shape,k,2);assert r['status']=='SAT'
   w=r['witness'];broken=[t for layer in w['layers'][1:] for t in layer][1:]
   try:verify(g,shape,w['layers'][0][0],broken,k)
   except AssertionError:pass
   else:raise AssertionError('incomplete corona accepted')
 checks.append({'family':family,'tinyCandidateUniverses':True,'deletedTileRejected':True})
expected={'omino':[1,1,2,5,12,35,108], 'hex':[1,1,3,7,22,82], 'iamond':[1,1,1,3,4,12,24]}
for family,counts in expected.items():
 _,rows=enumerate_free(Grid(family),len(counts));assert [r['all'] for r in rows]==counts
catalog={r['id']:r for r in json.loads((root/'catalog.json').read_text())}
replayed=0;regenerated=0;periodic=0;matched=0
for folder in ('runs','longer-runs','census'):
 for path in sorted((root/folder).rglob('*.json')):
  r=json.loads(path.read_text())
  if 'family' not in r and r.get('id') in catalog:r['family']=catalog[r['id']]['family'];r['cells']=catalog[r['id']]['cells']
  if 'witness' in r:
   g=Grid(r['family']);shape=g.from_source(r['cells']);w=r['witness'];layers=w['layers'];tiles=[t for layer in layers[1:] for t in layer]
   test=verify(g,shape,layers[0][0],tiles,r['depth']);assert test['verified']
   if 'holefree' in path.name:assert test['holeFree']
   replayed+=1
  if r.get('proofVerified') and 'depth' in r:
   d=build(Grid(r['family']),Grid(r['family']).from_source(r['cells']),r['depth'])
   if r.get('encoding')=='exact-parent':
    from strengthened import strengthen
    d=strengthen(Grid(r['family']),d)
   cnf=f"p cnf {d['variables']} {len(d['clauses'])}\n"+''.join(' '.join(map(str,c))+' 0\n' for c in d['clauses'])
   assert hashlib.sha256(cnf.encode()).hexdigest()==r['cnfSHA256']
   assert gzip.decompress(path.with_suffix('.cnf.gz').read_bytes())==cnf.encode()
   assert hashlib.sha256(gzip.decompress(path.with_suffix('.drup.gz').read_bytes())).hexdigest()==r['drupSHA256']
   assert 's VERIFIED' in path.with_suffix('.checker.log').read_text();regenerated+=1
  if 'certificate' in r:
   g=Grid(r['id'].split('-')[0]);c=r['certificate'];(a,_),(shift,b)=c['basis'];seen=[]
   for tile in c['tiles']:
    assert normalize(tile) in g.orientations(tuple(map(tuple,r['cells'])))
    seen.extend(((x-(y//b)*shift)%a,y%b,s) for x,y,s in tile)
   assert len(seen)==len(set(seen))==a*b*len(g.types);periodic+=1
  if r.get('status')=='finite' and r.get('publishedId'):
   assert r['Hh']==catalog[r['publishedId']]['Hh'];assert r['proofVerified'];matched+=1
receipt=dict(tinyChecks=checks,witnessesReplayed=replayed,formulasRegenerated=regenerated,periodicCertificatesReplayed=periodic,publishedFiniteValuesMatched=matched,engineSHA256=hashlib.sha256(pathlib.Path('scripts/planar-heesch/engine.py').read_bytes()).hexdigest())
(root/'verification.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
