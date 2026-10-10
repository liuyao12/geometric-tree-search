import json,hashlib,subprocess,time
from pathlib import Path
from export_factored_receptors import build
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal';NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();view=json.loads((DOC/'factored-receptors-reader-001.json').read_text())
    if view!=json.loads(json.dumps(build())):raise ValueError('complete audited reader projection')
    r=subprocess.run(['python3','-m','unittest','discover','-s',str(HERE),'-p','test_factored_receptors.py','-v'],capture_output=True,text=True,check=True);print(r.stderr,flush=True)
    reader=json.loads(subprocess.check_output([NODE,str(HERE/'test_factored_reader.cjs')]))
    sources=('factored_receptors.py','check_factored_receptors.py','run_factored_receptors.py','audit_factored_receptors.py','test_factored_receptors.py','run_factored_wang.py','audit_factored_wang.py','export_factored_receptors.py','test_factored_reader.cjs','validate_factored_receptors.py')
    out=dict(version='factored-receptors-validation-001',status='passed',sources={n:digest(HERE/n) for n in sources},documents={n:digest(DOC/n) for n in ('factored-receptors.html','factored-receptors.js','factored-receptors-reader-001.json')},tests=10,reader=reader,exact_projection=True,seconds=time.perf_counter()-began,browser=dict(status='pending'))
    (DOC/'factored-receptors-validation-001.json').write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps(reader),flush=True)
if __name__=='__main__':main()
