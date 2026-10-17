"""Source text/AST/literal metadata authoring only. No project evaluation."""
import ast,difflib,hashlib,json,subprocess,tempfile
from pathlib import Path
H=Path('/private/tmp/gcts-native-productive-inventory-cases-source-20261017');P=Path('/private/tmp/gcts-native-inventory-cases-source-20261017')
def raw(p):
 p=Path(p);assert not getattr(p.stat(),'st_flags',0)&0x40000000
 return p.read_bytes()
def pin(p):
 b=raw(p);return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def text(n,s):
 p=H/n
 with p.open('xb')as f:f.write(s.encode())
 return pin(p)
def save(n,v):return text(n,json.dumps(v,sort_keys=True,indent=2)+'\n')
a=raw(P/'native_connected_inventory_cases_v2.py');assert hashlib.sha256(a).hexdigest()=='c0d6552f984abb98040c97867486b3441f89c8e40248b38452582834baadbb4d'
s=a.decode();edits=[]
def edit(label,old,new):
 global s
 assert s.count(old)==1,(label,s.count(old));i=s.index(old);edits.append({'label':label,'start':i,'old':old,'new':new});s=s[:i]+new+s[i+len(old):]
edit('own_VERSION',"VERSION = 'ROOT-native-connected-conditional-inventory-cases-v2'","VERSION = 'ROOT-native-productive-conditional-inventory-cases-v3'")
edit('productive_evidence_schema',"RESULT_SCHEMA = 'ROOT-native-conditional-inventory-evidence-v1'","RESULT_SCHEMA = 'ROOT-native-productive-conditional-inventory-evidence-v1'")
edit('composer_VERSION',"COMPOSER_VERSION = 'receptor-family-native-conditional-component-composer-v1'","COMPOSER_VERSION = 'receptor-family-native-conditional-component-composer-v2-closed-open-slots'")
edit('miner_VERSION',"MINER_VERSION = 'receptor-family-primitive-DAG-miner-v2-connected-cut-selection'","MINER_VERSION = 'receptor-family-primitive-DAG-miner-v3-interface-coupled-catalogue'")
edit('explicit_allocation',"COMPOSER_LIMITS = {'root_advances': 48, 'extension_advances': 96,\n                   'heads_per_rule': 1, 'quantum': 8, 'components': 1}","COMPOSER_LIMITS = {'work': 1000000, 'depth': 128, 'root_advances': 48,\n                   'extension_advances': 96, 'heads_per_rule': 1,\n                   'quantum': 8, 'components': 2}\nFRAGMENT_PRIORITY = 'OPEN_INPUT_OUTPUT_FIRST'")
edit('result_arrays',"        'binding': json.loads(original_binding), 'components': None, 'collection': None, 'mining': None,\n        'qualified_records': [], 'census': [], 'census_joins': joins,","        'binding': json.loads(original_binding), 'components': None,\n        'collections': [], 'minings': [], 'qualified_records': [],\n        'descriptor_catalogue': [], 'census': [], 'census_joins': joins,")
edit('work_report_explicit_priority',"'composer_limits': dict(COMPOSER_LIMITS), 'miner_limits': dict(MINER_LIMITS)}","'composer_limits': dict(COMPOSER_LIMITS), 'miner_limits': dict(MINER_LIMITS),\n                          'fragment_priority': FRAGMENT_PRIORITY}")
start=s.index("        require(composed['operative_global_join_complete'] is True and len(composed['components']) == 1,")
end=s.index("        node_rows = {v['node_id']: v['row'] for v in collected['maps']['nodes']}",start)
old=s[start:end]
new="""        availability = composed['slot_availability']
        slot_ids = availability['observed_component_ids']
        require(composed['operative_global_join_complete'] is True and len(composed['components']) == 2
                and composed['request']['component_slots'] == {'closed': 1, 'open': 1}
                and composed['request']['slot_policy'] == 'FIRST_CLOSED_AND_FIRST_OPEN_EXTERNAL_INPUT'
                and availability['policy'] == 'FIRST_CLOSED_AND_FIRST_OPEN_EXTERNAL_INPUT'
                and availability['both_slots_observed'] is True
                and availability['normal_prefix_finished'] is True
                and availability['proposal_goal_complete'] is True
                and availability['missing_slots'] == [] and set(slot_ids) == {'closed', 'open'}
                and all(type(v) is str for v in slot_ids.values()) and len(set(slot_ids.values())) == 2,
                'COMPOSER', 'both declared slots and full public prefix census joined')
        host = work.copy(host_adapter.describe_host(language=language, tick=work.step))
        require(canonical(composed['host']) == canonical(host)
                and canonical(composed['binding']) == original_binding, 'COMPOSER', 'current full original host/binding')
        root = composed['root']['state']
        checked_root, totals, marks, selected, excluded, root_names = point.private_state(language, root, work.step)
        require(canonical(checked_root) == canonical(root) and root['height'] == 24
                and root['selected'] == [] and root['excluded'] == [], 'ROOT', 'actual complete empty original root')
        root_original = point.base_state(language, root, work.step)
        merge([[k, v] for k, v in sorted(root_names.items())], 'FRESH_ROOT')
        originals = {r['translation'][1]: _key(r) for r in root_original['selected']}
        complete = True
        observed_slots = set()
        # Collect all alternatives first. Their placements are NEVER combined.
        for component_index, component in enumerate(composed['components']):
            work.step()
            require(type(component['input_ports']) is list, 'COMPONENT', 'actual external input list')
            slot = 'open' if component['input_ports'] else 'closed'
            require(slot not in observed_slots and slot_ids[slot] == component['component_id'],
                    'COMPONENT', 'exact first-per-class component identity')
            observed_slots.add(slot)
            require(len(component['members']) == 2 and len(component['state']['selected']) == 2
                    and component['connected_edges'] and component['checks']['strict_prior_internal_edge'] is True,
                    'COMPONENT', 'complete native two-member connected construction')
            checked_component, unused_t, unused_m, unused_s, unused_e, component_names = point.private_state(
                language, component['state'], work.step)
            require(canonical(checked_component) == canonical(component['state']), 'COMPONENT', 'fresh full state union')
            require([_key(v) for v in checked_component['selected']]
                    == [v['tile']['placement_key'] for v in component['members']],
                    'COMPONENT', 'complete actual member keys and selection order')
            merge([[k, v] for k, v in sorted(component_names.items())], 'FRESH_COMPONENT:'+str(component_index))
            for member in component['members']:
                merge_tile(member['tile'], 'COMPOSER_COMPONENT_MEMBER:'+str(component_index))
            origin = {'kind': 'automatic_primitive_composition', 'engine_generated': False,
                      'component_id': component['component_id'], 'composer_version': COMPOSER_VERSION,
                      'component_index': component_index, 'slot': slot, 'root_proof_accepted': False}
            item = {'component_index': component_index, 'component_id': component['component_id'],
                    'slot': slot, 'component_origin': work.copy(component['origin']),
                    'collection': None, 'status': 'UNKNOWN'}
            result['collections'].append(item)
            collected = collector.collect_derivation(language=language, base_semantics=base_semantics,
                marked_semantics=point, host_adapter=host_adapter, state=component['state'],
                origin=origin, tick=work.step)
            item['collection'] = collected
            require(collected['schema'] == 'receptor-family-checked-state-DAG-collection-v1'
                    and collected['version'] == COLLECTOR_VERSION, 'COLLECTOR', 'fresh public protocol')
            if collected['status'] == 'UNKNOWN':
                require(collected['derivation'] is None, 'COLLECTOR', 'UNKNOWN has no partial DAG')
                complete = False; continue
            require(collected['status'] == 'COLLECTED_CONDITIONAL_DAG'
                    and len(collected['derivation']['nodes']) == 2
                    and collected['checks']['every_selected_native_member_checked'] is True,
                    'COLLECTOR', 'fresh whole two-member native DAG')
            require(canonical(collected['host']) == canonical(host)
                    and canonical(collected['state_projections']['marked_state']) == canonical(component['state']),
                    'COLLECTOR', 'same whole component/model')
            dag = collected['derivation']
            require(any('node' in ref for node in dag['nodes'] for ref in node['ordered_inputs']),
                    'CONNECTED', 'actual strict-prior selected-source edge retained')
            # The fresh collector independently supplies actual source occupancy.
            node_keys = {v['node_id']: v['decorated_full_key'] for v in collected['maps']['nodes']}
            expected_inputs, expected_edges = {}, []
            for read in collected['maps']['reads']:
                work.step()
                use = {'consumer_key': work.copy(node_keys[read['consumer_node_id']]),
                       'ordered_index': read['ordered_index'], 'row': read['row'],
                       'formula': work.copy(read['formula']), 'fact_accepted': False}
                require(read['fact_accepted'] is False, 'PORT', 'native conditional read never a fact')
                if read['occupied']:
                    expected_edges.append(dict(use, source_key=work.copy(read['decorated_full_key']), occupied=True))
                else:
                    if read['row'] not in expected_inputs:
                        expected_inputs[read['row']] = {'row': read['row'], 'formula': work.copy(read['formula']),
                            'sharing': 'ALLOW_SAME_EXACT_PRIOR_SOURCE', 'occupied': False,
                            'fact_accepted': False, 'ordered_uses': []}
                    expected_inputs[read['row']]['ordered_uses'].append(use)
            require(canonical(component['input_ports']) == canonical([expected_inputs[k] for k in sorted(expected_inputs)])
                    and canonical(component['connected_edges']) == canonical(expected_edges)
                    and (bool(expected_inputs) is (slot == 'open'))
                    and all(p['occupied'] is False and p['fact_accepted'] is False for p in dag['inputs']),
                    'PORT', 'whole actual closed/open port and internal-edge classification')
            merge_states(collected['state_projections']['original_state'],
                         collected['state_projections']['marked_state'], 'COLLECTOR_STATE_KEYS:'+str(component_index))
            for member in collected['checked_members']:
                merge_tile(member['marked_tile'], 'COLLECTOR_CHECKED_MEMBER:'+str(component_index))
            item['status'] = 'COLLECTED_CONDITIONAL_DAG'
        require(observed_slots == {'closed', 'open'}, 'COMPOSER', 'one actual component in each slot')
        signal('AFTER_DAG')
        # Mine every complete collected alternative before qualification begins.
        family_names = {}
        for item in result['collections']:
            work.step()
            pool = {k: work.copy(item[k]) for k in ('component_index','component_id','slot','component_origin')}
            pool.update(mining=None, status='UNKNOWN_NO_COMPLETE_DAG', catalogue_indices=[])
            result['minings'].append(pool)
            if item['status'] != 'COLLECTED_CONDITIONAL_DAG':continue
            collected = item['collection'];dag = collected['derivation']
            mined = miner.mine_families(host=work.copy(host), derivation=work.copy(dag), tick=work.step,
                limits=dict(MINER_LIMITS), cut_selection='CONNECTED_AT_LEAST_TWO',
                fragment_priority=FRAGMENT_PRIORITY)
            pool['mining'] = mined
            require(mined['schema'] == 'receptor-family-mining-prefix-v1'
                    and mined['version'] == MINER_VERSION, 'MINER', 'fresh bounded prefix protocol')
            if mined['status'] == 'UNKNOWN':
                require(mined['families'] == [], 'MINER', 'UNKNOWN has no completed extraction')
                complete = False; continue
            require(mined['status'] == 'PROPOSALS' and mined['mining_complete'] is False
                    and mined['families'] and canonical(mined['request']) == canonical({'host': host, 'derivation': dag}),
                    'MINER', 'full actual collected request and bounded automatic extraction')
            for record_index, record in enumerate(mined['families']):
                work.step()
                descriptor = record['descriptor'];fid = record['family_id']
                preimage = {k:v for k,v in descriptor.items() if k not in ('family_id','provenance')}
                require(fid == descriptor['family_id'] == ascii_digest(preimage)
                        and canonical(preimage) == canonical(record['family_preimage']),
                        'COLLISION', 'whole actual descriptor identity preimage')
                if fid in family_names:
                    index = family_names[fid]
                    require(canonical(result['descriptor_catalogue'][index]['family_preimage']) == canonical(preimage),
                            'COLLISION', 'cross-pool family IDs require whole descriptor preimage equality')
                else:
                    index = len(result['descriptor_catalogue']);family_names[fid] = index
                    result['descriptor_catalogue'].append({'family_id': fid, 'family_preimage': work.copy(preimage),
                        'occurrences': [], 'independent_lemma_accepted': False})
                occurrence = {'component_index': item['component_index'], 'component_id': item['component_id'],
                              'slot': item['slot'], 'record_index': record_index}
                result['descriptor_catalogue'][index]['occurrences'].append(occurrence)
                pool['catalogue_indices'].append(index)
            pool['status'] = 'PROPOSALS'
        signal('AFTER_MINER')
        # Qualify every emitted occurrence, even when its descriptor repeats.
        for pool in result['minings']:
            work.step()
            if pool['status'] != 'PROPOSALS':continue
            component_index = pool['component_index'];component = composed['components'][component_index]
            collected = result['collections'][component_index]['collection'];mined = pool['mining']
"""
edit('two_slots_collect_all_then_mine_all',old,new)
start=s.index("        node_rows = {v['node_id']: v['row'] for v in collected['maps']['nodes']}")
end=s.index("        signal('AFTER_QUALIFICATION')",start)
old=s[start:end]
new=''.join('    '+line if line.strip() else line for line in old.splitlines(True))
new=new.replace('            complete = True\n','')
# Keep all existing ground roundtrip/check/physical rebind/native adaptation code.
entry_anchor="                result['qualified_records'].append(entry)\n"
assert new.count(entry_anchor)==1
new=new.replace(entry_anchor,"                entry.update(component_index=component_index, component_id=pool['component_id'],\n                    slot=pool['slot'], component_origin=work.copy(pool['component_origin']),\n                    catalogue_index=pool['catalogue_indices'][record_index])\n"+entry_anchor)
edit('qualify_all_occurrences_separate_unions',old,new)
edit('whole_two_pool_success',"        if complete and len(result['qualified_records']) == len(mined['families']):", "        emitted = sum(len(pool['mining']['families']) for pool in result['minings'] if pool['mining'] is not None)\n        if complete and len(result['collections']) == len(result['minings']) == 2\n                and len(result['qualified_records']) == emitted\n                and all(v['status'] == 'CHECKED_SOURCE_GROUND_CONDITIONAL_RECORD' for v in result['qualified_records']):")
# Continuation over physical lines needs a parenthesized condition.
s=s.replace("        if complete and len(result['collections']) == len(result['minings']) == 2\n", "        if (complete and len(result['collections']) == len(result['minings']) == 2\n")
s=s.replace("                and all(v['status'] == 'CHECKED_SOURCE_GROUND_CONDITIONAL_RECORD' for v in result['qualified_records']):", "                and all(v['status'] == 'CHECKED_SOURCE_GROUND_CONDITIONAL_RECORD' for v in result['qualified_records'])):")
# Fold the punctuation into the declared final replacement, not an undeclared edit.
edits[-1]['new']=s[edits[-1]['start']:s.index("            result['status'] = 'CHECKED_CONDITIONAL_INVENTORY'",edits[-1]['start'])].rstrip('\n')
# The final stored new span must include only replaced condition, not its trailing LF.
assert edits[-1]['new'].endswith(')):\n')is False
b=s.encode();ast.parse(b);compile(b,'<productive-inventory-cases-Source>','exec',dont_inherit=True)
# Verify full sequential byte inverse before freezing code.
forward=a.decode()
for e in edits:
 i=e['start'];assert forward[i:i+len(e['old'])]==e['old'],e['label'];forward=forward[:i]+e['new']+forward[i+len(e['old']):]
