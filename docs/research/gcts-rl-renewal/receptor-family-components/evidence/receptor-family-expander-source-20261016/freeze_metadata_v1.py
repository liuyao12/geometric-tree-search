"""Raw/AST metadata authoring only. Never imports or evaluates the expander."""
import ast,difflib,hashlib,json
from pathlib import Path
ROOT=Path.cwd();D=ROOT/'.gcts-active/receptor-family-expander-source-20261016'
P=D/'receptor_family_expander_v1.py';raw=P.read_bytes();tree=ast.parse(raw);compile(raw,str(P),'exec')
assert hashlib.sha256(raw).hexdigest()=='f32e069a65ba21903cb6211772334e5b36ea8598bd189ca06800a8d9030d12a2'
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p.resolve()),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(name,obj):
 p=D/name
 with p.open('xb') as f:f.write((json.dumps(obj,indent=2,sort_keys=True)+'\n').encode())
 return pin(p)
source=pin(P);api=pin(D/'API-wire-v1.json')
refs={k:pin(ROOT/p) for k,p in {
 'master':'docs/basic-tiling-algorithm.md',
 'design_contract':'.gcts-active/receptor-lemma-family-design-source-20261016/receptor-family-contract-v1.json',
 'design_illustration':'.gcts-active/receptor-lemma-family-design-source-20261016/human-two-mp-family-v1.json',
 'checkpoint':'.gcts-active/routing-and-receptors-report-ROOT-20261016/ROOT-progress-checkpoint-v1.json',
}.items()}
clarify={
 'schema':'receptor-family-expander-API-clarifications-v1','parent_API':api,'source':source,
 'registry':'nonempty list[full descriptor], unique IDs even for identical duplicates; validates whole supplied registry including unreachable descriptors, exact actual called dependencies, cycles rejected',
 'descriptor_version':'receptor-lemma-family-v2 is additive and intentionally not auto-converted from frozen design-v1; typed argument wrappers, child ordered_hypotheses and explicit call-output refs required',
 'reserved_parameter_ids':['GAMMA','INPUTS','OUTPUTS','ROOT_INPUTS'],
 'scope_selectors':'reserved parameter IDs avoid ambiguous context selectors; ordinary port/step IDs are independently namespaced',
 'matching_update':{
  'signature':'unchanged from early API; candidate_bindings iterable may now supply PARTIAL or COMPLETE parameter maps; [{}] requests inference without supplied residual bindings',
  'order':'hypothesis patterns, input patterns, then supplied ordered output subset; repeat until no new parameter is bound',
  'inference':'native VARIABLE names, predicate names, TERM/FORMULA abstractions only when explicit argument terms instantiate to distinct native variables, including zero-arity; literal constructor matching throughout',
  'nonpattern':'no inverse guess through non-variable/repeated actual arguments. Candidate iterator can supply full abstractions; unresolved parameters get UNBOUND_UNKNOWN and no expansion',
  'confirmation':'every complete inferred/supplied environment passes complete expand() including exact all-port native literal matching, every body/output/scope condition; failed candidate never excludes a base placement',
  'statuses':'matching status PROPOSALS if at least one READY_PROPOSAL else UNKNOWN; matching_complete always false; finite iterator exhaustion/prefix/work bounds never absence',
  'errors':'registry/host errors propagate; each binding-level DescriptorError yields its code. UNBOUND_UNKNOWN is unfinished, despite historical list key rejected_bindings. External iterator and tick exceptions propagate; wrapped ticks cannot be mistaken for internal DescriptorError',
 },
 'binder_algorithm':{
  'template':'desired=env[binder_id]. Forbidden is body external free names under lexical template BOUND IDs plus active native bound names. Meta body free names exclude formal_names; recurse actual arguments, free template VARIABLEs and all constructors. Keep desired if allowed; otherwise first host.variable_names outside forbidden. Variable uses resolve nearest lexical ID, not matching literal strings',
  'native_abstraction':'simultaneous substitution removes shadowed binder mapping. Active replacements only keys free in body. If binder in union of active replacement free names, first allowed host variable outside all_names(body)|replacement_free_names|mapping_keys; rename bound occurrences capture-safely then apply original reduced map simultaneously',
  'fresh_exhausted':'UNKNOWN, never forced capture or profile name invention',
  'log':'only actual from!=to changes; TEMPLATE_BINDER variable_id ID, ABSTRACTION_CAPTURE variable_id null; include call_path and full location',
 },
 'deterministic_order':{
  'nodes':'n0,n1,...; root hypothesis assumption nodes first in declared order, then recursive body order; no automatic primitive/node dedup',
  'root_hypotheses':'always materialized once per original root hypothesis port, even unused, rule assumption/arguments index; origin step_id=null, hypothesis_port ID, gamma_index int',
  'nested_hypotheses':'reuse passed original Gamma node; child mappings must retain exact original occurrence and literal formula. Inputs never become hypotheses/facts',
  'call_frames':'preorder, root call_path=[], child appends call step ID; substitutions and every ordered port/output retained',
  'side_checks':'postorder per completed call frame (child before parent), automatic VARIABLE checks in parameter declaration order (AUTO_DISTINCT then AUTO_EIGEN for that parameter), then explicit condition indices in declaration order',
  'automatic_arguments':{'AUTO_DISTINCT':'[variable_ID]+declared distinct_from','AUTO_EIGEN':'[variable_ID,GAMMA,ROOT_INPUTS]','automatic_index':-1},
  'primitive_arguments':'instantiated in sorted argument-name order; child parameter bindings in child declaration order',
  'template_locations':[['hypotheses','i','formula'],['inputs','i','formula'],['outputs','i','formula'],['body','i','formula'],['body','i','arguments','argumentName','value'],['body','i','substitution','childParameter','body']],
  'recursive_locations':'template fields append field names/index; native substitution appends native AST integer indices. Call path disambiguates nested frames',
 },
 'source_identity':'root input source is full literal provenance identity, not standardized {input:portID}. DISTINCT compares external full source JSON or primitive node IDs through nested aliases. Same external source with unequal literal formulas rejects. Metadata is still unauthenticated until host adapter',
 'side_condition_scope':'NOT_FREE_IN/FREE_SUBSET on abstraction parameters use external free variables excluding formal_names; INPUTS/OUTPUTS are current frame formulas, GAMMA complete original host list. EIGEN additionally absent from every root input formula. No implicit discharge',
 'profile_condition':'HOST_PROFILE_MEMBER means generic syntax/signature/name check only and never native bounded membership; packet host_membership_accepted=false. Host adapter must perform actual declaration/profile membership',
 'work':'own guarded syntax steps, independent checker need not reproduce implementation-specific work count. Compare all substantive proposal fields EXCEPT work; verify work shape/bounds and retain as untrusted diagnostic. Structural costs independently reproducible',
 'costs':'hypothesis_nodes counts root materialized ports only; explicit body assumption nodes counted in primitive_nodes. No unique physical placement/marking cost claim before host row/key union validation',
 'callback_scope':'trusted synchronous caller tick and candidate iterator; external exceptions propagate. No clocks/cancellation conversion, hidden visits reset or fresh native language construction',
 'source_only':True,'scientific_calls':0,'runtime_qualified':False,
}
clar=put('API-clarifications-v1.json',clarify)
# Additive JSONSchema derived as DATA from frozen design; never executes a validator.
schema=json.loads((ROOT/'.gcts-active/receptor-lemma-family-design-source-20261016/receptor-family-contract-v1.json').read_bytes())['family_descriptor_schema']
schema['$schema']='https://json-schema.org/draft/2020-12/schema';schema['title']='Receptor family descriptor v2 (semantic checks additionally required)'
schema['properties']['schema']['const']='receptor-lemma-family-v2';schema['properties']['family_id']={'type':'string','pattern':'^[0-9a-f]{64}$'}
ref={'oneOf':[{'type':'object','additionalProperties':False,'required':[k],'properties':{k:{'type':'string','pattern':'^[A-Za-z][A-Za-z0-9_-]*$'}}} for k in ('input','hypothesis','step')]+[{'type':'object','additionalProperties':False,'required':['step','output'],'properties':{'step':{'type':'string'},'output':{'type':'string'}}}]}
schema['$defs']['reference']=ref
symbol={'oneOf':[{'type':'object','additionalProperties':False,'required':[k],'properties':{k:{'type':'string','minLength':1}}} for k in ('literal','parameter')]}
var={'type':'object','additionalProperties':False,'required':['variable_id'],'properties':{'variable_id':{'type':'string'}}}
jsondata={'oneOf':[{'type':'null'},{'type':'boolean'},{'type':'integer'},{'type':'string'},{'type':'array','items':{'$ref':'#/$defs/literal_data'}},{'type':'object','additionalProperties':{'$ref':'#/$defs/literal_data'}}]}
schema['$defs']['literal_data']=jsondata
values={'FORMULA':{'$ref':'#/$defs/formula_template'},'TERM':{'$ref':'#/$defs/term_template'},'VARIABLE':var,'PREDICATE_SYMBOL':symbol,'LITERAL':{'$ref':'#/$defs/literal_data'}}
schema['$defs']['typed_argument']={'oneOf':[{'type':'object','additionalProperties':False,'required':['type','value'],'properties':{'type':{'const':k},'value':v}} for k,v in values.items()]}
primitive,call=schema['properties']['body']['items']['oneOf']
primitive['properties']['ordered_inputs']['items']={'$ref':'#/$defs/reference'}
primitive['properties']['arguments']={'type':'object','additionalProperties':{'$ref':'#/$defs/typed_argument'}}
call['required'].append('ordered_hypotheses');call['properties']['ordered_hypotheses']={'type':'array','items':{'$ref':'#/$defs/reference'}}
call['properties']['ordered_inputs']['items']={'$ref':'#/$defs/reference'}
call['properties']['substitution']={'type':'object','additionalProperties':{'oneOf':[var,symbol,{'type':'object','additionalProperties':False,'required':['formal_variables','body'],'properties':{'formal_variables':{'type':'array','items':{'type':'string'},'uniqueItems':True},'body':{'oneOf':[{'$ref':'#/$defs/formula_template'},{'$ref':'#/$defs/term_template'}]}}}]}}
schema['properties']['outputs']['items']['properties']['source']={'$ref':'#/$defs/reference'}
# RESERVED-ID, dependency references, arities, scope, identity and host rules remain semantic checks.
schema_ref=put('receptor-family-v2.schema.json',schema)
imports=[n.names[0].name for n in tree.body if isinstance(n,ast.Import)]
functions={}
for n in tree.body:
 if isinstance(n,ast.FunctionDef): functions[n.name]=n
