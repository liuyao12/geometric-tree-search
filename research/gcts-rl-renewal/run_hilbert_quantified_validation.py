"""Record scope regressions, exact reader mutations and artifact bindings."""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOCS=ROOT/'docs/research/gcts-rl-renewal'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--node',default='node');args=parser.parse_args();began=time.perf_counter();logs=[];runs=[]
    for name,cmd in [('scope',[sys.executable,str(HERE/'test_hilbert_quantified.py')]),('reader',[args.node,str(HERE/'test_hilbert_quantified_reader.cjs')])]:
        t=time.perf_counter();r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);output=r.stdout+r.stderr;logs.append(name+'\n'+output)
        if r.returncode:raise ValueError(name+' failed: '+output)
        runs.append(dict(id=name,exit_code=r.returncode,seconds=time.perf_counter()-t,output=output))
    if 'Ran 4 tests' not in runs[0]['output'] or 'OK' not in runs[0]['output']:raise ValueError('scope regression count')
    reading=json.loads(runs[1]['output']);log='\n'.join(logs);(DOCS/'hilbert-quantified-validation-001.log').write_text(log)
    files=[HERE/n for n in ('quantified_proof_rules.py','hilbert_quantified_tiles.py','audit_hilbert_quantified.py','run_hilbert_quantified.py','test_hilbert_quantified.py','export_hilbert_quantified.py','test_hilbert_quantified_reader.cjs','run_hilbert_quantified_validation.py')]+[DOCS/n for n in ('hilbert-quantified.js','hilbert-quantified.html','hilbert-quantified-reader-001.json','hilbert-quantified-001.json.gz')]
    data=dict(status='passed',date='2026-10-10',python_tests=4,reader=reading,runs=runs,total_seconds=time.perf_counter()-began,sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},log=dict(file='hilbert-quantified-validation-001.log',sha256=hashlib.sha256(log.encode()).hexdigest()),scope='Generic quantifier scope, escaping-witness rejection, capture avoidance for colliding outer roles, forbidden block generalization, every reader formula/English rendering, four visible binder cells, exact tile/contact mutation controls. Full cold trace and all block audits are in the archive. No complete-Hilbert or GCTS acceleration claim.')
    (DOCS/'hilbert-quantified-validation-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print(json.dumps(dict(status='passed',python_tests=4,reader=reading)))
if __name__=='__main__':main()
