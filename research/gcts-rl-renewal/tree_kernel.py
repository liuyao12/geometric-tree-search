"""Pinned complete semantic checker on the explicit tree instruction machine.

Native JSON parsing/byte bounds/problem hashing are declared adapters. Every
signature, syntax, free-variable, substitution, inference and block decision
runs in the fixed compiled program. Literal tape/Wang lowering is still open.
"""
import hashlib,json,time
from pathlib import Path
from tree_machine import Compiler,Heap,Resource,encode_json,run,fingerprint,validate

SOURCE=Path(__file__).with_name('fol_checker.tree')
def canonical(value):return json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii')
def problem_hash(value):return hashlib.sha256(canonical({k:value[k] for k in ('protocol','theory','target')})).hexdigest()
def program():
    code=Compiler(SOURCE.read_text()).declaration();validate(code);return code

def parse(payload,max_bytes):
    if type(payload) is not bytes:raise ValueError('serialized bytes required')
    if max_bytes is not None and len(payload)>max_bytes:raise Resource('byte bound')
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError('duplicate JSON key')
            out[k]=v
        return out
    def forbidden(_):raise ValueError('floating and nonfinite numbers forbidden')
    return json.loads(payload.decode('utf-8'),object_pairs_hook=pairs,parse_float=forbidden,parse_constant=forbidden)

def check(payload,code,expected_problem_sha256=None,max_bytes=10000000,steps=20000000,heap_limit=2000000,keep_input=False,expected_program_sha256=None):
    started=time.perf_counter();out={'certificate_sha256':hashlib.sha256(payload).hexdigest() if type(payload) is bytes else None,
        'program_sha256':fingerprint(code),'problem_sha256':None}
    try:
        if expected_program_sha256 is not None and out['program_sha256']!=expected_program_sha256:raise ValueError('externally pinned program changed')
        validate(code)
        raw=parse(payload,max_bytes);bound=problem_hash(raw);out['problem_sha256']=bound
        if expected_problem_sha256 is not None and bound!=expected_problem_sha256:raise ValueError('externally pinned theory/target changed')
        heap=Heap(code['nodes'],limit=heap_limit);node=encode_json(heap,raw)
        if keep_input:out['initial']={'node':node,'nodes':list(heap.nodes)}
        r=run(code,heap,node,limit=steps);out.update(result=r,status=r['status'])
    except (Resource,MemoryError,RecursionError) as exc:out.update(status='unknown_resource_budget',reason=str(exc) or type(exc).__name__)
    except (ValueError,TypeError,KeyError,IndexError,UnicodeError) as exc:out.update(status='rejected',reason=str(exc))
    out.update(seconds=time.perf_counter()-started,certificate_bytes=len(payload) if type(payload) is bytes else None)
    return out
