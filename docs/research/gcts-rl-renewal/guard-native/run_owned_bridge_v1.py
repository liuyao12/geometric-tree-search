"""One-shot ROOT owner, metadata/resource supervision only; no project imports.

Only frozen preparation/query/replay workers may run. Receipt publication has
a prospective two-second reserve and a separate post-write observation. RSS
sampling is supplemented by conservative kernel peaks; no hard OS limit is
claimed. Process ownership includes birth identity and the fresh child group.
"""
import hashlib
import gzip
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def need(value, label):
    if not value:
        raise ValueError(label)

def peak(usage):
    return usage.ru_maxrss * (1 if sys.platform == 'darwin' else 1024)

def pin(path):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    h = hashlib.sha256(); size = 0
    before = p.stat()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); size += len(block)
    after = p.stat()
    need((before.st_dev,before.st_ino,before.st_mtime_ns,before.st_size) ==
         (after.st_dev,after.st_ino,after.st_mtime_ns,after.st_size), 'immutable frozen bytes')
    try: name = str(p.relative_to(ROOT))
    except ValueError: name = str(p)
    return dict(path=name, sha256=h.hexdigest(), bytes=size)

def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')

def table():
    out = subprocess.run(['/bin/ps','-axo','pid=,ppid=,pgid=,rss=,lstart='],
                         capture_output=True, text=True, timeout=2, check=True)
    rows = {}
    for line in out.stdout.splitlines():
        fields = line.split()
        if len(fields) == 9:
            pid,ppid,pgid,rss = map(int,fields[:4])
            rows[pid] = dict(ppid=ppid,pgid=pgid,rss_bytes=rss*1024,birth=' '.join(fields[4:]))
    return rows

def collect(rows, leader, owned, leader_live=False):
    identities = {pid:birth for pid,birth in owned.items()
                  if pid in rows and rows[pid]['birth'] == birth}
    if leader_live and leader in rows:
        identities[leader] = rows[leader]['birth']
    allow_group = leader_live or any(rows[pid]['pgid'] == leader for pid in identities)
    while True:
        new = {pid:row['birth'] for pid,row in rows.items()
               if row['ppid'] in identities or (allow_group and row['pgid'] == leader)}
        changed = any(pid not in identities for pid in new)
        identities.update(new)
        if not changed:
            owned.update(identities)
            return identities

def kill_owned(rows, leader, owned, sig, leader_live=False):
    active = collect(rows,leader,owned,leader_live)
    for pid,birth in active.items():
        if pid in rows and rows[pid]['birth'] == birth:
            try: os.kill(pid,sig)
            except ProcessLookupError: pass

