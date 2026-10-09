"""One complete research-suite run with source and log provenance."""
import hashlib,json,re,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DOCS=ROOT/'docs/research/gcts-rl-renewal'
def main():
    sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('test*.py'))};began=time.perf_counter()
    r=subprocess.run(['python3','-m','unittest','discover','-s',str(HERE),'-p','test*.py'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    seconds=time.perf_counter()-began;log=r.stdout.decode();Path('/private/tmp/gcts-r28-suite.log').write_text(log);print(log,flush=True)
    count=re.search(r'Ran (\d+) tests in ([0-9.]+)s',log)
    if r.returncode!=0 or count is None or not log.rstrip().endswith('OK'):raise ValueError('full research suite failed')
    data=dict(passed=int(count[1]),seconds=seconds,unittest_seconds=float(count[2]),source_sha256=sources,log_sha256=hashlib.sha256(r.stdout).hexdigest(),log=log,runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='One full suite run after all new theorem, search, normalization and audit changes; prior source files and historical experiments unchanged.')
    (DOCS/'theorem-tests-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    for stem in ('peano-theorems','euclid-theorems','proof-compaction'):
        path=DOCS/(stem+'-001.json');d=json.loads(path.read_text());d['semantic_tests']={k:v for k,v in data.items() if k!='log'};path.write_text(json.dumps(d,separators=(',',':'))+'\n')
    print('full suite',data['passed'],seconds,flush=True)
if __name__=='__main__':main()
