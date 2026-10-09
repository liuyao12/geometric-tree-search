"""Fresh local response atlas, composition, and resolution-policy experiment."""
import gc,hashlib,json,resource,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from turtle import Policy
from boundary_responses import declarations,mine,Atlas,search
from boundary_macros import singleton
from resident_regions import Universe
from region_tiles import Boundary

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
SOURCES=('boundary_responses.py','run_boundary_responses.py','boundary_macros.py','resident_regions.py',
         'region_tiles.py','cluster_tiles.py','spatial.py','coverage.py','turtle.py')

def main():
    start=time.monotonic();sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES}
    train=declarations(True);evals=declarations();u=Universe((singleton(),),train[0].allowed)
    data={'date':datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),'sources':sources,
          'scope':'sampled composable local boundary responses; complete singleton graph; exact finite regions only',
          'training_problems':[b.packed() for b in train],'problems':[b.packed() for b in evals],
          'inventory':{'seconds':u.seconds,'placements':len(u.keys)},'donors':[],'evaluation':[]}
    def save():
        data['total_seconds']=time.monotonic()-start
        data['peak_process_memory_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (DOCS/'boundary-responses-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    t0=time.monotonic()
    for i in range(16):
        b=train[i%4];r=search(b,u,110000+i,seconds=3);r['problem']=b.identity;data['donors'].append(r)
        print('donor',i,r['status'],r['attempted_base_placements'],round(r['seconds'],3),flush=True)
    data['donor_seconds']=time.monotonic()-t0
    library=mine(data['donors'],{b.identity:b for b in train},u.model);data['library']=library
    print('atlas',len(library['selected']),len(library['nodes']),library['seconds'],flush=True)
    geometry=Atlas(library,u,trace=False);small=Atlas(library,u,max_size=4);hierarchy=Atlas(library,u)
    data['compilation']={name:p.manifest for name,p in (('geometry',geometry),('trace-small',small),('trace-hierarchy',hierarchy))}
    policy=Policy();data['training']={'episodes':[],'initial_weights':{},'initial_marking':{},'imported_artifact':False}
    t0=time.monotonic()
    for i in range(48):
        b=train[i%4];r=search(b,u,111000+i,attempt_limit=500,seconds=2,atlas=hierarchy,policy=policy,learn=True,rollout=True)
        r['problem']=b.identity;data['training']['episodes'].append(r)
        print('train',i,r['status'],round(r['seconds'],3),flush=True)
    data['training'].update(seconds=time.monotonic()-t0,weights=dict(policy.weights),updates=policy.updates)
    lanes=('base','geometry','trace-small','trace-hierarchy+zero','trace-hierarchy+RL')
    proposers={'base':None,'geometry':geometry,'trace-small':small,'trace-hierarchy+zero':hierarchy,'trace-hierarchy+RL':hierarchy}
    data['configuration']={'lanes':lanes,'replicas':2,'base_attempts':4000,'seconds':6,'response_limit':8,
                           'response_sizes':[2,3,4,6,8,12],'training_episodes':48,
                           'scheduler':'global dead, forced, earliest generation in complete base graph',
                           'macro_execution':'conditional ordered proposal; interrupt before any unscheduled move; retain every singleton',
                           'lane_order':'rotated by target/replica; one sequential process',
                           'zero_control':'fresh zero weights, same features and evaluation seeds as learned policy'}
    save()
    for j,b in enumerate(evals):
        for replica in range(2):
            offset=(j*2+replica)%len(lanes);order=lanes[offset:]+lanes[:offset]
            for lane in order:
                p=policy if lane.endswith('+RL') else Policy() if lane.endswith('+zero') else None
                r=search(b,u,112000+j*2+replica,atlas=proposers[lane],policy=p)
                r.update(problem=b.identity,lane=lane,replica=replica);data['evaluation'].append(r);save();gc.collect()
                print('eval',b.identity,replica,lane,r['status'],r['attempted_base_placements'],round(r['seconds'],3),flush=True)
    controls=[]
    for j,b in enumerate(evals):
        pair=[search(b,u,113000+j,attempt_limit=100,seconds=None,atlas=hierarchy,policy=p) for p in (None,Policy())]
        fields=('status','nodes','branches','forced','backtracks','attempted_base_placements','state','execution','response_events')
        assert all(pair[0][name]==pair[1][name] for name in fields)
        controls.append({'problem':b.identity,'results':pair,'fields':fields,'equivalent':True})
        print('zero-control',b.identity,pair[0]['status'],'equivalent',flush=True)
    data['zero_controls']=controls
    # A finite existential movable-boundary pilot. A failed earlier target is
    # never a plane obstruction; successful later targets certify existence.
    family=(Boundary('moving-outer',u.allowed,u.allowed),
            Boundary('moving-inner-8',evals[2].required,u.allowed),Boundary('moving-inner-6',evals[1].required,u.allowed))
    data['movable_family']=[b.packed() for b in family];data['movable_evaluation']=[]
    for lane in lanes:
        t0=time.monotonic();attempts=[];selected=None
        for i,b in enumerate(family):
            p=policy if lane.endswith('+RL') else Policy() if lane.endswith('+zero') else None
            r=search(b,u,114000+i,atlas=proposers[lane],policy=p);attempts.append({'boundary':b.identity,'result':r})
            if r['status']=='finite_exact_region':selected=b.identity;break
        data['movable_evaluation'].append({'lane':lane,'selected':selected,'attempts':attempts,'seconds':time.monotonic()-t0})
        print('movable',lane,selected,flush=True)
    data['timing_provenance']='single sequential fresh process; universe, donor, mining, atlas validation/compilation and policy costs separate; process peak is not per-lane allocation'
    save();print('saved',data['total_seconds'],flush=True)

if __name__=='__main__':main()
