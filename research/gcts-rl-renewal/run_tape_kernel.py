"""Record the full checker on literal one-tape transitions with copy sweeps."""
import gzip,hashlib,json,resource,subprocess,time
from pathlib import Path
from tree_kernel import program,check,canonical,problem_hash
from serialized_examples import primitive_cases,addition_induction,adversarial_cases
from tape_tree_machine import Lowering,physical_declaration,sha
from tape_binary import write_machine,write_input,read_output,write_micro,write_micro_input,read_micro_output

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal';TMP=Path('/private/tmp/gcts-tape-kernel')
SOURCES=('tape_tree_machine.py','tape_binary.py','tape_runner.cpp','audit_tape_micro.cpp','run_tape_kernel.py',
         'tree_machine.py','tree_kernel.py','fol_checker.tree','serialized_examples.py','logic.py')
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def compile_runner(source,destination):
    subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),str('-o'),str(destination)],check=True)
def execute(executable,code,input_path,output_path,limit):
    start=time.perf_counter();r=json.loads(subprocess.check_output([str(executable),str(code),str(input_path),str(output_path),str(limit)]))
    r['wall_seconds']=time.perf_counter()-start;return r
def main():
    started=time.perf_counter();TMP.mkdir(exist_ok=True);compile_start=time.perf_counter()
    compile_runner('tape_runner.cpp',TMP/'literal');compile_runner('audit_tape_micro.cpp',TMP/'independent')
    native_compile=time.perf_counter()-compile_start;source=program();before=time.perf_counter();lower=Lowering(source);micro=lower.declaration();literal=physical_declaration(micro)
    lower_seconds=time.perf_counter()-before
    write_machine(literal,micro,TMP/'literal.bin');write_micro(micro,TMP/'micro.bin')
    micro_bytes=json.dumps(micro,separators=(',',':')).encode()
    (DOCS/'tape-microcode-001.json.gz').write_bytes(gzip.compress(micro_bytes,mtime=0))
    (DOCS/'tape-machine-001.bin.gz').write_bytes(gzip.compress((TMP/'literal.bin').read_bytes(),mtime=0))
    data=dict(program_sha256=sha(source),micro_sha256=sha(micro),literal_sha256=sha(literal),
        sources={n:digest(HERE/n) for n in SOURCES},native_compile_seconds=native_compile,lowering_seconds=lower_seconds,
        machine=dict(micro_states=len(micro['rows']),literal_states=len(literal['rows']),alphabet=len(literal['alphabet']),
            physical_registers=lower.registers,logical_registers=max(f['registers'] for f in source['functions']),tapes=lower.tapes,
            micro_binary_sha256=digest(TMP/'micro.bin'),literal_binary_sha256=digest(TMP/'literal.bin'),
            literal_binary_bytes=(TMP/'literal.bin').stat().st_size,entries=literal['entries']),
        artifacts={n:dict(sha256=digest(DOCS/n),bytes=(DOCS/n).stat().st_size) for n in ('tape-microcode-001.json.gz','tape-machine-001.bin.gz')},
        cases=[],controls=[],method='literal finite one-tape table; exact occurrence-index acceleration only for unchanged-symbol self loops',
        scope='complete checker grammar compiled; finite validation cases; native JSON/pin adapters remain; Wang free-certificate boundary and formal universal compiler equivalence remain open')
    cases=primitive_cases()[:8]+[('addition-induction',addition_induction())]+[
        (n,d) for n,d in adversarial_cases() if n in ('missing-induction-authorization','wrong-final-target','captured-instantiation','generalization-of-open-premise')]
    for name,request in cases:
        payload=canonical(request);pin=problem_hash(request);reference=check(payload,source,expected_problem_sha256=pin,keep_input=True)
        initial=lower.initial(reference['initial'],heap_padding=65536,stack_capacity=32768)
        write_input(literal,initial,TMP/'input.bin');write_micro_input(initial,TMP/'micro-input.bin')
        native=execute(TMP/'literal',TMP/'literal.bin',TMP/'input.bin',TMP/'output.bin',10**16)
        independent=execute(TMP/'independent',TMP/'micro.bin',TMP/'micro-input.bin',TMP/'micro-output.bin',10**11)
        end=read_output(literal,initial,TMP/'output.bin');other=read_micro_output(TMP/'micro-output.bin')
        for key in ('status','physical_steps','micro_steps','micro_fnv64'):
            if native[key]!=independent[key]:raise ValueError(name+' replay mismatch '+key)
        for key in ('heads','words'):
            if end[key]!=other[key]:raise ValueError(name+' tape output mismatch '+key)
        if native['status']!=reference['status']:raise ValueError(name+' logical mismatch')
        data['cases'].append(dict(name=name,payload_hex=payload.hex(),problem_pin=pin,tree_initial=reference.pop('initial'),reference=reference,
            initial=initial,native=native,independent=independent,output=end,independent_output_sha256=digest(TMP/'micro-output.bin'),
            literal_output_sha256=digest(TMP/'output.bin'),input_sha256=digest(TMP/'input.bin'),micro_input_sha256=digest(TMP/'micro-input.bin')))
        print(name,native['status'],native['micro_steps'],native['physical_steps'],native['wall_seconds'],independent['wall_seconds'],flush=True)
        (TMP/'progress.json').write_text(json.dumps({'completed':len(data['cases']),'last':name,'seconds':time.perf_counter()-started}))
    first=data['cases'][0]
    write_input(literal,first['initial'],TMP/'input.bin')
    for limit in (0,1,10000):
        r=execute(TMP/'literal',TMP/'literal.bin',TMP/'input.bin',TMP/'limited-output.bin',limit)
        if r['status']!='unknown_step_budget':raise ValueError('literal resource is unknown')
        data['controls'].append(dict(name='literal-limit-'+str(limit),limit=limit,result=r))
    addition=next(r for r in data['cases'] if r['name']=='addition-induction')
    limited=lower.initial(addition['tree_initial'],heap_padding=4096,stack_capacity=32768)
    write_input(literal,limited,TMP/'input.bin');write_micro_input(limited,TMP/'micro-input.bin')
    native=execute(TMP/'literal',TMP/'literal.bin',TMP/'input.bin',TMP/'output.bin',10**16)
    other=execute(TMP/'independent',TMP/'micro.bin',TMP/'micro-input.bin',TMP/'micro-output.bin',10**11)
    for k in ('status','physical_steps','micro_steps','micro_fnv64'):
        if native[k]!=other[k]:raise ValueError('space control replay '+k)
    if native['status']!='unknown_space_budget':raise ValueError('valid bounded proof must remain unknown')
    data['space_control']=dict(initial=limited,problem_pin=addition['problem_pin'],native=native,independent=other,
        output=read_output(literal,limited,TMP/'output.bin'),independent_output_sha256=digest(TMP/'micro-output.bin'))
    data.update(total_seconds=time.perf_counter()-started,peak_process_memory_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        bindings={'runtime_inputs':'strict native syntax adapter; initial heaps and fixed program pins independently checked',
                  'checksum':'FNV is a diagnostic microevent checksum, not cryptographic proof; independent execution and table laws carry verification',
                  'conformance':'no tiling legality, scheduler, graph, marking or policy changes; resource limits are unknown'},
        reused_tree_artifact=dict(name='tree-kernel-001.json',sha256=digest(DOCS/'tree-kernel-001.json')))
    (DOCS/'tape-kernel-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print(json.dumps({'cases':len(data['cases']),'machine':{k:v for k,v in data['machine'].items() if k!='entries'},'seconds':data['total_seconds']},indent=2),flush=True)
if __name__=='__main__':main()
