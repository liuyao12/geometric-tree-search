"""ROOT-only non-scientific Darwin resource calibration; one fixed attempt.

No project imports, proofs, model construction, random draws or search. Fresh
processes touch fixed byte arrays. Every direct child is reaped with wait4;
ps observers have separate leaf records, never cumulative RUSAGE_CHILDREN.
"""
import time
ENTRY = time.perf_counter()
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SOURCE = Path(__file__).resolve()
FRAME = struct.Struct('!8sBBHQQddd')
CANCELLED = None
UNRESOLVED_NONLEAF = False
FIXED_CASES = [('leaf16', 0, [16]), ('leaf48', 0, [48]),
               ('parent16-child48', 16, [48]), ('parent48-child16', 48, [16]),
               ('parent16-two48-sequential', 16, [48, 48])]


def pin(path):
    path = Path(path); sha = hashlib.sha256(); total = 0
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(65536), b''):
            sha.update(chunk); total += len(chunk)
    return dict(path=str(path), sha256=sha.hexdigest(), bytes=total)


def write(path, value):
    path = Path(path); temporary = path.with_name(path.name+'.partial')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
    os.link(temporary, path); temporary.unlink()


def read(path):
    with Path(path).open('rb') as stream: raw = stream.read(1048577)
    if len(raw) > 1048576: raise ValueError('bounded calibration metadata')
    return json.loads(raw)


def raw_usage(value):
    return {name: getattr(value, name) for name in dir(value) if name.startswith('ru_')}


def cutoff(*_):
    global CANCELLED
    CANCELLED = 'fixed non-scientific calibration cancellation/deadline'


def check_cancel():
    if CANCELLED: raise TimeoutError(CANCELLED)


def touch(mib):
    value = bytearray(mib * 1048576)
    for i in range(0, len(value), 4096): value[i] = 1
    return value


def terminal(role, code):
    check_cancel()
    closed = time.perf_counter()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    frame = FRAME.pack(b'GCTSCMP1', role, code, 0, os.getpid(), int(usage.ru_maxrss),
                       closed - ENTRY, ENTRY, closed)
    try:
        offset = 0
        while offset < len(frame):
            n = os.write(1, frame[offset:])
            if n <= 0: raise OSError('terminal frame')
            offset += n
    except BaseException: os._exit(2)
    os._exit(code)


def frame(path, role, pid):
    with Path(path).open('rb') as stream: raw = stream.read(FRAME.size + 1)
    if len(raw) != FRAME.size: raise ValueError('exact fixed terminal frame')
    magic, actual, code, reserved, birth, rss, seconds, start, close = FRAME.unpack(raw)
    if magic != b'GCTSCMP1' or actual != role or birth != pid or reserved or code:
        raise ValueError('terminal role/PID/success frame')
    if (rss<=0 or not all(math.isfinite(v) for v in (seconds,start,close))
            or seconds<0 or close<start or abs((close-start)-seconds)>.000001):
        raise ValueError('finite SELF and exact ordered monotone clocks')
    return dict(pid=pid, role=role, SELF_ru_maxrss_raw=rss,
                seconds_through_all_artifact_close=seconds, entry=start, last_close=close,
                pin=pin(path))


def stop_owned(child, leaf):
    """Cooperate through inner finally blocks; never certify an emergency kill."""
    global UNRESOLVED_NONLEAF
    if child.returncode is not None: return
    try: os.kill(child.pid,signal.SIGTERM)
    except ProcessLookupError: pass
    deadline=time.perf_counter()+3
    while True:
        pid,status,usage=os.wait4(child.pid,os.WNOHANG)
        if pid:
            child.returncode=os.waitstatus_to_exitcode(status)
            write(HERE/('cleanup-reaped-%s.json'%child.pid),dict(pid=child.pid,
                exit_code=child.returncode,reaped=True,leaf=leaf,wait4_raw=raw_usage(usage)))
            return
        if time.perf_counter()>=deadline: break
        time.sleep(.01)
    if not leaf:
        UNRESOLVED_NONLEAF=True
        raise RuntimeError('UNKNOWN: cooperative nonleaf cleanup unacknowledged; external group cleanup required')
    try: os.kill(child.pid,signal.SIGKILL)
    except ProcessLookupError: pass
    _,status,usage=os.wait4(child.pid,0);child.returncode=os.waitstatus_to_exitcode(status)
    write(HERE/('cleanup-reaped-%s.json'%child.pid),dict(pid=child.pid,
        exit_code=child.returncode,reaped=True,leaf=True,wait4_raw=raw_usage(usage)))


