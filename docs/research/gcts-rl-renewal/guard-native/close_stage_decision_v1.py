"""ROOT saved-metadata disposition; never a proof or native checker."""
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def read(path): return json.loads(Path(path).read_bytes())

def pin(path):
    p=Path(path); p=p if p.is_absolute() else ROOT/p
    h=hashlib.sha256(); size=0
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''): h.update(block); size+=len(block)
    try: name=str(p.relative_to(ROOT))
    except ValueError: name=str(p)
    return dict(path=name,sha256=h.hexdigest(),bytes=size)

def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ('preparation','native','replay'):
        raise ValueError('one literal completed phase')
    stage=sys.argv[1]; plan_path=HERE/(stage+'-plan-v1.json'); plan=read(plan_path)
    caller_path=HERE/(stage+'-actual-tool-observations-v1.json'); caller=read(caller_path)
    owner_path=HERE/(stage+'-owner-v1/ROOT-terminal-v1.json')
    provisional=HERE/(stage+'-owner-v1/provisional-terminal-v1.json')
    post_path=HERE/(stage+'-owner-v1/post-write-observation-v1.json')
    owner=read(owner_path if owner_path.exists() else provisional)
    post=read(post_path)
    worker_path=ROOT/plan['worker_receipt']; worker=read(worker_path) if worker_path.exists() else None
    mismatches=[a['path'] for a in plan['closure'] if pin(a['path'])!=a]
    terminal=caller['terminal']; output=terminal['output'].strip().splitlines()
    owner_print=json.loads(output[-1]) if output else None
    caller_seconds=(caller['terminal_observed_ms']-caller['started_ms'])/1000
    predicates=dict(actual_tool_terminal=terminal.get('exit_code')==0,
        caller_clock_bound=0<=caller_seconds+1<=plan['limits']['caller_seconds'],
        owner_terminal_link_present=owner_path.exists(),owner_gate=owner['resource_gate_accepted'] is True,
        post_write_gate=post['resource_gate_accepted'] is True,
        cancelled_at_final_print_false=owner_print is not None and owner_print.get('cancelled_at_final_print') is False,
        final_print_gate=owner_print is not None and owner_print.get('resource_gate_accepted') is True,
        stage_identity=owner['stage']==stage and worker is not None and worker['stage']==stage,
        worker_complete=worker is not None and worker['stage_completed'] is True,
        all_worker_direct_children_closed=worker is not None and worker['all_direct_children_terminal_and_reaped'] is True,
        all_owner_direct_children_closed=owner['all_direct_children_terminal_and_reaped'] is True,
        no_owned_leftovers=owner['owned_leftovers']==[],complete_post_closure_unchanged=not mismatches)
    if owner_path.exists():
        predicates['post_write_exact_terminal']=post['terminal']==pin(owner_path)
    else: predicates['post_write_exact_terminal']=False
    accepted=all(predicates.values())
    native=worker.get('native_result') if worker else None
    result=dict(schema='ROOT-guard-native-stage-final-decision-v1',stage=stage,
        status='accepted_complete_owned_stage' if accepted else 'UNKNOWN_complete_stage_qualification',
        ROOT_final_accepted=accepted,predicates=predicates,mismatches=mismatches,
        limits=plan['limits'],caller_elapsed_seconds=caller_seconds,caller_finish_reserve_seconds=1,
        caller_clock_scope='Elapsed Date.now tool request to observed terminal in one awaited isolate; no clock origins combined.',
        plan=pin(plan_path),actual_tool=pin(caller_path),owner=pin(owner_path) if owner_path.exists() else pin(provisional),
        post_write=pin(post_path),worker=pin(worker_path) if worker else None,
        native_queries=worker.get('native_queries',0) if worker else 0,
        native_replays=worker.get('native_replays',0) if worker else 0,
        target_searches=0,new_RL_training=False,native_status=native['status'] if native else None,
        native_accepted=accepted and native is not None and native['status']=='accepted',
        all_five_qualification=False,universal_compiler_theorem=False,finite_Wang_rectangle_accepted=False,
        scope='Owned stage qualification is separate from acceptance of a proof. Native UNKNOWN is retained even when a complete bounded computation and resource gate qualify. Toolchain and pinned owner/whole-host filter remain trusted; no hard OS or universal compiler proof claimed.')
    path=HERE/(stage+'-ROOT-final-decision-v1.json')
    with path.open('x') as stream: json.dump(result,stream,indent=2); stream.write('\n')
    print(json.dumps({k:result[k] for k in ('stage','status','ROOT_final_accepted','caller_elapsed_seconds','native_status','native_accepted','predicates')}),flush=True)

if __name__=='__main__': main()
