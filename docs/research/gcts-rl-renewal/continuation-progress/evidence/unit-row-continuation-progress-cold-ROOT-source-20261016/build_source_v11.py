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
parent=BASE/'unit-row-native-samples-cold-ROOT-source-20261016/unit_row_native_samples_cold_v10.py'
pc=parent.parent/'Source-contract-v10.json'
assert pin(parent)['sha256']=='bf2e53b429af5e0edd08cbae5f40b4faae79833c6b338a9fdf1dac1a611dfb99'
assert pin(pc)['sha256']=='81687b8621dd27dddb4cccb0d9d5125ae65a1bc662e55722b328f6db9683e71d'
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
replace("VERSION='unit-row-native-samples-cold-v10'","VERSION='unit-row-continuation-progress-cold-v11'")
replace("SCOPE='unit-row-native-samples-cold-Source'","SCOPE='unit-row-continuation-progress-cold-Source'")
replace("contract['schema'] == 'unit-row-native-samples-cold-Source-contract-v10'","contract['schema'] == 'unit-row-continuation-progress-cold-Source-contract-v11'")
path=HERE/'unit_row_continuation_progress_cold_v11.py'
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
observed=BASE/'unit-row-native-samples-ROOT-20261016/ROOT-advice-controls-disposition-v1.json'
assert pin(observed)['sha256']=='6f6fdaaf94c0c9956df6262ca8a0c2e3b7ab7432c176e9354e2365386a39f2d7'
delta=save('Source-delta-v11.json',{'schema':'ROOT-continuation-progress-cold-Source-delta-v11','parent':pin(parent),'source':source,'edits':edits,'entire_inverse_recovers_parent':True,'scope':'One controls pin and own VERSION/SCOPE/consumed schema only; all17 helpers/nestedfunctions/output-nativeexit exact.'})
c=dict(prior,schema='unit-row-continuation-progress-cold-Source-contract-v11',scope='unit-row-continuation-progress-cold-Source',sources=sources,parent_source=pin(parent),parent_contract=pin(pc),source_delta=delta)
c['compatible_source_fibres_successor']=dict(prior['compatible_source_fibres_successor'])
c['compatible_source_fibres_successor']['components']=dict(prior['compatible_source_fibres_successor']['components'],**components)
c['compatible_source_fibres_successor']['measured_predecessor']=pin(observed)
c['observation_reuse_successor']=dict(prior['observation_reuse_successor'],components=components)
c['phase_diagnostic_successor']={'components':components,'expected_consumer_cases':43,'cases':cases,'scope':'Only bounded native-first continuation callback progress observations added; existing24 phase groups remain unchanged. Counter/cap affect diagnostic records only. Same actual kwargs, existing snapshots/receipts, delegate-once/return identity/exceptions and scientific stop conditions. All original native20 work remains charged. All control semantics, report reuse, declared cases, target inputs and budgets unchanged. No new clock API, caller helper behavior, process or posttimeout scientific work; the explicit diagnostic tick-return/wire ABI is newly declared. Nested adapter step returnsNone and is not sampled. Samples are unqualified reached-write diagnostics; intervals between native reads include writes/checks and all intervening work. External original callerlaunch/terminal define the reference; no G/deadline reset, exclusive-method time, case count, proof/trajectory/resource-positive authority or earlier attribution.','measured_parent_failure':pin(observed),'target_policy':prior['compatible_source_fibres_successor']['target_policy'],'control_policy':prior['compatible_source_fibres_successor']['control_policy'],'runtime_qualification_inherited':False,'fit_prediction':False,'target_requires_all_current_consumer_no_skip_plus_original_and_retention':True}
c['native_sample_diagnostic_successor']={'components':components,'phase_stderr':cc['phase_stderr'],'native_tick_return':'Direct main.tick captured original native now; no caller helper behavior change. Control wrappers forward the same tick. Nested step callbacks returnNone, never sampled.','scope':'Diagnostic read intervals only; not per-method exclusive times, accepted cases, completed phases or proof/resource-positive authority.','original_G_and_deadline_unchanged':True}
c['continuation_progress_successor']={'components':components,'diagnostic_wire':'Exact current controls6 contract; at most24 TOTAL records across continuationcallback sites, no algorithm stopping or change at cap. Native int/context observations only, not qualified cases or per-method exclusive durations.','all_existing_phase_markers_preserved':True,'scientific_delegate_and_stop_semantics_preserved':True}
c['continuation_progress_successor']['continuation_stderr']=cc['continuation_stderr']
c['Review_ABI']=dict(prior['Review_ABI'],schema='unit-row-continuation-progress-cold-typed-Source-review-v11',scope=c['scope'],source=source,sources=sources)
c['advice']=dict(prior['advice'],current_sources={k:sources[k] for k in ('engine','adviser','advice_validator','advice_controls')})
cr=save('Source-contract-v11.json',c)
save('static-evidence-v11.json',{'source':source,'source_contract':cr,'literal_edits':4,'entire_inverse_recovers_parent':True,'top_level_helpers_raw_AST_exact':helpers,'all_nested_functions_AST_exact':True,'response_stdout_native_exit_suffix_raw_exact':True,'Source17_input2_sixlimits':True,'compile_only':True,'scientific_execution':False,'metadata_note':'Adapt existing AST-located literal pin assembly to one control pin and own identifiers only; no scientific execution.'})
hr=save('handoff-v11.json',{'schema':'ROOT-continuation-progress-cold-Source-handoff-v11','source':source,'source_contract':cr,'sources':sources,'inputs':c['inputs'],'limits':c['limits'],'source_delta':delta,'components':components,'expected_consumer_cases':len(cases),'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'whole_caller_peer_review_pending':True})
print(json.dumps({'source':source,'source_contract':cr,'handoff':hr}))
