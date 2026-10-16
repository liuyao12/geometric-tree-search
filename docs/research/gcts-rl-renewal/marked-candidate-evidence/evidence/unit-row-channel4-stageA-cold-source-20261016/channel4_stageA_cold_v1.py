"""Prospective first channel4 runtime qualification: degree/filter/cursor/EOF.
Current executable Source11 is distinct from the original semantic Source17.
No target search, graph/retention qualification, proof or activation.
"""
import time
CLOCK=time.clock_gettime_ns
CLOCK_ID=time.CLOCK_MONOTONIC
EARLY_G=CLOCK(CLOCK_ID)
import base64
import binascii
import zlib
import copy
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
import signal
import stat
import sys
import types
EXIT=os._exit
VERSION='unit-row-channel4-degree-cursor-cold-v1'
SCOPE='unit-row-channel4-stageA-cold-Source'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
CANCELLED=False
FIXED={'clean_support': {'bytes': 48584, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py', 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'}, 'kernel': {'bytes': 10323, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py', 'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'}, 'membership': {'bytes': 20112, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-implementation-source-20261015/bounded_six_rule_language_v2.py', 'sha256': '5d1fb647626c952f4653dd8cffabdb3fe29be0be122ef7e73ef4a7759da43332'}, 'proposer': {'bytes': 22030, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-degree-source-20261015/unit_row_missing_mark_degree_v3.py', 'sha256': 'c960e6e6560502f95f25611c9c85a72b32c67775aedc2e42e0300a366e3d7e90'}, 'degree_checker': {'bytes': 27553, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-checker-source-20261015/independent_unit_row_missing_mark_checker_v2.py', 'sha256': 'c35484000d8ab924d089ace9a185132ef164cad1e24729123290215b8baf8f6d'}, 'decorator': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-certified-mark-decorator-source-20261016/certified_row0_point_mark_decorator_v1.py', 'sha256': 'fcc4aeb3275f47cbdba26436e2224bffad91e80974e873d2d57d9263151a3895', 'bytes': 12619}, 'marked_verifier': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-state-verifier-source-20261016/independent_channel4_state_verifier_v1.py', 'sha256': '9fd60cad12881e3519c785c417b3348bd013a5ff0b8aa993399276e266da9a6a', 'bytes': 18475}, 'marked_adapter': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-engine-source-20261016/marked_unit_row_adapter_v1.py', 'sha256': '821fe692dc7a118cdc3355d3128ecdf08287abf229365b97a04341e0dc4cb7f9', 'bytes': 28980}, 'engine': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-engine-source-20261016/lazy_unit_row_global_engine_v11.py', 'sha256': 'fbd1455fbcb090045ae2a6ad151e4a5ae41d01e1549be135e8b8d7b64f597476', 'bytes': 56207}, 'fallback': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-all-six-fallback-source-20261015/unit_row_all_six_fallback_v1.py', 'sha256': '69b4a9170d931e01138f5d7f98514f26e47cbfe7ab8b7503b99f6a24934a4fae', 'bytes': 24227}}
FIXED_INPUTS={'marking_disposition': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-certified-marking-ROOT-20261016/ROOT-marking-disposition-v1.json', 'sha256': '46a04787501db397fc9993118ebd5800a301ddc7898398a386438a905a415f77', 'bytes': 5271}, 'marking_plan': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-certified-marking-ROOT-20261016/ROOT-marking-plan-v1.json', 'sha256': '32c2b9e377b3ebbc353ac17b1dd808fb5b85a5ab21a456d97fddee63ae0e2240', 'bytes': 7353}, 'marking_transport': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-certified-marking-ROOT-20261016/ROOT-marking-transport-concordance-v1.json', 'sha256': 'ef50dd4c265bc843ebda31174948abbbb9fb67e68bf800acddfdd2ca6d00c7f1', 'bytes': 1466}, 'marking_expanded': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-certified-marking-ROOT-20261016/ROOT-marking-expanded-result-v1.json', 'sha256': 'db4c457fb03d10787d2fea4061dd134868c0154ecd86a8e82322e61fbdd00cba', 'bytes': 502708}, 'marking_encoded': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-certified-marking-ROOT-20261016/marking-owned-v1/engine-result.json', 'sha256': '6c20a05df94f985d3e5ab4052af75aee155a10cab5ab90a927825cefa61e1b63', 'bytes': 46337}, 'marking_response': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-certified-marking-ROOT-20261016/marking-owned-v1/response.jsonl', 'sha256': '8099df1a00f8395c5d7cd026ba942723b59149cfc5a679f146c352fb1ffc5aca', 'bytes': 7079}, 'declaration': {'bytes': 2925, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-right-two-preparation-source-20261015/Q-right-two-declaration-v1.json', 'sha256': 'a1ce8237aca64485f94cbce0c909a055a74318ca0cc39b99cf0dc1990323d3df'}, 'profile': {'bytes': 8773, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-ROOT-20261015/ROOT-profile-choice-v2.json', 'sha256': '227b3d4c1e8f5491365b5da580f59367300840d43d388d94e0657cf1b5f89c02'}}
LIMITS={'aggregate_owned_bytes': 536870912, 'caller_finish_reserve_seconds': 1, 'caller_seconds': 90, 'failure_only_seconds': 55, 'joint_seconds': 20, 'owned_seconds': 60}

