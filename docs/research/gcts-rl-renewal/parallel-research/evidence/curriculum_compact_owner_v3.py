"""SOURCE ONLY compact owner V3; CLI intentionally cannot dispatch.

ROOT must separately freeze verified platform evidence, an exact accounting
adapter and an outer launcher before library entry may run. No counting rule
is implemented here. Original donor-two-guards is permanently excluded.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

OWNER_HERE=Path(__file__).resolve().parent
OWNER_ROOT=OWNER_HERE.parent.parent
EXACT_IMPORT_DIRECTORY=OWNER_ROOT/'.gcts-active/curriculum-compact-wrapper-source-20261012'
EXACT_TRANSPORT_PIN=dict(path='.gcts-active/curriculum-compact-wrapper-source-20261012/compact_static_transport_v1.py',
    sha256='65a0b598966ae4dffdda1b770eb2d4d5b64af1bcaf6aead4281a224a4123def3',bytes=13756)
EXACT_WORKER_PIN=dict(path='.gcts-active/curriculum-compact-wrapper-source-20261012/curriculum_compact_worker_v1.py',
    sha256='77a15d292833f82ee759b522ed8a615da4bad7d43f48e8ccc218844cac9c1dd3',bytes=13759)


def bootstrap_exact_import_directory():
    """Metadata-only bootstrap for a future ROOT entry; never called by author."""
    for record in (EXACT_TRANSPORT_PIN,EXACT_WORKER_PIN):
        path=OWNER_ROOT/record['path'];digest=hashlib.sha256();count=0
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(65536),b''):
                digest.update(block);count+=len(block)
        if digest.hexdigest()!=record['sha256'] or count!=record['bytes']:
            raise ValueError('exact original compact import source bytes required')
    cached=sys.modules.get('compact_static_transport_v1')
    if cached is not None and Path(cached.__file__).resolve()!=EXACT_IMPORT_DIRECTORY/'compact_static_transport_v1.py':
        raise ValueError('no alternate cached transport module')
    sys.path.insert(0,str(EXACT_IMPORT_DIRECTORY))


bootstrap_exact_import_directory()
from compact_static_transport_v1 import (HERE,ROOT,require_contract,verify_pin,
    stream_pin,read_small,validate_compact,write_new,raw_usage,
    read_closed_SELF,emit_closed_SELF_and_exit)
if Path(sys.modules['compact_static_transport_v1'].__file__).resolve()!=EXACT_IMPORT_DIRECTORY/'compact_static_transport_v1.py':
    raise ValueError('exact original pinned transport import directory')


def require_v3_group_contract(plan,contract):
    """ROOT supplies a fresh direct owner group leader; no group is created here."""
    if contract.get('fresh_ROOT_owned_owner_group_required') is not True:
        raise ValueError('separately ROOT-owned fresh process group required')
    owner_pid=os.getpid();group=os.getpgrp();session=os.getsid(0)
    if owner_pid!=group or owner_pid!=session:
        raise ValueError('owner must be ROOT fresh retained session/process-group leader')
    expected_worker={key:contract['worker_pin'][key] for key in ('path','sha256','bytes')}
    expected_transport={key:contract['transport_pin'][key] for key in ('path','sha256','bytes')}
    if expected_worker!=EXACT_WORKER_PIN or expected_transport!=EXACT_TRANSPORT_PIN:
        raise ValueError('V3 reuses exact original compact worker/transport bytes')
    containment=Path(contract['containment_output'])
    directory=Path(plan['outputs']['lifetime']).parent
    if (not containment.is_absolute() or containment.parent!=directory
            or containment in [Path(path) for path in plan['outputs'].values()]):
        raise ValueError('distinct supplemental containment path in unchanged fresh selector directory')
    if containment.exists():raise ValueError('containment publication must be still unexecuted')
    return dict(owner_pid=owner_pid,owner_pgid=group,owner_sid=session,ROOT_parent_pid=os.getppid())


def require_finite_closed_SELF(frame):
    names=('seconds_after_all_artifact_close_before_fixed_postlude',
           'entry_monotone_clock','last_closed_monotone_clock')
    if any(type(frame[name]) is not float or not math.isfinite(frame[name]) for name in names):
        raise ValueError('every raw SELF frame clock must be finite')
    elapsed,start,closed=(frame[name] for name in names)
    if (elapsed<0 or closed<start or elapsed!=closed-start
            or type(frame['SELF_ru_maxrss_raw']) is not int or frame['SELF_ru_maxrss_raw']<0):
        raise ValueError('exact finite SELF time relation and nonnegative raw peak')
    return frame


def contain_until_ROOT_group_termination(plan,group,reason,detail):
    """Never returns or emits a final SELF frame. ROOT terminates the live group.

    This parent cannot wait4-reap grandchildren. Every emergency is UNKNOWN.
    A publication failure also retains the leader until ROOT's complete gate.
    """
    try:
        contract=plan['compact_transport_contract'];path=Path(contract['containment_output'])
        temporary=path.with_name(path.name+'.closed-owner-'+str(os.getpid())+'.tmp')
        receipt=dict(schema='compact-owner-V3-live-group-containment-v1',status='UNKNOWN_REQUIRES_ROOT_LIVE_GROUP_TERMINATION',
            selector=plan['selector'],owner=stream_pin(Path(__file__)),group=group,
            reason=reason,detail=detail,clock_before_containment_serialization=time.perf_counter(),
            direct_owner_leader_retained=True,grandchildren_reaped_claim=False,
            success_SELF_frame_emitted=False,full_resource_accepted=False,all_five_qualification=False,
            whole_seconds=180,supervisor_seconds=175,child_seconds=170,peak_bytes=536870912)
        raw=json.dumps(receipt,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()+b'\n'
        if len(raw)>contract['compact_maximum_bytes']:
            raise ValueError('closed containment latch exceeds existing compact metadata envelope')
        with temporary.open('xb') as stream:stream.write(raw)
        # A closed inode is published exactly once; ROOT never reads partial JSON.
        os.link(str(temporary),str(path))
        temporary.unlink()
    except BaseException:
        # No further write/retry/exit: ROOT's retained direct leader and outer
        # deadline still own cleanup if the exclusive publication failed.
        pass
    while True:
        try:time.sleep(.02)
        except BaseException:continue


class DetailStream:
    """Append exact records without retaining a growing sample table in RAM."""
    def __init__(self,path):
        self.path=Path(path);self.stream=self.path.open('x');self.count=0;self.closed=False
    def append(self,value):
        value=dict(index=self.count,**value)
        self.stream.write(json.dumps(value,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n')
        self.stream.flush();self.count+=1
        return time.perf_counter()
    def close(self):
        if not self.closed:self.stream.close();self.closed=True
        return dict(pin=stream_pin(self.path),records=self.count)


def wait_terminal(child):
    while True:
        try:pid,status,usage=os.wait4(child.pid,0);break
        except InterruptedError:continue
    if pid!=child.pid:raise RuntimeError('exact owned direct child reap')
    child.returncode=os.waitstatus_to_exitcode(status)
    return usage


def stop_unreaped(child):
    # Caller proves this handle has not been terminal-reaped. Do not signal
    # historical PIDs or a group after the direct child terminal is consumed.
    try:os.kill(child.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    return wait_terminal(child)


def observe(plan,index,owner_started,check_cancel,expected_worker_pid,group):
    """One direct pinned ps child, two closed streams, exactly one wait4.

    Terminal usage stays RAW; no RUSAGE_CHILDREN query or unit inference.
    ROOT's platform adapter must establish observer leaf and memory semantics.
    """
    c=plan['compact_transport_contract']
    if c['observer_seconds']!=1:raise ValueError('unchanged one-second metadata timeout')
    binary=verify_pin(plan['runtime']['observer'])
    directory=Path(plan['outputs']['lifetime']).parent
    outpath=directory/('observer-'+str(index)+'-stdout.txt')
    errpath=directory/('observer-'+str(index)+'-stderr.txt')
    command=[str(binary),'-axo','pid=,ppid=,pgid=,lstart=,rss=']
    child=None;usage=None;waited=False;failure=None;after_spawn=None;cleanup_failure=None;clock_before=time.perf_counter()
    try:
        check_cancel()
        with outpath.open('xb') as out,errpath.open('xb') as err:
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
            after_spawn=time.perf_counter()
            # Signal handlers only set flags; handle registration is coherent.
            check_cancel()
            while True:
                check_cancel()
                pid,status,current=os.wait4(child.pid,os.WNOHANG)
                if pid:
                    waited=True;usage=current;child.returncode=os.waitstatus_to_exitcode(status)
                    # Only after terminal bookkeeping may cancellation raise.
                    check_cancel();break
                if time.perf_counter()-clock_before>=c['observer_seconds']:
                    raise TimeoutError('owned direct observer one-second lifetime')
                if max(outpath.stat().st_size,errpath.stat().st_size)>c['observer_stream_maximum_bytes']:
                    raise RuntimeError('ROOT-frozen observer stream envelope')
                time.sleep(.001)
    except BaseException as exc:failure=type(exc).__name__+': '+str(exc)
    finally:
        if child is not None and not waited:
            try:usage=stop_unreaped(child);waited=True
            except BaseException as exc:
                cleanup_failure=type(exc).__name__+': '+str(exc)
                failure=failure or cleanup_failure
        terminal=time.perf_counter()
    receipt=dict(observer_id=index,owner_pid=os.getpid(),observer_pid=child.pid if child else None,
        command=command,binary=plan['runtime']['observer'],clock_before_spawn=clock_before,
        clock_after_spawn=after_spawn if child else None,clock_after_stream_close_and_terminal_reap=terminal,
        seconds_from_owner_entry=terminal-owner_started,exit_code=child.returncode if child else None,
        reaped=waited,terminal_wait4_raw=raw_usage(usage) if usage else None,
        failure=failure,cleanup_failure=cleanup_failure,requires_outer_containment=bool(cleanup_failure),
        inherited_owner_group=group,unexpected_descendant_rows=[],unexpected_group_rows=[],
        raw_usage_scope='Direct observer wait4; expected leaf, verified ROOT platform evidence required')
    for name,path in [('stdout',outpath),('stderr',errpath)]:
        if path.exists():receipt[name]=stream_pin(path)
    rows={}
    try:
        if failure or child is None or not waited or child.returncode!=0:
            raise RuntimeError('observer terminal failure; no resource qualification')
        if max(outpath.stat().st_size,errpath.stat().st_size)>c['observer_stream_maximum_bytes']:
            raise RuntimeError('observer final stream envelope')
        with outpath.open() as stream:
            for line in stream:
                parts=line.split()
                if len(parts)<5:raise ValueError('exact PID/PPID/PGID/birth/RSS row')
                pid,ppid,pgid=map(int,parts[:3]);rss=int(parts[-1]);birth=' '.join(parts[3:-1])
                if min(pid,ppid,pgid,rss)<0 or not birth or pid in rows:
                    raise ValueError('unique nonnegative process metadata and birth identity')
                rows[pid]=dict(pid=pid,ppid=ppid,pgid=pgid,birth=birth,RSS_ps_raw=rss)
        observer_family=owned_rows(rows,child.pid,{})
        worker_family=owned_rows(rows,expected_worker_pid,{})
        receipt['unexpected_descendant_rows']=[row for row in observer_family+worker_family
            if row['pid'] not in (child.pid,expected_worker_pid)]
        receipt['unexpected_group_rows']=[row for row in rows.values()
            if row['pgid']==group['owner_pgid'] and row['pid'] not in (group['owner_pid'],child.pid,expected_worker_pid)]
        if receipt['unexpected_descendant_rows'] or receipt['unexpected_group_rows']:
            receipt['requires_outer_containment']=True
            raise RuntimeError('unexpected descendants/group members; ROOT retains live group containment authority')
    except BaseException as exc:
        receipt['failure']=receipt['failure'] or type(exc).__name__+': '+str(exc);rows=None
    receipt['clock_after_parse_and_stream_hash']=time.perf_counter()
    return rows,receipt


def owned_rows(rows,worker_pid,identities):
    active={worker_pid}
    while True:
        following=active|{pid for pid,row in rows.items() if row['ppid'] in active}
        if following==active:break
        active=following
    owned=[rows[pid] for pid in sorted(active) if pid in rows]
    for row in owned:
        if row['pid'] in identities and identities[row['pid']]!=row['birth']:
            raise RuntimeError('owned PID birth identity changed')
        identities.setdefault(row['pid'],row['birth'])
    return owned


def require_accounting_adapter(accounting,contract):
    """Interface binding only: no final platform rule or adapter is supplied."""
    if (accounting.source_pin!=contract['accounting_adapter_pin']
            or accounting.platform_evidence_pin!=contract['platform_evidence_pin']):
        raise ValueError('separately ROOT-frozen exact platform counting adapter')
    verify_pin(accounting.source_pin);verify_pin(accounting.platform_evidence_pin)
    for method in ('add_observer','add_sample','add_leaf_worker','add_SELF_before_receipt',
                   'rejects_current_caps','finish_provisional'):
        if not callable(getattr(accounting,method,None)):
            raise ValueError('complete separately reviewed accounting interface')


def run_owner(planpath,accounting):
    """Future ROOT library entry only, ends with fixed SELF frame/os._exit.

    accounting is not implemented or instantiated by this source package.
    Neither a positive worker nor an adapter can issue full ROOT qualification.
    """
    started=time.perf_counter();planpath=Path(planpath).resolve()
    # Actual plans are small pinned metadata with an independently frozen size
    # envelope; ROOT must bind them before this library entry can be called.
    plan=json.loads(planpath.read_text())
    contract=require_contract(plan,planpath,Path(plan['worker_path']))
    group=require_v3_group_contract(plan,contract)
    require_accounting_adapter(accounting,contract)
    if stream_pin(Path(__file__))!=contract['owner_pin']:raise ValueError('exact owner source')
    if (plan['runtime']['executable']!=sys.executable or plan['runtime']['platform']!=sys.platform):
        raise ValueError('same pinned actual runtime')
    verify_pin(plan['runtime']['binary']);verify_pin(plan['runtime']['observer'])
    checked={}
    for group in ('sources','libraries','inputs','preserved'):
        for record in plan[group]:
            exact={k:record[k] for k in ('path','sha256','bytes')}
            if record['path'] in checked and checked[record['path']]!=exact:
                raise ValueError('conflicting immutable pin spelling')
            if record['path'] not in checked:verify_pin(record);checked[record['path']]=exact
    activationpath=Path(plan['activation_path'])
    activation=read_small(activationpath,contract['compact_maximum_bytes'])
    if (activation.get('schema')!='ROOT-independent-frozen-curriculum-compact-static-activation-v1'
            or activation.get('authorized') is not True or activation.get('plan')!=stream_pin(planpath)
            or activation.get('selector')!=plan['selector']):
        raise ValueError('separate ROOT exact compact static activation after source review')
    outputs=plan['outputs'];directory=Path(outputs['lifetime']).parent
    if directory.exists():raise ValueError('one still-unexecuted immutable namespace; never a rerun')
    directory.mkdir(parents=True,exist_ok=False)
    observers=DetailStream(outputs['observers']);samples=DetailStream(outputs['samples'])
    child=None;usage=None;waited=False;child_start=None;worker_terminal_clock=None
    failure=None;compact=None;worker_SELF=None
    identities={};observer_count=0;provisional_accounting=None
    cancelled_signum=0
    def cancellation_flag(signum,_frame):
        nonlocal cancelled_signum
        cancelled_signum=signum
    def check_cancel():
        if cancelled_signum:
            raise TimeoutError('owned cancellation flag at safe boundary: '+str(cancelled_signum))
    signal.signal(signal.SIGTERM,cancellation_flag);signal.signal(signal.SIGALRM,cancellation_flag)
    signal.signal(signal.SIGINT,cancellation_flag)
    signal.setitimer(signal.ITIMER_REAL,max(.001,175-(time.perf_counter()-started)))
    try:
        check_cancel()
        with Path(outputs['stdout']).open('xb') as out,Path(outputs['stderr']).open('xb') as err:
            child_start=time.perf_counter()
            child=subprocess.Popen([sys.executable,'-B',plan['worker_path'],str(planpath)],
                stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            # No asynchronous raising handler can discard this registered handle.
            check_cancel()
            while True:
                check_cancel()
                pid,status,current=os.wait4(child.pid,os.WNOHANG)
                if pid:
                    waited=True;usage=current;child.returncode=os.waitstatus_to_exitcode(status)
                    worker_terminal_clock=time.perf_counter()
                    check_cancel();break
                if time.perf_counter()-started>=175:raise TimeoutError('complete owner supervisor gate')
                if observer_count>=contract['maximum_observers']:raise RuntimeError('ROOT-frozen observer metadata count')
                rows,receipt=observe(plan,observer_count,started,check_cancel,child.pid,group);observer_count+=1
                observer_close=observers.append(receipt);accounting.add_observer(receipt)
                if receipt['requires_outer_containment']:
                    raise RuntimeError('closed observer record requires live ROOT group containment')
                if rows is None:raise RuntimeError('owned observer failure after terminal reap')
                owned=owned_rows(rows,child.pid,identities)
                if any(row['pid']!=child.pid for row in owned):
                    raise RuntimeError('scientific worker launched a descendant; leaf-source contract violated')
                if os.getpid() not in rows:raise RuntimeError('SELF sampling unavailable')
                if (rows[os.getpid()]['pgid']!=group['owner_pgid']
                        or rows[os.getpid()]['ppid']!=group['ROOT_parent_pid']
                        or any(row['pgid']!=group['owner_pgid'] or row['ppid']!=group['owner_pid'] for row in owned)):
                    raise RuntimeError('observed fresh group/direct parent ownership changed')
                sample=dict(clock=time.perf_counter(),owner_SELF_row=rows[os.getpid()],worker_rows=owned,
                    inherited_ROOT_owner_group=group,
                    observer_id=receipt['observer_id'],observer_detail_append_close_clock=observer_close,
                    scope='Exact owned worker/SELF ps rows; separate direct observer terminal usage',
                    direct_worker_PID=child.pid)
                samples.append(sample);accounting.add_sample(sample)
                if accounting.rejects_current_caps():raise MemoryError('separately verified unchanged512MiB rule rejected')
                time.sleep(.02)
        check_cancel()
        child_seconds=worker_terminal_clock-child_start
        if child.returncode!=0:raise RuntimeError('scientific worker nonzero terminal')
        if child_seconds>170:raise TimeoutError('full scientific child170second exit/reap gate')
        worker_SELF=require_finite_closed_SELF(read_closed_SELF(outputs['stdout'],1,child.pid))
        if worker_SELF['exit_code']!=0:raise RuntimeError('worker terminal SELF frame rejected')
        if (worker_SELF['entry_monotone_clock']<child_start
                or worker_SELF['last_closed_monotone_clock']>worker_terminal_clock):
            raise ValueError('same verified cross-process monotone clock and complete child lifetime')
        accounting.add_leaf_worker(raw_usage(usage),worker_SELF,child_seconds)
        compact=validate_compact(plan,planpath,Path(plan['worker_path']),activationpath)
    except BaseException as exc:failure=dict(type=type(exc).__name__,message=str(exc))
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        if child is not None and not waited:
            try:
                usage=stop_unreaped(child);waited=True
                worker_terminal_clock=time.perf_counter()
            except BaseException as exc:
                failure=failure or dict(type=type(exc).__name__,message='direct worker cleanup: '+str(exc))
        try:observer_artifact=observers.close();sample_artifact=samples.close()
        except BaseException:
            contain_until_ROOT_group_termination(plan,group,'detail stream close or streamed pin failed',
                dict(child_pid=child.pid if child else None,child_reaped=waited,observer_count=observer_count))
    if cancelled_signum:
        failure=failure or dict(type='TimeoutError',message='owned non-raising cancellation requested before receipt')
    elapsed=time.perf_counter()-started
    if elapsed>175:failure=failure or dict(type='TimeoutError',message='owner complete pre-receipt175second gate')
    if failure:
        contain_until_ROOT_group_termination(plan,group,'post-spawn failure or cancellation',
            dict(failure=failure,cancellation_signum=cancelled_signum,
                 child_pid=child.pid if child else None,child_reaped=waited,
                 child_exit=child.returncode if child else None,observer_count=observer_count,
                 observer_detail=observer_artifact,sample_detail=sample_artifact))
    try:
        SELF_before=raw_usage(resource.getrusage(resource.RUSAGE_SELF))
        accounting.add_SELF_before_receipt(SELF_before)
        try:provisional_accounting=accounting.finish_provisional()
        except BaseException as exc:failure=failure or dict(type=type(exc).__name__,message=str(exc))
        receipt=dict(schema='compact-static-owner-pending-ROOT-lifetime-v1',
            status='completed_compact_semantic_candidate_pending_full_ROOT_resources' if compact and not failure else 'UNKNOWN_compact_static_owner',
            selector=plan['selector'],plan=stream_pin(planpath),owner=stream_pin(Path(__file__)),
            worker=contract['worker_pin'],activation=stream_pin(activationpath),
            source_manifest=contract['wrapper_source_manifest_pin'],platform_evidence=contract['platform_evidence_pin'],
            accounting_adapter=contract['accounting_adapter_pin'],
            inherited_ROOT_owner_group=group,containment_output=contract['containment_output'],
            child_pid=child.pid if child else None,child_exit=child.returncode if child else None,child_reaped=waited,
            worker_terminal_wait4_raw=raw_usage(usage) if usage else None,worker_closed_SELF=worker_SELF,
            raw_wait4_scope='Worker expected leaf; no subtraction from rolled nested peaks',
            child_seconds_including_startup_imports_all_serialization_exit_reap=worker_terminal_clock-child_start if child_start and worker_terminal_clock else None,
            observer_detail=observer_artifact,sample_detail=sample_artifact,observer_count=observer_count,
            SELF_before_final_receipt_serialization_raw=SELF_before,
            provisional_platform_accounting=provisional_accounting,
            full_audit=compact['full_audit'] if compact else stream_pin(Path(outputs['result'])) if Path(outputs['result']).exists() else None,
            compact_status=stream_pin(Path(outputs['compact'])) if Path(outputs['compact']).exists() else None,
            semantic_static_candidate=bool(compact),static_context_pool_accepted=False,
            full_resource_accepted=False,all_five_qualification=False,
            failure=failure,cancellation_signum=cancelled_signum,cancellation_requested=bool(cancelled_signum),
            cancellation_semantics='Non-raising INT/TERM/ALRM flags; checked only after spawn registration/terminal wait4 bookkeeping and at safe loop boundaries',
            owner_seconds_before_lifetime_receipt_write=elapsed,
            maximum_whole_seconds=180,maximum_supervisor_seconds=175,maximum_child_seconds=170,
            maximum_peak_bytes=536870912,OS_hard_cap_claim=False,
            remaining_scope='After this closed receipt: raw SELF snapshot, fixed52byte terminal frame, os._exit. ROOT separately reviews preserved reserve and full180second launcher/dispatcher accounting.',
            native_queries=0,searches_run_by_owner=0,training_runs=0)
        write_new(outputs['lifetime'],receipt)
        if cancelled_signum or failure:
            contain_until_ROOT_group_termination(plan,group,'late cancellation or provisional accounting failure',
                dict(cancellation_signum=cancelled_signum,failure=failure,lifetime_receipt=stream_pin(Path(outputs['lifetime'])),
                     observer_detail=observer_artifact,sample_detail=sample_artifact))
        # No interpreter atexit/print follows the post-close SELF reading. All
        # owner artifact files and detail streams are closed before this call.
        emit_closed_SELF_and_exit(2,started,0 if compact and not failure and not cancelled_signum else 1)
    except BaseException:
        contain_until_ROOT_group_termination(plan,group,"final metadata/accounting/SELF path failed",
            dict(child_pid=child.pid if child else None,child_reaped=waited,observer_count=observer_count))


def main():
    raise RuntimeError('SOURCE ONLY: no platform adapter/CLI binding frozen. ROOT must separately review and bind run_owner; no actual phase can dispatch from this package.')


if __name__=='__main__':main()
