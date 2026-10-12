"""SOURCE ONLY V2: process-local clock external gate after one trusted terminal ROOT tool.

No dispatch, process observation, scientific import or replay is performed.
Only exact adapter V4 is loaded, after the closed inputs have been rebound.
Saved tool evidence is trusted ROOT provenance, not external raw wait4 or OS
attestation. Finalization cost is additional to the observed static phase.
"""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shlex
import stat
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MAX_METADATA = 1048576
FRAME = struct.Struct('!8sBBHQQddd')
LIMITS = dict(whole_seconds=180, supervisor_seconds=175, child_seconds=170,
              peak_bytes=536870912)
RESERVE = 33554432
BIND = '.gcts-active/process-local-clock-successor-source-20261012/'
WRAP = '.gcts-active/curriculum-compact-wrapper-source-20261012/'
ENTRY = {'path': '.gcts-active/process-local-clock-successor-source-20261012/root_compact_entry_v3.py', 'sha256': '6aa5d2fc1885ff101edbd7139f6599e9df4bc625259f27b450f866f565f1e997', 'bytes': 46554}
ENTRY_MANIFEST = {'path': '.gcts-active/process-local-clock-successor-source-20261012/source-plan-root-entry-v3.json', 'sha256': 'c720005898f473482e1d2e852b06f5c05570b38c4e5630dc5a059d38c8adaf1e', 'bytes': 3294}
OWNER = {'path': '.gcts-active/process-local-clock-successor-source-20261012/curriculum_compact_owner_v5.py', 'sha256': '64a66b3f5feba295e1e4d1964873153d4f9400b4193058f8db4adc026b2ada7e', 'bytes': 27912}
OWNER_MANIFEST = {'path': '.gcts-active/process-local-clock-successor-source-20261012/source-plan-owner-v5.json', 'sha256': '1537702e25cccb9697d9404fc09c5a53dcf354de0415c54f77ea8f9b942c7422', 'bytes': 3071}
ADAPTER = {'path': '.gcts-active/curriculum-compact-root-binding-source-20261012/root_accounting_adapter_v4.py', 'sha256': 'e9620ffec78f2b014107b2907456aab2dc933084ecee0f5f96e62df11d6a631d', 'bytes': 21195}
CLOCK_CONTRACT = {'path': '.gcts-active/equality-clock-interface-source-review-20261012/future-clock-contract-v1.json', 'sha256': '61238d81491eea7c9cdd8501dff9a0a78d9666302a545b38f8dd2eadf2ad323b', 'bytes': 6153}
WORKER = dict(path=WRAP + 'curriculum_compact_worker_v1.py',
              sha256='77a15d292833f82ee759b522ed8a615da4bad7d43f48e8ccc218844cac9c1dd3', bytes=13759)
TRANSPORT = dict(path=WRAP + 'compact_static_transport_v1.py',
                 sha256='65a0b598966ae4dffdda1b770eb2d4d5b64af1bcaf6aead4281a224a4123def3', bytes=13756)
BOUND = {}


def need(test, message):
    if not test:
        raise ValueError(message)


def same(actual, expected, message):
    encode = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    need(encode(actual) == encode(expected), message)


def integer(value, message, positive=False):
    need(type(value) is int and value >= (1 if positive else 0), message)
    return value


def clock(value, message):
    need(type(value) in (int, float) and math.isfinite(value) and value >= 0, message)
    return value


def resolve(name):
    path = Path(name)
    return path if path.is_absolute() else ROOT / path


def pin(path, declared=None):
    path = Path(path)
    need(not path.is_symlink(), 'closed evidence/source is not a symlink')
    h = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        need(stat.S_ISREG(before.st_mode), 'closed regular source/artifact')
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); size += len(block)
        after = os.fstat(stream.fileno())
    identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
    need(identity(before) == identity(after) == identity(path.stat()) and size == after.st_size,
         'stable closed stream identity')
    if declared is None:
        try: declared = str(path.relative_to(ROOT))
        except ValueError: declared = str(path)
    return dict(path=declared, sha256=h.hexdigest(), bytes=size)


def verify(record):
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}, 'exact three-field pin')
    need(type(record['path']) is str and bool(record['path']), 'declared pin path')
    integer(record['bytes'], 'pin size')
    digest = record['sha256']
    need(type(digest) is str and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest),
         'lowercase exact SHA256')
    path = resolve(record['path'])
    same(pin(path, record['path']), record, 'exact source/artifact bytes')
    if record['path'] in BOUND:
        same(BOUND[record['path']], record, 'consistent repeated immutable pin')
    BOUND[record['path']] = dict(record)
    return path


def fields(pairs):
    value = {}
    for key, item in pairs:
        need(key not in value, 'duplicate metadata field')
        value[key] = item
    return value


def finite_number(token):
    value = float(token)
    need(math.isfinite(value), 'finite metadata number')
    return value


