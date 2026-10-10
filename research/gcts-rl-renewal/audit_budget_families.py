"""Replay all primary discovery/training/evaluation trees and primitive proofs."""
import collections,copy,hashlib,itertools,json,statistics,time
from pathlib import Path
import check_budget_families as V
from budget_family_artifact import load
from budget_family_cases import registry
from serialized_kernel import canonical,check,problem_hash
from audit_serialized_kernel import replay as primitive

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
LANES=['budget','families','rl','zero','occupied'];LIMITS=dict(attempts=10000,seconds=60,proposal_limit=32)
HEURISTIC=[0.,0.,2.,1.,2.,0.,0.,0.,0.,0.,0.,0.]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def semantic(c,r,cert):
    fields=('status','placements','tile_generations','proof','endpoint','candidate_universe',
        'search_tree','hints','solution_hints','policy_events','attention_support','weights',
        'stochastic','seed','mode','feature_mode','limits','tiles','root_marks')
    index=r['index']
    return dict(spec=c['spec'],catalog=c['catalog'],certificate={k:v for k,v in cert.items() if k!='seconds'},
        result={k:r[k] for k in fields},metrics={k:v for k,v in r['metrics'].items() if not k.endswith('seconds')},
        graph_metrics=r['graph_metrics'],index={k:v for k,v in index.items() if k!='build_seconds'} if index else None)

def run(c,r,cert,templates):
    rules,forms=V.A.A.inventory(c['spec'])
    V.N(V.F(rules)==V.F(c['catalog']['rules']) and V.F(forms)==V.F(c['catalog']['formulas']),'complete original statement grammar')
    required=V.D.certificate(rules,c['spec'],cert)
    V.N(r['limits']==LIMITS,'matched original placement/wall/proposal limits')
    checked=V.result(rules,dict(c['spec'],_formulas=forms),templates,r,required)
    best=()
    def selection(node,chosen):
        nonlocal best
        if node.get('cutoff')=='entry_wall':return
        if node['kind']!='dead' and len(chosen)>len(best):best=chosen
        for child in node['children']:selection(child['tree'],chosen+(V.F(child['key']),))
    selection(r['search_tree'],())
    if r['proof'] is None:
        V.N(V.F(r['placements'])==best and r['endpoint'] is None,'actual deepest nondead partial prefix, no invented completion')
    V.N(len(r['tile_generations'])==len(r['placements']) and V.F(r['tiles'])==tuple(V.D.tile(V.F(rules),c['spec'],k,required) for k in V.F(r['placements'])),'actual selected partial/complete tiles and generations')
    V.D.state(V.F(rules),c['spec'],r['placements'],required)
    h=len(c['spec']['hypotheses']);bound=c['spec']['bound']
    universe=bound+1+bound+int(bool(h))+sum(sum(1 for refs in itertools.product(range(-h,j),repeat=len(row['inputs']))
        if all(refs[a]!=refs[b] or row['inputs'][a]==row['inputs'][b] for a in range(len(refs)) for b in range(a)))
        for j in range(bound) for row in rules)
    V.N(r['candidate_universe']==universe,'unchanged complete original placement universe')
    V.N(r['semantic_sha256']==hashlib.sha256(canonical(semantic(c,r,cert))).hexdigest(),'entire retained semantic tree digest')
    V.N(r['total_seconds']>=r['preparation_seconds']+r['seconds']+r['positive_check_seconds']>=0 and
        r['preparation_seconds']>=r['synthesis_seconds']+r['certification_seconds']+r['library_load_seconds']+r['grammar_seconds']>=0,'inclusive observed cold clocks')
    checked['positive']=int(r['proof'] is not None)
    if checked['positive']:
        request=r['compact']['request'];payload=canonical(request);pin=problem_hash(request)
        V.N(check(payload,max_work=None,expected_problem_sha256=pin)['status']=='accepted' and primitive(payload,pin)['status']=='accepted','both independent primitive kernels')
    return checked

