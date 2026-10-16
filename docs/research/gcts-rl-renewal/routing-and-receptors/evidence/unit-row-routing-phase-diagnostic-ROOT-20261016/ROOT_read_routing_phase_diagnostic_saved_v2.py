"""Saved metadata/ASCII diagnostics only. Never imports or evaluates scientific Source.
A complete readout is not a qualification, proof, restoration or exhaustion claim.
"""
import hashlib,json,math,os,stat,sys,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
EXPECTED_CONTRACT={'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-routing-phase-diagnostic-cold-source-20261016/Source-contract-v1.json', 'sha256': 'b75016984df98895c6429491d9bb1cc3039be2042b3816d72c5f749d3473fc06', 'bytes': 52221}
VERSION='unit-row-routing-phase-saved-diagnostic-reader-v2'
PURPOSE='unit-row-marked-aware-router-protocol-controls'
INVOCATION='routing-phase-diagnostic-20261016-v1'
CLOCK_DOMAIN='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
LIMITS={'aggregate_owned_bytes':536870912,'caller_finish_reserve_seconds':1,'caller_seconds':90,'failure_only_seconds':55,'joint_seconds':20,'owned_seconds':60}
LABELS=('NATIVE_READY_BEFORE_PLAN', 'BEFORE_CURRENT_SOURCE_READS', 'BEFORE_CURRENT_AUTHORITY_CHECKS', 'BEFORE_FIXED_INPUT_READS', 'BEFORE_MODULE_LOAD_AND_SEAL', 'BEFORE_PRIOR_STAGEB_AUTHENTICATION', 'BEFORE_FRESH_MARKING_CHECK', 'AFTER_FRESH_MARKING_CHECK', 'BEFORE_ROUTING_SETUP', 'BEFORE_ZERO_QUERY', 'BEFORE_ONE_QUERY', 'BEFORE_TWO_QUERY', 'BEFORE_ABSENT_QUERY', 'BEFORE_IMPLICATION_QUERY', 'BEFORE_ROUTING_ASSERTIONS', 'AFTER_ROUTING_PROTOCOL')
PHASE_PREFIX=b'UNQUALIFIED_ROUTING_PHASE_OBSERVATION '
MAX_MARKER_BYTES=1321
MAX_LINE_BYTES=93
ERROR_PREFIX=b'UNIT_ROW_GLOBAL_ENGINE_UNKNOWN: '
TICK_TIMEOUT_LINE=b'UNIT_ROW_GLOBAL_ENGINE_UNKNOWN: TimeoutError: complete marking data controls original20/500 reserve unfinished\n'
def need(value,reason):
    if not value:raise ValueError('saved routing phase diagnostic: '+reason)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def unique(items):
    value={}
    for key,child in items:need(key not in value,'duplicate JSON key');value[key]=child
    return value
def reject(value):raise ValueError('saved routing phase diagnostic: nonfinite JSON constant')
def finite(value):
    result=float(value);need(math.isfinite(result),'finite JSON number');return result
def decode(raw):return json.loads(raw,object_pairs_hook=unique,parse_constant=reject,parse_float=finite)
def buffer_pin(path,raw):return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read_raw(path,cap):
    need(type(path)is Path or isinstance(path,Path),'literal saved path')
    need(path.is_absolute()and path==path.resolve(),'canonical saved path')
    fd=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd);need(stat.S_ISREG(info.st_mode)and 0<=info.st_size<=cap,'bounded regular complete file')
        blocks=[];size=0
        while True:
            block=os.read(fd,min(65536,cap+1-size))
            if not block:break
            blocks.append(block);size+=len(block);need(size<=cap,'whole file cap and EOF')
        raw=b''.join(blocks);need(len(raw)==info.st_size,'same opened complete file size')
        return raw
    finally:os.close(fd)
def pinned(ref,cap=1048576):
    need(type(ref)is dict and set(ref)=={'path','sha256','bytes'},'exact raw capsule')
    need(type(ref['path'])is str and type(ref['bytes'])is int and 0<=ref['bytes']<=cap,'literal capsule path/size')
    need(type(ref['sha256'])is str and re.fullmatch('[0-9a-f]{64}',ref['sha256'])is not None,'literal capsule hash')
    path=Path(ref['path']);raw=read_raw(path,cap);need(buffer_pin(path,raw)==ref,'raw capsule SHA/length/EOF')
    return raw
