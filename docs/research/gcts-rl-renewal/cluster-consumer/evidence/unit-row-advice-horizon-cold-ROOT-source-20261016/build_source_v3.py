"""Raw Source/JSON/AST assembly only; no project/scientific execution."""
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
parent=BASE/'unit-row-advice-diagnostic-cold-ROOT-source-20261016/unit_row_advised_domain_diagnostic_cold_v2.py'
assert pin(parent)['sha256']=='dd5d5951a2b269197d4bbdc56e5f6088b5b3bcbd1a47b18ec8db59ed0de26a50'
pc=parent.parent/'Source-contract-v2.json';assert pin(pc)['sha256']=='71ec9fc3bc8442f6c5a56e9836e4e195cc9c020a9c2db703ee7d622087c8b107'
prior=read(pc);old=parent.read_text();text=old;edits=[]
hp=BASE/'unit-row-goal-advice-controls-horizon-source-20261016/handoff-v3.json'
assert pin(hp)['sha256']=='325a670b6accb1a0f9156b54611e19738d656322bf502464733ef4c4f8c0d6a8'
h=read(hp);check(h['source']);check(h['source_contract']);assert h['source']['sha256']=='dac89e55a49d3fb6ee425ee97762674667745c2c222815897494555734a340f3'
observed=BASE/'unit-row-advice-diagnostic-ROOT-20261016/ROOT-advice-controls-disposition-v1.json'
assert pin(observed)['sha256']=='24c1669578e78ddccdc5e52b0236a95060789d90b5a2b2e9f987810eecba17a1'
o=read(observed);assert o['actual_closed'] and o['native_resources_qualified'] and not o['controls_accepted']
assert o['actual_adviser_return']['work']['guarded_steps']==50000 and o['actual_adviser_return']['partial_proposals']==8
def replace(before,after):
 global text
 assert text.count(before)==1,before[:100]
 text=text.replace(before,after,1);edits.append(dict(before=before,after=after))
replace(repr(prior['sources']['advice_controls']),repr(h['source']))
replace("VERSION='unit-row-advised-domain-diagnostic-cold-v2'","VERSION='unit-row-advised-domain-horizon-cold-v3'")
replace("SCOPE='unit-row-advised-domain-diagnostic-cold-Source'","SCOPE='unit-row-advised-domain-horizon-cold-Source'")
replace("contract['schema'] == 'unit-row-advised-domain-diagnostic-cold-Source-contract-v2'","contract['schema'] == 'unit-row-advised-domain-horizon-cold-Source-contract-v3'")
replace('            maximum_demands=16,maximum_terms=16,maximum_rounds=8):','            maximum_demands=5,maximum_terms=16,maximum_rounds=3):')
path=HERE/'unit_row_advised_domain_horizon_cold_v3.py'
with path.open('xb') as f:f.write(text.encode())
tree=ast.parse(text);compile(tree,str(path),'exec');oldtree=ast.parse(old)
inverse=text
for e in reversed(edits):assert inverse.count(e['after'])==1;inverse=inverse.replace(e['after'],e['before'],1)
assert inverse==old
defs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)};olddefs={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)};helpers=[n for n in olddefs if n!='main'];assert len(helpers)==17
for name in helpers:assert ast.dump(defs[name],include_attributes=False)==ast.dump(olddefs[name],include_attributes=False)
tail="    body = {'schema':'ROOT-unit-row-global-engine-response-body-v1',";assert text[text.index(tail):]==old[old.index(tail):]
source=pin(path);sources=dict(prior['sources'],intake=source,advice_controls=h['source'])
for r in [*sources.values(),*prior['inputs'].values()]:check(r)
delta=save('Source-delta-v3.json',{'schema':'ROOT-horizon-cold-Source-delta-v3','parent':pin(parent),'source':source,'edits':edits,'entire_inverse_recovers_parent':True,'scope':'Control pin/ownIDs/schema and adviser_adapter defaultdemands5/rounds3 only; terms16/work50000/proposals8 unchanged.'})
c=dict(prior,schema='unit-row-advised-domain-horizon-cold-Source-contract-v3',scope='unit-row-advised-domain-horizon-cold-Source',sources=sources,parent_source=pin(parent),parent_contract=pin(pc),source_delta=delta)
c['inherited_diagnostic_successor']=c.pop('diagnostic_successor')
c['horizon_successor']={'source':h['source'],'source_contract':h['source_contract'],'handoff':pin(hp),'measured_predecessor':pin(observed),'control_policy':{'maximum_demands':5,'maximum_rounds':3,'maximum_terms':1,'maximum_proposals':8,'maximum_work':50000},'target_advice_policy':{'maximum_demands':5,'maximum_rounds':3,'maximum_terms':16,'maximum_proposals':8,'maximum_work':50000},'meaning':'Hand-written finite advice horizon only; originalall-six base inventory/fallback/globaldead-forced-earliest scheduler/currentvalidation/rollback/unknown/nativegates remain unchanged. No supplied proof/route/family. Reduced advisory horizon may miss useful proposals or still return UNKNOWN.','fit_prediction':False,'runtime_qualification_inherited':False,'target_requires_all22_no_skip_plus_current_other_controls':True,'complete_diagnostic_return_preserved':True}
c['Review_ABI']=dict(prior['Review_ABI'],schema='unit-row-advised-domain-horizon-cold-typed-Source-review-v3',scope=c['scope'],source=source,sources=sources)
cr=save('Source-contract-v3.json',c)
save('static-evidence-v3.json',{'source':source,'source_contract':cr,'literal_edits':5,'entire_inverse_recovers_parent':True,'top_level_helpers_AST_exact':helpers,'response_stdout_native_exit_suffix_raw_exact':True,'Source17_input2_sixlimits':True,'compile_only':True,'scientific_execution':False})
hr=save('handoff-v3.json',{'schema':'ROOT-horizon-cold-Source-handoff-v3','source':source,'source_contract':cr,'sources':sources,'inputs':c['inputs'],'limits':c['limits'],'source_delta':delta,'controls_handoff':pin(hp),'measured_predecessor':pin(observed),'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'whole_caller_peer_review_pending':True})
print(json.dumps({'source':source,'source_contract':cr,'handoff':hr}))
