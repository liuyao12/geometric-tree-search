"""Bind frozen measured sources, separate index replay and exact visual reader."""
import gzip,hashlib,json,subprocess,sys,time
from pathlib import Path
from export_indexed_families import project
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    started=time.perf_counter();data=json.loads(gzip.decompress((DOC/'indexed-families-001.json.gz').read_bytes()));audit=json.loads((DOC/'indexed-families-audit-001.json').read_bytes())
    if audit['status']!='passed' or audit['input_sha256']!=sha(DOC/'indexed-families-001.json.gz') or audit['source_sha256']!=sha(HERE/'audit_indexed_families.py'):raise ValueError('exact audit/source binding')
    for n,pin in {**data['sources'],**audit['helpers']}.items():
        if sha(HERE/n)!=pin:raise ValueError('frozen source '+n)
    if canonical(project(data,audit))+b'\n'!=(DOC/'indexed-families-reader-001.json').read_bytes():raise ValueError('exact projection')
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_indexed_families.py','-v'],capture_output=True,text=True,check=True);print(tests.stderr,flush=True)
    node=subprocess.run([NODE,str(HERE/'test_indexed_reader.cjs')],capture_output=True,text=True,check=True);reader=json.loads(node.stdout)
    sources=('indexed_family_join.py','indexed_family_search.py','indexed_cases.py','run_indexed_families.py','check_indexed_families.py','audit_indexed_families.py','test_indexed_families.py','export_indexed_families.py','test_indexed_reader.cjs','validate_indexed_families.py')
    out=dict(version='indexed-families-validation-001',status='passed',tests=5,reader=reader,exact_projection=True,
        sources={n:sha(HERE/n) for n in sources},helpers={'export_resumable_clusters.py':sha(HERE/'export_resumable_clusters.py')},
        documents={n:sha(DOC/n) for n in ('indexed-families.html','indexed-families.js','indexed-families-reader-001.json')},seconds=time.perf_counter()-started)
    (DOC/'indexed-families-validation-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
