"""Matched authored source computations and compact fixed-machine point controls.

Adaptive engineering study after r17's cutoff; no learned policy or full FOL
port. Three lanes distinguish the historical machine from two data encodings
accepted by the SAME new table. All repeated requests and unknowns are saved.
"""
import hashlib,itertools,json,pathlib,resource,time
from datetime import datetime,timezone
import wang,lazy_wang,proof_search
from stack_program import run,equality_program,encode as unary_encode
from binary_program import encode,workspace
from uniform_stack_machine import UniformMachine
from binary_stack_machine import BinaryMachine
from uniform_examples import words,operation_cases,serialized_terms

HERE=pathlib.Path(__file__).parent
OUTPUT=HERE.parents[1]/'docs/research/gcts-rl-renewal/binary-machine-001.json'
REUSE=OUTPUT.with_name('uniform-machine-001.json')

def case(machine,name,p,left,right,capacities,limit=20000000,next_links=True,work=None):
    compact=isinstance(machine,BinaryMachine);before=machine.fingerprint()
    result=machine.run(p,left,right,capacities,limit=limit,next_links=next_links,workspace_capacity=work) if compact else machine.run(p,left,right,capacities,limit=limit)
    reference=run(p,left,right,capacities=capacities,limit=10000)
    observed=[{k:v for k,v in b.items() if k!='tm_step'} for b in result['boundaries']]
    if observed!=reference['trace'][:len(observed)]:raise AssertionError('instruction checkpoint '+name)
    if not result['status'].startswith('unknown') and result['status']!=reference['status']:raise AssertionError('terminal result '+name)
    if machine.fingerprint()!=before:raise AssertionError('mutable interpreter')
    return dict(name=name,program=p,code=encode(p,next_links) if compact else unary_encode(p),left=left,right=right,capacities=capacities,tm_limit=limit,vm_limit=10000,result=result,reference_status=reference['status'],reference_instructions=reference['steps'])

def raw_run(machine,row,limit=10000):
    for step in range(limit+1):
        q=next(s[1] for s in row if isinstance(s,tuple))
        if q in ('accept','reject','space-bound','workspace-bound'):return {'space-bound':'unknown_space_bound','workspace-bound':'unknown_workspace_bound'}.get(q,q),step
        if step==limit:return 'unknown_step_budget',step
        try:row=wang.direct_step(machine.compiler,row)
        except (KeyError,ValueError):return 'reject',step

