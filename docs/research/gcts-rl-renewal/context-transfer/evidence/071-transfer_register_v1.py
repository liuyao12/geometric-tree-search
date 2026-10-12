"""Fresh-context static gate and immutable entire-pool registration bridge."""
import json
import time

def accepted_static_gate(compiled_pin,evidence_pin,static,life_receipt,pins):
    if set(pins)!= {'plan','result','lifetime','root_terminal'}:raise ValueError('actual exact fresh gate pins required')
    if (static['status']!='passed_independent_fresh_context_family_pool_audit'
            or life_receipt['status']!='passed_owned_independent_fresh_context_family_pool_audit'
            or life_receipt['child_exit']!=0 or life_receipt['child_reaped'] is not True):
        raise ValueError('new independent complete static resource PASS required')
    if static['plan']!=pins['plan'] or life_receipt['plan']!=pins['plan'] or life_receipt['result']!=pins['result']:
        raise ValueError('same exact audited resource-credited static result')
    if static['compiled_context_pin']!=compiled_pin or static['preparation_evidence_pin']!=evidence_pin:
        raise ValueError('fresh gate must bind exact new model and pool bytes')
    required={'primitive_license_count':229,'non_assumption_witness_count':226,'source_body_count':171,'single_types':171,'pair_types':29241}
    if any(type(static[k]) is not int or static[k]!=v for k,v in required.items()):raise ValueError('complete fresh static inventory/census')

def register_pool(g,original,projection,proposals,life,evidence,static):
    begin=time.perf_counter();core=life.core
    def same(a,b,label):
        if core.canonical(a)!=core.canonical(b):raise ValueError(label)
    same(evidence['model_epoch'],g.model_epoch,'fresh exact graph epoch')
    same(static['model_epoch'],g.model_epoch,'independent graph epoch')
    same(evidence['original_body_authority_epoch'],original.epoch,'fresh complete conditional source authority')
    same(static['original_body_authority_epoch'],original.epoch,'independent complete conditional source authority')
    same(evidence['graph_binding'],life.graph_binding(g),'fresh graph full binding')
    records=proposals.interfaces(g,original,projection,core);anchors=proposals.root_anchors(g,core)
    same(records,evidence['declared_interfaces'],'all 171 unchanged declared conclusions and exact body records')
    same(anchors,evidence['root_anchors'],'original boundary insertion order/new gen-zero hypothesis identities')
    groups=evidence['groups'];checked=static['groups_checked']
    if len(groups)!=len(checked):raise ValueError('no subset of complete fresh pool')
    specs=[];priorities=[]
    for index,(descriptor,receipt) in enumerate(zip(groups,checked)):
        same(descriptor['pool_index'],index,'complete index order');same(receipt['pool_index'],index,'audited complete order')
        same(core.digest(descriptor),receipt['descriptor_sha256'],'independent full descriptor payload')
        same(descriptor['descriptor_id'],receipt['descriptor_id'],'full source union identity')
        same(descriptor['fixed_priority'],receipt['fixed_priority'],'fixed complete-pool priorities')
        specs.append(core.canonical(descriptor['binding_specification']));priorities.append(descriptor['fixed_priority'])
    source_text=core.canonical(evidence['group_epoch_payload']['source_bindings'])
    authority=proposals.GroupAuthority(original.graph_text,'',original,life,core.canonical(records),core.canonical(anchors),tuple(specs),tuple(priorities),source_text)
    authority=proposals.GroupAuthority(authority.graph_text,core.digest(authority.epoch_payload()),original,life,authority.interface_text,authority.anchor_text,authority.spec_texts,authority.fixed_priorities,authority.source_text)
    same(authority.epoch,evidence['group_authority_epoch'],'fresh exact group authority epoch')
    same(authority.epoch,static['group_authority_epoch'],'independent group authority epoch')
    for index,descriptor in enumerate(groups):
        same(authority.expected(g,index,priorities[index]),descriptor,'entire source authorized canonical embedding/full union');authority.compile(g,descriptor)
    return authority,groups,{'entire_pool_registration_seconds':time.perf_counter()-begin,'registered_group_count':len(groups),'original_source_body_count':171,'new_premise_seeds':0}
