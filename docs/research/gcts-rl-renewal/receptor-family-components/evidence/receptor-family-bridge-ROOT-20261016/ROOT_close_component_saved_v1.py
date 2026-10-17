"""Root saved-data closure only: no project imports, semantic calls or clocks.

Authenticates one already terminal native run and its complete lossless records.
Case assertions ran only inside that run. This helper does not replay them.
"""
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import zlib

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
CONTRACT={'path':str(BASE/'receptor-family-bridge-cold-ROOT-source-20261016/Source-contract-v2.json'),
 'sha256':'4d2387f7d343ebe4606ccf1a4aa897c0b2842f83a95ffb99e2e0b04f280d7c2e','bytes':27889}
PURPOSE='receptor-family-primitive-bridge-component-controls'
INVOCATION='receptor-family-component-20261016-v1'
CLOCK='time.clock_gettime_ns(time.CLOCK_MONOTONIC)'
LIMITS={'aggregate_owned_bytes':536870912,'caller_finish_reserve_seconds':1,'caller_seconds':90,
 'failure_only_seconds':55,'joint_seconds':20,'owned_seconds':60}

def need(value,why):
    if not value:raise ValueError('saved family component: '+why)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

def unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result,'duplicate key');result[key]=value
    return result

def reject(value):raise ValueError('nonfinite JSON constant')

def finite(value):
    result=float(value);need(math.isfinite(result),'finite JSON');return result

def decode(raw):
    return json.loads(raw,object_pairs_hook=unique,parse_constant=reject,parse_float=finite)

def raw_pin(raw):return dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

def read_raw(path,cap=1048576):
    path=Path(path);need(path.is_absolute()and path==path.resolve(),'canonical path')
    fd=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd);need(stat.S_ISREG(info.st_mode)and 0<=info.st_size<=cap,'bounded regular file')
        blocks=[];size=0
        while True:
            block=os.read(fd,min(65536,cap+1-size))
            if not block:break
            blocks.append(block);size+=len(block);need(size<=cap,'whole EOF')
        raw=b''.join(blocks);need(len(raw)==info.st_size,'whole opened size');return raw
    finally:os.close(fd)

def pin(path,cap=1048576):return dict(path=str(path),**raw_pin(read_raw(path,cap)))

def pinned(ref,cap=4*1048576+131072):
    need(type(ref)is dict and set(ref)=={'path','sha256','bytes'},'capsule keys')
    need(type(ref['bytes'])is int and 0<=ref['bytes']<=cap and type(ref['sha256'])is str
         and re.fullmatch('[0-9a-f]{64}',ref['sha256'])is not None,'capsule scalar types')
    raw=read_raw(ref['path'],cap);need(raw_pin(raw)=={k:ref[k]for k in('sha256','bytes')},'whole capsule');return raw

def same(left,right):need(canonical(left)==canonical(right),'literal concordance')
def integer(value,lo=0,hi=2**63-1):return type(value)is int and lo<=value<=hi
def saved(name):return decode(read_raw(HERE/name))
def save(name,value):
    path=HERE/name;raw=json.dumps(value,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False).encode()+b'\n'
    with path.open('xb')as file:file.write(raw)
    return dict(path=str(path),**raw_pin(raw))