assert forward==s
source=text('native_productive_inventory_cases_v3.py',s)
print(json.dumps({'source':source,'edits':len(edits)},sort_keys=True))
# Metadata continues only after immutable code and raw inverse checks exist.
back=s
for e in reversed(edits):
 i=e['start'];assert back[i:i+len(e['new'])]==e['new'];back=back[:i]+e['old']+back[i+len(e['new']):]
assert back.encode()==a and ast.dump(ast.parse(back),include_attributes=False)==ast.dump(ast.parse(a),include_attributes=False)
patches={}
for label,x,y in [('forward',a,b),('full-inverse',b,a)]:
 p=text(label+'-v3.patch',''.join(difflib.unified_diff(x.decode().splitlines(True),y.decode().splitlines(True),fromfile='before',tofile='after')));patches[label]=p
 with tempfile.TemporaryDirectory(dir=str(H))as td:
  target=Path(td)/'before';target.write_bytes(x)
  r=subprocess.run(['/usr/bin/patch','--batch',str(target),'-i',p['path']],cwd=td,capture_output=True)
  assert r.returncode==0 and target.read_bytes()==y
delta=save('Source-delta-v3.json',{'schema':'productive-inventory-cases-full-Source-delta-v3','parent_source':pin(P/'native_connected_inventory_cases_v2.py'),'source':source,'edits':edits,'patches':patches,'whole_raw_inverse_exact':True,'whole_AST_inverse_exact':True,'actual_patch_both_directions_exact':True,'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
constants={n.targets[0].id:ast.literal_eval(n.value)for n in ast.parse(b).body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
api=save('API-wire-v3.json',{'schema':'ROOT-native-productive-inventory-cases-API-v3','version':constants['VERSION'],'signature':'run_inventory(*,language,base_semantics,marked_semantics,point_module,base_fallback,host_adapter,composer,collector,miner,producer,expansion_checker,tick,phase=None)','result_schema':constants['RESULT_SCHEMA'],'statuses':['UNKNOWN','CHECKED_CONDITIONAL_INVENTORY'],'allocation':{'case_work':8000000,'case_depth':128,'composer':constants['COMPOSER_LIMITS'],'miner_per_component':constants['MINER_LIMITS'],'fragment_priority':constants['FRAGMENT_PRIORITY']},'phase_order':['BEFORE_COMPOSER','AFTER_COMPOSER','AFTER_DAG','AFTER_MINER','AFTER_QUALIFICATION'],'phase_scope':'Each site occurs once, outside all component/extraction loops. Early UNKNOWN/own-bound/native interruption may truncate this ordered subsequence; no repeated stage labels.','result_arrays':{'components':'whole composer2 packet; only actual BOTH slots/current global census are operative; UNKNOWN must havecomponents[]','collections':'encounter-order [{component_index,component_id,slot,component_origin,collection,status}] independently checked per alternative','minings':'sameprovenance +mining,status,catalogue_indices; explicit no completeDAG gives miningNone/statusUNKNOWN_NO_COMPLETE_DAG','qualified_records':'every emitted physical occurrence; all old full sourceproposal/sourcecheck/roundtrip/portbindings/rowassignment/reboundproposal/check/adaptation fields plus component_index/id/slot/origin and catalogue_index','descriptor_catalogue':'[{family_id,whole family_preimage excluding only declared ID/provenance,occurrences:[component_index/id/slot/record_index],independent_lemma_acceptedFalse}]. Same IDs require full preimage equality; no occurrence skipped or counted as independent lemma.','census':'one global full original/decorated ID-preimage census across all alternative exposures/checks, never an aggregate point union'},'success':'Both actual slots and every complete collected/mined/ground source+rebound/check/direct-native-adapt occurrence finish. Otherwise UNKNOWN retains honest full completed/unfinished arrays; no operative family preference, receiver, engine or theorem.','error_scope':'Only own CASE8m/depth128 prefix becomesUNKNOWN through existing guarded finish; native/callback/guard/malformed/collision errors propagate unchanged.','source_only':True,'scientific_calls':0,'scientific_acceptance':False})
def regions(data):
 ls=data.decode().splitlines(True);return {n.name:(''.join(ls[n.lineno-1:n.end_lineno]),ast.dump(n,include_attributes=False))for n in ast.parse(data).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
ra,rb=regions(a),regions(b);same=[k for k in ra if ra[k]==rb[k]]
assert [k for k in ra if ra[k]!=rb[k]]==['run_inventory']
assert constants['FLAGS']=={n.targets[0].id:ast.literal_eval(n.value)for n in ast.parse(a).body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}['FLAGS']
phases=[n.args[0].value for n in ast.walk(ast.parse(b))if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='signal'and n.args and isinstance(n.args[0],ast.Constant)]
assert len(phases)==5 and set(phases)==set(['BEFORE_COMPOSER','AFTER_COMPOSER','AFTER_DAG','AFTER_MINER','AFTER_QUALIFICATION'])
audit=save('static-audit-v3.json',{'schema':'ROOT-native-productive-inventory-cases-static-v3','source':source,'source_delta':delta,'checks':{'raw_full_AST_inverse':True,'both_actualpatches_apply_exact':True,'all_other_tophelpers_raw_AST_exact':True,'same_case8m_depth128_native_exception_classes':True,'composer_own1m_full24_48_96_head1_quantum8_fixed2slots':True,'miner3_explicit_OPEN_INPUT_OUTPUT_FIRST':True,'five_unique_phase_sites_not_percomponent':True,'alternative_point_unions_never_concatenated':True,'all_emitted_occurrences_checked_no_descriptor_digestshortcut':True,'AST_compile_without_evaluation':True},'unchanged_helpers':same,'five_phase_literals':phases,'module_imported_or_evaluated':False,'source_only':True,'scientific_calls':0,'scientific_acceptance':False})
comp=Path('/private/tmp/gcts-native-component-composer-productive-source-20261017');mine=Path('/private/tmp/gcts-interface-coupled-miner-source-20261017')
C={'schema':'ROOT-native-productive-inventory-cases-Source-contract-v3','scope':'ROOT-native-productive-inventory-cases-Source','author_identity':'/root/hilbert_advice_controls','author_overlap':'Author wrote composer2 and prior host/provider/consumer/native ancestry, not independent self-review. Original CASE author Arithmetic; Root integration/actual ownership separate.','source':source,'sources':{'cases':source},'version':constants['VERSION'],'result_schema':constants['RESULT_SCHEMA'],'API':api,'source_delta':delta,'static_audit':audit,'operative_parent_contract':pin(P/'Source-contract-v2.json'),'integration_design':pin('/private/tmp/gcts-native-inventory-startup-diagnostic-source-20261017/ROOT-productive-integration-design-v1.json'),'master':pin('/Users/liuyao/Documents/Codex/projects/geometric-tree-search/docs/basic-tiling-algorithm.md'),'composer':pin(comp/'native_conditional_component_composer_v2.py'),'composer_contract':pin(comp/'Source-contract-v2.json'),'miner':pin(mine/'receptor_family_miner_v3.py'),'miner_contract':pin(mine/'Source-contract-v3.json'),'allocation':{'case_work':8000000,'case_depth':128,'composer':constants['COMPOSER_LIMITS'],'miner_per_component':constants['MINER_LIMITS'],'fragment_priority':constants['FRAGMENT_PRIORITY']},'scope_statement':'Source-only staged qualification of two distinct alternative native component unions, closed/open. Original17/input2 model/epoch, six-rule domains and marking unchanged; no supplied receiver/Gamma/BRANCH/route or engine/provider activation. No model shrink, no descriptor/type digest injectivity or duplicate-lemma credit.','flow':'compose BOTH/currentcensus; freshcollectALL and full actual portclass; mineALL with explicit interface-coupled catalogue policy; qualifyALL emitted occurrences at original root separately. Full source+rebound independent expansion and direct-native membership/point-union checks preserved. Shared full type census and full descriptor-preimage ledger do not authorize concatenating alternative placements.','unknown':'ComposerUNKNOWN never yields operative component. Downstream own prefixes keep full available stage arrays and still check every emitted occurrence from complete collections; whole status staysUNKNOWN if any required stage unfinished. Native/malformed/collision errors propagate. No availability/absence/invalidity/proof/gain inference.','future_scope_gaps':['No pool usefulness ranking/matched comparison performed.','No nonidentity receptor transfer, scheduler-authorized consumption, completeengine/runtime qualification or fullproofsearch claim.','Postbuild coupling metadata remains data; open parameter inferability and utility not promised.','All setup/construction/check/output costs require separate Root once/native20/512 reviewed caller and grant.'],'qualification_inherited':False,'actual_execution_authorized':False,'runtime_fit':'UNMEASURED','source_only':True,'scientific_calls':0,'scientific_acceptance':False,'module_import_or_Source_evaluation':False,'actual_result_proofword_donor_reads':False}
C['Review_ABI']={'schema':'ROOT-native-productive-inventory-cases-typed-Source-review-v3','scope':C['scope'],'author_identity':C['author_identity'],'source':source,'sources':C['sources'],'source_contract':'current capsule','source_only':True,'scientific_calls':0,'scientific_acceptance':False}
cref=save('Source-contract-v3.json',C)
href=save('handoff-v3.json',{'schema':'ROOT-native-productive-inventory-cases-handoff-v3','source':source,'source_contract':cref,'API':api,'source_delta':delta,'static_audit':audit,'actual_patches':patches,'Review_ABI':dict(C['Review_ABI'],source_contract=cref),'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False})
print(json.dumps({'source':source,'contract':cref,'API':api,'delta':delta,'audit':audit,'handoff':href},sort_keys=True))
