"""UNEXECUTED separate W16 cold caller, not a successful20 or proof stage.

The actual native begin precedes every remaining import/read/compile/setup.
Only Root supplies one frozen small plan path. The original controller builds
all original snapshots and the genuine full model in its owned census child.
External meter/caller resources remain independent, including interpreter and
minimal preclock time-import startup. No preparation/model is decoded here.
"""
import time
_CLOCK, _CLOCK_ID = time.clock_gettime_ns, time.CLOCK_MONOTONIC
if type(_CLOCK_ID) is not int:
    raise ValueError('exact original global clock ID')
JOINT_BEGAN_NS = _CLOCK(_CLOCK_ID)

import builtins
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
from operator import attrgetter as _PATH_ATTRGETTER
import resource
import signal
import stat
import subprocess
import sys
import tempfile
import types
import zlib

VERSION = 'Q-W16-trusted-early-cold-caller-Source-v3-global-clock'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
# Exact two pinned-stdlib native properties; never a generic callable permit.
_PATH_PURE = Path.__mro__[1]
if (_PATH_PURE.__module__ != 'pathlib' or _PATH_PURE.__name__ != 'PurePath'
        or _PATH_ATTRGETTER.__module__ != 'operator' or _PATH_ATTRGETTER.__name__ != 'attrgetter'):
    raise ValueError('original native pathlib attrgetter class origin')
_PATH_ATTRGETTER_MRO = _PATH_ATTRGETTER.__mro__
_PATH_ATTRGETTER_CALL = vars(_PATH_ATTRGETTER)['__call__']
_PATH_NATIVE_PROPERTIES = tuple((name,vars(_PATH_PURE)[name],vars(_PATH_PURE)[name].fget) for name in ('drive','root'))
if any(type(prop) is not property or type(getter) is not _PATH_ATTRGETTER
       or prop.fset is not None or prop.fdel is not None for name,prop,getter in _PATH_NATIVE_PROPERTIES):
    raise ValueError('original exact PurePath drive/root native property descriptors')
