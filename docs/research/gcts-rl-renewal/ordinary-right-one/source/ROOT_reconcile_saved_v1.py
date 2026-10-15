"""Saved-data-only closure. No project Source import or mathematical replay."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-ordinary-first-ready-ROOT-20261015')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def unique(pairs):
    result = {}
    for key,value in pairs:
        need(key not in result,'duplicate saved JSON key')
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda token:(_ for _ in ()).throw(ValueError(token)))


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def pin(path):
    path = Path(path)
    h,count = hashlib.sha256(),0
    with path.open('rb') as stream:
        while True:
            block=stream.read(65536)
            if not block:break
            h.update(block);count+=len(block)
    return {'path':str(path),'sha256':h.hexdigest(),'bytes':count}


def bare(record):
    return {key:record[key] for key in ('sha256','bytes')}


def lines(path, schema):
    raw=Path(path).read_bytes()
    need(raw.endswith(b'\n') and raw.count(b'\n')==2,'whole two-line JSON/EOF')
    bodyraw,trailerraw,_=raw.split(b'\n')
    body,trailer=decode(bodyraw),decode(trailerraw)
    need(canonical(body)==bodyraw and canonical(trailer)==trailerraw,'canonical saved response')
    need(trailer['schema']==schema and trailer['body_bytes']==len(bodyraw)+1 and
         trailer['body_sha256']==hashlib.sha256(bodyraw+b'\n').hexdigest() and
         trailer['exit_zero_and_coordinator_deadline_required'] is True,'whole response hash link')
    return body


def main(argv):
    need(len(argv)==1 and argv[0] in ('controls','primary'),'saved purpose')
    purpose=argv[0]
    planpath=ROOT/('ROOT-'+purpose+'-plan-v1.json')
    plan=decode(planpath.read_bytes())
    closure=decode((ROOT/('ROOT-'+purpose+'-closure-v1.json')).read_bytes())
    need(pin(planpath)==closure['plan'],'frozen complete actual plan')
    run=Path(plan['output_directory']);ext=Path(closure['external_directory'])
    finalpath=run/'ordinary-provisional.json'
    final=decode(finalpath.read_bytes())
    native=decode((ext/'native-terminal.json').read_bytes())
    observation=decode((ext/'observation.json').read_bytes())
    wall=decode((ext/'tool-bracket.json').read_bytes())
    need(final['plan']==bare(pin(planpath)) and final['purpose']==purpose and
         final['invocation_id']==plan['invocation_id'] and final['limits']==plan['limits'],'whole current actual context')
    need(native['all_reaped'] is True and native['wait4_pid']==native['caller_pid'] and
         native['caller_returncode']==0 and native['wait4_status']==0 and native['error'] is None and
         native['interrupted'] is False and native['cancellation_forwarded'] is False,'true native parent wait4 exit0')
    need(observation['meter_returncode']==0 and observation['probe_returncode']==0 and
         observation['plan_sha256']==pin(planpath)['sha256'],'actual meter and new-process postprobe')
    need(int((ext/'postterminal-probe-stdout.txt').read_bytes())==observation['postterminal_native_probe_ns'],
         'raw genuine probe matches observation')
    launch=native['caller_launch_began_ns'];terminal=native['caller_terminal_observed_ns']
    post=observation['postterminal_native_probe_ns'];began=final['joint_began_ns']
    need(launch<=began<=terminal<=post and post-launch<=20000000000,'all startup/work/check/output/exit/postprobe within20')
    need(final['joint_deadline_ns']==began+20000000000 and terminal<final['joint_deadline_ns'],
         'original inherited deadline unchanged')
    need(type(wall['elapsed_ms']) is int and 0<=wall['elapsed_ms']<=60000 and
         wall['elapsed_ms']+1000<=90000,'actual complete tool wall60/caller90+1')
    children=final['children'];cut=final['cutoff'];previous=began
    need(cut['all_reaped'] is True and cut['no_future_spawn'] is True and cut['child_count']==len(children),
         'irreversible all-reaped cutoff')
    for child in children:
        need(child['reaped'] is True and child['wait4_pid']==child['pid'] and child['returncode']==0 and
             child['wait4_status']==0 and previous<=child['launch_began_ns']<child['terminal_observed_ns']<=cut['observed_ns'],
             'each exact PID true exit0, serial closed lifetime')
        need(type(child['kernel_peak_bytes']) is int and child['kernel_peak_bytes']==child['usage'][2],
             'actual Darwin wait4 leaf peak bytes')
        previous=child['terminal_observed_ns']
    need(len({child['pid'] for child in children})==len(children),'distinct native leaf PIDs')
    need(cut['observed_ns']<=terminal,'cutoff precedes actual true terminal')
    childpeak=max((child['kernel_peak_bytes'] for child in children),default=0)
    terminalpeak=native['caller_kernel_peak_bytes'];selfcut=cut['SELF_peak_bytes']
    livebound=selfcut+childpeak;bound=max(livebound,terminalpeak)
    need(childpeak==final['maximum_leaf_peak_bytes'] and livebound==final['live_epoch_bound_bytes'],
         'complete sequential live epoch bound')
    need(terminalpeak>=max(selfcut,childpeak) and bound<=536870912,'genuine terminal tail and whole512MiB bound')
    need(final['cleanup_errors']==[] and final['error'] is None and final['output_inventory']['complete'] is True,
         'complete actual cleanup/output')
    total=0;paths=set()
    for record in final['output_inventory']['files']:
        path=run/record['path']
        need(path.resolve().is_relative_to(run.resolve()) and not path.is_symlink(),'owned regular output path')
        actual=pin(path)
        need(bare(actual)==bare(record),'complete saved output hash/bytes '+record['path'])
        paths.add(record['path']);total+=actual['bytes']
    need(total==final['output_inventory']['bytes'],'whole output byte total')
    actualpaths={str(path.relative_to(run)) for path in run.rglob('*') if path.is_file()}
    need(actualpaths==paths|{'ordinary-provisional.json'},'all owned output files, provisional separately pinned')
    stdout=(ext/'meter-stdout.txt').read_bytes()
    receipt=decode(stdout)
    need(receipt['provisional']==bare(pin(finalpath)) and receipt['pending_external'] is True and
         receipt['purpose']==purpose,'complete final provisional receipt')
    for flag in ('ROOT_primary_accepted','ROOT_resource_accepted','selected_provenance_accepted',
                 'point_state_accepted','full24_accepted','trajectory_accepted','RL_accepted','native_accepted','Q_BASE_output_injected'):
        need(final[flag] is False,'no lower-layer strong acceptance '+flag)
    if purpose=='controls':
        need(final['status']=='CONTROLS_PENDING_EXTERNAL_TERMINAL' and final['controls_pending_caller'] is True and
             final['word_logically_accepted'] is False and [c['role'] for c in children]==
             ['inert-a','inert-b','bad-word','bad-authority'],'exact actual controls only')
        controls={item['id']:item for item in final['controls']}
        need(set(controls)=={'real-sequential-leaves','corrupt-word','corrupt-authority','postseal-launch-denial','parent-exit-tail'},
             'every concrete control record')
        need(controls['real-sequential-leaves']['true_wait4_reaped'] is True and
             controls['real-sequential-leaves']['disjoint_closed_lifetimes'] is True,'real serial control')
        for label,status in [('bad-word','WORD_REJECTED'),('bad-authority','INTAKE_REJECTED')]:
            body=lines(run/(label+'-response.jsonl'),'Q-clean-verifier-response-completion-v1')
            need(body['validation']['status']==status and body['validation']['certificate'] is None and
                 body['validation']['word_logically_accepted'] is False,'genuine negative checker response')
        denial=controls['postseal-launch-denial'];tail=controls['parent-exit-tail']
        need(denial['specific_rejection']=='NO_SPAWN_AFTER_CUTOFF' and denial['Popen_reached'] is False and
             denial['otherwise_valid_fixed_leaf_arguments'] is True and
             denial['children_before']==denial['children_after']==len(children),'actual launch fence')
        need(tail['resident_requested_bytes']==33554432 and tail['touched_pages']==8192 and
             tail['SELF_cut']==selfcut and terminalpeak>=tail['SELF_after_tail']>selfcut,
             'resident postcutoff parent tail covered by genuine T')
    else:
        need(final['status']=='WORD_VERIFIED_PENDING_CALLER' and final['primary_pending_caller'] is True and
             final['word_logically_accepted'] is True and [c['role'] for c in children]==['producer','verifier'],
             'genuine searched then independently checked word')
        producer=lines(run/'producer-response.jsonl','Q-ordinary-producer-response-completion-v1')
        checked=lines(run/'verifier-response.jsonl','Q-clean-verifier-response-completion-v1')
        candidate=producer['result']['candidate'];certificate=checked['validation']['certificate']
        need(producer['result']==final['producer_result'] and certificate==final['certificate'] and
             certificate['completed'] is True and certificate['original_Gamma_target_sequent_accepted'] is True,
             'exact accepted independent certificate and searched result')
        commands=candidate['commands']
        need(certificate['commands_sha256']==hashlib.sha256(canonical(commands)).hexdigest() and
             certificate['essential_rows']==list(range(len(commands))) and
             1<=len(commands)<=24 and certificate['original_ordered_Gamma']==[],
             'whole essential original-context command word')
        for row,(command,certrow) in enumerate(zip(commands,certificate['rows'])):
            refs=[command['antecedent'],command['implication']] if command['rule']=='mp' else (
                 [command['source']] if command['rule']=='generalize' else [])
            need(certrow['row']==row and certrow['rule']==command['rule'] and certrow['ordered_prior_rows']==refs and
                 certrow['formula_sha256']==hashlib.sha256(canonical(command['formula'])).hexdigest(),
                 'literal row formula/reference projection')
        need(commands[-1]['formula']==certificate['target'],'literal exact final target')
    result={'schema':'ROOT-ordinary-Q-saved-disposition-v1','purpose':purpose,
        'resource_accepted':True,'controls_accepted':purpose=='controls','primary_accepted':purpose=='primary',
        'classification':'ordinary searched primitive proof' if purpose=='primary' else 'actual negative/lifecycle controls',
        'native_launch_to_postprobe_ns':post-launch,'native_caller_elapsed_ns':terminal-launch,
        'tool_elapsed_ms':wall['elapsed_ms'],'SELF_cut_bytes':selfcut,'maximum_serial_leaf_peak_bytes':childpeak,
        'live_epoch_bound_bytes':livebound,'true_terminal_inclusive_peak_bytes':terminalpeak,
        'aggregate_owned_bound_bytes':bound,'aggregate_cap_bytes':536870912,
        'resource_rule':'ordinary-sequential-cutoff-max-v1','sequential_leaf_count':len(children),
        'all_true_reaped':True,'complete_saved_output_files':len(actualpaths),'complete_saved_output_bytes':total+pin(finalpath)['bytes'],
        'plan':pin(planpath),'provisional':pin(finalpath),'native_terminal':pin(ext/'native-terminal.json'),
        'external_observation':pin(ext/'observation.json'),'tool_bracket':pin(ext/'tool-bracket.json'),
        'point_full24_trajectory_native_RL_accepted':False,'old_UNKNOWNs_promoted':False,'goal_complete':False,
        'scope':'Fixed reviewed Sources/pinned Darwin runtime; conventional word only. No independent full search trace replay, point search, native Wang board, full PA or speed advantage.'}
    destination=ROOT/('ROOT-'+purpose+'-disposition-v1.json')
    with destination.open('x') as stream:
        json.dump(result,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main(sys.argv[1:])
