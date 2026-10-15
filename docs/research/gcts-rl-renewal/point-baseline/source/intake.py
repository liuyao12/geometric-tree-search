"""Unexecuted point-only sequential cold intake, no point BASE authority.

Parent executes only stdlib. No Q parse, mathematical code, observer child or
exit callback. Actual external meter2 plus postterminal native clock is required
for max(SELF_cut+max(leaf peaks), true_terminal_T); all ROOT flags remain false.
"""
import time
_NATIVE_CLOCK_GETTIME_NS = time.clock_gettime_ns
_NATIVE_CLOCK_ID = time.CLOCK_MONOTONIC
EARLY_BEGAN_NS = _NATIVE_CLOCK_GETTIME_NS(_NATIVE_CLOCK_ID)
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import stat
import subprocess
import sys

VERSION = 'Q-point-compact-sequential-cold-intake-v1'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
_NATIVE_EXIT = os._exit
PLAN_MAX = 1048576
WIRE_MAX = 4*1048576+1024
OUTPUT_MAX = 512*1048576
SOURCE_PINS = {'codec': {'bytes': 5806, 'sha256': 'd0d922416aab576ab324397cee94e82c3ddf1e4f0131426f76802695934f88df'},
 'control_leaf': {'bytes': 931, 'sha256': '8da445dfea2046b46559bd2eda2d1e503f085babb60516fc90e7e566a62bbb0a'},
 'independent_checker': {'bytes': 46514,
                         'sha256': '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3'},
 'point_graph': {'bytes': 28531,
                 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'},
 'point_producer': {'bytes': 28623,
                    'sha256': '4be9709eb3b5d8da15a0fdbf313683e61983f53519ac843c01afc2fe8233d052'},
 'producer_bootstrap': {'bytes': 12467,
                        'sha256': 'f2159c4271a0c26c691e5e620b20ea336fc2c861571407e061cb366e002703f2'},
 'verifier': {'bytes': 48584, 'sha256': '464537845c62478412270214589481ac34c55588d191df097686de09508ba9ba'}}
RAW_INPUT_BINDINGS = {'architecture_choice': {'bytes': 6808,
                         'sha256': '62b0d66686f890c9f604192058bdba48a4b171e233f25767b1e1de88fffbd82f'},
 'declaration': {'bytes': 2683,
                 'sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc'},
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
RUNTIME = {'bytes': 102352,
 'path': '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',
 'sha256': 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e'}
LIMITS = {'aggregate_owned_bytes': 536870912,
 'caller_finish_reserve_seconds': 1,
 'caller_seconds': 90,
 'failure_only_seconds': 55,
 'joint_seconds': 20,
 'owned_seconds': 60}
DECLARATION_VALUE_SHA256 = 'f6ca72af011a9343f4661b5092d54565f668a978fd020734072267b76f89b7a3'
PROTOCOL_CHOICE = {'bytes': 4300, 'sha256': '3b829573958c972f1395a4e70b3a7803cbc746affa38184ec22f22b0130b328c'}

def need(ok, message):
    if not ok:
        raise ValueError(message)

def global_now_ns(_native=_NATIVE_CLOCK_GETTIME_NS, _clock_id=_NATIVE_CLOCK_ID):
    # Defaults retain the actual native callable and exact ID across delegates.
    # The caller's Source guard also seals this helper/code/defaults/globals.
    need(type(_clock_id) is int and time.clock_gettime_ns is _native
         and type(time.CLOCK_MONOTONIC) is int and time.CLOCK_MONOTONIC == _clock_id,
         'same native kernel clock callable and exact integer ID')
    stamp = _native(_clock_id)
    need(type(stamp) is int and stamp >= 0, 'native nonnegative global integer ns')
    return stamp

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

def raw_peak(usage):
    return usage.ru_maxrss * (1 if sys.platform == 'darwin' else 1024)

def stream_snapshot(record, destination, owner):
    """Read/hash/copy the complete original buffer; never decode Q payload."""
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}, 'complete configured pin')
    size = integer(record['bytes'], 0, 64 * 1048576)
    source = regular_fd(record['path'], os.O_RDONLY)
    dest = regular_fd(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        before = os.fstat(source)
        need(before.st_size == size, 'whole original source/input size')
        h, count = hashlib.sha256(), 0
        while True:
            owner.check()
            raw = os.read(source, 65536)
            if not raw:
                break
            count += len(raw)
            need(count <= size, 'whole snapshot; no prefix/suffix')
            h.update(raw)
            offset = 0
            while offset < len(raw):
                written = os.write(dest, raw[offset:])
                need(written > 0, 'whole snapshot write')
                offset += written
        after = os.fstat(source)
        need(count == size and h.hexdigest() == record['sha256'], 'authenticated same complete buffer')
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'stable original descriptor')
        os.fchmod(dest, 0o400)
        owner.check()
    finally:
        os.close(source)
        os.close(dest)
    return {'sha256': record['sha256'], 'bytes': count}

def two_lines(path, body_schema, completion_schema, owner):
    owner.check()
    raw = read_small(path, WIRE_MAX)
    need(raw.endswith(b'\n') and raw.count(b'\n') == 2, 'exact two complete JSON lines/EOF')
    body_line, completion_line, empty = raw.split(b'\n')
    need(empty == b'' and len(body_line) + 1 <= 4 * 1048576 and len(completion_line) + 1 <= 1024,
         'whole body/completion size bounds')
    body = decode(body_line, 4 * 1048576, diagnostic_floats=True)
    completion = decode(completion_line, 1024)
    need(canonical(body) == body_line and canonical(completion) == completion_line,
         'exact canonical complete response lines')
    need(type(body) is dict and body.get('schema') == body_schema, 'exact role response schema')
    need(type(completion) is dict and set(completion) ==
         {'schema', 'body_sha256', 'body_bytes', 'exit_zero_and_coordinator_deadline_required'}
         and completion['schema'] == completion_schema and
         completion['exit_zero_and_coordinator_deadline_required'] is True, 'exact complete response trailer')
    need(type(completion['body_bytes']) is int and completion['body_bytes'] == len(body_line) + 1
         and completion['body_sha256'] == hashlib.sha256(body_line + b'\n').hexdigest(), 'whole hash-linked response')
    owner.check()
    return body, pin_bytes(raw)

def inventory(run, owner, *, success):
    """Coordinator enumerates only its owned tree, not child-provided paths."""
    records, total = [], 0
    stack = [run]
    while stack:
        directory = stack.pop()
        for entry in sorted(os.scandir(directory), key=lambda entry: entry.name):
            owner.check(success=success)
            need(not entry.is_symlink(), 'no owned output link/path alias')
            path = Path(entry.path)
            if entry.is_dir(follow_symlinks=False):
                need(len(path.relative_to(run).parts) <= 64, 'bounded owned tree depth')
                stack.append(path)
            else:
                need(entry.is_file(follow_symlinks=False), 'regular owned output only')
                fd = regular_fd(path, os.O_RDONLY)
                try:
                    h, count = hashlib.sha256(), 0
                    before = os.fstat(fd)
                    while True:
                        owner.check(success=success)
                        block = os.read(fd, 65536)
                        if not block:
                            break
                        count += len(block)
                        total += len(block)
                        need(count <= 64 * 1048576 and total <= OUTPUT_MAX, 'whole output storage bound; no truncate')
                        h.update(block)
                    after = os.fstat(fd)
                    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
                         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), 'stable complete output')
                finally:
                    os.close(fd)
                records.append({'path': str(path.relative_to(run)), 'bytes': count, 'sha256': h.hexdigest()})
                need(len(records) <= 4000, 'whole owned output file bound')
    return {'complete': True, 'files': records, 'bytes': total,
            'scope': 'all files present before coordinator receipts; receipts pinned separately'}


