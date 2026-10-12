"""Prospective ROOT-owned independent static pool audit; exclusive outputs.

Only this reviewed entry point is authorized by an exact ROOT activation.
The worker's independent literal model/body reconstruction is not metadata-only,
not a production engine execution and not a recipient proof/native check.
There is one direct child, no retries, and kill/wait4 reaping on every failure.
RSS samples and conservative final kernel peaks are resource gates; no hard OS
memory-limit claim is made. Final owner receipt writing is outside its timer.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time


def pin(path):
    path=Path(path).resolve(); digest=hashlib.sha256(); size=0
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):
            digest.update(block);size+=len(block)
    return dict(path=str(path),sha256=digest.hexdigest(),bytes=size)


def peak(usage):
    return usage.ru_maxrss*(1 if sys.platform=='darwin' else 1024)


def metadata(pid):
    result=subprocess.run(['/bin/ps','-o','rss=','-p',str(pid)],capture_output=True,text=True,timeout=1,check=False)
    if result.returncode!=0 or not result.stdout.strip():
        raise RuntimeError('owned PID RSS unavailable: '+str(pid))
    return int(result.stdout.strip())*1024,peak(resource.getrusage(resource.RUSAGE_CHILDREN))


def main():
    started=time.monotonic();planpath=Path(sys.argv[1]).resolve();plan=json.loads(planpath.read_text())
    outputs=plan['outputs']
    if any(Path(outputs[k]).exists() for k in ('lifetime','result','stdout','stderr')):
        raise RuntimeError('exclusive outputs already exist; no rerun')
    receipt=dict(status='unknown_before_independent_pool_launch',plan=pin(planpath),child_pid=None,
        child_exit=None,child_reaped=False,sampled_combined_peak_bytes=0,kernel_conservative_peak_bytes=0,
        metadata_child_peak_bytes=0,maximum_whole_seconds=plan['limits']['whole_seconds'],
        maximum_peak_bytes=plan['limits']['peak_bytes'],independent_literal_model_reconstruction='not started',
        production_engine_runs=0,controller_runs=0,target_searches=0,native_queries=0,
        whole_target_proof_checks=0,scope='Independent source-body/initial point-state/binding/identity/aggregate reconstruction only')
    child,usage,waited=None,None,False
    try:
        for group in ('sources','libraries','inputs','preserved'):
            for item in plan[group]:
                if pin(item['path'])!={k:item[k] for k in ('path','sha256','bytes')}:
                    raise ValueError('exact frozen source/input: '+item['path'])
        if (plan['runtime']['executable']!=sys.executable or plan['runtime']['platform']!=sys.platform
                or pin(Path(sys.executable).resolve())!=plan['runtime']['binary']):
            raise ValueError('exact Python runtime executable and resolved binary')
        activationpath=Path(plan['activation_path']);activation=json.loads(activationpath.read_text())
        if (activation.get('schema')!='root-independent-static-family-pool-activation-v1'
                or activation.get('authorized') is not True
                or activation.get('plan_sha256')!=receipt['plan']['sha256']):
            raise ValueError('exact ROOT-owned prospective audit activation required')
        receipt['activation']=pin(activationpath)
        with Path(outputs['stdout']).open('xb') as stdout,Path(outputs['stderr']).open('xb') as stderr:
            child=subprocess.Popen([sys.executable,plan['worker_path'],str(planpath)],stdin=subprocess.DEVNULL,
                stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            receipt['child_pid']=child.pid;receipt['independent_literal_model_reconstruction']='launched; completion not yet established'
            deadline=started+plan['limits']['supervisor_seconds']
            while True:
                pid,status,current=os.wait4(child.pid,os.WNOHANG)
                if pid:
                    usage=current;waited=True;child.returncode=os.waitstatus_to_exitcode(status)
                    receipt['child_exit']=child.returncode;break
                if time.monotonic()>=deadline:
                    raise TimeoutError('owned independent audit deadline')
                try:
                    childrss,monitor_a=metadata(child.pid);ownrss,monitor_b=metadata(os.getpid())
                    receipt['metadata_child_peak_bytes']=max(receipt['metadata_child_peak_bytes'],monitor_a,monitor_b)
                    combined=childrss+ownrss+receipt['metadata_child_peak_bytes']
                except RuntimeError:
                    pid,status,current=os.wait4(child.pid,os.WNOHANG)
                    if pid:
                        usage=current;waited=True;child.returncode=os.waitstatus_to_exitcode(status)
                        receipt['child_exit']=child.returncode;break
                    raise
                receipt['sampled_combined_peak_bytes']=max(receipt['sampled_combined_peak_bytes'],combined)
                if combined>plan['limits']['peak_bytes']:
                    raise MemoryError('owned independent audit sampled memory ceiling')
                time.sleep(.02)
        receipt['child_reaped']=True
        receipt['kernel_conservative_peak_bytes']=peak(usage)+peak(resource.getrusage(resource.RUSAGE_SELF))+receipt['metadata_child_peak_bytes']
        if child.returncode!=0:
            receipt['status']='unknown_independent_pool_child_failure'
        elif max(receipt['kernel_conservative_peak_bytes'],receipt['sampled_combined_peak_bytes'])>plan['limits']['peak_bytes']:
            receipt['status']='unknown_independent_pool_memory_budget'
        elif not Path(outputs['result']).is_file():
            receipt['status']='unknown_missing_independent_pool_result'
        else:
            result=json.loads(Path(outputs['result']).read_text())
            receipt['independent_literal_model_reconstruction']=result.get('independent_literal_point_state_reconstructed','unknown')
            receipt['status']=('passed_owned_independent_static_family_pool_audit'
                if result['status']=='passed_complete_independent_static_family_pool_audit'
                else 'unknown_independent_pool_result')
    except BaseException as exc:
        receipt['status']='unknown_independent_pool_infrastructure_or_resource'
        receipt['failure']=dict(type=type(exc).__name__,reason=str(exc))
    finally:
        if child is not None and not waited:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            _,status,usage=os.wait4(child.pid,0);child.returncode=os.waitstatus_to_exitcode(status)
            receipt['child_exit']=child.returncode;receipt['child_reaped']=True
            receipt['kernel_conservative_peak_bytes']=peak(usage)+peak(resource.getrusage(resource.RUSAGE_SELF))+receipt['metadata_child_peak_bytes']
        receipt['owner_seconds_before_final_receipt_write']=time.monotonic()-started
        if receipt['owner_seconds_before_final_receipt_write']>plan['limits']['whole_seconds']:
            receipt['status']='unknown_independent_pool_whole_deadline'
        for name in ('stdout','stderr','result'):
            if Path(outputs[name]).is_file():receipt[name]=pin(outputs[name])
        receipt['cost_scope']='Worker/result serialization and owner validation included; own final receipt serialization outside pre-write timer'
        with Path(outputs['lifetime']).open('x') as stream:
            json.dump(receipt,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')
    print(json.dumps({k:receipt.get(k) for k in ('status','child_pid','child_exit','child_reaped',
        'owner_seconds_before_final_receipt_write','kernel_conservative_peak_bytes','sampled_combined_peak_bytes')}))


if __name__=='__main__':main()
