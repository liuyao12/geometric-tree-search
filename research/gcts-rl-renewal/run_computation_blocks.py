"""Reused fixed-table computation proofs, exact block boundaries, paired checks.

Adaptive compression control after the r18 dense-size gate. These are authored
computations, not RL proof discovery or a changed candidate search engine.
"""
import hashlib,json,pathlib,resource,time
from datetime import datetime,timezone
from computation_blocks import certify,check,digest
from flat_computation import from_dag,verify
from audit_binary_machine import literal,freeze
import proof_search

HERE=pathlib.Path(__file__).parent
OUTPUT=HERE.parents[1]/'docs/research/gcts-rl-renewal/computation-blocks-001.json'
REUSE=OUTPUT.with_name('binary-machine-001.json')


def main():
    started=time.perf_counter();reuse_bytes=REUSE.read_bytes();old=json.loads(reuse_bytes);d=old['machine'];cases=[]
    def record(name,row,limit,**metadata):
        proof=certify(d,row,limit);checked=check(d,proof,proof['problem_sha256'])
        if checked['result']!=proof['status']:raise AssertionError('block certificate')
        cases.append(dict(name=name,proof=proof,checking=checked,**metadata));return proof
    for i,c in enumerate(old['cases']):
        proof=record(c['name'],c['result']['initial'],c['tm_limit'],case_index=i)
        for k in ('steps','status','final'):
            if freeze(proof[k])!=freeze(c['result'][k]):raise AssertionError('reused component '+k)
    source_indices=[i for i,c in enumerate(old['comparisons']) if c['lane']=='relative+next' and c['replica']==0]
    for i in source_indices:
        c=old['comparisons'][i];record(c['name'],c['result']['initial'],c['tm_limit'],source_index=i)
    seen=set()
    for i,c in enumerate(old['wang_runs']):
        if c.get('verified') and c['problem'] not in seen:
            seen.add(c['problem']);rows,_=proof_search.unpack(c);record('point-'+c['problem'],rows[0],len(rows)-1,point_index=i)
    addition=next(c['proof'] for c in cases if c['name']=='unary-addition');row=addition['initial']
    for limit in (0,100,5000):record('addition-prefix-'+str(limit),row,limit,prefix_control=True)
    benchmark=[]
    for c in [c for c in cases if 'source_index' in c]:
        proof=c['proof'];pin=proof['problem_sha256'];dag=json.dumps(proof,separators=(',',':'));flat=json.dumps(from_dag(proof),separators=(',',':'));direct=json.dumps({k:proof[k] for k in ('initial','final','steps','limit','status','machine_sha256','problem_sha256')},separators=(',',':'))
        lanes=('literal','flat-sweeps','block-dag')
        for replica in range(3):
            for lane in lanes[replica:]+lanes[:replica]:
                t=time.perf_counter();payload=json.loads({'literal':direct,'flat-sweeps':flat,'block-dag':dag}[lane])
                if lane=='block-dag':result=check(d,payload,pin)
                elif lane=='flat-sweeps':result=verify(d,payload,pin)
                else:
                    if digest(d)!=payload['machine_sha256'] or digest({k:payload[k] for k in ('machine_sha256','initial','steps','limit','final','status')})!=pin:raise AssertionError('literal binding')
                    result=literal(d,payload['initial'],payload['limit'])
                    for k in ('status','steps','final'):
                        if freeze(result[k])!=freeze(payload[k]):raise AssertionError('literal output')
                elapsed=time.perf_counter()-t
                benchmark.append(dict(problem=c['name'],lane=lane,replica=replica,seconds=elapsed,bytes=len({'literal':direct,'flat-sweeps':flat,'block-dag':dag}[lane].encode()),status=proof['status'],steps=proof['steps']))
                print('check',c['name'],lane,replica,round(elapsed,6),flush=True)
    source_names=('computation_blocks.py','flat_computation.py','audit_computation_blocks.py','run_computation_blocks.py','audit_binary_machine.py','audit_uniform_machine.py','wang.py','lazy_wang.py','proof_search.py')
    data=dict(date=datetime.now(timezone.utc).isoformat(),machine_sha256=digest(d),reused_artifact=dict(path=REUSE.name,sha256=hashlib.sha256(reuse_bytes).hexdigest()),sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in source_names},cases=cases,benchmark=benchmark,configuration=dict(literal_limit=20000000,dag_node_limit=1000000,dag_interface_cell_limit=100000000,flat_token_limit=1000000,replicas=3),scope='specialized computation-response certificate calculus; unchanged fixed interpreter and Wang rule; every block and headless frame checked; no search/marking/RL change',limitations=['all inputs and source computations explicitly reused from r18','sweep laws are exact table consequences, not learned markings','block input masks are disjunctive symbolic preconditions; concrete instantiated boundaries still have exact point equality values','literal table/host block checker lack a machine-checked correctness theorem','finite prefix checks are not accepting proofs; resource exhaustion remains unknown','full logical checker not ported; practical learned tiling and proof search remain open'],total_seconds=time.perf_counter()-started,peak_process_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    OUTPUT.write_text(json.dumps(data,separators=(',',':'))+'\n');print('main',round(data['total_seconds'],3),'seconds',round(data['peak_process_memory_bytes']/1048576,2),'MiB','cases',len(cases),'bytes',OUTPUT.stat().st_size,flush=True)

if __name__=='__main__':main()
