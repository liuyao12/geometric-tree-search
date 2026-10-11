"""Bound reader preparation only; do not run proof search or admit interfaces."""
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def peak(kind):
    value = resource.getrusage(kind).ru_maxrss
    return value if sys.platform == 'darwin' else value * 1024


def main():
    started = time.perf_counter()
    output = HERE / 'reader-extraction-lifetime-v1.json'
    if output.exists():
        raise ValueError('reader preparation lifetime already exists')
    plan_path = HERE / 'reader-extraction-plan-v1.json'
    plan = json.loads(plan_path.read_text())
    for p in plan['sources'] + plan['inputs']:
        raw = (ROOT / p['path']).read_bytes()
        assert len(raw) == p['bytes'] and hashlib.sha256(raw).hexdigest() == p['sha256']
    child, terminal, reason, error = None, None, None, None
    samples = []
    try:
        with (HERE / 'reader-stdout-v1.txt').open('xb') as stdout, (HERE / 'reader-stderr-v1.txt').open('xb') as stderr:
            child = subprocess.Popen([sys.executable, str(HERE / 'hilbert_aggregate_reader_data_v1.py')], stdout=stdout, stderr=stderr, cwd=HERE)
            try:
                while child.poll() is None:
                    elapsed = time.perf_counter() - started
                    if elapsed > 180:
                        reason = 'wall_ceiling'
                        break
                    ps = subprocess.run(['ps', '-o', 'rss=', '-p', str(child.pid)], capture_output=True, timeout=2, check=False)
                    if ps.returncode == 0 and ps.stdout.strip():
                        resident = int(ps.stdout.strip()) * 1024
                        if resident < 0:
                            raise ValueError('negative RSS')
                        samples.append({'seconds': elapsed, 'child_rss_bytes': resident})
                        if resident + peak(resource.RUSAGE_SELF) > 512 * 1024 * 1024:
                            reason = 'host_peak_ceiling'
                            break
                    elif child.poll() is None:
                        raise RuntimeError('owned child metadata unavailable')
                    time.sleep(.05)
            except BaseException as e:
                reason, error = 'watchdog_failure', type(e).__name__ + ': ' + str(e)
            finally:
                if reason and child.poll() is None:
                    child.kill()
                terminal = child.wait()
    except BaseException as e:
        reason, error = reason or 'supervisor_failure', error or type(e).__name__ + ': ' + str(e)
        if child is not None:
            if child.poll() is None:
                child.kill()
            terminal = child.wait()
    receipt_path = HERE / 'reader-extraction-receipt-v1.json'
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
    elapsed = time.perf_counter() - started
    host_peak = peak(resource.RUSAGE_SELF) + peak(resource.RUSAGE_CHILDREN)
    if elapsed > 180 or host_peak > 512 * 1024 * 1024:
        reason = reason or 'final_resource_ceiling'
    if not samples or receipt is None:
        reason = reason or 'missing_enforcement_or_result'
    result = {'status': 'passed_bounded_reader_preparation' if terminal == 0 and reason is None else 'unknown_or_failed',
              'scope': 'separate compact reader extraction preparation; not a logical audit, admission or search',
              'full_seconds_including_child_receipt_serialization': elapsed, 'host_kernel_peak_sum_bytes': host_peak,
              'plan_sha256': hashlib.sha256(plan_path.read_bytes()).hexdigest(),
              'child_receipt_sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest() if receipt else None,
              'child_pid': child.pid if child else None, 'terminal_exit_code': terminal, 'child_wait_reaped': child is not None and terminal is not None,
              'unknown_reason': reason, 'watchdog_error': error, 'rss_samples': samples,
              'wall_ceiling_seconds': 180, 'host_ceiling_bytes': 512 * 1024 * 1024,
              'native_queries': 0, 'target_searches': 0, 'engine_or_authority_activation': False,
              'own_lifetime_receipt_write': 'outside reported prewrite seconds'}
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'rss_samples'}), flush=True)


if __name__ == '__main__':
    main()
