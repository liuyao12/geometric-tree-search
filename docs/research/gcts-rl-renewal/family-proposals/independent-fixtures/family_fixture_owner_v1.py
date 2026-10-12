"""ROOT-owned prospective pure fixture lifetime supervisor, exclusive outputs.

No graph/producer/controller/model/scientific imports. ROOT must create exact
fixture-activation-v1.json and dispatch this owner once after source review.
Owned PID metadata needs permitted /bin/ps; missing metadata is UNKNOWN and the
child is killed/wait-reaped. No retry or cap adjustment is performed here.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time


def pin(path):
    data = Path(path).read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


def own_peak():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == 'darwin' else value * 1024


def child_peak(usage):
    return usage.ru_maxrss if sys.platform == 'darwin' else usage.ru_maxrss * 1024


def metadata(pid):
    result = subprocess.run(['/bin/ps', '-o', 'rss=', '-p', str(pid)], capture_output=True,
                            text=True, timeout=1, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError('owned process RSS unavailable: ' + str(pid))
    monitored_peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    monitored_peak = monitored_peak if sys.platform == 'darwin' else monitored_peak * 1024
    return int(result.stdout.strip()) * 1024, monitored_peak


def main():
    started = time.monotonic()
    plan_path = Path(sys.argv[1]).resolve()
    plan = json.loads(plan_path.read_text())
    output = Path(plan['outputs']['lifetime'])
    if any(Path(plan['outputs'][k]).exists() for k in ('lifetime', 'result', 'stdout', 'stderr')):
        raise RuntimeError('exclusive outputs already exist; no rerun')
    receipt = dict(status='unknown_before_fixture_launch', plan=pin(plan_path), child_pid=None,
                   child_exit=None, child_reaped=False, stdout=None, stderr=None, result=None,
                   sampled_combined_peak_bytes=0, kernel_conservative_peak_bytes=0, metadata_child_peak_bytes=0,
                   max_whole_seconds=plan['limits']['whole_seconds'], max_peak_bytes=plan['limits']['peak_bytes'],
                   execution_scope='pure synthetic source projection/port/interface/embedding/aggregate controls only',
                   native_queries=0, actual_model_loads=0, engine_or_scheduler_runs=0)
    child, usage, waited = None, None, False
    try:
        for item in plan['sources'] + plan['inputs'] + plan['preserved']:
            if pin(item['path']) != item:
                raise ValueError('exact frozen input/source pin mismatch: ' + item['path'])
        if plan['runtime']['executable'] != sys.executable or plan['runtime']['platform'] != sys.platform or pin(sys.executable) != plan['runtime']['binary']:
            raise ValueError('exact Python runtime binary')
        activation_path = Path(plan['activation_path'])
        activation = json.loads(activation_path.read_text())
        if activation.get('schema') != 'root-pure-family-fixture-activation-v1' or activation.get('authorized') is not True or activation.get('plan_sha256') != receipt['plan']['sha256']:
            raise ValueError('exact ROOT-only fixture activation required')
        receipt['activation'] = pin(activation_path)
        with Path(plan['outputs']['stdout']).open('xb') as stdout, Path(plan['outputs']['stderr']).open('xb') as stderr:
            child = subprocess.Popen([sys.executable, plan['worker_path'], str(plan_path)],
                stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            receipt['child_pid'] = child.pid
            deadline = started + plan['limits']['supervisor_seconds']
            while True:
                pid, status, current_usage = os.wait4(child.pid, os.WNOHANG)
                if pid:
                    waited = True; usage = current_usage
                    receipt['child_exit'] = os.waitstatus_to_exitcode(status)
                    child.returncode = receipt['child_exit']
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError('owned whole fixture deadline')
                try:
                    child_rss, monitor_a = metadata(child.pid)
                    owner_rss, monitor_b = metadata(os.getpid())
                    receipt['metadata_child_peak_bytes'] = max(receipt['metadata_child_peak_bytes'], monitor_a, monitor_b)
                    rss = child_rss + owner_rss + receipt['metadata_child_peak_bytes']
                except RuntimeError:
                    # A fast, already terminated child is legitimately absent
                    # from ps. Reap it and use wait4's complete kernel peak.
                    pid, status, current_usage = os.wait4(child.pid, os.WNOHANG)
                    if pid:
                        waited = True; usage = current_usage
                        receipt['child_exit'] = os.waitstatus_to_exitcode(status)
                        child.returncode = receipt['child_exit']
                        break
                    raise
                receipt['sampled_combined_peak_bytes'] = max(receipt['sampled_combined_peak_bytes'], rss)
                if rss > plan['limits']['peak_bytes']:
                    raise MemoryError('owned sampled RSS ceiling')
                time.sleep(0.02)
        receipt['child_reaped'] = True
        receipt['kernel_conservative_peak_bytes'] = child_peak(usage) + own_peak() + receipt['metadata_child_peak_bytes']
        if receipt['child_exit'] != 0:
            receipt['status'] = 'unknown_fixture_child_failure'
        elif max(receipt['kernel_conservative_peak_bytes'], receipt['sampled_combined_peak_bytes']) > plan['limits']['peak_bytes']:
            receipt['status'] = 'unknown_fixture_memory_budget'
        elif not Path(plan['outputs']['result']).is_file():
            receipt['status'] = 'unknown_missing_fixture_result'
        else:
            result = json.loads(Path(plan['outputs']['result']).read_text())
            receipt['status'] = 'passed_owned_pure_family_fixtures' if result['status'] == 'passed_pure_synthetic_family_binding_controls' else 'unknown_fixture_result'
    except BaseException as exc:
        receipt['status'] = 'unknown_fixture_infrastructure_or_resource'
        receipt['failure'] = dict(type=type(exc).__name__, reason=str(exc))
    finally:
        if child is not None and not waited:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _, status, usage = os.wait4(child.pid, 0)
            child.returncode = os.waitstatus_to_exitcode(status)
            receipt['child_exit'] = child.returncode
            receipt['child_reaped'] = True
            receipt['kernel_conservative_peak_bytes'] = child_peak(usage) + own_peak() + receipt['metadata_child_peak_bytes']
        receipt['owner_seconds_before_final_receipt_write'] = time.monotonic() - started
        if receipt['owner_seconds_before_final_receipt_write'] > plan['limits']['whole_seconds']:
            receipt['status'] = 'unknown_fixture_whole_deadline'
        for name in ('stdout', 'stderr', 'result'):
            if Path(plan['outputs'][name]).is_file():
                receipt[name] = pin(plan['outputs'][name])
        with output.open('x') as stream:
            json.dump(receipt, stream, indent=2, ensure_ascii=False, allow_nan=False); stream.write('\n')
    print(json.dumps({k: receipt.get(k) for k in ('status', 'child_pid', 'child_exit', 'child_reaped', 'owner_seconds_before_final_receipt_write', 'kernel_conservative_peak_bytes', 'sampled_combined_peak_bytes')}))


if __name__ == '__main__':
    main()
