"""Predeclared native preparation diagnostics, never complete admission.

Select the largest canonical definition in every operation/origin stratum.
Compare the original and generically compacted bytes under the fixed checker.
Each completed query and full parser tapes are checkpointed before continuing.
Any unresolved pair stops the pilot; no partial token can authorize search.
"""
import gzip,hashlib,json,subprocess,time
from pathlib import Path
from certificate_boundary_search import canonical
from semantic_inventory_worker import oracle_for
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011';TMP=Path('/private/tmp/gcts-left-successor-pilot-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def need(t,m):
    if not t:raise ValueError(m)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'native-pilot-plan.json').read_text());base=json.loads((OUT/'plan.json').read_text());need(json.loads((OUT/'audit.json').read_text())['status']=='passed_preparation_audit_only','full grammar audit');need(json.loads((OUT/'compaction-preparation-audit.json').read_text())['status']=='passed_compaction_preparation_audit_only','all local compactions independently reconstructed')
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen pilot source '+p)
    original=load(OUT/(plan['lane']+'-core.json.gz'));compact=load(OUT/(plan['lane']+'-compact-core.json.gz'));all_definitions=dict(original={d['name']:d for d in original['definitions']},compact={d['name']:d for d in compact['definitions']});TMP.mkdir(parents=True,exist_ok=True);compile_start=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True);compile_seconds=time.perf_counter()-compile_start;setup=time.perf_counter();oracle=oracle_for(dict(directory=str(TMP/'native'),executable=str(TMP/'oracle')));summary=dict(status='running_preparation_pilot',observations=[],native_queries=0,target_searches=0,compile_seconds=compile_seconds,oracle_setup_seconds=time.perf_counter()-setup,aggregate_native_steps=0)
    try:
        for item in plan['strata']:
            unresolved=False
            for variant in plan['variants']:
                if time.perf_counter()-began>=plan['ceilings']['seconds'] or len(oracle.records)>=plan['ceilings']['queries'] or summary['aggregate_native_steps']>=plan['ceilings']['aggregate_micro_steps']:
                    summary['status']='unknown_native_pilot_budget';return
                d=all_definitions[variant][item['name']];need(hashlib.sha256(canonical(d)).hexdigest()==item[variant+'_definition_sha256'],'declared exact representative definition');taut=['imp',['bot'],['bot']];request=dict(protocol='gcts-fol-1',theory=base['case']['theory'],blocks=[d],proof=[dict(rule='tautology',formula=taut)],target=taut)
                q=oracle.request(request,plan['ceilings']['per_query_micro_steps'],'left_successor_preparation_'+item['stratum']+'_'+variant);fixed,free=boundary_words(q['request']);q.update(boundary_words=dict(fixed=fixed,free=free),limit=plan['ceilings']['per_query_micro_steps'],stratum=item['stratum'],variant=variant,definition_name=d['name']);save(OUT/'pilot-native.json.gz',oracle.records)
                for name in ('input.bin','output.bin'):(OUT/('pilot-query-%03d-'%q['id']+name+'.gz')).write_bytes(gzip.compress((TMP/'native'/name).read_bytes(),mtime=0))
                obs=dict(query=q['id'],stratum=item['stratum'],variant=variant,definition=d['name'],commands=len(d['proof']),request_sha256=q['request_sha256'],status=q['result']['status'],seconds=q['seconds'],micro_steps=q['result']['micro_steps'],peak_native_memory_bytes=q['result']['peak_native_memory_bytes']);summary['observations'].append(obs);summary.update(native_queries=len(oracle.records),aggregate_native_steps=summary['aggregate_native_steps']+q['result']['micro_steps'],seconds=time.perf_counter()-began);(OUT/'pilot-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(obs),flush=True);unresolved=unresolved or q['result']['status']!='accepted'
            if unresolved:
                summary.update(status='unknown_or_rejected_native_pilot',complete_inventory_authority=False);return
        summary.update(status='complete_representative_pilot_only',complete_inventory_authority=False,scope='Every declared size-maximal operation/origin representative checked, not every definition. Native model/target search remains unauthorized until complete admission.')
    finally:
        summary.update(seconds=time.perf_counter()-began,native_queries=len(oracle.records),scope='Diagnostic representative queries only. Full native tapes preserved. No complete admission token, target search, theorem proof, or RL/speed claim.');(OUT/'pilot-summary.json').write_text(json.dumps(summary,indent=2)+'\n');save(OUT/'pilot-native.json.gz',oracle.records);oracle.close()
if __name__=='__main__':main()
