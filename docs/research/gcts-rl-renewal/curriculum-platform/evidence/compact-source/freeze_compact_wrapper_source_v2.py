"""Metadata-only immutable V2 freeze: AST/hash/source bytes/diff/ZIP.

Never import the owner, worker, transport, science, policy or checker modules.
Only this metadata freezer may be invoked by its source author.
"""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import time
import zipfile

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
ORIGINAL=ROOT/'.gcts-active/family-curriculum-independent-source-v3-20261012'
V1_SHA='2cfcfde17096cb74077ae8375df2cc50b51c0791270ca821b9fc89150e4329a1'


def pin(path,declared=None):
    path=Path(path);h=hashlib.sha256();count=0
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):
            h.update(block);count+=len(block)
    if declared is None:
        try:declared=str(path.relative_to(ROOT))
        except ValueError:declared=str(path)
    return dict(path=declared,sha256=h.hexdigest(),bytes=count)


def write_new(name,value):
    with (HERE/name).open('x') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write('\n')


def exact(record):
    return {key:record[key] for key in ('path','sha256','bytes')}


def checked(record,preserved):
    record=exact(record)
    if pin(ROOT/record['path'],record['path'])!=record:
        raise ValueError('immutable literal-path pin mismatch: '+record['path'])
    if preserved.setdefault(record['path'],record)!=record:
        raise ValueError('conflicting immutable pin: '+record['path'])
    return record


def dotted(node):
    if isinstance(node,ast.Name):return node.id
    if isinstance(node,ast.Attribute):return dotted(node.value)+'.'+node.attr
    return ''


def replace_once(text,before,after):
    if text.count(before)!=1:
        raise ValueError('non-unique source delta: '+before[:120])
    return text.replace(before,after,1)


def expected_owner(before):
    """Exact declared successor transform; every other byte must be preserved."""
    changes=[
        ('SOURCE ONLY compact owner implementation;','SOURCE ONLY compact owner V2;'),
        ("    previous={signum:signal.getsignal(signum) for signum in (signal.SIGTERM,signal.SIGALRM)}\n"
         "    try:\n"
         "        for signum in previous:signal.signal(signum,signal.SIG_IGN)\n"
         "        try:os.kill(child.pid,signal.SIGKILL)\n"
         "        except ProcessLookupError:pass\n"
         "        return wait_terminal(child)\n"
         "    finally:\n"
         "        for signum,handler in previous.items():signal.signal(signum,handler)\n",
         "    try:os.kill(child.pid,signal.SIGKILL)\n"
         "    except ProcessLookupError:pass\n"
         "    return wait_terminal(child)\n"),
        ('def observe(plan,index,owner_started):','def observe(plan,index,owner_started,check_cancel):'),
        ("    try:\n        with outpath.open('xb') as out,errpath.open('xb') as err:\n",
         "    try:\n        check_cancel()\n        with outpath.open('xb') as out,errpath.open('xb') as err:\n"),
        ("            after_spawn=time.perf_counter()\n            while True:\n                pid,status,current=os.wait4(child.pid,os.WNOHANG)\n",
         "            after_spawn=time.perf_counter()\n"
         "            # Signal handlers only set flags; handle registration is coherent.\n"
         "            check_cancel()\n            while True:\n                check_cancel()\n"
         "                pid,status,current=os.wait4(child.pid,os.WNOHANG)\n"),
        ("                    waited=True;usage=current;child.returncode=os.waitstatus_to_exitcode(status);break\n",
         "                    waited=True;usage=current;child.returncode=os.waitstatus_to_exitcode(status)\n"
         "                    # Only after terminal bookkeeping may cancellation raise.\n"
         "                    check_cancel();break\n"),
        ("    def cutoff(*_):raise TimeoutError('complete owner175second signal gate')\n"
         "    signal.signal(signal.SIGTERM,cutoff);signal.signal(signal.SIGALRM,cutoff)\n",
         "    cancelled_signum=0\n"
         "    def cancellation_flag(signum,_frame):\n"
         "        nonlocal cancelled_signum\n"
         "        cancelled_signum=signum\n"
         "    def check_cancel():\n"
         "        if cancelled_signum:\n"
         "            raise TimeoutError('owned cancellation flag at safe boundary: '+str(cancelled_signum))\n"
         "    signal.signal(signal.SIGTERM,cancellation_flag);signal.signal(signal.SIGALRM,cancellation_flag)\n"),
        ("    try:\n        with Path(outputs['stdout']).open('xb') as out,Path(outputs['stderr']).open('xb') as err:\n",
         "    try:\n        check_cancel()\n        with Path(outputs['stdout']).open('xb') as out,Path(outputs['stderr']).open('xb') as err:\n"),
        ("                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))\n"
         "            while True:\n                pid,status,current=os.wait4(child.pid,os.WNOHANG)\n",
         "                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))\n"
         "            # No asynchronous raising handler can discard this registered handle.\n"
         "            check_cancel()\n            while True:\n                check_cancel()\n"
         "                pid,status,current=os.wait4(child.pid,os.WNOHANG)\n"),
        ("                    worker_terminal_clock=time.perf_counter();break\n",
         "                    worker_terminal_clock=time.perf_counter()\n"
         "                    check_cancel();break\n"),
        ('observe(plan,observer_count,started);','observe(plan,observer_count,started,check_cancel);'),
        ("        child_seconds=worker_terminal_clock-child_start\n",
         "        check_cancel()\n        child_seconds=worker_terminal_clock-child_start\n"),
        ("        observer_artifact=observers.close();sample_artifact=samples.close()\n"
         "    elapsed=time.perf_counter()-started\n",
         "        observer_artifact=observers.close();sample_artifact=samples.close()\n"
         "    if cancelled_signum:\n"
         "        failure=failure or dict(type='TimeoutError',message='owned non-raising cancellation requested before receipt')\n"
         "    elapsed=time.perf_counter()-started\n"),
        ("        failure=failure,owner_seconds_before_lifetime_receipt_write=elapsed,\n",
         "        failure=failure,cancellation_signum=cancelled_signum,cancellation_requested=bool(cancelled_signum),\n"
         "        cancellation_semantics='Non-raising TERM/ALRM flags; checked only after spawn registration/terminal wait4 bookkeeping and at safe loop boundaries',\n"
         "        owner_seconds_before_lifetime_receipt_write=elapsed,\n"),
        ('0 if compact and not failure else 1)','0 if compact and not failure and not cancelled_signum else 1)')
    ]
    result=before
    for old,new in changes:result=replace_once(result,old,new)
    return result,changes


