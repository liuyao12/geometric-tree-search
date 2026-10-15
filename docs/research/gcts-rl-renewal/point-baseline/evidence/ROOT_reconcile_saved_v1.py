"""Saved evidence only: no Source execution, Q decode, or mathematical replay."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-compact-point-ROOT-20261015')

def need(test,message):
    if not test:raise ValueError(message)

def unique(pairs):
    out={}
    for k,v in pairs:
        need(k not in out,'duplicate saved key');out[k]=v
    return out

def decode(raw):
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

def pin(path):
    path=Path(path);h=hashlib.sha256();size=0
    with path.open('rb') as f:
        while True:
            block=f.read(65536)
            if not block:break
            h.update(block);size+=len(block)
    return {'path':str(path),'sha256':h.hexdigest(),'bytes':size}

def bare(record):return {k:record[k] for k in ('sha256','bytes')}

def lines(path,schema):
    raw=Path(path).read_bytes()
    need(raw.endswith(b'\n') and raw.count(b'\n')==2,'complete two-line response/EOF')
    a,b,_=raw.split(b'\n');body,trailer=decode(a),decode(b)
    need(canonical(body)==a and canonical(trailer)==b,'canonical response')
    need(trailer['schema']==schema and trailer['body_bytes']==len(a)+1 and
         trailer['body_sha256']==hashlib.sha256(a+b'\n').hexdigest() and
         trailer['exit_zero_and_coordinator_deadline_required'] is True,'complete hash-linked response')
    return body

def main(argv):
    need(len(argv)==1 and argv[0] in ('controls','primary'),'sole saved purpose')
    purpose=argv[0];planpath=ROOT/('ROOT-'+purpose+'-plan-v1.json')
    plan=decode(planpath.read_bytes());closure=decode((ROOT/('ROOT-'+purpose+'-closure-v1.json')).read_bytes())
    need(pin(planpath)==closure['plan'],'whole frozen plan')
    for group in ('sources','inputs','original_sources','source_reviews'):
        for record in plan[group].values():need(pin(record['path'])==record,'unchanged '+group+' pin')
    for record in (plan['runtime'],plan['protocol_choice'],plan['authorization'],closure['external_driver'],closure['native_meter']):
        need(pin(record['path'])==record,'whole runtime/protocol/grant/instrument')
    run=Path(plan['output_directory']);ext=Path(closure['external_directory'])
    finalpath=run/'point-provisional.json';final=decode(finalpath.read_bytes())
    native=decode((ext/'native-terminal.json').read_bytes());observation=decode((ext/'observation.json').read_bytes())
    wall=decode((ext/'tool-bracket.json').read_bytes());once=decode((ext/'ONCE.json').read_bytes())
    need(final['schema']=='Q-point-compact-cold-intake-provisional-v1' and final['plan']==bare(pin(planpath)) and
         final['purpose']==purpose and final['invocation_id']==plan['invocation_id'] and final['limits']==plan['limits'],
         'whole actual context')
    need(native['all_reaped'] is True and native['wait4_pid']==native['caller_pid'] and native['error'] is None and
         native['interrupted'] is False and native['cancellation_forwarded'] is False,'true parent terminal/reap without meter interruption')
    need(native['wait4_usage'][2]==native['caller_kernel_peak_bytes'] and native['caller_returncode'] in (0,2) and
         native['wait4_status']==native['caller_returncode']*256,'Darwin terminal native bytes/status')
    need(observation['meter_returncode']==native['caller_returncode'] and observation['probe_returncode']==0 and
         observation['plan_sha256']==pin(planpath)['sha256'] and observation['plan_bytes']==pin(planpath)['bytes'] and
         observation['invocation_id']==plan['invocation_id'] and observation['purpose']==purpose,'whole external observation')
    need(once['plan_sha256']==observation['plan_sha256'] and once['invocation_id']==plan['invocation_id'] and
         once['purpose']==purpose,'exclusive once-only actual')
    need(int((ext/'postterminal-probe-stdout.txt').read_bytes())==observation['postterminal_native_probe_ns'] and
         (ext/'postterminal-probe-stderr.txt').read_bytes()==b'','genuine new-process native probe')
    launch=native['caller_launch_began_ns'];terminal=native['caller_terminal_observed_ns']
    post=observation['postterminal_native_probe_ns'];began=final['joint_began_ns']
    need(launch<=began<=terminal<=post and final['joint_deadline_ns']==began+20000000000,'ordered native epochs/unchanged20')
    need(wall['elapsed_ms']==wall['end_ms']-wall['start_ms'] and type(wall['elapsed_ms']) is int and
         0<=wall['elapsed_ms']<=60000 and wall['elapsed_ms']+1000<=90000 and wall['observed_terminal'] is True and
         wall['exit_code']==native['caller_returncode'],'complete tool wall60/caller90+1')
    children=final['children'];cut=final['cutoff'];previous=began
    need(cut['all_reaped'] is True and cut['no_future_spawn'] is True and cut['child_count']==len(children),
         'irreversible all-reaped no-spawn cutoff')
    for child in children:
        need(child['reaped'] is True and child['wait4_pid']==child['pid'] and
             previous<=child['launch_began_ns']<child['terminal_observed_ns']<=cut['observed_ns'],
             'exact PID true reap and serial closed lifetime')
        need(child['kernel_peak_bytes']==child['usage'][2] and type(child['kernel_peak_bytes']) is int,'leaf native peak bytes')
        rc=child['returncode'];status=child['wait4_status']
        need((rc>=0 and status==rc*256) or (rc<0 and status & 127 == -rc),'native child exit/signal status')
        previous=child['terminal_observed_ns']
    need(len({c['pid'] for c in children})==len(children) and cut['observed_ns']<=terminal,'distinct PIDs/cut before terminal')
    childpeak=max((c['kernel_peak_bytes'] for c in children),default=0)
    selfcut=cut['SELF_peak_bytes'];terminalpeak=native['caller_kernel_peak_bytes'];live=selfcut+childpeak;bound=max(live,terminalpeak)
    need(childpeak==final['maximum_leaf_peak_bytes'] and live==final['live_epoch_bound_bytes'] and
         terminalpeak>=max(selfcut,childpeak),'whole sequential epochs and inclusive terminal tail')
    need(final['cleanup_errors']==[] and final['output_inventory']['complete'] is True,'actual cleanup and complete output')
    total=0;paths=set()
    for record in final['output_inventory']['files']:
        path=run/record['path']
        need(path.resolve().is_relative_to(run.resolve()) and not path.is_symlink() and record['path'] not in paths,'owned unique regular path')
        actual=pin(path);need(bare(actual)==bare(record),'saved output pin '+record['path'])
        total+=actual['bytes'];paths.add(record['path'])
    need(total==final['output_inventory']['bytes'],'complete output bytes')
    actualpaths={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file()}
    need(actualpaths==paths|{'point-provisional.json'},'complete saved output inventory')
    receipt=decode((ext/'meter-stdout.txt').read_bytes())
    need(receipt['schema']=='Q-point-compact-cold-final-observation-v1' and receipt['provisional']==bare(pin(finalpath)) and
         receipt['purpose']==purpose,'whole final receipt')
    for flag in ('ROOT_primary_accepted','ROOT_resource_accepted','selected_provenance_accepted','point_state_accepted',
                 'full24_accepted','trajectory_accepted','RL_accepted','native_accepted','Q_BASE_output_injected'):
        need(final[flag] is False,'no lower-layer promotion '+flag)
    timeok=post-launch<=20000000000 and terminal<final['joint_deadline_ns']
    memoryok=bound<=536870912
    primary=False;controlsok=False
    if purpose=='controls':
        need(native['caller_returncode']==0 and final['error'] is None and timeok and memoryok and
             final['status']=='CONTROLS_PENDING_EXTERNAL_TERMINAL' and final['controls_pending_caller'] is True and
             receipt['pending_external'] is True and final['word_logically_accepted'] is False,'actual controls pending and all resource gates')
        need([c['role'] for c in children]==['inert-a','inert-b','bad-word','bad-authority'] and
             [c['returncode'] for c in children]==[0,0,0,2],'exact four control lifecycles')
        controls={c['id']:c for c in final['controls']}
        need(set(controls)=={'real-sequential-leaves','corrupt-word','corrupt-authority','postseal-launch-denial','parent-exit-tail'},'all five controls')
        real=controls['real-sequential-leaves'];need(real['true_wait4_reaped'] and real['disjoint_closed_lifetimes'],'actual serial leaves')
        bad=lines(run/'bad-word-response.jsonl','Q-clean-verifier-response-completion-v1')
        need(bad==controls['corrupt-word']['actual_response'] and bad['status']=='WORD_REJECTED' and
             bad['independent_word_certificate'] is None and bad['rejection']['message']=='exact named original axiom','real mathematical rejection')
        need((run/'bad-authority-response.jsonl').read_bytes()==b'' and (run/'bad-authority-stderr.txt').read_bytes()==
             b'ValueError: unchanged original raw inputs/model/authority/registry\n' and
             controls['corrupt-authority']['actual_response']['status']=='AUTHORITY_REJECTED_BEFORE_RESPONSE','exact native corrupt-authority rejection')
        denial=controls['postseal-launch-denial'];tail=controls['parent-exit-tail']
        need(denial['specific_rejection']=='NO_SPAWN_AFTER_CUTOFF' and denial['Popen_reached'] is False and
             denial['otherwise_valid_fixed_leaf_arguments'] is True and denial['children_before']==denial['children_after']==4,'actual postseal launch denial')
        need(tail['resident_requested_bytes']==33554432 and tail['touched_pages']==8192 and tail['SELF_cut']==selfcut and
             terminalpeak>=tail['SELF_after_tail']>selfcut,'true terminal T covers resident parent exit tail')
        controlsok=True
    elif final['status']=='WORD_VERIFIED_PENDING_CALLER':
        need(timeok and memoryok and native['caller_returncode']==0 and final['error'] is None and
             final['primary_pending_caller'] is True and final['word_logically_accepted'] is True and receipt['pending_external'] is True and
             [c['role'] for c in children]==['producer','verifier'] and all(c['returncode']==0 for c in children),'searched/checked successful lifecycle')
        producer=lines(run/'producer-response.jsonl','Q-point-compact-producer-response-completion-v1')
        checked=lines(run/'verifier-response.jsonl','Q-clean-verifier-response-completion-v1')
        candidate=producer['result']['candidate'];cert=checked['independent_word_certificate'];commands=candidate['commands']
        declaration=decode(Path(plan['inputs']['declaration']['path']).read_bytes())
        need(producer['result']==final['producer_result'] and cert==final['certificate'] and cert['completed'] is True and
             checked['status']=='WORD_VERIFIED_PENDING_COORDINATOR' and cert['original_Gamma_target_sequent_accepted'] is True and
             cert['original_ordered_Gamma']==declaration['ordered_Gamma']==[] and cert['target']==declaration['target'] and
             cert['essential_rows']==list(range(len(commands))) and 1<=len(commands)<=24 and
             cert['commands_sha256']==hashlib.sha256(canonical(commands)).hexdigest(),'exact original independently accepted whole word')
        for i,(command,row) in enumerate(zip(commands,cert['rows'])):
            refs=[command['antecedent'],command['implication']] if command['rule']=='mp' else ([command['source']] if command['rule']=='generalize' else [])
            need(row['row']==i and row['rule']==command['rule'] and row['ordered_prior_rows']==refs and
                 row['formula_sha256']==hashlib.sha256(canonical(command['formula'])).hexdigest(),'literal certificate row projection')
        need(commands[-1]['formula']==cert['target'],'exact final target')
        primary=True
    else:
        need(final['status']=='UNKNOWN' and native['caller_returncode']==2 and receipt['pending_external'] is False and
             final['primary_pending_caller'] is False,'honest incomplete primary result')
    result={'schema':'ROOT-point-compact-Q-saved-disposition-v1','purpose':purpose,
        'controls_accepted':controlsok,'primary_accepted':primary,'resource_accepted':timeok and memoryok,
        'joint_twenty_seconds_accepted':timeok,'memory_accepted':memoryok,'lifecycle_output_closed':True,
        'classification':'point-produced independently checked word' if primary else 'actual negative/lifecycle controls' if controlsok else 'point BASE UNKNOWN',
        'native_launch_to_postprobe_ns':post-launch,'native_caller_elapsed_ns':terminal-launch,'tool_elapsed_ms':wall['elapsed_ms'],
        'SELF_cut_bytes':selfcut,'maximum_serial_leaf_peak_bytes':childpeak,'live_epoch_bound_bytes':live,
        'true_terminal_inclusive_peak_bytes':terminalpeak,'aggregate_owned_bound_bytes':bound,'aggregate_cap_bytes':536870912,
        'resource_rule':'point-sequential-cutoff-max-v1','sequential_leaf_count':len(children),'all_true_reaped':True,
        'complete_saved_output_files':len(actualpaths),'complete_saved_output_bytes':total+pin(finalpath)['bytes'],
        'plan':pin(planpath),'provisional':pin(finalpath),'native_terminal':pin(ext/'native-terminal.json'),
        'external_observation':pin(ext/'observation.json'),'tool_bracket':pin(ext/'tool-bracket.json'),
        'point_full24_trajectory_native_RL_accepted':False,'old_UNKNOWNs_promoted':False,'goal_complete':False,
        'scope':'Fixed reviewed pinned Sources/Darwin ABI. Saved evidence reconciliation, no mathematical or full-domain trajectory replay. No GCTS/RL advantage demonstrated.'}
    with (ROOT/('ROOT-'+purpose+'-disposition-v1.json')).open('x') as f:
        json.dump(result,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main(sys.argv[1:])
