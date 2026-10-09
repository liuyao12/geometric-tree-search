"""Two-level scalar exclusions and fixed-boundary dead-prefix replay."""
import copy,dataclasses,hashlib,json,resource,time
from pathlib import Path
from turtle import Model,VERTICES,Graph
from boundary_macros import singleton,problems,mine
from run_failure_interfaces import HERE,DOCS,selected_types,chosen_parent
from resident_regions import Universe
from cluster_tiles import ClusterModel,ClusterState,verify_state
from cluster_learning import check_corona_positive,check_corona_failure,exact_point
from multiscale_learning import decorate,unpack_markings
from region_tiles import Boundary,unpack_state,verify_region,packed_state,check_failure
from audit_boundary_macros import Oracle,normal,exact_key
from audit_compiled_macros import literal_domains
from audit_multiscale_regions import audit_stage,contact
from audit_geometry import audit as geometry_audit

def check_dead_sample(sample,boundary,universe,oracle):
    """One complete empty-domain leaf under an externally fixed prefix."""
    try:
        if normal(boundary.packed())!=normal(sample['boundary']):return False
        model=universe.bind(boundary);state=unpack_state(model,boundary,sample['context'])
        if not verify_region(model,boundary,state):return False
        action=tuple(exact_key(k) for k in sample['action'])
        if len(action)<2:return False
        for key in action:
            domains=literal_domains(oracle,state)
            if not domains or any(not cs for cs in domains.values()):return False
            forced=sorted(p for p,cs in domains.items() if len(cs)==1)
            p=forced[0] if forced else min(domains,key=lambda p:(state.generations[p],len(domains[p]),p))
            if key not in domains[p]:return False
            state.place(model.placement(key))
        if normal(packed_state(state))!=normal(sample['endpoint']):return False
        p=tuple(sample['certificate']['dead']);domains=literal_domains(oracle,state)
        return exact_point(p) and p in domains and not domains[p]
    except (ValueError,KeyError,TypeError,IndexError):return False

