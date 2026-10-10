"""Fresh resumable families, one completed hierarchy and on-policy learning."""
import hashlib,resource,time
from pathlib import Path
import resumable_clusters as R
import adaptive_receptor_clusters as C
import movable_proof_regions as M
import quantified_receptors as Q
import check_movable_regions as A
from resumable_cases import registry
from run_adaptive_clusters import inventory
from compact_contexts import compile_request
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
SOURCES=('run_resumable_clusters.py','resumable_clusters.py','resumable_cases.py','adaptive_receptor_clusters.py',
    'movable_proof_regions.py','quantified_receptors.py','check_movable_regions.py','check_quantified_receptors.py',
    'compact_contexts.py','compact_context_cases.py','quantified_receptor_cases.py','run_adaptive_clusters.py',
    'logic.py','turtle.py','serialized_kernel.py','audit_serialized_kernel.py','proof_clusters.py')

def decorate(spec,catalog,result):
    if result['proof'] is None:return
    start=time.perf_counter();m=M.Model(catalog,spec['target'],spec['bound'],spec['hypotheses'])
    result['tiles']=[dict(key=k,occupancy=m.placement(k).occupancy,marks=m.placement(k).marks) for k in result['placements']]
    result['point_check']=A.certificate(catalog['rules'],spec,result,result['tiles'])
    result['compact']=compile_request(result['proof'],spec['target'],spec['hypotheses'],spec['theory'])
    result['positive_check_seconds']=time.perf_counter()-start

def run(spec,library=(),mode='base',weights=None,stochastic=False,seed=0,attempts=50000):
    began=time.perf_counter();cat=inventory(spec);grammar=time.perf_counter()-began
    m=M.Model(cat,spec['target'],spec['bound'],spec['hypotheses'])
    if mode=='atomic':
        result=C.search(m,library,'policy',R.FIXED_WEIGHTS,False,seed,attempts=attempts,seconds=10,proposal_limit=32)
    else:result=R.search(m,library,mode,weights,stochastic,seed,attempts=attempts,seconds=10)
    result['grammar_seconds']=grammar;decorate(spec,cat,result)
    result['total_seconds']=time.perf_counter()-began
    return cat,result

def control(spec,kind):
    started=time.perf_counter();cat=inventory(spec);m=M.Model(cat,spec['target'],spec['bound'],spec['hypotheses'])
    result=M.chronological(m,node_limit=50000,seconds=10) if kind=='chronological' else Q.saturation(m)
    if result['proof'] is not None:
        result['fits_region_bound']=len(result['proof'])<=spec['bound']
        result['source_check']=A.A.proof(result['proof'],spec['target'],spec['hypotheses'],spec['theory'])
        if result['fits_region_bound']:
            known={i:a for i,a in enumerate(spec['hypotheses'],-len(spec['hypotheses']))};keys=[]
            for j,row in enumerate(result['proof']):
                rid=next(i for i,r in enumerate(cat['rules']) if r['kind']==row['kind'] and r['output']==row['formula']
                    and r['parameters']==row['parameters'] and list(r['inputs'])==[known[v] for v in row['refs']])
                keys.append((j,rid,row['refs']));known[j]=row['formula']
            end=len(keys);keys.extend([(end,M.END,())]+[(j,M.PAD,()) for j in range(end+1,spec['bound']+1)])
            witness=dict(status='finite_exact_proof_region',placements=keys,tile_generations=[1]*len(keys),endpoint=end,proof=result['proof'])
            decorate(spec,cat,witness);result['region_certificate']=witness
    result['total_seconds']=time.perf_counter()-started
    return result

def main():
    began=time.perf_counter();pins={n:digest(HERE/n) for n in SOURCES};ds,ts,es=registry();donors=[];library=[]
    for spec in ds:
        cat,result=run(spec,library,'fixed' if library else 'base')
        if result['proof'] is None:raise ValueError('fresh donor not found')
        new=R.promote(spec,cat,result,library,maximum=5);library.extend(new)
        donors.append(dict(spec=spec,catalog=cat,result=result))
        print(spec['id'],result['metrics'],[(len(t['pattern']),t['level']) for t in new],flush=True)
    donor_seconds=time.perf_counter()-began;weights=[0.0]*len(R.FEATURES);baseline=0.;episodes=[];train_start=time.perf_counter()
    for epoch in range(6):
        for j,s in enumerate(ts):
            cat,r=run(s,library,'policy',weights,True,7800+epoch*len(ts)+j,attempts=10000)
            next_weights,next_baseline,update=R.update(weights,baseline,r)
            episodes.append(dict(spec=s,catalog=cat,result=r,weights_before=weights,baseline_after=next_baseline,update=update))
            weights,baseline=next_weights,next_baseline
    training_seconds=time.perf_counter()-train_start;print('trained',weights,training_seconds,flush=True)
    cases=[]
    for s in es:
        runs={};cat=None
        for lane,mode,w in (('base','base',None),('fixed','fixed',None),('zero','policy',[0.]*len(R.FEATURES)),('rl','policy',weights),('atomic','atomic',None)):
            cat,runs[lane]=run(s,library,mode,w)
        controls={k:control(s,k) for k in ('chronological','saturation')}
        cases.append(dict(spec=s,catalog=cat,runs=runs,controls=controls))
        print(s['id'],{k:(v['status'],v['metrics']['attempts'],v['metrics'].get('hint_resumed',0),len(v.get('solution_hints',()))) for k,v in runs.items()},flush=True)
    out=dict(version='resumable-clusters-001',sources=pins,donors=donors,library=library,donor_seconds=donor_seconds,
        training=dict(specs=ts,episodes=episodes,weights=weights,baseline=baseline,initial_weights=[0.]*len(R.FEATURES),features=R.FEATURES,seconds=training_seconds),
        cases=cases,seconds=time.perf_counter()-began,peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scope='Branch-local resumable ordering hints; one original placement per transition, complete unchanged graph and all fallback. '
              'Completed source families may become larger checked families. Fresh work-proxy RL, arithmetic and symbolic incidence controls. '
              'No new failure marking, native Wang execution, literal-tile search or general completeness/speed claim.')
    if any(digest(HERE/n)!=pin for n,pin in pins.items()):raise ValueError('measured source changed')
    (DOC/'resumable-clusters-001.json').write_bytes(canonical(out)+b'\n');print('complete',out['seconds'],flush=True)
if __name__=='__main__':main()
