"""Sole-owned independent full-language lifecycle audit phase, activated only by root."""
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
        for b in iter(lambda:f.read(65536),b''):h.update(b)
    return dict(path=str(p.relative_to(ROOT)),sha256=h.hexdigest(),bytes=p.stat().st_size)


def main():
    began=time.perf_counter(); pp=HERE/'audit-plan-v2.json'; plan=json.loads(pp.read_bytes())
    destination=ROOT/plan['lifetime_path']
    if destination.exists():raise ValueError('immutable independent lifetime exists')
    child=terminal=usage=None;failure=None
    try:
        ap=HERE/'root-activation-v2.json'; a=json.loads(ap.read_bytes())
        if a['status']!='authorized_by_root_after_independent_source_review' or a['plan_sha256']!=pin(pp)['sha256']:
            raise ValueError('exact root activation required')
        for p,h in a.get('prerequisite_sha256',{}).items():
            if pin(ROOT/p)['sha256']!=h:raise ValueError('activation prerequisite changed '+p)
        checked={}
        for p in plan['sources']+plan['libraries']+plan['inputs']+plan['preserved_files']:
            actual=checked.setdefault(p['path'],pin(ROOT/p['path']))
            if actual!={k:p[k] for k in ('path','sha256','bytes')}:raise ValueError('independent pin '+p['path'])
        with (ROOT/plan['stdout_path']).open('xb') as out,(ROOT/plan['stderr_path']).open('xb') as err:
            child=subprocess.Popen([sys.executable,str(ROOT/plan['worker_path'])],cwd=HERE,stdout=out,stderr=err)
            while terminal is None:
                waited,status,u=os.wait4(child.pid,os.WNOHANG)
                if waited:
                    terminal=os.waitstatus_to_exitcode(status);usage=u;child.returncode=terminal;break
                if time.perf_counter()-began>=plan['whole_seconds']:
                    failure='independent owned wall gate';os.kill(child.pid,signal.SIGKILL)
                    _,status,usage=os.wait4(child.pid,0);terminal=os.waitstatus_to_exitcode(status);child.returncode=terminal;break
                time.sleep(.01)
    except BaseException as exc:failure=type(exc).__name__+': '+str(exc)
    finally:
        if child is not None and terminal is None:
            try:os.kill(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            _,status,usage=os.wait4(child.pid,0);terminal=os.waitstatus_to_exitcode(status);child.returncode=terminal
    resultpath=ROOT/plan['result_path']; result=None
    if resultpath.exists():
        try:result=json.loads(resultpath.read_bytes())
        except Exception as exc:failure=failure or 'invalid independent result '+str(exc)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;childpeak=usage.ru_maxrss if usage else 0
    if sys.platform!='darwin':peak*=1024;childpeak*=1024
    elapsed=time.perf_counter()-began
    success=(terminal==0 and failure is None and result is not None
        and result['status']=='passed_independent_full_language_lifecycle_controlled_artifact_audit'
        and result['plan_sha256']==pin(pp)['sha256'] and elapsed<=plan['whole_seconds']
        and peak+childpeak<=plan['peak_bytes'])
    receipt=dict(status='passed_owned_independent_full_language_lifecycle_audit' if success else 'unknown_or_failed_owned_independent_full_language_lifecycle_audit',
        plan=pin(pp),result_pin=pin(resultpath) if resultpath.exists() else None,
        child_pid=child.pid if child else None,child_exit_code=terminal,
        owned_child_terminal_and_reaped=child is not None and terminal is not None,failure=failure,
        full_owner_and_worker_seconds_before_receipt_write=elapsed,fresh_child_kernel_peak_bytes=childpeak,
        owner_kernel_peak_bytes=peak,conservative_combined_peak_bytes=peak+childpeak,
        whole_ceiling_seconds=plan['whole_seconds'],peak_ceiling_bytes=plan['peak_bytes'],
        wall_overshoot_seconds=max(0,elapsed-plan['whole_seconds']),memory_overshoot_bytes=max(0,peak+childpeak-plan['peak_bytes']),
        enforcement='Sole wait4 direct-child owner, worker SIGALRM and owned wall kill/reap; retrospective fresh-child plus owner kernel peak gate. No hard OS limit or live RSS-sampling claim.',
        clock_scope='Includes owner hashing/activation, entire child/result serialization/reap and assembly; excludes final own receipt write and unmeasured source authoring.',
        actual_geometry_model_loads=result.get('actual_geometry_model_loads') if result else None,target_searches=0,native_queries=0,compiler_activations=0,training_episodes=0)
    with destination.open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(receipt),flush=True)
    return 0 if success else 1


if __name__=='__main__':sys.exit(main())
