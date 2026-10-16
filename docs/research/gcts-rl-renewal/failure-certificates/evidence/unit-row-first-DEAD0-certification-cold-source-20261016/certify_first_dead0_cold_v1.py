"""SOURCE ONLY: fresh certification of two first saved DEAD0 contexts.
Current executable Source7 is separate from authenticated original Model Source17.
No engine/search/target proof or marking activation is performed.
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
VERSION='unit-row-first-DEAD0-certification-cold-v1'
SCOPE='unit-row-first-DEAD0-certification-cold-Source'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
CANCELLED=False
FIXED={'clean_support': {'bytes': 48584, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py', 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'}, 'kernel': {'bytes': 10323, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py', 'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'}, 'membership': {'bytes': 20112, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-implementation-source-20261015/bounded_six_rule_language_v2.py', 'sha256': '5d1fb647626c952f4653dd8cffabdb3fe29be0be122ef7e73ef4a7759da43332'}, 'proposer': {'bytes': 22030, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-degree-source-20261015/unit_row_missing_mark_degree_v3.py', 'sha256': 'c960e6e6560502f95f25611c9c85a72b32c67775aedc2e42e0300a366e3d7e90'}, 'degree_checker': {'bytes': 27553, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-checker-source-20261015/independent_unit_row_missing_mark_checker_v2.py', 'sha256': 'c35484000d8ab924d089ace9a185132ef164cad1e24729123290215b8baf8f6d'}, 'row0_projection': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-row-zero-projection-source-20261016/row_zero_rule_projection_v1.py', 'sha256': 'cbd14dfbcd95daa216638eb91e5b4df832606c7b8dcf910b5e9bd89105f38bab', 'bytes': 11074}}
FIXED_INPUTS={'declaration': {'bytes': 2925, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-right-two-preparation-source-20261015/Q-right-two-declaration-v1.json', 'sha256': 'a1ce8237aca64485f94cbce0c909a055a74318ca0cc39b99cf0dc1990323d3df'}, 'profile': {'bytes': 8773, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-ROOT-20261015/ROOT-profile-choice-v2.json', 'sha256': '227b3d4c1e8f5491365b5da580f59367300840d43d388d94e0657cf1b5f89c02'}, 'canonical_plan': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-frontier-ROOT-20261016/ROOT-canonical-search-plan-v1.json', 'sha256': 'b5d28b6269cf6fd19394850c8de833e185529568a66dffc84c2477a6af565366', 'bytes': 7926}, 'canonical_prefix': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-frontier-ROOT-20261016/canonical-search-owned-v1/unknown-diagnostic.json', 'sha256': 'af53a1a7fc531107c5f8dfdd6ecd2f3bc534a9c7ee5bf66a7d8fde812bbca9b4', 'bytes': 967331}, 'canonical_completion': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-frontier-ROOT-20261016/canonical-search-owned-v1/diagnostic-completion.json', 'sha256': '6140ae4d0aa61f61ac9a3a8f1d11d6c80756fb449f63590d93bdff94a16ec190', 'bytes': 337}, 'advised_plan': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-frontier-ROOT-20261016/ROOT-advised-search-plan-v1.json', 'sha256': '118cd141b9c45a7592e965c959ece6acfc49b0a4b4cbb15e2e9ccf5d62e8c7c1', 'bytes': 7917}, 'advised_prefix': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-frontier-ROOT-20261016/advised-search-owned-v1/unknown-diagnostic.json', 'sha256': '95156ef6f9b73eef97188a09d67a8c4b93ada761e7ccf9a69d9abbd6b7e0025d', 'bytes': 980523}, 'advised_completion': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-frontier-ROOT-20261016/advised-search-owned-v1/diagnostic-completion.json', 'sha256': '12d234026b2929daf831dcd6cc91c3aa409cd2cba8065b3a93eef4f7c2310515', 'bytes': 337}}
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

def extract_first_dead0(document, original_plan, original_plan_pin, expected_purpose, tick):
    """Select a bounded saved proposal, never accept its old degree claims."""
    tick()
    need(type(document) is dict and set(document)=={'context','diagnostic','returned_metadata','events_prefix'},
         'whole saved diagnostic fields')
    context=document['context'];diagnostic=document['diagnostic'];events=document['events_prefix']
    need(context['plan']=={k:original_plan_pin[k] for k in ('sha256','bytes')}
         and context['sources']==ORIGINAL_SOURCES and context['inputs']==ORIGINAL_INPUTS
         and context['language_binding']==ORIGINAL_BINDING and context['limits']==LIMITS
         and context['invocation_id']==original_plan['invocation_id']
         and context['purpose']==original_plan['purpose']==expected_purpose,
         'whole original saved context and model binding')
    need(diagnostic['schema']=='unit-row-search-failure-diagnostic-v1'
         and diagnostic['qualification']=='UNQUALIFIED_UNKNOWN_RAW_PREFIX'
         and diagnostic['diagnostic_only'] is True and diagnostic['capture_available'] is True
         and diagnostic['positive_joint_gate_accepted'] is False
         and diagnostic['ROOT_resource_accepted'] is False,
         'saved data are unqualified proposals only')
    need(type(events) is list and 0<len(events)<=2000
         and diagnostic['saved_event_count']==len(events), 'bounded complete saved prefix')
    index=None
    for ordinal,event in enumerate(events):
        tick()
        need(type(event) is dict and type(event.get('event')) is int
             and event['event']==ordinal and type(event.get('kind')) is str,
             'literal ordered saved events')
        decision=event.get('decision')
        if index is None and event['kind']=='DECISION' and type(decision) is dict and decision.get('kind')=='DEAD':
            need(set(decision)=={'kind','row'} and type(decision['row']) is int,'strict saved DEAD decision fields')
            if decision['row']==0:index=ordinal
    need(index is not None, 'saved prefix has a first DEAD0 proposal')
    prefix=events[:index+1];tries=[];places=[]
    for event in prefix:
        tick()
        need(event['kind'] in ('DECISION','FALLBACK','TRY','ADVICE','INVALIDATE','PLACE'),
             'root one-placement prefix only')
        if event['kind']=='TRY':tries.append(event)
        if event['kind']=='PLACE':places.append(event)
    need(len(tries)==len(places)==1 and 0<tries[0]['event']<places[0]['event']<index,
         'one preceding root TRY and PLACE')
    trial,place=tries[0],places[0];root=prefix[0]
    need(trial['mode']=='BRANCH' and type(trial['depth']) is int and trial['depth']==0
         and root['kind']=='DECISION' and root['decision']=={'kind':'BRANCH','row':trial['row']}
         and type(trial['row']) is int and 0<=trial['row']<24
         and place['row']==trial['row'] and canonical(trial['key'])==canonical(place['key'])
         and trial['state_sha256']==root['state_sha256']
         and place['state_sha256']==prefix[-1]['state_sha256'],
         'exact root branch and single full-key placement join')
    key=copy.deepcopy(place['key'])
    need(type(key) is dict and set(key)=={'tile_type_id','type_preimage','translation'}
         and key['translation']==[0,trial['row']], 'complete selected placement key')
    # All evidence/status arrays and returned_metadata are deliberately unused.
    tick()
    return {'schema':'first-DEAD0-context-extraction-v1','dead_event_index':index,
        'try_event_index':trial['event'],'place_event_index':place['event'],
        'selected_key':key,'expected_root_state_sha256':root['state_sha256'],
        'expected_state_sha256':place['state_sha256'],'selected_prefix_events':copy.deepcopy(prefix),
        'saved_receipts_accepted':False,'trajectory_accepted':False}


def require_fresh_zero(receipt, state):
    need(type(receipt) is dict and receipt['schema']=='unit-row-degree-evidence-check-v2'
         and receipt['version']=='independent-unit-row-missing-mark-degree-check-v2'
         and receipt['status']=='ZERO' and receipt['accepted_local_evidence'] is True
         and receipt['complete_cover_checked'] is True and type(receipt['degree_exact']) is int
         and receipt['degree_exact']==0 and receipt['candidate_keys']==[]
         and receipt['sole_candidate'] is None and type(receipt['row']) is int and receipt['row']==0
         and receipt['input_epoch']==state['input_epoch']
         and receipt['state_sha256']==hashlib.sha256(canonical(state)).hexdigest()
         and all(receipt[k] is False for k in ('complete_candidate_graph_accepted',
             'scheduler_or_rollback_accepted','logical_proof_accepted','ROOT_resource_accepted')),
         'fresh independently completed ZERO required')


def main(argv):
    need(__name__=='__main__' and len(argv)==1,'one Root local-certification plan')
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
            raise TimeoutError('complete local certification original20/500 reserve unfinished')
        return now
    tick();signal.signal(signal.SIGINT,cancel);signal.signal(signal.SIGTERM,cancel)
    path=Path(argv[0]);need(path.is_absolute() and path==path.resolve(),'canonical Root plan path')
    plan_raw=path.read_bytes();need(len(plan_raw)<=1048576,'whole bounded Root plan');plan=decode(plan_raw)
    need(set(plan)=={'schema','invocation_id','purpose','output_directory','sources','inputs','source_contract',
        'reviews','ROOT_authorization','runtime','limits','resource_rule'},'exact current plan12')
    need(plan['schema']=='ROOT-first-DEAD0-certification-plan-v1'
         and plan['purpose']=='unit-row-first-DEAD0-certification'
         and plan['resource_rule']=='single-owned-process-native-terminal-v1'
         and plan['limits']==LIMITS and all(type(v) is int for v in plan['limits'].values()),'original six limits')
    need(type(plan['invocation_id']) is str and 1<=len(plan['invocation_id'])<=128
         and all(c.isascii() and (c.isalnum() or c in '-_.:') for c in plan['invocation_id']),'strict actual nonce')
    need(set(plan['sources'])=={'intake',*FIXED}
         and all(plan['sources'][k]==v for k,v in FIXED.items())
         and plan['sources']['intake']['path']==str(Path(__file__).resolve())
         and plan['inputs']==FIXED_INPUTS,'exact current executable Source7 and saved input8')
    need(sys.platform=='darwin' and Path(sys.executable).resolve()==Path(plan['runtime']['path']).resolve(),'native Darwin runtime')
    read_pinned(plan['runtime'])
    source_raw={role:read_pinned(ref) for role,ref in plan['sources'].items()}
    contract=decode(read_pinned(plan['source_contract']))
    need(contract['schema']=='unit-row-first-DEAD0-certification-cold-Source-contract-v1'
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
    need(grant['schema']=='ROOT-first-DEAD0-certification-authorization-v1'
         and grant['author_identity']=='/root' and grant['actual_execution_authorized'] is True
         and type(grant['maximum_actual_invocations']) is int and grant['maximum_actual_invocations']==1
         and all(grant[k]==plan[k] for k in ('invocation_id','purpose','sources','inputs','source_contract',
             'reviews','runtime','limits','resource_rule','output_directory')),'exact once-only Root actual grant')
    inputs_raw={role:read_pinned(ref,4*1048576+131072) for role,ref in FIXED_INPUTS.items()}
    original_raw={role:read_pinned(ref) for role,ref in ORIGINAL_SOURCES.items()}
    for role in ('clean_support','kernel','membership','proposer','degree_checker'):
        need(FIXED[role]==ORIGINAL_SOURCES[role] and source_raw[role]==original_raw[role],
             'current delegated mathematical role raw-identical to original model')
    old_plans={}
    for arm,purpose in (('canonical','unit-row-advised-canonical-search'),('advised','unit-row-advised-target-search')):
        old=decode(inputs_raw[arm+'_plan']);old_plans[arm]=old
        need(old['schema']=='ROOT-unit-row-global-engine-plan-v1' and old['purpose']==purpose
             and old['sources']==ORIGINAL_SOURCES and old['inputs']==ORIGINAL_INPUTS
             and old['limits']==LIMITS and old['resource_rule']==plan['resource_rule'],
             'separately authenticated original Source17 plan')
        old_contract=decode(read_pinned(old['source_contract']))
        need(old_contract['sources']==ORIGINAL_SOURCES and old_contract['inputs']==ORIGINAL_INPUTS,
             'original whole source contract')
        old_grant=decode(read_pinned(old['ROOT_authorization']))
        need(old_grant['author_identity']=='/root' and old_grant['actual_execution_authorized'] is True
             and old_grant['maximum_actual_invocations']==1
             and all(old_grant[k]==old[k] for k in ('invocation_id','purpose','sources','inputs','source_contract',
                 'reviews','runtime','limits','resource_rule','output_directory')),'original fixed Root grant provenance only')
        for role,ref in old['reviews'].items():
            rv=decode(read_pinned(ref));need(rv['source']==ORIGINAL_SOURCES['intake']
                and rv['sources']==ORIGINAL_SOURCES and rv['source_contract']==old['source_contract']
                and rv['source_only'] is True and rv['source_review_passed'] is True,'original Source review provenance only')
        marker=decode(inputs_raw[arm+'_completion'])
        need(marker['schema']=='unit-row-search-failure-diagnostic-completion-v1'
             and marker['file']=='unknown-diagnostic.json'
             and {k:marker[k] for k in ('sha256','bytes')}==raw_pin(inputs_raw[arm+'_prefix'])
             and marker['diagnostic_only'] is True and marker['positive_joint_gate_accepted'] is False
             and marker['ROOT_resource_accepted'] is False
             and marker['terminal_exit2_and_external_failure_closure_required'] is True,'whole original raw diagnostic completion')
    declaration_raw,profile_raw=inputs_raw['declaration'],inputs_raw['profile']
    need(FIXED_INPUTS['declaration']==ORIGINAL_INPUTS['declaration'] and FIXED_INPUTS['profile']==ORIGINAL_INPUTS['profile'],
         'same original raw input2')
    authority_raw=canonical({'declaration':decode(declaration_raw),'policy':decode(profile_raw),
        'source_bindings':ORIGINAL_SOURCES,'binding':ORIGINAL_BINDING})
    original_context_raw=canonical({'sources':ORIGINAL_SOURCES,'binding':ORIGINAL_BINDING,'inputs':ORIGINAL_INPUTS,'plans':old_plans})
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
             'inputs':ORIGINAL_INPUTS,'plans':old_plans})==original_context_raw,'current plan and private original authority unchanged')
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
    def rebuild_sample(extraction,language):
        tick();epoch=ORIGINAL_BINDING['language_epoch']
        root={'schema':'unit-row-implicit-private-state-v1','input_epoch':epoch,'height':24,
            't':[[[0,r],0] for r in range(24)],
            'm':[[[1,k],['outside',epoch]] for k in range(-23,0)]+[[[1,23],['formula',canonical(language.target).decode('utf8')]]],
            'selected':[],'excluded':[],'generation':[[[0,r],0] for r in range(24)]}
        need(hashlib.sha256(canonical(root)).hexdigest()==extraction['expected_root_state_sha256'],'exact saved root state SHA')
        key=copy.deepcopy(extraction['selected_key'])
        need(key['type_preimage']['input_epoch']==epoch,'selected original epoch required')
        _,totals,marks,selected,excluded,names=semantics.private_state(language,root,tick)
        candidate=semantics.rebuild_tile(language,key['type_preimage'],key['translation'],tick)
        need(canonical(candidate['placement_key'])==canonical(key),'selected original full key without rewriting')
        semantics.check_collision(candidate,names)
        need(semantics.legality(candidate,totals,marks,selected,excluded) is None,'selected whole original placement legal')
        for point,value in candidate['global_t_values']:
            tick();point=tuple(point);need(point in totals,'selected support within fixed target');totals[point]+=value
        for point,value in candidate['global_m_values']:
            tick();point=tuple(point)
            need(point not in marks or canonical(marks[point])==canonical(value),'selected literal marking agreement')
            marks[point]=copy.deepcopy(value)
        state=dict(root,t=sorted([[list(p),v] for p,v in totals.items()]),m=sorted([[list(p),v] for p,v in marks.items()]),
            selected=[candidate['selection_record']])
        checked=semantics.private_state(language,state,tick)[0]
        need(canonical(checked)==canonical(state) and state['excluded']==[]
             and dict((tuple(p),v) for p,v in state['t'])[(0,0)]==0,'unfilled row0 exact reconstructed state')
        need(hashlib.sha256(canonical(state)).hexdigest()==extraction['expected_state_sha256'],'exact saved rebuilt state SHA')
        return state
    def check_proposal(state,proposal):
        language=fresh_language()
        return call(semantics.check_degree_evidence,kwargs={'language':language,'state':copy.deepcopy(state),
            'row':0,'proposal':copy.deepcopy(proposal),'tick':tick})
    controls=[]
    def negative(name,fn,reason):
        tick();caught=None
        try:call(fn)
        except ValueError as error:
            if type(error) is not ValueError:raise
            caught=str(error)
        need(caught==reason,'exact declared negative rejection, never callback/authority/resource failure')
        tick();controls.append({'case':name,'status':'PASSED','reason':caught})
    samples=[]
    for arm,purpose in (('canonical','unit-row-advised-canonical-search'),('advised','unit-row-advised-target-search')):
        tick();document=decode(inputs_raw[arm+'_prefix']);old=old_plans[arm]
        extraction=call(extract_first_dead0,(document,old,FIXED_INPUTS[arm+'_plan'],purpose,tick))
        language=fresh_language();state=call(rebuild_sample,(extraction,language))
        proposal=call(modules['proposer'].propose_degree,kwargs={'language':fresh_language(),
            'state':copy.deepcopy(state),'row':0,'tick':tick})
        receipt=check_proposal(state,proposal);call(require_fresh_zero,(receipt,state))
        literal=decode(dict((tuple(p),v) for p,v in state['m'])[(1,0)][1])
        projection=call(modules['row0_projection'].certify_row_zero_projection,kwargs={
            'language':fresh_language(),'authority':decode(authority_raw),'literal':copy.deepcopy(literal),'tick':tick})
        projection_check=call(modules['row0_projection'].check_row_zero_projection,kwargs={
            'language':fresh_language(),'authority':decode(authority_raw),'literal':copy.deepcopy(literal),
            'certificate':copy.deepcopy(projection),'tick':tick})
        need(projection['schema']=='unit-row-row-zero-projection-certificate-v1' and projection['status']=='FORBIDDEN'
             and projection_check['schema']=='unit-row-row-zero-projection-check-v1'
             and projection_check['projection_accepted'] is True
             and projection_check['certificate_sha256']==hashlib.sha256(json.dumps(projection,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')).hexdigest()
             and canonical(projection_check['recomputed_certificate'])==canonical(projection),'fresh input-scoped row0 projection check')
        samples.append({'arm':arm,'selection':extraction,'state':state,'state_sha256':hashlib.sha256(canonical(state)).hexdigest(),
            'original_model_binding':copy.deepcopy(ORIGINAL_BINDING),'fresh_proposal':proposal,'fresh_receipt':receipt,
            'literal':literal,'projection_certificate':projection,'projection_check':projection_check,
            'saved_receipts_accepted':False,'old_trajectory_accepted':False})
        controls.append({'case':arm+'-fresh-complete-ZERO-and-projection','status':'PASSED'})
        if arm=='canonical':
            bad=copy.deepcopy(extraction);bad['expected_state_sha256']='0'*64
            negative('changed-saved-state-hash-rejected',lambda:rebuild_sample(bad,fresh_language()),'exact saved rebuilt state SHA')
            bad_epoch=copy.deepcopy(extraction);bad_epoch['selected_key']['type_preimage']['input_epoch']='stale'
            negative('selected-stale-epoch-rejected',lambda:rebuild_sample(bad_epoch,fresh_language()),'selected original epoch required')
            bad_doc=copy.deepcopy(document);bad_doc['events_prefix'][0]['kind']='EXCLUDE'
            negative('root-exclusion-prefix-rejected',lambda:extract_first_dead0(bad_doc,old,FIXED_INPUTS[arm+'_plan'],purpose,tick),'root one-placement prefix only')
            old_receipt=dict(document['events_prefix'][extraction['dead_event_index']]['evidence'])[0]
            negative('copied-old-ZERO-is-not-a-proposal',lambda:check_proposal(state,old_receipt),'degree evidence: exact proposal fields')
            forged=copy.deepcopy(proposal);forged['coverage']['axiom_labels_seen']=[]
            negative('forged-complete-cover-census-rejected',lambda:check_proposal(state,forged),'degree evidence: complete occurrence/pair census')
            unknown=copy.deepcopy(proposal);unknown.update(kind='UNKNOWN',complete_cover_proposed=False,candidates=[],coverage=None,fibre_cover=None,rejections=[])
            unknown_receipt=check_proposal(state,unknown)
            need(unknown_receipt['status']=='UNKNOWN' and unknown_receipt['complete_cover_checked'] is False,'honest incomplete query remains UNKNOWN')
            negative('UNKNOWN-never-certified-ZERO',lambda:require_fresh_zero(unknown_receipt,state),'fresh independently completed ZERO required')
    projection_flags=('logical_proof_accepted','exact_point_board_accepted','target_impossibility_accepted',
        'complete_GCTS_model_accepted','marking_activation_accepted','trajectory_accepted','GCTS_advantage_accepted','RL_accepted','ROOT_resource_accepted')
    for sample in samples:
        need(all(sample['projection_certificate'][k] is False and sample['projection_check'][k] is False for k in projection_flags),
             'projection is narrow input-scoped lemma only')
    ax_name=sorted(decode(authority_raw)['declaration']['theory']['axioms'])[0]
    ax_literal=copy.deepcopy(decode(authority_raw)['declaration']['theory']['axioms'][ax_name])
    ax_certificate=call(modules['row0_projection'].certify_row_zero_projection,kwargs={
        'language':fresh_language(),'authority':decode(authority_raw),'literal':ax_literal,'tick':tick})
    ax_check=call(modules['row0_projection'].check_row_zero_projection,kwargs={
        'language':fresh_language(),'authority':decode(authority_raw),'literal':copy.deepcopy(ax_literal),
        'certificate':copy.deepcopy(ax_certificate),'tick':tick})
    need(ax_certificate['status']=='NOT_CERTIFIED' and ax_check['projection_accepted'] is False,
         'actual original named AX cannot yield a forbidden projection certificate')
    controls.append({'case':'original-AX-is-not-forbidden','status':'PASSED','AX_name':ax_name,
        'certificate':ax_certificate,'check':ax_check})
    reference=samples[0]
    def check_projection(certificate):
        return call(modules['row0_projection'].check_row_zero_projection,kwargs={
            'language':fresh_language(),'authority':decode(authority_raw),'literal':copy.deepcopy(reference['literal']),
            'certificate':certificate,'tick':tick})
    for mutation in ('census','binding','literal'):
        forged_projection=copy.deepcopy(reference['projection_certificate'])
        if mutation=='census':forged_projection['named_axiom_census']=[]
        elif mutation=='binding':forged_projection['model_authority']['binding']['language_epoch']='stale'
        else:forged_projection['literal']=copy.deepcopy(ax_literal)
        negative('projection-forged-'+mutation+'-rejected',lambda:check_projection(forged_projection),
            'row-zero projection: complete certificate matches original authority/literal/census/six-rule reasons')
    expected_controls=['canonical-fresh-complete-ZERO-and-projection','changed-saved-state-hash-rejected',
        'selected-stale-epoch-rejected','root-exclusion-prefix-rejected','copied-old-ZERO-is-not-a-proposal',
        'forged-complete-cover-census-rejected','UNKNOWN-never-certified-ZERO',
        'advised-fresh-complete-ZERO-and-projection','original-AX-is-not-forbidden',
        'projection-forged-census-rejected','projection-forged-binding-rejected','projection-forged-literal-rejected']
    need([v['case'] for v in controls]==expected_controls and all(v['status']=='PASSED' for v in controls)
         and len(samples)==2,'all two samples and twelve explicit local controls completed')
    certification={'schema':'ROOT-first-DEAD0-certification-payload-v1',
        'original_model_sources':ORIGINAL_SOURCES,'original_model_binding':ORIGINAL_BINDING,
        'samples':samples,'controls':controls,'sample_count':len(samples),'control_count':len(controls),
        'all_controls_completed':True,'local_contexts_freshly_checked':True,
        'row0_projection_certificates_checked':True,'saved_receipts_accepted':False,
        'logical_proof_accepted':False,'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,
        'failure_marking_activated':False,'RL_accepted':False,'GCTS_advantage_claimed':False,'ROOT_resource_accepted':False}
    result_raw=canonical({'schema':'ROOT-unit-row-global-engine-result-v1','purpose':plan['purpose'],
        'sources':plan['sources'],'inputs':plan['inputs'],'language_binding':ORIGINAL_BINDING,
        'controls':None,'search':None,'found_validation':None,'certification':certification,
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
