"""Fresh scoped quantifier families, contextual transfer and paired cold solves."""
import gzip,hashlib,json,resource,statistics,time
from pathlib import Path
import quantifier_family_search as I
import quantifier_family_patterns as P
import quantifier_family_cases as QC
import resumable_clusters as R
import movable_proof_regions as M
from run_adaptive_clusters import inventory
from run_resumable_clusters import decorate,control,SOURCES as OLD_SOURCES
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
SOURCES=tuple(dict.fromkeys(('run_quantifier_families.py','quantifier_family_patterns.py','quantifier_family_join.py','quantifier_family_search.py','quantifier_family_cases.py','indexed_family_join.py',*OLD_SOURCES)))
LANES=('base','fixed','rl','zero')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def semantic(r):
    keys=('status','placements','tile_generations','proof','endpoint','candidate_universe','search_tree','hints','solution_hints','policy_events')
    return dict(**{k:r[k] for k in keys},metrics={k:v for k,v in r['metrics'].items() if not k.endswith('seconds')})
def run(s,library=(),mode='base',weights=None,indexed=True,stochastic=False,seed=0,attempts=50000):
    began=time.perf_counter();cat=inventory(s);grammar=time.perf_counter()-began;m=M.Model(cat,s['target'],s['bound'],s['hypotheses'])
    result=I.search(m,library,mode,weights,stochastic,seed,attempts=attempts,seconds=10,indexed=indexed)
    result['grammar_seconds']=grammar;decorate(s,cat,result);result['total_seconds']=time.perf_counter()-began
    return cat,result
def main():
    began=time.perf_counter();pins={n:sha(HERE/n) for n in SOURCES};ds,ts,es=QC.registry();donors=[];library=[]
    for donor_index,s in enumerate(ds):
        c,r=run(s,library,'fixed' if library else 'base');library.extend(P.promote(s,c,r,library,maximum=6 if donor_index==2 else 5));donors.append(dict(spec=s,catalog=c,result=r))
    donor_seconds=time.perf_counter()-began;weights=[0.]*5;baseline=0.;episodes=[];started=time.perf_counter()
    for epoch in range(4):
        for j,s in enumerate(ts):
            c,r=run(s,library,'policy',weights,True,True,9800+epoch*len(ts)+j,attempts=10000)
            after,next_baseline,u=R.update(weights,baseline,r);episodes.append(dict(spec=s,catalog=c,result=r,weights_before=weights,baseline_after=next_baseline,update=u));weights,baseline=after,next_baseline
    training_seconds=time.perf_counter()-started
    def lane(s,name):
        return run(s,library,'base' if name=='base' else 'policy' if name in ('rl','zero') else 'fixed',
            weights if name=='rl' else [0.]*5 if name=='zero' else None,indexed=True)
    cases=[]
    for case_index,s in enumerate(es):
        runs={};samples={name:[] for name in LANES};cat=None
        for repetition in range(4):
            offset=(case_index+repetition)%len(LANES);order=LANES[offset:]+LANES[:offset]
            for name in order:
                cat,r=lane(s,name);pin=hashlib.sha256(canonical(semantic(r))).hexdigest()
                if name not in runs:r['semantic_sha256']=pin;runs[name]=r
                elif pin!=runs[name]['semantic_sha256']:raise ValueError('repeated cold solve changed semantic tree')
                samples[name].append(dict(repetition=repetition,order=order,seconds=r['total_seconds'],search_seconds=r['seconds'],
                    grammar_seconds=r['grammar_seconds'],positive_check_seconds=r.get('positive_check_seconds',0),semantic_sha256=pin,
                    index_build_seconds=r['index']['build_seconds'] if r['index'] else 0,proposal_seconds=r['metrics'].get('proposal_seconds',0)))
        timings={k:dict(samples=v,median_seconds=statistics.median(a['seconds'] for a in v),min_seconds=min(a['seconds'] for a in v),max_seconds=max(a['seconds'] for a in v)) for k,v in samples.items()}
        controls={k:control(s,k) for k in ('chronological','saturation')}
        cases.append(dict(spec=s,catalog=cat,runs=runs,timings=timings,controls=controls))
        print(s['id'],{k:(v['metrics']['attempts'],round(1000*timings[k]['median_seconds'],3)) for k,v in runs.items()},flush=True)
    out=dict(version='quantifier-families-001',sources=pins,donors=donors,library=library,donor_seconds=donor_seconds,
        training=dict(specs=ts,episodes=episodes,weights=weights,baseline=baseline,initial_weights=[0.]*5,features=R.FEATURES,seconds=training_seconds),cases=cases,
        seconds=time.perf_counter()-began,peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        timing_scope='Four independent cold model/index/cache solves per case/lane; cyclic order. Total includes fresh grammar, model, search/index, joins and positive proof/point/discharge checks. Raw trace serialization and whole independent audit are separate. No distributional or statistical significance claim.',
        scope='Freshly mined mixed instantiation/MP/generalization families and unary formula contexts. Context alpha normalization affects proposals only; ground words, rules, variable scope and every base alternative remain exact. One strict larger child containment at two hierarchy levels. Uniform finite grammar and full-capacity positional adaptation; no general FOL completeness, failure pruning or new native Wang execution.')
    if any(sha(HERE/n)!=pin for n,pin in pins.items()):raise ValueError('measured source changed')
    (DOC/'quantifier-families-001.json.gz').write_bytes(gzip.compress(canonical(out)+b'\n',mtime=0));print('complete',out['seconds'],flush=True)
if __name__=='__main__':main()