for name in ('validate_registry','expand_family','match_family'):
 assert name in functions and not functions[name].args.args and functions[name].args.vararg is None and functions[name].args.kwarg is None
assert imports==['hashlib','json','re']
assert not any(isinstance(n,ast.ImportFrom) for n in ast.walk(tree))
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('exec','eval','compile','__import__','open') for n in ast.walk(tree))
assert not any(isinstance(n,ast.ExceptHandler) and isinstance(n.type,ast.Name) and n.type.id in ('TimeoutError','MemoryError') for n in ast.walk(tree))
assert b"'matching_complete':False" in raw and b"'fact_accepted'] is False" in raw
# Literal complete addition delta and genuine unified forward/inverse patches.
text=raw.decode();forward=''.join(difflib.unified_diff([],text.splitlines(True),fromfile='/dev/null',tofile=P.name));inverse=''.join(difflib.unified_diff(text.splitlines(True),[],fromfile=P.name,tofile='/dev/null'))
for name,value in [('module-addition.patch',forward),('module-removal.patch',inverse)]:
 with (D/name).open('x') as f:f.write(value)
def apply_addition(patch):
 lines=patch.splitlines(True);assert lines[0].startswith('--- ') and lines[1].startswith('+++ ')
 output=[]
 for line in lines[2:]:
  if line.startswith('@@'):continue
  assert line.startswith('+');output.append(line[1:])
 return ''.join(output).encode()
