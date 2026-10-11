"""Sole root-activated direct-child owner; no searches or native calls."""
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def pin(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return dict(path=str(p.relative_to(ROOT)),sha256=h.hexdigest(),bytes=p.stat().st_size)


def main():
    began=time.perf_counter();pp=HERE/'audit-plan-v1.json';plan=json.loads(pp.read_text())
    output=ROOT/plan['lifetime_path']
    if output.exists():raise ValueError('immutable independent lifetime already exists')
    child=terminal=usage=None;failure=None
    try:
        activation=json.loads((HERE/'root-activation-v1.json').read_text())
        if activation['status']!='authorized_by_root_after_independent_source_review' or activation['plan_sha256']!=pin(pp)['sha256']:
            raise ValueError('exact root source-review activation required')
        for name,sha in activation.get('prerequisite_sha256',{}).items():
            if pin(ROOT/name)['sha256']!=sha:raise ValueError('activation prerequisite mismatch '+name)
        checked={}
        for e in plan['sources']+plan['libraries']+plan['inputs']+plan['preserved_files']:
            if e['path'] not in checked:checked[e['path']]=pin(ROOT/e['path'])
            if checked[e['path']]!={k:e[k] for k in ('path','sha256','bytes')}:
                raise ValueError('exact independent source/input pin '+e['path'])
        if any((ROOT/plan[k]).exists() for k in ('result_path','stdout_path','stderr_path')):
            raise ValueError('immutable scientific output already exists')
        with (ROOT/plan['stdout_path']).open('xb') as out,(ROOT/plan['stderr_path']).open('xb') as err:
            child=subprocess.Popen([sys.executable,str(ROOT/plan['worker_path'])],cwd=HERE,stdout=out,stderr=err)
            while terminal is None:
                waited,status,u=os.wait4(child.pid,os.WNOHANG)
                if waited:
                    terminal=os.waitstatus_to_exitcode(status);usage=u;child.returncode=terminal;break
                if time.perf_counter()-began>=plan['whole_seconds']:
                    failure='independent whole wall gate';os.kill(child.pid,signal.SIGKILL)
                    _,status,usage=os.wait4(child.pid,0);terminal=os.waitstatus_to_exitcode(status);child.returncode=terminal;break
                time.sleep(.01)
    except BaseException as exc:failure=type(exc).__name__+': '+str(exc)
    finally:
        if child is not None and terminal is None:
            try:os.kill(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            _,status,usage=os.wait4(child.pid,0);terminal=os.waitstatus_to_exitcode(status);child.returncode=terminal
    resultpath=ROOT/plan['result_path'];result=None
    if resultpath.exists():
        try:result=json.loads(resultpath.read_text())
        except Exception as exc:failure=failure or 'invalid result '+str(exc)
    owner_peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    child_peak=usage.ru_maxrss if usage else 0
    if sys.platform!='darwin':owner_peak*=1024;child_peak*=1024
    elapsed=time.perf_counter()-began
    success=(terminal==0 and failure is None and result is not None and
        result['status']=='passed_independent_complete_geometry_trace_audit_zero_certificates' and
        result['plan_sha256']==pin(pp)['sha256'] and elapsed<=plan['whole_seconds'] and
        owner_peak+child_peak<=plan['peak_bytes'])
    receipt=dict(status='passed_owned_independent_geometry_trace_audit' if success else
        'unknown_or_failed_owned_independent_geometry_trace_audit',plan=pin(pp),
        result=pin(resultpath) if resultpath.exists() else None,
        child_pid=child.pid if child else None,child_exit_code=terminal,
        owned_child_terminal_and_reaped=child is not None and terminal is not None,failure=failure,
        full_owner_and_worker_seconds_before_receipt_write=elapsed,
        fresh_child_kernel_peak_bytes=child_peak,owner_kernel_peak_bytes=owner_peak,
        conservative_combined_peak_bytes=child_peak+owner_peak,
        whole_ceiling_seconds=plan['whole_seconds'],peak_ceiling_bytes=plan['peak_bytes'],
        wall_overshoot_seconds=max(0,elapsed-plan['whole_seconds']),
        memory_overshoot_bytes=max(0,child_peak+owner_peak-plan['peak_bytes']),
        enforcement='Owned wait4 direct child, worker SIGALRM, owner deadline kill/wait/reap; retrospective fresh child plus owner kernel peak. No hard OS memory cap or live RSS sampling.',
        clock_scope='Owner verification/activation, child source-family setup, both complete trace audits, mutations, serialization/reap and receipt assembly; own final receipt write and source authoring excluded.',
        audit_observations=2 if success else None,searches_run_by_owner=0,native_queries=0,
        whole_target_logical_checks=0,positive_certificates=0)
    with output.open('x') as f:json.dump(receipt,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(receipt),flush=True)
    return 0 if success else 1


if __name__=='__main__':sys.exit(main())
