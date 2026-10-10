"""Fresh controls: no supplied theorem proofs; exact independent replay."""
import copy, hashlib, json, resource, statistics, time
from pathlib import Path
from types import SimpleNamespace
import propositional_receptors as R
import check_propositional_receptors as A

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/research/gcts-rl-renewal/propositional-receptors-001.json'
def pin(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def timed(fn,repeats=80):
    costs=[];result=None
    for _ in range(repeats):
        start=time.perf_counter();result=fn();costs.append(time.perf_counter()-start)
    return dict(median_seconds=statistics.median(costs),minimum_seconds=min(costs),maximum_seconds=max(costs),repeats=repeats,result=result)
def inspect(model,result,library):
    if result['proof'] is None:return
    proof=result['proof'];t=time.perf_counter();logical=A.logical(A.frozen(proof),model.target,model.hypotheses)
    result['logical_check_seconds']=time.perf_counter()-t;result['primitive_lines']=logical['primitive_lines']
    result['proof_tex']=[R.tex(row['formula']) for row in proof]
    if result.get('placements') is not None:
        tiles=[dict(key=k,occupancy=model.placement(k).occupancy,marks=model.placement(k).marks) for k in result['placements']]
        initial=sorted(model.initial().marks.items());t=time.perf_counter()
        result['independent']=A.certificate(model.catalog,model.target,model.length,model.hypotheses,result['placements'],tiles,library)
        result['full_check_seconds']=time.perf_counter()-t
        result['point_tiles']=tiles;result['initial_marks']=initial
        result['checking_costs']=dict(sparse_agreement=timed(lambda:A.sparse(initial,tiles,model.length)),
                                     logical_expansion=timed(lambda:{k:v for k,v in A.logical(proof,model.target,model.hypotheses).items() if k!='expanded'}))

def main():
    start=time.perf_counter();base=R.basis();pool_pin=hashlib.sha256(json.dumps(base,sort_keys=True).encode()).hexdigest()
    source_names=['propositional_receptors.py','check_propositional_receptors.py','run_propositional_receptors.py','test_propositional_receptors.py','turtle.py']
    sources={n:pin(Path(__file__).parent/n) for n in source_names}
    data=dict(version='propositional-receptors-1',sources=sources,basis=base,basis_sha256=pool_pin,
              initial_library=[],authored_proofs=[],cases=[],scope='bounded positional finite-alphabet proof-cell adapter; not a finite translation-invariant literal inventory')
    # A fresh graph search provides the proof promoted below. No proof is authored.
    t=time.perf_counter();donor_model=R.Model(base,R.imp(R.P,R.P),5);build=time.perf_counter()-t
    donor=R.search(donor_model,seconds=25);donor['build_seconds']=build;inspect(donor_model,donor,())
    if donor['proof'] is None:raise ValueError('identity donor search did not finish')
    family=R.family_from_discovery(donor['proof']);library=(family,);data['discovered_family']=family;data['donor']=donor
    # RL trains only on Q identity. P identity is the separate family discovery
    # donor, but is absent from RL training. Renaming is a weak transfer test.
    t=time.perf_counter();training_model=R.Model(base,R.imp(R.Q,R.Q),5);training_build=time.perf_counter()-t
    training=R.train(training_model,episodes=24);training['build_seconds']=training_build;data['training']=training
    specs=[
        dict(id='identity-P',title='Identity',target=R.imp(R.P,R.P),length=5,hypotheses=(),library=False),
        dict(id='identity-composite',title='Identity of an implication',target=R.imp(R.imp(R.P,R.Q),R.imp(R.P,R.Q)),length=5,hypotheses=(),library=False),
        dict(id='weakening',title='Weakening',target=R.imp(R.P,R.imp(R.Q,R.P)),length=1,hypotheses=(),library=False),
        dict(id='two-premise-links',title='Two successive premise connections',target=R.imp(R.P,R.Q),length=2,hypotheses=(R.Q,R.imp(R.Q,R.P),R.imp(R.P,R.imp(R.P,R.Q))),library=False),
        dict(id='contraposition',title='Classical contraposition',target=R.imp(R.P,R.Q),length=2,hypotheses=(R.imp(R.neg(R.Q),R.neg(R.P)),),library=False),
        dict(id='family-composite',title='Discovered identity family on an implication',target=R.imp(R.imp(R.P,R.Q),R.imp(R.P,R.Q)),length=1,hypotheses=(),library=True),
        dict(id='family-weakening',title='Compose a discovered lemma with weakening',target=R.imp(R.P,R.imp(R.Q,R.Q)),length=3,hypotheses=(),library=True),
        dict(id='primitive-weakening',title='Same conclusion using primitive rules',target=R.imp(R.P,R.imp(R.Q,R.Q)),length=7,hypotheses=(),library=False),
        dict(id='closed-P-one-slot',title='Exhausted one-slot control',target=R.P,length=1,hypotheses=(),library=False)]
    for spec in specs:
        cat=R.catalog(base,library if spec['library'] else ());lib=library if spec['library'] else ()
        case=dict(spec,target_tex=R.tex(spec['target']),hypotheses_tex=[R.tex(a) for a in spec['hypotheses']],rules=len(cat['rules']),runs={})
        for lane in ('point','point-rl'):
            t=time.perf_counter();m=R.Model(cat,spec['target'],spec['length'],spec['hypotheses']);build=time.perf_counter()-t
            if spec['id']=='identity-P' and lane=='point':r=copy.deepcopy(donor);r['reused_donor_measurement']=True
            else:r=R.search(m,node_limit=6000,seconds=12,policy_weights=training['weights'] if lane=='point-rl' else None)
            r['build_seconds']=build;inspect(m,r,lib);case['runs'][lane]=r
        descriptor=SimpleNamespace(catalog=cat,target=spec['target'],length=spec['length'],hypotheses=spec['hypotheses'])
        symbolic=R.chronological(descriptor,node_limit=6000,seconds=12)
        if symbolic['proof'] is not None:
            symbolic['independent_logical']=A.logical(symbolic['proof'],spec['target'],spec['hypotheses']);symbolic['primitive_lines']=symbolic['independent_logical']['primitive_lines']
        case['runs']['chronological']=symbolic
        saturation=R.forward(cat,spec['target'],spec['hypotheses'])
        if saturation['proof'] is not None:
            saturation['independent_logical']=A.logical(saturation['proof'],spec['target'],spec['hypotheses']);saturation['primitive_lines']=saturation['independent_logical']['primitive_lines']
            saturation['fits_slot_bound']=len(saturation['proof'])<=spec['length']
        case['runs']['saturation']=saturation;data['cases'].append(case)
        print(spec['id'],[(k,v['status'],round(v['seconds'],4)) for k,v in case['runs'].items()],flush=True)
    data['seconds']=time.perf_counter()-start;data['peak_process_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    data['rl_total_training_seconds']=training['seconds']+training_build
    OUT.write_text(json.dumps(data,indent=2)+'\n');print('wrote',OUT,'seconds',round(data['seconds'],3),flush=True)

if __name__=='__main__':main()
