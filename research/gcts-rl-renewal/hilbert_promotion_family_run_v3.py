"""Separately predeclared 20-billion-step guard continuation, unchanged heap.

Preserves every v1 unknown step and admits no incomplete guard catalog to search.
The API token normalization is the already frozen v2 worker.
"""
import gzip,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from hilbert_promotion_family_run import save,plain
from semantic_inventory_worker import oracle_for
from semantic_lemma_inventory import used_definitions
from certificate_boundary_search import digest
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/hilbert-promotion-family-20261011'
TMP=Path('/private/tmp/gcts-hilbert-promotion-family-v3-20261011')
def load(path):return json.loads(gzip.decompress(path.read_bytes()))
def hashed(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    began=time.perf_counter();resource=json.loads((OUT/'guard-resource-plan.json').read_text());plan=json.loads((OUT/'plan.json').read_text())
    amendment=json.loads((OUT/'api-token-amendment.json').read_text())
    if hashed(OUT/'plan.json')!=resource['original_plan_sha256'] or hashed(OUT/'api-token-amendment.json')!=resource['api_token_amendment_sha256']:raise ValueError('unchanged original and API plans')
    for p,h in dict(plan['sources'],**amendment['versioned_sources'],**resource['versioned_sources']).items():
        if hashed(ROOT/p)!=h:raise ValueError('frozen source '+p)
    for p,r in plan['data_dependencies'].items():
        if hashed(ROOT/p)!=r['sha256'] or (ROOT/p).stat().st_size!=r['bytes']:raise ValueError('frozen input '+p)
    for r in resource['prior_files'].values():
        if hashed(ROOT/r['path'])!=r['sha256'] or (ROOT/r['path']).stat().st_size!=r['bytes']:raise ValueError('exact audited v1 receipt')
    prior=load(ROOT/resource['prior_files']['native.json.gz']['path']);oldaudit=json.loads((ROOT/resource['prior_files']['audit.json']['path']).read_text());progress=json.loads((ROOT/resource['prior_files']['progress.json']['path']).read_text())
    if len(prior)!=128 or oldaudit['status']!='passed' or oldaudit['production_outcome']!='unknown_recipient_guard' or oldaudit['native_queries']!=128 or progress['observations']:raise ValueError('exact zero-search terminal v1 prefix')
    if progress['status']!='unknown_recipient_guard' or prior[-1]['result']['status']!='unknown_step_budget' or prior[-1]['basis_index']!=21 or prior[-1]['group']!='composed':raise ValueError('exact original guard cutoff')
    if hashed(OUT/'progress.json')!=resource['prior_files']['progress.json']['sha256'] or hashed(OUT/'native.json.gz')!=resource['prior_files']['native.json.gz']['sha256']:raise ValueError('live ledger must equal frozen terminal prefix before continuation')
    if len(progress['base_admissions'])!=28 or len(progress['promoted_admissions'])!=48 or set(progress['groups'])!={'direct'}:raise ValueError('complete rule inventory and direct guards')
    catalog=load(OUT/'catalog.json.gz');inventories=load(ROOT/resource['prior_files']['inventories.json.gz']['path']);compiled=load(ROOT/resource['prior_files']['compiled.json.gz']['path']);item=catalog['groups']['composed'];spec=item['representative'];basis=item['basis']
    if len(basis)!=28 or prior[-1]['request']['target']!=basis[21]:raise ValueError('full composed guard basis preserved')
    TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP/'production'),executable=str(TMP/'oracle')));oracle.records=prior
    cache={};prior_seconds=progress['seconds'];elapsed_prepare=time.perf_counter()-began;began=time.perf_counter()-elapsed_prepare
    progress.update(status='compiling_v3',api_token_correction=dict(amendment_sha256=hashed(OUT/'api-token-amendment.json'),normalization=amendment['normalization'],v2_outcome='refused_non_API_unknown_guard'),guard_resource_continuation=dict(plan_sha256=hashed(OUT/'guard-resource-plan.json'),v1_outcome='unknown_recipient_guard',v1_seconds=prior_seconds,original_unknown_query=127,original_unknown_steps=prior[-1]['result']['micro_steps'],guard_native_steps=resource['guard_native_steps']))
    progress.pop('native_outcome',None)
    def checkpoint():
        elapsed=time.perf_counter()-began;progress.update(native_queries=len(oracle.records),seconds=prior_seconds+elapsed,continuation_seconds=elapsed);plain(OUT/'progress.json',progress)
    def submit_guard(i):
        f=basis[i];req=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=[dict(rule='tautology',formula=f)],target=f)
        q=oracle.request(req,resource['guard_native_steps'],'recipient_tautology_guard');q.update(native_limit=resource['guard_native_steps'],group='composed',basis_index=i)
        if i==21:
            q['retry_of']=127
            if q['request']!=prior[127]['request'] or q['input_sha256']!=prior[127]['input_sha256']:raise ValueError('same unchanged unknown guard request and input')
        fixed,free=boundary_words(req);q['boundary_words']=dict(fixed=fixed,free=free);save(OUT/'native.json.gz',oracle.records);checkpoint();print('native',q['id'],'guard',i,q['result']['status'],round(q['seconds'],3),'seconds',flush=True);return q
    checkpoint()
    ids=[106+i for i in range(21)];tauts=[basis[i] for i,q in enumerate(ids) if prior[q]['result']['status']=='accepted'];compile_started=time.perf_counter()
    try:
        for i in range(21,28):
            q=submit_guard(i);ids.append(q['id'])
            if q['result']['status']=='accepted':tauts.append(basis[i])
            elif q['result']['status']!='rejected':
                progress.update(status='unknown_recipient_guard_v3',native_outcome=q['result']['status'],unresolved_basis_index=i);checkpoint();oracle.close();return
        prior_compile=sum(q['seconds'] for q in prior[:128] if q.get('group')=='composed')
        compiled['composed']=dict(status='complete',catalog=item['catalog'],basis=basis,variables=[],admitted_schemes=[],tautologies=tauts,queries=ids,theory_query=105,seconds=prior_compile+time.perf_counter()-compile_started)
        save(OUT/'compiled.json.gz',compiled);progress['groups']['composed']=dict(compile_seconds=compiled['composed']['seconds'],formulas=28);progress['status']='searching';checkpoint()
    except Exception as error:
        progress.update(status='failed',failure_type=type(error).__name__,failure_message=str(error));checkpoint();oracle.close();raise
    schedule=[(spec,rep,method) for spec in plan['cases'] for rep in plan['repetitions'] for method in plan['schedules'][str(rep)]]
    if len(schedule)!=64:raise ValueError('all original trials retained')
    try:
        for spec,rep,method_id in schedule:
            method=plan['methods'][method_id];inventory=inventories[method['language']];tag=spec['id']+'-'+method_id+'-r'+str(rep)
            job=dict(case=spec,compiled=compiled[spec['group']],inventory=inventory,seed=plan['seed'],weights=plan['weights'],limits=plan['limits'],mode=method['mode'],feature_semantics=method['feature_semantics'])
            inp=TMP/(tag+'-input.json');out=TMP/(tag+'-output.json.gz');inp.write_text(json.dumps(job,separators=(',',':'))+'\n');started=time.perf_counter()
            subprocess.run([sys.executable,str(HERE/'hilbert_promotion_family_worker_v2.py'),str(inp),str(out)],check=True,env=dict(os.environ,PYTHONPYCACHEPREFIX='/private/tmp/gcts-native-wang-pycache'))
            obs=load(out);obs.update(case_id=spec['id'],method=method_id,language=method['language'],repetition=rep,worker_wall_seconds=time.perf_counter()-started,native_query=None,cached_native_acceptance=False,certification='pending' if obs['search']['proof'] is not None else 'no_proof')
            save(OUT/(tag+'.json.gz'),obs);checkpoint_sha=hashed(OUT/(tag+'.json.gz'));obs['pre_certification_checkpoint_sha256']=checkpoint_sha
            proof=obs['search']['proof']
            if proof is not None:
                req=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=used_definitions(inventory,proof),proof=proof,target=spec['target']);key=digest(req)
                if key in cache:obs.update(native_query=cache[key],cached_native_acceptance=True,certification='accepted')
                else:
                    q=oracle.request(req,plan['whole_native_steps'],'family_discovered_whole');q.update(native_limit=plan['whole_native_steps'],observation=tag,pre_certification_checkpoint_sha256=checkpoint_sha)
                    fixed,free=boundary_words(req);q['boundary_words']=dict(fixed=fixed,free=free);save(OUT/'native.json.gz',oracle.records);checkpoint()
                    obs.update(native_query=q['id'],certification=q['result']['status'])
                    if q['result']['status']=='accepted':cache[key]=q['id']
                    print('native',q['id'],q['purpose'],q['result']['status'],round(q['seconds'],3),'seconds',flush=True)
            save(OUT/(tag+'-final.json.gz'),obs)
            progress['observations'].append(dict(tag=tag,case_id=spec['id'],method=method_id,language=method['language'],repetition=rep,status=obs['search']['status'],certification=obs['certification'],attempts=obs['search']['metrics'].get('attempts',0),search_seconds=obs['search']['seconds'],setup_seconds=obs['setup_seconds'],peak_rss_bytes=obs['peak_rss_bytes'],native_query=obs['native_query'],cached_native_acceptance=obs['cached_native_acceptance']));checkpoint()
            print(tag,obs['search']['status'],obs['certification'],obs['search']['metrics'].get('attempts',0),'attempts',round(obs['search']['seconds'],3),'seconds',flush=True)
        progress['status']='complete';checkpoint();print('COMPLETE V3 GUARD-RESOURCE AND UNCHANGED 64-RUN STUDY',flush=True)
    except Exception as error:
        progress.update(status='failed',failure_type=type(error).__name__,failure_message=str(error));checkpoint();raise
    finally:oracle.close()
if __name__=='__main__':main()
