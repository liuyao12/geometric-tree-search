"""ROOT-owned one-time dispatch and same-handle terminal record."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT/'.gcts-active/fixed-family-pool-search-source-20261012'

def pin(path):
    path = Path(path)
    return dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)

def main():
    output = HERE/'search-terminal-v1.json'
    if output.exists(): raise ValueError('immutable terminal already exists')
    argv = [sys.executable,str(SOURCE/'fixed_family_pool_outer_v1.py')]
    started = time.perf_counter()
    child = subprocess.Popen(argv,cwd=ROOT)
    cleanup = None
    try:
        code = child.wait(timeout=190)
    except subprocess.TimeoutExpired:
        cleanup = 'ROOT_dispatch_watchdog_outer_worker_terminal_unconfirmed'
        child.terminate()
        try: code = child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill();code = child.wait()
    seconds = time.perf_counter()-started
    life = SOURCE/'search-lifetime-v1.json'
    receipt = json.loads(life.read_text()) if life.exists() else None
    passed = code == 0 and cleanup is None and receipt is not None and receipt['status'] == 'passed_fixed_whole_family_pool_geometry_full_lifetime'
    result = dict(status='passed_ROOT_owned_fixed_family_pool_dispatch' if passed else 'failed_or_unknown_ROOT_dispatch',
        argv=argv,outer_pid=child.pid,outer_return_code=code,owner_process_terminal_reaped=True,
        full_owner_process_seconds_including_startup_and_receipt=seconds,
        cleanup_reason=cleanup,lifetime=pin(life) if receipt else None,
        worker_terminal_reaped_confirmed=bool(receipt and receipt['worker_terminal_reaped_confirmed']),
        ROOT_terminal_write_outside_process_clock=True,
        search_acceptance='pending independent tape audit',proof_acceptance='pending independent certificate audit',
        resource_scope='Retained owner peak estimate and time guards; observer RSS is not included in a strict aggregate host upper bound')
    with output.open('x') as f: json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result),flush=True)
    return 0 if passed else 1

if __name__ == '__main__': sys.exit(main())
