"""Generic native replay of every completed Python checker instruction trace."""
import copy,hashlib,json,resource,time
from pathlib import Path
import tree_native
from tree_kernel import program
from serialized_kernel import canonical,problem_hash
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-proof-block-native')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    started=time.perf_counter();TMP.mkdir(exist_ok=True);path=DOCS/'learned-proof-blocks-001.json';data=json.loads(path.read_text());seconds=tree_native.compile_tool(TMP);code=program();rows=[]
    requests={r['problem']['id']:r['result']['request'] for r in data['discovery']}
    requests.update({r['problem']+'/'+r['lane']:r['result']['request'] for r in data['evaluation']['runs'] if r['result']['status']=='accepted_proposal'})
    for old in data['tree_program_checks']:
        name=old['id'];request=requests[name];r=tree_native.check(canonical(request),code,TMP,problem_hash(request));ref=old['result']['result']
        for k in ('status','steps','event_sha256','peak_frames','heap_nodes','profile','value'):
            if r[k]!=ref[k]:raise ValueError('native/reference differs '+name+' '+k)
        rows.append(dict(id=name,result=r,reference_seconds=old['result']['seconds']));print(name,r['steps'],r['wall_seconds'],flush=True)
    data['native_tree_replay']=dict(cases=rows,compile_seconds=seconds,total_seconds=time.perf_counter()-started,peak_driver_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        sources={n:digest(HERE/n) for n in ('tree_runner.cpp','tree_native.py','run_proof_block_native.py')},
        scope='same fixed generic tree program, all 66 actual input heaps, complete small-step event SHA-256, instruction counts, call profiles, heap sizes and final values; no logical callback or changed proof grammar',
        trust='native input encoder and toolchain; full traces agree with the independent previously completed reference runs')
    path.write_text(json.dumps(data,separators=(',',':'))+'\n');print('complete',data['native_tree_replay']['total_seconds'],flush=True)
if __name__=='__main__':main()
