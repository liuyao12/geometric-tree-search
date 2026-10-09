"""Cold two-level palette learning, parent assembly and larger region requests."""
import dataclasses,gc,hashlib,json,resource,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter
from turtle import Model,Policy
from cluster_tiles import ClusterModel,compose_type
from multiscale_learning import learn,plain,decorate,unpack_markings
from resident_regions import Universe,search
from region_tiles import Boundary
from coverage import hexagon
from run_regions import load_types

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
SOURCES=('multiscale_learning.py','resident_regions.py','run_multiscale_regions.py','turtle.py','cluster_tiles.py',
         'cluster_learning.py','region_tiles.py','spatial.py','coverage.py','run_regions.py')

def initial_types():
    types=load_types();names=('base','cluster-2','cluster-3')
    return tuple(next(t for t in types if t.identity==n) for n in names)

def make_parent(children,stage):
    positive=[s for s in stage['samples'] if s['status']=='positive']
    if not positive:raise ValueError('no searched child assembly available')
    s=min(positive,key=lambda s:(s['contact'][0]==s['contact'][1],s['contact']))
    a,b,o,tr=s['contact'];keys=((a,0,(0,0,0)),(b,o,tuple(tr)))
    return compose_type(ClusterModel(children),'searched-multiscale-parent',keys),keys

def problems(training=False):
    allowed=frozenset(hexagon(14));items=[]
    if training:
        for i,center in enumerate(((0,0,0),(2,-2,0),(-2,2,0),(0,2,-2))):
            required=frozenset(tuple(x+y for x,y in zip(p,center)) for p in hexagon(2+i%2))
            items.append(Boundary(f'multiscale-train-{i}',required,allowed))
    else:
        for radius in (4,6,8):items.append(Boundary(f'core-{radius}',frozenset(hexagon(radius)),allowed))
        notch={p for p in hexagon(6) if not(p[0]>2 and p[1]>0)}|{(10,-5,-5),(11,-5,-6)}
        items.append(Boundary('notch-and-pocket',frozenset(notch),allowed))
    return tuple(items)

def summary(stage,filename):
    return {k:v for k,v in stage.items() if k not in ('samples','history','markings','disagreements')}|{
            'artifact':filename,'sha256':hashlib.sha256((DOCS/filename).read_bytes()).hexdigest()}

def main():
    start=time.monotonic();sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES}
    single,a,b=initial_types();children=(a,b)
    first=learn(children,'level-one')
    first['sources']=sources;(DOCS/'multiscale-level1-001.json').write_text(json.dumps(first,separators=(',',':'))+'\n')
    m1=unpack_markings(first);marked_children=tuple(decorate(t,m1[t.identity]) for t in children) if first['activation_gate_passed'] else children
    parent,child_map=make_parent(marked_children,first)
    bare_parent,_=make_parent(children,first)
    second=learn((parent,),'level-two')
    second['sources']=sources;(DOCS/'multiscale-level2-001.json').write_text(json.dumps(second,separators=(',',':'))+'\n')
    m2=unpack_markings(second);marked_parent=decorate(parent,m2[parent.identity]) if second['activation_gate_passed'] else parent
    raw=(single,*children,bare_parent);inherited=(single,*marked_children,parent);marked=(single,*marked_children,marked_parent)
    inventories={'singletons':(single,),'unmarked hierarchy':raw,'inherited GCTS':inherited,
                 'GCTS hierarchy':marked,'RL hierarchy':raw,'GCTS+RL hierarchy':marked}
    # Share only identical frozen tile/marking versions. Each request still
    # starts with new roots, global marks, ownership, graph and branch state.
    universes={};construction=[]
    for name,types in inventories.items():
        if types not in universes:
            u=Universe(types,problems()[0].allowed);universes[types]=u
            construction.append({'first_lane':name,'types':[t.identity for t in types],'seconds':u.seconds,'placements':len(u.keys)})
            print('resident inventory',name,len(u.keys),'placements',round(u.seconds,3),'s',flush=True)
    policy=Policy();episodes=[];training_start=time.monotonic();training=problems(True)
    for i in range(12):
        boundary=training[i%len(training)]
        r=search(raw,boundary,51000+i,node_limit=100,seconds=4,policy=policy,learn=True,rollout=True,universe=universes[raw])
        r['problem']=boundary.identity;episodes.append(r);print('training',i,r['status'],round(r['seconds'],3),flush=True);gc.collect()
    training_seconds=time.monotonic()-training_start;results=[];resident_controls=[]
    for j,boundary in enumerate(problems()):
        for replicate in range(2):
            seed=52000+2*j+replicate
            # Only the representation differs from its resident counterpart.
            cold=search(raw,boundary,seed,node_limit=4000,seconds=5)
            cold.update(problem=boundary.identity,replicate=replicate,lane='cold unmarked hierarchy');resident_controls.append(cold)
            print(boundary.identity,'cold',replicate,cold['status'],round(cold['seconds'],3),flush=True)
            for lane,types in inventories.items():
                p=policy if lane in ('RL hierarchy','GCTS+RL hierarchy') else None
                r=search(types,boundary,seed,node_limit=4000,seconds=5,policy=p,universe=universes[types])
                r.update(problem=boundary.identity,replicate=replicate,lane=lane);results.append(r)
                print(boundary.identity,lane,replicate,r['status'],round(r['seconds'],3),'s',flush=True);gc.collect()
    report={'date':datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),'sources':sources,
            'reuse':{'shape_artifact':'cluster-types-001.json','sha256':hashlib.sha256((DOCS/'cluster-types-001.json').read_bytes()).hexdigest(),
                     'imported':'unmarked singleton and two searched mixed-handed two-turtle shapes only; all palettes and policy start free/zero; no donor boundary or proof witness'},
            'stages':[summary(first,'multiscale-level1-001.json'),summary(second,'multiscale-level2-001.json')],
            'parent_children':child_map,'inventories':{n:[dataclasses.asdict(t) for t in ts] for n,ts in inventories.items()},
            'problems':[b.packed() for b in problems()],'configuration':{'lanes':list(inventories),'replicates':2,'nodes':4000,'seconds':5,
                      'training_episodes':12,'training_nodes':100,'training_seconds':4,'required_radii':[4,6,8],
                      'point_semantics':'all target points must sum to 12; other points in the radius-14 support envelope remain capacity-legal; every target root generation zero'},
            'resident_construction':construction,'training':{'episodes':episodes,'weights':dict(policy.weights),'seconds':training_seconds,
                      'boundaries':[b.packed() for b in training],'scope':'zero-start on unmarked hierarchy; finite rollout proposals; every full evaluation retains all alternatives'},
            'evaluation':results,'representation_controls':resident_controls,
            'total_seconds':time.monotonic()-start,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'scope':'finite exact point regions; learned shared level-one and own level-two scalar channels; same aggregate inventory in marking lanes, singleton representation comparison separate',
            'limits':['no turtle plane construction or geometric faithfulness theorem','two reused child shapes and one newly searched parent, not a complete metatile hierarchy',
                      'complete-base redundancy can restrict finite cluster groupings; all unmarked singleton paths retained',
                      'coarse atomic scheduler differs from macro execution in the base engine','small two-seed pilot; no cross-system practical-speed guarantee']}
    path=DOCS/'multiscale-regions-001.json';path.write_text(json.dumps(report,separators=(',',':'))+'\n')
    print('wrote',path.name,round(report['total_seconds'],3),'s',flush=True)

if __name__=='__main__':main()
