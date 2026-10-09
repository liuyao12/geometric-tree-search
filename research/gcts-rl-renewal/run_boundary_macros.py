"""Matched cold local-learning and held-out boundary-macro experiment."""
import gc,hashlib,json,resource,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from turtle import Policy,add
from resident_regions import Universe
from region_tiles import Boundary
from coverage import hexagon
from boundary_macros import singleton,problems,mine,Proposer,search

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
SOURCES=('boundary_macros.py','run_boundary_macros.py','resident_regions.py','region_tiles.py',
         'cluster_tiles.py','spatial.py','coverage.py','turtle.py')

def families():
    allowed=problems()[0].allowed;core=frozenset(hexagon(4))
    return ((Boundary('movable-edge',frozenset({(14,-7,-7)}),allowed),
             Boundary('movable-shift',frozenset(add(p,(2,-2,0)) for p in core),allowed),
             Boundary('movable-center',core,allowed)),)

def main():
    start=time.monotonic();sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES}
    training=problems(True);evaluation=problems();u=Universe((singleton(),),training[0].allowed)
    donors=[];t0=time.monotonic()
    for i in range(8):
        b=training[i%4];r=search(b,u,91000+i,seconds=3);r['problem']=b.identity;donors.append(r)
        print('donor',i,r['status'],round(r['seconds'],3),flush=True)
    donor_seconds=time.monotonic()-t0;library,mining=mine(donors,u.model);proposer=Proposer(library)
    policy=Policy();episodes=[];t0=time.monotonic()
    for i in range(24):
        b=training[i%4];r=search(b,u,92000+i,attempt_limit=500,seconds=3,policy=policy,proposer=proposer,learn=True,rollout=True)
        r['problem']=b.identity;episodes.append(r)
        print('train',i,r['status'],round(r['seconds'],3),flush=True)
    training_seconds=time.monotonic()-t0;results=[];lanes=['base','base+RL','macro','macro+RL']
    def run(b,lane,seed):
        return search(b,u,seed,attempt_limit=8000,seconds=6,policy=policy if '+RL' in lane else None,
                      proposer=proposer if lane.startswith('macro') else None)
    for j,b in enumerate(evaluation):
        for replica in range(2):
            # Rotate order to reduce a fixed late-lane/cache advantage.
            order=lanes[(j+replica)%4:]+lanes[:(j+replica)%4]
            for lane in order:
                r=run(b,lane,93000+j*2+replica);r.update(problem=b.identity,lane=lane,replica=replica)
                results.append(r);gc.collect()
                print('eval',b.identity,replica,lane,r['status'],round(r['seconds'],3),r['attempted_base_placements'],flush=True)
    movable=[]
    for j,family in enumerate(families()):
        for lane in lanes:
            t0=time.monotonic();attempts=[];selected=None
            for k,b in enumerate(family):
                r=run(b,lane,94000+j*3+k);attempts.append({'boundary':b.identity,'result':r})
                if r['status']=='finite_exact_region':selected=b.identity;break
            movable.append({'family':j,'lane':lane,'selected':selected,'attempts':attempts,'seconds':time.monotonic()-t0,
                            'status':'finite_exact_movable_region' if selected else 'unresolved_finite_family'})
            print('movable',lane,selected,round(time.monotonic()-t0,3),flush=True)
    data={'date':datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),'sources':sources,
          'scope':'fixed finite point regions and an explicit movable finite boundary family; no learned marking or plane claim',
          'configuration':{'base_attempts':8000,'seconds':6,'lanes':lanes,'replicas':2,'training_episodes':24,
                           'scheduler':'complete singleton graph: global dead, global forced, earliest generation then degree and point',
                           'proposal_limit':8,'macro_sizes':[2,3,4,5,6],'all_singletons_retained':True,
                           'negative_certificates_exported':False,'lane_order':'rotated by target and replica',
                           'cost':'same resident base inventory; requests include bind, graph, proposal validation and replay; cold reusable costs separate'},
          'inventory':{'seconds':u.seconds,'placements':len(u.keys),'types':[{'identity':t.identity,'expansion':t.expansion} for t in u.types]},
          'training_problems':[b.packed() for b in training],'problems':[b.packed() for b in evaluation],
          'donors':donors,'donor_seconds':donor_seconds,'library':library,'mining':mining,'proposer_build_seconds':proposer.seconds,
          'training':{'episodes':episodes,'seconds':training_seconds,'weights':dict(policy.weights),'updates':policy.updates,
                      'initial_weights':{},'initial_marking':{},'training_witness_imported':False},
          'evaluation':results,'movable_families':[[b.packed() for b in f] for f in families()],'movable_evaluation':movable,
          'total_seconds':time.monotonic()-start,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'timing_provenance':'one sequential official process; process peak, not per-lane allocation; cooperative cutoffs'}
    (DOCS/'boundary-macros-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('saved',data['total_seconds'],data['peak_process_memory_bytes'],flush=True)

if __name__=='__main__':main()