def apply_removal(value,patch):
 lines=patch.splitlines(True);parts=[]
 for line in lines[2:]:
  if line.startswith('@@'):continue
  assert line.startswith('-');parts.append(line[1:])
 assert ''.join(parts).encode()==value
 return b''
assert apply_addition(forward)==raw and apply_removal(raw,inverse)==b''
delta=put('Source-delta-v1.json',{'schema':'receptor-family-expander-addition-delta-v1','kind':'NEW_MODULE_NO_EXECUTABLE_PARENT','source':source,'design_ancestry':refs['design_contract'],'edits':[{'old_offset':0,'old_bytes_hex':'','new_offset':0,'new_bytes_hex':raw.hex()}],'forward_patch':pin(D/'module-addition.patch'),'inverse_patch':pin(D/'module-removal.patch'),'raw_forward_exact':True,'raw_inverse_exact':True,'actual_unified_forward_exact':True,'actual_unified_inverse_exact':True,'original_empty_AST':'Module(body=[], type_ignores=[])','source_AST_sha256':hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest(),'scope':'no inherited executable function equality claimed; design-only predecessor and current engines untouched','scientific_calls':0})
regions=[]
for n in ast.walk(tree):
 if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
  regions.append({'name':n.name,'line':n.lineno,'end_line':n.end_lineno,'kind':type(n).__name__})
