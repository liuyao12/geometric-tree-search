"""One whole fixed selected-symbol query or independent replay; no proof search.

The complete input/table are prepared and separately byte checked before this
worker. Interpreter sources differ between native and replay stages. Native
acceptance is conditional on earlier finite lowering evidence, not a universal
compiler theorem or a materialized accepting Wang rectangle.
"""
import array
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
RAW='B^01:,;'

def need(v,label):
    if not v: raise ValueError(label)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

def save(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,allow_nan=False); stream.write('\n')

def pin(path):
    p=Path(path); raw=p.read_bytes()
    return dict(path=str(p.relative_to(ROOT)),sha256=sha(raw),bytes=len(raw))

def words(raw):
    need(len(raw)%4==0,'whole four-byte words')
    a=array.array('I'); a.frombytes(raw)
    if sys.byteorder!='little': a.byteswap()
    return a

def micro_bytes(micro):
    a=array.array('I',[0x47544d32,len(micro['rows']),*[micro[k] for k in ('start','accept','reject','space')]])
    for row in micro['rows']:
        band,actions=(0,{}) if row is None else row
        a.extend([band,len(actions)])
        for symbol in sorted(actions):
            target,write,move=actions[symbol]
            a.extend([RAW.index(symbol),target,RAW.index(write),move+1])
    if sys.byteorder!='little': a.byteswap()
    return a.tobytes()

def input_check(raw,initial):
    a=words(raw); need(list(a[:2])==[0x47544d33,len(initial['words'])],'input header')
    cursor=2
    for word,head,capacity in zip(initial['words'],initial['heads'],initial['capacities']):
        need(list(a[cursor:cursor+2])==[capacity,head],'declared frame'); cursor+=2
        need(capacity>=len(word)+1 and 0<=head<capacity,'initial cursor capacity')
        for i in range(capacity):
            expected=1 if i==0 else RAW.index(word[i-1]) if i<=len(word) else 0
            need(a[cursor+i]==expected,'every initial symbol')
        cursor+=capacity
    need(cursor==len(a),'no trailing input')

def output_check(raw,initial):
    a=words(raw); need(list(a[:1])==[0x47544d34] and a[2]==len(initial['words']),'output header')
    cursor=3; bad=[]
    for band,capacity in enumerate(initial['capacities']):
        head,size=a[cursor:cursor+2]; cursor+=2
        need(size==capacity and len(a[cursor:cursor+capacity])==capacity,'final full capacity')
        need(all(v<7 for v in a[cursor:cursor+capacity]),'final full alphabet')
        if head>=capacity: bad.append(band)
        cursor+=capacity
    need(cursor==len(a),'no trailing output')
    return a[1],bad

