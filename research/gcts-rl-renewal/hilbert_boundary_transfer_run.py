"""Complete guarded recipient preparation and bounded derived-input searches."""
import gzip,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from hilbert_boundary_transfer_catalog import build
from semantic_inventory_worker import oracle_for
from semantic_lemma_inventory import used_definitions
from certificate_boundary_search import digest
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/hilbert-boundary-transfer-20261011';TMP=Path('/private/tmp/gcts-hilbert-boundary-transfer-20261011')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):
    t=p.with_suffix(p.suffix+'.tmp');t.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0));t.replace(p)
def plain(p,v):
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,indent=2)+'\n');t.replace(p)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text())
    if (OUT/'progress.json').exists():raise ValueError('fresh immutable study only')
    for p,h in plan['sources'].items():
        if sha(ROOT/p)!=h:raise ValueError('frozen source '+p)
    for p,d in plan['data_dependencies'].items():
        if sha(ROOT/p)!=d['sha256'] or (ROOT/p).stat().st_size!=d['bytes']:raise ValueError('frozen evidence '+p)
    prior=lambda name:ROOT/(plan['prior_prefix']+name);control=lambda name:ROOT/(plan['prior_control_prefix']+name)
    oldnative=load(prior('native.json.gz'));oldcontrol=load(control('native.json.gz'));oldaudit=json.loads(prior('audit.json').read_text());controlaudit=json.loads(control('audit.json').read_text())
    if oldaudit['status']!='passed' or oldaudit['native_queries']!=len(oldnative) or controlaudit['status']!='passed' or controlaudit['fresh_native_queries']!=len(oldcontrol):raise ValueError('actual complete inherited native replay')
    inventory=load(prior('inventories.json.gz'));catalog=build(plan['cases'],load(prior('catalog.json.gz')))
    if catalog!=load(OUT/'declared-catalog.json.gz'):raise ValueError('no post-declaration grammar change')
    save(OUT/'catalog.json.gz',catalog);save(OUT/'inventories.json.gz',inventory)
    cache={}
    for origin,records in [('prior-family',oldnative),('prior-control',oldcontrol)]:
        for q in records:
            if q['purpose'] in ['family_discovered_whole','fixed_expanded_discovered_whole'] and q['result']['status']=='accepted':cache[q['request_sha256']]=dict(origin=origin,query=q['id'],request_sha256=q['request_sha256'])
    progress=dict(status='preparing',plan_sha256=sha(OUT/'plan.json'),observations=[],groups={},native_queries=0,native_production_seconds=0.,native_budget_overshoots=[],native_budget_blocks=[],prior_cost_provenance=plan['prior_cost_provenance'])
    TMP.mkdir(parents=True,exist_ok=True);stage=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP/'production'),executable=str(TMP/'oracle')));progress['native_setup_seconds']=time.perf_counter()-stage;progress['initial_setup_seconds']=time.perf_counter()-began;save(OUT/'native.json.gz',[])
    def checkpoint():
        progress.update(seconds=time.perf_counter()-began,native_queries=len(oracle.records),native_production_seconds=sum(q['seconds'] for q in oracle.records));plain(OUT/'progress.json',progress)
    def submit(req,limit,purpose,**fields):
        before=sum(q['seconds'] for q in oracle.records);ceiling=plan['native_production_seconds_ceiling']
        if before>=ceiling:
            progress['native_budget_blocks'].append(dict(purpose=purpose,prior_native_seconds=before,ceiling_seconds=ceiling,**fields));checkpoint();return None
        q=oracle.request(req,limit,purpose);q.update(native_limit=limit,**fields);after=before+q['seconds'];overshoot=max(0.,after-ceiling)
        q['production_budget']=dict(prior_native_seconds=before,query_seconds=q['seconds'],after_native_seconds=after,ceiling_seconds=ceiling,overshoot_seconds=overshoot,checked_before_query=True)
        if overshoot:progress['native_budget_overshoots'].append(dict(query=q['id'],**q['production_budget']))
        fixed,free=boundary_words(req);q['boundary_words']=dict(fixed=fixed,free=free);save(OUT/'native.json.gz',oracle.records);checkpoint();print('native',q['id'],purpose,q['result']['status'],round(q['seconds'],3),'seconds',flush=True);return q
    checkpoint();compiled={};taut=['imp',['bot'],['bot']]
    try:
        for group,item in catalog['groups'].items():
            stage=time.perf_counter();spec=item['representative'];request=lambda f:dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=[dict(rule='tautology',formula=f)],target=f)
            q=submit(request(taut),plan['guard_native_steps'],'transfer_theory_admission',group=group)
            if q is None or q['result']['status']!='accepted':
                progress.update(status='unknown_preparation' if q is None or q['result']['status'].startswith('unknown') else 'rejected_theory',unresolved_group=group,native_outcome='unknown_native_cost_ceiling' if q is None else q['result']['status']);checkpoint();return
            theory_query=q['id'];ids=[];tauts=[]
            for i,f in enumerate(item['basis']):
                q=submit(request(f),plan['guard_native_steps'],'transfer_tautology_guard',group=group,basis_index=i)
                if q is None or q['result']['status'] not in ['accepted','rejected']:
                    progress.update(status='unknown_preparation',unresolved_group=group,unresolved_basis_index=i,native_outcome='unknown_native_cost_ceiling' if q is None else q['result']['status']);checkpoint();return
                ids.append(q['id'])
                if q['result']['status']=='accepted':tauts.append(f)
            compiled[group]=dict(status='complete',catalog=item['catalog'],basis=item['basis'],variables=[],admitted_schemes=[],tautologies=tauts,queries=ids,theory_query=theory_query,seconds=time.perf_counter()-stage)
            progress['groups'][group]=dict(status='complete',formulas=len(item['basis']),compile_seconds=compiled[group]['seconds']);save(OUT/'compiled.json.gz',compiled);checkpoint()
        progress.update(status='searching',preparation_seconds=time.perf_counter()-began);checkpoint()
        for item in plan['schedule']:
            spec=next(c for c in plan['cases'] if c['id']==item['case_id']);inv=inventory[item['language']];tag=item['tag']
            job=dict(case=spec,compiled=compiled[spec['group']],inventory=inv,seed=plan['seed'],weights=plan['weights'],limits=plan['limits'],mode=item['mode'],feature_semantics=item['feature_semantics'])
            inp=TMP/(tag+'-input.json');dest=TMP/(tag+'-output.json.gz');inp.write_text(json.dumps(job,separators=(',',':'))+'\n');stage=time.perf_counter()
            subprocess.run([sys.executable,str(HERE/'hilbert_promotion_family_worker_v2.py'),str(inp),str(dest)],check=True,env=dict(os.environ,PYTHONPYCACHEPREFIX='/private/tmp/gcts-native-wang-pycache'))
            obs=load(dest);obs.update(**item,worker_wall_seconds=time.perf_counter()-stage,native_binding=None,certification='pending' if obs['search']['proof'] is not None else 'no_proof')
            save(OUT/(tag+'.json.gz'),obs);obs['pre_certification_checkpoint_sha256']=sha(OUT/(tag+'.json.gz'));checkpoint();proof=obs['search']['proof'];stage=time.perf_counter()
            if proof is not None:
                req=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=used_definitions(inv,proof),proof=proof,target=spec['target']);key=digest(req)
                if key in cache:
                    binding=cache[key];records=oldnative if binding['origin']=='prior-family' else oldcontrol if binding['origin']=='prior-control' else oracle.records;q=records[binding['query']]
                    if q['request']!=req or q['result']['status']!='accepted':raise ValueError('exact inherited acceptance')
                    if binding['origin']=='fresh':
                        while True:
                            p=OUT/'native-audit-progress.json';receipt=json.loads(p.read_text()) if p.exists() else {}
                            if any(x['query']==binding['query'] and x['record_sha256']==digest(q) for x in receipt.get('replayed_bindings',[])):break
                            time.sleep(1)
                        binding=dict(binding,independent_replayed_record_sha256=digest(q))
                    obs.update(native_binding=binding,certification='accepted')
                else:
                    q=submit(req,plan['whole_native_steps'],'transfer_discovered_whole',observation=tag,pre_certification_checkpoint_sha256=obs['pre_certification_checkpoint_sha256'])
                    if q is None:obs['certification']='unknown_native_cost_ceiling'
                    else:
                        binding=dict(origin='fresh',query=q['id'],request_sha256=key);obs.update(native_binding=binding,certification=q['result']['status'])
                        if q['result']['status']=='accepted':cache[key]=binding
            obs['certification_wall_seconds']=time.perf_counter()-stage;save(OUT/(tag+'-final.json.gz'),obs)
            progress['observations'].append(dict(**item,status=obs['search']['status'],certification=obs['certification'],attempts=obs['search']['metrics'].get('attempts',0),search_seconds=obs['search']['seconds'],setup_seconds=obs['setup_seconds'],worker_wall_seconds=obs['worker_wall_seconds'],certification_wall_seconds=obs['certification_wall_seconds'],peak_rss_bytes=obs['peak_rss_bytes'],native_binding=obs['native_binding']));checkpoint()
            print(tag,obs['search']['status'],obs['certification'],obs['search']['metrics'].get('attempts',0),'attempts',round(obs['search']['seconds'],3),'seconds',flush=True)
        progress['status']='complete';checkpoint();print('COMPLETE 24 DERIVED-INPUT TRANSFER TRIALS',flush=True)
    except Exception as e:
        progress.update(status='failed',failure_type=type(e).__name__,failure_message=str(e));checkpoint();raise
    finally:oracle.close()
if __name__=='__main__':main()
