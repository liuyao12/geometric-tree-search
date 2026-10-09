"""Compile the complete fixed checker and record explicit operational runs."""
import hashlib,json,resource,time
from pathlib import Path
from tree_kernel import program,check,canonical,problem_hash
from tree_machine import fingerprint
from serialized_kernel import check as reference
from serialized_examples import primitive_cases,propositional_cases,adversarial_cases,addition_induction,flatten_blocks
from tree_examples import extra_cases

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
SOURCES=('tree_machine.py','tree_kernel.py','fol_checker.tree','tree_examples.py','run_tree_kernel.py',
         'serialized_kernel.py','serialized_examples.py','logic.py')
STEP_LIMIT=20000000;HEAP_LIMIT=2000000

def cases():
    return [(n,d,'primitive') for n,d in primitive_cases()]+[
        ('proposition-'+str(i),d,'propositional-exhaustion') for i,d in enumerate(propositional_cases())]+[
        (n,d,'adversarial') for n,d in adversarial_cases()]+[
        ('induction',addition_induction(),'historical-induction'),('expanded-induction',flatten_blocks(addition_induction()),'historical-induction')]+[
        (n,d,'port-control') for n,d in extra_cases()]

def machine_row(code,name,d,step_limit=STEP_LIMIT,heap_limit=HEAP_LIMIT,group='machine-resource',with_reference=False):
    payload=canonical(d);pin=problem_hash(d)
    got=check(payload,code,expected_problem_sha256=pin,expected_program_sha256=fingerprint(code),steps=step_limit,heap_limit=heap_limit,keep_input=True)
    row=dict(name=name,group=group,payload_hex=payload.hex(),problem_pin=pin,step_limit=step_limit,heap_limit=heap_limit,check=got)
    if with_reference:
        other=reference(payload,expected_problem_sha256=pin,max_work=None)
        row['reference']={k:other[k] for k in ('status','seconds','work') if k in other}
        if other['status']!=got['status']:raise ValueError('semantic mismatch '+name+': '+str(row))
    return row

def main():
    start=time.perf_counter();before=time.perf_counter();code=program();compiled=time.perf_counter()-before;pin=fingerprint(code)
    rows=[]
    for i,(name,d,group) in enumerate(cases()):
        row=machine_row(code,name,d,group=group,with_reference=True);rows.append(row)
        if i%100==0 or group!='propositional-exhaustion':print(i,name,row['check']['status'],row['check'].get('result',{}).get('steps'),flush=True)
    d=addition_induction();full=next(r for r in rows if r['name']=='induction')
    controls=[machine_row(code,'zero-step-bound',d,step_limit=0),machine_row(code,'inside-inference-step-bound',d,step_limit=100000),
              machine_row(code,'heap-allocation-bound',d,heap_limit=len(full['check']['initial']['nodes'])+1)]
    for r in controls:
        if not r['check']['status'].startswith('unknown'):raise ValueError('valid bounded proof must stay unknown')
    simple=canonical(primitive_cases()[0][1]);sp=problem_hash(primitive_cases()[0][1]);adapters=[]
    payloads=[('duplicate-object-key',b'{"protocol":"gcts-fol-1","protocol":"gcts-fol-1"}',None,None,None),
              ('floating-number',b'{"x":0.0}',None,None,None),('nonfinite-number',b'{"x":NaN}',None,None,None),
              ('broken-utf8',b'\xff',None,None,None),('bad-json',b'{',None,None,None),
              ('byte-bound',simple,sp,0,None),('initial-heap-bound',simple,sp,None,0),
              ('external-problem-change',simple,'0'*64,None,None)]
    for name,payload,bound,byte_limit,heap_limit in payloads:
        got=check(payload,code,expected_problem_sha256=bound,max_bytes=byte_limit,heap_limit=heap_limit,expected_program_sha256=pin)
        if got['status']!=('unknown_resource_budget' if name in ('byte-bound','initial-heap-bound') else 'rejected'):raise ValueError('adapter control '+name)
        adapters.append(dict(name=name,payload_hex=payload.hex(),problem_pin=bound,max_bytes=byte_limit,heap_limit=heap_limit,check=got))
    groups={}
    for r in rows:
        group=groups.setdefault(r['group'],dict(cases=0,accepted=0,rejected=0,steps=0,seconds=0.0,reference_seconds=0.0))
        group['cases']+=1;group[r['check']['status']]+=1;group['steps']+=r['check']['result']['steps'];group['seconds']+=r['check']['seconds'];group['reference_seconds']+=r['reference']['seconds']
    data=dict(program=code,program_sha256=pin,compile_seconds=compiled,cases=rows,machine_controls=controls,adapter_controls=adapters,groups=groups,
        sources={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in SOURCES},
        method='fixed full first-order checker compiled to generic byte/cons/register instructions; native syntax and pin adapters; no inference callbacks',
        conformance={'engine_change':'no tiling graph, scheduling, legality, policy or markings changed',
            'unknown':'byte, heap or step limits are explicit unknown results, never impossibility or pruning',
            'clusters':'exact proof-block interfaces remain replayed; no discovered proof blocks, GCTS search or RL training in this port experiment',
            'gap':'generic tree heap and call frames still use native dictionaries/lists; literal tape/Wang lowering and universal equivalence proof remain open'},
        total_seconds=time.perf_counter()-start,peak_process_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (DOCS/'tree-kernel-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print(json.dumps({'program_sha256':pin,'functions':len(code['functions']),'instructions':sum(len(f['code']) for f in code['functions']),
        'groups':groups,'resource_controls':[r['check']['status'] for r in controls],'seconds':data['total_seconds'],
        'peak_process_memory_bytes':data['peak_process_memory_bytes']},indent=2),flush=True)

if __name__=='__main__':main()
