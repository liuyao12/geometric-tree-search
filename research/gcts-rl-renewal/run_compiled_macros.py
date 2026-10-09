"""Cold matched representation ablations and exact base-attempt controls."""
import gc,hashlib,json,resource,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from turtle import Policy
from boundary_macros import singleton,problems,mine,Proposer,search
from compiled_macros import CompiledProposer
from resident_regions import Universe
from run_boundary_macros import families

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
SOURCES=('compiled_macros.py','run_compiled_macros.py','boundary_macros.py','run_boundary_macros.py',
         'resident_regions.py','region_tiles.py','cluster_tiles.py','spatial.py','coverage.py','turtle.py')

def main():
    start=time.monotonic();sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES}
    train=problems(True);evals=problems();u=Universe((singleton(),),train[0].allowed);donors=[];t0=time.monotonic()
    for i in range(8):
        b=train[i%4];r=search(b,u,95000+i,seconds=3);r['problem']=b.identity;donors.append(r)
        print('donor',i,r['status'],flush=True)
    donor_seconds=time.monotonic()-t0;library,mining=mine(donors,u.model);raw=Proposer(library)
    compiled=CompiledProposer(library,u,cache_size=0,shared_prefixes=False)
    shared=compiled.fork(0);cached=compiled.fork(128);rl_cached=compiled.fork(128)
    policy=Policy();episodes=[];t0=time.monotonic()
    for i in range(24):
        b=train[i%4];r=search(b,u,96000+i,attempt_limit=500,seconds=3,policy=policy,proposer=raw,learn=True,rollout=True)
        r['problem']=b.identity;episodes.append(r)
        print('train',i,r['status'],round(r['seconds'],3),flush=True)
    training_seconds=time.monotonic()-t0
    lanes=('base','raw','compiled','shared','cached','raw+RL','cached+RL')
    proposers={'base':None,'raw':raw,'compiled':compiled,'shared':shared,'cached':cached,'raw+RL':raw,'cached+RL':rl_cached}
    results=[]
    for j,b in enumerate(evals):
        for replica in range(2):
            offset=(j*2+replica)%len(lanes);order=lanes[offset:]+lanes[:offset]
            for lane in order:
                r=search(b,u,97000+j*2+replica,attempt_limit=8000,seconds=6,
                         policy=policy if '+RL' in lane else None,proposer=proposers[lane])
                r.update(problem=b.identity,lane=lane,replica=replica);results.append(r);gc.collect()
                print('eval',b.identity,replica,lane,r['status'],round(r['seconds'],3),r['attempted_base_placements'],flush=True)
    # Deterministic finite work controls remove wall-cutoff differences. Compare
    # the exact semantic trace/counters even when the exploration is unresolved.
    controls=[];control_cached=compiled.fork(128)
    for j,b in enumerate(evals):
        for use_rl in (False,True):
            pair=[]
            for lane,p in (('raw',raw),('cached',control_cached)):
                r=search(b,u,98000+j,attempt_limit=200,seconds=None,policy=policy if use_rl else None,proposer=p)
                r.update(problem=b.identity,lane=lane,use_rl=use_rl);pair.append(r)
            fields=('status','nodes','branches','forced','backtracks','attempted_base_placements','explored_macro_constituents','state','execution')
            assert all(pair[0][field]==pair[1][field] for field in fields)
            controls.append({'problem':b.identity,'use_rl':use_rl,'fields':fields,'results':pair,'equivalent':True})
            print('control',b.identity,use_rl,pair[0]['status'],'equal',flush=True)
    movable=[]
    for lane in ('base','raw','cached','raw+RL','cached+RL'):
        t0=time.monotonic();attempts=[];selected=None
        for i,b in enumerate(families()[0]):
            r=search(b,u,99000+i,seconds=6,policy=policy if '+RL' in lane else None,proposer=proposers[lane])
            attempts.append({'boundary':b.identity,'result':r})
            if r['status']=='finite_exact_region':selected=b.identity;break
        movable.append({'lane':lane,'selected':selected,'attempts':attempts,'seconds':time.monotonic()-t0})
        print('movable',lane,selected,flush=True)
    data={'date':datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),'sources':sources,
          'scope':'exact representation optimization of freshly learned local proposals; no GCTS marking, plane construction or proof-search result',
          'configuration':{'lanes':lanes,'base_attempts':8000,'seconds':6,'replicas':2,'proposal_limit':8,
                           'scheduler':'unchanged complete singleton graph; global dead, forced, earliest generation',
                           'cache_size':128,'controls':{'base_attempts':200,'seconds':None},'lane_order':'rotated by target and replica'},
          'inventory':{'seconds':u.seconds,'placements':len(u.keys)},'compilation':compiled.manifest,
          'training_problems':[b.packed() for b in train],'problems':[b.packed() for b in evals],
          'donors':donors,'donor_seconds':donor_seconds,'library':library,'mining':mining,'raw_proposer_build_seconds':raw.seconds,
          'training':{'seconds':training_seconds,'episodes':episodes,'updates':policy.updates,'weights':dict(policy.weights),
                      'initial_weights':{},'initial_marking':{},'saved_artifact_imported':False},
          'evaluation':results,'attempt_controls':controls,'movable_families':[[b.packed() for b in f] for f in families()],
          'movable_evaluation':movable,'total_seconds':time.monotonic()-start,
          'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'timing_provenance':'one sequential official process; cold compilation/learning charged; process peak is not per-lane allocation; controls have no wall limit'}
    (DOCS/'compiled-macros-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('saved',data['total_seconds'],flush=True)

if __name__=='__main__':main()
