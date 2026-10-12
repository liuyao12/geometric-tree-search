"""SOURCE ONLY registration bridge, no loader/import/dispatch of scientific code.

All arguments come from a future reviewed, pinned, ROOT-owned worker. It must
bind the actual complete independent static pool result and resource lifetime.
This function rebuilds the immutable relation; it does not perform preparation
enumeration, point selection, Controller/Executor calls, search or native work.
The imported production modules are passed explicitly by that future caller.
"""
import copy
import json
import time


def fixed_pool_registration(graph, life, proposals, original, projection,
                            preparation_plan, preparation_plan_pin, evidence,
                            static_audit, static_lifetime, static_gate_pins):
    started=time.perf_counter();core=life.core
    def same(actual,expected,label):
        if core.canonical(actual)!=core.canonical(expected):raise ValueError(label)
    if (static_audit.get('status')!='passed_complete_independent_static_family_pool_audit'
            or static_lifetime.get('status')!='passed_owned_independent_static_family_pool_audit'
            or static_lifetime.get('child_reaped') is not True or static_lifetime.get('child_exit')!=0):
        raise ValueError('Actual separately pinned complete static audit and owned resource PASS required')
    # ROOT's successor plan must pin these three actual artifacts before loading
    # any model. No placeholder/prediction pin is an activation prerequisite.
    if set(static_gate_pins)!={'plan','result','lifetime'}:
        raise ValueError('all three exact static gate artifact pins required')
    for artifact in static_gate_pins.values():
        if (set(artifact)!={'path','sha256','bytes'} or not isinstance(artifact['path'],str)
                or not isinstance(artifact['sha256'],str) or len(artifact['sha256'])!=64
                or type(artifact['bytes']) is not int or artifact['bytes']<0):
            raise ValueError('literal complete non-placeholder static gate pin')
    same(static_audit['plan'],static_gate_pins['plan'],'exact independent result plan')
    same(static_lifetime['plan'],static_gate_pins['plan'],'exact independent lifetime plan')
    same(static_lifetime['result'],static_gate_pins['result'],'exact resource-credited independent result')
    if evidence['status']!='complete_declared_proposal_grammar_prepared_pending_independent_audit':
        raise ValueError('complete immutable prepared pool required')
    same(evidence['plan'],preparation_plan_pin,'exact original preparation plan')
    same(evidence['inputs'],preparation_plan['inputs'],'all original role bindings')
    same(evidence['sources'],preparation_plan['sources'],'all original preparation source bytes')
    if (len(original.bodies)!=171 or len(graph.recipes)!=229 or len(graph.formulas)!=217 or graph.height!=24
            or static_audit['source_body_count']!=171):
        raise ValueError('unchanged all-171 / 229 / 217 / 24 finite language required')
    same(evidence['unchanged_model_epoch'],graph.model_epoch,'exact primitive point epoch')
    same(evidence['formula_codes'],graph.formulas,'exact injective formula values')
    same(evidence['formula_registry_sha256'],graph.registry_sha,'exact formula registry')
    same(evidence['original_body_authority_epoch'],original.epoch,'unchanged conditional source relation')
    same(static_audit['original_body_authority_epoch'],original.epoch,'independent conditional source relation')
    original.check_graph(graph)
    records=proposals.interfaces(graph,original,projection,core)
    anchors=proposals.root_anchors(graph,core)
    same(anchors,evidence['root_anchors'],'original seed insertion order and full identities')
    same(anchors,static_audit['root_anchors'],'independent exact root anchors')
    same(core.digest(records),static_audit['declared_interface_projection_sha256'],
         'independently rebuilt complete declared-conclusion interface relation')
    saved=evidence['groups'];checked=static_audit['groups_checked']
    if len(saved)!=len(checked) or len(saved)!=5:
        raise ValueError('entire exact five-group pool, never a selected subset')
    specs=[];priorities=[]
    for index,(descriptor,receipt) in enumerate(zip(saved,checked)):
        core.integer(descriptor['pool_index']);core.integer(descriptor['fixed_priority'])
        same(descriptor['pool_index'],index,'exact registry index order')
        same(receipt['pool_index'],index,'independently audited group order')
        same(core.digest(descriptor),receipt['descriptor_sha256'],'independently reconstructed full group payload')
        same(descriptor['descriptor_id'],receipt['descriptor_id'],'exact whole-union descriptor identity')
        same(descriptor['fixed_priority'],receipt['fixed_priority'],'unchanged independently audited priority')
        same(descriptor['distinct_member_count'],receipt['distinct_members'],'deduplicated physical members')
        same(descriptor['component_member_occurrences'],receipt['occurrence_members'],'every source occurrence')
        same(descriptor['shared_member_count'],receipt['shared_members'],'full-key physical sharing')
        specs.append(core.canonical(descriptor['binding_specification']));priorities.append(descriptor['fixed_priority'])
    sources=[copy.deepcopy(preparation_plan_pin)]+[
        {k:item[k] for k in ('path','sha256','bytes')} for item in preparation_plan['sources']]
    authority=proposals.GroupAuthority(original.graph_text,'',original,life,core.canonical(records),
        core.canonical(anchors),tuple(specs),tuple(priorities),core.canonical(sources))
    authority=proposals.GroupAuthority(authority.graph_text,core.digest(authority.epoch_payload()),original,life,
        authority.interface_text,authority.anchor_text,authority.spec_texts,authority.fixed_priorities,authority.source_text)
    same(authority.epoch,evidence['group_authority_epoch'],'exact registered body/priority union epoch')
    same(authority.epoch,static_audit['full_group_authority_epoch'],'independently checked whole-pool epoch')
    groups=[]
    for index,descriptor in enumerate(saved):
        expected=authority.expected(graph,index,priorities[index])
        same(expected,descriptor,'source-authorized complete canonical transport and marking union')
        authority.compile(graph,expected)
        groups.append(expected)
    if any(evidence.get(field)!=0 for field in ('target_searches','point_certificates','native_queries')):
        raise ValueError('prepared proposals cannot import proof/native acceptance')
    return authority,groups,dict(registration_seconds=time.perf_counter()-started,
        immutable_descriptor_count=5,conditional_source_family_count=171,
        static_gate_pins=copy.deepcopy(static_gate_pins),group_authority_epoch=authority.epoch,
        authored_words_used_as_hints=0,new_premise_seeds=0,new_RL_training=False,
        scope='All fixed source-body union proposals registered; pending members remain structural obligations, not newly proved premises')
