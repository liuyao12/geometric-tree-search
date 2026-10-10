"""New full-suite ledger without rewriting historical test evidence."""
import hashlib,json,re,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOCS=ROOT/'docs/research/gcts-rl-renewal'
def main():
    sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('test*.py'))};start=time.perf_counter()
    r=subprocess.run(['python3','-m','unittest','discover','-s',str(HERE),'-p','test*.py'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    log=r.stdout.decode();print(log,flush=True);count=re.search(r'Ran (\d+) tests in ([0-9.]+)s',log)
    if r.returncode or count is None or not log.rstrip().endswith('OK'):raise ValueError('full research suite failed')
    if any(hashlib.sha256((HERE/n).read_bytes()).hexdigest()!=pin for n,pin in sources.items()):raise ValueError('test sources changed during suite')
    data=dict(passed=int(count[1]),seconds=time.perf_counter()-start,unittest_seconds=float(count[2]),sources=sources,log=log,log_sha256=hashlib.sha256(r.stdout).hexdigest(),runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Full research suite, including fresh motif provenance, complete recipient relational joins, transfer of fixed-hypothesis inference families, all tiny solution sets, extended-mark graph differential and rollback, primitive fallback, both complete/open representations and adversarial graph/AC/witness mutations. The kernel rejects generalization under an open assumption. Historical ledgers remain unchanged.')
    (DOCS/'induction-cluster-tests-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
if __name__=='__main__':main()
