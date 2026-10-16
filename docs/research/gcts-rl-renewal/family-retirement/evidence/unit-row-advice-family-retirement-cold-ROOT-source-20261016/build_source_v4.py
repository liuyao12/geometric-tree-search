"""Adapted exact caller assembly: raw Source/JSON/AST only, no project calls."""
import ast,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def read(p):return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(r):
 p=Path(r['path']);assert p.is_absolute() and p==p.resolve() and pin(p)==r;return p
def save(n,v):
 p=HERE/n
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
 return pin(p)
assert len(sys.argv)==5,'engine handoff/hash and controls handoff/hash required'
component={}
for role,path,sha in [('engine',sys.argv[1],sys.argv[2]),('advice_controls',sys.argv[3],sys.argv[4])]:
 p=Path(path).resolve();assert pin(p)['sha256']==sha
 h=read(p);check(h['source']);check(h['source_contract'])
 assert h['source_only'] is True and h['scientific_calls']==0 and h['scientific_acceptance'] is False
 component[role]={'handoff':pin(p),'source':h['source'],'source_contract':h['source_contract']}
parent=BASE/'unit-row-advice-horizon-cold-ROOT-source-20261016/unit_row_advised_domain_horizon_cold_v3.py'
pc=parent.parent/'Source-contract-v3.json'
assert pin(parent)['sha256']=='98524052a3682a3374d7cf4988e7e74856c6e12e2de7b5f4a4973664ff411097'
assert pin(pc)['sha256']=='29ac934db17f88711763cfcd29e7f322e3037ebb52facfcc2c6ad2d3643bc1cf'
prior=read(pc);old=parent.read_text();text=old;edits=[]
def replace(before,after):
 global text
 assert text.count(before)==1,before[:100]
 text=text.replace(before,after,1);edits.append({'before':before,'after':after})
for role in ('engine','advice_controls'):replace(repr(prior['sources'][role]),repr(component[role]['source']))
replace("VERSION='unit-row-advised-domain-horizon-cold-v3'","VERSION='unit-row-advice-family-retirement-cold-v4'")
replace("SCOPE='unit-row-advised-domain-horizon-cold-Source'","SCOPE='unit-row-advice-family-retirement-cold-Source'")
replace("contract['schema'] == 'unit-row-advised-domain-horizon-cold-Source-contract-v3'","contract['schema'] == 'unit-row-advice-family-retirement-cold-Source-contract-v4'")
path=HERE/'unit_row_advice_family_retirement_cold_v4.py'
if path.exists():assert path.read_bytes()==text.encode()
else:
 with path.open('xb') as f:f.write(text.encode())
tree=ast.parse(text);compile(tree,str(path),'exec');oldtree=ast.parse(old)
inverse=text
for e in reversed(edits):
 assert inverse.count(e['after'])==1
 inverse=inverse.replace(e['after'],e['before'],1)
assert inverse==old
defs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
olddefs={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)}
helpers=[n for n in olddefs if n!='main'];assert len(helpers)==17
for name in helpers:assert ast.dump(defs[name],include_attributes=False)==ast.dump(olddefs[name],include_attributes=False)
for n in ast.walk(tree):
 if isinstance(n,ast.FunctionDef) and n.name not in ('main',):
  matches=[o for o in ast.walk(oldtree) if isinstance(o,ast.FunctionDef) and o.name==n.name and ast.dump(o,include_attributes=False)==ast.dump(n,include_attributes=False)]
  assert matches,n.name
tail="    body = {'schema':'ROOT-unit-row-global-engine-response-body-v1',"
assert text[text.index(tail):]==old[old.index(tail):]
source=pin(path);sources=dict(prior['sources'],intake=source,**{k:v['source'] for k,v in component.items()})
for r in [*sources.values(),*prior['inputs'].values()]:check(r)
control_contract=read(check(component['advice_controls']['source_contract']))
old_cases=read(BASE/'unit-row-goal-advice-controls-horizon-source-20261016/Source-contract-v3.json')['cases']
cases=old_cases+control_contract['new_cases']
assert len(cases)==control_contract['API']['expected_cases']==30 and len(cases)==len(set(cases))
observed=BASE/'unit-row-cluster-consumer-publication-ROOT-20261016/ROOT-progress-checkpoint-v1.json'
assert pin(observed)['sha256']=='b474e3dc0e11c05abce32eb57f51a8cbf98a35abca3b61001e265f4c86eeb52e'
delta=save('Source-delta-v4.json',{'schema':'ROOT-family-retirement-cold-Source-delta-v4','parent':pin(parent),'source':source,'edits':edits,'entire_inverse_recovers_parent':True,'scope':'Two component pins, own VERSION/SCOPE/consumed schema only. All adviser adapter defaults, model, native gates and checking unchanged.'})
c=dict(prior,schema='unit-row-advice-family-retirement-cold-Source-contract-v4',scope='unit-row-advice-family-retirement-cold-Source',sources=sources,parent_source=pin(parent),parent_contract=pin(pc),source_delta=delta)
c['inherited_horizon_successor']=c.pop('horizon_successor')
c['family_retirement_successor']={'components':component,'measured_predecessor':pin(observed),'expected_consumer_cases':len(cases),'cases':cases,'policy':'Any definite current pending-key rejection abandons all uninstalled advisory preferences; at most one new batch at same already selected BRANCH. Independent legality/fallback/global scheduling/exact rollback unchanged. No marking/candidate pruning or adviser quality change.','target_policy':{'maximum_demands':5,'maximum_rounds':3,'maximum_terms':16,'maximum_work':50000,'maximum_proposals':8},'control_policy':{'maximum_demands':5,'maximum_rounds':3,'maximum_terms':1,'maximum_work':50000,'maximum_proposals':8},'runtime_qualification_inherited':False,'fit_prediction':False,'target_requires_all_current_consumer_no_skip_plus_original_and_retention':True}
c['Review_ABI']=dict(prior['Review_ABI'],schema='unit-row-advice-family-retirement-cold-typed-Source-review-v4',scope=c['scope'],source=source,sources=sources)
cr=save('Source-contract-v4.json',c)
save('static-evidence-v4.json',{'source':source,'source_contract':cr,'literal_edits':5,'entire_inverse_recovers_parent':True,'top_level_helpers_AST_exact':helpers,'all_nested_functions_AST_exact':True,'response_stdout_native_exit_suffix_raw_exact':True,'Source17_input2_sixlimits':True,'compile_only':True,'scientific_execution':False,'metadata_recovery':'Initial helper expected old controls cases field; current capsule declares new_cases plus preserved22/API expected30. Corrected metadata assembly and recovered byte-identical already-written Source; no scientific execution or Source change.'})
hr=save('handoff-v4.json',{'schema':'ROOT-family-retirement-cold-Source-handoff-v4','source':source,'source_contract':cr,'sources':sources,'inputs':c['inputs'],'limits':c['limits'],'source_delta':delta,'components':component,'expected_consumer_cases':len(cases),'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'whole_caller_peer_review_pending':True})
print(json.dumps({'source':source,'source_contract':cr,'handoff':hr}))
