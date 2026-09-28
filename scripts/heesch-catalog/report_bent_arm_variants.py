#!/usr/bin/env python3
"""Build the viewer summary without promoting solver timeouts into bounds."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'data/bent-six-arm/variants'
def read(p):return json.loads((ROOT/p).read_text())
base='data/bent-six-arm/';prefix=base+'variants/'
rows=[]
for id,name,stem,verification in [('bend_018','Two three-cycles',prefix+'bend_018-k1.json',prefix+'bend_018-verification.json'),('bend_036','One six-cycle (original)',base+'bent_six_arm_25-k1.json',base+'verification.json')]:
 r=read(stem);v=read(verification);assert r['status']=='UNSAT' and v['proofVerified']
 rows.append({'id':id,'name':name,'exact':0,'lower':0,'note':f"Glucose: {r['solveSeconds']:.2f} s. Independent proof and placement checks passed.",'evidence':[verification,stem,stem.replace('.json','.cnf.gz'),stem.replace('.json','.drup.gz')]})
name=prefix+'bend_064-k1.json';glucose=read(prefix+'bend_064-k1-glucose.json');r=read(name) if (ROOT/name).exists() else None
row={'id':'bend_064','name':'Opposite pairs; repeated bend directions','exact':None,'lower':0,'note':'Glucose remained undecided at 120 seconds.','evidence':[prefix+'bend_064-k1-glucose.json']}
if r:
 row['evidence'].append(name)
 if r['status']=='UNSAT':
  v=read(prefix+'bend_064-verification.json');assert v['proofVerified'];row.update(exact=0,note=f"Glucose undecided at 120 s; CaDiCaL proved UNSAT in {r['searchAndSetupSeconds']:.2f} s including setup. Independently checked.");row['evidence']+=[prefix+'bend_064-verification.json',prefix+'bend_064-k1.cnf.gz',prefix+'bend_064-k1.drup.gz']
 elif r['status']=='SAT':
  from verify_bent_six_arm import rotations,star,normalized
  prototype=next(x['voxels'] for x in read(prefix+'catalog.json')['rows'] if x['id']==row['id']);shapes=rotations(prototype);w=r['witness'];root=frozenset(map(tuple,w['root']));seen=set(root)
  for raw in w['tiles']:
   t=frozenset(map(tuple,raw));assert normalized(t) in shapes and not seen&t and t&star(root);seen.update(t)
  assert normalized(root) in shapes and star(root)<=seen
  row.update(lower=1,note=f"CaDiCaL found a verified first corona in {r['searchAndSetupSeconds']:.2f} s including setup. No upper bound yet.")
 else:row['note']+=' CaDiCaL also remained undecided at its 120-second budget (checked between conflict chunks).'
rows.append(row)
catalog=read(prefix+'catalog.json')['rows'];known={r['id']:r for r in rows};runs={}
for path in sorted((OUT/'first-coronas').rglob('*-screen.json')):
 for run in json.loads(path.read_text())['results']:
  runs.setdefault(run['id'],[]).append({**run,'record':str(path.relative_to(ROOT))})
for tile in catalog:
 id=tile['id']
 if id not in known and id in runs:
  known[id]={'id':id,'name':id,'exact':None,'lower':0,'note':'No verified first corona found. Time-limited searches give no upper bound.','evidence':sorted({r['record'] for r in runs[id]})}
 if id not in known:continue
 row=known[id];row['antipodal']=tile['antipodal'];row['runs']=runs.get(id,[])
 row['evidence']=list(dict.fromkeys(row['evidence']+[r['record'] for r in row['runs']]))
 vpath=prefix+id+'-verification.json'
 if id not in ['bend_018','bend_036'] and (ROOT/vpath).exists():
  v=read(vpath);assert v['proofVerified'] and v['independentRectangularScan'];stem=prefix+id+'-k1.json'
  row.update(exact=0,lower=0,note='No first corona: independent placement audit and DRAT-trim proof check passed.',evidence=[vpath,stem,stem.replace('.json','.cnf.gz'),stem.replace('.json','.drup.gz')])
 for path in sorted((OUT/'first-coronas').rglob(id+'-*-witness.json')):
  from search_bent_arm_coronas import check
  w=json.loads(path.read_text());v=check(tile,w);assert v['verified'] and row['exact']!=0
  row.update(lower=1,witnessFile=str(path.relative_to(ROOT)),note=f"Verified first corona with {v['surroundingTiles']} surrounding tiles. Exact Heesch number unresolved.")
  row['evidence'].insert(0,str(path.relative_to(ROOT)))
 if row['exact'] is None and not row['lower'] and any(r['status']=='UNSAT-unchecked' for r in row['runs']):
  row['note']='A solver reported no first corona, but its proof has not been independently checked; no certified upper bound is assigned.'
rows=sorted(known.values(),key=lambda r:r['id'])
summary={'date':'2026-09-27','scope':'Two outward and two sideways steps; 25 nonoverlapping cubes; proper rotations and integer translations; full face/edge/vertex touching first coronas. Time limits are not exclusions.','rawAssignments':4096,'nonoverlappingAssignments':1496,'classes':72,'centrallySymmetricClasses':3,'notSearchedClasses':72-len(rows),'verifiedFirstCoronas':sum(r['lower']>=1 for r in rows),'certifiedH0':sum(r['exact']==0 for r in rows),'unresolvedClasses':sum(r['exact'] is None and r['lower']==0 for r in rows),'rows':rows}
files=['scripts/heesch-catalog/bent_arm_variants.py','scripts/heesch-catalog/bent_arm_cadical.py','scripts/heesch-catalog/report_bent_arm_variants.py','scripts/heesch-catalog/search_bent_arm_coronas.py','scripts/heesch-catalog/corona.py','scripts/heesch-catalog/verify_bent_six_arm.py',prefix+'catalog.json']
files+=['docs/projects/bent-arm-corona-search.md']
summary['sourceSHA256']={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in files}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['rows','sourceSHA256']}))
