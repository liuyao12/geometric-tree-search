"""ROOT one-shot static phase: exact preflight, activation and full owned clock."""
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
FOLDER = ROOT / '.gcts-active/fixed-family-transfer-independent-source-20261012'
OUT = ROOT / '.gcts-active/fixed-family-transfer-progress-20261012'


def pin(path):
    path = Path(path)
    data = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


def main():
    started = time.perf_counter()
    planpath = FOLDER / 'static-audit-plan-v1.json'
    planpin = pin(planpath)
    assert planpin['sha256'] == '43d8ae0fd11ff5616885b77d975dc6d9c85fadf9d4a5125e82ce710779e3bba6'
    plan = json.loads(planpath.read_text())
    reviewpath = OUT / 'static-audit-source-review-v1.json'
    review = json.loads(reviewpath.read_text())
    assert review['status'] == 'passed_ROOT_source_and_exact_metadata_review_for_static_stage_only'
    assert review['plan']['sha256'] == planpin['sha256']
    assert plan['stage'] == 'static'
    assert plan['limits'] == dict(whole_seconds=180, supervisor_seconds=175, child_seconds=170, peak_bytes=536870912)
    unique = {}
    for record in plan['sources'] + plan['libraries'] + plan['inputs'] + plan['preserved']:
        path = Path(record['path'])
        if str(path) not in unique:
            value = pin(path)
            value['path'] = str(path)
            unique[str(path)] = value
        assert unique[str(path)] == {key: record[key] for key in ('path', 'sha256', 'bytes')}, str(path)
    assert len(unique) == 855
    for role in ('binary', 'observer'):
        record = plan['runtime'][role]
        value = pin(record['path']); value['path'] = record['path']
        assert value == record
    terminalpath = OUT / 'static-audit-terminal-v1.json'
    activationpath = Path(plan['activation_path'])
    assert not terminalpath.exists() and not activationpath.exists()
    assert all(not Path(path).exists() for path in plan['outputs'].values())
    activation = dict(schema=plan['required_activation_schema'], authorized=True,
                      plan=planpin, source_review=pin(reviewpath),
                      scope='One static audit only; no search, training or target-proof acceptance.')
    with activationpath.open('x') as stream:
        json.dump(activation, stream, indent=2, allow_nan=False); stream.write('\n')
    command = [plan['runtime']['executable'], '-B', str(FOLDER / 'transfer_independent_owner_v1.py'), str(planpath)]
    stdoutpath = OUT / 'static-audit-outer-stdout.bin'
    stderrpath = OUT / 'static-audit-outer-stderr.bin'
    stdout = stdoutpath.open('xb'); stderr = stderrpath.open('xb')
    child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True)
    terminal = None; killed = False
    try:
        while terminal is None:
            pid, status, usage = os.wait4(child.pid, os.WNOHANG)
            if pid:
                child.returncode = os.waitstatus_to_exitcode(status)
                terminal = (child.returncode, usage)
                break
            if time.perf_counter() - started > plan['limits']['whole_seconds'] + 5 and not killed:
                os.killpg(child.pid, signal.SIGKILL); killed = True
            time.sleep(.02)
    finally:
        if terminal is None:
            try: os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            _, status, usage = os.wait4(child.pid, 0)
            child.returncode = os.waitstatus_to_exitcode(status)
            terminal = (child.returncode, usage); killed = True
        stdout.close(); stderr.close()
    full = time.perf_counter() - started
    lifepath = Path(plan['outputs']['lifetime'])
    life = json.loads(lifepath.read_text()) if lifepath.exists() else None
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss + max(
        terminal[1].ru_maxrss,
        max(life['kernel_conservative_peak_bytes'], life['sampled_combined_peak_bytes']) if life else 0)
    accepted = bool(terminal[0] == 0 and not killed and full <= 180 and peak <= 536870912
                    and life and life['status'] == plan['required_owner_success_status']
                    and life['child_reaped'] and life['static_context_pool_accepted'])
    receipt = dict(status='passed_ROOT_full_static_audit_lifetime' if accepted else 'unknown_or_failed_ROOT_full_static_audit',
                   plan=planpin, activation=pin(activationpath), source_review=pin(reviewpath),
                   command=command, owner_pid=child.pid, owner_exit_code=terminal[0],
                   owner_process_terminal_reaped=True, worker_reaped=bool(life and life['child_reaped']),
                   forced_kill=killed, full_phase_seconds_including_owner_final_write_and_reaping=full,
                   outer_time_gate_seconds=180, conservative_owned_peak_bytes=peak,
                   memory_scope='ROOT peak plus maximum direct-owner kernel peak or owner conservative child/observer estimate; retrospective gate, no hard OS cap.',
                   lifetime=pin(lifepath) if life else None,
                   result=pin(plan['outputs']['result']) if Path(plan['outputs']['result']).exists() else None,
                   stdout=pin(stdoutpath), stderr=pin(stderrpath), static_context_pool_accepted=accepted,
                   target_proof_accepted=False, theorem_searches=0, training_runs=0, native_queries=0)
    with terminalpath.open('x') as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps(receipt), flush=True)
    return 0 if accepted else 2


if __name__ == '__main__':
    sys.exit(main())
