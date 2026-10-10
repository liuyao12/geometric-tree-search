"""Bind the compact gate reader to the full audit and both primitive kernels."""
import gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
from export_proposal_gate import project
from serialized_kernel import canonical,check,problem_hash
from audit_serialized_kernel import replay
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE=shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();raw=DOC/'proposal-gate-001.json.gz';data=json.loads(gzip.decompress(raw.read_bytes()));audit=json.loads((DOC/'proposal-gate-audit-001.json').read_bytes())
    assert audit['status']=='passed' and audit['input_sha256']==sha(raw) and audit['source_sha256']==sha(HERE/'audit_proposal_gate.py')
    for n,p in {**data['sources'],**audit['helpers']}.items():assert sha(HERE/n)==p,n
    reader=json.loads((DOC/'proposal-gate-reader-001.json').read_bytes());assert canonical(reader)==canonical(project(data,audit))
    assert (DOC/'proposal-gate.js').read_text().startswith((DOC/'quantifier-families.js').read_text().split('function Qvalidate(data)')[0])
    tested=subprocess.run(['python3',str(HERE/'test_proposal_gate.py')],check=True,capture_output=True,text=True)
    print(tested.stderr,flush=True)
    result=subprocess.run([NODE,str(HERE/'test_proposal_gate_reader.cjs')],check=True,capture_output=True,text=True)
    kernels=0
    for c in reader['donors']+[dict(c,result=r) for c in reader['cases'] for r in c['runs'].values()]:
        r=c['result']
        if r['proof'] is not None:
            request=r['compact']['request'];payload=canonical(request);pin=problem_hash(request)
            assert check(payload,max_work=None,expected_problem_sha256=pin)['status']=='accepted'
            assert replay(payload,pin)['status']=='accepted';kernels+=1
    names=('proposal_gate.py','proposal_gate_cases.py','proposal_gate_search.py','run_proposal_gate.py','check_proposal_gate.py','test_proposal_gate.py','audit_proposal_gate.py','export_proposal_gate.py','test_proposal_gate_reader.cjs','validate_proposal_gate.py')
    out=dict(version='proposal-gate-validation-001',status='passed',exact_projection=True,tests=5,primitive_certificates=kernels,reader=json.loads(result.stdout),sources={n:sha(HERE/n) for n in names},
        helpers={n:sha(HERE/n) for n in ('export_resumable_clusters.py','check_proposal_gate.py','serialized_kernel.py','audit_serialized_kernel.py')},
        frozen_browser_core_sha256=sha(DOC/'quantifier-families.js'),documents={n:sha(DOC/n) for n in ('proposal-gate.html','proposal-gate.js','proposal-gate-reader-001.json')},seconds=time.perf_counter()-began)
    (DOC/'proposal-gate-validation-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
