"""UNEXECUTED neutral producer-role whole-model O07/O08 census leaf.

No word/search/placement/selection/checker is executed. Complete original raw
preparation is authenticated/decode/released/parsed once inside this fresh leaf.
Current full PointGraph fixture=False and all24 initial domains are compared
byte-for-byte with original cold-owned state/oracle FDs. Claims remain untrusted
until the Root owner closes native sources/EOF/terminal/resources.
"""
import builtins
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import stat
import sys
import time
import types

VERSION = 'Q-neutral-full-model-census-leaf-v2-global-clock'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
MANIFEST_SCHEMA = 'Q-neutral-full-model-census-manifest-v1'
SOURCE_PINS = {'codec': {'bytes': 5806,
           'sha256': 'd0d922416aab576ab324397cee94e82c3ddf1e4f0131426f76802695934f88df'},
 'point_graph': {'bytes': 28531,
                 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'}}
PREPARATION = {'bytes': 38376960,
 'sha256': '0321a462025357d188793bd45a44670adc20776e9ba30574049d77a8b5935d3a'}
STATE_PIN = {'bytes': 8296118,
 'sha256': 'c7e8cfd099b1b80ae170b6c35591d68d56f37aecb38f1bcf7b567d2e019acbb9'}
ORACLE_PIN = {'bytes': 8295473,
 'sha256': '03c42ca0083d5e40363d5237d69af56df4ebe3b3ae7d88fa3720fae3390d6969'}
BINDING = {'declaration_sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc',
 'formula_registry_sha256': '4a12ada631861b1637b7d5e17e76c45b9a942816c412f5a6f0fc48c1698eb7fe',
 'model_epoch': '3a8854e0e0137d125dfa8af8870be04e4242ec2e7036b6bb8977cd33ad1454f9',
 'primitive_authority_epoch': '4ac41a90b9655036e2e7ed6cd7d9a971b9097d6b2c7d0f70e8408b8d93a54039'}
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
DECLARATION_VALUE_SHA256 = 'f6ca72af011a9343f4661b5092d54565f668a978fd020734072267b76f89b7a3'
ALLOWED_IMPORTS = {'__future__',
 'copy',
 'dataclasses',
 'gzip',
 'hashlib',
 'json',
 'math',
 'pathlib',
 'resource',
 'time',
 'typing'}


def need(value, message):
    if not value:
        raise ValueError(message)


def decimal(text):
    need(type(text) is str and text and len(text) <= 32
         and all(c in '0123456789' for c in text), 'literal nonnegative decimal argument')
    value = int(text)
    need(value <= (1 << 63) - 1, 'signed64 interface integer')
    return value


class Budget:
    """Native untrusted guidance; exact integer-ns coordinator clock is authoritative."""
    def __init__(self, began_ns, deadline_ns):
        need(type(began_ns) is int and type(deadline_ns) is int
             and deadline_ns - began_ns == 20000000000, 'same original joint20e9 ns')
        need(type(time.CLOCK_MONOTONIC) is int, 'exact native global monotonic clock id')
        self.clock_module, self.clock, self.clock_id = time, time.clock_gettime_ns, time.CLOCK_MONOTONIC
        self.began_ns, self.deadline_ns = began_ns, deadline_ns
        self.check()

    def check(self, *, cleanup=False):
        if time is not self.clock_module or time.clock_gettime_ns is not self.clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != self.clock_id:
            raise ValueError('original actual native global clock endpoint/id changed')
        now = self.clock(self.clock_id)
        if now - self.began_ns >= 55000000000 or resource.getrusage(resource.RUSAGE_SELF).ru_maxrss >= 524288000:
            raise TimeoutError('bootstrap failure55/500 reserve exceeded')
        if not cleanup and now >= self.deadline_ns:
            raise TimeoutError('coordinator joint20 unfinished')


def fd_mode(fd, *, writable=False):
    need(type(fd) is int and fd >= 3, 'explicit inherited descriptor, not stdio')
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    need((flags & os.O_ACCMODE) == (os.O_WRONLY if writable else os.O_RDONLY),
         'result write-only and immutable inputs read-only')
    if not writable:
        need(stat.S_ISREG(os.fstat(fd).st_mode) and os.lseek(fd, 0, os.SEEK_CUR) == 0,
             'coordinator snapshot regular input at complete offset0')


def read_exact(fd, record, budget):
    need(type(record) is dict and set(record) == {'sha256', 'bytes'}
         and type(record['bytes']) is int and record['bytes'] >= 0
         and type(record['sha256']) is str and len(record['sha256']) == 64
         and all(c in '0123456789abcdef' for c in record['sha256']), 'exact buffer digest/length')
    budget.check()
    before = os.fstat(fd)
    need(before.st_size == record['bytes'], 'whole regular input length, no prefix')
    data = bytearray()
    digest = hashlib.sha256()
    while len(data) < record['bytes']:
        budget.check()
        block = os.read(fd, min(65536, record['bytes'] - len(data)))
        need(block, 'complete authenticated input, no early EOF')
        data.extend(block)
        digest.update(block)
    need(os.read(fd, 1) == b'', 'complete single input EOF')
    after = os.fstat(fd)
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
         == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
         'coordinator-owned snapshot unchanged while read')
    need(digest.hexdigest() == record['sha256'], 'whole input SHA, no subset')
    budget.check()
    result = bytes(data)
    del data
    return result


def unique(pairs):
    value = {}
    for name, child in pairs:
        need(name not in value, 'duplicate manifest field')
        value[name] = child
    return value


def load_source(role, raw, invocation, budget):
    budget.check()
    name = '_Q_untrusted_bootstrap_' + role + '_' + hashlib.sha256(invocation.encode()).hexdigest()[:16]
    need(name not in sys.modules, 'fresh private registered Source namespace')
    module = types.ModuleType(name)
    module.__file__ = '<Q-authenticated-FD-' + role + '-' + SOURCE_PINS[role]['sha256'] + '>'
    original_import = builtins.__import__
    def imports(name, globals=None, locals=None, fromlist=(), level=0):
        need(level == 0 and name.split('.')[0] in ALLOWED_IMPORTS, 'stdlib-only explicit producer imports')
        return original_import(name, globals, locals, fromlist, level)
    module.__dict__['__builtins__'] = dict(vars(builtins), __import__=imports)
    sys.modules[name] = module  # dataclass decorators require real module registration.
    try:
        code = compile(raw, module.__file__, 'exec')
        exec(code, module.__dict__)
    except BaseException:
        del sys.modules[name]
        raise
    budget.check()
    return module


def line(value, maximum):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode('utf8')
    need(len(raw) <= maximum, 'complete response line limit; never truncate')
    return raw


def write_all(fd, raw, budget, *, cleanup):
    view = memoryview(raw)
    try:
        while view:
            budget.check(cleanup=cleanup)
            count = os.write(fd, view[:65536])
            need(count > 0, 'whole response transport progress')
            view = view[count:]
    finally:
        view.release()
    budget.check(cleanup=cleanup)



class WitnessMismatch(ValueError):
    pass


def canonical_chunks(value, budget):
    parts, length = [], 0
    for piece in json.JSONEncoder(sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                                  allow_nan=False).iterencode(value):
        parts.append(piece)
        length += len(piece)
        if length >= 16384:
            budget.check()
            yield ''.join(parts).encode('utf8')
            parts, length = [], 0
    if parts:
        budget.check()
        yield ''.join(parts).encode('utf8')


def compare_fd(value, fd, expected, budget):
    """Full canonical bytes/hash/length/EOF, not counts or sampled factors."""
    os.lseek(fd, 0, os.SEEK_SET)
    fd_mode(fd)
    before = os.fstat(fd)
    need(before.st_size == expected['bytes'], 'whole frozen witness length')
    count, h = 0, hashlib.sha256()
    for raw in canonical_chunks(value, budget):
        budget.check()
        got = bytearray()
        while len(got) < len(raw):
            block = os.read(fd, len(raw) - len(got))
            if not block:
                raise WitnessMismatch('canonical view extends beyond authenticated witness')
            got.extend(block)
        if got != raw:
            raise WitnessMismatch('whole canonical view/witness differ near byte ' + str(count))
        count += len(raw)
        h.update(raw)
    if os.read(fd, 1) != b'':
        raise WitnessMismatch('whole canonical view omits witness suffix')
    after = os.fstat(fd)
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
         == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'original witness FD unchanged')
    need(count == expected['bytes'] and h.hexdigest() == expected['sha256'], 'complete original witness SHA/EOF')
    budget.check()
    return {'sha256': h.hexdigest(), 'bytes': count, 'complete_EOF': True}


