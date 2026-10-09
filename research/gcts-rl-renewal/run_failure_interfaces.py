"""Fresh variable-size cluster markings and failure-aware regional proposals."""
import dataclasses,gc,hashlib,json,resource,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from turtle import Model,Policy
from boundary_macros import singleton,problems,mine,search as macro_search
from compiled_macros import CompiledProposer
from viable_macros import ViableProposer
from resident_regions import Universe,search as atomic_search
from cluster_tiles import make_type,ClusterModel,compose_type
from cluster_learning import corona,check_corona_positive,check_corona_failure
from multiscale_learning import learn,decorate,unpack_markings

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
SOURCES=('viable_macros.py','run_failure_interfaces.py','compiled_macros.py','boundary_macros.py',
         'resident_regions.py','region_tiles.py','cluster_tiles.py','cluster_learning.py','multiscale_learning.py',
         'spatial.py','coverage.py','turtle.py')

def selected_types(library):
    selected=[min((m for m in library if len(m['expansion'])==size),
                  key=lambda m:(-len(m['donor_seeds']),-m['count'],m['expansion'])) for size in (2,3)]
    return tuple(make_type(Model(),'local-'+str(len(m['expansion'])),1,m['expansion']) for m in selected),[m['id'] for m in selected]

def chosen_parent(children,stage):
    positive=[s for s in stage['samples'] if s['status']=='positive' and s['contact'][0]!=s['contact'][1]]
    if not positive:return None,None
    a,b,o,tr=min(positive,key=lambda s:s['contact'])['contact'];keys=((a,0,(0,0,0)),(b,o,tuple(tr)))
    return compose_type(ClusterModel(children),'local-parent-5',keys),keys

def save_stage(stage,name,sources):
    stage['sources']=sources;(DOCS/name).write_text(json.dumps(stage,separators=(',',':'))+'\n')
    return {k:v for k,v in stage.items() if k not in ('samples','history','markings','disagreements','sources')}|{
            'artifact':name,'sha256':hashlib.sha256((DOCS/name).read_bytes()).hexdigest()}

def main():
    start=time.monotonic();sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES}
    train=problems(True);evals=problems();single=singleton();u=Universe((single,),train[0].allowed);donors=[];t0=time.monotonic()
    for i in range(8):
        b=train[i%4];r=macro_search(b,u,100000+i,seconds=3);r['problem']=b.identity;donors.append(r)
    donor_seconds=time.monotonic()-t0;library,mining=mine(donors,u.model);types,ids=selected_types(library)
    probes=[]
    for t in types:
        r=corona(Model(),t.expansion,2000,3);r['type']=t.identity;probes.append(r)
        if r['status']=='positive':assert check_corona_positive(Model(),t.expansion,r['witness'])
        elif r['status']=='negative':assert check_corona_failure(Model(),t.expansion,r['certificate'])[0]
        print('prototype',t.identity,r['status'],flush=True)
    first=learn(types,'variable-local-level-one');summaries=[save_stage(first,'failure-local-level1-001.json',sources)]
    marks=unpack_markings(first);marked=tuple(decorate(t,marks[t.identity]) for t in types) if first['activation_gate_passed'] else types
    parent,child_map=chosen_parent(marked,first);bare_parent,_=chosen_parent(types,first)
    second=None
    if parent:
        second=learn((parent,),'variable-local-level-two');summaries.append(save_stage(second,'failure-local-level2-001.json',sources))
        if second['activation_gate_passed']:parent=decorate(parent,unpack_markings(second)[parent.identity])
    raw_types=(single,*types,*((bare_parent,) if bare_parent else ()))
    marked_types=(single,*marked,*((parent,) if parent else ()))
    gc.collect();compiled=CompiledProposer(library,u);training_proposer=ViableProposer(compiled.fork(128));policy=Policy();episodes=[];t0=time.monotonic()
    for i in range(24):
        b=train[i%4];r=macro_search(b,u,101000+i,attempt_limit=500,seconds=3,policy=policy,
                                   proposer=training_proposer,learn=True,rollout=True)
        r['problem']=b.identity;episodes.append(r);print('train',i,r['status'],round(r['seconds'],3),flush=True)
    training_seconds=time.monotonic()-t0
    proposers={'base':None,'compiled':compiled.fork(128),'viable':ViableProposer(compiled.fork(128)),
               'compiled+RL':compiled.fork(128),'viable+RL':ViableProposer(compiled.fork(128))}
    lanes=tuple(proposers);results=[]
    for j,b in enumerate(evals):
        for replica in (0,1):
            offset=(j*2+replica)%len(lanes);order=lanes[offset:]+lanes[:offset]
            for lane in order:
                r=macro_search(b,u,102000+j*2+replica,seconds=6,policy=policy if '+RL' in lane else None,proposer=proposers[lane])
                r.update(problem=b.identity,lane=lane,replica=replica);results.append(r);gc.collect()
                print('eval',b.identity,replica,lane,r['status'],round(r['seconds'],3),flush=True)
    constructions=[];atomic=[];inventories={'aggregate unmarked':raw_types,'aggregate GCTS':marked_types};universes={}
    for lane,ts in inventories.items():
        v=Universe(ts,train[0].allowed);universes[lane]=v
        constructions.append({'lane':lane,'seconds':v.seconds,'placements':len(v.keys)})
    for j,b in enumerate(evals):
        for lane,ts in inventories.items():
            r=atomic_search(ts,b,103000+j,node_limit=4000,seconds=6,universe=universes[lane])
            r.update(problem=b.identity,lane=lane);atomic.append(r)
            print('atomic',b.identity,lane,r['status'],round(r['seconds'],3),flush=True)
    data={'date':datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),'sources':sources,
          'scope':'two distinct mechanisms: contextual complete-graph endpoint filter and own-level scalar GCTS from unmarked base-corona certificates',
          'configuration':{'lanes':lanes,'base_attempts':8000,'seconds':6,'replicas':2,'training_episodes':24,
                           'macro_scheduler':'unchanged complete singleton graph; global dead, forced, earliest generation',
                           'atomic_scheduler':'same rule in a separate four-type aggregate inventory; differs from singleton macros',
                           'all_singletons_retained':True,'saved_artifacts_imported':False},
          'inventory':{'seconds':u.seconds,'placements':len(u.keys)},'compilation':compiled.manifest,
          'donors':donors,'donor_seconds':donor_seconds,'library':library,'mining':mining,'selected_shape_ids':ids,'prototype_probes':probes,
          'stages':summaries,'parent_children':child_map,'inventories':{n:[dataclasses.asdict(t) for t in ts] for n,ts in inventories.items()},
          'training_problems':[b.packed() for b in train],'problems':[b.packed() for b in evals],
          'training':{'episodes':episodes,'seconds':training_seconds,'weights':dict(policy.weights),'updates':policy.updates,
                      'initial_weights':{},'initial_markings':{},'endpoint_samples':training_proposer.samples},
          'evaluation':results,'endpoint_samples':{n:p.samples for n,p in proposers.items() if isinstance(p,ViableProposer)},
          'atomic_construction':constructions,'atomic_evaluation':atomic,
          'total_seconds':time.monotonic()-start,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'timing_provenance':'one sequential cold process; all catalog, proof replay, synthesis, policy, construction and cutoff costs included; process peak, not per-lane allocation'}
    (DOCS/'failure-interfaces-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('saved',data['total_seconds'],flush=True)

if __name__=='__main__':main()