def main():
    plan_path=HERE/'ROOT-RF-plan-v1.json';plan=saved('ROOT-RF-plan-v1.json');pr=pin(plan_path)
    need(set(plan)=={'schema','invocation_id','purpose','output_directory','sources','inputs',
        'source_contract','reviews','ROOT_authorization','runtime','limits','resource_rule'},'plan12')
    need(plan['schema']=='ROOT-routed-engine-qualification-plan-v1'and plan['purpose']==PURPOSE
         and plan['invocation_id']==INVOCATION,'one fixed component actual')
    same(plan['source_contract'],CONTRACT);c=decode(pinned(CONTRACT));same(c['sources'],plan['sources']);same(c['inputs'],plan['inputs'])
    same(plan['limits'],LIMITS);need(all(type(v)is int for v in plan['limits'].values()),'literal six limits')
    need(len(plan['sources'])==18 and len(plan['inputs'])==9 and len(c['original_model_sources'])==17
         and len(c['original_model_inputs'])==2,'current and semantic scope')
    for refs in(plan['sources'],plan['inputs'],c['original_model_sources'],c['original_model_inputs']):
        for ref in refs.values():pinned(ref)
    pinned(plan['runtime']);need(set(plan['reviews'])=={'ROOT','peer'},'review pair')
    for role,ref in plan['reviews'].items():
        review=decode(pinned(ref));same(review['source'],c['source']);same(review['sources'],plan['sources']);same(review['source_contract'],CONTRACT)
        need(review['author_identity']=='/root'and review['scope']==c['scope']
             and review['source_only']is review['source_review_passed']is True
             and type(review['scientific_calls'])is int and review['scientific_calls']==0
             and review['scientific_acceptance']is False,'current scoped Source review')
        need(review['reviewer_identity']=='/root'if role=='ROOT'else review['reviewer_identity']!='/root','distinct peer')
    grant=decode(pinned(plan['ROOT_authorization']))
    need(grant['schema']=='ROOT-routed-engine-qualification-authorization-v1'and grant['author_identity']=='/root'
         and grant['actual_execution_authorized']is True and type(grant['maximum_actual_invocations'])is int
         and grant['maximum_actual_invocations']==1,'once grant')
    for key in('invocation_id','purpose','sources','inputs','source_contract','reviews','runtime','limits','resource_rule','output_directory'):same(grant[key],plan[key])
    need(plan['resource_rule']=='single-owned-process-native-terminal-v1','same native rule')
    bracket=saved('ROOT-RF-tool-bracket-v1.json');code=bracket['tool_exit_code']
    need(bracket['schema']=='ROOT-complete-tool-Date-bracket-v1'and bracket['plan_sha256']==pr['sha256']
         and bracket['plan_bytes']==pr['bytes']and bracket['unchanged_actual_restarted']is False,'tool bracket same once plan')
    need(integer(code,0,255)and integer(bracket['began_Date_ms'])and integer(bracket['ended_Date_ms']),'literal bracket')
    sid,seen=bracket['tool_session_id'],bracket['observed_session_id']
    need((sid is None and seen is None)or(integer(sid,1)and type(seen)is int and seen==sid),'same actual handle')
    seconds=(bracket['ended_Date_ms']-bracket['began_Date_ms'])/1000
    need(seconds==bracket['complete_Date_seconds']and 0<=seconds<=60 and seconds+1<=90,'complete tool/caller closure')
    external,owned=HERE/'RF-external-v1',HERE/'RF-owned-v1';need(str(owned)==plan['output_directory'],'fixed owned path')
    names=['ONCE.json','native-terminal.json','observation.json','meter-stdout.txt','meter-stderr.txt',
        'postterminal-probe-stdout.txt','postterminal-probe-stderr.txt']
    need(sorted(p.name for p in external.iterdir())==sorted(names),'complete external files')
    raw={name:read_raw(external/name)for name in names};refs={name:dict(path=str(external/name),**raw_pin(value))for name,value in raw.items()}
    once,native,observation=(decode(raw[name])for name in('ONCE.json','native-terminal.json','observation.json'))
    need(once['schema']=='ROOT-ordinary-once-consumed-v1'and observation['schema']=='ROOT-ordinary-external-observation-v1','measurement schemas')
    for value in(once,observation):
        need(value['plan_sha256']==pr['sha256']and value['plan_bytes']==pr['bytes']and value['purpose']==PURPOSE
             and value['invocation_id']==INVOCATION,'same consumed actual')
    need(native['schema']=='ROOT-Q-native-terminal-meter-v1'and native['version']=='Q-external-native-terminal-meter-Source-v2-global-clock'
         and native['CLOCK_DOMAIN']==CLOCK and native['error']is None and native['interrupted']is False
         and native['cancellation_forwarded']is False and native['all_reaped']is True,'native terminal')
    need(native['utility_argv']==[plan['runtime']['path'],'-I','-S','-B',c['source']['path'],str(plan_path)],'actual current argv')
    need(integer(native['caller_pid'],1)and type(native['wait4_pid'])is int and native['caller_pid']==native['wait4_pid']
         and type(native['caller_returncode'])is int and native['caller_returncode']==observation['meter_returncode']==code
         and type(native['wait4_status'])is int and native['wait4_status']==code*256,'exact pid/status/exit')
    for value in(native,observation):need(value['ROOT_resource_accepted']is value['ROOT_primary_accepted']is False,'pending native flags')
    need(observation['probe_returncode']==0 and type(observation['probe_returncode'])is int
         and observation['measurement_only']is True and raw['postterminal-probe-stderr.txt']==b'','native probe')
    need(re.fullmatch(rb'(0|[1-9][0-9]*)\n',raw['postterminal-probe-stdout.txt'])is not None,'complete probe scalar')
    start,terminal,probe=native['caller_launch_began_ns'],native['caller_terminal_observed_ns'],int(raw['postterminal-probe-stdout.txt'])
    need(probe==observation['postterminal_native_probe_ns']and all(integer(v)for v in(start,terminal,probe,
         native['meter_began_ns'],native['observed_before_output_ns'],observation['external_began_ns'])),'native literal clock reads')
    need(observation['external_began_ns']<=native['meter_began_ns']<=start<terminal<=native['observed_before_output_ns']<=probe
         and type(native['caller_kernel_elapsed_ns'])is int and terminal-start==native['caller_kernel_elapsed_ns']
         and probe-start<55000000000,'failure55 and original native timeline')
    peak=native['caller_kernel_peak_bytes'];need(integer(peak,1,536870912)and peak==native['wait4_usage'][2],'native owned peak512')
    readout=dict(schema='ROOT-receptor-family-component-readout-v1',plan=pr,source_contract=CONTRACT,
        sources=plan['sources'],inputs=plan['inputs'],original_model_binding=c['original_model_binding'],
        tool_bracket=pin(HERE/'ROOT-RF-tool-bracket-v1.json'),native_evidence=refs,terminal_exit_code=code,
        native_launch_to_postprobe_ns=probe-start,native_worker_lifetime_ns=terminal-start,
        aggregate_B_bytes=peak,complete_Date_seconds=seconds,all_reaped=True,
        current_engine_qualified_case_count=8,current_engine_required_case_count=12,engine_promoted=False,
        new_theorem_accepted=False,logical_proof_accepted=False,scheduler_or_rollback_accepted=False,
        family_library_activated=False,RL_accepted=False,GCTS_advantage_claimed=False,scientific_replay=False)
    if code!=0:
        need(raw['meter-stdout.txt']==b'','no positive final on failure')
        readout.update(classification='UNQUALIFIED_COMPONENT_FAILURE_OR_UNKNOWN',qualified_component_case_count=0,
            component_controls_accepted=False,ROOT_resource_accepted=False,
            raw_error=raw['meter-stderr.txt'].decode('utf-8',errors='replace'),failure_cause_established=False,
            owned_directory_exists=owned.exists())
    else:
        need(raw['meter-stderr.txt']==b''and probe-start<20000000000,'positive native20 complete closure')
        need(sorted(p.name for p in owned.iterdir())==['engine-result.json','response.jsonl'],'owned output2')
        encoded=read_raw(owned/'engine-result.json',4*1048576);response=read_raw(owned/'response.jsonl')
        er=dict(path=str(owned/'engine-result.json'),**raw_pin(encoded));rr=dict(path=str(owned/'response.jsonl'),**raw_pin(response))
        final=decode(raw['meter-stdout.txt']);need(canonical(final)+b'\n'==raw['meter-stdout.txt'],'whole final LF')
        need(final['schema']==c['artifact_API']['final_schema']and final['pending_external']is True,'final schema')
        same(final['outputs'],[er,rr]);same(final['response'],rr)
        need(final['logical_proof_accepted']is final['ROOT_resource_accepted']is False,'final pending')
        lines=response.splitlines(keepends=True);need(len(lines)==2 and all(v.endswith(b'\n')for v in lines),'response2LF')
        body,completion=map(decode,lines);need(all(canonical(v)+b'\n'==line for v,line in zip((body,completion),lines)),'canonical whole response')
        need(completion['schema']=='Q-clean-verifier-response-completion-v1'and completion['body_sha256']==raw_pin(lines[0])['sha256']
             and completion['body_bytes']==len(lines[0])and completion['exit_zero_and_coordinator_deadline_required']is True,'response completion')
        need(body['schema']==c['artifact_API']['response_schema']and body['version']==c['version']and body['status']=='COMPLETE_WORKER_PENDING_EXTERNAL'
             and body['invocation_id']==INVOCATION and body['CLOCK_DOMAIN']==CLOCK,'body identity')
        same(body['plan'],{k:pr[k]for k in('sha256','bytes')});same(body['sources'],plan['sources']);same(body['inputs'],plan['inputs']);same(body['outputs'],[er])
        same(body['limits'],LIMITS);same(body['language_binding'],c['original_model_binding']);same(body['original_model_binding'],c['original_model_binding'])
        need(body['resource_rule']==plan['resource_rule']and integer(body['joint_began_ns'])and integer(body['joint_deadline_ns'])
             and start<=body['joint_began_ns']<terminal and body['joint_deadline_ns']==body['joint_began_ns']+20000000000,'internal deadline metadata')
        for key in('ROOT_resource_accepted','logical_proof_accepted','complete_GCTS_model_accepted','failure_marking_activated','family_library_activated','engine_activated','RL_accepted','GCTS_advantage_claimed'):need(body[key]is False,'body strong flags')
        envelope=decode(encoded);need(canonical(envelope)+b'\n'==encoded and envelope['schema']=='ROOT-unit-row-lossless-result-envelope-v1'
             and envelope['encoding']=='zlib+base64'and integer(envelope['expanded_bytes'],1,16*1048576),'bounded full envelope')
        compressed=base64.b64decode(envelope['payload_base64'],validate=True)
        same(raw_pin(compressed),{'sha256':envelope['compressed_sha256'],'bytes':envelope['compressed_bytes']})
        stream=zlib.decompressobj();expanded=stream.decompress(compressed,16*1048576+1)
        need(stream.eof and not stream.unused_data and not stream.unconsumed_tail and len(expanded)<=16*1048576,'complete zlib EOF no tail')
        same(raw_pin(expanded),{'sha256':envelope['expanded_sha256'],'bytes':envelope['expanded_bytes']})
        result=decode(expanded);need(canonical(result)+b'\n'==expanded and result['schema']==c['artifact_API']['result_schema'],'complete canonical expanded result')
        same(result['sources'],plan['sources']);same(result['inputs'],plan['inputs']);same(result['language_binding'],c['original_model_binding'])
        need(result['purpose']==PURPOSE and result['logical_proof_accepted']is result['ROOT_resource_accepted']is False,'expanded scope')
        payload=result['family_bridge_component'];component=payload['component'];controls=component['controls']
        need(payload['schema']==c['artifact_API']['payload_schema']and payload['control_count']==12 and payload['all_controls_completed']is True,'payload scope')
        same(payload['original_model_sources'],c['original_model_sources']);same(payload['original_model_inputs'],c['original_model_inputs']);same(payload['original_model_binding'],c['original_model_binding'])
        same(payload['expected_cases'],c['expected_cases']);same([v['case']for v in controls],c['expected_cases'])
        need(len(controls)==12 and all(v['status']=='PASSED'and 'evidence'in v for v in controls)
             and component['schema']=='ROOT-receptor-family-component-cases-v1'and component['all_controls_completed']is True,'all ordered cases complete')
        need(component['implementation_version']=='ROOT-receptor-family-component-cases-v2-retained-checks-and-exceptions','current repaired cases')
        for key in('target_search_performed','logical_proof_accepted','engine_activated','family_library_activated',
            'complete_GCTS_model_accepted','scheduler_or_rollback_accepted','RL_accepted','GCTS_advantage_claimed','ROOT_resource_accepted'):need(payload[key]is False,'payload strong flags')
        for key in('proof_accepted','engine_activated','library_activated','RL_accepted','GCTS_advantage_claimed'):need(component[key]is False,'component strong flags')
        need(payload['current_engine_qualification_unchanged']is True and payload['original_qualified_case_count']==8
             and payload['original_required_case_count']==12 and payload['synthetic_syntax_hosts_not_native_authority']is True
             and payload['original_empty_Gamma_positive_assumption_unavailable']is True,'honest engine/native scope')
        same(payload['five_positive_adapter_rules'],['axiom','instantiate','eq_subst','mp','generalize'])
        records=component['records'];negatives=component['negative_cases']
        for record in records:
            need(type(record['request'])is dict and type(record['label'])is str,'full request retained')
            if 'check'in record:
                need(record['check']['status']=='CONDITIONAL_EXPANSION_CHECKED'and record['check']['conditional_expansion_checked']is True,'conditional record')
                same(record['proposal'],record['check']['expansion']);same(record['check']['request']['proposal'],record['proposal'])
            else:
                cluster=record['result'];need(cluster['status']=='READY_LOCAL_CLUSTER'
                     and cluster['local_member_membership_checked']is cluster['local_point_union_checked']is True,'native local cluster record')
                need(cluster['proof_accepted']is cluster['engine_activated']is cluster['scheduler_or_rollback_accepted']is False,'local flags')
                same(cluster['state'],component['original_state'])
        need(len(negatives)>=10 and all(v['rejected']is True and v['timeout_or_unknown_accepted_as_negative']is False
             and type(v['request'])is dict for v in negatives),'full definite-data negatives')
        labels=[v['label']for v in negatives]
        for label in('unused-port-final-formula-disagrees','nested-distinct-collapse-to-one-placement','remote-row-zero-mark','original-empty-Gamma'):need(label in labels,'retained interface/native negative')
        need(controls[10]['evidence']['declared_native_first_interruption_propagated']is True
             and controls[10]['evidence']['real_native_deadline_exhaustion_tested']is False,'declared seam scope')
        expanded_path=HERE/'ROOT-RF-expanded-result-v1.json'
        with expanded_path.open('xb')as file:file.write(expanded)
        readout.update(classification='BOUNDED_COMPONENT_CONTROLS_ACCEPTED',qualified_component_case_count=12,
            component_controls_accepted=True,ROOT_resource_accepted=True,controls=controls,
            record_count=len(records),negative_count=len(negatives),negative_labels=labels,
            outputs=[er,rr],expanded_result=dict(path=str(expanded_path),**raw_pin(expanded)),
            scientific_payload_decoded=True,proof_or_search_replayed=False,
            qualification_scope='Only12 infrastructure assertions. Human/synthetic fixtures, conditional local clusters; no target search, new theorem, native positive assumption, live rollback, engine/library/RL or gain acceptance.')
    out=save('ROOT-RF-component-readout-v1.json',readout)
    print(json.dumps(dict(readout=out,classification=readout['classification'],qualified_component_case_count=readout['qualified_component_case_count'],scientific_replay=False)))

if __name__=='__main__':main()
