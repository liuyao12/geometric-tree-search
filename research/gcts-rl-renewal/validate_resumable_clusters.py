"""Bind the measured sources, independent replay, reader and regressions."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
from export_resumable_clusters import project
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();data=json.loads((DOC/'resumable-clusters-001.json').read_bytes());audit=json.loads((DOC/'resumable-clusters-audit-001.json').read_bytes())
    if audit['status']!='passed' or audit['input_sha256']!=digest(DOC/'resumable-clusters-001.json'):raise ValueError('exact audit input')
    if audit['source_sha256']!=digest(HERE/'audit_resumable_clusters.py'):raise ValueError('independent audit source')
    for n,pin in audit['helpers'].items():
        if digest(HERE/n)!=pin:raise ValueError('audit helper '+n)
    for n,pin in data['sources'].items():
        if digest(HERE/n)!=pin:raise ValueError('measured source '+n)
    if canonical(project(data,audit))+b'\n'!=(DOC/'resumable-clusters-reader-001.json').read_bytes():raise ValueError('exact reader projection')
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_resumable_clusters.py','-v'],capture_output=True,text=True,check=True);print(tests.stderr,flush=True)
    node=subprocess.run([NODE,str(HERE/'test_resumable_reader.cjs')],capture_output=True,text=True,check=True);reader=json.loads(node.stdout)
    names=('resumable_clusters.py','resumable_cases.py','run_resumable_clusters.py','check_resumable_clusters.py','audit_resumable_clusters.py',
        'test_resumable_clusters.py','export_resumable_clusters.py','test_resumable_reader.cjs','validate_resumable_clusters.py')
    docs=('resumable-clusters.html','resumable-clusters.js','resumable-clusters-reader-001.json')
    out=dict(version='resumable-clusters-validation-001',status='passed',tests=5,reader=reader,exact_projection=True,
        sources={n:digest(HERE/n) for n in names},documents={n:digest(DOC/n) for n in docs},seconds=time.perf_counter()-began)
    (DOC/'resumable-clusters-validation-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
