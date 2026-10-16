"""Minimal caller successor assembly. Raw Source/AST/JSON only."""
import ast, hashlib, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; BASE=HERE.parent
def read(p): return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes(); return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(r):
 p=Path(r['path']); assert p.is_absolute() and p==p.resolve() and pin(p)==r; return p
def save(n,v):
 p=HERE/n
 with p.open('x') as f: json.dump(v,f,indent=2,sort_keys=True); f.write('\n')
 return pin(p)
roles=('advice_controls',)
assert len(sys.argv)==3
components={}
for index,role in enumerate(roles):
 p=Path(sys.argv[1+index*2]).resolve(); assert pin(p)['sha256']==sys.argv[2+index*2]
 h=read(p); check(h['source']); check(h['source_contract'])
 assert h['source_only'] is True and h['scientific_calls']==0 and h['scientific_acceptance'] is False
 components[role]={'handoff':pin(p),'source':h['source'],'source_contract':h['source_contract']}
parent=BASE/'unit-row-observation-reuse-cold-ROOT-source-20261016/unit_row_observation_reuse_cold_v7.py'
pc=parent.parent/'Source-contract-v7.json'
assert pin(parent)['sha256']=='5fdc91cc0078f02fb1c2c13b86204cff3310ae9e6456b95189a06b0ffb7c4f45'
assert pin(pc)['sha256']=='0efba1e772013fee3bdfc03367a25e1bbc523e4e3aa72ef437df2869d7c931f4'
prior=read(pc); old=parent.read_text(); text=old; edits=[]
def replace(before,after):
 global text
 assert text.count(before)==1,before[:100]
 text=text.replace(before,after,1); edits.append({'before':before,'after':after})
fixed=next(n.value for n in ast.parse(old).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FIXED' for t in n.targets))
literal_pins={ast.literal_eval(k):ast.get_source_segment(old,v) for k,v in zip(fixed.keys,fixed.values)}
for role in roles:
 assert ast.literal_eval(literal_pins[role])==prior['sources'][role]
 replace(literal_pins[role],repr(components[role]['source']))
replace("VERSION='unit-row-observation-reuse-cold-v7'","VERSION='unit-row-phase-diagnostic-cold-v8'")
replace("SCOPE='unit-row-observation-reuse-cold-Source'","SCOPE='unit-row-phase-diagnostic-cold-Source'")
replace("contract['schema'] == 'unit-row-observation-reuse-cold-Source-contract-v7'","contract['schema'] == 'unit-row-phase-diagnostic-cold-Source-contract-v8'")
path=HERE/'unit_row_phase_diagnostic_cold_v8.py'
with path.open('xb') as f: f.write(text.encode())
tree=ast.parse(text); compile(tree,str(path),'exec'); oldtree=ast.parse(old)
inverse=text
for e in reversed(edits):
 assert inverse.count(e['after'])==1
 inverse=inverse.replace(e['after'],e['before'],1)
assert inverse==old and len(edits)==4
defs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
olddefs={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)}
helpers=[n for n in olddefs if n!='main']; assert len(helpers)==17
for name in helpers:
 assert ast.dump(defs[name],include_attributes=False)==ast.dump(olddefs[name],include_attributes=False)
 assert ast.get_source_segment(text,defs[name])==ast.get_source_segment(old,olddefs[name])
for n in ast.walk(tree):
 if isinstance(n,ast.FunctionDef) and n.name!='main':
  assert any(isinstance(o,ast.FunctionDef) and o.name==n.name and ast.dump(o,include_attributes=False)==ast.dump(n,include_attributes=False) for o in ast.walk(oldtree)),n.name
tail="    body = {'schema':'ROOT-unit-row-global-engine-response-body-v1',"
assert text[text.index(tail):]==old[old.index(tail):]
source=pin(path); sources=dict(prior['sources'],intake=source,**{k:v['source'] for k,v in components.items()})
assert len(sources)==17 and len(prior['inputs'])==2
for ref in [*sources.values(),*prior['inputs'].values()]: check(ref)
cc=read(check(components['advice_controls']['source_contract']))
cases=prior['compatible_source_fibres_successor']['cases']
assert cc['API']['expected_cases']==len(cases)==43 and len(set(cases))==43
observed=BASE/'unit-row-observation-reuse-ROOT-20261016/ROOT-advice-controls-disposition-v1.json'
assert pin(observed)['sha256']=='302f9bed7339a267870a907e21db0a910fe50dba1fa32fe7928e78b9558bd08b'
delta=save('Source-delta-v8.json',{'schema':'ROOT-phase-diagnostic-cold-Source-delta-v8','parent':pin(parent),'source':source,'edits':edits,'entire_inverse_recovers_parent':True,'scope':'One controls pin and own VERSION/SCOPE/consumed schema only; all17 helpers/nestedfunctions/output-nativeexit exact.'})
c=dict(prior,schema='unit-row-phase-diagnostic-cold-Source-contract-v8',scope='unit-row-phase-diagnostic-cold-Source',sources=sources,parent_source=pin(parent),parent_contract=pin(pc),source_delta=delta)
c['compatible_source_fibres_successor']=dict(prior['compatible_source_fibres_successor'])
c['compatible_source_fibres_successor']['components']=dict(prior['compatible_source_fibres_successor']['components'],**components)
c['compatible_source_fibres_successor']['measured_predecessor']=pin(observed)
c['observation_reuse_successor']=dict(prior['observation_reuse_successor'],components=components)
c['phase_diagnostic_successor']={'components':components,'expected_consumer_cases':43,'cases':cases,'scope':'Only bounded fixed literal coarsephase stderr observations inside original native20. All control semantics, report reuse, declared cases, target inputs and budgets unchanged. No new clock/API/process or posttimeout scientific work. Markers are unqualified reached-phase diagnostics, never case counts, proof/trajectory/resource-positive authority.','measured_parent_failure':pin(observed),'target_policy':prior['compatible_source_fibres_successor']['target_policy'],'control_policy':prior['compatible_source_fibres_successor']['control_policy'],'runtime_qualification_inherited':False,'fit_prediction':False,'target_requires_all_current_consumer_no_skip_plus_original_and_retention':True}
c['Review_ABI']=dict(prior['Review_ABI'],schema='unit-row-phase-diagnostic-cold-typed-Source-review-v8',scope=c['scope'],source=source,sources=sources)
c['advice']=dict(prior['advice'],current_sources={k:sources[k] for k in ('engine','adviser','advice_validator','advice_controls')})
cr=save('Source-contract-v8.json',c)
save('static-evidence-v8.json',{'source':source,'source_contract':cr,'literal_edits':4,'entire_inverse_recovers_parent':True,'top_level_helpers_raw_AST_exact':helpers,'all_nested_functions_AST_exact':True,'response_stdout_native_exit_suffix_raw_exact':True,'Source17_input2_sixlimits':True,'compile_only':True,'scientific_execution':False,'metadata_note':'Adapt existing AST-located literal pin assembly to one control pin and own identifiers only; no scientific execution.'})
hr=save('handoff-v8.json',{'schema':'ROOT-phase-diagnostic-cold-Source-handoff-v8','source':source,'source_contract':cr,'sources':sources,'inputs':c['inputs'],'limits':c['limits'],'source_delta':delta,'components':components,'expected_consumer_cases':len(cases),'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'whole_caller_peer_review_pending':True})
print(json.dumps({'source':source,'source_contract':cr,'handoff':hr}))
