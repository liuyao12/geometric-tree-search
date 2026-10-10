"""Source-bound projection, independent reader mutation checks and invariants."""
import hashlib
import json
import subprocess
import time
from pathlib import Path
from dependency_budget_artifact import load
from export_dependency_budget import project
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    began=time.perf_counter();path=DOC/'dependency-budget-001.json';data=load(path)
    audit=json.loads((DOC/'dependency-budget-audit-001.json').read_text())
    assert audit['status']=='passed' and audit['input_sha256']==sha(path) and audit['source_sha256']==sha(HERE/'audit_dependency_budget.py')
    for name,pin in {**data['sources'],**audit['helpers']}.items():assert sha(HERE/name)==pin,name
    expected=canonical(project(data,audit));reader=json.loads((DOC/'dependency-budget-reader-001.json').read_text());assert canonical(reader)==expected
    prefix=(DOC/'quantifier-families.js').read_text().split('function Qvalidate(data)')[0]
    assert (DOC/'dependency-budget.js').read_text().startswith(prefix),'frozen original point/source proof core'
    subprocess.run(['python3',str(HERE/'test_dependency_budget.py')],check=True)
    checked=subprocess.run([NODE,str(HERE/'test_dependency_budget_reader.cjs')],capture_output=True,text=True,check=True)
    files=('dependency_budget.py','dependency_budget_search.py','dependency_budget_cases.py','dependency_budget_worker.py',
           'dependency_budget_artifact.py','check_dependency_budget.py','run_dependency_budget.py','audit_dependency_budget.py',
           'export_dependency_budget.py','test_dependency_budget.py','test_dependency_budget_reader.cjs','validate_dependency_budget.py')
    out=dict(version='dependency-budget-validation-001',status='passed',exact_projection=True,engine_tests=5,
             reader=json.loads(checked.stdout),sources={n:sha(HERE/n) for n in files},
             original_browser_core_sha256=hashlib.sha256(prefix.encode()).hexdigest(),
             documents={n:sha(DOC/n) for n in ('dependency-budget.html','dependency-budget.js','dependency-budget-reader-001.json')},
             seconds=time.perf_counter()-began)
    (DOC/'dependency-budget-validation-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)


if __name__=='__main__':main()