ORIGINAL_SOURCES={'advice_controls': {'bytes': 130156, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-selective-C-controls-source-20261016/compatible_fibres_controls_v11.py', 'sha256': '0790868b3dfda92e55e9f0acdda674bb0abd0853e13eef7008d66ab16f5c09e3'}, 'advice_validator': {'bytes': 16299, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-compatible-fibres-consumer-source-20261016/independent_advice_consumer_v3.py', 'sha256': '8116e9104a7bf431b2efefd08b38ebb607a0884d9ccf893626647edf9f37eca1'}, 'adviser': {'bytes': 26007, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-compatible-fibres-adviser-source-20261016/goal_branch_adviser_v3.py', 'sha256': '6b1a8b24509d8379b9f3747494810f9721481b0d692c7e144f8bc8c389d31e98'}, 'clean_support': {'bytes': 48584, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py', 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'}, 'controls': {'bytes': 31931, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marking-aware-controls-source-20261016/marking_aware_adversarial_controls_v2.py', 'sha256': '50faf07d85de3be6aa6f822f94f6d82f7fd6d103e60c2d96cb0c54cbb4f8567a'}, 'converter': {'bytes': 5528, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-point-board-source-20261015/word_to_point_board_v1.py', 'sha256': 'baefa732406c20087304643b16e812f0f1e4e0a62513f5069c6f30ba7f7b1e63'}, 'degree_checker': {'bytes': 27553, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-checker-source-20261015/independent_unit_row_missing_mark_checker_v2.py', 'sha256': 'c35484000d8ab924d089ace9a185132ef164cad1e24729123290215b8baf8f6d'}, 'engine': {'bytes': 55152, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marking-aware-engine-source-20261016/lazy_unit_row_global_engine_v9.py', 'sha256': '54983466d2530ea56d8eb43704b9036966c9325caf8a7179f65a47a7780ed146'}, 'fallback': {'bytes': 24227, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-all-six-fallback-source-20261015/unit_row_all_six_fallback_v1.py', 'sha256': '69b4a9170d931e01138f5d7f98514f26e47cbfe7ab8b7503b99f6a24934a4fae'}, 'intake': {'bytes': 55852, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-frontier-cold-ROOT-source-20261016/unit_row_marked_frontier_cold_v17.py', 'sha256': '652434adfb1951594b56689ebfece1a0fce3c1d40ad4a6338c58fa108cce51e5'}, 'kernel': {'bytes': 10323, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py', 'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'}, 'membership': {'bytes': 20112, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-implementation-source-20261015/bounded_six_rule_language_v2.py', 'sha256': '5d1fb647626c952f4653dd8cffabdb3fe29be0be122ef7e73ef4a7759da43332'}, 'point_checker': {'bytes': 10201, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-point-board-independent-source-20261015/independent_word_point_board_checker_v1.py', 'sha256': '99b3bdc393d4fbdc4bddf08b362ca58c80a06a129908e854b0303e495303c18d'}, 'proposer': {'bytes': 22030, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-degree-source-20261015/unit_row_missing_mark_degree_v3.py', 'sha256': 'c960e6e6560502f95f25611c9c85a72b32c67775aedc2e42e0300a366e3d7e90'}, 'retained_controls': {'bytes': 25338, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-retained-domain-controls-source-20261015/retained_domain_controls_v2.py', 'sha256': 'd1dcdfa9230ab1653c601ee2d769c64722d9ab0d0f292682bda214d8984488eb'}, 'transition': {'bytes': 8134, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-retained-domain-engine-source-20261015/unit_row_domain_transition_checker_v1.py', 'sha256': '2e2d66c3c5843ef086f073df09e2eda7a50d3972fa1900a8ecf33f5c92ab3491'}, 'word_checker': {'bytes': 46514, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-mathematical-audit-source-20261014/independent_Q_semantics_v1.py', 'sha256': '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3'}}
ORIGINAL_INPUTS={'declaration': {'bytes': 2925, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-right-two-preparation-source-20261015/Q-right-two-declaration-v1.json', 'sha256': 'a1ce8237aca64485f94cbce0c909a055a74318ca0cc39b99cf0dc1990323d3df'}, 'profile': {'bytes': 8773, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-ROOT-20261015/ROOT-profile-choice-v2.json', 'sha256': '227b3d4c1e8f5491365b5da580f59367300840d43d388d94e0657cf1b5f89c02'}}
ORIGINAL_BINDING={'declaration_sha256': 'a1ce8237aca64485f94cbce0c909a055a74318ca0cc39b99cf0dc1990323d3df', 'language_epoch': '382755b37139c6b57e694251f529a128003b50f518f2204535b3d8014cf9b11b', 'logical_input_sha256': '959249f6ccc68a57589402df5555202daddb5bfb73f05a7b52baa4e4d5712b57', 'profile_name': 'shared-bounded-six-rule-B12-N44-v2', 'profile_sha256': '227b3d4c1e8f5491365b5da580f59367300840d43d388d94e0657cf1b5f89c02', 'source_bindings_sha256': '977edd4149a2260e1babdc5096a18e32431810c1fa9573b0ee4eca4c0751c662'}

def need(value,message):
    if not value:raise ValueError(message)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

def raw_pin(raw):return {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

def unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result,'duplicate JSON key');result[key]=value
    return result

def reject_constant(value):raise ValueError('nonfinite JSON constant')

def finite_float(value):
    result=float(value);need(math.isfinite(result),'finite diagnostic float');return result

def decode(raw):
    return json.loads(raw,object_pairs_hook=unique,parse_float=finite_float,parse_constant=reject_constant)

def read_pinned(ref,cap=1048576):
    p=Path(ref['path']);need(p.is_absolute() and p==p.resolve(),'canonical current input')
    fd=os.open(str(p),os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd);need(stat.S_ISREG(info.st_mode) and info.st_size==ref['bytes']<=cap,'complete regular bounded input')
        blocks=[];total=0
        while True:
            block=os.read(fd,65536)
            if not block:break
            blocks.append(block);total+=len(block);need(total<=cap,'no truncated input')
        raw=b''.join(blocks)
        need(raw_pin(raw)=={k:ref[k] for k in ('sha256','bytes')},'whole current raw input SHA/EOF')
        return raw
    finally:os.close(fd)

def load_module(role,raw):
    name='_right_two_independent_'+role;need(name not in sys.modules,'fresh private module')
    module=types.ModuleType(name);module.__file__='<authenticated-'+role+'>'
    sys.modules[name]=module;exec(compile(raw,module.__file__,'exec'),module.__dict__)
    return module

def write_new(path,raw):
    fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        offset=0
        while offset<len(raw):
            n=os.write(fd,raw[offset:offset+65536]);need(n>0,'whole owned output');offset+=n
    finally:os.close(fd)
    return dict(raw_pin(raw),path=str(path))

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

def cancel(signum,frame):
    global CANCELLED
    CANCELLED=True

def all_function_anchors(modules):
    """Strong refs and identity tokens supplement unchanged CodeSeal snapshots."""
    functions=[];seen=set()
    def retain(fn):
        if type(fn) is types.FunctionType and id(fn) not in seen:
            seen.add(id(fn));functions.append((fn,anchor(fn)))
    for module in modules:
        for value in vars(module).values():
            if type(value) is types.FunctionType and value.__module__==module.__name__:retain(value)
            elif isinstance(value,type) and value.__module__==module.__name__:
                for base in value.__mro__:
                    for member in vars(base).values():
                        if isinstance(member,(staticmethod,classmethod)):member=member.__func__
                        if type(member) is property:
                            for fn in (member.fget,member.fset,member.fdel):retain(fn)
                        else:retain(member)
    return tuple(functions)

