"""One ROOT-activated numeric worker, owned/reaped here; no scientific imports.

The only functional child is the frozen V1 numeric runner. Bounded /bin/ps
observers are additional accounting children, each separately reaped here.
No retry, historical process-group kill, or existing-output overwrite.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import selectors
import signal
import subprocess
import sys
import time


def pin(path):
    data = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def write_new(path, value):
    with Path(path).open('x', encoding='utf-8') as output:
        json.dump(value, output, ensure_ascii=False, allow_nan=False, indent=2)
        output.write('\n')


class Streams:
    def __init__(self, child, output, prefix, ceiling):
        self.selector = selectors.DefaultSelector()
        self.files = {}; self.counts = {}; self.ceiling = ceiling
        self.exceeded = False
        self.finish_errors = []
        try:
            for name, pipe in (('stdout', child.stdout), ('stderr', child.stderr)):
                os.set_blocking(pipe.fileno(), False)
                self.selector.register(pipe, selectors.EVENT_READ, name)
                self.files[name] = (output / (prefix + '-' + name + '.bin')).open('xb')
                self.counts[name] = {'read_bytes': 0, 'retained_bytes': 0}
        except BaseException:
            for key in list(self.selector.get_map().values()):
                self.selector.unregister(key.fileobj)
            self.selector.close()
            for saved in self.files.values():
                saved.close()
            for pipe in (child.stdout, child.stderr):
                if pipe is not None and not pipe.closed:
                    pipe.close()
            raise

    def drain(self, timeout=0.0):
        for key, _ in self.selector.select(timeout):
            chunk = os.read(key.fileobj.fileno(), 65536)
            if not chunk:
                self.selector.unregister(key.fileobj)
                key.fileobj.close()
                continue
            item = self.counts[key.data]
            item['read_bytes'] += len(chunk)
            available = max(0, self.ceiling - item['retained_bytes'])
            keep = chunk[:available]
            self.files[key.data].write(keep)
            item['retained_bytes'] += len(keep)
            if len(keep) != len(chunk):
                self.exceeded = True

    def finish(self):
        # Worker is already terminal/reaped; drain bounded available bytes.
        deadline = time.monotonic() + 0.25
        try:
            while self.selector.get_map() and time.monotonic() < deadline:
                self.drain(0.01)
        except BaseException as exception:
            self.finish_errors.append(type(exception).__name__ + ': ' + str(exception))
        open_streams = bool(self.selector.get_map())
        for key in list(self.selector.get_map().values()):
            try:
                self.selector.unregister(key.fileobj); key.fileobj.close()
            except BaseException as exception:
                self.finish_errors.append(type(exception).__name__ + ': ' + str(exception))
        self.selector.close()
        for output in self.files.values():
            try:
                output.close()
            except BaseException as exception:
                self.finish_errors.append(type(exception).__name__ + ': ' + str(exception))
        return open_streams or bool(self.finish_errors)


def wait_nonblocking(child):
    waited, status, usage = os.wait4(child.pid, os.WNOHANG)
    if not waited:
        return None
    code = os.waitstatus_to_exitcode(status)
    child.returncode = code  # Popen must not reap a second time.
    return code, usage


def stop_unreaped(child, streams):
    """Only this still-owned unreaped child's current session may be signaled."""
    child.owned_cleanup_errors = []
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + 0.25
    while time.monotonic() < deadline:
        outcome = wait_nonblocking(child)
        if outcome is not None:
            return outcome, False
        if streams is not None:
            try:
                streams.drain(0.01)
            except BaseException as exception:
                child.owned_cleanup_errors.append(type(exception).__name__ + ': ' + str(exception))
                streams = None  # Broken I/O must not interrupt kill/wait4.
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    _, status, usage = os.wait4(child.pid, 0)
    code = os.waitstatus_to_exitcode(status); child.returncode = code
    return (code, usage), True


