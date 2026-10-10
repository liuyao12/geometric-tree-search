"""Independent full-tree, relational attention and sampled update audit."""
import copy
import gzip
import hashlib
import json
import statistics
import time
from pathlib import Path
import check_receptor_attention as V
from receptor_attention_artifact import load
from receptor_attention_cases import registry
from audit_quantifier_families import grammar,learn

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
LANES=('base','fixed','attention','zero','goal_heuristic')
HEURISTIC=(0.,0.,2.,1.,2.,0.,0.,0.,0.,0.,0.,0.)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def semantic(r):
    fields=('status','placements','tile_generations','proof','endpoint','candidate_universe','search_tree','hints','solution_hints','policy_events','attention_support','weights','stochastic','seed','mode')
    return dict(**{k:r[k] for k in fields},metrics={k:v for k,v in r['metrics'].items() if not k.endswith('seconds')})
def audit(data):
    began=time.perf_counter();ds,ts,es=registry();known={};checks=[]
    V.N(V.F([d['spec'] for d in data['donors']])==V.F(ds),'all fresh discovery statements')
    for i,d in enumerate(data['donors']):
        rules,spec=grammar(d);checks.append(V.result(rules,spec,known,d['result']))
        expected=learn(d,known,6 if i==2 else 5);actual=[t for t in data['library'] if t['source']['spec']['id']==d['spec']['id']]
        V.N(len(actual)==len(expected),'all and only fresh mixed primitive windows')
        for t,w in zip(actual,expected):
            fields=('name','pattern','children','level')
            V.N(V.F({k:t[k] for k in fields})==V.F({k:w[k] for k in fields}),'exact source abstraction and hierarchy')
            src=t['source'];V.N(V.F(src['members'])==V.F(w['members']),'original donor placements')
            V.N(V.V.V.digest(src['result'])==V.V.V.digest(d['result']) and V.F(src['spec'])==V.F(d['spec']) and V.F(src['catalog'])==V.F(d['catalog']),'same fresh searched provenance')
            V.N(V.F(src['check'])==V.F(d['result']['point_check']),'source point/kernel check')
            known[t['name']]=t
        print(d['spec']['id'],'discovery replayed',flush=True)
    train=data['training'];V.N(V.F(train['specs'])==V.F(ts) and len(known)==len(data['library']),'whole corpus and inventory')
    V.N(data['budgets']==dict(training=dict(attempts=50000,seconds=10),evaluation=dict(attempts=50000,seconds=60)),'explicit training/evaluation budgets')
    V.N(tuple(train['features'])==V.FEATURES and train['epochs']==8 and train['rate']==2. and train['initial_weights']==[0.]*12,'declared fresh sampled policy')
    V.N(len(train['initial_baseline_runs'])==6 and len(train['episodes'])==48,'six previous-observation baselines and forty-eight sampled episodes')
    baselines={};training_seconds=0.
    for spec,b in zip(ts,train['initial_baseline_runs']):
        V.N(V.F(spec)==V.F(b['spec']) and b['result']['mode']=='base','fresh base baseline statement')
        rules,sp=grammar(b);checks.append(V.result(rules,sp,known,b['result']))
        V.N(b['result']['limits']['attempts']==50000 and b['result']['limits']['seconds']==10,'original baseline budget')
        baselines[spec['id']]=V.reward(b['result']);training_seconds+=b['seconds']
    weights=[0.]*12;position=0;draws=0
    for epoch in range(8):
        order=list(range(6));offset=epoch%6;order=order[offset:]+order[:offset]
        for j in order:
            e=train['episodes'][position];r=e['result']
            V.N(e['epoch']==epoch and e['training_index']==j and V.F(e['spec'])==V.F(ts[j]),'rotating sampled episode inputs')
            V.V.V.close(weights,e['weights_before']);V.V.V.close(weights,r['weights'])
            V.N(r['mode']=='policy' and r['stochastic'] and r['seed']==17900+position,'actual sampled branch policy')
            V.N(r['limits']['attempts']==50000 and r['limits']['seconds']==10,'unchanged training cutoff and return normalization')
            rules,sp=grammar(e);checks.append(V.result(rules,sp,known,r))
            weights,baseline=V.update(weights,baselines[ts[j]['id']],r,e['update']);baselines[ts[j]['id']]=baseline
            draws+=len(r['policy_events']);position+=1;training_seconds+=e['seconds']
        print('epoch',epoch+1,'every draw and episode gradient replayed',flush=True)
    V.V.V.close(weights,train['weights']);V.N(baselines==train['baselines'] and training_seconds==train['seconds'],'frozen final parameters, per-statement baselines and stage sum')
    V.N(tuple(data['lanes'])==LANES and tuple(data['heuristic_weights'])==HEURISTIC and len(data['cases'])==len(es),'matched controls and whole evaluation registry')
    bound=V.deferral_bound(weights,known)
    repeats=0;positives=0;equivalences=0;learned_equivalences=0;evaluation_seconds=0.
    for i,(c,spec) in enumerate(zip(data['cases'],es)):
        V.N(V.F(c['spec'])==V.F(spec) and spec['id'] not in {s['id'] for s in ts},'frozen evaluation after all training')
        rules,sp=grammar(c);V.N(set(c['runs'])==set(LANES),'all five complete point lanes')
        for lane,r in c['runs'].items():
            expected=None if lane in ('base','fixed') else weights if lane=='attention' else HEURISTIC if lane=='goal_heuristic' else [0.]*12
            V.N(V.F(r['weights'])==V.F(expected) and not r['stochastic'] and r['seed']==0,'same frozen evaluation parameters')
            V.N(r['mode']==('base' if lane=='base' else 'fixed' if lane=='fixed' else 'policy'),'actual declared lane')
            V.N(r['limits']['attempts']==50000 and r['limits']['seconds']==60,'same longer evaluation budget in every lane')
            checks.append(V.result(rules,sp,known,r));positives+=r['proof'] is not None
            pin=V.V.V.digest(semantic(r));V.N(pin==r['semantic_sha256'],'full semantic tree binding')
            timing=c['timings'][lane];samples=timing['samples'];V.N(len(samples)==5,'five independent cold observations')
            for j,a in enumerate(samples):
                offset=(i+j)%5;V.N(tuple(a['order'])==LANES[offset:]+LANES[:offset] and a['repetition']==j,'all five lane positions balanced')
                V.N(a['semantic_sha256']==pin and a['seconds']>=a['search_seconds']+a['grammar_seconds']+a['positive_check_seconds']+a['worker_setup_seconds']>=0 and 0<=a['attention_prep_seconds']<=a['search_seconds'] and 0<=a['index_build_seconds']<=a['search_seconds'],'inclusive cold clock and exact tree binding')
            values=[a['seconds'] for a in samples]
            V.N(timing['median_seconds']==statistics.median(values) and timing['min_seconds']==min(values) and timing['max_seconds']==max(values),'exact observed timing summary');repeats+=5
        # Removing policy/join annotations gives a literal complete base tree
        # for zero attention, which chooses defer on every exact score tie.
        def strip(t):
            return dict(kind=t['kind'],point=t['point'],children=[dict(key=c['key'],tree=strip(c['tree'])) for c in t['children']],**({'cutoff':t['cutoff']} if 'cutoff' in t else {}))
        a,b=c['runs']['zero'],c['runs']['base']
        V.N(all(e['selected']==0 for e in a['policy_events']) and not a['hints'] and V.F(strip(a['search_tree']))==V.F(strip(b['search_tree'])),'entire zero-policy base fallback equivalence');equivalences+=1
        if bound['status']=='certified_always_defer':
            a=c['runs']['attention']
            V.N(all(e['selected']==0 for e in a['policy_events']) and not a['hints'] and V.F(strip(a['search_tree']))==V.F(strip(b['search_tree'])),'entire globally bounded attention/base equivalence');learned_equivalences+=1
        for r in c['controls'].values():
            if r['proof'] is not None:
                V.V.A.A.proof(r['proof'],spec['target'],spec['hypotheses'],spec['theory'])
                V.N(r['fits_region_bound']==(len(r['proof'])<=spec['bound']),'separate classical bound')
                if r['fits_region_bound']:
                    cert=r['region_certificate'];V.V.A.certificate(rules,spec,cert,cert['tiles']);V.V.W.certificate(spec,cert)
        evaluation_seconds+=c['seconds'];print(spec['id'],'full point search and attention replayed',flush=True)
    V.N(evaluation_seconds==data['evaluation_seconds'] and data['seconds']==data['donor_seconds']+train['seconds']+evaluation_seconds,'recorded complete-stage sums')
    mutations=[];sample=data['cases'][1];rules,sp=grammar(sample)
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,TypeError,IndexError):mutations.append(name)
        else:raise ValueError('accepted corrupt '+name)
    for field in ('features','scores','probabilities','gradient','selected','draw','chosen','point'):
        r=copy.deepcopy(sample['runs']['zero']);e=next(e for e in r['policy_events'] if e['items'])
        if field=='features':e[field][0][0]+=1
        elif field in ('scores','probabilities','gradient'):e[field][0]+=1
        elif field=='selected':e[field]=1
        elif field=='draw':e[field]=.1
        elif field=='chosen':e[field]=[[999,999,[]]]
        else:e[field]=[999,0]
        reject('attention-'+field,lambda r=r:V.result(rules,sp,known,r))
    r=copy.deepcopy(sample['runs']['zero']);r['attention_support']['distances']=[]
    reject('relaxed-support',lambda:V.result(rules,sp,known,r))
    for field in ('reward','baseline_before','advantage','gradient','weights_after','baseline_after'):
        e=copy.deepcopy(train['episodes'][0]);u=e['update']
        if isinstance(u[field],list):u[field][0]+=1
        else:u[field]+=1
        reject('update-'+field,lambda e=e:V.update(e['weights_before'],train['episodes'][0]['update']['baseline_before'],e['result'],e['update']))
    return dict(status='passed',searches=len(checks),independent_states=sum(c['nodes'] for c in checks),index_queries=sum(c['index_queries'] for c in checks),
        attention_events=sum(c['attention_events'] for c in checks),on_policy_draws=draws,updates=48,templates=len(known),levels=sorted({t['level'] for t in known.values()}),
        deferral_bound=bound,
        evaluation_positive_certificates=positives,repeated_cold_summaries=repeats,whole_zero_base_equivalences=equivalences,whole_attention_base_equivalences=learned_equivalences,mutations_rejected=mutations,seconds=time.perf_counter()-began,
        scope='Independent complete original domains, full primary trees and ordered family joins, all exact distant interfaces, typed matching tables and queries, source hierarchy, point/source/discharged proofs, relaxed relational features, every sampled draw and summed episode gradient. Repeat clocks are bound to primary digests; complete repeat trees, wall clocks and classical negative/unknown traces are not reconstructed.')
def main():
    path=DOC/'receptor-attention-001.json';data=load(path)
    for name,pin in {**data['sources'],**data['recovery_sources']}.items():V.N(sha(HERE/name)==pin,'frozen measured source '+name)
    out=audit(data);out.update(version='receptor-attention-audit-001',input_sha256=sha(path),source_sha256=sha(__file__),helpers={n:sha(HERE/n) for n in ('check_receptor_attention.py','check_quantifier_families.py','audit_quantifier_families.py','receptor_attention_cases.py','check_resumable_clusters.py','check_adaptive_clusters.py','check_compact_contexts.py','check_movable_regions.py','check_quantified_receptors.py')})
    (DOC/'receptor-attention-audit-001.json').write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
