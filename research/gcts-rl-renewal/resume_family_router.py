"""Recover the frozen training checkpoint; checkpoint every evaluated statement.

The original producer was interrupted after training. These searches use its
unchanged run function and policy. Discarded incomplete evaluation work is not
included in the recorded finalized experiment-stage clocks.
"""
import gzip,json,resource,time
from pathlib import Path
import run_family_router as R
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=R.DOC
ACTIVE=HERE.parents[1]/'.gcts-active/family-router-20261010'
def main():
    load_start=time.perf_counter();cp=ACTIVE/'feedback-checkpoint.json.gz';data=json.loads(gzip.decompress(cp.read_bytes()))
    for n,pin in data['sources'].items():
        if R.sha(HERE/n)!=pin:raise ValueError('frozen measured source '+n)
    data['sources']['resume_family_router.py']=R.sha(__file__)
    if R.sha_bytes(data['training']['policy'])!=data['training']['policy_sha256']:raise ValueError('frozen training checkpoint policy')
    load_seconds=time.perf_counter()-load_start;_,_,es=R.Cases.registry();cases=[];times=[]
    for i,s in enumerate(es):
        path=ACTIVE/('evaluation-'+str(i)+'.json.gz')
        if path.exists():
            saved=json.loads(gzip.decompress(path.read_bytes()))
            if saved['sources']!=data['sources'] or saved['policy_sha256']!=data['training']['policy_sha256'] or saved['case']['spec']!=json.loads(canonical(s)):raise ValueError('exact evaluation checkpoint binding')
            c=saved['case'];elapsed=saved['seconds']
        else:
            began=time.perf_counter();runs={};samples={lane:[] for lane in R.LANES}
            for rep in range(4):
                offset=(i+rep)%4;order=R.LANES[offset:]+R.LANES[:offset]
                for lane in order:
                    cat,r=R.run(s,data['library'],lane,data['training']['policy']);pin=R.sha_bytes(R.semantic(r))
                    if lane not in runs:r['semantic_sha256']=pin;runs[lane]=r
                    elif pin!=runs[lane]['semantic_sha256']:raise ValueError('evaluation repeat changed semantic tree')
                    samples[lane].append(R.summary(r,rep,order))
            c=dict(spec=s,catalog=cat,runs=runs,timings={k:R.timing(v) for k,v in samples.items()},controls={k:R.control(s,k) for k in ('chronological','saturation')})
            elapsed=time.perf_counter()-began
            path.write_bytes(gzip.compress(canonical(dict(case=c,seconds=elapsed,sources=data['sources'],policy_sha256=data['training']['policy_sha256']))+b'\n',mtime=0))
        cases.append(c);times.append(elapsed)
        print(s['id'],{k:(v['metrics']['attempts'],round(c['timings'][k]['median_seconds']*1000,2),v['router_event']['selected'] if v['router_event'] else None) for k,v in c['runs'].items()},flush=True)
    for n,pin in data['sources'].items():
        if R.sha(HERE/n)!=pin:raise ValueError('measured source changed '+n)
    data.update(version='family-router-001',cases=cases,evaluation_seconds=sum(times),
        seconds=data['donor_seconds']+data['training']['seconds']+sum(times),peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        recovery=dict(checkpoint_sha256=R.sha(cp),checkpoint_load_seconds=load_seconds,per_case_checkpoints=len(cases),
            scope='Finalized donor, training and complete evaluation-stage clocks are summed across the frozen checkpoint and recovered searches. Serialization, loading, independent audit and discarded incomplete interrupted evaluation work are outside this total; their omission is not a net research-compute saving.'),
        timing_scope='Four fresh cold observations per goal/lane, fully balanced four-lane order. Inclusive grammar, model, routing features/decision, fixed joins, original search and positive proof checks. Routed lanes construct an extra initial graph; that duplicate work is charged. Per-goal clocks reuse the freshly discovered library; donor and training costs must be charged for first use or net learning benefit.',
        scope='One episode-level full-feedback contextual policy selects base or fixed family search. It does not learn member selection or branch-level attention. All original candidates, scheduler, scope and rollback remain frozen. Evaluation namespaces are unseen, but many statement shapes occur in training; three additional compositions are structural probes. No new native Wang execution, proof theory, failure pruning or general speed claim.')
    (DOC/'family-router-001.json.gz').write_bytes(gzip.compress(canonical(data)+b'\n',mtime=0));print('complete',data['seconds'],flush=True)
if __name__=='__main__':main()
