"""Bind the complete reader projection, frozen bootstrap and regressions."""
import copy,gzip,hashlib,json,subprocess,time
from pathlib import Path
from export_propositional_wang import build
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name):return json.loads(gzip.decompress((DOC/name).read_bytes()))
def main():
    began=time.perf_counter();view=json.loads((DOC/'propositional-wang-reader-001.json').read_text())
    if view!=json.loads(json.dumps(build())):raise ValueError('reader differs from complete audited projection')
    data=load('propositional-wang-001.json.gz');audit=load('propositional-wang-audit-001.json.gz')
    expected={'fresh-hierarchy','primitive-identity','compound-family','arithmetic-syntax-family','geometry-syntax-family','invalid-unused-definition','wrong-fixed-target'}
    if len(audit['cases'])!=7 or {r['name'] for r in audit['cases']}!=expected:raise ValueError('independent case registry')
    old=json.loads((DOC/'proof-boundary-001.json').read_text());micro=load('proof-boundary-microcode-001.json.gz')
    for row in data['cases']+data['controls']:
        initial=copy.deepcopy(row['initial'])
        for band in (micro['boundary']['problem'],micro['boundary']['certificate']):
            if initial['capacities'][band]!=len(initial['words'][band])+2:raise ValueError('encoded boundary frame')
            initial['capacities'][band]=old['cases'][0]['initial']['capacities'][band]
            initial['words'][band]=old['cases'][0]['initial']['words'][band]
        if initial!=old['cases'][0]['initial']:raise ValueError('frozen bootstrap changed')
    r=subprocess.run(['python3','-m','unittest','discover','-s',str(HERE),'-p','test_propositional_wang_compiler.py','-v'],capture_output=True,text=True,check=True)
    print(r.stderr.strip(),flush=True)
    reader=json.loads(subprocess.check_output([NODE,str(HERE/'test_propositional_wang_reader.cjs')]))
    sources=('propositional_wang_compiler.py','run_propositional_wang.py','audit_propositional_wang.py','export_propositional_wang.py','validate_propositional_wang.py','test_propositional_wang_compiler.py','test_propositional_wang_reader.cjs')
    out=dict(version='propositional-wang-validation-001',status='passed',sources={n:digest(HERE/n) for n in sources},
        documents={n:digest(DOC/n) for n in ('propositional-wang.html','propositional-wang.js','propositional-wang-reader-001.json')},
        producer_sha256=digest(DOC/'propositional-wang-001.json.gz'),audit_sha256=digest(DOC/'propositional-wang-audit-001.json.gz'),
        compiler_tests=9,reader=reader,exact_projection=True,frozen_bootstrap=True,seconds=time.perf_counter()-began,
        browser=dict(status='pending'),scope='Complete audited projection, actual tile seams and context mutations; no universal soundness or direct literal-tile search claim.')
    (DOC/'propositional-wang-validation-001.json').write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps(reader),flush=True)
if __name__=='__main__':main()
