"""Strict fixed-key diagnostic guard successor. Raw Source/AST only."""
import ast,hashlib,json,difflib
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def read(p):return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(n,x):
 p=HERE/n
 with p.open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
 return pin(p)
parent=BASE/'unit-row-latest-context-cold-ROOT-source-20261016/unit_row_latest_context_cold_v12.py';pc=parent.parent/'Source-contract-v12.json'
assert pin(parent)['sha256']=='bc338290010bfa9038e1c6e5f1b8f7d8fec9832faa1d7bb8e656c6334106a2a2' and pin(pc)['sha256']=='98bad3f2d430c9e59388e544a005c760262efa9f1e50a4a21e6e89e6ade5b525'
c=read(pc);old=parent.read_text();text=old;edits=[]
for a,b in [("VERSION='unit-row-latest-context-cold-v12'","VERSION='unit-row-latest-context-cold-v13'"),("SCOPE='unit-row-latest-context-cold-Source'","SCOPE='unit-row-latest-context-typed-keys-cold-Source'"),("contract['schema'] == 'unit-row-latest-context-cold-Source-contract-v12'","contract['schema'] == 'unit-row-latest-context-typed-keys-cold-Source-contract-v13'"),("if type(capture) is not dict or set(capture) != set(roles):","if type(capture) is not dict or not all(type(key) is str for key in capture) or set(capture) != set(roles):")]:
 assert text.count(a)==1;text=text.replace(a,b,1);edits.append({'before':a,'after':b})
p=HERE/'unit_row_latest_context_cold_v13.py'
with p.open('xb') as f:f.write(text.encode())
compile(ast.parse(text),str(p),'exec');inverse=text
for e in reversed(edits):assert inverse.count(e['after'])==1;inverse=inverse.replace(e['after'],e['before'],1)
assert inverse==old and ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
source=pin(p);sources=dict(c['sources'],intake=source)
delta=save('Source-delta-v13.json',{'schema':'ROOT-latest-context-typed-keys-Source-delta-v13','parent':pin(parent),'source':source,'edits':edits,'whole_inverse_raw_AST_recovers_parent':True,'all_science_except_samecaller_bindings_unchanged':True,'scientific_calls':0})
(HERE/'caller12-to-caller13-forward.patch').write_text(''.join(difflib.unified_diff(old.splitlines(keepends=True),text.splitlines(keepends=True),fromfile='caller12',tofile='caller13')))
c.update(schema='unit-row-latest-context-typed-keys-cold-Source-contract-v13',scope='unit-row-latest-context-typed-keys-cold-Source',sources=sources,parent_source=pin(parent),parent_contract=pin(pc),source_delta=delta)
c['Review_ABI']=dict(c['Review_ABI'],schema='unit-row-latest-context-typed-keys-cold-typed-Source-review-v13',scope=c['scope'],source=source,sources=sources)
c['latest_context_successor']=dict(c['latest_context_successor'],strict_keys='Exactdict then exactstr keys BEFORE set equality; malformed customkeys rejected before hash dispatch. Capture remains private fixed4caller-owned roles; no hostile concurrent OS guarantee.')
c['diagnostics']='Target-search failure route and inherited bounded raw writer search branch retained; current controls latest-context extension is explicitly declared in latest_context_successor. Both remain unqualified failures, no scientific calls after timeout, native20 successgate unchanged.'
cr=save('Source-contract-v13.json',c)
save('static-evidence-v13.json',{'source':source,'source_contract':cr,'minimal_edits':4,'whole_raw_AST_inverse':True,'existing_native_callcounts_delegate_rules_unchanged':True,'other16Sources_input2_limits_unchanged':True,'compile_only':True,'scientific_calls':0,'scientific_acceptance':False})
hr=save('handoff-v13.json',{'schema':'ROOT-latest-context-typed-keys-Source-handoff-v13','source':source,'source_contract':cr,'sources':sources,'inputs':c['inputs'],'limits':c['limits'],'source_delta':delta,'expected_consumer_cases':43,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'actual_execution_authorized':False,'whole_caller_peer_review_pending':True})
print(json.dumps({'source':source,'source_contract':cr,'handoff':hr}))
