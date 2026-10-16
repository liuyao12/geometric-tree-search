"""Constant-only remote eligibility controls caller successor. Source/AST/JSON only."""
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
assert len(sys.argv)==3
hp=Path(sys.argv[1]).resolve();assert pin(hp)['sha256']==sys.argv[2];h=read(hp)
assert h['source_only'] and h['scientific_calls']==0 and not h['scientific_acceptance']
component={'handoff':pin(hp),'source':h['source'],'source_contract':h['source_contract']}
for r in component.values():check(r)
cc=read(check(h['source_contract']));assert cc['API']['expected_cases']==43
parent=BASE/'unit-row-remote-eligibility-cold-ROOT-source-20261016/unit_row_remote_eligibility_cold_v15.py';pc=parent.parent/'Source-contract-v15.json'
assert pin(parent)['sha256']=='451b484879c56bb31404ca942a47566f029f548ef16a2d38ecfe890738b711e2' and pin(pc)['sha256']=='19b9d91478a01239f75218d60b49b228d8b2df0000d7d44622d4136c34ac212b'
prior=read(pc);old=parent.read_text();text=old;edits=[]
def replace(a,b):
 global text
 assert text.count(a)==1;text=text.replace(a,b,1);edits.append({'before':a,'after':b})
tree=ast.parse(old);fixed=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FIXED' for t in n.targets))
raw=next(ast.get_source_segment(old,v) for k,v in zip(fixed.keys,fixed.values) if ast.literal_eval(k)=='advice_controls')
assert ast.literal_eval(raw)==prior['sources']['advice_controls'];replace(raw,repr(h['source']))
replace("VERSION='unit-row-remote-eligibility-cold-v15'","VERSION='unit-row-selective-multikey-cold-v16'")
replace("SCOPE='unit-row-remote-eligibility-cold-Source'","SCOPE='unit-row-selective-multikey-cold-Source'")
replace("contract['schema'] == 'unit-row-remote-eligibility-cold-Source-contract-v15'","contract['schema'] == 'unit-row-selective-multikey-cold-Source-contract-v16'")
p=HERE/'unit_row_selective_multikey_cold_v16.py'
with p.open('xb') as f:f.write(text.encode())
compile(ast.parse(text),str(p),'exec');inverse=text
for e in reversed(edits):assert inverse.count(e['after'])==1;inverse=inverse.replace(e['after'],e['before'],1)
assert inverse==old
otree=ast.parse(old);ntree=ast.parse(text)
for n in ast.walk(ntree):
 if isinstance(n,ast.FunctionDef) and n.name!='main':
  found=[o for o in ast.walk(otree) if isinstance(o,ast.FunctionDef) and o.name==n.name and ast.dump(o,include_attributes=False)==ast.dump(n,include_attributes=False)]
  assert found and any(ast.get_source_segment(text,n)==ast.get_source_segment(old,o) for o in found)
tail="    body = {'schema':'ROOT-unit-row-global-engine-response-body-v1',";assert text[text.index(tail):]==old[old.index(tail):]
source=pin(p);sources=dict(prior['sources'],intake=source,advice_controls=h['source'])
assert len(sources)==17 and all(sources[k]==prior['sources'][k] for k in sources if k not in ('intake','advice_controls'))
for r in [*sources.values(),*prior['inputs'].values()]:check(r)
cases=prior['compatible_source_fibres_successor']['cases'];assert cc['all_case_names']==cases and len(cases)==43
component_map={'advice_controls':component}
delta=save('Source-delta-v16.json',{'schema':'ROOT-selective-multikey-caller-Source-delta-v16','parent':pin(parent),'source':source,'edits':edits,'whole_raw_AST_inverse_recovers_parent':True,'scope':'One controls pin/own3IDs only; all17helpers/every nestedfunction/failurewriter/nativepositive/proof/output paths exact.'})
c=dict(prior,schema='unit-row-selective-multikey-cold-Source-contract-v16',scope='unit-row-selective-multikey-cold-Source',sources=sources,parent_source=pin(parent),parent_contract=pin(pc),source_delta=delta)
for key in ('compatible_source_fibres_successor','observation_reuse_successor','phase_diagnostic_successor','native_sample_diagnostic_successor','continuation_progress_successor','paired_fixture_successor','remote_eligibility_successor'):
 c[key]=dict(prior[key],components=component_map)
c['native_sample_diagnostic_successor']['phase_stderr']=cc['phase_stderr']
c['continuation_progress_successor']['continuation_stderr']=cc['continuation_stderr']
c['selective_multikey_successor']={'components':component_map,'scope':'Separately owned control-only generic selective multi-key C fixture, actual complete batch and independent whole/executed subset receipts; A first-ranked and B success contexts preserved. True forced-only normalization and actual bad-row BRANCH plus selective conflict/survivor checks required; all43 meanings and native gates retained. No target-policy change, proof route, future member preinstallation or fit prediction.','expected_cases':43,'cases':cases,'scientific_acceptance':False,'runtime_qualification_inherited':False}
c['Review_ABI']=dict(prior['Review_ABI'],schema='unit-row-selective-multikey-cold-typed-Source-review-v16',scope=c['scope'],source=source,sources=sources)
c['advice']=dict(prior['advice'],current_sources={k:sources[k] for k in ('engine','adviser','advice_validator','advice_controls')})
cr=save('Source-contract-v16.json',c)
save('static-evidence-v16.json',{'source':source,'source_contract':cr,'literal_edits':4,'whole_raw_AST_inverse':True,'all_helpers_nestedfunctions_raw_AST_exact':True,'response_proof_nativeexit_tail_exact':True,'15otherSources_input2_limits_exact':True,'compile_only':True,'scientific_calls':0,'scientific_acceptance':False})
hr=save('handoff-v16.json',{'schema':'ROOT-selective-multikey-cold-Source-handoff-v16','source':source,'source_contract':cr,'sources':sources,'inputs':c['inputs'],'limits':c['limits'],'source_delta':delta,'expected_consumer_cases':43,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'whole_caller_peer_review_pending':True})
print(json.dumps({'source':source,'source_contract':cr,'handoff':hr}))
