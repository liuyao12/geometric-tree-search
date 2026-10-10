"""Reconstruct discovery, hygienic instances, full searches and policy updates."""
import copy,gzip,hashlib,json,statistics,time
from pathlib import Path
import check_quantifier_families as V
from quantifier_family_cases import registry
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
LANES=('base','fixed','rl','zero')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def semantic(r):
    keys=('status','placements','tile_generations','proof','endpoint','candidate_universe','search_tree','hints','solution_hints','policy_events')
    return dict(**{k:r[k] for k in keys},metrics={k:v for k,v in r['metrics'].items() if not k.endswith('seconds')})
def grammar(c):
    rules,forms=V.A.A.inventory(c['spec']);V.N(V.F(c['catalog']['rules'])==V.F(rules) and V.F(c['catalog']['formulas'])==V.F(forms),'complete original finite grammar')
    return V.F(rules),dict(c['spec'],_formulas=forms)
def learn(d,known,maximum):
    rules,spec=grammar(d);r=d['result'];rows=sorted((V.F(k) for k in r['placements'] if k[1]>=0),key=lambda k:k[0]);expected=[];seen={V.V.digest(t['pattern']) for t in known.values()}
    for first in range(len(rows)):
        for size in range(2,min(maximum,len(rows)-first)+1):
            window=rows[first:first+size];pattern=V.pattern_for(rules,window);pin=V.V.digest(pattern)
            if pin in seen:continue
            name='quantifier-family-'+pin[:20];inside={k[0]:i for i,k in enumerate(window)};children=[]
            for done in r['solution_hints']:
                item=done['item'];parts=V.F(item['members'])
                if item['template'] in known and set(parts)<set(window):children.append(dict(template=item['template'],offsets=[inside[k[0]] for k in parts],hint_id=done['id'],kind='completed_ordering_hint'))
            level=1+max((known[ch['template']]['level'] for ch in children),default=0)
            expected.append(dict(name=name,pattern=pattern,children=children,level=level,members=window));seen.add(pin)
    return expected
