"""Transport to a generic native interpreter of unchanged tree bytecode.

Native JSON/input-heap adapter and toolchain are trusted, as in tree_kernel.
No formula, proof or induction callback occurs in the executor. Every small-step
trace has the same canonical event SHA-256 as the original interpreter.
"""
import hashlib,json,struct,subprocess,time
from pathlib import Path
from tree_machine import Heap,encode_json,validate,fingerprint,Resource
from tree_kernel import parse,problem_hash
HERE=Path(__file__).resolve().parent
OPS=('const','move','cons','head','tail','pair','atom','succ','not','branch','jump','call','return')
def compile_tool(directory):
    before=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17','-Wno-deprecated-declarations',str(HERE/'tree_runner.cpp'),'-o',str(directory/'tree')],check=True);return time.perf_counter()-before
def code_bytes(code):
    validate(code);values=[0x47545231,len(code['constants']),*code['constants'],len(code['functions'])]
    for f in code['functions']:
        values.extend((f['arity'],f['registers'],len(f['code'])))
        for row in f['code']:
            op,*args=row
            if op=='call':args=[args[0],args[1],len(args[2]),*args[2]]
            values.extend((OPS.index(op),len(args),*args))
    return struct.pack('<'+'I'*len(values),*values)
def input_bytes(code,request,heap_limit=None):
    heap=Heap(code['nodes'],limit=heap_limit);root=encode_json(heap,request);values=[0x47544931,root,len(heap.nodes)]
    for a,b in heap.nodes:values.extend((a,b))
    return struct.pack('<'+'I'*len(values),*values)
def check(payload,code,directory,expected_problem_sha256,steps=1000000000,heap_limit=2000000):
    before=time.perf_counter();raw=parse(payload,10000000)
    if problem_hash(raw)!=expected_problem_sha256:raise ValueError('externally fixed theory/target changed')
    directory=Path(directory);(directory/'tree-code.bin').write_bytes(code_bytes(code))
    try:encoded=input_bytes(code,raw,heap_limit)
    except (Resource,RecursionError,MemoryError) as exc:return dict(status='unknown_resource_budget',reason=str(exc),wall_seconds=time.perf_counter()-before,program_sha256=fingerprint(code))
    (directory/'tree-input.bin').write_bytes(encoded)
    r=json.loads(subprocess.check_output([str(directory/'tree'),str(directory/'tree-code.bin'),str(directory/'tree-input.bin'),str(directory/'tree-output.bin'),str(steps),str(heap_limit),str(directory/'tree-profile.json')]))
    profiles=json.loads((directory/'tree-profile.json').read_text());r['profile']={f['name']:n for f,n in zip(code['functions'],profiles) if n};r.update(wall_seconds=time.perf_counter()-before,program_sha256=fingerprint(code),input_sha256=hashlib.sha256((directory/'tree-input.bin').read_bytes()).hexdigest(),output_sha256=hashlib.sha256((directory/'tree-output.bin').read_bytes()).hexdigest())
    return r
