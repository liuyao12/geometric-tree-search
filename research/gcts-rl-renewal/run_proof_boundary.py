"""Whole-checker free-certificate input experiment, including induction."""
import gzip,hashlib,json,resource,subprocess,time
from pathlib import Path
from proof_boundary import BoundaryLowering,boundary_program,boundary_words,value_word,decoded_heap
from tape_tree_machine import physical_declaration,sha
from tape_binary import write_machine,write_micro,write_input,write_micro_input,read_output,read_micro_output
from tree_machine import Heap,encode_json,run
from tree_kernel import canonical,problem_hash,program,check
from serialized_examples import primitive_cases,addition_induction,adversarial_cases

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-proof-boundary')
SOURCES=('proof_boundary.py','boundary_syntax.tree','run_proof_boundary.py','tape_tree_machine.py','tape_binary.py',
         'tape_runner.cpp','audit_tape_micro.cpp','tree_machine.py','fol_checker.tree','serialized_examples.py')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def execute(exe,code,inp,out,limit):
    start=time.perf_counter();r=json.loads(subprocess.check_output([str(exe),str(code),str(inp),str(out),str(limit)]));r['wall_seconds']=time.perf_counter()-start;return r

def malformed(w):
    return [('empty-certificate',';'),('one-tree',value_word([])+';'),('three-trees',value_word([])*3+';'),
        ('stack-underflow','1;'),('fixed-stack-consumption','1'+value_word([])*3+';'),
        ('atom-above-nil','0'+'1'*9+';'),('truncated-atom','000;'),
        ('missing-terminator',w[:-1]),('early-terminator',';'+w),('trailing-data',w+'0'),
        ('unknown-value-tag',value_word([])+'0'+'111000000'+'0100000000'+'1;')]

