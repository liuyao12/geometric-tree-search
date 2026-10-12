"""Metadata-only AST/hash/function-byte/leaf-source/diff/ZIP freeze."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import struct
import time
import zipfile

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OLD=ROOT/'.gcts-active/family-curriculum-independent-source-v3-20261012'


def pin(path,declared=None):
    path=Path(path);h=hashlib.sha256();count=0
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):h.update(block);count+=len(block)
    if declared is None:
        try:declared=str(path.relative_to(ROOT))
        except ValueError:declared=str(path)
    return dict(path=declared,sha256=h.hexdigest(),bytes=count)


def write_new(name,value):
    path=HERE/name
    if path.exists():
        if json.loads(path.read_text())!=value:raise ValueError('preserved partial metadata differs')
        return
    with path.open('x') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')


def dotted(node):
    if isinstance(node,ast.Name):return node.id
    if isinstance(node,ast.Attribute):return dotted(node.value)+'.'+node.attr
    return ''


def main():
    started=time.monotonic();oldplan=OLD/'source-plan-v1.json';plan=json.loads(oldplan.read_text())
    if pin(oldplan)['sha256']!='34d94837ad995b7508f851968b8e861dc58d3bcf4495317adc68e61a3f9334b9':
        raise ValueError('exact original independent V3 source manifest')
    preserved={}
    for key in ('sources','libraries','inputs','preserved','preserved_files'):
        for record in plan.get(key,[]):
            exact={k:record[k] for k in ('path','sha256','bytes')}
            if pin(record['path'],record['path'])!=exact:raise ValueError('original immutable source pin changed')
            if preserved.setdefault(record['path'],exact)!=exact:raise ValueError('conflicting original source pin')
    preserved[str(oldplan.relative_to(ROOT))]=pin(oldplan)
    reviewpath=ROOT/'.gcts-active/curriculum-static-resource-independent-metadata-review-20261012/review-v1.json'
    review=json.loads(reviewpath.read_text())
    if pin(reviewpath)['sha256']!='43c9dabb621526ebe0f5836c69ed077ff2da6c6aaad21482d3438f93f9c94836':
        raise ValueError('exact preserved donor UNKNOWN review')
    for record in review['exact_input_pins']:
        if pin(ROOT/record['path'],record['path'])!=record:raise ValueError('preserved failed donor input changed')
        preserved[record['path']]=record
    preserved[str(reviewpath.relative_to(ROOT))]=pin(reviewpath)
    for name in ('design-v1.json','design-v1.html','input-pins-v1.json','handoff-v1.json'):
        path=ROOT/'.gcts-active/curriculum-future-resource-design-source-20261012'/name
        preserved[str(path.relative_to(ROOT))]=pin(path)
    old_worker=(OLD/'curriculum_independent_worker_v1.py').read_bytes()
    new_worker=(HERE/'curriculum_compact_worker_v1.py').read_bytes()
    marker=b'def main():';prefix=old_worker[:old_worker.index(marker)]
    if new_worker[:new_worker.index(marker)]!=prefix:
        raise ValueError('scientific audit/guard prefix must remain exact byte-identical')
    oldtree=ast.parse(old_worker.decode(),feature_version=(3,9))
    newtree=ast.parse(new_worker.decode(),feature_version=(3,9))
    oldlines=old_worker.decode().splitlines(keepends=True);newlines=new_worker.decode().splitlines(keepends=True)
    function_evidence=[]
    for node in oldtree.body:
        if isinstance(node,ast.FunctionDef) and node.name!='main':
            peer=next(n for n in newtree.body if isinstance(n,ast.FunctionDef) and n.name==node.name)
            before=''.join(oldlines[node.lineno-1:node.end_lineno]).encode()
            after=''.join(newlines[peer.lineno-1:peer.end_lineno]).encode()
            if before!=after:raise ValueError('scientific/guard function bytes changed: '+node.name)
            function_evidence.append(dict(name=node.name,bytes=len(before),sha256=hashlib.sha256(before).hexdigest(),byte_identical=True))
    if len(function_evidence)!=8:raise ValueError('all eight original functions must be preserved')
    write_new('scientific-function-byte-evidence-v1.json',dict(status='EXACT_SOURCE_BYTES_PRESERVED_NO_FUNCTION_EXECUTED',
        original=pin(OLD/'curriculum_independent_worker_v1.py'),successor=pin(HERE/'curriculum_compact_worker_v1.py'),
        complete_pre_main_prefix_bytes=len(prefix),complete_pre_main_prefix_sha256=hashlib.sha256(prefix).hexdigest(),
        functions=function_evidence,all_seven_original_semantic_libraries_preserved=True,scientific_calls=0))
    for oldname,newname,diffname in [('curriculum_independent_worker_v1.py','curriculum_compact_worker_v1.py','worker-v3-to-compact-v1.diff'),
                                    ('curriculum_independent_owner_v1.py','curriculum_compact_owner_v1.py','owner-v3-to-compact-v1.diff')]:
        text=''.join(difflib.unified_diff((OLD/oldname).read_text().splitlines(True),(HERE/newname).read_text().splitlines(True),
            fromfile=str((OLD/oldname).relative_to(ROOT)),tofile=str((HERE/newname).relative_to(ROOT))))
        path=HERE/diffname
        if path.exists():
            if path.read_text()!=text:raise ValueError('preserved source diff differs')
        else:
            with path.open('x') as stream:stream.write(text)
    libraries=plan['libraries']
    closure=[HERE/'curriculum_compact_worker_v1.py',HERE/'compact_static_transport_v1.py']+[Path(r['path']) for r in libraries]
    forbidden_modules={'subprocess','multiprocessing','pty','ctypes','socket','concurrent.futures','_posixsubprocess'}
    forbidden_calls={'os.system','os.fork','os.forkpty','os.posix_spawn','os.posix_spawnp',
        'os.spawnl','os.spawnle','os.spawnlp','os.spawnlpe','os.spawnv','os.spawnve','os.spawnvp','os.spawnvpe',
        'os.execv','os.execve','os.execl','os.execle','os.execvp','os.execvpe','os.execlp','os.execlpe','eval','exec','__import__'}
    leaves=[];latent_calls=[]
    known_project_modules={path.stem for path in closure}
    allowed_standard={'__future__','argparse','collections','copy','gc','gzip','hashlib','importlib',
        'itertools','json','math','os','pathlib','platform','resource','signal','struct','sys','time'}
    for path in closure:
        text=path.read_text();tree=ast.parse(text,filename=str(path),feature_version=(3,9));imports=[];banned=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports.extend(n.name for n in node.names)
            if isinstance(node,ast.ImportFrom):imports.append(node.module or '')
            if isinstance(node,ast.Call) and dotted(node.func) in forbidden_calls:
                banned.append(dict(line=node.lineno,call=dotted(node.func)))
        badimports=[name for name in imports if any(name==bad or name.startswith(bad+'.') for bad in forbidden_modules)]
        unknown_imports=[name for name in imports if name.split('.')[0] not in allowed_standard|known_project_modules]
        if unknown_imports:raise ValueError('unbound import outside known closed worker source set: '+str(unknown_imports))
        if banned or badimports:raise ValueError('leaf source proof found child/native execution primitive')
        for fn in tree.body:
            if 'platform' in imports and isinstance(fn,ast.FunctionDef):
                for node in ast.walk(fn):
                    if isinstance(node,ast.Call) and dotted(node.func).startswith('platform.'):
                        latent_calls.append(dict(path=str(path.relative_to(ROOT)),function=fn.name,line=node.lineno,call=dotted(node.func),scope='Dormant library CLI main, never reached by static worker'))
                        if fn.name!='main':raise ValueError('platform call in reachable static source')
        leaves.append(dict(pin=pin(path),imports=sorted(set(imports)),forbidden_process_or_native_imports=0,forbidden_launch_calls=0))
    write_new('worker-leaf-source-evidence-v1.json',dict(status='CLOSED_PINNED_PROJECT_SOURCE_CHILD_LAUNCH_ABSENCE',
        modules=leaves,library_roles=[r['role'] for r in libraries],latent_dormant_library_calls=latent_calls,
        reasoning='Worker dynamic load targets are all seven literal exact frozen libraries; their project imports resolve inside this inspected set. No inspected project module has process-spawn/native/eval/exec primitive. Existing library CLI main guards are not invoked by worker static_run. Transport performs metadata I/O/raw resource/frame/os._exit only.',
        limitations='Known pinned project source argument, not a hostile interpreter/import-hook/native security proof. Standard-library and pinned host/observer semantics still require ROOT verification/calibration; unexpected runtime descendants stay UNKNOWN.',
        source_only=True,functions_imported_or_invoked=0,scientific_calls=0))
    source_names=['compact_static_transport_v1.py','curriculum_compact_worker_v1.py','curriculum_compact_owner_v1.py','freeze_compact_wrapper_source_v1.py','freeze_compact_wrapper_source_v1b.py']
    sources=[];ASTs=[]
    for name in source_names:
        path=HERE/name;ast.parse(path.read_text(),filename=str(path),feature_version=(3,9))
        sources.append(pin(path));ASTs.append(dict(path=str(path.relative_to(ROOT)),status='Python3.9_AST_only'))
    owner_tree=ast.parse((HERE/'curriculum_compact_owner_v1.py').read_text(),feature_version=(3,9))
    if any(isinstance(n,ast.Attribute) and n.attr=='RUSAGE_CHILDREN' for n in ast.walk(owner_tree)):
        raise ValueError('no cumulative child observer estimate allowed')
    if struct.calcsize('!8sBBHQQddd')!=52:raise ValueError('fixed52byte postlude source encoding')
    members=source_names+['protocol-v1.json','source-review-blocker-v1.json','metadata-freeze-failure-v1.json','scientific-function-byte-evidence-v1.json','worker-leaf-source-evidence-v1.json',
        'worker-v3-to-compact-v1.diff','owner-v3-to-compact-v1.diff']
    archive=HERE/'source-v1.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_STORED) as z:
        for name in members:
            item=zipfile.ZipInfo(name,date_time=(2026,10,12,0,0,0));item.external_attr=0o100644<<16
            z.writestr(item,(HERE/name).read_bytes())
    with zipfile.ZipFile(archive) as z:
        if z.namelist()!=members:raise ValueError('source archive inventory')
        for name in members:
            if z.read(name)!=(HERE/name).read_bytes():raise ValueError('source archive exact bytes')
    write_new('source-plan-v1.json',dict(schema='source-only-compact-static-wrapper-manifest-v1',
        status='SOURCE_ONLY_V1_BLOCKED_BY_ASYNC_CANCELLATION_AND_UNBOUND_PLATFORM_ADAPTER',sources=sources,
        original_scientific_libraries=libraries,preserved=list(preserved.values()),
        original_independent_source_manifest=pin(oldplan),protocol=pin(HERE/'protocol-v1.json'),archive=pin(archive),
        scientific_function_byte_evidence=pin(HERE/'scientific-function-byte-evidence-v1.json'),
        worker_leaf_source_evidence=pin(HERE/'worker-leaf-source-evidence-v1.json'),
        exact_limits=dict(whole_seconds=180,supervisor_seconds=175,child_seconds=170,peak_bytes=536870912),
        source_review_blocker=pin(HERE/'source-review-blocker-v1.json'),owner_CLI_dispatch_blocked=True,final_platform_rule_frozen=False,actual_plan_exists=False,
        actual_activation_exists=False,actual_scientific_calls=0,execution_authorized=False,
        historical_donor_UNKNOWN_immutable=True,all_five_qualification=False))
    write_new('readiness-v1.json',dict(status='SOURCE_ONLY_V1_PRESERVED_BLOCKED_NO_FUNCTIONAL_EXECUTION',
        manifest=pin(HERE/'source-plan-v1.json'),ASTs=ASTs,scientific_functions_byte_identical=8,
        exact_original_libraries=7,leaf_source_modules=len(leaves),preserved_unique=len(preserved),
        metadata_freeze_seconds_before_final_receipts=time.monotonic()-started,
        postlude_bytes=52,scientific_calls=0,process_PS_browser_calibration_calls=0,
        qualification_issued=False,execution_authorized=False))
    write_new('integration-v1.json',dict(status='SOURCE_ONLY_COMPACT_WRAPPER_V1_PRESERVED_BLOCKED',
        manifest=pin(HERE/'source-plan-v1.json'),readiness=pin(HERE/'readiness-v1.json'),
        files=[pin(HERE/name) for name in members],archive=pin(archive),
        interfaces=['Worker main requires a real exact bound compact actual plan, separate ROOT activation, verified platform receipt and adapter pin; none are instantiated.',
                    'Owner CLI always refuses dispatch. run_owner(planpath,accounting) requires separately ROOT-frozen platform adapter and ends with post-close raw SELF frame/os._exit.',
                    'ROOT must separately review/bind outer launcher/dispatcher SELF frames/complete clocks/postlude reserve and raw distinct-domain accounting.'],
        original_donor_resource_UNKNOWN_preserved=True,scientific_calls=0,process_calls=0,
        no_actual_qualification=True,execution_authorized=False))
    print(json.dumps(dict(status='SOURCE_ONLY_READY',manifest=pin(HERE/'source-plan-v1.json'),
        scientific_functions_byte_identical=8,original_libraries=7,leaf_modules=len(leaves),
        sources=len(sources),preserved=len(preserved)),indent=2))


if __name__=='__main__':main()
