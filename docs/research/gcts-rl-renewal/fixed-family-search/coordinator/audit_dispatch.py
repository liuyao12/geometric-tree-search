"""ROOT one-time independent verifier dispatch with a full process clock."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
AUDIT=ROOT/'.gcts-active/fixed-family-pool-trace-independent-20261012'

def pin(path):
    path=Path(path).resolve()
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)

def main():
    output=HERE/'audit-terminal-v1.json'
    if output.exists():raise ValueError('immutable actual audit terminal already exists')
    argv=[sys.executable,'-B',str(AUDIT/'fixed_pool_trace_owner_v1.py'),str(AUDIT/'audit-plan-v1.json')]
    started=time.perf_counter();child=subprocess.Popen(argv,cwd=ROOT);cleanup=None
    try:code=child.wait(timeout=190)
    except subprocess.TimeoutExpired:
        cleanup='ROOT_verifier_owner_cutoff_worker_terminal_unconfirmed';child.terminate()
        try:code=child.wait(timeout=5)
        except subprocess.TimeoutExpired:child.kill();code=child.wait()
    seconds=time.perf_counter()-started
    lifetime=AUDIT/'audit-lifetime-v1.json';life=json.loads(lifetime.read_text()) if lifetime.exists() else None
    passed=code==0 and cleanup is None and life is not None and life['status']=='passed_owned_independent_fixed_family_trace_audit' and life['child_reaped'] is True
    receipt=dict(status='passed_ROOT_owned_independent_fixed_pool_audit_dispatch' if passed else 'failed_or_unknown_ROOT_owned_audit_dispatch',
        argv=argv,owner_pid=child.pid,owner_exit_code=code,owner_process_terminal_reaped=True,
        worker_reaped=bool(life and life['child_reaped']),cleanup_reason=cleanup,
        full_audit_process_seconds_including_startup_and_receipt=seconds,
        lifetime=pin(lifetime) if life else None,
        trace_accepted=bool(passed and life['trace_accepted']),proof_accepted=bool(passed and life['certificate_accepted']),
        ROOT_terminal_write_outside_process_clock=True,new_searches=0,new_training=0,native_queries=0)
    with output.open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(receipt),flush=True)
    return 0 if passed else 1

if __name__=='__main__':sys.exit(main())
