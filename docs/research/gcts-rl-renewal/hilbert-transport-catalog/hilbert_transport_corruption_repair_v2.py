"""Versioned adversarial wire normalization; preserve the complete v1 catalog."""
import copy,json,signal,time
from pathlib import Path
import hilbert_transport_produce_v1 as P
import hilbert_transport_adapter_v1 as T
HERE=Path(__file__).resolve().parent

def main():
    os_limits=P.setup();began=time.perf_counter();repair=P.load(HERE/'plan-v2.json');plan=P.load(HERE/'plan-v1.json')
    for rel,p in {**repair['source_pins'],**repair['inputs']}.items():T.require(P.pin(P.ROOT/rel)==p,'frozen repair source/input')
    cert,source,binding,entries=P.bind(plan);model=P.load(HERE/'catalog-v1.json.gz');P.verify(model,cert,plan,source,binding)
    reports=[];payloads=HERE/'mutants-v2';payloads.mkdir(exist_ok=True)
    for case in plan['corruptions']:
        # JSON round trip is part of this frozen adversarial-input protocol:
        # every field has its own container, with no hidden host alias action.
        target=json.loads(T.word(model if case['target']=='model' else cert));part=target
        for key in case['path'][:-1]:part=part[key]
        key=case['path'][-1]
        if case['operation']=='delete':part.pop(key)
        elif case['operation']=='append':part[key].append(copy.deepcopy(part[key][case['copy_index']]))
        else:part[key]=copy.deepcopy(case['value'])
        P.save(payloads/(case['name']+'.json.gz'),target)
        try:P.verify(target if case['target']=='model' else model,target if case['target']=='certificate' else cert,plan,source,binding)
        except (P.C.Invalid,T.Invalid,KeyError,IndexError,TypeError) as e:reports.append(dict(name=case['name'],mutant_sha256=T.digest(target),status='rejected',reason=str(e)))
        else:raise T.Invalid('repaired corruption accepted '+case['name'])
    P.save(HERE/'corruptions-v2.json',reports);old=P.load(HERE/'corruptions-v1.json');P.guard()
    result=dict(status='passed_wire_normalized_corruption_repair',amendment_plan_sha256=P.pin(HERE/'plan-v2.json')['sha256'],catalog_sha256=P.pin(HERE/'catalog-v1.json.gz')['sha256'],rejected_corruptions=len(reports),changed_mutant_hashes=sum(a['mutant_sha256']!=b['mutant_sha256'] for a,b in zip(old,reports)),preserved_v1_catalog=True,production_seconds_before_final_write=time.perf_counter()-began,peak_rss_bytes=P.peak(),os_limits=os_limits,native_queries=0,target_searches=0,existing_native_engine_activation=False)
    P.save(HERE/'production-v2.json',result);print(json.dumps(result),flush=True);signal.alarm(0)
if __name__=='__main__':main()
