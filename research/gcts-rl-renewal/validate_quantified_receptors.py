import hashlib,json,subprocess,time
from pathlib import Path
from export_quantified_receptors import build
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal';NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    start=time.perf_counter();view=json.loads((DOC/'quantified-receptors-reader-001.json').read_bytes())
    if view!=json.loads(json.dumps(build())):raise ValueError('complete reader/audit projection')
    r=subprocess.run(['python3','-m','unittest','discover','-s',str(HERE),'-p','test_quantified_receptors.py','-v'],capture_output=True,text=True,check=True);print(r.stderr,flush=True)
    reader=json.loads(subprocess.check_output([NODE,str(HERE/'test_quantified_reader.cjs')]))
    files=('quantified_receptors.py','quantified_receptor_cases.py','check_quantified_receptors.py','run_quantified_receptors.py','audit_quantified_receptors.py','test_quantified_receptors.py','run_quantified_wang.py','audit_quantified_wang.py','export_quantified_receptors.py','test_quantified_reader.cjs','validate_quantified_receptors.py')
    out=dict(version='quantified-receptors-validation-001',status='passed',tests=12,reader=reader,sources={n:digest(HERE/n) for n in files},documents={n:digest(DOC/n) for n in ('quantified-receptors.html','quantified-receptors.js','quantified-receptors-reader-001.json')},exact_projection=True,seconds=time.perf_counter()-start,browser=dict(status='pending'))
    (DOC/'quantified-receptors-validation-001.json').write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps(reader),flush=True)
if __name__=='__main__':main()
