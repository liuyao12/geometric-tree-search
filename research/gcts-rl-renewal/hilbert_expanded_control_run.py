"""Fresh fixed word-expanded searches, exact certified-request reuse only."""
import gzip,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from semantic_inventory_worker import oracle_for
from semantic_lemma_inventory import used_definitions
from certificate_boundary_search import digest
from proof_boundary import boundary_words
from semantic_inventory_guidance import FIXED

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/hilbert-expanded-control-20261011'
TMP=Path('/private/tmp/gcts-hilbert-expanded-control-20261011')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):
    t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0));t.replace(p)
def plain(p,v):
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2)+'\n');t.replace(p)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text())
    if (OUT/'progress.json').exists():raise ValueError('fresh study only')
    for p,h in plan['sources'].items():
        if sha(ROOT/p)!=h:raise ValueError('frozen source '+p)
    for p,d in plan['data_dependencies'].items():
        if sha(ROOT/p)!=d['sha256'] or (ROOT/p).stat().st_size!=d['bytes']:raise ValueError('frozen input '+p)
    prefix=ROOT/plan['prior_prefix'];p=lambda suffix:Path(str(prefix)+suffix)
    prior=load(p('native.json.gz'));audit=json.loads(p('audit.json').read_text())
    if audit['status']!='passed' or audit['production_outcome']!='complete' or audit['native_queries']!=len(prior) or len(prior)!=142:raise ValueError('complete prior native audit')
    if sum(q['result']['micro_steps'] for q in prior)!=audit['native_micro_steps']:raise ValueError('complete prior replay bill')
    if list(FIXED)!=plan['fixed_weights'] or plan['mode']!='fixed' or plan['feature_semantics']!='expanded-word':raise ValueError('declared treatment only')
    compiled=load(p('compiled.json.gz'));inventories=load(p('inventories.json.gz'))
    cache={q['request_sha256']:dict(origin='prior',query=q['id'],request_sha256=q['request_sha256']) for q in prior if q['purpose']=='family_discovered_whole' and q['result']['status']=='accepted'}
    if len(cache)!=7:raise ValueError('seven exact prior whole certificates')
    prior_progress=json.loads(p('progress.json').read_text())
    progress=dict(status='preparing',plan_sha256=sha(OUT/'plan.json'),observations=[],native_queries=0,
        prior_shared_costs=dict(production_seconds=prior_progress['seconds'],native_production_seconds=sum(q['seconds'] for q in prior),native_micro_steps=audit['native_micro_steps'],native_replay_seconds=audit['native_replay_seconds'],full_native_queries=len(prior)),
        source_reuse=dict(native_ledger_sha256=sha(p('native.json.gz')),full_audit_sha256=sha(p('audit.json')),exact_prior_certificates=7))
    TMP.mkdir(parents=True,exist_ok=True);stage=time.perf_counter()
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP/'production'),executable=str(TMP/'oracle')))
    progress['native_setup_seconds']=time.perf_counter()-stage;progress['preparation_seconds']=time.perf_counter()-began;save(OUT/'native.json.gz',[])
    def checkpoint():progress.update(seconds=time.perf_counter()-began,native_queries=len(oracle.records));plain(OUT/'progress.json',progress)
    progress['status']='searching';checkpoint()
    try:
        for item in plan['schedule']:
            spec=next(c for c in plan['cases'] if c['id']==item['case_id']);inv=inventories[item['language']];tag=item['tag']
            job=dict(case=spec,compiled=compiled[spec['group']],inventory=inv,seed=plan['seed'],weights=plan['fixed_weights'],limits=plan['limits'],mode='fixed',feature_semantics='expanded-word')
            inp=TMP/(tag+'-input.json');dest=TMP/(tag+'-output.json.gz');inp.write_text(json.dumps(job,separators=(',',':'))+'\n');stage=time.perf_counter()
            subprocess.run([sys.executable,str(HERE/'hilbert_promotion_family_worker_v2.py'),str(inp),str(dest)],check=True,env=dict(os.environ,PYTHONPYCACHEPREFIX='/private/tmp/gcts-native-wang-pycache'))
            obs=load(dest);obs.update(**item,worker_wall_seconds=time.perf_counter()-stage,native_binding=None,certification='pending' if obs['search']['proof'] is not None else 'no_proof')
            save(OUT/(tag+'.json.gz'),obs);obs['pre_certification_checkpoint_sha256']=sha(OUT/(tag+'.json.gz'));checkpoint()
            proof=obs['search']['proof'];stage=time.perf_counter()
            if proof is not None:
                req=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=used_definitions(inv,proof),proof=proof,target=spec['target']);key=digest(req)
                if key in cache:
                    binding=cache[key];q=(prior if binding['origin']=='prior' else oracle.records)[binding['query']]
                    if q['request']!=req or q['result']['status']!='accepted':raise ValueError('exact actual accepted whole request')
                    if binding['origin']=='fresh':
                        # An acceptance alone is insufficient for reuse in this
                        # control: wait for its actual independent full replay.
                        while True:
                            receipt=OUT/'native-audit-progress.json'
                            replay=json.loads(receipt.read_text()) if receipt.exists() else {}
                            matched=[b for b in replay.get('replayed_bindings',[]) if b['query']==binding['query'] and b['record_sha256']==digest(q)]
                            if matched:break
                            time.sleep(1)
                        binding=dict(binding,independent_replayed_record_sha256=digest(q))
                    obs.update(native_binding=binding,certification='accepted')
                else:
                    q=oracle.request(req,plan['whole_native_steps'],'fixed_expanded_discovered_whole');q.update(native_limit=plan['whole_native_steps'],observation=tag,pre_certification_checkpoint_sha256=obs['pre_certification_checkpoint_sha256'])
                    fixed,free=boundary_words(req);q['boundary_words']=dict(fixed=fixed,free=free);save(OUT/'native.json.gz',oracle.records)
                    binding=dict(origin='fresh',query=q['id'],request_sha256=key);obs.update(native_binding=binding,certification=q['result']['status'])
                    if q['result']['status']=='accepted':cache[key]=binding
                    print('native',q['id'],q['result']['status'],round(q['seconds'],3),'seconds',flush=True)
            obs['certification_wall_seconds']=time.perf_counter()-stage;save(OUT/(tag+'-final.json.gz'),obs)
            progress['observations'].append(dict(**item,status=obs['search']['status'],certification=obs['certification'],attempts=obs['search']['metrics'].get('attempts',0),search_seconds=obs['search']['seconds'],setup_seconds=obs['setup_seconds'],worker_wall_seconds=obs['worker_wall_seconds'],certification_wall_seconds=obs['certification_wall_seconds'],peak_rss_bytes=obs['peak_rss_bytes'],native_binding=obs['native_binding']))
            checkpoint();print(tag,obs['search']['status'],obs['certification'],obs['search']['metrics'].get('attempts',0),'attempts',round(obs['search']['seconds'],3),'seconds',flush=True)
        progress['status']='complete';checkpoint();print('COMPLETE 16 FIXED WORD-EXPANDED CONTROLS',flush=True)
    except Exception as e:
        progress.update(status='failed',failure_type=type(e).__name__,failure_message=str(e));checkpoint();raise
    finally:oracle.close()
if __name__=='__main__':main()
