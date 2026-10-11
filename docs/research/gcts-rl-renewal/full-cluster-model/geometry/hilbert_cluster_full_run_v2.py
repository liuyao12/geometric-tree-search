"""ONE root-dispatched actual controlled phase; task-owned fail-closed child watchdog."""
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SECONDS, BYTES = 175, 536870912


def peak(kind):
    return resource.getrusage(kind).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)


def save(name, data):
    path = HERE / name
    if path.exists(): raise ValueError('immutable artifact already exists: ' + name)
    path.write_text(json.dumps(data, indent=2) + '\n')


def main():
    started = time.perf_counter()
    planpath = HERE / 'full-language-plan-v2.json'; plan = json.loads(planpath.read_text())
    for p in plan['sources'] + plan['inputs'] + plan['preserved_files']:
        path = ROOT / p['path']; h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(65536), b''): h.update(block)
        if path.stat().st_size != p['bytes'] or h.hexdigest() != p['sha256']:
            raise ValueError('frozen source/input changed: ' + p['path'])
    for name in ('full-language-outcome-v2.json', 'full-language-launch-v2.json', 'full-language-supervision-v2.json',
                 'full-language-stdout-v2.txt', 'full-language-stderr-v2.txt'):
        if (HERE/name).exists(): raise ValueError('immutable prior execution exists')
    child, terminal, reason, error, samples = None, None, None, None, []
    try:
        with (HERE/'full-language-stdout-v2.txt').open('xb') as out, (HERE/'full-language-stderr-v2.txt').open('xb') as err:
            child = subprocess.Popen([sys.executable, str(HERE/'hilbert_cluster_full_v2.py')],
                                     cwd=HERE, stdout=out, stderr=err)
            save('full-language-launch-v2.json', {'pid': child.pid, 'scope':'actual full-language controlled transactions; no target DFS',
                 'wall_ceiling_seconds':SECONDS, 'host_ceiling_bytes':BYTES,
                 'actual_model_loads':1, 'native_queries':0})
            try:
                while child.poll() is None:
                    elapsed = time.perf_counter()-started
                    if elapsed > SECONDS: reason='wall_ceiling'; break
                    ps = subprocess.run(['/bin/ps','-o','rss=','-p',str(child.pid)], capture_output=True,
                                        timeout=min(2,max(.01,SECONDS-elapsed)), check=False)
                    raw = ps.stdout.strip()
                    if ps.returncode == 0 and raw:
                        rss = int(raw)*1024
                        if rss < 0: raise ValueError('negative RSS')
                        own = peak(resource.RUSAGE_SELF)
                        samples.append({'seconds':elapsed,'child_rss_bytes':rss,'supervisor_peak_bytes':own})
                        if rss+own > BYTES: reason='sampled_host_ceiling'; break
                    elif child.poll() is None:
                        raise RuntimeError('owned child metadata unavailable: '+ps.stderr.decode(errors='replace'))
                    time.sleep(.02)
            except BaseException as exc:
                reason,error='watchdog_failure',type(exc).__name__+': '+str(exc)
            finally:
                if reason is not None and child.poll() is None: child.kill()
                terminal=child.wait()
    except BaseException as exc:
        reason=reason or 'supervision_failure'; error=error or type(exc).__name__+': '+str(exc)
        if child is not None:
            if child.poll() is None: child.kill()
            terminal=child.wait()
    outcome=None
    try: outcome=json.loads((HERE/'full-language-outcome-v2.json').read_text())
    except BaseException as exc:
        reason=reason or 'missing_or_invalid_child_receipt'; error=error or str(exc)
    own,childpeak=peak(resource.RUSAGE_SELF),peak(resource.RUSAGE_CHILDREN)
    wall=time.perf_counter()-started
    if childpeak+own > BYTES: reason=reason or 'final_kernel_peak_ceiling'
    if wall > SECONDS: reason=reason or 'final_wall_ceiling'
    if not samples: reason=reason or 'no_owned_external_RSS_sample'
    if outcome is not None and outcome['status']!='passed_authored_full_language_lifecycle_controls_pending_independent_audit':
        reason=reason or 'unexpected_child_status'
    passed=terminal==0 and reason is None and outcome is not None
    receipt={'status':'passed_bounded_authored_full_language_lifecycle' if passed else 'unknown_or_failed',
             'pid':child.pid if child else None,'exit_code':terminal,
             'owned_child_terminal_wait_reaped':child is not None and terminal is not None,
             'supervisor_seconds_before_receipt_write':wall,'wall_ceiling_seconds':SECONDS,
             'host_ceiling_bytes':BYTES,'kernel_child_peak_bytes':childpeak,'supervisor_peak_bytes':own,
             'conservative_host_peak_bytes':own+childpeak,'rss_samples':samples,
             'resource_reason':reason,'watchdog_error':error,
             'enforcement':'task-owned external sampled RSS/time watchdog, child SIGALRM, final kernel peak rejection',
             'OS_soft_limit_claim':'none','plan_sha256':hashlib.sha256(planpath.read_bytes()).hexdigest(),
             'actual_geometry_model_execution':True,'geometry_target_searches':0,'native_queries':0,
             'native_authority_activated':False,'independent_lifecycle_audit':'not_run'}
    save('full-language-supervision-v2.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='rss_samples'}),flush=True)
    return 0 if passed else 1

if __name__=='__main__': sys.exit(main())
