"""One root-dispatched automatic geometry owner; fail-closed owned-child sampler.

No OS soft limit is claimed. The external sampled RSS/time watchdog, child alarm
and retrospective fresh-process kernel peaks decide the finite resource gate.
"""
import hashlib
import json
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SECONDS, BYTES = 175, 536870912


def peak(kind):
    return resource.getrusage(kind).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)


def pin(path):
    path = Path(path); h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''): h.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest(), 'bytes': path.stat().st_size}


def save(name, data):
    with (HERE / name).open('x') as stream:
        stream.write(json.dumps(data, indent=2, allow_nan=False) + '\n')


def alarm(*_):
    raise TimeoutError('owned supervisor full wall alarm')


def main():
    started = time.perf_counter()
    signal.signal(signal.SIGALRM, alarm); signal.alarm(SECONDS)
    # A terminated supervisor must unwind the owned child wait/finally below.
    signal.signal(signal.SIGTERM, alarm)
    planpath = HERE / 'search-plan-v1.json'
    plan = json.loads(planpath.read_text())
    for p in plan['sources'] + plan['inputs'] + plan['preserved_files']:
        if pin(ROOT / p['path']) != {k: p[k] for k in ('path', 'sha256', 'bytes')}:
            raise ValueError('frozen automatic search prerequisite changed: ' + p['path'])
    activation = json.loads((HERE / 'root-activation-v1.json').read_text())
    if (activation['status'] != 'root_authorized_bounded_automatic_primitive_geometry_search'
            or activation['plan'] != pin(planpath)):
        raise ValueError('reviewed root activation binding required before launch')
    for name in plan['proposed_outputs']:
        if (HERE / name).exists(): raise ValueError('immutable prior scientific artifact exists: ' + name)
    child, terminal, reason, error, samples = None, None, None, None, []
    try:
        with (HERE / 'search-stdout-v1.txt').open('xb') as out, (HERE / 'search-stderr-v1.txt').open('xb') as err:
            child = subprocess.Popen([sys.executable, str(HERE / 'shared_symbolic_geometry_search_v1.py')],
                                     cwd=HERE, stdout=out, stderr=err)
            save('search-launch-v1.json', {'pid': child.pid, 'plan': pin(planpath),
                 'scope': 'two bounded automatic primitive geometry searches; complete inventory; no cluster hints',
                 'wall_ceiling_seconds': SECONDS, 'host_ceiling_bytes': BYTES,
                 'maximum_geometry_searches': 2, 'native_queries': 0, 'new_training': False})
            try:
                while child.poll() is None:
                    elapsed = time.perf_counter() - started
                    if elapsed >= SECONDS: reason = 'wall_ceiling'; break
                    ps = subprocess.run(['/bin/ps', '-o', 'rss=', '-p', str(child.pid)],
                                        capture_output=True, timeout=min(2, max(.01, SECONDS - elapsed)), check=False)
                    raw = ps.stdout.strip()
                    if ps.returncode == 0 and raw:
                        rss = int(raw) * 1024
                        if rss < 0: raise ValueError('negative owned child RSS')
                        own = peak(resource.RUSAGE_SELF)
                        samples.append({'seconds': elapsed, 'child_rss_bytes': rss, 'supervisor_peak_bytes': own})
                        if rss + own > BYTES: reason = 'sampled_host_ceiling'; break
                    elif child.poll() is None:
                        raise RuntimeError('owned child metadata unavailable: ' + ps.stderr.decode(errors='replace'))
                    time.sleep(.02)
            except BaseException as exc:
                reason, error = 'watchdog_failure', type(exc).__name__ + ': ' + str(exc)
            finally:
                # Disarm only after the watchdog loop. The final retrospective
                # clock gate includes cleanup and rejects any genuine overshoot.
                signal.alarm(0)
                if reason is not None and child.poll() is None: child.kill()
                terminal = child.wait()
    except BaseException as exc:
        signal.alarm(0)
        reason = reason or 'supervision_failure'; error = error or type(exc).__name__ + ': ' + str(exc)
        if child is not None:
            if child.poll() is None: child.kill()
            terminal = child.wait()
    signal.alarm(0)
    outcome = None
    try:
        outcome = json.loads((HERE / 'search-outcome-v1.json').read_text())
    except BaseException as exc:
        reason = reason or 'missing_or_invalid_child_receipt'; error = error or str(exc)
    own, childpeak = peak(resource.RUSAGE_SELF), peak(resource.RUSAGE_CHILDREN)
    wall = time.perf_counter() - started
    if own + childpeak > BYTES: reason = reason or 'final_kernel_peak_ceiling'
    if wall > SECONDS: reason = reason or 'final_wall_ceiling'
    if not samples: reason = reason or 'no_owned_external_RSS_sample'
    if outcome is not None:
        if (outcome['status'] != 'completed_bounded_automatic_primitive_geometry_observations_pending_independent_audit'
                or outcome['target_search_observations'] != 2 or outcome['native_queries'] != 0
                or outcome['native_authority_activated'] is not False or outcome['new_RL_training'] is not False):
            reason = reason or 'unexpected_child_scope_or_status'
        for observation in outcome['observations']:
            if pin(ROOT / observation['result']['path']) != observation['result']:
                reason = reason or 'observation_output_pin_mismatch'
    passed = terminal == 0 and reason is None and outcome is not None
    receipt = {'status': 'passed_bounded_automatic_primitive_geometry_observations' if passed else 'unknown_or_failed',
        'pid': child.pid if child else None, 'exit_code': terminal,
        'owned_child_terminal_wait_reaped': child is not None and terminal is not None,
        'supervisor_seconds_before_receipt_write': wall, 'wall_ceiling_seconds': SECONDS, 'host_ceiling_bytes': BYTES,
        'kernel_child_peak_bytes': childpeak, 'supervisor_peak_bytes': own,
        'conservative_host_peak_bytes': own + childpeak, 'rss_samples': samples,
        'resource_reason': reason, 'watchdog_error': error,
        'enforcement': 'task-owned external sampled RSS/time watchdog, child SIGALRM, final kernel peak rejection',
        'OS_soft_limit_claim': 'none', 'plan': pin(planpath), 'root_activation': pin(HERE / 'root-activation-v1.json'),
        'outcome': pin(HERE / 'search-outcome-v1.json') if outcome is not None else None,
        'actual_geometry_model_execution': child is not None, 'maximum_geometry_target_searches': 2,
        'native_queries': 0, 'native_authority_activated': False, 'new_training': False,
        'mathematical_acceptance': 'pending separately owned complete trace and symbolic certificate audit'}
    save('search-supervision-v1.json', receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != 'rss_samples'}), flush=True)
    return 0 if passed else 1


if __name__ == '__main__': sys.exit(main())
