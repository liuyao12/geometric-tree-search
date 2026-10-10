"""Fresh matched graph representation controls and richer symbolic targets."""
import copy,hashlib,json,resource,time
from pathlib import Path
from types import SimpleNamespace
import factored_receptors as F
import propositional_receptors as R
import check_propositional_receptors as A
import check_factored_receptors as C
import propositional_wang_compiler as W
from serialized_kernel import canonical
from audit_semantic_proofs import whole_replay

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def pin(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inspect(m,r,rules):
    if r['proof'] is None:return
    t=time.perf_counter();tiles=[dict(key=k,occupancy=m.placement(k).occupancy,marks=m.placement(k).marks) for k in r['placements']]
    r['point_tiles']=tiles;r['independent']=C.certificate(rules,m.target,m.length,m.hypotheses,r['placements'],tiles)
    r['proof_check_seconds']=time.perf_counter()-t;r['primitive_lines']=r['independent']['primitive_lines']
def frames(m,r):
    s=m.initial();g=F.Graph(m,s);out=[]
    for key in r['placements']:
        kind,p,_=g.decision(s)
        out.append(dict(kind=kind,point=p,key=key,placed=list(s.order),domains=[dict(point=q,count=d.count,blocks=d.blocks) for q,d in sorted(g.domains.items())]))
        g.update(m,s,s.place(m.placement(key)))
    return out
def main():
    began=time.perf_counter();sources=('factored_receptors.py','check_factored_receptors.py','run_factored_receptors.py','test_factored_receptors.py','propositional_receptors.py','turtle.py','propositional_wang_compiler.py')
    pins={n:pin(HERE/n) for n in sources};prior=json.loads((DOC/'propositional-receptors-001.json').read_text())
    weights=prior['training']['weights'];data=dict(version='factored-receptors-001',sources=pins,reused_policy_artifact_sha256=pin(DOC/'propositional-receptors-001.json'),
        reused_policy_training_seconds=prior['rl_total_training_seconds'],authored_proofs=[],cases=[],ground_candidate_cap=50000)
    p,q=R.P,R.Q;n=R.neg;i=R.imp
    specs=[dict(id='plain-identity',title='Identity: matched old point model',mode='plain',target=i(p,p),length=5,hypotheses=(),family=False),
        dict(id='plain-exhausted',title='Closed atom: complete one-slot exhaustion',mode='plain',target=p,length=1,hypotheses=(),family=False),
        dict(id='double-negation-premise',title='Remove double negations from an implication premise',mode='negated',target=i(p,q),length=4,hypotheses=(i(n(n(p)),n(n(q))),),family=False),
        dict(id='negated-identity',title='Negated identity: broader primitive envelope',mode='negated',target=i(n(p),n(p)),length=5,hypotheses=(),family=False),
        dict(id='negated-family',title='Newly discovered identity family on a negation',mode='negated',target=i(n(p),n(p)),length=1,hypotheses=(),family=True),
        dict(id='negated-family-weakening',title='Compose the family with weakening',mode='negated',target=i(n(p),i(q,q)),length=3,hypotheses=(),family=True)]
    family=None
    for spec in specs:
        t=time.perf_counter();u=F.Universe(spec['mode'],family if spec['family'] else None);build=time.perf_counter()-t
        params,rules=C.inventory(spec['mode'],family if spec['family'] else None)
        if list(u.rules)!=rules:raise ValueError('full independently reconstructed inventory')
        case=dict(spec,pool=u.pool,rules=len(u.rules),implications=len(u.implications),inventory_sha256=hashlib.sha256(canonical(rules)).hexdigest(),
            universe_build_seconds=build,candidate_universe=u.cardinality(spec['length'],spec['hypotheses']),runs={})
        for lane,w in (('factored',None),('factored-rl',weights)):
            t=time.perf_counter();m=F.Model(u,spec['target'],spec['length'],spec['hypotheses']);model_build=time.perf_counter()-t
            r=F.search(m,node_limit=6000,seconds=6,policy_weights=w);r['build_seconds']=build+model_build;inspect(m,r,rules)
            if r['proof'] is not None and lane=='factored':case['frames']=frames(m,r)
            case['runs'][lane]=r
        if case['candidate_universe']<=data['ground_candidate_cap']:
            t=time.perf_counter();gm=R.Model(dict(rules=rules),spec['target'],spec['length'],spec['hypotheses']);gb=time.perf_counter()-t
            gr=R.search(gm,node_limit=6000,seconds=12);gr['build_seconds']=gb;inspect(gm,gr,rules);case['runs']['ground']=gr
            if A.frozen(gr['search_tree'])!=A.frozen(case['runs']['factored']['search_tree']):raise ValueError('matched ordinary search tree changed')
        else:case['runs']['ground']=dict(status='not_run_declared_candidate_cap',candidate_cap=data['ground_candidate_cap'],scope='No memory failure or relative speed claim is inferred from this resource gate.')
        descriptor=SimpleNamespace(catalog=dict(rules=rules),target=spec['target'],length=spec['length'],hypotheses=spec['hypotheses'])
        case['runs']['chronological']=R.chronological(descriptor,node_limit=6000,seconds=6)
        case['runs']['saturation']=R.forward(dict(rules=rules),spec['target'],spec['hypotheses'])
        for lane in ('chronological','saturation'):
            r=case['runs'][lane]
            if r['proof'] is not None:
                check=A.logical(r['proof'],spec['target'],spec['hypotheses']);r['primitive_lines']=check['primitive_lines'];r['fits_slot_bound']=len(r['proof'])<=spec['length']
        if spec['id']=='plain-identity':
            family=R.family_from_discovery(case['runs']['factored']['proof']);data['discovered_family']=family
        if spec['id']=='double-negation-premise':
            r=case['runs']['factored'];t=time.perf_counter();compiled=W.compile_request(r['proof'],spec['target'],spec['hypotheses']);case['compiled']=compiled
            case['syntax_compiler_seconds']=time.perf_counter()-t;case['independent_kernel']=whole_replay(compiled['request'],compiled['statement_pin'])
        data['cases'].append(case)
        print(spec['id'],[(k,v['status'],round(v.get('seconds',0),4)) for k,v in case['runs'].items()],flush=True)
        (Path('/private/tmp')/'gcts-factored-receptors-progress.json').write_bytes(canonical(data)+b'\n')
    data['seconds']=time.perf_counter()-began;data['peak_process_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if any(pin(HERE/n)!=p for n,p in pins.items()):raise ValueError('measured source changed')
    (DOC/'factored-receptors-001.json').write_bytes(canonical(data)+b'\n');print('complete',data['seconds'],flush=True)
if __name__=='__main__':main()
