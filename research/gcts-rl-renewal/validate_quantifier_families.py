"""Bind the reader exactly to the audited artifact and both primitive kernels."""
import gzip,hashlib,json,subprocess,time
from pathlib import Path
from export_quantifier_families import project
from serialized_kernel import canonical,check,problem_hash
from audit_serialized_kernel import replay
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    started=time.perf_counter();raw=DOC/'quantifier-families-001.json.gz';data=json.loads(gzip.decompress(raw.read_bytes()));audit=json.loads((DOC/'quantifier-families-audit-001.json').read_bytes())
    assert audit['status']=='passed' and audit['input_sha256']==sha(raw) and audit['source_sha256']==sha(HERE/'audit_quantifier_families.py')
    for n,p in {**data['sources'],**audit['helpers']}.items():assert sha(HERE/n)==p,n
    reader=json.loads((DOC/'quantifier-families-reader-001.json').read_bytes());assert canonical(reader)==canonical(project(data,audit))
    subprocess.run(['python3',str(HERE/'test_quantifier_families.py')],check=True)
    result=subprocess.run([NODE,str(HERE/'test_quantifier_reader.cjs')],check=True,capture_output=True,text=True)
    kernels=0
    for c in reader['donors']+[dict(c,result=r) for c in reader['cases'] for r in c['runs'].values()]:
        r=c['result']
        if r['proof'] is not None:
            request=r['compact']['request'];payload=canonical(request);pin=problem_hash(request)
            assert check(payload,max_work=None,expected_problem_sha256=pin)['status']=='accepted'
            assert replay(payload,pin)['status']=='accepted';kernels+=1
    names=('quantifier_family_patterns.py','quantifier_family_join.py','quantifier_family_search.py','quantifier_family_cases.py','run_quantifier_families.py','check_quantifier_families.py','audit_quantifier_families.py','test_quantifier_families.py','export_quantifier_families.py','test_quantifier_reader.cjs','validate_quantifier_families.py')
    out=dict(version='quantifier-families-validation-001',status='passed',exact_projection=True,tests=5,primitive_certificates=kernels,
        reader=json.loads(result.stdout),sources={n:sha(HERE/n) for n in names},helpers={'export_resumable_clusters.py':sha(HERE/'export_resumable_clusters.py')},
        documents={n:sha(DOC/n) for n in ('quantifier-families.html','quantifier-families.js','quantifier-families-reader-001.json')},seconds=time.perf_counter()-started)
    (DOC/'quantifier-families-validation-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