def processes(output, index, limit_seconds, stream_ceiling):
    """Bounded observer command, exact same PID wait4 and retained streams."""
    begin = time.monotonic()
    command = ['/bin/ps', '-axo', 'pid=,ppid=,pgid=,rss=,lstart=']
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True)
    streams = None
    outcome = None; error = None; hard_kill = False
    try:
        streams = Streams(child, output, 'ps-%04d' % index, stream_ceiling)
        while outcome is None:
            streams.drain(0.005)
            outcome = wait_nonblocking(child)
            if outcome is not None:
                break
            if streams.exceeded:
                raise RuntimeError('observer stream ceiling exceeded')
            if time.monotonic() - begin > limit_seconds:
                raise TimeoutError('observer command timeout')
    except BaseException as exception:
        error = type(exception).__name__ + ': ' + str(exception)
    finally:
        if outcome is None:
            outcome, hard_kill = stop_unreaped(child, streams)
        open_streams = streams.finish() if streams is not None else False
    code, usage = outcome
    metadata = {'pid': child.pid, 'exit_code': code, 'terminal_and_reaped': True,
                'seconds': time.monotonic() - begin, 'kernel_peak_bytes': usage.ru_maxrss,
                'streams': streams.counts if streams is not None else None,
                'stream_ceiling_exceeded': streams.exceeded if streams is not None else False,
                'streams_still_open_after_reap': open_streams,
                'stream_finish_errors': streams.finish_errors if streams else [],
                'cleanup_errors': getattr(child, 'owned_cleanup_errors', []),
                'forced_kill': hard_kill, 'error': error}
    if error or code != 0 or hard_kill or (streams and streams.exceeded) or open_streams:
        return None, metadata
    rows = []
    try:
        text = (output / ('ps-%04d-stdout.bin' % index)).read_text(encoding='utf-8')
        for line in text.splitlines():
            fields = line.split(None, 4)
            if len(fields) != 5:
                raise ValueError('unexpected ps record')
            rows.append((*map(int, fields[:4]), fields[4]))
    except BaseException as exception:
        metadata['error'] = 'parse: ' + type(exception).__name__ + ': ' + str(exception)
        return None, metadata
    return rows, metadata


