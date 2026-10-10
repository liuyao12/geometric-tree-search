"""Validate exact reader projection, transport guards and every point mutation."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

from export_transported_markings import build

HERE=Path(__file__).resolve().parent
DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    began=time.perf_counter()
    if json.loads((DOC/'transported-markings-reader-001.json').read_text())!=build():
        raise ValueError('reader is not the exact audited projection')
    result=subprocess.run(['python3','-m','unittest','discover','-s',str(HERE),
                           '-p','test_transported_markings.py','-v'],capture_output=True,text=True,check=True)
    print(result.stderr,flush=True)
    checked=json.loads(subprocess.check_output([NODE,str(HERE/'test_transported_reader.cjs')]))
    names=('transported_markings.py','check_transported_markings.py','run_transported_markings.py',
           'audit_transported_markings.py','test_transported_markings.py','export_transported_markings.py',
           'test_transported_reader.cjs','validate_transported_markings.py')
    docs=('transported-markings.html','transported-markings.js','transported-markings-reader-001.json')
    report=dict(version='transported-markings-validation-001',status='passed',tests=6,
                reader=checked,exact_projection=True,sources={n:digest(HERE/n) for n in names},
                documents={n:digest(DOC/n) for n in docs},seconds=time.perf_counter()-began,
                browser=dict(status='pending'))
    (DOC/'transported-markings-validation-001.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    print(json.dumps(checked),flush=True)


if __name__=='__main__':main()