def main():
    began=time.perf_counter(); need(len(sys.argv)==2,'frozen worker plan')
    plan=json.loads(Path(sys.argv[1]).read_bytes()); mode=plan['stage']
    need(mode in ('native','replay'),'one literal verification stage')
    out=ROOT/plan['output_directory']; out.mkdir()
    result=dict(stage=mode,status='running',stage_completed=False,native_queries=0,native_replays=0,
                target_searches=0,new_RL_training=False,finite_Wang_rectangle_accepted=False,
                universal_compiler_theorem=False,direct_children_peak_sum_bytes=0)
    active=None; peaks=[]; children_started=[False]
    cancelled=[False]
    def interrupt(*_): cancelled[0]=True
    signal.signal(signal.SIGTERM,interrupt); signal.signal(signal.SIGINT,interrupt)
    def run(argv,name,stdin_path=None):
        nonlocal active
        need(not cancelled[0],'worker cancellation before child spawn '+name)
        with (out/(name+'-stdout.txt')).open('xb') as stdout,(out/(name+'-stderr.txt')).open('xb') as stderr:
            stdin=Path(stdin_path).open('rb') if stdin_path else subprocess.DEVNULL
            try:
                active=subprocess.Popen(argv,cwd=ROOT,stdin=stdin,stdout=stdout,stderr=stderr)
                children_started[0]=True
                while True:
                    pid,status,usage=os.wait4(active.pid,os.WNOHANG)
                    if pid:
                        active.returncode=os.waitstatus_to_exitcode(status)
                        peaks.append(usage.ru_maxrss*(1 if sys.platform=='darwin' else 1024))
                        returncode=active.returncode; active=None
                        need(returncode==0,'child zero exit '+name)
                        need(not cancelled[0],'worker interrupted after child terminal '+name)
                        break
                    need(not cancelled[0],'worker interrupted '+name)
                    need(time.perf_counter()-began < plan['limits']['whole_seconds']-4,'worker deadline')
                    time.sleep(.05)
            finally:
                if hasattr(stdin,'close'): stdin.close()
                if active is not None:
                    try: active.kill()
                    except ProcessLookupError: pass
                    _,status,usage=os.wait4(active.pid,0)
                    active.returncode=os.waitstatus_to_exitcode(status)
                    peaks.append(usage.ru_maxrss*(1 if sys.platform=='darwin' else 1024)); active=None
        return (out/(name+'-stdout.txt')).read_bytes()
    try:
        for record in plan['closure']:
            p=Path(record['path']); p=p if p.is_absolute() else ROOT/p
            raw=p.read_bytes(); need(sha(raw)==record['sha256'] and len(raw)==record['bytes'],'frozen '+record['path'])
        prepared=json.loads((ROOT/plan['preparation_receipt']).read_bytes())
        need(prepared['stage']=='preparation' and prepared['stage_completed'] is True,
             'actual complete preparation prerequisite')
        admission=json.loads((ROOT/plan['preparation_ROOT_decision']).read_bytes())
        need(admission['ROOT_final_accepted'] is True and admission['native_queries']==0,
             'ROOT closed constructor/input preparation admission')
        previous=None; expected=None
        if mode=='replay':
            previous=json.loads((ROOT/plan['producer_receipt']).read_bytes())
            producer_admission=json.loads((ROOT/plan['producer_ROOT_decision']).read_bytes())
            need(producer_admission['ROOT_final_accepted'] is True and previous['stage_completed'] is True,
                 'producer whole-phase admission before any replay compilation/query')
            need(previous['request_sha256']==plan['request_sha256'] and
                 previous['input_sha256']==plan['input_bytes_sha256'] and
                 previous['limits']['micro_steps']==plan['limits']['micro_steps'],
                 'exact replay producer request/input/step bound before compilation/query')
            expected=gzip.decompress((ROOT/plan['producer_output']).read_bytes())
            need(sha(expected)==previous['output_sha256'] and len(expected)==previous['output_bytes'],
                 'complete immutable producer output before compilation/query')
        frame=json.loads(gzip.decompress((ROOT/plan['frame']).read_bytes()))
        raw_input=gzip.decompress((ROOT/plan['input']).read_bytes())
        raw_code=gzip.decompress((ROOT/plan['code']).read_bytes())
        micro=json.loads(gzip.decompress((ROOT/plan['microcode']).read_bytes()))
        need(sha(canonical(micro))==plan['micro_sha256'],'unchanged whole microtable')
        need(micro['program_sha256']==plan['program_sha256'],'unchanged program')
        need(micro['start']==plan['parser_start'] and micro['start']!=micro['boundary']['old_start'],'true parser start')
        need(raw_code==micro_bytes(micro),'every microtable byte independently reconstructed')
        need(frame['request_sha256']==plan['request_sha256'],'fixed whole request')
        need(sha(raw_input)==plan['input_bytes_sha256'] and sha(raw_code)==plan['micro_code_bytes_sha256'],'complete input/code pins')
        initial=frame['proposed_initial']; input_check(raw_input,initial)
        terminal_states={k:micro[v] for k,v in [('accepted','accept'),('rejected','reject'),('unknown_space_budget','space')]}
        handshake=['READY',str(len(micro['rows'])),*[str(micro[k]) for k in ('start','accept','reject','space')]]
        stop=len(micro['rows']); del frame,micro
        (out/'input.bin').write_bytes(raw_input); (out/'code.bin').write_bytes(raw_code)
        del raw_input,raw_code
        executable=out/'interpreter'; source=ROOT/plan['interpreter_source']
        compile_began=time.perf_counter()
        run([plan['compiler'],'-O3','-std=c++17',str(source),'-o',str(executable)],'compile')
        result['compile_seconds']=time.perf_counter()-compile_began
        result['interpreter_binary']=pin(executable)
        query_began=time.perf_counter(); limit=plan['limits']['micro_steps']
        if mode=='native':
            protocol=str(out/'input.bin')+' '+str(out/'output.bin')+' '+str(limit)+'\nquit\n'
            (out/'protocol.txt').write_text(protocol)
            result['native_queries']=1
            stdout=run([str(executable),str(out/'code.bin')],'query',out/'protocol.txt')
            lines=stdout.decode().splitlines()
            need(len(lines)==2 and lines[0].split()==handshake,'one whole pinned persistent query response')
            native=json.loads(lines[1])
            need(native['start']==plan['parser_start'],'reported actual parser start')
        else:
            result['native_replays']=1
            stdout=run([str(executable),str(out/'code.bin'),str(out/'input.bin'),str(out/'output.bin'),str(limit),str(stop)],'query')
            native=json.loads(stdout)
        result['query_seconds']=time.perf_counter()-query_began
        need(native['status'] in ('accepted','rejected','unknown_space_budget','unknown_step_budget'),'declared result')
        need(type(native['micro_steps']) is int and 0<=native['micro_steps']<=limit,'bounded complete trace')
        if native['status']=='unknown_step_budget': need(native['micro_steps']==limit,'actual step cutoff')
        raw_output=(out/'output.bin').read_bytes(); state,bad=output_check(raw_output,initial)
        if native['status'] in terminal_states: need(state==terminal_states[native['status']],'declared final state')
        if native['status']=='accepted': need(not bad,'accepted cursors inside all bands')
        if mode=='native': need(state==native['state'],'actual final state response')
        else:
            need(raw_output==expected,'all independent final output bytes')
            for key in ('status','micro_steps','physical_steps','micro_fnv64'):
                need(native[key]==previous['native_result'][key],'independent whole trace '+key)
            result['all_input_output_bytes_matched']=True
        with (out/'output.bin.gz').open('xb') as stream:
            stream.write(gzip.compress(raw_output,mtime=0))
        result.update(status='whole_native_check_complete' if mode=='native' else 'whole_independent_replay_matched',
            stage_completed=True,native_result=native,final_state=state,out_of_frame_bands=bad,
            output_sha256=sha(raw_output),output_bytes=len(raw_output),output_file=pin(out/'output.bin.gz'),
            request_sha256=plan['request_sha256'],input_sha256=plan['input_bytes_sha256'],
            micro_code_bytes_sha256=plan['micro_code_bytes_sha256'],program_sha256=plan['program_sha256'],
            micro_sha256=plan['micro_sha256'],limits=plan['limits'],discovery='previous_GCTS_fixed_family_pool_search',
            same_24_command_positions=True,closed_hypothesis_axiom_translation=True)
    except BaseException as exc:
        result.update(status='UNKNOWN_whole_native_stage',error=dict(type=type(exc).__name__,message=str(exc)))
    finally:
        if cancelled[0]:
            result.update(stage_completed=False,status='UNKNOWN_worker_cancellation')
        result['direct_children_peak_sum_bytes']=sum(peaks)
        result['worker_peak_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        result['elapsed_before_receipt_write_seconds']=time.perf_counter()-began
        result['all_direct_children_terminal_and_reaped']=active is None
        result['cancelled_before_receipt_write']=cancelled[0]
        result['requires_ROOT_group_cleanup']=children_started[0] and not result['stage_completed']
        hold_required=result['requires_ROOT_group_cleanup']
        try:
            save(ROOT/plan['worker_receipt'],result)
            need(not cancelled[0],'worker cancellation during receipt publication')
            print(json.dumps({k:result.get(k) for k in ('stage','status','stage_completed','native_queries','native_replays','native_result')}),flush=True)
        except BaseException:
            hold_required=children_started[0]
            if not hold_required: raise
        finally:
            if hold_required or (cancelled[0] and children_started[0]):
                # Keep the known fresh session leader alive after any spawned-
                # child or receipt failure. ROOT kills its still-owned group
                # and reaps it; failed publication cannot silently qualify.
                while True: time.sleep(.1)

if __name__=='__main__': main()
