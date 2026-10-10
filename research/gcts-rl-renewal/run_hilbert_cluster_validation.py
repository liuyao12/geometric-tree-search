"""Record exact indexed-join and displayed aggregate/English validation."""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOCS=ROOT/'docs/research/gcts-rl-renewal'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--node',default='node');args=parser.parse_args();began=time.perf_counter();runs=[];logs=[]
    for name,cmd in [('indexed-join',[sys.executable,str(HERE/'test_indexed_proof_clusters.py')]),('reader',[args.node,str(HERE/'test_hilbert_cluster_reader.cjs')])]:
        t=time.perf_counter();r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);out=r.stdout+r.stderr
        if r.returncode:raise ValueError(name+': '+out)
        runs.append(dict(id=name,seconds=time.perf_counter()-t,exit_code=r.returncode,output=out));logs.append(name+'\n'+out)
    if 'Ran 4 tests' not in runs[0]['output'] or 'OK' not in runs[0]['output']:raise ValueError('join test count')
    d=json.loads((DOCS/'hilbert-witness-clusters-001.json').read_text());audit=d['independent_audit'];a=HERE/audit['auditor']['file']
    if audit['status']!='passed' or hashlib.sha256(a.read_bytes()).hexdigest()!=audit['auditor']['sha256']:raise ValueError('auditor binding')
    log='\n'.join(logs);(DOCS/'hilbert-cluster-validation-001.log').write_text(log)
    names=('indexed_proof_clusters.py','hilbert_witness_clusters.py','test_indexed_proof_clusters.py','run_hilbert_witness_clusters.py','audit_hilbert_witness_clusters.py','audit_hilbert_witness_clusters_v2.py','export_hilbert_witness_clusters.py','test_hilbert_cluster_reader.cjs','run_hilbert_cluster_validation.py')
    files=[HERE/n for n in names]+[DOCS/n for n in ('hilbert-clusters.html','hilbert-clusters.js','hilbert-cluster-reader-001.json','hilbert-witness-clusters-001.json')]+[DOCS/x['file'] for x in d['donors']+d['cases']]
    result=dict(status='passed',date='2026-10-10',python_tests=4,reader=json.loads(runs[1]['output']),runs=runs,total_seconds=time.perf_counter()-began,sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},log=dict(file='hilbert-cluster-validation-001.log',sha256=hashlib.sha256(log.encode()).hexdigest()),scope='Exact exhaustive/indexed join equality including repeated and nonlocal contacts; all displayed base and aggregate point values, formula/English rendering, external receptor interfaces, actual source-family expansions and ownership; mutation rejection and report/manifest/history bindings. Complete 29-record inventory/prefix/native audits are recorded separately. Receptor deformation, recursive hierarchy, uniform computational tiles and RL are not claimed.')
    (DOCS/'hilbert-cluster-validation-001.json').write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps(dict(status='passed',python_tests=4,reader=result['reader'])))
if __name__=='__main__':main()
