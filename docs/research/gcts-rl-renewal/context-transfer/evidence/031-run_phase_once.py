"""ROOT owns one phase's exact full terminal clock, never resumes a timeout."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

FOLDER=Path('.gcts-active/fixed-family-transfer-source-v1-20261012');OUT=Path('.gcts-active/fixed-family-transfer-progress-20261012')

def pin(p):
    data=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}

def main():
    begin=time.monotonic();kind=sys.argv[1]
    assert kind in ('preparation','search')
    p=FOLDER/(kind+'-plan-v1.json');plan=json.loads(p.read_text());cfg=plan['phase'];cap=cfg['outer_seconds']
    terminal_path=OUT/(kind+'-terminal-v1.json');assert not terminal_path.exists()
    if kind=='preparation':
        peer=Path('.gcts-active/fixed-family-transfer-independent-source-20261012/preparation-source-review-v1.json')
        assert pin(peer)['sha256']=='8734876c26218990355f1e37033b97d82250989ee7a0a23ef45cafd7428d0d23'
    assert all(not (FOLDER/n).exists() for n in plan['proposed_outputs'])
    command=[plan['runtime']['executable'],'-B',str(FOLDER/'transfer_outer_v1.py'),p.name]
    out=(OUT/(kind+'-outer-stdout.bin')).open('xb');err=(OUT/(kind+'-outer-stderr.bin')).open('xb')
    child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
    terminal=None;forced=False
    try:
        while terminal is None:
            pid,status,usage=os.wait4(child.pid,os.WNOHANG)
            if pid:
                child.returncode=os.waitstatus_to_exitcode(status);terminal=(child.returncode,usage);break
            if time.monotonic()-begin>cap+5:
                os.killpg(child.pid,signal.SIGKILL);forced=True
            time.sleep(.02)
    finally:
        if terminal is None:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            _,status,usage=os.wait4(child.pid,0);child.returncode=os.waitstatus_to_exitcode(status);terminal=(child.returncode,usage);forced=True
        out.close();err.close()
    full=time.monotonic()-begin;lp=FOLDER/cfg['lifetime'];life=json.loads(lp.read_text()) if lp.exists() else None
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss+max(terminal[1].ru_maxrss,life['conservative_host_peak_bytes'] if life else 0)
    accepted=terminal[0]==0 and not forced and full<=cap and peak<=cfg['bytes'] and life and life['status']=='passed_full_fresh_context_'+kind+'_lifetime'
    receipt={'status':'passed_ROOT_complete_fresh_context_'+kind if accepted else 'unknown_or_failed_ROOT_fresh_context_'+kind,
       'plan':pin(p),'command':command,'owner_pid':child.pid,'owner_exit_code':terminal[0],
       'owner_process_terminal_reaped':True,'worker_reaped':bool(life and life['worker_reaped_confirmed']),
       'forced_kill':forced,'full_phase_seconds_including_outer_final_write_and_reaping':full,
       'outer_time_gate_seconds':cap,'conservative_owned_peak_estimate_bytes':peak,
       'memory_scope':'Inherited sampled and retrospective estimate omits observer RSS; not strict aggregate host upper bound or hard OS memory cap.',
       'lifetime':pin(lp) if life else None,'stdout':pin(OUT/(kind+'-outer-stdout.bin')),'stderr':pin(OUT/(kind+'-outer-stderr.bin')),
       'native_queries':0,'training_runs':0,'mathematical_acceptance':'Pending independent new-context static gate or full trace/certificate audit.'}
    if kind=='preparation':receipt['independent_source_review']=pin(peer)
    with terminal_path.open('x') as stream:json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(receipt));return 0 if accepted else 2

if __name__=='__main__':raise SystemExit(main())
