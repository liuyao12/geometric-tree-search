"""Reconstruct request decisions, all fallback trees and observed-time updates."""
import copy,gzip,hashlib,json,statistics,time
from pathlib import Path
import check_proposal_gate as V
import audit_quantifier_families as Old
from proposal_gate_cases import registry
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
LANES=('base','always','gate','zero_gate','eager_zero')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def semantic(r):
    keys=('status','placements','tile_generations','proof','endpoint','candidate_universe','search_tree','hints','solution_hints','policy_events','gate_events','gate_weights')
    return dict(**{k:r[k] for k in keys},metrics={k:v for k,v in r['metrics'].items() if not k.endswith('seconds')})
def original_tree(t):
    return {k:([{a:(original_tree(b) if a=='tree' else b) for a,b in child.items()} for child in value]
        if k=='children' else value) for k,value in t.items() if k!='gate_event'}
def first(t,p):
    if p(t):return t
    for child in t.get('children',()):
        found=first(child['tree'],p)
        if found is not None:return found
def audit(data):
    began=time.perf_counter();ds,ts,es=registry();known={};checks=[]
    V.N(V.F([d['spec'] for d in data['donors']])==V.F(ds),'statement-only fresh donors')
    for i,d in enumerate(data['donors']):
        rules,spec=Old.grammar(d);checks.append(V.result(rules,spec,known,d['result']))
        expected=Old.learn(d,known,6 if i==2 else 5);actual=[t for t in data['library'] if t['source']['spec']['id']==d['spec']['id']]
        V.N(len(actual)==len(expected),'all and only actual source windows')
        for t,w in zip(actual,expected):
            V.N(V.F({k:t[k] for k in ('name','pattern','children','level')})==V.F({k:w[k] for k in ('name','pattern','children','level')}),'independent typed family and strict child reconstruction')
            source=t['source'];V.N(V.F(source['members'])==V.F(w['members']),'actual source window')
            V.N(V.V.digest(source['result'])==V.V.digest(d['result']) and V.F(source['spec'])==V.F(d['spec']) and V.F(source['catalog'])==V.F(d['catalog']),'source search and original theory binding')
            V.N(V.F(source['check'])==V.F(d['result']['point_check']),'original source point/proof check');known[t['name']]=t
    V.N(len(known)==len(data['library']) and V.F(data['training']['specs'])==V.F(ts),'declared learned inventory and training inputs')
    weights=[0.]*8;baseline=0.;draws=0
    V.N(data['training']['initial_weights']==weights and tuple(data['training']['features'])==V.FEATURES and len(data['training']['episodes'])==64,'fresh zero gate and sixty-four episodes')
    for i,e in enumerate(data['training']['episodes']):
        V.N(V.F(e['spec'])==V.F(ts[i%len(ts)]),'declared on-policy input');rules,spec=Old.grammar(e)
        V.V.close(weights,e['weights_before']);V.V.close(weights,e['result']['gate_weights'])
        V.N(e['result']['mode']=='gated' and e['result']['stochastic'] and e['result']['seed']==14300+i,'fresh sampled gate')
        checks.append(V.result(rules,spec,known,e['result']));weights,baseline=V.update(weights,baseline,e['result'],e['update'])
        V.N(baseline==e['baseline_after'],'same observed-time baseline');draws+=len(e['result']['gate_events'])
    V.V.close(weights,data['training']['weights']);V.N(baseline==data['training']['baseline'],'frozen gate policy')
    V.N(len(data['cases'])==len(es),'complete evaluation corpus');repeats=0;positive=0;equivalent=0;classical=0
    for i,(c,s) in enumerate(zip(data['cases'],es)):
        V.N(V.F(c['spec'])==V.F(s) and s['id'] not in {t['id'] for t in ts},'evaluation statements and symbols outside training')
        V.N(set(c['runs'])==set(LANES),'all five matched controls');rules,spec=Old.grammar(c);statuses=set()
        for name,r in c['runs'].items():
            expected_mode={'base':'base','always':'fixed','gate':'gated','zero_gate':'gated','eager_zero':'policy'}[name]
            V.N(r['mode']==expected_mode and not r['stochastic'],'declared deterministic evaluation lane')
            if name=='gate':V.V.close(weights,r['gate_weights'])
            elif name=='zero_gate':V.V.close([0.]*8,r['gate_weights'])
            elif name=='eager_zero':V.V.close([0.]*5,r['weights'])
            checks.append(V.result(rules,spec,known,r));statuses.add(r['status']);positive+=r['proof'] is not None
            pin=V.V.digest(semantic(r));V.N(pin==r['semantic_sha256'],'complete retained semantic tree digest')
            timing=c['timings'][name];samples=timing['samples'];V.N(len(samples)==4,'four independent cold observations')
            for j,a in enumerate(samples):
                offset=(i+j)%5;V.N(tuple(a['order'])==LANES[offset:]+LANES[:offset] and a['repetition']==j,'rotating five-lane order')
                V.N(a['semantic_sha256']==pin and a['seconds']>=a['grammar_seconds']+a['search_seconds']+a['positive_check_seconds']>=0,'inclusive clocks and exact repeat binding')
                V.N(0<=a['gate_seconds']<=a['search_seconds'] and 0<=a['index_build_seconds']<=a['search_seconds'],'policy and construction charged');repeats+=1
            values=[a['seconds'] for a in samples];V.N(timing['median_seconds']==statistics.median(values) and timing['min_seconds']==min(values) and timing['max_seconds']==max(values),'literal cold clocks')
        V.N(len(statuses)==1,'same original boundaries and verified outcome')
        base,off=c['runs']['base'],c['runs']['zero_gate']
        V.N(V.F(original_tree(off['search_tree']))==V.F(base['search_tree']) and V.F(off['placements'])==V.F(base['placements']),'entire defer-only tree equals base')
        V.N(off['index'] is None and not off['hints'] and not off['metrics'].get('gate_queries',0),'defer never constructs proposals or syntax tables');equivalent+=1
        for control in c['controls'].values():
            if control['proof'] is not None:
                V.A.A.proof(control['proof'],s['target'],s['hypotheses'],s['theory'])
                V.N(control['fits_region_bound']==(len(control['proof'])<=s['bound']),'classical bound scope')
                if control['fits_region_bound']:
                    cert=control['region_certificate'];V.A.certificate(rules,s,cert,cert['tiles']);V.W.certificate(s,cert);classical+=1
        print(s['id'],'complete tree, request gates and joins replayed',flush=True)
    rejected=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,IndexError,TypeError):rejected.append(name)
        else:raise ValueError('accepted corrupted '+name)
    e=data['training']['episodes'][0];rules,spec=Old.grammar(e)
    for field,value in [('features',[0.]*8),('score',99.),('probabilities',[1.,0.]),('draw',-1.),('selected',3),('gradient',[99.]*8),('point',[999,0])]:
        bad=copy.deepcopy(e['result']);bad['gate_events'][0][field]=value
        reject('gate-'+field,lambda bad=bad:V.result(rules,spec,known,bad))
    bad=copy.deepcopy(e['result']);del first(bad['search_tree'],lambda t:'gate_event' in t)['gate_event']
    reject('missing-gate',lambda:V.result(rules,spec,known,bad))
    sample=data['cases'][0];rr,ss=Old.grammar(sample);bad=copy.deepcopy(sample['runs']['zero_gate'])
    first(bad['search_tree'],lambda t:'gate_event' in t)['proposal_pool']=[]
    reject('hidden-query-on-defer',lambda:V.result(rr,ss,known,bad))
    for field in ('reward','observed_total_seconds','gradient'):
        u=copy.deepcopy(e['update']);u[field]=[99.]*8 if field=='gradient' else u[field]+1
        reject('update-'+field,lambda u=u:V.update(e['weights_before'],e['update']['baseline_before'],e['result'],u))
    bad=copy.deepcopy(sample['runs']['always']);first(bad['search_tree'],lambda t:bool(t.get('proposal_pool')))['proposal_pool'].pop()
    reject('full-pool',lambda:V.result(rr,ss,known,bad))
    bad=copy.deepcopy(sample['runs']['zero_gate']);bad['search_tree']['children'][0]['key'][1]=999999
    reject('base-fallback',lambda:V.result(rr,ss,known,bad))
    bad=copy.deepcopy(sample['runs']['always']);bad['tiles'][0]['marks'][0][1]='!'
    reject('point-value',lambda:V.result(rr,ss,known,bad))
    return dict(status='passed',searches=len(checks),independent_states=sum(c['nodes'] for c in checks),index_queries=sum(c['index_queries'] for c in checks),
        request_decisions=sum(c.get('gate_decisions',0) for c in checks),on_policy_draws=draws,templates=len(known),levels=sorted({t['level'] for t in known.values()}),
        evaluation_positive_certificates=positive,whole_base_tree_equivalences=equivalent,classical_region_certificates=classical,repeated_cold_summaries=repeats,mutations_rejected=rejected,seconds=time.perf_counter()-began,
        scope='Full primary original-domain trees, all request features/actions/gradients and conditional exact joins, source hierarchy, proof kernels and recorded inclusive-time update algebra. Four repeat summaries are digest-bound, not full independently replayed repeat trees. Clocks and classical negative/unknown traces are not independently reconstructed.')
def main():
    path=DOC/'proposal-gate-001.json.gz';data=json.loads(gzip.decompress(path.read_bytes()))
    for n,pin in data['sources'].items():V.N(sha(HERE/n)==pin,'frozen measured source '+n)
    out=audit(data);out.update(version='proposal-gate-audit-001',input_sha256=sha(path),source_sha256=sha(__file__),helpers={n:sha(HERE/n) for n in ('check_proposal_gate.py','check_quantifier_families.py','audit_quantifier_families.py','check_movable_regions.py','check_adaptive_clusters.py','check_resumable_clusters.py','proposal_gate_cases.py')})
    (DOC/'proposal-gate-audit-001.json').write_bytes(V.W.P(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
