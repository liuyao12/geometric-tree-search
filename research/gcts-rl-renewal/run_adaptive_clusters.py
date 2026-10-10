"""Fresh discovery, promotion, episodic RL and disjoint receptor evaluations."""
import hashlib
import json
import resource
import time
from pathlib import Path

import adaptive_receptor_clusters as C
import movable_proof_regions as M
import quantified_receptors as Q
import check_movable_regions as A
from serialized_kernel import canonical
from audit_serialized_kernel import replay

HERE=Path(__file__).resolve().parent
DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'


def atom(s):return ('pred',s,())
def implication(a,b):return ('imp',a,b)


def case(name,n,bound,compound=False,distractors=0):
    atoms=[atom(name+'-'+str(j)) for j in range(n+1)]
    if compound:
        atoms=[('and',a,('not',atom(name+'-side'))) if j%2==0
               else implication(atom(name+'-side'),a) for j,a in enumerate(atoms)]
    h=[atoms[0]]+[implication(a,b) for a,b in zip(atoms,atoms[1:])]
    for j in range(distractors):
        a=atom(name+'-decoy-'+str(j))
        h.extend([implication(atoms[j%n],a),implication(a,atoms[(j+1)%n])])
    symbols=set()
    def collect(a):
        if a[0]=='pred':symbols.add(a[1])
        elif a[0] in ('imp','and','or','not'):
            for b in a[1:]:collect(b)
    for a in h:collect(a)
    return dict(id=name,bound=bound,target=atoms[-1],hypotheses=h,
                theory=dict(functions={},predicates={s:0 for s in sorted(symbols)},axioms={},schemas=[]),
                terms=(),variables=(),rounds=0,generalization_rounds=0)


def inventory(spec):
    return Q.inventory(spec['theory'],spec['hypotheses'],spec['terms'],spec['variables'],
                       spec['rounds'],generalization_rounds=spec['generalization_rounds'])


def decorate(spec,catalog,result):
    if result['proof'] is None:return
    start=time.perf_counter()
    result['tiles']=[dict(key=k,occupancy=p.occupancy,marks=p.marks)
                     for k in result['placements']
                     for p in [M.Model(catalog,spec['target'],spec['bound'],spec['hypotheses']).placement(k)]]
    result['point_check']=A.certificate(catalog['rules'],spec,result,result['tiles'])
    result['compiled']=M.compile_region(result['proof'],spec['target'],spec['hypotheses'],spec['theory'])
    if replay(canonical(result['compiled']['request']))['status']!='accepted':raise ValueError('independent logical check')
    result['deduction_scope']='Direct sequent checked with every hypothesis explicitly bound as a premise axiom; no expanded discharge certificate.'
    result['positive_check_seconds']=time.perf_counter()-start


