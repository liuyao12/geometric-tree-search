"""Root-authorized pure AST child only; ten-second owner/five-second child gate."""
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes': path.stat().st_size}


def peak_bytes(usage):
    return int(usage.ru_maxrss) * (1 if sys.platform == 'darwin' else 1024)


def main():
    started = time.perf_counter()
    plan = json.loads((HERE / 'pure-ast-plan-v1.json').read_text())
    for entry in plan['sources'] + plan['inputs']:
        if pin(ROOT / entry['path']) != {k: entry[k] for k in ('path', 'sha256', 'bytes')}:
            raise ValueError('pure AST freeze changed')
    if any((HERE / name).exists() for name in ('pure-ast-lifetime-v1.json', 'pure-ast-outcome-v1.json',
                                              'pure-ast-stdout-v1.txt', 'pure-ast-stderr-v1.txt')):
        raise ValueError('immutable pure gate output already exists')
    child = None; usage = None; terminal = None; status = 'unknown_pure_AST_owner_failure'
    failure = None
    with (HERE / 'pure-ast-stdout-v1.txt').open('xb') as out, (HERE / 'pure-ast-stderr-v1.txt').open('xb') as err:
        try:
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            child = subprocess.Popen([sys.executable, str(HERE / 'pure_ast_fixtures_v1.py')], stdout=out, stderr=err, env=env)
            while True:
                pid, waitstatus, used = os.wait4(child.pid, os.WNOHANG)
                if pid:
                    terminal = os.waitstatus_to_exitcode(waitstatus); usage = used
                    child.returncode = terminal
                    break
                if time.perf_counter() - started >= 10:
                    raise TimeoutError('ten-second pure-AST owner deadline')
                time.sleep(0.01)
        except BaseException as exc:
            failure = type(exc).__name__ + ': ' + str(exc)
        finally:
            if child is not None and terminal is None:
                try:
                    os.kill(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                pid, waitstatus, usage = os.wait4(child.pid, 0)
                terminal = os.waitstatus_to_exitcode(waitstatus); child.returncode = terminal
    elapsed = time.perf_counter() - started
    own_peak = peak_bytes(resource.getrusage(resource.RUSAGE_SELF))
    child_peak = peak_bytes(usage) if usage is not None else None
    conservative_peak = own_peak + child_peak if child_peak is not None else None
    if failure is None and terminal == 0 and elapsed <= 10 and conservative_peak <= 536870912:
        outcome = json.loads((HERE / 'pure-ast-outcome-v1.json').read_text())
        if outcome['status'] == 'passed_bounded_pure_AST_matcher_controls':
            status = 'passed_bounded_pure_AST_owner_gate'
    lifetime = {'status': status, 'plan': pin(HERE / 'pure-ast-plan-v1.json'),
        'child_pid': child.pid if child is not None else None, 'child_exit_code': terminal,
        'child_wait_reaped': terminal is not None, 'failure': failure,
        'full_child_and_owner_seconds_before_final_receipt_write': elapsed,
        'owner_kernel_peak_bytes': own_peak, 'child_kernel_peak_bytes': child_peak,
        'conservative_host_peak_bytes': conservative_peak,
        'limits': {'owner_seconds': 10, 'child_SIGALRM_seconds': 5, 'host_bytes': 536870912},
        'enforcement': 'Owned wait4 deadline/kill/reap, child SIGALRM, final child+owner kernel-peak validation; no OS soft-memory limit or live RSS sampler claimed.',
        'outcome': pin(HERE / 'pure-ast-outcome-v1.json') if (HERE / 'pure-ast-outcome-v1.json').exists() else None,
        'stdout': pin(HERE / 'pure-ast-stdout-v1.txt'), 'stderr': pin(HERE / 'pure-ast-stderr-v1.txt'),
        'actual_models': 0, 'engine_imports': 0, 'searches': 0, 'native_queries': 0, 'new_training': 0}
    with (HERE / 'pure-ast-lifetime-v1.json').open('x') as stream:
        stream.write(json.dumps(lifetime, indent=2, allow_nan=False) + '\n')
    print(json.dumps(lifetime))
    if status != 'passed_bounded_pure_AST_owner_gate':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
