"""Bind the audited full experiment to its readable projection and reader."""
import hashlib,json,subprocess,time
from pathlib import Path
from budget_family_artifact import load
from export_budget_families import project
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    began=time.perf_counter();path=DOC/'budget-families-001.json';data=load(path)
    audit=json.loads((DOC/'budget-families-audit-001.json').read_text())
    assert audit['status']=='passed' and audit['input_sha256']==sha(path) and audit['source_sha256']==sha(HERE/'audit_budget_families.py')
    for n,pin in {**data['sources'],**audit['helpers']}.items():assert sha(HERE/n)==pin,n
    reader=json.loads((DOC/'budget-families-reader-001.json').read_text());assert canonical(reader)==canonical(project(data,audit))
    original=(DOC/'quantifier-families.js').read_text().split('function Qvalidate(data)')[0]
    dependency=(DOC/'dependency-budget.js').read_text().split('function Dpacked')[1].split('async function Dvalidate')[0]
    current=(DOC/'budget-families.js').read_text()
    assert current.startswith(original),'frozen original point/source browser kernel'
    assert ('function Dpacked'+dependency) in current,'frozen independent necessity certificate browser checker'
    subprocess.run(['python3',str(HERE/'test_budget_families.py')],check=True)
    checked=subprocess.run([NODE,str(HERE/'test_budget_family_reader.cjs')],capture_output=True,text=True,check=True)
    names=('budget_family_policy.py','budget_family_search.py','budget_family_join.py','budget_family_cases.py','budget_family_worker.py',
           'run_budget_families.py','check_budget_families.py','budget_family_artifact.py','audit_budget_families.py','export_budget_families.py',
           'test_budget_families.py','test_budget_family_reader.cjs','validate_budget_families.py')
    out=dict(version='budget-families-validation-001',status='passed',exact_projection=True,engine_tests=5,reader=json.loads(checked.stdout),
        sources={n:sha(HERE/n) for n in names},original_browser_core_sha256=hashlib.sha256(original.encode()).hexdigest(),
        frozen_dependency_checker_sha256=hashlib.sha256(('function Dpacked'+dependency).encode()).hexdigest(),
        documents={n:sha(DOC/n) for n in ('budget-families.html','budget-families.js','budget-families-reader-001.json')},seconds=time.perf_counter()-began)
    (DOC/'budget-families-validation-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)

if __name__=='__main__':main()
