"""UNEXECUTED Source proposal. Exact V4/P3/O2/runner2/M1 bindings. Root-only activation.

Controls only: no production coordinator.main, controls-admission fabrication,
target route/search or parent Q preparation decode. Actual Root controls qualify
mechanics separately; all mathematical/fullboard/native/RL flags remain false.
"""
import builtins
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import time
import types
import tempfile  # declared coordinator.table dependency, preloaded before seals

VERSION = 'Q-split-neutral-owned-cold-worker-Source-v3'
COORDINATOR_RECORD = {'bytes': 53864,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-owned-coordinator-source-20261014/Q_split_owned_coordinator_v5.py',
 'sha256': '1a769203da1050d2ede508edf3f2d40a4620be31d873e75eb4eb84245425785f'}
PROTOCOL_ADAPTER_RECORD = {'bytes': 75561,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-clean-verifier-protocol-controls-adapter-source-20261014/Q_clean_verifier_protocol_controls_adapter_v4.py',
 'sha256': '495bd2ffa499734a9d4abbbf238a718c66c9fbebc2c3b82789960777f66a041f'}
OWNED_ADAPTER_RECORD = {'bytes': 25468,
 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-owned-controls-source-20261014/Q_owned_neutral_controls_adapter_v3.py',
 'sha256': '7155ba54659c722c308a6377f16e8cbfc719dfb98f7e7488d0dd86db886512c5'}