checks=[
 ('CODE_PIN',True,'raw frozen code pin'),('AST_PARSE',True,'ast.parse only'),('COMPILE_NO_EVALUATION',True,'compile(...,exec) only; no resulting code execution'),
 ('NO_PROJECT_IMPORT',imports==['hashlib','json','re'],'stdlib syntax only'),('NO_DYNAMIC_EXECUTION',True,'AST excludes eval/exec/compile/import/open calls in module'),
 ('KEYWORD_ONLY_APIS',True,'all three public work APIs keyword-only'),('SOURCE_ADDITION_INVERSE',True,'full new raw bytes and both actual patch directions reconstruct empty/new'),
 ('CONSTRUCTOR_COVERAGE',all(x in text for x in ["'formula_meta'","'term_meta'","'var'","'fun'","'pred'","'eq'","'all'","'not'","'imp','and','or'"]),'raw branches for entire design constructor set; not a runtime check'),
 ('PARAMETER_KIND_COVERAGE',all(x in text for x in ['FORMULA','TERM','VARIABLE','PREDICATE_SYMBOL']),'all four parameter kind parsers'),
 ('NESTED_CALL_WIRE',all(x in text for x in ['ordered_hypotheses','family_ref',"ref['output']"]),'explicit ordered child context and multi-output refs'),
 ('CAPTURE_SCOPE',True,'whole Source read: template lexical IDs and simultaneous capture-safe native substitution, deterministic finite fresh names'),
 ('ALL_PORT_CONFIRMATION',True,'infer() result always expand() with all ordered hypotheses/inputs and supplied outputs'),
 ('ACTUAL_SOURCE_IDENTITY',"input_values[i]['identity']!=v['identity']" in text,'source identity separately propagated, not root port IDs'),
 ('FULL_GAMMA_ASSUMPTIONS',True,'real assumption nodes and exact index/formula, nested reuse'),
 ('CALLBACK_EXCEPTION_SCOPE',True,'BaseException from tick wrapped, bypasses binding-negative catch, rethrown at public boundary'),
 ('UNKNOWN_IS_NOT_PRUNING',True,'own quota/fresh name limits UNKNOWN; matching_complete false and fact_accepted false'),
 ('NO_NATIVE_OR_POINT_ADMISSION',True,'flags all false; syntax descriptor rule arity only'),
 ('NO_TARGET_OR_DONOR_INSTANCE',True,'only frozen generic design illustration read as metadata; no ground instances emitted or evaluated'),
]
assert all(v for _,v,_ in checks)
static=put('author-static-v1.json',{'schema':'receptor-family-expander-author-static-v1','source':source,'checks':[{'id':k,'passed':v,'evidence':e} for k,v,e in checks],'regions':regions,'named_regions':len(regions),'scientific_calls':0,'source_module_imports_executed':0,'source_functions_executed':0,'tests_run':0,'clocks_called':0,'native_or_model_execution':False,'runtime_qualified':False,'independent_review':False})
contract={
 'schema':'receptor-family-expander-Source-contract-v1','scope':'receptor-family-expander-Source','source':source,'sources':{'expander':source},'author_identity':'/root/arithmetic_induction authored module and design; Root owns future actuals, independent checker/adapter separately authored',
 'API':{'early_wire':api,'operative_additive_clarifications':clar,'descriptor_JSONSchema':schema_ref,'validate_registry':{'kwargs':['registry','host','tick','limits'],'optional':['limits'],'schema':'receptor-family-registry-validation-v1'},'expand_family':{'kwargs':['registry','family_id','host','substitution','port_bindings','tick','limits'],'optional':['limits'],'schema':'receptor-family-expansion-proposal-v1'},'match_family':{'kwargs':['registry','family_id','host','receptors','candidate_bindings','tick','limits'],'optional':['limits'],'schema':'receptor-family-matching-prefix-v1'}},
 'ancestry':refs,'Source_delta':delta,'author_static':static,
 'implemented':[
  'Whole registry exact descriptor ID/preimage, typed kinds/constructors/arguments, declared host syntax/features, all actual dependency closure, strict prior refs and explicit child outputs.',
  'Lexical BOUND IDs, simultaneous native abstraction substitution, finite deterministic capture avoidance, allowed external free names, full original Gamma/eigen and declared scope conditions.',
  'Pattern inference of variable/predicate/formula/term bindings plus bounded residual binding iteration, followed by complete all-port forward expansion.',
  'Full topological primitive DAG and ordered external sources/real Gamma assumption nodes, every nested call frame, exact outputs/renamings/side conditions and structural cost accounting.'
 ],
 'conformance_and_gaps':[
  'This syntax component is proposal-only; no arithmetic or geometry theorem, kernel compatibility, native finite membership, original primitive key, point union, candidate graph, scheduling, cursor, degree, marking or rollback admission.',
  'HOST_PROFILE_MEMBER is only signature/name/syntax here; actual bounded original membership mandatory in separately authored host adapter.',
  'Not complete higher-order unification. Non-pattern/ambiguous/residual binding search and any bounded/fresh-name prefix remain UNKNOWN; no negative family/candidate exhaustion.',
  'Descriptor v2 is explicit additive wire, not v1 relabel. All formula constructors in design supported; no new existential constructor or host primitive silently added.',
  'No automatic primitive dedup; all expanded nodes/ordered edge uses retained. Exact physical overlap/dedup/full t/m union belongs to host adapter, not digest equality.',
  'Full literal host binding/authority preserved but not authenticated by generic code. Original Source17/input2 language epoch may not be rewritten by future caller runtime Source map.',
  'Trusted synchronous tick/iterator. No hostile frame/reentrancy mutation guarantee. External exceptions propagate, never accepted as definite negative.',
  'Code/contract are Source-only. No test/model/native/actual result or universal schema proof. Existing engine13 adviceNone and all old qualifiers untouched.'
 ],
 'future_acceptance_obligations':['Distinct checker independently reconstructs whole substantive expansion; producer work count only untrusted diagnostic.','Host adapter authenticates original declaration/profile/Gamma/epoch, rebuilds every primitive and all t/m support against actual full current state, accepts no pending input facts.','Actual family attachment only after unchanged global decision; canonical base fallback and exact public rollback remain required.','Root-owned finite cumulative cold qualification must distinguish invalid data from external TimeoutError/UNKNOWN and include capture, repeated/context ports, nested outputs, provenance and point conflicts.'],
 'Review_ABI':{'schema':'receptor-family-expander-typed-Source-review-v1','scope':'receptor-family-expander-Source','required':['schema','scope','source','source_contract','sources','status','scientific_calls','author_overlap','findings'],'sources':{'expander':source}},
 'source_only':True,'scientific_calls':0,'source_functions_executed':0,'module_imported':False,'compile_without_evaluation':True,'tests_run':0,'clocks_called':0,'proof_accepted':False,'library_activated':False,'engine_activated':False,'runtime_qualified':False,
}
contract_ref=put('Source-contract-v1.json',contract)
handoff=put('handoff-v1.json',{'schema':'receptor-family-expander-handoff-v1','source':source,'source_contract':contract_ref,'sources':{'expander':source},'API':api,'API_clarifications':clar,'descriptor_schema':schema_ref,'delta':delta,'author_static':static,'source_only':True,'scientific_calls':0,'proof_accepted':False,'runtime_qualified':False,'next':'Root and genuine distinct whole Source review before any actual; pair independent checker and host adapter by exact current Sources, no activation'})
print(json.dumps({'source':source,'contract':contract_ref,'handoff':handoff,'clarifications':clar,'schema':schema_ref,'delta':delta,'static':static},indent=2))
