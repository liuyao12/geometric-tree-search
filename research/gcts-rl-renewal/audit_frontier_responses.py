"""Literal saved-path/domain checks and independent policy-update algebra.

Does not import the new solver, its feature routines or its experiment driver.
Explored abandoned branches are not a serialized exhaustive proof tree.
"""
import copy,hashlib,json,math,resource,time
from collections import Counter,defaultdict
from pathlib import Path
from region_tiles import Boundary
from audit_boundary_macros import Oracle,exact_key
from audit_boundary_responses import certify,domains,matched_execution,normal
from audit_geometry import audit as geometry_audit
from turtle import VERTICES

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
MODES=('base','small','hierarchy')

def literal_prefix(oracle,b,placements):
    totals=dict(b.exterior);owned=set(b.owned);gens={p:0 for p,v in b.exterior};gens.update({p:0 for p in b.required})
    for raw in placements:
        k=exact_key(raw);occ=oracle.values[k]
        if (k[1],k[2]) in owned or any(totals.get(p,0)+v>12 for p,v in occ):raise ValueError('illegal sampled prefix')
        incident=[gens[p] for p,v in occ if p in gens];gen=1+min(incident) if incident else 0
        for p,v in occ:totals[p]=totals.get(p,0)+v;gens[p]=min(gens.get(p,gen),gen)
        owned.add((k[1],k[2]))
    return totals,owned,gens

def check_sample(sample,b,oracle,weights=None):
    totals,owned,gens=literal_prefix(oracle,b,sample['placements']);ds=domains(oracle,b,totals,owned)
    if not ds or any(not x for x in ds.values()):return False
    forced=sorted(p for p,x in ds.items() if len(x)==1)
    p=forced[0] if forced else min(ds,key=lambda p:(gens[p],len(ds[p]),p))
    keys=[exact_key(x) for x in sample['domain']];order=[exact_key(x) for x in sample['ordered']]
    if forced or sample['kind']!='branch' or tuple(sample['point'])!=p:return False
    if set(keys)!=ds[p] or len(keys)!=len(ds[p]) or len(order)!=len(set(order)) or set(order)!=set(keys):return False
    if sample['duplicates']!=sample['offered_actions']-len(keys) or sample['duplicates']<0:return False
    feedback={(m,k):v for m,k,v in sample['feedback']};degrees=list(map(len,ds.values()));fs=[]
    for m in MODES:
        values={'bias':1.,'remaining':1-sum(totals.get(p,0)==12 for p in b.required)/len(b.required),
                'domain':len(keys)/50,'mean_degree':sum(degrees)/len(degrees)/50,
                'low_degree':sum(d<=2 for d in degrees)/len(degrees),'frontier':len(ds)/300,
                'accepted':len(sample['placements'])/100,'contact':sum(totals.get(p,0)>0 for p in ds)/len(ds),
                'interruption':feedback.get((m,'interrupted'),0)/max(1,feedback.get((m,'closed'),0))}
        if not 0<=values['interruption']<=1:return False
        fs.append({'mode:'+m+':'+k:v for k,v in values.items()})
    if fs!=sample['mode_features'] or sample['mode'] not in MODES:return False
    if weights is not None:
        scores=[sum(weights.get(k,0)*v for k,v in f.items()) for f in fs]
        if scores[MODES.index(sample['mode'])]!=max(scores):return False
    return True

def reconstruct_updates(training):
    if training['initial_weights'] or training['initial_marking'] or training['policy_imported']:raise ValueError('not a fresh policy')
    w=defaultdict(float);baseline=0.;choices=0
    for r in training['episodes']:
        traces=[]
        for choice in r['learning_choices']:
            fs=choice['features'];i=choice['selected']
            if type(i) is not int or not 0<=i<len(fs) or choice['kind'] not in ('mode','move'):raise ValueError('bad choice')
            prefix=choice['kind']+':'
            if any(not k.startswith(prefix) or not math.isfinite(v) for f in fs for k,v in f.items()):raise ValueError('bad feature')
            scores=[sum(w[k]*v for k,v in f.items()) for f in fs];top=max(scores);ps=[math.exp(s-top) for s in scores]
            ps=[p/sum(ps) for p in ps];expected=defaultdict(float)
            for p,f in zip(ps,fs):
                for k,v in f.items():expected[k]+=p*v
            traces.append({k:fs[i].get(k,0)-expected[k] for k in fs[i].keys()|expected.keys()});choices+=1
        reward=r['reward'];elapsed=(r['coverage_fraction']+(1 if r['status']=='finite_exact_region' else -1)-.001*r['attempted_base_placements']-reward)/.01
        if not 0<=elapsed<=r['seconds']+.000001 or r['seconds']-elapsed>.1:raise ValueError('reward binding')
        advantage=reward-baseline;baseline=.9*baseline+.1*reward
        for g in traces:
            for k,v in g.items():w[k]+=.03*advantage*v/max(1,len(traces))
    if training['updates']!=len(training['episodes']) or abs(baseline-training['baseline'])>1e-12:raise ValueError('update count or baseline')
    if any(abs(w[k]-training['weights'].get(k,0))>1e-12 for k in w.keys()|training['weights'].keys()):raise ValueError('weights mismatch')
    return choices