class SequentialOwner:
    """Exactly reviewed leaf children; no observer/spawn after irreversible seal."""
    def __init__(self, began):
        self.began_ns = began
        self.deadline_ns = began + 20000000000
        self.failure_ns = began + 55000000000
        self.owned_ns = began + 60000000000
        self.children = []
        self.sealed = False
        self.cutoff = None
        self.cancelled = [False]

    def check(self, *, success=True):
        now = global_now_ns()
        need(not self.cancelled[0] and now < (self.deadline_ns if success else self.failure_ns),
             'original joint20/failure55; no reset')
        need(raw_peak(resource.getrusage(resource.RUSAGE_SELF)) < 524288000,
             'parent500MiB reserve; terminal whole512 gate remains external')
        return now

    def launch(self, role, argv, fds, run):
        # The same explicit check is exercised by the post-seal control.
        if self.sealed:
            raise RuntimeError('NO_SPAWN_AFTER_CUTOFF')
        need(all(c['reaped'] for c in self.children), 'prior leaf must be truly reaped before next Popen')
        self.check()
        with (run/(role+'-stdout.txt')).open('xb') as out, (run/(role+'-stderr.txt')).open('xb') as err:
            start = global_now_ns()
            proc = subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                pass_fds=tuple(fds),close_fds=True,start_new_session=True,cwd=str(run),
                env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})
        child = {'role':role,'process':proc,'pid':proc.pid,'launch_began_ns':start,
                 'reaped':False,'wait4_pid':None,'wait4_status':None,'usage':None,
                 'kernel_peak_bytes':None,'terminal_observed_ns':None,'returncode':None}
        self.children.append(child)
        return child

    def reap(self, child, *, blocking=False):
        if child['reaped']: return True
        pid,status,usage = os.wait4(child['pid'],0 if blocking else os.WNOHANG)
        if not pid: return False
        need(pid == child['pid'], 'exact native wait4 PID')
        code = os.waitstatus_to_exitcode(status)
        child.update(reaped=True,wait4_pid=pid,wait4_status=status,usage=usage,
                     kernel_peak_bytes=raw_peak(usage),terminal_observed_ns=global_now_ns(),returncode=code)
        child['process'].returncode = code
        return True

    def wait(self, child, *, expected_returncode=0):
        need(type(expected_returncode) is int and expected_returncode in (0,2), 'exact expected child returncode')
        while not self.reap(child):
            self.check()
            time.sleep(.01)
        self.check()
        need(child['returncode'] == expected_returncode and child['kernel_peak_bytes'] < 524288000,
             'timely complete expected leaf exit/500MiB')

    def cleanup(self):
        errors = []
        for child in self.children:
            if not child['reaped']:
                try: os.killpg(child['pid'],signal.SIGKILL)
                except ProcessLookupError: pass
                try: self.reap(child,blocking=True)
                except BaseException as error: errors.append(type(error).__name__+': '+str(error))
        return errors

    def seal(self):
        need(not self.sealed and all(c['reaped'] for c in self.children), 'whole true reaping before cutoff')
        need(all(a['terminal_observed_ns'] < b['launch_began_ns']
                 for a,b in zip(self.children,self.children[1:])), 'strict disjoint leaf lifetimes')
        self.sealed = True
        self.cutoff = {'schema':'Q-point-no-future-spawn-cutoff-v1',
            'observed_ns':global_now_ns(),'SELF_peak_bytes':raw_peak(resource.getrusage(resource.RUSAGE_SELF)),
            'all_reaped':True,'child_count':len(self.children),'no_future_spawn':True}
        return self.cutoff


