"""Metadata/AST composition only; never evaluates component or model Source."""
import ast,difflib,hashlib,json
from pathlib import Path
ROOT=Path('/Users/liuyao/Documents/Codex/projects/geometric-tree-search');BASE=ROOT/'.gcts-active'
HERE=Path(__file__).resolve().parent;DEST=BASE/'receptor-family-bridge-cold-ROOT-source-20261016'
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,value):
    p=DEST/name
    with p.open('x')as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
    return pin(p)
def main():
    DEST.mkdir()
    parent_folder=BASE/'unit-row-fresh-projection-qualification-cold-source-20261016'
    pc=read(parent_folder/'Source-contract-v1.json');parent=Path(pc['source']['path'])if'source'in pc else Path(pc['sources']['intake']['path'])
    raw=parent.read_bytes();assert hashlib.sha256(raw).hexdigest()=='007b29ef99c45d5d94cb29ff7a3b9659e3584164b9da825362e1b6ceacc262bb'
    text=raw.decode();tree=ast.parse(raw);lines=text.splitlines(keepends=True)
    module_contracts={
      'family_expander':BASE/'receptor-family-expander-source-20261016/Source-contract-v1.json',
      'family_checker':BASE/'receptor-family-expansion-checker-source-20261016/Source-contract-v1.json',
      'family_adapter':BASE/'receptor-family-six-rule-adapter-source-20261016/Source-contract-v3.json',
      'component_cases':BASE/'receptor-family-bridge-controls-ROOT-source-20261016/Source-contract-v1.json'}
    fixed={k:v for k,v in pc['sources'].items()if k!='intake'}
    for role,path in module_contracts.items():fixed[role]=read(path)['source']
    inputs=dict(pc['inputs']);inputs['family_descriptor']=pin(BASE/'receptor-lemma-family-design-source-20261016/human-two-mp-family-v1.json')
    cases=read(module_contracts['component_cases'])['expected_cases'];purpose='receptor-family-primitive-bridge-component-controls'
    replacements={'VERSION':'ROOT-receptor-family-bridge-cold-v1','SCOPE':'ROOT-receptor-family-bridge-cold-Source',
      'FIXED':fixed,'FIXED_INPUTS':inputs,'QUALIFICATION_CASES_BY_PURPOSE':{purpose:cases}}
    edits=[]
    for node in tree.body:
        if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)and node.targets[0].id in replacements:
            key=node.targets[0].id;start=sum(len(x)for x in lines[:node.lineno-1]);end=sum(len(x)for x in lines[:node.end_lineno])
            edits.append((start,end,key+'='+repr(replacements[key])+'\n'))
    for start,end,new in reversed(edits):text=text[:start]+new+text[end:]
    for a,b in [("contract['schema']=='unit-row-fresh-projection-qualification-cold-Source-contract-v1'","contract['schema']=='ROOT-receptor-family-bridge-cold-Source-contract-v1'"),
      ("review['author_identity']=='/root/hilbert_advice_controls'","review['author_identity']=='/root'"),
      ("review['reviewer_identity'] not in ('/root/hilbert_advice_controls','/root')","review['reviewer_identity'] != '/root'"),
      ('exact current executable Source14 and saved input8','exact current executable Source18 and saved input9')]:
        assert text.count(a)==1;text=text.replace(a,b)
    anchor='    controls, families = [], {}\n';assert text.count(anchor)==1
    prefix=text[:text.index(anchor)]
    body='''    def run_component():
        language=fresh_language()
        marked=adapter.MarkedSemantics(language=language,base_semantics=semantics,
            decorator=decorator,verifier=verifier,marking=copy.deepcopy(marking),tick=tick)
        state=marked.initial_state(language,tick)
        return modules['component_cases'].run_component_cases(
            producer=modules['family_expander'],checker=modules['family_checker'],
            host_adapter=modules['family_adapter'],language=language,base_semantics=semantics,
            marked_semantics=marked,state=state,human_descriptor=decode(inputs_raw['family_descriptor']),tick=tick)
    component=call(run_component)
    expected_controls=QUALIFICATION_CASES_BY_PURPOSE[plan['purpose']]
    need(component['schema']=='ROOT-receptor-family-component-cases-v1'
         and component['all_controls_completed'] is True
         and [c['case']for c in component['controls']]==expected_controls
         and len(component['controls'])==12 and all(c['status']=='PASSED'for c in component['controls'])
         and all(component[k]is False for k in ('proof_accepted','engine_activated','library_activated',
              'RL_accepted','GCTS_advantage_claimed')),'every frozen component assertion, no skip/substitution')
    payload={'schema':'ROOT-receptor-family-bridge-component-payload-v1','component':component,
        'control_count':12,'expected_cases':expected_controls,'all_controls_completed':True,
        'original_model_sources':ORIGINAL_SOURCES,'original_model_inputs':ORIGINAL_INPUTS,
        'original_model_binding':ORIGINAL_BINDING,'marking':marking,'definition_check':definition_check,
        'synthetic_syntax_hosts_not_native_authority':True,
        'current_engine_qualification_unchanged':True,'original_qualified_case_count':8,
        'original_required_case_count':12,'five_positive_adapter_rules':['axiom','instantiate','eq_subst','mp','generalize'],
        'original_empty_Gamma_positive_assumption_unavailable':True,
        'target_search_performed':False,'logical_proof_accepted':False,'engine_activated':False,
        'family_library_activated':False,'complete_GCTS_model_accepted':False,
        'scheduler_or_rollback_accepted':False,'RL_accepted':False,'GCTS_advantage_claimed':False,
        'ROOT_resource_accepted':False}
    result_raw=canonical({'schema':'ROOT-receptor-family-bridge-component-result-v1',
        'purpose':plan['purpose'],'sources':plan['sources'],'inputs':plan['inputs'],
        'language_binding':ORIGINAL_BINDING,'family_bridge_component':payload,
        'logical_proof_accepted':False,'ROOT_resource_accepted':False})+b'\\n'
    result_raw=call(encode_result_transport,(result_raw,))
    run=Path(plan['output_directory']);need(run.is_absolute()and run==run.resolve()and not run.exists(),
        'fresh canonical owned component output')
    run.mkdir(mode=0o700);result_pin=call(write_new,(run/'engine-result.json',result_raw))
    body={'schema':'ROOT-receptor-family-bridge-component-response-body-v1','version':VERSION,
        'status':'COMPLETE_WORKER_PENDING_EXTERNAL','invocation_id':plan['invocation_id'],'plan':raw_pin(plan_raw),
        'sources':plan['sources'],'inputs':plan['inputs'],'language_binding':ORIGINAL_BINDING,
        'original_model_binding':ORIGINAL_BINDING,'outputs':[result_pin],
        'joint_began_ns':EARLY_G,'joint_deadline_ns':end,'CLOCK_DOMAIN':CLOCK_DOMAIN,
        'limits':LIMITS,'resource_rule':plan['resource_rule'],'ROOT_resource_accepted':False,
        'logical_proof_accepted':False,'complete_GCTS_model_accepted':False,
        'failure_marking_activated':False,'family_library_activated':False,'engine_activated':False,
        'RL_accepted':False,'GCTS_advantage_claimed':False}
    body_raw=canonical(body)+b'\\n';completion={'schema':'Q-clean-verifier-response-completion-v1',
        'body_sha256':hashlib.sha256(body_raw).hexdigest(),'body_bytes':len(body_raw),
        'exit_zero_and_coordinator_deadline_required':True}
    response_pin=call(write_new,(run/'response.jsonl',body_raw+canonical(completion)+b'\\n'))
    need(sorted(p.name for p in run.iterdir())==['engine-result.json','response.jsonl'],'whole component output2')
    final_raw=canonical({'schema':'ROOT-receptor-family-bridge-component-final-observation-v1',
        'outputs':[result_pin,response_pin],'response':response_pin,'pending_external':True,
        'logical_proof_accepted':False,'ROOT_resource_accepted':False})+b'\\n'
'''
    suffix=raw[raw.index(b'    boundary();offset=0\n'):].decode()
    text=prefix+body+suffix;p=DEST/'ROOT_receptor_family_bridge_cold_v1.py'
    with p.open('x')as f:f.write(text)
    current=p.read_bytes();compile(ast.parse(current),str(p),'exec')
    oldt,newt=ast.parse(raw),ast.parse(current)
    segment=lambda b,n:b''.join(b.splitlines(keepends=True)[n.lineno-1:n.end_lineno])
    oldf={n.name:n for n in oldt.body if isinstance(n,ast.FunctionDef)};newf={n.name:n for n in newt.body if isinstance(n,ast.FunctionDef)}
    assert set(oldf)==set(newf)and len(oldf)==18
    for name in set(oldf)-{'main'}:assert segment(raw,oldf[name])==segment(current,newf[name])
    for cls in[n for n in oldt.body if isinstance(n,ast.ClassDef)]:
        new=next(n for n in newt.body if isinstance(n,ast.ClassDef)and n.name==cls.name);assert segment(raw,cls)==segment(current,new)
    assert current[current.index(b'    boundary();offset=0\n'):]==raw[raw.index(b'    boundary();offset=0\n'):]
    sources=dict(fixed,intake=pin(p));assert len(sources)==18 and len(inputs)==9
    forward=''.join(difflib.unified_diff(raw.decode().splitlines(keepends=True),text.splitlines(keepends=True),fromfile=str(parent),tofile=str(p)))
    inverse=''.join(difflib.unified_diff(text.splitlines(keepends=True),raw.decode().splitlines(keepends=True),fromfile=str(p),tofile=str(parent)))
    for name,value in [('parent-to-current-forward.patch',forward),('current-to-parent-full-inverse.patch',inverse)]:
        with(DEST/name).open('x')as f:f.write(value)
    delta=save('Source-delta-v1.json',dict(schema='ROOT-family-component-caller-Source-delta-v1',parent=pin(parent),source=pin(p),parent_source_contract=pin(parent_folder/'Source-contract-v1.json'),
      patches=[pin(DEST/'parent-to-current-forward.patch'),pin(DEST/'current-to-parent-full-inverse.patch')],top17_helpers_and2classes_raw_exact=True,native_final_exit_and_failure_suffix_raw_exact=True,Source18_input9_original17_input2_distinct=True,scientific_calls=0,
      changed_scope='OwnIDs and Source/input maps; one component purpose/12cases; callerRoot author; discard old6 family handlers/unused fixture helpers; new guarded component suite and unique result/wire schemas. Original native/Source/StageB authentication prefix and17tophelpers/2classes retained; no old control rerun or engine state/search call.'))
    contract=dict(schema='ROOT-receptor-family-bridge-cold-Source-contract-v1',scope='ROOT-receptor-family-bridge-cold-Source',author_identity='/root',source=pin(p),sources=sources,inputs=inputs,
      original_model_sources=pc['original_model_sources'],original_model_inputs=pc['original_model_inputs'],original_model_binding=pc['original_model_binding'],limits=pc['limits'],
      component_contracts={k:pin(v)for k,v in module_contracts.items()},unchanged_component_contract=pc['component_source_contract'],unchanged_component_reviews=pc['component_reviews'],
      implementation_choice=pin(HERE/'ROOT-implementation-choice-v1.json'),case_plan=pin(HERE/'ROOT-component-case-plan-v1.json'),parent_source=pin(parent),source_delta=delta,
      expected_cases=cases,purpose=purpose,scientific_calls=0,scientific_acceptance=False,source_only=True,
      artifact_API=dict(result_schema='ROOT-receptor-family-bridge-component-result-v1',payload_field='family_bridge_component',payload_schema='ROOT-receptor-family-bridge-component-payload-v1',response_schema='ROOT-receptor-family-bridge-component-response-body-v1',final_schema='ROOT-receptor-family-bridge-component-final-observation-v1',output_files=['engine-result.json','response.jsonl'],transport='unchanged bounded whole canonical JSON+LF/zlib6/base64 envelope; no trimming'),
      qualification='Only prospective12 compiler/checker/current point-adapter component cases. Even a full pass is no currentengine promotion, new theorem, library/RL activation, genericGCTS conformance or advantage. Original8/12 remains separate. Synthetic host tests are syntax-only; native host originalGamma/theory/profile/epoch stays unchanged.',
      Review_ABI=dict(schema='ROOT-receptor-family-bridge-cold-typed-Source-review-v1',scope='ROOT-receptor-family-bridge-cold-Source',author_identity='/root',source=pin(p),sources=sources,source_contract='Exact current caller contract capsule',source_only=True,scientific_calls=0,scientific_acceptance=False),
      remaining_gates=['Root author whole caller review plus genuine distinct caller and cases Source reviews; current component review cycle/composition audit.','Separate at-most-one Root plan/grant under unchanged once/meter2/CodeSeal/native limits. No actual authorized by Source packet.','Whole native/wire/saved closure before any component acceptance; all originalengine/theorem/RL/advantage flags false.'])
    cr=save('Source-contract-v1.json',contract)
    h=save('handoff-v1.json',dict(schema='ROOT-receptor-family-bridge-cold-handoff-v1',source=pin(p),source_contract=cr,source_delta=delta,source_only=True,scientific_calls=0,actual_execution_authorized=False))
    print(json.dumps(h))
if __name__=='__main__':main()