# Literal exact current Sources and original epochs are inserted by the author
# from saved Source AST/JSON only, never by executing an implementation.
# BEGIN_LITERAL_BINDINGS
CONTROLLER = {'bytes': 68771, 'sha256': '0c3a93428ef5cb4d22ea249ba8fc157f8df428322af945aeb7f8a62564080114'}
SOURCE_BINDINGS = {'census_leaf': {'bytes': 20215,
                 'sha256': 'bb30787adbeee4d479bbcad254eedcd02ed354135199524bd96103501f40aca6'},
 'codec': {'bytes': 5806, 'sha256': 'd0d922416aab576ab324397cee94e82c3ddf1e4f0131426f76802695934f88df'},
 'coordinator': {'bytes': 54630,
                 'sha256': 'dafc392dc1463cac98d36dcb8e74d164cc2aa91cb04e64ac7b9f7f304c001fab'},
 'independent_checker': {'bytes': 46514,
                         'sha256': '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3'},
 'late_leaf': {'bytes': 15699, 'sha256': 'c44016f9c1e84d24ad4fd75112ea9dac08e5810bdbce971691b5a52df285e12a'},
 'point_graph': {'bytes': 28531,
                 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'},
 'producer': {'bytes': 20219, 'sha256': '994b1ff8f3edf2621826f64fe7d974dee9041fa211e1990d76362268eb607f36'},
 'verifier': {'bytes': 48584, 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'}}
INPUT_BINDINGS = {'architecture_choice': {'bytes': 6808,
                         'sha256': '62b0d66686f890c9f604192058bdba48a4b171e233f25767b1e1de88fffbd82f'},
 'declaration': {'bytes': 2683, 'sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc'},
 'finite_ROOT_admission': {'bytes': 8563,
                           'sha256': '80dee8b9ec1bca398c24d61c10a026a82f73c8886cdeeb0ed9bf9ea5cf9c1ff1'},
 'finite_certificate': {'bytes': 5789,
                        'sha256': '3c3aefa4ff9d918a43a8b73d94fd6cebf0741e6203e0d47f3a44fbd716c7bc87'},
 'initial_oracle': {'bytes': 8295473,
                    'sha256': '03c42ca0083d5e40363d5237d69af56df4ebe3b3ae7d88fa3720fae3390d6969'},
 'initial_state': {'bytes': 8296118,
                   'sha256': 'c7e8cfd099b1b80ae170b6c35591d68d56f37aecb38f1bcf7b567d2e019acbb9'},
 'preparation': {'bytes': 38376960,
                 'sha256': '0321a462025357d188793bd45a44670adc20776e9ba30574049d77a8b5935d3a'},
 'word_controls_ROOT': {'bytes': 6796,
                        'sha256': 'f254219dc8e7324a7d15f9ff50661de627d207eca08660bca354e73978d39fd1'}}
ORIGINAL_SOURCES = {'catalogue': {'bytes': 10187,
               'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_catalog_v1.py',
               'sha256': '2db11af0d7206afd4e1c10b53b97c16f98064c14fd1e57a9a2ca34c0a602348a'},
 'controls': {'bytes': 19742,
              'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/arithmetic_Q_streamed_controls_v3.py',
              'sha256': '4e28fadd9c76ba6664e485fa2c5aa97beaa08639986b6d56aae50395b006e638'},
 'kernel': {'bytes': 10323,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py',
            'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'},
 'master': {'bytes': 21657,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/docs/basic-tiling-algorithm.md',
            'sha256': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9'},
 'payload': {'bytes': 5435,
             'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/q_preparation_owned_graph_v3.py',
             'sha256': 'ee2088bf60709f6c0c5a78297841bd0684674369fa9d3c08119b96a59caa88ad'},
 'point_graph': {'bytes': 28531,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py',
                 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'},
 'worker': {'bytes': 37266,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/arithmetic_Q_streamed_controls_worker_v7.py',
            'sha256': '75d5d80701a0815d78e182a5cb7eb99412bff5b48a5b936a8850b625743de48d'}}
RUNTIME = {'bytes': 102352,
 'path': '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',
 'sha256': 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'}
LIMITS = {'aggregate_owned_bytes': 536870912,
 'caller_finish_reserve_seconds': 1,
 'caller_seconds': 90,
 'failure_only_seconds': 55,
 'joint_seconds': 20,
 'owned_seconds': 60}
# END_LITERAL_BINDINGS
PLAN_FIELDS = {'schema','scope','author_identity','invocation_id','caller_source','caller_contract',
 'runtime','limits','sources','inputs','original_sources','reviews','run_directory',
 'raw_closure','controls_execution_authorized'}
FALSE_FLAGS = ('ROOT_primary_accepted','ROOT_resource_accepted','successful20_stage',
 'full52_qualified','full_architecture_qualified','original_Q_theorem_accepted',
 'actual_selected_accepted','point_snapshot_accepted','full24_accepted',
 'full_trajectory_accepted','native_accepted','RL_accepted')
_CANCEL = {'requested':False,'owner':None}


def need(ok, message):
    if ok is not True:raise ValueError(message)


def now(*, failure=False):
    if (time.clock_gettime_ns is not _CLOCK or type(time.CLOCK_MONOTONIC) is not int
            or time.CLOCK_MONOTONIC != _CLOCK_ID or type(_CLOCK_ID) is not int):
        raise ValueError('original native kernel clock callable/ID')
    stamp = _CLOCK(_CLOCK_ID)
    need(type(stamp) is int and JOINT_BEGAN_NS <= stamp < JOINT_BEGAN_NS + (55000000000 if failure else 20000000000),
         'original20 setup/readiness or failure-only55; never reset')
    if not failure:need(_CANCEL['requested'] is False,'cold setup interrupted')
    return stamp


def cancelled(signum, frame):
    _CANCEL['requested'] = True
    if _CANCEL['owner'] is not None:_CANCEL['owner'].cancelled = True


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf8')


def decode(raw):
    def pairs(items):
        value={}
        for key,member in items:
            need(key not in value,'duplicate metadata key');value[key]=member
        return value
    def reject(text):raise ValueError('no metadata float/nonfinite token')
    value=json.loads(raw.decode('utf8','strict'),object_pairs_hook=pairs,parse_float=reject,parse_constant=reject)
    need(type(value) is dict,'one whole metadata object');return value


def shape(record):
    need(type(record) is dict and set(record)=={'path','sha256','bytes'},'whole configured raw pin')
    need(type(record['bytes']) is int and 0<=record['bytes']<=64*1048576
         and type(record['sha256']) is str and len(record['sha256'])==64
         and all(c in '0123456789abcdef' for c in record['sha256']),'literal pin integer/SHA')
    path=Path(record['path'])
    need(type(record['path']) is str and path.is_absolute() and str(path)==str(path.resolve())
         and not path.is_symlink(),'canonical absolute original path')
    return path


def read_pin(record, *, failure=False, maximum=1048576):
    path=shape(record);need(record['bytes']<=maximum,'named small Source/metadata only')
    now(failure=failure);fd=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW)
    try:
        before=os.fstat(fd);need(stat.S_ISREG(before.st_mode) and before.st_size==record['bytes'],'whole raw regular file')
        chunks=[];count=0;digest=hashlib.sha256()
        while True:
            now(failure=failure);block=os.read(fd,min(65536,record['bytes']-count+1))
            if not block:break
            count+=len(block);need(count<=record['bytes'],'no raw prefix/suffix');chunks.append(block);digest.update(block)
        after=os.fstat(fd)
        need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
             (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'stable same descriptor through EOF')
        need(count==record['bytes'] and digest.hexdigest()==record['sha256'],'whole raw SHA/length/EOF')
        now(failure=failure);return b''.join(chunks)
    finally:os.close(fd)


def wire(record):
    shape(record);return {'sha256':record['sha256'],'bytes':record['bytes']}


def function_state(fn):
    if type(fn) is not types.FunctionType:raise ValueError('exact original Python function')
    d,k=fn.__defaults__,fn.__kwdefaults__
    if k is not None and (type(k) is not dict or any(type(n) is not str for n in k)):
        raise ValueError('literal keyword-default entries')
    return (fn,fn.__code__,id(d),d,tuple((id(v),v) for v in d or ()),id(k),k,
        tuple((n,id(v),v) for n,v in sorted((k or {}).items())),
        tuple((cell,id(cell.cell_contents),cell.cell_contents) for cell in fn.__closure__ or ()))


def data_state(value):
    if type(value) is dict:return (dict,tuple((k,data_state(v)) for k,v in sorted(value.items())))
    if type(value) in (tuple,list):return (type(value),tuple(data_state(v) for v in value))
    if type(value) in (set,frozenset):return (type(value),frozenset(data_state(v) for v in value))
    if type(value) is float:return (float,value.hex())
    if value is None or type(value) in (int,bool,str,bytes):return (type(value),value)
    return ('object',id(value),value)


def class_state(cls):
    rows=[]
    for base in cls.__mro__:
        for name,v in sorted(vars(base).items()):
            if type(v) is types.FunctionType:s=function_state(v)
            elif type(v) in (staticmethod,classmethod) and type(v.__func__) is types.FunctionType:s=(v,function_state(v.__func__))
            elif type(v) is property:
                accessors=[]
                for slot,f in enumerate((v.fget,v.fset,v.fdel)):
                    if f is None:accessors.append(None)
                    elif type(f) is types.FunctionType:accessors.append(function_state(f))
                    elif (slot==0 and base is _PATH_PURE and any(name==n and v is prop and f is getter
                            for n,prop,getter in _PATH_NATIVE_PROPERTIES)):
                        if (type(f) is not _PATH_ATTRGETTER or _PATH_ATTRGETTER.__mro__!=_PATH_ATTRGETTER_MRO
                                or vars(_PATH_ATTRGETTER).get('__call__') is not _PATH_ATTRGETTER_CALL):
                            raise ValueError('original exact native pathlib accessor type/MRO/call changed')
                        accessors.append(('native-PurePath-attrgetter',id(f),f,_PATH_ATTRGETTER,
                                          _PATH_ATTRGETTER_MRO,_PATH_ATTRGETTER_CALL))
                    else:raise ValueError('non-Python property accessor is not original PurePath drive/root getter')
                s=(v,tuple(accessors))
            else:s=(id(v),v)
            rows.append((base,name,s))
    return cls,cls.__mro__,tuple(rows)


def module_state(module, *, authored):
    rows=[]
    for name,v in sorted(vars(module).items()):
        if type(v) is types.FunctionType:s=function_state(v)
        elif type(v) is type:s=class_state(v)
        elif type(v) in (types.BuiltinFunctionType,types.BuiltinMethodType):s=(id(v),v)
        elif name=='__builtins__':
            mapping=vars(v) if type(v) is types.ModuleType else v
            s=tuple((k,function_state(item) if type(item) is types.FunctionType else (id(item),item)) for k,item in sorted(mapping.items()))
        elif authored:
            s=(id(v),v) if name=='_CANCEL' else data_state(v)
        else:
            # Only declared ordinary native caches/lifecycle data may evolve.
            # Native globals/constants/regex/parser objects remain bound.
            cache = (module is tempfile and name in ('tempdir','_name_sequence')) or (module is sys and name in ('modules','path_importer_cache')) or (module is subprocess and name=='_active')
            s=(id(v),v) if cache else data_state(v)
            if module is tempfile and name in ('tempdir','_name_sequence'):continue
        rows.append((name,s))
    return module,type(module),tuple(rows)


def effective(fn):
    if type(fn) is types.MethodType:return fn.__self__,function_state(fn.__func__)
    return function_state(fn) if type(fn) is types.FunctionType else (type(fn),id(fn),fn,getattr(fn,'__self__',None))


def load_exact(record, raw, name):
    now();need(name not in sys.modules,'fresh private cold module, no Source cache')
    module=types.ModuleType(name);module.__file__=record['path'];module.__package__='';module.__spec__=None;module.__loader__=None
    original_import=builtins.__import__
    def imports(name, globals=None, locals=None, fromlist=(), level=0):
        need(level==0 and name in ('gzip','hashlib','json','math','os','pathlib','resource','signal','stat','subprocess','sys','time','types','tempfile'),
             'only preloaded declared stdlib imports, no project loader')
        return original_import(name,globals,locals,fromlist,level)
    module.__dict__['__builtins__']=dict(vars(builtins),__import__=imports)
    sys.modules[name]=module
    exec(compile(raw,record['path'],'exec',dont_inherit=True),module.__dict__)
    now();return module


class Seal:
    __slots__=('modules','states','native','native_states','owner','owner_methods','containers','owner_class','fixed',
        'buffers','validators','entry','entry_code','registry','plan','plan_state','sealed')
    def __setattr__(self,name,value):
        if getattr(self,'sealed',False):raise ValueError('immutable cold Source seal')
        object.__setattr__(self,name,value)
    def __init__(self,modules,native,owner,buffers,plan):
        self.modules,self.native=tuple(modules),tuple(native)
        self.states=tuple(module_state(m,authored=True) for m in self.modules)
        self.native_states=tuple(module_state(m,authored=False) for m in self.native)
        self.owner,self.owner_class=owner,type(owner)
        self.owner_methods=tuple((name,effective(getattr(owner,name))) for name in
            ('check','launch','wait','reap','sample','cleanup','memory_bound','memory_diagnostic','table','active'))
        self.containers=tuple((name,getattr(owner,name)) for name in
            ('children','samples','known','launch_attempts','observer_intervals','cleanup_errors'))
        self.fixed=(owner.began_ns,owner.deadline_ns,owner.failure_ns,owner.owned_ns)
        self.buffers=tuple((b,hashlib.sha256(b).digest()) for b in buffers)
        self.validators=tuple((name,fn,fn.__code__,function_state(fn)) for name,fn in
            (('need',need),('now',now),('canonical',canonical),('function_state',function_state),('data_state',data_state),
             ('class_state',class_state),('module_state',module_state),('effective',effective)))
        self.entry,self.entry_code=Seal.check,Seal.check.__code__
        self.registry=tuple((k,id(v),v) for k,v in sorted(sys.modules.items()))
        self.plan,self.plan_state=plan,data_state(plan)
        self.sealed=True
    def check(self):
        if (Seal.check is not self.entry or self.entry.__code__ is not self.entry_code
                or time.clock_gettime_ns is not _CLOCK or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC!=_CLOCK_ID
                or function_state.__defaults__ is not None or function_state.__kwdefaults__ is not None or function_state.__closure__ is not None):
            raise ValueError('direct original cold entry/validator/native authority')
        for name,fn,code,s in self.validators:
            if globals().get(name) is not fn or fn.__code__ is not code:raise ValueError('original cold validator code changed')
        for name,fn,code,s in self.validators:
            if function_state(fn)!=s:raise ValueError('original cold validator defaults/cells changed')
        if tuple(module_state(m,authored=True) for m in self.modules)!=self.states or tuple(module_state(m,authored=False) for m in self.native)!=self.native_states:
            raise ValueError('original full Source/native/parser/global/MRO/accessor authority changed')
        if tuple((k,id(v),v) for k,v in sorted(sys.modules.items()))!=self.registry:
            raise ValueError('cold registered module cache changed')
        if type(self.owner) is not self.owner_class or (self.owner.began_ns,self.owner.deadline_ns,self.owner.failure_ns,self.owner.owned_ns)!=self.fixed:
            raise ValueError('actual Owner class/original clocks changed')
        for name,s in self.owner_methods:
            if name in self.owner.__dict__ or effective(getattr(self.owner,name))!=s:raise ValueError('actual effective Owner endpoint changed')
        for name,value in self.containers:
            if getattr(self.owner,name) is not value:raise ValueError('actual evolving Owner container identity changed')
        if data_state(self.plan)!=self.plan_state or any(hashlib.sha256(b).digest()!=h for b,h in self.buffers):
            raise ValueError('fixed metadata/authenticated immutable Source buffer changed')
        if (set(_CANCEL)!={'requested','owner'} or type(_CANCEL['requested']) is not bool or _CANCEL['owner'] is not self.owner):
            raise ValueError('declared cancellation holder changed')
        # Always failure55 for Source custody: controller/Owner enforce original20
        # until its genuine late rejection. Memory/cancellation must not prevent
        # actual failure cleanup; neither grants a success here.
        now(failure=True)


def review(record, *, source, scope, author, contract=None, sources=None):
    value=decode(read_pin(record))
    need(value.get('scope')==scope and value.get('source_only') is True and value.get('source_review_passed') is True
         and value.get('all_checks_passed') is True and type(value.get('scientific_calls')) is int and value['scientific_calls']==0
         and value.get('author_identity')==author and type(value.get('reviewer_identity')) is str and value['reviewer_identity']!=author,
         'genuine distinct current Source review, no future actual admission')
    read_pin(value['source_contract'])
    if source is not None:need(value.get('source')==source,'exact reviewed Source')
    if contract is not None:need(value.get('source_contract')==contract,'exact reviewed Source contract')
    if sources is not None:need(value.get('sources')==sources,'exact reviewed complete role map')
    return value


def main(argv):
    need(__name__=='__main__' and sys.platform=='darwin' and type(argv) is list and len(argv)==1,'genuine standalone Darwin early caller, sole Root planpath')
    need(sys.flags.isolated==1 and sys.flags.no_site==1 and sys.flags.dont_write_bytecode==1,'pinned Python -I -S -B')
    need(type(_CLOCK) is types.BuiltinFunctionType and _CLOCK.__module__=='time' and _CLOCK.__name__=='clock_gettime_ns','native original global primitive')
    need(str(Path(sys.executable).resolve())==RUNTIME['path'],'actual fixed Python runtime')
    signal.signal(signal.SIGINT,cancelled);signal.signal(signal.SIGTERM,cancelled)
    now();path=Path(argv[0]);need(path.is_absolute() and path==path.resolve() and not path.is_symlink(),'canonical frozen Root planpath')
    st=path.stat();need(stat.S_ISREG(st.st_mode) and 0<st.st_size<=1048576,'small Root plan only')
    fd=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW)
    try:
        before=os.fstat(fd)
        raw=os.read(fd,1048577);need(os.read(fd,1)==b'' and len(raw)==st.st_size,'complete Root plan EOF')
        after=os.fstat(fd)
        need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
             (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'same complete plan descriptor through EOF')
    finally:os.close(fd)
    root_plan_pin={'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    plan=decode(raw);now()
    need(set(plan)==PLAN_FIELDS and plan['schema']=='ROOT-Q-W16-early-cold-plan-v1'
         and plan['scope']=='W16_expected_late_exit_only' and plan['author_identity']=='/root'
         and plan['controls_execution_authorized'] is True,'exact genuine Root W16-only authorization')
    need(plan['runtime']==RUNTIME and plan['limits']==LIMITS and all(type(v) is int for v in plan['limits'].values()),'same original runtime/caps')
    nonce=plan['invocation_id'];need(type(nonce) is str and 1<=len(nonce)<=128 and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:' for c in nonce),'Root nonce')
    need(type(plan['sources']) is dict and set(plan['sources'])==set(SOURCE_BINDINGS)|{'W16_controller'},'complete current cold Source roles')
    for role,p in plan['sources'].items():need(wire(p)==(CONTROLLER if role=='W16_controller' else SOURCE_BINDINGS[role]),'exact current role '+role)
    need(type(plan['inputs']) is dict and set(plan['inputs'])==set(INPUT_BINDINGS),'full original8 input set')
    for role,p in plan['inputs'].items():need(wire(p)==INPUT_BINDINGS[role],'whole original input '+role)
    need(plan['original_sources']==ORIGINAL_SOURCES,'complete original7 unchanged')
    need(plan['caller_source']['path']==str(Path(__file__).resolve()),'actual early caller Source')
    need(type(plan['reviews']) is dict and set(plan['reviews'])=={'caller','controller','coordinator','census'},'four genuine current Source reviews')
    review(plan['reviews']['caller'],source=plan['caller_source'],contract=plan['caller_contract'],scope='Q-W16-trusted-early-cold-caller-Source',author='/root/arithmetic_induction')
    review(plan['reviews']['controller'],source=None,sources={k:plan['sources'][k] for k in ('W16_controller','late_leaf')},scope='Q-W16-global-clock-expected-UNKNOWN-control-Source',author='/root/hilbert_ordering_diagnosis')
    # These component records have established exact scopes/author identities;
    # no prior/future W16 actual result or successful20 qualification is used.
    review(plan['reviews']['coordinator'],source=plan['sources']['coordinator'],scope='Q-split-owned-coordinator-Source',author='/root')
    review(plan['reviews']['census'],source=plan['sources']['census_leaf'],scope='Q-neutral-full-model-census-leaf-Source',author='/root/hilbert_advice_controls')
    caller_raw=read_pin(plan['caller_source']);read_pin(plan['caller_contract']);read_pin(plan['runtime'])
    raws={role:read_pin(p) for role,p in plan['sources'].items()}
    deferred=list(plan['inputs'].values())+list(plan['original_sources'].values())
    need(type(plan['raw_closure']) is list and len(plan['raw_closure'])<=128,'bounded whole raw custody list')
    required=list(plan['sources'].values())+deferred+[plan['runtime'],plan['caller_source'],plan['caller_contract']]+list(plan['reviews'].values())
    need(all(p in plan['raw_closure'] for p in required),'all named small Sources and deferred original snapshot pins closed')
    for p in plan['raw_closure']:
        shape(p)
        if p not in deferred:read_pin(p)
    root=Path(plan['run_directory']);need(type(plan['run_directory']) is str and root.is_absolute() and str(root)==str(root.resolve()) and root.parent.is_dir() and not root.exists(),'fresh absent controller-owned directory')
    own=sys.modules[__name__]
    native=(builtins,time,json,json.decoder,json.encoder,json.scanner,gzip,zlib,hashlib,os,resource,signal,subprocess,tempfile,types,stat)
    own_before=module_state(own,authored=True);native_before=tuple(module_state(m,authored=False) for m in native)
    coordinator=load_exact(plan['sources']['coordinator'],raws['coordinator'],'_Q_W16_coordinator_'+nonce)
    coor_before=module_state(coordinator,authored=True)
    controller=load_exact(plan['sources']['W16_controller'],raws['W16_controller'],'_Q_W16_controller_'+nonce)
    controller_before=module_state(controller,authored=True)
    need(module_state(own,authored=True)==own_before and tuple(module_state(m,authored=False) for m in native)==native_before,'own/native authority retained through cold same-buffer loads')
    need(coordinator.CLOCK_DOMAIN==controller.CLOCK_DOMAIN==CLOCK_DOMAIN and coordinator.VERSION=='Q-split-owned-original-model-coordinator-Source-v6-global-clock','exact current loaded modules')
    need(coordinator.ORIGINAL_SOURCES==ORIGINAL_SOURCES and coordinator.RAW_INPUT_BINDINGS==INPUT_BINDINGS and coordinator.RUNTIME==RUNTIME,'original complete finite context')
    now();owner=coordinator.Owner(JOINT_BEGAN_NS);now()
    need(type(owner) is coordinator.Owner and owner.began_ns==JOINT_BEGAN_NS and owner.deadline_ns==JOINT_BEGAN_NS+20000000000
         and owner.failure_ns==JOINT_BEGAN_NS+55000000000 and not owner.children and not owner.launch_attempts and not owner.samples
         and not owner.observer_intervals and not owner.known and not owner.cleanup_errors and not owner.leftovers and owner.cancelled is False,'genuine unchanged complete Owner constructor, fresh native lifecycle')
    need(module_state(coordinator,authored=True)==coor_before and module_state(controller,authored=True)==controller_before
         and module_state(own,authored=True)==own_before and tuple(module_state(m,authored=False) for m in native)==native_before,
         'no authority reseal after actual original constructor')
    _CANCEL['owner']=owner
    context={'coordinator_module':coordinator,'coordinator_source_raw':raws['coordinator'],'owner':owner,'runtime':plan['runtime'],
        'run_directory':plan['run_directory'],'sources':{k:plan['sources'][k] for k in SOURCE_BINDINGS},
        'inputs':plan['inputs'],'original_sources':plan['original_sources'],'invocation_id':nonce}
    seal=Seal((own,coordinator,controller),native,owner,tuple(raws.values())+(caller_raw,),plan)
    guard_fn,guard_code,guard_state=Seal.check,Seal.check.__code__,function_state(Seal.check)
    state_fn,state_code=function_state,function_state.__code__
    def source_guard():
        if (Seal.check is not guard_fn or guard_fn.__code__ is not guard_code or function_state is not state_fn
                or state_fn.__code__ is not state_code or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None or state_fn.__closure__ is not None):
            raise ValueError('original immediate cold guard/state authority')
        if state_fn(guard_fn)!=guard_state:raise ValueError('original cold guard default-entry/cell changed')
        guard_fn(seal)
    callback,callback_code,callback_state=source_guard,source_guard.__code__,function_state(source_guard)
    entry=controller.run_W16_expected_UNKNOWN_control;entry_state=function_state(entry)
    returned=None;error=None
    try:
        if (function_state is not state_fn or state_fn.__code__ is not state_code or source_guard is not callback or callback.__code__ is not callback_code):
            raise ValueError('original precontroller callback authority')
        need(state_fn(callback)==callback_state and state_fn(entry)==entry_state,'original complete cold callback/controller state')
        if (function_state is not state_fn or state_fn.__code__ is not state_code
                or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None or state_fn.__closure__ is not None
                or source_guard is not callback or callback.__code__ is not callback_code):
            raise ValueError('original immediate callback caller authority changed')
        if state_fn(callback)!=callback_state:
            raise ValueError('original immediate callback defaults/cells changed')
        callback()
        returned=entry(context=context,source_guard=callback,joint_began_ns=JOINT_BEGAN_NS,joint_deadline_ns=JOINT_BEGAN_NS+20000000000)
    except BaseException as failure:
        error={'type':type(failure).__name__,'message':str(failure)[:2048]}
    finally:
        # Direct original validator+callback state before any postdelegate use.
        if (function_state is not state_fn or state_fn.__code__ is not state_code or state_fn.__defaults__ is not None
                or state_fn.__kwdefaults__ is not None or state_fn.__closure__ is not None
                or source_guard is not callback or callback.__code__ is not callback_code):
            raise ValueError('original postcontroller caller/callback authority')
        need(state_fn(callback)==callback_state and state_fn(entry)==entry_state,'original callback/controller preserved')
        if (function_state is not state_fn or state_fn.__code__ is not state_code
                or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None or state_fn.__closure__ is not None
                or source_guard is not callback or callback.__code__ is not callback_code):
            raise ValueError('original immediate callback caller authority changed')
        if state_fn(callback)!=callback_state:
            raise ValueError('original immediate callback defaults/cells changed')
        callback()
        # Normal controller return already cleaned its genuine two children.
        # If its wrapper failed before complete cleanup, the same native Owner
        # alone performs cleanup; never fabricate resource/reaping fields.
        if any(child['usage'] is None for child in owner.children):owner.cleanup()
        if (function_state is not state_fn or state_fn.__code__ is not state_code
                or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None or state_fn.__closure__ is not None
                or source_guard is not callback or callback.__code__ is not callback_code):
            raise ValueError('original immediate callback caller authority changed')
        if state_fn(callback)!=callback_state:
            raise ValueError('original immediate callback defaults/cells changed')
        callback()
    stamp=now(failure=True)
    memory=owner.memory_diagnostic()
    if (function_state is not state_fn or state_fn.__code__ is not state_code
            or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None or state_fn.__closure__ is not None
            or source_guard is not callback or callback.__code__ is not callback_code):
        raise ValueError('original immediate callback caller authority changed')
    if state_fn(callback)!=callback_state:
        raise ValueError('original immediate callback defaults/cells changed')
    callback()
    stamp=now(failure=True)
    complete=(error is None and type(returned) is dict and set(returned)=={'result','post_write'}
        and returned['result'].get('status')=='UNKNOWN_expected_late_exit_rejected'
        and returned['result'].get('complete_expected_UNKNOWN_evidence') is True
        and returned['post_write'].get('complete_expected_UNKNOWN_evidence') is True
        and returned['result'].get('successful20_stage') is False and returned['result'].get('all52_qualified') is False
        and all(returned['result'].get(k) is False for k in controller.FALSE_FLAGS)
        and returned['post_write'].get('successful20_stage') is False and returned['post_write'].get('all52_qualified') is False
        and returned['post_write'].get('ROOT_resource_accepted') is False and returned['post_write'].get('ROOT_primary_accepted') is False
        and returned['result'].get('joint_began_ns')==JOINT_BEGAN_NS
        and returned['result'].get('joint_deadline_ns')==JOINT_BEGAN_NS+20000000000
        and owner.cancelled is False and _CANCEL['requested'] is False and not owner.cleanup_errors and not owner.leftovers
        and len(owner.children)==2 and all(c['reaped'] is True and c['usage'] is not None for c in owner.children)
        and memory['complete'] is True and memory['peak_bytes']<=LIMITS['aggregate_owned_bytes']
        and JOINT_BEGAN_NS+20000000000<=stamp<owner.failure_ns)
    summary={'schema':'Q-W16-early-cold-caller-observation-v1','version':VERSION,'CLOCK_DOMAIN':CLOCK_DOMAIN,
        'joint_began_ns':JOINT_BEGAN_NS,'joint_deadline_ns':owner.deadline_ns,'failure_deadline_ns':owner.failure_ns,
        'observed_after_controller_ns':stamp,'invocation_id':nonce,'expected_UNKNOWN_complete':complete,
        'status':'UNKNOWN_expected_late_exit_rejected' if complete else 'UNKNOWN_incomplete',
        'caller_source':plan['caller_source'],'controller_source':plan['sources']['W16_controller'],'coordinator_source':plan['sources']['coordinator'],
        'root_plan_pin':root_plan_pin,'runtime':RUNTIME,'original_source_bindings':ORIGINAL_SOURCES,'full_input_bindings':plan['inputs'],
        'controller_result':returned,'memory_diagnostic':memory,'error':error,'cancelled':owner.cancelled,
        'setup_scope':'same earlyG before all remaining imports/Sourceauth/load/constructor and full controller snapshots+census; no parentQ parse',
        'external_meter_and_owned_caller_reconciliation_pending':True,'target_searches':0,'proofs_discovered':0}
    summary.update({k:False for k in FALSE_FLAGS})
    if root.is_dir():
        if (function_state is not state_fn or state_fn.__code__ is not state_code
                or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None or state_fn.__closure__ is not None
                or source_guard is not callback or callback.__code__ is not callback_code):
            raise ValueError('original immediate callback caller authority changed')
        if state_fn(callback)!=callback_state:
            raise ValueError('original immediate callback defaults/cells changed')
        callback()
        coordinator.write_exclusive(root/'W16-early-caller-observation.json',canonical(summary)+b'\n')
        if (function_state is not state_fn or state_fn.__code__ is not state_code
                or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None or state_fn.__closure__ is not None
                or source_guard is not callback or callback.__code__ is not callback_code):
            raise ValueError('original immediate callback caller authority changed')
        if state_fn(callback)!=callback_state:
            raise ValueError('original immediate callback defaults/cells changed')
        callback()
    notice={'schema':'Q-W16-early-caller-terminal-notice-v1','status':summary['status'],'expected_UNKNOWN_complete':complete,
        'run_directory':str(root),'ROOT_resource_accepted':False,'ROOT_primary_accepted':False}
    raw_notice=canonical(notice);need(len(raw_notice)<4096,'bounded complete terminal notice');print(raw_notice.decode(),flush=True)
    if (function_state is not state_fn or state_fn.__code__ is not state_code
            or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None or state_fn.__closure__ is not None
            or source_guard is not callback or callback.__code__ is not callback_code):
        raise ValueError('original immediate callback caller authority changed')
    if state_fn(callback)!=callback_state:
        raise ValueError('original immediate callback defaults/cells changed')
    callback()
    final_memory=owner.memory_diagnostic()
    if (function_state is not state_fn or state_fn.__code__ is not state_code
            or state_fn.__defaults__ is not None or state_fn.__kwdefaults__ is not None or state_fn.__closure__ is not None
            or source_guard is not callback or callback.__code__ is not callback_code):
        raise ValueError('original immediate callback caller authority changed')
    if state_fn(callback)!=callback_state:
        raise ValueError('original immediate callback defaults/cells changed')
    callback()
    final_ns=now(failure=True)
    return (0 if complete and not owner.cancelled and not _CANCEL['requested'] and final_memory['complete'] is True
        and final_memory['peak_bytes']<=LIMITS['aggregate_owned_bytes'] and final_ns<owner.failure_ns else 2)


if __name__=='__main__':
    try:raise SystemExit(main(sys.argv[1:]))
    except BaseException as error:
        if type(error) is SystemExit:raise
        sys.stderr.write(type(error).__name__+': '+str(error)[:2048]+'\n');raise SystemExit(2)
