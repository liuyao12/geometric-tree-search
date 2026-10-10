"""Fresh sampled branch attention, complete fallback and paired cold controls.

Every completed stage is checkpointed. Re-entry consumes only source-pinned
completed stages; it does not restart a live process or retrain a frozen model.
"""
import gzip
import hashlib
import json
import resource
import statistics
import time
from pathlib import Path
import receptor_attention as A
import receptor_attention_search as S
from receptor_attention_cases import registry
import quantifier_family_patterns as P
import movable_proof_regions as M
from run_quantifier_families import SOURCES as OLD_SOURCES
from run_adaptive_clusters import inventory
from run_resumable_clusters import decorate,control
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
LEDGER=ROOT/'.gcts-active/receptor-attention-20261010'
SOURCES=tuple(dict.fromkeys(('run_receptor_attention.py','receptor_attention.py','receptor_attention_search.py','receptor_attention_cases.py',*OLD_SOURCES)))
LANES=('base','fixed','attention','zero','goal_heuristic')
HEURISTIC=(0.,0.,2.,1.,2.,0.,0.,0.,0.,0.,0.,0.)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def semantic(r):
    keys=('status','placements','tile_generations','proof','endpoint','candidate_universe','search_tree','hints','solution_hints','policy_events','attention_support','weights','stochastic','seed','mode')
    return dict(**{k:r[k] for k in keys},metrics={k:v for k,v in r['metrics'].items() if not k.endswith('seconds')})
def run(spec,library=(),mode='base',weights=None,stochastic=False,seed=0):
    began=time.perf_counter();cat=inventory(spec);grammar=time.perf_counter()-began
    model=M.Model(cat,spec['target'],spec['bound'],spec['hypotheses'])
    result=S.search(model,library,mode,weights,stochastic,seed,attempts=50000,seconds=10,proposal_limit=32)
    result['grammar_seconds']=grammar;decorate(spec,cat,result);result['total_seconds']=time.perf_counter()-began
    return cat,result
def load_stage(name,pins):
    path=LEDGER/(name+'.json.gz')
    if not path.exists():return None
    record=json.loads(gzip.decompress(path.read_bytes()))
    if record['sources']!=pins:raise ValueError('checkpoint source mismatch: '+name)
    print('loaded completed stage',name,flush=True);return record['data']
def save_stage(name,pins,data):
    path=LEDGER/(name+'.json.gz');tmp=path.with_suffix('.partial')
    tmp.write_bytes(gzip.compress(canonical(dict(sources=pins,data=data))+b'\n',mtime=0));tmp.replace(path)

