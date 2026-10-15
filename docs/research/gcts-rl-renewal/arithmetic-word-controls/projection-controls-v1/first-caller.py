"""UNEXECUTED trusted projection-only outer caller; ROOT alone supplies argv3.

The external Date.now caller covers interpreter/this Source compilation/import
of time and actual final exit. This one native begin precedes every remaining
import, authentication, input copy, worker compile, child and output operation.
No project Source executes in this parent. Full52/W16 are NOT supported here.
"""
import time
_NATIVE_CLOCK = time.clock_gettime_ns
_NATIVE_ID = time.CLOCK_MONOTONIC
if type(_NATIVE_ID) is not int:
    raise ValueError('original native integer CLOCK_MONOTONIC ID')
JOINT_BEGAN_NS = _NATIVE_CLOCK(_NATIVE_ID)

import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat
import subprocess
import sys
import types

VERSION = 'Q-trusted-projection-only-outer-caller-Source-v2-global-clock'
CLOCK_DOMAIN = 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
RUNTIME = {'path': '/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9',
 'sha256': 'bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e', 'bytes': 102352}
TERMINAL_METER = {'path':'/usr/bin/time','sha256':'d2210b72e8c978748a0f0ac7d0819dda4dd411bb7a2e9730476038b0d695e7a2','bytes':135248}
POLICY = {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-runtime-clock-ABI-qualification-20261015/ROOT-global-clock-repair-choice-v1.json',
 'sha256': '2e526972409799e8874d10afdf0cb094ac4f6dc634b2fc0ffdaa2be789d172b4', 'bytes': 4443}
LIMITS = {'joint_seconds': 20, 'failure_only_seconds': 55, 'owned_seconds': 60,
 'aggregate_owned_bytes': 536870912, 'caller_seconds': 90, 'caller_finish_reserve_seconds': 1}
REQUEST_SCHEMA = 'ROOT-Q-isolated-projection-outer-preregistration-v1'
SCOPE = 'isolated_clock_projection_controls_only'
WORKER_SCOPE = 'Q-isolated-clock-projection-controls-Source'
CALLER_SCOPE = 'Q-trusted-projection-only-outer-caller-Source'
BODY_SCHEMA = 'Q-isolated-clock-projection-controls-body-v1'
TRAILER_SCHEMA = 'Q-isolated-clock-projection-controls-completion-v1'
BODY_MAX, TRAILER_MAX = 1048576, 1024
STRONG_FLAGS = ('ROOT_primary_accepted', 'ROOT_resource_accepted', 'original_Q_theorem_accepted',
 'full_architecture_qualified', 'full52_qualified', 'full24_accepted', 'native_accepted', 'RL_accepted')
_CANCELLED = False
_SLEEP = time.sleep
_GETRUSAGE = resource.getrusage
_WAIT4 = os.wait4

