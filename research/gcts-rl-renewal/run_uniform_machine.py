"""Uniform literal interpreter and supplied-trajectory Wang component controls.

No new policy is trained. Components are authored controls, including byte
equality of serialized terms without syntax/signature checking. The complete
first-order checker has not yet been ported to this instruction language.
"""
import hashlib,itertools,json,pathlib,resource,time
from datetime import datetime,timezone
import wang,lazy_wang,proof_search
from stack_program import encode,run,equality_program
from uniform_stack_machine import UniformMachine
from uniform_examples import words,operation_cases,serialized_terms,source_controls
from audit_uniform_machine import source_reference,source_checkpoints

HERE=pathlib.Path(__file__).parent
OUTPUT=HERE.parents[1]/'docs/research/gcts-rl-renewal/uniform-machine-001.json'

def case(machine,name,p,left,right,capacities,tm_limit=5000000,vm_limit=10000):
    before=machine.fingerprint(); result=machine.run(p,left,right,capacities,limit=tm_limit)
    reference=run(p,left,right,capacities=capacities,limit=vm_limit)
    observed=[{k:v for k,v in b.items() if k!='tm_step'} for b in result['boundaries']]
    if observed!=reference['trace'][:len(observed)]: raise AssertionError('VM checkpoint mismatch '+name)
    if result['status'] not in ('unknown_step_budget','unknown_space_bound','unknown_tape_bound') and result['status']!=reference['status']: raise AssertionError('terminal mismatch')
    if machine.fingerprint()!=before: raise AssertionError('interpreter mutated')
    return dict(name=name,code=encode(p),left=left,right=right,capacities=capacities,tm_limit=tm_limit,vm_limit=vm_limit,
                reference_status=reference['status'],reference_instructions=reference['steps'],result=result)

def raw_run(machine,row,limit=10000):
    for step in range(limit+1):
        heads=[s for s in row if isinstance(s,tuple)]
        q=heads[0][1]
        if q in ('accept','reject','space-bound'): return ('unknown_space_bound' if q=='space-bound' else q),step
        if step==limit: return 'unknown_step_budget',step
        try: row=wang.direct_step(machine.compiler,row)
        except (KeyError,ValueError): return 'reject',step

