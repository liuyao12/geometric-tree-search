"""Prospective sole ROOT entry V3 with process-local clock domains; no activation is bundled.

The owner is ROOT's fresh session/group leader. Worker and PS inherit that
group. ROOT retains its exact direct handle until terminal reaping. A latch,
cancellation or emergency termination is UNKNOWN and never qualifies a run.
"""
import time
ENTRY = time.perf_counter()
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import stat
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MAX_METADATA = 1048576
FRAME = struct.Struct('!8sBBHQQddd')
cancelled_signum = 0
EXACT_OWNER_PIN = {'path': '.gcts-active/process-local-clock-successor-source-20261012/curriculum_compact_owner_v5.py', 'sha256': '64a66b3f5feba295e1e4d1964873153d4f9400b4193058f8db4adc026b2ada7e', 'bytes': 27912}
EXACT_OWNER_MANIFEST_PIN = {'path': '.gcts-active/process-local-clock-successor-source-20261012/source-plan-owner-v5.json', 'sha256': '1537702e25cccb9697d9404fc09c5a53dcf354de0415c54f77ea8f9b942c7422', 'bytes': 3071}
EXACT_ADAPTER_PIN = dict(path='.gcts-active/curriculum-compact-root-binding-source-20261012/root_accounting_adapter_v4.py',
                        sha256='e9620ffec78f2b014107b2907456aab2dc933084ecee0f5f96e62df11d6a631d', bytes=21195)
EXACT_TRANSPORT_PIN = dict(path='.gcts-active/curriculum-compact-wrapper-source-20261012/compact_static_transport_v1.py',
                          sha256='65a0b598966ae4dffdda1b770eb2d4d5b64af1bcaf6aead4281a224a4123def3', bytes=13756)
EXACT_WORKER_PIN = dict(path='.gcts-active/curriculum-compact-wrapper-source-20261012/curriculum_compact_worker_v1.py',
                       sha256='77a15d292833f82ee759b522ed8a615da4bad7d43f48e8ccc218844cac9c1dd3', bytes=13759)

EXACT_CLOCK_CONTRACT_PIN = {'path': '.gcts-active/equality-clock-interface-source-review-20261012/future-clock-contract-v1.json', 'sha256': '61238d81491eea7c9cdd8501dff9a0a78d9666302a545b38f8dd2eadf2ad323b', 'bytes': 6153}


def cancellation_flag(signum, _frame):
    global cancelled_signum
    cancelled_signum = signum


def install_flags():
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGALRM):
        signal.signal(sig, cancellation_flag)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def resolve(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def pin(path, declared=None):
    path = Path(path)
    h = hashlib.sha256()
    n = 0
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode), 'closed regular immutable file with exact declared path spelling')
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
            n += len(block)
        after = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    need(identity(before) == identity(after) == identity(path.stat()) and n == after.st_size,
         'immutable closed source/metadata identity')
    if declared is None:
        try:
            declared = str(path.relative_to(ROOT))
        except ValueError:
            declared = str(path)
    return dict(path=declared, sha256=h.hexdigest(), bytes=n)


def verify(record):
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}, 'exact three-field metadata pin')
    need(type(record['path']) is str and bool(record['path'])
         and type(record['bytes']) is int and record['bytes'] >= 0
         and type(record['sha256']) is str and len(record['sha256']) == 64
         and all(char in '0123456789abcdef' for char in record['sha256']), 'strict pin spelling/count/digest')
    exact = {key: record[key] for key in ('path', 'sha256', 'bytes')}
    path = resolve(record['path'])
    need(pin(path, record['path']) == exact, 'exact separately frozen bytes')
    return path


def unique_fields(pairs):
    value = {}
    for key, item in pairs:
        need(key not in value, 'duplicate metadata fields')
        value[key] = item
    return value


