"""Fresh complete GCTS searches and compact, fully discharged certificates."""
import copy,hashlib,json,resource,time
from pathlib import Path
import movable_proof_regions as M
import check_movable_regions as A
import quantified_receptors as Q
import adaptive_receptor_clusters as C
from run_adaptive_clusters import inventory,decorate
from compact_contexts import compile_request
from compact_context_cases import registry
from serialized_kernel import canonical,check,problem_hash
from audit_serialized_kernel import replay

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
SOURCES=('run_compact_contexts.py','compact_contexts.py','compact_context_cases.py','movable_proof_regions.py',
    'quantified_receptors.py','check_movable_regions.py','check_quantified_receptors.py','logic.py','turtle.py',
    'serialized_kernel.py','audit_serialized_kernel.py','adaptive_receptor_clusters.py','run_adaptive_clusters.py',
    'quantified_receptor_cases.py')

def execute(spec):
    started=time.perf_counter();catalog=inventory(spec);grammar=time.perf_counter()-started
    model=M.Model(catalog,spec['target'],spec['bound'],spec['hypotheses'])
    result=M.search(model,node_limit=100000,seconds=20)
    if result['proof'] is not None:
        result['tiles']=[dict(key=k,occupancy=model.placement(k).occupancy,marks=model.placement(k).marks) for k in result['placements']]
        result['point_check']=A.certificate(catalog['rules'],spec,result,result['tiles'])
        result['compact']=compile_request(result['proof'],spec['target'],spec['hypotheses'],spec['theory'])
    comparison=None
    if result['proof'] is not None and 0<len(spec['hypotheses'])<=3:
        t=time.perf_counter();commands,_=Q.commands(result['proof'],spec['hypotheses'])
        expanded=Q.discharge(commands,spec['hypotheses']);target=result['compact']['curried_target']
        # Both adapters are compared before the optional universal closure.
        req=dict(protocol='gcts-fol-1',theory=spec['theory'],target=target,blocks=[],proof=expanded)
        payload=canonical(req);host=check(payload,max_work=None,expected_problem_sha256=problem_hash(req))
        other=replay(payload,problem_hash(req))
        if host['status']!='accepted' or other['status']!='accepted':raise ValueError('small expanded comparison')
        comparison=dict(commands=len(expanded),request_bytes=len(payload),seconds=time.perf_counter()-t,
            host=host,independent=other,closure_excluded=True)
    return dict(spec=spec,catalog=catalog,result=result,grammar_seconds=grammar,
                total_seconds=time.perf_counter()-started,expanded_comparison=comparison)

def main():
    started=time.perf_counter();pins={n:digest(HERE/n) for n in SOURCES};cases=[]
    for s in registry():
        c=execute(s);cases.append(c)
        print(s['id'],c['result']['status'],len(c['result']['proof'] or []),
              c['result'].get('compact',{}).get('commands'),flush=True)
    donor=next(c for c in cases if c['spec']['id']=='branch-donor')
    # A new discovery produces a non-chain family; no proof witness is supplied.
    library=C.promote(donor['spec'],donor['catalog'],donor['result'],maximum=3)
    spec=next(c['spec'] for c in cases if c['spec']['id']=='branch-compound')
    runs={}
    for mode in ('base','fixed'):
        catalog=inventory(spec);model=M.Model(catalog,spec['target'],spec['bound'],spec['hypotheses'])
        r=C.search(model,library,mode,attempts=20000,seconds=10);decorate(spec,catalog,r)
        if r['proof'] is not None:r['compact']=compile_request(r['proof'],spec['target'],spec['hypotheses'],spec['theory'])
        runs[mode]=r
    out=dict(version='compact-contexts-001',sources=pins,cases=cases,library=library,
        transfer=dict(spec=spec,catalog=catalog,runs=runs),seconds=time.perf_counter()-started,
        peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scope='Fresh bounded point searches; primitive unchanged-kernel conjunction discharge; actual shared-dependency family transfer. '
              'No new trusted rule, added premise axiom, RL training, attention implementation, general logical completeness or speed superiority.')
    if any(digest(HERE/n)!=p for n,p in pins.items()):raise ValueError('measured source changed')
    (DOC/'compact-contexts-001.json').write_bytes(canonical(out)+b'\n')
    print('complete',out['seconds'],flush=True)
if __name__=='__main__':main()
