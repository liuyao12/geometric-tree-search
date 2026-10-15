"""Unexecuted cold Q preparation/controls leaf. ROOT alone activates once.

No theorem search, Graph solve, induction/native/RL or authority issuance.
Raw-buffer Source loading and ordinary endpoint guards are part of20s; all
publication/exit/cleanup remains inside60s/512MiB/caller90 owned scope.
"""
import hashlib
import importlib.util
import inspect
import json
import math
import os
from pathlib import Path
import resource
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
SCHEMA='ROOT-Q-open-empty-Gamma-controls-worker-plan-v1'
SCOPE='Q-complete-preparation-and-finite-controls-no-search-no-admission'
COMMAND='ROOT-Q-open-empty-Gamma-preparation-controls'
AUTHOR='/root/arithmetic_induction'
LIMITS=dict(whole_seconds=60,peak_bytes=536870912,caller_seconds=90,control_seconds=20)
MAX_METADATA=64*1048576
FROZEN_SOURCES = {'kernel': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py', 'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9', 'bytes': 10323}, 'catalogue': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_catalog_v1.py', 'sha256': '2db11af0d7206afd4e1c10b53b97c16f98064c14fd1e57a9a2ca34c0a602348a', 'bytes': 10187}, 'point_graph': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py', 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567', 'bytes': 28531}, 'payload': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/q_preparation_owned_graph_v3.py', 'sha256': 'ee2088bf60709f6c0c5a78297841bd0684674369fa9d3c08119b96a59caa88ad', 'bytes': 5435}, 'controls': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/arithmetic_Q_streamed_controls_v3.py', 'sha256': '4e28fadd9c76ba6664e485fa2c5aa97beaa08639986b6d56aae50395b006e638', 'bytes': 19742}, 'master': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/docs/basic-tiling-algorithm.md', 'sha256': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9', 'bytes': 21657}}
SOURCE_ROLES=set(FROZEN_SOURCES)|{'worker'}
FROZEN_INPUTS = {'declaration': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/Q-declaration-v1.json', 'sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc', 'bytes': 2683}, 'prototype_contract': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/source-contract-v1.json', 'sha256': '78df35e4f72ce6cc46e70459d0e366d646a404305311d481c3d0671db5e2a870', 'bytes': 8367}, 'prototype_source_review': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-independent-20261014/source-findings-v1.json', 'sha256': 'c37a2f1c3f8fafdc3f35b41ecaa758352195e9cdf524443fce0ee34e1fd2bd4d', 'bytes': 11414}, 'control_specification': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/controls-specification-v4.json', 'sha256': 'f3cc208b518c7ddae480172bc6416e02b754a1a2e9ca7370f36f5e40cef97a79', 'bytes': 4886}}
INPUT_ROLES=set(FROZEN_INPUTS)
PROTOTYPE_SOURCE_PINS = {'catalogue': {'bytes': 10187, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_catalog_v1.py', 'sha256': '2db11af0d7206afd4e1c10b53b97c16f98064c14fd1e57a9a2ca34c0a602348a'}, 'kernel': {'bytes': 10323, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py', 'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'}, 'payload': {'bytes': 5219, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/q_preparation_gate_v1.py', 'sha256': '7712d2760570a0cd75d88de8099b492c99e8f824f2185c46322fb8fe33028a4a'}, 'point_graph': {'bytes': 28531, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py', 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'}}

def need(value, label):
    if not value:
        raise ValueError(label)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)

def pin(path):
    path = Path(path)
    need(path.is_absolute() and str(path.resolve()) == str(path) and not path.is_symlink(), 'canonical ABS pin')
    h = hashlib.sha256(); count = 0; before = path.stat()
    with path.open('rb') as stream:
        for raw in iter(lambda: stream.read(65536), b''):
            h.update(raw); count += len(raw)
    after = path.stat()
    need((before.st_dev,before.st_ino,before.st_mtime_ns,before.st_size) ==
         (after.st_dev,after.st_ino,after.st_mtime_ns,after.st_size), 'whole stable raw bytes')
    return dict(path=str(path), sha256=h.hexdigest(), bytes=count)

def verify(record):
    need(type(record) is dict and set(record) == {'path','sha256','bytes'}
         and type(record['bytes']) is int and record['bytes'] >= 0
         and type(record['sha256']) is str and len(record['sha256']) == 64
         and all(c in '0123456789abcdef' for c in record['sha256'])
         and pin(record['path']) == record, 'typed canonical full pin')
    return record

def parse(raw):
    def unique(pairs):
        result = {}
        for name, value in pairs:
            need(name not in result, 'duplicate JSON field'); result[name] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda token: (_ for _ in ()).throw(ValueError('nonfinite JSON '+token)))

