"""Resume the unchanged 64-run study after the preserved API-label failure.

No completed admission, guard or observation is rerun. The v1 native ledger
and its complete independent replay are pinned before this continuation starts.
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
TMP=Path('/private/tmp/gcts-hilbert-promotion-family-v2-20261011')
def load(path):return json.loads(gzip.decompress(path.read_bytes()))
def hashed(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    waiting_began=time.perf_counter()
    amendment=json.loads((OUT/'api-token-amendment.json').read_text());plan=json.loads((OUT/'plan.json').read_text())
    if hashed(OUT/'plan.json')!=amendment['original_plan_sha256']:raise ValueError('original plan changed')
    for p,h in dict(plan['sources'],**amendment['versioned_sources']).items():
        if hashed(ROOT/p)!=h:raise ValueError('frozen source changed '+p)
    for p,r in plan['data_dependencies'].items():
        if hashed(ROOT/p)!=r['sha256'] or (ROOT/p).stat().st_size!=r['bytes']:raise ValueError('frozen input '+p)
    print('Waiting for unchanged v1 admission/guard pipeline and independent native replay.',flush=True)
    while True:
        progress=json.loads((OUT/'progress.json').read_text())
        if progress['status']=='failed':
            if progress.get('failure_type')!='CalledProcessError' or 'hilbert_promotion_family_worker.py' not in progress.get('failure_message',''):raise ValueError('unexpected v1 failure')
            if (OUT/'audit.json').exists():
                oldaudit=json.loads((OUT/'audit.json').read_text())
                if oldaudit['status']=='passed' and oldaudit['production_outcome']=='failed' and oldaudit['native_queries']==progress['native_queries']:break
        elif progress['status']=='complete' or progress['status'].startswith(('unknown','rejected')):raise ValueError('v1 outcome does not permit API continuation '+progress['status'])
        time.sleep(1)
    resume_wait_seconds=time.perf_counter()-waiting_began;restart_started=time.perf_counter()
    schedule=[(spec,rep,method) for spec in plan['cases'] for rep in plan['repetitions'] for method in plan['schedules'][str(rep)]]
    if len(schedule)!=64 or len(progress['base_admissions'])!=28 or len(progress['promoted_admissions'])!=48 or len(progress['groups'])!=2:raise ValueError('complete unchanged preparation required')
    done=progress['observations']
    if len(done)!=3 or [o['method'] for o in done]!=[method for _,_,method in schedule[:3]]:raise ValueError('exact original first three runs required')
    if any(plan['methods'][method]['feature_semantics']=='expanded' for _,_,method in schedule[:3]):raise ValueError('affected lane already searched')
    prefix={}
    for n in ['native.json.gz','audit.json','progress.json']:
        dest=OUT/('v1-'+n);dest.write_bytes((OUT/n).read_bytes());prefix[n]=dict(path=str(dest.relative_to(ROOT)),sha256=hashed(dest),bytes=dest.stat().st_size)
    records=load(OUT/'v1-native.json.gz');receipt=dict(original_plan_sha256=hashed(OUT/'plan.json'),amendment_sha256=hashed(OUT/'api-token-amendment.json'),files=prefix,native_queries=len(records),observations=len(done))
    plain(OUT/'continuation-prefix.json',receipt)
    inventories=load(OUT/'inventories.json.gz');compiled=load(OUT/'compiled.json.gz')
    TMP.mkdir(parents=True,exist_ok=True);subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP/'production'),executable=str(TMP/'oracle')));oracle.records=records
    cache={r['request_sha256']:r['id'] for r in records if r['purpose']=='family_discovered_whole' and r['result']['status']=='accepted'}
    prior_seconds=progress['seconds'];began=restart_started;progress['api_token_correction']=dict(amendment_sha256=hashed(OUT/'api-token-amendment.json'),prefix_sha256=hashed(OUT/'continuation-prefix.json'),v1_outcome='failed',v1_failure_type=progress.pop('failure_type'),v1_failure_message=progress.pop('failure_message'),v1_seconds=prior_seconds,resume_process_wait_seconds=resume_wait_seconds,normalization=amendment['normalization'])
    progress['status']='searching'
    def checkpoint():
        elapsed=time.perf_counter()-began;progress.update(native_queries=len(oracle.records),seconds=prior_seconds+elapsed,continuation_seconds=elapsed);plain(OUT/'progress.json',progress)
    checkpoint()
    try:
        for spec,rep,method_id in schedule[len(done):]:
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
        progress['status']='complete';checkpoint();print('COMPLETE UNCHANGED 64-RUN FAMILY STUDY',flush=True)
    except Exception as error:
        progress.update(status='failed',failure_type=type(error).__name__,failure_message=str(error));checkpoint();raise
    finally:oracle.close()
if __name__=='__main__':main()
