"""ROOT-owned generic phase monitor. Source only, no OS hard-cap claim."""
import json
import resource
import signal
import subprocess
import sys
import time
from curriculum_runtime_v1 import HERE,ROOT,read,pin,verify,activation,save_json,plan_path

def peak(kind):return resource.getrusage(kind).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
def stopped(*_):raise TimeoutError('owned supervisor stop/timeout')
def main():
    start=time.perf_counter();planpath=plan_path(sys.argv[1]);plan=read(planpath);verify(plan);activation(plan,planpath)
    cfg=plan['phase'];ceiling=cfg['supervisor_seconds'];maximum=cfg['bytes'];kind=cfg['kind']
    if kind!='preparation' or ceiling!=55 or cfg['child_seconds']!=50 or maximum!=536870912:
        raise ValueError('unchanged exact phase ceilings')
    for name in plan['proposed_outputs']:
        if (HERE/name).exists():raise ValueError('immutable phase output already exists: '+name)
    signal.signal(signal.SIGALRM,stopped);signal.signal(signal.SIGTERM,stopped);signal.alarm(ceiling)
    child=None;terminal=None;reason=None;error=None;samples=[]
    try:
        with (HERE/cfg['stdout']).open('xb') as out,(HERE/cfg['stderr']).open('xb') as err:
            child=subprocess.Popen([sys.executable,str(HERE/cfg['worker']),str(planpath)],cwd=HERE,stdout=out,stderr=err)
            save_json(HERE/cfg['launch'],{'pid':child.pid,'plan':pin(planpath),'phase_kind':kind,'ROOT_activation':pin(HERE/plan['activation_basename']),'native_queries':0})
            try:
                while child.poll() is None:
                    elapsed=time.perf_counter()-start
                    if elapsed>=ceiling:reason='wall_ceiling';break
                    ps=subprocess.run(['/bin/ps','-o','rss=','-p',str(child.pid)],capture_output=True,timeout=min(2,max(.01,ceiling-elapsed)),check=False)
                    raw=ps.stdout.strip()
                    if ps.returncode==0 and raw:
                        rss=int(raw)*1024;own=peak(resource.RUSAGE_SELF)
                        if rss<0:raise ValueError('negative RSS')
                        samples.append({'seconds':elapsed,'child_rss_bytes':rss,'supervisor_peak_bytes':own})
                        if rss+own>maximum:reason='sampled_memory_ceiling';break
                    elif child.poll() is None:raise RuntimeError('owned process metadata unavailable: '+ps.stderr.decode(errors='replace'))
                    time.sleep(.02)
            except BaseException as exc:reason='watchdog_failure';error=type(exc).__name__+': '+str(exc)
            finally:
                signal.alarm(0)
                if reason and child.poll() is None:child.kill()
                terminal=child.wait()
    except BaseException as exc:
        signal.alarm(0);reason=reason or 'supervisor_failure';error=error or type(exc).__name__+': '+str(exc)
        if child is not None:
            if child.poll() is None:child.kill()
            terminal=child.wait()
    signal.alarm(0);outcome=None
    try:outcome=read(HERE/cfg['outcome'])
    except BaseException as exc:reason=reason or 'missing_child_outcome';error=error or str(exc)
    own=peak(resource.RUSAGE_SELF);childpeak=peak(resource.RUSAGE_CHILDREN);wall=time.perf_counter()-start
    if wall>ceiling:reason=reason or 'final_wall_ceiling'
    if own+childpeak>maximum:reason=reason or 'final_kernel_peak_ceiling'
    if not samples:reason=reason or 'no_owned_RSS_sample'
    if outcome is not None:
        if outcome.get('native_queries')!=0 or outcome.get('new_RL_training') is not False:reason=reason or 'unexpected_science_scope'
        if outcome.get('plan')!=pin(planpath):reason=reason or 'wrong_child_plan'
        artifacts=[outcome['compiled_context'],outcome['preparation_evidence']]
        for p in artifacts:
            if pin(ROOT/p['path'])!=p:reason=reason or 'child_output_pin_mismatch'
        if kind=='preparation' and outcome['status']!='completed_fresh_context_preparation_pending_independent_gate':reason=reason or 'incomplete_preparation'
        if outcome.get('selector')!=plan['selector']:reason=reason or 'wrong_frozen_context_selector'
    passed=terminal==0 and reason is None and outcome is not None
    receipt={'status':'passed_owned_fresh_context_'+kind if passed else 'unknown_or_failed','phase_kind':kind,
        'child_pid':child.pid if child else None,'child_exit':terminal,'child_reaped':child is not None and terminal is not None,
        'plan':pin(planpath),'root_activation':pin(HERE/plan['activation_basename']),
        'outcome':pin(HERE/cfg['outcome']) if outcome is not None else None,'supervisor_seconds_before_receipt_write':wall,
        'conservative_host_peak_bytes':own+childpeak,'kernel_child_peak_bytes':childpeak,'supervisor_peak_bytes':own,
        'resource_reason':reason,'watchdog_error':error,'rss_samples':samples,'wall_ceiling_seconds':ceiling,'host_ceiling_bytes':maximum,
        'OS_hard_limit_claim':False,'memory_scope':'sampled owned child RSS plus supervisor; retrospective own+child kernel peak; ps observer RSS omitted, not aggregate host upper bound',
        'native_queries':0,'new_training':False,'mathematical_acceptance':'pending separate fresh static or complete trace/logical gate'}
    save_json(HERE/cfg['supervision'],receipt);print(json.dumps({k:v for k,v in receipt.items() if k!='rss_samples'}),flush=True)
    return 0 if passed else 1
if __name__=='__main__':sys.exit(main())