def main():
    LEDGER.mkdir(parents=True,exist_ok=True);pins={n:sha(HERE/n) for n in SOURCES};ds,ts,es=registry()
    discovery=load_stage('discovery',pins)
    if discovery is None:
        began=time.perf_counter();donors=[];library=[]
        for i,spec in enumerate(ds):
            cat,r=run(spec,library,'fixed' if library else 'base')
            library.extend(P.promote(spec,cat,r,library,maximum=6 if i==2 else 5))
            donors.append(dict(spec=spec,catalog=cat,result=r))
        discovery=dict(donors=donors,library=library,seconds=time.perf_counter()-began)
        save_stage('discovery',pins,discovery)
    library=discovery['library'];baselines={};initial=[];training_seconds=0.
    for j,spec in enumerate(ts):
        name='baseline-'+str(j);record=load_stage(name,pins)
        if record is None:
            started=time.perf_counter();cat,r=run(spec)
            record=dict(spec=spec,catalog=cat,result=r,seconds=time.perf_counter()-started)
            save_stage(name,pins,record)
        baselines[spec['id']]=A.reward(record['result']);initial.append(record);training_seconds+=record['seconds']
    weights=[0.]*len(A.FEATURES);episodes=[]
    for epoch in range(A.EPOCHS):
        indices=list(range(len(ts)));offset=epoch%len(indices);indices=indices[offset:]+indices[:offset]
        for j in indices:
            i=len(episodes);name='episode-'+str(i);e=load_stage(name,pins);spec=ts[j]
            if e is None:
                started=time.perf_counter();cat,r=run(spec,library,'policy',weights,True,17900+i)
                after,next_baseline,u=A.update(weights,baselines[spec['id']],r)
                e=dict(epoch=epoch,training_index=j,spec=spec,catalog=cat,result=r,weights_before=weights,
                    update=u,seconds=time.perf_counter()-started)
                save_stage(name,pins,e)
            if e['weights_before']!=weights or e['training_index']!=j:raise ValueError('checkpoint training order')
            weights=e['update']['weights_after'];baselines[spec['id']]=e['update']['baseline_after'];episodes.append(e);training_seconds+=e['seconds']
        print('epoch',epoch+1,'weights',weights,'sampled_actions',sum(len(e['result']['policy_events']) for e in episodes),flush=True)
    def lane(spec,name):
        if name=='base':return run(spec)
        if name=='fixed':return run(spec,library,'fixed')
        return run(spec,library,'policy',weights if name=='attention' else HEURISTIC if name=='goal_heuristic' else [0.]*len(A.FEATURES))
    cases=[];evaluation_seconds=0.
    for i,spec in enumerate(es):
        name='evaluation-'+str(i);case=load_stage(name,pins)
        if case is None:
            started=time.perf_counter();runs={};samples={name:[] for name in LANES};cat=None
            for repetition in range(len(LANES)):
                offset=(i+repetition)%len(LANES);order=LANES[offset:]+LANES[:offset]
                for name in order:
                    cat,r=lane(spec,name);pin=hashlib.sha256(canonical(semantic(r))).hexdigest()
                    if name not in runs:r['semantic_sha256']=pin;runs[name]=r
                    elif pin!=runs[name]['semantic_sha256']:raise ValueError('cold repeat changed semantic tree')
                    samples[name].append(dict(repetition=repetition,order=order,seconds=r['total_seconds'],
                        search_seconds=r['seconds'],grammar_seconds=r['grammar_seconds'],positive_check_seconds=r.get('positive_check_seconds',0),
                        attention_prep_seconds=r['attention_prep_seconds'],index_build_seconds=r['index']['build_seconds'] if r['index'] else 0,
                        proposal_seconds=r['metrics'].get('proposal_seconds',0),semantic_sha256=pin))
            timings={name:dict(samples=v,median_seconds=statistics.median(s['seconds'] for s in v),min_seconds=min(s['seconds'] for s in v),max_seconds=max(s['seconds'] for s in v)) for name,v in samples.items()}
            case=dict(spec=spec,catalog=cat,runs=runs,timings=timings,controls={k:control(spec,k) for k in ('chronological','saturation')},seconds=time.perf_counter()-started)
            save_stage('evaluation-'+str(i),pins,case)
        cases.append(case);evaluation_seconds+=case['seconds']
        print(spec['id'],{k:(r['status'],r['metrics']['attempts'],len(r['hints']),round(1000*case['timings'][k]['median_seconds'],2)) for k,r in case['runs'].items()},flush=True)
    out=dict(version='receptor-attention-001',sources=pins,donors=discovery['donors'],library=library,donor_seconds=discovery['seconds'],
        training=dict(specs=ts,initial_baseline_runs=initial,episodes=episodes,initial_weights=[0.]*len(A.FEATURES),weights=weights,
            baselines=baselines,features=A.FEATURES,epochs=A.EPOCHS,rate=A.RATE,seconds=training_seconds),
        cases=cases,heuristic_weights=HEURISTIC,lanes=LANES,evaluation_seconds=evaluation_seconds,
        seconds=discovery['seconds']+training_seconds+evaluation_seconds,peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        timing_scope='Five fresh cold solves per lane/goal with all five lane positions balanced. Costs include grammar, model, relaxed support, every family join, attention, search and positive point/source/discharged-kernel checks. Stage sums omit serialization, checkpoint loading, independent audit and incomplete interrupted stages.',
        scope='Zero-initialized sampled branch-local softmax over validated quantified cluster instances and defer. Exact distant premises and relaxed goal dependencies supply shared relational features. No theorem-specific parameter, supplied proof, learned pruning or new point assignment. Complete original graph, propagation, reference scheduler, one-original-placement transitions, exact rollback and full fallback are retained. Finite uniform positional adapter with identity transforms, not new native universal Wang execution or general first-order completeness.')
    if any(sha(HERE/n)!=pin for n,pin in pins.items()):raise ValueError('measured source changed')
    (DOC/'receptor-attention-001.json.gz').write_bytes(gzip.compress(canonical(out)+b'\n',mtime=0))
    print('complete',out['seconds'],'gzip_bytes',(DOC/'receptor-attention-001.json.gz').stat().st_size,flush=True)
if __name__=='__main__':main()
