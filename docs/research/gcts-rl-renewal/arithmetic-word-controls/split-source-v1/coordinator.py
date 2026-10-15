"""UNEXECUTED once-only coordinator Source for the original full Q model.

This process imports only stdlib. It does not execute a project checker or
producer, and parses no preparation/point/oracle payload. Authenticated bytes
are copied to exclusive owned files and supplied as readonly descriptors.
Fresh children execute separate authenticated Source snapshots. No candidate
path, callable, proof flag or resource claim grants authority.

The CLI accepts one previously reviewed frozen baseline plan. A new owned
controls/resource admission and distinct Source reviews are mandatory first.
There is no admission/plan in this Source packet, and no actual was run.
Ordinary process separation is assumed: this is not hostile-OS isolation.
"""
import gzip
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
import time

VERSION = 'Q-split-owned-original-model-coordinator-Source-v2'
# Literal pins are inserted by the saved AST-only authoring script. Project
# modules are not imported to obtain them. No new model or proof is constructed.
SOURCE_PINS = {'bootstrap': {'bytes': 12502,
               'sha256': '7f6a091303f016c5ad732786c5e1ea76a85caf0c0700236187106f6d2e271857'},
 'codec': {'bytes': 5806,
           'sha256': 'd0d922416aab576ab324397cee94e82c3ddf1e4f0131426f76802695934f88df'},
 'independent_checker': {'bytes': 46514,
                         'sha256': '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3'},
 'point_graph': {'bytes': 28531,
                 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'},
 'producer': {'bytes': 20219,
              'sha256': '994b1ff8f3edf2621826f64fe7d974dee9041fa211e1990d76362268eb607f36'},
 'verifier': {'bytes': 42086,
              'sha256': 'a5cfbe5c72ab617d1c98b1939c4d24aefc0e1c701e36b5fc141dc48bd1ea329b'}}
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
PLAN_MAX = 1024 * 1024
WIRE_MAX = 4 * 1024 * 1024 + 1024
OUTPUT_MAX = 512 * 1024 * 1024
FALSE_SCOPES = ('actual_selected_accepted', 'point_snapshot_accepted',
    'full24_accepted', 'full_trajectory_accepted', 'native_accepted',
    'RL_accepted', 'induction_accepted', 'full_PA_accepted')


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
            need(pin_bytes(raw) == expected, 'same complete authenticated file buffer')
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


class Owner:
    """Native clocks, direct wait4 peaks, birth/pgid owned-row ledger.

    Sampled ownership relies on the fixed source and ordinary non-adversarial
    child lifecycle; sampling cannot prove arbitrary hostile escaped processes
    absent. Conservative sequential direct-child peaks are summed, not reset.
    The ps observer is measured separately and its peak added exactly once.
    """
    def __init__(self, began_ns):
        self.began_ns = began_ns
        self.deadline_ns = began_ns + 20000000000
        self.failure_ns = began_ns + 55000000000
        self.owned_ns = began_ns + 60000000000
        self.children = []
        self.samples = []
        self.observer_peak = 0
        self.child_peak_sum = 0
        self.cancelled = False
        self.known = {}
        self.cleanup_errors = []
        self.leftovers = []
        self.max_combined = 0

    def check(self, *, success=True):
        now = time.perf_counter_ns()
        need(not self.cancelled, 'owned invocation interrupted')
        need(now < (self.deadline_ns if success else self.failure_ns), 'original joint20/failure55 deadline')
        combined = raw_peak(resource.getrusage(resource.RUSAGE_SELF)) + self.child_peak_sum + self.observer_peak
        need(combined <= LIMITS['aggregate_owned_bytes'], 'conservative aggregate owned memory')
        return now

    def table(self):
        # Observer stderr/stdout go to anonymous regular files, not hidden pipes.
        import tempfile
        observer = None
        usage = None
        began = time.perf_counter_ns()
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            try:
                observer = subprocess.Popen(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,rss=,lstart='],
                    stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True,
                    env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
                while usage is None:
                    pid, status, usage_now = os.wait4(observer.pid, os.WNOHANG)
                    if pid:
                        usage = usage_now
                        observer.returncode = os.waitstatus_to_exitcode(status)
                        break
                    need(time.perf_counter_ns() - began < 2000000000, 'observer bounded two-second lifetime')
                    time.sleep(.01)
                need(observer.returncode == 0, 'terminal successful observer')
                need(out.tell() <= 4 * 1048576 and err.tell() <= 4 * 1048576, 'whole observer output bound')
                out.seek(0)
                raw = out.read()
            finally:
                if observer is not None and usage is None:
                    try:
                        os.kill(observer.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    _, status, usage = os.wait4(observer.pid, 0)
                    observer.returncode = os.waitstatus_to_exitcode(status)
                if usage is not None:
                    self.observer_peak = max(self.observer_peak, raw_peak(usage))
        rows = {}
        for line in raw.decode('utf8', 'strict').splitlines():
            fields = line.split()
            if not fields:
                continue
            need(len(fields) == 9, 'complete observer grammar')
            pid, ppid, pgid, rss = [int(word) for word in fields[:4]]
            need(pid > 0 and ppid >= 0 and pgid >= 0 and rss >= 0 and pid not in rows,
                 'unique native process row')
            rows[pid] = {'ppid': ppid, 'pgid': pgid, 'rss_bytes': rss * 1024,
                         'birth': ' '.join(fields[4:])}
        return rows

    def active(self, rows, child):
        proc = child['process']
        known = self.known.setdefault(proc.pid, {})
        active = {pid: birth for pid, birth in known.items()
                  if pid in rows and rows[pid]['birth'] == birth}
        if child['usage'] is None and proc.pid in rows:
            active[proc.pid] = rows[proc.pid]['birth']
        allow_group = child['usage'] is None or any(rows[pid]['pgid'] == proc.pid for pid in active)
        while True:
            additions = {pid: row['birth'] for pid, row in rows.items()
                         if row['ppid'] in active or (allow_group and row['pgid'] == proc.pid)}
            fresh = any(pid not in active for pid in additions)
            active.update(additions)
            if not fresh:
                known.update(active)
                return active

    def sample(self):
        rows = self.table()
        retained = {}
        for child in self.children:
            active = self.active(rows, child)
            retained.update({pid: rows[pid] for pid in active})
            # Source roles are deliberately leaf processes. Any discovered
            # descendant invalidates this baseline and is cleaned up.
            need(all(pid == child['process'].pid for pid in active), 'unexpected owned descendant')
        own = raw_peak(resource.getrusage(resource.RUSAGE_SELF))
        live = sum(row['rss_bytes'] for row in retained.values())
        combined = own + self.child_peak_sum + live + self.observer_peak
        self.max_combined = max(self.max_combined, combined)
        self.samples.append({'elapsed_ns': time.perf_counter_ns() - self.began_ns,
            'coordinator_peak_bytes': own, 'direct_child_peak_sum_bytes': self.child_peak_sum,
            'observer_peak_bytes': self.observer_peak, 'owned_rows': {str(pid): row for pid, row in retained.items()},
            'combined_bytes': combined})
        need(combined <= LIMITS['aggregate_owned_bytes'], 'sampled/conservative aggregate512 memory')
        for child in self.children:
            if child['role'] == 'producer' and child['process'].pid in retained:
                need(retained[child['process'].pid]['rss_bytes'] < 524288000, 'producer native500 memory')

    def launch(self, role, argv, pass_fds, run):
        self.check()
        out = (run / (role + '-stdout.txt')).open('xb')
        err = (run / (role + '-stderr.txt')).open('xb')
        try:
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                pass_fds=tuple(pass_fds), close_fds=True, start_new_session=True,
                cwd=str(run), env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C',
                                  'PYTHONDONTWRITEBYTECODE': '1'})
        finally:
            out.close()
            err.close()
        child = {'role': role, 'process': proc, 'usage': None, 'observed_terminal_ns': None,
                 'kernel_peak_bytes': None, 'reaped': False}
        self.children.append(child)
        return child

    def reap(self, child, *, blocking=False):
        if child['usage'] is not None:
            return True
        pid, status, usage = os.wait4(child['process'].pid, 0 if blocking else os.WNOHANG)
        if not pid:
            return False
        child['process'].returncode = os.waitstatus_to_exitcode(status)
        child['usage'] = usage
        child['reaped'] = True
        child['kernel_peak_bytes'] = raw_peak(usage)
        self.child_peak_sum += child['kernel_peak_bytes']
        child['observed_terminal_ns'] = time.perf_counter_ns()
        if child['role'] == 'producer':
            need(child['kernel_peak_bytes'] < 524288000, 'producer kernel500 memory')
        self.check(success=False)
        return True

    def wait(self, child):
        while not self.reap(child):
            self.check(success=False)
            self.sample()
            # Twenty seconds may be followed only by failure cleanup. It
            # never resets or authorizes a late submission or new verifier.
            if child['role'] == 'verifier':
                self.check()
            time.sleep(.05)
        self.sample()
        self.check()
        need(child['process'].returncode == 0, 'complete child exit zero')
        return child['observed_terminal_ns']

    def cleanup(self):
        for child in self.children:
            if child['usage'] is None:
                try:
                    os.killpg(child['process'].pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    self.reap(child, blocking=True)
                except BaseException as error:
                    self.cleanup_errors.append({'type': type(error).__name__, 'message': str(error)})
        try:
            rows = self.table()
            for child in self.children:
                active = self.active(rows, child)
                for pid, birth in active.items():
                    if rows[pid]['birth'] == birth:
                        try:
                            os.kill(pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
            rows = self.table()
            self.leftovers = [pid for child in self.children for pid in self.active(rows, child)]
        except BaseException as error:
            self.cleanup_errors.append({'type': type(error).__name__, 'message': str(error)})
            self.leftovers = ['ownership_unconfirmed']


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


def validate_plan(plan, own_pin):
    fields = {'schema', 'invocation_id', 'output_directory', 'sources', 'inputs',
              'original_sources', 'runtime', 'admission', 'controls_admission', 'limits'}
    need(type(plan) is dict and set(plan) == fields and plan['schema'] == 'ROOT-Q-split-once-baseline-plan-v1',
         'exact previously reviewed baseline plan')
    identifier = plan['invocation_id']
    need(type(identifier) is str and 1 <= len(identifier) <= 128 and
         all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:' for c in identifier), 'invocation identifier')
    need(type(plan['limits']) is dict and set(plan['limits']) == set(LIMITS)
         and all(type(value) is int for value in plan['limits'].values()) and plan['limits'] == LIMITS,
         'unchanged literal limits')
    need(plan['runtime'] == RUNTIME and plan['original_sources'] == ORIGINAL_SOURCES, 'exact runtime/original7')
    need(type(plan['sources']) is dict and set(plan['sources']) == set(SOURCE_PINS) | {'coordinator'}, 'full Source roles')
    need(type(plan['inputs']) is dict and set(plan['inputs']) == set(RAW_INPUT_BINDINGS), 'whole original input set')
    for name, expected in SOURCE_PINS.items():
        record = plan['sources'][name]
        need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}
             and {key: record[key] for key in ('sha256', 'bytes')} == expected
             and type(record['bytes']) is int, 'exact Source role pin ' + name)
    for name, expected in RAW_INPUT_BINDINGS.items():
        record = plan['inputs'][name]
        need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}
             and {key: record[key] for key in ('sha256', 'bytes')} == expected
             and type(record['bytes']) is int, 'exact raw input pin ' + name)
    own = plan['sources']['coordinator']
    need(type(own) is dict and set(own) == {'path', 'sha256', 'bytes'}
         and {key: own[key] for key in ('sha256', 'bytes')} == own_pin
         and Path(own['path']) == Path(__file__).resolve(), 'original executing coordinator Source')
    need(Path(sys.executable).resolve() == Path(RUNTIME['path']).resolve()
         and pin_bytes(read_small(RUNTIME['path'], 1024 * 1024)) ==
             {key: RUNTIME[key] for key in ('sha256', 'bytes')}, 'exact native runtime bytes')
    source_bindings = {name: {key: value[key] for key in ('sha256', 'bytes')}
                       for name, value in plan['sources'].items()}
    controls = decode(read_small(plan['controls_admission']['path'], PLAN_MAX,
        {key: plan['controls_admission'][key] for key in ('sha256', 'bytes')}), PLAN_MAX)
    need(controls.get('schema') == 'ROOT-Q-split-full-model-controls-resource-admission-v1'
         and controls.get('accepted') is True and controls.get('source_bindings') == source_bindings
         and controls.get('binding') == BINDING and controls.get('limits') == LIMITS,
         'NEW exact owned full-model controls/resource admission, never old controls')
    admission = decode(read_small(plan['admission']['path'], PLAN_MAX,
        {key: plan['admission'][key] for key in ('sha256', 'bytes')}), PLAN_MAX)
    need(admission.get('schema') == 'ROOT-Q-split-baseline-execution-admission-v1'
         and all(admission.get(field) is True for field in ('all_required_source_reviews_passed',
             'new_owned_controls_accepted', 'first_unsupplied_baseline_once_authorized'))
         and admission.get('source_bindings') == source_bindings
         and admission.get('controls_admission') == plan['controls_admission']
         and admission.get('raw_input_bindings') == RAW_INPUT_BINDINGS and admission.get('binding') == BINDING,
         'prior exact Source review/controls/admission for this once baseline')