def run(spec,library=(),mode='base',weights=None,stochastic=False,seed=0,attempts=5000):
    started=time.perf_counter();catalog=inventory(spec);grammar=time.perf_counter()-started
    model=M.Model(catalog,spec['target'],spec['bound'],spec['hypotheses'])
    result=C.search(model,library,mode,weights,stochastic,seed,attempts=attempts,seconds=5)
    result['grammar_seconds']=grammar
    decorate(spec,catalog,result)
    return catalog,result


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    began=time.perf_counter()
    names=('adaptive_receptor_clusters.py','run_adaptive_clusters.py','movable_proof_regions.py',
           'quantified_receptors.py','check_movable_regions.py','check_quantified_receptors.py',
           'logic.py','turtle.py','serialized_kernel.py','audit_serialized_kernel.py','proof_clusters.py')
    pins={n:digest(HERE/n) for n in names}
    first=case('donor-four',4,4)
    c,r=run(first)
    library=C.promote(first,c,r,maximum=4)
    print('donor',r['metrics'],[len(t['pattern']) for t in library],flush=True)
    second=case('donor-six',6,6)
    c2,r2=run(second,library,'fixed')
    new=C.promote(second,c2,r2,library,maximum=6)
    library.extend(new)
    print('hierarchy',r2['metrics'],[(len(t['pattern']),t['level']) for t in library],flush=True)
    donor_seconds=time.perf_counter()-began
    training_specs=[case('train-'+str(i),n,n+1,distractors=i%2) for i,n in enumerate((2,3,4,5))]
    weights=[0.0]*len(C.FEATURES);baseline=0.0;episodes=[]
    start=time.perf_counter()
    for epoch in range(6):
        for j,spec in enumerate(training_specs):
            catalog,result=run(spec,library,'policy',weights,True,2800+epoch*4+j,attempts=1000)
            next_weights,baseline_next,update=C.update(weights,baseline,result)
            episodes.append(dict(spec=spec,catalog=catalog,result=result,update=update,
                                 weights_before=weights,baseline_after=baseline_next))
            weights,baseline=next_weights,baseline_next
    training_seconds=time.perf_counter()-start
    print('policy',weights,'training',training_seconds,flush=True)
    evaluation_specs=[case('heldout-seven',7,8),case('heldout-compound',4,6,True),
                      case('heldout-distractors',5,6,distractors=2),case('heldout-two',2,5,True),
                      case('too-small',4,2),case('missing-link',3,4)]
    evaluation_specs[-1]['hypotheses'].pop(2)
    cases=[]
    for spec in evaluation_specs:
        runs={};catalog=None
        for mode,params in (('base',{}),('fixed',{}),('zero',dict(weights=[0.0]*len(C.FEATURES))),
                            ('rl',dict(weights=weights))):
            catalog,result=run(spec,library,'policy' if mode in ('zero','rl') else mode,**params,attempts=20000)
            runs[mode]=result
        saturation_start=time.perf_counter()
        saturation_catalog=inventory(spec)
        saturation_model=M.Model(saturation_catalog,spec['target'],spec['bound'],spec['hypotheses'])
        sat=Q.saturation(saturation_model)
        if sat['proof']:
            sat['check']=A.A.proof(sat['proof'],spec['target'],spec['hypotheses'],spec['theory'])
            sat['fits_region_bound']=len(sat['proof'])<=spec['bound']
            if sat['fits_region_bound']:
                h=len(spec['hypotheses']);known={i:a for i,a in enumerate(spec['hypotheses'],-h)}
                keys=[]
                for j,row in enumerate(sat['proof']):
                    rid=next(i for i,r in enumerate(saturation_catalog['rules'])
                             if r['kind']==row['kind'] and r['output']==row['formula']
                             and r['parameters']==row['parameters']
                             and list(r['inputs'])==[known[v] for v in row['refs']])
                    keys.append((j,rid,row['refs']));known[j]=row['formula']
                endpoint=len(keys)
                keys.extend([(endpoint,M.END,())]+[(j,M.PAD,()) for j in range(endpoint+1,spec['bound']+1)])
                certificate=dict(status='finite_exact_proof_region',placements=keys,tile_generations=[1]*len(keys),
                                 endpoint=endpoint,proof=sat['proof'])
                decorate(spec,saturation_catalog,certificate)
                sat['region_certificate']=certificate
        sat['total_seconds']=time.perf_counter()-saturation_start
        cases.append(dict(spec=spec,catalog=catalog,runs=runs,saturation=sat))
        print(spec['id'],{k:(v['status'],v['metrics'].get('attempts'),v['metrics'].get('accepted_transactions',0)) for k,v in runs.items()},flush=True)
    out=dict(version='adaptive-clusters-001',sources=pins,donors=[dict(spec=first,catalog=c,result=r),dict(spec=second,catalog=c2,result=r2)],
             library=library,donor_seconds=donor_seconds,training=dict(specs=training_specs,episodes=episodes,
             weights=weights,baseline=baseline,seconds=training_seconds,initial_weights=[0.0]*len(C.FEATURES),features=C.FEATURES),
             cases=cases,seconds=time.perf_counter()-began,
             peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
             scope='Fresh bounded MP proofs and capacity-preserving adaptive formula families. '
                   'Semantic point cells, complete unchanged graph, scheduler-checked transactions, full fallback. '
                   'No learned pruning, quantifier cluster discovery or new native Wang execution.')
    if any(digest(HERE/n)!=pin for n,pin in pins.items()):raise ValueError('measured source changed')
    (DOC/'adaptive-clusters-001.json').write_bytes(canonical(out)+b'\n')
    print('complete',out['seconds'],flush=True)


if __name__=='__main__':main()
