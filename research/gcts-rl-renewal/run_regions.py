"""Reused-boundary pilot: finite holes, aggregate tiles and zero-start RL.

The old patch is used ONLY to author a declared exterior problem and replay a
feasibility control. Its removed tiles never enter search or policy features.
Cluster prototypes are an explicitly reused separate motif artifact. No old
marking/policy is imported, and no new learned failure marking is claimed.
"""
import dataclasses,gc,hashlib,json,resource,time
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from turtle import Model,Policy,add,verify_patch
from cluster_tiles import ClusterType,ClusterModel,ClusterState,compose_type,verify_state
from coverage import hexagon
from spatial import keys_tuple
from region_tiles import Boundary,search,movable_search

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'

def load_types():
    artifact=json.loads((DOCS/'cluster-types-001.json').read_text());types=[]
    for t in artifact['types']:
        types.append(ClusterType(t['identity'],t['level'],keys_tuple(t['expansion']),tuple((tuple(p),v) for p,v in t['occupancy']),
            tuple(((tuple(p),ch),v) for (p,ch),v in t['marks']),tuple((n,o,tuple(tr)) for n,o,tr in t['children'])))
    return types

def hole(donor,radius,center,identity):
    base=Model();all_keys=keys_tuple(donor['placements']);totals=Counter();support={}
    for key in all_keys:
        support[key]=set(dict(base.placement(key).occupancy));totals.update(dict(base.placement(key).occupancy))
    core={add(p,center) for p in hexagon(radius)}
    # Retain fully filled donor points in a three-point collar as obligations.
    collar={add(p,center) for p in hexagon(radius+3)}
    required=frozenset(p for p in collar if totals[p]==12)
    if not core<=required:raise ValueError('donor does not fill the intended core')
    removed=tuple(k for k in all_keys if support[k]&core);fixed=tuple(k for k in all_keys if not support[k]&core)
    ext=Counter()
    for k in fixed:ext.update(dict(base.placement(k).occupancy))
    boundary=Boundary(identity,required,frozenset(totals),tuple(sorted(ext.items())),owned=fixed)
    assert verify_patch(base,all_keys,required)
    return boundary,{'donor_seed':donor['seed'],'radius':radius,'center':center,'fixed_base_tiles':fixed,
                     'removed_feasibility_control':removed,'control_not_exposed_to_search':True}

def problems():
    d=json.loads((DOCS/'iteration-003.json').read_text());donors={r['seed']:r for r in d['core_coverage'] if r['lane']=='baseline'}
    training=[];evaluation=[]
    centers=[(0,0,0),(2,-2,0),(-2,2,0),(0,2,-2),(0,-2,2),(2,0,-2)]
    for i,center in enumerate(centers):training.append(hole(donors[85000],2+i%2,center,'train-'+str(i)))
    for seed in [85001,85002]:
        for radius in [3,5]:evaluation.append(hole(donors[seed],radius,(0,0,0),f'eval-{seed}-{radius}'))
    # Independently authored targets; no donor, exterior or feasibility witness.
    required=frozenset(hexagon(4));allowed=frozenset(hexagon(10))
    evaluation.append((Boundary('free-core',required,allowed),{'kind':'witness-free required hexagonal core with finite placement envelope'}))
    irregular=(hexagon(4)-{p for p in hexagon(4) if p[0]>1 and p[1]>0})|{(6,-3,-3),(7,-3,-4)}
    evaluation.append((Boundary('free-notch-pocket',frozenset(irregular),frozenset(hexagon(12))),
                       {'kind':'witness-free notched core and disconnected required pocket with finite placement envelope'}))
    return training,evaluation

def movable_cases(evaluation):
    # One fixed exterior, one fixed envelope, three possible translated targets.
    # The remote target is a real dead branch; selecting the feasible member
    # must not inherit its roots, domains, ownership or exclusions.
    cases=[]
    for boundary,meta in evaluation[:4:2]:
        remote=frozenset({(60,-30,-30)})
        shifted=frozenset(add(p,(1,-1,0)) for p in boundary.required)
        allowed=boundary.allowed|remote|shifted
        dead=Boundary(boundary.identity+'-remote',remote,allowed,boundary.exterior,boundary.marks,boundary.owned)
        shift=Boundary(boundary.identity+'-shift',shifted,allowed,boundary.exterior,boundary.marks,boundary.owned)
        original=Boundary(boundary.identity,boundary.required,allowed,boundary.exterior,boundary.marks,boundary.owned)
        cases.append([dead,shift,original])
    return cases

