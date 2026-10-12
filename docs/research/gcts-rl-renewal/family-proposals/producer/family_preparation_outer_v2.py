"""Root-dispatched full owner lifetime; bounded cleanup, immutable receipts."""
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
    return resource.getrusage(kind).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)


def pin(path):
    path = Path(path); h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''): h.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def main():
    start = time.perf_counter(); output = HERE / 'preparation-lifetime-v2.json'
    if output.exists(): raise ValueError('immutable owner lifetime already exists')
    planpath = HERE / 'preparation-plan-v2.json'; plan = json.loads(planpath.read_text())
    for p in plan['sources'] + plan['inputs'] + plan['preserved_files']:
        if pin(ROOT / p['path']) != {k: p[k] for k in ('path', 'sha256', 'bytes')}:
            raise ValueError('frozen owner pin mismatch: ' + p['path'])
    child = subprocess.Popen([sys.executable, str(HERE / 'family_preparation_supervisor_v2.py')], cwd=HERE)
    cleanup_reason = None
    try:
        terminal = child.wait(timeout=max(.01, 70 - (time.perf_counter() - start)))
    except subprocess.TimeoutExpired:
        cleanup_reason = 'outer_wall_cutoff'
        child.terminate()  # Supervisor SIGTERM raises into its kill/reap finally.
        try: terminal = child.wait(timeout=3)
        except subprocess.TimeoutExpired:
            child.kill(); terminal = child.wait()
            cleanup_reason = 'outer_cutoff_supervisor_unresponsive_owned_worker_terminal_not_confirmed'
    wall = time.perf_counter() - start
    innerpath = HERE / 'preparation-supervision-v2.json'
    inner = json.loads(innerpath.read_text()) if innerpath.exists() else None
    own, children = peak(resource.RUSAGE_SELF), peak(resource.RUSAGE_CHILDREN)
    conservative = own + max(children, inner['conservative_host_peak_bytes'] if inner else 0)
    passed = (terminal == 0 and cleanup_reason is None and inner is not None
              and inner['status'] == 'passed_bounded_family_preparation_resource_phase'
              and inner['owned_child_terminal_wait_reaped'] and wall <= 70 and conservative <= 536870912)
    receipt = {'status': 'passed_family_preparation_full_lifetime_resource_phase' if passed else 'unknown_or_failed',
        'full_supervisor_process_seconds_including_receipt_write': wall, 'process_return_code': terminal,
        'supervisor_pid': child.pid, 'supervisor_wait_reaped': True, 'outer_cleanup_reason': cleanup_reason,
        'worker_terminal_reaped_confirmed': bool(inner and inner['owned_child_terminal_wait_reaped']),
        'outer_own_peak_bytes': own, 'outer_children_kernel_peak_bytes': children,
        'conservative_host_peak_bytes': conservative, 'host_ceiling_bytes': 536870912, 'wall_ceiling_seconds': 70,
        'actual_wall_overshoot_seconds': max(0, wall - 70), 'actual_memory_overshoot_bytes': max(0, conservative - 536870912),
        'plan': pin(planpath), 'supervision': pin(innerpath) if inner else None,
        'own_receipt_serialization': 'outside pre-write measurement; all worker/supervisor serialization included',
        'actual_geometry_model_execution': bool(inner and inner['actual_geometry_model_execution']),
        'maximum_geometry_target_searches': 0, 'native_queries': 0, 'native_authority_activated': False,
        'preparation_status': inner['preparation_status'] if inner else None, 'preparation_complete': bool(inner and inner['preparation_complete']),
        'mathematical_acceptance': 'none; independent proposal-pool audit separate; no search/native in this phase'}
    with output.open('x') as stream: stream.write(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(json.dumps(receipt), flush=True)
    return 0 if passed else 1


if __name__ == '__main__': sys.exit(main())
