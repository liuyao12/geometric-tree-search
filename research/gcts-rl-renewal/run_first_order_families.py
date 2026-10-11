"""Predeclared typed-family promotion, zero-start training and isolated controls."""
import copy,gzip,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from certificate_boundary_search import digest
from first_order_receptors import compile_guards
from first_order_families import mine,specialize,admit
from semantic_inventory_worker import oracle_for
from semantic_lemma_inventory import used_definitions
from semantic_inventory_policy import reward,update,FEATURES
from audit_first_order_families import compilation,registry_binding,model_binding
from audit_prefix_failure_markings import extended_tree
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/first-order-families-20261011';TMP=Path('/private/tmp/gcts-first-order-families-20261011')
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def load(p):return json.loads(gzip.decompress(p.read_bytes()))

def main():
    started=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());TMP.mkdir(parents=True,exist_ok=True)
    for f,h in {**plan['prior_source_closure'],**plan['source_sha256']}.items():
        if hashlib.sha256((ROOT/f).read_bytes()).hexdigest()!=h:raise ValueError('changed frozen source '+f)
    for f,r in plan['data_dependencies'].items():
        if hashlib.sha256((ROOT/f).read_bytes()).hexdigest()!=r['sha256'] or (ROOT/f).stat().st_size!=r['bytes']:raise ValueError('changed pinned data '+f)
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP/'native'),executable=str(TMP/'oracle')));original_request=oracle.request;cache={};library=[];summaries=[]
    def request(r,limit,purpose):
        q=original_request(r,limit,purpose);fixed,free=boundary_words(q['request']);q['boundary_words']=dict(fixed=fixed,free=free)
        save(OUT/'native-records.json.gz',oracle.records)
        if q['id']%8==0:print('native query',q['id'],purpose,q['result']['status'],round(q['seconds'],3),'seconds',flush=True)
        return q
    oracle.request=request
    def prepare(spec):
        c=compile_guards(spec,oracle,limit=plan['native_steps'],queries=plan['compile_queries']);compilation(spec,c,oracle.records)
        if c['status']!='complete':raise ValueError('incomplete first-order compilation retained')
        inv=admit(spec,specialize(library,spec,c['catalog']),oracle,plan['native_steps']);registry_binding(library,spec,c,inv,oracle.records)
        print(spec['id'],'compiled',len(c['basis']),'formulas;',len(inv['definitions']),'checked ground definitions',flush=True)
        return c,inv
    def observe(spec,compiled,inventory,mode,families,weights,seed,limits,name,stochastic=False,purpose='first_order_family_final'):
        job=dict(case=spec,compiled=compiled,inventory=inventory,arity=plan['arity'],families=families,
                 mode=mode,weights=weights,seed=seed,limits=limits,stochastic=stochastic)
        inp=TMP/(name+'-input.json');out=TMP/(name+'-output.json.gz');inp.write_text(json.dumps(job,separators=(',',':'))+'\n');stage=time.perf_counter()
        subprocess.run([sys.executable,str(HERE/'first_order_family_worker.py'),str(inp),str(out)],check=True,env=dict(os.environ,PYTHONPYCACHEPREFIX='/private/tmp/gcts-native-wang-pycache'))
        obs=load(out);obs['worker_wall_seconds']=time.perf_counter()-stage;model_binding(spec,compiled,inventory,obs['model'],plan['arity'],families)
        obs['tree_check']=extended_tree(spec,obs['model'],obs['search'],inventory if families else [],weights if mode in ('learned','no-family') else None,obs['model']['initial_marks'])
        obs.update(native_query=None,cached_native_acceptance=False)
        proof=obs['search']['proof']
        if proof is not None:
            native=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=used_definitions(inventory,proof),proof=proof,target=spec['target']);key=digest(native)
            if key in cache:obs.update(native_query=cache[key],cached_native_acceptance=True)
            else:
                q=oracle.request(native,plan['native_steps'],purpose)
                if q['result']['status']!='accepted':raise ValueError('discovered whole proof not accepted by unchanged native checker')
                cache[key]=q['id'];obs['native_query']=q['id']
        print(name,obs['search']['status'],'attempts',obs['search']['metrics'].get('attempts',0),'native',obs['native_query'],'cached',obs['cached_native_acceptance'],flush=True)
        return obs
    try:
        donor_records=load(DOC/'first-order-native-001.json.gz');donors=[]
        for descriptor in plan['donors']:
            raw=load(ROOT/descriptor['artifact']);source=next(o for o in raw['observations'] if o['mode']=='base' and o['repetition']==1)
            q=donor_records[source['native_query']]
            native=dict(protocol='gcts-fol-1',theory=raw['case']['theory'],blocks=[],proof=source['search']['proof'],target=raw['case']['target'])
            if q['result']['status']!='accepted' or q['request']!=native:raise ValueError('prior audited donor binding')
            provenance=dict(source_notebook=67,source_artifact=descriptor['artifact'],source_artifact_sha256=plan['data_dependencies'][descriptor['artifact']]['sha256'],source_query=q['id'],request_sha256=q['request_sha256'])
            family=mine(q['request'],None,provenance);library.append(family);donors.append(dict(source_query=q['id'],source_artifact=descriptor['artifact'],request=q['request'],family=family))
        spec=plan['promotion'];compiled,inventory=prepare(spec)
        obs=observe(spec,compiled,inventory,'fixed',True,None,plan['seed'],plan['search_limits'],'promotion',purpose='first_order_family_promotion')
        promoted=dict(case=spec,compiled=compiled,inventory=inventory,observation=obs)
        if obs['search']['proof'] is None:save(OUT/'promotion-unknown.json.gz',promoted);raise ValueError('bounded promotion unresolved; retain evidence rather than invent a family')
        q=oracle.records[obs['native_query']];family=mine(q['request'],inventory,dict(source_notebook=68,source_query=q['id'],request_sha256=q['request_sha256'],source_case=spec['id']))
        if not family['dependencies']:raise ValueError('promotion does not call an earlier discovered family')
        library.append(family);promoted['family']=family
        stage=time.perf_counter();training=dict(donors=donors,promotion=promoted,library=copy.deepcopy(library),cases=[],episodes=[],features=FEATURES,rate=.4)
        for spec in plan['training_cases']:
            c,inv=prepare(spec);training['cases'].append(dict(case=spec,compiled=c,inventory=inv))
        training['discovery_and_matching_seconds']=time.perf_counter()-started;weights=[0.]*len(FEATURES);baseline=0.;train_start=time.perf_counter()
        for i in range(plan['episodes']):
            item=training['cases'][i%len(training['cases'])];spec=item['case'];before=weights.copy()
            obs=observe(spec,item['compiled'],item['inventory'],'learned',True,before,plan['seed']+i,plan['training_limits'],'training-'+str(i),True,'first_order_family_training')
            value=reward(obs['search'],obs['search']['proof'] is not None,plan['arity']);weights,baseline,learning=update(weights,obs['search']['events'],value,baseline)
            training['episodes'].append(dict(id=i,case=spec['id'],observation=obs,weights_before=before,weights_after=weights.copy(),baseline_after=baseline,learning=learning))
            training.update(weights=weights.copy(),baseline=baseline,training_seconds=time.perf_counter()-train_start);save(OUT/'training.json.gz',training)
        save(OUT/'training.json.gz',training)
        (OUT/'policy.json').write_text(json.dumps(dict(features=FEATURES,weights=weights,library=library,episodes=plan['episodes'],source='fresh zero-start first-order training'),indent=2)+'\n')
        for spec in plan['cases']:
            c,inv=prepare(spec);raw=dict(case=spec,compiled=c,inventory=inv,models={},observations=[])
            for rep in plan['repetitions']:
                for lane in plan['schedules'][str(rep)]:
                    method=plan['lanes'][lane];name=spec['id']+'-'+lane+'-r'+str(rep)
                    obs=observe(spec,c,inv,method['mode'],method['families'],weights if method['mode'] in ('learned','no-family') else None,plan['seed'],plan['search_limits'],name)
                    obs.update(lane=lane,repetition=rep);record=obs.pop('model');model_id='family' if method['families'] else 'primitive'
                    if model_id in raw['models']:
                        stable=lambda r:{k:v for k,v in r.items() if k!='compile_seconds'}
                        if digest(stable(record))!=digest(stable(raw['models'][model_id])):raise ValueError('model changed across fresh workers')
                    else:raw['models'][model_id]=record
                    obs['model_id']=model_id;raw['observations'].append(obs);save(OUT/(spec['id']+'.json.gz'),raw)
            summaries.append(dict(id=spec['id'],compile_seconds=c['seconds'],matching_seconds=inv['matching_seconds'],admission_seconds=inv['admission_seconds'],interfaces=len(inv['interfaces']),definitions=len(inv['definitions']),observations=[dict(lane=o['lane'],repetition=o['repetition'],status=o['search']['status'],attempts=o['search']['metrics'].get('attempts',0),search_seconds=o['search']['seconds'],worker_wall_seconds=o['worker_wall_seconds'],peak_rss_bytes=o['peak_rss_bytes'],native_query=o['native_query']) for o in raw['observations']]))
            (OUT/'summary.json').write_text(json.dumps(dict(status='running',cases=summaries),indent=2)+'\n')
        result=dict(status='complete',cases=summaries,families=len(library),episodes=plan['episodes'],native_queries=len(oracle.records),distinct_whole_proofs=len(cache),seconds=time.perf_counter()-started)
        (OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print('FIRST ORDER FAMILY PILOT COMPLETE',time.perf_counter()-started,flush=True)
    finally:oracle.close()

if __name__=='__main__':main()
