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
roles=('engine','adviser','advice_validator','advice_controls')
assert len(sys.argv)==9
components={}
for index,role in enumerate(roles):
 p=Path(sys.argv[1+index*2]).resolve(); assert pin(p)['sha256']==sys.argv[2+index*2]
 h=read(p); check(h['source']); check(h['source_contract'])
 assert h['source_only'] is True and h['scientific_calls']==0 and h['scientific_acceptance'] is False
 components[role]={'handoff':pin(p),'source':h['source'],'source_contract':h['source_contract']}
parent=BASE/'unit-row-advice-family-retirement-cold-ROOT-source-20261016/unit_row_advice_family_retirement_cold_v4.py'
pc=parent.parent/'Source-contract-v4.json'
assert pin(parent)['sha256']=='5b88a8c096e8e55bad143c313749594d58631117584d4c9d34cf74c1a9dfcb95'
assert pin(pc)['sha256']=='439d2d6dcb3b6ae3d20a8247709b3d1c04ab27ab26a640c3c9cabe1fd0b5e59e'
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
replace("VERSION='unit-row-advice-family-retirement-cold-v4'","VERSION='unit-row-fair-interface-cold-v5'")
replace("SCOPE='unit-row-advice-family-retirement-cold-Source'","SCOPE='unit-row-fair-interface-cold-Source'")
replace("contract['schema'] == 'unit-row-advice-family-retirement-cold-Source-contract-v4'","contract['schema'] == 'unit-row-fair-interface-cold-Source-contract-v5'")
path=HERE/'unit_row_fair_interface_cold_v5.py'
with path.open('xb') as f: f.write(text.encode())
tree=ast.parse(text); compile(tree,str(path),'exec'); oldtree=ast.parse(old)
inverse=text
for e in reversed(edits):
 assert inverse.count(e['after'])==1
 inverse=inverse.replace(e['after'],e['before'],1)
assert inverse==old and len(edits)==7
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
oldcases=prior['family_retirement_successor']['cases']
cases=oldcases+cc['new_cases']
assert len(cases)==cc['API']['expected_cases'] and len(cases)==len(set(cases)) and len(oldcases)==30
observed=BASE/'unit-row-advice-family-retirement-publication-ROOT-20261016/ROOT-progress-checkpoint-v1.json'
assert pin(observed)['sha256']=='93cb85593720d512608295f94c45b01d1e83237c62f3a240f533da35fa049fda'
delta=save('Source-delta-v5.json',{'schema':'ROOT-fair-interface-cold-Source-delta-v5','parent':pin(parent),'source':source,'edits':edits,'entire_inverse_recovers_parent':True,'scope':'Four component pins and own VERSION/SCOPE/consumed schema only; all17 helpers/nestedfunctions/output-nativeexit exact.'})
c=dict(prior,schema='unit-row-fair-interface-cold-Source-contract-v5',scope='unit-row-fair-interface-cold-Source',sources=sources,parent_source=pin(parent),parent_contract=pin(pc),source_delta=delta)
c['inherited_family_retirement_successor']=c.pop('family_retirement_successor')
c['fair_interface_successor']={'components':components,'measured_predecessor':pin(observed),'expected_consumer_cases':len(cases),'cases':cases,'policy':'Generic bounded fair descriptor enumeration and literal interface-aware proposal ordering; independently recomputed by separate consumer. No candidate pruning or facts, full fallback/scheduler/retirement/rollback unchanged.','target_policy':{'maximum_demands':5,'maximum_rounds':3,'maximum_terms':16,'maximum_work':50000,'maximum_proposals':8},'control_policy':{'maximum_demands':5,'maximum_rounds':3,'maximum_terms':1,'maximum_work':50000,'maximum_proposals':8},'runtime_qualification_inherited':False,'fit_prediction':False,'target_requires_all_current_consumer_no_skip_plus_original_and_retention':True}
c['Review_ABI']=dict(prior['Review_ABI'],schema='unit-row-fair-interface-cold-typed-Source-review-v5',scope=c['scope'],source=source,sources=sources)
cr=save('Source-contract-v5.json',c)
save('static-evidence-v5.json',{'source':source,'source_contract':cr,'literal_edits':7,'entire_inverse_recovers_parent':True,'top_level_helpers_raw_AST_exact':helpers,'all_nested_functions_AST_exact':True,'response_stdout_native_exit_suffix_raw_exact':True,'Source17_input2_sixlimits':True,'compile_only':True,'scientific_execution':False,'metadata_note':'Initial assembly assumed repr key order from sorted JSON for original adviser/consumer FIXED pins; no Source written. Corrected to exact AST-located literal segments, preserving whole seven-region inverse. No scientific actual.'})
hr=save('handoff-v5.json',{'schema':'ROOT-fair-interface-cold-Source-handoff-v5','source':source,'source_contract':cr,'sources':sources,'inputs':c['inputs'],'limits':c['limits'],'source_delta':delta,'components':components,'expected_consumer_cases':len(cases),'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'whole_caller_peer_review_pending':True})
print(json.dumps({'source':source,'source_contract':cr,'handoff':hr}))