def main():
    started=time.perf_counter();t=time.perf_counter();machine=BinaryMachine();binary_build=time.perf_counter()-t;t=time.perf_counter();unary=UniformMachine();unary_build=time.perf_counter()-t
    previous=json.loads(REUSE.read_text());assert unary.fingerprint()==previous['machine_sha256']
    source_names=('binary_program.py','binary_stack_machine.py','run_binary_machine.py','audit_binary_machine.py','uniform_examples.py','stack_program.py','uniform_stack_machine.py','audit_uniform_machine.py','wang.py','lazy_wang.py','proof_search.py','rewrite_machine.py')
    u=lazy_wang.Universe(machine.compiler)
    data=dict(date=datetime.now(timezone.utc).isoformat(),machine=machine.declaration(),machine_sha256=machine.fingerprint(),unary_machine=unary.declaration(),unary_machine_sha256=unary.fingerprint(),inventory_count=u.inventory_count,build_seconds=dict(compact=binary_build,unary=unary_build),sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in source_names},reused_artifact=dict(path=REUSE.name,sha256=hashlib.sha256(REUSE.read_bytes()).hexdigest()),configuration=dict(literal_steps=20000000,vm_steps=10000,replicas=3,wang_nodes=20000,wang_seconds=4),cases=[],comparisons=[],raw_syntax_controls=[],wang_runs=[],scope='adaptive authored compact-program controls; same instruction semantics, two fixed interpreters; no learned GCTS/RL or full first-order checker port')
    for left,right in itertools.product(words(3),repeat=2):
        item=case(machine,'equal-'+''.join(map(str,left))+'-'+''.join(map(str,right)),equality_program(),left,right,(3,3))
        assert item['result']['status']==('accept' if left==right else 'reject');item['group']='short-word-equality';data['cases'].append(item)
    for next_links in (False,True):
        for name,p,l,r,c,limit in operation_cases():
            item=case(machine,name,p,l,r,c,limit,next_links);item.update(group='operation',next_links=next_links);data['cases'].append(item)
        for name,text,l,r in serialized_terms():
            item=case(machine,name,equality_program(),l,r,(len(l),len(r)),next_links=next_links);item.update(group='byte-equality',serialized_left_term=text,next_links=next_links);data['cases'].append(item)
    for next_links,work in ((False,0),(False,1),(True,0),(True,1)):
        item=case(machine,'workspace-next-link',(('pushL1',1),('accept',)),(),(),(1,0),next_links=next_links,work=work);item.update(group='workspace',next_links=next_links);data['cases'].append(item)
    print('component runs',len(data['cases']),flush=True)
    lanes=('unary','relative-binary','relative+next')
    for problem_index,old in enumerate(previous['source_controls']):
        p=tuple(tuple(i) for i in old['translation']['program']);l=tuple(old['left']);r=tuple(old['right']);c=tuple(old['capacities'])
        for replica in range(3):
            rotation=(problem_index+replica)%3
            for lane in lanes[rotation:]+lanes[:rotation]:
                item=case(unary if lane=='unary' else machine,old['name'],p,l,r,c,next_links=lane=='relative+next')
                item.update(lane=lane,replica=replica,source=old['source'],translation=old['translation'],source_result=old['source_result']);data['comparisons'].append(item)
                print('source',old['name'],replica,lane,len(item['code']),item['result']['status'],item['result']['steps'],round(item['result']['seconds'],3),flush=True)
    empty=machine.initial((('accept',),),capacities=(0,0));position=empty.index('A')
    def raw(code):return empty[:3]+tuple(code)+empty[position:]
    probes=[('empty-operand',raw('g;')),('leading-zero',raw('g>01;')),('negative-zero',raw('g<0;')),('missing-direction',raw('g1;')),('bad-next-suffix',raw('gn0;')),('unused-bad-record',raw('H;g>01;')),('unused-negative-target',raw('H;g<1111;'))]
    bad_work=list(machine.initial((('accept',),),capacities=(0,0),workspace_capacity=1));bad_work[bad_work.index('A')+1]='0';probes.append(('nonempty-initial-workspace',tuple(bad_work)))
    hole=list(machine.initial((('accept',),),left=(0,),capacities=(2,0)));start=hole.index('#')+1;hole[start:start+2]=['P','1'];probes.append(('padding-hole',tuple(hole)))
    for name,row in probes:
        status,steps=raw_run(machine,row);assert status==('accept' if name=='unused-negative-target' else 'reject'),name
        data['raw_syntax_controls'].append(dict(name=name,initial=row,status=status,steps=steps,tm_limit=10000))
    problems=[('ignored-bit',( ('accept',),),(),(1,),(0,1),True),('checked-bit',( ('popR',2,2,1),('accept',),('reject',)),(),(1,),(0,1),True),('push-pop',( ('pushR1',1),('popR',3,3,2),('accept',),('reject',)),(),(),(0,1),False)]
    wang_lanes=[('base',False,False),('analytic-neighbor',True,False),('supplied-trace',False,True)]
    for index,(name,p,l,r,c,unknown) in enumerate(problems):
        trajectory=machine.run(p,l,r,c,keep_rows=True);assert trajectory['status']=='accept';pattern=[(s,) for s in trajectory['initial']]
        if unknown:pattern[6+len(encode(p))+workspace(p)+c[0]]=('0','1')
        preferred=lazy_wang.preferred_from_rows(machine.compiler,trajectory['rows'])
        for lane,extended,supplied in wang_lanes[index:]+wang_lanes[:index]:
            result=lazy_wang.search(machine.compiler,pattern,trajectory['steps'],machine.accepting_row(trajectory['width']),node_limit=20000,seconds=4,extended=extended,preferred=preferred if supplied else None)
            packed=proof_search.pack(result);packed.update(problem=name,lane=lane,pattern=pattern,top=machine.accepting_row(trajectory['width']),program=encode(p),left=l,right=r,capacities=c,workspace_capacity=workspace(p),unknown_input_bits=int(unknown),supplied_trajectory=supplied,scope='authored compact computation component, not learned proof discovery');data['wang_runs'].append(packed)
            print('Wang',name,lane,result['status'],result['nodes'],round(result['seconds'],3),flush=True)
    data.update(total_seconds=time.perf_counter()-started,peak_process_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,conformance='unchanged complete symbolic Wang point engine; all centers root generation zero; global dead/forced checks; exact rollback and full base alternatives',limitations=['adaptive study uses the same five authored source controls as r17','unary versus compact comparison changes operand encoding, scratch algorithm and marker scans; not an address-only causal ablation','relative versus relative+next uses the same table and differs only in data encoding','unknown limits are not rejection certificates; no complete-time ratio against a cutoff','entire serialized first-order checker not ported; byte equality is not inference','no new learned policy, marking, mathematical proof discovery or plane construction'])
    OUTPUT.write_text(json.dumps(data,separators=(',',':'))+'\n');print('main seconds',round(data['total_seconds'],3),'peak MiB',round(data['peak_process_memory_bytes']/1048576,2),flush=True)

if __name__=='__main__':main()
