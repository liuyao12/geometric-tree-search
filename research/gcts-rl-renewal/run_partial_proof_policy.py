"""Matched zero-start complete-tree and partial-progress credit experiment."""
import hashlib,json,resource,time
from pathlib import Path
import partial_proof_policy as N,proof_clusters as H,proof_policy_problems as P
import audit_partial_proof_policy as V,audit_semantic_proofs as A
import semantic_proof_catalogs as C
from audit_serialized_kernel import freeze
from run_semantic_proofs import declaration
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-partial-policy')
SOURCES=('partial_proof_policy.py','run_partial_proof_policy.py','audit_partial_proof_policy.py','audit_proof_policy.py','audit_proof_clusters.py','audit_semantic_proofs.py','audit_serialized_kernel.py','audit_proof_compaction.py','audit_tree_kernel.py','proof_cluster_policy.py','proof_policy_problems.py','proof_clusters.py','proof_cluster_problems.py','semantic_proof_tiles.py','semantic_proof_catalogs.py','semantic_proof_problems.py','run_semantic_proofs.py','proof_block_search.py','turtle.py','logic.py','kernel_machine.py','serialized_kernel.py','tree_kernel.py','fol_checker.tree','tree_native.py','tree_runner.cpp')
def complete(c,p,r,library,code):
    if 'decoded' not in r:return {}
    h=H.hierarchical_certificate(c,r,p['length'],library);return dict(hierarchy=h,native=tree_native.check(canonical(h['request']),code,TMP,problem_hash(r['decoded']['request']),steps=100000000))
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);code=program();library=[];data=dict(sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES},initial_library=[],donors=[],training_catalogs=[],learners=[],evaluation=[],features=N.FEATURES,
      configuration=dict(seconds=5,base_attempts=50000,proposal_limit=8,index_instances=50000,seeds=[1,7,19],signals=['complete','local'],epochs=4,native_steps=100000000,rate=.2,weight_clip=6,baseline_decay=.9,online_prefix_gate=True),
      scope='Fresh donor searches and fragment mining; six zero-start learners, same eight training and ten withheld evaluation statements. Both signals save and independently replay every actually executed complete or open prefix before updating. Complete-tree control gives no unknown updates; local signal adds observed viable occupancy progress. All cutoffs remain unknown, without theorem labels or pruning.',
      comparison='Same instrumented primitive graph, scheduler, features, proposal pool and fallback; only training return changes between complete and local learners. All discovery, catalog, online replay, training, inference, validation, proof compilation and native costs exposed. Frozen evaluation includes base, fixed prior, zero weights and both learned policies.')
    data['compile_seconds']=tree_native.compile_tool(TMP);start=time.perf_counter()
    for p in P.donors():
        t=time.perf_counter();c=C.equational(p['theory'],p['target'],p['term_bound']);r=H.search(c,p['length'],library);row=dict(problem=p,catalog=declaration(c),input_library=[x['name'] for x in library],result=r,catalog_build_seconds=c['build_seconds'],**complete(c,p,r,library,code))
        if row.get('native',{}).get('status')!='accepted':raise ValueError('fresh source must fully check')
        row['promotion']=H.promote(c,r,p['length'],library,p['id']);library+=row['promotion']['templates'];row['library_check']=H.validate_library(p['theory'],library);row['cold_seconds']=time.perf_counter()-t;data['donors'].append(row);print('donor',p['id'],len(library),flush=True)
    probe=dict(protocol='gcts-fol-1',theory=P.donors()[0]['theory'],target=['imp',['bot'],['bot']],blocks=H.definitions(library),proof=[dict(rule='tautology',formula=['imp',['bot'],['bot']])]);data['whole_library_native']=dict(request=probe,result=tree_native.check(canonical(probe),code,TMP,problem_hash(probe),steps=100000000));data['library_seconds']=time.perf_counter()-start;data['library']=library
    if data['whole_library_native']['result']['status']!='accepted':raise ValueError('whole fresh library native gate')
    training=P.training();evaluation=P.evaluation();pin=lambda p:problem_hash(dict(protocol='gcts-fol-1',theory=p['theory'],target=p['target']))
    if {pin(p) for p in training}&{pin(p) for p in evaluation}:raise ValueError('external training/evaluation overlap')
    start=time.perf_counter();catalogs={}
    for p in training:
        c=C.equational(p['theory'],p['target'],p['term_bound']);t=time.perf_counter();inventory=A.equation_inventory(freeze(declaration(c)));gate=dict(report=inventory,seconds=time.perf_counter()-t);catalogs[p['id']]=c;data['training_catalogs'].append(dict(problem=p,catalog=declaration(c),catalog_sha256=H.digest(declaration(c)),build_seconds=c['build_seconds'],validation_seconds=c['validation_seconds'],inventory_gate=gate))
    data['training_catalog_seconds']=time.perf_counter()-start
    for index,seed in enumerate((1,7,19)):
        for signal in (('complete','local') if index%2==0 else ('local','complete')):
            start=time.perf_counter();weights=[0.0]*12;baseline=0.;state=seed;row=dict(seed=seed,signal=signal,initial_weights=list(weights),initial_baseline=baseline,episodes=[])
            for epoch in range(4):
                for p in training[epoch:]+training[:epoch]:
                    t=time.perf_counter();c=catalogs[p['id']];ctrl=N.Policy(seed=state,weights=weights,stochastic=True);r=N.search(c,p['length'],library,policy=ctrl);done=complete(c,p,r,library,code)
                    gate_start=time.perf_counter();report=V.replay(freeze(declaration(c)),p['length'],freeze(r),freeze(library),weights,state,True);gate=dict(report=report,seconds=time.perf_counter()-gate_start,source_sha256=data['sources']['audit_partial_proof_policy.py']);u=N.update(weights,baseline,r,done.get('native'),p['length'],signal);episode=dict(problem_id=p['id'],epoch=epoch,input_random_state=state,result=r,prefix_gate=gate,update=u,**done);weights=u['weights_after'];baseline=u['baseline_after'];state=r['random_state'];episode['cold_seconds']=time.perf_counter()-t;row['episodes'].append(episode);print('train',seed,signal,epoch,p['id'],r['status'],r['base_attempts'],len(u['credits']),round(episode['cold_seconds'],4),flush=True)
            row.update(weights=weights,baseline=baseline,random_state=state,training_seconds=time.perf_counter()-start);data['learners'].append(row);(TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('learner ready',seed,signal,[round(w,4) for w in weights],flush=True)
    learned={(r['seed'],r['signal']):r['weights'] for r in data['learners']}
    for i,p in enumerate(evaluation):
        row=dict(problem=p,runs=[]);expected=None
        for index,seed in enumerate((1,7,19)):
            lanes=['base','prior','zero','complete','local'];shift=(i+index)%5
            for lane in lanes[shift:]+lanes[:shift]:
                selected=[] if lane=='base' else library;t=time.perf_counter();c=C.equational(p['theory'],p['target'],p['term_bound']);binding=H.digest(declaration(c))
                if expected is None:row.update(catalog=declaration(c),catalog_sha256=binding);expected=binding
                if binding!=expected:raise ValueError('matched base grammar changed')
                policy=N.Policy(weights=learned[seed,lane] if lane in ('complete','local') else None) if lane in ('zero','complete','local') else None;r=N.search(c,p['length'],selected,policy=policy);run=dict(seed=seed,lane=lane,library=[x['name'] for x in selected],catalog_sha256=binding,catalog_build_seconds=c['build_seconds'],catalog_validation_seconds=c['validation_seconds'],result=r,**complete(c,p,r,selected,code));run['cold_seconds']=time.perf_counter()-t;row['runs'].append(run);print('eval',p['id'],seed,lane,r['status'],r['base_attempts'],round(run['cold_seconds'],4),flush=True)
        data['evaluation'].append(row);(TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    data.update(total_seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,program_sha256=H.digest(code));target=DOCS/'partial-policy-001.json';target.write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',data['total_seconds'],target.stat().st_size,flush=True)
if __name__=='__main__':main()