def read(record):
    need(record['bytes'] <= MAX_METADATA, 'existing one-MiB metadata bound before hash/decode')
    path = verify(record)
    with path.open('rb') as stream:
        raw = stream.read(MAX_METADATA + 1)
    need(len(raw) == record['bytes'] and hashlib.sha256(raw).hexdigest() == record['sha256'],
         'decoded metadata buffer is the exact pinned stream')
    verify(record)
    return json.loads(raw, object_pairs_hook=fields, parse_float=finite_number,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite metadata token')))


def read_path(path):
    need(Path(path).stat().st_size <= MAX_METADATA, 'bounded metadata before initial pin')
    record = pin(path)
    return read(record), record


def frame(path, role, pid):
    need(Path(path).stat().st_size == FRAME.size == 52, 'raw frame size before streamed hash')
    record = pin(path)
    need(record['bytes'] == FRAME.size == 52, 'exact raw52 byte frame')
    with Path(path).open('rb') as stream:
        raw = stream.read(53)
    need(len(raw) == 52 and hashlib.sha256(raw).hexdigest() == record['sha256'],
         'actual decoded frame buffer equals the pinned hash')
    magic, tag, code, reserved, actual_pid, rss, elapsed, began, closed = FRAME.unpack(raw)
    need(magic == b'GCTSCMP1' and tag == role and code == reserved == 0
         and actual_pid == integer(pid, 'registered raw frame PID', True) and rss > 0,
         'successful exact raw frame role/PID/code/reserved/SELF')
    need(all(math.isfinite(v) and v >= 0 for v in (elapsed, began, closed))
         and closed >= began and elapsed == closed - began, 'finite exact closed raw frame clock')
    verify(record)
    return dict(role=tag, pid=actual_pid, exit_code=code, SELF_ru_maxrss_raw=rss,
                seconds_after_all_artifact_close_before_fixed_postlude=elapsed,
                entry_monotone_clock=began, last_closed_monotone_clock=closed,
                remaining_postlude='Fixed52-byte pack/write then os._exit; separately ROOT-reviewed reserve required',
                terminal_frame=record)


def raw_usage(value):
    times = {'ru_utime', 'ru_stime'}
    counts = {'ru_maxrss', 'ru_ixrss', 'ru_idrss', 'ru_isrss', 'ru_minflt', 'ru_majflt',
              'ru_nswap', 'ru_inblock', 'ru_oublock', 'ru_msgsnd', 'ru_msgrcv',
              'ru_nsignals', 'ru_nvcsw', 'ru_nivcsw'}
    need(type(value) is dict and set(value) == times | counts, 'complete original raw Python3.9 usage fields')
    for name in times:
        need(type(value[name]) is float, 'raw usage floating CPU time')
        clock(value[name], 'raw usage finite CPU time')
    for name in counts:
        integer(value[name], 'raw usage integer counter', name == 'ru_maxrss')
    return value


def local_child_lifetime(receipt, owner_frame, worker_frame, owner_pid):
    """Authenticate one emitter's local chain and durations, never align origins."""
    same(dict(clock_emitter_pid=receipt['clock_emitter_pid'],
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
    same(started,owner_frame['entry_monotone_clock'],'raw owner entry equals receipt local entry')
    need(started<=created<=reaped<=closed<=owner_frame['last_closed_monotone_clock']
         and seconds==reaped-created and full==closed-created,
         'same-owner raw creation/reap/stream-close chain and exact reconstructed durations')
    need(worker_frame['seconds_after_all_artifact_close_before_fixed_postlude']<=seconds<=170
         and seconds<=full<=owner_frame['seconds_after_all_artifact_close_before_fixed_postlude']<=175,
         'per-process durations nest inside unchanged child/owner caps')
    return seconds,full


def finalize(contract_path, terminal_path):
    contract, contract_pin = read_path(contract_path)
    selector=contract['selector']
    need(selector in ('donor-repeated-guard','donor-repeated-equality','heldout-mixed-guard-equality'),
         'still-unexecuted future selector; both actual UNKNOWN donors excluded')
    gate_directory=HERE/'terminal-gates'/selector
    need(Path(contract_path).resolve()==gate_directory/'static-prospective-tool-contract-v1.json',
         'exact prior ROOT contract in fresh future selector namespace')
    fixed = dict(schema='ROOT-compact-static-external-tool-contract-v1', selector=selector,
                 ROOT_sole_actual_owner=True, attempts=1, cwd=str(ROOT), limits=LIMITS,
                 postlude_reserve_bytes=RESERVE, external_wait4_claim=False,
                 all_five_qualification=False, scientific_settings_changed=False,
                 process_local_clock_contract_pin=CLOCK_CONTRACT)
    same({key: contract[key] for key in fixed}, fixed, 'strict prospective scope/settings/limits')
    same(contract['clock'], dict(kind='ROOT-Date.now-enclosing-tool-boundary-v1', margin_seconds=1),
         'unchanged explicit external clock rule')
    need(contract['expected_tool_terminal_path'] == str(gate_directory / 'static-tool-terminal-v1.json')
         and Path(terminal_path).resolve() == Path(contract['expected_tool_terminal_path']), 'exact real terminal path')
    output = gate_directory / 'static-resource-disposition-v1.json'
    need(contract['result_output'] == str(output) and not output.exists(), 'exclusive fixed disposition output')
    need(verify(contract['finalizer_pin']).resolve() == Path(__file__).resolve(), 'this exact separately reviewed finalizer')
    freeze = read(contract['entry_activation_pin'])
    fixed_freeze = dict(schema='ROOT-prospective-compact-static-entry-activation-v3', authorized=True,
                        ROOT_sole_actual_owner=True, selector=contract['selector'], limits=LIMITS,
                        entry_pin=ENTRY, entry_source_manifest_pin=ENTRY_MANIFEST, owner_pin=OWNER,
                        owner_source_manifest_pin=OWNER_MANIFEST, adapter_pin=ADAPTER,
                        platform_evidence_pin=contract['platform_evidence_pin'])
    same({key: freeze[key] for key in fixed_freeze}, fixed_freeze, 'exact frozen entry/owner/adapter/activation')
    same(freeze['runtime'], contract['runtime'], 'complete runtime activation/contract correspondence')
    for record in (ENTRY, ENTRY_MANIFEST, OWNER, OWNER_MANIFEST, ADAPTER, WORKER, TRANSPORT, CLOCK_CONTRACT):
        verify(record)
    runtime = contract['runtime']
    need(runtime['platform'] == sys.platform == 'darwin'
         and Path(sys.executable).resolve() == Path(runtime['binary']['path'])
         and Path(runtime['executable']).resolve() == Path(sys.executable).resolve(), 'actual pinned Darwin interpreter')
    for key in ('binary', 'resource_extension', 'posixsubprocess_extension', 'observer'):
        verify(runtime[key])
    # These future ROOT imports locate the actual native modules only; no
    # getrusage/Popen/process or scientific function is called here.
    import resource
    import _posixsubprocess
    need(Path(resource.__file__).resolve() == Path(runtime['resource_extension']['path'])
         and Path(_posixsubprocess.__file__).resolve() == Path(runtime['posixsubprocess_extension']['path']),
         'native pins are tied to actual loaded runtime module paths')
    need('sitecustomize' not in sys.modules and 'usercustomize' not in sys.modules,
         'no unreviewed runtime customization')
    argv = [runtime['executable'], '-B', str(resolve(ENTRY['path'])), 'entry',
            str(verify(contract['entry_activation_pin']))]
    actual_argv = shlex.split(contract['literal_command'])
    need(len(actual_argv) == 5, 'one exact five-argument entry command')
    actual_argv[2] = str(resolve(actual_argv[2]))
    actual_argv[4] = str(resolve(actual_argv[4]))
    same(actual_argv, argv, 'literal command resolves under exact cwd to this one frozen entry invocation')
    review = read(contract['source_review_pin'])
    fixed_review = dict(schema='ROOT-compact-static-source-review-for-terminal-gate-v1',
                        full_sources_reviewed=True, source_review_passed=True, scientific_calls=0)
    same({key: review[key] for key in fixed_review}, fixed_review, 'separate full source review before invocation')
    need(type(review['source_records']) is list, 'source review exact records')
    for record in review['source_records']:
        verify(record)
    for record in (ENTRY, ENTRY_MANIFEST, OWNER, OWNER_MANIFEST, ADAPTER, WORKER, TRANSPORT, CLOCK_CONTRACT,
                   contract['finalizer_pin']):
        need(record in review['source_records'], 'complete frozen code/manifest/finalizer source review')
    platform = read(contract['platform_evidence_pin'])
    need(platform['status'] == 'ROOT_verified_platform_accounting_evidence'
         and all(platform[name] is True for name in ('units_verified', 'wait4_descendant_scope_verified',
                 'leaf_worker_and_observer_scope_verified', 'closed_SELF_postlude_scope_reviewed')),
         'separately verified conditional platform/topology/postlude scope')
    same(platform['adapter_pin'], ADAPTER, 'platform evidence authorizes exact adapter V4')
    same(platform['postlude_reserve_bytes'], RESERVE, 'platform retains original prospective32MiB reserve')
    plan = read(freeze['plan_pin']); activation = read(freeze['activation_pin'])
    fixed_plan = dict(schema='frozen-curriculum-independent-compact-static-plan-v1',
                      status='frozen_actual_inputs_pending_ROOT_activation', selector=contract['selector'],
                      stage='static', actual_execution_authorized=False, ROOT_sole_actual_owner=True, limits=LIMITS)
    same({key: plan[key] for key in fixed_plan}, fixed_plan, 'exact unchanged actual static plan')
    need(plan['required_owner_success_status'] == 'completed_compact_semantic_candidate_pending_full_ROOT_resources'
         and plan['required_result_status'] == 'passed_independent_frozen_curriculum_context_family_pool_audit',
         'actual plan names the exact source-defined owner/result successes')
    fixed_activation = dict(schema='ROOT-independent-frozen-curriculum-compact-static-activation-v1',
                            authorized=True, selector=contract['selector'], plan=freeze['plan_pin'])
    same({key: activation[key] for key in fixed_activation}, fixed_activation, 'exact original owner/worker activation')
    ct = plan['compact_transport_contract']
    for key, expected in dict(owner_pin=OWNER, worker_pin=WORKER, transport_pin=TRANSPORT,
                              accounting_adapter_pin=ADAPTER, wrapper_source_manifest_pin=OWNER_MANIFEST,
                              platform_evidence_pin=contract['platform_evidence_pin'],
                              fresh_ROOT_owned_owner_group_required=True,
                              process_local_clock_contract_pin=CLOCK_CONTRACT).items():
        same(ct[key], expected, 'same original compact contract binding: ' + key)
    need(integer(ct['compact_maximum_bytes'], 'frozen compact byte bound', True) <= MAX_METADATA
         and ct['observer_seconds'] == 1, 'existing compact metadata and observer bounds')
    for key in ('executable', 'platform', 'binary', 'observer'):
        same(plan['runtime'][key], runtime[key], 'actual plan/runtime connection: ' + key)
    for key in ('resource_extension', 'posixsubprocess_extension'):
        if key in plan['runtime']:
            same(plan['runtime'][key], runtime[key], 'native plan/runtime connection: ' + key)
    terminal, terminal_pin = read_path(terminal_path)
    fixed_terminal = dict(schema='ROOT-compact-static-actual-terminal-tool-v1',
                          prospective_plan=contract_pin, literal_command=contract['literal_command'],
                          actual_invocations=1, terminal=True, external_wait4_claim=False,
                          all_five_qualification=False)
    same({key: terminal[key] for key in fixed_terminal}, fixed_terminal, 'actual trusted terminal/contract/one-shot binding')
    observation = terminal['terminal_tool_result']
    need(type(observation) is dict and set(observation) == {'began_ms', 'observed_ms', 'enclosing_seconds',
         'enclosing_bound_seconds', 'result'}, 'exact terminal tool window')
    began_ms = integer(observation['began_ms'], 'actual tool window begin', True)
    observed_ms = integer(observation['observed_ms'], 'actual tool window close', True)
    need(observed_ms >= began_ms, 'nondecreasing real external tool window')
    for record in (contract_pin, contract['entry_activation_pin'], freeze['activation_pin'],
                   contract['source_review_pin'], contract['platform_evidence_pin']):
        need(resolve(record['path']).stat().st_mtime_ns // 1000000 <= began_ms,
             'prospective contract/review/activation/platform files precede actual tool start')
    elapsed = clock(observation['enclosing_seconds'], 'external enclosing seconds')
    bound = clock(observation['enclosing_bound_seconds'], 'external full bound')
    need(abs(elapsed - (observed_ms - began_ms) / 1000) <= 0.000000001
         and abs(bound - (elapsed + 1)) <= 0.000000001, 'actual Date.now interval plus exact prospective1-second margin')
    result = observation['result']
    need(type(result) is dict and {'exit_code', 'wall_time_seconds', 'chunk_id', 'output'} <= set(result)
         and set(result) <= {'exit_code', 'wall_time_seconds', 'chunk_id', 'output', 'original_token_count'}
         and type(result['exit_code']) is int and result['exit_code'] == 0
         and type(result['chunk_id']) is str and bool(result['chunk_id']) and result['output'] == '',
         'trusted successful terminal tool result; no running session or extra output')
    tool_wall = clock(result['wall_time_seconds'], 'actual tool wait wall time')
    need(tool_wall <= bound <= 180, 'external full bound covers tool wall and frozen180-second limit')
    eo = freeze['entry_outputs']; po = plan['outputs']
    need(set(eo) == {'owner_stdout', 'owner_stderr', 'pending_receipt', 'ROOT_closed_SELF', 'failure_state'}
         and set(po) == {'result', 'compact', 'lifetime', 'observers', 'samples', 'stdout', 'stderr'},
         'unchanged complete output schemas')
    root_dir = ROOT / BIND / 'outputs' / contract['selector']
    owner_dir = ROOT / WRAP / 'outputs' / contract['selector']
    need(len(set(eo.values())) == 5 and len(set(po.values())) == 7
         and all(Path(p).is_absolute() and Path(p).parent == root_dir for p in eo.values())
         and all(Path(p).is_absolute() and Path(p).parent == owner_dir for p in po.values()),
         'paths derived from exact separate fresh source namespaces')
    need(Path(ct['containment_output']).parent == owner_dir
         and ct['containment_output'] not in po.values()
         and not Path(ct['containment_output']).exists() and not Path(eo['failure_state']).exists(),
         'no containment latch or failed-reap boundary publication')
    pending, pending_pin = read_path(eo['pending_receipt'])
    fixed_pending = dict(schema='ROOT-compact-static-pending-terminal-tool-v2',
        status='pending_external_terminal_ROOT_ledger', selector=contract['selector'],
        freeze=contract['entry_activation_pin'], plan=freeze['plan_pin'], activation=freeze['activation_pin'],
        entry_source=ENTRY, entry_source_manifest=ENTRY_MANIFEST, owner_source=OWNER,
        owner_source_manifest=OWNER_MANIFEST, adapter_source=ADAPTER,
        platform_evidence=contract['platform_evidence_pin'], owner_reaped=True, owner_exit=0,
        containment_record=None, cancellation_signum=0, emergency_group_kill=False,
        group_kill_attempted_once=False, group_kill_error=None, cooperative_stop=False,
        containment_latched=False, failure=None, semantic_candidate=True, resource_accepted=False,
        all_five_qualification=False, known_topology_only=True, no_grandchild_reap_claim=True,
        remaining='Closed receipt, raw ROOT SELF, fixed52byte ROOT frame file, hard exit; separate trusted external terminal/full tool clock/topology/reserve gate required.')
    same({key: pending[key] for key in fixed_pending}, fixed_pending, 'exact successful pending source/artifact/flag scope')
    pending_variable = {'ROOT_pid', 'owner_pid', 'owner_group', 'owner_terminal_wait4_raw',
        'owner_creation_clock', 'owner_terminal_reap_clock', 'owner_streams_closed_clock',
        'owner_creation_through_reap_and_stream_close_seconds', 'owner_closed_SELF', 'provisional',
        'closed_accounting_replay', 'closed_artifacts', 'ROOT_SELF_before_final_receipt_write_raw',
        'ROOT_seconds_before_final_receipt_write'}
    need(set(pending) == set(fixed_pending) | pending_variable, 'exact closed entry V2 pending grammar')
    root_pid = integer(pending['ROOT_pid'], 'actual saved ROOT PID', True)
    owner_pid = integer(pending['owner_pid'], 'retained directly reaped owner PID', True)
    need(root_pid != owner_pid and pending['owner_group'] == owner_pid, 'distinct fresh retained owner group')
    owner_receipt, owner_receipt_pin = read_path(po['lifetime'])
    need(type(owner_receipt) is dict and set(owner_receipt)==set(['OS_hard_cap_claim', 'SELF_before_final_receipt_serialization_raw', 'accounting_adapter', 'activation', 'all_five_qualification', 'cancellation_requested', 'cancellation_semantics', 'cancellation_signum', 'child_creation_through_reap_and_stream_close_seconds', 'child_exit', 'child_pid', 'child_reaped', 'child_seconds_including_startup_imports_all_serialization_exit_reap', 'clock_emitter_pid', 'clock_function', 'clock_origin_scope', 'compact_status', 'containment_output', 'failure', 'full_audit', 'full_resource_accepted', 'inherited_ROOT_owner_group', 'maximum_child_seconds', 'maximum_peak_bytes', 'maximum_supervisor_seconds', 'maximum_whole_seconds', 'native_queries', 'observer_count', 'observer_detail', 'owner', 'owner_entry_clock', 'owner_seconds_before_lifetime_receipt_write', 'plan', 'platform_evidence', 'provisional_platform_accounting', 'raw_wait4_scope', 'remaining_scope', 'sample_detail', 'schema', 'searches_run_by_owner', 'selector', 'semantic_static_candidate', 'source_manifest', 'static_context_pool_accepted', 'status', 'training_runs', 'worker', 'worker_closed_SELF', 'worker_creation_clock', 'worker_streams_closed_clock', 'worker_terminal_reap_clock', 'worker_terminal_wait4_raw']),
         'exact V5 closed owner receipt v2 grammar consistent with entry V3')
    same(pending['closed_artifacts']['owner_lifetime'], owner_receipt_pin, 'bounded owner receipt already exact-bound')
    count = integer(owner_receipt['observer_count'], 'complete paired observer census')
    need(count <= integer(ct['maximum_observers'], 'frozen observer count bound', True), 'same frozen complete count envelope')
    need(Path(po['compact']).stat().st_size <= ct['compact_maximum_bytes'], 'compact bound before stream hash')
    for name in ('observers', 'samples'):
        need(Path(po[name]).stat().st_size <= count * MAX_METADATA, 'complete table bound before stream hash')
    for path in (po['stdout'], eo['owner_stdout'], eo['ROOT_closed_SELF']):
        need(Path(path).stat().st_size == 52, 'exact frame size before artifact hashes')
    need(Path(po['stderr']).stat().st_size == Path(eo['owner_stderr']).stat().st_size == 0,
         'closed successful stderr size before hashes')
    expected_artifacts = {'owner_' + name: pin(path) for name, path in po.items()}
    expected_artifacts.update(owner_frame_stdout=pin(eo['owner_stdout']), owner_frame_stderr=pin(eo['owner_stderr']))
    same(pending['closed_artifacts'], expected_artifacts, 'all exact saved closed artifact pins rebound without decoding full audit')
    for record in expected_artifacts.values():
        verify(record)
    need(expected_artifacts['owner_stderr']['bytes'] == expected_artifacts['owner_frame_stderr']['bytes'] == 0,
         'successful owner/worker stderr closed and empty')
    same(owner_receipt_pin, expected_artifacts['owner_lifetime'], 'same bounded owner receipt through artifact hashing')
    worker_pid = integer(owner_receipt['child_pid'], 'registered direct worker PID', True)
    need(len({root_pid, owner_pid, worker_pid}) == 3, 'distinct actual saved role identities')
    group = dict(owner_pid=owner_pid, owner_pgid=owner_pid, owner_sid=owner_pid, ROOT_parent_pid=root_pid)
    owner_fixed = dict(schema='compact-static-owner-pending-ROOT-lifetime-v2',
        status='completed_compact_semantic_candidate_pending_full_ROOT_resources', selector=contract['selector'],
        plan=freeze['plan_pin'], owner=OWNER, worker=WORKER, activation=freeze['activation_pin'],
        source_manifest=OWNER_MANIFEST, platform_evidence=contract['platform_evidence_pin'], accounting_adapter=ADAPTER,
        inherited_ROOT_owner_group=group, containment_output=ct['containment_output'], child_exit=0, child_reaped=True,
        semantic_static_candidate=True, static_context_pool_accepted=False, full_resource_accepted=False,
        all_five_qualification=False, failure=None, cancellation_signum=0, cancellation_requested=False,
        native_queries=0, searches_run_by_owner=0, training_runs=0,
        raw_wait4_scope='Worker expected leaf; no subtraction from rolled nested peaks',
        cancellation_semantics='Non-raising INT/TERM/ALRM flags; checked only after spawn registration/terminal wait4 bookkeeping and at safe loop boundaries',
        maximum_whole_seconds=180,maximum_supervisor_seconds=175,maximum_child_seconds=170,
        maximum_peak_bytes=536870912,OS_hard_cap_claim=False,
        remaining_scope='After this closed receipt: raw SELF snapshot, fixed52byte terminal frame, os._exit. ROOT separately reviews preserved reserve and full180second launcher/dispatcher accounting.')
    same({key: owner_receipt[key] for key in owner_fixed}, owner_fixed, 'owner/worker bound sources and no failed/cancelled state')
    root_frame = frame(eo['ROOT_closed_SELF'], 3, root_pid)
    owner_frame = frame(eo['owner_stdout'], 2, owner_pid)
    worker_frame = frame(po['stdout'], 1, worker_pid)
    same(pending['owner_closed_SELF'], owner_frame, 'pending owner frame equals independently decoded raw52 bytes')
    same(owner_receipt['worker_closed_SELF'], worker_frame, 'worker frame equals independently decoded raw52 bytes')
    created = clock(pending['owner_creation_clock'], 'registered owner creation clock')
    reaped = clock(pending['owner_terminal_reap_clock'], 'actual direct owner reap clock')
    streams_closed = clock(pending['owner_streams_closed_clock'], 'actual owner raw stream close clock')
    full_owner = clock(pending['owner_creation_through_reap_and_stream_close_seconds'], 'full observed owner lifetime')
    need(root_frame['entry_monotone_clock']<=created<=reaped<=streams_closed<=root_frame['last_closed_monotone_clock']
         and full_owner==streams_closed-created,'same-ROOT local creation/reap/stream-close chain')
    need(owner_frame['seconds_after_all_artifact_close_before_fixed_postlude']<=full_owner<=175,
         'authenticated owner duration inside same-ROOT observed complete owner lifetime')
    worker_seconds,worker_full_close_seconds=local_child_lifetime(owner_receipt,owner_frame,worker_frame,owner_pid)
    owner_before=clock(owner_receipt['owner_seconds_before_lifetime_receipt_write'],'owner pre-receipt elapsed')
    need(owner_before<=owner_frame['seconds_after_all_artifact_close_before_fixed_postlude']<=175,
         'same-owner pre-receipt elapsed covered by own closed frame')
    root_seconds = root_frame['seconds_after_all_artifact_close_before_fixed_postlude']
    need(clock(pending['ROOT_seconds_before_final_receipt_write'], 'ROOT pre-final-write clock') <= root_seconds <= bound,
         'full external tool bound covers role3 after-close clock and pending serialization')
    root_before = raw_usage(pending['ROOT_SELF_before_final_receipt_write_raw'])
    need(root_before['ru_maxrss'] <= root_frame['SELF_ru_maxrss_raw'], 'raw closed ROOT SELF covers receipt allocation')
    replay = pending['closed_accounting_replay']
    replay_fixed = dict(schema='ROOT-independent-closed-accounting-replay-v3',
        status='replayed_closed_raw_records_pending_external_terminal_GATE', root_pid=root_pid,
        owner_pid=owner_pid, worker_pid=worker_pid, group=group, freeze=contract['entry_activation_pin'],
        plan=freeze['plan_pin'], activation=freeze['activation_pin'], owner_receipt=expected_artifacts['owner_lifetime'],
        owner_raw_frame=owner_frame['terminal_frame'], worker_raw_frame=worker_frame['terminal_frame'],
        observer_detail=owner_receipt['observer_detail'], sample_detail=owner_receipt['sample_detail'],
        clock_domains=dict(ROOT_emitter_pid=root_pid,owner_emitter_pid=owner_pid,worker_emitter_pid=worker_pid,
            function='time.perf_counter',absolute_origins='process_local_untrusted_across_processes'),
        clock_durations=dict(worker_create_through_reap_seconds=worker_seconds,
            worker_create_through_stream_close_seconds=worker_full_close_seconds,
            owner_create_through_stream_close_seconds=full_owner),
        raw_PS_rows_and_role_birth_rederived=True, provisional_exactly_regenerated=True,
        resource_accepted=False, all_five_qualification=False)
    same({key: replay[key] for key in replay_fixed}, replay_fixed, 'trusted exact entry already replayed and pinned complete raw accounting')
    need(set(replay) == set(replay_fixed) | {'raw_PS_pairs', 'full_JSONL_records', 'maximum_observer_complete_seconds'},
         'exact saved complete entry replay grammar')
    same(dict(raw_PS_pairs=replay['raw_PS_pairs'], full_JSONL_records=replay['full_JSONL_records'],
         observers=owner_receipt['observer_detail']['records'], samples=owner_receipt['sample_detail']['records']),
         dict(raw_PS_pairs=count, full_JSONL_records=2 * count, observers=count, samples=count),
         'same complete typed observed pair/table census')
    need(clock(replay['maximum_observer_complete_seconds'], 'saved full observer maximum') <= 1,
         'same frozen observer full one-second bound')
    for field, name in (('observer_detail', 'observers'), ('sample_detail', 'samples')):
        same(owner_receipt[field]['pin'], expected_artifacts['owner_' + name], 'exact closed full table pin')
        need(expected_artifacts['owner_' + name]['bytes'] <= count * MAX_METADATA,
             'bounded closed table before finalization; no table semantic replay')
    compact = read(expected_artifacts['owner_compact'])
    compact_fixed = dict(schema='exact-bound-independent-static-worker-compact-v1',
        plan=freeze['plan_pin'], worker=WORKER, transport=TRANSPORT, activation=freeze['activation_pin'],
        source_manifest=OWNER_MANIFEST, full_audit=expected_artifacts['owner_result'],
        full_resource_accepted=False, all_five_qualification=False)
    same({key: compact[key] for key in compact_fixed}, compact_fixed, 'unchanged closed full audit/compact/source binding')
    same(owner_receipt['full_audit'], expected_artifacts['owner_result'], 'owner binds exact full static audit bytes')
    same(owner_receipt['compact_status'], expected_artifacts['owner_compact'], 'owner binds exact compact scalar bytes')
    projection = compact['projection']
    same({key: projection[key] for key in ct['expected_scalar_identity']}, ct['expected_scalar_identity'],
         'same exact small context identity')
    expected_projection = dict(status=plan['required_result_status'], static_context_pool_accepted=True,
        trace_accepted=False, certificate_accepted=False, RL_full_pool_capacity=64,
        primitive_license_count=229, non_assumption_witness_count=226, source_body_count=171,
        single_types=171, pair_types=29241, whole_target_logical_checks=0,
        native_queries=0, native_accepted=False, searches=0, training=0)
    same({key: projection[key] for key in expected_projection}, expected_projection,
         'unchanged compact static census/zero search/proof/training/native scope')
    need(type(compact['complete_group_count']) is int and compact['complete_group_count'] >= 0
         and compact['complete_group_count'] == ct['expected_complete_group_count']
         and projection['RL_full_pool_capacity_satisfied'] is (compact['complete_group_count'] <= 64),
         'same pending semantic static result and unchanged complete64-capacity scope')
    same(pending['provisional'], owner_receipt['provisional_platform_accounting'], 'same entry-reconstructed full provisional projection')
    worker_raw = raw_usage(owner_receipt['worker_terminal_wait4_raw'])
    worker_seconds = clock(owner_receipt['child_seconds_including_startup_imports_all_serialization_exit_reap'],
                           'complete direct worker clock')
    need(worker_frame['seconds_after_all_artifact_close_before_fixed_postlude'] <= worker_seconds <= 170,
         'authenticated raw worker closed clock inside complete170-second scope')
    same(pending['provisional']['leaf_worker'], dict(pid=worker_pid,
         terminal_peak_bytes=worker_raw['ru_maxrss'], closed_SELF_peak_bytes=worker_frame['SELF_ru_maxrss_raw'],
         full_seconds=worker_seconds), 'provisional direct worker bound to actual raw frame/wait4/clock')
    own_before = raw_usage(owner_receipt['SELF_before_final_receipt_serialization_raw'])
    same(pending['provisional']['owner_SELF_before_receipt_bytes'], own_before['ru_maxrss'],
         'provisional owner pre-close SELF bound to its saved raw observation')
    owner_raw = raw_usage(pending['owner_terminal_wait4_raw'])
    # The only project module imported is the exact metadata-only adapter.
    name = 'ROOT_external_terminal_adapter_v4'
    need(name not in sys.modules, 'no cached external adapter substitution')
    spec = importlib.util.spec_from_file_location(name, verify(ADAPTER))
    adapter = importlib.util.module_from_spec(spec); sys.modules[name] = adapter
    spec.loader.exec_module(adapter)
    provenance = dict(terminal=True, exit_code=result['exit_code'], cancelled=False,
        emergency_group_kill=False, containment_latched=False, complete_known_topology=True,
        full_tool_boundary_seconds=bound, terminal_tool_result=terminal_pin, prospective_contract=contract_pin,
        ROOT_raw_closed_frame=root_frame['terminal_frame'], external_wait4_claim=False,
        topology_scope='Conditional exact pinned one-leaf/sequential-observer topology; source and sampled record scope, not an escape-free OS guarantee')
    ledger = adapter.finish_root_ledger(pending['provisional'], owner_frame, owner_raw,
        {'ru_maxrss': root_frame['SELF_ru_maxrss_raw']}, full_owner, root_seconds, provenance)
    need(ledger['all_five_qualification'] is False, 'adapter cannot escalate all-five scope')
    same(ledger['terms_bytes']['reviewed_fixed_postlude_reserve'], RESERVE, 'original prospective reviewed32MiB reserve')
    for record in tuple(BOUND.values()):
        verify(record)
    need(not Path(ct['containment_output']).exists() and not Path(eo['failure_state']).exists(), 'no late failure/latch publication')
    accepted = ledger['resource_accepted'] is True
    disposition = dict(schema='ROOT-compact-static-external-resource-disposition-v1',
        status='accepted_conditional_known_topology_static_resource_envelope' if accepted else 'UNKNOWN',
        selector=contract['selector'], prospective_contract=contract_pin, terminal_tool_result=terminal_pin,
        finalizer=contract['finalizer_pin'], entry_activation=contract['entry_activation_pin'],
        plan=freeze['plan_pin'], activation=freeze['activation_pin'], source_review=contract['source_review_pin'],
        platform_evidence=contract['platform_evidence_pin'], pending_receipt=pending_pin,
        ROOT_raw_frame=root_frame, owner_raw_frame=owner_frame, worker_raw_frame=worker_frame,
        closed_artifacts=expected_artifacts, resource_ledger=ledger, resource_accepted=accepted,
        semantic_static_candidate=True, static_context_pool_resource_qualified=accepted,
        RL_full_pool_capacity=64, RL_full_pool_capacity_satisfied=projection['RL_full_pool_capacity_satisfied'],
        complete_group_count=compact['complete_group_count'], all_five_qualification=False,
        target_proof_accepted=False, trace_accepted=False, new_training=False, external_wait4_claim=False,
        OS_hard_cap_claim=False, whole_host_cap_claim=False, historical_donor_two_guards_UNKNOWN_preserved=True,
        finalization_scope='Additional post-terminal metadata-only cost; no dispatcher/PS/scientific calls or full audit/JSONL semantic replay. Trusted tool completion plus conditional known topology and source-reviewed reserve only.')
    data = (json.dumps(disposition, indent=2, allow_nan=False) + '\n').encode('utf8')
    need(len(data) <= MAX_METADATA, 'exclusive disposition stays in original one-MiB metadata bound')
    with output.open('xb') as stream:
        stream.write(data)
    return dict(disposition=pin(output), resource_accepted=accepted, all_five_qualification=False)


def main():
    need(len(sys.argv) == 3, 'pass the exact prior prospective contract and real saved terminal tool result')
    print(json.dumps(finalize(sys.argv[1], sys.argv[2]), allow_nan=False), flush=True)


if __name__ == '__main__':
    main()
