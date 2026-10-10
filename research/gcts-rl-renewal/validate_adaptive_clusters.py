"""Validate frozen sources, exact projection, differential tests and reader."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from export_adaptive_clusters import project
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DOC=ROOT/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    began=time.perf_counter()
    raw=DOC/'adaptive-clusters-001.json';data=json.loads(raw.read_bytes())
    audit=json.loads((DOC/'adaptive-clusters-audit-001.json').read_bytes())
    if audit['input_sha256']!=digest(raw) or audit['source_sha256']!=digest(HERE/'audit_adaptive_clusters.py') or audit['checker_sha256']!=digest(HERE/'check_adaptive_clusters.py'):
        raise ValueError('exact independent audit and source pins')
    for n,pin in data['sources'].items():
        if digest(HERE/n)!=pin:raise ValueError('frozen measured source '+n)
    if canonical(project(data,audit))+b'\n'!=(DOC/'adaptive-clusters-reader-001.json').read_bytes():
        raise ValueError('exact reproducible reader projection')
    p=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_adaptive_clusters.py','-v'],capture_output=True,text=True,check=True)
    print(p.stderr,flush=True)
    r=subprocess.run([NODE,str(HERE/'test_adaptive_reader.cjs')],capture_output=True,text=True,check=True)
    reader=json.loads(r.stdout)
    names=('adaptive_receptor_clusters.py','run_adaptive_clusters.py','check_adaptive_clusters.py',
           'audit_adaptive_clusters.py','test_adaptive_clusters.py','export_adaptive_clusters.py',
           'test_adaptive_reader.cjs','validate_adaptive_clusters.py')
    docs=('adaptive-clusters.html','adaptive-clusters.js','adaptive-clusters-reader-001.json')
    value=dict(version='adaptive-clusters-validation-001',status='passed',tests=5,reader=reader,
               exact_projection=True,sources={n:digest(HERE/n) for n in names},
               documents={n:digest(DOC/n) for n in docs},seconds=time.perf_counter()-began)
    (DOC/'adaptive-clusters-validation-001.json').write_bytes(canonical(value)+b'\n')
    print(json.dumps(value),flush=True)


if __name__=='__main__':main()
