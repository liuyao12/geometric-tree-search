"""Independent transitive-call closure and exact unchanged-request audit."""
import gzip,hashlib,json,resource,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];PARENT=ROOT/'.gcts-active/left-successor-20261011';OUT=PARENT/'definition-slice'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def packed(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def need(t,m):
    if not t:raise ValueError(m)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'audit-plan.json').read_text());records=load(PARENT/'forward-control/native.json.gz');observations=load(OUT/'result.json.gz');result=dict(status='checking',observations=[],native_queries=0)
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'exact audit source '+p)
    need(json.loads((PARENT/'forward-control/audit.json').read_text())['status']=='passed_complete_forward_control_and_native_replay','source whole requests independently replayed');need(len(records)==len(observations),'all existing whole computations')
    for i,(rec,obs) in enumerate(zip(records,observations)):
        request=rec['request'];definitions={d['name']:d for d in request['blocks']};roots=[r['name'] for r in request['proof'] if r['rule']=='block'];needed=set(roots);todo=list(roots)
        while todo:
            caller=todo.pop();need(caller in definitions,'closed declared calls')
            for row in definitions[caller]['proof']:
                if row['rule']=='block' and row['name'] not in needed:needed.add(row['name']);todo.append(row['name'])
        kept=[d for d in request['blocks'] if d['name'] in needed];sliced={**request,'blocks':kept};order={d['name']:j for j,d in enumerate(kept)};need(all(order[r['name']]<order[d['name']] for d in kept for r in d['proof'] if r['rule']=='block'),'strict prior dependency order');need(obs['query']==i and obs['source_request_sha256']==rec['request_sha256']==hashlib.sha256(packed(request)).hexdigest(),'exact audited whole request binding');need(obs['sliced_request']==sliced and obs['witness']['retained']==[d['name'] for d in kept] and obs['witness']['removed']==[d['name'] for d in request['blocks'] if d['name'] not in needed],'whole explicit transitive closure, relative order unchanged');need(obs['byte_identical_whole_request']==(packed(sliced)==packed(request)),'exact unchanged byte comparison');result['observations'].append(dict(query=i,original_definitions=len(definitions),minimal_dependency_closure_definitions=len(kept),proof_commands=len(request['proof']),byte_identical_request=obs['byte_identical_whole_request'],source_request_sha256=rec['request_sha256'],native_retry=False))
    result.update(status='passed_generic_definition_dependency_slice_diagnostic',seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,all_requests_already_minimal=all(o['byte_identical_request'] for o in result['observations']),scope='All actual whole request definitions already equal their minimal explicit transitive proof-call closure. Theory, target, exact proof commands and all retained definitions are unchanged. Both earlier heap unknowns are preserved; no native retry or new proof was performed.')
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
