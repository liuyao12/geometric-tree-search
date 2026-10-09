"""New-boundary factorial controls for parametric, reorderable local responses."""
import gc,hashlib,json,resource,time
from pathlib import Path
from turtle import Policy
from boundary_macros import singleton
from boundary_responses import declarations
from frontier_responses import search as prior_search
from conditional_clusters import CompiledAtlas,boundaries,moving_families,search,movable
from resident_regions import Universe

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
SOURCES=('conditional_clusters.py','run_conditional_clusters.py','frontier_responses.py','boundary_responses.py',
         'boundary_macros.py','resident_regions.py','region_tiles.py','cluster_tiles.py','turtle.py','spatial.py','coverage.py')
LANES=('base','trace-fixed','trace-adaptive','interval-fixed','interval-adaptive','interval-uniform','interval-RL')
def parameters(lane,policy):
    return {'condition':'trace' if lane.startswith('trace') else 'interval',
            'adaptive':not lane.endswith('fixed'),
            'fixed_mode':'base' if lane=='base' else None if lane in ('interval-uniform','interval-RL') else 'hierarchy',
            'policy':policy if lane=='interval-RL' else None}

def main():
    start=time.monotonic();source=DOCS/'boundary-responses-001.json';parent=json.loads(source.read_text())
    data={'source_artifact':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES},
        'scope':'new authored target shapes after the r20 diagnosis; exact analytic capacity generalization; fresh policy; sampled library explicitly reused',
        'training':{'initial_weights':{},'initial_marking':{},'policy_imported':False,'episodes':[]},
        'evaluation':[],'movable_evaluation':[],'controls':[]}
    train=boundaries(True);evals=boundaries();families=moving_families();u=Universe((singleton(),),evals[0].allowed);atlas=CompiledAtlas(parent['library'],u)
    data['inventory']={'seconds':u.seconds,'placements':len(u.keys)};data['atlas']=atlas.manifest
    data['interfaces']=[{'identity':r.identity,'delta':r.delta,'upper':tuple((p,12-v) for p,v in r.delta),'children':r.children,'level':r.level} for r in atlas.records.values()]
    data['training_problems']=[b.packed() for b in train];data['problems']=[b.packed() for b in evals];data['movable_families']=[[b.packed() for b in f] for f in families]
    def save():
        data['total_seconds']=time.monotonic()-start;data['peak_process_memory_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (DOCS/'conditional-clusters-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    fields=('status','state','attempted_base_placements','nodes','branches','forced','backtracks')
    for i,b in enumerate(declarations(True)[:2]):
        a=prior_search(b,u,{},140000+i,attempt_limit=40,seconds=None,fixed_mode='base')
        c=search(b,u,atlas,140000+i,attempt_limit=40,seconds=None,fixed_mode='base')
        assert all(a[f]==c[f] for f in fields)
        assert [(s['kind'],s['point'],s['placement']) for s in a['execution']]==[(s['kind'],s['point'],s['placement']) for s in c['execution']]
        data['controls'].append({'kind':'base-path','boundary':b.packed(),'fields':fields,'results':[a,c]})
    policy=Policy();t0=time.monotonic()
    for i in range(48):
        b=train[i%len(train)];r=search(b,u,atlas,140100+i,attempt_limit=300,seconds=1.5,policy=policy,learn=True,rollout=True)
        r['problem']=b.identity;data['training']['episodes'].append(r)
        print('conditional-train',i,r['status'],round(r['seconds'],3),r['stats'].get('reordered_constituents',0),flush=True)
    data['training'].update(seconds=time.monotonic()-t0,weights=dict(policy.weights),baseline=policy.baseline,updates=policy.updates);save()
    for j,b in enumerate(evals):
        for replica in range(2):
            offset=(2*j+replica)%len(LANES);order=LANES[offset:]+LANES[:offset]
            for lane in order:
                r=search(b,u,atlas,141000+2*j+replica,**parameters(lane,policy));r.update(problem=b.identity,lane=lane,replica=replica)
                data['evaluation'].append(r);save();gc.collect()
                print('conditional-eval',b.identity,replica,lane,r['status'],round(r['seconds'],3),r['stats'].get('reordered_constituents',0),flush=True)
    for j,family in enumerate(families):
        offset=j%len(LANES);order=LANES[offset:]+LANES[:offset]
        for lane in order:
            r=movable(family,u,atlas,141100+10*j,seconds=3,**parameters(lane,policy));r.update(family=j,lane=lane)
            data['movable_evaluation'].append(r);save();gc.collect()
            print('conditional-moving',j,lane,r['status'],len(r['attempts']),round(r['seconds'],3),flush=True)
    data['configuration']={'lanes':LANES,'base_attempts':4000,'fixed_seconds':5,'fixed_replicas':2,'movable_seconds_per_member':3,
        'movable_replicas':1,'proposal_scans':256,'offered_responses':8,'training_episodes':48,'training_seconds_per_episode':1.5,
        'training_base_attempts':300,'training_rollout':True,'learning':'fresh REINFORCE over current resolution and validated cluster preferences; original verified-coverage/cost reward',
        'comparison':'same compiled any-member proposal index and scan quota; trace/interval input conditions crossed with fixed/adaptive remaining order; all base keys retained',
        'timing':'rotated lanes in one sequential process; binding, complete graph and proposals charged; envelope, complete sampled-library pose compilation, reused donor/mining and fresh training separate; no concurrent audit/tests'}
    save();print('saved-conditional',round(data['total_seconds'],3),flush=True)

if __name__=='__main__':main()