def audit(data):
    started=time.perf_counter();ds,ts,es=registry();known={};checks=[]
    V.N(V.F([d['spec'] for d in data['donors']])==V.F(ds),'fresh statement-only donor registry')
    for i,d in enumerate(data['donors']):
        rules,spec=grammar(d);checks.append(V.result(rules,spec,known,d['result']))
        expected=learn(d,known,6 if i==2 else 5);actual=[t for t in data['library'] if t['source']['spec']['id']==d['spec']['id']]
        V.N(len(actual)==len(expected),'all and only fresh primitive proof windows')
        for t,w in zip(actual,expected):
            V.N(V.F({k:t[k] for k in ('name','pattern','children','level')})==V.F({k:w[k] for k in ('name','pattern','children','level')}),'entire reconstructed typed abstraction and strict hierarchy')
            s=t['source'];V.N(V.F(s['members'])==V.F(w['members']),'actual consecutive logical source window')
            V.N(V.V.digest(s['result'])==V.V.digest(d['result']) and V.F(s['spec'])==V.F(d['spec']) and V.F(s['catalog'])==V.F(d['catalog']),'same freshly searched source, statement and original grammar')
            V.N(V.F(s['check'])==V.F(d['result']['point_check']),'source original point/kernel check binding')
            known[t['name']]=t
        print(d['spec']['id'],'discovery independently reconstructed',flush=True)
    V.N(len(known)==len(data['library']) and V.F(data['training']['specs'])==V.F(ts),'complete discovered inventory and declared training inputs')
    weights=[0.]*5;baseline=0.;draws=0
    V.N(data['training']['initial_weights']==weights and len(data['training']['episodes'])==16,'fresh zero weights and sixteen episodes')
    for i,e in enumerate(data['training']['episodes']):
        V.N(V.F(e['spec'])==V.F(ts[i%4]),'declared episode input');rules,spec=grammar(e)
        V.V.close(weights,e['weights_before']);V.V.close(weights,e['result']['weights']);V.N(e['result']['stochastic'] and e['result']['seed']==9800+i,'sampled on-policy episode')
        checks.append(V.result(rules,spec,known,e['result']));weights,baseline=V.W.update(weights,baseline,e['result'],e['update']);V.N(baseline==e['baseline_after'],'same moving baseline');draws+=len(e['result']['policy_events'])
    V.V.close(weights,data['training']['weights']);V.N(baseline==data['training']['baseline'],'frozen learned preferences')
    repeats=0;positives=0;completed=0;classical=0
    V.N(len(data['cases'])==len(es),'whole evaluation registry')
    for i,(c,s) in enumerate(zip(data['cases'],es)):
        V.N(V.F(c['spec'])==V.F(s) and s['id'] not in {q['id'] for q in ts},'held-out declared symbols and statements')
        rules,spec=grammar(c);statuses=set()
        for name,r in c['runs'].items():
            V.N(name in LANES,'declared point comparison lane')
            if name=='rl':V.V.close(weights,r['weights'])
            elif name=='zero':V.V.close([0.]*5,r['weights'])
            checks.append(V.result(rules,spec,known,r));statuses.add(r['status']);positives+=r['proof'] is not None;completed+=len(r['solution_hints'])
            pin=V.V.digest(semantic(r));V.N(pin==r['semantic_sha256'],'retained full semantic tree digest');t=c['timings'][name];samples=t['samples'];V.N(len(samples)==4,'four independently cold observations')
            for j,a in enumerate(samples):
                offset=(i+j)%4;V.N(tuple(a['order'])==LANES[offset:]+LANES[:offset] and a['repetition']==j,'rotating matched lane order')
                V.N(a['semantic_sha256']==pin and a['seconds']>=a['search_seconds']+a['grammar_seconds']+a['positive_check_seconds']>=0 and 0<=a['index_build_seconds']<=a['search_seconds'],'inclusive clocks and repeated trace binding')
            values=[a['seconds'] for a in samples];V.N(t['median_seconds']==statistics.median(values) and t['min_seconds']==min(values) and t['max_seconds']==max(values),'literal cold observations');repeats+=len(samples)
        V.N(set(c['runs'])==set(LANES) and len(statuses)==1,'same original inventory, finite boundaries and outcome')
        for r in c['controls'].values():
            if r['proof'] is not None:
                V.A.A.proof(r['proof'],s['target'],s['hypotheses'],s['theory']);V.N(r['fits_region_bound']==(len(r['proof'])<=s['bound']),'classical proof bound')
                if r['fits_region_bound']:
                    cert=r['region_certificate'];V.A.certificate(rules,s,cert,cert['tiles']);V.W.certificate(s,cert);classical+=1
        print(s['id'],'full original search and contextual queries replayed',flush=True)
    mutations=[];sample=next(c for c in data['cases'] if c['spec']['id']=='quantifier-capture');rules,spec=grammar(sample)
    def first(t,p):
        if p(t):return t
        for ch in t.get('children',()):
            out=first(ch['tree'],p)
            if out is not None:return out
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,TypeError,IndexError):mutations.append(name)
        else:raise ValueError('accepted corrupt '+name)
    for name in ('context','term','scope-guard','query','query-hits','model','library','pool','pending','fallback','point','target','role'):
        r=copy.deepcopy(sample['runs']['fixed']);a=r['index']
        if name in ('context','term','scope-guard'):
            node=next(n for n in a['nodes'].values() if n['rows'] and (n['node']['guards'] if name=='scope-guard' else True))
            if name=='scope-guard':node['node']['guards']=[]
            else:
                bindings=node['rows'][0][1];key=next(k for k in bindings if k.startswith('P' if name=='context' else 'T'));bindings[key]=['bot'] if name=='context' else ['fun','c',[]]
        elif name=='query':a['queries'].pop()
        elif name=='query-hits':a['metrics']['query_cache_hits']+=1
        elif name=='model':a['context']='!'
        elif name=='library':a['library_pin']='!'
        elif name=='pool':first(r['search_tree'],lambda t:bool(t.get('proposal_pool')))['proposal_pool'].pop()
        elif name=='pending':first(r['search_tree'],lambda t:bool(t.get('review',{}).get('pending')))['review']['pending']=[]
        elif name=='fallback':r['search_tree']['children'][0]['key'][1]=999999
        elif name=='point':r['tiles'][0]['marks'][0][1]='!'
        elif name=='target':r['compact']['request']['target']=['bot']
        else:r['search_tree']['children'][0]['role']='member'
        reject(name,lambda r=r:V.result(rules,spec,known,r))
    episode=copy.deepcopy(data['training']['episodes'][0]);episode['result']['policy_events'][0]['draw']=-1
    er,sp=grammar(episode);reject('policy-draw',lambda:V.result(er,sp,known,episode['result']))
    u=copy.deepcopy(data['training']['episodes'][0]);u['update']['reward']+=1;reject('policy-reward',lambda:V.W.update(u['weights_before'],u['update']['baseline_before'],u['result'],u['update']))
    return dict(status='passed',searches=len(checks),independent_states=sum(q['nodes'] for q in checks),index_queries=sum(q['index_queries'] for q in checks),templates=len(known),levels=sorted({t['level'] for t in known.values()}),on_policy_draws=draws,
        evaluation_positive_certificates=positives,evaluation_completed_families=completed,classical_region_certificates=classical,repeated_cold_summaries=repeats,mutations_rejected=mutations,seconds=time.perf_counter()-started,
        scope='Independent original domains, complete retained trees, every ordered family pool, typed term/context table, query/cache count, strict child containment, primitive proof and policy update. Four repeated clocks per lane are digest-bound; their full trees are not retained or independently replayed. Classical negative/unknown traces and wall clocks are not certified.')
def main():
    path=DOC/'quantifier-families-001.json.gz';data=json.loads(gzip.decompress(path.read_bytes()))
    for n,pin in data['sources'].items():V.N(sha(HERE/n)==pin,'frozen measured source '+n)
    out=audit(data);out.update(version='quantifier-families-audit-001',input_sha256=sha(path),source_sha256=sha(__file__),helpers={n:sha(HERE/n) for n in ('check_quantifier_families.py','check_resumable_clusters.py','check_adaptive_clusters.py','check_movable_regions.py','check_quantified_receptors.py','check_compact_contexts.py','quantifier_family_cases.py')})
    (DOC/'quantifier-families-audit-001.json').write_bytes(V.W.P(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
