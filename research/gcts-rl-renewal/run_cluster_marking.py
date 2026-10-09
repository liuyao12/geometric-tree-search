"""Own-level cluster failure marking pilot, with fresh label and RL oracles."""
import dataclasses,gc,hashlib,json,resource,time
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
from turtle import Model,Policy,SYMMETRIES,transform,compose
from cluster_tiles import ClusterModel,ClusterState,compose_type,verify_state
from cluster_learning import catalog,pair_expansion,corona,Encoder,decorated,all_disagreements
from region_tiles import search
from run_regions import HERE,DOCS,load_types,problems

def mixed(t):
    def hand(o):
        p=SYMMETRIES[o][1];return sum(p[i]>p[j] for i in range(3) for j in range(i+1,3))%2
    return len({hand(o) for o,tr in t.expansion})>1

def selected_types():
    types=load_types();prototype=min((t for t in types if t.level==1 and mixed(t)),key=lambda t:(len(t.expansion),t.identity))
    return next(t for t in types if t.identity=='base'),prototype

def main():
    start=time.monotonic();single,prototype=selected_types();plain=ClusterModel([prototype]);contacts=catalog(prototype)
    encoder=Encoder(prototype,0);samples=[];base=Model();label_start=time.monotonic()
    local=HERE/'results';local.mkdir(exist_ok=True)
    for i,k in enumerate(contacts):
        if i and i%70==0:base=Model();gc.collect()
        seeds=pair_expansion(plain,k);r=corona(base,seeds,2000,5)
        if r['status']=='unresolved':
            prior=r;r=corona(base,seeds,20000,30);r['prior_attempt']=prior
        r['second']=k;samples.append(r);encoder.add(r)
        if (i+1)%30==0 or i+1==len(contacts):
            print('cluster labels',i+1,'of',len(contacts),dict(Counter(s['status'] for s in samples)),flush=True)
            (local/'cluster-marking-001-labels.json').write_text(json.dumps(samples,separators=(',',':'))+'\n')
    marking,statistics=encoder.finish();label_seconds=time.monotonic()-label_start
    rejected=all_disagreements(prototype,marking);by_key={s['second']:s for s in samples}
    proof_eligible=(bool(marking) and rejected<=by_key.keys() and all(by_key[k]['status']=='negative' for k in rejected))
    # Publication/activation still requires a separate independent proof replay.
    statistics['all_disagreements_are_labeled_negative']=proof_eligible
    print('learned',statistics['assigned'],'assigned;',statistics['negative_rejected'],'negative exclusions;',len(rejected),'all possible disagreements',flush=True)
    marked=decorated(prototype,marking);training,evaluation=problems();policy=Policy();episodes=[];t0=time.monotonic()
    for i in range(24):
        b,_=training[i%len(training)];r=search([single,prototype],b,31000+i,node_limit=500,seconds=3,policy=policy,learn=True,rollout=True)
        r['problem']=b.identity;episodes.append(r);gc.collect()
    training_seconds=time.monotonic()-t0;results=[]
    for i,(b,meta) in enumerate(evaluation):
        for lane,typ,p in [('unmarked',prototype,None),('GCTS',marked,None),('RL',prototype,policy),('GCTS+RL',marked,policy)]:
            r=search([single,typ],b,32000+i,node_limit=10000,seconds=10,policy=p)
            r.update(problem=b.identity,lane=lane);results.append(r);gc.collect()
            print(b.identity,lane,r['status'],round(r['seconds'],3),'s',flush=True)
    # A searched positive assembly inherits the new channel at its next level.
    parent=None;parent_checks=0
    positive=next((s for s in samples if s['status']=='positive'),None)
    if positive:
        parent=compose_type(ClusterModel([marked]),'marked-cluster-parent',[(prototype.identity,0,(0,0,0)),positive['second']])
        pm=ClusterModel([marked,parent])
        for o in range(12):
            s=ClusterState();s.place(pm.placement((parent.identity,o,(0,0,0))),seed=True);assert verify_state(pm,s);parent_checks+=1
    data={'date':datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),
          'scope':'own-level cluster marking from complete unmarked base extension tests; finite region pilot; independent redundancy replay pending',
          'reuse':{'artifact':'cluster-types-001.json','sha256':hashlib.sha256((DOCS/'cluster-types-001.json').read_bytes()).hexdigest(),
                   'imported':'one searched mixed-handed two-tile shape and unmarked singleton only; no marking, policy, substitution or known tiling witness',
                   'selection':'minimum size then identity among mixed-handed level-one types'},
          'configuration':{'prototype':dataclasses.asdict(prototype),'catalog_count':len(contacts),'marking_radius':0,'marking_channel':'cluster:1',
                           'label_oracle':'unmarked base inventory, all 12 orientations and all support alignments; global dead/forced/earliest-generation',
                           'label_node_limit':2000,'label_seconds':5,'retry_node_limit':20000,'retry_seconds':30,'cache_reset_every_contacts':70,
                           'evaluation_node_limit':10000,'evaluation_seconds':10,'training_seeds':list(range(31000,31024)),'evaluation_seeds':list(range(32000,32006))},
          'labels':{'samples':samples,'seconds':label_seconds,'counts':dict(Counter(s['status'] for s in samples))},
          'marking':statistics,'marking_for_inspection_only':sorted(marking.items()),'canonical_disagreements':sorted(rejected),
          'training':{'episodes':episodes,'seconds':training_seconds,'weights':dict(policy.weights),'updates':policy.updates,
                      'scope':'zero-start on unmarked two-type inventory; same frozen policy for both learned lanes; no marked oracle labels'},
          'problems':[{'boundary':b.packed(),'construction':meta} for b,meta in evaluation],'evaluation':results,
          'parent':dataclasses.asdict(parent) if parent else None,'parent_transformed_expansions_checked':parent_checks,
          'source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in HERE.glob('*.py')},
          'total_seconds':time.monotonic()-start,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
          'limits':['one reused prototype shape, not the complete 14-type library','one-corona positives are not infinite-extension proofs',
                    'finite region groupings can change under complete-tiling-redundant markings; all unmarked singleton paths retained',
                    'no plane construction, Penrose hierarchy or logic-kernel compiler produced']}
    (DOCS/'cluster-marking-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('wrote cluster-marking-001.json',round(data['total_seconds'],3),'s',flush=True)

if __name__=='__main__':main()
