"""ROOT sole actual entry; exact outer Popen-to-wait4 clock, no retry."""
import time
ENTRY=time.perf_counter()
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys

HERE=Path(__file__).resolve().parent
CANCELLED=False


def cancel(*_):
    global CANCELLED
    CANCELLED=True


def pin(path):
    path=Path(path);h=hashlib.sha256();n=0
    with path.open('rb') as f:
        for b in iter(lambda:f.read(65536),b''):h.update(b);n+=len(b)
    return dict(path=str(path),sha256=h.hexdigest(),bytes=n)


def main():
    import struct
    fmt=struct.Struct('!8sBBHQQddd')
    freeze=json.loads((HERE/'ROOT-execution-freeze-v1.json').read_text())
    for item in freeze['pins']:
        if pin(item['path'])!=item:raise ValueError('exact ROOT reviewed source/plan/runtime')
    if freeze['authorized'] is not True or freeze['scientific_calls']!=0:
        raise ValueError('ROOT non-scientific one-attempt activation')
    if (HERE/'outer-reap-v1.json').exists():raise ValueError('immutable actual outer receipt exists')
    source=HERE/'calibrate_platform_v4.py';plan=HERE/'plan-v4.json'
    child=None;usage=None;waited=False;stopping=False;emergency=False
    for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGALRM):signal.signal(sig,cancel)
    with (HERE/'external.stdout').open('xb') as out,(HERE/'external.stderr').open('xb') as err:
        started=time.perf_counter()
        try:
            child=subprocess.Popen([sys.executable,'-B',str(source),'external',str(plan)],
                stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
            while True:
                pid,status,current=os.wait4(child.pid,os.WNOHANG)
                if pid:
                    waited=True;usage=current;child.returncode=os.waitstatus_to_exitcode(status);break
                now=time.perf_counter()
                if (CANCELLED or now-started>=50) and not stopping:
                    stopping=True
                    try:os.kill(child.pid,signal.SIGTERM)
                    except ProcessLookupError:pass
                if now-started>=58:
                    emergency=True
                    try:os.killpg(child.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    _,status,usage=os.wait4(child.pid,0);waited=True
                    child.returncode=os.waitstatus_to_exitcode(status);break
                time.sleep(.01)
        finally:
            if child is not None and not waited:
                # Unexpected runner exception: bounded cooperative cancellation
                # of the held group leader, then emergency group cleanup UNKNOWN.
                stopping=True
                try:os.kill(child.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                deadline=min(started+58,time.perf_counter()+3)
                while time.perf_counter()<deadline:
                    pid,status,current=os.wait4(child.pid,os.WNOHANG)
                    if pid:
                        waited=True;usage=current;child.returncode=os.waitstatus_to_exitcode(status);break
                    time.sleep(.01)
                if not waited:
                    emergency=True
                    try:os.killpg(child.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    _,status,usage=os.wait4(child.pid,0);waited=True
                    child.returncode=os.waitstatus_to_exitcode(status)
        reaped=time.perf_counter()
    value=dict(schema='ROOT-calibration-complete-outer-reap-v1',source=pin(source),plan=pin(plan),
        freeze=pin(HERE/'ROOT-execution-freeze-v1.json'),child_pid=child.pid,child_exit=child.returncode,
        child_reaped=True,full_external_process_seconds=reaped-started,
        cancellation_observed=CANCELLED,cooperative_stop=stopping,emergency_group_kill=emergency,
        runner_seconds_before_receipt=time.perf_counter()-ENTRY,
        wait4_descendant_inclusive_ru_maxrss_raw=usage.ru_maxrss,
        raw_semantic_scope='No mathematics, model, search or RL; finite platform observations',
        postwrite_FRAME_validated=False,resource_estimate_accepted=False)
    if child.returncode==0 and not (CANCELLED or stopping or emergency):
        raw=(HERE/'external.stdout').read_bytes()
        if len(raw)!=fmt.size:raise ValueError('exact final external frame')
        magic,role,code,reserved,pid,rss,seconds,entry,closed=fmt.unpack(raw)
        if (magic,role,code,reserved,pid)!=(b'GCTSCMP1',4,0,0,child.pid):raise ValueError('final ROOT external frame identity')
        if (rss<=0 or not all(math.isfinite(x) for x in (seconds,entry,closed))
                or seconds<0 or closed<entry or abs(seconds-(closed-entry))>.000001):
            raise ValueError('finite postclose SELF/clock observations')
        receipt=json.loads((HERE/'external-receipt-v1.json').read_text())
        # Exact external SELF after receipt write supersedes the earlier own
        # term. Runner SELF is additional; rolled wait4 is preserved, not added.
        result=json.loads((HERE/'outputs/calibration-result-v1.json').read_text())
        root=receipt['coordinator_frame']['SELF_ru_maxrss_raw']
        actors=max(c['actor_frame']['SELF_ru_maxrss_raw'] for c in result['cases'])
        leaves=max(c['leaf_frame']['SELF_ru_maxrss_raw'] for case in result['cases']
            for c in (case['parent_receipt'] or {}).get('children',[]))
        observers=max(o['wait4_raw']['ru_maxrss'] for o in result['observers'])
        runner=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        conservative=runner+rss+root+actors+leaves+observers+33554432
        value.update(postwrite_FRAME_validated=True,external_SELF_after_receipt_close_raw=rss,
            external_seconds_through_receipt_close=seconds,complete_distinct_role_estimate_bytes=conservative,
            resource_estimate_accepted=conservative<=268435456 and reaped-started<=60,
            resource_scope='Distinct role maxima plus32MiB fixed postlude/runner final receipt reserve; retrospective finite estimate, no OS hard cap',
            result=pin(HERE/'outputs/calibration-result-v1.json'))
    with (HERE/'outer-reap-v1.json').open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(exit_code=child.returncode,reaped=True,seconds=value['full_external_process_seconds'],
        estimate_bytes=value.get('complete_distinct_role_estimate_bytes'),accepted=value['resource_estimate_accepted'])))
    return 0 if value['resource_estimate_accepted'] else 1


if __name__=='__main__':sys.exit(main())
