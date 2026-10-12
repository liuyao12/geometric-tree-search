"""Prospective exact ROOT-activated per-context static audit owner; no retry.

The independent worker is a verifier, not a search. Complete worker/alarm,
owned RSS sampling, wait4 terminal status and fresh kernel peaks are charged.
No hard OS cap is claimed. Own final receipt serialization is outside timer.
"""
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def pin(path):
    path=Path(path).resolve();h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):h.update(block)
    return dict(path=str(path),sha256=h.hexdigest(),bytes=path.stat().st_size)


def wire_pin(path):
    item=pin(path);item['path']=str(Path(path).resolve().relative_to(ROOT));return item


def peak(usage):return usage.ru_maxrss*(1 if sys.platform=='darwin' else 1024)


def metadata(pid):
    result=subprocess.run(['/bin/ps','-o','rss=','-p',str(pid)],capture_output=True,text=True,timeout=1,check=False)
    if result.returncode!=0 or not result.stdout.strip():raise RuntimeError('owned audit RSS unavailable')
    value=int(result.stdout.strip())*1024
    if value<0:raise ValueError('negative owned RSS')
    return value,peak(resource.getrusage(resource.RUSAGE_CHILDREN))


def main():
    started=time.perf_counter();planpath=Path(sys.argv[1]).resolve();plan=json.loads(planpath.read_text())
    if plan['status']!='frozen_actual_inputs_pending_ROOT_activation':raise ValueError('actual plan required, not source-readiness template')
    outputs=plan['outputs']
    if any(Path(outputs[k]).exists() for k in ('lifetime','result','stdout','stderr')):
        raise ValueError('immutable audit outputs already exist; no rerun')
    receipt=dict(status='unknown_before_independent_trace_launch',plan=wire_pin(planpath),child_pid=None,
        child_exit=None,child_reaped=False,maximum_whole_seconds=plan['limits']['whole_seconds'],
        maximum_peak_bytes=plan['limits']['peak_bytes'],sampled_combined_peak_bytes=0,
        kernel_conservative_peak_bytes=0,metadata_child_peak_bytes=0,trace_accepted=False,
        certificate_accepted=False,static_context_pool_accepted=False,searches_run_by_owner=0,native_queries=0,training_runs=0)
    child=usage=None;waited=False
    def cutoff(*_):raise TimeoutError('owned independent full phase signal')
    signal.signal(signal.SIGTERM,cutoff);signal.signal(signal.SIGALRM,cutoff)
    signal.alarm(plan['limits']['whole_seconds'])
    try:
        checked={}
        for group in ('sources','libraries','inputs','preserved'):
            for item in plan[group]:
                if item['path'] not in checked:checked[item['path']]=pin(item['path'])
                if checked[item['path']]!={k:item[k] for k in ('path','sha256','bytes')}:
                    raise ValueError('exact independent frozen byte: '+item['path'])
        runtime=plan['runtime']
        if (runtime['executable']!=sys.executable or runtime['platform']!=sys.platform
                or pin(Path(sys.executable).resolve())!=runtime['binary'] or pin('/bin/ps')!=runtime['observer']):
            raise ValueError('exact audit runtime/observer binary')
        activationpath=Path(plan['activation_path']);activation=json.loads(activationpath.read_text())
        if (activation.get('schema')!=plan['required_activation_schema']
                or activation.get('authorized') is not True or activation.get('plan')!=wire_pin(planpath)):
            raise ValueError('separate exact ROOT activation after all source reviews required')
        receipt['activation']=pin(activationpath)
        with Path(outputs['stdout']).open('xb') as out,Path(outputs['stderr']).open('xb') as err:
            child=subprocess.Popen([sys.executable,'-B',plan['worker_path'],str(planpath)],stdin=subprocess.DEVNULL,
                stdout=out,stderr=err,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            receipt['child_pid']=child.pid
            while True:
                pid,status,current=os.wait4(child.pid,os.WNOHANG)
                if pid:
                    waited=True;usage=current;child.returncode=os.waitstatus_to_exitcode(status)
                    receipt['child_exit']=child.returncode;break
                if time.perf_counter()-started>=plan['limits']['supervisor_seconds']:
                    raise TimeoutError('owned independent audit full deadline')
                try:
                    childrss,a=metadata(child.pid);ownrss,b=metadata(os.getpid())
                    receipt['metadata_child_peak_bytes']=max(receipt['metadata_child_peak_bytes'],a,b)
                    combined=childrss+ownrss+receipt['metadata_child_peak_bytes']
                except RuntimeError:
                    pid,status,current=os.wait4(child.pid,os.WNOHANG)
                    if pid:
                        waited=True;usage=current;child.returncode=os.waitstatus_to_exitcode(status)
                        receipt['child_exit']=child.returncode;break
                    raise
                receipt['sampled_combined_peak_bytes']=max(receipt['sampled_combined_peak_bytes'],combined)
                if combined>plan['limits']['peak_bytes']:raise MemoryError('owned audit RSS ceiling')
                time.sleep(.02)
        receipt['child_reaped']=True
        receipt['kernel_conservative_peak_bytes']=peak(usage)+peak(resource.getrusage(resource.RUSAGE_SELF))+receipt['metadata_child_peak_bytes']
        if child.returncode!=0:receipt['status']='unknown_independent_trace_child_failure'
        elif max(receipt['kernel_conservative_peak_bytes'],receipt['sampled_combined_peak_bytes'])>plan['limits']['peak_bytes']:
            receipt['status']='unknown_independent_trace_memory_budget'
        elif not Path(outputs['result']).is_file():receipt['status']='unknown_missing_independent_trace_result'
        else:
            result=json.loads(Path(outputs['result']).read_text())
            if result['status']==plan['required_result_status'] and result['plan']==wire_pin(planpath):
                receipt['status']=plan['required_owner_success_status']
                receipt['trace_accepted']=result.get('trace_accepted',False);receipt['certificate_accepted']=result.get('certificate_accepted',False)
                receipt['static_context_pool_accepted']=result.get('static_context_pool_accepted',False)
                receipt['whole_target_logical_checks']=result.get('whole_target_logical_checks',0)
            else:receipt['status']='unknown_independent_trace_result'
    except BaseException as exc:
        receipt['status']='unknown_independent_trace_infrastructure_or_resource'
        receipt['failure']=dict(type=type(exc).__name__,reason=str(exc))
    finally:
        signal.alarm(0)
        if child is not None and not waited:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            _,status,usage=os.wait4(child.pid,0);child.returncode=os.waitstatus_to_exitcode(status)
            receipt['child_exit']=child.returncode;receipt['child_reaped']=True
            receipt['kernel_conservative_peak_bytes']=peak(usage)+peak(resource.getrusage(resource.RUSAGE_SELF))+receipt['metadata_child_peak_bytes']
        # Result JSON decoding and acceptance assembly are owner work too.
        # Do not keep the earlier owner peak from before result loading.
        if usage is not None:
            receipt['kernel_conservative_peak_bytes']=max(receipt['kernel_conservative_peak_bytes'],
                peak(usage)+peak(resource.getrusage(resource.RUSAGE_SELF))+receipt['metadata_child_peak_bytes'])
        if max(receipt['kernel_conservative_peak_bytes'],receipt['sampled_combined_peak_bytes'])>plan['limits']['peak_bytes']:
            receipt['status']='unknown_independent_trace_memory_budget';receipt['trace_accepted']=receipt['certificate_accepted']=receipt['static_context_pool_accepted']=False
        receipt['owner_seconds_before_final_receipt_write']=time.perf_counter()-started
        if receipt['owner_seconds_before_final_receipt_write']>plan['limits']['whole_seconds']:
            receipt['status']='unknown_independent_trace_whole_deadline';receipt['trace_accepted']=receipt['certificate_accepted']=receipt['static_context_pool_accepted']=False
        for name in ('stdout','stderr','result'):
            if Path(outputs[name]).is_file():receipt[name]=wire_pin(outputs[name])
        receipt['enforcement']='One owned wait4 child, worker SIGALRM, owned sampled RSS/time and fresh kernel peaks with retrospective rejection. No hard OS cap.'
        receipt['cost_scope']='Setup, body/model reconstruction, complete context/body/pool controls, worker serialization and reaping included. Own final receipt serialization and source authoring excluded; ROOT external process lifetime additional.'
        with Path(outputs['lifetime']).open('x') as stream:json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({k:receipt.get(k) for k in ('status','child_pid','child_exit','child_reaped','owner_seconds_before_final_receipt_write',
        'kernel_conservative_peak_bytes','sampled_combined_peak_bytes','trace_accepted','certificate_accepted')}),flush=True)
    return 0 if receipt['status']==plan['required_owner_success_status'] else 1


if __name__=='__main__':sys.exit(main())
