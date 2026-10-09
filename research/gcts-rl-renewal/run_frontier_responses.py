"""Sequential practical-region controls after the duplicate-prefix diagnosis."""
import gc,hashlib,json,resource,time
from pathlib import Path
from turtle import Policy
from boundary_macros import singleton
from boundary_responses import declarations,Atlas,search as legacy
from response_resolution import training_boundaries
from resident_regions import Universe
from frontier_responses import search

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
SOURCES=('frontier_responses.py','run_frontier_responses.py','boundary_responses.py','response_resolution.py',
         'boundary_macros.py','resident_regions.py','region_tiles.py','cluster_tiles.py','turtle.py','spatial.py','coverage.py')
LANES=('legacy-base','legacy-hierarchy','unique-base','unique-small','unique-hierarchy','frontier-zero','frontier-RL')

def main():
    start=time.monotonic();path=DOCS/'boundary-responses-001.json';parent=json.loads(path.read_text())
    data={'source_artifact':path.name,'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES},
          'scope':'adaptive engineering follow-up on the earlier six authored targets; new seeds, not independent boundary generalization',
          'training':{'initial_weights':{},'initial_marking':{},'policy_imported':False,'episodes':[]},'evaluation':[],'controls':[]}
    evals=declarations();u=Universe((singleton(),),evals[0].allowed)
    atlases={'small':Atlas(parent['library'],u,max_size=4),'hierarchy':Atlas(parent['library'],u)}
    data['inventory']={'seconds':u.seconds,'placements':len(u.keys)};data['atlases']={m:a.manifest for m,a in atlases.items()}
    train=training_boundaries(u.allowed);data['training_problems']=[b.packed() for b in train];data['problems']=[b.packed() for b in evals]
    def save():
        data['total_seconds']=time.monotonic()-start;data['peak_process_memory_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (DOCS/'frontier-responses-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    # Equal finite-work controls do not rely on a wall-clock cutoff.
    for i,b in enumerate(evals[:3]):
        a=legacy(b,u,seed=130000+i,attempt_limit=60,seconds=None)
        c=search(b,u,atlases,seed=130000+i,attempt_limit=60,seconds=None,fixed_mode='base')
        fields=('status','state','execution','attempted_base_placements','nodes','branches','forced','backtracks')
        assert all(a[f]==c[f] for f in fields)
        data['controls'].append({'kind':'base-path','problem':b.identity,'fields':fields,'results':[a,c]})
        a=search(b,u,atlases,seed=130020+i,attempt_limit=60,seconds=None)
        c=search(b,u,atlases,seed=130020+i,attempt_limit=60,seconds=None,policy=Policy())
        assert all(a[f]==c[f] for f in fields)
        data['controls'].append({'kind':'zero-policy-path','problem':b.identity,'fields':fields,'results':[a,c]})
    policy=Policy();t0=time.monotonic()
    for i in range(48):
        b=train[i%len(train)];r=search(b,u,atlases,130100+i,attempt_limit=300,seconds=1.5,policy=policy,learn=True,rollout=True)
        r['problem']=b.identity;data['training']['episodes'].append(r)
        print('frontier-train',i,r['status'],round(r['seconds'],3),r['stats'].get('response_starts',0),flush=True)
    data['training'].update(seconds=time.monotonic()-t0,weights=dict(policy.weights),baseline=policy.baseline,updates=policy.updates)
    save()
    for j,b in enumerate(evals):
        for replica in range(2):
            offset=(j*2+replica)%len(LANES);order=LANES[offset:]+LANES[:offset]
            for lane in order:
                seed=131000+j*2+replica
                if lane.startswith('legacy'):
                    r=legacy(b,u,seed,seconds=5,atlas=atlases['hierarchy'] if lane.endswith('hierarchy') else None)
                else:
                    mode=lane.split('-')[1] if lane.startswith('unique') else None
                    r=search(b,u,atlases,seed,seconds=5,fixed_mode=mode,policy=policy if lane=='frontier-RL' else None)
                r.update(problem=b.identity,lane=lane,replica=replica);data['evaluation'].append(r)
                print('frontier-eval',b.identity,replica,lane,r['status'],round(r['seconds'],3),r['attempted_base_placements'],flush=True)
                save();gc.collect()
    data['configuration']={'base_attempts':4000,'seconds':5,'replicas':2,'training_episodes':48,
        'training_seconds_per_episode':1.5,'training_base_attempts':300,'training_rollout':True,
        'learning':'zero-start REINFORCE of current-frontier modes and response ordering; verified coverage/completion minus real attempts and elapsed cost',
        'lane_order':'rotated, sequential; all lanes keep full base domains and the global scheduler',
        'timing_scope':'search includes boundary binding, graph construction and proposals; frozen envelope and atlas construction charged separately; reused donor/mining costs in parent artifact',
        'fairness':'unique traversal changes macro branching granularity/order, so hierarchy comparison is not a same-path caching ablation; all singleton alternatives survive full evaluation'}
    save();print('saved-frontier',round(data['total_seconds'],3),flush=True)

if __name__=='__main__':main()