# Fixed reviewed bootstrap is part of THIS Source, not another executable role.
# The same original begin is received, never replaced by a new child begin.
CHILD_BOOTSTRAP = r'''
import time
clock, clock_id = time.clock_gettime_ns, time.CLOCK_MONOTONIC
import fcntl, hashlib, os, stat, sys, types
if len(sys.argv) != 11: raise ValueError('workerSourceFD/SHA/bytes/path plus unchanged worker argv6')
sfd, sha, size, path = sys.argv[1:5]
args = sys.argv[5:]
for text in (sfd, size, args[0], args[2], args[3], args[4], args[5]):
    if not (text.isascii() and text.isdecimal() and (text == '0' or not text.startswith('0'))):
        raise ValueError('literal canonical decimal inherited CLI')
sfd, size = int(sfd), int(size)
began, deadline = int(args[4]), int(args[5])
if not (type(clock_id) is int and type(clock) is types.BuiltinFunctionType
        and clock.__module__ == 'time' and clock.__name__ == 'clock_gettime_ns'
        and 0 < began < deadline < 2**63 and deadline-began == 20000000000):
    raise ValueError('one inherited original global20')
if time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id:
    raise ValueError('original child clock endpoint')
if not began <= clock(clock_id) < deadline: raise TimeoutError('child startup charged to original20')
if not (3 <= sfd <= 2**20 and 0 < size <= 1048576 and os.path.isabs(path)
        and path == os.path.realpath(path)):
    raise ValueError('complete bounded canonical worker Source')
if fcntl.fcntl(sfd, fcntl.F_GETFL) & os.O_ACCMODE != os.O_RDONLY:
    raise ValueError('worker Source readonly')
before = os.fstat(sfd)
if not stat.S_ISREG(before.st_mode) or before.st_size != size or os.lseek(sfd,0,os.SEEK_CUR) != 0:
    raise ValueError('exact Source regular FD/length/offset0')
chunks, count = [], 0
while True:
    if time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id:
        raise ValueError('child clock changed during same-buffer Source load')
    if clock(clock_id) >= deadline: raise TimeoutError('Source authentication is original20 work')
    block = os.read(sfd, min(65536, size-count+1))
    if not block: break
    count += len(block)
    if count > size: raise ValueError('no Source suffix/prefix')
    chunks.append(block)
after = os.fstat(sfd)
if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns) != (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns):
    raise ValueError('stable original readonly Source through EOF')
raw = b''.join(chunks)
if count != size or hashlib.sha256(raw).hexdigest() != sha: raise ValueError('exact complete worker Source SHA')
os.close(sfd)
request_fd, result_fd = int(args[0]), int(args[3])
if not (len({sfd,request_fd,result_fd})==3 and request_fd>=3 and result_fd>=3):
    raise ValueError('three distinct inherited channels')
if (fcntl.fcntl(request_fd,fcntl.F_GETFL)&os.O_ACCMODE != os.O_RDONLY
        or fcntl.fcntl(result_fd,fcntl.F_GETFL)&os.O_ACCMODE != os.O_WRONLY
        or os.lseek(request_fd,0,os.SEEK_CUR)!=0):
    raise ValueError('whole readonly request and write-only result')
if not stat.S_ISREG(os.fstat(request_fd).st_mode) or not stat.S_ISREG(os.fstat(result_fd).st_mode) or os.fstat(result_fd).st_size!=0:
    raise ValueError('regular immutable request/fresh result')
name = '_Q_projection_worker_' + sha
if name in sys.modules: raise ValueError('no Source cache reuse')
module=types.ModuleType(name); module.__file__=path; module.__package__=''; module.__loader__=None; module.__spec__=None
sys.modules[name]=module
exec(compile(raw,path,'exec',dont_inherit=True),module.__dict__)
del raw, chunks
if module.CLOCK_DOMAIN != 'time.clock_gettime_ns(time.CLOCK_MONOTONIC)': raise ValueError('mixed Source clock domain')
entry=module.main
if type(entry) is not types.FunctionType or entry.__globals__ is not module.__dict__ or entry.__code__.co_filename!=path:
    raise ValueError('actual private same-buffer worker entry')
code, defaults, kw, cells = entry.__code__,entry.__defaults__,entry.__kwdefaults__,tuple((c,c.cell_contents) for c in entry.__closure__ or ())
kw_entries=tuple((k,id(v),v) for k,v in sorted((kw or {}).items()))
if time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id or clock(clock_id)>=deadline:
    raise TimeoutError('original20 before worker invocation')
returned=entry(args)
if (module.main is not entry or entry.__code__ is not code or entry.__defaults__ is not defaults or entry.__kwdefaults__ is not kw
        or len(entry.__closure__ or ())!=len(cells)
        or any(c is not old or c.cell_contents is not value for c,(old,value) in zip(entry.__closure__ or (),cells))
        or tuple(sorted((entry.__kwdefaults__ or {}).keys()))!=tuple(k for k,_,_ in kw_entries)
        or any(entry.__kwdefaults__[k] is not value for k,_,value in kw_entries)):
    raise ValueError('actual worker code/default-entry/closure authority changed')
if time.clock_gettime_ns is not clock or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != clock_id:
    raise ValueError('original child global clock retained after worker')
if type(returned) is not int or returned not in (0,2): raise ValueError('exact worker return0/2')
if returned==0 and clock(clock_id)>=deadline: raise TimeoutError('worker return remains original20')
raise SystemExit(returned)
'''


def need(ok, message):
    if not ok:
        raise ValueError(message)