def main():
    started=time.perf_counter();TMP.mkdir(exist_ok=True)
    compile_start=time.perf_counter()
    for source,exe in (('tape_runner.cpp','literal'),('audit_tape_micro.cpp','selected')):
        subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(TMP/exe)],check=True)
    compile_seconds=time.perf_counter()-compile_start
    before=time.perf_counter();p=boundary_program();lower=BoundaryLowering(p);micro=lower.declaration();literal=physical_declaration(micro)
    lowering_seconds=time.perf_counter()-before
    write_machine(literal,micro,TMP/'literal.bin');write_micro(micro,TMP/'micro.bin')
    (DOCS/'proof-boundary-microcode-001.json.gz').write_bytes(gzip.compress(json.dumps(micro,separators=(',',':')).encode(),mtime=0))
    (DOCS/'proof-boundary-machine-001.bin.gz').write_bytes(gzip.compress((TMP/'literal.bin').read_bytes(),mtime=0))
    data=dict(program=p,program_sha256=sha(p),sources={n:digest(HERE/n) for n in SOURCES},compile_seconds=compile_seconds,lowering_seconds=lowering_seconds,
        artifacts={n:dict(sha256=digest(DOCS/n),bytes=(DOCS/n).stat().st_size) for n in ('proof-boundary-microcode-001.json.gz','proof-boundary-machine-001.bin.gz')},
        machine=dict(micro_states=len(micro['rows']),literal_states=len(literal['rows']),alphabet=len(literal['alphabet']),tapes=micro['tapes'],
            literal_bytes=(TMP/'literal.bin').stat().st_size,literal_binary_sha256=digest(TMP/'literal.bin'),micro_sha256=sha(micro),literal_sha256=sha(literal)),
        boundary=micro['boundary'],cases=[],controls=[],
        grammar='postfix tagged byte trees; exact byte-string names, duplicate object keys forbidden; no JSON text parsing or node identifiers on the free boundary',
        conformance='proof-system adaptation only; all original tiling graph, generations, rollback, markings and RL engines unchanged; no Wang search added',
        scope='complete semantic checker plus tagged-tree syntax and finite input constructor; accepting Wang/hierarchical certificates, useful proof search, compiler equivalence and logical soundness formalization remain open')
    original=program()
    cases=primitive_cases()[:8]+[('addition-induction',addition_induction())]+[(n,r) for n,r in adversarial_cases() if n in ('missing-induction-authorization','wrong-final-target','captured-instantiation','generalization-of-open-premise')]
    for name,request in cases:
        request=json.loads(canonical(request));fixed,free=boundary_words(request);initial=lower.initial_boundary(fixed,free)
        h=Heap(p['nodes']);root=encode_json(h,request);reference=run(p,h,root)
        old=check(canonical(request),original,expected_problem_sha256=problem_hash(request))
        if old['status']!=reference['status']:raise ValueError('whole-checker reference disagreement')
        write_micro_input(initial,TMP/'micro-input.bin')
        selected=execute(TMP/'selected',TMP/'micro.bin',TMP/'micro-input.bin',TMP/'micro-output.bin',10**12)
        end=read_micro_output(TMP/'micro-output.bin')
        if selected['status']!=reference['status']:raise ValueError(name+' selected disagreement')
        native=None
        if name in ('addition-induction','reflexivity','captured-instantiation'):
            write_input(literal,initial,TMP/'input.bin');native=execute(TMP/'literal',TMP/'literal.bin',TMP/'input.bin',TMP/'output.bin',10**16)
            other=read_output(literal,initial,TMP/'output.bin')
            for k in ('status','micro_steps','physical_steps','micro_fnv64'):
                if native[k]!=selected[k]:raise ValueError(name+' literal disagreement '+k)
            for k in ('heads','words'):
                if other[k]!=end[k]:raise ValueError(name+' tape output disagreement')
        data['cases'].append(dict(name=name,request=request,problem_pin=problem_hash(request),fixed_word=fixed,free_word=free,initial=initial,
            reference=reference,old_reference=old,selected=selected,native=native,output=end,output_sha256=digest(TMP/'micro-output.bin')))
        (TMP/'progress.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
        print(name,selected['status'],selected['micro_steps'],selected['wall_seconds'],native and native['wall_seconds'],flush=True)
    example=next(r for r in data['cases'] if r['name']=='reflexivity')
    for name,free in malformed(example['free_word']):
        initial=lower.initial_boundary(example['fixed_word'],free);write_micro_input(initial,TMP/'micro-input.bin')
        result=execute(TMP/'selected',TMP/'micro.bin',TMP/'micro-input.bin',TMP/'micro-output.bin',10**10)
        if result['status']!='rejected':raise ValueError(name+' malformed input did not reject')
        data['controls'].append(dict(name=name,initial=initial,result=result,output_sha256=digest(TMP/'micro-output.bin')))
        print(name,result['status'],flush=True)
    # Same proof, a different fixed target: the certificate cannot modify it.
    changed=dict(example['request'],target=['bot']);fixed,_=boundary_words(changed)
    initial=lower.initial_boundary(fixed,example['free_word']);write_micro_input(initial,TMP/'micro-input.bin')
    result=execute(TMP/'selected',TMP/'micro.bin',TMP/'micro-input.bin',TMP/'micro-output.bin',10**10)
    if result['status']!='rejected':raise ValueError('changed fixed target accepted')
    data['controls'].append(dict(name='different-fixed-target',initial=initial,result=result,output_sha256=digest(TMP/'micro-output.bin')))
    initial=lower.initial_boundary(example['fixed_word'],example['free_word'],heap_padding=2)
    write_micro_input(initial,TMP/'micro-input.bin');result=execute(TMP/'selected',TMP/'micro.bin',TMP/'micro-input.bin',TMP/'micro-output.bin',10**10)
    if result['status']!='unknown_space_budget':raise ValueError('constructor resource limit not unknown')
    data['controls'].append(dict(name='constructor-heap-bound',initial=initial,result=result,output_sha256=digest(TMP/'micro-output.bin')))
    write_micro_input(example['initial'],TMP/'micro-input.bin')
    for limit in (0,1,10000):
        result=execute(TMP/'selected',TMP/'micro.bin',TMP/'micro-input.bin',TMP/'micro-output.bin',limit)
        if result['status']!='unknown_step_budget':raise ValueError('constructor cutoff not unknown')
        data['controls'].append(dict(name='constructor-step-'+str(limit),initial=example['initial'],limit=limit,result=result,output_sha256=digest(TMP/'micro-output.bin')))
    data.update(total_seconds=time.perf_counter()-started,peak_process_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        reused_artifacts={n:digest(DOCS/n) for n in ('tree-kernel-001.json','tape-kernel-001.json')})
    prior=Path('/private/tmp/gcts-r25-preliminary.json')
    if prior.exists():data['preliminary_attempt']=json.loads(prior.read_text())
    (DOCS/'proof-boundary-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('complete',data['total_seconds'],flush=True)
if __name__=='__main__':main()