def read(record, maximum=MAX_METADATA):
    verify(record)
    with Path(record['path']).open('rb') as stream:
        raw = stream.read(maximum+1)
        need(len(raw) <= maximum and stream.read(1) == b'', 'whole bounded raw buffer, no prefix')
    need(len(raw) == record['bytes'] and hashlib.sha256(raw).hexdigest() == record['sha256'],
         'parse the authenticated same raw buffer')
    value = parse(raw); verify(record); return value

def load(record, name):
    verify(record); raw = Path(record['path']).read_bytes()
    need(len(raw) == record['bytes'] and hashlib.sha256(raw).hexdigest() == record['sha256'],
         'same exact raw source execution buffer')
    spec = importlib.util.spec_from_file_location(name, record['path'])
    need(spec is not None, 'source metadata spec')
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    exec(compile(raw, record['path'], 'exec'), module.__dict__)
    need(str(Path(module.__file__).resolve()) == record['path'], 'bound raw source origin, no bytecode loader')
    return module

def normalize(record):
    path = Path(record['path']); actual = path if path.is_absolute() else ROOT/path
    return dict(record, path=str(actual))

def value_state(value):
    """Detect ordinary namespace/default mutation without accepting origin claims."""
    if value is None or type(value) in (str, int, bool, float, list, dict, tuple):
        try: return canonical(value)
        except (TypeError, ValueError): pass
    return None

def executable_state(module, *, class_roots=()):
    state = []; namespaces = []; mros = []; seen_classes = set()
    def keys(owner):
        return tuple(k for k in vars(owner) if not k.startswith('__') and k != '_NEXT_CAPSULE')
    def add(owner, name, value):
        if isinstance(value, (staticmethod, classmethod)): value = value.__func__
        code = value.__code__ if inspect.isfunction(value) else None
        defaults = (value_state(value.__defaults__), value_state(value.__kwdefaults__)) if code else None
        closure = tuple((cell.cell_contents, value_state(cell.cell_contents))
                        for cell in (value.__closure__ or ())) if code else None
        state.append((owner, name, value, code, defaults, closure, value_state(value)))
        if isinstance(value, property):
            # The descriptor object can stay unchanged while its getter code mutates.
            for accessor in ('fget', 'fset', 'fdel'):
                add(value, accessor, getattr(value, accessor))
    def record_class(value):
        # Generated methods may dispatch through super() or a captured base_type.
        # Preserve every actual MRO class/method, not just that class object's ID.
        for parent in value.__mro__:
            if parent is object or parent in seen_classes: continue
            seen_classes.add(parent); mros.append((parent, parent.__mro__))
            namespaces.append((parent, keys(parent)))
            for field, child in vars(parent).items():
                if field not in ('__dict__', '__weakref__'): add(parent, field, child)
    namespaces.append((module, keys(module)))
    for name, value in vars(module).items():
        if name.startswith('__') or name == '_NEXT_CAPSULE': continue
        add(module, name, value)
        if isinstance(value, type) and value.__module__ == module.__name__:
            record_class(value)
    for value in class_roots:
        need(isinstance(value, type), 'actual generated endpoint class')
        record_class(value)
    return namespaces, state, mros

