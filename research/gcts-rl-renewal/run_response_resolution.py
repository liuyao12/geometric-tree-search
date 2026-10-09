"""Adaptive follow-up: fresh full-search training and paired request controls."""
import gc,hashlib,json,resource,time
from pathlib import Path
from turtle import Policy
from boundary_macros import singleton
from boundary_responses import declarations,Atlas,search
from response_resolution import training_boundaries,request
from resident_regions import Universe

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def main():
    start=time.monotonic();p=DOCS/'boundary-responses-001.json';source_sha=hashlib.sha256(p.read_bytes()).hexdigest();parent=json.loads(p.read_text())
    data={'source_artifact':'boundary-responses-001.json','source_sha256_before_audit':source_sha,
          'library_sha256':hashlib.sha256(json.dumps(parent['library'],separators=(',',':')).encode()).hexdigest(),
          'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('response_resolution.py','run_response_resolution.py','boundary_responses.py','turtle.py')},
          'scope':'adaptive follow-up after observing move-ranking failures; fresh full-search training; finite request-level proposal resolution, not held-out mathematical generalization',
          'training':{'episodes':[],'initial_weights':{},'initial_policy_imported':False},'evaluation':[]}
    evals=declarations();u=Universe((singleton(),),evals[0].allowed)
    atlases={'small':Atlas(parent['library'],u,max_size=4),'hierarchy':Atlas(parent['library'],u)}
    train=training_boundaries(u.allowed);data['training_problems']=[b.packed() for b in train];data['problems']=[b.packed() for b in evals]
    data['inventory_seconds']=u.seconds;data['atlas_build_seconds']=sum(a.seconds for a in atlases.values());policy=Policy()
    def save():
        data['total_seconds']=time.monotonic()-start;data['peak_process_memory_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (DOCS/'response-resolution-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    t0=time.monotonic()
    for i in range(42):
        b=train[i%len(train)];r=request(b,u,atlases,policy,120000+i,learn=True,seconds=3)
        r['problem']=b.identity;data['training']['episodes'].append(r)
        print('resolution-train',i,r['mode'],r['result']['status'],round(r['total_request_seconds'],3),flush=True)
    data['training'].update(seconds=time.monotonic()-t0,weights=dict(policy.weights),baseline=policy.baseline,updates=policy.updates)
    save();lanes=('base','resolution+zero','resolution+RL')
    for j,b in enumerate(evals):
        for replica in range(2):
            offset=(j*2+replica)%3;order=lanes[offset:]+lanes[:offset]
            for lane in order:
                seed=121000+j*2+replica
                if lane=='base':
                    t0=time.monotonic();r=search(b,u,seed);row={'mode':'base','total_request_seconds':time.monotonic()-t0,'result':r}
                else:row=request(b,u,atlases,policy,seed,zero=lane.endswith('+zero'))
                row.update(problem=b.identity,lane=lane,replica=replica);data['evaluation'].append(row);save();gc.collect()
                print('resolution-eval',b.identity,replica,lane,row['mode'],row['result']['status'],round(row['total_request_seconds'],3),flush=True)
    data['configuration']={'base_attempts':4000,'seconds':6,'training_episodes':42,'training_seconds_per_episode':3,
                           'learning':'one-decision REINFORCE on whole-request verified completion and elapsed cost',
                           'zero_control':'uniform seeded tie among three modes, no learned weights',
                           'lane_order':'rotated, one sequential process; different seeds from main response experiment'}
    data['timing_scope']='new sequential follow-up process; atlas explicitly reused; universe/build/reused donor/mining and new RL costs remain separate; no audit ran concurrently'
    save();print('saved-resolution',data['total_seconds'],flush=True)

if __name__=='__main__':main()
