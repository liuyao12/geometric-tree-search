"""Save the bounded soundness/reader test log and current artifact bindings."""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOCS=ROOT/'docs/research/gcts-rl-renewal'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--node',default='node');args=parser.parse_args();began=time.perf_counter();logs=[];runs=[]
    for name,cmd in [('soundness',[sys.executable,str(HERE/'test_hilbert_incidence.py')]),('reader',[args.node,str(HERE/'test_hilbert_reader.cjs')])]:
        before=time.perf_counter();r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);output=r.stdout+r.stderr;logs.append(name+'\n'+output)
        if r.returncode:raise ValueError(name+' failed: '+output)
        runs.append(dict(id=name,exit_code=r.returncode,seconds=time.perf_counter()-before,output=output))
    if 'Ran 6 tests' not in runs[0]['output'] or 'OK' not in runs[0]['output']:raise ValueError('test count')
    reading=json.loads(runs[1]['output']);log='\n'.join(logs);(DOCS/'hilbert-validation-001.log').write_text(log)
    files=[HERE/'hilbert_incidence_tiles.py',HERE/'audit_hilbert_incidence.py',HERE/'test_hilbert_incidence.py',HERE/'test_hilbert_reader.cjs',Path(__file__),DOCS/'hilbert-proofs.js',DOCS/'hilbert-reader-001.json',DOCS/'hilbert-incidence-001.json']
    data=dict(status='passed',date='2026-10-10',python_tests=6,reader=reading,runs=runs,total_seconds=time.perf_counter()-began,sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},log=dict(file='hilbert-validation-001.log',sha256=hashlib.sha256(log.encode()).hexdigest()),scope='Finite compiled inventory validation, source/signature and proof/point negative controls, two GCTS proof replays, abstract model/countermodel evaluation, symbol renaming, actual reader marking/contact mutations and all primitive formula/English renderings. Independent full cold search audits are in the bound dataset; generic kernel soundness and full Hilbert geometry remain open.')
    (DOCS/'hilbert-validation-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n');print(json.dumps(dict(status='passed',python_tests=6,reader=reading,total_seconds=data['total_seconds'])))
if __name__=='__main__':main()
