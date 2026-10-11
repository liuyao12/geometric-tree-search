"""Execute predeclared first-order compilation and fresh-process search lanes."""
import gzip,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from certificate_boundary_search import digest
from first_order_receptors import compile_guards
from semantic_inventory_worker import oracle_for
from audit_first_order import compilation,model_binding
from audit_prefix_failure_markings import extended_tree
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOC=ROOT/'docs/research/gcts-rl-renewal'
OUT=ROOT/'.gcts-active/first-order-20261011';TMP=Path('/private/tmp/gcts-first-order-20261011')
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());TMP.mkdir(parents=True,exist_ok=True)
    for f,h in plan['source_sha256'].items():
        if hashlib.sha256((ROOT/f).read_bytes()).hexdigest()!=h:raise ValueError('changed measured source '+f)
    policy_bytes=(DOC/'semantic-inventory-policy-001.json').read_bytes()
    if hashlib.sha256(policy_bytes).hexdigest()!=plan['policy_sha256']:raise ValueError('frozen weights changed')
    weights=json.loads(policy_bytes)['weights'];subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP/'native'),executable=str(TMP/'oracle')));cache={};summaries=[]
    try:
        for spec in plan['cases']:
            compiled=compile_guards(spec,oracle,limit=plan['native_steps'],queries=plan['compile_queries'])
            print(spec['id'],'native compilation',compiled['status'],'queries',len(compiled['queries']),flush=True)
            compilation(spec,compiled,oracle.records)
            if compiled['status']!='complete':
                save(OUT/'native-records.json.gz',oracle.records);raise ValueError('incomplete catalog retained; cannot run point lanes')
            raw=dict(case=spec,compiled=compiled,model=None,observations=[],policy_sha256=plan['policy_sha256'])
            for rep in plan['repetitions']:
                for mode in plan['schedules'][str(rep)]:
                    job=dict(case=spec,compiled=compiled,mode=mode,repetition=rep,weights=weights,
                        seed=plan['seed'],limits=plan['search_limits'])
                    name=spec['id']+'-'+mode+'-r'+str(rep);inp=TMP/(name+'-input.json');out=TMP/(name+'-output.json.gz')
                    inp.write_text(json.dumps(job,separators=(',',':'))+'\n');start=time.perf_counter()
                    subprocess.run([sys.executable,str(HERE/'first_order_worker.py'),str(inp),str(out)],check=True,
                        env=dict(os.environ,PYTHONPYCACHEPREFIX='/private/tmp/gcts-native-wang-pycache'))
                    obs=json.loads(gzip.decompress(out.read_bytes()));obs['worker_wall_seconds']=time.perf_counter()-start;record=obs.pop('model')
                    model_binding(spec,compiled,record)
                    if raw['model'] is None:raw['model']=record
                    else:
                        def stable(r):return {k:v for k,v in r.items() if k!='compile_seconds'}
                        if digest(stable(record))!=digest(stable(raw['model'])):raise ValueError('model changed across workers')
                    obs['tree_check']=extended_tree(spec,record,obs['search'],[],weights if mode=='learned' else None,record['initial_marks'])
                    obs.update(native_query=None,cached_native_acceptance=False)
                    if obs['search']['proof'] is not None:
                        request=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[],proof=obs['search']['proof'],target=spec['target']);key=digest(request)
                        if key in cache:obs.update(native_query=cache[key],cached_native_acceptance=True)
                        else:
                            q=oracle.request(request,plan['native_steps'],'first_order_final')
                            if q['result']['status']!='accepted':raise ValueError('whole searched first-order certificate not accepted')
                            cache[key]=q['id'];obs['native_query']=q['id']
                    raw['observations'].append(obs)
                    print(name,obs['search']['status'],'attempts',obs['search']['metrics'].get('attempts',0),'native',obs['native_query'],'cached',obs['cached_native_acceptance'],flush=True)
                    save(OUT/(spec['id']+'.json.gz'),raw)
                    for q in oracle.records:
                        fixed,free=boundary_words(q['request']);q['boundary_words']=dict(fixed=fixed,free=free)
                    save(OUT/'native-records.json.gz',oracle.records)
            summary=dict(id=spec['id'],basis=len(compiled['basis']),schemes=len(compiled['admitted_schemes']),compile_seconds=compiled['seconds'],
                observations=[dict(mode=o['mode'],repetition=o['repetition'],status=o['search']['status'],attempts=o['search']['metrics'].get('attempts',0),search_seconds=o['search']['seconds'],worker_wall_seconds=o['worker_wall_seconds'],peak_rss_bytes=o['peak_rss_bytes'],native_query=o['native_query']) for o in raw['observations']])
            summaries.append(summary);(OUT/'summary.json').write_text(json.dumps(dict(status='running',cases=summaries),indent=2)+'\n')
        (OUT/'summary.json').write_text(json.dumps(dict(status='complete',cases=summaries,native_queries=len(oracle.records),distinct_final_proofs=len(cache),seconds=time.perf_counter()-began),indent=2)+'\n')
        print('FIRST ORDER PILOT COMPLETE',time.perf_counter()-began,flush=True)
    finally:oracle.close()

if __name__=='__main__':main()
