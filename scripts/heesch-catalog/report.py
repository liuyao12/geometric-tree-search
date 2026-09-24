#!/usr/bin/env python3
"""Assemble the candidate-only report; unknown cutoffs never become upper bounds."""
import collections,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2];F=ROOT/'data/heesch-catalog'
def read(p):return json.loads(p.read_text())
C=read(F/'catalog.json');skipped=set(read(F/'skipped-known-tilers.json')['skipped']);rows=[]
verified_upper=set()
for name in ['verification.json','runs-verification.json','deeper-verification.json']:
 if (F/name).exists():verified_upper.update((r['id'],r['k']) for r in read(F/name) if r.get('dratVerified'))
proof_checks={}
if (F/'graph-proof-verification.json').exists():proof_checks={r['id']:r for r in read(F/'graph-proof-verification.json')}
for r in C['systems']:
 if not r.get('voxels') or r['id'] in skipped or r['id']=='polycube_p9_48258':continue
 id=r['id'];record={'id':id,'name':r['name'],'voxels':r['voxels'],'scope':'Integer translations and proper cubic rotations; full touching-tile coronas.','evidence':[],'runs':[],'lower':0,'exact':None}
 if id=='nonacube_cross':record.update(exact=1,lower=1,aliases=['polycube_p9_48258'],note='Same shape as p9-48258; existing complete two-corona certificate.');record['evidence']=['docs/projects/nonacube-geometric-learning.html']
 for folder in ['runs','deeper']:
  for k in [1,2]:
   p=F/folder/(id+'-k'+str(k)+'.json')
   if not p.exists():continue
   run=read(p);record['runs'].append({key:v for key,v in run.items() if key!='witness'})
   if run['status']=='SAT':
    if k>=record['lower']:record['witnessFile']=str(p.relative_to(ROOT))
    record['lower']=max(record['lower'],k)
   if run['status']=='UNSAT' and (id,k) in verified_upper:record['exact']=k-1;record['evidence'].append(str(p.relative_to(ROOT)))
 for p in (F/'graph-screen').glob(id+'-*.json') if (F/'graph-screen').exists() else []:
  run=read(p);record['runs'].append({key:v for key,v in run.items() if key not in ['rules','witness']})
  if run['status']=='SAT':
   if run['k']>=record['lower']:record['witnessFile']=str(p.relative_to(ROOT))
   record['lower']=max(record['lower'],run['k'])
  if run['status']=='UNSAT' and id in proof_checks and proof_checks[id]['verified']:record['exact']=run['k']-1;record['evidence'].append('data/heesch-catalog/graph-proofs/'+id+'-k2.drup.gz')
 if record['exact'] is not None:assert record['lower']>=record['exact'];record['note']=record.get('note') or 'Complete corona exclusion, with an independently checked certificate.'
 else:record['note']='Verified corona witness; deeper cutoffs remain unresolved.'
 if id in proof_checks and proof_checks[id]['verified']:
  record['evidence'].extend([proof_checks[id]['formulaArchive'],proof_checks[id]['proofArchive'],proof_checks[id]['checkerLog']])
 if record.get('witnessFile'):record['evidence'].insert(0,record['witnessFile'])
 rows.append(record)
for angle in read(F/'edge-obstructions.json'):
 original=next(c for s in C['systems'] if s['id']==angle['system'] for c in s['components'] if c['name']==angle['component']);name={'TruncTetra':'Truncated tetrahedron'}.get(angle['component'],angle['component'])
 rows.append({'id':angle['system']+'::'+angle['component'],'name':name,'vertices':original['vertices'],'faces':original['faces'],'exact':angle.get('heesch'),'lower':0,'scope':'Individual solid, not its mixed-tile catalog system.','note':'Exact uniform-edge-angle obstruction; arbitrary rigid motions allowed.' if angle.get('verified') else 'Mixed dihedral angles: this angle test is inconclusive. A full corona reduction is still needed.','evidence':['data/heesch-catalog/edge-obstructions.json'],'runs':[]})
rows.append({'id':'chair44_relief','name':'Chair44 centered relief','exact':None,'lower':0,'scope':'Geometric relief tile; chamber-point export is not yet a Heesch-corona reduction.','note':'Deferred: needs a faithful full-boundary corona model; no inference from finite point windows.','evidence':['docs/projects/chair44-lattice-export.md'],'runs':[]})
benchmarks=[]
for d in ['benchmarks','benchmarks-k2']:
 p=F/d/'summary.json'
 if p.exists():benchmarks.extend(read(p)['results'])
rows.sort(key=lambda r:(r['exact'] is None,r['exact'] if r['exact'] is not None else -r['lower'],r['name']))
controls=[]
cp=F/'positive-controls/periodic-witness-checks.json'
if cp.exists():
 for r in read(cp):
  control=dict(r)
  for lane,suffix in [('blindGlucose','-blind.json'),('blindCadical','-cadical-blind.json'),('positivePhases','-positive-phases.json')]:
   p=cp.parent/(r['id']+suffix)
   if p.exists():control[lane]={key:v for key,v in read(p).items() if key!='witness'}
  control['witnessFile']='data/heesch-catalog/positive-controls/'+r['id']+'-periodic-coronas.json'
  controls.append(control)
result={'date':'2026-09-24','externalSourceAudit':'data/heesch-catalog/papoutsis/audit.json','scope':'Potential non-tilers only. Known space-fillers and periodic controls excluded; aliases consolidated.','newlyCertifiedPeriodic':[read(p) for p in sorted((F/'periodic').glob('*.json')) if read(p).get('verified')],'rows':rows,'positiveControls':controls,'benchmarks':benchmarks,'counts':{'candidates':len(rows),'finite':sum(r['exact'] is not None for r in rows),'zero':sum(r['exact']==0 for r in rows),'one':sum(r['exact']==1 for r in rows),'unresolved':sum(r['exact'] is None for r in rows)}}
(F/'study.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['counts']))
