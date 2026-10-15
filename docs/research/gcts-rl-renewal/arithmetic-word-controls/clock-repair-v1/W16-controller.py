"""UNEXECUTED standalone W16 controller, not the full52 worker or baseline main.

A separately reviewed trusted early-clock caller authenticates/compiles/seals
this module/current global coor6 and supplies a genuine fresh Owner. Its Source guard
must protect code/raw/effective endpoints without replacing the two explicit
original20 versus failure55 clocks. This callable cold-copies ALL original8
and original7 bytes, runs the complete unchanged census leaf once in a producer
role, then one extra control-only late-exit wrapper in a verifier role.

A useful observation remains UNKNOWN: successful20/full52/proof/resource
acceptance is ALWAYS false. No existing plan/grant/full52 main is consumed.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import types

VERSION = 'Q-W16-separate-expected-UNKNOWN-controller-Source-v6-global-clock'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
COORDINATOR = {'bytes': 54630, 'sha256': 'dafc392dc1463cac98d36dcb8e74d164cc2aa91cb04e64ac7b9f7f304c001fab'}
FIXED_SOURCES = {'census_leaf': {'bytes': 20215,
                 'sha256': 'bb30787adbeee4d479bbcad254eedcd02ed354135199524bd96103501f40aca6'},
 'codec': {'bytes': 5806,
           'sha256': 'd0d922416aab576ab324397cee94e82c3ddf1e4f0131426f76802695934f88df'},
 'coordinator': {'bytes': 54630,
                 'sha256': 'dafc392dc1463cac98d36dcb8e74d164cc2aa91cb04e64ac7b9f7f304c001fab'},
 'independent_checker': {'bytes': 46514,
                         'sha256': '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3'},
 'late_leaf': {'bytes': 15699,
               'sha256': 'c44016f9c1e84d24ad4fd75112ea9dac08e5810bdbce971691b5a52df285e12a'},
 'point_graph': {'bytes': 28531,
                 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'},
 'producer': {'bytes': 20219,
              'sha256': '994b1ff8f3edf2621826f64fe7d974dee9041fa211e1990d76362268eb607f36'},
 'verifier': {'bytes': 48584,
              'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'}}
FALSE_FLAGS = ('original_Q_theorem_accepted', 'selected_accepted', 'point_union_accepted',
 'full24_accepted', 'trajectory_accepted', 'ROOT_resource_accepted', 'RL_accepted')
CONTEXT_FIELDS = {'coordinator_module', 'coordinator_source_raw', 'owner', 'runtime',
 'run_directory', 'sources', 'inputs', 'original_sources', 'invocation_id'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def state(fn):
    need(type(fn) is types.FunctionType, 'original actual Python callable')
    return (fn, fn.__code__, id(fn.__defaults__), tuple(id(v) for v in fn.__defaults__ or ()),
            id(fn.__kwdefaults__), tuple((k, id(v)) for k,v in sorted((fn.__kwdefaults__ or {}).items())),
            tuple((id(cell), id(cell.cell_contents)) for cell in fn.__closure__ or ()))


def effective(fn):
    if type(fn) is types.MethodType:
        return (fn.__self__, state(fn.__func__))
    return state(fn) if type(fn) is types.FunctionType else (type(fn), fn, getattr(fn, '__self__', None))


def code_state(module):
    members = tuple(sorted(vars(module).items()))
    functions = [(key, state(value)) for key,value in members if type(value) is types.FunctionType]
    classes = []
    for key, cls in members:
        if type(cls) is type and cls.__module__ == module.__name__:
            for base in cls.__mro__:
                values = tuple(sorted(vars(base).items()))
                accessors = []
                for name,value in values:
                    if isinstance(value, (staticmethod, classmethod)):
                        value = value.__func__
                    if type(value) is types.FunctionType:
                        accessors.append((name, state(value)))
                    elif type(value) is property:
                        accessors.append((name, tuple(state(fn) if fn else None for fn in (value.fget,value.fset,value.fdel))))
                classes.append((key, base, values, tuple(accessors)))
    return (members, tuple(functions), tuple(classes))


def raw_pin(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def wire(record):
    need(type(record) is dict and set(record) == {'path','sha256','bytes'}, 'trusted complete configured pin')
    need(type(record['bytes']) is int and record['bytes'] >= 0, 'literal byte count')
    return {'sha256':record['sha256'],'bytes':record['bytes']}


def run_W16_expected_UNKNOWN_control(*, context, source_guard, joint_began_ns, joint_deadline_ns):
    """Only a fresh purpose-specific cold caller may supply these native objects.

    The caller captures shared begin before Source read/compile/metadata/setup.
    No future/old controls admission is required or fabricated. Current full52
    main/ColdGuard is not invoked. Root must independently review this NEW caller.
    """
    need(type(context) is dict and set(context) == CONTEXT_FIELDS, 'exact standalone Root context')
    coordinator, owner = context['coordinator_module'], context['owner']
    need(type(coordinator) is types.ModuleType and type(owner) is coordinator.Owner,
         'genuine exact current global coor6 Owner, no fabricated resource object')
    need(coordinator.CLOCK_DOMAIN == CLOCK_DOMAIN and coordinator.VERSION == 'Q-split-owned-original-model-coordinator-Source-v6-global-clock',
         'exact global-domain coordinator Source/version; no mixed clocks')
    need(type(joint_began_ns) is int and type(joint_deadline_ns) is int
         and joint_deadline_ns - joint_began_ns == 20000000000
         and owner.began_ns == joint_began_ns and owner.deadline_ns == joint_deadline_ns,
         'same original early-clock integer20; no reset')
    need(type(context['coordinator_source_raw']) is bytes and raw_pin(context['coordinator_source_raw']) == COORDINATOR,
         'same complete Root-authenticated global coordinator6 Source buffer')
    need(context['runtime'] == coordinator.RUNTIME and context['original_sources'] == coordinator.ORIGINAL_SOURCES,
         'same runtime/original7 source epoch, no profile/model rewrite')
    need(set(context['inputs']) == set(coordinator.RAW_INPUT_BINDINGS), 'complete original8 inputs')
    for name, record in context['inputs'].items():
        need(wire(record) == coordinator.RAW_INPUT_BINDINGS[name], 'whole current original input '+name)
    need(set(context['sources']) == set(FIXED_SOURCES), 'exact standalone Source roles')
    for role, record in context['sources'].items():
        need(wire(record) == FIXED_SOURCES[role], 'fixed current Source '+role)
    need(not owner.children and not owner.samples and not owner.launch_attempts
         and not owner.observer_intervals, 'genuine fresh invocation, not full52 retry')
    nonce = context['invocation_id']
    need(type(nonce) is str and 1 <= len(nonce) <= 128 and all(c in
         'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:' for c in nonce), 'Root-owned nonce')
    root = Path(context['run_directory'])
    need(root.is_absolute() and root == root.resolve() and not root.exists(), 'fresh standalone owned run namespace')
    state_fn, state_code = state, state.__code__
    effective_fn, effective_code = effective, effective.__code__
    code_fn, code_code = code_state, code_state.__code__
    need_fn, need_code = need, need.__code__
    originals = tuple((name,fn,fn.__code__,fn.__defaults__,fn.__kwdefaults__,fn.__closure__)
       for name,fn in (('state',state_fn),('effective',effective_fn),('code_state',code_fn),('need',need_fn),
                       ('raw_pin',raw_pin),('wire',wire)))
    own = sys.modules[__name__]
    own_anchor, coor_anchor = code_fn(own), code_fn(coordinator)
    guard, guard_anchor = source_guard, state_fn(source_guard)
    clock = time.clock_gettime_ns
    clock_id = time.CLOCK_MONOTONIC
    if (type(clock) is not types.BuiltinFunctionType or clock.__module__ != 'time'
            or clock.__name__ != 'clock_gettime_ns' or type(clock_id) is not int):
        raise ValueError('original native global clock callable/exact integer ID')
    owner_methods = {name:effective_fn(getattr(owner,name)) for name in
        ('check','launch','wait','reap','sample','cleanup','memory_bound','memory_diagnostic','table','active')}
    owner_containers = {name:getattr(owner,name) for name in
        ('children','samples','known','launch_attempts','observer_intervals','cleanup_errors','leftovers')}
    fixed_values = coordinator.canonical({key:value for key,value in context.items()
        if key not in ('coordinator_module','owner','coordinator_source_raw')})
    phase = {'failure':False}
    calls = []
    result = {'schema':'Q-W16-standalone-expected-UNKNOWN-result-v1','version':VERSION,
        'status':'UNKNOWN_unfinished','expected_late_gate_observed':False,'complete_expected_UNKNOWN_evidence':False,
        'control_only_extra_verifier_wrapper':True,'full_cold_census':None,'timely_verifier_readiness':None,
        'owner_wait_exception':None,'verifier_live_at_gate':None,'failure':None,'joint_began_ns':joint_began_ns,
        'joint_deadline_ns':joint_deadline_ns,'successful20_stage':False,'all52_qualified':False,
        'target_searches':0,'proofs_discovered':0,'source_functions_are_actual_only_if_Root_runs_later':True}
    result.update({name:False for name in FALSE_FLAGS})
    result.update({name:False for name in ('ROOT_primary_accepted','actual_selected_accepted',
        'point_snapshot_accepted','full_trajectory_accepted','native_accepted',
        'induction_accepted','full_PA_accepted','universal_compiler_accepted')})
    files, child, gate_ns = [], None, None
    # Declared once-only native child registration; this holder identity is stable.
    late_child_holder = {'binding': None}

    def checked():
        for name,fn,code,defaults,kwdefaults,closure in originals:
            if (own.__dict__.get(name) is not fn or fn.__code__ is not code or fn.__defaults__ is not defaults
                    or fn.__kwdefaults__ is not kwdefaults or fn.__closure__ is not closure):
                raise ValueError('original immediate W16 validator authority changed')
        if (time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int
                or time.CLOCK_MONOTONIC != clock_id) or clock(clock_id) >= (owner.failure_ns if phase['failure'] else joint_deadline_ns):
            raise TimeoutError('original20 or failure-only55; never reset')
        if type(late_child_holder) is not dict or set(late_child_holder) != {'binding'}:
            raise ValueError('original once-only late-child holder shape changed')
        binding = late_child_holder['binding']
        if binding is None:
            if any(c['role'] == 'verifier' for c in owner.children):
                raise ValueError('native verifier child must be sealed before exposure')
        else:
            if (type(binding) is not tuple or len(binding) != 5 or type(binding[0]) is not dict
                    or len(owner.children) != 2 or owner.children[1] is not binding[0]
                    or binding[0]['role'] != 'verifier' or binding[0]['process'] is not binding[1]
                    or type(binding[2]) is not int or binding[2] != 1
                    or type(binding[0]['launch_index']) is not int or binding[0]['launch_index'] != binding[2]
                    or type(binding[3]) is not int or binding[0]['launch_began_ns'] != binding[3]
                    or type(binding[4]) is not int or binding[4] <= 0 or binding[1].pid != binding[4]
                    or len(owner.launch_attempts) != 2):
                raise ValueError('original native verifier child/process/occurrence identity changed')
            attempt = owner.launch_attempts[1]
            if (attempt['role'] != 'verifier' or attempt['launch_index'] != binding[2]
                    or attempt['launch_began_ns'] != binding[3] or attempt['pid'] != binding[4]
                    or attempt['error'] is not None):
                raise ValueError('original native verifier launch provenance changed')
        if state_fn(guard) != guard_anchor:
            raise ValueError('original cold Source guard code/default/cells changed')
        if code_fn(own) != own_anchor or code_fn(coordinator) != coor_anchor:
            raise ValueError('same original own/coordinator namespace/class/property/code')
        for name,anchor in owner_methods.items():
            if name in owner.__dict__ or effective_fn(getattr(owner,name)) != anchor:
                raise ValueError('effective Owner endpoint shadow/code changed')
        # cleanup legitimately replaces leftovers with its final native census.
        for name,container in owner_containers.items():
            if name != 'leftovers' and getattr(owner,name) is not container:
                raise ValueError('actual evolving Owner container identity changed')
        if coordinator.canonical({key:value for key,value in context.items()
                if key not in ('coordinator_module','owner','coordinator_source_raw')}) != fixed_values:
            raise ValueError('fixed Source/input/runtime/nonce context changed')
        guard()
        for name,fn,code,defaults,kwdefaults,closure in originals:
            if (own.__dict__.get(name) is not fn or fn.__code__ is not code or fn.__defaults__ is not defaults
                    or fn.__kwdefaults__ is not kwdefaults or fn.__closure__ is not closure):
                raise ValueError('original W16 helper changed during guard')
        if type(late_child_holder) is not dict or set(late_child_holder) != {'binding'}:
            raise ValueError('original once-only late-child holder shape changed')
        binding = late_child_holder['binding']
        if binding is None:
            if any(c['role'] == 'verifier' for c in owner.children):
                raise ValueError('native verifier child must be sealed before exposure')
        else:
            if (type(binding) is not tuple or len(binding) != 5 or type(binding[0]) is not dict
                    or len(owner.children) != 2 or owner.children[1] is not binding[0]
                    or binding[0]['role'] != 'verifier' or binding[0]['process'] is not binding[1]
                    or type(binding[2]) is not int or binding[2] != 1
                    or type(binding[0]['launch_index']) is not int or binding[0]['launch_index'] != binding[2]
                    or type(binding[3]) is not int or binding[0]['launch_began_ns'] != binding[3]
                    or type(binding[4]) is not int or binding[4] <= 0 or binding[1].pid != binding[4]
                    or len(owner.launch_attempts) != 2):
                raise ValueError('original native verifier child/process/occurrence identity changed')
            attempt = owner.launch_attempts[1]
            if (attempt['role'] != 'verifier' or attempt['launch_index'] != binding[2]
                    or attempt['launch_began_ns'] != binding[3] or attempt['pid'] != binding[4]
                    or attempt['error'] is not None):
                raise ValueError('original native verifier launch provenance changed')
        if state_fn(guard) != guard_anchor:
            raise ValueError('cold Source guard changed during delegation')
        if not phase['failure']:
            owner.check(success=True)
        # After a genuine work failure or the expected actual20 gate, only
        # Source/clock-guarded kill/reap/raw diagnostics are allowed. Rejected
        # memory/cancellation MUST NOT prevent cleanup. All eventual acceptance
        # remains false, and expected-evidence completeness separately requires
        # real final512, uncancelled, noleftovers and originalfailure55.
        elif clock(clock_id) >= owner.failure_ns:
            raise TimeoutError('original failure55 ended during Source guard')
    checked_anchor = state_fn(checked)

    def call(fn, *args, **kwargs):
        # Main caller also checks this actual shim before each delegation.
        if state is not state_fn or state_fn.__code__ is not state_code or state_fn(checked) != checked_anchor:
            raise ValueError('original immediate checked endpoint changed')
        checked()
        if state is not state_fn or state_fn.__code__ is not state_code or effective is not effective_fn or effective_fn.__code__ is not effective_code:
            raise ValueError('original helper changed before actual delegate capture')
        anchor = effective_fn(fn)
        record = {'endpoint':getattr(fn,'__name__',str(type(fn))),'phase':'failure55' if phase['failure'] else 'original20',
                  'started_ns':clock(clock_id),'returned':False,'exception':None}
        calls.append(record)
        delegate_returned = False
        try:
            value = fn(*args,**kwargs)
            delegate_returned = True
        except BaseException as error:
            record['exception']={'type':type(error).__name__,'message':str(error)}
            binding = late_child_holder['binding']
            tracked_child = None if binding is None else binding[0]
            if (tracked_child is not None and len(args) == 1 and args[0] is tracked_child
                    and type(fn) is types.MethodType and fn.__self__ is owner
                    and fn.__func__ is coordinator.Owner.wait
                    and type(error) is ValueError and str(error) in
                        ('original joint20/failure55 deadline',
                         'original joint20/failure55 deadline after memory computation')
                    and clock(clock_id) >= joint_deadline_ns and clock(clock_id) < owner.failure_ns
                    and not owner.cancelled and tracked_child['usage'] is None and tracked_child['reaped'] is False):
                phase['failure']=True
            raise
        finally:
            record['ended_ns']=clock(clock_id)
            if state is not state_fn or state_fn.__code__ is not state_code or effective is not effective_fn or effective_fn.__code__ is not effective_code:
                raise ValueError('original helper changed after delegated call')
            for name,original,code,defaults,kwdefaults,closure in originals:
                if (own.__dict__.get(name) is not original or original.__code__ is not code
                        or original.__defaults__ is not defaults or original.__kwdefaults__ is not kwdefaults
                        or original.__closure__ is not closure):
                    raise ValueError('original full helper metadata changed after delegate')
            if effective_fn(fn) != anchor or state_fn(checked) != checked_anchor:
                raise ValueError('effective delegated code/default/cells or livecheck changed')
            if (delegate_returned and type(fn) is types.MethodType and fn.__self__ is owner
                    and fn.__func__ is coordinator.Owner.launch and args and args[0] == 'verifier'):
                # The original native Owner return is sealed exactly once BEFORE
                # checked() exposes it. No callback/cell authority is re-anchored.
                if (late_child_holder['binding'] is not None or type(value) is not dict
                        or len(owner.children) != 2 or owner.children[1] is not value
                        or value['role'] != 'verifier' or type(value['launch_index']) is not int
                        or value['launch_index'] != 1 or type(value['launch_began_ns']) is not int
                        or type(value['process'].pid) is not int or value['process'].pid <= 0
                        or value['usage'] is not None or value['reaped'] is not False
                        or len(owner.launch_attempts) != 2):
                    raise ValueError('exact once-only genuine Owner verifier child return required')
                attempt = owner.launch_attempts[1]
                if (attempt['launch_index'] != value['launch_index'] or attempt['role'] != 'verifier'
                        or attempt['launch_began_ns'] != value['launch_began_ns']
                        or attempt['pid'] != value['process'].pid or attempt['error'] is not None):
                    raise ValueError('genuine native verifier launch occurrence required')
                late_child_holder['binding'] = (value, value['process'], value['launch_index'],
                    value['launch_began_ns'], value['process'].pid)
            checked()
        checked()
        record['returned']=True
        return value
    call_fn, call_anchor = call, state_fn(call)
    try:
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(root.mkdir, mode=0o700)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        snapshots = root/'cold-snapshots'
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(snapshots.mkdir, mode=0o700)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        for group, records in (('input',context['inputs']),('original',context['original_sources']),('source',context['sources'])):
            for role,record in records.items():
                if (state is not state_fn or state_fn.__code__ is not state_code
                        or effective is not effective_fn or effective_fn.__code__ is not effective_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original actual W16 call shim/helper code/default/cell changed')
                snapshot_pin = call_fn(coordinator.stream_snapshot,record,snapshots/(group+'-'+role),owner)
                if (state is not state_fn or state_fn.__code__ is not state_code
                        or effective is not effective_fn or effective_fn.__code__ is not effective_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original actual W16 call shim/helper code/default/cell changed')
                files.append({'role':group+':'+role,'pin':snapshot_pin})
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(coordinator.read_small,context['runtime']['path'],1048576,wire(context['runtime']))
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        declaration_raw = call_fn(coordinator.read_small,snapshots/'input-declaration',2683,coordinator.RAW_INPUT_BINDINGS['declaration'])
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        declaration = call_fn(coordinator.decode,declaration_raw,2683)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        need(coordinator.digest(declaration)==coordinator.DECLARATION_VALUE_SHA256,'exact whole original declaration')
        manifest={'schema':'Q-neutral-full-model-census-manifest-v1','coordinator_invocation_id':nonce,
            'declaration':declaration,'binding':coordinator.BINDING,'original_source_bindings':coordinator.ORIGINAL_SOURCES,
            'source_bindings':{role:wire(context['sources'][key]) for role,key in
                (('census_leaf','census_leaf'),('codec','codec'),('point_graph','point_graph'))},
            'input_bindings':{role:coordinator.RAW_INPUT_BINDINGS[role] for role in
                ('preparation','initial_state','initial_oracle')},
            'scopes':{'search':False,'placement':False,'proof':False,'parent_preparation_parse':False}}
        manifest_raw=coordinator.canonical(manifest);manifest_pin=raw_pin(manifest_raw)
        manifest_path=root/'census-manifest.json'
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(coordinator.write_exclusive,manifest_path,manifest_raw)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        census_dir=root/'whole-cold-census'
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(census_dir.mkdir,mode=0o700)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        census_paths=[manifest_path,snapshots/'input-preparation',snapshots/'source-codec',
            snapshots/'source-point_graph',snapshots/'input-initial_state',snapshots/'input-initial_oracle']
        fds=[]
        try:
            for path in census_paths:
                if (state is not state_fn or state_fn.__code__ is not state_code
                        or effective is not effective_fn or effective_fn.__code__ is not effective_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original actual W16 call shim/helper code/default/cell changed')
                fd = call_fn(coordinator.regular_fd,path,os.O_RDONLY)
                if (state is not state_fn or state_fn.__code__ is not state_code
                        or effective is not effective_fn or effective_fn.__code__ is not effective_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original actual W16 call shim/helper code/default/cell changed')
                fds.append(fd)
            census_path=census_dir/'census-response.jsonl'
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            fd = call_fn(coordinator.regular_fd,census_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            fds.append(fd)
            argv=[context['runtime']['path'],'-I','-S','-B',str(snapshots/'source-census_leaf'),
                str(fds[0]),manifest_pin['sha256'],str(manifest_pin['bytes'])]+[str(fd) for fd in fds[1:]]+[str(joint_began_ns),str(joint_deadline_ns)]
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            census_child = call_fn(owner.launch,'producer',argv,fds,census_dir)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        finally:
            for fd in fds:os.close(fd)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(owner.wait,census_child)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        parsed = call_fn(coordinator.two_lines,census_path,'Q-neutral-full-model-census-response-v1','Q-neutral-full-model-census-completion-v1',owner)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        census,census_pin=parsed
        need(census['binding']==coordinator.BINDING and census['coordinator_invocation_id']==nonce
             and census['input_bindings']==manifest['input_bindings'] and census['source_bindings']==manifest['source_bindings']
             and census['joint_began_ns']==joint_began_ns and census['joint_deadline_ns']==joint_deadline_ns
             and census['constructor_returned'] is True and census['fixture'] is False
             and census['preparation_decodes']==1 and census['preparation_parses']==1
             and type(census['row_count']) is int and census['row_count']==24
             and len(census['all24_rows'])==24 and type(census['search_calls']) is int and census['search_calls']==0
             and type(census['placements']) is int and census['placements']==0
             and type(census['selected_facts']) is int and census['selected_facts']==0
             and all(census[name] is False for name in FALSE_FLAGS), 'actual complete original cold model census, no target proof/search')
        result['full_cold_census']={'body':census,'response_pin':census_pin,'argv':argv}
        authority={'schema':'Q-clean-verifier-fixed-authority-v1','coordinator_invocation_id':nonce,'declaration':declaration,
            'binding':coordinator.BINDING,'raw_input_bindings':coordinator.RAW_INPUT_BINDINGS,
            'source_bindings':{role:wire(context['sources'][role]) for role in
                ('coordinator','producer','verifier','independent_checker','point_graph')},'limits':coordinator.LIMITS}
        authority_raw=coordinator.canonical(authority);authority_pin=raw_pin(authority_raw)
        candidate={'schema':'Q-untrusted-first-candidate-word-v1','coordinator_invocation_id':nonce,
            'authority_sha256':authority_pin['sha256'],'binding':coordinator.BINDING,'submission_index':0,
            'commands':[{'rule':'axiom','name':'CONTROL_UNDECLARED','formula':['bot']}],
            'origin':{'kind':'producer_claimed_selected_original_target_ancestry','source_event_index':0,'physical_keys':[[0,0,[]]]},
            'termination':{'producer_status':'CANDIDATE_NOT_VERIFIED','root_rollback_claimed':True,
                'proof_accepted':False,'full24_accepted':False,'trajectory_accepted':False}}
        candidate_raw=coordinator.canonical(candidate);candidate_pin=raw_pin(candidate_raw)
        late_dir=root/'control-only-late-verifier'
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(late_dir.mkdir,mode=0o700)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        authority_path,candidate_path=late_dir/'authority.json',late_dir/'candidate.json'
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(coordinator.write_exclusive,authority_path,authority_raw)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(coordinator.write_exclusive,candidate_path,candidate_raw)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        fds=[]
        try:
            for path in (authority_path,candidate_path,snapshots/'source-independent_checker'):
                if (state is not state_fn or state_fn.__code__ is not state_code
                        or effective is not effective_fn or effective_fn.__code__ is not effective_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original actual W16 call shim/helper code/default/cell changed')
                fd = call_fn(coordinator.regular_fd,path,os.O_RDONLY)
                if (state is not state_fn or state_fn.__code__ is not state_code
                        or effective is not effective_fn or effective_fn.__code__ is not effective_code
                        or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                        or state_fn(call_fn) != call_anchor):
                    raise ValueError('original actual W16 call shim/helper code/default/cell changed')
                fds.append(fd)
            response_path=late_dir/'verifier-response.jsonl';ready_path=late_dir/'readiness.jsonl'
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            fd = call_fn(coordinator.regular_fd,response_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            fds.append(fd)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            sourcefd = call_fn(coordinator.regular_fd,snapshots/'source-verifier',os.O_RDONLY)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            fds.append(sourcefd)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            responsefd = call_fn(coordinator.regular_fd,response_path,os.O_RDONLY)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            fds.append(responsefd)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            readyfd = call_fn(coordinator.regular_fd,ready_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            fds.append(readyfd)
            original=[str(fds[0]),authority_pin['sha256'],str(authority_pin['bytes']),str(fds[1]),
                candidate_pin['sha256'],str(candidate_pin['bytes']),str(fds[2]),str(fds[3]),
                str(joint_began_ns),str(joint_deadline_ns)]
            late_argv=[context['runtime']['path'],'-I','-S','-B',str(snapshots/'source-late_leaf'),
                str(sourcefd),str(snapshots/'source-verifier'),str(responsefd),str(readyfd)]+original
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            child = call_fn(owner.launch,'verifier',late_argv,fds,late_dir)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        finally:
            for fd in fds:os.close(fd)
        # Complete real readiness only, never parse/accept a response prefix.
        partial_readiness=[]
        while True:
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            ready_raw = call_fn(coordinator.read_small,ready_path,16384)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            partial_readiness.append({'observed_ns':clock(clock_id),'pin':raw_pin(ready_raw)})
            if ready_raw.endswith(b'\n') and ready_raw.count(b'\n')==2:
                break
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            already_reaped = call_fn(owner.reap,child)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            need(not already_reaped,'late leaf exited before genuine readiness; not expected late rejection')
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            ignored = call_fn(owner.sample)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            ignored = call_fn(time.sleep,0.01)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        parsed = call_fn(coordinator.two_lines,ready_path,'Q-W16-ready-for-deliberate-late-exit-v1','Q-W16-readiness-completion-v1',owner)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ready,ready_pin=parsed
        need(ready['version']=='Q-W16-control-only-late-exit-verifier-leaf-Source-v3-global-clock'
             and ready['verifier_status']=='WORD_REJECTED' and ready['verifier_main_returned']==0
             and ready['joint_began_ns']==joint_began_ns and ready['joint_deadline_ns']==joint_deadline_ns
             and ready['authority_raw_sha256']==authority_pin['sha256']
             and ready['candidate_raw_sha256']==candidate_pin['sha256']
             and ready['binding']==coordinator.BINDING and ready['source_bindings']==authority['source_bindings'],
             'actual source-bound rejected-word readiness in same original context')
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        response = call_fn(coordinator.two_lines,response_path,'Q-clean-verifier-response-body-v1','Q-clean-verifier-response-completion-v1',owner)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        body,response_pin=response
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        accepted = call_fn(coordinator.verifier_response,body,authority,authority_pin,candidate,candidate_pin,owner)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        need(accepted is False and response_pin==ready['actual_response_pin'],'real verifier rejection body is complete and original')
        result['timely_verifier_readiness']={'body':ready,'ready_pin':ready_pin,'parent_observed_ns':clock(clock_id),
            'actual_response_pin':response_pin,'actual_verifier_body':body,'argv':late_argv,
            'partial_readiness_observations':partial_readiness}
        try:
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            ignored = call_fn(owner.wait,child)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            raise ValueError('late process returned timely; expected UNKNOWN late-gate not observed')
        except ValueError as error:
            # Only this actual timed method exception can enter failure capture.
            now=clock(clock_id)
            expected=str(error) in ('original joint20/failure55 deadline',
                'original joint20/failure55 deadline after memory computation')
            if not (expected and now>=joint_deadline_ns and now<owner.failure_ns
                    and not owner.cancelled and child['usage'] is None and child['reaped'] is False):
                raise
            phase['failure']=True;gate_ns=now
            result['owner_wait_exception']={'type':type(error).__name__,'message':str(error),'parent_observed_ns':now}
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            rows = call_fn(owner.table)
            if (state is not state_fn or state_fn.__code__ is not state_code
                    or effective is not effective_fn or effective_fn.__code__ is not effective_code
                    or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                    or state_fn(call_fn) != call_anchor):
                raise ValueError('original actual W16 call shim/helper code/default/cell changed')
            live=rows.get(child['process'].pid)
            need(live is not None and live['pgid']==child['process'].pid,'actual verifier-role process remains live at original deadline gate')
            result['verifier_live_at_gate']={'pid':child['process'].pid,'native_row':live,'parent_observed_ns':clock(clock_id)}
            result['expected_late_gate_observed']=True
            result['status']='UNKNOWN_expected_late_exit_rejected'
    except BaseException as error:
        phase['failure']=True
        result['failure']={'type':type(error).__name__,'message':str(error)}
    finally:
        # Failure-only55 permits cleanup/raw evidence, never late verification.
        phase['failure']=True
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(owner.cleanup)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        memory = call_fn(owner.memory_diagnostic)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        outputs = call_fn(coordinator.inventory,root,owner,success=False)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        result['memory_diagnostic']=memory
        result['owned_output_inventory_before_receipts']=outputs
        result['native_call_tape_before_receipts']=coordinator.decode(coordinator.canonical(calls),1048576)
        result['call_tape_scope']='all actual delegated cold/census/verifier/late-gate/cleanup calls through pre-receipt inventory; final publication clocks/peaks separately in post/caller'
        result['all_calls_are_recorded_through_return']=False
        result['complete_expected_UNKNOWN_evidence']=(result['expected_late_gate_observed']
            and result['failure'] is None and not owner.cancelled and not owner.cleanup_errors
            and not owner.leftovers and len(owner.children)==2
            and all(c['reaped'] is True and c['usage'] is not None for c in owner.children)
            and memory['complete'] is True and memory['peak_bytes']<=coordinator.LIMITS['aggregate_owned_bytes']
            and outputs['complete'] is True and clock(clock_id)<owner.failure_ns)
        ledger={'launch_attempts':owner.launch_attempts,'observer_intervals':owner.observer_intervals,
            'samples':owner.samples,'known_births':owner.known,'memory_diagnostic':memory,
            'children':[{k:c[k] for k in ('role','launch_index','launch_began_ns','observed_terminal_ns',
                'wait4_pid','wait_status','kernel_peak_bytes','reaped')}|{'pid':c['process'].pid,'returncode':c['process'].returncode}
                for c in owner.children],'cleanup_errors':owner.cleanup_errors,'leftovers':owner.leftovers}
        ledger_raw=gzip.compress(coordinator.canonical(ledger)+b'\n',mtime=0)
        result['ownership_ledger']={'path':'W16-owned-ledger.json.gz',**raw_pin(ledger_raw)}
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(coordinator.write_exclusive,root/'W16-owned-ledger.json.gz',ledger_raw)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        result['source_snapshot_pins']=files
        result_raw=coordinator.canonical(result)+b'\n'
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(coordinator.write_exclusive,root/'W16-expected-UNKNOWN-result.json',result_raw)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(coordinator.read_small,root/'W16-expected-UNKNOWN-result.json',8*1048576,raw_pin(result_raw))
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        final_memory = call_fn(owner.memory_diagnostic)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        post={'schema':'Q-W16-expected-UNKNOWN-post-write-v1','result_pin':raw_pin(result_raw),
            'ownership_ledger':result['ownership_ledger'],'joint_began_ns':joint_began_ns,
            'joint_deadline_ns':joint_deadline_ns,'failure_deadline_ns':owner.failure_ns,
            'observed_post_ns':clock(clock_id),'memory_diagnostic':final_memory,
            'native_call_tape_through_result_write_read':coordinator.decode(coordinator.canonical(calls),1048576),
            'complete_expected_UNKNOWN_evidence':result['complete_expected_UNKNOWN_evidence']
                and final_memory['complete'] is True and final_memory['peak_bytes']<=coordinator.LIMITS['aggregate_owned_bytes']
                and not owner.cancelled and clock(clock_id)<owner.failure_ns,
            'successful20_stage':False,'all52_qualified':False,'ROOT_resource_accepted':False,
            'ROOT_primary_accepted':False,'original_Q_theorem_accepted':False,
            'actual_selected_accepted':False,'point_snapshot_accepted':False,
            'full24_accepted':False,'full_trajectory_accepted':False,'native_accepted':False,
            'induction_accepted':False,'full_PA_accepted':False,'RL_accepted':False}
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(coordinator.write_exclusive,root/'W16-post-write.json',coordinator.canonical(post)+b'\n')
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
        ignored = call_fn(owner.memory_diagnostic)
        if (state is not state_fn or state_fn.__code__ is not state_code
                or effective is not effective_fn or effective_fn.__code__ is not effective_code
                or call_fn is not call_anchor[0] or call_fn.__code__ is not call_anchor[1]
                or state_fn(call_fn) != call_anchor):
            raise ValueError('original actual W16 call shim/helper code/default/cell changed')
    return {'result':result,'post_write':post}
