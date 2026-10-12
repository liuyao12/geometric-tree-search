"""One root-dispatched family-preparation owner; fail-closed owned-child sampler.

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
SECONDS, BYTES = 65, 536870912


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
    planpath = HERE / 'preparation-plan-v2.json'
    plan = json.loads(planpath.read_text())
    for p in plan['sources'] + plan['inputs'] + plan['preserved_files']:
        if pin(ROOT / p['path']) != {k: p[k] for k in ('path', 'sha256', 'bytes')}:
            raise ValueError('frozen family preparation prerequisite changed: ' + p['path'])
    activation = json.loads((HERE / 'root-preparation-activation-v2.json').read_text())
    if (activation['status'] != 'root_authorized_bounded_family_proposal_preparation_only'
            or activation['plan'] != pin(planpath)):
        raise ValueError('reviewed root activation binding required before launch')
    for name in plan['proposed_outputs']:
        if (HERE / name).exists(): raise ValueError('immutable prior preparation artifact exists: ' + name)
    child, terminal, reason, error, samples = None, None, None, None, []
    try:
        with (HERE / 'preparation-stdout-v2.txt').open('xb') as out, (HERE / 'preparation-stderr-v2.txt').open('xb') as err:
            child = subprocess.Popen([sys.executable, str(HERE / 'family_preparation_worker_v2.py')],
                                     cwd=HERE, stdout=out, stderr=err)
            save('preparation-launch-v2.json', {'pid': child.pid, 'plan': pin(planpath),
                 'scope': 'complete bounded single/pair proposal preparation only; no controller/executor/search',
                 'wall_ceiling_seconds': SECONDS, 'host_ceiling_bytes': BYTES,
                 'maximum_geometry_searches': 0, 'native_queries': 0, 'new_training': False})
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
        outcome = json.loads((HERE / 'preparation-outcome-v2.json').read_text())
    except BaseException as exc:
        reason = reason or 'missing_or_invalid_child_receipt'; error = error or str(exc)
    own, childpeak = peak(resource.RUSAGE_SELF), peak(resource.RUSAGE_CHILDREN)
    wall = time.perf_counter() - started
    if own + childpeak > BYTES: reason = reason or 'final_kernel_peak_ceiling'
    if wall > SECONDS: reason = reason or 'final_wall_ceiling'
    if not samples: reason = reason or 'no_owned_external_RSS_sample'
    if outcome is not None:
        if (outcome['status'] not in ('complete_declared_proposal_grammar_prepared_pending_independent_audit', 'unknown_preparation_budget')
                or outcome['target_searches'] != 0 or outcome['logical_checker_runs'] != 0
                or outcome['point_certificates'] != 0 or outcome['native_queries'] != 0
                or outcome['native_authority_activated'] is not False or outcome['new_RL_training'] is not False):
            reason = reason or 'unexpected_child_scope_or_status'
        if outcome['worker_seconds_before_receipt_write'] > 60:
            reason = reason or 'worker_wall_ceiling'
        if pin(ROOT / outcome['evidence']['path']) != outcome['evidence']:
            reason = reason or 'evidence_output_pin_mismatch'
    passed = terminal == 0 and reason is None and outcome is not None
    receipt = {'status': 'passed_bounded_family_preparation_resource_phase' if passed else 'unknown_or_failed',
        'pid': child.pid if child else None, 'exit_code': terminal,
        'owned_child_terminal_wait_reaped': child is not None and terminal is not None,
        'supervisor_seconds_before_receipt_write': wall, 'wall_ceiling_seconds': SECONDS, 'host_ceiling_bytes': BYTES,
        'kernel_child_peak_bytes': childpeak, 'supervisor_peak_bytes': own,
        'conservative_host_peak_bytes': own + childpeak, 'rss_samples': samples,
        'resource_reason': reason, 'watchdog_error': error,
        'enforcement': 'task-owned external sampled RSS/time watchdog, child SIGALRM, final kernel peak rejection',
        'OS_soft_limit_claim': 'none', 'plan': pin(planpath), 'root_activation': pin(HERE / 'root-preparation-activation-v2.json'),
        'outcome': pin(HERE / 'preparation-outcome-v2.json') if outcome is not None else None,
        'actual_geometry_model_execution': child is not None, 'maximum_geometry_target_searches': 0,
        'native_queries': 0, 'native_authority_activated': False, 'new_training': False,
        'preparation_status': outcome['status'] if outcome else None, 'preparation_complete': bool(outcome and outcome['status'].startswith('complete_')),
        'mathematical_acceptance': 'none; independent pool audit pending' }
    save('preparation-supervision-v2.json', receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k != 'rss_samples'}), flush=True)
    return 0 if passed else 1


if __name__ == '__main__': sys.exit(main())