def function_bytes(text,node):
    return ''.join(text.splitlines(True)[node.lineno-1:node.end_lineno]).encode()


def source_cancel_evidence(text):
    tree=ast.parse(text,feature_version=(3,9))
    top={node.name:node for node in tree.body if isinstance(node,(ast.ClassDef,ast.FunctionDef))}
    run=top['run_owner'];observer=top['observe'];cleanup=top['stop_unreaped']
    flag=next(node for node in run.body if isinstance(node,ast.FunctionDef) and node.name=='cancellation_flag')
    if any(isinstance(node,(ast.Raise,ast.Call,ast.Try,ast.With,ast.While,ast.For)) for node in ast.walk(flag)):
        raise ValueError('handler must assign flag only, never execute a call or raise')
    if (len(flag.body)!=2 or not isinstance(flag.body[0],ast.Nonlocal)
            or flag.body[0].names!=['cancelled_signum']
            or not isinstance(flag.body[1],ast.Assign)
            or ast.dump(flag.body[1],include_attributes=False)!=ast.dump(ast.parse('cancelled_signum=signum').body[0],include_attributes=False)):
        raise ValueError('exact non-raising handler body')
    registrations=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and dotted(node.func)=='signal.signal']
    if len(registrations)!=2:
        raise ValueError('only TERM/ALRM registrations')
    signal_names=[]
    for node in registrations:
        if (len(node.args)!=2 or dotted(node.args[1])!='cancellation_flag'
                or dotted(node.args[0]) not in ('signal.SIGTERM','signal.SIGALRM')):
            raise ValueError('no asynchronously raising registered handler')
        signal_names.append(dotted(node.args[0]))
    if sorted(signal_names)!=['signal.SIGALRM','signal.SIGTERM']:
        raise ValueError('both exact cancellation signals')
    if any(isinstance(node,ast.Attribute) and node.attr=='RUSAGE_CHILDREN' for node in ast.walk(tree)):
        raise ValueError('no cumulative descendant ledger')
    if any(isinstance(node,ast.Call) and dotted(node.func) in ('signal.getsignal','signal.signal') for node in ast.walk(cleanup)):
        raise ValueError('cleanup must not discard flags through ignore/restore')
    expected_scopes=[]
    for name,node in [('run_owner',run),('observe',observer)]:
        pops=[n for n in ast.walk(node) if isinstance(n,ast.Call) and dotted(n.func)=='subprocess.Popen']
        waits=[n for n in ast.walk(node) if isinstance(n,ast.Call) and dotted(n.func)=='os.wait4']
        checks=[n.lineno for n in ast.walk(node) if isinstance(n,ast.Call) and dotted(n.func)=='check_cancel']
        if len(pops)!=1 or len(waits)!=1:
            raise ValueError('exactly one launch and polling wait4 source per ownership scope')
        # Exact full transform above proves the ordering; positions retain its raw evidence.
        if not any(line>pops[0].end_lineno for line in checks) or not any(line>waits[0].end_lineno for line in checks):
            raise ValueError('safe checks must follow spawn and wait source')
        expected_scopes.append(dict(function=name,spawn_line=pops[0].lineno,
            spawn_end_line=pops[0].end_lineno,polling_wait4_line=waits[0].lineno,
            explicit_check_cancel_lines=sorted(checks),source_sha256=hashlib.sha256(function_bytes(text,node)).hexdigest()))
    main=top['main']
    if len(main.body)!=1 or not isinstance(main.body[0],ast.Raise):
        raise ValueError('owner CLI must remain unconditionally SOURCE ONLY')
    return dict(schema='source-only-compact-owner-cancellation-evidence-v2',
        status='AST_AND_EXACT_SOURCE_TRANSFORM_REVIEWED_NO_RUNTIME_FIXTURE',
        owner=pin(HERE/'curriculum_compact_owner_v2.py'),handler_line=flag.lineno,
        handler_sha256=hashlib.sha256(function_bytes(text,flag)).hexdigest(),
        handler_operations=['nonlocal cancelled_signum','cancelled_signum=signum'],
        registrations=[dict(line=node.lineno,signal=dotted(node.args[0]),handler=dotted(node.args[1])) for node in registrations],
        ownership_scopes=expected_scopes,
        cleanup='Direct registered unreaped handle retained through SIGKILL/exact terminal wait4. No signal ignore/restore, historical PID or group cleanup.',
        complete_lifetime_gap='Blocking exact-child wait4 after SIGKILL requires ROOT outer complete bounded lifetime/cleanup and platform verification; no kernel-independent reap bound is claimed.',
        late_signal_gap='External cancellation provenance and complete ROOT gate must reject a signal after final exit-code/frame sampling; pending owner never resource-qualifies.',
        interpreter_scope='Source argument, not runtime/Popen/import-hook/native/Mach-O/ELF safety certification.',
        source_only=True,runtime_fixtures=0,scientific_calls=0,process_calls=0,execution_authorized=False)