def audit(data):
    started=time.perf_counter();ds,ts,es=registry();total=collections.Counter();mutations=[];templates={}
    V.N(data['lanes']==LANES and data['limits']==LIMITS and data['repetitions']==5 and data['heuristic_weights']==HEURISTIC,'whole declared cold comparison')
    for i,(d,spec) in enumerate(zip(data['donors'],ds)):
        V.N(V.F(d['spec'])==V.F(spec),'donor statement-only input')
        r=d['result'];V.N(r['mode']==('base' if i==0 else 'policy') and r['weights']==(None if i==0 else HEURISTIC) and not r['stochastic'],'fresh donor search control')
        checked=run(d,r,d['certificate'],templates);total.update({k:checked.get(k,0) for k in ('nodes','index_queries','positive')});total['searches']+=1
        rows=sorted(k for k in V.F(r['placements']) if k[1]>=0);patterns={V.Q.V.digest(t['pattern']) for t in templates.values()};new=[]
        for first in range(len(rows)):
            for size in range(2,min(6,len(rows)-first)+1):
                members=tuple(rows[first:first+size]);pattern=V.Q.pattern_for(V.F(d['catalog']['rules']),members);pin=V.Q.V.digest(pattern)
                if pin in patterns:continue
                patterns.add(pin);new.append((members,pattern,pin))
        actual=[t for t in data['library'] if t['source']['spec']['id']==spec['id']]
        V.N(len(actual)==len(new),'every new mined donor window')
        for t,(members,pattern,pin) in zip(actual,new):
            source=t['source'];V.N(V.F(source['spec'])==V.F(spec) and V.F(source['catalog'])==V.F(d['catalog']) and V.F(source['result'])==V.F(r),'exact freshly searched inventory provenance')
            V.N(t['name']=='quantifier-family-'+pin[:20] and V.F(t['pattern'])==pattern and V.F(source['members'])==members,'independently abstracted typed receptor pattern')
            inside={k[0]:j for j,k in enumerate(members)};children=[]
            for done in r['solution_hints']:
                item=done['item'];parts=V.F(item['members'])
                if item['template'] in templates and set(parts)<set(members):
                    children.append(dict(template=item['template'],offsets=[inside[k[0]] for k in parts],hint_id=done['id'],kind='completed_ordering_hint'))
            V.N(t['children']==children and t['level']==1+max((templates[c['template']]['level'] for c in children),default=0),'every genuine promoted hierarchical child')
        templates.update((t['name'],t) for t in actual)
        print('donor',i,'full tree and all promoted windows passed',flush=True)
    V.N(len(templates)==len(data['library']) and len(data['donors'])==len(ds),'entire inventory and donor list')
    train=data['training'];V.N(V.F(train['specs'])==V.F(ts) and train['initial_weights']==[0.]*12 and train['epochs']==8 and train['rate']==2. and tuple(train['features'])==V.FEATURES,'whole zero-start training declaration')
    baselines={}
    for b,spec in zip(train['initial_baseline_runs'],ts):
        V.N(V.F(b['spec'])==V.F(spec) and b['result']['mode']=='base','training baseline input')
        checked=run(b,b['result'],b['certificate'],templates);total.update({k:checked.get(k,0) for k in ('nodes','index_queries','positive')});total['searches']+=1
        baselines[spec['id']]=V.Old.reward(b['result'])
    weights=[0.]*12
    for j,e in enumerate(train['episodes']):
        epoch=j//len(ts);order=list(range(len(ts)));off=epoch%len(ts);order=order[off:]+order[:off];index=order[j%len(ts)];spec=ts[index];r=e['result']
        V.N(e['epoch']==epoch and e['training_index']==index and V.F(e['spec'])==V.F(spec) and e['weights_before']==weights and r['weights']==weights and r['seed']==57100+j and r['stochastic'] and r['feature_mode']=='justified','exact on-policy episode and weights before observation')
        checked=run(e,r,e['certificate'],templates);total.update({k:checked.get(k,0) for k in ('nodes','index_queries','positive')});total['searches']+=1;total['policy_events']+=len(r['policy_events']);total['sampled_family_choices']+=sum(v['selected']!=0 for v in r['policy_events'])
        weights,baselines[spec['id']]=V.update(weights,baselines[spec['id']],r,e['update'])
        print('episode',j,'entire sampled tree and update passed',flush=True)
    V.N(len(train['episodes'])==8*len(ts) and weights==train['weights'] and baselines==train['baselines'],'all frozen parameters and previous-only baselines')
    cases=[];observations=0
    for i,(c,spec) in enumerate(zip(data['cases'],es)):
        V.N(V.F(c['spec'])==V.F(spec),'evaluation statement-only input')
        outcomes={}
        for lane in LANES:
            r=c['runs'][lane];expected=None if lane=='budget' else weights if lane=='rl' else [0.]*12 if lane=='zero' else HEURISTIC
            V.N(r['weights']==expected and not r['stochastic'] and r['seed']==0 and r['feature_mode']==('occupied' if lane=='occupied' else 'justified'),'frozen matched evaluation lane')
            checked=run(c,r,c['certificates'][lane],templates);total.update({k:checked.get(k,0) for k in ('nodes','index_queries','positive')});total['searches']+=1;outcomes[lane]=r['status']
            timing=c['timings'][lane];values=[]
            for rep,sample in enumerate(timing['samples']):
                off=(i+rep)%len(LANES);order=LANES[off:]+LANES[:off]
                V.N(sample['order']==order and sample['repetition']==rep and sample['semantic_sha256']==r['semantic_sha256'] and sample['status']==r['status'] and sample['attempts']==r['metrics']['attempts'],'balanced cold repeat bound to complete primary tree')
                V.N(sample['total_seconds']>=sample['preparation_seconds']+sample['seconds']+sample['positive_check_seconds']>=0 and sample['peak_process_rss_bytes']>0,'literal observed cold costs and process memory')
                values.append(sample['total_seconds']);observations+=1
            V.N(len(values)==5 and timing['median_seconds']==statistics.median(values) and timing['min_seconds']==min(values) and timing['max_seconds']==max(values),'actual timing summary algebra')
        for lane in ('zero',):
            base=c['runs']['budget'];r=c['runs'][lane]
            V.N(r['placements']==base['placements'] and r['metrics']['attempts']==base['metrics']['attempts'] and not r['hints'],'zero tie-defer preserves base placements and complete fallback')
        control=c['controls']['saturation']
        if control['proof'] is not None:
            V.A.A.proof(control['proof'],spec['target'],spec['hypotheses'],spec['theory']);V.N(control['fits_region_bound']==(len(control['proof'])<=spec['bound']),'saturation proof and boundary scope')
            if control['fits_region_bound']:w=control['region_certificate'];V.A.certificate(c['catalog']['rules'],spec,w,w['tiles'])
        cases.append(dict(id=spec['id'],outcomes=outcomes));print(spec['id'],'all five primary trees and repeats passed',flush=True)
        if i==0:
            def reject(label,fn):
                try:fn()
                except (ValueError,KeyError,TypeError,IndexError):mutations.append(label)
                else:raise ValueError('corruption accepted: '+label)
            for field in ('feature','score','gradient','census','fallback','query','budget-mark','root'):
                broken=copy.deepcopy(c['runs']['families'])
                if field=='feature':broken['policy_events'][0]['features'][0]=[1.]*12
                elif field=='score':broken['policy_events'][0]['scores'][0]+=1
                elif field=='gradient':broken['policy_events'][0]['gradient'][0]+=1
                elif field=='census':broken['search_tree']['census'][0][1]+=1
                elif field=='fallback':broken['search_tree']['children'][0]['key'][1]=999999
                elif field=='query':broken['index']['queries'].pop()
                elif field=='budget-mark':next(v for v in broken['tiles'][0]['marks'] if v[0][0]==-3000)[1]=1
                else:broken['root_marks'].pop()
                reject(field,lambda r=broken:V.result(V.F(c['catalog']['rules']),dict(spec,_formulas=c['catalog']['formulas']),templates,r,V.D.certificate(c['catalog']['rules'],spec,c['certificates']['families'])))
    V.N(len(cases)==len(es),'all evaluation goals')
    return dict(status='passed',**total,observations=observations,inventory_families=len(templates),inventory_levels=sorted(set(t['level'] for t in templates.values())),cases=cases,mutations_rejected=mutations,seconds=time.perf_counter()-started,
        scope='Every discovery, baseline, sampled training and primary evaluation tree: complete original grammar, every fixed-point round, literal distant domains and censuses, every typed family instance and matching query, full original fallback, hint lifetimes, justified-source feature closure, softmax draws and gradients, training algebra, actual cold repeat summaries, positive decorated/original point certificates and both primitive kernels. Repeated full worker trees remain private and digest-bound, not separately replayed. Physical clock authenticity and negative saturation closure are outside this audit.')

def main():
    path=DOC/'budget-families-001.json';data=load(path)
    for n,pin in data['sources'].items():V.N(sha(HERE/n)==pin,'measured source '+n)
    out=audit(data);out.update(version='budget-families-audit-001',input_sha256=sha(path),source_sha256=sha(__file__),helpers={n:sha(HERE/n) for n in ('check_budget_families.py','check_dependency_budget.py','check_quantifier_families.py','check_receptor_attention.py','check_movable_regions.py','check_quantified_receptors.py','audit_serialized_kernel.py','budget_family_artifact.py','receptor_attention_artifact.py')})
    (DOC/'budget-families-audit-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)

if __name__=='__main__':main()
