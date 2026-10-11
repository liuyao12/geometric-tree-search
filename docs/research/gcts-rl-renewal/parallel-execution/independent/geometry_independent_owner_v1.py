"""Sole direct-child owner for one bounded pure independent fixture worker."""
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def main():
    start = time.perf_counter()
    plan_path = HERE / 'geometry-independent-plan-v1.json'
    plan = json.loads(plan_path.read_bytes())
    output = HERE / 'geometry-independent-lifetime-v1.json'
    if output.exists():
        raise ValueError('immutable independent fixture receipt exists')
    for path, expected in plan['pins'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    child = terminal = usage = None
    failure = None
    try:
        with (HERE / 'geometry-independent-stdout-v1.txt').open('xb') as stdout, \
                (HERE / 'geometry-independent-stderr-v1.txt').open('xb') as stderr:
            child = subprocess.Popen([sys.executable, str(HERE / 'geometry_independent_fixtures_v1.py')],
                stdout=stdout, stderr=stderr, cwd=ROOT)
            while terminal is None:
                pid, status, got_usage = os.wait4(child.pid, os.WNOHANG)
                if pid:
                    terminal = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -os.WTERMSIG(status)
                    usage = got_usage
                    child.returncode = terminal
                    break
                if time.perf_counter() - start > plan['whole_seconds']:
                    failure = 'owned whole lifetime ceiling'
                    child.kill()
                    _, status, usage = os.wait4(child.pid, 0)
                    terminal = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -os.WTERMSIG(status)
                    child.returncode = terminal
                    break
                time.sleep(.01)
    except BaseException as exc:
        failure = type(exc).__name__ + ': ' + str(exc)
        if child is not None and terminal is None:
            child.kill()
            _, status, usage = os.wait4(child.pid, 0)
            terminal = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -os.WTERMSIG(status)
            child.returncode = terminal
    result_path = HERE / 'geometry-independent-result-v1.json'
    result = json.loads(result_path.read_bytes()) if result_path.exists() else None
    owner_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    child_peak = usage.ru_maxrss if usage else 0
    if sys.platform != 'darwin':
        owner_peak *= 1024
        child_peak *= 1024
    elapsed = time.perf_counter() - start
    success = terminal == 0 and failure is None and result is not None \
        and result['status'] == 'passed_independent_synthetic_domain_identity_scheduler_fixtures_with_cluster_gap_confirmed' \
        and elapsed <= plan['whole_seconds'] and owner_peak + child_peak <= plan['peak_bytes']
    receipt = {'status': 'passed_owned_independent_pure_fixture_lifetime' if success else 'unknown_or_failed',
        'plan_sha256': hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        'result_sha256': hashlib.sha256(result_path.read_bytes()).hexdigest() if result else None,
        'child_pid': child.pid if child else None, 'child_exit_code': terminal,
        'owned_child_terminal_and_reaped': terminal is not None, 'failure': failure,
        'full_worker_lifecycle_and_owner_seconds_before_receipt_write': elapsed,
        'owner_kernel_peak_bytes': owner_peak, 'fresh_child_kernel_peak_bytes': child_peak,
        'conservative_combined_peak_bytes': owner_peak + child_peak,
        'whole_ceiling_seconds': plan['whole_seconds'], 'peak_ceiling_bytes': plan['peak_bytes'],
        'enforcement': 'Sole wait4 direct-child owner; internal alarm and external wall kill/reap. Retrospective conservative fresh kernel peak gate, no hard memory cap or sampler claim.',
        'receipt_write': 'Owner own final receipt write excluded; full fixture receipt write and worker lifecycle included.',
        'production_model_loads': 0, 'target_searches': 0, 'native_queries': 0}
    with output.open('x') as stream:
        json.dump(receipt, stream, indent=2); stream.write('\n')
    print(json.dumps(receipt), flush=True)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