def saved_json(path,cap=1048576):
    raw=read_raw(path,cap);return decode(raw),buffer_pin(path,raw)
def exact_int(value,low,high):return type(value)is int and low<=value<=high
def same(left,right):need(canonical(left)==canonical(right),'full literal metadata concordance')

def main():
    need(len(sys.argv)==1,'no extra arguments or scientific inputs')
    plan_path=HERE/'ROOT-RP-plan-v1.json';plan,plan_ref=saved_json(plan_path)
    need(type(plan)is dict and set(plan)=={'schema','invocation_id','purpose','output_directory','sources','inputs','source_contract','reviews','ROOT_authorization','runtime','limits','resource_rule'},'exact plan12')
    need(plan['schema']=='ROOT-routed-engine-qualification-plan-v1'and plan['purpose']==PURPOSE and plan['invocation_id']==INVOCATION,'one declared diagnostic endpoint')
    same(plan['limits'],LIMITS);need(all(type(x)is int for x in plan['limits'].values()),'literal unchanged limits')
    need(plan['resource_rule']=='single-owned-process-native-terminal-v1','native resource rule')
    same(plan['source_contract'],EXPECTED_CONTRACT);contract=decode(pinned(EXPECTED_CONTRACT))
    need(contract['schema']=='unit-row-routing-phase-diagnostic-cold-Source-contract-v1','current caller contract schema')
    same(contract['sources'],plan['sources']);same(contract['inputs'],plan['inputs']);same(contract['limits'],LIMITS)
    need(len(plan['sources'])==14 and len(plan['inputs'])==8 and len(contract['original_model_sources'])==17 and len(contract['original_model_inputs'])==2,'current14/input8 and original17/input2')
    same(contract['source'],plan['sources']['intake'])
    for group in(plan['sources'],plan['inputs'],contract['original_model_sources'],contract['original_model_inputs']):
        for ref in group.values():pinned(ref,4*1048576+131072)
    same(contract['original_model_inputs'],{k:plan['inputs'][k]for k in('declaration','profile')})
    pinned(plan['runtime']);need(set(plan['reviews'])=={'ROOT','peer'},'two distinct Source reviews')
    for role,ref in plan['reviews'].items():
        review=decode(pinned(ref));need(review['scope']=='unit-row-routing-phase-diagnostic-cold-Source'and review['author_identity']=='/root/hilbert_advice_controls','current author and review scope')
        same(review['source'],contract['source']);same(review['source_contract'],EXPECTED_CONTRACT);same(review['sources'],plan['sources'])
        need(review['source_only']is review['source_review_passed']is True and type(review['scientific_calls'])is int and review['scientific_calls']==0 and review['scientific_acceptance']is False,'genuine Source-only pass')
        need(review['reviewer_identity']=='/root'if role=='ROOT'else review['reviewer_identity']not in('/root','/root/hilbert_advice_controls'),'distinct reviewer identity')
    need(Path(plan['ROOT_authorization']['path'])==HERE/'ROOT-RP-authorization-v1.json','fixed Root grant file')
    grant=decode(pinned(plan['ROOT_authorization']))
    need(grant['schema']=='ROOT-routed-engine-qualification-authorization-v1'and grant['author_identity']=='/root'and grant['actual_execution_authorized']is True and type(grant['maximum_actual_invocations'])is int and grant['maximum_actual_invocations']==1,'once Root grant')
    for key in('invocation_id','purpose','sources','inputs','source_contract','reviews','runtime','limits','resource_rule','output_directory'):same(grant[key],plan[key])
    external=HERE/'RP-external-v1';owned=HERE/'RP-owned-v1';need(Path(plan['output_directory'])==owned,'fixed owned directory')
    bracket,bracket_ref=saved_json(HERE/'ROOT-RP-tool-bracket-v1.json')
    need(bracket['schema']=='ROOT-complete-tool-Date-bracket-v1'and bracket['plan_sha256']==plan_ref['sha256']and bracket['plan_bytes']==plan_ref['bytes'],'same plan tool bracket')
    code=bracket['tool_exit_code'];need(exact_int(code,0,255),'terminal literal tool exit')
    sid,seen=bracket['tool_session_id'],bracket['observed_session_id']
    need((sid is None and seen is None)or(exact_int(sid,1,2**63-1)and type(seen)is int and seen==sid),'same terminal session or none')
    need(bracket.get('unchanged_actual_restarted')is False,'no unchanged restart')
    need(type(bracket['began_Date_ms'])is int and type(bracket['ended_Date_ms'])is int,'literal Date bounds')
    duration=(bracket['ended_Date_ms']-bracket['began_Date_ms'])/1000
    need(duration==bracket['complete_Date_seconds']and 0<=duration<=60 and duration+1<=90,'whole tool Date/caller closure')
    names=('ONCE.json','native-terminal.json','observation.json','meter-stdout.txt','meter-stderr.txt','postterminal-probe-stdout.txt','postterminal-probe-stderr.txt')
    raw={name:read_raw(external/name,65536 if name=='meter-stderr.txt'else 1048576)for name in names}
    refs={name:buffer_pin(external/name,value)for name,value in raw.items()}
    once,native,observation=(decode(raw[name])for name in('ONCE.json','native-terminal.json','observation.json'))
    need(once['schema']=='ROOT-ordinary-once-consumed-v1'and observation['schema']=='ROOT-ordinary-external-observation-v1','once/native observation schemas')
    for value in(once,observation):
        need(value['plan_sha256']==plan_ref['sha256']and value['plan_bytes']==plan_ref['bytes']and value['invocation_id']==INVOCATION and value['purpose']==PURPOSE,'consumed same once plan/invocation/purpose')
    need(native['schema']=='ROOT-Q-native-terminal-meter-v1'and native['version']=='Q-external-native-terminal-meter-Source-v2-global-clock'and native['CLOCK_DOMAIN']==CLOCK_DOMAIN,'existing meter2/same native clock')
    need(native['utility_argv']==[plan['runtime']['path'],'-I','-S','-B',contract['source']['path'],str(plan_path)],'actual utility argv/current Source/runtime/plan')
    need(type(native['caller_returncode'])is int and native['caller_returncode']==observation['meter_returncode']==code and type(native['wait4_status'])is int and native['wait4_status']==code*256,'terminal exit/wait4status')
    need(type(observation['probe_returncode'])is int and observation['probe_returncode']==0 and type(observation['meter_returncode'])is int and native['all_reaped']is True and type(native['wait4_pid'])is int and native['caller_pid']==native['wait4_pid']and exact_int(native['caller_pid'],1,2**63-1),'same owned pid/reaped/probe')
    need(native['error']is None and native['interrupted']is native['cancellation_forwarded']is False,'clean terminal meter closure')
    need(native['all_strong_acceptance_false']is True and observation['measurement_only']is True,'external measurement-only scope')
    for value in(native,observation):
        need(value['ROOT_resource_accepted']is value['ROOT_primary_accepted']is False,'native pending flags')
    need(raw['postterminal-probe-stderr.txt']==b'','empty probe stderr')
    probe_raw=raw['postterminal-probe-stdout.txt'];need(re.fullmatch(rb'(0|[1-9][0-9]*)\n',probe_raw)is not None,'whole literal probe scalar LF')
    probe=int(probe_raw);need(probe==observation['postterminal_native_probe_ns'],'same saved postterminal probe')
    start,terminal=native['caller_launch_began_ns'],native['caller_terminal_observed_ns']
    need(all(exact_int(x,0,2**63-1)for x in(start,terminal,probe,native['meter_began_ns'],native['observed_before_output_ns'],observation['external_began_ns']))and observation['external_began_ns']<=native['meter_began_ns']<=start<terminal<=native['observed_before_output_ns']<=probe and type(native['caller_kernel_elapsed_ns'])is int and terminal-start==native['caller_kernel_elapsed_ns']and probe-start<55000000000,'complete native failure55 closure')
    peak=native['caller_kernel_peak_bytes'];need(type(peak)is int and peak==native['wait4_usage'][2]and 0<peak<=536870912,'whole owned peak512')
    stderr=raw['meter-stderr.txt'];need(len(stderr)<=MAX_MARKER_BYTES+2200 and stderr.isascii(),'bounded ASCII phase/error wire')
    samples=[];error_line=None;marker_bytes=0;unparsed=[];wire_recognizing=True
    lines=stderr.splitlines(keepends=True);tail=b''
    if lines and not lines[-1].endswith(b'\n'):
        tail=lines.pop();need(len(tail)<=2200,'bounded final incomplete ASCII fragment')
    for line in lines:
        if wire_recognizing and line.endswith(b'\n') and line.startswith(ERROR_PREFIX):
            need(error_line is None and len(line)<=2200,'one original complete error line')
            error_line=line.decode('ascii');wire_recognizing=False;continue
        match=re.fullmatch(re.escape(PHASE_PREFIX)+rb'([A-Z0-9_]+) (0|[1-9][0-9]*)\n',line)if wire_recognizing else None
        if match is None:
            unparsed.append(line.decode('ascii'));wire_recognizing=False;continue
        need(len(line)<=MAX_LINE_BYTES,'fixed label whole-line bound')
        label=match.group(1).decode('ascii');need(len(samples)<len(LABELS)and label==LABELS[len(samples)],'literal single-use ordered prefix')
        ns=int(match.group(2));need(exact_int(ns,0,2**63-1)and start<=ns<terminal<=probe,'same native launch/sample/terminal/probe clock')
        need(not samples or samples[-1]['native_ns']<=ns,'nondecreasing native reads')
        marker_bytes+=len(line);samples.append(dict(label=label,native_ns=ns))
    need(len(samples)<=16 and marker_bytes<=MAX_MARKER_BYTES,'finite sixteen-site total marker bound')
    outputs=[];output_raw={}
    if owned.exists():
        need(owned.is_dir()and not owned.is_symlink(),'owned directory')
        for path in sorted(owned.iterdir()):
            need(path.name in('engine-result.json','response.jsonl'),'no late diagnostic/context files in this caller')
            content=read_raw(path,4194304 if path.name=='engine-result.json'else 1048576)
            output_raw[path.name]=content;outputs.append(buffer_pin(path,content))
    clock_context=None;positive_wire_metadata_checked=False
    if code==0:
        need(len(samples)==16 and error_line is None and not tail and not unparsed,'zero exit reaches all sixteen complete markers')
        need(set(output_raw)=={'engine-result.json','response.jsonl'},'whole existing output2')
        stdout=raw['meter-stdout.txt'];need(stdout.endswith(b'\n')and stdout.count(b'\n')==1,'single existing final metadata LF')
        final=decode(stdout);need(canonical(final)+b'\n'==stdout,'canonical whole final metadata')
        same(sorted(final),sorted(['schema','outputs','response','pending_external','logical_proof_accepted','ROOT_resource_accepted']))
        need(final['schema']=='ROOT-unit-row-routed-engine-qualification-final-observation-v1'and final['pending_external']is True,'existing final metadata schema')
        same(final['outputs'],outputs);same(final['response'],outputs[-1])
        need(final['logical_proof_accepted']is final['ROOT_resource_accepted']is False,'pending final acceptance')
        response=output_raw['response.jsonl'].splitlines(keepends=True)
        need(len(response)==2 and all(x.endswith(b'\n')for x in response),'whole response2LF')
        body,completion=map(decode,response)
        need(canonical(body)+b'\n'==response[0]and canonical(completion)+b'\n'==response[1],'canonical entire response')
        same(sorted(completion),sorted(['schema','body_sha256','body_bytes','exit_zero_and_coordinator_deadline_required']))
        need(completion['schema']=='Q-clean-verifier-response-completion-v1'and completion['body_sha256']==hashlib.sha256(response[0]).hexdigest()and completion['body_bytes']==len(response[0])and completion['exit_zero_and_coordinator_deadline_required']is True,'full response completion hash/size')
        need(body['schema']=='ROOT-unit-row-routed-engine-qualification-response-body-v1'and body['version']=='unit-row-routing-phase-diagnostic-cold-v1'and body['status']=='COMPLETE_WORKER_PENDING_EXTERNAL','current body schema/version')
        same(body['plan'],{k:plan_ref[k]for k in('sha256','bytes')});same(body['sources'],plan['sources']);same(body['inputs'],plan['inputs']);same(body['outputs'],outputs[:1]);same(body['limits'],LIMITS)
        same(body['language_binding'],contract['original_model_binding']);same(body['original_model_binding'],contract['original_model_binding'])
        need(body['invocation_id']==INVOCATION and body['resource_rule']==plan['resource_rule']and body['CLOCK_DOMAIN']==CLOCK_DOMAIN,'same current invocation/resource/clock')
        for k in('ROOT_resource_accepted','logical_proof_accepted','complete_GCTS_model_accepted','GCTS_search_trajectory_accepted','failure_marking_activated','RL_accepted','GCTS_advantage_claimed'):need(body[k]is False,'body strong flags pending')
        began,deadline=body['joint_began_ns'],body['joint_deadline_ns']
        need(exact_int(began,0,2**63-1)and exact_int(deadline,0,2**63-1)and start<=began<terminal and deadline==began+20000000000,'original internal clock and deadline metadata')
        need(all(began<=s['native_ns']<deadline for s in samples),'all markers in original internal window')
        clock_context={k:body[k]for k in('joint_began_ns','joint_deadline_ns','CLOCK_DOMAIN')}
        positive_wire_metadata_checked=True
        classification='DIAGNOSTIC_EXIT_ZERO_NO_CASE_QUALIFICATION'
    else:
        need(raw['meter-stdout.txt']==b'','nonzero has no fabricated positive final wire')
        classification='UNQUALIFIED_FAILURE_PHASE_DIAGNOSTIC_ONLY'
    intervals=[dict(from_label=x['label'],to_label=y['label'],inclusive_native_ns=y['native_ns']-x['native_ns'],exclusive_method_cost=False)for x,y in zip(samples,samples[1:])]
    result=dict(schema='ROOT-routing-phase-saved-diagnostic-readout-v1',version=VERSION,classification=classification,diagnostic_only=True,
        plan=plan_ref,authorization=plan['ROOT_authorization'],source_contract=EXPECTED_CONTRACT,sources=plan['sources'],inputs=plan['inputs'],original_model_sources=contract['original_model_sources'],original_model_inputs=contract['original_model_inputs'],original_model_binding=contract['original_model_binding'],
        tool_bracket=bracket_ref,native_evidence=refs,terminal_exit_code=code,all_reaped=True,native_terminal_closed=True,native_worker_lifetime_ns=terminal-start,native_launch_to_postprobe_ns=probe-start,aggregate_B_bytes=peak,complete_Date_seconds=duration,
        raw_stderr=refs['meter-stderr.txt'],stderr_error_line=error_line,stderr_unparsed_complete_lines=unparsed,stderr_uninterpreted_trailing_fragment=tail.decode('ascii')if tail else None,stderr_partial_or_unparsed_bytes_interpreted=False,
        native_tick_timeout_line_observed=error_line==TICK_TIMEOUT_LINE.decode('ascii'),caller_lifetime_at_least20=terminal-start>=20000000000,failure_cause_established=False,
        phase_samples=samples,phase_marker_wire_bytes=marker_bytes,declared_phase_labels=list(LABELS),complete_marker_line_count=len(samples),latest_reached_boundary=samples[-1]['label']if samples else None,
        inclusive_group_intervals=intervals,original20_clock_context=clock_context,positive_wire_metadata_checked=positive_wire_metadata_checked,original20_native_time_bound_observed=probe-start<20000000000,
        owned_output_directory_exists=owned.exists(),raw_output_files=outputs,scientific_payload_decoded=False,successful_payload_requires_separate_reconciliation=code==0,
        reader=buffer_pin(Path(__file__).resolve(),read_raw(Path(__file__).resolve(),1048576)),reported_case_count=None,qualified_case_count=0,case_completion_inferred=False,qualification_accepted=False,engine_promoted=False,
        original20_positive_gate_accepted=False,native_resource_success_accepted=False,logical_proof_accepted=False,exact_point_board_accepted=False,restoration_accepted=False,exhaustion_accepted=False,trajectory_accepted=False,marking_activated=False,GCTS_advantage_claimed=False,RL_accepted=False,scientific_replay=False,
        interpretation='Fixed reached writes only. Inclusive groups include guards, fixture/state construction, IO, nested work and gaps; no exclusive cost, active failure frame, returned query, mathematical result or cause is inferred. Partial or unparsed ASCII stays raw and stops further recognition. Even exit0 and complete positive metadata confer no case/engine qualification; scientific payload remains opaque. No retroactive explanation of the older failure.')
    out=HERE/'ROOT-RP-diagnostic-readout-v1.json';raw_result=json.dumps(result,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False).encode()+b'\n'
    need(len(raw_result)<=131072,'bounded metadata readout128KiB')
    with out.open('xb')as f:f.write(raw_result)
    print(json.dumps(dict(readout=buffer_pin(out,raw_result),classification=classification,qualification_accepted=False,scientific_replay=False)))
if __name__=='__main__':main()