def descendants(rows, leader):
    owned = {leader}
    while True:
        expanded = owned | {row[0] for row in rows if row[1] in owned}
        if expanded == owned:
            return [row for row in rows if row[0] in owned]
        owned = expanded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True)
    parser.add_argument('--activation', required=True)
    args = parser.parse_args()
    begin = time.monotonic()
    plan_pin = pin(args.plan); activation_pin = pin(args.activation)
    plan = json.loads(Path(args.plan).read_text())
    activation = json.loads(Path(args.activation).read_text())
    if activation.get('scope') != 'root_authorized_owned_numeric_fixture_only':
        raise ValueError('ROOT owned numeric-only activation required')
    if activation.get('plan') != plan_pin or activation.get('source_pins') != plan['sources']:
        raise ValueError('exact owner plan/source activation required')
    if activation.get('runtime') != plan['runtime']:
        raise ValueError('exact runtime activation required')
    for record in plan['sources'] + plan['inputs']:
        if pin(record['path']) != record:
            raise ValueError('frozen pin mismatch: ' + record['path'])
    runtime = plan['runtime']
    if pin(runtime['alias_pin']['path']) != runtime['alias_pin']:
        raise ValueError('runtime alias bytes mismatch')
    if str(Path(runtime['alias_pin']['path']).resolve()) != runtime['resolved_pin']['path']:
        raise ValueError('runtime alias target mismatch')
    if pin(runtime['resolved_pin']['path']) != runtime['resolved_pin']:
        raise ValueError('resolved runtime bytes mismatch')
    if pin(runtime['observer_pin']['path']) != runtime['observer_pin']:
        raise ValueError('process observer bytes mismatch')
    if str(Path(sys.executable).resolve()) != runtime['resolved_pin']['path']:
        raise ValueError('owner must use the declared runtime too')
    if sys.version_info[:2] != (3, 9) or sys.platform != 'darwin':
        raise ValueError('declared macOS Python3.9 kernel accounting required')
    output = Path(plan['owned_output'])
    numeric_output = Path(plan['numeric_output'])
    if numeric_output.exists():
        raise ValueError('numeric output already exists; no restart/retry')
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / 'activation-copy.json', activation)
    child = None; streams = None; outcome = None; child_started = None
    launch_attempted = False
    observers = []; samples = []; identities = {}; violation = None
    error = None; hard_kill = False; open_streams = False
    leftovers = None; cleaned = []; inner = None; inner_pin = None

    def alarm(signum, frame):
        raise TimeoutError('owner phase budget or external cancellation')

    signal.signal(signal.SIGALRM, alarm)
    signal.signal(signal.SIGTERM, alarm)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, plan['limits']['whole_phase_seconds'] -
                                            (time.monotonic() - begin)))

    def observe():
        if len(observers) >= plan['limits']['maximum_observer_commands']:
            raise RuntimeError('bounded observer count ceiling exceeded')
        rows, metadata = processes(output, len(observers),
                                   plan['limits']['observer_seconds'],
                                   plan['limits']['observer_stream_bytes'])
        observers.append(metadata)
        if rows is None:
            raise RuntimeError('bounded process observer failed')
        return rows

    try:
        observe()  # Capability check BEFORE functional worker creation.
        if time.monotonic() - begin + plan['limits']['owned_seconds'] > plan['limits']['whole_phase_seconds']:
            violation = 'unknown_phase_reservation_budget'
        else:
            worker_plan = json.loads(Path(plan['worker_plan']['path']).read_text())
            worker_activation = {'scope': 'root_authorized_numeric_fixture_only',
                                 'plan': plan['worker_plan'],
                                 'source_pins': worker_plan['sources'],
                                 'runtime_pin': runtime['alias_pin'],
                                 'parent_activation': activation_pin}
            activation_path = output / 'worker-activation.json'
            write_new(activation_path, worker_activation)
            command = [runtime['alias_pin']['path'], '-B', plan['worker'],
                       '--plan', plan['worker_plan']['path'], '--activation', str(activation_path),
                       '--output', plan['numeric_output']]
            child_started = time.monotonic()
            launch_attempted = True
            child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     start_new_session=True)
            streams = Streams(child, output, 'worker', plan['limits']['worker_stream_bytes'])
            write_new(output / 'worker-owner.json', {'pid': child.pid, 'command': command,
                                                      'plan': plan_pin, 'activation': activation_pin})
            while outcome is None:
                streams.drain(0.005)
                outcome = wait_nonblocking(child)
                if outcome is not None:
                    break
                elapsed = time.monotonic() - child_started
                if elapsed > plan['limits']['owned_seconds']:
                    violation = 'unknown_owned_lifetime_budget'; break
                if streams.exceeded:
                    violation = 'unknown_worker_stream_budget'; break
                rows = observe()
                owned_rows = descendants(rows, os.getpid())
                worker_rows = descendants(rows, child.pid)
                for row in worker_rows:
                    identities[row[0]] = row[4]
                rss = sum(row[3] * 1024 for row in owned_rows)
                samples.append({'seconds': time.monotonic() - begin, 'aggregate_rss_bytes': rss,
                                'worker_pids': [row[0] for row in worker_rows]})
                if any(row[0] != child.pid for row in worker_rows):
                    violation = 'unknown_unexpected_worker_descendant'; break
                if rss > plan['limits']['memory_bytes']:
                    violation = 'unknown_sampled_memory_budget'; break
                if any(p.is_file() and p.stat().st_size > plan['limits']['artifact_bytes']
                       for p in numeric_output.glob('*')):
                    violation = 'unknown_numeric_artifact_budget'; break
                time.sleep(0.05)
    except BaseException as exception:
        error = type(exception).__name__ + ': ' + str(exception)
        violation = violation or 'unknown_owner_observation_or_control_failure'
    finally:
        # Disable the phase alarm only for bounded cleanup of the one still-owned
        # child. Actual cleanup/overshoot is charged, never credited as passed.
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        if child is not None and outcome is None:
            outcome, hard_kill = stop_unreaped(child, streams)
        if streams is not None:
            open_streams = streams.finish()
        child_lifetime = (time.monotonic() - child_started) if child_started is not None else None
        try:
            rows = observe()
            leftovers = [row[0] for row in rows if row[0] != (child.pid if child else None)
                         and identities.get(row[0]) == row[4]]
            if leftovers:
                # Leader is reaped: never grow from/re-signal its historical PID
                # or process group. Only saved PID plus birth-matched victims.
                for row in rows:
                    if row[0] in leftovers and identities.get(row[0]) == row[4]:
                        try:
                            os.kill(row[0], signal.SIGKILL); cleaned.append(row[0])
                        except ProcessLookupError:
                            pass
                rows = observe()
                leftovers = [row[0] for row in rows if identities.get(row[0]) == row[4]]
                violation = violation or 'unknown_supervisor_orphan_cleanup'
        except BaseException as exception:
            error = (error or '') + '; final observer: ' + type(exception).__name__ + ': ' + str(exception)
            violation = violation or 'unknown_final_observation_failure'
        result_path = numeric_output / 'result.json'
        try:
            if result_path.exists():
                if result_path.stat().st_size > plan['limits']['artifact_bytes']:
                    violation = violation or 'unknown_numeric_artifact_budget'
                else:
                    inner_pin = pin(result_path)
                    inner = json.loads(result_path.read_text())
        except BaseException as exception:
            error = (error or '') + '; worker result: ' + type(exception).__name__ + ': ' + str(exception)
            violation = violation or 'unknown_malformed_worker_result'

    own_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    observer_peak = max((o['kernel_peak_bytes'] for o in observers), default=0)
    worker_peak = outcome[1].ru_maxrss if outcome is not None else 0
    conservative = own_peak + observer_peak + worker_peak
    total_seconds = time.monotonic() - begin
    controls = inner.get('controls', []) if isinstance(inner, dict) else []
    ids = [control.get('id') for control in controls if isinstance(control, dict)]
    controls_ok = (ids == plan['expected_control_ids'] and
                   all(control.get('status') == 'passed' for control in controls))
    inner_ok = (isinstance(inner, dict) and inner.get('status') == 'passed_numeric_and_abstract_API_controls_only'
                and inner.get('numeric_fixture_worker_runs') == 1
                and inner.get('policy_numeric_functions_executed') is True
                and inner.get('production_engine_runs') == 0 and inner.get('search_runs') == 0
                and inner.get('training_runs') == 0 and inner.get('random_draws_generated') == 0
                and inner.get('runtime_adapter_implemented') is False and controls_ok)
    resource_ok = (violation is None and error is None and child is not None and outcome is not None
                   and outcome[0] == 0 and not hard_kill and not open_streams and leftovers == []
                   and not cleaned and not streams.exceeded
                   and child_lifetime <= plan['limits']['owned_seconds']
                   and total_seconds <= plan['limits']['whole_phase_seconds']
                   and conservative <= plan['limits']['memory_bytes'])
    receipt = {'status': ('passed_owned_numeric_and_abstract_API_controls_only' if resource_ok and inner_ok
                          else 'unknown_or_failed_owned_numeric_gate'),
               'plan': plan_pin, 'activation': activation_pin, 'runtime': runtime,
               'worker_attempted': launch_attempted, 'unexecuted': not launch_attempted,
               'functional_worker_created': child is not None,
               'worker_pid': child.pid if child else None,
               'worker_terminal_and_reaped_same_PID': outcome is not None,
               'worker_exit_code': outcome[0] if outcome else None,
               'worker_lifetime_seconds_including_imports_output_and_reaping': child_lifetime,
               'whole_phase_seconds_before_final_receipt': total_seconds,
               'owned_overshoot_seconds': max(0.0, (child_lifetime or 0.0) - plan['limits']['owned_seconds']),
               'phase_overshoot_seconds': max(0.0, total_seconds - plan['limits']['whole_phase_seconds']),
               'kernel_owner_peak_bytes': own_peak, 'kernel_worker_peak_bytes': worker_peak,
               'kernel_observer_maximum_peak_bytes': observer_peak,
               'conservative_combined_peak_bytes': conservative,
               'sampled_combined_peak_bytes': max((s['aggregate_rss_bytes'] for s in samples), default=0),
               'memory_overshoot_bytes': max(0, conservative - plan['limits']['memory_bytes']),
               'violation': violation, 'error': error, 'forced_kill': hard_kill,
               'streams_still_open_after_reap': open_streams,
               'streams': streams.counts if streams else None,
               'stream_finish_errors': streams.finish_errors if streams else [],
               'worker_cleanup_errors': getattr(child, 'owned_cleanup_errors', []) if child else [],
               'remaining_owned_pids': leftovers, 'cleaned_verified_orphan_pids': cleaned,
               'worker_result': inner_pin, 'worker_status': inner.get('status') if isinstance(inner, dict) else None,
               'ordered_control_ids_match': controls_ok,
               'resource_gate_passed': resource_ok, 'numeric_and_abstract_contract_gate_passed': inner_ok,
               'observer_receipts': observers, 'resource_samples': samples,
               'numeric_fixture_worker_runs': 1 if child is not None else 0,
               'policy_numeric_functions_executed': (inner.get('policy_numeric_functions_executed')
                                                      if isinstance(inner, dict) else None),
               'production_engine_runs': 0, 'search_runs': 0, 'training_runs': 0,
               'scope': plan['scope'],
               'memory_scope': 'macOS byte-valued kernel peaks summed conservatively; bounded /bin/ps RSS includes owner/functional worker/current descendants/observer. No hard OS memory limit claimed.',
               'final_receipt_write_scope': 'Final owner receipt serialization is outside reported whole-phase timer; worker receipt serialization and cleanup are included.'}
    write_new(output / 'owned-lifetime.json', receipt)
    print(json.dumps({key: value for key, value in receipt.items()
                      if key not in ('observer_receipts', 'resource_samples')}, ensure_ascii=False), flush=True)
    return 0 if resource_ok and inner_ok else 2


if __name__ == '__main__':
    raise SystemExit(main())
