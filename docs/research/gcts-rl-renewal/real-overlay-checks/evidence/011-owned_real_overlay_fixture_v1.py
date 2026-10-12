"""Prospective one-shot ROOT owner; no engine imports in this supervisor.

Reuses exact pinned non-scientific Streams/ps/wait4 cleanup helpers. Every
observer and the single direct fixture worker is reaped by this owner. No retry.
ROOT must additionally qualify the full outer lifetime including this receipt.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time


def encoded(value):
    return json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n'


def write_new(path, value):
    with path.open('x') as stream: stream.write(encoded(value))


def verify(pin, root):
    path = Path(pin['path']); path = path if path.is_absolute() else root / path
    raw = path.read_bytes()
    if len(raw) != pin['bytes'] or hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise ValueError('exact source/runtime/input changed: ' + pin['path'])
    return path


def main():
    begin = time.monotonic()
    root = Path(__file__).resolve().parents[2]
    plan_path = Path(sys.argv[1]).resolve(); plan = json.loads(plan_path.read_text())
    plan_pin = dict(path=str(plan_path.relative_to(root)),
        sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(), bytes=plan_path.stat().st_size)
    activation_path = root / plan['activation_path']
    activation = json.loads(activation_path.read_text())
    if (activation.get('schema') != 'ROOT-real-Controller-overlay-fixture-activation-v1'
            or activation.get('authorized') is not True or activation.get('plan') != plan_pin):
        raise ValueError('separate exact ROOT activation required')
    for pin in plan['sources'] + plan['inputs'] + plan['preserved']: verify(pin, root)
    runtime = plan['runtime']; verify(runtime['binary'], root); verify(runtime['observer'], root)
    if (Path(sys.executable).resolve() != Path(runtime['binary']['path']).resolve()
            or Path(runtime['executable']).resolve() != Path(runtime['binary']['path']).resolve()
            or sys.version_info[:2] != (3, 9) or sys.platform != 'darwin'):
        raise ValueError('declared actual macOS Python3.9 runtime required')
    roles = {p['role']:p for p in plan['inputs'] if 'role' in p}
    helper_path = verify(roles['owned_helpers'], root)
    spec = importlib.util.spec_from_file_location('real_overlay_fixture_owned_helpers', helper_path)
    helpers = importlib.util.module_from_spec(spec); spec.loader.exec_module(helpers)
    output = root / plan['outputs']['directory']
    if output.exists(): raise ValueError('existing output: no retry/restart/overwrite')
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / 'activation-copy.json', activation)
    child = None; outcome = None; streams = None; child_start = None
    observers = []; samples = []; identities = {}; failure = None; killed = False
    open_streams = False; final_leftovers = None; result_pin = None; result = None
    def alarm(*_): raise TimeoutError('owned fixture phase cancellation/deadline')
    signal.signal(signal.SIGALRM, alarm); signal.signal(signal.SIGTERM, alarm)
    signal.setitimer(signal.ITIMER_REAL, max(0.001,
        plan['limits']['supervisor_seconds']-(time.monotonic()-begin)))
    def observe():
        if len(observers) >= plan['limits']['maximum_observers']:
            raise RuntimeError('observer count ceiling')
        rows, receipt = helpers.processes(output, len(observers),
            plan['limits']['observer_seconds'], plan['limits']['observer_stream_bytes'])
        observers.append(receipt)
        if rows is None: raise RuntimeError('owned process observation failed')
        return rows
    try:
        observe()
        if time.monotonic()-begin+plan['limits']['child_seconds'] > plan['limits']['supervisor_seconds']:
            raise TimeoutError('full child reservation unavailable; scientific worker unexecuted')
        command = [runtime['executable'], '-B', str(root / plan['worker_path']), str(plan_path)]
        child_start = time.monotonic()
        child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 start_new_session=True)
        streams = helpers.Streams(child, output, 'worker', plan['limits']['worker_stream_bytes'])
        write_new(output/'worker-owner.json', dict(pid=child.pid, parent_pid=os.getpid(),
            command=command, plan=plan_pin, activation_sha256=hashlib.sha256(activation_path.read_bytes()).hexdigest()))
        while outcome is None:
            streams.drain(0.005); outcome = helpers.wait_nonblocking(child)
            if outcome is not None: break
            if streams.exceeded: raise RuntimeError('worker stream limit')
            if time.monotonic()-begin > plan['limits']['supervisor_seconds']:
                raise TimeoutError('owned full supervisor lifetime')
            rows = observe(); worker_rows = helpers.descendants(rows, child.pid)
            for row in worker_rows: identities[row[0]] = row[4]
            if any(row[0] != child.pid for row in worker_rows):
                raise RuntimeError('unexpected scientific worker descendant')
            owned_rows = helpers.descendants(rows, os.getpid())
            rss = sum(row[3]*1024 for row in owned_rows)
            samples.append(dict(seconds=time.monotonic()-begin, aggregate_rss_bytes=rss,
                                worker_pids=[row[0] for row in worker_rows]))
            if rss > plan['limits']['memory_bytes']: raise MemoryError('sampled aggregate RSS gate')
            if any(p.is_file() and p.stat().st_size > plan['limits']['artifact_bytes'] for p in output.glob('*')):
                raise RuntimeError('fixture artifact size gate')
            time.sleep(0.025)
    except BaseException as exc:
        failure = type(exc).__name__+': '+str(exc)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        if child is not None and outcome is None:
            outcome, killed = helpers.stop_unreaped(child, streams)
        if streams is not None: open_streams = streams.finish()
        child_seconds = time.monotonic()-child_start if child_start is not None else None
        try:
            rows = observe()
            final_leftovers = [row[0] for row in rows if row[0] != (child.pid if child else None)
                               and identities.get(row[0]) == row[4]]
            if final_leftovers:
                # Fixture worker is forbidden to create subprocesses. Any
                # observed descendant means UNKNOWN. Only birth-matched PIDs
                # may be cleaned; never signal the reaped leader's old PGID.
                for row in rows:
                    if row[0] in final_leftovers and identities.get(row[0]) == row[4]:
                        try: os.kill(row[0], signal.SIGKILL)
                        except ProcessLookupError: pass
                failure = failure or 'unexpected owned descendant cleanup'
                rows = observe()
                final_leftovers = [row[0] for row in rows if identities.get(row[0]) == row[4]]
        except BaseException as exc:
            failure = (failure or '')+'; final observer: '+type(exc).__name__+': '+str(exc)
        target = root / plan['outputs']['result']
        if target.exists():
            try:
                if target.stat().st_size > plan['limits']['artifact_bytes']: raise ValueError('result size ceiling')
                raw = target.read_bytes(); result = json.loads(raw)
                result_pin = dict(path=str(target.relative_to(root)), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            except BaseException as exc:
                failure = (failure or '')+'; result: '+type(exc).__name__+': '+str(exc)
    own_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    worker_peak = outcome[1].ru_maxrss if outcome else 0
    observer_peak = max((r['kernel_peak_bytes'] for r in observers), default=0)
    combined = own_peak + worker_peak + observer_peak
    before_write = time.monotonic()-begin
    resources = (failure is None and outcome is not None and outcome[0] == 0 and not killed
        and not open_streams and streams is not None and not streams.exceeded
        and final_leftovers == [] and child_seconds <= plan['limits']['child_seconds']
        and before_write <= plan['limits']['supervisor_seconds'] and combined <= plan['limits']['memory_bytes'])
    data_ok = (isinstance(result, dict)
        and result.get('status') == 'completed_producer_fixture_assertions_pending_independent_replay'
        and [s.get('id') for s in result.get('scenarios',[])] == plan['expected_scenario_ids']
        and all(s.get('producer_assertions_passed') is True for s in result.get('scenarios',[]))
        and result.get('independent_acceptance') is False and result.get('actual_RNG_draws') == 0
        and result.get('training_updates') == 0 and result.get('actual_Hilbert_models') == 0)
    receipt = dict(schema='owned-real-Controller-overlay-fixture-lifetime-v1',
        status='completed_owned_producer_fixture_pending_ROOT_clock_and_independent_replay' if resources and data_ok else 'UNKNOWN_or_failed_fixture',
        plan=plan_pin, worker_created=child is not None, worker_pid=child.pid if child else None,
        worker_terminal_reaped=outcome is not None, worker_exit_code=outcome[0] if outcome else None,
        child_lifetime_including_imports_serialization_and_reaping_seconds=child_seconds,
        supervisor_seconds_before_final_receipt=before_write,
        kernel_owner_peak_bytes=own_peak, kernel_worker_peak_bytes=worker_peak,
        kernel_observer_max_peak_bytes=observer_peak, conservative_combined_peak_bytes=combined,
        sampled_aggregate_peak_bytes=max((s['aggregate_rss_bytes'] for s in samples),default=0),
        memory_scope='Sum of macOS kernel peaks including observer; sampled owned RSS; measurement, not hard OS cap',
        final_receipt_scope='ROOT separately measures full owner exit/reap and final serialization; required for qualification',
        resource_gate_before_final_receipt=resources, producer_data_gate=data_ok,
        failure=failure, forced_kill=killed, streams_open_after_reap=open_streams,
        remaining_owned_pids=final_leftovers, result=result_pin,
        observer_receipts=observers, resource_samples=samples,
        independent_acceptance=False, full_ROOT_outer_clock_qualified=False)
    write_new(root / plan['outputs']['lifetime'], receipt)
    print(encoded({k:v for k,v in receipt.items() if k not in ('observer_receipts','resource_samples')}), flush=True)
    return 0 if resources and data_ok else 2


if __name__ == '__main__': raise SystemExit(main())