def unchanged_executable(state):
    namespaces, records, mros = state
    for owner, original_mro in mros:
        need(owner.__mro__ == original_mro and all(a is b for a, b in zip(owner.__mro__, original_mro)),
             'compiled generated endpoint inheritance changed')
    for owner, names in namespaces:
        need(tuple(k for k in vars(owner) if not k.startswith('__') and k != '_NEXT_CAPSULE') == names,
             'compiled namespace gained or lost bindings')
    for owner, name, original, code, defaults, closure, data in records:
        actual = getattr(owner, name) if isinstance(owner, property) else vars(owner).get(name)
        if isinstance(actual, (staticmethod, classmethod)): actual = actual.__func__
        need(actual is original, 'compiled namespace/function identity changed')
        if code is not None:
            need(actual.__code__ is code and
                 (value_state(actual.__defaults__), value_state(actual.__kwdefaults__)) == defaults,
                 'compiled executable/defaults changed; co_filename is insufficient')
            current = actual.__closure__ or ()
            need(len(current) == len(closure) and all(cell.cell_contents is old and value_state(cell.cell_contents) == text
                 for cell, (old, text) in zip(current, closure)), 'compiled source closure changed')
        if data is not None: need(value_state(actual) == data, 'compiled source constant changed')

def function_signature(fn):
    return (fn, fn.__code__, tuple(id(v) for v in fn.__defaults__ or ()),
            tuple((k,id(v)) for k,v in sorted((fn.__kwdefaults__ or {}).items())),
            tuple((id(c),id(c.cell_contents)) for c in fn.__closure__ or ()))


def source_cache_guard(sources,modules,anchors):
    expected={p['path']:p for p in sources.values() if p['path'].endswith('.py')}
    seen=[]
    for name,module in list(sys.modules.items()):
        file=getattr(module,'__file__',None)
        if not isinstance(file,str):continue
        path=str(Path(file).resolve())
        if not path.startswith(str(ROOT)+os.sep):continue
        need(path in expected and not path.endswith(('.pyc','.pyo')),'no undeclared local executable/cache module')
        need(name==__name__ or any(module is value for value in modules.values()),'same exact admitted module object')
        verify(expected[path]);seen.append(expected[path])
    need(all(modules[k] is anchors[k] and sys.modules.get(modules[k].__name__) is modules[k] for k in modules),
         'source-bound module object remains its actual namespace')
    return sorted({p['path']:p for p in seen}.values(),key=lambda p:p['path'])


def json_blockable(value):
    # A C-json block is a bounded existing subtree: at most512 scalar/container
    # visits,32768 total string characters and4096 bits per integer. This test
    # retains references only; oversized containers are streamed recursively.
    stack=[value];visits=0;characters=0
    while stack:
        child=stack.pop();visits+=1
        if visits>512:return False
        if type(child) is str:
            characters+=len(child)
            if characters>32768:return False
        elif type(child) is int:
            if child.bit_length()>4096:return False
        elif child is None or type(child) in (bool,float):pass
        elif type(child) is dict:
            if len(child)>512:return False
            for name,item in child.items():
                if type(name) is not str:return False
                stack.append(name);stack.append(item)
                if len(stack)>512:return False
        elif type(child) in (list,tuple):
            if len(child)>512:return False
            stack.extend(child)
            if len(stack)>512:return False
        else:return False
    return True


def json_chunks(value):
    # Full canonical JSON: C blocks only for bounded existing subtrees. No full
    # model/state copy, JSON string or UTF-8 buffer is constructed here.
    if json_blockable(value):
        yield canonical(value)
    elif type(value) is dict:
        yield '{'
        for index,name in enumerate(sorted(value)):
            need(type(name) is str,'literal JSON object keys')
            if index:yield ','
            yield canonical(name)+':'
            yield from json_chunks(value[name])
        yield '}'
    elif type(value) in (list,tuple):
        yield '['
        for start in range(0,len(value),32):
            block=value[start:start+32]
            if start:yield ','
            if json_blockable(block):yield canonical(block)[1:-1]
            else:
                for offset,item in enumerate(block):
                    if offset:yield ','
                    yield from json_chunks(item)
        yield ']'
    else:yield canonical(value)


