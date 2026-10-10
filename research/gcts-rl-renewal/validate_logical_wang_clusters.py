"""Projection binding and focused native/reader regression checks."""
import gzip,json,hashlib,subprocess,time
from pathlib import Path
from export_logical_wang_clusters import build
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    start=time.perf_counter()
    reader=json.loads((DOCS/'logical-wang-clusters-reader-001.json').read_text())
    if reader!=json.loads(json.dumps(build())):raise ValueError('reader differs from complete audited projection')
    result=subprocess.run(['python3','-m','unittest','discover','-s',str(HERE),'-p','test_logical_wang_clusters.py','-v'],capture_output=True,text=True,check=True)
    print(result.stderr.strip(),flush=True)
    tests=json.loads(subprocess.check_output([NODE,str(HERE/'test_logical_cluster_reader.cjs')]))
    sources=('run_logical_wang_clusters.py','audit_logical_wang_clusters.py','micro_line_builder.cpp','micro_line_check.cpp',
        'export_logical_wang_clusters.py','test_logical_wang_clusters.py','test_logical_cluster_reader.cjs','validate_logical_wang_clusters.py')
    result=dict(version='logical-wang-clusters-validation-001',status='passed',sources={n:digest(HERE/n) for n in sources},
        documents={n:digest(DOCS/n) for n in ('logical-wang-clusters.html','logical-wang-clusters.js','logical-wang-clusters-reader-001.json')},
        native_tests=3,reader=tests,exact_projection=True,seconds=time.perf_counter()-start,
        browser={'status':'pending'},scope='Finite observed-cluster regressions, all displayed line/tile projection bindings and reader mutations; no new proof-search or formal universal compiler claim.')
    (DOCS/'logical-wang-clusters-validation-001.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps(dict(status=result['status'],native_tests=3,reader=tests,seconds=result['seconds'])),flush=True)
if __name__=='__main__':main()
