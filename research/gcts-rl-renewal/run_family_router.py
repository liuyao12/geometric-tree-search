"""Fresh discovery, paired cold feedback, frozen routing and balanced controls."""
import gzip,hashlib,resource,statistics,time
from pathlib import Path
import family_router as Policy
import family_router_cases as Cases
import proposal_gate_search as Search
import movable_proof_regions as M
import quantifier_family_patterns as Patterns
from run_proposal_gate import SOURCES as OLD_SOURCES
from run_adaptive_clusters import inventory
from run_resumable_clusters import decorate,control
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
SOURCES=tuple(dict.fromkeys(('run_family_router.py','family_router.py','family_router_cases.py',*OLD_SOURCES)))
LANES=('base','fixed','router','zero')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def semantic(r):
    keys=('status','placements','tile_generations','proof','endpoint','candidate_universe','search_tree','hints','solution_hints','policy_events','gate_events','gate_weights','router_event')
    return dict(**{k:r[k] for k in keys},metrics={k:v for k,v in r['metrics'].items() if not k.endswith('seconds')})
def run(spec,library=(),lane='base',policy=None):
    began=time.perf_counter();cat=inventory(spec);grammar=time.perf_counter()-began
    model=M.Model(cat,spec['target'],spec['bound'],spec['hypotheses']);event=None;routing=0.;mode=lane
    if lane in ('router','zero'):
        start=time.perf_counter();state=model.initial();graph=M.Graph(model,state);ctx=Policy.context(model,state,graph)
        weights=policy['weights'] if lane=='router' else [0.]*len(policy['centers'])
        event=Policy.decision(ctx['features'],policy['centers'],weights,policy['bandwidth'])
        event.update(kind=ctx['kind'],point=ctx['point'],weights=weights)
        mode='fixed' if event['selected'] else 'base';routing=time.perf_counter()-start
    r=Search.search(model,library,mode,attempts=50000,seconds=10)
    r.update(grammar_seconds=grammar,router_event=event,routing_seconds=routing)
    decorate(spec,cat,r);r['total_seconds']=time.perf_counter()-began
    return cat,r
def summary(r,repetition,order):
    return dict(repetition=repetition,order=order,seconds=r['total_seconds'],search_seconds=r['seconds'],
        grammar_seconds=r['grammar_seconds'],positive_check_seconds=r.get('positive_check_seconds',0),
        routing_seconds=r['routing_seconds'],proposal_seconds=r['metrics'].get('proposal_seconds',0),
        index_build_seconds=r['index']['build_seconds'] if r['index'] else 0,
        status=r['status'],attempts=r['metrics']['attempts'],semantic_sha256=sha_bytes(semantic(r)))
def sha_bytes(value):return hashlib.sha256(canonical(value)).hexdigest()
def timing(samples):
    values=[s['seconds'] for s in samples]
    return dict(samples=samples,median_seconds=statistics.median(values),min_seconds=min(values),max_seconds=max(values))
