"""Exact audited projection, browser mutation checks and both primitive kernels."""
import hashlib
import json
import subprocess
import time
from pathlib import Path
from receptor_attention_artifact import load
from export_receptor_attention import project
from serialized_kernel import canonical,check,problem_hash
from audit_serialized_kernel import replay
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();path=DOC/'receptor-attention-001.json';data=load(path);audit=json.loads((DOC/'receptor-attention-audit-001.json').read_text())
    assert audit['status']=='passed' and audit['input_sha256']==sha(path) and audit['source_sha256']==sha(HERE/'audit_receptor_attention.py')
    for name,pin in {**data['sources'],**data['recovery_sources'],**audit['helpers']}.items():assert sha(HERE/name)==pin,name
    reader=json.loads((DOC/'receptor-attention-reader-001.json').read_text());assert canonical(reader)==canonical(project(data,audit))
    frozen=(DOC/'quantifier-families.js').read_text().split('function Qvalidate(data)')[0]
    assert (DOC/'receptor-attention.js').read_text().startswith(frozen),'original browser proof/point core'
    prefix=(HERE/'run_receptor_attention.py').read_text().split('    def lane(spec,name):')[0]
    assert (HERE/'train_receptor_attention.py').read_text().startswith(prefix),'exact training-only producer prefix'
    subprocess.run(['python3',str(HERE/'test_receptor_attention.py')],check=True)
    tests=subprocess.run([NODE,str(HERE/'test_receptor_attention_reader.cjs')],capture_output=True,text=True,check=True)
    count=0
    for c in reader['donors']+[dict(c,result=r) for c in reader['cases'] for r in c['runs'].values()]:
        r=c['result']
        if r['proof'] is not None:
            req=r['compact']['request'];payload=canonical(req);pin=problem_hash(req)
            assert check(payload,max_work=None,expected_problem_sha256=pin)['status']=='accepted'
            assert replay(payload,pin)['status']=='accepted';count+=1
    files=('receptor_attention.py','receptor_attention_search.py','receptor_attention_cases.py','run_receptor_attention.py','train_receptor_attention.py','resume_receptor_attention.py','receptor_attention_worker.py',
        'receptor_attention_artifact.py','check_receptor_attention.py','audit_receptor_attention.py','export_receptor_attention.py','test_receptor_attention.py','test_receptor_attention_reader.cjs','validate_receptor_attention.py')
    out=dict(version='receptor-attention-validation-001',status='passed',exact_projection=True,tests=5,primitive_certificates_including_duplicates=count,
        reader=json.loads(tests.stdout),sources={n:sha(HERE/n) for n in files},frozen_browser_core_sha256=hashlib.sha256(frozen.encode()).hexdigest(),
        documents={n:sha(DOC/n) for n in ('receptor-attention.html','receptor-attention.js','receptor-attention-reader-001.json')},seconds=time.perf_counter()-began)
    (DOC/'receptor-attention-validation-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
