"""Bind every displayed line, exact palette row and statistic to audited data."""
import gzip,hashlib,json,subprocess,unittest,time
from pathlib import Path
from audit_serialized_kernel import replay
from shared_wang_inventory import Inventory
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();d=json.loads(gzip.decompress((DOCS/'shared-wang-001.json.gz').read_bytes()));v=json.loads((DOCS/'shared-wang-reader-001.json').read_text())
    i=Inventory(gzip.decompress((DOCS/'proof-boundary-machine-001.bin.gz').read_bytes()))
    for source,shown in zip(d['cases'],v['cases']):
        if source['request']!=shown['request'] or source['patch']!=shown['patch']:raise ValueError('request/actual tile projection')
        ordinary=replay(json.dumps(source['request'],separators=(',',':')).encode('ascii'))
        if ordinary['status']!='accepted' or json.loads(json.dumps(ordinary['proof']))!=shown['primitive']:raise ValueError('every displayed primitive line')
        for k in ('literal','selected','problem_pin','inventory_fingerprint'):
            if source[k]!=shown[k]:raise ValueError('statistic projection '+k)
        for t in shown['patch']['tiles']:
            for symbol in t['triple']:
                h=i.decode(symbol)
                if h is not None:
                    expected={str(s):list(a) for s in range(i.A) if (a:=i.transition(h[0],s)) is not None}
                    if v['transition_rows'][str(h[0])]!=expected:raise ValueError('displayed finite table row')
    suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_shared_wang_inventory.py')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():raise ValueError('inventory tests')
    reader=json.loads(subprocess.check_output([NODE,str(HERE/'test_shared_wang_reader.cjs')]))
    files=('shared-wang.html','shared-wang.js','shared-wang-reader-001.json','shared-wang-001.json.gz','shared-wang-audit-001.json')
    record=dict(status='passed',inventory_tests=result.testsRun,reader=reader,
        exact_projection='Every primitive line, proof request, actual tile, finite delta row and execution statistic matches the audited source.',
        sources={n:sha(HERE/n) for n in ('shared_wang_inventory.py','test_shared_wang_inventory.py','export_shared_wang.py','test_shared_wang_reader.cjs','validate_shared_wang.py')},
        artifacts={n:sha(DOCS/n) for n in files},seconds=time.perf_counter()-began)
    (DOCS/'shared-wang-validation-001.json').write_text(json.dumps(record,separators=(',',':'))+'\n');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