def validate_plan(plan, own):
    fields = {'schema','purpose','invocation_id','output_directory','sources','inputs','original_sources',
              'runtime','limits','authorization','source_reviews','protocol_choice'}
    need(type(plan) is dict and set(plan) == fields and plan['schema'] == 'ROOT-point-compact-Q-cold-plan-v1',
         'exact new point-only plan; never old point BASE grant')
    need(plan['purpose'] in ('primary','controls'), 'separate target/control purpose')
    token = plan['invocation_id']
    need(type(token) is str and 1 <= len(token) <= 128 and
         all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:' for c in token), 'invocation')
    need(plan['runtime'] == RUNTIME and plan['original_sources'] == ORIGINAL_SOURCES,
         'unchanged runtime/original source7')
    need(plan['limits'] == LIMITS and all(type(v) is int for v in plan['limits'].values()), 'unchanged20/55/60/512/90+1')
    need(set(plan['sources']) == set(SOURCE_PINS)|{'intake'} and set(plan['inputs']) == set(RAW_INPUT_BINDINGS),
         'complete actual Source9/original input8')
    for role,pin in SOURCE_PINS.items():
        need({k:plan['sources'][role][k] for k in ('sha256','bytes')} == pin, 'fixed Source '+role)
    need({k:plan['sources']['intake'][k] for k in ('sha256','bytes')} == own, 'actual intake Source pin')
    for role,pin in RAW_INPUT_BINDINGS.items():
        need({k:plan['inputs'][role][k] for k in ('sha256','bytes')} == pin, 'whole original input '+role)
    need({k:plan['protocol_choice'][k] for k in ('sha256','bytes')} == PROTOCOL_CHOICE,
         'explicit ROOT ordinary-only sequential memory protocol')
    need(type(plan['source_reviews']) is dict and set(plan['source_reviews']) == {'ROOT','peer'},
         'genuine distinct whole current Source reviews')
    for role,pin in plan['source_reviews'].items():
        review = decode(read_small(pin['path'],1048576,pin),1048576)
        need(review['source_only'] is True and review['source_review_passed'] is True
             and type(review['scientific_calls']) is int and review['scientific_calls'] == 0
             and review['author_identity'] == '/root/arithmetic_induction'
             and review['reviewer_identity'] != '/root/arithmetic_induction'
             and (review['reviewer_identity'] == '/root' if role == 'ROOT' else
                  review['reviewer_identity'] != '/root')
             and review['scope'] == 'Q-point-compact-cold-intake-Source'
             and review['sources'] == plan['sources'], 'genuine exact current Source review '+role)
    need(plan['source_reviews']['ROOT'] != plan['source_reviews']['peer'], 'distinct review records')
    grantpin = plan['authorization']
    grant = decode(read_small(grantpin['path'],1048576,grantpin),1048576)
    need(grant['schema'] == 'ROOT-point-compact-Q-cold-authorization-v1' and grant['author_identity'] == '/root'
         and grant['actual_execution_authorized'] is True and grant['purpose'] == plan['purpose']
         and grant['invocation_id'] == token and grant['limits'] == LIMITS
         and grant['source_bindings'] == {r:{k:p[k] for k in ('sha256','bytes')} for r,p in plan['sources'].items()}
         and grant['binding'] == BINDING and grant['resource_rule'] == 'point-sequential-cutoff-max-v1'
         and grant['point_BASE_receives_ordinary_output'] is False, 'future scoped ROOT grant only')


def channel_set(paths, result):
    channels = []
    try:
        channels.extend(regular_fd(str(path),os.O_RDONLY) for path in paths)
        channels.append(regular_fd(str(result),os.O_WRONLY|os.O_CREAT|os.O_EXCL))
        return channels
    except BaseException:
        for fd in channels: os.close(fd)
        raise


FALSE_SCOPES = ('actual_selected_accepted', 'point_snapshot_accepted', 'full24_accepted', 'full_trajectory_accepted', 'native_accepted', 'RL_accepted', 'induction_accepted', 'full_PA_accepted')

def verifier_response(body, authority, authority_pin, candidate, candidate_pin, owner):
    fields = {'schema', 'version', 'coordinator_invocation_id', 'authority_raw_sha256',
        'candidate_raw_sha256', 'authority_value_sha256', 'candidate_value_sha256',
        'binding', 'source_bindings', 'submission_index', 'submissions_checked',
        'status', 'independent_word_certificate', 'rejection', 'producer_origin_claim',
        'producer_termination_claim', 'ROOT_primary_accepted', 'ROOT_resource_accepted',
        'joint_began_ns', 'joint_deadline_ns'} | set(FALSE_SCOPES)
    need(set(body) == fields and body['version'] == 'Q-clean-original-target-word-verifier-Source-v4-global-clock',
         'full expected current verifier body')
    need(body['coordinator_invocation_id'] == authority['coordinator_invocation_id']
         and body['authority_raw_sha256'] == authority_pin['sha256']
         and body['candidate_raw_sha256'] == candidate_pin['sha256']
         and body['authority_value_sha256'] == digest(authority)
         and body['candidate_value_sha256'] == digest(candidate)
         and body['binding'] == BINDING and body['source_bindings'] == authority['source_bindings'],
         'same exact authority/candidate context and Source roles')
    need(type(body['submission_index']) is int and body['submission_index'] == 0
         and type(body['submissions_checked']) is int and body['submissions_checked'] == 1,
         'one complete original first submission')
    need(all(body[field] is False for field in FALSE_SCOPES + ('ROOT_primary_accepted', 'ROOT_resource_accepted')),
         'no promoted secondary or producer resource authority')
    need(type(body['joint_began_ns']) is int and body['joint_began_ns'] == owner.began_ns
         and type(body['joint_deadline_ns']) is int and body['joint_deadline_ns'] == owner.deadline_ns,
         'original exact ns deadline')
    need(body['producer_origin_claim'] == candidate['origin']
         and body['producer_termination_claim'] == candidate['termination'], 'provenance claims retained')
    if body['status'] == 'WORD_REJECTED':
        need(body['independent_word_certificate'] is None and type(body['rejection']) is dict, 'complete rejection')
        return False
    need(body['status'] == 'WORD_VERIFIED_PENDING_COORDINATOR' and body['rejection'] is None, 'exact proof pending status')
    cert = body['independent_word_certificate']
    need(type(cert) is dict and cert.get('schema') == 'independent-Q-primitive-word-certificate-v1'
         and cert.get('completed') is True and cert.get('original_Gamma_target_sequent_accepted') is True,
         'complete independent word certificate')
    declaration = authority['declaration']
    need(cert['original_ordered_Gamma'] == declaration['ordered_Gamma']
         and cert['parameters'] == declaration['parameters'] and cert['target'] == declaration['target']
         and cert['theory_sha256'] == digest(declaration['theory'])
         and cert['commands_sha256'] == digest(candidate['commands']), 'certificate proves unchanged exact original sequent')
    need(cert['essential_rows'] == list(range(len(candidate['commands'])))
         and all(type(row) is int for row in cert['essential_rows']), 'every complete submitted command essential')
    need(all(cert.get(field) is False for field in ('native_accepted', 'full24_accepted',
        'current_state_point_union_accepted', 'full_trajectory_accepted', 'induction_accepted',
        'full_PA_accepted', 'universal_compiler_accepted', 'ROOT_resource_accepted')), 'exact word-only certificate scope')
    return True


def run_checker(owner, plan, run, snapshots, label, authority, candidate, *, expected_returncode=0):
    need(expected_returncode == 0 or (expected_returncode == 2 and plan['purpose']=='controls'
         and label=='bad-authority'), 'exit2 is exact corrupt-authority control only')
    authority_raw, candidate_raw = canonical(authority),canonical(candidate)
    authority_pin, candidate_pin = pin_bytes(authority_raw),pin_bytes(candidate_raw)
    need(len(authority_raw)<=1048576 and len(candidate_raw)<=2*1048576,'complete small checker inputs')
    ap,cp,rp=run/(label+'-authority.json'),run/(label+'-candidate.json'),run/(label+'-response.jsonl')
    write_exclusive(ap,authority_raw);write_exclusive(cp,candidate_raw)
    fds=channel_set([ap,cp,snapshots/'source-independent_checker.py'],rp)
    try:
        args=[fds[0],authority_pin['sha256'],authority_pin['bytes'],fds[1],candidate_pin['sha256'],
              candidate_pin['bytes'],*fds[2:],owner.began_ns,owner.deadline_ns]
        child=owner.launch(label,[RUNTIME['path'],'-I','-S','-B',str(snapshots/'source-verifier.py'),
                                  *map(str,args)],fds,run)
    finally:
        for fd in fds:os.close(fd)
    owner.wait(child,expected_returncode=expected_returncode)
    if expected_returncode == 2:
        response_raw=read_small(str(rp),WIRE_MAX)
        stderr_raw=read_small(str(run/(label+'-stderr.txt')),4096)
        need(response_raw==b'' and stderr_raw==
             b'ValueError: unchanged original raw inputs/model/authority/registry\n',
             'exact original authority rejection before response, not arbitrary exit2')
        owner.check()
        return {'schema':'Q-point-corrupt-authority-observation-v1',
                'status':'AUTHORITY_REJECTED_BEFORE_RESPONSE','response':pin_bytes(response_raw),
                'stderr':pin_bytes(stderr_raw),'actual_returncode':child['returncode'],
                'exact_required_stderr':stderr_raw.decode('ascii'),'ROOT_primary_accepted':False},pin_bytes(response_raw)
    body,pin=two_lines(str(rp),'Q-clean-verifier-response-body-v1',
                      'Q-clean-verifier-response-completion-v1',owner)
    verifier_response(body,authority,authority_pin,candidate,candidate_pin,owner)
    return body,pin


def bad_word(plan, declaration, authority_pin):
    # NEGATIVE CONTROL: original target wrongly tagged AZ; no valid proof route.
    return {'schema':'Q-untrusted-first-candidate-word-v1','coordinator_invocation_id':plan['invocation_id'],
        'authority_sha256':authority_pin['sha256'],'binding':BINDING,'submission_index':0,
        'commands':[{'rule':'axiom','name':'AZ','formula':declaration['target']}],
        'origin':{'kind':'producer_claimed_selected_original_target_ancestry',
                  'source_event_index':0,'physical_keys':[[0,0,[]]]},
        'termination':{'producer_status':'CANDIDATE_NOT_VERIFIED','root_rollback_claimed':True,
                       'proof_accepted':False,'full24_accepted':False,'trajectory_accepted':False}}


def main(argv, *, joint_began_ns):
    need(len(argv)==1 and sys.platform=='darwin','sole plan and pinned Darwin byte ABI')
    owner = SequentialOwner(integer(joint_began_ns,1))
    signal.signal(signal.SIGTERM,lambda *_:owner.cancelled.__setitem__(0,True))
    signal.signal(signal.SIGINT,lambda *_:owner.cancelled.__setitem__(0,True))
    owner.check()
    plan_raw = read_small(argv[0],PLAN_MAX);plan = decode(plan_raw,PLAN_MAX)
    own_raw = read_small(str(Path(__file__).resolve()),PLAN_MAX)
    validate_plan(plan,pin_bytes(own_raw))
    run = Path(plan['output_directory'])
    need(run.is_absolute() and run==run.resolve() and not run.exists(),'exclusive canonical point run')
    run.mkdir(mode=0o700)
    result, controls, error, certificate = None,[],None,None
    logical = False;cleanup_errors=[];pending=False
    try:
        snapshots=run/'authenticated-snapshots';snapshots.mkdir(mode=0o700)
        for role,pin in plan['inputs'].items():stream_snapshot(pin,snapshots/('input-'+role),owner)
        for role,pin in plan['original_sources'].items():stream_snapshot(pin,snapshots/('original-'+role),owner)
        for role,pin in plan['sources'].items():stream_snapshot(pin,snapshots/('source-'+role+'.py'),owner)
        stream_snapshot(RUNTIME,snapshots/'runtime-raw',owner)
        declaration=decode(read_small(str(snapshots/'input-declaration'),2683,RAW_INPUT_BINDINGS['declaration']),2683)
        need(digest(declaration)==DECLARATION_VALUE_SHA256,'exact original declaration/emptyGamma/target')
        authority={'schema':'Q-clean-verifier-fixed-authority-v1','coordinator_invocation_id':plan['invocation_id'],
            'declaration':declaration,'binding':BINDING,'raw_input_bindings':RAW_INPUT_BINDINGS,
            'source_bindings':{r:{k:plan['sources'][r][k] for k in ('sha256','bytes')}
                 for r in ('verifier','independent_checker','point_graph')}|
                 {'coordinator':pin_bytes(own_raw),'producer':SOURCE_PINS['point_producer']},'limits':LIMITS}
        authority_raw=canonical(authority);authority_pin=pin_bytes(authority_raw)
        if plan['purpose']=='controls':
            for label in ('a','b'):
                child=owner.launch('inert-'+label,[RUNTIME['path'],'-I','-S','-B',
                    str(snapshots/'source-control_leaf.py'),label,str(owner.began_ns),str(owner.deadline_ns)],[],run)
                owner.wait(child)
            controls.append({'id':'real-sequential-leaves','child_indices':[0,1],
                'kernel_peak_bytes':[c['kernel_peak_bytes'] for c in owner.children],
                'disjoint_closed_lifetimes':owner.children[0]['terminal_observed_ns']<
                                           owner.children[1]['launch_began_ns'],
                'true_wait4_reaped':all(c['reaped'] for c in owner.children)})
            candidate=bad_word(plan,declaration,authority_pin)
            body,pin=run_checker(owner,plan,run,snapshots,'bad-word',authority,candidate)
            need(body['status']=='WORD_REJECTED' and body['independent_word_certificate'] is None,'genuine unchanged-checker negative control')
            controls.append({'id':'corrupt-word','response':pin,'actual_response':body})
            corrupt=dict(authority,binding=dict(BINDING,model_epoch='0'*64))
            candidate=dict(candidate,authority_sha256=pin_bytes(canonical(corrupt))['sha256'])
            body,pin=run_checker(owner,plan,run,snapshots,'bad-authority',corrupt,candidate,expected_returncode=2)
            need(body['status']=='AUTHORITY_REJECTED_BEFORE_RESPONSE' and body['actual_returncode']==2,
                 'actual original authority rejection, not arbitrary Source/clock failure')
            controls.append({'id':'corrupt-authority','response':pin,'actual_response':body})
        else:
            event_base=run/'producer-event-base';event_base.mkdir(mode=0o700)
            event_directory=event_base/'producer-events' # Initially absent; producer creates it.
            manifest={'schema':'Q-point-compact-producer-manifest-v1','coordinator_invocation_id':plan['invocation_id'],
                'authority_sha256':authority_pin['sha256'],'declaration':declaration,'binding':BINDING,
                'original_source_bindings':ORIGINAL_SOURCES,
                'source_bindings':{'bootstrap':{k:plan['sources']['producer_bootstrap'][k] for k in ('sha256','bytes')},
                     'codec':SOURCE_PINS['codec'],'point_graph':SOURCE_PINS['point_graph'],
                     'producer':SOURCE_PINS['point_producer']},'event_directory':str(event_directory)}
            mp=run/'producer-manifest.json';mraw=canonical(manifest);write_exclusive(mp,mraw);mpin=pin_bytes(mraw)
            fds=channel_set([mp,snapshots/'input-preparation',snapshots/'source-codec.py',
                             snapshots/'source-point_graph.py',snapshots/'source-point_producer.py'],run/'producer-response.jsonl')
            try:
                args=[fds[0],mpin['sha256'],mpin['bytes'],*fds[1:],owner.began_ns,owner.deadline_ns]
                child=owner.launch('producer',[RUNTIME['path'],'-I','-S','-B',
                    str(snapshots/'source-producer_bootstrap.py'),*map(str,args)],fds,run)
            finally:
                for fd in fds:os.close(fd)
            owner.wait(child) # COMPLETE true wait4 before any clean checker Popen.
            body,ppin=two_lines(str(run/'producer-response.jsonl'),'Q-point-compact-producer-response-body-v1',
                                'Q-point-compact-producer-response-completion-v1',owner)
            need(body['authority_sha256']==authority_pin['sha256'] and body['binding']==BINDING
                 and body['coordinator_invocation_id']==plan['invocation_id']
                 and body['source_bindings']==manifest['source_bindings'],'point whole producer context')
            result=body['result'];need(result['schema']=='Q-full-original-model-untrusted-producer-return-v1'
                 and result['version']=='Q-full-original-model-untrusted-compact-candidate-Source-v4'
                 and result['CLOCK_DOMAIN']==CLOCK_DOMAIN
                 and result['joint_began_ns']==owner.began_ns and result['joint_deadline_ns']==owner.deadline_ns,
                 'exact compact point return/native context')
            candidate=result.get('candidate')
            need(result['producer_status']=='CANDIDATE_NOT_VERIFIED' and type(candidate) is dict,
                 'NO_POINT_CANDIDATE_UNKNOWN; no rescue/restart/negative theorem')
            candidate=decode(canonical(candidate),2*1048576)
            body,pin=run_checker(owner,plan,run,snapshots,'verifier',authority,candidate)
            certificate=body['independent_word_certificate']
            logical=(body['status']=='WORD_VERIFIED_PENDING_COORDINATOR' and certificate is not None)
            need(logical,'point-produced word not independently accepted; retain rejection UNKNOWN')
        owner.check()
    except BaseException as failure:
        error={'type':type(failure).__name__,'message':str(failure)[:2048]}
    finally:
        cleanup_errors=owner.cleanup()
        try:output_inventory=inventory(run,owner,success=error is None)
        except BaseException as failure:
            output_inventory={'complete':False,'error':type(failure).__name__+': '+str(failure)}
            if error is None:error=output_inventory['error']
        # Final owned-child activity is over. No later branch can Popen/fork,
        # invoke a callback or a generic cleanup/observer. Native exit below
        # skips Python atexit/finalizers and leaves terminal T to the meter.
        try:cut=owner.seal()
        except BaseException as failure:
            print('POINT_CUTOFF_UNKNOWN: '+str(failure),file=sys.stderr,flush=True)
            _NATIVE_EXIT(2)
        denied=None
        tail=None
        post_tail_self=None
        if plan['purpose']=='controls':
            before=len(owner.children)
            try:owner.launch('forbidden-after-cutoff',[RUNTIME['path'],'-I','-S','-B',
                 str(snapshots/'source-control_leaf.py'),'a',str(owner.began_ns),str(owner.deadline_ns)],[],run)
            except RuntimeError as rejection:denied=str(rejection)=='NO_SPAWN_AFTER_CUTOFF'
            need(denied is True and len(owner.children)==before,'sealed launch denied before Popen')
            controls.append({'id':'postseal-launch-denial','specific_rejection':'NO_SPAWN_AFTER_CUTOFF',
                'otherwise_valid_fixed_leaf_arguments':True,'children_before':before,
                'children_after':len(owner.children),'Popen_reached':False})
            # Explicit NONLOGICAL post-cutoff parent-memory tail; kept live
            # until captured native exit. Actual external T must account it.
            tail=bytearray(32*1048576)
            for offset in range(0,len(tail),4096):tail[offset]=1
            post_tail_self=raw_peak(resource.getrusage(resource.RUSAGE_SELF))
            need(post_tail_self>cut['SELF_peak_bytes'],'actual resident parent exit-tail growth')
            controls.append({'id':'parent-exit-tail','resident_requested_bytes':len(tail),
                'touched_pages':len(tail)//4096,'SELF_cut':cut['SELF_peak_bytes'],
                'SELF_after_tail':post_tail_self,'external_true_terminal_must_cover_tail':True,
                'external_control_accepted':False})
        children=[{k:v for k,v in c.items() if k not in ('process','usage')}|
                  {'usage':None if c['usage'] is None else
                           [{'kind':'float','hex':x.hex()} if type(x)is float else x for x in c['usage']]}
                  for c in owner.children]
        peak=max((c['kernel_peak_bytes'] for c in owner.children if c['kernel_peak_bytes'] is not None),default=0)
        live_bound=cut['SELF_peak_bytes']+peak
        now=global_now_ns()
        complete=output_inventory['complete'] is True and not cleanup_errors and all(c['reaped'] for c in children)
        pending=(error is None and complete and not owner.cancelled[0] and now<owner.deadline_ns
                 and live_bound<=536870912 and (logical if plan['purpose']=='primary' else denied is True))
        final={'schema':'Q-point-compact-cold-intake-provisional-v1','version':VERSION,'purpose':plan['purpose'],
            'invocation_id':plan['invocation_id'],'plan':pin_bytes(plan_raw),'binding':BINDING,'limits':LIMITS,
            'joint_began_ns':owner.began_ns,'joint_deadline_ns':owner.deadline_ns,
            'status':'WORD_VERIFIED_PENDING_CALLER' if pending and logical else
                     'CONTROLS_PENDING_EXTERNAL_TERMINAL' if pending else 'UNKNOWN',
            'primary_pending_caller':pending and logical,'controls_pending_caller':pending and plan['purpose']=='controls',
            'word_logically_accepted':logical,'certificate':certificate,'producer_result':result,
            'controls':controls,'post_seal_launch_denied':denied,'post_seal_tail_bytes':0 if tail is None else len(tail),
            'cutoff':cut,'children':children,'maximum_leaf_peak_bytes':peak,'live_epoch_bound_bytes':live_bound,
            'external_rule':'max(SELF_cut+max(all sequential leaf peaks),true external terminal inclusive T)',
            'output_inventory':output_inventory,'cleanup_errors':cleanup_errors,'error':error,
            'ROOT_primary_accepted':False,'ROOT_resource_accepted':False,'selected_provenance_accepted':False,
            'point_state_accepted':False,'full24_accepted':False,'trajectory_accepted':False,'RL_accepted':False,
            'native_accepted':False,'Q_BASE_output_injected':False,'external_true_terminal_required':True}
        final_raw=canonical(final)+b'\n';need(len(final_raw)<=8*1048576,'complete final record bound')
        write_exclusive(run/'point-provisional.json',final_raw)
        os.write(1,canonical({'schema':'Q-point-compact-cold-final-observation-v1','provisional':pin_bytes(final_raw),
             'pending_external':pending,'purpose':plan['purpose'],'ROOT_primary_accepted':False})+b'\n')
        timely=(pending and not owner.cancelled[0] and global_now_ns()<owner.deadline_ns)
        _NATIVE_EXIT(0 if timely else 2)


if __name__ == '__main__':
    try:
        main(sys.argv[1:],joint_began_ns=EARLY_BEGAN_NS)
    except BaseException as error:
        os.write(2,('POINT_INTAKE_UNKNOWN: '+type(error).__name__+': '+str(error)+'\n').encode('utf8'))
        _NATIVE_EXIT(2)