def main():
    started=time.monotonic();preserved={}
    v1path=HERE/'source-plan-v1.json';v1=json.loads(v1path.read_text())
    if pin(v1path)['sha256']!=V1_SHA:
        raise ValueError('exact preserved V1 freeze required')
    checked(pin(v1path),preserved)
    for key in ('sources','original_scientific_libraries','preserved'):
        for record in v1[key]:checked(record,preserved)
    for key in ('original_independent_source_manifest','protocol','archive',
                'scientific_function_byte_evidence','worker_leaf_source_evidence','source_review_blocker'):
        checked(v1[key],preserved)
    integration=json.loads((HERE/'integration-v1.json').read_text())
    if integration['manifest']!=pin(v1path):raise ValueError('preserved V1 handoff binds exact manifest')
    checked(pin(HERE/'integration-v1.json'),preserved)
    checked(integration['readiness'],preserved)
    for record in integration['files']:checked(record,preserved)
    checked(integration['archive'],preserved)
    with zipfile.ZipFile(ROOT/integration['archive']['path']) as archive:
        if archive.namelist()!=[Path(record['path']).name for record in integration['files']]:
            raise ValueError('immutable V1 archive inventory')
        for record in integration['files']:
            data=archive.read(Path(record['path']).name)
            if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:
                raise ValueError('immutable V1 archive member bytes')
    if (HERE/'outputs').exists():raise ValueError('author must never create actual outputs')
    before=(HERE/'curriculum_compact_owner_v1.py').read_text()
    after=(HERE/'curriculum_compact_owner_v2.py').read_text()
    expected,changes=expected_owner(before)
    if after!=expected:raise ValueError('undeclared owner byte change')
    oldtree=ast.parse(before,feature_version=(3,9));newtree=ast.parse(after,feature_version=(3,9))
    original_nodes={n.name:n for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    successor_nodes={n.name:n for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    if original_nodes.keys()!=successor_nodes.keys():raise ValueError('no unrelated owner construct changes')
    unchanged_owner=[]
    for name in original_nodes:
        if name not in ('stop_unreaped','observe','run_owner'):
            old=function_bytes(before,original_nodes[name]);new=function_bytes(after,successor_nodes[name])
            if old!=new:raise ValueError('unrelated owner function/class bytes changed: '+name)
            unchanged_owner.append(dict(name=name,bytes=len(old),sha256=hashlib.sha256(old).hexdigest(),byte_identical=True))
    write_new('cancellation-source-evidence-v2.json',source_cancel_evidence(after))
    oldworker=(ORIGINAL/'curriculum_independent_worker_v1.py').read_bytes()
    worker=(HERE/'curriculum_compact_worker_v1.py').read_bytes()
    marker=b'def main():';prefix=oldworker[:oldworker.index(marker)]
    if worker[:worker.index(marker)]!=prefix:
        raise ValueError('exact original scientific/guard prefix')
    oldworkertext=oldworker.decode();workertext=worker.decode()
    oldworkerAST=ast.parse(oldworkertext,feature_version=(3,9));workerAST=ast.parse(workertext,feature_version=(3,9))
    functions=[]
    for node in oldworkerAST.body:
        if isinstance(node,ast.FunctionDef) and node.name!='main':
            peer=next(n for n in workerAST.body if isinstance(n,ast.FunctionDef) and n.name==node.name)
            a=function_bytes(oldworkertext,node);b=function_bytes(workertext,peer)
            if a!=b:raise ValueError('scientific bytes changed')
            functions.append(dict(name=node.name,bytes=len(a),sha256=hashlib.sha256(a).hexdigest(),byte_identical=True))
    if len(functions)!=8 or len(v1['original_scientific_libraries'])!=7:
        raise ValueError('unchanged complete eight-function/seven-library scope')
    leaf=json.loads((HERE/'worker-leaf-source-evidence-v1.json').read_text())
    for module in leaf['modules']:checked(module['pin'],preserved)
    write_new('unchanged-science-evidence-v2.json',dict(
        status='EXACT_V1_WORKER_TRANSPORT_AND_ORIGINAL_SCIENTIFIC_BYTES_PRESERVED',
        predecessor=pin(v1path),original_worker=pin(ORIGINAL/'curriculum_independent_worker_v1.py'),
        reused_worker=pin(HERE/'curriculum_compact_worker_v1.py'),reused_transport=pin(HERE/'compact_static_transport_v1.py'),
        prefix_bytes=len(prefix),prefix_sha256=hashlib.sha256(prefix).hexdigest(),
        original_scientific_functions=functions,original_libraries=v1['original_scientific_libraries'],
        inherited_leaf_source_evidence=v1['worker_leaf_source_evidence'],
        unchanged_owner_constructs=unchanged_owner,declared_exact_owner_transform_count=len(changes),
        exact_limits=v1['exact_limits'],no_budget_or_feature_grammar_reward_seed_change=True,
        source_only=True,scientific_calls=0,project_function_imports=0,process_calls=0))
    for oldpath,newpath,name in [
        (HERE/'curriculum_compact_owner_v1.py',HERE/'curriculum_compact_owner_v2.py','owner-v1-to-v2.diff'),
        (ORIGINAL/'curriculum_independent_owner_v1.py',HERE/'curriculum_compact_owner_v2.py','owner-original-v3-to-v2.diff')]:
        diff=''.join(difflib.unified_diff(oldpath.read_text().splitlines(True),newpath.read_text().splitlines(True),
            fromfile=str(oldpath.relative_to(ROOT)),tofile=str(newpath.relative_to(ROOT))))
        with (HERE/name).open('x') as stream:stream.write(diff)
    source_names=['curriculum_compact_owner_v2.py','freeze_compact_wrapper_source_v2.py']
    ASTs=[];sources=[]
    for name in source_names:
        path=HERE/name;ast.parse(path.read_text(),filename=str(path),feature_version=(3,9))
        sources.append(pin(path));ASTs.append(dict(path=str(path.relative_to(ROOT)),status='Python3.9_AST_only'))
    protocol=json.loads((HERE/'protocol-v2.json').read_text())
    if protocol['predecessor']!=pin(v1path) or protocol['execution_authorized'] is not False:
        raise ValueError('V2 source-only protocol exact predecessor')
    members=source_names+['protocol-v2.json','cancellation-source-evidence-v2.json',
        'unchanged-science-evidence-v2.json','owner-v1-to-v2.diff','owner-original-v3-to-v2.diff']
    archive=HERE/'source-v2.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_STORED) as zipped:
        for name in members:
            item=zipfile.ZipInfo(name,date_time=(2026,10,12,0,0,0));item.external_attr=0o100644<<16
            zipped.writestr(item,(HERE/name).read_bytes())
    with zipfile.ZipFile(archive) as zipped:
        if zipped.namelist()!=members:raise ValueError('V2 source archive exact inventory')
        for name in members:
            if zipped.read(name)!=(HERE/name).read_bytes():raise ValueError('V2 archive exact bytes')
    write_new('source-plan-v2.json',dict(schema='source-only-compact-static-wrapper-manifest-v2',
        status='SOURCE_ONLY_V2_FLAG_CANCELLATION_PLATFORM_ADAPTER_AND_CLI_UNBOUND',
        predecessor=pin(v1path),sources=sources,reused_scientific_worker=pin(HERE/'curriculum_compact_worker_v1.py'),
        reused_transport=pin(HERE/'compact_static_transport_v1.py'),original_scientific_libraries=v1['original_scientific_libraries'],
        preserved=list(preserved.values()),protocol=pin(HERE/'protocol-v2.json'),archive=pin(archive),
        cancellation_source_evidence=pin(HERE/'cancellation-source-evidence-v2.json'),
        unchanged_science_evidence=pin(HERE/'unchanged-science-evidence-v2.json'),
        exact_limits=v1['exact_limits'],owner_CLI_dispatch_blocked=True,final_platform_rule_frozen=False,
        complete_outer_lifetime_and_reap_binding_pending=True,actual_plan_exists=False,
        actual_activation_exists=False,actual_scientific_calls=0,execution_authorized=False,
        historical_donor_UNKNOWN_immutable=True,all_five_qualification=False))
    write_new('readiness-v2.json',dict(status='SOURCE_ONLY_V2_FROZEN_NO_FUNCTIONAL_EXECUTION',
        manifest=pin(HERE/'source-plan-v2.json'),ASTs=ASTs,
        predecessor_fully_preserved=True,exact_original_scientific_functions=8,exact_original_semantic_libraries=7,
        inherited_leaf_modules=len(leaf['modules']),preserved_unique=len(preserved),
        metadata_freeze_seconds_before_final_receipts=time.monotonic()-started,
        cancellation_AST_and_exact_source_transform_checked=True,runtime_cancellation_fixture_executed=False,
        postlude_bytes=52,scientific_calls=0,process_PS_browser_calibration_calls=0,
        qualification_issued=False,execution_authorized=False))
    write_new('integration-v2.json',dict(status='SOURCE_ONLY_COMPACT_WRAPPER_V2_AWAITING_ROOT_OUTER_PLATFORM_BINDING',
        manifest=pin(HERE/'source-plan-v2.json'),readiness=pin(HERE/'readiness-v2.json'),
        files=[pin(HERE/name) for name in members],archive=pin(archive),predecessor_handoff=pin(HERE/'integration-v1.json'),
        actual_interfaces=[
            'Reuse exact compact V1 worker/transport and all original V3 semantic libraries; actual owner_pin must name V2 and source manifest pin must name source-plan-v2.',
            'Owner CLI remains an unconditional SOURCE ONLY error. ROOT must review source, pinned platform/Popen semantics, complete lifetime and direct reap ownership, metadata-only adapter and outer binding before any future actual plan/activation.',
            'TERM/ALRM flags are inspected only after handle assignment or terminal wait4 bookkeeping; every observer remains individually recorded and reaped. No executed race fixture is claimed.',
            'Owner resource flags always remain false; outer ROOT must reject late cancellation even if pending compact semantic candidate bytes were already closed.',
            'Complete blocking direct wait4 cleanup requires ROOT outer bounded ownership; current package does not certify kernel-independent bounded reaping.',
            'All SELF/leaf terminal usage remains raw. No nested rolled-peak subtraction/addition, final platform rule, historical resource discount or all-five qualification.'
        ],original_donor_resource_UNKNOWN_preserved=True,
        scientific_calls=0,project_function_imports=0,process_calls=0,
        no_actual_qualification=True,execution_authorized=False))
    print(json.dumps(dict(status='SOURCE_ONLY_V2_FROZEN',manifest=pin(HERE/'source-plan-v2.json'),
        owner=pin(HERE/'curriculum_compact_owner_v2.py'),integration=pin(HERE/'integration-v2.json'),
        sources=len(sources),preserved=len(preserved),scientific_calls=0,process_calls=0),indent=2))


if __name__=='__main__':main()
