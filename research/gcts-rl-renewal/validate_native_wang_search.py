"""Bind the independently audited trees, six fixed fixtures and actual reader."""
import gzip,hashlib,json,struct,subprocess,time
from pathlib import Path
from export_native_wang_search import project
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fixtures(data):
    raw=gzip.decompress((DOC/'proof-boundary-machine-001.bin.gz').read_bytes());_,A,Q,start,accept,reject,_=struct.unpack_from('<7I',raw);D=A*(Q+1)
    def guard(w,h,top=None):
        root=[entry for y in range(h) for entry in ([[-1,2*y],[1,1]],[[2*w-1,2*y],[1,1]])]
        if top is not None:root += [[[2*x,2*h-1],v] for x,v in enumerate(top)]
        return root
    want=[]
    for h,w in ((2,5),(3,7)):
        pattern=[[1] for _ in range(w)];pattern[w//2]={'range':[2*A,D]};top=[1]*w;top[w//2]=A+A*accept+9
        want.append(('inverse-accept-'+str(h),pattern,h,guard(w,h,top),True,None))
    # Independently serialize only the fixed bootstrap cells actually used.
    initial=json.loads((DOC/'proof-boundary-001.json').read_text())['cases'][0]['initial'];alphabet=json.loads((DOC/'shared-wang-reader-001.json').read_text())['inventory']['alphabet'];prefix=['L']
    for j in range(len(initial['words'])):
        body=['^']+list(initial['words'][j])+['B']*(initial['capacities'][j]-len(initial['words'][j])-1);head=initial['heads'][j];body[head]='@'+body[head];prefix += ['S'+str(j),*body,'#']
        if len(prefix)>=13:break
    prefix=[alphabet.index(v) for v in prefix[:13]];pattern=[[1],[1],*[[v] for v in prefix],[1],[1]];pattern[2]=[A+A*start+prefix[0]]
    want.append(('boot-prefix',pattern,4,guard(17,4),False,None));top=[p[0] for p in pattern];top[2]=prefix[0];top[3]=A+A*accept+9
    want.append(('premature-accept',pattern,2,guard(17,2,top),True,None));want.append(('undefined-center',[[1],[1],[A+A*reject+1],[1],[1]],1,guard(5,1),False,None));want.append(('zero-budget',want[0][1],2,want[0][3],True,0))
    assert len(data['cases'])==len(want)
    for c,(identity,p,h,b,accepting,limit) in zip(data['cases'],want):
        s=c['spec'];assert (s['id'],s['pattern'],s['height'],s['boundary'],s['accepting'],s.get('attempts'))==(identity,p,h,b,accepting,limit),identity
    return dict(fixtures=6,unknown_head_pool_excludes_accept=True,actual_bootstrap_prefix=True,free_proof_boundary=False)
def main():
    began=time.perf_counter();path=DOC/'native-wang-search-001.json';data=json.loads(path.read_text());audit=json.loads((DOC/'native-wang-search-audit-001.json').read_text())
    assert audit['status']=='passed' and audit['input_sha256']==sha(path) and audit['source_sha256']==sha(HERE/'audit_native_wang_search.py')
    for n,pin in {**data['sources'],**audit['helpers']}.items():assert sha(HERE/n)==pin,n
    for n,pin in data['reused_inputs'].items():assert sha(DOC/n)==pin,n
    fixture_check=fixtures(data);reader=json.loads((DOC/'native-wang-search-reader-001.json').read_text());assert canonical(reader)==canonical(project(data,audit))
    subprocess.run(['python3',str(HERE/'test_native_wang_search.py')],check=True)
    checked=subprocess.run([NODE,str(HERE/'test_native_wang_reader.cjs')],capture_output=True,text=True,check=True)
    names=('native_wang_domains.cpp','native_wang_search.py','native_wang_cases.py','native_wang_worker.py','run_native_wang_search.py','check_native_rectangle.py','check_native_wang.py','audit_native_wang_search.py','test_native_wang_search.py','export_native_wang_search.py','test_native_wang_reader.cjs','validate_native_wang_search.py')
    out=dict(version='native-wang-search-validation-001',status='passed',exact_projection=True,fixture_check=fixture_check,engine_tests=5,reader=json.loads(checked.stdout),sources={n:sha(HERE/n) for n in names},documents={n:sha(DOC/n) for n in ('native-wang-search.html','native-wang-search.js','native-wang-search-reader-001.json')},seconds=time.perf_counter()-began)
    (DOC/'native-wang-search-validation-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
