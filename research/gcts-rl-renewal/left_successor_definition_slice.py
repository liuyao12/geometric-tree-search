"""Generic whole-request transitive block-call dependency slice diagnostic.

Proof commands, definitions retained, theory and target remain byte-identical.
Only definitions outside the explicit proof-call dependency closure can go.
This diagnostic does not submit a native query or supply a new derivation.
"""
import copy,gzip,hashlib,json,resource,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];PARENT=ROOT/'.gcts-active/left-successor-20261011';OUT=PARENT/'definition-slice'
def packed(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def slice_request(request):
    blocks=request['blocks'];registry={d['name']:d for d in blocks}
    if len(registry)!=len(blocks):raise ValueError('duplicate definition names')
    reached=set();calls=[]
    def visit(name):
        if name in reached:return
        if name not in registry:raise ValueError('undeclared called definition')
        reached.add(name)
        for row in registry[name]['proof']:
            if row['rule']=='block':calls.append(dict(caller=name,callee=row['name']));visit(row['name'])
    for row in request['proof']:
        if row['rule']=='block':calls.append(dict(caller='whole-proof',callee=row['name']));visit(row['name'])
    retained=[d for d in blocks if d['name'] in reached];order={d['name']:i for i,d in enumerate(retained)}
    if any(edge['caller']!='whole-proof' and order[edge['callee']]>=order[edge['caller']] for edge in calls):raise ValueError('definition dependencies are not strict prior')
    sliced=copy.deepcopy(request);sliced['blocks']=retained
    return sliced,dict(calls=calls,retained=[d['name'] for d in retained],removed=[d['name'] for d in blocks if d['name'] not in reached])
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text())
    for p,h in plan['source_sha256'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise ValueError('frozen diagnostic source '+p)
    for p,h in plan['input_sha256'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise ValueError('frozen diagnostic input '+p)
    observations=[]
    for i,record in enumerate(load(PARENT/'forward-control/native.json.gz')):
        request=record['request'];sliced,witness=slice_request(request);same=packed(sliced)==packed(request);observations.append(dict(query=i,source_request_sha256=hashlib.sha256(packed(request)).hexdigest(),original_definitions=len(request['blocks']),retained_definitions=len(sliced['blocks']),original_proof_commands=len(request['proof']),witness=witness,byte_identical_whole_request=same,diagnosis='already minimal explicit block-call dependency closure; no retry' if same else 'slice available; separate audit/native predeclaration required before retry',sliced_request=sliced))
    (OUT/'result.json.gz').write_bytes(gzip.compress(json.dumps(observations,separators=(',',':')).encode(),mtime=0));(OUT/'summary.json').write_text(json.dumps(dict(status='diagnostic_complete_pending_independent_audit',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,native_queries=0,all_requests_already_minimal=all(o['byte_identical_whole_request'] for o in observations),scope='Minimal explicit transitive definition-call dependency closure only; no claim of mathematically shortest proof or minimal heap footprint.'),indent=2)+'\n')
if __name__=='__main__':main()