def save_failure_diagnostic(output_path, context_raw, capture, failure_kind, began_ns, *,
        _clock=CLOCK, _clock_id=CLOCK_ID, _usage=resource.getrusage, _self_id=resource.RUSAGE_SELF,
        _open=os.open, _mkdir=os.mkdir, _write=os.write, _close=os.close,
        _escape=json.encoder.encode_basestring_ascii, _hash=hashlib.sha256,
        _flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW):
    """Best-effort raw builtin data ONLY. No late authority or scientific calls.

    This helper never supplies a positive result. A complete two-file diagnostic
    still requires Root's separate terminal/failure-window reconciliation.
    """
    def failure_gate():
        # Captured native endpoints; no original20 Source callback is invoked.
        peak = _usage(_self_id).ru_maxrss
        now = _clock(_clock_id)
        if (type(_clock) is not types.BuiltinFunctionType or type(_clock_id) is not int
                or type(_escape) is not types.BuiltinFunctionType
                or peak >= 524288000 or not began_ns <= now < began_ns+55000000000):
            raise TimeoutError('failure-only diagnostic window/resource unfinished')
        return now
    def encoded(value, maximum):
        # Exact builtin containers only: no arbitrary iterator/property/default
        # hook, repr, __str__, or project encoder can execute on this path.
        chunks = []; size = 0; nodes = 0
        def append(raw):
            nonlocal size
            size += len(raw)
            if size > maximum: raise ValueError('diagnostic byte bound')
            chunks.append(raw)
        def visit(item, depth):
            nonlocal nodes
            nodes += 1
            if nodes > 200000 or depth > 128: raise ValueError('diagnostic structure bound')
            if nodes % 64 == 1: failure_gate()
            kind = type(item)
            if item is None: append(b'null')
            elif kind is bool: append(b'true' if item else b'false')
            elif kind is int:
                if item.bit_length() > 4096: raise ValueError('diagnostic integer bound')
                append(str(item).encode('ascii'))
            elif kind is str:
                if len(item) > 262144: raise ValueError('diagnostic string bound')
                append(_escape(item).encode('ascii'))
            elif kind is list or kind is dict:
                append(b'[' if kind is list else b'{')
                for index, entry in enumerate(item if kind is list else item.items()):
                    if index: append(b',')
                    if kind is dict:
                        key, child = entry
                        if type(key) is not str: raise ValueError('diagnostic string key required')
                        visit(key, depth+1); append(b':'); visit(child, depth+1)
                    else: visit(entry, depth+1)
                append(b']' if kind is list else b'}')
            else: raise ValueError('non-builtin diagnostic value')
        visit(value, 0); failure_gate()
        return b''.join(chunks)
    failure_gate()
    # context_raw was encoded before the untrusted search delegation.
    if type(context_raw) is not bytes or len(context_raw) > 65536:
        raise ValueError('bounded predelegation diagnostic context')
    if failure_kind == 'CONTROLS_TIMEOUT_LAST_SCALARS':
        roles = ('proposer','fallback','completion','validator')
        if type(capture) is not dict or not all(type(key) is str for key in capture) or set(capture) != set(roles):
            raise ValueError('fixed builtin last-context slots')
        observations = {}
        for role in roles:
            item = capture[role]
            if item is None:
                observations[role] = None
                continue
            if type(item) is not tuple or len(item) != 4:
                raise ValueError('fixed scalar last-context tuple')
            stage,row,selected,native_ns = item
            if (type(stage) is not str or stage != role.upper()+'_NATIVE_STEP'
                    or type(row) is not int or not -1<=row<24
                    or type(selected) is not int or not -1<=selected<=24
                    or type(native_ns) is not int or not began_ns<=native_ns<began_ns+20000000000
                    or not 0<=native_ns<=9223372036854775807):
                raise ValueError('bounded builtin last-context fields')
            observations[role] = {'stage':stage,'row':row,'selected_count':selected,'native_ns':native_ns}
        labels = encoded({'schema':'unit-row-controls-last-context-diagnostic-v1',
            'diagnostic_only':True,'qualification':'UNQUALIFIED_LAST_ADAPTER_NATIVE_OBSERVATIONS',
            'failure_kind':'TimeoutError','returned_control_record':False,
            'callback_context':'ENTRY_ARGUMENT_ROW_AND_SELECTED_COUNT_AT_LAST_SUCCESSFUL_EXISTING_NATIVE_CHECK',
            'last_observation_is_active_failure_frame':False,'live_state_or_proof_trajectory_accepted':False,
            'positive_joint_gate_accepted':False,'logical_proof_accepted':False,
            'exact_point_board_accepted':False,'complete_GCTS_model_accepted':False,
            'GCTS_search_trajectory_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False},4096)
        raw = b'{"context":'+context_raw+b',"diagnostic":'+labels+b',"last_observations":'+encoded(observations,4096)+b'}\n'
        if len(raw)>16384:raise ValueError('whole controls-context diagnostic16KiB bound')
    else:
        available = capture['returned'] is True
        value = capture['payload'] if available else None
        metadata = None; metadata_saved = False; total_events = None; event_raw = []
        prefix_reason = 'NO_RETURNED_RECORD'; metadata_reason = None
        if type(value) is dict and all(type(key) is str for key in value):
            try:
                metadata = encoded({key: item for key,item in value.items() if key != 'events'}, 1048576)
                metadata_saved = True
            except ValueError:
                metadata_reason = 'BUILTIN_METADATA_OUTPUT_BOUND_OR_TYPE'
            events = value.get('events')
            if type(events) is list:
                total_events = len(events); used = 0; prefix_reason = 'ALL_RETURNED_EVENTS_SAVED'
                for event in events:
                    if len(event_raw) >= 2000:
                        prefix_reason = 'DIAGNOSTIC_EVENT_PREFIX_LIMIT'; break
                    try: raw = encoded(event, 262144)
                    except ValueError:
                        prefix_reason = 'NEXT_EVENT_OUTPUT_BOUND_OR_TYPE'; break
                    if used+len(raw)+1 > 3*1048576:
                        prefix_reason = 'DIAGNOSTIC_EVENT_BYTE_LIMIT'; break
                    event_raw.append(raw); used += len(raw)+1
            else: prefix_reason = 'RETURNED_EVENTS_NOT_BUILTIN_LIST'
        elif available: metadata_reason = 'RETURNED_VALUE_NOT_BUILTIN_STRING_KEY_DICT'
        # These labels are caller observations, never claims trusted from the payload.
        labels = encoded({'schema':'unit-row-search-failure-diagnostic-v1',
            'diagnostic_only':True,'qualification':'UNQUALIFIED_UNKNOWN_RAW_PREFIX',
            'capture_available':available,'capture_is_builtin_dict':type(value) is dict,
            'engine_return_observed_ns':capture['returned_ns'], 'failure_kind':failure_kind,
            'metadata_saved':metadata_saved,'metadata_omission_reason':metadata_reason,
            'returned_event_count':total_events,'saved_event_count':len(event_raw),
            'omitted_event_count':None if total_events is None else total_events-len(event_raw),
            'event_prefix_reason':prefix_reason,'may_include_post_deadline_unwind':True,
            'positive_joint_gate_accepted':False,'logical_proof_accepted':False,
            'exact_point_board_accepted':False,'complete_GCTS_model_accepted':False,
            'GCTS_search_trajectory_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False}, 65536)
        raw = (b'{"context":'+context_raw+b',"diagnostic":'+labels+b',"returned_metadata":'
               +(metadata if metadata_saved else b'null')+b',"events_prefix":['
               +b','.join(event_raw)+b']}\n')
    if len(raw) > 4*1048576+131072: raise ValueError('whole diagnostic output bound')
    def write(name, content):
        failure_gate()
        fd = _open(output_path+'/'+name, _flags, 0o600)
        try:
            offset = 0
            while offset < len(content):
                failure_gate()
                count = _write(fd,content[offset:offset+65536])
                if count <= 0: raise OSError('diagnostic output unfinished')
                offset += count
        finally: _close(fd)
        failure_gate()
    failure_gate(); _mkdir(output_path, 0o700)
    write('unknown-diagnostic.json',raw)
    marker = encoded({'schema':('unit-row-controls-last-context-completion-v1' if failure_kind == 'CONTROLS_TIMEOUT_LAST_SCALARS' else 'unit-row-search-failure-diagnostic-completion-v1'),
        'file':'unknown-diagnostic.json','sha256':_hash(raw).hexdigest(),'bytes':len(raw),
        'diagnostic_only':True,'positive_joint_gate_accepted':False,
        'ROOT_resource_accepted':False,'terminal_exit2_and_external_failure_closure_required':True}, 1024)+b'\n'
    write('diagnostic-completion.json',marker)
    failure_gate()

def encode_result_transport(expanded_raw):
    """Lossless transport only; caller invoke charges original20 pre/post gates."""
    need(type(expanded_raw) is bytes and len(expanded_raw) <= 16*1048576,
         'whole expanded lossless result output cap')
    compressed = zlib.compress(expanded_raw, 6)
    envelope = {'schema':'ROOT-unit-row-lossless-result-envelope-v1',
        'encoding':'zlib+base64', 'expanded_bytes':len(expanded_raw),
        'expanded_sha256':hashlib.sha256(expanded_raw).hexdigest(),
        'compressed_bytes':len(compressed),
        'compressed_sha256':hashlib.sha256(compressed).hexdigest(),
        'payload_base64':base64.b64encode(compressed).decode('ascii')}
    encoded = canonical(envelope) + b'\n'
    need(len(encoded) <= 4*1048576, 'whole encoded lossless result output cap')
    return encoded


def main(argv):
    need(__name__=='__main__' and len(argv)==1,'one Root certified-marking data plan')
    end=EARLY_G+20000000000
    usage,self_id,clock,clock_id,exit_fn=resource.getrusage,resource.RUSAGE_SELF,CLOCK,CLOCK_ID,EXIT
    def tick():
        if (time.clock_gettime_ns is not clock or time.CLOCK_MONOTONIC is not clock_id
                or type(clock_id) is not int or type(clock) is not types.BuiltinFunctionType
                or resource.getrusage is not usage or resource.RUSAGE_SELF is not self_id
                or os._exit is not exit_fn or EXIT is not exit_fn):
            raise RuntimeError('original native clock/resource/exit endpoints changed')
        peak=usage(self_id).ru_maxrss;now=clock(clock_id)
        if CANCELLED or not EARLY_G<=now<end or peak>=524288000:
            raise TimeoutError('complete marking data controls original20/500 reserve unfinished')
        return now
    tick();signal.signal(signal.SIGINT,cancel);signal.signal(signal.SIGTERM,cancel)
    path=Path(argv[0]);need(path.is_absolute() and path==path.resolve(),'canonical Root plan path')
    plan_raw=path.read_bytes();need(len(plan_raw)<=1048576,'whole bounded Root plan');plan=decode(plan_raw)
    need(set(plan)=={'schema','invocation_id','purpose','output_directory','sources','inputs','source_contract',
        'reviews','ROOT_authorization','runtime','limits','resource_rule'},'exact current plan12')
    need(plan['schema']=='ROOT-channel4-stageA-plan-v1'
         and plan['purpose']=='unit-row-channel4-degree-cursor-controls'
         and plan['resource_rule']=='single-owned-process-native-terminal-v1'
         and plan['limits']==LIMITS and all(type(v) is int for v in plan['limits'].values()),'original six limits')
    need(type(plan['invocation_id']) is str and 1<=len(plan['invocation_id'])<=128
         and all(c.isascii() and (c.isalnum() or c in '-_.:') for c in plan['invocation_id']),'strict actual nonce')
    need(set(plan['sources'])=={'intake',*FIXED}
         and all(plan['sources'][k]==v for k,v in FIXED.items())
         and plan['sources']['intake']['path']==str(Path(__file__).resolve())
         and plan['inputs']==FIXED_INPUTS,'exact current executable Source11 and saved input8')
    need(sys.platform=='darwin' and Path(sys.executable).resolve()==Path(plan['runtime']['path']).resolve(),'native Darwin runtime')
    read_pinned(plan['runtime'])
    source_raw={role:read_pinned(ref) for role,ref in plan['sources'].items()}
    contract=decode(read_pinned(plan['source_contract']))
    need(contract['schema']=='unit-row-channel4-stageA-cold-Source-contract-v1'
         and contract['sources']==plan['sources'] and contract['inputs']==FIXED_INPUTS
         and contract['limits']==LIMITS and contract['original_model_sources']==ORIGINAL_SOURCES
         and contract['original_model_inputs']==ORIGINAL_INPUTS
         and contract['original_model_binding']==ORIGINAL_BINDING,'whole current and original-model contract')
    need(set(plan['reviews'])=={'ROOT','peer'},'Root review and distinct whole-Source peer')
    for role,ref in plan['reviews'].items():
        review=decode(read_pinned(ref))
        need(review['scope']==SCOPE and review['author_identity']=='/root/arithmetic_induction'
             and review['source']==plan['sources']['intake'] and review['sources']==plan['sources']
             and review['source_contract']==plan['source_contract'] and review['source_only'] is True
             and review['source_review_passed'] is True and type(review['scientific_calls']) is int
             and review['scientific_calls']==0 and review['scientific_acceptance'] is False
             and (review['reviewer_identity']=='/root' if role=='ROOT' else review['reviewer_identity'] not in ('/root/arithmetic_induction','/root')),
             'genuine current scoped Source reviews')
    grant=decode(read_pinned(plan['ROOT_authorization']))
    need(grant['schema']=='ROOT-channel4-stageA-authorization-v1'
         and grant['author_identity']=='/root' and grant['actual_execution_authorized'] is True
         and type(grant['maximum_actual_invocations']) is int and grant['maximum_actual_invocations']==1
         and all(grant[k]==plan[k] for k in ('invocation_id','purpose','sources','inputs','source_contract',
             'reviews','runtime','limits','resource_rule','output_directory')),'exact once-only Root actual grant')
    inputs_raw={role:read_pinned(ref,4*1048576+131072) for role,ref in FIXED_INPUTS.items()}
    original_raw={role:read_pinned(ref) for role,ref in ORIGINAL_SOURCES.items()}
    for role in ('clean_support','kernel','membership','proposer','degree_checker','fallback'):
        need(FIXED[role]==ORIGINAL_SOURCES[role] and source_raw[role]==original_raw[role],
             'current delegated mathematical role raw-identical to original model')
    declaration_raw,profile_raw=inputs_raw['declaration'],inputs_raw['profile']
    need(FIXED_INPUTS['declaration']==ORIGINAL_INPUTS['declaration'] and FIXED_INPUTS['profile']==ORIGINAL_INPUTS['profile'],
         'same original raw input2')
    authority_raw=canonical({'declaration':decode(declaration_raw),'policy':decode(profile_raw),
        'source_bindings':ORIGINAL_SOURCES,'binding':ORIGINAL_BINDING})
    original_context_raw=canonical({'sources':ORIGINAL_SOURCES,'binding':ORIGINAL_BINDING,'inputs':ORIGINAL_INPUTS,'accepted_inputs':FIXED_INPUTS})
    modules={role:load_module(role,source_raw[role]) for role in FIXED}
    support,kernel,membership,semantics=(modules[k] for k in ('clean_support','kernel','membership','degree_checker'))
    decoder=json.JSONDecoder(object_pairs_hook=unique,parse_float=finite_float,parse_constant=reject_constant)
    sealed_modules=(sys.modules[__name__],*modules.values(),json,json.decoder,json.encoder,json.scanner,
        copy,hashlib,itertools,math,os,resource,signal,stat,sys,time,types,base64,binascii,zlib)
    seal=support.CodeSeal(sealed_modules,decoder,end)
    plan_raw_value=canonical(plan)
    anchor_fn,anchor_code,same_fn,same_code=anchor,anchor.__code__,same,same.__code__
    tick_state=anchor_fn(tick);method,method_fn=seal.check,support.CodeSeal.check;method_state=anchor_fn(method_fn)
    strong_functions=all_function_anchors(sealed_modules)
    def guard():
        for phase in (0,1):
            if (anchor is not anchor_fn or anchor_fn.__code__ is not anchor_code
                    or same is not same_fn or same_fn.__code__ is not same_code
                    or support.CodeSeal.check is not method_fn or not same_fn(method_fn,method_state)
                    or method.__self__ is not seal or method.__func__ is not method_fn
                    or not same_fn(tick,tick_state)):
                raise RuntimeError('original complete Source/native guard changed')
            tick()
            if phase==0:method()
            if any(not same_fn(fn,state) for fn,state in strong_functions):
                raise RuntimeError('original Source code/defaults/cells changed')
        need(canonical(plan)==plan_raw_value and canonical({'sources':ORIGINAL_SOURCES,'binding':ORIGINAL_BINDING,
             'inputs':ORIGINAL_INPUTS,'accepted_inputs':FIXED_INPUTS})==original_context_raw,'current plan and private original authority unchanged')
    guard_state=anchor_fn(guard)
    def boundary():
        if not same_fn(guard,guard_state):raise RuntimeError('original immediate boundary guard changed')
        guard()
        if not same_fn(guard,guard_state):raise RuntimeError('original immediate boundary guard changed on return')
    boundary_anchor=anchor_fn(boundary);invoke_fn,invoke_code=invoke,invoke.__code__
    def call(fn,args=(),kwargs=None):
        return invoke_fn(fn,args,{} if kwargs is None else kwargs,boundary,boundary_anchor,anchor_fn,anchor_code,same_fn,same_code)
    local_deadline=call(support.project_local_float_deadline,(end,),{'producer_pair':False})[1]
    def fresh_language():
        d,p=read_pinned(ORIGINAL_INPUTS['declaration']),read_pinned(ORIGINAL_INPUTS['profile'])
        need(d==declaration_raw and p==profile_raw,'whole original authority input bytes')
        language=call(membership.make_language,kwargs={'declaration_raw':d,
            'expected_declaration_sha256':ORIGINAL_INPUTS['declaration']['sha256'],'profile_raw':p,
            'source_bindings':copy.deepcopy(ORIGINAL_SOURCES),'kernel_module':kernel,'local_deadline':local_deadline,'tick':tick})
        need(canonical(language.binding)==canonical(ORIGINAL_BINDING),'exact original model epoch without rebasing')
        return language
    # Authenticate the WHOLE prior construction result. Its receipts are inputs,
    # never substituted for the fresh checks in this current native window.
    accepted = decode(inputs_raw['marking_disposition'])
    prior = decode(inputs_raw['marking_plan'])
    transport = decode(inputs_raw['marking_transport'])
    expanded = decode(inputs_raw['marking_expanded'])
    need(accepted['schema'] == 'ROOT-certified-row0-marking-disposition-v1'
         and accepted['actual_closed'] is True and accepted['all_reaped'] is True
         and accepted['native_resources_qualified'] is True and accepted['complete_wire_verified'] is True
         and accepted['constructed_marking_data_accepted'] is True
         and accepted['independent_marking_data_check_accepted'] is True
         and accepted['passed_cases'] == 16 and accepted['skipped_cases'] == 0,
         'fixed prior Root acceptance of constructed marking data only')
    need(accepted['plan'] == FIXED_INPUTS['marking_plan']
         and accepted['lossless_transport_concordance'] == FIXED_INPUTS['marking_transport']
         and accepted['outputs'] == [FIXED_INPUTS['marking_encoded'], FIXED_INPUTS['marking_response']]
         and transport['plan'] == FIXED_INPUTS['marking_plan']
         and transport['encoded_file'] == FIXED_INPUTS['marking_encoded']
         and transport['expanded_file'] == FIXED_INPUTS['marking_expanded']
         and transport['all_full_record_bytes_retained'] is True,
         'prior marking disposition/plan/transport/full output joins')
    need(canonical(expanded)+b'\n' == inputs_raw['marking_expanded']
         and expanded['sources'] == prior['sources'] and expanded['inputs'] == prior['inputs']
         and expanded['purpose'] == prior['purpose'] == 'unit-row-certified-row0-marking-data-controls'
         and expanded['language_binding'] == accepted['original_model_binding'] == ORIGINAL_BINDING,
         'accepted canonical whole result and original semantic epoch')
    old_contract = decode(read_pinned(prior['source_contract']))
    need(old_contract['sources'] == prior['sources'] and old_contract['inputs'] == prior['inputs']
         and old_contract['original_model_sources'] == ORIGINAL_SOURCES
         and old_contract['original_model_binding'] == ORIGINAL_BINDING, 'prior Source9 versus original Model17')
    for ref in prior['sources'].values(): read_pinned(ref)
    for ref in prior['inputs'].values(): read_pinned(ref,4*1048576+131072)
    old_grant = decode(read_pinned(prior['ROOT_authorization']))
    need(old_grant['author_identity'] == '/root' and old_grant['actual_execution_authorized'] is True
         and old_grant['maximum_actual_invocations'] == 1
         and all(old_grant[k] == prior[k] for k in ('invocation_id','purpose','sources','inputs',
            'source_contract','reviews','runtime','limits','resource_rule','output_directory')),
         'prior Root once grant provenance only')
    for ref in prior['reviews'].values():
        review = decode(read_pinned(ref))
        need(review['source'] == prior['sources']['intake'] and review['sources'] == prior['sources']
             and review['source_contract'] == prior['source_contract'] and review['source_only'] is True
             and review['source_review_passed'] is True, 'prior complete Source review provenance')
    lines = inputs_raw['marking_response'].splitlines(keepends=True)
    need(len(lines) == 2 and all(v.endswith(b'\n') for v in lines), 'prior response exactly twoLF')
    old_body, old_completion = map(decode,lines)
    need(old_completion['body_sha256'] == hashlib.sha256(lines[0]).hexdigest()
         and old_completion['body_bytes'] == len(lines[0])
         and old_body['plan'] == raw_pin(inputs_raw['marking_plan'])
         and old_body['sources'] == prior['sources'] and old_body['inputs'] == prior['inputs']
         and old_body['outputs'] == [FIXED_INPUTS['marking_encoded']], 'prior complete response bytes')
    previous = expanded['marking_data']
    need(previous['schema'] == 'ROOT-certified-row0-marking-data-payload-v1'
         and previous['original_model_sources'] == ORIGINAL_SOURCES
         and previous['original_model_binding'] == ORIGINAL_BINDING
         and previous['control_count'] == 16 and len(previous['controls']) == 16
         and previous['all_controls_completed'] is True
         and all(c['status'] == 'PASSED' for c in previous['controls'])
         and all(accepted[k] is False for k in ('engine_activated','target_search_performed',
            'logical_proof_accepted','complete_GCTS_model_accepted','RL_accepted','GCTS_advantage_claimed')),
         'prior narrow marking-data acceptance, no engine activation')
    marking = copy.deepcopy(previous['marking'])
    need(marking['marking_id'] == accepted['marking_id']
         and hashlib.sha256(canonical(marking)).hexdigest() == accepted['marking_sha256'],
         'whole accepted frozen marking identity')
    adapter, engine, fallback = (modules[k] for k in ('marked_adapter','engine','fallback'))
    decorator, verifier = modules['decorator'], modules['marked_verifier']
    need(engine.VERSION == 'lazy-unit-row-global-engine-v11-channel4-global-original-key-collision'
         and adapter.VERSION == 'unit-row-channel4-point-adapter-v1', 'current reviewed engine/adapter versions')
    definition_check = call(verifier.check_marking,kwargs={'language':fresh_language(),
        'semantics':semantics,'marking':copy.deepcopy(marking),'tick':tick})
    need(definition_check['marking_checked'] is True and definition_check['marking_id'] == marking['marking_id'],
         'fresh independent whole marking check')
    controls, fixtures, cursors = [], {}, {}

    def passed(name, **data):
        tick(); controls.append(dict(case=name,status='PASSED',**data))

    def negative(name, fn, exact_reason):
        reason = None
        try: call(fn)
        except ValueError as error:
            if type(error) is not ValueError: raise
            reason = str(error)
        need(reason == exact_reason,'exact negative, no swallowed authority/resource failure')
        passed(name,reason=reason)

    def marked_semantics(language, endpoint_tick=None):
        return adapter.MarkedSemantics(language=language,base_semantics=semantics,
            decorator=decorator,verifier=verifier,marking=copy.deepcopy(marking),
            tick=tick if endpoint_tick is None else endpoint_tick)

    def root_state(language):
        epoch = ORIGINAL_BINDING['language_epoch']
        return {'schema':'unit-row-implicit-private-state-v1','input_epoch':epoch,'height':24,
            't':[[[0,r],0] for r in range(24)],
            'm':[[[1,k],['outside',epoch]] for k in range(-23,0)]
                + [[[1,23],['formula',canonical(language.target).decode('utf8')]]],
            'selected':[],'excluded':[],'generation':[[[0,r],0] for r in range(24)]}

    def tile(witness, premises, reads, row):
        pre = {'input_epoch':ORIGINAL_BINDING['language_epoch'],'primitive_witness':copy.deepcopy(witness),
            'ordered_premise_formulas':copy.deepcopy(premises),'ordered_offsets':[k-row for k in reads]}
        return semantics.rebuild_tile(fresh_language(),pre,[0,row],tick)

    def state_from(tiles, excluded=None):
        language = fresh_language(); state = root_state(language)
        for offered in tiles:
            _,totals,marks,selected,exclusions,names = semantics.private_state(language,state,tick)
            key = offered['placement_key']
            rebuilt = semantics.rebuild_tile(language,key['type_preimage'],key['translation'],tick)
            need(canonical(rebuilt) == canonical(offered),'whole original fixture tile')
            semantics.check_collision(rebuilt,names)
            need(semantics.legality(rebuilt,totals,marks,selected,exclusions) is None,'legal original fixture placement')
            for p,v in rebuilt['global_t_values']: totals[tuple(p)] += v
            for p,v in rebuilt['global_m_values']: semantics.agree(marks,tuple(p),v)
            state = dict(state,t=sorted([[list(p),v] for p,v in totals.items()]),
                m=sorted([[list(p),v] for p,v in marks.items()]),
                selected=state['selected']+[rebuilt['selection_record']])
        state['excluded'] = copy.deepcopy([] if excluded is None else excluded)
        state = semantics.private_state(language,state,tick)[0]
        packets = [decorator.decorate_prototype(marking=copy.deepcopy(marking),base_tile=t,tick=tick) for t in tiles]
        full = decorator.decorate_state(marking=copy.deepcopy(marking),base_state=state,decorated_selected=packets,tick=tick)
        excluded_packets = [decorator.decorate_prototype(marking=copy.deepcopy(marking),
            base_tile=semantics.rebuild_tile(language,k['type_preimage'],k['translation'],tick),tick=tick)
            for k in state['excluded']]
        marked = {'schema':'unit-row-channel4-private-state-v1','marking_id':marking['marking_id'],
            'input_epoch':state['input_epoch'],'height':24,'t':full['global_t_values'],
            'm':full['global_m_values'],'selected':[dict(p['placement_key'],generation=1) for p in packets],
            'excluded':[p['placement_key'] for p in excluded_packets],'generation':state['generation']}
        checked = marked_semantics(language).private_state(language,marked,tick)[0]
        need(canonical(checked) == canonical(marked),'fresh full marked state, no projection-only acceptance')
        return marked

    def query(name,state,row,status,base_status=None):
        language = fresh_language()
        proposer_semantics = marked_semantics(language)
        proposal = proposer_semantics.propose_degree(language=language,state=copy.deepcopy(state),row=row,
            degree_proposer=modules['proposer'].propose_degree,tick=tick)
        check_language = fresh_language()
        checker_semantics = marked_semantics(check_language)
        receipt = checker_semantics.check_degree_evidence(language=check_language,state=copy.deepcopy(state),
            row=row,proposal=copy.deepcopy(proposal),tick=tick)
        need(receipt['status'] == status and receipt['marking_id'] == marking['marking_id']
             and receipt['state_sha256'] == hashlib.sha256(canonical(state)).hexdigest(), 'actual fresh marked degree status/context')
        if base_status is not None: need(receipt['original_base_receipt']['status'] == base_status,'actual original status')
        evidence = {'state':copy.deepcopy(state),'base_state':checker_semantics.base_state(check_language,state,tick),
            'row':row,'proposal':proposal,'receipt':receipt}
        fixtures[name] = evidence
        return evidence

    def certify(state,row,completion,candidates):
        language = fresh_language(); current = marked_semantics(language)
        def proposer(**kwargs):
            return current.propose_degree(degree_proposer=modules['proposer'].propose_degree,**kwargs)
        return engine.certify_by_current_cover(language=language,state=copy.deepcopy(state),row=row,
            completion=copy.deepcopy(completion),checked_candidates=copy.deepcopy(candidates),
            degree_proposer=proposer,semantics=current,tick=tick)

    def streams(name,evidence,original_count,marked_count,certified_status):
        state,row = evidence['state'],evidence['row']
        language = fresh_language(); current = marked_semantics(language)
        base = current.base_state(language,state,tick)
        original_cursor = fallback.open_fallback(language=language,state=base,row=row,tick=tick)
        marked_cursor = adapter.open_fallback(language=language,semantics=current,state=copy.deepcopy(state),
            row=row,base_fallback=fallback.open_fallback,tick=tick)
        oc,mc = original_cursor.context(),marked_cursor.context()
        original_events,marked_events = [],[]
        for cursor,events in ((original_cursor,original_events),(marked_cursor,marked_events)):
            while True:
                tick(); event = cursor.advance(); events.append(event)
                if event['kind'] == 'EOF': break
        original_candidates = [e['candidate'] for e in original_events if e['kind'] == 'CANDIDATE']
        marked_candidates = [e['candidate'] for e in marked_events if e['kind'] == 'CANDIDATE']
        need(len(original_candidates) == original_count and len(marked_candidates) == marked_count,'actual complete finite stream lengths')
        expected,rejections = current._filter(language,state,original_candidates,tick)
        need(canonical(expected) == canonical(marked_candidates),'exact original-order surviving full packet subsequence')
        need([e['ordinal'] for e in original_events[:-1]] == list(range(original_count))
             and [e['ordinal'] for e in marked_events[:-1]] == list(range(marked_count)), 'actual contiguous stream ordinals')
        completion = marked_events[-1]['completion']
        need(canonical(completion['original_completion']) == canonical(original_events[-1]['completion'])
             and canonical(mc['original_context']) == canonical(oc),'complete original context/EOF provenance retained')
        receipt = certify(state,row,completion,marked_candidates)
        need(receipt is None if certified_status is None else receipt['status'] == certified_status,
             'fresh complete cover gate, EOF does not imply independent completeness')
        packet = {'fixture_ref':name,'state':state,'base_state':base,'row':row,'original_context':oc,
            'marked_context':mc,'original_events':original_events,'marked_events':marked_events,
            'full_stream_filter_rejections':rejections,'fresh_cover_receipt':receipt,
            'scope':'Actual finite fallback stream; EOF untrusted absent fresh complete cover. Partial proposal scope remains separate.'}
        cursors[name] = packet
        return packet

    language = fresh_language(); root = call(state_from,([],))
    need(root['m'][-1] == [[4,0],0] and root['input_epoch'] == ORIGINAL_BINDING['language_epoch'],
         'original epoch and explicit fixed channel4 zero')
    passed('accepted-marking-fresh-independent-root',state=root,definition_check=definition_check)
    def tiny_carriers():
        left = list(modules['proposer'].iter_bounded_formulas(language=fresh_language(),maximum_nodes=1,tick=tick))
        right = list(semantics.independent_carrier(fresh_language(),1,tick))
        need(left == right == [['bot']] and ['bot'] in marking['definition']['certified_literals'],
             'actual complete size1 carrier and admitted bot literal')
        return {'proposer':left,'independent':right}
    carriers = call(tiny_carriers)
    passed('fresh-complete-size-one-carriers',carriers=carriers)
    variable = language.parameters[0]
    ax_name = sorted(language.theory['axioms'])[0]; ax_formula = copy.deepcopy(language.theory['axioms'][ax_name])
    axioms = [call(tile,({'rule':'axiom','name':ax_name,'formula':ax_formula},[],[],r)) for r in (0,1)]
    universal = ['all',variable,ax_formula]
    seed = call(tile,({'rule':'generalize','variable':variable,'formula':['all',variable,universal]},[universal],[2],3))
    ug_state = call(state_from,(axioms+[seed],))
    many = call(query,('UG-many',ug_state,2,'MANY','MANY'))
    need(many['receipt']['degree_exact'] == 2,'two actual complete UG occurrences')
    passed('complete-UG-many',fixture_ref='UG-many')
    base_keys = [c['base_tile']['placement_key'] for c in many['proposal']['candidates']]
    one_state = call(state_from,(axioms+[seed],base_keys[:1]))
    one = call(query,('UG-one',one_state,2,'SINGLETON','SINGLETON'))
    passed('complete-UG-singleton-with-explicit-control-exclusion',fixture_ref='UG-one',conditional_exclusion=True)
    zero_state = call(state_from,(axioms+[seed],base_keys))
    zero = call(query,('UG-zero',zero_state,2,'ZERO','ZERO'))
    passed('complete-UG-zero-with-explicit-control-exclusions',fixture_ref='UG-zero',conditional_exclusions=True)
    deep42 = ['bot']
    for _ in range(41): deep42 = ['not',deep42]
    deep43 = ['not',deep42]
    need(language.formula(deep42) == 42 and language.formula(deep43) == 43,'native bounded deep formulas')
    def demand(formula,row):
        outer = ['all',variable,formula]
        return tile({'rule':'generalize','variable':variable,'formula':outer},[formula],[row],row+1)
    deep_zero_state = call(state_from,([call(demand,(deep43,2))],))
    deep_zero = call(query,('deep43-zero',deep_zero_state,2,'ZERO','ZERO'))
    passed('deep43-complete-zero',fixture_ref='deep43-zero')
    target = copy.deepcopy(language.target)
    target_state = call(state_from,([call(tile,({'rule':'generalize','variable':variable,
        'formula':['all',variable,target]},[target],[1],3))],))
    filtered_zero = call(query,('target-complete-filtered-zero',target_state,1,'ZERO','SINGLETON'))
    need(filtered_zero['receipt']['complete_cover_checked'] is True
         and filtered_zero['receipt']['original_base_receipt']['degree_exact'] == 1
         and len(filtered_zero['proposal']['marked_rejections']) == 1, 'genuine complete original one loses actual marking')
    passed('complete-original-singleton-filtered-to-zero',fixture_ref='target-complete-filtered-zero',
        scope='Conditional pending UG control only; no target derivation supplied or accepted.')
    partials = []
    for row,expected_survivors,reads in ((2,1,[[0,1],[1,0]]),(3,0,[[0,1],[0,2]])):
        s = call(state_from,([call(demand,(deep42,row))],))
        q = call(query,('deep42-row'+str(row),s,row,'UNKNOWN','TWO_OR_MORE'))
        original = q['proposal']['original_proposal']['candidates']
        actual_reads = [[row+d for d in c['placement_key']['type_preimage']['ordered_offsets']] for c in original]
        need(actual_reads == reads and len(q['proposal']['candidates']) == expected_survivors
             and q['receipt']['complete_cover_checked'] is False and q['receipt']['degree_exact'] is None
             and q['receipt']['sole_candidate'] is None, 'actual partial witness loss remains UNKNOWN')
        partials.append(q)
        passed('partial-two-to-'+str(expected_survivors)+'-remains-UNKNOWN',fixture_ref='deep42-row'+str(row),
            scope='Observed original two-witness prefix only, never entire original inventory.')
    for name,q,bc,mc,expected in (('UG-many',many,2,2,'MANY'),('UG-one',one,1,1,'SINGLETON'),
            ('UG-zero',zero,0,0,'ZERO'),('target-complete-filtered-zero',filtered_zero,1,0,'ZERO'),
            ('deep42-row2',partials[0],2,1,None),('deep42-row3',partials[1],6,4,None)):
        call(streams,(name,q,bc,mc,expected))
        passed('real-cursor-'+name,fixture_ref=name,fresh_cover_expected=expected)
    def verify_proposal(evidence,proposal):
        language = fresh_language(); current = marked_semantics(language)
        return current.check_degree_evidence(language=language,state=copy.deepcopy(evidence['state']),
            row=evidence['row'],proposal=copy.deepcopy(proposal),tick=tick)
    negative('copied-receipt-is-not-a-proposal',lambda:verify_proposal(partials[0],partials[0]['receipt']),
             'channel4 adapter: exact untrusted marked proposal')
    forged = copy.deepcopy(partials[0]['proposal']); forged['original_proposal']['complete_cover_proposed'] = True
    negative('forged-incomplete-cover-flag-rejected',lambda:verify_proposal(partials[0],forged),
             'degree evidence: cover flag exact boolean')
    forged = copy.deepcopy(many['proposal']); forged['candidates'].reverse()
    negative('wrong-full-survivor-proposal-order-rejected',lambda:verify_proposal(many,forged),
             'channel4 adapter: complete independent marked filtering')
    complete = cursors['UG-one']; completion = complete['marked_events'][-1]['completion']
    candidates = [e['candidate'] for e in complete['marked_events'][:-1]]
    wrong_candidates = copy.deepcopy(candidates); wrong_candidates[0] = copy.deepcopy(many['proposal']['candidates'][0])
    negative('wrong-fresh-cover-key-set-rejected',lambda:certify(one_state,2,completion,wrong_candidates),
             'lazy engine: fresh complete cover agrees with entire checked fallback stream')
    forged = copy.deepcopy(completion); forged['state_sha256'] = '0'*64
    negative('wrong-completion-state-digest-rejected',lambda:certify(one_state,2,forged,candidates),
             'lazy engine: fresh completion/cover exact original context')
    forged = copy.deepcopy(completion); forged['marking_id'] = 'forged'
    negative('wrong-completion-marking-id-rejected',lambda:certify(one_state,2,forged,candidates),
             'lazy engine: fresh completion/cover exact original context')
    def poisoned_cursor(interrupt):
        language = fresh_language(); current = marked_semantics(language); gate = {'armed':False}
        def endpoint_tick():
            tick()
            if gate['armed']: raise TimeoutError('declared native-first StageA cursor interruption')
        cursor = adapter.open_fallback(language=language,semantics=current,state=copy.deepcopy(ug_state),
            row=2,base_fallback=fallback.open_fallback,tick=endpoint_tick)
        context = cursor.context(); first = cursor.advance()
        need(first['kind'] == 'CANDIDATE','actual nonempty cursor prefix before poison')
        reason = None
        if interrupt:
            gate['armed'] = True
            try: cursor.advance()
            except TimeoutError as error:
                if type(error) is not TimeoutError: raise
                reason = str(error)
            need(reason == 'declared native-first StageA cursor interruption','explicit callback fault propagated')
            gate['armed'] = False
        else: cursor.abort()
        poison = None
        try: cursor.advance()
        except RuntimeError as error:
            if type(error) is not RuntimeError: raise
            poison = str(error)
        need(poison == 'marked fallback poisoned; no EOF','failed or aborted cursor cannot become EOF')
        return {'context':context,'first_event':first,'interruption_reason':reason,'permanent_poison_reason':poison}
    interrupted = call(poisoned_cursor,(True,))
    passed('interrupted-partial-cursor-permanently-poisoned',evidence=interrupted)
    aborted = call(poisoned_cursor,(False,))
    passed('aborted-partial-cursor-permanently-poisoned',evidence=aborted)
    expected_controls = ['accepted-marking-fresh-independent-root','fresh-complete-size-one-carriers',
        'complete-UG-many','complete-UG-singleton-with-explicit-control-exclusion',
        'complete-UG-zero-with-explicit-control-exclusions','deep43-complete-zero',
        'complete-original-singleton-filtered-to-zero','partial-two-to-1-remains-UNKNOWN','partial-two-to-0-remains-UNKNOWN',
        'real-cursor-UG-many','real-cursor-UG-one','real-cursor-UG-zero','real-cursor-target-complete-filtered-zero',
        'real-cursor-deep42-row2','real-cursor-deep42-row3','copied-receipt-is-not-a-proposal',
        'forged-incomplete-cover-flag-rejected','wrong-full-survivor-proposal-order-rejected',
        'wrong-fresh-cover-key-set-rejected','wrong-completion-state-digest-rejected',
        'wrong-completion-marking-id-rejected','interrupted-partial-cursor-permanently-poisoned',
        'aborted-partial-cursor-permanently-poisoned']
    need([c['case'] for c in controls] == expected_controls and all(c['status'] == 'PASSED' for c in controls),
         'all23 essential StageA controls completed without gaps')
    stageA = {'schema':'ROOT-unit-row-channel4-stageA-payload-v1','stage':'DEGREE_FILTER_ORDERED_CURSOR_EOF_ONLY',
        'prior_acceptance':{k:FIXED_INPUTS[k] for k in FIXED_INPUTS if k.startswith('marking_')},
        'original_model_sources':ORIGINAL_SOURCES,'original_model_binding':ORIGINAL_BINDING,
        'marking':marking,'definition_check':definition_check,'root_state':root,'carriers':carriers,
        'fixtures':fixtures,'cursors':cursors,'controls':controls,'control_count':len(controls),
        'expected_cases':expected_controls,'all_controls_completed':True,
        'later_graph_dependency_retention_rollback_scheduler_qualified':False,
        'target_search_performed':False,'failure_marking_activated':False,'engine_search_performed':False,
        'logical_proof_accepted':False,'exact_point_board_accepted':False,'complete_GCTS_model_accepted':False,
        'GCTS_search_trajectory_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False,'ROOT_resource_accepted':False}
    result_raw = canonical({'schema':'ROOT-unit-row-global-engine-result-v1','purpose':plan['purpose'],
        'sources':plan['sources'],'inputs':plan['inputs'],'language_binding':ORIGINAL_BINDING,
        'controls':None,'search':None,'found_validation':None,'channel4_stageA':stageA,
        'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,
        'logical_proof_accepted':False,'ROOT_resource_accepted':False})+b'\n'
    result_raw=call(encode_result_transport,(result_raw,))
    run=Path(plan['output_directory']);need(run.is_absolute() and run==run.resolve() and not run.exists(),'fresh canonical owned output')
    run.mkdir(mode=0o700);result_pin=call(write_new,(run/'engine-result.json',result_raw))
    body={'schema':'ROOT-unit-row-global-engine-response-body-v1','version':VERSION,
        'status':'COMPLETE_WORKER_PENDING_EXTERNAL','invocation_id':plan['invocation_id'],'plan':raw_pin(plan_raw),
        'sources':plan['sources'],'inputs':plan['inputs'],'language_binding':ORIGINAL_BINDING,'original_model_binding':ORIGINAL_BINDING,
        'outputs':[result_pin],'joint_began_ns':EARLY_G,'joint_deadline_ns':end,'CLOCK_DOMAIN':CLOCK_DOMAIN,
        'limits':LIMITS,'resource_rule':plan['resource_rule'],'ROOT_resource_accepted':False,
        'logical_proof_accepted':False,'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,
        'failure_marking_activated':False,'RL_accepted':False,'GCTS_advantage_claimed':False}
    body_raw=canonical(body)+b'\n';completion={'schema':'Q-clean-verifier-response-completion-v1',
        'body_sha256':hashlib.sha256(body_raw).hexdigest(),'body_bytes':len(body_raw),
        'exit_zero_and_coordinator_deadline_required':True}
    response_pin=call(write_new,(run/'response.jsonl',body_raw+canonical(completion)+b'\n'))
    need(sorted(p.name for p in run.iterdir())==['engine-result.json','response.jsonl'],'whole output2')
    final_raw=canonical({'schema':'ROOT-unit-row-global-engine-final-observation-v1',
        'outputs':[result_pin,response_pin],'response':response_pin,'pending_external':True,
        'logical_proof_accepted':False,'ROOT_resource_accepted':False})+b'\n'
    boundary();offset=0
    while offset<len(final_raw):
        count=os.write(1,final_raw[offset:]);need(count>0,'whole final output receipt');offset+=count
    boundary()
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invoke_code
            or not same_fn(tick,tick_state) or os._exit is not exit_fn or EXIT is not exit_fn):
        raise RuntimeError('original final native/Source endpoint changed')
    tick();exit_fn(0)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except BaseException as error:
        try:
            if (os._exit is EXIT and time.clock_gettime_ns is CLOCK
                    and time.CLOCK_MONOTONIC is CLOCK_ID and CLOCK(CLOCK_ID) < EARLY_G+55000000000):
                os.write(2,('UNIT_ROW_GLOBAL_ENGINE_UNKNOWN: '+type(error).__name__+': '+str(error)[:2048]+'\n').encode())
        finally:
            EXIT(2)
