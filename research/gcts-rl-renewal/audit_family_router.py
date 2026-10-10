"""Full primary proof-search replay and independent paired-feedback policy audit."""
import copy,gzip,hashlib,json,statistics,time
from pathlib import Path
import check_family_router as C
import audit_quantifier_families as Old
from family_router_cases import registry
V,N,F=C.V,C.N,C.F
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
LANES=('base','fixed','router','zero')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def semantic(r):
    keys=('status','placements','tile_generations','proof','endpoint','candidate_universe','search_tree','hints','solution_hints','policy_events','gate_events','gate_weights','router_event')
    return dict(**{k:r[k] for k in keys},metrics={k:v for k,v in r['metrics'].items() if not k.endswith('seconds')})
def timing(c,lane,i,training=False):
    r=c['runs'][lane];pin=V.V.digest(semantic(r));N(pin==r['semantic_sha256'],'full retained semantic digest')
    t=c['timings'][lane];samples=t['samples'];N(len(samples)==4,'four independent cold observations')
    for rep,a in enumerate(samples):
        if training:order=('base','fixed') if (i+rep)%2==0 else ('fixed','base')
        else:
            offset=(i+rep)%4;order=LANES[offset:]+LANES[:offset]
        N(tuple(a['order'])==order and a['repetition']==rep,'declared fully balanced order')
        N(a['semantic_sha256']==pin and a['status']==r['status'] and a['attempts']==r['metrics']['attempts'],'cold repeat semantics')
        N(a['seconds']>=a['grammar_seconds']+a['search_seconds']+a['positive_check_seconds']+a['routing_seconds']>=0,'inclusive routing clocks')
        N(0<=a['index_build_seconds']<=a['search_seconds'] and 0<=a['proposal_seconds']<=a['search_seconds'],'matching costs included')
        N(a['routing_seconds']>=0 and (r['router_event'] is not None or a['routing_seconds']==0),'all and only route costs')
    values=[a['seconds'] for a in samples]
    N(t['median_seconds']==statistics.median(values) and t['min_seconds']==min(values) and t['max_seconds']==max(values),'literal medians and ranges')
    return len(samples)
def route(rules,spec,p,r,lane):
    e=r['router_event'];ctx=C.context(rules,spec)
    N(e is not None and e['kind']==ctx['kind'] and F(e['point'])==ctx['point'],'actual initial global scheduler')
    weights=p['weights'] if lane=='router' else [0.]*len(p['centers'])
    V.V.close(weights,e['weights']);C.decision(ctx['features'],p['centers'],weights,p['bandwidth'],e)
    N(r['mode']==('fixed' if e['selected'] else 'base'),'selected frozen controller')
    N(r['routing_seconds']>0,'feature graph construction and policy charged')
    return e['selected']
