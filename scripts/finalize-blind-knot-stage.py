"""Assemble an immutable retry/scaling stage without replacing prior results."""
import sys,json,hashlib,shutil,gzip,time
from pathlib import Path
from knot_proof_archive import archive_parts
started=time.perf_counter();source=Path(sys.argv[1]);name=sys.argv[2];project=Path(__file__).resolve().parents[1];dest=project/'research/knot-classifier'
data=json.loads((source/'manifest.json').read_text());data['lanes']=[json.loads((source/f'{lane}.json').read_text()) for lane in ('marked','brute')]
if any(l['incomplete'] or len(l['runs'])!=len(data['cases']) for l in data['lanes']):raise ValueError('Incomplete paired stage')
if data['lanes'][0]['bounds']!=data['lanes'][1]['bounds']:raise ValueError('Unmatched budgets')
for lane in data['lanes']:
    last=lane['runs'][-1];lane['proofCosts']={}
    for channel,field in [('root','rootLearning'),('local','extensions'),('capacity','learning')]:
        r=last[field] or {};lane['proofCosts'][channel]={k:r.get(k,0) for k in ('nodes','probeMs','activationValidationNodes','activationValidationMs','transferValidationNodes','transferValidationMs','cacheHits','transferredApplications')}
    lane['proofProbeAndValidationNodes']=sum(c['nodes']+c['activationValidationNodes']+c['transferValidationNodes'] for c in lane['proofCosts'].values())
    lane['certificateVerificationMs']=sum(r['verificationMs'] for r in lane['runs'])
    if lane['learn']:
        lane['proofArchive'].pop('file',None);lane['proofArchive'].update(archive_parts(source/'marked-proofs.jsonl.gz',dest,name))
    lane['nodeAccountingScope']='Geometric expansions and relaxed proof/validation nodes are separate units. Elapsed lane totals include both.'
data['bounds']=data['lanes'][0]['bounds'];data['incomplete']=False;data['createdUtc']=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
data['sourceSha256']=data['lanes'][0].get('sourceSha256') or json.loads((source/'source-sha256.json').read_text())
if all('sourceSha256' in l for l in data['lanes']) and data['lanes'][0]['sourceSha256']!=data['lanes'][1]['sourceSha256']:raise ValueError('Different engine versions between lanes')
data['costScope']='Lane elapsed includes all queries, full root domains, wrong references, failed contours, online learning, validation, certificate replay, cold initialization, and proof archival/checkpoints. Common preparation and independent audit separately reported. Prior-stage costs retained in combined reporting.'
if data.get('stage')=='scale12':
    data['artifactFormat']='blind-lattice-sharded-json-v1'
    for lane in data['lanes']:
        stubs=[]
        for run in lane['runs']:
            filename=f'{name}-{lane["lane"]}-query-{run["caseIndex"]:03d}.json.gz';raw=gzip.compress((json.dumps(run)+'\n').encode(),mtime=0);(dest/filename).write_bytes(raw)
            stub={k:run[k] for k in ('caseIndex','status','predictedKnot','correct','referenceIndex','nodes','totalMs')}
            stub['artifact']={'file':filename,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'format':'json.gz'};stubs.append(stub)
        lane['runs']=stubs
    data['artifactScope']='Lossless per-query gzip JSON includes complete root graph, every attempted search contour, learned-cost snapshots and any positive certificate. Each artifact is hash-bound by its manifest stub. Gzip JSONL proof archive parts preserve their original concatenated compressed bytes.'
data['artifactFinalizationMs']=1000*(time.perf_counter()-started)
path=dest/f'{name}-benchmark.json';path.write_text(json.dumps(data)+'\n');print(json.dumps({'report':str(path),'correct':[l['correct'] for l in data['lanes']],'unknown':[l['unknown'] for l in data['lanes']]}))