def now(_clock=_NATIVE_CLOCK, _clock_id=_NATIVE_ID, _module=time):
    if (time is not _module or time.clock_gettime_ns is not _clock
            or type(time.CLOCK_MONOTONIC) is not int or time.CLOCK_MONOTONIC != _clock_id
            or type(_clock_id) is not int):
        raise ValueError('original parent native global clock callable/ID')
    value = _clock(_clock_id)
    need(type(value) is int and value >= JOINT_BEGAN_NS, 'monotone exact native integer observation')
    return value


def budget(*, failure=False):
    if not failure:need(not _CANCELLED, 'actual caller interrupted')
    if now() >= JOINT_BEGAN_NS + (55 if failure else 20)*1000000000:
        raise TimeoutError('original20 success / failure-only55, no reset')


def decimal(text):
    need(type(text) is str and text.isascii() and text.isdecimal()
         and (text=='0' or not text.startswith('0')), 'canonical decimal CLI')
    value=int(text); need(0 <= value < 2**63, 'bounded exact CLI integer'); return value


def unique(items):
    result={}
    for k,v in items:
        need(k not in result, 'duplicate JSON member'); result[k]=v
    return result


def reject_number(text):
    raise ValueError('no JSON float/nonfinite token in trusted control metadata/wire')


def decode(raw, *, large_integers=False):
    value=json.loads(raw.decode('utf8','strict'),object_pairs_hook=unique,
        parse_float=reject_number,parse_constant=reject_number,parse_int=ratio_integer if large_integers else decimal_signed)
    return value


def decimal_signed(text):
    need(len(text)<=20, 'bounded signed integer token'); value=int(text)
    need(-(2**63)<=value<2**63, 'signed64 metadata token'); return value


def ratio_integer(text):
    need(len(text)<=4096, 'bounded exact binary64 ratio/bit integer token');return int(text)


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')


class ExactPathCapsule:
    """Immutable exact raw pin; no candidate-provided path authority."""
    __slots__=('path','sha256','bytes')
    def __init__(self, record):
        need(type(record) is dict and set(record)=={'path','sha256','bytes'}, 'complete exact path capsule')
        p,d,n=record['path'],record['sha256'],record['bytes']
        need(type(p) is str and type(d) is str and len(d)==64 and all(c in '0123456789abcdef' for c in d), 'literal path/hash')
        need(type(n) is int and 0<=n<=64*1048576, 'strict integer whole-file byte count')
        path=Path(p)
        need(path.is_absolute() and str(path)==p and path==path.resolve() and stat.S_ISREG(path.lstat().st_mode), 'canonical regular no-link path')
        for k,v in (('path',p),('sha256',d),('bytes',n)):object.__setattr__(self,k,v)
    def __setattr__(self, key, value):
        raise AttributeError('sealed exact path capsule')
    def record(self):
        return {'path':self.path,'sha256':self.sha256,'bytes':self.bytes}
    def read(self):
        budget(); fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            before=os.fstat(fd);need(stat.S_ISREG(before.st_mode) and before.st_size==self.bytes,'exact whole raw input')
            chunks=[];size=0;h=hashlib.sha256()
            while True:
                budget();block=os.read(fd,min(65536,self.bytes-size+1))
                if not block:break
                size+=len(block);need(size<=self.bytes,'no prefix/suffix raw custody');chunks.append(block);h.update(block)
            after=os.fstat(fd)
            need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
                 (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'stable full input EOF')
            need(size==self.bytes and h.hexdigest()==self.sha256,'complete SHA/length/EOF');budget();return b''.join(chunks)
        finally:os.close(fd)


def write_exclusive(path, raw, *, failure=False):
    budget(failure=failure);fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        offset=0
        while offset<len(raw):
            budget(failure=failure);n=os.write(fd,raw[offset:]);need(n>0,'complete write');offset+=n
    finally:os.close(fd)
    budget(failure=failure)


def whole_output(path, cap):
    # Complete raw bytes after wait4 only. Failure evidence is never a prefix.
    budget(failure=True);fd=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW)
    try:
        before=os.fstat(fd);need(stat.S_ISREG(before.st_mode) and before.st_size<=cap,'bounded full owned output')
        raw=b''
        while True:
            budget(failure=True);block=os.read(fd,min(65536,cap-len(raw)+1))
            if not block:break
            raw+=block;need(len(raw)<=cap,'complete output cap; no truncate')
        after=os.fstat(fd)
        need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==
             (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'stable result through full EOF')
        need(len(raw)==before.st_size,'whole output EOF');return raw
    finally:os.close(fd)


