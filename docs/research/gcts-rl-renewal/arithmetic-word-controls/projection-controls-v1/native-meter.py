"""UNEXECUTED external measurement instrument; no project Source imports.

CLI9: fresh_evidence pinned_python -I -S -B caller_source prereg_path SHA bytes.
Only the measured caller executes project Source, in a distinct address space.
The tool Date bracket includes instrument startup/final serialization. Observer
memory is explicitly outside owned caller+worker scope, like the tool executor.
"""
import time
_CLOCK, _CLOCK_ID = time.clock_gettime_ns, time.CLOCK_MONOTONIC
if type(_CLOCK_ID) is not int:raise ValueError('exact native global clock ID')
METER_BEGAN_NS = _CLOCK(_CLOCK_ID)

import json
import os
from pathlib import Path
import resource
import signal
import stat
import subprocess
import sys
import types

VERSION='Q-external-native-terminal-meter-Source-v1-global-clock'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
RUNTIME='/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'
_WAIT4, _SLEEP, _USAGE = os.wait4, time.sleep, resource.getrusage
_INTERRUPTED=False


def need(ok,message):
    if not ok:raise ValueError(message)


def now():
    if (time.clock_gettime_ns is not _CLOCK or type(time.CLOCK_MONOTONIC) is not int
            or time.CLOCK_MONOTONIC != _CLOCK_ID or type(_CLOCK_ID) is not int):
        raise ValueError('original native global clock callable/ID')
    value=_CLOCK(_CLOCK_ID)
    need(type(value) is int and METER_BEGAN_NS<=value<2**63,'strict global observation')
    return value


def interrupted(signum,frame):
    global _INTERRUPTED
    _INTERRUPTED=True


def main(argv):
    need(sys.platform=='darwin' and len(argv)==9,'native Darwin external meter CLI9')
    need(type(_CLOCK) is types.BuiltinFunctionType and _CLOCK.__module__=='time'
         and _CLOCK.__name__=='clock_gettime_ns','original native kernel clock')
    need(argv[1]==RUNTIME and str(Path(sys.executable).resolve())==RUNTIME
         and argv[2:5]==['-I','-S','-B'],'exact pinned Python isolated caller command')
    for index in (0,5,6):
        path=Path(argv[index]);need(path.is_absolute() and str(path)==argv[index]
            and path.parent==path.parent.resolve(),'canonical instrument/caller/prereg path')
    need(len(argv[7])==64 and all(c in '0123456789abcdef' for c in argv[7])
         and argv[8].isascii() and argv[8].isdecimal() and not argv[8].startswith('0'),'exact Root capsule arguments')
    output=Path(argv[0]);need(not output.exists() and not output.is_symlink(),'fresh external evidence, never overwrite')
    descriptor=os.open(str(output),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    child=None;usage=None;status=None;terminal=None;error=None;cancel_sent=False
    began=None
    try:
        began=now()
        child=subprocess.Popen(argv[1:],stdin=subprocess.DEVNULL,start_new_session=True,
            close_fds=True,env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})
        while True:
            if os.wait4 is not _WAIT4 or time.sleep is not _SLEEP or resource.getrusage is not _USAGE:
                raise ValueError('original native meter wait/sleep/resource endpoints')
            pid,observed_status,observed_usage=_WAIT4(child.pid,os.WNOHANG)
            if pid:
                need(pid==child.pid,'exact measured caller terminal wait4')
                usage=observed_usage;status=observed_status;terminal=now()
                child.returncode=os.waitstatus_to_exitcode(status);break
            stamp=now()
            if (_INTERRUPTED or stamp>=METER_BEGAN_NS+55000000000) and not cancel_sent:
                os.killpg(child.pid,signal.SIGTERM);cancel_sent=True
            if stamp>=METER_BEGAN_NS+60000000000:
                os.killpg(child.pid,signal.SIGKILL)
            _SLEEP(.005)
    except BaseException as failure:
        error={'type':type(failure).__name__,'message':str(failure)[:1024]}
    finally:
        if child is not None and usage is None:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            # Complete native reap, not Popen.poll or a fabricated terminal row.
            pid,status,usage=_WAIT4(child.pid,0)
            need(pid==child.pid,'exact failed caller native reap')
            terminal=now();child.returncode=os.waitstatus_to_exitcode(status)
        peak=None if usage is None else usage.ru_maxrss
        need(peak is None or type(peak) is int and peak>=0,'actual terminal Darwin RSS byte count')
        record={'schema':'ROOT-Q-native-terminal-meter-v1','version':VERSION,'CLOCK_DOMAIN':CLOCK_DOMAIN,
            'meter_began_ns':METER_BEGAN_NS,'caller_launch_began_ns':began,'caller_terminal_observed_ns':terminal,
            'caller_pid':None if child is None else child.pid,'wait4_pid':None if usage is None else pid,
            'wait4_status':status,'caller_returncode':None if child is None else child.returncode,
            'caller_kernel_peak_bytes':peak,'caller_kernel_elapsed_ns':None if terminal is None else terminal-began,
            'wait4_usage':None if usage is None else [{'kind':'float','hex':v.hex()} if type(v) is float else v for v in usage],
            'all_reaped':usage is not None,'interrupted':_INTERRUPTED,'cancellation_forwarded':cancel_sent,
            'error':error,'observed_before_output_ns':now(),'utility_argv':argv[1:],
            'observer_source_path':str(Path(__file__).resolve()),'observer_memory_excluded':True,
            'observer_scope':'External trusted native measurement instrument only; its wall startup/output/exit is charged by actual tool Date bracket. Owned memory uses terminal caller rusage plus worker wait4 peak conservatively.',
            'ROOT_resource_accepted':False,'ROOT_primary_accepted':False,'all_strong_acceptance_false':True}
        raw=json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
        need(len(raw)<=16384,'complete bounded canonical meter evidence')
        offset=0
        try:
            while offset<len(raw):
                count=os.write(descriptor,raw[offset:]);need(count>0,'complete meter output');offset+=count
        finally:os.close(descriptor)
    return 0 if child is not None and usage is not None and child.returncode==0 and error is None and not _INTERRUPTED else 2


if __name__=='__main__':
    try:raise SystemExit(main(sys.argv[1:]))
    except BaseException as failure:
        if type(failure) is SystemExit:raise
        sys.stderr.write(type(failure).__name__+': '+str(failure)+'\n');raise SystemExit(2)
