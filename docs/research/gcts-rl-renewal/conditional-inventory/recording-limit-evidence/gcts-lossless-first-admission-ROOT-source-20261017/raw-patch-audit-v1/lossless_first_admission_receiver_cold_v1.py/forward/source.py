"""One separately granted real receiver-search probe with a reused inventory.
Full original model; actual global decisions; no supplied proof or receiver route."""
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
VERSION='ROOT-receiver-inference-probe-cold-v6-lossless-first-admission-journal'
SCOPE='ROOT-receiver-inference-probe-Source'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
CANCELLED=False
QUALIFICATION_CASES_BY_PURPOSE={'receptor-inference-visible-probe': ['RI-01-visible-observed-port-inference'], 'receptor-inference-literal-probe': ['RI-02-literal-origin-binding-control']}
FIXED={'clean_support': {'bytes': 48584, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-global-clock-lane-A-source-20261015/Q_clean_word_verifier_global_clock_v4.py', 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'}, 'decorator': {'bytes': 12619, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-certified-mark-decorator-source-20261016/certified_row0_point_mark_decorator_v1.py', 'sha256': 'fcc4aeb3275f47cbdba26436e2224bffad91e80974e873d2d57d9263151a3895'}, 'degree_checker': {'bytes': 27553, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-checker-source-20261015/independent_unit_row_missing_mark_checker_v2.py', 'sha256': 'c35484000d8ab924d089ace9a185132ef164cad1e24729123290215b8baf8f6d'}, 'degree_router': {'bytes': 12779, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-aware-router-engine-source-20261016/marked_degree_router_v1.py', 'sha256': 'a56d7f08779bb0f47c23a1bb8f1ce73cd9f214154dbc1d7efa6be99d2748c150'}, 'expansion_checker': {'bytes': 56670, 'path': '/private/tmp/gcts-current-source-pool-20261017/independent_receptor_family_expansion_checker_v1.py', 'sha256': '4358026b3eeb9c96366d522c65b5f6d6d4acd7336a0816360da5cd44233a93b1'}, 'fallback': {'bytes': 24227, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-all-six-fallback-source-20261015/unit_row_all_six_fallback_v1.py', 'sha256': '69b4a9170d931e01138f5d7f98514f26e47cbfe7ab8b7503b99f6a24934a4fae'}, 'family_consumer': {'bytes': 13040, 'path': '/private/tmp/gcts-current-source-pool-20261017/receptor_family_preference_consumer_v2.py', 'sha256': 'd68095aae1855c2469cf3b160818e202231cb0883c7242a8f0b6ee130903e874'}, 'family_engine': {'bytes': 98533, 'path': '/private/tmp/gcts-first-admission-journal-engine-source-20261017/receptor_family_search_engine_v8.py', 'sha256': '9fd543e42db1e8f657a36cd081c7f9bd4621bb22b97e4daabe5a8856e944eb7f'}, 'head_gate': {'bytes': 15276, 'path': '/private/tmp/gcts-coarse-head-plan-marks-source-20261017/coarse_formula_head_plan_marks_v1.py', 'sha256': '7595f771bd09953ffb736cd18c66ebedb19e7b51407c977f61f5ea8108416738'}, 'host_adapter': {'bytes': 25205, 'path': '/private/tmp/gcts-current-source-pool-20261017/receptor_family_six_rule_adapter_v3.py', 'sha256': '4bd6c6fe723b17da0afec54fb0409f33dcb01e699e774f673e8de12c33efeba9'}, 'kernel': {'bytes': 10323, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py', 'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'}, 'marked_adapter': {'bytes': 31038, 'path': '/private/tmp/gcts-marked-prefix-census-source-20261017/marked_unit_row_adapter_v5.py', 'sha256': '7e508c4a099a20b250e7e679277a1e0dc3346207256c4660106b220ffc697b24'}, 'marked_aware_checker': {'bytes': 25783, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-aware-fibre-checker-source-20261016/independent_marked_aware_fibre_checker_v1.py', 'sha256': '8f7a06a28bebb2558a4d2acdae58be4c793d0179f1616b2625d5cb1ee80e9188'}, 'marked_aware_proposer': {'bytes': 14064, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-aware-fibre-proposer-source-20261016/marked_aware_nonimp_fibre_proposer_v1.py', 'sha256': '4316adcc791b8e078cd2bc5ebade234ae24936c2195b6be9addc25b12a0cbd1d'}, 'marked_verifier': {'bytes': 18475, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-state-verifier-source-20261016/independent_channel4_state_verifier_v1.py', 'sha256': '9fd60cad12881e3519c785c417b3348bd013a5ff0b8aa993399276e266da9a6a'}, 'membership': {'bytes': 20112, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-implementation-source-20261015/bounded_six_rule_language_v2.py', 'sha256': '5d1fb647626c952f4653dd8cffabdb3fe29be0be122ef7e73ef4a7759da43332'}, 'producer': {'bytes': 60281, 'path': '/private/tmp/gcts-observed-subset-expander-source-20261017/receptor_family_expander_v2.py', 'sha256': 'fd3eb85497b9845422d56ab3d734a84a8c0a358f4931bc8b61243d66eacaff18'}, 'proposer': {'bytes': 22030, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-missing-mark-degree-source-20261015/unit_row_missing_mark_degree_v3.py', 'sha256': 'c960e6e6560502f95f25611c9c85a72b32c67775aedc2e42e0300a366e3d7e90'}, 'receiver_cases': {'bytes': 8872, 'path': '/private/tmp/gcts-engine-milestone-helper-source-20261017/engine_milestone_receiver_cases_v1.py', 'sha256': '1685db2acce5bf8425f45cbf58cf4d28944132e2309ba613689da1068d61fbfb'}, 'receiver_provider': {'bytes': 60912, 'path': '/private/tmp/gcts-head-gated-provider-source-20261017/receptor_transfer_physical_provider_v8.py', 'sha256': 'fd38402191e68567f62029dc19391942b4cdd3f0d1d23dcd9df5d4b1e3c268e0'}, 'residual_policy': {'bytes': 12826, 'path': '/private/tmp/gcts-residual-binding-prefix-source-20261017/residual_binding_prefix_v2.py', 'sha256': '2925609b1ec3cb0957b1030bcfcf8a4bfc2ea4b29f35ec3b44e30ed776bdd479'}}
FIXED_INPUTS={'declaration': {'bytes': 2925, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-right-two-preparation-source-20261015/Q-right-two-declaration-v1.json', 'sha256': 'a1ce8237aca64485f94cbce0c909a055a74318ca0cc39b99cf0dc1990323d3df'}, 'profile': {'bytes': 8773, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/shared-bounded-language-ROOT-20261015/ROOT-profile-choice-v2.json', 'sha256': '227b3d4c1e8f5491365b5da580f59367300840d43d388d94e0657cf1b5f89c02'}, 'stageB_disposition': {'bytes': 4574, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageB-qualification-ROOT-20261016/ROOT-stageB-disposition-v1.json', 'sha256': 'ecb994c6ada2835db51c7a2d8ada6f7833d9945635449ba9be448da0dee6193e'}, 'stageB_encoded': {'bytes': 162591, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageB-qualification-ROOT-20261016/stageB-owned-v1/engine-result.json', 'sha256': '3515e77e2554df1b588311772e38f12a401039ca9e2c106227ff0a16e7a149ca'}, 'stageB_expanded': {'bytes': 1926833, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageB-qualification-ROOT-20261016/ROOT-stageB-expanded-result-v1.json', 'sha256': 'bb64b73377940ae6833ae2b30d1bd96396dabffe3e7f773bdfaa640327d8ad93'}, 'stageB_plan': {'bytes': 7924, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageB-qualification-ROOT-20261016/ROOT-stageB-plan-v1.json', 'sha256': '7047504acb8527a7476a7cb24c8031d6b5796150f9f0ce07b914bbd955e5d009'}, 'stageB_response': {'bytes': 7572, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageB-qualification-ROOT-20261016/stageB-owned-v1/response.jsonl', 'sha256': '8ca1ac71fa5a4c1734b68460cf029cfa2e1da0cf7e0670ab53e956f43d95435e'}, 'stageB_transport': {'bytes': 1502, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-channel4-stageB-qualification-ROOT-20261016/ROOT-stageB-transport-concordance-v1.json', 'sha256': '8704567e955cab88e42cd867a4cd28d2911e4afffa286b87b2b27b1b5afda08b'}, 'frozen_inventory': {'path': '/private/tmp/gcts-native-productive-inventory-work4m-ROOT-20261017/ROOT-expanded-result-v1.json', 'sha256': '26a3898bf0266621193c6320f64e8446d518f44123a21a7115ef10bd07153b38', 'bytes': 3433689}, 'inventory_acceptance': {'path': '/private/tmp/gcts-native-productive-inventory-work4m-ROOT-20261017/ROOT-source-ground-acceptance-v1.json', 'sha256': '4ef4ebdcd431a284f73ded43caf1957b819d1ddd4e3180e212a619e3b736d817', 'bytes': 2723}}
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
        _compress=zlib.compress, _compress_anchor=zlib.compress,
        _b64=binascii.b2a_base64, _b64_anchor=binascii.b2a_base64,
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
    elif failure_kind == 'CONTROLS_TIMEOUT_PROVIDER_RETURNS_V2':
        roles = ('proposer','fallback','completion','validator')
        counters = ('planned_assignments','attempted_assignments','binding_attempts',
            'ground_environment_proposals','distinct_environment_attempts','full_expansions',
            'checked_expansions','preflight_checks','native_member_exclusions','native_adaptations',
            'checked_instances','duplicate_instances','offered_instances','head_gate_calls',
            'head_gate_receipts_returned','head_gate_conflicting_plans','head_gate_no_known_conflict',
            'head_gate_unknown','head_gate_absent_head_passes','head_gate_downstream_assignments')
        if (type(capture) is not dict or len(capture) != 2
                or not all(type(key) is str for key in capture)
                or set(capture) != {'legacy','provider_returns'}):
            raise ValueError('fixed builtin provider-return capture')
        legacy = capture['legacy']; returned = capture['provider_returns']
        if (type(legacy) is not dict or len(legacy) != 4
                or not all(type(key) is str for key in legacy) or set(legacy) != set(roles)
                or type(returned) is not list or len(returned) != 2):
            raise ValueError('fixed legacy and two provider-return slots')
        observations = {}
        for role in roles:
            failure_gate()
            item = legacy[role]
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
        summaries = []
        for index in range(2):
            failure_gate()
            item = returned[index]
            if item is None:
                summaries.append(None)
                continue
            if (type(item) is not dict or len(item) != 7
                    or not all(type(key) is str for key in item)
                    or set(item) != {'ordinal','native_ns','batch_status','instance_count',
                        'provider_reason','provider_steps','accounting'}):
                raise ValueError('fixed builtin provider-return fields')
            ordinal = item['ordinal']; native_ns = item['native_ns']; counts = item['accounting']
            if (type(ordinal) is not int or ordinal != index+1
                    or type(native_ns) is not int or not began_ns<=native_ns<began_ns+20000000000
                    or not 0<=native_ns<=9223372036854775807
                    or type(item['batch_status']) is not str or len(item['batch_status'])>64
                    or type(item['instance_count']) is not int or not 0<=item['instance_count']<=1
                    or type(item['provider_reason']) is not str or len(item['provider_reason'])>256
                    or type(item['provider_steps']) is not int or not 0<=item['provider_steps']<=1000000
                    or type(counts) is not dict or len(counts) != 20
                    or not all(type(key) is str for key in counts) or set(counts) != set(counters)
                    or not all(type(counts[key]) is int and 0<=counts[key]<=1000000 for key in counters)):
                raise ValueError('bounded builtin provider-return scalars')
            summaries.append({'ordinal':ordinal,'native_ns':native_ns,
                'batch_status':item['batch_status'],'instance_count':item['instance_count'],
                'provider_reason':item['provider_reason'],'provider_steps':item['provider_steps'],
                'accounting':{key:counts[key] for key in counters}})
        labels = encoded({'schema':'unit-row-controls-provider-returns-diagnostic-v2',
            'diagnostic_only':True,'qualification':'UNQUALIFIED_LITERAL_PROVIDER_RETURN_SCALARS',
            'failure_kind':'TimeoutError','returned_control_record':False,
            'callback_context':'LITERAL_RETURNED_SCALARS_ONLY_NOT_FULL_RECEIPTS',
            'provider_return_summaries_are_unvalidated_scalars':True,
            'last_observation_is_active_failure_frame':False,'callback_return_to_engine_proved':False,
            'offers_accepted':False,'current_state_accepted':False,'failure_cause_established':False,
            'live_state_or_proof_trajectory_accepted':False,
            'positive_joint_gate_accepted':False,'logical_proof_accepted':False,
            'exact_point_board_accepted':False,'complete_GCTS_model_accepted':False,
            'GCTS_search_trajectory_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False},4096)
        raw = (b'{"context":'+context_raw+b',"diagnostic":'+labels
               +b',"last_observations":'+encoded(observations,4096)
               +b',"provider_returns":'+encoded(summaries,8192)+b'}\n')
        # Sum of the four independently bounded values and their exact JSON wrapper.
        if len(raw)>81988:raise ValueError('whole provider-return diagnostic byte bound')
    elif failure_kind == 'CONTROLS_TIMEOUT_ENGINE_MILESTONES_LOSSLESS_V4':
        roles = ('proposer','fallback','completion','validator')
        counters = ('planned_assignments','attempted_assignments','binding_attempts',
            'ground_environment_proposals','distinct_environment_attempts','full_expansions',
            'checked_expansions','preflight_checks','native_member_exclusions','native_adaptations',
            'checked_instances','duplicate_instances','offered_instances','head_gate_calls',
            'head_gate_receipts_returned','head_gate_conflicting_plans','head_gate_no_known_conflict',
            'head_gate_unknown','head_gate_absent_head_passes','head_gate_downstream_assignments')
        if (type(capture) is not dict or len(capture) != 3
                or not all(type(key) is str for key in capture)
                or set(capture) != {'legacy','provider_returns','engine_milestones'}):
            raise ValueError('fixed builtin provider-return capture')
        legacy = capture['legacy']; returned = capture['provider_returns']
        if (type(legacy) is not dict or len(legacy) != 4
                or not all(type(key) is str for key in legacy) or set(legacy) != set(roles)
                or type(returned) is not list or len(returned) != 2):
            raise ValueError('fixed legacy and two provider-return slots')
        observations = {}
        for role in roles:
            failure_gate()
            item = legacy[role]
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
        summaries = []
        for index in range(2):
            failure_gate()
            item = returned[index]
            if item is None:
                summaries.append(None)
                continue
            if (type(item) is not dict or len(item) != 7
                    or not all(type(key) is str for key in item)
                    or set(item) != {'ordinal','native_ns','batch_status','instance_count',
                        'provider_reason','provider_steps','accounting'}):
                raise ValueError('fixed builtin provider-return fields')
            ordinal = item['ordinal']; native_ns = item['native_ns']; counts = item['accounting']
            if (type(ordinal) is not int or ordinal != index+1
                    or type(native_ns) is not int or not began_ns<=native_ns<began_ns+20000000000
                    or not 0<=native_ns<=9223372036854775807
                    or type(item['batch_status']) is not str or len(item['batch_status'])>64
                    or type(item['instance_count']) is not int or not 0<=item['instance_count']<=1
                    or type(item['provider_reason']) is not str or len(item['provider_reason'])>256
                    or type(item['provider_steps']) is not int or not 0<=item['provider_steps']<=1000000
                    or type(counts) is not dict or len(counts) != 20
                    or not all(type(key) is str for key in counts) or set(counts) != set(counters)
                    or not all(type(counts[key]) is int and 0<=counts[key]<=1000000 for key in counters)):
                raise ValueError('bounded builtin provider-return scalars')
            summaries.append({'ordinal':ordinal,'native_ns':native_ns,
                'batch_status':item['batch_status'],'instance_count':item['instance_count'],
                'provider_reason':item['provider_reason'],'provider_steps':item['provider_steps'],
                'accounting':{key:counts[key] for key in counters}})
        stages = ('FIRST_ROOT_FAMILY_PLAN_READY','FIRST_ROOT_FAMILY_EVENT_READY',
            'FIRST_ROOT_PRIMITIVE_PLACED','FIRST_CHILD_DECISION_READY')
        milestones = capture['engine_milestones']
        if type(milestones) is not list or len(milestones) != 4:
            raise ValueError('fixed four raw engine milestone slots')
        headers = []; captured = 0; ended = False; previous_ns = began_ns
        for index in range(4):
            failure_gate()
            item = milestones[index]
            if item is None:
                ended = True; headers.append(None); continue
            if (ended or type(item) is not dict or len(item) != 4
                    or not all(type(key) is str for key in item)
                    or set(item) != {'ordinal','stage','native_ns','record'}
                    or type(item['ordinal']) is not int or item['ordinal'] != index+1
                    or type(item['stage']) is not str or item['stage'] != stages[index]
                    or type(item['native_ns']) is not int
                    or not previous_ns<=item['native_ns']<began_ns+20000000000
                    or not 0<=item['native_ns']<=9223372036854775807
                    or type(item['record']) is not dict):
                raise ValueError('literal monotone-prefix raw milestone headers')
            headers.append({'ordinal':index+1,'stage':item['stage'],'native_ns':item['native_ns']})
            previous_ns=item['native_ns']; captured+=1
        # Only this new V4 branch changes encoding. Legacy/V3 stays literal.
        def codec_gate():
            failure_gate()
            if (type(_compress) is not types.BuiltinFunctionType or _compress is not _compress_anchor
                    or type(_b64) is not types.BuiltinFunctionType or _b64 is not _b64_anchor):
                raise RuntimeError('original captured lossless codec endpoint changed')
        def journal_item(value, maximum, ordinal):
            chunks=[];size=0;nodes=0;omission=None
            def reject(code, limit, observed):
                nonlocal omission
                if omission is None:
                    omission={'phase':'BUILTIN_SERIALIZATION','code':code,
                        'record_ordinal':ordinal,'limit':limit,'observed':observed}
                return False
            def append(raw):
                nonlocal size
                size+=len(raw)
                if size>maximum:return reject('EXPANDED_BYTE_LIMIT',maximum,size)
                chunks.append(raw);return True
            def visit(item, depth):
                nonlocal nodes
                nodes+=1
                if nodes>200000:return reject('NODE_LIMIT',200000,nodes)
                if depth>128:return reject('DEPTH_LIMIT',128,depth)
                if nodes%64==1:failure_gate()
                kind=type(item)
                if item is None:return append(b'null')
                if kind is bool:return append(b'true'if item else b'false')
                if kind is int:
                    bits=item.bit_length()
                    if bits>4096:return reject('INTEGER_BIT_LIMIT',4096,bits)
                    return append(str(item).encode('ascii'))
                if kind is str:
                    if len(item)>262144:return reject('STRING_LENGTH_LIMIT',262144,len(item))
                    return append(_escape(item).encode('ascii'))
                if kind is list or kind is dict:
                    if not append(b'['if kind is list else b'{'):return False
                    for index,entry in enumerate(item if kind is list else item.items()):
                        if index and not append(b','):return False
                        if kind is dict:
                            key,child=entry
                            if type(key)is not str:return reject('NON_STRING_KEY',None,'NON_STRING_KEY')
                            if not visit(key,depth+1)or not append(b':')or not visit(child,depth+1):return False
                        elif not visit(entry,depth+1):return False
                    return append(b']'if kind is list else b'}')
                return reject('NON_BUILTIN_VALUE',None,'UNSUPPORTED')
            complete=visit(value,0);failure_gate()
            if not complete:return None,omission
            return b''.join(chunks),None
        journal=[b'null',b'null',b'null',b'null'];journal_bytes=21
        candidate_prefix=0;serialization_omission=None;wire_omission=None
        for index in range(captured):
            failure_gate()
            item_raw,serialization_omission=journal_item(milestones[index],16777216-journal_bytes+4,index+1)
            if serialization_omission is not None:break
            journal[index]=item_raw;journal_bytes+=len(item_raw)-4;candidate_prefix+=1
        journal_raw=b'['+b','.join(journal)+b']'
        if len(journal_raw)!=journal_bytes or journal_bytes>16777216:
            raise RuntimeError('lossless expanded journal exact byte accounting')
        journal=[];item_raw=None
        codec_gate();expanded_sha=_hash(journal_raw).hexdigest();codec_gate()
        codec_gate();compressed=_compress(journal_raw,6);codec_gate()
        if type(compressed)is not bytes:raise RuntimeError('captured compressor returned nonbytes')
        journal_raw=None
        codec_gate();compressed_sha=_hash(compressed).hexdigest();codec_gate()
        envelope_prefix=encoded({'schema':'unit-row-engine-milestone-lossless-envelope-v1',
            'encoding':'zlib+base64','expanded_bytes':journal_bytes,'expanded_sha256':expanded_sha,
            'compressed_bytes':len(compressed),'compressed_sha256':compressed_sha},4096)[:-1]+b',"payload_base64":"'
        envelope_suffix=b'"}'
        projected=len(envelope_prefix)+4*((len(compressed)+2)//3)+len(envelope_suffix)
        envelope_raw=None;retained=0
        if projected>3145728:
            wire_omission={'phase':'ENCODED_ENVELOPE','code':'ENCODED_ENVELOPE_BYTE_LIMIT',
                'record_ordinal':1 if captured else None,'limit':3145728,'observed':projected}
        else:
            codec_gate();payload=_b64(compressed,newline=False);codec_gate()
            if type(payload)is not bytes or len(payload)!=4*((len(compressed)+2)//3):
                raise RuntimeError('captured base64 exact whole length')
            envelope_raw=envelope_prefix+payload+envelope_suffix
            if len(envelope_raw)!=projected or len(envelope_raw)>3145728:
                raise RuntimeError('lossless encoded envelope exact byte accounting')
            retained=candidate_prefix
        compressed=None;payload=None
        prefix_reason=('ENCODED_ENVELOPE_BYTE_LIMIT'if wire_omission is not None else
            'OWN_PRIMITIVE_SERIALIZATION_LIMIT'if serialization_omission is not None else 'ALL_CAPTURED_RECORDS_SAVED')
        labels=encoded({'schema':'unit-row-controls-engine-milestones-diagnostic-v4',
            'diagnostic_only':True,'qualification':'UNQUALIFIED_LITERAL_ENGINE_MILESTONE_RECORDS',
            'failure_kind':'TimeoutError','returned_control_record':False,
            'callback_context':'LITERAL_RETURNED_SCALARS_AND_RAW_ENGINE_RECORDS_ONLY',
            'provider_return_summaries_are_unvalidated_scalars':True,'engine_milestone_records_are_unvalidated':True,
            'captured_headers':headers,'captured_record_count':captured,
            'encoded_candidate_prefix_count':candidate_prefix,'serialized_record_count':retained,
            'omitted_record_count':captured-retained,'next_omitted_ordinal':retained+1 if retained<captured else None,
            'engine_record_prefix_reason':prefix_reason,'engine_journal_bytes':journal_bytes if envelope_raw is not None else None,
            'expanded_candidate_bytes':journal_bytes,'encoded_envelope_bytes':None if envelope_raw is None else len(envelope_raw),
            'serialization_omission':serialization_omission,'wire_omission':wire_omission,
            'last_observation_is_active_failure_frame':False,'callback_return_to_engine_proved':False,
            'offers_accepted':False,'current_state_accepted':False,'failure_cause_established':False,
            'live_state_or_proof_trajectory_accepted':False,'positive_joint_gate_accepted':False,
            'logical_proof_accepted':False,'exact_point_board_accepted':False,'complete_GCTS_model_accepted':False,
            'GCTS_search_trajectory_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False},65536)
        raw=(b'{"context":'+context_raw+b',"diagnostic":'+labels
            +b',"last_observations":'+encoded(observations,4096)+b',"provider_returns":'+encoded(summaries,8192)
            +b',"engine_milestones_envelope":'+(b'null'if envelope_raw is None else envelope_raw)+b'}\n')
    elif failure_kind == 'CONTROLS_TIMEOUT_ENGINE_MILESTONES_V3':
        roles = ('proposer','fallback','completion','validator')
        counters = ('planned_assignments','attempted_assignments','binding_attempts',
            'ground_environment_proposals','distinct_environment_attempts','full_expansions',
            'checked_expansions','preflight_checks','native_member_exclusions','native_adaptations',
            'checked_instances','duplicate_instances','offered_instances','head_gate_calls',
            'head_gate_receipts_returned','head_gate_conflicting_plans','head_gate_no_known_conflict',
            'head_gate_unknown','head_gate_absent_head_passes','head_gate_downstream_assignments')
        if (type(capture) is not dict or len(capture) != 3
                or not all(type(key) is str for key in capture)
                or set(capture) != {'legacy','provider_returns','engine_milestones'}):
            raise ValueError('fixed builtin provider-return capture')
        legacy = capture['legacy']; returned = capture['provider_returns']
        if (type(legacy) is not dict or len(legacy) != 4
                or not all(type(key) is str for key in legacy) or set(legacy) != set(roles)
                or type(returned) is not list or len(returned) != 2):
            raise ValueError('fixed legacy and two provider-return slots')
        observations = {}
        for role in roles:
            failure_gate()
            item = legacy[role]
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
        summaries = []
        for index in range(2):
            failure_gate()
            item = returned[index]
            if item is None:
                summaries.append(None)
                continue
            if (type(item) is not dict or len(item) != 7
                    or not all(type(key) is str for key in item)
                    or set(item) != {'ordinal','native_ns','batch_status','instance_count',
                        'provider_reason','provider_steps','accounting'}):
                raise ValueError('fixed builtin provider-return fields')
            ordinal = item['ordinal']; native_ns = item['native_ns']; counts = item['accounting']
            if (type(ordinal) is not int or ordinal != index+1
                    or type(native_ns) is not int or not began_ns<=native_ns<began_ns+20000000000
                    or not 0<=native_ns<=9223372036854775807
                    or type(item['batch_status']) is not str or len(item['batch_status'])>64
                    or type(item['instance_count']) is not int or not 0<=item['instance_count']<=1
                    or type(item['provider_reason']) is not str or len(item['provider_reason'])>256
                    or type(item['provider_steps']) is not int or not 0<=item['provider_steps']<=1000000
                    or type(counts) is not dict or len(counts) != 20
                    or not all(type(key) is str for key in counts) or set(counts) != set(counters)
                    or not all(type(counts[key]) is int and 0<=counts[key]<=1000000 for key in counters)):
                raise ValueError('bounded builtin provider-return scalars')
            summaries.append({'ordinal':ordinal,'native_ns':native_ns,
                'batch_status':item['batch_status'],'instance_count':item['instance_count'],
                'provider_reason':item['provider_reason'],'provider_steps':item['provider_steps'],
                'accounting':{key:counts[key] for key in counters}})
        stages = ('FIRST_ROOT_FAMILY_PLAN_READY','FIRST_ROOT_FAMILY_EVENT_READY',
            'FIRST_ROOT_PRIMITIVE_PLACED','FIRST_CHILD_DECISION_READY')
        milestones = capture['engine_milestones']
        if type(milestones) is not list or len(milestones) != 4:
            raise ValueError('fixed four raw engine milestone slots')
        headers = []; captured = 0; ended = False; previous_ns = began_ns
        for index in range(4):
            failure_gate()
            item = milestones[index]
            if item is None:
                ended = True; headers.append(None); continue
            if (ended or type(item) is not dict or len(item) != 4
                    or not all(type(key) is str for key in item)
                    or set(item) != {'ordinal','stage','native_ns','record'}
                    or type(item['ordinal']) is not int or item['ordinal'] != index+1
                    or type(item['stage']) is not str or item['stage'] != stages[index]
                    or type(item['native_ns']) is not int
                    or not previous_ns<=item['native_ns']<began_ns+20000000000
                    or not 0<=item['native_ns']<=9223372036854775807
                    or type(item['record']) is not dict):
                raise ValueError('literal monotone-prefix raw milestone headers')
            headers.append({'ordinal':index+1,'stage':item['stage'],'native_ns':item['native_ns']})
            previous_ns=item['native_ns']; captured+=1
        journal = [b'null',b'null',b'null',b'null']; journal_bytes = 21
        serialized = 0; prefix_reason = 'ALL_CAPTURED_RECORDS_SAVED'
        for index in range(captured):
            failure_gate()
            try:
                item_raw = encoded(milestones[index],3*1048576)
            except ValueError:
                prefix_reason = 'NEXT_RECORD_OUTPUT_BOUND_OR_BUILTIN_TYPE'; break
            if journal_bytes+len(item_raw)-4 > 3*1048576:
                prefix_reason = 'ENGINE_JOURNAL_AGGREGATE_BYTE_LIMIT'; break
            journal[index]=item_raw; journal_bytes+=len(item_raw)-4; serialized+=1
        journal_raw=b'['+b','.join(journal)+b']'
        if len(journal_raw)!=journal_bytes:raise ValueError('literal journal byte accounting')
        labels = encoded({'schema':'unit-row-controls-engine-milestones-diagnostic-v3',
            'diagnostic_only':True,'qualification':'UNQUALIFIED_LITERAL_ENGINE_MILESTONE_RECORDS',
            'failure_kind':'TimeoutError','returned_control_record':False,
            'callback_context':'LITERAL_RETURNED_SCALARS_AND_RAW_ENGINE_RECORDS_ONLY',
            'provider_return_summaries_are_unvalidated_scalars':True,
            'engine_milestone_records_are_unvalidated':True,
            'captured_headers':headers,'captured_record_count':captured,
            'serialized_record_count':serialized,'omitted_record_count':captured-serialized,
            'next_omitted_ordinal':serialized+1 if serialized<captured else None,
            'engine_record_prefix_reason':prefix_reason,'engine_journal_bytes':journal_bytes,
            'last_observation_is_active_failure_frame':False,'callback_return_to_engine_proved':False,
            'offers_accepted':False,'current_state_accepted':False,'failure_cause_established':False,
            'live_state_or_proof_trajectory_accepted':False,
            'positive_joint_gate_accepted':False,'logical_proof_accepted':False,
            'exact_point_board_accepted':False,'complete_GCTS_model_accepted':False,
            'GCTS_search_trajectory_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False},65536)
        raw = (b'{"context":'+context_raw+b',"diagnostic":'+labels
               +b',"last_observations":'+encoded(observations,4096)
               +b',"provider_returns":'+encoded(summaries,8192)
               +b',"engine_milestones":'+journal_raw+b'}\n')
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
    marker = encoded({'schema':('unit-row-controls-last-context-completion-v1' if failure_kind == 'CONTROLS_TIMEOUT_LAST_SCALARS' else 'unit-row-controls-provider-returns-completion-v2' if failure_kind == 'CONTROLS_TIMEOUT_PROVIDER_RETURNS_V2' else 'unit-row-controls-engine-milestones-completion-v4' if failure_kind == 'CONTROLS_TIMEOUT_ENGINE_MILESTONES_LOSSLESS_V4' else 'unit-row-controls-engine-milestones-completion-v3' if failure_kind == 'CONTROLS_TIMEOUT_ENGINE_MILESTONES_V3' else 'unit-row-search-failure-diagnostic-completion-v1'),
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
    phase_tick,phase_tick_code=tick,tick.__code__
    phase_tick_defaults,phase_tick_kwdefaults=tick.__defaults__,tick.__kwdefaults__
    phase_write,phase_write_type=os.write,types.BuiltinFunctionType
    phase_labels=('BEFORE_PLAN_READ', 'BEFORE_CURRENT_SOURCE_READS', 'BEFORE_AUTHORITY_INPUT_READS', 'BEFORE_MODULE_LOAD', 'BEFORE_GUARD_CONSTRUCTION', 'BEFORE_STAGEB_PROVENANCE', 'BEFORE_MARKING_CHECK', 'BEFORE_POOL_READ', 'BEFORE_ENGINE', 'BEFORE_PROVIDER', 'AFTER_PROVIDER', 'AFTER_ENGINE', 'BEFORE_OUTPUT', 'P1_ENTER', 'P1_DELEGATE_RETURN', 'P1_CALLBACK_READY', 'P2_ENTER', 'P2_DELEGATE_RETURN', 'P2_CALLBACK_READY', 'C1_ENTER', 'C1_DELEGATE_RETURN', 'C1_CALLBACK_READY', 'C2_ENTER', 'C2_DELEGATE_RETURN', 'C2_CALLBACK_READY', 'C3_ENTER', 'C3_DELEGATE_RETURN', 'C3_CALLBACK_READY', 'SEARCH_RETURN_OBSERVED', 'POSTSEARCH_SNAPSHOT_READY', 'M1_PLAN_READY', 'M2_EVENT_READY', 'M3_PLACE_RETURN', 'M4_CHILD_DECISION')
    def phase(stage):
        if (tick is not phase_tick or phase_tick.__code__ is not phase_tick_code
                or phase_tick.__defaults__ is not phase_tick_defaults
                or phase_tick.__kwdefaults__ is not phase_tick_kwdefaults
                or os.write is not phase_write or type(phase_write)is not phase_write_type):
            raise RuntimeError('original connected diagnostic native endpoints changed')
        native_ns=phase_tick()
        need(type(stage)is str and stage in phase_labels and type(native_ns)is int
             and 0<=native_ns<=9223372036854775807,'fixed connected phase/native sample')
        raw=('COMPONENT_INVENTORY_PHASE '+stage+' '+str(native_ns)+'\n').encode('ascii')
        offset=0
        while offset<len(raw):
            phase_tick()
            if os.write is not phase_write or type(phase_write)is not phase_write_type:
                raise RuntimeError('original connected diagnostic write endpoint changed')
            count=phase_write(2,raw[offset:]);need(type(count)is int and count>0,'complete bounded phase write')
            offset+=count
        phase_tick()
    phase('BEFORE_PLAN_READ')
    path=Path(argv[0]);need(path.is_absolute() and path==path.resolve(),'canonical Root plan path')
    plan_raw=path.read_bytes();need(len(plan_raw)<=1048576,'whole bounded Root plan');plan=decode(plan_raw)
    need(set(plan)=={'schema','invocation_id','purpose','output_directory','sources','inputs','source_contract',
        'reviews','ROOT_authorization','runtime','limits','resource_rule'},'exact current plan12')
    need(plan['schema']=='ROOT-routed-engine-qualification-plan-v1'
         and plan['purpose'] in QUALIFICATION_CASES_BY_PURPOSE
         and plan['resource_rule']=='single-owned-process-native-terminal-v1'
         and plan['limits']==LIMITS and all(type(v) is int for v in plan['limits'].values()),'original six limits')
    need(type(plan['invocation_id']) is str and 1<=len(plan['invocation_id'])<=128
         and all(c.isascii() and (c.isalnum() or c in '-_.:') for c in plan['invocation_id']),'strict actual nonce')
    need(set(plan['sources'])=={'intake',*FIXED}
         and all(plan['sources'][k]==v for k,v in FIXED.items())
         and plan['sources']['intake']['path']==str(Path(__file__).resolve())
         and plan['inputs']==FIXED_INPUTS,'exact current executable Sources and saved inputs')
    need(sys.platform=='darwin' and Path(sys.executable).resolve()==Path(plan['runtime']['path']).resolve(),'native Darwin runtime')
    read_pinned(plan['runtime'])
    phase('BEFORE_CURRENT_SOURCE_READS')
    source_raw={role:read_pinned(ref) for role,ref in plan['sources'].items()}
    contract=decode(read_pinned(plan['source_contract']))
    need(contract['schema']=='ROOT-receiver-inference-probe-Source-contract-v1'
         and contract['sources']==plan['sources'] and contract['inputs']==FIXED_INPUTS
         and contract['limits']==LIMITS and contract['original_model_sources']==ORIGINAL_SOURCES
         and contract['original_model_inputs']==ORIGINAL_INPUTS
         and contract['original_model_binding']==ORIGINAL_BINDING,'whole current and original-model contract')
    need(set(plan['reviews'])=={'ROOT','peer'},'Root review and distinct whole-Source peer')
    for role,ref in plan['reviews'].items():
        review=decode(read_pinned(ref))
        need(review['scope']==SCOPE and review['author_identity']=='/root'
             and review['source']==plan['sources']['intake'] and review['sources']==plan['sources']
             and review['source_contract']==plan['source_contract'] and review['source_only'] is True
             and review['source_review_passed'] is True and type(review['scientific_calls']) is int
             and review['scientific_calls']==0 and review['scientific_acceptance'] is False
             and (review['reviewer_identity']=='/root' if role=='ROOT' else review['reviewer_identity'] != '/root'),
             'genuine current scoped Source reviews')
    grant=decode(read_pinned(plan['ROOT_authorization']))
    need(grant['schema']=='ROOT-routed-engine-qualification-authorization-v1'
         and grant['author_identity']=='/root' and grant['actual_execution_authorized'] is True
         and type(grant['maximum_actual_invocations']) is int and grant['maximum_actual_invocations']==1
         and all(grant[k]==plan[k] for k in ('invocation_id','purpose','sources','inputs','source_contract',
             'reviews','runtime','limits','resource_rule','output_directory')),'exact once-only Root actual grant')
    phase('BEFORE_AUTHORITY_INPUT_READS')
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
    phase('BEFORE_MODULE_LOAD')
    modules={role:load_module(role,source_raw[role]) for role in FIXED}
    support,kernel,membership,semantics=(modules[k] for k in ('clean_support','kernel','membership','degree_checker'))
    phase('BEFORE_GUARD_CONSTRUCTION')
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
    phase('BEFORE_STAGEB_PROVENANCE')
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
    adapter, fallback = (modules[k] for k in ('marked_adapter','fallback'))
    decorator, verifier = modules['decorator'], modules['marked_verifier']
    need(adapter.VERSION == 'unit-row-channel4-point-adapter-v1'
         and adapter.IMPLEMENTATION_VERSION == 'unit-row-channel4-point-adapter-public-prefix-census-v5',
         'current reviewed public-prefix adapter version')
    phase('BEFORE_MARKING_CHECK')
    definition_check = call(verifier.check_marking,kwargs={'language':fresh_language(),
        'semantics':semantics,'marking':copy.deepcopy(marking),'tick':tick})
    need(definition_check['marking_checked'] is True and definition_check['marking_id'] == marking['marking_id'],
         'fresh independent whole marking check')
    latest_observations={'proposer':None,'fallback':None,'completion':None,'validator':None}
    provider_return_slots=[None,None]
    diagnostic_capture={'legacy':latest_observations,'provider_returns':provider_return_slots}
    summary_counters=('planned_assignments','attempted_assignments','binding_attempts',
        'ground_environment_proposals','distinct_environment_attempts','full_expansions',
        'checked_expansions','preflight_checks','native_member_exclusions','native_adaptations',
        'checked_instances','duplicate_instances','offered_instances','head_gate_calls',
        'head_gate_receipts_returned','head_gate_conflicting_plans','head_gate_no_known_conflict',
        'head_gate_unknown','head_gate_absent_head_passes','head_gate_downstream_assignments')
    def capture_provider_summary(ordinal,value):
        # Original20 metadata only. Never traverse/copy/hash or mutate the report.
        # An absent slot never blocks the existing scientific callback.
        if (tick is not phase_tick or phase_tick.__code__ is not phase_tick_code
                or phase_tick.__defaults__ is not phase_tick_defaults
                or phase_tick.__kwdefaults__ is not phase_tick_kwdefaults):
            raise RuntimeError('original summary native endpoint changed')
        native_ns=phase_tick()
        if type(ordinal)is not int or not 1<=ordinal<=2 or type(value)is not dict:
            return
        batch=value.get('batch');report=value.get('report')
        if type(batch)is not dict or type(report)is not dict:
            return
        status=batch.get('status');instances=batch.get('instances')
        reason=report.get('reason');work=report.get('work');accounting=report.get('accounting')
        if (type(status)is not str or len(status)>64 or type(instances)is not list
                or len(instances)>1 or type(reason)is not str or len(reason)>256
                or type(work)is not dict or type(accounting)is not dict
                or len(accounting)!=len(summary_counters)):
            return
        steps=work.get('steps')
        if type(steps)is not int or not 0<=steps<=1000000:
            return
        for key in summary_counters:
            count=accounting.get(key)
            if type(count)is not int or not 0<=count<=1000000:
                return
        summary={'ordinal':ordinal,'native_ns':native_ns,'batch_status':status,
            'instance_count':len(instances),'provider_reason':reason,'provider_steps':steps,
            'accounting':{key:accounting[key]for key in summary_counters}}
        if (tick is not phase_tick or phase_tick.__code__ is not phase_tick_code
                or phase_tick.__defaults__ is not phase_tick_defaults
                or phase_tick.__kwdefaults__ is not phase_tick_kwdefaults):
            raise RuntimeError('original summary native endpoint changed')
        phase_tick()
        provider_return_slots[ordinal-1]=summary
    engine_milestone_records=[None,None,None,None]
    milestone_stages=('FIRST_ROOT_FAMILY_PLAN_READY','FIRST_ROOT_FAMILY_EVENT_READY',
        'FIRST_ROOT_PRIMITIVE_PLACED','FIRST_CHILD_DECISION_READY')
    milestone_phases=('M1_PLAN_READY','M2_EVENT_READY','M3_PLACE_RETURN','M4_CHILD_DECISION')
    def capture_engine_milestone(stage,record):
        # Native20 metadata only; retain owned COW references without traversal.
        # The late bounded journal is raw evidence, never scientific admission.
        if (tick is not phase_tick or phase_tick.__code__ is not phase_tick_code
                or phase_tick.__defaults__ is not phase_tick_defaults
                or phase_tick.__kwdefaults__ is not phase_tick_kwdefaults):
            raise RuntimeError('original milestone native endpoint changed')
        phase_tick()
        if type(stage)is not str or stage not in milestone_stages or type(record)is not dict:
            return
        ordinal=milestone_stages.index(stage)
        if (engine_milestone_records[ordinal]is not None
                or any(engine_milestone_records[i]is None for i in range(ordinal))
                or record.get('schema')!='unit-row-first-family-engine-milestone-v1'
                or record.get('stage')!=stage or record.get('diagnostic_only')is not True
                or record.get('scientific_acceptance')is not False):
            return
        phase(milestone_phases[ordinal])
        native_ns=phase_tick()
        engine_milestone_records[ordinal]={'ordinal':ordinal+1,'stage':stage,
            'native_ns':native_ns,'record':record}
    diagnostic_capture['engine_milestones']=engine_milestone_records
    phase('BEFORE_POOL_READ')
    frozen = decode(inputs_raw['frozen_inventory'])
    accepted_inventory = decode(inputs_raw['inventory_acceptance'])
    need(frozen['schema']=='ROOT-native-conditional-inventory-result-v1'
         and frozen['language_binding']==ORIGINAL_BINDING
         and frozen['conditional_inventory']['original_model_binding']==ORIGINAL_BINDING
         and frozen['conditional_inventory']['original_model_sources']==ORIGINAL_SOURCES
         and frozen['conditional_inventory']['original_model_inputs']==ORIGINAL_INPUTS
         and canonical(frozen['conditional_inventory']['marking'])==canonical(marking)
         and accepted_inventory['schema']=='ROOT-native-productive-source-ground-inventory-acceptance-v1'
         and accepted_inventory['expanded']==FIXED_INPUTS['frozen_inventory']
         and accepted_inventory['source_ground_inventory_qualified'] is True
         and accepted_inventory['native_resources_qualified'] is True
         and accepted_inventory['descriptors_qualified']==4,
         'same frozen qualified inventory and original model; prior receipts are data only')
    old_inventory_contract=decode(read_pinned(accepted_inventory['source_contract']))
    need(old_inventory_contract['sources']==frozen['sources']
         and old_inventory_contract['inputs']==frozen['inputs']
         and old_inventory_contract['original_model_sources']==ORIGINAL_SOURCES
         and old_inventory_contract['original_model_binding']==ORIGINAL_BINDING,
         'complete frozen original-model/current-Source contract joins')
    inventory_data=frozen['conditional_inventory']['inventory']
    prior_records=[]
    for pool in inventory_data['minings']:
        need(pool['status']=='PROPOSALS' and pool['mining']['status']=='PROPOSALS',
             'complete frozen extraction data')
        for record_index,record in enumerate(pool['mining']['families']):
            entries=[e for e in inventory_data['qualified_records']
                     if e['component_id']==pool['component_id'] and e['record_index']==record_index]
            need(len(entries)==1 and canonical(entries[0]['record'])==canonical(record)
                 and entries[0]['status']=='CHECKED_SOURCE_GROUND_CONDITIONAL_RECORD'
                 and entries[0]['adaptation']['status']=='READY_LOCAL_CLUSTER',
                 'every frozen mined record joined to its saved qualified occurrence')
            prior_records.append(record['family_id'])
    need(prior_records==accepted_inventory['family_ids']
         and len(prior_records)==accepted_inventory['descriptors_qualified'],
         'whole frozen library identity; fresh source/current checks still required')
    def run_receiver():
        language=fresh_language()
        marked=adapter.MarkedSemantics(language=language,base_semantics=semantics,
            decorator=decorator,verifier=verifier,marking=copy.deepcopy(marking),tick=tick)
        mode=('VISIBLE_RECEPTOR' if plan['purpose']=='receptor-inference-visible-probe' else 'LITERAL_GROUND')
        return modules['receiver_cases'].run_receiver(language=language,
            base_semantics=semantics,marked_semantics=marked,modules=modules,
            frozen_inventory=copy.deepcopy(inventory_data),matching_mode=mode,
            tick=tick,phase=phase,capture_provider_summary=capture_provider_summary,
            engine_milestone_observer=capture_engine_milestone)
    diagnostic_context_raw=canonical({'schema':'ROOT-receptor-inference-probe-diagnostic-context-v1',
        'invocation_id':plan['invocation_id'],'purpose':plan['purpose'],'plan':raw_pin(plan_raw),
        'sources':plan['sources'],'inputs':plan['inputs'],'source_contract':plan['source_contract'],
        'original_model_binding':ORIGINAL_BINDING,'joint_began_ns':EARLY_G,'joint_deadline_ns':end,
        'diagnostic_only':True,'reported_case_count':None,'qualified_case_count':0,
        'positive_joint_gate_accepted':False,'engine_qualified':False,'logical_proof_accepted':False,
        'complete_GCTS_model_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False})
    need(len(diagnostic_context_raw)<=65536,'bounded predelegation connected diagnostic context')
    diagnostic_output_path=str(Path(plan['output_directory']).resolve())
    diagnostic_writer=save_failure_diagnostic
    diagnostic_writer_anchor=anchor_fn(diagnostic_writer)
    try:
        receiver=call(run_receiver)
    except TimeoutError as diagnostic_error:
        if type(diagnostic_error)is TimeoutError:
            try:
                a=diagnostic_writer_anchor;f=diagnostic_writer
                if (save_failure_diagnostic is f and f.__code__ is a[1] and f.__globals__ is a[2]
                        and f.__defaults__ is a[3] and f.__kwdefaults__ is a[4]
                        and len(f.__closure__ or ())==len(a[5])
                        and all(x is y and x.cell_contents is v for x,(y,v)in zip(f.__closure__ or (),a[5]))
                        and tuple((k,id(v))for k,v in sorted((f.__kwdefaults__ or {}).items()))
                            ==tuple((k,token)for k,token,v in a[6])
                        and all(f.__kwdefaults__[k]is v for k,token,v in a[6])):
                    f(diagnostic_output_path,diagnostic_context_raw,diagnostic_capture,
                      'CONTROLS_TIMEOUT_ENGINE_MILESTONES_LOSSLESS_V4',EARLY_G)
            except BaseException:
                pass
        raise
    need(receiver['schema']=='ROOT-receiver-inference-evidence-v1'
         and receiver['status']=='RECEIVER_PROBE_RECORDED',
         'whole returned actual receiver probe; no theorem or broad engine authority')
    phase('BEFORE_OUTPUT')
    payload={'schema':'ROOT-receptor-inference-probe-payload-v1','receiver':receiver,
        'engine_milestones':engine_milestone_records,
        'original_model_sources':ORIGINAL_SOURCES,'original_model_inputs':ORIGINAL_INPUTS,
        'original_model_binding':ORIGINAL_BINDING,'marking':marking,'definition_check':definition_check,
        'frozen_inventory_input':FIXED_INPUTS['frozen_inventory'],
        'inventory_acceptance_input':FIXED_INPUTS['inventory_acceptance'],
        'inventory_reused':True,'construction_in_this_window':False,
        'actual_engine_called':True,
        'new_theorem_discovered':False,'logical_proof_accepted':False,
        'engine_activated':False,'family_library_activated':False,'whole_engine_qualified':False,
        'scheduler_or_rollback_accepted':False,'complete_GCTS_model_accepted':False,
        'RL_accepted':False,'GCTS_advantage_claimed':False,'ROOT_resource_accepted':False}
    result_raw=canonical({'schema':'ROOT-receptor-inference-probe-result-v1',
        'purpose':plan['purpose'],'sources':plan['sources'],'inputs':plan['inputs'],
        'language_binding':ORIGINAL_BINDING,'receiver_probe':payload,
        'logical_proof_accepted':False,'ROOT_resource_accepted':False})+b'\n'
    result_raw=call(encode_result_transport,(result_raw,))
    run=Path(plan['output_directory']);need(run.is_absolute()and run==run.resolve()and not run.exists(),
        'fresh canonical owned component output')
    run.mkdir(mode=0o700);result_pin=call(write_new,(run/'engine-result.json',result_raw))
    body={'schema':'ROOT-receptor-inference-probe-response-body-v1','version':VERSION,
        'status':'COMPLETE_WORKER_PENDING_EXTERNAL','invocation_id':plan['invocation_id'],'plan':raw_pin(plan_raw),
        'sources':plan['sources'],'inputs':plan['inputs'],'language_binding':ORIGINAL_BINDING,
        'original_model_binding':ORIGINAL_BINDING,'outputs':[result_pin],
        'joint_began_ns':EARLY_G,'joint_deadline_ns':end,'CLOCK_DOMAIN':CLOCK_DOMAIN,
        'limits':LIMITS,'resource_rule':plan['resource_rule'],'ROOT_resource_accepted':False,
        'logical_proof_accepted':False,'complete_GCTS_model_accepted':False,
        'failure_marking_activated':False,'family_library_activated':False,'engine_activated':False,
        'RL_accepted':False,'GCTS_advantage_claimed':False}
    body_raw=canonical(body)+b'\n';completion={'schema':'Q-clean-verifier-response-completion-v1',
        'body_sha256':hashlib.sha256(body_raw).hexdigest(),'body_bytes':len(body_raw),
        'exit_zero_and_coordinator_deadline_required':True}
    response_pin=call(write_new,(run/'response.jsonl',body_raw+canonical(completion)+b'\n'))
    need(sorted(p.name for p in run.iterdir())==['engine-result.json','response.jsonl'],'whole component output2')
    final_raw=canonical({'schema':'ROOT-receptor-inference-probe-final-observation-v1',
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
