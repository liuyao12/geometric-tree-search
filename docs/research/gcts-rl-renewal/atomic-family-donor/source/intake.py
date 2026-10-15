"""Source-only proposal: one admitted ordinary proof as TRAINING/debug donor.

One owned process, no child launch. No Q catalogue/state/oracle read, no recipient
or graph, and no supplied family/root/route. ROOT's earlier searched-word admission
is historical provenance; unchanged1717 rechecks the full closed-target word.
The existing CodeSeal covers fixed same-buffer modules and parser endpoints in a
fresh synchronous process, not an asynchronous hostile interpreter/OS guarantee.
"""
import time
_NATIVE_CLOCK_GETTIME_NS = time.clock_gettime_ns
_NATIVE_CLOCK_ID = time.CLOCK_MONOTONIC
EARLY_BEGAN_NS = _NATIVE_CLOCK_GETTIME_NS(_NATIVE_CLOCK_ID)
import builtins
import copy
import fcntl
import hashlib
import itertools
import json
import json.decoder
import json.encoder
import json.scanner
import math
import os
from pathlib import Path
import resource
import select
import stat
import sys
import types

VERSION = 'atomic-family-admitted-donor-training-intake-Source-v2'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
AUTHOR = '/root/hilbert_ordering_diagnosis'
REVIEW_SCOPE = 'atomic-family-admitted-donor-training-intake-Source'
_NATIVE_EXIT = os._exit
MAX_SMALL = 1048576
RESPONSE_MAX = 2*1048576
FIXED_SOURCES = {'checker_adapter': {'bytes': 3901,
                     'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/equality-operand-transport-source-20261015/checker_adapters_v1.py',
                     'sha256': 'b32ae182d7deda4707eca3ee7f99dfe8d526ec246778d7a994339aef640e069f'},
 'clean_support': {'bytes': 48584,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py',
                   'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'},
 'family': {'bytes': 29157,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/typed-atomic-context-family-source-20261015/typed_atomic_context_transport_v2.py',
            'sha256': 'e4998ebf6a4045396b2c4475f8e41d37f83dcb98f09b30676b30bf38f86093ee'},
 'independent_checker': {'bytes': 46514,
                         'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-mathematical-audit-source-20261014/independent_Q_semantics_v1.py',
                         'sha256': '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3'}}
FIXED_INPUTS = {'checked_candidate': {'bytes': 4292,
                       'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/primary-owned-v1/verifier-candidate.json',
                       'sha256': 'cb8f196ae80c97e41e8be6b5dd8e48b3a49a2ade903978b083e970fe1534bcf4'},
 'checked_verifier_response': {'bytes': 5051,
                               'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/primary-owned-v1/verifier-response.jsonl',
                               'sha256': '7076d1c96f2bbf66e5ba4f732e1ec166074aee35f292291a55e8501a71c95a85'},
 'declaration': {'bytes': 2683,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/Q-declaration-v1.json',
                 'sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc'},
 'original_authority': {'bytes': 2990,
                        'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/primary-owned-v1/verifier-authority.json',
                        'sha256': '75d731bdc4ab9ce986eaf5768583da40678f1b295cc88c98a2a7e263770afb54'},
 'prior_ROOT_disposition': {'bytes': 2576,
                            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/ROOT-primary-disposition-v1.json',
                            'sha256': '1f4d947319f65e24256322c24933881856ec3a90011c6499708145f18d3cdef7'},
 'prior_authorization': {'bytes': 2285,
                         'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/ROOT-primary-authorization-v1.json',
                         'sha256': 'd078ac950ca7743cea470fc6e8279f644d7be6efb8d4b1e68c69ff7aa8802dcc'},
 'prior_plan': {'bytes': 9646,
                'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/ROOT-primary-plan-v1.json',
                'sha256': '2025b362053e1926da033c9e6260e1a3fd8ec0141cc1c6c5b94e62b0a1c37756'},
 'searched_producer_response': {'bytes': 6846,
                                'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015/primary-owned-v1/producer-response.jsonl',
                                'sha256': '28038e79c4e27576581b7c64bc8be298aeaa1a3105a8a73e875d90c2bfa7c083'}}
FAMILY_CONTRACT = {'bytes': 12386,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/typed-atomic-context-family-source-20261015/Source-contract-v2.json',
 'sha256': '2436441fec2ec9482d460139ea13f4ce8e3fc8be07a4276725237b9ff2434f1c'}
FAMILY_PEER = {'bytes': 3472,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/typed-atomic-context-family-independent-source-20261015/typed-Source-review-v1.json',
 'sha256': '3164ef1b1a22d873f6c0d6307c61cb7bae5181e46ad69a1f00b82c4aa5ecd9c0'}
PROTOCOL = {'bytes': 5048,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/atomic-family-donor-ROOT-20261015/ROOT-protocol-choice-v1.json',
 'sha256': '35fe07d4d24fdb1181fddfc711c22c6bddf7f9b204fd09864520f9fc27438b12'}
