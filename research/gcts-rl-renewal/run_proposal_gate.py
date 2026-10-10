"""Fresh families and wall-time-trained request gates, with cold controls."""
import gzip,hashlib,resource,statistics,time
from pathlib import Path
import proposal_gate as Gate
import proposal_gate_search as S
import proposal_gate_cases as Cases
import quantifier_family_patterns as P
import movable_proof_regions as M
from run_quantifier_families import SOURCES as OLD_SOURCES
from run_adaptive_clusters import inventory
from run_resumable_clusters import decorate,control
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
SOURCES=tuple(dict.fromkeys(('run_proposal_gate.py','proposal_gate.py','proposal_gate_search.py','proposal_gate_cases.py','quantifier_family_search.py',*OLD_SOURCES)))
LANES=('base','always','gate','zero_gate','eager_zero')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def semantic(r):
    keys=('status','placements','tile_generations','proof','endpoint','candidate_universe','search_tree','hints','solution_hints','policy_events','gate_events','gate_weights')
    return dict(**{k:r[k] for k in keys},metrics={k:v for k,v in r['metrics'].items() if not k.endswith('seconds')})
def run(spec,library=(),mode='base',weights=None,gate_weights=None,stochastic=False,seed=0):
    began=time.perf_counter();cat=inventory(spec);grammar=time.perf_counter()-began
    model=M.Model(cat,spec['target'],spec['bound'],spec['hypotheses'])
    r=S.search(model,library,mode,weights,stochastic,seed,attempts=50000,seconds=10,gate_weights=gate_weights)
    r['grammar_seconds']=grammar;decorate(spec,cat,r);r['total_seconds']=time.perf_counter()-began
    return cat,r
def main():
    began=time.perf_counter();pins={name:sha(HERE/name) for name in SOURCES};ds,ts,es=Cases.registry();donors=[];library=[]
    for i,spec in enumerate(ds):
        cat,r=run(spec,library,'fixed' if library else 'base')
        library.extend(P.promote(spec,cat,r,library,maximum=6 if i==2 else 5))
        donors.append(dict(spec=spec,catalog=cat,result=r))
    donor_seconds=time.perf_counter()-began;weights=[0.]*len(Gate.FEATURES);baseline=0.;episodes=[];started=time.perf_counter()
    for epoch in range(8):
        for j,spec in enumerate(ts):
            i=epoch*len(ts)+j;cat,r=run(spec,library,'gated',gate_weights=weights,stochastic=True,seed=14300+i)
            after,next_baseline,update=Gate.update(weights,baseline,r)
            episodes.append(dict(spec=spec,catalog=cat,result=r,weights_before=weights,baseline_after=next_baseline,update=update))
            weights,baseline=after,next_baseline
        print('epoch',epoch+1,'weights',weights,flush=True)
    training_seconds=time.perf_counter()-started
    def lane(spec,name):
        if name=='base':return run(spec,library)
        if name=='always':return run(spec,library,'fixed')
        if name=='eager_zero':return run(spec,library,'policy',weights=[0.]*5)
        return run(spec,library,'gated',gate_weights=weights if name=='gate' else [0.]*len(Gate.FEATURES))
    cases=[]
    for i,spec in enumerate(es):
        runs={};samples={name:[] for name in LANES};cat=None
        for repetition in range(4):
            offset=(i+repetition)%len(LANES);order=LANES[offset:]+LANES[:offset]
            for name in order:
                cat,r=lane(spec,name);pin=hashlib.sha256(canonical(semantic(r))).hexdigest()
                if name not in runs:r['semantic_sha256']=pin;runs[name]=r
                elif pin!=runs[name]['semantic_sha256']:raise ValueError('cold repeat changed non-time semantics')
                samples[name].append(dict(repetition=repetition,order=order,seconds=r['total_seconds'],search_seconds=r['seconds'],grammar_seconds=r['grammar_seconds'],
                    positive_check_seconds=r.get('positive_check_seconds',0),gate_seconds=r['metrics'].get('gate_seconds',0),
                    index_build_seconds=r['index']['build_seconds'] if r['index'] else 0,proposal_seconds=r['metrics'].get('proposal_seconds',0),semantic_sha256=pin))
        timings={k:dict(samples=v,median_seconds=statistics.median(a['seconds'] for a in v),min_seconds=min(a['seconds'] for a in v),max_seconds=max(a['seconds'] for a in v)) for k,v in samples.items()}
        cases.append(dict(spec=spec,catalog=cat,runs=runs,timings=timings,controls={k:control(spec,k) for k in ('chronological','saturation')}))
        print(spec['id'],{k:(r['metrics']['attempts'],r['metrics'].get('gate_queries',0),r['metrics'].get('hint_started',0),round(1000*timings[k]['median_seconds'],2)) for k,r in runs.items()},flush=True)
    out=dict(version='proposal-gate-001',sources=pins,donors=donors,library=library,donor_seconds=donor_seconds,
        training=dict(specs=ts,episodes=episodes,weights=weights,baseline=baseline,initial_weights=[0.]*len(Gate.FEATURES),features=Gate.FEATURES,seconds=training_seconds),
        cases=cases,seconds=time.perf_counter()-began,peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        timing_scope='Four independent cold observations per goal/lane, rotating five-lane order. Inclusive grammar, model, gate, query/index, search and positive proof checks. Raw serialization and independent replay are separate.',
        scope='Request/defer decisions before any family construction, using existing graph counts. A requested pool uses the unchanged fixed selector; RL learns when to request it. Complete graph, all original alternatives and exact scope remain. No failure pruning, new native Wang execution or general completeness/speed claim.')
    if any(sha(HERE/n)!=pin for n,pin in pins.items()):raise ValueError('measured source changed')
    (DOC/'proposal-gate-001.json.gz').write_bytes(gzip.compress(canonical(out)+b'\n',mtime=0));print('complete',out['seconds'],flush=True)
if __name__=='__main__':main()
