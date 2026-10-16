"""Constant-only paired-controls caller successor. Source/AST/JSON only."""
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
parent=BASE/'unit-row-latest-context-typed-keys-cold-ROOT-source-20261016/unit_row_latest_context_cold_v13.py';pc=parent.parent/'Source-contract-v13.json'
assert pin(parent)['sha256']=='db4fcab69a94c76895ece3a533e983d8d16a136d0ea22b060cf73b4307ff72c3' and pin(pc)['sha256']=='c938d5355dff3807b127653eaf32939bfcab70891c26bf38585dabebc60f80f0'
prior=read(pc);old=parent.read_text();text=old;edits=[]
def replace(a,b):
 global text
 assert text.count(a)==1;text=text.replace(a,b,1);edits.append({'before':a,'after':b})
tree=ast.parse(old);fixed=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FIXED' for t in n.targets))
raw=next(ast.get_source_segment(old,v) for k,v in zip(fixed.keys,fixed.values) if ast.literal_eval(k)=='advice_controls')
assert ast.literal_eval(raw)==prior['sources']['advice_controls'];replace(raw,repr(h['source']))
replace("VERSION='unit-row-latest-context-cold-v13'","VERSION='unit-row-paired-fixture-cold-v14'")
replace("SCOPE='unit-row-latest-context-typed-keys-cold-Source'","SCOPE='unit-row-paired-fixture-cold-Source'")
replace("contract['schema'] == 'unit-row-latest-context-typed-keys-cold-Source-contract-v13'","contract['schema'] == 'unit-row-paired-fixture-cold-Source-contract-v14'")
p=HERE/'unit_row_paired_fixture_cold_v14.py'
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
delta=save('Source-delta-v14.json',{'schema':'ROOT-paired-fixture-caller-Source-delta-v14','parent':pin(parent),'source':source,'edits':edits,'whole_raw_AST_inverse_recovers_parent':True,'scope':'One controls pin/own3IDs only; all17helpers/every nestedfunction/failurewriter/nativepositive/proof/output paths exact.'})
c=dict(prior,schema='unit-row-paired-fixture-cold-Source-contract-v14',scope='unit-row-paired-fixture-cold-Source',sources=sources,parent_source=pin(parent),parent_contract=pin(pc),source_delta=delta)
for key in ('compatible_source_fibres_successor','observation_reuse_successor','phase_diagnostic_successor','native_sample_diagnostic_successor','continuation_progress_successor'):
 c[key]=dict(prior[key],components=component_map)
c['native_sample_diagnostic_successor']['phase_stderr']=cc['phase_stderr']
c['continuation_progress_successor']['continuation_stderr']=cc['continuation_stderr']
c['paired_fixture_successor']={'components':component_map,'scope':'Control-specific paired original/duplicate-source generic fixtures. Actual complete current adviser batch/independent receipt/global BRANCH/selection/TRY/checkpoint evidence required; all43 meanings and original target/grammar/limits preserved. No provided target word/route, fitted degree/receipt, future member preinstallation, new scheduler or hypothesis pruning. Eligibility not assumed from static pair construction.','expected_cases':43,'cases':cases,'runtime_qualification_inherited':False,'fit_prediction':False,'scientific_acceptance':False}
c['Review_ABI']=dict(prior['Review_ABI'],schema='unit-row-paired-fixture-cold-typed-Source-review-v14',scope=c['scope'],source=source,sources=sources)
c['advice']=dict(prior['advice'],current_sources={k:sources[k] for k in ('engine','adviser','advice_validator','advice_controls')})
cr=save('Source-contract-v14.json',c)
save('static-evidence-v14.json',{'source':source,'source_contract':cr,'literal_edits':4,'whole_raw_AST_inverse':True,'all_helpers_nestedfunctions_raw_AST_exact':True,'response_proof_nativeexit_tail_exact':True,'15otherSources_input2_limits_exact':True,'compile_only':True,'scientific_calls':0,'scientific_acceptance':False})
hr=save('handoff-v14.json',{'schema':'ROOT-paired-fixture-cold-Source-handoff-v14','source':source,'source_contract':cr,'sources':sources,'inputs':c['inputs'],'limits':c['limits'],'source_delta':delta,'expected_consumer_cases':43,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'whole_caller_peer_review_pending':True})
print(json.dumps({'source':source,'source_contract':cr,'handoff':hr}))