FIXED_SOURCE_RECORDS = {'census_leaf': {'bytes': 19640,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-owned-controls-source-20261014/Q_neutral_full_model_census_leaf_v1.py',
                 'sha256': '1de670a269e612a454ba58a9b8c9a219934b8ae7666867a0f0a28105f0c44959'},
 'codec': {'bytes': 5806,
           'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-untrusted-preparation-codec-source-20261014/Q_untrusted_lossless_preparation_codec_v1.py',
           'sha256': 'd0d922416aab576ab324397cee94e82c3ddf1e4f0131426f76802695934f88df'},
 'coordinator': {'bytes': 53864,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-owned-coordinator-source-20261014/Q_split_owned_coordinator_v5.py',
                 'sha256': '1a769203da1050d2ede508edf3f2d40a4620be31d873e75eb4eb84245425785f'},
 'disposable_leaf': {'bytes': 2985,
                     'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-owned-controls-source-20261014/Q_neutral_calibration_leaf_v1.py',
                     'sha256': '8c88dabb29c1e5e5b7af0bceddc37173ac03fd6de86e89604cf10a406bb5e190'},
 'independent_checker': {'bytes': 46514,
                         'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-mathematical-audit-source-20261014/independent_Q_semantics_v1.py',
                         'sha256': '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3'},
 'owned_adapter': {'bytes': 25468,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-owned-controls-source-20261014/Q_owned_neutral_controls_adapter_v3.py',
                   'sha256': '7155ba54659c722c308a6377f16e8cbfc719dfb98f7e7488d0dd86db886512c5'},
 'point_adapter': {'bytes': 21715,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-neutral-point-adapter-source-20261014/Q_neutral_point_scheduler_adapter_v1.py',
                   'sha256': '4349af2c387cc6ccee27cdf5bf02d50f6bfdb51474ce46648b4d9f94a3f5bd8d'},
 'point_graph': {'bytes': 28531,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py',
                 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'},
 'producer': {'bytes': 20219,
              'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-untrusted-candidate-producer-source-20261014/Q_untrusted_candidate_search_v2.py',
              'sha256': '994b1ff8f3edf2621826f64fe7d974dee9041fa211e1990d76362268eb607f36'},
 'profile_leaf': {'bytes': 5085,
                  'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-owned-controls-source-20261014/Q_control_verifier_profile_leaf_v1.py',
                  'sha256': '7ccbc8818af91cc2e83aaf558dfab645fbc5bdd4acf130ee4309e53ec49af18b'},
 'protocol_adapter': {'bytes': 75561,
                      'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-clean-verifier-protocol-controls-adapter-source-20261014/Q_clean_verifier_protocol_controls_adapter_v4.py',
                      'sha256': '495bd2ffa499734a9d4abbbf238a718c66c9fbebc2c3b82789960777f66a041f'},
 'runner': {'bytes': 31622,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-search-verifier-controls-runner-source-20261014/Q_split_neutral_controls_runner_v2.py',
            'sha256': '56293f4a7acb8664e4a4745ed35d96db869f29c8a93327f83aea41decc3e4f71'},
 'verifier': {'bytes': 42086,
              'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-clean-verifier-protocol-source-20261014/Q_clean_word_verifier_v3.py',
              'sha256': 'a5cfbe5c72ab617d1c98b1939c4d24aefc0e1c701e36b5fc141dc48bd1ea329b'}}
FIXED_INPUT_RECORDS = {'architecture_choice': {'bytes': 6808,
                         'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-search-verifier-architecture-design-source-20261014/ROOT-architecture-choice-v1.json',
                         'sha256': '62b0d66686f890c9f604192058bdba48a4b171e233f25767b1e1de88fffbd82f'},
 'declaration': {'bytes': 2683,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/Q-declaration-v1.json',
                 'sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc'},
 'finite_ROOT_admission': {'bytes': 8563,
                           'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-audit-shared-wire-progress-20261014/ROOT-actual-independent-Q-shared-wire-audit-reconciled-disposition-v2.json',
                           'sha256': '80dee8b9ec1bca398c24d61c10a026a82f73c8886cdeeb0ed9bf9ea5cf9c1ff1'},
 'finite_certificate': {'bytes': 5789,
                        'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-audit-shared-wire-progress-20261014/worker-output-v1/Q-independent-audit-certificate-provisional-v1.json',
                        'sha256': '3c3aefa4ff9d918a43a8b73d94fd6cebf0741e6203e0d47f3a44fbd716c7bc87'},
 'fixtures': {'bytes': 62584,
              'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-search-verifier-controls-design-source-20261014/complete-fixtures-design-v2.json',
              'sha256': '1420cd2c0a56d09e629ca65fe4b7f690570ccb283b1998762c10de1190180575'},
 'initial_oracle': {'bytes': 8295473,
                    'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/worker-output-v1/Q-initial-oracle-domains-v2.json',
                    'sha256': '03c42ca0083d5e40363d5237d69af56df4ebe3b3ae7d88fa3720fae3390d6969'},
 'initial_state': {'bytes': 8296118,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/worker-output-v1/Q-initial-state-witness-v2.json',
                   'sha256': 'c7e8cfd099b1b80ae170b6c35591d68d56f37aecb38f1bcf7b567d2e019acbb9'},
 'preparation': {'bytes': 38376960,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/worker-output-v1/Q-preparation-provisional-v1.json',
                 'sha256': '0321a462025357d188793bd45a44670adc20776e9ba30574049d77a8b5935d3a'},
 'word_controls_ROOT': {'bytes': 6796,
                        'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-word-controls-progress-20261014/ROOT-actual-unrelated-word-controls-reconciled-disposition-v1.json',
                        'sha256': 'f254219dc8e7324a7d15f9ff50661de627d207eca08660bca354e73978d39fd1'}}
FIXED_REVIEW_CONTRACTS = {'coordinator': {'bytes': 12908,
                 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-owned-coordinator-source-20261014/Source-contract-v5.json',
                 'sha256': '3e7c37d1478aaa6494e9b38af0babca8d80d0aba49c333dae624b26ffc83f1c0'},
 'owned_adapter': {'bytes': 18268,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-owned-controls-source-20261014/Source-contract-v3.json',
                   'sha256': 'acef27e411a9d6c2d9a0b81fd6a22aa5133567cb2d7f48f802917bed35a757fd'},
 'point_adapter': {'bytes': 9944,
                   'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-neutral-point-adapter-source-20261014/Source-contract-v1.json',
                   'sha256': '125e5d999890f97f14819bff6a2ecbefc39b8229525342aca93dafe965d65936'},
 'protocol_adapter': {'bytes': 21852,
                      'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-clean-verifier-protocol-controls-adapter-source-20261014/Source-contract-v3.json',
                      'sha256': '2a1a9aa53a3f7e9e105721f964b340754bf5d5199f3167dd8987cdd0fa2f7e95'},
 'runner': {'bytes': 17195,
            'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-search-verifier-controls-runner-source-20261014/Source-contract-v2.json',
            'sha256': 'a0ad630e848c3bfbab9edccc756a79f6e9a88b790353ae83661796b9bb3b7644'}}
EXPECTED_REVIEW_SCOPES = {
    'worker': 'Q-split-neutral-owned-controls-worker-Source',
    'launcher': 'Q-neutral-controls-early-clock-launcher-Source',
    'runner': 'Q-split-neutral-controls-callable-Source',
    'protocol_adapter': 'Q-split-neutral-hard-target-protocol-adapter-Source',
    'point_adapter': 'Q-split-neutral-NONLOGICAL-point-scheduler-adapter-Source',
    'owned_adapter': 'Q-split-neutral-owned-model-role-deadline-adapter-Source',
    'coordinator': 'Q-split-owned-coordinator-Source',
}
PARENT_EXECUTION_ROLES = ('coordinator', 'runner', 'independent_checker', 'point_graph',
                          'protocol_adapter', 'point_adapter', 'owned_adapter')
SUCCESS_NS = 20000000000
FAILURE_NS = 55000000000
OWNED_NS = 60000000000
MAX_RAW_METADATA = 2 * 1048576
MAX_OUTPUT = 64 * 1048576
OUTPUT_DIRECTORY = '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-split-neutral-controls-progress-20261014/controls-output-v1'
FIXED_RUNTIME = {'bytes': 102352, 'path': '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9', 'sha256': 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'}
FIXED_ORIGINAL_SOURCES = {'catalogue': {'bytes': 10187,
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
FIXED_LIMITS = {'aggregate_owned_bytes': 536870912, 'caller_finish_reserve_seconds': 1, 'caller_seconds': 90, 'failure_only_seconds': 55, 'joint_seconds': 20, 'owned_seconds': 60}

def need(ok, message):
    if not ok:
        raise ValueError(message)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf8')

def wire_pin(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def function_state(fn):
    owner = fn.__self__ if type(fn) is types.MethodType else None
    fn = fn.__func__ if type(fn) is types.MethodType else fn
    need(type(fn) is types.FunctionType, 'original declared Python function')
    cells = []
    for cell in fn.__closure__ or ():
        try:
            value = cell.cell_contents
        except ValueError:
            value = EMPTY_CELL
        cells.append((cell, value))
    return (owner, fn, fn.__code__, fn.__defaults__, fn.__kwdefaults__, tuple(cells))

EMPTY_CELL = object()

def same_function(fn, capture):
    owner = fn.__self__ if type(fn) is types.MethodType else None
    fn = fn.__func__ if type(fn) is types.MethodType else fn
    if owner is not capture[0] or fn is not capture[1] or fn.__code__ is not capture[2] or fn.__defaults__ is not capture[3] or fn.__kwdefaults__ is not capture[4]:
        return False
    if len(fn.__closure__ or ()) != len(capture[5]):
        return False
    for cell, (old, value) in zip(fn.__closure__ or (), capture[5]):
        if cell is not old:
            return False
        try:
            current = cell.cell_contents
        except ValueError:
            current = EMPTY_CELL
        if current is not value:
            return False
    return True

def data_state(value, depth=0):
    if depth > 64:
        raise ValueError('bounded complete Source constant tree')
    if value is None or type(value) in (bool, int, str, bytes):
        return (type(value), value)
    if type(value) is float:
        return (float, value.hex())
    if type(value) in (tuple, list):
        return (type(value), tuple(data_state(child, depth + 1) for child in value))
    if type(value) in (dict, types.MappingProxyType):
        return (type(value), tuple((key, data_state(value[key], depth + 1)) for key in sorted(value)))
    if type(value) in (set, frozenset):
        return (type(value), frozenset(data_state(child, depth + 1) for child in value))
    return ('identity', id(value), type(value))

def class_state(cls):
    entries = []
    for base in cls.__mro__:
        for name, descriptor in sorted(vars(base).items()):
            if type(descriptor) is types.FunctionType:
                entries.append((base, name, 'function', function_state(descriptor)))
            elif type(descriptor) in (staticmethod, classmethod):
                fn = descriptor.__func__
                entries.append((base, name, type(descriptor), function_state(fn) if type(fn) is types.FunctionType else ('native', fn, type(fn))))
            elif type(descriptor) is property:
                entries.append((base, name, property, tuple(function_state(fn) if fn is not None else None for fn in (descriptor.fget, descriptor.fset, descriptor.fdel))))
            else:
                entries.append((base, name, 'native-or-data', id(descriptor), type(descriptor)))
    return (cls, cls.__mro__, tuple(entries))

def module_state(module):
    namespace = vars(module)
    entries = []
    for name, value in sorted(namespace.items()):
        if name == '__builtins__':
            mapping = vars(value) if type(value) is types.ModuleType else value
            need(type(mapping) is dict, 'actual compiled builtin resolution mapping')
            entries.append((name, 'builtins-holder', id(value), type(value),
                            tuple((key, id(child), type(child), function_state(child) if type(child) is types.FunctionType else None)
                                  for key, child in sorted(mapping.items()))))
        elif type(value) is types.FunctionType:
            entries.append((name, 'function', function_state(value)))
        elif type(value) is type and value.__module__ == module.__name__:
            entries.append((name, 'class', class_state(value)))
        elif type(value) in (dict, tuple, list, set, frozenset, str, bytes, int, bool, float) or value is None:
            entries.append((name, 'data', data_state(value)))
        else:
            entries.append((name, 'identity', id(value), type(value)))
    return (module, module.__name__, getattr(module,'__file__',None), tuple(entries))

def object_state(object, endpoint_names):
    cls = type(object)
    methods = tuple((name, function_state(getattr(object, name))) for name in endpoint_names)
    need(all(capture[0] is object for _, capture in methods), 'actual effective bound instance endpoints')
    return (object, cls, class_state(cls), methods)

def review_record(record, expected_source, expected_contract, scope):
    raw = raw_read(record, MAX_RAW_METADATA)
    value = decode_metadata(raw)
    need(type(value) is dict and value['source'] == expected_source and value['source_contract'] == expected_contract
         and value['scope'] == scope and value['source_only'] is True and value['source_review_passed'] is True
         and value['all_checks_passed'] is True and type(value['scientific_calls']) is int and value['scientific_calls'] == 0
         and value['author_identity'] != value['reviewer_identity'], 'genuine distinct current byte/contract/scope Source pass')
    return value

def canonical_regular(value):
    need(type(value) is str and value and '\x00' not in value, 'literal absolute path')
    path = Path(value)
    need(path.is_absolute() and str(path) == value and path == path.resolve() and not path.is_symlink(), 'canonical nonsymlink path')
    return path

def raw_read(record, cap):
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'} and type(record['bytes']) is int
         and 0 <= record['bytes'] <= cap and type(record['sha256']) is str and len(record['sha256']) == 64
         and all(c in '0123456789abcdef' for c in record['sha256']), 'complete explicit raw pin')
    path = canonical_regular(record['path'])
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_size == record['bytes'], 'whole regular pin, no prefix')
        raw = bytearray()
        while len(raw) <= record['bytes']:
            chunk = os.read(fd, min(65536, record['bytes'] + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        need(os.read(fd, 1) == b'', 'whole raw EOF')
        after = os.fstat(fd)
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'stable complete original descriptor')
        result = bytes(raw)
        need(wire_pin(result) == {key: record[key] for key in ('sha256', 'bytes')}, 'whole raw SHA/length')
        return result
    finally:
        os.close(fd)

def unique(pairs):
    value = {}
    for key, child in pairs:
        need(key not in value, 'no duplicate metadata key')
        value[key] = child
    return value

def decode_metadata(raw):
    def no_constant(token):
        raise ValueError('nonfinite metadata token')
    def no_float(token):
        raise ValueError('floating metadata token')
    return json.loads(raw.decode('utf8'), object_pairs_hook=unique, parse_constant=no_constant, parse_float=no_float)

def load_source(role, record, raw):
    name = '_Q_neutral_cold_' + role + '_' + record['sha256'][:16]
    need(name not in sys.modules, 'once fresh private Source namespace')
    module = types.ModuleType(name)
    module.__file__ = record['path']
    module.__package__, module.__loader__, module.__spec__ = '', None, None
    imports = builtins.__import__
    allowed = {'__future__','builtins','copy','gzip','hashlib','json','math','os','pathlib','resource','signal','stat','subprocess','sys','time','types','dataclasses','typing','fcntl','tempfile'}
    def import_stdlib(name, globals=None, locals=None, fromlist=(), level=0):
        need(level == 0 and name.split('.')[0] in allowed, 'stdlib only; no filesystem project/pyc import')
        return imports(name, globals, locals, fromlist, level)
    module.__dict__['__builtins__'] = dict(vars(builtins), __import__=import_stdlib)
    sys.modules[name] = module
    exec(compile(raw, record['path'], 'exec', dont_inherit=True), module.__dict__)
    return module

class ColdGuard:
    __slots__ = ('_sealed','clock','usage','frame_reader','began','deadline','modules','runner_namespace','module_anchors','buffer_records','builtin_anchors','module_registry','native_modules','native_anchors','decoder','decoder_fields','objects','callbacks','fixed_objects','gate_extras','original_codes','validators','check_fn','check_code')
    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False):raise ValueError('sealed complete cold guard fields')
        object.__setattr__(self,name,value)
    """Complete synchronous Source/object custody, not hostile OS/VM sandbox.

    Data state of actual graph/Owner containers evolves. Code/module/builtins,
    class descriptors, effective methods, callback code/default/cells and fixed
    Source buffers do not. Registration is once before each new object is used.
    """
    def __init__(self, modules, source_buffers, began_ns):
        self.clock, self.usage = time.perf_counter_ns, resource.getrusage
        self.frame_reader = sys._getframe
        self.began, self.deadline = began_ns, began_ns + SUCCESS_NS
        self.modules = tuple(modules)
        self.runner_namespace = next(vars(module) for module in self.modules
             if getattr(module,'__file__',None)==FIXED_SOURCE_RECORDS['runner']['path'])
        self.module_anchors = tuple(module_state(module) for module in self.modules)
        self.buffer_records = tuple((raw, wire_pin(raw)) for raw in source_buffers.values())
        self.builtin_anchors = tuple(sorted(vars(builtins).items()))
        self.module_registry = tuple(sorted(sys.modules.items()))
        self.native_modules = (json, time, resource, os, types)
        self.native_modules += (json.encoder, json.decoder, json.scanner)
        self.native_anchors = tuple(module_state(module) for module in self.native_modules)
        self.decoder = json._default_decoder
        self.decoder_fields = (type(self.decoder), tuple(sorted(vars(self.decoder).items())),
                               class_state(type(self.decoder)))
        self.objects, self.callbacks, self.fixed_objects, self.gate_extras = [], [], [], []
        self.original_codes = set()
        def code_roots(code):
            if code in self.original_codes:return
            self.original_codes.add(code)
            for value in code.co_consts:
                if type(value) is types.CodeType:code_roots(value)
        for module in self.modules:
            for value in vars(module).values():
                if type(value) is types.FunctionType:code_roots(value.__code__)
                elif type(value) is type and value.__module__ == module.__name__:
                    for base in value.__mro__:
                        for descriptor in vars(base).values():
                            if type(descriptor) is types.FunctionType:code_roots(descriptor.__code__)
                            elif type(descriptor) is property:
                                for function in (descriptor.fget,descriptor.fset,descriptor.fdel):
                                    if function is not None:code_roots(function.__code__)
        self.validators = tuple((fn, function_state(fn)) for fn in
            (need, canonical, wire_pin, function_state, same_function, data_state, class_state, module_state, object_state))
        self.check_fn, self.check_code = ColdGuard.check, ColdGuard.check.__code__
        self._sealed=True
    def register_object(self, object, endpoint_names):
        if any(object is old[0] for old in self.objects):return
        record = object_state(object,endpoint_names)
        need(all(capture[2] in self.original_codes for _,capture in record[3]), 'original presealed instance code, no post-check authority recapture')
        self.objects.append(record)
        if type(object).__name__=='Gate':
            fields=('guard','guard_state','clock','usage','began','deadline','need','state','same','need_code','state_code','same_code','check_fn','check_code')
            self.fixed_objects.append((object,tuple((name,getattr(object,name)) for name in fields)))
            self.gate_extras.append([object,object.extra])
        elif type(object).__name__=='Boundary':
            fields=tuple(name for name in type(object).__slots__ if name!='__weakref__')
            self.fixed_objects.append((object,tuple((name,getattr(object,name)) for name in fields)))
        elif type(object).__name__=='Owner':
            self.fixed_objects.append((object,tuple((name,getattr(object,name)) for name in ('began_ns','deadline_ns','failure_ns','owned_ns'))))
        elif type(object).__name__=='Executor':
            self.fixed_objects.append((object,(('graph',object.graph),)))
    def register_callback(self, callback):
        capture = function_state(callback)
        need(capture[2] in self.original_codes and any(callback.__globals__ is vars(module) for module in self.modules), 'only original presealed callback code and namespace')
        need(all(callback is not old for old, _ in self.callbacks), 'once callback registration, not authority reseal')
        self.callbacks.append((callback, capture))
    def discover_ephemeral_objects(self):
        # Restricted to original presealed code and genuine module globals. No
        # candidate frame/path chooses authority. New toy graphs/Gates are fully
        # constructed by guarded original source before their postguard use.
        if sys._getframe is not self.frame_reader:raise ValueError('original frame endpoint changed')
        frame = self.frame_reader()
        while frame is not None:
            if frame.f_code in self.original_codes and any(frame.f_globals is vars(module) for module in self.modules):
                for name in ('graph','executor','gate','result','self','boundary'):
                    value = frame.f_locals.get(name)
                    if value is None:continue
                    cls = type(value)
                    for module in self.modules:
                        if cls is vars(module).get('PointGraph'):
                            self.register_object(value,tuple(name for name,value in vars(cls).items() if type(value) is types.FunctionType))
                        elif cls is vars(module).get('Executor'):
                            self.register_object(value,tuple(name for name,value in vars(cls).items() if type(value) is types.FunctionType))
                        elif cls is vars(module).get('Gate') and hasattr(value,'check_fn'):
                            self.register_object(value,('check','invoke'))
                        elif cls is vars(module).get('Boundary') and getattr(value,'_sealed',False) is True:
                            self.register_object(value,('check','invoke'))
            frame=frame.f_back
    def check(self, *, cleanup=False):
        if ColdGuard.check is not self.check_fn or ColdGuard.check.__code__ is not self.check_code or time.perf_counter_ns is not self.clock or resource.getrusage is not self.usage:
            raise ValueError('original complete cold guard/clock changed')
        if any(vars(sys.modules[__name__]).get(fn.__name__) is not fn or fn.__code__ is not capture[2] or fn.__defaults__ is not capture[3] or fn.__kwdefaults__ is not capture[4] for fn, capture in self.validators):
            raise ValueError('original cold validation helper changed before delegation')
        if self.clock() >= self.began + (FAILURE_NS if cleanup else SUCCESS_NS):
            raise TimeoutError('complete cold setup/control/output exceeded original interval')
        if tuple(sorted(sys.modules.items())) != self.module_registry:
            raise ValueError('exact original module registry; no project/cache additions')
        if tuple(sorted(vars(builtins).items())) != self.builtin_anchors:
            raise ValueError('builtin name resolution changed')
        if tuple(module_state(module) for module in self.native_modules) != self.native_anchors:
            raise ValueError('complete native stdlib namespace changed')
        if tuple(module_state(module) for module in self.modules) != self.module_anchors:
            raise ValueError('complete original Source namespaces/classes/defaults/constants changed')
        if json._default_decoder is not self.decoder or (type(self.decoder), tuple(sorted(vars(self.decoder).items())), class_state(type(self.decoder))) != self.decoder_fields:
            raise ValueError('actual cached JSON decoder/scanner changed')
        self.discover_ephemeral_objects()
        for object, cls, class_anchor, methods in self.objects:
            if type(object) is not cls or class_state(cls) != class_anchor:
                raise ValueError('constructed exact object class/MRO/getters changed')
            for name, capture in methods:
                if not same_function(getattr(object, name), capture):
                    raise ValueError('actual effective object method/instance shadow changed')
        if any(not same_function(callback, capture) for callback, capture in self.callbacks):
            raise ValueError('actual once-registered callback/code/default/closure changed')
        for object, fields in self.fixed_objects:
            if any(getattr(object,name) is not value for name,value in fields):
                raise ValueError('original constructed object fixed authority fields changed')
        for registration in self.gate_extras:
            object, original=registration
            if original is None and object.extra is not None:
                extra=object.extra
                need(type(extra) is tuple and len(extra)==2 and type(extra[0]) is types.FunctionType
                     and extra[0].__code__ in self.original_codes and extra[0].__globals__ is self.runner_namespace
                     and same_function(extra[0],extra[1]),'declared once genuine runner callback registration')
                registration[1]=extra
            elif object.extra is not original:
                raise ValueError('once-bound Gate runner callback changed')
        if any(wire_pin(raw) != record for raw, record in self.buffer_records):
            raise ValueError('same authenticated immutable Source buffer changed')
        if self.usage(resource.RUSAGE_SELF).ru_maxrss >= 500*1048576:raise ValueError('original worker500 memory guidance')
        if self.clock() >= self.began + (FAILURE_NS if cleanup else SUCCESS_NS):
            raise TimeoutError('complete cold guard returned after original interval')

def main(argv, *, joint_began_ns):
    # Pre-import authentication is independent of any current project module.
    if len(argv) != 1 or type(joint_began_ns) is not int or sys.platform != 'darwin':
        raise ValueError('one Root request/native Darwin/original integer begin')
    native_clock, native_usage = time.perf_counter_ns, resource.getrusage
    if not joint_began_ns <= native_clock() < joint_began_ns + SUCCESS_NS:
        raise TimeoutError('original first trusted launcher begin')
    original_helpers = tuple((fn, function_state(fn)) for fn in
        (need, canonical, wire_pin, function_state, same_function, data_state, class_state, module_state,
         object_state, review_record, canonical_regular, raw_read, unique, decode_metadata, load_source))
    same_fn, same_anchor = same_function, function_state(same_function)
    request_path = canonical_regular(argv[0])
    request_metadata = request_path.stat()
    request_record = {'path':str(request_path),'sha256':hashlib.sha256(request_path.read_bytes()).hexdigest(),'bytes':request_metadata.st_size}
    request_raw = raw_read(request_record, MAX_RAW_METADATA)
    request = decode_metadata(request_raw)
    need(type(request) is dict and set(request) == {'schema','invocation_id','sources','inputs','original_sources','runtime','reviews','output_directory','preregistration','worker_source','launcher_source','raw_closure'}, 'exact controls-only request12')
    need(request['schema'] == 'ROOT-Q-split-neutral-owned-controls-request-v1'
         and request['sources'] == FIXED_SOURCE_RECORDS and request['inputs'] == FIXED_INPUT_RECORDS
         and request['original_sources'] == FIXED_ORIGINAL_SOURCES and request['runtime'] == FIXED_RUNTIME,
         'complete fixed current sources/original data/runtime; no guessed admission')
    need(type(request['invocation_id']) is str and 1 <= len(request['invocation_id']) <= 128
         and request['invocation_id'].isascii(), 'literal bounded Root invocation id')
    own_raw = raw_read(request['worker_source'], MAX_RAW_METADATA)
    launcher_raw = raw_read(request['launcher_source'], MAX_RAW_METADATA)
    need(request['worker_source']['path'] == __file__, 'actual immutable worker Source origin')
    launcher_module = sys.modules['__main__']
    need(launcher_module.__file__ == request['launcher_source']['path']
         and launcher_module.JOINT_BEGAN_NS == joint_began_ns
         and launcher_module.WORKER_SOURCE == request['worker_source'], 'actual reviewed early launcher/current worker/original begin')
    need(canonical_regular(sys.executable)==Path(FIXED_RUNTIME['path']),'actual original canonical Python runtime')
    runtime_raw = raw_read(request['runtime'], MAX_RAW_METADATA); del runtime_raw
    need(set(request['reviews'])==set(EXPECTED_REVIEW_SCOPES), 'complete current distinct Source reviews before imports')
    reviewed = {}
    common_contract = None
    for role, scope in EXPECTED_REVIEW_SCOPES.items():
        current = request['worker_source'] if role=='worker' else request['launcher_source'] if role=='launcher' else request['sources'][role]
        if role in ('worker','launcher'):
            review_value = decode_metadata(raw_read(request['reviews'][role],MAX_RAW_METADATA))
            contract_record = review_value['source_contract']
            implementation_contract = decode_metadata(raw_read(contract_record,MAX_RAW_METADATA))
            need(implementation_contract['worker_source'] == request['worker_source']
                 and implementation_contract['launcher_source'] == request['launcher_source']
                 and implementation_contract['sources'] == FIXED_SOURCE_RECORDS
                 and implementation_contract['inputs'] == FIXED_INPUT_RECORDS
                 and implementation_contract['limits'] == FIXED_LIMITS
                 and implementation_contract['author_identity'] == '/root/hilbert_advice_controls', 'exact current common implementation contract; no circular self pin')
            need(common_contract is None or common_contract == contract_record, 'same genuine worker/launcher current contract')
            common_contract = contract_record
        else:
            contract_record = FIXED_REVIEW_CONTRACTS[role]
        reviewed[role] = review_record(request['reviews'][role],current,contract_record,scope)
    prereg = decode_metadata(raw_read(request['preregistration'],MAX_RAW_METADATA))
    need(prereg['schema']=='ROOT-Q-split-neutral-owned-controls-preregistration-v1'
         and prereg['invocation_id']==request['invocation_id'] and prereg['sources']==FIXED_SOURCE_RECORDS
         and prereg['inputs']==FIXED_INPUT_RECORDS and prereg['limits']==FIXED_LIMITS
         and prereg['case_counts']=={'kernel':20,'protocol':16,'point':8,'owned':8}
         and prereg['W16']=='not_exercised_separate_expected_UNKNOWN'
         and prereg['scope']=='controls_only_no_original_target_positive_route', 'genuine Root neutral preregistration/no fake baseline admission')
    required_records = list(FIXED_SOURCE_RECORDS.values())+list(FIXED_INPUT_RECORDS.values())+list(FIXED_ORIGINAL_SOURCES.values())
    required_records += list(request['reviews'].values())+list(FIXED_REVIEW_CONTRACTS.values())+[request['worker_source'],request['launcher_source'],request['preregistration'],common_contract]
    need(type(request['raw_closure']) is list and len(request['raw_closure'])<=512
         and all(type(r) is dict and set(r)=={'path','sha256','bytes'} for r in request['raw_closure'])
         and len({r['path'] for r in request['raw_closure']})==len(request['raw_closure'])
         and all(r in request['raw_closure'] for r in required_records), 'complete exact named lexical raw closure; no arbitrary ancestor decode')
    source_buffers = {role:raw_read(record,MAX_RAW_METADATA) for role,record in request['sources'].items()}
    modules, loaded_anchors = {}, []
    for role in PARENT_EXECUTION_ROLES:
        if same_function is not same_fn or same_fn.__code__ is not same_anchor[2]:raise ValueError('original loader validator before imports')
        if any(not same_fn(fn,capture) or vars(sys.modules[__name__]).get(fn.__name__) is not fn for fn,capture in original_helpers):raise ValueError('original loader own code/defaults/cells')
        if any(module_state(m)!=anchor for m,anchor in loaded_anchors):raise ValueError('already authenticated module changed before registration')
        if time.perf_counter_ns is not native_clock or resource.getrusage is not native_usage:raise ValueError('original native endpoints before imports')
        module = load_source(role,request['sources'][role],source_buffers[role])
        if same_function is not same_fn or same_fn.__code__ is not same_anchor[2]:raise ValueError('original loader validator after imports')
        if any(not same_fn(fn,capture) or vars(sys.modules[__name__]).get(fn.__name__) is not fn for fn,capture in original_helpers):raise ValueError('own Source modified during module registration')
        if any(module_state(m)!=anchor for m,anchor in loaded_anchors):raise ValueError('previous module modified during declared registration')
        modules[role]=module;loaded_anchors.append((module,module_state(module)))
    coor = modules['coordinator']
    guard = ColdGuard(tuple(modules.values()) + (sys.modules[__name__],launcher_module),
                      dict(source_buffers,worker=own_raw,launcher=launcher_raw),joint_began_ns)
    check_fn, check_capture = ColdGuard.check, function_state(ColdGuard.check)
    def source_guard():
        if (same_function is not same_fn or same_fn.__code__ is not same_anchor[2]
            or same_fn.__defaults__ is not same_anchor[3] or same_fn.__kwdefaults__ is not same_anchor[4]
            or ColdGuard.check is not check_fn or check_fn.__code__ is not check_capture[2]
            or check_fn.__defaults__ is not check_capture[3] or check_fn.__kwdefaults__ is not check_capture[4]):
            raise ValueError('original delegated Source validation code before caller')
        if not same_fn(check_fn,check_capture):raise ValueError('original delegated Source validation closure')
        check_fn(guard)
        if (same_function is not same_fn or same_fn.__code__ is not same_anchor[2]
            or ColdGuard.check is not check_fn or check_fn.__code__ is not check_capture[2]):raise ValueError('actual Source guard changed during call')
        if not same_fn(check_fn,check_capture):raise ValueError('actual Source guard closure changed during call')
    guard.register_callback(source_guard)
    source_guard_anchor = function_state(source_guard)
    invocation_anchor = {}  # one original invoke state filled before first call
    def invoke(function,*arguments,_cleanup=False,**keywords):
        # Direct own validator and actual nested endpoints, before delegation.
        if (same_function is not same_fn or same_fn.__code__ is not same_anchor[2]
            or same_fn.__defaults__ is not same_anchor[3] or same_fn.__kwdefaults__ is not same_anchor[4]
            or ColdGuard.check is not check_fn or check_fn.__code__ is not check_capture[2]
            or invoke.__code__ is not invocation_anchor['state'][2]
            or time.perf_counter_ns is not native_clock or resource.getrusage is not native_usage):
            raise ValueError('actual immediate invoke/validator/clock code before delegation')
        if not same_fn(invoke,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor) or not same_fn(check_fn,check_capture):raise ValueError('actual nested caller code/defaults/cells changed')
        check_fn(guard,cleanup=_cleanup)
        class_target = type(function) is type
        capture = class_state(function) if class_target else function_state(function)
        try:
            returned=function(*arguments,**keywords)
        except BaseException:
            if (same_function is not same_fn or same_fn.__code__ is not same_anchor[2]
                or invoke.__code__ is not invocation_anchor['state'][2]
                or ColdGuard.check is not check_fn or check_fn.__code__ is not check_capture[2]):raise ValueError('actual failed immediate caller code changed')
            if not same_fn(invoke,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('failed caller closure changed')
            check_fn(guard,cleanup=True)
            raise
        if (same_function is not same_fn or same_fn.__code__ is not same_anchor[2]
            or invoke.__code__ is not invocation_anchor['state'][2]
            or ColdGuard.check is not check_fn or check_fn.__code__ is not check_capture[2]):raise ValueError('actual immediate caller code changed after delegation')
        if not same_fn(invoke,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual immediate caller closure changed after delegation')
        if class_target:
            if class_state(function)!=capture:raise ValueError('original constructed class changed')
        elif not same_fn(function,capture):raise ValueError('actual delegated function/code/defaults/cells changed')
        check_fn(guard,cleanup=_cleanup)
        return returned
    invocation_anchor['state']=function_state(invoke)
    invoke_fn=invoke
    if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
    if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
    owner=invoke_fn(coor.Owner,joint_began_ns)
    guard.register_object(owner,('check','table','active','sample','launch','reap','wait','cleanup','memory_bound','memory_diagnostic'))
    need(request['output_directory']==OUTPUT_DIRECTORY,'exact fresh Root task-owned controls output namespace')
    run = canonical_regular(request['output_directory'])
    need(not run.exists(), 'fresh exclusive once-only controls directory')
    run.mkdir(mode=0o700)
    result, error, pending = None, None, False
    w01 = []
    try:
        snapshots = run / 'snapshots'; snapshots.mkdir(mode=0o700)
        for name, record in request['inputs'].items():
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
            if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
            invoke_fn(coor.stream_snapshot, record, snapshots/('input-'+name), owner)
        for name, record in request['original_sources'].items():
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
            if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
            invoke_fn(coor.stream_snapshot, record, snapshots/('original-'+name), owner)
        for name, record in request['sources'].items():
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
            if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
            invoke_fn(coor.stream_snapshot, record, snapshots/('source-'+name+'.py'), owner)
        for record in request['raw_closure']:
            # Raw custody only, not arbitrary ancestor metadata/Q decoding.
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
            if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
            fd = invoke_fn(coor.regular_fd, record['path'], os.O_RDONLY)
            try:
                sha, count = hashlib.sha256(), 0
                before=os.fstat(fd)
                need(stat.S_ISREG(before.st_mode) and before.st_size==record['bytes'],'whole named regular closure input')
                while True:
                    if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('immediate raw Source caller')
                    if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('raw Source callback cells')
                    invoke_fn(source_guard); block = os.read(fd,65536)
                    if not block:break
                    sha.update(block);count+=len(block)
                after=os.fstat(fd)
                need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'same complete lexical closure descriptor')
                need(count==record['bytes'] and sha.hexdigest()==record['sha256'],'complete named raw closure')
            finally:os.close(fd)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        declaration_raw = invoke_fn(coor.read_small, snapshots/'input-declaration',2683)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        declaration = invoke_fn(coor.decode, declaration_raw,2683)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        fixtures_raw = invoke_fn(coor.read_small, snapshots/'input-fixtures',62584)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        fixtures = invoke_fn(coor.decode, fixtures_raw,62584)
        roles = {name:{key:request['sources'][name][key] for key in ('sha256','bytes')}
                 for name in ('coordinator','producer','verifier','independent_checker','point_graph')}
        authority = {'schema':'Q-clean-verifier-fixed-authority-v1','coordinator_invocation_id':request['invocation_id'],
                     'declaration':declaration,'binding':coor.BINDING,'raw_input_bindings':coor.RAW_INPUT_BINDINGS,
                     'source_bindings':roles,'limits':coor.LIMITS}
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        authority_raw = invoke_fn(coor.canonical, authority)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        authority_path = run/'fixed-authority.json';invoke_fn(coor.write_exclusive, authority_path,authority_raw)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        baseline = copy.deepcopy(fixtures['protocol_rejection_baseline']);baseline['coordinator_invocation_id']=request['invocation_id'];baseline['authority_sha256']=invoke_fn(coor.pin_bytes, authority_raw)['sha256']
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        baseline_raw = invoke_fn(coor.canonical, baseline);candidate_path=run/'rejected-control-candidate.json';invoke_fn(coor.write_exclusive, candidate_path,baseline_raw)
        protocol_dir=run/'protocol'
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        protocol = invoke_fn(modules['protocol_adapter'].make_protocol_surface_adapter, 
            coordinator_module=coor,coordinator_source_raw=source_buffers['coordinator'],verifier_source_raw=source_buffers['verifier'],
            checker_source_raw=source_buffers['independent_checker'],fixed_authority_raw=authority_raw,declaration_raw=declaration_raw,
            source_records={name:request['sources'][name] for name in roles},runtime_record=request['runtime'],
            owned_output_directory=str(protocol_dir),owner=owner,source_guard=source_guard,
            joint_began_ns=joint_began_ns,joint_deadline_ns=owner.deadline_ns,observations_sink=w01)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        point = invoke_fn(modules['point_adapter'].make_point_scheduler_adapter, point_module=modules['point_graph'],point_source_raw=source_buffers['point_graph'],
            point_source_record=request['sources']['point_graph'],complete_fixtures_raw=fixtures_raw,source_guard=source_guard,
            joint_began_ns=joint_began_ns,joint_deadline_ns=owner.deadline_ns)
        manifest={'schema':'Q-neutral-full-model-census-manifest-v1','coordinator_invocation_id':request['invocation_id'],
                  'declaration':declaration,'binding':coor.BINDING,'original_source_bindings':coor.ORIGINAL_SOURCES,
                  'source_bindings':{name:{key:request['sources'][name][key] for key in ('sha256','bytes')} for name in ('census_leaf','codec','point_graph')},
                  'input_bindings':{name:coor.RAW_INPUT_BINDINGS[name] for name in ('preparation','initial_state','initial_oracle')},
                  'scopes':{'search':False,'placement':False,'proof':False,'parent_preparation_parse':False}}
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        manifest_raw=invoke_fn(coor.canonical, manifest);manifest_path=run/'census-manifest.json';invoke_fn(coor.write_exclusive, manifest_path,manifest_raw)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        owned_context={'owner':owner,'coordinator_module':coor,'runtime':request['runtime'],'run_directory':str(run),
                       'source_guard':source_guard,'current_W01_observation':w01,
                       'authority':{'path':str(authority_path),**invoke_fn(coor.pin_bytes, authority_raw)},
                       'candidate':{'path':str(candidate_path),**invoke_fn(coor.pin_bytes, baseline_raw)},
                       'census_manifest':{'path':str(manifest_path),**invoke_fn(coor.pin_bytes, manifest_raw)}}
        for role,key in [('verifier_source','verifier'),('checker_source','independent_checker'),('profile_source','profile_leaf'),
                         ('calibration_source','disposable_leaf'),('census_source','census_leaf'),('codec_source','codec'),('point_source','point_graph')]:
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
            if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
            owned_context[role]={'path':str(snapshots/('source-'+key+'.py')),**invoke_fn(coor.pin_bytes, source_buffers[key])}
        for name in ('preparation','initial_state','initial_oracle'):
            owned_context[name]={'path':str(snapshots/('input-'+name)),**{key:request['inputs'][name][key] for key in ('sha256','bytes')}}
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        owned=invoke_fn(modules['owned_adapter'].make_owned_neutral_adapter, context=owned_context,joint_began_ns=joint_began_ns,joint_deadline_ns=owner.deadline_ns)
        need(owned is not None,'full genuine owned context required; no ignored controls surface')
        for callback in (protocol,point,owned):guard.register_callback(callback)
        bindings={surface:{'endpoint':endpoint,'authenticated_source_raw':source_buffers[role],
                  'reviewed_source_record':request['sources'][role],'genuine_typed_review':reviewed[role]}
                  for surface,endpoint,role in (
                    ('hard-target-protocol',protocol,'protocol_adapter'),
                    ('NONLOGICAL-point-scheduler',point,'point_adapter'),
                    ('owned-model-role-deadline',owned,'owned_adapter'))}
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        result=invoke_fn(modules['runner'].run_split_neutral_controls, complete_fixtures_raw=fixtures_raw,checker_module=modules['independent_checker'],
             checker_source_raw=source_buffers['independent_checker'],source_guard=source_guard,joint_began_ns=joint_began_ns,
             joint_deadline_ns=owner.deadline_ns,adapter_bindings=bindings,authority_raw=authority_raw,invocation_id=request['invocation_id'])
        need(len(result['results'])==52 and result['full_architecture_qualified'] is False,'all52 retained no self qualification')
        result_raw=canonical(result)+b'\n';need(len(result_raw)<=MAX_OUTPUT,'complete result no truncation')
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        invoke_fn(coor.write_exclusive, run/'complete-controls-result.json',result_raw)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('final immediate Source caller')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('final Source callback cells')
        invoke_fn(source_guard)
        pending=(result['all_exercised_checks_passed'] is True and result['unfinished'] is None
                 and result['complete_declared_case_records'] is True and result['case_count']==52
                 and all(row['actual_status'].startswith('pass_') for row in result['results'] if row['id']!='W16-late-exit-or-held-EOF')
                 and next(row for row in result['results'] if row['id']=='W16-late-exit-or-held-EOF')['actual_status']=='not_exercised')
    except BaseException as failure:
        error={'type':type(failure).__name__,'message':str(failure)[:2048]};pending=False
    finally:
        # Final Source must preserve complete failure/partial lifecycle evidence,
        # even if new V4 bound is incomplete or unknown; never require success here.
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        invoke_fn(owner.cleanup, _cleanup=True)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        ledger={'launch_attempts':owner.launch_attempts,'observer_intervals':owner.observer_intervals,
                'memory_diagnostic':invoke_fn(owner.memory_diagnostic, _cleanup=True),'samples':owner.samples,'known_births':owner.known,'children':[
            {'role':child['role'],'reaped':child['reaped'],'observed_terminal_ns':child['observed_terminal_ns'],
             'kernel_peak_bytes':child['kernel_peak_bytes'],'pid':child['process'].pid,
             'launch_index':child['launch_index'],'usage':list(child['usage']) if child['usage'] is not None else None,
             'exit_code':child['process'].returncode} for child in owner.children]}
        ledger_raw=gzip.compress(canonical(ledger)+b'\n',mtime=0)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        invoke_fn(coor.write_exclusive, run/'owned-ledger.json.gz',ledger_raw, _cleanup=True)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original output inventory caller')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual output inventory caller cells')
        output_inventory=invoke_fn(coor.inventory,run,owner,success=False,_cleanup=True)
        final={'output_inventory_before_receipts':output_inventory,'schema':'Q-split-neutral-owned-controls-provisional-v1','status':'CONTROLS_PENDING_CALLER' if pending and error is None else 'UNKNOWN',
               'joint_began_ns':joint_began_ns,'joint_deadline_ns':owner.deadline_ns,'pending_caller':pending,'error':error,
               'result_complete':result is not None,'ownership_ledger':invoke_fn(coor.pin_bytes, ledger_raw, _cleanup=True),
               'all_reaped':all(child['reaped'] for child in owner.children),'leftovers':owner.leftovers,'cleanup_errors':owner.cleanup_errors,
               'ROOT_resource_accepted':False,'full_architecture_qualified':False,'original_Q_theorem_accepted':False,
               'selected_accepted':False,'point_union_accepted':False,'full24_accepted':False,'trajectory_accepted':False,'RL_accepted':False}
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        invoke_fn(coor.write_exclusive, run/'worker-provisional.json',canonical(final)+b'\n', _cleanup=True)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        native_bound=invoke_fn(owner.memory_diagnostic, _cleanup=True)
        pending=(pending and error is None and native_bound['complete'] is True
                 and native_bound['peak_bytes']+8*1048576<=coor.LIMITS['aggregate_owned_bytes']
                 and time.perf_counter_ns()+2000000000<owner.deadline_ns and not owner.leftovers and not owner.cleanup_errors)
        post={'schema':'Q-split-neutral-owned-controls-postwrite-v1','pending_caller':pending,
              'memory_bound':native_bound,'observed_postwrite_ns':time.perf_counter_ns(),'joint_deadline_ns':owner.deadline_ns,
              'failure_deadline_ns':owner.failure_ns,'owned_deadline_ns':owner.owned_ns,'ROOT_resource_accepted':False}
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        invoke_fn(coor.write_exclusive, run/'worker-postwrite.json',canonical(post)+b'\n', _cleanup=True)
        print(json.dumps({'status':'CONTROLS_PENDING_CALLER' if pending else 'UNKNOWN','pending_caller':pending,'ROOT_resource_accepted':False}),flush=True)
        if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
        if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
        final_bound=invoke_fn(owner.memory_diagnostic, _cleanup=True)
        pending=(pending and final_bound['complete'] is True and final_bound['peak_bytes']<=coor.LIMITS['aggregate_owned_bytes']
                 and time.perf_counter_ns()<owner.deadline_ns)
        if not pending:
            revoke={'schema':'Q-split-neutral-owned-controls-final-revocation-v1','pending_caller':False,
                    'observed_after_stdout_ns':time.perf_counter_ns(),'memory_diagnostic':final_bound,
                    'ROOT_resource_accepted':False,'full_architecture_qualified':False,'whole_outputs_preserved':True}
            if (invoke is not invoke_fn or invoke_fn.__code__ is not invocation_anchor['state'][2] or same_function is not same_fn or same_fn.__code__ is not same_anchor[2]):raise ValueError('original immediate main caller/shim')
            if not same_fn(invoke_fn,invocation_anchor['state']) or not same_fn(source_guard,source_guard_anchor):raise ValueError('actual main caller/callback defaults and cells')
            invoke_fn(coor.write_exclusive, run/'worker-revocation.json',canonical(revoke)+b'\n', _cleanup=True)
    return 0 if pending and error is None else 2

if __name__=='__main__':
    raise SystemExit('Reviewed early launcher required; direct worker CLI forbidden')
