"""ROOT external process clock, terminal reap and launcher-envelope audit.

No scientific imports/calls. Frozen dispatcher owns the one actual child phase.
After full dispatcher exit/reap, require its stored prospective envelope to
cover complete Python startup/import/final-write/exit and launcher peak.
No normalized accepted path survives failed external envelope validation.
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    path = Path(path); raw = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def main():
    phase, selector = sys.argv[1:]
    if phase not in ('preparation', 'static') or selector not in (
        'donor-two-guards','donor-two-equalities','donor-repeated-guard',
        'donor-repeated-equality','heldout-mixed-guard-equality'):
        raise ValueError('literal one-shot frozen phase and selector')
    stem = phase + '-' + selector
    receipt_path = HERE/(stem+'-external-launcher-v1.json')
    if receipt_path.exists():
        raise ValueError('immutable external launch receipt exists; no retry')
    dispatcher = HERE/'run_owned_context_gate_v3.py'
    began = time.perf_counter()
    child = None; interrupted = None
    def stop(*_):
        raise TimeoutError('external launcher interrupted')
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    try:
        child = subprocess.Popen([sys.executable,'-B',str(dispatcher),phase,selector],cwd=ROOT,
            stdin=subprocess.DEVNULL,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        _, status, usage = os.wait4(child.pid,0)
    except BaseException as exc:
        interrupted = dict(type=type(exc).__name__,message=str(exc))
        signal.signal(signal.SIGTERM,signal.SIG_IGN); signal.signal(signal.SIGINT,signal.SIG_IGN)
        if child is None: raise
        try: os.kill(child.pid,signal.SIGTERM)
        except ProcessLookupError: pass
        # Dispatcher handles TERM, stops its owned descendants, and reaps.
        # Its exact frozen own deadline also continues; no second launch.
        _, status, usage = os.wait4(child.pid,0)
    child.returncode = os.waitstatus_to_exitcode(status)
    full = time.perf_counter()-began
    terminal_path = HERE/(stem+'-ROOT-terminal-v1.json')
    observation_path = HERE/(stem+'-post-write-observation-v1.json')
    observation = json.loads(observation_path.read_text()) if observation_path.exists() else None
    terminal = json.loads(terminal_path.read_text()) if terminal_path.exists() else None
    own_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    dispatcher_peak = usage.ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    complete_peak = (observation['conservative_peak_after_receipt_serialization_bytes']+own_peak
        +max(0,dispatcher_peak-observation['peak_after_receipt_serialization_bytes'])) if observation else None
    accepted = bool(interrupted is None and child.returncode==0 and terminal and observation
        and observation['accepted_for_metadata_finalization'] is True
        and observation['terminal']==pin(terminal_path)
        and full<=terminal['full_outer_seconds_including_receipt_write']<=terminal['maximum_seconds']
        and complete_peak<=terminal['conservative_combined_peak_bytes']<=terminal['maximum_bytes'])
    rejected_path = None
    if terminal_path.exists() and not accepted:
        rejected_path = HERE/(stem+'-externally-rejected-ROOT-terminal-v1.json')
        if rejected_path.exists(): raise ValueError('immutable rejected receipt exists')
        os.rename(terminal_path,rejected_path)
    receipt = dict(schema='ROOT-context-gate-external-launcher-observation-v1',
        phase=phase,selector=selector,accepted_for_metadata_finalization=accepted,
        dispatcher=pin(dispatcher),launcher=pin(Path(__file__)),owner_pid=child.pid,
        owner_exit_code=child.returncode,owner_terminal_reaped=True,interruption=interrupted,
        full_dispatcher_process_seconds_including_startup_imports_final_write_exit_reap=full,
        launcher_peak_bytes=own_peak,dispatcher_kernel_peak_bytes=dispatcher_peak,
        observer_inclusive_phase_plus_launcher_peak_estimate_bytes=complete_peak,
        terminal=pin(terminal_path) if accepted else None,
        post_write_observation=pin(observation_path) if observation else None,
        rejected_terminal=pin(rejected_path) if rejected_path else None,
        receipt_scope='External launcher imports and this metadata receipt serialization/exit are additional; full actual dispatcher lifetime and simultaneous launcher peak are covered by validated frozen terminal envelope.',
        scientific_calls_by_launcher=0)
    with receipt_path.open('x') as stream:
        json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(external_launcher=pin(receipt_path),accepted=accepted,
        actual_full_dispatcher_seconds=full,actual_complete_peak_estimate_bytes=complete_peak)),flush=True)
    return 0 if accepted else 1


if __name__=='__main__':
    sys.exit(main())