def main():
    started=time.perf_counter(); t=time.perf_counter(); machine=UniformMachine(); build=time.perf_counter()-t
    sources=('stack_program.py','uniform_stack_machine.py','uniform_examples.py','run_uniform_machine.py',
             'wang.py','lazy_wang.py','proof_search.py','rewrite_machine.py','audit_uniform_machine.py')
    u=lazy_wang.Universe(machine.compiler)
    data=dict(date=datetime.now(timezone.utc).isoformat(),sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in sources},
              machine=machine.declaration(),machine_sha256=machine.fingerprint(),build_seconds=build,inventory_count=u.inventory_count,
              scope='fixed input-independent two-stack interpreter and general finite-TM data translation; component controls, not a compiled first-order checker or new learned search',
              configuration=dict(literal_steps=5000000,vm_steps=10000,wang_nodes=20000,wang_seconds=4),
              equality_cases=[],operation_cases=[],serialized_components=[],source_controls=[],raw_syntax_controls=[],wang_runs=[])
    for left,right in itertools.product(words(3),repeat=2):
        name='equal-'+''.join(map(str,left))+'-'+''.join(map(str,right))
        item=case(machine,name,equality_program(),left,right,(3,3))
        if item['result']['status']!=('accept' if left==right else 'reject'): raise AssertionError('binary equality failed')
        data['equality_cases'].append(item)
    print('equality',len(data['equality_cases']),'complete controls',flush=True)
    for name,p,left,right,capacities,limit in operation_cases():
        data['operation_cases'].append(case(machine,name,p,left,right,capacities,tm_limit=limit))
    for name,text,left,right in serialized_terms():
        item=case(machine,name,equality_program(),left,right,(len(left),len(right)))
        item.update(serialized_left_term=text,component='byte equality only; no AST validation, declared-signature checking or inference')
        data['serialized_components'].append(item)
        print('serialized',name,len(left),'bits',item['result']['status'],item['result']['steps'],flush=True)
    for name,source,translation,left,right in source_controls():
        t=time.perf_counter(); reference=run(translation['program'],left,right); source_result=source_reference(source)
        if source_checkpoints(translation,reference['trace'])!=source_result['trace'] or reference['status']!=source_result['status']:
            raise AssertionError('source TM correspondence failed')
        item=case(machine,name,translation['program'],left,right,(max(32,len(left))+16,max(32,len(right))+16))
        item.update(source=source,translation=translation,source_result=source_result,correspondence_seconds=time.perf_counter()-t)
        data['source_controls'].append(item)
        print('source',name,len(translation['program']),'instructions',len(item['code']),'program bytes',item['result']['status'],item['result']['steps'],flush=True)
    # Raw grammar checks include unused records; executed invalid addresses
    # are a separate operational rejection, while unused dangling ones are legal.
    p=(('accept',),); good=machine.initial(p,(0,),capacities=(2,0)); offset=4+len(encode(p))
    hole=list(good); hole[offset:offset+2]=['P','1']
    empty=machine.initial(p,capacities=(0,0))
    raw=[('padding-hole',tuple(hole)),('unused-invalid-opcode',empty[:5]+('0',';')+empty[5:]),
         ('unused-malformed-pop',empty[:5]+tuple('f;')+empty[5:]),
         ('unused-malformed-halt',empty[:5]+tuple('Hp;')+empty[5:]),
         ('missing-stack-delimiter',tuple('P' if s=='|' else s for s in empty))]
    for name,row in raw:
        status,steps=raw_run(machine,row)
        if status!='reject': raise AssertionError('raw grammar accepted bad input')
        data['raw_syntax_controls'].append(dict(name=name,initial=row,status=status,steps=steps,tm_limit=10000))
    # Known operation traces supply only a comparison preference. Unknown
    # bottom bits are selected by the complete point search in each lane.
    problems=[('ignored-bit',( ('accept',),),(),(1,),(0,1),True),
              ('checked-bit',( ('popR',2,2,1),('accept',),('reject',)),(),(1,),(0,1),True),
              ('push-pop',( ('pushR1',1),('popR',3,3,2),('accept',),('reject',)),(),(),(0,1),False)]
    lanes=[('base',False,False),('analytic-neighbor',True,False),('supplied-trace',False,True)]
    for index,(name,p,left,right,capacities,unknown) in enumerate(problems):
        trajectory=machine.run(p,left,right,capacities,keep_rows=True)
        if trajectory['status']!='accept': raise AssertionError('authored operation control did not accept')
        pattern=[(s,) for s in trajectory['initial']]
        if unknown:
            position=4+len(encode(p))+capacities[0]+1
            pattern[position]=('0','1')
        preferred=lazy_wang.preferred_from_rows(machine.compiler,trajectory['rows'])
        rotated=lanes[index:]+lanes[:index]
        for lane,extended,supplied in rotated:
            result=lazy_wang.search(machine.compiler,pattern,trajectory['steps'],machine.accepting_row(trajectory['width']),
                                    node_limit=20000,seconds=4,extended=extended,preferred=preferred if supplied else None)
            packed=proof_search.pack(result)
            packed.update(problem=name,lane=lane,pattern=pattern,top=machine.accepting_row(trajectory['width']),
                          program=encode(p),capacities=capacities,left=left,right=right,unknown_input_bits=int(unknown),supplied_trajectory=supplied,
                          scope='component accepting rectangle; supplied trace is an authored control, not learned discovery')
            data['wang_runs'].append(packed)
            print('Wang',name,lane,result['status'],result['nodes'],round(result['seconds'],3),flush=True)
    data.update(total_seconds=time.perf_counter()-started,peak_process_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                conformance='unchanged complete symbolic Wang engine; all centers root generation zero; global dead/forced precedence; exact trail rollback; full base alternatives behind supplied preferences',
                limitations=['full serialized first-order checker not ported; syntax, schemas and proof blocks remain host-level',
                             'unary addresses make program storage quadratic and instruction lookup expensive',
                             'finite capacities and step budgets are unknown; accepting finite rectangles are not plane-tiling proofs',
                             'general source-TM correspondence is an analytic construction with finite executable controls, not a formalized compiler theorem',
                             'no new GCTS failure markings or RL policy in this component batch'])
    OUTPUT.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('main seconds',round(data['total_seconds'],3),'peak MiB',round(data['peak_process_memory_bytes']/1048576,2),flush=True)

if __name__=='__main__': main()
