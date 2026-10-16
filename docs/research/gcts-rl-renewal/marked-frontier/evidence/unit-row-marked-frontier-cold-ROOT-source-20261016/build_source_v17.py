"""Minimal caller forwarding and target-policy successor. Source/AST/JSON only."""
import ast,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def read(p):return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(r):
 p=Path(r['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==r;return p
def save(n,x):
 p=HERE/n
 with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
 return pin(p)
assert len(sys.argv)==5
components={}
for role,i in (('engine',1),('controls',3)):
 p=Path(sys.argv[i]).resolve();assert pin(p)['sha256']==sys.argv[i+1];h=read(p)
 assert h['scientific_calls']==0
 components[role]={'handoff':pin(p),'source':h['source'],'source_contract':h['source_contract']}
 for r in components[role].values():check(r)
 c=read(check(h['source_contract']))
 assert c['source_only'] is True and c['scientific_calls']==0 and c['scientific_acceptance'] is False
 if role=='controls':assert h['prospective_case_count']==23 and h['original_case_count']==17 and h['new_policy_case_count']==6
parent=BASE/'unit-row-selective-multikey-cold-ROOT-source-20261016/unit_row_selective_multikey_cold_v16.py';pc=parent.parent/'Source-contract-v16.json'
assert pin(parent)['sha256']=='05da14dfe2a6d18cc29bd7a582f60bbbac49caf38336dbbf421b84d2b746ca02' and pin(pc)['sha256']=='c3c1b026b51cd273f575ca70d475727f05c239d371881e771f248e4e1f85ed98'
prior=read(pc);old=parent.read_text();text=old;edits=[]
def replace(a,b):
 global text
 assert text.count(a)==1;offset=text.index(a);text=text.replace(a,b,1);edits.append({'before':a,'after':b,'forward_offset_at_this_step':offset})
tree=ast.parse(old);fixed=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FIXED' for t in n.targets))
for role in ('engine','controls'):
 raw=next(ast.get_source_segment(old,v) for k,v in zip(fixed.keys,fixed.values) if ast.literal_eval(k)==role)
 assert ast.literal_eval(raw)==prior['sources'][role];replace(raw,repr(components[role]['source']))
replace("VERSION='unit-row-selective-multikey-cold-v16'","VERSION='unit-row-marked-frontier-cold-v17'")
replace("SCOPE='unit-row-selective-multikey-cold-Source'","SCOPE='unit-row-marked-frontier-cold-Source'")
replace("contract['schema'] == 'unit-row-selective-multikey-cold-Source-contract-v16'","contract['schema'] == 'unit-row-marked-frontier-cold-Source-contract-v17'")
replace('            branch_adviser=None,validate_advice=None,tick):',"            branch_adviser=None,validate_advice=None,tick,branch_tie='ROW'):")
replace('            branch_adviser=branch_adviser,validate_advice=validate_advice,\n            initial_state=', '            branch_adviser=branch_adviser,validate_advice=validate_advice,branch_tie=branch_tie,\n            initial_state=')
replace('    def scheduler_adapter(*,evidence,generations,tick):',"    def scheduler_adapter(*,evidence,generations,tick,branch_tie='ROW',assigned_output_rows=None):")
replace("            'evidence':copy.deepcopy(evidence),'generations':copy.deepcopy(generations),'tick':step},", "            'evidence':copy.deepcopy(evidence),'generations':copy.deepcopy(generations),'tick':step,\n            'branch_tie':branch_tie,'assigned_output_rows':copy.deepcopy(assigned_output_rows)},")
replace('        engine = engine_factory(initial_state=None,tick=tick,\n            branch_adviser=', "        engine = engine_factory(initial_state=None,tick=tick,branch_tie='ASSIGNED-OUTPUT-THEN-ROW',\n            branch_adviser=")
assert len(edits)==10
inverse=text
for e in reversed(edits):
 assert inverse.count(e['after'])==1;inverse=inverse.replace(e['after'],e['before'],1)
assert inverse==old
p=HERE/'unit_row_marked_frontier_cold_v17.py'
with p.open('xb') as f:f.write(text.encode())
ntree=ast.parse(text);compile(ntree,str(p),'exec');otree=ast.parse(old)
changed={'main','engine_factory','scheduler_adapter','run_original_search'};unchanged=[]
for n in ast.walk(ntree):
 if isinstance(n,ast.FunctionDef) and n.name not in changed:
  same=[o for o in ast.walk(otree) if isinstance(o,ast.FunctionDef) and o.name==n.name and ast.dump(o,include_attributes=False)==ast.dump(n,include_attributes=False)]
  assert same and any(ast.get_source_segment(text,n)==ast.get_source_segment(old,o) for o in same);unchanged.append(n.name)
for anchor in ('def save_failure_diagnostic(', '    def validate_found(found):',"    result_raw = canonical({'schema':'ROOT-unit-row-global-engine-result-v1',"):
 a=old.index(anchor);b=text.index(anchor)
 if anchor.startswith('def save'):
  end='\ndef encode_result_transport(';assert old[a:old.index(end,a)]==text[b:text.index(end,b)]
 elif anchor.startswith('    def validate'):
  end='\n    search_capture = ';assert old[a:old.index(end,a)]==text[b:text.index(end,b)]
 else:assert old[a:]==text[b:]
source=pin(p);sources=dict(prior['sources'],intake=source,engine=components['engine']['source'],controls=components['controls']['source'])
assert len(sources)==17 and all(sources[k]==prior['sources'][k] for k in sources if k not in ('intake','engine','controls'))
for r in [*sources.values(),*prior['inputs'].values()]:check(r)
delta=save('Source-delta-v17.json',{'schema':'ROOT-marked-frontier-caller-Source-delta-v17','parent':pin(parent),'source':source,'edits':edits,'whole_raw_inverse_recovers_parent':True,'affected_nested_functions':['engine_factory','scheduler_adapter','run_original_search'],'unchanged_raw_AST_function_regions':unchanged,'native_failure_fullproof_output_tail_raw_exact':True})
c=dict(prior,schema='unit-row-marked-frontier-cold-Source-contract-v17',scope='unit-row-marked-frontier-cold-Source',sources=sources,parent_source=pin(parent),parent_contract=pin(pc),source_delta=delta)
c['Review_ABI']=dict(prior['Review_ABI'],schema='unit-row-marked-frontier-cold-typed-Source-review-v17',scope=c['scope'],source=source,sources=sources)
c['scheduler']='Global DEAD, unresolved completeness gate, global FORCED, earliest generation preserved. ROW default for original/retention/advice controls; explicit ASSIGNED-OUTPUT-THEN-ROW only for both target arms and separately counted new policy controls. Literal current output-mark presence breaks generation ties, never occupancy or established-fact status. Exact kind,row decision wire unchanged.'
c['purposes']=dict(prior['purposes']);c['purposes']['unit-row-advised-original-controls']='Original17 ROW cases unchanged plus6 separately counted marking-aware policy controls, prospective23. Other control suites17/43 remain ROW default. Essential gaps prohibit target admission.'
c['search']=prior['search']+' Both target arms now explicitly use the same ASSIGNED-OUTPUT-THEN-ROW policy. Current ROW-TIE results stay immutable; no target proof/route or old outcome prediction is supplied.'
c['advice']=dict(prior['advice'],current_sources={k:sources[k] for k in ('engine','adviser','advice_validator','advice_controls')})
c['marked_frontier_successor']={'components':components,'original_control_cases':23,'retention_control_cases':17,'advice_control_cases':43,'current_sources':sources,'target_policy':'ASSIGNED-OUTPUT-THEN-ROW','default_policy':'ROW','scope':'Current default-ROW consumer controls do not alone qualify MARK. Six new policy controls are separately counted, including genuine original-language decision/placement/checkpoint cases. Markings are obligations, not facts. Engine constructor and scheduler forwarding only; native guards/callback scalar diagnostics/failure55/fullproof/transport/output unchanged.','historical_dependency_provenance':'Unchanged C11/retention2 contracts retain earlier engine8 provenance. This current Source17 capsule and new cross-integration Source review declare engine9 operative; no historical contract is silently rewritten.','scientific_acceptance':False,'runtime_qualification_inherited':False}
cr=save('Source-contract-v17.json',c)
save('static-evidence-v17.json',{'source':source,'source_contract':cr,'literal_edits':10,'whole_raw_AST_inverse':True,'unchanged_raw_AST_function_regions':unchanged,'native_failure_fullproof_response_transport_output_tail_exact':True,'other14Sources_input2_limits_exact':True,'compile_only':True,'scientific_calls':0,'scientific_acceptance':False})
hr=save('handoff-v17.json',{'schema':'ROOT-marked-frontier-cold-Source-handoff-v17','source':source,'source_contract':cr,'sources':sources,'inputs':c['inputs'],'limits':c['limits'],'source_delta':delta,'expected_original_cases':23,'expected_domain_cases':17,'expected_consumer_cases':43,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'whole_caller_peer_review_pending':True})
print(json.dumps({'source':source,'source_contract':cr,'handoff':hr}))
