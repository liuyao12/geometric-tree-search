"""Assemble completed paired blind experiment; render report after independent audit."""
import sys,json,shutil,hashlib,re,html
from pathlib import Path
source=Path(sys.argv[1] if len(sys.argv)>1 else '/private/tmp/knot-blind35');project=Path(__file__).resolve().parents[1];dest=project/'research/knot-classifier'
data=json.loads((source/'manifest.json').read_text());data['lanes']=[json.loads((source/f'{name}.json').read_text()) for name in ('marked','brute')]
if any(l['incomplete'] for l in data['lanes']):raise ValueError('Both lanes must complete all 105 cases')
for lane in data['lanes']:
 last=lane['runs'][-1];lane['proofCosts']={}
 for name,field in [('root','rootLearning'),('local','extensions'),('capacity','learning')]:
  r=last[field] or {};lane['proofCosts'][name]={key:r.get(key,0) for key in ('nodes','probeMs','activationValidationNodes','activationValidationMs','transferValidationNodes','transferValidationMs','cacheHits','transferredApplications')}
 lane['proofProbeAndValidationNodes']=sum(c['nodes']+c['activationValidationNodes']+c['transferValidationNodes'] for c in lane['proofCosts'].values())
 lane['certificateVerificationMs']=sum(r['verificationMs'] for r in lane['runs'])
 lane['nodeAccountingScope']='Search expansions and cheap relaxed-cover/point-probe nodes are reported separately; their units have different author-geometry costs. All associated elapsed work is included in query and lane time.'
data['bounds']=data['lanes'][0]['bounds'];data['incomplete']=False;data['createdUtc']=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat();data['scheduler']='Resumable fair full-bank iterative DFS; same driver in both lanes.'
data['costScope']='Elapsed lane time through final snapshot includes all queries, root domains, failed reference/contour searches, online probes and activation/transfer checks, JavaScript positive-certificate replay, cold model construction and inter-query proof archival/checkpoints. Common scramble generation and independent artifact audit are separate.'
data['developmentPilot']='First three fixed inputs tested during development; not scored or timed in this fresh full experiment.'
files=['apps/knot-movie/depth-point-path.mjs','research/knot-classifier/lattice-blind-search.mjs','research/knot-classifier/lattice-lazy-search.mjs','research/knot-classifier/lattice-moves.mjs','research/knot-classifier/lattice-search.mjs','research/knot-classifier/local-extension-markings.mjs','scripts/prepare-blind-knots.mjs','scripts/benchmark-blind-lattice-knots.mjs']
data['sourceSha256']={f:hashlib.sha256((project/f).read_bytes()).hexdigest() for f in files}
shutil.copyfile(source/'marked-proofs.jsonl.gz',dest/'marked-proofs.jsonl.gz');(dest/'lattice-blind-benchmark.json').write_text(json.dumps(data)+'\n')
print(json.dumps({'assembled':True,'queries':len(data['cases']),'correct':[l['correct'] for l in data['lanes']],'unknown':[l['unknown'] for l in data['lanes']]}))