def owned_wait(child, deadline, leaf=True):
    try:
        while True:
            check_cancel()
            pid, status, usage = os.wait4(child.pid, os.WNOHANG)
            if pid:
                child.returncode = os.waitstatus_to_exitcode(status)
                if child.returncode: raise RuntimeError('calibration child failed')
                return raw_usage(usage)
            if time.perf_counter() >= deadline: raise TimeoutError('calibration child deadline')
            time.sleep(.01)
    except BaseException:
        stop_owned(child,leaf)
        raise


def observer(pids, directory, index):
    stdout = directory / ('observer-%s.stdout' % index)
    stderr = directory / ('observer-%s.stderr' % index)
    argv = ['/bin/ps', '-p', ','.join(str(p) for p in pids), '-o', 'pid=,ppid=,rss=']
    started = time.perf_counter()
    with stdout.open('xb') as out, stderr.open('xb') as err:
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                 start_new_session=False)
        usage = owned_wait(child, started + 2)
    rows=[]
    for line in stdout.read_text().splitlines():
        parts=line.split()
        if not parts:continue
        if len(parts)!=3:raise ValueError('literal three-column calibration ps schema')
        rows.append(dict(zip(('pid','ppid','RSS_1024_byte_units'),map(int,parts))))
    if (len(rows)!=len(pids) or set(r['pid'] for r in rows)!=set(pids)
            or any(r['RSS_1024_byte_units']<0 for r in rows)):
        raise ValueError('unique exact owned PIDs and nonnegative RSS sampled')
    return dict(pid=child.pid, argv=argv, exit_code=child.returncode, reaped=True,
                leaf=True, wait4_raw=usage, rows=rows, stdout=pin(stdout), stderr=pin(stderr),
                whole_seconds=time.perf_counter()-started)


def leaf(plan, directory, index, mib):
    signal.alarm(4)
    allocated = touch(mib)
    check_cancel()
    write(directory / ('leaf-%s-ready.json' % index), dict(pid=os.getpid(), ppid=os.getppid(),
          touched_bytes=len(allocated), SELF_before_hold=raw_usage(resource.getrusage(resource.RUSAGE_SELF))))
    time.sleep(.8)
    check_cancel()
    write(directory / ('leaf-%s-receipt.json' % index), dict(status='fixed_non_scientific_leaf_completed',
          touched_bytes=len(allocated), no_children=True,
          SELF_before_receipt=raw_usage(resource.getrusage(resource.RUSAGE_SELF))))
    signal.alarm(0); terminal(1, 0)


def parent(plan, directory, own_mib, child_mibs):
    signal.alarm(9)
    allocated = touch(own_mib)
    initial = raw_usage(resource.getrusage(resource.RUSAGE_SELF))
    children = []
    for index, mib in enumerate(child_mibs):
        check_cancel()
        stdout, stderr = directory / ('leaf-%s.stdout' % index), directory / ('leaf-%s.stderr' % index)
        with stdout.open('xb') as out, stderr.open('xb') as err:
            child=None
            try:
                child = subprocess.Popen([sys.executable, '-B', str(SOURCE), 'leaf', str(HERE/'plan-v4.json'),
                    str(directory), str(index), str(mib)], stdin=subprocess.DEVNULL,
                    stdout=out, stderr=err, start_new_session=False)
                usage = owned_wait(child, time.perf_counter()+4)
            finally:
                if child is not None: stop_owned(child,True)
        children.append(dict(pid=child.pid, exit_code=child.returncode, reaped=True,
            wait4_raw=usage, leaf_frame=frame(stdout, 1, child.pid),
            SELF_after_reap=raw_usage(resource.getrusage(resource.RUSAGE_SELF)),
            CHILDREN_after_reap=raw_usage(resource.getrusage(resource.RUSAGE_CHILDREN))))
    write(directory/'parent-receipt.json', dict(status='fixed_non_scientific_parent_completed',
        touched_bytes=len(allocated), SELF_initial=initial, children=children,
        SELF_after_all_reaps=raw_usage(resource.getrusage(resource.RUSAGE_SELF)),
        CHILDREN_after_all_reaps=raw_usage(resource.getrusage(resource.RUSAGE_CHILDREN))))
    signal.alarm(0); terminal(2, 0)


