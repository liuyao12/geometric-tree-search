"""Bind all projected proofs, source pins, reader checks and primitive kernels."""
import gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
from export_family_router import project
from serialized_kernel import canonical,check,problem_hash
from audit_serialized_kernel import replay
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE=shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();raw=DOC/'family-router-001.json.gz';data=json.loads(gzip.decompress(raw.read_bytes()));audit=json.loads((DOC/'family-router-audit-001.json').read_bytes())
    assert audit['status']=='passed' and audit['input_sha256']==sha(raw) and audit['source_sha256']==sha(HERE/'audit_family_router.py')
    for n,pin in {**data['sources'],**audit['helpers']}.items():assert sha(HERE/n)==pin,n
    reader=json.loads((DOC/'family-router-reader-001.json').read_bytes());assert canonical(reader)==canonical(project(data,audit))
    browser=(DOC/'family-router.js').read_text();old=(DOC/'proposal-gate.js').read_text()
    assert browser.startswith(old.split('const PGfeatures=')[0])
    assert old[old.index('function PGstate'):old.index('function PGevent')] in browser
    tested=subprocess.run(['python3',str(HERE/'test_family_router.py')],check=True,capture_output=True,text=True);print(tested.stderr,flush=True)
    tested=subprocess.run([NODE,str(HERE/'test_family_router_reader.cjs')],check=True,capture_output=True,text=True)
    kernels=0
    records=reader['donors']+[dict(c,result=r) for c in reader['cases']+reader['training']['feedback'] for r in c['runs'].values()]
    for c in records:
        r=c['result']
        if r['proof'] is not None:
            req=r['compact']['request'];payload=canonical(req);pin=problem_hash(req)
            assert check(payload,max_work=None,expected_problem_sha256=pin)['status']=='accepted'
            assert replay(payload,pin)['status']=='accepted';kernels+=1
    names=('family_router.py','family_router_cases.py','run_family_router.py','resume_family_router.py','check_family_router.py','audit_family_router.py','export_family_router.py','test_family_router.py','test_family_router_reader.cjs','validate_family_router.py')
    result=dict(version='family-router-validation-001',status='passed',exact_projection=True,engine_tests=5,primitive_certificates=kernels,reader=json.loads(tested.stdout),sources={n:sha(HERE/n) for n in names},
        helpers={n:sha(HERE/n) for n in ('export_resumable_clusters.py','serialized_kernel.py','audit_serialized_kernel.py')},
        frozen_browser_core_sha256=sha(DOC/'proposal-gate.js'),documents={n:sha(DOC/n) for n in ('family-router.html','family-router.js','family-router-reader-001.json')},seconds=time.perf_counter()-began)
    (DOC/'family-router-validation-001.json').write_bytes(canonical(result)+b'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