def raw_pin(raw):
    return {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}


def exact_review(record, source, contract, scope, author):
    value=decode(ExactPathCapsule(record).read())
    need(value.get('source_only') is True and value.get('source_review_passed') is True
         and type(value.get('scientific_calls')) is int and value['scientific_calls']==0
         and value.get('scope')==scope and value.get('source')==source and value.get('source_contract')==contract
         and value.get('author_identity')==author and type(value.get('reviewer_identity')) is str
         and value['author_identity']!=value['reviewer_identity'],'genuine exact distinct current Source review')
    return value


def peak(usage):
    need(sys.platform=='darwin' and type(usage.ru_maxrss) is int and usage.ru_maxrss>=0,'actual Darwin kernel peak bytes')
    return usage.ru_maxrss


def usage_record(usage):
    return [{'kind':'float','hex':x.hex()} if type(x) is float else x for x in usage]


def cancel(signum, frame):
    global _CANCELLED
    _CANCELLED=True


def main(argv):
    need(len(argv)==3 and sys.platform=='darwin','Root prereg path/SHA/bytes, actual Darwin only')
    need(sys.flags.isolated==1 and sys.flags.no_site==1 and sys.flags.dont_write_bytecode==1,'actual pinned Python -I -S -B invocation')
    need(type(_NATIVE_CLOCK) is types.BuiltinFunctionType and _NATIVE_CLOCK.__module__=='time'
         and _NATIVE_CLOCK.__name__=='clock_gettime_ns','original native clock')
    prereg_capsule=ExactPathCapsule({'path':argv[0],'sha256':argv[1],'bytes':decimal(argv[2])})
    need(prereg_capsule.bytes<=1048576,'small explicit Root preregistration only')
    prereg=decode(prereg_capsule.read())
    fields={'schema','scope','invocation_id','clock_domain','limits','runtime','caller_source','caller_review',
        'caller_contract','worker_source','worker_review','worker_contract','request','output_directory','external_meter','raw_closure'}
    need(type(prereg) is dict and set(prereg)==fields and prereg['schema']==REQUEST_SCHEMA
         and prereg['scope']==SCOPE and prereg['clock_domain']==CLOCK_DOMAIN and type(prereg['limits']) is dict and set(prereg['limits'])==set(LIMITS)
         and all(type(v) is int and v==LIMITS[k] for k,v in prereg['limits'].items()),
         'exact projection-only Root preregistration16/current clock/original caps')
    need(type(prereg['invocation_id']) is str and 1<=len(prereg['invocation_id'])<=128 and prereg['invocation_id'].isascii(),'opaque Root nonce')
    need(prereg['runtime']==RUNTIME and str(Path(sys.executable).resolve())==RUNTIME['path'],'actual pinned Python runtime')
    need(prereg['caller_source']['path']==str(Path(__file__).resolve()),'actual reviewed caller Source origin')
    meter=prereg['external_meter']
    need(type(meter) is dict and set(meter)=={'source','output_path'} and meter['source']==TERMINAL_METER
         and type(meter['output_path']) is str and Path(meter['output_path']).is_absolute()
         and Path(meter['output_path']).parent==Path(meter['output_path']).parent.resolve(),
         'exact external native terminal meter and Root fresh evidence path')
    runtime_raw=ExactPathCapsule(RUNTIME).read();del runtime_raw
    own_raw=ExactPathCapsule(prereg['caller_source']).read();del own_raw
    worker_raw=ExactPathCapsule(prereg['worker_source']).read();need(len(worker_raw)<=1048576,'small fixed reviewed worker')
    request_raw=ExactPathCapsule(prereg['request']).read();need(len(request_raw)<=1048576,'whole opaque worker request; no Q decode in parent')
    worker_contract=decode(ExactPathCapsule(prereg['worker_contract']).read())
    caller_contract=decode(ExactPathCapsule(prereg['caller_contract']).read())
    need(worker_contract.get('source')==prereg['worker_source'] and worker_contract.get('CLOCK_DOMAIN')==CLOCK_DOMAIN,
         'current exact worker contract/source/global clock')
    need(caller_contract.get('caller_source')==prereg['caller_source'] and caller_contract.get('CLOCK_DOMAIN')==CLOCK_DOMAIN
         and caller_contract.get('limits')==LIMITS,'current caller contract/caps')
    exact_review(prereg['caller_review'],prereg['caller_source'],prereg['caller_contract'],CALLER_SCOPE,'/root/hilbert_advice_controls')
    exact_review(prereg['worker_review'],prereg['worker_source'],prereg['worker_contract'],WORKER_SCOPE,'/root/arithmetic_induction')
    required=[prereg[k] for k in ('runtime','caller_source','caller_review','caller_contract','worker_source','worker_review','worker_contract','request')]+[POLICY,TERMINAL_METER]
    closure=prereg['raw_closure']
    need(type(closure) is list and len(closure)<=512 and all(type(r) is dict and set(r)=={'path','sha256','bytes'} for r in closure)
         and len({r['path'] for r in closure})==len(closure) and all(r in closure for r in required),'complete named current raw closure')
    raw_receipts=[]
    for record in closure:
        buffer=ExactPathCapsule(record).read();raw_receipts.append(record);del buffer
    root=Path(prereg['output_directory'])
    need(type(prereg['output_directory']) is str and root.is_absolute() and str(root)==prereg['output_directory']
         and root.parent==root.parent.resolve() and root.parent.is_dir() and len(str(root))<=1024 and not root.exists(),'fresh once-only owned Root directory')
    budget();root.mkdir(mode=0o700)
    signal.signal(signal.SIGINT,cancel);signal.signal(signal.SIGTERM,cancel)
    worker_path,request_path=root/'worker-source.py',root/'request.json'
    write_exclusive(worker_path,worker_raw);write_exclusive(request_path,request_raw)
    os.chmod(worker_path,0o400);os.chmod(request_path,0o400)
    del worker_raw,request_raw
    write_exclusive(root/'raw-closure-receipts.json',canonical({'preregistration':prereg_capsule.record(),'records':raw_receipts})+b'\n')
    result_path=root/'worker-result.jsonl';stdout_path=root/'worker-stdout.txt';stderr_path=root/'worker-stderr.txt'
    child=None;usage=None;terminal_ns=None;wait_status=None;launch_ns=None;error=None;response=None;pending=False;fds=[]
    try:
        for path,flags in ((worker_path,os.O_RDONLY),(request_path,os.O_RDONLY),(result_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL)):
            fds.append(os.open(str(path),flags|os.O_NOFOLLOW,0o600))
        output=stdout_path.open('xb');errors=stderr_path.open('xb')
        try:
            budget();launch_ns=now()
            argv=[RUNTIME['path'],'-I','-S','-B','-c',CHILD_BOOTSTRAP,str(fds[0]),prereg['worker_source']['sha256'],str(prereg['worker_source']['bytes']),
                prereg['worker_source']['path'],str(fds[1]),prereg['request']['sha256'],str(prereg['request']['bytes']),str(fds[2]),
                str(JOINT_BEGAN_NS),str(JOINT_BEGAN_NS+20000000000)]
            child=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=output,stderr=errors,pass_fds=tuple(fds),close_fds=True,
                start_new_session=True,cwd=str(root),env={'PATH':'/usr/bin:/bin','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})
        finally:output.close();errors.close()
        for fd in fds:os.close(fd)
        fds=[]
        while True:
            if os.wait4 is not _WAIT4 or resource.getrusage is not _GETRUSAGE or time.sleep is not _SLEEP:
                raise ValueError('original parent wait4/resource/sleep native endpoints')
            pid,status,observed_usage=_WAIT4(child.pid,os.WNOHANG)
            if pid:
                need(pid==child.pid,'exact actual child wait4')
                terminal_ns=now();usage=observed_usage;wait_status=status;child.returncode=os.waitstatus_to_exitcode(status);break
            budget()
            need(peak(_GETRUSAGE(resource.RUSAGE_SELF))<=LIMITS['aggregate_owned_bytes'],'parent native peak cap')
            need(result_path.stat().st_size<=BODY_MAX+TRAILER_MAX and stdout_path.stat().st_size<=1048576
                 and stderr_path.stat().st_size<=1048576,'bounded complete output; never truncate')
            _SLEEP(.005)
        budget();need(child.returncode==0 and terminal_ns<JOINT_BEGAN_NS+20000000000,'actual timely worker exit0')
        result_raw=whole_output(result_path,BODY_MAX+TRAILER_MAX)
        need(result_raw.endswith(b'\n') and result_raw.count(b'\n')==2,'complete response two lines+EOF')
        body_line,trailer_line,empty=result_raw.split(b'\n')
        need(empty==b'' and len(body_line)+1<=BODY_MAX and len(trailer_line)+1<=TRAILER_MAX,'complete size bounds')
        response,trailer=decode(body_line,large_integers=True),decode(trailer_line)
        need(canonical(response)==body_line and canonical(trailer)==trailer_line,'exact canonical complete wire')
        need(type(response) is dict and response.get('schema')==BODY_SCHEMA and response.get('CLOCK_DOMAIN')==CLOCK_DOMAIN
             and type(response.get('joint_began_ns')) is int and response['joint_began_ns']==JOINT_BEGAN_NS
             and type(response.get('joint_deadline_ns')) is int and response['joint_deadline_ns']==JOINT_BEGAN_NS+20000000000
             and response.get('completed') is True and response.get('all_checks_passed') is True,'complete current controls body, original clock')
        need(all(response.get(flag) is False for flag in STRONG_FLAGS),'no theorem/native/fullpipeline/Root admission')
        need(type(trailer) is dict and set(trailer)=={'schema','body_sha256','body_bytes','exit_zero_and_caller_deadline_required'}
             and trailer['schema']==TRAILER_SCHEMA and type(trailer['body_bytes']) is int and trailer['body_bytes']==len(body_line)+1
             and trailer['body_sha256']==hashlib.sha256(body_line+b'\n').hexdigest()
             and trailer['exit_zero_and_caller_deadline_required'] is True,'whole hash-linked completion')
        budget();pending=True
    except BaseException as failure:
        error={'type':type(failure).__name__,'message':str(failure)[:2048]};pending=False
    finally:
        for fd in fds:os.close(fd)
        if child is not None and usage is None:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            while now()<JOINT_BEGAN_NS+55000000000:
                pid,status,observed_usage=_WAIT4(child.pid,os.WNOHANG)
                if pid:
                    need(pid==child.pid,'cleanup exact child wait4');terminal_ns=now();usage=observed_usage;wait_status=status
                    child.returncode=os.waitstatus_to_exitcode(status);break
                _SLEEP(.005)
        files={}
        for path,cap in ((result_path,BODY_MAX+TRAILER_MAX),(stdout_path,1048576),(stderr_path,1048576)):
            if path.exists():
                complete_raw=whole_output(path,cap);files[path.name]=raw_pin(complete_raw)
        parent_peak=peak(_GETRUSAGE(resource.RUSAGE_SELF));child_peak=peak(usage) if usage is not None else None
        bound=parent_peak+child_peak if child_peak is not None else None
        pending=(pending and error is None and not _CANCELLED and usage is not None and child.returncode==0
            and bound<=LIMITS['aggregate_owned_bytes'] and now()<JOINT_BEGAN_NS+20000000000)
        ledger={'schema':'Q-projection-outer-native-ledger-v1','CLOCK_DOMAIN':CLOCK_DOMAIN,'joint_began_ns':JOINT_BEGAN_NS,
            'joint_deadline_ns':JOINT_BEGAN_NS+20000000000,'launch_began_ns':launch_ns,'terminal_observed_ns':terminal_ns,
            'parent_pid':os.getpid(),'child_pid':child.pid if child is not None else None,'child_returncode':child.returncode if child is not None else None,
            'wait4_status':wait_status,'all_reaped':usage is not None,'wait4_usage':usage_record(usage) if usage is not None else None,
            'parent_peak_bytes_before_receipts':parent_peak,'child_kernel_peak_bytes':child_peak,'aggregate_bound_bytes_before_receipts':bound,
            'memory_bound_scope':'internal provisional parent self-peak plus exact complete child wait4 peak; true terminal caller peak comes separately from pinned external time -l meter, whose own observer memory is excluded; no other child/observer Source is authorized',
            'external_terminal_meter':meter,'external_terminal_parent_peak_pending':True,
            'owned_elapsed_ns_before_receipts':now()-JOINT_BEGAN_NS,'outputs_before_receipts':files,'error':error,
            'raw_closure':raw_receipts,'ROOT_resource_accepted':False,'ROOT_primary_accepted':False,
            'full52_supported':False,'W16_supported':False,'all_strong_acceptance_false':True}
        ledger_raw=canonical(ledger)+b'\n';write_exclusive(root/'outer-native-ledger.json',ledger_raw,failure=True)
        status={'schema':'Q-projection-outer-provisional-v1','version':VERSION,'pending_external_caller':pending,
            'worker_body':response,'native_ledger':raw_pin(ledger_raw),'whole_outputs':files,'error':error,
            'observed_postwrite_ns':now(),'ROOT_resource_accepted':False,'ROOT_primary_accepted':False,
            'full52_qualified':False,'full_architecture_qualified':False,'original_Q_theorem_accepted':False,
            'actual_selected_accepted':False,'full24_accepted':False,'native_accepted':False,'RL_accepted':False}
        write_exclusive(root/'outer-provisional.json',canonical(status)+b'\n',failure=True)
        notice=canonical({'schema':'Q-projection-outer-bounded-terminal-notice-v1','pending_external_caller':pending,
            'output_directory':str(root),'native_ledger':raw_pin(ledger_raw),'worker_wire':files.get('worker-result.jsonl'),
            'ROOT_resource_accepted':False})
        need(len(notice)<4096,'bounded complete stdout terminal notice');print(notice.decode(),flush=True)
        final_peak=peak(_GETRUSAGE(resource.RUSAGE_SELF));final_ns=now()
        pending=(pending and final_peak+child_peak<=LIMITS['aggregate_owned_bytes']
            and final_ns<JOINT_BEGAN_NS+20000000000 and not _CANCELLED)
        final_observation={'schema':'Q-projection-outer-final-native-observation-v1','observed_after_stdout_ns':final_ns,
            'joint_began_ns':JOINT_BEGAN_NS,'joint_deadline_ns':JOINT_BEGAN_NS+20000000000,
            'parent_peak_bytes_before_final_receipt':final_peak,'complete_child_kernel_peak_bytes':child_peak,
            'aggregate_bound_bytes_before_final_receipt':final_peak+child_peak if child_peak is not None else None,
            'pending_external_caller':pending,'actual_parent_terminal_not_observed_by_self':True,
            'observation_scope':'after stdout, before this final receipt write; return gate and true external terminal remain later',
            'ROOT_resource_accepted':False,'all_strong_acceptance_false':True}
        write_exclusive(root/'outer-final-native-observation.json',canonical(final_observation)+b'\n',failure=True)
        after_receipt_peak=peak(_GETRUSAGE(resource.RUSAGE_SELF))
        after_receipt_ns=now()
        pending=(pending and after_receipt_peak+child_peak<=LIMITS['aggregate_owned_bytes']
            and after_receipt_ns<JOINT_BEGAN_NS+20000000000 and not _CANCELLED)
        if not pending:
            write_exclusive(root/'outer-revocation.json',canonical({'schema':'Q-projection-outer-revocation-v1',
                'pending_external_caller':False,'observed_after_stdout_ns':final_ns,'parent_peak_bytes':final_peak,
                'all_reaped':usage is not None,'error':error,'ROOT_resource_accepted':False})+b'\n',failure=True)
    if pending:
        # No output/helper delegation after this success test: resource first,
        # then a fresh original global clock and cancellation immediately before
        # return. True process exit remains the external caller's observation.
        return_peak=peak(_GETRUSAGE(resource.RUSAGE_SELF))
        return_ns=now()
        if (return_peak+child_peak<=LIMITS['aggregate_owned_bytes']
                and return_ns<JOINT_BEGAN_NS+20000000000 and not _CANCELLED):
            return 0
        pending=False
        write_exclusive(root/'outer-return-revocation.json',canonical({
            'schema':'Q-projection-outer-return-revocation-v1','pending_external_caller':False,
            'observed_before_return_ns':return_ns,'parent_peak_bytes':return_peak,
            'cancelled':_CANCELLED,'all_reaped':usage is not None,
            'ROOT_resource_accepted':False})+b'\n',failure=True)
    return 2


if __name__=='__main__':
    try:raise SystemExit(main(sys.argv[1:]))
    except BaseException as error:
        if type(error) is SystemExit:raise
        sys.stderr.write(type(error).__name__+': '+str(error)+'\n');raise SystemExit(2)