def preflight(plan_path,owner_path):
    plan_pin,owner_pin=pin(plan_path),pin(owner_path)
    plan,owner=read(plan_pin,2*1048576),read(owner_pin,2*1048576)
    need(set(plan)=={'schema','ROOT_owned_once_only','scope','sources','inputs','runtime','reviews','closure','limits','owner_plan_path','output_directory'}
         and plan['schema']==SCHEMA and plan['ROOT_owned_once_only'] is True and plan['scope']==SCOPE and plan['limits']==LIMITS,
         'strict11-field current Q controls leaf')
    need(set(plan['sources'])==SOURCE_ROLES and {r:p for r,p in plan['sources'].items() if r!='worker'}==FROZEN_SOURCES
         and plan['sources']['worker']==pin(Path(__file__).resolve()) and plan['inputs']==FROZEN_INPUTS,
         'exact current seven raw sources/four fixed inputs')
    need(plan_path.parent==owner_path.parent and plan['owner_plan_path']==str(owner_path),'same flat cold plan namespace')
    output=Path(plan['output_directory'])
    need(output.is_absolute() and output==output.resolve() and output.parent==plan_path.parent and not output.exists(),'exclusive immutable output')
    closure={}
    for record in plan['closure']:
        verify(record);need(record['path'] not in closure,'unique canonical leaf closure');closure[record['path']]=record
    need(list(closure)==sorted(closure),'canonical sorted full raw closure')
    for record in [*plan['sources'].values(),*plan['inputs'].values(),*plan['reviews'].values()]:
        verify(record);need(closure.get(record['path'])==record,'every direct source/input/review is closed')
    need(set(plan['reviews'])=={'ROOT','independent'},'genuine separate actual Source review slots')
    for role in ('ROOT','independent'):
        review=read(plan['reviews'][role])
        need(review.get('source_only') is True and review.get('source_review_passed') is True and review.get('scientific_calls')==0
             and review.get('sources')==plan['sources'],'current exact Source review, never scientific acceptance')
        if role=='independent':need(review.get('author_identity')==AUTHOR and review.get('reviewer_identity')!=AUTHOR,'distinct Q implementation reviewer')
    need(plan['reviews']['ROOT']['path']==str(plan_path.parent/'ROOT-source-review-v1.json'),'generic owner local ROOT Source review')
    runtime=plan['runtime']
    need(set(runtime)=={'binary','resource_extension','python_version','platform'} and runtime['python_version']==[3,9,6]
         and runtime['platform']=='darwin' and list(sys.version_info[:3])==[3,9,6] and sys.platform=='darwin','exact pinned CLT runtime')
    for field in ('binary','resource_extension'):verify(runtime[field]);need(closure.get(runtime[field]['path'])==runtime[field],'runtime closed')
    need(str(Path(sys.executable).resolve())==runtime['binary']['path'] and str(Path(resource.__file__).resolve())==runtime['resource_extension']['path'],
         'actual runtime/resource extension origin')
    argv=[runtime['binary']['path'],'-B',plan['sources']['worker']['path'],COMMAND,str(plan_path),str(owner_path)]
    need(set(owner)=={'schema','stage','runtime_binary','worker','argv','worker_receipt','limits','closure','ROOT_source_review','scope'}
         and owner['schema']=='ROOT-guard-native-owned-plan-v1' and owner['stage']=='preparation' and owner['limits']==LIMITS and owner['scope']==SCOPE
         and owner['argv']==argv and normalize(owner['runtime_binary'])==runtime['binary'] and normalize(owner['ROOT_source_review'])==plan['reviews']['ROOT'],
         'strict10 generic owned preparation plan and literal six argv')
    need((ROOT/owner['worker']).resolve()==Path(plan['sources']['worker']['path'])
         and (ROOT/owner['worker_receipt']).resolve()==output/'Q-controls-result-v1.json','exact worker and final receipt path')
    owner_closure={}
    for record in owner['closure']:
        p=normalize(record);verify(p);need(p['path'] not in owner_closure,'unique canonical owner closure');owner_closure[p['path']]=p
    for record in closure.values():need(owner_closure.get(record['path'])==record,'full worker closure in owned closure')
    need(owner_closure.get(plan_pin['path'])==plan_pin,'owner closes actual worker plan')
    # Read precisely these scientific metadata roots; recursively authenticate
    # their pin values without interpreting arbitrary ancestor JSON as authority.
    def authenticate(value):
        if isinstance(value,dict):
            if set(value)=={'path','sha256','bytes'}:
                p=normalize(value);verify(p);need(closure.get(p['path'])==p,'every named input raw pin in full closure')
            for child in value.values():authenticate(child)
        elif isinstance(value,list):
            for child in value:authenticate(child)
    documents={role:read(record) for role,record in plan['inputs'].items()}
    for document in documents.values():authenticate(document)
    prior=documents['prototype_source_review']
    need(prior['source_only'] is True and prior['source_review_passed'] is True and prior['scientific_calls']==0
         and prior['sources']==PROTOTYPE_SOURCE_PINS,'original Q Source-only prerequisite, not current admission')
    need(documents['declaration']['ordered_Gamma']==[] and documents['control_specification']['grammar_changed'] is False
         and documents['control_specification']['target_changed'] is False,'original empty-Gamma target/grammar preserved')
    return plan,output,plan_pin,owner_pin,closure,owner_closure,documents


