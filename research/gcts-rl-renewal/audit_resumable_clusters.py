"""Audit fresh sources, all joins/trees, resumed hierarchy and policy updates."""
import copy,hashlib,json,time
from pathlib import Path
import check_resumable_clusters as V
from resumable_cases import registry

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(data):
    began=time.perf_counter();ds,ts,es=registry();checks=[];known={};donors={V.V.digest(d['result']):d for d in data['donors']}
    V.N(V.F([d['spec'] for d in data['donors']])==V.F(ds),'fresh declarative donor registry')
    for d in data['donors']:
        rules,forms=V.A.A.inventory(d['spec']);V.N(V.F(rules)==V.F(d['catalog']['rules']) and V.F(forms)==V.F(d['catalog']['formulas']),'whole donor grammar')
        checks.append(V.result(rules,d['spec'],known,d['result']))
        for t in data['library']:
            if t['source']['spec']['id']!=d['spec']['id']:continue
            source=t['source'];pin=V.V.digest(source['result']);V.N(pin in donors and V.F(source['result'])==V.F(d['result']),'actual fresh discovery')
            V.N(V.F(source['spec'])==V.F(d['spec']) and V.F(source['catalog'])==V.F(d['catalog']),'full donor binding')
            members=V.F(source['members']);proof=sorted((V.F(k) for k in d['result']['placements'] if k[1]>=0),key=lambda k:k[0])
            V.N(any(proof[i:i+len(members)]==list(members) for i in range(len(proof))),'actual proof window')
            pattern=V.V.pattern_for(V.F(rules),members);V.N(V.F(t['pattern'])==pattern and t['name']=='receptor-cluster-'+V.V.digest(pattern)[:20],'whole learned abstraction')
            inside={k[0]:i for i,k in enumerate(members)};children=[]
            for done in d['result']['solution_hints']:
                item=done['item'];parts=V.F(item['members'])
                if item['template'] in known and set(parts)<=set(members):
                    children.append(dict(template=item['template'],offsets=[inside[k[0]] for k in parts],hint_id=done['id'],kind='completed_ordering_hint'))
            V.N(V.F(t['children'])==V.F(children),'only actually completed children')
            V.N(t['level']==1+max((known[c['template']]['level'] for c in children),default=0),'acyclic learned hierarchy')
            known[t['name']]=t
    V.N(len(known)==len(data['library']) and V.F(data['training']['specs'])==V.F(ts),'complete library and training registry')
    weights=[0.]*5;baseline=0.;draws=0
    for i,episode in enumerate(data['training']['episodes']):
        spec=ts[i%len(ts)];V.N(V.F(episode['spec'])==V.F(spec),'declared training task');V.V.close(weights,episode['weights_before'])
        rules,forms=V.A.A.inventory(spec);V.N(V.F(rules)==V.F(episode['catalog']['rules']) and V.F(forms)==V.F(episode['catalog']['formulas']),'whole training grammar')
        V.V.close(weights,episode['result']['weights']);V.N(episode['result']['stochastic'] and episode['result']['seed']==7800+i,'fresh on-policy episode')
        checks.append(V.result(rules,spec,known,episode['result']));weights,baseline=V.update(weights,baseline,episode['result'],episode['update'])
        V.N(abs(baseline-episode['baseline_after'])<1e-12,'moving reward baseline');draws+=len(episode['result']['policy_events'])
    V.V.close(weights,data['training']['weights']);V.N(baseline==data['training']['baseline'],'frozen final controller')
    completed=0;positives=0;controls=0
    V.N(len(data['cases'])==len(es),'all held-out cases')
    for c,spec in zip(data['cases'],es):
        V.N(V.F(c['spec'])==V.F(spec) and spec['id'] not in {s['id'] for s in ts},'held-out external registry')
        rules,forms=V.A.A.inventory(spec);V.N(V.F(rules)==V.F(c['catalog']['rules']) and V.F(forms)==V.F(c['catalog']['formulas']),'complete evaluation grammar')
        statuses=set()
        for lane,r in c['runs'].items():
            if lane=='rl':V.V.close(weights,r['weights'])
            elif lane=='zero':V.V.close([0.]*5,r['weights'])
            elif lane=='atomic':V.V.close(V.FIXED,r['weights'])
            checks.append(V.result(rules,spec,known,r,lane=='atomic'));statuses.add(r['status'])
            completed+=len(r.get('solution_hints',()));positives+=r['proof'] is not None
        V.N(len(statuses)==1,'same bounded point result in every lane')
        for name,r in c['controls'].items():
            if r['proof'] is None:continue
            V.A.A.proof(r['proof'],spec['target'],spec['hypotheses'],spec['theory'])
            V.N(r['fits_region_bound']==(len(r['proof'])<=spec['bound']),'classical control proof horizon')
            if r['fits_region_bound']:
                region=r['region_certificate'];V.N(V.F(region['proof'])==V.F(r['proof']),'control certificate bound to same proof')
                V.A.certificate(rules,spec,region,region['tiles']);V.certificate(spec,region);controls+=1
        print(spec['id'],'audited',flush=True)
    sample=next(c for c in data['cases'] if c['spec']['id']=='resume-held-long');mutations=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,IndexError,TypeError):mutations.append(name)
        else:raise ValueError('accepted mutation '+name)
    def first(tree,test):
        if test(tree):return tree
        for ch in tree.get('children',()):
            got=first(ch['tree'],test)
            if got:return got
        return None
    for name in ('phase','pending','hint-id','hint-aggregate','pool','fallback','target','point','child-role'):
        bad=copy.deepcopy(sample['runs']['fixed']);tree=bad['search_tree']
        if name=='phase':first(tree,lambda t:t.get('review',{}).get('phase')=='resumed')['review']['phase']='suspended'
        elif name=='pending':first(tree,lambda t:bool(t.get('review',{}).get('pending')))['review']['pending']=[]
        elif name=='hint-id':first(tree,lambda t:t.get('hint_in') is not None)['hint_in']=99999
        elif name=='hint-aggregate':bad['hints'][0]['item']['occupancy'][0][1]=11
        elif name=='pool':first(tree,lambda t:bool(t.get('proposal_pool')))['proposal_pool'].pop()
        elif name=='fallback':tree['children'][0]['key'][1]=99999
        elif name=='target':bad['compact']['request']['target']=['bot']
        elif name=='point':bad['tiles'][0]['marks'][0][1]='!'
        else:tree['children'][0]['role']='base'
        reject(name,lambda b=bad:V.result(sample['catalog']['rules'],sample['spec'],known,b))
    for name in ('draw','gradient','reward','scans'):
        episode=copy.deepcopy(data['training']['episodes'][0]);r=episode['result']
        if name=='draw':r['policy_events'][0]['draw']=.00000001
        elif name=='gradient':r['policy_events'][0]['gradient'][0]+=1
        elif name=='reward':episode['update']['reward']+=1
        else:r['metrics']['proposal_scanned']+=1
        if name=='reward':reject(name,lambda e=episode:V.update(e['weights_before'],e['update']['baseline_before'],e['result'],e['update']))
        else:reject(name,lambda e=episode:V.result(e['catalog']['rules'],e['spec'],known,e['result']))
    return dict(status='passed',searches=len(checks),independent_states=sum(c['nodes'] for c in checks),
        templates=len(known),levels=sorted({t['level'] for t in known.values()}),on_policy_draws=draws,
        evaluation_positive_certificates=positives,evaluation_completed_families=completed,classical_region_certificates=controls,
        mutations_rejected=mutations,seconds=time.perf_counter()-began,
        scope='Every base domain/tree, complete declared finite proposal pool, pending set, phase, expiry, original candidate fallback, source/child provenance and policy update is independently reconstructed. '
              'Positive classical controls are bound to exact regions; their negative/unknown search traces are not independently reconstructed.')
def main():
    path=DOC/'resumable-clusters-001.json';data=json.loads(path.read_bytes())
    for n,pin in data['sources'].items():V.N(digest(HERE/n)==pin,'frozen measured source '+n)
    out=audit(data);out.update(version='resumable-clusters-audit-001',input_sha256=digest(path),source_sha256=digest(__file__),
        helpers={n:digest(HERE/n) for n in ('check_resumable_clusters.py','check_adaptive_clusters.py','check_movable_regions.py','check_compact_contexts.py','resumable_cases.py')})
    (DOC/'resumable-clusters-audit-001.json').write_bytes(V.P(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
