"""Freeze all measured dependencies, exact reader projection and regressions."""
import gzip,hashlib,json,subprocess,sys,time
from pathlib import Path
from export_compact_contexts import project
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(n):
    p=DOC/n;return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def main():
    began=time.perf_counter();data,audit,native,other=[read(n) for n in ('compact-contexts-001.json','compact-contexts-audit-001.json','context-wang-001.json.gz','context-wang-audit-001.json.gz')]
    for out,name in ((audit,'compact-contexts-001.json'),(other,'context-wang-001.json.gz')):
        if out['input_sha256']!=digest(DOC/name):raise ValueError('audit input binding')
        for n,pin in out['helpers'].items():
            if digest(HERE/n)!=pin:raise ValueError('audit helper '+n)
    if audit['source_sha256']!=digest(HERE/'audit_compact_contexts.py') or other['source_sha256']!=digest(HERE/'audit_context_wang.py'):raise ValueError('audit sources')
    for out in (data,native):
        for n,pin in out['sources'].items():
            if digest(HERE/n)!=pin:raise ValueError('producer source '+n)
    for n,pin in native['reused_artifacts'].items():
        if digest(DOC/n)!=pin:raise ValueError('native input '+n)
    for n,pin in native['reused_source_pins'].items():
        if digest(HERE/n)!=pin:raise ValueError('fixed shared source '+n)
    for c in native['cases']:
        for n in ('grammar','events','responses'):
            a=c[n];p=DOC/a['name']
            if digest(p)!=a['sha256'] or p.stat().st_size!=a['bytes'] or len(gzip.decompress(p.read_bytes()))!=a['uncompressed_bytes']:raise ValueError('native artifact '+n)
    if canonical(project(data,audit,native,other))+b'\n'!=(DOC/'compact-contexts-reader-001.json').read_bytes():raise ValueError('exact projection')
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_compact_contexts.py','-v'],capture_output=True,text=True,check=True);print(tests.stderr,flush=True)
    node=subprocess.run([NODE,str(HERE/'test_compact_reader.cjs')],capture_output=True,text=True,check=True);reader=json.loads(node.stdout)
    names=('compact_contexts.py','compact_context_cases.py','run_compact_contexts.py','check_compact_contexts.py','audit_compact_contexts.py',
        'test_compact_contexts.py','run_context_wang.py','audit_context_wang.py','export_compact_contexts.py','test_compact_reader.cjs','validate_compact_contexts.py')
    docs=('compact-contexts.html','compact-contexts.js','compact-contexts-reader-001.json')
    out=dict(version='compact-contexts-validation-001',status='passed',tests=4,reader=reader,exact_projection=True,
        sources={n:digest(HERE/n) for n in names},documents={n:digest(DOC/n) for n in docs},seconds=time.perf_counter()-began)
    (DOC/'compact-contexts-validation-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
