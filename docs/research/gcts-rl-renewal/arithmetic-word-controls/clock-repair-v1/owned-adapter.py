"""UNEXECUTED O01-O08 adapter factory for a genuine Root cold-owned context.

No coordinator.main, forged admission, local Q proof, search or supplied route.
Factory returns None unless the entire owned context is available; current
runner then retains all O8 as not_exercised. Native children/ledgers/EOF are real
when later Root-activated, never expected-only or caller-provided pass flags.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import time
import types

VERSION = 'Q-split-owned-neutral-controls-adapter-v4-global-clock'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
COORDINATOR_SHA = 'dafc392dc1463cac98d36dcb8e74d164cc2aa91cb04e64ac7b9f7f304c001fab'
FALSE_FLAGS = ('original_Q_theorem_accepted', 'selected_accepted', 'point_union_accepted',
               'full24_accepted', 'trajectory_accepted', 'ROOT_resource_accepted', 'RL_accepted')
FIELDS = {'owner', 'coordinator_module', 'runtime', 'run_directory', 'source_guard',
          'verifier_source', 'checker_source', 'authority', 'candidate', 'current_W01_observation',
          'profile_source', 'calibration_source', 'census_source', 'census_manifest',
          'codec_source', 'point_source', 'preparation', 'initial_state', 'initial_oracle'}

def need(value, message):
    if not value:
        raise ValueError(message)

def state(function):
    need(type(function) is types.FunctionType, 'exact declared Python endpoint')
    return (function, function.__code__, function.__defaults__, function.__kwdefaults__,
            tuple((cell, cell.cell_contents) for cell in function.__closure__ or ()))

def same(function, captured):
    return (function is captured[0] and function.__code__ is captured[1]
            and function.__defaults__ is captured[2] and function.__kwdefaults__ is captured[3]
            and len(function.__closure__ or ()) == len(captured[4])
            and all(cell is old and cell.cell_contents is value for cell, (old, value) in zip(function.__closure__ or (), captured[4])))

def make_owned_neutral_adapter(*, context, joint_began_ns, joint_deadline_ns):
    """Trusted factory API, not candidate-wire data. Requires caller full seals.

    Cold caller must authenticate/compile exact current coordinator and these
    Sources from the same buffers, seal all actual classes/MRO/properties and
    effective Owner endpoints, native stdlib globals/builtins and context pins
    before calling the factory. Passing a claimed hash/filename is insufficient.
    No q/preparation is parsed in this process or in the fresh verifier process.
    """
    if context is None or type(context) is not dict or set(context) != FIELDS:
        return None
    need(type(joint_began_ns) is int and type(joint_deadline_ns) is int
         and joint_deadline_ns - joint_began_ns == 20000000000, 'same exact original joint20')
    guard = context['source_guard']
    guard_anchor = state(guard)
    state_fn, state_anchor, same_fn, same_anchor = state, state(state), same, state(same)
    coordinator = context['coordinator_module']
    owner = context['owner']
    fixed_bindings = tuple((key, value) for key, value in context.items())
    need(type(time.CLOCK_MONOTONIC) is int and guard.__globals__.get('CLOCK_DOMAIN')==CLOCK_DOMAIN,'current global-clock cold guard, no mixed per-process epoch')
    clock_module, clock_id = time, time.CLOCK_MONOTONIC
    clock = time.clock_gettime_ns
    anchors = {}  # two constructor-owned registrations, complete before first guard
    def checked():
        if (state is not state_fn or state_fn.__code__ is not state_anchor[1]
                or same is not same_fn or same_fn.__code__ is not same_anchor[1]
                or time is not clock_module or time.clock_gettime_ns is not clock
                or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id
                or checked.__code__ is not anchors['checked'][1]
                or anchors['call'][0].__code__ is not anchors['call'][1]):
            raise ValueError('original factory validators/clock changed')
        if not same_fn(guard, guard_anchor):
            raise ValueError('actual original cold Source guard changed')
        guard()
        if (state is not state_fn or state_fn.__code__ is not state_anchor[1]
                or same is not same_fn or same_fn.__code__ is not same_anchor[1]
                or time is not clock_module or time.clock_gettime_ns is not clock
                or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id
                or checked.__code__ is not anchors['checked'][1]
                or anchors['call'][0].__code__ is not anchors['call'][1]):
            raise ValueError('original factory validators/clock changed after delegation')
        if not same_fn(guard, guard_anchor) or any(context[key] is not value for key, value in fixed_bindings):
            raise ValueError('actual Source guard/context binding changed')
        if type(coordinator) is not types.ModuleType or type(owner) is not coordinator.Owner:
            raise ValueError('exact current native Owner, no double/subclass')
        if owner.began_ns != joint_began_ns or owner.deadline_ns != joint_deadline_ns or clock(clock_id) >= joint_deadline_ns:
            raise TimeoutError('original suite interval cannot reset or finish late')
    checked_anchor = state(checked)
    anchors['checked'] = checked_anchor
    def call(function, *args, **keywords):
        if (state is not state_fn or state_fn.__code__ is not state_anchor[1]
                or state_fn.__defaults__ is not state_anchor[2] or state_fn.__kwdefaults__ is not state_anchor[3]
                or same is not same_fn or same_fn.__code__ is not same_anchor[1]
                or same_fn.__defaults__ is not same_anchor[2] or same_fn.__kwdefaults__ is not same_anchor[3]
                or checked.__code__ is not checked_anchor[1] or checked.__defaults__ is not checked_anchor[2]
                or checked.__kwdefaults__ is not checked_anchor[3]):
            raise ValueError('original immediate checked validators/code/defaults changed')
        if not same_fn(checked, checked_anchor):
            raise ValueError('actual checked factory callback changed before use')
        checked()
        fn = function.__func__ if type(function) is types.MethodType else function
        anchor = state_fn(fn)
        receiver = function.__self__ if type(function) is types.MethodType else None
        try:
            result = function(*args, **keywords)
        except BaseException:
            if (state is not state_fn or state_fn.__code__ is not state_anchor[1]
                    or same is not same_fn or same_fn.__code__ is not same_anchor[1]
                    or checked.__code__ is not checked_anchor[1]):
                raise ValueError('original validators changed during failed delegation')
            if not same_fn(checked, checked_anchor) or not same_fn(fn, anchor):
                raise ValueError('actual cold delegated endpoint changed during failure')
            checked()
            raise
        if (state is not state_fn or state_fn.__code__ is not state_anchor[1]
                or state_fn.__defaults__ is not state_anchor[2] or state_fn.__kwdefaults__ is not state_anchor[3]
                or same is not same_fn or same_fn.__code__ is not same_anchor[1]
                or same_fn.__defaults__ is not same_anchor[2] or same_fn.__kwdefaults__ is not same_anchor[3]
                or checked.__code__ is not checked_anchor[1] or checked.__defaults__ is not checked_anchor[2]
                or checked.__kwdefaults__ is not checked_anchor[3]):
            raise ValueError('original immediate checked validators/code/defaults changed')
        if not same_fn(checked, checked_anchor) or not same_fn(fn, anchor):
            raise ValueError('actual cold delegated endpoint changed during call')
        if receiver is not None and function.__self__ is not receiver:
            raise ValueError('effective delegated receiver changed')
        checked()
        return result
    call_anchor = state(call)
    anchors['call'] = call_anchor
    checked()
    actual_coordinator_raw = Path(coordinator.__file__).read_bytes()
    need(hashlib.sha256(actual_coordinator_raw).hexdigest() == COORDINATOR_SHA, 'whole actual cold-loaded coordinator Source')
    del actual_coordinator_raw
    need(coordinator.VERSION == 'Q-split-owned-original-model-coordinator-Source-v6-global-clock' and coordinator.CLOCK_DOMAIN == CLOCK_DOMAIN, 'current exact coordinator API')
    run = Path(context['run_directory'])
    need(run.is_absolute() and run == run.resolve() and run.is_dir() and not run.is_symlink(), 'Root-owned canonical controls directory')
    census = []
    child_records = []

    def directory(label):
        path = run / label
        need(not path.exists(), 'fresh exclusive per-case owned output')
        path.mkdir(mode=0o700)
        return path

    def launch(role, argv, fds, case_dir, *, expected_zero):
        child = call(owner.launch, role, argv, fds, case_dir)
        if expected_zero:
            terminal = call(owner.wait, child)
        else:
            while not call(owner.reap, child):
                call(owner.sample)
                time.sleep(.01)
            call(owner.sample)
            terminal = child['observed_terminal_ns']
        need(child['reaped'] is True and child['usage'] is not None and type(terminal) is int
             and terminal < joint_deadline_ns, 'actual native terminal/reaping in original interval')
        record = {'role': role, 'pid': child['process'].pid, 'exit_code': child['process'].returncode,
                  'observed_terminal_ns': terminal, 'kernel_peak_bytes': child['kernel_peak_bytes'], 'reaped': child['reaped']}
        child_records.append(record)
        return child, record

    def open_input(role):
        record = context[role]
        need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'}, 'complete Root closed record')
        return call(coordinator.regular_fd, record['path'], os.O_RDONLY)

    def run_verifier(label, *, alias=False, profiled=False):
        case_dir = directory(label)
        authority_fd, candidate_fd, checker_fd = [open_input(role) for role in ('authority', 'candidate', 'checker_source')]
        output_path = case_dir / 'verifier-response.jsonl'
        output_fd = call(coordinator.regular_fd, output_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        trace_path, trace_fd = case_dir / 'execution-profile.jsonl', None
        try:
            arguments = [str(authority_fd), context['authority']['sha256'], str(context['authority']['bytes']),
                         str(authority_fd if alias else candidate_fd), context['candidate']['sha256'], str(context['candidate']['bytes']),
                         str(checker_fd), str(output_fd), str(joint_began_ns), str(joint_deadline_ns)]
            fds = [authority_fd, candidate_fd, checker_fd, output_fd]
            if profiled:
                trace_fd = call(coordinator.regular_fd, trace_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
                argv = [context['runtime']['path'], '-I', '-S', '-B', context['profile_source']['path'],
                        context['verifier_source']['path'], context['verifier_source']['sha256'], str(context['verifier_source']['bytes']), str(trace_fd)] + arguments
                fds.append(trace_fd)
            else:
                argv = [context['runtime']['path'], '-I', '-S', '-B', context['verifier_source']['path']] + arguments
            child, record = launch('verifier', argv, fds, case_dir, expected_zero=not alias)
        finally:
            for fd in [authority_fd, candidate_fd, checker_fd, output_fd] + ([] if trace_fd is None else [trace_fd]):
                os.close(fd)
        return case_dir, record, trace_path

    def ensure_census_once():
        if census:
            return
        case_dir = directory('O07-whole-model-census')
        roles = ('census_manifest', 'preparation', 'codec_source', 'point_source', 'initial_state', 'initial_oracle')
        fds = [open_input(role) for role in roles]
        result_path = case_dir / 'census-response.jsonl'
        result_fd = call(coordinator.regular_fd, result_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        manifest = context['census_manifest']
        argv = [context['runtime']['path'], '-I', '-S', '-B', context['census_source']['path'],
                str(fds[0]), manifest['sha256'], str(manifest['bytes'])] + [str(fd) for fd in fds[1:]] + [str(result_fd), str(joint_began_ns), str(joint_deadline_ns)]
        try:
            child, record = launch('producer', argv, fds + [result_fd], case_dir, expected_zero=True)
        finally:
            for fd in fds + [result_fd]:
                os.close(fd)
        body, result_pin = call(coordinator.two_lines, result_path, 'Q-neutral-full-model-census-response-v1',
                                'Q-neutral-full-model-census-completion-v1', owner)
        need(not census, 'exact once-only O07 complete census')
        census.append((body, result_pin, record))

    def observation(case, predicate, evidence):
        result = {'schema': 'Q-split-neutral-surface-observation-v1', 'case_id': case['id'],
                  'surface': 'owned-model-role-deadline', 'completed': True, 'observed_predicate': predicate,
                  'expected_source': 'frozen-neutral-fixture', 'evidence': evidence}
        result.update({flag: False for flag in FALSE_FLAGS})
        return result

    def adapter(*, request, literal_expected, joint_began_ns, joint_deadline_ns, source_guard):
        if (state is not state_fn or state_fn.__code__ is not state_anchor[1]
                or same is not same_fn or same_fn.__code__ is not same_anchor[1]
                or call.__code__ is not call_anchor[1] or checked.__code__ is not checked_anchor[1]):
            raise ValueError('original adapter immediate validators/shim changed')
        if not same_fn(call, call_anchor) or not same_fn(checked, checked_anchor):
            raise ValueError('actual adapter delegation validators changed')
        checked()
        need(source_guard is not None and type(request) is dict and request['id'].startswith('O'), 'exact O8 request, no candidate callable')
        need(joint_began_ns == owner.began_ns and joint_deadline_ns == owner.deadline_ns, 'exact original current suite clock')
        code = request['id'].split('-')[0]
        evidence = {'primary_acceptance': False, 'original_inputs_modified': False}
        if code == 'O01':
            # All factories must already exist before this first child. The full
            # cold census is performed ONCE now, charged to current joint20, so
            # O05 later measures both producer and verifier lifetimes.
            ensure_census_once()
            case_dir, child, trace_path = run_verifier('O01-profiled-role-census', profiled=True)
            body, body_pin = call(coordinator.two_lines, case_dir / 'verifier-response.jsonl',
                                  'Q-clean-verifier-response-body-v1', 'Q-clean-verifier-response-completion-v1', owner)
            profile, profile_pin = call(coordinator.two_lines, trace_path,
                 'Q-control-verifier-execution-profile-body-v1', 'Q-control-verifier-execution-profile-completion-v1', owner)
            calls = profile['actual_calls']
            verifier_file = context['verifier_source']['path']
            own_file = context['profile_source']['path']
            checker_file = '<coordinator-authenticated-independent-Q-semantics>'
            actual_verifier = sum(row['count'] for row in calls if row['filename'] == verifier_file)
            actual_checker = sum(row['count'] for row in calls if row['filename'] == checker_file)
            foreign_calls = [row for row in calls if ('/.gcts-active/' in row['filename'] or '/geometric-tree-search/' in row['filename'])
                             and row['filename'] not in (verifier_file, own_file)]
            foreign_modules = [row for row in profile['modules_after_origins'] if type(row['origin']) is str
                 and ('/.gcts-active/' in row['origin'] or '/geometric-tree-search/' in row['origin'])
                 and row['origin'] not in (verifier_file, own_file)]
            predicate = actual_verifier > 0 and actual_checker > 0 and not foreign_calls and not foreign_modules
            need(body['status'] == 'WORD_REJECTED', 'role probe is rejected undeclared word, no Q proof')
            evidence.update({'control_only_profiler_role_added': True, 'actual_python_verifier_calls': actual_verifier,
                'actual_python_checker_calls': actual_checker, 'foreign_project_calls': foreign_calls, 'foreign_project_modules': foreign_modules,
                'whole_profile': profile, 'whole_profile_pin': profile_pin, 'whole_verifier_body': body,
                'whole_response_pin': body_pin, 'child': child, 'native_call_census_complete': False,
                'baseline_performance_evidence': False})
        elif code == 'O02':
            case_dir, child, _ = run_verifier('O02-real-FD-alias-rejection', alias=True)
            stderr = call(coordinator.read_small, case_dir / 'verifier-stderr.txt', 4 * 1048576)
            response = call(coordinator.read_small, case_dir / 'verifier-response.jsonl', 4 * 1048576)
            predicate = child['exit_code'] != 0 and not response and b'distinct' in stderr
            evidence.update({'child': child, 'actual_stdout_stderr_response_owned': True,
                'complete_stderr_hex': stderr.hex(), 'response_bytes': len(response), 'authority_fd_equals_candidate_fd': True})
        elif code == 'O03':
            need(type(context['current_W01_observation']) is list and len(context['current_W01_observation']) == 1, 'genuine once-only same-suite W01 observation required')
            actual = context['current_W01_observation'][0]['evidence']
            body = copy.deepcopy(actual['complete_verifier_body'])
            authority = json.loads(bytes.fromhex(actual['authority_sent_complete_raw_hex']))
            candidate = json.loads(bytes.fromhex(actual['candidate_complete_raw_hex']))
            # Exact original API first reconciles the real unaltered observation.
            original = call(coordinator.verifier_response, body, authority, actual['authority_sent_pin'], candidate, actual['candidate_actual_pin'], owner)
            need(original is False and body['status'] == 'WORD_REJECTED', 'real current baseline whole rejection')
            changed = copy.deepcopy(body)
            changed['joint_deadline_ns'] = body['joint_deadline_ns'] + 1
            rejected = False
            try:
                call(coordinator.verifier_response, changed, authority, actual['authority_sent_pin'], candidate, actual['candidate_actual_pin'], owner)
            except ValueError as error:
                if 'original exact ns deadline' not in str(error):
                    raise
                rejected = True
            predicate = rejected
            evidence.update({'real_original_body': body, 'literal_control_body': changed,
                             'only_original_interval_changed': True, 'actual_API_rejected': rejected,
                             'producer_or_verifier_output_replaced': False})
        elif code in ('O04', 'O06'):
            case_dir = directory(code + '-disposable-child')
            path = case_dir / 'disposable-result.jsonl'
            fd = call(coordinator.regular_fd, path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
            mode = 'callable-shadow' if code == 'O04' else 'partial-wire'
            argv = [context['runtime']['path'], '-I', '-S', '-B', context['calibration_source']['path'], mode, str(fd)]
            try:
                if code == 'O04':
                    child, record = launch('calibration', argv, [fd], case_dir, expected_zero=True)
                    result, result_pin = call(coordinator.two_lines, path, 'Q-disposable-callable-calibration-body-v1',
                                            'Q-disposable-callable-calibration-completion-v1', owner)
                    predicate = result['same_object_code_change_rejected'] is True and result['original_endpoint_restored'] is True and result['production_module_mutated'] is False
                    evidence.update({'child': record, 'whole_disposable_result': result, 'whole_result_pin': result_pin,
                                     'dedicated_toy_isolate_only': True, 'production_guard_weakened': False})
                else:
                    child = call(owner.launch, 'calibration', argv, [fd], case_dir)
                    while path.stat().st_size == 0:
                        checked()
                        call(owner.sample)
                        time.sleep(.01)
                    prefix = call(coordinator.read_small, path, 4 * 1048576)
                    need(prefix == b'{"disposable_partial_control":', 'actual disposable partial bytes observed')
                    os.killpg(child['process'].pid, signal.SIGKILL)
                    call(owner.reap, child, blocking=True)
                    call(owner.sample)
                    record = {'pid': child['process'].pid, 'exit_code': child['process'].returncode,
                              'reaped': child['reaped'], 'kernel_peak_bytes': child['kernel_peak_bytes']}
                    rejected = False
                    try:
                        call(coordinator.two_lines, path, 'Q-disposable-callable-calibration-body-v1',
                             'Q-disposable-callable-calibration-completion-v1', owner)
                    except ValueError as error:
                        if 'exact two complete JSON lines/EOF' not in str(error):
                            raise
                        rejected = True
                    table = call(owner.table)
                    active = call(owner.active, table, child)
                    predicate = rejected and child['reaped'] is True and child['usage'] is not None and not active
                    evidence.update({'actual_partial_hex': prefix.hex(), 'child': record, 'actual_complete_wire_rejected': rejected,
                                     'actual_remaining_owned_birth_rows': active, 'cancellation_reaped': child['reaped']})
            finally:
                os.close(fd)
        elif code == 'O05':
            call(owner.sample)
            bound = call(owner.memory_bound, require_complete=True)
            roles = {record['role'] for record in bound['intervals']}
            predicate = (bound['complete'] is True and {'producer', 'verifier'} <= roles
                         and bound['peak_bytes'] <= coordinator.LIMITS['aggregate_owned_bytes']
                         and owner.observer_peak > 0 and bool(owner.samples))
            evidence.update({'actual_complete_lifetime_bound': copy.deepcopy(bound),
                'actual_expanded_child_intervals': copy.deepcopy(bound['intervals']),
                'actual_overlap_witness_ns': bound['witness_ns'],
                'actual_overlap_witness_launch_indices': copy.deepcopy(bound['witness_launch_indices']),
                'actual_all_native_launch_records': copy.deepcopy(owner.launch_attempts),
                'actual_all_native_observer_records': copy.deepcopy(owner.observer_intervals),
                'all_child_peak_sum_bytes_diagnostic_only': owner.child_peak_sum,
                'actual_whole_samples': copy.deepcopy(owner.samples),
                'actual_child_records': copy.deepcopy(child_records),
                'not_single_child_or_all_sequential_sum_proxy': True,
                'Root_aggregate_acceptance': False})
        elif code == 'O07':
            ensure_census_once()
            body, result_pin, record = census[0]
            predicate = (body['row_count'] == 24 and len(body['all24_rows']) == 24
                         and body['preparation_decodes'] == body['preparation_parses'] == 1
                         and body['full_state_match']['complete_EOF'] is True and body['full_domains_match']['complete_EOF'] is True
                         and body['search_calls'] == body['placements'] == body['selected_facts'] == 0)
            evidence.update({'whole_original_census_body': body, 'whole_result_pin': result_pin, 'child': record,
                             'parent_or_verifier_preparation_decodes': 0,
                             'prepared_once_in_current_suite_before_O01': True})
        elif code == 'O08':
            need(len(census) == 1, 'real complete O07 census required, no fabricated view')
            body, result_pin, record = census[0]
            controls = body['O08_controls']
            predicate = (len(controls) == 2 and {row['label'] for row in controls} == {'omit-required-row23', 'omit-last-factor-row23'}
                         and all(row['actual_rejected'] is True and row['original_output_preserved'] is True for row in controls))
            evidence.update({'actual_complete_census_result_pin': result_pin, 'whole_actual_omission_controls': controls,
                             'original_full_state_match': body['full_state_match'], 'original_full_domains_match': body['full_domains_match'],
                             'control_views_are_not_current_model': True})
        else:
            raise ValueError('undeclared owned case')
        if (state is not state_fn or state_fn.__code__ is not state_anchor[1]
                or same is not same_fn or same_fn.__code__ is not same_anchor[1]
                or call.__code__ is not call_anchor[1] or checked.__code__ is not checked_anchor[1]):
            raise ValueError('original adapter immediate validators/shim changed')
        if not same_fn(call, call_anchor) or not same_fn(checked, checked_anchor):
            raise ValueError('actual adapter delegated validator changed before final scope')
        checked()
        return observation(request, predicate, evidence)
    return adapter