def coordinator(plan):
    signal.alarm(55)
    directory = HERE/'outputs'; directory.mkdir(exist_ok=False)
    results = []; observers = []
    for name, own_mib, child_mibs in FIXED_CASES:
        check_cancel()
        case = directory/name; case.mkdir()
        is_leaf = own_mib == 0
        stdout, stderr = case/'actor.stdout', case/'actor.stderr'
        argv = [sys.executable, '-B', str(SOURCE), 'leaf' if is_leaf else 'parent',
                str(HERE/'plan-v4.json'), str(case)]
        argv += ['0', str(child_mibs[0])] if is_leaf else [str(own_mib), ','.join(map(str,child_mibs))]
        with stdout.open('xb') as out, stderr.open('xb') as err:
            child=None
            try:
                child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=False)
                sampled = set(); deadline = time.perf_counter()+10
                while True:
                    check_cancel()
                    for index in range(len(child_mibs)):
                        ready = case/('leaf-%s-ready.json' % index)
                        if ready.exists() and index not in sampled:
                            data = read(ready); targets = [child.pid] if is_leaf else [child.pid,data['pid']]
                            obs = observer(targets, case, index)
                            expected={child.pid:os.getpid()}
                            if is_leaf:
                                if data['pid']!=child.pid or data['ppid']!=os.getpid():
                                    raise ValueError('same registered direct calibration leaf')
                            else:
                                if data['ppid']!=child.pid:raise ValueError('registered actor owns exact nested leaf')
                                expected[data['pid']]=child.pid
                            if {r['pid']:r['ppid'] for r in obs['rows']}!=expected:
                                raise ValueError('live observed exact owned ancestry')
                            obs['case'] = name; obs['leaf_index'] = index
                            obs['sampled_ready_pin'] = pin(ready); observers.append(obs); sampled.add(index)
                    pid, status, usage = os.wait4(child.pid, os.WNOHANG)
                    if pid:
                        child.returncode=os.waitstatus_to_exitcode(status)
                        if child.returncode: raise RuntimeError('fixed calibration case exit')
                        break
                    if time.perf_counter() >= deadline: raise TimeoutError('fixed calibration case deadline')
                    time.sleep(.01)
            finally:
                if child is not None: stop_owned(child,is_leaf)
        if sampled != set(range(len(child_mibs))): raise ValueError('missing non-scientific sample')
        results.append(dict(name=name, own_touched_mib=own_mib, child_touched_mib=child_mibs,
            pid=child.pid, reaped=True, exit_code=child.returncode, wait4_raw=raw_usage(usage),
            actor_frame=frame(stdout,1 if is_leaf else 2,child.pid),
            parent_receipt=read(case/'parent-receipt.json') if not is_leaf else None))
    write(directory/'calibration-result-v1.json', dict(status='completed_fixed_non_scientific_platform_calibration',
        plan=pin(HERE/'plan-v4.json'), source=pin(SOURCE), cases=results, observers=observers,
        scientific_calls=0, project_imports=0, random_draws=0, proof_searches=0,
        qualification_scope='Raw finite unit/roll-up observations only; no mathematical/proof/RL qualification'))
    signal.alarm(0); terminal(3,0)


