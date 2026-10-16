"""Raw Source/JSON/AST assembly only; never call a project/scientific module."""
import ast,hashlib,json
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
parent=BASE/'unit-row-advice-cold-ROOT-source-20261016/unit_row_advised_domain_cold_v1.py'
assert pin(parent)['sha256']=='2baf0264a35c29f0e23d0466039627e5302f4deb25792a6f807a0c1b3b4c7b59'
pc=parent.parent/'Source-contract-v1.json';assert pin(pc)['sha256']=='c9a1391bfbd4edfef779432cdc0779a9971edd1fb4cb58537a660d7be1373e90'
prior=read(pc);old=parent.read_text();text=old;edits=[]
controls_handoff=BASE/'unit-row-goal-advice-controls-source-20261016/handoff-v2.json'
assert pin(controls_handoff)['sha256']=='293b60d17f679cb9b47419578d0226776d96f4c18989269a790c2df1cd5da7c3'
h=read(controls_handoff);check(h['source']);check(h['source_contract'])
assert h['source']['sha256']=='229f9cdd2daf6b9aa7f9b6ea071f2ffdbf69b1caf82351a818cf8a489c30a98b'
def replace(before,after):
 global text
 assert text.count(before)==1,before[:100]
 text=text.replace(before,after,1);edits.append(dict(before=before,after=after))
replace(repr(prior['sources']['advice_controls']),repr(h['source']))
replace("VERSION='unit-row-advised-domain-cold-v1'","VERSION='unit-row-advised-domain-diagnostic-cold-v2'")
replace("SCOPE='unit-row-advised-domain-cold-Source'","SCOPE='unit-row-advised-domain-diagnostic-cold-Source'")
replace("contract['schema'] == 'unit-row-advised-domain-cold-Source-contract-v1'","contract['schema'] == 'unit-row-advised-domain-diagnostic-cold-Source-contract-v2'")
source_path=HERE/'unit_row_advised_domain_diagnostic_cold_v2.py'
with source_path.open('xb') as f:f.write(text.encode())
tree=ast.parse(text);compile(tree,str(source_path),'exec');oldtree=ast.parse(old)
inverse=text
for e in reversed(edits):
 assert inverse.count(e['after'])==1;inverse=inverse.replace(e['after'],e['before'],1)
assert inverse==old
defs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)};olddefs={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)}
helpers=[n for n in olddefs if n!='main'];assert len(helpers)==17
for name in helpers:
 assert ast.dump(defs[name],include_attributes=False)==ast.dump(olddefs[name],include_attributes=False)
 assert ast.get_source_segment(text,defs[name])==ast.get_source_segment(old,olddefs[name])
tail="    body = {'schema':'ROOT-unit-row-global-engine-response-body-v1',"
assert text[text.index(tail):]==old[old.index(tail):]
source=pin(source_path);sources=dict(prior['sources'],intake=source,advice_controls=h['source'])
for r in [*sources.values(),*prior['inputs'].values()]:check(r)
delta=save('Source-delta-v2.json',{'schema':'ROOT-diagnostic-cold-Source-delta-v2','parent':pin(parent),'source':source,'edits':edits,'entire_inverse_recovers_parent':True,'semantic_scope':'Control pin and ownVERSION/SCOPE/contract schema only. No scientific algorithm/helper/adapter/budget/positive-check/output changes.'})
contract=dict(prior,schema='unit-row-advised-domain-diagnostic-cold-Source-contract-v2',scope='unit-row-advised-domain-diagnostic-cold-Source',sources=sources,parent_source=pin(parent),parent_contract=pin(pc),source_delta=delta)
contract['diagnostic_successor']={'source':h['source'],'source_contract':h['source_contract'],'handoff':pin(controls_handoff),'scope':'Preserve complete actual initial adviser return before unchanged fixture eligibility. No quota/model/fallback/case/qualification change. Old2pass20skip preserved. NewSource runtime not inherited.','expected_cases':22,'all22_without_skips_required_for_target':True,'all_costs_charged':True,'changed_algorithm':False}
contract['Review_ABI']=dict(prior['Review_ABI'],schema='unit-row-advised-domain-diagnostic-cold-typed-Source-review-v2',scope=contract['scope'],source=source,sources=sources)
cr=save('Source-contract-v2.json',contract)
save('static-evidence-v2.json',{'schema':'ROOT-diagnostic-cold-static-evidence-v2','source':source,'source_contract':cr,'parent':pin(parent),'literal_edits':4,'entire_inverse_recovers_parent':True,'top_level_helpers_raw_and_AST_exact':helpers,'response_stdout_native_exit_suffix_raw_exact':True,'Source17_input2_sixlimits':True,'compile_only':True,'scientific_execution':False})
hr=save('handoff-v2.json',{'schema':'ROOT-diagnostic-cold-Source-handoff-v2','source':source,'source_contract':cr,'sources':sources,'inputs':contract['inputs'],'limits':contract['limits'],'source_delta':delta,'controls_handoff':pin(controls_handoff),'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'whole_caller_peer_review_pending':True})
print(json.dumps({'source':source,'source_contract':cr,'handoff':hr}))
