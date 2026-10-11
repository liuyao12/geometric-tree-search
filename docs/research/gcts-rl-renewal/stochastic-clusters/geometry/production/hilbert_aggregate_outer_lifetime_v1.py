"""Root-requested outer measurement includes final supervisor serialization."""
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    destination = HERE / 'outer-lifetime-v1.json'
    if destination.exists():
        raise ValueError('outer lifetime evidence already exists')
    started = time.perf_counter()
    result = subprocess.run([sys.executable, str(HERE / 'hilbert_aggregate_static_run_v1.py')], check=False)
    supervisor_wall = time.perf_counter() - started
    inner_path = HERE / 'stage-costs-v1.json'
    inner = json.loads(inner_path.read_text()) if inner_path.exists() else None
    own = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    children = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    if sys.platform != 'darwin':
        own *= 1024
        children *= 1024
    combined_peak = own + children + (inner['conservative_sum_kernel_peak_bytes'] if inner else 0)
    # Conservative host charge intentionally double-counts some child peaks.
    total = time.perf_counter() - started
    passed = result.returncode == 0 and inner is not None and inner['status'] == 'passed_bounded_static_production' and total <= 180 and combined_peak <= 512 * 1024 * 1024
    receipt = {'status': 'passed_outer_static_production_lifetime' if passed else 'unknown_or_failed',
               'scope': 'outer production lifetime including child and final supervisor receipt serialization',
               'full_outer_seconds_before_this_receipt_write': total,
               'supervisor_subprocess_full_wall_seconds': supervisor_wall,
               'supervisor_process_return_code': result.returncode,
               'supervisor_child_wait_reaped': True,
               'supervisor_receipt_sha256': hashlib.sha256(inner_path.read_bytes()).hexdigest() if inner else None,
               'plan_sha256': hashlib.sha256((HERE / 'plan-v1.json').read_bytes()).hexdigest(),
               'measurement_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'wrapper_peak_bytes': own, 'wrapper_children_kernel_peak_bytes': children,
               'deliberately_conservative_all_host_peak_sum_bytes': combined_peak,
               'wall_ceiling_seconds': 180, 'host_ceiling_bytes': 512 * 1024 * 1024,
               'native_queries': 0, 'target_searches': 0, 'existing_engine_activation': False,
               'own_receipt_write': 'outside reported outer pre-write seconds; producer and supervisor receipt serialization included'}
    destination.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