def main():
    start=time.monotonic();path=DOCS/'failure-interfaces-001.json';d=json.loads(path.read_text())
    for n,s in d['sources'].items():assert hashlib.sha256((HERE/n).read_bytes()).hexdigest()==s
    train=problems(True);evals=problems();declarations={b.identity:b for b in (*train,*evals)}
    assert d['training_problems']==normal([b.packed() for b in train]);assert d['problems']==normal([b.packed() for b in evals])
    u=Universe((singleton(),),train[0].allowed);oracle=Oracle(train[0].allowed)
    states=complete=moves=tampers=0;patches=[]
    def replay(r,display=False):
        nonlocal states,complete,moves,tampers
        b=declarations[r['problem']];assert oracle.replay(r,b);assert r['admissible_placements']==len(oracle.values)
        states+=1;complete+=r['status']=='finite_exact_region';moves+=len(r['execution'])
        if r['execution']:
            bad=copy.deepcopy(r);bad['execution'][0]['point']=[90,-45,-45];assert not oracle.replay(bad,b);tampers+=1
        if display and r['status']=='finite_exact_region':patches.append({'lane':r['lane']+'/'+r['problem'],'seed':r['seed'],'placements':r['state']['base_expansion']})
    for r in d['donors']+d['training']['episodes']:replay(r)
    for r in d['evaluation']:replay(r,True)
    library,info=mine(d['donors'],u.model);assert normal(library)==d['library']
    types,ids=selected_types(library);assert ids==d['selected_shape_ids']
    for r,t in zip(d['prototype_probes'],types):
        assert r['type']==t.identity
        if r['status']=='positive':assert check_corona_positive(Model(),t.expansion,r['witness'])
        elif r['status']=='negative':assert check_corona_failure(Model(),t.expansion,r['certificate'])[0]
        else:assert r['certificate'] is None
    stages=[]
    for decl in d['stages']:
        raw=(DOCS/decl['artifact']).read_bytes();assert hashlib.sha256(raw).hexdigest()==decl['sha256']
        stages.append(json.loads(raw))
    first=stages[0];stage_audits=[audit_stage(first,types)];marks=unpack_markings(first)
    marked=tuple(decorate(t,marks[t.identity]) for t in types) if first['activation_gate_passed'] else types
    parent,children=chosen_parent(marked,first);bare_parent,_=chosen_parent(types,first)
    assert normal(children)==d['parent_children']
    if parent:
        second=stages[1];stage_audits.append(audit_stage(second,(parent,)))
        if second['activation_gate_passed']:parent=decorate(parent,unpack_markings(second)[parent.identity])
    inventories={'aggregate unmarked':(singleton(),*types,*((bare_parent,) if bare_parent else ())),
                 'aggregate GCTS':(singleton(),*marked,*((parent,) if parent else ()))}
    assert normal({n:[dataclasses.asdict(t) for t in ts] for n,ts in inventories.items()})==d['inventories']
    transforms=0
    for lane,ts in inventories.items():
        cm=ClusterModel(ts)
        for t in ts:
            for o in range(12):
                s=ClusterState();s.place(cm.placement((t.identity,o,(0,0,0))),seed=True);assert verify_state(cm,s);transforms+=1
    negative_nodes=0
    for r in d['atomic_evaluation']:
        cm=ClusterModel(inventories[r['lane']]);b=declarations[r['problem']];s=unpack_state(cm,b,r['state'])
        exact=r['status']=='finite_exact_region';assert verify_region(cm,b,s,exact)
        assert r['accepted_base_tiles']==len(s.owned_base-set(b.owned))
        assert r['coverage_fraction']==sum(s.totals.get(p,0)==12 for p in b.required)/len(b.required)
        if r['status']=='exhausted_finite_region':
            valid,n=check_failure(cm,b,r['certificate']);assert valid;negative_nodes+=n
        else:assert r['certificate'] is None
        states+=1;complete+=exact
        if exact:patches.append({'lane':r['lane']+'/'+r['problem'],'seed':r['seed'],'placements':r['state']['base_expansion']})
    samples=d['training']['endpoint_samples']+[s for rows in d['endpoint_samples'].values() for s in rows]
    for sample in samples:
        b=declarations[sample['boundary']['identity']];assert check_dead_sample(sample,b,u,oracle)
        bad=copy.deepcopy(sample);bad['certificate']['dead']=[90,-45,-45]
        assert not check_dead_sample(bad,b,u,oracle);tampers+=1
    assert d['training']['initial_weights']=={} and d['training']['initial_markings']=={} and not d['configuration']['saved_artifacts_imported']
    assert d['training']['updates']==len(d['training']['episodes'])
    assert set(r['seed'] for r in d['donors']+d['training']['episodes']).isdisjoint(r['seed'] for r in d['evaluation'])
    geometry=geometry_audit({'point_model':{'vertices':VERTICES},'pair_catalog':{'samples':[]},'evaluation':patches})
    inherited=own=new_own=0;parent_obstruction=None
    if parent:
        cm=ClusterModel((singleton(),*marked,chosen_parent(marked,first)[0]));root=ClusterState();root.place(cm.placement((parent.identity,0,(0,0,0))),seed=True)
        inherited_set={contact(s['contact']) for s in stages[1]['samples'] if not root.legal(cm.placement((s['contact'][1],s['contact'][2],tuple(s['contact'][3]))))}
        own_set={contact(k) for k in stages[1]['disagreements']};inherited=len(inherited_set);own=len(own_set);new_own=len(own_set-inherited_set)
        if all(s['status']=='negative' for s in stages[1]['samples']):
            p,v=next((p,v) for p,v in parent.occupancy if v<12)
            parent_obstruction={'type':parent.identity,'partial_point':p,'contribution':v,
                                'contacts':len(stages[1]['samples']),'failure_nodes':stage_audits[1]['negative_nodes'],
                                'scope':'analytic parent-only point-tiling obstruction: a partial point needs another parent, whose normalized pair has a complete unmarked base failure; mixed regions remain admissible'}
    d['independent_audit']={'stages':stage_audits,'states_replayed':states,'complete_states':complete,'scheduled_macro_base_moves':moves,
        'contextual_dead_prefixes_checked':len(samples),'tampered_certificates_rejected':tampers,'transformed_expansions':transforms,
        'atomic_failure_nodes':negative_nodes,'parent_inherited_exclusions':inherited,'parent_own_exclusions':own,
        'parent_new_own_exclusions':new_own,'parent_only_obstruction':parent_obstruction,'geometry':geometry,
        'seconds':time.monotonic()-start,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'helper_source_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('audit_boundary_macros.py','audit_compiled_macros.py','audit_multiscale_regions.py','audit_geometry.py')},
        'scope':'all scalar exclusions at both levels have base-corona proofs; fixed-boundary endpoint leaves have only their declared prefix/region scope; all saved regions independently expand; no plane construction'}
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in d['independent_audit'].items() if k!='geometry'},indent=2),flush=True)

if __name__=='__main__':main()
