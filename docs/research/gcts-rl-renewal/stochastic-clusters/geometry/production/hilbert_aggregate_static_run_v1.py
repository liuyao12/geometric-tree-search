"""Task-owned fail-closed static producer supervision; no native or search."""
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIMIT_SECONDS = 180
LIMIT_BYTES = 512 * 1024 * 1024


def peak_bytes(kind):
    value = resource.getrusage(kind).ru_maxrss
    return value if sys.platform == 'darwin' else value * 1024


def save(path, value):
    if path.exists():
        raise ValueError('immutable supervisor receipt exists: ' + str(path))
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    start = time.perf_counter()
    child, reason, error, terminal = None, None, None, None
    watch = []
    plan_path = HERE / 'plan-v1.json'
    plan = json.loads(plan_path.read_text())
    sources = {x['path'].split('/')[-1]: x for x in plan['sources']}
    for name in ('hilbert_aggregate_expand_v1.py', 'hilbert_aggregate_static_run_v1.py'):
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == sources[name]['sha256']
    for name in ('production-v1.json', 'stage-costs-v1.json', 'production-launch-v1.json'):
        if (HERE / name).exists():
            raise ValueError('prior immutable stage exists')
    try:
        with (HERE / 'production-stdout-v1.txt').open('wb') as out, (HERE / 'production-stderr-v1.txt').open('wb') as err:
            child = subprocess.Popen([sys.executable, str(HERE / 'hilbert_aggregate_expand_v1.py')],
                                     cwd=HERE, stdout=out, stderr=err)
            save(HERE / 'production-launch-v1.json', {'pid': child.pid, 'wall_ceiling_seconds': LIMIT_SECONDS,
                                                      'host_ceiling_bytes': LIMIT_BYTES,
                                                      'scope': 'owned static expansion producer only'})
            try:
                while child.poll() is None:
                    elapsed = time.perf_counter() - start
                    if elapsed > LIMIT_SECONDS:
                        reason = 'wall_ceiling'
                        break
                    ps = subprocess.run(['ps', '-o', 'rss=', '-p', str(child.pid)], capture_output=True,
                                        timeout=min(2, max(.01, LIMIT_SECONDS - elapsed)), check=False)
                    raw = ps.stdout.strip()
                    if ps.returncode == 0 and raw:
                        resident = int(raw) * 1024
                        if resident < 0:
                            raise ValueError('negative process RSS')
                        own = peak_bytes(resource.RUSAGE_SELF)
                        watch.append({'elapsed_seconds': elapsed, 'child_rss_bytes': resident,
                                      'supervisor_peak_rss_bytes': own})
                        if resident + own > LIMIT_BYTES:
                            reason = 'sampled_combined_host_ceiling'
                            break
                    elif child.poll() is None:
                        raise RuntimeError('owned process metadata unavailable: ' + str(ps.returncode) + ' ' + ps.stderr.decode(errors='replace'))
                    time.sleep(.05)
            except BaseException as e:
                reason, error = 'watchdog_failure', type(e).__name__ + ': ' + str(e)
            finally:
                if reason is not None and child.poll() is None:
                    child.kill()
                terminal = child.wait()
    except BaseException as e:
        reason = reason or 'supervisory_failure'
        error = error or type(e).__name__ + ': ' + str(e)
        if child is not None:
            if child.poll() is None:
                child.kill()
            terminal = child.wait()
    elapsed = time.perf_counter() - start
    receipt = None
    try:
        receipt = json.loads((HERE / 'production-v1.json').read_text())
    except BaseException as e:
        reason = reason or 'missing_or_invalid_child_receipt'
        error = error or type(e).__name__ + ': ' + str(e)
    reported_peak = receipt.get('peak_rss_bytes') if receipt else None
    child_kernel_peak = peak_bytes(resource.RUSAGE_CHILDREN)
    own_peak = peak_bytes(resource.RUSAGE_SELF)
    # Conservative sum includes all child processes, including short ps probes.
    conservative_host_peak = child_kernel_peak + own_peak
    if type(reported_peak) is not int or reported_peak < 0:
        reason = reason or 'missing_or_invalid_reported_peak'
    elif reported_peak > LIMIT_BYTES:
        reason = reason or 'reported_child_peak_ceiling'
    if conservative_host_peak > LIMIT_BYTES:
        reason = reason or 'final_conservative_kernel_host_peak_ceiling'
    if elapsed > LIMIT_SECONDS:
        reason = reason or 'final_wall_ceiling'
    if not watch:
        reason = reason or 'no_external_owned_RSS_samples'
    passed = terminal == 0 and reason is None and receipt is not None
    result = {'status': 'passed_bounded_static_production' if passed else 'unknown_or_failed',
              'plan_sha256': hashlib.sha256(plan_path.read_bytes()).hexdigest(),
              'process_pid': child.pid if child else None, 'exit_code': terminal,
              'owned_child_wait_reaped': child is not None and terminal is not None,
              'full_process_wall_seconds': elapsed, 'wall_ceiling_seconds': LIMIT_SECONDS,
              'host_ceiling_bytes': LIMIT_BYTES, 'watchdog_error': error, 'resource_unknown_reason': reason,
              'rss_samples': watch, 'reported_child_peak_bytes': reported_peak,
              'kernel_children_peak_bytes': child_kernel_peak, 'supervisor_peak_bytes': own_peak,
              'conservative_sum_kernel_peak_bytes': conservative_host_peak,
              'enforcement': 'external owned process RSS/time watchdog, child SIGALRM, final conservative kernel peak rejection',
              'OS_soft_limit_claim': 'none', 'native_queries': 0, 'target_searches': 0,
              'existing_engine_activation': False, 'point_placement_graphs': 0,
              'independent_audit': 'separate agent/gate, not executed by this supervisor'}
    save(HERE / 'stage-costs-v1.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rss_samples'}), flush=True)


if __name__ == '__main__':
    main()