def main():
    began=time.perf_counter()
    need(len(sys.argv)==4 and sys.argv[1]==COMMAND,'one literal cold Q controls invocation')
    plan_path,owner_path=(Path(p) for p in sys.argv[2:])
    need(all(p.is_absolute() and p==p.resolve() for p in (plan_path,owner_path)),'canonical actual plans')
    plan,output,plan_pin,owner_pin,closure,owner_closure,documents=preflight(plan_path,owner_path)
    output.mkdir();artifacts=[];final_receipt=None
    def whole_tick():
        need(time.perf_counter()-began<55 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<500*1048576,
             'whole60/512 includes inherited prospective finishing reserves')
    whole_tick_fn=whole_tick;whole_tick_anchor=function_signature(whole_tick_fn)
    streamed_bytes=[0];partial_stream_paths=[];serialization_records=[]
    def write_snapshot(name,chunks):
        need(type(name) is str and Path(name).name==name and name.endswith('.json'),'scoped owned JSON witness name')
        write_began=time.perf_counter()
        path=output/name;partial_stream_paths.append(str(path));count=0;maximum_block=0
        with path.open('xb') as stream:
            for chunk in chunks:
                if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
                    raise ValueError('original own validator changed before local limit delegation')
                if function_signature(whole_tick)!=whole_tick_anchor or function_signature(whole_tick_fn)!=whole_tick_anchor:
                    raise ValueError('original whole_tick function/code/default/closure endpoint changed')
                whole_tick_fn()
                if time.perf_counter()>=deadline:raise TimeoutError('complete output stream exceeded shared20s')
                need(type(chunk) is str,'stream literal JSON text chunks');raw=chunk.encode('utf8')
                need(len(raw)<=4*1048576,'bounded individual JSON block')
                count+=len(raw);streamed_bytes[0]+=len(raw);maximum_block=max(maximum_block,len(raw))
                need(count<=MAX_METADATA and streamed_bytes[0]<=256*1048576,'whole per-file64MiB and aggregate256MiB output ceilings')
                need(stream.write(raw)==len(raw),'entire stream block written')
        record=pin(path);artifacts.append(record);partial_stream_paths.remove(str(path))
        if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
            raise ValueError('original own validator changed before local limit delegation')
        if function_signature(whole_tick)!=whole_tick_anchor or function_signature(whole_tick_fn)!=whole_tick_anchor:
            raise ValueError('original whole_tick function/code/default/closure endpoint changed')
        whole_tick_fn()
        serialization_records.append(dict(file=record,bytes=count,maximum_block_bytes=maximum_block,
            inclusive_source_encoding_write_seconds=time.perf_counter()-write_began,
            scope='Includes generator/domain work; nested in shared20 and whole owned cost, not additive pure serialization time.'))
        return record
    def save(name,value):
        return write_snapshot(name,json_chunks(value))
    own=sys.modules[__name__]
    names=('need','canonical','pin','verify','read','load','normalize','executable_state','unchanged_executable','source_cache_guard','function_signature','json_blockable','json_chunks')
    validators={name:(globals()[name],globals()[name].__code__) for name in names}
    guard_fn,guard_code=unchanged_executable,unchanged_executable.__code__;own_state=executable_state(own)
    modules={};states=[];anchors={};declaration=documents['declaration'];declaration_text=canonical(declaration)
    inner_began=time.perf_counter();deadline=inner_began+LIMITS['control_seconds']
    def inner_tick():
        if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
            raise ValueError('original own validator changed before local limit delegation')
        if function_signature(whole_tick)!=whole_tick_anchor or function_signature(whole_tick_fn)!=whole_tick_anchor:
            raise ValueError('original whole_tick function/code/default/closure endpoint changed')
        whole_tick_fn()
        if time.perf_counter()>=deadline:raise TimeoutError('whole20s Q preparation/controls incomplete; no accepted prefix')
    inner_tick_fn=inner_tick;inner_tick_anchor=function_signature(inner_tick_fn)
    try:
        for role in ('kernel','catalogue','point_graph','payload','controls'):
            if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):raise ValueError('own cold endpoint changed before project load')
            if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
                raise ValueError('original own validator changed before local limit delegation')
            if function_signature(inner_tick)!=inner_tick_anchor or function_signature(inner_tick_fn)!=inner_tick_anchor:
                raise ValueError('original inner_tick function/code/default/closure endpoint changed')
            inner_tick_fn()
            module=load(plan['sources'][role],'_cold_arithmetic_Q_controls_'+role)
            modules[role]=module;states.append(executable_state(module))
            if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):raise ValueError('own cold endpoint changed after project load')
            guard_fn(own_state)
            for state in states:guard_fn(state)
        anchors=dict(modules)
        source_guard=None;source_guard_code=None
        def source_guard():
            if source_guard.__code__ is not source_guard_code or unchanged_executable is not guard_fn or guard_fn.__code__ is not guard_code:
                raise ValueError('original callback/validator code replaced')
            if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):raise ValueError('original cold rejection/validator replaced')
            guard_fn(own_state)
            for state in states:guard_fn(state)
            need(canonical(declaration)==declaration_text,'original declared target/grammar/Gamma unchanged')
            source_cache_guard(plan['sources'],modules,anchors)
            for record in closure.values():verify(record)
            for record in owner_closure.values():verify(record)
            need(pin(plan_path)==plan_pin and pin(owner_path)==owner_pin,'same once-only immutable plans')
            if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
                raise ValueError('original own validator changed before local limit delegation')
            if function_signature(inner_tick)!=inner_tick_anchor or function_signature(inner_tick_fn)!=inner_tick_anchor:
                raise ValueError('original inner_tick function/code/default/closure endpoint changed')
            inner_tick_fn()
        source_guard_code=source_guard.__code__;callback_fn=source_guard;callback_anchor=function_signature(callback_fn)
        def invoke_guard():
            if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):raise ValueError('own validator replaced before callback')
            if function_signature(callback_fn)!=callback_anchor:raise ValueError('original callback code/default/closure identity changed')
            callback_fn()
            if function_signature(callback_fn)!=callback_anchor:raise ValueError('callback changed during delegated call')
        invoke_fn=invoke_guard;invoke_anchor=function_signature(invoke_fn)
        if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
            raise ValueError('original own validator replaced at outer call boundary')
        if function_signature(invoke_guard)!=invoke_anchor:
            raise ValueError('original invoking shim changed at outer call boundary')
        invoke_fn()
        serialization_fixtures=[{},[],{'b':None,'a':[False,True,0,-0.0,10**30,'\u03bb\\\"']},
            list(range(97)),{'nested':{'list':(None,{'empty':[],'zero':0})}},
            {'domains':[{'factors':[[r,0,0,False,r] for r in range(513)],'count':0} for _ in range(2)]}]
        for index,value in enumerate(serialization_fixtures):
            if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
                raise ValueError('original own validator changed before local limit delegation')
            if function_signature(inner_tick)!=inner_tick_anchor or function_signature(inner_tick_fn)!=inner_tick_anchor:
                raise ValueError('original inner_tick function/code/default/closure endpoint changed')
            inner_tick_fn()
            need(''.join(json_chunks(value))==canonical(value),'whole bounded JSON fixture byte correspondence')
        prepared,owned_graph=modules['payload'].prepare_owned(declaration=declaration,kernel_module=modules['kernel'],catalogue_module=modules['catalogue'],
            graph_module=modules['point_graph'],source_bindings=plan['sources'],source_guard=invoke_fn,deadline=deadline)
        if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
            raise ValueError('original own validator replaced at outer call boundary')
        if function_signature(invoke_guard)!=invoke_anchor:
            raise ValueError('original invoking shim changed at outer call boundary')
        invoke_fn()
        prepared_pin=save('Q-preparation-provisional-v1.json',prepared)
        if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
            raise ValueError('original own validator replaced at outer call boundary')
        if function_signature(invoke_guard)!=invoke_anchor:
            raise ValueError('original invoking shim changed at outer call boundary')
        invoke_fn()
        initial_record=save('Q-initial-state-witness-v2.json',prepared['initial_state'])
        model=prepared['catalogue'];initial_decision=prepared['initial_decision'];prepared=None
        writer_fn=write_snapshot;writer_anchor=function_signature(writer_fn)
        controls=modules['controls'].run_controls(declaration=declaration,model=model,owned_graph=owned_graph,
            initial_record=initial_record,initial_decision=initial_decision,kernel_module=modules['kernel'],
            graph_module=modules['point_graph'],source_bindings=plan['sources'],source_guard=invoke_fn,write_snapshot=writer_fn,deadline=deadline)
        if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
            raise ValueError('own validator replaced before writer endpoint check')
        if function_signature(writer_fn)!=writer_anchor:raise ValueError('owned snapshot writer changed')
        if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
            raise ValueError('original own validator replaced at outer call boundary')
        if function_signature(invoke_guard)!=invoke_anchor:
            raise ValueError('original invoking shim changed at outer call boundary')
        invoke_fn()
        need(controls['completed'] is True and controls['target_searches']==0 and controls['independent_mathematical_catalogue_admission'] is False,
            'whole controls complete, no search or admission')
        controls_pin=save('Q-controls-provisional-v1.json',controls)
        if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
            raise ValueError('original own validator replaced at outer call boundary')
        if function_signature(invoke_guard)!=invoke_anchor:
            raise ValueError('original invoking shim changed at outer call boundary')
        invoke_fn()
        # Completion is asserted only after full model/controls/transport bytes
        # and the final20s guard; earlier files are deliberately provisional.
        inner_complete=time.perf_counter()-inner_began
        evidence_pin=save('Q-controls-evidence-v1.json',dict(schema='cold-Q-preparation-controls-evidence-v1',
            sources=plan['sources'],inputs=plan['inputs'],worker_plan=plan_pin,owner_plan=owner_pin,
            prepared=prepared_pin,controls=controls_pin,inner_complete_seconds=inner_complete,
            complete_witness_output_closure=list(artifacts),stream_output_records_before_evidence=list(serialization_records),
            all_production_graph_constructions=1,initial_copy_released_before_controls=True,serializer_control_count=len(serialization_fixtures),
            aggregate_streamed_bytes_before_evidence=streamed_bytes[0],
            file_backed_complete_snapshot_protocol='canonical-JSON-no-trailing-newline-v2',
            executed_raw_project_source_ledger=source_cache_guard(plan['sources'],modules,anchors),
            independent_mathematical_catalogue_admission=False,universal_theorem_discovered=False,native_accepted=False,
            source_only_prototype_now_called=True,target_searches=0,RL_training_runs=0,scientific_search_activation=False))
        if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
            raise ValueError('original own validator replaced at outer call boundary')
        if function_signature(invoke_guard)!=invoke_anchor:
            raise ValueError('original invoking shim changed at outer call boundary')
        invoke_fn()
        final_receipt=output/'Q-controls-result-v1.json'
        save(final_receipt.name,dict(schema='cold-Q-preparation-controls-receipt-v1',stage='preparation',stage_completed=True,
            status='completed_producer_Q_preparation_controls_pending_ROOT',worker_plan=plan_pin,owner_plan=owner_pin,
            evidence=evidence_pin,prepared=prepared_pin,controls=controls_pin,all_direct_children_terminal_and_reaped=True,
            stream_output_records_before_receipt=list(serialization_records),
            aggregate_streamed_bytes_before_receipt=streamed_bytes[0],
            direct_children_peak_sum_bytes=0,worker_elapsed_before_receipt_seconds=time.perf_counter()-began,
            worker_SELF_peak_before_receipt_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            target_searches=0,native_queries=0,RL_training_runs=0,resource_acceptance_issued=False,
            independent_mathematical_catalogue_admission=False,universal_theorem_discovered=False,scientific_search_activation=False))
        if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
            raise ValueError('original own validator replaced at outer call boundary')
        if function_signature(invoke_guard)!=invoke_anchor:
            raise ValueError('original invoking shim changed at outer call boundary')
        invoke_fn()
        if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
            raise ValueError('original own validator changed before local limit delegation')
        if function_signature(whole_tick)!=whole_tick_anchor or function_signature(whole_tick_fn)!=whole_tick_anchor:
            raise ValueError('original whole_tick function/code/default/closure endpoint changed')
        whole_tick_fn()
        print(canonical(dict(stage_completed=True,target_searches=0,scientific_search_activation=False)),flush=True)
        if any(globals()[name] is not fn or fn.__code__ is not code for name,(fn,code) in validators.items()):
            raise ValueError('original own validator changed before local limit delegation')
        if function_signature(whole_tick)!=whole_tick_anchor or function_signature(whole_tick_fn)!=whole_tick_anchor:
            raise ValueError('original whole_tick function/code/default/closure endpoint changed')
        whole_tick_fn()
    except BaseException as exc:
        if final_receipt is not None and final_receipt.exists():
            withdrawn=output/'Q-controls-result-withdrawn-v1.json';final_receipt.rename(withdrawn)
            artifacts=[pin(withdrawn) if p['path']==str(final_receipt) else p for p in artifacts]
        failure=dict(schema='cold-Q-preparation-controls-failure-v1',stage='preparation',stage_completed=False,
            status='UNKNOWN_incomplete_Q_preparation_controls',error=dict(type=type(exc).__name__,message=str(exc)[:512]),
            worker_plan=plan_pin,owner_plan=owner_pin,provisional_artifacts=artifacts,partial_stream_paths=partial_stream_paths,accepted_prefix=False,
            target_searches=0,native_queries=0,RL_training_runs=0,scientific_search_activation=False)
        raw=(canonical(failure)+'\n').encode('utf8')
        if len(raw)<=1048576:
            with (output/'failure-v1.json').open('xb') as stream:stream.write(raw)
        raise


if __name__=='__main__':main()