RUNTIME = {'bytes': 102352,
 'path': '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',
 'sha256': 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'}
LIMITS = {'aggregate_owned_bytes': 536870912,
 'caller_finish_reserve_seconds': 1,
 'caller_seconds': 90,
 'failure_only_seconds': 55,
 'joint_seconds': 20,
 'owned_seconds': 60}


def need(ok, message):
    if not ok:
        raise ValueError(message)

def integer(value, low=0, high=(1 << 63) - 1):
    need(type(value) is int and low <= value <= high, 'literal bounded integer')
    return value

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf8')

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def pin_bytes(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def duplicate_free(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'duplicate JSON key')
        result[key] = value
    return result

def no_constant(token):
    raise ValueError('non-finite JSON token prohibited: ' + token)

def no_float(token):
    raise ValueError('floating token prohibited in semantic/control data')

def signed_integer(token):
    need(len(token) <= 20, 'bounded integer token')
    value = int(token)
    need(-(1 << 63) <= value < (1 << 63), 'signed64 JSON integer')
    return value

def finite_float(token):
    value = float(token)
    need(math.isfinite(value), 'finite diagnostic float')
    return value

def tree(value, depth=0, visits=None):
    if visits is None:
        visits = [0]
    visits[0] += 1
    need(depth <= 64 and visits[0] <= 500000, 'whole bounded data tree')
    if type(value) is dict:
        for key, item in value.items():
            need(type(key) is str and len(key.encode('utf8')) <= 128, 'bounded member')
            tree(item, depth + 1, visits)
    elif type(value) is list:
        for item in value:
            tree(item, depth + 1, visits)
    elif type(value) is str:
        need(len(value.encode('utf8')) <= 4096, 'bounded string')
    else:
        need(type(value) in (int, float, bool, type(None)), 'JSON scalar')
        if type(value) is float:
            need(math.isfinite(value), 'finite scalar')

def decode(raw, cap, *, diagnostic_floats=False):
    need(type(raw) is bytes and len(raw) <= cap, 'complete bounded buffer')
    decoder = json.JSONDecoder(object_pairs_hook=duplicate_free,
        parse_int=signed_integer, parse_float=finite_float if diagnostic_floats else no_float,
        parse_constant=no_constant, strict=True)
    text = raw.decode('utf8', 'strict')
    start = 0
    while start < len(text) and text[start] in ' \t\r\n':
        start += 1
    value, end = decoder.raw_decode(text, start)
    need(all(character in ' \t\r\n' for character in text[end:]), 'one whole JSON plus exact whitespace/EOF')
    tree(value)
    return value

def regular_fd(path, flags):
    path = Path(path)
    need(path.is_absolute() and path == path.resolve(), 'canonical owned/configured path')
    fd = os.open(str(path), flags | os.O_NOFOLLOW)
    try:
        need(stat.S_ISREG(os.fstat(fd).st_mode), 'regular file; no symlink/device')
        return fd
    except BaseException:
        os.close(fd)
        raise

def read_small(path, cap, expected=None):
    fd = regular_fd(path, os.O_RDONLY)
    try:
        before = os.fstat(fd)
        need(before.st_size <= cap, 'whole file bound, never truncate')
        raw = b''
        while True:
            block = os.read(fd, min(65536, cap - len(raw) + 1))
            if not block:
                break
            raw += block
            need(len(raw) <= cap, 'complete bounded file')
        after = os.fstat(fd)
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'stable opened file')
        if expected is not None:
            need(type(expected) is dict and set(expected) in
                 ({'sha256','bytes'}, {'path','sha256','bytes'}), 'exact configured raw pin')
            if 'path' in expected:
                need(expected['path'] == str(path), 'same configured path-bearing raw pin')
            need(pin_bytes(raw) == {key:expected[key] for key in ('sha256','bytes')},
                 'same complete authenticated file buffer')
        return raw
    finally:
        os.close(fd)

def write_exclusive(path, raw):
    fd = regular_fd(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        offset = 0
        while offset < len(raw):
            count = os.write(fd, raw[offset:offset + 65536])
            need(count > 0, 'complete owned write')
            offset += count
    finally:
        os.close(fd)

def anchor(fn):
    need(type(fn) is types.FunctionType, 'original Python function')
    return (fn, fn.__code__, fn.__globals__, fn.__defaults__, fn.__kwdefaults__,
            tuple((cell, cell.cell_contents) for cell in fn.__closure__ or ()),
            tuple((key, id(value), value) for key, value in sorted((fn.__kwdefaults__ or {}).items())))

def same(fn, state):
    return (fn is state[0] and fn.__code__ is state[1] and fn.__globals__ is state[2]
        and fn.__defaults__ is state[3] and fn.__kwdefaults__ is state[4]
        and len(fn.__closure__ or ()) == len(state[5])
        and all(a is b and a.cell_contents is value for a, (b, value)
                in zip(fn.__closure__ or (), state[5]))
        and tuple((k, id(v)) for k, v in sorted((fn.__kwdefaults__ or {}).items()))
            == tuple((k, token) for k, token, value in state[6])
        and all(fn.__kwdefaults__[k] is v for k, token, v in state[6]))


def load_fixed(role, raw):
    name = '_atomic_training_' + role
    need(name not in sys.modules, 'fresh private registered dependency')
    module = types.ModuleType(name)
    module.__file__ = '<authenticated-' + role + '-' + FIXED_SOURCES[role]['sha256'] + '>'
    sys.modules[name] = module
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


def exact_limits(value):
    need(type(value) is dict and set(value) == set(LIMITS)
         and all(type(value[k]) is int and value[k] == LIMITS[k] for k in LIMITS),
         'literal unchanged20/55/60/512/90+1 limits')


def metadata_review(value, source, contract, sources, reviewer):
    need(type(value) is dict and value.get('source_only') is True
         and value.get('source_review_passed') is True
         and type(value.get('scientific_calls')) is int and value['scientific_calls'] == 0
         and value.get('scientific_acceptance') is False and value.get('scope') == REVIEW_SCOPE
         and value.get('source') == source and value.get('source_contract') == contract
         and value.get('sources') == sources and value.get('author_identity') == AUTHOR
         and value.get('reviewer_identity') == reviewer and reviewer != AUTHOR,
         'genuine current exact whole Source5 review')


def validate_plan(plan, own_pin):
    need(type(plan) is dict and set(plan) == {
        'schema','invocation_id','purpose','output_directory','resource_rule','runtime','limits',
        'source_contract','sources','inputs','reviews','protocol_choice','family_contract',
        'family_peer','ROOT_authorization'}, 'sole Root plan exact15 fields')
    need(plan['schema'] == 'ROOT-atomic-family-donor-training-plan-v1'
         and plan['purpose'] == 'admitted-donor-training'
         and plan['resource_rule'] == 'single-owned-process-native-terminal-v1', 'explicit training lane')
    name = plan['invocation_id']
    need(type(name) is str and 1 <= len(name) <= 128
         and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name),
         'bounded ASCII invocation')
    exact_limits(plan['limits'])
    need(plan['runtime'] == RUNTIME and Path(sys.executable).resolve() == Path(RUNTIME['path']).resolve()
         and sys.platform == 'darwin', 'same pinned native Darwin runtime')
    need(type(plan['sources']) is dict and set(plan['sources']) == {'intake',*FIXED_SOURCES}
         and all(plan['sources'][r] == p for r,p in FIXED_SOURCES.items())
         and plan['sources']['intake'] == dict(own_pin,path=str(Path(__file__).resolve())),
         'current exact Source5; no extra executable role')
    need(plan['inputs'] == FIXED_INPUTS and plan['protocol_choice'] == PROTOCOL
         and plan['family_contract'] == FAMILY_CONTRACT and plan['family_peer'] == FAMILY_PEER,
         'only eight exact small saved inputs and current protocol/family metadata')
    need(type(plan['reviews']) is dict and set(plan['reviews']) == {'ROOT','peer'}, 'two current reviews')
    for record in [plan['source_contract'],plan['ROOT_authorization'],*plan['reviews'].values()]:
        need(type(record) is dict and set(record) == {'path','sha256','bytes'}
             and type(record['bytes']) is int and 0 < record['bytes'] <= MAX_SMALL,
             'bounded complete current metadata capsule')


def historical_two_lines(raw, body_schema, completion_schema):
    need(type(raw) is bytes and len(raw) <= MAX_SMALL and raw.endswith(b'\n')
         and raw.count(b'\n') == 2, 'complete exact two LF lines and EOF')
    body_raw, completion_raw, final = raw.split(b'\n')
    body = decode(body_raw,MAX_SMALL,diagnostic_floats=True)
    completion = decode(completion_raw,1024)
    need(final == b'' and canonical(body) == body_raw and canonical(completion) == completion_raw
         and body['schema'] == body_schema and set(completion) == {
             'schema','body_bytes','body_sha256','exit_zero_and_coordinator_deadline_required'}
         and completion['schema'] == completion_schema
         and type(completion['body_bytes']) is int and completion['body_bytes'] == len(body_raw)+1
         and completion['body_sha256'] == hashlib.sha256(body_raw+b'\n').hexdigest()
         and completion['exit_zero_and_coordinator_deadline_required'] is True,
         'whole canonical historical body/completion hash includes LF')
    return body


def bind_historical(values):
    declaration, prior, grant, admitted, producer, verified, candidate, authority = (
        values[k] for k in ('declaration','prior_plan','prior_authorization','prior_ROOT_disposition',
                           'searched_producer_response','checked_verifier_response','checked_candidate',
                           'original_authority'))
    binding = grant['binding']
    need(prior['schema'] == 'ROOT-ordinary-Q-cold-plan-v1' and prior['purpose'] == 'primary'
         and type(prior['sources']) is dict and len(prior['sources']) == 9
         and type(prior['inputs']) is dict and len(prior['inputs']) == 8
         and type(prior['original_sources']) is dict and len(prior['original_sources']) == 7
         and prior['authorization'] == FIXED_INPUTS['prior_authorization'], 'complete historical Source9/input8/original7 metadata')
    need(admitted['schema'] == 'ROOT-ordinary-Q-saved-disposition-v1'
         and admitted['plan'] == FIXED_INPUTS['prior_plan'] and admitted['primary_accepted'] is True
         and admitted['resource_accepted'] is True and admitted['purpose'] == 'primary'
         and admitted['all_true_reaped'] is True
         and admitted['point_full24_trajectory_native_RL_accepted'] is False,
         'genuine prior Root admission, not producer authority')
    need(grant['schema'] == 'ROOT-ordinary-Q-cold-authorization-v1'
         and grant['author_identity'] == '/root' and grant['actual_execution_authorized'] is True
         and grant['invocation_id'] == prior['invocation_id'] and grant['purpose'] == 'primary'
         and grant['source_bindings'] == {r:pin_bytes_record(p) for r,p in prior['sources'].items()},
         'linked once-only original searched invocation')
    exact_limits(grant['limits']);exact_limits(prior['limits']);exact_limits(authority['limits'])
    need(authority['schema'] == 'Q-ordinary-word-fixed-authority-v1' and authority['declaration'] == declaration
         and authority['coordinator_invocation_id'] == prior['invocation_id']
         and authority['binding'] == binding and binding['declaration_sha256'] == FIXED_INPUTS['declaration']['sha256']
         and authority['raw_input_bindings'] == {r:pin_bytes_record(p) for r,p in prior['inputs'].items()}
         and authority['source_bindings'] == {r:pin_bytes_record(prior['sources'][s]) for r,s in
             (('coordinator','intake'),('independent_checker','independent_checker'),
              ('ordinary_adapter','ordinary_adapter'),('ordinary_producer','ordinary_producer'))},
         'exact original declaration/target/Gamma/parameters and four epochs')
    need(producer['schema'] == 'Q-ordinary-producer-response-body-v1'
         and producer['coordinator_invocation_id'] == prior['invocation_id']
         and producer['binding'] == binding and producer['authority_sha256'] == FIXED_INPUTS['original_authority']['sha256']
         and producer['source_bindings'] == {r:pin_bytes_record(prior['sources'][s]) for r,s in
             (('bootstrap','producer_bootstrap'),('codec','codec'),('producer','ordinary_producer'))}
         and producer['result']['schema'] == 'Q-untrusted-ordinary-first-ready-return-v1'
         and producer['result']['candidate'] == candidate
         and producer['result']['producer_status'] == 'CANDIDATE_NOT_VERIFIED', 'complete actual ordinary return')
    need(candidate['schema'] == 'Q-untrusted-ordinary-first-ready-word-v1'
         and candidate['coordinator_invocation_id'] == prior['invocation_id'] and candidate['binding'] == binding
         and candidate['authority_sha256'] == FIXED_INPUTS['original_authority']['sha256']
         and type(candidate['submission_index']) is int and candidate['submission_index'] == 0
         and type(candidate['commands']) is list and 0 < len(candidate['commands']) <= declaration['height']
         and candidate['origin']['kind'] == 'ordinary_first_ready_forward_saturation', 'whole searched word and origin')
    commands = candidate['commands']
    origin = candidate['origin']
    need(all(type(origin[k]) is list and len(origin[k]) == len(commands) for k in
         ('recipe_indices','formula_codes','discovery_ordinals'))
         and all(type(n) is int and n >= 0 for k in ('recipe_indices','formula_codes','discovery_ordinals') for n in origin[k])
         and all(a < b for a,b in zip(origin['discovery_ordinals'],origin['discovery_ordinals'][1:])),
         'literal whole historical row-origin arrays; no independent saturation replay claimed')
    validation = verified['validation']; cert = validation['certificate']
    need(verified['schema'] == 'Q-ordinary-clean-response-body-v1'
         and verified['coordinator_invocation_id'] == prior['invocation_id'] and verified['binding'] == binding
         and verified['candidate_raw_sha256'] == FIXED_INPUTS['checked_candidate']['sha256']
         and verified['authority_raw_sha256'] == FIXED_INPUTS['original_authority']['sha256']
         and verified['source_bindings'] == authority['source_bindings']
         and validation['status'] == 'WORD_ACCEPTED' and validation['word_logically_accepted'] is True
         and cert['completed'] is True and cert['original_Gamma_target_sequent_accepted'] is True
         and cert['commands_sha256'] == digest(commands) and cert['target'] == declaration['target']
         and cert['theory_sha256'] == digest(declaration['theory'])
         and cert['original_ordered_Gamma'] == declaration['ordered_Gamma']
         and cert['parameters'] == declaration['parameters'] and len(cert['rows']) == len(commands),
         'complete saved independent closed-target certificate binds same actual buffers')
    for i,(row,command) in enumerate(zip(cert['rows'],commands)):
        refs = [command['antecedent'],command['implication']] if command['rule'] == 'mp' else (
               [command['source']] if command['rule'] == 'generalize' else [])
        need(type(row['row']) is int and row['row'] == i and row['rule'] == command['rule']
             and row['ordered_prior_rows'] == refs and row['formula_sha256'] == digest(command['formula'])
             and all(type(r) is int and 0 <= r < i for r in refs), 'whole row hashes and ordered prior ports')
    context = {k:declaration[k] for k in ('theory','parameters','ordered_Gamma','target')}
    return {'id':prior['invocation_id'],'profile':'Q-six-rule-open-parameter','context':context,
            'commands':commands,'origin':{'prior_ROOT_admission':FIXED_INPUTS['prior_ROOT_disposition'],
            'saved_inputs':FIXED_INPUTS,'producer_origin':origin,'binding':binding,
            'historical_origin_scope':'Root-admitted actual searched return; no independent saturation trace replay'}}


def pin_bytes_record(record):
    return {k:record[k] for k in ('sha256','bytes')}


def invoke(fn, args, kwargs, boundary, boundary_anchor, anchor_fn, anchor_code, same_fn, same_code):
    # Both ordinary return and exceptional return pass the same full guard.
    # This prevents a custody/timeout fault from masquerading as a negative.
    if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn
            or same_fn.__code__ is not same_code or anchor_fn.__defaults__ is not None
            or same_fn.__defaults__ is not None or anchor_fn.__kwdefaults__ is not None
            or same_fn.__kwdefaults__ is not None or anchor_fn.__closure__ is not None
            or same_fn.__closure__ is not None):
        raise RuntimeError('original invoking validators changed')
    fn_anchor = anchor_fn(fn)
    if boundary.__code__ is not boundary_anchor[1] or not same_fn(boundary,boundary_anchor):
        raise RuntimeError('original invoking boundary changed')
    boundary()
    if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn
            or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1]
            or not same_fn(boundary,boundary_anchor) or not same_fn(fn,fn_anchor)):
        raise RuntimeError('original pre-delegation callback/endpoint changed')
    try:
        return fn(*args,**kwargs)
    finally:
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn
                or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1]
                or not same_fn(boundary,boundary_anchor) or not same_fn(fn,fn_anchor)):
            raise RuntimeError('actual delegated endpoint or boundary changed')
        boundary()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn
                or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1]
                or not same_fn(boundary,boundary_anchor) or not same_fn(fn,fn_anchor)):
            raise RuntimeError('post-delegation boundary or endpoint changed')


