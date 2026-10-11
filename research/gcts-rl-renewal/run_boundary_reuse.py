"""Execute the predeclared boundary-reuse and direct-constraint comparison."""
import copy,gzip,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from certificate_boundary_search import digest
from boundary_reuse_constraints import packet
from audit_boundary_reuse import admit,parent,direct_tree,semantic_tree,direct_record
from audit_conditional_failure_markings import check_overlay
from audit_prefix_failure_markings import extended_tree
from semantic_inventory_worker import oracle_for,verify
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/boundary-reuse-20261011';TMP=Path('/private/tmp/gcts-boundary-reuse-20261011')


def load(path):return json.loads(gzip.decompress(path.read_bytes()))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):path.write_bytes(gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0))


def main():
    began=time.perf_counter();OUT.mkdir(parents=True,exist_ok=True);TMP.mkdir(parents=True,exist_ok=True)
    plan=json.loads((OUT/'plan.json').read_text())
    for path,h in plan['source_sha256'].items():
        if sha(ROOT/path)!=h:raise ValueError('predeclared source changed '+path)
    for path,h in plan['prior_source_closure'].items():
        if sha(ROOT/path)!=h:raise ValueError('prior proof source changed '+path)
    policy_path=DOC/'semantic-inventory-policy-001.json'
    if sha(policy_path)!=plan['policy_sha256']:raise ValueError('changed frozen policy')
    policy=json.loads(policy_path.read_text())
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP),executable=str(TMP/'oracle')))
    cache={};summaries=[]
    try:
        for config in plan['configs']:
            source_path=DOC/('conditional-001-'+config['source_case']+'.json.gz')
            source=dict(path=source_path.relative_to(ROOT).as_posix(),sha256=sha(source_path))
            raw=load(source_path)
            spec=copy.deepcopy(raw['case']);spec.update(id=config['id'],length=config['length'],
                scope='Same symbolic assertion and syntax inventory; declared finite boundary comparison.')
            constraints=packet(raw['learning'],source);constraints['pair_certificate']=raw['certificate']
            stage=time.perf_counter();certificate=admit(raw,spec,constraints,source);transfer_seconds=time.perf_counter()-stage
            print(config['id'],'transfer admitted',certificate['pairs'],'pairs',round(transfer_seconds,3),'seconds',flush=True)
            job=dict(case=spec,compiled=raw['compiled'],inventory=raw['inventory'],constraints=constraints,
                transfer_certificate=certificate,weights=policy['weights'],limits=plan['search_limits'])
            results=[];models={};checks={};p=parent(spec,raw['compiled'],raw['inventory'])
            for observation in plan['schedules'][config['id']]:
                job.update(observation);name=config['id']+'-'+observation['layer']+'-'+observation['mode']+'-r'+str(observation['repetition'])
                inp=TMP/(name+'-input.json');out=TMP/(name+'-output.json.gz')
                inp.write_text(json.dumps(job,separators=(',',':'))+'\n')
                stage=time.perf_counter()
                subprocess.run([sys.executable,str(HERE/'boundary_reuse_worker.py'),str(inp),str(out)],check=True,
                    env=dict(os.environ,PYTHONPYCACHEPREFIX='/private/tmp/gcts-native-wang-pycache'))
                wall=time.perf_counter()-stage;result=load(out);result['worker_wall_seconds']=wall
                layer=observation['layer'];mode=observation['mode'];record=result.pop('model')
                if layer in models:
                    from audit_conditional_failure_markings import plain
                    if digest(plain(record))!=digest(plain(models[layer])):raise ValueError('representation changed between fresh processes')
                else:models[layer]=record
                if layer=='original':
                    from audit_conditional_failure_markings import plain
                    if digest(plain(record))!=digest(plain(p.record())):raise ValueError('original inventory changed')
                elif layer=='point':checks['point']=check_overlay(p,raw['learning'],raw['certificate'],record)
                elif layer=='direct':checks['direct']=direct_record(models['original'],models['point'],record)
                if layer=='direct':checked=direct_tree(spec,models['original'],models['point'],result['search'],raw['inventory'])
                else:checked=extended_tree(spec,record,result['search'],raw['inventory'],
                        policy['weights'] if mode=='learned' else None,record['initial_marks'])
                result['tree_check']=checked;result['native_query']=None;result['cached_native_acceptance']=False
                proof=result['search']['proof']
                if proof is not None:
                    from semantic_lemma_inventory import used_definitions
                    request=dict(protocol='gcts-fol-1',theory=spec['theory'],
                        blocks=used_definitions(raw['inventory'],proof),proof=proof,target=spec['target'])
                    pin=digest(request)
                    if pin in cache:
                        result['native_query']=cache[pin];result['cached_native_acceptance']=True
                    else:
                        q=verify(oracle,spec,proof,raw['inventory'],'boundary_reuse_final')
                        if q['result']['status']!='accepted':raise ValueError('new proof native computation unfinished')
                        fixed,free=boundary_words(q['request']);q['boundary_words']=dict(fixed=fixed,free=free)
                        result['native_query']=q['id'];cache[pin]=q['id']
                        save(OUT/'native-records.json.gz',oracle.records)
                results.append(result)
                print(name,'independently checked','native',result['native_query'],'cache',result['cached_native_acceptance'],flush=True)
            equivalence=[]
            for rep in plan['repetitions']:
                a=next(x['search'] for x in results if x['layer']=='point' and x['mode']=='base' and x['repetition']==rep)
                b=next(x['search'] for x in results if x['layer']=='direct' and x['repetition']==rep)
                if semantic_tree(a)!=semantic_tree(b):raise ValueError('point/direct semantic trees differ')
                equivalence.append(dict(repetition=rep,nodes=a['metrics']['nodes'],sha256=semantic_tree(a)))
            data=dict(version='boundary-reuse-pilot-001',case=spec,source=source,compiled=raw['compiled'],inventory=raw['inventory'],
                constraints=constraints,transfer_certificate=certificate,transfer_seconds=transfer_seconds,
                source_collection_seconds=raw['learning']['seconds'],models=models,overlay_checks=checks,
                results=results,equivalence=equivalence,
                scope='Fresh-process reuse comparison with every lane twice; context, source failure labels and frozen policy disclosed. Exact direct/point control in base ordering, separate fixed/learned point observations. Search traces and native checks retained; no fresh failure learning, RL training, minimality or general acceleration claim.')
            path=OUT/(config['id']+'.json.gz');save(path,data)
            summaries.append(dict(case=config['id'],length=spec['length'],source=source,
                artifact=path.name,bytes=path.stat().st_size,transfer_seconds=transfer_seconds,
                results=[{k:x[k] for k in ('layer','mode','repetition','native_query','cached_native_acceptance','worker_wall_seconds','setup_seconds','representation_seconds','peak_rss_bytes')}
                         |dict(status=x['search']['status'],attempts=x['search']['metrics'].get('attempts',0),seconds=x['search']['seconds']) for x in results],
                equivalence=equivalence))
            (OUT/'summary.json').write_text(json.dumps(dict(status='running',cases=summaries),indent=2)+'\n')
        save(OUT/'native-records.json.gz',oracle.records)
        (OUT/'summary.json').write_text(json.dumps(dict(status='complete',cases=summaries,
            native_queries=len(oracle.records),seconds=time.perf_counter()-began),indent=2)+'\n')
        print('BOUNDARY COMPARISON COMPLETE',round(time.perf_counter()-began,3),'seconds',flush=True)
    finally:oracle.close()


if __name__=='__main__':main()