def main():
    start=time.monotonic();types=load_types();single=[t for t in types if t.identity=='base'];training,evaluation=problems()
    policy=Policy();episodes=[];t0=time.monotonic()
    for i in range(24):
        boundary,_=training[i%len(training)]
        r=search(types,boundary,26000+i,node_limit=500,seconds=3,policy=policy,learn=True,rollout=True)
        r['problem']=boundary.identity;episodes.append(r);gc.collect()
        print('train',i,r['status'],'base',r['accepted_base_tiles'],'s',round(r['seconds'],3),flush=True)
    training_seconds=time.monotonic()-t0;results=[]
    for j,(boundary,meta) in enumerate(evaluation):
        for lane,inventory,proposer in [('singletons',single,None),('aggregate',types,None),('aggregate+RL',types,policy)]:
            r=search(inventory,boundary,27000+j,node_limit=10000,seconds=10,policy=proposer)
            r.update(problem=boundary.identity,lane=lane);results.append(r);gc.collect()
            print(boundary.identity,lane,r['status'],'base',r['accepted_base_tiles'],'s',round(r['seconds'],3),flush=True)
    movable=[];families=movable_cases(evaluation)
    for j,family in enumerate(families):
        for lane,inventory,proposer in [('singletons',single,None),('aggregate',types,None),('aggregate+RL',types,policy)]:
            r=movable_search(inventory,family,28000+j,node_limit=10000,seconds=10,policy=proposer)
            r.update(family=j,lane=lane);movable.append(r);gc.collect()
            print('movable',j,lane,r['status'],r['selected'],'s',round(r['seconds'],3),flush=True)
    # Searched local completions now become actual parent types, with explicit
    # child maps and their boundary provenance. No own-level colors are assumed.
    t0=time.monotonic();model=ClusterModel(types);parents=[]
    for r in results:
        if r['lane']=='aggregate+RL' and r['status']=='finite_exact_region':
            children=tuple((n,o,tuple(tr)) for n,o,tr in r['state']['placements'])
            parents.append(compose_type(model,'solution-'+r['problem'],children))
    parent_model=ClusterModel(types+parents);checks=0
    for parent in parents:
        for o in range(12):
            s=ClusterState();s.place(parent_model.placement((parent.identity,o,(0,0,0))),seed=True)
            assert verify_state(parent_model,s);checks+=1
    parent_seconds=time.monotonic()-t0
    points=frozenset(hexagon(5));negative=Boundary('closed-hex-control',points,points)
    negative_result=search(single,negative,seconds=10)
    data={'date':datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),'kind':'explicitly reused boundary and cluster pilot',
          'scope':'finite point boundary completion; atomic aggregate inventory; no learned GCTS marking, substitution, plane proof or practical speed guarantee',
          'reuse':{'artifacts':{name:hashlib.sha256((DOCS/name).read_bytes()).hexdigest() for name in ['iteration-003.json','cluster-types-001.json']},
                   'patch_use':'fixed exterior and independently checked feasibility controls only; removed placements unavailable to search/policy',
                   'cluster_use':'16 frozen unmarked first-class types, including all base singletons',
                   'old_marking_imported':False,'old_policy_imported':False},
          'configuration':{'node_limit':10000,'seconds_per_fixed_problem':10,'budget_semantics':'cooperative wall cutoff includes inventory construction; a construction overrun returns unknown at its next checkpoint',
                           'training_episodes':24,'training_node_limit':500,'training_seconds':3,'training_seeds':list(range(26000,26024)),
                           'evaluation_seeds':list(range(27000,27006)),'movable_seeds':[28000,28001],
                           'scheduler':'global dead, global forced, earliest generation then degree and point; aggregate-level decisions',
                           'generations':'all required roots and exterior support have generation zero; new tiles use minimum incident generation',
                           'inventory':'12 symmetries, integer A2 translations; all positive support inside finite allowed envelope; fixed exterior ownership retained'},
          'training':{'seconds':training_seconds,'episodes':episodes,'policy_weights':dict(policy.weights),'policy_updates':policy.updates,
                      'problems':[{'boundary':b.packed(),'construction':m} for b,m in training]},
          'problems':[{'boundary':b.packed(),'construction':m} for b,m in evaluation],'evaluation':results,
          'movable_families':[[b.packed() for b in family] for family in families],'movable_evaluation':movable,
          'local_solution_types':{'types':[dataclasses.asdict(t) for t in parents],'transformed_expansions_checked':checks,'seconds':parent_seconds,
                                  'scope':'searched local completions with descending child maps; context-specific completion guarantee, globally valid flattened partial tile',
                                  'own_marking_status':'unassigned; inherited child marks retained'},
          'negative_control':{'boundary':negative.packed(),'result':negative_result},
          'total_seconds':time.monotonic()-start,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in HERE.glob('*.py')},
          'open':['cold boundary generation without feasibility witnesses','learned own-level cluster markings from checked failures','local-to-coarse interface assembly and refinement',
                  'larger targets and other tile systems','unbounded plane continuation','first-order kernel compiler']}
    (DOCS/'regions-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('wrote regions-001.json',round(data['total_seconds'],3),'s',flush=True)

if __name__=='__main__':main()
