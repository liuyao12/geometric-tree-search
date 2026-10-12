"""ROOT one-shot activation and full owner-exit/reap measurement.

No engine, fixture, replay or learning module is imported here. Source review
must precede activation. Scientific work occurs only in the frozen owned child.
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

ROOT = Path.cwd()
PROGRESS = ROOT / '.gcts-active/real-overlay-fixture-progress-20261012'
PHASES = {
    'producer': ('.gcts-active/family-proposal-real-overlay-source-20261012/fixture-plan-v2.json',
                 'e179fbbaec47518d3661c5faee24417c590cbd73ea0d52364f7e6e387298ae27',
                 'ROOT-real-Controller-overlay-fixture-activation-v1'),
    'independent': ('.gcts-active/family-rl-independent-review-20261012/actual-replay-plan-v1.json',
                    None, 'ROOT-independent-real-Controller-overlay-replay-activation-v1'),
}


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)) if ROOT in path.parents else str(path),
                sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


def write_new(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    started = time.monotonic()
    phase = sys.argv[1]
    relative, required_sha, activation_schema = PHASES[phase]
    plan_path = ROOT / relative
    plan_pin = pin(plan_path)
    if required_sha is not None:
        assert plan_pin['sha256'] == required_sha
    plan = json.loads(plan_path.read_text())
    review_path = PROGRESS / (phase + '-source-review-v2.json')
    review = json.loads(review_path.read_text())
    assert review['source_review_passed'] is True and review['full_sources_reviewed'] is True
    assert review['plan_pin'] == plan_pin
    unique = {}
    for record in plan['sources'] + plan['inputs'] + plan['preserved']:
        expected = {k:record[k] for k in ('path', 'sha256', 'bytes')}
        if record['path'] not in unique:
            actual = pin(ROOT / record['path'])
            actual['path'] = record['path']
            unique[record['path']] = actual
        assert unique[record['path']] == expected, record['path']
    for role in ('binary', 'observer'):
        assert pin(plan['runtime'][role]['path']) == plan['runtime'][role]
    assert Path(sys.executable).resolve() == Path(plan['runtime']['binary']['path']).resolve()
    assert plan['limits']['whole_ROOT_phase_seconds'] == 60
    assert plan['limits']['memory_bytes'] == 536870912
    activation_path = ROOT / plan['activation_path']
    terminal_path = PROGRESS / (phase + '-terminal-v2.json')
    assert not activation_path.exists() and not terminal_path.exists()
    assert all(not (ROOT / value).exists() for value in plan['outputs'].values())
    write_new(activation_path, dict(schema=activation_schema, authorized=True, plan=plan_pin,
        ROOT_source_review=pin(review_path), scope='One frozen bounded fixture phase; no theorem search, training or native query'))
    command = [plan['runtime']['executable'], '-B', str(ROOT / plan['owner_path']), str(plan_path)]
    stdout_path = PROGRESS / (phase + '-v2-outer-stdout.bin')
    stderr_path = PROGRESS / (phase + '-v2-outer-stderr.bin')
    child = None
    terminal = None
    cancelled = False
    forced_kill = False
    term_at = None
    with stdout_path.open('xb') as stdout, stderr_path.open('xb') as stderr:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout,
                                 stderr=stderr, start_new_session=True)
        try:
            while terminal is None:
                pid, status, usage = os.wait4(child.pid, os.WNOHANG)
                if pid:
                    child.returncode = os.waitstatus_to_exitcode(status)
                    terminal = child.returncode, usage
                    break
                now = time.monotonic()
                if now - started > 60 and term_at is None:
                    # The reviewed owner catches TERM and reaps its worker.
                    os.kill(child.pid, signal.SIGTERM)
                    cancelled = True
                    term_at = now
                if term_at is not None and now - term_at > 5:
                    os.kill(child.pid, signal.SIGKILL)
                    forced_kill = True
                    _, status, usage = os.wait4(child.pid, 0)
                    child.returncode = os.waitstatus_to_exitcode(status)
                    terminal = child.returncode, usage
                    break
                time.sleep(0.01)
        finally:
            if terminal is None:
                os.kill(child.pid, signal.SIGTERM)
                cancelled = True
                _, status, usage = os.wait4(child.pid, 0)
                child.returncode = os.waitstatus_to_exitcode(status)
                terminal = child.returncode, usage
    full_seconds = time.monotonic() - started
    lifetime_path = ROOT / plan['outputs']['lifetime']
    result_path = ROOT / plan['outputs']['result']
    life = json.loads(lifetime_path.read_text()) if lifetime_path.exists() else None
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss + max(
        terminal[1].ru_maxrss,
        max(life['conservative_combined_peak_bytes'], life['sampled_aggregate_peak_bytes']) if life else 0)
    accepted = bool(terminal[0] == 0 and not cancelled and not forced_kill and full_seconds <= 60
        and peak <= 536870912 and life and life['resource_gate_before_final_receipt'] is True
        and life['worker_terminal_reaped'] is True and life['worker_exit_code'] == 0
        and not life['forced_kill'] and life['remaining_owned_pids'] == [])
    receipt = dict(schema='ROOT-actual-real-Controller-overlay-fixture-terminal-v1' if phase == 'producer'
        else 'ROOT-actual-independent-real-Controller-overlay-replay-terminal-v1',
        status='passed_ROOT_full_owned_lifetime' if accepted else 'unknown_or_failed_ROOT_full_owned_lifetime',
        source_plan_pin=plan_pin, source_review_pin=pin(review_path), activation_pin=pin(activation_path),
        result_pin=pin(result_path) if result_path.exists() else None,
        owned_lifetime_pin=pin(lifetime_path) if life else None,
        owner_pid=child.pid, owner_exit_code=terminal[0], owner_terminal_reaped=True,
        worker_terminal_reaped=bool(life and life['worker_terminal_reaped']),
        full_owner_lifetime_seconds=full_seconds, conservative_combined_peak_bytes=peak,
        full_resource_accepted=accepted, cancelled=cancelled, forced_kill=forced_kill,
        memory_scope='ROOT peak plus max direct owner peak or owned owner/worker/observer estimate; retrospective gate, not hard OS cap',
        command=command, stdout_pin=pin(stdout_path), stderr_pin=pin(stderr_path),
        mathematical_proofs_accepted=0, training_runs=0, native_queries=0)
    write_new(terminal_path, receipt)
    print(json.dumps(receipt), flush=True)
    return 0 if accepted else 2


if __name__ == '__main__':
    raise SystemExit(main())