def main():
    began=time.perf_counter();pins={n:sha(HERE/n) for n in SOURCES};ds,ts,es=Cases.registry();donors=[];library=[]
    for i,s in enumerate(ds):
        cat,r=run(s,library,'fixed' if library else 'base');library.extend(Patterns.promote(s,cat,r,library,maximum=6 if i==2 else 5))
        donors.append(dict(spec=s,catalog=cat,result=r))
    donor_seconds=time.perf_counter()-began;feedback=[];contexts=[];returns=[];train_start=time.perf_counter()
    for i,s in enumerate(ts):
        start=time.perf_counter();cat=inventory(s);m=M.Model(cat,s['target'],s['bound'],s['hypotheses']);state=m.initial();g=M.Graph(m,state)
        ctx=Policy.context(m,state,g);ctx['seconds']=time.perf_counter()-start;contexts.append(ctx)
        runs={};samples={lane:[] for lane in ('base','fixed')}
        for rep in range(4):
            order=('base','fixed') if (i+rep)%2==0 else ('fixed','base')
            for lane in order:
                cat,r=run(s,library,lane);pin=sha_bytes(semantic(r))
                if lane not in runs:r['semantic_sha256']=pin;runs[lane]=r
                elif pin!=runs[lane]['semantic_sha256']:raise ValueError('training repeat changed complete semantic tree')
                samples[lane].append(summary(r,rep,order))
        tsums={lane:timing(v) for lane,v in samples.items()}
        values=[statistics.median(Policy.reward(dict(status=a['status'],total_seconds=a['seconds'],limits=runs[lane]['limits'])) for a in samples[lane]) for lane in ('base','fixed')]
        returns.append(values);feedback.append(dict(spec=s,catalog=cat,context=ctx,runs=runs,timings=tsums,returns=values))
        print('feedback',s['id'],{lane:round(1000*t['median_seconds'],2) for lane,t in tsums.items()},values,flush=True)
    feedback_seconds=time.perf_counter()-train_start;fit_start=time.perf_counter();policy=Policy.fit(contexts,returns);fit_seconds=time.perf_counter()-fit_start
    # Freeze before the first evaluation search. No evaluation outcome updates it.
    policy_pin=sha_bytes(policy);print('frozen bandwidth',policy['bandwidth'],'training decisions',policy['training_decisions'],flush=True)
    checkpoint=dict(sources=pins,donors=donors,library=library,donor_seconds=donor_seconds,
        training=dict(specs=ts,feedback=feedback,policy=policy,policy_sha256=policy_pin,feedback_seconds=feedback_seconds,fit_seconds=fit_seconds,seconds=feedback_seconds+fit_seconds))
    checkpoint_path=HERE.parents[1]/'.gcts-active/family-router-20261010/feedback-checkpoint.json.gz'
    checkpoint_path.write_bytes(gzip.compress(canonical(checkpoint)+b'\n',mtime=0))
    cases=[]
    for i,s in enumerate(es):
        runs={};samples={lane:[] for lane in LANES}
        for rep in range(4):
            offset=(i+rep)%4;order=LANES[offset:]+LANES[:offset]
            for lane in order:
                cat,r=run(s,library,lane,policy);pin=sha_bytes(semantic(r))
                if lane not in runs:r['semantic_sha256']=pin;runs[lane]=r
                elif pin!=runs[lane]['semantic_sha256']:raise ValueError('evaluation repeat changed complete semantic tree')
                samples[lane].append(summary(r,rep,order))
        cases.append(dict(spec=s,catalog=cat,runs=runs,timings={k:timing(v) for k,v in samples.items()},controls={k:control(s,k) for k in ('chronological','saturation')}))
        print('evaluation',s['id'],{lane:(r['metrics']['attempts'],round(1000*statistics.median(a['seconds'] for a in samples[lane]),2),r['router_event']['selected'] if r['router_event'] else None) for lane,r in runs.items()},flush=True)
    if sha_bytes(policy)!=policy_pin or any(sha(HERE/n)!=v for n,v in pins.items()):raise ValueError('frozen policy or measured source changed')
    out=dict(version='family-router-001',sources=pins,donors=donors,library=library,donor_seconds=donor_seconds,
        training=dict(specs=ts,feedback=feedback,policy=policy,policy_sha256=policy_pin,feedback_seconds=feedback_seconds,fit_seconds=fit_seconds,seconds=feedback_seconds+fit_seconds),
        cases=cases,seconds=time.perf_counter()-began,peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        timing_scope='Four fresh cold solves per goal/lane, fully balanced four-lane order. Inclusive grammar, model, router features/decision, fixed joins, original search and positive proof checks. The routed lanes construct an extra initial graph to obtain their context; that duplicate work is charged. Training feedback reuses no evaluation result. Donor and training costs, raw serialization and independent audit are separate.',
        scope='One episode-level full-feedback contextual policy selects base or fixed family search. It does not learn member selection or branch-level attention. All original candidates, scheduler, scope and rollback remain frozen. Evaluation namespaces are unseen, but many statement shapes occur in training; three additional compositions are structural probes. No new native Wang execution, proof theory, failure pruning or general speed claim.')
    (DOC/'family-router-001.json.gz').write_bytes(gzip.compress(canonical(out)+b'\n',mtime=0));print('complete',out['seconds'],flush=True)
if __name__=='__main__':main()
