"""ROOT-only full phase lifetime. Frozen outputs, fail-closed child cleanup."""
import json
import resource
import subprocess
import sys
import time
from transfer_runtime_v1 import HERE,read,pin,verify,activation,save_json

def peak(kind):return resource.getrusage(kind).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
def main():
    start=time.perf_counter();planpath=HERE/sys.argv[1]
    if planpath.name not in ('preparation-plan-v1.json','search-plan-v1.json'):raise ValueError('declared exact phase plan only')
    plan=read(planpath);verify(plan);activation(plan,planpath);cfg=plan['phase'];maximum=cfg['bytes'];outer=cfg['outer_seconds']
    if maximum!=536870912 or (cfg['kind']=='preparation' and outer!=60) or (cfg['kind']=='search' and outer!=180):raise ValueError('exact fixed ROOT lifetime gate')
    if (HERE/cfg['lifetime']).exists():raise ValueError('immutable owned lifetime exists')
    child=subprocess.Popen([sys.executable,str(HERE/'transfer_supervisor_v1.py'),planpath.name],cwd=HERE)
    reason=None
    try:terminal=child.wait(timeout=max(.01,outer-(time.perf_counter()-start)-2))
    except subprocess.TimeoutExpired:
        reason='outer_cutoff';child.terminate()
        try:terminal=child.wait(timeout=3)
        except subprocess.TimeoutExpired:
            child.kill();terminal=child.wait();reason='unresponsive_supervisor_owned_worker_reap_not_confirmed'
    wall=time.perf_counter()-start;inner=read(HERE/cfg['supervision']) if (HERE/cfg['supervision']).exists() else None
    own=peak(resource.RUSAGE_SELF);children=peak(resource.RUSAGE_CHILDREN);conservative=own+max(children,inner['conservative_host_peak_bytes'] if inner else 0)
    passed=(terminal==0 and reason is None and inner is not None and inner['status']=='passed_owned_fresh_context_'+cfg['kind'] and inner['child_reaped'] and wall<=outer and conservative<=maximum)
    receipt={'status':'passed_full_fresh_context_'+cfg['kind']+'_lifetime' if passed else 'unknown_or_failed',
        'plan':pin(planpath),'phase_kind':cfg['kind'],'supervision':pin(HERE/cfg['supervision']) if inner else None,
        'supervisor_pid':child.pid,'supervisor_exit':terminal,'supervisor_reaped':True,'worker_reaped_confirmed':bool(inner and inner['child_reaped']),
        'full_supervisor_seconds_including_receipt_write':wall,'outer_receipt_write':'outside pre-write interval; ROOT should also time full outer process',
        'conservative_host_peak_bytes':conservative,'host_ceiling_bytes':maximum,'wall_ceiling_seconds':outer,
        'cleanup_reason':reason,'actual_memory_overshoot_bytes':max(0,conservative-maximum),'actual_wall_overshoot_seconds':max(0,wall-outer),
        'memory_scope':'retrospective owned-process peak estimate; no OS hard cap or strict aggregate host upper bound',
        'native_queries':0,'training_runs':0,'scope':'producer resource receipt only; no mathematical acceptance'}
    save_json(HERE/cfg['lifetime'],receipt);print(json.dumps(receipt),flush=True);return 0 if passed else 1
if __name__=='__main__':sys.exit(main())