def verifier_response(body, authority, authority_pin, candidate, candidate_pin, owner):
    fields = {'schema', 'version', 'coordinator_invocation_id', 'authority_raw_sha256',
        'candidate_raw_sha256', 'authority_value_sha256', 'candidate_value_sha256',
        'binding', 'source_bindings', 'submission_index', 'submissions_checked',
        'status', 'independent_word_certificate', 'rejection', 'producer_origin_claim',
        'producer_termination_claim', 'ROOT_primary_accepted', 'ROOT_resource_accepted',
        'joint_began_ns', 'joint_deadline_ns'} | set(FALSE_SCOPES)
    need(set(body) == fields and body['version'] == 'Q-clean-original-target-word-verifier-Source-v3',
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


def main(argv, *, joint_began_ns):
    # REQUIRED earlier native clock from the separately pinned trusted cold
    # launcher, before this entire coordinator Source authentication/load/import.
    # No clock fallback/reset or direct CLI can make omitted setup free.
    began_ns = integer(joint_began_ns, 1)
    need(began_ns <= time.perf_counter_ns() < began_ns + 20000000000,
         'original earlier trusted launcher perf_counter_ns begin')
    owner = Owner(began_ns)
    need(len(argv) == 1 and sys.platform == 'darwin', 'one frozen plan on admitted native platform')
    signal.signal(signal.SIGTERM, lambda *_: setattr(owner, 'cancelled', True))
    signal.signal(signal.SIGINT, lambda *_: setattr(owner, 'cancelled', True))
    plan_raw = read_small(argv[0], PLAN_MAX)
    plan = decode(plan_raw, PLAN_MAX)
    own_raw = read_small(str(Path(__file__).resolve()), PLAN_MAX)
    validate_plan(plan, pin_bytes(own_raw))
    owner.check()
    run = Path(plan['output_directory'])
    need(run.is_absolute() and run == run.resolve() and not run.exists(), 'fresh exclusive once-only run namespace')
    run.mkdir(mode=0o700)
    error, certificate, candidate_pin, response_pin = None, None, None, None
    output_inventory = {'complete': False, 'files': [], 'bytes': 0}
    word_verified = False
    final_wire_timely = False
    try:
        launch = {'schema': 'Q-split-owned-launch-v1', 'version': VERSION,
            'plan': pin_bytes(plan_raw), 'source': pin_bytes(own_raw), 'invocation_id': plan['invocation_id'],
            'joint_began_ns': began_ns, 'joint_deadline_ns': owner.deadline_ns,
            'limits': LIMITS, 'status': 'once_original_unsupplied_baseline'}
        write_exclusive(run / 'launch.json', canonical(launch) + b'\n')
        snapshots = run / 'authenticated-snapshots'
        snapshots.mkdir(mode=0o700)
        # All original inputs and original7 provenance bytes are cold-read,
        # even when only the producer or prior admission uses their contents.
        for name, record in plan['inputs'].items():
            stream_snapshot(record, snapshots / ('input-' + name), owner)
        for name, record in plan['original_sources'].items():
            stream_snapshot(record, snapshots / ('original-' + name), owner)
        for name, record in plan['sources'].items():
            stream_snapshot(record, snapshots / ('source-' + name + '.py'), owner)
        declaration_raw = read_small(str(snapshots / 'input-declaration'), 2683, RAW_INPUT_BINDINGS['declaration'])
        declaration = decode(declaration_raw, 2683)
        need(digest(declaration) == DECLARATION_VALUE_SHA256, 'whole original declaration value')
        role_pins = {name: {key: plan['sources'][name][key] for key in ('sha256', 'bytes')}
                     for name in ('coordinator', 'producer', 'verifier', 'independent_checker', 'point_graph')}
        authority = {'schema': 'Q-clean-verifier-fixed-authority-v1',
            'coordinator_invocation_id': plan['invocation_id'], 'declaration': declaration,
            'binding': BINDING, 'raw_input_bindings': RAW_INPUT_BINDINGS,
            'source_bindings': role_pins, 'limits': LIMITS}
        authority_raw = canonical(authority)
        authority_pin = pin_bytes(authority_raw)
        write_exclusive(run / 'fixed-authority.json', authority_raw)
        base = run / 'producer-event-base'
        base.mkdir(mode=0o700)
        manifest = {'schema': 'Q-untrusted-producer-bootstrap-manifest-v1',
            'coordinator_invocation_id': plan['invocation_id'], 'authority_sha256': authority_pin['sha256'],
            'declaration': declaration, 'binding': BINDING, 'original_source_bindings': ORIGINAL_SOURCES,
            'source_bindings': {name: {key: plan['sources'][name][key] for key in ('sha256', 'bytes')}
                for name in ('bootstrap', 'codec', 'point_graph', 'producer')}, 'event_directory': str(base)}
        manifest_raw = canonical(manifest)
        manifest_pin = pin_bytes(manifest_raw)
        write_exclusive(run / 'producer-manifest.json', manifest_raw)
        channels = []
        try:
            for path in (run / 'producer-manifest.json', snapshots / 'input-preparation',
                snapshots / 'source-codec.py', snapshots / 'source-point_graph.py', snapshots / 'source-producer.py'):
                channels.append(regular_fd(str(path), os.O_RDONLY))
            channels.append(regular_fd(str(run / 'producer-response.jsonl'), os.O_WRONLY | os.O_CREAT | os.O_EXCL))
            args = [channels[0], manifest_pin['sha256'], manifest_pin['bytes'], *channels[1:], began_ns, owner.deadline_ns]
            child = owner.launch('producer', [RUNTIME['path'], '-I', '-B',
                str(snapshots / 'source-bootstrap.py'), *[str(value) for value in args]], channels, run)
        finally:
            for fd in channels:
                os.close(fd)
        owner.wait(child)
        producer_body, producer_response_pin = two_lines(str(run / 'producer-response.jsonl'),
            'Q-untrusted-producer-bootstrap-response-body-v1',
            'Q-untrusted-producer-bootstrap-response-completion-v1', owner)
        need(set(producer_body) == {'schema', 'coordinator_invocation_id', 'authority_sha256',
            'binding', 'source_bindings', 'result'} and producer_body['coordinator_invocation_id'] == plan['invocation_id']
            and producer_body['authority_sha256'] == authority_pin['sha256']
            and producer_body['binding'] == BINDING and producer_body['source_bindings'] == manifest['source_bindings'],
            'complete fixed producer context, no claimed authority')
        producer_result = producer_body['result']
        need(type(producer_result) is dict and producer_result.get('schema') == 'Q-full-original-model-untrusted-producer-return-v1',
             'full producer return data')
        candidate = producer_result.get('candidate')
        need(type(candidate) is dict, 'no candidate means UNKNOWN, never exhausted theorem')
        # Re-decode semantic candidate with NO floats and exact JSON rules.
        candidate_raw = canonical(candidate)
        need(len(candidate_raw) <= 2 * 1048576, 'whole candidate transport cap')
        candidate = decode(candidate_raw, 2 * 1048576)
        candidate_pin = pin_bytes(candidate_raw)
        write_exclusive(run / 'first-candidate.json', candidate_raw)
        channels = []
        try:
            for path in (run / 'fixed-authority.json', run / 'first-candidate.json', snapshots / 'source-independent_checker.py'):
                channels.append(regular_fd(str(path), os.O_RDONLY))
            channels.append(regular_fd(str(run / 'verifier-response.jsonl'), os.O_WRONLY | os.O_CREAT | os.O_EXCL))
            args = [channels[0], authority_pin['sha256'], authority_pin['bytes'],
                    channels[1], candidate_pin['sha256'], candidate_pin['bytes'],
                    channels[2], channels[3], began_ns, owner.deadline_ns]
            child = owner.launch('verifier', [RUNTIME['path'], '-I', '-B',
                str(snapshots / 'source-verifier.py'), *[str(value) for value in args]], channels, run)
        finally:
            for fd in channels:
                os.close(fd)
        owner.wait(child)
        body, response_pin = two_lines(str(run / 'verifier-response.jsonl'),
            'Q-clean-verifier-response-body-v1', 'Q-clean-verifier-response-completion-v1', owner)
        word_verified = verifier_response(body, authority, authority_pin, candidate, candidate_pin, owner)
        certificate = body['independent_word_certificate']
        owner.check()
    except BaseException as failure:
        error = {'type': type(failure).__name__, 'message': str(failure)[:2048]}
    finally:
        owner.cleanup()
        try:
            output_inventory = inventory(run, owner, success=word_verified and error is None)
        except BaseException as failure:
            if error is None:
                error = {'type': type(failure).__name__, 'message': str(failure)[:2048]}
        all_reaped = all(child['reaped'] for child in owner.children)
        peak = max(owner.max_combined, raw_peak(resource.getrusage(resource.RUSAGE_SELF)) +
                   owner.child_peak_sum + owner.observer_peak)
        before_receipt_ns = time.perf_counter_ns()
        pending = (word_verified and error is None and not owner.cancelled and not owner.cleanup_errors
            and not owner.leftovers and all_reaped and output_inventory['complete'] is True
            and peak + 8 * 1048576 <= LIMITS['aggregate_owned_bytes']
            and before_receipt_ns + 2000000000 < owner.deadline_ns)
        ledger_raw = canonical({'samples': owner.samples, 'known_births': owner.known,
            'scope': 'only pinned coordinator filtered owned rows; no hostile-OS or whole-host custody claim'}) + b'\n'
        ledger_compressed = gzip.compress(ledger_raw, mtime=0)
        ownership_ledger_pin = {'path': 'owned-ledger.json.gz', **pin_bytes(ledger_compressed)}
        write_exclusive(run / 'owned-ledger.json.gz', ledger_compressed)
        del ledger_compressed
        terminal = {'schema': 'Q-split-owned-coordinator-provisional-v1', 'version': VERSION,
            'invocation_id': plan['invocation_id'], 'binding': BINDING, 'limits': LIMITS,
            'status': 'WORD_VERIFIED_PENDING_CALLER' if pending else 'UNKNOWN',
            'mathematical_word_verified': word_verified, 'primary_pending_caller': pending,
            'ROOT_primary_accepted': False, 'ROOT_resource_accepted': False,
            'candidate': candidate_pin, 'verifier_response': response_pin,
            'independent_word_certificate': certificate, 'error': error,
            'joint_began_ns': began_ns, 'joint_deadline_ns': owner.deadline_ns,
            'before_receipt_ns': before_receipt_ns, 'conservative_peak_bytes': peak,
            'direct_children_peak_sum_bytes': owner.child_peak_sum, 'observer_peak_bytes': owner.observer_peak,
            'all_direct_children_terminal_and_reaped': all_reaped, 'leftovers': owner.leftovers,
            'cleanup_errors': owner.cleanup_errors, 'cancelled': owner.cancelled,
            'children': [{key: child[key] for key in ('role', 'observed_terminal_ns', 'kernel_peak_bytes', 'reaped')}
                | {'returncode': child['process'].returncode} for child in owner.children],
            'output_inventory': output_inventory, 'ownership_ledger': ownership_ledger_pin,
            'actual_selected_accepted': False,
            'point_snapshot_accepted': False, 'full24_accepted': False, 'full_trajectory_accepted': False,
            'native_accepted': False, 'RL_accepted': False, 'induction_accepted': False, 'full_PA_accepted': False,
            'no_OS_hard_memory_limit_claim': True, 'caller_gate_required': True}
        terminal_raw = canonical(terminal) + b'\n'
        need(len(terminal_raw) <= 8 * 1048576, 'complete terminal output bound')
        write_exclusive(run / 'coordinator-provisional.json', terminal_raw)
        post_ns = time.perf_counter_ns()
        post_peak = max(peak, raw_peak(resource.getrusage(resource.RUSAGE_SELF)) + owner.child_peak_sum + owner.observer_peak)
        final_wire_timely = pending and post_ns < owner.deadline_ns and post_peak <= LIMITS['aggregate_owned_bytes']
        post = {'schema': 'Q-split-owned-coordinator-post-write-v1', 'primary_pending_caller': final_wire_timely,
            'provisional': pin_bytes(terminal_raw), 'ownership_ledger': ownership_ledger_pin,
            'observed_post_write_ns': post_ns,
            'conservative_peak_bytes': post_peak, 'joint_deadline_ns': owner.deadline_ns,
            'owned_deadline_ns': owner.owned_ns, 'caller_gate_required': True, 'ROOT_primary_accepted': False}
        post_raw = canonical(post) + b'\n'
        write_exclusive(run / 'coordinator-post-write.json', post_raw)
        # Root must observe this complete final file AND CLI exit zero under
        # joint20/owned60/aggregate512 and genuine caller90+finish1. A late
        # post file/print cannot be promoted using the earlier pending flag.
        final_ns = time.perf_counter_ns()
        final_wire_timely = final_wire_timely and final_ns < owner.deadline_ns
        print(json.dumps({'schema': 'Q-split-owned-final-tool-observation-v1',
            'primary_pending_caller': final_wire_timely, 'post_write': pin_bytes(post_raw),
            'joint_began_ns': began_ns, 'joint_deadline_ns': owner.deadline_ns,
            'before_final_print_ns': final_ns, 'ROOT_primary_accepted': False}), flush=True)
    return 0 if final_wire_timely else 2


if __name__ == '__main__':
    try:
        raise ValueError('direct coordinator CLI prohibited; exact trusted cold launcher is required')
    except Exception as error:
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        raise SystemExit(2)