def external(plan):
    signal.alarm(60)
    if (plan['schema']!='ROOT-fixed-non-scientific-platform-calibration-v1'
            or plan['cases'] != [[n,a,b] for n,a,b in FIXED_CASES]
            or pin(SOURCE)!=plan['source'] or pin(Path(sys.executable).resolve())!=plan['python_binary']
            or pin('/bin/ps')!=plan['ps_binary'] or sys.platform!='darwin'
            or plan['limits']!=dict(whole_seconds=60, case_seconds=10, leaf_seconds=4,
                                   peak_bytes=268435456, memory_reserve_bytes=33554432)):
        raise ValueError('exact ROOT-frozen non-scientific source/runtime/cases/bounds')
    if (HERE/'outputs').exists() or (HERE/'external-receipt-v1.json').exists():
        raise ValueError('one immutable calibration attempt; no retry')
    stdout,stderr=HERE/'coordinator.stdout',HERE/'coordinator.stderr'
    child=None
    try:
        with stdout.open('xb') as out,stderr.open('xb') as err:
            child=subprocess.Popen([sys.executable,'-B',str(SOURCE),'coordinator',str(HERE/'plan-v4.json')],
                stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=False)
            usage=owned_wait(child,ENTRY+57,False)
    except BaseException as exc:
        write(HERE/'external-failed-cleanup-v4.json',dict(status='UNKNOWN_NO_CALIBRATION_QUALIFICATION',
            error=dict(type=type(exc).__name__,message=str(exc)),
            emergency_group_cleanup=bool(child is not None and child.returncode is None),
            descendant_reaping_qualified=False,original_donor_two_guards_UNKNOWN_preserved=True))
        if child is not None and child.returncode is None:
            # All actors/leaves share this session. This last resort prevents
            # live escaped work; it does NOT establish descendant wait4 reaping.
            # ROOT entry owns this still-live external group leader and will
            # reap it. Kill includes external itself; no false success frame.
            os.killpg(os.getpgrp(),signal.SIGKILL)
        raise
    result=read(HERE/'outputs/calibration-result-v1.json')
    rootframe=frame(stdout,3,child.pid)
    max_actor=max(c['actor_frame']['SELF_ru_maxrss_raw'] for c in result['cases'])
    max_leaf=max(c['leaf_frame']['SELF_ru_maxrss_raw'] for case in result['cases']
                 for c in (case['parent_receipt'] or {}).get('children',[]))
    observer_peak=max(o['wait4_raw']['ru_maxrss'] for o in result['observers'])
    own=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Distinct active roles. Separate direct-leaf cases are already covered by
    # max_actor; including max_leaf additionally is conservative, never a discount.
    conservative=own+rootframe['SELF_ru_maxrss_raw']+max_actor+max_leaf+observer_peak+33554432
    write(HERE/'external-receipt-v1.json',dict(status='completed_non_scientific_calibration_external_lifetime',
        plan=pin(HERE/'plan-v4.json'),result=pin(HERE/'outputs/calibration-result-v1.json'),
        coordinator_pid=child.pid,coordinator_reaped=True,coordinator_exit_code=child.returncode,
        coordinator_wait4_raw=usage,coordinator_frame=rootframe,
        distinct_scope_peak_sum_raw_plus_32MiB=conservative,
        raw_bytes_interpretation_pending_independent_platform_review=True,
        estimate_under_fixed_256MiB=conservative<=268435456,
        external_seconds_before_final_receipt=time.perf_counter()-ENTRY,
        remaining_scope='External receipt close/fixed52-byte postlude/hard exit within declared32MiB reserve; retrospective estimate, no OS hard cap',
        original_donor_two_guards_UNKNOWN_preserved=True))
    signal.alarm(0);terminal(4,0)


if __name__=='__main__':
    signal.signal(signal.SIGALRM,cutoff);signal.signal(signal.SIGTERM,cutoff)
    signal.signal(signal.SIGINT,cutoff)
    mode=sys.argv[1];plan=read(sys.argv[2])
    try:
        if mode=='leaf':leaf(plan,Path(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]))
        elif mode=='parent':parent(plan,Path(sys.argv[3]),int(sys.argv[4]),list(map(int,sys.argv[5].split(','))))
        elif mode=='coordinator':coordinator(plan)
        elif mode=='external':external(plan)
        else:raise ValueError('fixed calibration mode')
    except BaseException:
        if mode=='coordinator' and UNRESOLVED_NONLEAF:
            write(HERE/'unresolved-contained-coordinator-v3.json',dict(status='UNKNOWN_AWAITING_EXTERNAL_GROUP_CLEANUP',
                coordinator_pid=os.getpid(),descendant_reaping_qualified=False))
            # Keep registered coordinator/group identity alive until its owner
            # terminates it; do not release the leader PID before group cleanup.
            while True:time.sleep(.1)
        raise
