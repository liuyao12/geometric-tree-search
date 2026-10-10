"""Fresh fragment discovery, three zero-start policy seeds, matched evaluation."""
import hashlib,json,resource,time
from pathlib import Path
import proof_cluster_policy as R,proof_clusters as H,proof_policy_problems as P
import semantic_proof_catalogs as C
from run_semantic_proofs import declaration
from serialized_kernel import canonical,problem_hash
from tree_kernel import program
import tree_native
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-proof-policy')
SOURCES=('proof_cluster_policy.py','proof_policy_problems.py','run_proof_policy.py','proof_clusters.py','proof_cluster_problems.py','semantic_proof_tiles.py','semantic_proof_catalogs.py','semantic_proof_problems.py','run_semantic_proofs.py','proof_block_search.py','turtle.py','logic.py','kernel_machine.py','serialized_kernel.py','tree_kernel.py','fol_checker.tree','tree_native.py','tree_runner.cpp')
def complete(c,p,r,library,code):
    if 'decoded' not in r:return {}
    h=H.hierarchical_certificate(c,r,p['length'],library);native=tree_native.check(canonical(h['request']),code,TMP,problem_hash(r['decoded']['request']),steps=100000000)
    return dict(hierarchy=h,native=native)
def main():
    began=time.perf_counter();TMP.mkdir(exist_ok=True);code=program();library=[];data=dict(sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES},initial_library=[],donors=[],training_catalogs=[],seeds=[],evaluation=[],features=R.FEATURES,
      configuration=dict(seconds=5,base_attempts=50000,proposal_limit=8,index_instances=50000,seeds=[1,7,19],epochs=4,native_steps=100000000,rate=.2,weight_clip=6,baseline_decay=.9),
      scope='Fresh GCTS donor discoveries; no saved library or policy input. Eight training statements are separate from ten frozen evaluation statements. Three zero-weight seeds train a projected softmax policy on complete, checked continuation traces. Unknown training trees provide no parameter update. No failure markings, induction, fair FOL grammar or unrestricted novel-cluster synthesis.',
      comparison='Identical complete base catalogs, targets, bounds, global scheduler and actual-placement budgets in every lane. Base, level-one, fixed hierarchy prior, zero-weight identity-order policy, and trained policy; all base alternatives remain. Policies may select any compatible bounded fragment instance or defer. Total learning, index, inference, validation, expansion, native and compilation costs are exposed.')
    data['compile_seconds']=tree_native.compile_tool(TMP);start=time.perf_counter()
    for p in P.donors():
        t=time.perf_counter();c=C.equational(p['theory'],p['target'],p['term_bound']);inputs=[t['name'] for t in library];r=H.search(c,p['length'],library);row=dict(problem=p,catalog=declaration(c),input_library=inputs,result=r,catalog_build_seconds=c['build_seconds'],**complete(c,p,r,library,code))
        if row.get('native',{}).get('status')!='accepted':raise ValueError('fresh donor must fully check')
        row['promotion']=H.promote(c,r,p['length'],library,p['id']);library+=row['promotion']['templates'];row['library_check']=H.validate_library(p['theory'],library);row['cold_seconds']=time.perf_counter()-t;data['donors'].append(row);print('donor',p['id'],len(library),flush=True)
    probe=dict(protocol='gcts-fol-1',theory=P.donors()[0]['theory'],target=['imp',['bot'],['bot']],blocks=H.definitions(library),proof=[dict(rule='tautology',formula=['imp',['bot'],['bot']])]);data['whole_library_native']=dict(request=probe,result=tree_native.check(canonical(probe),code,TMP,problem_hash(probe),steps=100000000));data['library_seconds']=time.perf_counter()-start;data['library']=library
    if data['whole_library_native']['result']['status']!='accepted':raise ValueError('complete library machine gate')
    training=P.training();evaluation=P.evaluation();train_pins={problem_hash(dict(protocol='gcts-fol-1',theory=p['theory'],target=p['target'])) for p in training};eval_pins={problem_hash(dict(protocol='gcts-fol-1',theory=p['theory'],target=p['target'])) for p in evaluation}
    if train_pins&eval_pins:raise ValueError('training and evaluation external statements overlap')
    start=time.perf_counter();catalogs={}
    for p in training:
        c=C.equational(p['theory'],p['target'],p['term_bound']);catalogs[p['id']]=c;data['training_catalogs'].append(dict(problem=p,catalog=declaration(c),catalog_sha256=H.digest(declaration(c)),build_seconds=c['build_seconds'],validation_seconds=c['validation_seconds']))
    data['training_catalog_seconds']=time.perf_counter()-start
    for seed in data['configuration']['seeds']:
        start=time.perf_counter();weights=[0.0]*len(R.FEATURES);baseline=0.0;random_state=seed;row=dict(seed=seed,initial_weights=list(weights),initial_baseline=baseline,episodes=[])
        for epoch in range(4):
            ordered=training[epoch:]+training[:epoch]
            for p in ordered:
                t=time.perf_counter();c=catalogs[p['id']];ctrl=R.Policy(seed=random_state,weights=weights,stochastic=True);r=R.search(c,p['length'],library,policy=ctrl);done=complete(c,p,r,library,code);u=R.update(weights,baseline,r,done.get('native'));episode=dict(problem_id=p['id'],epoch=epoch,input_random_state=random_state,result=r,update=u,**done);weights=u['weights_after'];baseline=u['baseline_after'];random_state=r['random_state'];episode['cold_seconds']=time.perf_counter()-t;row['episodes'].append(episode);print('train',seed,epoch,p['id'],r['status'],r['base_attempts'],len(u['credits']),round(episode['cold_seconds'],4),flush=True)
        row.update(weights=weights,baseline=baseline,random_state=random_state,training_seconds=time.perf_counter()-start);data['seeds'].append(row);(TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('seed ready',seed,[round(w,4) for w in weights],flush=True)
    for i,p in enumerate(evaluation):
        row=dict(problem=p,runs=[]);expected=None
        for seed_row in data['seeds']:
            seed=seed_row['seed'];lanes=['base','level1','prior','zero','trained'];shift=(i+data['configuration']['seeds'].index(seed))%len(lanes);lanes=lanes[shift:]+lanes[:shift]
            for lane in lanes:
                selected=[] if lane=='base' else [t for t in library if t['level']==1] if lane=='level1' else library;t=time.perf_counter();c=C.equational(p['theory'],p['target'],p['term_bound']);pin=H.digest(declaration(c))
                if expected is None:row.update(catalog=declaration(c),catalog_sha256=pin);expected=pin
                if pin!=expected:raise ValueError('matched base grammar changed')
                policy=R.Policy(weights=seed_row['weights'] if lane=='trained' else None) if lane in ('zero','trained') else None
                r=R.search(c,p['length'],selected,policy=policy);run=dict(seed=seed,lane=lane,library=[t['name'] for t in selected],catalog_sha256=pin,catalog_build_seconds=c['build_seconds'],catalog_validation_seconds=c['validation_seconds'],result=r,**complete(c,p,r,selected,code));run['cold_seconds']=time.perf_counter()-t;row['runs'].append(run);print('eval',p['id'],seed,lane,r['status'],r['base_attempts'],round(run['cold_seconds'],4),flush=True)
        data['evaluation'].append(row);(TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    data.update(total_seconds=time.perf_counter()-began,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,program_sha256=H.digest(code))
    (DOCS/'proof-policy-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',data['total_seconds'],flush=True)
if __name__=='__main__':main()