def audit(data):
    began=time.perf_counter();ds,ts,es=registry();known={};checks=[]
    N(F([d['spec'] for d in data['donors']])==F(ds),'fresh donor statements')
    for i,d in enumerate(data['donors']):
        rules,spec=Old.grammar(d);checks.append(V.result(rules,spec,known,d['result']))
        N(d['result']['router_event'] is None,'donor needs no saved routing policy')
        expected=Old.learn(d,known,6 if i==2 else 5);actual=[t for t in data['library'] if t['source']['spec']['id']==d['spec']['id']]
        N(len(actual)==len(expected),'all and only source windows')
        for t,w in zip(actual,expected):
            N(F({k:t[k] for k in ('name','pattern','children','level')})==F({k:w[k] for k in ('name','pattern','children','level')}),'independent mixed-rule abstraction and strict hierarchy')
            src=t['source'];N(F(src['members'])==F(w['members']),'actual searched window')
            N(V.V.digest(src['result'])==V.V.digest(d['result']) and F(src['spec'])==F(d['spec']) and F(src['catalog'])==F(d['catalog']),'source proof and original theory binding')
            N(F(src['check'])==F(d['result']['point_check']),'source point certificate');known[t['name']]=t
    tr=data['training'];feedback=tr['feedback'];N(len(known)==len(data['library']) and F(tr['specs'])==F(ts) and len(feedback)==12,'whole fresh inventory and feedback corpus')
    repeats=0
    for i,(c,s) in enumerate(zip(feedback,ts)):
        N(F(c['spec'])==F(s) and set(c['runs'])=={'base','fixed'},'two observed training actions and statement-only inputs')
        rules,spec=Old.grammar(c);ctx=C.context(rules,spec)
        V.V.close(ctx['features'],c['context']['features']);N(ctx['kind']==c['context']['kind'] and ctx['point']==F(c['context']['point']),'independent complete graph context')
        for lane,r in c['runs'].items():
            N(r['mode']==lane and r['router_event'] is None and not r['stochastic'],'both cold action returns before fitting')
            checks.append(V.result(rules,spec,known,r));repeats+=timing(c,lane,i,True)
        N(len({r['status'] for r in c['runs'].values()})==1,'same training proof-region outcome');C.returns(c)
        print('feedback',s['id'],'complete original trees replayed',flush=True)
    fitting=C.policy(feedback,tr['policy']);N(V.V.digest(tr['policy'])==tr['policy_sha256'],'frozen full policy before evaluation')
    N(len(data['cases'])==14,'entire evaluation registry');equivalent=0;requested=[];positive=0;classical=0
    for i,(c,s) in enumerate(zip(data['cases'],es)):
        N(F(c['spec'])==F(s) and s['id'] not in {t['id'] for t in ts},'declared unseen symbol namespace and evaluation statement')
        N(set(c['runs'])==set(LANES),'all four matched controls');rules,spec=Old.grammar(c)
        for lane,r in c['runs'].items():
            N(not r['stochastic'] and not r['gate_events'],'episode routing supplies no branch policy')
            N(r['limits']==dict(attempts=50000,seconds=10,proposal_limit=32),'same original budgets')
            if lane in ('router','zero'):route(rules,spec,tr['policy'],r,lane)
            else:N(r['mode']==lane and r['router_event'] is None and r['routing_seconds']==0,'unchanged fixed/base control')
            checks.append(V.result(rules,spec,known,r));repeats+=timing(c,lane,i);positive+=r['proof'] is not None
        N(len({r['status'] for r in c['runs'].values()})==1,'same verified original-region outcome')
        for lane in ('router','zero'):
            r=c['runs'][lane];ref=c['runs']['fixed' if r['router_event']['selected'] else 'base']
            for k in ('search_tree','placements','hints','solution_hints','proof','candidate_universe'):
                N(F(r[k])==F(ref[k]),'whole chosen original controller equivalence '+k)
            if not r['router_event']['selected']:N(r['index'] is None and not r['hints'],'deferral builds no family index')
            equivalent+=1
        if c['runs']['router']['router_event']['selected']:requested.append(s['id'])
        for control in c['controls'].values():
            if control['proof'] is not None:
                V.A.A.proof(control['proof'],s['target'],s['hypotheses'],s['theory']);N(control['fits_region_bound']==(len(control['proof'])<=s['bound']),'classical boundary scope')
                if control['fits_region_bound']:
                    cert=control['region_certificate'];V.A.certificate(rules,s,cert,cert['tiles']);V.W.certificate(s,cert);classical+=1
        print('evaluation',s['id'],'whole controller, routing and original proofs replayed',flush=True)
    rejected=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,IndexError,TypeError):rejected.append(name)
        else:raise ValueError('accepted corrupted '+name)
    c=data['cases'][0];rr,ss=Old.grammar(c)
    for field,value in [('features',[0.]*8),('basis',[0.]*12),('score',99.),('probabilities',[1.,0.]),('selected',3),('point',[999,0]),('weights',[99.]*12)]:
        bad=copy.deepcopy(c['runs']['router']);bad['router_event'][field]=value
        reject('route-'+field,lambda bad=bad:route(rr,ss,tr['policy'],bad,'router'))
    first=tr['policy']['selection']['candidates'][0]['updates'][0];centers=tr['policy']['centers'];values=feedback[0]['returns']
    for field,value in [('returns',[99.,99.]),('gradient',[99.]*12),('weights_after',[99.]*12),('expected_reward',99.)]:
        bad=copy.deepcopy(first);bad[field]=value
        reject('update-'+field,lambda bad=bad:C.step([0.]*12,centers[0],centers,values,.03,bad))
    bad=copy.deepcopy(c);bad['timings']['router']['samples'][0]['routing_seconds']=bad['timings']['router']['samples'][0]['seconds']+1
    reject('omitted-route-clock',lambda:timing(bad,'router',0))
    return dict(status='passed',searches=len(checks),independent_states=sum(c['nodes'] for c in checks),index_queries=sum(c['index_queries'] for c in checks),
        contexts=len(feedback)+2*len(data['cases']),updates=fitting['updates'],selected_bandwidth=fitting['bandwidth'],requested_evaluation=requested,
        templates=len(known),levels=sorted({t['level'] for t in known.values()}),whole_controller_equivalences=equivalent,evaluation_positive_certificates=positive,
        classical_region_certificates=classical,repeated_cold_summaries=repeats,mutations_rejected=rejected,seconds=time.perf_counter()-began,
        scope='Full primary original-domain trees, complete joins, source hierarchy, exact source/primitive proofs, initial routing contexts, all four candidate fits and training-only selection. Cold summaries bind to full primary digests; complete repeat trees, classical negative/unknown traces and clocks are not independently reconstructed.')
def main():
    path=DOC/'family-router-001.json.gz';data=json.loads(gzip.decompress(path.read_bytes()))
    for n,pin in data['sources'].items():N(sha(HERE/n)==pin,'frozen measured source '+n)
    out=audit(data);out.update(version='family-router-audit-001',input_sha256=sha(path),source_sha256=sha(__file__),helpers={n:sha(HERE/n) for n in ('check_family_router.py','check_proposal_gate.py','check_quantifier_families.py','audit_quantifier_families.py','family_router_cases.py')})
    (DOC/'family-router-audit-001.json').write_bytes(V.W.P(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
