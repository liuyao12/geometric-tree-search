#!/usr/bin/env python3
import collections,datetime,hashlib,json,pathlib,platform
import pysat
base=pathlib.Path('data/planar-heesch');catalog={r['id']:r for r in json.loads((base/'catalog.json').read_text())};records=[]
for sid in ['omino-17-44','omino-17-193','hex-11-19','iamond-20-131']:
 row=catalog[sid];runs=[]
 for folder in ('runs','longer-runs'):
  for p in sorted((base/folder).glob(sid+'-*.json')):
   r=json.loads(p.read_text());r['path']=str(p);runs.append(r)
 positives=[r for r in runs if r['status']=='SAT'];uppers=[r for r in runs if r['status']=='UNSAT' and r.get('proofVerified')]
 witness=max(positives,key=lambda r:(r['depth'],r.get('witness',{}).get('holeFree',False))) if positives else None
 upper=min(uppers,key=lambda r:r['depth']) if uppers else None
 records.append(dict(**row,witness=witness,upper=upper,runs=[{k:v for k,v in r.items() if k!='witness'} for r in runs]))
census=[];examples=[]
for p in sorted((base/'census').glob('*summary.json')):
 r=json.loads(p.read_text());hist=collections.Counter(x['Hh'] for x in r['rows'] if x['status']=='finite')
 census.append(dict(family=r['family'],size=r['size'],enumerated=r['counts'][-1]['holeFree'],processed=len(r['rows']),classification=r['classification'],finiteHistogram=dict(hist),counts=r['counts'],path=str(p)))
 for x in r['rows']:
  if x['status']!='finite':continue
  runs=[json.loads((base/'census'/name).read_text()) for name in x['runs']]
  positives=[t for t in runs if t['status']=='SAT'];w=max(positives,key=lambda t:t['depth']) if positives else None
  if w:examples.append(dict(id=x['id'],family=r['family'],size=r['size'],Hh=x['Hh'],witness=w,publishedId=x.get('publishedId')))
report=dict(date=datetime.datetime.now(datetime.timezone.utc).isoformat(),records=records,census=census,examples=examples,python=platform.python_version(),pysat=pysat.__version__)
(base/'report.json').write_text(json.dumps(report,separators=(',',':')))
files=list(pathlib.Path('scripts/planar-heesch').glob('*.py'))+list(base.glob('sources/*'))+list(base.glob('runs/*.json'))+list(base.glob('longer-runs/*.json'))+list(base.glob('census/**/*.json'))+list(base.glob('**/*.checker.log'))
(base/'provenance.json').write_text(json.dumps(dict(date=report['date'],python=report['python'],pysat=report['pysat'],solvers=['Glucose3','Glucose4'],dratTrimCommit='2e3b2dc0ecf938addbd779d42877b6ed69d9a985',sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}),indent=2))
print('records',[(r['id'],r['witness'] and r['witness']['depth'],r['upper'] and r['upper']['depth']) for r in records]);print('census',[(r['family'],r['size'],r['processed'],r['classification']) for r in census])