def main(argv, *, joint_began_ns):
    need(len(argv) == 1 and type(joint_began_ns) is int and joint_began_ns > 0, 'sole Root plan and true early native begin')
    began, end = joint_began_ns, joint_began_ns+20000000000
    clock, clock_id, usage, self_id, exit_fn = (_NATIVE_CLOCK_GETTIME_NS,_NATIVE_CLOCK_ID,
        resource.getrusage,resource.RUSAGE_SELF,_NATIVE_EXIT)
    def tick():
        if (time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int
                or time.CLOCK_MONOTONIC is not clock_id or type(clock) is not types.BuiltinFunctionType
                or resource.getrusage is not usage or resource.RUSAGE_SELF is not self_id
                or os._exit is not exit_fn or _NATIVE_EXIT is not exit_fn):
            raise RuntimeError('original native clock/resource/exit endpoints changed')
        now = clock(clock_id)
        peak = usage(self_id).ru_maxrss
        if type(now) is not int or not began <= now < end or type(peak) is not int or peak >= 524288000:
            raise TimeoutError('whole original20/500MiB donor stage incomplete')
    tick()
    own_raw = read_small(str(Path(__file__).resolve()),MAX_SMALL)
    plan_raw = read_small(argv[0],MAX_SMALL);plan = decode(plan_raw,MAX_SMALL)
    validate_plan(plan,pin_bytes(own_raw));tick()
    # All metadata intakes parse the exact authenticated buffer; no path to any
    # historical large input is followed. Fixed Source4 is loaded once only.
    metadata_records = {'source_contract':plan['source_contract'],'ROOT_authorization':plan['ROOT_authorization'],
        'protocol_choice':PROTOCOL,'family_contract':FAMILY_CONTRACT,'family_peer':FAMILY_PEER,
        'ROOT_review':plan['reviews']['ROOT'],'peer_review':plan['reviews']['peer']}
    meta_raw = {r:read_small(p['path'],MAX_SMALL,p) for r,p in metadata_records.items()}
    metadata = {r:decode(raw,MAX_SMALL) for r,raw in meta_raw.items()};tick()
    for r in ('ROOT','peer'):
        reviewer = metadata[r+'_review'].get('reviewer_identity')
        need(type(reviewer) is str and (reviewer == '/root' if r == 'ROOT' else reviewer not in ('/root',AUTHOR)), 'distinct actual reviewer')
        metadata_review(metadata[r+'_review'],plan['sources']['intake'],plan['source_contract'],plan['sources'],reviewer)
    grant=metadata['ROOT_authorization']
    need(grant.get('schema') == 'ROOT-atomic-family-donor-training-authorization-v1'
         and grant.get('author_identity') == '/root' and grant.get('actual_execution_authorized') is True
         and grant.get('invocation_id') == plan['invocation_id'] and grant.get('purpose') == plan['purpose']
         and grant.get('source_bindings') == plan['sources'] and grant.get('inputs') == FIXED_INPUTS
         and grant.get('resource_rule') == plan['resource_rule'] and grant.get('protocol_choice') == PROTOCOL,
         'genuine fresh once-only Root training authorization')
    exact_limits(grant['limits'])
    need(metadata['source_contract'].get('schema') == 'atomic-family-admitted-donor-training-Source-contract-v1'
         and metadata['source_contract'].get('sources') == plan['sources']
         and metadata['protocol_choice']['schema'] == 'ROOT-prospective-atomic-family-donor-choice-v1'
         and metadata['family_peer'].get('source_only') is True
         and metadata['family_peer'].get('source_review_passed') is True
         and metadata['family_peer'].get('source') == FIXED_SOURCES['family']
         and metadata['family_peer'].get('source_contract') == FAMILY_CONTRACT,
         'current wrapper/family authority; no activation from Source-only protocol')
    raw_sources = {'intake':own_raw}
    raw_sources.update({r:read_small(p['path'],MAX_SMALL,p) for r,p in FIXED_SOURCES.items()});tick()
    support = load_fixed('clean_support',raw_sources['clean_support'])
    family = load_fixed('family',raw_sources['family'])
    adapter = load_fixed('checker_adapter',raw_sources['checker_adapter'])
    checker = load_fixed('independent_checker',raw_sources['independent_checker'])
    need(family.VERSION == 'mined-typed-atomic-context-transport-Source-v2'
         and checker.VERSION == 'independent-complete-finite-Q-semantics-v1', 'unchanged family and checker')
    strict_decoder = json.JSONDecoder(object_pairs_hook=duplicate_free,parse_int=signed_integer,
        parse_float=no_float,parse_constant=no_constant,strict=True)
    modules = (sys.modules[__name__],support,family,adapter,checker,json,json.decoder,json.encoder,
        json.scanner,copy,hashlib,itertools,math,os,select,sys,time,types,resource,fcntl,stat)
    seal = support.CodeSeal(modules,strict_decoder,end)
    functions=[]
    for module in modules:
        for value in vars(module).values():
            if type(value) is types.FunctionType and value.__module__ == module.__name__:functions.append(value)
            elif isinstance(value,type) and value.__module__ == module.__name__:
                for cls in value.__mro__:
                    for member in vars(cls).values():
                        if type(member) in (staticmethod,classmethod):member=member.__func__
                        if type(member) is types.FunctionType:functions.append(member)
                        elif type(member) is property:
                            functions.extend(f for f in (member.fget,member.fset,member.fdel) if type(f) is types.FunctionType)
    states=tuple((fn,anchor(fn)) for fn in functions)
    anchor_fn,anchor_code,same_fn,same_code=anchor,anchor.__code__,same,same.__code__
    tick_state=anchor(tick)
    check_method,check_function,check_code=seal.check,support.CodeSeal.check,support.CodeSeal.check.__code__
    immutable_intake=digest({'plan':plan,'metadata':metadata})
    def guard():
        for phase in (0,1):
            if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
                    or same is not same_fn or same_fn.__code__ is not same_code
                    or support.CodeSeal.check is not check_function or check_function.__code__ is not check_code
                    or check_method.__self__ is not seal or check_method.__func__ is not check_function):
                raise RuntimeError('original immediate donor validators changed')
            if any(not same_fn(fn,state) for fn,state in states) or not same_fn(tick,tick_state):
                raise RuntimeError('full original callable/default/closure state changed')
            tick()
            if phase == 0:check_method()
        need(digest({'plan':plan,'metadata':metadata}) == immutable_intake
             and all(pin_bytes(raw_sources[r]) == pin_bytes_record(plan['sources'][r]) for r in raw_sources),
             'same immutable plan/metadata and compiled raw Source buffers')
    guard_state=anchor(guard)
    def boundary():
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
                or same is not same_fn or same_fn.__code__ is not same_code
                or guard.__code__ is not guard_state[1] or not same_fn(guard,guard_state)):
            raise RuntimeError('original donor boundary caller changed')
        guard()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
                or same is not same_fn or same_fn.__code__ is not same_code
                or guard.__code__ is not guard_state[1] or not same_fn(guard,guard_state)):
            raise RuntimeError('original donor boundary changed after delegation')
    boundary_anchor=anchor(boundary)
    invoke_fn,invoke_code=invoke,invoke.__code__
    run=Path(plan['output_directory'])
    need(run.is_absolute() and run == run.resolve() and not run.exists(), 'fresh exclusive canonical output')
    run.mkdir(mode=0o700)
    # Every CALL below expands immediate original caller checks. The same
    # original callback is passed into the unchanged miner/word checker.
    # CALL: input read + exact own parser are guarded as whole bounded work.
    raw_inputs = {}
    for r,p in FIXED_INPUTS.items():
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed')
        raw_inputs[r] = invoke_fn(read_small,(p['path'], MAX_SMALL, p),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed after delegation')
    values={}
    for r,raw in raw_inputs.items():
        if r == 'searched_producer_response':
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
                raise RuntimeError('original immediate dispatch caller changed')
            values[r] = invoke_fn(historical_two_lines,(raw, 'Q-ordinary-producer-response-body-v1', 'Q-ordinary-producer-response-completion-v1'),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
                raise RuntimeError('original immediate dispatch caller changed after delegation')
        elif r == 'checked_verifier_response':
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
                raise RuntimeError('original immediate dispatch caller changed')
            values[r] = invoke_fn(historical_two_lines,(raw, 'Q-ordinary-clean-response-body-v1', 'Q-clean-verifier-response-completion-v1'),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
                raise RuntimeError('original immediate dispatch caller changed after delegation')
        else:
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
                raise RuntimeError('original immediate dispatch caller changed')
            values[r] = invoke_fn(decode,(raw, MAX_SMALL),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
                raise RuntimeError('original immediate dispatch caller changed after delegation')
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed')
    donor = invoke_fn(bind_historical,(values,),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed after delegation')
    donor_seal=digest(donor);origin_seal=digest(donor['origin'])
    context_seal=digest(donor['context']);commands_seal=digest(donor['commands'])
    def authenticate_donor(value):
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1] or not same_fn(boundary,boundary_anchor)):
            raise RuntimeError('owned callback immediate boundary changed')
        boundary()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1] or not same_fn(boundary,boundary_anchor)):
            raise RuntimeError('owned callback boundary changed after delegation')
        need(type(value) is dict and digest(value.get('origin')) == origin_seal,
             'admitted searched origin linkage')
        need(value is donor and digest(value) == donor_seal, 'exact private admitted donor identity and value')
        result={'schema':'ROOT-authenticated-searched-donor-v1','donor_id':donor['id'],
            'automatically_searched':True,'complete_original_target_return':True,
            'commands_sha256':commands_seal,'context_sha256':context_seal,'origin_sha256':origin_seal}
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1] or not same_fn(boundary,boundary_anchor)):
            raise RuntimeError('owned callback immediate boundary changed')
        boundary()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1] or not same_fn(boundary,boundary_anchor)):
            raise RuntimeError('owned callback boundary changed after delegation')
        return result
    def check_word(*,profile,context,commands,conclusion,primary):
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1] or not same_fn(boundary,boundary_anchor)):
            raise RuntimeError('owned callback immediate boundary changed')
        boundary()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1] or not same_fn(boundary,boundary_anchor)):
            raise RuntimeError('owned callback boundary changed after delegation')
        need(profile == donor['profile'] and context is donor['context'] and commands is donor['commands']
             and conclusion is donor['context']['target'] and primary is True
             and digest(donor) == donor_seal, 'only full private original closed-target donor word')
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed')
        (_,local_deadline) = invoke_fn(support.project_local_float_deadline,(end,),{'producer_pair':False},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed after delegation')
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed')
        result = invoke_fn(adapter.check_word,(),{'profile':profile,'context':context,'commands':commands,'conclusion':conclusion,'primary':True,'q_module':checker,'hilbert_checker_class':None,'source_guard':boundary,'local_deadline':local_deadline,'tick':boundary},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed after delegation')
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1] or not same_fn(boundary,boundary_anchor)):
            raise RuntimeError('owned callback immediate boundary changed')
        boundary()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1] or not same_fn(boundary,boundary_anchor)):
            raise RuntimeError('owned callback boundary changed after delegation')
        return result
    # No callback is recaptured/resealed after mutation. These callbacks close
    # only already fixed donor/data/endpoint objects. Mutable semantic caches
    # inside the unchanged checker remain its ordinary per-call implementation.
    auth_state,word_state=anchor(authenticate_donor),anchor(check_word)
    bad_origin=decode(canonical(donor),MAX_SMALL)
    bad_origin['origin']['producer_origin']['kind']='CONTROL_CORRUPT_ORIGIN'
    controls=[]
    try:
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed')
        unused = invoke_fn(authenticate_donor,(bad_origin,),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed after delegation')
    except ValueError as rejection:
        need(str(rejection) == 'admitted searched origin linkage', 'specific actual origin rejection')
        controls.append({'id':'corrupt-origin','rejected':True,'error':str(rejection),
            'corrupted_donor_sha256':digest(bad_origin),'unchanged_commands_sha256':commands_seal})
    else:raise ValueError('corrupt origin unexpectedly accepted')
    bad_commands=decode(canonical(donor['commands']),MAX_SMALL)
    axiom_indices=[i for i,c in enumerate(bad_commands) if c.get('rule') == 'axiom']
    need(axiom_indices, 'actual donor contains a corruptible original axiom, not a supplied proof fixture')
    bad_row=axiom_indices[0];bad_name='CONTROL_UNDECLARED'
    while bad_name in donor['context']['theory']['axioms']:bad_name+='X'
    need(len(bad_name)<=128, 'bounded derived undeclared label')
    bad_commands[bad_row]['name']=bad_name
    def reject_corrupt_word():
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1] or not same_fn(boundary,boundary_anchor)):
            raise RuntimeError('owned callback immediate boundary changed')
        boundary()
        if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code or boundary.__code__ is not boundary_anchor[1] or not same_fn(boundary,boundary_anchor)):
            raise RuntimeError('owned callback boundary changed after delegation')
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed')
        (_,local_deadline) = invoke_fn(support.project_local_float_deadline,(end,),{'producer_pair':False},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed after delegation')
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed')
        unexpected = invoke_fn(adapter.check_word,(),{'profile':donor['profile'],'context':donor['context'],'commands':bad_commands,'conclusion':donor['context']['target'],'primary':True,'q_module':checker,'hilbert_checker_class':None,'source_guard':boundary,'local_deadline':local_deadline,'tick':boundary},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed after delegation')
        return unexpected
    try:
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed')
        unused = invoke_fn(reject_corrupt_word,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed after delegation')
    except ValueError as rejection:
        need(str(rejection) == 'exact named original axiom', 'actual unchanged checker specific rejection')
        controls.append({'id':'corrupted-command','rejected':True,'error':str(rejection),
            'actual_source_row':bad_row,'corrupted_commands_sha256':digest(bad_commands),
            'original_commands_sha256':commands_seal,'original_target_unchanged':True})
    else:raise ValueError('corrupt command word unexpectedly accepted')
    # Both negative exceptions must still pass full Source and callback guards.
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed')
    unused = invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed after delegation')
    need(same_fn(authenticate_donor,auth_state) and same_fn(check_word,word_state), 'original owned callbacks')
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed')
    library = invoke_fn(family.mine_transport,([donor],),{'authenticate_donor': authenticate_donor, 'check_word': check_word, 'tick': boundary},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed after delegation')
    need(digest(donor) == donor_seal and same_fn(authenticate_donor,auth_state)
         and same_fn(check_word,word_state) and len(library['donor_census']) == len(donor['commands'])
         and [e['root'] for e in library['donor_census']] == list(range(len(donor['commands'])))
         and len(library['donor_checks']) == 1 and len(library['families']) <= 1,
         'complete all-root census and immutable donor; no expected eligible root/count')
    records={'donor.json':donor,'controls.json':controls,'mined-library.json':library,
        'intake-record.json':{'schema':'atomic-family-training-intake-record-v1','plan_sha256':hashlib.sha256(plan_raw).hexdigest(),
            'sources':plan['sources'],'inputs':FIXED_INPUTS,'metadata':metadata_records,
            'prior_training_launch_to_postprobe_ns':values['prior_ROOT_disposition']['native_launch_to_postprobe_ns'],
            'historical_origin_scope':'Root-admitted searched return, no independent saturation-history replay',
            'large_Q_files_read':False,'recipient_instances':0}}
    output_inventory=[]
    for name,value in records.items():
        raw=canonical(value)+b'\n';need(len(raw)<=RESPONSE_MAX, 'complete bounded output, no prefix')
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed')
        unused = invoke_fn(write_exclusive,(run / name, raw),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed after delegation')
        output_inventory.append(dict(pin_bytes(raw),path=name))
    body={'schema':'atomic-family-donor-training-response-body-v1','version':VERSION,
        'CLOCK_DOMAIN':CLOCK_DOMAIN,'invocation_id':plan['invocation_id'],'purpose':plan['purpose'],
        'joint_began_ns':began,'joint_deadline_ns':end,'plan':pin_bytes(plan_raw),
        'sources':plan['sources'],'inputs':FIXED_INPUTS,'resource_rule':plan['resource_rule'],'limits':LIMITS,
        'status':'COMPLETE_TRAINING_PENDING_EXTERNAL','complete_root_census':True,
        'root_count':len(library['donor_census']),'eligible_root_count':sum(e['reason']=='eligible' for e in library['donor_census']),
        'selected_family_count':len(library['families']),'controls':controls,'output_inventory':output_inventory,
        'prior_training_launch_to_postprobe_ns':values['prior_ROOT_disposition']['native_launch_to_postprobe_ns'],
        'fresh_original_closed_word_check_complete':True,'no_descendant_launch_in_fixed_Source':True,
        'ROOT_library_admitted':False,'ROOT_resource_accepted':False,'new_theorem_claimed':False,
        'recipient_accepted':False,'point_state_accepted':False,'full24_accepted':False,
        'trajectory_accepted':False,'native_accepted':False,'RL_accepted':False,'advantage_claimed':False}
    response_path=run/'response.jsonl';response_fd=regular_fd(response_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
    try:
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed')
        unused = invoke_fn(support.write_response,(response_fd, body, boundary),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
            raise RuntimeError('original immediate dispatch caller changed after delegation')
    finally:os.close(response_fd)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed')
    response_raw = invoke_fn(read_small,(str(response_path), RESPONSE_MAX + 1024),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed after delegation')
    # The exact unchanged writer completion schema is retained, not relabeled.
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed')
    rejoined = invoke_fn(historical_two_lines,(response_raw, 'atomic-family-donor-training-response-body-v1', 'Q-clean-verifier-response-completion-v1'),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed after delegation')
    need(rejoined == body, 'whole written response/EOF matches returned body')
    output_inventory.append(dict(pin_bytes(response_raw),path='response.jsonl'))
    need(sorted(p.name for p in run.iterdir()) == sorted(p['path'] for p in output_inventory), 'complete generated file inventory')
    final={'schema':'atomic-family-training-final-observation-v1','response':pin_bytes(response_raw),
        'output_inventory':output_inventory,'pending_external':True,'invocation_id':plan['invocation_id'],
        'ROOT_library_admitted':False,'ROOT_resource_accepted':False,'new_theorem_claimed':False}
    final_raw=canonical(final)+b'\n'
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed')
    unused = invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed after delegation')
    offset=0
    while offset<len(final_raw):
        count=os.write(1,final_raw[offset:]);need(count>0,'complete stdout');offset+=count
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed')
    unused = invoke_fn(boundary,(),{},boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code or invoke_fn.__defaults__ is not None or invoke_fn.__kwdefaults__ is not None or invoke_fn.__closure__ is not None or anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code or same is not same_fn or same_fn.__code__ is not same_code):
        raise RuntimeError('original immediate dispatch caller changed after delegation')
    # Native terminal meter T alone covers this single process including exit.
    # Direct captured exit skips interpreter finalizers/atexit, no later spawn.
    tick()
    if os._exit is not exit_fn or _NATIVE_EXIT is not exit_fn or clock(clock_id)>=end:
        raise TimeoutError('final poststdout original20 gate failed')
    exit_fn(0)


if __name__ == '__main__':
    try:
        main(sys.argv[1:],joint_began_ns=EARLY_BEGAN_NS)
    except BaseException as error:
        # Failure-only diagnostics never rescue an incomplete mining/check/wire.
        # A terminal exit2 or missing completion stays UNKNOWN at Root.
        try:
            if (_NATIVE_CLOCK_GETTIME_NS is time.clock_gettime_ns
                    and type(_NATIVE_CLOCK_ID) is int and time.CLOCK_MONOTONIC is _NATIVE_CLOCK_ID
                    and _NATIVE_CLOCK_GETTIME_NS(_NATIVE_CLOCK_ID) < EARLY_BEGAN_NS+55000000000):
                os.write(2,('ATOMIC_DONOR_UNKNOWN: '+type(error).__name__+': '+str(error)[:2048]+'\n').encode('utf8'))
        finally:_NATIVE_EXIT(2)
