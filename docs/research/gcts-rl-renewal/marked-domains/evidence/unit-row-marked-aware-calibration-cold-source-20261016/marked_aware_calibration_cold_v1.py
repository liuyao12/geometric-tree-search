"""Prospective local marked-aware degree calibration only, Source unexecuted.
Four separately granted original20 endpoints; six essential assertions total.
New proposals/receipts never masquerade as engine11 or old c354 evidence.
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
VERSION='unit-row-marked-aware-local-degree-calibration-cold-v1'
SCOPE='unit-row-marked-aware-calibration-cold-Source'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
CANCELLED=False
CALIBRATION_CASES_BY_PURPOSE={'unit-row-marked-aware-calibration-zero': ['MA-01-complete-marked-ZERO'], 'unit-row-marked-aware-calibration-singleton': ['MA-02-complete-marked-SINGLETON'], 'unit-row-marked-aware-calibration-two': ['MA-03-two-marked-witnesses-lower-bound-only'], 'unit-row-marked-aware-calibration-negative-protocol': ['MA-04-wrong-original-binding-provenance-rejected', 'MA-05-omitted-ordered-MP-fibre-rejected', 'MA-06-inconsistent-completion-flag-rejected']}
FIXED={'clean_support': {'bytes': 48584, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py', 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'}, 'kernel': {'bytes': 10323, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py', 'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'}, 'membership': {'bytes': 20112, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-implementation-source-20261015/bounded_six_rule_language_v2.py', 'sha256': '5d1fb647626c952f4653dd8cffabdb3fe29be0be122ef7e73ef4a7759da43332'}, 'proposer': {'bytes': 22030, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-degree-source-20261015/unit_row_missing_mark_degree_v3.py', 'sha256': 'c960e6e6560502f95f25611c9c85a72b32c67775aedc2e42e0300a366e3d7e90'}, 'degree_checker': {'bytes': 27553, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-checker-source-20261015/independent_unit_row_missing_mark_checker_v2.py', 'sha256': 'c35484000d8ab924d089ace9a185132ef164cad1e24729123290215b8baf8f6d'}, 'decorator': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-certified-mark-decorator-source-20261016/certified_row0_point_mark_decorator_v1.py', 'sha256': 'fcc4aeb3275f47cbdba26436e2224bffad91e80974e873d2d57d9263151a3895', 'bytes': 12619}, 'marked_verifier': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-state-verifier-source-20261016/independent_channel4_state_verifier_v1.py', 'sha256': '9fd60cad12881e3519c785c417b3348bd013a5ff0b8aa993399276e266da9a6a', 'bytes': 18475}, 'marked_adapter': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-engine-source-20261016/marked_unit_row_adapter_v1.py', 'sha256': '821fe692dc7a118cdc3355d3128ecdf08287abf229365b97a04341e0dc4cb7f9', 'bytes': 28980}, 'engine': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-engine-source-20261016/lazy_unit_row_global_engine_v11.py', 'sha256': 'fbd1455fbcb090045ae2a6ad151e4a5ae41d01e1549be135e8b8d7b64f597476', 'bytes': 56207}, 'fallback': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-all-six-fallback-source-20261015/unit_row_all_six_fallback_v1.py', 'sha256': '69b4a9170d931e01138f5d7f98514f26e47cbfe7ab8b7503b99f6a24934a4fae', 'bytes': 24227}, 'marked_aware_proposer': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-aware-fibre-proposer-source-20261016/marked_aware_nonimp_fibre_proposer_v1.py', 'sha256': '4316adcc791b8e078cd2bc5ebade234ae24936c2195b6be9addc25b12a0cbd1d', 'bytes': 14064}, 'marked_aware_checker': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-aware-fibre-checker-source-20261016/independent_marked_aware_fibre_checker_v1.py', 'sha256': '8f7a06a28bebb2558a4d2acdae58be4c793d0179f1616b2625d5cb1ee80e9188', 'bytes': 25783}}
FIXED_INPUTS={'stageB_disposition': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageB-qualification-ROOT-20261016/ROOT-stageB-disposition-v1.json', 'sha256': 'ecb994c6ada2835db51c7a2d8ada6f7833d9945635449ba9be448da0dee6193e', 'bytes': 4574}, 'stageB_plan': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageB-qualification-ROOT-20261016/ROOT-stageB-plan-v1.json', 'sha256': '7047504acb8527a7476a7cb24c8031d6b5796150f9f0ce07b914bbd955e5d009', 'bytes': 7924}, 'stageB_transport': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageB-qualification-ROOT-20261016/ROOT-stageB-transport-concordance-v1.json', 'sha256': '8704567e955cab88e42cd867a4cd28d2911e4afffa286b87b2b27b1b5afda08b', 'bytes': 1502}, 'stageB_expanded': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageB-qualification-ROOT-20261016/ROOT-stageB-expanded-result-v1.json', 'sha256': 'bb64b73377940ae6833ae2b30d1bd96396dabffe3e7f773bdfaa640327d8ad93', 'bytes': 1926833}, 'stageB_encoded': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageB-qualification-ROOT-20261016/stageB-owned-v1/engine-result.json', 'sha256': '3515e77e2554df1b588311772e38f12a401039ca9e2c106227ff0a16e7a149ca', 'bytes': 162591}, 'stageB_response': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageB-qualification-ROOT-20261016/stageB-owned-v1/response.jsonl', 'sha256': '8ca1ac71fa5a4c1734b68460cf029cfa2e1da0cf7e0670ab53e956f43d95435e', 'bytes': 7572}, 'declaration': {'bytes': 2925, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-right-two-preparation-source-20261015/Q-right-two-declaration-v1.json', 'sha256': 'a1ce8237aca64485f94cbce0c909a055a74318ca0cc39b99cf0dc1990323d3df'}, 'profile': {'bytes': 8773, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-ROOT-20261015/ROOT-profile-choice-v2.json', 'sha256': '227b3d4c1e8f5491365b5da580f59367300840d43d388d94e0657cf1b5f89c02'}}
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


class ObservedCursor:
    """Record genuine state-bound fallback events; never create or alter EOF."""
    def __init__(self,real,record,tick):
        self.real,self.record,self.tick = real,record,tick
    def context(self):
        return self.real.context()
    def advance(self):
        self.tick()
        event = self.real.advance()
        self.record['events'].append(copy.deepcopy(event))
        return event
    def abort(self):
        return self.real.abort()


class ChildControlInterruption(TimeoutError):
    """Declared native-first actual-child callback stop; not native exhaustion."""
    pass


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
    need(plan['schema']=='ROOT-marked-aware-calibration-plan-v1'
         and plan['purpose'] in CALIBRATION_CASES_BY_PURPOSE
         and plan['resource_rule']=='single-owned-process-native-terminal-v1'
         and plan['limits']==LIMITS and all(type(v) is int for v in plan['limits'].values()),'original six limits')
    need(type(plan['invocation_id']) is str and 1<=len(plan['invocation_id'])<=128
         and all(c.isascii() and (c.isalnum() or c in '-_.:') for c in plan['invocation_id']),'strict actual nonce')
    need(set(plan['sources'])=={'intake',*FIXED}
         and all(plan['sources'][k]==v for k,v in FIXED.items())
         and plan['sources']['intake']['path']==str(Path(__file__).resolve())
         and plan['inputs']==FIXED_INPUTS,'exact current executable Source13 and saved input8')
    need(sys.platform=='darwin' and Path(sys.executable).resolve()==Path(plan['runtime']['path']).resolve(),'native Darwin runtime')
    read_pinned(plan['runtime'])
    source_raw={role:read_pinned(ref) for role,ref in plan['sources'].items()}
    contract=decode(read_pinned(plan['source_contract']))
    need(contract['schema']=='unit-row-marked-aware-calibration-cold-Source-contract-v1'
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
    need(grant['schema']=='ROOT-marked-aware-calibration-authorization-v1'
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
    # Authenticate the WHOLE prior StageB result. Its receipts are inputs,
    # never substituted for the fresh checks in this current native window.
    accepted = decode(inputs_raw['stageB_disposition'])
    prior = decode(inputs_raw['stageB_plan'])
    transport = decode(inputs_raw['stageB_transport'])
    expanded = decode(inputs_raw['stageB_expanded'])
    need(accepted['schema'] == 'ROOT-channel4-stageB-disposition-v1'
         and accepted['actual_closed'] is True and accepted['all_reaped'] is True
         and accepted['native_resources_qualified'] is True and accepted['complete_wire_verified'] is True
         and accepted['support_retention_archive_reference_controls_accepted'] is True
         and accepted['cached_degree_receipt_transfer_exercised'] is False
         and accepted['global_decision_or_scheduler_qualified'] is False
         and accepted['unknown_child_search_rollback_qualified'] is False
         and accepted['passed_cases'] == 9 and accepted['skipped_cases'] == 0,
         'fixed prior Root acceptance of9support/archive/refcount cases only')
    need(accepted['plan'] == FIXED_INPUTS['stageB_plan']
         and accepted['lossless_transport_concordance'] == FIXED_INPUTS['stageB_transport']
         and accepted['outputs'] == [FIXED_INPUTS['stageB_encoded'], FIXED_INPUTS['stageB_response']]
         and transport['plan'] == FIXED_INPUTS['stageB_plan']
         and transport['encoded_file'] == FIXED_INPUTS['stageB_encoded']
         and transport['expanded_file'] == FIXED_INPUTS['stageB_expanded']
         and transport['all_full_record_bytes_retained'] is True,
         'prior marking disposition/plan/transport/full output joins')
    need(canonical(expanded)+b'\n' == inputs_raw['stageB_expanded']
         and expanded['sources'] == prior['sources'] and expanded['inputs'] == prior['inputs']
         and expanded['purpose'] == prior['purpose'] == 'unit-row-channel4-retention-archive-refs-controls'
         and expanded['language_binding'] == accepted['original_model_binding'] == ORIGINAL_BINDING,
         'accepted canonical whole result and original semantic epoch')
    old_contract = decode(read_pinned(prior['source_contract']))
    need(old_contract['sources'] == prior['sources'] and old_contract['inputs'] == prior['inputs']
         and old_contract['original_model_sources'] == ORIGINAL_SOURCES
         and old_contract['original_model_binding'] == ORIGINAL_BINDING, 'prior Source11 versus original Model17')
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
    lines = inputs_raw['stageB_response'].splitlines(keepends=True)
    need(len(lines) == 2 and all(v.endswith(b'\n') for v in lines), 'prior response exactly twoLF')
    old_body, old_completion = map(decode,lines)
    need(old_completion['body_sha256'] == hashlib.sha256(lines[0]).hexdigest()
         and old_completion['body_bytes'] == len(lines[0])
         and old_body['plan'] == raw_pin(inputs_raw['stageB_plan'])
         and old_body['sources'] == prior['sources'] and old_body['inputs'] == prior['inputs']
         and old_body['outputs'] == [FIXED_INPUTS['stageB_encoded']], 'prior complete response bytes')
    previous = expanded['channel4_stageB']
    need(previous['schema'] == 'ROOT-unit-row-channel4-stageB-payload-v1'
         and previous['original_model_sources'] == ORIGINAL_SOURCES
         and previous['original_model_binding'] == ORIGINAL_BINDING
         and previous['control_count'] == 9 and len(previous['controls']) == 9
         and len(previous['families']) == 3
         and previous['cached_degree_receipt_transfer_exercised'] is False
         and previous['global_decision_or_scheduler_qualified'] is False
         and previous['unknown_child_search_rollback_qualified'] is False
         and previous['all_controls_completed'] is True
         and all(c['status'] == 'PASSED' for c in previous['controls'])
         and all(accepted[k] is False for k in ('target_search_performed',
            'logical_proof_accepted','complete_GCTS_model_accepted','RL_accepted','GCTS_advantage_claimed')),
         'prior narrow StageB acceptance, no cached-degree/global/search qualification')
    marking = copy.deepcopy(previous['marking'])
    need(marking['marking_id'] == accepted['marking_id'],
         'whole accepted frozen marking identity')
    adapter, engine, fallback = (modules[k] for k in ('marked_adapter','engine','fallback'))
    decorator, verifier = modules['decorator'], modules['marked_verifier']
    need(engine.VERSION == 'lazy-unit-row-global-engine-v11-channel4-global-original-key-collision'
         and adapter.VERSION == 'unit-row-channel4-point-adapter-v1', 'current reviewed engine/adapter versions')
    definition_check = call(verifier.check_marking,kwargs={'language':fresh_language(),
        'semantics':semantics,'marking':copy.deepcopy(marking),'tick':tick})
    need(definition_check['marking_checked'] is True and definition_check['marking_id'] == marking['marking_id'],
         'fresh independent whole marking check')
    controls, families = [], {}
    def passed(name, **data):
        tick(); controls.append(dict(case=name,status='PASSED',**data))

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

    language = fresh_language()
    variable = language.parameters[0]
    ax_name = sorted(language.theory['axioms'])[0]
    ax_formula = copy.deepcopy(language.theory['axioms'][ax_name])
    need(['bot'] in marking['definition']['certified_literals'], 'authenticated certified bot literal for new mark supports')

    def ug(body, source, row):
        return tile({'rule':'generalize','variable':variable,'formula':['all',variable,copy.deepcopy(body)]},
                    [body],[source],row)

    def snapshot(e):
        value = e.state_snapshot()
        need(value['state']['generation'] == [[[0,r],0] for r in range(24)]
             and value['marking_id'] == marking['marking_id'], 'original roots0 and frozen marked snapshot')
        return value

    def candidate(base,state):
        language = fresh_language(); current = marked_semantics(language)
        _,totals,marks,selected,excluded,names = current.private_state(language,state,tick)
        key = base['placement_key']
        pre = {'schema':'unit-row-row0-decorated-type-v1',
            'base_type_preimage':copy.deepcopy(key['type_preimage']),'marking_id':marking['marking_id']}
        value = current.rebuild_tile(language,pre,copy.deepcopy(key['translation']),tick)
        current.check_collision(value,names)
        reason = current.legality(value,totals,marks,selected,excluded)
        return current.with_obligations(value,totals,tick),reason

    def place_base(e,base):
        before = snapshot(e)
        value,reason = candidate(base,before['state'])
        need(reason is None,'fresh whole-current-point legality before public placement')
        e.place(value)
        return value

    def rowproof(value,row):
        return next(p for p in value['last_transition']['rows'] if p['row'] == row)

    def slot(value,row):
        return dict(value['cursors'])[row]

    def archived(value,old_slot):
        return [entry for entry in value.get('context_archive',[]) if
            all(canonical(entry[name]) == canonical(old_slot[name])
                for name in ('context','keys','candidates','completion'))]

    def core(value):
        return {k:v for k,v in value.items() if k != 'read_obligations'}

    def maps(entries):
        return {tuple(p):v for p,v in entries}

    def exact_restore(e,token,before):
        e.rollback(token)
        after = snapshot(e)
        need(canonical(after) == canonical(before),'exact owned semantic/domain/cursor/archive/dependency restore')
        return after

    new_proposer, new_checker = modules['marked_aware_proposer'], modules['marked_aware_checker']
    need(new_proposer.VERSION == 'unit-row-marked-aware-nonimp-fibre-proposer-v1'
         and new_checker.VERSION == 'unit-row-independent-marked-aware-nonimp-fibre-checker-v1',
         'exact new local-only proposer/checker versions')
    marking_raw = canonical(marking)

    def check_new(state, row, proposal):
        receipt = call(new_checker.check_degree_evidence,kwargs={
            'language':fresh_language(),'base_semantics':semantics,'verifier':verifier,
            'marking':copy.deepcopy(marking),'state':copy.deepcopy(state),'row':row,
            'proposal':copy.deepcopy(proposal),'tick':tick})
        need(canonical(marking) == marking_raw, 'private accepted marking unchanged')
        return receipt

    def new_query(state, row):
        private_state_raw = canonical(state)
        producer_language = fresh_language()
        current = marked_semantics(producer_language)
        proposal = call(new_proposer.propose_degree,kwargs={'language':producer_language,
            'semantics':current,'state':copy.deepcopy(state),'row':row,'tick':tick})
        del current, producer_language
        need(canonical(state) == private_state_raw and canonical(marking) == marking_raw,
             'producer cannot replace private current state or marking')
        receipt = check_new(state,row,proposal)
        need(proposal['schema'] == 'unit-row-marked-aware-nonimp-fibre-proposal-v1'
             and receipt['schema'] == 'unit-row-marked-aware-nonimp-fibre-check-v1'
             and receipt['version'] == new_checker.VERSION
             and receipt['proposal_sha256'] == hashlib.sha256(canonical(proposal)).hexdigest()
             and canonical(receipt['state']) == private_state_raw
             and receipt['state_sha256'] == hashlib.sha256(private_state_raw).hexdigest()
             and canonical(receipt['original_state']) == canonical(proposal['original_state'])
             and receipt['original_state_sha256'] == proposal['original_state_sha256']
             and receipt['row'] == row and receipt['input_epoch'] == ORIGINAL_BINDING['language_epoch']
             and receipt['language_binding'] == ORIGINAL_BINDING
             and receipt['marking_id'] == marking['marking_id']
             and receipt['independent_marked_state_check']['marked_state_checked'] is True
             and all(proposal[k] is False and receipt[k] is False for k in
                 ('complete_candidate_graph_accepted','scheduler_or_rollback_accepted',
                  'logical_proof_accepted','ROOT_resource_accepted')),
             'fresh new typed local receipt/full context with all strong flags false')
        return {'state':copy.deepcopy(state),'query_row':row,'proposal':proposal,'receipt':receipt}

    def reads_of(candidate):
        key = candidate['placement_key']
        return [key['translation'][1]+d for d in key['type_preimage']['base_type_preimage']['ordered_offsets']]

    def fixture(mode):
        deep42 = ['bot']
        for unused in range(41): deep42 = ['not',deep42]
        carrier = None
        if mode in ('singleton','two'):
            need(language.formula(deep42) == 42, 'fresh deep42 bounded constructor size')
            carrier = list(new_proposer.iter_bounded_formulas(language=language,maximum_nodes=1,tick=tick))
            need(carrier == [['bot']], 'whole original size1 carrier exactly bot')
        if mode == 'zero':
            body = ['all',variable,['bot']]
            seeds, row = [ug(body,1,3)], 1
        elif mode == 'singleton':
            seeds, row = [ug(ax_formula,1,4),ug(deep42,3,5)], 3
        else:
            need(mode == 'two','declared fixture mode')
            seeds, row = [ug(deep42,3,5)], 3
        state = state_from(seeds)
        result = new_query(state,row)
        p, r = result['proposal'], result['receipt']
        need(state['excluded'] == [] and state['generation'] == [[[0,k],0] for k in range(24)]
             and r['accepted_local_evidence'] is True
             and canonical(p['candidates']) == canonical(r['checked_candidates'])
             and r['candidate_keys'] == [c['placement_key'] for c in p['candidates']]
             and r['checked_root_rejections'] == p['root_rejections'],
             'actual fixture local evidence, empty exclusions and original roots0')
        actual_reads = [reads_of(c) for c in p['candidates']]
        if mode in ('zero','singleton'):
            cover = r['checked_fibre_cover']
            need(p['kind'] == 'COMPLETE_NONIMP_FIBRE_COVER' and p['complete_cover_proposed'] is True
                 and r['complete_cover_checked'] is True and r['nonimp_fibre_cover_checked'] is True
                 and canonical(cover) == canonical(p['fibre_cover']) and cover['completed'] is True
                 and len(cover['UG_fibres']) == row and len(cover['ordered_MP_fibres']) == row*row
                 and all(f['completed'] is True for f in cover['UG_fibres']+cover['ordered_MP_fibres']),
                 'entire new independent complete finite nonimp census')
            if mode == 'zero':
                need(r['status'] == 'ZERO' and type(r['degree_exact']) is int and r['degree_exact'] == 0
                     and r['candidate_keys'] == [] and r['sole_candidate'] is None
                     and p['candidates'] == [] and cover['UG_fibres'][0]['examined'] == 1
                     and cover['UG_fibres'][0]['rejections'] == 1
                     and cover['ordered_MP_fibres'][0]['case'] == 'FINITE_AST_OCCURS_CHECK_EMPTY',
                     'complete ZERO after genuine marked UG rejection and same-row MP occurs check')
            else:
                need(r['status'] == 'SINGLETON' and type(r['degree_exact']) is int and r['degree_exact'] == 1
                     and len(r['candidate_keys']) == 1 and actual_reads == [[2,0]]
                     and canonical(r['sole_candidate']) == canonical(p['candidates'][0])
                     and cover['output_nodes'] == 42 and cover['MP_antecedent_max_nodes'] == 1
                     and sum(f['rejections'] for f in cover['ordered_MP_fibres']) >= 1,
                     'complete fresh marked singleton from same oldC4 state, no old receipt replay')
        else:
            need(p['kind'] == 'TWO_LEGAL_WITNESSES' and p['complete_cover_proposed'] is False
                 and p['fibre_cover']['completed'] is False and len(p['candidates']) == 2
                 and r['status'] == 'TWO_OR_MORE' and r['complete_cover_checked'] is False
                 and r['nonimp_fibre_cover_checked'] is False and r['degree_exact'] is None
                 and r['sole_candidate'] is None and r['checked_fibre_cover'] is None
                 and actual_reads == [[1,0],[1,2]]
                 and canonical(r['candidate_keys'][0]) != canonical(r['candidate_keys'][1]),
                 'two actual marked-legal witnesses only, no complete count or EOF authority')
        result.update(seeds=seeds,size1_carrier=carrier,actual_candidate_reads=actual_reads,
            evidence_scope='Local degree calibration only; pending read obligations are not installed facts.')
        return result

    def positive(mode):
        data = fixture(mode)
        families[mode.upper()] = data
        passed(CALIBRATION_CASES_BY_PURPOSE[plan['purpose']][0],family=mode.upper())

    def negative_protocol():
        data = fixture('zero')
        proposal, state, row = data['proposal'], data['state'], data['query_row']
        failures = []
        for index in range(3):
            bad = copy.deepcopy(proposal)
            if index == 0:
                bad['language_binding']['language_epoch'] = '0'*64
                mutation = 'language_binding.language_epoch replaced by a stale literal'
                reason = 'whole original/marked current context'
            elif index == 1:
                need(len(bad['fibre_cover']['ordered_MP_fibres']) == 1,'ZERO has one actual ordered MP fibre')
                omitted = bad['fibre_cover']['ordered_MP_fibres'].pop()
                mutation = 'required complete ordered_MP_fibres[0] omitted'
                reason = 'complete independent fibres/counts/hashes'
            else:
                bad['complete_cover_proposed'] = False
                mutation = 'complete kind retained while completion flag falsely changed to partial'
                reason = 'literal completion flag'
            expected = 'marked-aware fibre evidence: '+reason
            try:
                check_new(state,row,bad)
            except ValueError as error:
                need(type(error) is ValueError and str(error) == expected,
                     'only exact declared invalid-data rejection counts; callback/resource errors propagate')
                failure = {'mutation':mutation,'failing_proposal':bad,'expected_reason':expected,
                    'exception_type':'ValueError','actual_reason':str(error),'rejected':True,
                    'returned_receipt':None}
                if index == 1: failure['omitted_original_fibre'] = omitted
                failures.append(failure)
            else:
                raise ValueError('new checker accepted deliberately invalid protocol data')
            passed(CALIBRATION_CASES_BY_PURPOSE[plan['purpose']][index],family='NEGATIVE_PROTOCOL')
        families['NEGATIVE_PROTOCOL'] = {'valid_zero_fixture':data,'failures':failures,
            'scope':'Three invalid-data checks only; no callback/timeout is caught or treated as rejection.'}

    need(ax_formula[0]=='all' and ax_formula[1] not in language.parameter_set
         and ax_formula not in marking['definition']['certified_literals'],
         'declaration-derived first named AX has required literal binder and no forbidden-literal match')
    suffix = plan['purpose'].removeprefix('unit-row-marked-aware-calibration-')
    if suffix == 'negative-protocol': call(negative_protocol)
    else: call(positive,(suffix,))
    expected_controls = CALIBRATION_CASES_BY_PURPOSE[plan['purpose']]
    need([c['case'] for c in controls] == expected_controls
         and len(controls) == len(expected_controls) and all(c['status'] == 'PASSED' for c in controls),
         'every essential local calibration assertion completed, without SKIP/substitution')
    calibration = {'schema':'ROOT-unit-row-marked-aware-calibration-payload-v1',
        'stage':'LOCAL_NEW_MARKED_AWARE_NONIMP_DEGREE_ONLY','endpoint_purpose':plan['purpose'],
        'separate_endpoint_count':4,'whole_calibration_qualification_accepted':False,
        'same_process_all_six_qualified':False,
        'prior_acceptance':{k:FIXED_INPUTS[k] for k in FIXED_INPUTS if k.startswith('stageB_')},
        'original_model_sources':ORIGINAL_SOURCES,'original_model_binding':ORIGINAL_BINDING,
        'marking':marking,'definition_check':definition_check,'families':families,
        'controls':controls,'control_count':len(controls),'expected_cases':expected_controls,'all_controls_completed':True,
        'target_search_performed':False,'engine_or_fallback_queried':False,
        'old_degree_proposal_or_receipt_replayed':False,'new_receipt_engine_compatibility_claimed':False,
        'failure_marking_activated':False,'logical_proof_accepted':False,'exact_point_board_accepted':False,
        'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,'RL_accepted':False,
        'GCTS_advantage_claimed':False,'ROOT_resource_accepted':False}
    result_raw = canonical({'schema':'ROOT-unit-row-marked-aware-calibration-result-v1','purpose':plan['purpose'],
        'sources':plan['sources'],'inputs':plan['inputs'],'language_binding':ORIGINAL_BINDING,
        'controls':None,'search':None,'found_validation':None,'marked_aware_calibration':calibration,
        'complete_GCTS_model_accepted':False,'GCTS_search_trajectory_accepted':False,
        'logical_proof_accepted':False,'ROOT_resource_accepted':False})+b'\n'
    result_raw=call(encode_result_transport,(result_raw,))
    run=Path(plan['output_directory']);need(run.is_absolute() and run==run.resolve() and not run.exists(),'fresh canonical owned output')
    run.mkdir(mode=0o700);result_pin=call(write_new,(run/'engine-result.json',result_raw))
    body={'schema':'ROOT-unit-row-marked-aware-calibration-response-body-v1','version':VERSION,
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
    final_raw=canonical({'schema':'ROOT-unit-row-marked-aware-calibration-final-observation-v1',
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
