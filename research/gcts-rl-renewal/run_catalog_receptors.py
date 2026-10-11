"""Frozen representation/cost comparison; no new training or theorem scripts."""
import gzip,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from certificate_boundary_search import digest
from semantic_inventory_worker import oracle_for
from semantic_lemma_inventory import used_definitions
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'.gcts-active/catalog-receptors-20261011';TMP=Path('/private/tmp/gcts-catalog-receptors-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def pins(plan):
    for f,h in plan['sources'].items():
        if hashlib.sha256((ROOT/f).read_bytes()).hexdigest()!=h:raise ValueError('source changed '+f)
    for f,r in plan['data_dependencies'].items():
        p=ROOT/f
        if p.stat().st_size!=r['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:raise ValueError('data changed '+f)

def main():
    began=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());pins(plan);TMP.mkdir(parents=True,exist_ok=True)
    donor=json.loads((ROOT/plan['input_reader']).read_text());inputs={x['spec']['id']:x for x in donor['cases']}
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP/'native'),executable=str(TMP/'oracle')));cache={};summary=[]
    try:
        for name in plan['cases']:
            item=inputs[name];spec=item['spec'];raw=dict(case=spec,compiled=item['compiled'],inventory=item['inventory'],observations=[])
            for rep in plan['repetitions']:
                for lane in plan['schedules'][str(rep)]:
                    method=plan['lanes'][lane];tag=name+'-'+lane+'-r'+str(rep);model_file=OUT/(name+'-'+method['representation']+'-model.json.gz')
                    job=dict(case=spec,compiled=item['compiled'],inventory=item['inventory'],weights=plan['weights'],seed=plan['seed'],limits=plan['limits'],**method)
                    if not model_file.exists():job['save_model']=str(model_file)
                    inp=TMP/(tag+'-input.json');out=TMP/(tag+'-output.json.gz');inp.write_text(json.dumps(job,separators=(',',':'))+'\n')
                    stage=time.perf_counter();subprocess.run([sys.executable,str(HERE/'catalog_receptor_worker.py'),str(inp),str(out)],check=True,env=dict(os.environ,PYTHONPYCACHEPREFIX='/private/tmp/gcts-native-wang-pycache'))
                    obs=load(out);obs.update(lane=lane,repetition=rep,worker_wall_seconds=time.perf_counter()-stage,native_query=None,cached_native_acceptance=False)
                    proof=obs['search']['proof']
                    if proof is not None:
                        req=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=used_definitions(raw['inventory'],proof),proof=proof,target=spec['target']);key=digest(req)
                        if key in cache:obs.update(native_query=cache[key],cached_native_acceptance=True)
                        else:
                            q=oracle.request(req,plan['native_steps'],'catalog_receptor_whole');fixed,free=boundary_words(q['request']);q['boundary_words']=dict(fixed=fixed,free=free)
                            save(OUT/'native.json.gz',oracle.records)
                            if q['result']['status']!='accepted':raise ValueError('fresh whole native check incomplete or rejected')
                            cache[key]=q['id'];obs['native_query']=q['id']
                    raw['observations'].append(obs);save(OUT/(name+'.json.gz'),raw)
                    print(tag,obs['search']['status'],obs['search']['metrics'].get('attempts',0),'attempts',round(obs['search']['seconds'],3),'search seconds',round(obs['setup_seconds'],3),'setup seconds',round(obs['peak_rss_bytes']/2**20,1),'MiB',flush=True)
            summary.append(dict(id=name,observations=[{k:o[k] for k in ('lane','repetition','setup_seconds','model_reporting_seconds','model_stats','worker_wall_seconds','peak_rss_bytes','native_query')}|dict(status=o['search']['status'],attempts=o['search']['metrics'].get('attempts',0),search_seconds=o['search']['seconds']) for o in raw['observations']]))
            (OUT/'summary.json').write_text(json.dumps(dict(status='running',cases=summary),indent=2)+'\n')
        (OUT/'summary.json').write_text(json.dumps(dict(status='complete',cases=summary,native_queries=len(oracle.records),seconds=time.perf_counter()-began),indent=2)+'\n')
        print('CATALOG STUDY COMPLETE',time.perf_counter()-began,flush=True)
    finally:oracle.close()

if __name__=='__main__':main()
