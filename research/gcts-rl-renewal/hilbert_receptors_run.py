"""Frozen full catalog pilot. No searched proof is read as an input."""
import gzip,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from hilbert_receptors_catalog import prepare
from semantic_inventory_worker import oracle_for
from semantic_lemma_inventory import used_definitions
from proof_boundary import boundary_words
from certificate_boundary_search import digest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/hilbert-receptors-20261011';TMP=Path('/private/tmp/gcts-hilbert-receptors-20261011')
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def main():
    started=time.perf_counter();plan=json.loads((OUT/'plan.json').read_text());TMP.mkdir(parents=True,exist_ok=True)
    for f,h in plan['sources'].items():
        if hashlib.sha256((ROOT/f).read_bytes()).hexdigest()!=h:raise ValueError('frozen source changed '+f)
    for f,d in plan['data_dependencies'].items():
        p=ROOT/f
        if p.stat().st_size!=d['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=d['sha256']:raise ValueError('data dependency changed '+f)
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True)
    oracle=oracle_for(dict(directory=str(TMP/'native'),executable=str(TMP/'oracle')));request=oracle.request;cache={};summaries=[]
    def submit(r,limit,purpose):
        q=request(r,limit,purpose);fixed,free=boundary_words(q['request']);q['boundary_words']=dict(fixed=fixed,free=free);save(OUT/'native.json.gz',oracle.records)
        print('native',q['id'],purpose,q['result']['status'],round(q['seconds'],3),'seconds',flush=True);return q
    oracle.request=submit
    try:
        for spec in plan['cases']:
            c,inv,construction=prepare(spec,oracle,plan['native_steps']);raw=dict(case=spec,compiled=c,inventory=inv,construction_seconds=construction,observations=[])
            for rep in plan['repetitions']:
                for lane in plan['schedules'][str(rep)]:
                    method=plan['lanes'][lane];tag=spec['id']+'-'+lane+'-r'+str(rep)
                    job=dict(case=spec,compiled=c,inventory=inv,seed=plan['seed'],weights=plan['weights'],limits=plan['limits'],**method)
                    inp=TMP/(tag+'-input.json');out=TMP/(tag+'-output.json.gz');inp.write_text(json.dumps(job,separators=(',',':'))+'\n');stage=time.perf_counter()
                    subprocess.run([sys.executable,str(HERE/'hilbert_receptors_worker.py'),str(inp),str(out)],check=True,env=dict(os.environ,PYTHONPYCACHEPREFIX='/private/tmp/gcts-native-wang-pycache'))
                    obs=json.loads(gzip.decompress(out.read_bytes()));obs.update(lane=lane,repetition=rep,worker_wall_seconds=time.perf_counter()-stage,native_query=None,cached_native_acceptance=False)
                    if obs['search']['proof'] is not None:
                        native=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=used_definitions(inv,obs['search']['proof']),proof=obs['search']['proof'],target=spec['target']);key=digest(native)
                        if key in cache:obs.update(native_query=cache[key],cached_native_acceptance=True)
                        else:
                            q=submit(native,plan['native_steps'],'hilbert_discovered_whole')
                            if q['result']['status']!='accepted':raise ValueError('whole proof native check unfinished')
                            cache[key]=q['id'];obs['native_query']=q['id']
                    print(tag,obs['search']['status'],obs['search']['metrics'].get('attempts',0),'attempts',round(obs['search']['seconds'],3),'seconds',flush=True)
                    raw['observations'].append(obs);save(OUT/(spec['id']+'.json.gz'),raw)
            summaries.append(dict(id=spec['id'],construction_seconds=construction,compile_seconds=c['seconds'],admission_seconds=inv['admission_seconds'],interfaces=len(inv['interfaces']),observations=[dict(lane=o['lane'],repetition=o['repetition'],status=o['search']['status'],attempts=o['search']['metrics'].get('attempts',0),search_seconds=o['search']['seconds'],setup_seconds=o['setup_seconds'],worker_wall_seconds=o['worker_wall_seconds'],peak_rss_bytes=o['peak_rss_bytes'],native_query=o['native_query']) for o in raw['observations']]))
            (OUT/'summary.json').write_text(json.dumps(dict(status='running',cases=summaries),indent=2)+'\n')
        (OUT/'summary.json').write_text(json.dumps(dict(status='complete',cases=summaries,native_queries=len(oracle.records),seconds=time.perf_counter()-started),indent=2)+'\n');print('HILBERT RECEPTORS COMPLETE',flush=True)
    finally:oracle.close()
if __name__=='__main__':main()
