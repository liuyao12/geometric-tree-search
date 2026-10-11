"""Full 48-binding admission, finite recipients and checkpointed certification.

No incomplete expanded inventory is used to assert forced or dead points. Every
searched tree is saved before its whole native request, including unknowns.
"""
import copy,gzip,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from hilbert_promotion_family_catalog import build
from semantic_inventory_worker import oracle_for
from semantic_lemma_inventory import used_definitions
from certificate_boundary_search import digest
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/hilbert-promotion-family-20261011'
TMP=Path('/private/tmp/gcts-hilbert-promotion-family-20261011')
def save(path,value):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_bytes(gzip.compress(json.dumps(value,separators=(',',':')).encode(),mtime=0));temp.replace(path)
def plain(path,value):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text())
    for path,sha in plan['sources'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=sha:raise ValueError('frozen source changed '+path)
    for path,item in plan['data_dependencies'].items():
        f=ROOT/path
        if hashlib.sha256(f.read_bytes()).hexdigest()!=item['sha256'] or f.stat().st_size!=item['bytes']:raise ValueError('frozen input changed '+path)
    source=json.loads(gzip.decompress((ROOT/plan['source_native_record']).read_bytes()))[0]
    if source['result']['status']!='accepted':raise ValueError('source receptor not admitted')
    stage=time.perf_counter();catalog=build(source['request']);construction=time.perf_counter()-stage
    if catalog['cases']!=plan['cases'] or catalog['parameter_domains']!=plan['parameter_domains'] or catalog['bindings_before_dedup']!=48:raise ValueError('predeclared complete domain')
    save(OUT/'catalog.json.gz',catalog);TMP.mkdir(parents=True,exist_ok=True)
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP/'production'),executable=str(TMP/'oracle')))
    progress=dict(status='admitting',construction_seconds=construction,bindings=48,distinct_promoted=len(catalog['promoted_definitions']),base_admissions=[],promoted_admissions=[],groups={},observations=[],native_queries=0)
    def checkpoint():
        progress.update(native_queries=len(oracle.records),seconds=time.perf_counter()-began);plain(OUT/'progress.json',progress)
    def submit(request,limit,purpose,**metadata):
        rec=oracle.request(request,limit,purpose);rec.update(native_limit=limit,**metadata)
        fixed,free=boundary_words(request);rec['boundary_words']=dict(fixed=fixed,free=free)
        save(OUT/'native.json.gz',oracle.records);checkpoint()
        print('native',rec['id'],purpose,rec['result']['status'],round(rec['seconds'],3),'seconds',flush=True);return rec
    taut=['imp',['bot'],['bot']];admission_start=time.perf_counter()
    def request(theory,blocks,proof=None,target=None):return dict(protocol='gcts-fol-1',theory=theory,blocks=blocks,proof=proof or [dict(rule='tautology',formula=taut)],target=taut if target is None else target)
    try:
        q=submit(request(catalog['theory'],[]),plan['admission_native_steps'],'family_theory_admission')
        if q['result']['status']!='accepted':
            progress.update(status='unknown_theory_admission',native_outcome=q['result']['status']);checkpoint();return
        for kind,definitions in [('base',catalog['base_definitions']),('promoted',catalog['promoted_definitions'])]:
            byname={d['name']:d['definition'] for d in catalog['base_definitions']}
            for d in definitions:
                if time.perf_counter()-admission_start>=plan['admission_seconds_ceiling']:
                    progress.update(status='unknown_admission_cost_ceiling',admission_seconds=time.perf_counter()-admission_start,remaining_bindings=48-len(progress['promoted_admissions']));checkpoint();return
                dependencies=[byname[n] for n in d.get('dependencies',[])];q=submit(request(catalog['theory'],dependencies+[d['definition']]),plan['admission_native_steps'],'family_'+kind+'_admission',definition_name=d['name'])
                progress[kind+'_admissions'].append(dict(name=d['name'],query=q['id'],status=q['result']['status']));checkpoint()
                if q['result']['status']!='accepted':
                    progress.update(status='unknown_full_inventory_admission' if q['result']['status'].startswith('unknown') else 'rejected_full_inventory_admission',admission_seconds=time.perf_counter()-admission_start);checkpoint();return
        progress['admission_seconds']=time.perf_counter()-admission_start
        inventories={}
        for language,ds in [('level1',catalog['base_definitions']),('promoted',catalog['definitions'])]:
            inventories[language]=dict(status='native_accepted',definitions=ds,interfaces=[d['name'] for d in ds],native_blocks=[d['definition'] for d in ds],
                                       admissions=progress['base_admissions']+(progress['promoted_admissions'] if language=='promoted' else []),
                                       scope='Complete predeclared level-one interfaces'+(' plus all exact discovered-family matches.' if language=='promoted' else '.'))
        save(OUT/'inventories.json.gz',inventories);compiled={};progress['status']='compiling'
        for group,item in catalog['groups'].items():
            started=time.perf_counter();spec=item['representative'];ids=[];tauts=[]
            q=submit(request(spec['theory'],[]),plan['admission_native_steps'],'recipient_theory_admission',group=group);theory_query=q['id']
            if q['result']['status']!='accepted':progress.update(status='unknown_recipient_theory',native_outcome=q['result']['status']);checkpoint();return
            for i,f in enumerate(item['basis']):
                q=submit(request(spec['theory'],[],[dict(rule='tautology',formula=f)],f),plan['admission_native_steps'],'recipient_tautology_guard',group=group,basis_index=i);ids.append(q['id'])
                if q['result']['status']=='accepted':tauts.append(f)
                elif q['result']['status']!='rejected':progress.update(status='unknown_recipient_guard',native_outcome=q['result']['status']);checkpoint();return
            compiled[group]=dict(status='complete',catalog=item['catalog'],basis=item['basis'],variables=[],admitted_schemes=[],tautologies=tauts,queries=ids,theory_query=theory_query,seconds=time.perf_counter()-started)
            progress['groups'][group]=dict(compile_seconds=compiled[group]['seconds'],formulas=len(item['basis']));save(OUT/'compiled.json.gz',compiled);checkpoint()
        progress['status']='searching';cache={};checkpoint()
        for spec in plan['cases']:
            for rep in plan['repetitions']:
                for method_id in plan['schedules'][str(rep)]:
                    method=plan['methods'][method_id];inventory=inventories[method['language']];tag=spec['id']+'-'+method_id+'-r'+str(rep)
                    job=dict(case=spec,compiled=compiled[spec['group']],inventory=inventory,seed=plan['seed'],weights=plan['weights'],limits=plan['limits'],mode=method['mode'],feature_semantics=method['feature_semantics'])
                    inp=TMP/(tag+'-input.json');out=TMP/(tag+'-output.json.gz');inp.write_text(json.dumps(job,separators=(',',':'))+'\n');started=time.perf_counter()
                    subprocess.run([sys.executable,str(HERE/'hilbert_promotion_family_worker.py'),str(inp),str(out)],check=True,env=dict(os.environ,PYTHONPYCACHEPREFIX='/private/tmp/gcts-native-wang-pycache'))
                    obs=json.loads(gzip.decompress(out.read_bytes()));obs.update(case_id=spec['id'],method=method_id,language=method['language'],repetition=rep,worker_wall_seconds=time.perf_counter()-started,native_query=None,cached_native_acceptance=False,certification='pending' if obs['search']['proof'] is not None else 'no_proof')
                    # This exact file exists before whole certification is launched.
                    save(OUT/(tag+'.json.gz'),obs);checkpoint_sha=hashlib.sha256((OUT/(tag+'.json.gz')).read_bytes()).hexdigest();obs['pre_certification_checkpoint_sha256']=checkpoint_sha
                    proof=obs['search']['proof']
                    if proof is not None:
                        req=request(spec['theory'],used_definitions(inventory,proof),proof,spec['target']);key=digest(req)
                        if key in cache:obs.update(native_query=cache[key],cached_native_acceptance=True,certification='accepted')
                        else:
                            q=submit(req,plan['whole_native_steps'],'family_discovered_whole',observation=tag,pre_certification_checkpoint_sha256=checkpoint_sha)
                            obs.update(native_query=q['id'],certification=q['result']['status'])
                            if q['result']['status']=='accepted':cache[key]=q['id']
                    save(OUT/(tag+'-final.json.gz'),obs)
                    progress['observations'].append(dict(tag=tag,case_id=spec['id'],method=method_id,language=method['language'],repetition=rep,status=obs['search']['status'],certification=obs['certification'],attempts=obs['search']['metrics'].get('attempts',0),search_seconds=obs['search']['seconds'],setup_seconds=obs['setup_seconds'],peak_rss_bytes=obs['peak_rss_bytes'],native_query=obs['native_query'],cached_native_acceptance=obs['cached_native_acceptance']));checkpoint()
                    print(tag,obs['search']['status'],obs['certification'],obs['search']['metrics'].get('attempts',0),'attempts',round(obs['search']['seconds'],3),'seconds',flush=True)
        progress['status']='complete';checkpoint();print('COMPLETE FAMILY RECIPIENT STUDY',flush=True)
    except Exception as error:
        progress.update(status='failed',failure_type=type(error).__name__,failure_message=str(error));checkpoint();raise
    finally:oracle.close()
if __name__=='__main__':main()