def main():
    began = time.perf_counter()
    need(len(sys.argv) == 2, 'one frozen plan')
    path = Path(sys.argv[1]).resolve()
    plan = json.loads(path.read_bytes())
    need(plan['schema'] == 'ROOT-guard-native-owned-plan-v1' and
         plan['stage'] in ('translation','preparation','native','replay'), 'literal frozen stage')
    need(path.parent == HERE, 'owned plan namespace')
    review = json.loads((HERE/'ROOT-source-review-v1.json').read_bytes())
    need(review['source_review_passed'] and review['scientific_calls'] == 0, 'prior ROOT source review')
    for record in plan['closure']:
        need(pin(record['path']) == record, 'frozen source/input/runtime pin '+record['path'])
    need(pin(sys.executable) == plan['runtime_binary'], 'frozen Python executable')
    worker = (ROOT / plan['worker']).resolve()
    need(worker == Path(plan['argv'][2]).resolve() and plan['argv'][:2] == [sys.executable,'-B'],
         'literal Python worker argv')
    limit = plan['limits']['whole_seconds']; memory = plan['limits']['peak_bytes']
    stage = HERE / (plan['stage']+'-owner-v1')
    need(not stage.exists(), 'one immutable attempt, no retry')
    table() # Fail before worker activation if ownership metadata unavailable.
    stage.mkdir()
    save(stage/'launch-v1.json',dict(plan=pin(path),owner=pin(__file__),argv=plan['argv'],
         limits=plan['limits'],status='one_frozen_attempt'))
    child = None; usage = None; owned = {}; samples = []; error = None
    observer_peak = peak(resource.getrusage(resource.RUSAGE_CHILDREN))
    cancelled = [False]
    def interrupt(*_): cancelled[0] = True
    signal.signal(signal.SIGTERM,interrupt); signal.signal(signal.SIGINT,interrupt)
    try:
        with (stage/'stdout-v1.txt').open('xb') as out, (stage/'stderr-v1.txt').open('xb') as err:
            child = subprocess.Popen(plan['argv'],cwd=ROOT,stdin=subprocess.DEVNULL,
                stdout=out,stderr=err,start_new_session=True,
                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            while True:
                pid,status,current = os.wait4(child.pid,os.WNOHANG)
                if pid:
                    usage=current; child.returncode=os.waitstatus_to_exitcode(status); break
                need(not cancelled[0], 'ROOT owner interrupted')
                early_receipt=ROOT/plan['worker_receipt']
                if early_receipt.exists():
                    try: early=json.loads(early_receipt.read_bytes())
                    except json.JSONDecodeError: early=None
                    need(not (early and early.get('requires_ROOT_group_cleanup') is True),
                         'worker failure containment latch requires owned group cleanup')
                elapsed=time.perf_counter()-began
                need(elapsed < limit-2, 'whole phase deadline before receipt reserve')
                rows=table(); active=collect(rows,child.pid,owned,True)
                observer_peak=max(observer_peak,peak(resource.getrusage(resource.RUSAGE_CHILDREN)))
                rss=sum(rows[pid]['rss_bytes'] for pid in active)
                own_sample_peak=peak(resource.getrusage(resource.RUSAGE_SELF))
                combined=own_sample_peak+rss+observer_peak
                samples.append(dict(seconds=elapsed,owned_rss_bytes=rss,combined_bytes=combined,
                    ROOT_peak_bytes=own_sample_peak,
                    observer_peak_bytes=observer_peak,owned_rows={str(pid):rows[pid] for pid in active}))
                need(combined <= memory, 'sampled owner/observer/owned-worker memory')
                time.sleep(.1)
    except BaseException as exc:
        error=dict(type=type(exc).__name__,message=str(exc))
    finally:
        cleanup_errors=[]
        if child is not None and usage is None:
            try:
                rows=table(); kill_owned(rows,child.pid,owned,signal.SIGTERM,True)
            except BaseException as exc:
                cleanup_errors.append(dict(type=type(exc).__name__,message=str(exc)))
                # This unreaped direct child still owns its PID and fresh group.
                # Kill the group even when the observer fails; do not abandon reap.
                try: os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError: pass
            end=time.perf_counter()+2
            while time.perf_counter()<end:
                pid,status,current=os.wait4(child.pid,os.WNOHANG)
                if pid:
                    usage=current; child.returncode=os.waitstatus_to_exitcode(status); break
                time.sleep(.02)
            if usage is None:
                try: os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                _,status,usage=os.wait4(child.pid,0)
                child.returncode=os.waitstatus_to_exitcode(status)
        leftovers={}
        if child is not None:
            try:
                rows=table(); leftovers=collect(rows,child.pid,owned,False)
                if leftovers:
                    kill_owned(rows,child.pid,owned,signal.SIGKILL,False)
                    time.sleep(.05); leftovers=collect(table(),child.pid,owned,False)
            except BaseException as exc:
                cleanup_errors.append(dict(type=type(exc).__name__,message=str(exc)))
                leftovers={'unconfirmed': 'observer unavailable after direct-child reap'}
        worker_receipt_path=ROOT/plan['worker_receipt']
        worker_receipt=json.loads(worker_receipt_path.read_bytes()) if worker_receipt_path.exists() else None
        own_peak=peak(resource.getrusage(resource.RUSAGE_SELF))
        observer_peak=max(observer_peak,peak(resource.getrusage(resource.RUSAGE_CHILDREN)))
        worker_peak=peak(usage) if usage else 0
        # Worker declares the sum of its sequential direct-child kernel peaks;
        # its own peak is also protected by the outer wait4 and sampled RSS.
        child_peaks=worker_receipt.get('direct_children_peak_sum_bytes',0) if worker_receipt else 0
        peak_valid=type(child_peaks) is int and child_peaks>=0 and math.isfinite(child_peaks)
        if not peak_valid: child_peaks=0
        conservative=max([own_peak+worker_peak+child_peaks+observer_peak]+
                         [s['combined_bytes'] for s in samples])
        elapsed=time.perf_counter()-began
        accepted=(error is None and not cancelled[0] and not cleanup_errors and child is not None and child.returncode==0 and not leftovers
                  and worker_receipt is not None and worker_receipt.get('stage_completed') is True
                  and worker_receipt.get('stage')==plan['stage']
                  and worker_receipt.get('all_direct_children_terminal_and_reaped') is True and peak_valid
                  and conservative+8*1024*1024 <= memory and elapsed+2 <= limit)
        ledger=stage/'owned-ownership-ledger-v1.json.gz'
        with ledger.open('xb') as stream:
            stream.write(gzip.compress((json.dumps(dict(samples=samples,final_retained_births=owned,
                leftovers=leftovers,kernel_worker_peak_bytes=worker_peak,
                scope='Every sampled task-owned process row retained; complete-host process filtering trusts the pinned owner source. No unrelated host rows published.'),
                separators=(',',':'))+'\n').encode(),mtime=0))
        result=dict(schema='ROOT-guard-native-owner-terminal-v1',stage=plan['stage'],
            status='resource_gate_accepted_pending_post_write_observation' if accepted else 'UNKNOWN_owned_phase_gate',
            resource_gate_accepted=accepted,error=error,cancelled=cancelled[0],cleanup_errors=cleanup_errors,plan=pin(path),worker_receipt=pin(worker_receipt_path) if worker_receipt else None,
            elapsed_before_write_seconds=elapsed,write_reserve_seconds=2,peak_bytes=conservative,
            memory_write_reserve_bytes=8*1024*1024,ROOT_peak_bytes=own_peak,worker_kernel_peak_bytes=worker_peak,
            direct_children_peak_sum_bytes=child_peaks,observer_peak_bytes=observer_peak,
            worker_returncode=child.returncode if child else None,owned_leftovers=list(leftovers),
            sampled_observations=len(samples),max_sampled_owned_rss_bytes=max([s['owned_rss_bytes'] for s in samples] or [0]),
            ownership_ledger=pin(ledger),ownership_accounting_scope='pinned owner source plus complete retained owned-row ledger; no independent whole-host observer claimed',
            all_direct_children_terminal_and_reaped=child is not None and usage is not None,
            no_OS_hard_memory_limit_claim=True,scientific_stage=worker_receipt.get('stage') if worker_receipt else None)
        provisional=stage/'provisional-terminal-v1.json'; terminal=stage/'ROOT-terminal-v1.json'
        save(provisional,result)
        post_elapsed=time.perf_counter()-began
        post_peak=max(conservative,peak(resource.getrusage(resource.RUSAGE_SELF))+worker_peak+child_peaks+observer_peak)
        post_accepted=accepted and not cancelled[0] and post_elapsed<=limit and post_peak<=memory
        if post_accepted: os.link(provisional,terminal)
        save(stage/'post-write-observation-v1.json',dict(resource_gate_accepted=post_accepted,
            elapsed_seconds=post_elapsed,peak_bytes=post_peak,limits=plan['limits'],
            terminal=pin(terminal) if post_accepted else None,provisional=pin(provisional),
            scope='post-write observation; tool caller observation is separately required'))
        print(json.dumps(dict(stage=plan['stage'],resource_gate_accepted=post_accepted,
            elapsed_seconds=post_elapsed,peak_bytes=post_peak,worker_receipt=plan['worker_receipt'],
            cancelled_at_final_print=cancelled[0],
            terminal=str(terminal.relative_to(ROOT)) if post_accepted else None)),flush=True)

if __name__ == '__main__': main()
