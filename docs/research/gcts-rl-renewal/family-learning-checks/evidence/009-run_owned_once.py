"""ROOT outer clock and exact child ownership, one numeric owner dispatch."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time

FOLDER = Path('.gcts-active/family-proposal-learning-numeric-source-20261012')
PROGRESS = Path('.gcts-active/family-numeric-actual-progress-20261012')

def pin(path):
    data = Path(path).read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

def main():
    begin = time.monotonic()
    assert not (PROGRESS / 'outer-terminal-v1.json').exists()
    plan_path = FOLDER / 'owner-plan-v1.json'
    plan = json.loads(plan_path.read_text())
    command = plan['prospective_command']
    assert pin(plan_path)['sha256'] == 'a9c41c98a38a9e03b658f27a9390fe14f66a261d94ceb5fc4e1ef033aa2fb5af'
    for key in ('numeric_output', 'owned_output'):
        assert not Path(plan[key]).exists(), 'No retry or output reuse'
    stdout = (PROGRESS / 'owner-stdout.bin').open('xb')
    stderr = (PROGRESS / 'owner-stderr.bin').open('xb')
    child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
    forced = False
    terminal = None
    try:
        while terminal is None:
            pid, status, usage = os.wait4(child.pid, os.WNOHANG)
            if pid:
                child.returncode = os.waitstatus_to_exitcode(status)
                terminal = (child.returncode, usage)
                break
            if time.monotonic() - begin > 35.0:
                os.killpg(child.pid, signal.SIGKILL)
                forced = True
            time.sleep(0.01)
    finally:
        if terminal is None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _, status, usage = os.wait4(child.pid, 0)
            child.returncode = os.waitstatus_to_exitcode(status)
            terminal = (child.returncode, usage)
            forced = True
        stdout.close()
        stderr.close()
    elapsed = time.monotonic() - begin
    receipt_path = Path(plan['owned_output']) / 'owned-lifetime.json'
    receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else None
    own_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # The child's receipt adds its functional worker and observer peaks. The
    # outer wait4 peak includes complete owner serialization; add the outer peak.
    combined = own_peak + terminal[1].ru_maxrss
    if receipt:
        combined += receipt['kernel_worker_peak_bytes'] + receipt['kernel_observer_maximum_peak_bytes']
    accepted = (terminal[0] == 0 and not forced and elapsed <= 30.0 and combined <= 536870912
                and receipt is not None and receipt['status'] == 'passed_owned_numeric_and_abstract_API_controls_only')
    result = {'status': 'passed_complete_numeric_fixture_lifecycle' if accepted else 'unknown_or_failed_numeric_fixture_lifecycle',
              'command': command, 'pid': child.pid, 'same_PID_terminal_and_reaped': True,
              'exit_code': terminal[0], 'forced_kill': forced,
              'full_seconds_including_owner_final_serialization_and_reaping': elapsed,
              'phase_limit_seconds': 30.0,
              'outer_kernel_peak_bytes': own_peak, 'owner_wait4_kernel_peak_bytes': terminal[1].ru_maxrss,
              'conservative_combined_peak_bytes': combined, 'memory_limit_bytes': 536870912,
              'owner_receipt': pin(receipt_path) if receipt else None,
              'activation': pin(FOLDER / 'owner-activation-v1.json'),
              'streams': [pin(PROGRESS / 'owner-stdout.bin'), pin(PROGRESS / 'owner-stderr.bin')],
              'scope': 'Numeric and abstract API controls only; no production engine, policy training, theorem search or RL benefit.'}
    with (PROGRESS / 'outer-terminal-v1.json').open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result))
    return 0 if accepted else 2

if __name__ == '__main__':
    raise SystemExit(main())