def stream_hash(value, budget):
    h, size = hashlib.sha256(), 0
    for raw in canonical_chunks(value, budget):
        h.update(raw)
        size += len(raw)
    budget.check()
    return {'sha256': h.hexdigest(), 'bytes': size}


def parse_manifest(raw):
    value = json.loads(raw.decode('utf8'), object_pairs_hook=unique,
                       parse_constant=lambda token: (_ for _ in ()).throw(ValueError('nonfinite manifest')))
    need(type(value) is dict and set(value) == {'schema', 'coordinator_invocation_id', 'declaration',
         'binding', 'original_source_bindings', 'source_bindings', 'input_bindings', 'scopes'}, 'exact manifest8')
    need(value['schema'] == MANIFEST_SCHEMA and value['binding'] == BINDING
         and value['original_source_bindings'] == ORIGINAL_SOURCES, 'unchanged complete original model/source epoch')
    nonce = value['coordinator_invocation_id']
    need(type(nonce) is str and 1 <= len(nonce) <= 128
         and all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:' for c in nonce), 'native coordinator nonce')
    declaration = value['declaration']
    need(hashlib.sha256(json.dumps(declaration, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
         allow_nan=False).encode('utf8')).hexdigest() == DECLARATION_VALUE_SHA256, 'whole exact original declaration, no route')
    need(value['input_bindings'] == {'preparation': PREPARATION, 'initial_state': STATE_PIN, 'initial_oracle': ORACLE_PIN}, 'full original input records')
    need(type(value['source_bindings']) is dict and set(value['source_bindings']) == {'census_leaf', 'codec', 'point_graph'}, 'only3 executed leaf roles')
    for role in SOURCE_PINS:
        need(value['source_bindings'][role] == SOURCE_PINS[role], 'exact immutable source role ' + role)
    own = Path(__file__).read_bytes()
    need(value['source_bindings']['census_leaf'] == {'sha256': hashlib.sha256(own).hexdigest(), 'bytes': len(own)}, 'own Root-invoked leaf source')
    need(value['scopes'] == {'search': False, 'placement': False, 'proof': False, 'parent_preparation_parse': False}, 'neutral role scope only')
    return value


def main(arguments):
    need(len(arguments) == 11, 'manifestFD/hash/length prepFD codecFD pointFD stateFD oracleFD resultFD beginNS deadlineNS')
    manifest_fd = decimal(arguments[0])
    manifest_pin = {'sha256': arguments[1], 'bytes': decimal(arguments[2])}
    need(manifest_pin['bytes'] <= 1048576, 'whole small manifest')
    prep_fd, codec_fd, point_fd, state_fd, oracle_fd, result_fd = map(decimal, arguments[3:9])
    began, deadline = map(decimal, arguments[9:11])
    budget = Budget(began, deadline)
    fds = [manifest_fd, prep_fd, codec_fd, point_fd, state_fd, oracle_fd, result_fd]
    need(len(set(fds)) == 7, 'seven distinct owned FD channels')
    for fd in fds[:-1]:
        fd_mode(fd)
    fd_mode(result_fd, writable=True)
    manifest = parse_manifest(read_exact(manifest_fd, manifest_pin, budget))
    modules, role_census = {}, []
    for role, fd in (('codec', codec_fd), ('point_graph', point_fd)):
        raw = read_exact(fd, SOURCE_PINS[role], budget)
        modules[role] = load_source(role, raw, manifest['coordinator_invocation_id'], budget)
        role_census.append({'role': role, 'authenticated_raw': {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)},
                            'registered_module': modules[role].__name__, 'compiled_filename': modules[role].__file__,
                            'same_buffer_exec_completed': True})
        del raw
    raw_preparation = read_exact(prep_fd, PREPARATION, budget)
    text = modules['codec'].decode_lossless_preparation(raw_preparation, budget)
    del raw_preparation
    preparation = modules['codec'].parse_lossless_preparation_text(text, budget)
    del text
    budget.check()
    catalogue = preparation['catalogue']
    need(catalogue['declaration'] == manifest['declaration'] and catalogue['height'] == 24,
         'complete original emptyGamma declaration24')
    boundary = catalogue['boundary']
    graph = modules['point_graph'].PointGraph(height=catalogue['height'], formulas=catalogue['formula_codes'],
        recipe_data=catalogue['recipes'], context=catalogue['context'], authority=catalogue['authority'],
        fixed_marks=boundary['fixed_marks'], roots=boundary['roots'], seed_keys=(), fixture=False,
        source_bindings=ORIGINAL_SOURCES)
    budget.check()
    need(graph.model_epoch == BINDING['model_epoch'] and graph.registry_sha == BINDING['formula_registry_sha256']
         and graph.authority_epoch == BINDING['primitive_authority_epoch'] and graph.initial_selected == (), 'all exact original graph epochs/no seed')
    state = graph.semantic_state()
    need(state == preparation['initial_state'], 'whole actual initial state matches original complete parse')
    need(len(graph.formulas) == 11147 and len(graph.recipes) == 16200 and len(state['domains']) == 24
         and state['order'] == [] and state['selected_generations'] == [], 'full inventories/current state, no selected fact')
    del preparation
    state_match = compare_fd(state, state_fd, STATE_PIN, budget)
    domains_match = compare_fd(state['domains'], oracle_fd, ORACLE_PIN, budget)
    rows = []
    for row, domain in enumerate(state['domains']):
        budget.check()
        need(type(domain['count']) is int and type(domain['base_count']) is int and type(domain['factors']) is list,
             'literal whole initial factor record')
        rows.append({'row': row, 'factor_count': len(domain['factors']), 'count': domain['count'],
                     'base_count': domain['base_count'], 'complete_domain': stream_hash(domain, budget)})
    controls = []
    views = [('omit-required-row23', state['domains'][:-1])]
    last_factor_view = [dict(domain) for domain in state['domains']]
    need(last_factor_view[-1]['factors'], 'actual last-row factor exists for whole omission calibration')
    last_factor_view[-1]['factors'] = last_factor_view[-1]['factors'][:-1]
    views.append(('omit-last-factor-row23', last_factor_view))
    for label, view in views:
        view_pin = stream_hash(view, budget)
        try:
            compare_fd(view, oracle_fd, ORACLE_PIN, budget)
        except WitnessMismatch as error:
            controls.append({'label': label, 'actual_rejected': True, 'error_type': type(error).__name__,
                             'message': str(error), 'control_view': view_pin, 'original_output_preserved': True})
        else:
            raise ValueError('incomplete control view cannot pass complete original oracle')
    # Recompare full original state and full oracle after both views; no subset
    # becomes the current Graph, catalogue, original witness or accepted output.
    after_state = compare_fd(state, state_fd, STATE_PIN, budget)
    after_domains = compare_fd(state['domains'], oracle_fd, ORACLE_PIN, budget)
    need(after_state == state_match and after_domains == domains_match, 'entire original outputs unchanged after calibration views')
    body = {'schema': 'Q-neutral-full-model-census-response-v1', 'coordinator_invocation_id': manifest['coordinator_invocation_id'],
            'binding': BINDING, 'input_bindings': manifest['input_bindings'], 'source_bindings': manifest['source_bindings'],
            'same_buffer_execution_census': role_census, 'preparation_decodes': 1, 'preparation_parses': 1,
            'caller_raw_released_before_parse': True, 'text_released_after_parse': True,
            'formula_count': len(graph.formulas), 'recipe_count': len(graph.recipes), 'row_count': len(rows),
            'full_state_match': state_match, 'full_domains_match': domains_match, 'all24_rows': rows,
            'O08_controls': controls, 'constructor_returned': True, 'fixture': False,
            'search_calls': 0, 'placements': graph.metrics['placements'], 'selected_facts': len(state['order']),
            'original_Q_theorem_accepted': False, 'selected_accepted': False, 'point_union_accepted': False,
            'full24_accepted': False, 'trajectory_accepted': False, 'ROOT_resource_accepted': False, 'RL_accepted': False,
            'joint_began_ns': began, 'joint_deadline_ns': deadline}
    body_raw = line(body, 4 * 1048576)
    trailer_raw = line({'schema': 'Q-neutral-full-model-census-completion-v1', 'body_sha256': hashlib.sha256(body_raw).hexdigest(),
                        'body_bytes': len(body_raw), 'exit_zero_and_coordinator_deadline_required': True}, 1024)
    budget.check()
    write_all(result_fd, body_raw, budget, cleanup=False)
    write_all(result_fd, trailer_raw, budget, cleanup=False)
    budget.check()
    os.close(result_fd)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except BaseException as failure:
        if isinstance(failure, SystemExit):
            raise
        print('NEUTRAL_CENSUS_FAILURE: ' + type(failure).__name__ + ': ' + str(failure)[:1024], file=sys.stderr, flush=True)
        sys.exit(2)