def read_small(path):
    need(Path(path).stat().st_size <= MAX_METADATA, 'bounded closed metadata before streamed hash')
    expected = pin(path)
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_METADATA + 1)
    need(len(raw) <= MAX_METADATA, 'one-MiB separately frozen metadata bound')
    need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256']
         and pin(path) == expected, 'decoded metadata bytes equal exact closed pin')
    return json.loads(raw, object_pairs_hook=unique_fields,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite metadata')))


def write_new(path, value):
    # Serialize before writing; no partial JSON is treated as a terminal frame.
    raw = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode('utf-8')
    need(len(raw) <= MAX_METADATA, 'bounded closed ROOT receipt')
    with Path(path).open('xb') as stream:
        stream.write(raw)


def raw_usage(usage):
    return {key: getattr(usage, key) for key in dir(usage) if key.startswith('ru_')}


def integer(value, label, positive=False):
    need(type(value) is int and value >= (1 if positive else 0), label)
    return value


def clock(value, label):
    need(type(value) in (int, float) and math.isfinite(value) and value >= 0, label)
    return value


def same_json(actual, expected, label):
    # Preserve JSON types: True must not compare equal to integer one.
    encode = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    need(encode(actual) == encode(expected), label)


def validate_raw_usage(raw, label):
    times = {'ru_utime', 'ru_stime'}
    integers = {'ru_maxrss', 'ru_ixrss', 'ru_idrss', 'ru_isrss', 'ru_minflt', 'ru_majflt',
                'ru_nswap', 'ru_inblock', 'ru_oublock', 'ru_msgsnd', 'ru_msgrcv',
                'ru_nsignals', 'ru_nvcsw', 'ru_nivcsw'}
    need(type(raw) is dict and set(raw) == times | integers, label + ' complete pinned Python3.9 raw usage fields')
    for name in times:
        need(type(raw[name]) is float, label + ' floating CPU time')
        clock(raw[name], label + ' finite nonnegative CPU time')
    for name in integers:
        integer(raw[name], label + ' raw integer usage', name == 'ru_maxrss')
    return raw


def read_frame_exact(path, role, pid):
    need(not Path(path).is_symlink(), 'owned frame has no path alias')
    exact = pin(path)
    need(exact['bytes'] == FRAME.size == 52, 'exact raw finite SELF frame length')
    with Path(path).open('rb') as stream:
        raw = stream.read(53)
    need(len(raw) == 52 and hashlib.sha256(raw).hexdigest() == exact['sha256'],
         'decoded raw buffer equals closed pinned frame bytes')
    magic, tag, code, reserved, actual_pid, rss, elapsed, began, closed = FRAME.unpack(raw)
    need(magic == b'GCTSCMP1' and tag == role and code == 0 and reserved == 0
         and actual_pid == integer(pid, 'registered frame PID', True) and rss > 0,
         'successful exact raw role/PID/code/reserved/peak')
    need(all(math.isfinite(value) and value >= 0 for value in (elapsed, began, closed))
         and closed >= began and elapsed == closed - began, 'finite exact raw SELF clocks')
    return dict(role=tag, pid=actual_pid, exit_code=code, SELF_ru_maxrss_raw=rss,
                seconds_after_all_artifact_close_before_fixed_postlude=elapsed,
                entry_monotone_clock=began, last_closed_monotone_clock=closed,
                remaining_postlude='Fixed52-byte pack/write then os._exit; separately ROOT-reviewed reserve required',
                terminal_frame=exact)


def closed_jsonl(artifact, expected_path, maximum_records):
    need(type(artifact) is dict and set(artifact) == {'pin', 'records'}, 'closed exact JSONL artifact')
    count = integer(artifact['records'], 'JSONL complete record count')
    need(not Path(expected_path).is_symlink(), 'owned JSONL has no path alias')
    need(count <= maximum_records, 'frozen complete JSONL record envelope')
    need(Path(expected_path).stat().st_size <= count * MAX_METADATA,
         'bounded total JSONL before streamed hashing')
    expected = pin(expected_path)
    same_json(artifact['pin'], expected, 'JSONL pin equals exact owned output path and bytes')
    need(expected['bytes'] <= count * MAX_METADATA, 'bounded total JSONL bytes from complete census')
    h = hashlib.sha256(); total = 0
    with Path(expected_path).open('rb') as stream:
        for index in range(count):
            line = stream.readline(MAX_METADATA + 1)
            need(0 < len(line) <= MAX_METADATA and line.endswith(b'\n'), 'bounded complete JSONL line')
            h.update(line); total += len(line)
            value = json.loads(line, object_pairs_hook=unique_fields,
                               parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSONL')))
            need(type(value) is dict and type(value.get('index')) is int and value['index'] == index,
                 'complete chronological JSONL index')
            value.pop('index')
            yield value
        need(stream.read(1) == b'', 'no omitted trailing JSONL records or bytes')
    need(total == expected['bytes'] and h.hexdigest() == expected['sha256']
         and pin(expected_path) == expected, 'closed replay stream equals initial immutable pin')


def raw_ps_rows(receipt, plan, index, owner_pid, worker_pid, root_pid, birth):
    contract = plan['compact_transport_contract']
    expected_fields = {'observer_id','owner_pid','observer_pid','command','binary','clock_before_spawn',
        'clock_after_spawn','clock_after_stream_close_and_terminal_reap','seconds_from_owner_entry','exit_code',
        'reaped','terminal_wait4_raw','failure','cleanup_failure','requires_outer_containment','inherited_owner_group',
        'unexpected_descendant_rows','unexpected_group_rows','raw_usage_scope','stdout','stderr','clock_after_parse_and_stream_hash'}
    need(set(receipt) == expected_fields, 'exact complete successful raw observer record')
    need(type(receipt['observer_id']) is int and receipt['observer_id'] == index
         and type(receipt['owner_pid']) is int and receipt['owner_pid'] == owner_pid,
         'registered sequential direct observer owner/ID')
    observer_pid = integer(receipt['observer_pid'], 'raw direct observer PID', True)
    need(observer_pid not in (root_pid, owner_pid, worker_pid), 'distinct direct observer role')
    need(receipt['reaped'] is True and type(receipt['exit_code']) is int and receipt['exit_code'] == 0
         and receipt['failure'] is None and receipt['cleanup_failure'] is None
         and receipt['requires_outer_containment'] is False
         and receipt['unexpected_descendant_rows'] == [] and receipt['unexpected_group_rows'] == [],
         'successful observer without cancellation/cleanup/descendant ambiguity')
    same_json(receipt['binary'], plan['runtime']['observer'], 'same frozen raw PS binary pin')
    command = [str(verify(plan['runtime']['observer'])), '-axo', 'pid=,ppid=,pgid=,lstart=,rss=']
    same_json(receipt['command'], command, 'exact raw PS command/field grammar')
    need(receipt['raw_usage_scope'] == 'Direct observer wait4; expected leaf, verified ROOT platform evidence required',
         'exact leaf observer provenance scope')
    validate_raw_usage(receipt['terminal_wait4_raw'], 'observer')
    directory = Path(plan['outputs']['lifetime']).parent
    stdout = directory / ('observer-' + str(index) + '-stdout.txt')
    stderr = directory / ('observer-' + str(index) + '-stderr.txt')
    need(not stdout.is_symlink() and not stderr.is_symlink(), 'owned raw PS streams have no path alias')
    maximum = integer(contract['observer_stream_maximum_bytes'], 'frozen raw PS byte bound', True)
    need(stdout.stat().st_size <= maximum and stderr.stat().st_size == 0,
         'raw PS stream size bound before hashes/parsing')
    same_json(receipt['stdout'], pin(stdout), 'exact closed raw PS stdout')
    same_json(receipt['stderr'], pin(stderr), 'exact closed raw PS stderr')
    need(receipt['stderr']['bytes'] == 0, 'successful PS stderr is empty')
    need(receipt['stdout']['bytes'] <= maximum, 'bounded closed raw PS stdout')
    rows = {}; digest = hashlib.sha256(); total = 0
    with stdout.open('rb') as stream:
        while True:
            line = stream.readline(MAX_METADATA + 1)
            if not line: break
            need(len(line) <= MAX_METADATA and line.endswith(b'\n'), 'bounded raw PS line')
            digest.update(line); total += len(line)
            parts = line.decode('utf-8', errors='strict').split()
            need(len(parts) >= 5, 'raw PS PID/PPID/PGID/birth/RSS fields')
            pid, ppid, pgid = map(int, parts[:3]); rss = int(parts[-1]); identity = ' '.join(parts[3:-1])
            need(min(pid, ppid, pgid, rss) >= 0 and bool(identity) and pid not in rows,
                 'unique nonnegative complete raw PS row')
            rows[pid] = dict(pid=pid, ppid=ppid, pgid=pgid, birth=identity, RSS_ps_raw=rss)
    need(total == receipt['stdout']['bytes'] and digest.hexdigest() == receipt['stdout']['sha256']
         and pin(stdout) == receipt['stdout'], 'parsed PS bytes exactly match closed pin')
    need(owner_pid in rows and root_pid in rows and observer_pid in rows, 'raw PS contains its live owner/ROOT/self')
    need(rows[owner_pid]['ppid'] == root_pid and rows[owner_pid]['pgid'] == owner_pid
         and rows[observer_pid]['ppid'] == owner_pid and rows[observer_pid]['pgid'] == owner_pid,
         'raw direct ownership and fresh owner-led group')
    for pid in (owner_pid, root_pid, worker_pid):
        if pid in rows:
            if pid in birth: need(birth[pid] == rows[pid]['birth'], 'stable raw live role birth identity')
            else: birth[pid] = rows[pid]['birth']
    active = {worker_pid, observer_pid}
    while True:
        following = active | {pid for pid, row in rows.items() if row['ppid'] in active}
        if following == active: break
        active = following
    need(active == {worker_pid, observer_pid}, 'independently reconstructed worker/observer have no descendants')
    need(all(row['pid'] in (owner_pid, worker_pid, observer_pid) for row in rows.values() if row['pgid'] == owner_pid),
         'no extra known member of retained fresh owner group')
    workers = [rows[worker_pid]] if worker_pid in rows else []
    if workers:
        need(workers[0]['ppid'] == owner_pid and workers[0]['pgid'] == owner_pid,
             'raw worker inherits direct owner group')
    return rows[owner_pid], workers


def local_child_lifetime(receipt, owner_frame, worker_frame, owner_pid):
    """Authenticate one emitter's local chain and durations, never align origins."""
    same_json(dict(clock_emitter_pid=receipt['clock_emitter_pid'],
                   clock_function=receipt['clock_function'],clock_origin_scope=receipt['clock_origin_scope']),
              dict(clock_emitter_pid=owner_pid,clock_function='time.perf_counter',
                   clock_origin_scope='process_local_no_cross_process_absolute_comparison'),
              'exact authenticated owner clock emitter and process-local scope')
    names=('owner_entry_clock','worker_creation_clock','worker_terminal_reap_clock','worker_streams_closed_clock',
           'child_seconds_including_startup_imports_all_serialization_exit_reap',
           'child_creation_through_reap_and_stream_close_seconds')
    for name in names:
        need(type(receipt[name]) is float, 'actual emitter-local floating clock/duration')
        clock(receipt[name], 'finite nonnegative owner clock/duration: '+name)
    started,created,reaped,closed,seconds,full=(receipt[name] for name in names)
    same_json(started,owner_frame['entry_monotone_clock'],'raw owner entry equals receipt local entry')
    need(started<=created<=reaped<=closed<=owner_frame['last_closed_monotone_clock']
         and seconds==reaped-created and full==closed-created,
         'same-owner raw creation/reap/stream-close chain and exact reconstructed durations')
    need(worker_frame['seconds_after_all_artifact_close_before_fixed_postlude']<=seconds<=170
         and seconds<=full<=owner_frame['seconds_after_all_artifact_close_before_fixed_postlude']<=175,
         'per-process durations nest inside unchanged child/owner caps')
    return seconds,full


def replay_closed_accounting(freeze, freeze_pin, plan_path, plan, owner_pid, root_pid, began, terminal):
    """Reconstruct raw PS/frames and adapter inputs; never finalize resources."""
    contract = plan['compact_transport_contract']; outputs = plan['outputs']
    need(not Path(contract['containment_output']).exists(), 'no closed containment publication')
    adapter = load(EXACT_ADAPTER_PIN, 'ROOT_compact_replay_adapter_v4')
    owner_frame = read_frame_exact(freeze['entry_outputs']['owner_stdout'], 2, owner_pid)
    adapter.frame(owner_frame, 2, owner_pid)
    owner_observed_seconds=clock(terminal,'ROOT owner stream close')-clock(began,'ROOT owner creation')
    need(owner_frame['seconds_after_all_artifact_close_before_fixed_postlude']<=owner_observed_seconds<=175,
         'authenticated owner duration inside same-ROOT observed complete direct lifetime')
    owner_receipt_pin = pin(outputs['lifetime'])
    receipt = read_small(outputs['lifetime'])
    receipt_fields = {'schema','status','selector','plan','owner','worker','activation','source_manifest',
        'platform_evidence','accounting_adapter','inherited_ROOT_owner_group','containment_output','child_pid',
        'child_exit','child_reaped','worker_terminal_wait4_raw','worker_closed_SELF','raw_wait4_scope',
        'child_seconds_including_startup_imports_all_serialization_exit_reap','observer_detail','sample_detail',
        'observer_count','SELF_before_final_receipt_serialization_raw','provisional_platform_accounting','full_audit',
        'compact_status','semantic_static_candidate','static_context_pool_accepted','full_resource_accepted',
        'all_five_qualification','failure','cancellation_signum','cancellation_requested','cancellation_semantics',
        'owner_seconds_before_lifetime_receipt_write','maximum_whole_seconds','maximum_supervisor_seconds',
        'maximum_child_seconds','maximum_peak_bytes','OS_hard_cap_claim','remaining_scope','native_queries',
        'searches_run_by_owner','training_runs','clock_emitter_pid','clock_function','clock_origin_scope',
        'owner_entry_clock','worker_creation_clock','worker_terminal_reap_clock','worker_streams_closed_clock',
        'child_creation_through_reap_and_stream_close_seconds'}
    need(type(receipt) is dict and set(receipt) == receipt_fields, 'exact V5 closed owner receipt v2 grammar')
    fixed = dict(schema='compact-static-owner-pending-ROOT-lifetime-v2',
        status='completed_compact_semantic_candidate_pending_full_ROOT_resources',selector=freeze['selector'],
        plan=freeze['plan_pin'],owner=EXACT_OWNER_PIN,worker=EXACT_WORKER_PIN,
        activation=freeze['activation_pin'],source_manifest=EXACT_OWNER_MANIFEST_PIN,
        platform_evidence=freeze['platform_evidence_pin'],accounting_adapter=EXACT_ADAPTER_PIN,
        containment_output=contract['containment_output'],child_exit=0,child_reaped=True,
        raw_wait4_scope='Worker expected leaf; no subtraction from rolled nested peaks',
        semantic_static_candidate=True,static_context_pool_accepted=False,full_resource_accepted=False,
        all_five_qualification=False,failure=None,cancellation_signum=0,cancellation_requested=False,
        cancellation_semantics='Non-raising INT/TERM/ALRM flags; checked only after spawn registration/terminal wait4 bookkeeping and at safe loop boundaries',
        maximum_whole_seconds=180,maximum_supervisor_seconds=175,maximum_child_seconds=170,
        maximum_peak_bytes=536870912,OS_hard_cap_claim=False,native_queries=0,searches_run_by_owner=0,training_runs=0,
        remaining_scope='After this closed receipt: raw SELF snapshot, fixed52byte terminal frame, os._exit. ROOT separately reviews preserved reserve and full180second launcher/dispatcher accounting.')
    same_json({key:receipt[key] for key in fixed}, fixed, 'exact owner source/plan/activation/pending scope and constants')
    worker_pid = integer(receipt['child_pid'], 'retained owner-registered direct worker PID', True)
    need(worker_pid not in (owner_pid, root_pid), 'three distinct ROOT/owner/worker roles')
    group = dict(owner_pid=owner_pid, owner_pgid=owner_pid, owner_sid=owner_pid, ROOT_parent_pid=root_pid)
    same_json(receipt['inherited_ROOT_owner_group'], group, 'exact fresh owner group and actual ROOT parent PID')
    worker_frame = read_frame_exact(outputs['stdout'], 1, worker_pid)
    same_json(receipt['worker_closed_SELF'], worker_frame, 'raw worker frame independently reconstructed')
    adapter.frame(worker_frame, 1, worker_pid)
    worker_seconds,worker_full_close_seconds=local_child_lifetime(receipt,owner_frame,worker_frame,owner_pid)
    count = integer(receipt['observer_count'], 'owner complete observer census')
    maximum = integer(contract['maximum_observers'], 'frozen observer maximum', True)
    need(count <= maximum and receipt['observer_detail']['records'] == count
         and receipt['sample_detail']['records'] == count, 'complete equal observer/sample census')
    accounting = adapter.AccountingAdapter(EXACT_ADAPTER_PIN, freeze['platform_evidence_pin'], owner_pid)
    observers = closed_jsonl(receipt['observer_detail'], outputs['observers'], maximum)
    samples = closed_jsonl(receipt['sample_detail'], outputs['samples'], maximum)
    birth = {}; maximum_observer_seconds = 0
    for index in range(count):
        observer = next(observers); sample = next(samples)
        same_json(observer['inherited_owner_group'], group, 'raw observer fresh ROOT group identity')
        own, workers = raw_ps_rows(observer, plan, index, owner_pid, worker_pid, root_pid, birth)
        pre = clock(observer['clock_before_spawn'], 'raw observer pre-spawn')
        post = clock(observer['clock_after_parse_and_stream_hash'], 'raw observer closed/parsed')
        need(receipt['worker_creation_clock'] <= pre <= post <= receipt['worker_terminal_reap_clock']
             and clock(observer['seconds_from_owner_entry'], 'observer owner offset')
             == observer['clock_after_stream_close_and_terminal_reap'] - owner_frame['entry_monotone_clock'],
             'raw observer clock belongs to exact owner entry')
        maximum_observer_seconds = max(maximum_observer_seconds, post - pre)
        accounting.add_observer(observer)
        sample_fields = {'clock','owner_SELF_row','worker_rows','inherited_ROOT_owner_group','observer_id',
                         'observer_detail_append_close_clock','scope','direct_worker_PID'}
        need(type(sample) is dict and set(sample) == sample_fields, 'exact raw sample grammar')
        expected = dict(owner_SELF_row=own, worker_rows=workers, inherited_ROOT_owner_group=group,
                        observer_id=index, direct_worker_PID=worker_pid,
                        scope='Exact owned worker/SELF ps rows; separate direct observer terminal usage')
        same_json({key:sample[key] for key in expected}, expected, 'sample fully derived from exact raw PS rows')
        need(receipt['worker_creation_clock'] <= clock(sample['clock'], 'raw sample clock') <= receipt['worker_terminal_reap_clock'],
             'sample precedes owner close')
        accounting.add_sample(sample)
        need(not accounting.rejects_current_caps(), 'same frozen partial metadata cap never rejected')
    marker = object()
    need(next(observers, marker) is marker and next(samples, marker) is marker, 'both full JSONL streams exhausted and hashed')
    raw_worker = validate_raw_usage(receipt['worker_terminal_wait4_raw'], 'direct worker')
    accounting.add_leaf_worker(raw_worker, worker_frame, worker_seconds, expected_pid=worker_pid)
    accounting.add_SELF_before_receipt(validate_raw_usage(receipt['SELF_before_final_receipt_serialization_raw'], 'owner SELF'))
    regenerated = accounting.finish_provisional()
    adapter.validate_provisional(regenerated)
    same_json(regenerated, receipt['provisional_platform_accounting'], 'exact independently replayed provisional ledger')
    before_receipt = clock(receipt['owner_seconds_before_lifetime_receipt_write'], 'owner pre-receipt scope')
    need(before_receipt <= 175 and before_receipt <= owner_frame['seconds_after_all_artifact_close_before_fixed_postlude'],
         'complete owner pre-close scope inside its final raw frame')
    same_json(receipt['full_audit'], pin(outputs['result']), 'unchanged full closed scientific audit bytes')
    same_json(receipt['compact_status'], pin(outputs['compact']), 'exact closed compact transport')
    sys.path.insert(0, str(resolve(freeze['transport_directory'])))
    from compact_static_transport_v1 import validate_compact
    compact = validate_compact(plan, plan_path, Path(plan['worker_path']), Path(plan['activation_path']))
    need(pin(outputs['lifetime']) == owner_receipt_pin and pin(resolve(freeze['plan_pin']['path'])) == freeze['plan_pin'],
         'owner receipt and frozen plan remain exact after replay')
    verify(freeze['activation_pin']); verify(freeze['entry_source_manifest_pin']); verify(EXACT_OWNER_MANIFEST_PIN)
    return dict(owner_frame=owner_frame, owner_receipt=receipt, owner_receipt_pin=owner_receipt_pin,
                regenerated_provisional=regenerated, worker_frame=worker_frame,
                compact=compact, replay=dict(schema='ROOT-independent-closed-accounting-replay-v3',
                    status='replayed_closed_raw_records_pending_external_terminal_GATE',
                    root_pid=root_pid, owner_pid=owner_pid, worker_pid=worker_pid, group=group,
                    freeze=freeze_pin, plan=freeze['plan_pin'], activation=freeze['activation_pin'],
                    owner_receipt=owner_receipt_pin, owner_raw_frame=owner_frame['terminal_frame'],
                    worker_raw_frame=worker_frame['terminal_frame'], observer_detail=receipt['observer_detail'],
                    sample_detail=receipt['sample_detail'], raw_PS_pairs=count, full_JSONL_records=2*count,
                    maximum_observer_complete_seconds=maximum_observer_seconds,
                    clock_domains=dict(ROOT_emitter_pid=root_pid,owner_emitter_pid=owner_pid,worker_emitter_pid=worker_pid,
                        function='time.perf_counter',absolute_origins='process_local_untrusted_across_processes'),
                    clock_durations=dict(worker_create_through_reap_seconds=worker_seconds,
                        worker_create_through_stream_close_seconds=worker_full_close_seconds,
                        owner_create_through_stream_close_seconds=owner_observed_seconds),
                    raw_PS_rows_and_role_birth_rederived=True, provisional_exactly_regenerated=True,
                    resource_accepted=False, all_five_qualification=False))


def load(record, name):
    path = verify(record)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def preflight(freeze_path):
    freeze = read_small(freeze_path)
    need(freeze['schema'] == 'ROOT-prospective-compact-static-entry-activation-v3'
         and freeze['authorized'] is True and freeze['ROOT_sole_actual_owner'] is True,
         'separate exact ROOT activation after source review; none is supplied')
    same_json(freeze['limits'], dict(whole_seconds=180, supervisor_seconds=175,
                                   child_seconds=170, peak_bytes=536870912), 'unchanged exact typed full limits')
    need(freeze['selector'] in ('donor-repeated-guard','donor-repeated-equality','heldout-mixed-guard-equality'),
         'only still-unexecuted selectors; both actual UNKNOWN donor attempts remain excluded')
    need(freeze['runtime']['platform'] == sys.platform == 'darwin', 'pinned Darwin topology only')
    need(Path(freeze['runtime']['executable']).resolve() == Path(sys.executable).resolve(),
         'same exact interpreter')
    verify(freeze['runtime']['binary'])
    verify(freeze['runtime']['resource_extension'])
    verify(freeze['runtime']['posixsubprocess_extension'])
    verify(freeze['runtime']['observer'])
    for record in freeze['pins']:
        verify(record)
    need(verify(freeze['entry_pin']).resolve() == Path(__file__).resolve(), 'same outer entry source')
    same_json(freeze['owner_pin'], EXACT_OWNER_PIN, 'exact process-local clock owner V5')
    same_json(freeze['adapter_pin'], EXACT_ADAPTER_PIN, 'exact immutable raw-frame-authenticating adapter V4')
    same_json(freeze['owner_source_manifest_pin'], EXACT_OWNER_MANIFEST_PIN, 'exact process-local owner V5 source freeze')
    verify(EXACT_OWNER_PIN); verify(EXACT_ADAPTER_PIN); verify(EXACT_OWNER_MANIFEST_PIN)
    entry_manifest_path = verify(freeze['entry_source_manifest_pin'])
    need(entry_manifest_path == HERE/'source-plan-root-entry-v3.json', 'exact separately frozen outer source manifest namespace')
    entry_manifest = read_small(entry_manifest_path)
    same_json(entry_manifest['entry_pin'], freeze['entry_pin'], 'source manifest pins this outer source')
    same_json(entry_manifest['owner_pin'], EXACT_OWNER_PIN, 'outer source manifest exact owner')
    same_json(entry_manifest['adapter_pin'], EXACT_ADAPTER_PIN, 'outer source manifest exact adapter')
    plan_path = verify(freeze['plan_pin'])
    plan = read_small(plan_path)
    need(plan['selector'] == freeze['selector'], 'same frozen future selector')
    need(plan['schema'] == 'frozen-curriculum-independent-compact-static-plan-v1'
         and plan['status'] == 'frozen_actual_inputs_pending_ROOT_activation'
         and plan['stage'] == 'static' and plan['actual_execution_authorized'] is False
         and plan['ROOT_sole_actual_owner'] is True, 'same original frozen compact static scope')
    same_json(plan['limits'], freeze['limits'], 'same exact frozen actual-plan limits')
    contract = plan['compact_transport_contract']
    same_json(contract['process_local_clock_contract_pin'],EXACT_CLOCK_CONTRACT_PIN,'exact process-local clock policy')
    verify(EXACT_CLOCK_CONTRACT_PIN)
    need(contract['owner_pin'] == freeze['owner_pin']
         and contract['accounting_adapter_pin'] == freeze['adapter_pin'], 'exact V3/adapter binding')
    same_json(contract['worker_pin'], EXACT_WORKER_PIN, 'unchanged original compact worker')
    same_json(contract['transport_pin'], EXACT_TRANSPORT_PIN, 'unchanged original compact transport')
    same_json(contract['wrapper_source_manifest_pin'], EXACT_OWNER_MANIFEST_PIN, 'owner scientific/source manifest separation')
    same_json(contract['platform_evidence_pin'], freeze['platform_evidence_pin'], 'same exact verified platform record')
    for key in ('compact_maximum_bytes','observer_stream_maximum_bytes','maximum_observers'):
        integer(contract[key], 'frozen metadata transport envelope', True)
        need(contract[key] <= 536870912, 'unchanged whole memory cap bounds metadata')
    need(contract['compact_maximum_bytes'] <= MAX_METADATA and contract['observer_seconds'] == 1,
         'existing one-MiB ROOT compact bound and unchanged one-second observer timeout')
    platform = read_small(verify(freeze['platform_evidence_pin']))
    need(platform['status'] == 'ROOT_verified_platform_accounting_evidence'
         and all(platform[key] is True for key in ('units_verified','wait4_descendant_scope_verified',
             'leaf_worker_and_observer_scope_verified','closed_SELF_postlude_scope_reviewed')),
         'separately ROOT-reviewed platform/accounting scope')
    same_json(platform['adapter_pin'], EXACT_ADAPTER_PIN, 'same platform-authorized adapter source')
    activation_path = Path(plan['activation_path'])
    same_json(pin(activation_path), freeze['activation_pin'], 'same original worker/owner activation bytes')
    activation = read_small(verify(freeze['activation_pin']))
    need(activation['schema'] == 'ROOT-independent-frozen-curriculum-compact-static-activation-v1'
         and activation['authorized'] is True and activation['selector'] == freeze['selector'],
         'original exact ROOT worker/owner activation')
    same_json(activation['plan'], freeze['plan_pin'], 'activation pins the entire actual plan')
    need(contract['fresh_ROOT_owned_owner_group_required'] is True,
         'owner is the newly created retained group leader')
    containment = Path(contract['containment_output'])
    need(containment.is_absolute() and containment.parent == Path(plan['outputs']['lifetime']).parent
         and str(containment) not in plan['outputs'].values(), 'distinct exact closed containment latch')
    transport = verify(EXACT_TRANSPORT_PIN)
    need(verify(EXACT_WORKER_PIN) == Path(plan['worker_path']), 'exact original worker source path')
    need(transport.parent == resolve(freeze['transport_directory']).resolve(), 'exact original transport import directory')
    need('compact_static_transport_v1' not in sys.modules, 'no previously loaded transport cache')
    need('sitecustomize' not in sys.modules and 'usercustomize' not in sys.modules,
         'no unreviewed runtime customization module')
    need(set(plan['outputs']) == {'result','compact','lifetime','observers','samples','stdout','stderr'},
         'unchanged seven owner/worker outputs')
    owner_directory = transport.parent/'outputs'/freeze['selector']
    owner_paths = [Path(value) for value in plan['outputs'].values()]
    need(len(set(owner_paths)) == 7 and all(path.is_absolute() and path.parent == owner_directory for path in owner_paths),
         'fresh original compact output namespace')
    expected = {'owner_stdout', 'owner_stderr', 'pending_receipt', 'ROOT_closed_SELF', 'failure_state'}
    need(set(freeze['entry_outputs']) == expected, 'complete distinct ROOT output paths')
    paths = [Path(value) for value in freeze['entry_outputs'].values()]
    directory = HERE / 'outputs' / freeze['selector']
    need(len(set(paths)) == len(paths) and all(path.is_absolute() and path.parent == directory for path in paths),
         'fresh exact ROOT selector namespace')
    need(directory != owner_directory, 'ROOT frames and owner seven-output directory are separate')
    return freeze, pin(freeze_path), plan_path, plan, containment


def owner_mode(freeze_path):
    freeze, freeze_pin, plan_path, plan, containment = preflight(freeze_path)
    need(os.getpid() == os.getpgrp() == os.getsid(0), 'ROOT-created owner session/group leader')
    sys.path.insert(0, str(resolve(freeze['transport_directory'])))
    adapter = load(EXACT_ADAPTER_PIN, 'prospective_ROOT_accounting_adapter_v4')
    owner = load(EXACT_OWNER_PIN, 'prospective_compact_owner_v5')
    accounting = adapter.AccountingAdapter(freeze['adapter_pin'],
                                          plan['compact_transport_contract']['platform_evidence_pin'], os.getpid())
    # This ends with an owned closed SELF frame or a retained containment latch.
    owner.run_owner(plan_path, accounting)
    raise RuntimeError('owner unexpectedly returned without frame or containment')


def run_entry(freeze_path):
    install_flags()
    root_pid = os.getpid()
    freeze, freeze_pin, plan_path, plan, containment = preflight(freeze_path)
    outputs = freeze['entry_outputs']
    directory = Path(outputs['pending_receipt']).parent
    need(not directory.exists() and not Path(plan['outputs']['lifetime']).parent.exists(),
         'one never-executed namespace; partial/unknown attempts cannot be restarted')
    directory.mkdir(parents=True, exist_ok=False)
    child = None; waited = False; usage = None; reap_clock = None
    emergency = False; kill_attempted = False; kill_error = None
    stopping = False; latched = False; failure = None; started = None
    deadline_record_attempted = False

    def reap_once():
        nonlocal waited, usage, reap_clock
        try:
            pid, status, current = os.wait4(child.pid, os.WNOHANG)
        except InterruptedError:
            return False
        if not pid:
            return False
        need(pid == child.pid, 'exact retained direct owner reap')
        waited = True
        usage = current
        child.returncode = os.waitstatus_to_exitcode(status)
        reap_clock = time.perf_counter()
        return True

    def kill_live_group_once():
        nonlocal emergency, kill_attempted, kill_error
        if child is None or waited or kill_attempted:
            return
        # Claim the single attempt before syscall. Non-raising flags preserve
        # bookkeeping; never signal a historical group after terminal reap.
        emergency = True
        kill_attempted = True
        try:
            need(os.getpgid(child.pid) == child.pid, 'retained direct fresh owner-led group')
            os.killpg(child.pid, signal.SIGKILL)
        except BaseException as exc:
            kill_error = type(exc).__name__ + ': ' + str(exc)

    def record_expired_boundary(now):
        nonlocal failure, deadline_record_attempted
        if now - ENTRY < 180 or deadline_record_attempted:
            return
        deadline_record_attempted = True
        failure = failure or 'UNKNOWN: ROOT deadline; retain exact owner handle until terminal reap'
        try:
            write_new(outputs['failure_state'], dict(status='UNKNOWN_retained_owner_pending_reap',
                      ROOT_pid=root_pid, pid=child.pid if child else None,
                      group=child.pid if child else None, elapsed=now - ENTRY,
                      latched=latched, emergency=emergency, kill_attempted=kill_attempted,
                      kill_error=kill_error, no_complete_reap_claim=True))
        except BaseException:
            pass

    with Path(outputs['owner_stdout']).open('xb') as out, Path(outputs['owner_stderr']).open('xb') as err:
        try:
            need(not cancelled_signum, 'cancellation before launch')
            started = time.perf_counter()
            child = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()),
                                      'owner', str(Path(freeze_path).resolve())],
                                     stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                     start_new_session=True,
                                     env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            # The exact handle is assigned before any cancellation decision.
            while True:
                if reap_once():
                    break
                now = time.perf_counter()
                latched = latched or containment.exists()
                if (cancelled_signum or latched or now - started >= 175 or now - ENTRY >= 178) and not stopping:
                    stopping = True
                    try:
                        os.kill(child.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                if latched or now - started >= 176 or now - ENTRY >= 179:
                    kill_live_group_once()
                record_expired_boundary(now)
                time.sleep(.005)
        except BaseException as exc:
            failure = type(exc).__name__ + ': ' + str(exc)
        finally:
            if child is not None and not waited:
                kill_live_group_once()
                # No timeout is a completed reap. Retain this exact handle and
                # recorded failure indefinitely if the kernel cannot return.
                while not waited:
                    try:
                        if reap_once():
                            break
                    except BaseException as exc:
                        failure = failure or type(exc).__name__ + ': ' + str(exc)
                    record_expired_boundary(time.perf_counter())
                    time.sleep(.005)
    terminal = time.perf_counter()
    latched = latched or containment.exists()
    candidate = bool(child is not None and waited and child.returncode == 0
                     and not (cancelled_signum or emergency or stopping or latched or failure)
                     and terminal - started <= 175 and terminal - ENTRY <= 180)
    result = None; closed_artifacts = {}; containment_record = None
    if candidate:
        try:
            need(Path(outputs['owner_stderr']).stat().st_size == 0
                 and Path(plan['outputs']['stderr']).stat().st_size == 0,
                 'successful raw owner and worker stderr streams are empty')
            result = replay_closed_accounting(freeze, freeze_pin, plan_path, plan,
                                              child.pid, root_pid, started, terminal)
            for name, path in plan['outputs'].items():
                closed_artifacts['owner_' + name] = pin(path)
            closed_artifacts['owner_frame_stdout'] = pin(outputs['owner_stdout'])
            closed_artifacts['owner_frame_stderr'] = pin(outputs['owner_stderr'])
            need(pin(Path(freeze_path).resolve()) == freeze_pin, 'immutable exact activation through full replay')
            verify(freeze['entry_pin']); verify(EXACT_OWNER_PIN); verify(EXACT_ADAPTER_PIN)
            validate_raw_usage(raw_usage(usage), 'direct owner descendant-inclusive terminal')
        except BaseException as exc:
            candidate = False
            failure = type(exc).__name__ + ': ' + str(exc)
    if latched:
        try:
            containment_record = read_small(containment)
            need(containment_record['schema'] == 'compact-owner-V3-live-group-containment-v1'
                 and containment_record['status'] == 'UNKNOWN_REQUIRES_ROOT_LIVE_GROUP_TERMINATION'
                 and containment_record['selector'] == freeze['selector'], 'exact closed containment grammar')
            same_json(containment_record['owner'], EXACT_OWNER_PIN, 'closed latch exact owner source')
            same_json(containment_record['group'], dict(owner_pid=child.pid, owner_pgid=child.pid,
                      owner_sid=child.pid, ROOT_parent_pid=root_pid), 'latched exact fresh retained group')
            containment_record = dict(pin=pin(containment), value=containment_record)
        except BaseException as exc:
            failure = failure or type(exc).__name__ + ': ' + str(exc)
            containment_record = dict(status='UNKNOWN_invalid_or_missing_closed_latch', error=str(exc))
    own_before = raw_usage(resource.getrusage(resource.RUSAGE_SELF))
    elapsed = time.perf_counter() - ENTRY
    candidate = bool(candidate and not cancelled_signum and not containment.exists() and elapsed <= 180)
    receipt = dict(schema='ROOT-compact-static-pending-terminal-tool-v2',
                   status='pending_external_terminal_ROOT_ledger' if candidate else 'UNKNOWN',
                   ROOT_pid=root_pid, selector=freeze['selector'], freeze=freeze_pin,
                   plan=freeze['plan_pin'], activation=freeze['activation_pin'],
                   entry_source=freeze['entry_pin'], entry_source_manifest=freeze['entry_source_manifest_pin'],
                   owner_source=EXACT_OWNER_PIN, owner_source_manifest=EXACT_OWNER_MANIFEST_PIN,
                   adapter_source=EXACT_ADAPTER_PIN, platform_evidence=freeze['platform_evidence_pin'],
                   owner_pid=child.pid if child else None, owner_group=child.pid if child else None,
                   owner_reaped=waited, owner_exit=child.returncode if child else None,
                   owner_terminal_wait4_raw=raw_usage(usage) if usage else None,
                   owner_creation_clock=started, owner_terminal_reap_clock=reap_clock,
                   owner_streams_closed_clock=terminal,
                   owner_creation_through_reap_and_stream_close_seconds=terminal - started if started else None,
                   owner_closed_SELF=result['owner_frame'] if result else None,
                   provisional=result['regenerated_provisional'] if result else None,
                   closed_accounting_replay=result['replay'] if result else None,
                   closed_artifacts=closed_artifacts, containment_record=containment_record,
                   ROOT_SELF_before_final_receipt_write_raw=own_before,
                   ROOT_seconds_before_final_receipt_write=elapsed,
                   cancellation_signum=cancelled_signum, emergency_group_kill=emergency,
                   group_kill_attempted_once=kill_attempted, group_kill_error=kill_error,
                   cooperative_stop=stopping, containment_latched=latched, failure=failure,
                   semantic_candidate=candidate, resource_accepted=False, all_five_qualification=False,
                   known_topology_only=True, no_grandchild_reap_claim=True,
                   remaining='Closed receipt, raw ROOT SELF, fixed52byte ROOT frame file, hard exit; separate trusted external terminal/full tool clock/topology/reserve gate required.')
    write_new(outputs['pending_receipt'], receipt)
    # This file closes after the fixed postlude; external ROOT provenance owns
    # final hash/exit/reap/time. No finish_root_ledger call is made internally.
    with Path(outputs['ROOT_closed_SELF']).open('xb', buffering=0) as stream:
        closed = time.perf_counter()
        raw = resource.getrusage(resource.RUSAGE_SELF)
        need(math.isfinite(ENTRY) and math.isfinite(closed) and closed >= ENTRY
             and type(raw.ru_maxrss) is int and raw.ru_maxrss > 0, 'finite final raw ROOT frame')
        code = 0 if candidate and not cancelled_signum and closed - ENTRY <= 180 else 1
        data = FRAME.pack(b'GCTSCMP1', 3, code, 0, root_pid, raw.ru_maxrss,
                          closed - ENTRY, ENTRY, closed)
        offset = 0
        while offset < len(data):
            count = stream.write(data[offset:])
            if count <= 0:
                os._exit(2)
            offset += count
    os._exit(code)


def main():
    need(len(sys.argv) == 3 and sys.argv[1] in ('entry', 'owner'),
         'SOURCE ONLY until exact separately ROOT-frozen activation is supplied')
    path = Path(sys.argv[2]).resolve()
    if sys.argv[1] == 'owner':
        owner_mode(path)
    else:
        run_entry(path)


if __name__ == '__main__':
    main()
