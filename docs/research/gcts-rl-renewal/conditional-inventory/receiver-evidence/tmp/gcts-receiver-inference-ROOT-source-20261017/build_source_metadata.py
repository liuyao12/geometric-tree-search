"""Source/AST and saved-data metadata only; never evaluates project code."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

S = Path('/private/tmp/gcts-receiver-inference-ROOT-source-20261017')
PARENT = Path('/private/tmp/gcts-native-productive-inventory-work4m-ROOT-source-20261017')
VERSION = 'ROOT-receiver-inference-probe-cold-v1'
SCOPE = 'ROOT-receiver-inference-probe-Source'


def ref(p):
    b=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}


def literal(raw,name):
    tree=ast.parse(raw)
    n=next(n for n in tree.body if isinstance(n,ast.Assign)
           and any(isinstance(x,ast.Name) and x.id==name for x in n.targets))
    return ast.literal_eval(n.value)


def replace_literal(raw,name,value):
    tree=ast.parse(raw)
    n=next(n for n in tree.body if isinstance(n,ast.Assign)
           and any(isinstance(x,ast.Name) and x.id==name for x in n.targets))
    lines=raw.splitlines(keepends=True)
    return ''.join(lines[:n.lineno-1])+name+'='+repr(value)+'\n'+''.join(lines[n.end_lineno:])


def save(name,data):
    p=S/name
    raw=(json.dumps(data,indent=2,sort_keys=True)+'\n').encode()
    assert not p.exists(),p
    p.write_bytes(raw)
    return ref(p)


def new_source(name,raw,parent_raw=None):
    p=S/name;assert not p.exists(),p
    compile(raw,str(p),'exec',dont_inherit=True)
    p.write_text(raw)
    if parent_raw is not None:
        f=''.join(difflib.unified_diff(parent_raw.splitlines(keepends=True),raw.splitlines(keepends=True),fromfile='a/source.py',tofile='b/source.py'))
        i=''.join(difflib.unified_diff(raw.splitlines(keepends=True),parent_raw.splitlines(keepends=True),fromfile='a/source.py',tofile='b/source.py'))
        (S/(name+'.forward.patch')).write_text(f)
        (S/(name+'.inverse.patch')).write_text(i)
    return ref(p)


def main():
    parent_path=PARENT/'native_productive_inventory_cold_v2.py'
    parent=parent_path.read_text();raw=parent
    fixed=literal(parent,'FIXED')
    for role in ('collector','composer','inventory_cases','miner'):fixed.pop(role)
    additions={
      'producer':'/private/tmp/gcts-observed-subset-expander-source-20261017/receptor_family_expander_v2.py',
      'degree_router':'/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-aware-router-engine-source-20261016/marked_degree_router_v1.py',
      'marked_aware_proposer':'/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-aware-fibre-proposer-source-20261016/marked_aware_nonimp_fibre_proposer_v1.py',
      'marked_aware_checker':'/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/unit-row-marked-aware-fibre-checker-source-20261016/independent_marked_aware_fibre_checker_v1.py',
      'family_engine':'/private/tmp/gcts-family-census-engine-source-20261017/receptor_family_search_engine_v5.py',
      'family_consumer':'/private/tmp/gcts-current-source-pool-20261017/receptor_family_preference_consumer_v2.py',
      'receiver_provider':'/private/tmp/gcts-observed-receptor-provider-source-20261017/receptor_transfer_physical_provider_v6.py',
      'residual_policy':'/private/tmp/gcts-residual-binding-prefix-source-20261017/residual_binding_prefix_v2.py',
      'receiver_cases':str(S/'receiver_inference_cases_v1.py')}
    for role,path in additions.items():fixed[role]=ref(Path(path))
    fixed=dict(sorted(fixed.items()))
    inputs=literal(parent,'FIXED_INPUTS')
    inputs['frozen_inventory']=ref(Path('/private/tmp/gcts-native-productive-inventory-work4m-ROOT-20261017/ROOT-expanded-result-v1.json'))
    inputs['inventory_acceptance']=ref(Path('/private/tmp/gcts-native-productive-inventory-work4m-ROOT-20261017/ROOT-source-ground-acceptance-v1.json'))
    raw=replace_literal(raw,'VERSION',VERSION)
    raw=replace_literal(raw,'SCOPE',SCOPE)
    raw=replace_literal(raw,'FIXED',fixed)
    raw=replace_literal(raw,'FIXED_INPUTS',inputs)
    raw=replace_literal(raw,'QUALIFICATION_CASES_BY_PURPOSE',{
        'receptor-inference-visible-probe':['RI-01-visible-observed-port-inference'],
        'receptor-inference-literal-probe':['RI-02-literal-origin-binding-control']})
    raw=raw.replace("contract['schema']=='ROOT-native-productive-inventory-cold-Source-contract-v1'", "contract['schema']=='ROOT-receiver-inference-probe-Source-contract-v1'")
    old_labels="('BEFORE_PLAN_READ', 'BEFORE_CURRENT_SOURCE_READS', 'BEFORE_AUTHORITY_INPUT_READS', 'BEFORE_MODULE_LOAD', 'BEFORE_GUARD_CONSTRUCTION', 'BEFORE_STAGEB_PROVENANCE', 'BEFORE_MARKING_CHECK', 'BEFORE_COMPOSER', 'AFTER_COMPOSER', 'AFTER_DAG', 'AFTER_MINER', 'AFTER_QUALIFICATION', 'BEFORE_OUTPUT')"
    labels=('BEFORE_PLAN_READ','BEFORE_CURRENT_SOURCE_READS','BEFORE_AUTHORITY_INPUT_READS',
            'BEFORE_MODULE_LOAD','BEFORE_GUARD_CONSTRUCTION','BEFORE_STAGEB_PROVENANCE',
            'BEFORE_MARKING_CHECK','BEFORE_POOL_READ','BEFORE_ENGINE','BEFORE_PROVIDER',
            'AFTER_PROVIDER','AFTER_ENGINE','BEFORE_OUTPUT')
    assert raw.count(old_labels)==1
    raw=raw.replace(old_labels,repr(labels))
    start=raw.index('    def run_inventory():\n')
    end=raw.index('    diagnostic_context_raw=',start)
    section='''    phase('BEFORE_POOL_READ')
    frozen = decode(inputs_raw['frozen_inventory'])
    accepted_inventory = decode(inputs_raw['inventory_acceptance'])
    need(frozen['schema']=='ROOT-native-conditional-inventory-result-v1'
         and frozen['language_binding']==ORIGINAL_BINDING
         and frozen['conditional_inventory']['original_model_binding']==ORIGINAL_BINDING
         and frozen['conditional_inventory']['original_model_sources']==ORIGINAL_SOURCES
         and frozen['conditional_inventory']['original_model_inputs']==ORIGINAL_INPUTS
         and canonical(frozen['conditional_inventory']['marking'])==canonical(marking)
         and accepted_inventory['schema']=='ROOT-native-productive-source-ground-inventory-acceptance-v1'
         and accepted_inventory['expanded']==FIXED_INPUTS['frozen_inventory']
         and accepted_inventory['source_ground_inventory_qualified'] is True
         and accepted_inventory['native_resources_qualified'] is True
         and accepted_inventory['descriptors_qualified']==4,
         'same frozen qualified inventory and original model; prior receipts are data only')
    old_inventory_contract=decode(read_pinned(accepted_inventory['source_contract']))
    need(old_inventory_contract['sources']==frozen['sources']
         and old_inventory_contract['inputs']==frozen['inputs']
         and old_inventory_contract['original_model_sources']==ORIGINAL_SOURCES
         and old_inventory_contract['original_model_binding']==ORIGINAL_BINDING,
         'complete frozen original-model/current-Source contract joins')
    inventory_data=frozen['conditional_inventory']['inventory']
    prior_records=[]
    for pool in inventory_data['minings']:
        need(pool['status']=='PROPOSALS' and pool['mining']['status']=='PROPOSALS',
             'complete frozen extraction data')
        for record_index,record in enumerate(pool['mining']['families']):
            entries=[e for e in inventory_data['qualified_records']
                     if e['component_id']==pool['component_id'] and e['record_index']==record_index]
            need(len(entries)==1 and canonical(entries[0]['record'])==canonical(record)
                 and entries[0]['status']=='CHECKED_SOURCE_GROUND_CONDITIONAL_RECORD'
                 and entries[0]['adaptation']['status']=='READY_LOCAL_CLUSTER',
                 'every frozen mined record joined to its saved qualified occurrence')
            prior_records.append(record['family_id'])
    need(prior_records==accepted_inventory['family_ids']
         and len(prior_records)==accepted_inventory['descriptors_qualified'],
         'whole frozen library identity; fresh source/current checks still required')
    def run_receiver():
        language=fresh_language()
        marked=adapter.MarkedSemantics(language=language,base_semantics=semantics,
            decorator=decorator,verifier=verifier,marking=copy.deepcopy(marking),tick=tick)
        mode=('VISIBLE_RECEPTOR' if plan['purpose']=='receptor-inference-visible-probe' else 'LITERAL_GROUND')
        return modules['receiver_cases'].run_receiver(language=language,
            base_semantics=semantics,marked_semantics=marked,modules=modules,
            frozen_inventory=copy.deepcopy(inventory_data),matching_mode=mode,
            tick=tick,phase=phase)
'''
    raw=raw[:start]+section+raw[end:]
    raw=raw.replace('inventory=call(run_inventory)','receiver=call(run_receiver)')
    start=raw.index("    need(inventory['schema']==")
    end=raw.index('    result_raw=',start)
    raw=raw[:start]+'''    need(receiver['schema']=='ROOT-receiver-inference-evidence-v1'
         and receiver['status']=='RECEIVER_PROBE_RECORDED',
         'whole returned actual receiver probe; no theorem or broad engine authority')
    phase('BEFORE_OUTPUT')
    payload={'schema':'ROOT-receptor-inference-probe-payload-v1','receiver':receiver,
        'original_model_sources':ORIGINAL_SOURCES,'original_model_inputs':ORIGINAL_INPUTS,
        'original_model_binding':ORIGINAL_BINDING,'marking':marking,'definition_check':definition_check,
        'frozen_inventory_input':FIXED_INPUTS['frozen_inventory'],
        'inventory_acceptance_input':FIXED_INPUTS['inventory_acceptance'],
        'inventory_reused':True,'construction_in_this_window':False,
        'actual_engine_called':True,
        'new_theorem_discovered':False,'logical_proof_accepted':False,
        'engine_activated':False,'family_library_activated':False,'whole_engine_qualified':False,
        'scheduler_or_rollback_accepted':False,'complete_GCTS_model_accepted':False,
        'RL_accepted':False,'GCTS_advantage_claimed':False,'ROOT_resource_accepted':False}
'''+raw[end:]
    raw=raw.replace("'conditional_inventory':payload","'receiver_probe':payload")
    raw=raw.replace('ROOT-native-conditional-inventory-result-v1','ROOT-receptor-inference-probe-result-v1')
    # The frozen input retains its original schema; only current output changes.
    raw=raw.replace("need(frozen['schema']=='ROOT-receptor-inference-probe-result-v1'", "need(frozen['schema']=='ROOT-native-conditional-inventory-result-v1'")
    for name in ('diagnostic-context','response-body','final-observation'):
        raw=raw.replace('ROOT-native-'+('inventory' if name=='diagnostic-context' else 'conditional-inventory')+'-'+name+'-v1','ROOT-receptor-inference-probe-'+name+'-v1')
    source=new_source('receiver_inference_cold_v1.py',raw,parent)
    sources={'intake':source,**fixed}
    contract={'schema':'ROOT-receiver-inference-probe-Source-contract-v1',
        'scope':SCOPE,'source_only':True,'author_identity':'/root',
        'sources':sources,'inputs':inputs,'limits':literal(parent,'LIMITS'),
        'original_model_sources':literal(parent,'ORIGINAL_SOURCES'),
        'original_model_inputs':literal(parent,'ORIGINAL_INPUTS'),
        'original_model_binding':literal(parent,'ORIGINAL_BINDING'),
        'parent_source':ref(parent_path),'phase_sites':list(labels),
        'purpose':'Matched finite actual receiver probes using the same frozen prior-qualified open cluster pool as data, with fresh source/current native checks. No composer rerun and no cold speedup claim.',
        'allocation':{'rows':24,'maximum_nodes':2,'maximum_events':256,
            'branch_tie':'ASSIGNED-OUTPUT-THEN-ROW','pool_policy':'FIRST_QUALIFIED_OPEN_POOL_THEN_NATIVE_FALLBACK',
            'provider_limits':literal((S/'receiver_inference_cases_v1.py').read_text(),'PROVIDER_LIMITS')},
        'scientific_calls':0,'scientific_acceptance':False,'runtime_qualified':False,
        'native_policy':'Original20s launch-to-fresh-postprobe/512MiB, internal500MiB reserve, failure55/owned60/caller90+1; once wrapper unchanged. Fixed original17/input2 epoch; new executable set tracked separately.',
        'required_evidence':['Actual complete global decision before family provider; all24 original required rows and full fallback preserved.','Every public original/decorated preimage, including removed/no-offer proposals, checked in current owned ledger; seed frozen construction census explicitly.','Ordinary full expansion/4358/native4bd6; derivation obligations remain unproved.','One primitive per actual branch, then fresh global decision and exact owned rollback.','Shared pool/row prefix/caps; record denominators and failed checks. No completed theorem/useful transfer/speedup inferred from merely returned packet.']}
    cref=save('Source-contract-v1.json',contract)
    rp=PARENT/'ROOT_read_native_productive_inventory_saved_v2.py'
    rparent=rp.read_text();reader=rparent
    reader=replace_literal(reader,'CURRENT_CONTRACT',cref)
    reader=replace_literal(reader,'PHASES',labels)
    reader=reader.replace('ROOT-native-productive-inventory-cold-Source-contract-v1',contract['schema'])
    reader=reader.replace('ROOT-native-productive-inventory-cold-Source',SCOPE)
    reader=reader.replace('ROOT-native-productive-inventory-cold-v2-work4m',VERSION)
    for suffix in ('result','response-body','final-observation','diagnostic-context','disposition'):
        reader=reader.replace('ROOT-native-conditional-inventory-'+suffix+'-v1','ROOT-receptor-inference-probe-'+suffix+'-v1')
    reader=reader.replace('ROOT-native-inventory-diagnostic-context-v1','ROOT-receptor-inference-probe-diagnostic-context-v1')
    reader=reader.replace("payload=evidence['conditional_inventory'];pipeline=payload['inventory']", "payload=evidence['receiver_probe'];pipeline=payload['receiver']")
    reader=reader.replace('ROOT-native-conditional-inventory-payload-v1','ROOT-receptor-inference-probe-payload-v1')
    reader=reader.replace('ROOT-native-productive-conditional-inventory-evidence-v1','ROOT-receiver-inference-evidence-v1')
    reader=reader.replace("pipeline['status']in ('UNKNOWN','CHECKED_CONDITIONAL_INVENTORY')", "pipeline['status']=='RECEIVER_PROBE_RECORDED'")
    reader=reader.replace("pipeline['status']!='CHECKED_CONDITIONAL_INVENTORY'", "pipeline['status']!='RECEIVER_PROBE_RECORDED'")
    reader=reader.replace("pipeline['status']=='CHECKED_CONDITIONAL_INVENTORY'", "pipeline['status']=='RECEIVER_PROBE_RECORDED'")
    reader=reader.replace("[x['stage']for x in phases]==list(PHASES)",
        "[x['stage']for x in phases if x['stage'] not in ('BEFORE_PROVIDER','AFTER_PROVIDER')]==[x for x in PHASES if x not in ('BEFORE_PROVIDER','AFTER_PROVIDER')]")
    reader=reader.replace('conditional_inventory_record_complete','receiver_probe_record_complete')
    reader=reader.replace('all thirteen sites','all required sites; provider sites are conditional')
    readerref=new_source('ROOT_read_receiver_inference_saved_v1.py',reader,rparent)
    readercontract=save('reader-Source-contract-v1.json',{'schema':'ROOT-receiver-inference-saved-reader-Source-contract-v1',
        'source':readerref,'current_operative_contract':cref,'source_only':True,
        'scope':'Saved complete bytes, original once/native terminal/wire and resource reconciliation only. No scientific imports, replay, semantic proof or target/transfer acceptance.',
        'parent_source':ref(rp),'scientific_calls':0,'scientific_acceptance':False})
    handoff={'schema':'ROOT-receiver-inference-probe-Source-handoff-v1',
        'source':source,'sources':sources,'source_contract':cref,'reader':readerref,
        'reader_source_contract':readercontract,'source_only':True,'scientific_calls':0,
        'Review_ABI':{'schema':'ROOT-receiver-inference-probe-typed-Source-review-v1',
          'scope':SCOPE,'author_identity':'/root','source':source,'sources':sources,
          'source_contract':cref,'source_only':True,'scientific_calls':0,'scientific_acceptance':False},
        'required_reviews':'Distinct peer whole caller/case/reader and current provider/residual/engine Source before Root once actual. Existing producer fd3e peer e50e retained. No actual authorized by this metadata builder.'}
    save('handoff-v1.json',handoff)
    for name in ('ROOT_external_once_v1.py','Q_native_terminal_meter_v2.py'):
        data=(PARENT/name).read_bytes();p=S/name;assert not p.exists();p.write_bytes(data)
    print(json.dumps({'caller':source,'contract':cref,'reader':readerref,'scientific_calls':0}))


if __name__=='__main__':main()