def main():
    start=time.monotonic();path=DOCS/'frontier-responses-001.json';d=json.loads(path.read_text())
    for n,sha in d['sources'].items():assert hashlib.sha256((HERE/n).read_bytes()).hexdigest()==sha
    raw=(DOCS/d['source_artifact']).read_bytes();assert hashlib.sha256(raw).hexdigest()==d['source_sha256'];parent=json.loads(raw)
    assert d['problems']==parent['problems']
    # Authored training declarations are also independently bound to the
    # earlier request-resolution artifact. Its policy is never imported.
    prior_path=DOCS/'response-resolution-001.json';prior=json.loads(prior_path.read_text())
    assert d['training_problems']==prior['training_problems']
    bs={b.identity:b for b in map(Boundary.unpack,d['problems']+d['training_problems'])}
    oracle=Oracle(next(iter(bs.values())).allowed);assert len(oracle.values)==d['inventory']['placements']
    nodes,maps=certify(parent['library']);states=moves=samples=complete=matched=0;patches=[]
    def replay(r):
        nonlocal states,moves,samples,complete,matched
        b=bs[r['problem']];assert oracle.replay(r,b),'saved literal schedule or values disagree'
        assert matched_execution(r,b,oracle,parent['library'],True),'response input or suffix disagree'
        states+=1;moves+=len(r['execution']);matched+=1;complete+=r['status']=='finite_exact_region'
        for s in r.get('decision_samples',[]):
            assert check_sample(s,b,oracle,d['training']['weights'] if r.get('lane')=='frontier-RL' else None),'sampled full domain or features disagree'
            samples+=1
        if r.get('lane') and r['status']=='finite_exact_region':patches.append({'lane':r['lane']+'/'+b.identity,'seed':r['seed'],'placements':r['state']['base_expansion']})
    for r in d['training']['episodes']+d['evaluation']:replay(r)
    controls=0
    for c in d['controls']:
        a,b=c['results'];assert all(a[f]==b[f] for f in c['fields']);controls+=1
        for r in c['results']:replay(dict(r,problem=c['problem']))
    choices=reconstruct_updates(d['training']);assert d['training']['updates']==48
    assert len(d['evaluation'])==84 and len({(r['problem'],r['replica'],r['lane']) for r in d['evaluation']})==84
    assert set(r['seed'] for r in d['training']['episodes']).isdisjoint(r['seed'] for r in d['evaluation'])
    rejected=0;r=next(r for r in d['evaluation'] if r['execution']);b=bs[r['problem']]
    for mutation in ('point','key','generation','total','response','offset'):
        bad=copy.deepcopy(r)
        if mutation=='point':bad['execution'][0]['point']=[90,-45,-45]
        elif mutation=='key':bad['execution'][0]['placement'][1]=12
        elif mutation=='generation':bad['state']['tile_generations'][0]+=1
        elif mutation=='total':bad['state']['totals'][0][1]+=1
        elif mutation=='response':bad['execution'][0]['response']='unknown-response'
        else:bad['execution'][0]['proposal_offset']=100
        try:okay=oracle.replay(bad,b) and matched_execution(bad,b,oracle,parent['library'],True)
        except (ValueError,KeyError,IndexError):okay=False
        assert not okay;rejected+=1
    r=next(r for r in d['evaluation'] if r.get('decision_samples'));s=r['decision_samples'][0];b=bs[r['problem']]
    for mutation in ('omit','duplicate','feature','point'):
        bad=copy.deepcopy(s)
        if mutation=='omit':bad['ordered'].pop()
        elif mutation=='duplicate':bad['ordered'].append(bad['ordered'][0])
        elif mutation=='feature':bad['mode_features'][0]['mode:base:remaining']+=.1
        else:bad['point']=[90,-45,-45]
        assert not check_sample(bad,b,oracle);rejected+=1
    bad=copy.deepcopy(d['training']);key=next(iter(bad['weights']));bad['weights'][key]+=.1
    try:reconstruct_updates(bad);raise AssertionError('changed learned weights accepted')
    except ValueError:rejected+=1
    geometry=geometry_audit({'point_model':{'vertices':VERTICES},'pair_catalog':{'samples':[]},'evaluation':patches})
    d['independent_audit']={'states':states,'complete_states':complete,'scheduled_moves':moves,'matched_paths':matched,
        'sampled_complete_domains':samples,'equal_path_controls':controls,'policy_updates':48,'policy_choices':choices,
        'literal_inventory':len(oracle.values),'response_nodes':len(nodes),'response_child_maps':maps,'tampered_records_rejected':rejected,
        'geometry':geometry,'seconds':time.monotonic()-start,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'helper_sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('audit_boundary_macros.py','audit_boundary_responses.py','audit_geometry.py','region_tiles.py','turtle.py')},
        'training_declaration_artifact_sha256':hashlib.sha256(prior_path.read_bytes()).hexdigest(),
        'scope':'saved successful/best paths, sampled complete parent domains and update algebra; not an independent replay of every abandoned branch or exhaustive negative tree; no plane proof'}
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in d['independent_audit'].items() if k not in ('geometry','helper_sources')},indent=2),flush=True)

if __name__=='__main__':main()
